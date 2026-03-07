"""Phase 2 Analysis Service - chunk-aware map-reduce pipeline

Orchestrates four AI analysis jobs against extracted document text:
  1. Structured entity extraction
  2. Executive summary
  3. Risk detection (CUAD rule-based primary, LLM fallback)
  4. Missing clause detection (CUAD gap detection primary, LLM fallback)

Small documents (≤ _SINGLE_PASS_CHARS) are analysed in a single LLM call
per job.  Larger documents are split into their pre-computed chunks and each
chunk is processed independently ("map"), then results are merged ("reduce").

Risk detection and missing clause analysis use the CUAD rule-based engine as
the primary system.  The LLM extracts clause text, then deterministic rules
evaluate risk — no hallucination in scoring.  If CUAD extraction fails,
the system falls back to the original LLM-prompted approach.

Entry point: AnalysisService.run(contract_id)

Designed to be invoked from the async task queue.  All exceptions are caught
internally; the contract status is updated to FAILED on any unrecoverable
error so callers can detect the outcome by polling.
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from app.models.schemas import ContractStatus, Language
from app.services.sqlite_service import DatabaseService
from app.services.ollama_service import OllamaService
from app.agents.cuad_clause_extraction_agent import CUADClauseExtractionAgent
from app.agents.risk_evaluation_engine import RiskEvaluationEngine
from app.agents.gap_detection_agent import GapDetectionAgent
from app.models.clause_schema import RiskLevel

logger = logging.getLogger(__name__)

# Documents under this size are analysed in one shot (no chunking needed).
_SINGLE_PASS_CHARS = 12_000

# When chunking, hard-cap each chunk text sent to the LLM.
_MAX_CHUNK_CHARS = 10_000

# Maximum chunks processed per job to bound total LLM time.
_MAX_CHUNKS = 20

# Standard clauses evaluated in gap analysis
_STANDARD_CLAUSES = [
    "confidentiality",
    "data_protection",
    "force_majeure",
    "termination",
    "governing_law",
]


def _truncate(text: str, limit: int = _SINGLE_PASS_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


def _parse_json_response(raw: str, context: str) -> Optional[Dict]:
    """
    Robustly extract a JSON object from an LLM response string.

    The LLM sometimes wraps the JSON in markdown fences (```json ... ```) or
    adds a preamble sentence. This function strips all of that before parsing.
    Returns None on failure so callers can use their fallback.
    """
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()
    # Find first { and last } to isolate the JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        logger.warning(f"No JSON object found in LLM response for {context}")
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        logger.warning(f"JSON parse error for {context}: {exc}")
        return None


class AnalysisService:
    """
    Orchestrates the four Phase 2 analysis jobs.

    A single DatabaseService and OpenAIService are injected at construction
    time to allow mocking in tests.
    """

    def __init__(
        self,
        db: Optional[DatabaseService] = None,
        ai: Optional[OllamaService] = None,
    ) -> None:
        from app.services.sqlite_service import database_service
        from app.services.ollama_service import ollama_service

        self._db = db or database_service
        self._ai = ai or ollama_service
        self._clause_extractor = CUADClauseExtractionAgent(ai_service=self._ai)
        self._risk_evaluator = RiskEvaluationEngine()
        self._gap_detector = GapDetectionAgent()

    # ── Public entry point ────────────────────────────────────────────────────

    async def run(self, contract_id: str) -> None:
        """
        Run all four analysis jobs for a document.

        Automatically chooses single-pass or map-reduce depending on
        document size.
        """
        logger.info(f"[analysis] Starting analysis for {contract_id}")

        contract = await self._db.get_contract_by_id(contract_id)
        if not contract:
            logger.error(f"[analysis] Contract {contract_id} not found")
            return

        current_status = contract.get("status")
        if current_status not in (
            ContractStatus.EXTRACTED.value,
            ContractStatus.ANALYZED.value,
            ContractStatus.PROCESSING.value,
        ):
            logger.warning(
                f"[analysis] Skipping {contract_id}: status is '{current_status}'"
            )
            return

        # ── Fetch full text ───────────────────────────────────────────────────
        text_record = await self._db.get_document_text(contract_id)
        if not text_record or not text_record.get("raw_text"):
            logger.error(f"[analysis] No extracted text for {contract_id}")
            await self._db.update_contract_status(contract_id, ContractStatus.FAILED)
            return

        raw_text: str = text_record["raw_text"]
        is_large = len(raw_text) > _SINGLE_PASS_CHARS

        # ── Fetch chunks for large documents ──────────────────────────────────
        chunk_texts: List[str] = []
        if is_large:
            chunks = await self._db.get_chunks(contract_id)
            if chunks:
                chunk_texts = [
                    _truncate(c["chunk_text"], _MAX_CHUNK_CHARS)
                    for c in chunks[:_MAX_CHUNKS]
                ]
                logger.info(
                    f"[analysis] Large document ({len(raw_text)} chars) — "
                    f"using {len(chunk_texts)} chunks for map-reduce"
                )
            else:
                logger.warning(
                    f"[analysis] No chunks found for large doc {contract_id}; "
                    "falling back to truncated single-pass"
                )
                is_large = False

        text_for_single_pass = _truncate(raw_text) if not is_large else ""

        await self._db.update_contract_status(contract_id, ContractStatus.PROCESSING)

        try:
            # ── Entity extraction & summary (always LLM) ─────────────────────
            if is_large:
                entities = await self._map_reduce_entities(chunk_texts)
                summary = await self._map_reduce_summary(chunk_texts)
            else:
                entities = await self._extract_entities(text_for_single_pass)
                summary = await self._generate_summary(text_for_single_pass)

            # ── Risk & gap detection: CUAD rule-based (primary) ──────────────
            lang_raw = contract.get("language", "en")
            lang_map = {"english": "en", "arabic": "ar"}
            lang_code = lang_map.get(lang_raw, lang_raw) if lang_raw not in ("en", "ar") else lang_raw
            try:
                language = Language(lang_code)
            except ValueError:
                language = Language.ENGLISH
            cuad_risks, cuad_missing = await self._detect_risks_cuad(
                contract_id, raw_text, language, entities
            )
            if cuad_risks is not None:
                risks = cuad_risks
                missing = cuad_missing or []
                logger.info(f"[analysis] Using CUAD rule-based risks for {contract_id}")
            else:
                # ── Fallback: LLM-prompted risk detection ────────────────────
                logger.warning(
                    f"[analysis] CUAD extraction failed for {contract_id}; "
                    "falling back to LLM risk detection"
                )
                if is_large:
                    risks = await self._map_reduce_risks(chunk_texts)
                    missing = await self._map_reduce_missing_clauses(chunk_texts)
                else:
                    risks = await self._detect_risks(text_for_single_pass)
                    missing = await self._detect_missing_clauses(text_for_single_pass)

            # ── Persist ───────────────────────────────────────────────────────
            await self._db.save_contract_entities(contract_id, entities)
            await self._db.save_contract_summary(contract_id, summary)
            await self._db.save_contract_risks(contract_id, risks)
            await self._db.save_contract_gaps(contract_id, missing)

            risk_score = self._compute_risk_score(risks)
            await self._db.update_contract_analysis(
                contract_id,
                {
                    "extracted_data": entities,
                    "analysis": {
                        "summary": summary,
                        "risks": risks,
                        "compliance": [],
                        "legal_opinions": [],
                        "overall_risk_score": risk_score,
                        "compliance_score": max(0.0, 100.0 - risk_score * 10),
                        "entities": entities,
                        "missing_clauses": missing,
                    },
                },
            )

            await self._db.update_contract_status(contract_id, ContractStatus.ANALYZED)
            logger.info(
                f"[analysis] Completed for {contract_id} "
                f"({'map-reduce' if is_large else 'single-pass'}): "
                f"{len(risks)} risks, {len(missing)} missing clauses"
            )

        except Exception as exc:
            logger.error(
                f"[analysis] Failed for {contract_id}: {exc}", exc_info=True
            )
            try:
                await self._db.update_contract_status(
                    contract_id, ContractStatus.FAILED
                )
            except Exception:
                pass

    # ── Private analysis jobs ─────────────────────────────────────────────────

    # ── CUAD rule-based risk & gap detection (primary) ────────────────────────

    _CUAD_SEVERITY_MAP = {
        RiskLevel.HIGH: "high",
        RiskLevel.MEDIUM: "medium",
        RiskLevel.LOW: "low",
        RiskLevel.NONE: "low",
    }

    async def _detect_risks_cuad(
        self,
        contract_id: str,
        raw_text: str,
        language: Language,
        entities: Dict[str, Any],
    ) -> tuple[Optional[List[Dict]], Optional[List[str]]]:
        """
        CUAD rule-based risk detection.

        1. LLM extracts clause text (what the clause says).
        2. Deterministic rule engine scores risk (no hallucination).
        3. Gap detector finds missing clauses.

        Returns (risks, missing_clauses) on success, or (None, None)
        if clause extraction fails so the caller can fall back to LLM.
        """
        try:
            # Step 1: extract clauses via LLM
            clause_analysis = await self._clause_extractor.extract_clauses(
                contract_id=contract_id,
                contract_text=raw_text,
                language=language,
            )

            # Sanity check: if CUAD found zero clauses on non-trivial text,
            # the LLM probably returned garbage — fall back to prompted risks.
            clause_fields = [
                "governing_law", "confidentiality", "termination",
                "liability", "indemnification", "payment_terms",
                "intellectual_property", "data_protection", "force_majeure",
                "non_compete", "exclusivity", "change_of_control",
                "anti_assignment", "audit_rights", "post_termination_services",
            ]
            any_present = any(
                getattr(clause_analysis, f, None)
                and getattr(clause_analysis, f).present
                for f in clause_fields
            )
            if not any_present and len(raw_text) > 200:
                logger.warning(
                    f"[analysis] CUAD extracted zero clauses from {len(raw_text)} chars "
                    f"for {contract_id}; treating as extraction failure"
                )
                return None, None

            # Step 2: evaluate risk with deterministic rules
            clause_analysis = self._risk_evaluator.evaluate_contract_risk(clause_analysis)

            # Step 3: generate risk summary (includes risk_flags)
            risk_summary = self._risk_evaluator.generate_risk_summary(
                clause_analysis, entities
            )

            # Step 4: gap detection
            gap_report = self._gap_detector.generate_gap_report(clause_analysis)

            # ── Convert to the Risk dict format the UI expects ────────────────
            risks: List[Dict] = []

            # Add high + medium risk items from the rule engine
            for item in risk_summary.high_risk_items:
                risks.append({
                    "risk_type": item["clause"].lower().replace(" ", "_"),
                    "severity": "high",
                    "description": item["reason"],
                    "source_text": self._get_clause_text(clause_analysis, item["clause"]),
                })
            for item in risk_summary.medium_risk_items:
                risks.append({
                    "risk_type": item["clause"].lower().replace(" ", "_"),
                    "severity": "medium",
                    "description": item["reason"],
                    "source_text": self._get_clause_text(clause_analysis, item["clause"]),
                })

            # ── Convert missing clauses to a flat list of names ───────────────
            missing: List[str] = []
            for gap in gap_report.get("critical_gaps", []):
                name = gap.get("clause_type") or gap.get("clause", "")
                if isinstance(name, str) and name:
                    missing.append(name)
            for gap in gap_report.get("recommended_gaps", []):
                name = gap.get("clause_type") or gap.get("clause", "")
                if isinstance(name, str) and name:
                    missing.append(name)

            logger.info(
                f"[analysis] CUAD rule-based: {len(risks)} risks, "
                f"{len(missing)} missing clauses for {contract_id}"
            )
            return risks, missing

        except BaseException as exc:
            logger.warning(f"[analysis] CUAD risk detection failed: {exc}", exc_info=True)
            return None, None

    @staticmethod
    def _get_clause_text(clause_analysis, display_name: str) -> Optional[str]:
        """Get the source text for a clause from the CUAD analysis."""
        field_map = {
            "governing law": "governing_law",
            "confidentiality": "confidentiality",
            "termination": "termination",
            "liability": "liability",
            "indemnification": "indemnification",
            "payment terms": "payment_terms",
            "intellectual property": "intellectual_property",
            "data protection": "data_protection",
            "force majeure": "force_majeure",
            "non-compete": "non_compete",
            "exclusivity": "exclusivity",
            "change of control": "change_of_control",
            "anti-assignment": "anti_assignment",
            "audit rights": "audit_rights",
            "post-termination services": "post_termination_services",
        }
        field = field_map.get(display_name.lower())
        if field:
            clause = getattr(clause_analysis, field, None)
            if clause and clause.text:
                return clause.text[:300]
        return None

    # ── LLM-based analysis jobs (entity/summary always, risk/gap as fallback) ─

    async def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Feature 1: structured entity extraction."""
        system_prompt = (
            "You are a contract analysis AI. Extract the following fields from the contract text.\n"
            "Return ONLY a JSON object with these exact keys:\n"
            "  parties: array of party names (strings)\n"
            "  effective_date: ISO date string or empty string\n"
            "  expiration_date: ISO date string or empty string\n"
            "  governing_law: jurisdiction name or empty string\n"
            "  financial_terms: array of plain-text descriptions of financial obligations\n"
            "  obligations: array of plain-text descriptions of key obligations\n"
            "If a field cannot be determined, use an empty string or empty array.\n"
            "Do not include any explanation outside the JSON object."
        )
        schema = {
            "parties": [],
            "effective_date": "",
            "expiration_date": "",
            "governing_law": "",
            "financial_terms": [],
            "obligations": [],
        }
        raw = await self._ai.structured_extraction(
            prompt=system_prompt,
            context=text,
            schema=schema,
        )
        parsed = _parse_json_response(json.dumps(raw) if isinstance(raw, dict) else str(raw), "entities")
        if not parsed:
            logger.warning("[analysis] Entity extraction returned no parseable JSON; using defaults")
            return schema.copy()
        # Ensure all required keys are present
        for key, default in schema.items():
            if key not in parsed:
                parsed[key] = default
        return parsed

    async def _generate_summary(self, text: str) -> str:
        """Feature 2: executive summary (150–250 words)."""
        system_prompt = (
            "You are a legal analyst. Write a concise executive summary of the following contract.\n"
            "The summary must be 150 to 250 words.\n"
            "Cover: contract purpose, scope, key obligations, financial exposure, and important risks.\n"
            "Write in plain business English. Do not use bullet points."
        )
        try:
            result = await self._ai.analyze_with_guidance(
                system_prompt=system_prompt,
                content=text,
                temperature=0.2,
                max_tokens=400,
            )
            return result.strip() if result else "Summary not available."
        except Exception as exc:
            logger.warning(f"[analysis] Summary generation failed: {exc}")
            return "Summary not available."

    async def _detect_risks(self, text: str) -> List[Dict]:
        """Feature 3: risk detection."""
        system_prompt = (
            "You are a contract risk analyst. Identify risk clauses in the contract.\n"
            "Return ONLY a JSON object with a single key 'risks' whose value is an array.\n"
            "Each risk object must have these exact keys:\n"
            "  risk_type: short category name (e.g. 'liability', 'termination', 'penalty')\n"
            "  severity: one of 'low', 'medium', 'high', 'critical'\n"
            "  description: one sentence explaining the risk\n"
            "  source_text: the verbatim clause or phrase that triggered this risk (max 200 chars)\n"
            "Focus on: unlimited liability, one-sided termination, excessive penalties, "
            "unbalanced obligations, missing indemnification caps.\n"
            "If no risks are found, return {\"risks\": []}.\n"
            "Do not include any explanation outside the JSON object."
        )
        schema = {"risks": []}
        raw = await self._ai.structured_extraction(
            prompt=system_prompt,
            context=text,
            schema=schema,
        )
        if isinstance(raw, dict):
            risks = raw.get("risks", [])
        else:
            parsed = _parse_json_response(str(raw), "risks")
            risks = parsed.get("risks", []) if parsed else []
        return self._validate_risks(risks)

    async def _detect_missing_clauses(self, text: str) -> List[str]:
        """Feature 4: missing standard clause detection."""
        clauses_list = ", ".join(_STANDARD_CLAUSES)
        system_prompt = (
            f"You are a contract compliance analyst. Check whether the following standard clauses "
            f"are present in the contract: {clauses_list}.\n"
            "Return ONLY a JSON object with this exact key:\n"
            "  missing_clauses: array of clause names that are ABSENT from the contract\n"
            f"Only use clause names from this list: {clauses_list}.\n"
            "If all clauses are present, return {\"missing_clauses\": []}.\n"
            "Do not include any explanation outside the JSON object."
        )
        schema = {"missing_clauses": []}
        raw = await self._ai.structured_extraction(
            prompt=system_prompt,
            context=text,
            schema=schema,
        )
        if isinstance(raw, dict):
            missing = raw.get("missing_clauses", [])
        else:
            parsed = _parse_json_response(str(raw), "gaps")
            missing = parsed.get("missing_clauses", []) if parsed else []

        # Whitelist: only keep recognised clause names; guard against non-list values
        if not isinstance(missing, list):
            return []
        return [c for c in missing if isinstance(c, str) and c in _STANDARD_CLAUSES]

    # ══════════════════════════════════════════════════════════════════════════
    # MAP-REDUCE jobs (for large documents)
    # ══════════════════════════════════════════════════════════════════════════

    async def _map_reduce_entities(self, chunks: List[str]) -> Dict[str, Any]:
        """Extract entities from each chunk, then merge into one result."""
        partial_results = await asyncio.gather(
            *(self._extract_entities(chunk) for chunk in chunks),
            return_exceptions=True,
        )
        merged: Dict[str, Any] = {
            "parties": [],
            "effective_date": "",
            "expiration_date": "",
            "governing_law": "",
            "financial_terms": [],
            "obligations": [],
        }
        seen_parties: set = set()
        seen_financial: set = set()
        seen_obligations: set = set()

        for result in partial_results:
            if isinstance(result, Exception):
                logger.warning(f"[analysis] Entity chunk failed: {result}")
                continue
            if not isinstance(result, dict):
                continue
            for p in result.get("parties", []):
                norm = p.strip().lower()
                if norm and norm not in seen_parties:
                    seen_parties.add(norm)
                    merged["parties"].append(p.strip())
            if not merged["effective_date"] and result.get("effective_date"):
                merged["effective_date"] = result["effective_date"]
            if not merged["expiration_date"] and result.get("expiration_date"):
                merged["expiration_date"] = result["expiration_date"]
            if not merged["governing_law"] and result.get("governing_law"):
                merged["governing_law"] = result["governing_law"]
            for ft in result.get("financial_terms", []):
                norm = ft.strip().lower()
                if norm and norm not in seen_financial:
                    seen_financial.add(norm)
                    merged["financial_terms"].append(ft.strip())
            for ob in result.get("obligations", []):
                norm = ob.strip().lower()
                if norm and norm not in seen_obligations:
                    seen_obligations.add(norm)
                    merged["obligations"].append(ob.strip())

        logger.info(
            f"[analysis] Entity map-reduce: {len(chunks)} chunks → "
            f"{len(merged['parties'])} parties, "
            f"{len(merged['financial_terms'])} financial terms"
        )
        return merged

    async def _map_reduce_summary(self, chunks: List[str]) -> str:
        """Summarise each chunk, then produce a combined executive summary."""
        partial_summaries = await asyncio.gather(
            *(self._generate_summary(chunk) for chunk in chunks),
            return_exceptions=True,
        )
        valid_summaries = [
            s for s in partial_summaries
            if isinstance(s, str) and s != "Summary not available."
        ]
        if not valid_summaries:
            return "Summary not available."

        combined = "\n\n".join(valid_summaries)
        reduce_prompt = (
            "You are a legal analyst. Below are partial summaries of different sections "
            "of a single contract. Synthesise them into one coherent executive summary "
            "of 150 to 250 words.\n"
            "Cover: contract purpose, scope, key obligations, financial exposure, and important risks.\n"
            "Write in plain business English. Do not use bullet points."
        )
        try:
            result = await self._ai.analyze_with_guidance(
                system_prompt=reduce_prompt,
                content=combined,
                temperature=0.2,
                max_tokens=400,
            )
            return result.strip() if result else "Summary not available."
        except Exception as exc:
            logger.warning(f"[analysis] Summary reduce failed: {exc}")
            return combined[:2000]

    async def _map_reduce_risks(self, chunks: List[str]) -> List[Dict]:
        """Detect risks per chunk, then deduplicate and merge."""
        partial_results = await asyncio.gather(
            *(self._detect_risks(chunk) for chunk in chunks),
            return_exceptions=True,
        )
        all_risks: List[Dict] = []
        seen_descriptions: set = set()

        for result in partial_results:
            if isinstance(result, Exception):
                logger.warning(f"[analysis] Risk chunk failed: {result}")
                continue
            if not isinstance(result, list):
                continue
            for risk in result:
                desc_key = risk.get("description", "").strip().lower()
                if desc_key and desc_key not in seen_descriptions:
                    seen_descriptions.add(desc_key)
                    all_risks.append(risk)

        logger.info(
            f"[analysis] Risk map-reduce: {len(chunks)} chunks → "
            f"{len(all_risks)} unique risks"
        )
        return all_risks

    async def _map_reduce_missing_clauses(self, chunks: List[str]) -> List[str]:
        """
        A clause is considered "present" if ANY chunk found it.
        Only clauses missing from ALL chunks are reported as missing.
        """
        partial_results = await asyncio.gather(
            *(self._detect_missing_clauses(chunk) for chunk in chunks),
            return_exceptions=True,
        )
        missing_counts: Dict[str, int] = {c: 0 for c in _STANDARD_CLAUSES}
        valid_chunk_count = 0

        for result in partial_results:
            if isinstance(result, Exception):
                continue
            if not isinstance(result, list):
                continue
            valid_chunk_count += 1
            for clause in result:
                if clause in missing_counts:
                    missing_counts[clause] += 1

        if valid_chunk_count == 0:
            return list(_STANDARD_CLAUSES)

        truly_missing = [
            clause
            for clause, count in missing_counts.items()
            if count == valid_chunk_count
        ]
        logger.info(
            f"[analysis] Clause gap map-reduce: {len(chunks)} chunks → "
            f"{len(truly_missing)} truly missing clauses"
        )
        return truly_missing

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _validate_risks(risks: list) -> List[Dict]:
        valid = []
        for r in risks:
            if not isinstance(r, dict):
                continue
            valid.append({
                "risk_type": str(r.get("risk_type", "unknown")),
                "severity": str(r.get("severity", "medium")),
                "description": str(r.get("description", "")),
                "source_text": str(r.get("source_text", ""))[:300] or None,
            })
        return valid

    @staticmethod
    def _compute_risk_score(risks: List[Dict]) -> float:
        """
        Compute an overall risk score (0–10) from a list of risk findings.

        Severity weights: critical=4, high=3, medium=2, low=1.
        Score = min(10, sum_of_weights / 2).
        An empty risk list scores 0.
        """
        weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        total = sum(weights.get(r.get("severity", "low"), 1) for r in risks)
        return round(min(10.0, total / 2), 1)


# Module-level singleton — matches the pattern used by document_processor
analysis_service = AnalysisService()
