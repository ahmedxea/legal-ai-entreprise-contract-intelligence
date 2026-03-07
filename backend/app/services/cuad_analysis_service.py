"""
CUAD-Based Contract Analysis Service

Integrated service that orchestrates the complete CUAD-based contract analysis pipeline:

1. Entity Extraction (LLM-powered) - parties, dates, governing law
2. CUAD Clause Extraction (LLM-powered) - 15 high-value clauses
3. Risk Evaluation (Rule-based) - deterministic risk scoring
4. Gap Detection (Deterministic) - missing clause identification
5. Risk Summary Generation

This service provides structured, explainable contract risk analysis
grounded in the CUAD dataset methodology.

Architecture:
    Contract Upload
           ↓
    Text Extraction
           ↓
    Entity Extraction (parties, dates, etc.)
           ↓
    CUAD Clause Extraction (15 clauses)
           ↓
    Structured Contract Data
           ↓
    Risk Rule Engine
           ↓
    Risk Analysis
           ↓
    Gap Detection
           ↓
    Summary Output
"""

import logging
import json
from typing import Dict, Any, Optional
from app.models.schemas import ContractStatus, Language
from app.models.clause_schema import ContractAnalysisSchema, RiskSummary
from app.agents.cuad_clause_extraction_agent import CUADClauseExtractionAgent
from app.agents.risk_evaluation_engine import RiskEvaluationEngine
from app.agents.gap_detection_agent import GapDetectionAgent
from app.agents.extraction_agent import ExtractionAgent
from app.services.sqlite_service import DatabaseService
from app.services.database_factory import database_service

logger = logging.getLogger(__name__)


class CUADAnalysisService:
    """
    CUAD-based contract analysis orchestrator
    
    Coordinates extraction, evaluation, and gap detection
    to produce comprehensive structured contract intelligence.
    """
    
    def __init__(self, db: Optional[DatabaseService] = None):
        """
        Initialize the CUAD analysis service
        
        Args:
            db: Database service (uses default if not provided)
        """
        self._db = db or database_service
        self._clause_extractor = CUADClauseExtractionAgent()
        self._risk_evaluator = RiskEvaluationEngine()
        self._gap_detector = GapDetectionAgent()
        self._entity_extractor = ExtractionAgent()
    
    async def analyze_contract(self, contract_id: str) -> Dict[str, Any]:
        """
        Run complete CUAD-based analysis on a contract
        
        End-to-end pipeline:
        1. Fetch contract text from database
        2. Extract basic entities (parties, dates, governing law)
        3. Extract CUAD clauses using LLM (15 clause types)
        4. Evaluate risks using rule engine (deterministic)
        5. Generate risk summary
        6. Detect missing clauses (gap analysis)
        7. Persist results to database (analysis + extracted_data)
        
        Args:
            contract_id: Contract ID to analyze
            
        Returns:
            Complete analysis results including entities and clauses
        """
        logger.info(f"[CUAD] Starting CUAD analysis for contract {contract_id}")
        
        # ── Step 0: Validate contract exists and has text ──────────────────────
        contract = await self._db.get_contract_by_id(contract_id)
        if not contract:
            logger.error(f"[CUAD] Contract {contract_id} not found")
            raise ValueError(f"Contract {contract_id} not found")
        
        # Check status
        current_status = contract.get("status")
        if current_status not in (
            ContractStatus.EXTRACTED.value,
            ContractStatus.ANALYZED.value,
            ContractStatus.PROCESSING.value,
        ):
            logger.warning(
                f"[CUAD] Contract {contract_id} has status '{current_status}', "
                "expected 'extracted' or 'analyzed'"
            )
        
        # Get contract text
        text_record = await self._db.get_document_text(contract_id)
        if not text_record or not text_record.get("raw_text"):
            logger.error(f"[CUAD] No extracted text for contract {contract_id}")
            await self._db.update_contract_status(contract_id, ContractStatus.FAILED)
            raise ValueError(f"No extracted text for contract {contract_id}")
        
        contract_text = text_record["raw_text"]
        language = Language(contract.get("language", "english"))
        
        # Mark as processing
        await self._db.update_contract_status(contract_id, ContractStatus.PROCESSING)
        
        try:
            # ── Step 1: Extract CUAD clauses using LLM (CUAD-based) ────────────
            logger.info(f"[CUAD] Step 1: Extracting CUAD clauses for {contract_id}")
            clause_analysis = await self._clause_extractor.extract_clauses(
                contract_id=contract_id,
                contract_text=contract_text,
                language=language
            )
            
            # ── Step 2: Extract additional entities (LLM-based) ────────────────
            logger.info(f"[CUAD] Step 2: Extracting supplementary entities for {contract_id}")
            extracted_data = await self._entity_extractor.extract_data(
                contract_text=contract_text,
                language=language
            )
            
            # ── Step 2.5: Merge CUAD clause data with entity data ──────────────
            # CUAD clauses take priority over entity extraction for overlapping fields
            extracted_data = self._merge_cuad_with_entities(clause_analysis, extracted_data)
            logger.info(f"[CUAD] Merged CUAD clauses with entity data for {contract_id}")
            
            # ── Step 3: Evaluate risks using rule engine (Rule-based) ──────────
            logger.info(f"[CUAD] Step 3: Evaluating risks with deterministic rules for {contract_id}")
            clause_analysis = self._risk_evaluator.evaluate_contract_risk(clause_analysis)
            
            # ── Step 4: Generate risk summary ──────────────────────────────────
            logger.info(f"[CUAD] Step 4: Generating risk summary for {contract_id}")
            risk_summary = self._risk_evaluator.generate_risk_summary(clause_analysis, extracted_data)
            
            # ── Step 5: Detect missing clauses (gap analysis) ──────────────────
            logger.info(f"[CUAD] Step 5: Detecting gaps for {contract_id}")
            gap_analysis = self._gap_detector.generate_gap_report(clause_analysis)
            
            # ── Step 6: Persist results ────────────────────────────────────────
            logger.info(f"[CUAD] Step 6: Persisting results for {contract_id}")
            await self._persist_cuad_results(
                contract_id=contract_id,
                extracted_data=extracted_data,
                clause_analysis=clause_analysis,
                risk_summary=risk_summary,
                gap_analysis=gap_analysis
            )
            
            # ── Step 7: Update contract status ─────────────────────────────────
            await self._db.update_contract_status(contract_id, ContractStatus.ANALYZED)
            
            # Build complete result
            result = {
                "contract_id": contract_id,
                "status": "success",
                "extracted_data": extracted_data,
                "clause_analysis": clause_analysis.dict(),
                "risk_summary": risk_summary.dict(),
                "gap_analysis": gap_analysis,
                "overall_risk": risk_summary.overall_risk,
                "completeness_score": gap_analysis["completeness_score"]
            }
            
            logger.info(
                f"[CUAD] Analysis completed for {contract_id}: "
                f"Risk={risk_summary.overall_risk}, "
                f"Completeness={gap_analysis['completeness_score']}%"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"[CUAD] Error analyzing contract {contract_id}: {e}", exc_info=True)
            await self._db.update_contract_status(contract_id, ContractStatus.FAILED)
            raise
    
    async def _persist_cuad_results(
        self,
        contract_id: str,
        extracted_data: Dict[str, Any],
        clause_analysis: ContractAnalysisSchema,
        risk_summary: RiskSummary,
        gap_analysis: Dict[str, Any]
    ) -> None:
        """
        Persist CUAD analysis results to database
        
        Saves complete CUAD analysis to the contract.analysis JSON column
        and extracted entities to the extracted_data column
        
        Args:
            contract_id: Contract ID
            extracted_data: Basic entities (parties, dates, etc.)
            clause_analysis: Extracted and evaluated clauses
            risk_summary: Risk summary
            gap_analysis: Gap detection results
        """
        try:
            # Build comprehensive analysis JSON
            analysis_json = {
                "cuad_version": "1.0",
                "analysis_type": "cuad_structured",
                "entities": extracted_data,  # Include entities in analysis
                "clauses": clause_analysis.dict(),
                "risk_summary": risk_summary.dict(),
                "gap_analysis": gap_analysis
            }
            
            # Save to contract analysis column and extracted_data column
            # Use positional args to avoid Union type parameter name conflicts
            # (SQLiteService uses 'analysis_result', AzureSQLService uses 'analysis_data')
            await self._db.update_contract_analysis(
                contract_id,
                {
                    "analysis": analysis_json,
                    "extracted_data": extracted_data
                }
            )
            
            logger.info(f"[CUAD] Results persisted for contract {contract_id}")
            
        except Exception as e:
            logger.error(f"[CUAD] Error persisting results for {contract_id}: {e}", exc_info=True)
            # Don't raise - we want to return results even if persistence fails
    
    def _merge_cuad_with_entities(
        self,
        clause_analysis: ContractAnalysisSchema,
        extracted_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge CUAD clause-extracted data with LLM entity extraction
        
        CUAD clause data takes priority for overlapping fields:
        - Governing Law (from CUAD governing_law clause)
        - Parties (from CUAD contract_parties)
        - Dates (from CUAD effective_date, expiration_date)
        
        This ensures CUAD-extracted legal entities are authoritative
        while preserving additional context from LLM extraction.
        
        Args:
            clause_analysis: CUAD clause extraction results
            extracted_data: LLM entity extraction results
            
        Returns:
            Merged entity data with CUAD taking priority
        """
        merged = extracted_data.copy()
        
        # Governing Law: CUAD clause takes priority
        if clause_analysis.governing_law.present and clause_analysis.governing_law.text:
            jurisdiction, confidence = self._extract_jurisdiction(
                clause_analysis.governing_law.text
            )
            if jurisdiction:
                merged["governing_law"] = jurisdiction
                merged["jurisdiction_confidence"] = confidence
                merged["jurisdiction_source"] = "cuad_clause"
            elif extracted_data.get("governing_law"):
                # LLM entity extraction fallback
                merged["jurisdiction_confidence"] = 0.7
                merged["jurisdiction_source"] = "llm_entity"
            else:
                # Clause present but jurisdiction not parseable
                merged["governing_law"] = clause_analysis.governing_law.text[:120].strip()
                merged["jurisdiction_confidence"] = 0.4
                merged["jurisdiction_source"] = "clause_text_fallback"
            logger.debug(f"[CUAD] Governing law: {merged.get('governing_law')} (confidence={merged.get('jurisdiction_confidence')})")
        elif extracted_data.get("governing_law"):
            merged["jurisdiction_confidence"] = 0.7
            merged["jurisdiction_source"] = "llm_entity"
        
        # Parties: CUAD contract_parties takes priority if present
        if clause_analysis.contract_parties:
            merged["parties"] = clause_analysis.contract_parties
            logger.debug(f"[CUAD] Using CUAD-extracted parties: {len(clause_analysis.contract_parties)} parties")
        
        # Effective Date: CUAD takes priority
        if clause_analysis.effective_date:
            merged["effective_date"] = clause_analysis.effective_date
            logger.debug(f"[CUAD] Using CUAD-extracted effective date: {clause_analysis.effective_date}")
        
        # Expiration Date: CUAD takes priority
        if clause_analysis.expiration_date:
            merged["expiration_date"] = clause_analysis.expiration_date
            logger.debug(f"[CUAD] Using CUAD-extracted expiration date: {clause_analysis.expiration_date}")
        
        # If no governing law found at all, mark explicitly
        if not merged.get("governing_law"):
            merged["jurisdiction_confidence"] = 0.0
            merged["jurisdiction_source"] = "not_found"
        
        # Contract Type: Try to infer from CUAD clauses if not present
        if not merged.get("contract_type"):
            # Infer type based on present clauses
            if clause_analysis.confidentiality.present and not clause_analysis.payment_terms.present:
                merged["contract_type"] = "NDA"
            elif clause_analysis.intellectual_property.present:
                merged["contract_type"] = "License Agreement"
            elif clause_analysis.payment_terms.present:
                merged["contract_type"] = "Service Agreement"
            else:
                merged["contract_type"] = "General Agreement"
        
        return merged
    
    @staticmethod
    def _extract_jurisdiction(clause_text: str) -> tuple:
        """
        Extract jurisdiction from governing law clause text.
        
        Uses ranked regex patterns covering common legal phrasings:
        - "governed by the laws of [State/Country]"
        - "laws of the State of [State]"
        - "[State/Country] law shall govern"
        - "courts of [Jurisdiction] shall have jurisdiction"
        - "governed by [Jurisdiction]" (without 'laws of')
        - "subject to [Jurisdiction] law"
        
        Returns:
            Tuple of (jurisdiction_string or None, confidence_float)
        """
        import re
        
        if not clause_text:
            return None, 0.0
        
        text = clause_text.strip()
        
        # Ranked patterns: most specific first, with confidence scores
        patterns = [
            # "laws of the State of X" / "laws of the Commonwealth of X"
            (r'laws?\s+of\s+the\s+(?:State|Commonwealth|Province|Territory)\s+of\s+([A-Z][^,\.;\n]{1,60})', 0.95),
            # "governed by the laws of X" / "subject to the laws of X"
            (r'(?:governed|construed|interpreted|subject)\s+(?:by|to|under)\s+(?:the\s+)?laws?\s+of\s+([A-Z][^,\.;\n]{1,60})', 0.95),
            # "laws of X" (standalone)
            (r'laws?\s+of\s+([A-Z][^,\.;\n]{1,60})', 0.90),
            # "X law shall govern" / "X law applies" / "X law"
            (r'\b([A-Z][A-Za-z\s]{1,40})\s+laws?\s+(?:shall\s+)?(?:govern|appl)', 0.90),
            # "courts of X shall have jurisdiction"
            (r'courts?\s+(?:of|in|located in)\s+([A-Z][^,\.;\n]{1,60})\s+(?:shall\s+)?have\s+(?:exclusive\s+)?jurisdiction', 0.85),
            # "governed by X" (without 'laws of')
            (r'(?:governed|construed|interpreted)\s+(?:by|under)\s+(?:the\s+laws?\s+(?:of|applicable\s+in)\s+)?([A-Z][^,\.;\n]{1,60})', 0.80),
            # "jurisdiction of X" / "jurisdiction shall be X"
            (r'jurisdiction\s+(?:of|shall\s+be|is)\s+([A-Z][^,\.;\n]{1,60})', 0.80),
            # "under X law"
            (r'under\s+(?:the\s+)?([A-Z][A-Za-z\s]{1,40})\s+laws?', 0.80),
        ]
        
        for pattern, confidence in patterns:
            match = re.search(pattern, text)
            if match:
                jurisdiction = match.group(1).strip()
                # Clean trailing words like "and", "or", "without"
                jurisdiction = re.sub(r'\s+(?:and|or|without|except|including|excluding|shall|will|may)\s*$', '', jurisdiction, flags=re.IGNORECASE)
                jurisdiction = jurisdiction.strip(' \t\n"\'')
                if len(jurisdiction) >= 2:
                    return jurisdiction, confidence
        
        # Last-resort: case-insensitive "laws of X"
        fallback = re.search(r'laws?\s+of\s+([^,\.;\n]{2,60})', text, re.IGNORECASE)
        if fallback:
            jurisdiction = fallback.group(1).strip()
            jurisdiction = re.sub(r'\s+(?:and|or|without|except)\s*$', '', jurisdiction, flags=re.IGNORECASE)
            if len(jurisdiction) >= 2:
                return jurisdiction.strip(), 0.6
        
        return None, 0.0
    
    async def get_contract_analysis(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve CUAD analysis results for a contract
        
        Args:
            contract_id: Contract ID
            
        Returns:
            Analysis results or None if not found
        """
        try:
            contract = await self._db.get_contract_by_id(contract_id)
            if not contract:
                return None
            
            analysis_data = contract.get("analysis")
            
            # Check if it's CUAD analysis
            if analysis_data and isinstance(analysis_data, dict):
                if analysis_data.get("analysis_type") == "cuad_structured":
                    return analysis_data
            
            # Not CUAD analysis or no analysis yet
            return None
            
        except Exception as e:
            logger.error(f"[CUAD] Error retrieving analysis for {contract_id}: {e}")
            return None
    
    async def re_evaluate_risk(self, contract_id: str) -> Dict[str, Any]:
        """
        Re-run risk evaluation on existing extracted clauses
        
        Useful when risk rules are updated without needing to
        re-extract clauses from the contract.
        
        Args:
            contract_id: Contract ID
            
        Returns:
            Updated risk analysis
        """
        logger.info(f"[CUAD] Re-evaluating risk for contract {contract_id}")
        
        # Get existing analysis
        existing = await self.get_contract_analysis(contract_id)
        if not existing or "clauses" not in existing:
            raise ValueError(f"No existing CUAD analysis for contract {contract_id}")
        
        # Get existing extracted data (entities)
        extracted_data = existing.get("entities", {})
        
        # Reconstruct clause analysis from saved data
        clause_analysis = ContractAnalysisSchema(**existing["clauses"])
        
        # Re-run risk evaluation with current rules
        clause_analysis = self._risk_evaluator.evaluate_contract_risk(clause_analysis)
        
        # Regenerate risk summary with risk flags
        risk_summary = self._risk_evaluator.generate_risk_summary(clause_analysis, extracted_data)
        
        # Regenerate gap analysis
        gap_analysis = self._gap_detector.generate_gap_report(clause_analysis)
        
        # Persist updated results
        await self._persist_cuad_results(
            contract_id=contract_id,
            extracted_data=extracted_data,
            clause_analysis=clause_analysis,
            risk_summary=risk_summary,
            gap_analysis=gap_analysis
        )
        
        return {
            "contract_id": contract_id,
            "status": "re-evaluated",
            "risk_summary": risk_summary.dict(),
            "gap_analysis": gap_analysis
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global service instance
cuad_analysis_service = CUADAnalysisService()


async def run_cuad_analysis(contract_id: str) -> Dict[str, Any]:
    """
    Run CUAD analysis on a contract
    
    Convenience function
    
    Args:
        contract_id: Contract ID
        
    Returns:
        Complete analysis results
    """
    return await cuad_analysis_service.analyze_contract(contract_id)
