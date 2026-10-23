from __future__ import annotations

import json
import math
from html import escape
from pathlib import Path
from typing import Any


def write_report(report: dict[str, Any], output_dir: str | Path, include_html: bool = True) -> dict[str, Path]:
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    module_dir = out / "modules"
    module_dir.mkdir(exist_ok=True)

    paths = {
        "json": out / "analysis.json",
        "markdown": out / "README_REPORT.md",
        "architecture_svg": out / "architecture.svg",
        "call_graph_svg": out / "call_graph.svg",
    }

    paths["json"].write_text(json.dumps(report, indent=2), encoding="utf-8")
    paths["markdown"].write_text(_markdown_summary(report), encoding="utf-8")
    _write_module_docs(report, module_dir)
    _write_svg_graph(
        title="Module Dependency Graph",
        nodes=[module["name"] for module in report["modules"]],
        edges=[
            (item["source"], item["target"], item["imported"])
            for item in report["module_dependencies"]
        ],
        output_path=paths["architecture_svg"],
    )
    _write_svg_graph(
        title="Call Graph",
        nodes=[node["id"] for node in report["call_graph"]["nodes"]],
        edges=[
            (edge["source"], edge["target"], edge["label"])
            for edge in report["call_graph"]["edges"]
        ],
        output_path=paths["call_graph_svg"],
        labels={
            node["id"]: f'{node["module"]}.{node["label"]}'
            for node in report["call_graph"]["nodes"]
        },
        max_nodes=45,
    )

    if include_html:
        paths["html"] = out / "index.html"
        paths["html"].write_text(_html_dashboard(report), encoding="utf-8")

    return paths


def _markdown_summary(report: dict[str, Any]) -> str:
    summary = report["summary"]
    dead = report["dead_code"]
    quality = report["quality"]
    lines = [
        f"# CodeArchaeologist Report: {report['project']['name']}",
        "",
        "## Summary",
        "",
        f"- Modules: {summary['modules']}",
        f"- Classes: {summary['classes']}",
        f"- Functions/methods: {summary['functions']}",
        f"- Lines of code: {summary['lines_of_code']}",
        f"- Call graph edges: {summary['call_edges']}",
        f"- Average complexity: {summary['average_complexity']}",
        f"- Likely dead functions: {summary['likely_dead_functions']}",
        f"- Likely dead classes: {summary['likely_dead_classes']}",
        f"- Syntax errors: {summary['syntax_errors']}",
        "",
        "## Modules",
        "",
        "| Module | Classes | Functions | Imports | LOC |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]

    for module in report["modules"]:
        lines.append(
            f"| `{module['name']}` | {len(module['classes'])} | {len(module['functions'])} | "
            f"{len(module['imports'])} | {module['loc']} |"
        )

    lines.extend(["", "## Complexity Hotspots", ""])
    if quality["high_complexity"]:
        for function in sorted(quality["high_complexity"], key=lambda item: item["complexity"], reverse=True):
            lines.append(
                f"- `{function['module']}.{function['qualified_name']}`: complexity {function['complexity']} "
                f"at {function['file']}:{function['line_start']}"
            )
    else:
        lines.append("- No high-complexity functions found.")

    lines.extend(["", "## Likely Dead Code", ""])
    if dead["functions"] or dead["classes"]:
        for function in dead["functions"]:
            lines.append(
                f"- Function `{function['module']}.{function['qualified_name']}` "
                f"at {function['file']}:{function['line_start']}"
            )
        for class_info in dead["classes"]:
            lines.append(
                f"- Class `{class_info['module']}.{class_info['qualified_name']}` "
                f"at {class_info['file']}:{class_info['line_start']}"
            )
    else:
        lines.append("- No likely dead code found.")

    lines.extend(["", "## Generated Diagrams", "", "- `architecture.svg`", "- `call_graph.svg`"])
    return "\n".join(lines) + "\n"


def _write_module_docs(report: dict[str, Any], module_dir: Path) -> None:
    for module in report["modules"]:
        safe_name = module["name"].replace(".", "_") or "root"
        path = module_dir / f"{safe_name}.md"
        lines = [
            f"# Module `{module['name']}`",
            "",
            f"- File: `{module['file']}`",
            f"- Lines of code: {module['loc']}",
            f"- Imports: {len(module['imports'])}",
            f"- Classes: {len(module['classes'])}",
            f"- Functions/methods: {len(module['functions'])}",
            "",
            "## Purpose Summary",
            "",
            _module_summary(module),
            "",
            "## Imports",
            "",
        ]
        if module["imports"]:
            for import_info in module["imports"]:
                alias = f" as {import_info['alias']}" if import_info["alias"] else ""
                if import_info["kind"] == "import":
                    lines.append(f"- `import {import_info['module']}{alias}`")
                else:
                    dots = "." * import_info.get("level", 0)
                    lines.append(f"- `from {dots}{import_info['module']} import {import_info['name']}{alias}`")
        else:
            lines.append("- No imports.")

        lines.extend(["", "## Classes", ""])
        if module["classes"]:
            for class_info in module["classes"]:
                lines.append(f"### `{class_info['qualified_name']}`")
                if class_info["docstring"]:
                    lines.append(class_info["docstring"])
                lines.append(f"- Lines: {class_info['line_start']}-{class_info['line_end']}")
                lines.append(f"- Methods: {len(class_info['methods'])}")
                lines.append("")
        else:
            lines.append("- No classes.")

        lines.extend(["", "## Functions And Methods", ""])
        if module["functions"]:
            for function in module["functions"]:
                signature = ", ".join(function["args"])
                lines.append(f"### `{function['qualified_name']}({signature})`")
                if function["docstring"]:
                    lines.append(function["docstring"])
                lines.append(f"- Kind: {function['kind']}")
                lines.append(f"- Lines: {function['line_start']}-{function['line_end']}")
                lines.append(f"- Complexity: {function['complexity']}")
                if function["calls"]:
                    lines.append(f"- Calls: {', '.join('`' + item + '`' for item in function['calls'])}")
                else:
                    lines.append("- Calls: none detected")
                lines.append("")
        else:
            lines.append("- No functions.")

        path.write_text("\n".join(lines), encoding="utf-8")


def _module_summary(module: dict[str, Any]) -> str:
    parts: list[str] = []
    if module["classes"]:
        class_names = ", ".join(item["name"] for item in module["classes"])
        parts.append(f"Defines class-level behavior through {class_names}.")
    if module["functions"]:
        names = ", ".join(item["qualified_name"] for item in module["functions"][:6])
        parts.append(f"Exposes callable logic such as {names}.")
    if module["imports"]:
        parts.append("Uses imported dependencies that are included in the dependency graph.")
    if module["syntax_error"]:
        parts.append(f"Could not parse cleanly: {module['syntax_error']}.")
    return " ".join(parts) if parts else "This module has no extractable Python symbols."


def _write_svg_graph(
    title: str,
    nodes: list[str],
    edges: list[tuple[str, str, str]],
    output_path: Path,
    labels: dict[str, str] | None = None,
    max_nodes: int = 80,
) -> None:
    labels = labels or {node: node for node in nodes}
    important_nodes = _limit_nodes(nodes, edges, max_nodes)
    node_set = set(important_nodes)
    filtered_edges = [
        (source, target, label)
        for source, target, label in edges
        if source in node_set and target in node_set
    ]

    count = max(1, len(important_nodes))
    cols = max(1, min(5, math.ceil(math.sqrt(count))))
    rows = math.ceil(count / cols)
    box_w = 205
    box_h = 54
    gap_x = 42
    gap_y = 48
    margin = 52
    width = margin * 2 + cols * box_w + (cols - 1) * gap_x
    height = margin * 2 + rows * box_h + (rows - 1) * gap_y + 64

    positions: dict[str, tuple[int, int]] = {}
    for index, node in enumerate(important_nodes):
        row = index // cols
        col = index % cols
        x = margin + col * (box_w + gap_x)
        y = margin + 58 + row * (box_h + gap_y)
        positions[node] = (x, y)

    svg: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<defs>",
        '<marker id="arrow" markerWidth="10" markerHeight="10" refX="10" refY="3" orient="auto" markerUnits="strokeWidth">',
        '<path d="M0,0 L0,6 L9,3 z" fill="#3b556d" />',
        "</marker>",
        "</defs>",
        '<rect x="0" y="0" width="100%" height="100%" fill="#f8fafc"/>',
        f'<text x="{margin}" y="40" font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="#102030">{escape(title)}</text>',
    ]

    for source, target, label in filtered_edges:
        sx, sy = positions[source]
        tx, ty = positions[target]
        x1 = sx + box_w
        y1 = sy + box_h / 2
        x2 = tx
        y2 = ty + box_h / 2
        if tx < sx:
            x1 = sx
            x2 = tx + box_w
        svg.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            'stroke="#3b556d" stroke-width="1.6" marker-end="url(#arrow)" opacity="0.74"/>'
        )

    for node in important_nodes:
        x, y = positions[node]
        label = _short_label(labels.get(node, node), 28)
        svg.extend(
            [
                f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="8" fill="#ffffff" stroke="#bfd0df" stroke-width="1.4"/>',
                f'<text x="{x + 14}" y="{y + 24}" font-family="Arial, sans-serif" font-size="13" font-weight="700" fill="#102030">{escape(label[0])}</text>',
                f'<text x="{x + 14}" y="{y + 42}" font-family="Arial, sans-serif" font-size="12" fill="#52677a">{escape(label[1])}</text>',
            ]
        )

    if len(nodes) > len(important_nodes):
        hidden = len(nodes) - len(important_nodes)
        svg.append(
            f'<text x="{margin}" y="{height - 24}" font-family="Arial, sans-serif" font-size="12" fill="#52677a">'
            f'{hidden} lower-degree nodes hidden to keep the diagram readable.</text>'
        )

    svg.append("</svg>")
    output_path.write_text("\n".join(svg), encoding="utf-8")


def _limit_nodes(nodes: list[str], edges: list[tuple[str, str, str]], max_nodes: int) -> list[str]:
    if len(nodes) <= max_nodes:
        return nodes
    degree = CounterLike()
    for source, target, _ in edges:
        degree[source] += 1
        degree[target] += 1
    return sorted(nodes, key=lambda node: (-degree[node], node))[:max_nodes]


class CounterLike(dict[str, int]):
    def __missing__(self, key: str) -> int:
        return 0


def _short_label(label: str, max_len: int) -> tuple[str, str]:
    if "." in label:
        first, second = label.rsplit(".", 1)
        return (_trim(second, max_len), _trim(first, max_len))
    return (_trim(label, max_len), "")


def _trim(value: str, max_len: int) -> str:
    return value if len(value) <= max_len else value[: max_len - 3] + "..."


def _html_dashboard(report: dict[str, Any]) -> str:
    # A separate template avoids collisions between Python f-strings and JavaScript.
    template = (Path(__file__).parent / "web" / "report.html").read_text(encoding="utf-8")
    data = json.dumps(report, ensure_ascii=True).replace("<", "\\u003c")
    return template.replace("__ANALYSIS_DATA__", data)
