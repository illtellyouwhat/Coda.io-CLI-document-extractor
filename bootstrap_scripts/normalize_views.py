"""
Produce normalized view records for views_normalized.jsonl.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

from .utils import relative_path


def build_normalized_views(contexts: Iterable[Dict[str, Any]], repo_root: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []

    for context in contexts:
        doc_id = context["doc_id"]
        tables = context["tables"]
        columns = context["columns"]
        pages = context["pages"]

        for view_id, view_info in context["views"].items():
            view_data = view_info["data"]
            table_detail = view_data.get("tableDetail") or {}
            display_column = table_detail.get("displayColumn") or {}
            display_column_id = display_column.get("id")

            parent = view_data.get("parent") or {}
            parent_id = parent.get("id")
            parent_page = pages.get(parent_id) if parent_id else None

            base_table_id = view_data.get("baseTableId")
            base_table = tables.get(base_table_id) if base_table_id else None

            record: Dict[str, Any] = {
                "docId": doc_id,
                "viewId": view_id,
                "viewName": view_info.get("name"),
                "path": relative_path(view_info["path"], repo_root),
                "browserLink": view_data.get("browserLink"),
                "tableType": view_data.get("tableType"),
                "baseTableId": base_table_id,
                "baseTableName": (base_table or {}).get("name"),
                "displayColumnId": display_column_id,
                "displayColumnName": (columns.get(display_column_id) or {}).get("name"),
                "layout": table_detail.get("layout"),
                "rowCount": table_detail.get("rowCount"),
                "filters": table_detail.get("filters"),
                "groupings": table_detail.get("groupings"),
                "sorts": table_detail.get("sorts"),
                "parentPageId": parent_id,
                "parentPageName": parent.get("name"),
                "parentPagePath": relative_path(parent_page["path"], repo_root) if parent_page else None,
            }

            # Normalize None values for consistent schema
            for key in ("filters", "groupings", "sorts"):
                if key not in record:
                    record[key] = None

            records.append(record)

    records.sort(key=lambda item: (item.get("docId"), item.get("viewName") or "", item.get("viewId")))
    return records

