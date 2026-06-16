NAME = "worm_gear_set"
DESCRIPTION = "Create a worm and worm wheel gear set using cq_gears — high reduction ratio, self-locking"
PARAMETERS = {
    "module":        {"type": "float", "default": 1.0},
    "worm_starts":   {"type": "int",   "default": 1,   "desc": "number of worm starts (threads)"},
    "worm_length":   {"type": "float", "default": 20.0, "unit": "mm"},
    "wheel_teeth":   {"type": "int",   "default": 20,  "desc": "worm wheel teeth count"},
    "wheel_width":   {"type": "float", "default": 8.0,  "unit": "mm"},
    "bore_d":        {"type": "float", "default": 5.0,  "unit": "mm"},
    "show_both":     {"type": "bool",  "default": True, "desc": "show worm and wheel assembled"},
}

TEMPLATE = """import cadquery as cq

try:
    from cq_gears import WormGear, WormWheel
except ImportError:
    raise ImportError("cq_gears not installed. Run: pip install cq_gears")

module      = {module}
worm_starts = {worm_starts}
worm_length = {worm_length}
wheel_teeth = {wheel_teeth}
wheel_width = {wheel_width}
bore_d      = {bore_d}
show_both   = {show_both}

worm = WormGear(
    module=module,
    teeth_number=worm_starts,
    width=worm_length,
    bore_d=bore_d,
)

wheel = WormWheel(
    module=module,
    teeth_number=wheel_teeth,
    width=wheel_width,
    bore_d=bore_d,
    worm_teeth_number=worm_starts,
)

worm_solid  = worm.build()
wheel_solid = wheel.build()

if show_both:
    # Position wheel at 90 degrees to worm
    import cadquery as cq
    assy = (cq.Assembly()
        .add(worm_solid,  name="worm",  loc=cq.Location((0, 0, 0)))
        .add(wheel_solid, name="wheel", loc=cq.Location(
            (0, 0, 0),
            cq.Vector(1, 0, 0), 90
        )))
    result = assy
    show_object(result)
else:
    result = worm_solid
    show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        module=float(params.get("module", 1.0)),
        worm_starts=int(params.get("worm_starts", 1)),
        worm_length=float(params.get("worm_length", 20.0)),
        wheel_teeth=int(params.get("wheel_teeth", 20)),
        wheel_width=float(params.get("wheel_width", 8.0)),
        bore_d=float(params.get("bore_d", 5.0)),
        show_both=bool(params.get("show_both", True)),
    )
