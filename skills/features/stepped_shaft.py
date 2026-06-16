NAME = "stepped_shaft"
DESCRIPTION = "Create a stepped cylindrical shaft with multiple diameters and optional keyway or flat"
PARAMETERS = {
    "steps": {"type": "list", "default": [[20, 10], [15, 25], [10, 15]],
              "desc": "list of [diameter, length] for each step, base to tip"},
    "keyway_width":  {"type": "float", "default": 0.0,  "unit": "mm", "desc": "keyway width (0 = none)"},
    "keyway_depth":  {"type": "float", "default": 0.0,  "unit": "mm"},
    "keyway_length": {"type": "float", "default": 0.0,  "unit": "mm", "desc": "0 = full length of largest step"},
    "chamfer":       {"type": "float", "default": 0.5,  "unit": "mm", "desc": "chamfer on step transitions"},
    "center_hole_d": {"type": "float", "default": 0.0,  "unit": "mm", "desc": "through-hole diameter (0 = solid)"},
}

TEMPLATE = """import cadquery as cq

steps        = {steps}
kw_w         = {keyway_width}
kw_d         = {keyway_depth}
kw_l         = {keyway_length}
chamfer_size = {chamfer}
center_d     = {center_hole_d}

# Build stacked cylinders bottom to top
result = cq.Workplane("XY")
z = 0
for d, l in steps:
    result = (
        result
        .workplane(offset=z) if z > 0 else result
    )
    result = result.circle(d / 2).extrude(l)
    z += l

# Chamfer step transitions
if chamfer_size > 0:
    try:
        result = result.edges("|Z").chamfer(chamfer_size)
    except Exception:
        pass

# Keyway slot
if kw_w > 0 and kw_d > 0:
    largest_d = max(d for d, l in steps)
    largest_l = next(l for d, l in steps if d == largest_d)
    kl = kw_l if kw_l > 0 else largest_l
    z_start = sum(l for d, l in steps if d != largest_d) * 0  # approx — assumes first step is largest
    keyway = (
        cq.Workplane("XY")
        .box(kl, kw_w, kw_d)
        .translate((kl / 2, 0, largest_d / 2 - kw_d / 2))
    )
    result = result.cut(keyway)

# Through-hole
if center_d > 0:
    total_length = sum(l for _, l in steps)
    hole = cq.Workplane("XY").cylinder(total_length + 1, center_d / 2)
    result = result.cut(hole)

show_object(result)
"""


def render(params: dict) -> str:
    steps = params.get("steps", [[20, 10], [15, 25], [10, 15]])
    if isinstance(steps, str):
        import ast
        steps = ast.literal_eval(steps)
    return TEMPLATE.format(
        steps=repr(steps),
        keyway_width=float(params.get("keyway_width", 0.0)),
        keyway_depth=float(params.get("keyway_depth", 0.0)),
        keyway_length=float(params.get("keyway_length", 0.0)),
        chamfer=float(params.get("chamfer", 0.5)),
        center_hole_d=float(params.get("center_hole_d", 0.0)),
    )
