# CadQuery AI Agent v4 — End-to-End Project Documentation

## Table of Contents

1. [What This Project Is](#1-what-this-project-is)
2. [Why Agentic AI for CAD?](#2-why-agentic-ai-for-cad)
3. [System Architecture](#3-system-architecture)
4. [How the Pipeline Works — Step by Step](#4-how-the-pipeline-works--step-by-step)
5. [Each Agent — Role, Inputs, Outputs](#5-each-agent--role-inputs-outputs)
6. [How Agents Communicate](#6-how-agents-communicate)
7. [The Skill Library](#7-the-skill-library)
8. [Memory System](#8-memory-system)
9. [Decision Points and Routing Logic](#9-decision-points-and-routing-logic)
10. [Fast Mode vs Full Mode](#10-fast-mode-vs-full-mode)
11. [The Human Approval Gate](#11-the-human-approval-gate)
12. [A Complete Example — End to End](#12-a-complete-example--end-to-end)
13. [Technology Stack](#13-technology-stack)
14. [File-by-File Reference](#14-file-by-file-reference)

---

## 1. What This Project Is

**CadQuery AI Agent v4** is an agentic AI system that lives inside [CQ-Editor](https://github.com/CadQuery/CQ-editor) — the open-source CadQuery GUI — and generates 3D CAD Python code from plain English descriptions or reference images.

You describe what you want to build (or attach a photo of it), and the AI:
- Extracts dimensions and detects whether it is a single part or an assembly
- Plans an exact feature list
- Selects the best starting template from 71 pre-built shapes
- Writes and validates CadQuery Python code
- Checks the code logically matches the plan
- Renders the shape in 3 views and reviews it visually
- Validates proportions against your reference image
- Shows you the result for approval
- Saves the shape to long-term memory for future reuse

The generated code is loaded directly into CQ-Editor — ready to run, render, or export.

---

## 2. Why Agentic AI for CAD?

A single LLM call is not enough for 3D CAD code generation. Here is why:

| Problem | Single LLM | Agentic AI v4 |
|---------|-----------|---------------|
| Dimensions from image | Guesses randomly | Dimension Extractor reads proportions |
| Multi-part assemblies | Merges everything into one blob | Assembly Decomposer splits into parts |
| Skill template selection | Random keyword search | Skill Selector reads all 71 skills and plans together |
| Code matches the plan? | No verification | Code Critic checks before rendering |
| Hard-to-fix CadQuery errors | Retries same broken approach | Repair Specialist has error pattern library |
| Proportions correct? | No visual check | Dimension Validator compares SVG vs image |
| Shape looks right? | No visual check | Reviewer sees rendered SVG and judges |
| Duplicate memory? | Saves everything blindly | Memory Curator deduplicates and improves tags |
| Remembers past shapes? | No | Long-term memory with similarity search |

The difference between a chatbot and an agentic system:

```
Chatbot:    You ask → AI answers → Done

Agent v4:   You ask
              → AI extracts dimensions   (Agent 1)
              → AI detects parts         (Agent 2)
              → AI plans features        (Agent 3)
              → AI selects templates     (Agent 4)
              → AI writes + tests code   (Agent 5)
              → AI critiques its code    (Agent 6)
              → AI repairs hard errors   (Agent 7, if needed)
              → AI renders shape         (pipeline step)
              → AI validates proportions (Agent 8)
              → AI reviews visually      (Agent 9)
              → You approve
              → AI curates memory        (Agent 10)
              → Code loaded into editor
```

Each agent is specialised. Specialisation means each agent has a focused system prompt, sees only the information it needs, and produces structured output that the next agent depends on.

---

## 3. System Architecture

### 3.1 Core Framework

The pipeline is built on **LangGraph** — a stateful graph framework for multi-agent workflows:

- **StateGraph** — defines the pipeline as a directed graph of nodes (agents + operations)
- **AgentState** — a typed dictionary that holds all pipeline data as it flows through nodes
- **MemorySaver** — checkpoint system that saves graph state so the pipeline can pause and resume
- **interrupt()** — pauses the graph at the human approval node and waits for user input
- **stream\_mode="updates"** — the widget streams each node's output as it completes, updating the UI in real time

### 3.2 The 13 Nodes

```
Node name              Type        Description
─────────────────────────────────────────────────────────────────────
recall_memory          operation   Search memory JSON for similar past shapes
dimension_extractor    LLM agent   Extract dimensions from image or text
assembly_decomposer    LLM agent   Detect single part vs multi-part assembly
plan                   LLM agent   Produce exact feature plan
skill_selector         LLM agent   Pick best 1-3 skill templates
code                   LLM agent   Write + validate CadQuery code (5 retries)
code_critic            LLM agent   Check plan vs code logic (post-execution)
repair_specialist      LLM agent   Fix hard errors using pattern library
render                 operation   Export 3 SVG projections headlessly
dimension_validator    LLM agent   Compare SVG proportions vs reference image
review                 LLM agent   Visual approval/rejection of rendered shape
human_approval         interrupt   Pause for user input (approve/recreate/cancel)
save_memory            operation   Memory Curator + write to JSON store
```

### 3.3 The AgentState

All data flows through a single shared state dict. Key fields:

```python
# Input
user_request: str          # The user's text description
image_path: str            # Path to reference image (if any)
api_key: str               # Google API key
model: str                 # e.g. "gemini-2.0-flash"
visual_review: bool        # True = full mode, False = fast mode

# Memory
recalled_shapes: list      # Similar past shapes from memory store

# Extraction
dimension_hints: dict      # {overall: {width_mm, height_mm, depth_mm}, features: [...]}
is_assembly: bool          # True if multi-part
sub_shapes: list           # List of part descriptions if assembly

# Planning
plan: str                  # Exact feature list from planner
skill_recommendations: list  # [{name, reason, priority}, ...]

# Coding
generated_code: str        # Latest CadQuery code
execution_success: bool    # Did execute_cadquery return SUCCESS?
execution_error: str       # Last error message if failed
repair_attempts: int       # How many times code_node has run
repair_used: bool          # True if repair_specialist was activated

# Code review
code_critic_feedback: str  # Issues found by code_critic
critic_loops: int          # How many times critic has sent back to coder

# Visual pipeline
svg_paths: dict            # {"isometric": path, "front": path, "top": path}
dimension_validation: dict  # Proportion comparison result
visual_critique: str       # Reviewer's written assessment
visual_loops: int          # How many times reviewer has sent back to coder
shape_approved: bool       # True if reviewer approved

# Human gate
human_approved: bool       # True if user clicked Approve
human_feedback: str        # User's typed feedback (if rejected)

# Output
final_code: str            # Code sent to CQ-Editor
final_message: str         # Status message shown in UI
```

---

## 4. How the Pipeline Works — Step by Step

Here is what happens from the moment you press **Generate**:

```
1. Widget reads: user text, image path, API key, model, visual_review setting
2. Widget starts a background thread running _run_agent()
3. _run_agent() calls graph.stream() — starts the LangGraph pipeline
4. Each node runs in sequence, streaming updates back to the widget
5. Widget receives updates chunk by chunk and updates the UI (step indicator, status, log)
6. When human_approval node runs: graph pauses via interrupt()
7. Widget shows the approval panel (SVG preview + buttons)
8. User clicks Approve / Recreate / Cancel
9. Widget resumes the graph with the user's response
10. save_memory node runs, code is returned
11. Widget emits final_code signal → CQ-Editor loads the code
```

The graph never blocks the UI because it runs in a background `threading.Thread`. The `_Bridge` object uses Qt signals to safely pass data from the background thread to the UI thread.

---

## 5. Each Agent — Role, Inputs, Outputs

---

### Agent 1 — Dimension Extractor

**File:** `cq_agent_v4/agents/dimension_extractor.py`  
**Runs:** Always, immediately after memory recall  
**Model call:** 1 LLM call

**Problem it solves:**  
Without this agent, the planner and coder have to guess dimensions. They tend to pick round numbers (100×50×20mm) that bear no relation to the actual shape. This agent grounds the pipeline in real measurements before planning begins.

**Mode A — WITH reference image:**
- Sends the image to the vision LLM
- Instructs it to measure the overall width:height:depth ratio visually
- Counts every visible feature: holes, ribs, slots, fillets, steps, pockets
- Estimates absolute mm by asking "what would this part be in real life?"  
  (A bolt hole looks like M4–M8; a machine bracket looks like 50–150mm wide)
- Records feature positions: "4 holes at corners, ~10% from each edge"
- Reports confidence per measurement: high / medium / low

**Mode B — WITHOUT reference image:**
- Parses the text request for explicit numbers: "80mm", "M4 holes", "3mm thick"
- Applies engineering standards:
  - M3 = 3mm, M4 = 4mm, M5 = 5mm, M6 = 6mm, M8 = 8mm
  - Standard PCB = 60×40mm, Arduino = 68×53mm, Raspberry Pi = 85×56mm
  - Standard bracket thickness = 4–6mm
  - Fillet radius = 1–3mm (small parts), 3–8mm (large parts)
- Infers missing dimensions from shape type:
  - "small bracket" → ~80×40×5mm
  - "enclosure" → ~100×60×40mm
  - "gear" → module=1–2, 20–40 teeth
- Tags each dimension as `explicit` (from user text) or `inferred` (estimated)

**Output format:**
```json
{
  "has_image": true,
  "overall": {
    "width_mm": 80,
    "height_mm": 40,
    "depth_mm": 5,
    "confidence": "medium"
  },
  "features": [
    {
      "type": "hole",
      "count": 4,
      "size_mm": 4.5,
      "position": "corners, ~8mm from each edge",
      "source": "inferred"
    },
    {
      "type": "fillet",
      "size_mm": 2,
      "position": "all vertical edges",
      "source": "inferred"
    }
  ],
  "shape_type": "bracket"
}
```

**What receives this output:** Planner and Coder both receive a formatted text block:
```
=== DIMENSION EXTRACTOR OUTPUT ===
Overall size: 80mm (W) × 40mm (H) × 5mm (D)  [confidence: medium]
Shape type: bracket
Features detected:
  - 4x hole, size=4.5mm, at: corners, ~8mm from each edge [inferred]
  - 1x fillet, size=2mm, at: all vertical edges [inferred]
=== USE THESE DIMENSIONS IN YOUR PLAN ===
```

---

### Agent 2 — Assembly Decomposer

**File:** `cq_agent_v4/agents/assembly_decomposer.py`  
**Runs:** Always, after dimension extraction  
**Model call:** 1 LLM call

**Problem it solves:**  
When a user attaches an image of a "box with a lid" or types "motor mount with bearings", a single-pass coder tries to build it all as one solid — producing wrong geometry. This agent decides early whether to treat it as one shape or multiple.

**Single part detection (most common):**  
A bracket, gear, shaft, PCB standoff, enclosure — one solid body with features.  
→ Passes through cleanly with no added overhead.

**Assembly detection:**  
- Visual cues: visible gap/joint lines between components, different materials/colours, "exploded view" style gaps
- Text cues: "with lid", "and bolts", "housing assembly", "two parts", "attach", "connect"

**When assembly detected:**
- Names each part: "base\_plate", "cover", "standoff\_x4"
- Describes each part individually: "Rectangular plate 100×60×5mm with 4 corner M4 holes"
- Identifies assembly type: bolted / press-fit / snap-fit / adhesive / constrained
- Provides relative positioning: "cover sits on top of base, aligned at edges"

**Output example (assembly):**
```json
{
  "is_assembly": true,
  "part_count": 2,
  "assembly_type": "snap_fit",
  "parts": [
    {
      "name": "base",
      "description": "Rectangular box 100×60×30mm, open top, 2mm wall thickness",
      "primary_shape": "shell",
      "relative_position": "at origin"
    },
    {
      "name": "lid",
      "description": "Flat plate 100×60×3mm with snap-fit tabs on 2 short edges",
      "primary_shape": "box",
      "relative_position": "placed on top of base, Z offset = 30mm"
    }
  ],
  "assembly_note": "Use .union() or MAssembly to combine after building each part"
}
```

**What receives this output:** Planner receives the full assembly context as a text block injected into its prompt. The planner then plans how to build all parts and assemble them.

---

### Agent 3 — Planner

**File:** `cq_agent_v4/agents/planner.py`  
**Runs:** Always, after assembly decomposition  
**Model call:** 1 LLM agent (ReAct loop with `plan_shape` tool)

**Problem it solves:**  
If the coder reads just the raw user text, it tends to interpret it loosely and omit or add features. The planner forces an explicit, committed feature list before any code is written. The plan is a contract.

**What the planner receives:**
- User request (text)
- Reference image (if provided)
- Dimension hints from Extractor (structured sizes)
- Assembly context from Decomposer (part descriptions)
- Similar past shapes from memory (for context)

**Rules the planner follows:**
- If image provided → image is the PRIMARY specification. Text request is secondary.
- Describe ONLY what is visible in the image — no invented features
- Be exact: not "some holes" but "4 circular holes, M4 (4.5mm diameter), at corners 10mm from each edge"
- Use the extracted dimensions as the starting point — do not ignore them
- Call `plan_shape(features)` tool to commit the plan formally

**Output example:**
```
Plan:
- Main body: box 80mm (W) × 40mm (H) × 5mm (D)
- 4 holes at corners: M4 counterbore, clearance dia 4.5mm, counterbore dia 8mm, depth 3mm
- Rectangular pocket on top face: 50mm × 20mm × 2mm deep, centred
- Fillet all vertical edges: 2mm radius
- show_object(result) at end
```

This plan is stored in `state["plan"]` and passed to the Skill Selector and Coder.

---

### Agent 4 — Skill Selector

**File:** `cq_agent_v4/agents/skill_selector.py`  
**Runs:** Always, after planning  
**Model call:** 1 LLM call

**Problem it solves:**  
The coder has 71 skill templates available but searches them by keyword matching — which can miss the right template or pick an irrelevant one. The Skill Selector reads the full plan holistically and picks the best match.

**What it receives:**
- The complete feature plan (text)
- The full `skill_registry.json` with name + description for all 71 skills

**How it picks:**
- Reads the plan and identifies the PRIMARY shape (what the thing fundamentally is)
- Finds the skill that best matches the primary shape → priority 1
- Identifies any secondary features with dedicated templates → priority 2, 3
- Only recommends skills that are genuinely relevant — wrong recommendation is worse than none
- Maximum 3 skills recommended

**Output example:**
```json
{
  "selected": [
    {
      "name": "bracket",
      "reason": "Plan describes an L-shaped mounting bracket — this is the primary shape",
      "priority": 1
    },
    {
      "name": "counterbore_hole",
      "reason": "Plan specifies M4 counterbore holes at corners",
      "priority": 2
    }
  ]
}
```

**What the coder receives:**
```
=== SKILL SELECTOR: RECOMMENDED TEMPLATES ===
Start your code from these templates (in priority order):
  [1] use_skill('bracket', ...) — Plan describes an L-shaped mounting bracket
  [2] use_skill('counterbore_hole', ...) — Plan specifies M4 counterbore holes at corners
Call use_skill() for the priority-1 skill first, then extend/modify.
=== USE THE RECOMMENDED SKILL AS YOUR STARTING POINT ===
```

---

### Agent 5 — Coder

**File:** `cq_agent_v4/agents/coder.py`  
**Runs:** Always, after skill selection. Also re-runs when: Code Critic sends back issues, Reviewer rejects, Human clicks Recreate  
**Model call:** 1 LLM agent (ReAct loop with 4 tools)

**Problem it solves:**  
This is the core generator. Writes CadQuery Python code step by step, runs it to validate, fixes errors, and retries.

**What the coder receives:**
- Feature plan (the contract to implement)
- Skill recommendations (which templates to use as base)
- Dimension hints (exact sizes to use in code)
- Reference image (sees target shape directly)
- Code Critic feedback (if being sent back for correction)
- Visual critique from reviewer (if looping after rejection)
- Past similar code from memory (for reference)

**PRIME DIRECTIVE:**  
> If a reference image is provided, your code must reproduce that EXACT shape. The image overrides everything else. Do not simplify, do not add features not in the image.

**Self-repair loop:**
```
1. Calls use_skill(name, params) — renders best template as starting code
2. Modifies template code to implement ALL features from plan
3. Calls execute_cadquery(code) to test
4. If SUCCESS → done
5. If ERROR → reads exact error message, identifies root cause, fixes code
6. Go to step 3
7. Repeat up to 5 times maximum
```

**Tools available:**

| Tool | What it does |
|------|-------------|
| `search_skills(query)` | Keyword search over 71 templates |
| `list_skills()` | Returns all 71 skill names + descriptions |
| `use_skill(name, params_json)` | Renders a template with custom parameters as starting Python code |
| `execute_cadquery(code)` | Runs code in a subprocess — returns `SUCCESS` or full error traceback |

**Output:** `generated_code` (the validated Python code), `execution_success` (bool), `execution_error` (last error if failed)

---

### Agent 6 — Code Critic

**File:** `cq_agent_v4/agents/code_critic.py`  
**Runs:** After every successful code execution, before rendering  
**Model call:** 1 LLM call

**Problem it solves:**  
The Coder's self-repair loop only catches **syntax errors and runtime crashes**. It cannot detect that the code runs fine but produces the wrong shape. Example: code runs successfully but draws a plain box when the plan called for a hollow shell with 4 holes.

**What it checks:**
- Feature counts: "plan says 4 holes but code has only 2 `pushPoints`"
- Missing features: "plan mentions fillet, no `.fillet()` call in code"
- Wrong dimensions: "plan says 80mm wide, code has `box(40, ...)`"
- Wrong shape type: "plan says hollow/shell, code is solid"
- Wrong hole type: "plan says countersink, code uses plain `.hole()`"
- Wrong axis: "plan says vertical cylinder, code extrudes on XZ not XY"
- Missing `show_object(result)` at end

**What it does NOT flag:**
- Variable naming style
- Comment presence or absence
- Import ordering
- Minor dimension estimates when no exact size was specified

**If issues found:**
- Formats a structured feedback block with numbered issues and corrections
- Sends back to Coder with `code_critic_feedback` injected into the prompt
- Coder rewrites targeting all flagged issues
- This loop runs **at most once** — critic gets one correction shot

**If no issues:** pipeline continues to render.

**Output example when issues found:**
```
=== CODE CRITIC: PLAN vs CODE MISMATCH ===
Severity: critical
Issues found:
  ISSUE: Plan specifies 4 corner holes but code only has pushPoints([(20,10),(-20,10)])
  ISSUE: Plan mentions filleted edges but no .fillet() call present
Required corrections:
  FIX: Add all 4 corner positions: .pushPoints([(35,15),(-35,15),(35,-15),(-35,-15)])
  FIX: Add before show_object: result = result.edges('|Z').fillet(2)
=== REWRITE CODE TO FIX ALL ISSUES ABOVE ===
```

---

### Agent 7 — Repair Specialist

**File:** `cq_agent_v4/agents/repair_specialist.py`  
**Runs:** Only when Coder exhausts all 5 retries and still fails  
**Model call:** 1 LLM call

**Problem it solves:**  
The Coder's self-repair is general-purpose. When it faces a hard CadQuery geometry error (like `StdFail_NotDone` or a failed fillet), it often retries with slight variations that all fail for the same root cause. The Repair Specialist has a focused system prompt built around known CadQuery error patterns.

**Error pattern library:**

| Error | Root Cause | Fix |
|-------|-----------|-----|
| `StdFail_NotDone` / `BRep_Builder` | Shape construction failed at kernel level | Reduce sweep profile, check loft wire counts, add `.clean()` |
| `NullPointerException` / `AttributeError: NoneType` | Empty selection (`.faces(">Z")` returned nothing) | Try alternate selectors, split into variables |
| `Cannot add edge to wire` | Sketch curves don't connect at endpoints | Use `.close()`, replace with `rect()` / `circle()` |
| `Fillet failed` / `BRepFilletAPI` | Fillet radius exceeds edge geometry | Reduce radius, use `\|Z` edge filter, wrap in try/except |
| `could not find a face` / `ValueError` | Selector string returned empty | Use positional: `.faces()[0]`, `.faces()[-1]` |
| `Shape is null` | Boolean op on non-overlapping shapes | Translate shape before boolean operation |
| `ImportError` | External library not installed | Replace with pure CadQuery equivalent |
| `ZeroDivisionError` | Division by zero in math | Add guards: `max(x, 1e-10)` |

**Process:**
1. Identifies root cause from error message
2. Applies the appropriate fix from the pattern library
3. If pattern not recognised: tries a simpler alternative implementation
4. Fixed code is validated with `execute_cadquery` before passing on

---

### Agent 8 — Dimension Validator

**File:** `cq_agent_v4/agents/dimension_validator.py`  
**Runs:** After render, only meaningful when a reference image is provided  
**Model call:** 1 LLM call (vision)

**Problem it solves:**  
The Reviewer judges whether the shape has the right features. But even if all features are present, the shape might be the wrong proportions — e.g. 3:1 width:height when the reference shows 2:1. A reviewer looking at "does it have 4 holes?" might miss "it's the wrong aspect ratio". This agent focuses purely on numbers.

**What it measures:**
- Overall width:height ratio in the front/isometric view
- Relative feature sizes (hole diameter vs body width)
- Depth vs width ratio from isometric view
- Spacing between features vs body size

**How it measures without a ruler:**
- Compares pixel proportions at key points in both images
- Reports as ratios, not absolute mm (SVG has no scale)
- If reference width is 2× its height, generated should also be 2:1

**Output when mismatch detected:**
```json
{
  "proportions_match": false,
  "ref_width_height": 2.1,
  "gen_width_height": 3.4,
  "corrections": [
    "Shape is ~60% too wide relative to height — reduce width or increase height",
    "Holes appear ~25% too small relative to body — increase hole diameter"
  ],
  "confidence": "medium"
}
```

**What receives this:** The Reviewer agent receives the dimension corrections as an additional context block, so it can specifically flag proportion issues alongside feature issues.

---

### Agent 9 — Reviewer

**File:** `cq_agent_v4/agents/reviewer.py`  
**Runs:** After render + dimension validation, in full mode only  
**Model call:** 1 LLM call (vision)

**Problem it solves:**  
Without a visual reviewer, the pipeline would need a human to judge every generation. The Reviewer sees the actual rendered shape and compares it to the target.

**What it sees:**
- Your original reference image (placed first in the prompt so it's the target to match)
- All 3 SVG projection images (isometric, front, top) of the generated shape
- The feature plan
- Dimension corrections from the validator

**How SVGs are sent to the LLM:**
CadQuery SVG files are rendered to PNG using PyQt5's `QSvgRenderer` (no external dependencies needed — PyQt5 is bundled with CQ-Editor). The PNG is then base64-encoded and sent in the multimodal message content.

**Decision:**

`APPROVED` → pipeline proceeds to human approval gate

`REJECTED` + bullet list of specific differences → critique stored in `visual_critique`, pipeline loops back to Coder

**Visual loop limit:** Maximum 2 rejections before forcing human approval regardless. This prevents infinite loops.

**Example rejection:**
```
REJECTED
- Reference shows a hollow shell, generated shape is solid (no shell operation)
- 4 corner holes visible in reference, none present in generated shape
- Shape is approximately 40% too wide compared to reference proportions
```

---

### Agent 10 — Memory Curator

**File:** `cq_agent_v4/agents/memory_curator.py`  
**Runs:** In save\_memory node, before writing to disk  
**Model call:** 1 LLM call

**Problem it solves:**  
Without curation, memory fills up with duplicates and poorly-tagged entries. A shape saved as `["bracket", "with", "holes", "and"]` is hard to recall later. This agent acts as a quality gate before every save.

**What it does:**
1. Reviews the last 15 memory entries for similar shapes
2. Decides: SAVE\_NEW / UPDATE\_EXISTING / SKIP
3. Generates semantically meaningful tags

**Decision logic:**
- `SAVE_NEW` — no similar shape exists (different type, different features, or different size)
- `UPDATE_EXISTING` — same shape type and main features, but this version has better/corrected code
- `SKIP` — nearly identical to an existing entry (same request, same features, similar code)

**Tag quality improvement:**

| Without curator | With curator |
|----------------|--------------|
| `["bracket", "with", "M4", "holes", "and", "fillet"]` | `["bracket", "L-shape", "mounting", "M4-holes", "medium", "filleted"]` |
| `["box", "with", "lid"]` | `["enclosure", "snap-fit", "lid", "electronics", "100x60x40"]` |
| `["gear", "20", "teeth"]` | `["gear", "spur", "involute", "20-teeth", "module-2", "mechanical"]` |

Good tags improve future recall accuracy because `recall_similar()` does word-overlap scoring.

---

## 6. How Agents Communicate

Agents do not call each other directly. They communicate through the shared **AgentState** dictionary that flows through the LangGraph nodes.

```
Node A runs → writes to state["field_name"]
Node B runs → reads state["field_name"]
```

**Key data flows:**

```
dimension_extractor → writes: state["dimension_hints"]
                    → read by: plan_node, code_node

assembly_decomposer → writes: state["is_assembly"], state["sub_shapes"]
                    → read by: plan_node (assembly context formatted from sub_shapes)

plan_node          → writes: state["plan"]
                    → read by: skill_selector_node, code_node, code_critic_node, review_node

skill_selector     → writes: state["skill_recommendations"]
                    → read by: code_node

code_node          → writes: state["generated_code"], state["execution_success"],
                             state["execution_error"], state["repair_attempts"]
                    → read by: code_critic_node, repair_specialist_node, render_node,
                               human_approval_node, save_memory_node

code_critic_node   → writes: state["code_critic_feedback"], state["critic_loops"]
                    → read by: code_node (on next iteration)

repair_specialist  → writes: state["generated_code"], state["execution_success"],
                             state["repair_used"]
                    → read by: render_node

render_node        → writes: state["svg_paths"]
                    → read by: dimension_validator_node, review_node, human_approval_node

dimension_validator → writes: state["dimension_validation"]
                    → read by: review_node (as extra_context)

review_node        → writes: state["shape_approved"], state["visual_critique"],
                             state["visual_loops"]
                    → read by: human_approval_node, code_node (critique on loop)

human_approval     → writes: state["human_approved"], state["human_feedback"],
                             state["visual_critique"] (updated with rejection reason)
                    → read by: route_after_human (routing), code_node (on recreate)
```

---

## 7. The Skill Library

The skill library is 71 pre-built CadQuery shape templates, indexed in `skills/skill_registry.json`.

### Structure of a Skill File

```python
# skills/features/bracket.py

NAME = "bracket"
DESCRIPTION = "L-shaped mounting bracket with configurable width, height, depth and flange size"
PARAMETERS = {
    "width":       {"type": "float", "default": 80.0, "unit": "mm"},
    "height":      {"type": "float", "default": 60.0, "unit": "mm"},
    "depth":       {"type": "float", "default": 40.0, "unit": "mm"},
    "thickness":   {"type": "float", "default": 5.0,  "unit": "mm"},
    "fillet_r":    {"type": "float", "default": 3.0,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

w = {width}
h = {height}
d = {depth}
t = {thickness}
r = {fillet_r}

base  = cq.Workplane("XY").box(w, d, t)
wall  = cq.Workplane("XZ").box(w, t, h).translate((0, 0, t))
result = base.union(wall)
if r > 0:
    result = result.edges("|Y").fillet(r)
show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(**{k: params.get(k, v["default"]) for k, v in PARAMETERS.items()})
```

### How the Coder Uses Skills

1. Skill Selector recommends `bracket` with priority 1
2. Coder calls `use_skill("bracket", {"width": 80, "height": 40, "thickness": 5})`
3. Tool returns the rendered Python code string
4. Coder reads the code, extends it to add holes, pockets, threads, etc.
5. Calls `execute_cadquery` to validate
6. Iterates until SUCCESS

### Skill Categories (71 total)

| Category | Skills |
|----------|--------|
| Basic shapes | sphere, cone, torus, hex prism, ring, pin, ellipse, wedge, partial cylinder |
| Features | bracket, enclosure, pocket, stepped shaft, shell, revolve, text on face, helix, involute gear, sweep, ISO thread, grid holes, polar holes, counterbore hole, countersink hole, loft |
| Structural | rib, boss, snap fit, T-slot, channel, living hinge |
| Mechanical | pulley, pipe flange, hook, handle, cable clip |
| Splines | spline path sweep, spline profile, spline surface, NACA airfoil, spline transition |
| 2D primitives | bezier profile, offset profile, slot plate |
| Arrays | rectangular array, polar array, mirror body, angled feature |
| Compound | lidded box, boolean intersection |
| Gears | helical, bevel, ring, worm set, rack, herringbone, planetary |
| Assemblies | MAssembly, bolt, nut, washer, bolt+nut, flange bolt pattern, plate with bolts |
| Electronics | PCB standoff, heat sink |
| Import/Export | STEP import, STEP/STL/SVG export, DXF import |

---

## 8. Memory System

### Storage

All shapes are stored in `cq_agent_v4/memory/shapes_memory.json`:

```json
[
  {
    "request": "L-shaped aluminum mounting bracket with 4×M4 corner holes and 2mm fillets",
    "code": "import cadquery as cq\n\nw = 80\n...",
    "tags": ["bracket", "L-shape", "mounting", "M4-holes", "medium", "filleted"]
  }
]
```

Maximum 100 entries. Newest first. Updated by the Memory Curator on every save.

### Recall Algorithm

`recall_similar(query, top_n=3)` does word-overlap scoring:

```python
query_words = set("mounting bracket with holes".split())
# → {"mounting", "bracket", "with", "holes"}

for shape in memory:
    req_words = set(shape["request"].split())
    overlap = len(query_words & req_words)
    # "L-shaped mounting bracket..." → overlap=2 (mounting, bracket)
    # "PCB standoff..." → overlap=0
```

Returns the top-N shapes by overlap score. These are passed to the Planner and Coder as context hints.

### Memory Curation (Agent 10)

Before saving, the curator receives the last 15 memory entries and the new shape. It decides:

- **SAVE\_NEW:** write a new entry at position 0
- **UPDATE\_EXISTING:** replace an existing entry at a specific index
- **SKIP:** do nothing (duplicate detected)

The `update_shape(index)` function in `store.py` translates the curator's 0-based index (into the last-15 slice) back to the real position in the full memory file.

---

## 9. Decision Points and Routing Logic

The LangGraph graph has 6 conditional routing functions. Here is each one explained:

### route\_after\_code\_exec
```
code_node → code_critic   (if execution_success=True OR code exists)
code_node → repair_specialist  (if execution_success=False AND code is empty)
```
If the coder produced some code but it failed: Code Critic still runs (the critic can sometimes spot why).  
If the coder produced nothing at all: skip Critic, go straight to Repair Specialist.

### route\_after\_code\_critic
```
code_critic → code          (if issues_found AND critic_loops <= 1)
code_critic → render        (if no issues AND visual_review=True)
code_critic → save_memory   (if no issues AND visual_review=False)
```
The critic gets exactly one correction shot (critic\_loops max = 1). After that, it passes through regardless of whether issues were found — to avoid blocking the pipeline forever.

### route\_after\_repair
```
repair_specialist → render       (if visual_review=True)
repair_specialist → save_memory  (if visual_review=False)
```
After repair, the pipeline continues normally. The repaired code may or may not be correct — if it's wrong, the Reviewer will catch it.

### route\_after\_review
```
review_node → human_approval   (if shape_approved=True OR visual_loops >= 2)
review_node → code             (if shape_approved=False AND visual_loops < 2)
```
The visual loop runs maximum 2 times. If the reviewer rejects twice, human approval is forced anyway — so the user is never blocked forever by a failing visual loop.

### route\_after\_human
```
human_approval → save_memory   (if human_approved=True)
human_approval → save_memory   (if human_feedback="CANCELLED")
human_approval → code          (if human_approved=False, user clicked Recreate)
```
Cancel exits cleanly without saving. Recreate sends the human's feedback text back to the Coder with "HUMAN REJECTED — try a completely different approach."

---

## 10. Fast Mode vs Full Mode

Fast mode skips the render/review/approval stages for quick results on simple shapes.

| Stage | Full Mode | Fast Mode | Why skipped in fast? |
|-------|-----------|-----------|----------------------|
| Memory Recall | ✅ | ✅ | Fast, no LLM call |
| Dimension Extractor | ✅ | ✅ | Fast, improves code quality |
| Assembly Decomposer | ✅ | ✅ | Fast, avoids wrong geometry |
| Planner | ✅ | ✅ | Needed for Skill Selector |
| Skill Selector | ✅ | ✅ | Improves code quality |
| Coder | ✅ | ✅ | Core operation |
| Code Critic | ✅ | ✅ | Catches logical mismatches |
| Repair Specialist | ✅ if needed | ✅ if needed | Needed if code fails |
| Render | ✅ | ❌ | Adds ~5-10 seconds |
| Dimension Validator | ✅ | ❌ | Needs render output |
| Reviewer | ✅ | ❌ | Needs render output |
| Human Approval | ✅ | ❌ | Skipped — code auto-loaded |
| Memory Curator + Save | ✅ | ✅ | Always save |
| Typical total time | 60–120 sec | 15–30 sec | |

**Toggle:** `Visual Review` checkbox in the Preferences panel.

---

## 11. The Human Approval Gate

The approval gate is implemented using LangGraph's `interrupt()` mechanism:

```python
# In human_approval_node:
response = interrupt({
    "message": "Shape looks correct. Do you approve loading this code?",
    "svg_paths": svg_paths,
    "visual_critique": visual_critique,
    "code_preview": first_6_lines_of_code,
    "code_failed": code_failed,
})
```

`interrupt()` causes the graph to pause and serialise its entire state to the `MemorySaver` checkpoint. The background thread returns. The UI shows the approval panel.

When the user clicks a button:
- **Approve:** widget calls `graph.stream(Command(resume={"approved": True}), ...)`
- **Recreate:** widget calls `graph.stream(Command(resume={"approved": False, "feedback": user_text}), ...)`
- **Cancel:** widget calls `graph.stream(Command(resume={"cancel": True}), ...)`

The graph resumes from the checkpoint, `human_approval_node` reads the response, and routing continues.

**Code Failed state:** If the coder produced no code (code=""), the approval panel shows:
- "Code generation failed — no shape to show"
- Approve button is disabled (greyed out)
- Only Recreate and Cancel are available

---

## 12. A Complete Example — End to End

**User action:** Types "Create a small L-shaped mounting bracket with 4 M4 holes at the corners" and attaches a photo of a metal bracket.

---

**Step 1 — Memory Recall**  
Searches `shapes_memory.json` for similar past shapes.  
Finds: "wall bracket with mounting holes" from a previous session.  
Passes it as a hint to planner and coder.

---

**Step 2 — Dimension Extractor (WITH image)**  
Analyses the photo:
- Estimates overall: 80mm (W) × 50mm (H) × 40mm (D)
- Identifies two rectangular planes at 90° → L-shape confirmed
- Thickness: approximately 5mm
- 4 holes at corners, look like M4 clearance (4.5mm)
- Fillet visible on the inner bend, ~3mm

Outputs dimension hints dict → stored in state.

---

**Step 3 — Assembly Decomposer**  
Reads: "L-shaped mounting bracket with 4 M4 holes"  
Decision: **single part** — one solid with features.  
Passes through with `is_assembly=False`.

---

**Step 4 — Planner**  
Receives: user text + image + dimension hints + past shape hint  
Produces plan:
```
- L-shaped body: vertical plate 80×50×5mm + horizontal flange 80×40×5mm
- 4 holes M4 clearance (4.5mm dia) at corners of each plate face
- Fillet inner corner 3mm radius
- show_object(result)
```
Calls `plan_shape(features)` tool to commit.

---

**Step 5 — Skill Selector**  
Reads plan: "L-shaped body" → searches 71 skills → finds `bracket` skill matches perfectly.  
Also: "M4 holes at corners" → `counterbore_hole` template relevant.  
Returns: `[{name: "bracket", priority: 1}, {name: "counterbore_hole", priority: 2}]`

---

**Step 6 — Coder**  
Receives: plan + skill recommendations + dimension hints + reference image  
1. Calls `use_skill("bracket", {"width": 80, "height": 50, "depth": 40, "thickness": 5})`  
2. Gets starting code for L-shape  
3. Extends it: adds `.pushPoints(corner_pts).hole(4.5)` for the 4 M4 holes  
4. Adds `.edges("|Z").fillet(3)` for inner corner  
5. Calls `execute_cadquery(code)` → SUCCESS  

---

**Step 7 — Code Critic**  
Reads plan vs code:
- Plan says 4 holes ✅ — code has 4 pushPoints
- Plan says fillet ✅ — code has .fillet(3)
- Plan says L-shape ✅ — code creates base + wall + union
- `show_object(result)` present ✅

Result: `issues_found: false` → pipeline continues.

---

**Step 8 — Render**  
Runs code in subprocess, exports 3 SVG files:
- `isometric.svg` — diagonal 3D view
- `front.svg` — straight front face
- `top.svg` — looking down

---

**Step 9 — Dimension Validator**  
Compares reference photo vs isometric SVG:
- Reference W:H ≈ 1.6:1, generated W:H ≈ 1.7:1 → close enough
- Hole size relative to body: reference ~0.12, generated ~0.11 → acceptable
Result: `proportions_match: true` → no corrections needed.

---

**Step 10 — Reviewer**  
Sees: reference photo + 3 SVG projections + plan + "proportions look correct"  
Assessment:
```
APPROVED
Shape matches reference — L-shaped bracket with 4 corner holes and filleted inner corner visible in all projections.
```

---

**Step 11 — Human Approval Gate**  
Graph pauses. UI shows:
- Isometric SVG preview
- "APPROVED — L-shaped bracket with 4 corner holes..."
- Code preview (first 6 lines)
- Approve & Load / Recreate / Cancel buttons

User clicks **Approve & Load**.

---

**Step 12 — Memory Curator + Save**  
Curator reviews last 15 memory entries.  
No identical bracket found → decision: `SAVE_NEW`  
Generates tags: `["bracket", "L-shape", "mounting", "M4-holes", "small", "filleted"]`  
Description: "L-shaped aluminum mounting bracket with 4×M4 corner holes and 3mm inner fillet"  
Writes to `shapes_memory.json`.

---

**Result:** Code is loaded into CQ-Editor. Shape appears in the 3D viewer. The entire process took approximately 75 seconds.

---

## 13. Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| AI orchestration | LangGraph (StateGraph) | Multi-node pipeline with conditional routing |
| LLM | Google Gemini (via langchain-google-genai) | All 10 agents — text + vision |
| Agent pattern | LangChain ReAct | Planner, Coder use tool-calling loops |
| State persistence | LangGraph MemorySaver | Checkpoint for human approval pause/resume |
| CadQuery execution | subprocess | Isolated headless execution for safety |
| SVG rendering | PyQt5 QSvgRenderer | Convert SVG to PNG for vision LLM (no extra deps) |
| GUI panel | PyQt5 QWidget | Integrated into CQ-Editor's panel system |
| Threading | Python threading.Thread | Keeps UI responsive during pipeline run |
| Thread-UI bridge | PyQt5 signals + slots | Safe cross-thread UI updates |
| Memory store | JSON file | Simple, persistent, readable without a database |

---

## 14. File-by-File Reference

```
cadquery-ai-agent/
│
├── README.md                          Quick-start, feature list, setup guide
│
├── docs/
│   ├── v4_agentic_workflow.md         Stage-by-stage pipeline reference
│   └── end_to_end_documentation.md   This file — full project documentation
│
├── skills/
│   ├── skill_registry.json            [{name, description, category, file}] for all 71 skills
│   ├── features/                      Individual shape skills
│   │   ├── bracket.py                 L-shaped bracket
│   │   ├── enclosure.py               Hollow box with open face
│   │   ├── pocket.py                  Rectangular pocket in a plate
│   │   ├── involute_gear.py           Spur gear with involute profile
│   │   ├── sphere.py, cone.py, ...    Basic shapes
│   │   ├── rib.py, boss.py, ...       Structural features
│   │   ├── spline_path_sweep.py, ...  Spline-based shapes
│   │   └── (44 more files)
│   ├── assemblies/
│   │   ├── bolt.py, nut.py, ...       Fastener templates
│   │   └── massembly.py               Constrained assembly via cadquery-massembly
│   ├── import_export/
│   │   ├── step_import.py
│   │   ├── step_export.py
│   │   └── dxf_import.py
│   └── generic/
│       └── fallback.py                Minimal template when no skill matches
│
├── cq_agent_v4/
│   ├── __init__.py
│   │
│   ├── state.py                       AgentState TypedDict — all 20+ pipeline fields
│   │
│   ├── graph.py                       LangGraph StateGraph — 13 nodes + 6 routing functions
│   │                                  Imports all node functions, builds and compiles graph
│   │
│   ├── widget.py                      PyQt5 UI panel
│   │                                  - QWidget with chat bubbles, SVG preview, approval buttons
│   │                                  - _Bridge: Qt signals for thread-safe UI updates
│   │                                  - _run_agent(): background thread running graph.stream()
│   │                                  - _resume_agent(): resumes graph after human approval
│   │                                  - _on_approval_needed(): shows approval panel + SVG
│   │                                  - _show_svg(): renders SVG → QPixmap with Y-flip fix
│   │
│   ├── agents/
│   │   ├── dimension_extractor.py     run_dimension_extractor() + format_hints_for_planner()
│   │   ├── assembly_decomposer.py     run_assembly_decomposer() + format_assembly_context()
│   │   ├── planner.py                 run_planner() — ReAct agent with plan_shape tool
│   │   ├── skill_selector.py          run_skill_selector() + format_skill_recommendations()
│   │   ├── coder.py                   run_coder() — ReAct agent with 4 tools
│   │   │                              _extract_code() — finds last SUCCESS code from messages
│   │   │                              _extract_last_error() — finds last error for repair
│   │   ├── code_critic.py             run_code_critic() + format_critic_feedback()
│   │   ├── repair_specialist.py       run_repair_specialist() — error pattern library
│   │   ├── dimension_validator.py     run_dimension_validator() + format_dimension_corrections()
│   │   ├── reviewer.py                run_reviewer() + _svg_to_image() (SVG→PNG via PyQt5)
│   │   └── memory_curator.py          run_memory_curator()
│   │
│   ├── tools/
│   │   ├── cadquery_tools.py          @tool execute_cadquery(code)
│   │   │                              @tool render_shape(code) → 3 SVG paths JSON
│   │   └── skill_tools.py             @tool search_skills(query)
│   │                                  @tool list_skills()
│   │                                  @tool use_skill(name, params_json)
│   │                                  @tool plan_shape(features)
│   │
│   └── memory/
│       ├── store.py                   _load(), _save(), recall_similar(), save_shape(),
│       │                              update_shape(), all_shapes()
│       └── shapes_memory.json         Persistent shape database (auto-created, max 100)
│
└── cq_editor_integration/
    ├── README.md                      How to install the widget into CQ-Editor
    └── widgets/
        └── ai_chat_agent_v4.py        Drop-in file → CQ-editor/cq_editor/widgets/
```
