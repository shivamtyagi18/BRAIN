
import json
from typing import TypedDict, Annotated, List, Union, Optional
from langgraph.graph import StateGraph, END

from ..agents.sensory_agent import SensoryAgent
from ..agents.memory_agent import MemoryAgent
from ..agents.emotional_agent import EmotionalAgent
from ..agents.logic_agent import LogicAgent
from ..agents.executive_agent import ExecutiveAgent
from .persona import PersonaProfile
from .working_memory import WorkingMemory
from .vector_memory import VectorMemory

class BrainState(TypedDict):
    input: str
    conversation_context: str
    sensory_analysis: str
    memory_context: str
    raw_memories: List[str]
    logical_analysis: str
    emotional_analysis: str
    final_response: str

class BrainOrchestrator:
    def __init__(self, provider: str = "gemini", model_name: str = None):
        self.provider = provider
        self.model_name = model_name
        self.sensory = SensoryAgent(provider=provider, model_name=model_name)
        self.memory = MemoryAgent(provider=provider, model_name=model_name)
        self.emotional = EmotionalAgent(provider=provider, model_name=model_name)
        self.logic = LogicAgent(provider=provider, model_name=model_name)
        self.executive = ExecutiveAgent(provider=provider, model_name=model_name)
        self.persona: Optional[PersonaProfile] = None

        # Memory subsystems
        self.working_memory = WorkingMemory(max_turns=15)
        self.vector_memory = VectorMemory()

        # Wire vector memory into memory agent
        self.memory.vector_memory = self.vector_memory

        self.app = self._build_graph()

    def set_persona(self, filepath: str):
        """Load a persona from a document and inject into all agents."""
        self.persona = PersonaProfile()
        self.persona.load_from_document(
            filepath,
            provider=self.provider,
            model_name=self.model_name
        )
        self._inject_persona()

        # Index the full document text for biography search
        from .document_loader import DocumentLoader
        text = DocumentLoader.load(filepath)
        self.vector_memory.index_text(text, self.persona.name or "persona")

    def set_persona_from_dict(self, persona_dict: dict):
        """Load a pre-curated persona from a dict and inject into all agents."""
        self.persona = PersonaProfile()
        self.persona.load_from_dict(persona_dict)
        self._inject_persona()

        # Index the pre-curated profile fields for biography search
        profile_fields = persona_dict.get("profile", {})
        self.vector_memory.index_profile(
            profile_fields, persona_dict.get("name", "persona")
        )

    def _inject_persona(self):
        """Inject role-specific persona context into each agent."""
        agents = [self.sensory, self.memory, self.emotional, self.logic, self.executive]
        for agent in agents:
            agent.persona_context = self.persona.get_agent_context(agent.role)

    def _build_graph(self):
        workflow = StateGraph(BrainState)

        # Add Nodes
        workflow.add_node("sensory_processing", self._sensory_node)
        workflow.add_node("memory_retrieval", self._memory_node)
        workflow.add_node("logic_processing", self._logic_node)
        workflow.add_node("emotional_processing", self._emotion_node)
        workflow.add_node("executive_decision", self._executive_node)

        # Define Edges
        # 1. Start -> Sensory
        workflow.set_entry_point("sensory_processing")

        # 2. Sensory -> Parallel Processing (Memory, Logic, Emotion)
        workflow.add_edge("sensory_processing", "memory_retrieval")
        workflow.add_edge("sensory_processing", "logic_processing")
        workflow.add_edge("sensory_processing", "emotional_processing")

        # 3. Parallel Processing -> Executive
        workflow.add_edge("memory_retrieval", "executive_decision")
        workflow.add_edge("logic_processing", "executive_decision")
        workflow.add_edge("emotional_processing", "executive_decision")

        # 4. Executive -> End
        workflow.add_edge("executive_decision", END)

        return workflow.compile()

    # Node Functions
    def _sensory_node(self, state: BrainState):
        result = self.sensory.process({"input": state["input"]})
        return {"sensory_analysis": result["sensory_analysis"]}

    def _memory_node(self, state: BrainState):
        result = self.memory.process({"input": state["input"]})
        return {
            "memory_context": result["memory_context"],
            "raw_memories": result["raw_memories"]
        }

    def _logic_node(self, state: BrainState):
        result = self.logic.process({
            "input": state["input"],
            "context": state.get("memory_context", "")
        })
        return {"logical_analysis": result["logical_analysis"]}

    def _emotion_node(self, state: BrainState):
        result = self.emotional.process({
            "input": state["input"],
            "context": state.get("memory_context", "")
        })
        return {"emotional_analysis": result["emotional_analysis"]}

    def _executive_node(self, state: BrainState):
        result = self.executive.process({
            "input": state["input"],
            "sensory_analysis": state["sensory_analysis"],
            "memory_context": state["memory_context"],
            "logical_analysis": state["logical_analysis"],
            "emotional_analysis": state["emotional_analysis"],
            "conversation_context": state.get("conversation_context", ""),
        })

        # Store the turn in working memory (conversation buffer)
        self.working_memory.add_turn(
            state["input"], result["final_response"]
        )

        return {"final_response": result["final_response"]}

    def run(self, user_input: str) -> dict:
        """Run the brain pipeline. Returns full state with all agent outputs."""
        initial_state = BrainState(
            input=user_input,
            conversation_context=self.working_memory.get_context(last_n=10),
        )
        result = self.app.invoke(initial_state)
        return {
            "final_response": result["final_response"],
            "agent_outputs": {
                "sensory": {
                    "name": "Sensory Agent",
                    "role": "Thalamus & Sensory Cortex",
                    "output": result.get("sensory_analysis", ""),
                },
                "memory": {
                    "name": "Memory Agent",
                    "role": "Hippocampus",
                    "output": result.get("memory_context", ""),
                },
                "logic": {
                    "name": "Logic Agent",
                    "role": "Left Frontal Lobe",
                    "output": result.get("logical_analysis", ""),
                },
                "emotional": {
                    "name": "Emotional Agent",
                    "role": "Amygdala & Limbic System",
                    "output": result.get("emotional_analysis", ""),
                },
                "executive": {
                    "name": "Executive Agent",
                    "role": "Prefrontal Cortex",
                    "output": result.get("final_response", ""),
                },
            }
        }
