"""
Async LLM service for interacting with OpenAI's chat completion API.
Converted from the original synchronous implementation to async-compatible service.
"""
import asyncio
from typing import AsyncGenerator, List, Dict, Optional

from .base import BaseService
from ..core.config import settings
from ..config.prompts import get_system_prompt


class LLMService(BaseService):
    """
    Async OpenAI ChatCompletion service with support for different chef modes and streaming.
    
    Features:
    - Async/await compatible
    - Multiple chef personalities (normal, sassy, gordon_ramsay)
    - Streaming responses
    - Conversation history management
    - Configurable parameters per mode
    - Error handling with mode-appropriate messages
    """
    
    def __init__(self):
        """Initialize LLM service."""
        super().__init__("llm")
        
        # OpenAI client (lazy initialization)
        self.openai_client = None
        
        # Chef mode configurations
        self.mode_configs = {
            "normal": {
                "max_tokens": settings.llm.max_tokens,
                "temperature": settings.llm.temperature
            },
            "sassy": {
                "max_tokens": settings.llm.sassy_max_tokens,
                "temperature": settings.llm.sassy_temperature
            },
            "gordon_ramsay": {
                "max_tokens": settings.llm.gordon_max_tokens,
                "temperature": settings.llm.gordon_temperature
            }
        }
        
        # System prompts are now imported from prompts module
    
    async def _initialize_impl(self) -> None:
        """Initialize OpenAI client."""
        try:
            # Import and initialize OpenAI client in thread pool
            loop = asyncio.get_event_loop()
            
            def create_client():
                import openai
                api_key = settings.openai_api_key
                if not api_key:
                    raise EnvironmentError("OPENAI_API_KEY not set in environment")
                return openai.OpenAI(api_key=api_key)
            
            self.openai_client = await loop.run_in_executor(None, create_client)
            self._store_resource("openai_client", self.openai_client)
            
            self.logger.info(f"LLM service initialized with model: {settings.llm.model}")
            
        except ImportError:
            raise RuntimeError("OpenAI package not installed. Install with: pip install openai")
    
    async def _cleanup_impl(self) -> None:
        """Clean up LLM resources."""
        # OpenAI client doesn't need explicit cleanup
        pass
    
    
    async def ask(
        self,
        recipe_text: str,
        user_question: str,
        history: Optional[List[Dict]] = None,
        chef_mode: str = "normal"
    ) -> str:
        """
        Get a complete response from the LLM.
        
        Args:
            recipe_text: The recipe context
            user_question: User's question
            history: Conversation history (if maintaining context)
            chef_mode: Chef personality mode - "normal", "sassy", or "gordon_ramsay"
            
        Returns:
            Complete assistant response
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.managed_operation("ask"):
            messages = self._build_messages(recipe_text, user_question, history, chef_mode)
            max_tokens, temperature = self._get_mode_parameters(chef_mode)
            
            try:
                # Run the API call in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                
                def make_request():
                    return self.openai_client.chat.completions.create(
                        model=settings.llm.model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                
                response = await loop.run_in_executor(None, make_request)
                result = response.choices[0].message.content.strip()
                
                self.logger.info(f"LLM response generated: {len(result)} chars in {chef_mode} mode")
                return result
                
            except Exception as e:
                self.logger.error(f"LLM request failed: {e}")
                return self._get_error_message(chef_mode)
    
    async def stream(
        self,
        recipe_text: str,
        user_question: str,
        history: Optional[List[Dict]] = None,
        chef_mode: str = "normal"
    ) -> AsyncGenerator[str, None]:
        """
        Stream response chunks from the LLM.
        
        Args:
            recipe_text: The recipe context  
            user_question: User's question
            history: Conversation history (if maintaining context)
            chef_mode: Chef personality mode - "normal", "sassy", or "gordon_ramsay"
            
        Yields:
            Text chunks as they arrive
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.managed_operation("stream"):
            messages = self._build_messages(recipe_text, user_question, history, chef_mode)
            max_tokens, temperature = self._get_mode_parameters(chef_mode)
            
            try:
                # Create streaming request
                loop = asyncio.get_event_loop()
                
                def create_stream():
                    return self.openai_client.chat.completions.create(
                        model=settings.llm.model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stream=True
                    )
                
                stream = await loop.run_in_executor(None, create_stream)
                
                self.logger.info(f"LLM streaming started in {chef_mode} mode")
                
                # Process stream in thread pool and yield chunks
                def get_next_chunk(stream_iter):
                    try:
                        return next(stream_iter)
                    except StopIteration:
                        return None
                
                stream_iter = iter(stream)
                
                while True:
                    chunk = await loop.run_in_executor(None, get_next_chunk, stream_iter)
                    if chunk is None:
                        break
                    
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
                
                self.logger.info("LLM streaming completed")
                
            except Exception as e:
                self.logger.error(f"LLM streaming failed: {e}")
                yield self._get_error_message(chef_mode)
    
    def _get_mode_parameters(self, chef_mode: str) -> tuple[int, float]:
        """Get max_tokens and temperature for the specified chef mode."""
        config = self.mode_configs.get(chef_mode, self.mode_configs["normal"])
        return config["max_tokens"], config["temperature"]
    
    def _get_error_message(self, chef_mode: str) -> str:
        """Get an appropriate error message for the chef mode."""
        if chef_mode == "sassy":
            return "Great, now I'm broken too. Try again, genius."
        elif chef_mode == "gordon_ramsay":
            return "BLOODY HELL! The system's gone down! Come back when the tech's been sorted!"
        else:
            return "Sorry, I'm having trouble right now. Please try again."
    
    def _build_messages(
        self,
        recipe_text: str,
        user_question: str,
        history: Optional[List[Dict]] = None,
        chef_mode: str = "normal"
    ) -> List[Dict]:
        """
        Build the message array for the API call.
        
        Args:
            recipe_text: The recipe context
            user_question: User's question
            history: Conversation history
            chef_mode: Chef personality mode
            
        Returns:
            List of message dictionaries
        """
        # Get appropriate system prompt
        system_prompt = get_system_prompt(chef_mode)
        
        if history:
            # Using conversation history - append new user message
            messages = history.copy()
            messages.append({"role": "user", "content": user_question})
            
            # Update system prompt if it's different (mode changed)
            if messages[0]["role"] == "system":
                messages[0]["content"] = system_prompt
            else:
                # Insert system prompt at beginning
                messages.insert(0, {"role": "system", "content": system_prompt})
        else:
            # No history - create fresh conversation
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Here is my recipe:\n{recipe_text}\n\nQuestion: {user_question}"
                }
            ]
        
        return messages
    
    async def update_history_with_response(
        self,
        history: List[Dict],
        response: str,
        chef_mode: str = "normal"
    ) -> List[Dict]:
        """
        Add assistant response to conversation history.
        
        Args:
            history: Current conversation history
            response: Assistant's response to add
            chef_mode: Chef personality mode
            
        Returns:
            Updated history
        """
        if history:
            history.append({"role": "assistant", "content": response})
            
            # Ensure system prompt matches current mode
            system_prompt = get_system_prompt(chef_mode)
            if history[0]["role"] == "system":
                history[0]["content"] = system_prompt
        
        return history
    
    async def get_available_models(self) -> List[str]:
        """
        Get list of available OpenAI models.
        
        Returns:
            List of available model names
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            loop = asyncio.get_event_loop()
            
            def list_models():
                models = self.openai_client.models.list()
                return [model.id for model in models.data if "gpt" in model.id]
            
            available_models = await loop.run_in_executor(None, list_models)
            return sorted(available_models)
            
        except Exception as e:
            self.logger.error(f"Failed to get available models: {e}")
            return settings.llm.available_models
    
    def get_chef_modes(self) -> List[str]:
        """
        Get list of available chef modes.
        
        Returns:
            List of chef mode names
        """
        return list(self.mode_configs.keys())
    
    def get_llm_stats(self) -> dict:
        """
        Get LLM service statistics.
        
        Returns:
            Dictionary with LLM stats
        """
        return {
            "model": settings.llm.model,
            "available_modes": list(self.mode_configs.keys()),
            "mode_configs": self.mode_configs,
            "is_initialized": self._initialized
        }
    
    # Legacy methods for backward compatibility
    async def ask_legacy(
        self,
        recipe_text: str,
        user_question: str,
        history: Optional[List[Dict]] = None,
        sassy_mode: bool = False
    ) -> str:
        """Legacy method for backward compatibility."""
        chef_mode = "sassy" if sassy_mode else "normal"
        return await self.ask(recipe_text, user_question, history, chef_mode)
    
    async def stream_legacy(
        self,
        recipe_text: str,
        user_question: str,
        history: Optional[List[Dict]] = None,
        sassy_mode: bool = False
    ) -> AsyncGenerator[str, None]:
        """Legacy method for backward compatibility."""
        chef_mode = "sassy" if sassy_mode else "normal"
        async for chunk in self.stream(recipe_text, user_question, history, chef_mode):
            yield chunk