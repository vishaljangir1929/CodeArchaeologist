from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if not (PROJECT_ROOT / 'pyproject.toml').exists():
    PROJECT_ROOT = Path.cwd()


@dataclass
class Settings:
    data_dir: Path
    models_dir: Path
    llama_url: str = 'http://127.0.0.1:8081'
    ollama_url: str = 'http://127.0.0.1:11434'
    ollama_model: str = 'qwen2.5-coder:1.5b'
    embedding_model: str = 'BAAI/bge-small-en-v1.5'
    enable_embeddings: bool = True
    ai_timeout: float = 180
    local_api_key: str = ''

    @classmethod
    def from_env(cls):
        return cls(
            Path(os.environ.get('CODEARCH_DATA_DIR', PROJECT_ROOT / 'data')),
            Path(os.environ.get('CODEARCH_MODELS_DIR', PROJECT_ROOT / '.models')),
            ollama_model=os.environ.get('CODEARCH_OLLAMA_MODEL', 'qwen2.5-coder:1.5b'),
            enable_embeddings=os.environ.get('CODEARCH_EMBEDDINGS', '1') != '0',
            local_api_key=os.environ.get('CODEARCH_LOCAL_API_KEY', ''),
        )


class AppError(Exception):
    def __init__(self, message: str, status: int = 400):
        self.message = message
        self.status = status
        super().__init__(message)
