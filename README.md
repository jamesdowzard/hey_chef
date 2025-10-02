# 🍳 Hey Chef - Voice-Controlled Cooking Assistant

A sophisticated voice-controlled cooking assistant that helps you with recipes using AI. Features wake word detection, speech-to-text, AI-powered responses, text-to-speech, and multiple chef personalities!

## ✨ Features

### Core Features
- 🎤 **Voice Control**: Say "Hey Chef" to activate, then ask your cooking questions
- 🧠 **AI-Powered**: Uses OpenAI GPT-4 for intelligent cooking assistance
- 🗣️ **Text-to-Speech**: Responds with spoken answers (macOS built-in or OpenAI TTS)
- 📝 **Recipe Management**: Default recipes, Notion database integration, or custom input
- 💬 **Conversation History**: Maintains context across questions
- 🔄 **Streaming Responses**: Start hearing answers as they're generated
- 🗂️ **Notion Integration**: Connect to your Notion recipe database

### Chef Personalities

#### Normal Mode 😊
- Friendly, helpful responses
- Detailed explanations
- Patient and encouraging tone

#### Sassy Mode 😈
- Short, brutally honest responses (1-2 sentences max)
- Sarcastic and impatient tone
- Calls out cooking mistakes with attitude
- Example: *"How much salt?"* → *"Did your taste buds abandon ship? Start with a pinch and taste as you go, Einstein."*

#### Gordon Ramsay Mode 🔥
- Explosive, passionate Hell's Kitchen-style responses
- Longer, more dramatic answers
- High-energy coaching with colorful language
- Example: *"Is this cooked?"* → *"LOOK AT IT! That chicken is so raw it's still clucking! Get it back in the pan, NOW!"*

## 🚀 Quick Start

### Prerequisites
- macOS (for built-in TTS and wake word detection)
- Python 3.8+
- Microphone
- Internet connection for AI features

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/jamesdowzard/hey_chef.git
   cd hey_chef
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   Create a `.env` file with:
   ```bash
   # Required
   OPENAI_API_KEY=your_openai_api_key_here
   PICO_ACCESS_KEY=your_picovoice_access_key_here

   # Optional - for OpenAI TTS instead of macOS
   USE_EXTERNAL_TTS=1

   # Optional - for Notion integration
   NOTION_API_TOKEN=your_notion_api_token
   NOTION_RECIPES_DB_ID=your_notion_database_id
   ```

4. **Run the application**

   **Standard mode** (Streamlit only):
   ```bash
   streamlit run main.py
   # or
   python main.py  # auto-launches streamlit
   ```

   **With Notion integration**:
   ```bash
   ./run.sh
   # Starts both Notion API server and Streamlit UI
   ```

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
├── notion_api.py        # FastAPI server for Notion integration
├── run.sh               # Convenience script (API + UI)
└── requirements.txt     # Python dependencies
```

## ⚙️ Configuration

The application uses a structured configuration system in `config/config.yaml`:

```yaml
# Audio settings
audio:
  sample_rate: 16000
  wake_word_sensitivity: 0.7
  whisper_model_size: "tiny"
  vad_aggressiveness: 1
  max_silence_sec: 1.0
  macos_voice: "Samantha"
  external_voice: "alloy"
  speech_rate: 219  # ~1.25x speed

# LLM settings
llm:
  model: "gpt-4-turbo"
  available_models:
    - "gpt-4-turbo"
    - "gpt-4o"
  max_tokens: 150
  temperature: 0.2
  sassy_max_tokens: 100  # Shorter for sassy mode
  sassy_temperature: 0.7
  gordon_max_tokens: 180  # Longer for Gordon mode
  gordon_temperature: 0.8

# UI settings
ui:
  page_title: "Hey Chef"
  page_icon: "🍳"
  default_use_history: true
  default_use_streaming: false
```

## 🎤 Usage

1. **Start the application** and configure your preferences in the sidebar
2. **Choose a recipe source**:
   - 📄 Default recipe (included)
   - 🗂️ Notion database (if configured)
   - ✏️ Custom text input
3. **Select your chef personality**: Normal, Sassy, or Gordon Ramsay
4. **Enable streaming** if you want to hear responses as they're generated
5. **Click "Start Listening"**
6. **Say "Hey Chef"** and wait for the audio tone
7. **Ask your question** clearly
8. **Listen to the response** in your chosen personality style

### Example Questions
- "What ingredients do I need?"
- "How long should I cook the chicken?"
- "What temperature should the oven be?"
- "Can I substitute butter with oil?"
- "How do I know when it's done?"
- "What's the next step?"

## 🗂️ Notion Integration

Hey Chef can connect to your Notion recipe database:

1. **Create a Notion integration** at https://www.notion.so/my-integrations
2. **Share your recipe database** with the integration
3. **Add credentials to `.env`**:
   ```bash
   NOTION_API_TOKEN=secret_xxxxx
   NOTION_RECIPES_DB_ID=your_database_id
   ```
4. **Run with Notion support**:
   ```bash
   ./run.sh
   ```

The Notion integration runs a separate FastAPI server on port 3333 that provides REST endpoints for recipe access.

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
- Can be toggled on/off in the sidebar

### Audio Feedback
- Ready tone (Tink): Models loaded and listening
- Wake word tone (Pop): "Hey Chef" detected

## 🛠️ Development

### Adding New Features
The modular architecture makes it easy to extend:

- **New audio features**: Add to `src/audio/`
- **New AI models**: Extend `src/ai/llm_client.py`
- **New UI components**: Add to `src/ui/app.py`
- **New configurations**: Update `src/config/settings.py`
- **New chef personalities**: Add prompts in `src/config/prompts.py`

### Adding a New Chef Personality

1. Add system prompt in `src/config/prompts.py`:
   ```python
   def get_system_prompt(chef_mode: str = "normal") -> str:
       if chef_mode == "your_mode":
           return "Your custom system prompt..."
   ```

2. Add settings in `src/config/settings.py`:
   ```python
   your_mode_max_tokens: int = 150
   your_mode_temperature: float = 0.7
   ```

3. Update UI in `src/ui/app.py` (radio button options and mode indicators)

## 🐛 Troubleshooting

### Common Issues

**"Wake word model not found"**
- Ensure `models/porcupine_models/hey_chef.ppn` exists
- Check your Picovoice access key in `.env`

**"OpenAI API error"**
- Verify your `OPENAI_API_KEY` in `.env`
- Check your OpenAI account has credits

**"Audio device error"**
- Check microphone permissions in System Preferences
- Ensure no other apps are using the microphone
- Try restarting the application

**"Module not found"**
- Run `pip install -r requirements.txt`
- Ensure you're in the correct directory and virtual environment

**"Notion recipes not loading"**
- Verify `NOTION_API_TOKEN` and `NOTION_RECIPES_DB_ID` in `.env`
- Ensure you ran with `./run.sh` to start the Notion API server
- Check that your integration has access to the database

### Getting Help
- Check the console output for detailed error messages
- Ensure all environment variables are set correctly
- Try restarting the application if it gets stuck
- Verify your API keys are valid and have sufficient credits

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

**Enjoy cooking with your AI sous chef!** 🍳✨
