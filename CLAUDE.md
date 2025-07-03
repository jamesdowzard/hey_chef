# Hey Chef - AI Assistant Development Guide

## Project Overview

Hey Chef is a sophisticated voice-controlled cooking assistant that combines AI, speech processing, and a clean Streamlit interface. The application features wake word detection, speech-to-text, AI-powered responses with multiple personality modes, and text-to-speech capabilities.

## Architecture & Core Principles

### 1. Modular Design
- **Clean separation of concerns**: Each module has a single responsibility
- **Dependency injection**: Components accept dependencies rather than creating them
- **Configuration-driven**: Behavior controlled through `config/config.yaml`
- **Defensive programming**: Comprehensive error handling and graceful degradation

### 2. Core Components Structure
```
src/
├── config/          # Settings and prompts management
├── audio/           # Speech processing (STT, TTS, wake word)
├── ai/              # LLM integration with multiple personality modes
├── ui/              # Streamlit interface
└── utils/           # Shared utilities (logging, helpers)
```

## Development Guidelines

### Code Style & Standards
- **Simplicity first**: Every change should impact minimal code
- **Descriptive naming**: Function and variable names should be self-documenting
- **Type hints**: Use Python type hints for all function parameters and returns
- **Docstrings**: Include docstrings for all classes and public methods
- **Error handling**: Always handle potential failures gracefully

### Configuration Management
- **Single source of truth**: All settings in `config/config.yaml`
- **Dataclass-based**: Settings use `@dataclass` for structure and validation
- **Environment variables**: Support for environment variable overrides
- **Hierarchical loading**: Settings merge from defaults → config file → env vars

### Testing Strategy
- **Comprehensive test suite**: Run via `python test_runner.py`
- **Test categories**: Unit tests, integration tests, configuration tests, Notion API tests
- **Mock external dependencies**: Use `unittest.mock` for APIs and file system
- **Test isolation**: Each test should be independent and repeatable

## Key Implementation Patterns

### 1. Settings Pattern
```python
from src.config.settings import Settings
settings = Settings()  # Auto-loads from config/config.yaml
```

### 2. Logging Pattern
```python
from src.utils.logger import get_logger
logger = get_logger()
logger.log_audio_event("WAKE_WORD_DETECTED", "Hey Chef detected")
```

### 3. LLM Client Pattern
```python
from src.ai.llm_client import LLMClient
client = LLMClient(
    model=settings.llm.model,
    max_tokens=settings.llm.max_tokens
)
response = client.ask(recipe_text, question, history, chef_mode="sassy")
```

### 4. Audio Processing Pattern
```python
from src.audio import WakeWordDetector, WhisperSTT, TTSEngine
detector = WakeWordDetector(settings.get_wake_word_path())
stt = WhisperSTT(model_size=settings.audio.whisper_model_size)
tts = TTSEngine(use_external=settings.audio.use_external_tts)
```

## Essential Files & Their Purposes

### Configuration Files
- `config/config.yaml` - Main configuration with audio, LLM, UI, and logging settings
- `config/default_recipe.yaml` - Default recipe template
- `src/config/settings.py` - Settings classes and loading logic
- `src/config/prompts.py` - System prompts for different chef personalities

### Core Application Files
- `main.py` - Entry point, handles Streamlit launch
- `src/ui/app.py` - Main Streamlit application with UI logic
- `src/ai/llm_client.py` - OpenAI integration with multiple chef modes
- `src/utils/logger.py` - Smart logging system with rotating logs

### Audio Processing
- `src/audio/wake_word.py` - Porcupine wake word detection
- `src/audio/speech_to_text.py` - Whisper speech-to-text
- `src/audio/text_to_speech.py` - TTS with macOS and OpenAI support

### Development & Testing
- `test_runner.py` - Comprehensive test suite runner
- `pytest.ini` - Pytest configuration
- `run.sh` - Convenience script to start both Notion server and Streamlit UI

## Environment Variables

### Required
- `OPENAI_API_KEY` - OpenAI API key for GPT and TTS
- `PICO_ACCESS_KEY` - Picovoice access key for wake word detection

### Optional
- `USE_EXTERNAL_TTS=1` - Use OpenAI TTS instead of macOS built-in
- `RECIPE_API_URL` - Notion MCP server URL (default: http://localhost:3333)

## Development Workflow

### 1. Before Making Changes
- Run the test suite: `python test_runner.py`
- Review configuration in `config/config.yaml`
- Check existing patterns in similar modules

### 2. Making Changes
- Follow the established patterns and architecture
- Update tests for any changed functionality
- Ensure configuration changes are reflected in `settings.py`
- Test both normal and error conditions

### 3. Testing Changes
- Run relevant tests: `python test_runner.py --pattern <test_name>`
- Test the full application: `./run.sh`
- Verify both voice and UI functionality work correctly

### 4. Common Commands
```bash
# Run all tests
python test_runner.py

# Run specific test pattern
python test_runner.py --pattern "test_config"

# Check test environment
python test_runner.py --check-env

# Start the application
./run.sh

# Start only Streamlit (without Notion server)
streamlit run main.py
```

## Debugging & Troubleshooting

### Log Files
- `hey_chef.log` - Master log with key events and errors
- `logs/sessions/` - Detailed session logs
- `logs/audio/` - Audio processing logs
- `logs/streamlit/` - Streamlit-specific logs

### Common Issues
1. **Wake word not detected**: Check `PICO_ACCESS_KEY` and model file at `models/porcupine_models/hey_chef.ppn`
2. **OpenAI errors**: Verify `OPENAI_API_KEY` and account credits
3. **Audio device issues**: Check microphone permissions and availability
4. **Module import errors**: Ensure `pip install -r requirements.txt` completed successfully

### Feature Flags & Modes
- **Chef Personalities**: "normal", "sassy", "gordon_ramsay" - each with different prompts and parameters
- **Audio Sources**: Built-in macOS TTS vs OpenAI TTS via `USE_EXTERNAL_TTS`
- **Streaming**: Response streaming can be toggled in UI
- **Conversation History**: Context memory can be enabled/disabled

## Security Considerations
- API keys loaded from environment variables, never committed to code
- No sensitive data logged to files
- Input validation on all user-provided data
- Graceful error handling without exposing internal details

## Performance Optimization
- **Model Selection**: Whisper model size configurable (tiny/base/small/medium/large)
- **Token Limits**: Different limits for each chef mode (sassy=100, normal=150, gordon=180)
- **Log Rotation**: Automatic cleanup of old logs to prevent disk bloat
- **Caching**: Recipe data cached to avoid repeated API calls

## Contributing Guidelines
1. **Test First**: Write or update tests before implementing features
2. **Configuration**: Add new settings to `config.yaml` and `settings.py`
3. **Documentation**: Update this file when adding new patterns or components
4. **Error Handling**: Always provide user-friendly error messages
5. **Logging**: Use the logging system for debugging and monitoring

## Integration Points
- **Notion API**: Recipe management via MCP server at localhost:3333
- **OpenAI API**: GPT-4 for responses, Whisper for STT, TTS for speech
- **Picovoice**: Porcupine for wake word detection
- **Streamlit**: Web UI framework for the main interface

---

Remember: Every change should be simple, well-tested, and follow the established patterns. When in doubt, look at existing code for examples of how similar functionality is implemented.