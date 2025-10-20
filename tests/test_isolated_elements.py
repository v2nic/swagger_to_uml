import os
import sys
import re

# Add repository root to sys.path so tests can import local modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from puml_parser import parse_puml

PUML_PATH = os.path.join(ROOT, "xsd-openadr", "oadr_20b_subsgroups.puml")


def load_model():
    with open(PUML_PATH, "r", encoding="utf-8") as f:
        return parse_puml(f.read())


def test_isolated_elements_basic():
    """Basic test to find elements that have no relationships in the PlantUML file"""
    model = load_model()
    
    # Get all classes and enums from the model
    classes = list(model.classes.keys())
    enums = list(model.enums.keys())
    all_elements = classes + enums
    
    # Find all relationships in the model
    relationships = model.relationships
    
    # Create a set of all related elements (sources and destinations)
    related_elements = set()
    for src, dst, rel_type in relationships:
        related_elements.add(src)
        related_elements.add(dst)
    
    # Find field references
    field_references = set()
    for cls_name, cls_data in model.classes.items():
        for field_name, field_type in cls_data["fields"]:
            # Only add if it's not a built-in xs: type
            if not field_type.startswith('xs:') and field_type != 'string':
                field_references.add(field_type)
    
    # Add field references to related elements
    related_elements.update(field_references)
    
    # Find isolated elements
    isolated_elements = []
    for elem in all_elements:
        if elem not in related_elements:
            isolated_elements.append(elem)
    
    # Report the findings
    print(f"Total classes found: {len(classes)}")
    print(f"Total enums found: {len(enums)}")
    print(f"Total elements found: {len(all_elements)}")
    print(f"Total relationships found: {len(relationships)}")
    print(f"Elements with relationships: {len(related_elements)}")
    print(f"Isolated elements (no relationships): {len(isolated_elements)}")
    print()
    
    if isolated_elements:
        print("Isolated elements:")
        for elem in sorted(isolated_elements):
            print(f"  - {elem}")
    else:
        print("No isolated elements found!")
    
    # This test will pass if we have fewer than 20 isolated elements (adjusting threshold)
    #assert len(isolated_elements) < 20, f"Found {len(isolated_elements)} isolated elements that may need relationships"


def test_isolated_elements_detailed():
    """Detailed test to analyze isolated elements and categorize them"""
    model = load_model()
    
    # Get all classes and enums from the model
    classes = list(model.classes.keys())
    enums = list(model.enums.keys())
    
    # Find all relationships in the model
    relationships = model.relationships
    
    # Create a set of all related elements (sources and destinations)
    related_elements = set()
    for src, dst, rel_type in relationships:
        related_elements.add(src)
        related_elements.add(dst)
    
    # Find field references
    field_references = set()
    for cls_name, cls_data in model.classes.items():
        for field_name, field_type in cls_data["fields"]:
            # Only add if it's not a built-in xs: type
            if not field_type.startswith('xs:') and field_type != 'string':
                field_references.add(field_type)
    
    # Add field references to related elements
    related_elements.update(field_references)
    
    # Find isolated classes and enums
    isolated_classes = [cls for cls in classes if cls not in related_elements]
    isolated_enums = [enum for enum in enums if enum not in related_elements]
    
    # Report detailed analysis
    print("=== ANALYSIS OF ISOLATED ELEMENTS ===\n")
    print(f"Total classes: {len(classes)}")
    print(f"Total enums: {len(enums)}")
    print(f"Isolated classes: {len(isolated_classes)}")
    print(f"Isolated enums: {len(isolated_enums)}")
    print()
    
    # Categorize isolated elements
    print("=== ISOLATED ENUMS ===")
    for enum in sorted(isolated_enums):
        print(f"  {enum}")
    print()
    
    print("=== ISOLATED CLASSES ===")
    for cls in sorted(isolated_classes):
        print(f"  {cls}")
    print()
    
    # Check for fields that reference isolated elements
    field_references_to_isolated = {}
    for cls_name, cls_data in model.classes.items():
        for field_name, field_type in cls_data["fields"]:
            # Check if this field references an isolated element
            if field_type in isolated_classes:
                if field_type not in field_references_to_isolated:
                    field_references_to_isolated[field_type] = []
                field_references_to_isolated[field_type].append(f"{cls_name}.{field_name}")
    
    # Report field references
    if field_references_to_isolated:
        print("=== FIELD REFERENCES TO ISOLATED ELEMENTS ===")
        for field_type, field_names in field_references_to_isolated.items():
            print(f"  {field_type} referenced by: {field_names}")
        print()
    
    # Return isolated elements for further analysis
    return isolated_classes, isolated_enums, field_references_to_isolated


def test_isolated_elements_categorization():
    """Test that categorizes isolated elements to determine which ones are problematic"""
    model = load_model()
    
    # Get all classes and enums from the model
    classes = list(model.classes.keys())
    enums = list(model.enums.keys())
    
    # Find all relationships in the model
    relationships = model.relationships
    
    # Create a set of all related elements (sources and destinations)
    related_elements = set()
    for src, dst, rel_type in relationships:
        related_elements.add(src)
        related_elements.add(dst)
    
    # Find field references
    field_references = set()
    for cls_name, cls_data in model.classes.items():
        for field_name, field_type in cls_data["fields"]:
            # Only add if it's not a built-in xs: type
            if not field_type.startswith('xs:') and field_type != 'string':
                field_references.add(field_type)
    
    # Add field references to related elements
    related_elements.update(field_references)
    
    # Find isolated classes and enums
    isolated_classes = [cls for cls in classes if cls not in related_elements]
    isolated_enums = [enum for enum in enums if enum not in related_elements]
    
    print("=== CATEGORIZATION OF ISOLATED ELEMENTS ===\n")
    
    # Categorize isolated enums
    print("=== ISOLATED ENUMS ===")
    for enum in sorted(isolated_enums):
        print(f"  {enum}")
    print()
    
    print("=== ISOLATED CLASSES - CATEGORIZATION ===")
    
    # Check for fields that reference isolated classes
    field_references_to_isolated = {}
    for cls_name, cls_data in model.classes.items():
        for field_name, field_type in cls_data["fields"]:
            # Check if this field references an isolated element
            if field_type in isolated_classes:
                if field_type not in field_references_to_isolated:
                    field_references_to_isolated[field_type] = []
                field_references_to_isolated[field_type].append(f"{cls_name}.{field_name}")
    
    # Analyze isolated classes
    potentially_problematic = []
    expected_isolated = []
    
    for cls in sorted(isolated_classes):
        if cls in field_references_to_isolated:
            potentially_problematic.append(cls)
            print(f"  {cls} - REFERENCED by fields: {', '.join(field_references_to_isolated[cls])}")
        elif cls.endswith('Type') and not cls.endswith('EnumeratedType'):
            potentially_problematic.append(cls)
            print(f"  {cls} - Type class, may need relationships")
        elif cls in ['Object', 'IdentifiedObject']:
            expected_isolated.append(cls)
            print(f"  {cls} - Base class, expected to be isolated")
        else:
            expected_isolated.append(cls)
            print(f"  {cls} - No clear reason for relationships")
    
    print()
    print("=== SUMMARY ===")
    print(f"Potentially problematic isolated classes: {len(potentially_problematic)}")
    print(f"Expected isolated classes: {len(expected_isolated)}")
    print(f"Isolated enums: {len(isolated_enums)}")
    
    # Report potentially problematic isolated elements
    if potentially_problematic:
        print("\n=== POTENTIALLY PROBLEMATIC ISOLATED CLASSES ===")
        for cls in potentially_problematic:
            if cls in field_references_to_isolated:
                print(f"  {cls} is referenced by fields but has no relationships")
            else:
                print(f"  {cls} is a Type class but has no relationships")
    
    return isolated_classes, isolated_enums, potentially_problematic


def test_no_isolated_elements():
    """Test that fails if there are isolated elements that should have relationships"""
    model = load_model()
    
    # Get all classes and enums from the model
    classes = list(model.classes.keys())
    enums = list(model.enums.keys())
    all_elements = classes + enums
    
    # Find all relationships in the model
    relationships = model.relationships
    
    # Create a set of all related elements (sources and destinations)
    related_elements = set()
    for src, dst, rel_type in relationships:
        related_elements.add(src)
        related_elements.add(dst)
    
    # Find field references
    field_references = set()
    for cls_name, cls_data in model.classes.items():
        for field_name, field_type in cls_data["fields"]:
            # Only add if it's not a built-in xs: type
            if not field_type.startswith('xs:') and field_type != 'string':
                field_references.add(field_type)
    
    # Add field references to related elements
    related_elements.update(field_references)
    
    # Find isolated elements
    isolated_elements = []
    for elem in all_elements:
        if elem not in related_elements:
            isolated_elements.append(elem)
    
    # This test will fail if there are isolated elements
    assert not isolated_elements, f"Found {len(isolated_elements)} isolated elements that should have relationships: {isolated_elements}"


def test_uint16_not_entity():
    """Test that UInt16 is not treated as an entity in the PlantUML model"""
    model = load_model()
    
    # Get all classes and enums from the model
    classes = list(model.classes.keys())
    enums = list(model.enums.keys())
    all_elements = classes + enums
    
    # UInt16 should not be present as an entity (class or enum)
    assert 'UInt16' not in all_elements, f"UInt16 should not be treated as an entity, but found in: {all_elements}"
    
    print("✓ UInt16 correctly not treated as an entity")


def test_xs_string_not_entity():
    """Test that xs:string is not treated as an entity in the PlantUML model"""
    model = load_model()
    
    # Get all classes and enums from the model
    classes = list(model.classes.keys())
    enums = list(model.enums.keys())
    all_elements = classes + enums
    
    # xs:string should not be present as an entity (class or enum)
    assert 'xs:string' not in all_elements, f"xs:string should not be treated as an entity, but found in: {all_elements}"
    
    print("✓ xs:string correctly not treated as an entity")


def test_xs_datetime_not_entity():
    """Test that xs:dateTime is not treated as an entity in the PlantUML model"""
    model = load_model()
    
    # Get all classes and enums from the model
    classes = list(model.classes.keys())
    enums = list(model.enums.keys())
    all_elements = classes + enums
    
    # xs:dateTime should not be present as an entity (class or enum)
    assert 'xs:dateTime' not in all_elements, f"xs:dateTime should not be treated as an entity, but found in: {all_elements}"
    
    print("✓ xs:dateTime correctly not treated as an entity")


def test_ei_created_event_exists():
    """Test that eiCreatedEvent appears as a class in the PlantUML model"""
    model = load_model()
    
    # Get all classes from the model
    classes = list(model.classes.keys())
    
    # eiCreatedEvent should be present as a class
    assert 'eiCreatedEvent' in classes, f"eiCreatedEvent should be defined as a class, but not found in: {classes}"
    
    print("✓ eiCreatedEvent correctly defined as a class")


if __name__ == "__main__":
    # Run all tests when executed directly
    try:
        test_isolated_elements_detailed()
        print("Detailed isolated elements test completed successfully!")
    except Exception as e:
        print(f"Detailed isolated elements test failed: {e}")
        sys.exit(1)
    
    try:
        test_isolated_elements_categorization()
        print("Categorization isolated elements test completed successfully!")
    except Exception as e:
        print(f"Categorization isolated elements test failed: {e}")
        sys.exit(1)
    
    try:
        test_no_isolated_elements()
        print("No isolated elements test completed successfully!")
    except Exception as e:
        print(f"No isolated elements test failed: {e}")
        sys.exit(1)
    
    try:
        test_uint16_not_entity()
        print("UInt16 not entity test completed successfully!")
    except Exception as e:
        print(f"UInt16 not entity test failed: {e}")
        sys.exit(1)
    
    try:
        test_xs_string_not_entity()
        print("xs:string not entity test completed successfully!")
    except Exception as e:
        print(f"xs:string not entity test failed: {e}")
        sys.exit(1)
    
    try:
        test_xs_datetime_not_entity()
        print("xs:dateTime not entity test completed successfully!")
    except Exception as e:
        print(f"xs:dateTime not entity test failed: {e}")
        sys.exit(1)
    
    try:
        test_ei_created_event_exists()
        print("eiCreatedEvent exists test completed successfully!")
    except Exception as e:
        print(f"eiCreatedEvent exists test failed: {e}")
        sys.exit(1)
