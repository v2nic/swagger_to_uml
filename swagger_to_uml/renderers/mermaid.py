import json
import re
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


def _sanitize_name(name: str) -> str:
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    if sanitized and sanitized[0].isdigit():
        sanitized = "_" + sanitized
    return sanitized


def _escape_field_content(s: str) -> str:
    return s.replace('"', "'").replace("<", "‹").replace(">", "›")


class MermaidRenderer(DiagramRenderer):
    def render(self, diagram: Diagram) -> str:
        lines = ["classDiagram"]

        for path in diagram.paths:
            lines.extend(self._render_path(path))

        for enum in diagram.enums:
            lines.extend(self._render_enum(enum))

        for cls in diagram.classes:
            lines.extend(self._render_class(cls))

        return "\n".join(lines) + "\n"

    def _render_field(self, f: DiagramField) -> str:
        type_str = f.type_str if f.type_str else "unspecified"

        if f.format_str and f.type_str:
            type_str += f"~{f.format_str}~"

        type_str = _escape_field_content(type_str)
        name_str = _escape_field_content(f.name)

        visibility = "+" if f.required else "-"
        result = f"{visibility}{type_str} {name_str}"

        annotations = []
        if f.enum_values is not None:
            enum_str = ",".join([json.dumps(x) for x in f.enum_values[:3]])
            if len(f.enum_values) > 3:
                enum_str += ",..."
            annotations.append(enum_str)

        if f.min_value is not None or f.max_value is not None:
            min_val = f.min_value if f.min_value is not None else ""
            max_val = f.max_value if f.max_value is not None else ""
            annotations.append(f"{min_val}..{max_val}")

        if f.default is not None:
            annotations.append(f"={json.dumps(f.default)}")

        if annotations:
            result += f" [{' '.join(annotations)}]"

        return result

    def _render_parameter(self, p: DiagramParameter) -> str:
        type_str = p.type_str if p.type_str else "unspecified"

        if p.format_str and p.type_str:
            type_str += f"~{p.format_str}~"

        type_str = _escape_field_content(type_str)
        name_str = _escape_field_content(p.name)

        visibility = "+" if p.required else "-"
        return f"{visibility}{type_str} {name_str}"

    def _render_response(self, r: DiagramResponse) -> str:
        type_str = r.type_str if r.type_str else "unspecified"
        type_str = _escape_field_content(type_str)
        return f"+{r.status} {type_str}"

    def _render_enum(self, enum: DiagramEnum) -> List[str]:
        safe_name = _sanitize_name(enum.name)
        lines = [f"    class {safe_name} {{", "        <<enumeration>>"]
        for val in enum.values:
            lines.append(f"        {_escape_field_content(str(val))}")
        lines.append("    }")
        return lines

    def _render_class(self, cls: DiagramClass) -> List[str]:
        safe_name = _sanitize_name(cls.name)
        lines = [f"    class {safe_name} {{"]

        sorted_fields = sorted(cls.fields, key=lambda x: x.required, reverse=True)
        for f in sorted_fields:
            lines.append(f"        {self._render_field(f)}")

        lines.append("    }")

        for rel in cls.relations:
            safe_source = _sanitize_name(rel.source)
            safe_target = _sanitize_name(rel.target)
            if rel.relation_type == RelationType.INHERITANCE:
                lines.append(f"    {safe_source} --|> {safe_target}")
            else:
                lines.append(f"    {safe_source} ..> {safe_target}")

        return lines

    def _render_operation(self, op: DiagramOperation) -> List[str]:
        safe_name = _sanitize_name(op.name)
        lines = [f"    class {safe_name} {{"]

        possible_types = ["header", "path", "query", "body", "formData"]
        parameter_types = {p.location for p in op.parameters}

        for param_type in [x for x in possible_types if x in parameter_types]:
            for param in [p for p in op.parameters if p.location == param_type]:
                lines.append(f"        {self._render_parameter(param)}")

        for r in op.responses:
            lines.append(f"        {self._render_response(r)}")

        lines.append("    }")

        for t in op.referenced_types:
            safe_target = _sanitize_name(t)
            lines.append(f"    {safe_name} ..> {safe_target}")

        return lines

    def _render_path(self, path: DiagramPath) -> List[str]:
        safe_path_name = _sanitize_name(path.path)
        lines = [f"    class {safe_path_name} {{", "        <<interface>>", "    }"]

        for op in path.operations:
            lines.extend(self._render_operation(op))
            safe_op_name = _sanitize_name(op.name)
            lines.append(f"    {safe_path_name} ..> {safe_op_name}")

        return lines
