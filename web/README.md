# Web page — "Is this a scam?"

The interface of the prototype, built with HTML, CSS, JavaScript and Bootstrap 5.3 so it
can be hosted on Netlify. It replaces the gradio interface that used to live in notebook
sections 12.6 and 12.7.

One HTML page per screen, with that page's own CSS and JavaScript named after it.
Files used by every page are listed first.

```
web/
├── index.html          entry point only: sends the visitor to Homepage.html
├── Homepage.html       the homepage
├── Checker.html        the email and link checker
├── css/
│   ├── theme.css       shared: the three colour themes
│   ├── homepage.css    Homepage.html only
│   └── checker.css     Checker.html only
├── js/
│   ├── theme.js        shared: theme setting and the Theme button
│   ├── config.js       shared: where the model server is
│   ├── homepage.js     Homepage.html only
│   └── checker.js      Checker.html only
└── animations/
    └── shield-scan.json
```

| File | What it is |
| --- | --- |
| `index.html` | the site's entry point; Netlify and Laragon open it for the root address, and it forwards to `Homepage.html` |
| `Homepage.html` | the homepage: what the prototype does, its measured test F1-scores, and an animated scan monitor |
| `Checker.html` | the checker: two tabs (email, link), the forms, and where answers appear. `Checker.html#url` opens the link tab |
| `css/theme.css` | the three colour themes (Default, Dark, Light) shared by every page, and the Theme button's look |
| `css/homepage.css` | the homepage's layout and motion, on top of Bootstrap (`delay-0` ... `delay-5` set the order things appear in) |
| `css/checker.css` | the checker's layout, on top of Bootstrap |
| `js/theme.js` | applies the saved theme before the page is drawn, and adds the Theme button (top-right) |
| `js/config.js` | **where the model server is** (`apiBaseUrl`) — the only setting |
| `js/homepage.js` | the homepage's motion: count-up figures, typed examples, the Lottie shield |
| `js/checker.js` | sends what the user pasted to the model server, shows the answer, and opens the link tab for `#url` |
| `animations/shield-scan.json` | the Lottie (JSON) shield animation, made by `scripts/make_shield_lottie.py` |

No page has inline `<script>` or `style="..."`: all behaviour is in `js/` and all styling in `css/`.

### Adding a new page

Name it after what it is (e.g. `Flashcards.html`), give it its own `css/flashcards.css` and
`js/flashcards.js`, and load the shared files the same way the existing pages do:
`js/theme.js` and `css/theme.css` in `<head>`, then the page's own stylesheet.

`netlify.toml` at the repository root tells Netlify to publish this folder as it is, and
forwards the old `check.html` address to `Checker.html`.

### The homepage's scan monitor

The three results it cycles through are **illustrations** of what an answer looks like,
not live model output, and the monitor says so on screen. The figures under the headline
are the real held-out test results (`docs/PROJECT_STATE.md`): F1 0.9846 for email and
0.9641 for links. Animations are switched off for visitors who ask their system for
reduced motion. The Lottie player is `lottie-web` 5.12.2 from jsDelivr, pinned with an
integrity hash like Bootstrap.

### Colour themes

A **Theme** button in the top-right corner of every page offers three looks:

| Theme | Look |
| --- | --- |
| Default | navy blue, the homepage's original colours |
| Dark | near-black and neutral |
| Light | light background, for daylight and projectors |

The choice is saved in the visitor's browser (`localStorage`, key `isthisascam-theme`) and
applies to both pages. Every colour is a variable in `css/theme.css`, so a theme is only a
list of values that the pages' own stylesheets use. Red still means "towards
phishing" and green "towards legitimate" in every theme. If the browser blocks storage, the
theme still switches but is not remembered.

## Status

**Not connected yet.** The page is finished enough to use, but the models (BERT +
XGBoost) are Python and run in the notebook, and nothing serves them over the web yet.
Until that model server exists, the checker shows "The model server isn't connected".

The next step is a small web API around the predictors that notebook section 12.3 builds,
answering the requests below. The helpers it needs already exist: `classify()` and
`url_warning_signs()` (12.1), `explain_link()` and `explain_email()` (12.4).

## Trying the page

Serve the folder (for example with Laragon, or
`python -m http.server` from inside `web/`). Opening `Homepage.html` straight from disk works except for the Lottie
shield, which browsers only load over http. With no model server `Checker.html` loads and
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
