NAME = "bolt_nut_assembly"
DESCRIPTION = "Create an assembly of a hex bolt and matching hex nut using cq_warehouse"
PARAMETERS = {"size": {"type": "str", "default": "M8-1.25"}, "length": {"type": "float", "default": 30.0}}
TEMPLATE = """import cadquery as cq
from cq_warehouse.fastener import HexHeadScrew, HexNut

bolt = HexHeadScrew(size="{size}", length={length}, fastener_type="iso4017")
nut  = HexNut(size="{size}", fastener_type="iso4032")

assy = cq.Assembly()
assy.add(bolt, name="bolt")
assy.add(nut, name="nut", loc=cq.Location(cq.Vector(0, 0, -10)))

result = assy.toCompound()
show_object(result)
"""
def render(p): return TEMPLATE.format(size=p.get("size","M8-1.25"), length=p.get("length",30.0))
