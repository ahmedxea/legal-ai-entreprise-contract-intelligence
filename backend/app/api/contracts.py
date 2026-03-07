"""
Contracts API endpoints
"""
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, HTTPException, Depends, Query, Header, Request
from fastapi.responses import StreamingResponse, RedirectResponse
from typing import List, Optional
import logging
from datetime import datetime
import os
import mimetypes

from app.models.schemas import (
    ContractUploadResponse, ContractDetail, ContractListItem,
    ContractStatus, Language, Industry, GoverningLaw,
    DocumentTextResponse, DocumentChunksResponse, ChunkItem,
    ContractAnalysisResponse,
)
from app.services.storage_factory import storage as storage_service
from app.services.sqlite_service import DatabaseService
from app.services.document_processor import document_processor
from app.services.auth_service import validate_session
from app.core.config import settings
from app.core.limiter import limiter
from app.agents.orchestrator import ContractOrchestrator
from app.services.analysis_service import analysis_service as phase2_analysis_service

logger = logging.getLogger(__name__)
router = APIRouter()

# Services
db_service = DatabaseService()
orchestrator = ContractOrchestrator()

# Allowed file types and max size from config
ALLOWED_EXTENSIONS = set(settings.supported_file_types_list)
MAX_FILE_SIZE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


def _get_user_id_from_token(authorization: Optional[str]) -> str:
    """Extract and validate user from auth token. Falls back to 'anonymous' for dev."""
    if not authorization:
        return "anonymous"
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        return "anonymous"
    user = validate_session(token)
    if not user:
        return "anonymous"
    return user.get("id", "anonymous")


@router.post("/upload", response_model=ContractUploadResponse)
@limiter.limit(settings.RATE_LIMIT_UPLOAD)
async def upload_contract(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: Language = Query(Language.ENGLISH),
    industry: Optional[Industry] = Query(None),
    authorization: Optional[str] = Header(None),
):
    """
    Upload a contract document for analysis.
    Accepts PDF and DOCX files up to the configured size limit.
    Uses auth token to identify the user.
    """
    try:
        user_id = _get_user_id_from_token(authorization)

        # Validate file type
        file_ext = os.path.splitext(file.filename or "")[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: '{file_ext}'. Only {', '.join(ALLOWED_EXTENSIONS)} files are accepted."
            )

        # Read and validate file size
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File size ({len(content) / (1024*1024):.1f} MB) exceeds the {settings.MAX_FILE_SIZE_MB} MB limit."
            )

        # Store file
        logger.info(f"Uploading contract: {file.filename} for user: {user_id}")
        blob_url = await storage_service.upload_file(
            file_content=content,
            filename=file.filename,
            user_id=user_id
        )

        # Create contract record in database (now includes file metadata)
        contract_id = await db_service.create_contract(
            user_id=user_id,
            filename=file.filename,
            blob_url=blob_url,
            language=language,
            industry=industry,
            file_size=len(content),
            file_type=file_ext.lstrip("."),
        )

        # Log audit event
        await db_service.create_audit_log(
            user_id=user_id,
            action="upload_contract",
            contract_id=contract_id,
            metadata={"filename": file.filename, "size": len(content)}
        )

        # Kick off text extraction as a background task so this response is immediate
        background_tasks.add_task(
            document_processor.process,
            contract_id,
            blob_url,
            file_ext.lstrip("."),
        )

        logger.info(f"Contract uploaded successfully: {contract_id}")

        # Return safe response — no file paths or internal URLs
        return ContractUploadResponse(
            contract_id=contract_id,
            filename=file.filename,
            status=ContractStatus.UPLOADED,
            message="Contract uploaded successfully. Text extraction started."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading contract: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload contract. Please try again.")


async def _run_analysis_background(
    contract_id: str,
    blob_url: str,
    language: Language,
    industry: Optional[str],
    user_id: str,
) -> None:
    """
    Execute AI analysis in a background task so the HTTP request returns immediately.
    Failures are logged and the contract status is set to FAILED; the caller can poll
    GET /{contract_id} to check status.
    """
    try:
        analysis_result = await orchestrator.analyze_contract(
            contract_id=contract_id,
            blob_url=blob_url,
            language=language,
            industry=industry,
        )
        await db_service.update_contract_analysis(contract_id, analysis_result)
        await db_service.update_contract_status(contract_id, ContractStatus.ANALYZED)
        await db_service.create_audit_log(
            user_id=user_id,
            action="analyze_contract",
            contract_id=contract_id,
        )
        logger.info(f"Background analysis completed: {contract_id}")
    except Exception as exc:
        logger.error(f"Background analysis failed for {contract_id}: {exc}", exc_info=True)
        try:
            await db_service.update_contract_status(contract_id, ContractStatus.FAILED)
        except Exception:
            pass


@router.post("/{contract_id}/analyze")
@limiter.limit(settings.RATE_LIMIT_ANALYZE)
async def analyze_contract(
    request: Request,
    contract_id: str,
    background_tasks: BackgroundTasks,
    user_id: Optional[str] = Query(None, description="User ID"),
    authorization: Optional[str] = Header(None),
):
    """
    Trigger AI analysis of an uploaded contract.
    Returns 202 Accepted immediately; analysis runs as a background job.
    Poll GET /{contract_id} and check the `status` field for completion.
    """
    try:
        resolved_user_id = user_id or _get_user_id_from_token(authorization)
        contract = await db_service.get_contract(contract_id, resolved_user_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")

        # Prevent duplicate analysis runs
        if contract.get("status") == ContractStatus.PROCESSING:
            return {
                "contract_id": contract_id,
                "status": "processing",
                "message": "Analysis already in progress.",
            }

        await db_service.update_contract_status(contract_id, ContractStatus.PROCESSING)
        logger.info(f"Queued background analysis for contract: {contract_id}")

        background_tasks.add_task(
            phase2_analysis_service.run,
            contract_id,
        )

        return {
            "contract_id": contract_id,
            "status": "processing",
            "message": "Analysis started. Poll GET /api/contracts/{contract_id} to check progress.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error queuing contract analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start contract analysis")


@router.get("/{contract_id}/analysis", response_model=ContractAnalysisResponse)
async def get_contract_analysis(
    contract_id: str,
    user_id: Optional[str] = Query(None, description="User ID"),
    authorization: Optional[str] = Header(None),
):
    """
    Return the Phase 2 structured analysis results for a contract.

    Returns the latest saved results from all four analysis jobs:
      - entities (structured extraction)
      - summary (executive summary)
      - risks (risk detection)
      - missing_clauses (gap analysis)

    Returns 404 if the contract does not exist or analysis has not yet completed.
    """
    try:
        resolved_user_id = user_id or _get_user_id_from_token(authorization)
        contract = await db_service.get_contract(contract_id, resolved_user_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")

        # Read from dedicated Phase 2 tables
        entities = await db_service.get_contract_entities(contract_id)
        summary = await db_service.get_contract_summary(contract_id)
        risks = await db_service.get_contract_risks(contract_id)
        missing_clauses = await db_service.get_contract_gaps(contract_id)

        if entities is None and summary is None and not risks and missing_clauses is None:
            # Analysis has not been run yet or is still in progress
            status = contract.get("status", "unknown")
            if status == ContractStatus.PROCESSING.value:
                raise HTTPException(
                    status_code=202,
                    detail="Analysis in progress. Try again shortly.",
                )
            raise HTTPException(
                status_code=404,
                detail="Analysis not yet available. POST /api/contracts/{contract_id}/analyze first.",
            )

        overall_risk_score = phase2_analysis_service._compute_risk_score(risks or [])

        return ContractAnalysisResponse(
            contract_id=contract_id,
            status=contract.get("status", "unknown"),
            summary=summary,
            entities=entities,
            risks=risks or [],
            missing_clauses=missing_clauses or [],
            overall_risk_score=overall_risk_score,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving contract analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve contract analysis")


@router.get("/{contract_id}", response_model=ContractDetail)
async def get_contract(
    contract_id: str,
    user_id: Optional[str] = Query(None, description="User ID"),
    authorization: Optional[str] = Header(None),
):
    """
    Get detailed information about a specific contract
    """
    try:
        resolved_user_id = user_id or _get_user_id_from_token(authorization)
        contract = await db_service.get_contract(contract_id, resolved_user_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        return contract
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving contract: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve contract")


@router.get("/{contract_id}/text", response_model=DocumentTextResponse)
async def get_contract_text(
    contract_id: str,
    user_id: Optional[str] = Query(None, description="User ID"),
    authorization: Optional[str] = Header(None),
):
    """
    Return the extracted raw text and paragraph list for a contract.

    Returns 404 if text extraction has not completed yet.
    Poll GET /{contract_id} and wait for status 'extracted' before calling this.
    """
    try:
        resolved_user_id = user_id or _get_user_id_from_token(authorization)

        # Ownership check
        contract = await db_service.get_contract(contract_id, resolved_user_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")

        text_record = await document_processor.get_text(contract_id)
        if text_record is None:
            raise HTTPException(
                status_code=404,
                detail="Text not yet extracted. Poll GET /contracts/{contract_id} until status is 'extracted'.",
            )

        return DocumentTextResponse(
            document_id=contract_id,
            raw_text=text_record["raw_text"],
            paragraphs=text_record["paragraphs"],
            page_count=text_record.get("page_count"),
            file_type=text_record.get("file_type"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving contract text: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve contract text")


@router.get("/{contract_id}/chunks", response_model=DocumentChunksResponse)
async def get_contract_chunks(
    contract_id: str,
    user_id: Optional[str] = Query(None, description="User ID"),
    authorization: Optional[str] = Header(None),
):
    """
    Return all text chunks for a contract in index order.

    Returns 404 if chunking has not completed yet.
    """
    try:
        resolved_user_id = user_id or _get_user_id_from_token(authorization)

        contract = await db_service.get_contract(contract_id, resolved_user_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")

        raw_chunks = await document_processor.get_chunks(contract_id)
        if not raw_chunks:
            raise HTTPException(
                status_code=404,
                detail="Chunks not yet available. Poll GET /contracts/{contract_id} until status is 'extracted'.",
            )

        return DocumentChunksResponse(
            document_id=contract_id,
            total_chunks=len(raw_chunks),
            chunks=[
                ChunkItem(
                    chunk_id=c["chunk_id"],
                    chunk_index=c["chunk_index"],
                    chunk_text=c["chunk_text"],
                )
                for c in raw_chunks
            ],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving contract chunks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve contract chunks")


@router.get("/", response_model=List[ContractListItem])
async def list_contracts(
    user_id: Optional[str] = Query(None, description="User ID"),
    status: Optional[ContractStatus] = None,
    limit: int = Query(50, le=100),
    authorization: Optional[str] = Header(None),
):
    """
    List all contracts for a user
    """
    try:
        resolved_user_id = user_id or _get_user_id_from_token(authorization)
        contracts = await db_service.list_contracts(
            user_id=resolved_user_id,
            status=status,
            limit=limit
        )
        return contracts
        
    except Exception as e:
        logger.error(f"Error listing contracts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list contracts")


@router.get("/{contract_id}/file")
async def download_contract_file(
    contract_id: str,
    user_id: Optional[str] = Query(None, description="User ID"),
    authorization: Optional[str] = Header(None),
):
    """
    Stream the original uploaded file (PDF / DOCX) back to the client.
    For Azure blob URLs the request is redirected; for local paths the file
    is streamed directly.
    """
    try:
        resolved_user_id = user_id or _get_user_id_from_token(authorization)
        contract = await db_service.get_contract(contract_id, resolved_user_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")

        blob_url: str = contract.get("blob_url", "")
        filename: str = contract.get("filename", "contract")

        # Azure / public HTTP URL → redirect the browser to it directly
        if blob_url.startswith("http://") or blob_url.startswith("https://"):
            return RedirectResponse(url=blob_url)

        # Local file path → stream the bytes
        file_bytes = await storage_service.download_file(blob_url)

        mime, _ = mimetypes.guess_type(filename)
        if not mime:
            mime = "application/octet-stream"

        import io
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type=mime,
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Content-Length": str(len(file_bytes)),
            },
        )

    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Original file not found on disk")
    except Exception as e:
        logger.error(f"Error serving contract file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to serve contract file")


@router.delete("/{contract_id}")
async def delete_contract(
    contract_id: str,
    user_id: Optional[str] = Query(None, description="User ID"),
    authorization: Optional[str] = Header(None),
):
    """
    Delete a contract
    """
    try:
        resolved_user_id = user_id or _get_user_id_from_token(authorization)
        # Get contract to verify ownership
        contract = await db_service.get_contract(contract_id, resolved_user_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        # Delete from blob storage
        await storage_service.delete_file(contract['blob_url'])
        
        # Delete from database
        await db_service.delete_contract(contract_id)
        
        # Log audit event
        await db_service.create_audit_log(
            user_id=resolved_user_id,
            action="delete_contract",
            contract_id=contract_id
        )
        
        return {"message": "Contract deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting contract: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete contract")
