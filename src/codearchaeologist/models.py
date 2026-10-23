from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ImportInfo:
    module: str
    name: str
    alias: str | None
    line: int
    kind: str
    level: int = 0


@dataclass
class FunctionInfo:
    id: str
    name: str
    qualified_name: str
    module: str
    file: str
    line_start: int
    line_end: int
    kind: str
    class_name: str | None
    args: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    docstring: str = ""
    returns: str = ""
    calls: list[str] = field(default_factory=list)
    complexity: int = 1
    loc: int = 0
    bindings: dict[str, str] = field(default_factory=dict)


@dataclass
class ClassInfo:
    id: str
    name: str
    qualified_name: str
    module: str
    file: str
    line_start: int
    line_end: int
    bases: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    docstring: str = ""


@dataclass
class ModuleInfo:
    name: str
    file: str
    loc: int
    imports: list[ImportInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    main_calls: list[str] = field(default_factory=list)
    syntax_error: str | None = None
    is_package: bool = False


@dataclass
class EdgeInfo:
    source: str
    target: str
    label: str
    resolution: str


def to_dict(value: Any) -> Any:
    """Convert nested dataclasses into JSON-safe dictionaries."""
    return asdict(value)

