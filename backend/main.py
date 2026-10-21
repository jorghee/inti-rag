"""FastAPI application entrypoint for Inti Legal AI Assistant."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.api.v1.api import api_router
from backend.core.config import settings

app = FastAPI(
    title="Inti - Asistente Juridico Inteligente API",
    description="Backend API for institutional legal research and RAG assistance at UNSA.",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix="/api/v1")

# Mount frontend directory for static web access if available
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    def root_redirect():
        """Redirect root requests to frontend login interface."""
        index_file = FRONTEND_DIR / "index.html"
        if index_file.is_file():
            return RedirectResponse(url="/static/index.html")
        return RedirectResponse(url="/docs")
else:

    @app.get("/", include_in_schema=False)
    def root():
        """Default root redirect to API documentation."""
        return RedirectResponse(url="/docs")
