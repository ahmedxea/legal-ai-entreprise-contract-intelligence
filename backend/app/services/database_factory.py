"""
Database Factory - Provides unified interface for SQLite or Azure SQL
Automatically selects the appropriate database service based on configuration
"""
import logging
from typing import Union

from app.core.config import settings
from app.services.sqlite_service import DatabaseService as SQLiteService
from app.services.azure_sql_service import AzureSQLService

logger = logging.getLogger(__name__)


class DatabaseFactory:
    """Factory class to provide the appropriate database service"""
    
    @staticmethod
    def get_database_service() -> Union[SQLiteService, AzureSQLService]:
        """
        Return the appropriate database service based on configuration.
        
        Priority order:
        1. SQL_CONNECTION_STRING (Azure SQL)
        2. DATABASE_URL (PostgreSQL, Azure SQL, or any SQLAlchemy-supported DB)
        3. SQLite (fallback for local development)
        
        Returns:
            Database service instance
        """
        
        if settings.SQL_CONNECTION_STRING:
            logger.info("Using Azure SQL Database (SQL_CONNECTION_STRING)")
            from app.services.azure_sql_service import azure_sql_service
            return azure_sql_service
            
        elif settings.DATABASE_URL:
            logger.info(f"Using DATABASE_URL database service")
            from app.services.azure_sql_service import azure_sql_service
            return azure_sql_service
            
        else:
            logger.info("Using SQLite database service (local development)")
            return SQLiteService()


# Global database service instance
database_service = DatabaseFactory.get_database_service()


def get_db():
    """Dependency injection helper for FastAPI routes"""
    return database_service
