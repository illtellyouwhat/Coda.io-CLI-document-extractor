# Coda Export Toolkit – Low-Level Summary

This document inventories the important modules, their responsibilities, and the main data flows after the October 2025 refactor. Use it as an implementation map when extending or debugging the toolchain.

---

## Core Package (`coda_export/`)

### `__main__.py`
- Typer CLI entry point.
- Parses options (`--doc-id`, `--out`, filters, row toggles, etc.); default `--out` is `Structure/`.
- Sets up logging (`log.txt` alongside the export), loads API token, constrains requested rows.
- Invokes `CodaExporter`. On success calls `bootstrap_scripts.run_bootstrap.generate_artifacts()` so TOC JSONLs land in the export root.
- Any bootstrap failure is logged but does not abort the export.

### `api.py`
- Houses `CodaAPI`, a `requests` Session wrapper with retry/backoff (via `tenacity`).
- Provides helpers for GET, POST, pagination, and binary downloads (canvas exports).
- Handles exponential backoff, rate-limit awareness, and strips auth headers when downloading presigned assets.

### `extract.py`
- `CodaExporter` orchestrates the export.
- Key steps:
  1. `_write_doc()` → `doc.json`.
  2. `_write_pages()` → page metadata JSONs + HTML/Markdown canvases. Calls `_extract_canvas_refs_html` (from `canvas_parser.py`) to build `_page_elements`.
  3. `_collect_tables()` + `_process_tables()` → table schemas, view metadata, optional sample rows.
  4. Optional branches `_process_formulas()` / `_process_controls()` if toggled on.
  5. `_write_edges()` persists legacy relation edges (`relations/edges.jsonl`).
  6. `_write_readme()` emits run summary.
  7. `_write_page_index()` writes `pages/page-content.ndjson` from `_page_elements`.
- Tracks counts for logging (`ExportCounts` dataclass).

### `canvas_parser.py`
- Uses BeautifulSoup to parse each `canvas.html`.
- Emits normalized dictionaries with `pageId`, `elementType`, `ordinal`, `text`, `codaId`, plus an `attributes` payload (view config, control metadata, hrefs, etc.).
- Feeds `_page_elements`, which ultimately write `pages/page-content.ndjson` and help bootstrap scripts connect views/controls to pages.

### `derive_edges.py`
- Legacy helper that inspects table schemas to derive lookup edges (`relations/edges.jsonl`).
- Still used by `_write_edges()`; newer, richer graph edges are built by `bootstrap_scripts/build_dependency_index.py`.

### `writers.py`
- Thin utilities for writing JSON and NDJSON files, ensuring parent directories exist.

### `utils.py`
- Provides the `ExportConfig` dataclass, token loading (`load_token`), regex filter compilation, logging setup, and row clamping.

---

## TOC-Layer Package (`bootstrap_scripts/`)

### `run_bootstrap.py`
- CLI for manual regeneration (`python3 bootstrap_scripts/run_bootstrap.py --export-root Structure ...`).
- Exposes `generate_artifacts()` so other code (CLI, tests) can trigger the same workflow programmatically.
- Pipeline: `collect_export()` → `build_crosswalk()` → `build_normalized_views()` → `build_dependency_index()` → `write_jsonl`.

### `export_loader.py`
- Walks an export directory and assembles an in-memory context:
  - Doc metadata, pages, tables (with column caches), views, controls, formulas.
  - Relations from `relations/edges.jsonl`.
  - Page content rows (`pages/page-content.ndjson`) grouped per page.
- Normalizes paths so downstream writers can emit repo-relative references.

### `build_crosswalk.py`
- Generates one record per asset (doc/page/table/column/view/control/formula).
- Fields include friendly names, IDs, parent references, ordinals, and `Structure/...` paths.
- Backs the “lookup” step in LLM prompts.

### `normalize_views.py`
- Emits normalized view rows capturing base tables, parent pages, display columns, layout, filters, groupings, and sorts.
- Ensures missing values appear as `null` for diff stability across exports.

### `build_dependency_index.py`
- Produces the comprehensive relation graph:
  - Column formulas (`has_formula`)
  - Lookups (`lookup_to_table`)
  - Views to base tables (`uses_table`)
  - Controls/formulas placed on pages (`placed_on_page`, `button_on_page`, `defined_on_page`)
  - Canvas-derived edges (`view_on_page`, `control_on_page`) sourced from `page-content.ndjson`
- Each row includes IDs, friendly names (when resolvable), and evidence paths (`Structure/...`).

### `utils.py`
- Shared helpers for JSON/NDJSON IO, path normalization, and directory creation.

---

## Data Flow Summary
```
CLI (--doc-id) ──► CodaExporter
                  ├─ doc.json
                  ├─ pages/*.json + canvases + page-content.ndjson
                  ├─ tables/*/schema.json [+ sample-rows.ndjson]
                  ├─ views/*/view.json
                  ├─ controls/*.json
                  ├─ formulas/*.json
                  └─ relations/edges.jsonl
                        │
                        ▼
  generate_artifacts()
        ├─ id_crosswalk.jsonl
        ├─ views_normalized.jsonl
        └─ dependency_index.jsonl
```

---

## Supporting Documentation
- `docs/Human/quickstart.md` – setup + first export.
- `docs/Human/help.md` – full CLI flags.
- `docs/Human/BOOTSTRAP.md` – checklist for regenerating/auditing TOC files.
- `docs/Human/TOC.md` – describes what each JSONL file represents.

These docs, combined with the modules above, give contributors everything needed to adapt the exporter or integrate it with LLM-driven analyses.
