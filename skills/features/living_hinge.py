NAME = "living_hinge"
DESCRIPTION = "Create a flat plate with a living hinge — thin flexible section for 3D-printed hinged parts"
PARAMETERS = {
    "panel_length":   {"type": "float", "default": 60.0, "unit": "mm", "desc": "length of each rigid panel"},
    "panel_width":    {"type": "float", "default": 40.0, "unit": "mm"},
    "panel_thickness":{"type": "float", "default": 3.0,  "unit": "mm"},
    "hinge_length":   {"type": "float", "default": 8.0,  "unit": "mm", "desc": "length of flexible hinge zone"},
    "hinge_thickness":{"type": "float", "default": 0.6,  "unit": "mm", "desc": "thin wall thickness (0.4–0.8mm)"},
    "num_hinges":     {"type": "int",   "default": 1,    "desc": "number of hinges (panels = num_hinges + 1)"},
}

TEMPLATE = """import cadquery as cq

pl  = {panel_length}
pw  = {panel_width}
pt  = {panel_thickness}
hl  = {hinge_length}
ht  = {hinge_thickness}
nh  = {num_hinges}

num_panels = nh + 1
total_length = num_panels * pl + nh * hl

result = None
x_pos = -total_length / 2

for i in range(num_panels):
    panel = (cq.Workplane("XY")
        .box(pl, pw, pt)
        .translate((x_pos + pl / 2, 0, 0)))
    result = result.union(panel) if result else panel
    x_pos += pl

    if i < nh:
        hinge = (cq.Workplane("XY")
            .box(hl, pw, ht)
            .translate((x_pos + hl / 2, 0, 0)))
        result = result.union(hinge)
        x_pos += hl

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        panel_length=float(params.get("panel_length", 60.0)),
        panel_width=float(params.get("panel_width", 40.0)),
        panel_thickness=float(params.get("panel_thickness", 3.0)),
        hinge_length=float(params.get("hinge_length", 8.0)),
        hinge_thickness=float(params.get("hinge_thickness", 0.6)),
        num_hinges=int(params.get("num_hinges", 1)),
    )
