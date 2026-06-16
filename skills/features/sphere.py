NAME = "sphere"
DESCRIPTION = "Create a sphere or partial sphere (dome)"
PARAMETERS = {
    "radius":    {"type": "float", "default": 25.0, "unit": "mm"},
    "angle1":    {"type": "float", "default": -90.0, "desc": "start latitude angle (-90 = full bottom)"},
    "angle2":    {"type": "float", "default":  90.0, "desc": "end latitude angle (90 = full top)"},
}

TEMPLATE = """import cadquery as cq

radius = {radius}
angle1 = {angle1}
angle2 = {angle2}

result = cq.Workplane("XY").sphere(radius, angle1=angle1, angle2=angle2)
show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        radius=float(params.get("radius", 25.0)),
        angle1=float(params.get("angle1", -90.0)),
        angle2=float(params.get("angle2",  90.0)),
    )
