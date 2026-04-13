"""
test_northwind_cheatsheet.py
============================
Validates every cheat-sheet Pure query against the live Legend Intelligence
backend (http://localhost:8080).

For each entry in CHEAT_SHEET:
  - DB-backed examples: seed Northwind tables once, then execute
  - TDS-literal examples: execute directly (no model / seeding needed)

Run:
    pytest tests/test_northwind_cheatsheet.py -v

Requirements:
    pip install pytest requests
    ./legend-lite/start-nlq.sh &   # backend must be running on :8080
"""

import json
import sys
import time
import urllib.request
import urllib.error

import pytest

# ── import constants from the dedicated data module (no Streamlit dependency) ─
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from northwind_data import (  # noqa: E402
    NORTHWIND_MODEL,
    NORTHWIND_SEED_SQL,
    CHEAT_SHEET,
    ENGINE_URL,
)

# ── helpers ───────────────────────────────────────────────────────────────────

def _post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        ENGINE_URL + path,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _health() -> bool:
    try:
        with urllib.request.urlopen(f"{ENGINE_URL}/health", timeout=3) as r:
            return json.loads(r.read()).get("status") == "ok"
    except Exception:
        return False


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def require_engine():
    """Fail fast if the Legend engine is not reachable."""
    for attempt in range(3):
        if _health():
            return
        time.sleep(2)
    pytest.skip(
        "Legend engine not reachable at http://localhost:8080 — "
        "start it with ./legend-lite/start-nlq.sh before running tests."
    )


@pytest.fixture(scope="session")
def northwind_seeded():
    """Seed Northwind tables once for the whole session."""
    result = _post(
        "/engine/sql",
        {
            "code": NORTHWIND_MODEL,
            "sql": NORTHWIND_SEED_SQL,
            "runtime": "northwind::runtime::NorthwindRuntime",
        },
    )
    if not result.get("success"):
        pytest.fail(f"Northwind seed failed: {result.get('error')}")
    return True


# ── parametrised test ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("op_name", list(CHEAT_SHEET.keys()))
def test_cheat_sheet_query(op_name, northwind_seeded):
    """
    Each cheat-sheet query must:
      1. Execute without error (success=True)
      2. Return a non-negative row count
      3. Return column metadata
    """
    group, description, query, explanation, uses_db = CHEAT_SHEET[op_name]

    full_code = (NORTHWIND_MODEL.strip() + "\n\n" + query.strip()).strip()

    result = _post("/engine/execute", {"code": full_code})

    assert result.get("success"), (
        f"\n[FAIL] {op_name}\n"
        f"Query:\n{query}\n\n"
        f"Error: {result.get('error', 'No error message returned')}"
    )

    row_count = result.get("rowCount", -1)
    assert row_count >= 0, (
        f"[{op_name}] rowCount should be >= 0, got {row_count}"
    )

    columns = result.get("columns")
    assert columns and len(columns) > 0, (
        f"[{op_name}] Expected at least one column in result, got: {columns}"
    )


# ── standalone seed test ──────────────────────────────────────────────────────

def test_northwind_seed_succeeds():
    """Verify that seeding the Northwind DB returns success."""
    result = _post(
        "/engine/sql",
        {
            "code": NORTHWIND_MODEL,
            "sql": NORTHWIND_SEED_SQL,
            "runtime": "northwind::runtime::NorthwindRuntime",
        },
    )
    assert result.get("success"), f"Seed failed: {result.get('error')}"


def test_product_count():
    """After seeding, Product.all() should return 15 rows."""
    query = (
        "northwind::model::Product.all()"
        "->project([p|$p.productId, p|$p.productName], ['id','name'])"
    )
    full_code = NORTHWIND_MODEL.strip() + "\n\n" + query
    result = _post("/engine/execute", {"code": full_code})
    assert result.get("success"), result.get("error")
    assert result.get("rowCount") == 15, (
        f"Expected 15 products, got {result.get('rowCount')}"
    )


def test_order_count():
    """After seeding, Order.all() should return 15 rows."""
    query = (
        "northwind::model::Order.all()"
        "->project([o|$o.orderId, o|$o.shipCountry], ['id','country'])"
    )
    full_code = NORTHWIND_MODEL.strip() + "\n\n" + query
    result = _post("/engine/execute", {"code": full_code})
    assert result.get("success"), result.get("error")
    assert result.get("rowCount") == 15, (
        f"Expected 15 orders, got {result.get('rowCount')}"
    )


def test_window_rank_tds_literal():
    """TDS-literal rank example — needs Runtime even though it doesn't use DB."""
    query = """\
#TDS
    product, category, unitPrice
    Chai,              Beverages, 18.0
    Chang,             Beverages, 19.0
    Aniseed Syrup,     Condiments, 10.0
    Chef Antons Cajun, Condiments, 22.0
#->extend(
    over(~category, ~unitPrice->descending()),
    ~priceRank:{p,w,r|$p->rank($w,$r)}
)"""
    full_code = NORTHWIND_MODEL.strip() + "\n\n" + query
    result = _post("/engine/execute", {"code": full_code})
    assert result.get("success"), result.get("error")
    assert result.get("rowCount") == 4


def test_asof_join_tds_literal():
    """AsOf join TDS literal — needs Runtime even though it doesn't use DB."""
    query = """\
#TDS
    tradeId, tradeTime
    1, %2024-01-15T10:30:00
    2, %2024-01-15T10:50:00
    3, %2024-01-15T11:30:00
#->asOfJoin(
    #TDS
        quoteId, quoteTime, marketPrice
        A, %2024-01-15T10:15:00, 100.0
        B, %2024-01-15T10:45:00, 102.5
        C, %2024-01-15T11:15:00, 105.0
        D, %2024-01-15T12:00:00, 108.0
    #,
    {t, q | $t.tradeTime > $q.quoteTime}
)"""
    full_code = NORTHWIND_MODEL.strip() + "\n\n" + query
    result = _post("/engine/execute", {"code": full_code})
    assert result.get("success"), result.get("error")
    assert result.get("rowCount") == 3


def test_join_product_category():
    """Navigation join: Product → Category must return categoryName column."""
    query = (
        "northwind::model::Product.all()"
        "->project([p|$p.productName, p|$p.category.categoryName], ['product','category'])"
        "->sort('category')"
    )
    full_code = NORTHWIND_MODEL.strip() + "\n\n" + query
    result = _post("/engine/execute", {"code": full_code})
    assert result.get("success"), result.get("error")
    assert "category" in result.get("columns", [])


def test_groupby_count():
    """GroupBy + count on shipCountry should return fewer rows than total orders."""
    query = (
        "northwind::model::Order.all()"
        "->project([o|$o.shipCountry, o|$o.orderId], ['country','orderId'])"
        "->groupBy([{r|$r.country}],[{r|$r.orderId->count()}],['country','orderCount'])"
        "->sort(~orderCount->descending())"
    )
    full_code = NORTHWIND_MODEL.strip() + "\n\n" + query
    result = _post("/engine/execute", {"code": full_code})
    assert result.get("success"), result.get("error")
    # 15 orders across multiple countries → distinct country count < 15
    assert 0 < result.get("rowCount", 0) < 15
