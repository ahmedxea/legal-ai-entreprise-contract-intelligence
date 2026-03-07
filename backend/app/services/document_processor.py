"""
Document Processor Service

Orchestrates the Phase 1 ingestion pipeline:
  UPLOADED → EXTRACTING → text saved → chunks saved → EXTRACTED

This service is intentionally free of AI logic. Its sole responsibility is
converting uploaded files into persisted, structured text ready for analysis.

Called as a FastAPI BackgroundTask so the upload HTTP response is not blocked.
"""
import logging
from typing import Optional

from app.agents.document_parser import DocumentParserAgent
from app.services.sqlite_service import DatabaseService
from app.models.schemas import ContractStatus

logger = logging.getLogger(__name__)

# Chunking constants — match the spec
_MAX_CHUNK_SIZE = 1000
_CHUNK_OVERLAP = 200


class DocumentProcessorService:
    """
    Ingestion pipeline: parse → chunk → persist.

    Each public method is designed to be safe to call from a BackgroundTask:
    all exceptions are caught internally; the contract status is set to FAILED
    so the caller can detect the outcome by polling GET /contracts/{id}.
    """

    def __init__(
        self,
        db_service: Optional[DatabaseService] = None,
        parser_agent: Optional[DocumentParserAgent] = None,
    ) -> None:
        # Allow injection for testing; default to module singletons otherwise
        self._db = db_service or DatabaseService()
        self._parser = parser_agent or DocumentParserAgent()

    # ── Public pipeline entry point ───────────────────────────────────────────

    async def process(self, contract_id: str, blob_url: str, file_type: str) -> None:
        """
        Run the full extraction pipeline for one document.

        Steps:
          1. Guard: skip if text already extracted (idempotent re-trigger)
          2. Set status → EXTRACTING
          3. Parse file (PDF or DOCX)
          4. Normalise paragraphs
          5. Chunk text
          6. Persist extracted text + chunks
          7. Update page_count on contracts row
          8. Set status → EXTRACTED

        On any failure the status is set to FAILED and the error is logged.
        No exception is re-raised because this runs in a background task.
        """
        logger.info(f"[processor] Starting extraction for contract {contract_id}")

        try:
            # Guard: already processed — safe to re-trigger but skip work
            existing = await self._db.get_document_text(contract_id)
            if existing is not None:
                logger.info(
                    f"[processor] Text already extracted for {contract_id}; skipping"
                )
                return

            # Step 1: mark as extracting
            await self._db.update_contract_status(contract_id, ContractStatus.EXTRACTING)

            # Step 2: parse
            parse_result = await self._parser.parse_document(blob_url)
            raw_text: str = parse_result.get("full_text", "").strip()

            if not raw_text:
                raise ValueError(
                    f"Extracted text is empty for contract {contract_id}. "
                    "The document may be blank, image-only, or corrupted."
                )

            # Step 3: normalise paragraphs
            paragraphs = self._parser.extract_paragraphs(parse_result)

            # Step 4: chunk
            chunks = self._parser.chunk_text(
                raw_text,
                max_chunk_size=_MAX_CHUNK_SIZE,
                overlap=_CHUNK_OVERLAP,
            )

            page_count: Optional[int] = parse_result.get("page_count")
            detected_file_type: str = parse_result.get("file_type", file_type)

            # Step 5: persist text
            await self._db.save_document_text(
                document_id=contract_id,
                raw_text=raw_text,
                paragraphs=paragraphs,
                page_count=page_count,
                file_type=detected_file_type,
            )

            # Step 6: persist chunks
            await self._db.save_chunks(contract_id, chunks)

            # Step 7: update page_count on contracts row (best-effort)
            if page_count is not None:
                await self._db.update_contract_page_count(contract_id, page_count)

            # Step 8: mark as ready
            await self._db.update_contract_status(contract_id, ContractStatus.EXTRACTED)

            logger.info(
                f"[processor] Extraction complete for {contract_id}: "
                f"{len(raw_text)} chars, {len(paragraphs)} paragraphs, "
                f"{len(chunks)} chunks"
            )

        except Exception as exc:
            logger.error(
                f"[processor] Extraction failed for {contract_id}: {exc}",
                exc_info=True,
            )
            try:
                await self._db.update_contract_status(contract_id, ContractStatus.FAILED)
            except Exception:
                pass  # best-effort; do not mask original error

    # ── Convenience read-throughs ─────────────────────────────────────────────

    async def get_text(self, contract_id: str):
        """Return raw stored text record or None if not yet extracted."""
        return await self._db.get_document_text(contract_id)

    async def get_chunks(self, contract_id: str):
        """Return stored chunks or empty list if not yet extracted."""
        return await self._db.get_chunks(contract_id)


# Module-level singleton — mirrors the pattern used by other services
document_processor = DocumentProcessorService()
