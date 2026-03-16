# CODA_LLM Instruction Guide

This repository equips an LLM to answer structural questions about the exported Coda doc. Follow the playbook below to keep responses precise, grounded, and low-token.

## 1. Know the Assets
- **Raw data** lives under `Structure/` (pages, tables, views, controls, formulas, relations, exporter log).
- **Canvas content** is captured in `Structure/docs/{docID}/pages/page-content.ndjson` (normalized records) with the underlying HTML at `Structure/docs/{docID}/pages/<pageId>/canvas.html`.
- **Navigation aids** in repo root: `directory_contract.md`, `id_crosswalk.jsonl`, `views_normalized.jsonl`, `dependency_index.jsonl`.
- **Prompt scaffolding**: `answer_protocol.md` (mandatory response sequence).
- **Skills** in `Skill/`: `SKILL.MD.md` defines the “Coda Document Analysis” skill; `Skill/references/*.md` provide reusable patterns, anti-patterns, and templates.

## 2. Startup Sequence
1. **Load the contract** – Read `directory_contract.md` to confirm what each path means. Treat it as source of truth before touching raw JSON.
2. **Adopt the protocol** – Load `answer_protocol.md` and follow the numbered procedure for every query (clarify → locate → verify → cite → warn).
3. **Only load skills when needed** – Pull in `Skill/SKILL.MD.md` (and targeted references) when analysis, optimization advice, or refactor planning is required; skip for simple lookups to save tokens.

## 3. Locating Information
- **First stop:** `id_crosswalk.jsonl` to resolve any human-friendly name or Coda ID to its file path.
- **Schema/details:** Go to the corresponding JSON under `Structure/docs/{docID}/...` (tables → `grid-*/schema.json`, views → `table-*/view.json`, etc.).
- **Page layout:** Use `Structure/docs/{docID}/pages/page-content.ndjson` to list headings, views, controls, and other elements in display order; fall back to the matching `canvas.html` if the NDJSON seems stale.
- **Relationships:** Check `dependency_index.jsonl` for precomputed edges and `Structure/docs/{docID}/relations/edges.jsonl` for lookup columns.
- **Export caveats:** If a canvas file lacks body content, cite `Structure/log.txt` which records the 404 hydration warnings.

## 4. Using Skills Effectively
- **When to load:** Invoke `Skill/SKILL.MD.md` when the task involves diagnosing architecture, redundancy, or refactor impacts. Pull specific reference files (`analysis_templates.md`, `anti_patterns.md`, etc.) as needed for guidance.
- **How to integrate:** Blend skill insights with the structural data by anchoring every claim in the JSON source files while using the skill docs to shape recommendations or risk assessments.

## 5. Answer Workflow (TL;DR)
1. Clarify the question scope.
2. Resolve IDs and paths via `id_crosswalk.jsonl`.
3. Read the definitive JSON artifact(s).
4. Pull page structure from `Structure/docs/{docID}/pages/page-content.ndjson` (and HTML if needed) before confirming dependencies (`dependency_index.jsonl`, relations).
5. Compose a concise answer citing `Structure/...` paths; note any missing data with `Structure/log.txt`.
6. Reference skill materials only when deeper analysis is requested.

Stick to this flow to minimize token usage, avoid hallucinations, and ensure every answer is traceable back to the exported Coda data.
