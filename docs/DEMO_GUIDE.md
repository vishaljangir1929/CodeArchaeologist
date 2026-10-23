# Capstone demonstration guide

## Prepare before the review

Run START.bat and check that the model-status dialog shows both the generation model and semantic embeddings as ready. Choose Legacy Shop. Keep a downloaded source ZIP ready as a second input. Model files must be installed before an offline demonstration.

The Legacy Shop source is a small, intentionally inspectable reference project. It is not an ecommerce service connected to real payment or email systems.

## Suggested 8-10 minute demonstration

1. **Problem and objective, 45 seconds.** Explain that unfamiliar Python projects are hard to navigate, and that the tool combines program structure with natural-language explanations.
2. **Import, 1 minute.** Choose New analysis and upload a Python project ZIP, enter a local folder, or create the sample analysis. Show the parsing/indexing progress and saved project selector.
3. **Overview, 45 seconds.** Explain module/function counts, estimated complexity, resolved calls, and unresolved calls. These numbers come from the imported source snapshot.
4. **Source explorer, 1 minute.** Open `legacy_shop/models.py` and select `calculate_total`. Show the actual source, argument information, line range, and complexity. Select Explain symbol and compare the model's statements with the code.
5. **Architecture, 1 minute.** Switch between module dependencies and function calls. Filter to `legacy_shop.service`, zoom, and select a graph node to jump to its source.
6. **Code quality, 1 minute.** Open Potentially unused and find `unused_promo_code_normalizer`. Explain why an unreferenced symbol is a review candidate rather than proof that it is safe to remove. Show unresolved calls as an explicit limitation.
7. **Semantic search and Q&A, 1-2 minutes.** In Ask the codebase, use Search code with `Where are empty carts and invalid quantities checked?`. Then use Ask AI with `How does calculate_total compute the cart amount?`. Open a returned source reference. Show that a previous question remains in Recent questions.
8. **Documentation and export, 1 minute.** Generate an AI overview, download the report ZIP, and show its JSON, Markdown, diagrams, offline HTML report, and saved AI notes.
9. **Evaluation and limits, 45 seconds.** Show the regression suite and the saved live-model verification. State that the reference-project retrieval checks are small functional tests, not a broad accuracy claim.

## Useful source facts to check yourself

- `CartItem.subtotal` multiplies product price by quantity.
- `calculate_total` adds item subtotals and rounds the result to two decimal places.
- `send_receipt` formats a receipt and returns a `queued:` string based on its hash. It does not actually deliver email.
- `CheckoutService.validate_cart` contains explicit input checks.
- `unused_promo_code_normalizer` is intentionally present to demonstrate unused-code candidates.

If an AI answer contradicts these facts, identify the discrepancy and show the relevant source. Do not present source-label validation as proof of factual accuracy.

## Explain the technical contribution

- **AST:** turns source text into syntax nodes, allowing definitions, imports, calls, and decisions to be extracted without executing input code.
- **Call graph:** connects functions or classes when a supported call can be resolved. Unresolved calls are preserved for review.
- **Cyclomatic complexity estimate:** starts at one and counts supported decision constructs within the function's own scope; nested function decisions do not inflate the parent function.
- **Grounding:** supplies bounded code excerpts plus AST-derived signatures, calls, graph relationships, metrics, and limitations to the model.
- **Semantic retrieval:** BGE encodes code chunks and questions into vectors; cosine similarity is combined with lexical matching. Stored vectors and source metadata allow results to link back to actual files and lines.
- **Persistence:** SQLite stores projects and generated notes, while local files hold snapshots, reports, and vectors.
- **No source execution:** ingestion copies `.py` files and the analyzer parses them. It does not import the uploaded project, install that project's dependencies, or run its tests.

## Common viva questions

**Where is the AI?** The pretrained embedding model supplies semantic vectors, and the local Qwen model generates source-linked explanations. AST parsing and graph construction are deterministic program-analysis components.

**Did you train the models?** No. The application integrates pretrained local models and implements ingestion, structural analysis, retrieval, grounding, validation, storage, and the user workflow. Do not claim model training or fine-tuning.

**Why Python AST instead of tree-sitter?** This edition supports Python, and the standard parser provides its syntax structure without an additional grammar installation. A parser interface can be extended for additional languages later.

**Why no NetworkX or FAISS?** Directed edge lists and NumPy vector operations are sufficient for the bounded local edition. The final implementation should be explained as built, rather than claiming every tool named in an early proposal.

**Does this prove the AI is correct?** No. References are restricted to retrieved source labels, but a model may still misinterpret that source. Source navigation and saved model responses make review possible.

**Can it delete dead code?** No. It surfaces candidates; callbacks, framework conventions, or external callers can still use them.

**Does reanalysis track an original folder live?** No. Each import creates a snapshot. Import the updated folder as a new analysis to inspect changed source. Reanalyze rebuilds the existing snapshot and its index.

**Is it a multi-user hosted service?** No. This release is a local single-user application. Authentication, collaboration, public deployment, and additional programming languages are future extensions.
