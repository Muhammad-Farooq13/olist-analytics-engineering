"""Tests for the business metrics export."""

from __future__ import annotations

import json

import duckdb
import pytest

from src.config import load_config, resolve_path
from src.export_metrics import compute_headline_metrics

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


def test_compute_headline_metrics_shape(con):
    metrics = compute_headline_metrics(con)
    expected_keys = {
        "total_revenue", "total_delivered_orders", "average_order_value",
        "top_category_by_revenue", "top_category_revenue",
        "weighted_avg_delivery_days", "weighted_pct_late_deliveries",
        "n_months_of_data", "n_categories", "n_unique_customers",
    }
    assert expected_keys.issubset(metrics.keys())


def test_compute_headline_metrics_values_are_sane(con):
    metrics = compute_headline_metrics(con)
    assert metrics["total_revenue"] > 0
    assert metrics["total_delivered_orders"] > 0
    assert 0 < metrics["average_order_value"] < 10000
    assert 0 <= metrics["weighted_pct_late_deliveries"] <= 100
    assert metrics["n_unique_customers"] > 0


def test_compute_headline_metrics_json_serializable(con):
    metrics = compute_headline_metrics(con)
    # should not raise — catches Decimal/serialization regressions
    json.dumps(metrics)


def test_metrics_file_matches_computed_values(con):
    config = load_config()
    metrics_path = resolve_path(config["metrics"]["output_path"])
    if not metrics_path.exists():
        pytest.skip("Metrics file not exported yet — run `make metrics` first.")

    with open(metrics_path, "r", encoding="utf-8") as f:
        saved = json.load(f)

    fresh = compute_headline_metrics(con)
    assert saved["total_revenue"] == fresh["total_revenue"]
    assert saved["top_category_by_revenue"] == fresh["top_category_by_revenue"]
