#!/bin/bash

# 1. Asegurar que el entorno virtual está activo (opcional si ya lo tienes)
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Entorno virtual activado."
else
    echo "❌ Error: No se encontró la carpeta venv."
    exit 1
fi

# 2. Configurar el Path para que Python encuentre la carpeta /app
export PYTHONPATH=$PYTHONPATH:.

# 3. Informar al usuario
echo "--------------------------------------------"
echo "🚀 Iniciando StockWise AI Dashboard..."
echo "📍 URL: http://localhost:8000"
echo "--------------------------------------------"

# 4. Lanzar Uvicorn con recarga automática para Python, HTML, CSS y JSON
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --reload-include "*.html" \
    --reload-include "*.css" \
    --reload-include "*.json"