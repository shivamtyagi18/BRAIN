"""
brain_system.wrapper
~~~~~~~~~~~~~~~~~~~~

High-level wrapper that lets developers add Brain's five-agent cognitive
pipeline to their own projects with a single class.

Usage::

    from brain_system import BrainWrapper

    brain = BrainWrapper(provider="openai", model_name="gpt-4o")
    result = brain.think("What is justice?")
    print(result.response)
    print(result.agent_signals)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

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

        # Override the memory store path if the caller specified one
        if memory_path is not None:
            self._orchestrator.memory.memory_store.filepath = os.path.abspath(
                memory_path
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

    def load_persona(self, filepath: str) -> None:
        """Load a persona from a biography/autobiography document.

        Supported formats: ``.txt``, ``.pdf``.  After loading, every agent
        will respond in the voice and style of the extracted persona.
        """
        self._orchestrator.set_persona(filepath)

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
        """Erase all stored long-term memories."""
        filepath = self._orchestrator.memory.memory_store.filepath
        with open(filepath, "w") as f:
            json.dump([], f)

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
