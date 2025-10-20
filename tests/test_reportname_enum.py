import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from puml_parser import parse_puml

PUML_PATH = os.path.join(ROOT, "xsd-openadr", "oadr_20b_subsgroups.puml")

def load_model():
    with open(PUML_PATH, "r", encoding="utf-8") as f:
        return parse_puml(f.read())


def test_reportNameEnumeratedType_present_and_referenced():
    m = load_model()
    # It should exist as an enum in the diagram
    assert "reportNameEnumeratedType" in m.enums, "reportNameEnumeratedType enum missing from PlantUML output"
    
    # It should be referenced by some other type (e.g., union reportNameType)
    refs = [src for (src, dst, kind) in m.relationships if dst == "reportNameEnumeratedType"]
    assert len(refs) > 0, "reportNameEnumeratedType has no incoming relationships (no one references it)"
