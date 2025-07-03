"""
Wake word detection using Picovoice Porcupine.
"""
import os
import pvporcupine
import pyaudio
import struct
import sys
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Import logger utility
try:
    from ..utils.logger import get_logger
except ImportError:
    # Fallback for when logger is not available
    class DummyLogger:
        def log_audio_event(self, *args, **kwargs): pass
        def log_error(self, *args, **kwargs): pass
    def get_logger(): return DummyLogger()


class WakeWordDetector:
    """
    Detects wake word "hey chef" using Porcupine on-device detection.
    """

    def __init__(self, keyword_path: str, sensitivity: float = 0.7):
        """
        Initialize wake word detector.
        
        Args:
            keyword_path: Path to the .ppn wake word model file
            sensitivity: Detection sensitivity (0.0 to 1.0)
        """
        self.logger = get_logger()
        
        if not os.path.isfile(keyword_path):
            self.logger.log_error("WAKE_WORD_INIT", f"Wake-word model not found: {keyword_path}")
            raise FileNotFoundError(f"Wake-word model not found: {keyword_path}")
        
        access_key = os.getenv("PICO_ACCESS_KEY")
        if not access_key:
            self.logger.log_error("WAKE_WORD_INIT", "PICO_ACCESS_KEY not set in environment")
            raise EnvironmentError("PICO_ACCESS_KEY not set in environment")
            
        self.logger.log_audio_event("WAKE_WORD_INIT", f"Initializing wake word detector: sensitivity={sensitivity}")
        
        self.porcupine: Optional[pvporcupine.Porcupine] = None
        self.pa: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        # Optional external event to interrupt detection
        self.stop_event = None
        
        try:
            # Create Porcupine instance
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keyword_paths=[keyword_path],
                sensitivities=[sensitivity]
            )

            # Open microphone stream
            self.pa = pyaudio.PyAudio()
            self.stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
        except Exception as e:
            self.cleanup()
            raise RuntimeError(f"Failed to initialize wake word detector: {e}")

    def detect_once(self) -> bool:
        """
        Block until wake word is detected once.
        
        Returns:
            True when wake word is detected
            False if stopped before detection
            
        Raises:
            RuntimeError: If detection fails
        """
        if not self.stream or not self.porcupine:
            error_msg = "Wake word detector not properly initialized"
            print(f"❌ {error_msg}")
            self.logger.log_error("WAKE_WORD_DETECT", error_msg, "Missing stream or porcupine")
            raise RuntimeError(error_msg)
            
        print("👂 Listening for wake word ('Hey Chef')…")
        self.logger.log_audio_event("WAKE_WORD_LISTENING", "Started listening for wake word")
        
        try:
            frame_count = 0
            while True:
                frame_count += 1
                
                # Log periodic status (every 1000 frames, roughly every 2 seconds)
                if frame_count % 1000 == 0:
                    print(f"👂 Still listening... (frame {frame_count})")
                
                # Exit early if stop_event is set
                if self.stop_event and self.stop_event.is_set():
                    print(f"🛑 Wake word detection stopped by event")
                    self.logger.log_audio_event("WAKE_WORD_STOPPED", f"Stopped by event after {frame_count} frames")
                    return False
                
                try:
                    pcm = self.stream.read(
                        self.porcupine.frame_length, 
                        exception_on_overflow=False
                    )
                except Exception as audio_e:
                    print(f"❌ Audio read error: {audio_e}")
                    self.logger.log_error("WAKE_WORD_AUDIO", str(audio_e), "Failed to read audio stream")
                    raise RuntimeError(f"Audio stream read failed: {audio_e}")

                # Convert raw PCM bytes to int16 samples
                try:
                    pcm_int16 = struct.unpack(
                        f"<{self.porcupine.frame_length}h", 
                        pcm
                    )
                except Exception as unpack_e:
                    print(f"❌ Audio unpacking error: {unpack_e}")
                    self.logger.log_error("WAKE_WORD_UNPACK", str(unpack_e), "Failed to unpack audio data")
                    raise RuntimeError(f"Audio data unpacking failed: {unpack_e}")
                
                try:
                    result = self.porcupine.process(pcm_int16)
                    if result >= 0:
                        print("🟢 Wake word detected!")
                        self.logger.log_audio_event("WAKE_WORD_DETECTED", f"Wake word detected after {frame_count} frames")
                        return True
                except Exception as process_e:
                    print(f"❌ Porcupine processing error: {process_e}")
                    self.logger.log_error("WAKE_WORD_PROCESS", str(process_e), "Failed to process audio with Porcupine")
                    raise RuntimeError(f"Porcupine processing failed: {process_e}")
                    
        except Exception as e:
            error_msg = f"Wake word detection failed: {e}"
            print(f"❌ {error_msg}")
            self.logger.log_error("WAKE_WORD_DETECT", str(e), "General wake word detection failure")
            raise RuntimeError(error_msg)

    def cleanup(self):
        """Release all resources cleanly."""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
            
        if self.pa:
            try:
                self.pa.terminate()
            except Exception:
                pass
            self.pa = None
            
        if self.porcupine:
            try:
                self.porcupine.delete()
            except Exception:
                pass
            self.porcupine = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup() 