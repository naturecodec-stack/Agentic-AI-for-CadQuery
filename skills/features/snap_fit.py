NAME = "snap_fit"
DESCRIPTION = "Create a cantilever snap-fit latch — flexible arm with hook for clip-together parts"
PARAMETERS = {
    "base_length":   {"type": "float", "default": 20.0, "unit": "mm"},
    "base_width":    {"type": "float", "default": 10.0, "unit": "mm"},
    "base_thickness":{"type": "float", "default": 4.0,  "unit": "mm"},
    "arm_length":    {"type": "float", "default": 18.0, "unit": "mm"},
    "arm_thickness": {"type": "float", "default": 1.5,  "unit": "mm"},
    "hook_height":   {"type": "float", "default": 2.5,  "unit": "mm"},
    "hook_length":   {"type": "float", "default": 3.0,  "unit": "mm"},
}

TEMPLATE = """import cadquery as cq

base_l = {base_length}
base_w = {base_width}
base_t = {base_thickness}
arm_l  = {arm_length}
arm_t  = {arm_thickness}
hook_h = {hook_height}
hook_l = {hook_length}

# Mounting base
base = cq.Workplane("XY").box(base_l, base_w, base_t)

# Flexible cantilever arm (sits on top of base, extending in X)
arm = (cq.Workplane("XY")
    .box(arm_l, base_w * 0.7, arm_t)
    .translate((base_l / 2 + arm_l / 2, 0, base_t / 2 + arm_t / 2)))

# Hook at end of arm (angled for easy insertion)
hook = (cq.Workplane("XY")
    .box(hook_l, base_w * 0.7, hook_h)
    .translate((base_l / 2 + arm_l - hook_l / 2, 0, base_t / 2 + arm_t + hook_h / 2)))

result = base.union(arm).union(hook)
show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        base_length=float(params.get("base_length", 20.0)),
        base_width=float(params.get("base_width", 10.0)),
        base_thickness=float(params.get("base_thickness", 4.0)),
        arm_length=float(params.get("arm_length", 18.0)),
        arm_thickness=float(params.get("arm_thickness", 1.5)),
        hook_height=float(params.get("hook_height", 2.5)),
        hook_length=float(params.get("hook_length", 3.0)),
    )
