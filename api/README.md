# Accounts API — PHP + MySQL (Laragon)

Optional accounts for the web page. A visitor who signs up (email, first name, last
name, password) gets **My records** (`web/Account.html`): every link and email they
check in the Checker, and every round of *Scam or Safe?* they play, with how many
times they passed.

Without an account the site works exactly as before. On Netlify, which has no PHP,
the "Log in" link simply never appears.

This folder sits **next to** `web/`, not inside it, so Netlify (which publishes only
`web/`) never serves these files.

```
api/
├── config.php          settings: MySQL login (Laragon defaults), pass mark, list length
├── _bootstrap.php      shared code: database connection, JSON in/out, the login session
├── signup.php          POST  create an account and log in
├── login.php           POST  log in
├── logout.php          POST  log out
├── me.php              GET   who is logged in (or null)
├── scans.php           GET   my checks   · POST save one check
├── game-attempts.php   GET   my games    · POST save one game
└── .htaccess           blocks opening config.php and _bootstrap.php in a browser
database/
└── schema.sql          creates the isthisascam database and its three tables
```

## Setting it up in Laragon (once)

1. Open Laragon and press **Start All** (Apache and MySQL).
2. Press **Database** (opens HeidiSQL), connect, then **File → Run SQL file…** and pick
   `database/schema.sql`. Or, in Laragon's **Terminal**:
   `mysql -u root < database/schema.sql`
3. Open the site through Laragon, for example
   `http://localhost/Final-Year-Project/web/Homepage.html`
   (or `http://final-year-project.test/web/Homepage.html` with Laragon's pretty URLs).
   A **Log in** link appears at the right end of the header.

If MySQL has a password, or a different user or port, change `api/config.php`.

The page finds this API at `accountApiUrl` in `web/js/config.js` (`"../api"`: one folder
up from `web/`).

## The tables

| Table | One row per | Main columns |
| --- | --- | --- |
| `users` | account | `email` (unique, lower case), `first_name`, `last_name`, `password_hash`, `created_at`, `last_login_at` |
| `scan_results` | check made while logged in | `scan_type` (`email`/`url`), `url` **or** `email_subject` + `email_preview` (first 200 characters only), `verdict`, `confidence`, `phishing_probability`, `top_reason` (links: strongest SHAP reason) |
| `game_attempts` | finished game while logged in | `score`, `correct_count` / `total_rounds`, `scams_caught` / `scams_total`, `safe_trusted` / `safe_total`, `best_streak`, `hints_used`, `passed` |

A game is **passed** with at least 8 of 10 right (`game_pass_mark` in `config.php`; 8 is
where the game's "Sharp Eyes" rank starts). The server decides this, not the page, and
refuses a result whose numbers don't add up (for example more points than right answers
allow).

## Requests

All requests and answers are JSON. Every POST must be sent as `application/json`.

| Request | Sent | Answer |
| --- | --- | --- |
| `POST signup.php` | `{"email","first_name","last_name","password"}` | `201 {"ok":true,"user":{...}}`; `400` with `fields` (a message per field); `409` email taken |
| `POST login.php` | `{"email","password"}` | `200 {"ok":true,"user":{...}}`; `401 "Email or password is wrong."` |
| `POST logout.php` | `{}` | `200 {"ok":true}` |
| `GET me.php` | | `{"ok":true,"user":{...}}` or `{"ok":true,"user":null}` |
| `POST scans.php` | `{"scan_type":"url","url","verdict","confidence","phishing_probability","top_reason"}` or `{"scan_type":"email","subject","body",...}` | `201 {"ok":true,"id":12}` |
| `GET scans.php` | | `{"summary":{"total","phishing","legitimate"},"scans":[...]}` newest first |
| `POST game-attempts.php` | `{"score","correct_count","total_rounds","scams_caught","scams_total","safe_trusted","safe_total","best_streak","hints_used"}` | `201 {"ok":true,"passed":true,"stats":{...}}` |
| `GET game-attempts.php` | | `{"stats":{"attempts","passed","best_score","pass_mark","first_pass_attempt"},"attempts":[...]}` |

`user` is `{"id","email","first_name","last_name","created_at"}`. The password hash is
never sent. `scans.php` and `game-attempts.php` answer `401` when nobody is logged in.

## Safety

* Passwords are stored only as `password_hash()` hashes (bcrypt) and checked with
  `password_verify()`. Login gives the same message for a wrong email and a wrong
  password, so nobody can find out which emails have accounts.
* Every query uses PDO prepared statements, so typed-in text can never change a query.
* The login is a PHP session cookie marked HttpOnly (page scripts can't read it) and
  SameSite=Lax; the session id is renewed at login.
* POSTs must be JSON, which a form on another website can't send without the browser
  asking first: this stops cross-site request forgery.
* Each user only ever reads and writes their own rows (`WHERE user_id = ?` from the
  session, never from the request).
* Database errors go to PHP's error log, not to the page.
* The pages put everything from the database on screen with `textContent`, never as HTML.

This is a student prototype on one computer, not a hardened service: there is no email
confirmation, password reset or limit on login attempts.
