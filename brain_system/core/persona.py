
from typing import Dict, Any, Optional
from .document_loader import DocumentLoader
from .llm_interface import LLMFactory


class PersonaProfile:
    """
    Extracts and stores a persona profile from a biography/autobiography.
    The profile is injected into agent system prompts so the brain
    responds as that person would.
    """

    def __init__(self):
        self.name: str = ""
        self.profile: Dict[str, str] = {}
        self.raw_summary: str = ""
        self.active: bool = False

    def load_from_document(
        self,
        filepath: str,
        provider: str = "gemini",
        model_name: str = None
    ):
        """
        Load a document, extract a persona profile using the LLM.
        """
        print(f"📖 Loading document: {filepath}")
        full_text = DocumentLoader.load(filepath)

        # If document is very large, use only the first ~8000 chars for profile extraction
        # to stay within context limits
        extract_text = full_text[:8000] if len(full_text) > 8000 else full_text

        llm = LLMFactory.create_llm(provider=provider, model_name=model_name)

        extraction_prompt = f"""
Analyze the following biography/autobiography text and extract a detailed persona profile.
Return the profile in EXACTLY this format (fill in each field):

NAME: [Full name of the person]
ERA: [Time period they lived/live in]
BELIEFS: [Core beliefs, philosophies, worldview — 2-3 sentences]
VALUES: [What they valued most — 2-3 sentences]  
SPEECH_STYLE: [How they spoke/wrote — formal, casual, poetic, blunt, etc. Include notable phrases or patterns]
EMOTIONAL_TENDENCIES: [Their emotional patterns — were they passionate, stoic, anxious, optimistic, etc.]
REASONING_STYLE: [How they approached problems — analytical, intuitive, empirical, philosophical, etc.]
KEY_EXPERIENCES: [3-5 defining life events that shaped their worldview]
PERSONALITY_TRAITS: [5-7 dominant personality traits]
KNOWN_VIEWS: [Their well-known stances on important topics — 2-3 sentences]

Text to analyze:
{extract_text}
"""

        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content=extraction_prompt)])
        raw_profile = response.content

        # Parse the structured profile
        self._parse_profile(raw_profile)
        self.raw_summary = raw_profile
        self.active = True

        # Also store the full document text for memory seeding
        self._document_text = full_text

        print(f"✅ Persona loaded: {self.name}")

    def _parse_profile(self, raw_text: str):
        """Parse the LLM's structured output into a dictionary."""
        fields = [
            "NAME", "ERA", "BELIEFS", "VALUES", "SPEECH_STYLE",
            "EMOTIONAL_TENDENCIES", "REASONING_STYLE",
            "KEY_EXPERIENCES", "PERSONALITY_TRAITS", "KNOWN_VIEWS"
        ]

        for field in fields:
            self.profile[field] = ""

        for line in raw_text.split("\n"):
            line = line.strip()
            for field in fields:
                if line.upper().startswith(f"{field}:"):
                    value = line[len(field) + 1:].strip()
                    self.profile[field] = value
                    if field == "NAME":
                        self.name = value
                    break

    def get_agent_context(self, agent_role: str) -> str:
        """
        Returns persona-specific context tailored for a given agent role.
        """
        if not self.active:
            return ""

        base = f"""
🎭 PERSONA MODE ACTIVE — You are embodying: {self.name}
Era: {self.profile.get('ERA', 'Unknown')}
Personality: {self.profile.get('PERSONALITY_TRAITS', '')}
"""

        role_specific = {
            "Amygdala & Limbic System": f"""
Emotional Tendencies: {self.profile.get('EMOTIONAL_TENDENCIES', '')}
Values: {self.profile.get('VALUES', '')}
Respond with the emotional patterns of {self.name}. Feel as they would feel.
""",
            "Left Frontal Lobe": f"""
Reasoning Style: {self.profile.get('REASONING_STYLE', '')}
Known Views: {self.profile.get('KNOWN_VIEWS', '')}
Think and reason exactly as {self.name} would. Use their analytical approach.
""",
            "Prefrontal Cortex (PFC)": f"""
Beliefs: {self.profile.get('BELIEFS', '')}
Speech Style: {self.profile.get('SPEECH_STYLE', '')}
Key Experiences: {self.profile.get('KEY_EXPERIENCES', '')}
Make decisions as {self.name} would. Speak in their voice and style.
""",
            "Thalamus & Sensory Cortex": f"""
Interpret the input through the lens of {self.name}'s worldview and era.
""",
            "Hippocampus": f"""
Key Experiences: {self.profile.get('KEY_EXPERIENCES', '')}
Draw on {self.name}'s life experiences as context for memory retrieval.
"""
        }

        return base + role_specific.get(agent_role, "")
