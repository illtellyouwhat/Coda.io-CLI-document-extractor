"""
Load a Coda export snapshot into convenient Python structures.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

from .utils import list_subdirs, read_json, read_ndjson


def collect_export(export_root: Path) -> List[Dict[str, Any]]:
    """
    Load all docs contained in the export root.

    Each element in the returned list contains these keys:
      - doc_id: str
      - doc: dict (may be empty if doc.json missing)
      - doc_path: Path
      - pages: dict[page_id] -> {"data": dict, "path": Path}
      - tables: dict[table_id] -> {"data": dict, "columns": List[dict], "schema_path": Path, "name": str}
      - columns: dict[column_id] -> column metadata dict with table references
      - views: dict[view_id] -> {"data": dict, "path": Path, "name": str}
      - controls: dict[control_id] -> {"data": dict, "path": Path, "name": str}
      - formulas: dict[formula_id] -> {"data": dict, "path": Path, "name": str}
      - relations: List[dict]
      - relations_path: Path
      - page_content: List[dict]
      - page_content_path: Path
      - page_elements_by_page: dict[page_id] -> List[dict]
    """
    export_root = export_root.resolve()
    docs_dir = export_root / "docs"
    if not docs_dir.is_dir():
        raise FileNotFoundError(f"Expected 'docs' directory inside {export_root}")

    contexts: List[Dict[str, Any]] = []

    for doc_dir in list_subdirs(docs_dir):
        doc_id = doc_dir.name
        logging.info("Collecting doc %s", doc_id)
        context: Dict[str, Any] = {
            "doc_id": doc_id,
            "root": export_root,
            "doc": {},
            "doc_path": doc_dir / "doc.json",
            "pages": {},
            "tables": {},
            "columns": {},
            "views": {},
            "controls": {},
            "formulas": {},
            "relations": [],
            "relations_path": doc_dir / "relations" / "edges.jsonl",
            "page_content": [],
            "page_content_path": doc_dir / "pages" / "page-content.ndjson",
            "page_elements_by_page": {},
        }

        if context["doc_path"].exists():
            context["doc"] = read_json(context["doc_path"])
        else:
            logging.warning("Missing doc.json for doc %s", doc_id)

        # Pages
        pages_dir = doc_dir / "pages"
        if pages_dir.is_dir():
            for page_json in sorted(pages_dir.glob("*.json")):
                page_data = read_json(page_json)
                page_id = page_data.get("id") or page_json.stem
                context["pages"][page_id] = {"data": page_data, "path": page_json}

        # Tables and columns
        tables_dir = doc_dir / "tables"
        if tables_dir.is_dir():
            for table_dir in list_subdirs(tables_dir):
                schema_path = table_dir / "schema.json"
                if not schema_path.exists():
                    logging.warning("Skipping table %s (missing schema.json)", table_dir.name)
                    continue
                schema = read_json(schema_path)
                table_meta = schema.get("table", {})
                table_id = table_meta.get("id") or table_dir.name
                table_name = table_meta.get("name") or table_dir.name

                column_entries: List[Dict[str, Any]] = []
                for ordinal, column in enumerate(schema.get("columns", [])):
                    column_id = column.get("id") or f"{table_id}__{ordinal}"
                    column_name = column.get("name") or ""
                    column_info = {
                        "id": column_id,
                        "name": column_name,
                        "data": column,
                        "ordinal": ordinal,
                        "table_id": table_id,
                        "table_name": table_name,
                        "schema_path": schema_path,
                    }
                    column_entries.append(column_info)
                    context["columns"][column_id] = column_info

                context["tables"][table_id] = {
                    "id": table_id,
                    "name": table_name,
                    "data": schema,
                    "columns": column_entries,
                    "schema_path": schema_path,
                }

        # Views
        views_dir = doc_dir / "views"
        if views_dir.is_dir():
            for view_dir in list_subdirs(views_dir):
                view_path = view_dir / "view.json"
                if not view_path.exists():
                    logging.warning("Skipping view %s (missing view.json)", view_dir.name)
                    continue
                view_data = read_json(view_path)
                view_id = view_data.get("id") or view_dir.name
                context["views"][view_id] = {
                    "id": view_id,
                    "name": view_data.get("name"),
                    "data": view_data,
                    "path": view_path,
                }

        # Controls
        controls_dir = doc_dir / "controls"
        if controls_dir.is_dir():
            for control_path in sorted(controls_dir.glob("*.json")):
                if not control_path.is_file():
                    continue
                control_data = read_json(control_path)
                control_id = control_data.get("id") or control_path.stem
                context["controls"][control_id] = {
                    "id": control_id,
                    "name": control_data.get("name"),
                    "data": control_data,
                    "path": control_path,
                }

        # Formulas
        formulas_dir = doc_dir / "formulas"
        if formulas_dir.is_dir():
            for formula_path in sorted(formulas_dir.glob("*.json")):
                if not formula_path.is_file():
                    continue
                formula_data = read_json(formula_path)
                formula_id = formula_data.get("id") or formula_path.stem
                context["formulas"][formula_id] = {
                    "id": formula_id,
                    "name": formula_data.get("name"),
                    "data": formula_data,
                    "path": formula_path,
                }

        # Relations
        if context["relations_path"].exists():
            context["relations"] = read_ndjson(context["relations_path"])

        # Page content
        if context["page_content_path"].exists():
            page_content = read_ndjson(context["page_content_path"])
            context["page_content"] = page_content
            by_page: Dict[str, List[Dict[str, Any]]] = {}
            for entry in page_content:
                page_id = entry.get("pageId")
                if not page_id:
                    continue
                by_page.setdefault(page_id, []).append(entry)
            for elements in by_page.values():
                elements.sort(key=lambda item: item.get("ordinal", 0))
            context["page_elements_by_page"] = by_page

        contexts.append(context)

        logging.info(
            "  %s pages, %s tables, %s views, %s controls, %s formulas",
            len(context["pages"]),
            len(context["tables"]),
            len(context["views"]),
            len(context["controls"]),
            len(context["formulas"]),
        )

    return contexts

