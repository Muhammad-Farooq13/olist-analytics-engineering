"""Raw CSV ingestion for the Olist e-commerce dataset.

Downloads the real Olist tables (see data/README.md for provenance and
license — CC BY-NC-SA 4.0, non-commercial use). Run directly:

    python -m src.ingest
"""

from __future__ import annotations

from typing import Any, Dict, List

import requests

from src.config import load_config, resolve_path
from src.logger import get_logger

logger = get_logger(__name__)


def download_raw_files(config: Dict[str, Any]) -> List[str]:
    """Download all configured raw CSV files if not already present.

    Args:
        config: Full configuration dictionary.

    Returns:
        List of local file paths that were downloaded or already existed.
    """
    source_cfg = config["source"]
    raw_dir = resolve_path(source_cfg["raw_dir"])
    raw_dir.mkdir(parents=True, exist_ok=True)

    base_url = source_cfg["base_url"]
    saved_paths: List[str] = []

    for table_name, filename in source_cfg["files"].items():
        local_path = raw_dir / filename
        if local_path.exists():
            logger.info("Already present, skipping: %s", filename)
            saved_paths.append(str(local_path))
            continue

        url = f"{base_url}/{filename}"
        logger.info("Downloading %s (%s)", filename, table_name)
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        local_path.write_bytes(response.content)
        saved_paths.append(str(local_path))

    logger.info("Ingestion complete: %d files in %s", len(saved_paths), raw_dir)
    return saved_paths


def main() -> None:
    config = load_config()
    download_raw_files(config)


if __name__ == "__main__":
    main()
