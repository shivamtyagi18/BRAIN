
from typing import Any, Dict
from .base_agent import BaseAgent

class EmotionalAgent(BaseAgent):
    def __init__(self, provider: str = "gemini", model_name: str = None):
        super().__init__(name="EmotionalAgent", role="Amygdala & Limbic System", provider=provider, model_name=model_name)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        user_input = inputs.get("input", "")
        context = inputs.get("context", "")
        
        system_prompt = f"""
        You are the Emotional Agent, acting as the Amygdala and Limbic System of a digital brain.
        Your role is to assess the input for emotional weight, sentiment, and human values.
        
        Guidelines:
        1. Determining the emotional tone (Positive, Negative, Neutral, Anxious, Excited, etc.).
        2. Identify any potential harm, offense, or ethical concerns (Safety Check).
        3. Assess the "human" impact of the decision.
        4. Do not perform logical calculations; focus on how the input *feels* and impacts well-being.
        5. Provide an 'Emotional Assessment' and an 'Empathy Score' (0-10).
        
        Context from Memory: {context}
        """
        
        response = self._query_llm(system_prompt, user_input)
        return {"emotional_analysis": response}
