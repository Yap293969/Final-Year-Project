// Is this a scam? -- Account.html behaviour ("My records").
//
// Shows the logged-in person's saved records from the accounts API:
//   api/game-attempts.php  every finished round of Scam or Safe?, and how many passed
//   api/scans.php          every link and email checked in the Checker
// Nobody logged in: goes to Login.html, and comes back here afterwards.
//
// SAFETY: everything from the database is put on screen with textContent, never
// as HTML, so a saved link or subject containing markup is shown as text.

(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  // MySQL sends "2026-10-23 16:30:23" (the server's local time, which for Laragon
  // is this computer's time).
  function when(value) {
    var parts = String(value || "").split(/[- :]/).map(Number);
    if (parts.length < 6 || parts.some(isNaN)) return String(value || "");
    var date = new Date(parts[0], parts[1] - 1, parts[2], parts[3], parts[4], parts[5]);
    return date.toLocaleString(undefined, { day: "numeric", month: "short", year: "numeric",
                                            hour: "numeric", minute: "2-digit" });
  }

  function day(value) {
    var parts = String(value || "").split(/[- :]/).map(Number);
    if (parts.length < 3 || parts.some(isNaN)) return String(value || "");
    return new Date(parts[0], parts[1] - 1, parts[2])
      .toLocaleDateString(undefined, { day: "numeric", month: "long", year: "numeric" });
  }

  function plural(n, one, many) { return n + " " + (n === 1 ? one : many); }

  function ordinal(n) {
    var s = ["th", "st", "nd", "rd"], v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
  }

  function fail(message) {
    $("loading").hidden = true;
    $("error-notice").textContent = message;
    $("error-notice").hidden = false;
  }

  // --- Scam or Safe? -----------------------------------------------------------------

  function renderGames(data) {
    var stats = data.stats;
    var attempts = data.attempts || [];
    $("stat-games").textContent = String(stats.attempts);
    $("stat-passed").textContent = String(stats.passed);
    $("stat-best").textContent = String(stats.best_score);

    var note = "You pass with at least " + stats.pass_mark + " out of 10 right. ";
    if (!stats.attempts) note = "You pass with at least " + stats.pass_mark + " out of 10 right.";
    else if (stats.first_pass_attempt) {
      note += "You passed " + plural(stats.passed, "time", "times") + " in " +
              plural(stats.attempts, "game", "games") + ", first on your " +
              ordinal(stats.first_pass_attempt) + " try.";
    } else {
      note += "Not passed yet in " + plural(stats.attempts, "game", "games") + ". Keep going!";
    }
    $("games-note").textContent = note;

    var list = $("games-list");
    list.textContent = "";
    $("games-empty").hidden = attempts.length > 0;
    attempts.forEach(function (a, i) {
      var li = el("li", "record " + (a.passed ? "is-pass" : "is-fail"));
      var number = stats.attempts - i; // newest first; attempt 1 is the very first game
      li.appendChild(el("span", "record-badge", a.passed ? "Passed" : "Not yet"));
      var body = el("div", "record-body");
      body.appendChild(el("p", "record-main",
        "Attempt " + number + ": " + a.correct_count + " / " + a.total_rounds + " right · " +
        a.score + " points"));
      body.appendChild(el("p", "record-sub",
        "Scams caught " + a.scams_caught + "/" + a.scams_total +
        " · real ones trusted " + a.safe_trusted + "/" + a.safe_total +
        " · best streak " + a.best_streak +
        (a.hints_used ? " · " + plural(a.hints_used, "hint", "hints") : "")));
      li.appendChild(body);
      li.appendChild(el("time", "record-time", when(a.created_at)));
      list.appendChild(li);
    });
  }

  // --- Checker -----------------------------------------------------------------------

  function renderScans(data) {
    var summary = data.summary;
    var scans = data.scans || [];
    $("stat-scans").textContent = String(summary.total);
    $("stat-phishing").textContent = String(summary.phishing);
    $("scans-note").textContent = summary.total
      ? plural(summary.total, "check", "checks") + ": " + summary.phishing + " looked like phishing, " +
        summary.legitimate + " looked legitimate." +
        (summary.total > scans.length ? " The newest " + scans.length + " are listed." : "")
      : "";

    var list = $("scans-list");
    list.textContent = "";
    $("scans-empty").hidden = scans.length > 0;
    scans.forEach(function (s) {
      var phishing = s.verdict === "phishing";
      var li = el("li", "record " + (phishing ? "is-phish" : "is-safe"));
      li.appendChild(el("span", "record-badge", phishing ? "Phishing" : "Legitimate"));

      var body = el("div", "record-body");
      var main = el("p", "record-main");
      main.appendChild(el("span", "record-kind", s.scan_type === "url" ? "Link" : "Email"));
      if (s.scan_type === "url") main.appendChild(el("code", "record-url", s.url));
      else main.appendChild(el("span", null, s.email_subject || "(no subject)"));
      body.appendChild(main);

      var sub = "Confidence " + Number(s.confidence).toFixed(1) + "%";
      if (s.top_reason) sub += " · strongest clue: " + s.top_reason;
      else if (s.scan_type === "email" && s.email_preview) sub += " · “" + s.email_preview + "”";
      body.appendChild(el("p", "record-sub", sub));
      li.appendChild(body);
      li.appendChild(el("time", "record-time", when(s.created_at)));
      list.appendChild(li);
    });
  }

  // --- Start -----------------------------------------------------------------------------

  Account.ready.then(function (user) {
    if (user === undefined) {
      fail("Your records can't be loaded: the accounts server isn't running. Open the site " +
           "through Laragon with Apache and MySQL started.");
      return;
    }
    if (!user) {
      location.replace("Login.html?next=Account.html");
      return;
    }

    $("hello").textContent = "Hi, " + user.first_name + " " + user.last_name;
    $("who").textContent = user.email + " · member since " + day(user.created_at);

    Promise.all([Account.request("game-attempts.php"), Account.request("scans.php")])
      .then(function (results) {
        renderGames(results[0]);
        renderScans(results[1]);
        $("loading").hidden = true;
        $("records").hidden = false;
      })
      .catch(function (error) {
        if (error.status === 401) location.replace("Login.html?next=Account.html");
        else fail(error.message);
      });
  });

  $("logout-button").addEventListener("click", function () {
    var button = $("logout-button");
    button.disabled = true;
    button.textContent = "Logging out…";
    Account.logout()
      .catch(function () { /* already logged out, or the server is gone: leave anyway */ })
      .then(function () { location.href = "Homepage.html"; });
  });
})();
