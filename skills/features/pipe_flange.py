NAME = "pipe_flange"
DESCRIPTION = "Create a pipe section with flanges at both ends for bolted pipe connections"
PARAMETERS = {
    "pipe_od":        {"type": "float", "default": 40.0, "unit": "mm", "desc": "pipe outer diameter"},
    "pipe_id":        {"type": "float", "default": 32.0, "unit": "mm", "desc": "pipe inner diameter"},
    "pipe_length":    {"type": "float", "default": 80.0, "unit": "mm"},
    "flange_od":      {"type": "float", "default": 80.0, "unit": "mm"},
    "flange_thickness":{"type":"float", "default": 8.0,  "unit": "mm"},
    "num_bolt_holes": {"type": "int",   "default": 4},
    "bolt_hole_d":    {"type": "float", "default": 8.5,  "unit": "mm"},
    "bolt_circle_d":  {"type": "float", "default": 65.0, "unit": "mm"},
    "both_ends":      {"type": "bool",  "default": True, "desc": "flange on both ends"},
}

TEMPLATE = """import cadquery as cq
import math

pod  = {pipe_od}
pid  = {pipe_id}
pl   = {pipe_length}
fod  = {flange_od}
ft   = {flange_thickness}
nbh  = {num_bolt_holes}
bhd  = {bolt_hole_d}
bcd  = {bolt_circle_d}
both = {both_ends}

# Pipe body
pipe = (cq.Workplane("XY")
    .circle(pod / 2).extrude(pl))
bore = (cq.Workplane("XY")
    .circle(pid / 2).extrude(pl))
result = pipe.cut(bore)

# Bolt hole positions on flange
pts = [(bcd / 2 * math.cos(math.radians(360 * i / nbh)),
        bcd / 2 * math.sin(math.radians(360 * i / nbh))) for i in range(nbh)]

def make_flange(z_pos):
    fl = (cq.Workplane("XY")
        .circle(fod / 2)
        .extrude(ft)
        .translate((0, 0, z_pos)))
    bore_fl = (cq.Workplane("XY")
        .circle(pid / 2)
        .extrude(ft)
        .translate((0, 0, z_pos)))
    fl = fl.cut(bore_fl)
    fl = (fl.faces(">Z" if z_pos >= 0 else "<Z").workplane()
        .pushPoints(pts)
        .hole(bhd, depth=ft))
    return fl

result = result.union(make_flange(-ft))
if both:
    result = result.union(make_flange(pl))

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        pipe_od=float(params.get("pipe_od", 40.0)),
        pipe_id=float(params.get("pipe_id", 32.0)),
        pipe_length=float(params.get("pipe_length", 80.0)),
        flange_od=float(params.get("flange_od", 80.0)),
        flange_thickness=float(params.get("flange_thickness", 8.0)),
        num_bolt_holes=int(params.get("num_bolt_holes", 4)),
        bolt_hole_d=float(params.get("bolt_hole_d", 8.5)),
        bolt_circle_d=float(params.get("bolt_circle_d", 65.0)),
        both_ends=bool(params.get("both_ends", True)),
    )
