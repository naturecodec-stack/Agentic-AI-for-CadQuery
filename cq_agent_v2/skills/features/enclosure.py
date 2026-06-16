NAME = "enclosure"
DESCRIPTION = "Create a hollow rectangular enclosure (open-top box) with optional lid slots, mounting bosses, and vent holes"
PARAMETERS = {
    "outer_length":  {"type": "float", "default": 100.0, "unit": "mm"},
    "outer_width":   {"type": "float", "default": 60.0,  "unit": "mm"},
    "outer_height":  {"type": "float", "default": 40.0,  "unit": "mm"},
    "wall_thickness":{"type": "float", "default": 2.5,   "unit": "mm"},
    "boss_diameter": {"type": "float", "default": 6.0,   "unit": "mm", "desc": "mounting boss OD (0 = no bosses)"},
    "boss_hole":     {"type": "float", "default": 3.2,   "unit": "mm", "desc": "boss screw hole diameter"},
    "boss_inset":    {"type": "float", "default": 8.0,   "unit": "mm"},
    "fillet_r":      {"type": "float", "default": 3.0,   "unit": "mm"},
    "lid_slot_depth":{"type": "float", "default": 0.0,   "unit": "mm", "desc": "lid groove depth (0 = none)"},
}

TEMPLATE = """import cadquery as cq

ol = {outer_length}
ow = {outer_width}
oh = {outer_height}
wt = {wall_thickness}
bd = {boss_diameter}
bh = {boss_hole}
bi = {boss_inset}
fr = {fillet_r}
ls = {lid_slot_depth}

# Outer shell — open top
outer = cq.Workplane("XY").box(ol, ow, oh)
inner = cq.Workplane("XY").box(ol - 2*wt, ow - 2*wt, oh - wt).translate((0, 0, wt / 2))
body  = outer.cut(inner)

# Optional lid groove (slot around top rim)
if ls > 0:
    slot_outer = cq.Workplane("XY").box(ol - wt, ow - wt, ls).translate((0, 0, oh/2 - ls/2))
    slot_inner = cq.Workplane("XY").box(ol - 3*wt, ow - 3*wt, ls).translate((0, 0, oh/2 - ls/2))
    groove = slot_outer.cut(slot_inner)
    body = body.cut(groove)

# Optional corner mounting bosses (inside corners)
if bd > 0:
    corners = [
        ( ol/2 - bi,  ow/2 - bi),
        (-ol/2 + bi,  ow/2 - bi),
        ( ol/2 - bi, -ow/2 + bi),
        (-ol/2 + bi, -ow/2 + bi),
    ]
    for cx, cy in corners:
        boss = (
            cq.Workplane("XY")
            .cylinder(oh - wt, bd / 2)
            .translate((cx, cy, wt / 2))
        )
        body = body.union(boss)

    # Drill boss holes
    for cx, cy in corners:
        hole_cyl = (
            cq.Workplane("XY")
            .cylinder(oh, bh / 2)
            .translate((cx, cy, oh / 2))
        )
        body = body.cut(hole_cyl)

# Fillet outer vertical edges
if fr > 0:
    try:
        body = body.edges("|Z").fillet(fr)
    except Exception:
        pass

result = body
show_object(result)
"""


def render(params: dict) -> str:
    return TEMPLATE.format(
        outer_length=float(params.get("outer_length", 100.0)),
        outer_width=float(params.get("outer_width", 60.0)),
        outer_height=float(params.get("outer_height", 40.0)),
        wall_thickness=float(params.get("wall_thickness", 2.5)),
        boss_diameter=float(params.get("boss_diameter", 6.0)),
        boss_hole=float(params.get("boss_hole", 3.2)),
        boss_inset=float(params.get("boss_inset", 8.0)),
        fillet_r=float(params.get("fillet_r", 3.0)),
        lid_slot_depth=float(params.get("lid_slot_depth", 0.0)),
    )
