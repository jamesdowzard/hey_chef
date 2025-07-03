"""
Simplified FastAPI backend for Hey Chef v2 - AI voice cooking assistant.
Production-ready entry point with comprehensive error handling, logging, and WebSocket support.
"""
import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("hey_chef_v2_api.log")
    ]
)
logger = logging.getLogger("hey_chef_v2")

# Global state for application health and WebSocket connections
app_state = {
    "startup_time": None,
    "shutdown_initiated": False,
    "active_websockets": set(),
    "request_count": 0,
    "error_count": 0
}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all incoming requests and responses"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = datetime.utcnow()
        app_state["request_count"] += 1
        
        # Log incoming request
        logger.info(f"Incoming {request.method} request to {request.url.path}")
        
        try:
            response = await call_next(request)
            
            # Log successful response
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Duration: {duration:.3f}s"
            )
            
            return response
            
        except Exception as e:
            app_state["error_count"] += 1
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"- Error: {str(e)} - Duration: {duration:.3f}s"
            )
            raise


async def startup_tasks():
    """Tasks to run on application startup"""
    logger.info("Starting Hey Chef v2 Backend API...")
    app_state["startup_time"] = datetime.utcnow()
    
    # Verify critical environment variables
    required_env_vars = ["OPENAI_API_KEY", "PICO_ACCESS_KEY"]
    missing_vars = []
    
    for var in required_env_vars:
        env_val = getattr(settings, var.lower(), None)
        if not env_val:
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)} - some features may be disabled")
    
    # Verify wake word model exists
    wake_word_path = Path(settings.get_wake_word_path())
    if not wake_word_path.exists():
        logger.warning(f"Wake word model not found at: {wake_word_path}")
    
    # Test critical dependencies
    try:
        import openai
        logger.info("OpenAI client available")
    except ImportError:
        logger.warning("OpenAI package not available")
    
    try:
        import pvporcupine
        logger.info("Porcupine wake word detection available")
    except ImportError:
        logger.warning("Porcupine package not available - wake word detection disabled")
    
    logger.info("Startup tasks completed successfully")


async def shutdown_tasks():
    """Tasks to run on application shutdown"""
    logger.info("Initiating graceful shutdown...")
    app_state["shutdown_initiated"] = True
    
    # Close all active WebSocket connections
    if app_state["active_websockets"]:
        logger.info(f"Closing {len(app_state['active_websockets'])} active WebSocket connections")
        disconnect_tasks = []
        for websocket in app_state["active_websockets"].copy():
            disconnect_tasks.append(websocket.close())
        
        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
    
    # Log final statistics
    uptime = datetime.utcnow() - app_state["startup_time"] if app_state["startup_time"] else None
    logger.info(
        f"Shutdown complete - Uptime: {uptime}, "
        f"Total requests: {app_state['request_count']}, "
        f"Total errors: {app_state['error_count']}"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    try:
        await startup_tasks()
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        await shutdown_tasks()
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Create FastAPI app instance with lifespan management
app = FastAPI(
    title=settings.app_name,
    description="Production-ready voice-controlled AI cooking assistant backend API",
    version="2.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    lifespan=lifespan
)

# Add security middleware
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure this properly for production
    )

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper logging"""
    logger.warning(f"HTTP {exc.status_code} error on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Request validation failed",
            "details": exc.errors(),
            "status_code": 422,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error on {request.url.path}: {str(exc)}", exc_info=True)
    app_state["error_count"] += 1
    
    if settings.environment == "development":
        # Return detailed error info in development
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "details": str(exc),
                "type": exc.__class__.__name__,
                "status_code": 500,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    else:
        # Return generic error in production
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "status_code": 500,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Core API endpoints
@app.get("/")
async def root():
    """Root endpoint with comprehensive status information"""
    uptime = None
    if app_state["startup_time"]:
        uptime = str(datetime.utcnow() - app_state["startup_time"])
    
    return {
        "message": "Hey Chef v2 Backend API",
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.environment,
        "uptime": uptime,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "app_name": settings.app_name,
        "environment": settings.environment,
        "uptime": None,
        "stats": {
            "total_requests": app_state["request_count"],
            "total_errors": app_state["error_count"],
            "active_websockets": len(app_state["active_websockets"])
        },
        "dependencies": {},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if app_state["startup_time"]:
        health_status["uptime"] = str(datetime.utcnow() - app_state["startup_time"])
    
    # Check critical dependencies
    try:
        import openai
        health_status["dependencies"]["openai"] = "available"
    except ImportError:
        health_status["dependencies"]["openai"] = "unavailable"
        health_status["status"] = "degraded"
    
    try:
        import pvporcupine
        health_status["dependencies"]["porcupine"] = "available"
    except ImportError:
        health_status["dependencies"]["porcupine"] = "unavailable"
    
    # Check wake word model
    wake_word_path = Path(settings.get_wake_word_path())
    health_status["dependencies"]["wake_word_model"] = "available" if wake_word_path.exists() else "unavailable"
    
    return health_status


@app.get("/metrics")
async def get_metrics():
    """Basic metrics endpoint for monitoring"""
    uptime_seconds = 0
    if app_state["startup_time"]:
        uptime_seconds = (datetime.utcnow() - app_state["startup_time"]).total_seconds()
    
    return {
        "uptime_seconds": uptime_seconds,
        "total_requests": app_state["request_count"],
        "total_errors": app_state["error_count"],
        "active_websockets": len(app_state["active_websockets"]),
        "error_rate": app_state["error_count"] / max(app_state["request_count"], 1),
        "timestamp": datetime.utcnow().isoformat()
    }


# WebSocket endpoint for real-time communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time audio and messaging"""
    await websocket.accept()
    app_state["active_websockets"].add(websocket)
    client_id = id(websocket)
    
    logger.info(f"WebSocket client {client_id} connected")
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connection",
            "message": "Connected to Hey Chef v2 WebSocket",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                logger.debug(f"Received WebSocket message from {client_id}: {data}")
                
                # Echo message back for now (implement specific handlers later)
                await websocket.send_json({
                    "type": "echo",
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error for client {client_id}: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "An error occurred processing your message",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket connection error for client {client_id}: {e}")
    finally:
        app_state["active_websockets"].discard(websocket)
        logger.info(f"WebSocket client {client_id} disconnected")


# Basic API status endpoint
@app.get("/api/v1/status")
async def api_status():
    """API status endpoint"""
    return {
        "message": "Hey Chef v2 API is operational",
        "version": "2.0.0",
        "endpoints": {
            "root": "Root status endpoint",
            "health": "Health check endpoint",
            "metrics": "Basic metrics endpoint",
            "websocket": "Real-time communication available at /ws"
        }
    }


# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    app_state["shutdown_initiated"] = True


if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info(f"Starting Hey Chef v2 API server on {settings.host}:{settings.port}")
    
    uvicorn.run(
        "main_simple:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload and settings.environment == "development",
        log_level=settings.log_level.lower(),
        access_log=True,
        server_header=False,
        date_header=False
    )