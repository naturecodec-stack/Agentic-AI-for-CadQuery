NAME = "massembly"
DESCRIPTION = "Create a multi-part constrained assembly using cadquery-massembly (MAssembly + Mate)"
PARAMETERS = {
    "example": {"type": "str", "default": "box_lid", "desc": "box_lid | shaft_bearing | hinge"},
}

TEMPLATE = """import cadquery as cq

try:
    from cadquery_massembly import MAssembly, Mate
    HAS_MASSEMBLY = True
except ImportError:
    HAS_MASSEMBLY = False

example = "{example}"

if example == "shaft_bearing":
    # Shaft inside a bearing housing
    shaft = cq.Workplane("XY").circle(5).extrude(40)
    housing = (cq.Workplane("XY").circle(12).extrude(20)
        .faces(">Z").workplane().hole(10.1))

    if HAS_MASSEMBLY:
        assy = (MAssembly(housing, name="housing")
            .add(shaft, name="shaft",
                 mate=Mate(housing, "housing@faces@>Z",
                           shaft,   "shaft@faces@<Z")))
        assy.assemble()
        result = assy
    else:
        shaft_placed = shaft.translate((0, 0, 0))
        result = housing.union(shaft_placed)

elif example == "hinge":
    # Two plates with a pin hinge
    plate_a = cq.Workplane("XY").box(40, 30, 4)
    plate_b = cq.Workplane("XY").box(40, 30, 4)
    pin     = cq.Workplane("XY").circle(2).extrude(35)

    if HAS_MASSEMBLY:
        assy = (MAssembly(plate_a, name="plate_a")
            .add(plate_b, name="plate_b",
                 loc=cq.Location((0, 30, 0)))
            .add(pin, name="pin",
                 loc=cq.Location((0, 0, 2))))
        result = assy
    else:
        result = plate_a.union(plate_b.translate((0, 30, 0)))

else:  # box_lid — default
    box = (cq.Workplane("XY").box(60, 40, 30)
        .faces(">Z").shell(-2))
    lid = (cq.Workplane("XY").box(60, 40, 4))

    if HAS_MASSEMBLY:
        assy = (MAssembly(box, name="box")
            .add(lid, name="lid",
                 mate=Mate(box, "box@faces@>Z",
                           lid, "lid@faces@<Z")))
        assy.assemble()
        result = assy
    else:
        # Place lid on top of box
        lid_placed = lid.translate((0, 0, 30 / 2 + 4 / 2))
        result = cq.Assembly().add(box, name="box").add(lid_placed, name="lid")

show_object(result)
"""

def render(params: dict) -> str:
    return TEMPLATE.format(
        example=str(params.get("example", "box_lid")),
    )
