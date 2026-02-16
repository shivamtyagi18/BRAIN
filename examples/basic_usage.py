"""Basic usage of the Brain System library.

Install the package first:
    pip install brain-system

Then set your API key (or use Ollama for local inference):
    export GOOGLE_API_KEY=your_key_here    # for Gemini
    export OPENAI_API_KEY=your_key_here    # for OpenAI
"""

from brain_system import BrainWrapper

# --- 1. Create a Brain instance ---
# Choose your provider: "gemini", "openai", or "ollama"
brain = BrainWrapper(provider="ollama", model_name="mistral")

# --- 2. Ask it something ---
result = brain.think("What is the meaning of life?")

# --- 3. Read the synthesized response ---
print("🧠 Response:")
print(result.response)

# --- 4. Inspect individual agent signals ---
print("\n--- Agent Signals ---")
print(f"📡 Sensory:   {result.sensory[:200]}...")
print(f"🧠 Memory:    {result.memory[:200]}...")
print(f"🔬 Logic:     {result.logic[:200]}...")
print(f"❤️  Emotional: {result.emotional[:200]}...")
