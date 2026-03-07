"""
Configuration settings for the CLM application
Loads from environment variables and .env file
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-08-01-preview"
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4o"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "text-embedding-3-large"
    
    # Azure Blob Storage
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER_NAME: str = "contracts"
    
    # Azure Cosmos DB
    COSMOS_ENDPOINT: str = ""
    COSMOS_KEY: str = ""
    COSMOS_DATABASE_NAME: str = "clm_database"
    
    # Azure AI Search
    AZURE_SEARCH_ENDPOINT: str = ""
    AZURE_SEARCH_API_KEY: str = ""
    AZURE_SEARCH_INDEX_NAME: str = "contracts-index"
    
    # Azure Document Intelligence
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: str = ""
    AZURE_DOCUMENT_INTELLIGENCE_KEY: str = ""
    
    # Database — defaults to local SQLite; override with postgresql+asyncpg:// for production
    DATABASE_URL: str = ""
    
    # Azure SQL Database (alternative to DATABASE_URL for Azure SQL specific connection)
    SQL_CONNECTION_STRING: str = ""

    # API Configuration - parse comma-separated string
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    MAX_FILE_SIZE_MB: int = 50
    SUPPORTED_FILE_TYPES: str = ".pdf,.docx,.txt,.png,.jpg,.jpeg,.tif,.tiff,.bmp"

    # AI processing
    # Set MOCK_MODE=true to skip Ollama/Azure AI calls and return stub responses.
    # Automatically forced to true when ENVIRONMENT is not "production" and no AI
    # credentials are configured.
    MOCK_MODE: bool = False

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    # Set COOKIE_SECURE=true in production (HTTPS only).
    # Must be False for localhost development.
    COOKIE_SECURE: bool = False

    # Rate limiting (requests per minute per IP)
    RATE_LIMIT_UPLOAD: str = "10/minute"
    RATE_LIMIT_ANALYZE: str = "10/minute"
    
    # Processing
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    MAX_TOKENS_EXTRACTION: int = 4000
    MAX_TOKENS_ANALYSIS: int = 8000
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS as list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def supported_file_types_list(self) -> List[str]:
        """Parse SUPPORTED_FILE_TYPES as list"""
        return [ft.strip() for ft in self.SUPPORTED_FILE_TYPES.split(",")]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Create settings instance
settings = Settings()
