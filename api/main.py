import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

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

# Include API routes
app.include_router(extract_router, prefix="/api", tags=["extraction"])
app.include_router(config_router, prefix="/api", tags=["configuration"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """Mount static files on startup if they exist."""
    if STATIC_DIR.exists():
        print(f"Static directory found: {STATIC_DIR}")
        print(f"Contents: {list(STATIC_DIR.iterdir())}")
        if (STATIC_DIR / "assets").exists():
            app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")
            print("Mounted /assets")
    else:
        print(f"Static directory NOT found: {STATIC_DIR}")


@app.get("/")
async def root(request: Request):
    """Serve index.html or API info."""
    if INDEX_HTML.exists():
        return FileResponse(INDEX_HTML)
    return {"message": "PDF Text Extractor API", "docs": "/docs"}


@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    """Serve static files or index.html for SPA routing."""
    # Skip API routes (they're handled by routers)
    if full_path.startswith("api/"):
        return JSONResponse({"error": "Not found"}, status_code=404)

    # Try to serve static file
    if STATIC_DIR.exists():
        file_path = STATIC_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

    # Serve index.html for SPA routing
    if INDEX_HTML.exists():
        return FileResponse(INDEX_HTML)

    return JSONResponse({"error": "Not found"}, status_code=404)
