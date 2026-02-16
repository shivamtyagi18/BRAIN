"""Persona Mode — make the Brain respond as a historical figure.

Upload a biography or autobiography, and every agent adapts to that
person's personality, reasoning style, emotional tendencies, and voice.
"""

from brain_system import BrainWrapper

# --- 1. Create a Brain ---
brain = BrainWrapper(provider="ollama", model_name="mistral")

# --- 2. Load a persona from a document (TXT or PDF) ---
brain.load_persona("path/to/gandhi_autobiography.pdf")

print(f"🎭 Persona active: {brain.persona_name}")

# --- 3. Ask questions — the Brain responds in that person's voice ---
result = brain.think("How should we deal with injustice?")
print(f"\n🧠 {brain.persona_name} says:")
print(result.response)

# --- 4. Clear the persona when done ---
brain.clear_persona()
print(f"\nPersona active: {brain.persona_active}")  # False
