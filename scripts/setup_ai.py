"""Download the official CPU runtime and model files; never requires an API key."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if (ROOT / '.runtime' / 'python').exists() and sys.version_info[:2] == (3, 12):
    sys.path.insert(0, str(ROOT / '.runtime' / 'python'))
RUNTIME_URL = 'https://github.com/ggml-org/llama.cpp/releases/download/b11827/llama-b11827-bin-win-cpu-x64.zip'
RUNTIME_SHA = '2740eeac6ed9b727a3a1002f5a42e74defa3c4cbb9a8b42b11356a07f969cb13'
MODEL_REVISION = 'f86cb2c1fa58255f8052cc32aeede1b7482d4361'
MODEL_FILE = 'qwen2.5-coder-1.5b-instruct-q2_k.gguf'
MODEL_URL = f'https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/{MODEL_REVISION}/{MODEL_FILE}'
MODEL_SHA = '3ec56d48cc5acdb93c4323f0d01a3b5db0c73c54fe71831199223720d37f6fcd'


def digest(path):
    sha = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(8 * 1024 * 1024):
            sha.update(block)
    return sha.hexdigest()


def download(url, target, sha):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and digest(target) == sha:
        print(f'Already verified: {target.name}', flush=True)
        return
    temporary = target.with_suffix(target.suffix + '.partial')
    print(f'Downloading {target.name}', flush=True)
    request = urllib.request.Request(url, headers={'User-Agent': 'CodeArchaeologist/1.0'})
    with urllib.request.urlopen(request, timeout=90) as response, temporary.open('wb') as stream:
        total = int(response.headers.get('Content-Length', 0))
        received = 0
        last = -1
        while block := response.read(4 * 1024 * 1024):
            stream.write(block)
            received += len(block)
            progress = int(received / total * 10) if total else received // (100 * 1024 * 1024)
            if progress != last:
                print(f'  {received / 1024**2:.0f} MB' + (f' / {total / 1024**2:.0f} MB' if total else ''), flush=True)
                last = progress
    if digest(temporary) != sha:
        raise RuntimeError(f'Checksum mismatch: {target.name}. Download again before running it.')
    temporary.replace(target)
    print(f'Checksum verified: {target.name}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--embeddings-only', action='store_true')
    args = parser.parse_args()
    models = ROOT / '.models'
    models.mkdir(exist_ok=True)
    if not args.embeddings_only:
        if sys.platform != 'win32' or platform.machine().lower() not in {'amd64', 'x86_64'}:
            raise RuntimeError('Automatic CPU runtime setup targets Windows x64. On other systems use Ollama; see README.')
        runtime = ROOT / '.runtime'
        archive = runtime / 'llama-cpu.zip'
        download(RUNTIME_URL, archive, RUNTIME_SHA)
        with zipfile.ZipFile(archive) as package:
            for item in package.infolist():
                target = (runtime / item.filename).resolve()
                if not target.is_relative_to(runtime.resolve()):
                    raise RuntimeError('Unsafe runtime archive')
            package.extractall(runtime)
        download(MODEL_URL, models / MODEL_FILE, MODEL_SHA)
        (models / 'llm-manifest.json').write_text(json.dumps({
            'model': 'Qwen2.5-Coder-1.5B-Instruct Q2_K', 'file': MODEL_FILE,
            'sha256': MODEL_SHA, 'revision': MODEL_REVISION,
            'license': 'Apache-2.0', 'source': MODEL_URL,
            'runtime_release': 'b11827', 'runtime_sha256': RUNTIME_SHA,
        }, indent=2), encoding='utf-8')
    os.environ.setdefault('HF_HUB_DISABLE_XET', '1')
    from fastembed import TextEmbedding
    print('Preparing BGE semantic embeddings (about 67 MB of model weights)...', flush=True)
    engine = TextEmbedding(model_name='BAAI/bge-small-en-v1.5',
                           cache_dir=str(models / 'embeddings'), threads=2, providers=['CPUExecutionProvider'])
    vector = next(iter(engine.embed(['CodeArchaeologist semantic search verification'])))
    (models / 'embeddings-ready.json').write_text(json.dumps({
        'model': 'BAAI/bge-small-en-v1.5', 'dimensions': len(vector),
        'source': 'Qdrant/bge-small-en-v1.5-onnx-Q', 'license': 'MIT',
    }, indent=2), encoding='utf-8')
    print(f'AI setup complete. Embedding dimensions: {len(vector)}. Start the application with START.bat.', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'AI setup failed: {exc}', file=sys.stderr)
        print('Check the internet connection and rerun SETUP_AI.bat. Verified downloads will be reused.', file=sys.stderr)
        sys.exit(1)
