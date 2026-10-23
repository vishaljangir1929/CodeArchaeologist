"""Launch from source, with either installed dependencies or the prepared local runtime."""
from pathlib import Path
import sys

root = Path(__file__).resolve().parent
prepared = root / '.runtime' / 'python'
if prepared.exists() and sys.version_info[:2] == (3, 12):
    sys.path.insert(0, str(prepared))
sys.path.insert(0, str(root / 'src'))
try:
    from codearchaeologist.server import main
except ImportError as exc:
    print(f'Missing dependency: {exc}. Run INSTALL.bat first.')
    raise SystemExit(1)
main()
