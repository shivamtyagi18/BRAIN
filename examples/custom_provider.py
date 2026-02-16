"""Switching between LLM providers.

Brain System supports three providers out of the box.
Just pass the provider name when creating a BrainWrapper.
"""

import os
from brain_system import BrainWrapper

question = "Explain the trolley problem in one paragraph."

# --- Option 1: Ollama (local, no API key needed) ---
brain_local = BrainWrapper(provider="ollama", model_name="mistral")
print("🏠 Ollama (local):")
print(brain_local.think(question).response)

# --- Option 2: Google Gemini (requires GOOGLE_API_KEY) ---
if os.getenv("GOOGLE_API_KEY"):
    brain_gemini = BrainWrapper(provider="gemini")
    print("\n🔵 Gemini:")
    print(brain_gemini.think(question).response)

# --- Option 3: OpenAI (requires OPENAI_API_KEY) ---
if os.getenv("OPENAI_API_KEY"):
    brain_openai = BrainWrapper(provider="openai", model_name="gpt-4o")
    print("\n🟢 OpenAI:")
    print(brain_openai.think(question).response)
