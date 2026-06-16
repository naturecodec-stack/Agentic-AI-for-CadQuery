NAME = "boolean_intersection"
DESCRIPTION = "Create a shape by intersecting two solids — lens, crescent, rounded cube, organic intersection"
PARAMETERS = {
    "shape_a":   {"type": "str",   "default": "sphere",  "desc": "sphere | cylinder | box | cone"},
    "shape_b":   {"type": "str",   "default": "cylinder","desc": "sphere | cylinder | box | cone"},
    "size_a":    {"type": "float", "default": 40.0, "unit": "mm", "desc": "radius or half-size of shape A"},
    "size_b":    {"type": "float", "default": 35.0, "unit": "mm"},
    "offset":    {"type": "float", "default": 20.0, "unit": "mm", "desc": "offset of shape B from A centre"},
    "height":    {"type": "float", "default": 60.0, "unit": "mm", "desc": "height for cylinder/box"},
}

TEMPLATE = """import cadquery as cq

sa    = "{shape_a}"
sb    = "{shape_b}"
ra    = {size_a}
rb    = {size_b}
off   = {offset}
h     = {height}

def make_shape(name, r, ht):
    if name == "sphere":
        return cq.Workplane("XY").sphere(r)
    elif name == "cylinder":
        return cq.Workplane("XY").cylinder(ht, r)
    elif name == "cone":
        return (cq.Workplane("XY").circle(r).workplane(offset=ht).circle(r * 0.1).loft())
    else:  # box
        return cq.Workplane("XY").box(r * 2, r * 2, ht)

solid_a = make_shape(sa, ra, h)
solid_b = make_shape(sb, rb, h).translate((off, 0, 0))

result = solid_a.intersect(solid_b)
show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        shape_a=str(params.get("shape_a", "sphere")),
        shape_b=str(params.get("shape_b", "cylinder")),
        size_a=float(params.get("size_a", 40.0)),
        size_b=float(params.get("size_b", 35.0)),
        offset=float(params.get("offset", 20.0)),
        height=float(params.get("height", 60.0)),
    )
