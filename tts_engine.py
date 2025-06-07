# tts_engine.py
#
# A TTS interface that toggles between:
#   • macOS built-in voices (“Samantha”, etc.), at 1.25× speed, or
#   • OpenAI’s TTS via the `tts-1` model, post‐processed with sox to 1.25× speed.

import os
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
    Provides both one-off `say()` and streaming `stream_and_play()` methods.
    """

    def __init__(self, macos_voice: str = "Samantha", external_voice: str = "alloy"):
        """
        macos_voice: name of a local macOS TTS voice.
        external_voice: name of an OpenAI TTS voice.
        """
        # True if USE_EXTERNAL_TTS is set to a non-empty value
        self.use_external = bool(os.getenv("USE_EXTERNAL_TTS", "").strip())
        self.macos_voice = macos_voice
        self.macos_rate = 219  # ~1.25× default WPM

        if self.use_external:
            if ExternalTTSEngine is None:
                raise ImportError(
                    "ExternalTTSEngine not available. Ensure tts_engine_external.py is present and openai installed."
                )
            self.external_tts = ExternalTTSEngine(voice=external_voice)
        else:
            self.external_tts = None

    def say(self, text: str):
        """
        Speak `text`.  
        If external mode, delegate to ExternalTTSEngine.say().  
        Otherwise use macOS voices for a single utterance.
        """
        if self.use_external and self.external_tts:
            self.external_tts.say(text)
        else:
            self._say_macos(text)

    def _say_macos(self, text: str):
        """
        Generate a temp AIFF via say, then play it via afplay.
        """
        tmpfile = tempfile.NamedTemporaryFile(suffix=".aiff", delete=False)
        tmpfile.close()
        aiff_path = tmpfile.name

        try:
            subprocess.run(
                ["say", "-v", self.macos_voice, "-r", str(self.macos_rate), "-o", aiff_path, text],
                check=True
            )
            subprocess.run(["afplay", aiff_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"⚠️ macOS TTS error (say/afplay): {e}")
        finally:
            if os.path.exists(aiff_path):
                os.remove(aiff_path)

    def stream_and_play(self, text_generator, start_threshold: int = 80) -> str:
        """
        text_generator: iterator yielding strings (e.g. LLMClient.stream()).
        Buffers until `start_threshold` chars, starts playback, then continues.
        Returns full assembled text.
        """
        if self.use_external and self.external_tts:
            return self.external_tts.stream_and_play(text_generator, start_threshold)

        # Fallback: collect all chunks then speak once
        full_text = ""
        for chunk in text_generator:
            full_text += chunk
        # One-shot macOS TTS
        self._say_macos(full_text)
        return full_text
