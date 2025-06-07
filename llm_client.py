# llm_client.py
#
# A minimal OpenAI GPT client. Reads a system prompt from config.yaml,
# and offers both blocking `ask()` and streaming `stream()` methods.

import os
import openai
import yaml
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# 1) LOAD ENV & CONFIG
# -----------------------------------------------------------------------------
load_dotenv()  # loads OPENAI_API_KEY, etc.

if "OPENAI_API_KEY" not in os.environ or not os.environ["OPENAI_API_KEY"].strip():
    raise EnvironmentError("Please set OPENAI_API_KEY in .env")
openai.api_key = os.environ["OPENAI_API_KEY"]

# _config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
_config_path = os.path.join(os.path.dirname(__file__), "config_eng.yaml")
if not os.path.isfile(_config_path):
    raise FileNotFoundError(f"Missing config.yaml at {_config_path!r}")

with open(_config_path, "r") as cf:
    _cfg = yaml.safe_load(cf)

SYSTEM_PROMPT = _cfg.get("system_prompt", "").strip()
if not SYSTEM_PROMPT:
    raise ValueError("`system_prompt` in config.yaml is empty or missing.")


class LLMClient:
    """
    Wraps OpenAI ChatCompletion calls:
      • ask(...)    → full blocking reply
      • stream(...) → yields text deltas as they arrive
    """

    def __init__(self, model: str = "gpt-3.5-turbo", max_tokens: int = 150, temperature: float = 0.2):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def ask(self, recipe_text: str, user_question: str, history: list[dict] = None) -> str:
        """Blocking call; returns the full assistant reply."""
        messages = self._build_messages(recipe_text, user_question, history)
        resp = openai.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return resp.choices[0].message.content.strip()

    def stream(self, recipe_text: str, user_question: str, history: list[dict] = None):
        """
        Streaming call; yields each chunk of new text as it arrives.
        Usage:
            for delta in llm.stream(...):
                handle_delta(delta)
        """
        messages = self._build_messages(recipe_text, user_question, history)
        streamer = openai.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )

        for chunk in streamer:
            yield chunk.choices[0].delta.get("content") or ""

    def _build_messages(self, recipe_text, user_question, history):
        if history:
            history.append({"role": "user", "content": user_question})
            return history
        else:
            return [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Here is my recipe:\n{recipe_text}\n\nQuestion: {user_question}"
                }
            ]