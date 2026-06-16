# V4 Agentic Workflow

CadQuery AI Agent v4 is a domain-specific agentic AI that turns your text description or reference image into validated, working CadQuery Python code — automatically, inside CQ-Editor.

---

## The Big Picture

```
You → [Memory] → [Dims] → [Assembly?] → [Plan] → [Skills] → [Code] → [Critic]
    → [Repair?] → [Render] → [Dim Check] → [Review] → [Approve] → [Save] → CQ-Editor
```

**10 AI agents** collaborate in a 13-node pipeline. You only intervene at the final approval gate.

---

## Stage by Stage

### Stage 1 — Memory Recall

Before anything, the AI searches its long-term memory for shapes it has built before.

- Loads the 3 most similar past shapes as hints for the planner and coder
- Memory stored in `cq_agent_v4/memory/shapes_memory.json`
- Example: ask for "a bracket" → recalls "L-bracket with mounting holes" from a previous session

---

### Stage 2 — Dimension Extractor *(Agent 1)*

The first agent dedicated to accuracy. Runs immediately after memory recall.

**WITH a reference image:**
- Analyses the image to extract proportions (width:height:depth ratios)
- Counts every visible feature: holes, ribs, slots, fillets, steps, pockets
- Estimates absolute mm based on what the part looks like in real life
- Reports confidence level per measurement

**WITHOUT a reference image:**
- Parses the text request for explicit dimensions ("80mm", "M4 holes")
- Applies engineering standards (M4 = 4mm diameter, standard bracket = 4-6mm thick)
- Infers missing dimensions from shape type ("small bracket → ~80×40×5mm")
- Tags each dimension as `explicit` (from text) or `inferred` (estimated)

Output is a structured dimension hints block injected into the planner and coder prompts.

---

### Stage 3 — Assembly Decomposer *(Agent 2)*

Detects whether the input describes a **single part** or a **multi-part assembly**.

**Single part examples:** gear, bracket, enclosure, bolt, shaft  
**Assembly examples:** bolt + nut, housing + lid, motor mount + bearings

If assembly detected:
- Splits the request into individual part descriptions
- Identifies how parts connect (bolted, press-fit, snap-fit, constrained)
- Passes part list to the Planner so it can plan each part separately

If single part: passes through cleanly with no overhead.

---

### Stage 4 — Planner Agent *(Agent 3)*

A dedicated Planner AI reads:
- Your text request
- The reference image (if provided)
- Dimension hints from the extractor
- Assembly context (if multi-part)
- Past similar shapes from memory

It produces an exact feature list — the contract the coder must honour:

```
- Box body: 80mm × 40mm × 5mm
- 4 counterbore holes at corners, M4 (4.5mm), 10mm from each edge
- 2mm fillet on all vertical edges
- Central pocket: 50mm × 20mm × 3mm deep
```

**Rules:**
- If image provided → image is the PRIMARY specification, text is secondary
- Describe ONLY what is visible — do not invent features
- Estimate dimensions from image proportions when not explicitly stated

---

### Stage 5 — Skill Selector *(Agent 4)*

A dedicated agent that reads the full feature plan and picks the best 1-3 skill templates from the 71-skill library.

**Why it beats keyword search:**
- Reads the plan holistically, not just one keyword
- "Plan describes L-shaped bracket" → recommends `bracket` skill (not just string matching)
- Ranks by primary shape first, then secondary feature templates
- Only recommends genuinely relevant skills — wrong recommendation = worse than none

Output: ranked list of skill names with reasoning, injected into the coder prompt.

---

### Stage 6 — Coder Agent *(Agent 5)*

A dedicated Coder AI receives:
- Feature plan
- Skill recommendations (which templates to start from)
- Dimension hints (exact sizes to use)
- Reference image (sees the target shape directly)
- Code Critic feedback (if sent back for correction)
- Visual critique from reviewer (if looping back)
- Past similar shapes from memory

It writes CadQuery Python code, then validates it by running it:

**Self-repair loop:**
1. Picks best skill template via `use_skill()`
2. Extends template code to match all plan features
3. Calls `execute_cadquery` to test
4. If error → reads traceback, fixes code
5. Repeats up to **5 times** until `SUCCESS`

**Tools the coder uses:**

| Tool | Purpose |
|------|---------|
| `search_skills` | Keyword search over 71 templates |
| `list_skills` | See all 71 available templates |
| `use_skill(name, params)` | Render a template as starting code |
| `execute_cadquery(code)` | Run headlessly — returns `SUCCESS` or full error |

---

### Stage 7 — Code Critic *(Agent 6)*

Runs immediately after the coder, **before rendering**. Catches logical mismatches that execution can't detect.

Examples of what it catches:
- "Plan says 4 holes but code only has 2 `pushPoints`"
- "Plan specifies fillet but no `.fillet()` call found"
- "Plan says hollow/shell but code produces a solid"
- "Plan says M6 holes (6mm) but code uses `hole(3)`"

If issues found → feedback sent back to Coder. Coder rewrites targeting all flagged issues.  
This loop runs **at most once** — critic gets one correction shot.

If no issues → continues to render.

---

### Stage 8 — Repair Specialist *(Agent 7)*  *(activated only on failure)*

Activated **only** when the coder exhausts all 5 retries and still fails.

The Repair Specialist has a deep knowledge library of CadQuery error patterns:

| Error | Root cause | Fix applied |
|-------|-----------|-------------|
| `StdFail_NotDone` | Shape construction failed at kernel | Reduce sweep profile, check loft wire counts |
| `NullPointerException` | Empty face/edge selection | Try alternate selectors, split into variables |
| `Fillet failed` | Radius exceeds edge geometry | Reduce radius, use `\|Z` edge filter |
| `Wire is not closed` | Sketch curves don't connect | Add `.close()`, use rect/circle instead |
| `Shape is null` | Boolean op on non-overlapping shapes | Translate shape before boolean |
| `ImportError` | External library missing | Replace with pure CadQuery equivalent |

After repair: validates the fix with `execute_cadquery`, then continues to render.

---

### Stage 9 — Render

If code is valid, renders 3 SVG projection views:

| View | Direction |
|------|----------|
| Isometric | Diagonal 3D angle |
| Front | Straight-on front face |
| Top | Looking down from above |

SVG files are saved temporarily and passed to the next agents.

---

### Stage 10 — Dimension Validator *(Agent 8)*

Runs after render. **Only meaningful when a reference image is provided.**

Compares proportions numerically between the reference image and the rendered SVG:
- Measures width:height ratio in both images
- Measures relative feature sizes (hole diameter vs body width)
- Reports percentage mismatches: "shape is 50% too wide — reduce width from ~120mm to ~80mm"

Output is a dimension correction block appended to the Reviewer's context, so the reviewer also sees it.

---

### Stage 11 — Reviewer Agent *(Agent 9)*

A Reviewer AI (with vision capability) sees:
- Your original reference image (if provided)
- All 3 SVG projection images of the generated shape
- The feature plan
- Dimension corrections from the validator

Responds with exactly:

```
APPROVED
Shape matches reference — box body with 4 corner holes and central pocket visible.
```

or:

```
REJECTED
- Holes are missing from top face
- Central pocket not visible in any projection
- Shape is ~40% too wide compared to reference proportions
```

**If REJECTED:** critique sent back to Coder, which rewrites.  
This visual loop repeats up to **2 times** before forcing human approval.

---

### Stage 12 — Human Approval Gate *(interrupt)*

The pipeline **pauses** and shows you:
- Rendered SVG (isometric view)
- Reviewer's written assessment
- First 6 lines of generated code preview

| Button | What happens |
|--------|-------------|
| **Approve & Load** | Code loaded into CQ-Editor immediately |
| **Recreate** | AI recodes with your optional typed feedback |
| **Cancel** | Stops the run cleanly, nothing loaded |

If you type feedback before Recreate → coder receives it as "HUMAN REJECTED — feedback: [your text]"

---

### Stage 13 — Memory Curator + Save *(Agent 10)*

Before saving, the Memory Curator agent:
- Checks if a similar shape already exists in memory
- Decides: **SAVE\_NEW** | **UPDATE\_EXISTING** | **SKIP** (duplicate)
- Generates better tags than keyword extraction:
  - Simple extraction: `["bracket", "with", "holes"]`
  - Curator output: `["bracket", "L-shape", "mounting", "M4-holes", "medium", "filleted"]`

After curation, the shape is saved to `shapes_memory.json` for future recall.

---

## Full Pipeline Diagram

```
         ┌──────────────────────────────────────────────┐
         │         YOUR REQUEST + IMAGE (optional)       │
         └────────────────────┬─────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   MEMORY RECALL     │ ← search past shapes
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │ DIMENSION EXTRACTOR │ ← extract mm from image OR text
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │ ASSEMBLY DECOMPOSER │ ← single part or multi-part?
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │   PLANNER AGENT     │ ← build exact feature plan
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │   SKILL SELECTOR    │ ← pick best 1-3 templates
                    └─────────┬──────────┘
                              │
              ┌───────────────▼───────────────┐ ◄───────────────────────────┐
              │         CODER AGENT            │                             │
              │  (5 retries via execute_cq)    │                             │
              └───────────────┬───────────────┘                             │
                              │                                             │
              ┌───────────────▼───────────────┐                             │
              │         CODE CRITIC            │ ─── issues found ──────────┘
              │  (plan vs code logic check)    │     (max 1 correction)
              └──────┬────────────────┬────────┘
                  OK │           FAILED │ (code never executed)
                     │                 │
                     │    ┌────────────▼────────────┐
                     │    │    REPAIR SPECIALIST     │
                     │    │ (error pattern library)  │
                     │    └────────────┬────────────┘
                     │                 │
                     └────────┬────────┘
                              │
                    ┌─────────▼──────────┐
                    │       RENDER        │ ← isometric, front, top SVG
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │ DIMENSION VALIDATOR │ ← compare SVG proportions to image
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │   REVIEWER AGENT    │ ← visual approval/rejection
                    └──────────┬─────────┘
                               │
          ┌────────────────────┴─────────────────────┐
       APPROVED                               REJECTED (max 2×)
          │                                          │
          │                                   ┌──────▼──────┐
          │                                   │ CODER AGENT │ ← (loop)
          │                                   └─────────────┘
          │
    ┌─────▼──────────────────────────────────────────┐
    │              HUMAN APPROVAL GATE                │
    │       [Approve & Load] [Recreate] [Cancel]      │
    └─────┬───────────────────────────────────────────┘
          │ Approve                   │ Recreate ──► Coder again
          │
    ┌─────▼─────────┐
    │ MEMORY CURATOR │ ← dedup check, better tags, SAVE/UPDATE/SKIP
    └─────┬─────────┘
          │
    ┌─────▼─────────┐
    │   CQ-EDITOR    │ ← code loaded, shape visible
    └───────────────┘
```

---

## Fast Mode vs Full Mode

Toggle **Visual Review** in Preferences:

| Stage | Full Mode (Visual Review ON) | Fast Mode (Visual Review OFF) |
|-------|------------------------------|-------------------------------|
| Memory Recall | ✅ | ✅ |
| Dimension Extractor | ✅ | ✅ |
| Assembly Decomposer | ✅ | ✅ |
| Planner | ✅ | ✅ |
| Skill Selector | ✅ | ✅ |
| Coder | ✅ | ✅ |
| Code Critic | ✅ | ✅ |
| Repair Specialist | ✅ (if needed) | ✅ (if needed) |
| Render | ✅ | ❌ skipped |
| Dimension Validator | ✅ | ❌ skipped |
| Reviewer | ✅ | ❌ skipped |
| Human Approval | ✅ | ❌ auto-loaded |
| Memory Curator + Save | ✅ | ✅ |
| Typical time | ~60–120 seconds | ~15–30 seconds |
| Best for | Complex shapes, image input | Quick iterations, simple shapes |

---

## All 10 Agents at a Glance

| # | Agent | Solves | When |
|---|-------|--------|------|
| 1 | Dimension Extractor | AI guessing dimensions blindly | Always — before planning |
| 2 | Assembly Decomposer | Multi-part images treated as one shape | Always — before planning |
| 3 | Planner | Unstructured code without a plan | Always — before coding |
| 4 | Skill Selector | Coder picking wrong template or reinventing wheels | Always — before coding |
| 5 | Coder | Writing and validating the CadQuery code | Always — core generator |
| 6 | Code Critic | Code that runs but doesn't match the plan | Always — after coding |
| 7 | Repair Specialist | Hard errors after 3+ failed retries | Only on failure |
| 8 | Dimension Validator | Shape looks right but proportions are wrong | Full mode + image only |
| 9 | Reviewer | No automatic visual quality check | Full mode only |
| 10 | Memory Curator | Duplicate/poor-quality memory entries | Always — before saving |

---

## What Makes v4 Agentic

```
Normal AI:   You ask → AI answers → Done

v4 Agent:    You ask
               → AI extracts dimensions
               → AI detects assembly structure
               → AI plans exact features
               → AI selects skill templates
               → AI writes + self-tests code
               → AI critiques its own code
               → (AI repairs hard errors if needed)
               → AI renders shape
               → AI validates proportions
               → AI visually reviews output
               → AI fixes its own mistakes
               → You approve
               → AI curates memory
               → Done
```

The AI acts, observes, evaluates, and corrects itself through **13 pipeline stages**.  
You only intervene **once** — at the human approval gate.

---

## File Structure

```
cq_agent_v4/
├── state.py                    Full pipeline state (all 20+ fields)
├── graph.py                    LangGraph StateGraph — 13 nodes, conditional routing
├── widget.py                   PyQt5 panel — UI, approval buttons, streaming display
├── agents/
│   ├── dimension_extractor.py  Agent 1 — extract mm from image or text
│   ├── assembly_decomposer.py  Agent 2 — detect multi-part assemblies
│   ├── planner.py              Agent 3 — build exact feature plan
│   ├── skill_selector.py       Agent 4 — pick best skill templates
│   ├── coder.py                Agent 5 — write + validate CadQuery code
│   ├── code_critic.py          Agent 6 — plan vs code logic check
│   ├── repair_specialist.py    Agent 7 — deep error repair (error pattern library)
│   ├── dimension_validator.py  Agent 8 — proportion comparison (image vs SVG)
│   ├── reviewer.py             Agent 9 — visual inspection via SVG → PNG
│   └── memory_curator.py       Agent 10 — dedup + tag improvement before save
├── tools/
│   ├── cadquery_tools.py       execute_cadquery, render_shape
│   └── skill_tools.py          search_skills, list_skills, use_skill, plan_shape
└── memory/
    ├── store.py                recall_similar(), save_shape(), update_shape()
    └── shapes_memory.json      persistent shape database (up to 100 entries)
```

---

## Skill Library (71 skills)

The Skill Selector and Coder can access 71 pre-built CadQuery shape templates:

**Basic shapes:** sphere · cone · frustum · torus · hex prism · ring · pin · ellipse · wedge · partial cylinder

**Features:** bracket · enclosure · pocket · stepped shaft · shell · revolve · text on face · helix · involute gear · sweep · ISO thread · grid holes · polar holes · counterbore hole · countersink hole · multi-section loft

**Structural:** rib · boss · snap fit · T-slot extrusion · U/C/L channel · living hinge

**Mechanical:** pulley · pipe flange · hook · handle · cable clip

**Splines:** spline path sweep · spline profile · spline surface · NACA airfoil · spline transition

**2D Primitives:** bezier profile · offset profile (frame/gasket) · slot plate

**Arrays & Patterns:** rectangular array · polar array · mirror body · angled feature

**Compound Shapes:** lidded box · boolean intersection

**Gears (cq_gears):** helical · bevel · ring · worm set · rack · herringbone · planetary

**Assemblies:** MAssembly constrained · bolt · nut · washer · bolt+nut · flange bolt pattern · plate with bolts

**Electronics:** PCB standoff · heat sink

**Import/Export:** STEP import · STEP/STL/SVG export · DXF import
