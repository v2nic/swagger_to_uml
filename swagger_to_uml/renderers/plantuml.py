import json
from typing import List

from swagger_to_uml.model import (
    Diagram,
    DiagramClass,
    DiagramEnum,
    DiagramField,
    DiagramOperation,
    DiagramParameter,
    DiagramPath,
    DiagramResponse,
    RelationType,
)
from swagger_to_uml.renderers.base import DiagramRenderer

TYPE_NOT_SPECIFIED = "<i>not specified</i>"


class PlantUMLRenderer(DiagramRenderer):
    def render(self, diagram: Diagram) -> str:
        parts = ["@startuml", "hide empty members", "set namespaceSeparator none", ""]

        for path in diagram.paths:
            parts.append(self._render_path(path))

        for enum in diagram.enums:
            parts.append(self._render_enum(enum))

        for cls in diagram.classes:
            parts.append(self._render_class(cls))

        parts.append("@enduml")
        return "\n".join(parts) + "\n"

    def _render_field(self, f: DiagramField) -> str:
        type_str = f.type_str if f.type_str else TYPE_NOT_SPECIFIED

        if f.format_str and f.type_str:
            type_str += f" ({f.format_str})"

        if f.required:
            name_str = f"<b>{f.name}</b>"
        else:
            name_str = f.name

        result = f"{{field}} {type_str} {name_str}"

        if f.enum_values is not None:
            enum_str = ", ".join([json.dumps(x) for x in f.enum_values])
            result += f" {{{enum_str}}}"

        if f.min_value is not None or f.max_value is not None:
            min_val = f.min_value if f.min_value is not None else ""
            max_val = f.max_value if f.max_value is not None else ""
            result += f" {{{min_val}..{max_val}}}"

        if f.default is not None:
            result += f" = {json.dumps(f.default)}"

        return result

    def _render_parameter(self, p: DiagramParameter) -> str:
        type_str = p.type_str if p.type_str else TYPE_NOT_SPECIFIED

        if p.format_str and p.type_str:
            type_str += f" ({p.format_str})"

        if p.required:
            name_str = f"<b>{p.name}</b>"
        else:
            name_str = p.name

        result = f"{{field}} {type_str} {name_str}"

        if p.enum_values is not None:
            enum_str = ", ".join([json.dumps(x) for x in p.enum_values])
            result += f" {{{enum_str}}}"

        if p.min_value is not None or p.max_value is not None:
            min_val = p.min_value if p.min_value is not None else ""
            max_val = p.max_value if p.max_value is not None else ""
            result += f" {{{min_val}..{max_val}}}"

        if p.default is not None:
            result += f" = {json.dumps(p.default)}"

        return result

    def _render_response(self, r: DiagramResponse) -> str:
        type_str = r.type_str if r.type_str else TYPE_NOT_SPECIFIED
        return f"{r.status}: {{field}} {type_str} "

    def _render_enum(self, enum: DiagramEnum) -> str:
        members = [f"    {str(val)}" for val in enum.values]
        return f"enum {enum.name} {{\n{chr(10).join(members)}\n}}\n"

    def _render_class(self, cls: DiagramClass) -> str:
        lines = [f"class {cls.name} {{"]

        sorted_fields = sorted(cls.fields, key=lambda x: x.required, reverse=True)
        for f in sorted_fields:
            lines.append(f"    {self._render_field(f)}")

        lines.append("}")
        lines.append("")

        for rel in cls.relations:
            if rel.relation_type == RelationType.INHERITANCE:
                lines.append(f"{rel.source} --|> {rel.target}")
            else:
                lines.append(f"{rel.source} ..> {rel.target}")

        return "\n".join(lines) + "\n"

    def _render_operation(self, op: DiagramOperation) -> str:
        possible_types = ["header", "path", "query", "body", "formData"]
        parameter_types = {p.location for p in op.parameters}

        param_lines: List[str] = []
        for param_type in [x for x in possible_types if x in parameter_types]:
            param_lines.append(f".. {param_type} ..")
            for param in [p for p in op.parameters if p.location == param_type]:
                param_lines.append(self._render_parameter(param))

        response_lines = [self._render_response(r) for r in op.responses]

        associations = "\n".join(
            {f'"{op.name}" ..> {t}' for t in op.referenced_types}
        )

        return f"""class "{op.name}" {{
{chr(10).join(param_lines)}
.. responses ..
{chr(10).join(response_lines)}
}}

{associations}
"""

    def _render_path(self, path: DiagramPath) -> str:
        ops_str = "\n".join([self._render_operation(op) for op in path.operations])
        assoc_str = "\n".join(
            [
                f'"{path.path}" ..> "{op.name}"'
                for op in sorted(path.operations, key=lambda x: x.method)
            ]
        )
        return f'interface "{path.path}" {{\n}}\n\n{ops_str}\n{assoc_str}\n\n'
