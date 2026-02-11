
from typing import Any, Dict
from .base_agent import BaseAgent

class SensoryAgent(BaseAgent):
    def __init__(self, provider: str = "gemini", model_name: str = None):
        super().__init__(name="SensoryAgent", role="Thalamus & Sensory Cortex", provider=provider, model_name=model_name)

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sensory processing:
        1. Breaks down input into components (Questions, Statements, Commands).
        2. Identifies key entities/topics.
        3. Formats for downstream agents.
        """
        user_input = inputs.get("input", "")
        
        system_prompt = """
        You are the Sensory Agent, acting as the Thalamus and Sensory Cortex.
        Your job is to parse raw input and structure it for the Brain.
        
        Output Format:
        - Input Type: (Question/Statement/Command/Creative Prompt)
        - Key Entities: [List of main subjects]
        - Intent: What does the user want?
        - Priority: (High/Medium/Low)
        """
        
        response = self._query_llm(system_prompt, user_input)
        return {"sensory_analysis": response}
