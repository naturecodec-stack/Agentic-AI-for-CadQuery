NAME = "pcb_standoff"
DESCRIPTION = "Create PCB mounting standoffs — hollow hexagonal or round posts with threaded bore"
PARAMETERS = {
    "outer_diameter": {"type": "float", "default": 6.0,  "unit": "mm"},
    "height":         {"type": "float", "default": 10.0, "unit": "mm"},
    "bore_diameter":  {"type": "float", "default": 3.2,  "unit": "mm", "desc": "M3=3.2, M2.5=2.7, M2=2.2"},
    "shape":          {"type": "str",   "default": "hex", "desc": "hex | round"},
    "num_standoffs":  {"type": "int",   "default": 4},
    "pcb_width":      {"type": "float", "default": 60.0, "unit": "mm", "desc": "PCB width (for corner placement)"},
    "pcb_length":     {"type": "float", "default": 80.0, "unit": "mm"},
    "corner_inset":   {"type": "float", "default": 4.0,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

od     = {outer_diameter}
h      = {height}
bore   = {bore_diameter}
shape  = "{shape}"
n      = {num_standoffs}
pcb_w  = {pcb_width}
pcb_l  = {pcb_length}
inset  = {corner_inset}

def make_standoff(x, y):
    if shape == "hex":
        s = cq.Workplane("XY").polygon(6, od).extrude(h).translate((x, y, 0))
    else:
        s = cq.Workplane("XY").circle(od/2).extrude(h).translate((x, y, 0))
    if bore > 0:
        s = s.faces(">Z").workplane().hole(bore, depth=h)
    return s

if n == 1:
    positions = [(0, 0)]
elif n == 2:
    positions = [(-pcb_l/2 + inset, 0), (pcb_l/2 - inset, 0)]
else:
    positions = [
        (-pcb_l/2 + inset,  pcb_w/2 - inset),
        ( pcb_l/2 - inset,  pcb_w/2 - inset),
        (-pcb_l/2 + inset, -pcb_w/2 + inset),
        ( pcb_l/2 - inset, -pcb_w/2 + inset),
    ]

result = make_standoff(*positions[0])
for pos in positions[1:]:
    result = result.union(make_standoff(*pos))

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        outer_diameter=float(params.get("outer_diameter", 6.0)),
        height=float(params.get("height", 10.0)),
        bore_diameter=float(params.get("bore_diameter", 3.2)),
        shape=str(params.get("shape", "hex")),
        num_standoffs=int(params.get("num_standoffs", 4)),
        pcb_width=float(params.get("pcb_width", 60.0)),
        pcb_length=float(params.get("pcb_length", 80.0)),
        corner_inset=float(params.get("corner_inset", 4.0)),
    )
