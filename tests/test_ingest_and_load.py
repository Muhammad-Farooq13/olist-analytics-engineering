"""Tests for data ingestion and raw layer loading."""

from __future__ import annotations

import duckdb
import pytest

from src.config import load_config, resolve_path

pytestmark = pytest.mark.skipif(
    not resolve_path("data/raw/olist_orders_dataset.csv").exists(),
    reason="Raw data not found — run `make ingest` first.",
)


@pytest.fixture(scope="module")
def config():
    return load_config()


def test_raw_files_exist(config):
    source_cfg = config["source"]
    raw_dir = resolve_path(source_cfg["raw_dir"])
    for filename in source_cfg["files"].values():
        assert (raw_dir / filename).exists(), f"Missing {filename}"


def test_raw_files_nonempty(config):
    source_cfg = config["source"]
    raw_dir = resolve_path(source_cfg["raw_dir"])
    for filename in source_cfg["files"].values():
        path = raw_dir / filename
        assert path.stat().st_size > 0


@pytest.fixture(scope="module")
def warehouse_con(config):
    warehouse_path = resolve_path(config["warehouse"]["path"])
    if not warehouse_path.exists():
        pytest.skip("Warehouse not built — run `make load` first.")
    con = duckdb.connect(str(warehouse_path), read_only=True)
    yield con
    con.close()


def test_raw_orders_row_count(warehouse_con):
    count = warehouse_con.execute("select count(*) from raw.raw_orders").fetchone()[0]
    assert count > 90000  # real dataset has 99,441 orders


def test_raw_tables_all_present(warehouse_con, config):
    tables = warehouse_con.execute(
        "select table_name from information_schema.tables where table_schema = 'raw'"
    ).fetchall()
    table_names = {t[0] for t in tables}
    for table_name in config["source"]["files"]:
        assert f"raw_{table_name}" in table_names
