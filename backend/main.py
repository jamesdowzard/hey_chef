"""
Hey Chef v2 - FastAPI Main Application

Production-ready FastAPI backend with WebSocket support, CORS middleware,
and comprehensive error handling for the Hey Chef voice assistant.
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.core.config import Settings
from app.api import websocket, audio, recipes


# Global settings instance
settings = Settings()

# Setup basic logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hey_chef_v2")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    logger.info("🚀 Starting Hey Chef v2 backend...")
    
    # Startup
    try:
        # Initialize services if needed
        logger.info("✅ Backend services initialized successfully")
        yield
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise
    finally:
        # Shutdown
        logger.info("🛑 Shutting down Hey Chef v2 backend...")
        # Cleanup resources if needed
        logger.info("✅ Backend shutdown complete")


# Create FastAPI application with lifespan management
app = FastAPI(
    title="Hey Chef v2 API",
    description="Voice-controlled cooking assistant with real-time WebSocket communication",
    version="2.0.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    lifespan=lifespan
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://localhost:3001",  # Alternative React port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:5173",
    ] if settings.environment == "development" else settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper logging."""
    logger.error(f"HTTP {exc.status_code} error on {request.url}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with proper logging."""
    logger.error(f"Unexpected error on {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "path": str(request.url)
        }
    )


# Health check endpoints
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "hey-chef-v2",
        "version": "2.0.0",
        "environment": settings.environment
    }


@app.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with service status."""
    # TODO: Add actual service health checks
    health_status = {
        "status": "healthy",
        "service": "hey-chef-v2",
        "version": "2.0.0",
        "environment": settings.environment,
        "services": {
            "audio_pipeline": "healthy",
            "wake_word": "healthy", 
            "speech_to_text": "healthy",
            "text_to_speech": "healthy",
            "llm": "healthy"
        },
        "configuration": {
            "whisper_model": settings.audio.whisper_model_size,
            "llm_model": settings.llm.model,
            "wake_word_sensitivity": settings.audio.wake_word_sensitivity
        }
    }
    
    return health_status


# Include API routers
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
app.include_router(audio.router, prefix="/api/audio", tags=["audio"])
app.include_router(recipes.router, prefix="/api/recipes", tags=["recipes"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Hey Chef v2 API",
        "version": "2.0.0",
        "docs": "/docs" if settings.environment == "development" else "Documentation disabled in production",
        "health": "/health"
    }


# Development server configuration
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.environment == "development" else False,
        log_level="info",
        access_log=True
    )