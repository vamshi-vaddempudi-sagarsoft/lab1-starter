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
    if raw is None:
        return True
    return raw.strip().lower() in NULL_TOKENS


def normalise_text(raw: str | None, *, title_case: bool = False) -> str | None:
    """Collapse whitespace and optionally title-case a text field.

    Returns None for null-ish input rather than an empty string, so that a
    missing region and a region literally named "" cannot be confused.
    """
    if is_null(raw):
        return None
    collapsed = " ".join(raw.split())
    return collapsed.title() if title_case else collapsed


def parse_date(raw: str | None) -> date | None:
    """Parse a date written in any of the formats this feed uses.

    Returns None when the value is missing or matches none of the known formats.
    A date that parses but is obviously wrong (year 1900, year 2999) is still
    returned — range checking is a validation concern, not a parsing one.
    """
    if is_null(raw):
        return None
    text = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def parse_amount(raw: str | None) -> Decimal | None:
    """Parse a monetary amount into a Decimal.

    Handles currency symbols, thousands separators, parenthesised negatives
    (1,200.00) and trailing-minus negatives (1200.00-), both of which appear in
    exports from older accounting systems.

    Decimal rather than float: money in a float is a bug waiting for a reconciliation
    meeting. 0.1 + 0.2 != 0.3 and finance will notice.
    """
    if is_null(raw):
        return None

    text = raw.strip()
    negative = False

    matched = _PARENTHESISED.match(text)
    if matched:
        negative = True
        text = matched.group("body")

    text = _AMOUNT_STRIP.sub("", text)

    matched = _TRAILING_MINUS.match(text)
    if matched:
        negative = True
        text = matched.group("body")

    if text.startswith("-"):
        negative = True
        text = text[1:]

    if not text:
        return None

    try:
        value = Decimal(text)
    except InvalidOperation:
        return None

    return -value if negative else value


def parse_int(raw: str | None) -> int | None:
    """Parse an integer, tolerating separators and a stray decimal .0 suffix."""
    if is_null(raw):
        return None
    text = _AMOUNT_STRIP.sub("", raw.strip())
    if text.endswith(".0"):
        text = text[:-2]
    try:
        return int(text)
    except ValueError:
        return None
