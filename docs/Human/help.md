# CLI Usage Guide

This guide walks through the `coda_export` command-line interface, the flags it supports, and how to combine them for common workflows. Run the tool with:

```bash
python -m coda_export --doc-id DOC_ID [options]
```

By default the exporter writes into `./Structure/`, mirroring Coda’s structure under `docs/<docId>/`. At the end of every successful run the helper scripts also regenerate three TOC JSONL files (`id_crosswalk.jsonl`, `views_normalized.jsonl`, `dependency_index.jsonl`) in the export root so downstream LLM processes stay in sync.

## Required flag
- `--doc-id <DOC_ID>` – The Coda document identifier (e.g., `HerO7BFkYl`). This must match the token’s access scope, otherwise the API calls will fail.

## Output & file layout
- `--out <PATH>` *(default: `./Structure`)* – Directory where the export is stored. The tool creates `PATH/docs/<docId>/...` plus the TOC JSONL files in `PATH/`.

## Data volume controls
- `--rows-per-table <N>` *(default: `100`, max hard-clamped to 100)* – Number of sample rows to fetch per table when `--include-rows` is enabled.
- `--include-rows / --no-include-rows` *(default: include)* – Toggle row sampling entirely. Disable if you only need schema metadata.
- `--include-formulas / --no-include-formulas` *(default: include)* – Export named formulas (`formulas/f-*.json`). Turn off for lighter runs when formulas are irrelevant.
- `--include-controls / --no-include-controls` *(default: include)* – Export canvas controls (`controls/ctrl-*.json`). Disable to skip lookup-heavy docs without controls.
- `--visible-only / --include-hidden` *(default: visible-only)* – When true, the column fetcher filters to visible columns. Use `--include-hidden` to pull hidden columns as well.

## Canvas assets
- `--export-markdown-also / --export-html-only` *(default: HTML only)* – Download Markdown alongside HTML for each page canvas. Markdown is handy for quick human review but doubles the canvas download volume.

## Request behaviour
- `--timeout <SECONDS>` *(default: 30.0)* – HTTP timeout per request.
- `--max-retries <N>` *(default: 5)* – Max retry attempts for failed API calls (with backoff).
- `--sleep-initial <SECONDS>` *(default: 0.8)* – Initial backoff duration. The exponential strategy multiplies from this baseline.

## Filtering docs
- `--filter-tables <REGEX>` – Only export tables/views whose name matches the regex. Useful when you want a subset (e.g., `--filter-tables "(Deals|CRM)"`).

## General workflow
1. Set the `CODA_API_TOKEN` (or whichever environment variable your `.env` uses). The CLI exits early if no token is available.
2. Choose an output directory (defaults to `./Structure`) and run the command. Example:
   ```bash
   python -m coda_export --doc-id {DocID} --out Structure --no-include-rows --export-markdown-also
   ```
3. After completion, inspect:
   - `Structure/docs/<docId>/...` for raw doc assets.
   - `Structure/id_crosswalk.jsonl`, `Structure/views_normalized.jsonl`, and `Structure/dependency_index.jsonl` for generated lookup layers.
   - `Structure/log.txt` for API/instrumentation details.
4. Re-run with updated flags as needed; the exporter overwrites prior files in place.

Tip: add `--filter-tables` when iterating on a single table/view—the CLI remains fast, and the derived JSONL files still update with the subset you pulled. To refresh the full dataset afterward, rerun without the filter.
