"""
Tests for audio components - Speech-to-Text, Text-to-Speech, and Wake Word Detection.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import tempfile

# Add src to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from audio.speech_to_text import WhisperSTT
from audio.text_to_speech import TTSEngine
from audio.wake_word import WakeWordDetector


class TestWhisperSTT:
    """Test Whisper Speech-to-Text functionality."""
    
    @patch('audio.speech_to_text.whisper.load_model')
    @patch('audio.speech_to_text.webrtcvad.Vad')
    @patch('audio.speech_to_text.pyaudio.PyAudio')
    def test_whisper_initialization(self, mock_pyaudio, mock_vad, mock_whisper):
        """Test WhisperSTT initialization."""
        # Mock whisper model
        mock_model = Mock()
        mock_whisper.return_value = mock_model
        
        # Mock VAD
        mock_vad_instance = Mock()
        mock_vad.return_value = mock_vad_instance
        
        # Mock PyAudio
        mock_pyaudio_instance = Mock()
        mock_pyaudio.return_value = mock_pyaudio_instance
        
        stt = WhisperSTT(model_size="tiny", aggressiveness=2, max_silence_sec=3)
        
        assert stt.model == mock_model
        assert stt.vad == mock_vad_instance
        assert stt.pyaudio == mock_pyaudio_instance
        assert stt.max_silence_sec == 3
        
        mock_whisper.assert_called_once_with("tiny")
        mock_vad.assert_called_once_with(2)
    
    @patch('audio.speech_to_text.whisper.load_model')
    @patch('audio.speech_to_text.webrtcvad.Vad')
    @patch('audio.speech_to_text.pyaudio.PyAudio')
    def test_whisper_model_loading_error(self, mock_pyaudio, mock_vad, mock_whisper):
        """Test handling of whisper model loading errors."""
        mock_whisper.side_effect = Exception("Model loading failed")
        
        with pytest.raises(Exception, match="Model loading failed"):
            WhisperSTT(model_size="tiny")
    
    @patch('audio.speech_to_text.whisper.load_model')
    @patch('audio.speech_to_text.webrtcvad.Vad')
    @patch('audio.speech_to_text.pyaudio.PyAudio')
    def test_speech_to_text_success(self, mock_pyaudio, mock_vad, mock_whisper):
        """Test successful speech-to-text conversion."""
        # Mock whisper model
        mock_model = Mock()
        mock_model.transcribe.return_value = {"text": "Hello world"}
        mock_whisper.return_value = mock_model
        
        stt = WhisperSTT(model_size="tiny")
        
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            result = stt.speech_to_text(tmp_path)
            assert result == "Hello world"
            mock_model.transcribe.assert_called_once_with(tmp_path)
        finally:
            os.unlink(tmp_path)
    
    @patch('audio.speech_to_text.whisper.load_model')
    @patch('audio.speech_to_text.webrtcvad.Vad')
    @patch('audio.speech_to_text.pyaudio.PyAudio')
    def test_speech_to_text_file_not_found(self, mock_pyaudio, mock_vad, mock_whisper):
        """Test speech-to-text with non-existent file."""
        mock_model = Mock()
        mock_whisper.return_value = mock_model
        
        stt = WhisperSTT(model_size="tiny")
        result = stt.speech_to_text("nonexistent.wav")
        
        assert result == ""
    
    @patch('audio.speech_to_text.whisper.load_model')
    @patch('audio.speech_to_text.webrtcvad.Vad') 
    @patch('audio.speech_to_text.pyaudio.PyAudio')
    def test_record_until_silence_mock(self, mock_pyaudio, mock_vad, mock_whisper):
        """Test record_until_silence method with mocking."""
        # Setup mocks
        mock_model = Mock()
        mock_whisper.return_value = mock_model
        
        mock_vad_instance = Mock()
        mock_vad.return_value = mock_vad_instance
        
        mock_pyaudio_instance = Mock()
        mock_stream = Mock()
        mock_pyaudio_instance.open.return_value = mock_stream
        mock_pyaudio.return_value = mock_pyaudio_instance
        
        # Mock audio data (simulate voice activity)
        mock_stream.read.side_effect = [
            b'audio_data_1',  # Voice detected
            b'audio_data_2',  # Voice detected
            b'silence_data',  # Silence detected
            b'silence_data'   # More silence - should stop
        ]
        
        # Mock VAD to return voice activity then silence
        mock_vad_instance.is_speech.side_effect = [True, True, False, False]
        
        stt = WhisperSTT(model_size="tiny", max_silence_sec=1)
        
        with patch('audio.speech_to_text.wave.open') as mock_wave, \
             patch('audio.speech_to_text.tempfile.NamedTemporaryFile') as mock_temp:
            
            # Mock temporary file
            mock_temp_file = Mock()
            mock_temp_file.name = "test_recording.wav"
            mock_temp.return_value.__enter__.return_value = mock_temp_file
            
            # Mock wave file
            mock_wave_file = Mock()
            mock_wave.return_value.__enter__.return_value = mock_wave_file
            
            result = stt.record_until_silence()
            
            assert result == "test_recording.wav"
            mock_stream.start_stream.assert_called_once()
            mock_stream.stop_stream.assert_called_once()
            mock_stream.close.assert_called_once()


class TestTTSEngine:
    """Test Text-to-Speech functionality."""
    
    @patch.dict(os.environ, {"USE_EXTERNAL_TTS": "false"})
    @patch('audio.text_to_speech.subprocess.run')
    def test_tts_initialization_local(self, mock_subprocess):
        """Test TTS initialization with local engine."""
        tts = TTSEngine(voice_speed=150, voice_id="default")
        
        assert not tts.use_openai_tts
        assert tts.voice_speed == 150
        assert tts.voice_id == "default"
    
    @patch.dict(os.environ, {"USE_EXTERNAL_TTS": "true"})
    @patch('audio.text_to_speech.OpenAI')
    def test_tts_initialization_openai(self, mock_openai):
        """Test TTS initialization with OpenAI."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        tts = TTSEngine(voice_speed=150, voice_id="alloy")
        
        assert tts.openai_client == mock_client
        assert tts.use_openai_tts
        mock_openai.assert_called_once()
    
    @patch.dict(os.environ, {"USE_EXTERNAL_TTS": "false"})
    @patch('audio.text_to_speech.subprocess.run')
    def test_speak_local_engine(self, mock_subprocess):
        """Test speaking with local engine."""
        tts = TTSEngine()
        tts.say("Hello world")
        
        mock_subprocess.assert_called_once()
        args = mock_subprocess.call_args[0][0]
        assert "say" in args
        assert "Hello world" in args
    
    @patch.dict(os.environ, {"USE_EXTERNAL_TTS": "true"})
    @patch('audio.text_to_speech.OpenAI')
    @patch('audio.text_to_speech.subprocess.run')
    def test_speak_openai_engine(self, mock_subprocess, mock_openai):
        """Test speaking with OpenAI engine."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = b"audio_data"
        mock_client.audio.speech.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        tts = TTSEngine(voice_id="alloy")
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp_file = Mock()
            mock_temp_file.name = "temp_audio.mp3"
            mock_temp.return_value.__enter__.return_value = mock_temp_file
            
            tts.say("Hello world")
            
            mock_client.audio.speech.create.assert_called_once()
            mock_subprocess.assert_called_once()
    
    @patch.dict(os.environ, {"USE_EXTERNAL_TTS": "false"})
    @patch('audio.text_to_speech.subprocess.run')
    def test_speak_error_handling(self, mock_subprocess):
        """Test error handling in speak method."""
        mock_subprocess.side_effect = Exception("TTS Error")
        
        tts = TTSEngine()
        
        # Should not raise exception
        tts.say("Hello world")


class TestWakeWordDetector:
    """Test Wake Word Detection."""
    
    @patch('audio.wake_word.pvporcupine.create')
    @patch('audio.wake_word.pyaudio.PyAudio')
    def test_wake_word_initialization(self, mock_pyaudio, mock_porcupine):
        """Test wake word detector initialization."""
        mock_porcupine_instance = Mock()
        mock_porcupine_instance.sample_rate = 16000
        mock_porcupine_instance.frame_length = 512
        mock_porcupine.return_value = mock_porcupine_instance
        
        mock_pyaudio_instance = Mock()
        mock_pyaudio.return_value = mock_pyaudio_instance
        
        detector = WakeWordDetector(
            keyword_path="test_path.ppn"
        )
        
        assert detector.porcupine == mock_porcupine_instance
        assert detector.audio == mock_pyaudio_instance
        mock_porcupine.assert_called_once()
    
    @patch('audio.wake_word.pvporcupine.create')
    @patch('audio.wake_word.pyaudio.PyAudio')
    def test_wake_word_invalid_key(self, mock_pyaudio, mock_porcupine):
        """Test wake word detector with invalid access key."""
        mock_porcupine.side_effect = Exception("Invalid access key")
        
        with pytest.raises(Exception, match="Invalid access key"):
            WakeWordDetector(
                keyword_path="test_path.ppn"
            )
    
    @patch('audio.wake_word.pvporcupine.create')
    @patch('audio.wake_word.pyaudio.PyAudio')
    def test_listen_for_wake_word_detected(self, mock_pyaudio, mock_porcupine):
        """Test wake word detection."""
        # Setup mocks
        mock_porcupine_instance = Mock()
        mock_porcupine_instance.sample_rate = 16000
        mock_porcupine_instance.frame_length = 512
        mock_porcupine_instance.process.side_effect = [-1, -1, 0, -1]  # Wake word on 3rd frame
        mock_porcupine.return_value = mock_porcupine_instance
        
        mock_pyaudio_instance = Mock()
        mock_stream = Mock()
        mock_stream.read.return_value = b'audio_frame_data'
        mock_pyaudio_instance.open.return_value = mock_stream
        mock_pyaudio.return_value = mock_pyaudio_instance
        
        detector = WakeWordDetector(
            keyword_path="test_path.ppn"
        )
        
        with patch('audio.wake_word.struct.unpack') as mock_unpack:
            mock_unpack.return_value = [1, 2, 3]  # Mock PCM data
            
            result = detector.listen_for_wake_word()
            
            assert result is True
            mock_stream.start_stream.assert_called_once()
            mock_stream.stop_stream.assert_called_once()
            mock_stream.close.assert_called_once()
    
    @patch('audio.wake_word.pvporcupine.create')
    @patch('audio.wake_word.pyaudio.PyAudio')
    def test_listen_for_wake_word_interrupted(self, mock_pyaudio, mock_porcupine):
        """Test wake word detection with interruption."""
        mock_porcupine_instance = Mock()
        mock_porcupine_instance.sample_rate = 16000
        mock_porcupine_instance.frame_length = 512
        mock_porcupine_instance.process.return_value = -1
        mock_porcupine.return_value = mock_porcupine_instance
        
        mock_pyaudio_instance = Mock()
        mock_stream = Mock()
        mock_stream.read.return_value = b'audio_frame_data'
        mock_pyaudio_instance.open.return_value = mock_stream
        mock_pyaudio.return_value = mock_pyaudio_instance
        
        detector = WakeWordDetector(
            keyword_path="test_path.ppn"
        )
        
        # Setup interrupt event
        import threading
        interrupt_event = threading.Event()
        detector.interrupt_event = interrupt_event
        
        with patch('audio.wake_word.struct.unpack') as mock_unpack:
            mock_unpack.return_value = [1, 2, 3]
            
            # Interrupt after a short delay
            def set_interrupt():
                import time
                time.sleep(0.1)
                interrupt_event.set()
            
            import threading
            interrupt_thread = threading.Thread(target=set_interrupt)
            interrupt_thread.start()
            
            result = detector.listen_for_wake_word()
            interrupt_thread.join()
            
            assert result is False


class TestAudioComponentsIntegration:
    """Integration tests for audio components."""
    
    @patch('audio.speech_to_text.whisper.load_model')
    @patch('audio.text_to_speech.pyttsx3.init')
    def test_audio_pipeline_mocked(self, mock_tts, mock_whisper):
        """Test complete audio pipeline with mocking."""
        # Mock whisper
        mock_model = Mock()
        mock_model.transcribe.return_value = {"text": "test transcription"}
        mock_whisper.return_value = mock_model
        
        # Mock TTS engine
        mock_engine = Mock()
        mock_tts.return_value = mock_engine
        
        # Create components
        with patch('audio.speech_to_text.webrtcvad.Vad'), \
             patch('audio.speech_to_text.pyaudio.PyAudio'), \
             patch.dict(os.environ, {"USE_EXTERNAL_TTS": "false"}):
            
            stt = WhisperSTT(model_size="tiny")
            tts = TTSEngine()
            
            # Test speech-to-text
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            try:
                transcription = stt.speech_to_text(tmp_path)
                assert transcription == "test transcription"
                
                # Test text-to-speech
                tts.say(transcription)
                # Note: Updated implementation uses subprocess.run, not pyttsx3
                
            finally:
                os.unlink(tmp_path)
    
    def test_error_propagation(self):
        """Test that errors are properly handled across components."""
        # Test with missing environment variables
        with patch.dict(os.environ, {}, clear=True):
            # TTS should handle missing OpenAI key gracefully
            with patch('audio.text_to_speech.subprocess.run'):
                tts = TTSEngine()
                # Should not raise exception
                tts.say("test")
    
    @patch('audio.wake_word.os.path.isfile')
    @patch.dict(os.environ, {"PICO_ACCESS_KEY": "test_access_key"})
    @patch('audio.wake_word.pvporcupine.create')
    def test_resource_cleanup(self, mock_porcupine, mock_isfile):
        """Test that audio resources are properly cleaned up."""
        # Mock file existence
        mock_isfile.return_value = True
        
        mock_porcupine_instance = Mock()
        mock_porcupine.return_value = mock_porcupine_instance
        
        with patch('audio.wake_word.pyaudio.PyAudio') as mock_pyaudio:
            mock_pyaudio_instance = Mock()
            mock_stream = Mock()
            mock_pyaudio_instance.open.return_value = mock_stream
            mock_pyaudio.return_value = mock_pyaudio_instance
            
            detector = WakeWordDetector(
                keyword_path="test_path.ppn"
            )
            
            detector.cleanup()
            mock_porcupine_instance.delete.assert_called_once()