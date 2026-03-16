# Answer Protocol for CODA_LLM

Follow this deterministic sequence for every user query. Abort and escalate only if a required artifact is missing from the directory contract.

1. **Clarify scope** – Restate the requested resource or question in your own words to confirm the target (table schema, view layout, control details, etc.). If the request is ambiguous, ask for specifics before continuing.
2. **Locate via crosswalk** – Use `id_crosswalk.jsonl` to resolve names, IDs, and file paths. Prefer exact matches; for partial matches, list the candidates and request disambiguation.
3. **Fetch canonical source** – Open the identified JSON artifact (`Structure/...`) and extract only the fields required to answer. For page layout or element placement, start with `Structure/docs/{docID}/pages/page-content.ndjson` (fall back to `Structure/docs/{docID}/pages/<pageId>/canvas.html` if needed). When multiple files are involved (e.g., view + table + relation), gather each in turn.
4. **Verify dependencies** – Consult `dependency_index.jsonl`, `relations/edges.jsonl`, and `Structure/docs/{docID}/pages/page-content.ndjson` (for view/control placement) to confirm upstream/downstream links. Highlight any missing dependencies or logged hydration gaps (`Structure/log.txt`).
5. **Compose response** – Provide a concise answer that cites every referenced path (e.g., `Structure/docs/{DocID}/tables/grid-{GridID}/schema.json`). Quote only the necessary JSON keys/values; avoid large dumps unless explicitly requested.
6. **Warn on uncertainty** – If data is absent, stale, or inferred, state the limitation, cite the relevant file (including `Structure/log.txt` for 404s), and suggest next steps.
7. **Offer verifications** – When applicable, recommend follow-up checks (e.g., confirm view filters, validate control default values) using the existing artifacts. Do not assume live Coda access.

Always preserve this order to keep answers predictable, auditable, and low-token.
