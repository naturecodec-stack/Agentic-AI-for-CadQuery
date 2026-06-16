NAME = "bevel_gear"
DESCRIPTION = "Create a bevel gear using cq_gears — transfers rotation between intersecting shafts"
PARAMETERS = {
    "module":        {"type": "float", "default": 1.0},
    "teeth_number":  {"type": "int",   "default": 20},
    "width":         {"type": "float", "default": 6.0,  "unit": "mm"},
    "cone_angle":    {"type": "float", "default": 45.0, "desc": "cone half-angle (45=miter gear, 90=crown)"},
    "pressure_angle":{"type": "float", "default": 20.0, "desc": "pressure angle in degrees"},
    "bore_d":        {"type": "float", "default": 5.0,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

try:
    from cq_gears import BevelGear
except ImportError:
    raise ImportError("cq_gears not installed. Run: pip install cq_gears")

module         = {module}
teeth_number   = {teeth_number}
width          = {width}
cone_angle     = {cone_angle}
pressure_angle = {pressure_angle}
bore_d         = {bore_d}

gear = BevelGear(
    module=module,
    teeth_number=teeth_number,
    width=width,
    cone_angle=cone_angle,
    pressure_angle=pressure_angle,
    bore_d=bore_d,
)
result = gear.build()
show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        module=float(params.get("module", 1.0)),
        teeth_number=int(params.get("teeth_number", 20)),
        width=float(params.get("width", 6.0)),
        cone_angle=float(params.get("cone_angle", 45.0)),
        pressure_angle=float(params.get("pressure_angle", 20.0)),
        bore_d=float(params.get("bore_d", 5.0)),
    )
