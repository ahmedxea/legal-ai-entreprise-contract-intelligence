# Deployment

## Prerequisites

- Azure CLI installed and authenticated (`az login`)
- Resource group: `msft-aidevdays-2026`
- Backend App Service: `lexra-backend-ahmedelabed`
- Frontend Static Web App: `lexra-frontend`

## Backend (Azure App Service)

```bash
cd backend
zip -r ../deploy-backend.zip . \
  -x "*.pyc" -x "__pycache__/*" -x ".venv/*" -x "data/*" -x "logs/*"
cd ..

az webapp deploy \
  --resource-group msft-aidevdays-2026 \
  --name lexra-backend-ahmedelabed \
  --src-path deploy-backend.zip \
  --type zip

rm deploy-backend.zip
```

Startup command is defined in `backend/azure-startup.sh`. It installs dependencies and starts Gunicorn with the Uvicorn worker.

## Frontend (Azure Static Web Apps)

The frontend deploys automatically via GitHub Actions on every push to `main`. The workflow is defined in `.github/workflows/ci.yml`.

To deploy manually:

```bash
npm run build

DEPLOY_TOKEN=$(az staticwebapp secrets list \
  --name lexra-frontend \
  --resource-group msft-aidevdays-2026 \
  --query "properties.apiKey" -o tsv)

npx @azure/static-web-apps-cli deploy ./out --deployment-token "$DEPLOY_TOKEN"
```

## Deployed URLs

| Service  | URL |
|----------|-----|
| Frontend | https://zealous-desert-04982c30f.1.azurestaticapps.net |
| Backend  | https://lexra-backend-ahmedelabed.azurewebsites.net |
| API Docs | https://lexra-backend-ahmedelabed.azurewebsites.net/docs |

## Required Environment Variables (Backend)

Set these in Azure App Service > Configuration > Application Settings:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Session signing key (generate with `openssl rand -hex 32`) |
| `ENVIRONMENT` | Set to `production` |
| `AZURE_STORAGE_ACCOUNT` | Blob storage account name |
| `AZURE_STORAGE_KEY` | Blob storage account key |
| `AZURE_STORAGE_CONTAINER` | Blob container name |
| `DATABASE_URL` | Azure SQL connection string (omit for SQLite) |
| `MOCK_MODE` | Set to `true` if Ollama is not available |

## Troubleshooting

**Backend does not start after deployment**
Delete `__pycache__` directories on the server. Oryx can cache stale bytecode that blocks imports after a code update.

```bash
# SSH into the App Service:
find /home/site/wwwroot -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; true
```

**Frontend shows "Backend Offline"**
The Azure App Service F1 free tier idles after 20 minutes. Issue a warm-up request before a demo:

```bash
curl https://lexra-backend-ahmedelabed.azurewebsites.net/health
```

**401 Unauthorized on API calls**
Session cookies expire after 24 hours. Sign out and sign back in.
