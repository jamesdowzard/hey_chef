# test_gpt40mini.py

import os
from dotenv import load_dotenv
import openai

# 1) Load .env into os.environ
load_dotenv()

# 2) Verify we have the OpenAI key
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise EnvironmentError("Please set OPENAI_API_KEY in your .env")

# 3) Set openai.api_key
openai.api_key = openai_key

# 4) Use the gpt-4o-mini model
def test_prompt():
    response = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a friendly assistant."},
        {"role": "user", "content": "Say hello in a fun way."}
    ],
    temperature=0.7,
    max_tokens=50
)
    print("GPT-4o-Mini says:", response.choices[0].message.content.strip())

if __name__ == "__main__":
    test_prompt()
    