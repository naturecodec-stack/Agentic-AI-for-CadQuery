from state import AgentState
from llm import call_llm

SYSTEM = """You are a CadQuery debugging expert. Fix the broken script.
Rules:
- Output ONLY the fixed Python code — no markdown, no backticks, no explanation
- Keep show_object(result) at the end
- Fix ONLY what is causing the error
"""

MAX_ATTEMPTS = 3


def repair_node(state: AgentState, api_key: str, model: str) -> AgentState:
    state.repair_attempts += 1
    print(f"  [Repair] Attempt {state.repair_attempts}/{MAX_ATTEMPTS}...")

    state.repair_history.append((state.generated_code, state.execution_error))

    user = (
        f"Broken script:\n{state.generated_code}\n\n"
        f"Error:\n{state.execution_error}\n\n"
        f"Fix the script and return only the corrected code."
    )

    fixed = call_llm(api_key, model, SYSTEM, user)

    if fixed.startswith("```"):
        lines = fixed.splitlines()
        lines = [l for l in lines if not l.startswith("```")]
        fixed = "\n".join(lines).strip()

    state.generated_code = fixed
    return state
