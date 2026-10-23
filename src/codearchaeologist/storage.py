from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from .config import AppError


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.database = self.root / 'workspace.sqlite3'
        with self.connection() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, source_kind TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    status TEXT NOT NULL, stage TEXT NOT NULL, error TEXT,
                    summary TEXT, retrieval_mode TEXT NOT NULL DEFAULT 'lexical');
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL,
                    kind TEXT NOT NULL, target TEXT NOT NULL, question TEXT,
                    content TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL,
                    citations TEXT NOT NULL, created_at TEXT NOT NULL);
            ''')
            db.execute("UPDATE projects SET status='failed', error='Analysis was interrupted. Run the analysis again.' WHERE status IN ('queued','running')")

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.database, timeout=20)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        finally:
            db.close()

    def directory(self, project_id):
        if not re.fullmatch(r'[a-f0-9]{32}', project_id):
            raise AppError('Project not found.', 404)
        return self.root / 'projects' / project_id

    def create(self, project_id, name, source_kind):
        with self.connection() as db:
            db.execute('INSERT INTO projects(id,name,source_kind,created_at,updated_at,status,stage) VALUES(?,?,?,?,?,?,?)',
                       (project_id, name, source_kind, now(), now(), 'queued', 'Waiting for analysis'))
        return self.get(project_id)

    def update(self, project_id, **values):
        allowed = {'status','stage','error','summary','retrieval_mode','name'}
        if set(values) - allowed:
            raise ValueError('Unsupported project field')
        if 'summary' in values:
            values['summary'] = json.dumps(values['summary'])
        values['updated_at'] = now()
        with self.connection() as db:
            db.execute('UPDATE projects SET ' + ','.join(key+'=?' for key in values) + ' WHERE id=?',
                       (*values.values(), project_id))

    def _decode(self, row):
        item = dict(row)
        item['summary'] = json.loads(item['summary']) if item.get('summary') else None
        return item

    def get(self, project_id):
        self.directory(project_id)
        with self.connection() as db:
            row = db.execute('SELECT * FROM projects WHERE id=?', (project_id,)).fetchone()
        if not row:
            raise AppError('Project not found.', 404)
        return self._decode(row)

    def list(self):
        with self.connection() as db:
            return [self._decode(row) for row in db.execute('SELECT * FROM projects ORDER BY created_at DESC')]

    def report(self, project_id):
        project = self.get(project_id)
        if project['status'] != 'ready':
            raise AppError(project['error'] or 'Analysis is not ready yet.', 409)
        return json.loads((self.directory(project_id) / 'report' / 'analysis.json').read_text(encoding='utf-8'))

    def add_note(self, project_id, kind, target, question, result):
        with self.connection() as db:
            cursor = db.execute('INSERT INTO notes(project_id,kind,target,question,content,provider,model,citations,created_at) VALUES(?,?,?,?,?,?,?,?,?)',
                (project_id, kind, target, question, result['answer'], result['provider'], result['model'],
                 json.dumps(result['citations']), now()))
            return cursor.lastrowid

    def notes(self, project_id, kind=None):
        self.get(project_id)
        with self.connection() as db:
            rows = db.execute('SELECT * FROM notes WHERE project_id=? ORDER BY id DESC LIMIT 100', (project_id,)).fetchall()
        items = [dict(row) for row in rows if kind is None or row['kind'] == kind]
        for item in items:
            item['citations'] = json.loads(item['citations'])
        return items
