NAME = "constrained_assembly"
DESCRIPTION = "Build a multi-part assembly with named parts and constraints solved automatically"
PARAMETERS = {
    "base_l": {"type": "float", "default": 60.0, "unit": "mm"},
    "base_w": {"type": "float", "default": 60.0, "unit": "mm"},
    "base_h": {"type": "float", "default": 10.0, "unit": "mm"},
    "pin_r":  {"type": "float", "default": 5.0,  "unit": "mm"},
    "pin_h":  {"type": "float", "default": 20.0, "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

base = cq.Workplane("XY").box({base_l}, {base_w}, {base_h})
pin  = cq.Workplane("XY").circle({pin_r}).extrude({pin_h})

assy = cq.Assembly()
assy.add(base, name="base", color=cq.Color("gray"))
assy.add(pin, name="pin", color=cq.Color("orange"))

# Constrain pin to sit centered on top of the base
assy.constrain("base@faces@>Z", "pin@faces@<Z", "Plane")
assy.solve()

result = assy.toCompound()
show_object(result)
"""


def render(params: dict) -> str:
    return TEMPLATE.format(
        base_l=params.get("base_l", 60.0),
        base_w=params.get("base_w", 60.0),
        base_h=params.get("base_h", 10.0),
        pin_r=params.get("pin_r", 5.0),
        pin_h=params.get("pin_h", 20.0),
    )
