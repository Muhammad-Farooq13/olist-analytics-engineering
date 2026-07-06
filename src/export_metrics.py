"""Export headline business metrics and charts from the dbt marts.

This is the "so what" layer on top of the warehouse — the numbers and charts
a stakeholder would actually see, computed directly from the marts dbt just
built (not recomputed independently, so there's exactly one source of truth
for these figures).

Run directly:
    python -m src.export_metrics
"""

from __future__ import annotations

import json
from typing import Any, Dict

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from src.config import load_config, resolve_path
from src.logger import get_logger

logger = get_logger(__name__)


def compute_headline_metrics(con: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    """Compute headline business metrics from the marts layer."""
    revenue_row = con.execute(
        "select sum(total_revenue) as revenue, sum(n_orders) as orders "
        "from marts.mart_monthly_revenue"
    ).fetchone()
    total_revenue, total_orders = revenue_row

    aov = round(total_revenue / total_orders, 2) if total_orders else None

    top_category = con.execute(
        "select category, total_revenue from marts.mart_category_performance "
        "order by total_revenue desc limit 1"
    ).fetchone()

    delivery_row = con.execute(
        "select "
        "  round(sum(avg_delivery_days * n_orders) / sum(n_orders), 2) as weighted_avg_delivery_days, "
        "  round(100.0 * sum(pct_late_deliveries / 100.0 * n_orders) / sum(n_orders), 2) as weighted_pct_late "
        "from marts.mart_delivery_performance"
    ).fetchone()

    n_months = con.execute("select count(*) from marts.mart_monthly_revenue").fetchone()[0]
    n_categories = con.execute("select count(*) from marts.mart_category_performance").fetchone()[0]
    n_customers = con.execute("select count(*) from marts.dim_customers").fetchone()[0]

    return {
        "total_revenue": float(round(total_revenue, 2)),
        "total_delivered_orders": int(total_orders),
        "average_order_value": float(aov) if aov is not None else None,
        "top_category_by_revenue": top_category[0],
        "top_category_revenue": float(round(top_category[1], 2)),
        "weighted_avg_delivery_days": float(delivery_row[0]),
        "weighted_pct_late_deliveries": float(delivery_row[1]),
        "n_months_of_data": int(n_months),
        "n_categories": int(n_categories),
        "n_unique_customers": int(n_customers),
    }


def plot_monthly_revenue(con: duckdb.DuckDBPyConnection, out_path) -> None:
    """Plot monthly revenue trend."""
    df = con.execute(
        "select order_month, total_revenue from marts.mart_monthly_revenue order by order_month"
    ).df()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["order_month"], df["total_revenue"], marker="o", linewidth=1.5)
    ax.set_title("Monthly Revenue — Delivered Orders")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue (BRL)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_top_categories(con: duckdb.DuckDBPyConnection, out_path, top_n: int = 10) -> None:
    """Plot top N categories by revenue."""
    df = con.execute(
        f"select category, total_revenue from marts.mart_category_performance "
        f"order by total_revenue desc limit {top_n}"
    ).df()

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(df["category"][::-1], df["total_revenue"][::-1])
    ax.set_title(f"Top {top_n} Product Categories by Revenue")
    ax.set_xlabel("Revenue (BRL)")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main() -> None:
    config = load_config()
    warehouse_path = resolve_path(config["warehouse"]["path"])

    if not warehouse_path.exists():
        raise FileNotFoundError("Warehouse not found — run `make build` (ingest -> load -> dbt build) first.")

    con = duckdb.connect(str(warehouse_path), read_only=True)
    try:
        metrics = compute_headline_metrics(con)
        logger.info("Headline metrics: %s", json.dumps(metrics, indent=2))

        metrics_path = resolve_path(config["metrics"]["output_path"])
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        logger.info("Saved metrics to %s", metrics_path)

        revenue_chart_path = resolve_path(config["metrics"]["revenue_chart_path"])
        plot_monthly_revenue(con, revenue_chart_path)
        logger.info("Saved revenue chart to %s", revenue_chart_path)

        category_chart_path = resolve_path(config["metrics"]["category_chart_path"])
        plot_top_categories(con, category_chart_path)
        logger.info("Saved category chart to %s", category_chart_path)
    finally:
        con.close()


if __name__ == "__main__":
    main()
