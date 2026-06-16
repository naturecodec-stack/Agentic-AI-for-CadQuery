NAME = "hex_prism"
DESCRIPTION = "Create a hexagonal prism — for hex bolt heads, sockets, nuts, hex adapters"
PARAMETERS = {
    "diameter":  {"type": "float", "default": 20.0, "unit": "mm", "desc": "across-flats diameter"},
    "height":    {"type": "float", "default": 15.0, "unit": "mm"},
    "bore_d":    {"type": "float", "default": 0.0,  "unit": "mm", "desc": "central through-hole diameter (0 = none)"},
    "fillet_r":  {"type": "float", "default": 0.5,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

diameter = {diameter}
height   = {height}
bore_d   = {bore_d}
fillet_r = {fillet_r}

result = cq.Workplane("XY").polygon(6, diameter).extrude(height)

if bore_d > 0:
    result = result.faces(">Z").workplane().hole(bore_d)

if fillet_r > 0:
    try:
        result = result.edges("|Z").fillet(fillet_r)
    except Exception:
        pass

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        diameter=float(params.get("diameter", 20.0)),
        height=float(params.get("height", 15.0)),
        bore_d=float(params.get("bore_d", 0.0)),
        fillet_r=float(params.get("fillet_r", 0.5)),
    )
