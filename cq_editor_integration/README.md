# CQ-Editor Integration

These files plug the AI Agent v3 panel into an existing CQ-Editor installation.

## Step 1 — Copy the widget

```
widgets/ai_chat_agent_v3.py  →  CQ-editor/cq_editor/widgets/ai_chat_agent_v3.py
```

## Step 2 — Edit main_window.py

In `CQ-editor/cq_editor/main_window.py`:

**Add import** (near other widget imports at the top):
```python
from .widgets.ai_chat_agent_v3 import AIChatWidget as AIAgentV3Widget
```

**Register the panel** (inside `prepare_panes()`):
```python
self.registerComponent(
    "ai_agent_v3",
    AIAgentV3Widget(self),
    lambda c: dock(c, "AI Agent v3", self, defaultArea="right"),
)
```

**Connect the editor** (inside `prepare_actions()`):
```python
self.components["ai_agent_v3"].set_editor(self.components["editor"])
```

## Step 3 — Set the Agent Dir in Preferences

Open the AI Agent v3 panel → Preferences → Agent Dir and set it to the
full path of the `cq_agent_v3_langgraph/` folder from this repo.
