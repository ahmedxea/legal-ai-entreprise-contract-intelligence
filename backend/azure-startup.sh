#!/bin/bash
# filepath: backend/azure-startup.sh

echo "Starting Lexra Backend in DEMO mode..."

export ENVIRONMENT=production
export MOCK_MODE=true

cd /home/site/wwwroot

# Install dependencies (no Oryx build)
pip install --no-cache-dir -r requirements.txt 2>&1 | tail -5

# Azure App Service expects the app on $PORT (default 8000)
PORT=${PORT:-8000}
echo "Starting on port $PORT"
gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT --timeout 120