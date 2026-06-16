from state import AgentState
from llm import call_llm

SYSTEM = """You are a CAD geometry expert and CadQuery construction planner.

Analyze the user's request and produce a structured build plan.

Return your analysis in EXACTLY this format:

SHAPE: <one-line description of the overall shape>

FEATURES:
- <feature 1>
- <feature 2>
- ...

DIMENSIONS:
- <dimension name>: <value with unit>
- ...

BUILD_STEPS:
1. <first CadQuery operation — e.g. "Create base box 80x40x10 on XY plane">
2. <second operation>
3. ...

COMPLEXITY: simple | medium | complex

TIPS:
- <any non-obvious construction advice — face selector choices, boolean order, fillet last, etc.>

Rules:
- Be specific with numbers — assume standard dimensions if not given
- BUILD_STEPS must be in the correct CadQuery construction order (booleans before fillets, etc.)
- TIPS should flag face selector risks after boolean ops, workplane choices, and similar pitfalls
- Think like a mechanical engineer writing a machining plan"""


def planning_node(state: AgentState) -> dict:
    print("[1/5] Planning...")
    user = f"Plan the CadQuery construction for:\n{state['user_request']}"
    plan = call_llm(state["api_key"], state["model"], SYSTEM, user, state["image_path"])
    print(f"  Plan:\n{plan}")
    return {"plan": plan}
