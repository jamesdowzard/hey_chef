"""
Async speech-to-text service using OpenAI Whisper with voice activity detection.
Converted from the original synchronous implementation to async-compatible service.
"""
import asyncio
import os
import tempfile
import wave
from pathlib import Path
from typing import Optional, AsyncGenerator
import urllib.error

import sounddevice as sd
import webrtcvad

from .base import AudioService
from ..core.config import settings


class STTService(AudioService):
    """
    Async speech-to-text service using Whisper with voice activity detection.
    
    Features:
    - Async/await compatible
    - Voice activity detection (VAD)
    - Configurable silence detection
    - Temporary file management
    - Multiple model sizes
    - Streaming audio processing
    """
    
    def __init__(
        self,
        model_size: Optional[str] = None,
        aggressiveness: Optional[int] = None,
        max_silence_sec: Optional[float] = None,
        sample_rate: Optional[int] = None
    ):
        """
        Initialize speech-to-text service.
        
        Args:
            model_size: Whisper model size ("tiny", "base", "small", etc.)
            aggressiveness: VAD aggressiveness (0-3, higher = more aggressive)
            max_silence_sec: Seconds of silence before stopping recording
            sample_rate: Audio sample rate
        """
        super().__init__("stt")
        
        self.model_size = model_size or settings.audio.whisper_model_size
        self.aggressiveness = aggressiveness or settings.audio.vad_aggressiveness
        self.max_silence_sec = max_silence_sec or settings.audio.max_silence_sec
        self.sample_rate = sample_rate or settings.audio.sample_rate
        
        # Audio settings
        self.frame_duration_ms = 30  # 10, 20, or 30 ms supported by WebRTC VAD
        self.frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)
        self.max_silence_frames = int((self.max_silence_sec * 1000) / self.frame_duration_ms)
        
        # VAD and Whisper instances
        self.vad: Optional[webrtcvad.Vad] = None
        self.model = None
        self.stream: Optional[sd.RawInputStream] = None
        
        # Recording state
        self._recording_task: Optional[asyncio.Task] = None
    
    async def _initialize_impl(self) -> None:
        """Initialize VAD and Whisper model."""
        # Initialize VAD
        self.vad = webrtcvad.Vad(self.aggressiveness)
        self._store_resource("vad", self.vad)
        
        # Load Whisper model
        await self._load_whisper_model()
        
        self.logger.info(
            f"STT service initialized: model={self.model_size}, "
            f"vad_aggressiveness={self.aggressiveness}, "
            f"max_silence_sec={self.max_silence_sec}"
        )
    
    async def _cleanup_impl(self) -> None:
        """Clean up STT resources."""
        # Stop any recording
        if self._recording_task and not self._recording_task.done():
            self._recording_task.cancel()
            try:
                await self._recording_task
            except asyncio.CancelledError:
                pass
        
        # Close audio stream
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                self.logger.warning(f"Error closing audio stream: {e}")
            self.stream = None
    
    async def _start_impl(self) -> None:
        """Start the STT service (no-op, recordings are on-demand)."""
        pass
    
    async def _stop_impl(self) -> None:
        """Stop the STT service."""
        if self._recording_task and not self._recording_task.done():
            self._recording_task.cancel()
            try:
                await self._recording_task
            except asyncio.CancelledError:
                pass
    
    async def _load_whisper_model(self) -> None:
        """Load Whisper model asynchronously."""
        self.logger.info(f"Loading Whisper '{self.model_size}' model...")
        
        try:
            # Import whisper in the executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            def load_model():
                import whisper
                return whisper.load_model(self.model_size)
            
            self.model = await loop.run_in_executor(None, load_model)
            self._store_resource("model", self.model)
            
            self.logger.info("Whisper model loaded successfully")
            
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Failed to download Whisper model weights. "
                f"Please ensure internet access or pre-download: "
                f"`whisper --download-model {self.model_size}`"
            ) from e
        except ImportError:
            raise RuntimeError(
                "Whisper not installed. Install with: pip install openai-whisper"
            )
    
    async def _open_stream(self) -> None:
        """Open audio input stream if not already open."""
        if self.stream is None:
            try:
                self.stream = sd.RawInputStream(
                    samplerate=self.sample_rate,
                    blocksize=self.frame_size,
                    dtype="int16",
                    channels=1
                )
                self.stream.start()
                self.logger.debug("Audio input stream opened")
            except Exception as e:
                raise RuntimeError(f"Failed to open audio stream: {e}")
    
    async def _read_frame(self) -> Optional[bytes]:
        """Read one audio frame from the stream."""
        if not self.stream:
            return None
        
        try:
            # Run the blocking read in a thread pool
            loop = asyncio.get_event_loop()
            data, _ = await loop.run_in_executor(
                None,
                lambda: self.stream.read(self.frame_size)
            )
            return data.tobytes() if hasattr(data, "tobytes") else bytes(data)
        except Exception as e:
            self.logger.warning(f"Error reading audio frame: {e}")
            return None
    
    async def record_until_silence(self) -> str:
        """
        Record audio until silence is detected.
        
        Returns:
            Path to temporary WAV file containing the recording
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.managed_operation("record_until_silence"):
            self.logger.info("Starting audio recording...")
            await self._open_stream()
            
            frames = []
            triggered = False
            silence_count = 0
            
            try:
                while not self._should_stop():
                    frame = await self._read_frame()
                    if frame is None:
                        break
                    
                    # Check if frame contains speech
                    is_speech = await self._is_speech(frame)
                    
                    if not triggered:
                        # Wait for speech to begin
                        if is_speech:
                            triggered = True
                            frames.append(frame)
                            self.logger.debug("Speech detected, starting recording")
                    else:
                        # Recording in progress
                        frames.append(frame)
                        if not is_speech:
                            silence_count += 1
                            if silence_count > self.max_silence_frames:
                                self.logger.info("Silence detected, stopping recording")
                                break
                        else:
                            silence_count = 0
                
            except asyncio.CancelledError:
                self.logger.info("Recording interrupted")
                raise
            except Exception as e:
                self.logger.error(f"Recording error: {e}")
                return ""
            
            if not frames:
                self.logger.warning("No speech captured")
                return ""
            
            # Save to temporary WAV file
            wav_path = await self._save_frames_to_wav(frames)
            self.logger.info(f"Recording saved to {wav_path}")
            return wav_path
    
    async def _is_speech(self, frame: bytes) -> bool:
        """
        Check if audio frame contains speech using VAD.
        
        Args:
            frame: Audio frame data
            
        Returns:
            True if frame contains speech
        """
        try:
            # Run VAD in thread pool since it might be CPU intensive
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self.vad.is_speech,
                frame,
                self.sample_rate
            )
        except Exception as e:
            self.logger.warning(f"VAD error: {e}")
            return False
    
    async def _save_frames_to_wav(self, frames: list) -> str:
        """
        Save audio frames to a temporary WAV file.
        
        Args:
            frames: List of audio frames
            
        Returns:
            Path to temporary WAV file
        """
        # Create temporary file
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp.name
        tmp.close()
        
        try:
            # Save frames to WAV file (run in thread pool)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._write_wav_file,
                tmp_path,
                frames
            )
            
            return tmp_path
            
        except Exception as e:
            # Clean up on error
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            raise RuntimeError(f"Failed to save audio file: {e}")
    
    def _write_wav_file(self, path: str, frames: list) -> None:
        """Write frames to WAV file (synchronous helper)."""
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(b"".join(frames))
    
    async def transcribe_file(self, wav_path: str) -> str:
        """
        Transcribe WAV file using Whisper.
        
        Args:
            wav_path: Path to WAV file to transcribe
            
        Returns:
            Transcribed text (empty string if transcription fails)
        """
        if not wav_path or not Path(wav_path).is_file():
            return ""
        
        if not self._initialized:
            await self.initialize()
        
        async with self.managed_operation("transcribe_file"):
            try:
                # Run transcription in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self.model.transcribe(wav_path, fp16=False)
                )
                
                text = result.get("text", "").strip()
                self.logger.info(f"Transcribed: '{text}'")
                return text
                
            except Exception as e:
                self.logger.error(f"Transcription failed: {e}")
                return ""
            finally:
                # Clean up temporary file
                try:
                    os.remove(wav_path)
                except OSError as e:
                    self.logger.warning(f"Failed to remove temp file {wav_path}: {e}")
    
    async def transcribe_from_microphone(self) -> str:
        """
        Record from microphone and transcribe in one operation.
        
        Returns:
            Transcribed text
        """
        async with self.managed_operation("transcribe_from_microphone"):
            # Record audio
            wav_path = await self.record_until_silence()
            if not wav_path:
                return ""
            
            # Transcribe
            return await self.transcribe_file(wav_path)
    
    async def stream_transcription(self) -> AsyncGenerator[str, None]:
        """
        Stream transcription results as they become available.
        This is a placeholder for future streaming implementation.
        
        Yields:
            Transcribed text chunks
        """
        # For now, just do a single transcription
        # Future versions could implement real-time streaming
        text = await self.transcribe_from_microphone()
        if text:
            yield text
    
    def get_transcription_stats(self) -> dict:
        """
        Get transcription statistics.
        
        Returns:
            Dictionary with transcription stats
        """
        return {
            "model_size": self.model_size,
            "aggressiveness": self.aggressiveness,
            "max_silence_sec": self.max_silence_sec,
            "sample_rate": self.sample_rate,
            "is_active": self.is_active,
            "is_recording": self._recording_task is not None and not self._recording_task.done()
        }