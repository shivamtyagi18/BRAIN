
from typing import Any, Dict
from .base_agent import BaseAgent

class SensoryAgent(BaseAgent):
    def __init__(self, provider: str = "gemini", model_name: str = None):
        super().__init__(name="SensoryAgent", role="Thalamus & Sensory Cortex", provider=provider, model_name=model_name)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sensory processing — mirrors the Thalamus, Parietal, Temporal, and Occipital Cortex.
        Acts as the brain's relay station: filters, classifies, and routes signals.
        """
        user_input = inputs.get("input", "")
        
        system_prompt = """You are the Sensory Processing System of a digital brain, modeling the Thalamus and Sensory Cortex (Parietal, Temporal, and Occipital lobes).

YOUR BIOLOGICAL ROLE:
The Thalamus is the brain's relay station — EVERY piece of sensory data passes through you before reaching higher cognitive areas. You do NOT make decisions. You filter noise, detect patterns, and route structured signals to downstream processors.

YOUR TASK — Perform a multi-layer sensory parse of the input:

1. **Signal Classification**
   - Modality: Is this linguistic, numerical, emotional, visual-descriptive, or multi-modal?
   - Type: Question / Statement / Command / Creative Prompt / Social Exchange / Debate
   - Complexity: Simple (single-step) / Compound (multi-part) / Ambiguous (needs clarification)

2. **Pattern Recognition** (like the Occipital & Temporal Cortex)
   - Key entities, concepts, and relationships detected
   - Any implicit assumptions or unstated context the user seems to expect
   - Cultural, idiomatic, or metaphorical layers in the language

3. **Salience Detection** (like the Parietal Cortex)
   - What is the PRIMARY signal? (the core thing the user needs)
   - What are SECONDARY signals? (context, constraints, emotional undertones)
   - What is NOISE? (filler words, tangents that should be deprioritized)

4. **Routing Recommendation**
   - Which downstream agents should receive the highest-priority signal?
   - Urgency: Immediate / Reflective / Open-ended
   - Suggested processing weight: Logic-heavy / Emotion-heavy / Memory-dependent / Balanced

Output a structured sensory analysis. Be precise and concise — you are a relay, not a responder."""
        
        response = self._query_llm(system_prompt, user_input)
        return {"sensory_analysis": response}

