"""
CUAD Analysis API Endpoint

Provides REST API access to CUAD-based contract risk analysis.

Endpoints:
- POST /api/contracts/{contract_id}/cuad-analysis - Run CUAD analysis
- GET /api/contracts/{contract_id}/cuad-analysis - Get existing CUAD analysis results
- POST /api/contracts/{contract_id}/cuad-analysis/re-evaluate - Re-run risk evaluation
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Header, Query
from typing import Optional, Dict, Any
import logging

from app.services.cuad_analysis_service import cuad_analysis_service
from app.services.sqlite_service import DatabaseService
from app.models.schemas import ContractStatus

logger = logging.getLogger(__name__)
router = APIRouter()

# Services
db_service = DatabaseService()


def _get_user_id_from_token(authorization: Optional[str]) -> str:
    """Extract and validate user from auth token. Falls back to 'anonymous' for dev."""
    from app.services.auth_service import validate_session
    
    if not authorization:
        return "anonymous"
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        return "anonymous"
    user = validate_session(token)
    if not user:
        return "anonymous"
    return user.get("id", "anonymous")


@router.post("/{contract_id}/cuad-analysis")
async def run_cuad_analysis(
    contract_id: str,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None),
    user_id: Optional[str] = Query(None, description="User ID for testing"),
):
    """
    Run CUAD-based contract risk analysis
    
    This endpoint triggers a comprehensive analysis:
    1. CUAD clause extraction (9 clause types)
    2. Rule-based risk evaluation
    3. Gap detection (missing clauses)
    4. Risk summary generation
    
    The analysis runs as a background task.
    
    Pre-conditions:
    - Contract must be in EXTRACTED status (text extraction completed)
    
    Returns:
    - 202 Accepted: Analysis started in background
    - 404: Contract not found
    - 400: Contract not ready for analysis
    """
    try:
        # Verify user ownership
        resolved_user_id = user_id or _get_user_id_from_token(authorization)
        contract = await db_service.get_contract(contract_id, resolved_user_id)
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        # Check if contract is ready for analysis
        current_status = contract.get("status")
        if current_status not in (
            ContractStatus.EXTRACTED.value,
            ContractStatus.ANALYZED.value,  # allow re-analysis
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Contract must be extracted before analysis. Current status: {current_status}"
            )
        
        # Schedule CUAD analysis as background task
        background_tasks.add_task(
            cuad_analysis_service.analyze_contract,
            contract_id
        )
        
        logger.info(f"CUAD analysis scheduled for contract {contract_id}")
        
        return {
            "message": "CUAD analysis started",
            "contract_id": contract_id,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting CUAD analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")


@router.get("/{contract_id}/cuad-analysis")
async def get_cuad_analysis(
    contract_id: str,
    authorization: Optional[str] = Header(None),
    user_id: Optional[str] = Query(None, description="User ID for testing"),
) -> Dict[str, Any]:
    """
    Get CUAD analysis results for a contract
    
    Returns the complete CUAD analysis including:
    - Extracted clauses with locations
    - Risk evaluation for each clause
    - Overall risk summary
    - Missing clause detection (gap analysis)
    - Completeness score
    - Actionable recommendations
    
    Returns:
    - 200: Analysis results
    - 404: Contract or analysis not found
    - 202: Analysis still in progress
    """
    try:
        # Verify user ownership
        resolved_user_id = user_id or _get_user_id_from_token(authorization)
        contract = await db_service.get_contract(contract_id, resolved_user_id)
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        # Check contract status
        current_status = contract.get("status")
        if current_status == ContractStatus.PROCESSING.value:
            return {
                "message": "Analysis in progress",
                "contract_id": contract_id,
                "status": "processing"
            }
        
        # Get CUAD analysis results
        analysis = await cuad_analysis_service.get_contract_analysis(contract_id)
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail="No CUAD analysis found. Run POST /cuad-analysis first."
            )
        
        return {
            "contract_id": contract_id,
            "status": "complete",
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving CUAD analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analysis: {str(e)}")


@router.post("/{contract_id}/cuad-analysis/re-evaluate")
async def re_evaluate_risk(
    contract_id: str,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None),
    user_id: Optional[str] = Query(None, description="User ID for testing"),
):
    """
    Re-run risk evaluation on existing clause extraction
    
    This is useful when:
    - Risk evaluation rules have been updated
    - You want to recalculate risk without re-extracting clauses
    
    Uses existing extracted clause data and applies current risk rules.
    Runs as a background task.
    
    Returns:
    - 202 Accepted: Re-evaluation started
    - 404: Contract or existing analysis not found
    """
    try:
        # Verify user ownership
        resolved_user_id = user_id or _get_user_id_from_token(authorization)
        contract = await db_service.get_contract(contract_id, resolved_user_id)
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        # Check if CUAD analysis exists
        existing = await cuad_analysis_service.get_contract_analysis(contract_id)
        if not existing:
            raise HTTPException(
                status_code=404,
                detail="No existing CUAD analysis found. Run POST /cuad-analysis first."
            )
        
        # Schedule re-evaluation as background task
        background_tasks.add_task(
            cuad_analysis_service.re_evaluate_risk,
            contract_id
        )
        
        logger.info(f"CUAD risk re-evaluation scheduled for contract {contract_id}")
        
        return {
            "message": "Risk re-evaluation started",
            "contract_id": contract_id,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting risk re-evaluation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start re-evaluation: {str(e)}")


@router.get("/{contract_id}/cuad-analysis/summary")
async def get_cuad_summary(
    contract_id: str,
    authorization: Optional[str] = Header(None),
    user_id: Optional[str] = Query(None, description="User ID for testing"),
) -> Dict[str, Any]:
    """
    Get quick CUAD analysis summary
    
    Returns a condensed version of the analysis focusing on:
    - Overall risk level
    - Completeness score
    - Critical high-risk items
    - Critical missing clauses
    - Key findings
    
    Useful for dashboard displays and quick overviews.
    
    Returns:
    - 200: Summary data
    - 404: Contract or analysis not found
    """
    try:
        # Verify user ownership
        resolved_user_id = user_id or _get_user_id_from_token(authorization)
        contract = await db_service.get_contract(contract_id, resolved_user_id)
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        # Get full analysis
        analysis = await cuad_analysis_service.get_contract_analysis(contract_id)
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail="No CUAD analysis found"
            )
        
        # Extract summary information
        risk_summary = analysis.get("risk_summary", {})
        gap_analysis = analysis.get("gap_analysis", {})
        
        summary = {
            "contract_id": contract_id,
            "overall_risk": risk_summary.get("overall_risk", "UNKNOWN"),
            "completeness_score": gap_analysis.get("completeness_score", 0),
            "high_risk_count": len(risk_summary.get("high_risk_items", [])),
            "missing_clauses_count": len(gap_analysis.get("critical_gaps", [])),
            "key_findings": risk_summary.get("key_findings", [])[:5],  # Top 5 findings
            "top_risks": risk_summary.get("high_risk_items", [])[:3],  # Top 3 risks
            "critical_gaps": gap_analysis.get("critical_gaps", [])[:3]  # Top 3 gaps
        }
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving CUAD summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve summary: {str(e)}")
