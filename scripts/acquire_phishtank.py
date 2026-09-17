"""
Acquire the PhishTank verified-and-online phishing URL feed.

Approved primary URL data source for FYP2.

Official documentation
----------------------
Developer information : https://phishtank.org/developer_info.php
API information       : https://phishtank.org/api_info.php
Operated by           : Cisco Talos Intelligence Group

Feed characteristics (from the official developer page, verified 2026-08-13)
---------------------------------------------------------------------------
Contents      : verified AND currently online phishes only
Update period : hourly, on the hour
Formats       : CSV, JSON, XML, serialized PHP; each plain, .gz or .bz2
Fields        : phish_id, url, phish_detail_url, submission_time,
                verified, verification_time, online, target
User-Agent    : a descriptive User-Agent is REQUIRED, recommended form
                "phishtank/<username>"; blank or generic agents get
                additional rate limiting or security checks
App key       : optional in the URL path; without a key you are limited to
                "a few downloads per day". With a key, HEAD requests to
                check the ETag are unlimited.

Important limitation (verified 2026-08-13)
------------------------------------------
PhishTank new user registration is currently disabled, so a NEW application
key cannot be obtained. This script therefore defaults to the keyless feed
and will use a key only if one is supplied via the environment.

Credentials
-----------
No key is hard-coded. If you do have one, supply it as an environment
variable before running:

    export PHISHTANK_APP_KEY=...            # optional
    export PHISHTANK_USER_AGENT=phishtank/yourusername

Usage
-----
    python scripts/acquire_phishtank.py
    python scripts/acquire_phishtank.py --format json --compression gz

Output
------
    data/raw/phishtank/online-valid_<UTCSTAMP>.<ext>
    data/raw/phishtank/online-valid_<UTCSTAMP>.<ext>.metadata.json

The downloaded file is written byte-for-byte as received and is never
modified, decompressed in place, or cleaned by this script.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))

from acquisition_common import (  # noqa: E402
    get_secret,
    human_size,
    raw_dir,
    redact,
    refuse_overwrite,
    sha256_file,
    utc_now_iso,
    utc_stamp,
    write_metadata,
)

FEED_HOST = "http://data.phishtank.com/data"
FEED_BASENAME = "online-valid"
DEFAULT_USER_AGENT = "phishtank/fyp2-research-prototype"

# Documented field list for the online-valid feed. Recorded for provenance;
# the actual columns present are confirmed later by inspect_datasets.py.
DOCUMENTED_FIELDS = [
    "phish_id",
    "url",
    "phish_detail_url",
    "submission_time",
    "verified",
    "verification_time",
    "online",
    "target",
]


def build_feed_url(data_format: str, compression: str, app_key: str | None) -> str:
    """Construct the feed URL, inserting the application key path segment if present."""
    extension = data_format if compression == "none" else f"{data_format}.{compression}"
    if app_key:
        return f"{FEED_HOST}/{app_key}/{FEED_BASENAME}.{extension}"
    return f"{FEED_HOST}/{FEED_BASENAME}.{extension}"


def download(url: str, user_agent: str, timeout: int = 120) -> requests.Response:
    """Stream the feed. Raises requests.HTTPError on a non-2xx response."""
    response = requests.get(
        url,
        headers={"User-Agent": user_agent, "Accept-Encoding": "identity"},
        stream=True,
        timeout=timeout,
    )
    response.raise_for_status()
    return response


def explain_failure(status_code: int) -> str:
    """Return actionable guidance for the common PhishTank failure modes."""
    if status_code == 403:
        return (
            "403 Forbidden. This is the documented behaviour when the keyless "
            "download allowance is exhausted, or when Cloudflare interposes a "
            "challenge. Options: retry later from a different network, or "
            "supply PHISHTANK_APP_KEY if you have an existing key. Note that "
            "new key registration is currently disabled by PhishTank."
        )
    if status_code == 429:
        return "429 Too Many Requests. Rate limited. Wait and retry; do not loop."
    if status_code == 509:
        return "509 Bandwidth Exceeded. PhishTank feed is temporarily over quota. Retry later."
    if status_code == 404:
        return "404 Not Found. Check the --format and --compression combination against the developer page."
    return f"HTTP {status_code}. See https://phishtank.org/developer_info.php"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    # Restricted to CSV on purpose: inspect_datasets.py parses delimited text only,
    # so offering json/xml here would produce raw files that are silently never
    # inspected. JSON/XML additionally carry per-phish detail records (ip_address,
    # cidr_block, announcing_network, rir) — if those become useful for URL feature
    # engineering, widen this choice AND extend inspect_datasets.py in the same change.
    parser.add_argument("--format", default="csv", choices=["csv"], help="feed format (default: csv)")
    parser.add_argument("--compression", default="gz", choices=["gz", "bz2", "none"], help="feed compression (default: gz)")
    args = parser.parse_args()

    app_key = get_secret("PHISHTANK_APP_KEY")
    user_agent = get_secret("PHISHTANK_USER_AGENT") or DEFAULT_USER_AGENT

    url = build_feed_url(args.format, args.compression, app_key)
    safe_url = redact(url, app_key)

    extension = args.format if args.compression == "none" else f"{args.format}.{args.compression}"
    destination_dir = raw_dir("phishtank")
    filename = f"{FEED_BASENAME}_{utc_stamp()}.{extension}"
    destination = destination_dir / filename
    try:
        refuse_overwrite(destination)
    except FileExistsError as error:
        print(f"\nABORTED: {error}", file=sys.stderr)
        return 1

    print(f"Source      : PhishTank (Cisco Talos)")
    print(f"URL         : {safe_url}")
    print(f"App key     : {'supplied via environment' if app_key else 'NONE (keyless request)'}")
    print(f"User-Agent  : {user_agent}")
    print(f"Destination : {destination}")

    requested_at = utc_now_iso()
    try:
        response = download(url, user_agent)
    except requests.HTTPError as error:
        status = error.response.status_code if error.response is not None else 0
        print(f"\nDOWNLOAD FAILED: {explain_failure(status)}", file=sys.stderr)
        write_metadata(
            destination_dir,
            f"FAILED_{FEED_BASENAME}_{utc_stamp()}",
            {
                "source_name": "PhishTank",
                "outcome": "failed",
                "requested_at_utc": requested_at,
                "request_url": safe_url,
                "http_status": status,
                "diagnosis": explain_failure(status),
                "app_key_used": bool(app_key),
            },
        )
        return 1
    except requests.RequestException as error:
        print(f"\nDOWNLOAD FAILED: network error: {error}", file=sys.stderr)
        return 1

    written = 0
    with destination.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=1024 * 256):
            if chunk:
                handle.write(chunk)
                written += len(chunk)

    checksum = sha256_file(destination)
    metadata = {
        "source_name": "PhishTank",
        "source_operator": "Cisco Talos Intelligence Group",
        "source_homepage": "https://phishtank.org/",
        "documentation_url": "https://phishtank.org/developer_info.php",
        "outcome": "success",
        "feed_name": "online-valid (verified and currently online phishes)",
        "request_url": safe_url,
        "requested_at_utc": requested_at,
        "completed_at_utc": utc_now_iso(),
        "http_status": response.status_code,
        "http_etag": response.headers.get("ETag"),
        "http_last_modified": response.headers.get("Last-Modified"),
        "http_content_type": response.headers.get("Content-Type"),
        "http_content_length": response.headers.get("Content-Length"),
        "app_key_used": bool(app_key),
        "user_agent": user_agent,
        "data_format": args.format,
        "compression": args.compression,
        "documented_fields": DOCUMENTED_FIELDS,
        "documented_update_frequency": "hourly, on the hour",
        "documented_rate_limit": (
            "Keyless: a few downloads per day. With application key: higher limits "
            "and unlimited HEAD requests for ETag checks."
        ),
        "version_information": (
            "PhishTank does not assign version numbers to this feed. The ETag and "
            "Last-Modified headers plus the retrieval timestamp identify the snapshot."
        ),
        "raw_filename": destination.name,
        "raw_file_bytes": written,
        "raw_file_sha256": checksum,
        "licence_note": "Use governed by PhishTank / Cisco terms of use. Free for research use.",
    }
    write_metadata(destination_dir, destination.name, metadata)

    print(f"\nOK. Wrote {human_size(written)}")
    print(f"SHA-256     : {checksum}")
    print(f"ETag        : {response.headers.get('ETag')}")
    print(f"Last-Modified: {response.headers.get('Last-Modified')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
