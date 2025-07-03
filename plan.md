# Hey Chef: Migration to FastAPI + WebSocket + React Architecture

## 🎯 **Project Goals**

Transform Hey Chef from a Streamlit prototype into a production-ready voice assistant with:
- **10x Faster Response Times**: Direct WebSocket communication (<100ms latency)
- **Multi-user Support**: Handle hundreds of concurrent users
- **Better Audio Quality**: Dedicated audio processing threads
- **Modern UI**: React-based interface with real-time updates
- **Cloud Ready**: Containerized with proper monitoring

## 🔍 **Current Architecture Issues**

### **Root Problems Identified:**
1. **Streamlit-Threading Incompatibility**: Session state resets causing "Whisper model not available" errors
2. **UI Monolith**: 1,297-line `app.py` with 138+ session state variables
3. **Performance**: Continuous 0.5s polling causing unnecessary CPU usage
4. **Scalability**: Cannot handle multiple users or scale horizontally
5. **Real-time Limitations**: Web page refreshes instead of true real-time communication

### **Current Tech Stack:**
- **Frontend**: Streamlit (web framework)
- **Backend**: Python with threading
- **Audio**: Porcupine + Whisper + OpenAI TTS
- **AI**: OpenAI GPT models
- **Data**: Notion API for recipes

## 🏗️ **New Architecture Design**

### **Technology Stack:**
- **Frontend**: React + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python 3.11+
- **Communication**: WebSockets for real-time updates
- **Audio Processing**: Async queuing with dedicated threads
- **Database**: PostgreSQL for user data, Redis for caching
- **Deployment**: Docker + Kubernetes
- **Monitoring**: Prometheus + Grafana

### **System Architecture:**

```
┌─────────────────┐    WebSocket    ┌─────────────────┐    Async Queue    ┌─────────────────┐
│   React UI      │ ◄──────────────► │   FastAPI       │ ◄────────────────► │  Audio Pipeline │
│                 │                  │   WebSocket     │                    │                 │
│ - Voice Controls│                  │   Server        │                    │ - Wake Word     │
│ - Recipe Display│                  │                 │                    │ - STT (Whisper) │
│ - Chat Interface│                  │ - Session Mgmt  │                    │ - LLM (OpenAI)  │
│ - Settings      │                  │ - Recipe API    │                    │ - TTS           │
└─────────────────┘                  └─────────────────┘                    └─────────────────┘
         │                                     │                                       │
         │                                     │                                       │
         ▼                                     ▼                                       ▼
┌─────────────────┐                  ┌─────────────────┐                    ┌─────────────────┐
│   Static Assets │                  │   PostgreSQL    │                    │   Redis Cache   │
│                 │                  │                 │                    │                 │
│ - React Bundle  │                  │ - User Profiles │                    │ - Sessions      │
│ - Audio Files   │                  │ - Recipes       │                    │ - Audio Queue   │
│ - CSS/Images    │                  │ - Chat History  │                    │ - Model Cache   │
└─────────────────┘                  └─────────────────┘                    └─────────────────┘
```

## 📋 **Migration Plan**

### **Phase 1: Foundation Setup (Week 1-2)**

#### **Backend Setup:**
1. **Create FastAPI Application Structure**
   ```
   hey_chef_v2/
   ├── backend/
   │   ├── app/
   │   │   ├── api/
   │   │   │   ├── websocket.py
   │   │   │   ├── recipes.py
   │   │   │   └── audio.py
   │   │   ├── core/
   │   │   │   ├── config.py
   │   │   │   ├── audio_pipeline.py
   │   │   │   └── models.py
   │   │   ├── services/
   │   │   │   ├── wake_word.py
   │   │   │   ├── stt.py
   │   │   │   ├── llm.py
   │   │   │   └── tts.py
   │   │   └── main.py
   │   ├── tests/
   │   ├── requirements.txt
   │   └── Dockerfile
   └── frontend/
       ├── src/
       │   ├── components/
       │   ├── hooks/
       │   ├── services/
       │   └── App.tsx
       ├── package.json
       └── Dockerfile
   ```

2. **Port Audio Components**
   - Migrate existing `src/audio/` modules to new services
   - Implement async audio processing pipeline
   - Add proper error handling and recovery

3. **Setup WebSocket Communication**
   - Real-time audio status updates
   - Bidirectional voice command flow
   - Session management

#### **Frontend Setup:**
1. **Create React Application**
   - Modern React 18 with hooks
   - TypeScript for type safety
   - Tailwind CSS for styling
   - WebSocket client integration

2. **Core Components**
   - VoiceController: Start/stop listening, status display
   - RecipeViewer: Display and manage recipes
   - ChatInterface: Conversation history
   - SettingsPanel: Configuration options

### **Phase 2: Core Features (Week 3-4)**

#### **Audio Pipeline Migration:**
1. **Async Processing Queue**
   ```python
   # Audio processing flow
   Wake Word Detection → Audio Queue → STT → LLM Queue → TTS → Response Queue
   ```

2. **WebSocket Integration**
   - Stream audio status in real-time
   - Send voice commands instantly
   - Display responses as they arrive

3. **Session Management**
   - Multi-user support with isolated sessions
   - Conversation history persistence
   - Recipe context management

#### **Recipe Management:**
1. **Database Schema**
   ```sql
   users: id, name, preferences, created_at
   recipes: id, user_id, title, content, source, created_at
   conversations: id, user_id, recipe_id, messages, created_at
   ```

2. **API Endpoints**
   - CRUD operations for recipes
   - Integration with existing Notion API
   - Search and filtering capabilities

### **Phase 3: Advanced Features (Week 5-6)**

#### **Performance Optimization:**
1. **Caching Strategy**
   - Redis for session data
   - Model caching for faster responses
   - Recipe content caching

2. **Audio Quality Improvements**
   - Noise reduction algorithms
   - Better microphone handling
   - Audio streaming optimization

#### **User Experience:**
1. **Real-time Features**
   - Live audio waveform display
   - Typing indicators during AI response
   - Voice activity detection visualization

2. **Advanced UI Components**
   - Recipe step-by-step guidance
   - Voice command shortcuts
   - Mobile-responsive design

### **Phase 4: Production Deployment (Week 7-8)**

#### **Infrastructure:**
1. **Containerization**
   ```dockerfile
   # Multi-stage builds for optimization
   # Separate containers for frontend/backend
   # Health checks and monitoring
   ```

2. **Orchestration**
   - Docker Compose for development
   - Kubernetes manifests for production
   - Auto-scaling configuration

#### **Monitoring & Observability:**
1. **Metrics Collection**
   - Response time tracking
   - Audio processing latency
   - User interaction analytics

2. **Logging & Debugging**
   - Structured logging with context
   - Error tracking and alerting
   - Performance profiling

## 📊 **Migration Benefits**

### **Performance Improvements:**
- **Response Time**: 2000ms → 200ms (10x faster)
- **Concurrent Users**: 1 → 1000+ (1000x scalability)
- **Resource Usage**: 90% reduction in CPU polling
- **Audio Quality**: Professional-grade processing

### **Developer Experience:**
- **Code Maintainability**: Modular architecture vs 1,297-line monolith
- **Testing**: Comprehensive test suite with CI/CD
- **Debugging**: Proper logging and monitoring tools
- **Deployment**: One-command container deployment

### **User Experience:**
- **Reliability**: No more "Whisper model not available" errors
- **Speed**: Instant voice command processing
- **Features**: Multi-device support, user profiles, cloud sync
- **Interface**: Modern, responsive, intuitive design

## 🛠️ **Development Workflow**

### **Week 1-2: Foundation**
- [ ] Setup new repository structure
- [ ] Create FastAPI backend skeleton
- [ ] Setup React frontend with TypeScript
- [ ] Implement basic WebSocket communication
- [ ] Port core audio components

### **Week 3-4: Core Features**
- [ ] Implement async audio pipeline
- [ ] Add user authentication
- [ ] Create recipe management system
- [ ] Build conversation interface
- [ ] Add comprehensive testing

### **Week 5-6: Enhancement**
- [ ] Performance optimization
- [ ] Advanced UI features
- [ ] Error handling and recovery
- [ ] Documentation and guides

### **Week 7-8: Production**
- [ ] Container deployment setup
- [ ] Monitoring and logging
- [ ] Security hardening
- [ ] Load testing and optimization

## 🚀 **Success Metrics**

### **Technical Metrics:**
- Response latency < 200ms (vs current 2000ms)
- 99.9% uptime with proper error handling
- Support for 100+ concurrent users
- <1% error rate in voice recognition

### **User Experience Metrics:**
- Voice command success rate > 95%
- User session duration increase by 50%
- Recipe completion rate improvement
- User satisfaction scores > 4.5/5

## 📝 **Risk Mitigation**

### **Technical Risks:**
- **Audio Compatibility**: Extensive testing across devices/browsers
- **Performance**: Load testing and optimization before launch
- **Security**: Audio data privacy and secure API design

### **Project Risks:**
- **Timeline**: Iterative development with MVP milestones
- **Complexity**: Modular architecture for manageable components
- **Resources**: Clear documentation and knowledge transfer

## 🎯 **Next Steps**

1. **Create new repository**: `hey_chef_v2` with clean architecture
2. **Setup development environment**: Docker, databases, tooling
3. **Begin Phase 1 implementation**: FastAPI backend + React frontend
4. **Maintain current app**: Keep Streamlit version running during migration
5. **Testing strategy**: Parallel testing of new vs old implementation

This migration plan transforms Hey Chef from a prototype into a production-ready voice assistant that can scale to thousands of users while providing a superior user experience.