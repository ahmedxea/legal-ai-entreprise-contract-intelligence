# Architecture

## Overview

Lexra is a monorepo consisting of a statically exported Next.js frontend and a FastAPI backend. In development, both run locally. In production, the frontend deploys to Azure Static Web Apps and the backend deploys to Azure App Service.

```
Browser
  |
  | HTTPS
  v
Next.js Frontend              (Azure Static Web Apps)
  |
  | REST API (JSON)
  v
FastAPI Backend               (Azure App Service)
  |
  +-- SQLite / Azure SQL      (contract metadata, users, sessions)
  +-- Local FS / Azure Blob   (uploaded files)
  +-- Ollama / Phi-3 Mini     (AI analysis, clause generation)
```

## Frontend

- Framework: Next.js 16, App Router, static export (`output: 'export'`)
- Language: TypeScript (strict)
- Styling: Tailwind CSS 4, Radix UI primitives (shadcn/ui pattern)
- Auth state: React Context with HttpOnly cookie sessions
- HTTP client: Native Fetch wrapped in `lib/api-client.ts`

## Backend

- Framework: FastAPI 0.115 (async)
- Server: Uvicorn + Gunicorn
- Auth: Session tokens in HttpOnly cookies, bcrypt password hashing
- AI: Ollama local server running Phi-3 Mini (3.8B, Q4)
- OCR: pytesseract + pdf2image as fallback for scanned PDFs

## Storage Backends (Factory Pattern)

| Environment | Database | File Storage |
|-------------|----------|--------------|
| Development | SQLite   | Local filesystem |
| Production  | Azure SQL / PostgreSQL | Azure Blob Storage |

The factory modules (`database_factory.py`, `storage_factory.py`) select the backend at startup based on environment variables.

## AI Processing Pipeline

### Phase 1 — Text Extraction (automatic after upload)

1. Upload saved to storage
2. Contract record created in DB (status: `uploaded`)
3. Background task: parse PDF/DOCX/image via `document_parser.py`
4. OCR fallback triggered if PDF yields fewer than 100 characters per page
5. Text chunked (1000 chars, 200-char overlap) and stored
6. Status updated to `extracted`

### Phase 2 — Analysis (triggered by user)

Four async jobs run in parallel:

| Job | Agent | Method |
|-----|-------|--------|
| Entity extraction | `ExtractionAgent` | LLM structured extraction |
| Executive summary | `AnalysisService` | LLM freeform generation |
| Risk detection | `CUADClauseExtractionAgent` + `RiskEvaluationEngine` | LLM clause extraction + deterministic rules |
| Gap detection | `GapDetectionAgent` | Deterministic (no LLM) |

Large documents (over 12,000 characters) use map-reduce: each chunk is processed independently, then results are merged.

## Task Queue

Processing runs in an in-process asyncio queue (`task_queue.py`) with two workers and exponential-backoff retry (2 attempts, 3-second base). The frontend polls `GET /api/contracts/{id}` every 3 seconds to check status.

Note: the in-process queue does not share state across multiple App Service instances. For scaled deployments, replace with Redis + Celery.
