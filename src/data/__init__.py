"""Data acquisition and loading modules for FYP2.

Each module in this package is responsible ONLY for acquiring raw data and
recording provenance. Cleaning, feature engineering, splitting and modelling
belong to later stages and must not appear here.
"""

from .phishtank import (  # noqa: F401
    EXPECTED_COLUMNS,
    PhishTankAcquisitionError,
    fetch_phishtank_dataset,
    find_latest_snapshot,
    list_snapshots,
)

__all__ = [
    "EXPECTED_COLUMNS",
    "PhishTankAcquisitionError",
    "fetch_phishtank_dataset",
    "find_latest_snapshot",
    "list_snapshots",
]
