"""
Main API router that combines all API endpoints.
This file provides a central place to include all API routes.
"""
from fastapi import APIRouter

# Import individual routers (to be implemented)
# from .audio import router as audio_router
# from .recipes import router as recipes_router
# from .websocket import router as websocket_router

# Create main API router
router = APIRouter()

# Placeholder endpoints that can be expanded later
@router.get("/status")
async def api_status():
    """API status endpoint"""
    return {
        "message": "Hey Chef v2 API is operational",
        "version": "2.0.0",
        "endpoints": {
            "audio": "Audio processing endpoints (to be implemented)",
            "recipes": "Recipe management endpoints (to be implemented)", 
            "websocket": "Real-time communication (available at /ws)"
        }
    }

# Include individual routers when they're ready
# router.include_router(audio_router, prefix="/audio", tags=["audio"])
# router.include_router(recipes_router, prefix="/recipes", tags=["recipes"]) 
# router.include_router(websocket_router, prefix="/ws", tags=["websocket"])