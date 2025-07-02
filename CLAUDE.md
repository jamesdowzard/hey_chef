# Hey Chef - Voice-Controlled Cooking Assistant

This is a sophisticated Python-based voice assistant designed specifically for cooking and culinary guidance. The application combines AI-powered conversation with real-time voice interaction to create an intuitive kitchen companion.

## What This Application Does

Hey Chef is a multi-modal cooking assistant that:
- Listens for the wake word "Hey Chef" using Porcupine wake word detection
- Converts spoken questions to text using OpenAI Whisper
- Processes questions with OpenAI's GPT models to provide cooking guidance
- Responds with spoken answers using text-to-speech
- Maintains conversation context for follow-up questions
- Supports multiple chef personalities (normal, sassy, Gordon Ramsay mode)

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

### Key Features

- **Multi-personality modes**: Normal (helpful), Sassy (brutally honest), Gordon Ramsay (explosive)
- **Recipe sources**: Default YAML recipes, Notion database integration, custom text input
- **Streaming responses**: Start hearing AI responses as they're being generated
- **Conversation memory**: Maintains context across multiple questions
- **Real-time interaction**: Background voice loop with immediate audio feedback

## Technical Architecture

The application uses a multi-threaded architecture:
- Main thread runs the Streamlit UI
- Background thread handles the voice interaction loop
- Thread synchronization via `threading.Event` for clean start/stop

Voice interaction flow:
1. Wake word detection (blocking, interruptible)
2. Voice activity detection + recording
3. Speech-to-text conversion
4. LLM processing (with or without streaming)
5. Text-to-speech playback
6. History update and UI refresh

## Configuration

Centralized configuration in `config/config.yaml`:
- Audio settings (sample rates, model sizes, voice parameters)
- LLM settings (models, token limits, temperatures per personality)
- UI preferences (defaults, layout options)

Environment variables:
- `OPENAI_API_KEY`: Required for LLM and TTS
- `PICO_ACCESS_KEY`: Required for wake word detection
- `USE_EXTERNAL_TTS`: Optional, uses OpenAI TTS instead of macOS
- `RECIPE_API_URL`: For Notion database integration

## Dependencies

Key dependencies:
- `streamlit`: Web UI framework
- `openai`: GPT models and TTS
- `pvporcupine`: Wake word detection
- `openai-whisper`: Speech recognition
- `webrtcvad`: Voice activity detection
- `pyyaml`: Configuration management
- `notion-client`: Recipe database integration

## Common Operations

### Starting the Application
```bash
streamlit run main.py
# or
python main.py  # auto-launches streamlit
```

### Adding New Personalities
1. Add system prompt in `src/config/prompts.py`
2. Add mode parameters in `src/config/settings.py`
3. Update UI mode selection in `src/ui/app.py`

### Performance Monitoring
The application includes built-in latency monitoring:
- API call timing for LLM requests
- Time-to-first-chunk for streaming responses
- Voice processing pipeline timing

## Code Quality Notes

The codebase follows good practices:
- Type hints throughout
- Centralized configuration
- Clean separation of concerns
- Error handling with graceful degradation
- Thread-safe operations
- Resource cleanup (audio processes, threads)

### Minor Issues Identified
1. `src/config/settings.py:29`: Hardcoded increase factor comment could be extracted to constant
2. `src/ui/app.py:288-293`: Audio process cleanup uses broad exception handling
3. Some configuration validation could be added for required environment variables

## Testing

Test files are present in `test/` directory covering:
- LLM client functionality
- Audio components (Porcupine, Whisper, TTS)
- Performance testing

## Development Workflow

1. The application is designed to be run via Streamlit
2. Configuration changes can be made in YAML files without code changes
3. New audio models or voices can be configured via settings
4. The modular architecture supports easy extension of functionality

This is a well-structured, production-ready voice assistant specifically tailored for culinary use cases.