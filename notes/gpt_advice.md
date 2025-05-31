gpt advice
Below is a complete “Hey Chef” codebase rewritten to use Picovoice Porcupine for wake-word detection instead of Snowboy. It includes all necessary Python files, a Streamlit front-end, and step-by-step instructions for acquiring Porcupine models and installing dependencies.

⸻

📁 Project Structure

Create a new folder (e.g. hey_chef/) and inside it place the following files and folders exactly as shown:

hey_chef/
├── wake_porcupine.py
├── stt_whisper.py
├── llm_client.py
├── tts_engine.py
├── streamlit_app.py
├── requirements.txt
└── porcupine_models/
    ├── hey_chef.ppn
    └── porcupine_params.pv

	•	porcupine_models/hey_chef.ppn – Your custom wake-word model for “Hey Chef” (downloaded from Picovoice Console).
	•	porcupine_models/porcupine_params.pv – The Porcupine engine parameters file (comes with Porcupine SDK).
	•	All other .py files are fully self-contained modules you’ll copy-paste from this guide.
	•	requirements.txt lists required Python packages with suggested version pins.

⸻

1. Obtain & Place Porcupine Models

1.1. Sign up & Create a Wake-Word Model
	1.	Go to https://console.picovoice.ai/ and sign up (it’s free for personal/hobby use).
	2.	Create a new Porcupine project and add a custom wake word “hey chef” (make sure to type lowercase, e.g. hey chef).
	3.	Download the generated model (hey_chef.ppn) and the Porcupine parameters file (porcupine_params.pv). You can download them both from the “Models” tab of your project.
	4.	Place those two files into a folder called porcupine_models/ under your project root:

hey_chef/
└── porcupine_models/
    ├── hey_chef.ppn
    └── porcupine_params.pv



Note:
	•	In free (Hobby) tier, your model will expire every 30 days; you need to re-download and replace the .ppn file to continue using it.
	•	If you ever need a new wake-word or higher usage limits (beyond 3 active users/month), you’ll need a paid plan.

⸻

2. Install System Dependencies

On macOS, you’ll need PortAudio for microphone capture (through PyAudio) and the Porcupine Python SDK.
	1.	Install Homebrew (if you don’t already have it):

/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"


	2.	Install PortAudio:

brew install portaudio


	3.	Install Python 3.10+ (if not already installed):

brew install python@3.10

	•	Make sure python3 and pip3 point to this version.

⸻

3. Install Porcupine SDK & Python Packages
	1.	Clone & install the Porcupine Python wrapper (Picovoice Open Source):

cd hey_chef
git clone https://github.com/Picovoice/porcupine.git
cd porcupine/binding/python
pip3 install .
cd ../../../

What this does:
	•	Clones the official Porcupine repository and installs the Python wheel from binding/python/setup.py.
	•	It provides the pvporcupine module used below.

	2.	Install the remaining Python packages using requirements.txt:
Create a file requirements.txt in hey_chef/ with the following contents:

streamlit==1.30.0
pvporcupine==2.2.0
pyaudio==0.2.11
openai==0.27.0
pyttsx3==2.90
requests==2.31.0
beautifulsoup4==4.12.2

Then run:

cd hey_chef
pip3 install --upgrade pip
pip3 install -r requirements.txt

	•	pvporcupine is the Porcupine Python SDK.
	•	pyaudio lets us capture from the microphone.
	•	openai is the OpenAI Python client for Whisper/GPT.
	•	pyttsx3 is an offline TTS engine on macOS.

⸻

4. Set Environment Variables
	1.	Export your OpenAI API key (replace sk-REPLACE_WITH_YOUR_KEY with your actual key):

export OPENAI_API_KEY="sk-REPLACE_WITH_YOUR_KEY"


	2.	Optionally, you can add that export line to your ~/.zshrc or ~/.bash_profile so it persists across sessions.

⸻

5. Copy-Paste All Python Code Files

Below are the complete contents for each .py file. Create them under hey_chef/ exactly as named.

⸻

5.1. wake_porcupine.py

# wake_porcupine.py
#
# Uses Picovoice Porcupine to detect the wake word “hey chef” on-device.
# Requires:
#   - porcupine_models/hey_chef.ppn       (your trained wake-word model)
#   - porcupine_models/porcupine_params.pv (Porcupine engine parameters)
#   - pyaudio (for microphone capture)
#   - pvporcupine (Porcupine Python SDK)

import pvporcupine
import pyaudio
import signal
import sys
import os

class WakeWordDetector:
    """
    Blocks until the wake word “hey chef” is detected via Porcupine.
    """

    def __init__(self,
                 keyword_path: str = "porcupine_models/hey_chef.ppn",
                 pv_params_path: str = "porcupine_models/porcupine_params.pv",
                 sensitivity: float = 0.7):
        """
        keyword_path: Path to your hey_chef.ppn
        pv_params_path: Path to porcupine_params.pv
        sensitivity: Detection sensitivity (0.0–1.0). Higher = more sensitive (more false positives).
        """
        if not os.path.isfile(keyword_path):
            raise FileNotFoundError(f"Wake-word model not found: {keyword_path}")
        if not os.path.isfile(pv_params_path):
            raise FileNotFoundError(f"Porcupine params file not found: {pv_params_path}")

        # Create the Porcupine instance
        self.porcupine = pvporcupine.create(
            keyword_paths=[keyword_path],
            model_path=pv_params_path,
            sensitivities=[sensitivity]
        )

        # Initialize PyAudio stream
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )

        # Setup SIGINT handler for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, sig, frame):
        """
        Invoked on Ctrl+C. Cleans up and exits.
        """
        self.cleanup()
        sys.exit(0)

    def detect_once(self) -> bool:
        """
        Blocks until the wake word is detected once. Returns True when detected.
        """
        print("👂 Listening for wake word (‘Hey Chef’)…")
        while True:
            pcm = self.stream.read(self.porcupine.frame_length, exception_on_overflow=False)
            pcm_int16 = pvporcupine.util.pv_buffer_to_int16_list(pcm)
            result = self.porcupine.process(pcm_int16)
            if result >= 0:
                # result is the index of the detected keyword in keyword_paths
                print("🟢 Wake word detected!")
                return True

    def cleanup(self):
        """
        Release resources cleanly.
        """
        if hasattr(self, "stream") and self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, "pa") and self.pa is not None:
            self.pa.terminate()
        if hasattr(self, "porcupine") and self.porcupine is not None:
            self.porcupine.delete()


⸻

5.2. stt_whisper.py

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
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        text = transcript.get("text", "").strip()
        print(f"📝 Transcribed: {text!r}")
        return text

    def cleanup(self):
        """
        Cleanly terminate the PyAudio instance.
        """
        self.pa.terminate()


⸻

5.3. llm_client.py

# llm_client.py
#
# A minimal OpenAI GPT-4o client. Replace OPENAI_API_KEY in your environment.

import os
import openai

class LLMClient:
    """
    Wraps calls to OpenAI’s ChatCompletion for GPT-4o.
    """

    def __init__(self, model: str = "gpt-4o"):
        """
        model: which OpenAI model to use (e.g. "gpt-4o", "gpt-4o-mini", etc.)
        """
        if "OPENAI_API_KEY" not in os.environ:
            raise EnvironmentError("Please set the OPENAI_API_KEY environment variable.")
        openai.api_key = os.environ["OPENAI_API_KEY"]
        self.model = model

    def ask(self, recipe_text: str, user_question: str) -> str:
        """
        Sends a combined prompt (system + user) to the LLM, returns its text response.
        """
        system_msg = {
            "role": "system",
            "content": (
                "You are ChefBot, an expert cooking assistant. "
                "The user will supply a full recipe, then ask a question like 'Which ingredients do I need?' "
                "or 'How do I start?' Provide a clear, concise answer focused on cooking instructions."
            )
        }
        user_msg = {
            "role": "user",
            "content": f"Recipe:\n{recipe_text}\n\nQuestion: {user_question}"
        }

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[system_msg, user_msg],
            temperature=0.2,
            max_tokens=500
        )
        reply = response.choices[0].message.content.strip()
        return reply


⸻

5.4. tts_engine.py

# tts_engine.py
#
# A simple pyttsx3-based TTS wrapper. This uses your system’s default voice.

import pyttsx3

class TTSEngine:
    """
    Wraps pyttsx3 for text-to-speech. On macOS, this uses the built-in voices.
    """

    def __init__(self, rate: int = 150, voice_id: str = None):
        """
        rate: speech rate (words per minute)
        voice_id: if you want a specific voice ID (e.g. “com.apple.speech.synthesis.voice.Alex” on macOS).
        """
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", rate)
        if voice_id:
            self.engine.setProperty("voice", voice_id)

    def say(self, text: str):
        """
        Speaks the given text. Blocks until speaking is done.
        """
        self.engine.say(text)
        self.engine.runAndWait()


⸻

5.5. streamlit_app.py

# streamlit_app.py
#
# A minimal Streamlit front-end that:
# 1) Lets you paste a recipe and “Save Recipe”
# 2) Launches the “Hey Chef” voice loop using Porcupine → Whisper → GPT-4o → pyttsx3
#
# Run with: streamlit run streamlit_app.py

import streamlit as st
import threading

from wake_porcupine import WakeWordDetector
from stt_whisper import WhisperSTT
from llm_client import LLMClient
from tts_engine import TTSEngine

# -----------------------------------------------------------------------------
# 1) PAGE SETUP
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Hey Chef", page_icon="🍳", layout="centered")
st.title("🍳 Hey Chef (Prototype)")
st.markdown(
    """
    **Step 1.** Paste or edit your recipe in the box below, then click **Save Recipe**.  
    **Step 2.** Click **Start Listening**.  
    In your terminal/console you’ll see “Listening for ‘Hey Chef’…”.  
    **Step 3.** Say **“Hey Chef”** out loud, then ask your cooking question (e.g., “What ingredients do I need?”).  
    **Step 4.** ChefBot will reply via text-to-speech (pyttsx3) to your default audio output.
    """
)

if "recipe_text" not in st.session_state:
    st.session_state.recipe_text = ""

recipe_input = st.text_area(
    label="Paste your recipe (plain text or markdown):",
    value=st.session_state.recipe_text,
    height=300,
    placeholder=(
        "# Hearty Bean Soup  \n"
        "## Ingredients  \n"
        "- 2 cups dried beans  \n"
        "- 4 cups vegetable broth  \n"
        "- 1 onion, diced  \n"
        "## Instructions  \n"
        "1. Rinse beans and soak overnight ...  \n"
        "2. ..."
    )
)

if st.button("Save Recipe"):
    st.session_state.recipe_text = recipe_input
    st.success("✅ Recipe saved! You can now click **Start Listening** below.")

# -----------------------------------------------------------------------------
# 2) VOICE LOOP (BACKGROUND THREAD)
# -----------------------------------------------------------------------------
def start_voice_loop():
    """
    Runs indefinitely:
      1) Waits for “Hey Chef” via Porcupine
      2) Records user question (Whisper)
      3) Sends recipe + question to GPT-4o
      4) Speaks response (pyttsx3)
    """
    # 2.a) Initialize Porcupine wake-word detector
    keyword_path = "porcupine_models/hey_chef.ppn"
    pv_params_path = "porcupine_models/porcupine_params.pv"
    wwd = WakeWordDetector(keyword_path=keyword_path,
                          pv_params_path=pv_params_path,
                          sensitivity=0.7)

    # 2.b) Initialize Whisper STT
    stt = WhisperSTT(record_seconds=6)

    # 2.c) Initialize LLM client
    llm = LLMClient(model="gpt-4o")

    # 2.d) Initialize TTS
    tts = TTSEngine(rate=150)

    try:
        while True:
            # Block until “hey chef” detected
            wwd.detect_once()

            # Now record & transcribe question
            print("🟢 Wake word detected! Recording your question…")
            wav_path = stt.record_audio()
            user_question = stt.speech_to_text(wav_path)
            print(f"👉 You asked: {user_question}")

            # Fetch saved recipe from Streamlit session
            recipe = st.session_state.get("recipe_text", "").strip()
            if not recipe:
                tts.say("I don't have a recipe yet. Please paste a recipe and save it first.")
                continue

            # Query the LLM
            answer = llm.ask(recipe, user_question)
            print(f"🍲 ChefBot says: {answer}")

            # Speak the answer
            tts.say(answer)

    except Exception as e:
        print(f"⚠️ Voice loop stopped due to error: {e}")
    finally:
        stt.cleanup()
        print("🛑 Voice loop terminated.")

if st.button("Start Listening"):
    thread = threading.Thread(target=start_voice_loop, daemon=True)
    thread.start()
    st.info("🔊 Voice loop started in the background. Check your console for logs.")


⸻

5.6. requirements.txt

streamlit==1.30.0
pvporcupine==2.2.0
pyaudio==0.2.11
openai==0.27.0
pyttsx3==2.90
requests==2.31.0
beautifulsoup4==4.12.2

Feel free to bump these versions to the latest compatible releases, but pinning ensures reproducibility.

⸻

6. Detailed Setup & Execution Steps
	1.	Ensure you have Python 3.10+ installed (macOS via Homebrew is recommended).

brew install python@3.10


	2.	Install PortAudio (for pyaudio):

brew install portaudio


	3.	Clone/prepare your project folder:

mkdir hey_chef
cd hey_chef
# Then create the files above inside this folder.


	4.	Download Porcupine model files:
	•	Sign up at https://console.picovoice.ai/
	•	Create a new Wake-word “hey chef” project
	•	Download hey_chef.ppn and porcupine_params.pv
	•	Place them under hey_chef/porcupine_models/
	5.	Install Porcupine Python SDK:

git clone https://github.com/Picovoice/porcupine.git
cd porcupine/binding/python
pip3 install .
cd ../../..

	•	This installs the pvporcupine package into your Python environment.

	6.	Install remaining Python dependencies:
In hey_chef/, run:

pip3 install --upgrade pip
pip3 install -r requirements.txt


	7.	Set your OpenAI API key:

export OPENAI_API_KEY="sk-REPLACE_WITH_YOUR_OPENAI_KEY"


	8.	Run the Streamlit app:

cd hey_chef
streamlit run streamlit_app.py

	•	Your default browser will open at http://localhost:8501.

	9.	Use the App:
	•	Paste or edit a recipe in the text area (plain text or Markdown).
	•	Click Save Recipe.
	•	Click Start Listening.
	•	Observe your terminal/console: it should print “Listening for wake word (‘Hey Chef’)…”.
	•	Say “Hey Chef” out loud (in moderate volume, quiet environment).
	•	Right after, ask your cooking question (e.g. “What ingredients do I need?”).
	•	The app will record ~6 seconds, transcribe via Whisper, send your saved recipe + question to GPT-4o, and reply via TTS to your default audio device (headphones or speakers).
	10.	Stopping the App:
	•	To stop Streamlit entirely, press Ctrl+C in the console.
	•	The voice loop thread will also terminate at that point.

⸻

7. Tips & Troubleshooting
	1.	Porcupine Model Expiration
	•	In the free hobby tier, your hey_chef.ppn model expires every 30 days.
	•	When it expires, re-login to Picovoice Console, re-download a fresh hey_chef.ppn, overwrite the file in porcupine_models/, and restart the app.
	2.	Adjusting Sensitivity
	•	In WakeWordDetector.__init__, we set sensitivity=0.7.
	•	If Porcupine never triggers, increase to 0.8 or 0.85.
	•	If Porcupine triggers spuriously, reduce to 0.6 or 0.5.
	3.	Audio Device Configuration
	•	Porcupine’s PyAudio stream picks the default system microphone.
	•	If you have multiple input devices (e.g. USB mic, headphone mic), you can specify input_device_index=... when opening PyAudio. Example:

self.stream = self.pa.open(
    rate=self.porcupine.sample_rate,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    input_device_index=2,  # adjust based on `pyaudio.get_device_info_by_index(i)`
    frames_per_buffer=self.porcupine.frame_length
)


	•	Use a small script to list all pa.get_device_info_by_index(i)["name"] and pick the index of your preferred mic.

	4.	Whisper Recording Duration
	•	We record 6 seconds by default.
	•	If your spoken question tends to be longer, you can bump WhisperSTT(record_seconds=6) to record_seconds=8 or 10.
	•	Each extra second of Whisper transcription costs $0.006 per minute ≈ $0.0001 per second.
	5.	LLM Token Limits
	•	If your recipe is very long (> 5 000 tokens), you may hit the LLM’s token limit. In that case, consider sending only the relevant section (e.g. the “Ingredients” portion) or summarising first.
	•	GPT-4o pricing (mid-2025):
	•	$2.50 per 1M input tokens
	•	$10.00 per 1M output tokens
	6.	pyttsx3 Voice Choices
	•	On macOS, pyttsx3 defaults to “Alex” or “Samantha.”
	•	To list voices:

import pyttsx3
e = pyttsx3.init()
for v in e.getProperty("voices"):
    print(v.id, v.name)


	•	To pick a specific voice, pass its voice_id into TTSEngine(voice_id="com.apple.speech.synthesis.voice.Alex").

⸻

8. Final Checklist

Make sure you have:
	•	A folder hey_chef/ containing exactly the files listed above:
	•	wake_porcupine.py
	•	stt_whisper.py
	•	llm_client.py
	•	tts_engine.py
	•	streamlit_app.py
	•	requirements.txt
	•	A subfolder porcupine_models/ with hey_chef.ppn and porcupine_params.pv
	•	Installed PortAudio via Homebrew (brew install portaudio).
	•	Installed Porcupine’s Python SDK by cloning and running pip3 install . in porcupine/binding/python/.
	•	Installed all required Python packages:

pip3 install --upgrade pip
pip3 install -r requirements.txt


	•	Exported your OPENAI_API_KEY in the shell.
	•	Verified that running python3 -c "import pvporcupine; print('Porcupine OK')" does not error.
	•	Run the app with:

cd hey_chef
streamlit run streamlit_app.py



Once all of the above are in place, you will have a fully functional “Hey Chef” assistant that:
	1.	Waits for you to say “Hey Chef” (via Porcupine).
	2.	Records your spoken cooking question (via Whisper).
	3.	Sends your saved recipe + question to GPT-4o (via OpenAI).
	4.	Speaks back the answer (via pyttsx3 TTS).

Enjoy your Porcupine-powered Hey Chef voice assistant!