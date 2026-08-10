"""Shared fixtures.

tmp_path is a pytest built-in fixture giving each test its own throwaway
directory, so no test can see another test's files and nothing is left behind.
"""

from __future__ import annotations

from pathlib import Path

import pytest

MESSY_CSV = """\ufefforder_id,Order Date, customer_name ,region,product,quantity,unit_price
ORD-1001,2024-01-15,  ravi   kumar ,SOUTH,Widget A,3,"1,200.50"
ORD-1002,15/01/2024,PRIYA SHARMA,north,Widget B,2,899
ORD-1003,Jan 17 2024,anil verma,South,Widget A,1,450.00
ORD-1004,2024-01-18,,East,Widget C,5,300
ORD-1005,not-a-date,Sunita Rao,West,Widget A,2,500
ORD-1006,2024-01-19,Mohan Das,North,Widget B,-2,750
ORD-1007,2024-01-20,Kavita Nair,South,Widget C,N/A,650
ORD-1008,2024-01-21,Deepak Menon,East,Widget A,4,(1200.00)
,2024-01-22,Ghost Order,West,Widget B,1,100
ORD-1001,2024-01-25,Ravi Kumar,South,Widget A,4,"1,200.50"
ORD-1009,2024-01-23,Sneha Iyer,north,,2,400
ORD-1010,2024-01-24,Arjun Pillai,South,Widget D,2,NULL
"""


@pytest.fixture
def messy_csv(tmp_path: Path) -> Path:
    """A CSV containing every failure mode this lab has to handle."""
    path = tmp_path / "messy_sales.csv"
    path.write_text(MESSY_CSV, encoding="utf-8")
    return path


@pytest.fixture
def raw_row() -> dict[str, str]:
    """One valid raw row. Tests copy and mutate it rather than rebuilding it."""
    return {
        "order_id": "ORD-9001",
        "order_date": "2024-03-01",
        "customer_name": "test customer",
        "region": "south",
        "product": "Widget Z",
        "quantity": "2",
        "unit_price": "100.00",
    }
