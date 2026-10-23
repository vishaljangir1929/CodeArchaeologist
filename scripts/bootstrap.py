"""Install project dependencies into a project-local virtual environment."""
from pathlib import Path
import subprocess
import sys
import venv

root = Path(__file__).resolve().parents[1]
environment = root / '.venv'
python = environment / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
if not python.exists():
    print('Creating .venv...', flush=True)
    venv.EnvBuilder(with_pip=False).create(environment)
# pip's --python option also supports a fresh venv without an existing pip installation.
subprocess.run([sys.executable, '-m', 'pip', '--python', str(python), 'install',
                'pip>=23', '-r', str(root/'requirements-lock.txt'), '-e', str(root)], check=True)
print('Installation complete. Run SETUP_AI.bat once, then START.bat.', flush=True)
