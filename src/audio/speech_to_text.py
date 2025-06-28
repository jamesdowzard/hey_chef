"""
Speech-to-text using OpenAI Whisper with voice activity detection.
"""
import os
import wave
import webrtcvad
import sounddevice as sd
from tempfile import NamedTemporaryFile
from typing import Optional
import urllib.error


class WhisperSTT:
    """
    Records from microphone until silence detected, then transcribes using Whisper.
    """

    def __init__(
        self,
        model_size: str = "tiny",
        aggressiveness: int = 2,
        max_silence_sec: float = 0.5,
        sample_rate: int = 16000
    ):
        """
        Initialize speech-to-text engine.
        
        Args:
            model_size: Whisper model size ("tiny", "base", "small", etc.)
            aggressiveness: VAD aggressiveness (0-3, higher = more aggressive)
            max_silence_sec: Seconds of silence before stopping recording
            sample_rate: Audio sample rate
        """
        self.sample_rate = sample_rate
        self.frame_duration_ms = 30  # 10, 20, or 30 ms supported by WebRTC VAD
        self.frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)
        
        # VAD setup
        self.vad = webrtcvad.Vad(aggressiveness)
        self.max_silence_frames = int((max_silence_sec * 1000) / self.frame_duration_ms)
        
        # Audio stream (lazy initialization)
        self.stream: Optional[sd.RawInputStream] = None
        
        # Load Whisper model
        self._load_whisper_model(model_size)

    def _load_whisper_model(self, model_size: str):
        """Load Whisper model with error handling."""
        print(f"Loading Whisper '{model_size}' model...")
        try:
            import whisper
            self.model = whisper.load_model(model_size)
            print("Model loaded successfully.")
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Failed to download Whisper model weights. "
                f"Please ensure internet access or pre-download: "
                f"`whisper --download-model {model_size}`"
            ) from e
        except ImportError:
            raise RuntimeError(
                "Whisper not installed. Install with: pip install openai-whisper"
            )

    def _open_stream(self):
        """Open audio input stream if not already open."""
        if self.stream is None:
            try:
                self.stream = sd.RawInputStream(
                    samplerate=self.sample_rate,
                    blocksize=self.frame_size,
                    dtype="int16",
                    channels=1
                )
                self.stream.start()
            except Exception as e:
                raise RuntimeError(f"Failed to open audio stream: {e}")

    def _read_frame(self) -> Optional[bytes]:
        """Read one audio frame from the stream."""
        try:
            data, _ = self.stream.read(self.frame_size)
            return data.tobytes() if hasattr(data, "tobytes") else bytes(data)
        except Exception as e:
            print(f"⚠️ Error reading audio frame: {e}")
            return None

    def record_until_silence(self) -> str:
        """
        Record audio until silence is detected.
        
        Returns:
            Path to temporary WAV file containing the recording
        """
        print("🎤 Listening...")
        self._open_stream()

        frames = []
        triggered = False
        silence_count = 0

        try:
            while True:
                frame = self._read_frame()
                if frame is None:
                    break

                is_speech = self.vad.is_speech(frame, sample_rate=self.sample_rate)

                if not triggered:
                    # Wait for speech to begin
                    if is_speech:
                        triggered = True
                        frames.append(frame)
                else:
                    # Recording in progress
                    frames.append(frame)
                    if not is_speech:
                        silence_count += 1
                        if silence_count > self.max_silence_frames:
                            print("🛑 Silence detected.")
                            break
                    else:
                        silence_count = 0

        except KeyboardInterrupt:
            print("🛑 Recording interrupted.")
        except Exception as e:
            print(f"⚠️ Recording error: {e}")

        if not frames:
            print("⚠️ No speech captured.")
            return ""

        # Save to temporary WAV file
        return self._save_frames_to_wav(frames)

    def _save_frames_to_wav(self, frames: list) -> str:
        """Save audio frames to a temporary WAV file."""
        tmp = NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp.name
        tmp.close()

        try:
            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(b"".join(frames))
            
            print(f"✅ Saved recording to {tmp_path}")
            return tmp_path
        except Exception as e:
            # Clean up on error
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            raise RuntimeError(f"Failed to save audio file: {e}")

    def speech_to_text(self, wav_path: str) -> str:
        """
        Transcribe WAV file using Whisper.
        
        Args:
            wav_path: Path to WAV file to transcribe
            
        Returns:
            Transcribed text (empty string if transcription fails)
        """
        if not wav_path or not os.path.isfile(wav_path):
            return ""

        try:
            result = self.model.transcribe(wav_path, fp16=False)
            text = result.get("text", "").strip()
            print(f"📝 Transcribed: '{text}'")
            return text
        except Exception as e:
            print(f"⚠️ Transcription failed: {e}")
            return ""
        finally:
            # Clean up temporary file
            try:
                os.remove(wav_path)
            except OSError:
                pass

    def cleanup(self):
        """Clean up audio resources."""
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup() 