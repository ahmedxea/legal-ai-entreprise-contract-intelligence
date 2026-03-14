# Lexra — AI Contract Intelligence Platform

Lexra is an enterprise-grade platform that analyzes legal contracts using AI. It extracts key information, identifies risks and missing clauses, and generates contract-ready remediation clauses — all from a single upload.

---

## Key Features

- **Automated text extraction** from PDF, DOCX, and scanned documents (OCR)
- **Entity extraction** — parties, dates, financial terms, obligations
- **Risk detection** — 60+ deterministic rules across 15 clause categories, severity-scored
- **Gap analysis** — identifies missing critical and recommended clauses vs. CUAD baseline
- **AI clause generator** — drafts remediation clauses from CUAD templates, jurisdiction-aware
- **Executive summary** — concise 200-500 word plain-language contract summary
- **Multi-user authentication** with session management and per-user data isolation

---

## Architecture

```
Browser (Next.js static export)
         |
         | REST API
         |
FastAPI Backend (Python 3.11)
    |           |           |
  SQLite     Local FS    Ollama (Phi-3 Mini)
  (dev)      (dev)       LLM inference
    |           |
  Azure SQL  Azure Blob
  (prod)     (prod)
```

The frontend is a statically exported Next.js application deployed to Azure Static Web Apps. The backend is a FastAPI service deployed to Azure App Service. In development, SQLite and local filesystem are used. In production, these are replaced by Azure SQL/PostgreSQL and Azure Blob Storage.

AI analysis runs locally via Ollama with the Phi-3 Mini model. On Azure App Service free tier, `MOCK_MODE=true` is set by default since Ollama cannot run on that tier.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend framework | Next.js 16 (App Router, static export) |
| Frontend language | TypeScript 5 |
| Styling | Tailwind CSS 4, Radix UI, shadcn/ui |
| Backend framework | FastAPI 0.115 (async) |
| Backend language | Python 3.11 |
| Database (dev) | SQLite via sqlite3 |
| Database (prod) | Azure SQL / PostgreSQL via SQLAlchemy 2.0 |
| Storage (dev) | Local filesystem |
| Storage (prod) | Azure Blob Storage |
| AI / LLM | Ollama — Microsoft Phi-3 Mini |
| PDF parsing | pdfplumber |
| DOCX parsing | python-docx |
| OCR | pytesseract + pdf2image |
| Auth | Custom session tokens, HttpOnly cookies |

---

## Repository Structure

```
.
├── app/                        # Next.js App Router pages
│   ├── home/                   # Dashboard + drag-drop upload
│   ├── upload/                 # Dedicated upload page
│   ├── contracts/              # Contract list + detail view
│   ├── risk/                   # Risk and compliance dashboard
│   ├── clauses/                # AI clause generator
│   └── settings/               # Profile, password, system status
├── components/
│   ├── ui/                     # Radix UI primitive components
│   ├── enterprise-layout.tsx   # Authenticated shell
│   ├── enterprise-sidebar.tsx  # Left navigation
│   └── enterprise-header.tsx   # Top bar
├── lib/
│   ├── api-client.ts           # Typed HTTP client
│   ├── auth-context.tsx        # Auth state (React Context)
│   └── config.ts               # Frontend configuration
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── requirements.txt
│   └── app/
│       ├── api/                # Route handlers
│       ├── agents/             # AI agent layer
│       ├── core/               # Config, logging, rate limiting
│       ├── models/             # Pydantic schemas, ORM models
│       └── services/           # Business logic, DB, storage
├── docs/
│   ├── architecture.md         # Pipeline and component details
│   ├── deployment.md           # Azure deployment guide
│   └── api.md                  # API endpoint reference
└── data/
    ├── english/                # Sample English contracts
    └── arabic/                 # Sample Arabic contracts
```

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.com) with `phi3:mini` pulled

### Setup

```bash
# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Frontend
npm install
```

### Run

Open two terminals from the project root.

**Terminal 1 — Backend:**

```bash
source .venv/bin/activate
cd backend
python main.py
```

API available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

**Terminal 2 — Frontend:**

```bash
npm run dev
```

Application available at `http://localhost:3000`

**Demo account:**

```
Email:    demo@lexra.ai
Password: demo123
```

---

## Configuration

### Frontend

Create `.env.local` in the project root:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Backend API base URL |

### Backend

Create `backend/.env` or set these in the deployment environment:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | No | `development` | `development` or `production` |
| `SECRET_KEY` | Yes (prod) | — | Secret for session token signing |
| `MOCK_MODE` | No | `false` | Return stub AI responses (no Ollama needed) |
| `MAX_FILE_SIZE_MB` | No | `50` | Maximum upload size in MB |
| `AZURE_STORAGE_CONNECTION_STRING` | No | — | Azure Blob Storage (production) |
| `DATABASE_URL` | No | SQLite | PostgreSQL/Azure SQL connection string (production) |

---

## Processing Pipeline

1. **Upload** — File validated (type, size), stored, contract record created
2. **Phase 1** — Text extracted from PDF/DOCX/image; paragraphs normalized; document chunked
3. **Phase 2** — Four parallel AI jobs:
   - Entity extraction (parties, dates, financials, obligations)
   - Executive summary generation
   - CUAD clause extraction + deterministic risk scoring
   - Gap detection (missing clause analysis)
4. **Results** — Risks ranked by severity, missing clauses listed with generate-clause links

---

## Testing

```bash
# Backend tests
source .venv/bin/activate
cd backend
python -m pytest tests/ -v

# Health check
curl http://localhost:8000/health
```

---

## Deployment

See [docs/deployment.md](docs/deployment.md) for step-by-step Azure deployment instructions.

| Service | URL |
|---------|-----|
| Frontend | https://zealous-desert-04982c30f.1.azurestaticapps.net |
| Backend | https://lexra-backend-ahmedelabed.azurewebsites.net |
| API Docs | https://lexra-backend-ahmedelabed.azurewebsites.net/docs |

---

## Known Limitations

- SQLite is not suitable for concurrent writes. PostgreSQL or Azure SQL is required for production scale.
- In-process async task queue does not scale across multiple App Service instances. A distributed queue (Redis/Celery) is needed for horizontal scaling.
- Phi-3 Mini via Ollama is CPU-only. AI analysis is disabled on the Azure free tier (`MOCK_MODE=true`).
- Auth tokens are stored in `localStorage`. Acceptable for prototype use; production requires HttpOnly cookies to eliminate XSS exposure.
- Password hashing uses SHA-256 with salt. bcrypt migration is in progress.

---

## License

MIT
