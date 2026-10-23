from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
import httpx
from .config import PROJECT_ROOT, Settings


def start_model(root=PROJECT_ROOT):
    """Start only the verified, project-local runtime; return a process owned by us."""
    try:
        with httpx.Client(timeout=1, trust_env=False) as client:
            if client.get('http://127.0.0.1:8081/health').status_code == 200:
                print('Using the existing local AI server.', flush=True)
                return None
    except httpx.HTTPError:
        pass
    manifest_path = root / '.models' / 'llm-manifest.json'
    executables = list((root / '.runtime').glob('**/llama-server.exe'))
    if not manifest_path.exists() or not executables:
        print('Local generation is not installed. Run SETUP_AI.bat for AI answers.', flush=True)
        return None
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    model = (root / '.models' / manifest['file']).resolve()
    if not model.is_relative_to((root / '.models').resolve()) or not model.is_file():
        print('Local model file is missing. Run SETUP_AI.bat.', flush=True)
        return None
    logdir = root / 'data'
    logdir.mkdir(exist_ok=True)
    log = (logdir / 'local-model.log').open('ab')
    key = secrets.token_urlsafe(32)
    os.environ['CODEARCH_LOCAL_API_KEY'] = key
    command = [str(executables[0]), '--model', str(model), '--host', '127.0.0.1',
               '--port', '8081', '--ctx-size', '6144', '--parallel', '1',
               '--threads', str(min(4, os.cpu_count() or 2)), '--n-gpu-layers', '0',
               '--alias', 'codearch-local', '--no-webui', '--api-key', key,
               '--cors-origins', 'http://127.0.0.1:8765']
    print('Starting local code model. First load may take a moment...', flush=True)
    child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                             creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
    log.close()
    for _ in range(60):
        if child.poll() is not None:
            print('The model stopped during startup. See data/local-model.log.', flush=True)
            return None
        try:
            with httpx.Client(timeout=1, trust_env=False, headers={'Authorization':'Bearer '+key}) as client:
                if client.get('http://127.0.0.1:8081/health').status_code == 200:
                    print('Local code model is ready.', flush=True)
                    return child
        except httpx.HTTPError:
            pass
        time.sleep(.5)
    child.terminate()
    print('The model startup timed out. Static analysis and search are still available.', flush=True)
    return None


def main(argv=None):
    parser = argparse.ArgumentParser(description='Start the local CodeArchaeologist application.')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--no-ai', action='store_true')
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error('Choose a port between 1024 and 65535.')
    url = f'http://127.0.0.1:{args.port}'
    try:
        with httpx.Client(timeout=1, trust_env=False) as client:
            response = client.get(url + '/api/health')
            if response.status_code == 200 and response.json().get('edition') == 'local-single-user':
                print(f'CodeArchaeologist is already running: {url}', flush=True)
                if not args.no_browser:
                    webbrowser.open(url)
                return
    except (httpx.HTTPError, ValueError):
        pass
    from .api import create_app
    import uvicorn
    child = start_model() if not args.no_ai else None
    app = create_app(seed_demo=True)
    url = f'http://127.0.0.1:{args.port}'
    print(f'CodeArchaeologist: {url}', flush=True)
    print('Keep this terminal open. Press Ctrl+C to stop.', flush=True)
    if not args.no_browser:
        def open_when_ready():
            for _ in range(30):
                try:
                    with httpx.Client(timeout=1, trust_env=False) as client:
                        if client.get(url + '/api/health').status_code == 200:
                            webbrowser.open(url)
                            return
                except httpx.HTTPError:
                    pass
                time.sleep(.3)
        threading.Thread(target=open_when_ready, daemon=True).start()
    try:
        uvicorn.run(app, host='127.0.0.1', port=args.port, log_level='info', access_log=False)
    finally:
        if child and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()


if __name__ == '__main__':
    main()
