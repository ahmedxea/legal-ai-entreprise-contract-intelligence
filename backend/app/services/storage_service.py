"""
Azure Blob Storage service for file management
"""
from azure.storage.blob import BlobServiceClient, BlobClient, ContentSettings
from azure.core.exceptions import AzureError
import logging
from typing import Optional
import uuid
from datetime import datetime
import io

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing file storage in Azure Blob Storage"""
    
    def __init__(self):
        self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = settings.AZURE_STORAGE_CONTAINER_NAME
        self.blob_service_client = None
        
        if self.connection_string:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    self.connection_string
                )
                self._ensure_container_exists()
            except Exception as e:
                logger.warning(f"Failed to initialize Blob Storage: {e}")
    
    def _ensure_container_exists(self):
        """Create container if it doesn't exist"""
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            if not container_client.exists():
                container_client.create_container()
                logger.info(f"Created container: {self.container_name}")
        except Exception as e:
            logger.error(f"Error ensuring container exists: {e}")
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        user_id: str
    ) -> str:
        """
        Upload a file to Blob Storage
        
        Args:
            file_content: File bytes
            filename: Original filename
            user_id: User ID who owns the file
            
        Returns:
            Blob URL
        """
        if not self.blob_service_client:
            logger.warning("Blob Storage not configured, using mock URL")
            return f"mock://contracts/{user_id}/{filename}"
        
        try:
            # Generate unique blob name
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            blob_name = f"{user_id}/{timestamp}_{filename}"
            
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Set content type based on file extension
            content_type = (
                "application/pdf" if filename.endswith('.pdf')
                else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
            # Upload file
            blob_client.upload_blob(
                file_content,
                content_settings=ContentSettings(content_type=content_type),
                overwrite=True
            )
            
            logger.info(f"Uploaded file to blob storage: {blob_name}")
            return blob_client.url
            
        except AzureError as e:
            logger.error(f"Azure error uploading file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    async def download_file(self, blob_url: str) -> bytes:
        """
        Download a file from Blob Storage
        
        Args:
            blob_url: Blob URL
            
        Returns:
            File bytes
        """
        if blob_url.startswith("mock://"):
            logger.warning("Mock blob URL, returning empty bytes")
            return b""
        
        try:
            # Use authenticated client when available (avoids 403 on private containers)
            if self.blob_service_client:
                blob_client = BlobClient.from_blob_url(
                    blob_url,
                    credential=self.blob_service_client.credential,
                )
            else:
                blob_client = BlobClient.from_blob_url(blob_url)
            downloader = blob_client.download_blob()
            return downloader.readall()
            
        except AzureError as e:
            logger.error(f"Azure error downloading file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            raise
    
    async def delete_file(self, blob_url: str) -> bool:
        """
        Delete a file from Blob Storage
        
        Args:
            blob_url: Blob URL
            
        Returns:
            True if successful
        """
        if blob_url.startswith("mock://"):
            logger.warning("Mock blob URL, skipping delete")
            return True
        
        try:
            blob_client = BlobClient.from_blob_url(blob_url)
            blob_client.delete_blob()
            logger.info(f"Deleted blob: {blob_url}")
            return True
            
        except AzureError as e:
            logger.error(f"Azure error deleting file: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    async def get_file_metadata(self, blob_url: str) -> dict:
        """
        Get file metadata
        
        Args:
            blob_url: Blob URL
            
        Returns:
            Metadata dictionary
        """
        try:
            blob_client = BlobClient.from_blob_url(blob_url)
            properties = blob_client.get_blob_properties()
            
            return {
                "size": properties.size,
                "content_type": properties.content_settings.content_type,
                "created_on": properties.creation_time,
                "last_modified": properties.last_modified
            }
            
        except Exception as e:
            logger.error(f"Error getting file metadata: {e}")
            return {}
