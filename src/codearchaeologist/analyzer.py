from __future__ import annotations

import builtins
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .collector import discover_python_files
from .models import ClassInfo, EdgeInfo, FunctionInfo, ImportInfo, ModuleInfo, to_dict
from .parser import parse_python_file


BUILTIN_NAMES = set(dir(builtins)) | {
    "append",
    "clear",
    "copy",
    "extend",
    "format",
    "get",
    "items",
    "join",
    "keys",
    "lower",
    "pop",
    "read",
    "replace",
    "sort",
    "split",
    "strip",
    "upper",
    "values",
    "write",
}


def analyze_repository(root: str | Path) -> dict[str, Any]:
    """Analyze a Python repository and return a JSON-serializable report."""
    root_path = Path(root).resolve()
    files = discover_python_files(root_path)
    modules = [parse_python_file(root_path, file_path) for file_path in files]
    return _build_report(root_path, modules)


def _build_report(root: Path, modules: list[ModuleInfo]) -> dict[str, Any]:
    functions = [function for module in modules for function in module.functions]
    classes = [class_info for module in modules for class_info in module.classes]

    function_by_id = {function.id: function for function in functions}
    class_by_id = {class_info.id: class_info for class_info in classes}
    full_symbol_index: dict[str, str] = {}
    simple_function_index: dict[str, list[str]] = defaultdict(list)
    simple_class_index: dict[str, list[str]] = defaultdict(list)

    for function in functions:
        full_symbol_index[f"{function.module}.{function.qualified_name}"] = function.id
        simple_function_index[function.name].append(function.id)
    for class_info in classes:
        full_symbol_index[f"{class_info.module}.{class_info.qualified_name}"] = class_info.id
        simple_class_index[class_info.name].append(class_info.id)

    aliases_by_module = {
        module.name: _import_aliases(module.name, module.imports, module.is_package) for module in modules
    }

    edges: list[EdgeInfo] = []
    incoming = Counter()
    outgoing = Counter()
    entry_points: set[str] = set()
    unresolved_calls = []

    for module in modules:
        for call in module.main_calls:
            target = _resolve_call(
                call,
                module.name,
                None,
                aliases_by_module,
                full_symbol_index,
                simple_function_index,
                simple_class_index,
            )
            if target:
                entry_points.add(target)

    for function in functions:
        for call in function.calls:
            receiver, dot, method = call.partition(".")
            resolved_call = call
            if dot and receiver in function.bindings:
                resolved_call = function.bindings[receiver] + "." + method
            target = _resolve_call(
                resolved_call,
                function.module,
                function.class_name,
                aliases_by_module,
                full_symbol_index,
                simple_function_index,
                simple_class_index,
            )
            if target:
                edges.append(
                    EdgeInfo(
                        source=function.id,
                        target=target,
                        label=call,
                        resolution="static-best-effort",
                    )
                )
                incoming[target] += 1
                outgoing[function.id] += 1
            elif call.split(".")[0] not in BUILTIN_NAMES:
                unresolved_calls.append({"source": function.id, "call": call,
                                         "file": function.file, "line": function.line_start})

    for target in entry_points:
        incoming[target] += 1

    edges = _dedupe_edges(edges)

    module_dependencies = _module_dependencies(modules)
    dead_functions = [
        function
        for function in functions
        if incoming[function.id] == 0 and not _is_expected_entry_function(function)
    ]
    dead_classes = [
        class_info
        for class_info in classes
        if incoming[class_info.id] == 0 and not any(incoming[method] for method in class_info.methods)
        and not class_info.name.endswith("Error")
    ]

    high_complexity = [
        function for function in functions if function.complexity >= 8
    ]
    long_functions = [function for function in functions if function.loc >= 60]
    syntax_errors = [module for module in modules if module.syntax_error]
    total_loc = sum(module.loc for module in modules)

    avg_complexity = 0.0
    if functions:
        avg_complexity = round(sum(function.complexity for function in functions) / len(functions), 2)

    return {
        "schema_version": "1.0.0",
        "limitations": [
            "Python static analysis only; source is never executed.",
            "Call resolution is best-effort; reflection, callbacks, and dynamic dispatch may be unresolved.",
            "Unused symbols are review candidates, not proof that code can be deleted.",
            "Complexity is an AST-based estimate, not runtime performance.",
        ],
        "project": {
            "name": root.name,
            "root": str(root),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "summary": {
            "modules": len(modules),
            "files": len(modules),
            "classes": len(classes),
            "functions": len(functions),
            "lines_of_code": total_loc,
            "call_edges": len(edges),
            "module_dependencies": len(module_dependencies),
            "likely_dead_functions": len(dead_functions),
            "likely_dead_classes": len(dead_classes),
            "average_complexity": avg_complexity,
            "syntax_errors": len(syntax_errors),
            "unresolved_calls": len(unresolved_calls),
        },
        "modules": [to_dict(module) for module in modules],
        "classes": [to_dict(class_info) for class_info in classes],
        "functions": [to_dict(function) for function in functions],
        "call_graph": {
            "nodes": _call_graph_nodes(functions, classes, incoming, outgoing),
            "edges": [to_dict(edge) for edge in _dedupe_edges(edges)],
        },
        "module_dependencies": module_dependencies,
        "unresolved_calls": unresolved_calls,
        "dead_code": {
            "functions": [to_dict(function) for function in dead_functions],
            "classes": [to_dict(class_info) for class_info in dead_classes],
        },
        "quality": {
            "high_complexity": [to_dict(function) for function in high_complexity],
            "long_functions": [to_dict(function) for function in long_functions],
            "syntax_errors": [to_dict(module) for module in syntax_errors],
        },
        "ai_context": {
                "purpose": "Structured evidence for code explanation and retrieval.",
            "suggested_prompt": (
                "Use this static analysis JSON as grounded context. Explain each module, "
                "summarize risky code, and answer questions only from evidence in the JSON."
            ),
            "available_sections": [
                "summary",
                "modules",
                "classes",
                "functions",
                "call_graph",
                "module_dependencies",
                "dead_code",
                "quality",
            ],
        },
    }


def _resolve_call(
    call: str,
    module_name: str,
    class_name: str | None,
    aliases_by_module: dict[str, dict[str, str]],
    full_symbol_index: dict[str, str],
    simple_function_index: dict[str, list[str]],
    simple_class_index: dict[str, list[str]],
) -> str | None:
    if not call:
        return None

    last_part = call.rsplit(".", 1)[-1]
    if class_name and call.startswith(("self.", "cls.")):
        method_name = call.split(".", 1)[1].split(".")[-1]
        candidate = f"{module_name}.{class_name}.{method_name}"
        if candidate in full_symbol_index:
            return full_symbol_index[candidate]

    aliases = aliases_by_module.get(module_name, {})
    first, sep, rest = call.partition(".")
    if first in aliases:
        candidate = aliases[first] + (f".{rest}" if sep else "")
        if candidate in full_symbol_index:
            return full_symbol_index[candidate]
        return None

    same_module_function = f"{module_name}.{call}"
    if same_module_function in full_symbol_index:
        return full_symbol_index[same_module_function]

    same_module_method = f"{module_name}.{class_name}.{call}" if class_name else ""
    if same_module_method in full_symbol_index:
        return full_symbol_index[same_module_method]

    if "." in call and call in full_symbol_index:
        return full_symbol_index[call]

    if "." in call or call in BUILTIN_NAMES:
        return None

    function_matches = simple_function_index.get(last_part, [])
    class_matches = simple_class_index.get(last_part, [])
    matches = function_matches + class_matches
    if len(matches) == 1:
        return matches[0]
    return None


def _import_aliases(module_name: str, imports: list[ImportInfo], is_package: bool = False) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for import_info in imports:
        if import_info.kind == "import":
            alias = import_info.alias or import_info.module.split(".")[0]
            aliases[alias] = import_info.module if import_info.alias else import_info.module.split(".")[0]
        else:
            base = _absolute_import(module_name, import_info.module, import_info.level, is_package)
            alias = import_info.alias or import_info.name
            if import_info.name == "*":
                continue
            aliases[alias] = f"{base}.{import_info.name}" if base else import_info.name
    return aliases


def _absolute_import(current_module: str, imported_module: str, level: int, is_package: bool = False) -> str:
    if level == 0:
        return imported_module

    parts = current_module.split(".")
    remove = level - 1 if is_package else level
    if remove == 0:
        base_parts = parts
    elif len(parts) >= remove:
        base_parts = parts[:-remove]
    else:
        base_parts = []
    if imported_module:
        base_parts.append(imported_module)
    return ".".join(part for part in base_parts if part)


def _module_dependencies(modules: list[ModuleInfo]) -> list[dict[str, str]]:
    known_modules = {module.name for module in modules}
    dependencies: set[tuple[str, str, str]] = set()

    for module in modules:
        for import_info in module.imports:
            imported = _absolute_import(module.name, import_info.module, import_info.level, module.is_package)
            if import_info.kind == "from" and import_info.name != "*":
                imported_symbol = f"{imported}.{import_info.name}" if imported else import_info.name
            else:
                imported_symbol = imported

            target_module = _nearest_module(imported_symbol, known_modules)
            if target_module and target_module != module.name:
                dependencies.add((module.name, target_module, imported_symbol))

    return [
        {"source": source, "target": target, "imported": imported}
        for source, target, imported in sorted(dependencies)
    ]


def _nearest_module(symbol: str, known_modules: set[str]) -> str | None:
    parts = symbol.split(".")
    for index in range(len(parts), 0, -1):
        candidate = ".".join(parts[:index])
        if candidate in known_modules:
            return candidate
    return None


def _call_graph_nodes(
    functions: list[FunctionInfo],
    classes: list[ClassInfo],
    incoming: Counter,
    outgoing: Counter,
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for function in functions:
        nodes.append(
            {
                "id": function.id,
                "label": function.qualified_name,
                "module": function.module,
                "kind": function.kind,
                "complexity": function.complexity,
                "incoming": incoming[function.id],
                "outgoing": outgoing[function.id],
            }
        )
    for class_info in classes:
        nodes.append(
            {
                "id": class_info.id,
                "label": class_info.qualified_name,
                "module": class_info.module,
                "kind": "class",
                "complexity": 0,
                "incoming": incoming[class_info.id],
                "outgoing": outgoing[class_info.id],
            }
        )
    return nodes


def _dedupe_edges(edges: list[EdgeInfo]) -> list[EdgeInfo]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[EdgeInfo] = []
    for edge in edges:
        key = (edge.source, edge.target, edge.label)
        if key not in seen:
            unique.append(edge)
            seen.add(key)
    return unique


def _is_expected_entry_function(function: FunctionInfo) -> bool:
    if function.name in {"main", "run", "cli"}:
        return True
    if function.name.startswith("test_"):
        return True
    if function.name.startswith("__") and function.name.endswith("__"):
        return True
    if function.class_name and function.name in {"setUp", "tearDown"}:
        return True
    return False

