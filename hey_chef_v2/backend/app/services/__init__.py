"""
Hey Chef v2 Services Module

This module contains all the async services for the Hey Chef application:
- Base service classes for common patterns
- Wake word detection service
- Speech-to-text service  
- Text-to-speech service
- LLM (Large Language Model) service

All services are designed to be:
- Async/await compatible
- Independently testable and mockable
- Resource-managed with proper cleanup
- Error-handled with appropriate logging
- Configurable through the settings system
"""

from .base import BaseService, AudioService
from .wake_word import WakeWordService
from .stt import STTService
from .tts import TTSService
from .llm import LLMService

__all__ = [
    # Base classes
    "BaseService",
    "AudioService",
    
    # Service implementations
    "WakeWordService", 
    "STTService",
    "TTSService",
    "LLMService"
]

# Service factory functions for easy instantiation with default settings
def create_wake_word_service(**kwargs) -> WakeWordService:
    """Create a wake word service with optional overrides."""
    return WakeWordService(**kwargs)

def create_stt_service(**kwargs) -> STTService:
    """Create a speech-to-text service with optional overrides."""
    return STTService(**kwargs)

def create_tts_service(**kwargs) -> TTSService:
    """Create a text-to-speech service with optional overrides."""
    return TTSService(**kwargs)

def create_llm_service(**kwargs) -> LLMService:
    """Create an LLM service with optional overrides."""
    return LLMService(**kwargs)