# Getting started

The tested environment is **Windows x64 with Python 3.12**. Normal use does not require Node.js, a GPU, or a paid model API.

## Fresh GitHub clone

1. Install Python 3.12 from [python.org](https://www.python.org/downloads/), with Python on PATH.
2. Clone or download the repository into a writable folder. Extract a downloaded ZIP before running anything inside it.
3. Run `INSTALL.bat` to create `.venv` and install pinned Python dependencies.
4. Run `SETUP_AI.bat` once to download the CPU runtime, code model, and embedding model.
5. Run `START.bat`, wait for model loading, and keep the terminal open.
6. Open **http://127.0.0.1:8765** if the browser does not open automatically.

If several Python versions are installed:

```powershell
py -3.12 scripts/bootstrap.py
.\SETUP_AI.bat
.\START.bat
```

The code model is approximately 718 MiB and the embedding weights approximately 67 MB. Allow at least 2 GB free disk space for dependencies, caches, and snapshots. Setup needs internet access. Ordinary operation uses local files and services after setup.

## Original prepared copy

The original local delivery contains prepared `.runtime` and `.models` folders. In that copy, double-click `START.bat`. Those large folders are deliberately excluded from Git, so a fresh clone must run setup.

## First walkthrough

1. Choose **Legacy Shop**, the included reference project.
2. Open **Source explorer** and locate `calculate_total`.
3. Switch **Architecture** between module dependencies and function calls.
4. Review **Code quality** and explain why an unused candidate may still be used dynamically.
5. Open **Search code** and ask where empty carts are checked.
6. Use **Ask AI** for an explanation, then inspect its source references.
7. Choose **Export report** to download the generated documentation.

The reference `send_receipt` function returns a queue-like string. It does not implement actual email delivery. Use it to demonstrate why source review matters.

## Import your own code

Choose **New analysis** and upload a ZIP or enter a local folder path. A downloaded GitHub repository ZIP is supported. Direct Git URL cloning is not implemented.

Imports accept Python source within these limits: 30 MB uploaded ZIP, 60 MB expanded archive, 500 Python files, and 1 MB per source file. The app creates a saved snapshot and never imports or executes the supplied project.

**Reanalyze** rebuilds the saved snapshot and index. To inspect changed original source, import it as a new project.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Missing Python dependency | Run `INSTALL.bat` and check its terminal output. |
| Setup download fails | Check connectivity and disk space, then rerun `SETUP_AI.bat`. Completed checksum-verified files are reused. |
| AI unavailable | Open model status, check `data/local-model.log`, and restart the app. Static reports remain available. |
| Search reports lexical mode | Install embeddings and reanalyze that snapshot to build its semantic index. |
| Port 8765 already used | Launch with `python run.py --port 8770` using the installed environment. |
| A previous analysis stopped halfway | The next startup marks it failed. Retry Reanalyze. |
| Syntax errors in imported source | Inspect Code quality and the original snapshot. The app does not repair imported code. |

Keep the service local. It has no multi-user authentication or public deployment configuration. Press **Ctrl+C** in the launcher terminal to stop the app and the model process it owns.

Continue with the [full user guide](USER_GUIDE.md), [architecture](ARCHITECTURE.md), or [demo guide](DEMO_GUIDE.md).
