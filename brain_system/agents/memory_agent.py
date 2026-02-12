
from typing import Any, Dict
from ..core.memory_store import MemoryStore
from .base_agent import BaseAgent

class MemoryAgent(BaseAgent):
    def __init__(self, provider: str = "gemini", model_name: str = None):
        super().__init__(name="MemoryAgent", role="Hippocampus", provider=provider, model_name=model_name)
        self.memory_store = MemoryStore()

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Memory processing — mirrors the Hippocampus and Dorsolateral PFC (working memory).
        Retrieves, contextualizes, and synthesizes relevant past interactions.
        """
        user_input = inputs.get("input", "")
        
        # 1. Retrieve relevant memories from LTM
        past_memories = self.memory_store.retrieve_memories(user_input, limit=5)
        formatted_memories = "\n".join([f"- [{m['timestamp']}] {m['content']}" for m in past_memories])
        
        if not formatted_memories:
            formatted_memories = "No relevant past memories found."

        system_prompt = f"""You are the Memory System of a digital brain, modeling the Hippocampus and the Dorsolateral Prefrontal Cortex (working memory).

YOUR BIOLOGICAL ROLE:
The Hippocampus is the brain's memory hub — it doesn't just STORE memories, it LINKS them. It connects current stimuli to past experiences, creating associative networks. The DLPFC holds recent context in working memory for active manipulation. Together, they give the brain continuity of self.

RETRIEVED MEMORIES (from long-term store):
{formatted_memories}

YOUR TASK — Perform memory processing on the current input:

1. **Episodic Recall**
   - Which retrieved memories are genuinely relevant to the current input? Filter out noise.
   - What PATTERNS emerge across multiple memories? (recurring topics, evolving opinions, consistent preferences)

2. **Associative Linking** (the Hippocampus's signature function)
   - How does the current input CONNECT to past interactions?
   - Has the user asked something similar before? If so, how has the context shifted?
   - Are there contradictions between past and present that other agents should know about?

3. **Temporal Context**
   - How recent are the relevant memories? Recent context should weigh more heavily.
   - Is there a conversational ARC developing? (e.g., the user is building toward a larger question)

4. **Memory Synthesis for Downstream Agents**
   - Provide a concise CONTEXTUAL BRIEFING that the Logic, Emotional, and Executive agents can use.
   - Flag any critical past context that should NOT be ignored (e.g., user corrections, stated preferences, sensitive topics previously discussed).

You are NOT the responder. You are the brain's historian — provide context, not conclusions."""
        
        response = self._query_llm(system_prompt, user_input)
        return {
            "memory_context": response,
            "raw_memories": past_memories
        }

    def commit_memory(self, memory_text: str):
        """
        Called by Executive Agent or Orchestrator after a decision is made.
        """
        self.memory_store.add_memory(memory_text)

