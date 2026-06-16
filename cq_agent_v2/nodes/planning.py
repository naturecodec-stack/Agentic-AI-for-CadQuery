from state import AgentState
from llm import call_llm

SYSTEM = """You are a CAD geometry expert. Analyze the user's request and think freely about:
1. What is the overall shape?
2. What are the key geometric features? (holes, fillets, extrusions, etc.)
3. What are the exact dimensions?
4. What is the best construction strategy?

Output a structured analysis like this:
SHAPE: <overall shape description>
FEATURES: <list of geometric features>
DIMENSIONS: <all dimensions mentioned or assumed>
STRATEGY: <how to build it step by step>

Be specific. Think like a mechanical engineer."""


def planning_node(state: AgentState, api_key: str, model: str) -> AgentState:
    print("[1/4] Thinking...")
    user = f"Analyze this CAD request:\n{state.user_request}"
    state.plan = call_llm(api_key, model, SYSTEM, user, state.image_path)
    print(f"  Analysis:\n{state.plan}")
    return state
