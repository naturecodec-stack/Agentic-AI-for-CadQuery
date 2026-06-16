# CadQuery AI Agent

An AI assistant that lives inside [CQ-Editor](https://github.com/CadQuery/CQ-editor) and generates 3D CAD code from plain English descriptions.

**You type:** *"Make an L-shaped bracket with 4 mounting holes and rounded edges"*
**It writes:** Complete, validated CadQuery Python code — loaded directly into your editor.

---

## What's Inside

```
cq_agent_v2/              Sequential pipeline agent (Plan → Skills → Code → Fix)
cq_agent_v3_langgraph/    LangGraph tool-calling agent (smarter, self-directing)
cq_editor_integration/    Files to drop into CQ-Editor
```

### Agent v2 — Sequential Pipeline

Fixed 5-stage pipeline:

```
Plan → Select Skill → Generate Code → Execute → Repair (up to 3x)
```

Simple and predictable. Each stage runs in order every time.

### Agent v3 — LangGraph Tool-Calling

The LLM decides dynamically what to do next using real tools:

| Tool | What it does |
|------|-------------|
| `plan_shape` | Commits to a feature list — the LLM's contract with itself |
| `search_skills` | Searches the 27-skill library by keyword |
| `list_skills` | Lists all available templates |
| `use_skill` | Renders a template with custom parameters |
| `execute_cadquery` | Runs code headlessly, returns SUCCESS or error |

The agent keeps calling `execute_cadquery` until it gets SUCCESS — repairing errors itself without any fixed loop.

---

## Skill Library (27 skills)

Reusable shape templates the AI can load and customize:

**Features:** bracket, enclosure, pocket, stepped shaft, shell, revolve, text on face, helix, gear (involute), sweep, thread, grid holes, polar holes, counterbore hole, countersink hole, multi-section sweep

**Assemblies:** bolt, nut, washer, bolt+nut assembly, flange bolt pattern, plate with bolts, constrained assembly

**Import/Export:** import STEP, export STEP/STL/SVG, import DXF

---

## Setup

### 1. Install dependencies

```bash
# In CQ-Editor's Python environment:
pip install langchain-google-genai langgraph langchain-core
```

### 2. Get a Google API key

Get one free at [aistudio.google.com](https://aistudio.google.com)

Copy `.env.example` to `.env` and fill in your key:

```
GOOGLE_API_KEY=your_key_here
MODEL=gemini-2.0-flash
```

Recommended models (best to good): `gemini-2.5-pro` → `gemini-2.5-flash` → `gemini-2.0-flash`

### 3. Install the CQ-Editor widget

Copy the widget file into CQ-Editor:

```
cq_editor_integration/widgets/ai_chat_agent_v3.py
  → CQ-editor/cq_editor/widgets/ai_chat_agent_v3.py
```

Add 3 lines to `cq_editor/main_window.py`:

```python
# At the top, with other imports:
from .widgets.ai_chat_agent_v3 import AIChatWidget as AIAgentV3Widget

# In prepare_panes(), with other registerComponent calls:
self.registerComponent(
    "ai_agent_v3",
    AIAgentV3Widget(self),
    lambda c: dock(c, "AI Agent v3", self, defaultArea="right"),
)

# In prepare_actions():
self.components["ai_agent_v3"].set_editor(self.components["editor"])
```

### 4. Configure in CQ-Editor

Open the **AI Agent v3** panel → Preferences:

- **Google API Key** — paste your key (auto-loads from `.env` if present)
- **Model** — e.g. `gemini-2.0-flash`
- **Agent Dir** — full path to the `cq_agent_v3_langgraph/` folder
- **Agent Mode** — `tool-calling` (recommended) or `sequential`

---

## How It Works

```
You type a description
        │
        ▼
  [Plan] agent calls plan_shape() — commits to ALL features
        │
        ▼
  [Skills] searches library → loads template if match found
        │
        ▼
  [Code] writes complete CadQuery Python
        │
        ▼
  [Exec] runs code headlessly to check for errors
        │
    ┌───┴────────────────┐
  FAIL                 SUCCESS
    │                     │
    ▼                     ▼
  [Fix] reads error    Code loaded into
  and tries again      CQ-Editor editor
  (up to 5x)
```

The **anti-simplification rule** prevents the agent from writing a plain box when something complex was requested. It must implement every item in its plan.

---

## Project Structure

```
cq_agent_v2/
├── graph.py              LangGraph StateGraph pipeline
├── state.py              AgentState TypedDict
├── llm.py                LLM factory (Google Generative AI)
├── skill_loader.py       Loads skill templates from registry
├── ai_chat_agent.py      CQ-Editor PyQt5 widget (v2)
├── nodes/
│   ├── planning.py       Analyses request, creates build plan
│   ├── skill_selection.py Picks best skill template
│   ├── code_generation.py Generates CadQuery Python
│   └── repair.py         Fixes errors (targeted fix → full rewrite)
└── skills/               27 shape templates
    ├── skill_registry.json
    ├── features/
    ├── assemblies/
    ├── import_export/
    └── generic/

cq_agent_v3_langgraph/
├── agent_graph.py        ReAct tool-calling agent (main entry point)
├── tools.py              LangGraph @tool definitions
├── widget.py             CQ-Editor PyQt5 widget (v3, dual-mode)
├── graph.py              Sequential pipeline (same as v2 but improved)
├── skill_loader.py       Points to cq_agent_v2/skills/ (shared)
├── state.py              AgentState TypedDict
└── nodes/                Improved planning, codegen, repair nodes

cq_editor_integration/
└── widgets/
    └── ai_chat_agent_v3.py   Drop-in widget for CQ-Editor
```

---

## Requirements

- Python 3.10+
- CadQuery 2.4+
- CQ-Editor (for the UI panel)
- `langchain-google-genai`, `langgraph`, `langchain-core`
- Google API key (free tier works)

Optional: `cq-warehouse` for thread, bolt, nut, and washer skills

---

## License

MIT
