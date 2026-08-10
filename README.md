# Day 1 · Lab 1 — Clean the messy sales file  (STARTER)

> Every function in `parsing.py` and `cleaner.py` raises `NotImplementedError`.
> The tests are complete and currently failing. Make them pass.
> Read a failing test before you write the function it covers — the test is the spec.

Read a deliberately messy CSV, clean it, write the output, and prove it works
with tests. Submitted as a pull request and reviewed by a peer before it counts
as done.

Time: the afternoon workshop, 13:30–16:15. Demo at 16:15.

---

## The problem

`data/messy_sales.csv` is a real-shaped export from an order system. It contains
every failure mode we will meet again in Week 2 when the same data arrives through
Azure Data Factory:

| What is wrong | Example in the file |
|---|---|
| A byte-order mark on the first header | `\ufefforder_id` |
| Inconsistent header casing and spacing | `Order Date`, `  customer_name  ` |
| Six date formats | `2024-01-15`, `15/01/2024`, `Jan 17 2024`, `17 Jan 2024`, `2024/01/26` |
| Currency symbols and thousands separators | `"1,200.50"` |
| Accounting negatives | `(1200.00)`, `1200.00-` |
| Six spellings of "nothing" | empty, `NA`, `N/A`, `NULL`, `-`, `?` |
| Inconsistent casing and spacing in text | `  ravi   kumar `, `PRIYA SHARMA`, `SOUTH` |
| Invalid values that still parse | `quantity = -2` |
| A missing business key | a row with no `order_id` |
| A duplicate corrected later | `ORD-1001` appears twice, the later one wins |

## What you build

A package that turns that file into two files:

- **`clean.csv`** — validated rows, normalised, deduplicated, with a computed `line_total`
- **`clean_rejects.csv`** — every row that did not make it, with a readable reason and its line number

The rule that matters: **nothing is dropped silently.** For any run,
`rows in == clean + rejected + duplicates removed`. There is a test that asserts
exactly this, and it is the test to point at in your demo.

## Running it

```bash
uv sync --extra dev                 # create the environment
uv run pytest                       # run the tests
uv run clean-sales data/messy_sales.csv out/clean.csv --rejects out/rejects.csv
```

Without uv:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
python -m sales_cleaner.cli data/messy_sales.csv out/clean.csv
```

Expected on the shipped data file:

```
in=14 clean=4 rejected=9 duplicates_removed=1
```

## Layout

```
src/sales_cleaner/
    parsing.py    field-level parsers — never raise, return None on failure
    cleaner.py    row validation, rejection, deduplication, file IO
    cli.py        argument parsing and printing only
tests/
    conftest.py       shared fixtures
    test_parsing.py   the five required edge-case tests
    test_cleaner.py   row validation, rejection and deduplication
```

## The five tests the brief requires

They are in `tests/test_parsing.py`, one section per edge case:

1. **Amounts** — currency symbols, thousands separators, and three ways of writing a negative
2. **Dates** — six formats from one source, plus day-first disambiguation
3. **Nulls** — twelve spellings of "no value", and the proof that `0` is not one of them
4. **Text** — whitespace collapsing and title casing, returning `None` rather than `""`
5. **Integers** — tolerating `4.0` and `1,000`, rejecting `4.5`

## Design decisions you should be able to defend

Your reviewer will ask about these. So will an interviewer.

- **Parsers return `None`, they never raise.** Parsing that raises forces the caller to wrap every call in `try/except`, and the usual result is a bare `except:` that swallows real bugs alongside bad data.
- **`Decimal`, not `float`, for money.** `0.1 + 0.2 != 0.3` and finance will notice. There is a test that stops anyone "simplifying" this later.
- **Bad rows are rejected, not dropped.** A pipeline that silently discards rows is one nobody trusts, and "the numbers don't match" is the most expensive conversation in data engineering.
- **A missing required column raises.** That is a structural failure of the whole file. There is no sensible per-row recovery, and continuing would produce clean-looking output that is silently wrong.
- **Parsing succeeding and validation failing are different things.** `(1200.00)` parses correctly to `-1200.00` and is then rejected as an invalid unit price. Conflating the two is how a credit note gets loaded as a sale.
- **Deduplication keeps the latest per `order_id`**, with file order breaking a date tie, because that is how this source issues corrections.

## Definition of done

- [ ] `uv run pytest` passes, all tests green
- [ ] `uv run ruff check .` clean
- [ ] The CLI runs end to end on `data/messy_sales.csv` and produces both output files
- [ ] Running it twice produces identical output — there is a test for this
- [ ] Every rejected row has a reason a non-engineer could act on
- [ ] Type hints on every public function
- [ ] No bare `except:` anywhere in the codebase
- [ ] README updated if you changed the interface
- [ ] Opened as a pull request, reviewed by a peer, comments addressed, merged

## Pull request checklist

Reviewers: do not approve until you can answer yes to all of these.

- [ ] Can I run this from a clean checkout by following the README alone?
- [ ] Does every test assert something that would actually fail if the code were wrong?
- [ ] Is there a test for the case the author found hardest? (Ask them which one it was.)
- [ ] Are exceptions caught by type, never bare?
- [ ] Is money a `Decimal` everywhere?
- [ ] Would I understand the reject reasons if I were the person who owns the source system?

## Stretch, if you finish early

Do not start these until the definition of done is met.

1. Add `--strict` so unknown columns cause a rejection instead of being ignored.
2. Emit a run summary as JSON for a future orchestrator to read.
3. Add a `--sample N` flag that processes only the first N rows, for quick iteration on a large file.
4. Make the date formats configurable rather than hard-coded, and explain in the PR what you gave up by doing so.
