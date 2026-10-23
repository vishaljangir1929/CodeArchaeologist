# CodeArchaeologist

**An AST-guided, LLM-powered system for Python code comprehension and automated documentation.**

A working local capstone application: import a Python project, explore its structure, inspect code-quality findings, generate documentation, search by meaning, and ask a local language model questions with source references.

## Start on this computer

This section applies to the original prepared local delivery. A fresh GitHub clone must complete the installation steps in the next section first.

1. Double-click **START.bat**.
2. Wait for the local model to load. Keep the terminal open.
3. The application opens at **http://127.0.0.1:8765**.
4. Choose **Legacy Shop** to explore the reference project, or select **New analysis** to import your own Python project.
5. Press **Ctrl+C** in the terminal when finished. The model process started by the app will also stop.

If the application is already running, START.bat opens the existing instance.

## Install on another Windows computer

Use Windows x64 and Python 3.12, which is the tested Python version. Select **Add Python to PATH** when installing Python from [python.org](https://www.python.org/downloads/).

1. Extract the source ZIP into a normal writable folder. Do not run it inside the ZIP viewer.
2. Run **INSTALL.bat**. It creates a `.venv` and installs the Python application and its dependencies.
3. Run **SETUP_AI.bat** once. It downloads the official llama.cpp CPU runtime, a quantized Qwen2.5-Coder-1.5B-Instruct model, and BGE semantic embeddings. The code-model file is about 718 MB and the embedding weights are about 67 MB. Allow at least 2 GB of free disk space for dependencies, caches, and source snapshots.
4. Run **START.bat**.

Internet access is needed for first-time dependency/model installation. Normal analysis, search, and generation use local files and local processes after setup. A GPU and a paid API key are not required.

The portable source ZIP deliberately excludes downloaded model weights, installed dependencies, and workspace records. SETUP_AI.bat prepares those files on the destination computer. The original prepared folder on this computer already includes them.

If several Python versions are installed, use `py -3.12 scripts/bootstrap.py` instead of INSTALL.bat, then run SETUP_AI.bat and START.bat.

## Use the application

### Import source

**New analysis** offers three inputs:

- **Upload ZIP:** a project archive containing Python files, including GitHub's downloaded ZIP archives.
- **Local folder:** an absolute folder path on the computer running the server.
- **Sample project:** the included Legacy Shop reference project.

Limits: 30 MB uploaded ZIP, 60 MB expanded archive, 500 Python files, and 1 MB per Python source file. Generated environments and vendor folders are skipped. Only Python source is copied into the analysis snapshot. Uploaded code is parsed and never imported or executed.

Each import creates a saved snapshot. To analyze changed source, create a new analysis from the updated folder or ZIP. **Reanalyze** recomputes the existing snapshot and rebuilds its search index; it does not reread an original folder that has changed.

### Explore results

- **Overview:** module/function counts, source lines, resolved and unresolved calls, complexity, and review signals.
- **Source explorer:** browse files, jump to definitions, inspect line numbers, and explain a selected file or symbol.
- **Architecture:** switch between module dependencies and resolved function calls; filter by module, zoom, and select a node to open its source. Large graphs display a bounded subset of nodes with a hidden-node count.
- **Code quality:** inspect potentially unused symbols, high-complexity functions, long functions, unresolved calls, and parse errors.
- **Documentation:** view static analysis documentation, generate a local-AI project overview, and revisit saved explanations.
- **Ask the codebase:** choose **Ask AI** for generated explanations or **Search code** for retrieved source snippets. Source references open the relevant file and line.
- **Export report:** download JSON, Markdown module references, SVG diagrams, an offline HTML report, and saved AI notes in a ZIP.

Project records, source snapshots, embeddings, explanations, and question history persist in `data/`. Select a project from the project dropdown to reopen it.

### Suggested first questions

For Legacy Shop:

- `How does calculate_total compute the cart amount?`
- `Where are empty carts and invalid quantities checked?`
- `How is a loyalty discount calculated?`
- `What does send_receipt return? Does it actually send an email?`

The receipt sample returns a queue-like string; it does not implement an email delivery service. Distinguishing that behavior is useful when reviewing AI explanations.

## What each component does

| Component | Implementation | Purpose |
| --- | --- | --- |
| Parsing | Python `ast` | Extracts definitions, imports, signatures, calls, source locations, and estimated complexity. |
| Graph analysis | Python symbol indexes and directed edge lists | Resolves supported local/imported calls and module dependencies; records unresolved calls. |
| API | FastAPI + Uvicorn | Handles imports, analysis, source retrieval, search, explanations, history, and export. |
| Persistence | SQLite + local snapshot/report/index files | Keeps project records, AI notes, source evidence, and generated artifacts. |
| Semantic retrieval | FastEmbed + BGE-small-en-v1.5 + ONNX Runtime + NumPy | Encodes AST-derived source chunks and combines cosine similarity with lexical matching. |
| Local generation | llama.cpp + Qwen2.5-Coder-1.5B-Instruct Q2_K | Produces short, source-linked facts using code excerpts and structured static-analysis context. |
| Alternative generation | Ollama | Uses a locally installed model selected with an environment variable. |
| Frontend | React + Lucide + react-markdown | Provides the working browser interface. SVG graphs are generated from actual analysis data. |
| Frontend build | esbuild | Produces the included local JS/CSS assets; Node.js is only needed to modify/rebuild the frontend. |

Python AST and custom graph logic replace the proposed tree-sitter/NetworkX combination for the Python-only edition. The vector index is stored as NumPy arrays and JSON metadata rather than FAISS/ChromaDB. These are deliberate implementation choices; the final college report should describe the implemented stack accurately.

## Use a different local model with Ollama

The included compact model keeps installation and CPU inference manageable. It can make factual mistakes and is intended for a local demonstration. A more capable model may improve explanations.

Install [Ollama](https://docs.ollama.com/windows), then run these commands in PowerShell:

```powershell
ollama pull qwen2.5-coder:1.5b
$env:CODEARCH_OLLAMA_MODEL = 'qwen2.5-coder:1.5b'
.\.venv\Scripts\python.exe run.py --no-ai
```

`--no-ai` prevents the bundled llama.cpp process from starting; the backend can still connect to a running Ollama service. The application checks the bundled model server first, then Ollama. Stop a previous bundled application instance before switching providers.

Ollama generation uses its [chat API](https://docs.ollama.com/api/chat). The bundled server uses llama.cpp's [schema-constrained response support](https://github.com/ggml-org/llama.cpp/tree/master/tools/server). Model names and download sizes can be checked in the [Ollama model library](https://ollama.com/library/qwen2.5-coder).

## Command-line use

After INSTALL.bat, open a terminal in the project folder:

```powershell
.\.venv\Scripts\codearch.exe analyze sample_project --out reports --html
.\.venv\Scripts\codearch.exe inspect reports\analysis.json
.\.venv\Scripts\codearch.exe search reports\analysis.json checkout
.\.venv\Scripts\codearch.exe serve
```

CLI `search` is explicitly a keyword search over an exported JSON report. The web application's **Search code** uses semantic retrieval when the embedding model and project index are ready.

## Development and tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The suite covers CLI generation, parser regressions, import/call resolution, ZIP handling, source traversal, persistent projects, API workflows, export contents, model-unavailable behavior, and source-reference validation. Mock model responses are used only in isolated unit tests. The live verification script calls the real local models:

```powershell
.\.venv\Scripts\python.exe scripts\verify_live.py
```

See `verification/VERIFICATION.md` and `verification/live-model-results.json` for the performed checks and actual model responses. The small reference-project checks are not a general accuracy benchmark.

To edit the React interface, install Node.js, then:

```powershell
cd frontend
npm ci
npm run build
cd ..
```

The compiled interface is written into `src/codearchaeologist/web/`. Restart the server after Python changes; reload the browser after frontend builds.

## Troubleshooting

- **Missing dependency:** run INSTALL.bat. Do not move or delete `.venv` or `.runtime` while the app is running.
- **Model setup fails:** check internet access and free disk space, then rerun SETUP_AI.bat. Completed downloads are checksum verified and reused.
- **AI is unavailable:** open the model-status button, inspect `data/local-model.log`, and restart with START.bat. Search and static analysis still work without generation.
- **Search says keyword index:** install semantic embeddings, then choose Reanalyze for that project.
- **Port 8765 is occupied:** try `python run.py --port 8770`; the server always binds to the local computer.
- **An analysis failed:** inspect the displayed error and try Reanalyze. An interrupted analysis is marked as failed on the next startup rather than appearing permanently active.
- **Invalid Python source:** parse errors are shown in Code quality, and the original snapshot is still viewable.

## Practical scope and limitations

This is a local, single-user Python capstone edition. It has no user accounts, public hosting, repository URL cloning, IDE extension, or support for Java/JavaScript/C++. Upload a downloaded repository ZIP or use a local folder.

Call resolution is best-effort. Reflection, decorators, frameworks, higher-order functions, type-dependent dispatch, and callbacks may be unresolved. Potentially unused symbols need human review. Complexity is a static estimate, not measured runtime performance. Near-duplicate code detection is outside this edition.

AI source labels are checked against the retrieved evidence, but that does not prove the explanation is factually correct. The small model can miss details, misinterpret control flow, or invent intent. Verify claims in the source. No measured reduction in onboarding time or hallucination rate is claimed.

The app binds to loopback and rejects cross-origin application requests. It is designed to be used on the same computer. Keep it local; this implementation does not provide multi-user deployment authentication.

## Further reading

- `docs/DEMO_GUIDE.md`: an ordered capstone demonstration and talking points.
- `docs/ARCHITECTURE.md`: source layout, data flow, schema, and API routes.
- `THIRD_PARTY.md`: upstream components, model sources, and licenses.
