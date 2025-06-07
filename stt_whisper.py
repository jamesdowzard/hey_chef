# stt_whisper.py
#
# Records from the default microphone until the user stops speaking (detected via VAD),
# saves to a temporary WAV file, then calls the OpenAI Whisper API (new v1.x interface) to transcribe.

import os
import wave
import webrtcvad
import sounddevice as sd
import numpy as np

from tempfile import NamedTemporaryFile
from dotenv import load_dotenv

# Load OPENAI_API_KEY from .env
load_dotenv()
import openai

if "OPENAI_API_KEY" not in os.environ or not os.environ["OPENAI_API_KEY"].strip():
    raise EnvironmentError("Please set OPENAI_API_KEY in your .env before running.")
openai.api_key = os.environ["OPENAI_API_KEY"]


class WhisperSTT:
    """
    Continuously listens to the mic until the user stops speaking (detected via VAD).
    Saves the captured audio to a temporary WAV, then uses OpenAI's Whisper API (v1.x) to transcribe.
    """

    def __init__(self, aggressiveness: int = 2, max_silence_sec: float = 0.5):
        """
        aggressiveness: VAD aggressiveness (0–3). 0 = least aggressive, 3 = most aggressive.
        max_silence_sec: how many seconds of consecutive “no speech” before deciding the user is done.
        """
        # Whisper expects 16 kHz, 16-bit PCM, mono WAV
        self.sample_rate = 16000
        self.frame_duration_ms = 30  # WebRTC VAD supports 10, 20, or 30 ms frames
        self.frame_size = int(self.sample_rate * (self.frame_duration_ms / 1000.0))  # samples per frame

        self.vad = webrtcvad.Vad(aggressiveness)
        self.max_silence_frames = int((max_silence_sec * 1000) / self.frame_duration_ms)

        # sounddevice stream will be opened lazily
        self.stream = None

    def _open_stream(self):
        """
        Open a sounddevice RawInputStream with 16 kHz / 16-bit / mono and blocksize = frame_size.
        """
        if self.stream is None:
            self.stream = sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=self.frame_size,
                dtype="int16",  # 16-bit PCM
                channels=1,     # mono
            )
            self.stream.start()

    def _read_frame(self):
        """
        Read exactly one frame’s worth of bytes from the sounddevice stream.
        Returns raw bytes or None on failure.
        """
        try:
            data, _ = self.stream.read(self.frame_size)
            # If data is a NumPy array, use .tobytes(); otherwise wrap in bytes()
            if hasattr(data, "tobytes"):
                return data.tobytes()
            else:
                return bytes(data)
        except Exception as e:
            print(f"⚠️ Error reading audio frame: {e}")
            return None

    def record_until_silence(self) -> str:
        """
        Records from the mic until “max_silence_sec” of consecutive silence is detected.
        Returns the path to a temporary WAV file containing the captured speech.
        """
        print("🎤 Listening for speech… (speak now)")
        self._open_stream()

        frames = []
        triggered = False
        silence_frame_count = 0

        while True:
            frame = self._read_frame()
            if frame is None:
                # Could not read from mic – break
                break

            is_speech = self.vad.is_speech(frame, sample_rate=self.sample_rate)

            if not triggered:
                # Haven’t seen speech yet
                if is_speech:
                    triggered = True
                    frames.append(frame)
                    silence_frame_count = 0
                # else: keep waiting for first speech
            else:
                # Already in speech mode; continue buffering until enough silence
                frames.append(frame)
                if not is_speech:
                    silence_frame_count += 1
                    if silence_frame_count > self.max_silence_frames:
                        # Enough consecutive silence → end recording
                        print("🛑 Silence detected; finishing recording.")
                        break
                else:
                    # Reset silence counter on any speech frame
                    silence_frame_count = 0

        # If no speech was detected at all, return an empty string
        if not frames:
            print("⚠️ No speech detected; returning empty path.")
            return ""

        # Write buffered frames to a temporary WAV file
        tmp = NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp.name
        tmp.close()

        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16 bits = 2 bytes
            wf.setframerate(self.sample_rate)
            wf.writeframes(b"".join(frames))

        print(f"✅ Recorded speech to {tmp_path}")
        return tmp_path

    def speech_to_text(self, wav_path: str) -> str:
        """
        Sends the WAV at `wav_path` to OpenAI Whisper API (v1.x) and returns the transcribed text.
        """
        if not wav_path or not os.path.isfile(wav_path):
            return ""

        try:
            with open(wav_path, "rb") as audio_file:
                response = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                text = response.text.strip()
        except Exception as e:
            print(f"⚠️ Whisper API call failed: {e}")
            text = ""

        # Clean up the temporary WAV file
        try:
            os.remove(wav_path)
        except OSError:
            pass

        print(f"📝 Transcribed: {text!r}")
        return text

    def cleanup(self):
        """
        Gracefully close the sounddevice stream.
        """
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None