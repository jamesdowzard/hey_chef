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
warnings.filterwarnings(
    "ignore",
    message=".*missing ScriptRunContext.*",
    category=UserWarning,
    module="streamlit.runtime.scriptrunner"
)

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
        self.voice_loop_event = threading.Event()  # Thread-safe control
        self.voice_loop_thread = None
        self._init_session_state()
        self._setup_page()
    
    def _init_session_state(self):
        """Initialize Streamlit session state variables."""
        defaults = {
            'custom_recipe': '',
            'last_answer': '',
            'conversation_history': [],
            'voice_loop_running': False,
            'current_mode': 'normal'
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def _setup_page(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title=self.settings.ui.page_title,
            page_icon=self.settings.ui.page_icon,
            layout=self.settings.ui.layout
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
        sassy_mode: bool
    ):
        """Start the voice interaction loop in a background thread."""
        try:
            # Initialize components
            wwd = WakeWordDetector(
                keyword_path=self.settings.get_wake_word_path(),
                sensitivity=self.settings.audio.wake_word_sensitivity
            )
            
            stt = WhisperSTT(
                model_size=self.settings.audio.whisper_model_size,
                aggressiveness=self.settings.audio.vad_aggressiveness,
                max_silence_sec=self.settings.audio.max_silence_sec
            )
            
            llm = LLMClient(
                model=self.settings.llm.model,
                max_tokens=self.settings.llm.max_tokens,
                temperature=self.settings.llm.temperature,
                sassy_max_tokens=self.settings.llm.sassy_max_tokens,
                sassy_temperature=self.settings.llm.sassy_temperature
            )
            
            tts = TTSEngine(
                macos_voice=self.settings.audio.macos_voice,
                external_voice=self.settings.audio.external_voice,
                macos_rate=self.settings.audio.speech_rate
            )
            
            # Initialize conversation history
            history = None
            if maintain_history:
                system_prompt = get_system_prompt(sassy_mode=sassy_mode)
                history = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here is my recipe:\n{recipe}"}
                ]
            
            print("🎤 Voice loop started. Say 'Hey Chef' to begin!")
            
            # Main voice loop - use threading.Event for control
            while not self.voice_loop_event.is_set():
                try:
                    # Wait for wake word
                    wwd.detect_once()
                    
                    # Record user speech
                    wav_path = stt.record_until_silence()
                    if not wav_path:
                        continue
                    
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
                                sassy_mode=sassy_mode
                            ),
                            start_threshold=80
                        )
                    else:
                        response = llm.ask(
                            recipe_text=(recipe if history is None else ""),
                            user_question=user_question,
                            history=history,
                            sassy_mode=sassy_mode
                        )
                        # For non-streaming, speak the complete response at once
                        tts.say(response)
                        answer_text = response
                    
                    # Update history
                    if history is not None:
                        llm.update_history_with_response(history, answer_text, sassy_mode)
                    
                    # Store response for UI (thread-safe assignment)
                    st.session_state.last_answer = answer_text
                    st.session_state.current_mode = 'sassy' if sassy_mode else 'normal'
                    
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
            
            # Update UI state
            st.session_state.voice_loop_running = False
    
    def _render_header(self):
        """Render the application header."""
        st.title(f"{self.settings.ui.page_icon} Hey Chef")
        
        # Mode indicator
        mode_emoji = "😈" if st.session_state.current_mode == 'sassy' else "😊"
        mode_text = "Sassy Chef Mode" if st.session_state.current_mode == 'sassy' else "Friendly Chef Mode"
        
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
            
            # Mode selection
            st.subheader("🎭 Chef Personality")
            sassy_mode = st.checkbox(
                "Enable Sassy Mode 😈",
                value=self.settings.ui.default_sassy_mode,
                help="Get brutally honest, short, and sarcastic responses!"
            )
            
            if sassy_mode:
                st.warning("⚠️ Sassy mode enabled! Expect attitude and short responses.")
            
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
            
            # Status indicator
            if st.session_state.voice_loop_running:
                st.success("🟢 Listening for 'Hey Chef'...")
                if st.button("🛑 Stop Listening", type="secondary"):
                    self.voice_loop_event.set()  # Signal thread to stop
                    if self.voice_loop_thread and self.voice_loop_thread.is_alive():
                        self.voice_loop_thread.join(timeout=2)  # Wait for thread to finish
                    st.session_state.voice_loop_running = False
                    st.rerun()
            else:
                start_button = st.button(
                    "🎤 Start Listening", 
                    type="primary",
                    help="Start voice interaction"
                )
                
                if start_button:
                    return sassy_mode, use_history, use_streaming, True
            
            return sassy_mode, use_history, use_streaming, False
    
    def _render_recipe_section(self) -> str:
        """Render the recipe selection section."""
        st.subheader("📝 Recipe Selection")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            source = st.radio(
                "Recipe source",
                ("Default", "Notion DB", "Custom"),
                index=0
            )

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
                    choice = st.selectbox("Select a recipe", options)
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
            if st.session_state.current_mode == 'sassy':
                st.markdown(
                    f"""
                    <div style="background-color: #FFE4E1; padding: 15px; border-radius: 10px; border-left: 4px solid #FF6B6B;">
                        <strong>Chef Sass says:</strong><br>
                        <em>"{st.session_state.last_answer}"</em>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div style="background-color: #F0F8FF; padding: 15px; border-radius: 10px; border-left: 4px solid #4CAF50;">
                        <strong>Chef Bot says:</strong><br>
                        "{st.session_state.last_answer}"
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            if st.button("🗑️ Clear Response"):
                st.session_state.last_answer = ""
                st.rerun()
    
    def run(self):
        """Main application entry point."""
        # Render UI components
        self._render_header()
        
        # Sidebar controls
        sassy_mode, use_history, use_streaming, should_start = self._render_sidebar()
        
        # Recipe section
        recipe = self._render_recipe_section()
        
        # Handle voice loop start
        if should_start:
            if not recipe.strip():
                st.error("❌ Please select or enter a recipe before starting.")
            else:
                st.session_state.voice_loop_running = True
                self.voice_loop_event.clear()  # Clear the stop event
                
                # Start voice loop in background thread
                self.voice_loop_thread = threading.Thread(
                    target=self._start_voice_loop,
                    args=(recipe, use_history, use_streaming, sassy_mode),
                    daemon=True
                )
                self.voice_loop_thread.start()
                
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