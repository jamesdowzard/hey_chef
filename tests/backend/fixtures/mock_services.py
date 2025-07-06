"""
Mock service implementations for Hey Chef v2 backend testing.
"""

import asyncio
from typing import AsyncGenerator, Dict, Any, List, Optional
from unittest.mock import AsyncMock, Mock
from backend.app.services.base import BaseService, AudioService
from backend.app.core.models import ChefMode


class MockWakeWordService(AudioService):
    """Mock wake word detection service for testing."""
    
    def __init__(self, should_detect: bool = True, confidence: float = 0.85):
        super().__init__("mock_wake_word")
        self.should_detect = should_detect
        self.confidence = confidence
        self.detection_count = 0
        
    async def start(self) -> None:
        """Start the mock wake word service."""
        self.logger.info("Mock wake word service started")
        
    async def stop(self) -> None:
        """Stop the mock wake word service."""
        self.logger.info("Mock wake word service stopped")
        
    async def detect(self, audio_data: bytes) -> bool:
        """Mock wake word detection."""
        await asyncio.sleep(0.01)  # Simulate processing time
        self.detection_count += 1
        return self.should_detect
        
    async def get_confidence(self) -> float:
        """Get detection confidence."""
        return self.confidence
        
    async def cleanup(self) -> None:
        """Clean up mock resources."""
        pass


class MockSTTService(AudioService):
    """Mock speech-to-text service for testing."""
    
    def __init__(self, transcription: str = "test transcription"):
        super().__init__("mock_stt")
        self.transcription = transcription
        self.transcription_count = 0
        
    async def transcribe(self, audio_data: bytes, language: str = "en") -> str:
        """Mock audio transcription."""
        await asyncio.sleep(0.05)  # Simulate processing time
        self.transcription_count += 1
        
        # Simulate different responses based on audio content
        if b"pasta" in audio_data.lower():
            return "How do I cook pasta?"
        elif b"recipe" in audio_data.lower():
            return "Show me pasta recipes"
        elif b"chef" in audio_data.lower():
            return "Hey chef, help me cook"
        
        return self.transcription
        
    async def get_supported_languages(self) -> List[str]:
        """Get supported languages."""
        return ["en", "es", "fr", "it"]
        
    async def cleanup(self) -> None:
        """Clean up mock resources."""
        pass


class MockTTSService(AudioService):
    """Mock text-to-speech service for testing."""
    
    def __init__(self, use_external: bool = False):
        super().__init__("mock_tts")
        self.use_external = use_external
        self.synthesis_count = 0
        
    async def synthesize(
        self, 
        text: str, 
        voice: Optional[str] = None, 
        speed: float = 1.0
    ) -> bytes:
        """Mock text-to-speech synthesis."""
        await asyncio.sleep(0.1)  # Simulate processing time
        self.synthesis_count += 1
        
        # Return different mock audio based on text content
        if "error" in text.lower():
            raise Exception("Mock TTS error")
            
        # Simulate different voice outputs
        voice_prefix = voice or "default"
        mock_audio = f"mock_audio_{voice_prefix}_{len(text)}_bytes".encode()
        return mock_audio
        
    async def get_available_voices(self) -> List[str]:
        """Get available voices."""
        if self.use_external:
            return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        return ["Samantha", "Alex", "Victoria"]
        
    async def cleanup(self) -> None:
        """Clean up mock resources."""
        pass


class MockLLMService(BaseService):
    """Mock LLM service for testing."""
    
    def __init__(self):
        super().__init__("mock_llm")
        self.responses_by_mode = {
            ChefMode.NORMAL: "Here's how to cook that properly: {question}",
            ChefMode.SASSY: "Oh please, {question}? Even a child could figure that out.",
            ChefMode.GORDON_RAMSAY: "RIGHT! {question}? Listen carefully because I'm only saying this once!"
        }
        self.call_count = 0
        
    async def ask(
        self,
        recipe_text: str,
        question: str,
        history: List[Dict[str, Any]] = None,
        chef_mode: ChefMode = ChefMode.NORMAL
    ) -> str:
        """Mock LLM question answering."""
        await asyncio.sleep(0.1)  # Simulate API call time
        self.call_count += 1
        
        # Simulate error responses
        if "error" in question.lower():
            raise Exception("Mock LLM error")
            
        # Return mode-specific responses
        template = self.responses_by_mode.get(chef_mode, self.responses_by_mode[ChefMode.NORMAL])
        response = template.format(question=question)
        
        # Add recipe context if provided
        if recipe_text and "recipe" in question.lower():
            response += f" Based on the recipe: {recipe_text[:50]}..."
            
        return response
        
    async def ask_streaming(
        self,
        recipe_text: str,
        question: str,
        history: List[Dict[str, Any]] = None,
        chef_mode: ChefMode = ChefMode.NORMAL
    ) -> AsyncGenerator[str, None]:
        """Mock streaming LLM responses."""
        response = await self.ask(recipe_text, question, history, chef_mode)
        
        # Split response into chunks for streaming
        words = response.split()
        for i, word in enumerate(words):
            await asyncio.sleep(0.01)  # Simulate streaming delay
            if i == len(words) - 1:
                yield word
            else:
                yield word + " "
                
    async def cleanup(self) -> None:
        """Clean up mock resources."""
        pass


class MockAudioPipelineManager:
    """Mock audio pipeline manager for integration testing."""
    
    def __init__(self):
        self.wake_word_service = MockWakeWordService()
        self.stt_service = MockSTTService()
        self.tts_service = MockTTSService()
        self.llm_service = MockLLMService()
        self.processing_count = 0
        
    async def process_audio_request(self, request) -> Dict[str, Any]:
        """Mock full audio processing pipeline."""
        await asyncio.sleep(0.2)  # Simulate full pipeline time
        self.processing_count += 1
        
        # Simulate wake word detection
        wake_detected = await self.wake_word_service.detect(request.audio_data)
        if not wake_detected:
            return {
                "success": False,
                "error": "Wake word not detected",
                "wake_word_detected": False
            }
            
        # Simulate STT
        transcription = await self.stt_service.transcribe(request.audio_data)
        
        # Simulate LLM response
        llm_response = await self.llm_service.ask(
            "", transcription, [], request.chef_mode
        )
        
        # Simulate TTS
        audio_response = await self.tts_service.synthesize(llm_response)
        
        return {
            "success": True,
            "transcription": transcription,
            "llm_response": llm_response,
            "audio_response": audio_response,
            "wake_word_detected": True,
            "processing_time": 0.2,
            "chef_mode": request.chef_mode
        }
        
    async def start_pipeline(self) -> None:
        """Start all pipeline services."""
        await self.wake_word_service.start()
        
    async def stop_pipeline(self) -> None:
        """Stop all pipeline services."""
        await self.wake_word_service.stop()
        
    async def cleanup(self) -> None:
        """Clean up all services."""
        await self.wake_word_service.cleanup()
        await self.stt_service.cleanup()
        await self.tts_service.cleanup()
        await self.llm_service.cleanup()


class MockNotionAPI:
    """Mock Notion API for recipe testing."""
    
    def __init__(self):
        self.recipes = [
            {
                "id": "recipe-1",
                "title": "Test Pasta",
                "ingredients": ["pasta", "sauce"],
                "instructions": ["cook pasta", "add sauce"]
            },
            {
                "id": "recipe-2", 
                "title": "Test Soup",
                "ingredients": ["broth", "vegetables"],
                "instructions": ["heat broth", "add vegetables"]
            }
        ]
        
    async def get_recipes(self, limit: int = 10, category: str = None) -> List[Dict[str, Any]]:
        """Mock get recipes."""
        await asyncio.sleep(0.05)
        recipes = self.recipes[:limit]
        if category:
            recipes = [r for r in recipes if category.lower() in r["title"].lower()]
        return recipes
        
    async def get_recipe_by_id(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Mock get recipe by ID."""
        await asyncio.sleep(0.05)
        return next((r for r in self.recipes if r["id"] == recipe_id), None)
        
    async def search_recipes(self, query: str) -> List[Dict[str, Any]]:
        """Mock recipe search."""
        await asyncio.sleep(0.1)
        return [r for r in self.recipes if query.lower() in r["title"].lower()]


# Factory functions for creating mock services
def create_mock_services() -> Dict[str, Any]:
    """Create all mock services for testing."""
    return {
        "wake_word": MockWakeWordService(),
        "stt": MockSTTService(),
        "tts": MockTTSService(),
        "llm": MockLLMService(),
        "pipeline": MockAudioPipelineManager(),
        "notion": MockNotionAPI()
    }


def create_mock_error_services() -> Dict[str, Any]:
    """Create mock services that simulate errors."""
    error_wake_word = MockWakeWordService(should_detect=False)
    error_stt = MockSTTService("error in transcription")
    error_tts = MockTTSService()
    error_llm = MockLLMService()
    
    return {
        "wake_word": error_wake_word,
        "stt": error_stt,
        "tts": error_tts,
        "llm": error_llm
    }