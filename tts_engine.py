# tts_engine.py
#
# A TTS interface that toggles between:
#   • macOS built-in voices (“Samantha”, etc.), at 1.25× speed, or
#   • OpenAI’s TTS via the `tts-1` model, post‐processed with sox to 1.25× speed.

import os
import sys
import subprocess
import tempfile
from dotenv import load_dotenv
import shutil

# Load environment variables from .env
load_dotenv()

# Attempt to import the external engine; if missing, we’ll fallback to macOS voices
try:
    from tts_engine_external import ExternalTTSEngine
except ImportError:
    ExternalTTSEngine = None

class TTSEngine:
    """
    If USE_EXTERNAL_TTS is set in the environment, delegate to ExternalTTSEngine (OpenAI TTS).
    Otherwise, use macOS’s built-in `say -v <voice> -r <rate>` + `afplay`.
    Both modes speak at 1.25x speed.
    """

    def __init__(self, macos_voice: str = "Samantha", external_voice: str = "alloy"):
        """
        macos_voice: name of a local macOS TTS voice (e.g. "Samantha", "Victoria").
        external_voice: name of an OpenAI TTS voice (e.g. "alloy").
        """
        # True if USE_EXTERNAL_TTS is set to a non-empty value
        self.use_external = bool(os.getenv("USE_EXTERNAL_TTS", "").strip())
        self.macos_voice = macos_voice

        if self.use_external:
            if ExternalTTSEngine is None:
                raise ImportError(
                    "ExternalTTSEngine not available. "
                    "Ensure you have tts_engine_external.py and openai installed."
                )
            # Initialize the external engine
            self.external_tts = ExternalTTSEngine(voice=external_voice)
        else:
            self.external_tts = None

        # For macOS `say`, default words-per-minute is ~175; 1.25× that is ~219
        self.macos_rate = 219

    def say(self, text: str):
        """
        Speak `text`.  
        If USE_EXTERNAL_TTS is truthy, use ExternalTTSEngine.say(), then speed up with sox.  
        Otherwise, use macOS’s say with -r 219 for 1.25× speed.
        """
        if self.use_external and self.external_tts:
            self.external_tts.say(text)
        else:
            self._say_macos(text)

    def _say_macos(self, text: str):
        """
        Generate a temp AIFF via: say -v <macos_voice> -r <macos_rate> -o <path> "<text>", 
        then play it via afplay.
        """
        tmpfile = tempfile.NamedTemporaryFile(suffix=".aiff", delete=False)
        tmpfile.close()
        aiff_path = tmpfile.name

        try:
            # 1) Generate the AIFF using the chosen macOS voice at 1.25× speed
            subprocess.run(
                ["say", "-v", self.macos_voice, "-r", str(self.macos_rate), "-o", aiff_path, text],
                check=True
            )
            # 2) Play it using afplay
            subprocess.run(["afplay", aiff_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"⚠️ macOS TTS error (say/afplay): {e}")
        finally:
            # 3) Clean up the temporary file
            if os.path.exists(aiff_path):
                os.remove(aiff_path)