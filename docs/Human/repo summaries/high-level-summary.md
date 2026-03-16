# Coda Export Toolkit – High-Level Summary

## Purpose
This repository provides a CLI and supporting scripts that mirror a Coda document into a reproducible file tree. The export captures every structural artifact (doc metadata, pages, tables, views, controls, formulas, relations) and emits a “TOC layer” of JSONL indexes so downstream LLM or analytics workflows can reason about the doc without touching Coda’s API.

## Key Capabilities
- **Deterministic export** – `python -m coda_export --doc-id …` downloads pages, table schemas, view configs, optional sample rows, controls, and named formulas into `Structure/docs/<docId>/…`.
- **Canvas parsing** – each HTML page export is parsed into `pages/page-content.ndjson`, cataloguing views, controls, headings, and links with display ordinals.
- **TOC-layer generation** – after every run the CLI writes three JSONL helpers at the export root:
  - `id_crosswalk.jsonl` (name ↔ ID ↔ path lookup for all resources)
  - `views_normalized.jsonl` (normalized, diff-friendly view metadata)
  - `dependency_index.jsonl` (precomputed relations: formulas, lookups, view usage, control placement, page layout edges)
- **Reusable scripts** – `bootstrap_scripts/run_bootstrap.py` and the `generate_artifacts` entry point allow manual regeneration of the TOC files for archived exports or CI flows.
- **Human-facing docs** – quickstart, CLI help, TOC_audit , and TOC explain setup, flags, and artifact meaning.

## Architecture Overview
```
coda_export/               # Core exporter
├── __main__.py            # Typer CLI; now defaults --out to Structure/
├── api.py                 # Coda REST client with retry/backoff helpers
├── extract.py             # Orchestrates doc/page/table/view/control/formula export
├── canvas_parser.py       # Converts page HTML to normalized element records
├── derive_edges.py        # Builds legacy dependency edges (still feeds NDJSON)
├── writers.py             # JSON/NDJSON output helpers
└── utils.py               # Config models, logging, token loading, filters

bootstrap_scripts/         # TOC-layer generation
├── run_bootstrap.py       # CLI + importable generate_artifacts() helper
├── export_loader.py       # Reads export directories into Python maps
├── build_crosswalk.py     # Emits id_crosswalk.jsonl
├── normalize_views.py     # Emits views_normalized.jsonl
├── build_dependency_index.py  # Emits dependency_index.jsonl
└── utils.py               # Shared JSON/NDJSON helpers
```

## Workflow at a Glance
1. **Setup** – clone, `uv sync`, set `CODA_API_TOKEN`. (See `docs/Human/quickstart.md`.)
2. **Run** – export with the CLI (CLI writes `log.txt`, HTML canvases, JSON artifacts, and TOC layer to `Structure/`).
3. **Inspect** – explore schemas (`tables/*/schema.json`), views, controls, and `pages/page-content.ndjson`.
4. **Index** – use the JSONL files for programmatic navigation or LLM prompts (see `docs/Human/TOC.md`).
5. **Regenerate** – rerun `bootstrap_scripts/run_bootstrap.py` if TOC files need rebuilding for a static export.

## Audience
- **Data/analytics engineers** using Coda metadata offline.
- **LLM prompt engineers** needing deterministic file maps and dependency graphs.
- **Doc maintainers** documenting or auditing complex spaces.

## Notable Choices / Defaults
- Packaged with UV (pinning dependencies via `pyproject.toml` + `uv.lock`).
- Default output directory is `Structure/`, matching the references baked into system prompts.
- TOC-layer generation is part of the export run, ensuring the repo remains LLM-ready without manual steps.
