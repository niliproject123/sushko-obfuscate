# Deployment Architecture

## Overview

The PDF Obfuscator uses a **single-container architecture** where both the backend API and frontend UI are served from one Docker container.

```
┌─────────────────────────────────────────────────────────┐
│                    Railway Container                     │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              FastAPI (uvicorn)                   │   │
│  │                                                  │   │
│  │   /api/*  ──────►  API Routes (extract, config) │   │
│  │   /assets/* ────►  Static Assets (JS, CSS)      │   │
│  │   /*  ──────────►  React SPA (index.html)       │   │
│  │   /health ──────►  Health Check                 │   │
│  │   /docs ────────►  Swagger UI                   │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                               │
│                    PORT (8080)                          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │   Railway Network   │
              │   (Public Domain)   │
              └─────────────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │      Internet       │
              │  (your-app.up.      │
              │   railway.app)      │
              └─────────────────────┘
```

## Container Build Process

The Dockerfile performs these steps:

```
1. Base Image: python:3.11-slim
           │
           ▼
2. Install System Dependencies
   - poppler-utils (PDF processing)
   - curl (for Node.js setup)
           │
           ▼
3. Install Node.js 20 LTS
   - Required for frontend build
           │
           ▼
4. Install Python Dependencies
   - pip install -r requirements.txt
           │
           ▼
5. Build Frontend
   - npm install
   - npm run build (vite)
   - Output: /app/ui/dist/
           │
           ▼
6. Copy Files
   - Backend: /app/api/
   - Frontend: /app/static/
           │
           ▼
7. Start Server
   - uvicorn api.main:app
   - Listens on $PORT (default 8080)
```

## Request Flow

### API Requests (`/api/*`)

```
Client Request
     │
     ▼
┌─────────────┐
│   /api/*    │ ──► FastAPI Router ──► Processing ──► JSON Response
└─────────────┘
```

### Frontend Requests (`/*`)

```
Client Request
     │
     ▼
┌─────────────┐
│  /assets/*  │ ──► StaticFiles Mount ──► JS/CSS/Images
└─────────────┘

┌─────────────┐
│     /*      │ ──► serve_spa() ──► index.html (SPA routing)
└─────────────┘
```

## File Structure in Container

```
/app/
├── api/                    # Backend Python code
│   ├── main.py            # FastAPI application
│   ├── routes/            # API endpoints
│   ├── processors/        # PDF processing
│   ├── detectors/         # PII detection
│   ├── obfuscators/       # Text obfuscation
│   └── config/            # Configuration
│
├── static/                 # Built frontend (from ui/dist)
│   ├── index.html         # React SPA entry
│   └── assets/            # JS, CSS bundles
│       ├── index-*.js
│       └── index-*.css
│
└── requirements.txt        # Python dependencies
```

## Key Components

### FastAPI Application (`api/main.py`)

- **Startup Event**: Mounts static files if they exist
- **Health Endpoint**: `/health` for Railway health checks
- **API Routers**: `/api/extract`, `/api/config`
- **SPA Handler**: Serves `index.html` for all non-API routes

### Static File Serving

```python
# On startup, mount assets if they exist
if (STATIC_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(...))

# Catch-all route for SPA
@app.get("/{full_path:path}")
async def serve_spa(...):
    if INDEX_HTML.exists():
        return FileResponse(INDEX_HTML)
```

## Why Single Container?

| Aspect | Single Container | Two Containers |
|--------|------------------|----------------|
| Complexity | Simple | More complex |
| Cost | Lower (one service) | Higher (two services) |
| Scaling | Scale together | Independent scaling |
| Deployment | One build | Two builds |
| Best for | Small-medium apps | Large apps, microservices |

For this application, single container is ideal because:
- Simple deployment and management
- Lower Railway costs
- Frontend and backend are tightly coupled
- No need for independent scaling

## Production Considerations

### Security
- CORS is configured for all origins (`*`) - restrict in production if needed
- No authentication by default - add if handling sensitive documents

### Performance
- Static files served directly by FastAPI (consider CDN for high traffic)
- Temporary files cleaned up after 1 hour

### Monitoring
- Use Railway's built-in metrics
- `/health` endpoint for uptime monitoring
- Startup logs indicate static file mounting status

## Alternative: Two-Container Architecture

For larger deployments, you could split into:

1. **Backend Service**: FastAPI only, handles `/api/*`
2. **Frontend Service**: Nginx serving static files, proxies API calls

This repo includes an alternative branch (`claude/plan-railway-deployment-tcRTO`) with this architecture if needed.
