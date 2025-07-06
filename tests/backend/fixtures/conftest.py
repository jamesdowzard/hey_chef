"""
Pytest configuration and fixtures for Hey Chef v2 backend testing.
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import the FastAPI app
from backend.main import app
from backend.app.core.config import Settings
from backend.app.core.models import *
from backend.app.services import *


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with safe defaults."""
    settings = Settings()
    settings.environment = "test"
    settings.openai_api_key = "test-openai-key"
    settings.pico_access_key = "test-pico-key"
    settings.audio.use_external_tts = False  # Use mock TTS for tests
    settings.recipe_api_url = "http://localhost:3333"
    return settings


@pytest.fixture
def test_client(test_settings: Settings) -> TestClient:
    """Create a test client for the FastAPI app."""
    # Override the settings dependency
    app.dependency_overrides[Settings] = lambda: test_settings
    client = TestClient(app)
    yield client
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
async def async_client(test_settings: Settings) -> AsyncGenerator[AsyncClient, None]:
    """Create an async client for testing async endpoints."""
    app.dependency_overrides[Settings] = lambda: test_settings
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing LLM service."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "Test response from chef"
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_wake_word_service():
    """Mock wake word service for testing."""
    mock_service = AsyncMock(spec=WakeWordService)
    mock_service.detect.return_value = True
    mock_service.start.return_value = None
    mock_service.stop.return_value = None
    mock_service.cleanup.return_value = None
    return mock_service


@pytest.fixture
def mock_stt_service():
    """Mock speech-to-text service for testing."""
    mock_service = AsyncMock(spec=STTService)
    mock_service.transcribe.return_value = "test transcription"
    mock_service.cleanup.return_value = None
    return mock_service


@pytest.fixture
def mock_tts_service():
    """Mock text-to-speech service for testing."""
    mock_service = AsyncMock(spec=TTSService)
    mock_service.synthesize.return_value = b"mock audio data"
    mock_service.cleanup.return_value = None
    return mock_service


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing."""
    mock_service = AsyncMock(spec=LLMService)
    mock_service.ask.return_value = "Test response from chef"
    mock_service.ask_streaming.return_value = async_generator_mock(["Test ", "response ", "from ", "chef"])
    mock_service.cleanup.return_value = None
    return mock_service


async def async_generator_mock(items):
    """Helper to create async generator for mocking streaming responses."""
    for item in items:
        yield item


@pytest.fixture
def sample_audio_data():
    """Sample audio data for testing."""
    return b"fake audio data for testing purposes"


@pytest.fixture
def sample_recipe_data():
    """Sample recipe data for testing."""
    return {
        "id": "test-recipe-123",
        "title": "Test Recipe",
        "description": "A test recipe for unit testing",
        "ingredients": ["1 cup test ingredient", "2 tbsp mock seasoning"],
        "instructions": ["Mix ingredients", "Cook until done"],
        "prep_time": 10,
        "cook_time": 20,
        "servings": 4,
        "category": "test"
    }


@pytest.fixture
def sample_websocket_messages():
    """Sample WebSocket messages for testing."""
    return {
        "audio_start": {
            "type": MessageType.AUDIO_START,
            "data": {"session_id": "test-session", "chef_mode": "normal"}
        },
        "audio_data": {
            "type": MessageType.AUDIO_DATA,
            "data": {"audio": "base64encodedaudio", "format": "wav"}
        },
        "text_message": {
            "type": MessageType.TEXT_MESSAGE,
            "data": {"text": "How do I cook pasta?", "chef_mode": "sassy"}
        }
    }


@pytest.fixture
def mock_audio_pipeline():
    """Mock audio pipeline manager for testing."""
    mock_pipeline = AsyncMock()
    mock_pipeline.process_audio_request.return_value = AudioProcessingResponse(
        success=True,
        text_response="Test chef response",
        audio_response=b"mock audio response",
        processing_time=0.1,
        chef_mode="normal"
    )
    return mock_pipeline


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection for testing."""
    mock_ws = AsyncMock()
    mock_ws.send_text = AsyncMock()
    mock_ws.send_bytes = AsyncMock()
    mock_ws.receive_text = AsyncMock()
    mock_ws.receive_bytes = AsyncMock()
    mock_ws.accept = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset any singleton instances between tests."""
    # Reset any global state or singletons here
    yield
    # Cleanup after test
    pass


# Helper functions for tests
def assert_valid_response(response, expected_status=200):
    """Assert that a response is valid and has expected status."""
    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json() is not None


def assert_error_response(response, expected_status=500):
    """Assert that a response is an error with expected status."""
    assert response.status_code == expected_status
    data = response.json()
    assert "error" in data
    assert data["status_code"] == expected_status


async def assert_websocket_response(websocket, expected_type: MessageType):
    """Assert that WebSocket sends expected message type."""
    # Implementation depends on your WebSocket testing setup
    pass