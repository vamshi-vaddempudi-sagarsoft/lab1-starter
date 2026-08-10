"""Field-level parsing helpers.

Every function here follows the same contract: it takes whatever ugly string the
CSV actually contained and returns either a clean typed value or None. None means
"absent or unparseable" — it never means zero, and it never raises. Deciding what
to *do* about a None is the caller's job, not ours.

That separation is deliberate. Parsing that raises forces the caller to wrap every
call in try/except, and the usual result is a bare `except:` that swallows real
bugs alongside bad data.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

# Values that different upstream systems use to mean "nothing here".
# Compared case-insensitively after stripping.
NULL_TOKENS: frozenset[str] = frozenset(
    {"", "na", "n/a", "null", "none", "-", "--", "nil", "nan", "?"}
)

# The three date formats this source is known to emit. Order matters:
# %d/%m/%Y is tried before %m/%d/%Y because this feed is European-formatted.
DATE_FORMATS: tuple[str, ...] = (
    "%Y-%m-%d",      # 2024-01-15
    "%d/%m/%Y",      # 15/01/2024
    "%d-%m-%Y",      # 15-01-2024
    "%b %d %Y",      # Jan 15 2024
    "%d %b %Y",      # 15 Jan 2024
    "%Y/%m/%d",      # 2024/01/15
)

# Currency symbols and separators we strip before parsing a number.
_AMOUNT_STRIP = re.compile(r"[₹$€£,\s]")
_TRAILING_MINUS = re.compile(r"^(?P<body>[\d.]+)-$")
_PARENTHESISED = re.compile(r"^\((?P<body>.+)\)$")


def is_null(raw: str | None) -> bool:
    """True when the raw field means 'no value'.

    Handles the six different spellings of nothing that show up in this feed.
    """
    # TODO: implement. See the tests for the exact behaviour required.
    raise NotImplementedError

def normalise_text(raw: str | None, *, title_case: bool = False) -> str | None:
    """Collapse whitespace and optionally title-case a text field.

    Returns None for null-ish input rather than an empty string, so that a
    missing region and a region literally named "" cannot be confused.
    """
    # TODO: implement. See the tests for the exact behaviour required.
    raise NotImplementedError

def parse_date(raw: str | None) -> date | None:
    """Parse a date written in any of the formats this feed uses.

    Returns None when the value is missing or matches none of the known formats.
    A date that parses but is obviously wrong (year 1900, year 2999) is still
    returned — range checking is a validation concern, not a parsing one.
    """
    # TODO: implement. See the tests for the exact behaviour required.
    raise NotImplementedError

def parse_amount(raw: str | None) -> Decimal | None:
    """Parse a monetary amount into a Decimal.

    Handles currency symbols, thousands separators, parenthesised negatives
    (1,200.00) and trailing-minus negatives (1200.00-), both of which appear in
    exports from older accounting systems.

    Decimal rather than float: money in a float is a bug waiting for a reconciliation
    meeting. 0.1 + 0.2 != 0.3 and finance will notice.
    """
    # TODO: implement. See the tests for the exact behaviour required.
    raise NotImplementedError

def parse_int(raw: str | None) -> int | None:
    """Parse an integer, tolerating separators and a stray decimal .0 suffix."""
    # TODO: implement. See the tests for the exact behaviour required.
    raise NotImplementedError
