NAME = "ring_gear"
DESCRIPTION = "Create an internal ring gear using cq_gears — used in planetary gear sets"
PARAMETERS = {
    "module":         {"type": "float", "default": 1.0},
    "teeth_number":   {"type": "int",   "default": 40, "desc": "must be > planet + sun teeth"},
    "width":          {"type": "float", "default": 6.0,  "unit": "mm"},
    "rim_width":      {"type": "float", "default": 4.0,  "unit": "mm", "desc": "wall thickness outside teeth"},
    "pressure_angle": {"type": "float", "default": 20.0},
}

TEMPLATE = """import cadquery as cq

try:
    from cq_gears import RingGear
except ImportError:
    raise ImportError("cq_gears not installed. Run: pip install cq_gears")

module         = {module}
teeth_number   = {teeth_number}
width          = {width}
rim_width      = {rim_width}
pressure_angle = {pressure_angle}

gear = RingGear(
    module=module,
    teeth_number=teeth_number,
    width=width,
    rim_width=rim_width,
    pressure_angle=pressure_angle,
)
result = gear.build()
show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        module=float(params.get("module", 1.0)),
        teeth_number=int(params.get("teeth_number", 40)),
        width=float(params.get("width", 6.0)),
        rim_width=float(params.get("rim_width", 4.0)),
        pressure_angle=float(params.get("pressure_angle", 20.0)),
    )
