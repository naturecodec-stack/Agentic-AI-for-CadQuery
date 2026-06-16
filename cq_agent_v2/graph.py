import subprocess
import sys
import tempfile
import os

from state import AgentState
from nodes.planning import planning_node
from nodes.skill_selection import skill_selection_node
from nodes.code_generation import code_generation_node
from nodes.repair import repair_node

MAX_REPAIR_ATTEMPTS = 3


def _execute_code(code: str) -> tuple[bool, str]:
    """Write code to a temp file, run it, return (success, error)."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        # Replace show_object with a no-op for headless execution check
        headless_code = code.replace("show_object(", "#show_object(")
        f.write(headless_code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return True, ""
        else:
            return False, result.stderr or result.stdout
    except Exception as e:
        return False, str(e)
    finally:
        os.unlink(tmp_path)


def run_graph(user_request: str, image_path: str,
              api_key: str, model: str) -> AgentState:

    state = AgentState(user_request=user_request, image_path=image_path)

    # Step 1: Plan
    state = planning_node(state, api_key, model)

    # Step 2: Select skill + extract params
    state = skill_selection_node(state, api_key, model)

    # Step 3: Generate code
    state = code_generation_node(state, api_key, model)

    # Step 4: Execute + repair loop
    print("[4/4] Validating code...")
    success, error = _execute_code(state.generated_code)
    state.execution_success = success
    state.execution_error   = error

    while not state.execution_success and state.repair_attempts < MAX_REPAIR_ATTEMPTS:
        state = repair_node(state, api_key, model)
        success, error = _execute_code(state.generated_code)
        state.execution_success = success
        state.execution_error   = error

    if state.execution_success:
        state.final_message = "✓ Code ready."
    else:
        state.final_message = f"✗ Could not fix after {state.repair_attempts} attempts."

    return state
