# Hey Chef - Voice-Controlled Cooking Assistant

This is a sophisticated Python-based voice assistant designed specifically for cooking and culinary guidance. The application combines AI-powered conversation with real-time voice interaction to create an intuitive kitchen companion.

## What This Application Does

Hey Chef is a multi-modal cooking assistant that:
- Listens for the wake word "Hey Chef" using Porcupine wake word detection
- Converts spoken questions to text using OpenAI Whisper
- Processes questions with OpenAI's GPT models to provide cooking guidance
- Responds with spoken answers using text-to-speech
- Maintains conversation context for follow-up questions
- Supports multiple chef personalities (Normal, Sassy, Gordon Ramsay)
- Integrates with Notion databases for recipe management

## Architecture Overview

### Core Components

1. **Audio Processing** (`src/audio/`)
   - `wake_word.py`: Porcupine-based wake word detection for "Hey Chef"
   - `speech_to_text.py`: Whisper-based speech recognition with voice activity detection
   - `text_to_speech.py`: TTS engine supporting both macOS built-in and OpenAI TTS

2. **AI Integration** (`src/ai/`)
   - `llm_client.py`: OpenAI ChatCompletion client with streaming support and personality modes

3. **Configuration** (`src/config/`)
   - `settings.py`: Centralized configuration management with YAML loading
   - `prompts.py`: System prompts for different chef personalities

4. **User Interface** (`src/ui/`)
   - `app.py`: Streamlit-based web interface with real-time voice interaction

5. **Recipe Integration**
   - `notion_api.py`: FastAPI server providing REST API to Notion recipe database
   - `run.sh`: Convenience script that launches both Notion API and Streamlit UI

### Key Features

- **Three personality modes**:
  - **Normal**: Friendly, helpful, patient guidance
  - **Sassy**: Brutally honest, short responses (1-2 sentences max) with sarcastic tone
  - **Gordon Ramsay**: Explosive, passionate, Hell's Kitchen-style responses with longer token limit

- **Multiple recipe sources**:
  - Default YAML recipes (`config/default_recipe.yaml`)
  - Notion database integration (via REST API)
  - Custom text input

- **Streaming responses**: Start hearing AI responses as they're being generated
- **Conversation memory**: Maintains context across multiple questions
- **Real-time interaction**: Background voice loop with immediate audio feedback
- **Audio feedback**: System tones for ready state and wake word detection

## Technical Architecture

### Multi-threaded Design
The application uses a multi-threaded architecture:
- Main thread runs the Streamlit UI
- Background thread handles the voice interaction loop
- Thread synchronization via `threading.Event` for clean start/stop
- Thread-safe state management via Streamlit session state

### Voice Interaction Flow
1. Wake word detection (blocking, interruptible via threading event)
2. Audio tone feedback (wake word detected)
3. Voice activity detection + recording
4. Speech-to-text conversion (Whisper)
5. LLM processing (with or without streaming)
6. Text-to-speech playback (buffered for streaming)
7. History update and UI refresh
8. Return to wake word detection

### Notion Integration
- Separate FastAPI server (`notion_api.py`) running on port 3333
- REST endpoints:
  - `GET /recipes` - List all recipes from Notion database
  - `GET /recipes/{recipe_id}` - Get full recipe details with content blocks
- Streamlit UI fetches and renders recipes via HTTP requests
- Recipe content cached during active voice sessions to avoid repeated API calls

## Configuration

### Centralized Configuration
All settings in `config/config.yaml`:

```yaml
audio:
  sample_rate: 16000
  wake_word_sensitivity: 0.7
  whisper_model_size: "tiny"
  vad_aggressiveness: 1
  max_silence_sec: 1.0
  macos_voice: "Samantha"
  external_voice: "alloy"
  speech_rate: 219  # ~1.25x speed

llm:
  model: "gpt-4-turbo"
  available_models: ["gpt-4-turbo", "gpt-4o"]
  max_tokens: 150
  temperature: 0.2
  sassy_max_tokens: 100
  sassy_temperature: 0.7
  gordon_max_tokens: 180  # Longer for explosive rants
  gordon_temperature: 0.8  # High creativity

ui:
  page_title: "Hey Chef"
  page_icon: "🍳"
  default_use_history: true
  default_use_streaming: false
```

### Environment Variables
Required:
- `OPENAI_API_KEY`: Required for LLM and TTS
- `PICO_ACCESS_KEY`: Required for wake word detection

Optional:
- `USE_EXTERNAL_TTS`: Set to "1" to use OpenAI TTS instead of macOS
- `NOTION_API_TOKEN`: For Notion database integration
- `NOTION_RECIPES_DB_ID`: Notion database ID for recipes
- `RECIPE_API_URL`: URL for Notion API (defaults to http://localhost:3333)

## Dependencies

Key dependencies (see `requirements.txt`):
- `streamlit`: Web UI framework
- `openai`: GPT models and TTS
- `pvporcupine`: Wake word detection
- `openai-whisper`: Speech recognition
- `webrtcvad`: Voice activity detection
- `pyyaml`: Configuration management
- `notion-client`: Recipe database integration
- `fastapi`: REST API for Notion integration
- `uvicorn`: ASGI server for FastAPI
- `requests`: HTTP client for API calls

## Running the Application

### Standard Mode (Streamlit only)
```bash
streamlit run main.py
# or
python main.py  # auto-launches streamlit
```

### With Notion Integration
```bash
./run.sh
# Starts both Notion API server (port 3333) and Streamlit UI
```

## Project Structure

```
hey_chef/
├── src/
│   ├── audio/           # Audio processing (wake word, STT, TTS)
│   ├── ai/              # LLM integration
│   ├── config/          # Settings and prompts
│   └── ui/              # Streamlit interface
├── config/
│   ├── config.yaml      # Main configuration
│   └── default_recipe.yaml
├── models/
│   └── porcupine_models/  # Wake word detection models
├── main.py              # Application entry point
├── notion_api.py        # FastAPI server for Notion integration
├── run.sh               # Convenience script (API + UI)
└── requirements.txt     # Python dependencies
```

## Development Notes

### Adding New Personalities
1. Add system prompt in `src/config/prompts.py`
2. Add mode-specific parameters (max_tokens, temperature) in `src/config/settings.py`
3. Add mode to UI radio buttons in `src/ui/app.py`
4. Update mode indicators dictionary in `_render_header()`

### Extending Recipe Sources
The recipe system is designed to be extensible. Current sources:
- YAML files (default)
- Notion API (via REST)
- Custom text input

To add new sources, update `_render_recipe_section()` in `src/ui/app.py`.

### Audio Feedback
The application provides audio feedback:
- Ready tone (Tink.aiff): Models loaded and ready
- Wake word tone (Pop.aiff): "Hey Chef" detected

### State Management
Key session state variables:
- `voice_loop_running`: Boolean, whether voice loop is active
- `conversation_state`: String, one of `idle`, `listening_for_wake_word`, `recording`, `processing`
- `models_loaded`: Boolean, whether AI models are loaded
- `selected_recipe`: String, cached recipe content during active session
- `chef_mode`: String, current personality mode

## Code Quality

The codebase follows good practices:
- Type hints throughout for better IDE support
- Centralized configuration via YAML
- Clean separation of concerns
- Comprehensive error handling with graceful degradation
- Thread-safe operations with proper cleanup
- Resource management (audio processes, threads, API connections)

### Thread Safety
- Uses `threading.Event` for interruptible blocking operations
- Session state managed through Streamlit's thread-safe session_state
- Proper cleanup of background threads on stop
- Audio process termination via `pkill` on macOS

## Repository History

This repository was recently cleaned up from experimental branches:
- Removed failed React/Next.js frontend attempts (v2, v2-migration, cc_refactor)
- Removed old FastAPI backend experiments
- Consolidated to single clean branch (master) with working Streamlit app
- All features from experimental branches (Gordon Ramsay mode, Notion integration, etc.) were merged into master before cleanup

The current codebase represents a stable, production-ready voice assistant specifically tailored for culinary use cases.
