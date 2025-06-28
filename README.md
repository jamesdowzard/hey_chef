# 🍳 Hey Chef - Voice-Controlled Cooking Assistant

A sophisticated voice-controlled cooking assistant that helps you with recipes using AI. Features wake word detection, speech-to-text, AI-powered responses, and text-to-speech - now with **Sassy Mode** for brutally honest cooking advice!

## ✨ Features

### Core Features
- 🎤 **Voice Control**: Say "Hey Chef" to activate, then ask your cooking questions
- 🧠 **AI-Powered**: Uses OpenAI GPT-4 for intelligent cooking assistance
- 🗣️ **Text-to-Speech**: Responds with spoken answers (macOS built-in or OpenAI TTS)
- 📝 **Recipe Management**: Use default recipes or input custom ones
- 💬 **Conversation History**: Maintains context across questions
- 🔄 **Streaming Responses**: Start hearing answers as they're generated

### New in v2.0
- 😈 **Sassy Mode**: Get brutally honest, short, and sarcastic responses like Gordon Ramsay's sarcastic cousin
- 🎨 **Improved UI**: Better organized interface with mode indicators
- ⚙️ **Better Configuration**: Structured settings system
- 🏗️ **Refactored Codebase**: Clean, modular architecture
- 🛡️ **Better Error Handling**: More robust error handling and recovery

## 🚀 Quick Start

### Prerequisites
- macOS (for built-in TTS and wake word detection)
- Python 3.8+
- Microphone
- Internet connection for AI features

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hey_chef
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file with:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   PICO_ACCESS_KEY=your_picovoice_access_key_here
   # Optional: USE_EXTERNAL_TTS=1 (to use OpenAI TTS instead of macOS)
   ```

4. **Run the application**
   ```bash
   # Recommended method:
   streamlit run main.py
   
   # Or use the convenience script:
   ./run.sh
   
   # Or run directly (will auto-launch streamlit):
   python main.py
   ```

## 🎭 Modes

### Normal Mode 😊
- Friendly, helpful responses
- Detailed explanations
- Patient and encouraging tone

### Sassy Mode 😈
- Short, brutally honest responses (1-2 sentences max)
- Sarcastic and impatient tone
- Calls out cooking mistakes with attitude
- Like having Gordon Ramsay's sarcastic cousin in your kitchen

**Example Sassy Responses:**
- *"How much salt?"* → *"Did your taste buds abandon ship? Start with a pinch and taste as you go, Einstein."*
- *"Is my pasta done?"* → *"If it's crunchy, it's not pasta, it's disappointment. Cook until al dente, genius."*

## 🏗️ Project Structure

```
hey_chef/
├── src/
│   ├── config/          # Configuration management
│   │   ├── settings.py  # Settings classes
│   │   └── prompts.py   # System prompts for different modes
│   ├── audio/           # Audio processing
│   │   ├── wake_word.py # Porcupine wake word detection
│   │   ├── speech_to_text.py # Whisper STT
│   │   └── text_to_speech.py # TTS engines
│   ├── ai/              # AI/LLM integration
│   │   └── llm_client.py # OpenAI client with mode support
│   └── ui/              # User interface
│       └── app.py       # Streamlit application
├── config/              # Configuration files
│   ├── config.yaml      # Main configuration
│   └── default_recipe.yaml # Default recipe
├── models/              # Model files
│   └── porcupine_models/ # Wake word models
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## ⚙️ Configuration

The application uses a structured configuration system in `config/config.yaml`:

```yaml
audio:
  sample_rate: 16000
  wake_word_sensitivity: 0.7
  whisper_model_size: "tiny"
  # ... other audio settings

llm:
  model: "gpt-4o"
  max_tokens: 150
  sassy_max_tokens: 100  # Shorter for sassy mode
  # ... other LLM settings

ui:
  page_title: "Hey Chef"
  default_sassy_mode: false
  # ... other UI settings
```

## 🎤 Usage

1. **Start the application** and configure your preferences in the sidebar
2. **Choose a recipe** (default provided or enter your own)
3. **Enable Sassy Mode** if you want brutally honest responses 😈
4. **Click "Start Listening"** 
5. **Say "Hey Chef"** and wait for the wake word detection
6. **Ask your question** clearly and wait for the response
7. **Listen to the AI's answer** (friendly or sassy, depending on mode)

### Example Questions
- "What ingredients do I need?"
- "How long should I cook the chicken?"
- "What temperature should the oven be?"
- "Can I substitute butter with oil?"
- "How do I know when it's done?"

## 🔧 Advanced Features

### Voice Activity Detection
- Automatically detects when you start and stop speaking
- Configurable sensitivity levels
- Uses WebRTC VAD for reliable detection

### Streaming Responses
- Start hearing answers as the AI generates them
- Buffered playback for smooth experience
- Works with both macOS and OpenAI TTS

### Conversation Memory
- Maintains context across multiple questions
- Remembers your recipe and previous questions
- Can be toggled on/off

## 🛠️ Development

### Adding New Features
The modular architecture makes it easy to extend:

- **New audio features**: Add to `src/audio/`
- **New AI models**: Extend `src/ai/llm_client.py`
- **New UI components**: Add to `src/ui/app.py`
- **New configurations**: Update `src/config/settings.py`

### Running Tests
```bash
python -m pytest test/
```

## 🐛 Troubleshooting

### Common Issues

**"Wake word model not found"**
- Ensure `models/porcupine_models/hey_chef.ppn` exists
- Check your Picovoice access key

**"OpenAI API error"**
- Verify your `OPENAI_API_KEY` in `.env`
- Check your OpenAI account has credits

**"Audio device error"**
- Check microphone permissions
- Ensure no other apps are using the microphone

**"Module not found"**
- Run `pip install -r requirements.txt`
- Ensure you're in the correct directory

### Getting Help
- Check the console output for detailed error messages
- Ensure all environment variables are set correctly
- Try restarting the application if it gets stuck

## 📝 License

This project is open source. Feel free to contribute!

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 🙏 Acknowledgments

- OpenAI for GPT and TTS APIs
- Picovoice for wake word detection
- OpenAI Whisper for speech recognition
- Streamlit for the web interface

---

**Enjoy cooking with your new sassy (or friendly) AI sous chef!** 🍳✨ 