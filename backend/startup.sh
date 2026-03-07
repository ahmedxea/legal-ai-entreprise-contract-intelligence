#!/bin/bash
# filepath: backend/startup.sh

echo " Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

echo " Starting Ollama service..."
ollama serve &

echo "⏳ Waiting for Ollama to be ready..."
sleep 15

echo " Pulling Phi-3 model (this takes 3-5 minutes)..."
ollama pull phi3

echo " Ollama ready with Phi-3!"

echo " Starting Lexra Backend API..."
cd /home/site/wwwroot
gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000 --timeout 300