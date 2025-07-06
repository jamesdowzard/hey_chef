"""
Async text-to-speech service supporting both macOS and OpenAI TTS API.
Converted from the original synchronous implementation to async-compatible service.
"""
import asyncio
import os
import subprocess
import tempfile
import shutil
from typing import Optional, List, AsyncGenerator
from pathlib import Path

from .base import BaseService
from ..core.config import settings


class TTSService(BaseService):
    """
    Async text-to-speech service that can use either:
    - macOS built-in voices with customizable speed
    - OpenAI TTS API with voice selection
    
    Features:
    - Async/await compatible
    - Multiple TTS backends (macOS, OpenAI)
    - Streaming text-to-speech
    - Process management
    - Configurable voices and settings
    """
    
    def __init__(
        self,
        macos_voice: Optional[str] = None,
        external_voice: Optional[str] = None,
        macos_rate: Optional[int] = None,
        use_external: Optional[bool] = None
    ):
        """
        Initialize TTS service.
        
        Args:
            macos_voice: Name of macOS TTS voice
            external_voice: Name of OpenAI TTS voice
            macos_rate: Speech rate for macOS voice (~219 is 1.25x speed)
            use_external: Force external TTS. If None, use config setting
        """
        super().__init__("tts")
        
        self.macos_voice = macos_voice or settings.audio.macos_voice
        self.external_voice = external_voice or settings.audio.external_voice
        self.macos_rate = macos_rate or settings.audio.speech_rate
        self.use_external = use_external if use_external is not None else settings.audio.use_external_tts
        
        # OpenAI client (lazy initialization)
        self.openai_client = None
        
        # Process tracking for cleanup
        self.active_processes: List[subprocess.Popen] = []
        
        # Streaming state
        self._streaming_tasks: List[asyncio.Task] = []
    
    async def _initialize_impl(self) -> None:
        """Initialize TTS service."""
        self.logger.info(f"TTS service initializing: {'external' if self.use_external else 'macOS'} mode")
        
        # Initialize OpenAI client if using external TTS
        if self.use_external:
            await self._init_openai_client()
        
        self.logger.info("TTS service initialized successfully")
    
    async def _cleanup_impl(self) -> None:
        """Clean up TTS resources."""
        # Cancel streaming tasks
        for task in self._streaming_tasks:
            if not task.done():
                task.cancel()
        
        if self._streaming_tasks:
            await asyncio.gather(*self._streaming_tasks, return_exceptions=True)
        self._streaming_tasks.clear()
        
        # Terminate active processes
        await self._cleanup_processes()
    
    async def _init_openai_client(self) -> None:
        """Initialize OpenAI client for TTS."""
        try:
            # Import and initialize in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def create_client():
                import openai
                api_key = settings.openai_api_key
                if not api_key:
                    raise EnvironmentError("OPENAI_API_KEY not set in environment")
                return openai.OpenAI(api_key=api_key)
            
            self.openai_client = await loop.run_in_executor(None, create_client)
            self._store_resource("openai_client", self.openai_client)
            
        except ImportError:
            raise RuntimeError("OpenAI package not installed. Install with: pip install openai")
    
    async def say(self, text: str) -> None:
        """
        Speak the given text.
        
        Args:
            text: Text to speak
        """
        if not text.strip():
            return
        
        if not self._initialized:
            await self.initialize()
        
        async with self.managed_operation("say"):
            if self.use_external and self.openai_client:
                await self._say_openai(text)
            else:
                await self._say_macos(text)
    
    async def _say_macos(self, text: str) -> None:
        """Speak text using macOS built-in TTS."""
        self.logger.info(f"macOS TTS starting: {len(text)} chars")
        
        # Create temporary file for audio
        tmp_file = tempfile.NamedTemporaryFile(suffix=".aiff", delete=False)
        tmp_file.close()
        aiff_path = tmp_file.name
        
        try:
            # Generate audio file
            say_cmd = [
                "say", "-v", self.macos_voice,
                "-r", str(self.macos_rate),
                "-o", aiff_path, text
            ]
            
            process = await asyncio.create_subprocess_exec(
                *say_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                self.logger.warning(f"say command failed: {stderr.decode()}")
                # Try fallback without file output
                await self._say_macos_direct(text)
                return
            
            self.logger.debug(f"Audio file generated: {aiff_path}")
            
            # Play audio file
            await self._play_audio_file(aiff_path)
            
        except Exception as e:
            self.logger.error(f"macOS TTS error: {e}")
            # Try fallback
            try:
                await self._say_macos_direct(text)
            except Exception as fallback_e:
                self.logger.error(f"macOS TTS fallback also failed: {fallback_e}")
        finally:
            # Clean up temporary file
            try:
                os.remove(aiff_path)
            except OSError as e:
                self.logger.warning(f"Failed to remove temp file: {e}")
    
    async def _say_macos_direct(self, text: str) -> None:
        """Speak text using direct say command (fallback)."""
        say_cmd = [
            "say", "-v", self.macos_voice,
            "-r", str(self.macos_rate), text
        ]
        
        process = await asyncio.create_subprocess_exec(
            *say_cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        
        await process.communicate()
        self.logger.debug("Direct say command completed")
    
    async def _say_openai(self, text: str) -> None:
        """Speak text using OpenAI TTS API."""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")
        
        self.logger.info(f"OpenAI TTS starting: {len(text)} chars")
        
        # Create temporary file for audio
        tmp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp_file.close()
        mp3_path = tmp_file.name
        
        try:
            # Generate speech (run in thread pool)
            loop = asyncio.get_event_loop()
            
            def generate_speech():
                response = self.openai_client.audio.speech.create(
                    model="tts-1",
                    voice=self.external_voice,
                    input=text,
                    response_format="mp3"
                )
                return response
            
            response = await loop.run_in_executor(None, generate_speech)
            
            # Save to file (run in thread pool)
            def save_audio():
                with open(mp3_path, "wb") as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
            
            await loop.run_in_executor(None, save_audio)
            self.logger.debug(f"OpenAI audio saved to: {mp3_path}")
            
            # Play audio file
            await self._play_audio_file(mp3_path, speed_up=True)
            
        except Exception as e:
            self.logger.error(f"OpenAI TTS error: {e}")
        finally:
            # Clean up temporary file
            try:
                os.remove(mp3_path)
            except OSError as e:
                self.logger.warning(f"Failed to remove temp file: {e}")
    
    async def _play_audio_file(self, file_path: str, speed_up: bool = False) -> None:
        """
        Play audio file with optional speed adjustment.
        
        Args:
            file_path: Path to audio file
            speed_up: Whether to speed up playback (for MP3 files)
        """
        if speed_up and file_path.endswith('.mp3') and shutil.which("sox") and shutil.which("play"):
            # Use sox/play with tempo adjustment
            play_cmd = ["play", file_path, "tempo", "1.25"]
        else:
            # Use afplay (default macOS player)
            play_cmd = ["afplay", file_path]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *play_cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            
            # Track process for cleanup
            self.active_processes.append(process)
            
            await process.communicate()
            
            # Remove from tracking when done
            if process in self.active_processes:
                self.active_processes.remove(process)
            
            self.logger.debug("Audio playback completed")
            
        except Exception as e:
            self.logger.error(f"Audio playback error: {e}")
    
    async def stream_and_play(
        self,
        text_chunks: AsyncGenerator[str, None],
        start_threshold: int = 80
    ) -> str:
        """
        Stream text chunks and play audio progressively.
        
        Args:
            text_chunks: Async generator yielding text chunks
            start_threshold: Number of chars to buffer before starting playback
            
        Returns:
            Complete assembled text
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.managed_operation("stream_and_play"):
            if self.use_external and self.openai_client:
                return await self._stream_and_play_openai(text_chunks, start_threshold)
            else:
                return await self._stream_and_play_macos(text_chunks)
    
    async def _stream_and_play_macos(self, text_chunks: AsyncGenerator[str, None]) -> str:
        """Stream for macOS - collect all text then speak once."""
        full_text = ""
        async for chunk in text_chunks:
            full_text += chunk
        
        if full_text.strip():
            await self._say_macos(full_text)
        
        return full_text
    
    async def _stream_and_play_openai(
        self,
        text_chunks: AsyncGenerator[str, None],
        start_threshold: int = 80
    ) -> str:
        """Stream with OpenAI TTS - buffer and play in chunks."""
        buffer = ""
        full_text = ""
        first_chunk_played = False
        
        try:
            async for chunk in text_chunks:
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
                            # Start speaking in background
                            task = asyncio.create_task(self._say_openai(to_speak))
                            self._streaming_tasks.append(task)
                            first_chunk_played = True
            
            # Speak any remaining buffered text
            if buffer.strip():
                task = asyncio.create_task(self._say_openai(buffer.strip()))
                self._streaming_tasks.append(task)
            
            # Wait for all speech tasks to complete
            if self._streaming_tasks:
                await asyncio.gather(*self._streaming_tasks, return_exceptions=True)
                self._streaming_tasks.clear()
            
        except Exception as e:
            self.logger.error(f"Streaming TTS error: {e}")
        
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
    
    async def stop_playback(self) -> None:
        """Stop all active audio playback."""
        self.logger.info("Stopping all audio playback")
        
        # Cancel streaming tasks
        for task in self._streaming_tasks:
            if not task.done():
                task.cancel()
        
        if self._streaming_tasks:
            await asyncio.gather(*self._streaming_tasks, return_exceptions=True)
        self._streaming_tasks.clear()
        
        # Terminate active processes
        await self._cleanup_processes()
    
    async def _cleanup_processes(self) -> None:
        """Clean up all active audio processes."""
        if not self.active_processes:
            return
        
        self.logger.debug(f"Cleaning up {len(self.active_processes)} active processes")
        
        # Try to terminate gracefully first
        for process in self.active_processes:
            try:
                process.terminate()
            except Exception as e:
                self.logger.warning(f"Error terminating process: {e}")
        
        # Wait a bit for graceful termination
        await asyncio.sleep(0.1)
        
        # Force kill any remaining processes
        for process in self.active_processes:
            try:
                if process.poll() is None:  # Still running
                    process.kill()
            except Exception as e:
                self.logger.warning(f"Error killing process: {e}")
        
        self.active_processes.clear()
    
    async def get_available_voices(self) -> dict:
        """
        Get available voices for both TTS backends.
        
        Returns:
            Dictionary with available voices
        """
        voices = {
            "macos": [],
            "openai": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        }
        
        try:
            # Get macOS voices
            process = await asyncio.create_subprocess_exec(
                "say", "-v", "?",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            
            if process.returncode == 0:
                lines = stdout.decode().strip().split('\n')
                for line in lines:
                    if line.strip():
                        # Extract voice name (first word before space)
                        voice_name = line.split()[0]
                        voices["macos"].append(voice_name)
        
        except Exception as e:
            self.logger.warning(f"Could not get macOS voices: {e}")
        
        return voices
    
    def get_tts_stats(self) -> dict:
        """
        Get TTS statistics.
        
        Returns:
            Dictionary with TTS stats
        """
        return {
            "use_external": self.use_external,
            "macos_voice": self.macos_voice,
            "external_voice": self.external_voice,
            "macos_rate": self.macos_rate,
            "active_processes": len(self.active_processes),
            "streaming_tasks": len(self._streaming_tasks),
            "is_initialized": self._initialized
        }