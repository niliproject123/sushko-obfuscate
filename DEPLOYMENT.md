# Railway Deployment Guide

This document provides step-by-step instructions for deploying the PDF Anonymizer application to Railway using a two-service architecture.

## Overview

The application is deployed as two independent services:
- **Backend API Service** - FastAPI application serving the REST API
- **Frontend UI Service** - React application served via nginx

## Prerequisites

- Railway account (https://railway.app)
- GitHub repository connected to Railway
- Custom domain (optional)

## Architecture

```
┌─────────────────────┐
│   Your Domain       │
│  (yourdomain.com)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐         ┌─────────────────────┐
│  Frontend Service   │────────▶│  Backend Service    │
│  (React + nginx)    │  CORS   │  (FastAPI)          │
│  Port: 80           │         │  Port: 8000         │
│                     │         │                     │
│  https://ui-xxx.    │         │  https://api-xxx.   │
│  railway.app        │         │  railway.app        │
└─────────────────────┘         └─────────────────────┘
```

## Deployment Steps

### Step 1: Connect Repository to Railway

1. Log in to Railway dashboard
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose the `sushko-obfuscate` repository
5. Railway will automatically detect the `railway.toml` configuration

### Step 2: Deploy Backend Service

Railway will create the `pdf-anonymizer-api` service automatically.

1. Wait for the initial build to complete
2. Once deployed, go to the service **Settings** → **Networking**
3. Copy the generated Railway URL (e.g., `https://pdf-anonymizer-api-production.up.railway.app`)
4. **Save this URL** - you'll need it for the frontend configuration

#### Verify Backend Health

```bash
curl https://your-backend-url.railway.app/health
# Expected: {"status":"healthy"}

# Check API documentation
open https://your-backend-url.railway.app/docs
```

### Step 3: Configure and Deploy Frontend Service

Railway will create the `pdf-anonymizer-ui` service automatically.

#### Add Environment Variables

1. Go to `pdf-anonymizer-ui` service
2. Click **Variables** tab
3. Add the following variable:

```env
VITE_API_URL=https://your-backend-url.railway.app
```

**Important:**
- Use the backend URL from Step 2
- Do NOT include `/api` suffix
- Do NOT include trailing slash

4. Railway will automatically rebuild and redeploy

#### Get Frontend URL

1. Go to **Settings** → **Networking**
2. Copy the generated Railway URL (e.g., `https://pdf-anonymizer-ui-production.up.railway.app`)

### Step 4: Update Backend CORS Configuration

Now that you have the frontend URL, configure the backend to accept requests from it.

1. Go to `pdf-anonymizer-api` service
2. Click **Variables** tab
3. Add the following variable:

```env
CORS_ORIGINS=https://your-frontend-url.railway.app
```

**Multiple origins (if using custom domain):**
```env
CORS_ORIGINS=https://your-frontend-url.railway.app,https://yourdomain.com
```

4. Railway will automatically redeploy the backend

### Step 5: Configure Custom Domain (Optional)

#### For Frontend Service

1. Go to `pdf-anonymizer-ui` service
2. Click **Settings** → **Domains**
3. Click **"Custom Domain"**
4. Enter your domain (e.g., `yourdomain.com` or `app.yourdomain.com`)
5. Railway will provide DNS configuration instructions
6. Add the CNAME record to your DNS provider:
   ```
   CNAME  yourdomain.com  →  your-app.up.railway.app
   ```
7. Wait for DNS propagation (5-60 minutes)
8. Railway automatically provisions SSL certificate

#### Update CORS After Custom Domain

Once your custom domain is active, update the backend CORS:

```env
CORS_ORIGINS=https://your-frontend-url.railway.app,https://yourdomain.com
```

### Step 6: Verify Deployment

#### Backend Tests

```bash
# Health check
curl https://your-backend-url.railway.app/health

# Test configuration endpoint
curl https://your-backend-url.railway.app/api/config

# Test with sample PDF upload
curl -X POST https://your-backend-url.railway.app/api/extract \
  -F "file=@sample.pdf" \
  -F "custom_obfuscations=[]"
```

#### Frontend Tests

1. Open your frontend URL in a browser
2. Open Browser DevTools → Console
3. Check for errors (especially CORS errors)
4. Open Network tab
5. Upload a test PDF file
6. Verify:
   - API requests go to correct backend URL
   - Requests return 200 status codes
   - No CORS errors in console
   - Download works correctly

## Environment Variables Reference

### Backend Service (`pdf-anonymizer-api`)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `CORS_ORIGINS` | Yes | Comma-separated list of allowed origins | `https://ui.railway.app,https://yourdomain.com` |
| `PORT` | No | Auto-set by Railway | `8000` (default) |

### Frontend Service (`pdf-anonymizer-ui`)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `VITE_API_URL` | Yes | Backend service URL (no trailing slash) | `https://api.railway.app` |

## Troubleshooting

### CORS Errors

**Symptom:** Console shows `Access-Control-Allow-Origin` errors

**Solution:**
1. Check `CORS_ORIGINS` is set in backend service
2. Verify it includes the exact frontend URL (including `https://`)
3. Check for typos (trailing slashes, wrong protocol)
4. Redeploy backend after changes

### API Requests Fail

**Symptom:** Network tab shows failed requests to wrong URL

**Solution:**
1. Verify `VITE_API_URL` is set correctly in frontend service
2. Frontend must rebuild when env vars change - check build logs
3. Clear browser cache and hard reload

### Frontend Shows Blank Page

**Symptom:** White screen, no content

**Solution:**
1. Check Railway build logs for frontend service
2. Verify nginx is running (check service logs)
3. Check browser console for JavaScript errors
4. Verify `dist` folder was created during build

### Backend 502/503 Errors

**Symptom:** Health check fails

**Solution:**
1. Check Railway logs for backend service
2. Verify `PORT` env var is being used correctly
3. Check for Python errors in startup
4. Verify dependencies installed correctly

## Monitoring

### View Logs

Railway provides real-time logs for each service:

1. Go to service in Railway dashboard
2. Click **"View Logs"** tab
3. Monitor for errors during requests

### Health Checks

Both services have health checks configured in `railway.toml`:

- **Backend:** `GET /health` every 30s
- **Frontend:** `GET /` every 30s

If health checks fail, Railway will restart the service automatically.

## Cost Optimization

Railway pricing is based on usage. To optimize costs:

1. **Use sleep mode** - Railway can pause services when inactive
2. **Monitor resource usage** - Check CPU/memory in dashboard
3. **Optimize builds** - `.dockerignore` files reduce build times
4. **Set spending limits** - Configure in Railway account settings

## Security Recommendations

### Production Checklist

- [ ] CORS limited to specific domains (not `*`)
- [ ] Custom domain configured with SSL
- [ ] Environment variables set (never hardcoded)
- [ ] Railway service variables encrypted by default
- [ ] File upload size limits enforced (20MB in code)
- [ ] Temporary files auto-cleanup enabled (1hr TTL)

### DNS Security

When configuring custom domain:
- Use DNSSEC if your DNS provider supports it
- Enable CAA records to restrict certificate issuance
- Consider using Cloudflare for DDoS protection

## Updating the Application

### Code Changes

1. Push changes to GitHub repository
2. Railway automatically detects changes
3. Triggers rebuild and redeploy
4. Zero-downtime deployment

### Environment Variable Changes

1. Update variables in Railway dashboard
2. Service automatically redeploys
3. Frontend requires rebuild for build-time vars (`VITE_*`)

## Rollback Procedure

If deployment fails:

1. Go to service in Railway dashboard
2. Click **"Deployments"** tab
3. Find last working deployment
4. Click **"Redeploy"**

## Support

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **Application Issues:** Check GitHub repository issues
