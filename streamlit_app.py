import warnings

# Silence only the “missing ScriptRunContext” warning
warnings.filterwarnings(
    "ignore",
    message=".*missing ScriptRunContext.*",
    category=UserWarning,
    module="streamlit.runtime.scriptrunner"
)

import os
import streamlit as st
import threading

from wake_porcupine import WakeWordDetector
from stt_whisper import WhisperSTT
from llm_client import LLMClient, SYSTEM_PROMPT
from tts_engine import TTSEngine

# -----------------------------------------------------------------------------
# 1) PAGE SETUP
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Hey Chef", page_icon="🍳", layout="centered")
st.title("🍳 Hey Chef")
st.markdown(
    """
    **Step 1.** Paste or edit your recipe in the box below.  
    **Step 2.** Configure history and streaming options on the right.  
    **Step 3.** Click **Start Listening**.  
    In your terminal you’ll see “Listening for ‘Hey Chef’…”.  
    **Step 4.** Say **“Hey Chef”** then ask your cooking question.  
    **Step 5.** ChefBot will reply via text‐to‐speech.  
    """
)

# -----------------------------------------------------------------------------
# 2) BACKGROUND THREAD FUNCTION
# -----------------------------------------------------------------------------
def start_voice_loop(recipe: str, maintain_history: bool, streaming: bool):
    print(f"[DEBUG] recipe length = {len(recipe)}")
    # Initialize components
    wwd = WakeWordDetector(keyword_path="porcupine_models/hey_chef.ppn", sensitivity=0.7)
    stt = WhisperSTT(aggressiveness=1, max_silence_sec=1)
    llm = LLMClient(model="gpt-4o")
    tts = TTSEngine(macos_voice="Samantha", external_voice="alloy")

    history = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Here is my recipe:\n{recipe}"}
    ] if maintain_history else None

    try:
        while True:
            wwd.detect_once()
            wav_path = stt.record_until_silence()
            user_question = stt.speech_to_text(wav_path)

            if streaming:
                stream_gen = llm.stream(
                    recipe_text=(recipe if history is None else ""),
                    user_question=user_question,
                    history=history
                )
                answer_text = tts.stream_and_play(stream_gen, start_threshold=80)
            else:
                answer_text = llm.ask(
                    recipe_text=(recipe if history is None else ""),
                    user_question=user_question,
                    history=history
                )
                # Speak full reply via streaming API on single-element generator
                tts.stream_and_play(iter([answer_text]), start_threshold=0)

            if history is not None:
                history.append({"role": "assistant", "content": answer_text})

            # Store for UI
            st.session_state.last_answer = answer_text
    except Exception as e:
        print(f"⚠️ Voice loop stopped: {e}")
    finally:
        stt.cleanup()

# -----------------------------------------------------------------------------
# 3) DISPLAY ANSWER FUNCTION
# -----------------------------------------------------------------------------
def check_and_display_answer():
    ans = st.session_state.get("last_answer", "").strip()
    if ans:
        st.write("**ChefBot says:**")
        st.markdown(f"> {ans}")
        st.session_state.last_answer = ""

# -----------------------------------------------------------------------------
# 4) SESSION_STATE INITIALIZATION
# -----------------------------------------------------------------------------
if "recipe_text" not in st.session_state:
    st.session_state.recipe_text = ""
if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""

# -----------------------------------------------------------------------------
# 5) USER INPUT + CONTROLS LAYOUT
# -----------------------------------------------------------------------------
col1, col2 = st.columns([3, 1])

# Left column: recipe input
with col1:
    recipe_input = st.text_area(
        label="Paste your recipe (plain text or markdown):",
        value=st.session_state.recipe_text,
        height=300,
    )
    if st.button("Save Recipe"):
        st.session_state.recipe_text = recipe_input
        st.success("✅ Recipe saved!")

# Right column: options and start button
with col2:
    st.write("### Options")
    use_history = st.checkbox("Maintain history", value=True)
    use_streaming = st.checkbox("Use streaming", value=False)
    if st.button("Start Listening"):
        recipe_to_use = st.session_state.get("recipe_text", "").strip()
        if not recipe_to_use:
            st.error("❌ Paste & save a recipe first.")
        else:
            thread = threading.Thread(
                target=start_voice_loop,
                args=(recipe_to_use, use_history, use_streaming),
                daemon=True
            )
            thread.start()
            st.success("🔊 Voice loop started. Check console.")

# -----------------------------------------------------------------------------
# 6) RERUN: DISPLAY ANSWER
# -----------------------------------------------------------------------------
check_and_display_answer()