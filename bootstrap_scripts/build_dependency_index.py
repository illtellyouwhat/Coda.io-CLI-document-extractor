"""
Construct dependency_index.jsonl records.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

from .utils import relative_path


def _page_name(context: Dict[str, Any], page_id: str | None) -> str | None:
    if not page_id:
        return None
    page = context["pages"].get(page_id)
    if not page:
        return None
    return page["data"].get("name")


def _view_name(context: Dict[str, Any], view_id: str | None) -> str | None:
    if not view_id:
        return None
    view = context["views"].get(view_id)
    if not view:
        return None
    return view.get("name")


def _control_name(context: Dict[str, Any], control_id: str | None) -> str | None:
    if not control_id:
        return None
    control = context["controls"].get(control_id)
    if not control:
        return None
    return control.get("name")


def build_dependency_index(contexts: Iterable[Dict[str, Any]], repo_root: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []

    for context in contexts:
        doc_id = context["doc_id"]
        tables = context["tables"]
        columns = context["columns"]
        views = context["views"]
        controls = context["controls"]
        formulas = context["formulas"]
        relations = context["relations"]
        relations_path = context["relations_path"]
        page_content_path = context["page_content_path"]

        # Column formulas
        for table_info in tables.values():
            for column in table_info.get("columns", []):
                col_data = column["data"]
                formula = col_data.get("formula")
                if not formula:
                    continue
                records.append(
                    {
                        "docId": doc_id,
                        "relation": "has_formula",
                        "sourceType": "column",
                        "sourceId": column["id"],
                        "sourceName": column.get("name"),
                        "tableId": column.get("table_id"),
                        "tableName": column.get("table_name"),
                        "ordinal": column.get("ordinal"),
                        "formula": formula,
                        "path": relative_path(column["schema_path"], repo_root),
                    }
                )

        # Lookup relations
        for rel in relations:
            source_table_id = rel.get("fromTableId")
            column_id = rel.get("columnId")
            target_table_id = rel.get("toTableId")
            records.append(
                {
                    "docId": doc_id,
                    "relation": "lookup_to_table",
                    "sourceTableId": source_table_id,
                    "sourceTableName": (tables.get(source_table_id) or {}).get("name"),
                    "columnId": column_id,
                    "columnName": (columns.get(column_id) or {}).get("name") or rel.get("columnName"),
                    "targetTableId": target_table_id,
                    "targetTableName": (tables.get(target_table_id) or {}).get("name"),
                    "isArray": rel.get("isArray"),
                    "formatType": rel.get("formatType"),
                    "path": relative_path(relations_path, repo_root),
                }
            )

        # View-to-table
        for view_id, view_info in views.items():
            view_data = view_info["data"]
            base_table_id = view_data.get("baseTableId")
            if not base_table_id:
                continue
            records.append(
                {
                    "docId": doc_id,
                    "relation": "uses_table",
                    "sourceType": "view",
                    "sourceId": view_id,
                    "sourceName": view_info.get("name"),
                    "targetType": "table",
                    "targetId": base_table_id,
                    "targetName": (tables.get(base_table_id) or {}).get("name"),
                    "path": relative_path(view_info["path"], repo_root),
                }
            )

        # Controls placed on pages (+button edges)
        for control_id, control_info in controls.items():
            control_data = control_info["data"]
            parent = control_data.get("parent") or {}
            parent_id = parent.get("id")
            base_record = {
                "docId": doc_id,
                "relation": "placed_on_page",
                "sourceType": "control",
                "sourceId": control_id,
                "sourceName": control_info.get("name"),
                "controlType": control_data.get("controlType"),
                "targetType": "page",
                "targetId": parent_id,
                "targetName": parent.get("name") or _page_name(context, parent_id),
                "path": relative_path(control_info["path"], repo_root),
            }
            records.append(base_record)
            if control_data.get("controlType") == "button":
                button_record = dict(base_record)
                button_record["relation"] = "button_on_page"
                records.append(button_record)

        # Named formulas defined on pages
        for formula_id, formula_info in formulas.items():
            formula_data = formula_info["data"]
            parent = formula_data.get("parent") or {}
            parent_id = parent.get("id")
            records.append(
                {
                    "docId": doc_id,
                    "relation": "defined_on_page",
                    "sourceType": "formula",
                    "sourceId": formula_id,
                    "sourceName": formula_info.get("name"),
                    "targetType": "page",
                    "targetId": parent_id,
                    "targetName": parent.get("name") or _page_name(context, parent_id),
                    "path": relative_path(formula_info["path"], repo_root),
                }
            )

        # Page layout edges derived from NDJSON
        if context["page_content"]:
            page_content_rel_path = relative_path(page_content_path, repo_root)
            for entry in context["page_content"]:
                page_id = entry.get("pageId")
                element_type = entry.get("elementType")
                ordinal = entry.get("ordinal")
                attributes = entry.get("attributes") or {}

                if element_type == "view":
                    view_id = entry.get("viewId") or entry.get("codaId")
                    table_id = entry.get("tableId") or attributes.get("baseTableId")
                    records.append(
                        {
                            "docId": doc_id,
                            "relation": "view_on_page",
                            "pageId": page_id,
                            "pageName": _page_name(context, page_id),
                            "viewId": view_id,
                            "viewName": _view_name(context, view_id),
                            "baseTableId": table_id,
                            "baseTableName": (tables.get(table_id) or {}).get("name"),
                            "ordinal": ordinal,
                            "pageContentPath": page_content_rel_path,
                            "viewPath": relative_path((views.get(view_id) or {}).get("path", page_content_path), repo_root)
                            if view_id in views
                            else None,
                        }
                    )

                if element_type == "control":
                    control_id = entry.get("controlId") or entry.get("codaId")
                    control_type = attributes.get("controlType")
                    records.append(
                        {
                            "docId": doc_id,
                            "relation": "control_on_page",
                            "pageId": page_id,
                            "pageName": _page_name(context, page_id),
                            "controlId": control_id,
                            "controlName": _control_name(context, control_id) or entry.get("text"),
                            "controlType": control_type,
                            "ordinal": ordinal,
                            "pageContentPath": page_content_rel_path,
                            "controlPath": relative_path((controls.get(control_id) or {}).get("path", page_content_path), repo_root)
                            if control_id in controls
                            else None,
                        }
                    )

    records.sort(
        key=lambda item: (
            item.get("docId"),
            item.get("relation"),
            item.get("pageId") or item.get("sourceId") or "",
            item.get("sourceId") or "",
            item.get("ordinal", -1),
        )
    )
    return records

