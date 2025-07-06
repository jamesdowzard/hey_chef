"""
Test examples for Hey Chef v2 services.
Demonstrates how to test the async services with proper mocking.
"""
import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator

from .wake_word import WakeWordService
from .stt import STTService
from .tts import TTSService
from .llm import LLMService


class TestWakeWordService:
    """Test cases for WakeWordService."""
    
    @pytest_asyncio.fixture
    async def mock_wake_word_service(self):
        """Create a mock wake word service for testing."""
        with patch('pvporcupine.create') as mock_porcupine, \
             patch('pyaudio.PyAudio') as mock_pyaudio, \
             patch('pathlib.Path.is_file', return_value=True):
            
            # Configure mocks
            mock_porcupine_instance = MagicMock()
            mock_porcupine_instance.sample_rate = 16000
            mock_porcupine_instance.frame_length = 512
            mock_porcupine.return_value = mock_porcupine_instance
            
            mock_stream = MagicMock()
            mock_pa = MagicMock()
            mock_pa.open.return_value = mock_stream
            mock_pyaudio.return_value = mock_pa
            
            service = WakeWordService()
            await service.initialize()
            
            yield service, mock_porcupine_instance, mock_stream
            
            await service.cleanup()
    
    @pytest.mark.asyncio
    async def test_initialization(self, mock_wake_word_service):
        """Test that the wake word service initializes properly."""
        service, mock_porcupine, mock_stream = mock_wake_word_service
        
        assert service._initialized
        assert service.porcupine is not None
        assert service.stream is not None
    
    @pytest.mark.asyncio
    async def test_detection_callback(self, mock_wake_word_service):
        """Test wake word detection with callback."""
        service, mock_porcupine, mock_stream = mock_wake_word_service
        
        callback_called = asyncio.Event()
        
        async def detection_callback():
            callback_called.set()
        
        await service.set_detection_callback(detection_callback)
        
        # Mock successful detection
        mock_porcupine.process.return_value = 0  # Wake word detected
        mock_stream.read.return_value = b'\x00' * 1024
        
        # Start detection and simulate one cycle
        await service.start()
        
        # Wait a bit for detection loop to process
        await asyncio.sleep(0.1)
        
        await service.stop()
        
        # Note: In a real test, you'd need to properly simulate the detection loop
        # This is a simplified example showing the structure


class TestSTTService:
    """Test cases for STTService."""
    
    @pytest_asyncio.fixture
    async def mock_stt_service(self):
        """Create a mock STT service for testing."""
        with patch('webrtcvad.Vad') as mock_vad, \
             patch('sounddevice.RawInputStream') as mock_stream, \
             patch.object(STTService, '_load_whisper_model'):
            
            mock_vad_instance = MagicMock()
            mock_vad.return_value = mock_vad_instance
            
            mock_stream_instance = MagicMock()
            mock_stream.return_value = mock_stream_instance
            
            service = STTService()
            service.model = MagicMock()  # Mock Whisper model
            await service.initialize()
            
            yield service, mock_vad_instance, mock_stream_instance
            
            await service.cleanup()
    
    @pytest.mark.asyncio
    async def test_transcription(self, mock_stt_service):
        """Test audio transcription."""
        service, mock_vad, mock_stream = mock_stt_service
        
        # Mock successful transcription
        service.model.transcribe.return_value = {"text": "Hello world"}
        
        with patch('tempfile.NamedTemporaryFile'), \
             patch('wave.open'), \
             patch('pathlib.Path.is_file', return_value=True):
            
            result = await service.transcribe_file("/fake/path.wav")
            assert result == "Hello world"


class TestTTSService:
    """Test cases for TTSService."""
    
    @pytest_asyncio.fixture
    async def mock_tts_service(self):
        """Create a mock TTS service for testing."""
        service = TTSService(use_external=False)  # Use macOS TTS for testing
        await service.initialize()
        
        yield service
        
        await service.cleanup()
    
    @pytest.mark.asyncio
    async def test_say_macos(self, mock_tts_service):
        """Test macOS TTS functionality."""
        service = mock_tts_service
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b'', b'')
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            await service._say_macos("Hello world")
            
            # Verify subprocess was called
            assert mock_subprocess.called
    
    @pytest.mark.asyncio
    async def test_streaming_tts(self, mock_tts_service):
        """Test streaming TTS functionality."""
        service = mock_tts_service
        
        async def text_generator():
            chunks = ["Hello ", "world ", "from ", "streaming!"]
            for chunk in chunks:
                yield chunk
        
        with patch.object(service, '_say_macos') as mock_say:
            result = await service.stream_and_play(text_generator())
            assert result == "Hello world from streaming!"
            mock_say.assert_called_once()


class TestLLMService:
    """Test cases for LLMService."""
    
    @pytest_asyncio.fixture
    async def mock_llm_service(self):
        """Create a mock LLM service for testing."""
        with patch.object(LLMService, '_initialize_impl'):
            service = LLMService()
            
            # Mock OpenAI client
            mock_client = MagicMock()
            service.openai_client = mock_client
            service._initialized = True
            
            yield service, mock_client
            
            await service.cleanup()
    
    @pytest.mark.asyncio
    async def test_ask_normal_mode(self, mock_llm_service):
        """Test LLM ask functionality in normal mode."""
        service, mock_client = mock_llm_service
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Here's your cooking advice!"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = await service.ask(
            recipe_text="Pasta recipe",
            user_question="How long to cook?",
            chef_mode="normal"
        )
        
        assert result == "Here's your cooking advice!"
        mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_streaming_response(self, mock_llm_service):
        """Test LLM streaming functionality."""
        service, mock_client = mock_llm_service
        
        # Mock streaming response
        class MockStreamChunk:
            def __init__(self, content):
                self.choices = [MagicMock()]
                self.choices[0].delta.content = content
        
        mock_stream = [
            MockStreamChunk("Hello "),
            MockStreamChunk("there!"),
            MockStreamChunk(None)  # End of stream
        ]
        mock_client.chat.completions.create.return_value = iter(mock_stream)
        
        chunks = []
        async for chunk in service.stream(
            recipe_text="Test recipe",
            user_question="Test question",
            chef_mode="sassy"
        ):
            chunks.append(chunk)
        
        assert chunks == ["Hello ", "there!"]
    
    @pytest.mark.asyncio
    async def test_chef_modes(self, mock_llm_service):
        """Test different chef modes have different parameters."""
        service, _ = mock_llm_service
        
        normal_tokens, normal_temp = service._get_mode_parameters("normal")
        sassy_tokens, sassy_temp = service._get_mode_parameters("sassy")
        gordon_tokens, gordon_temp = service._get_mode_parameters("gordon_ramsay")
        
        # Verify different modes have different parameters
        assert normal_tokens != sassy_tokens
        assert normal_temp != sassy_temp
        assert sassy_tokens != gordon_tokens


class TestServiceIntegration:
    """Integration tests for multiple services working together."""
    
    @pytest.mark.asyncio
    async def test_audio_pipeline_simulation(self):
        """Test a simulated audio processing pipeline."""
        # This would test the services working together
        # In a real scenario, you'd mock the external dependencies
        # and test the flow between services
        
        async def simulate_wake_word_to_response():
            # 1. Wake word detected
            wake_word_detected = True
            
            # 2. Record and transcribe speech
            if wake_word_detected:
                transcribed_text = "How long should I cook pasta?"
            
            # 3. Get LLM response
            if transcribed_text:
                llm_response = "Cook pasta for 8-12 minutes until al dente."
            
            # 4. Speak response
            if llm_response:
                tts_completed = True
            
            return tts_completed
        
        result = await simulate_wake_word_to_response()
        assert result is True


# Example of how to run specific tests
if __name__ == "__main__":
    # Run a specific test
    async def run_test():
        service = TTSService()
        await service.initialize()
        
        print("TTS Service Stats:", service.get_tts_stats())
        print("Available Voices:", await service.get_available_voices())
        
        await service.cleanup()
    
    asyncio.run(run_test())