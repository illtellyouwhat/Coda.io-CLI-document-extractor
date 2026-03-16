# Directory Contract for CODA_LLM

This contract defines the canonical meaning of every top-level directory and structured artifact so downstream LLM tooling can resolve file paths deterministically.

| Path | Purpose | Notes |
| --- | --- | --- |
| `Structure/README.md` | Snapshot of the Coda export run configuration and artifact counts. | Use to confirm export parameters (rows suppressed, controls included, etc.). |
| `Structure/log.txt` | Diagnostics from the exporter. | Canvas hydration failures are logged here; cite them when a page JSON lacks body content. |
| `Structure/docs/{DocID}/doc.json` | Doc-level metadata (title, workspace, owner, browser link). | Entry point for doc identity and provenance. |
| `Structure/docs/{DocID}/pages/` | One JSON per canvas/page (`canvas-*.json`). | Metadata: hierarchy, authors, timestamps, visibility flags. Use alongside the HTML/NDJSON artifacts below for body content. |
| `Structure/docs/{DocID}/pages/<pageId>/canvas.html` | Raw HTML export for the page canvas. | Source of truth for headings, buttons, embeds, and other rendered elements. Parsed to build `page-content.ndjson`. |
| `Structure/docs/{DocID}/pages/page-content.ndjson` | Derived index of page elements. | One NDJSON record per element with `pageId`, `elementType`, `ordinal`, Coda identifiers, and enriched attributes (view config, links, etc.). |
| `Structure/docs/{DocID}/tables/` | One directory per table (`grid-*`). Each contains `schema.json`. | `schema.json` lists table metadata and all columns, including formulas and formats. No row data is stored. |
| `Structure/docs/{DocID}/views/` | One directory per view (`table-*`). Each contains `view.json`. | View metadata: parent page, base table, display column, layout, filters, groupings, sorts. |
| `Structure/docs/{DocID}/controls/` | Individual control definitions (`ctrl-*.json`). | Includes control type (slider, select, button), default value, parent page. |
| `Structure/docs/{DocID}/formulas/` | Named formula outputs (`f-*.json`). | Stores resolved value and owning page. |
| `Structure/docs/{DocID}/relations/edges.jsonl` | Lookup edges between tables. | Each line is a JSON object mapping source column/table to target table with array-ness. |
| `Structure/docs/{DocID}/logical.json` *(absent)* | Not generated in this export. | Mention absence if a workflow expects derived document structure. |
| `id_crosswalk.jsonl` | Derived map of resource names ↔ Coda IDs ↔ file paths. | Generated in this repo root for fast reverse lookups. |
| `views_normalized.jsonl` | Derived normalized view configs. | Guarantees consistent key ordering and compatible schema for diffing. |
| `dependency_index.jsonl` | Derived dependency edges. | Precomputed graph: columns→formulas, views→tables, controls/formulas→pages, lookups. |
| `prompt2.md` | Prompting instructions for structural Q&A. | Reference when constructing LLM call instructions. |
| `answer_protocol.md` | Step-by-step LLM answering procedure. | Ensures deterministic responses and required citations. |

Any new artifact MUST be documented here before use in automation so the contract stays authoritative.
