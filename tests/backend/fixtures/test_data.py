"""
Test data factories for Hey Chef v2 backend testing.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from backend.app.core.models import *


class TestDataFactory:
    """Factory for generating test data."""
    
    @staticmethod
    def create_user_session(session_id: str = None) -> UserSession:
        """Create a test user session."""
        return UserSession(
            session_id=session_id or str(uuid.uuid4()),
            connected_at=datetime.now(timezone.utc),
            chef_mode=ChefMode.NORMAL,
            conversation_history=[],
            recipe_context=None,
            audio_state=AudioState.IDLE
        )
    
    @staticmethod
    def create_conversation_message(
        role: str = "user",
        content: str = "Test message",
        chef_mode: ChefMode = ChefMode.NORMAL
    ) -> ConversationMessage:
        """Create a test conversation message."""
        return ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now(timezone.utc),
            chef_mode=chef_mode
        )
    
    @staticmethod
    def create_audio_processing_request(
        audio_data: bytes = b"test audio",
        chef_mode: ChefMode = ChefMode.NORMAL
    ) -> AudioProcessingRequest:
        """Create a test audio processing request."""
        return AudioProcessingRequest(
            session_id=str(uuid.uuid4()),
            audio_data=audio_data,
            chef_mode=chef_mode,
            sample_rate=16000,
            format="wav"
        )
    
    @staticmethod
    def create_audio_processing_response(
        success: bool = True,
        text_response: str = "Test chef response"
    ) -> AudioProcessingResponse:
        """Create a test audio processing response."""
        return AudioProcessingResponse(
            success=success,
            text_response=text_response,
            audio_response=b"test audio response" if success else None,
            processing_time=0.15,
            chef_mode=ChefMode.NORMAL,
            error_message=None if success else "Test error"
        )
    
    @staticmethod
    def create_wake_word_detection_request(
        audio_data: bytes = b"hey chef test"
    ) -> WakeWordDetectionRequest:
        """Create a test wake word detection request."""
        return WakeWordDetectionRequest(
            session_id=str(uuid.uuid4()),
            audio_data=audio_data,
            sample_rate=16000
        )
    
    @staticmethod
    def create_wake_word_detection_response(
        detected: bool = True,
        confidence: float = 0.85
    ) -> WakeWordDetectionResponse:
        """Create a test wake word detection response."""
        return WakeWordDetectionResponse(
            detected=detected,
            confidence=confidence,
            processing_time=0.05
        )
    
    @staticmethod
    def create_tts_request(
        text: str = "Hello from the chef!",
        chef_mode: ChefMode = ChefMode.NORMAL
    ) -> TTSRequest:
        """Create a test TTS request."""
        return TTSRequest(
            text=text,
            chef_mode=chef_mode,
            voice="alloy",
            speed=1.0
        )
    
    @staticmethod
    def create_tts_response(
        audio_data: bytes = b"test tts audio"
    ) -> TTSResponse:
        """Create a test TTS response."""
        return TTSResponse(
            audio_data=audio_data,
            format="wav",
            duration=2.5,
            voice_used="alloy"
        )
    
    @staticmethod
    def create_websocket_message(
        message_type: MessageType = MessageType.TEXT_MESSAGE,
        data: Dict[str, Any] = None
    ) -> WebSocketMessage:
        """Create a test WebSocket message."""
        if data is None:
            data = {"text": "test message", "chef_mode": "normal"}
        
        return WebSocketMessage(
            type=message_type,
            data=data,
            session_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc)
        )
    
    @staticmethod
    def create_recipe_data() -> Dict[str, Any]:
        """Create test recipe data."""
        return {
            "id": str(uuid.uuid4()),
            "title": "Test Pasta Recipe",
            "description": "A simple test pasta recipe",
            "ingredients": [
                "1 lb pasta",
                "2 tbsp olive oil",
                "3 cloves garlic",
                "Salt to taste"
            ],
            "instructions": [
                "Boil water and cook pasta",
                "Heat olive oil in pan",
                "Add garlic and cook until fragrant",
                "Toss pasta with oil and garlic",
                "Season with salt"
            ],
            "prep_time": 10,
            "cook_time": 15,
            "total_time": 25,
            "servings": 4,
            "difficulty": "easy",
            "category": "pasta",
            "cuisine": "italian",
            "tags": ["quick", "easy", "vegetarian"]
        }
    
    @staticmethod
    def create_error_response(
        status_code: int = 500,
        error_message: str = "Test error"
    ) -> ErrorResponse:
        """Create a test error response."""
        return ErrorResponse(
            success=False,
            error=error_message,
            status_code=status_code,
            details={"test": True}
        )
    
    @staticmethod
    def create_multiple_recipes(count: int = 5) -> List[Dict[str, Any]]:
        """Create multiple test recipes."""
        recipes = []
        categories = ["pasta", "soup", "salad", "dessert", "main"]
        
        for i in range(count):
            recipe = TestDataFactory.create_recipe_data()
            recipe["title"] = f"Test Recipe {i+1}"
            recipe["category"] = categories[i % len(categories)]
            recipes.append(recipe)
        
        return recipes
    
    @staticmethod
    def create_chef_mode_responses() -> Dict[ChefMode, str]:
        """Create responses for different chef modes."""
        return {
            ChefMode.NORMAL: "Here's how to cook pasta properly. Boil salted water, add pasta, and cook until al dente.",
            ChefMode.SASSY: "Oh, pasta? Really? Fine, boil water, toss in pasta, don't overcook it. Even you can manage that.",
            ChefMode.GORDON_RAMSAY: "RIGHT! Listen up! Pasta needs BOILING water, not lukewarm! Get that water ROLLING and cook it properly!"
        }
    
    @staticmethod
    def create_audio_test_samples() -> Dict[str, bytes]:
        """Create different audio test samples."""
        return {
            "wake_word": b"hey chef wake word audio sample",
            "cooking_question": b"how do I cook pasta audio sample",
            "recipe_request": b"show me pasta recipes audio sample",
            "invalid_audio": b"not valid audio data",
            "empty_audio": b"",
            "large_audio": b"x" * 10000  # Large audio sample
        }


# Convenience functions for common test scenarios
def get_test_session() -> UserSession:
    """Get a standard test session."""
    return TestDataFactory.create_user_session()


def get_test_audio_request() -> AudioProcessingRequest:
    """Get a standard test audio request."""
    return TestDataFactory.create_audio_processing_request()


def get_test_recipe() -> Dict[str, Any]:
    """Get a standard test recipe."""
    return TestDataFactory.create_recipe_data()


def get_chef_mode_test_data() -> List[tuple]:
    """Get test data for all chef modes."""
    return [
        (ChefMode.NORMAL, "normal cooking question"),
        (ChefMode.SASSY, "sassy cooking question"),
        (ChefMode.GORDON_RAMSAY, "gordon ramsay cooking question")
    ]