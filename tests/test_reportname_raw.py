import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

PUML_PATH = os.path.join(ROOT, "xsd-openadr", "oadr_20b_subsgroups.puml")

def test_reportNameEnumeratedType_raw_relationships():
    """Test that reportNameEnumeratedType has relationships in the raw PlantUML file."""
    with open(PUML_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if reportNameEnumeratedType exists in the file
    assert "reportNameEnumeratedType" in content, "reportNameEnumeratedType not found in PlantUML file"
    
    # Check if there's a relationship to reportNameEnumeratedType
    # Look for lines like "someClass ..> reportNameEnumeratedType"
    lines = content.split('\n')
    relationship_lines = [line for line in lines if "..>" in line and "reportNameEnumeratedType" in line]
    
    # Also check if reportNameType references reportNameEnumeratedType
    report_name_type_lines = [line for line in lines if "reportNameType" in line and "..>" in line and "reportNameEnumeratedType" in line]
    
    assert len(relationship_lines) > 0 or len(report_name_type_lines) > 0, \
        f"No relationships found to reportNameEnumeratedType. Found {len(relationship_lines)} general relationships and {len(report_name_type_lines)} reportNameType relationships."
