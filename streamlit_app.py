import warnings

# Silence only the “missing ScriptRunContext” warning
warnings.filterwarnings(
    "ignore",
    message=".*missing ScriptRunContext.*",
    category=UserWarning,
    module="streamlit.runtime.scriptrunner"
)

import os
import yaml
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
    **Step 1.** Choose default or custom recipe.  
    **Step 2.** Configure history and streaming on the right.  
    **Step 3.** Click **Start Listening**, then say **“Hey Chef”** and ask your question.  
    """
)

# -----------------------------------------------------------------------------
# 2) LOAD DEFAULT RECIPE
# -----------------------------------------------------------------------------
def load_default_recipe(path: str) -> str:
    try:
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            return data.get('recipe', '') if isinstance(data, dict) else ''
    except Exception:
        return ''

DEFAULT_RECIPE_PATH = os.path.join(os.path.dirname(__file__), 'default_recipe.yaml')
def_recipe = load_default_recipe(DEFAULT_RECIPE_PATH)

# -----------------------------------------------------------------------------
# 3) SESSION_STATE INIT
# -----------------------------------------------------------------------------
if 'custom_recipe' not in st.session_state:
    st.session_state.custom_recipe = ''
if 'last_answer' not in st.session_state:
    st.session_state.last_answer = ''

# -----------------------------------------------------------------------------
# 4) BACKGROUND THREAD
# -----------------------------------------------------------------------------
def start_voice_loop(recipe: str, maintain_history: bool, streaming: bool):
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
                answer_text = tts.stream_and_play(
                    llm.stream(
                        recipe_text=(recipe if history is None else ""),
                        user_question=user_question,
                        history=history
                    ),
                    start_threshold=80
                )
            else:
                resp = llm.ask(
                    recipe_text=(recipe if history is None else ""),
                    user_question=user_question,
                    history=history
                )
                answer_text = tts.stream_and_play(iter([resp]), start_threshold=0)

            if history is not None:
                history.append({"role": "assistant", "content": answer_text})

            st.session_state.last_answer = answer_text
    except Exception as e:
        print(f"⚠️ Voice loop stopped: {e}")
    finally:
        stt.cleanup()

# -----------------------------------------------------------------------------
# 5) DISPLAY ANSWER
# -----------------------------------------------------------------------------
def check_and_display_answer():
    ans = st.session_state.get('last_answer', '').strip()
    if ans:
        st.write("**ChefBot says:**")
        st.markdown(f"> {ans}")
        st.session_state.last_answer = ''

# -----------------------------------------------------------------------------
# 6) UI: recipe selection + controls
# -----------------------------------------------------------------------------
col1, col2 = st.columns([3, 1])

# Left side: choose recipe mode
with col1:
    use_default = st.checkbox("Use default recipe", value=True)
    if use_default:
        st.info("Using default recipe.")
    else:
        recipe_input = st.text_area(
            label="Custom recipe (plain text or markdown):",
            value=st.session_state.custom_recipe,
            height=300,
        )
        if st.button("Save Custom Recipe"):
            st.session_state.custom_recipe = recipe_input
            st.success("✅ Custom recipe saved.")

# Right side: options + start
with col2:
    st.write("### Options")
    use_history = st.checkbox("Maintain history", value=True)
    use_streaming = st.checkbox("Use streaming", value=False)
    if st.button("Start Listening"):
        recipe_to_use = def_recipe if use_default else st.session_state.custom_recipe
        if not recipe_to_use:
            st.error("❌ No recipe available. Ensure default or custom is set.")
        else:
            threading.Thread(
                target=start_voice_loop,
                args=(recipe_to_use, use_history, use_streaming),
                daemon=True
            ).start()
            st.success("🔊 Voice loop started. Check console.")

# -----------------------------------------------------------------------------
# 7) RERUN: show answer
# -----------------------------------------------------------------------------
check_and_display_answer()