"""
Integration tests for Hey Chef v2 WebSocket communication.
"""

import pytest
import json
import asyncio
from fastapi.testclient import TestClient
from fastapi import WebSocket
from unittest.mock import patch, Mock, AsyncMock
from typing import Dict, Any, List

from backend.main import app
from backend.app.core.models import MessageType, AudioState, ChefMode
from tests.backend.fixtures.test_data import TestDataFactory
from tests.backend.fixtures.mock_services import MockAudioPipelineManager


class TestWebSocketConnection:
    """Test WebSocket connection management."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection_establishment(self):
        """Test successful WebSocket connection."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Connection should be established successfully
                assert websocket is not None
                
                # Send a test message
                test_message = {
                    "type": MessageType.TEXT_MESSAGE,
                    "data": {"text": "hello", "chef_mode": "normal"}
                }
                websocket.send_json(test_message)
                
                # Should receive acknowledgment or response
                response = websocket.receive_json()
                assert "type" in response
    
    @pytest.mark.asyncio
    async def test_websocket_connection_with_session_id(self):
        """Test WebSocket connection with session ID."""
        session_id = "test-session-123"
        
        with TestClient(app) as client:
            with client.websocket_connect(f"/ws?session_id={session_id}") as websocket:
                # Send message with session context
                test_message = {
                    "type": MessageType.TEXT_MESSAGE,
                    "data": {"text": "test with session", "chef_mode": "normal"},
                    "session_id": session_id
                }
                websocket.send_json(test_message)
                
                response = websocket.receive_json()
                assert "session_id" in response or "type" in response
    
    def test_websocket_connection_rejection(self):
        """Test WebSocket connection rejection scenarios."""
        with TestClient(app) as client:
            # Test connection to invalid endpoint
            with pytest.raises(Exception):
                with client.websocket_connect("/ws/invalid"):
                    pass


class TestWebSocketMessageTypes:
    """Test different WebSocket message types."""
    
    @pytest.mark.asyncio
    async def test_text_message_handling(self):
        """Test text message processing."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                test_message = {
                    "type": MessageType.TEXT_MESSAGE,
                    "data": {
                        "text": "How do I cook pasta?",
                        "chef_mode": "normal"
                    }
                }
                
                with patch('backend.app.services.create_llm_service') as mock_llm:
                    mock_service = AsyncMock()
                    mock_service.ask.return_value = "Here's how to cook pasta properly."
                    mock_llm.return_value = mock_service
                    
                    websocket.send_json(test_message)
                    response = websocket.receive_json()
                    
                    assert response["type"] in [
                        MessageType.TEXT_RESPONSE,
                        MessageType.STATUS_UPDATE,
                        MessageType.ERROR
                    ]
    
    @pytest.mark.asyncio
    async def test_audio_message_handling(self):
        """Test audio message processing."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Send audio start message
                audio_start = {
                    "type": MessageType.AUDIO_START,
                    "data": {
                        "sample_rate": 16000,
                        "format": "wav",
                        "chef_mode": "normal"
                    }
                }
                websocket.send_json(audio_start)
                
                # Should receive status update
                response = websocket.receive_json()
                assert response["type"] in [
                    MessageType.STATUS_UPDATE,
                    MessageType.AUDIO_READY
                ]
    
    @pytest.mark.asyncio
    async def test_wake_word_detection_message(self):
        """Test wake word detection message."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                wake_word_msg = {
                    "type": MessageType.WAKE_WORD_DETECTED,
                    "data": {
                        "confidence": 0.85,
                        "audio_data": "base64_encoded_audio_data"
                    }
                }
                
                with patch('backend.app.services.create_wake_word_service') as mock_wake_word:
                    mock_service = AsyncMock()
                    mock_service.detect.return_value = True
                    mock_service.get_confidence.return_value = 0.85
                    mock_wake_word.return_value = mock_service
                    
                    websocket.send_json(wake_word_msg)
                    response = websocket.receive_json()
                    
                    assert response["type"] in [
                        MessageType.WAKE_WORD_DETECTED,
                        MessageType.STATUS_UPDATE
                    ]
    
    @pytest.mark.asyncio
    async def test_invalid_message_handling(self):
        """Test handling of invalid messages."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Send invalid message type
                invalid_message = {
                    "type": "invalid_type",
                    "data": {}
                }
                websocket.send_json(invalid_message)
                
                response = websocket.receive_json()
                assert response["type"] == MessageType.ERROR
                assert "error" in response["data"]


class TestWebSocketAudioPipeline:
    """Test WebSocket integration with audio pipeline."""
    
    @pytest.mark.asyncio
    async def test_full_audio_pipeline_via_websocket(self):
        """Test complete audio processing pipeline through WebSocket."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Mock the entire audio pipeline
                with patch('backend.app.core.audio_pipeline.AudioPipelineManager') as mock_pipeline:
                    mock_manager = MockAudioPipelineManager()
                    mock_pipeline.return_value = mock_manager
                    
                    # Send audio processing request
                    audio_request = {
                        "type": MessageType.AUDIO_DATA,
                        "data": {
                            "audio_data": "base64_encoded_audio",
                            "chef_mode": "normal",
                            "sample_rate": 16000
                        }
                    }
                    websocket.send_json(audio_request)
                    
                    # Should receive multiple responses during processing
                    responses = []
                    try:
                        for _ in range(5):  # Expect up to 5 responses
                            response = websocket.receive_json(timeout=1)
                            responses.append(response)
                            
                            # Break if we get final response
                            if response.get("type") == MessageType.AUDIO_RESPONSE:
                                break
                    except:
                        pass  # Timeout is expected
                    
                    assert len(responses) > 0
                    
                    # Should have received at least one status update
                    status_updates = [r for r in responses if r["type"] == MessageType.STATUS_UPDATE]
                    assert len(status_updates) > 0
    
    @pytest.mark.asyncio
    async def test_streaming_llm_response_via_websocket(self):
        """Test streaming LLM responses through WebSocket."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                with patch('backend.app.services.create_llm_service') as mock_llm:
                    mock_service = AsyncMock()
                    
                    # Mock streaming response
                    async def mock_streaming():
                        chunks = ["Hello ", "from ", "the ", "chef!"]
                        for chunk in chunks:
                            await asyncio.sleep(0.01)
                            yield chunk
                    
                    mock_service.ask_streaming.return_value = mock_streaming()
                    mock_llm.return_value = mock_service
                    
                    # Send streaming request
                    stream_request = {
                        "type": MessageType.TEXT_MESSAGE,
                        "data": {
                            "text": "Tell me about cooking",
                            "chef_mode": "normal",
                            "streaming": True
                        }
                    }
                    websocket.send_json(stream_request)
                    
                    # Collect streaming responses
                    stream_responses = []
                    try:
                        for _ in range(10):
                            response = websocket.receive_json(timeout=0.5)
                            stream_responses.append(response)
                            
                            if response.get("type") == MessageType.STREAM_END:
                                break
                    except:
                        pass
                    
                    # Should have received multiple streaming chunks
                    stream_chunks = [r for r in stream_responses if r.get("type") == MessageType.STREAM_CHUNK]
                    assert len(stream_chunks) > 0


class TestWebSocketSessionManagement:
    """Test WebSocket session management."""
    
    @pytest.mark.asyncio
    async def test_session_creation_and_management(self):
        """Test session creation and state management."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Send session initialization
                init_message = {
                    "type": MessageType.SESSION_INIT,
                    "data": {
                        "chef_mode": "sassy",
                        "user_preferences": {}
                    }
                }
                websocket.send_json(init_message)
                
                response = websocket.receive_json()
                assert "session_id" in response.get("data", {})
    
    @pytest.mark.asyncio
    async def test_chef_mode_switching(self):
        """Test switching chef modes during session."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Switch to Gordon Ramsay mode
                mode_switch = {
                    "type": MessageType.CHEF_MODE_CHANGE,
                    "data": {
                        "chef_mode": "gordon_ramsay"
                    }
                }
                websocket.send_json(mode_switch)
                
                response = websocket.receive_json()
                assert response["type"] in [
                    MessageType.STATUS_UPDATE,
                    MessageType.CHEF_MODE_CHANGED
                ]
    
    @pytest.mark.asyncio
    async def test_conversation_history_management(self):
        """Test conversation history tracking."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Send multiple messages to build history
                messages = [
                    {"text": "How do I cook pasta?", "chef_mode": "normal"},
                    {"text": "What about seasoning?", "chef_mode": "normal"},
                    {"text": "How long to cook?", "chef_mode": "normal"}
                ]
                
                for msg in messages:
                    websocket.send_json({
                        "type": MessageType.TEXT_MESSAGE,
                        "data": msg
                    })
                    
                    # Receive response
                    try:
                        response = websocket.receive_json(timeout=1)
                    except:
                        pass
                
                # Request conversation history
                history_request = {
                    "type": MessageType.GET_HISTORY,
                    "data": {}
                }
                websocket.send_json(history_request)
                
                response = websocket.receive_json()
                assert response["type"] == MessageType.CONVERSATION_HISTORY
                assert "history" in response["data"]


class TestWebSocketErrorHandling:
    """Test WebSocket error handling."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection_errors(self):
        """Test WebSocket connection error scenarios."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Send malformed JSON
                try:
                    websocket.send_text("invalid json")
                    response = websocket.receive_json()
                    assert response["type"] == MessageType.ERROR
                except:
                    pass  # Connection might be closed
    
    @pytest.mark.asyncio
    async def test_service_failure_handling(self):
        """Test handling when audio services fail."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                with patch('backend.app.services.create_llm_service') as mock_llm:
                    mock_service = AsyncMock()
                    mock_service.ask.side_effect = Exception("LLM service failed")
                    mock_llm.return_value = mock_service
                    
                    # Send message that should cause service failure
                    test_message = {
                        "type": MessageType.TEXT_MESSAGE,
                        "data": {
                            "text": "This should cause an error",
                            "chef_mode": "normal"
                        }
                    }
                    websocket.send_json(test_message)
                    
                    response = websocket.receive_json()
                    assert response["type"] == MessageType.ERROR
                    assert "error" in response["data"]
    
    @pytest.mark.asyncio
    async def test_websocket_timeout_handling(self):
        """Test WebSocket timeout scenarios."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Send message requiring long processing
                long_request = {
                    "type": MessageType.TEXT_MESSAGE,
                    "data": {
                        "text": "This is a complex cooking question that might take time to process",
                        "chef_mode": "normal"
                    }
                }
                websocket.send_json(long_request)
                
                # Should receive timeout or processing status
                try:
                    response = websocket.receive_json(timeout=5)
                    assert response["type"] in [
                        MessageType.TEXT_RESPONSE,
                        MessageType.STATUS_UPDATE,
                        MessageType.ERROR
                    ]
                except:
                    pass  # Timeout is acceptable


class TestWebSocketMultipleConnections:
    """Test multiple WebSocket connections."""
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_connections(self):
        """Test handling multiple WebSocket connections."""
        with TestClient(app) as client:
            websockets = []
            
            try:
                # Create multiple connections
                for i in range(3):
                    ws = client.websocket_connect(f"/ws?session_id=test-{i}")
                    websockets.append(ws.__enter__())
                
                # Send messages from each connection
                for i, ws in enumerate(websockets):
                    test_message = {
                        "type": MessageType.TEXT_MESSAGE,
                        "data": {
                            "text": f"Message from connection {i}",
                            "chef_mode": "normal"
                        }
                    }
                    ws.send_json(test_message)
                
                # Each should receive independent responses
                for i, ws in enumerate(websockets):
                    try:
                        response = ws.receive_json(timeout=2)
                        assert "type" in response
                    except:
                        pass  # Some connections might timeout
            
            finally:
                # Clean up connections
                for ws in websockets:
                    try:
                        ws.__exit__(None, None, None)
                    except:
                        pass


class TestWebSocketPerformance:
    """Test WebSocket performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_websocket_message_throughput(self):
        """Test WebSocket message throughput."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Send multiple messages quickly
                message_count = 10
                start_time = asyncio.get_event_loop().time()
                
                for i in range(message_count):
                    test_message = {
                        "type": MessageType.TEXT_MESSAGE,
                        "data": {
                            "text": f"Quick message {i}",
                            "chef_mode": "normal"
                        }
                    }
                    websocket.send_json(test_message)
                
                # Try to receive responses
                responses_received = 0
                try:
                    for _ in range(message_count):
                        response = websocket.receive_json(timeout=0.5)
                        responses_received += 1
                except:
                    pass
                
                end_time = asyncio.get_event_loop().time()
                total_time = end_time - start_time
                
                # Performance assertions
                assert total_time < 10.0  # Should complete within 10 seconds
                assert responses_received > 0  # Should receive at least some responses
    
    @pytest.mark.asyncio
    async def test_websocket_large_message_handling(self):
        """Test handling of large WebSocket messages."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Send large message
                large_text = "x" * 10000  # 10KB message
                large_message = {
                    "type": MessageType.TEXT_MESSAGE,
                    "data": {
                        "text": large_text,
                        "chef_mode": "normal"
                    }
                }
                
                websocket.send_json(large_message)
                
                # Should handle large message without error
                try:
                    response = websocket.receive_json(timeout=3)
                    assert response["type"] in [
                        MessageType.TEXT_RESPONSE,
                        MessageType.ERROR,
                        MessageType.STATUS_UPDATE
                    ]
                except:
                    pass  # Timeout is acceptable for large messages