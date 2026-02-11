
from typing import Any, Dict
from ..core.memory_store import MemoryStore
from .base_agent import BaseAgent

class MemoryAgent(BaseAgent):
    def __init__(self, provider: str = "gemini", model_name: str = None):
        super().__init__(name="MemoryAgent", role="Hippocampus", provider=provider, model_name=model_name)
        self.memory_store = MemoryStore()

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieves relevant past memories based on the input.
        """
        user_input = inputs.get("input", "")
        
        # 1. Retrieve relevant memories from LTM
        past_memories = self.memory_store.retrieve_memories(user_input, limit=3)
        formatted_memories = "\n".join([f"- {m['content']} ({m['timestamp']})" for m in past_memories])
        
        if not formatted_memories:
            formatted_memories = "No relevant past memories found."
            
        return {
            "memory_context": formatted_memories,
            "raw_memories": past_memories
        }

    def commit_memory(self, memory_text: str):
        """
        Called by Executive Agent or Orchestrator after a decision is made.
        """
        self.memory_store.add_memory(memory_text)
