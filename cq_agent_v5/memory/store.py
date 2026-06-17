"""
Long-term memory: persists successful shapes to a JSON file.
Survives across CQ-Editor restarts.
"""

import json
import os

_MEMORY_FILE = os.path.join(os.path.dirname(__file__), "shapes_memory.json")


def _load() -> list:
    if not os.path.exists(_MEMORY_FILE):
        return []
    try:
        with open(_MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save(shapes: list) -> None:
    os.makedirs(os.path.dirname(_MEMORY_FILE), exist_ok=True)
    with open(_MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(shapes, f, indent=2, ensure_ascii=False)


def recall_similar(query: str, top_n: int = 3) -> list:
    """Return up to top_n past shapes whose request overlaps with query."""
    shapes = _load()
    if not shapes:
        return []

    query_words = set(query.lower().split())

    scored = []
    for shape in shapes:
        req_words = set(shape.get("request", "").lower().split())
        overlap = len(query_words & req_words)
        if overlap > 0:
            scored.append((overlap, shape))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:top_n]]


def save_shape(request: str, code: str, tags: list = None) -> None:
    """Save a successfully generated shape to long-term memory."""
    shapes = _load()

    entry = {
        "request": request,
        "code": code,
        "tags": tags or [],
    }

    # Remove duplicate if same request already saved
    shapes = [s for s in shapes if s.get("request", "") != request]
    shapes.insert(0, entry)

    # Keep last 100 shapes
    _save(shapes[:100])


def update_shape(index: int, request: str, code: str, tags: list = None) -> None:
    """Update an existing memory entry by its position index in the full list."""
    shapes = _load()
    full_len = len(shapes)
    # Curator receives last-15 slice; translate index back to full list
    offset = max(0, full_len - 15)
    real_idx = offset + index
    if 0 <= real_idx < full_len:
        shapes[real_idx] = {"request": request, "code": code, "tags": tags or []}
        _save(shapes)
    else:
        # Index out of range — fall back to save_new
        save_shape(request=request, code=code, tags=tags)


def all_shapes() -> list:
    return _load()
