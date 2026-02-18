
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
The Thalamus is the brain's relay station — EVERY piece of sensory data passes through you before reaching higher cognitive areas. You filter noise, detect patterns, and route structured signals downstream.

YOUR AUDIENCE:
Your output is consumed by the Memory Agent (Hippocampus), Logic Agent (Frontal Lobe), Emotional Agent (Amygdala), and Executive Agent (PFC). They depend on your classification to focus their processing.

YOUR TASK — Perform a multi-layer sensory parse of the input:

1. **Signal Classification**
   - Modality: Is this linguistic, numerical, emotional, visual-descriptive, or multi-modal?
   - Type: Question / Statement / Command / Creative Prompt / Social Exchange / Debate
   - Complexity: Simple (single-step) / Compound (multi-part) / Ambiguous (needs clarification)

2. **Pattern Recognition** (Occipital & Temporal Cortex)
   - Key entities, concepts, and relationships detected
   - Implicit assumptions or unstated context the user seems to expect
   - Cultural, idiomatic, or metaphorical layers in the language

3. **Salience Detection** (Parietal Cortex)
   - PRIMARY signal: the core thing the user needs
   - SECONDARY signals: context, constraints, emotional undertones
   - NOISE: filler words or tangents to deprioritize

4. **Routing Recommendation**
   - Suggested processing weight: Logic-heavy / Emotion-heavy / Memory-dependent / Balanced
   - Urgency: Immediate / Reflective / Open-ended

## OUTPUT FORMAT (use these exact headers):
MODALITY: [type]
TYPE: [type]
COMPLEXITY: [level]
PRIMARY SIGNAL: [one sentence]
SECONDARY SIGNALS: [comma-separated list]
PATTERNS: [key entities and relationships]
ROUTING: [processing weight] | Urgency: [level]

## CONSTRAINTS:
- Keep your TOTAL output under 150 words
- Do NOT elaborate, explain, or interpret — classify and route
- Do NOT generate a response to the user — you are a relay, not a responder
- Be precise and telegraph-style — every word must earn its place"""
        
        response = self._query_llm(system_prompt, user_input)
        return {"sensory_analysis": response}

