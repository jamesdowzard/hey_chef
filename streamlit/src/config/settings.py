import os
import yaml
from typing import Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AudioSettings:
    """Audio-related settings"""
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
    """LLM-related settings"""
    model: str = "gpt-4o"
    available_models: list = None
    max_tokens: int = 150
    temperature: float = 0.2
    sassy_max_tokens: int = 100  # Shorter responses for sassy mode
    sassy_temperature: float = 0.7  # More creative for sassy mode
    gordon_max_tokens: int = 180  # Longer explosive responses for Gordon mode (1.5x increase)
    gordon_temperature: float = 0.8  # High creativity for explosive personality
    
    def __post_init__(self):
        if self.available_models is None:
            self.available_models = ["gpt-4o"]


@dataclass
class UISettings:
    """UI-related settings"""
    page_title: str = "Hey Chef"
    page_icon: str = "🍳"
    layout: str = "wide"
    default_use_history: bool = True
    default_use_streaming: bool = False
    default_sassy_mode: bool = False


@dataclass
class LoggingSettings:
    """Logging-related settings"""
    master_log_file: str = "hey_chef.log"
    logs_directory: str = "logs"
    session_logs_directory: str = "logs/sessions"
    audio_logs_directory: str = "logs/audio"
    streamlit_logs_directory: str = "logs/streamlit"
    archived_logs_directory: str = "logs/archived"
    max_session_logs: int = 5
    log_archive_days: int = 7
    max_session_buffer_lines: int = 10
    max_error_buffer_lines: int = 20
    max_audio_buffer_lines: int = 15
    max_state_buffer_lines: int = 10
    default_log_level: str = "INFO"
    audio_log_level: str = "DEBUG"
    session_log_level: str = "DEBUG"


class Settings:
    """Central configuration manager for Hey Chef"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.audio = AudioSettings()
        self.llm = LLMSettings()
        self.ui = UISettings()
        self.logging = LoggingSettings()
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML files"""
        config_file = self.config_dir / "config.yaml"
        if config_file.exists():
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
                self._update_from_dict(config_data)
    
    def _update_from_dict(self, config_data: Dict[str, Any]):
        """Update settings from dictionary"""
        if not config_data:
            return
            
        # Update audio settings
        if "audio" in config_data:
            audio_data = config_data["audio"]
            for key, value in audio_data.items():
                if hasattr(self.audio, key):
                    setattr(self.audio, key, value)
        
        # Update LLM settings
        if "llm" in config_data:
            llm_data = config_data["llm"]
            for key, value in llm_data.items():
                if hasattr(self.llm, key):
                    setattr(self.llm, key, value)
        
        # Update UI settings
        if "ui" in config_data:
            ui_data = config_data["ui"]
            for key, value in ui_data.items():
                if hasattr(self.ui, key):
                    setattr(self.ui, key, value)
        
        # Update logging settings
        if "logging" in config_data:
            logging_data = config_data["logging"]
            for key, value in logging_data.items():
                if hasattr(self.logging, key):
                    setattr(self.logging, key, value)
    
    def get_wake_word_path(self) -> str:
        """Get path to wake word model"""
        return str(self.config_dir.parent / "models" / "porcupine_models" / "hey_chef.ppn")
    
    def get_default_recipe_path(self) -> str:
        """Get path to default recipe"""
        return str(self.config_dir / "default_recipe.yaml") 