NAME = "bracket"
DESCRIPTION = "Create an L-shaped or T-shaped mounting bracket with optional gusset and mounting holes"
PARAMETERS = {
    "base_length":   {"type": "float", "default": 80.0,  "unit": "mm"},
    "base_width":    {"type": "float", "default": 40.0,  "unit": "mm"},
    "base_thickness":{"type": "float", "default": 5.0,   "unit": "mm"},
    "wall_height":   {"type": "float", "default": 40.0,  "unit": "mm"},
    "wall_thickness":{"type": "float", "default": 5.0,   "unit": "mm"},
    "hole_diameter": {"type": "float", "default": 5.0,   "unit": "mm"},
    "hole_inset":    {"type": "float", "default": 10.0,  "unit": "mm", "desc": "distance from edge to hole centre"},
    "num_base_holes":{"type": "int",   "default": 2,     "desc": "holes in base plate (2 or 4)"},
    "num_wall_holes":{"type": "int",   "default": 2,     "desc": "holes in wall (0, 2, or 4)"},
    "fillet_r":      {"type": "float", "default": 2.0,   "unit": "mm", "desc": "edge fillet radius (0 = none)"},
    "gusset":        {"type": "bool",  "default": False, "desc": "add triangular gusset at inside corner"},
}

TEMPLATE = """import cadquery as cq

base_l  = {base_length}
base_w  = {base_width}
base_t  = {base_thickness}
wall_h  = {wall_height}
wall_t  = {wall_thickness}
hole_d  = {hole_diameter}
inset   = {hole_inset}
n_base  = {num_base_holes}
n_wall  = {num_wall_holes}
fil_r   = {fillet_r}
gusset  = {gusset}

# Base plate
base = cq.Workplane("XY").box(base_l, base_w, base_t).translate((0, 0, base_t / 2))

# Vertical wall (joins at back edge of base)
wall = (
    cq.Workplane("XY")
    .box(wall_t, base_w, wall_h)
    .translate((-(base_l / 2 - wall_t / 2), 0, base_t + wall_h / 2))
)

body = base.union(wall)

# Optional gusset (triangle in the inside corner)
if gusset:
    gusset_pts = [
        (0, 0),
        (min(base_l * 0.4, 30), 0),
        (0, min(wall_h * 0.4, 20)),
    ]
    g = (
        cq.Workplane("XZ")
        .polyline(gusset_pts).close()
        .extrude(base_w)
        .translate((-(base_l / 2 - wall_t), -base_w / 2, base_t))
    )
    body = body.union(g)

# Mounting holes — base plate
if n_base >= 2:
    x_pos = base_l / 2 - inset
    body = (
        body.faces(">Z").workplane(origin=(0, 0, base_t))
        .pushPoints([(x_pos - (base_l - 2*inset) * (i / max(n_base-1,1)), 0) for i in range(n_base)])
        .hole(hole_d)
    ) if n_base > 1 else (
        body.faces(">Z").workplane(origin=(0, 0, base_t))
        .pushPoints([(0, 0)])
        .hole(hole_d)
    )

# Mounting holes — wall
if n_wall >= 2:
    x_off = -(base_l / 2 - wall_t / 2)
    y_positions = [base_w / 2 - inset - (base_w - 2*inset) * i / max(n_wall-1,1) for i in range(n_wall)]
    body = (
        body.faces("<X").workplane()
        .pushPoints([(y, base_t + wall_h / 2) for y in y_positions])
        .hole(hole_d)
    )

# Fillet
if fil_r > 0:
    try:
        body = body.edges("|Z").fillet(fil_r)
    except Exception:
        pass  # skip if fillet fails on complex geometry

result = body
show_object(result)
"""


def render(params: dict) -> str:
    return TEMPLATE.format(
        base_length=float(params.get("base_length", 80.0)),
        base_width=float(params.get("base_width", 40.0)),
        base_thickness=float(params.get("base_thickness", 5.0)),
        wall_height=float(params.get("wall_height", 40.0)),
        wall_thickness=float(params.get("wall_thickness", 5.0)),
        hole_diameter=float(params.get("hole_diameter", 5.0)),
        hole_inset=float(params.get("hole_inset", 10.0)),
        num_base_holes=int(params.get("num_base_holes", 2)),
        num_wall_holes=int(params.get("num_wall_holes", 2)),
        fillet_r=float(params.get("fillet_r", 2.0)),
        gusset=bool(params.get("gusset", False)),
    )
