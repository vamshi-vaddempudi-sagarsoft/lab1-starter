"""Tests for row validation, rejection and deduplication.

The central claim these tests defend: a row that does not reach the output must
appear in the rejects with a reason. Nothing is dropped silently.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from sales_cleaner.cleaner import (
    CleanRow,
    MissingColumnsError,
    RejectedRow,
    clean_file,
    clean_row,
    clean_rows,
    deduplicate,
    read_raw_csv,
    write_clean_csv,
    write_rejects_csv,
)


def test_a_good_row_cleans_and_normalises(raw_row):
    result = clean_row(raw_row, source_line=2)
    assert isinstance(result, CleanRow)
    assert result.customer_name == "Test Customer"   # title-cased
    assert result.region == "South"                  # title-cased
    assert result.order_date == date(2024, 3, 1)
    assert result.unit_price == Decimal("100.00")
    assert result.line_total == Decimal("200.00")


@pytest.mark.parametrize(
    ("field", "value", "expected_reason"),
    [
        ("order_id", "", "missing order_id"),
        ("order_date", "not-a-date", "unparseable or missing order_date"),
        ("customer_name", "N/A", "missing customer_name"),
        ("region", "", "missing region"),
        ("product", "NULL", "missing product"),
        ("quantity", "abc", "unparseable or missing quantity"),
        ("unit_price", "NULL", "unparseable or missing unit_price"),
    ],
)
def test_bad_rows_are_rejected_with_a_readable_reason(raw_row, field, value, expected_reason):
    """Every rejection carries a reason someone can act on without reading the code."""
    raw_row[field] = value
    result = clean_row(raw_row, source_line=7)
    assert isinstance(result, RejectedRow)
    assert result.reason == expected_reason
    assert result.source_line == 7


def test_negative_quantity_is_rejected_not_silently_corrected(raw_row):
    """A negative quantity is a source problem. Fixing it here hides the problem."""
    raw_row["quantity"] = "-2"
    result = clean_row(raw_row, source_line=9)
    assert isinstance(result, RejectedRow)
    assert "positive" in result.reason


def test_zero_quantity_is_rejected(raw_row):
    raw_row["quantity"] = "0"
    result = clean_row(raw_row, source_line=9)
    assert isinstance(result, RejectedRow)


def test_deduplicate_keeps_the_latest_row_per_order_id():
    """Corrections arrive as a second row with the same id and a later date."""
    early = CleanRow("ORD-1", date(2024, 1, 1), "A", "South", "W", 1, Decimal("10"))
    late = CleanRow("ORD-1", date(2024, 1, 9), "A", "South", "W", 4, Decimal("10"))
    other = CleanRow("ORD-2", date(2024, 1, 5), "B", "North", "W", 2, Decimal("20"))

    kept, removed = deduplicate([early, other, late])

    assert removed == 1
    assert len(kept) == 2
    surviving = {row.order_id: row for row in kept}
    assert surviving["ORD-1"].quantity == 4      # the later row won
    assert surviving["ORD-2"].quantity == 2


def test_deduplicate_breaks_a_date_tie_with_file_order():
    """Same id, same date: the row that appeared later is the correction."""
    first = CleanRow("ORD-1", date(2024, 1, 1), "A", "South", "W", 1, Decimal("10"))
    second = CleanRow("ORD-1", date(2024, 1, 1), "A", "South", "W", 9, Decimal("10"))
    kept, removed = deduplicate([first, second])
    assert removed == 1
    assert kept[0].quantity == 9


def test_nothing_is_lost_every_row_is_accounted_for(messy_csv: Path):
    """The count that matters: in == clean + rejected + duplicates removed."""
    result = clean_file(messy_csv)
    assert result.total_in == 12
    assert len(result.clean) + len(result.rejected) + result.duplicates_removed == 12


def test_the_messy_file_produces_the_expected_split(messy_csv: Path):
    """12 rows in: 3 survive, 8 are rejected with reasons, 1 is a duplicate.

    Worth reading the reject list out loud in review — every one of the eight is
    a different failure mode, and none of them was dropped silently.
    """
    result = clean_file(messy_csv)
    assert len(result.clean) == 3
    assert result.duplicates_removed == 1
    assert len(result.rejected) == 8

    reasons = [row.reason for row in result.rejected]
    assert "missing customer_name" in reasons
    assert "unparseable or missing order_date" in reasons
    assert "missing order_id" in reasons
    assert "missing product" in reasons
    assert any("quantity must be positive" in reason for reason in reasons)
    assert any("unit_price must not be negative" in reason for reason in reasons)


def test_a_parenthesised_negative_parses_then_fails_validation(messy_csv: Path):
    """(1200.00) is a valid number and an invalid unit price.

    Parsing succeeding and validation failing are different things. Conflating
    them is how you end up with a credit note silently loaded as a sale.
    """
    result = clean_file(messy_csv)
    negatives = [r for r in result.rejected if "unit_price must not be negative" in r.reason]
    assert len(negatives) == 1
    assert negatives[0].raw["order_id"] == "ORD-1008"


def test_header_normalisation_handles_bom_case_and_spaces(messy_csv: Path):
    """The file starts with a BOM and has 'Order Date' and ' customer_name '."""
    rows = list(read_raw_csv(messy_csv))
    assert "order_date" in rows[0]
    assert "customer_name" in rows[0]
    assert "\ufefforder_id" not in rows[0]


def test_missing_required_column_raises_rather_than_producing_wrong_output(tmp_path: Path):
    """A structural failure has no sensible per-row recovery — it must stop the run."""
    broken = tmp_path / "broken.csv"
    broken.write_text("order_id,order_date\nORD-1,2024-01-01\n", encoding="utf-8")
    with pytest.raises(MissingColumnsError) as excinfo:
        list(read_raw_csv(broken))
    assert "customer_name" in str(excinfo.value)


def test_outputs_are_written_and_readable(messy_csv: Path, tmp_path: Path):
    result = clean_file(messy_csv)
    clean_path = tmp_path / "out" / "clean.csv"
    rejects_path = tmp_path / "out" / "rejects.csv"

    written = write_clean_csv(result.clean, clean_path)
    rejected = write_rejects_csv(result.rejected, rejects_path)

    assert written == len(result.clean)
    assert rejected == len(result.rejected)
    assert clean_path.exists() and rejects_path.exists()

    header = clean_path.read_text(encoding="utf-8").splitlines()[0]
    assert header.split(",") == [
        "order_id", "order_date", "customer_name", "region",
        "product", "quantity", "unit_price", "line_total",
    ]


def test_cleaning_is_idempotent(messy_csv: Path, tmp_path: Path):
    """Running twice produces the same output. Re-runnable is the whole point."""
    first = clean_file(messy_csv)
    second = clean_file(messy_csv)
    assert [row.as_dict() for row in first.clean] == [row.as_dict() for row in second.clean]


def test_clean_rows_reports_source_line_numbers_matching_the_file():
    """A reject reported as 'line 4' must be line 4 when someone opens the file."""
    rows = [
        {"order_id": "ORD-1", "order_date": "2024-01-01", "customer_name": "A",
         "region": "South", "product": "W", "quantity": "1", "unit_price": "10"},
        {"order_id": "", "order_date": "2024-01-02", "customer_name": "B",
         "region": "North", "product": "W", "quantity": "1", "unit_price": "10"},
    ]
    result = clean_rows(rows)
    assert result.rejected[0].source_line == 3   # header is 1, first data row is 2
