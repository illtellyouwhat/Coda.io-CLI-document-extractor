# Quickstart: Coda Export Toolkit

This repo packages a CLI that mirrors a Coda doc into structured JSON (plus derived lookup files) so analysts and LLM workflows can inspect schema, views, and dependencies offline. Follow the steps below to get running with the default UV-based setup. Adapt as needed if you prefer another Python toolchain.

## 1. Clone & install
```bash
git clone https://github.com/your-org/codaio_APIcalls.git
cd codaio_APIcalls

# Uses uv (https://github.com/astral-sh/uv) for isolation + locking
uv sync
```
> If you manage environments differently (e.g., `pipenv`, `poetry`, `conda`), inspect `pyproject.toml` / `requirements.txt` and install the listed dependencies manually.

## 2. Configure credentials
- Copy `.env.example` (or create `.env`) and set `CODA_API_TOKEN=<personal token>` with permissions to read the target doc.
- Alternatively export the token in your shell before running the CLI.

## 3. Run an export
```bash
uv run python -m coda_export --doc-id {DocID} --out Structure
```
Key defaults:
- `--out Structure` (can be overridden; holds `docs/<docId>/…` plus the JSONL TOC layer).
   IF YOU CHANGE THE OUTPUT DIR UPDATE Instructions.md APPROPRIATELY.
- Rows, controls, and formulas are included; use `--no-include-rows`, `--no-include-controls`, or `--no-include-formulas` to slim the output.
- `--export-markdown-also` downloads Markdown alongside the HTML canvases.

During the run the CLI logs to `Structure/log.txt` and automatically regenerates:
- `Structure/id_crosswalk.jsonl`
- `Structure/views_normalized.jsonl`
- `Structure/dependency_index.jsonl`

## 4. Inspect the results
- Schema: `Structure/docs/<docId>/tables/*/schema.json`
- Views: `Structure/docs/<docId>/views/*/view.json`
- Canvas HTML/NDJSON: `Structure/docs/<docId>/pages/*`
- TOC summaries: see `docs/Human/TOC.md` for how the JSONL files map the export.

## 5. Regenerate TOC artifacts (optional)
If you need to rebuild them separately:
```bash
uv run python3 bootstrap_scripts/run_bootstrap.py --export-root Structure --output-dir Structure
```

## 6. Next steps
- Review `docs/Human/help.md` for full CLI flag descriptions.
- Include `docs/LLM/sys_files/` if you are integrating the export with an LLM workflow.


