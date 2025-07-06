# Hey Chef v2 - AI Voice Assistant Development Guide

## Project Overview

Hey Chef v2 is a modern voice-controlled cooking assistant built with FastAPI backend and React frontend. The application features real-time WebSocket communication, wake word detection, speech-to-text, AI-powered responses with multiple personality modes, and text-to-speech capabilities.

## Architecture & Core Principles

### 1. Modern Web Stack
- **Backend**: FastAPI with async/await patterns for high performance
- **Frontend**: React 18 with TypeScript and Vite for fast development
- **Communication**: WebSocket for real-time audio processing (<200ms response times)
- **Styling**: Tailwind CSS with custom chef-themed components

### 2. Core Components Structure
```
backend/
├── app/
│   ├── api/             # FastAPI endpoints and WebSocket handlers
│   ├── core/            # Configuration, models, and pipeline orchestration
│   ├── services/        # Audio processing services (Wake word, STT, TTS, LLM)
│   └── logs/            # Application logs with automatic rotation
frontend/
├── src/
│   ├── components/      # React UI components
│   ├── hooks/           # Custom React hooks for state management
│   ├── services/        # API and WebSocket client services
│   └── types/           # TypeScript type definitions
```

### 3. Async Architecture
- **Event-driven**: WebSocket messages drive state transitions
- **Non-blocking**: All audio processing runs asynchronously
- **Concurrent**: Supports 100+ simultaneous connections
- **Stateful**: Per-session state management with conversation history

## Development Guidelines

### Code Style & Standards
- **Type Safety**: Full TypeScript on frontend, type hints on backend
- **Async/Await**: Consistent async patterns throughout
- **Error Handling**: Comprehensive error boundaries and graceful degradation
- **Performance**: Sub-200ms response times for voice interactions
- **Security**: API keys via environment variables, input validation

### Configuration Management
- **Environment-based**: Settings loaded from environment variables
- **Dataclass structure**: Strongly typed configuration with defaults
- **Multi-environment**: Development, staging, production configurations
- **Feature flags**: Chef personalities, audio sources, debug modes

### Testing Strategy
- **Backend**: FastAPI test client with async support
- **Frontend**: React Testing Library with WebSocket mocking
- **Integration**: End-to-end tests with Playwright
- **Performance**: Load testing for concurrent connections

## Key Implementation Patterns

### 1. WebSocket Communication Pattern
```python
# Backend: app/api/websocket.py
@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = uuid.uuid4()
    
    async for message in websocket.iter_text():
        await process_audio_message(session_id, message, websocket)
```

```typescript
// Frontend: services/websocket.ts
const useWebSocket = () => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/audio');
    ws.onmessage = (event) => handleMessage(JSON.parse(event.data));
    setSocket(ws);
  }, []);
};
```

### 2. Audio Pipeline Pattern
```python
# Backend: app/core/audio_pipeline.py
class AudioPipelineManager:
    async def process_audio_request(self, request: AudioProcessingRequest) -> AudioProcessingResponse:
        # Wake word detection
        if await self.wake_word_service.detect(request.audio_data):
            # Speech-to-text
            text = await self.stt_service.transcribe(request.audio_data)
            # AI processing
            response = await self.ai_service.generate_response(text, request.chef_mode)
            # Text-to-speech
            audio = await self.tts_service.synthesize(response)
            
            return AudioProcessingResponse(text=response, audio=audio)
```

### 3. State Management Pattern
```typescript
// Frontend: hooks/useAudio.ts
const useAudio = () => {
  const [state, setState] = useState<AudioState>({
    isListening: false,
    isProcessing: false,
    currentMode: 'normal'
  });
  
  const startListening = useCallback(async () => {
    setState(prev => ({ ...prev, isListening: true }));
    // WebSocket communication
  }, []);
};
```

## Essential Files & Their Purposes

### Backend Core Files
- `backend/main.py` - FastAPI application entry point
- `backend/app/api/websocket.py` - WebSocket connection handling
- `backend/app/core/audio_pipeline.py` - Audio processing orchestration
- `backend/app/core/config.py` - Configuration management
- `backend/app/core/models.py` - Pydantic models for type safety

### Frontend Core Files
- `frontend/src/App.tsx` - Main React application
- `frontend/src/components/VoiceController.tsx` - Voice interaction UI
- `frontend/src/hooks/useWebSocket.ts` - WebSocket state management
- `frontend/src/services/websocket.ts` - WebSocket client implementation

### Audio Services
- `backend/app/services/wake_word.py` - Porcupine wake word detection
- `backend/app/services/stt.py` - OpenAI Whisper speech-to-text
- `backend/app/services/tts.py` - Text-to-speech with multiple engines
- `backend/app/services/llm.py` - OpenAI GPT integration with chef personalities

### Configuration & Scripts
- `start-dev.sh` - Development environment startup script
- `stop-dev.sh` - Clean shutdown script
- `check-ports.sh` - Port conflict debugging
- `cleanup-ports.sh` - Force cleanup utility

## Environment Variables

### Required
- `OPENAI_API_KEY` - OpenAI API key for GPT, Whisper, and TTS
- `PICO_ACCESS_KEY` - Picovoice access key for wake word detection

### Optional
- `USE_EXTERNAL_TTS=true` - Use OpenAI TTS instead of system TTS
- `RECIPE_API_URL=http://localhost:3333` - Notion MCP server URL
- `WHISPER_MODEL_SIZE=tiny` - Whisper model size (tiny/base/small/medium/large)
- `SECRET_KEY` - FastAPI secret key for production

## Development Workflow

### 1. Initial Setup
```bash
# Install dependencies
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install

# Set environment variables
export OPENAI_API_KEY="your_openai_api_key"
export PICO_ACCESS_KEY="your_pico_access_key"
```

### 2. Development Server
```bash
# Start both backend and frontend
./start-dev.sh

# Or manually:
# Backend: cd backend && python main.py
# Frontend: cd frontend && npm run dev
```

### 3. Testing
```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test

# Integration tests
cd testing && python comprehensive_test_suite.py
```

## Performance Characteristics

### Response Times
- **Voice to Response**: <200ms (vs 2000ms in v1)
- **WebSocket Latency**: <50ms
- **Wake Word Detection**: <100ms
- **STT Processing**: <500ms (tiny model)

### Scalability
- **Concurrent Users**: 100+ simultaneous connections
- **Memory Usage**: ~90% reduction vs Streamlit version
- **CPU Usage**: Async processing prevents blocking

## Chef Personality Modes

### 1. Normal Mode
- **Tone**: Helpful and informative
- **Max Tokens**: 150
- **Temperature**: 0.2
- **Use Case**: General cooking assistance

### 2. Sassy Mode
- **Tone**: Playful and witty
- **Max Tokens**: 100
- **Temperature**: 0.7
- **Use Case**: Fun, casual cooking sessions

### 3. Gordon Ramsay Mode
- **Tone**: Energetic and passionate
- **Max Tokens**: 180
- **Temperature**: 0.8
- **Use Case**: Motivational cooking challenges

## WebSocket Message Types

### Client to Server
```typescript
interface AudioRequest {
  type: 'audio_data' | 'start_listening' | 'stop_listening';
  data: ArrayBuffer | null;
  chef_mode?: 'normal' | 'sassy' | 'gordon_ramsay';
}
```

### Server to Client
```typescript
interface AudioResponse {
  type: 'wake_word' | 'stt_result' | 'ai_response' | 'tts_audio' | 'error';
  data: {
    text?: string;
    audio?: ArrayBuffer;
    error?: string;
  };
}
```

## Debugging & Troubleshooting

### Common Issues

1. **"WebSocket connection failed"**
   - Check backend is running on port 8000
   - Verify firewall settings
   - Run `./check-ports.sh` to see active services

2. **"Wake word not detected"**
   - Verify `PICO_ACCESS_KEY` is set
   - Check microphone permissions
   - Ensure wake word model exists at `models/porcupine_models/hey_chef.ppn`

3. **"Port already in use"**
   - Run `./stop-dev.sh` then `./start-dev.sh`
   - If persistent, use `./cleanup-ports.sh`

### Log Files
- `backend/logs/sessions/` - Session-specific logs
- `backend/logs/audio/` - Audio processing logs
- `backend/logs/api/` - API request logs
- `backend/hey_chef_v2_api.log` - Main application log

### Health Checks
- **Backend Health**: `curl http://localhost:8000/health`
- **WebSocket**: `wscat -c ws://localhost:8000/ws/audio`
- **Frontend**: Browser console for WebSocket connection status

## Security Considerations
- **API Keys**: Never commit keys to repository
- **CORS**: Configured for development origins only
- **Input Validation**: Pydantic models validate all inputs
- **Error Handling**: No sensitive information in error messages
- **Rate Limiting**: WebSocket connection limits prevent abuse

## Performance Optimization
- **Model Selection**: Configurable Whisper model size
- **Connection Pooling**: Efficient WebSocket connection management
- **Async Processing**: Non-blocking audio pipeline
- **Memory Management**: Automatic cleanup of audio buffers
- **Caching**: Session state and conversation history

## Deployment Considerations
- **Environment Variables**: Use proper secret management
- **Process Management**: Use PM2 or systemd for production
- **Reverse Proxy**: Nginx for static files and WebSocket proxying
- **SSL/TLS**: Required for microphone access in production
- **Monitoring**: Structured logging for observability

## Contributing Guidelines
1. **Type Safety**: All new code must be fully typed
2. **Async Patterns**: Use async/await consistently
3. **Error Handling**: Implement proper error boundaries
4. **Testing**: Add tests for new functionality
5. **Documentation**: Update this guide for architectural changes

## Integration Points
- **Notion API**: Recipe management via MCP server
- **OpenAI API**: GPT-4 for responses, Whisper for STT, TTS for speech
- **Picovoice**: Porcupine for wake word detection
- **WebSocket**: Real-time bidirectional communication

## Migration from v1
Hey Chef v2 represents a complete rewrite with:
- **10x Performance**: Sub-200ms response times
- **100x Scalability**: Supports concurrent users
- **Modern Stack**: FastAPI + React replacing Streamlit
- **Real-time Communication**: WebSocket replacing HTTP polling
- **Professional Architecture**: Microservices replacing monolithic design

---

Remember: Hey Chef v2 prioritizes performance, scalability, and user experience. Every change should maintain sub-200ms response times and support concurrent users while providing a delightful voice interaction experience.