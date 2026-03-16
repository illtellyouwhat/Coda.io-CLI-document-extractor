"""File writing helpers for the coda_export package."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping


def write_json(path: Path, data: Mapping) -> None:
    """Write JSON data to the given path, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def write_ndjson(path: Path, rows: Iterable[Mapping]) -> None:
    """Write newline-delimited JSON objects."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, separators=(",", ":")))
            fh.write("\n")


def append_ndjson_line(path: Path, record: Mapping) -> None:
    """Append a single JSON object to an NDJSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, separators=(",", ":")))
        fh.write("\n")
