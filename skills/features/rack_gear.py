NAME = "rack_gear"
DESCRIPTION = "Create a linear rack gear using cq_gears — mates with a spur or helical gear"
PARAMETERS = {
    "module":         {"type": "float", "default": 1.0},
    "teeth_number":   {"type": "int",   "default": 20, "desc": "number of rack teeth"},
    "width":          {"type": "float", "default": 6.0,  "unit": "mm", "desc": "face width"},
    "height":         {"type": "float", "default": 8.0,  "unit": "mm", "desc": "rack body height"},
    "pressure_angle": {"type": "float", "default": 20.0},
    "helix_angle":    {"type": "float", "default": 0.0, "desc": "0 = straight rack, >0 = helical rack"},
}

TEMPLATE = """import cadquery as cq

try:
    from cq_gears import RackGear
except ImportError:
    raise ImportError("cq_gears not installed. Run: pip install cq_gears")

module         = {module}
teeth_number   = {teeth_number}
width          = {width}
height         = {height}
pressure_angle = {pressure_angle}
helix_angle    = {helix_angle}

gear = RackGear(
    module=module,
    teeth_number=teeth_number,
    width=width,
    height=height,
    pressure_angle=pressure_angle,
    helix_angle=helix_angle,
)
result = gear.build()
show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        module=float(params.get("module", 1.0)),
        teeth_number=int(params.get("teeth_number", 20)),
        width=float(params.get("width", 6.0)),
        height=float(params.get("height", 8.0)),
        pressure_angle=float(params.get("pressure_angle", 20.0)),
        helix_angle=float(params.get("helix_angle", 0.0)),
    )
