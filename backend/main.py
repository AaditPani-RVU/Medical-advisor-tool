"""
FastAPI application — Verified Health Content API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.settings import settings
from backend.api.routes_content import router as content_router
from backend.api.routes_family import router as family_router
from backend.api.routes_triage import router as triage_router
from backend.api.routes_chat import router as chat_router
from backend.api.routes_ocr import router as ocr_router

app = FastAPI(
    title="Verified Health Content API",
    description=(
        "Educational-only API serving verified health content from trusted sources. "
        "NOT medical advice. NOT diagnosis. NOT treatment."
    ),
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(content_router, prefix="/content", tags=["Content"])
app.include_router(family_router, prefix="/family", tags=["Family"])
app.include_router(triage_router, prefix="/triage", tags=["Triage"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(ocr_router, prefix="/analyze-prescription", tags=["OCR"])


@app.get("/")
def root():
    return {
        "service": "Verified Health Content API",
        "status": "running",
        "disclaimer": "Educational content only. Not medical advice. If worried, seek professional care.",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
