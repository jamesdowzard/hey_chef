# Changelog

## v2.0.0 - Major Refactor & Sassy Mode (2024-06-28)

### 🆕 New Features
- **Sassy Mode**: Added a brutally honest, sarcastic cooking assistant mode
  - Short, cutting responses (1-2 sentences max)
  - Sarcastic tone with attitude like Gordon Ramsay's cousin
  - Configurable via UI toggle
  - Different temperature and token limits for more creative snark

### 🏗️ Architecture Improvements
- **Complete codebase refactor** into organized package structure:
  - `src/config/` - Configuration management with structured settings
  - `src/audio/` - Audio processing (wake word, STT, TTS)
  - `src/ai/` - AI/LLM integration
  - `src/ui/` - Streamlit user interface
- **Improved configuration system** with YAML-based structured settings
- **Better error handling** throughout the application
- **Type hints** added for better code maintainability
- **Context managers** for proper resource cleanup

### 🎨 UI/UX Improvements
- **Redesigned interface** with sidebar controls
- **Mode indicators** showing current personality (😊 Friendly vs 😈 Sassy)
- **Better status indicators** for voice loop state
- **Improved response display** with mode-specific styling
- **Recipe management** with better preview and editing

### 🔧 Technical Improvements
- **Consolidated TTS engines** - combined macOS and OpenAI TTS into single engine
- **Better streaming support** with improved buffering
- **Enhanced LLM client** with mode-specific parameters
- **Modular audio components** with proper initialization and cleanup
- **Structured logging** and error reporting

### 📁 File Organization
```
Before:                   After:
├── streamlit_app.py  →  ├── src/
├── llm_client.py     →  │   ├── config/
├── wake_porcupine.py →  │   ├── audio/  
├── stt_whisper.py    →  │   ├── ai/
├── tts_engine*.py    →  │   └── ui/
├── config.yaml       →  ├── config/
└── default_recipe.yaml  ├── models/
                         └── main.py
```

### ⚙️ Configuration Changes
- **Structured config** with separate sections for audio, LLM, and UI settings
- **Mode-specific parameters** for normal vs sassy responses
- **Backward compatibility** maintained for existing configs

### 🧪 Testing & Quality
- **Improved error handling** with graceful fallbacks
- **Resource management** with proper cleanup
- **Configuration validation** on startup
- **Better debugging** output and error messages

### 📖 Documentation
- **Comprehensive README** with usage instructions
- **Code documentation** with docstrings and type hints
- **Configuration examples** and troubleshooting guide

### 🗑️ Cleanup
- Removed duplicate and redundant files
- Consolidated TTS implementations
- Simplified import structure
- Reduced code duplication

---

## v1.0.0 - Initial Release
- Basic voice-controlled cooking assistant
- Wake word detection with Porcupine
- Speech-to-text with Whisper  
- AI responses via OpenAI GPT
- Text-to-speech playback
- Streamlit web interface 