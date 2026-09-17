"""
Inspect acquired raw datasets and report their ACTUAL structure.

Stage: Dataset Acquisition -> preliminary inspection only.

This script is strictly READ-ONLY with respect to data/raw/. It does not
clean, deduplicate, merge, balance, tokenise or otherwise preprocess any
dataset. It only measures what is actually present, so that the project
documentation records observed facts rather than dataset-page claims.

Usage
-----
    pip install -r scripts/requirements-acquisition.txt
    python scripts/inspect_datasets.py
    python scripts/inspect_datasets.py --sample-rows 20000

Output
------
    reports/dataset_inspection/inspection_<UTCSTAMP>.json
    reports/dataset_inspection/inspection_<UTCSTAMP>.md
"""

from __future__ import annotations

import argparse
import bz2
import gzip
import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from acquisition_common import human_size, project_root, utc_now_iso, utc_stamp  # noqa: E402

URL_PATTERN = re.compile(r"https?://|www\.", re.IGNORECASE)

# Column-name hints used to categorise fields. Matching is case-insensitive
# substring matching against the real column names found in the file.
FIELD_HINTS = {
    "label": ["label", "type", "class", "target", "is_phish", "category"],
    "body": ["body", "text", "content", "message", "email"],
    "subject": ["subject", "title"],
    "sender": ["sender", "from", "sender_email", "return_path"],
    "receiver": ["receiver", "to", "recipient"],
    "date": ["date", "time", "timestamp"],
    "url": ["url", "urls", "link", "links"],
}


def categorise_columns(columns: list[str]) -> dict[str, list[str]]:
    """Map semantic categories to the real column names present."""
    found: dict[str, list[str]] = {category: [] for category in FIELD_HINTS}
    for column in columns:
        lowered = column.strip().lower()
        for category, hints in FIELD_HINTS.items():
            if any(hint in lowered for hint in hints):
                found[category].append(column)
    return {category: names for category, names in found.items() if names}


def open_text(path: Path):
    """Open a plain, gzip- or bzip2-compressed text file for reading."""
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    if path.suffix == ".bz2":
        return bz2.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("r", encoding="utf-8", errors="replace")


def separator_for(path: Path) -> str:
    """Return the field separator implied by the filename.

    Compressed files carry their real extension before the compression suffix,
    e.g. online-valid.csv.gz -> ".csv".
    """
    name = path.name
    for suffix in (".gz", ".bz2"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return "\t" if name.endswith(".tsv") else ","


def pick_label_column(frame: pd.DataFrame, candidates: list[str]) -> str | None:
    """Choose the most plausible label column: few distinct values, non-empty."""
    best: tuple[int, str] | None = None
    for column in candidates:
        distinct = frame[column].dropna().nunique()
        if 1 < distinct <= 12:
            if best is None or distinct < best[0]:
                best = (distinct, column)
    return best[1] if best else None


def inspect_csv(path: Path, sample_rows: int) -> dict[str, Any]:
    """Inspect one delimited text file (optionally .gz/.bz2) and return observed facts."""
    separator = separator_for(path)
    report: dict[str, Any] = {
        "file": str(path.relative_to(project_root())),
        "file_bytes": path.stat().st_size,
        "file_size_human": human_size(path.stat().st_size),
        "separator": "tab" if separator == "\t" else "comma",
    }

    # Full pass, as strings, to count rows and missing values without type coercion.
    total_rows = 0
    missing_counts: dict[str, int] = {}
    columns: list[str] = []
    try:
        with open_text(path) as handle:
            for chunk in pd.read_csv(
                handle,
                sep=separator,
                dtype=str,
                chunksize=50_000,
                on_bad_lines="skip",
                low_memory=False,
            ):
                if not columns:
                    columns = list(chunk.columns)
                    missing_counts = {c: 0 for c in columns}
                total_rows += len(chunk)
                for column in columns:
                    if column in chunk:
                        blank = chunk[column].isna() | (chunk[column].astype(str).str.strip() == "")
                        missing_counts[column] += int(blank.sum())
    except Exception as error:  # noqa: BLE001
        report["error"] = f"Could not parse as CSV: {error}"
        return report

    report["n_rows"] = total_rows
    report["n_columns"] = len(columns)
    report["columns"] = columns
    report["missing_or_blank_per_column"] = missing_counts
    report["column_categories"] = categorise_columns(columns)

    # Sampled pass for dtype inference, duplicates, labels and text statistics.
    with open_text(path) as handle:
        sample = pd.read_csv(
            handle, sep=separator, nrows=sample_rows, on_bad_lines="skip", low_memory=False
        )

    report["sample_rows_used"] = int(len(sample))
    report["inferred_dtypes_from_sample"] = {c: str(t) for c, t in sample.dtypes.items()}
    report["exact_duplicate_rows_in_sample"] = int(sample.duplicated().sum())

    categories = report["column_categories"]

    # A URL feed (e.g. PhishTank online-valid) has URL rows but no email body.
    # Such feeds contain positives only, so class-label detection does not apply:
    # a "target" column names the impersonated brand, not the class.
    is_url_feed = bool(categories.get("url")) and not categories.get("body")
    report["dataset_kind"] = "url_feed" if is_url_feed else "email_corpus"

    if is_url_feed:
        report["label_column_detected"] = None
        report["labelling_note"] = (
            "Single-class source: every row is a verified phishing URL. "
            "Legitimate URLs must be obtained from a separate benign source "
            "before supervised training is possible."
        )
        url_columns = categories.get("url", [])
        # Prefer an exact 'url' column rather than relying on physical column order.
        exact = [c for c in url_columns if c.strip().lower() == "url"]
        url_column = exact[0] if exact else url_columns[0]
        urls = sample[url_column].astype(str)
        report["url_column_detected"] = url_column
        report["unique_urls_in_sample"] = int(urls.nunique())
        report["duplicate_urls_in_sample"] = int(urls.duplicated().sum())
        report["url_char_length"] = {
            "mean": round(float(urls.str.len().mean()), 1),
            "median": float(urls.str.len().median()),
            "max": int(urls.str.len().max()),
        }
        report["https_share_pct_in_sample"] = round(
            float(urls.str.lower().str.startswith("https://").mean()) * 100, 2
        )
        report["example_url"] = urls.iloc[0][:200] if len(urls) else None
        return report

    label_column = pick_label_column(sample, categories.get("label", []) or list(sample.columns))
    if label_column:
        counts = sample[label_column].astype(str).value_counts(dropna=False)
        report["label_column_detected"] = label_column
        report["class_distribution_in_sample"] = {str(k): int(v) for k, v in counts.items()}
        if len(counts) == 2:
            minority, majority = sorted(counts.values)
            report["class_balance_ratio_in_sample"] = round(minority / majority, 3)
    else:
        report["label_column_detected"] = None

    body_columns = categories.get("body", [])
    if body_columns:
        body_column = max(
            body_columns,
            key=lambda c: sample[c].astype(str).str.len().mean() if c in sample else 0,
        )
        text = sample[body_column].astype(str)
        report["body_column_detected"] = body_column
        report["body_char_length"] = {
            "mean": round(float(text.str.len().mean()), 1),
            "median": float(text.str.len().median()),
            "min": int(text.str.len().min()),
            "max": int(text.str.len().max()),
            "p95": float(text.str.len().quantile(0.95)),
        }
        report["body_contains_url_pct_in_sample"] = round(
            float(text.str.contains(URL_PATTERN).mean()) * 100, 2
        )
        report["duplicate_body_text_in_sample"] = int(text.duplicated().sum())
        report["example_body_excerpt"] = text.iloc[0][:300] if len(text) else None
    else:
        report["body_column_detected"] = None

    return report


SUPPORTED_SUFFIXES = (
    ".csv",
    ".tsv",
    ".csv.gz",
    ".csv.bz2",
    ".tsv.gz",
    ".tsv.bz2",
)

# Raw files that are legitimately present but that this stage does not inspect.
# They are reported explicitly rather than skipped in silence.
UNINSPECTED_SUFFIXES = (".json", ".xml", ".zip", ".php_serialized")


def discover_files() -> tuple[list[Path], list[Path]]:
    """Find raw dataset files.

    Returns (inspectable, skipped). Metadata sidecars and placeholders are ignored
    entirely; data files in formats this stage cannot parse are returned as skipped
    so the caller can warn about them.
    """
    raw_root = project_root() / "data" / "raw"
    if not raw_root.exists():
        return [], []

    inspectable: list[Path] = []
    skipped: list[Path] = []
    for path in sorted(raw_root.rglob("*")):
        if not path.is_file() or path.name == ".gitkeep":
            continue
        if path.name.endswith(".metadata.json"):
            continue
        name = path.name.lower()
        if name.endswith(SUPPORTED_SUFFIXES):
            inspectable.append(path)
        elif name.endswith(UNINSPECTED_SUFFIXES) or ".json.gz" in name or ".xml.gz" in name:
            skipped.append(path)
        else:
            skipped.append(path)
    return inspectable, skipped


def to_markdown(reports: list[dict[str, Any]], generated_at: str) -> str:
    """Render a human-readable inspection summary."""
    lines = [
        "# Raw Dataset Inspection Report",
        "",
        f"Generated: {generated_at}",
        "",
        "All figures below were measured from the actual downloaded files.",
        "No cleaning or preprocessing was performed.",
        "",
        "## Summary",
        "",
        "| File | Rows | Cols | Label column | Body column | Size |",
        "| --- | ---: | ---: | --- | --- | ---: |",
    ]
    for report in reports:
        if "error" in report:
            lines.append(f"| `{report['file']}` | — | — | parse error | — | {report['file_size_human']} |")
            continue
        lines.append(
            f"| `{report['file']}` | {report['n_rows']:,} | {report['n_columns']} | "
            f"{report.get('label_column_detected') or '—'} | "
            f"{report.get('body_column_detected') or '—'} | {report['file_size_human']} |"
        )

    for report in reports:
        lines += ["", f"## `{report['file']}`", ""]
        if "error" in report:
            lines.append(f"Parse error: {report['error']}")
            continue
        lines += [
            f"* Rows: {report['n_rows']:,}",
            f"* Columns ({report['n_columns']}): {', '.join(f'`{c}`' for c in report['columns'])}",
            f"* Sample used for detailed statistics: {report['sample_rows_used']:,} rows",
            f"* Exact duplicate rows in sample: {report['exact_duplicate_rows_in_sample']:,}",
        ]
        if report.get("dataset_kind") == "url_feed":
            lines += [
                f"* Dataset kind: URL feed (single class)",
                f"* URL column: `{report['url_column_detected']}`",
                f"* Unique URLs in sample: {report['unique_urls_in_sample']:,} "
                f"({report['duplicate_urls_in_sample']:,} duplicates)",
                f"* URL length (chars): mean {report['url_char_length']['mean']}, "
                f"max {report['url_char_length']['max']}",
                f"* HTTPS share: {report['https_share_pct_in_sample']}%",
                f"* Labelling: {report['labelling_note']}",
            ]
        if report.get("class_distribution_in_sample"):
            distribution = ", ".join(
                f"{k} = {v:,}" for k, v in report["class_distribution_in_sample"].items()
            )
            lines.append(f"* Class distribution in sample (`{report['label_column_detected']}`): {distribution}")
        if report.get("body_char_length"):
            stats = report["body_char_length"]
            lines.append(
                f"* Body length (chars): mean {stats['mean']}, median {stats['median']}, "
                f"p95 {stats['p95']}, max {stats['max']}"
            )
            lines.append(f"* Rows whose body contains a URL: {report['body_contains_url_pct_in_sample']}%")
            lines.append(f"* Duplicate body texts in sample: {report['duplicate_body_text_in_sample']:,}")
        blank = {k: v for k, v in report["missing_or_blank_per_column"].items() if v}
        lines.append(
            "* Missing/blank values: "
            + (", ".join(f"`{k}` = {v:,}" for k, v in blank.items()) if blank else "none")
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample-rows", type=int, default=50_000, help="rows used for detailed statistics")
    args = parser.parse_args()

    files, skipped = discover_files()

    if skipped:
        print("NOT INSPECTED — this stage parses delimited text (.csv/.tsv, optionally .gz/.bz2) only:")
        for path in skipped:
            print(f"  ! {path.relative_to(project_root())}")
        print(
            "  If a PhishTank feed was downloaded with --format json or --format xml, "
            "re-run acquire_phishtank.py with the default CSV format.\n"
        )

    if not files:
        print(
            "No inspectable raw dataset files found under data/raw/.\n"
            "Run scripts/acquire_phishtank.py and scripts/acquire_kaggle.py first.",
            file=sys.stderr,
        )
        return 1

    print(f"Inspecting {len(files)} file(s)...\n")
    reports = []
    for path in files:
        print(f"  {path.name}")
        reports.append(inspect_csv(path, args.sample_rows))

    generated_at = utc_now_iso()
    out_dir = project_root() / "reports" / "dataset_inspection"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_stamp()

    json_path = out_dir / f"inspection_{stamp}.json"
    json_path.write_text(
        json.dumps({"generated_at_utc": generated_at, "files": reports}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    md_path = out_dir / f"inspection_{stamp}.md"
    md_path.write_text(to_markdown(reports, generated_at), encoding="utf-8")

    print(f"\nWrote {json_path.relative_to(project_root())}")
    print(f"Wrote {md_path.relative_to(project_root())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
