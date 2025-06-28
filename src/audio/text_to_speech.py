"""
Text-to-speech engine supporting both macOS and OpenAI TTS API.
"""
import os
import subprocess
import tempfile
import shutil
from typing import Iterator, Optional
from dotenv import load_dotenv

load_dotenv()


class TTSEngine:
    """
    Text-to-speech engine that can use either:
    - macOS built-in voices with customizable speed
    - OpenAI TTS API with voice selection
    """

    def __init__(
        self, 
        macos_voice: str = "Samantha", 
        external_voice: str = "alloy",
        macos_rate: int = 219,
        use_external: Optional[bool] = None
    ):
        """
        Initialize TTS engine.
        
        Args:
            macos_voice: Name of macOS TTS voice
            external_voice: Name of OpenAI TTS voice
            macos_rate: Speech rate for macOS voice (~219 is 1.25x speed)
            use_external: Force external TTS. If None, use USE_EXTERNAL_TTS env var
        """
        self.macos_voice = macos_voice
        self.external_voice = external_voice
        self.macos_rate = macos_rate
        
        # Determine which TTS to use
        if use_external is None:
            self.use_external = bool(os.getenv("USE_EXTERNAL_TTS", "").strip())
        else:
            self.use_external = use_external
            
        # Initialize OpenAI client if using external TTS
        self.openai_client = None
        if self.use_external:
            self._init_openai_client()

    def _init_openai_client(self):
        """Initialize OpenAI client for TTS."""
        try:
            import openai
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise EnvironmentError("OPENAI_API_KEY not set in environment")
            self.openai_client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise RuntimeError("OpenAI package not installed. Install with: pip install openai")

    def say(self, text: str):
        """
        Speak the given text.
        
        Args:
            text: Text to speak
        """
        if not text.strip():
            return
            
        if self.use_external and self.openai_client:
            self._say_openai(text)
        else:
            self._say_macos(text)

    def _say_macos(self, text: str):
        """Speak text using macOS built-in TTS."""
        tmpfile = tempfile.NamedTemporaryFile(suffix=".aiff", delete=False)
        tmpfile.close()
        aiff_path = tmpfile.name

        try:
            # Generate audio file
            subprocess.run([
                "say", "-v", self.macos_voice, 
                "-r", str(self.macos_rate), 
                "-o", aiff_path, text
            ], check=True, capture_output=True)
            
            # Play audio file
            subprocess.run(["afplay", aiff_path], check=True, capture_output=True)
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️ macOS TTS error: {e}")
            # Try fallback without file output
            try:
                subprocess.run([
                    "say", "-v", self.macos_voice, 
                    "-r", str(self.macos_rate), text
                ], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                print("⚠️ macOS TTS fallback also failed")
        finally:
            # Clean up temporary file
            try:
                os.remove(aiff_path)
            except OSError:
                pass

    def _say_openai(self, text: str):
        """Speak text using OpenAI TTS API."""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")
            
        tmpfile = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmpfile.close()
        mp3_path = tmpfile.name

        try:
            # Generate speech
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice=self.external_voice,
                input=text,
                response_format="mp3"
            )
            
            # Save to file
            with open(mp3_path, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
            
            # Speed up and play with sox if available, otherwise use afplay
            if shutil.which("sox") and shutil.which("play"):
                subprocess.run([
                    "play", mp3_path, "tempo", "1.25"
                ], check=True, capture_output=True)
            else:
                # Fallback to afplay (no speed adjustment)
                subprocess.run(["afplay", mp3_path], check=True, capture_output=True)
                
        except Exception as e:
            print(f"⚠️ OpenAI TTS error: {e}")
        finally:
            # Clean up temporary file
            try:
                os.remove(mp3_path)
            except OSError:
                pass

    def stream_and_play(
        self, 
        text_generator: Iterator[str], 
        start_threshold: int = 80
    ) -> str:
        """
        Stream text chunks and play audio progressively.
        
        Args:
            text_generator: Iterator yielding text chunks
            start_threshold: Number of chars to buffer before starting playback
            
        Returns:
            Complete assembled text
        """
        if self.use_external and self.openai_client:
            return self._stream_and_play_openai(text_generator, start_threshold)
        else:
            return self._stream_and_play_macos(text_generator)

    def _stream_and_play_macos(self, text_generator: Iterator[str]) -> str:
        """Stream for macOS - collect all text then speak once."""
        full_text = ""
        for chunk in text_generator:
            full_text += chunk
            
        if full_text.strip():
            self._say_macos(full_text)
        return full_text

    def _stream_and_play_openai(
        self, 
        text_generator: Iterator[str], 
        start_threshold: int = 80
    ) -> str:
        """Stream with OpenAI TTS - buffer and play in chunks."""
        buffer = ""
        full_text = ""
        first_chunk_played = False

        try:
            for chunk in text_generator:
                buffer += chunk
                full_text += chunk
                
                # Start playing when we have enough text
                if not first_chunk_played and len(buffer) >= start_threshold:
                    # Find a good breaking point (sentence end)
                    break_point = self._find_break_point(buffer)
                    if break_point > 0:
                        to_speak = buffer[:break_point].strip()
                        buffer = buffer[break_point:].strip()
                        
                        if to_speak:
                            self._say_openai(to_speak)
                            first_chunk_played = True

            # Speak any remaining buffered text
            if buffer.strip():
                self._say_openai(buffer.strip())
                
        except Exception as e:
            print(f"⚠️ Streaming TTS error: {e}")

        return full_text

    def _find_break_point(self, text: str) -> int:
        """Find a good place to break text for streaming."""
        # Look for sentence endings
        for punct in ['. ', '! ', '? ']:
            pos = text.rfind(punct)
            if pos > 20:  # Ensure minimum chunk size
                return pos + 2
        
        # Fallback to comma or just use threshold
        comma_pos = text.rfind(', ')
        if comma_pos > 20:
            return comma_pos + 2
            
        # If no good break point, use the whole buffer
        return len(text) 