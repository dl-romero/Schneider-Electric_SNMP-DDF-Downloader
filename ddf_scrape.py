import argparse
import json
from pathlib import Path

import requests


DDF_SEARCH_URL = "https://ddf.ecostruxureit.com/ddfsearchapi/ddfSearch?search=*snmp*&size=9999&startingIndex=0"
DDF_DOWNLOAD_URL = "https://ddf.ecostruxureit.com/ddfsearchapi/ddf/{ddf_id}/download"
REQUEST_TIMEOUT_SECONDS = 60

BASE_DIR = Path(__file__).resolve().parent
DDF_DIR = BASE_DIR / "ddf_files"
MANIFEST_PATH = DDF_DIR / "ddf_manifest.json"
DOWNLOADED_MANIFEST_PATH = DDF_DIR / "ddf_manifest_download.json"


def download_ddf(
    session: requests.Session,
    ddf_id: int,
    ddf_filename: str,
    ddf_state: str,
) -> tuple[bool, str | None]:
    """Download an individual DDF file into its state folder."""
    try:
        url = DDF_DOWNLOAD_URL.format(ddf_id=ddf_id)
        response = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS, allow_redirects=True)
        response.raise_for_status()

        state_dir = DDF_DIR / str(ddf_state).lower()
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / str(ddf_filename)).write_bytes(response.content)
        return True, None
    except (requests.RequestException, OSError) as exc:
        return False, str(exc)


def fetch_ddf_list(session: requests.Session) -> list[dict]:
    """Get the full SNMP DDF manifest and cache the downloaded copy."""
    response = session.get(DDF_SEARCH_URL, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    ddf_list = response.json()
    if not isinstance(ddf_list, list):
        raise ValueError("Unexpected API response format for DDF manifest.")

    DDF_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOADED_MANIFEST_PATH.write_text(
        json.dumps(ddf_list, indent=2),
        encoding="utf-8",
    )
    return ddf_list


def finalize_manifest() -> None:
    """Replace the active manifest with the latest downloaded manifest."""
    if not DOWNLOADED_MANIFEST_PATH.exists():
        raise FileNotFoundError("Downloaded manifest was not found.")

    if MANIFEST_PATH.exists():
        MANIFEST_PATH.unlink()

    DOWNLOADED_MANIFEST_PATH.rename(MANIFEST_PATH)


def process_new(session: requests.Session) -> tuple[int, int, list[str]]:
    """Download every DDF in the current manifest."""
    ddf_list = fetch_ddf_list(session)
    downloaded_count = 0
    skipped_count = 0
    failed_downloads: list[str] = []

    for ddf in ddf_list:
        ddf_id = ddf.get("id")
        ddf_filename = ddf.get("fileName")
        ddf_state = ddf.get("ddfState")

        if ddf_id is None or not ddf_filename or not ddf_state:
            skipped_count += 1
            continue

        success, error_message = download_ddf(session, ddf_id, ddf_filename, ddf_state)
        if success:
            downloaded_count += 1
        else:
            failed_downloads.append(f"{ddf_filename}: {error_message}")

    finalize_manifest()
    return downloaded_count, skipped_count, failed_downloads


def process_upgrade(session: requests.Session) -> tuple[int, int, list[str]]:
    """Update changed or new DDF files based on version changes."""
    with MANIFEST_PATH.open(encoding="utf-8") as existing_manifest:
        existing_ddf_manifest = json.load(existing_manifest)

    existing_versions = {
        str(existing_ddf.get("fileName")): str(existing_ddf.get("ddfVersion"))
        for existing_ddf in existing_ddf_manifest
        if existing_ddf.get("fileName")
    }

    ddf_list = fetch_ddf_list(session)
    downloaded_count = 0
    skipped_count = 0
    failed_downloads: list[str] = []

    for ddf in ddf_list:
        ddf_id = ddf.get("id")
        ddf_filename = ddf.get("fileName")
        ddf_state = ddf.get("ddfState")
        ddf_version = str(ddf.get("ddfVersion"))

        if ddf_id is None or not ddf_filename or not ddf_state:
            skipped_count += 1
            continue

        if existing_versions.get(str(ddf_filename)) == ddf_version:
            skipped_count += 1
            continue

        success, error_message = download_ddf(session, ddf_id, ddf_filename, ddf_state)
        if success:
            downloaded_count += 1
        else:
            failed_downloads.append(f"{ddf_filename}: {error_message}")

    finalize_manifest()
    return downloaded_count, skipped_count, failed_downloads


def main() -> int:
    parser = argparse.ArgumentParser(description="Download Schneider Electric SNMP DDF files.")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Download all DDF files instead of only changed/new ones.",
    )
    args = parser.parse_args()

    DDF_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with requests.Session() as session:
            if args.full or not MANIFEST_PATH.exists():
                downloaded, skipped, failures = process_new(session)
                print(
                    "Full sync complete. "
                    f"Downloaded {downloaded} DDF files; skipped {skipped} invalid entries."
                )
            else:
                downloaded, skipped, failures = process_upgrade(session)
                print(
                    "Incremental sync complete. "
                    f"Downloaded {downloaded} changed/new DDF files; skipped {skipped} unchanged entries."
                )

            if failures:
                print(f"Encountered {len(failures)} download failure(s):")
                for failure in failures[:10]:
                    print(f"- {failure}")
                if len(failures) > 10:
                    print(f"- ...and {len(failures) - 10} more failure(s).")
                return 2
    except requests.RequestException as exc:
        print(f"Network/API error while downloading DDFs: {exc}")
        return 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Local processing error while updating DDF files: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
