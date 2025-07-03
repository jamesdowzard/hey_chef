"""
Main Streamlit application for Hey Chef voice assistant.
Includes sassy mode, improved UI, and better error handling.
"""
import warnings
import os
import sys

# Comprehensive warning suppression - must be first
warnings.filterwarnings("ignore")
import logging
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger("streamlit").setLevel(logging.ERROR)

# Suppress all Streamlit warnings and logging
class NullHandler(logging.Handler):
    def emit(self, record):
        pass

# Apply null handler to all loggers
for name in logging.Logger.manager.loggerDict:
    logging.getLogger(name).addHandler(NullHandler())
    logging.getLogger(name).setLevel(logging.CRITICAL)

import yaml
import streamlit as st
import threading
from typing import Optional, Dict, Any, List
from pathlib import Path
import requests
import subprocess
import signal
import psutil

from ..audio import WakeWordDetector, WhisperSTT, TTSEngine
from ..ai import LLMClient
from ..config import Settings, get_system_prompt
from ..utils.logger import get_logger

API_URL = os.getenv("RECIPE_API_URL", "http://localhost:3333")

# Cache for recipes to avoid repeated API calls
_recipes_cache = None
_recipe_details_cache = {}
_server_connected = None

def check_notion_server():
    """Check if Notion server is available."""
    global _server_connected
    if _server_connected is not None:
        return _server_connected
    
    try:
        resp = requests.get(f"{API_URL}/health", timeout=2)
        _server_connected = resp.status_code == 200
    except:
        _server_connected = False
    return _server_connected

def fetch_recipes():
    """Fetch recipes with caching and error handling."""
    global _recipes_cache
    
    if _recipes_cache is not None:
        return _recipes_cache
    
    if not check_notion_server():
        return []
    
    try:
        resp = requests.get(f"{API_URL}/recipes", timeout=5)
        resp.raise_for_status()
        _recipes_cache = resp.json().get("recipes", [])
        return _recipes_cache
    except Exception as e:
        st.warning(f"Could not fetch recipes from Notion: {e}")
        return []

def fetch_recipe_details(recipe_id):
    """Fetch recipe details with caching."""
    global _recipe_details_cache
    
    if recipe_id in _recipe_details_cache:
        return _recipe_details_cache[recipe_id]
    
    if not check_notion_server():
        return {}
    
    try:
        resp = requests.get(f"{API_URL}/recipes/{recipe_id}", timeout=10)
        resp.raise_for_status()
        details = resp.json()
        _recipe_details_cache[recipe_id] = details
        return details
    except Exception as e:
        st.warning(f"Could not fetch recipe details: {e}")
        return {}

def clear_notion_cache():
    """Clear the Notion cache to force refresh."""
    global _recipes_cache, _recipe_details_cache, _server_connected
    _recipes_cache = None
    _recipe_details_cache = {}
    _server_connected = None

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
        # Initialize logging
        self.logger = get_logger()
        # Audio process tracking
        self.active_audio_processes: List[subprocess.Popen] = []
        # Use persistent event and thread from session state for voice loop
        if 'voice_loop_event' not in st.session_state:
            st.session_state.voice_loop_event = threading.Event()
        if 'voice_loop_thread' not in st.session_state:
            st.session_state.voice_loop_thread = None
        self.voice_loop_event = st.session_state.voice_loop_event
        self.voice_loop_thread = st.session_state.voice_loop_thread
        self._init_session_state()
        self._setup_page()
        self._preload_models()
        
    def _debug_print(self, message: str):
        """Print to terminal and log to file for debugging."""
        print(message)
        # Also log to the master log for easier review
        self.logger.log_state_change("DEBUG", "TERMINAL_OUTPUT", message)
    
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
            'models_loaded': False,
            'current_question': '',  # Current user question
            'current_response': '',  # Current model response
            'response_chunks': [],  # For typewriter effect
            'response_complete': False,
            'chat_messages': [],  # List of chat messages [{type: 'user'/'chef', content: str, timestamp: str, response_time: float}]
            'current_response_start_time': None,
            'notion_server_checked': False
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
    
    def _preload_models(self):
        """Pre-load Whisper model at app startup for faster response times."""
        if 'whisper_loaded' not in st.session_state:
            st.session_state.whisper_loaded = False
            st.session_state.models_loading = True
            
        # Check Notion server connection in background (non-blocking)
        if not st.session_state.get('notion_server_checked', False):
            st.session_state.notion_server_checked = True
            if check_notion_server():
                # Pre-fetch recipes in background
                try:
                    fetch_recipes()  # This will cache the results
                except:
                    pass  # Silently fail, user can retry later
            
        # Only load if not already loaded (with proper locking)
        if not st.session_state.whisper_loaded:
            # Use a lock to prevent duplicate loading
            if st.session_state.get('whisper_loading_in_progress', False):
                # Another process is already loading, skip
                return
            
            # Set lock to prevent concurrent loading
            st.session_state.whisper_loading_in_progress = True
            st.session_state.whisper_loading_started = True
            
            # Show loading message
            loading_placeholder = st.empty()
            loading_placeholder.info("🔄 Loading Whisper model...")
            
            try:
                from ..audio import WhisperSTT
                # Create and initialize Whisper model
                stt = WhisperSTT(
                    model_size=self.settings.audio.whisper_model_size,
                    aggressiveness=self.settings.audio.vad_aggressiveness,
                    max_silence_sec=self.settings.audio.max_silence_sec
                )
                
                # Store in session state for reuse
                st.session_state.whisper_model = stt
                st.session_state.whisper_loaded = True
                st.session_state.models_loading = False
                
                loading_placeholder.success("✅ Whisper model ready!")
                # Only play ready tone once per session
                if not st.session_state.get('ready_tone_played', False):
                    self._play_ready_tone()
                    st.session_state.ready_tone_played = True
                
            except Exception as e:
                print(f"❌ Failed to load Whisper model: {str(e)}")
                st.session_state.whisper_loaded = False
                st.session_state.models_loading = False
                st.session_state.whisper_loading_started = False  # Reset so it can try again
                loading_placeholder.error(f"❌ Failed to load Whisper model: {e}")
            finally:
                # Always release the lock
                st.session_state.whisper_loading_in_progress = False
    
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
        # Start session logging
        recipe_type = "Custom" if recipe and recipe != self._load_default_recipe() else "Default"
        self.logger.start_session(chef_mode, recipe_type, streaming)
        self.logger.log_state_change("idle", "voice_loop_starting", f"model={model}, history={maintain_history}")
        
        try:
            # Environment validation first
            self._debug_print(f"\n🔍 Validating environment setup...")
            
            # Check PICO_ACCESS_KEY
            import os
            pico_key = os.getenv("PICO_ACCESS_KEY")
            if not pico_key:
                self._debug_print(f"❌ PICO_ACCESS_KEY not found in environment!")
                self.logger.log_error("ENV_VALIDATION", "PICO_ACCESS_KEY missing", "Required for wake word detection")
                return
            else:
                self._debug_print(f"✅ PICO_ACCESS_KEY found (length: {len(pico_key)})")
            
            # Check OpenAI API key
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                self._debug_print(f"❌ OPENAI_API_KEY not found in environment!")
                self.logger.log_error("ENV_VALIDATION", "OPENAI_API_KEY missing", "Required for LLM")
                return
            else:
                self._debug_print(f"✅ OPENAI_API_KEY found (length: {len(openai_key)})")
            
            # Check wake word model file
            wake_word_path = self.settings.get_wake_word_path()
            if not os.path.exists(wake_word_path):
                self._debug_print(f"❌ Wake word model not found at: {wake_word_path}")
                self.logger.log_error("ENV_VALIDATION", f"Wake word model missing: {wake_word_path}")
                return
            else:
                self._debug_print(f"✅ Wake word model found: {wake_word_path}")
            
            # Initialize components with detailed logging
            self._debug_print(f"\n🔧 Initializing voice loop components...")
            self._debug_print(f"📁 Wake word model path: {self.settings.get_wake_word_path()}")
            self._debug_print(f"🎯 Sensitivity: {self.settings.audio.wake_word_sensitivity}")
            
            wwd = WakeWordDetector(
                keyword_path=self.settings.get_wake_word_path(),
                sensitivity=self.settings.audio.wake_word_sensitivity
            )
            print(f"✅ Wake word detector initialized successfully")
            # Allow wake-word detection to be interrupted
            wwd.stop_event = self.voice_loop_event
            
            # Use pre-loaded Whisper model (must be available)
            if st.session_state.get('whisper_loaded', False) and 'whisper_model' in st.session_state:
                stt = st.session_state.whisper_model
                print(f"✅ Using pre-loaded Whisper model")
            else:
                # Model should have been preloaded - this is an error condition
                print(f"❌ Whisper model not available! Please refresh the page.")
                st.error("❌ Whisper model not available. Please refresh the page.")
                self.logger.log_error("VOICE_LOOP_SETUP", "Whisper model not available", "Pre-loaded model missing")
                return
            
            print(f"🤖 Initializing LLM client with model: {model}")
            llm = LLMClient(
                model=model,
                max_tokens=self.settings.llm.max_tokens,
                temperature=self.settings.llm.temperature,
                sassy_max_tokens=self.settings.llm.sassy_max_tokens,
                sassy_temperature=self.settings.llm.sassy_temperature,
                gordon_max_tokens=self.settings.llm.gordon_max_tokens,
                gordon_temperature=self.settings.llm.gordon_temperature
            )
            print(f"✅ LLM client initialized")
            
            print(f"🔊 Initializing TTS engine...")
            tts = TTSEngine(
                macos_voice=self.settings.audio.macos_voice,
                external_voice=self.settings.audio.external_voice,
                macos_rate=self.settings.audio.speech_rate,
                process_tracker=self.active_audio_processes
            )
            print(f"✅ TTS engine initialized")
            
            # Initialize conversation history
            history = None
            if maintain_history:
                system_prompt = get_system_prompt(chef_mode=chef_mode)
                history = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Here is my recipe:\n{recipe}"}
                ]
            
            self.logger.log_state_change("voice_loop_starting", "listening_for_wake_word", "Voice loop started successfully")
            
            # Update state - models are loaded and ready
            st.session_state.models_loaded = True
            st.session_state.conversation_state = 'listening_for_wake_word'
            
            # Print status to terminal
            print(f"\n🎤 Hey Chef is listening! Say 'Hey Chef' to start...")
            print("=" * 50)
            
            # Main voice loop - use threading.Event for control
            print(f"🔄 Starting main voice interaction loop...")
            loop_count = 0
            while not self.voice_loop_event.is_set():
                try:
                    loop_count += 1
                    print(f"🔁 Voice loop iteration #{loop_count}")
                    
                    # Update state - listening for wake word
                    st.session_state.conversation_state = 'listening_for_wake_word'
                    
                    # Wait for wake word (returns False if stopped)
                    print(f"👂 Calling wake word detector...")
                    detected = wwd.detect_once()
                    print(f"🔍 Wake word detection result: {detected}")
                    
                    if not detected:
                        print(f"❌ Wake word detection returned False, breaking loop")
                        break
                    
                    # Wake word detected - play tone and update state
                    self._play_wake_word_tone()
                    st.session_state.conversation_state = 'recording'
                    
                    # Wait for tone to finish before starting to listen (reduced for responsiveness)
                    import time
                    time.sleep(0.5)
                    
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
                    
                    self.logger.log_user_action("VOICE_QUESTION", user_question)
                    
                    # Print user question to terminal for real-time monitoring
                    print(f"\n🗣️  USER: {user_question}")
                    print("-" * 50)
                    
                    # Add user message to chat
                    import time
                    from datetime import datetime
                    current_time = datetime.now().strftime("%H:%M:%S")
                    
                    # Initialize chat_messages if not exists
                    if not hasattr(st.session_state, 'chat_messages') or st.session_state.chat_messages is None:
                        st.session_state.chat_messages = []
                    
                    # Add user question to chat history
                    st.session_state.chat_messages.append({
                        'type': 'user',
                        'content': user_question,
                        'timestamp': current_time
                    })
                    
                    # Update UI with user question
                    st.session_state.current_question = user_question
                    st.session_state.current_response = ""
                    st.session_state.response_chunks = []
                    st.session_state.response_complete = False
                    st.session_state.current_response_start_time = time.time()
                    
                    # Get AI response
                    if streaming:
                        # Custom streaming with typewriter effect
                        def stream_with_typewriter():
                            chunks = []
                            for chunk in llm.stream(
                                recipe_text=(recipe if history is None else ""),
                                user_question=user_question,
                                history=history,
                                chef_mode=chef_mode
                            ):
                                chunks.append(chunk)
                                st.session_state.response_chunks = chunks.copy()
                                yield chunk
                        
                        answer_text = tts.stream_and_play(
                            stream_with_typewriter(),
                            start_threshold=80
                        )
                    else:
                        response = llm.ask(
                            recipe_text=(recipe if history is None else ""),
                            user_question=user_question,
                            history=history,
                            chef_mode=chef_mode
                        )
                        # For non-streaming, show complete response immediately
                        st.session_state.response_chunks = [response]
                        st.session_state.response_complete = True
                        tts.say(response)
                        answer_text = response
                    
                    # Update history
                    if history is not None:
                        llm.update_history_with_response(history, answer_text, chef_mode)
                    
                    # Calculate response time
                    response_time = time.time() - st.session_state.current_response_start_time
                    
                    # Initialize chat_messages if not exists
                    if not hasattr(st.session_state, 'chat_messages') or st.session_state.chat_messages is None:
                        st.session_state.chat_messages = []
                    
                    # Add chef response to chat history
                    st.session_state.chat_messages.append({
                        'type': 'chef',
                        'content': answer_text,
                        'timestamp': datetime.now().strftime("%H:%M:%S"),
                        'response_time': f" ({response_time:.1f}s)"
                    })
                    
                    # Print AI response to terminal for real-time monitoring
                    chef_names = {'normal': '🤖 CHEF BOT', 'sassy': '😈 CHEF SASS', 'gordon_ramsay': '🔥 CHEF RAMSAY'}
                    chef_name = chef_names.get(chef_mode, '🤖 CHEF BOT')
                    print(f"\n{chef_name}: {answer_text}")
                    print(f"⏱️  Response time: {response_time:.1f}s")
                    print("=" * 50)
                    
                    # Mark response as complete and store final answer
                    st.session_state.current_response = answer_text
                    st.session_state.response_complete = True
                    st.session_state.last_answer = answer_text
                    st.session_state.current_mode = chef_mode
                    st.session_state.current_response_start_time = None
                    
                    # Clear current conversation state for next question
                    st.session_state.current_question = ""
                    st.session_state.current_response = ""
                    st.session_state.response_chunks = []
                    st.session_state.response_complete = False
                    
                    self.logger.log_state_change("processing", "response_complete", f"Assistant responded with {len(answer_text)} characters")
                    
                except Exception as e:
                    print(f"❌ ERROR in voice loop iteration #{loop_count}: {str(e)}")
                    print(f"🔧 Exception type: {type(e).__name__}")
                    import traceback
                    print(f"📍 Traceback: {traceback.format_exc()}")
                    self.logger.log_error("VOICE_LOOP_ITERATION", str(e), "During main voice loop iteration")
                    continue
        
        except Exception as e:
            print(f"❌ CRITICAL ERROR during voice loop setup: {str(e)}")
            print(f"🔧 Exception type: {type(e).__name__}")
            import traceback
            print(f"📍 Full traceback:")
            traceback.print_exc()
            self.logger.log_error("VOICE_LOOP_SETUP", str(e), "During voice loop initialization")
            self.logger.end_session(success=False, error_msg=f"Setup error: {e}")
            self.voice_loop_event.set()  # Stop the loop on error
        
        finally:
            # Cleanup
            print(f"\n🧹 Voice loop cleanup started...")
            self.logger.log_state_change("voice_loop_running", "cleanup", "Voice loop stopped")
            try:
                if 'stt' in locals():
                    print(f"🧹 Cleaning up STT...")
                    stt.cleanup()
                    self.logger.log_audio_event("CLEANUP", "STT cleanup completed")
                    print(f"✅ STT cleanup completed")
                if 'wwd' in locals():
                    print(f"🧹 Cleaning up wake word detector...")
                    wwd.cleanup()
                    self.logger.log_audio_event("CLEANUP", "Wake word detector cleanup completed")
                    print(f"✅ Wake word detector cleanup completed")
            except Exception as e:
                print(f"❌ Cleanup error: {e}")
                self.logger.log_error("CLEANUP", f"Component cleanup failed: {e}")

            # Kill any playing audio processes
            self._stop_audio_processes()
            
            # Update UI state
            st.session_state.voice_loop_running = False
            st.session_state.voice_loop_thread = None  # Clear thread reference
            st.session_state.conversation_state = 'idle'
            st.session_state.models_loaded = False
            # Clear conversation display
            st.session_state.current_question = ""
            st.session_state.current_response = ""
            st.session_state.response_chunks = []
            st.session_state.response_complete = False
            st.session_state.chat_messages = []
            st.session_state.current_response_start_time = None
            
            # End session logging
            self.logger.end_session(success=True)
    
    def _stop_audio_processes(self):
        """Stop tracked audio processes gracefully."""
        stopped_count = 0
        failed_count = 0
        
        # Stop tracked processes first
        for process in self.active_audio_processes[:]:  # Copy list to avoid modification during iteration
            try:
                if process.poll() is None:  # Process is still running
                    pid = process.pid
                    self.logger.log_audio_event("TERMINATING", f"Graceful termination of tracked process", pid)
                    
                    # Try graceful termination first
                    process.terminate()
                    try:
                        process.wait(timeout=2)  # Wait up to 2 seconds
                        stopped_count += 1
                        self.logger.log_audio_event("TERMINATED", f"Process terminated gracefully", pid)
                    except subprocess.TimeoutExpired:
                        # Force kill if graceful termination fails
                        process.kill()
                        process.wait()
                        stopped_count += 1
                        self.logger.log_audio_event("KILLED", f"Process force-killed after timeout", pid)
                else:
                    # Process already finished
                    stopped_count += 1
                
                self.active_audio_processes.remove(process)
                
            except Exception as e:
                failed_count += 1
                self.logger.log_error("AUDIO_CLEANUP", f"Failed to stop tracked process: {e}")
        
        # Fallback: find and stop audio processes by name (safer approach)
        audio_processes = ["afplay", "play", "say"]
        for proc_name in audio_processes:
            try:
                # Use psutil to find processes by name
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'] == proc_name:
                        try:
                            pid = proc.info['pid']
                            proc_obj = psutil.Process(pid)
                            proc_obj.terminate()
                            proc_obj.wait(timeout=2)
                            stopped_count += 1
                            self.logger.log_audio_event("TERMINATED", f"Found and terminated {proc_name}", pid)
                        except (psutil.TimeoutExpired, psutil.NoSuchProcess):
                            try:
                                proc_obj.kill()
                                stopped_count += 1
                                self.logger.log_audio_event("KILLED", f"Force-killed {proc_name}", pid)
                            except psutil.NoSuchProcess:
                                pass  # Process already gone
                        except Exception as e:
                            failed_count += 1
                            self.logger.log_error("AUDIO_CLEANUP", f"Failed to stop {proc_name}: {e}")
            except Exception as e:
                self.logger.log_error("AUDIO_CLEANUP", f"Failed to find {proc_name} processes: {e}")
        
        # Log summary
        if stopped_count > 0 or failed_count > 0:
            self.logger.log_audio_event("CLEANUP_COMPLETE", f"Stopped: {stopped_count}, Failed: {failed_count}")
        
        # Clear the process list
        self.active_audio_processes.clear()
    
    def _play_tone(self, tone_type: str):
        """Play a tone using macOS system sounds."""
        import threading
        
        def play_sound():
            try:
                sound_file = None
                if tone_type == "ready":
                    sound_file = "/System/Library/Sounds/Tink.aiff"
                elif tone_type == "wake_word":
                    sound_file = "/System/Library/Sounds/Pop.aiff"
                
                if sound_file:
                    # Start the process and track it
                    process = subprocess.Popen(["afplay", sound_file], 
                                             stdout=subprocess.DEVNULL, 
                                             stderr=subprocess.DEVNULL)
                    self.active_audio_processes.append(process)
                    self.logger.log_audio_event("TONE_START", f"Playing {tone_type} tone", process.pid)
                    
                    # Wait for completion and clean up
                    process.wait()
                    if process in self.active_audio_processes:
                        self.active_audio_processes.remove(process)
                    self.logger.log_audio_event("TONE_END", f"Finished {tone_type} tone", process.pid)
                    
            except Exception as e:
                self.logger.log_error("TONE_PLAY", f"Failed to play {tone_type} tone: {e}")
        
        # Play sound in background thread to avoid blocking
        threading.Thread(target=play_sound, daemon=True).start()
    
    def _play_ready_tone(self):
        """Play tone when models are loaded and ready."""
        self._play_tone("ready")
    
    def _play_wake_word_tone(self):
        """Play tone when wake word is detected."""
        self._play_tone("wake_word")
    
    def _render_conversation_display(self):
        """Render the chat-style conversation display."""
        st.markdown("---")
        st.markdown("### 💬 Conversation")
        
        # Create scrollable chat container
        st.markdown(
                """
                <style>
                .chat-container {
                    max-height: 400px;
                    overflow-y: auto;
                    padding: 10px;
                    border: 1px solid #e0e0e0;
                    border-radius: 10px;
                    background-color: #fafafa;
                }
                </style>
            """,
            unsafe_allow_html=True
        )
        
        # Create chat container
        chat_container = st.container()
        
        # Initialize chat_messages if not exists
        if not hasattr(st.session_state, 'chat_messages') or st.session_state.chat_messages is None:
            st.session_state.chat_messages = []
        
        # Limit chat history to last 20 messages to prevent memory issues
        if len(st.session_state.chat_messages) > 20:
            st.session_state.chat_messages = st.session_state.chat_messages[-20:]
        
        with chat_container:
            # Display all chat messages
            for i, msg in enumerate(st.session_state.chat_messages):
                self._render_chat_message(msg)
            
            # Show current active conversation if in progress
            if st.session_state.current_question and not any(
                msg['content'] == st.session_state.current_question and msg['type'] == 'user' 
                for msg in st.session_state.chat_messages
            ):
                # Show current user question
                self._render_chat_message({
                    'type': 'user',
                    'content': st.session_state.current_question,
                    'timestamp': 'now'
                })
            
            # Show current response being typed
            if st.session_state.response_chunks or (st.session_state.conversation_state == 'processing' and st.session_state.current_question):
                partial_text = "".join(st.session_state.response_chunks)
                
                # Calculate response time if available
                response_time_str = ""
                if st.session_state.current_response_start_time:
                    import time
                    current_time = time.time() - st.session_state.current_response_start_time
                    response_time_str = f" ({current_time:.1f}s)"
                
                if partial_text:
                    self._render_chat_message({
                        'type': 'chef',
                        'content': partial_text + "▌",  # Add cursor
                        'timestamp': 'typing...',
                        'response_time': response_time_str
                    })
                else:
                    self._render_chat_message({
                        'type': 'chef',
                        'content': "_Thinking..._",
                        'timestamp': 'typing...',
                        'response_time': response_time_str
                    })
            
            # Show status when waiting
            elif st.session_state.conversation_state == 'listening_for_wake_word':
                st.info("🟢 Say 'Hey Chef' to ask a question...")
            elif st.session_state.conversation_state == 'recording':
                st.info("🎤 Listening... Ask your question now!")
            
            # Auto-scroll marker (invisible element at bottom)
            st.markdown('<div id="chat-bottom"></div>', unsafe_allow_html=True)
            
        # Auto-scroll JavaScript
        st.markdown(
            """
            <script>
            var element = document.getElementById("chat-bottom");
            if (element) {
                element.scrollIntoView({behavior: "smooth"});
            }
            </script>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("---")
    
    def _render_chat_message(self, message):
        """Render a single chat message with styling."""
        if message['type'] == 'user':
            # User message - right aligned, blue background
            st.markdown(
                f"""
                <div style="text-align: right; margin: 10px 0;">
                    <div style="display: inline-block; background-color: #e3f2fd; padding: 10px 15px; 
                                border-radius: 18px 18px 4px 18px; max-width: 70%; text-align: left;">
                        <strong>🗣️ You:</strong><br>
                        {message['content']}
                        <div style="font-size: 0.8em; color: #666; margin-top: 5px;">
                            {message.get('timestamp', '')}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            # Chef message - left aligned, chef mode colored
            mode_colors = {
                'normal': '#f0f8ff',
                'sassy': '#ffe4e1', 
                'gordon_ramsay': '#fff5ee'
            }
            bg_color = mode_colors.get(st.session_state.chef_mode, '#f0f8ff')
            
            # Chef name with response time
            chef_names = {
                'normal': '🤖 Chef Bot',
                'sassy': '😈 Chef Sass',
                'gordon_ramsay': '🔥 Chef Ramsay'
            }
            chef_name = chef_names.get(st.session_state.chef_mode, '🤖 Chef Bot')
            response_time = message.get('response_time', '')
            
            st.markdown(
                f"""
                <div style="text-align: left; margin: 10px 0;">
                    <div style="display: inline-block; background-color: {bg_color}; padding: 10px 15px;
                                border-radius: 18px 18px 18px 4px; max-width: 70%; text-align: left;">
                        <strong>{chef_name}{response_time}:</strong><br>
                        {message['content']}
                        <div style="font-size: 0.8em; color: #666; margin-top: 5px;">
                            {message.get('timestamp', '')}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

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
                    # Clear conversation display
                    st.session_state.current_question = ""
                    st.session_state.current_response = ""
                    st.session_state.response_chunks = []
                    st.session_state.response_complete = False
                    st.rerun()
            
            # Always return False for sidebar start; starting handled on main page
            return selected_model, chef_mode, use_history, use_streaming, False
    
    def _render_recipe_section(self) -> str:
        """Render the recipe selection section with tabs."""
        st.subheader("📝 Recipe Selection")
        
        # Use tabs instead of radio buttons
        tab1, tab2, tab3 = st.tabs(["📄 Default", "🗂️ Notion DB", "✏️ Custom"])
        
        recipe_content = ""
        
        with tab1:
            default_recipe = self._load_default_recipe()
            if default_recipe:
                st.markdown("**Default Recipe:**")
                st.markdown(default_recipe)
                recipe_content = default_recipe
            else:
                st.error("❌ No default recipe found")
        
        with tab2:
            # Check server connection status
            if not check_notion_server():
                st.error("❌ Notion server not available. Please check if the server is running.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Retry Connection", key="retry_notion"):
                        clear_notion_cache()
                        st.rerun()
                with col2:
                    if st.button("🗑️ Clear Cache", key="clear_notion_cache"):
                        clear_notion_cache()
                        st.success("Cache cleared!")
            else:
                try:
                    # Show loading state if needed
                    if _recipes_cache is None:
                        with st.spinner("Loading recipes from Notion..."):
                            recipes = fetch_recipes()
                    else:
                        recipes = fetch_recipes()
                        
                    if not recipes:
                        st.info("📝 No recipes found in Notion database.")
                    else:
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
                        choice = st.selectbox("Select a recipe", options, index=default_notion_index, key="notion_recipe_select")
                        st.session_state.selected_notion_choice_index = options.index(choice)
                        selected = next(r for r, name in zip(recipes, options) if name == choice)
                        
                        # Get recipe details from cache or fetch if needed
                        recipe_id = selected.get("id")
                        if recipe_id not in _recipe_details_cache:
                            with st.spinner("Loading recipe details..."):
                                details = fetch_recipe_details(recipe_id)
                        else:
                            # Use cached details without API call
                            details = _recipe_details_cache[recipe_id]
                            
                        content_md = format_notion_recipe(details)
                        
                        st.markdown("**Selected Recipe:**")
                        st.markdown(content_md)
                        
                        # Return this recipe if this tab is active and valid
                        if content_md:
                            recipe_content = content_md
                            
                except Exception as e:
                    st.error(f"❌ Failed to load recipes: {e}")
                    if st.button("🔄 Retry", key="retry_recipes"):
                        clear_notion_cache()
                        st.rerun()
        
        with tab3:
            st.markdown("**Custom Recipe:**")
            recipe_input = st.text_area(
                label="Enter your recipe (plain text or markdown):",
                value=st.session_state.custom_recipe,
                height=300,
                placeholder="Enter your recipe here...",
                key="custom_recipe_input"
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
            
            # Show saved recipe if available
            if st.session_state.custom_recipe:
                st.markdown("**Saved Custom Recipe:**")
                st.markdown(st.session_state.custom_recipe)
                recipe_content = st.session_state.custom_recipe
            elif recipe_input.strip():
                recipe_content = recipe_input
        
        # Recipe tips in a sidebar
        with st.sidebar:
            st.markdown("### 📝 Recipe Tips")
            st.info(
                """
                - Include ingredients and instructions
                - Add cooking times and temperatures  
                - Mention serving sizes
                - Use clear, simple language
                """
            )
        
        return recipe_content if recipe_content else default_recipe if 'default_recipe' in locals() else ""
    
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
            # Disable button until models are loaded
            models_ready = st.session_state.get('whisper_loaded', False)
            button_disabled = not models_ready or st.session_state.get('models_loading', False)
            
            if st.session_state.get('models_loading', False):
                button_text = "🔄 Loading Models..."
                help_text = "Please wait while models are loading"
            elif not models_ready:
                button_text = "⏳ Models Not Ready"
                help_text = "Whisper model is still loading"
            else:
                button_text = "🎤 Start Listening"
                help_text = "Start voice interaction"
            
            if col_ctrl1.button(button_text, key="main_start_listening", type="primary", 
                              disabled=button_disabled, help=help_text):
                start_main = True
                self.logger.log_user_action("CLICKED_START", f"mode={chef_mode}, model={selected_model}")
                
        # Handle stop action immediately
        if stop_requested:
            self.logger.log_user_action("CLICKED_STOP", "User requested voice loop stop")
            self.voice_loop_event.set()
            if self.voice_loop_thread and self.voice_loop_thread.is_alive():
                self.voice_loop_thread.join(timeout=2)
            self._stop_audio_processes()
            st.session_state.voice_loop_thread = None  # Clear thread reference
            st.session_state.voice_loop_running = False
            st.session_state.conversation_state = 'idle'
            st.session_state.models_loaded = False
            # Clear conversation display
            st.session_state.current_question = ""
            st.session_state.current_response = ""
            st.session_state.response_chunks = []
            st.session_state.response_complete = False
            st.session_state.chat_messages = []
            st.session_state.current_response_start_time = None
            st.rerun()
        should_start = start_main

        # Show conversation display after buttons
        self._render_conversation_display()

        # Recipe section (cached during active voice loop to avoid repeated GETs)
        if st.session_state.voice_loop_running:
            # Use cached recipe to completely avoid API calls during voice mode
            recipe = st.session_state.selected_recipe
            # Show cached recipe info without re-rendering recipe section
            st.subheader("📝 Active Recipe")
            st.info("🔒 Recipe locked during voice session")
            with st.expander("View Active Recipe", expanded=False):
                st.markdown(recipe)
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
            time.sleep(0.5)  # Reduced from 1s for better responsiveness
            st.rerun()


def main():
    """Entry point for the Streamlit app."""
    app = ChefApp()
    app.run()


if __name__ == "__main__":
    main() 