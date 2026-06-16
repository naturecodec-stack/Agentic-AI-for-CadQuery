from state import AgentState
from llm import call_llm

MAX_ATTEMPTS = 3

SYSTEM_FIX = """You are a CadQuery debugging expert. Fix the broken script.
Rules:
- Output ONLY the fixed Python code — no markdown, no backticks, no explanation
- Keep show_object(result) at the end
- Fix ONLY what is causing the error
- Do not restructure or rewrite the whole script unless necessary"""

SYSTEM_REWRITE = """You are an expert CadQuery programmer. The previous attempts to fix a script have all failed.
Write a completely fresh, correct CadQuery script for the original request.

Key rules:
- Output ONLY raw Python code — no markdown, no backticks, no explanation
- import cadquery as cq at the top
- Store final result in `result`
- End with show_object(result)
- Use simpler, more reliable CadQuery patterns (avoid complex selectors)
- Build bodies separately and union them for complex shapes"""


def _strip_markdown(code: str) -> str:
    if code.startswith("```"):
        lines = [l for l in code.splitlines() if not l.startswith("```")]
        return "\n".join(lines).strip()
    return code


def repair_node(state: AgentState) -> dict:
    attempt = state["repair_attempts"] + 1
    print(f"[5/5] Repair attempt {attempt}/{MAX_ATTEMPTS}...")

    history = list(state["repair_history"])
    history.append((state["generated_code"], state["execution_error"]))

    if attempt < MAX_ATTEMPTS:
        # Attempts 1 & 2: targeted fix with full history context
        history_text = ""
        for i, (code, err) in enumerate(history[:-1], 1):
            history_text += f"\n--- Previous attempt {i} (also failed) ---\nError: {err[:300]}\n"

        user = (
            f"Original request: {state['user_request']}\n\n"
            f"{history_text}"
            f"--- Current broken script ---\n{state['generated_code']}\n\n"
            f"--- Current error ---\n{state['execution_error']}\n\n"
            f"Fix the script. Return only the corrected code."
        )
        fixed = call_llm(state["api_key"], state["model"], SYSTEM_FIX, user)
    else:
        # Final attempt: full rewrite with a different strategy
        print("  [Repair] All fixes failed — rewriting from scratch...")
        history_text = "\n".join(
            f"Attempt {i+1} error: {err[:200]}"
            for i, (_, err) in enumerate(history)
        )
        user = (
            f"Original request: {state['user_request']}\n\n"
            f"Previous attempts all failed:\n{history_text}\n\n"
            f"Write a completely fresh, simpler CadQuery script that achieves the same result."
        )
        fixed = call_llm(state["api_key"], state["model"], SYSTEM_REWRITE, user)

    print(f"  ✓ Repaired code received (attempt {attempt})")
    return {
        "generated_code": _strip_markdown(fixed),
        "repair_attempts": attempt,
        "repair_history": history,
    }
