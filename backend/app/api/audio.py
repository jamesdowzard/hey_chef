"""
Audio API endpoints for Hey Chef v2.

HTTP endpoints for audio processing control, service health checks,
and audio configuration management.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel

from app.core.config import Settings
from app.core.models import AudioProcessingRequest, AudioProcessingResponse, ErrorResponse
from app.core.logger import get_logger
from app.services import create_wake_word_service, create_stt_service, create_tts_service, create_llm_service

logger = get_logger()
router = APIRouter()

class AudioHealthResponse(BaseModel):
    """Response model for audio service health check."""
    status: str
    services: Dict[str, str]
    configuration: Dict[str, Any]

class AudioConfigResponse(BaseModel):
    """Response model for audio configuration."""
    wake_word_sensitivity: float
    whisper_model_size: str
    sample_rate: int
    max_silence_sec: float
    speech_rate: int
    use_external_tts: bool

class TTSRequest(BaseModel):
    """Request model for text-to-speech."""
    text: str
    voice: Optional[str] = None
    speed: Optional[float] = None

async def get_settings() -> Settings:
    """Dependency to get settings."""
    return Settings()

@router.get("/health", response_model=AudioHealthResponse)
async def audio_health_check(settings: Settings = Depends(get_settings)):
    """
    Check health status of all audio services.
    
    Returns detailed status of wake word detection, STT, TTS, and LLM services.
    """
    try:
        services_status = {}
        
        # Check wake word service
        try:
            wake_word_service = create_wake_word_service()
            services_status["wake_word"] = "healthy"
        except Exception as e:
            logger.error(f"Wake word service health check failed: {e}")
            services_status["wake_word"] = f"unhealthy: {str(e)}"
        
        # Check STT service
        try:
            stt_service = create_stt_service()
            services_status["speech_to_text"] = "healthy"
        except Exception as e:
            logger.error(f"STT service health check failed: {e}")
            services_status["speech_to_text"] = f"unhealthy: {str(e)}"
        
        # Check TTS service
        try:
            tts_service = create_tts_service()
            services_status["text_to_speech"] = "healthy"
        except Exception as e:
            logger.error(f"TTS service health check failed: {e}")
            services_status["text_to_speech"] = f"unhealthy: {str(e)}"
        
        # Check LLM service
        try:
            llm_service = create_llm_service()
            services_status["llm"] = "healthy"
        except Exception as e:
            logger.error(f"LLM service health check failed: {e}")
            services_status["llm"] = f"unhealthy: {str(e)}"
        
        # Determine overall status
        overall_status = "healthy" if all(
            status == "healthy" for status in services_status.values()
        ) else "degraded"
        
        return AudioHealthResponse(
            status=overall_status,
            services=services_status,
            configuration={
                "whisper_model": settings.audio.whisper_model_size,
                "wake_word_sensitivity": settings.audio.wake_word_sensitivity,
                "sample_rate": settings.audio.sample_rate,
                "llm_model": settings.llm.model
            }
        )
        
    except Exception as e:
        logger.error(f"Audio health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/config", response_model=AudioConfigResponse)
async def get_audio_config(settings: Settings = Depends(get_settings)):
    """Get current audio configuration."""
    try:
        return AudioConfigResponse(
            wake_word_sensitivity=settings.audio.wake_word_sensitivity,
            whisper_model_size=settings.audio.whisper_model_size,
            sample_rate=settings.audio.sample_rate,
            max_silence_sec=settings.audio.max_silence_sec,
            speech_rate=settings.audio.speech_rate,
            use_external_tts=settings.audio.use_external_tts
        )
    except Exception as e:
        logger.error(f"Failed to get audio config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get audio config: {str(e)}")

@router.post("/transcribe", response_model=Dict[str, Any])
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    settings: Settings = Depends(get_settings)
):
    """
    Transcribe uploaded audio file to text.
    
    Accepts audio files and returns transcribed text using Whisper.
    """
    try:
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Read audio file content
        audio_content = await audio_file.read()
        
        # Create STT service and transcribe
        stt_service = create_stt_service()
        async with stt_service:
            # Save temporary file for transcription
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_file.write(audio_content)
                temp_file_path = temp_file.name
            
            try:
                text = await stt_service.transcribe_file(temp_file_path)
                
                return {
                    "status": "success",
                    "text": text,
                    "filename": audio_file.filename,
                    "size": len(audio_content)
                }
            finally:
                # Cleanup temp file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@router.post("/synthesize", response_model=Dict[str, Any])
async def synthesize_speech(
    request: TTSRequest,
    settings: Settings = Depends(get_settings)
):
    """
    Synthesize text to speech.
    
    Converts text to audio using configured TTS service.
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Create TTS service
        tts_service = create_tts_service()
        async with tts_service:
            # Synthesize speech
            audio_file_path = await tts_service.speak_async(
                text=request.text,
                voice=request.voice,
                speed=request.speed
            )
            
            return {
                "status": "success",
                "message": "Speech synthesized successfully",
                "audio_file": audio_file_path,
                "text": request.text,
                "voice": request.voice or settings.audio.external_voice
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Speech synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")

@router.post("/test-wake-word", response_model=Dict[str, Any])
async def test_wake_word(settings: Settings = Depends(get_settings)):
    """
    Test wake word detection functionality.
    
    Starts wake word detection for a short period to verify it's working.
    """
    try:
        import asyncio
        
        wake_word_service = create_wake_word_service()
        detection_results = []
        
        def detection_callback(detected: bool):
            detection_results.append({
                "detected": detected,
                "timestamp": asyncio.get_event_loop().time()
            })
        
        async with wake_word_service:
            # Set up detection callback
            wake_word_service.set_detection_callback(detection_callback)
            
            # Start detection for 5 seconds
            await wake_word_service.start()
            await asyncio.sleep(5)
            await wake_word_service.stop()
        
        return {
            "status": "success",
            "message": "Wake word test completed",
            "duration_seconds": 5,
            "detections": detection_results,
            "total_detections": len([r for r in detection_results if r["detected"]])
        }
        
    except Exception as e:
        logger.error(f"Wake word test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Wake word test failed: {str(e)}")

@router.get("/models", response_model=Dict[str, Any])
async def get_available_models(settings: Settings = Depends(get_settings)):
    """
    Get information about available audio models.
    
    Returns details about Whisper models, TTS voices, and LLM models.
    """
    try:
        return {
            "whisper_models": [
                "tiny", "base", "small", "medium", "large"
            ],
            "current_whisper_model": settings.audio.whisper_model_size,
            "tts_voices": {
                "macos": settings.audio.macos_voice,
                "openai": settings.audio.external_voice,
                "current": settings.audio.external_voice if settings.use_external_tts else settings.audio.macos_voice
            },
            "llm_models": settings.llm.available_models,
            "current_llm_model": settings.llm.model,
            "chef_modes": ["normal", "sassy", "gordon_ramsay"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get model information: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model information: {str(e)}")

@router.post("/validate-api-keys", response_model=Dict[str, Any])
async def validate_api_keys(settings: Settings = Depends(get_settings)):
    """
    Validate required API keys for audio services.
    
    Checks OpenAI API key and Picovoice access key.
    """
    try:
        validation_results = {}
        
        # Check OpenAI API key
        try:
            if not settings.openai_api_key:
                validation_results["openai"] = "invalid: API key not set"
            else:
                # Try to create LLM service
                llm_service = create_llm_service()
                async with llm_service:
                    validation_results["openai"] = "valid"
        except Exception as e:
            validation_results["openai"] = f"invalid: {str(e)}"
        
        # Check Picovoice access key
        try:
            wake_word_service = create_wake_word_service()
            validation_results["picovoice"] = "valid"
        except Exception as e:
            validation_results["picovoice"] = f"invalid: {str(e)}"
        
        # Overall status
        all_valid = all("valid" in status for status in validation_results.values())
        
        return {
            "status": "success" if all_valid else "warning",
            "message": "All API keys valid" if all_valid else "Some API keys are invalid",
            "openai_valid": "valid" in validation_results.get("openai", ""),
            "picovoice_valid": "valid" in validation_results.get("picovoice", ""),
            "api_keys": validation_results
        }
        
    except Exception as e:
        logger.error(f"API key validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"API key validation failed: {str(e)}")

@router.get("/stats", response_model=Dict[str, Any])
async def get_audio_stats():
    """
    Get audio processing statistics.
    
    Returns metrics about audio processing performance and usage.
    """
    try:
        # TODO: Implement actual statistics collection
        return {
            "status": "success",
            "stats": {
                "total_transcriptions": 0,
                "total_synthesized_speech": 0,
                "wake_word_detections": 0,
                "average_transcription_time": 0.0,
                "average_synthesis_time": 0.0,
                "uptime_seconds": 0
            },
            "message": "Statistics collection not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Failed to get audio stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get audio stats: {str(e)}")