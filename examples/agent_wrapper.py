"""Wrap your own agent with Brain's cognitive pipeline.

The Brain's four preprocessing agents (Sensory, Memory, Logic, Emotional)
run first, then pass their signals to YOUR agent function — which acts as
the "executive" decision-maker.

Install:
    pip install brain-system

Run:
    python examples/agent_wrapper.py
"""

from brain_system import AgentWrapper, BrainContext


# --- 1. Define your agent function ---
# It receives the original query + a BrainContext with all cognitive signals.
def my_agent(query: str, ctx: BrainContext) -> str:
    """Your custom agent logic — use brain signals however you want."""
    return (
        f"📋 Here's my analysis:\n\n"
        f"The brain's logic engine says:\n{ctx.logic[:300]}\n\n"
        f"The emotional reading:\n{ctx.emotional[:300]}\n\n"
        f"My final answer: I've considered both logic and emotion to respond."
    )


# --- 2. Wrap it with Brain's cognitive pipeline ---
agent = AgentWrapper(my_agent, provider="ollama", model_name="mistral")

# --- 3. Run it ---
result = agent.run("Should AI be regulated?")

print("🧠 Response from YOUR agent (powered by Brain):")
print(result.response)

print("\n--- Raw Brain Signals ---")
print(f"📡 Sensory:   {result.sensory[:150]}...")
print(f"🔬 Logic:     {result.logic[:150]}...")
print(f"❤️  Emotional: {result.emotional[:150]}...")
