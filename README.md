# Lexra

Enterprise AI contract intelligence platform. Extracts key information from legal contracts, identifies risks and missing clauses, and provides an AI-powered query interface.

---

## Architecture

```
                        +-------------------------+
     Browser            |    Next.js Frontend     |
     (port 3000)  <---> |  (Azure Static Web App) |
                        +------------|------------+
                                     |
                                 REST API
                                     |
                        +------------|------------+
                        |    FastAPI Backend      |
                        |  (Azure App Service)    |
                        +---+--------+--------+---+
                            |        |        |
                       SQLite DB  File     AI Layer
                       (contracts  Storage   (Phi-3 /
                        .db)      (local /   Ollama or
                                  Azure      Azure AI)
                                  Blob)
```

The frontend is a statically exported Next.js application. The backend is a FastAPI service that handles authentication, contract storage, and AI analysis. In development, SQLite and local file storage are used. In production, these are replaced by Azure SQL/PostgreSQL and Azure Blob Storage.

---

## Directory Structure

```
.
+-- app/                        # Next.js pages (App Router)
|   +-- api/                    # Next.js route handlers
|   +-- clauses/                # Clause library page
|   +-- contracts/              # Contract list page
|   +-- dashboard/              # Home dashboard page
|   +-- login/                  # Authentication page
|   +-- risk/                   # Risk analysis page
|   +-- upload/                 # Contract upload page
|   +-- layout.tsx              # Root layout
|   +-- client-layout.tsx       # Client-side providers (auth, theme)
|   +-- page.tsx                # Landing page
+-- components/
|   +-- enterprise-header.tsx   # Top navigation bar
|   +-- enterprise-layout.tsx   # Authenticated shell (sidebar + header + auth guard)
|   +-- enterprise-sidebar.tsx  # Left navigation sidebar
|   +-- ui/                     # shadcn/ui component library
+-- hooks/
|   +-- use-mobile.ts           # Viewport hook
|   +-- use-toast.ts            # Toast notification hook
+-- lib/
|   +-- api-client.ts           # Typed HTTP client for the backend API
|   +-- auth-context.tsx        # Authentication state and session management
|   +-- config.ts               # Frontend runtime configuration (single source)
|   +-- utils.ts                # Utility functions
+-- backend/
|   +-- main.py                 # FastAPI application entry point
|   +-- app/
|   |   +-- api/                # Route handlers (auth, contracts, analysis, clauses)
|   |   +-- agents/             # AI agent orchestration
|   |   +-- core/               # Config, logging
|   |   +-- models/             # Pydantic schemas
|   |   +-- services/           # Database, storage, auth services
|   +-- tests/                  # Backend tests
|   +-- requirements.txt
+-- data/
|   +-- arabic/                 # Sample Arabic contract documents
|   +-- english/                # Sample English contract documents
```

---

## Installation

### Prerequisites

- Python 3.11 or later
- Node.js 18 or later
- npm, pnpm, or yarn

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### Frontend

```bash
npm install
```

---

## Configuration

### Frontend environment variables

Create a `.env.local` file in the project root.

| Variable              | Required | Default                 | Description               |
|-----------------------|----------|-------------------------|---------------------------|
| NEXT_PUBLIC_API_URL   | No       | http://localhost:8000   | Backend API base URL      |

### Backend environment variables

Create a `.env` file in `backend/` or set these in the deployment environment.

| Variable                  | Required   | Default       | Description                                               |
|---------------------------|------------|---------------|-----------------------------------------------------------|
| ENVIRONMENT               | No         | development   | Runtime environment: development or production            |
| SECRET_KEY                | Yes (prod) | --            | Secret used for token signing                             |
| MAX_FILE_SIZE_MB           | No         | 10            | Maximum allowed upload size in MB                         |
| SUPPORTED_FILE_TYPES      | No         | .pdf,.docx    | Comma-separated list of accepted file extensions          |
| MOCK_MODE                 | No         | false         | Skip AI inference and return stub responses               |
| AZURE_STORAGE_ACCOUNT     | No         | --            | Azure Blob Storage account name (production)              |
| AZURE_STORAGE_KEY         | No         | --            | Azure Blob Storage account key (production)               |
| AZURE_STORAGE_CONTAINER   | No         | --            | Azure Blob Storage container name (production)            |
| DATABASE_URL              | No         | SQLite local  | Override for production database connection string        |

---

## Local Development

Open two terminal sessions from the project root.

**Terminal 1 — Backend:**

```bash
source .venv/bin/activate
cd backend
python main.py
```

The API is available at http://localhost:8000.
Interactive API documentation is at http://localhost:8000/docs.

**Terminal 2 — Frontend:**

```bash
npm run dev
```

The application is available at http://localhost:3000.

**Demo account:**

```
Email:    demo@lexra.ai
Password: demo123
```

---

## Testing

### Backend tests

```bash
source .venv/bin/activate
cd backend
python -m pytest tests/ -v
```

### Verify API health

```bash
curl http://localhost:8000/health
```

### Manual upload test

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@lexra.ai","password":"demo123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

curl -X POST "http://localhost:8000/api/contracts/upload?language=en" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/contract.pdf"
```

---

## Deployment

### Backend (Azure App Service)

```bash
cd backend
zip -r ../deploy-backend.zip . \
  -x "*.pyc" -x "__pycache__/*" -x ".venv/*" -x "data/*" -x "logs/*"
cd ..

az webapp deployment source config-zip \
  --resource-group msft-aidevdays-2026 \
  --name lexra-backend-ahmedelabed \
  --src deploy-backend.zip
```

After deployment, clear stale bytecode to prevent import errors:

```bash
# SSH into the App Service and run:
find /home/site/wwwroot -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; true
```

### Frontend (Azure Static Web Apps)

```bash
npm run build

DEPLOY_TOKEN=$(az staticwebapp secrets list \
  --name lexra-frontend \
  --resource-group msft-aidevdays-2026 \
  --query "properties.apiKey" -o tsv)

npx @azure/static-web-apps-cli deploy ./out --deployment-token "$DEPLOY_TOKEN"
```

### Deployed URLs

| Service  | URL                                                         |
|----------|-------------------------------------------------------------|
| Frontend | https://zealous-desert-04982c30f.1.azurestaticapps.net     |
| Backend  | https://lexra-backend-ahmedelabed.azurewebsites.net         |
| API Docs | https://lexra-backend-ahmedelabed.azurewebsites.net/docs    |

---

## Troubleshooting

**Backend does not start after deployment**
Delete `__pycache__` directories on the server. Oryx can cache stale bytecode that prevents the application from importing correctly after a code update.

**Frontend shows "Backend Offline"**
The Azure App Service F1 free tier idles after 20 minutes of inactivity. The first request after idle takes 30 to 60 seconds. Issue a health check request before a demo:

```bash
curl https://lexra-backend-ahmedelabed.azurewebsites.net/health
```

**Upload fails with 400 Unsupported file type**
Only `.pdf` and `.docx` files are accepted. Verify the file extension is one of these.

**401 Unauthorized on API calls**
Session tokens expire after 24 hours. Sign out and sign back in to obtain a fresh token.

---

## Known Limitations

- SQLite is not suitable for concurrent writes at scale. A production deployment requires PostgreSQL or Azure SQL.
- Local file storage in `backend/data/uploads/` is not replicated across Azure App Service instances. Azure Blob Storage must be configured for multi-instance or scaled deployments.
- AI analysis via Phi-3 and Ollama is CPU-only. Analysis is disabled on the Azure free tier by default (`MOCK_MODE=true`).
- The `/analyze` endpoint is synchronous. Large documents may cause request timeouts. There is no background job queue.
- No rate limiting is implemented on the API.
- Session tokens are stored in `localStorage`. Acceptable for a prototype; production use requires HttpOnly cookies to mitigate XSS exposure.

---

## Future Improvements

- Replace synchronous analysis with an async job queue so uploads return immediately and results are delivered via polling or WebSocket.
- Migrate to a production relational database (PostgreSQL or Azure SQL).
- Add OpenTelemetry tracing with correlation IDs spanning frontend requests and backend operations.
- Implement per-user rate limiting and row-level access controls so users can only read their own contracts.
- Add a CI pipeline (type-check, lint, backend tests, build verification) on every pull request.
- Introduce contract versioning to track amendments and re-analysis of the same document.
- Establish a regression test suite for AI analysis using fixed evaluation fixtures and expected output tolerances.
