NAME = "wedge"
DESCRIPTION = "Create a wedge, ramp, door stop, or tapered block using CadQuery wedge primitive"
PARAMETERS = {
    "length":     {"type": "float", "default": 80.0, "unit": "mm"},
    "height":     {"type": "float", "default": 30.0, "unit": "mm"},
    "width":      {"type": "float", "default": 40.0, "unit": "mm"},
    "top_length": {"type": "float", "default": 0.0,  "unit": "mm", "desc": "top face length (0=sharp edge)"},
    "fillet_r":   {"type": "float", "default": 1.0,  "unit": "mm"},
    "mount_holes":{"type": "bool",  "default": False},
    "hole_d":     {"type": "float", "default": 4.5,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

l      = {length}
h      = {height}
w      = {width}
top_l  = {top_length}
fil_r  = {fillet_r}
holes  = {mount_holes}
hole_d = {hole_d}

# wedge(dx, dy, dz, xmin, zmin, xmax, zmax)
# dx=length, dy=width, dz=height
# xmin/zmin = bottom face X/Z start, xmax/zmax = top face X/Z end
result = cq.Workplane("XY").wedge(l, w, h, 0, 0, top_l, w)

if fil_r > 0:
    try:
        result = result.edges("|Y").fillet(fil_r)
    except Exception:
        pass

if holes:
    inset = 12.0
    result = (result
        .faces("<Z").workplane()
        .pushPoints([( l/2 - inset, w/2 - inset),
                     (-l/2 + inset, w/2 - inset),
                     ( l/2 - inset,-w/2 + inset),
                     (-l/2 + inset,-w/2 + inset)])
        .hole(hole_d, depth=min(h * 0.6, 15)))

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        length=float(params.get("length", 80.0)),
        height=float(params.get("height", 30.0)),
        width=float(params.get("width", 40.0)),
        top_length=float(params.get("top_length", 0.0)),
        fillet_r=float(params.get("fillet_r", 1.0)),
        mount_holes=bool(params.get("mount_holes", False)),
        hole_d=float(params.get("hole_d", 4.5)),
    )
