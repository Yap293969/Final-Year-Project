# FYP2 Dataset Sources

Record of data sources, acquisition method, selection justification and known limitations.

Investigation date: 2026-08-13
Stage: Dataset Acquisition (FIND → VERIFY → DOWNLOAD → RECORD)

> **Execution status:** the acquisition tooling below is written and tested, but the
> downloads have **not yet been executed**. `data/raw/` is currently empty apart from
> `.gitkeep` placeholders. See [§5 How to run](#5-how-to-run) and
> [§6 Acquisition log](#6-acquisition-log). No dataset property in this document is
> asserted from a dataset page alone — all observed figures will be filled in from
> `reports/dataset_inspection/` after the scripts run.

---

## 1. URL data source — PhishTank

### 1.1 Why PhishTank was selected

* It is the source named in the approved FYP1 methodology, so using it keeps the
  implementation aligned with the accepted research plan.
* It is operated by **Cisco Talos Intelligence Group**, which gives the data a
  credible and citable institutional owner.
* Entries are **community-verified** rather than automatically scraped, so the
  phishing label carries a human verification step.
* The `online-valid` feed contains only phishes that are verified **and** currently
  online, which suits a study of live phishing characteristics.
* It is free for research use and provides a bulk downloadable feed, avoiding the
  need for large numbers of individual URL lookups.

### 1.2 Verified feed characteristics

Confirmed from the official developer page on 2026-08-13.

| Property | Value |
| --- | --- |
| Feed name | `online-valid` (verified **and** currently online phishes) |
| Formats | CSV, JSON, XML, serialized PHP |
| Compression | plain, `.gz`, `.bz2` |
| Base URL | `http://data.phishtank.com/data/online-valid.<ext>` |
| With app key | `http://data.phishtank.com/data/<app_key>/online-valid.<ext>` |
| Update frequency | Hourly, on the hour |
| Authentication | Application key is **optional** for the download feed |
| Rate limit (keyless) | "a few downloads per day" |
| Rate limit (with key) | Higher; unlimited HTTP HEAD requests for `ETag` checks |
| Required header | Descriptive `User-Agent`, recommended form `phishtank/<username>` |
| Versioning | No version numbers. Snapshots identified by `ETag`, `Last-Modified` and retrieval timestamp |

Documented fields:

| Field | Meaning |
| --- | --- |
| `phish_id` | PhishTank identifier (positive integer) |
| `url` | The phishing URL |
| `phish_detail_url` | PhishTank detail page for the entry |
| `submission_time` | ISO 8601 report time |
| `verified` | Always `yes` in this feed |
| `verification_time` | ISO 8601 community verification time |
| `online` | Always `yes` in this feed |
| `target` | Impersonated brand, where known |

### 1.3 Recommended request method

Bulk download of the compressed CSV feed, **not** per-URL lookups:

```
GET http://data.phishtank.com/data/online-valid.csv.gz
User-Agent: phishtank/<username>
```

Implemented in `scripts/acquire_phishtank.py`.

### 1.3.1 Keyless access — verified 2026-08-16

Third-party posts describe "downloading the public data dump without an API key" as
if it were a separate channel. It is not. Checked against the official developer page:

| Claim | Verdict |
| --- | --- |
| The feed can be downloaded without an application key | **Correct**, and officially sanctioned |
| It is a distinct, unrestricted "public dump" | **Incorrect.** Same URLs, same host, same rate limit: *"Without this key, you will be limited to a few downloads per day."* |
| `phishtank.net` is a different service | **Incorrect.** `.net`, `.org` and `.com` serve identical content; all format tables point at `data.phishtank.com` |
| JSON feed lives at `https://phishtank.com` | **Incorrect.** The JSON feed is `http://data.phishtank.com/data/online-valid.json` (`.gz`, `.bz2`) |
| Registration is *permanently* closed | **Unsupported.** The register page states *"New user registration temporarily disabled"*. Do not describe it as permanent in the report |

Conclusion: keyless bulk download **is** the fallback, and it is already what
`acquire_phishtank.py` performs by default. There is no additional method that avoids
the daily limit.

### 1.3.2 Manual download fallback

If the automated request is refused (daily allowance exhausted, or a Cloudflare
challenge), download the feed in a browser and register it with:

```
python scripts/register_manual_download.py --file <path-to-download> \
    --downloaded-at <ISO 8601 time>
```

This produces the **same provenance sidecar** as the automated path, so both routes
are equivalent evidence. The script verifies that the file really is the PhishTank
CSV feed — a Cloudflare challenge page saved as `.csv` is rejected rather than
silently accepted as data — copies it into `data/raw/phishtank/` under a timestamped
name, and records the SHA-256. The original download is left untouched.

The transport differs, the research record does not. What a manual download loses is
only the `ETag` and `Last-Modified` headers; the snapshot remains identified by
download time and checksum.

### 1.4 Known limitations and risks

1. **A new application key cannot currently be obtained.** PhishTank's registration
   page states *"New user registration temporarily disabled"* (re-checked 2026-08-16;
   wording unchanged — "temporarily", not permanently),
   so the project must operate keyless unless an existing account is available.
   Keyless access is limited to a few downloads per day and is frequently met with
   a Cloudflare `403`.
2. **Snapshot, not history.** The feed is a point-in-time view of currently-online
   phishes. Dataset size therefore depends on when it is retrieved, and the snapshot
   is not reproducible by a later re-download. The retrieved file must be preserved.
3. **Single class.** Every row is a phishing URL. **A separate benign URL source is
   required** before supervised URL classification is possible — see §3.
4. **No page content.** Only the URL string and metadata are provided, which suits
   lexical/structural URL features and BERT over the URL string, but rules out
   HTML-content features.
5. **Brand skew.** `target` is dominated by a small number of heavily-phished brands,
   which may bias any brand-derived feature.
6. **Platform instability.** Talos has announced a full rewrite of PhishTank with no
   timeline, so feed availability should not be assumed stable across the project.

**Agreed handling (2026-08-13):** PhishTank remains the primary URL source. A second
URL source will be introduced **only if** the keyless limitation materially prevents
the experiments. Any such addition will be recorded here as an implementation
decision, not as a methodology change.

---

## 2. Email data source — Kaggle candidates

Two candidates are acquired for inspection. **No primary dataset has been selected
yet**; selection follows inspection, per the project rule that dataset properties
must be observed rather than assumed.

### Candidate A — `naserabdullahalam/phishing-email-dataset`

| Field | Value |
| --- | --- |
| Title | Phishing Email Dataset |
| Owner | naserabdullahalam |
| URL | https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset |
| Identifier | `naserabdullahalam/phishing-email-dataset` |
| Description | "Phish No More: The Enron, Ling, CEAS, Nazario, Nigerian & SpamAssassin Datasets" |
| Constituent corpora | Enron, Ling, CEAS_08, Nazario, Nigerian Fraud, SpamAssassin |
| Academic provenance | Associated with *Curated Datasets and Feature Analysis for Phishing Email Detection with Machine Learning*, IEEE ICMI 2024 — the paper reports seven curated datasets totalling 203,176 email instances |
| Version | To be recorded at download |
| Records | To be measured at inspection |
| Columns | To be measured at inspection |

Expected relevance: aggregates several standard corpora used in the phishing-detection
literature, and is reported to retain header-level fields (sender, receiver, subject)
in addition to the body, which supports richer feature engineering for XGBoost.

### Candidate B — `subhajournal/phishingemails`

| Field | Value |
| --- | --- |
| Title | Phishing Email Detection |
| Owner | subhajournal |
| URL | https://www.kaggle.com/datasets/subhajournal/phishingemails |
| Identifier | `subhajournal/phishingemails` |
| Description | "Detecting Phishing Emails by Text Analytics" |
| Reported size | ~18,650 rows; secondary literature reports 11,322 legitimate and 7,328 phishing, with 16 null bodies |
| Reported columns | `Email Text`, `Email Type` (classes: *Safe Email*, *Phishing Email*) |
| Version | To be recorded at download |
| Records | To be measured at inspection |
| Columns | To be measured at inspection |

Expected relevance: small, simple and easy to defend in a viva; useful as an
independent hold-out corpus even if not chosen as primary.

### Selection criteria to be applied after inspection

Email text quality · availability of subject and body · availability of metadata ·
label clarity · class balance · dataset size · duplicate risk · source diversity ·
suitability for BERT feature extraction · suitability for XGBoost · potential data
leakage · reproducibility · research relevance · practicality on Colab.

---

## 3. Benign URL source — RESOLVED 2026-08-22

Previously an open gap: PhishTank is phishing-only, so supervised URL classification was
impossible. Resolved by taking the **`benign` rows only** of the Kaggle dataset
`sid321axn/malicious-urls-dataset` (file `malicious_phish.csv`).

| Property | Value |
| --- | --- |
| Identifier | `sid321axn/malicious-urls-dataset` |
| Retrieved (UTC) | 2026-08-22T09:51:09Z |
| Rows in file (measured) | 651,191 |
| `benign` rows (measured) | **428,103** |
| Rows used by this project | the 428,103 `benign` rows only |
| Rows deliberately unused | `defacement` 96,457, `phishing` 94,111, `malware` 32,520 |

**Why not a popularity list.** Tranco, Majestic and Cisco Umbrella publish registered
*domains*, not full URLs. PhishTank entries are typically deep links with paths and query
strings, so pairing them with bare domains would let a classifier separate the classes on
URL length or the presence of a path alone — an artificially easy task producing inflated
metrics. The `benign` rows here are full URLs, keeping both classes structurally
comparable. Tranco remained reachable at the time of the decision (HTTP 200, 9.74 MB) and
stays available as a secondary cross-check should one be wanted later.

**Why the phishing rows of this file are not used.** PhishTank is the approved primary
phishing-URL source (`FYP_Specification.md` §7); sourcing phishing URLs elsewhere would
change the approved dataset strategy.

### 3.1 Measured limitations of this pairing

1. **Vintage mismatch.** This snapshot dates from 2021-07-23; the PhishTank snapshot is
   from 2026-08-18.
2. **URL formatting differs sharply between the sources — measured, not suspected.**
   100.00% of the 72,230 PhishTank URLs begin with an explicit scheme such as `https://`,
   against only 28.87% of the URLs in this file. Combined naively, the presence of a
   scheme would be an almost perfect indicator of *which dataset a URL came from*, and a
   model could score well while learning nothing about phishing. This must be neutralised
   during preprocessing.
3. **Different collection processes.** Beyond the scheme, any other systematic difference
   between the two sources carries the same risk.
4. **Internal duplication.** The file contains 10,066 exactly duplicated rows and 10,138
   duplicate URL strings.
5. **40 URL strings appear in both sources**, which would carry contradictory labels.
   Because the two sources write URLs differently, that count is a **lower bound**.

## 4. Acquisition tooling

| File | Purpose |
| --- | --- |
| `scripts/acquisition_common.py` | Shared helpers: paths, UTC stamps, SHA-256, secret redaction, provenance writing, overwrite guard |
| `scripts/acquire_phishtank.py` | Downloads the PhishTank `online-valid` feed and writes a provenance sidecar |
| `scripts/register_manual_download.py` | Fallback: verifies and registers a browser-downloaded feed file with the same provenance record |
| `scripts/acquire_kaggle.py` | Downloads both Kaggle candidates via the official Kaggle API into separate folders |
| `scripts/inspect_datasets.py` | Read-only inspection producing measured statistics into `reports/dataset_inspection/` |
| `scripts/requirements-acquisition.txt` | Minimal dependencies for this stage (no ML packages) |

Design rules enforced by the tooling:

* **No credential is hard-coded.** `PHISHTANK_APP_KEY`, `KAGGLE_USERNAME` and
  `KAGGLE_KEY` are read from the environment; keys are redacted before any URL is
  written to a metadata file.
* **Raw data is never overwritten.** `refuse_overwrite()` aborts rather than replacing
  an existing raw file; filenames carry a UTC timestamp.
* **Raw data is never modified.** Downloads are written byte-for-byte; the Kaggle
  archive is preserved alongside the extracted originals.
* **Every download writes a provenance sidecar** (`*.metadata.json`) containing source,
  URL, retrieval time, HTTP status, `ETag`/`Last-Modified`, byte count, SHA-256 and
  runtime environment.
* **Inspection is read-only** and writes only into `reports/`.

---

## 5. How to run

The easiest route is `Anti_phishing_prototype.ipynb`, which wraps all three steps in
ordered cells. The equivalent shell commands are below.

Run every command from the **project root** (the folder containing `scripts/` and
`docs/`) — the scripts resolve paths relative to it.

### 5.1 Install dependencies

```
pip install -r scripts/requirements-acquisition.txt
pip show requests pandas kaggle       # record the resolved versions in §6
```

### 5.2 Credentials

Nothing is hard-coded. Set credentials for your platform:

**Windows PowerShell**

```powershell
$env:PHISHTANK_USER_AGENT = "phishtank/<your-username>"
# optional, only if you already hold a key:
# $env:PHISHTANK_APP_KEY = "<key>"
$env:KAGGLE_USERNAME = "<your-kaggle-username>"
$env:KAGGLE_KEY      = "<your-kaggle-key>"
```

**Windows Command Prompt**

```bat
set PHISHTANK_USER_AGENT=phishtank/<your-username>
set KAGGLE_USERNAME=<your-kaggle-username>
set KAGGLE_KEY=<your-kaggle-key>
```

**macOS / Linux (bash, zsh)**

```bash
export PHISHTANK_USER_AGENT="phishtank/<your-username>"
export KAGGLE_USERNAME="<your-kaggle-username>"
export KAGGLE_KEY="<your-kaggle-key>"
```

**Notebook / Google Colab** — `export` and `set` do **not** work in notebook cells.
Use `os.environ`, and on Colab read the values from Colab Secrets rather than typing
them into a cell:

```python
import os

os.environ["PHISHTANK_USER_AGENT"] = "phishtank/<your-username>"

from google.colab import userdata            # Colab only
os.environ["KAGGLE_USERNAME"] = userdata.get("KAGGLE_USERNAME")
os.environ["KAGGLE_KEY"] = userdata.get("KAGGLE_KEY")
```

**Credentials file alternative to the Kaggle variables.** Download `kaggle.json` from
<https://www.kaggle.com/settings> → API → *Create New Token*, then place it at:

| kaggle version | Location |
| --- | --- |
| ≥ 1.7 (current) | `~/.config/kaggle/kaggle.json` — Windows: `%USERPROFILE%\.config\kaggle\kaggle.json` |
| legacy fallback, still accepted | `~/.kaggle/kaggle.json` — Windows: `%USERPROFILE%\.kaggle\kaggle.json` |

On macOS/Linux run `chmod 600` on the file. Never commit it.

> The `kaggle` package authenticates **at import time**, so absent credentials fail
> before any acquisition code runs. `acquire_kaggle.py` catches this and prints the
> guidance above instead of a raw traceback.

### 5.3 Acquire and inspect

```
python scripts/acquire_phishtank.py
python scripts/acquire_kaggle.py
python scripts/inspect_datasets.py
```

In a notebook, prefix each with `!` (e.g. `!python scripts/acquire_phishtank.py`).

If the PhishTank download returns `403`, that is the documented keyless behaviour or a
Cloudflare challenge — retry later or from a different network before considering a
secondary source. The script records the failure in a `FAILED_*.metadata.json` sidecar
so unsuccessful attempts remain part of the research record.

### 5.4 Scope of the inspection step

`inspect_datasets.py` parses delimited text only: `.csv` / `.tsv`, optionally
`.gz`- or `.bz2`-compressed. Any other raw file is listed as *NOT INSPECTED* in the
run output rather than skipped silently. This is why `acquire_phishtank.py` currently
offers CSV only — the JSON and XML feeds carry extra per-phish detail fields
(`ip_address`, `cidr_block`, `announcing_network`, `rir`) that may be worth adopting
later, but that would require extending the inspection step in the same change.

---

## 6. Acquisition log

Filled from the `*.metadata.json` provenance sidecars. Every row reflects an executed
download.

| Date (UTC) | Source | Identifier | Outcome | Raw file | SHA-256 (first 16) | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-08-18T03:16Z | PhishTank | `online-valid` | **failed** | — | — | HTTP 429, rate limited; recorded as `FAILED_*.json` |
| 2026-08-18T03:19Z | PhishTank | `online-valid` | **failed** | — | — | HTTP 429, rate limited; recorded as `FAILED_*.json` |
| 2026-08-18T03:27Z | PhishTank | `online-valid` | **success** | `online-valid_20260818T032746Z.csv` | `ece3cda672a2e9e7` | 13.84 MB, HTTP 200, payload validated, 72,230 rows |
| 2026-08-17T03:47Z | Kaggle | `naserabdullahalam/phishing-email-dataset` | success | `phishing-email-dataset.zip` + 7 CSVs | — | 80.86 MB archive preserved |
| 2026-08-17T03:48Z | Kaggle | `subhajournal/phishingemails` | success | `phishingemails.zip` + 1 CSV | `5d4d5cd1` | 18.92 MB archive preserved |
| 2026-08-22T09:51Z | Kaggle | `sid321axn/malicious-urls-dataset` | success | `malicious-urls-dataset.zip` + `malicious_phish.csv` | `8d085ce1fb4e4621` | 17.75 MB archive; benign URL source |

### Resolved package versions

Record the actual versions used, so the acquisition can be reproduced exactly.

| Package | Constraint | Resolved version | Recorded on |
| --- | --- | --- | --- |
| requests | `>=2.31,<3` | — | — |
| pandas | `>=2.0,<3` | — | — |
| kaggle | `>=1.7.4,<1.8` | — | — |

---

## 7. Inspection results

**Measured 2026-08-22** by section 5 of `Anti_phishing_prototype.ipynb`. Full source:
`reports/dataset_inspection/inspection_20260822T100100Z.{json,md}`.

Every figure below is a **full-file count**. Nothing is sampled, no malformed rows were
encountered (0 across all ten files), and every label column was declared from the real
file header rather than inferred.

### 7.1 Email datasets

| Dataset | Rows | Cols | Label column | Class distribution | Exact dup rows | Dup body text | Blank body | Missing values |
| --- | ---: | ---: | --- | --- | ---: | ---: | ---: | --- |
| A/CEAS_08 | 39,154 | 7 | `label` | 1: 21,842 (55.78%) / 0: 17,312 (44.22%) | 0 | 795 | 0 | receiver 462, subject 28 |
| A/Enron | 29,767 | 3 | `label` | 0: 15,791 (53.05%) / 1: 13,976 (46.95%) | 0 | 407 | 0 | subject 198 |
| A/Ling | 2,859 | 3 | `label` | 0: 2,401 (83.98%) / 1: 458 (16.02%) | 0 | 0 | 0 | subject 62 |
| A/Nazario | 1,565 | 7 | `label` | 1: 1,565 (100%) | 0 | 38 | 2 | receiver 96, subject 4, date 1 |
| A/Nigerian_Fraud | 3,332 | 7 | `label` | 1: 3,332 (100%) | 0 | 61 | 1 | receiver 1,324, date 482, sender 331, subject 39 |
| A/SpamAssasin | 5,809 | 7 | `label` | 0: 4,091 (70.43%) / 1: 1,718 (29.57%) | 0 | 24 | 2 | receiver 210, subject 16, body 1 |
| A/phishing_email (aggregated) | 82,486 | 2 | `label` | 1: 42,891 (52.00%) / 0: 39,595 (48.00%) | 408 | 408 | 1 | none |
| B/Phishing_Email | 18,650 | 3 | `Email Type` | Safe 11,322 (60.71%) / Phishing 7,328 (39.29%) | 0 | 1,135 | 19 | Email Text 16 |

### 7.2 URL datasets

| Dataset | Rows | Label column | Class distribution | Exact dup rows | Dup URLs | URLs with explicit scheme |
| --- | ---: | --- | --- | ---: | ---: | ---: |
| PhishTank `online-valid` | 72,230 | none (single class) | all phishing | 0 | 3 | 72,230 (**100.00%**) |
| sid321axn `malicious_phish` | 651,191 | `type` | benign 428,103 (65.74%), defacement 96,457, phishing 94,111, malware 32,520 | 10,066 | 10,138 | 187,999 (**28.87%**) |

Usable URL supply: **428,103 benign** against **72,230 phishing**, a ratio of 5.93 : 1.
Whether and how to rebalance is a preprocessing decision and has not been made.

### 7.3 Label semantics — verified, not assumed

The corpora ship `0`/`1` labels with no codebook. The claim that `1` means phishing was
tested against corpora whose composition is fixed by origin:

| Evidence | Corpus | Measured | Consistent? |
| --- | --- | --- | --- |
| Decisive — phishing/fraud-only collection, must be ~100% `1` | A/Nazario | `1` = 100.00% | yes |
| Decisive — phishing/fraud-only collection, must be ~100% `1` | A/Nigerian_Fraud | `1` = 100.00% | yes |
| Corroborating — mixed corpus, must contain both classes | A/Ling | `1` = 16.02%, `0` = 83.98% | yes |
| Corroborating — mixed corpus, must contain both classes | A/Enron | `1` = 46.95%, `0` = 53.05% | yes |
| Corroborating — mixed corpus, must contain both classes | A/SpamAssasin | `1` = 29.57%, `0` = 70.43% | yes |

**Conclusion: `1` = phishing, `0` = legitimate** for candidate A, supported by measured
evidence.

> Note on method: Ling, Enron and SpamAssassin are *mixed* corpora containing both
> ordinary mail and spam. Expecting them to be overwhelmingly `0` would be a mistake
> about the corpora, not a finding about the labels; the test only requires that both
> classes are materially present.

### 7.4 Cross-dataset overlap — leakage risk

Shared content between datasets, compared after case and whitespace normalisation:

| Pair | Shared records |
| --- | ---: |
| A/SpamAssasin ↔ B/Phishing_Email | 155 |
| A/Enron ↔ B/Phishing_Email | 66 |
| A/Ling ↔ B/Phishing_Email | 62 |
| A/phishing_email ↔ B/Phishing_Email | 9 |
| 12 further pairs | 1–3 each |
| **URL benign source ↔ PhishTank** | **40** (lower bound) |

**The aggregated file of candidate A is its six corpora, re-encoded.** The six corpora
sum to 39,154 + 29,767 + 2,859 + 1,565 + 3,332 + 5,809 = **82,486 rows — exactly** the
row count of the aggregated file. Yet only 6 body texts match verbatim, because
`phishing_email.csv` stores text already lower-cased and stripped of punctuation while
the six corpora retain raw message bodies. They are **two representations of one corpus,
not two datasets**; using both would duplicate every record.

**Consequence:** these datasets cannot be concatenated and split naively. Deduplication
must precede the train/validation/test split (`FYP_Specification.md` §12). No
deduplication has been performed.

## 8. Primary dataset recommendation

Deferred until inspection results exist. Recording a recommendation now would
contradict the project rule that dataset properties must be observed before use.

---

## 9. Sources consulted

* PhishTank — Developer Information: https://phishtank.org/developer_info.php
* PhishTank — FAQ: https://phishtank.org/faq.php
* PhishTank — Registration status: https://phishtank.org/register.php
* Kaggle — Candidate A: https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset
* Kaggle — Candidate B: https://www.kaggle.com/datasets/subhajournal/phishingemails
* IEEE Xplore — Curated Datasets and Feature Analysis for Phishing Email Detection with Machine Learning (ICMI 2024): https://ieeexplore.ieee.org/document/10585821/
