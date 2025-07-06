"""
Pydantic models and schemas for Hey Chef v2 backend.
Comprehensive data models for WebSocket communication, audio processing, recipes, and user sessions.
"""
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic.types import UUID4
from pydantic import ConfigDict


# Base Models
class TimestampedModel(BaseModel):
    """Base model with timestamps"""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Enums
class MessageType(str, Enum):
    """WebSocket message types"""
    # Audio messages
    AUDIO_START = "audio_start"
    AUDIO_DATA = "audio_data"
    AUDIO_END = "audio_end"
    AUDIO_PROCESSED = "audio_processed"
    AUDIO_STATUS = "audio_status"
    
    # Wake word messages
    WAKE_WORD_DETECTED = "wake_word_detected"
    WAKE_WORD_LISTENING = "wake_word_listening"
    
    # Speech processing messages
    SPEECH_TO_TEXT = "speech_to_text"
    TEXT_TO_SPEECH = "text_to_speech"
    TTS_COMPLETE = "tts_complete"
    
    # AI/Chat messages
    AI_THINKING = "ai_thinking"
    AI_RESPONSE = "ai_response"
    AI_RESPONSE_STREAM = "ai_response_stream"
    AI_RESPONSE_COMPLETE = "ai_response_complete"
    
    # System messages
    CONNECTION = "connection"
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_CLOSED = "connection_closed"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    STATUS_UPDATE = "status_update"
    
    # Session messages
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    SESSION_UPDATE = "session_update"
    
    # Recipe messages
    RECIPE_LOADED = "recipe_loaded"
    RECIPE_UPDATED = "recipe_updated"
    
    # Frontend compatibility messages
    TEXT_MESSAGE = "text_message"
    SETTINGS_UPDATED = "settings_updated"


class AudioState(str, Enum):
    """Audio processing pipeline states"""
    IDLE = "idle"
    LISTENING_WAKE_WORD = "listening_wake_word"
    WAKE_WORD_DETECTED = "wake_word_detected"
    RECORDING = "recording"
    PROCESSING_AUDIO = "processing_audio"
    TRANSCRIBING = "transcribing"
    AI_PROCESSING = "ai_processing"
    GENERATING_SPEECH = "generating_speech"
    PLAYING_SPEECH = "playing_speech"
    ERROR = "error"


class ChefMode(str, Enum):
    """Chef personality modes"""
    NORMAL = "normal"
    SASSY = "sassy"
    GORDON_RAMSAY = "gordon_ramsay"


class AudioFormat(str, Enum):
    """Supported audio formats"""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    WEBM = "webm"


class TTSProvider(str, Enum):
    """Text-to-speech providers"""
    MACOS = "macos"
    OPENAI = "openai"


# WebSocket Message Models
class BaseMessage(BaseModel):
    """Base WebSocket message"""
    type: MessageType
    session_id: UUID4
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message_id: UUID4 = Field(default_factory=uuid.uuid4)


class AudioStartMessage(BaseMessage):
    """Audio recording start message"""
    type: MessageType = MessageType.AUDIO_START
    sample_rate: int = 16000
    channels: int = 1
    format: AudioFormat = AudioFormat.WAV


class AudioDataMessage(BaseMessage):
    """Audio data chunk message"""
    type: MessageType = MessageType.AUDIO_DATA
    audio_data: bytes
    chunk_size: int
    sequence_number: int


class AudioEndMessage(BaseMessage):
    """Audio recording end message"""
    type: MessageType = MessageType.AUDIO_END
    total_chunks: int
    total_duration: float


class WakeWordMessage(BaseMessage):
    """Wake word detection message"""
    type: MessageType = MessageType.WAKE_WORD_DETECTED
    confidence: float = Field(ge=0.0, le=1.0)
    keyword: str = "hey chef"


class SpeechToTextMessage(BaseMessage):
    """Speech-to-text result message"""
    type: MessageType = MessageType.SPEECH_TO_TEXT
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    language: Optional[str] = None
    processing_time: float


class AIResponseMessage(BaseMessage):
    """AI response message"""
    type: MessageType = MessageType.AI_RESPONSE
    text: str
    chef_mode: ChefMode
    tokens_used: int
    processing_time: float
    is_streaming: bool = False


class AIResponseStreamMessage(BaseMessage):
    """AI response streaming chunk message"""
    type: MessageType = MessageType.AI_RESPONSE_STREAM
    text_chunk: str
    is_final: bool = False
    chunk_number: int


class TextToSpeechMessage(BaseMessage):
    """Text-to-speech message"""
    type: MessageType = MessageType.TEXT_TO_SPEECH
    text: str
    voice: str
    provider: TTSProvider
    audio_data: Optional[bytes] = None
    audio_url: Optional[str] = None


class ErrorMessage(BaseMessage):
    """Error message"""
    type: MessageType = MessageType.ERROR
    error_code: str
    error_message: str
    error_details: Optional[Dict[str, Any]] = None


class StatusUpdateMessage(BaseMessage):
    """Status update message"""
    type: MessageType = MessageType.STATUS_UPDATE
    audio_state: AudioState
    is_processing: bool = False
    current_operation: Optional[str] = None


# Audio Processing Models
class AudioProcessingRequest(BaseModel):
    """Audio processing request"""
    session_id: UUID4
    audio_data: bytes
    sample_rate: int = 16000
    format: AudioFormat = AudioFormat.WAV
    max_duration: int = 30


class AudioProcessingResponse(BaseResponse):
    """Audio processing response"""
    transcription: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    processing_time: float
    audio_duration: float
    language: Optional[str] = None


class WakeWordDetectionRequest(BaseModel):
    """Wake word detection request"""
    audio_data: bytes
    sensitivity: float = Field(default=0.7, ge=0.0, le=1.0)


class WakeWordDetectionResponse(BaseResponse):
    """Wake word detection response"""
    detected: bool
    confidence: float = Field(ge=0.0, le=1.0)
    keyword: str
    detection_time: float


class TTSRequest(BaseModel):
    """Text-to-speech request"""
    text: str = Field(min_length=1, max_length=4000)
    voice: Optional[str] = None
    provider: TTSProvider = TTSProvider.MACOS
    speed: float = Field(default=1.0, ge=0.25, le=4.0)
    pitch: float = Field(default=1.0, ge=0.0, le=2.0)


class TTSResponse(BaseResponse):
    """Text-to-speech response"""
    audio_data: Optional[bytes] = None
    audio_url: Optional[str] = None
    audio_format: AudioFormat
    duration: float
    provider: TTSProvider


# Recipe Models
class Ingredient(BaseModel):
    """Recipe ingredient"""
    name: str
    amount: Optional[str] = None
    unit: Optional[str] = None
    notes: Optional[str] = None


class RecipeStep(BaseModel):
    """Recipe step"""
    step_number: int = Field(ge=1)
    instruction: str
    duration: Optional[str] = None
    temperature: Optional[str] = None
    notes: Optional[str] = None


class NutritionInfo(BaseModel):
    """Nutrition information"""
    calories: Optional[int] = None
    protein: Optional[str] = None
    carbs: Optional[str] = None
    fat: Optional[str] = None
    fiber: Optional[str] = None
    sugar: Optional[str] = None


class Recipe(TimestampedModel):
    """Recipe model"""
    id: UUID4 = Field(default_factory=uuid.uuid4)
    title: str
    description: Optional[str] = None
    cuisine_type: Optional[str] = None
    difficulty: Optional[str] = None
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None
    total_time: Optional[str] = None
    servings: Optional[int] = None
    ingredients: List[Ingredient] = []
    steps: List[RecipeStep] = []
    nutrition: Optional[NutritionInfo] = None
    tags: List[str] = []
    source: Optional[str] = None
    image_url: Optional[str] = None


class RecipeQuery(BaseModel):
    """Recipe query parameters"""
    search_term: Optional[str] = None
    cuisine_type: Optional[str] = None
    difficulty: Optional[str] = None
    max_prep_time: Optional[int] = None
    dietary_restrictions: List[str] = []
    ingredients: List[str] = []
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class RecipeResponse(BaseResponse):
    """Recipe response"""
    recipe: Optional[Recipe] = None
    recipes: List[Recipe] = []
    total_count: int = 0


# User Session Models
class SessionSettings(BaseModel):
    """User session settings"""
    chef_mode: ChefMode = ChefMode.NORMAL
    use_streaming: bool = False
    use_history: bool = True
    tts_enabled: bool = True
    tts_provider: TTSProvider = TTSProvider.MACOS
    tts_voice: Optional[str] = None
    wake_word_enabled: bool = True
    wake_word_sensitivity: float = Field(default=0.7, ge=0.0, le=1.0)


class ConversationMessage(TimestampedModel):
    """Conversation message"""
    id: UUID4 = Field(default_factory=uuid.uuid4)
    role: str  # "user" or "assistant"
    content: str
    chef_mode: Optional[ChefMode] = None
    tokens_used: Optional[int] = None
    processing_time: Optional[float] = None


class UserSession(TimestampedModel):
    """User session model"""
    id: UUID4 = Field(default_factory=uuid.uuid4)
    user_id: Optional[str] = None  # For future user authentication
    is_active: bool = True
    settings: SessionSettings = Field(default_factory=SessionSettings)
    current_recipe: Optional[Recipe] = None
    conversation_history: List[ConversationMessage] = []
    audio_state: AudioState = AudioState.IDLE
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('conversation_history')
    @classmethod
    def limit_history_size(cls, v):
        # Keep only last 50 messages to prevent memory bloat
        return v[-50:] if len(v) > 50 else v


class SessionCreateRequest(BaseModel):
    """Session creation request"""
    settings: Optional[SessionSettings] = None
    recipe_id: Optional[UUID4] = None


class SessionUpdateRequest(BaseModel):
    """Session update request"""
    settings: Optional[SessionSettings] = None
    recipe_id: Optional[UUID4] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionResponse(BaseResponse):
    """Session response"""
    session: Optional[UserSession] = None


# AI Processing Models
class AIRequest(BaseModel):
    """AI processing request"""
    session_id: UUID4
    message: str
    chef_mode: ChefMode = ChefMode.NORMAL
    use_history: bool = True
    use_streaming: bool = False
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    recipe_context: Optional[Recipe] = None


class AIResponse(BaseResponse):
    """AI processing response"""
    response_text: str
    chef_mode: ChefMode
    tokens_used: int
    processing_time: float
    conversation_id: UUID4


# Audio Pipeline State Models
class AudioPipelineState(BaseModel):
    """Audio processing pipeline state"""
    session_id: UUID4
    current_state: AudioState = AudioState.IDLE
    is_processing: bool = False
    wake_word_active: bool = True
    recording_active: bool = False
    current_operation: Optional[str] = None
    error_message: Optional[str] = None
    last_state_change: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processing_start_time: Optional[datetime] = None
    
    def transition_to(self, new_state: AudioState, operation: Optional[str] = None):
        """Transition to a new state"""
        self.current_state = new_state
        self.current_operation = operation
        self.last_state_change = datetime.now(timezone.utc)
        self.is_processing = new_state in [
            AudioState.PROCESSING_AUDIO,
            AudioState.TRANSCRIBING,
            AudioState.AI_PROCESSING,
            AudioState.GENERATING_SPEECH
        ]
        if self.is_processing and not self.processing_start_time:
            self.processing_start_time = datetime.now(timezone.utc)
        elif not self.is_processing:
            self.processing_start_time = None


# Health Check Models
class HealthCheckResponse(BaseResponse):
    """Health check response"""
    status: str = "healthy"
    version: str = "2.0.0"
    uptime: float
    components: Dict[str, str] = Field(default_factory=dict)


# Validation Models
class ValidationError(BaseModel):
    """Validation error details"""
    field: str
    message: str
    value: Any


class ValidationResponse(BaseResponse):
    """Validation response"""
    success: bool = False
    errors: List[ValidationError] = []


# File Upload Models
class FileUploadRequest(BaseModel):
    """File upload request"""
    filename: str
    content_type: str
    size: int = Field(ge=0, le=10_000_000)  # Max 10MB


class FileUploadResponse(BaseResponse):
    """File upload response"""
    file_id: UUID4
    filename: str
    url: str
    size: int


# WebSocket Connection Models
class ConnectionInfo(BaseModel):
    """WebSocket connection information"""
    session_id: UUID4
    client_ip: str
    user_agent: Optional[str] = None
    connected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message_count: int = 0


# Batch Processing Models
class BatchAudioRequest(BaseModel):
    """Batch audio processing request"""
    requests: List[AudioProcessingRequest] = Field(max_length=10)


class BatchAudioResponse(BaseResponse):
    """Batch audio processing response"""
    results: List[AudioProcessingResponse]
    processing_time: float
    success_count: int
    error_count: int


# Configuration Models for API
class ConfigResponse(BaseResponse):
    """Configuration response for client"""
    audio_config: Dict[str, Any]
    chef_modes: List[str]
    supported_languages: List[str]
    max_recording_duration: int
    websocket_url: str


# Additional API Models for compatibility
class WebSocketMessage(BaseModel):
    """WebSocket message model (compatibility)"""
    type: MessageType
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    client_id: Optional[str] = None


class AudioProcessRequest(BaseModel):
    """Audio processing request (compatibility)"""
    action: str
    audio_data: Optional[str] = None
    format: Optional[str] = "wav"
    sample_rate: Optional[int] = 16000


class AudioStatusResponse(BaseResponse):
    """Audio status response (compatibility)"""
    status: AudioState
    is_listening: bool
    is_processing: bool
    wake_word_detected: bool = False
    message: Optional[str] = None


class TranscriptionResponse(BaseResponse):
    """Transcription response (compatibility)"""
    text: str
    confidence: Optional[float] = None
    duration: Optional[float] = None
    language: Optional[str] = None


class ChatRequest(BaseModel):
    """Chat request (compatibility)"""
    message: str
    recipe_context: Optional[str] = None
    chef_mode: ChefMode = ChefMode.NORMAL
    use_history: bool = True
    conversation_history: Optional[List[Dict[str, str]]] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class ChatResponse(BaseResponse):
    """Chat response (compatibility)"""
    response: str
    chef_mode: ChefMode
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    processing_time: Optional[float] = None
    audio_url: Optional[str] = None
    
    model_config = {"protected_namespaces": ()}


class RecipeSearchRequest(BaseModel):
    """Recipe search request (compatibility)"""
    query: str
    category: Optional[str] = None
    cuisine: Optional[str] = None
    dietary_restrictions: Optional[List[str]] = None
    max_results: int = 10


class RecipeCreateRequest(BaseModel):
    """Recipe create request (compatibility)"""
    title: str
    description: Optional[str] = None
    ingredients: List[str]
    instructions: List[str]
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None
    category: Optional[str] = None
    cuisine: Optional[str] = None
    dietary_tags: Optional[List[str]] = None
    notes: Optional[str] = None


class RecipeUpdateRequest(BaseModel):
    """Recipe update request (compatibility)"""
    title: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[List[str]] = None
    instructions: Optional[List[str]] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None
    category: Optional[str] = None
    cuisine: Optional[str] = None
    dietary_tags: Optional[List[str]] = None
    notes: Optional[str] = None


class RecipeListResponse(BaseResponse):
    """Recipe list response (compatibility)"""
    recipes: List[Recipe]
    total: int
    page: int = 1
    per_page: int = 10
    has_more: bool = False


class ErrorResponse(BaseResponse):
    """Error response (compatibility)"""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class APIResponse(BaseResponse):
    """Generic API response (compatibility)"""
    data: Optional[Any] = None
    error: Optional[ErrorResponse] = None


# Type aliases for compatibility
WebSocketMessageType = MessageType
AudioStatus = AudioState