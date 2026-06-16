NAME = "rib"
DESCRIPTION = "Create a flat plate with stiffening ribs on one or both sides"
PARAMETERS = {
    "plate_length":  {"type": "float", "default": 100.0, "unit": "mm"},
    "plate_width":   {"type": "float", "default": 60.0,  "unit": "mm"},
    "plate_thickness":{"type": "float","default": 4.0,   "unit": "mm"},
    "rib_height":    {"type": "float", "default": 12.0,  "unit": "mm"},
    "rib_thickness": {"type": "float", "default": 3.0,   "unit": "mm"},
    "num_ribs":      {"type": "int",   "default": 3,     "desc": "number of ribs along length"},
    "rib_direction": {"type": "str",   "default": "length", "desc": "length | width | cross"},
    "fillet_r":      {"type": "float", "default": 1.0,   "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

pl = {plate_length}
pw = {plate_width}
pt = {plate_thickness}
rh = {rib_height}
rt = {rib_thickness}
n  = {num_ribs}
direction = "{rib_direction}"
fil_r = {fillet_r}

# Base plate
result = cq.Workplane("XY").box(pl, pw, pt)

# Ribs
if direction in ("length", "cross"):
    spacing = pw / (n + 1)
    for i in range(1, n + 1):
        y_pos = -pw / 2 + i * spacing
        rib = (cq.Workplane("XY")
            .box(pl, rt, rh)
            .translate((0, y_pos, pt / 2 + rh / 2)))
        result = result.union(rib)

if direction in ("width", "cross"):
    spacing = pl / (n + 1)
    for i in range(1, n + 1):
        x_pos = -pl / 2 + i * spacing
        rib = (cq.Workplane("XY")
            .box(rt, pw, rh)
            .translate((x_pos, 0, pt / 2 + rh / 2)))
        result = result.union(rib)

if fil_r > 0:
    try:
        result = result.edges("|Z").fillet(fil_r)
    except Exception:
        pass

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        plate_length=float(params.get("plate_length", 100.0)),
        plate_width=float(params.get("plate_width", 60.0)),
        plate_thickness=float(params.get("plate_thickness", 4.0)),
        rib_height=float(params.get("rib_height", 12.0)),
        rib_thickness=float(params.get("rib_thickness", 3.0)),
        num_ribs=int(params.get("num_ribs", 3)),
        rib_direction=str(params.get("rib_direction", "length")),
        fillet_r=float(params.get("fillet_r", 1.0)),
    )
