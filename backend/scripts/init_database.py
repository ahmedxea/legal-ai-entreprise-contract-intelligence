"""
Database initialization script for Azure SQL Database
Creates all tables and indexes required for the Lexra platform
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.azure_sql_service import azure_sql_service
from app.models.database import Base
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_database():
    """Initialize Azure SQL Database with all required tables"""
    
    logger.info("=" * 60)
    logger.info("Lexra Database Initialization")
    logger.info("=" * 60)
    
    # Check configuration
    if settings.SQL_CONNECTION_STRING:
        logger.info("✓ Using Azure SQL Database (SQL_CONNECTION_STRING)")
    elif settings.DATABASE_URL:
        logger.info(f"✓ Using DATABASE_URL: {settings.DATABASE_URL.split('@')[0]}...")
    else:
        logger.info("✓ Using SQLite fallback (./data/contracts.db)")
    
    try:
        # Create all tables
        logger.info("\nCreating database tables...")
        await azure_sql_service.create_tables()
        
        logger.info("\n✓ Database initialization complete!")
        logger.info("\nCreated tables:")
        logger.info("  - users")
        logger.info("  - sessions")
        logger.info("  - contracts")
        logger.info("  - document_text")
        logger.info("  - document_chunks")
        logger.info("  - contract_entities")
        logger.info("  - contract_summaries")
        logger.info("  - contract_risks")
        logger.info("  - contract_gaps")
        logger.info("  - audit_logs")
        
        logger.info("\n" + "=" * 60)
        logger.info("Ready to start the application!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n✗ Database initialization failed: {e}", exc_info=True)
        sys.exit(1)


async def create_demo_user():
    """Create demo user for testing"""
    from app.services.auth_service import hash_password
    
    try:
        logger.info("\nCreating demo user...")
        
        # Check if demo user already exists
        existing = await azure_sql_service.get_user_by_email("demo@lexra.ai")
        
        if existing:
            logger.info("✓ Demo user already exists: demo@lexra.ai")
        else:
            # Create demo user
            await azure_sql_service.create_user(
                email="demo@lexra.ai",
                password_hash=hash_password("demo12345@"),
                full_name="Demo User",
                organization="Lexra Demo"
            )
            logger.info("✓ Demo user created: demo@lexra.ai")
            
    except Exception as e:
        logger.error(f"Error creating demo user: {e}")


if __name__ == "__main__":
    print("\nLexra Database Setup\n")
    print("This script will create all required database tables.")
    print("Make sure your database connection is configured in .env\n")
    
    if settings.SQL_CONNECTION_STRING or settings.DATABASE_URL:
        proceed = input("Proceed with database initialization? (yes/no): ")
        if proceed.lower() not in ["yes", "y"]:
            print("Aborted.")
            sys.exit(0)
    
    asyncio.run(init_database())
    asyncio.run(create_demo_user())
