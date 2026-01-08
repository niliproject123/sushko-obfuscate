from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.routes.extract import router as extract_router

app = FastAPI(
    title="PDF Text Extractor",
    description="Extract text from PDFs and obfuscate PII",
    version="1.0.0"
)

# Include routes
app.include_router(extract_router, prefix="/api", tags=["extraction"])


# Serve static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """Serve the web UI."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "PDF Text Extractor API", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
