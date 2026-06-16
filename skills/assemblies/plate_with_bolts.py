NAME = "plate_with_bolts"
DESCRIPTION = "Create a rectangular plate with corner mounting holes sized for bolts, plus an assembly with the bolts placed"
PARAMETERS = {"plate_l": {"type": "float", "default": 80.0}, "plate_w": {"type": "float", "default": 60.0}, "plate_h": {"type": "float", "default": 6.0}, "hole_diameter": {"type": "float", "default": 6.5}, "edge_margin": {"type": "float", "default": 10.0}}
TEMPLATE = """import cadquery as cq

l = {plate_l}
w = {plate_w}
m = {edge_margin}

points = [
    (-l/2 + m, -w/2 + m),
    ( l/2 - m, -w/2 + m),
    (-l/2 + m,  w/2 - m),
    ( l/2 - m,  w/2 - m),
]

result = (
    cq.Workplane("XY")
    .box(l, w, {plate_h})
    .faces(">Z")
    .workplane()
    .pushPoints(points)
    .hole({hole_diameter})
)
show_object(result)
"""
def render(p): return TEMPLATE.format(plate_l=p.get("plate_l",80.0), plate_w=p.get("plate_w",60.0), plate_h=p.get("plate_h",6.0), hole_diameter=p.get("hole_diameter",6.5), edge_margin=p.get("edge_margin",10.0))
