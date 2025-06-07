# tts_engine_external.py
#
# A TTS engine that uses OpenAI’s speech endpoint, with incremental‐playback support.

import os
import tempfile
import subprocess
import shutil
from dotenv import load_dotenv

load_dotenv()  # ensure OPENAI_API_KEY is set

try:
    import openai
except ImportError:
    raise ImportError("Please install openai: pip install openai")

class ExternalTTSEngine:
    """
    - `say(text)` does a one-off TTS call + playback.
    - `stream_and_play(text_generator, start_threshold=80)` buffers tokens from
       any iterator of strings, starts playback once the buffer length exceeds
       start_threshold, then continues until exhausted, and RETURNS the full text.
    """

    def __init__(self, voice: str = "alloy"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY not set in environment")
        openai.api_key = api_key

        self.voice = voice
        self.has_sox = bool(shutil.which("sox"))

    def say(self, text: str):
        """One-off TTS → write MP3 → optional sox speed-up → afplay."""
        try:
            resp = openai.audio.speech.create(model="tts-1", voice=self.voice, input=text)
            audio = resp.read()
        except Exception as e:
            print(f"⚠️ OpenAI TTS failed: {e}")
            return

        # write MP3
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.write(audio); tmp.flush(); path = tmp.name; tmp.close()

        # optional speed-up
        play_path = path
        if self.has_sox:
            fast = tempfile.NamedTemporaryFile(suffix="_fast.mp3", delete=False)
            fast.close()
            try:
                subprocess.run(["sox", path, fast.name, "tempo", "1.25"], check=True)
                play_path = fast.name
            except subprocess.CalledProcessError:
                play_path = path

        # playback + cleanup
        try:
            subprocess.run(["afplay", play_path], check=True)
        finally:
            for p in {path, play_path}:
                if os.path.exists(p):
                    os.remove(p)

    def stream_and_play(self, text_generator, start_threshold: int = 80) -> str:
        """
        text_generator: any iterator yielding str chunks (e.g. LLMClient.stream()).
        Buffers until start_threshold chars, then calls self.say(buffer)
        and continues flushing each remaining chunk directly.
        Returns the full accumulated text.
        """
        full_text = ""
        buffer = ""
        started = False

        for chunk in text_generator:
            buffer += chunk
            full_text += chunk

            if not started and len(buffer) >= start_threshold:
                self.say(buffer)
                started = True
                buffer = ""

        # final flush
        if buffer:
            self.say(buffer)

        return full_text