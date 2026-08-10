"""sales_cleaner — Day 1 Lab 1.

Read a messy sales CSV, clean it, and write two outputs: the rows that survived
and the rows that did not, each with a reason.
"""

from .cleaner import (
    CleanResult,
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
from .parsing import is_null, normalise_text, parse_amount, parse_date, parse_int

__all__ = [
    "CleanResult", "CleanRow", "RejectedRow", "MissingColumnsError",
    "clean_file", "clean_row", "clean_rows", "deduplicate", "read_raw_csv",
    "write_clean_csv", "write_rejects_csv",
    "is_null", "normalise_text", "parse_amount", "parse_date", "parse_int",
]
__version__ = "1.0.0"
