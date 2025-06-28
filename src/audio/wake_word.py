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
        if not os.path.isfile(keyword_path):
            raise FileNotFoundError(f"Wake-word model not found: {keyword_path}")
        
        access_key = os.getenv("PICO_ACCESS_KEY")
        if not access_key:
            raise EnvironmentError("PICO_ACCESS_KEY not set in environment")
        
        self.porcupine: Optional[pvporcupine.Porcupine] = None
        self.pa: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        
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
            
        Raises:
            RuntimeError: If detection fails
        """
        if not self.stream or not self.porcupine:
            raise RuntimeError("Wake word detector not properly initialized")
            
        print("👂 Listening for wake word ('Hey Chef')…")
        
        try:
            while True:
                pcm = self.stream.read(
                    self.porcupine.frame_length, 
                    exception_on_overflow=False
                )

                # Convert raw PCM bytes to int16 samples
                pcm_int16 = struct.unpack(
                    f"<{self.porcupine.frame_length}h", 
                    pcm
                )
                
                result = self.porcupine.process(pcm_int16)
                if result >= 0:
                    print("🟢 Wake word detected!")
                    return True
                    
        except Exception as e:
            raise RuntimeError(f"Wake word detection failed: {e}")

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