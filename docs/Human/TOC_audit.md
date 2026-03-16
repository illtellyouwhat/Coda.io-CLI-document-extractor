# Checklist (Human Reference)

This guide documents the TOC-layer artifacts (`id_crosswalk.jsonl`, `views_normalized.jsonl`, `dependency_index.jsonl`) and the steps to regenerate or audit them after a Coda export. The CLI now runs these steps automatically, but the checklist remains the reference for manual reruns, troubleshooting, or validating a downstream handoff.

## When to use this document
- After running `python -m coda_export …` to confirm the JSONL outputs look sane.
- When regenerating artifacts for an archived export with `python3 bootstrap_scripts/run_bootstrap.py`.
- During code reviews or onboarding to understand what “complete export metadata” should contain.

## 1. Establish context
1. Identify the export root (typically `Structure/` or `output/<run>/`).
2. Read `README.md` and `log.txt` inside that directory to note doc ID, toggled flags, and any hydration warnings.
3. Locate the doc folder under `docs/<docId>/`; all subsequent checks reference this path.

## 2. Verify static guidance
- Ensure `docs/LLM/sys_files/directory_contract.md`, `instructions.md`, and `answer_protocol.md` still describe the structure in front of you (e.g., `pages/page-content.ndjson` exists, canvas HTML lives under `pages/<pageId>/canvas.html`). Update them before regenerating dynamic files if anything drifted.

## 3. Regenerate the glue layer (optional manual run)
The CLI calls these scripts automatically, but you can run them by hand:

```bash
python3 bootstrap_scripts/run_bootstrap.py \
  --export-root Structure \
  --output-dir Structure \
  --repo-root .
```

This script loads the export, builds the datasets below, and writes them to the export root.

### 3.1 `id_crosswalk.jsonl`
- Should include one line per doc, page, table, column, view, control, and named formula.
- Each record must expose friendly name, Coda ID, and relative file path (`Structure/docs/...`).
- Spot check pages and tables referenced in recent questions to ensure paths and IDs match reality.

### 3.2 `views_normalized.jsonl`
- One line per view with parent page, base table, display column, layout, and filter/group/sort metadata.
- Confirm parent page paths reference `pages/<pageId>.json`, and layout/filters match a source `view.json`.

### 3.3 `dependency_index.jsonl`
- Aggregates relationships: column formulas (`has_formula`), lookups (`lookup_to_table`), view-to-table (`uses_table`), control and formula placements (`placed_on_page`, `button_on_page`, `defined_on_page`), and page layout entries from `pages/page-content.ndjson` (`view_on_page`, `control_on_page`).
- Ensure each edge cites the evidence path (`Structure/docs/...`). For page layout edges, verify `page-content.ndjson` exists and contains the referenced `pageId`.

## 4. Validation checklist
- All three JSONL files present at the export root.
- `Structure/docs/<docId>/pages/page-content.ndjson` exists (otherwise page relations will be incomplete).
- Randomly open a view record, a control placement, and a column formula entry to confirm the source file aligns with the data.
- Capture any missing artifacts or hydration failures.

## Relationship to `TOC.md`
- `TOC.md` explains *what each JSONL file represents* and why it matters to the LLM.
- This `TOC_audit.md` records *how to produce and audit those files*. Keep both: TOC for conceptual overview, Bootstrap for the operational checklist.

Following this checklist ensures the repo remains a deterministic, LLM-friendly snapshot of any exported Coda doc, even when the automation runs headless.
