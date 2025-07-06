"""
WebSocket API for real-time communication with Hey Chef v2 frontend.

Handles voice commands, audio processing status, and recipe interactions
through persistent WebSocket connections.
"""

import json
import asyncio
from typing import Dict, Set, Optional
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState

from app.core.config import Settings
from app.core.models import (
    WebSocketMessage, AudioProcessingRequest, AudioProcessingResponse,
    RecipeSearchRequest, RecipeResponse, ErrorResponse, StatusUpdateMessage
)
from app.core.logger import get_logger
from app.core.audio_pipeline import AudioPipelineManager
from app.services import create_wake_word_service, create_stt_service, create_tts_service, create_llm_service

logger = get_logger()
router = APIRouter()

# Global connection manager
class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket) -> str:
        """Accept new WebSocket connection and return session ID."""
        await websocket.accept()
        session_id = str(uuid4())
        self.active_connections[session_id] = websocket
        self.user_sessions[session_id] = {
            "connected_at": asyncio.get_event_loop().time(),
            "audio_pipeline": None,
            "recipe_context": None
        }
        logger.info(f"WebSocket connected: {session_id}")
        return session_id
    
    def disconnect(self, session_id: str):
        """Remove WebSocket connection and cleanup session."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.user_sessions:
            # Cleanup audio pipeline if active
            pipeline = self.user_sessions[session_id].get("audio_pipeline")
            if pipeline:
                asyncio.create_task(pipeline.stop())
            del self.user_sessions[session_id]
        logger.info(f"WebSocket disconnected: {session_id}")
    
    async def send_message(self, session_id: str, message: WebSocketMessage):
        """Send message to specific session."""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_text(message.model_dump_json())
                except Exception as e:
                    logger.error(f"Failed to send message to {session_id}: {e}")
                    self.disconnect(session_id)
    
    async def broadcast(self, message: WebSocketMessage):
        """Broadcast message to all connected sessions."""
        disconnected = []
        for session_id, websocket in self.active_connections.items():
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(message.model_dump_json())
                else:
                    disconnected.append(session_id)
            except Exception as e:
                logger.error(f"Failed to broadcast to {session_id}: {e}")
                disconnected.append(session_id)
        
        # Cleanup disconnected sessions
        for session_id in disconnected:
            self.disconnect(session_id)

# Global connection manager instance
manager = ConnectionManager()

async def get_settings() -> Settings:
    """Dependency to get settings."""
    return Settings()

@router.websocket("/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for audio processing communication.
    
    Handles:
    - Audio pipeline control (start/stop)
    - Real-time audio status updates
    - Voice command processing
    - Recipe context management
    """
    # Create settings instance
    settings = Settings()
    session_id = await manager.connect(websocket)
    
    try:
        # Send welcome message
        welcome_msg = WebSocketMessage(
            type="connection",
            data={"status": "connected", "session_id": session_id},
            timestamp=asyncio.get_event_loop().time()
        )
        await manager.send_message(session_id, welcome_msg)
        
        # Message processing loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = WebSocketMessage.model_validate_json(data)
                
                logger.debug(f"Received message from {session_id}: {message.type}")
                
                # Route message based on type
                await handle_websocket_message(session_id, message, settings)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected normally: {session_id}")
                break
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from {session_id}: {e}")
                error_msg = WebSocketMessage(
                    type="error",
                    data=ErrorResponse(
                        error="Invalid JSON format",
                        details=str(e)
                    ).model_dump(),
                    timestamp=asyncio.get_event_loop().time()
                )
                await manager.send_message(session_id, error_msg)
            except Exception as e:
                logger.error(f"Unexpected error handling message from {session_id}: {e}")
                error_msg = WebSocketMessage(
                    type="error", 
                    data=ErrorResponse(
                        error="Internal server error",
                        details=str(e)
                    ).model_dump(),
                    timestamp=asyncio.get_event_loop().time()
                )
                await manager.send_message(session_id, error_msg)
    
    except Exception as e:
        logger.error(f"WebSocket connection error for {session_id}: {e}")
    finally:
        manager.disconnect(session_id)

async def handle_websocket_message(
    session_id: str, 
    message: WebSocketMessage, 
    settings: Settings
):
    """Handle incoming WebSocket messages based on type."""
    
    if message.type == "audio_start":
        await handle_audio_start(session_id, message, settings)
    elif message.type == "audio_stop":
        await handle_audio_stop(session_id, message)
    elif message.type == "recipe_load":
        await handle_recipe_load(session_id, message)
    elif message.type == "settings_update":
        await handle_settings_update(session_id, message)
    elif message.type == "connection":
        await handle_connection_message(session_id, message)
    elif message.type == "text_message":
        await handle_text_message(session_id, message)
    elif message.type == "heartbeat":
        await handle_heartbeat(session_id, message)
    else:
        logger.warning(f"Unknown message type from {session_id}: {message.type}")
        error_msg = WebSocketMessage(
            type="error",
            data=ErrorResponse(
                error="Unknown message type",
                details=f"Message type '{message.type}' is not supported"
            ).model_dump(),
            timestamp=asyncio.get_event_loop().time()
        )
        await manager.send_message(session_id, error_msg)

async def handle_audio_start(session_id: str, message: WebSocketMessage, settings: Settings):
    """Start audio processing pipeline for session."""
    try:
        session = manager.user_sessions[session_id]
        
        # Don't start if already running
        if session.get("audio_pipeline"):
            await send_audio_status(session_id, "already_running", "Audio pipeline already active")
            return
        
        # Create audio pipeline
        wake_word_service = create_wake_word_service()
        stt_service = create_stt_service()
        tts_service = create_tts_service()
        llm_service = create_llm_service()
        
        # Create pipeline with settings only
        pipeline = AudioPipelineManager(settings)
        
        # Inject services using the proper method
        pipeline.inject_services(
            wake_word_service=wake_word_service,
            stt_service=stt_service,
            ai_service=llm_service,
            tts_service=tts_service,
            session_manager=None  # TODO: Implement session manager
        )
        
        # Set WebSocket callback
        pipeline.set_websocket_callback(
            lambda session_id, message: asyncio.create_task(
                send_audio_status(session_id, message.type, message.model_dump())
            )
        )
        
        # Store pipeline in session
        session["audio_pipeline"] = pipeline
        
        # Start pipeline
        recipe_text = session.get("recipe_context", "")
        await pipeline.start(recipe_text=recipe_text)
        
        await send_audio_status(session_id, "started", "Audio pipeline started successfully")
        logger.info(f"Audio pipeline started for session {session_id}")
        
    except Exception as e:
        logger.error(f"Failed to start audio pipeline for {session_id}: {e}")
        await send_audio_status(session_id, "error", f"Failed to start audio pipeline: {str(e)}")

async def handle_audio_stop(session_id: str, message: WebSocketMessage):
    """Stop audio processing pipeline for session."""
    try:
        session = manager.user_sessions[session_id]
        pipeline = session.get("audio_pipeline")
        
        if not pipeline:
            await send_audio_status(session_id, "not_running", "No audio pipeline to stop")
            return
        
        # Stop pipeline
        await pipeline.stop()
        session["audio_pipeline"] = None
        
        await send_audio_status(session_id, "stopped", "Audio pipeline stopped successfully")
        logger.info(f"Audio pipeline stopped for session {session_id}")
        
    except Exception as e:
        logger.error(f"Failed to stop audio pipeline for {session_id}: {e}")
        await send_audio_status(session_id, "error", f"Failed to stop audio pipeline: {str(e)}")

async def handle_recipe_load(session_id: str, message: WebSocketMessage):
    """Load recipe context for session."""
    try:
        recipe_data = message.data
        session = manager.user_sessions[session_id]
        session["recipe_context"] = recipe_data.get("content", "")
        
        response_msg = WebSocketMessage(
            type="recipe_loaded",
            data={"status": "success", "recipe_title": recipe_data.get("title", "Unknown")},
            timestamp=asyncio.get_event_loop().time()
        )
        await manager.send_message(session_id, response_msg)
        logger.info(f"Recipe loaded for session {session_id}: {recipe_data.get('title', 'Unknown')}")
        
    except Exception as e:
        logger.error(f"Failed to load recipe for {session_id}: {e}")
        error_msg = WebSocketMessage(
            type="error",
            data=ErrorResponse(
                error="Failed to load recipe",
                details=str(e)
            ).model_dump(),
            timestamp=asyncio.get_event_loop().time()
        )
        await manager.send_message(session_id, error_msg)

async def handle_settings_update(session_id: str, message: WebSocketMessage):
    """Handle settings updates from client."""
    try:
        # TODO: Implement settings updates
        response_msg = WebSocketMessage(
            type="settings_updated",
            data={"status": "success"},
            timestamp=asyncio.get_event_loop().time()
        )
        await manager.send_message(session_id, response_msg)
        
    except Exception as e:
        logger.error(f"Failed to update settings for {session_id}: {e}")
        error_msg = WebSocketMessage(
            type="error",
            data=ErrorResponse(
                error="Failed to update settings",
                details=str(e)
            ).model_dump(),
            timestamp=asyncio.get_event_loop().time()
        )
        await manager.send_message(session_id, error_msg)

async def send_audio_status(session_id: str, status: str, message: str):
    """Send audio status update to client."""
    status_msg = WebSocketMessage(
        type="audio_status",
        data={
            "status": status,
            "message": message,
            "timestamp": asyncio.get_event_loop().time()
        },
        timestamp=asyncio.get_event_loop().time()
    )
    await manager.send_message(session_id, status_msg)

async def handle_connection_message(session_id: str, message: WebSocketMessage):
    """Handle connection status messages."""
    try:
        response_msg = WebSocketMessage(
            type="connection_established",
            data={"status": "acknowledged", "session_id": session_id},
            timestamp=asyncio.get_event_loop().time()
        )
        await manager.send_message(session_id, response_msg)
        logger.debug(f"Connection message acknowledged for session {session_id}")
        
    except Exception as e:
        logger.error(f"Failed to handle connection message for {session_id}: {e}")

async def handle_text_message(session_id: str, message: WebSocketMessage):
    """Handle text messages from client."""
    try:
        # Extract text from message data
        text_content = message.data.get("text", "") if message.data else ""
        
        # Echo back for now (can be extended for AI processing)
        response_msg = WebSocketMessage(
            type="text_message",
            data={
                "response": f"Received: {text_content}",
                "original": text_content,
                "timestamp": asyncio.get_event_loop().time()
            },
            timestamp=asyncio.get_event_loop().time()
        )
        await manager.send_message(session_id, response_msg)
        logger.debug(f"Text message processed for session {session_id}")
        
    except Exception as e:
        logger.error(f"Failed to handle text message for {session_id}: {e}")

async def handle_heartbeat(session_id: str, message: WebSocketMessage):
    """Handle heartbeat messages to keep connection alive."""
    try:
        response_msg = WebSocketMessage(
            type="heartbeat",
            data={"status": "alive", "timestamp": asyncio.get_event_loop().time()},
            timestamp=asyncio.get_event_loop().time()
        )
        await manager.send_message(session_id, response_msg)
        logger.debug(f"Heartbeat acknowledged for session {session_id}")
        
    except Exception as e:
        logger.error(f"Failed to handle heartbeat for {session_id}: {e}")

# Health check for WebSocket connections
@router.get("/health")
async def websocket_health():
    """WebSocket service health check."""
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "total_sessions": len(manager.user_sessions)
    }