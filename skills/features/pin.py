NAME = "pin"
DESCRIPTION = "Create a dowel pin, locating pin, or spring pin for alignment and assembly"
PARAMETERS = {
    "diameter":      {"type": "float", "default": 6.0,  "unit": "mm"},
    "length":        {"type": "float", "default": 30.0, "unit": "mm"},
    "chamfer":       {"type": "float", "default": 0.5,  "unit": "mm", "desc": "lead-in chamfer on ends"},
    "head":          {"type": "bool",  "default": False, "desc": "add a flange head"},
    "head_diameter": {"type": "float", "default": 10.0, "unit": "mm"},
    "head_thickness":{"type": "float", "default": 3.0,  "unit": "mm"},
    "hollow":        {"type": "bool",  "default": False, "desc": "hollow spring pin"},
    "wall_thickness":{"type": "float", "default": 1.0,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

d   = {diameter}
ln  = {length}
ch  = {chamfer}
head      = {head}
head_d    = {head_diameter}
head_t    = {head_thickness}
hollow    = {hollow}
wall_t    = {wall_thickness}

result = cq.Workplane("XY").circle(d / 2).extrude(ln)

if hollow:
    bore = cq.Workplane("XY").circle(d / 2 - wall_t).extrude(ln)
    result = result.cut(bore)

if ch > 0:
    try:
        result = result.faces(">Z").chamfer(ch)
        result = result.faces("<Z").chamfer(ch)
    except Exception:
        pass

if head:
    flange = (cq.Workplane("XY")
        .circle(head_d / 2)
        .extrude(head_t)
        .translate((0, 0, -head_t)))
    result = result.union(flange)

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        diameter=float(params.get("diameter", 6.0)),
        length=float(params.get("length", 30.0)),
        chamfer=float(params.get("chamfer", 0.5)),
        head=bool(params.get("head", False)),
        head_diameter=float(params.get("head_diameter", 10.0)),
        head_thickness=float(params.get("head_thickness", 3.0)),
        hollow=bool(params.get("hollow", False)),
        wall_thickness=float(params.get("wall_thickness", 1.0)),
    )
