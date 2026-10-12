# Web page — "Is this a scam?"

The interface of the prototype, built with HTML, CSS, JavaScript and Bootstrap 5.3 so it
can be hosted on Netlify. It replaces the gradio interface that used to live in notebook
sections 12.6 and 12.7.

| File | What it is |
| --- | --- |
| `index.html` | the landing page: what the prototype does, its measured test F1-scores, and an animated scan monitor |
| `css/landing.css` | the landing page's dark look, on top of Bootstrap |
| `js/landing.js` | the landing page's motion: count-up figures, typed examples, the Lottie shield |
| `animations/shield-scan.json` | the Lottie (JSON) shield animation, made by `scripts/make_shield_lottie.py` |
| `check.html` | the checker: two tabs (email, link), the forms, and where answers appear |
| `css/style.css` | the checker's look, on top of Bootstrap |
| `js/config.js` | **where the model server is** (`apiBaseUrl`) — the only setting |
| `js/app.js` | sends what the user pasted to the model server and shows the answer |

`netlify.toml` at the repository root tells Netlify to publish this folder as it is.

### The landing page's scan monitor

The three results it cycles through are **illustrations** of what an answer looks like,
not live model output, and the monitor says so on screen. The figures under the headline
are the real held-out test results (`docs/PROJECT_STATE.md`): F1 0.9846 for email and
0.9641 for links. Animations are switched off for visitors who ask their system for
reduced motion. The Lottie player is `lottie-web` 5.12.2 from jsDelivr, pinned with an
integrity hash like Bootstrap.

## Status

**Not connected yet.** The page is finished enough to use, but the models (BERT +
XGBoost) are Python and run in the notebook, and nothing serves them over the web yet.
Until that model server exists, the page shows "The model server isn't connected".

The next step is a small web API around the predictors that notebook section 12.3 builds,
answering the requests below. The helpers it needs already exist: `classify()` and
`url_warning_signs()` (12.1), `explain_link()` and `explain_email()` (12.4).

## Trying the page

Serve the folder (for example with Laragon, or
`python -m http.server` from inside `web/`). Opening `index.html` straight from disk works except for the Lottie
shield, which browsers only load over http. With no model server `check.html` loads and
says it isn't connected.

## What the page asks the model server

All requests and answers are JSON. Paths are relative to `apiBaseUrl` in `js/config.js`.

### `GET /api/health`

Which models answer, for the footer.

```json
{"status": "ok",
 "models": {
   "email": {"name": "email_bert", "test_f1": 0.9846, "test_accuracy": 0.9842,
             "best_other_name": "email_tfidf_logreg", "best_other_f1": 0.9868},
   "url":   {"name": "url_bert_lexical", "test_f1": 0.9641, "test_accuracy": 0.9642,
             "best_other_name": "url_tfidf_logreg", "best_other_f1": 0.9678}}}
```

### `POST /api/check-email`

Sent: `{"subject": "...", "body": "..."}`. Answer: the output of `classify()` (12.1).

```json
{"verdict": "phishing", "confidence": 97.3, "phishing_probability": 97.3}
```

`verdict` is `"phishing"` or `"legitimate"`. The page never sends an empty email.

### `POST /api/explain-email`

Sent: the same as check-email. Answer: the output of `explain_email()` (12.4), which
takes several seconds on a CPU.

```json
{"visible_text": "...", "was_cut": false,
 "words": ["Dear ", "customer, ", "..."], "values": [0.02, -0.11, "..."],
 "base_value": 0.03, "margin": 3.4, "seconds": 14.2, "max_evals": 100,
 "method": "shap Partition explainer over words (approximate)"}
```

### `POST /api/check-url`

Sent: `{"url": "..."}`. Answer: `classify()`, plus `url_warning_signs()` and
`explain_link()` (exact and instant, so it comes with the verdict).

```json
{"verdict": "phishing", "confidence": 99.1, "phishing_probability": 99.1,
 "warning_signs": ["Lots of hyphens in the address, ..."],
 "explanation": {"base_value": -0.2, "margin": 4.7,
                 "method": "TreeSHAP built into XGBoost (exact)",
                 "reasons": [{"label": "Hyphens in the website name", "detail": "3",
                              "value": 1.6, "feature": "host_hyphen_count"}]}}
```

SHAP values are in log-odds: positive pushes towards phishing, negative towards
legitimate. The page describes a push of 1.0 or more as strong and 0.3 or more as
moderate, the same cut-offs as notebook section 12.4.

## Safety

Everything that comes from the user or the server is put on screen with `textContent`,
never as HTML, so pasted markup such as `<script>` is shown as text and never runs.
