"""API package for Hey Chef v2 backend."""
from fastapi import APIRouter
from .websocket import router as websocket_router
from .audio import router as audio_router  
from .recipes import router as recipes_router

# Create main API router
router = APIRouter()

# Include all endpoint routers
router.include_router(websocket_router, prefix="", tags=["WebSocket"])
router.include_router(audio_router, prefix="/audio", tags=["Audio"])
router.include_router(recipes_router, prefix="/recipes", tags=["Recipes"])