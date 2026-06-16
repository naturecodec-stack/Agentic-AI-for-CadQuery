from state import AgentState
from llm import call_llm
from skill_loader import load_skill

SYSTEM = """You are an expert CadQuery programmer. Generate correct, working Python code.

═══════════════════════════════════════════════════════
CADQUERY API REFERENCE
═══════════════════════════════════════════════════════

WORKPLANE & PRIMITIVES
  cq.Workplane("XY")                        # base plane
  .box(l, w, h)                             # centred box
  .cylinder(h, r)                           # centred cylinder
  .sphere(r)
  .wedge(dx,dy,dz,xmin,zmin,xmax,zmax)
  .circle(r).extrude(h)                     # cylinder from profile
  .rect(w,h).extrude(h)
  .polyline([(x,y),...]).close().extrude(h) # custom profile

FACES & WORKPLANES
  .faces(">Z")                # top face (max Z)
  .faces("<Z")                # bottom face (min Z)
  .faces(">X") / .faces("<X") / .faces(">Y") / .faces("<Y")
  .faces("|Z")                # all faces parallel to Z
  .workplane()                # new workplane on selected face
  .workplane(offset=h)        # offset from current plane
  .workplane(origin=(x,y,z), normal=(nx,ny,nz))  # explicit plane

HOLES & FEATURES
  .hole(diameter)
  .cboreHole(d, cboreD, cboreDepth)
  .cskHole(d, cskD, cskAngle)
  .slot2D(length, diameter)

ARRAYS
  .rarray(xSpacing, ySpacing, xCount, yCount).hole(d)   # grid
  .polarArray(radius, startAngle, angle, count).hole(d)  # polar

EDGES & FINISH
  .edges("|Z").fillet(r)     # vertical edges
  .edges(">Z").fillet(r)     # top face edges
  .edges().fillet(r)         # ALL edges (use carefully)
  .edges("|Z").chamfer(l)

BOOLEAN OPS
  .union(other)   / a.union(b)
  .cut(other)     / a.cut(b)
  .intersect(other)

TRANSFORMS
  .translate((x,y,z))
  .rotate((0,0,0),(0,0,1), angle)   # rotate around Z
  .mirror("XY") / .mirror("XZ") / .mirror("YZ")

SHELL & LOFT
  .faces(">Z").shell(-thickness)     # hollow — NEGATIVE = inward
  .workplane(offset=h).rect(w,h).loft()
  .revolve(angleDeg, axisStart, axisEnd)

SWEEP
  helix = cq.Wire.makeHelix(pitch, height, radius)
  cq.Workplane("XY").circle(r).sweep(cq.Workplane(obj=helix), isFrenet=True)

TEXT
  .faces(">Z").workplane().text("str", size, depth)          # emboss
  .faces(">Z").workplane().text("str", size, -depth, cut=True) # deboss

FASTENERS (cq_warehouse)
  from cq_warehouse.fastener import HexHeadScrew, HexNut, PlainWasher
  HexHeadScrew(size="M8-1.25", length=30, fastener_type="iso4017")

═══════════════════════════════════════════════════════
PATTERNS FOR COMPLEX SHAPES
═══════════════════════════════════════════════════════

Pattern 1 — Build bodies separately, then combine:
  base  = cq.Workplane("XY").box(80, 40, 5)
  wall  = cq.Workplane("XY").box(5, 40, 30).translate((37.5, 0, 17.5))
  body  = base.union(wall)
  # Now add holes/features to the combined body

Pattern 2 — Use .tag() to mark faces BEFORE boolean ops:
  base = cq.Workplane("XY").box(50, 30, 10).tag("top")
  body = base.union(other)
  result = body.faces(tag="top").workplane().hole(5)

Pattern 3 — Workplane from explicit origin when face selectors are ambiguous:
  result = body.workplane(origin=(0,0,10), normal=(0,0,1)).hole(d)

Pattern 4 — Pocket (rectangular cutout):
  result = (
      cq.Workplane("XY").box(80, 50, 15)
      .faces(">Z").workplane()
      .rect(60, 30).cutBlind(-8)   # pocket 8mm deep
  )

Pattern 5 — Stepped/multi-diameter solid:
  result = (
      cq.Workplane("XY")
      .circle(15).extrude(10)           # base disk
      .faces(">Z").workplane()
      .circle(10).extrude(20)           # middle step
      .faces(">Z").workplane()
      .circle(6).extrude(15)            # top pin
  )

Pattern 6 — Fillet/chamfer ALWAYS last (after all booleans):
  result = (
      body
      .edges("|Z").fillet(2)   # vertical edges first
      .edges(">Z").fillet(1)   # then top face edges
  )

Pattern 7 — Mirror for symmetric parts:
  half = cq.Workplane("XY").box(20, 40, 10).translate((10, 0, 5))
  result = half.union(half.mirror("YZ"))

═══════════════════════════════════════════════════════
RULES
═══════════════════════════════════════════════════════
- ALWAYS start with: import cadquery as cq
- Store final shape in variable named `result`
- ALWAYS end with: show_object(result)
- Use Pattern 1 (separate bodies + union) for L-shapes, T-shapes, brackets
- Use .tag() when you need reliable face selection after booleans
- Add fillets/chamfers LAST — they break face selectors if done early
- Output ONLY raw Python code — no markdown, no backticks, no explanation
"""


def _strip_markdown(code: str) -> str:
    if code.startswith("```"):
        lines = [l for l in code.splitlines() if not l.startswith("```")]
        return "\n".join(lines).strip()
    return code


def code_generation_node(state: AgentState) -> dict:
    print("[3/5] Generating code...")

    if state["selected_skill"] and state["selected_skill"] != "generic":
        try:
            skill = load_skill(state["selected_skill"])
            code = skill.render(state["extracted_params"])
            if code.strip():
                print(f"  ✓ Code from skill template: {state['selected_skill']}")
                return {"generated_code": code}
        except Exception as e:
            print(f"  Skill render failed ({e}), falling back to LLM")

    user = (
        f"User request: {state['user_request']}\n\n"
        f"Construction plan:\n{state['plan']}\n\n"
        f"Write the complete CadQuery Python script following the plan's BUILD_STEPS. "
        f"Add a short comment before each major step."
    )
    code = call_llm(state["api_key"], state["model"], SYSTEM, user, state["image_path"])
    print("  ✓ Code generated by LLM")
    return {"generated_code": _strip_markdown(code)}
