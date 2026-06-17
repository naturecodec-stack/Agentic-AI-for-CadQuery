"""
Assembly Decomposer — v5 (local model via Ollama).
Vision model when image provided; text model otherwise.
"""

import base64
import json
import os
import re

from langchain_core.messages import HumanMessage, SystemMessage

from .llm_factory import get_text_llm, get_vision_llm

SYSTEM_WITH_IMAGE = """You are a CAD Assembly Decomposer.

You see an image and a text description.

DECIDE: Is this a SINGLE PART or a MULTI-PART ASSEMBLY?

SINGLE PART: one solid body (may have holes, fillets, pockets, ribs)
ASSEMBLY: multiple distinct solids that exist as separate pieces

RESPOND WITH VALID JSON ONLY (no markdown fences):
{
  "is_assembly": false,
  "part_count": 1,
  "assembly_type": "none",
  "confidence": "high",
  "parts": [
    {
      "name": "main_body",
      "description": "Rectangular plate 80x40x5mm with 4 corner holes",
      "primary_shape": "box",
      "relative_position": "at origin"
    }
  ],
  "assembly_note": ""
}"""

SYSTEM_WITHOUT_IMAGE = """You are a CAD Assembly Decomposer.

You read TEXT to determine if it describes a single part or assembly.

ASSEMBLY keywords: "with lid", "and bolts", "assembly", "two parts", "attach", "connect", "plus"
SINGLE PART keywords: single shape name + adjectives only

RESPOND WITH VALID JSON ONLY (no markdown fences):
{
  "is_assembly": false,
  "part_count": 1,
  "assembly_type": "none",
  "confidence": "high",
  "parts": [
    {
      "name": "main_body",
      "description": "<restate the shape cleanly>",
      "primary_shape": "<box|cylinder|bracket|...>",
      "relative_position": "at origin"
    }
  ],
  "assembly_note": ""
}"""


def run_assembly_decomposer(ollama_url: str, text_model: str, vision_model: str,
                             user_request: str, image_path: str = "") -> dict:
    has_image = bool(image_path and os.path.exists(image_path))

    if has_image:
        llm = get_vision_llm(ollama_url, vision_model, temperature=0.0)
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = os.path.splitext(image_path)[1].lower().lstrip(".")
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                "png": "image/png", "webp": "image/webp"}.get(ext, "image/png")
        content = [
            {"type": "text",
             "text": f"USER REQUEST: {user_request}\n\nSingle part or multi-part assembly?"},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
        ]
        system = SYSTEM_WITH_IMAGE
    else:
        llm = get_text_llm(ollama_url, text_model, temperature=0.0)
        content = [{"type": "text",
                    "text": f"USER REQUEST: {user_request}\n\nSingle part or multi-part assembly?"}]
        system = SYSTEM_WITHOUT_IMAGE

    result = llm.invoke([SystemMessage(content=system), HumanMessage(content=content)])
    raw = result.content if isinstance(result.content, str) else str(result.content)
    raw = re.sub(r"^```[a-z]*\n?", "", raw.strip(), flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw.strip())

    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return {
            "is_assembly": False, "part_count": 1, "assembly_type": "none",
            "confidence": "low",
            "parts": [{"name": "main", "description": user_request,
                       "primary_shape": "unknown", "relative_position": "at origin"}],
            "assembly_note": "",
        }


def format_assembly_context(data: dict) -> str:
    if not data or not data.get("is_assembly"):
        parts = data.get("parts", []) if data else []
        if parts:
            desc = parts[0].get("description", "")
            shape = parts[0].get("primary_shape", "")
            if desc:
                return f"Shape identified as: {shape} — {desc}"
        return ""

    lines = [
        "=== ASSEMBLY DECOMPOSER ===",
        f"MULTI-PART ASSEMBLY: {data.get('part_count', '?')} parts ({data.get('assembly_type', '')})",
        "Parts to build:",
    ]
    for i, part in enumerate(data.get("parts", []), 1):
        lines.append(f"  Part {i} — '{part['name']}': {part.get('description', '?')}")
        lines.append(f"    Position: {part.get('relative_position', 'unknown')}")
    if data.get("assembly_note"):
        lines.append(f"Assembly: {data['assembly_note']}")
    lines.append("Use .union() or MAssembly to combine parts.")
    lines.append("=== BUILD EACH PART THEN COMBINE ===")
    return "\n".join(lines)
