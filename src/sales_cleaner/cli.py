"""Command-line entry point.

    uv run clean-sales data/messy_sales.csv out/clean.csv --rejects out/rejects.csv

Kept deliberately thin: argument parsing and printing only. Everything the CLI
does is available as a function, which is what makes the logic testable without
shelling out.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .cleaner import MissingColumnsError, clean_file, write_clean_csv, write_rejects_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clean-sales",
        description="Clean a messy sales CSV into a validated output plus a rejects file.",
    )
    parser.add_argument("source", type=Path, help="input CSV")
    parser.add_argument("destination", type=Path, help="where to write the clean CSV")
    parser.add_argument(
        "--rejects",
        type=Path,
        default=None,
        help="where to write rejected rows (default: alongside the output)",
    )
    parser.add_argument(
        "--fail-on-rejects",
        action="store_true",
        help="exit non-zero if any row was rejected (useful in CI)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.source.exists():
        print(f"error: {args.source} does not exist", file=sys.stderr)
        return 2

    try:
        result = clean_file(args.source)
    except MissingColumnsError as exc:
        # Caught by type, not with a bare except. We know exactly what this is
        # and exactly what to tell the user about it.
        print(f"error: {exc}", file=sys.stderr)
        return 3

    rejects_path = args.rejects or args.destination.with_name(
        args.destination.stem + "_rejects.csv"
    )

    written = write_clean_csv(result.clean, args.destination)
    rejected = write_rejects_csv(result.rejected, rejects_path)

    print(result.summary())
    print(f"wrote {written} clean rows to {args.destination}")
    print(f"wrote {rejected} rejected rows to {rejects_path}")

    if args.fail_on_rejects and rejected:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
