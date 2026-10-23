from __future__ import annotations

import os
from pathlib import Path


DEFAULT_IGNORED_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "env",
    "node_modules",
    "site-packages",
    "venv",
    ".runtime",
    ".models",
    "data",
    ".test-tmp",
}


def discover_python_files(root: str | Path, ignored_dirs: set[str] | None = None) -> list[Path]:
    """Return Python source files under root while skipping generated/vendor folders."""
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise ValueError("Provide an existing Python project directory.")
    ignored = DEFAULT_IGNORED_DIRS if ignored_dirs is None else ignored_dirs
    files: list[Path] = []

    for current, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [name for name in dirnames if name not in ignored and not name.startswith(".eggs")
                       and not (Path(current) / name).is_symlink()
                       and (Path(current) / name).resolve().is_relative_to(root_path)]
        for filename in filenames:
            if filename.endswith(".py") and not (Path(current) / filename).is_symlink():
                files.append(Path(current) / filename)

    return sorted(files)


def module_name_for_path(root: str | Path, file_path: str | Path) -> str:
    root_path = Path(root).resolve()
    path = Path(file_path).resolve()
    relative = path.relative_to(root_path).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[0] == "src":
        parts = parts[1:]
    if (root_path / '__init__.py').is_file():
        parts = [root_path.name] + parts
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts:
        return path.parent.name
    return ".".join(parts)

