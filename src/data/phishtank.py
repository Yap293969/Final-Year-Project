"""
Reusable PhishTank URL-feed acquisition for FYP2.

Stage: Dataset Acquisition. This module ONLY downloads, preserves and loads the
official PhishTank feed, and records provenance. It performs NO cleaning, feature
engineering, balancing, splitting or modelling -- those belong to later stages.

Official source
---------------
Feed          : http://data.phishtank.com/data/online-valid.csv
Developer doc : https://phishtank.org/developer_info.php
Operator      : Cisco Talos Intelligence Group
Contents      : verified AND currently online phishing entries
Update period : hourly, on the hour

Access model
------------
Keyless access is the default. PhishTank documents the keyless allowance as "a few
downloads per day", and requests are frequently met with a Cloudflare challenge.
New application keys cannot currently be obtained because PhishTank registration is
temporarily disabled.

If a key becomes available later, supply it through the environment -- never in code:

    PHISHTANK_APP_KEY=...                     optional application key
    PHISHTANK_USER_AGENT=phishtank/yourname   optional descriptive User-Agent

Typical use from a notebook
---------------------------
    from src.data.phishtank import fetch_phishtank_dataset

    df = fetch_phishtank_dataset()                  # reuse a recent snapshot
    df = fetch_phishtank_dataset(force_refresh=True)
    path = fetch_phishtank_dataset(load=False)      # raw file path only

Outputs
-------
    data/raw/phishtank/online-valid_<UTCSTAMP>.csv          exact bytes as served
    data/metadata/phishtank/online-valid_<UTCSTAMP>.json    provenance record
    data/metadata/phishtank/FAILED_<UTCSTAMP>.json          failed attempts
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import platform
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

__all__ = [
    "EXPECTED_COLUMNS",
    "PhishTankAcquisitionError",
    "fetch_phishtank_dataset",
    "find_latest_snapshot",
    "list_snapshots",
]

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

DEFAULT_FEED_URL = "http://data.phishtank.com/data/online-valid.csv"
FEED_BASENAME = "online-valid"
DEFAULT_USER_AGENT = "phishtank/fyp2-anti-phishing-research"

# Fields documented for the online-valid feed. Presence is verified after download;
# the raw file is never altered to make it match.
EXPECTED_COLUMNS = [
    "phish_id",
    "url",
    "phish_detail_url",
    "submission_time",
    "verified",
    "verification_time",
    "online",
    "target",
]

RAW_RELATIVE = Path("data") / "raw" / "phishtank"
METADATA_RELATIVE = Path("data") / "metadata" / "phishtank"

# A snapshot younger than this is reused instead of re-downloaded. The feed refreshes
# hourly and the keyless allowance is small, so the default is deliberately cautious.
DEFAULT_MAX_AGE_HOURS = 6.0

_STAMP_PATTERN = re.compile(r"_(\d{8}T\d{6}Z)\.csv$", re.IGNORECASE)

LOGGER = logging.getLogger(__name__)


class PhishTankAcquisitionError(RuntimeError):
    """Raised when a snapshot could not be acquired or failed validation."""


# --------------------------------------------------------------------------
# Paths, time, hashing
# --------------------------------------------------------------------------

def project_root() -> Path:
    """Return the FYP2 project root.

    Resolved from this file's location (src/data/phishtank.py -> two levels up).
    Falls back to the working directory when __file__ is unavailable, which happens
    if the module body is pasted directly into a notebook cell.
    """
    try:
        return Path(__file__).resolve().parents[2]
    except (NameError, IndexError):  # pragma: no cover - notebook fallback
        return Path.cwd()


def _raw_dir() -> Path:
    target = project_root() / RAW_RELATIVE
    target.mkdir(parents=True, exist_ok=True)
    return target


def _metadata_dir() -> Path:
    target = project_root() / METADATA_RELATIVE
    target.mkdir(parents=True, exist_ok=True)
    return target


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat(timespec="seconds")


def _utc_stamp() -> str:
    return _utc_now().strftime("%Y%m%dT%H%M%SZ")


def _sha256(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()


def _human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def _ensure_logging() -> None:
    """Attach a plain handler once, so notebook callers see progress messages."""
    if not LOGGER.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("[phishtank] %(message)s"))
        LOGGER.addHandler(handler)
    if LOGGER.level == logging.NOTSET:
        LOGGER.setLevel(logging.INFO)


# --------------------------------------------------------------------------
# Credentials (never hard-coded)
# --------------------------------------------------------------------------

def _get_env(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


def _build_feed_url(base_url: str, app_key: str | None) -> str:
    """Insert the application-key path segment when a key is supplied.

    PhishTank's keyed form is /data/<app_key>/online-valid.csv
    """
    if not app_key:
        return base_url
    marker = "/data/"
    if marker not in base_url:
        return base_url
    head, _, tail = base_url.partition(marker)
    return head + marker + app_key + "/" + tail


def _redact(text: str, secret: str | None) -> str:
    """Remove a secret from any string before it is logged or written to disk."""
    if secret and secret in text:
        return text.replace(secret, "<APP_KEY_REDACTED>")
    return text


# --------------------------------------------------------------------------
# Snapshot discovery
# --------------------------------------------------------------------------

def list_snapshots() -> list[Path]:
    """Return every stored snapshot, oldest first."""
    raw_dir = _raw_dir()
    return sorted(
        (p for p in raw_dir.glob(FEED_BASENAME + "_*.csv") if p.is_file()),
        key=lambda p: p.name,
    )


def _snapshot_timestamp(path: Path) -> datetime | None:
    """Recover the UTC timestamp encoded in a snapshot filename."""
    match = _STAMP_PATTERN.search(path.name)
    if not match:
        return None
    try:
        parsed = datetime.strptime(match.group(1), "%Y%m%dT%H%M%SZ")
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc)


def find_latest_snapshot() -> Path | None:
    """Return the most recent stored snapshot, or None if there is none."""
    snapshots = list_snapshots()
    return snapshots[-1] if snapshots else None


def _snapshot_age_hours(path: Path) -> float | None:
    stamp = _snapshot_timestamp(path)
    if stamp is None:
        return None
    return (_utc_now() - stamp).total_seconds() / 3600.0


# --------------------------------------------------------------------------
# Payload validation
# --------------------------------------------------------------------------

def _validate_feed_file(path: Path) -> dict[str, Any]:
    """Confirm a downloaded file really is the PhishTank CSV feed.

    PhishTank sits behind Cloudflare, which can return a challenge page with an
    HTTP 200 status rather than an error code. Trusting the status alone would
    record an HTML page as a successful dataset, so the bytes are checked.

    Returns a report dict; report["valid"] is False when the file is unusable.
    """
    report: dict[str, Any] = {"valid": False}

    if path.stat().st_size == 0:
        report["problem"] = "The downloaded file is empty (0 bytes)."
        return report

    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        first_line = handle.readline()
        stripped = first_line.lstrip().lower()
        if stripped.startswith(("<!doctype", "<html", "<?xml")):
            report["problem"] = (
                "The response body is HTML/XML, not CSV. This is almost certainly a "
                "Cloudflare challenge or an error page returned with a 200 status. "
                "Retry later, from a different network, or download the feed in a "
                "browser and register it manually."
            )
            report["first_line"] = first_line[:200]
            return report

        header = next(csv.reader([first_line]), [])
        report["header_found"] = header

        missing = [column for column in EXPECTED_COLUMNS if column not in header]
        report["missing_columns"] = missing
        report["expected_columns_present"] = not missing
        if missing:
            report["problem"] = (
                "Header does not match the documented PhishTank feed. "
                "Missing column(s): " + str(missing)
            )
            return report

        data_rows = sum(1 for _ in handle)

    report["data_rows"] = data_rows
    report["valid"] = True
    if data_rows == 0:
        report["warning"] = "Header is correct but the feed contains no data rows."
    return report


# --------------------------------------------------------------------------
# Metadata
# --------------------------------------------------------------------------

def _write_metadata(name: str, record: dict[str, Any]) -> Path:
    """Write a provenance record under data/metadata/phishtank/."""
    path = _metadata_dir() / (name + ".json")
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _runtime_record() -> dict[str, Any]:
    return {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "runtime": "colab" if "COLAB_RELEASE_TAG" in os.environ else "local",
    }


def _explain_http_status(status: int) -> str:
    if status == 403:
        return (
            "403 Forbidden. Documented behaviour when the keyless download allowance "
            "is exhausted, or when Cloudflare interposes a challenge. Retry later or "
            "from a different network. New application keys cannot currently be "
            "registered with PhishTank."
        )
    if status == 429:
        return "429 Too Many Requests. Rate limited -- wait before retrying; do not loop."
    if status == 509:
        return "509 Bandwidth Exceeded. The feed is temporarily over quota. Retry later."
    if status == 404:
        return (
            "404 Not Found. Check the feed URL against "
            "https://phishtank.org/developer_info.php"
        )
    return "HTTP " + str(status) + ". See https://phishtank.org/developer_info.php"


def _record_failure(name_suffix: str, record: dict[str, Any]) -> None:
    _write_metadata("FAILED_" + FEED_BASENAME + "_" + name_suffix, record)


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def fetch_phishtank_dataset(
    force_refresh: bool = False,
    max_age_hours: float = DEFAULT_MAX_AGE_HOURS,
    load: bool = True,
    feed_url: str = DEFAULT_FEED_URL,
    timeout: int = 120,
) -> pd.DataFrame | Path:
    """Acquire the current PhishTank online-valid snapshot.

    A recent local snapshot is reused rather than re-downloaded, because the keyless
    allowance is only a few requests per day.

    Parameters
    ----------
    force_refresh:
        Download even when a recent snapshot exists.
    max_age_hours:
        A stored snapshot younger than this is reused. The feed updates hourly.
    load:
        When True (default) return a pandas DataFrame; when False return the Path of
        the raw snapshot without parsing it.
    feed_url:
        Official feed URL. An application key from PHISHTANK_APP_KEY is inserted into
        the path automatically when present.
    timeout:
        Per-request timeout in seconds.

    Returns
    -------
    pandas.DataFrame or pathlib.Path
        The DataFrame carries provenance in df.attrs (source_path, sha256,
        retrieved_at_utc, from_cache and the full provenance record).

    Raises
    ------
    PhishTankAcquisitionError
        If no snapshot could be obtained, or the downloaded payload was not the
        expected CSV feed. Raw data already on disk is never modified.
    """
    _ensure_logging()

    # ---- 1. Reuse a recent snapshot where possible -------------------------
    if not force_refresh:
        latest = find_latest_snapshot()
        if latest is not None:
            age = _snapshot_age_hours(latest)
            if age is not None and age <= max_age_hours:
                LOGGER.info(
                    "Reusing existing snapshot %s (age %.1f h <= %.1f h). "
                    "Pass force_refresh=True to download again.",
                    latest.name, age, max_age_hours,
                )
                return _load_snapshot(latest, from_cache=True) if load else latest
            LOGGER.info(
                "Newest snapshot %s is %s; downloading a fresh one.",
                latest.name,
                ("%.1f h old" % age) if age is not None else "of unknown age",
            )

    # ---- 2. Build the request ----------------------------------------------
    app_key = _get_env("PHISHTANK_APP_KEY")
    user_agent = _get_env("PHISHTANK_USER_AGENT") or DEFAULT_USER_AGENT
    request_url = _build_feed_url(feed_url, app_key)
    safe_url = _redact(request_url, app_key)

    LOGGER.info("Source     : PhishTank (Cisco Talos)")
    LOGGER.info("URL        : %s", safe_url)
    LOGGER.info("App key    : %s", "supplied via environment" if app_key else "none (keyless)")
    LOGGER.info("User-Agent : %s", user_agent)

    requested_at = _utc_now_iso()
    started = time.monotonic()
    stamp = _utc_stamp()

    # ---- 3. Download to a temporary file, so a bad response never lands in
    #         data/raw/ and can never be mistaken for a dataset --------------
    temp_descriptor, temp_name = tempfile.mkstemp(prefix="phishtank_", suffix=".csv.part")
    os.close(temp_descriptor)
    temp_path = Path(temp_name)

    try:
        response = requests.get(
            request_url,
            headers={"User-Agent": user_agent, "Accept-Encoding": "identity"},
            stream=True,
            timeout=timeout,
        )
        response.raise_for_status()

        written = 0
        with temp_path.open("wb") as sink:
            for chunk in response.iter_content(chunk_size=1 << 18):
                if chunk:
                    sink.write(chunk)
                    written += len(chunk)

    except requests.HTTPError as error:
        status = error.response.status_code if error.response is not None else 0
        diagnosis = _explain_http_status(status)
        _record_failure(stamp, {
            "source_name": "PhishTank",
            "outcome": "failed",
            "failure_kind": "http_error",
            "source_url": safe_url,
            "requested_at_utc": requested_at,
            "failed_at_utc": _utc_now_iso(),
            "http_status": status,
            "diagnosis": diagnosis,
            "app_key_used": bool(app_key),
            "user_agent": user_agent,
            "runtime": _runtime_record(),
        })
        temp_path.unlink(missing_ok=True)
        LOGGER.error("Download FAILED: %s", diagnosis)
        raise PhishTankAcquisitionError(diagnosis) from error

    except (requests.ConnectionError, requests.Timeout) as error:
        message = "Network error contacting " + safe_url + ": " + str(error)
        _record_failure(stamp, {
            "source_name": "PhishTank",
            "outcome": "failed",
            "failure_kind": "network_error",
            "source_url": safe_url,
            "requested_at_utc": requested_at,
            "failed_at_utc": _utc_now_iso(),
            "http_status": None,
            "diagnosis": message,
            "app_key_used": bool(app_key),
            "user_agent": user_agent,
            "runtime": _runtime_record(),
        })
        temp_path.unlink(missing_ok=True)
        LOGGER.error("Download FAILED: %s", message)
        raise PhishTankAcquisitionError(message) from error

    except requests.RequestException as error:
        temp_path.unlink(missing_ok=True)
        message = "Request failed: " + str(error)
        LOGGER.error("Download FAILED: %s", message)
        raise PhishTankAcquisitionError(message) from error

    elapsed = time.monotonic() - started

    # ---- 4. Validate the payload before it becomes a dataset ---------------
    validation = _validate_feed_file(temp_path)
    if not validation["valid"]:
        problem = validation.get("problem", "Downloaded payload failed validation.")
        _record_failure(stamp, {
            "source_name": "PhishTank",
            "outcome": "failed",
            "failure_kind": "payload_validation",
            "source_url": safe_url,
            "requested_at_utc": requested_at,
            "failed_at_utc": _utc_now_iso(),
            "http_status": response.status_code,
            "http_content_type": response.headers.get("Content-Type"),
            "bytes_received": written,
            "diagnosis": problem,
            "validation": validation,
            "app_key_used": bool(app_key),
            "user_agent": user_agent,
            "runtime": _runtime_record(),
        })
        temp_path.unlink(missing_ok=True)
        LOGGER.error("Validation FAILED: %s", problem)
        raise PhishTankAcquisitionError(problem)

    # ---- 5. Move the verified bytes into data/raw/, never overwriting ------
    destination = _raw_dir() / (FEED_BASENAME + "_" + stamp + ".csv")
    if destination.exists():
        temp_path.unlink(missing_ok=True)
        raise PhishTankAcquisitionError(
            "Refusing to overwrite an existing raw snapshot: " + str(destination)
        )
    temp_path.replace(destination)

    checksum = _sha256(destination)
    size_bytes = destination.stat().st_size
    record: dict[str, Any] = {
        "source_name": "PhishTank",
        "source_operator": "Cisco Talos Intelligence Group",
        "documentation_url": "https://phishtank.org/developer_info.php",
        "feed_name": "online-valid (verified and currently online phishes)",
        "outcome": "success",
        "source_url": safe_url,
        "requested_at_utc": requested_at,
        "retrieved_at_utc": _utc_now_iso(),
        "elapsed_seconds": round(elapsed, 2),
        "http_status": response.status_code,
        "http_content_type": response.headers.get("Content-Type"),
        "http_etag": response.headers.get("ETag"),
        "http_last_modified": response.headers.get("Last-Modified"),
        "http_content_length": response.headers.get("Content-Length"),
        "app_key_used": bool(app_key),
        "user_agent": user_agent,
        "local_filename": destination.name,
        "local_path": str(destination.relative_to(project_root())),
        "file_size_bytes": size_bytes,
        "file_size_human": _human_size(size_bytes),
        "sha256": checksum,
        "expected_columns": EXPECTED_COLUMNS,
        "validation": validation,
        "documented_update_frequency": "hourly, on the hour",
        "version_information": (
            "PhishTank does not version this feed. The ETag, Last-Modified header and "
            "retrieval timestamp identify the snapshot."
        ),
        "modification_note": "Raw file stored exactly as served; never modified.",
        "licence_note": "Use governed by PhishTank / Cisco terms. Free for research use.",
        "runtime": _runtime_record(),
    }
    metadata_path = _write_metadata(destination.stem, record)

    LOGGER.info("Saved      : %s (%s)", record["local_path"], record["file_size_human"])
    LOGGER.info("Rows       : %s", validation.get("data_rows"))
    LOGGER.info("SHA-256    : %s", checksum)
    LOGGER.info("Metadata   : %s", metadata_path.relative_to(project_root()))
    LOGGER.info("Acquisition SUCCEEDED.")

    if load:
        return _load_snapshot(destination, from_cache=False, record=record)
    return destination


def _load_snapshot(
    path: Path,
    from_cache: bool,
    record: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Load a stored snapshot into a DataFrame. The file itself is not modified.

    Values are read as strings with blanks preserved, so the loaded frame is a
    faithful view of the raw file rather than a type-coerced interpretation.
    """
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)

    if record is None:
        metadata_path = _metadata_dir() / (path.stem + ".json")
        if metadata_path.exists():
            try:
                record = json.loads(metadata_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                record = None

    missing = [column for column in EXPECTED_COLUMNS if column not in frame.columns]
    if missing:
        LOGGER.warning("Loaded snapshot is missing expected column(s): %s", missing)

    frame.attrs.update({
        "source": "PhishTank online-valid",
        "source_path": str(path),
        "from_cache": from_cache,
        "sha256": (record or {}).get("sha256"),
        "retrieved_at_utc": (record or {}).get("retrieved_at_utc"),
        "missing_expected_columns": missing,
        "provenance": record,
    })
    LOGGER.info(
        "Loaded %s rows x %s columns from %s", len(frame), len(frame.columns), path.name
    )
    return frame
