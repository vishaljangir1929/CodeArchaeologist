# Project roadmap

## Implemented local edition

- Folder, ZIP, and reference-project ingestion into saved Python snapshots.
- AST symbol extraction, supported call resolution, dependency graphs, and review metrics.
- Source explorer, graph filters, documentation, and portable exports.
- Local semantic retrieval with explicit lexical fallback.
- Local Qwen explanations and questions with saved source evidence.
- SQLite persistence, Windows launchers, and checksum-verified model setup.
- Phase-I report, editable presentation, detailed design, and review preparation.

See [verification](../verification/VERIFICATION.md) for the evidence and limits of the performed checks.

## Next priority: broader evaluation

1. Select independent Python projects of different sizes and structures, and record exact revisions.
2. Manually label representative definitions, imports, and resolvable calls.
3. Prepare source-grounded questions before inspecting retrieval rankings.
4. Measure exact-symbol retrieval and source coverage separately.
5. Review factual correctness and citation relevance separately for every answer.
6. Record indexing time, memory, source size, and repeated query/generation latency on a stated environment.

The current four-question fixture check is a functional check, not a benchmark of general accuracy. A larger model or reranker should be evaluated against a fixed comparison set.

## Possible extensions

Direct Git URL imports, additional programming languages, change-aware documentation, IDE integration, duplicate-code analysis, and authenticated multi-user deployment remain separate development work. No completion dates or implemented status are claimed for these extensions.
