"""
Register a manually downloaded PhishTank feed file into the raw data store.

Why this exists
---------------
PhishTank's keyless download allowance is "a few downloads per day", and requests
are sometimes met with a Cloudflare 403. Since new account registration is
disabled, an application key cannot currently be obtained. When the automated
path in acquire_phishtank.py fails, downloading the feed in a browser is a
legitimate fallback.

What matters for the research record is provenance, not the transport. This
script gives a browser-downloaded file exactly the same provenance sidecar that
acquire_phishtank.py produces, so the two acquisition routes are equivalent
evidence and the acquisition remains auditable.

How to use
----------
1. In a browser, open one of the official feed URLs (see the Format Options table
   at https://phishtank.org/developer_info.php), for example:

       http://data.phishtank.com/data/online-valid.csv.gz

2. Note the time you downloaded it.

3. Register the file:

       python scripts/register_manual_download.py --file ~/Downloads/online-valid.csv.gz

   Optionally record the exact source URL and download time:

       python scripts/register_manual_download.py \
           --file ~/Downloads/online-valid.csv.gz \
           --source-url http://data.phishtank.com/data/online-valid.csv.gz \
           --downloaded-at 2026-08-16T09:30:00+00:00

The original file is COPIED (not moved) into data/raw/phishtank/ under a
timestamped name, leaving your download untouched. Existing raw files are never
overwritten.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import bz2
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from acquisition_common import (  # noqa: E402
    human_size,
    raw_dir,
    refuse_overwrite,
    sha256_file,
    utc_now_iso,
    utc_stamp,
    write_metadata,
)

EXPECTED_HEADER = [
    "phish_id",
    "url",
    "phish_detail_url",
    "submission_time",
    "verified",
    "verification_time",
    "online",
    "target",
]

OFFICIAL_HOSTS = ("data.phishtank.com",)


def open_text(path: Path):
    """Open a plain, gzip- or bzip2-compressed text file."""
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    if path.suffix == ".bz2":
        return bz2.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def verify_feed(path: Path) -> dict[str, object]:
    """Confirm the file really is a PhishTank online-valid CSV feed.

    A browser download can silently be an HTML error page or a Cloudflare
    challenge saved with a .csv name, so the content is checked rather than
    trusted.
    """
    result: dict[str, object] = {"verified_as_phishtank_csv": False}

    try:
        with open_text(path) as handle:
            first = handle.readline().strip()
            if first.lower().startswith(("<!doctype", "<html")):
                result["problem"] = (
                    "File starts with HTML, not CSV. This is almost certainly a "
                    "Cloudflare challenge or error page rather than the feed. "
                    "Open the URL in a browser and confirm a file downloads."
                )
                return result

            header = next(csv.reader([first]), [])
            result["header_found"] = header

            missing = [column for column in EXPECTED_HEADER if column not in header]
            if missing:
                result["problem"] = (
                    f"Header does not match the documented PhishTank feed. "
                    f"Missing columns: {missing}"
                )
                return result

            rows = 0
            for _ in handle:
                rows += 1
            result["data_rows"] = rows
            result["verified_as_phishtank_csv"] = True
            if rows == 0:
                result["problem"] = "Header is correct but the file contains no data rows."
    except Exception as error:  # noqa: BLE001
        result["problem"] = f"Could not read the file: {error}"

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--file", required=True, help="path to the manually downloaded feed file")
    parser.add_argument(
        "--source-url",
        default="http://data.phishtank.com/data/online-valid.csv.gz",
        help="the exact URL the file was downloaded from",
    )
    parser.add_argument(
        "--downloaded-at",
        default=None,
        help="ISO 8601 time of download, e.g. 2026-08-16T09:30:00+00:00 (default: registration time)",
    )
    parser.add_argument(
        "--allow-unverified",
        action="store_true",
        help="register the file even if the feed structure check fails",
    )
    args = parser.parse_args()

    source = Path(args.file).expanduser().resolve()
    if not source.is_file():
        print(f"No such file: {source}", file=sys.stderr)
        return 1

    if not any(host in args.source_url for host in OFFICIAL_HOSTS):
        print(
            f"WARNING: --source-url does not point at {OFFICIAL_HOSTS[0]}.\n"
            "         Only the official PhishTank feed host should be recorded as the source.",
            file=sys.stderr,
        )

    print(f"Registering  : {source}")
    print(f"Size         : {human_size(source.stat().st_size)}")

    verification = verify_feed(source)
    if verification.get("verified_as_phishtank_csv"):
        print(f"Structure    : OK, {verification['data_rows']:,} data rows")
    else:
        print(f"Structure    : FAILED — {verification.get('problem')}", file=sys.stderr)
        if not args.allow_unverified:
            print(
                "\nNot registered. Fix the download, or re-run with --allow-unverified "
                "if you are deliberately registering a non-CSV format.",
                file=sys.stderr,
            )
            return 1
        print("Registering anyway because --allow-unverified was given.", file=sys.stderr)

    destination_dir = raw_dir("phishtank")
    suffix = "".join(source.suffixes[-2:]) if source.suffixes[-1:] in ([".gz"], [".bz2"]) else source.suffix
    destination = destination_dir / f"online-valid_{utc_stamp()}{suffix}"

    try:
        refuse_overwrite(destination)
    except FileExistsError as error:
        print(f"\nABORTED: {error}", file=sys.stderr)
        return 1

    shutil.copy2(source, destination)
    checksum = sha256_file(destination)

    metadata = {
        "source_name": "PhishTank",
        "source_operator": "Cisco Talos Intelligence Group",
        "source_homepage": "https://phishtank.org/",
        "documentation_url": "https://phishtank.org/developer_info.php",
        "outcome": "success",
        "acquisition_method": "manual browser download, registered by script",
        "acquisition_method_reason": (
            "Keyless automated download is limited to a few requests per day and is "
            "subject to Cloudflare challenges. New application keys cannot currently "
            "be obtained because PhishTank registration is disabled."
        ),
        "feed_name": "online-valid (verified and currently online phishes)",
        "request_url": args.source_url,
        "downloaded_at_utc": args.downloaded_at or utc_now_iso(),
        "registered_at_utc": utc_now_iso(),
        "app_key_used": False,
        "data_format": "csv",
        "documented_fields": EXPECTED_HEADER,
        "documented_update_frequency": "hourly, on the hour",
        "version_information": (
            "PhishTank does not version this feed. ETag and Last-Modified are not "
            "available for a manual download; the snapshot is identified by the "
            "download time and the SHA-256 below."
        ),
        "structure_verification": verification,
        "original_local_path": str(source),
        "raw_filename": destination.name,
        "raw_file_bytes": destination.stat().st_size,
        "raw_file_sha256": checksum,
        "licence_note": "Use governed by PhishTank / Cisco terms of use. Free for research use.",
    }
    write_metadata(destination_dir, destination.name, metadata)

    print(f"\nOK. Registered as {destination.name}")
    print(f"SHA-256      : {checksum}")
    print("\nRecord this in the acquisition log (§6) of docs/DATASET_SOURCES.md.")
    print("Next: python scripts/inspect_datasets.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
