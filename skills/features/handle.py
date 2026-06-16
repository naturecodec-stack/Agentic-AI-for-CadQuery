NAME = "handle"
DESCRIPTION = "Create a grip handle or door handle with mounting base"
PARAMETERS = {
    "grip_length":   {"type": "float", "default": 100.0, "unit": "mm"},
    "grip_diameter": {"type": "float", "default": 22.0,  "unit": "mm"},
    "base_height":   {"type": "float", "default": 30.0,  "unit": "mm", "desc": "height of mounting posts"},
    "base_width":    {"type": "float", "default": 30.0,  "unit": "mm"},
    "base_thickness":{"type": "float", "default": 8.0,   "unit": "mm"},
    "hole_diameter": {"type": "float", "default": 4.5,   "unit": "mm"},
    "fillet_r":      {"type": "float", "default": 3.0,   "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

gl  = {grip_length}
gd  = {grip_diameter}
bh  = {base_height}
bw  = {base_width}
bt  = {base_thickness}
hd  = {hole_diameter}
fr  = {fillet_r}

# Grip bar (horizontal cylinder)
grip = (cq.Workplane("XY")
    .circle(gd / 2)
    .extrude(gl)
    .translate((-gl / 2, 0, bh + gd / 2)))

# Left mounting base
left_base = (cq.Workplane("XY")
    .box(bt, bw, bh + gd)
    .translate((-gl / 2 - bt / 2, 0, (bh + gd) / 2)))

# Right mounting base
right_base = (cq.Workplane("XY")
    .box(bt, bw, bh + gd)
    .translate((gl / 2 + bt / 2, 0, (bh + gd) / 2)))

result = grip.union(left_base).union(right_base)

# Mounting holes
result = (result
    .faces("<Z").workplane()
    .pushPoints([(-gl / 2 - bt / 2, 0), (gl / 2 + bt / 2, 0)])
    .hole(hd, depth=bt))

if fr > 0:
    try:
        result = result.edges("|Z").fillet(fr)
    except Exception:
        pass

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        grip_length=float(params.get("grip_length", 100.0)),
        grip_diameter=float(params.get("grip_diameter", 22.0)),
        base_height=float(params.get("base_height", 30.0)),
        base_width=float(params.get("base_width", 30.0)),
        base_thickness=float(params.get("base_thickness", 8.0)),
        hole_diameter=float(params.get("hole_diameter", 4.5)),
        fillet_r=float(params.get("fillet_r", 3.0)),
    )
