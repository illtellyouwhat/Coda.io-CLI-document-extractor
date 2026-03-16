"""Helpers to normalize Coda canvas HTML exports."""

from __future__ import annotations

import html
import json
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from bs4 import Tag  # type: ignore


def parse_canvas_html(page_id: str, html_bytes: bytes) -> List[dict]:
    """
    Convert a canvas HTML export into normalized element records.

    The resulting dictionaries are designed to feed `pages/page-content.ndjson`
    so downstream consumers can traverse a structured view of each canvas.
    """
    try:
        from bs4 import BeautifulSoup  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError(
            "BeautifulSoup is required to parse canvas HTML. "
            "Install beautifulsoup4 to enable canvas parsing."
        ) from exc

    soup = BeautifulSoup(html_bytes, "html.parser")
    records: List[dict] = []
    ordinal = 0

    def add_record(payload: Optional[Dict]) -> None:
        nonlocal ordinal
        if not payload:
            return
        record = {"pageId": page_id, "ordinal": ordinal}
        record.update(payload)
        records.append(record)
        ordinal += 1

    for table in soup.find_all("table"):
        add_record(_parse_table(table))

    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        add_record(_parse_heading(heading))

    for img in soup.find_all("img"):
        add_record(_parse_image(img))

    for iframe in soup.find_all("iframe"):
        add_record(_parse_embed(iframe))

    # Collect prominent links outside of tables (avoid noisy inline anchors)
    for anchor in soup.find_all("a"):
        if _is_inline_anchor(anchor):
            continue
        add_record(_parse_link(anchor))

    return records


def _parse_table(tag: "Tag") -> Optional[dict]:
    grid_id = tag.get("data-coda-grid-id")
    if not grid_id:
        return None

    attributes: Dict[str, object] = {}
    display_col = tag.get("data-coda-display-column-id")
    if display_col:
        attributes["displayColumnId"] = display_col

    sorts_raw = tag.get("data-coda-sorts")
    if sorts_raw:
        attributes["sorts"] = _maybe_json(sorts_raw)

    view_cfg: Dict[str, object] = {}
    for attr, value in tag.attrs.items():
        if attr.startswith("data-coda-view-config-"):
            key = attr.replace("data-coda-view-config-", "")
            view_cfg[key] = _maybe_json(value)
    if view_cfg:
        attributes["viewConfig"] = view_cfg

    caption = tag.find("caption")
    heading_text = _clean_text(caption.get_text(" ", strip=True)) if caption else None

    record: Dict[str, object] = {
        "elementType": "view",
        "tableId": grid_id,
        "codaId": grid_id,
    }
    if heading_text:
        record["text"] = heading_text
    if attributes:
        record["attributes"] = attributes
    return record


def _parse_heading(tag: "Tag") -> Optional[dict]:
    text = _clean_text(tag.get_text(" ", strip=True))
    if not text:
        return None
    level = int(tag.name[1])
    return {
        "elementType": "heading",
        "text": text,
        "attributes": {"level": level},
    }


def _parse_image(tag: "Tag") -> Optional[dict]:
    src = tag.get("src")
    if not src:
        return None
    attributes = {"src": src}
    alt = _clean_text(tag.get("alt"))
    if alt:
        attributes["alt"] = alt
    return {
        "elementType": "image",
        "attributes": attributes,
    }


def _parse_embed(tag: "Tag") -> Optional[dict]:
    src = tag.get("src")
    if not src:
        return None
    attributes = {"src": src}
    title = _clean_text(tag.get("title"))
    if title:
        attributes["title"] = title
    return {
        "elementType": "embed",
        "attributes": attributes,
    }


def _parse_link(tag: "Tag") -> Optional[dict]:
    href = tag.get("href")
    if not href:
        return None
    text = _clean_text(tag.get_text(" ", strip=True))
    attributes = {"href": href}
    rel = tag.get("rel")
    if rel:
        attributes["rel"] = rel
    if tag.get("target"):
        attributes["target"] = tag["target"]
    record: Dict[str, object] = {
        "elementType": "link",
        "attributes": attributes,
    }
    if text:
        record["text"] = text
    return record


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def _maybe_json(raw: str) -> object:
    unescaped = html.unescape(raw)
    try:
        return json.loads(unescaped)
    except json.JSONDecodeError:
        return unescaped


def _is_inline_anchor(tag: "Tag") -> bool:
    """Return True if an anchor is part of a table or header, to avoid duplication."""
    parent = tag.parent
    while parent:
        if parent.name in {"table", "thead", "tbody", "tr"}:
            return True
        parent = parent.parent
    return False
