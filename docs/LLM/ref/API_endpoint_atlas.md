# Coda API Endpoint Atlas + Hydration Playbook (Corrected)
_Last verified against [Coda API v1](https://coda.io/developers/apis/v1) — 2025-10-21_

> Purpose: concise, LLM-friendly reference to the **documented** Coda v1 API surface for structural exports and hydration  
> (pages ⇄ tables ⇄ columns ⇄ rows, plus controls & formulas).

---

## 1) Endpoint Catalog (Official)

### A. Docs (root)
- **`GET /docs`** — List docs visible to the API token. Supports pagination.
- **`GET /docs/{docId}`** — Fetch document metadata (name, owner, links, counts). Serves as crawl root.

### B. Pages & Canvas
- **`GET /docs/{docId}/pages`** — List pages (id, name, parent, browserLink, contentType).
- **`GET /docs/{docId}/pages/{pageIdOrName}`** — Get metadata for a specific page.
- **`POST /docs/{docId}/pages/{pageIdOrName}/export`** — Start export job for full page canvas (`outputFormat: html|markdown`).
- **`GET /docs/{docId}/pages/{pageIdOrName}/export/{requestId}`** — Poll for export status until `status: complete`, then use `downloadLink`.


### C. Tables & Views
- **`GET /docs/{docId}/tables`** — List all tables in a doc, including **views**.  
  Each item includes `tableType` ("table" or "view") and `sourceTable` for views.
- **`GET /docs/{docId}/tables/{tableId}`** — Retrieve metadata for a specific table (or view).
- **(No `/tables/{tableId}/views` endpoint)** — Enumerate views by filtering `tableType=view`.

### D. Columns (Schema)
- **`GET /docs/{docId}/tables/{tableId}/columns`** — List columns for a table/view.  
  Includes `id`, `name`, `type`, `formula`, `calculated`, and `lookup.table.id`.
- **`GET /docs/{docId}/tables/{tableId}/columns/{columnId}`** — Get single column metadata.

### E. Rows (Data)
- **`GET /docs/{docId}/tables/{tableId}/rows`** — Fetch rows.  
  Params: `limit`, `pageToken`, `useColumnNames`, `valueFormat=rich` (recommended for fidelity).
- **`GET /docs/{docId}/tables/{tableId}/rows/{rowId}`** — Fetch one row.


### F. Controls
- **`GET /docs/{docId}/controls`** — List controls (id, name, type, parent).
- **`GET /docs/{docId}/controls/{controlId}`** — Get full control metadata (`controlType`, `value`, `action`).

### G. Formulas
- **`GET /docs/{docId}/formulas`** — List named formulas (id, name, parent, browserLink).
- **`GET /docs/{docId}/formulas/{formulaId}`** — Retrieve formula `expression` and computed `value`.

### H. Misc & Metadata Helpers
- **Pagination** — Most list endpoints return `nextPageToken`. Pass `pageToken` to continue.
- **Links** — Most items include `href` (API follow-up) and `browserLink` (UI link).

> Note: Coda treats **views** as tables with `tableType = "view"`. There is no separate “rows for views” endpoint; you query rows on the **base table** and apply the view’s filters yourself if you’re reproducing view semantics off-platform.

---

## 2) Hydration Chains (Recommended Sequences)

### Chain A — Structure & Relations
1. `GET /docs/{docId}`
2. `GET /docs/{docId}/pages`
3. `GET /docs/{docId}/tables`
4. For each view: read `sourceTable.id` (base table id) and `parent.id` (hosting page)
5. For each **unique** base table `grid-*` encountered: `GET /docs/{docId}/tables/{tableId}/columns`
6. Derive relation edges from column schema (`lookup.table.id`, `meta.format`, `isArray`) → emit `{fromTableId, columnId, toTableId}`

### Chain B — Page Canvas (Visual Content)
1. `GET /docs/{docId}/pages`
2. For each page:  
   a. `POST /pages/{pageId}/export`  
   b. Poll via `GET /pages/{pageId}/export/{requestId}`  
   c. Download via `downloadLink`
3. Parse HTML/Markdown for embedded items (`viewId`, `tableId`, `controlId`, `buttonId`).
4. Cross-link those IDs to their respective JSON metadata.

### Chain C — Controls & Formulas
1. `GET /docs/{docId}/controls` → list
2. For each: `GET /docs/{docId}/controls/{controlId}` (capture `controlType`, `value`, actions)
3. `GET /docs/{docId}/formulas` → list
4. For each: `GET /docs/{docId}/formulas/{formulaId}` (capture `expression`, `value`, and detect volatile functions like `Now()`/`Today()`/`User()`)

### Chain D — Sample Data (for LLM examples)
1. From Chain A, collect unique base tables
2. For each: `GET /docs/{docId}/tables/{gridId}/rows?limit=100&useColumnNames=true`
3. Persist NDJSON lines keyed by column ids/names for lightweight RAG samples

### Chain E — **Full lineage graph (one pass)**
1. Run Chain A for structure + relations
2. Run Chain C for logic nodes
3. Join: page → view → base table → columns; columns with lookups → edge to target table; page → controls; page/formula nodes → connect to referenced tables/columns when expressions mention them (optional static parse)

---

## 3) Common Fields & How They’re Useful

### Identity & Links
- **`id`** — Stable identifier. **Prefixes** convey type: `canvas-` (page), `grid-` (base table), `table-` (view), `c-` (column), `r-` (row), `ctrl-` (control), `f-` (named formula).
- **`type`** — Resource kind for this object (e.g., `"page"`, `"control"`, `"formula"`) or for a **nested reference** such as `parent.type`.
- **`href`** — API follow-up URL. Use to **hydrate** details per item (formulas, controls, etc.).
- **`browserLink`** — UI URL. Helpful for human debugging and LLM-generated “open in Coda” suggestions.

### Tables & Views
- **`tableType`** — `"table"` (base) or `"view"` (presentation). Drives logic for where to fetch columns/rows and how to map `sourceTable`.
- **`sourceTable`** — Present on views; points to base table `{ id, name }`.
- **`parent`** — Where this thing lives (commonly `type: "page"`). Lets you build `page → view` placement.

### Columns (schema)
- **`name`, `type`** — Column label and base type (text, number, checkbox, people, relation, canvas, etc.).
- **`formula`** + **`calculated`** — Presence of expression and whether the column computes per-row.
- **`meta.format` / `lookup`** — Rich formatting & relation metadata. Key fields:
  - `format.type` (e.g., `lookup`, `text`, `date`)
  - `lookup.table.id` (target table for relations)
  - `isArray` (multi-select/many-to-many)

**Use:** drives **relation graph** and column semantics for LLM answers (e.g., “Tasks link to Projects via `Project` column, many-to-one”).

### Rows (data)
- **`items[]`** — Row array; each row has `id`, `values`/`cells` keyed by column id/name.
- **`nextPageToken`** — For paging. Persist alongside last-seen sort/filter if you plan resumable exports.

### Controls
- **`controlType`** — Specific kind (text, select, multiSelect, checkbox, dateRange, etc.).
- **`value`** — Current resolved value (watch for personal vs collaborative controls).
- **`parent`** — Typically a page; sometimes a table context for button columns.

**Use:** map **page → controls** for filter wiring; let LLM answer “what inputs drive this dashboard?”

### Formulas (named)
- **`name`** — Display name of the named formula.
- **`value`** — Last computed value returned by the API (may be snapshot/volatile).
- **`expression`** (in hydrated detail) — Formula body; parse to detect references.
- **`parent`** — Usually a page (where it’s defined in UI), sometimes doc-level.

**Use:** expose **logic nodes** the LLM can traverse; tag volatile ones (`Now()`, `Today()`, `User()`) for reasoning about staleness.

### Pagination
- **`nextPageToken` / `pageToken`** — Standard list paging. Always design loops to stop on null.

---

### Implementation Notes
- Prefer **list → follow `href`** for fine-grained hydration (controls/formulas especially).
- Normalize ID prefixes to an internal enum for simpler graph edges.
- Persist a lightweight **edges.jsonl** for relations: one line per relation column → `{type:"relation", fromTableId, columnId, columnName, toTableId, isArray}`.
- For page composition, use **views** (fast) or **page content** (complete). In practice, do both: views build the structural map; content confirms what’s actually rendered.
---

## 5) Reference
- [Official Coda API v1 Docs](https://coda.io/developers/apis/v1)
- [Community: Page Export Announcement](https://community.coda.io/t/more-powerful-page-endpoints-in-the-coda-api/44103)
- [Canvas Column Example](https://community.coda.io/t/api-get-content-of-a-canvas-column/39947)

