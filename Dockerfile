FROM python:3.11-slim

# Install system dependencies including OCR
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-heb \
    tesseract-ocr-eng \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20 (LTS) - Debian's nodejs is too old
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Build frontend
COPY ui/ /app/ui/
WORKDIR /app/ui
RUN npm install && npm run build

# Copy backend
WORKDIR /app
COPY api/ /app/api/

# Copy built frontend to static folder for serving
RUN mkdir -p /app/static && cp -r /app/ui/dist/* /app/static/

# Railway sets PORT env var automatically
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
