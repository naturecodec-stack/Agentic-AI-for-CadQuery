NAME = "heat_sink"
DESCRIPTION = "Create a heat sink with parallel cooling fins on a base plate"
PARAMETERS = {
    "base_length":   {"type": "float", "default": 60.0, "unit": "mm"},
    "base_width":    {"type": "float", "default": 40.0, "unit": "mm"},
    "base_thickness":{"type": "float", "default": 5.0,  "unit": "mm"},
    "fin_height":    {"type": "float", "default": 20.0, "unit": "mm"},
    "fin_thickness": {"type": "float", "default": 2.0,  "unit": "mm"},
    "fin_gap":       {"type": "float", "default": 4.0,  "unit": "mm"},
    "fin_direction": {"type": "str",   "default": "length", "desc": "length | width"},
    "mount_holes":   {"type": "bool",  "default": True, "desc": "corner mounting holes"},
    "hole_diameter": {"type": "float", "default": 3.5,  "unit": "mm"},
    "hole_inset":    {"type": "float", "default": 5.0,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq
import math

bl = {base_length}
bw = {base_width}
bt = {base_thickness}
fh = {fin_height}
ft = {fin_thickness}
fg = {fin_gap}
fd = "{fin_direction}"
add_holes = {mount_holes}
hole_d = {hole_diameter}
inset  = {hole_inset}

# Base plate
result = cq.Workplane("XY").box(bl, bw, bt)

# Fins
if fd == "length":
    pitch = ft + fg
    num_fins = max(1, int(bw / pitch))
    total = num_fins * pitch - fg
    start = -total / 2 + ft / 2
    for i in range(num_fins):
        y = start + i * pitch
        fin = (cq.Workplane("XY")
            .box(bl, ft, fh)
            .translate((0, y, bt / 2 + fh / 2)))
        result = result.union(fin)
else:
    pitch = ft + fg
    num_fins = max(1, int(bl / pitch))
    total = num_fins * pitch - fg
    start = -total / 2 + ft / 2
    for i in range(num_fins):
        x = start + i * pitch
        fin = (cq.Workplane("XY")
            .box(ft, bw, fh)
            .translate((x, 0, bt / 2 + fh / 2)))
        result = result.union(fin)

# Mounting holes
if add_holes:
    result = (result
        .faces("<Z").workplane()
        .rect(bl - 2*inset, bw - 2*inset, forConstruction=True)
        .vertices()
        .hole(hole_d, depth=bt))

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        base_length=float(params.get("base_length", 60.0)),
        base_width=float(params.get("base_width", 40.0)),
        base_thickness=float(params.get("base_thickness", 5.0)),
        fin_height=float(params.get("fin_height", 20.0)),
        fin_thickness=float(params.get("fin_thickness", 2.0)),
        fin_gap=float(params.get("fin_gap", 4.0)),
        fin_direction=str(params.get("fin_direction", "length")),
        mount_holes=bool(params.get("mount_holes", True)),
        hole_diameter=float(params.get("hole_diameter", 3.5)),
        hole_inset=float(params.get("hole_inset", 5.0)),
    )
