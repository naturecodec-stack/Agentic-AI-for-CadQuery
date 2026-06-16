NAME = "flange_bolt_pattern"
DESCRIPTION = "Create a circular flange plate with a polar pattern of bolt holes sized for a given fastener"
PARAMETERS = {"flange_radius": {"type": "float", "default": 50.0}, "flange_height": {"type": "float", "default": 10.0}, "bolt_hole_diameter": {"type": "float", "default": 8.5}, "bolt_circle_radius": {"type": "float", "default": 35.0}, "bolt_count": {"type": "int", "default": 6}}
TEMPLATE = """import cadquery as cq

result = (
    cq.Workplane("XY")
    .circle({flange_radius})
    .extrude({flange_height})
    .faces(">Z")
    .workplane()
    .polarArray({bolt_circle_radius}, 0, 360, {bolt_count})
    .hole({bolt_hole_diameter})
)
show_object(result)
"""
def render(p): return TEMPLATE.format(flange_radius=p.get("flange_radius",50.0), flange_height=p.get("flange_height",10.0), bolt_hole_diameter=p.get("bolt_hole_diameter",8.5), bolt_circle_radius=p.get("bolt_circle_radius",35.0), bolt_count=p.get("bolt_count",6))
