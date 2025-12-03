import json
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

from swagger_to_uml.model import (
    Diagram,
    DiagramClass,
    DiagramEnum,
    DiagramField,
    DiagramOperation,
    DiagramParameter,
    DiagramPath,
    DiagramRelation,
    DiagramResponse,
    RelationType,
)


def resolve_ref(ref: str) -> str:
    return ref.split("/")[-1]


def resolve_allof(
    schema: Dict[str, Any], definitions: Dict[str, Any]
) -> Tuple[Dict[str, Any], List[str]]:
    if "allOf" not in schema:
        return schema, []

    resolved: Dict[str, Any] = {}
    allof_refs: List[str] = []

    for item in schema["allOf"]:
        if "$ref" in item:
            ref_name = resolve_ref(item["$ref"])
            allof_refs.append(ref_name)
            sub_schema = definitions.get(ref_name, {})
            sub_resolved, sub_refs = resolve_allof(sub_schema, definitions)
            allof_refs.extend(sub_refs)
        else:
            sub_resolved, sub_refs = resolve_allof(item, definitions)
            allof_refs.extend(sub_refs)

        for key, value in sub_resolved.items():
            if key == "properties":
                if "properties" not in resolved:
                    resolved["properties"] = {}
                resolved["properties"].update(value)
            elif key == "required":
                if "required" not in resolved:
                    resolved["required"] = []
                if isinstance(value, list):
                    resolved["required"].extend(value)
                else:
                    resolved["required"].append(value)
            else:
                resolved[key] = value

    return resolved, allof_refs


def _parse_type_info(d: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    ref_type = None
    format_str = None
    items = None

    if "type" in d or "$ref" in d:
        type_dict = d
    elif "schema" in d:
        type_dict = d["schema"]
    elif "allOf" in d and len(d["allOf"]) > 0:
        type_dict = d["allOf"][0]
    elif "oneOf" in d and len(d["oneOf"]) > 0:
        oneof_types = []
        format_candidates = []
        for option in d["oneOf"]:
            if "type" in option:
                opt_type = option["type"]
                if opt_type == "array" and "items" in option and "type" in option["items"]:
                    items_type = option["items"]["type"]
                    oneof_types.append(f"{items_type}[]")
                    if "format" in option["items"]:
                        format_candidates.append(option["items"]["format"])
                else:
                    oneof_types.append(opt_type)
                    if "format" in option:
                        format_candidates.append(option["format"])
            elif "$ref" in option:
                ref_name = resolve_ref(option["$ref"])
                oneof_types.append(ref_name)
        if oneof_types:
            type_str = "/".join(list(dict.fromkeys(oneof_types)))
            format_str = format_candidates[0] if format_candidates else None
            return type_str, format_str, items, ref_type
        type_dict = {}
    else:
        type_dict = {}

    if "type" in type_dict:
        type_str = type_dict["type"]
    elif "$ref" in type_dict:
        type_str = resolve_ref(type_dict["$ref"])
        ref_type = type_str
    else:
        type_str = None

    if type_str is None and "default" in d:
        default_val = d["default"]
        if isinstance(default_val, bool):
            type_str = "boolean"
        elif isinstance(default_val, int):
            type_str = "integer"
        elif isinstance(default_val, float):
            type_str = "number"
        elif isinstance(default_val, str):
            type_str = "string"

    if format_str is None:
        format_str = d.get("format")

    if isinstance(type_str, list):
        type_str = "/".join(type_str)

    if "items" in type_dict:
        if "type" in type_dict["items"]:
            items = type_dict["items"]["type"]
        else:
            items = resolve_ref(type_dict["items"]["$ref"])
            ref_type = items

    return type_str, format_str, items, ref_type


def _format_type_str(type_str: Optional[str], items: Optional[str], min_items: int = 0, max_items: Optional[int] = None, exclusive_minimum: bool = False) -> str:
    if type_str == "array" and items:
        lower = ""
        upper = ""
        if min_items:
            lower = min_items + 1 if exclusive_minimum else min_items
        if max_items:
            upper = max_items - 1 if exclusive_minimum else max_items

        bounds = ""
        if lower or upper:
            bounds = f"{lower}:{upper}"

        return f"{items}[{bounds}]"
    return type_str or ""


def parse_field(property_name: str, d: Dict[str, Any], required: bool) -> Tuple[DiagramField, Optional[str]]:
    type_str, format_str, items, ref_type = _parse_type_info(d)

    min_items = d.get("minItems", 0)
    max_items = d.get("maxItems")
    exclusive_minimum = d.get("exclusiveMinimum", False)

    final_type_str = _format_type_str(type_str, items, min_items, max_items, exclusive_minimum)

    minimum = d.get("minimum")
    maximum = d.get("maximum")

    return DiagramField(
        name=property_name,
        type_str=final_type_str,
        required=required,
        enum_values=d.get("enum"),
        default=d.get("default"),
        min_value=minimum,
        max_value=maximum,
        format_str=format_str,
    ), ref_type


def parse_definition(name: str, d: Dict[str, Any], definitions: Dict[str, Any]) -> Tuple[Optional[DiagramClass], Optional[DiagramEnum]]:
    inheritances: Set[str] = set()

    if "allOf" in d:
        d, allof_refs = resolve_allof(d, definitions)
        inheritances = set(allof_refs)

    enum_values = d.get("enum") if isinstance(d.get("enum"), list) else None

    if enum_values is not None:
        return None, DiagramEnum(name=name, values=enum_values)

    fields: List[DiagramField] = []
    relationships: Set[str] = set()

    for property_name, prop in d.get("properties", {}).items():
        field, ref_type = parse_field(
            property_name=property_name,
            d=prop,
            required=property_name in d.get("required", []),
        )
        fields.append(field)
        if ref_type:
            relationships.add(ref_type)

    if "type" not in d:
        print(f'required key "type" not found in dictionary {json.dumps(d)}', file=sys.stderr)

    relations: List[DiagramRelation] = []
    for inh in sorted(inheritances):
        relations.append(DiagramRelation(source=name, target=inh, relation_type=RelationType.INHERITANCE))
    for rel in sorted(relationships):
        relations.append(DiagramRelation(source=name, target=rel, relation_type=RelationType.ASSOCIATION))

    return DiagramClass(name=name, fields=fields, relations=relations), None


def parse_parameter(whole: Dict[str, Any], d: Dict[str, Any]) -> Tuple[DiagramParameter, Optional[str]]:
    ref = d.get("$ref")
    if ref is not None:
        d = whole["parameters"][resolve_ref(ref)]

    type_str, format_str, items, ref_type = _parse_type_info(d)
    final_type_str = _format_type_str(type_str, items)

    return DiagramParameter(
        name=d["name"],
        location=d["in"],
        type_str=final_type_str,
        required=d.get("required", False),
        enum_values=d.get("enum"),
        default=d.get("default"),
        min_value=d.get("minimum"),
        max_value=d.get("maximum"),
        format_str=format_str,
    ), ref_type


def parse_response(whole: Dict[str, Any], status: str, d: Dict[str, Any]) -> Tuple[DiagramResponse, Optional[str]]:
    type_str, format_str, items, ref_type = _parse_type_info(d)
    final_type_str = _format_type_str(type_str, items)

    if format_str and type_str:
        final_type_str = f"{final_type_str} ({format_str})"

    return DiagramResponse(status=status, type_str=final_type_str), ref_type


def parse_operation(whole: Dict[str, Any], path: str, method: str, d: Dict[str, Any], path_parameters: List[DiagramParameter], path_refs: Set[str]) -> DiagramOperation:
    parameters: List[DiagramParameter] = list(path_parameters)
    referenced_types: Set[str] = set(path_refs)

    for param in d.get("parameters", []):
        p, ref_type = parse_parameter(whole, param)
        parameters.append(p)
        if ref_type:
            referenced_types.add(ref_type)

    responses: List[DiagramResponse] = []
    for status, resp in d.get("responses", {}).items():
        r, ref_type = parse_response(whole, status, resp)
        responses.append(r)
        if ref_type:
            referenced_types.add(ref_type)

    return DiagramOperation(
        name=f"{method.upper()} {path}",
        method=method,
        path=path,
        parameters=parameters,
        responses=responses,
        referenced_types=referenced_types,
    )


def parse_path(whole: Dict[str, Any], path_name: str, d: Dict[str, Any]) -> DiagramPath:
    path_parameters: List[DiagramParameter] = []
    path_refs: Set[str] = set()

    for param in d.get("parameters", []):
        p, ref_type = parse_parameter(whole, param)
        path_parameters.append(p)
        if ref_type:
            path_refs.add(ref_type)

    operations: List[DiagramOperation] = []
    for method, op in d.items():
        if method not in ["parameters", "summary", "description"]:
            operations.append(parse_operation(whole, path_name, method, op, path_parameters, path_refs))

    return DiagramPath(path=path_name, operations=operations)


def normalize_openapi_to_swagger2(openapi_doc: Dict[str, Any]) -> Dict[str, Any]:
    def pick_schema_from_content(content_obj):
        if not isinstance(content_obj, dict):
            return None
        if "application/json" in content_obj and isinstance(content_obj["application/json"], dict):
            return content_obj["application/json"].get("schema")
        for v in content_obj.values():
            if isinstance(v, dict) and "schema" in v:
                return v.get("schema")
        return None

    swagger_like: Dict[str, Any] = {
        "paths": {},
        "definitions": {},
    }

    components = openapi_doc.get("components", {})
    if "schemas" in components and isinstance(components["schemas"], dict):
        swagger_like["definitions"] = components["schemas"]

    if "parameters" in components and isinstance(components["parameters"], dict):
        swagger_like["parameters"] = components["parameters"]

    for path_name, path_item in openapi_doc.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        new_path_item: Dict[str, Any] = {}

        path_level_params = path_item.get("parameters", [])
        if isinstance(path_level_params, list):
            new_path_item["parameters"] = path_level_params

        for method, op in path_item.items():
            if method in ["get", "put", "post", "delete", "options", "head", "patch", "trace"] and isinstance(op, dict):
                new_op = dict(op)

                if "requestBody" in op and isinstance(op["requestBody"], dict):
                    rb = op["requestBody"]
                    schema = pick_schema_from_content(rb.get("content", {}))
                    if schema is not None:
                        body_param = {
                            "name": "body",
                            "in": "body",
                            "required": rb.get("required", False),
                            "schema": schema,
                            "description": rb.get("description"),
                        }
                        new_op_params = list(op.get("parameters", []))
                        new_op_params.append(body_param)
                        new_op["parameters"] = new_op_params

                responses = {}
                for status, resp in op.get("responses", {}).items():
                    if isinstance(resp, dict):
                        new_resp = {"description": resp.get("description")}
                        if "content" in resp:
                            schema = pick_schema_from_content(resp.get("content", {}))
                            if schema is not None:
                                new_resp["schema"] = schema
                        if "schema" in resp:
                            new_resp["schema"] = resp["schema"]
                        responses[status] = new_resp
                    else:
                        responses[status] = resp
                new_op["responses"] = responses

                new_path_item[method] = new_op

        swagger_like["paths"][path_name] = new_path_item

    return swagger_like


def parse_spec(d: Dict[str, Any]) -> Diagram:
    if "openapi" in d and "paths" in d:
        d = normalize_openapi_to_swagger2(d)

    classes: List[DiagramClass] = []
    enums: List[DiagramEnum] = []

    definitions = d.get("definitions", {})
    for name, definition in definitions.items():
        cls, enum = parse_definition(name, definition, definitions)
        if cls:
            classes.append(cls)
        if enum:
            enums.append(enum)

    paths: List[DiagramPath] = []
    for path_name, path in d.get("paths", {}).items():
        paths.append(parse_path(d, path_name, path))

    return Diagram(classes=classes, enums=enums, paths=paths)


def parse_file(filename: str) -> Diagram:
    loader = json.load
    if filename.endswith(".yml") or filename.endswith(".yaml"):
        import yaml
        loader = yaml.safe_load
    with open(filename, "r") as fd:
        return parse_spec(loader(fd))
