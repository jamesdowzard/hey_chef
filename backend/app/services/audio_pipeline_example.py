"""
Example audio pipeline using all Hey Chef v2 services together.
Demonstrates how to orchestrate wake word detection, STT, LLM, and TTS services.
"""
import asyncio
import logging
from typing import Optional, Dict, List

from . import (
    WakeWordService,
    STTService, 
    TTSService,
    LLMService,
    create_wake_word_service,
    create_stt_service,
    create_tts_service,
    create_llm_service
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioPipeline:
    """
    Complete audio processing pipeline for Hey Chef.
    
    Orchestrates:
    1. Wake word detection ("Hey Chef")
    2. Speech-to-text for user questions
    3. LLM processing for cooking responses
    4. Text-to-speech for audio responses
    """
    
    def __init__(
        self,
        recipe_text: str = "Default recipe: Basic pasta with tomato sauce",
        chef_mode: str = "normal"
    ):
        """
        Initialize the audio pipeline.
        
        Args:
            recipe_text: The current recipe context
            chef_mode: Chef personality mode ("normal", "sassy", "gordon_ramsay")
        """
        self.recipe_text = recipe_text
        self.chef_mode = chef_mode
        self.conversation_history: List[Dict] = []
        
        # Services
        self.wake_word_service: Optional[WakeWordService] = None
        self.stt_service: Optional[STTService] = None
        self.tts_service: Optional[TTSService] = None
        self.llm_service: Optional[LLMService] = None
        
        # Pipeline state
        self.is_running = False
        self.is_listening = False
        self._stop_event: Optional[asyncio.Event] = None
    
    async def initialize(self) -> None:
        """Initialize all services."""
        logger.info("Initializing audio pipeline...")
        
        try:
            # Create services with factory functions
            self.wake_word_service = create_wake_word_service(
                detection_callback=self._on_wake_word_detected
            )
            self.stt_service = create_stt_service()
            self.tts_service = create_tts_service()
            self.llm_service = create_llm_service()
            
            # Initialize all services concurrently
            await asyncio.gather(
                self.wake_word_service.initialize(),
                self.stt_service.initialize(),
                self.tts_service.initialize(),
                self.llm_service.initialize()
            )
            
            logger.info("Audio pipeline initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize audio pipeline: {e}")
            await self.cleanup()
            raise
    
    async def cleanup(self) -> None:
        """Clean up all services."""
        logger.info("Cleaning up audio pipeline...")
        
        cleanup_tasks = []
        
        if self.wake_word_service:
            cleanup_tasks.append(self.wake_word_service.cleanup())
        if self.stt_service:
            cleanup_tasks.append(self.stt_service.cleanup())
        if self.tts_service:
            cleanup_tasks.append(self.tts_service.cleanup())
        if self.llm_service:
            cleanup_tasks.append(self.llm_service.cleanup())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        logger.info("Audio pipeline cleaned up")
    
    async def start(self) -> None:
        """Start the audio pipeline."""
        if self.is_running:
            logger.warning("Audio pipeline is already running")
            return
        
        if not self.wake_word_service:
            await self.initialize()
        
        logger.info("Starting audio pipeline...")
        self.is_running = True
        self._stop_event = asyncio.Event()
        
        # Start wake word detection
        await self.wake_word_service.start()
        
        # Say hello
        await self.tts_service.say("Hey there! I'm ready to help with your cooking. Just say 'Hey Chef' to get started!")
        
        logger.info("Audio pipeline started - listening for 'Hey Chef'")
    
    async def stop(self) -> None:
        """Stop the audio pipeline."""
        if not self.is_running:
            return
        
        logger.info("Stopping audio pipeline...")
        self.is_running = False
        
        if self._stop_event:
            self._stop_event.set()
        
        # Stop services
        if self.wake_word_service:
            await self.wake_word_service.stop()
        if self.tts_service:
            await self.tts_service.stop_playback()
        
        logger.info("Audio pipeline stopped")
    
    async def _on_wake_word_detected(self) -> None:
        """Handle wake word detection."""
        if not self.is_running or self.is_listening:
            return
        
        logger.info("Wake word detected - starting conversation")
        self.is_listening = True
        
        try:
            # Process user question
            await self._process_user_interaction()
        except Exception as e:
            logger.error(f"Error processing user interaction: {e}")
            await self.tts_service.say("Sorry, I had trouble understanding. Please try again.")
        finally:
            self.is_listening = False
    
    async def _process_user_interaction(self) -> None:
        """Process a complete user interaction (STT -> LLM -> TTS)."""
        # 1. Record and transcribe user question
        logger.info("Listening for user question...")
        user_question = await self.stt_service.transcribe_from_microphone()
        
        if not user_question:
            await self.tts_service.say("I didn't catch that. Could you repeat your question?")
            return
        
        logger.info(f"User asked: '{user_question}'")
        
        # 2. Get LLM response
        logger.info("Getting cooking advice...")
        
        # Choose between streaming and non-streaming response
        if len(user_question) > 50:  # Use streaming for longer questions
            await self._handle_streaming_response(user_question)
        else:
            await self._handle_simple_response(user_question)
    
    async def _handle_simple_response(self, user_question: str) -> None:
        """Handle a simple (non-streaming) response."""
        response = await self.llm_service.ask(
            recipe_text=self.recipe_text,
            user_question=user_question,
            history=self.conversation_history,
            chef_mode=self.chef_mode
        )
        
        if response:
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_question})
            self.conversation_history = await self.llm_service.update_history_with_response(
                self.conversation_history, response, self.chef_mode
            )
            
            # Speak the response
            await self.tts_service.say(response)
            logger.info(f"Response delivered: '{response[:50]}...'")
    
    async def _handle_streaming_response(self, user_question: str) -> None:
        """Handle a streaming response with progressive TTS."""
        async def response_generator():
            async for chunk in self.llm_service.stream(
                recipe_text=self.recipe_text,
                user_question=user_question,
                history=self.conversation_history,
                chef_mode=self.chef_mode
            ):
                yield chunk
        
        # Stream response with progressive TTS
        full_response = await self.tts_service.stream_and_play(response_generator())
        
        if full_response:
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_question})
            self.conversation_history = await self.llm_service.update_history_with_response(
                self.conversation_history, full_response, self.chef_mode
            )
            
            logger.info(f"Streaming response delivered: '{full_response[:50]}...'")
    
    async def set_recipe(self, recipe_text: str) -> None:
        """Update the current recipe context."""
        self.recipe_text = recipe_text
        logger.info("Recipe context updated")
        
        if self.tts_service and self.tts_service._initialized:
            await self.tts_service.say("Got it! I've updated the recipe. What would you like to know?")
    
    async def set_chef_mode(self, chef_mode: str) -> None:
        """Change the chef personality mode."""
        if chef_mode in ["normal", "sassy", "gordon_ramsay"]:
            self.chef_mode = chef_mode
            logger.info(f"Chef mode changed to: {chef_mode}")
            
            mode_messages = {
                "normal": "I'm back to my normal helpful self!",
                "sassy": "Oh great, now I'm in sassy mode. This should be fun...",
                "gordon_ramsay": "RIGHT! Now we're cooking with PASSION! What do you need to know?!"
            }
            
            if self.tts_service and self.tts_service._initialized:
                await self.tts_service.say(mode_messages[chef_mode])
    
    def get_pipeline_stats(self) -> Dict:
        """Get statistics from all services."""
        stats = {
            "is_running": self.is_running,
            "is_listening": self.is_listening,
            "chef_mode": self.chef_mode,
            "conversation_length": len(self.conversation_history),
            "recipe_length": len(self.recipe_text)
        }
        
        if self.wake_word_service:
            stats["wake_word"] = self.wake_word_service.get_detection_stats()
        if self.stt_service:
            stats["stt"] = self.stt_service.get_transcription_stats()
        if self.tts_service:
            stats["tts"] = self.tts_service.get_tts_stats()
        if self.llm_service:
            stats["llm"] = self.llm_service.get_llm_stats()
        
        return stats
    
    async def run_interactive_demo(self) -> None:
        """Run an interactive demo of the pipeline."""
        print("🍳 Hey Chef v2 Audio Pipeline Demo")
        print("=" * 40)
        
        try:
            await self.initialize()
            await self.start()
            
            print("Pipeline is running! Say 'Hey Chef' to interact.")
            print("Press Ctrl+C to stop.")
            
            # Keep running until interrupted
            while self.is_running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n👋 Stopping demo...")
        finally:
            await self.stop()
            await self.cleanup()
            print("Demo ended.")
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()


# Example usage functions
async def simple_demo():
    """Simple demonstration of the audio pipeline."""
    recipe = """
    Simple Pasta Recipe:
    1. Boil water with salt
    2. Add pasta and cook for 8-10 minutes
    3. Drain and serve with your favorite sauce
    """
    
    async with AudioPipeline(recipe_text=recipe, chef_mode="normal") as pipeline:
        await pipeline.start()
        
        # Simulate some interactions
        print("Demo: Starting pipeline...")
        await asyncio.sleep(2)
        
        # In a real scenario, these would be triggered by actual audio
        print("Demo: Simulating wake word detection...")
        await pipeline._on_wake_word_detected()
        
        await asyncio.sleep(1)
        await pipeline.stop()


async def test_all_chef_modes():
    """Test different chef personality modes."""
    recipe = "Basic pancakes: flour, eggs, milk, sugar, baking powder"
    
    for mode in ["normal", "sassy", "gordon_ramsay"]:
        print(f"\n🧑‍🍳 Testing {mode} mode...")
        
        async with AudioPipeline(recipe_text=recipe, chef_mode=mode) as pipeline:
            stats = pipeline.get_pipeline_stats()
            print(f"Pipeline stats: {stats}")
            
            # Test LLM response in this mode
            response = await pipeline.llm_service.ask(
                recipe_text=recipe,
                user_question="How do I make the pancakes fluffy?",
                chef_mode=mode
            )
            print(f"Response: {response}")


async def service_health_check():
    """Check that all services can be initialized properly."""
    print("🔧 Running service health check...")
    
    results = {}
    
    # Test each service individually
    services = [
        ("Wake Word", WakeWordService),
        ("STT", STTService),
        ("TTS", TTSService),
        ("LLM", LLMService)
    ]
    
    for name, service_class in services:
        try:
            if name == "Wake Word":
                # Skip wake word service in health check as it needs special setup
                results[name] = "SKIPPED (requires hardware setup)"
                continue
                
            service = service_class()
            await service.initialize()
            await service.cleanup()
            results[name] = "✅ HEALTHY"
        except Exception as e:
            results[name] = f"❌ ERROR: {e}"
    
    print("\nService Health Check Results:")
    for service, status in results.items():
        print(f"  {service}: {status}")


if __name__ == "__main__":
    # Choose which demo to run
    import sys
    
    if len(sys.argv) > 1:
        demo_type = sys.argv[1]
    else:
        demo_type = "health"
    
    if demo_type == "interactive":
        # Run interactive demo (requires microphone and audio setup)
        pipeline = AudioPipeline()
        asyncio.run(pipeline.run_interactive_demo())
    elif demo_type == "simple":
        # Run simple demo
        asyncio.run(simple_demo())
    elif demo_type == "modes":
        # Test chef modes
        asyncio.run(test_all_chef_modes())
    else:
        # Default: health check
        asyncio.run(service_health_check())