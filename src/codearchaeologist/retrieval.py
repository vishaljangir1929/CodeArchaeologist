from __future__ import annotations

import json
import math
import re
import threading
from collections import Counter
from pathlib import Path
from .ingestion import read_source

STOPWORDS = set('a an the is are was were to of in on and or for does do how what where which this that with from code function method module please me it be can you'.split())


def tokens(text):
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    return [token for token in re.findall(r'[a-z][a-z0-9]+', text.lower()) if token not in STOPWORDS]


def make_chunks(report, source_root):
    chunks = []
    for module in report['modules']:
        source_lines = read_source(source_root, module['file']).splitlines()
        symbols = [dict(id=module['name'], qualified_name=module['name'], kind='module',
                        file=module['file'], line_start=1, line_end=min(60, len(source_lines)),
                        docstring='', calls=[])] + module['classes'] + module['functions']
        for symbol in symbols:
            first = symbol['line_start']
            end = symbol['line_end']
            for start in range(first, max(first+1, end+1), 60):
                last = min(start+79, end)
                content = '\n'.join(source_lines[start-1:last])
                if not content.strip():
                    continue
                label = symbol['qualified_name']
                chunks.append({
                    'id': f"{symbol['id']}@{start}", 'symbol_id': symbol['id'],
                    'name': label, 'kind': symbol.get('kind', 'class'), 'module': module['name'],
                    'file': module['file'], 'line_start': start, 'line_end': last,
                    'content': content,
                    'text': f"Python {symbol.get('kind', 'class')} {label}\n{symbol.get('docstring', '')}\nCalls: {', '.join(symbol.get('calls', []))}\n{content}",
                })
                if last >= end:
                    break
    return chunks


class Embeddings:
    """Load only verified/cached models. Normal application use never downloads models."""
    def __init__(self, settings):
        self.settings = settings
        self.model = None
        self.error = None
        self.lock = threading.RLock()

    def get(self):
        if not self.settings.enable_embeddings:
            return None
        if not (self.settings.models_dir / 'embeddings-ready.json').exists():
            self.error = 'Run SETUP_AI.bat to install semantic embeddings.'
            return None
        with self.lock:
            if self.model is None:
                try:
                    from fastembed import TextEmbedding
                    self.model = TextEmbedding(model_name=self.settings.embedding_model,
                        cache_dir=str(self.settings.models_dir / 'embeddings'),
                        threads=2, providers=['CPUExecutionProvider'], local_files_only=True)
                    self.error = None
                except Exception as exc:
                    self.error = f'Semantic model could not load: {type(exc).__name__}. Rerun SETUP_AI.bat.'
                    return None
            return self.model

    def status(self):
        return {'ready': self.get() is not None, 'model': self.settings.embedding_model,
                'message': self.error}


class SearchIndex:
    def __init__(self, embeddings):
        self.embeddings = embeddings

    def build(self, directory: Path, chunks):
        directory.mkdir(parents=True, exist_ok=True)
        mode = 'lexical'
        model = self.embeddings.get()
        if model and chunks:
            import numpy as np
            with self.embeddings.lock:
                vectors = np.asarray(list(model.embed([chunk['text'] for chunk in chunks], batch_size=16)), dtype=np.float32)
            vectors /= np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-9)
            np.save(directory / 'vectors.npy', vectors, allow_pickle=False)
            mode = 'semantic'
        (directory / 'chunks.json').write_text(json.dumps(chunks, ensure_ascii=False), encoding='utf-8')
        (directory / 'manifest.json').write_text(json.dumps({'mode': mode,
            'model': self.embeddings.settings.embedding_model if mode == 'semantic' else 'TF-IDF cosine',
            'chunks': len(chunks)}), encoding='utf-8')
        return mode

    def search(self, directory: Path, query: str, limit=6):
        chunks = json.loads((directory / 'chunks.json').read_text(encoding='utf-8'))
        manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
        lexical = lexical_scores(chunks, query)
        scores = lexical[:]
        mode = 'lexical'
        model = self.embeddings.get() if manifest['mode'] == 'semantic' else None
        if model and chunks:
            import numpy as np
            matrix = np.load(directory / 'vectors.npy', allow_pickle=False)
            with self.embeddings.lock:
                vector = np.asarray(next(iter(model.query_embed(query))), dtype=np.float32)
            vector /= max(float(np.linalg.norm(vector)), 1e-9)
            semantic = (matrix @ vector).tolist()
            # Hybrid ranking combines learned semantics with exact symbol/name matches.
            scores = [0.8 * float(s) + 0.2 * float(l) for s, l in zip(semantic, lexical)]
            mode = 'semantic'
        ranked = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)
        results = []
        seen = set()
        for i in ranked:
            chunk = chunks[i]
            if scores[i] <= 0 or chunk['symbol_id'] in seen:
                continue
            seen.add(chunk['symbol_id'])
            item = {key: value for key, value in chunk.items() if key != 'text'}
            item['score'] = round(scores[i], 4)
            results.append(item)
            if len(results) == limit:
                break
        return {'mode': mode, 'model': manifest['model'] if mode == manifest['mode'] else 'TF-IDF cosine', 'results': results}


def lexical_scores(chunks, query):
    counters = [Counter(tokens(chunk['text'])) for chunk in chunks]
    query_counts = Counter(tokens(query))
    frequency = Counter(token for counter in counters for token in counter)
    def idf(token):
        return math.log(1 + (len(chunks)+1) / (frequency[token]+1))
    query_norm = math.sqrt(sum((count * idf(token))**2 for token, count in query_counts.items())) or 1
    scores = []
    for chunk, counter in zip(chunks, counters):
        numerator = sum(counter[token] * count * idf(token)**2 for token, count in query_counts.items())
        norm = math.sqrt(sum((count * idf(token))**2 for token, count in counter.items())) or 1
        score = numerator / (norm * query_norm)
        if query.lower().strip() in chunk['name'].lower():
            score = min(1, score + 0.5)
        scores.append(score)
    return scores
