import os
import subprocess
import sys
import tempfile

from state import AgentState

MAX_REPAIR_ATTEMPTS = 3


def _run_code(code: str) -> tuple[bool, str]:
    """Write code to a temp file and execute it headlessly."""
    headless = code.replace("show_object(", "#show_object(")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(headless)
        tmp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return True, ""
        return False, result.stderr or result.stdout
    except Exception as e:
        return False, str(e)
    finally:
        os.unlink(tmp_path)


def execute_node(state: AgentState) -> dict:
    print("[4/5] Executing code...")
    success, error = _run_code(state["generated_code"])

    updates: dict = {"execution_success": success, "execution_error": error}

    if success:
        updates["final_message"] = "✓ Code ready."
        print("  ✓ Execution succeeded")
    elif state["repair_attempts"] >= MAX_REPAIR_ATTEMPTS:
        updates["final_message"] = (
            f"✗ Could not fix after {state['repair_attempts']} repair attempts."
        )
        print(f"  ✗ Max repairs reached: {error[:120]}")
    else:
        print(f"  ✗ Execution failed (attempt {state['repair_attempts']}): {error[:120]}")

    return updates
