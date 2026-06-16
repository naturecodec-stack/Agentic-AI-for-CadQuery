NAME = "lidded_box"
DESCRIPTION = "Create a hollow shell box with a separate snap-fit or friction lid"
PARAMETERS = {
    "length":        {"type": "float", "default": 80.0, "unit": "mm"},
    "width":         {"type": "float", "default": 50.0, "unit": "mm"},
    "height":        {"type": "float", "default": 40.0, "unit": "mm"},
    "wall_thickness":{"type": "float", "default": 2.5,  "unit": "mm"},
    "lid_height":    {"type": "float", "default": 8.0,  "unit": "mm"},
    "lid_fit":       {"type": "float", "default": 0.3,  "unit": "mm", "desc": "clearance gap between lid and box"},
    "fillet_r":      {"type": "float", "default": 2.0,  "unit": "mm"},
    "show_separate": {"type": "bool",  "default": True,  "desc": "True=show box and lid side by side"},
}

TEMPLATE = """import cadquery as cq

l    = {length}
w    = {width}
h    = {height}
wt   = {wall_thickness}
lh   = {lid_height}
fit  = {lid_fit}
fr   = {fillet_r}
sep  = {show_separate}

# Box body — open top using shell
box = (cq.Workplane("XY")
    .box(l, w, h)
    .faces(">Z")
    .shell(-wt))

# Lid — fits over the outside of box top
lid_outer_l = l + wt * 2 - fit * 2
lid_outer_w = w + wt * 2 - fit * 2
lid_inner_l = l - fit * 2
lid_inner_w = w - fit * 2

lid = (cq.Workplane("XY")
    .box(lid_outer_l, lid_outer_w, lh))
lid_cut = (cq.Workplane("XY")
    .box(lid_inner_l, lid_inner_w, lh - wt)
    .translate((0, 0, -wt / 2)))
lid = lid.cut(lid_cut)

if fr > 0:
    try:
        box = box.edges("|Z").fillet(fr)
    except Exception:
        pass
    try:
        lid = lid.edges("|Z").fillet(fr)
    except Exception:
        pass

if sep:
    result = cq.Assembly()
    result.add(box, name="box",  loc=cq.Location((0,          0, 0)))
    result.add(lid, name="lid",  loc=cq.Location((l + 20, 0, 0)))
else:
    result = cq.Assembly()
    result.add(box, name="box")
    result.add(lid, name="lid", loc=cq.Location((0, 0, h)))

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        length=float(params.get("length", 80.0)),
        width=float(params.get("width", 50.0)),
        height=float(params.get("height", 40.0)),
        wall_thickness=float(params.get("wall_thickness", 2.5)),
        lid_height=float(params.get("lid_height", 8.0)),
        lid_fit=float(params.get("lid_fit", 0.3)),
        fillet_r=float(params.get("fillet_r", 2.0)),
        show_separate=bool(params.get("show_separate", True)),
    )
