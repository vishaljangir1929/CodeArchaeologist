from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = ROOT / '.test-tmp'
TEST_DIR.mkdir(exist_ok=True)
sys.path.insert(0, str(ROOT / 'src'))
from codearchaeologist.analyzer import analyze_repository
from codearchaeologist.ingestion import extract_zip
from codearchaeologist.config import Settings, AppError
from codearchaeologist.api import create_app
from codearchaeologist.ai import LocalAI
from fastapi.testclient import TestClient
import httpx


def archive_of(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return stream.getvalue()


class AnalyzerRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TEST_DIR)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, relative, source):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding='utf-8')

    def test_nested_functions_do_not_inflate_parent_complexity(self):
        self.write('app.py', 'def outer():\n    def inner(x):\n        if x:\n            return 1\n    return inner(2)\n')
        result = analyze_repository(self.root)
        functions = {item['qualified_name']: item for item in result['functions']}
        self.assertEqual(functions['outer']['complexity'], 1)
        self.assertEqual(functions['outer.inner']['complexity'], 2)
        self.assertIn('inner', functions['outer']['calls'])

    def test_src_layout_relative_imports_and_instance_calls(self):
        self.write('src/shop/__init__.py', 'from .worker import Worker\nWorker()\n')
        self.write('src/shop/worker.py', 'class Worker:\n    def go(self):\n        return 1\n')
        self.write('src/shop/main.py', 'from .worker import Worker\ndef main():\n    worker = Worker()\n    return worker.go()\n')
        result = analyze_repository(self.root)
        self.assertIn({'source':'shop','target':'shop.worker','imported':'shop.worker.Worker'}, result['module_dependencies'])
        edges = {(e['source'],e['target']) for e in result['call_graph']['edges']}
        self.assertIn(('shop.main:main','shop.worker:Worker.go'), edges)

    def test_external_alias_does_not_resolve_to_unrelated_local_symbol(self):
        self.write('local.py', 'def send():\n    return 1\n')
        self.write('main.py', 'import external\ndef main():\n    external.send()\n')
        result = analyze_repository(self.root)
        self.assertFalse(any(e['target']=='local:send' for e in result['call_graph']['edges']))
        self.assertTrue(any(e['call']=='external.send' for e in result['unresolved_calls']))

    def test_recursive_edges_are_preserved_and_builtins_can_be_shadowed(self):
        self.write('app.py', 'def format(x):\n    return x\ndef recurse(n):\n    if n:\n        return recurse(n-1)\n    return format(n)\n')
        result = analyze_repository(self.root)
        edges = {(e['source'],e['target']) for e in result['call_graph']['edges']}
        self.assertIn(('app:recurse','app:recurse'), edges)
        self.assertIn(('app:recurse','app:format'), edges)

    def test_syntax_errors_are_reported_without_executing_any_input(self):
        self.write('invalid.py', 'def broken(:\n pass\n')
        self.write('danger.py', "raise RuntimeError('input code must never run')\ndef safe():\n return 1\n")
        result = analyze_repository(self.root)
        self.assertEqual(result['summary']['syntax_errors'], 1)
        self.assertEqual(result['summary']['modules'], 2)

    def test_package_root_keeps_its_import_namespace(self):
        self.write('package/__init__.py', 'from .worker import run\nrun()\n')
        self.write('package/worker.py', 'def run():\n return 1\n')
        result = analyze_repository(self.root/'package')
        self.assertEqual({m['name'] for m in result['modules']}, {'package','package.worker'})
        self.assertIn({'source':'package','target':'package.worker','imported':'package.worker.run'}, result['module_dependencies'])

    def test_cli_generates_portable_reports_without_script_injection(self):
        self.write('app.py', 'def example():\n    """</script><img src=x onerror=alert(1)>"""\n    return 1\n')
        env = dict(os.environ, PYTHONPATH=str(ROOT / 'src'))
        completed = subprocess.run([sys.executable,'-m','codearchaeologist','analyze',str(self.root),
                                    '--out',str(self.root/'report'),'--html'],env=env,capture_output=True,text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads((self.root/'report/analysis.json').read_text())
        self.assertEqual(report['schema_version'],'1.0.0')
        html = (self.root/'report/index.html').read_text()
        self.assertNotIn('</script><img', html)
        self.assertNotIn('__ANALYSIS_DATA__', html)
        self.assertTrue((self.root/'report/call_graph.svg').exists())


class APIWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TEST_DIR)
        root = Path(self.temp.name)
        self.settings = Settings(root/'data', root/'models', enable_embeddings=False)
        self.app = create_app(self.settings)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def project(self):
        response = self.client.post('/api/projects/upload', files={'file':('project.zip',archive_of({
            'project/app.py':'def calculate_total(items):\n    """Calculate the sum of item prices."""\n    return sum(items)\ndef main():\n    return calculate_total([1,2])\n'}),'application/zip')})
        self.assertEqual(response.status_code,202,response.text)
        return response.json()['id']

    def test_upload_analysis_source_search_documentation_and_export(self):
        project = self.project()
        prefix = f'/api/projects/{project}'
        self.assertEqual(self.client.get(prefix).json()['status'],'ready')
        report = self.client.get(prefix+'/analysis').json()
        self.assertEqual(report['modules'][0]['file'],'app.py')
        self.assertEqual(report['project']['root'],'.')
        source = self.client.get(prefix+'/source',params={'file':'app.py'})
        self.assertIn('calculate_total',source.json()['content'])
        self.assertEqual(self.client.get(prefix+'/source',params={'file':'../workspace.sqlite3'}).status_code,404)
        search = self.client.get(prefix+'/search',params={'q':'calculate total'}).json()
        self.assertEqual(search['mode'],'lexical')
        self.assertTrue(search['results'])
        self.assertIn('markdown',self.client.get(prefix+'/documentation').json())
        export = self.client.get(prefix+'/export')
        self.assertEqual(export.status_code,200)
        with zipfile.ZipFile(io.BytesIO(export.content)) as archive:
            self.assertIn('analysis.json',archive.namelist())
            self.assertIn('README_REPORT.md',archive.namelist())
        self.assertEqual(self.client.post(prefix+'/reanalyze').status_code,202)
        self.assertEqual(self.client.get(prefix).json()['status'],'ready')
        reopened = create_app(self.settings)
        self.assertEqual(reopened.state.service.store.get(project)['status'],'ready')

    def test_invalid_inputs_host_and_cross_origin_requests(self):
        self.assertEqual(self.client.post('/api/projects/folder',json={'path':'Z:/missing-codearch-folder'}).status_code,400)
        self.assertEqual(self.client.post('/api/projects/upload',files={'file':('bad.zip',b'not a zip')}).status_code,400)
        self.assertEqual(self.client.get('/api/projects/invalid').status_code,404)
        self.assertEqual(self.client.get('/api/health',headers={'host':'evil.example'}).status_code,400)
        self.assertEqual(self.client.post('/api/projects/demo',headers={'origin':'https://evil.example'}).status_code,403)
        self.assertEqual(self.client.get('/api/health').status_code,200)

    def test_zip_path_traversal_and_symlinks_are_rejected(self):
        for filename in ['../escape.py','C:/escape.py','/absolute.py']:
            with self.subTest(filename=filename):
                response=self.client.post('/api/projects/upload',files={'file':('unsafe.zip',archive_of({filename:'pass'}))})
                self.assertEqual(response.status_code,400)
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as archive:
            item=zipfile.ZipInfo('link.py');item.create_system=3;item.external_attr=(0o120777<<16)
            archive.writestr(item,'../elsewhere')
        self.assertEqual(self.client.post('/api/projects/upload',files={'file':('symlink.zip',stream.getvalue())}).status_code,400)

    def test_ai_unavailable_is_visible_instead_of_fabricated_output(self):
        project=self.project()
        with patch.object(self.app.state.service.ai,'status',return_value={'ready':False,'message':'Model unavailable'}):
            response=self.client.post(f'/api/projects/{project}/ask',json={'question':'calculate total'})
        self.assertEqual(response.status_code,503)
        self.assertIn('unavailable',response.json()['detail'])
        self.assertEqual(self.client.get(f'/api/projects/{project}/history').json(),[])

    def test_grounded_ai_request_persists_answer_and_evidence(self):
        project=self.project()
        original_client=httpx.Client
        captured=[]
        def handler(request):
            if request.url.path=='/health':return httpx.Response(200,json={'status':'ok'})
            if request.url.path=='/v1/models':return httpx.Response(200,json={'data':[{'id':'unit-test-model'}]})
            captured.append(json.loads(request.content))
            content=json.dumps({'facts':[{'statement':'The function sums item prices.','source':'S1'},
                                        {'statement':'Invalid reference should be rejected.','source':'S99'}],'uncertainty':''})
            return httpx.Response(200,json={'choices':[{'message':{'content':content}}]})
        with patch('codearchaeologist.ai.httpx.Client',side_effect=lambda **kw: original_client(transport=httpx.MockTransport(handler),**kw)):
            response=self.client.post(f'/api/projects/{project}/ask',json={'question':'calculate total'})
        self.assertEqual(response.status_code,200,response.text)
        answer=response.json()
        self.assertNotIn('Invalid reference',answer['answer'])
        self.assertIn('[S1]',answer['answer'])
        self.assertTrue(answer['citations'])
        self.assertEqual(answer['citations'][0]['file'],'app.py')
        self.assertIn('untrusted',captured[0]['messages'][0]['content'])
        self.assertIn('SOURCE EVIDENCE',captured[0]['messages'][1]['content'])
        history=self.client.get(f'/api/projects/{project}/history').json()
        self.assertEqual(len(history),1)
        with zipfile.ZipFile(io.BytesIO(self.client.get(f'/api/projects/{project}/export').content)) as archive:
            self.assertIn('AI_NOTES.md',archive.namelist())


if __name__=='__main__':
    unittest.main()
