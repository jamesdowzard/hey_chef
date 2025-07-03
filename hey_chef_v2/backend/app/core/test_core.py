"""
Simple tests for core configuration and models.
Run with: python -m pytest app/core/test_core.py -v
"""
import os
import pytest
import tempfile
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

from .config import Settings
from .models import (
    AudioState, ChefMode, MessageType, AudioPipelineState,
    UserSession, SessionSettings, Recipe, Ingredient, RecipeStep,
    AudioProcessingRequest, WakeWordDetectionRequest, TTSRequest
)
from .audio_pipeline import AudioPipelineManager
from .logger import setup_logging, get_logger


class TestSettings:
    """Test Settings configuration"""
    
    def test_default_settings(self):
        """Test default settings creation"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key',
            'OPENAI_API_KEY': 'test-openai-key', 
            'PICO_ACCESS_KEY': 'test-pico-key'
        }):
            settings = Settings()
            
            assert settings.app_name == "Hey Chef v2 API"
            assert settings.environment == "development"
            assert settings.debug is True
            assert settings.audio.sample_rate == 16000
            assert settings.llm.model == "gpt-4o"
            assert settings.llm.temperature == 0.2
    
    def test_environment_overrides(self):
        """Test environment variable overrides"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key',
            'OPENAI_API_KEY': 'test-openai-key',
            'PICO_ACCESS_KEY': 'test-pico-key',
            'ENVIRONMENT': 'production',
            'DEBUG': 'false',
            'AUDIO__SAMPLE_RATE': '48000',
            'LLM__TEMPERATURE': '0.5'
        }):
            settings = Settings()
            
            assert settings.environment == "production"
            assert settings.debug is False
            assert settings.audio.sample_rate == 48000
            assert settings.llm.temperature == 0.5
    
    def test_chef_mode_config(self):
        """Test chef mode configuration"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key',
            'OPENAI_API_KEY': 'test-openai-key',
            'PICO_ACCESS_KEY': 'test-pico-key'
        }):
            settings = Settings()
            
            normal_config = settings.get_chef_mode_config("normal")
            assert normal_config["max_tokens"] == 150
            assert normal_config["temperature"] == 0.2
            
            sassy_config = settings.get_chef_mode_config("sassy")
            assert sassy_config["max_tokens"] == 100
            assert sassy_config["temperature"] == 0.7
            
            gordon_config = settings.get_chef_mode_config("gordon_ramsay")
            assert gordon_config["max_tokens"] == 180
            assert gordon_config["temperature"] == 0.8


class TestModels:
    """Test Pydantic models"""
    
    def test_audio_pipeline_state(self):
        """Test AudioPipelineState model"""
        session_id = uuid4()
        state = AudioPipelineState(session_id=session_id)
        
        assert state.current_state == AudioState.IDLE
        assert not state.is_processing
        assert state.wake_word_active
        
        # Test state transition
        state.transition_to(AudioState.TRANSCRIBING, "testing")
        assert state.current_state == AudioState.TRANSCRIBING
        assert state.is_processing
        assert state.current_operation == "testing"
    
    def test_user_session(self):
        """Test UserSession model"""
        session = UserSession()
        
        assert session.is_active
        assert session.settings.chef_mode == ChefMode.NORMAL
        assert session.audio_state == AudioState.IDLE
        assert len(session.conversation_history) == 0
    
    def test_recipe_model(self):
        """Test Recipe model"""
        recipe = Recipe(
            title="Test Recipe",
            description="A test recipe",
            ingredients=[
                Ingredient(name="flour", amount="2", unit="cups"),
                Ingredient(name="sugar", amount="1", unit="cup")
            ],
            steps=[
                RecipeStep(step_number=1, instruction="Mix ingredients"),
                RecipeStep(step_number=2, instruction="Bake for 30 minutes")
            ]
        )
        
        assert recipe.title == "Test Recipe"
        assert len(recipe.ingredients) == 2
        assert len(recipe.steps) == 2
        assert recipe.ingredients[0].name == "flour"
        assert recipe.steps[0].step_number == 1
    
    def test_audio_processing_request(self):
        """Test AudioProcessingRequest validation"""
        session_id = uuid4()
        audio_data = b"fake audio data"
        
        request = AudioProcessingRequest(
            session_id=session_id,
            audio_data=audio_data,
            sample_rate=16000
        )
        
        assert request.session_id == session_id
        assert request.audio_data == audio_data
        assert request.sample_rate == 16000
        assert request.max_duration == 30
    
    def test_wake_word_detection_request(self):
        """Test WakeWordDetectionRequest validation"""
        audio_data = b"fake audio data"
        
        request = WakeWordDetectionRequest(
            audio_data=audio_data,
            sensitivity=0.8
        )
        
        assert request.audio_data == audio_data
        assert request.sensitivity == 0.8
        
        # Test validation bounds
        with pytest.raises(ValueError):
            WakeWordDetectionRequest(
                audio_data=audio_data,
                sensitivity=1.5  # Invalid: > 1.0
            )
    
    def test_tts_request(self):
        """Test TTSRequest validation"""
        request = TTSRequest(
            text="Hello, world!",
            speed=1.5,
            pitch=0.8
        )
        
        assert request.text == "Hello, world!"
        assert request.speed == 1.5
        assert request.pitch == 0.8
        
        # Test validation bounds
        with pytest.raises(ValueError):
            TTSRequest(
                text="Hello",
                speed=5.0  # Invalid: > 4.0
            )


class TestAudioPipeline:
    """Test AudioPipelineManager"""
    
    @pytest.fixture
    def settings(self):
        """Create test settings"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key',
            'OPENAI_API_KEY': 'test-openai-key',
            'PICO_ACCESS_KEY': 'test-pico-key'
        }):
            return Settings()
    
    @pytest.fixture
    def pipeline_manager(self, settings):
        """Create test pipeline manager"""
        return AudioPipelineManager(settings)
    
    @pytest.mark.asyncio
    async def test_create_session_pipeline(self, pipeline_manager):
        """Test session pipeline creation"""
        session_id = uuid4()
        
        pipeline_state = await pipeline_manager.create_session_pipeline(session_id)
        
        assert pipeline_state.session_id == session_id
        assert pipeline_state.current_state == AudioState.IDLE
        assert session_id in pipeline_manager.session_states
        assert session_id in pipeline_manager.session_locks
    
    @pytest.mark.asyncio
    async def test_state_transition(self, pipeline_manager):
        """Test state transitions"""
        session_id = uuid4()
        await pipeline_manager.create_session_pipeline(session_id)
        
        await pipeline_manager.transition_state(
            session_id, 
            AudioState.LISTENING_WAKE_WORD, 
            "test_transition"
        )
        
        state = await pipeline_manager.get_pipeline_state(session_id)
        assert state.current_state == AudioState.LISTENING_WAKE_WORD
        assert state.current_operation == "test_transition"
    
    @pytest.mark.asyncio
    async def test_destroy_session_pipeline(self, pipeline_manager):
        """Test session pipeline cleanup"""
        session_id = uuid4()
        await pipeline_manager.create_session_pipeline(session_id)
        
        assert session_id in pipeline_manager.session_states
        
        await pipeline_manager.destroy_session_pipeline(session_id)
        
        assert session_id not in pipeline_manager.session_states
        assert session_id not in pipeline_manager.session_locks
    
    @pytest.mark.asyncio 
    async def test_pipeline_metrics(self, pipeline_manager):
        """Test pipeline metrics"""
        session_id1 = uuid4()
        session_id2 = uuid4()
        
        await pipeline_manager.create_session_pipeline(session_id1)
        await pipeline_manager.create_session_pipeline(session_id2)
        
        metrics = await pipeline_manager.get_pipeline_metrics()
        
        assert metrics["total_sessions"] == 2
        assert metrics["current_sessions"] == 2
        assert len(metrics["session_details"]) == 2


class TestLogging:
    """Test logging functionality"""
    
    def test_logger_setup(self):
        """Test logger setup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {
                'SECRET_KEY': 'test-secret-key',
                'OPENAI_API_KEY': 'test-openai-key',
                'PICO_ACCESS_KEY': 'test-pico-key'
            }):
                settings = Settings()
                settings.logging.logs_directory = temp_dir
                
                logger_manager = setup_logging(settings)
                logger = logger_manager.get_logger("test_logger")
                
                assert logger.name == "test_logger"
                assert len(logger.handlers) > 0
    
    def test_specialized_loggers(self):
        """Test specialized logger creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {
                'SECRET_KEY': 'test-secret-key',
                'OPENAI_API_KEY': 'test-openai-key',
                'PICO_ACCESS_KEY': 'test-pico-key'
            }):
                settings = Settings()
                settings.logging.logs_directory = temp_dir
                settings.logging.session_logs_directory = f"{temp_dir}/sessions"
                
                logger_manager = setup_logging(settings)
                
                api_logger = logger_manager.get_api_logger()
                audio_logger = logger_manager.get_audio_logger()
                session_logger = logger_manager.get_session_logger("test-session-123")
                
                assert api_logger.name == "hey_chef_api"
                assert audio_logger.name == "hey_chef_audio"
                assert session_logger.name == "session_test-ses"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])