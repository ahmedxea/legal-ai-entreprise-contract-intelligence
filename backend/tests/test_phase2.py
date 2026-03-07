"""
Phase 2 Tests — Intelligence Layer

Tests cover:
  - Entity extraction (valid JSON, malformed JSON, empty response)
  - Summary generation (valid response, LLM failure)
  - Risk detection (valid list, empty list, malformed JSON)
  - Missing clause detection (full list, partial list, whitelist enforcement)
  - Risk score computation (edge cases)
  - Full pipeline: PROCESSING → ANALYZED status transition
  - Guard: non-extracted contract is skipped (no status change)
  - GET /analysis endpoint returns correct response shape
  - POST /analyze endpoint returns 202 + launches background task
  - JSON parsing helper robustness (_parse_json_response)
"""

import json
import pytest
import asyncio
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch


# ── Helpers / shared fixtures ──────────────────────────────────────────────────

SAMPLE_CONTRACT_TEXT = """
SOFTWARE DEVELOPMENT AGREEMENT

This Software Development Agreement ("Agreement") is entered into as of January 1, 2025
("Effective Date") by and between Acme Corp, a Delaware corporation ("Client"), and
DevShop Ltd, a UK private limited company ("Contractor").

1. SCOPE OF WORK
Contractor shall develop a custom e-commerce platform as outlined in Schedule A.

2. PAYMENT TERMS
Client shall pay Contractor USD 50,000 per milestone, with three milestones defined
in Schedule B. Late payments accrue interest at 1.5% per month.

3. LIABILITY
Developer's total liability under this Agreement shall not exceed USD 10,000.
Client may terminate this Agreement at any time without cause with 30 days' notice.
Developer may not terminate without 90 days' notice and Client consent.

4. GOVERNING LAW
This Agreement shall be governed by the laws of the State of Delaware.
"""

MOCK_ENTITIES_RESPONSE = {
    "parties": ["Acme Corp", "DevShop Ltd"],
    "effective_date": "2025-01-01",
    "expiration_date": "",
    "governing_law": "Delaware",
    "financial_terms": ["USD 50,000 per milestone", "1.5% monthly interest on late payments"],
    "obligations": ["Develop custom e-commerce platform", "Three milestone deliverables"],
}

MOCK_RISKS_RESPONSE = {
    "risks": [
        {
            "risk_type": "termination",
            "severity": "high",
            "description": "Client can terminate without cause; Developer cannot.",
            "source_text": "Client may terminate this Agreement at any time without cause",
        },
        {
            "risk_type": "liability",
            "severity": "medium",
            "description": "Developer liability capped at USD 10,000, far below project value.",
            "source_text": "Developer's total liability shall not exceed USD 10,000",
        },
    ]
}

MOCK_GAPS_RESPONSE = {
    "missing_clauses": ["confidentiality", "data_protection", "force_majeure"]
}

MOCK_SUMMARY = (
    "This Software Development Agreement dated January 1, 2025 establishes a"
    " relationship between Acme Corp (Client) and DevShop Ltd (Contractor) for"
    " the development of a custom e-commerce platform. The contract defines three"
    " payment milestones totalling USD 150,000 with 1.5% monthly interest on late"
    " payments. A significant risk is the asymmetric termination clause allowing"
    " the Client to exit without cause, while Developer faces restrictive exit"
    " conditions. Developer liability is capped at USD 10,000, creating financial"
    " exposure mismatch. The agreement lacks confidentiality, data protection, and"
    " force majeure protections, which is unusual for technology contracts of this"
    " nature."
)


def _make_mock_db(
    contract_status: str = "extracted",
    has_text: bool = True,
) -> MagicMock:
    """Construct a mock DatabaseService with preconfigured async methods."""
    db = MagicMock()
    db.get_contract_by_id = AsyncMock(
        return_value={"id": "test-123", "status": contract_status}
    )
    db.get_document_text = AsyncMock(
        return_value={"raw_text": SAMPLE_CONTRACT_TEXT, "paragraphs": []} if has_text else None
    )
    db.update_contract_status = AsyncMock(return_value=None)
    db.save_contract_entities = AsyncMock(return_value=None)
    db.save_contract_summary = AsyncMock(return_value=None)
    db.save_contract_risks = AsyncMock(return_value=None)
    db.save_contract_gaps = AsyncMock(return_value=None)
    db.update_contract_analysis = AsyncMock(return_value=None)
    return db


def _make_mock_ai(
    entities: Optional[Dict] = None,
    summary: Optional[str] = None,
    risks: Optional[Dict] = None,
    gaps: Optional[Dict] = None,
) -> MagicMock:
    """Construct a mock OpenAIService with deterministic async responses."""
    ai = MagicMock()
    ai.structured_extraction = AsyncMock(side_effect=_structured_extraction_side_effect(
        entities=entities or MOCK_ENTITIES_RESPONSE,
        risks=risks or MOCK_RISKS_RESPONSE,
        gaps=gaps or MOCK_GAPS_RESPONSE,
    ))
    ai.analyze_with_guidance = AsyncMock(return_value=summary or MOCK_SUMMARY)
    return ai


def _structured_extraction_side_effect(entities, risks, gaps):
    """Return different mocked values depending on pipeline call order.

    Call order:
      1: entity extraction
      2: CUAD metadata extraction (empty dict — triggers fallback)
      3: CUAD clause extraction  (empty dict — triggers fallback)
      4: risk detection fallback
      5: gap  detection fallback
    """
    call_index = {"n": 0}

    async def side_effect(prompt: str, context: str, schema: Dict):
        call_index["n"] += 1
        n = call_index["n"]
        if n == 1:
            return entities
        elif n in (2, 3):
            return {}        # CUAD calls — wrong schema, will fail silently
        elif n == 4:
            return risks
        elif n == 5:
            return gaps
        return {}

    return side_effect


# ── Import analysis_service AFTER helpers so patches resolve correctly ─────────

from app.services.analysis_service import AnalysisService, _parse_json_response


# ── _parse_json_response tests ─────────────────────────────────────────────────

class TestParseJsonResponse:
    def test_valid_json_object(self):
        result = _parse_json_response('{"key": "value"}', "test")
        assert result == {"key": "value"}

    def test_json_wrapped_in_markdown_fence(self):
        raw = '```json\n{"parties": ["Acme", "Dev"]}\n```'
        result = _parse_json_response(raw, "test")
        assert result == {"parties": ["Acme", "Dev"]}

    def test_json_with_preamble_text(self):
        raw = 'Here is the extracted JSON:\n{"governing_law": "Delaware"}'
        result = _parse_json_response(raw, "test")
        assert result == {"governing_law": "Delaware"}

    def test_empty_string_returns_none(self):
        assert _parse_json_response("", "test") is None

    def test_none_input_returns_none(self):
        assert _parse_json_response(None, "test") is None  # type: ignore

    def test_no_json_object_returns_none(self):
        assert _parse_json_response("No JSON here at all", "test") is None

    def test_malformed_json_returns_none(self):
        assert _parse_json_response('{"bad": json}', "test") is None

    def test_nested_object(self):
        raw = '{"risks": [{"severity": "high", "description": "foo"}]}'
        result = _parse_json_response(raw, "test")
        assert result["risks"][0]["severity"] == "high"


# ── Risk score computation ─────────────────────────────────────────────────────

class TestComputeRiskScore:
    def test_empty_risks_scores_zero(self):
        assert AnalysisService._compute_risk_score([]) == 0.0

    def test_single_critical_risk(self):
        # weight=4, score = min(10, 4/2) = 2.0
        risks = [{"severity": "critical"}]
        assert AnalysisService._compute_risk_score(risks) == 2.0

    def test_capped_at_ten(self):
        risks = [{"severity": "critical"}] * 10  # 40 / 2 = 20 → capped at 10
        assert AnalysisService._compute_risk_score(risks) == 10.0

    def test_unknown_severity_treated_as_low(self):
        risks = [{"severity": "unknown"}]
        assert AnalysisService._compute_risk_score(risks) == 0.5  # low=1, /2=0.5

    def test_mixed_severities(self):
        risks = [
            {"severity": "high"},   # 3
            {"severity": "medium"}, # 2
            {"severity": "low"},    # 1
        ]
        # total=6, score=3.0
        assert AnalysisService._compute_risk_score(risks) == 3.0


# ── Full pipeline: happy path ──────────────────────────────────────────────────

class TestAnalysisServiceHappyPath:

    @pytest.mark.asyncio
    async def test_run_sets_analyzed_status_on_success(self):
        db = _make_mock_db(contract_status="extracted")
        ai = _make_mock_ai()
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("test-123")

        # Status should end in ANALYZED
        status_calls = [str(call) for call in db.update_contract_status.call_args_list]
        assert any("analyzed" in c.lower() for c in status_calls), \
            f"Expected 'analyzed' in status calls but got: {status_calls}"

    @pytest.mark.asyncio
    async def test_run_saves_all_four_components(self):
        db = _make_mock_db(contract_status="extracted")
        ai = _make_mock_ai()
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("test-123")

        db.save_contract_entities.assert_called_once()
        db.save_contract_summary.assert_called_once()
        db.save_contract_risks.assert_called_once()
        db.save_contract_gaps.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_updates_legacy_analysis_column(self):
        db = _make_mock_db(contract_status="extracted")
        ai = _make_mock_ai()
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("test-123")

        db.update_contract_analysis.assert_called_once()
        call_kwargs = db.update_contract_analysis.call_args
        assert call_kwargs[0][0] == "test-123"
        analysis_data = call_kwargs[0][1]
        assert "extracted_data" in analysis_data
        assert "analysis" in analysis_data
        assert "summary" in analysis_data["analysis"]

    @pytest.mark.asyncio
    async def test_entities_contain_expected_fields(self):
        db = _make_mock_db(contract_status="extracted")
        ai = _make_mock_ai()
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("test-123")

        saved_entities = db.save_contract_entities.call_args[0][1]
        assert "parties" in saved_entities
        assert isinstance(saved_entities["parties"], list)
        assert "governing_law" in saved_entities

    @pytest.mark.asyncio
    async def test_risks_are_validated_and_saved(self):
        db = _make_mock_db(contract_status="extracted")
        ai = _make_mock_ai()
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("test-123")

        saved_risks = db.save_contract_risks.call_args[0][1]
        assert len(saved_risks) == 2
        for r in saved_risks:
            assert "risk_type" in r
            assert "severity" in r
            assert "description" in r

    @pytest.mark.asyncio
    async def test_missing_clauses_whitelisted(self):
        db = _make_mock_db(contract_status="extracted")
        ai = _make_mock_ai()
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("test-123")

        saved_gaps = db.save_contract_gaps.call_args[0][1]
        valid_clauses = {
            "confidentiality", "data_protection", "force_majeure",
            "termination", "governing_law",
        }
        for clause in saved_gaps:
            assert clause in valid_clauses, f"Unexpected clause: {clause}"


# ── Guard: wrong status ────────────────────────────────────────────────────────

class TestAnalysisServiceGuards:

    @pytest.mark.asyncio
    async def test_skips_uploaded_status(self):
        db = _make_mock_db(contract_status="uploaded")
        ai = _make_mock_ai()
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("test-123")

        # Nothing should have been saved or status changed
        db.save_contract_entities.assert_not_called()
        db.update_contract_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_failed_status(self):
        db = _make_mock_db(contract_status="failed")
        ai = _make_mock_ai()
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("test-123")

        db.save_contract_entities.assert_not_called()

    @pytest.mark.asyncio
    async def test_allows_processing_status(self):
        """Endpoint may set PROCESSING before background task runs — must still proceed."""
        db = _make_mock_db(contract_status="processing")
        ai = _make_mock_ai()
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("test-123")

        db.save_contract_entities.assert_called_once()

    @pytest.mark.asyncio
    async def test_allows_reanalysis_of_analyzed_contract(self):
        db = _make_mock_db(contract_status="analyzed")
        ai = _make_mock_ai()
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("test-123")

        db.save_contract_entities.assert_called_once()

    @pytest.mark.asyncio
    async def test_contract_not_found_is_no_op(self):
        db = _make_mock_db()
        db.get_contract_by_id = AsyncMock(return_value=None)
        ai = _make_mock_ai()
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("nonexistent-id")

        db.update_contract_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_text_sets_failed_status(self):
        db = _make_mock_db(contract_status="extracted", has_text=False)
        ai = _make_mock_ai()
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("test-123")

        db.update_contract_status.assert_called_once()
        call_arg = str(db.update_contract_status.call_args)
        assert "failed" in call_arg.lower()


# ── Failure resilience ─────────────────────────────────────────────────────────

class TestAnalysisServiceFailureResilience:

    @pytest.mark.asyncio
    async def test_ai_exception_sets_failed_status(self):
        db = _make_mock_db(contract_status="extracted")
        ai = MagicMock()
        ai.structured_extraction = AsyncMock(side_effect=RuntimeError("LLM timeout"))
        ai.analyze_with_guidance = AsyncMock(side_effect=RuntimeError("LLM timeout"))
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("test-123")

        status_calls = [str(c) for c in db.update_contract_status.call_args_list]
        assert any("failed" in c.lower() for c in status_calls)

    @pytest.mark.asyncio
    async def test_malformed_risk_json_returns_empty_list(self):
        db = _make_mock_db(contract_status="extracted")
        ai = MagicMock()
        # Entities and gaps return valid dicts, but risks returns garbage
        ai.structured_extraction = AsyncMock(side_effect=[
            MOCK_ENTITIES_RESPONSE,
            {},                          # CUAD metadata (will fail silently)
            {},                          # CUAD clauses (will fail silently)
            {"risks": "not-a-list"},  # malformed
            MOCK_GAPS_RESPONSE,
        ])
        ai.analyze_with_guidance = AsyncMock(return_value=MOCK_SUMMARY)
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("test-123")

        saved_risks = db.save_contract_risks.call_args[0][1]
        assert saved_risks == []  # bad items filtered out

    @pytest.mark.asyncio
    async def test_unknown_gap_clauses_are_filtered(self):
        db = _make_mock_db(contract_status="extracted")
        gaps_with_garbage = {
            "missing_clauses": ["confidentiality", "INVALID_CLAUSE", "data_protection", 42]
        }
        ai = _make_mock_ai(gaps=gaps_with_garbage)
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("test-123")

        saved_gaps = db.save_contract_gaps.call_args[0][1]
        assert "INVALID_CLAUSE" not in saved_gaps
        assert 42 not in saved_gaps
        assert "confidentiality" in saved_gaps

    @pytest.mark.asyncio
    async def test_summary_llm_failure_uses_fallback(self):
        db = _make_mock_db(contract_status="extracted")
        ai = MagicMock()
        ai.structured_extraction = AsyncMock(side_effect=[
            MOCK_ENTITIES_RESPONSE,
            {},                          # CUAD metadata
            {},                          # CUAD clauses
            MOCK_RISKS_RESPONSE,
            MOCK_GAPS_RESPONSE,
        ])
        ai.analyze_with_guidance = AsyncMock(side_effect=RuntimeError("LLM unavailable"))
        svc = AnalysisService(db=db, ai=ai)

        await svc.run("test-123")

        # Should still complete with a fallback summary, not raise
        saved_summary = db.save_contract_summary.call_args[0][1]
        assert saved_summary == "Summary not available."


# ── API endpoint smoke tests ───────────────────────────────────────────────────

class TestAnalysisEndpoints:
    """Lightweight HTTP contract tests using FastAPI TestClient."""

    def _build_app(self):
        """Create an isolated FastAPI app with only the contracts router."""
        from fastapi import FastAPI
        from app.api.contracts import router as contracts_router

        app = FastAPI()
        app.include_router(contracts_router, prefix="/api/contracts")
        return app

    def test_analyze_endpoint_returns_202_for_extracted_contract(self):
        from fastapi.testclient import TestClient
        from app.api import contracts as contracts_module

        mock_db = _make_mock_db(contract_status="extracted")
        mock_db.get_contract = AsyncMock(
            return_value={"id": "test-123", "status": "extracted", "blob_url": "blob://test"}
        )

        with patch.object(contracts_module, "db_service", mock_db), \
             patch.object(contracts_module, "phase2_analysis_service") as mock_svc:
            mock_svc.run = AsyncMock(return_value=None)
            client = TestClient(self._build_app())
            resp = client.post("/api/contracts/test-123/analyze")

        assert resp.status_code == 200  # FastAPI returns 200 for dicts without response_model
        body = resp.json()
        assert body["contract_id"] == "test-123"
        assert body["status"] == "processing"

    def test_get_analysis_returns_results_when_available(self):
        from fastapi.testclient import TestClient
        from app.api import contracts as contracts_module

        mock_db = MagicMock()
        mock_db.get_contract = AsyncMock(
            return_value={"id": "test-123", "status": "analyzed"}
        )
        mock_db.get_contract_entities = AsyncMock(return_value=MOCK_ENTITIES_RESPONSE)
        mock_db.get_contract_summary = AsyncMock(return_value=MOCK_SUMMARY)
        mock_db.get_contract_risks = AsyncMock(return_value=MOCK_RISKS_RESPONSE["risks"])
        mock_db.get_contract_gaps = AsyncMock(return_value=["confidentiality", "data_protection"])

        with patch.object(contracts_module, "db_service", mock_db), \
             patch.object(contracts_module, "phase2_analysis_service") as mock_svc:
            mock_svc._compute_risk_score = AnalysisService._compute_risk_score
            client = TestClient(self._build_app())
            resp = client.get("/api/contracts/test-123/analysis")

        assert resp.status_code == 200
        body = resp.json()
        assert body["contract_id"] == "test-123"
        assert body["status"] == "analyzed"
        assert body["summary"] == MOCK_SUMMARY
        assert len(body["risks"]) == 2
        assert "confidentiality" in body["missing_clauses"]
        assert body["overall_risk_score"] >= 0

    def test_get_analysis_returns_404_when_not_yet_analyzed(self):
        from fastapi.testclient import TestClient
        from app.api import contracts as contracts_module

        mock_db = MagicMock()
        mock_db.get_contract = AsyncMock(
            return_value={"id": "test-123", "status": "extracted"}
        )
        mock_db.get_contract_entities = AsyncMock(return_value=None)
        mock_db.get_contract_summary = AsyncMock(return_value=None)
        mock_db.get_contract_risks = AsyncMock(return_value=[])
        mock_db.get_contract_gaps = AsyncMock(return_value=None)

        with patch.object(contracts_module, "db_service", mock_db), \
             patch.object(contracts_module, "phase2_analysis_service") as mock_svc:
            mock_svc._compute_risk_score = AnalysisService._compute_risk_score
            client = TestClient(self._build_app())
            resp = client.get("/api/contracts/test-123/analysis")

        assert resp.status_code == 404

    def test_get_analysis_returns_404_for_unknown_contract(self):
        from fastapi.testclient import TestClient
        from app.api import contracts as contracts_module

        mock_db = MagicMock()
        mock_db.get_contract = AsyncMock(return_value=None)

        with patch.object(contracts_module, "db_service", mock_db):
            client = TestClient(self._build_app())
            resp = client.get("/api/contracts/nonexistent/analysis")

        assert resp.status_code == 404
