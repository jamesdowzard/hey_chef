# llm_client.py
#
# A minimal OpenAI GPT-4o client. Reads a system prompt from config.yaml,
# and now optionally supports passing in a conversation history _without_ repeating the recipe.

import os
import openai
import yaml
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# 1) LOAD ENV & CONFIG
# -----------------------------------------------------------------------------
load_dotenv()  # loads OPENAI_API_KEY, USE_EXTERNAL_TTS, etc.

if "OPENAI_API_KEY" not in os.environ or not os.environ["OPENAI_API_KEY"].strip():
    raise EnvironmentError("Please set the OPENAI_API_KEY environment variable (in .env).")
openai.api_key = os.environ["OPENAI_API_KEY"]

_config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
if not os.path.isfile(_config_path):
    raise FileNotFoundError(f"Missing config.yaml at {_config_path!r}")

with open(_config_path, "r") as cf:
    _cfg = yaml.safe_load(cf)

SYSTEM_PROMPT = _cfg.get("system_prompt", "").strip()
if not SYSTEM_PROMPT:
    raise ValueError("`system_prompt` in config.yaml is empty or missing.")


class LLMClient:
    """
    Wraps calls to OpenAI’s ChatCompletion for GPT-4o, with optional history support.
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        """
        model: which OpenAI model to use (e.g. "gpt-4o", "gpt-4o-mini", etc.)
        """
        self.model = model

    def ask(self,
            recipe_text: str,
            user_question: str,
            history: list[dict] = None
    ) -> str:
        """
        Sends a combined prompt to the LLM.  
        If `history` is None, we build:
            [ {role: "system", content: SYSTEM_PROMPT},
              {role: "user",   content: "Here is my recipe:\n{recipe_text}\n\nQuestion: {user_question}"} ]

        If `history` is NOT None, we assume history already contains:
           [ {role:"system", content:SYSTEM_PROMPT},
             {role:"user", content:"Here is my recipe:\n{original_recipe}"} ,
             {role:"assistant", content:"(previous reply)"} , … ]
        and only append:
           {role:"user", content: "{user_question}"}
        so the recipe isn’t resent each time.

        The caller (e.g. `start_voice_loop`) must do:
            history.append({"role":"assistant","content": reply})
        after receiving `reply`.

        Returns the assistant’s text response.
        """
        if history:
            # We already seeded history once (with system + recipe),
            # so now just append the new question (no recipe).
            history.append({"role": "user", "content": user_question})
            messages = history
        else:
            # No history means “stateless” mode → include both recipe and question
            system_msg = {"role": "system", "content": SYSTEM_PROMPT}
            user_msg = {
                "role": "user",
                "content": f"Here is my recipe:\n{recipe_text}\n\nQuestion: {user_question}"
            }
            messages = [system_msg, user_msg]

        response = openai.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=500
        )
        reply = response.choices[0].message.content.strip()
        return reply