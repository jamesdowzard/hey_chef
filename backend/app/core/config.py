"""
Configuration management for Hey Chef v2 backend.
Based on the existing Hey Chef settings structure but adapted for FastAPI.
"""
import os
import yaml
from typing import List, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class AudioSettings:
    """Audio settings for compatibility"""
    sample_rate: int = 16000
    wake_word_sensitivity: float = 0.7
    whisper_model_size: str = "tiny"
    vad_aggressiveness: int = 1
    max_silence_sec: float = 1.0
    macos_voice: str = "Samantha"
    external_voice: str = "alloy"
    speech_rate: int = 219


@dataclass  
class LLMSettings:
    """LLM settings for compatibility"""
    model: str = "gpt-4o"
    available_models: List[str] = None
    max_tokens: int = 150
    temperature: float = 0.2
    sassy_max_tokens: int = 100
    sassy_temperature: float = 0.7
    gordon_max_tokens: int = 180
    gordon_temperature: float = 0.8

    def __post_init__(self):
        if self.available_models is None:
            self.available_models = ["gpt-4o"]


@dataclass
class LoggingSettings:
    """Logging settings for compatibility"""
    logs_directory: str = "logs"
    log_level: str = "INFO"
    max_session_logs: int = 5


@dataclass
class Settings:
    """FastAPI application settings"""
    
    # App settings
    app_name: str = "Hey Chef v2 API"
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    log_level: str = "INFO"
    
    # Security settings
    secret_key: str = "dev-secret-key-change-in-production"
    
    # API settings
    api_v1_prefix: str = "/api/v1"
    allowed_origins: List[str] = None
    
    # External API keys (optional for development)
    openai_api_key: str = ""
    pico_access_key: str = ""
    
    # WebSocket settings
    websocket_heartbeat_interval: int = 30
    websocket_max_connections: int = 100
    
    # Audio settings
    use_external_tts: bool = False
    audio: AudioSettings = None
    llm: LLMSettings = None
    logging: LoggingSettings = None
    
    # Recipe API settings
    recipe_api_url: str = "http://localhost:3333"
    
    # Audio processing settings
    max_recording_duration: int = 30  # Maximum recording duration in seconds
    
    # File paths
    wake_word_model_path: str = "../models/porcupine_models/hey_chef.ppn"
    config_directory: str = "../config"

    def __post_init__(self):
        """Initialize settings from environment variables"""
        # Initialize sub-settings first
        if self.audio is None:
            self.audio = AudioSettings()
        if self.llm is None:
            self.llm = LLMSettings()
            self.llm.__post_init__()
        if self.logging is None:
            self.logging = LoggingSettings()
            
        # Load from environment variables
        self.secret_key = os.getenv("SECRET_KEY", self.secret_key)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.pico_access_key = os.getenv("PICO_ACCESS_KEY", self.pico_access_key)
        self.use_external_tts = os.getenv("USE_EXTERNAL_TTS", "false").lower() == "true"
        self.recipe_api_url = os.getenv("RECIPE_API_URL", self.recipe_api_url)
        
        # Set default allowed origins
        if self.allowed_origins is None:
            self.allowed_origins = [
                "http://localhost:3000",
                "http://localhost:3001", 
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001"
            ]

    def get_wake_word_path(self) -> str:
        """Get absolute path to wake word model"""
        base_path = Path(__file__).parent.parent.parent.parent
        return str(base_path / "models" / "porcupine_models" / "hey_chef.ppn")


# Create global settings instance  
settings = Settings()
settings.__post_init__()

def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings