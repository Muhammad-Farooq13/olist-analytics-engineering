"""Tests for the dbt-built marts layer.

These check business-logic invariants directly against the warehouse — a
complement to (not a replacement for) dbt's own schema tests, which already
ran as part of `dbt build`. This is the kind of check a data team adds when
a number "looks funny" and they want a permanent regression test for it.
"""

from __future__ import annotations

import duckdb
import pytest

from src.config import load_config, resolve_path

pytestmark = pytest.mark.skipif(
    not resolve_path("artifacts/warehouse.duckdb").exists(),
    reason="Warehouse not found — run `make build` first.",
)


@pytest.fixture(scope="module")
def con():
    config = load_config()
    warehouse_path = resolve_path(config["warehouse"]["path"])
    connection = duckdb.connect(str(warehouse_path), read_only=True)
    yield connection
    connection.close()


def _table_exists(con, schema: str, table: str) -> bool:
    result = con.execute(
        "select count(*) from information_schema.tables "
        "where table_schema = ? and table_name = ?",
        [schema, table],
    ).fetchone()[0]
    return result > 0


@pytest.mark.parametrize(
    "table",
    ["dim_customers", "dim_products", "dim_date", "fct_order_items",
     "mart_monthly_revenue", "mart_category_performance", "mart_delivery_performance"],
)
def test_mart_table_exists(con, table):
    assert _table_exists(con, "marts", table), f"Missing marts.{table}"


def test_fct_order_items_no_orphan_orders(con):
    """Every order_id in the fact table should exist in staging orders."""
    orphans = con.execute(
        """
        select count(*) from marts.fct_order_items f
        left join staging.stg_orders o on f.order_id = o.order_id
        where o.order_id is null
        """
    ).fetchone()[0]
    assert orphans == 0


def test_monthly_revenue_totals_are_positive(con):
    df = con.execute("select total_revenue, n_orders from marts.mart_monthly_revenue").df()
    assert (df["total_revenue"] > 0).all()
    assert (df["n_orders"] > 0).all()


def test_monthly_revenue_sum_matches_headline_total(con):
    """The sum of monthly revenue should equal the total computed independently
    from delivered order items — catches double-counting or filter bugs."""
    monthly_sum = con.execute("select sum(total_revenue) from marts.mart_monthly_revenue").fetchone()[0]

    independent_total = con.execute(
        """
        select sum(order_value) from (
            select order_id, sum(item_price + freight_value) as order_value
            from marts.fct_order_items
            where order_status = 'delivered'
            group by order_id
        )
        """
    ).fetchone()[0]

    assert abs(float(monthly_sum) - float(independent_total)) < 0.01


def test_category_performance_no_duplicate_categories(con):
    total = con.execute("select count(*) from marts.mart_category_performance").fetchone()[0]
    distinct = con.execute("select count(distinct category) from marts.mart_category_performance").fetchone()[0]
    assert total == distinct


def test_delivery_performance_percentages_in_valid_range(con):
    df = con.execute("select pct_late_deliveries from marts.mart_delivery_performance").df()
    assert (df["pct_late_deliveries"] >= 0).all()
    assert (df["pct_late_deliveries"] <= 100).all()


def test_dim_customers_unique_ids(con):
    total = con.execute("select count(*) from marts.dim_customers").fetchone()[0]
    distinct = con.execute("select count(distinct customer_unique_id) from marts.dim_customers").fetchone()[0]
    assert total == distinct


def test_no_negative_prices_in_fact_table(con):
    negative_count = con.execute(
        "select count(*) from marts.fct_order_items where item_price < 0 or freight_value < 0"
    ).fetchone()[0]
    assert negative_count == 0
