"""
Analysis API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
import logging

from app.models.schemas import RiskLevel
from app.services.sqlite_service import DatabaseService

logger = logging.getLogger(__name__)
router = APIRouter()

db_service = DatabaseService()


@router.get("/risks")
async def get_all_risks(
    user_id: str = Query(..., description="User ID"),
    severity: RiskLevel = Query(None),
    limit: int = Query(50, le=100)
):
    """
    Get all risks across all user contracts
    """
    try:
        risks = await db_service.get_user_risks(
            user_id=user_id,
            severity=severity,
            limit=limit
        )
        return {"risks": risks}
        
    except Exception as e:
        logger.error(f"Error retrieving risks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve risks")


@router.get("/dashboard/{user_id}")
async def get_dashboard_stats(user_id: str):
    """
    Get dashboard statistics for user
    """
    try:
        stats = await db_service.get_user_dashboard_stats(user_id)
        return stats
        
    except Exception as e:
        logger.error(f"Error retrieving dashboard stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard stats")


@router.get("/audit-log")
async def get_audit_log(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(50, le=100)
):
    """
    Get audit log entries for user
    """
    try:
        logs = await db_service.get_audit_logs(user_id=user_id, limit=limit)
        return {"logs": logs}
        
    except Exception as e:
        logger.error(f"Error retrieving audit logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve audit logs")
