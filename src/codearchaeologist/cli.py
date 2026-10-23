from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .analyzer import analyze_repository
from .reporter import write_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="codearch",
        description="Analyze Python codebases and generate documentation, metrics, and diagrams.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a Python project.")
    analyze_parser.add_argument("path", help="Path to the Python project or folder.")
    analyze_parser.add_argument("--out", default="reports", help="Output folder for generated report files.")
    analyze_parser.add_argument("--html", action="store_true", help="Generate an interactive browser dashboard.")
    analyze_parser.set_defaults(func=_cmd_analyze)

    inspect_parser = subparsers.add_parser("inspect", help="Print a compact report summary.")
    inspect_parser.add_argument("json_file", help="Path to analysis.json.")
    inspect_parser.add_argument("--top", type=int, default=8, help="Number of hotspots/dead-code items to show.")
    inspect_parser.set_defaults(func=_cmd_inspect)

    search_parser = subparsers.add_parser("search", help="Search symbols and files inside analysis.json.")
    search_parser.add_argument("json_file", help="Path to analysis.json.")
    search_parser.add_argument("query", help="Search term.")
    search_parser.set_defaults(func=_cmd_search)

    serve_parser = subparsers.add_parser("serve", help="Start the local web application.")
    serve_parser.add_argument("--port", type=int, default=8765)
    serve_parser.add_argument("--no-browser", action="store_true")
    serve_parser.add_argument("--no-ai", action="store_true")
    serve_parser.set_defaults(func=_cmd_serve)

    args = parser.parse_args(argv)
    return args.func(args)


def _cmd_analyze(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    if not root.exists():
        print(f"Path does not exist: {root}", file=sys.stderr)
        return 2

    report = analyze_repository(root)
    paths = write_report(report, args.out, include_html=args.html)

    summary = report["summary"]
    print("CodeArchaeologist analysis complete")
    print(f"Project: {report['project']['name']}")
    print(f"Modules: {summary['modules']} | Classes: {summary['classes']} | Functions: {summary['functions']}")
    print(f"LOC: {summary['lines_of_code']} | Call edges: {summary['call_edges']} | Avg complexity: {summary['average_complexity']}")
    print(f"Likely dead functions: {summary['likely_dead_functions']} | Syntax errors: {summary['syntax_errors']}")
    print("")
    for label, path in paths.items():
        print(f"{label}: {path}")
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    from .server import main as serve
    argv = ["--port", str(args.port)]
    if args.no_browser:
        argv.append("--no-browser")
    if args.no_ai:
        argv.append("--no-ai")
    serve(argv)
    return 0


def _cmd_inspect(args: argparse.Namespace) -> int:
    report = _load_report(args.json_file)
    summary = report["summary"]
    print(f"Project: {report['project']['name']}")
    print(f"Root: {report['project']['root']}")
    print(f"Modules: {summary['modules']}")
    print(f"Classes: {summary['classes']}")
    print(f"Functions: {summary['functions']}")
    print(f"Lines of code: {summary['lines_of_code']}")
    print(f"Call edges: {summary['call_edges']}")
    print(f"Average complexity: {summary['average_complexity']}")
    print("")

    print("Top complexity hotspots:")
    hotspots = sorted(
        report["functions"],
        key=lambda item: item["complexity"],
        reverse=True,
    )[: args.top]
    for item in hotspots:
        print(f"- {item['module']}.{item['qualified_name']}: {item['complexity']} ({item['file']}:{item['line_start']})")

    print("")
    print("Likely dead code:")
    dead_items = report["dead_code"]["functions"][: args.top]
    if not dead_items and not report["dead_code"]["classes"]:
        print("- none detected")
    for item in dead_items:
        print(f"- function {item['module']}.{item['qualified_name']} ({item['file']}:{item['line_start']})")
    for item in report["dead_code"]["classes"][: args.top]:
        print(f"- class {item['module']}.{item['qualified_name']} ({item['file']}:{item['line_start']})")
    return 0


def _cmd_search(args: argparse.Namespace) -> int:
    report = _load_report(args.json_file)
    query = args.query.lower()
    matches: list[tuple[str, str, str]] = []

    for module in report["modules"]:
        if _matches(module, query):
            matches.append(("module", module["name"], module["file"]))
    for class_info in report["classes"]:
        if _matches(class_info, query):
            matches.append(("class", f"{class_info['module']}.{class_info['qualified_name']}", class_info["file"]))
    for function in report["functions"]:
        if _matches(function, query):
            location = f"{function['file']}:{function['line_start']}"
            matches.append(("function", f"{function['module']}.{function['qualified_name']}", location))

    if not matches:
        print(f"No matches for: {args.query}")
        return 1

    for kind, name, location in matches[:50]:
        print(f"{kind:8} {name} - {location}")
    if len(matches) > 50:
        print(f"... and {len(matches) - 50} more matches")
    return 0


def _load_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _matches(item: Any, query: str) -> bool:
    return query in json.dumps(item, ensure_ascii=False).lower()

