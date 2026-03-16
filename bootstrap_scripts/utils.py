"""
Shared helpers for the bootstrap scripts.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Iterable, List, Optional


def read_json(path: Path) -> Any:
    """Load a JSON document from disk."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_ndjson(path: Path) -> List[Any]:
    """Load newline-delimited JSON; gracefully skip malformed rows."""
    rows: List[Any] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            text = raw.strip()
            if not text:
                continue
            try:
                rows.append(json.loads(text))
            except json.JSONDecodeError as exc:
                logging.warning("Skipping invalid JSON (%s line %s): %s", path, line_no, exc)
    return rows


def relative_path(path: Path, base: Path) -> str:
    """Return a POSIX-style path relative to base when possible."""
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def ensure_directory(path: Path) -> None:
    """Create parent directories for a file output."""
    path.parent.mkdir(parents=True, exist_ok=True)


def write_jsonl(records: Iterable[Any], path: Path) -> int:
    """Write records to newline-delimited JSON. Returns the count written."""
    ensure_directory(path)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True))
            handle.write("\n")
            count += 1
    return count


def list_subdirs(path: Path) -> List[Path]:
    """Return sorted immediate subdirectories."""
    if not path.exists():
        return []
    return sorted(p for p in path.iterdir() if p.is_dir())

