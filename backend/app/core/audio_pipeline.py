"""
Async audio processing pipeline orchestration for Hey Chef v2.
Coordinates wake word detection, speech-to-text, AI processing, and text-to-speech.
"""
import asyncio
import logging
import time
from typing import Dict, Optional, Callable, Any, List
from datetime import datetime, timezone
from uuid import UUID

from .models import (
    AudioState, AudioPipelineState, MessageType, ChefMode,
    WakeWordMessage, SpeechToTextMessage, AIResponseMessage, 
    TextToSpeechMessage, ErrorMessage, StatusUpdateMessage,
    AudioProcessingRequest, AudioProcessingResponse,
    WakeWordDetectionRequest, WakeWordDetectionResponse,
    TTSRequest, TTSResponse, UserSession, ConversationMessage
)
from .config import Settings


class AudioPipelineError(Exception):
    """Audio pipeline specific error"""
    pass


class AudioPipelineManager:
    """
    Manages the complete audio processing pipeline with async orchestration.
    Handles state transitions, error recovery, and WebSocket communication.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Pipeline state management
        self.session_states: Dict[UUID, AudioPipelineState] = {}
        self.session_locks: Dict[UUID, asyncio.Lock] = {}
        
        # Service instances (to be injected)
        self.wake_word_service = None
        self.stt_service = None
        self.ai_service = None
        self.tts_service = None
        self.session_manager = None
        
        # WebSocket callback for sending messages
        self.websocket_callback: Optional[Callable] = None
        
        # Pipeline performance metrics
        self.metrics = {
            "total_sessions": 0,
            "active_sessions": 0,
            "successful_processes": 0,
            "failed_processes": 0,
            "average_processing_time": 0.0
        }
    
    def inject_services(self, 
                       wake_word_service,
                       stt_service, 
                       ai_service,
                       tts_service,
                       session_manager):
        """Inject service dependencies"""
        self.wake_word_service = wake_word_service
        self.stt_service = stt_service
        self.ai_service = ai_service
        self.tts_service = tts_service
        self.session_manager = session_manager
    
    def set_websocket_callback(self, callback: Callable):
        """Set WebSocket message callback"""
        self.websocket_callback = callback
    
    async def create_session_pipeline(self, session_id: UUID) -> AudioPipelineState:
        """Create a new audio pipeline state for a session"""
        if session_id in self.session_states:
            return self.session_states[session_id]
        
        pipeline_state = AudioPipelineState(session_id=session_id)
        self.session_states[session_id] = pipeline_state
        self.session_locks[session_id] = asyncio.Lock()
        
        self.metrics["total_sessions"] += 1
        self.metrics["active_sessions"] += 1
        
        self.logger.info(f"Created audio pipeline for session {session_id}")
        return pipeline_state
    
    async def destroy_session_pipeline(self, session_id: UUID):
        """Clean up audio pipeline for a session"""
        if session_id in self.session_states:
            del self.session_states[session_id]
        if session_id in self.session_locks:
            del self.session_locks[session_id]
        
        self.metrics["active_sessions"] = max(0, self.metrics["active_sessions"] - 1)
        self.logger.info(f"Destroyed audio pipeline for session {session_id}")
    
    async def get_pipeline_state(self, session_id: UUID) -> Optional[AudioPipelineState]:
        """Get current pipeline state for a session"""
        return self.session_states.get(session_id)
    
    async def transition_state(self, session_id: UUID, new_state: AudioState, 
                             operation: Optional[str] = None):
        """Safely transition pipeline state and notify clients"""
        async with self.session_locks.get(session_id, asyncio.Lock()):
            if session_id in self.session_states:
                pipeline_state = self.session_states[session_id]
                old_state = pipeline_state.current_state
                pipeline_state.transition_to(new_state, operation)
                
                self.logger.debug(f"Session {session_id}: {old_state} -> {new_state}")
                
                # Send status update via WebSocket
                if self.websocket_callback:
                    status_message = StatusUpdateMessage(
                        session_id=session_id,
                        audio_state=new_state,
                        is_processing=pipeline_state.is_processing,
                        current_operation=operation
                    )
                    await self.websocket_callback(session_id, status_message)
    
    async def handle_error(self, session_id: UUID, error: Exception, 
                          error_code: str = "PIPELINE_ERROR"):
        """Handle pipeline errors with recovery"""
        pipeline_state = self.session_states.get(session_id)
        if pipeline_state:
            pipeline_state.current_state = AudioState.ERROR
            pipeline_state.error_message = str(error)
            pipeline_state.is_processing = False
        
        self.metrics["failed_processes"] += 1
        self.logger.error(f"Pipeline error in session {session_id}: {error}")
        
        # Send error message via WebSocket
        if self.websocket_callback:
            error_message = ErrorMessage(
                session_id=session_id,
                error_code=error_code,
                error_message=str(error),
                error_details={"pipeline_state": pipeline_state.current_state if pipeline_state else None}
            )
            await self.websocket_callback(session_id, error_message)
        
        # Attempt to recover to idle state after a brief delay
        await asyncio.sleep(1.0)
        await self.transition_state(session_id, AudioState.IDLE, "error_recovery")
    
    async def start_wake_word_listening(self, session_id: UUID):
        """Start wake word detection for a session"""
        try:
            await self.transition_state(session_id, AudioState.LISTENING_WAKE_WORD, 
                                      "wake_word_detection")
            
            # This would typically start a background task for wake word detection
            # For now, we'll simulate it with a placeholder
            if self.wake_word_service:
                # Background task would continuously listen for wake word
                self.logger.info(f"Started wake word listening for session {session_id}")
            
        except Exception as e:
            await self.handle_error(session_id, e, "WAKE_WORD_START_ERROR")
    
    async def process_wake_word_detection(self, session_id: UUID, 
                                        audio_data: bytes, 
                                        sensitivity: float = None) -> bool:
        """Process wake word detection"""
        try:
            if not self.wake_word_service:
                raise AudioPipelineError("Wake word service not available")
            
            # Use session-specific sensitivity or default
            pipeline_state = self.session_states.get(session_id)
            if not pipeline_state:
                raise AudioPipelineError("No pipeline state found for session")
            
            # Get user session for sensitivity (if session manager available)
            if self.session_manager:
                user_session = await self.session_manager.get_session(session_id)
                if user_session:
                    sensitivity = sensitivity or user_session.settings.wake_word_sensitivity
                else:
                    sensitivity = sensitivity or self.settings.audio.wake_word_sensitivity
            else:
                sensitivity = sensitivity or self.settings.audio.wake_word_sensitivity
            
            # Detect wake word
            request = WakeWordDetectionRequest(
                audio_data=audio_data,
                sensitivity=sensitivity
            )
            
            response = await self.wake_word_service.detect_wake_word(request)
            
            if response.detected:
                await self.transition_state(session_id, AudioState.WAKE_WORD_DETECTED, 
                                          "wake_word_detected")
                
                # Send wake word message
                if self.websocket_callback:
                    wake_word_message = WakeWordMessage(
                        session_id=session_id,
                        confidence=response.confidence,
                        keyword=response.keyword
                    )
                    await self.websocket_callback(session_id, wake_word_message)
                
                # Automatically start recording
                await self.start_audio_recording(session_id)
                return True
            
            return False
            
        except Exception as e:
            await self.handle_error(session_id, e, "WAKE_WORD_DETECTION_ERROR")
            return False
    
    async def start_audio_recording(self, session_id: UUID):
        """Start audio recording for speech input"""
        try:
            await self.transition_state(session_id, AudioState.RECORDING, "audio_recording")
            
            pipeline_state = self.session_states.get(session_id)
            if pipeline_state:
                pipeline_state.recording_active = True
            
            self.logger.info(f"Started audio recording for session {session_id}")
            
        except Exception as e:
            await self.handle_error(session_id, e, "RECORDING_START_ERROR")
    
    async def stop_audio_recording(self, session_id: UUID):
        """Stop audio recording"""
        try:
            pipeline_state = self.session_states.get(session_id)
            if pipeline_state:
                pipeline_state.recording_active = False
            
            await self.transition_state(session_id, AudioState.PROCESSING_AUDIO, 
                                      "processing_recorded_audio")
            
            self.logger.info(f"Stopped audio recording for session {session_id}")
            
        except Exception as e:
            await self.handle_error(session_id, e, "RECORDING_STOP_ERROR")
    
    async def process_audio_to_text(self, session_id: UUID, 
                                   audio_data: bytes, 
                                   sample_rate: int = 16000) -> Optional[str]:
        """Process recorded audio to text"""
        start_time = time.time()
        
        try:
            if not self.stt_service:
                raise AudioPipelineError("Speech-to-text service not available")
            
            await self.transition_state(session_id, AudioState.TRANSCRIBING, 
                                      "speech_to_text")
            
            # Prepare STT request
            request = AudioProcessingRequest(
                session_id=session_id,
                audio_data=audio_data,
                sample_rate=sample_rate,
                max_duration=self.settings.max_recording_duration
            )
            
            # Process audio to text
            response = await self.stt_service.transcribe_audio(request)
            processing_time = time.time() - start_time
            
            if response.success and response.transcription:
                # Send STT result
                if self.websocket_callback:
                    stt_message = SpeechToTextMessage(
                        session_id=session_id,
                        text=response.transcription,
                        confidence=response.confidence,
                        language=response.language,
                        processing_time=processing_time
                    )
                    await self.websocket_callback(session_id, stt_message)
                
                # Start AI processing
                await self.process_ai_response(session_id, response.transcription)
                return response.transcription
            else:
                raise AudioPipelineError("Failed to transcribe audio")
                
        except Exception as e:
            await self.handle_error(session_id, e, "STT_ERROR")
            return None
    
    async def process_ai_response(self, session_id: UUID, user_message: str):
        """Process AI response for user message"""
        start_time = time.time()
        
        try:
            if not self.ai_service:
                raise AudioPipelineError("AI service not available")
            
            await self.transition_state(session_id, AudioState.AI_PROCESSING, 
                                      "generating_ai_response")
            
            # Get user session for context (if session manager available)
            user_session = None
            if self.session_manager:
                user_session = await self.session_manager.get_session(session_id)
            
            if not user_session:
                # Use default session settings when no session manager
                from .models import UserSession
                user_session = UserSession()
            
            # Prepare AI request
            chef_mode = user_session.settings.chef_mode
            use_history = user_session.settings.use_history
            use_streaming = user_session.settings.use_streaming
            
            # Get chef mode configuration
            chef_config = self.settings.get_chef_mode_config(chef_mode.value)
            
            # Process with AI service
            ai_response = await self.ai_service.generate_response(
                message=user_message,
                session_id=session_id,
                chef_mode=chef_mode,
                use_history=use_history,
                use_streaming=use_streaming,
                max_tokens=chef_config.get("max_tokens"),
                temperature=chef_config.get("temperature"),
                recipe_context=user_session.current_recipe
            )
            
            processing_time = time.time() - start_time
            
            # Send AI response
            if self.websocket_callback:
                ai_message = AIResponseMessage(
                    session_id=session_id,
                    text=ai_response.response_text,
                    chef_mode=chef_mode,
                    tokens_used=ai_response.tokens_used,
                    processing_time=processing_time,
                    is_streaming=use_streaming
                )
                await self.websocket_callback(session_id, ai_message)
            
            # Update conversation history (if session manager available)
            if self.session_manager:
                await self.session_manager.add_conversation_message(
                    session_id, "user", user_message
                )
                await self.session_manager.add_conversation_message(
                    session_id, "assistant", ai_response.response_text, chef_mode
                )
            
            # Start TTS if enabled
            if user_session.settings.tts_enabled:
                await self.process_text_to_speech(session_id, ai_response.response_text)
            else:
                await self.transition_state(session_id, AudioState.IDLE, "response_complete")
            
            self.metrics["successful_processes"] += 1
            
        except Exception as e:
            await self.handle_error(session_id, e, "AI_PROCESSING_ERROR")
    
    async def process_text_to_speech(self, session_id: UUID, text: str):
        """Process text to speech"""
        try:
            if not self.tts_service:
                raise AudioPipelineError("Text-to-speech service not available")
            
            await self.transition_state(session_id, AudioState.GENERATING_SPEECH, 
                                      "text_to_speech")
            
            # Get user session for TTS preferences (if session manager available)
            user_session = None
            if self.session_manager:
                user_session = await self.session_manager.get_session(session_id)
            
            if not user_session:
                # Use default session settings when no session manager
                from .models import UserSession
                user_session = UserSession()
            
            # Prepare TTS request
            tts_request = TTSRequest(
                text=text,
                voice=user_session.settings.tts_voice,
                provider=user_session.settings.tts_provider,
                speed=1.0,  # Could be made configurable
                pitch=1.0   # Could be made configurable
            )
            
            # Generate speech
            tts_response = await self.tts_service.generate_speech(tts_request)
            
            if tts_response.success:
                await self.transition_state(session_id, AudioState.PLAYING_SPEECH, 
                                          "playing_speech")
                
                # Send TTS result
                if self.websocket_callback:
                    tts_message = TextToSpeechMessage(
                        session_id=session_id,
                        text=text,
                        voice=tts_request.voice or "default",
                        provider=tts_request.provider,
                        audio_data=tts_response.audio_data,
                        audio_url=tts_response.audio_url
                    )
                    await self.websocket_callback(session_id, tts_message)
                
                # Simulate speech playback duration
                await asyncio.sleep(tts_response.duration)
                
                # Return to listening state
                await self.transition_state(session_id, AudioState.LISTENING_WAKE_WORD, 
                                          "ready_for_next_interaction")
            else:
                raise AudioPipelineError("Failed to generate speech")
                
        except Exception as e:
            await self.handle_error(session_id, e, "TTS_ERROR")
    
    async def process_complete_pipeline(self, session_id: UUID, audio_data: bytes, 
                                      sample_rate: int = 16000) -> bool:
        """Process complete audio pipeline from recording to response"""
        try:
            # Check if session exists
            if session_id not in self.session_states:
                await self.create_session_pipeline(session_id)
            
            # Process audio to text
            transcription = await self.process_audio_to_text(session_id, audio_data, sample_rate)
            
            if transcription:
                # AI processing and TTS are handled in process_audio_to_text
                return True
            
            return False
            
        except Exception as e:
            await self.handle_error(session_id, e, "COMPLETE_PIPELINE_ERROR")
            return False
    
    async def reset_pipeline(self, session_id: UUID):
        """Reset pipeline to idle state"""
        try:
            pipeline_state = self.session_states.get(session_id)
            if pipeline_state:
                pipeline_state.is_processing = False
                pipeline_state.recording_active = False
                pipeline_state.error_message = None
                pipeline_state.processing_start_time = None
            
            await self.transition_state(session_id, AudioState.IDLE, "pipeline_reset")
            self.logger.info(f"Reset pipeline for session {session_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to reset pipeline for session {session_id}: {e}")
    
    async def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get pipeline performance metrics"""
        active_sessions = len([s for s in self.session_states.values() if s.is_processing])
        self.metrics["active_sessions"] = active_sessions
        
        return {
            **self.metrics,
            "current_sessions": len(self.session_states),
            "session_details": [
                {
                    "session_id": str(state.session_id),
                    "state": state.current_state.value,
                    "is_processing": state.is_processing,
                    "last_activity": state.last_state_change.isoformat()
                }
                for state in self.session_states.values()
            ]
        }
    
    async def cleanup_inactive_sessions(self, timeout_minutes: int = 60):
        """Clean up inactive sessions"""
        now = datetime.now(timezone.utc)
        inactive_sessions = []
        
        for session_id, state in self.session_states.items():
            minutes_inactive = (now - state.last_state_change).total_seconds() / 60
            if minutes_inactive > timeout_minutes and not state.is_processing:
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            await self.destroy_session_pipeline(session_id)
            self.logger.info(f"Cleaned up inactive session {session_id}")
        
        return len(inactive_sessions)