"""
Phase 2 Analysis Service

Orchestrates four AI analysis jobs against extracted document text:
  1. Structured entity extraction
  2. Executive summary
  3. Risk detection
  4. Missing clause detection

Entry point: AnalysisService.run(contract_id)

Designed to run as a FastAPI BackgroundTask. All exceptions are caught
internally; the contract status is updated to FAILED on any unrecoverable
error so callers can detect the outcome by polling.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from app.models.schemas import ContractStatus
from app.services.sqlite_service import DatabaseService
from app.services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

# Maximum characters sent to the LLM in a single request.
# 12k chars ≈ 3k tokens — fast, safe, covers most contracts.
_MAX_TEXT_CHARS = 12_000

# Standard clauses evaluated in gap analysis
_STANDARD_CLAUSES = [
    "confidentiality",
    "data_protection",
    "force_majeure",
    "termination",
    "governing_law",
]


def _truncate(text: str) -> str:
    """Keep only the first _MAX_TEXT_CHARS characters of a document."""
    if len(text) <= _MAX_TEXT_CHARS:
        return text
    logger.warning(f"Document text truncated from {len(text)} to {_MAX_TEXT_CHARS} chars for LLM call")
    return text[:_MAX_TEXT_CHARS] + "\n...[truncated]"


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

    # ── Public entry point ────────────────────────────────────────────────────

    async def run(self, contract_id: str) -> None:
        """
        Run all four analysis jobs for a document.

        Pre-conditions:
          - Contract must be in status EXTRACTED. Any other status results
            in a no-op with a warning log.

        Post-conditions:
          - On success: status → ANALYZED, all four result sets persisted.
          - On failure: status → FAILED, partial results may be persisted.
        """
        logger.info(f"[analysis] Starting Phase 2 analysis for {contract_id}")

        # ── Guard: only run on extracted documents ────────────────────────────
        contract = await self._db.get_contract_by_id(contract_id)
        if not contract:
            logger.error(f"[analysis] Contract {contract_id} not found")
            return

        current_status = contract.get("status")
        if current_status not in (
            ContractStatus.EXTRACTED.value,
            ContractStatus.ANALYZED.value,   # allow re-analysis
            ContractStatus.PROCESSING.value, # endpoint may pre-set this before background task runs
        ):
            logger.warning(
                f"[analysis] Skipping {contract_id}: status is '{current_status}', "
                "expected 'extracted'"
            )
            return

        # ── Fetch text ────────────────────────────────────────────────────────
        text_record = await self._db.get_document_text(contract_id)
        if not text_record or not text_record.get("raw_text"):
            logger.error(f"[analysis] No extracted text for {contract_id}")
            await self._db.update_contract_status(contract_id, ContractStatus.FAILED)
            return

        text = _truncate(text_record["raw_text"])

        # ── Mark as processing ────────────────────────────────────────────────
        await self._db.update_contract_status(contract_id, ContractStatus.PROCESSING)

        try:
            entities = await self._extract_entities(text)
            summary = await self._generate_summary(text)
            risks = await self._detect_risks(text)
            missing = await self._detect_missing_clauses(text)

            # ── Persist to dedicated Phase 2 tables ──────────────────────────
            await self._db.save_contract_entities(contract_id, entities)
            await self._db.save_contract_summary(contract_id, summary)
            await self._db.save_contract_risks(contract_id, risks)
            await self._db.save_contract_gaps(contract_id, missing)

            # ── Also update contracts.extracted_data / contracts.analysis ─────
            # This keeps GET /contracts/{id} backward compatible with Phase 1
            # callers that read from ContractDetail.analysis.
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
                f"[analysis] Completed for {contract_id}: "
                f"{len(risks)} risks, {len(missing)} missing clauses"
            )

        except Exception as exc:
            logger.error(
                f"[analysis] Failed for {contract_id}: {exc}", exc_info=True
            )
            try:
                await self._db.update_contract_status(contract_id, ContractStatus.FAILED)
            except Exception:
                pass

    # ── Private analysis jobs ─────────────────────────────────────────────────

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

        # Validate each risk item has required keys
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

    # ── Helpers ───────────────────────────────────────────────────────────────

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
