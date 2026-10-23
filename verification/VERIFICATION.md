# Verification record

Verified on 23 October 2026 on this Windows computer using Python 3.12 and CPU inference.

## Automated regression and integration checks

**15 tests passed.** The suite was run against the delivered backend after its final functional changes.

Coverage includes:

- Core symbol extraction and the intentionally unused demo function.
- Nested-function complexity isolation.
- Package roots, `src` layouts, relative imports, and supported instance calls.
- Recursive graph edges and locally shadowed builtin names.
- Avoiding false resolution of an external alias to an unrelated project symbol.
- Parse-error reporting without executing any input source.
- Actual CLI startup and JSON/Markdown/SVG/HTML generation.
- Safe embedding of source strings in the offline HTML report.
- ZIP ingestion, malformed inputs, path traversal, and symlink rejection.
- Project persistence, source retrieval, lexical fallback, documentation, export contents, and reanalysis.
- Local host/origin restrictions.
- Explicit model-unavailable errors, rather than fabricated AI answers.
- Generation request construction, saved notes, and rejection of unknown source labels, using a mock transport only inside isolated tests.

The installed Starlette test client emits a deprecation notice about its HTTPX compatibility path; the tests pass. This notice is not a failed application request.

## Real local models

Both model-ready states were verified through the running HTTP application:

- Generation: **Qwen2.5-Coder-1.5B-Instruct Q2_K**, served by the official llama.cpp Windows CPU runtime.
- Embeddings: **BAAI/bge-small-en-v1.5**, 384 dimensions, using FastEmbed/ONNX Runtime.

`live-model-results.json` records real retrieved symbols, source evidence, generated answers, provider/model metadata, and timing. These calls did not use a mock or paid API.

For four handwritten questions about the six-file Legacy Shop reference project:

- Exact expected symbol in the top three results: **2 of 4**.
- Source excerpts covering the expected function in the top three results: **4 of 4**. A retrieved module excerpt can contain the expected function even when its individual function chunk ranks lower.

These are small functional checks, not a general retrieval-quality benchmark. The sample calculation question took about **24.7 seconds** in the recorded run; runtime depends on the computer and the selected evidence.

The original 0.5B model produced repetition and incorrectly claimed that `send_receipt` sends an email. That failure was caught during live browser testing. It was replaced with the 1.5B quantized model, and the generation instructions and output structure were tightened. The final recorded response correctly distinguishes the queue-like return string from actual email delivery.

The final calculation and symbol explanations describe the input list, subtotal accumulation, and rounded return value. Source-label validation does not prove that every generated sentence or citation is correct. Manual source review is still required, especially with a heavily quantized small model.

## Application and packaging checks

- The documented CLI generated a sample report: 6 modules, 5 classes, 13 functions/methods, 135 source lines, 12 resolved call edges, and no parse errors.
- The browser imported the application's own Python package through the Local folder form. Its saved snapshot contains 22 modules, 118 functions/methods, 2,206 source lines, and no parse errors. These counts describe that snapshot, not a general performance claim.
- Browser navigation was exercised through overview, source explorer, both graph modes, module filtering, documentation, question history, and source references.
- The source explorer opened `calculate_total` at its actual definition, lines 29-33 of the reference snapshot.
- The function graph filtered to `legacy_shop.service` displayed 5 nodes and 1 internal resolved edge.
- A Python wheel built successfully and installed into a separate virtual environment without project runtime dependencies. Its packaged contents were checked for the React assets, offline report template, and reference Python sources. API dependencies were separately installed and exercised in the prepared application environment.
- The Windows START.bat launcher correctly detected an already running application and exited successfully with `--no-browser`.
- The frontend was built from its source using esbuild; compiled assets are included for normal use without Node.js.
- An AI project overview was generated through the browser and remained available after reloading the application.
- A live export contained 12 files, including the saved real-model notes; `sample-report.zip` is included as an inspectable example.
- Desktop and mobile breakpoints were checked. At the mobile check, the page width matched the document client width, with no page-wide horizontal overflow. Wide documentation tables use their own horizontal scrolling.

The clean virtual-environment wheel check validates package installation and included assets. It is not a claim that the full online installer was rerun from scratch on a second physical computer. First-time model downloads were actually performed and checksum verified on this computer.

## Boundaries

This delivery is a working local single-user Python capstone edition. It does not implement public hosting, accounts/authentication, repository URL cloning, IDE integration, other programming languages, duplicate-code detection, or live watching of source folders.

Static call resolution and potentially unused-code findings are heuristic. AI factual accuracy, general retrieval accuracy, large-repository scaling, and reduced onboarding time have not been established by these checks.
