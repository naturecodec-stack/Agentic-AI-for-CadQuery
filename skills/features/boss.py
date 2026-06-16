NAME = "boss"
DESCRIPTION = "Create a flat plate with one or more cylindrical bosses (raised mounting posts)"
PARAMETERS = {
    "plate_length":  {"type": "float", "default": 80.0,  "unit": "mm"},
    "plate_width":   {"type": "float", "default": 60.0,  "unit": "mm"},
    "plate_thickness":{"type":"float", "default": 4.0,   "unit": "mm"},
    "boss_diameter": {"type": "float", "default": 12.0,  "unit": "mm"},
    "boss_height":   {"type": "float", "default": 8.0,   "unit": "mm"},
    "bore_diameter": {"type": "float", "default": 4.0,   "unit": "mm", "desc": "through-hole in boss (0 = solid)"},
    "num_bosses":    {"type": "int",   "default": 4,     "desc": "1, 2, or 4"},
    "boss_inset":    {"type": "float", "default": 15.0,  "unit": "mm", "desc": "distance from edge to boss centre"},
    "fillet_r":      {"type": "float", "default": 1.0,   "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

pl = {plate_length}
pw = {plate_width}
pt = {plate_thickness}
bd = {boss_diameter}
bh = {boss_height}
bore = {bore_diameter}
n  = {num_bosses}
inset = {boss_inset}
fil_r = {fillet_r}

result = cq.Workplane("XY").box(pl, pw, pt)

# Boss positions
if n == 1:
    positions = [(0, 0)]
elif n == 2:
    positions = [(pl/2 - inset, 0), (-(pl/2 - inset), 0)]
else:  # 4
    positions = [
        ( pl/2 - inset,  pw/2 - inset),
        (-pl/2 + inset,  pw/2 - inset),
        ( pl/2 - inset, -pw/2 + inset),
        (-pl/2 + inset, -pw/2 + inset),
    ]

for (x, y) in positions:
    boss = (cq.Workplane("XY")
        .circle(bd / 2)
        .extrude(bh)
        .translate((x, y, pt / 2)))
    result = result.union(boss)

if bore > 0:
    for (x, y) in positions:
        result = (result
            .faces(">Z").workplane()
            .pushPoints([(x, y)])
            .hole(bore))

if fil_r > 0:
    try:
        result = result.edges("|Z").fillet(fil_r)
    except Exception:
        pass

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        plate_length=float(params.get("plate_length", 80.0)),
        plate_width=float(params.get("plate_width", 60.0)),
        plate_thickness=float(params.get("plate_thickness", 4.0)),
        boss_diameter=float(params.get("boss_diameter", 12.0)),
        boss_height=float(params.get("boss_height", 8.0)),
        bore_diameter=float(params.get("bore_diameter", 4.0)),
        num_bosses=int(params.get("num_bosses", 4)),
        boss_inset=float(params.get("boss_inset", 15.0)),
        fillet_r=float(params.get("fillet_r", 1.0)),
    )
