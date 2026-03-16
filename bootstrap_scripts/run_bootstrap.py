"""
CLI entry point to regenerate id_crosswalk.jsonl, views_normalized.jsonl,
and dependency_index.jsonl from a Coda export.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

if __package__ in (None, ""):
    # Allow running the script directly: python bootstrap_scripts/run_bootstrap.py
    package_root = Path(__file__).resolve().parent.parent
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    from bootstrap_scripts.build_crosswalk import build_crosswalk
    from bootstrap_scripts.build_dependency_index import build_dependency_index
    from bootstrap_scripts.export_loader import collect_export
    from bootstrap_scripts.normalize_views import build_normalized_views
    from bootstrap_scripts.utils import write_jsonl
else:
    from .build_crosswalk import build_crosswalk
    from .build_dependency_index import build_dependency_index
    from .export_loader import collect_export
    from .normalize_views import build_normalized_views
    from .utils import write_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate glue-layer JSONL artifacts for a Coda export.")
    parser.add_argument(
        "--export-root",
        type=Path,
        required=False,
        default=None,
        help="Path to the export root (expects a 'docs/' directory underneath). Defaults to ./Structure when omitted.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Directory where JSONL files will be written (default: current directory).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Base directory used to compute relative paths in the JSON output (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging for troubleshooting.",
    )
    return parser.parse_args()


def generate_artifacts(
    *,
    export_root: Path,
    output_dir: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    logger: Optional[logging.Logger] = None,
) -> dict:
    """
    Build the JSONL glue artifacts for a given export.

    Returns a mapping of artifact path -> record count.
    """
    log = logger or logging.getLogger(__name__)

    export_root = export_root.resolve()
    if not export_root.exists():
        raise FileNotFoundError(f"Export root {export_root} does not exist.")

    if output_dir is None:
        output_dir = export_root
    if not output_dir.is_absolute():
        output_dir = (export_root / output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if repo_root is None:
        repo_root = export_root.parent
    else:
        if not repo_root.is_absolute():
            repo_root = repo_root.resolve()

    contexts = collect_export(export_root)
    if not contexts:
        raise RuntimeError(f"No docs found under {export_root}")

    summary: dict[str, int] = {}

    crosswalk_records = build_crosswalk(contexts, repo_root)
    crosswalk_path = output_dir / "id_crosswalk.jsonl"
    count = write_jsonl(crosswalk_records, crosswalk_path)
    log.info("Wrote %s (%s records)", crosswalk_path, count)
    summary[str(crosswalk_path)] = count

    views_records = build_normalized_views(contexts, repo_root)
    views_path = output_dir / "views_normalized.jsonl"
    count = write_jsonl(views_records, views_path)
    log.info("Wrote %s (%s records)", views_path, count)
    summary[str(views_path)] = count

    dependency_records = build_dependency_index(contexts, repo_root)
    dependency_path = output_dir / "dependency_index.jsonl"
    count = write_jsonl(dependency_records, dependency_path)
    log.info("Wrote %s (%s records)", dependency_path, count)
    summary[str(dependency_path)] = count

    log.info("Bootstrap artifacts regenerated successfully.")
    return summary


def main() -> int:
    args = parse_args()
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    repo_root = args.repo_root.resolve()

    export_root = args.export_root
    if export_root is None:
        export_root = Path("Structure")
    if not export_root.is_absolute():
        export_root = (repo_root / export_root).resolve()

    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = (repo_root / output_dir).resolve()

    try:
        generate_artifacts(
            export_root=export_root,
            output_dir=output_dir,
            repo_root=repo_root,
            logger=logging.getLogger("bootstrap"),
        )
    except FileNotFoundError as exc:
        logging.error("%s", exc)
        return 1
    except RuntimeError as exc:
        logging.error("%s", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
