"""
Shared helpers for FYP2 dataset acquisition.

Stage: Dataset Acquisition (FIND -> VERIFY -> DOWNLOAD -> RECORD)

These helpers only WRITE raw files and provenance metadata.
They never modify, clean or preprocess acquired data.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

def project_root() -> Path:
    """Return the FYP2 project root (parent of the scripts/ directory).

    Falls back to the current working directory when running in an
    environment where __file__ is not defined (e.g. some notebook cells).
    """
    try:
        return Path(__file__).resolve().parent.parent
    except NameError:  # pragma: no cover - notebook fallback
        return Path.cwd()


def raw_dir(*parts: str) -> Path:
    """Return (and create) a directory under data/raw/."""
    target = project_root().joinpath("data", "raw", *parts)
    target.mkdir(parents=True, exist_ok=True)
    return target


# --------------------------------------------------------------------------
# Time / hashing
# --------------------------------------------------------------------------

def utc_now_iso() -> str:
    """ISO 8601 UTC timestamp, e.g. 2026-08-13T09:15:42+00:00."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def utc_stamp() -> str:
    """Filename-safe UTC stamp, e.g. 20260813T091542Z."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA-256 hex digest of a file (read-only operation)."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --------------------------------------------------------------------------
# Secrets
# --------------------------------------------------------------------------

def redact(text: str, secret: str | None) -> str:
    """Replace a secret value with a placeholder so it is never written to disk."""
    if secret and secret in text:
        return text.replace(secret, "<APP_KEY_REDACTED>")
    return text


def get_secret(env_var: str) -> str | None:
    """Read a credential from the environment.

    Credentials are NEVER hard-coded in this repository. Set them in the
    shell, in a local .env file that is not committed, or via Colab secrets.
    """
    value = os.environ.get(env_var, "").strip()
    return value or None


# --------------------------------------------------------------------------
# Provenance records
# --------------------------------------------------------------------------

def environment_record() -> dict[str, Any]:
    """Capture the runtime environment for reproducibility."""
    return {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "hostname_type": "colab" if "COLAB_RELEASE_TAG" in os.environ else "local",
    }


def write_metadata(destination_dir: Path, name: str, record: dict[str, Any]) -> Path:
    """Write a provenance record as JSON next to the raw data.

    The metadata file is a sidecar. The raw data file itself is never touched.
    """
    record = {"recorded_at_utc": utc_now_iso(), **record, "environment": environment_record()}
    path = destination_dir / f"{name}.metadata.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def refuse_overwrite(path: Path) -> None:
    """Guard against overwriting an existing raw dataset file.

    Project rule: raw datasets must be preserved and never overwritten
    unless explicitly instructed.
    """
    if path.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing raw file: {path}\n"
            "Raw datasets are preserved by project rule. Move or rename the "
            "existing file first if you intend to re-acquire."
        )


def human_size(num_bytes: int) -> str:
    """Format a byte count for logging."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"
