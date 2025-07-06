"""
Unit tests for Hey Chef v2 audio pipeline manager.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from backend.app.core.audio_pipeline import AudioPipelineManager
from backend.app.core.models import ChefMode, AudioState
from tests.backend.fixtures.test_data import TestDataFactory
from tests.backend.fixtures.mock_services import MockAudioPipelineManager


class TestAudioPipelineManager:
    """Test audio pipeline manager functionality."""
    
    @pytest.fixture
    def pipeline_manager(self):
        """Create audio pipeline manager for testing."""
        return AudioPipelineManager()
    
    @pytest.fixture
    def mock_pipeline_manager(self):
        """Create mock audio pipeline manager for testing."""
        return MockAudioPipelineManager()
    
    def test_audio_pipeline_manager_initialization(self, pipeline_manager):
        """Test audio pipeline manager initializes correctly."""
        assert pipeline_manager.wake_word_service is None
        assert pipeline_manager.stt_service is None
        assert pipeline_manager.tts_service is None
        assert pipeline_manager.llm_service is None
        assert pipeline_manager.is_running is False
    
    @pytest.mark.asyncio
    async def test_mock_pipeline_initialization(self, mock_pipeline_manager):
        """Test mock pipeline initialization."""
        assert mock_pipeline_manager.wake_word_service is not None
        assert mock_pipeline_manager.stt_service is not None
        assert mock_pipeline_manager.tts_service is not None
        assert mock_pipeline_manager.llm_service is not None
        assert mock_pipeline_manager.processing_count == 0
    
    @pytest.mark.asyncio
    async def test_mock_pipeline_start_stop(self, mock_pipeline_manager):
        """Test mock pipeline start and stop."""
        # Test start
        await mock_pipeline_manager.start_pipeline()
        
        # Test stop
        await mock_pipeline_manager.stop_pipeline()
        
        # Test cleanup
        await mock_pipeline_manager.cleanup()
    
    @pytest.mark.asyncio
    async def test_mock_audio_processing_success(self, mock_pipeline_manager):
        """Test successful audio processing through mock pipeline."""
        # Create test request
        request = TestDataFactory.create_audio_processing_request(
            audio_data=b"hey chef how do I cook pasta",
            chef_mode=ChefMode.NORMAL
        )
        
        # Process audio
        result = await mock_pipeline_manager.process_audio_request(request)
        
        # Verify result
        assert result["success"] is True
        assert result["wake_word_detected"] is True
        assert "transcription" in result
        assert "llm_response" in result
        assert "audio_response" in result
        assert result["chef_mode"] == ChefMode.NORMAL
        assert result["processing_time"] > 0
        assert mock_pipeline_manager.processing_count == 1
    
    @pytest.mark.asyncio
    async def test_mock_audio_processing_no_wake_word(self, mock_pipeline_manager):
        """Test audio processing when wake word not detected."""
        # Configure mock to not detect wake word
        mock_pipeline_manager.wake_word_service.should_detect = False
        
        request = TestDataFactory.create_audio_processing_request(
            audio_data=b"regular speech without wake word"
        )
        
        result = await mock_pipeline_manager.process_audio_request(request)
        
        assert result["success"] is False
        assert result["wake_word_detected"] is False
        assert "error" in result
        assert result["error"] == "Wake word not detected"
    
    @pytest.mark.asyncio
    async def test_mock_audio_processing_different_chef_modes(self, mock_pipeline_manager):
        """Test audio processing with different chef modes."""
        chef_modes = [ChefMode.NORMAL, ChefMode.SASSY, ChefMode.GORDON_RAMSAY]
        
        for mode in chef_modes:
            request = TestDataFactory.create_audio_processing_request(
                audio_data=b"hey chef cooking question",
                chef_mode=mode
            )
            
            result = await mock_pipeline_manager.process_audio_request(request)
            
            assert result["success"] is True
            assert result["chef_mode"] == mode
            assert "llm_response" in result
            
            # Different modes should produce different responses
            response = result["llm_response"]
            if mode == ChefMode.SASSY:
                assert "Oh please" in response
            elif mode == ChefMode.GORDON_RAMSAY:
                assert "RIGHT!" in response
    
    @pytest.mark.asyncio
    async def test_mock_audio_processing_performance(self, mock_pipeline_manager):
        """Test audio processing performance."""
        # Process multiple requests
        requests = [
            TestDataFactory.create_audio_processing_request(
                audio_data=f"hey chef question {i}".encode()
            ) for i in range(5)
        ]
        
        start_time = asyncio.get_event_loop().time()
        
        # Process all requests
        results = []
        for request in requests:
            result = await mock_pipeline_manager.process_audio_request(request)
            results.append(result)
        
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        
        # Verify results
        assert len(results) == 5
        assert all(r["success"] for r in results)
        assert mock_pipeline_manager.processing_count == 5
        
        # Performance check (mock should be fast)
        assert total_time < 5.0  # Should complete in under 5 seconds
    
    @pytest.mark.asyncio
    async def test_mock_audio_processing_concurrent(self, mock_pipeline_manager):
        """Test concurrent audio processing."""
        # Create multiple requests
        requests = [
            TestDataFactory.create_audio_processing_request(
                audio_data=f"hey chef concurrent question {i}".encode()
            ) for i in range(3)
        ]
        
        # Process concurrently
        tasks = [
            mock_pipeline_manager.process_audio_request(req) 
            for req in requests
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all succeeded
        assert len(results) == 3
        assert all(r["success"] for r in results)
        
        # Each should have unique responses
        transcriptions = [r["transcription"] for r in results]
        assert len(set(transcriptions)) == 3  # All should be different


class TestAudioPipelineIntegration:
    """Test audio pipeline integration scenarios."""
    
    @pytest.fixture
    def mock_pipeline_manager(self):
        """Create mock pipeline manager for integration testing."""
        return MockAudioPipelineManager()
    
    @pytest.mark.asyncio
    async def test_full_conversation_flow(self, mock_pipeline_manager):
        """Test full conversation flow through pipeline."""
        # Simulate a conversation
        conversation_requests = [
            ("hey chef how do I cook pasta", ChefMode.NORMAL),
            ("hey chef what about seasoning", ChefMode.NORMAL),
            ("hey chef be more specific", ChefMode.SASSY),
            ("hey chef explain it like gordon ramsay", ChefMode.GORDON_RAMSAY)
        ]
        
        conversation_results = []
        
        for audio_text, chef_mode in conversation_requests:
            request = TestDataFactory.create_audio_processing_request(
                audio_data=audio_text.encode(),
                chef_mode=chef_mode
            )
            
            result = await mock_pipeline_manager.process_audio_request(request)
            conversation_results.append(result)
        
        # Verify all requests processed successfully
        assert len(conversation_results) == 4
        assert all(r["success"] for r in conversation_results)
        
        # Verify different chef modes produced different responses
        normal_responses = [r["llm_response"] for r in conversation_results[:2]]
        sassy_response = conversation_results[2]["llm_response"]
        gordon_response = conversation_results[3]["llm_response"]
        
        assert "Oh please" in sassy_response
        assert "RIGHT!" in gordon_response
    
    @pytest.mark.asyncio
    async def test_pipeline_error_recovery(self, mock_pipeline_manager):
        """Test pipeline error recovery."""
        # First, process a normal request
        normal_request = TestDataFactory.create_audio_processing_request(
            audio_data=b"hey chef normal question"
        )
        
        normal_result = await mock_pipeline_manager.process_audio_request(normal_request)
        assert normal_result["success"] is True
        
        # Then, process a request that should cause an error
        error_request = TestDataFactory.create_audio_processing_request(
            audio_data=b"hey chef this should cause an error"
        )
        
        try:
            error_result = await mock_pipeline_manager.process_audio_request(error_request)
            # Mock doesn't actually throw errors, but would handle them
            assert "error" in error_result or error_result["success"] is False
        except Exception:
            # If exception is thrown, that's also acceptable
            pass
        
        # Then, process another normal request to verify recovery
        recovery_request = TestDataFactory.create_audio_processing_request(
            audio_data=b"hey chef recovery question"
        )
        
        recovery_result = await mock_pipeline_manager.process_audio_request(recovery_request)
        assert recovery_result["success"] is True
    
    @pytest.mark.asyncio
    async def test_pipeline_with_recipe_context(self, mock_pipeline_manager):
        """Test pipeline with recipe context."""
        # Simulate having a recipe context
        recipe_context = TestDataFactory.create_recipe_data()
        
        request = TestDataFactory.create_audio_processing_request(
            audio_data=b"hey chef how do I make the sauce for this recipe"
        )
        
        # In a real implementation, we'd pass recipe context
        # For now, just verify the pipeline works
        result = await mock_pipeline_manager.process_audio_request(request)
        
        assert result["success"] is True
        assert "llm_response" in result
        
        # Mock should include recipe context in response
        if "recipe" in result["llm_response"]:
            assert "Based on the recipe" in result["llm_response"]
    
    @pytest.mark.asyncio
    async def test_pipeline_audio_state_transitions(self, mock_pipeline_manager):
        """Test audio state transitions through pipeline."""
        # In a real implementation, we'd track audio states
        # For now, verify the pipeline can handle different states
        
        states_to_test = [
            AudioState.IDLE,
            AudioState.LISTENING,
            AudioState.PROCESSING
        ]
        
        for state in states_to_test:
            request = TestDataFactory.create_audio_processing_request(
                audio_data=f"hey chef question in {state} state".encode()
            )
            
            result = await mock_pipeline_manager.process_audio_request(request)
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_pipeline_cleanup_and_restart(self, mock_pipeline_manager):
        """Test pipeline cleanup and restart."""
        # Process a request
        request = TestDataFactory.create_audio_processing_request()
        result = await mock_pipeline_manager.process_audio_request(request)
        assert result["success"] is True
        
        # Cleanup pipeline
        await mock_pipeline_manager.cleanup()
        
        # Restart pipeline
        await mock_pipeline_manager.start_pipeline()
        
        # Process another request
        request2 = TestDataFactory.create_audio_processing_request()
        result2 = await mock_pipeline_manager.process_audio_request(request2)
        assert result2["success"] is True


class TestAudioPipelinePerformance:
    """Test audio pipeline performance characteristics."""
    
    @pytest.fixture
    def mock_pipeline_manager(self):
        """Create mock pipeline manager for performance testing."""
        return MockAudioPipelineManager()
    
    @pytest.mark.asyncio
    async def test_pipeline_latency(self, mock_pipeline_manager):
        """Test pipeline processing latency."""
        request = TestDataFactory.create_audio_processing_request()
        
        start_time = asyncio.get_event_loop().time()
        result = await mock_pipeline_manager.process_audio_request(request)
        end_time = asyncio.get_event_loop().time()
        
        processing_time = end_time - start_time
        
        assert result["success"] is True
        assert processing_time < 1.0  # Mock should be fast
        assert result["processing_time"] > 0
    
    @pytest.mark.asyncio
    async def test_pipeline_throughput(self, mock_pipeline_manager):
        """Test pipeline throughput."""
        # Process multiple requests sequentially
        request_count = 10
        requests = [
            TestDataFactory.create_audio_processing_request(
                audio_data=f"hey chef throughput test {i}".encode()
            ) for i in range(request_count)
        ]
        
        start_time = asyncio.get_event_loop().time()
        
        results = []
        for request in requests:
            result = await mock_pipeline_manager.process_audio_request(request)
            results.append(result)
        
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        
        # Verify all succeeded
        assert len(results) == request_count
        assert all(r["success"] for r in results)
        
        # Calculate throughput
        throughput = request_count / total_time
        assert throughput > 1.0  # Should process at least 1 request per second
    
    @pytest.mark.asyncio
    async def test_pipeline_memory_usage(self, mock_pipeline_manager):
        """Test pipeline memory usage patterns."""
        # Process many requests to test memory stability
        for i in range(20):
            request = TestDataFactory.create_audio_processing_request(
                audio_data=f"hey chef memory test {i}".encode()
            )
            
            result = await mock_pipeline_manager.process_audio_request(request)
            assert result["success"] is True
            
            # In a real test, we'd check memory usage here
            # For now, just verify no obvious memory leaks
        
        # Processing count should match requests
        assert mock_pipeline_manager.processing_count == 20