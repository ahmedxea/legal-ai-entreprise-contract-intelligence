"""
Clauses API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
import logging

from app.models.schemas import (
    ClauseTemplate, GenerateContractRequest,
    Industry, GoverningLaw, Language
)
from app.services.clause_service import ClauseService
from app.agents.clause_agent import ClauseGenerationAgent

logger = logging.getLogger(__name__)
router = APIRouter()

clause_service = ClauseService()
clause_agent = ClauseGenerationAgent()


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
