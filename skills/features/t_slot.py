NAME = "t_slot"
DESCRIPTION = "Create a T-slot aluminium extrusion profile (like 2020/3030/4040 frames)"
PARAMETERS = {
    "size":      {"type": "float", "default": 20.0, "unit": "mm", "desc": "outer width and height (20=2020, 30=3030, 40=4040)"},
    "length":    {"type": "float", "default": 100.0,"unit": "mm"},
    "slot_w":    {"type": "float", "default": 6.0,  "unit": "mm", "desc": "slot opening width"},
    "slot_d":    {"type": "float", "default": 5.5,  "unit": "mm", "desc": "slot depth"},
    "head_w":    {"type": "float", "default": 10.0, "unit": "mm", "desc": "T-head width inside slot"},
    "num_sides": {"type": "int",   "default": 4,    "desc": "number of sides with slots (1–4)"},
    "center_bore":{"type": "float","default": 4.2,  "unit": "mm", "desc": "central bore diameter (0 = none)"},
}

TEMPLATE = """import cadquery as cq

sz    = {size}
ln    = {length}
sw    = {slot_w}
sd    = {slot_d}
hw    = {head_w}
sides = {num_sides}
bore  = {center_bore}

# Outer square body
result = cq.Workplane("XY").box(sz, sz, ln)

# Cut T-slots on each requested side
slot_configs = [
    (">Y", (0,  sz/2, 0)),   # front
    ("<Y", (0, -sz/2, 0)),   # back
    (">X", ( sz/2, 0, 0)),   # right
    ("<X", (-sz/2, 0, 0)),   # left
]

for i, (face_sel, _) in enumerate(slot_configs[:sides]):
    # Opening channel
    opening = (cq.Workplane("XY")
        .box(sw, sd, ln)
        .translate((0 if "X" not in face_sel else (sz/2 - sd/2) * (1 if ">" in face_sel else -1),
                    0 if "Y" not in face_sel else (sz/2 - sd/2) * (1 if ">" in face_sel else -1),
                    0)))
    # T-head channel
    head = (cq.Workplane("XY")
        .box(hw, sd * 0.5, ln)
        .translate((0 if "X" not in face_sel else (sz/2 - sd * 0.75) * (1 if ">" in face_sel else -1),
                    0 if "Y" not in face_sel else (sz/2 - sd * 0.75) * (1 if ">" in face_sel else -1),
                    0)))
    result = result.cut(opening).cut(head)

# Central bore
if bore > 0:
    result = result.faces(">Z").workplane().hole(bore, depth=ln)

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        size=float(params.get("size", 20.0)),
        length=float(params.get("length", 100.0)),
        slot_w=float(params.get("slot_w", 6.0)),
        slot_d=float(params.get("slot_d", 5.5)),
        head_w=float(params.get("head_w", 10.0)),
        num_sides=int(params.get("num_sides", 4)),
        center_bore=float(params.get("center_bore", 4.2)),
    )
