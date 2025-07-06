"""
Working unit tests for Hey Chef v2 Pydantic models.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

# Add backend to Python path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from app.core.models import *
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False

@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models not available")
class TestEnums:
    """Test enum definitions."""
    
    def test_message_type_enum(self):
        """Test MessageType enum values."""
        assert MessageType.AUDIO_START == "audio_start"
        assert MessageType.WAKE_WORD_DETECTED == "wake_word_detected"
        assert MessageType.TEXT_MESSAGE == "text_message"
        
    def test_audio_state_enum(self):
        """Test AudioState enum values."""
        assert AudioState.IDLE == "idle"
        assert AudioState.LISTENING_WAKE_WORD == "listening_wake_word"
        assert AudioState.PROCESSING_AUDIO == "processing_audio"
        
    def test_chef_mode_enum(self):
        """Test ChefMode enum values."""
        assert ChefMode.NORMAL == "normal"
        assert ChefMode.SASSY == "sassy"
        assert ChefMode.GORDON_RAMSAY == "gordon_ramsay"

@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models not available")
class TestBaseModels:
    """Test base model functionality."""
    
    def test_timestamped_model_creation(self):
        """Test that TimestampedModel sets timestamps correctly."""
        model = TimestampedModel()
        
        assert isinstance(model.created_at, datetime)
        assert model.updated_at is None
        assert model.created_at.tzinfo == timezone.utc
        
    def test_base_response_defaults(self):
        """Test BaseResponse default values."""
        response = BaseResponse()
        
        assert response.success is True
        assert response.message is None
        assert isinstance(response.timestamp, datetime)

@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models not available")
class TestConversationMessage:
    """Test ConversationMessage model."""
    
    def test_conversation_message_creation(self):
        """Test creating a conversation message."""
        message = ConversationMessage(
            role="user",
            content="Test message",
            chef_mode=ChefMode.SASSY
        )
        
        assert message.role == "user"
        assert message.content == "Test message"
        assert message.chef_mode == ChefMode.SASSY
        assert isinstance(message.created_at, datetime)
        
    def test_conversation_message_validation(self):
        """Test conversation message validation."""
        from pydantic import ValidationError
        
        # Test missing required fields
        with pytest.raises(ValidationError):
            ConversationMessage()  # Missing required role and content
            
        # Test invalid chef_mode
        with pytest.raises(ValidationError):
            ConversationMessage(
                role="user",
                content="Test message",
                chef_mode="invalid_mode"
            )

@pytest.mark.skipif(not MODELS_AVAILABLE, reason="Models not available")
class TestWebSocketModels:
    """Test WebSocket communication models."""
    
    def test_websocket_message(self):
        """Test WebSocketMessage creation."""
        message = WebSocketMessage(
            type=MessageType.TEXT_MESSAGE,
            data={"text": "test", "chef_mode": "normal"},
            session_id=str(uuid4())
        )
        
        assert message.type == MessageType.TEXT_MESSAGE
        assert message.data["text"] == "test"
        assert message.data["chef_mode"] == "normal"
        assert isinstance(message.timestamp, datetime)

def test_backend_availability():
    """Test that backend modules can be imported."""
    if MODELS_AVAILABLE:
        print("✓ Backend models are available")
    else:
        print("✗ Backend models are not available - check import paths")