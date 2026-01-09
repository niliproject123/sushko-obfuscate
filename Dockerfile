FROM python:3.11-slim

RUN apt-get update && apt-get install -y poppler-utils && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ /app/api/

# Railway provides PORT env var, default to 8000 for local dev
ENV PORT=8000
CMD uvicorn api.main:app --host 0.0.0.0 --port $PORT
