#!/usr/bin/env python3
import time
import os
from src.ai.llm_client import LLMClient

def main():
    # Ensure OPENAI_API_KEY is set
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("Please set OPENAI_API_KEY in environment.")
        return
    client = LLMClient()
    sample_recipe = (
        "Ingredients: 2 eggs, salt and pepper. Steps: Beat eggs thoroughly. "
        "Cook in a non-stick pan over medium heat for 2 minutes, then flip."
    )
    question = "How long should I cook the eggs for medium doneness?"
    print("🚀 Running end-to-end ask() test…")
    t0 = time.monotonic()
    answer = client.ask(sample_recipe, question)
    t1 = time.monotonic()
    print(f"Answer: {answer}\n")
    total = t1 - t0
    print(f"⏱️ Total end-to-end time: {total:.2f}s")

if __name__ == "__main__":
    main() 