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
            # ── Step 1: Extract basic entities (parties, dates, etc.) ──────────
            logger.info(f"[CUAD] Step 1: Extracting entities for {contract_id}")
            extracted_data = await self._entity_extractor.extract_data(
                contract_text=contract_text,
                language=language
            )
            
            # ── Step 2: Extract CUAD clauses using LLM ─────────────────────────
            logger.info(f"[CUAD] Step 2: Extracting clauses for {contract_id}")
            clause_analysis = await self._clause_extractor.extract_clauses(
                contract_id=contract_id,
                contract_text=contract_text,
                language=language
            )
            
            # ── Step 3: Evaluate risks using rule engine ───────────────────────
            logger.info(f"[CUAD] Step 3: Evaluating risks for {contract_id}")
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
