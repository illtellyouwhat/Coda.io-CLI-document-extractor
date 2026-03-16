"""High-level orchestration for exporting Coda document metadata."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .api import APIError, CodaAPI
from .canvas_parser import parse_canvas_html
from .derive_edges import build_edge_list
from .utils import ExportConfig, clamp_rows
from .writers import write_json, write_ndjson


@dataclass
class ExportCounts:
    """Track counts for reporting."""

    pages: int = 0
    tables: int = 0
    views: int = 0
    columns: int = 0
    rows_sampled: int = 0
    formulas: int = 0
    controls: int = 0
    relation_edges: int = 0
    view_edges: int = 0

    def as_dict(self) -> Dict[str, int]:
        """Expose counts as a dictionary for reporting."""
        return {
            "Pages": self.pages,
            "Tables": self.tables,
            "Views": self.views,
            "Columns": self.columns,
            "Rows sampled": self.rows_sampled,
            "Formulas": self.formulas,
            "Controls": self.controls,
            "Relation edges": self.relation_edges,
            "View mappings": self.view_edges,
        }


class CodaExporter:
    """Orchestrates export of metadata for a Coda document."""

    def __init__(self, api: CodaAPI, config: ExportConfig) -> None:
        self.api = api
        self.config = config
        self.base_dir = config.out_dir / "docs" / config.doc_id
        self.counts = ExportCounts()
        self._schemas: Dict[str, dict] = {}
        self._views: Dict[str, dict] = {}
        self._views_by_page: Dict[str, List[dict]] = defaultdict(list)
        self._page_elements: List[dict] = []

    def run(self) -> ExportCounts:
        """Execute the export sequence."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._write_doc()
        self._write_pages()
        table_list = self._collect_tables()
        self._process_tables(table_list)
        if self.config.include_formulas:
            self._process_formulas()
        if self.config.include_controls:
            self._process_controls()
        self._write_edges()
        self._write_readme()
        self._write_page_index()
        return self.counts

    def _write_doc(self) -> None:
        data = self.api.get(f"/docs/{self.config.doc_id}")
        write_json(self.base_dir / "doc.json", data)

    def _write_pages(self) -> None:
        pages_dir = self.base_dir / "pages"
        for page in self.api.paginate(f"/docs/{self.config.doc_id}/pages"):
            page_id = page.get("id")
            if not page_id:
                continue
            write_json(pages_dir / f"{page_id}.json", page)
            page_dir = pages_dir / page_id
            page_dir.mkdir(parents=True, exist_ok=True)
            html_bytes = self._export_page_canvas(page_id, output_format="html")
            if html_bytes:
                (page_dir / "canvas.html").write_bytes(html_bytes)
                try:
                    refs = self._extract_canvas_refs_html(page_id, html_bytes)
                except Exception as exc:  # pragma: no cover - defensive guard
                    self.api.logger.debug("Canvas parse failed for %s: %s", page_id, exc)
                else:
                    if refs:
                        self._page_elements.extend(refs)
            if getattr(self.config, "export_markdown_also", False):
                md_bytes = self._export_page_canvas(page_id, output_format="markdown")
                if md_bytes:
                    (page_dir / "canvas.md").write_bytes(md_bytes)
            self.counts.pages += 1

    def _collect_tables(self) -> List[dict]:
        tables = []
        for table in self.api.paginate(f"/docs/{self.config.doc_id}/tables"):
            if self.config.filter_tables:
                if not self.config.filter_tables.search(table.get("name", "")):
                    continue
            tables.append(table)
        return tables

    def _process_tables(self, tables: Iterable[dict]) -> None:
        tables_dir = self.base_dir / "tables"
        views_dir = self.base_dir / "views"
        rows_cap = clamp_rows(self.config.rows_per_table)
        for table in tables:
            table_id = table.get("id")
            if not table_id:
                continue
            table_type = (table.get("type") or "").lower()
            table_variant = (table.get("tableType") or "").lower()
            is_view = table.get("isView") is True or table_type == "view" or (
                table_variant and table_variant != "table"
            )
            schema = self._fetch_schema(table_id, table, is_view=is_view)
            write_json(tables_dir / table_id / "schema.json", schema)
            self._schemas[table_id] = schema
            column_count = len(schema.get("columns", []))
            self.counts.columns += column_count
            if is_view:
                base_table = table.get("table")
                if isinstance(base_table, dict):
                    base_table_id = base_table.get("id")
                else:
                    base_table_id = base_table
                view_record = {
                    "id": table_id,
                    "type": "view",
                    "tableType": table.get("tableType"),
                    "name": table.get("name"),
                    "baseTableId": base_table_id,
                    "browserLink": table.get("browserLink"),
                    "parent": table.get("parent"),
                }
                table_detail = self._fetch_detail(
                    f"/docs/{self.config.doc_id}/tables/{table_id}",
                    entity="view detail",
                    entity_id=table_id,
                )
                if table_detail:
                    view_record["tableDetail"] = table_detail
                    if not base_table_id:
                        parent_table = table_detail.get("parentTable")
                        if isinstance(parent_table, dict):
                            base_table_id = parent_table.get("id")
                            if base_table_id:
                                view_record["baseTableId"] = base_table_id
                write_json(views_dir / table_id / "view.json", view_record)
                self._views[table_id] = view_record
                parent_page = view_record.get("parent")
                if isinstance(parent_page, dict):
                    parent_id = parent_page.get("id")
                    if parent_id:
                        self._views_by_page[parent_id].append(view_record)
                self.counts.views += 1
            else:
                self.counts.tables += 1
                if self.config.include_rows and rows_cap > 0:
                    samples, sampled_count = self._fetch_rows(table_id, rows_cap)
                    write_ndjson(
                        tables_dir / table_id / "sample-rows.ndjson",
                        samples,
                    )
                    self.counts.rows_sampled += sampled_count

    def _fetch_schema(self, table_id: str, table: dict, *, is_view: bool = False) -> dict:
        columns = list(
            self.api.paginate(
                f"/docs/{self.config.doc_id}/tables/{table_id}/columns",
                params=self._column_params(),
            )
        )
        formatted_columns = [self._format_column(column) for column in columns]
        if is_view:
            base_table_field = table.get("table")
            if isinstance(base_table_field, dict):
                base_table_id = base_table_field.get("id")
            else:
                base_table_id = base_table_field
            if base_table_id:
                for column in formatted_columns:
                    if "lookup" in column and isinstance(column["lookup"], dict):
                        lookup_table = column["lookup"].get("table")
                        if isinstance(lookup_table, dict) and not lookup_table.get("id"):
                            lookup_table["id"] = base_table_id
        return {
            "table": {
                "id": table_id,
                "name": table.get("name"),
                "type": table.get("type"),
                "tableType": table.get("tableType"),
            },
            "columns": formatted_columns,
            "browserLink": table.get("browserLink"),
        }

    def _column_params(self) -> Dict[str, str]:
        params: Dict[str, str] = {}
        if self.config.visible_only:
            params["visibleOnly"] = "true"
        return params

    def _format_column(self, column: dict) -> dict:
        data = {
            "id": column.get("id"),
            "name": column.get("name"),
            "type": column.get("type"),
        }
        column_type = column.get("columnType")
        if column_type:
            data["columnType"] = column_type
        formula = column.get("formula")
        if formula:
            data["formula"] = formula
        calculated = column.get("calculated")
        if calculated is not None:
            data["calculated"] = calculated
        lookup = self._extract_lookup(column)
        if lookup:
            data["lookup"] = lookup
        format_props = {}
        for key in ("format", "display", "description"):
            value = column.get(key)
            if value is not None:
                format_props[key] = value
        if format_props:
            data["meta"] = format_props
        return data

    def _extract_lookup(self, column: dict) -> Optional[dict]:
        """Normalize lookup metadata regardless of where the API surfaces it."""
        primary = self._normalize_lookup_dict(column.get("lookup"))
        if primary:
            return primary

        fmt = column.get("format")
        normalized = self._lookup_from_format(fmt)
        if normalized:
            return normalized

        display = column.get("display")
        if isinstance(display, dict):
            normalized = self._lookup_from_format(display.get("format"))
            if normalized:
                return normalized
        meta = column.get("meta")
        if isinstance(meta, dict):
            normalized = self._lookup_from_format(meta.get("format"))
            if normalized:
                return normalized

        return None

    def _lookup_from_format(self, fmt: Optional[dict]) -> Optional[dict]:
        if not isinstance(fmt, dict):
            return None
        fmt_type = fmt.get("type")
        if fmt_type not in {"lookup", "relation"}:
            return None
        table_ref = self._normalize_table_ref(fmt.get("table"))
        normalized: Dict[str, Any] = {}
        if table_ref:
            normalized["table"] = table_ref
        for key in ("relationship", "isArray", "valueType", "displayColumn", "relationshipSide"):
            if fmt.get(key) is not None:
                normalized[key] = fmt.get(key)
        normalized["formatType"] = fmt_type
        return normalized if normalized.get("table") else None

    def _normalize_lookup_dict(self, lookup: Optional[dict]) -> Optional[dict]:
        if not isinstance(lookup, dict):
            return None
        normalized: Dict[str, Any] = {}
        for key, value in lookup.items():
            if key == "table":
                table_ref = self._normalize_table_ref(value)
                if table_ref:
                    normalized["table"] = table_ref
            elif value is not None:
                normalized[key] = value
        return normalized if normalized.get("table") else None

    def _normalize_table_ref(self, table: Optional[dict | str]) -> Optional[dict]:
        if isinstance(table, str):
            return {"id": table}
        if not isinstance(table, dict):
            return None
        keys = ("id", "name", "type", "tableType", "href", "browserLink")
        ref = {key: table.get(key) for key in keys if table.get(key) is not None}
        return ref if ref.get("id") else None

    def _fetch_rows(self, table_id: str, limit: int) -> Tuple[List[dict], int]:
        remaining = limit
        rows: List[dict] = []
        params: Dict[str, str] = {"valueFormat": "rich"}
        next_token: Optional[str] = None
        sampled = 0
        while remaining > 0:
            params["limit"] = str(min(remaining, 100))
            if next_token:
                params["pageToken"] = next_token
            response = self.api.get(
                f"/docs/{self.config.doc_id}/tables/{table_id}/rows",
                params=params,
            )
            items = response.get("items", [])
            for row in items:
                rows.append(self._format_row(row))
            sampled += len(items)
            remaining -= len(items)
            next_token = response.get("nextPageToken")
            if not next_token or remaining <= 0:
                break
        params.pop("pageToken", None)
        return rows[:limit], min(sampled, limit)

    def _format_row(self, row: dict) -> dict:
        cells = row.get("valuesByColumnId") or row.get("values") or {}
        return {
            "id": row.get("id"),
            "cells": cells,
            "href": row.get("browserLink"),
        }

    def _process_formulas(self) -> None:
        formulas_dir = self.base_dir / "formulas"
        for formula in self.api.paginate(f"/docs/{self.config.doc_id}/formulas"):
            formula_id = formula.get("id")
            if not formula_id:
                continue
            detail = self._fetch_detail(
                f"/docs/{self.config.doc_id}/formulas/{formula_id}",
                entity="formula",
                entity_id=formula_id,
            )
            enriched = dict(formula)
            if detail:
                enriched.update(detail)
            write_json(formulas_dir / f"{formula_id}.json", enriched)
            self.counts.formulas += 1

    def _process_controls(self) -> None:
        controls_dir = self.base_dir / "controls"
        for control in self.api.paginate(f"/docs/{self.config.doc_id}/controls"):
            control_id = control.get("id")
            if not control_id:
                continue
            detail = self._fetch_detail(
                f"/docs/{self.config.doc_id}/controls/{control_id}",
                entity="control",
                entity_id=control_id,
            )
            enriched = dict(control)
            if detail:
                enriched.update(detail)
            write_json(controls_dir / f"{control_id}.json", enriched)
            self.counts.controls += 1
            parent_ref = (detail or {}).get("parent") or control.get("parent")
            page_id = self._extract_ref_id(parent_ref)
            if page_id:
                record: Dict[str, Any] = {
                    "pageId": page_id,
                    "elementType": "control",
                    "controlId": control_id,
                }
                control_name = enriched.get("name")
                if control_name:
                    record["text"] = control_name
                attributes: Dict[str, Any] = {}
                control_type = enriched.get("controlType")
                if control_type:
                    attributes["controlType"] = control_type
                value = enriched.get("value")
                if value is not None:
                    attributes["value"] = value
                if attributes:
                    record["attributes"] = attributes
                self._page_elements.append(record)

    def _write_edges(self) -> None:
        relations_dir = self.base_dir / "relations"
        edges = build_edge_list(self._schemas, self._views)
        filepath = relations_dir / "edges.jsonl"
        relation_count = sum(1 for edge in edges if edge.get("type") == "relation")
        view_count = sum(1 for edge in edges if edge.get("type") == "viewMapping")
        if edges:
            write_ndjson(filepath, edges)
        else:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text("", encoding="utf-8")
        self.counts.relation_edges += relation_count
        self.counts.view_edges += view_count

    def _write_readme(self) -> None:
        readme_path = self.config.out_dir / "README.md"
        lines = [
            f"# Coda Export for {self.config.doc_id}",
            "",
            "## Run Configuration",
        ]
        for key, value in self.config.to_readme_dict().items():
            lines.append(f"- **{key}**: {value}")
        lines.extend(
            [
                "",
                "## Artifact Counts",
            ]
        )
        for label, count in self.counts.as_dict().items():
            lines.append(f"- **{label}**: {count}")
        lines.append("")
        lines.append(
            f"Output directory: `{self.base_dir}`"
        )
        readme_path.write_text("\n".join(lines), encoding="utf-8")

    def _write_page_index(self) -> None:
        if not self._page_elements:
            return
        index_path = self.base_dir / "pages" / "page-content.ndjson"
        enriched = [self._augment_page_element(record) for record in self._page_elements]
        write_ndjson(index_path, enriched)

    def _extract_canvas_refs(self, page_id: str, node: Any, path: Optional[List[str]] = None) -> List[dict]:
        """Walk canvas JSON and extract references to tables, views, controls, etc."""
        results: List[dict] = []
        current_path = list(path or [])
        if isinstance(node, dict):
            node_type = node.get("type")
            if node_type:
                current_path.append(str(node_type))
            entry_base = {
                "pageId": page_id,
            }
            if node_type:
                entry_base["elementType"] = node_type
            ref_data: Dict[str, str] = {}
            for key in ("tableId", "viewId", "controlId", "formulaId", "canvasId", "sectionId", "buttonId"):
                value = node.get(key)
                if isinstance(value, str):
                    ref_data[key] = value
            for ref_key in ("table", "view", "control"):
                ref_obj = node.get(ref_key)
                if isinstance(ref_obj, dict):
                    ref_id = ref_obj.get("id")
                    if isinstance(ref_id, str):
                        mapped_key = f"{ref_key}Id"
                        ref_data.setdefault(mapped_key, ref_id)
            base_table_id = node.get("baseTableId")
            if isinstance(base_table_id, str):
                ref_data["baseTableId"] = base_table_id
            if ref_data:
                entry = dict(entry_base)
                entry.update(ref_data)
                name = node.get("name") or node.get("title") or node.get("label") or node.get("caption")
                if name:
                    entry["name"] = name
                if current_path:
                    entry["path"] = "/".join(current_path)
                results.append(entry)
            for child_key in ("children", "items", "contents", "rows", "cells", "columns", "sections", "blocks"):
                child_value = node.get(child_key)
                if child_value:
                    results.extend(self._extract_canvas_refs(page_id, child_value, current_path))
        elif isinstance(node, list):
            for item in node:
                results.extend(self._extract_canvas_refs(page_id, item, path))
        return results

    def _extract_canvas_refs_html(self, page_id: str, html_bytes: bytes) -> List[dict]:
        """Parse exported canvas HTML into normalized element records."""
        return parse_canvas_html(page_id, html_bytes)

    def _augment_page_element(self, element: dict) -> dict:
        """Enrich raw page element data with metadata gleaned from other exports."""
        record = dict(element)
        attributes = record.get("attributes")
        if isinstance(attributes, dict):
            record["attributes"] = dict(attributes)
        element_type = record.get("elementType")
        if element_type == "view":
            table_id = record.get("tableId") or record.get("codaId")
            page_id = record.get("pageId")
            if page_id and table_id:
                view = self._find_view_for_page(page_id, table_id)
                if view:
                    record["viewId"] = view.get("id")
                    view_name = view.get("name")
                    if view_name and not record.get("text"):
                        record["text"] = view_name
                    base_table_id = view.get("baseTableId")
                    if not base_table_id:
                        parent_table = view.get("tableDetail", {}).get("parentTable", {})
                        if isinstance(parent_table, dict):
                            base_table_id = parent_table.get("id")
                    if base_table_id:
                        attrs = record.setdefault("attributes", {})
                        attrs.setdefault("baseTableId", base_table_id)
        return record

    def _find_view_for_page(self, page_id: str, base_table_id: str) -> Optional[dict]:
        """Return the first view on a page matching the supplied base table id."""
        for view in self._views_by_page.get(page_id, []):
            candidate_base = view.get("baseTableId")
            if not candidate_base:
                parent_table = view.get("tableDetail", {}).get("parentTable", {})
                if isinstance(parent_table, dict):
                    candidate_base = parent_table.get("id")
            if candidate_base == base_table_id:
                return view
        return None

    @staticmethod
    def _extract_ref_id(ref: Any) -> Optional[str]:
        if isinstance(ref, str):
            return ref
        if isinstance(ref, dict):
            value = ref.get("id")
            if isinstance(value, str):
                return value
        return None

    def _fetch_detail(
        self,
        path: str,
        *,
        entity: str,
        entity_id: str,
        params: Optional[Dict[str, str]] = None,
    ) -> Optional[dict]:
        """Fetch additional metadata for an entity, logging and continuing on failure."""
        try:
            return self.api.get(path, params=params)
        except APIError as exc:
            self.api.logger.warning(
                "Failed to hydrate %s %s (%s): %s",
                entity,
                entity_id,
                path,
                exc,
            )
        return None

    def _export_page_canvas(
        self,
        page_id: str,
        output_format: str = "html",
        timeout_s: int = 180,
        poll_interval_s: float = 2.0,
    ) -> Optional[bytes]:
        """Export page canvas content via documented export endpoints."""
        doc_id = self.config.doc_id
        export_path = f"/docs/{doc_id}/pages/{page_id}/export"
        poll_path = f"/docs/{doc_id}/pages/{page_id}/export/{{export_id}}"
        try:
            start, http_response = self.api.request_with_response(
                "POST",
                export_path,
                json={"outputFormat": output_format},
            )
        except APIError as exc:
            self.api.logger.warning(
                "Failed to start %s export for page %s: %s",
                output_format,
                page_id,
                exc,
            )
            return None
        status_code = http_response.status_code
        header_subset = {
            key: value
            for key, value in http_response.headers.items()
            if key.lower()
            in {
                "x-coda-requestid",
                "x-request-id",
                "x-trace-id",
                "content-type",
                "date",
            }
        }
        export_id = (start or {}).get("requestId") or (start or {}).get("id")
        if not export_id:
            href = (start or {}).get("href")
            if isinstance(href, str):
                export_id = href.rsplit("/", 1)[-1]
        if not export_id:
            self.api.logger.warning(
                "No export id returned for page %s %s export (status=%s headers=%s body=%s)",
                page_id,
                output_format,
                status_code,
                header_subset or dict(http_response.headers),
                start,
            )
            return None
        self.api.logger.debug(
            "Started page export for page %s (%s) exportId=%s status=%s headers=%s",
            page_id,
            output_format,
            export_id,
            status_code,
            header_subset or dict(http_response.headers),
        )
        time.sleep(max(0.5, poll_interval_s / 2))

        deadline = time.time() + timeout_s
        while time.time() < deadline:
            try:
                status = self.api.request(
                    "GET",
                    poll_path.format(export_id=export_id),
                )
            except APIError as exc:
                self.api.logger.warning(
                    "Failed to poll export %s for page %s: %s",
                    export_id,
                    page_id,
                    exc,
                )
                time.sleep(poll_interval_s)
                continue
            state = (status or {}).get("status")
            if state == "complete":
                download_link = status.get("downloadLink")
                if not download_link:
                    self.api.logger.warning(
                        "Export complete but missing download link for page %s (export %s)",
                        page_id,
                        export_id,
                    )
                    return None
                try:
                    return self.api.download(download_link)
                except APIError as exc:
                    self.api.logger.warning(
                        "Failed to download canvas for page %s from %s: %s",
                        page_id,
                        download_link,
                        exc,
                    )
                    return None
            if state in {"failed", "error"}:
                self.api.logger.warning(
                    "Export reported %s for page %s (export %s): %s",
                    state,
                    page_id,
                    export_id,
                    status,
                )
                return None
            time.sleep(poll_interval_s)

        self.api.logger.warning(
            "Timed out waiting for %s export of page %s (export %s)",
            output_format,
            page_id,
            export_id,
        )
        return None
