# streamlit_app.py

import os
import streamlit as st
import threading
import warnings

from wake_porcupine import WakeWordDetector
from stt_whisper import WhisperSTT
from llm_client import LLMClient, SYSTEM_PROMPT
from tts_engine import TTSEngine

# Silence Streamlit’s ScriptRunContext warning
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="streamlit.runtime.scriptrunner"
)

# -----------------------------------------------------------------------------
# 1) PAGE SETUP
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Hey Chef", page_icon="🍳", layout="centered")
st.title("🍳 Hey Chef")
st.markdown(
    """
    **Step 1.** Paste or edit your recipe in the box below, then click **Save Recipe**.  
    **Step 2.** Toggle **Maintain History** if you want ChefBot to remember past queries (recipe sent once only).  
    **Step 3.** Click **Start Listening**.  
    In your terminal/console you’ll see “Listening for ‘Hey Chef’…”.  
    **Step 4.** Say **“Hey Chef”** out loud, then ask your cooking question.  
    **Step 5.** ChefBot will reply via text‐to‐speech.  
    """
)

# -----------------------------------------------------------------------------
# 2) SESSION_STATE INITIALIZATION
# -----------------------------------------------------------------------------
if "recipe_text" not in st.session_state:
    st.session_state.recipe_text = ""
if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""

# -----------------------------------------------------------------------------
# 3) USER INPUT: RECIPE & HISTORY TOGGLE
# -----------------------------------------------------------------------------
recipe_input = st.text_area(
    label="Paste your recipe (plain text or markdown):",
    value=st.session_state.recipe_text,
    height=300,
)

if st.button("Save Recipe"):
    st.session_state.recipe_text = recipe_input
    st.success("✅ Recipe saved! Now click **Start Listening**.")

use_history = st.checkbox("Maintain conversation history", value=True)

# -----------------------------------------------------------------------------
# 4) BACKGROUND THREAD FUNCTION
# -----------------------------------------------------------------------------
def start_voice_loop(recipe: str, maintain_history: bool):
    """
    Background thread logic:
      1) Wait for “Hey Chef” via Porcupine
      2) Record & transcribe via Whisper STT
      3) Call LLM (with or without maintaining history)
      4) Speak via TTS
    """
    print(f"[DEBUG] (thread) recipe length = {len(recipe)}")
    preview = recipe[:50] + "..." if len(recipe) > 50 else recipe
    print(f"[DEBUG] (thread) Recipe preview: {preview!r}")

    # a) Initialize Porcupine wake-word detector
    wwd = WakeWordDetector(keyword_path="porcupine_models/hey_chef.ppn", sensitivity=0.7)

    # b) Initialize Whisper STT
    stt = WhisperSTT(record_seconds=6)

    # c) Initialize LLM client
    # llm = LLMClient(model="gpt-4o-mini")
    llm = LLMClient(model="gpt-4o")

    # d) Initialize TTS engine
    tts = TTSEngine(macos_voice="Samantha", external_voice="alloy")

    # e) Prepare local history if requested
    if maintain_history:
        # Create a fresh copy so the thread owns its own list
        history = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"Here is my recipe:\n{recipe}"}
        ]
    else:
        history = None

    try:
        while True:
            # 1) Wait for wake word
            print("[DEBUG] Waiting for wake word…")
            wwd.detect_once()
            print("🟢 Wake word detected! Recording your question…")

            # 2) Record & transcribe
            wav_path = stt.record_audio()
            question = stt.speech_to_text(wav_path)
            print(f"[DEBUG] You asked: {question!r}")

            # 3) Query LLM
            print("[DEBUG] Sending prompt to LLM…")
            if history is not None:
                # history already holds system+recipe, so send only the new question
                answer = llm.ask(recipe_text="", user_question=question, history=history)
                # Append assistant’s reply so next turn retains full context
                history.append({"role": "assistant", "content": answer})
            else:
                # Stateless: send recipe+question each time
                answer = llm.ask(recipe_text=recipe, user_question=question, history=None)

            print(f"[DEBUG] ChefBot’s answer: {answer!r}")

            # 4) Store answer so main thread can render it
            st.session_state.last_answer = answer

            # 5) Speak the answer
            print("[DEBUG] Invoking TTS to speak answer…")
            tts.say(answer)
            print("[DEBUG] Done speaking. Looping back…\n")

    except Exception as e:
        print(f"⚠️ Voice loop stopped due to error: {e}")
    finally:
        stt.cleanup()
        print("🛑 Voice loop terminated.")


# -----------------------------------------------------------------------------
# 5) MAIN-THREAD: START LISTENING BUTTON & DISPLAY ANSWER
# -----------------------------------------------------------------------------
def check_and_display_answer():
    """
    On each Streamlit rerun, if last_answer is nonempty, show it and clear it.
    """
    ans = st.session_state.get("last_answer", "").strip()
    if ans:
        st.write("**ChefBot says:**")
        st.markdown(f"> {ans}")
        # Clear it so we don’t repeatedly display the same answer
        st.session_state.last_answer = ""


if st.button("Start Listening"):
    recipe_to_use = st.session_state.get("recipe_text", "").strip()
    if not recipe_to_use:
        st.error("❌ Paste a recipe and click 'Save Recipe' first.")
    else:
        # Build initial history or None
        if use_history:
            initial_history = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Here is my recipe:\n{recipe_to_use}"}
            ]
        else:
            initial_history = None

        # Start background thread, passing in recipe and a boolean for history
        thread = threading.Thread(
            target=start_voice_loop,
            args=(recipe_to_use, use_history),
            daemon=True
        )
        thread.start()
        st.success("🔊 Voice loop started. Check your console for logs.")

# Every rerun: check if there’s a new answer to display
check_and_display_answer()