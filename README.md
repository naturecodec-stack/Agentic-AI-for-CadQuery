# CadQuery AI Agent v4

A full agentic AI that lives inside [CQ-Editor](https://github.com/CadQuery/CQ-editor) and generates 3D CAD code from plain English descriptions or reference images.

**You type or attach an image** → AI plans, codes, renders, reviews, and self-corrects → **Working CadQuery code loaded into your editor**

---

## What It Does

```
You → [Memory] → [Plan] → [Code] → [Render] → [Review] → [Approve] → [Save] → CQ-Editor
```

Three AI agents collaborate automatically. You only step in at the final approval.

---

## Key Features

- **Image input** — attach a reference photo and the AI reproduces the exact shape
- **Multi-agent pipeline** — Planner + Coder + Reviewer, each specialised
- **Visual feedback** — renders 3 SVG projections and AI inspects them visually
- **Long-term memory** — remembers shapes across sessions, recalls similar ones automatically
- **Human approval gate** — you approve, recreate, or cancel before code is loaded
- **Self-repair** — coder retries up to 5 times on execution errors
- **Fast mode** — toggle off visual review for instant results on simple shapes

---

## Workflow

```
         YOUR REQUEST + IMAGE
                  │
          [1] MEMORY RECALL        ← searches past shapes for hints
                  │
          [2] PLANNER AGENT        ← extracts exact features from image/text
                  │
          [3] CODER AGENT ◄─────── sees reference image + plan + critique
          (5 retries until SUCCESS)
                  │
          [4] RENDER               ← isometric, front, top SVG projections
                  │
          [5] REVIEWER AGENT       ← compares rendered shape to reference image
                  │
      APPROVED ───┤─── REJECTED (up to 2 loops back to coder)
                  │
      [6] YOU: Approve / Recreate / Cancel
                  │
          [7] SAVE TO MEMORY       ← stored for future recall
                  │
          CODE IN CQ-EDITOR
```

Full documentation: [docs/v4_agentic_workflow.md](docs/v4_agentic_workflow.md)

---

## Project Structure

```
cadquery-ai-agent/
├── docs/
│   └── v4_agentic_workflow.md       Full pipeline explanation
├── skills/                          27 shape templates the AI can load
│   ├── skill_registry.json
│   ├── features/                    bracket, gear, pocket, shaft, thread, sweep...
│   ├── assemblies/                  bolt, nut, washer, flange, constrained assembly
│   ├── import_export/               STEP import/export, DXF import
│   └── generic/                     fallback template
├── cq_agent_v4/                     Full agentic pipeline
│   ├── state.py                     Pipeline state
│   ├── graph.py                     LangGraph StateGraph — 7 nodes
│   ├── widget.py                    CQ-Editor panel with approval UI
│   ├── agents/
│   │   ├── planner.py               Planner agent
│   │   ├── coder.py                 Coder agent (sees reference image)
│   │   └── reviewer.py              Reviewer agent (vision — SVG comparison)
│   ├── tools/
│   │   ├── cadquery_tools.py        execute_cadquery, render_shape
│   │   └── skill_tools.py           search_skills, list_skills, use_skill
│   └── memory/
│       ├── store.py                 recall_similar(), save_shape()
│       └── shapes_memory.json       persistent shape database
└── cq_editor_integration/           Drop-in files for CQ-Editor
    ├── README.md
    └── widgets/
        └── ai_chat_agent_v4.py
```

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

Recommended models: `gemini-2.5-pro` (best quality) · `gemini-2.0-flash` (fastest, free tier)

### 3. Install the CQ-Editor widget

```
cq_editor_integration/widgets/ai_chat_agent_v4.py
  → CQ-editor/cq_editor/widgets/ai_chat_agent_v4.py
```

See `cq_editor_integration/README.md` for the 3-line edit to `main_window.py`.

### 4. Configure in CQ-Editor

Open the **AI Agent v4** panel → Preferences:

| Setting | Description |
|---------|-------------|
| Google API Key | Auto-loads from `.env` if present |
| Model | e.g. `gemini-2.0-flash` |
| Agent Dir | Full path to the `CQ-editor` root folder |
| Visual Review | ON = full pipeline · OFF = fast mode (skip render/review/approval) |

---

## Agent Tools

| Tool | Used by | Purpose |
|------|---------|---------|
| `plan_shape` | Planner | Commits to feature list — contract the coder must honour |
| `search_skills` | Coder | Keyword search over the skill library |
| `list_skills` | Coder | Shows all 27 available templates |
| `use_skill` | Coder | Renders a template with custom parameters |
| `execute_cadquery` | Coder | Runs code headlessly — returns SUCCESS or full error |
| `render_shape` | Graph | Exports 3 SVG projections for visual review |

---

## Skill Library (59 skills)

**Basic shapes:** sphere · cone · frustum · torus · hex prism · ring · pin

**Features:** bracket · enclosure · pocket · stepped shaft · shell · revolve · text on face · helix · involute gear · sweep · ISO thread · grid holes · polar holes · counterbore hole · countersink hole · multi-section loft

**Structural:** rib · boss · snap fit · T-slot extrusion · U/C/L channel · living hinge

**Mechanical:** pulley · pipe flange · hook · handle · cable clip

**Splines:** spline path sweep · spline profile (teardrop/leaf/blob/star) · spline surface (vase/hourglass) · NACA airfoil · spline transition (round→square)

**Gears (cq_gears):** helical gear · bevel gear · ring gear · worm gear set · rack gear · herringbone gear · planetary gear set

**Assemblies (cadquery-massembly):** MAssembly constrained assembly · bolt · nut · washer · bolt+nut · flange bolt pattern · plate with bolts

**Electronics:** PCB standoff · heat sink

**Assemblies:** bolt · nut · washer · bolt+nut · flange bolt pattern · plate with bolts · constrained assembly

**Import/Export:** STEP import · STEP/STL/SVG export · DXF import

---

## Requirements

- Python 3.10+
- CadQuery 2.4+
- CQ-Editor (bundled Python 3.12)
- `langchain-google-genai`, `langgraph`, `langchain-core`
- Google API key (free tier works for `gemini-2.0-flash`)
- PyQt5 (bundled with CQ-Editor — used for SVG rendering)

Optional: `cq-warehouse` — needed for thread, bolt, nut, and washer skills

---

## License

MIT
