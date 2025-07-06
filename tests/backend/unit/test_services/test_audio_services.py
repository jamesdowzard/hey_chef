"""
Unit tests for Hey Chef v2 audio services.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import List

from backend.app.services.wake_word import WakeWordService
from backend.app.services.stt import STTService
from backend.app.services.tts import TTSService
from backend.app.core.models import ChefMode
from tests.backend.fixtures.test_data import TestDataFactory
from tests.backend.fixtures.mock_services import MockWakeWordService, MockSTTService, MockTTSService


class TestWakeWordService:
    """Test wake word detection service."""
    
    @pytest.fixture
    def wake_word_service(self):
        """Create wake word service for testing."""
        return WakeWordService()
    
    @pytest.fixture
    def mock_wake_word_service(self):
        """Create mock wake word service for testing."""
        return MockWakeWordService()
    
    def test_wake_word_service_initialization(self, wake_word_service):
        """Test wake word service initializes correctly."""
        assert wake_word_service.service_name == "wake_word"
        assert wake_word_service.porcupine is None  # Lazy initialization
        assert wake_word_service.keywords == ["hey chef"]
    
    @pytest.mark.asyncio
    async def test_mock_wake_word_detection_success(self, mock_wake_word_service):
        """Test successful wake word detection."""
        audio_data = b"hey chef test audio"
        
        detected = await mock_wake_word_service.detect(audio_data)
        assert detected is True
        assert mock_wake_word_service.detection_count == 1
        
        confidence = await mock_wake_word_service.get_confidence()
        assert confidence == 0.85
    
    @pytest.mark.asyncio
    async def test_mock_wake_word_detection_failure(self):
        """Test wake word detection failure."""
        mock_service = MockWakeWordService(should_detect=False)
        
        audio_data = b"not wake word audio"
        detected = await mock_service.detect(audio_data)
        assert detected is False
    
    @pytest.mark.asyncio
    async def test_wake_word_service_lifecycle(self, mock_wake_word_service):
        """Test wake word service lifecycle."""
        # Test start
        await mock_wake_word_service.start()
        
        # Test detection
        detected = await mock_wake_word_service.detect(b"test audio")
        assert isinstance(detected, bool)
        
        # Test stop
        await mock_wake_word_service.stop()
        
        # Test cleanup
        await mock_wake_word_service.cleanup()
    
    @pytest.mark.asyncio
    async def test_wake_word_performance_metrics(self, mock_wake_word_service):
        """Test wake word detection performance."""
        # Test multiple detections
        audio_samples = [
            b"hey chef sample 1",
            b"hey chef sample 2", 
            b"hey chef sample 3"
        ]
        
        results = []
        for audio in audio_samples:
            result = await mock_wake_word_service.detect(audio)
            results.append(result)
        
        assert len(results) == 3
        assert mock_wake_word_service.detection_count == 3
        
        # All should be detected (mock is configured to detect)
        assert all(results)


class TestSTTService:
    """Test speech-to-text service."""
    
    @pytest.fixture
    def stt_service(self):
        """Create STT service for testing."""
        return STTService()
    
    @pytest.fixture
    def mock_stt_service(self):
        """Create mock STT service for testing."""
        return MockSTTService()
    
    def test_stt_service_initialization(self, stt_service):
        """Test STT service initializes correctly."""
        assert stt_service.service_name == "stt"
        assert stt_service.model is None  # Lazy initialization
        assert stt_service.model_size == "base"
    
    @pytest.mark.asyncio
    async def test_mock_stt_transcription_basic(self, mock_stt_service):
        """Test basic STT transcription."""
        audio_data = b"test audio for transcription"
        
        transcription = await mock_stt_service.transcribe(audio_data)
        assert transcription == "test transcription"
        assert mock_stt_service.transcription_count == 1
    
    @pytest.mark.asyncio
    async def test_mock_stt_transcription_context_aware(self, mock_stt_service):
        """Test context-aware STT transcription."""
        # Test pasta context
        pasta_audio = b"pasta cooking question"
        pasta_transcription = await mock_stt_service.transcribe(pasta_audio)
        assert "pasta" in pasta_transcription.lower()
        
        # Test recipe context
        recipe_audio = b"recipe search request"
        recipe_transcription = await mock_stt_service.transcribe(recipe_audio)
        assert "recipe" in recipe_transcription.lower()
        
        # Test chef context
        chef_audio = b"chef cooking help"
        chef_transcription = await mock_stt_service.transcribe(chef_audio)
        assert "chef" in chef_transcription.lower()
    
    @pytest.mark.asyncio
    async def test_stt_supported_languages(self, mock_stt_service):
        """Test STT supported languages."""
        languages = await mock_stt_service.get_supported_languages()
        assert isinstance(languages, list)
        assert "en" in languages
        assert len(languages) > 0
    
    @pytest.mark.asyncio
    async def test_stt_transcription_with_language(self, mock_stt_service):
        """Test STT transcription with specific language."""
        audio_data = b"test audio"
        
        # Test with different languages
        for lang in ["en", "es", "fr"]:
            transcription = await mock_stt_service.transcribe(audio_data, language=lang)
            assert isinstance(transcription, str)
            assert len(transcription) > 0
    
    @pytest.mark.asyncio
    async def test_stt_cleanup(self, mock_stt_service):
        """Test STT service cleanup."""
        await mock_stt_service.cleanup()
        # Cleanup should not raise any errors


class TestTTSService:
    """Test text-to-speech service."""
    
    @pytest.fixture
    def tts_service(self):
        """Create TTS service for testing."""
        return TTSService()
    
    @pytest.fixture
    def mock_tts_service(self):
        """Create mock TTS service for testing."""
        return MockTTSService()
    
    @pytest.fixture
    def mock_external_tts_service(self):
        """Create mock external TTS service for testing."""
        return MockTTSService(use_external=True)
    
    def test_tts_service_initialization(self, tts_service):
        """Test TTS service initializes correctly."""
        assert tts_service.service_name == "tts"
        assert tts_service.openai_client is None  # Lazy initialization
    
    @pytest.mark.asyncio
    async def test_mock_tts_synthesis_basic(self, mock_tts_service):
        """Test basic TTS synthesis."""
        text = "Hello from the chef!"
        
        audio_data = await mock_tts_service.synthesize(text)
        assert isinstance(audio_data, bytes)
        assert len(audio_data) > 0
        assert mock_tts_service.synthesis_count == 1
    
    @pytest.mark.asyncio
    async def test_mock_tts_synthesis_with_voice(self, mock_tts_service):
        """Test TTS synthesis with specific voice."""
        text = "Test voice synthesis"
        voice = "alloy"
        
        audio_data = await mock_tts_service.synthesize(text, voice=voice)
        assert isinstance(audio_data, bytes)
        assert voice.encode() in audio_data  # Mock includes voice in response
    
    @pytest.mark.asyncio
    async def test_mock_tts_synthesis_with_speed(self, mock_tts_service):
        """Test TTS synthesis with different speeds."""
        text = "Test speed synthesis"
        
        # Test different speeds
        for speed in [0.5, 1.0, 1.5, 2.0]:
            audio_data = await mock_tts_service.synthesize(text, speed=speed)
            assert isinstance(audio_data, bytes)
            assert len(audio_data) > 0
    
    @pytest.mark.asyncio
    async def test_tts_available_voices_internal(self, mock_tts_service):
        """Test getting available voices for internal TTS."""
        voices = await mock_tts_service.get_available_voices()
        assert isinstance(voices, list)
        assert "Samantha" in voices or "Alex" in voices
    
    @pytest.mark.asyncio
    async def test_tts_available_voices_external(self, mock_external_tts_service):
        """Test getting available voices for external TTS."""
        voices = await mock_external_tts_service.get_available_voices()
        assert isinstance(voices, list)
        assert "alloy" in voices
        assert "echo" in voices
    
    @pytest.mark.asyncio
    async def test_tts_error_handling(self, mock_tts_service):
        """Test TTS error handling."""
        # Text that should cause an error
        error_text = "This should cause an error"
        
        with pytest.raises(Exception, match="Mock TTS error"):
            await mock_tts_service.synthesize(error_text)
    
    @pytest.mark.asyncio
    async def test_tts_synthesis_performance(self, mock_tts_service):
        """Test TTS synthesis performance."""
        texts = [
            "Short text",
            "Medium length text for testing synthesis",
            "This is a longer text to test the performance of the text-to-speech synthesis service"
        ]
        
        results = []
        for text in texts:
            audio_data = await mock_tts_service.synthesize(text)
            results.append(len(audio_data))
        
        # Longer texts should generally produce more audio data
        assert len(results) == 3
        assert all(r > 0 for r in results)
    
    @pytest.mark.asyncio
    async def test_tts_cleanup(self, mock_tts_service):
        """Test TTS service cleanup."""
        await mock_tts_service.cleanup()
        # Cleanup should not raise any errors


class TestAudioServicesIntegration:
    """Test integration between audio services."""
    
    @pytest.fixture
    def audio_services(self):
        """Create all audio services for integration testing."""
        return {
            "wake_word": MockWakeWordService(),
            "stt": MockSTTService(),
            "tts": MockTTSService()
        }
    
    @pytest.mark.asyncio
    async def test_audio_pipeline_integration(self, audio_services):
        """Test integration of all audio services."""
        wake_word = audio_services["wake_word"]
        stt = audio_services["stt"]
        tts = audio_services["tts"]
        
        # Simulate full pipeline
        audio_data = b"hey chef how do I cook pasta"
        
        # 1. Wake word detection
        wake_detected = await wake_word.detect(audio_data)
        assert wake_detected is True
        
        # 2. Speech-to-text
        transcription = await stt.transcribe(audio_data)
        assert isinstance(transcription, str)
        assert len(transcription) > 0
        
        # 3. Text-to-speech (for response)
        response_text = "Here's how to cook pasta properly"
        response_audio = await tts.synthesize(response_text)
        assert isinstance(response_audio, bytes)
        assert len(response_audio) > 0
    
    @pytest.mark.asyncio
    async def test_audio_services_with_different_chef_modes(self, audio_services):
        """Test audio services with different chef modes."""
        tts = audio_services["tts"]
        
        # Test responses for different chef modes
        base_text = "Here's how to cook pasta"
        
        # Different chef modes might affect TTS voice or style
        modes = [ChefMode.NORMAL, ChefMode.SASSY, ChefMode.GORDON_RAMSAY]
        
        for mode in modes:
            # In a real implementation, chef mode might affect voice selection
            audio_data = await tts.synthesize(base_text, voice="alloy")
            assert isinstance(audio_data, bytes)
            assert len(audio_data) > 0
    
    @pytest.mark.asyncio
    async def test_audio_services_error_propagation(self, audio_services):
        """Test error propagation through audio services."""
        services = audio_services.values()
        
        # Test that all services can handle cleanup without errors
        for service in services:
            await service.cleanup()
        
        # Test that services can be reused after cleanup
        wake_word = audio_services["wake_word"]
        detected = await wake_word.detect(b"test audio")
        assert isinstance(detected, bool)
    
    @pytest.mark.asyncio
    async def test_audio_services_concurrent_operations(self, audio_services):
        """Test concurrent operations across audio services."""
        wake_word = audio_services["wake_word"]
        stt = audio_services["stt"]
        tts = audio_services["tts"]
        
        # Run multiple operations concurrently
        tasks = [
            wake_word.detect(b"hey chef audio 1"),
            wake_word.detect(b"hey chef audio 2"),
            stt.transcribe(b"transcribe this audio"),
            tts.synthesize("synthesize this text")
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All operations should complete successfully
        assert len(results) == 4
        assert all(not isinstance(r, Exception) for r in results)
        
        # Check result types
        assert isinstance(results[0], bool)  # wake word detection
        assert isinstance(results[1], bool)  # wake word detection
        assert isinstance(results[2], str)   # transcription
        assert isinstance(results[3], bytes) # synthesized audio