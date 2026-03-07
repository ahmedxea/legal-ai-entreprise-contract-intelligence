"""
Storage Quota Service

Enforces per-user document count and storage limits for public-facing safety.
"""
import logging
from dataclasses import dataclass
from typing import Optional

from app.core.config import settings
from app.services.sqlite_service import DatabaseService

logger = logging.getLogger(__name__)

MAX_DOCUMENTS_PER_USER: int = settings.MAX_DOCUMENTS_PER_USER
MAX_USER_STORAGE_BYTES: int = settings.MAX_USER_STORAGE_MB * 1024 * 1024
MAX_FILE_SIZE_BYTES: int = settings.MAX_FILE_SIZE_MB * 1024 * 1024

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@dataclass
class QuotaValidationResult:
    allowed: bool
    error: Optional[str] = None
    document_count: int = 0
    storage_used_bytes: int = 0


class StorageQuotaService:
    """Validates upload requests against per-user quotas."""

    def __init__(self, db_service: Optional[DatabaseService] = None) -> None:
        self._db = db_service or DatabaseService()

    async def get_user_document_count(self, user_id: str) -> int:
        return await self._db.get_user_document_count(user_id)

    async def get_user_storage_usage(self, user_id: str) -> int:
        return await self._db.get_user_storage_usage(user_id)

    async def validate_upload(
        self,
        user_id: str,
        file_size: int,
        filename: str,
        content_type: Optional[str] = None,
    ) -> QuotaValidationResult:
        """
        Run all pre-upload validations. Returns a result indicating whether
        the upload is allowed or the specific rejection reason.
        """
        import os

        # 1. File extension check
        ext = os.path.splitext(filename or "")[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return QuotaValidationResult(
                allowed=False,
                error=f"Unsupported file type: '{ext}'. Only PDF and DOCX files are accepted.",
            )

        # 2. MIME type check (if provided by the client)
        if content_type and content_type not in ALLOWED_MIME_TYPES:
            # Also accept generic octet-stream (some clients send it)
            if content_type != "application/octet-stream":
                return QuotaValidationResult(
                    allowed=False,
                    error=f"Invalid MIME type: '{content_type}'. Only PDF and DOCX files are accepted.",
                )

        # 3. Single-file size limit
        if file_size > MAX_FILE_SIZE_BYTES:
            size_mb = file_size / (1024 * 1024)
            return QuotaValidationResult(
                allowed=False,
                error=f"File size ({size_mb:.1f} MB) exceeds the {settings.MAX_FILE_SIZE_MB} MB limit.",
            )

        if file_size == 0:
            return QuotaValidationResult(
                allowed=False,
                error="Uploaded file is empty.",
            )

        # 4. Document count limit
        doc_count = await self.get_user_document_count(user_id)
        if doc_count >= MAX_DOCUMENTS_PER_USER:
            return QuotaValidationResult(
                allowed=False,
                error=f"Document limit reached ({MAX_DOCUMENTS_PER_USER}). Delete a document before uploading a new one.",
                document_count=doc_count,
            )

        # 5. Storage quota
        storage_used = await self.get_user_storage_usage(user_id)
        if storage_used + file_size > MAX_USER_STORAGE_BYTES:
            used_mb = storage_used / (1024 * 1024)
            limit_mb = settings.MAX_USER_STORAGE_MB
            return QuotaValidationResult(
                allowed=False,
                error=f"Storage quota exceeded. You are using {used_mb:.1f} MB of {limit_mb} MB allowed.",
                document_count=doc_count,
                storage_used_bytes=storage_used,
            )

        return QuotaValidationResult(
            allowed=True,
            document_count=doc_count,
            storage_used_bytes=storage_used,
        )


# Module-level singleton
storage_quota_service = StorageQuotaService()
