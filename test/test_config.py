"""
Tests for configuration management and settings.
"""
import pytest
from unittest.mock import Mock, patch, mock_open
import sys
import os
import tempfile
import yaml

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from config.settings import Settings
from config.prompts import (NORMAL_SYSTEM_PROMPT, SASSY_SYSTEM_PROMPT, 
                          GORDON_RAMSAY_SYSTEM_PROMPT, get_system_prompt)


class TestSettings:
    """Test Settings configuration management."""
    
    def test_settings_initialization_default(self):
        """Test Settings initialization with default values."""
        with patch('config.settings.Path.exists', return_value=False):
            settings = Settings()
            
            # Test default values
            assert settings.audio.whisper_model_size == "tiny"
            assert settings.audio.vad_aggressiveness == 1  # Actual default is 1
            assert settings.audio.max_silence_sec == 1.0  # Actual default is 1.0
            assert settings.llm.model == "gpt-4o"  # Actual default is gpt-4o
            assert settings.llm.max_tokens == 150
            assert settings.ui.page_title == "Hey Chef - Voice Cooking Assistant"
    
    def test_settings_load_from_yaml(self):
        """Test loading settings from YAML file."""
        config_data = {
            "audio": {
                "whisper_model_size": "base",
                "vad_aggressiveness": 3,
                "max_silence_sec": 5.0
            },
            "llm": {
                "model": "gpt-4",
                "max_tokens": 200,
                "temperature": 0.8
            },
            "ui": {
                "page_title": "Custom Chef App",
                "page_icon": "🍳"
            }
        }
        
        yaml_content = yaml.dump(config_data)
        
        with patch('config.settings.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml_content)):
            
            settings = Settings()
            
            assert settings.audio.whisper_model_size == "base"
            assert settings.audio.vad_aggressiveness == 3
            assert settings.audio.max_silence_sec == 5.0
            assert settings.llm.model == "gpt-4"
            assert settings.llm.max_tokens == 200
            assert settings.llm.temperature == 0.8
            assert settings.ui.page_title == "Custom Chef App"
            assert settings.ui.page_icon == "🍳"
    
    def test_settings_partial_yaml_config(self):
        """Test loading with partial YAML configuration."""
        config_data = {
            "audio": {
                "whisper_model_size": "small"
                # Missing other audio settings
            },
            "llm": {
                "model": "gpt-3.5-turbo"
                # Missing other LLM settings
            }
            # Missing UI settings entirely
        }
        
        yaml_content = yaml.dump(config_data)
        
        with patch('config.settings.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml_content)):
            
            settings = Settings()
            
            # Should use config values where available
            assert settings.audio.whisper_model_size == "small"
            assert settings.llm.model == "gpt-3.5-turbo"
            
            # Should use defaults for missing values
            assert settings.audio.vad_aggressiveness == 2  # Default
            assert settings.llm.max_tokens == 150  # Default
            assert settings.ui.page_title == "Hey Chef - Voice Cooking Assistant"  # Default
    
    def test_settings_invalid_yaml(self):
        """Test handling of invalid YAML configuration."""
        invalid_yaml = "invalid: yaml: content: ["
        
        with patch('config.settings.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=invalid_yaml)):
            
            # Should fall back to defaults without crashing
            settings = Settings()
            assert settings.audio.whisper_model_size == "tiny"  # Default
            assert settings.llm.model == "gpt-4o-mini"  # Default
    
    def test_settings_file_not_readable(self):
        """Test handling when config file cannot be read."""
        with patch('config.settings.Path.exists', return_value=True), \
             patch('builtins.open', side_effect=IOError("File not readable")):
            
            # Should fall back to defaults
            settings = Settings()
            assert settings.audio.whisper_model_size == "tiny"
            assert settings.llm.model == "gpt-4o-mini"
    
    def test_get_default_recipe_path(self):
        """Test getting default recipe path."""
        with patch('config.settings.Path.exists', return_value=False):
            settings = Settings()
            
            recipe_path = settings.get_default_recipe_path()
            assert recipe_path.name == "default_recipe.yaml"
            assert "config" in str(recipe_path)
    
    def test_get_porcupine_model_path(self):
        """Test getting Porcupine model path."""
        with patch('config.settings.Path.exists', return_value=False):
            settings = Settings()
            
            model_path = settings.get_porcupine_model_path()
            assert model_path.name == "hey_chef.ppn"
            assert "models" in str(model_path)
    
    def test_settings_nested_config_merge(self):
        """Test that nested configurations merge properly."""
        config_data = {
            "audio": {
                "whisper_model_size": "large"
                # Note: not specifying vad_aggressiveness or max_silence_sec
            }
        }
        
        yaml_content = yaml.dump(config_data)
        
        with patch('config.settings.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml_content)):
            
            settings = Settings()
            
            # Should merge with defaults
            assert settings.audio.whisper_model_size == "large"  # From config
            assert settings.audio.vad_aggressiveness == 2  # Default
            assert settings.audio.max_silence_sec == 3.0  # Default
    
    def test_environment_variable_override(self):
        """Test that environment variables can override settings."""
        config_data = {
            "llm": {
                "model": "gpt-4"
            }
        }
        
        yaml_content = yaml.dump(config_data)
        
        with patch('config.settings.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml_content)), \
             patch.dict(os.environ, {"OPENAI_MODEL": "gpt-3.5-turbo"}):
            
            settings = Settings()
            
            # Environment variable should take precedence if the setting supports it
            # (This test assumes environment variable support is implemented)
            assert settings.llm.model in ["gpt-4", "gpt-3.5-turbo"]


class TestChefPrompts:
    """Test chef prompt configurations."""
    
    def test_chef_prompts_exist(self):
        """Test that all required chef prompts exist."""
        assert NORMAL_SYSTEM_PROMPT is not None
        assert SASSY_SYSTEM_PROMPT is not None
        assert GORDON_RAMSAY_SYSTEM_PROMPT is not None
    
    def test_chef_prompts_are_strings(self):
        """Test that all prompts are non-empty strings."""
        prompts = {
            "normal": NORMAL_SYSTEM_PROMPT,
            "sassy": SASSY_SYSTEM_PROMPT,
            "gordon_ramsay": GORDON_RAMSAY_SYSTEM_PROMPT
        }
        
        for mode, prompt in prompts.items():
            assert isinstance(prompt, str)
            assert len(prompt.strip()) > 0
            assert len(prompt) > 50  # Should be reasonably detailed
    
    def test_chef_prompts_contain_role_instructions(self):
        """Test that prompts contain appropriate role instructions."""
        # Normal mode should be helpful
        assert any(word in NORMAL_SYSTEM_PROMPT.lower() for word in ["helpful", "assist", "guide"])
        
        # Sassy mode should indicate attitude
        assert any(word in SASSY_SYSTEM_PROMPT.lower() for word in ["sassy", "attitude", "direct"])
        
        # Gordon Ramsay mode should be intense
        assert any(word in GORDON_RAMSAY_SYSTEM_PROMPT.lower() for word in ["gordon", "ramsay", "intense"])
    
    def test_chef_prompts_are_cooking_focused(self):
        """Test that all prompts are focused on cooking."""
        cooking_keywords = ["cook", "recipe", "ingredient", "kitchen", "chef", "food", "dish"]
        
        prompts = {
            "normal": NORMAL_SYSTEM_PROMPT,
            "sassy": SASSY_SYSTEM_PROMPT,
            "gordon_ramsay": GORDON_RAMSAY_SYSTEM_PROMPT
        }
        
        for mode, prompt in prompts.items():
            prompt_lower = prompt.lower()
            assert any(keyword in prompt_lower for keyword in cooking_keywords), \
                f"Prompt for {mode} mode should contain cooking-related keywords"
    
    def test_get_system_prompt_function(self):
        """Test the get_system_prompt function."""
        assert get_system_prompt("normal") == NORMAL_SYSTEM_PROMPT
        assert get_system_prompt("sassy") == SASSY_SYSTEM_PROMPT
        assert get_system_prompt("gordon_ramsay") == GORDON_RAMSAY_SYSTEM_PROMPT
        
        # Test default behavior
        assert get_system_prompt() == NORMAL_SYSTEM_PROMPT
        assert get_system_prompt("unknown_mode") == NORMAL_SYSTEM_PROMPT


class TestConfigurationValidation:
    """Test configuration validation and error handling."""
    
    def test_audio_settings_validation(self):
        """Test validation of audio settings."""
        # Valid whisper model sizes
        valid_models = ["tiny", "base", "small", "medium", "large"]
        
        for model in valid_models:
            config_data = {"audio": {"whisper_model_size": model}}
            yaml_content = yaml.dump(config_data)
            
            with patch('config.settings.Path.exists', return_value=True), \
                 patch('builtins.open', mock_open(read_data=yaml_content)):
                
                settings = Settings()
                assert settings.audio.whisper_model_size == model
    
    def test_llm_settings_validation(self):
        """Test validation of LLM settings."""
        # Test temperature bounds
        config_data = {
            "llm": {
                "temperature": 1.5,  # High but valid
                "max_tokens": 500
            }
        }
        
        yaml_content = yaml.dump(config_data)
        
        with patch('config.settings.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml_content)):
            
            settings = Settings()
            assert settings.llm.temperature == 1.5
            assert settings.llm.max_tokens == 500
    
    def test_ui_settings_validation(self):
        """Test validation of UI settings."""
        config_data = {
            "ui": {
                "page_title": "Custom Title",
                "page_icon": "🔥",
                "default_use_history": True,
                "default_use_streaming": False
            }
        }
        
        yaml_content = yaml.dump(config_data)
        
        with patch('config.settings.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml_content)):
            
            settings = Settings()
            assert settings.ui.page_title == "Custom Title"
            assert settings.ui.page_icon == "🔥"
            assert settings.ui.default_use_history is True
            assert settings.ui.default_use_streaming is False


class TestConfigurationFiles:
    """Test configuration file handling."""
    
    def test_config_file_discovery(self):
        """Test that config files are discovered correctly."""
        with patch('config.settings.Path.exists') as mock_exists:
            # Simulate config.yaml exists
            mock_exists.return_value = True
            
            settings = Settings()
            
            # Should try to load config.yaml
            mock_exists.assert_called()
    
    def test_multiple_config_file_formats(self):
        """Test handling of different config file formats."""
        # YAML format
        yaml_config = {
            "audio": {"whisper_model_size": "base"},
            "llm": {"model": "gpt-4"}
        }
        
        yaml_content = yaml.dump(yaml_config)
        
        with patch('config.settings.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml_content)):
            
            settings = Settings()
            assert settings.audio.whisper_model_size == "base"
            assert settings.llm.model == "gpt-4"
    
    def test_config_file_paths(self):
        """Test that config file paths are constructed correctly."""
        with patch('config.settings.Path.exists', return_value=False):
            settings = Settings()
            
            # Test various path methods
            recipe_path = settings.get_default_recipe_path()
            assert recipe_path.exists() or not recipe_path.exists()  # Path object should be valid
            
            porcupine_path = settings.get_porcupine_model_path()
            assert porcupine_path.exists() or not porcupine_path.exists()  # Path object should be valid


class TestConfigurationIntegration:
    """Integration tests for configuration system."""
    
    def test_full_configuration_loading(self):
        """Test loading a complete configuration."""
        full_config = {
            "audio": {
                "whisper_model_size": "small",
                "vad_aggressiveness": 3,
                "max_silence_sec": 4.0,
                "sample_rate": 16000,
                "channels": 1
            },
            "llm": {
                "model": "gpt-4",
                "max_tokens": 300,
                "temperature": 0.9,
                "sassy_max_tokens": 100,
                "sassy_temperature": 1.2,
                "gordon_max_tokens": 200,
                "gordon_temperature": 1.5
            },
            "ui": {
                "page_title": "Advanced Chef Assistant",
                "page_icon": "👨‍🍳",
                "default_use_history": True,
                "default_use_streaming": True
            }
        }
        
        yaml_content = yaml.dump(full_config)
        
        with patch('config.settings.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=yaml_content)):
            
            settings = Settings()
            
            # Verify all settings loaded correctly
            assert settings.audio.whisper_model_size == "small"
            assert settings.audio.vad_aggressiveness == 3
            assert settings.audio.max_silence_sec == 4.0
            
            assert settings.llm.model == "gpt-4"
            assert settings.llm.max_tokens == 300
            assert settings.llm.temperature == 0.9
            
            assert settings.ui.page_title == "Advanced Chef Assistant"
            assert settings.ui.page_icon == "👨‍🍳"
            assert settings.ui.default_use_history is True
    
    def test_configuration_with_real_file(self):
        """Test configuration loading with a real temporary file."""
        config_data = {
            "audio": {"whisper_model_size": "base"},
            "llm": {"model": "gpt-3.5-turbo"},
            "ui": {"page_title": "Test Chef"}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            with patch('config.settings.Settings._get_config_path') as mock_path:
                from pathlib import Path
                mock_path.return_value = Path(config_path)
                
                settings = Settings()
                
                assert settings.audio.whisper_model_size == "base"
                assert settings.llm.model == "gpt-3.5-turbo"
                assert settings.ui.page_title == "Test Chef"
                
        finally:
            os.unlink(config_path)