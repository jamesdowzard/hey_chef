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
    use_external_tts: bool = True


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
    default_log_level: str = "INFO"
    api_log_level: str = "INFO"
    audio_log_level: str = "INFO"
    session_log_level: str = "INFO"
    session_logs_directory: str = "logs/sessions"
    audio_logs_directory: str = "logs/audio"
    api_logs_directory: str = "logs/api"
    archived_logs_directory: str = "logs/archived"
    log_archive_days: int = 30
    max_session_logs: int = 5


@dataclass
class Settings:
    """FastAPI application settings"""
    
    # App settings
    app_name: str = "Hey Chef v2 API"
    environment: str = "development"
    debug: bool = True
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
        self.environment = os.getenv("ENVIRONMENT", self.environment)
        self.debug = os.getenv("DEBUG", str(self.environment == "development")).lower() == "true"
        self.audio.use_external_tts = os.getenv("USE_EXTERNAL_TTS", "true").lower() == "true"
        self.recipe_api_url = os.getenv("RECIPE_API_URL", self.recipe_api_url)
        
        # Parse nested environment variables
        self._parse_nested_env_vars()
        
        # Set default allowed origins
        if self.allowed_origins is None:
            self.allowed_origins = [
                "http://localhost:3000",
                "http://localhost:3001", 
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
                "http://localhost:5173",  # Vite default port
                "http://127.0.0.1:5173"
            ]

    def _parse_nested_env_vars(self):
        """Parse nested environment variables like AUDIO__SAMPLE_RATE"""
        # Audio settings
        if os.getenv("AUDIO__SAMPLE_RATE"):
            self.audio.sample_rate = int(os.getenv("AUDIO__SAMPLE_RATE"))
        if os.getenv("AUDIO__WHISPER_MODEL_SIZE"):
            self.audio.whisper_model_size = os.getenv("AUDIO__WHISPER_MODEL_SIZE")
        if os.getenv("AUDIO__WAKE_WORD_SENSITIVITY"):
            self.audio.wake_word_sensitivity = float(os.getenv("AUDIO__WAKE_WORD_SENSITIVITY"))
            
        # LLM settings
        if os.getenv("LLM__TEMPERATURE"):
            self.llm.temperature = float(os.getenv("LLM__TEMPERATURE"))
        if os.getenv("LLM__MAX_TOKENS"):
            self.llm.max_tokens = int(os.getenv("LLM__MAX_TOKENS"))
        if os.getenv("LLM__MODEL"):
            self.llm.model = os.getenv("LLM__MODEL")
            
        # Logging settings
        if os.getenv("LOGGING__LOG_LEVEL"):
            self.logging.log_level = os.getenv("LOGGING__LOG_LEVEL")
            
    def get_chef_mode_config(self, mode: str) -> dict:
        """Get configuration for a specific chef mode"""
        mode_configs = {
            "normal": {
                "max_tokens": self.llm.max_tokens,
                "temperature": self.llm.temperature
            },
            "sassy": {
                "max_tokens": self.llm.sassy_max_tokens,
                "temperature": self.llm.sassy_temperature
            },
            "gordon_ramsay": {
                "max_tokens": self.llm.gordon_max_tokens,
                "temperature": self.llm.gordon_temperature
            }
        }
        return mode_configs.get(mode, mode_configs["normal"])
        
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"
        
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