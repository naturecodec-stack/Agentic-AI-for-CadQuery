NAME = "revolve"
DESCRIPTION = "Revolve a 2D closed profile around an axis to create a solid of revolution (vase, bottle, shaft, ring)"
PARAMETERS = {
    "profile_pts": {"type": "list",  "default": [[0,0],[8,0],[8,15],[5,20],[0,20]],
                    "desc": "2D points on XZ plane (x=radius, z=height); outline going CCW"},
    "angle":       {"type": "float", "default": 360.0, "unit": "deg", "desc": "sweep angle"},
    "axis_origin": {"type": "list",  "default": [0, 0, 0]},
    "axis_dir":    {"type": "list",  "default": [0, 0, 1], "desc": "axis direction vector"},
}

TEMPLATE = """import cadquery as cq

profile_pts = {profile_pts}
angle       = {angle}
axis_origin = {axis_origin}
axis_dir    = {axis_dir}

result = (
    cq.Workplane("XZ")
    .polyline(profile_pts)
    .close()
    .revolve(
        angleDegrees=angle,
        axisStart=cq.Vector(*axis_origin),
        axisEnd=cq.Vector(
            axis_origin[0] + axis_dir[0],
            axis_origin[1] + axis_dir[1],
            axis_origin[2] + axis_dir[2],
        ),
    )
)
show_object(result)
"""


def render(params: dict) -> str:
    def _listval(key, default):
        v = params.get(key, default)
        return repr(list(v) if not isinstance(v, list) else v)

    return TEMPLATE.format(
        profile_pts=_listval("profile_pts", [[0,0],[8,0],[8,15],[5,20],[0,20]]),
        angle=float(params.get("angle", 360.0)),
        axis_origin=_listval("axis_origin", [0, 0, 0]),
        axis_dir=_listval("axis_dir", [0, 0, 1]),
    )
