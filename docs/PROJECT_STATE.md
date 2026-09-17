# FYP2 Development State

> Purpose: single source of truth for "Where are we now?".
> Update this file at the end of every working session or whenever a stage, dataset, model, experiment, or result changes.
> Last updated: 2026-09-17

## Current Stage

**Dataset acquisition, inspection, preprocessing and URL feature engineering COMPLETE.
BERT contextual feature extraction IMPLEMENTED AND VERIFIED, but NOT YET RUN IN FULL.**

CRISP-DM position: **modelling, feature representation stage.** Both branches of the
approved architecture now have their feature extraction code written and tested. The URL
branch has its 35 lexical/structural features for train and validation. The BERT branch
runs correctly end to end but has so far only been executed over a **512-row sample per
split**, because a full pass needs a GPU. Nothing has been trained.

| Thread | State |
| --- | --- |
| Email corpora (Kaggle, 2 candidates) | acquired 2026-08-17, measured 2026-08-22, primary selected and preprocessed 2026-09-10 |
| Phishing URLs (PhishTank) | acquired 2026-08-18 and 2026-08-22, measured 2026-08-22, preprocessed 2026-09-10 |
| Legitimate URLs (Kaggle `sid321axn`) | acquired and measured 2026-08-22, preprocessed 2026-09-10 |
| Model environment (Stage 0) | complete and verified 2026-08-16 |
| Train/validation/test splits | created 2026-09-10, leakage-checked, test set untouched |
| URL lexical/structural features | 35 features extracted 2026-09-15 for train + validation; test deferred |
| **URL BERT features** | **code verified 2026-09-17 on 512 rows/split; FULL RUN PENDING on GPU** |
| **Email BERT features** | **code verified 2026-09-17 on 512 rows/split; FULL RUN PENDING on GPU** |
| XGBoost training | not started |

**Do not train anything yet.** The `.npy` files currently under `data/features/` carry the
`subset512` tag and hold 512 rows per split, not the full data. They exist to prove the
extraction code is correct, and are not a usable feature set.

## Completed

* **BERT contextual feature extraction implemented, tested and verified** (2026-09-17):
  section 8 of `Anti_phishing_prototype.ipynb` (8.1 helpers, 8.2 self-test, 8.3 settings,
  8.4 extraction, 8.5 verify/measure/write). Notebook grew 73 → 84 cells. All five new
  code cells executed in a live kernel with 0 errors, without re-running sections 2 to 7.
  Self-test: **24 of 24 assertions passed**, inside the notebook. Frozen
  `bert-base-uncased`, mean pooling, 768 dimensions per record.

* FYP1 methodology established
* Research objectives established
* BERT + XGBoost approach selected
* Google Colab selected for ML execution
* VS Code selected as development workspace
* Claude Code selected as development agent
* Project instruction file (CLAUDE.md) created
* `docs/FYP_Specification.md` created — intended system definition
* `docs/PROJECT_STATE.md` created — this file
* PhishTank access method investigated and verified against official documentation (2026-08-13)
* Kaggle email dataset candidates identified and shortlisted to two
* `docs/DATASET_SOURCES.md` created
* Reproducible acquisition scripts written and tested against synthetic fixtures
* Project data/report directory structure created
* Acquisition notebook rebuilt as proper ordered cells
* Code review findings from Claude Code addressed (see Change Log, 2026-08-13)
* Modelling library stack selected and justified against the specification
* **Stage 0 — Model Environment Setup completed and executed** (2026-08-16):
  section 1 of `Anti_phishing_prototype.ipynb`, all 5 code cells run with no errors
* **Kaggle dataset acquisition completed and executed** (2026-08-17): section 2 of
  `Anti_phishing_prototype.ipynb`, both candidates downloaded, archives preserved,
  provenance sidecars written
* **PhishTank snapshot acquired** (2026-08-18, 03:27:48 UTC): 72,230 verified online
  phishing URLs, payload validated, raw file and provenance preserved
* **Benign URL source selected and acquired** (2026-08-22): section 4 of the notebook —
  `sid321axn/malicious-urls-dataset`, `benign` rows only, closing the single-class gap
  that made supervised URL classification impossible
* **Dataset inspection completed and executed** (2026-08-22): section 5 of the notebook —
  all 10 CSVs measured in full passes; report written to
  `reports/dataset_inspection/inspection_20260822T100100Z.{json,md}`
* **Primary email dataset selected** (2026-09-10): candidate A's six corpora, on measured
  evidence — see "Primary Email Dataset Decision" below
* **Preprocessing completed and executed** (2026-09-10): section 6 of
  `Anti_phishing_prototype.ipynb` — cleaning, deduplication, source-leak neutralisation,
  class balancing and the stratified split; 8 code cells executed with 0 errors;
  83-assertion self-test passed; outputs written to `data/processed/` and
  `reports/preprocessing/`
* **URL lexical and structural feature engineering completed and executed**
  (2026-09-15): section 7 of `Anti_phishing_prototype.ipynb` — 35 numeric features per
  URL, 5 code cells executed with 0 errors, 164-assertion self-test passed, outputs
  written to `data/features/url/` and `reports/features/`. See "URL Engineered Features"
  below

## Version Control

**This folder IS a git repository** (corrected 2026-09-17 — the previous entry said it was
not). Branch `main`.

A `.gitignore` was added on 2026-09-17, and it mattered: **every file in the project had
already been staged with `git add`, including `Legacy_API_Credential(Kaggle)/kaggle.json`
and roughly 670 MB of raw and processed data.** Committing that would have written a live
API credential permanently into git history, where deleting it later does not remove it.
The index was cleared and rebuilt before the first commit was ever made.

Tracked: the notebook, `docs/`, `scripts/`, `src/`, `reports/`, `data/metadata/`
provenance sidecars, `CLAUDE.md`, the FYP1 report — about **1 MB** in total.

Not tracked: `data/raw/`, `data/processed/`, `data/features/`, `*.npy`, `*.zip`,
credentials, `__pycache__/`, `backups/`. The data is excluded on size, and is
reproducible: `data/metadata/` records the identifier, retrieval time, byte count and
SHA-256 of every raw file, so it can be re-acquired and checked.

## Acquired Datasets (measured on disk, 2026-08-17 and 2026-08-22)

Downloaded by section 2 of `Anti_phishing_prototype.ipynb`. Sizes are **observed file
sizes**, not dataset-page claims. Row counts and class balance were **measured on
2026-08-22** and appear under "Current Dataset" below.

### Candidate A — `naserabdullahalam/phishing-email-dataset`

Archive `phishing-email-dataset.zip`, 80.86 MB, preserved alongside 7 extracted CSVs:

| File | Size |
| --- | ---: |
| `phishing_email.csv` | 106.60 MB |
| `CEAS_08.csv` | 67.90 MB |
| `Enron.csv` | 45.56 MB |
| `SpamAssasin.csv` | 14.88 MB |
| `Ling.csv` | 9.34 MB |
| `Nigerian_Fraud.csv` | 9.19 MB |
| `Nazario.csv` | 7.81 MB |

### Candidate B — `subhajournal/phishingemails`

Archive `phishingemails.zip`, 18.92 MB (SHA-256 `5d4d5cd1…b821be`), preserved alongside:

| File | Size |
| --- | ---: |
| `Phishing_Email.csv` | 52.03 MB |

### Benign URL source — `sid321axn/malicious-urls-dataset` (added 2026-08-22)

Archive `malicious-urls-dataset.zip`, 17.75 MB (SHA-256 `8d085ce1…69ca79`), preserved
alongside `malicious_phish.csv` (45.66 MB). Only its **`benign`** rows are used by this
project; its phishing/defacement/malware rows are deliberately unused, because PhishTank
is the approved primary phishing-URL source.

Total under `data/raw/kaggle/`: **15 files, 476.5 MB**. Provenance sidecars
(`<owner>.metadata.json`) record identifier, retrieval time, byte counts and SHA-256 for
every archive and extracted file.

## PhishTank Acquisition Module (2026-08-18)

**`src/data/phishtank.py`** — reusable, callable from any notebook or script:

```python
from src.data.phishtank import fetch_phishtank_dataset
df = fetch_phishtank_dataset()                    # reuses a recent snapshot
df = fetch_phishtank_dataset(force_refresh=True)  # forces a new download
path = fetch_phishtank_dataset(load=False)        # raw file path only
```

| Aspect | Implementation |
| --- | --- |
| Source | `http://data.phishtank.com/data/online-valid.csv` |
| Authentication | keyless by default; `PHISHTANK_APP_KEY` inserted into the path only if set; key redacted before logging or writing |
| User-Agent | `phishtank/fyp2-anti-phishing-research`, overridable via `PHISHTANK_USER_AGENT` |
| Raw snapshot | `data/raw/phishtank/online-valid_<UTCSTAMP>.csv`, exact bytes, never overwritten |
| Metadata | `data/metadata/phishtank/<name>.json` — source URL, retrieval time, filename, size, HTTP status, ETag, SHA-256, whether a key was used, runtime |
| Failed attempts | recorded as `FAILED_<stamp>.json`, so unsuccessful acquisition stays in the research record |
| Caching | a snapshot younger than `max_age_hours` (default 6) is reused; `force_refresh=True` overrides |
| Payload validation | downloads to a temp file first; rejects HTML/XML bodies and headers missing the documented fields, so a Cloudflare page served with HTTP 200 can never be stored as data |
| Return value | `pandas.DataFrame` with provenance in `df.attrs`, or `Path` when `load=False` |
| Scope | download → save → metadata → load only; no cleaning, feature engineering, splitting or modelling |

**Module test result (2026-08-18): 34 of 34 assertions passed** against a local HTTP
server serving a synthetic feed with the real PhishTank schema — covering successful
acquisition, byte-exact preservation, SHA-256, metadata completeness, pandas load, all
eight expected columns, cache reuse, `force_refresh` without overwrite, rejection of a
Cloudflare 200/HTML payload, and an actionable 403. Synthetic data was written to a
temporary root and never entered `data/raw/`.

**Live feed result: FAILED — HTTP 429 (rate limited)**, at 03:16 and 03:19 UTC on
2026-08-18. No real snapshot exists, so the module's behaviour on genuine PhishTank
data is verified only against the synthetic fixture.

## Not Yet Done

* **The full BERT feature set does not exist.** Section 8 has been verified on 512 rows
  per split. The real pass needs `MAX_ROWS_PER_SPLIT = None` in section 8.3 on a GPU
  runtime. This is the immediate next task.
* No BERT features for the **test** split — deferred with the same reasoning as the URL
  features.
* No URL features for the **test** split — deliberately deferred.
* No email engineered features. None are planned: Specification §6 gives the email branch
  BERT only, and §9 gives lexical/structural features to the URL branch alone.
* No XGBoost training, no baseline models, no evaluation.
* No GPU verified for this project — the only environment executed so far is CPU-only.
* No web prototype.

## Primary Email Dataset Decision (2026-09-10)

**Chosen: candidate A's six corpora.** 82,486 rows, intact message bodies, and a subject
field. Recorded here as required before preprocessing could begin.

The decision rests on a full-pass measurement of text representation taken on 2026-09-10,
which corrected an assumption in the previous entry. Candidate A does **not** hold six raw
corpora — it holds four:

| Corpus | Rows | Rows with an uppercase letter | Rows with spaced punctuation | Representation |
| --- | ---: | ---: | ---: | --- |
| A/CEAS_08 | 39,154 | 98.55% | 3.14% | raw |
| A/Nazario | 1,565 | 99.04% | 12.46% | raw |
| A/Nigerian_Fraud | 3,332 | 99.91% | 24.73% | raw |
| A/SpamAssasin | 5,809 | 99.78% | 7.13% | raw |
| A/Enron | 29,767 | **0.00%** | 92.79% | pre-normalised |
| A/Ling | 2,859 | **0.00%** | 99.30% | pre-normalised |
| A/phishing_email | 82,486 | 0.00% | 0.00% | normalised **and punctuation stripped** |
| B/Phishing_Email | 18,650 | 29.59% | 66.43% | mostly normalised |

Why the six corpora win anyway:

* **The aggregated file is excluded outright.** 0.00% spaced punctuation means its
  punctuation is not spaced out but *deleted*, and that is unrecoverable. BERT needs raw
  text (Specification §9).
* **Candidate B was rejected**: 4.4× less data, no subject field, and 66.43% of its rows
  already punctuation-spaced.
* **The mixed representation inside candidate A is a measured, accepted limitation.**
  `bert-base-uncased` lower-cases its input, so the tokeniser removes the casing half of
  the difference before the model sees it. Casing was also measured to be a *weak* label
  predictor — 56.60% phishing among cased rows against 45.18% among lower-cased rows — not
  the near-perfect source detector the URL scheme was.

## Files Created This Stage

| File | Purpose |
| --- | --- |
| `scripts/acquisition_common.py` | Shared provenance, hashing, redaction and overwrite-guard helpers |
| `scripts/acquire_phishtank.py` | PhishTank `online-valid` feed acquisition |
| `scripts/register_manual_download.py` | Fallback path: registers a browser-downloaded feed with identical provenance |
| `scripts/acquire_kaggle.py` | Kaggle acquisition for both candidate email datasets |
| `scripts/inspect_datasets.py` | Read-only inspection producing measured dataset statistics |
| `scripts/requirements-acquisition.txt` | Stage dependencies (no ML packages) |
| `docs/DATASET_SOURCES.md` | Source records, justification, limitations, acquisition log |
| `Anti_phishing_prototype.ipynb` | Notebook runner for the acquisition scripts (Colab-ready) |
| `data/raw/phishtank/` | Raw PhishTank snapshots (empty) |
| `data/raw/kaggle/naserabdullahalam/` | Raw candidate A (empty) |
| `data/raw/kaggle/subhajournal/` | Raw candidate B (empty) |
| `reports/dataset_inspection/` | Inspection output — **populated 2026-08-22** |
| `data/raw/kaggle/sid321axn/` | Benign URL source, archive + CSV + provenance sidecar |
| `reports/dataset_inspection/inspection_20260822T100100Z.json` | Machine-readable measured dataset properties |
| `reports/dataset_inspection/inspection_20260822T100100Z.md` | Quotable measured dataset properties |
| `data/processed/email/{train,validation,test}.csv` | **Added 2026-09-10** — cleaned, deduplicated, split email data |
| `data/processed/url/{train,validation,test}.csv` | **Added 2026-09-10** — cleaned, neutralised, balanced, split URL data |
| `reports/preprocessing/preprocessing_<UTCSTAMP>.json` | **Added 2026-09-10** — every figure section 6 measured |
| `data/features/url/{train,validation}.csv` | **Added 2026-09-15** — 35 lexical/structural features per URL |
| `reports/features/url_features_20260915T030436Z.json` | **Added 2026-09-15** — every figure section 7 measured |

## Current Dataset

All figures below are **measured** (full-file counts, 2026-08-22), never taken from
dataset pages. Source of truth:
`reports/dataset_inspection/inspection_20260822T100100Z.md`.

### Email data

| Dataset | Rows | Label column | Phishing | Legitimate |
| --- | ---: | --- | ---: | ---: |
| A/CEAS_08 | 39,154 | `label` | 21,842 | 17,312 |
| A/Enron | 29,767 | `label` | 13,976 | 15,791 |
| A/Ling | 2,859 | `label` | 458 | 2,401 |
| A/Nazario | 1,565 | `label` | 1,565 | 0 |
| A/Nigerian_Fraud | 3,332 | `label` | 3,332 | 0 |
| A/SpamAssasin | 5,809 | `label` | 1,718 | 4,091 |
| A/phishing_email (aggregated) | 82,486 | `label` | 42,891 | 39,595 |
| B/Phishing_Email | 18,650 | `Email Type` | 7,328 | 11,322 |

**Label meaning verified, not assumed:** `1` = phishing, `0` = legitimate. Nazario and
Nigerian_Fraud are phishing/fraud-only collections and measured 100.00% `1`; the mixed
corpora (Ling, Enron, SpamAssassin) each contain both classes, as they must.

**The aggregated file is not a ninth dataset.** The six corpora sum to exactly 82,486
rows — the aggregated file's row count — but only 6 body texts match verbatim, because
`phishing_email.csv` stores pre-normalised text (lower-cased, punctuation stripped) while
the six corpora keep raw bodies. Two representations of one corpus.

### URL data

| Class | Source | Rows | Notes |
| --- | --- | ---: | --- |
| Phishing | PhishTank `online-valid_20260818T032746Z.csv` | 72,230 | single-class; 3 duplicate URLs |
| Legitimate | `malicious_phish.csv`, `benign` rows only | 428,103 | of 651,191 rows total |

Ratio benign : phishing = **5.93 : 1** against the 08-18 snapshot, **5.87 : 1** against
the pinned 08-22 one. **Decided 2026-09-10:** undersample the legitimate class to 1:1 at
seed 42 — see "Processed Dataset" above.

### Data quality issues found (all ADDRESSED in preprocessing, 2026-09-10)

Measured during inspection while still unaddressed; see "Processed Dataset" above for
what each one cost. The counts below are the section 5 figures and are left unchanged.

| Issue | Measured |
| --- | --- |
| Malformed/unparseable rows | **0** across all ten files |
| Exact duplicate rows | 408 (aggregated file), 10,066 (URL benign source) |
| Duplicate content after normalisation | 795 CEAS, 1,135 candidate B, 10,138 URL source, others smaller |
| Blank content rows | 19 (candidate B), small counts elsewhere |
| Missing values | subject/receiver/sender/date fields; 16 missing `Email Text` in candidate B |
| Cross-dataset shared records | 155 / 66 / 62 for the largest pairs, plus 12 smaller pairs |
| URLs claimed by both URL sources | 40 (lower bound — contradictory labels) |

## Processed Dataset (produced 2026-09-10, section 6)

Every figure below was printed by the executed notebook cells and is recorded in
`reports/preprocessing/preprocessing_<UTCSTAMP>.json`.

### Email — candidate A, six corpora

| Step | Rows |
| --- | ---: |
| Loaded | 82,486 |
| Blank content removed | 1 |
| Duplicate copies removed | 1,840 |
| Contradictory rows removed (1 key labelled both ways) | 2 |
| **Kept** | **80,643** (97.77%) |

Class balance after cleaning: 41,480 phishing (51.44%), 39,163 legitimate (48.56%).

### URL — PhishTank vs sid321axn benign

| Step | Rows |
| --- | ---: |
| Loaded (72,901 phishing + 428,103 legitimate) | 501,004 |
| Duplicate copies removed | 3,730 |
| Contradictory rows removed (1 key labelled both ways) | 2 |
| Kept after deduplication | 497,272 (70,245 phishing, 427,027 legitimate) |
| **After undersampling legitimate to 1:1, seed 42** | **140,490** (70,245 / 70,245) |

Of PhishTank's 72,901 rows, **2,656 were merged by normalisation** — the same page written
with or without a trailing slash, or in different casing. Section 5 measured only 3 exact
duplicates because it compared raw strings; these collapse only after neutralisation, and
left separate they would have been a plain train/test leak.

### Train/validation/test split

Stratified 70/15/15, seed 42, performed **after** deduplication.

| Task | Train | Validation | Test | Phishing share |
| --- | ---: | ---: | ---: | ---: |
| Email | 56,450 | 12,096 | 12,097 | 51.44% in each |
| URL | 98,344 | 21,074 | 21,072 | 50.00% in each |

**Leakage verification: 0 shared duplicate keys** across all six split pairs (train/test,
train/validation, validation/test, for both tasks). The cell raises and writes nothing if
any pair is non-zero.

**Reproducibility verified by execution**, not asserted: the pipeline was run twice in
separate processes, and all six output CSVs were **byte-identical (SHA-256)**.

Output files:

| Path | Rows | Size |
| --- | ---: | ---: |
| `data/processed/email/train.csv` | 56,450 | 93.34 MB |
| `data/processed/email/validation.csv` | 12,096 | 24.08 MB |
| `data/processed/email/test.csv` | 12,097 | 19.65 MB |
| `data/processed/url/train.csv` | 98,344 | 6.64 MB |
| `data/processed/url/validation.csv` | 21,074 | 1.41 MB |
| `data/processed/url/test.csv` | 21,072 | 1.41 MB |

Email columns: `source`, `text` (subject + body), `label`.
URL columns: `source`, `url` (scheme-neutralised), `label`.
`1` = phishing, `0` = legitimate, in both tasks.

The duplicate-detection key is deliberately **not** saved: it exists to detect duplicates,
not to be fed to a model.

### Preprocessing rules applied

| Rule | Why, measured |
| --- | --- |
| Email text = subject + body | subject carries phishing signal; missing in only 347 of 82,486 rows |
| Email duplicate key = **body only**, lower-cased, punctuation removed | catches the same message across candidate A's two representations; body-only collapses to 80,626 distinct keys against 81,504 for subject+body, so it removes 878 more near-duplicates (1.06%) |
| URL scheme removed | 100.00% PhishTank vs **8.26%** benign |
| URL trailing slash removed | 33.05% vs 25.98% |
| URL casing kept | 38.16% vs 34.66% — not source-identifying |
| URL `www.` kept | 4.13% vs 3.09% — not source-identifying |
| Contradictory records: **every** copy dropped | picking a winner would be inventing data |

## Processed Split Integrity (hashes recorded 2026-09-15)

Recorded because a modification time proved too weak to carry the "untouched" claim
(known problem 22). These are the SHA-256 digests of the six files section 6 produces.
Section 6 is reproducible — the 2026-09-10 change log records the same pipeline run twice
in separate processes producing byte-identical output — so **any future re-run must
reproduce these digests exactly.** A mismatch means the inputs or the code changed and the
splits are no longer the ones every recorded figure was measured on.

| File | SHA-256 |
| --- | --- |
| `data/processed/email/train.csv` | `e62762e07798a58a6cb7eda31fc75918a35fcbf44b2f133c4ccc8be920e9ba43` |
| `data/processed/email/validation.csv` | `3be74a1b56adbf90f31bacd198215cc56cc57de8c6a6aa463de811b2af01deae` |
| `data/processed/email/test.csv` | `555348f63578bac132d146b9b2c95e3069fcd2a871cdebe9bca55a2f82e0cdff` |
| `data/processed/url/train.csv` | `e9f7fdb33d7f1b2e0dd02c3716ad3a3d59c301986bf6b06a7ca78541ddaba01a` |
| `data/processed/url/validation.csv` | `5388a53bb4479c57b18759bb67c77f8a4ebcea5438ab02fe4495e50e7e339a0a` |
| `data/processed/url/test.csv` | `2fa0db9e85f1689bd324966e40398fd8a0403e03aed13b79b2e8bf7a14d01475` |

And the engineered URL features, for the same reason:

| File | SHA-256 |
| --- | --- |
| `data/features/url/train.csv` | `53b5ee4ab385b53f58c3e66fcf7b9105b0a3a5284068338af327d438a33eda03` |
| `data/features/url/validation.csv` | `06e616305e2029b68e47f4e807d372041a0042df101e69bd33e33894c46af244` |

## URL Engineered Features (produced 2026-09-15, section 7)

Specification §6 gives the URL branch **two** feature blocks: a BERT representation of the
URL string, and lexical/structural features computed from the string itself. Section 7
produces the second block. Every figure below was printed by the executed notebook cells
and is recorded in `reports/features/url_features_20260915T030436Z.json`.

### What was produced

| Split | Rows in | Feature rows out | Size | Time |
| --- | ---: | ---: | ---: | ---: |
| `data/features/url/train.csv` | 98,344 | 98,344 | 14.34 MB | 3.4 s |
| `data/features/url/validation.csv` | 21,074 | 21,074 | 3.06 MB | 0.71 s |
| test | — | **not produced** | — | — |

Columns: `url`, `label`, then the 35 features. `url` and `label` are carried for
traceability; **`FEATURE_NAMES` in notebook cell 7.1 is the authoritative list of model
inputs** and the URL string is never fed to XGBoost. Row order is identical to the
processed split files, so the BERT vectors produced later from the same files align by
position with no join key.

### The 35 features

| Group | Count | Features |
| --- | ---: | --- |
| Whole-URL lexical | 9 | length, digit count, digit ratio, letter ratio, uppercase ratio, special-character count, Shannon entropy, token count, longest token length |
| Punctuation counts | 9 | `.` `-` `_` `/` `?` `=` `@` `&` `%` |
| Host / structural | 10 | length, dots, hyphens, digits, subdomain count, TLD length, is-an-IP, has-a-port, has-punycode, has-`www.` |
| Path / query / fragment | 5 | path length, path depth, query length, query parameter count, has-fragment |
| Nested URL | 1 | embedded URL count (open-redirect abuse) |
| Content words | 1 | suspicious word count |

`url_uppercase_ratio` and `host_has_www` are permitted **only because** section 6 measured
them not to identify the source (38.16% vs 34.66% for casing, 4.13% vs 3.09% for `www.`),
which is why preprocessing kept both instead of stripping them.

### Why this stage cannot leak

Every feature is computed from **one URL string on its own** — no vocabulary, no scaler,
no learned mean, no threshold. There is **no fitted parameter**, so nothing can carry
training information into validation or test (Specification §12).

**The test split was still not read.** Not because extraction would leak — it would not —
but because this file records that nothing except the writer that created it has ever
opened it. At final evaluation, `"test"` is added to `FEATURE_SPLITS` in cell 7.3 and
cells 7.4 and 7.5 run unchanged, so the test features come from exactly the code that
produced the training ones.

**Correction, 2026-09-15.** An earlier version of this entry proved the point with a file
modification time, and that proof is now void: all six split files were rewritten at
02:53:36 UTC by a section 6 re-execution that is not accounted for (known problem 22). The
substantive guarantee is unaffected — re-running section 6 *writes* the test split, it does
not feed it to a model, and no feature, threshold or model has read it — but timestamps are
clearly too fragile to carry the claim. **Content hashes replace them**, see
"Processed Split Integrity" below.

### Verification (all passed; nothing is written if any fails)

| Check | Result |
| --- | --- |
| Self-test of the helpers, known-answer fixtures | **164 of 164 assertions passed** |
| Rows in == feature rows out | 98,344 and 21,074, exact |
| URLs still **beginning** with a scheme | **0** in both splits |
| Missing or negative feature values | **0** |
| Ratios outside 0–1, binaries other than 0/1 | **0** |
| Features constant on the training split | **0 of 35** |
| Reproducibility | pipeline run twice in separate processes; both CSVs **byte-identical by SHA-256** |

### What the features say about phishing URLs (Objective 1)

Measured on the **training split only**. Strongest class separation, where
`separation = |phishing mean − legitimate mean| ÷ overall mean`:

| Feature | Separation | Coverage | Phishing mean | Legitimate mean |
| --- | ---: | ---: | ---: | ---: |
| `host_is_ip` | 2.1429 | 0.074% | 0.0015 | 0.0000 |
| `has_fragment` | 1.8421 | 0.376% | 0.0073 | 0.0002 |
| `embedded_url_count` | 1.6377 | 0.617% | 0.0126 | 0.0013 |
| `host_has_punycode` | 1.5714 | 0.066% | 0.0012 | 0.0001 |
| `host_hyphen_count` | 1.3576 | **20.555%** | 0.5182 | 0.0991 |
| `host_has_port` | 1.3000 | 0.101% | 0.0016 | 0.0004 |
| `count_percent` | 1.2575 | 3.072% | 0.1239 | 0.5434 |
| `host_digit_count` | 1.2357 | **16.926%** | 1.8221 | 0.4304 |
| `count_at` | 1.1556 | 0.428% | 0.0071 | 0.0019 |
| `count_underscore` | 0.8691 | **14.875%** | 0.1919 | 0.4867 |

**The separation column must never be quoted on its own** — see known problem 19. Only
three of the ten (`host_hyphen_count`, `host_digit_count`, `count_underscore`) are both
strong and present in more than 5% of URLs. The other seven are sharp when they fire and
absent from almost every URL.

**No feature selection was performed.** The ranking is descriptive; XGBoost receives all
35 features.

**One measured result contradicts a common claim** and must be reported as measured, not
as expected: phishing URLs here are **shorter**, not longer — mean length 49.67 against
56.82 for legitimate, with fewer slashes (1.26 vs 2.31) and shorter paths (16.59 vs
32.22). This follows from the sources: the benign class is drawn from a general URL
collection in which 99.93% of rows carry a path. The phishing URLs are instead
distinguished by their **hosts** — longer (20.95 vs 16.67), more hyphens, more digits,
more subdomains.

### Decisions recorded for this stage

| Decision | Choice | Why |
| --- | --- | --- |
| Feature selection | **none** | XGBoost receives all 35; the separation ranking drops nothing |
| Constant features | reported, **not removed** | measured: none of the 35 is constant |
| Suspicious-word list | 14 terms, fixed in advance, **no brand names** | a list tuned on the training labels would be a fitted parameter; brand names chosen after seeing this data could not be defended as prior knowledge, and would not transfer to next year's targets |
| Network lookups | **none** — no WHOIS, DNS or page fetch | PhishTank lists only *currently-online* phishes, so a lookup made today would describe a different internet from the one the snapshot captured |
| Subdomain rule | labels minus two | simple and its error stated, rather than a public-suffix list to download, version and defend |
| Test split | **deferred** | preserves the audit trail; extraction itself could not leak |

## Current Model

Not yet implemented.

Planned architecture:

```
Input (email text / URL)
  → preprocessing
  → BERT feature extraction
  → XGBoost classification
  → phishing / legitimate result
```

## Modelling Environment (Stage 0 — verified by execution)

Implemented as **section 1 of `Anti_phishing_prototype.ipynb`** (subsections 1.1–1.5).
Each library is traceable to an approved requirement; nothing is included to make the
project appear more advanced.

Versions below were **measured** by executing the notebook on 2026-08-16, not declared.

| Library | Constraint | Approved role | Resolved version |
| --- | --- | --- | --- |
| numpy | `>=2.0,<3` | core numerical arrays | **2.3.3** |
| pandas | `>=2.0,<3` | tabular dataset handling | **2.3.2** |
| torch | `>=2.4,<3` | BERT backend (Specification §9) | **2.13.0+cpu** |
| transformers | `>=5.0,<6` | BERT feature extraction (Specification §9) | **5.15.0** |
| xgboost | `>=3.0,<4` | classification component (Specification §10) | **3.4.1** |
| scikit-learn | `>=1.5,<2` | accuracy/precision/recall/F1 + baselines (§11) | **1.9.0** |
| matplotlib | `>=3.8,<4` | evaluation figures for the report | **3.10.6** |
| seaborn | `>=0.13,<1` | confusion matrix / class-distribution plots | **0.13.2** |
| tqdm | `>=4.66,<5` | progress reporting for long extraction passes | **4.67.3** |
| joblib | `>=1.3,<2` | model and feature persistence | **1.5.2** |

Deliberately excluded, with reasons: `datasets` (pandas suffices for the CSV corpora),
`nltk` / `spacy` (classical NLP preprocessing is not in the approved method; BERT
supplies its own tokeniser), `lightgbm` / `catboost` (additional models beyond
BERT + XGBoost, CLAUDE.md rule 12), `optuna` / `shap` (optional later experiments),
`sentencepiece` (not required by `bert-base-uncased`).

### Measured runtime (2026-08-16)

| Item | Observed value |
| --- | --- |
| Python | 3.12.0 |
| Platform | Windows-11-10.0.26200-SP0 |
| Runtime | local VS Code kernel (not Colab) |
| CUDA available | **False** |
| torch built with CUDA | None (CPU-only wheel) |
| Selected device | `cpu` |
| Random seed | `42` (applied to `random`, `numpy`, `torch`, `PYTHONHASHSEED`) |
| Intended BERT checkpoint | `bert-base-uncased` (weights not downloaded) |

On Google Colab, `torch` is deliberately excluded from the install list because Colab
ships a torch build matched to its CUDA driver, and reinstalling from PyPI can replace
it with a CPU-only wheel — which is exactly the build that landed locally.

## Current Experiments

None.

## Current Results

None.

No results have been produced. Any figure appearing in the report before this section is populated is not experimentally supported.

## Known Problems

0. **The BERT features on disk are a 512-row sample, not the real feature set.** Recorded
   2026-09-17. Files are tagged `bert_subset512` precisely so they cannot be mistaken for
   a full run; a limited run and a full run write to separate folders and section 8.1
   refuses to join shards whose row counts do not match the split. Nothing may be trained
   until the full pass has been produced on a GPU.

1. **PhishTank application keys are unobtainable.** New user registration is
   temporarily disabled (verified 2026-08-13), so the project must run keyless:
   a few downloads per day, with frequent Cloudflare `403` responses.
   Agreed handling: keep PhishTank as primary; introduce a second URL source only
   if this materially blocks the experiments. Re-checked 2026-08-16: the wording is
   still "temporarily disabled". Claims elsewhere of a separate unrestricted "public
   data dump" that bypasses the limit were checked and are false — it is the same
   host, same URLs, same limit. A manual-download fallback with equivalent
   provenance is provided instead (`scripts/register_manual_download.py`).
2. **RESOLVED 2026-08-22 — benign URL source.** The `benign` rows of
   `sid321axn/malicious-urls-dataset` (428,103 URLs) are now the legitimate class. A
   popularity list was rejected because Tranco/Majestic/Umbrella publish bare domains,
   which against PhishTank deep links would make the task artificially easy. **This
   introduced known problem 14** — read it before preprocessing.
3. **PhishTank snapshots are not reproducible.** The feed reflects currently-online
   phishes only, so a later re-download yields different data. The first retrieved
   snapshot must be preserved and cited.
4. **RESOLVED 2026-08-22 — Kaggle dataset properties.** All row counts, columns and
   class distributions in `docs/DATASET_SOURCES.md` §7 are now measured by full-file
   passes and traceable to `reports/dataset_inspection/inspection_20260822T100100Z.json`.
5. **RESOLVED 2026-09-10 — duplicate risk across corpora.** Deduplication now runs in
   section 6.5/6.6 **before** the split, and the split is verified afterwards to share 0
   duplicate keys between train, validation and test for both tasks. Removed: 1,840
   duplicate emails and 3,730 duplicate URLs, plus every copy of the 2 keys that carried
   contradictory labels. The cross-dataset overlaps below involved candidate B, which is
   not used. Original entry, kept for the record: Confirmed
   2026-08-22: 16 overlapping dataset pairs, largest being SpamAssassin ↔ candidate B
   (155 shared records), Enron ↔ candidate B (66), Ling ↔ candidate B (62). Within
   files: 408 exact duplicate rows in the aggregated file, 10,066 in the URL benign
   source, and 1,135 duplicate email texts in candidate B. **Deduplication must happen
   before the train/validation/test split** or the evaluation is contaminated.
6. **Platform risk.** Talos has announced a full PhishTank rewrite with no timeline.
7. **`acquire_phishtank.py` cannot detect a Cloudflare page served as HTTP 200.**
   Verified by simulation on 2026-08-16: an HTML challenge body is written to
   `online-valid_<stamp>.csv.gz`, hashed, and recorded with `"outcome": "success"` and
   exit code 0. The response `Content-Type` is stored but never checked. This would put
   a **false success into the acquisition log**. `register_manual_download.py` does
   validate content (HTML detection, header match, row count); the automated path does
   not. Fix before relying on an automated download, or prefer the manual route.
8. **`scripts/requirements-acquisition.txt` contains a false verification claim.**
   It states "Verified on PyPI 2026-08-13: the `kaggle` package has NO 2.x release".
   `pip index versions kaggle` on 2026-08-16 returned latest **2.2.4**, with the 1.8.x
   and 2.x lines published. The pin `>=1.7.4,<1.8` is itself sound; only the stated
   justification is wrong and must be corrected under CLAUDE.md rule 3.
9. **PARTLY RESOLVED — the Kaggle API key is out of the notebook, but still on disk.**
   Confirmed 2026-09-17: notebook cell 2.1 no longer contains the token and reads
   `~/.kaggle/kaggle.json` instead. The real key still sits in
   `Legacy_API_Credential(Kaggle)/kaggle.json`, which is now git-ignored so it cannot be
   committed. **Still outstanding:** expire that token at kaggle.com/settings → API, since
   it was previously embedded in a notebook that may have been shared. Superseded text of
   the original problem: Section 2.1 of
   `Anti_phishing_prototype.ipynb` contains the plaintext legacy token for account
   `xiangyang2939`, at the owner's explicit request (2026-08-17). It is also written to
   `%USERPROFILE%\.kaggle\kaggle.json` at runtime. **Action required before the notebook
   is shared, submitted or committed:** delete the key from cell 2.1 and expire it at
   kaggle.com/settings → API. Resolved along the way: the earlier `~/.config/kaggle/`
   claim was wrong — `~/.kaggle/kaggle.json` is the location that actually worked with
   kaggle 1.7.4.5.
10. **SUPERSEDED 2026-08-22 — `scripts/inspect_datasets.py` is no longer used.** Its
    three verified defects (silent dropping of malformed rows, guessed label column,
    sampled rather than full-file statistics) are all fixed in **section 5 of
    `Anti_phishing_prototype.ipynb`**, which is now the source of truth for dataset
    properties. The script is left on disk, unmodified, but must not be run for figures.
    The replacement logic was tested against fixtures with known answers before use —
    33 assertions, including one regression test per defect.
11. **No GPU in the verified environment — now the binding constraint.** Re-measured
    2026-09-17 with section 8: full BERT extraction on this CPU would take about **4.8
    hours** (68,546 emails at 5.6 rows/s with `max_length` 256 ≈ 203 min; 119,418 URLs at
    23 rows/s with `max_length` 128 ≈ 87 min). Length-sorted dynamic padding is already
    applied. This is why the full pass is deferred to Colab. Original entry:
    Measured 2026-08-16: `torch 2.13.0+cpu`,
    `torch.cuda.is_available() == False`. PyPI's Windows torch wheel is CPU-only, so
    BERT feature extraction over ~10^5 emails is not practical on this machine. Plan to
    run the extraction pass on a Colab GPU runtime; section 1.2 of the notebook already
    skips the torch install on Colab to preserve its CUDA build.
12. **`tqdm.auto` warns `IProgress not found`** because `ipywidgets` is not installed.
    Harmless — progress bars fall back to plain text — but install `ipywidgets` if
    graphical bars are wanted during long extraction runs.
13. **VS Code silently overwrote the notebook during editing.** On 2026-08-16 an open
    VS Code notebook buffer twice clobbered externally written cells, deleting the
    `title` and `# 1. Model Environment Setup` cells and truncating the final cell.
    Both were restored and re-verified by re-execution. **Close the notebook in VS Code
    before any external tool edits it**, or content is lost without warning.
    **Third occurrence, 2026-09-15 — the worst so far.** At 11:13 local an open VS Code
    buffer holding the 10:30 pre-section-7 version saved itself over the finished file,
    silently deleting **all of section 7** (10 cells, ~111 KB) and the 21 section 6
    comment edits made at 11:08. The notebook fell back to 62 cells whose closing
    markdown still read "feature engineering — not implemented", while
    `data/features/url/*.csv` and `reports/features/url_features_20260915T030436Z.json`
    sat on disk, written at 11:04. **Nothing on disk warned that the notebook and its
    own outputs disagreed.**
    **Recovered the same day, without re-running anything.** The previous session's
    scratchpad still held the five final cell sources and the captured stdout of the
    11:04 run. Re-executing those five sources in a fresh process against
    `data/processed/url/` reproduced **both feature CSVs byte for byte** (SHA-256 equal:
    train `53b5ee4a…33eda03`, validation `06e61630…94c46af2`) and reproduced every line
    of stored output except the report's wall-clock timestamp — which is what proves the
    restored cells are the cells that made the files on disk. Sections 1-6 were then
    shown by AST comparison to have identical executable code, identical stored outputs
    and unchanged execution counts, so sections 2-4 were never re-run.
    **Lesson, now non-negotiable:** the notebook must be closed in VS Code before any
    external write, and a backup taken immediately before it. Recovery worked only
    because a scratchpad happened to survive; it is not a recovery plan.
14. **RESOLVED 2026-09-10 — URL formatting identified the source.** The scheme is now
    stripped from every URL in both sources, and section 6.6 **re-measures** the balanced
    set afterwards and raises if a single URL still carries one (measured: 0 of 140,490).
    **The original figure was also wrong and is corrected here.** This entry quoted
    28.87% of the benign source as carrying a scheme; that was computed over all 651,191
    rows of `malicious_phish.csv`. Over the **428,103 `benign` rows the project actually
    uses it is 8.26%**, against 100.00% for PhishTank — so the leak was worse than
    recorded, not milder.
    **Residual, and not removable:** 93.77% of PhishTank URLs contain a path against
    99.93% of benign URLs. Unlike the scheme this cannot be stripped without destroying
    the URL, so it stays a source signal and any strong URL result must be read against it.
    **Measured consequence, 2026-09-15:** section 7.5 checks whether any path-shaped
    feature (`path_length`, `path_depth`, `count_slash`) reaches the ten strongest class
    separators, and prints the caveat in its own output if one does. **None of the three
    does.** The asymmetry is real but it is not what the engineered features key on — the
    separation comes from the host, not the path.
15. **CORRECTED 2026-09-10 — the 40 shared URLs are not conflicts.** Re-measured against
    each class of the sid321axn file separately: **all 40** of those shared URL strings
    sit in that file's **`phishing`** rows, where the two sources *agree*. Against the
    `benign` rows — the only rows this project opposes to PhishTank — the raw-string
    overlap is **0**, and after normalisation exactly **1** URL carries contradictory
    labels. Both of its copies were dropped. The earlier "lower bound" reading was sound
    in principle but the number was measured over the wrong subset.
16. **Candidate A ships the same corpus twice.** `phishing_email.csv` (82,486 rows) is
    exactly the six corpora combined (39,154 + 29,767 + 2,859 + 1,565 + 3,332 + 5,809 =
    82,486), re-encoded as lower-cased, punctuation-stripped text. Using both would
    duplicate every record. BERT needs raw text (Specification §9), which argues for the
    six corpora. **Decided 2026-09-10: the six corpora are used and the aggregated file is
   excluded.** See "Primary Email Dataset Decision" above.

17. **Section 5 resolves the PhishTank snapshot at runtime.** `latest_phishtank_snapshot()`
    in notebook cell 35 picks whichever snapshot file is newest, so re-running section 5
    silently changes its own inputs — which is exactly what happened between the `100100Z`
    and `101958Z` reports. Section 6 does **not** do this: it pins
    `online-valid_20260822T101938Z.csv` by filename. Section 5 is left as executed, but
    its PhishTank row count must always be quoted together with the snapshot it used.
18. **RESOLVED 2026-09-10 — mixed text representation inside candidate A.** Enron and Ling
    arrive already lower-cased (0.00% of rows contain an uppercase letter) while the other
    four corpora keep raw text (98.55–99.91%). Handled rather than removed: the
    deduplication key ignores punctuation and casing, so one message is matched across
    both representations, and `bert-base-uncased` lower-cases its input anyway. Accepted
    as a limitation because casing was measured to be a weak label predictor (56.60%
    phishing among cased rows vs 45.18% among lower-cased).
19. **The feature separation ranking favours rare features and must not be quoted
    alone.** `separation` in `reports/features/url_features_*.json` is the class-mean gap
    divided by the overall mean, which is the only way to compare features measured in
    different units — but it rewards scarcity. `host_is_ip` tops the 2026-09-15 ranking on
    a mean of 0.0015 against 0.0000 while being present in just **0.074%** of training
    URLs, so it cannot decide much. Section 7.5 therefore prints a `coverage` column
    beside it, and the report must quote the two together. Of the top ten, only
    `host_hyphen_count` (20.56%), `host_digit_count` (16.93%) and `count_underscore`
    (14.88%) are both strong and common.
20. **738 processed URLs contain a scheme, and that is correct.** Found 2026-09-15 when
    section 7.5's first run refused to write, reporting them as "still carrying a scheme".
    Measuring them showed the check was wrong, not the data: **0** processed URLs *begin*
    with a scheme, and all 738 carry one *further inside* as a redirect target
    (`l.wl.co/l?u=https://qrco.de/bfPiOf`). Section 6 only ever removed the leading
    scheme, and removing an embedded one would destroy the URL. The distinction is now
    explicit in the code: `has_leading_scheme()` is the integrity check, and
    `count_embedded_urls()` is a feature. **Checked for source contamination rather than
    assumed innocent:** 1.119% of phishing rows against 0.117% of legitimate rows across
    the two sources, and the same pattern reproduces *inside one file* — the sid321axn
    source's own `phishing` rows score 0.806% against 0.104% for its `benign` rows. A
    difference that holds within one file cannot be an artefact of which file a row came
    from, so it is phishing signal and not provenance.
21. **Notebook cells 44–60 (section 6) carry no nbformat `id` field**, which makes
    `nbformat.validate` emit `MissingIDFieldWarning` and will become a hard error in a
    future nbformat release. Pre-existing since the section 6 splice on 2026-09-10, not
    introduced by section 7 — section 7's cells all have ids. Harmless today; fix by
    running `nbformat.normalize()` when the notebook is next edited wholesale, since
    adding ids touches those cells' bytes without changing their content.

22. **Section 6 was re-executed at 2026-09-15 02:53:36 UTC by something unaccounted
    for, and it rewrote all six split files.** Evidence: the six CSVs under
    `data/processed/` all carry that modification time, and a third preprocessing report
    `preprocessing_20260915T025336Z.json` appeared alongside them. It was not run from the
    notebook on disk — section 6's stored cells still show execution counts 10–17 and cell
    6.8's stored output still cites `preprocessing_20260910T014200Z.json` — so the most
    likely explanation is a kernel execution from an editor session whose buffer never
    reached the file, which is the same hazard as known problem 13.
    **The data is unharmed, and that was checked rather than assumed:**
    * the new preprocessing report is **identical** to the 2026-09-10 one apart from its
      timestamp and timing fields — same row counts, same deduplication figures, same class
      balances, and **0 shared keys across all six split pairs**;
    * the URL feature files rebuilt from the **rewritten** train and validation splits hash
      **identically** to those built from the originals
      (`53b5ee4a…`, `06e61630…`), which proves the rewritten splits have identical content.
    **Consequences.** The "test split untouched since 2026-09-10" claim can no longer be
    supported by a modification time, and has been replaced by the content hashes in
    "Processed Split Integrity" above. The leakage guarantee itself stands: section 6
    *writes* the test split, it does not feed it to a model, and nothing has read it for
    training, thresholding or model selection. **Close the notebook in VS Code before any
    external tool edits it** (known problem 13), and prefer content hashes over timestamps
    for every future integrity claim.

## Next Task

**Produce the full BERT feature set on a Colab GPU runtime.** Everything else waits on it.

1. Open `Anti_phishing_prototype.ipynb` on a Colab GPU runtime (Runtime → Change runtime
   type → GPU). Section 1.2 already skips the `torch` install on Colab so its CUDA build
   is preserved.
2. Run section 1 to set the project root and confirm `torch.cuda.is_available()` is now
   `True`, then run section 8.
3. In section 8.3 set `MAX_ROWS_PER_SPLIT = None`, then run 8.4 and 8.5. Output lands in
   `bert_full/` folders, entirely separate from the `subset512` sample already on disk.
4. If the runtime disconnects, re-run 8.4 — completed shards are skipped and the run
   resumes.
5. Record the measured GPU name, CUDA version and real extraction time in the Modelling
   Environment table above, replacing the CPU-only figures.

**After the full features exist**, the next stage is XGBoost training (Specification §10),
which must not begin before then. The URL branch has two feature sets to combine — 35
lexical/structural features and 768 BERT dimensions — and how they are joined is a
modelling decision to be recorded here when it is made.

**Still outstanding, unrelated to BERT:**

* **Expire the Kaggle API token** at kaggle.com/settings → API (known problem 9). It is out
  of the notebook and git-ignored, but was previously embedded.
* Known problem 8 — the false PyPI claim in `scripts/requirements-acquisition.txt`.
* Known problem 7 — payload validation in `scripts/acquire_phishtank.py`.
* Known problem 21 — section 6 cells still carry no nbformat `id` field.

Do not train any model, produce any metric, or read either test split until instructed.

## Important Decisions

* Do not change the approved research objectives.
* Do not change the BERT + XGBoost methodology without justification.
* Do not report results before actual experiments are executed.
* Do not use test data during model development.
* Fixed random seeds for all experiments.
* Scope limited to an undergraduate FYP research prototype.
* PhishTank remains the primary URL source despite the keyless limitation (2026-08-13).
* Both Kaggle candidates are acquired and inspected before one is selected (2026-08-13).
* Raw datasets are never modified or overwritten; provenance sidecars accompany every download.
* Primary email dataset is candidate A's six corpora; the aggregated file is excluded because its punctuation is destroyed (2026-09-10).
* Data sources are pinned by filename, never resolved as "the latest file" at runtime (2026-09-10).
* Deduplication always precedes splitting, and the split is verified afterwards to share zero keys (2026-09-10).
* Records carrying contradictory labels are dropped entirely rather than assigned a winner (2026-09-10).
* Preprocessing code is written in basic Python and must pass its self-test before the rest of the stage runs (2026-09-10).
* URL engineered features are computed per URL with no fitted parameter, so the stage has nothing to leak (2026-09-15).
* The test split stays unread through feature engineering, to preserve the audit trail rather than because extraction could leak (2026-09-15).
* No feature selection: XGBoost receives all 35 engineered features, and the separation ranking is descriptive only (2026-09-15).
* The suspicious-word list is fixed in advance from the literature and excludes brand names, so it is prior knowledge rather than a parameter fitted on the data (2026-09-15).
* No network lookups in feature engineering — no WHOIS, DNS or page fetch — because PhishTank lists only currently-online phishes (2026-09-15).
* File integrity is claimed with SHA-256 content hashes, never with modification times (2026-09-15, after known problem 22).
* Comment-only edits to an executed cell are permitted without re-executing it, but must be proven comment-only by comparing the parsed code with docstrings stripped (2026-09-15).

## Change Log

| Date | Change |
| --- | --- |
| 2026-09-17 | **BERT contextual feature extraction implemented and verified; git repository made safe before its first commit.** Added section 8 to `Anti_phishing_prototype.ipynb` (8.1 helpers, 8.2 self-test, 8.3 settings, 8.4 extraction, 8.5 verify/measure/write); 73 → 84 cells, five new code cells executed in a live kernel, 0 errors, sections 2–7 not re-run. Frozen `bert-base-uncased`, mean pooling over non-padding tokens, 768 dimensions; `max_length` 256 for email and 128 for URLs, both chosen from measured token distributions. Self-test 24/24, covering the failure that matters most — length-sorted batching reordering rows away from their labels — plus shard resume, atomic shard writes and refusal to join shards from a differently-sized run. Two real bugs were caught by that test and fixed: `np.save` appending `.npy` to the temporary shard name and breaking the atomic rename, and a short shard from a limited run being joinable into a full run. Run limited to 512 rows per split (CPU full pass measured at ~4.8 hours); all verification checks passed and `reports/features/bert_features_20260917T062736Z.json` was written. **The full feature set does not exist yet and nothing has been trained.** Separately: the project was found to be a git repository with zero commits, no `.gitignore`, and every file already staged — including a live Kaggle credential and ~670 MB of data. The index was cleared and a `.gitignore` added before the first commit, which covers 42 files and about 1 MB. Notebook backups taken to `backups/`. |
| 2026-09-15 | **Notebook documentation pass, and a record correction.** (a) The status table in the notebook's title cell was stale — it still listed preprocessing and feature engineering together under "Later / not implemented" — and now records **6. Preprocessing** and **7. Feature Engineering** as implemented, with the test split's deferral stated. (b) The two stages were given short, clearly separated titles: `# 6. Data Preparation (Preprocessing)` became **`# 6. Preprocessing`**, and `# 7. URL Lexical and Structural Feature Engineering` became **`# 7. Feature Engineering — URL Lexical and Structural`**, following the house style of sections 2 and 3. (c) **Plain-language comments added to all 13 code cells of sections 6 and 7** at the owner's request: each cell gained a "WHAT THIS CELL DOES, in plain words" block, and 30 helper functions gained worked `Example:` lines (`shannon_entropy("abcd") -> 2.0`, `host_is_ip_address("1.2.3.256") -> False`, and so on). Section 7's five cells were **re-executed** afterwards and their outputs re-spliced; the feature CSVs hashed **identically** to before the comment pass, confirming the comments changed nothing. Section 6 was deliberately **not** re-executed, because cell 6.8 rewrites all six split files including the test splits; instead the edit was **proven** comment-only by parsing each cell before and after, stripping every docstring, and comparing the two abstract syntax trees — all 8 cells reported identical executable code, identical stored outputs and unchanged execution counts. (d) **Correction forced by a discovery:** all six split files were found rewritten at 02:53:36 UTC by a section 6 re-execution that is not accounted for, which voided the previous entry's proof that the test split still carried its 2026-09-10 modification time. The data was checked and is unharmed — the new preprocessing report is identical to the 2026-09-10 one bar its timestamp, 0 shared keys across all six split pairs, and the URL features rebuilt from the rewritten splits hash identically to those built from the originals. Recorded as known problem 22, and **modification times have been replaced by SHA-256 content hashes** for all six split files and both feature files under the new "Processed Split Integrity" heading. **No BERT feature extraction and no model training performed.** |
| 2026-09-15 | **URL lexical and structural feature engineering completed and executed.** Added section 7 to `Anti_phishing_prototype.ipynb` (7.1 feature helpers, 7.2 self-test, 7.3 sources and settings, 7.4 extraction, 7.5 verify/measure/write). Notebook grew 62 → 73 cells; the 5 new code cells were executed in a fresh kernel with **0 errors**, without re-running sections 1–6 — section 7 reads only the processed CSVs, so sections 2–4 were never touched. Cells 0–60 verified **byte-identical** to their pre-existing state. Helpers written in **basic Python** and tested first against known-answer fixtures worked out by hand — **164 assertions**, including one regression test per silent-failure mode (the `@`-host rule, fragment-before-query, the empty-URL division, determinism, and every-value-is-a-number). **Produced:** `data/features/url/train.csv` (98,344 rows, 14.34 MB) and `validation.csv` (21,074 rows, 3.06 MB), 35 numeric features each, plus `reports/features/url_features_20260915T030436Z.json`. **Verified:** rows in == rows out exactly; 0 URLs begin with a scheme; 0 missing, 0 negative, 0 out-of-range and 0 non-binary values; 0 of 35 features constant on train; and the pipeline run twice in separate processes produced **byte-identical CSVs by SHA-256**. **The test split was not read** — and one line in cell 7.3 turns it on at final evaluation. *(This entry originally proved that with a modification time. That proof was voided later the same day — see known problem 22 and the 2026-09-15 documentation-pass entry above. The claim itself still holds; only its evidence changed, to the SHA-256 digests under "Processed Split Integrity".)* **Decisions recorded:** no feature selection (XGBoost receives all 35); constant features reported not removed; a 14-term suspicious-word list fixed in advance with no brand names; no WHOIS/DNS/page lookups; subdomains counted as "labels minus two" with the `co.uk` error stated. **A correction to the project record:** 7.5's first run refused to write, flagging 738 URLs as "still carrying a scheme". Measurement showed the check was wrong, not the data — **0** processed URLs *begin* with a scheme and all 738 carry one *inside*, as a redirect target. That became the distinction between `has_leading_scheme()` (integrity check) and `count_embedded_urls()` (feature), and the feature was cleared of source contamination by reproducing the effect **inside one file** (sid321axn's own phishing rows 0.806% vs its benign rows 0.104%). **Measured against expectation:** phishing URLs here are *shorter* than legitimate ones (mean 49.67 vs 56.82) with shorter paths — the separation comes from the **host** (longer, more hyphens, more digits, more subdomains), not the path. Known problem 14 updated with the measured consequence (no path-shaped feature reaches the ten strongest separators); known problems 19–21 added. **No BERT feature extraction and no model training performed.** |
| 2026-09-10 | **Preprocessing (CRISP-DM data preparation) completed and executed.** Added section 6 to `Anti_phishing_prototype.ipynb` (6.1 helpers, 6.2 self-test, 6.3 sources and settings, 6.4 load email, 6.5 clean and deduplicate email, 6.6 load/neutralise/deduplicate/balance URLs, 6.7 stratified split, 6.8 verify and write). Notebook grew 45 → 62 cells; the 8 new code cells were executed in a fresh kernel with **0 errors**, without re-running sections 2–4. Sections 1–5 verified byte-identical to their pre-existing state. Helpers written in **basic Python** at the owner's request and tested first against known-answer fixtures — **83 assertions**, including one regression test per recorded leakage risk; the suite caught a real defect before the code reached the notebook (`int()` instead of `round()` in the split, which silently moved one record out of every train split because `700 * 0.70` is `489.99999999999994`). **Decisions recorded:** candidate A's six corpora as the primary email dataset, aggregated file excluded, candidate B rejected; email text = subject + body with a body-only duplicate key; PhishTank snapshot pinned by filename; legitimate URLs undersampled to 1:1 at seed 42; stratified 70/15/15 at seed 42 after deduplication. **Measured results:** email 82,486 → 80,643 (1,840 duplicates, 1 blank, 2 contradictory); URL 501,004 → 497,272 → 140,490 after balancing. Leakage verification returned **0 shared keys across all six split pairs**. Reproducibility verified by running the pipeline twice in separate processes and confirming all six output CSVs were **byte-identical by SHA-256**. **Three corrections to the record:** a second PhishTank snapshot (72,901 rows, a strict superset of the 08-18 one) had been on disk unrecorded since 2026-08-22 and was being picked up silently by section 5; the URL scheme leak is **8.26%** not 28.87% on the benign rows actually used, so it was worse than recorded; and the "40 conflicting URLs" of known problem 15 are **not conflicts** — all 40 lie in the sid321axn file's `phishing` rows where the sources agree, leaving exactly 1 genuine contradiction. Known problems 5, 14 and 18 resolved, 15 corrected, 17 and 18 added. **No feature engineering, BERT feature extraction or model training performed; the test splits have not been read.** |
| 2026-08-22 | **Benign URL source acquired and full dataset inspection completed.** Corrected the record: the PhishTank snapshot had in fact been acquired successfully on 2026-08-18 at 03:27:48 UTC (72,230 rows) and this file wrongly stated the feed was blocked. Added section 4 to `Anti_phishing_prototype.ipynb` (legitimate URL source — `sid321axn/malicious-urls-dataset`, `benign` rows only, 428,103 URLs; idempotent acquisition with SHA-256 provenance) and section 5 (dataset inspection — full-file measurement of all 10 CSVs). Notebook grew 27 → 45 cells; the 8 new code cells were executed in a live kernel with 0 errors, without re-running sections 2 and 3. Inspection logic was tested against known-answer fixtures first (33 assertions, including a regression test for each of the three defects in the superseded `scripts/inspect_datasets.py`). Measured: 0 malformed rows across all files; label meaning verified as 1 = phishing; the aggregated file shown to be the six corpora re-encoded; 16 overlapping dataset pairs; PhishTank 100% schemed vs benign source 28.87%; 40 URLs claimed by both sources. Known problems 2 and 4 resolved, 5 and 10 rewritten, 14–16 added. `docs/DATASET_SOURCES.md` §3, §6 and §7 populated with measured figures. **No cleaning, deduplication, merging, balancing, splitting, feature engineering or training performed.** |
| 2026-08-12 | PROJECT_STATE.md created. Stage: Initial Project Setup. |
| 2026-08-13 | Dataset acquisition stage opened. PhishTank access verified; key registration found disabled. Two Kaggle candidates shortlisted. Acquisition and inspection scripts written and tested. Downloads still pending. |
| 2026-08-16 | Verified third-party claims about keyless PhishTank "public data dumps": confirmed keyless download is official but rate-limited, `phishtank.net` is a mirror of the same site, the quoted JSON URL was wrong, and registration is "temporarily" not permanently disabled. Added `scripts/register_manual_download.py` as a provenance-equivalent manual fallback. |
| 2026-08-18 | **PhishTank acquisition module implemented; live feed blocked.** Created `src/data/phishtank.py` (plus `src/__init__.py`, `src/data/__init__.py`) exposing `fetch_phishtank_dataset()`, `find_latest_snapshot()`, `list_snapshots()`, `EXPECTED_COLUMNS` and `PhishTankAcquisitionError`. Keyless by default, optional `PHISHTANK_APP_KEY` from the environment with redaction, timestamped raw snapshots under `data/raw/phishtank/`, provenance under `data/metadata/phishtank/`, snapshot reuse with `force_refresh` override, and payload validation that rejects a Cloudflare page served as HTTP 200. Section 3 added to `Anti_phishing_prototype.ipynb` (3.1 fetch, 3.2 verify) and executed — notebook now 27 cells, 11 code cells, exit 0, no error outputs. Module test: 34/34 assertions passed against a local server with a synthetic feed. **Live acquisition FAILED with HTTP 429 on both attempts; `data/raw/phishtank/` is still empty.** No cleaning, feature engineering, splitting or training performed. |
| 2026-09-15 | **Section 7 recovered after VS Code deleted it.** An open VS Code buffer saved the stale pre-section-7 notebook over the finished file at 11:13, destroying all 10 section 7 cells and the 21 section 6 comment edits, while the feature CSVs and report written at 11:04 remained on disk. Restored from the previous session's scratchpad and **verified by re-execution in a fresh process**: both feature CSVs reproduced byte for byte (SHA-256 equal) and all five cells' stored output reproduced except the report timestamp. Sections 1-6 proven unchanged by AST comparison — identical code, outputs and execution counts — so **nothing was re-executed and sections 2-4 were never touched**. Notebook back to 73 cells; section 7 execution counts renumbered 28-32 to continue the notebook's own sequence. Known problem 13 rewritten with the third occurrence. |
| 2026-08-17 | **Kaggle dataset acquisition completed.** Section 2 added to `Anti_phishing_prototype.ipynb` (2.1 legacy credentials, 2.2 kaggle client install, 2.3 download, 2.4 on-disk verification) and executed — 9 code cells, exit 0, no errors. kaggle 1.7.4.5 authenticated successfully via `~/.kaggle/kaggle.json`. Downloaded `naserabdullahalam/phishing-email-dataset` (7 CSVs, 80.86 MB archive) and `subhajournal/phishingemails` (1 CSV, 18.92 MB archive) — 12 files, 413.1 MB total, archives preserved, SHA-256 provenance sidecars written. **No inspection, preprocessing, feature engineering, split or training performed.** Known problem 9 rewritten: a live API key is now embedded in cell 2.1 at the owner's request and must be removed and expired before sharing. |
| 2026-08-16 | **Stage 0 — Model Environment Setup completed and verified.** `Anti_phishing_prototype.ipynb` rebuilt as 13 cells: section 1 with subsections 1.1 project root/runtime, 1.2 install, 1.3 imports, 1.4 environment + hardware verification, 1.5 import verification. Executed via `jupyter nbconvert --execute` — all 5 code cells ran, exit 0, no errors. Measured: Python 3.12.0, torch 2.13.0+cpu, transformers 5.15.0, xgboost 3.4.1, scikit-learn 1.9.0, CUDA unavailable, device `cpu`, seed 42. Known problems 11–13 added (no GPU locally, tqdm/ipywidgets warning, VS Code clobbering the notebook). No preprocessing, feature engineering, split, feature extraction or training performed. `data/raw/` remains empty. |
| 2026-08-16 | Development Phase 1 opened. Modelling library stack selected and justified against Specification §9–§11, with exclusions recorded. Second code review logged four unresolved defects as known problems 7–10, including a verified false-success path in `acquire_phishtank.py` and a false PyPI claim in `requirements-acquisition.txt`. |
| 2026-08-13 | Code review fixes: notebook rebuilt as valid cells; Windows/PowerShell and notebook credential instructions added; dependency versions bounded; Kaggle provenance sidecars timestamped so re-runs cannot overwrite them; `.bz2` and `.tsv` parsing corrected; uninspectable formats now reported instead of silently skipped; PhishTank format restricted to CSV; overwrite guard fails cleanly; URL column matched by exact name. Also fixed: kaggle authenticates at import time (now caught), and the kaggle credentials path moved to `~/.config/kaggle/` in kaggle ≥ 1.7. |
