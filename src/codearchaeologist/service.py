from __future__ import annotations

import io
import json
import logging
import shutil
import threading
import uuid
import zipfile
from pathlib import Path
from .ai import LocalAI
from .analyzer import analyze_repository
from .config import AppError, PROJECT_ROOT
from .ingestion import copy_folder, extract_zip, read_source
from .reporter import write_report, _markdown_summary
from .retrieval import Embeddings, SearchIndex, make_chunks
from .storage import Store

logger = logging.getLogger(__name__)


class ProjectService:
    def __init__(self, settings):
        self.settings = settings
        self.store = Store(settings.data_dir)
        self.embeddings = Embeddings(settings)
        self.index = SearchIndex(self.embeddings)
        self.ai = LocalAI(settings)
        self.analysis_lock = threading.Lock()

    def create(self, name, source_kind, *, folder=None, zip_content=None):
        project_id = uuid.uuid4().hex
        directory = self.store.directory(project_id)
        source = directory / 'source'
        source.mkdir(parents=True)
        try:
            if source_kind == 'zip':
                extract_zip(zip_content, source)
            else:
                copy_folder(Path(folder).resolve(), source)
        except Exception:
            # Only remove this newly generated project directory, never the input folder.
            if directory.resolve().parent == (self.store.root / 'projects').resolve():
                shutil.rmtree(directory)
            raise
        return self.store.create(project_id, name[:100], source_kind)

    def demo(self):
        sample = Path(__file__).parent / 'demo'
        if not sample.exists():
            sample = PROJECT_ROOT / 'sample_project'
        return self.create('Legacy Shop', 'demo', folder=sample)

    def analyze(self, project_id):
        # CPU inference and analysis run serially to keep memory bounded on student laptops.
        with self.analysis_lock:
            directory = self.store.directory(project_id)
            try:
                self.store.update(project_id, status='running', stage='Parsing Python source', error=None)
                source = directory / 'source'
                report = analyze_repository(source)
                if not report['modules']:
                    raise AppError('No supported Python files were found.')
                self._relative_paths(report, source)
                report['project']['name'] = self.store.get(project_id)['name']
                report['project']['root'] = '.'
                self.store.update(project_id, stage='Building graphs and documentation')
                write_report(report, directory / 'report', include_html=True)
                self.store.update(project_id, stage='Indexing source evidence')
                chunks = make_chunks(report, source)
                mode = self.index.build(directory / 'index', chunks)
                self.store.update(project_id, status='ready', stage='Analysis complete',
                                  summary=report['summary'], retrieval_mode=mode, error=None)
            except Exception as exc:
                logger.exception('Analysis failed for %s', project_id)
                message = exc.message if isinstance(exc, AppError) else f'Analysis failed ({type(exc).__name__}). See the application log.'
                self.store.update(project_id, status='failed', stage='Analysis failed', error=message)

    def _relative_paths(self, value, source):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == 'file' and isinstance(item, str):
                    value[key] = Path(item).relative_to(source).as_posix()
                else:
                    self._relative_paths(item, source)
        elif isinstance(value, list):
            for item in value:
                self._relative_paths(item, source)

    def source(self, project_id, filename):
        report = self.store.report(project_id)
        if filename not in {module['file'] for module in report['modules']}:
            raise AppError('Source file not found.', 404)
        return {'file': filename, 'content': read_source(self.store.directory(project_id) / 'source', filename)}

    def search(self, project_id, query, limit=6):
        self.store.report(project_id)
        return self.index.search(self.store.directory(project_id) / 'index', query, limit)

    def ask(self, project_id, question):
        report = self.store.report(project_id)
        retrieval = self.search(project_id, question)
        result = self.ai.answer(question, retrieval['results'], self.context(report, retrieval['results']))
        result['retrieval_mode'] = retrieval['mode']
        result['id'] = self.store.add_note(project_id, 'question', '', question, result)
        return result

    def explain(self, project_id, target=None):
        report = self.store.report(project_id)
        chunks = json.loads((self.store.directory(project_id) / 'index' / 'chunks.json').read_text(encoding='utf-8'))
        if target:
            evidence = [item for item in chunks if item['symbol_id'] == target]
            question = f'Explain only {target} in three short facts: its declared inputs or fields, its visible body operations, and its returned value or defined methods. Do not invent callers, business intent, side effects, or safety guarantees.'
        else:
            evidence = []
            for kind in ['module','function','method','class']:
                for item in chunks:
                    if item['kind'] == kind and item['file'] not in {found['file'] for found in evidence}:
                        evidence.append(item)
                    if len(evidence) >= 6:
                        break
                if len(evidence) >= 6:
                    break
            question = 'Write a project overview from these representative source excerpts. Explain the visible components and relationships, likely execution flow, maintenance concerns, and what evidence is missing. Do not claim to have examined files not provided.'
        if not evidence:
            raise AppError('This symbol was not found in the source index.', 404)
        result = self.ai.answer(question, evidence, self.context(report, evidence))
        result['id'] = self.store.add_note(project_id, 'explanation', target or 'overview', None, result)
        return result

    def documentation(self, project_id):
        report = self.store.report(project_id)
        return {'markdown': _markdown_summary(report), 'explanations': self.store.notes(project_id, 'explanation')}

    def context(self, report, evidence):
        ids = {item['symbol_id'] for item in evidence}
        modules = {item['module'] for item in evidence}
        functions = [item for item in report['functions'] if item['id'] in ids]
        return {
            'summary':report['summary'],
            'functions':[{key:item[key] for key in ['id','args','returns','calls','complexity']} for item in functions[:6]],
            'resolved_calls':[edge for edge in report['call_graph']['edges'] if edge['source'] in ids][:16],
            'module_dependencies':[edge for edge in report['module_dependencies'] if edge['source'] in modules][:12],
            'limitations':report['limitations'],
        }

    def export(self, project_id):
        self.store.report(project_id)
        stream = io.BytesIO()
        report_dir = self.store.directory(project_id) / 'report'
        with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(report_dir.rglob('*')):
                if path.is_file():
                    archive.write(path, path.relative_to(report_dir).as_posix())
            notes = self.store.notes(project_id)
            if notes:
                blocks = ['# AI explanations and questions', '', 'AI output requires review against the cited source.']
                for note in reversed(notes):
                    blocks += ['', '## ' + (note['question'] or note['target']), '', note['content'], '',
                               f"Provider: {note['provider']} | Model: {note['model']}", '']
                    for citation in note['citations']:
                        blocks.append(f"- [{citation['label']}] {citation['file']}:{citation['line_start']}-{citation['line_end']}")
                archive.writestr('AI_NOTES.md', '\n'.join(blocks))
        return stream.getvalue()
