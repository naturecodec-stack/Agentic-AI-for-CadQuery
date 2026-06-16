NAME = "pocket"
DESCRIPTION = "Create a plate with one or more rectangular or circular pockets (blind cavities)"
PARAMETERS = {
    "plate_length":  {"type": "float", "default": 80.0,  "unit": "mm"},
    "plate_width":   {"type": "float", "default": 50.0,  "unit": "mm"},
    "plate_height":  {"type": "float", "default": 15.0,  "unit": "mm"},
    "pocket_length": {"type": "float", "default": 50.0,  "unit": "mm"},
    "pocket_width":  {"type": "float", "default": 30.0,  "unit": "mm"},
    "pocket_depth":  {"type": "float", "default": 8.0,   "unit": "mm"},
    "pocket_shape":  {"type": "str",   "default": "rect", "desc": "rect | circle"},
    "pocket_radius": {"type": "float", "default": 15.0,  "unit": "mm", "desc": "used when pocket_shape=circle"},
    "corner_radius": {"type": "float", "default": 0.0,   "unit": "mm", "desc": "fillet inside pocket corners (0=sharp)"},
    "num_pockets":   {"type": "int",   "default": 1,     "desc": "1 or 2 symmetric pockets"},
    "pocket_offset": {"type": "float", "default": 0.0,   "unit": "mm", "desc": "X offset for each pocket centre (used if num_pockets=2)"},
    "wall_holes":    {"type": "bool",  "default": False, "desc": "add mounting holes in corners"},
    "hole_d":        {"type": "float", "default": 5.0,   "unit": "mm"},
    "fillet_r":      {"type": "float", "default": 1.5,   "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

pl = {plate_length}
pw = {plate_width}
ph = {plate_height}
pkl = {pocket_length}
pkw = {pocket_width}
pkd = {pocket_depth}
pk_shape  = "{pocket_shape}"
pk_r      = {pocket_radius}
cr        = {corner_radius}
n_pockets = {num_pockets}
pk_off    = {pocket_offset}
add_holes = {wall_holes}
hole_d    = {hole_d}
fil_r     = {fillet_r}

# Base plate
result = cq.Workplane("XY").box(pl, pw, ph)

# Pocket(s)
offsets = [0] if n_pockets == 1 else [pk_off, -pk_off]
for xo in offsets:
    if pk_shape == "circle":
        pocket_solid = (
            cq.Workplane("XY")
            .cylinder(pkd, pk_r)
            .translate((xo, 0, ph / 2 - pkd / 2))
        )
    else:
        pocket_solid = (
            cq.Workplane("XY")
            .box(pkl, pkw, pkd)
            .translate((xo, 0, ph / 2 - pkd / 2))
        )
    result = result.cut(pocket_solid)

# Fillet pocket bottom edges
if cr > 0 and pk_shape == "rect":
    try:
        result = result.edges("<Z").fillet(cr)
    except Exception:
        pass

# Corner mounting holes
if add_holes:
    inset = 8.0
    result = (
        result.faces(">Z").workplane()
        .rect(pl - 2*inset, pw - 2*inset, forConstruction=True)
        .vertices()
        .hole(hole_d)
    )

# Outer edge fillet
if fil_r > 0:
    try:
        result = result.edges("|Z").fillet(fil_r)
    except Exception:
        pass

show_object(result)
"""


def render(params: dict) -> str:
    return TEMPLATE.format(
        plate_length=float(params.get("plate_length", 80.0)),
        plate_width=float(params.get("plate_width", 50.0)),
        plate_height=float(params.get("plate_height", 15.0)),
        pocket_length=float(params.get("pocket_length", 50.0)),
        pocket_width=float(params.get("pocket_width", 30.0)),
        pocket_depth=float(params.get("pocket_depth", 8.0)),
        pocket_shape=str(params.get("pocket_shape", "rect")),
        pocket_radius=float(params.get("pocket_radius", 15.0)),
        corner_radius=float(params.get("corner_radius", 0.0)),
        num_pockets=int(params.get("num_pockets", 1)),
        pocket_offset=float(params.get("pocket_offset", 0.0)),
        wall_holes=bool(params.get("wall_holes", False)),
        hole_d=float(params.get("hole_d", 5.0)),
        fillet_r=float(params.get("fillet_r", 1.5)),
    )
