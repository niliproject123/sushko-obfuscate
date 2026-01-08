from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.extract import router as extract_router
from api.routes.config import router as config_router

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
