"""
Repair Specialist — v5 (local model via Ollama, text_model).
"""

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from .llm_factory import get_text_llm

SYSTEM = """You are a CadQuery Repair Specialist — expert at fixing hard CadQuery errors.

COMMON ERROR PATTERNS:

"StdFail_NotDone" | "BRep_Builder":
  Root: Shape construction failed. Fix: reduce sweep profile size, add .clean() before boolean ops.

"NullPointerException" | "AttributeError: NoneType":
  Root: Empty selection. Fix: try alternate selectors ">Z"->">X", split into variables.

"Cannot add edge to wire":
  Root: Curves don't connect. Fix: use .close(), replace with rect()/circle().

"Fillet failed" | "BRepFilletAPI":
  Root: Radius too large. Fix: reduce radius to <50% of smallest edge, use "|Z" filter.

"could not find a face" | "ValueError":
  Root: Wrong selector. Fix: use positional .faces()[0] instead of string selector.

"Shape is null":
  Root: Boolean on non-overlapping shapes. Fix: translate shapes to overlap first.

"ImportError":
  Root: Missing library. Fix: replace with pure CadQuery equivalent.

RESPOND WITH VALID JSON ONLY (no markdown fences):
{
  "root_cause": "Fillet radius 5mm exceeds wall thickness 3mm",
  "fix_applied": "Reduced fillet to 1mm, applied only to |Z edges",
  "fixed_code": "import cadquery as cq\\nresult = (cq.Workplane('XY').box(80,40,5))\\nshow_object(result)"
}"""


def run_repair_specialist(ollama_url: str, text_model: str,
                           code: str, error: str, plan: str,
                           previous_repair_attempts: int = 0) -> dict:
    if not error:
        return {"fixed_code": code, "root_cause": "Unknown", "fix_applied": ""}

    llm = get_text_llm(ollama_url, text_model, temperature=0.2)

    retry = ""
    if previous_repair_attempts > 0:
        retry = (f"\n\nNOTE: {previous_repair_attempts} previous repair(s) failed. "
                 "Try a completely different implementation approach.")

    prompt = f"""FEATURE PLAN:
{plan}

FAILING CODE:
```python
{code or "(no code generated)"}
```

ERROR:
{error}{retry}

Fix the root cause and provide complete working code."""

    result = llm.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=prompt)])
    raw = result.content if isinstance(result.content, str) else str(result.content)
    raw = re.sub(r"^```[a-z]*\n?", "", raw.strip(), flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw.strip())

    try:
        return json.loads(raw.strip())
    except Exception:
        code_match = re.search(r"(import cadquery.*?show_object\(.*?\))", raw, re.DOTALL)
        return {
            "fixed_code": code_match.group(1).strip() if code_match else "",
            "root_cause": "Parse error in repair response",
            "fix_applied": raw[:300],
        }
