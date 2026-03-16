"""Helpers to derive relation edges between tables and views."""

from __future__ import annotations

from typing import Dict, Iterable, List


def relation_edges_from_schema(schema: dict) -> List[dict]:
    """Extract relation edges from a table schema document."""
    table = schema.get("table", {})
    table_id = table.get("id")
    edges: List[dict] = []
    table_info = schema.get("table") or {}
    from_type = table_info.get("tableType") or table_info.get("type")
    for column in schema.get("columns", []):
        lookup = column.get("lookup")
        if not isinstance(lookup, dict):
            continue
        target = lookup.get("table")
        if isinstance(target, dict):
            target_id = target.get("id")
        elif isinstance(target, str):
            target_id = target
        else:
            target_id = None
        if not (table_id and target_id):
            continue
        edge = {
            "type": "relation",
            "fromTableId": table_id,
            "columnId": column.get("id"),
            "columnName": column.get("name"),
            "toTableId": target_id,
        }
        if from_type:
            edge["fromTableType"] = from_type
        relationship = lookup.get("relationship")
        if relationship:
            edge["relationship"] = relationship
        format_type = lookup.get("formatType")
        if format_type:
            edge["formatType"] = format_type
        is_array = lookup.get("isArray")
        if is_array is not None:
            edge["isArray"] = is_array
        edges.append(edge)
    return edges


def view_edges_from_views(views: Iterable[dict]) -> List[dict]:
    """Build edges describing view-to-base-table mappings."""
    edges: List[dict] = []
    for view in views:
        view_id = view.get("id")
        base_id = view.get("baseTableId")
        if not (view_id and base_id):
            continue
        edge = {
            "type": "viewMapping",
            "viewId": view_id,
            "baseTableId": base_id,
        }
        table_type = view.get("tableType")
        if table_type:
            edge["tableType"] = table_type
        parent = view.get("parent")
        if isinstance(parent, dict):
            parent_id = parent.get("id")
            if parent_id:
                edge["parentPageId"] = parent_id
        edges.append(edge)
    return edges


def build_edge_list(schemas: Dict[str, dict], views: Dict[str, dict]) -> List[dict]:
    """Convenience method to collate all edges."""
    edges: List[dict] = []
    for schema in schemas.values():
        edges.extend(relation_edges_from_schema(schema))
    edges.extend(view_edges_from_views(views.values()))
    return edges
