"""
Unit tests for Hey Chef v2 Pydantic models and schemas.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import ValidationError

from backend.app.core.models import *


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
        assert AudioState.LISTENING == "listening"
        assert AudioState.PROCESSING == "processing"
        
    def test_chef_mode_enum(self):
        """Test ChefMode enum values."""
        assert ChefMode.NORMAL == "normal"
        assert ChefMode.SASSY == "sassy"
        assert ChefMode.GORDON_RAMSAY == "gordon_ramsay"


class TestUserSession:
    """Test UserSession model."""
    
    def test_user_session_creation(self):
        """Test creating a valid user session."""
        session_id = str(uuid4())
        session = UserSession(
            session_id=session_id,
            chef_mode=ChefMode.NORMAL,
            conversation_history=[],
            audio_state=AudioState.IDLE
        )
        
        assert session.session_id == session_id
        assert session.chef_mode == ChefMode.NORMAL
        assert session.conversation_history == []
        assert session.audio_state == AudioState.IDLE
        assert isinstance(session.connected_at, datetime)
        
    def test_user_session_with_history(self):
        """Test user session with conversation history."""
        message = ConversationMessage(
            role="user",
            content="How do I cook pasta?",
            chef_mode=ChefMode.NORMAL
        )
        
        session = UserSession(
            session_id=str(uuid4()),
            conversation_history=[message]
        )
        
        assert len(session.conversation_history) == 1
        assert session.conversation_history[0].content == "How do I cook pasta?"


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
        assert isinstance(message.timestamp, datetime)
        
    def test_conversation_message_validation(self):
        """Test conversation message validation."""
        with pytest.raises(ValidationError):
            ConversationMessage(
                role="",  # Empty role should fail
                content="Test message"
            )


class TestAudioProcessingModels:
    """Test audio processing related models."""
    
    def test_audio_processing_request(self):
        """Test AudioProcessingRequest creation."""
        request = AudioProcessingRequest(
            session_id=str(uuid4()),
            audio_data=b"test audio",
            chef_mode=ChefMode.NORMAL,
            sample_rate=16000,
            format="wav"
        )
        
        assert request.audio_data == b"test audio"
        assert request.chef_mode == ChefMode.NORMAL
        assert request.sample_rate == 16000
        assert request.format == "wav"
        
    def test_audio_processing_response_success(self):
        """Test successful AudioProcessingResponse."""
        response = AudioProcessingResponse(
            success=True,
            text_response="Test response",
            audio_response=b"audio data",
            processing_time=0.15,
            chef_mode=ChefMode.NORMAL
        )
        
        assert response.success is True
        assert response.text_response == "Test response"
        assert response.audio_response == b"audio data"
        assert response.processing_time == 0.15
        assert response.error_message is None
        
    def test_audio_processing_response_error(self):
        """Test error AudioProcessingResponse."""
        response = AudioProcessingResponse(
            success=False,
            text_response=None,
            audio_response=None,
            processing_time=0.05,
            chef_mode=ChefMode.NORMAL,
            error_message="Processing failed"
        )
        
        assert response.success is False
        assert response.text_response is None
        assert response.audio_response is None
        assert response.error_message == "Processing failed"


class TestWakeWordModels:
    """Test wake word detection models."""
    
    def test_wake_word_detection_request(self):
        """Test WakeWordDetectionRequest creation."""
        request = WakeWordDetectionRequest(
            session_id=str(uuid4()),
            audio_data=b"hey chef",
            sample_rate=16000
        )
        
        assert request.audio_data == b"hey chef"
        assert request.sample_rate == 16000
        
    def test_wake_word_detection_response(self):
        """Test WakeWordDetectionResponse creation."""
        response = WakeWordDetectionResponse(
            detected=True,
            confidence=0.85,
            processing_time=0.05
        )
        
        assert response.detected is True
        assert response.confidence == 0.85
        assert response.processing_time == 0.05


class TestTTSModels:
    """Test text-to-speech models."""
    
    def test_tts_request(self):
        """Test TTSRequest creation."""
        request = TTSRequest(
            text="Hello from the chef!",
            chef_mode=ChefMode.GORDON_RAMSAY,
            voice="alloy",
            speed=1.2
        )
        
        assert request.text == "Hello from the chef!"
        assert request.chef_mode == ChefMode.GORDON_RAMSAY
        assert request.voice == "alloy"
        assert request.speed == 1.2
        
    def test_tts_response(self):
        """Test TTSResponse creation."""
        response = TTSResponse(
            audio_data=b"audio bytes",
            format="wav",
            duration=2.5,
            voice_used="alloy"
        )
        
        assert response.audio_data == b"audio bytes"
        assert response.format == "wav"
        assert response.duration == 2.5
        assert response.voice_used == "alloy"


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
        
    def test_status_update_message(self):
        """Test StatusUpdateMessage creation."""
        message = StatusUpdateMessage(
            status="processing",
            message="Processing your request",
            progress=0.5
        )
        
        assert message.status == "processing"
        assert message.message == "Processing your request"
        assert message.progress == 0.5


class TestErrorModels:
    """Test error response models."""
    
    def test_error_response(self):
        """Test ErrorResponse creation."""
        error = ErrorResponse(
            success=False,
            error="Test error message",
            status_code=500,
            details={"component": "llm_service"}
        )
        
        assert error.success is False
        assert error.error == "Test error message"
        assert error.status_code == 500
        assert error.details["component"] == "llm_service"


class TestRecipeModels:
    """Test recipe-related models."""
    
    def test_recipe_search_request(self):
        """Test RecipeSearchRequest creation."""
        request = RecipeSearchRequest(
            query="pasta",
            category="main_course",
            limit=10
        )
        
        assert request.query == "pasta"
        assert request.category == "main_course"
        assert request.limit == 10
        
    def test_recipe_response(self):
        """Test RecipeResponse creation."""
        recipe_data = {
            "id": "123",
            "title": "Test Recipe",
            "ingredients": ["pasta", "sauce"],
            "instructions": ["cook pasta", "add sauce"]
        }
        
        response = RecipeResponse(
            recipes=[recipe_data],
            total=1,
            page=1,
            limit=10
        )
        
        assert len(response.recipes) == 1
        assert response.recipes[0]["title"] == "Test Recipe"
        assert response.total == 1


class TestModelSerialization:
    """Test model serialization and deserialization."""
    
    def test_conversation_message_json(self):
        """Test ConversationMessage JSON serialization."""
        message = ConversationMessage(
            role="assistant",
            content="Here's how to cook pasta",
            chef_mode=ChefMode.NORMAL
        )
        
        json_data = message.model_dump()
        assert json_data["role"] == "assistant"
        assert json_data["content"] == "Here's how to cook pasta"
        assert json_data["chef_mode"] == "normal"
        
        # Test deserialization
        new_message = ConversationMessage(**json_data)
        assert new_message.role == message.role
        assert new_message.content == message.content
        assert new_message.chef_mode == message.chef_mode
        
    def test_audio_processing_request_json(self):
        """Test AudioProcessingRequest JSON handling."""
        request = AudioProcessingRequest(
            session_id=str(uuid4()),
            audio_data=b"test audio",
            chef_mode=ChefMode.SASSY
        )
        
        # Note: Binary data handling may require special serialization
        json_data = request.model_dump(exclude={"audio_data"})
        assert json_data["chef_mode"] == "sassy"


class TestModelValidation:
    """Test model validation rules."""
    
    def test_invalid_chef_mode(self):
        """Test validation with invalid chef mode."""
        with pytest.raises(ValidationError):
            ConversationMessage(
                role="user",
                content="test",
                chef_mode="invalid_mode"  # Should fail validation
            )
            
    def test_invalid_message_type(self):
        """Test validation with invalid message type."""
        with pytest.raises(ValidationError):
            WebSocketMessage(
                type="invalid_type",  # Should fail validation
                data={},
                session_id=str(uuid4())
            )
            
    def test_audio_processing_constraints(self):
        """Test audio processing model constraints."""
        # Test valid sample rate
        request = AudioProcessingRequest(
            session_id=str(uuid4()),
            audio_data=b"test",
            sample_rate=16000
        )
        assert request.sample_rate == 16000
        
        # Test processing time constraints
        response = AudioProcessingResponse(
            success=True,
            processing_time=0.001  # Very fast processing
        )
        assert response.processing_time >= 0