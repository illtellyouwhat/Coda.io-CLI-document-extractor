"""Utility helpers for the coda_export package."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Pattern

from dotenv import load_dotenv


LOGGER_NAME = "coda_export"


def setup_logging(log_path: Optional[Path] = None) -> logging.Logger:
    """Configure and return the package logger."""
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_path, encoding="utf-8")
    else:
        handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


@dataclass(frozen=True)
class ExportConfig:
    """Holds runtime configuration for an export run."""

    doc_id: str
    out_dir: Path
    rows_per_table: int = 100
    include_rows: bool = True
    include_formulas: bool = True
    include_controls: bool = True
    export_markdown_also: bool = False
    timeout: float = 30.0
    max_retries: int = 5
    sleep_initial: float = 0.8
    filter_tables: Optional[Pattern[str]] = None
    visible_only: bool = True

    def to_readme_dict(self) -> dict[str, str]:
        """Return a JSON-serializable view of the config for README output."""
        return {
            "doc_id": self.doc_id,
            "out_dir": str(self.out_dir),
            "rows_per_table": str(self.rows_per_table),
            "include_rows": str(self.include_rows).lower(),
            "include_formulas": str(self.include_formulas).lower(),
            "include_controls": str(self.include_controls).lower(),
            "export_markdown_also": str(self.export_markdown_also).lower(),
            "timeout": f"{self.timeout:.1f}s",
            "max_retries": str(self.max_retries),
            "sleep_initial": f"{self.sleep_initial:.2f}s",
            "filter_tables": self.filter_tables.pattern if self.filter_tables else "",
            "visible_only": str(self.visible_only).lower(),
        }


def ensure_within_output(base: Path, target: Path) -> Path:
    """
    Ensure the target path is within the output base directory.

    Raises:
        ValueError if the resolved target is outside the base directory.
    """
    base_resolved = base.resolve()
    target_resolved = target.resolve()
    if not str(target_resolved).startswith(str(base_resolved)):
        raise ValueError(f"Path {target} escapes output directory {base}")
    return target


def load_token(env_var: str = "CODA_API_TOKEN") -> str:
    """
    Load the Coda API token from environment variable or .env file.

    Raises:
        RuntimeError: If the token cannot be found.
    """
    load_dotenv()
    token = os.getenv(env_var)
    if not token:
        raise RuntimeError(
            f"Missing API token. Set {env_var} or add it to a .env file."
        )
    return token


def clamp_rows(rows: int, cap: int = 100) -> int:
    """Clamp the rows per table to the API-specified maximum."""
    return max(0, min(rows, cap))


def compile_filter(pattern: Optional[str]) -> Optional[Pattern[str]]:
    """Compile a regex pattern if provided."""
    if not pattern:
        return None
    try:
        return re.compile(pattern)
    except re.error as exc:
        raise ValueError(f"Invalid table filter regex: {pattern}") from exc


def summarize_counts(counts: dict[str, int]) -> str:
    """Format a human-readable summary string from counts."""
    parts = [f"{key}: {value}" for key, value in counts.items()]
    return ", ".join(parts)
