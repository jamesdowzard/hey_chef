# wake_porcupine.py
#
# Uses Picovoice Porcupine to detect the wake word “hey chef” on-device.
# Requires:
#   - porcupine_models/hey_chef.ppn       (your trained wake-word model)
#   - porcupine_models/porcupine_params.pv (Porcupine engine parameters)
#   - pyaudio (for microphone capture)
#   - pvporcupine (Porcupine Python SDK)

import pvporcupine
import pyaudio
import signal
import struct
import sys
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file if it exists

class WakeWordDetector:
    """
    Blocks until the wake word “hey chef” is detected via Porcupine.
    """

    def __init__(self, keyword_path: str = "porcupine_models/hey_chef.ppn", sensitivity: float = 0.7):
        if not os.path.isfile(keyword_path):
            raise FileNotFoundError(f"Wake-word model not found: {keyword_path}")
        
        access_key = os.getenv("PICO_ACCESS_KEY")
        if not access_key:
            raise EnvironmentError("PICO_ACCESS_KEY not set in environment")
        
        # Create Porcupine instance using the built-in parameters
        self.porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=[keyword_path],
            sensitivities=[sensitivity]
        )

        # Open the default mic with Porcupine’s required sample_rate and frame_length
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )

        # signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, sig, frame):
        """
        Invoked on Ctrl+C. Cleans up and exits.
        """
        self.cleanup()
        sys.exit(0)

    def detect_once(self) -> bool:
        """
        Blocks until the wake word is detected once. Returns True when detected.
        """
        print("👂 Listening for wake word (‘Hey Chef’)…")
        while True:
            pcm = self.stream.read(self.porcupine.frame_length, exception_on_overflow=False)

            # Convert raw PCM bytes to a tuple of int16 samples (little-endian)
            pcm_int16 = struct.unpack("<{}h".format(self.porcupine.frame_length), pcm)

            # pcm_int16 = pvporcupine._util.pv_buffer_to_int16_list(pcm)
            
            result = self.porcupine.process(pcm_int16)
            if result >= 0:
                # result is the index of the detected keyword in keyword_paths
                print("🟢 Wake word detected!")
                return True

    def cleanup(self):
        """
        Release resources cleanly.
        """
        if hasattr(self, "stream") and self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, "pa") and self.pa is not None:
            self.pa.terminate()
        if hasattr(self, "porcupine") and self.porcupine is not None:
            self.porcupine.delete()