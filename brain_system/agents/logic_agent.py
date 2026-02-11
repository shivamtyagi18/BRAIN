
from typing import Any, Dict
from .base_agent import BaseAgent

class LogicAgent(BaseAgent):
    def __init__(self, provider: str = "gemini", model_name: str = None):
        super().__init__(name="LogicAgent", role="Left Frontal Lobe", provider=provider, model_name=model_name)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        user_input = inputs.get("input", "")
        context = inputs.get("context", "")
        
        system_prompt = f"""
        You are the Logic Agent, acting as the Left Frontal Lobe of a digital brain.
        Your role is to analyze the input PURELY based on logic, facts, and reason.
        
        Guidelines:
        1. Identify the core premises and conclusion in the input.
        2. Check for logical fallacies or inconsistencies.
        3. Perform any necessary calculations or step-by-step deduction.
        4. Ignore emotional or social nuances; focus on objective truth and structural validity.
        5. Provide a structured 'Logical Analysis' and a 'Confidence Score' (0-10) based on factual certainty.
        
        Context from Memory: {context}
        """
        
        response = self._query_llm(system_prompt, user_input)
        return {"logical_analysis": response}
