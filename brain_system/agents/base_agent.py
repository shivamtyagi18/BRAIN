
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from langchain_core.messages import HumanMessage, SystemMessage
from ..core.llm_interface import LLMFactory

class BaseAgent(ABC):
    def __init__(self, name: str, role: str, provider: str = "gemini", model_name: str = None):
        self.name = name
        self.role = role
        self.persona_context: str = ""  # Injected by orchestrator when persona is active
        self.llm = LLMFactory.create_llm(provider=provider, model_name=model_name)
    
    @abstractmethod
    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input dictionary and return a result dictionary.
        Must be implemented by subclasses.
        """
        pass

    def _query_llm(self, system_prompt: str, user_input: str) -> str:
        """
        Helper method to query the LLM with a system and user message.
        Prepends persona context if active.
        """
        full_prompt = system_prompt
        if self.persona_context:
            full_prompt = self.persona_context + "\n\n" + system_prompt

        messages = [
            SystemMessage(content=full_prompt),
            HumanMessage(content=user_input)
        ]
        response = self.llm.invoke(messages)
        return response.content

