#!/usr/bin/env python3
"""
Quick verification script to test Azure SQL integration
Run this after setting up your database configuration
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


async def verify_setup():
    """Verify database configuration and connectivity"""
    
    print("=" * 60)
    print("Lexra Backend Configuration Verification")
    print("=" * 60)
    print()
    
    # Check environment
    print(f"Environment: {settings.ENVIRONMENT}")
    print()
    
    # Check database configuration
    print("Database Configuration:")
    if settings.SQL_CONNECTION_STRING:
        print("✅ SQL_CONNECTION_STRING configured (Azure SQL)")
        db_type = "Azure SQL Server"
    elif settings.DATABASE_URL:
        print(f"✅ DATABASE_URL configured")
        db_url = settings.DATABASE_URL
        if "postgresql" in db_url:
            db_type = "PostgreSQL"
        elif "mysql" in db_url:
            db_type = "MySQL"
        elif "sqlite" in db_url:
            db_type = "SQLite"
        else:
            db_type = "Unknown"
    else:
        print("✅ No SQL config - using SQLite (default)")
        db_type = "SQLite (local)"
    
    print(f"   Database Type: {db_type}")
    print()
    
    # Check storage configuration
    print("Storage Configuration:")
    if settings.AZURE_STORAGE_CONNECTION_STRING:
        print("✅ Azure Blob Storage configured")
    else:
        print("⚠️  Azure Blob Storage NOT configured - using local storage")
    print()
    
    # Check AI configuration
    print("AI Processing Configuration:")
    if settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY:
        print(f"✅ Azure OpenAI configured")
        print(f"   Endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
        print(f"   Model: {settings.AZURE_OPENAI_DEPLOYMENT_NAME}")
    else:
        print("⚠️  Azure OpenAI NOT configured - will use Ollama or mock mode")
    print()
    
    # Check security configuration
    print("Security Configuration:")
    if settings.SECRET_KEY != "your-secret-key-change-in-production":
        print("✅ JWT Secret Key configured")
    else:
        print("⚠️  Using default SECRET_KEY - change in production!")
    print(f"   Token expiry: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
    print(f"   HTTPS cookies: {settings.COOKIE_SECURE}")
    print()
    
    # Test database connectivity (if Azure SQL/PostgreSQL)
    if settings.SQL_CONNECTION_STRING or (settings.DATABASE_URL and "sqlite" not in settings.DATABASE_URL):
        print("Testing database connectivity...")
        try:
            from app.services.azure_sql_service import azure_sql_service
            
            # Try to query database
            await azure_sql_service._get_db_session().__aenter__()
            print("✅ Database connection successful!")
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print()
            print("Troubleshooting:")
            print("  1. Check your connection string is correct")
            print("  2. Verify firewall rules allow your IP")
            print("  3. Ensure database exists")
            print("  4. Run: python scripts/init_database.py")
            return False
        print()
    
    # Summary
    print("=" * 60)
    print("Configuration Summary")
    print("=" * 60)
    
    ready_for_prod = all([
        settings.AZURE_STORAGE_CONNECTION_STRING,
        settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY,
        settings.SECRET_KEY != "your-secret-key-change-in-production",
        settings.SQL_CONNECTION_STRING or settings.DATABASE_URL,
    ])
    
    if ready_for_prod:
        print("✅ Ready for production deployment!")
    else:
        print("⚠️  Ready for local development")
        print()
        print("For production, configure:")
        if not settings.AZURE_STORAGE_CONNECTION_STRING:
            print("  - AZURE_STORAGE_CONNECTION_STRING")
        if not (settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY):
            print("  - AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY")
        if settings.SECRET_KEY == "your-secret-key-change-in-production":
            print("  - SECRET_KEY (use: openssl rand -hex 32)")
        if not (settings.SQL_CONNECTION_STRING or settings.DATABASE_URL):
            print("  - SQL_CONNECTION_STRING or DATABASE_URL")
    
    print()
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. If using Azure SQL: python scripts/init_database.py")
    print("  2. Start backend: uvicorn main:app --reload --port 8000")
    print("  3. Test: curl http://localhost:8000/health")
    print()
    
    return True


if __name__ == "__main__":
    success = asyncio.run(verify_setup())
    sys.exit(0 if success else 1)
