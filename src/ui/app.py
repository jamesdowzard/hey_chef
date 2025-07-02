"""
Main Streamlit application for Hey Chef voice assistant.
Includes sassy mode, improved UI, and better error handling.
"""
import warnings
import os
import yaml
import streamlit as st
import threading
from typing import Optional, Dict, Any
from pathlib import Path
import requests

# Silence Streamlit warnings
warnings.filterwarnings("ignore", category=UserWarning)
import logging
logging.getLogger("streamlit").setLevel(logging.ERROR)

from ..audio import WakeWordDetector, WhisperSTT, TTSEngine
from ..ai import LLMClient
from ..config import Settings, get_system_prompt

API_URL = os.getenv("RECIPE_API_URL", "http://localhost:3333")

def fetch_recipes():
    resp = requests.get(f"{API_URL}/recipes")
    resp.raise_for_status()
    return resp.json().get("recipes", [])

def fetch_recipe_details(recipe_id):
    resp = requests.get(f"{API_URL}/recipes/{recipe_id}")
    resp.raise_for_status()
    return resp.json()

def format_notion_recipe(details):
    md = ""
    props = details.get("properties", {})
    for k, v in props.items():
        if v.get("type") == "title":
            title = "".join(t.get("plain_text", "") for t in v.get("title", []))
            md += f"## {title}\n\n"
        elif v.get("type") == "rich_text":
            text = "".join(t.get("plain_text", "") for t in v.get("rich_text", []))
            md += f"**{k}:** {text}\n\n"
        elif v.get("type") == "number":
            md += f"**{k}:** {v.get('number')}\n\n"
        elif v.get("type") == "select" and v.get("select"):
            md += f"**{k}:** {v['select'].get('name')}\n\n"
        elif v.get("type") == "multi_select":
            names = [opt.get("name") for opt in v.get("multi_select", [])]
            md += f"**{k}:** {', '.join(names)}\n\n"
        elif v.get("type") == "date" and v.get("date"):
            start = v['date'].get('start')
            end = v['date'].get('end')
            md += f"**{k}:** {start}" + (f" to {end}" if end else "") + "\n\n"
        elif v.get("type") == "people":
            names = [p.get('name') for p in v.get('people', [])]
            md += f"**{k}:** {', '.join(names)}\n\n"
        elif v.get("type") == "checkbox":
            md += f"**{k}:** {'Yes' if v.get('checkbox') else 'No'}\n\n"
        elif v.get("type") in ('url', 'email', 'phone_number'):
            val = v.get(v['type'])
            md += f"**{k}:** {val}\n\n"

    def render_blocks(blocks):
        text = ""
        for b in blocks:
            t = b.get("type")
            data = b.get(t, {})
            if t == "paragraph":
                text += "".join(rt.get("plain_text", "") for rt in data.get("rich_text", [])) + "\n\n"
            elif t in ("heading_1", "heading_2", "heading_3"):
                level = {"heading_1": "#", "heading_2": "##", "heading_3": "###"}[t]
                text += level + " " + "".join(rt.get("plain_text", "") for rt in data.get("rich_text", [])) + "\n\n"
            elif t in ("bulleted_list_item", "numbered_list_item"):
                prefix = "- " if t == "bulleted_list_item" else "1. "
                text += prefix + "".join(rt.get("plain_text", "") for rt in data.get("rich_text", [])) + "\n"
            elif t == "code":
                lang = data.get("language", "")
                code = data.get("rich_text", [])
                text += "```" + lang + "\n" + (code[0].get("plain_text", "") if code else "") + "\n```\n\n"
            elif t == "image":
                url = data.get("file", {}).get("url") or data.get("external", {}).get("url", "")
                caption = "".join(rt.get("plain_text", "") for rt in data.get("caption", []))
                text += f"![{caption}]({url})\n\n"
            if b.get('children'):
                text += render_blocks(b['children'])
        return text

    content = render_blocks(details.get('content', []))
    md += content
    return md

class ChefApp:
    """Main Hey Chef application class."""
    
    def __init__(self):
        """Initialize the application."""
        self.settings = Settings()
        # Use persistent event and thread from session state for voice loop
        if 'voice_loop_event' not in st.session_state:
            st.session_state.voice_loop_event = threading.Event()
        if 'voice_loop_thread' not in st.session_state:
            st.session_state.voice_loop_thread = None
        self.voice_loop_event = st.session_state.voice_loop_event
        self.voice_loop_thread = st.session_state.voice_loop_thread
        self._init_session_state()
        self._setup_page()
    
    def _init_session_state(self):
        """Initialize Streamlit session state variables."""
        defaults = {
            'custom_recipe': '',
            'last_answer': '',
            'conversation_history': [],
            'voice_loop_running': False,
            'current_mode': 'normal',
            'chef_mode': 'normal',  # Track chef personality mode
            'selected_recipe': '',
            'selected_source': 'Default',
            'selected_notion_choice_index': 0,
            'conversation_state': 'idle',  # idle, listening_for_wake_word, recording, processing
            'models_loaded': False
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def _setup_page(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title=self.settings.ui.page_title,
            page_icon=self.settings.ui.page_icon,
            layout="wide"
        )
    
    def _load_default_recipe(self) -> str:
        """Load the default recipe from YAML file."""
        try:
            recipe_path = self.settings.get_default_recipe_path()
            if os.path.exists(recipe_path):
                with open(recipe_path, 'r') as f:
                    data = yaml.safe_load(f)
                    return data.get('recipe', '') if isinstance(data, dict) else ''
        except Exception as e:
            st.error(f"⚠️ Failed to load default recipe: {e}")
        return ''
    
    def _start_voice_loop(
        self, 
        recipe: str, 
        maintain_history: bool, 
        streaming: bool, 
        chef_mode: str,
        model: str
    ):
        """Start the voice interaction loop in a background thread."""
        try:
            # Initialize components
            wwd = WakeWordDetector(
                keyword_path=self.settings.get_wake_word_path(),
                sensitivity=self.settings.audio.wake_word_sensitivity
            )
            # Allow wake-word detection to be interrupted
            wwd.stop_event = self.voice_loop_event
            
            stt = WhisperSTT(
                model_size=self.settings.audio.whisper_model_size,
                aggressiveness=self.settings.audio.vad_aggressiveness,
                max_silence_sec=self.settings.audio.max_silence_sec
            )
            
            llm = LLMClient(
                model=model,
                max_tokens=self.settings.llm.max_tokens,
                temperature=self.settings.llm.temperature,
                sassy_max_tokens=self.settings.llm.sassy_max_tokens,
                sassy_temperature=self.settings.llm.sassy_temperature,
                gordon_max_tokens=self.settings.llm.gordon_max_tokens,
                gordon_temperature=self.settings.llm.gordon_temperature
            )
            
            tts = TTSEngine(
                macos_voice=self.settings.audio.macos_voice,
                external_voice=self.settings.audio.external_voice,
                macos_rate=self.settings.audio.speech_rate
            )
            
            # Initialize conversation history
            history = None
            if maintain_history:
                system_prompt = get_system_prompt(chef_mode=chef_mode)
                history = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here is my recipe:\n{recipe}"}
                ]
            
            print("🎤 Voice loop started. Say 'Hey Chef' to begin!")
            
            # Update state - models are loaded and ready
            st.session_state.models_loaded = True
            st.session_state.conversation_state = 'listening_for_wake_word'
            
            # Play ready tone to indicate models are loaded
            self._play_ready_tone()
            
            # Main voice loop - use threading.Event for control
            while not self.voice_loop_event.is_set():
                try:
                    # Update state - listening for wake word
                    st.session_state.conversation_state = 'listening_for_wake_word'
                    
                    # Wait for wake word (returns False if stopped)
                    detected = wwd.detect_once()
                    if not detected:
                        break
                    
                    # Wake word detected - play tone and update state
                    self._play_wake_word_tone()
                    st.session_state.conversation_state = 'recording'
                    
                    # Record user speech
                    wav_path = stt.record_until_silence()
                    if not wav_path:
                        continue
                    
                    # Update state - processing
                    st.session_state.conversation_state = 'processing'
                    
                    # Convert speech to text
                    user_question = stt.speech_to_text(wav_path)
                    if not user_question.strip():
                        continue
                    
                    print(f"🗣️ User asked: {user_question}")
                    
                    # Get AI response
                    if streaming:
                        answer_text = tts.stream_and_play(
                            llm.stream(
                                recipe_text=(recipe if history is None else ""),
                                user_question=user_question,
                                history=history,
                                chef_mode=chef_mode
                            ),
                            start_threshold=80
                        )
                    else:
                        response = llm.ask(
                            recipe_text=(recipe if history is None else ""),
                            user_question=user_question,
                            history=history,
                            chef_mode=chef_mode
                        )
                        # For non-streaming, speak the complete response at once
                        tts.say(response)
                        answer_text = response
                    
                    # Update history
                    if history is not None:
                        llm.update_history_with_response(history, answer_text, chef_mode)
                    
                    # Store response for UI (thread-safe assignment)
                    st.session_state.last_answer = answer_text
                    st.session_state.current_mode = chef_mode
                    
                    print(f"🤖 Assistant responded: {answer_text}")
                    
                except Exception as e:
                    print(f"⚠️ Voice loop iteration error: {e}")
                    continue
        
        except Exception as e:
            print(f"⚠️ Voice loop setup error: {e}")
            self.voice_loop_event.set()  # Stop the loop on error
        
        finally:
            # Cleanup
            print("🛑 Voice loop stopped.")
            try:
                if 'stt' in locals():
                    stt.cleanup()
                if 'wwd' in locals():
                    wwd.cleanup()
            except:
                pass

            # Kill any playing audio processes
            self._stop_audio_processes()
            
            # Update UI state
            st.session_state.voice_loop_running = False
            st.session_state.voice_loop_thread = None  # Clear thread reference
            st.session_state.conversation_state = 'idle'
            st.session_state.models_loaded = False
    
    def _stop_audio_processes(self):
        """Kill any running TTS audio processes."""
        import subprocess
        for proc in ["afplay", "play", "say"]:
            try:
                subprocess.run(["pkill", proc], check=False)
            except Exception as e:
                print(f"⚠️ Failed to kill audio process {proc}: {e}")
    
    def _play_tone(self, tone_type: str):
        """Play a tone using macOS system sounds."""
        import subprocess
        import threading
        
        def play_sound():
            try:
                if tone_type == "ready":
                    # Higher pitch beep for ready
                    subprocess.run(["afplay", "/System/Library/Sounds/Tink.aiff"], check=False)
                elif tone_type == "wake_word":
                    # Different sound for wake word detection
                    subprocess.run(["afplay", "/System/Library/Sounds/Pop.aiff"], check=False)
            except Exception as e:
                print(f"⚠️ Failed to play tone: {e}")
        
        # Play sound in background thread to avoid blocking
        threading.Thread(target=play_sound, daemon=True).start()
    
    def _play_ready_tone(self):
        """Play tone when models are loaded and ready."""
        self._play_tone("ready")
    
    def _play_wake_word_tone(self):
        """Play tone when wake word is detected."""
        self._play_tone("wake_word")

    def _render_header(self):
        """Render the application header."""
        st.title(f"{self.settings.ui.page_icon} Hey Chef")
        
        # Status bar at top - only show when listening for wake word
        if st.session_state.voice_loop_running and st.session_state.conversation_state == 'listening_for_wake_word':
            st.success("🟢 Say 'Hey Chef' to ask your question...")
        elif st.session_state.voice_loop_running and st.session_state.conversation_state == 'recording':
            st.info("🎤 Listening... Ask your question now!")
        elif st.session_state.voice_loop_running and st.session_state.conversation_state == 'processing':
            st.warning("⏳ Processing your question...")
        
        # Mode indicator
        mode_indicators = {
            'normal': ("😊", "Friendly Chef Mode"),
            'sassy': ("😈", "Sassy Chef Mode"),
            'gordon_ramsay': ("🔥", "Gordon Ramsay Mode")
        }
        selected_mode = st.session_state.chef_mode  
        mode_emoji, mode_text = mode_indicators.get(selected_mode, ("😊", "Friendly Chef Mode"))
        
        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 20px;">
                <span style="font-size: 24px;">{mode_emoji}</span>
                <span style="font-size: 18px; margin-left: 10px;">{mode_text}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown(
            """
            **How to use:**  
            1️⃣ Choose your recipe (default or custom)  
            2️⃣ Configure your preferences in the sidebar  
            3️⃣ Click **Start Listening** and say **"Hey Chef"** followed by your question  
            """
        )
    
    def _render_sidebar(self):
        """Render the sidebar with controls."""
        with st.sidebar:
            st.header("⚙️ Settings")
            
            # Model selection
            st.subheader("🤖 AI Model")
            selected_model = st.selectbox(
                "Choose GPT Model",
                options=self.settings.llm.available_models,
                index=self.settings.llm.available_models.index(self.settings.llm.model),
                help="Select which OpenAI model to use"
            )
            
            st.divider()
            
            # Mode selection
            st.subheader("🎭 Chef Personality")
            chef_mode = st.radio(
                "Choose your chef personality:",
                options=["normal", "sassy", "gordon_ramsay"],
                format_func=lambda x: {
                    "normal": "😊 Friendly Chef - Helpful and encouraging",
                    "sassy": "😈 Sassy Chef - Brutally honest with attitude",
                    "gordon_ramsay": "🔥 Gordon Ramsay - Explosive Hell's Kitchen mode"
                }[x],
                index=0 if not hasattr(st.session_state, 'chef_mode') else ["normal", "sassy", "gordon_ramsay"].index(st.session_state.chef_mode),
                help="Select the chef personality for your cooking assistant"
            )
            
            # Update session state
            st.session_state.chef_mode = chef_mode
            
            # Mode-specific warnings
            if chef_mode == "sassy":
                st.warning("⚠️ Sassy mode enabled! Expect attitude and short responses.")
            elif chef_mode == "gordon_ramsay":
                st.error("🔥 WARNING: Gordon Ramsay mode! Prepare for explosive, demanding responses!")
            
            st.divider()
            
            # Audio settings
            st.subheader("🔊 Audio Options")
            use_history = st.checkbox(
                "Maintain conversation history",
                value=self.settings.ui.default_use_history,
                help="Keep track of the conversation for context"
            )
            
            use_streaming = st.checkbox(
                "Enable streaming responses",
                value=self.settings.ui.default_use_streaming,
                help="Start speaking as soon as AI begins responding"
            )
            
            st.divider()
            
            # Voice controls
            st.subheader("🎤 Voice Control")
            
            # Show stop button when running
            if st.session_state.voice_loop_running:
                if st.button("🛑 Stop Listening", type="secondary"):
                    self.voice_loop_event.set()  # Signal thread to stop
                    if self.voice_loop_thread and self.voice_loop_thread.is_alive():
                        self.voice_loop_thread.join(timeout=2)  # Wait for thread to finish
                    self._stop_audio_processes()  # Kill any playing audio
                    st.session_state.voice_loop_thread = None  # Clear thread reference
                    st.session_state.voice_loop_running = False
                    st.session_state.conversation_state = 'idle'
                    st.session_state.models_loaded = False
                    st.rerun()
            
            # Always return False for sidebar start; starting handled on main page
            return selected_model, chef_mode, use_history, use_streaming, False
    
    def _render_recipe_section(self) -> str:
        """Render the recipe selection section."""
        st.subheader("📝 Recipe Selection")
        
        col1, col2 = st.columns([5, 1])
        
        with col1:
            # Persist selected recipe source between reruns
            sources = ["Default", "Notion DB", "Custom"]
            default_index = sources.index(st.session_state.selected_source) if st.session_state.selected_source in sources else 0
            source = st.radio(
                "Recipe source",
                sources,
                index=default_index,
                format_func=lambda x: {
                    "Default": "📄 Default",
                    "Notion DB": "🗂️ Notion DB",
                    "Custom": "✏️ Custom"
                }[x],
                horizontal=True
            )
            st.session_state.selected_source = source

            if source == "Default":
                default_recipe = self._load_default_recipe()
                if default_recipe:
                    with st.expander("👀 View default recipe"):
                        st.markdown(default_recipe)
                    return default_recipe
                else:
                    st.error("❌ No default recipe found")
                    source = "Notion DB"

            if source == "Notion DB":
                st.write("Fetching recipes from Notion...")
                try:
                    recipes = fetch_recipes()
                    # Extract recipe names from title property for each recipe
                    options = []
                    for r in recipes:
                        props = r.get("properties", {})
                        # Find the title property (type "title")
                        title_prop = None
                        for prop in props.values():
                            if prop.get("type") == "title":
                                title_prop = prop
                                break
                        if title_prop and title_prop.get("title"):
                            name = next((t.get("plain_text") for t in title_prop["title"] if t.get("plain_text")), "<Unnamed>")
                        else:
                            name = "<Unnamed>"
                        options.append(name)
                    # Persist selected Notion recipe choice index
                    default_notion_index = st.session_state.selected_notion_choice_index if 0 <= st.session_state.selected_notion_choice_index < len(options) else 0
                    choice = st.selectbox("Select a recipe", options, index=default_notion_index)
                    st.session_state.selected_notion_choice_index = options.index(choice)
                    selected = next(r for r, name in zip(recipes, options) if name == choice)
                    details = fetch_recipe_details(selected.get("id"))
                    content_md = format_notion_recipe(details)
                    with st.expander("👀 View selected recipe"):
                        st.markdown(content_md)
                    return content_md
                except Exception as e:
                    st.error(f"❌ Failed to load recipes: {e}")
                    source = "Custom"

            if source == "Custom":
                recipe_input = st.text_area(
                    label="Custom recipe (plain text or markdown):",
                    value=st.session_state.custom_recipe,
                    height=300,
                    placeholder="Enter your recipe here..."
                )
                col_save, col_clear = st.columns(2)
                with col_save:
                    if st.button("💾 Save Recipe", type="secondary"):
                        st.session_state.custom_recipe = recipe_input
                        st.success("✅ Custom recipe saved!")
                with col_clear:
                    if st.button("🗑️ Clear Recipe", type="secondary"):
                        st.session_state.custom_recipe = ""
                        st.rerun()
                return recipe_input

        with col2:
            st.info(
                """
                **Recipe Tips:**
                - Include ingredients and instructions
                - Add cooking times and temperatures
                - Mention serving sizes
                - Use clear, simple language
                """
            )

        return ""
    
    def _render_last_response(self):
        """Display the last AI response if available."""
        if st.session_state.last_answer:
            st.subheader("💬 Last Response")
            
            # Style based on mode
            mode_styles = {
                'normal': {
                    'bg_color': '#F0F8FF',
                    'border_color': '#4CAF50',
                    'title': 'Chef Bot says:',
                    'style': 'normal'
                },
                'sassy': {
                    'bg_color': '#FFE4E1',
                    'border_color': '#FF6B6B',
                    'title': 'Chef Sass says:',
                    'style': 'italic'
                },
                'gordon_ramsay': {
                    'bg_color': '#FFF5EE',
                    'border_color': '#FF4500',
                    'title': 'CHEF RAMSAY SHOUTS:',
                    'style': 'bold'
                }
            }
            
            current_style = mode_styles.get(st.session_state.current_mode, mode_styles['normal'])
            
            # Format the message based on style
            if current_style['style'] == 'italic':
                message_format = f'<em>"{st.session_state.last_answer}"</em>'
            elif current_style['style'] == 'bold':
                message_format = f'<strong>"{st.session_state.last_answer}"</strong>'
            else:
                message_format = f'"{st.session_state.last_answer}"'
            
            st.markdown(
                f"""
                <div style="background-color: {current_style['bg_color']}; padding: 15px; border-radius: 10px; border-left: 4px solid {current_style['border_color']};">
                    <strong>{current_style['title']}</strong><br>
                    {message_format}
                </div>
                """,
                unsafe_allow_html=True
            )
            
            if st.button("🗑️ Clear Response"):
                st.session_state.last_answer = ""
                st.rerun()
    
    def run(self):
        """Main application entry point."""
        # Sidebar controls (update mode; no start here)
        selected_model, chef_mode, use_history, use_streaming, _ = self._render_sidebar()

        # Render header after mode is set
        self._render_header()

        # Main page voice controls (start/stop)
        start_main = False
        stop_requested = False
        col_ctrl1, col_ctrl2 = st.columns([1, 3])
        
        if st.session_state.voice_loop_running:
            # Show dynamic button text based on state
            if st.session_state.conversation_state == 'listening_for_wake_word':
                button_text = "🟢 Listening for 'Hey Chef'"
            elif st.session_state.conversation_state == 'recording':
                button_text = "🎤 Recording"
            elif st.session_state.conversation_state == 'processing':
                button_text = "⏳ Processing"
            else:
                button_text = "🟢 Listening"
                
            if col_ctrl1.button(button_text, key="main_status_button", type="primary", disabled=True):
                pass  # Disabled button, no action
            if col_ctrl2.button("🛑 Stop", key="main_stop_listening", type="secondary"):
                stop_requested = True
        else:
            if col_ctrl1.button("🎤 Start Listening", key="main_start_listening", type="primary", help="Start voice interaction"):
                start_main = True
                
        # Handle stop action immediately
        if stop_requested:
            self.voice_loop_event.set()
            if self.voice_loop_thread and self.voice_loop_thread.is_alive():
                self.voice_loop_thread.join(timeout=2)
            self._stop_audio_processes()
            st.session_state.voice_loop_thread = None  # Clear thread reference
            st.session_state.voice_loop_running = False
            st.session_state.conversation_state = 'idle'
            st.session_state.models_loaded = False
            st.rerun()
        should_start = start_main

        # Recipe section (cached during active voice loop to avoid repeated GETs)
        if st.session_state.voice_loop_running:
            recipe = st.session_state.selected_recipe
        else:
            recipe = self._render_recipe_section()
        
        # Handle voice loop start
        if should_start:
            if not recipe.strip():
                st.error("❌ Please select or enter a recipe before starting.")
            else:
                # Cache selected recipe to avoid re-fetch on reruns
                st.session_state.selected_recipe = recipe
                st.session_state.voice_loop_running = True
                st.session_state.conversation_state = 'idle'  # Will change to listening_for_wake_word once models load
                st.session_state.models_loaded = False
                self.voice_loop_event.clear()  # Clear the stop event
                
                # Start voice loop in background thread
                self.voice_loop_thread = threading.Thread(
                    target=self._start_voice_loop,
                    args=(recipe, use_history, use_streaming, chef_mode, selected_model),
                    daemon=True
                )
                self.voice_loop_thread.start()
                st.session_state.voice_loop_thread = self.voice_loop_thread  # Persist thread
                
                st.success("🔊 Voice assistant started! Say 'Hey Chef' and ask your question.")
                st.rerun()
        
        # Display last response
        self._render_last_response()
        
        # Auto-refresh to show responses (only if voice loop is running)
        if st.session_state.voice_loop_running:
            import time
            time.sleep(1)  # Slightly longer sleep to reduce CPU usage
            st.rerun()


def main():
    """Entry point for the Streamlit app."""
    app = ChefApp()
    app.run()


if __name__ == "__main__":
    main() 