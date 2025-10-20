import importlib.util
import importlib.machinery
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "bin" / "swagger_to_uml"
PETSTORE_DIR = ROOT / "petstore_example"


def load_swagger_module():
    # Use SourceFileLoader because the target is an executable without .py suffix
    loader = importlib.machinery.SourceFileLoader("swagger_to_uml", str(SCRIPT_PATH))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None and spec.loader is not None, "Failed to create import spec for swagger_to_uml"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


# --------------------
# Unit tests
# --------------------

def test_resolve_ref():
    mod = load_swagger_module()
    assert mod.resolve_ref("#/components/schemas/Pet") == "Pet"
    assert mod.resolve_ref("#/definitions/User") == "User"
    assert mod.resolve_ref("Pet") == "Pet"


def test_property_from_dict_basic_and_ref():
    mod = load_swagger_module()

    # Simple string property
    p1 = mod.Property.from_dict("name", {"type": "string", "description": "pet name"}, required=True)
    assert p1.type == "string"
    assert p1.required is True
    # Required should render bold name in UML
    assert "<b>name</b>" in p1.uml

    # $ref property
    p2 = mod.Property.from_dict("category", {"$ref": "#/definitions/Category"}, required=False)
    assert p2.type == "Category"
    assert p2.ref_type == "Category"
    assert "{field} Category category" in p2.uml

    # Array of refs
    p3 = mod.Property.from_dict(
        "tags",
        {"type": "array", "items": {"$ref": "#/definitions/Tag"}},
        required=False,
    )
    assert p3.type == "array"
    assert p3.items == "Tag"
    assert p3.ref_type == "Tag"
    assert "{field} Tag[] tags" in p3.uml


def test_definition_from_dict_and_uml_relationships():
    mod = load_swagger_module()

    d = {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "format": "int64"},
            "category": {"$ref": "#/definitions/Category"},
            "tags": {"type": "array", "items": {"$ref": "#/definitions/Tag"}},
        },
        "required": ["id"],
    }

    definition = mod.Definition.from_dict("Pet", d)
    # Relationships should include referenced types
    assert "Category" in definition.relationships
    assert "Tag" in definition.relationships

    uml = definition.uml
    # Class header and fields
    assert uml.startswith("class Pet {")
    assert "{field} integer (int64) <b>id</b>" in uml or "{field} integer (int64) id" in uml
    # Associations
    assert "Pet ..> Category" in uml
    assert "Pet ..> Tag" in uml


def test_definition_from_dict_allof():
    mod = load_swagger_module()

    definitions = {
        "Base": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"}
            },
            "required": ["id"]
        },
        "Extended": {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            }
        }
    }

    d = {
        "allOf": [
            {"$ref": "#/definitions/Base"},
            {"$ref": "#/definitions/Extended"}
        ]
    }

    definition = mod.Definition.from_dict("Combined", d, definitions)
    assert definition.type == "object"
    # Check properties merged
    prop_names = [p.name for p in definition.properties]
    assert "id" in prop_names
    assert "name" in prop_names
    # Check required
    id_prop = next(p for p in definition.properties if p.name == "id")
    assert id_prop.required == True
    # Check inheritance relationships
    assert "Base" in definition.inheritances
    assert "Extended" in definition.inheritances
    # Check UML includes inheritance arrows
    uml = definition.uml
    assert "Combined --|> Base" in uml
    assert "Combined --|> Extended" in uml


# --------------------
# End-to-end test against petstore example
# --------------------
@pytest.mark.parametrize(
    "input_file, expected_puml",
    [
        (PETSTORE_DIR / "swagger.json", PETSTORE_DIR / "swagger.puml"),
    ],
)
def test_end_to_end_petstore_matches_expected(input_file: Path, expected_puml: Path):
    # Run the script as a subprocess to mimic real CLI usage
    result = subprocess.run(
        ["python3", str(SCRIPT_PATH), str(input_file)],
        check=True,
        capture_output=True,
        text=True,
    )

    generated = result.stdout
    expected = expected_puml.read_text()

    # Helpful diff on failure
    if generated != expected:
        import difflib

        diff = "\n".join(
            difflib.unified_diff(
                expected.splitlines(),
                generated.splitlines(),
                fromfile=str(expected_puml),
                tofile="generated",
                lineterm="",
            )
        )
        pytest.fail(f"Generated UML does not match expected file.\n{diff}")


def test_openapi_end_to_end_smoke():
    # Ensure OpenAPI 3 input is accepted and produces UML with key elements
    input_file = PETSTORE_DIR / "openapi.json"

    result = subprocess.run(
        ["python3", str(SCRIPT_PATH), str(input_file)],
        check=True,
        capture_output=True,
        text=True,
    )

    generated = result.stdout
    # Minimal invariants
    assert generated.startswith("@startuml")
    assert "class Pet {" in generated  # model from components.schemas
    assert 'interface "/pet"' in generated  # a path interface should exist
