"""
Generate id_crosswalk.jsonl records from a loaded export.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

from .utils import relative_path


def _authors_list(page_data: Dict[str, Any]) -> List[str]:
    names: List[str] = []
    for author in page_data.get("authors", []):
        if isinstance(author, dict) and author.get("name"):
            names.append(author["name"])
    return names


def build_crosswalk(contexts: Iterable[Dict[str, Any]], repo_root: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []

    for context in contexts:
        doc_id = context["doc_id"]
        doc_data = context["doc"]
        doc_path = context["doc_path"]

        doc_record: Dict[str, Any] = {
            "docId": doc_id,
            "resource": "doc",
            "id": doc_data.get("id", doc_id),
            "name": doc_data.get("name"),
            "path": relative_path(doc_path, repo_root),
            "browserLink": doc_data.get("browserLink"),
            "workspaceId": doc_data.get("workspaceId"),
            "workspaceName": (doc_data.get("workspace") or {}).get("name"),
            "owner": doc_data.get("owner"),
            "ownerName": doc_data.get("ownerName"),
            "createdAt": doc_data.get("createdAt"),
            "updatedAt": doc_data.get("updatedAt"),
            "sourceDocId": (doc_data.get("sourceDoc") or {}).get("id"),
        }
        records.append(doc_record)

        # Pages
        for page_id, page_info in context["pages"].items():
            data = page_info["data"]
            parent = data.get("parent") or {}
            page_record: Dict[str, Any] = {
                "docId": doc_id,
                "resource": "page",
                "id": page_id,
                "name": data.get("name"),
                "path": relative_path(page_info["path"], repo_root),
                "browserLink": data.get("browserLink"),
                "parentId": parent.get("id"),
                "parentName": parent.get("name"),
                "isHidden": data.get("isHidden"),
                "isEffectivelyHidden": data.get("isEffectivelyHidden"),
                "createdAt": data.get("createdAt"),
                "updatedAt": data.get("updatedAt"),
            }
            authors = _authors_list(data)
            if authors:
                page_record["authors"] = authors
            subtitle = data.get("subtitle")
            if subtitle:
                page_record["subtitle"] = subtitle
            records.append(page_record)

        # Tables and columns
        for table_id, table_info in context["tables"].items():
            schema = table_info["data"]
            table_meta = schema.get("table") or {}
            table_record: Dict[str, Any] = {
                "docId": doc_id,
                "resource": "table",
                "id": table_id,
                "name": table_info.get("name"),
                "path": relative_path(table_info["schema_path"], repo_root),
                "tableType": table_meta.get("tableType"),
                "browserLink": table_meta.get("browserLink"),
                "columnCount": len(table_info.get("columns", [])),
            }
            records.append(table_record)

            for column in table_info.get("columns", []):
                col_data = column["data"]
                format_meta = (col_data.get("meta") or {}).get("format") or {}
                column_record: Dict[str, Any] = {
                    "docId": doc_id,
                    "resource": "column",
                    "id": column["id"],
                    "name": column.get("name"),
                    "tableId": column.get("table_id"),
                    "tableName": column.get("table_name"),
                    "path": relative_path(column["schema_path"], repo_root),
                    "ordinal": column.get("ordinal"),
                    "columnType": col_data.get("type"),
                    "valueType": col_data.get("valueType"),
                    "formatType": format_meta.get("type"),
                    "formatIsArray": format_meta.get("isArray"),
                    "isDisplay": (col_data.get("meta") or {}).get("display"),
                    "aggregation": (col_data.get("meta") or {}).get("aggregation"),
                    "formula": col_data.get("formula"),
                }
                records.append(column_record)

        # Views
        for view_id, view_info in context["views"].items():
            view_data = view_info["data"]
            parent = view_data.get("parent") or {}
            table_detail = view_data.get("tableDetail") or {}
            display_column = table_detail.get("displayColumn") or {}
            base_table_id = view_data.get("baseTableId")

            view_record: Dict[str, Any] = {
                "docId": doc_id,
                "resource": "view",
                "id": view_id,
                "name": view_info.get("name"),
                "path": relative_path(view_info["path"], repo_root),
                "browserLink": view_data.get("browserLink"),
                "parentPageId": parent.get("id"),
                "parentPageName": parent.get("name"),
                "baseTableId": base_table_id,
                "baseTableName": (context["tables"].get(base_table_id) or {}).get("name"),
                "displayColumnId": display_column.get("id"),
                "displayColumnName": (context["columns"].get(display_column.get("id")) or {}).get("name"),
                "layout": table_detail.get("layout"),
                "tableType": view_data.get("tableType"),
            }
            records.append(view_record)

        # Controls
        for control_id, control_info in context["controls"].items():
            control_data = control_info["data"]
            parent = control_data.get("parent") or {}
            control_record: Dict[str, Any] = {
                "docId": doc_id,
                "resource": "control",
                "id": control_id,
                "name": control_info.get("name"),
                "path": relative_path(control_info["path"], repo_root),
                "controlType": control_data.get("controlType"),
                "parentPageId": parent.get("id"),
                "parentPageName": parent.get("name"),
                "value": control_data.get("value"),
            }
            records.append(control_record)

        # Named formulas
        for formula_id, formula_info in context["formulas"].items():
            formula_data = formula_info["data"]
            parent = formula_data.get("parent") or {}
            formula_record: Dict[str, Any] = {
                "docId": doc_id,
                "resource": "formula",
                "id": formula_id,
                "name": formula_info.get("name"),
                "path": relative_path(formula_info["path"], repo_root),
                "parentPageId": parent.get("id"),
                "parentPageName": parent.get("name"),
                "value": formula_data.get("value"),
            }
            records.append(formula_record)

    records.sort(
        key=lambda item: (
            item.get("docId"),
            item.get("resource"),
            item.get("tableId"),
            item.get("id"),
            item.get("ordinal", -1),
        )
    )
    return records

