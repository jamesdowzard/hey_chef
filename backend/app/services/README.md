# Hey Chef v2 Services Architecture

This directory contains the async-compatible services for Hey Chef v2, ported from the original synchronous implementations in the main Hey Chef application.

## Overview

The services architecture provides a clean, testable, and async-compatible foundation for all audio processing and AI functionality in Hey Chef v2. Each service is designed to be:

- **Async/await compatible**: All operations use async/await patterns
- **Resource-managed**: Proper initialization and cleanup of resources
- **Error-handled**: Comprehensive error handling with appropriate logging
- **Independently testable**: Services can be easily mocked and tested
- **Configurable**: All settings come from the centralized configuration system

## Service Components

### Base Services (`base.py`)

- **`BaseService`**: Abstract base class providing common functionality
  - Logging setup
  - Resource management
  - Error handling patterns
  - Async context management

- **`AudioService`**: Specialized base class for audio-related services
  - Start/stop lifecycle management
  - Audio-specific error handling
  - Stop event coordination

### Wake Word Detection (`wake_word.py`)

**`WakeWordService`**: Async wake word detection using Picovoice Porcupine

- **Key Features**:
  - Continuous background listening for "Hey Chef"
  - Callback-based detection notifications
  - Configurable sensitivity
  - Graceful shutdown and resource cleanup

- **Usage**:
```python
async def on_wake_word():
    print("Hey Chef detected!")

service = WakeWordService(detection_callback=on_wake_word)
await service.start()
```

### Speech-to-Text (`stt.py`)

**`STTService`**: Async speech-to-text using OpenAI Whisper with VAD

- **Key Features**:
  - Voice activity detection (VAD) for automatic recording
  - Multiple Whisper model sizes
  - Configurable silence detection
  - Temporary file management

- **Usage**:
```python
service = STTService(model_size="base")
text = await service.transcribe_from_microphone()
```

### Text-to-Speech (`tts.py`)

**`TTSService`**: Async text-to-speech with multiple backends

- **Key Features**:
  - macOS built-in TTS support
  - OpenAI TTS API support
  - Streaming text-to-speech
  - Process management and cleanup

- **Usage**:
```python
service = TTSService(use_external=True)
await service.say("Hello, chef!")

# Streaming TTS
async def text_stream():
    yield "Hello "
    yield "world!"

await service.stream_and_play(text_stream())
```

### Large Language Model (`llm.py`)

**`LLMService`**: Async OpenAI ChatCompletion with chef personalities

- **Key Features**:
  - Multiple chef modes (normal, sassy, gordon_ramsay)
  - Streaming responses
  - Conversation history management
  - Mode-specific parameters and prompts

- **Usage**:
```python
service = LLMService()
response = await service.ask(
    recipe_text="Pasta recipe...",
    user_question="How long to cook?",
    chef_mode="sassy"
)

# Streaming response
async for chunk in service.stream(recipe_text, question, chef_mode="gordon_ramsay"):
    print(chunk, end="")
```

## Service Factory Functions

The `__init__.py` file provides convenient factory functions:

```python
from services import (
    create_wake_word_service,
    create_stt_service,
    create_tts_service,
    create_llm_service
)

# Create services with default settings
wake_word = create_wake_word_service()
stt = create_stt_service(model_size="small")
tts = create_tts_service(use_external=True)
llm = create_llm_service()
```

## Audio Pipeline Example

The `audio_pipeline_example.py` demonstrates how to orchestrate all services together:

```python
from services.audio_pipeline_example import AudioPipeline

async def main():
    recipe = "Your recipe text here..."
    
    async with AudioPipeline(recipe_text=recipe, chef_mode="normal") as pipeline:
        await pipeline.start()
        
        # Pipeline automatically handles:
        # 1. Wake word detection
        # 2. Speech-to-text
        # 3. LLM processing
        # 4. Text-to-speech response
        
        # Keep running until interrupted
        await pipeline.run_interactive_demo()
```

## Testing

The `test_services.py` file provides comprehensive test examples:

- **Unit tests** for individual services
- **Integration tests** for service interactions
- **Mocking patterns** for external dependencies
- **Async test patterns** using pytest-asyncio

Run tests with:
```bash
pytest test_services.py -v
```

## Configuration

All services use settings from `../core/config.py`:

```python
# Audio settings
settings.audio.sample_rate = 16000
settings.audio.whisper_model_size = "tiny"
settings.audio.wake_word_sensitivity = 0.7

# LLM settings  
settings.llm.model = "gpt-4o"
settings.llm.max_tokens = 150
settings.llm.temperature = 0.2

# API keys
settings.openai_api_key = "your-key"
settings.pico_access_key = "your-key"
```

## Error Handling

All services implement comprehensive error handling:

- **Initialization errors**: Clear error messages for setup issues
- **Runtime errors**: Graceful degradation and recovery
- **Resource cleanup**: Proper cleanup even when errors occur
- **Logging**: Detailed logging for debugging and monitoring

## Resource Management

Services properly manage resources:

- **Async context managers**: Use `async with service:` for automatic cleanup
- **Explicit cleanup**: Call `await service.cleanup()` when done
- **Resource tracking**: Internal tracking of all resources for cleanup
- **Graceful shutdown**: Stop operations before cleanup

## Performance Considerations

- **Thread pool execution**: Blocking operations run in thread pools
- **Concurrent initialization**: Services can be initialized concurrently
- **Resource sharing**: Shared resources where appropriate
- **Memory management**: Proper cleanup of temporary files and objects

## Migration from Original Services

The v2 services maintain compatibility with the original Hey Chef functionality while adding async support:

| Original | v2 Service | Key Changes |
|----------|------------|-------------|
| `WakeWordDetector` | `WakeWordService` | Async detection loop, callback-based |
| `WhisperSTT` | `STTService` | Async transcription, better VAD handling |
| `TTSEngine` | `TTSService` | Async speech, streaming support |
| `LLMClient` | `LLMService` | Async responses, enhanced chef modes |

## Future Enhancements

Potential improvements for the services:

1. **Real-time streaming STT**: Continuous transcription during speech
2. **Voice cloning**: Custom voice synthesis for different chef personalities  
3. **Multi-language support**: Support for different languages
4. **Edge deployment**: Optimize for edge device deployment
5. **Caching**: Intelligent caching of LLM responses and TTS audio
6. **Metrics**: Detailed performance and usage metrics

## Troubleshooting

Common issues and solutions:

1. **Import errors**: Ensure all dependencies are installed
2. **API key errors**: Check environment variables are set
3. **Audio device errors**: Verify microphone permissions
4. **Model loading errors**: Check internet connection for Whisper models
5. **Resource leaks**: Always use proper cleanup or context managers

## Dependencies

The services require these key dependencies:

- `pvporcupine`: Wake word detection
- `openai-whisper`: Speech-to-text
- `webrtcvad`: Voice activity detection
- `sounddevice`: Audio I/O
- `openai`: LLM and TTS API
- `asyncio`: Async programming support

Make sure these are included in your `requirements.txt` or installed via pip.