"""
Cyber Threat Intelligence Platform - FastAPI Application Entry Point

This platform is a RESEARCH AND PROTOTYPE system for cybersecurity studies.
It is designed to help identify domains potentially associated with online gambling,
analyze their infrastructure, classify them using machine learning, and provide
threat intelligence dashboards and DNS filtering mechanisms.

DISCLAIMER: Machine learning classification represents an automated risk indication
and does not constitute legal determination.
"""
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
import sys
import asyncio

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import CTIException
from app.api.v1.router import api_router
from app.database.init_db import init_db

# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - runs on startup and shutdown."""
    logger.info("application_starting", version=settings.APP_VERSION)
    await init_db()
    logger.info("application_started")
    yield
    logger.info("application_shutting_down")


app = FastAPI(
    title="Cyber Threat Intelligence Platform",
    description=(
        "Research platform for detecting, analyzing, and mitigating "
        "domains potentially associated with online gambling. "
        "ML classification represents automated risk indication, "
        "not legal determination."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

from fastapi.staticfiles import StaticFiles

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Screenshots Directory
import os
screenshots_path = os.path.join(os.getcwd(), "screenshots")
os.makedirs(screenshots_path, exist_ok=True)
app.mount("/screenshots", StaticFiles(directory=screenshots_path), name="screenshots")

# Include API routes
app.include_router(api_router)


# ── Exception Handlers ──────────────────────────────────────────────

@app.exception_handler(CTIException)
async def cti_exception_handler(request: Request, exc: CTIException):
    """Handle custom CTI exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": type(exc).__name__,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
        },
    )


# ── Health Check ────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with platform info."""
    return {
        "name": "Cyber Threat Intelligence Platform",
        "version": settings.APP_VERSION,
        "description": (
            "Research platform for cybersecurity threat intelligence. "
            "ML classification represents automated risk indication, "
            "not legal determination."
        ),
        "docs": "/docs" if settings.is_development else None,
        "health": "/health",
    }
