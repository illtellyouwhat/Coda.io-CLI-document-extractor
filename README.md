# Coda Export Toolkit

Command-line workflow for mirroring a Coda doc into a deterministic file tree that analysts (and LLM agents) can explore offline. The exporter pulls doc metadata, pages, tables, views, controls, formulas, relations, and a parsed page-content index. It also emits three JSONL “TOC” files that map friendly names to IDs and precompute cross-resource dependencies.

## TLDR
1) Run the export tool
2) Drop LLM/sys into Output dir root.
3) Set Output Dir as root or copy to new folder
3) Tell LLM to read instructions.md
4) Ask away

## Documentation Map

### Human-facing references (`docs/Human/`)
- `quickstart.md` – Installation, token setup, and first run via UV.
- `help.md` – Full CLI flag catalogue with usage notes.
- `TOC_audit.md` – Checklist for regenerating or auditing the JSONL TOC layer.
- `TOC.md` – Explains the purpose of `id_crosswalk.jsonl`, `views_normalized.jsonl`, and `dependency_index.jsonl`.
- `repo summaries/high-level-summary.md` – Architectural overview of modules and workflows.
- `repo summaries/low-level-summary.md` – Module-by-module technical breakdown.


### LLM-facing references (`docs/LLM/`)

These files should be dropped in the output directory root ("Skill" should stay as a folder)

- `sys_files/instructions.md` – Startup flow for the answering agent.
- `sys_files/answer_protocol.md` – Mandatory response sequence and citation rules.
- `sys_files/directory_contract.md` – Authoritative map of directories and artifact semantics.
- `sys_files/skills/` – Skill prompts and reusable analysis templates.
- `ref/` – Supplemental technical references (canvas schema, API atlas) that the agent can load on demand.

## After Running an Export
1. Run the CLI (default output is `Structure/`; see `docs/Human/quickstart.md` for command examples). The run logs to `Structure/log.txt` and writes the TOC JSONLs at the export root.
2. Drop the resulting output directory into your IDE.
3. In your LLM session, have the LLM read:  `docs/LLM/sys_files/instructions.md`, then `answer_protocol.md` and `directory_contract.md`. These files teach the model how to navigate the export safely.
4. Begin asking structural questions (e.g., “Which pages surface the *Bookings* table?”). The LLM will rely on the crosswalk/dependency files to stay grounded.

That’s it—once the export is present and the sys docs are loaded, the environment is ready for interactive analysis. Point the LLM at the Skill folder when asking questions about how to imporve the coda doc.


