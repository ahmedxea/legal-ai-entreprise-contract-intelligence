"""
Storage service factory.

Returns the appropriate storage backend based on runtime configuration:
  - When AZURE_STORAGE_CONNECTION_STRING is set: Azure Blob Storage
  - Otherwise: Local filesystem under backend/data/uploads/

This means the same contracts.py code works in development (local) and
in production (Azure Blob) without any code changes — just set or unset
the environment variable.
"""
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_storage_service():
    """
    Instantiate and return the active storage backend.

    Azure Blob is used when AZURE_STORAGE_CONNECTION_STRING is non-empty.
    Falls back to local filesystem storage (never to a mock:// stub).
    """
    if settings.AZURE_STORAGE_CONNECTION_STRING:
        # Only attempt Azure Storage if the connection string looks non-trivial
        conn = settings.AZURE_STORAGE_CONNECTION_STRING.strip()
        if conn and conn not in ("", "your-connection-string-here"):
            try:
                from app.services.storage_service import StorageService
                logger.info("Storage backend: Azure Blob Storage")
                return StorageService()
            except Exception as exc:
                logger.error(
                    f"Failed to initialise Azure Blob Storage — falling back to local storage. Error: {exc}"
                )

    from app.services.local_storage_service import LocalStorageService
    logger.info("Storage backend: local filesystem (data/uploads/)")
    return LocalStorageService()


# Module-level singleton — importable directly
storage = get_storage_service()
