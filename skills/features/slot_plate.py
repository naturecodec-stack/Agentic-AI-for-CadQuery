NAME = "slot_plate"
DESCRIPTION = "Create a plate with slotted holes (oblong slots) using slot2D — for adjustable mounting"
PARAMETERS = {
    "plate_length":  {"type": "float", "default": 100.0, "unit": "mm"},
    "plate_width":   {"type": "float", "default": 60.0,  "unit": "mm"},
    "plate_thickness":{"type":"float", "default": 6.0,   "unit": "mm"},
    "slot_length":   {"type": "float", "default": 20.0,  "unit": "mm"},
    "slot_diameter": {"type": "float", "default": 8.0,   "unit": "mm"},
    "slot_direction":{"type": "str",   "default": "X",   "desc": "X | Y — slot alignment axis"},
    "num_slots":     {"type": "int",   "default": 2},
    "slot_inset":    {"type": "float", "default": 15.0,  "unit": "mm"},
    "fillet_r":      {"type": "float", "default": 2.0,   "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

pl   = {plate_length}
pw   = {plate_width}
pt   = {plate_thickness}
sl   = {slot_length}
sd   = {slot_diameter}
sdir = "{slot_direction}"
n    = {num_slots}
inset = {slot_inset}
fil_r = {fillet_r}

result = cq.Workplane("XY").box(pl, pw, pt)

# Slot positions
if n == 1:
    positions = [(0, 0)]
elif n == 2:
    if sdir == "X":
        positions = [(0,  pw / 2 - inset), (0, -pw / 2 + inset)]
    else:
        positions = [( pl / 2 - inset, 0), (-pl / 2 + inset, 0)]
else:  # 4
    positions = [
        ( pl / 2 - inset,  pw / 2 - inset),
        (-pl / 2 + inset,  pw / 2 - inset),
        ( pl / 2 - inset, -pw / 2 + inset),
        (-pl / 2 + inset, -pw / 2 + inset),
    ]

angle = 0 if sdir == "X" else 90

for (x, y) in positions:
    result = (result
        .faces(">Z").workplane()
        .pushPoints([(x, y)])
        .slot2D(sl, sd, angle)
        .cutThruAll())

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
        plate_thickness=float(params.get("plate_thickness", 6.0)),
        slot_length=float(params.get("slot_length", 20.0)),
        slot_diameter=float(params.get("slot_diameter", 8.0)),
        slot_direction=str(params.get("slot_direction", "X")),
        num_slots=int(params.get("num_slots", 2)),
        slot_inset=float(params.get("slot_inset", 15.0)),
        fillet_r=float(params.get("fillet_r", 2.0)),
    )
