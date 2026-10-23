from __future__ import annotations

import logging
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks, File, UploadFile, Query, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .config import Settings, AppError
from .ingestion import MAX_UPLOAD_BYTES
from .service import ProjectService


class FolderInput(BaseModel):
    path: str = Field(min_length=1, max_length=2000)
    name: str = Field(default='', max_length=100)


class QuestionInput(BaseModel):
    question: str = Field(min_length=3, max_length=1500)


class ExplanationInput(BaseModel):
    symbol_id: str | None = Field(default=None, max_length=500)


def create_app(settings=None, seed_demo=False):
    settings = settings or Settings.from_env()
    service = ProjectService(settings)
    app = FastAPI(title='CodeArchaeologist', version='1.0.0', description='Local Python code comprehension and grounded AI.')
    app.state.service = service
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1','localhost','testserver'])

    @app.middleware('http')
    async def local_requests(request: Request, call_next):
        origin = request.headers.get('origin')
        if origin and origin != str(request.base_url).rstrip('/'):
            return JSONResponse({'detail': 'Cross-origin requests are not allowed.'}, status_code=403)
        if request.method in {'POST','PUT','PATCH','DELETE'}:
            try:
                if int(request.headers.get('content-length', 0)) > MAX_UPLOAD_BYTES + 1024*1024:
                    return JSONResponse({'detail': 'Request exceeds the 30 MB upload limit.'}, status_code=413)
            except ValueError:
                return JSONResponse({'detail': 'Invalid content length.'}, status_code=400)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"
        return response

    @app.exception_handler(AppError)
    async def app_error(request, exc):
        return JSONResponse({'detail': exc.message}, status_code=exc.status)

    @app.exception_handler(Exception)
    async def unexpected_error(request, exc):
        logging.getLogger(__name__).exception('Unhandled request error', exc_info=exc)
        return JSONResponse({'detail': 'The operation failed. See the application terminal for details.'}, status_code=500)

    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'version': '1.0.0', 'edition': 'local-single-user'}

    @app.get('/api/ai/status')
    def ai_status():
        return {'generation': service.ai.status(), 'embeddings': service.embeddings.status()}

    @app.get('/api/projects')
    def projects():
        return service.store.list()

    @app.post('/api/projects/demo', status_code=202)
    def demo(background_tasks: BackgroundTasks):
        project = service.demo()
        background_tasks.add_task(service.analyze, project['id'])
        return project

    @app.post('/api/projects/folder', status_code=202)
    def folder(body: FolderInput, background_tasks: BackgroundTasks):
        source = Path(body.path).expanduser().resolve()
        project = service.create(body.name.strip() or source.name, 'folder', folder=source)
        background_tasks.add_task(service.analyze, project['id'])
        return project

    @app.post('/api/projects/upload', status_code=202)
    def upload(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
        if not file.filename or not file.filename.lower().endswith('.zip'):
            raise AppError('Choose a .zip file containing Python source.')
        content = file.file.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise AppError('Upload a ZIP smaller than 30 MB.', 413)
        project = service.create(Path(file.filename).stem or 'Uploaded project', 'zip', zip_content=content)
        background_tasks.add_task(service.analyze, project['id'])
        return project

    @app.get('/api/projects/{project_id}')
    def project(project_id: str):
        return service.store.get(project_id)

    @app.get('/api/projects/{project_id}/analysis')
    def analysis(project_id: str):
        return service.store.report(project_id)

    @app.post('/api/projects/{project_id}/reanalyze', status_code=202)
    def reanalyze(project_id: str, background_tasks: BackgroundTasks):
        project = service.store.get(project_id)
        if project['status'] in {'queued','running'}:
            raise AppError('This project is already being analyzed.', 409)
        service.store.update(project_id, status='queued', stage='Waiting for analysis', error=None)
        background_tasks.add_task(service.analyze, project_id)
        return service.store.get(project_id)

    @app.get('/api/projects/{project_id}/source')
    def source(project_id: str, file: str = Query(max_length=2000)):
        return service.source(project_id, file)

    @app.get('/api/projects/{project_id}/search')
    def search(project_id: str, q: str = Query(min_length=2, max_length=1500), limit: int = Query(default=6, ge=1, le=12)):
        return service.search(project_id, q, limit)

    @app.post('/api/projects/{project_id}/ask')
    def ask(project_id: str, body: QuestionInput):
        return service.ask(project_id, body.question.strip())

    @app.post('/api/projects/{project_id}/explain')
    def explain(project_id: str, body: ExplanationInput):
        return service.explain(project_id, body.symbol_id)

    @app.get('/api/projects/{project_id}/documentation')
    def documentation(project_id: str):
        return service.documentation(project_id)

    @app.get('/api/projects/{project_id}/history')
    def history(project_id: str):
        return service.store.notes(project_id, 'question')

    @app.get('/api/projects/{project_id}/export')
    def export(project_id: str):
        content = service.export(project_id)
        return Response(content, media_type='application/zip', headers={
            'Content-Disposition': 'attachment; filename="CodeArchaeologist-report.zip"'})

    web = Path(__file__).parent / 'web'
    if (web / 'assets').exists():
        app.mount('/assets', StaticFiles(directory=web / 'assets'), name='assets')

    @app.get('/', include_in_schema=False)
    def index():
        if not (web / 'index.html').exists():
            raise AppError('The frontend has not been built. Run npm install and npm run build inside frontend.', 503)
        return FileResponse(web / 'index.html', headers={'Cache-Control': 'no-cache'})

    if seed_demo and not service.store.list():
        project = service.demo()
        service.analyze(project['id'])
    return app
