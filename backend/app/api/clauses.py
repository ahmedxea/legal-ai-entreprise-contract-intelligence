"""
Clauses API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from app.models.schemas import (
    ClauseTemplate, GenerateContractRequest,
    Industry, GoverningLaw, Language
)
from app.services.clause_service import ClauseService
from app.services.clause_generator_service import clause_generator_service
from app.agents.clause_agent import ClauseGenerationAgent

logger = logging.getLogger(__name__)
router = APIRouter()

clause_service = ClauseService()
clause_agent = ClauseGenerationAgent()


class GenerateClauseRequest(BaseModel):
    """Request for AI clause generation based on risk/gap context"""
    clause_type: str = Field(..., description="CUAD clause type (e.g. 'liability', 'confidentiality')")
    risk_description: str = Field(default="", description="Detected risk or missing clause description")
    jurisdiction: str = Field(default="", description="Governing law / jurisdiction")
    contract_context: str = Field(default="", description="Relevant contract context or summary")


@router.get("/templates", response_model=List[ClauseTemplate])
async def get_clause_templates(
    industry: Industry = Query(None),
    jurisdiction: GoverningLaw = Query(None),
    language: Language = Query(Language.ENGLISH)
):
    """
    Get available clause templates
    """
    try:
        templates = await clause_service.get_templates(
            industry=industry,
            jurisdiction=jurisdiction,
            language=language
        )
        return templates
        
    except Exception as e:
        logger.error(f"Error retrieving templates: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve templates")


@router.post("/generate")
async def generate_clauses(
    request: GenerateContractRequest,
    user_id: str = Query(..., description="User ID")
):
    """
    Generate contract clauses based on parameters
    """
    try:
        logger.info(f"Generating clauses for industry: {request.industry}, law: {request.governing_law}")
        
        clauses = await clause_agent.generate_clauses(
            industry=request.industry,
            governing_law=request.governing_law,
            language=request.language,
            clause_types=request.clause_types,
            custom_parameters=request.custom_parameters
        )
        
        return {"clauses": clauses}
        
    except Exception as e:
        logger.error(f"Error generating clauses: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate clauses")


@router.post("/generate-for-risk")
async def generate_clause_for_risk(request: GenerateClauseRequest):
    """
    Generate a tailored clause to address a specific risk or missing clause.
    Uses CUAD templates as guidance for LLM generation.
    """
    try:
        result = await clause_generator_service.generate_clause(
            clause_type=request.clause_type,
            risk_description=request.risk_description,
            jurisdiction=request.jurisdiction,
            contract_context=request.contract_context,
        )
        return result

    except Exception as e:
        logger.error(f"Error generating clause for risk: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate clause")


@router.get("/cuad-templates")
async def list_cuad_templates():
    """List all available CUAD clause templates."""
    return clause_generator_service.list_available_templates()
