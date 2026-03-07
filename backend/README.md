# Lexra Backend - Engine API

FastAPI backend for Lexra enterprise contract intelligence platform.

## 🚀 Quick Links

- **[Azure SQL Database Setup Guide](AZURE_SQL_GUIDE.md)** - Complete guide for production database setup
- **[Implementation Summary](../IMPLEMENTATION_SUMMARY.md)** - Feature overview and deployment instructions
- **[API Documentation](#api-endpoints)** - REST API reference below

## 🗄️ Database Support

The backend supports **two database backends**:

- **SQLite** (default) - Zero configuration, perfect for local development
- **Azure SQL Database** - Production-ready with full async support via SQLAlchemy

The system automatically selects the appropriate backend based on environment variables:
- `SQL_CONNECTION_STRING` → Azure SQL Server
- `DATABASE_URL` → PostgreSQL or other databases
- Neither set → SQLite (automatic fallback)

## Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── app/
│   ├── core/              # Core configuration
│   │   ├── config.py      # Settings and configuration
│   │   └── logging_config.py
│   ├── models/            # Pydantic schemas
│   │   └── schemas.py
│   ├── api/               # API endpoints
│   │   ├── contracts.py   # Contract upload & management
│   │   ├── analysis.py    # Analysis & dashboard
│   │   └── clauses.py     # Clause generation
│   ├── services/          # Business logic services
│   │   ├── storage_service.py      # Azure Blob Storage
│   │   ├── database_service.py     # Azure Cosmos DB
│   │   ├── openai_service.py       # Azure OpenAI
│   │   └── clause_service.py       # Clause templates
│   └── agents/            # AI Agents
│       ├── orchestrator.py         # Coordinates agents
│       ├── document_parser.py      # PDF/DOCX parsing
│       ├── extraction_agent.py     # Data extraction
│       ├── risk_agent.py           # Risk analysis
│       ├── legal_advisory_agent.py # Legal opinions
│       ├── compliance_agent.py     # Compliance checks
│       └── clause_agent.py         # Clause generation
```

## Setup Instructions

### 1. Create Python Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your Azure credentials
```

Required environment variables:
- `AZURE_OPENAI_ENDPOINT` - Your Azure OpenAI endpoint
- `AZURE_OPENAI_API_KEY` - Your Azure OpenAI API key
- `AZURE_STORAGE_CONNECTION_STRING` - Azure Blob Storage connection string
- `COSMOS_ENDPOINT` - Azure Cosmos DB endpoint
- `COSMOS_KEY` - Azure Cosmos DB key

### 4. Run the Server

```bash
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python main.py
```

The API will be available at: `http://localhost:8000`

API documentation (Swagger): `http://localhost:8000/docs`

## API Endpoints

### Contracts
- `POST /api/contracts/upload` - Upload a contract
- `POST /api/contracts/{id}/analyze` - Trigger analysis
- `GET /api/contracts/{id}` - Get contract details
- `GET /api/contracts/` - List all contracts
- `GET /api/contracts/{id}/analysis` - Retrieve structured analysis results
- `GET /api/contracts/{id}/text` - Retrieve extracted contract text
- `GET /api/contracts/{id}/file` - Retrieve the original uploaded file
- `DELETE /api/contracts/{id}` - Delete a contract

### Analysis
- `GET /api/analysis/risks` - Get all risks
- `GET /api/analysis/dashboard/{user_id}` - Get dashboard stats
- `GET /api/analysis/audit-log` - Get audit logs

### Clauses
- `GET /api/clauses/templates` - Get clause templates
- `POST /api/clauses/generate` - Generate contract clauses

## Agent Pipeline

The orchestrator coordinates multiple specialized agents:

1. **Document Parser Agent** - Extracts text from PDF/DOCX
2. **Extraction Agent** - Extracts structured data (parties, dates, financials)
3. **Risk Analysis Agent** - Identifies risks and unusual clauses
4. **Legal Advisory Agent** - Provides legal opinions and regulatory compliance
5. **Compliance Agent** - Checks for missing standard clauses
6. **Clause Generation Agent** - Generates contract clauses

## Development Mode (Without Azure)

The backend can run in development mode without Azure services:
- Storage, Database, and OpenAI services have fallback mock implementations
- Check logs for "mock" warnings to identify services running in mock mode
- Configure Azure services for production use

## Testing

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs
```

## Deployment

See main project README for Azure deployment instructions.

## Architecture

### Multi-Agent System
Each agent is independent and specialized:
- Clear separation of concerns
- Parallel execution where possible (Risk + Legal + Compliance)
- Coordinator pattern for orchestration

### Services Layer
- **Storage Service**: Handles Azure Blob Storage operations
- **Database Service**: Manages Cosmos DB CRUD operations
- **OpenAI Service**: Wraps Azure OpenAI API calls
- **Clause Service**: Manages clause template library

### Enterprise Features
- Audit logging for all operations
- User-based access control
- Error handling and logging
- API versioning ready
- CORS configuration for frontend

## Environment Variables Reference

See `.env.example` for all available configuration options.

## Troubleshooting

**Import errors**: Ensure you're in the virtual environment and all dependencies are installed

**Azure connection errors**: Check your credentials in `.env` and ensure services are provisioned

**OpenAI errors**: Verify your deployment name matches the model you deployed

**Port already in use**: Change the port with `--port 8001`
