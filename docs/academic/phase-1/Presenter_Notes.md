# CodeArchaeologist presenter notes

Suggested total 15 to 18 minutes, including a short live demonstration. Adjust to the guide's allotted time.

Vishal Kumar Jangir presents slides 1 to 7. Syed Mudassir presents slides 8 to 18. Junaid Pasha presents slides 19 to 28. Every member should understand the whole project.

The slide deck also contains these notes in its speaker-note field.

## Before the review

- Confirm the names, USNs, programme, and guide.
- Compare the report with the actual college sample.
- Add genuine geotagged team photographs using Appendix B.
- Start the local application and check model readiness.
- Keep the source open for the demo and review the known limitations.
- Obtain guide approval before printing.

## Slide 1 CodeArchaeologist

Vishal opens the presentation. Explain that the local Python implementation is available for demonstration. Describe the long title without claiming perfect comprehension. Team and guide details follow the populated title slide in the supplied eight-page PDF. Confirm these details before submission.

## Slide 2 Presentation outline

Vishal introduces the problem, objectives, and literature. Syed explains architecture and design. Junaid presents the implementation, results, and next work. This is a suggested speaking allocation, not a statement that each member completed a specific task.

## Slide 3 Problem statement

Vishal describes an unfamiliar Python project with missing documentation. Manual inspection can reveal its behavior, but relationships across files are tedious to trace. The project combines explicit static records with a local language model. Do not repeat the earlier unsupported claim that existing tools cannot explain code.

## Slide 4 Final project objectives

Vishal presents five objectives. Clarify that unused-code findings are candidates and that the project has not measured reduced onboarding time or hallucination rates.

## Slide 5 Literature survey 1

Vishal summarizes the research contributions, then distinguishes research inspiration from the installed models. CodeBERT, Codex, and GraphCodeBERT are not installed components. Sources: https://aclanthology.org/2020.findings-emnlp.139/ https://arxiv.org/abs/2107.03374 https://arxiv.org/abs/2009.08366

## Slide 6 Literature survey 2

Vishal explains that the research studies address related learning tasks. Their published results are not evidence of this application’s accuracy. Sources: https://ink.library.smu.edu.sg/sis_research/4292/ https://aclanthology.org/2020.acl-main.449/ https://arxiv.org/abs/1709.06182

## Slide 7 Identified gaps and challenges

Vishal concludes the literature section. These are engineering requirements for this implementation, not claims that no other tool offers the features. Hand over to Syed for detailed design.

## Slide 8 Methodology

Syed walks through the implemented stages. Analysis does not execute uploaded code. Search and generation operate on saved snapshots. Reanalyze rebuilds a saved snapshot; import changed source as a new project.

## Slide 9 System architecture

Syed explains the actual deployment. React and FastAPI use loopback port 8765. The bundled local llama.cpp server uses port 8081. SQLite stores metadata and notes, while snapshots and indices are files. This is a local single-user application with no application login. See the delivered source docs/ARCHITECTURE.md.

## Slide 10 Detailed module design

Syed gives the contract for each implemented subsystem. The file names are actual source modules. Data moves through ProjectService so the interface does not need to understand parsing internals.

## Slide 11 Data-flow diagram level 0

Syed names this the context diagram. The developer supplies source, questions, and requests. CodeArchaeologist returns results, explanations, source references, or errors. Local models and storage are internal to the system boundary. DFD arrows represent data, not program control.

## Slide 12 Data-flow diagram level 1

Syed describes the logical processes. P1 validates and snapshots input, P2 analyzes it, P3 indexes source, P4 retrieves and explains, and P5 assembles exports. The simplified view combines report and index files in D2 and D3 while D4 is SQLite metadata and notes.

## Slide 13 Data-flow diagram level 2 analysis

Syed expands process 2.0 only. Collector paths feed the parser, which returns typed records and syntax errors. The resolver builds supported call relationships. Metrics and candidate flags then join the records in versioned JSON. Dynamic unresolved calls remain explicit.

## Slide 14 Use-case diagram

Syed explains the single user role and the system boundary. Import and saved-project access are separate use cases. AI explanation requires ready local generation, while static views and search can still work without generation. These are application use cases, not account roles.

## Slide 15 Use-case contracts

Syed presents preconditions and observable outcomes. An invalid ZIP fails without executing code. A model-unavailable answer is a clear error rather than a fabricated explanation. Successful export includes only saved real AI notes.

## Slide 16 Question-answer sequence

Syed reads the sequence from top to bottom. The backend loads report and search index, retrieves evidence, creates bounded context, calls local generation, validates supplied source labels, persists successful notes, and returns the result. Source-label validation cannot establish factual correctness.

## Slide 17 Data and storage design

Syed explains the actual schema. projects.id logically links notes.project_id. The current schema does not declare a database foreign-key constraint. JSON stores summary and citations. Source/report/index files live under a generated project identifier.

## Slide 18 Analysis output contract

Syed explains schema version 1.0.0. Module records contain symbols, imports and parse errors. Call edges contain source, target, label and resolution. Web imports use relative file paths. Source snippets are retrieved from validated snapshot paths, not arbitrary filesystem requests.

## Slide 19 Static-analysis algorithms

Junaid begins implementation. Python ast parses source text without import or execution. Complexity starts at one and counts supported branches in the current function scope. Candidate flags are heuristics. The details are in parser.py and analyzer.py.

## Slide 20 Retrieval and local generation

Junaid explains AST-derived chunks, normalized 384-dimensional BGE vectors, and hybrid ranking. The semantic score has weight 0.8 and lexical cosine 0.2. A labeled lexical fallback is available. Source comments are untrusted context. Sources for model identity: https://huggingface.co/BAAI/bge-small-en-v1.5 and https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF

## Slide 21 Implemented technology stack

Junaid distinguishes this stack from the earlier proposal. This edition uses Python AST and custom graph logic, not tree-sitter or NetworkX. NumPy stores the vector matrix, not FAISS or Chroma. The application does not train a model.

## Slide 22 Working application

Junaid demonstrates the same Legacy Shop project shown in the screenshot. Open Source explorer, select calculate_total, then switch Architecture from module graph to call graph. The picture is a captured running interface, not a design mockup. Evidence: verification/overview-final.jpg and verification/VERIFICATION.md in the source delivery.

## Slide 23 Local AI with inspectable source

Junaid asks the sample question and opens the source references. The real recorded explanation is short and can miscite evidence. For example, the saved calculation answer assigns rounding to a source label that points to checkout. The more focused symbol explanation points directly to calculate_total. Do not claim that source-label validation detects this semantic mismatch. Evidence: verification/live-model-results.json.

## Slide 24 Verification results

Junaid states the measurement scope. Fifteen automated tests passed. Four handwritten semantic questions were evaluated on the six-file fixture. Source coverage counts a module excerpt that contains the expected function. These are distinct retrieval measures. Source: delivered verification/VERIFICATION.md and live-model-results.json, checked 23 October 2026.

## Slide 25 Limitations and future work

Junaid explains that local operation and Python-only scope are current boundaries. Graph resolution is heuristic. A public service would need separate authentication and deployment design. Broad accuracy and onboarding benefit require controlled evaluation.

## Slide 26 Project status and presentation roles

Junaid closes the implementation section. This table describes current software status and a suggested presentation split. All three students should demonstrate understanding of the whole system. Genuine geotagged work photos, guide approval, signatures, and physical printing must be completed before submission.

## Slide 27 References

The six studies are background research, not installed runtime components. Bibliographic entries and model/runtime links are in the Phase-I report. Sources: https://aclanthology.org/2020.findings-emnlp.139/ https://arxiv.org/abs/2107.03374 https://arxiv.org/abs/2009.08366 https://ink.library.smu.edu.sg/sis_research/4292/ https://aclanthology.org/2020.acl-main.449/ https://arxiv.org/abs/1709.06182

## Slide 28 Thank you

All members should be ready to answer questions. Close with a live source walkthrough instead of claiming perfect generated documentation. Guide and student details follow the populated supplied title slide and should be confirmed before final submission.

## Short viva answers

**Did you train an LLM?** No. The application integrates pretrained local models. The project work is ingestion, analysis, retrieval, grounding context, source navigation, persistence, and reporting.

**Why can a function look unused when it is used?** Static analysis may miss callbacks, decorators, framework entry points, or runtime dispatch. A candidate needs human review.

**Does a valid citation prove the answer?** No. The current backend checks that the label was supplied, but a sentence can still be wrong or point to the wrong supplied excerpt.

**Does reanalyze track the original folder?** No. It rebuilds the saved snapshot. Import changed source as a new analysis.

**What actually sends the demo receipt email?** Nothing in the fixture implements email delivery. Inspect send_receipt rather than inferring behavior from its name.

**What does the retrieval result prove?** The four questions demonstrate source retrieval on the small fixture. Exact-symbol success was 2/4 at top three; source coverage was 4/4. These are not general accuracy estimates.