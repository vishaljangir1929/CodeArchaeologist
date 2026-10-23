"""Check the committed/staged project package without downloading dependencies."""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = ('.runtime/', '.models/', '.venv/', 'data/', '.test-tmp/',
            'work/', 'frontend/node_modules/', 'docs/academic/private-evidence/')
TEXT_TYPES = {'.md', '.py', '.js', '.mjs', '.jsx', '.css', '.json', '.yml', '.yaml', '.toml', '.txt', '.bat', '.svg'}
TOKEN_PATTERNS = [
    re.compile(r'gh[pousr]_[A-Za-z0-9]{32,}'),
    re.compile(r'github_pat_[A-Za-z0-9_]{60,}'),
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
]


def main() -> int:
    result = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True, check=True)
    files = [name for name in result.stdout.decode('utf-8').split('\0') if name]
    if not files:
        print('No tracked files. Stage the intended repository files first.')
        return 1
    errors = []
    links = 0
    for name in files:
        path = ROOT / name
        if name.startswith(EXCLUDED) or '__pycache__' in path.parts or path.suffix in {'.gguf', '.onnx', '.pyc'}:
            errors.append(f'Local/generated asset must not be tracked: {name}')
        if path.name.startswith('.env') and path.name != '.env.example':
            errors.append(f'Local environment file must not be tracked: {name}')
        if not path.is_file():
            errors.append(f'Tracked file is missing: {name}')
            continue
        if path.stat().st_size > 20 * 1024 * 1024:
            errors.append(f'Large asset needs an explicit packaging decision: {name}')
        if path.suffix not in TEXT_TYPES:
            continue
        content = path.read_text(encoding='utf-8-sig')
        if any(pattern.search(content) for pattern in TOKEN_PATTERNS):
            errors.append(f'Potential credential material requires review: {name}')
        if path.suffix != '.md':
            continue
        prose = re.sub(r'```.*?```', '', content, flags=re.S)
        targets = re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', prose)
        targets += re.findall(r'(?:href|src)="([^"]+)"', prose)
        for target in targets:
            target = target.strip('<> ').split(' "', 1)[0]
            parts = urlsplit(target)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            destination = (path.parent / unquote(parts.path)).resolve()
            if not destination.is_relative_to(ROOT):
                errors.append(f'Link leaves repository in {name}: {target}')
            elif not destination.exists():
                errors.append(f'Missing link target in {name}: {target}')
            links += 1
    for message in errors:
        print(message)
    print(f'Checked {len(files)} files and {links} relative documentation links; {len(errors)} findings.')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
