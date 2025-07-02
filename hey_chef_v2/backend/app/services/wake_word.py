"""
Async wake word detection service using Picovoice Porcupine.
Converted from the original synchronous implementation to async-compatible service.
"""
import asyncio
import os
import struct
from typing import Optional, Callable, Awaitable
from pathlib import Path

import pvporcupine
import pyaudio

from .base import AudioService
from ..core.config import settings


class WakeWordService(AudioService):
    """
    Async wake word detection service using Porcupine on-device detection.
    
    Features:
    - Async/await compatible
    - Proper resource management
    - Configurable sensitivity
    - Callback-based detection
    - Graceful shutdown
    """
    
    def __init__(
        self,
        keyword_path: Optional[str] = None,
        sensitivity: Optional[float] = None,
        detection_callback: Optional[Callable[[], Awaitable[None]]] = None
    ):
        """
        Initialize wake word detection service.
        
        Args:
            keyword_path: Path to the .ppn wake word model file (uses config default if None)
            sensitivity: Detection sensitivity 0.0-1.0 (uses config default if None)
            detection_callback: Async callback to call when wake word is detected
        """
        super().__init__("wake_word")
        
        self.keyword_path = keyword_path or settings.get_wake_word_path()
        self.sensitivity = sensitivity or settings.audio.wake_word_sensitivity
        self.detection_callback = detection_callback
        
        # Porcupine resources
        self.porcupine: Optional[pvporcupine.Porcupine] = None
        self.pa: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        
        # Detection state
        self._detection_task: Optional[asyncio.Task] = None
        self._frame_count = 0
    
    async def _initialize_impl(self) -> None:
        """Initialize Porcupine wake word detector."""
        # Validate keyword model file
        if not Path(self.keyword_path).is_file():
            raise FileNotFoundError(f"Wake-word model not found: {self.keyword_path}")
        
        # Validate API key
        access_key = settings.pico_access_key
        if not access_key:
            raise EnvironmentError("PICO_ACCESS_KEY not set in environment")
        
        self.logger.info(f"Initializing wake word detector: sensitivity={self.sensitivity}")
        
        try:
            # Create Porcupine instance
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keyword_paths=[self.keyword_path],
                sensitivities=[self.sensitivity]
            )
            self._store_resource("porcupine", self.porcupine)
            
            # Open microphone stream
            self.pa = pyaudio.PyAudio()
            self._store_resource("pyaudio", self.pa)
            
            self.stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            self._store_resource("stream", self.stream)
            
        except Exception as e:
            await self._cleanup_resources()
            raise RuntimeError(f"Failed to initialize wake word detector: {e}")
    
    async def _cleanup_impl(self) -> None:
        """Clean up Porcupine resources."""
        await self._cleanup_resources()
    
    async def _cleanup_resources(self) -> None:
        """Clean up all Porcupine-related resources."""
        # Stop detection if running
        if self._detection_task and not self._detection_task.done():
            self._detection_task.cancel()
            try:
                await self._detection_task
            except asyncio.CancelledError:
                pass
        
        # Close audio stream
        stream = self._get_resource("stream")
        if stream:
            try:
                stream.stop_stream()
                stream.close()
            except Exception as e:
                self.logger.warning(f"Error closing audio stream: {e}")
        
        # Terminate PyAudio
        pa = self._get_resource("pyaudio")
        if pa:
            try:
                pa.terminate()
            except Exception as e:
                self.logger.warning(f"Error terminating PyAudio: {e}")
        
        # Delete Porcupine instance
        porcupine = self._get_resource("porcupine")
        if porcupine:
            try:
                porcupine.delete()
            except Exception as e:
                self.logger.warning(f"Error deleting Porcupine instance: {e}")
    
    async def _start_impl(self) -> None:
        """Start wake word detection."""
        if not self.porcupine or not self.stream:
            raise RuntimeError("Wake word detector not properly initialized")
        
        self.logger.info("Starting wake word detection")
        self._detection_task = asyncio.create_task(self._detection_loop())
    
    async def _stop_impl(self) -> None:
        """Stop wake word detection."""
        if self._detection_task and not self._detection_task.done():
            self.logger.info("Stopping wake word detection")
            self._detection_task.cancel()
            try:
                await self._detection_task
            except asyncio.CancelledError:
                pass
    
    async def _detection_loop(self) -> None:
        """
        Main detection loop that processes audio frames.
        Runs in the background and calls the detection callback when wake word is detected.
        """
        self.logger.info("Wake word detection loop started - listening for 'Hey Chef'")
        self._frame_count = 0
        
        try:
            while not self._should_stop():
                self._frame_count += 1
                
                # Log periodic status (every 1000 frames, roughly every 2 seconds)
                if self._frame_count % 1000 == 0:
                    self.logger.debug(f"Still listening for wake word (frame {self._frame_count})")
                
                try:
                    # Read audio frame (non-blocking)
                    pcm = await self._read_audio_frame()
                    if pcm is None:
                        continue
                    
                    # Process with Porcupine
                    result = await self._process_audio_frame(pcm)
                    if result >= 0:
                        self.logger.info(f"Wake word detected after {self._frame_count} frames!")
                        await self._handle_wake_word_detected()
                        
                except Exception as e:
                    self.logger.error(f"Error in detection loop: {e}")
                    await asyncio.sleep(0.01)  # Brief pause on errors
                    
        except asyncio.CancelledError:
            self.logger.info("Wake word detection loop cancelled")
            raise
        except Exception as e:
            self.logger.error(f"Wake word detection loop failed: {e}")
        finally:
            self.logger.info("Wake word detection loop ended")
    
    async def _read_audio_frame(self) -> Optional[bytes]:
        """
        Read one audio frame from the stream.
        
        Returns:
            Audio frame data or None if read fails
        """
        try:
            # Run the blocking read in a thread pool
            loop = asyncio.get_event_loop()
            pcm = await loop.run_in_executor(
                None,
                lambda: self.stream.read(
                    self.porcupine.frame_length,
                    exception_on_overflow=False
                )
            )
            return pcm
        except Exception as e:
            self.logger.warning(f"Failed to read audio frame: {e}")
            return None
    
    async def _process_audio_frame(self, pcm: bytes) -> int:
        """
        Process audio frame with Porcupine.
        
        Args:
            pcm: Raw PCM audio data
            
        Returns:
            Porcupine processing result (>= 0 means wake word detected)
        """
        try:
            # Convert raw PCM bytes to int16 samples
            pcm_int16 = struct.unpack(
                f"<{self.porcupine.frame_length}h",
                pcm
            )
            
            # Process with Porcupine (run in thread pool since it might be CPU intensive)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.porcupine.process,
                pcm_int16
            )
            
            return result
            
        except Exception as e:
            self.logger.warning(f"Failed to process audio frame: {e}")
            return -1
    
    async def _handle_wake_word_detected(self) -> None:
        """Handle wake word detection by calling the callback if provided."""
        try:
            if self.detection_callback:
                await self.detection_callback()
            else:
                self.logger.info("Wake word detected but no callback provided")
        except Exception as e:
            self.logger.error(f"Error in wake word detection callback: {e}")
    
    async def detect_once(self) -> bool:
        """
        Wait for wake word to be detected once.
        
        Returns:
            True if wake word was detected, False if cancelled
        """
        if not self._initialized:
            await self.initialize()
        
        self.logger.info("Starting single wake word detection")
        
        # Create a future to track detection
        detection_future: asyncio.Future[bool] = asyncio.Future()
        
        async def detection_callback():
            if not detection_future.done():
                detection_future.set_result(True)
        
        # Temporarily set the callback
        original_callback = self.detection_callback
        self.detection_callback = detection_callback
        
        try:
            # Start detection
            await self.start()
            
            # Wait for detection or cancellation
            try:
                result = await detection_future
                return result
            except asyncio.CancelledError:
                return False
            
        finally:
            # Restore original callback and stop detection
            self.detection_callback = original_callback
            await self.stop()
    
    async def set_detection_callback(self, callback: Optional[Callable[[], Awaitable[None]]]) -> None:
        """
        Set or update the detection callback.
        
        Args:
            callback: Async callback to call when wake word is detected
        """
        self.detection_callback = callback
        self.logger.info("Wake word detection callback updated")
    
    def get_detection_stats(self) -> dict:
        """
        Get detection statistics.
        
        Returns:
            Dictionary with detection stats
        """
        return {
            "is_active": self.is_active,
            "frame_count": self._frame_count,
            "sensitivity": self.sensitivity,
            "keyword_path": self.keyword_path
        }