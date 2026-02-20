
from typing import Any, Dict, List, Optional
from .base_agent import BaseAgent


class MemoryAgent(BaseAgent):
    def __init__(self, provider: str = "gemini", model_name: str = None):
        super().__init__(name="MemoryAgent", role="Hippocampus", provider=provider, model_name=model_name)
        self._vector_memory = None  # Set by orchestrator when persona is loaded

    @property
    def vector_memory(self):
        return self._vector_memory

    @vector_memory.setter
    def vector_memory(self, vm):
        self._vector_memory = vm

    def process(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Memory processing — mirrors the Hippocampus.
        Searches the persona's biography for life experiences relevant
        to the user's current input.
        """
        user_input = inputs.get("input", "")

        # Search persona biography via ZVec semantic search
        retrieved_passages = self._search_persona_memories(user_input)

        if not retrieved_passages:
            # No persona loaded or no relevant memories found
            return {
                "memory_context": "No persona memories available. Responding without biographical context.",
                "raw_memories": []
            }

        formatted_memories = "\n".join(
            [f"- {passage}" for passage in retrieved_passages]
        )

        system_prompt = f"""You are the Memory System of a digital brain, modeling the Hippocampus — the brain's autobiographical memory hub.

YOUR BIOLOGICAL ROLE:
The Hippocampus stores and retrieves EPISODIC MEMORIES — specific life experiences, personal events, and autobiographical knowledge. When the current input arrives, you search the persona's life history for relevant experiences, beliefs, and formative moments.

YOUR AUDIENCE:
Your output is consumed by the Logic Agent, Emotional Agent, and Executive Agent. They need a concise briefing of relevant life experiences, not raw data.

RETRIEVED PERSONA MEMORIES (from biography/autobiography):
{formatted_memories}

YOUR TASK — Think step-by-step:

Step 1: **Relevance Assessment** — Which retrieved passages are most relevant to the current input? Rate each (High / Medium / Low). Discard Low-relevance passages.

Step 2: **Autobiographical Linking** (the Hippocampus's core function)
   - What specific LIFE EXPERIENCES connect to the user's question?
   - What formative events shaped the persona's perspective on this topic?
   - What personal struggles or triumphs are relevant here?

Step 3: **Pattern Detection**
   - What recurring THEMES from the persona's life apply here?
   - How did this person's views EVOLVE over time on related topics?

Step 4: **Memory Briefing** — Synthesize into a concise briefing for downstream agents.

## OUTPUT FORMAT (use these exact headers):
RELEVANT MEMORIES: [list only High/Medium relevance passages with brief context]
LIFE PATTERN: [key patterns from the persona's life, or "None detected"]
MEMORY BRIEFING: [2-3 sentence synthesis of relevant life experiences]
FLAGS: [any critical biographical context that must not be ignored, or "None"]

## CONSTRAINTS:
- Keep your TOTAL output under 200 words
- Do NOT fabricate memories — only use what is provided above
- Do NOT answer the user's question — you provide biographical context, not conclusions
- Focus on SPECIFIC life experiences, not general knowledge"""

        response = self._query_llm(system_prompt, user_input)
        return {
            "memory_context": response,
            "raw_memories": retrieved_passages
        }

    def _search_persona_memories(self, query: str, top_k: int = 5) -> List[str]:
        """Search the persona's indexed biography for relevant passages."""
        if self._vector_memory is None or not self._vector_memory.is_loaded:
            return []
        return self._vector_memory.search(query, top_k=top_k)
