from __future__ import annotations

import io
import stat
import tokenize
import zipfile
from pathlib import Path, PurePosixPath
from .collector import DEFAULT_IGNORED_DIRS, discover_python_files
from .config import AppError

MAX_FILES = 500
MAX_FILE_BYTES = 1024 * 1024
MAX_UPLOAD_BYTES = 30 * 1024 * 1024
MAX_EXPANDED_BYTES = 60 * 1024 * 1024


def copy_folder(source: Path, destination: Path):
    if not source.is_dir():
        raise AppError('That folder does not exist. Enter a directory containing Python files.')
    if (source / '__init__.py').is_file():
        destination = destination / source.name
    files = discover_python_files(source)
    if not files:
        raise AppError('No Python files were found in this folder.')
    if len(files) > MAX_FILES:
        raise AppError(f'This local edition supports up to {MAX_FILES} Python files per analysis.')
    total = 0
    for path in files:
        relative = path.relative_to(source.resolve())
        content = path.read_bytes()
        total += len(content)
        if len(content) > MAX_FILE_BYTES or total > MAX_EXPANDED_BYTES:
            raise AppError('The project exceeds the source-size limit (1 MB per file, 60 MB total).')
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def extract_zip(content: bytes, destination: Path):
    if len(content) > MAX_UPLOAD_BYTES:
        raise AppError('Upload a ZIP smaller than 30 MB.', 413)
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
        members = archive.infolist()
        if len(members) > 10000:
            raise AppError('This ZIP contains too many entries.')
        total = 0
        selected = []
        for item in members:
            name = item.filename.replace('\\', '/')
            path = PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or ':' in name or '\x00' in name:
                raise AppError('The ZIP contains an unsafe file path.')
            if stat.S_ISLNK(item.external_attr >> 16):
                raise AppError('ZIP symlinks are not supported.')
            if item.flag_bits & 1:
                raise AppError('Password-protected ZIPs are not supported.')
            total += item.file_size
            if total > MAX_EXPANDED_BYTES:
                raise AppError('The expanded ZIP exceeds 60 MB.', 413)
            if item.is_dir() or path.suffix.lower() != '.py' or any(p in DEFAULT_IGNORED_DIRS for p in path.parts[:-1]):
                continue
            if item.file_size > MAX_FILE_BYTES:
                raise AppError('A Python file exceeds the 1 MB limit.', 413)
            selected.append((item, path))
        if not selected:
            raise AppError('The ZIP does not contain supported Python source files.')
        if len(selected) > MAX_FILES:
            raise AppError(f'Upload at most {MAX_FILES} Python files.')
        first_parts = {path.parts[0] for _, path in selected}
        strip_root = (len(first_parts) == 1 and all(len(path.parts) > 1 for _, path in selected)
                      and not any(len(path.parts) == 2 and path.name == '__init__.py' for _, path in selected))
        for item, relative in selected:
            if strip_root:
                relative = PurePosixPath(*relative.parts[1:])
            target = destination.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(item))
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
        raise AppError('This file could not be read as a ZIP archive.') from exc


def read_source(root: Path, relative: str):
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file() or target.suffix != '.py':
        raise AppError('Source file not found.', 404)
    try:
        with tokenize.open(target) as stream:
            return stream.read()
    except (UnicodeError, SyntaxError):
        return target.read_text(encoding='utf-8', errors='replace')
