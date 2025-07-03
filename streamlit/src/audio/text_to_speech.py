"""
Text-to-speech engine supporting both macOS and OpenAI TTS API.
"""
import os
import subprocess
import tempfile
import shutil
from typing import Iterator, Optional, List
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
        use_external: Optional[bool] = None,
        process_tracker: Optional[List[subprocess.Popen]] = None
    ):
        """
        Initialize TTS engine.
        
        Args:
            macos_voice: Name of macOS TTS voice
            external_voice: Name of OpenAI TTS voice
            macos_rate: Speech rate for macOS voice (~219 is 1.25x speed)
            use_external: Force external TTS. If None, use USE_EXTERNAL_TTS env var
            process_tracker: List to track spawned audio processes
        """
        self.macos_voice = macos_voice
        self.external_voice = external_voice
        self.macos_rate = macos_rate
        self.logger = get_logger()
        self.process_tracker = process_tracker or []
        
        # Determine which TTS to use
        if use_external is None:
            self.use_external = bool(os.getenv("USE_EXTERNAL_TTS", "").strip())
        else:
            self.use_external = use_external
        
        self.logger.log_audio_event("TTS_INIT", f"TTS engine initialized: {'external' if self.use_external else 'macOS'} mode")
            
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
        
        self.logger.log_audio_event("TTS_START", f"macOS TTS starting: {len(text)} chars")

        try:
            # Generate audio file
            say_process = subprocess.run([
                "say", "-v", self.macos_voice, 
                "-r", str(self.macos_rate), 
                "-o", aiff_path, text
            ], check=True, capture_output=True)
            
            self.logger.log_audio_event("TTS_GENERATED", f"Audio file generated: {aiff_path}")
            
            # Play audio file - track this process
            afplay_process = subprocess.Popen(["afplay", aiff_path], 
                                           stdout=subprocess.DEVNULL, 
                                           stderr=subprocess.DEVNULL)
            self.process_tracker.append(afplay_process)
            self.logger.log_audio_event("TTS_PLAY", f"Playing audio file", afplay_process.pid)
            
            # Wait for playback to complete
            afplay_process.wait()
            if afplay_process in self.process_tracker:
                self.process_tracker.remove(afplay_process)
            self.logger.log_audio_event("TTS_COMPLETE", f"Playback completed", afplay_process.pid)
            
        except subprocess.CalledProcessError as e:
            self.logger.log_error("TTS_MACOS", f"macOS TTS error: {e}")
            # Try fallback without file output
            try:
                say_direct = subprocess.Popen([
                    "say", "-v", self.macos_voice, 
                    "-r", str(self.macos_rate), text
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.process_tracker.append(say_direct)
                self.logger.log_audio_event("TTS_FALLBACK", f"Using direct say command", say_direct.pid)
                
                say_direct.wait()
                if say_direct in self.process_tracker:
                    self.process_tracker.remove(say_direct)
                self.logger.log_audio_event("TTS_FALLBACK_COMPLETE", f"Direct say completed", say_direct.pid)
                
            except subprocess.CalledProcessError as fallback_e:
                self.logger.log_error("TTS_FALLBACK", f"macOS TTS fallback also failed: {fallback_e}")
        finally:
            # Clean up temporary file
            try:
                os.remove(aiff_path)
                self.logger.log_audio_event("TTS_CLEANUP", f"Temporary file removed: {aiff_path}")
            except OSError as e:
                self.logger.log_error("TTS_CLEANUP", f"Failed to remove temp file: {e}")

    def _say_openai(self, text: str):
        """Speak text using OpenAI TTS API."""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")
            
        tmpfile = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmpfile.close()
        mp3_path = tmpfile.name
        
        self.logger.log_audio_event("TTS_OPENAI_START", f"OpenAI TTS starting: {len(text)} chars")

        try:
            # Generate speech
            self.logger.log_audio_event("TTS_OPENAI_API", f"Requesting speech generation from OpenAI")
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice=self.external_voice,
                input=text,
                response_format="mp3"
            )
            
            # Save to file
            self.logger.log_audio_event("TTS_OPENAI_SAVE", f"Saving audio to: {mp3_path}")
            with open(mp3_path, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
            
            # Speed up and play with sox if available, otherwise use afplay
            if shutil.which("sox") and shutil.which("play"):
                play_process = subprocess.Popen([
                    "play", mp3_path, "tempo", "1.25"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.process_tracker.append(play_process)
                self.logger.log_audio_event("TTS_OPENAI_PLAY", f"Playing with sox/play", play_process.pid)
                
                play_process.wait()
                if play_process in self.process_tracker:
                    self.process_tracker.remove(play_process)
                self.logger.log_audio_event("TTS_OPENAI_COMPLETE", f"Sox playback completed", play_process.pid)
            else:
                # Fallback to afplay (no speed adjustment)
                afplay_process = subprocess.Popen(["afplay", mp3_path], 
                                               stdout=subprocess.DEVNULL, 
                                               stderr=subprocess.DEVNULL)
                self.process_tracker.append(afplay_process)
                self.logger.log_audio_event("TTS_OPENAI_AFPLAY", f"Playing with afplay fallback", afplay_process.pid)
                
                afplay_process.wait()
                if afplay_process in self.process_tracker:
                    self.process_tracker.remove(afplay_process)
                self.logger.log_audio_event("TTS_OPENAI_AFPLAY_COMPLETE", f"Afplay completed", afplay_process.pid)
                
        except Exception as e:
            self.logger.log_error("TTS_OPENAI", f"OpenAI TTS error: {e}")
        finally:
            # Clean up temporary file
            try:
                os.remove(mp3_path)
                self.logger.log_audio_event("TTS_OPENAI_CLEANUP", f"Temporary file removed: {mp3_path}")
            except OSError as e:
                self.logger.log_error("TTS_OPENAI_CLEANUP", f"Failed to remove temp file: {e}")

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