"""
LLM client for interacting with OpenAI's chat completion API.
Supports both normal and sassy modes with different prompts and parameters.
"""
import os
import openai
from typing import Iterator, List, Dict, Optional
from dotenv import load_dotenv

from ..config import get_system_prompt

load_dotenv()


class LLMClient:
    """
    OpenAI ChatCompletion client with support for different modes and streaming.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        max_tokens: int = 150,
        temperature: float = 0.2,
        sassy_max_tokens: int = 100,
        sassy_temperature: float = 0.7
    ):
        """
        Initialize LLM client.
        
        Args:
            model: OpenAI model to use
            max_tokens: Maximum tokens for normal mode
            temperature: Temperature for normal mode
            sassy_max_tokens: Maximum tokens for sassy mode
            sassy_temperature: Temperature for sassy mode (higher for more creativity)
        """
        # Validate API key
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise EnvironmentError("Please set OPENAI_API_KEY in environment")
        
        openai.api_key = api_key
        
        # Model parameters
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.sassy_max_tokens = sassy_max_tokens
        self.sassy_temperature = sassy_temperature

    def ask(
        self,
        recipe_text: str,
        user_question: str,
        history: Optional[List[Dict]] = None,
        sassy_mode: bool = False
    ) -> str:
        """
        Get a complete response from the LLM.
        
        Args:
            recipe_text: The recipe context
            user_question: User's question
            history: Conversation history (if maintaining context)
            sassy_mode: Whether to use sassy mode
            
        Returns:
            Complete assistant response
        """
        messages = self._build_messages(recipe_text, user_question, history, sassy_mode)
        
        # Choose parameters based on mode
        max_tokens = self.sassy_max_tokens if sassy_mode else self.max_tokens
        temperature = self.sassy_temperature if sassy_mode else self.temperature
        
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ LLM request failed: {e}")
            error_msg = "Sorry, I'm having trouble right now."
            if sassy_mode:
                error_msg = "Great, now I'm broken too. Try again, genius."
            return error_msg

    def stream(
        self,
        recipe_text: str,
        user_question: str,
        history: Optional[List[Dict]] = None,
        sassy_mode: bool = False
    ) -> Iterator[str]:
        """
        Stream response chunks from the LLM.
        
        Args:
            recipe_text: The recipe context
            user_question: User's question
            history: Conversation history (if maintaining context)
            sassy_mode: Whether to use sassy mode
            
        Yields:
            Text chunks as they arrive
        """
        messages = self._build_messages(recipe_text, user_question, history, sassy_mode)
        
        # Choose parameters based on mode
        max_tokens = self.sassy_max_tokens if sassy_mode else self.max_tokens
        temperature = self.sassy_temperature if sassy_mode else self.temperature
        
        try:
            stream = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
                    
        except Exception as e:
            print(f"⚠️ LLM streaming failed: {e}")
            error_msg = "Sorry, I'm having trouble right now."
            if sassy_mode:
                error_msg = "Great, now I'm broken too. Try again, genius."
            yield error_msg

    def _build_messages(
        self,
        recipe_text: str,
        user_question: str,
        history: Optional[List[Dict]] = None,
        sassy_mode: bool = False
    ) -> List[Dict]:
        """
        Build the message array for the API call.
        
        Args:
            recipe_text: The recipe context
            user_question: User's question
            history: Conversation history
            sassy_mode: Whether to use sassy mode
            
        Returns:
            List of message dictionaries
        """
        # Get appropriate system prompt
        system_prompt = get_system_prompt(sassy_mode=sassy_mode)
        
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

    def update_history_with_response(
        self, 
        history: List[Dict], 
        response: str,
        sassy_mode: bool = False
    ) -> List[Dict]:
        """
        Add assistant response to conversation history.
        
        Args:
            history: Current conversation history
            response: Assistant's response to add
            sassy_mode: Whether sassy mode was used
            
        Returns:
            Updated history
        """
        if history:
            history.append({"role": "assistant", "content": response})
            
            # Ensure system prompt matches current mode
            system_prompt = get_system_prompt(sassy_mode=sassy_mode)
            if history[0]["role"] == "system":
                history[0]["content"] = system_prompt
        
        return history 