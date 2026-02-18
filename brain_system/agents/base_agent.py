
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
        Injects persona context as a structured section within the prompt.
        """
        full_prompt = system_prompt
        if self.persona_context:
            # Insert persona as a dedicated section after the role definition
            # rather than blindly prepending it
            persona_block = (
                "\n\n--- ACTIVE PERSONA ---\n"
                "You are currently embodying the following persona. "
                "All your processing must be filtered through this identity — "
                "adopt their worldview, reasoning patterns, and communication style.\n\n"
                f"{self.persona_context}\n"
                "--- END PERSONA ---\n"
            )
            # Insert after the first paragraph (role definition) if possible
            first_break = full_prompt.find("\n\n", 10)
            if first_break != -1:
                full_prompt = full_prompt[:first_break] + persona_block + full_prompt[first_break:]
            else:
                full_prompt = full_prompt + persona_block

        messages = [
            SystemMessage(content=full_prompt),
            HumanMessage(content=user_input)
        ]
        response = self.llm.invoke(messages)
        return response.content

