"""
Acquire candidate Kaggle phishing email datasets.

Approved email data source strategy for FYP2: a suitable public Kaggle
phishing email dataset. Two candidates are acquired for inspection before a
primary dataset is selected. The datasets are kept SEPARATE and are not
merged, cleaned or preprocessed at this stage.

Candidates
----------
1. naserabdullahalam/phishing-email-dataset
   "Phish No More: The Enron, Ling, CEAS, Nazario, Nigerian & SpamAssassin Datasets"
   https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset

2. subhajournal/phishingemails
   "Phishing Email Detection - Detecting Phishing Emails by Text Analytics"
   https://www.kaggle.com/datasets/subhajournal/phishingemails

Credentials
-----------
No credentials are hard-coded. The Kaggle API reads either:

  (a) a credentials file at ~/.config/kaggle/kaggle.json (kaggle >= 1.7) or the
      legacy ~/.kaggle/kaggle.json — both are accepted; chmod 600, or
  (b) environment variables KAGGLE_USERNAME and KAGGLE_KEY

Note: the kaggle package authenticates when it is IMPORTED, so missing
credentials raise an OSError before any function in this file runs. That case is
caught in authenticate() and reported with actionable guidance.

Obtain kaggle.json from https://www.kaggle.com/settings -> API -> Create New Token.

In Google Colab, prefer Colab Secrets:

    from google.colab import userdata
    import os
    os.environ["KAGGLE_USERNAME"] = userdata.get("KAGGLE_USERNAME")
    os.environ["KAGGLE_KEY"] = userdata.get("KAGGLE_KEY")

Usage
-----
    pip install -r scripts/requirements-acquisition.txt
    python scripts/acquire_kaggle.py
    python scripts/acquire_kaggle.py --only subhajournal

Output
------
    data/raw/kaggle/<owner>/<original archive .zip>
    data/raw/kaggle/<owner>/<extracted original files>
    data/raw/kaggle/<owner>/<slug>.metadata.json

The downloaded archive is preserved alongside the extracted files. Extracted
files keep their original Kaggle filenames and contents; nothing is modified.
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from acquisition_common import (  # noqa: E402
    human_size,
    raw_dir,
    sha256_file,
    utc_now_iso,
    utc_stamp,
    write_metadata,
)

CANDIDATES: dict[str, dict[str, str]] = {
    "naserabdullahalam": {
        "slug": "naserabdullahalam/phishing-email-dataset",
        "title": "Phishing Email Dataset",
        "url": "https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset",
        "note": (
            "Aggregates Enron, Ling, CEAS_08, Nazario, Nigerian Fraud and SpamAssassin. "
            "Associated publication: Champa, Rabbi, Zibran et al., 'Curated Datasets and "
            "Feature Analysis for Phishing Email Detection with Machine Learning', "
            "IEEE ICMI 2024."
        ),
    },
    "subhajournal": {
        "slug": "subhajournal/phishingemails",
        "title": "Phishing Email Detection",
        "url": "https://www.kaggle.com/datasets/subhajournal/phishingemails",
        "note": "Two-column text dataset (email body text and email type label).",
    },
}


def authenticate():
    """Authenticate against the Kaggle API using file or environment credentials."""
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        print(
            "The 'kaggle' package is not installed.\n"
            "Install it first:  pip install -r scripts/requirements-acquisition.txt",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
    except OSError as error:
        # The kaggle package authenticates at IMPORT time, so a missing
        # credentials file surfaces here rather than at api.authenticate().
        print(
            "Kaggle credentials were not found at import time.\n"
            "Provide them by either:\n"
            "  * placing kaggle.json in ~/.config/kaggle/ (or ~/.kaggle/), chmod 600, or\n"
            "  * setting KAGGLE_USERNAME and KAGGLE_KEY in the environment.\n"
            "Get kaggle.json from https://www.kaggle.com/settings -> API -> Create New Token.\n"
            f"Underlying error: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1) from None

    api = KaggleApi()
    try:
        api.authenticate()
    except Exception as error:  # noqa: BLE001 - surface the real cause to the user
        print(
            "Kaggle authentication failed. Provide credentials via ~/.kaggle/kaggle.json "
            "or the KAGGLE_USERNAME / KAGGLE_KEY environment variables.\n"
            f"Underlying error: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
    return api


def collect_remote_metadata(api, slug: str) -> dict[str, Any]:
    """Query Kaggle for file listing and version information.

    Any field the API does not return is recorded as None rather than guessed.
    """
    remote: dict[str, Any] = {"listed_files": None, "version_number": None, "last_updated": None}

    try:
        listing = api.dataset_list_files(slug)
        remote["listed_files"] = [
            {"name": f.name, "size_bytes": getattr(f, "totalBytes", None)} for f in listing.files
        ]
    except Exception as error:  # noqa: BLE001
        remote["listed_files_error"] = str(error)

    try:
        matches = api.dataset_list(search=slug.split("/")[1], user=slug.split("/")[0])
        for item in matches:
            if getattr(item, "ref", None) == slug:
                remote["version_number"] = getattr(item, "currentVersionNumber", None)
                last_updated = getattr(item, "lastUpdated", None)
                remote["last_updated"] = str(last_updated) if last_updated else None
                remote["total_bytes"] = getattr(item, "totalBytes", None)
                remote["licence"] = getattr(item, "licenseName", None)
                break
    except Exception as error:  # noqa: BLE001
        remote["version_lookup_error"] = str(error)

    return remote


def acquire(api, key: str, spec: dict[str, str]) -> dict[str, Any]:
    """Download one dataset archive and record provenance. Returns the metadata record."""
    slug = spec["slug"]
    destination_dir = raw_dir("kaggle", key)

    print(f"\n=== {slug} ===")
    print(f"Destination : {destination_dir}")

    requested_at = utc_now_iso()
    remote = collect_remote_metadata(api, slug)

    # unzip=False keeps the original archive as the preserved raw artefact.
    api.dataset_download_files(slug, path=str(destination_dir), unzip=False, quiet=False)

    archives = sorted(destination_dir.glob("*.zip"))
    if not archives:
        raise FileNotFoundError(f"No .zip archive found in {destination_dir} after download.")
    archive = max(archives, key=lambda p: p.stat().st_mtime)

    extracted: list[dict[str, Any]] = []
    with zipfile.ZipFile(archive) as zf:
        for member in zf.infolist():
            if member.is_dir():
                continue
            target = destination_dir / member.filename
            if target.exists():
                print(f"  skip (already present, not overwriting): {member.filename}")
            else:
                zf.extract(member, destination_dir)
                print(f"  extracted: {member.filename} ({human_size(member.file_size)})")
            extracted.append(
                {
                    "filename": member.filename,
                    "uncompressed_bytes": member.file_size,
                    "sha256": sha256_file(target) if target.exists() else None,
                }
            )

    record = {
        "source_name": "Kaggle",
        "dataset_identifier": slug,
        "dataset_owner": slug.split("/")[0],
        "dataset_title": spec["title"],
        "dataset_url": spec["url"],
        "selection_note": spec["note"],
        "outcome": "success",
        "requested_at_utc": requested_at,
        "completed_at_utc": utc_now_iso(),
        "remote_metadata": remote,
        "archive_filename": archive.name,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": sha256_file(archive),
        "extracted_files": extracted,
        "modification_note": "Archive preserved. Extracted files are unmodified originals.",
    }
    # Timestamped sidecar name: re-running the acquisition must never destroy the
    # provenance record of a previous run.
    write_metadata(destination_dir, f"{slug.replace('/', '__')}_{utc_stamp()}", record)
    print(f"  archive: {archive.name} ({human_size(archive.stat().st_size)})")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", choices=sorted(CANDIDATES), help="acquire a single candidate")
    args = parser.parse_args()

    selected = {args.only: CANDIDATES[args.only]} if args.only else CANDIDATES

    api = authenticate()
    print("Kaggle authentication OK.")

    failures = 0
    for key, spec in selected.items():
        try:
            acquire(api, key, spec)
        except Exception as error:  # noqa: BLE001
            failures += 1
            print(f"FAILED {spec['slug']}: {error}", file=sys.stderr)

    if failures:
        print(f"\n{failures} dataset(s) failed.", file=sys.stderr)
        return 1

    print("\nAll requested datasets acquired.")
    print("Next: python scripts/inspect_datasets.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
