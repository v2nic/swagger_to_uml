from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Set


class RelationType(Enum):
    ASSOCIATION = "association"
    INHERITANCE = "inheritance"


@dataclass
class DiagramField:
    name: str
    type_str: str
    required: bool = False
    enum_values: Optional[List[Any]] = None
    default: Optional[Any] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    format_str: Optional[str] = None


@dataclass
class DiagramRelation:
    source: str
    target: str
    relation_type: RelationType


@dataclass
class DiagramClass:
    name: str
    fields: List[DiagramField] = field(default_factory=list)
    relations: List[DiagramRelation] = field(default_factory=list)


@dataclass
class DiagramEnum:
    name: str
    values: List[Any] = field(default_factory=list)


@dataclass
class DiagramParameter:
    name: str
    location: str
    type_str: str
    required: bool = False
    enum_values: Optional[List[Any]] = None
    default: Optional[Any] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    format_str: Optional[str] = None


@dataclass
class DiagramResponse:
    status: str
    type_str: str


@dataclass
class DiagramOperation:
    name: str
    method: str
    path: str
    parameters: List[DiagramParameter] = field(default_factory=list)
    responses: List[DiagramResponse] = field(default_factory=list)
    referenced_types: Set[str] = field(default_factory=set)


@dataclass
class DiagramPath:
    path: str
    operations: List[DiagramOperation] = field(default_factory=list)


@dataclass
class Diagram:
    classes: List[DiagramClass] = field(default_factory=list)
    enums: List[DiagramEnum] = field(default_factory=list)
    paths: List[DiagramPath] = field(default_factory=list)
