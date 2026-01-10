# Deployment Guide

This guide explains how to deploy the PDF Obfuscator application to Railway.

## Prerequisites

- A [Railway](https://railway.app) account (free tier available)
- GitHub account with access to this repository

## Quick Deploy to Railway

1. **Login to Railway**
   - Go to https://railway.app
   - Sign in with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `niliproject123/sushko-obfuscate`

3. **Configure Branch**
   - In Settings, set the branch to deploy from (e.g., `main`)
   - Railway auto-detects the Dockerfile

4. **Configure Networking**
   - Go to Settings → Networking
   - Railway assigns a public URL automatically
   - **Important**: Set Target Port to match the `PORT` environment variable (usually `8080`)

5. **Deploy**
   - Railway automatically builds and deploys on every push
   - Check the Deployments tab for build logs

## Environment Variables

No environment variables are required. The application uses:
- `PORT` - Automatically set by Railway (typically `8080`)

## Verifying Deployment

After deployment, verify the application:

1. **Health Check**: `https://your-app.up.railway.app/health`
   - Should return: `{"status": "healthy"}`

2. **API Docs**: `https://your-app.up.railway.app/docs`
   - Interactive Swagger documentation

3. **Frontend**: `https://your-app.up.railway.app/`
   - The React UI for uploading and processing PDFs

## Local Development

### Backend (Python/FastAPI)

```bash
# From project root
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn api.main:app --reload --host localhost --port 8000
```

### Frontend (React/TypeScript)

```bash
# From ui/ directory
cd ui
npm install
npm run dev
```

- Backend runs on: http://localhost:8000
- Frontend runs on: http://localhost:5173
- Frontend proxies `/api` requests to backend automatically

## Troubleshooting

### "Application failed to respond"

1. Check the deploy logs in Railway
2. Verify the Target Port matches what the app is listening on
3. Look for startup errors in the logs

### Frontend not loading (shows JSON instead)

1. Check build logs for npm/vite errors
2. Verify the static files were copied to `/app/static`
3. Check startup logs for "Static directory found" message

### Port mismatch

Railway sets the `PORT` environment variable. The app uses `${PORT:-8000}`.
Make sure the Target Port in Railway networking settings matches the actual port.

## Costs

Railway offers:
- **Free tier**: 500 hours/month, 512MB RAM
- **Hobby plan**: $5/month for always-on deployments

This application typically uses ~200-300MB RAM.
