"""
Code Critic — v5 (local model via Ollama, text_model).
"""

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from .llm_factory import get_text_llm

SYSTEM = """You are a CadQuery Code Critic.

Compare the FEATURE PLAN against GENERATED CODE. Find LOGICAL mismatches only.
DO NOT check syntax — code already executed. Only check LOGIC.

CHECK FOR:
- Feature count: "plan says 4 holes, code has 2 pushPoints"
- Missing features: "plan says fillet, no .fillet() call"
- Wrong dimensions: "plan says 80mm, code has box(40, ...)"
- Wrong shape type: "plan says hollow/shell, code is solid"
- Missing show_object()

RESPOND WITH VALID JSON ONLY (no markdown fences):
{
  "issues_found": true,
  "issues": ["Plan says 4 holes but code only has 2 pushPoints"],
  "corrections": ["Add all 4 corner positions to pushPoints"],
  "severity": "critical|minor|none"
}

If no issues: {"issues_found": false, "issues": [], "corrections": [], "severity": "none"}"""


def run_code_critic(ollama_url: str, text_model: str,
                    plan: str, code: str) -> dict:
    if not plan or not code:
        return {"issues_found": False, "issues": [], "corrections": [], "severity": "none"}

    llm = get_text_llm(ollama_url, text_model, temperature=0.0)
    prompt = f"FEATURE PLAN:\n{plan}\n\nGENERATED CODE:\n```python\n{code}\n```\n\nFind logical mismatches."

    result = llm.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=prompt)])
    raw = result.content if isinstance(result.content, str) else str(result.content)
    raw = re.sub(r"^```[a-z]*\n?", "", raw.strip(), flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw.strip())

    try:
        return json.loads(raw.strip())
    except Exception:
        return {"issues_found": False, "issues": [], "corrections": [], "severity": "none"}


def format_critic_feedback(data: dict) -> str:
    if not data or not data.get("issues_found"):
        return ""
    lines = [
        "=== CODE CRITIC: PLAN vs CODE MISMATCH ===",
        f"Severity: {data.get('severity', 'unknown')}",
        "Issues found:",
    ]
    for issue in data.get("issues", []):
        lines.append(f"  ISSUE: {issue}")
    lines.append("Required corrections:")
    for fix in data.get("corrections", []):
        lines.append(f"  FIX: {fix}")
    lines.append("=== REWRITE CODE TO FIX ALL ISSUES ===")
    return "\n".join(lines)
