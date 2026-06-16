# V4 Agentic Workflow

CadQuery AI Agent v4 is a domain-specific agentic AI that turns your text description or reference image into validated, working CadQuery Python code — automatically, inside CQ-Editor.

---

## The Big Picture

```
You → [Memory] → [Plan] → [Code] → [Render] → [Review] → [Approve] → [Save] → CQ-Editor
```

Three AI agents collaborate in a pipeline. You only intervene at the final approval gate.

---

## Stage by Stage

### Stage 1 — Memory Recall

Before doing anything, the AI searches its long-term memory for shapes it has built before.

- Loads the 3 most similar past shapes as hints
- Memory is stored in `cq_agent_v4/memory/shapes_memory.json`
- Example: you ask for "a bracket" — it recalls "L-bracket with mounting holes" from a previous session and uses it as context

**Fast mode:** included even in fast mode — memory recall is instant.

---

### Stage 2 — Planner Agent

A dedicated Planner AI reads your request, the memory hints, and your reference image (if attached).

It breaks the shape into an exact feature list:

```
- Box body: 100mm × 50mm × 10mm
- 4 counterbore holes at corners, 5mm diameter, 10mm from each edge
- 2mm fillet on all vertical edges
- Central pocket: 60mm × 30mm × 5mm deep
```

**Rules the planner follows:**
- If an image is provided → the image is the PRIMARY source, text request is secondary
- Must describe only what is visible in the image — no invented features
- Must estimate dimensions from image proportions if not stated explicitly

This plan is the contract the coder must follow completely.

**Fast mode:** skipped — coder works directly from the user request.

---

### Stage 3 — Coder Agent

A dedicated Coder AI receives:
- The feature plan from the planner
- The original reference image (so it can see exactly what to build)
- Any visual critique from a previous review loop
- Relevant past shapes from memory

It writes CadQuery Python code step by step, then validates it by running it.

**Self-repair loop:**
1. Writes code
2. Calls `execute_cadquery` to test it
3. If error → reads the exact error message, fixes the code
4. Repeats up to **5 times** until `SUCCESS`

If all 5 attempts fail → approval panel shows "Code generation failed".

**Tools the coder uses:**

| Tool | Purpose |
|------|---------|
| `search_skills` | Search the 27-template skill library by keyword |
| `list_skills` | See all available skill templates |
| `use_skill` | Render a template with custom parameters as starting code |
| `execute_cadquery` | Run code headlessly — returns `SUCCESS` or full error |

---

### Stage 4 — Render

If the coder succeeds, the shape is rendered into **3 SVG projection images**:

| View | Direction |
|------|----------|
| Isometric | Diagonal 3D angle view |
| Front | Straight-on front face |
| Top | Looking down from above |

These are saved as temporary SVG files and passed to the reviewer.

**Fast mode:** skipped entirely.

---

### Stage 5 — Reviewer Agent

A Reviewer AI (with vision capability) looks at all 3 SVG images and compares them against:
- Your original reference image (if provided)
- The feature plan from the planner

It responds with exactly:

```
APPROVED
Shape has all planned features — box body with 4 corner holes and central pocket visible.
```

or:

```
REJECTED
- Holes are missing from top face
- Central pocket not visible in any projection
- Proportions too wide compared to reference image
```

**If REJECTED:** feedback is sent back to the Coder, which rewrites the code.
This visual loop repeats up to **2 times** before forcing human approval regardless.

**Fast mode:** skipped entirely.

---

### Stage 6 — Human Approval

The pipeline **pauses** and shows you:
- The rendered SVG (isometric view)
- The reviewer's written assessment
- A preview of the first 6 lines of generated code

You choose:

| Button | What happens |
|--------|-------------|
| **Approve & Load** | Code is loaded into CQ-Editor immediately |
| **Recreate** | AI recodes with your optional feedback typed below |
| **Cancel** | Stops the run cleanly, nothing is loaded |

If you type feedback before clicking Recreate, the coder receives it alongside "HUMAN REJECTED — try a different approach."

**Fast mode:** skipped — code is loaded automatically without asking.

---

### Stage 7 — Save to Memory

After approval, the shape is saved to long-term memory with:
- The original request text
- The validated code
- Auto-extracted keyword tags

Next session, Stage 1 will recall this shape if you ask for anything similar.

---

## Full Flow Diagram

```
         ┌─────────────────────────────────────────┐
         │       YOUR REQUEST + IMAGE (optional)    │
         └──────────────────┬──────────────────────┘
                            │
                    ┌───────▼────────┐
                    │  MEMORY RECALL  │  ← searches past shapes
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │  PLANNER AGENT  │  ← extracts features from image/text
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐◄─────────────────────────┐
                    │   CODER AGENT   │  ← writes + self-tests   │
                    │  (5 retries)    │     (sees reference img)  │
                    └───────┬────────┘                           │
                            │                                    │
                    ┌───────▼────────┐                           │
                    │     RENDER      │  ← 3 SVG projections     │
                    └───────┬────────┘                           │
                            │                                    │
                    ┌───────▼────────┐                           │
                    │  REVIEWER AGENT │  ← compares to image     │
                    └───────┬────────┘                           │
                            │                                    │
              ┌─────────────┴──────────────┐                     │
           APPROVED                    REJECTED (max 2×) ────────┘
              │
     ┌────────▼─────────────────────────────────┐
     │         HUMAN APPROVAL GATE               │
     │  [Approve & Load] [Recreate] [Cancel]     │
     └────────┬──────────────────────────────────┘
              │ Approve                │ Recreate ──────────────► Coder again
              │
     ┌────────▼────────┐
     │   SAVE MEMORY    │  ← stores to shapes_memory.json
     └────────┬────────┘
              │
     ┌────────▼────────┐
     │   CQ-EDITOR      │  ← code loaded, shape visible
     └─────────────────┘
```

---

## Fast Mode vs Full Mode

Toggle **Visual Review** in Preferences:

| Stage | Full Mode (Visual Review ON) | Fast Mode (Visual Review OFF) |
|-------|------------------------------|-------------------------------|
| Memory | ✅ | ✅ |
| Plan | ✅ | ❌ (skipped) |
| Code | ✅ | ✅ |
| Render | ✅ | ❌ (skipped) |
| Review | ✅ | ❌ (skipped) |
| Approve | ✅ | ❌ (auto-loaded) |
| Save | ✅ | ✅ |
| Speed | ~45–90 seconds | ~10–20 seconds |
| Best for | Complex shapes, image input | Quick iterations, simple shapes |

---

## What Makes v4 Agentic

```
Normal AI:   You ask → AI answers → Done

Agentic AI:  You ask → AI plans → AI codes → AI tests itself
                     → AI renders → AI sees result → AI judges it
                     → AI fixes mistakes → You approve → AI remembers
```

The AI acts, observes, evaluates, and corrects itself without you doing anything between steps.
You only intervene once — at the approval gate.

---

## File Structure

```
cq_agent_v4/
├── state.py               Full pipeline state (all fields)
├── graph.py               LangGraph StateGraph — 7 nodes, conditional routing
├── widget.py              PyQt5 panel — UI, approval buttons, streaming display
├── agents/
│   ├── planner.py         Planner agent — extracts features from image + text
│   ├── coder.py           Coder agent — writes + validates CadQuery code
│   └── reviewer.py        Reviewer agent — visual inspection via SVG → PNG
├── tools/
│   ├── cadquery_tools.py  execute_cadquery, render_shape tools
│   └── skill_tools.py     search_skills, list_skills, use_skill tools
└── memory/
    ├── store.py            recall_similar(), save_shape(), all_shapes()
    └── shapes_memory.json  persistent shape database (up to 100 entries)
```

---

## Comparison: v3 vs v4

| Feature | v3 | v4 |
|---------|----|----|
| Agents | 1 (ReAct) | 3 (Planner + Coder + Reviewer) |
| Visual feedback | ❌ | ✅ |
| Long-term memory | ❌ | ✅ |
| Human approval gate | ❌ | ✅ |
| Image input (reference photo) | ❌ | ✅ |
| Self-repair loop | ✅ (5 retries) | ✅ (5 retries + visual loop) |
| Fast mode | ✅ (always) | ✅ (toggle) |
| Speed | Fast | Slower (full) / Fast (toggle OFF) |
