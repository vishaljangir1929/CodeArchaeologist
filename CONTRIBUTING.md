# Contributing

CodeArchaeologist is a local Python capstone with a React interface. Keep implementation claims consistent with the source and preserve the distinction between static findings and AI interpretations.

## Set up development

Follow [Getting started](docs/GETTING_STARTED.md) with Python 3.12. The application uses a `src` package layout. Normal use loads the prebuilt frontend; editing React requires Node.js 24 and `npm ci` inside `frontend/`.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
python tools/check_repository.py
```

To rebuild the UI:

```powershell
cd frontend
npm ci
npm run build
```

Commit the compiled UI with its source changes so normal users do not need Node.js. Rebuilds can change generated output; review the diff rather than committing unrelated build churn.

## Validation expectations

- Run checks appropriate to the change. Preserve meaningful regression coverage for parser, path, API, and persistence changes.
- The automated regression suite does not need model downloads. It isolates generation protocol checks with mock transport.
- Use `scripts/verify_live.py` only with the real app and both local models ready. Retain real provider/model metadata, source references, and timing. Never replace live evidence with mock answers.
- Inspect UI changes in the browser and check narrow layouts when affected.
- Update the technical and academic documentation when observable behavior or scope changes.

## Pull requests

Describe the problem, resulting behavior, relevant validation, and material limitations. For a source-analysis change, include a small reproducible example. For an AI change, distinguish factual accuracy, citation relevance, and retrieval quality.

Do not commit downloaded models, installed environments, analyzed user repositories, private work photos, credentials, or generated local workspace records. These are not source dependencies. The model setup script recreates the required runtime assets.

## Licensing and acknowledgements

The maintainers have not selected a license for the original project code. Keep upstream acknowledgements and dependency license metadata intact. Discuss licensing decisions with the maintainers rather than assuming a third-party license covers the whole repository.
