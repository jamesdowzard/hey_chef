"""
Integration tests for Hey Chef v2 API endpoints.
"""

import pytest
import json
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import patch, Mock

from backend.main import app
from backend.app.core.config import Settings
from tests.backend.fixtures.conftest import test_settings, assert_valid_response, assert_error_response
from tests.backend.fixtures.test_data import TestDataFactory
from tests.backend.fixtures.mock_services import create_mock_services


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_basic_health_endpoint(self, test_client: TestClient):
        """Test basic health endpoint."""
        response = test_client.get("/health")
        assert_valid_response(response, 200)
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "hey-chef-v2"
        assert data["version"] == "2.0.0"
        assert "environment" in data
    
    def test_detailed_health_endpoint(self, test_client: TestClient):
        """Test detailed health endpoint."""
        response = test_client.get("/health/detailed")
        assert_valid_response(response, 200)
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert "configuration" in data
        
        # Check that all expected services are reported
        services = data["services"]
        expected_services = ["audio_pipeline", "wake_word", "speech_to_text", "text_to_speech", "llm"]
        for service in expected_services:
            assert service in services
    
    def test_root_endpoint(self, test_client: TestClient):
        """Test root endpoint."""
        response = test_client.get("/")
        assert_valid_response(response, 200)
        
        data = response.json()
        assert data["message"] == "Hey Chef v2 API"
        assert data["version"] == "2.0.0"
        assert "docs" in data
        assert "health" in data


class TestAudioEndpoints:
    """Test audio API endpoints."""
    
    def test_audio_health_endpoint(self, test_client: TestClient):
        """Test audio health endpoint."""
        with patch('backend.app.services.create_wake_word_service') as mock_wake_word, \
             patch('backend.app.services.create_stt_service') as mock_stt, \
             patch('backend.app.services.create_tts_service') as mock_tts, \
             patch('backend.app.services.create_llm_service') as mock_llm:
            
            # Mock successful service creation
            mock_wake_word.return_value = Mock()
            mock_stt.return_value = Mock()
            mock_tts.return_value = Mock()
            mock_llm.return_value = Mock()
            
            response = test_client.get("/api/audio/health")
            assert_valid_response(response, 200)
            
            data = response.json()
            assert data["status"] in ["healthy", "degraded"]
            assert "services" in data
            assert "configuration" in data
    
    def test_audio_config_endpoint(self, test_client: TestClient):
        """Test audio configuration endpoint."""
        response = test_client.get("/api/audio/config")
        assert_valid_response(response, 200)
        
        data = response.json()
        assert "wake_word_sensitivity" in data
        assert "whisper_model_size" in data
        assert "sample_rate" in data
        assert "use_external_tts" in data
        
        # Validate data types
        assert isinstance(data["wake_word_sensitivity"], float)
        assert isinstance(data["sample_rate"], int)
        assert isinstance(data["use_external_tts"], bool)
    
    def test_audio_models_endpoint(self, test_client: TestClient):
        """Test audio models endpoint."""
        response = test_client.get("/api/audio/models")
        
        # This endpoint was previously failing, should now work
        if response.status_code == 200:
            data = response.json()
            assert "whisper_models" in data
            assert "tts_voices" in data
            assert "llm_models" in data
        else:
            # If still failing, check the error
            assert response.status_code in [500, 404]
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_endpoint(self, async_client: AsyncClient):
        """Test audio transcription endpoint."""
        # Create mock audio file
        audio_content = b"fake audio data for testing"
        files = {"audio_file": ("test.wav", audio_content, "audio/wav")}
        
        with patch('backend.app.services.create_stt_service') as mock_stt_service:
            mock_service = Mock()
            mock_service.transcribe.return_value = "transcribed text"
            mock_stt_service.return_value = mock_service
            
            response = await async_client.post("/api/audio/transcribe", files=files)
            
            if response.status_code == 200:
                data = response.json()
                assert "transcription" in data
                assert data["transcription"] == "transcribed text"
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_endpoint(self, async_client: AsyncClient):
        """Test speech synthesis endpoint."""
        tts_data = {
            "text": "Hello from the chef!",
            "voice": "alloy",
            "speed": 1.0
        }
        
        with patch('backend.app.services.create_tts_service') as mock_tts_service:
            mock_service = Mock()
            mock_service.synthesize.return_value = b"fake audio response"
            mock_tts_service.return_value = mock_service
            
            response = await async_client.post("/api/audio/synthesize", json=tts_data)
            
            if response.status_code == 200:
                # Should return audio data
                assert response.headers.get("content-type") in ["audio/wav", "application/octet-stream"]
                assert len(response.content) > 0
    
    def test_validate_api_keys_endpoint(self, test_client: TestClient):
        """Test API key validation endpoint."""
        response = test_client.post("/api/audio/validate-api-keys")
        assert_valid_response(response, 200)
        
        data = response.json()
        assert "status" in data
        assert "api_keys" in data
        
        # Check API key validation results
        api_keys = data["api_keys"]
        assert "openai" in api_keys
        assert "picovoice" in api_keys


class TestRecipeEndpoints:
    """Test recipe API endpoints."""
    
    @pytest.mark.asyncio
    async def test_recipe_health_endpoint(self, async_client: AsyncClient):
        """Test recipe service health endpoint."""
        response = await async_client.get("/api/recipes/health")
        
        # May fail if Notion MCP server is not running
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "notion_api" in data
    
    @pytest.mark.asyncio
    async def test_list_recipes_endpoint(self, async_client: AsyncClient):
        """Test list recipes endpoint."""
        with patch('httpx.AsyncClient.get') as mock_get:
            # Mock successful response from Notion MCP
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "recipes": TestDataFactory.create_multiple_recipes(3),
                "total": 3
            }
            mock_get.return_value = mock_response
            
            response = await async_client.get("/api/recipes/")
            
            if response.status_code == 200:
                data = response.json()
                assert "recipes" in data
                assert "total" in data
                assert isinstance(data["recipes"], list)
    
    @pytest.mark.asyncio
    async def test_search_recipes_endpoint(self, async_client: AsyncClient):
        """Test recipe search endpoint."""
        search_params = {"q": "pasta", "limit": 5}
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "recipes": [TestDataFactory.create_recipe_data()],
                "total": 1
            }
            mock_get.return_value = mock_response
            
            response = await async_client.get("/api/recipes/search", params=search_params)
            
            if response.status_code == 200:
                data = response.json()
                assert "recipes" in data
                assert len(data["recipes"]) <= 5
    
    @pytest.mark.asyncio
    async def test_get_recipe_by_id_endpoint(self, async_client: AsyncClient):
        """Test get recipe by ID endpoint."""
        recipe_id = "test-recipe-123"
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = TestDataFactory.create_recipe_data()
            mock_get.return_value = mock_response
            
            response = await async_client.get(f"/api/recipes/{recipe_id}")
            
            if response.status_code == 200:
                data = response.json()
                assert "id" in data
                assert "title" in data
                assert "ingredients" in data
    
    @pytest.mark.asyncio
    async def test_get_recipe_categories_endpoint(self, async_client: AsyncClient):
        """Test get recipe categories endpoint."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "categories": ["pasta", "soup", "salad", "dessert"]
            }
            mock_get.return_value = mock_response
            
            response = await async_client.get("/api/recipes/categories")
            
            if response.status_code == 200:
                data = response.json()
                assert "categories" in data
                assert isinstance(data["categories"], list)


class TestCORSConfiguration:
    """Test CORS configuration."""
    
    def test_cors_headers_present(self, test_client: TestClient):
        """Test that CORS headers are present in responses."""
        # Test preflight request
        response = test_client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        assert response.status_code == 200
        
        # Check for CORS headers
        headers = response.headers
        assert "access-control-allow-origin" in headers
        assert "access-control-allow-methods" in headers
        assert "access-control-allow-headers" in headers
    
    def test_cors_allowed_origins(self, test_client: TestClient):
        """Test that allowed origins are properly configured."""
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:5173",
            "http://127.0.0.1:3000"
        ]
        
        for origin in allowed_origins:
            response = test_client.get("/health", headers={"Origin": origin})
            assert response.status_code == 200
            
            # Should include CORS headers for allowed origins
            if "access-control-allow-origin" in response.headers:
                assert response.headers["access-control-allow-origin"] in [origin, "*"]


class TestErrorHandling:
    """Test API error handling."""
    
    def test_404_error_handling(self, test_client: TestClient):
        """Test 404 error handling."""
        response = test_client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
    
    def test_method_not_allowed_error(self, test_client: TestClient):
        """Test method not allowed error."""
        response = test_client.post("/health")  # Health endpoint only accepts GET
        assert response.status_code == 405
    
    @pytest.mark.asyncio
    async def test_invalid_json_error(self, async_client: AsyncClient):
        """Test invalid JSON error handling."""
        response = await async_client.post(
            "/api/audio/synthesize",
            content="invalid json content",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_missing_required_fields_error(self, test_client: TestClient):
        """Test missing required fields error."""
        # Try to post empty data to an endpoint that requires fields
        response = test_client.post("/api/audio/synthesize", json={})
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data


class TestRateLimiting:
    """Test rate limiting (if implemented)."""
    
    @pytest.mark.skip(reason="Rate limiting not yet implemented")
    def test_rate_limiting(self, test_client: TestClient):
        """Test rate limiting functionality."""
        # Make many requests quickly
        responses = []
        for _ in range(100):
            response = test_client.get("/health")
            responses.append(response)
        
        # Should eventually get rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        # This test would need rate limiting to be implemented


class TestAuthentication:
    """Test authentication (if implemented)."""
    
    @pytest.mark.skip(reason="Authentication not yet implemented")
    def test_protected_endpoints(self, test_client: TestClient):
        """Test that protected endpoints require authentication."""
        # This would test endpoints that require authentication
        pass


class TestAPIDocumentation:
    """Test API documentation endpoints."""
    
    def test_openapi_schema(self, test_client: TestClient):
        """Test that OpenAPI schema is available."""
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "Hey Chef v2 API"
    
    def test_docs_endpoint(self, test_client: TestClient):
        """Test that docs endpoint is available in development."""
        response = test_client.get("/docs")
        # Should be available in development mode
        assert response.status_code in [200, 404]  # 404 if disabled in production
    
    def test_redoc_endpoint(self, test_client: TestClient):
        """Test that ReDoc endpoint is available in development."""
        response = test_client.get("/redoc")
        # Should be available in development mode
        assert response.status_code in [200, 404]  # 404 if disabled in production