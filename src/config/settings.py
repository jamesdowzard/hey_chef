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
    max_tokens: int = 150
    temperature: float = 0.2
    sassy_max_tokens: int = 100  # Shorter responses for sassy mode
    sassy_temperature: float = 0.7  # More creative for sassy mode


@dataclass
class UISettings:
    """UI-related settings"""
    page_title: str = "Hey Chef"
    page_icon: str = "🍳"
    layout: str = "centered"
    default_use_history: bool = True
    default_use_streaming: bool = False
    default_sassy_mode: bool = False


class Settings:
    """Central configuration manager for Hey Chef"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.audio = AudioSettings()
        self.llm = LLMSettings()
        self.ui = UISettings()
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
    
    def get_wake_word_path(self) -> str:
        """Get path to wake word model"""
        return str(self.config_dir.parent / "models" / "porcupine_models" / "hey_chef.ppn")
    
    def get_default_recipe_path(self) -> str:
        """Get path to default recipe"""
        return str(self.config_dir / "default_recipe.yaml") 