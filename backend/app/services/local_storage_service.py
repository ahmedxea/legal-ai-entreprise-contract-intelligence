"""
Local file storage service (free alternative to Azure Blob Storage)
"""
import logging
from typing import Optional
import uuid
from datetime import datetime
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)


class LocalStorageService:
    """Service for managing file storage locally"""
    
    def __init__(self, storage_path: str = "data/uploads"):
        """
        Initialize local storage
        
        Args:
            storage_path: Path to store uploaded files
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Local storage initialized at: {self.storage_path.absolute()}")
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        user_id: str
    ) -> str:
        """
        Upload a file to local storage
        
        Args:
            file_content: File bytes
            filename: Original filename
            user_id: User ID who owns the file
            
        Returns:
            Local file path
        """
        try:
            # Create user directory
            user_dir = self.storage_path / user_id
            user_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            file_ext = Path(filename).suffix
            unique_filename = f"{timestamp}_{unique_id}{file_ext}"
            
            # Full file path
            file_path = user_dir / unique_filename
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"File uploaded: {file_path}")
            
            # Return absolute path as string
            return str(file_path.absolute())
            
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    async def download_file(self, file_path: str) -> bytes:
        """
        Download a file from local storage
        
        Args:
            file_path: Path to the file
            
        Returns:
            File content as bytes
        """
        try:
            path = Path(file_path).resolve()
            storage_root = self.storage_path.resolve()
            
            # Security: ensure file is within storage directory (prevent path traversal)
            if not str(path).startswith(str(storage_root)):
                logger.error(f"Path traversal attempt blocked: {file_path}")
                raise PermissionError(f"Access denied: file outside storage directory")
            
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            with open(path, 'rb') as f:
                content = f.read()
            
            logger.info(f"File downloaded: {file_path} ({len(content)} bytes)")
            return content
            
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            raise
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from local storage
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            path = Path(file_path)
            
            if path.exists():
                path.unlink()
                logger.info(f"File deleted: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    async def list_files(self, user_id: str) -> list:
        """
        List all files for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of file paths
        """
        try:
            user_dir = self.storage_path / user_id
            
            if not user_dir.exists():
                return []
            
            files = [str(f.absolute()) for f in user_dir.iterdir() if f.is_file()]
            return files
            
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []


# Global instance
local_storage_service = LocalStorageService()
