# stt_whisper.py
#
# Records from the default microphone until the user stops speaking (detected via VAD),
# saves to a temporary WAV file, then runs a local Whisper model to transcribe in real-time.

import os
import wave
import webrtcvad
import sounddevice as sd
from tempfile import NamedTemporaryFile
import urllib.error

class WhisperSTT:
    """
    Continuously listens to the mic until the user stops speaking (detected via VAD),
    then transcribes using a local Whisper model loaded at runtime.
    """

    def __init__(
        self,
        model_size: str = "tiny",
        aggressiveness: int = 2,
        max_silence_sec: float = 0.5
    ):
        """
        model_size: one of "tiny", "base", "small", etc. Ensure model weights are already cached locally
        (e.g. via `whisper --download-model tiny` or by running once with internet).
        aggressiveness: VAD aggressiveness (0–3). 0 = least aggressive, 3 = most aggressive.
        max_silence_sec: how many seconds of consecutive silence before stopping.
        """
        # audio settings
        self.sample_rate = 16000
        self.frame_duration_ms = 30  # 10, 20, or 30 ms
        self.frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)

        # VAD setup
        self.vad = webrtcvad.Vad(aggressiveness)
        self.max_silence_frames = int((max_silence_sec * 1000) / self.frame_duration_ms)

        # sounddevice stream (lazy)
        self.stream = None

        # Lazy import of Whisper to avoid Streamlit watcher issues
        print(f"Loading Whisper '{model_size}' model...")
        try:
            import whisper
            self.model = whisper.load_model(model_size)
        except urllib.error.URLError as e:
            raise RuntimeError(
                "Failed to download Whisper model weights due to a certificate error.\n"
                "Please ensure you have internet access with a valid CA chain, or pre-download the model: `whisper --download-model {model_size}`"
            ) from e
        print("Model loaded and warmed.")

    def _open_stream(self):
        if self.stream is None:
            self.stream = sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=self.frame_size,
                dtype="int16",
                channels=1
            )
            self.stream.start()

    def _read_frame(self):
        try:
            data, _ = self.stream.read(self.frame_size)
            return data.tobytes() if hasattr(data, "tobytes") else bytes(data)
        except Exception as e:
            print(f"⚠️ Error reading audio frame: {e}")
            return None

    def record_until_silence(self) -> str:
        """
        Record until max_silence_sec of silence is detected.
        Returns path to WAV file.
        """
        print("🎤 Listening...")
        self._open_stream()

        frames = []
        triggered = False
        silence_count = 0

        while True:
            frame = self._read_frame()
            if frame is None:
                break

            is_speech = self.vad.is_speech(frame, sample_rate=self.sample_rate)

            if not triggered:
                if is_speech:
                    triggered = True
                    frames.append(frame)
                # otherwise, keep waiting
            else:
                frames.append(frame)
                if not is_speech:
                    silence_count += 1
                    if silence_count > self.max_silence_frames:
                        print("🛑 Silence detected.")
                        break
                else:
                    silence_count = 0

        if not frames:
            print("⚠️ No speech captured.")
            return ""

        tmp = NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = tmp.name
        tmp.close()

        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(b"".join(frames))

        print(f"✅ Saved WAV to {tmp_path}")
        return tmp_path

    def speech_to_text(self, wav_path: str) -> str:
        """
        Transcribe WAV using local Whisper model.
        """
        if not wav_path or not os.path.isfile(wav_path):
            return ""

        try:
            result = self.model.transcribe(wav_path, fp16=False)
            text = result.get("text", "").strip()
        except Exception as e:
            print(f"⚠️ Local transcription failed: {e}")
            text = ""

        # Cleanup
        try:
            os.remove(wav_path)
        except OSError:
            pass

        print(f"📝 Transcribed: '{text}'")
        return text

    def cleanup(self):
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None


if __name__ == "__main__":
    stt = WhisperSTT(model_size="tiny", aggressiveness=2, max_silence_sec=0.5)
    wav = stt.record_until_silence()
    if wav:
        print(stt.speech_to_text(wav))
    stt.cleanup()