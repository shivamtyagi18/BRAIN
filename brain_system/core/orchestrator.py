
import json
from typing import TypedDict, Annotated, List, Union, Optional
from langgraph.graph import StateGraph, END

from ..agents.sensory_agent import SensoryAgent
from ..agents.memory_agent import MemoryAgent
from ..agents.emotional_agent import EmotionalAgent
from ..agents.logic_agent import LogicAgent
from ..agents.executive_agent import ExecutiveAgent
from .persona import PersonaProfile

class BrainState(TypedDict):
    input: str
    sensory_analysis: str
    memory_context: str
    raw_memories: List[dict]
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
        
        self.app = self._build_graph()

    def set_persona(self, filepath: str):
        """Load a persona from a document and inject into all agents."""
        self.persona = PersonaProfile()
        self.persona.load_from_document(
            filepath,
            provider=self.provider,
            model_name=self.model_name
        )

        # Inject role-specific persona context into each agent
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
            "context": state.get("memory_context", "") # Note: In parallel execution, this might be empty initially.
            # Ideally, Memory should run before Logic/Emotion if they depend on it.
            # For now, we keep them parallel for speed, assuming they analyze the *input*.
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
            "emotional_analysis": state["emotional_analysis"]
        })
        
        # Commit the interaction to memory
        self.memory.commit_memory(
            f"User: {state['input']}\nResponse: {result['final_response']}"
        )
        
        return {"final_response": result["final_response"]}

    def run(self, user_input: str):
        initial_state = BrainState(input=user_input)
        result = self.app.invoke(initial_state)
        return result["final_response"]
