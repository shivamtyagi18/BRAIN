"""
brain_system.wrapper
~~~~~~~~~~~~~~~~~~~~

High-level wrappers that let developers add Brain's five-agent cognitive
pipeline to their own projects.

**BrainWrapper** — standalone brain, call ``.think()`` directly::

    from brain_system import BrainWrapper

    brain = BrainWrapper(provider="openai", model_name="gpt-4o")
    result = brain.think("What is justice?")
    print(result.response)

**AgentWrapper** — wrap YOUR agent with brain processing::

    from brain_system import AgentWrapper

    @AgentWrapper(provider="openai")
    def my_agent(query: str, brain_context) -> str:
        return f"Based on logic: {brain_context.logic[:200]}..."

    result = my_agent("What is justice?")
    print(result.response)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Union

from .core.orchestrator import BrainOrchestrator


@dataclass
class BrainResult:
    """Structured result from a Brain processing run.

    Attributes:
        response: The final synthesized response from the Executive Agent.
        agent_signals: Dictionary of each agent's individual output, keyed by
            agent name (``sensory``, ``memory``, ``logic``, ``emotional``,
            ``executive``).  Each value is a dict with ``name``, ``role``,
            and ``output`` keys.
    """

    response: str
    agent_signals: Dict[str, Dict[str, str]] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------

    @property
    def sensory(self) -> str:
        """Raw output from the Sensory Agent (Thalamus)."""
        return self.agent_signals.get("sensory", {}).get("output", "")

    @property
    def memory(self) -> str:
        """Raw output from the Memory Agent (Hippocampus)."""
        return self.agent_signals.get("memory", {}).get("output", "")

    @property
    def logic(self) -> str:
        """Raw output from the Logic Agent (Frontal Lobe)."""
        return self.agent_signals.get("logic", {}).get("output", "")

    @property
    def emotional(self) -> str:
        """Raw output from the Emotional Agent (Amygdala)."""
        return self.agent_signals.get("emotional", {}).get("output", "")

    @property
    def executive(self) -> str:
        """Raw output from the Executive Agent (Prefrontal Cortex)."""
        return self.agent_signals.get("executive", {}).get("output", "")


class BrainWrapper:
    """Wrap any agent with Brain's five-agent cognitive pipeline.

    This is the primary developer-facing class.  Instantiate it with an LLM
    provider, then call :meth:`think` to process input through all five
    agents (Sensory → Memory / Logic / Emotional → Executive).

    Parameters:
        provider: LLM provider — ``"gemini"``, ``"openai"``, or ``"ollama"``.
        model_name: Model identifier to use (provider-specific).  When *None*,
            each provider falls back to its default model.
        memory_path: Path to the JSON file used for long-term memory.
            Defaults to ``brain_memory.json`` in the current working directory.

    Example::

        from brain_system import BrainWrapper

        brain = BrainWrapper(provider="ollama", model_name="mistral")
        result = brain.think("Explain quantum entanglement simply.")
        print(result.response)
    """

    def __init__(
        self,
        provider: str = "gemini",
        model_name: Optional[str] = None,
        memory_path: Optional[str] = None,
    ) -> None:
        self._provider = provider
        self._model_name = model_name
        self._memory_path = memory_path

        # Build the underlying orchestrator (creates all 5 agents + LangGraph)
        self._orchestrator = BrainOrchestrator(
            provider=provider,
            model_name=model_name,
        )

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def think(self, user_input: str) -> BrainResult:
        """Process *user_input* through the full five-agent pipeline.

        Returns a :class:`BrainResult` containing the synthesised response
        and each agent's individual signal.
        """
        raw = self._orchestrator.run(user_input)
        return BrainResult(
            response=raw["final_response"],
            agent_signals=raw["agent_outputs"],
        )

    # ------------------------------------------------------------------
    # Persona helpers
    # ------------------------------------------------------------------

    @staticmethod
    def list_personas() -> list[dict]:
        """Return available pre-curated personas.

        Each dict has: ``id``, ``name``, ``emoji``, ``category``, ``source``.
        Use the ``id`` value with :meth:`load_persona`.
        """
        from .personas.persona_registry import list_personas as _list
        return _list()

    def load_persona(self, persona_or_path: str) -> None:
        """Load a persona by pre-curated ID or from a document file.

        Pre-curated IDs: ``gandhi``, ``einstein``, ``mandela``, ``curie``,
        ``davinci``, ``mlk``, ``tesla``, ``lovelace``.

        Call :meth:`list_personas` to see all available IDs.

        Also accepts a ``.txt`` or ``.pdf`` file path for custom personas.
        """
        from .personas.persona_registry import get_persona

        persona_data = get_persona(persona_or_path)
        if persona_data is not None:
            self._orchestrator.set_persona_from_dict(persona_data)
        else:
            self._orchestrator.set_persona(persona_or_path)

    def clear_persona(self) -> None:
        """Remove the active persona.  Agents revert to default behaviour."""
        agents = [
            self._orchestrator.sensory,
            self._orchestrator.memory,
            self._orchestrator.emotional,
            self._orchestrator.logic,
            self._orchestrator.executive,
        ]
        for agent in agents:
            agent.persona_context = ""
        self._orchestrator.persona = None

    # ------------------------------------------------------------------
    # Memory helpers
    # ------------------------------------------------------------------

    def clear_memory(self) -> None:
        """Clear conversation history (working memory)."""
        self._orchestrator.working_memory.clear()

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def provider(self) -> str:
        """The active LLM provider name."""
        return self._provider

    @property
    def model_name(self) -> Optional[str]:
        """The active model name (or *None* for provider default)."""
        return self._model_name

    @property
    def persona_active(self) -> bool:
        """Whether a persona is currently loaded."""
        return (
            self._orchestrator.persona is not None
            and self._orchestrator.persona.active
        )

    @property
    def persona_name(self) -> Optional[str]:
        """Name of the active persona, or *None*."""
        if self.persona_active:
            return self._orchestrator.persona.name
        return None

    def __repr__(self) -> str:
        parts = [f"provider={self._provider!r}"]
        if self._model_name:
            parts.append(f"model={self._model_name!r}")
        if self.persona_active:
            parts.append(f"persona={self.persona_name!r}")
        return f"BrainWrapper({', '.join(parts)})"


# ======================================================================
# AgentWrapper — wrap any existing agent with brain processing
# ======================================================================


@dataclass
class BrainContext:
    """Cognitive signals from Brain's preprocessing agents.

    Passed to your agent function so it can use the Brain's analysis
    when generating its response.

    Attributes:
        query: The original user input.
        sensory: Sensory Agent output — input classification and routing.
        memory: Memory Agent output — relevant past context.
        logic: Logic Agent output — logical/analytical reasoning.
        emotional: Emotional Agent output — emotional and ethical analysis.
    """

    query: str = ""
    sensory: str = ""
    memory: str = ""
    logic: str = ""
    emotional: str = ""


class AgentWrapper:
    """Wrap an existing agent function with Brain's cognitive pipeline.

    Brain's four preprocessing agents (Sensory, Memory, Logic, Emotional)
    run first, then their signals are passed to **your** agent function
    as a :class:`BrainContext`.  Your function acts as the "executive"
    decision-maker.

    Can be used as a **class** or as a **decorator**.

    **As a class**::

        from brain_system import AgentWrapper, BrainContext

        def my_agent(query: str, ctx: BrainContext) -> str:
            return f"Logic says: {ctx.logic[:200]}"

        agent = AgentWrapper(my_agent, provider="openai")
        result = agent.run("What is justice?")
        print(result.response)

    **As a decorator**::

        from brain_system import AgentWrapper

        @AgentWrapper(provider="ollama", model_name="mistral")
        def my_agent(query: str, brain_context) -> str:
            return f"My take: {brain_context.logic[:200]}"

        result = my_agent("What is justice?")
        print(result.response)

    Parameters:
        agent_fn: Your agent function.  Must accept ``(query: str, brain_context: BrainContext)``
            and return a ``str``.
        provider: LLM provider for the brain agents.
        model_name: Model identifier (provider-specific).
        memory_path: Path to JSON memory file.
    """

    def __init__(
        self,
        agent_fn: Optional[Callable] = None,
        *,
        provider: str = "gemini",
        model_name: Optional[str] = None,
        memory_path: Optional[str] = None,
    ) -> None:
        self._provider = provider
        self._model_name = model_name
        self._memory_path = memory_path
        self._agent_fn = agent_fn

        # If agent_fn is provided, build the brain immediately
        if agent_fn is not None:
            self._brain = BrainWrapper(
                provider=provider,
                model_name=model_name,
                memory_path=memory_path,
            )

    def __call__(self, *args, **kwargs):
        """Support both decorator and direct-call usage."""
        # Case 1: Used as @AgentWrapper(provider=...) — agent_fn not set yet
        # The first __call__ receives the decorated function
        if self._agent_fn is None and len(args) == 1 and callable(args[0]):
            self._agent_fn = args[0]
            self._brain = BrainWrapper(
                provider=self._provider,
                model_name=self._model_name,
                memory_path=self._memory_path,
            )
            return self  # Return self so subsequent calls go to run()

        # Case 2: Called as agent("some input") — run the pipeline
        return self.run(*args, **kwargs)

    def run(self, user_input: str) -> BrainResult:
        """Process *user_input* through Brain's agents, then your agent.

        1. Brain's Sensory, Memory, Logic, and Emotional agents process the input.
        2. Their signals are bundled into a :class:`BrainContext`.
        3. Your agent function is called with ``(user_input, brain_context)``.
        4. Your function's return value becomes the final ``BrainResult.response``.
        """
        if self._agent_fn is None:
            raise RuntimeError("No agent function provided to AgentWrapper.")

        # Run the full brain pipeline to get all agent signals
        brain_result = self._brain.think(user_input)

        # Build the context for the user's agent
        context = BrainContext(
            query=user_input,
            sensory=brain_result.sensory,
            memory=brain_result.memory,
            logic=brain_result.logic,
            emotional=brain_result.emotional,
        )

        # Call the user's agent with original input + brain context
        user_response = self._agent_fn(user_input, context)

        # Return a BrainResult with the user's response + brain signals
        return BrainResult(
            response=user_response,
            agent_signals=brain_result.agent_signals,
        )

    # ------------------------------------------------------------------
    # Persona & memory (delegated to internal BrainWrapper)
    # ------------------------------------------------------------------

    def load_persona(self, filepath: str) -> None:
        """Load a persona into the brain agents."""
        self._brain.load_persona(filepath)

    def clear_persona(self) -> None:
        """Clear the active persona."""
        self._brain.clear_persona()

    def clear_memory(self) -> None:
        """Clear all stored memories."""
        self._brain.clear_memory()

    def __repr__(self) -> str:
        fn_name = getattr(self._agent_fn, "__name__", "unknown")
        return f"AgentWrapper({fn_name}, provider={self._provider!r})"

