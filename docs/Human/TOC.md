# TOC Overview

This note explains the three derived JSONL artifacts that every export produces. They act as the “table of contents” (TOC) for downstream LLM work so the model can reason over the directory without scanning hundreds of raw JSON files.

## `id_crosswalk.jsonl`
- **Purpose:** Universal lookup table from human-friendly names → Coda IDs → file paths.
- **Contents:** One record per doc, page, table, column, view, control, and named formula. Each row carries metadata (IDs, names, parent IDs, ordinals) and the relative `Structure/...` path to the canonical JSON artifact.
- **Why it matters:** When the LLM receives a question (“What columns are in *Advertisers*?”), it first resolves names through this file. That means it never has to guess the right directory or spelunk the filesystem, keeping responses deterministic and auditable.

## `views_normalized.jsonl`
- **Purpose:** Canonical, diff‑ready snapshot of every view configuration.
- **Contents:** Each row anchors a view ID to its base table, parent page, display column, layout, filters, groupings, sorts, and source file path. Fields are normalized into a consistent schema (missing data is `null`) so tools can diff across exports or preload view context quickly.
- **Why it matters:** Views reshape tables; without this file the LLM would need to open many `view.json` files to understand layouts or filters. The normalized ledger lets prompts or automations reason about where views live, how they’re configured, and how they relate to the base tables.

## `dependency_index.jsonl`
- **Purpose:** Precomputed graph of relationships the LLM relies on for cross‑resource reasoning.
- **Contents:** Relations include column formulas (`has_formula`), lookups (`lookup_to_table`), view→table links (`uses_table`), control placements (`placed_on_page`, `control_on_page`, `button_on_page`), formula placements, and page layout entries derived from `pages/page-content.ndjson`. Each record references the source/target IDs, names, and the path where the evidence lives.
- **Why it matters:** Many questions hinge on dependencies (“Which pages surface *Sales Forecast*?”, “What powers this button?”). By walking this index the model answers those queries without rescanning raw JSON or missing hidden relations, and it can cite the exact supporting files every time.

Together these artifacts give the LLM a fast index of *what exists*, *where it lives*, and *how it connects*. They turn the export directory into a navigable knowledge graph rather than a pile of unrelated JSON dumps.
