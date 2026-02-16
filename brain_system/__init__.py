"""Brain System — Multi-Agent Cognitive Architecture powered by LangGraph.

Five specialised AI agents — modelled after the human brain — collaborate
to process input and generate thoughtful, nuanced responses.

Quick start::

    from brain_system import BrainWrapper

    brain = BrainWrapper(provider="openai")
    result = brain.think("What is justice?")
    print(result.response)
"""

__version__ = "0.2.0"

from brain_system.wrapper import BrainWrapper, BrainResult, AgentWrapper, BrainContext  # noqa: F401
from brain_system.core.orchestrator import BrainOrchestrator  # noqa: F401
from brain_system.core.llm_interface import LLMFactory  # noqa: F401
from brain_system.agents.base_agent import BaseAgent  # noqa: F401

__all__ = [
    "BrainWrapper",
    "BrainResult",
    "AgentWrapper",
    "BrainContext",
    "BrainOrchestrator",
    "LLMFactory",
    "BaseAgent",
    "__version__",
]
