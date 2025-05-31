# tts_engine_external.py

import os
import tempfile
import subprocess
from dotenv import load_dotenv
import shutil

# Load .env so OPENAI_API_KEY (and USE_EXTERNAL_TTS) are available
load_dotenv()

try:
    import openai
except ImportError:
    raise ImportError("Please install openai: pip install openai")

class ExternalTTSEngine:
    """
    A TTS engine that uses OpenAI’s speech endpoint.
    - Requires: OPENAI_API_KEY in environment (loaded from .env).
    - Generates an MP3 via OpenAI, writes to a temp file, optionally applies sox tempo 1.25,
      then plays via afplay.
    """

    def __init__(self, voice: str = "alloy"):
        """
        voice: The OpenAI TTS voice name.
               Examples (if available): "alloy", "rainier", etc.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY not set in environment.")
        openai.api_key = api_key

        self.voice = voice

        # Check if sox is available for speedup
        self.has_sox = bool(shutil.which("sox"))

    def say(self, text: str):
        """
        1) Request speech bytes from OpenAI (MP3).
        2) Write to a temp MP3, optionally speed up by 1.25× using sox.
        3) Play via afplay.
        """
        try:
            # 1) Request TTS from OpenAI (response is HttpxBinaryResponseContent)
            response = openai.audio.speech.create(
                model="tts-1",    # or another TTS model you have access to
                voice=self.voice,
                input=text
            )
            # 2) Read raw MP3 bytes from the response object
            audio_bytes = response.read()
        except Exception as e:
            print(f"⚠️ OpenAI TTS generation failed: {e}")
            return

        # 3) Write those bytes to a temporary MP3 file
        tmp_original = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        try:
            tmp_original.write(audio_bytes)
            tmp_original.flush()
            original_path = tmp_original.name
        finally:
            tmp_original.close()

        # 4) If sox is installed, create a sped-up version at 1.25×
        if self.has_sox:
            sped_up_file = tempfile.NamedTemporaryFile(suffix="_fast.mp3", delete=False)
            sped_up_file.close()
            sped_up_path = sped_up_file.name
            try:
                subprocess.run(
                    ["sox", original_path, sped_up_path, "tempo", "1.25"],
                    check=True
                )
                play_path = sped_up_path
            except subprocess.CalledProcessError as e:
                print(f"⚠️ sox speedup failed: {e}. Playing original MP3.")
                play_path = original_path
        else:
            # No sox: just play the original
            play_path = original_path

        # 5) Play the chosen file via afplay
        try:
            subprocess.run(["afplay", play_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Error playing external TTS file: {e}")
        finally:
            # 6) Clean up both files
            if os.path.exists(original_path):
                os.remove(original_path)
            if self.has_sox and os.path.exists(sped_up_path):
                os.remove(sped_up_path)