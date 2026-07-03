"""
MOSDAC Satellite Collector — Module 1.

Downloads GSMaP_ISRO rainfall, LST, vegetation from ISRO MOSDAC API.
ISRO-JAXA joint product — see docs/RESEARCH_REFERENCES.md.

Usage:
    python satellite/collector/run_mosdac.py --dataset GSMaP_ISRO --days 7
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

MOSDAC_API_BASE = "https://mosdac.gov.in"
DEFAULT_DATASET = "GSMaP_ISRO"
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "satellite"


def build_search_config(
    dataset_id: str,
    bbox: str,
    start_time: str,
    end_time: str,
    username: str,
    password: str,
) -> dict:
    """Build MOSDAC mdapi config.json structure."""
    lat_min, lat_max, lon_min, lon_max = [float(x) for x in bbox.split(",")]
    return {
        "user_credentials": {"username": username, "password": password},
        "search_parameters": {
            "datasetId": dataset_id,
            "startTime": start_time,
            "endTime": end_time,
            "boundingBox": {
                "minLat": lat_min,
                "maxLat": lat_max,
                "minLon": lon_min,
                "maxLon": lon_max,
            },
            "count": 100,
        },
        "download_options": {"output_dir": str(OUTPUT_DIR / dataset_id)},
    }


def download_mosdac(config: dict) -> dict:
    """
    Invoke MOSDAC search API.
    Production: use official mdapi.py client from mosdac.gov.in/software/mdapi.zip
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config_path = OUTPUT_DIR / "config.json"
    config_path.write_text(json.dumps(config, indent=2))

    # Placeholder search — replace with mdapi.py subprocess in production
    return {
        "status": "configured",
        "config_path": str(config_path),
        "message": "Run mdapi.py with generated config or integrate mdapi as library",
    }


def main():
    parser = argparse.ArgumentParser(description="MOSDAC satellite data collector")
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--bbox", default=os.getenv("MOSDAC_BOUNDING_BOX", "26.7,26.95,80.8,81.1"))
    args = parser.parse_args()

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=args.days)

    config = build_search_config(
        dataset_id=args.dataset,
        bbox=args.bbox,
        start_time=start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        end_time=end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        username=os.getenv("MOSDAC_USERNAME", ""),
        password=os.getenv("MOSDAC_PASSWORD", ""),
    )
    result = download_mosdac(config)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
