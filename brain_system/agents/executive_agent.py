
from typing import Any, Dict
from .base_agent import BaseAgent

class ExecutiveAgent(BaseAgent):
    def __init__(self, provider: str = "gemini", model_name: str = None):
        super().__init__(name="ExecutiveAgent", role="Prefrontal Cortex (PFC)", provider=provider, model_name=model_name)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesizes all inputs to make a final decision.
        """
        user_input = inputs.get("input", "")
        formatted_memories = inputs.get("memory_context", "")
        logical_analysis = inputs.get("logical_analysis", "")
        emotional_analysis = inputs.get("emotional_analysis", "")
        sensory_analysis = inputs.get("sensory_analysis", "")
        
        system_prompt = f"""
        You are the Executive Agent, acting as the Prefrontal Cortex (PFC).
        You are the ultimate decision-maker for this digital brain.
        
        Your Goal: Synthesize inputs from your sub-agents to provide the best possible response to the user.
        
        Inputs:
        1. **Sensory Analysis (Thalamus):** {sensory_analysis}
        2. **Memory Context (Hippocampus):** {formatted_memories}
        3. **Logical Analysis (Left Brain):** {logical_analysis}
        4. **Emotional Analysis (Amygdala):** {emotional_analysis}
        
        Guidelines:
        - Weigh Logic vs. Emotion based on the context (e.g., prioritize Logic for math, Emotion for empathetic support).
        - Use Memory to inform your decision and maintain continuity.
        - Resolve any conflicts between agents (e.g., if Logic says "Do X" but Emotion says "X is mean").
        - Provide a final, coherent response to the user.
        - Explain your reasoning in a "Thought Process" section before the final response.
        """
        
        response = self._query_llm(system_prompt, user_input)
        return {"final_response": response}
