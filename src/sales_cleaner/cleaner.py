"""Row-level cleaning, validation and deduplication.

Design decision worth being able to defend in a review: bad rows are *rejected*,
not dropped. Every row that does not make it into the clean output comes out in
the rejects list with a human-readable reason. A pipeline that silently discards
rows is a pipeline nobody can trust, and "the numbers don't match" is the most
expensive conversation in data engineering.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Iterable, Iterator

from .parsing import normalise_text, parse_amount, parse_date, parse_int

# The columns the downstream contract requires. Anything else in the file is
# ignored rather than passed through — an unexpected column is not our problem
# to solve, but it is our problem to not propagate.
REQUIRED_COLUMNS: tuple[str, ...] = (
    "order_id",
    "order_date",
    "customer_name",
    "region",
    "product",
    "quantity",
    "unit_price",
)


@dataclass(frozen=True, slots=True)
class CleanRow:
    """A validated sales row. Immutable on purpose — nothing downstream edits it."""

    order_id: str
    order_date: date
    customer_name: str
    region: str
    product: str
    quantity: int
    unit_price: Decimal

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity

    def as_dict(self) -> dict[str, str]:
        return {
            "order_id": self.order_id,
            "order_date": self.order_date.isoformat(),
            "customer_name": self.customer_name,
            "region": self.region,
            "product": self.product,
            "quantity": str(self.quantity),
            "unit_price": f"{self.unit_price:.2f}",
            "line_total": f"{self.line_total:.2f}",
        }


@dataclass(frozen=True, slots=True)
class RejectedRow:
    """A row that failed validation, kept with the reason and its source line."""

    source_line: int
    reason: str
    raw: dict[str, str]

    def as_dict(self) -> dict[str, str]:
        return {
            "source_line": str(self.source_line),
            "reason": self.reason,
            "order_id": self.raw.get("order_id", ""),
            "raw": "|".join(f"{k}={v}" for k, v in self.raw.items()),
        }


@dataclass(slots=True)
class CleanResult:
    """What came out of a clean run: the good rows, the bad rows, and counts."""

    clean: list[CleanRow] = field(default_factory=list)
    rejected: list[RejectedRow] = field(default_factory=list)
    duplicates_removed: int = 0

    @property
    def total_in(self) -> int:
        return len(self.clean) + len(self.rejected) + self.duplicates_removed

    def summary(self) -> str:
        return (
            f"in={self.total_in} clean={len(self.clean)} "
            f"rejected={len(self.rejected)} duplicates_removed={self.duplicates_removed}"
        )


class MissingColumnsError(ValueError):
    """Raised when the file does not have the columns the contract requires.

    This one *does* raise, unlike the parsing helpers. A missing column is a
    structural failure of the whole file — there is no sensible per-row recovery,
    and continuing would produce a clean-looking output that is silently wrong.
    """

    def __init__(self, missing: Iterable[str]) -> None:
        self.missing = sorted(missing)
        super().__init__(f"missing required columns: {', '.join(self.missing)}")


def _normalise_header(name: str) -> str:
    """Header names arrive with stray spaces, mixed case and the odd BOM."""
    return name.replace("\ufeff", "").strip().lower().replace(" ", "_")


def clean_row(raw: dict[str, str], source_line: int) -> CleanRow | RejectedRow:
    """Validate and convert one raw row.

    Returns a CleanRow or a RejectedRow — never raises, and never returns None.
    A union return type keeps the caller honest: they have to handle both.
    """
    # TODO: implement. See the tests for the exact behaviour required.
    raise NotImplementedError

def deduplicate(rows: Iterable[CleanRow]) -> tuple[list[CleanRow], int]:
    """Keep the latest row per order_id.

    'Latest' means the highest order_date; where two rows share a date, the one
    that appeared later in the file wins, because that is the convention this
    source uses for corrections.

    Returns (kept_rows, number_removed). Order of the input is preserved for the
    rows that survive, which makes the output diffable between runs.
    """
    # TODO: implement. See the tests for the exact behaviour required.
    raise NotImplementedError

def clean_rows(raw_rows: Iterable[dict[str, str]], *, first_line: int = 2) -> CleanResult:
    """Clean an iterable of raw rows and deduplicate the survivors.

    first_line defaults to 2 because line 1 of a CSV is the header, and reporting
    a rejected row as "line 7" only helps if it matches what the person sees when
    they open the file.
    """
    # TODO: implement. See the tests for the exact behaviour required.
    raise NotImplementedError

def read_raw_csv(path: Path) -> Iterator[dict[str, str]]:
    """Read a CSV, normalising headers and tolerating a BOM.

    Raises MissingColumnsError if the contract columns are not all present.
    Rows with the wrong number of fields come back with None values, which the
    row validator then rejects with a readable reason.
    """
    # TODO: implement. See the tests for the exact behaviour required.
    raise NotImplementedError

def clean_file(source: Path) -> CleanResult:
    """Read and clean a CSV file. Thin wrapper so the CLI stays trivial."""
    return clean_rows(read_raw_csv(source))


def write_clean_csv(rows: Iterable[CleanRow], destination: Path) -> int:
    """Write clean rows. Returns the count written."""
    # TODO: implement. See the tests for the exact behaviour required.
    raise NotImplementedError

def write_rejects_csv(rows: Iterable[RejectedRow], destination: Path) -> int:
    """Write rejected rows with their reasons. Returns the count written."""
    # TODO: implement. See the tests for the exact behaviour required.
    raise NotImplementedError
