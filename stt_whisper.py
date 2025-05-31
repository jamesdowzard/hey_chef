# stt_whisper.py
#
# Records a fixed-duration audio clip from the default microphone,
# writes it to a temporary WAV file, and transcribes via OpenAI Whisper.

import pyaudio
import wave
import tempfile
import openai
import os

class WhisperSTT:
    """
    Records a short audio snippet (default 6 seconds) and transcribes with OpenAI Whisper.
    """

    def __init__(self, record_seconds: int = 6, sample_rate: int = 16000, chunk: int = 1024):
        """
        record_seconds: how many seconds to record after wake word
        sample_rate: must match Whisper’s expected sample rate (16 kHz)
        chunk: frames per buffer
        """
        self.record_seconds = record_seconds
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = sample_rate
        self.chunk = chunk
        self.pa = pyaudio.PyAudio()

        # Ensure OPENAI_API_KEY is set
        if "OPENAI_API_KEY" not in os.environ:
            raise EnvironmentError("Please set the OPENAI_API_KEY environment variable.")
        openai.api_key = os.environ["OPENAI_API_KEY"]

    def record_audio(self) -> str:
        """
        Records from the default microphone for self.record_seconds,
        saves to a temp WAV file, and returns its filepath.
        """
        stream = self.pa.open(format=self.format,
                              channels=self.channels,
                              rate=self.rate,
                              input=True,
                              frames_per_buffer=self.chunk)
        frames = []
        print(f"🎤 Recording for {self.record_seconds} seconds…")
        for _ in range(int(self.rate / self.chunk * self.record_seconds)):
            data = stream.read(self.chunk, exception_on_overflow=False)
            frames.append(data)
        print("🛑 Recording complete.")
        stream.stop_stream()
        stream.close()

        # Write to a temp WAV
        temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(temp_wav.name, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.pa.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b"".join(frames))

        return temp_wav.name

    def speech_to_text(self, wav_path: str) -> str:
        """
        Uses OpenAI Whisper (whisper-1) to transcribe the given WAV file.
        Returns the transcribed text.
        """
        with open(wav_path, "rb") as audio_file:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        text = transcript.text.strip()
        print(f"📝 Transcribed: {text!r}")
        return text

    def cleanup(self):
        """
        Cleanly terminate the PyAudio instance.
        """
        self.pa.terminate()