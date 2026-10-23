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
├── Learn.html          the guide for young people: what phishing is and how to spot it
├── Vulnerabilities.html  under Learn: software weak spots (CVEs), six real cases, why updates matter
├── Game.html           the "Scam or Safe?" mini-game
├── Login.html          log in / sign up (optional accounts, needs Laragon: see api/README.md)
├── Account.html        "My records": the logged-in person's saved checks and games
├── css/
│   ├── theme.css       shared: the three colour themes
│   ├── nav.css         shared: the site header (Home, Learn, Checker)
│   ├── homepage.css    Homepage.html only
│   ├── learn.css       Learn.html (and Vulnerabilities.html, which builds on it)
│   ├── vulnerabilities.css  Vulnerabilities.html only, on top of learn.css
│   ├── game.css        Game.html only
│   ├── account.css     Login.html and Account.html
│   └── checker.css     Checker.html only
├── js/
│   ├── theme.js        shared: theme setting and the Theme button
│   ├── config.js       shared: where the model server and the accounts API are
│   ├── auth.js         shared: who is logged in, the header's account link, saving records
│   ├── login.js        Login.html only
│   ├── account.js      Account.html only
│   ├── homepage.js     Homepage.html only
│   ├── learn.js        Learn.html (and Vulnerabilities.html: animations, fade-ins, chapter bar)
│   ├── vulnerabilities.js  Vulnerabilities.html only: builds the page from data/vulnerabilities.json
│   ├── game.js         Game.html only: how the game plays
│   ├── game-scenarios.js  Game.html only: the 18 messages the game uses
│   └── checker.js      Checker.html only
├── data/
│   └── vulnerabilities.json  the words, cases and quiz shown on Vulnerabilities.html
└── animations/
    ├── shield-scan.json
    ├── learn-*.json    the eight animations on Learn.html, plus learn-patch and learn-update
    └── game-*.json     the four animations on Game.html
```

| File | What it is |
| --- | --- |
| `index.html` | the site's entry point; Netlify and Laragon open it for the root address, and it forwards to `Homepage.html` |
| `Homepage.html` | the homepage: what the prototype does, its measured test F1-scores, and an animated scan monitor |
| `Checker.html` | the checker: two tabs (email, link), the forms, and where answers appear. `Checker.html#url` opens the link tab and `Checker.html#email` the email tab |
| `Learn.html` | the education page for young people, in seven parts: what phishing is, why it works (feelings scammers use), red flags at first sight with a practice email, reading a link, common baits, real or fake side by side (three real messages next to their fake twins, and what real messages usually do), and what to do (Stop, Check, Ask). Each part has its own Lottie animation; part 06 ends with a link to the game |
| `Vulnerabilities.html` | the "Hidden weak spots" page under Learn, in five parts: what a weak spot (vulnerability, CVE) is and how to read a CVE ID, the two kinds of trap (tricks you / tricks your app), six real cases from CISA's Known Exploited Vulnerabilities list that arrived by message, file or web page (with filters and a "What happened?" story for each), what to do (updates), and a four-question quick check. Learn.html links to it at the end of part 07. Its words and facts are in `data/vulnerabilities.json`, so the page needs to be opened through a web server (Netlify, Laragon or `python -m http.server`), not straight from disk |
| `data/vulnerabilities.json` | the content of Vulnerabilities.html. Each case's CISA facts (product, date added) are checked against CISA's live feed by `python scripts/check_vulnerability_data.py` (add `--update` to refresh the catalogue count and checked date) |
| `css/vulnerabilities.css`, `js/vulnerabilities.js` | the page's own styles and behaviour, on top of `learn.css` and `learn.js`. The JavaScript builds every case and question with `textContent`, never as HTML |
| `css/learn.css` | the education page's layout, cards and motion, on top of Bootstrap |
| `js/learn.js` | the education page's behaviour: plays each animation only while it is on screen, fades parts in, the chapter bar and reading progress, the "Show the red flags" practice, and the link quiz |
| `animations/learn-*.json` | the education page's eight Lottie animations, made by `scripts/make_learn_lotties.py` (`python scripts/make_learn_lotties.py web/animations`) |
| `Game.html` | the "Scam or Safe?" mini-game: 10 rounds (6 scams, 4 real messages, picked at random from 18). Each round shows a situation and a message (text, email, chat, phone call or web page); the player picks Scam or Safe, and the card flips to show the answer, the clues marked on the message, and one thing to remember. 100 points per right answer, 50 if the hint was used; the results screen gives a rank and a review of every answer |
| `css/game.css` | the game's layout, the flip card and the message mock-ups, on top of Bootstrap |
| `js/game.js` | the game's behaviour. The best score is kept in the visitor's browser (`localStorage`, key `isthisascam-game-best`); if storage is blocked the game still works but doesn't remember it |
| `js/game-scenarios.js` | the game's messages, kept apart from the code so they're easy to edit or add to. The comment at the top explains the fields; `[[2|some words]]` marks words as clue 2 |
| `animations/game-*.json` | the game's four Lottie animations, made by `scripts/make_game_lotties.py` (`python scripts/make_game_lotties.py web/animations`) |
| `css/nav.css` | the site header shared by every page: the name on the left, Home / Learn / Checker on the right, the current page highlighted (`aria-current="page"`), and the top-right corner kept free for the Theme button |
| `css/theme.css` | the three colour themes (Default, Dark, Light) shared by every page, and the Theme button's look |
| `css/homepage.css` | the homepage's layout and motion, on top of Bootstrap (`delay-0` ... `delay-5` set the order things appear in) |
| `css/checker.css` | the checker's layout, on top of Bootstrap |
| `js/theme.js` | applies the saved theme before the page is drawn, and adds the Theme button (top-right) |
| `js/config.js` | **where the model server is** (`apiBaseUrl`), and where the accounts API is (`accountApiUrl`, `"../api"`) |
| `js/auth.js` | loaded on every page after `config.js`. Asks `api/me.php` who is logged in and adds one link to the end of the header: "Log in", or the person's first name (to My records). If the API can't be reached (Netlify has no PHP) nothing is added. Gives `window.Account` to the other scripts: `checker.js` saves each answer and `game.js` each finished game, only when logged in |
| `Login.html`, `js/login.js` | one card with two forms: Log in (email, password) and Sign up (first name, last name, email, password). `Login.html#signup` opens sign-up; `?next=Game.html` returns there afterwards (only this site's own pages are accepted) |
| `Account.html`, `js/account.js` | My records: totals, every Scam or Safe? attempt (passed or not, with the pass mark of 8/10 and which try was the first pass), and every saved check. Logged-out visitors are sent to Login.html |
| `css/account.css` | the two account pages' styles, the same look as the other pages |
| `js/homepage.js` | the homepage's motion: count-up figures, typed examples, the Lottie shield |
| `js/checker.js` | sends what the user pasted to the model server, shows the answer, and opens the tab named by `#url` or `#email` |
| `animations/shield-scan.json` | the Lottie (JSON) shield animation, made by `scripts/make_shield_lottie.py` |

No page has inline `<script>` or `style="..."`: all behaviour is in `js/` and all styling in `css/`.

### Adding a new page

Name it after what it is (e.g. `Flashcards.html`), give it its own `css/flashcards.css` and
`js/flashcards.js`, and load the shared files the same way the existing pages do:
`js/theme.js`, `css/theme.css` and `css/nav.css` in `<head>`, then the page's own stylesheet.
Copy the `<header class="site-nav">` block (Home, Learn, Game, Checker) from an existing page, add the new page to its
list of links on every page, and move `aria-current="page"` to the new page's own link.

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

## Accounts (optional)

Visitors can sign up to keep **My records**. Accounts are PHP + MySQL in the `api/` folder
next to `web/` (so Netlify never publishes it); set-up steps, tables and requests are in
`api/README.md`. They only work when the project is opened through Laragon; everywhere else
the site behaves as before and the header shows no "Log in" link. While logged in, the
Checker shows "Saved to My records" under each answer and the game's results screen says
whether the round counted as a pass.

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

Both `/api/check-url` and `/api/explain-email` also return `attack_techniques`: the
MITRE ATT&CK / CAPEC techniques the SHAP reasons point to, worked out by
`server/attack_mapping.py`. It is only filled in for a phishing answer.

```json
"attack_techniques": {
  "applies": true, "reason": "",
  "catalogues": ["MITRE ATT&CK v20", "MITRE CAPEC 3.9"],
  "techniques": [
    {"id": "CAPEC-632", "framework": "CAPEC", "name": "Homograph Attack via Homoglyphs",
     "url": "https://capec.mitre.org/data/definitions/632.html",
     "meaning": "A website name written with look-alike characters, ...",
     "basis": "shap", "push": 1.2,
     "evidence": ["The website name uses look-alike (punycode) characters."]},
    {"id": "T1566.002", "framework": "ATT&CK", "name": "Phishing: Spearphishing Link",
     "url": "https://attack.mitre.org/techniques/T1566/002/", "meaning": "...",
     "basis": "verdict", "push": null, "evidence": []}]}
```

`basis` is `"shap"` when a SHAP reason pointed to the technique (strongest first), or
`"verdict"` for the general techniques any phishing link or email belongs to. For a
legitimate answer `applies` is false and `techniques` is empty, and the page shows
nothing. The page only makes a link clickable when it goes to attack.mitre.org or
capec.mitre.org.

SHAP values are in log-odds: positive pushes towards phishing, negative towards
legitimate. The page describes a push of 1.0 or more as strong and 0.3 or more as
moderate, the same cut-offs as notebook section 12.4.

## Safety

Everything that comes from the user or the server is put on screen with `textContent`,
never as HTML, so pasted markup such as `<script>` is shown as text and never runs.
