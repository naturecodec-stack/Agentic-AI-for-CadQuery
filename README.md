# CadQuery AI Agent

An AI assistant that lives inside [CQ-Editor](https://github.com/CadQuery/CQ-editor) and generates 3D CAD code from plain English descriptions.

**You type:** *"Make an L-shaped bracket with 4 mounting holes and rounded edges"*
**It writes:** Complete, validated CadQuery Python code — loaded directly into your editor.

---

## How It Works

```
You type a description
        │
        ▼
  [Plan]   agent calls plan_shape() — commits to ALL required features
        │
        ▼
  [Skills] searches 27-skill library → loads template if match found
        │
        ▼
  [Code]   writes complete CadQuery Python implementing every planned feature
        │
        ▼
  [Exec]   runs code headlessly to check for errors
        │
    ┌───┴────────────────┐
  FAIL                 SUCCESS
    │                     │
    ▼                     ▼
  [Fix]  reads error    Code loaded into
  and tries again       CQ-Editor editor
  (up to 5 times)
```

The **anti-simplification rule** forces the agent to implement every feature it planned. It cannot write a plain box when you asked for a bracket with holes and fillets.

---

## Project Structure

```
cadquery-ai-agent/
├── skills/                      27 shape templates the AI can load
│   ├── skill_registry.json
│   ├── features/                bracket, gear, pocket, shaft, thread, sweep...
│   ├── assemblies/              bolt, nut, washer, flange, constrained assembly
│   ├── import_export/           STEP import/export, DXF import
│   └── generic/                 fallback for anything not in the library
├── cq_agent_v3_langgraph/       LangGraph ReAct agent
│   ├── agent_graph.py           main entry point — tool-calling agent
│   ├── tools.py                 plan_shape, search_skills, use_skill, execute_cadquery
│   ├── widget.py                CQ-Editor PyQt5 panel
│   ├── graph.py                 sequential fallback pipeline
│   ├── skill_loader.py          loads templates from ../skills/
│   ├── state.py
│   ├── llm.py
│   └── nodes/                   planning, codegen, execute, repair
└── cq_editor_integration/       drop-in files for CQ-Editor
    ├── README.md
    └── widgets/
        └── ai_chat_agent_v3.py
```

---

## Agent Tools

The LLM calls these autonomously during generation:

| Tool | Purpose |
|------|---------|
| `plan_shape` | Lists every feature to build — acts as a contract the agent must honour |
| `search_skills` | Keyword search over the skill library |
| `list_skills` | Shows all 27 available templates |
| `use_skill` | Renders a template with custom parameters |
| `execute_cadquery` | Runs code headlessly — returns SUCCESS or full error traceback |

---

## Skill Library (27 skills)

**Features:** bracket · enclosure · pocket · stepped shaft · shell · revolve · text on face · helix · involute gear · sweep · ISO thread · grid holes · polar holes · counterbore hole · countersink hole · multi-section loft

**Assemblies:** bolt · nut · washer · bolt+nut · flange bolt pattern · plate with bolts · constrained assembly

**Import/Export:** STEP import · STEP/STL/SVG export · DXF import

---

## Setup

### 1. Install dependencies

```bash
pip install langchain-google-genai langgraph langchain-core
```

### 2. Get a Google API key

Get one free at [aistudio.google.com](https://aistudio.google.com)

Copy `.env.example` → `.env` and fill in your key:

```
GOOGLE_API_KEY=your_key_here
MODEL=gemini-2.0-flash
```

Recommended models: `gemini-2.5-pro` (best) · `gemini-2.5-flash` · `gemini-2.0-flash`

### 3. Install the CQ-Editor widget

```
cq_editor_integration/widgets/ai_chat_agent_v3.py
  → CQ-editor/cq_editor/widgets/ai_chat_agent_v3.py
```

See `cq_editor_integration/README.md` for the 3-line edit to `main_window.py`.

### 4. Configure in CQ-Editor

Open the **AI Agent v3** panel → Preferences:

- **Google API Key** — auto-loads from `.env` if present
- **Model** — e.g. `gemini-2.0-flash`
- **Agent Dir** — full path to `cq_agent_v3_langgraph/`
- **Agent Mode** — `tool-calling` (recommended) or `sequential`

---

## Requirements

- Python 3.10+
- CadQuery 2.4+
- CQ-Editor
- `langchain-google-genai`, `langgraph`, `langchain-core`
- Google API key (free tier works)

Optional: `cq-warehouse` — needed for thread, bolt, nut, and washer skills

---

## License

MIT
