"""
Azure SQL compatible authentication service with async support
Handles user registration, login, session management
"""
import logging
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from hashlib import sha256

from app.core.config import settings

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash password with random salt using SHA-256"""
    salt = secrets.token_hex(16)
    hash_value = sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{hash_value}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against stored hash"""
    try:
        salt, stored_hash = password_hash.split(":")
        return sha256(f"{salt}{password}".encode()).hexdigest() == stored_hash
    except (ValueError, AttributeError):
        return False


class AzureAuthService:
    """
    Authentication service for Azure SQL Database.
    
    Note: This service expects an AzureSQLService instance via database_factory.
    Type errors about missing methods are expected when using DatabaseService (SQLite).
    The factory ensures the correct service is provided based on configuration.
    """
    
    def __init__(self):
        """Initialize with database service"""
        from app.services.database_factory import database_service
        self.db = database_service  # Will be AzureSQLService if SQL_CONNECTION_STRING or DATABASE_URL is set
    
    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        organization: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Register a new user account"""
        password_hash = hash_password(password)
        return await self.db.create_user(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            organization=organization
        )
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user by email and password"""
        user = await self.db.get_user_by_email(email)
        
        if user and user.get("password_hash") and verify_password(password, user["password_hash"]):
            # Update last login timestamp
            await self.db.update_user_last_login(user["id"])
            
            return {
                "id": user["id"],
                "email": user["email"],
                "full_name": user.get("full_name") or user.get("name") or "",
                "name": user.get("full_name") or user.get("name") or "",
                "organization": user.get("organization") or "",
                "role": user.get("role") or "user"
            }
        
        return None
    
    async def create_session(self, user_id: str, hours: int = 24) -> str:
        """Create a session token for the user"""
        token = secrets.token_urlsafe(48)
        expires_at = datetime.utcnow() + timedelta(hours=hours)
        
        await self.db.create_session(user_id, token, expires_at)
        return token
    
    async def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a session token and return user data"""
        return await self.db.get_session(token)
    
    async def delete_session(self, token: str):
        """Delete a session token (logout)"""
        await self.db.delete_session(token)


# Singleton instance
azure_auth_service = AzureAuthService()
