# Schneider Electric SNMP DDF Downloader

Downloads Schneider Electric SNMP Device Definition Files (DDFs) from the EcoStruxure IT DDF API and keeps a local `ddf_files` directory up to date.

## What This Project Does

This script pulls the public SNMP DDF catalog from:

- `https://ddf.ecostruxureit.com/ddfsearchapi/ddfSearch?search=*snmp*&size=9999&startingIndex=0`

Then it:

- Saves a downloaded manifest snapshot as `ddf_files/ddf_manifest_download.json`.
- Downloads XML files into folders by state (for example `ddf_files/provided`, `ddf_files/unverified`, `ddf_files/verified`).
- Promotes the downloaded manifest to `ddf_files/ddf_manifest.json` once processing completes.

## Requirements

- Python 3.10+
- Internet access to `ddf.ecostruxureit.com`
- Dependency:
	- `requests`

## Installation

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies.

Example:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run from the repository root.

### Incremental Sync (default)

Downloads only new or changed DDF files when a local `ddf_files/ddf_manifest.json` already exists.

```bash
python ddf_scrape.py
```

### Full Sync

Downloads every DDF file in the current remote manifest.

```bash
python ddf_scrape.py --full
```

## Output Summary

The script prints a completion summary:

- Full sync: number of DDF files downloaded.
- Incremental sync: number of changed/new files downloaded and unchanged files skipped.
- If individual DDF downloads fail (for example due to upstream 5xx errors), the run continues and reports failed filenames at the end.

Exit codes:

- `0`: successful run with no per-file download failures.
- `1`: fatal network/API or local processing error (run aborted).
- `2`: sync completed, but one or more individual DDF files failed to download.

## Project Structure

- `ddf_scrape.py`: main sync script.
- `requirements.txt`: Python dependencies.
- `ddf_files/ddf_manifest.json`: active local manifest used for version comparison.
- `ddf_files/ddf_manifest_download.json`: temporary downloaded manifest for the current run.
- `ddf_files/<state>/*.xml`: downloaded DDF files grouped by state.

## How Incremental Updates Work

1. Current local manifest is loaded.
2. Latest remote manifest is downloaded.
3. For each remote DDF entry:
	 - If `fileName` exists locally and `ddfVersion` is unchanged, it is skipped.
	 - If new or version changed, the file is downloaded.
4. The active local manifest is replaced with the newly downloaded manifest.

## Troubleshooting

- If downloads fail due to connectivity issues, retry when network access is available.
- If you suspect local files are out of sync, run a full sync with `--full`.
- If dependencies are missing, reinstall with `pip install -r requirements.txt`.

## Notes

- This repository stores downloaded DDF content under `ddf_files`.
- API response schema and available DDF states are controlled by Schneider Electric.
