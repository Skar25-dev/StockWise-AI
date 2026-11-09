FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias primero: aprovecha la caché de capas de Docker
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN mkdir -p data app/ai/model_store

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
