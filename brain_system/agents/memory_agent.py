
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

YOUR AUDIENCE:
Your output is consumed by the Logic Agent, Emotional Agent, and Executive Agent. They need a concise contextual briefing, not raw memory dumps.

RETRIEVED MEMORIES (from long-term store):
{formatted_memories}

YOUR TASK — Think step-by-step:

Step 1: **Relevance Assessment** — For each retrieved memory, rate its relevance to the current input (High / Medium / Low). Discard Low-relevance memories.

Step 2: **Associative Linking** (the Hippocampus's signature function)
   - How does the current input CONNECT to past interactions?
   - Has the user asked something similar before? If so, how has the context shifted?
   - Are there contradictions between past and present that other agents should know about?

Step 3: **Pattern Detection**
   - What PATTERNS emerge across multiple memories? (recurring topics, evolving opinions, preferences)
   - Is there a conversational ARC developing? (user is building toward something)

Step 4: **Context Briefing** — Synthesize the above into a concise briefing for downstream agents.

## OUTPUT FORMAT (use these exact headers):
RELEVANT MEMORIES: [list only High/Medium relevance memories with brief context]
PATTERN: [key patterns detected, or "None detected"]
CONTEXT BRIEFING: [2-3 sentence synthesis for downstream agents]
FLAGS: [any critical past context that must not be ignored, or "None"]

## CONSTRAINTS:
- Keep your TOTAL output under 200 words
- Do NOT generate fictional or fabricated memories — only use what is provided above
- Do NOT answer the user's question — you provide context, not conclusions
- If no memories are relevant, say so clearly and briefly"""
        
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

