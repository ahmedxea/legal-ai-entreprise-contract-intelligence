# Azure SQL Database Integration Guide

## Overview

The Lexra backend now supports **two database backends**:

1. **SQLite** - For local development (default, no configuration needed)
2. **Azure SQL Database / PostgreSQL** - For production deployment

The system automatically selects the appropriate database based on environment variables.

---

## Quick Start (Local Development)

No configuration needed! The app uses SQLite out of the box:

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

SQLite database is created automatically at: `backend/data/contracts.db`

---

## Azure SQL Database Setup

### 1. Create Azure SQL Database

Using Azure CLI:

```bash
# Set variables
RESOURCE_GROUP="msft-aidevdays-2026"
SQL_SERVER="lexra-sql-server"
DATABASE_NAME="lexra-db"
ADMIN_USER="lexraadmin"
ADMIN_PASSWORD="YourSecurePassword123!"
LOCATION="eastus"

# Create SQL Server
az sql server create \
  --name $SQL_SERVER \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --admin-user $ADMIN_USER \
  --admin-password $ADMIN_PASSWORD

# Create database
az sql db create \
  --resource-group $RESOURCE_GROUP \
  --server $SQL_SERVER \
  --name $DATABASE_NAME \
  --service-objective S0 \
  --backup-storage-redundancy Local

# Allow Azure services to access
az sql server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --server $SQL_SERVER \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# Allow your local IP (for testing)
MY_IP=$(curl -s ifconfig.me)
az sql server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --server $SQL_SERVER \
  --name AllowLocalDev \
  --start-ip-address $MY_IP \
  --end-ip-address $MY_IP
```

### 2. Get Connection String

```bash
# Get connection string
az sql db show-connection-string \
  --client ado.net \
  --server $SQL_SERVER \
  --name $DATABASE_NAME
```

Example output:
```
Server=tcp:lexra-sql-server.database.windows.net,1433;Database=lexra-db;User ID=<username>;Password=<password>;Encrypt=true;Connection Timeout=30;
```

### 3. Configure Environment Variables

Add to your `.env` file:

**Option A: Using SQL_CONNECTION_STRING (Azure SQL)**

```bash
# Azure SQL Database
SQL_CONNECTION_STRING="mssql+pyodbc://lexraadmin:YourSecurePassword123!@lexra-sql-server.database.windows.net/lexra-db?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes&Encrypt=yes"
```

**Option B: Using DATABASE_URL (PostgreSQL/Generic)**

```bash
# PostgreSQL (Azure Database for PostgreSQL)
DATABASE_URL="postgresql+asyncpg://username:password@server.postgres.database.azure.com:5432/lexra-db"

# Or SQLite for local
DATABASE_URL="sqlite+aiosqlite:///./data/contracts.db"
```

### 4. Install Database Drivers

The `requirements.txt` already includes:

```bash
pip install -r requirements.txt
```

- `pyodbc` - For Azure SQL Server
- `asyncpg` - For PostgreSQL
- `aiosqlite` - For SQLite

**For Azure SQL on Linux/macOS**, you may need ODBC Driver 18:

```bash
# macOS
brew install unixodbc
brew install microsoft/mssql-release/msodbcsql18

# Ubuntu/Debian
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc
```

### 5. Initialize Database Tables

Run the initialization script:

```bash
cd backend
python scripts/init_database.py
```

This creates all required tables:
- users
- sessions
- contracts
- document_text, document_chunks
- contract_entities, contract_summaries, contract_risks, contract_gaps
- audit_logs

A demo user is also created:
- Email: `demo@lexra.ai`
- Password: `demo123`

---

## Database Architecture

### Tables

**users**
- id, email, password_hash, full_name, organization, role, last_login, is_active, created_date

**sessions**
- id, user_id, token, expires_at, created_at

**contracts**
- id, user_id, filename, blob_url, upload_date, status, language, industry, extracted_data, analysis, file_size, file_type

**document_text** (Phase 1: Extraction)
- document_id, raw_text, paragraphs, page_count, file_type, created_at

**document_chunks** (Phase 1: Chunking)
- chunk_id, document_id, chunk_index, chunk_text

**contract_entities** (Phase 2: Entity Extraction)
- document_id, extraction_json, created_at

**contract_summaries** (Phase 2: Summary)
- document_id, summary_text, created_at

**contract_risks** (Phase 2: Risk Detection)
- risk_id, document_id, risk_type, severity, description, source_text

**contract_gaps** (Phase 2: Gap Analysis)
- document_id, missing_clauses_json, created_at

**audit_logs**
- id, user_id, action, contract_id, timestamp, metadata

### Indexes

- `idx_contracts_user_id` - Fast contract lookups by user
- `idx_contracts_status` - Filter by processing status
- `idx_contracts_user_status` - Combined index for dashboard queries
- `idx_sessions_token` - Fast session validation
- `idx_document_chunks_document_id` - Efficient chunk retrieval
- `idx_contract_risks_document_id` - Risk aggregation

---

## Deployment to Azure App Service

### 1. Configure App Service Environment Variables

```bash
APP_NAME="lexra-backend-ahmedelabed"
RESOURCE_GROUP="msft-aidevdays-2026"

# Set SQL connection string
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings SQL_CONNECTION_STRING="mssql+pyodbc://..."

# Set other required variables
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    AZURE_OPENAI_ENDPOINT="https://..." \
    AZURE_OPENAI_API_KEY="..." \
    AZURE_STORAGE_CONNECTION_STRING="..." \
    JWT_SECRET="$(openssl rand -hex 32)" \
    ENVIRONMENT="production" \
    COOKIE_SECURE="true"
```

### 2. Initialize Database from App Service

SSH into the App Service:

```bash
az webapp ssh --name $APP_NAME --resource-group $RESOURCE_GROUP
```

Then run:

```bash
cd /home/site/wwwroot/backend
python scripts/init_database.py
```

Alternatively, run it locally (if firewall allows):

```bash
# Set production connection string locally
export SQL_CONNECTION_STRING="..."
python scripts/init_database.py
```

### 3. Deploy Backend

```bash
cd backend

# Create deployment package
rm -rf backend-deploy.zip backend-deploy-temp
mkdir backend-deploy-temp
rsync -a . backend-deploy-temp/ \
  --exclude __pycache__ \
  --exclude .pytest_cache \
  --exclude "*.pyc" \
  --exclude tests \
  --exclude data/uploads \
  --exclude .venv

# Copy production requirements
cp requirements-azure.txt backend-deploy-temp/requirements.txt

# Create zip
cd backend-deploy-temp && zip -rq ../backend-deploy.zip . && cd ..

# Deploy
az webapp deploy \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --src-path backend-deploy.zip \
  --type zip
```

---

## Testing

### 1. Test Authentication

```bash
# Sign up
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User",
    "organization": "Test Org"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# Get current user
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <token>"
```

### 2. Test Upload with Authentication

```bash
TOKEN="<your-token>"

curl -X POST http://localhost:8000/api/contracts/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample-contract.pdf" \
  -F "language=en"
```

### 3. Test Multi-Tenancy

```bash
# User A uploads a contract
curl -X POST http://localhost:8000/api/contracts/upload \
  -H "Authorization: Bearer $TOKEN_USER_A" \
  -F "file=@contract.pdf"

# User B cannot access User A's contract
curl http://localhost:8000/api/contracts/<contract_id> \
  -H "Authorization: Bearer $TOKEN_USER_B"
# Should return 404
```

---

## Migration from SQLite to Azure SQL

If you have existing data in SQLite that you want to migrate:

### 1. Export SQLite Data

```python
import sqlite3
import json

conn = sqlite3.connect('data/contracts.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Export users
cursor.execute("SELECT * FROM users")
users = [dict(row) for row in cursor.fetchall()]
with open('users.json', 'w') as f:
    json.dump(users, f)

# Export contracts
cursor.execute("SELECT * FROM contracts")
contracts = [dict(row) for row in cursor.fetchall()]
with open('contracts.json', 'w') as f:
    json.dump(contracts, f)

# ... repeat for other tables
```

### 2. Import to Azure SQL

```python
import asyncio
import json
from app.services.azure_sql_service import azure_sql_service

async def import_data():
    # Import users
    with open('users.json', 'r') as f:
        users = json.load(f)
    
    for user in users:
        await azure_sql_service.create_user(
            email=user['email'],
            password_hash=user['password_hash'],
            full_name=user['full_name'],
            organization=user.get('organization', '')
        )
    
    # Import contracts
    with open('contracts.json', 'r') as f:
        contracts = json.load(f)
    
    for contract in contracts:
        await azure_sql_service.create_contract(
            user_id=contract['user_id'],
            filename=contract['filename'],
            blob_url=contract['blob_url'],
            language=contract['language'],
            industry=contract.get('industry'),
            file_size=contract.get('file_size'),
            file_type=contract.get('file_type')
        )

asyncio.run(import_data())
```

---

## Troubleshooting

### Connection Errors

**"Login failed for user"**
- Check username and password in connection string
- Verify firewall rules allow your IP

**"Cannot open database"**
- Ensure database exists: `az sql db show --name lexra-db ...`
- Check server is running: `az sql server show --name lexra-sql-server ...`

**"ODBC Driver not found"**
- Install ODBC Driver 18 for SQL Server (see setup steps above)

### Performance Issues

**Slow queries**
- Check indexes are created: Run `scripts/init_database.py`
- Monitor with Azure Portal → Query Performance Insight

**Connection timeouts**
- Increase pool size in connection string: `pool_size=10&max_overflow=20`
- Use connection pooling in App Service

### Debugging

Enable SQL query logging:

```python
# In azure_sql_service.py, set echo=True
self.engine = create_async_engine(
    db_url,
    echo=True,  # <-- Log all SQL queries
    future=True,
)
```

---

## Cost Optimization

**Azure SQL Database Pricing:**

- **Basic tier**: ~$5/month (2GB)
- **S0 Standard**: ~$15/month (250GB)
- **S1 Standard**: ~$30/month (250GB, better performance)

**Recommendation for development:**
- Use SQLite locally (free)
- Use Basic tier for staging (~$5/month)
- Use S0/S1 for production (~$15-30/month)

**Save money:**
```bash
# Auto-pause after inactivity (Serverless tier only)
az sql db update \
  --resource-group $RESOURCE_GROUP \
  --server $SQL_SERVER \
  --name $DATABASE_NAME \
  --compute-model Serverless \
  --auto-pause-delay 60
```

---

## Security Best Practices

1. **Never commit connection strings to Git**
   - Use environment variables
   - Add `.env` to `.gitignore`

2. **Use Managed Identity in production**
   ```bash
   # Enable managed identity on App Service
   az webapp identity assign \
     --name $APP_NAME \
     --resource-group $RESOURCE_GROUP
   
   # Grant access to SQL
   # (then use Azure AD auth instead of SQL auth)
   ```

3. **Rotate passwords regularly**
   ```bash
   az sql server update \
     --name $SQL_SERVER \
     --resource-group $RESOURCE_GROUP \
     --admin-password "NewPassword123!"
   ```

4. **Encrypt sensitive data at rest**
   - Azure SQL has Transparent Data Encryption (TDE) enabled by default

5. **Use SSL/TLS**
   - Always include `Encrypt=yes` in connection string

---

## Support

For issues or questions:

1. Check logs: `az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP`
2. Review Azure SQL metrics in Azure Portal
3. Test connection locally first before deploying

---

**✅ You're now ready to use Azure SQL Database with Lexra!**
