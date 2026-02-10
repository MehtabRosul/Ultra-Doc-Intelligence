"""
Ultra Doc-Intelligence — FastAPI Application Entry Point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.documents import router as documents_router

app = FastAPI(
    title="Ultra Doc-Intelligence API",
    description="AI-powered logistics document analysis with RAG, guardrails, and structured extraction.",
    version="1.0.0",
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents_router, prefix="/api", tags=["Documents"])


@app.get("/")
async def root():
    return {
        "name": "Ultra Doc-Intelligence API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /api/upload",
            "ask": "POST /api/ask",
            "extract": "POST /api/extract",
            "docs": "GET /docs",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
