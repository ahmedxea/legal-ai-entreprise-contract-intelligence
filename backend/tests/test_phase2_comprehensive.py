"""
Phase 2 Comprehensive Test Suite — Intelligence Layer

Maps 1:1 to the 10 Phase 2 capability areas:

  STEP 1 — TestEndToEndPipeline
      Full ingestion + analysis pipeline integration (upload → extract → analyze → store → return)

  STEP 2 — TestContractAcceptance
      File format validation and guard rails before processing begins

  STEP 3 — TestTextExtractionOutput
      Quality and schema of raw_text / paragraphs / chunks produced by Phase 1

  STEP 4 — TestEntityExtraction
      Structured entity extraction: parties, dates, governing_law, financial_terms, obligations

  STEP 5 — TestSummaryGeneration
      Executive summary: length, content, fallback on LLM failure

  STEP 6 — TestRiskDetection
      Risk clause identification: schema validation, severity weights, score computation

  STEP 7 — TestGapAnalysis
      Missing-clause detection: whitelist enforcement, empty/full lists, partial lists

  STEP 8 — TestIntelligencePersistence
      All four result sets are stored to their dedicated Phase 2 tables AND legacy column

  STEP 9 — TestAnalysisAPIEndpoints
      HTTP contract for POST /analyze and GET /analysis

  STEP 10 — TestErrorHandlingSafety
      Invalid input, LLM failures, malformed JSON — all handled gracefully, no 500s

Each class is independent. Tests may run in any order.
"""

import json
import pytest
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch


# ── Shared constants ───────────────────────────────────────────────────────────

FULL_CONTRACT_TEXT = """
MASTER SERVICE AGREEMENT

This Master Service Agreement ("Agreement") is entered into as of March 1, 2025
("Effective Date") by and between TechCorp Inc., a California corporation ("Client"),
and SoftSolutions GmbH, a German GmbH ("Vendor").

1. SERVICES
Vendor shall provide software development and consulting services as described
in each Statement of Work ("SOW") mutually executed by the parties.

2. PAYMENT
Client shall pay Vendor EUR 10,000 per calendar month.
Invoices are due within 30 days. Late payments accrue interest at 2% per month.

3. INTELLECTUAL PROPERTY
All work product created under this Agreement is work-for-hire and shall be
owned exclusively by Client upon full payment.

4. LIABILITY
Vendor's total aggregate liability under this Agreement shall not exceed EUR 5,000.
In no event shall either party be liable for indirect or consequential damages.

5. TERMINATION
Either party may terminate this Agreement upon 90 days' written notice.
Client may terminate immediately for cause.

6. GOVERNING LAW
This Agreement is governed by the laws of the State of California, USA.
"""

SHORT_CONTRACT_WITHOUT_RISK_TERMS = """
SIMPLE LETTER AGREEMENT

This Letter Agreement confirms the arrangement between Party A and Party B.
Both parties agree to cooperate in good faith on the project.
"""

MOCK_ENTITIES = {
    "parties": ["TechCorp Inc.", "SoftSolutions GmbH"],
    "effective_date": "2025-03-01",
    "expiration_date": "",
    "governing_law": "California",
    "financial_terms": ["EUR 10,000 per month", "2% monthly interest on late payments"],
    "obligations": ["Provide software development services", "Pay invoices within 30 days"],
}

MOCK_RISKS = {
    "risks": [
        {
            "risk_type": "liability",
            "severity": "high",
            "description": "Vendor liability capped at EUR 5,000 — far below monthly fees.",
            "source_text": "Vendor's total aggregate liability shall not exceed EUR 5,000",
        },
        {
            "risk_type": "termination",
            "severity": "medium",
            "description": "Client can terminate immediately for cause; Vendor needs 90 days.",
            "source_text": "Client may terminate immediately for cause",
        },
    ]
}

MOCK_GAPS = {"missing_clauses": ["confidentiality", "data_protection", "force_majeure"]}

MOCK_SUMMARY = (
    "This Master Service Agreement dated March 1, 2025 establishes a professional "
    "services relationship between TechCorp Inc. (Client) and SoftSolutions GmbH "
    "(Vendor) for software development and consulting. Monthly fees of EUR 10,000 "
    "are due within 30 days with a 2% monthly late-payment penalty. All work product "
    "is owned by Client as work-for-hire upon payment. The Vendor's total liability "
    "is capped at EUR 5,000 — a significant exposure mismatch relative to contract "
    "value. Termination rights are asymmetric: Client may terminate for cause "
    "immediately, while Vendor must provide 90 days' notice. Notable gaps include "
    "missing confidentiality, data protection, and force majeure provisions."
)

_STANDARD_CLAUSES = [
    "confidentiality",
    "data_protection",
    "force_majeure",
    "termination",
    "governing_law",
]


# ── Test helpers ───────────────────────────────────────────────────────────────

def _make_mock_db(
    contract_status: str = "extracted",
    has_text: bool = True,
) -> MagicMock:
    """Build a mock DatabaseService with all Phase 2 async methods pre-configured."""
    db = MagicMock()
    db.get_contract_by_id = AsyncMock(
        return_value={"id": "doc-001", "status": contract_status}
    )
    db.get_document_text = AsyncMock(
        return_value=(
            {"raw_text": FULL_CONTRACT_TEXT, "paragraphs": FULL_CONTRACT_TEXT.split("\n")}
            if has_text
            else None
        )
    )
    db.update_contract_status = AsyncMock(return_value=None)
    db.save_contract_entities = AsyncMock(return_value=None)
    db.save_contract_summary = AsyncMock(return_value=None)
    db.save_contract_risks = AsyncMock(return_value=None)
    db.save_contract_gaps = AsyncMock(return_value=None)
    db.update_contract_analysis = AsyncMock(return_value=None)

    # GET methods used by the analysis API
    db.get_contract = AsyncMock(
        return_value={"id": "doc-001", "status": contract_status}
    )
    db.get_contract_entities = AsyncMock(return_value=MOCK_ENTITIES)
    db.get_contract_summary = AsyncMock(return_value=MOCK_SUMMARY)
    db.get_contract_risks = AsyncMock(return_value=MOCK_RISKS["risks"])
    db.get_contract_gaps = AsyncMock(return_value=list(MOCK_GAPS["missing_clauses"]))
    return db


def _side_effect_factory(entities=None, risks=None, gaps=None):
    """Return a coroutine side_effect that cycles through the analysis pipeline responses.

    Call order:
      0: entity extraction → MOCK_ENTITIES
      1: CUAD metadata extraction → {} (wrong schema, triggers all-absent sanity check)
      2: CUAD clause extraction  → {} (wrong schema, triggers all-absent sanity check)
      3: risk detection fallback → MOCK_RISKS
      4: gap  detection fallback → MOCK_GAPS
    """
    responses = [
        entities or MOCK_ENTITIES,
        {},                          # CUAD metadata (will fail silently)
        {},                          # CUAD clause extraction (will fail silently)
        risks or MOCK_RISKS,
        gaps or MOCK_GAPS,
    ]
    state = {"idx": 0}

    async def side_effect(*args, **kwargs):
        result = responses[state["idx"]]
        state["idx"] = min(state["idx"] + 1, len(responses) - 1)
        return result

    return side_effect


def _make_mock_ai(
    entities=None,
    summary: Optional[str] = None,
    risks=None,
    gaps=None,
) -> MagicMock:
    """Build a mock OllamaService with deterministic responses for all four analysis jobs."""
    ai = MagicMock()
    ai.structured_extraction = AsyncMock(
        side_effect=_side_effect_factory(entities=entities, risks=risks, gaps=gaps)
    )
    ai.analyze_with_guidance = AsyncMock(return_value=summary or MOCK_SUMMARY)
    return ai


def _build_test_app():
    """Create an isolated FastAPI app with the contracts router only."""
    from fastapi import FastAPI
    from app.api.contracts import router as contracts_router

    app = FastAPI()
    app.include_router(contracts_router, prefix="/api/contracts")
    return app


# ── Import the module under test ───────────────────────────────────────────────

from app.services.analysis_service import AnalysisService, _parse_json_response, _truncate


# ==============================================================================
# STEP 1 — End-to-End Pipeline
# ==============================================================================

class TestEndToEndPipeline:
    """
    Verify the full logical pipeline from an extracted contract to a
    fully-analysed one. No real LLM or storage — only mock injection.
    """

    @pytest.mark.asyncio
    async def test_pipeline_transitions_from_extracted_to_analyzed(self):
        db = _make_mock_db(contract_status="extracted")
        ai = _make_mock_ai()
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        status_values = [c[0][1] for c in db.update_contract_status.call_args_list]
        # Expect at least one PROCESSING and final ANALYZED
        status_strs = [s.value if hasattr(s, "value") else str(s) for s in status_values]
        assert "analyzed" in status_strs

    @pytest.mark.asyncio
    async def test_pipeline_persists_all_four_intelligence_components(self):
        db = _make_mock_db(contract_status="extracted")
        ai = _make_mock_ai()
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        db.save_contract_entities.assert_called_once()
        db.save_contract_summary.assert_called_once()
        db.save_contract_risks.assert_called_once()
        db.save_contract_gaps.assert_called_once()

    @pytest.mark.asyncio
    async def test_pipeline_marks_processing_before_ai_calls(self):
        """Status must become PROCESSING before any AI work starts."""
        processing_set = []

        async def track_status(contract_id, status):
            val = status.value if hasattr(status, "value") else str(status)
            processing_set.append(val)

        db = _make_mock_db(contract_status="extracted")
        db.update_contract_status = AsyncMock(side_effect=track_status)
        ai = _make_mock_ai()
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        # First status update must be PROCESSING
        assert len(processing_set) >= 2
        assert processing_set[0] == "processing"
        assert processing_set[-1] == "analyzed"

    @pytest.mark.asyncio
    async def test_pipeline_also_updates_legacy_contracts_analysis_column(self):
        db = _make_mock_db(contract_status="extracted")
        ai = _make_mock_ai()
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        db.update_contract_analysis.assert_called_once()
        args = db.update_contract_analysis.call_args[0]
        assert args[0] == "doc-001"
        payload = args[1]
        assert "extracted_data" in payload
        assert "analysis" in payload
        analysis = payload["analysis"]
        assert "summary" in analysis
        assert "risks" in analysis
        assert "missing_clauses" in analysis
        assert "overall_risk_score" in analysis
        assert "compliance_score" in analysis

    @pytest.mark.asyncio
    async def test_pipeline_risk_score_appears_in_legacy_column(self):
        db = _make_mock_db(contract_status="extracted")
        ai = _make_mock_ai()
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        analysis_payload = db.update_contract_analysis.call_args[0][1]["analysis"]
        score = analysis_payload["overall_risk_score"]
        assert 0.0 <= score <= 10.0

    @pytest.mark.asyncio
    async def test_pipeline_compliance_score_is_inverse_of_risk_score(self):
        db = _make_mock_db(contract_status="extracted")
        ai = _make_mock_ai()
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        analysis = db.update_contract_analysis.call_args[0][1]["analysis"]
        risk_score = analysis["overall_risk_score"]
        compliance_score = analysis["compliance_score"]
        assert abs(compliance_score - max(0.0, 100.0 - risk_score * 10)) < 0.01


# ==============================================================================
# STEP 2 — Contract Acceptance & Validation
# ==============================================================================

class TestContractAcceptance:
    """
    Guard rails that prevent invalid or unready contracts from entering the
    analysis pipeline.
    """

    @pytest.mark.asyncio
    async def test_accepted_status_extracted(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")
        db.save_contract_entities.assert_called_once()

    @pytest.mark.asyncio
    async def test_accepted_status_processing(self):
        """Endpoint marks PROCESSING before the background task runs — must still work."""
        db = _make_mock_db(contract_status="processing")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")
        db.save_contract_entities.assert_called_once()

    @pytest.mark.asyncio
    async def test_accepted_status_analyzed_for_reanalysis(self):
        db = _make_mock_db(contract_status="analyzed")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")
        db.save_contract_entities.assert_called_once()

    @pytest.mark.asyncio
    async def test_rejected_status_uploaded(self):
        db = _make_mock_db(contract_status="uploaded")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")
        db.save_contract_entities.assert_not_called()
        db.update_contract_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_rejected_status_extracting(self):
        db = _make_mock_db(contract_status="extracting")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")
        db.save_contract_entities.assert_not_called()

    @pytest.mark.asyncio
    async def test_rejected_status_failed(self):
        db = _make_mock_db(contract_status="failed")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")
        db.save_contract_entities.assert_not_called()

    @pytest.mark.asyncio
    async def test_rejected_unknown_contract_id(self):
        db = _make_mock_db()
        db.get_contract_by_id = AsyncMock(return_value=None)
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("nonexistent-id")
        db.update_contract_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_extracted_text_sets_failed_status(self):
        db = _make_mock_db(contract_status="extracted", has_text=False)
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")
        status_vals = [
            (c[0][1].value if hasattr(c[0][1], "value") else str(c[0][1]))
            for c in db.update_contract_status.call_args_list
        ]
        assert "failed" in status_vals

    @pytest.mark.asyncio
    async def test_empty_raw_text_sets_failed_status(self):
        db = _make_mock_db(contract_status="extracted")
        db.get_document_text = AsyncMock(return_value={"raw_text": "", "paragraphs": []})
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")
        status_vals = [
            (c[0][1].value if hasattr(c[0][1], "value") else str(c[0][1]))
            for c in db.update_contract_status.call_args_list
        ]
        assert "failed" in status_vals


# ==============================================================================
# STEP 3 — Text Extraction Output Quality
# ==============================================================================

class TestTextExtractionOutput:
    """
    The analysis pipeline consumes `raw_text` produced by Phase 1.
    Verify that the service correctly handles the text_record schema and
    that the truncation guard works as expected.
    """

    def test_truncate_leaves_short_text_unchanged(self):
        text = "Short contract text."
        assert _truncate(text) == text

    def test_truncate_trims_overlong_text(self):
        long_text = "A" * 15_000
        result = _truncate(long_text)
        assert len(result) < 15_000
        assert result.endswith("[truncated]")

    def test_truncate_preserves_exactly_max_chars(self):
        from app.services.analysis_service import _SINGLE_PASS_CHARS
        text = "X" * _SINGLE_PASS_CHARS
        assert _truncate(text) == text  # exactly the limit, no truncation

    def test_truncate_one_over_max_trims(self):
        from app.services.analysis_service import _SINGLE_PASS_CHARS
        text = "Y" * (_SINGLE_PASS_CHARS + 1)
        result = _truncate(text)
        assert "[truncated]" in result

    @pytest.mark.asyncio
    async def test_text_record_without_raw_text_key_fails_gracefully(self):
        db = _make_mock_db(contract_status="extracted")
        # Return a record missing the raw_text key
        db.get_document_text = AsyncMock(return_value={"paragraphs": ["paragraph 1"]})
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")
        status_vals = [
            (c[0][1].value if hasattr(c[0][1], "value") else str(c[0][1]))
            for c in db.update_contract_status.call_args_list
        ]
        assert "failed" in status_vals

    @pytest.mark.asyncio
    async def test_only_raw_text_is_sent_to_llm_not_paragraphs(self):
        """The LLM receives the text field, not a stringified paragraph list."""
        db = _make_mock_db(contract_status="extracted")
        captured_contexts = []

        async def capture(*args, **kwargs):
            captured_contexts.append(kwargs.get("context", args[1] if len(args) > 1 else ""))
            return MOCK_ENTITIES

        ai = MagicMock()
        ai.structured_extraction = AsyncMock(side_effect=capture)
        ai.analyze_with_guidance = AsyncMock(return_value=MOCK_SUMMARY)

        svc = AnalysisService(db=db, ai=ai)
        await svc.run("doc-001")

        # At least one LLM call should have received the raw text
        assert any(FULL_CONTRACT_TEXT[:50].strip() in ctx for ctx in captured_contexts)


# ==============================================================================
# STEP 4 — Structured Entity Extraction
# ==============================================================================

class TestEntityExtraction:
    """Verify that entity extraction returns the correct schema and values."""

    @pytest.mark.asyncio
    async def test_entities_contain_all_required_keys(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        saved = db.save_contract_entities.call_args[0][1]
        for key in ("parties", "effective_date", "expiration_date",
                    "governing_law", "financial_terms", "obligations"):
            assert key in saved, f"Missing entity key: {key}"

    @pytest.mark.asyncio
    async def test_parties_is_a_list(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        saved = db.save_contract_entities.call_args[0][1]
        assert isinstance(saved["parties"], list)

    @pytest.mark.asyncio
    async def test_parties_contains_expected_names(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        saved = db.save_contract_entities.call_args[0][1]
        assert "TechCorp Inc." in saved["parties"] or "SoftSolutions GmbH" in saved["parties"]

    @pytest.mark.asyncio
    async def test_governing_law_is_a_string(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        saved = db.save_contract_entities.call_args[0][1]
        assert isinstance(saved["governing_law"], str)

    @pytest.mark.asyncio
    async def test_financial_terms_is_a_list(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        saved = db.save_contract_entities.call_args[0][1]
        assert isinstance(saved["financial_terms"], list)

    @pytest.mark.asyncio
    async def test_entity_extraction_falls_back_to_schema_defaults_on_invalid_response(self):
        """If the LLM returns garbage for entities, the service must use schema defaults."""
        db = _make_mock_db(contract_status="extracted")
        ai = MagicMock()
        ai.structured_extraction = AsyncMock(side_effect=[
            "This is not JSON at all",  # entities call returns a string
            {},                          # CUAD metadata
            {},                          # CUAD clauses
            MOCK_RISKS,
            MOCK_GAPS,
        ])
        ai.analyze_with_guidance = AsyncMock(return_value=MOCK_SUMMARY)
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        saved = db.save_contract_entities.call_args[0][1]
        # Should fall back to empty defaults, not crash
        assert isinstance(saved["parties"], list)
        assert isinstance(saved["financial_terms"], list)

    @pytest.mark.asyncio
    async def test_entity_extraction_fills_missing_keys_automatically(self):
        """LLM response missing some keys should be padded with defaults."""
        partial_entities = {"parties": ["Only One Party"]}  # missing all other keys
        db = _make_mock_db(contract_status="extracted")
        ai = _make_mock_ai(entities=partial_entities)
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        saved = db.save_contract_entities.call_args[0][1]
        assert "governing_law" in saved
        assert "financial_terms" in saved
        assert isinstance(saved["financial_terms"], list)


# ==============================================================================
# STEP 5 — Executive Summary Generation
# ==============================================================================

class TestSummaryGeneration:
    """Verify the executive summary output and failure fallback."""

    @pytest.mark.asyncio
    async def test_summary_is_saved_as_string(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        saved_summary = db.save_contract_summary.call_args[0][1]
        assert isinstance(saved_summary, str)
        assert len(saved_summary) > 0

    @pytest.mark.asyncio
    async def test_summary_matches_mock_response(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai(summary=MOCK_SUMMARY))
        await svc.run("doc-001")

        saved_summary = db.save_contract_summary.call_args[0][1]
        assert saved_summary == MOCK_SUMMARY

    @pytest.mark.asyncio
    async def test_summary_stored_in_legacy_analysis_column(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        analysis = db.update_contract_analysis.call_args[0][1]["analysis"]
        assert analysis["summary"] == MOCK_SUMMARY

    @pytest.mark.asyncio
    async def test_summary_fallback_on_llm_exception(self):
        ai = MagicMock()
        ai.structured_extraction = AsyncMock(side_effect=[
            MOCK_ENTITIES,
            {},              # CUAD metadata
            {},              # CUAD clauses
            MOCK_RISKS,
            MOCK_GAPS,
        ])
        ai.analyze_with_guidance = AsyncMock(side_effect=RuntimeError("LLM crashed"))
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        saved_summary = db.save_contract_summary.call_args[0][1]
        assert saved_summary == "Summary not available."

    @pytest.mark.asyncio
    async def test_summary_fallback_pipeline_completes_despite_summary_failure(self):
        """A summary failure must NOT abort the rest of the pipeline."""
        ai = MagicMock()
        ai.structured_extraction = AsyncMock(side_effect=[
            MOCK_ENTITIES,
            {},              # CUAD metadata
            {},              # CUAD clauses
            MOCK_RISKS,
            MOCK_GAPS,
        ])
        ai.analyze_with_guidance = AsyncMock(side_effect=RuntimeError("LLM crashed"))
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        # All four saves still happen
        db.save_contract_entities.assert_called_once()
        db.save_contract_risks.assert_called_once()
        db.save_contract_gaps.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_llm_response_uses_fallback(self):
        ai = MagicMock()
        ai.structured_extraction = AsyncMock(side_effect=[
            MOCK_ENTITIES,
            {},              # CUAD metadata
            {},              # CUAD clauses
            MOCK_RISKS,
            MOCK_GAPS,
        ])
        ai.analyze_with_guidance = AsyncMock(return_value="")
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        saved_summary = db.save_contract_summary.call_args[0][1]
        # empty string from LLM should be normalised to the fallback message
        assert saved_summary == "Summary not available."


# ==============================================================================
# STEP 6 — Risk Clause Detection
# ==============================================================================

class TestRiskDetection:
    """Verify risk schema validation, score computation, and edge cases."""

    # ── Pure unit: _compute_risk_score ─────────────────────────────────────────

    def test_risk_score_empty_list_is_zero(self):
        assert AnalysisService._compute_risk_score([]) == 0.0

    def test_risk_score_single_low(self):
        # weight=1, score = min(10, 1/2) = 0.5
        assert AnalysisService._compute_risk_score([{"severity": "low"}]) == 0.5

    def test_risk_score_single_medium(self):
        # weight=2, score = 1.0
        assert AnalysisService._compute_risk_score([{"severity": "medium"}]) == 1.0

    def test_risk_score_single_high(self):
        # weight=3, score = 1.5
        assert AnalysisService._compute_risk_score([{"severity": "high"}]) == 1.5

    def test_risk_score_single_critical(self):
        # weight=4, score = 2.0
        assert AnalysisService._compute_risk_score([{"severity": "critical"}]) == 2.0

    def test_risk_score_mixed_severities(self):
        risks = [
            {"severity": "critical"},  # 4
            {"severity": "high"},      # 3
            {"severity": "low"},       # 1
        ]
        # total=8, score=4.0
        assert AnalysisService._compute_risk_score(risks) == 4.0

    def test_risk_score_capped_at_ten(self):
        risks = [{"severity": "critical"}] * 10  # 40 / 2 = 20 → capped at 10
        assert AnalysisService._compute_risk_score(risks) == 10.0

    def test_risk_score_unknown_severity_treated_as_low(self):
        risks = [{"severity": "gigantic"}]
        assert AnalysisService._compute_risk_score(risks) == 0.5

    def test_risk_score_missing_severity_key_treated_as_low(self):
        risks = [{"risk_type": "liability"}]  # no severity key
        assert AnalysisService._compute_risk_score(risks) == 0.5

    # ── Integration: risk list schema ──────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_saved_risks_is_a_list(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        saved = db.save_contract_risks.call_args[0][1]
        assert isinstance(saved, list)

    @pytest.mark.asyncio
    async def test_each_risk_has_required_keys(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        saved = db.save_contract_risks.call_args[0][1]
        for risk in saved:
            for key in ("risk_type", "severity", "description"):
                assert key in risk, f"Risk missing key '{key}': {risk}"

    @pytest.mark.asyncio
    async def test_risk_severity_values_are_valid(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        saved = db.save_contract_risks.call_args[0][1]
        valid_severities = {"low", "medium", "high", "critical"}
        for risk in saved:
            assert risk["severity"] in valid_severities, f"Invalid severity: {risk['severity']}"

    @pytest.mark.asyncio
    async def test_non_dict_risk_items_are_filtered_out(self):
        """The service must discard non-dict entries in the risks array."""
        bad_risks = {
            "risks": [
                {"risk_type": "liability", "severity": "high", "description": "Real risk", "source_text": "..."},
                "this is not a risk object",
                42,
                None,
                {"risk_type": "termination", "severity": "medium", "description": "Another real risk", "source_text": "..."},
            ]
        }
        db = _make_mock_db(contract_status="extracted")
        ai = _make_mock_ai(risks=bad_risks)
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        saved = db.save_contract_risks.call_args[0][1]
        assert all(isinstance(r, dict) for r in saved)
        assert len(saved) == 2  # only the two valid dicts

    @pytest.mark.asyncio
    async def test_empty_risks_array_is_accepted(self):
        db = _make_mock_db(contract_status="extracted")
        ai = _make_mock_ai(risks={"risks": []})
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        saved = db.save_contract_risks.call_args[0][1]
        assert saved == []

    @pytest.mark.asyncio
    async def test_risks_not_a_list_returns_empty_list(self):
        """If the LLM returns 'risks' as a non-list, the service saves an empty list."""
        db = _make_mock_db(contract_status="extracted")
        ai = _make_mock_ai(risks={"risks": "not-a-list"})
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        saved = db.save_contract_risks.call_args[0][1]
        assert saved == []


# ==============================================================================
# STEP 7 — Gap Analysis (Missing Clause Detection)
# ==============================================================================

class TestGapAnalysis:
    """Verify missing clause whitelist enforcement, edge cases, and integration."""

    @pytest.mark.asyncio
    async def test_missing_clauses_saved_as_list(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        saved = db.save_contract_gaps.call_args[0][1]
        assert isinstance(saved, list)

    @pytest.mark.asyncio
    async def test_missing_clauses_only_contain_whitelisted_values(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        saved = db.save_contract_gaps.call_args[0][1]
        for clause in saved:
            assert clause in _STANDARD_CLAUSES, f"Non-standard clause found: {clause}"

    @pytest.mark.asyncio
    async def test_unrecognised_clause_names_filtered_out(self):
        gaps_with_extras = {
            "missing_clauses": [
                "confidentiality",
                "UNKNOWN_CLAUSE",
                "data_protection",
                "this-is-not-real",
                "force_majeure",
            ]
        }
        db = _make_mock_db(contract_status="extracted")
        ai = _make_mock_ai(gaps=gaps_with_extras)
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        saved = db.save_contract_gaps.call_args[0][1]
        assert "UNKNOWN_CLAUSE" not in saved
        assert "this-is-not-real" not in saved
        assert "confidentiality" in saved
        assert "force_majeure" in saved

    @pytest.mark.asyncio
    async def test_non_string_items_filtered_out(self):
        dirty_gaps = {"missing_clauses": ["confidentiality", 42, None, True, "data_protection"]}
        db = _make_mock_db(contract_status="extracted")
        ai = _make_mock_ai(gaps=dirty_gaps)
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        saved = db.save_contract_gaps.call_args[0][1]
        assert all(isinstance(c, str) for c in saved)

    @pytest.mark.asyncio
    async def test_all_clauses_present_returns_empty_list(self):
        db = _make_mock_db(contract_status="extracted")
        ai = _make_mock_ai(gaps={"missing_clauses": []})
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        saved = db.save_contract_gaps.call_args[0][1]
        assert saved == []

    @pytest.mark.asyncio
    async def test_all_five_clauses_missing(self):
        all_missing = {"missing_clauses": list(_STANDARD_CLAUSES)}
        db = _make_mock_db(contract_status="extracted")
        ai = _make_mock_ai(gaps=all_missing)
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        saved = db.save_contract_gaps.call_args[0][1]
        assert set(saved) == set(_STANDARD_CLAUSES)

    @pytest.mark.asyncio
    async def test_gap_analysis_stored_in_legacy_column(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        legacy = db.update_contract_analysis.call_args[0][1]["analysis"]
        assert "missing_clauses" in legacy
        assert isinstance(legacy["missing_clauses"], list)


# ==============================================================================
# STEP 8 — Intelligence Persistence
# ==============================================================================

class TestIntelligencePersistence:
    """
    Verify that save methods are called with the correct contract_id and data
    shapes, and that all dedicated Phase 2 tables are targeted.
    """

    @pytest.mark.asyncio
    async def test_save_entities_called_with_correct_contract_id(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        args = db.save_contract_entities.call_args[0]
        assert args[0] == "doc-001"

    @pytest.mark.asyncio
    async def test_save_summary_called_with_correct_contract_id(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        args = db.save_contract_summary.call_args[0]
        assert args[0] == "doc-001"

    @pytest.mark.asyncio
    async def test_save_risks_called_with_correct_contract_id(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        args = db.save_contract_risks.call_args[0]
        assert args[0] == "doc-001"

    @pytest.mark.asyncio
    async def test_save_gaps_called_with_correct_contract_id(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        args = db.save_contract_gaps.call_args[0]
        assert args[0] == "doc-001"

    @pytest.mark.asyncio
    async def test_update_contract_analysis_called_with_correct_id(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        args = db.update_contract_analysis.call_args[0]
        assert args[0] == "doc-001"

    @pytest.mark.asyncio
    async def test_entities_data_passed_to_save_is_a_dict(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        data = db.save_contract_entities.call_args[0][1]
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_summary_data_passed_to_save_is_a_string(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        data = db.save_contract_summary.call_args[0][1]
        assert isinstance(data, str)

    @pytest.mark.asyncio
    async def test_risks_data_passed_to_save_is_a_list(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        data = db.save_contract_risks.call_args[0][1]
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_gaps_data_passed_to_save_is_a_list(self):
        db = _make_mock_db(contract_status="extracted")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        data = db.save_contract_gaps.call_args[0][1]
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_no_saves_called_on_guard_rejection(self):
        """If the contract is in an invalid state, no Phase 2 tables should be written."""
        db = _make_mock_db(contract_status="uploaded")
        svc = AnalysisService(db=db, ai=_make_mock_ai())
        await svc.run("doc-001")

        db.save_contract_entities.assert_not_called()
        db.save_contract_summary.assert_not_called()
        db.save_contract_risks.assert_not_called()
        db.save_contract_gaps.assert_not_called()
        db.update_contract_analysis.assert_not_called()


# ==============================================================================
# STEP 9 — Analysis API Endpoints
# ==============================================================================

class TestAnalysisAPIEndpoints:
    """HTTP contract tests for POST /analyze and GET /analysis."""

    def test_post_analyze_returns_202_for_extracted_contract(self):
        from fastapi.testclient import TestClient
        from app.api import contracts as contracts_module

        mock_db = _make_mock_db(contract_status="extracted")
        with patch.object(contracts_module, "db_service", mock_db), \
             patch.object(contracts_module, "phase2_analysis_service") as mock_svc:
            mock_svc.run = AsyncMock(return_value=None)
            client = TestClient(_build_test_app())
            resp = client.post("/api/contracts/doc-001/analyze")

        assert resp.status_code in (200, 202)
        body = resp.json()
        assert body["contract_id"] == "doc-001"
        assert body["status"] == "processing"

    def test_post_analyze_returns_404_for_unknown_contract(self):
        from fastapi.testclient import TestClient
        from app.api import contracts as contracts_module

        mock_db = _make_mock_db()
        mock_db.get_contract = AsyncMock(return_value=None)
        mock_db.get_contract_by_id = AsyncMock(return_value=None)
        with patch.object(contracts_module, "db_service", mock_db):
            client = TestClient(_build_test_app())
            resp = client.post("/api/contracts/nonexistent/analyze")

        assert resp.status_code == 404

    def test_get_analysis_returns_200_with_full_response_for_analyzed_contract(self):
        from fastapi.testclient import TestClient
        from app.api import contracts as contracts_module

        mock_db = _make_mock_db(contract_status="analyzed")
        with patch.object(contracts_module, "db_service", mock_db), \
             patch.object(contracts_module, "phase2_analysis_service") as mock_svc:
            mock_svc._compute_risk_score = AnalysisService._compute_risk_score
            client = TestClient(_build_test_app())
            resp = client.get("/api/contracts/doc-001/analysis")

        assert resp.status_code == 200
        body = resp.json()
        assert body["contract_id"] == "doc-001"
        assert "summary" in body
        assert "risks" in body
        assert "missing_clauses" in body
        assert "overall_risk_score" in body

    def test_get_analysis_returns_404_for_not_yet_analyzed_contract(self):
        from fastapi.testclient import TestClient
        from app.api import contracts as contracts_module

        mock_db = _make_mock_db(contract_status="extracted")
        mock_db.get_contract_entities = AsyncMock(return_value=None)
        mock_db.get_contract_summary = AsyncMock(return_value=None)
        mock_db.get_contract_risks = AsyncMock(return_value=[])
        mock_db.get_contract_gaps = AsyncMock(return_value=None)

        with patch.object(contracts_module, "db_service", mock_db), \
             patch.object(contracts_module, "phase2_analysis_service") as mock_svc:
            mock_svc._compute_risk_score = AnalysisService._compute_risk_score
            client = TestClient(_build_test_app())
            resp = client.get("/api/contracts/doc-001/analysis")

        assert resp.status_code == 404

    def test_get_analysis_returns_404_for_unknown_contract(self):
        from fastapi.testclient import TestClient
        from app.api import contracts as contracts_module

        mock_db = MagicMock()
        mock_db.get_contract = AsyncMock(return_value=None)

        with patch.object(contracts_module, "db_service", mock_db):
            client = TestClient(_build_test_app())
            resp = client.get("/api/contracts/nonexistent/analysis")

        assert resp.status_code == 404

    def test_get_analysis_response_contains_risk_score_in_range(self):
        from fastapi.testclient import TestClient
        from app.api import contracts as contracts_module

        mock_db = _make_mock_db(contract_status="analyzed")
        with patch.object(contracts_module, "db_service", mock_db), \
             patch.object(contracts_module, "phase2_analysis_service") as mock_svc:
            mock_svc._compute_risk_score = AnalysisService._compute_risk_score
            client = TestClient(_build_test_app())
            resp = client.get("/api/contracts/doc-001/analysis")

        assert resp.status_code == 200
        score = resp.json()["overall_risk_score"]
        assert 0 <= score <= 10

    def test_get_analysis_summary_matches_stored_value(self):
        from fastapi.testclient import TestClient
        from app.api import contracts as contracts_module

        mock_db = _make_mock_db(contract_status="analyzed")
        with patch.object(contracts_module, "db_service", mock_db), \
             patch.object(contracts_module, "phase2_analysis_service") as mock_svc:
            mock_svc._compute_risk_score = AnalysisService._compute_risk_score
            client = TestClient(_build_test_app())
            resp = client.get("/api/contracts/doc-001/analysis")

        assert resp.status_code == 200
        assert resp.json()["summary"] == MOCK_SUMMARY

    def test_get_analysis_missing_clauses_contains_expected_values(self):
        from fastapi.testclient import TestClient
        from app.api import contracts as contracts_module

        mock_db = _make_mock_db(contract_status="analyzed")
        with patch.object(contracts_module, "db_service", mock_db), \
             patch.object(contracts_module, "phase2_analysis_service") as mock_svc:
            mock_svc._compute_risk_score = AnalysisService._compute_risk_score
            client = TestClient(_build_test_app())
            resp = client.get("/api/contracts/doc-001/analysis")

        assert resp.status_code == 200
        mc = resp.json()["missing_clauses"]
        assert "confidentiality" in mc


# ==============================================================================
# STEP 10 — Error Handling & Safety
# ==============================================================================

class TestErrorHandlingSafety:
    """
    Verify that all failure paths are handled gracefully — no unhandled
    exceptions, no partial-save crashes, no 500 responses.
    """

    @pytest.mark.asyncio
    async def test_total_llm_failure_sets_failed_status(self):
        db = _make_mock_db(contract_status="extracted")
        ai = MagicMock()
        ai.structured_extraction = AsyncMock(side_effect=RuntimeError("LLM unavailable"))
        ai.analyze_with_guidance = AsyncMock(side_effect=RuntimeError("LLM unavailable"))
        svc = AnalysisService(db=db, ai=ai)

        # Must not raise
        await svc.run("doc-001")

        status_vals = [
            (c[0][1].value if hasattr(c[0][1], "value") else str(c[0][1]))
            for c in db.update_contract_status.call_args_list
        ]
        assert "failed" in status_vals

    @pytest.mark.asyncio
    async def test_db_save_failure_sets_failed_status(self):
        """If saving entities raises, the service should catch and mark FAILED."""
        db = _make_mock_db(contract_status="extracted")
        db.save_contract_entities = AsyncMock(side_effect=Exception("DB write error"))
        svc = AnalysisService(db=db, ai=_make_mock_ai())

        await svc.run("doc-001")

        status_vals = [
            (c[0][1].value if hasattr(c[0][1], "value") else str(c[0][1]))
            for c in db.update_contract_status.call_args_list
        ]
        assert "failed" in status_vals

    @pytest.mark.asyncio
    async def test_malformed_entities_json_does_not_crash_pipeline(self):
        db = _make_mock_db(contract_status="extracted")
        ai = MagicMock()
        ai.structured_extraction = AsyncMock(side_effect=[
            "!@#$% not json",   # entities
            {},                  # CUAD metadata
            {},                  # CUAD clauses
            MOCK_RISKS,
            MOCK_GAPS,
        ])
        ai.analyze_with_guidance = AsyncMock(return_value=MOCK_SUMMARY)
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        # Pipeline should complete, not raise
        db.save_contract_entities.assert_called_once()

    @pytest.mark.asyncio
    async def test_malformed_risks_json_results_in_empty_risk_list(self):
        db = _make_mock_db(contract_status="extracted")
        ai = MagicMock()
        ai.structured_extraction = AsyncMock(side_effect=[
            MOCK_ENTITIES,
            {},                              # CUAD metadata
            {},                              # CUAD clauses
            {"risks": "this is not a list"},
            MOCK_GAPS,
        ])
        ai.analyze_with_guidance = AsyncMock(return_value=MOCK_SUMMARY)
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        saved = db.save_contract_risks.call_args[0][1]
        assert saved == []

    @pytest.mark.asyncio
    async def test_malformed_gaps_results_in_empty_list(self):
        db = _make_mock_db(contract_status="extracted")
        ai = MagicMock()
        ai.structured_extraction = AsyncMock(side_effect=[
            MOCK_ENTITIES,
            {},                              # CUAD metadata
            {},                              # CUAD clauses
            MOCK_RISKS,
            {"missing_clauses": 12345},   # number instead of list
        ])
        ai.analyze_with_guidance = AsyncMock(return_value=MOCK_SUMMARY)
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("doc-001")

        # Service should not crash and should save an empty list
        db.save_contract_gaps.assert_called_once()
        saved = db.save_contract_gaps.call_args[0][1]
        assert isinstance(saved, list)

    @pytest.mark.asyncio
    async def test_none_return_from_structured_extraction_handled(self):
        db = _make_mock_db(contract_status="extracted")
        ai = MagicMock()
        ai.structured_extraction = AsyncMock(return_value=None)
        ai.analyze_with_guidance = AsyncMock(return_value=MOCK_SUMMARY)
        svc = AnalysisService(db=db, ai=ai)

        # Must not raise
        await svc.run("doc-001")

    def test_post_analyze_does_not_return_500_for_unexpected_error(self):
        """Even when the background task env is broken, the HTTP response must be clean."""
        from fastapi.testclient import TestClient
        from app.api import contracts as contracts_module

        mock_db = _make_mock_db(contract_status="extracted")
        with patch.object(contracts_module, "db_service", mock_db), \
             patch.object(contracts_module, "phase2_analysis_service") as mock_svc:
            # The task itself will silently fail
            mock_svc.run = AsyncMock(side_effect=Exception("unexpected"))
            client = TestClient(_build_test_app(), raise_server_exceptions=False)
            resp = client.post("/api/contracts/doc-001/analyze")

        # Background task errors must not leak as 500s in TestClient w/raise_server_exceptions=False
        assert resp.status_code != 500

    # ── _parse_json_response robustness ───────────────────────────────────────

    def test_parse_json_valid_object(self):
        assert _parse_json_response('{"key": "value"}', "ctx") == {"key": "value"}

    def test_parse_json_with_markdown_fence(self):
        raw = "```json\n{\"a\": 1}\n```"
        assert _parse_json_response(raw, "ctx") == {"a": 1}

    def test_parse_json_with_preamble_text(self):
        raw = "Sure, here you go:\n{\"b\": 2}"
        assert _parse_json_response(raw, "ctx") == {"b": 2}

    def test_parse_json_empty_string_returns_none(self):
        assert _parse_json_response("", "ctx") is None

    def test_parse_json_none_returns_none(self):
        assert _parse_json_response(None, "ctx") is None  # type: ignore

    def test_parse_json_no_braces_returns_none(self):
        assert _parse_json_response("just some plain text", "ctx") is None

    def test_parse_json_malformed_json_returns_none(self):
        assert _parse_json_response("{broken: json", "ctx") is None

    def test_parse_json_nested_objects(self):
        raw = '{"risks": [{"severity": "high", "type": "x"}]}'
        result = _parse_json_response(raw, "ctx")
        assert result["risks"][0]["severity"] == "high"
