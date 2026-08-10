"""Tests for the field-level parsers — the five edge cases the brief requires.

Each test targets something that actually appears in the source file. None of
them is a happy path that would pass whatever the implementation did.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from sales_cleaner.parsing import (
    is_null,
    normalise_text,
    parse_amount,
    parse_date,
    parse_int,
)


# ============================================================ EDGE CASE 1
# Amounts arrive with currency symbols, thousands separators and three
# different conventions for writing a negative number.
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1,200.50", Decimal("1200.50")),      # thousands separator
        ("899", Decimal("899")),                # plain
        ("$1,000", Decimal("1000")),            # currency symbol
        ("  450.00  ", Decimal("450.00")),      # surrounding whitespace
        ("(1200.00)", Decimal("-1200.00")),     # accounting negative
        ("1200.00-", Decimal("-1200.00")),      # trailing-minus negative
        ("-750", Decimal("-750")),              # ordinary negative
        ("0", Decimal("0")),                    # zero is a value, not a null
    ],
)
def test_parse_amount_handles_symbols_separators_and_negatives(raw, expected):
    assert parse_amount(raw) == expected


def test_parse_amount_returns_none_rather_than_raising():
    """Unparseable input returns None so the caller decides. It never raises."""
    assert parse_amount("twelve hundred") is None
    assert parse_amount("N/A") is None
    assert parse_amount("") is None
    assert parse_amount(None) is None


def test_parse_amount_uses_decimal_not_float():
    """Money must not be a float. This test stops someone 'simplifying' later."""
    total = parse_amount("0.1") + parse_amount("0.2")
    assert total == Decimal("0.3")
    assert isinstance(total, Decimal)


# ============================================================ EDGE CASE 2
# One source system, six date formats. This is normal and it is not going away.
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2024-01-15", date(2024, 1, 15)),
        ("15/01/2024", date(2024, 1, 15)),
        ("15-01-2024", date(2024, 1, 15)),
        ("Jan 17 2024", date(2024, 1, 17)),
        ("17 Jan 2024", date(2024, 1, 17)),
        ("2024/01/15", date(2024, 1, 15)),
        ("  2024-01-15  ", date(2024, 1, 15)),
    ],
)
def test_parse_date_handles_every_format_in_the_feed(raw, expected):
    assert parse_date(raw) == expected


def test_parse_date_is_day_first_not_month_first():
    """13/01/2024 can only be 13 January. If this fails, the format order flipped."""
    assert parse_date("13/01/2024") == date(2024, 1, 13)


def test_parse_date_returns_none_for_unparseable_input():
    assert parse_date("not-a-date") is None
    assert parse_date("2024-13-45") is None
    assert parse_date("") is None


# ============================================================ EDGE CASE 3
# Several upstream systems, a dozen ways of writing "no value here".
@pytest.mark.parametrize(
    "token",
    ["", "  ", "NA", "n/a", "NULL", "null", "None", "-", "--", "nil", "NaN", "?"],
)
def test_every_spelling_of_nothing_is_treated_as_null(token):
    assert is_null(token) is True
    assert normalise_text(token) is None
    assert parse_amount(token) is None
    assert parse_date(token) is None
    assert parse_int(token) is None


def test_zero_is_a_value_not_a_null():
    """The classic falsy-value bug: 0 is data, not absence."""
    assert is_null("0") is False
    assert parse_amount("0") == Decimal("0")
    assert parse_int("0") == 0


# ============================================================ EDGE CASE 4
# The same customer written three different ways is still one customer.
def test_normalise_text_collapses_whitespace_and_title_cases():
    assert normalise_text("  ravi   kumar ", title_case=True) == "Ravi Kumar"
    assert normalise_text("SOUTH", title_case=True) == "South"
    assert normalise_text("Widget  A") == "Widget A"


def test_normalise_text_returns_none_not_empty_string():
    """None and '' must not be confused: one is missing, one would be a real value."""
    assert normalise_text("   ") is None
    assert normalise_text("   ") != ""


# ============================================================ EDGE CASE 5
# Spreadsheet exports write integers as 4.0 and 1,000. Both are integers.
# 4.5 is not, and must not silently become 4.
@pytest.mark.parametrize(
    ("raw", "expected"),
    [("3", 3), ("  5  ", 5), ("1,000", 1000), ("4.0", 4), ("-2", -2)],
)
def test_parse_int_tolerates_separators_and_decimal_suffix(raw, expected):
    assert parse_int(raw) == expected


def test_parse_int_rejects_genuine_decimals():
    assert parse_int("4.5") is None
