"""CLI entry point for the coda_export package."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from .api import CodaAPI, APIError
from .extract import CodaExporter
from .utils import ExportConfig, clamp_rows, compile_filter, load_token, setup_logging

try:
    from bootstrap_scripts.run_bootstrap import generate_artifacts
except ImportError:  # pragma: no cover - fallback if scripts missing
    generate_artifacts = None  # type: ignore[assignment]


app = typer.Typer(add_completion=False, help="Export structured metadata from a Coda doc.")


@app.command()
def main(
    doc_id: str = typer.Option(..., "--doc-id", help="Coda document identifier.", show_default=False),
    out: Path = typer.Option(Path("./Structure"), "--out", help="Output directory."),
    rows_per_table: int = typer.Option(100, "--rows-per-table", help="Maximum rows to sample per table (cap at 100)."),
    include_rows: bool = typer.Option(True, "--include-rows/--no-include-rows", help="Toggle sample row export."),
    include_formulas: bool = typer.Option(True, "--include-formulas/--no-include-formulas", help="Toggle formulas export."),
    include_controls: bool = typer.Option(True, "--include-controls/--no-include-controls", help="Toggle controls export."),
    export_markdown_also: bool = typer.Option(
        False,
        "--export-markdown-also/--export-html-only",
        help="Additionally download each page canvas as Markdown alongside HTML.",
    ),
    timeout: float = typer.Option(30.0, "--timeout", help="HTTP timeout in seconds."),
    max_retries: int = typer.Option(5, "--max-retries", help="Maximum retry attempts on failed requests."),
    sleep_initial: float = typer.Option(
        0.8,
        "--sleep-initial",
        help="Initial backoff duration (seconds) when retrying requests.",
    ),
    filter_tables: Optional[str] = typer.Option(
        None,
        "--filter-tables",
        help="Regex to include tables/views by name.",
    ),
    visible_only: bool = typer.Option(
        True,
        "--visible-only/--include-hidden",
        help="Whether to include only visible columns.",
    ),
) -> None:
    """Entry point invoked by ``python -m coda_export``."""
    out_dir = out.resolve()
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        typer.secho(f"Failed to prepare output directory {out_dir}: {exc}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    log_path = out_dir / "log.txt"
    logger = setup_logging(log_path)
    logger.info("Logging diagnostics to %s", log_path)

    try:
        token = load_token()
    except RuntimeError as exc:
        logger.error("Missing API token: %s", exc)
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    try:
        compiled_filter = compile_filter(filter_tables)
    except ValueError as exc:
        logger.error("Invalid table filter: %s", exc)
        typer.secho(str(exc), err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc

    clamped_rows = clamp_rows(rows_per_table)

    config = ExportConfig(
        doc_id=doc_id,
        out_dir=out_dir,
        rows_per_table=clamped_rows,
        include_rows=include_rows,
        include_formulas=include_formulas,
        include_controls=include_controls,
        export_markdown_also=export_markdown_also,
        timeout=timeout,
        max_retries=max_retries,
        sleep_initial=sleep_initial,
        filter_tables=compiled_filter,
        visible_only=visible_only,
    )

    logger.info("Starting export for doc %s", doc_id)

    try:
        with CodaAPI(
            token=token,
            timeout=timeout,
            max_retries=max_retries,
            sleep_initial=sleep_initial,
            logger=logger,
        ) as api:
            exporter = CodaExporter(api=api, config=config)
            counts = exporter.run()
    except APIError as exc:
        logger.error("Export failed: %s", exc)
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # pragma: no cover - safeguard
        logger.exception("Unexpected error during export")
        raise typer.Exit(code=1) from exc

    counts_str = ", ".join(f"{k}={v}" for k, v in counts.as_dict().items())
    logger.info("Export complete. %s", counts_str)
    logger.info("Output written to %s/docs/%s", out_dir, doc_id)

    if generate_artifacts is not None:
        try:
            artifact_summary = generate_artifacts(
                export_root=out_dir,
                output_dir=out_dir,
                repo_root=out_dir.parent,
                logger=logger,
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.error("Failed to generate bootstrap artifacts: %s", exc)
        else:
            formatted = ", ".join(f"{Path(path).name}={count}" for path, count in artifact_summary.items())
            logger.info("Bootstrap artifacts updated: %s", formatted)
    else:  # pragma: no cover - scaffolding
        logger.warning("bootstrap_scripts package not available; skipping artifact generation.")


if __name__ == "__main__":
    app()
