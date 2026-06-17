"""
Skill Selector — v5 (local model via Ollama, text_model).
"""

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from .llm_factory import get_text_llm


def run_skill_selector(ollama_url: str, text_model: str, plan: str,
                        skill_registry_path: str) -> list:
    if not plan:
        return []

    try:
        with open(skill_registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)
    except Exception:
        return []

    skill_lines = [f"  {e['name']}: {e['description']}" for e in registry]
    skills_block = "\n".join(skill_lines)

    SYSTEM = f"""You are a CadQuery Skill Selector.

Read the FEATURE PLAN and pick 1-3 skill templates that best match it.

AVAILABLE SKILLS:
{skills_block}

RESPOND WITH VALID JSON ONLY (no markdown fences):
{{
  "selected": [
    {{
      "name": "bracket",
      "reason": "Plan describes an L-shaped bracket",
      "priority": 1
    }}
  ]
}}

If nothing matches well: {{"selected": []}}
Maximum 3 skills. Be selective."""

    llm = get_text_llm(ollama_url, text_model, temperature=0.0)
    result = llm.invoke([
        SystemMessage(content=SYSTEM),
        HumanMessage(content=f"FEATURE PLAN:\n{plan}\n\nSelect best matching skills."),
    ])

    raw = result.content if isinstance(result.content, str) else str(result.content)
    raw = re.sub(r"^```[a-z]*\n?", "", raw.strip(), flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw.strip())

    try:
        return json.loads(raw.strip()).get("selected", [])
    except Exception:
        return []


def format_skill_recommendations(recommendations: list) -> str:
    if not recommendations:
        return ""
    lines = [
        "=== SKILL SELECTOR: RECOMMENDED TEMPLATES ===",
        "Start from these (in priority order):",
    ]
    for rec in sorted(recommendations, key=lambda x: x.get("priority", 9)):
        lines.append(f"  [{rec.get('priority', '?')}] use_skill('{rec['name']}', ...) — {rec['reason']}")
    lines.append("Call use_skill() for priority-1 first, then extend/modify.")
    lines.append("=== USE THE RECOMMENDED SKILL AS STARTING POINT ===")
    return "\n".join(lines)
