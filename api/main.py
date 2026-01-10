import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.routes.extract import router as extract_router
from api.routes.config import router as config_router

# Static files directory (built frontend in production)
STATIC_DIR = Path("/app/static")
INDEX_HTML = STATIC_DIR / "index.html"

app = FastAPI(
    title="PDF Anonymizer API",
    description="Extract text from PDFs and obfuscate PII with configurable patterns",
    version="2.0.0"
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(extract_router, prefix="/api", tags=["extraction"])
app.include_router(config_router, prefix="/api", tags=["configuration"])


@app.get("/")
async def root():
    """API root."""
    return {"message": "PDF Text Extractor API", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Serve frontend static files in production
if STATIC_DIR.exists() and INDEX_HTML.exists():
    # Mount static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    # Serve index.html for all non-API routes (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve the React SPA for all non-API routes."""
        # Check if it's a static file that exists
        file_path = STATIC_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        # Otherwise serve index.html for SPA routing
        return FileResponse(INDEX_HTML)
