import os
import sys

# Add repository root to sys.path so tests can import local modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from puml_parser import parse_puml

PUML_PATH = os.path.join(ROOT, "xsd-openadr", "oadr_20b_subsgroups.puml")


def load_model():
    with open(PUML_PATH, "r", encoding="utf-8") as f:
        return parse_puml(f.read())


def test_oadrCreatePartyRegistrationType_has_simple_fields_and_no_link_for_simple_refs():
    m = load_model()
    fields = dict(m.get_fields("oadrCreatePartyRegistrationType"))
    # spot-check fields present
    assert "requestID" in fields
    assert "oadrReportOnly" in fields
    assert "oadrHttpPullModel" in fields
    # ensure no association to simple refs
    assert not m.has_assoc("oadrCreatePartyRegistrationType", "oadrReportOnly")
    assert not m.has_assoc("oadrCreatePartyRegistrationType", "oadrTransportAddress")


def test_temperature_item_units_linked_to_temperatureUnitType():
    m = load_model()
    # temperatureType should have an itemUnits field of temperatureUnitType
    fields = dict(m.get_fields("temperatureType"))
    assert fields.get("itemUnits") == "temperatureUnitType"
    assert m.has_assoc("temperatureType", "temperatureUnitType")


def test_marketContext_is_simple_anyURI_field_in_report_description():
    m = load_model()
    fields = dict(m.get_fields("oadrReportDescriptionType"))
    assert fields.get("marketContext") == "xs:anyURI"


def test_substitution_groups_rendered_and_membership():
    m = load_model()
    # itemBase is abstract and has members pulseCount and temperature
    assert "itemBase" in m.abstract_classes
    assert m.has_inherit("pulseCount", "itemBase")
    assert m.has_inherit("temperature", "itemBase")


def test_EiTargetType_field_types_resolved():
    m = load_model()
    fields = dict(m.get_fields("EiTargetType"))
    assert fields.get("serviceLocation") == "ServiceLocationType"
    assert fields.get("transportInterface") == "TransportInterfaceType"


def test_pulseCount_member_of_itemBase():
    m = load_model()
    assert m.has_inherit("pulseCount", "itemBase")
