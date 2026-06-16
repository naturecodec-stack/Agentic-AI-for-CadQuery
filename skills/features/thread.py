NAME = "thread"
DESCRIPTION = "Create an ISO metric threaded rod (external) or threaded insert (internal) using cq_warehouse"
PARAMETERS = {
    "major_diameter": {"type": "float", "default": 8.0,   "unit": "mm",  "desc": "e.g. 8 for M8"},
    "pitch":          {"type": "float", "default": 1.25,  "unit": "mm",  "desc": "thread pitch"},
    "length":         {"type": "float", "default": 20.0,  "unit": "mm"},
    "external":       {"type": "bool",  "default": True,               "desc": "True=rod/bolt, False=threaded hole insert"},
    "end_finish":     {"type": "str",   "default": "fade",             "desc": "raw | fade | square | chamfer"},
}

TEMPLATE = """import cadquery as cq
from cq_warehouse.thread import IsoThread

thread = IsoThread(
    major_diameter={major_diameter},
    pitch={pitch},
    length={length},
    external={external},
    end_finishes=("{end_finish}", "{end_finish}"),
)
result = thread.cq_object
show_object(result)
"""


def render(params: dict) -> str:
    return TEMPLATE.format(
        major_diameter=float(params.get("major_diameter", 8.0)),
        pitch=float(params.get("pitch", 1.25)),
        length=float(params.get("length", 20.0)),
        external=bool(params.get("external", True)),
        end_finish=str(params.get("end_finish", "fade")),
    )
