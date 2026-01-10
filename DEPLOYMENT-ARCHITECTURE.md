# Deployment Architecture

This document describes the deployment architecture for the PDF Anonymizer application on Railway.

## Architecture Overview

The application uses a **two-service microservice architecture** where the frontend and backend are deployed as separate, independent services.

```
┌──────────────────────────────────────────────────────────────┐
│                        Internet                               │
└────────────────────┬─────────────────────┬───────────────────┘
                     │                     │
                     │                     │
          ┌──────────▼──────────┐ ┌────────▼──────────┐
          │   Custom Domain     │ │  Railway CDN      │
          │  (yourdomain.com)   │ │  (*.railway.app)  │
          └──────────┬──────────┘ └────────┬──────────┘
                     │                     │
                     │                     │
          ┌──────────▼─────────────────────▼──────────┐
          │         Railway Platform                  │
          │  ┌────────────────────────────────────┐   │
          │  │  Frontend Service                  │   │
          │  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │   │
          │  │  Container: Node 20 + nginx        │   │
          │  │  Port: 80                          │   │
          │  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │   │
          │  │  Build Stage:                      │   │
          │  │    - npm install                   │   │
          │  │    - npm run build (Vite)          │   │
          │  │    - Inject VITE_API_URL           │   │
          │  │                                    │   │
          │  │  Serve Stage:                      │   │
          │  │    - nginx serves /dist            │   │
          │  │    - SPA routing                   │   │
          │  │    - Gzip compression              │   │
          │  │    - Static asset caching          │   │
          │  └───────────┬────────────────────────┘   │
          │              │ HTTP/HTTPS                 │
          │              │ (Cross-Origin)             │
          │              ▼                            │
          │  ┌────────────────────────────────────┐   │
          │  │  Backend Service                   │   │
          │  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │   │
          │  │  Container: Python 3.11            │   │
          │  │  Port: 8000                        │   │
          │  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │   │
          │  │  - FastAPI (uvicorn)               │   │
          │  │  - CORS middleware                 │   │
          │  │  - PDF processing (PyMuPDF)        │   │
          │  │  - PII detection & obfuscation     │   │
          │  │  - Temporary file storage          │   │
          │  │                                    │   │
          │  │  Endpoints:                        │   │
          │  │    GET  /health                    │   │
          │  │    GET  /api/config                │   │
          │  │    POST /api/config                │   │
          │  │    POST /api/extract               │   │
          │  │    GET  /api/download/{file_id}    │   │
          │  └────────────────────────────────────┘   │
          └────────────────────────────────────────────┘
```

## Service Breakdown

### Frontend Service (`pdf-anonymizer-ui`)

**Purpose:** Serve the React-based user interface

**Technology Stack:**
- React 18
- TypeScript
- Vite (build tool)
- nginx (web server)

**Dockerfile Strategy:** Multi-stage build
1. **Stage 1 (Builder):**
   - Base: `node:20-alpine`
   - Install dependencies
   - Build production bundle with Vite
   - Environment variable `VITE_API_URL` injected at build time

2. **Stage 2 (Server):**
   - Base: `nginx:alpine`
   - Copy built files from Stage 1
   - Custom nginx configuration
   - Lightweight runtime (no Node.js)

**Key Files:**
- `ui/Dockerfile` - Multi-stage container definition
- `ui/nginx.conf` - Web server configuration
- `ui/.dockerignore` - Build optimization

**Environment Variables:**
- `VITE_API_URL` - Backend service URL (set at build time)

**Networking:**
- Exposes port 80
- Public HTTPS endpoint via Railway
- Optional custom domain support

### Backend Service (`pdf-anonymizer-api`)

**Purpose:** Process PDF files and provide REST API

**Technology Stack:**
- Python 3.11
- FastAPI framework
- uvicorn ASGI server
- PyMuPDF (PDF processing)
- pdfplumber (table extraction)

**Dockerfile Strategy:** Single-stage build
1. Install system dependencies (poppler-utils)
2. Install Python packages
3. Copy application code
4. Configure uvicorn to listen on `$PORT`

**Key Files:**
- `Dockerfile` - Container definition (root level)
- `.dockerignore` - Build optimization
- `api/main.py` - Application entry point with CORS

**Environment Variables:**
- `PORT` - Listen port (auto-set by Railway)
- `CORS_ORIGINS` - Comma-separated allowed origins

**Networking:**
- Exposes port 8000 (configurable)
- Public HTTPS endpoint via Railway
- CORS headers for cross-origin requests

## Communication Flow

### 1. User Uploads PDF

```
Browser (yourdomain.com)
    │
    │ User selects PDF file
    │
    ▼
Frontend Service (nginx)
    │ Serves React app
    │
    ▼
Browser JavaScript
    │ fetch('/api/extract', FormData)
    │ (resolves to https://backend.railway.app/api/extract)
    │
    │ Preflight: OPTIONS request
    ▼
Backend Service (FastAPI)
    │ CORS middleware checks origin
    │ Returns Access-Control headers
    │
    ▼
Browser
    │ CORS check passes
    │ Sends actual POST request
    │
    ▼
Backend Service
    │ 1. Validate file size/type
    │ 2. Extract text from PDF
    │ 3. Detect PII patterns
    │ 4. Obfuscate matches
    │ 5. Generate new PDF
    │ 6. Store in temp directory (1hr TTL)
    │ 7. Return file_id + summary
    │
    ▼
Browser JavaScript
    │ Display results
    │ Enable download button
    │
```

### 2. User Downloads Processed PDF

```
Browser
    │ Click download button
    │
    ▼
Frontend JavaScript
    │ fetch(`/api/download/${file_id}`)
    │ (resolves to https://backend.railway.app/api/download/xxx)
    │
    ▼
Backend Service
    │ 1. Validate file_id
    │ 2. Check file exists
    │ 3. Stream PDF file
    │ 4. Set Content-Disposition header
    │
    ▼
Browser
    │ Triggers file download
    │
```

## Cross-Origin Resource Sharing (CORS)

### Why CORS is Required

The two-service architecture creates a **cross-origin scenario**:

- **Frontend Origin:** `https://yourdomain.com`
- **Backend Origin:** `https://backend.railway.app`
- **Different domains** = Browser enforces CORS policy

Without CORS configuration, browsers block API requests for security.

### CORS Flow

```
1. Browser: OPTIONS /api/extract
   Origin: https://yourdomain.com

2. Backend CORS Middleware:
   - Check if origin in CORS_ORIGINS
   - If yes, add headers:
     Access-Control-Allow-Origin: https://yourdomain.com
     Access-Control-Allow-Methods: POST, GET, ...
     Access-Control-Allow-Headers: Content-Type, ...

3. Browser:
   - Receives preflight response
   - Checks headers
   - If valid, sends actual request

4. Backend:
   - Process request
   - Add CORS headers to response

5. Browser:
   - Receives response
   - Allows JavaScript to access data
```

### CORS Configuration

In `api/main.py`:

```python
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:80"
)
allowed_origins = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Specific origins only
    allow_credentials=True,
    allow_methods=["*"],            # Allow all HTTP methods
    allow_headers=["*"],            # Allow all headers
)
```

**Production Example:**
```env
CORS_ORIGINS=https://pdf-ui.railway.app,https://yourdomain.com
```

## Environment Variable Strategy

### Build-Time vs Runtime Variables

**Frontend (Build-Time):**
- `VITE_API_URL` - Compiled into JavaScript bundle
- Cannot change without rebuild
- Set before build starts
- Accessible via `import.meta.env.VITE_API_URL`

**Backend (Runtime):**
- `PORT` - Read when uvicorn starts
- `CORS_ORIGINS` - Read when FastAPI initializes
- Can change with restart (no rebuild needed)
- Accessible via `os.getenv()`

### API URL Resolution

In `ui/src/services/api.ts`:

```typescript
const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api';
```

**Local Development:**
- `VITE_API_URL` not set
- Uses relative path `/api`
- Vite proxy forwards to `localhost:8000`

**Production:**
- `VITE_API_URL=https://backend.railway.app`
- Resolves to absolute URL
- Direct requests to backend service

## File Storage

### Temporary File Management

**Backend Behavior:**
- Uploaded PDFs stored in container filesystem
- Processed PDFs stored in temp directory
- Files auto-cleaned after 1-hour TTL

**Railway Considerations:**
- Container filesystem is **ephemeral**
- Files lost on redeploy/restart
- No persistent storage needed (per requirements)
- TTL cleanup runs periodically

**Flow:**
```
Upload → /tmp/uploads/original_abc123.pdf
Process → /tmp/processed/obfuscated_abc123.pdf
Return file_id → "abc123"
After 1hr → File deleted
```

## Health Checks

### Frontend Health Check

**Configuration:**
```toml
[services.healthcheck]
path = "/"
timeout = 10
interval = 30
```

**How it Works:**
- Railway sends `GET /` every 30 seconds
- nginx responds with `index.html`
- 200 status = healthy
- Failures trigger auto-restart

### Backend Health Check

**Configuration:**
```toml
[services.healthcheck]
path = "/health"
timeout = 10
interval = 30
```

**Endpoint:**
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**How it Works:**
- Railway sends `GET /health` every 30 seconds
- FastAPI responds with JSON
- 200 status = healthy
- Failures trigger auto-restart

## Scaling Considerations

### Horizontal Scaling

**Frontend:**
- ✅ Fully stateless
- ✅ No session storage
- ✅ Can scale to multiple instances
- Railway load balancer distributes traffic

**Backend:**
- ✅ Stateless API design
- ✅ No in-memory session state
- ⚠️ Temporary files in container
- **Challenge:** File uploaded to instance A, download request to instance B fails
- **Solution:** Use shared storage (Redis, S3) if scaling beyond 1 instance

### Vertical Scaling

Railway auto-detects resource usage and can scale:
- CPU cores
- Memory allocation
- Disk space

## Security Architecture

### Network Security

**HTTPS Everywhere:**
- Railway provides automatic SSL/TLS
- All traffic encrypted in transit
- Certificates auto-renewed

**Origin Restrictions:**
- CORS limited to specific domains
- No wildcard `*` in production
- Prevents unauthorized API access

### Application Security

**Input Validation:**
- File size limits (20MB max)
- File type validation (PDF only)
- Sanitized user input

**Output Security:**
- Temporary files isolated
- No persistent PII storage
- Auto-cleanup prevents leakage

**Headers:**
- nginx security headers configured:
  - `X-Frame-Options: SAMEORIGIN`
  - `X-Content-Type-Options: nosniff`
  - `X-XSS-Protection: 1; mode=block`

## Deployment Workflow

### Continuous Deployment

```
Developer pushes to GitHub
    │
    ▼
Railway webhook triggered
    │
    ├─▶ Backend Service
    │   1. Pull latest code
    │   2. Build Docker image (Dockerfile)
    │   3. Run health check
    │   4. Route traffic to new container
    │   5. Terminate old container
    │
    └─▶ Frontend Service
        1. Pull latest code
        2. Build Docker image (ui/Dockerfile)
        3. Inject VITE_API_URL
        4. Build React app
        5. Run health check
        6. Route traffic to new container
        7. Terminate old container
```

**Zero-Downtime:**
- New containers start before old ones stop
- Health checks ensure stability
- Traffic switches only when ready

## Alternative Architectures

### Monolith Approach (Not Used)

**Single Service:**
```
┌─────────────────────────────┐
│  Monolith Service           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━  │
│  FastAPI + Static Files     │
│                             │
│  /         → index.html     │
│  /assets/* → static files   │
│  /api/*    → FastAPI routes │
└─────────────────────────────┘
```

**Pros:**
- No CORS needed (same origin)
- Single deployment
- Simpler configuration

**Cons:**
- Frontend/backend coupled
- Cannot scale independently
- Slower frontend updates (Python rebuild)
- Not chosen for this project

### Reverse Proxy Approach (Not Used)

**Single Domain, Multiple Services:**
```
┌─────────────────────────────┐
│  nginx Reverse Proxy        │
│  yourdomain.com             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━  │
│  /       → Frontend Service │
│  /api/*  → Backend Service  │
└─────────────────────────────┘
```

**Pros:**
- Single domain (no CORS)
- Independent services
- Flexible routing

**Cons:**
- Additional service to manage
- Extra complexity
- Railway doesn't provide managed reverse proxy
- Not chosen for this project

## Monitoring and Observability

### Railway Dashboard

**Metrics Available:**
- CPU usage per service
- Memory usage per service
- Network traffic
- Request counts
- Error rates

**Logs:**
- Real-time streaming logs
- Container stdout/stderr
- Deployment logs
- Build logs

### Application Logging

**Backend (Python):**
```python
import logging
logging.info("Processing PDF file_id=%s", file_id)
```
Logs appear in Railway dashboard

**Frontend (nginx):**
- Access logs: Request path, status, timing
- Error logs: 404s, 500s, nginx errors

## Cost Estimation

Railway pricing based on:
- **Build time:** Minutes building containers
- **Runtime:** vCPU-hours and GB-RAM-hours
- **Network:** Egress bandwidth

**Typical Usage:**
- **Frontend:** Low CPU, low memory (~100MB)
- **Backend:** Medium CPU (PDF processing), medium memory (~512MB)

**Optimization Tips:**
- Use `.dockerignore` to reduce build time
- Optimize Docker layers for caching
- Enable Railway sleep mode for dev environments
- Set reasonable resource limits

## Disaster Recovery

### Backup Strategy

**Code:**
- ✅ Version controlled in GitHub
- ✅ Railway pulls from Git
- ✅ Easy rollback to any commit

**Data:**
- ✅ No persistent data to back up
- ✅ Temporary files disposable
- ✅ Configuration in environment variables

### Rollback Procedure

1. Railway Deployments tab
2. Select previous successful deployment
3. Click "Redeploy"
4. Zero-downtime rollback

### Failure Scenarios

**Container Crash:**
- Health check fails
- Railway auto-restarts
- Restart policy: `on_failure` (max 10 retries)

**Railway Outage:**
- Deploy to multiple regions (if needed)
- Use Railway status page for updates
- Consider multi-cloud backup deployment

## Future Enhancements

### Potential Improvements

1. **Shared Storage:**
   - Add Redis for distributed file tracking
   - Use S3 for temporary file storage
   - Enable horizontal scaling

2. **Caching:**
   - Add CDN (Cloudflare) for frontend assets
   - Cache API responses (config endpoints)

3. **Background Jobs:**
   - Queue large PDF processing
   - Email processed files instead of download

4. **Database:**
   - Track processing history
   - User accounts and preferences
   - Analytics

5. **Monitoring:**
   - Add Sentry for error tracking
   - Add application metrics (Prometheus)
   - Set up alerting

## Conclusion

The two-service architecture provides:

✅ **Separation of Concerns:** Frontend and backend independent
✅ **Scalability:** Each service scales independently
✅ **Flexibility:** Different tech stacks, update cycles
✅ **Reliability:** Failure isolation, independent health checks
✅ **Developer Experience:** Clear boundaries, easier testing

Trade-offs:
- CORS configuration required
- More environment variables
- Slightly more complex deployment

For this application, the benefits outweigh the costs, providing a production-ready, scalable architecture.
