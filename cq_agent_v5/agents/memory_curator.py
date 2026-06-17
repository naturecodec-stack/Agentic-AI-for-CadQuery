"""
Memory Curator — v5 (local model via Ollama, text_model).
"""

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from .llm_factory import get_text_llm

SYSTEM = """You are a CadQuery Memory Curator.

Before saving a new shape, check existing memory and decide: SAVE_NEW | UPDATE_EXISTING | SKIP

Also generate better tags (5-10 tags, use hyphenated compounds: "M4-holes", "L-shape").

RESPOND WITH VALID JSON ONLY (no markdown fences):
{
  "action": "SAVE_NEW",
  "update_index": null,
  "reason": "No similar shape exists",
  "improved_tags": ["bracket", "L-shape", "M4-holes", "medium", "filleted"],
  "improved_description": "L-shaped mounting bracket with 4xM4 corner holes and 2mm fillets"
}"""


def run_memory_curator(ollama_url: str, text_model: str,
                        user_request: str, code: str,
                        existing_memory: list) -> dict:
    if not code:
        return {"action": "SKIP", "update_index": None, "reason": "No code",
                "improved_tags": [], "improved_description": ""}

    llm = get_text_llm(ollama_url, text_model, temperature=0.0)

    mem_lines = ["EXISTING MEMORY (last 15):"]
    for i, entry in enumerate(existing_memory[-15:]):
        tags = ", ".join(entry.get("tags", []))
        req = entry.get("request", "")[:80]
        mem_lines.append(f"  [{i}] {req} | tags: {tags}")

    prompt = f"""{chr(10).join(mem_lines)}

NEW SHAPE:
Request: {user_request}
Code preview: {code[:300].replace(chr(10), ' ')}

Decide: save new, update existing, or skip?"""

    result = llm.invoke([SystemMessage(content=SYSTEM), HumanMessage(content=prompt)])
    raw = result.content if isinstance(result.content, str) else str(result.content)
    raw = re.sub(r"^```[a-z]*\n?", "", raw.strip(), flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw.strip())

    try:
        return json.loads(raw.strip())
    except Exception:
        stop = {"a", "an", "the", "with", "and", "or", "for", "of", "to", "in", "on", "at"}
        tags = [w for w in user_request.lower().split() if w not in stop and len(w) > 2][:8]
        return {"action": "SAVE_NEW", "update_index": None, "reason": "Fallback",
                "improved_tags": tags, "improved_description": user_request}
