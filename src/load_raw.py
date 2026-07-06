"""Load raw CSVs into a DuckDB warehouse under a `raw` schema.

This is the boundary between plain file ingestion and the dbt-managed
transformation layer: dbt's sources.yml points at exactly the tables created
here, so dbt never has to know how the raw data got into the warehouse — it
could just as easily be swapped for a real production loader (Fivetran,
Airbyte, a Kafka sink) without touching a single dbt model.

Run directly:
    python -m src.load_raw
"""

from __future__ import annotations

from typing import Any, Dict

import duckdb

from src.config import load_config, resolve_path
from src.logger import get_logger

logger = get_logger(__name__)


def load_raw_tables(config: Dict[str, Any]) -> None:
    """Load each configured raw CSV into a DuckDB table under the raw schema.

    Args:
        config: Full configuration dictionary.
    """
    source_cfg = config["source"]
    warehouse_cfg = config["warehouse"]

    raw_dir = resolve_path(source_cfg["raw_dir"])
    warehouse_path = resolve_path(warehouse_cfg["path"])
    warehouse_path.parent.mkdir(parents=True, exist_ok=True)
    schema = warehouse_cfg["raw_schema"]

    con = duckdb.connect(str(warehouse_path))
    try:
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

        for table_name, filename in source_cfg["files"].items():
            csv_path = raw_dir / filename
            if not csv_path.exists():
                raise FileNotFoundError(f"Missing raw file: {csv_path}. Run `make ingest` first.")

            qualified_name = f"{schema}.raw_{table_name}"
            con.execute(
                f"CREATE OR REPLACE TABLE {qualified_name} AS "
                f"SELECT * FROM read_csv_auto(?, header=True, sample_size=-1)",
                [str(csv_path)],
            )
            row_count = con.execute(f"SELECT COUNT(*) FROM {qualified_name}").fetchone()[0]
            logger.info("Loaded %s: %d rows", qualified_name, row_count)
    finally:
        con.close()

    logger.info("Raw layer loaded into %s", warehouse_path)


def main() -> None:
    config = load_config()
    load_raw_tables(config)


if __name__ == "__main__":
    main()
