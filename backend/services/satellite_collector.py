"""
MOSDAC Satellite Data Collector — Real ISRO integration.

Uses the official MOSDAC mdapi.py client to download:
- GSMaP_ISRO: ISRO-JAXA rainfall (0.1° hourly)
- 3RIMG_L2B_LST: INSAT-3D Land Surface Temperature
- 3RIMG_L2B_IMC: Cloud/hydro-estimator QPE

Reference: https://mosdac.gov.in/downloadapi-manual
"""

import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import httpx

MOSDAC_API_BASE = "https://mosdac.gov.in"
MOSDAC_SIGNUP_URL = "https://mosdac.gov.in/signup/"
MOSDAC_MDAPI_URL = "https://mosdac.gov.in/software/mdapi.zip"

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "satellite"

# Available MOSDAC datasets for mosquito prediction
DATASETS = {
    "GSMaP_ISRO": "ISRO-JAXA GSMaP rainfall (0.1° hourly over India)",
    "3RIMG_L2B_LST": "INSAT-3D Land Surface Temperature (4km, 30-min)",
    "3RIMG_L2B_IMC": "INSAT-3D Cloud/hydro-estimator QPE (4km, 30-min)",
}


def build_mosdac_config(
    dataset_id: str,
    bbox: tuple[float, float, float, float],
    start_time: str,
    end_time: str,
    username: str,
    password: str,
    download_path: str,
    count: int = 50,
) -> dict:
    """Build MOSDAC mdapi config.json structure.

    bbox format for MOSDAC: minLon,minLat,maxLon,maxLat
    """
    w, s, e, n = bbox
    return {
        "user_credentials": {"username": username, "password": password},
        "search_parameters": {
            "datasetId": dataset_id,
            "startTime": start_time,
            "endTime": end_time,
            "count": str(count),
            "boundingBox": f"{w},{s},{e},{n}",
            "gId": "",
        },
        "download_settings": {
            "download_path": download_path,
            "organize_by_ate": True,
            "skip_user_prompt": True,
            "generate_error_log": True,
            "error_log_path": str(OUTPUT_DIR / "logs"),
        },
    }


def download_mosdac_data(
    dataset_id: str = "GSMaP_ISRO",
    days: int = 7,
    bbox: Optional[tuple[float, float, float, float]] = None,
    mdapi_path: Optional[str] = None,
) -> dict:
    """
    Download data from MOSDAC using the official mdapi.py client.

    Returns dict with status and downloaded file paths.
    Raises detailed error if credentials or mdapi.py are missing.
    """
    username = os.getenv("MOSDAC_USERNAME", "")
    password = os.getenv("MOSDAC_PASSWORD", "")
    mdapi_path = mdapi_path or os.getenv("MOSDAC_MDAPI_PATH", "")

    if not username or not password:
        return {
            "status": "error",
            "message": (
                "MOSDAC credentials not configured. "
                "1. Register at https://mosdac.gov.in/signup/ "
                "2. Set MOSDAC_USERNAME and MOSDAC_PASSWORD in .env"
            ),
            "signup_url": MOSDAC_SIGNUP_URL,
        }

    if not mdapi_path or not Path(mdapi_path).exists():
        return {
            "status": "error",
            "message": (
                "MOSDAC mdapi.py not found. "
                "1. Download from https://mosdac.gov.in/software/mdapi.zip "
                "2. Unzip and set MOSDAC_MDAPI_PATH in .env"
            ),
            "download_url": MOSDAC_MDAPI_URL,
        }

    if bbox is None:
        bbox = (
            float(os.getenv("SADAR_CANTT_BBOX_WEST", "80.90")),
            float(os.getenv("SADAR_CANTT_BBOX_SOUTH", "26.80")),
            float(os.getenv("SADAR_CANTT_BBOX_EAST", "81.00")),
            float(os.getenv("SADAR_CANTT_BBOX_NORTH", "26.90")),
        )

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    download_dir = str(OUTPUT_DIR / dataset_id)
    config = build_mosdac_config(
        dataset_id=dataset_id,
        bbox=bbox,
        start_time=start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        end_time=end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        username=username,
        password=password,
        download_path=download_dir,
    )

    config_path = OUTPUT_DIR / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2))

    try:
        result = subprocess.run(
            ["python", mdapi_path],
            cwd=str(Path(mdapi_path).parent),
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            return {
                "status": "error",
                "message": f"mdapi.py failed: {result.stderr[:500]}",
                "config_path": str(config_path),
            }

        downloaded = list(Path(download_dir).rglob("*.h5")) + list(
            Path(download_dir).rglob("*.nc")
        )
        return {
            "status": "success",
            "dataset": dataset_id,
            "files_downloaded": len(downloaded),
            "file_paths": [str(f) for f in downloaded],
            "config_path": str(config_path),
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "MOSDAC download timed out (300s)"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_live_satellite_status() -> dict:
    """Check MOSDAC API availability and return dataset info."""
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(f"{MOSDAC_API_BASE}/thredds/catalog.xml")
            mosdac_available = resp.status_code == 200
    except Exception:
        mosdac_available = False

    username = os.getenv("MOSDAC_USERNAME", "")
    return {
        "mosdac_api_available": mosdac_available,
        "credentials_configured": bool(username),
        "available_datasets": DATASETS,
        "signup_url": MOSDAC_SIGNUP_URL,
        "mdapi_download": MOSDAC_MDAPI_URL,
        "bounding_box": {
            "south": float(os.getenv("SADAR_CANTT_BBOX_SOUTH", "26.80")),
            "north": float(os.getenv("SADAR_CANTT_BBOX_NORTH", "26.90")),
            "west": float(os.getenv("SADAR_CANTT_BBOX_WEST", "80.90")),
            "east": float(os.getenv("SADAR_CANTT_BBOX_EAST", "81.00")),
        },
    }
