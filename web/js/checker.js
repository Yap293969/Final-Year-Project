// Is this a scam? -- Checker.html behaviour.
//
// WHAT THIS FILE DOES, in plain words
// -----------------------------------
// It reads what the user pasted, sends it to the model server, and shows the
// answer: the verdict, the confidence, and the reasons (SHAP explanations).
// The models themselves (BERT + XGBoost) run on the model server, not in the
// browser. The requests this page makes are listed in web/README.md.
//
// SAFETY
// ------
// Everything that came from the user or the server is put on screen with
// textContent, never as HTML. A pasted "<script>" is shown as text, not run.
// This replaces the html.escape() protection the old Python cards used.

(function () {
  "use strict";

  var API_BASE = ((window.APP_CONFIG && window.APP_CONFIG.apiBaseUrl) || "").replace(/\/+$/, "");

  // Timeouts. Checking is quick; explaining an email re-runs BERT many times.
  var CHECK_TIMEOUT_MS = 30000;
  var EXPLAIN_TIMEOUT_MS = 180000;

  // How a push is described. Same cut-offs as notebook section 12.4 (log-odds).
  var STRONG_PUSH = 1.0;
  var MODERATE_PUSH = 0.3;
  var TOP_LINK_REASONS = 5;
  var TOP_EMAIL_WORDS = 6;

  var VERDICTS = {
    phishing: {
      title: "Looks like phishing",
      advice: "Don't log in, don't enter passwords, and don't pay anything."
    },
    legitimate: {
      title: "Looks legitimate",
      advice: "Nothing suspicious was found. Stay careful anyway."
    }
  };

  var EXAMPLES = {
    "email-scam": {
      subject: "Your account has been suspended",
      body: "Dear customer, we detected unusual activity on your account. You must verify your " +
            "identity within 24 hours or your account will be permanently closed. Click the secure " +
            "link below and confirm your password and card details immediately."
    },
    "email-normal": {
      subject: "Lecture notes for Friday",
      body: "Hi everyone, I have uploaded the slides for Friday's session to the shared folder. " +
            "Let me know if anything does not open properly. See you in class."
    },
    "url-scam": { url: "http://paypa1-secure-login.verify-account.com/signin/confirm.php" },
    "url-normal": { url: "https://github.com/pandas-dev/pandas" }
  };

  // --- Small helpers ----------------------------------------------------------

  function byId(id) {
    return document.getElementById(id);
  }

  // Build an element. Text is always set with textContent, never as HTML.
  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text !== undefined && text !== null) {
      node.textContent = text;
    }
    return node;
  }

  function clear(node) {
    while (node.firstChild) {
      node.removeChild(node.firstChild);
    }
  }

  function pushStrength(value) {
    var size = Math.abs(value);
    if (size >= STRONG_PUSH) { return "strong"; }
    if (size >= MODERATE_PUSH) { return "moderate"; }
    return "slight";
  }

  function pushClass(value) {
    return value > 0 ? "to-phishing" : "to-legitimate";
  }

  function pushText(value) {
    return pushStrength(value) + " push towards " + (value > 0 ? "phishing" : "legitimate");
  }

  function formatScore(value) {
    return (value >= 0 ? "" : "−") + Math.abs(value).toFixed(2);
  }

  // --- Talking to the model server --------------------------------------------

  function ApiError(message) {
    this.message = message;
  }

  function request(path, payload, timeoutMs) {
    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, timeoutMs);
    var options = { method: payload ? "POST" : "GET", signal: controller.signal, headers: {} };
    if (payload) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(payload);
    }

    return fetch(API_BASE + path, options)
      .then(function (response) {
        if (!response.ok) {
          throw new ApiError("The model server returned an error (status " + response.status +
                             "). Try again, or check the server's log.");
        }
        return response.json();
      })
      .catch(function (error) {
        if (error instanceof ApiError) { throw error; }
        if (error && error.name === "AbortError") {
          throw new ApiError("The model server took too long to answer. Try again in a moment.");
        }
        throw new ApiError("Couldn't reach the model server. Check that it's running, then try again.");
      })
      .finally(function () { clearTimeout(timer); });
  }

  // Put a button into a busy state while a request runs, and back afterwards.
  function setBusy(button, busyText) {
    var original = button.textContent;
    button.disabled = true;
    clear(button);
    var spinner = el("span", "spinner-border spinner-border-sm me-2");
    spinner.setAttribute("aria-hidden", "true");
    button.appendChild(spinner);
    button.appendChild(document.createTextNode(busyText));
    return function done() {
      button.disabled = false;
      button.textContent = original;
    };
  }

  // --- Rendering ---------------------------------------------------------------

  function renderError(container, message) {
    clear(container);
    var card = el("div", "error-card");
    card.setAttribute("role", "alert");
    card.appendChild(el("p", null, message));
    container.appendChild(card);
  }

  function renderVerdict(container, result, warningSigns) {
    clear(container);
    var style = VERDICTS[result.verdict];
    if (!style) {
      renderError(container, "The model server sent an answer this page doesn't understand.");
      return;
    }

    var card = el("div", "verdict verdict-" + result.verdict);
    card.appendChild(el("h2", "verdict-title", style.title));
    card.appendChild(el("p", "verdict-advice", style.advice));

    var confidence = el("div", "confidence");
    var percent = Number(result.confidence).toFixed(1);
    confidence.appendChild(el("div", "confidence-label", "Confidence " + percent + "%"));
    var progress = el("div", "progress");
    progress.setAttribute("role", "progressbar");
    progress.setAttribute("aria-label", "Confidence");
    progress.setAttribute("aria-valuenow", percent);
    progress.setAttribute("aria-valuemin", "0");
    progress.setAttribute("aria-valuemax", "100");
    var bar = el("div", "progress-bar");
    bar.style.width = percent + "%";
    progress.appendChild(bar);
    confidence.appendChild(progress);
    card.appendChild(confidence);

    if (warningSigns && warningSigns.length) {
      var signs = el("div", "warning-signs");
      signs.appendChild(el("h3", null, "General warning signs (fixed rules, not the model's reasons)"));
      var list = el("ul");
      warningSigns.forEach(function (sign) { list.appendChild(el("li", null, sign)); });
      signs.appendChild(list);
      card.appendChild(signs);
    }

    container.appendChild(card);
  }

  function whyCard(intro) {
    var card = el("div", "why");
    card.appendChild(el("h3", null, "Why the model decided this"));
    card.appendChild(el("p", "why-intro", intro));
    return card;
  }

  function methodNote(text) {
    return el("p", "why-method",
              "These are the model's own reasons, worked out with SHAP. They show what it paid " +
              "attention to, not proof that it's right. " + text);
  }

  // A link: the clues that pushed hardest, each with a bar.
  function renderLinkExplanation(container, explanation) {
    clear(container);
    if (!explanation) { return; }

    var reasons = (explanation.reasons || [])
      .filter(function (reason) { return reason.value !== 0; })
      .sort(function (a, b) { return Math.abs(b.value) - Math.abs(a.value); })
      .slice(0, TOP_LINK_REASONS);

    var largest = 0;
    reasons.forEach(function (reason) { largest = Math.max(largest, Math.abs(reason.value)); });

    var card = whyCard("The clues that pushed hardest. Red pushed towards phishing, green towards " +
                       "legitimate. A longer bar is a bigger push.");

    reasons.forEach(function (reason) {
      var row = el("div", "reason");
      var label = el("p", "reason-label", reason.label);
      if (reason.detail) {
        label.appendChild(document.createTextNode(": "));
        label.appendChild(el("strong", null, reason.detail));
      }
      row.appendChild(label);
      row.appendChild(el("p", "reason-push " + pushClass(reason.value), pushText(reason.value)));
      var track = el("div", "reason-bar");
      track.setAttribute("aria-hidden", "true");
      var fill = el("span", pushClass(reason.value));
      fill.style.width = (largest > 0 ? (100 * Math.abs(reason.value) / largest) : 0).toFixed(1) + "%";
      track.appendChild(fill);
      row.appendChild(track);
      card.appendChild(row);
    });

    card.appendChild(methodNote(
      "Method: " + explanation.method + ". Values are in log-odds (the model's raw score, not a " +
      "percentage): starting score " + formatScore(explanation.base_value) + ", plus every push, gives " +
      "the final score " + formatScore(explanation.margin) + "."));
    container.appendChild(card);
  }

  function cleanWord(word) {
    return word.replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, "");
  }

  // An email: the text marked word by word, plus the strongest words each way.
  function renderEmailExplanation(container, explanation) {
    clear(container);
    if (!explanation) { return; }

    var words = explanation.words || [];
    var values = explanation.values || [];
    var largest = 0;
    values.forEach(function (value) { largest = Math.max(largest, Math.abs(value)); });

    var card = whyCard("Red words pushed the answer towards phishing, green words towards " +
                       "legitimate. A stronger colour is a bigger push.");

    var text = el("p", "marked-text");
    var joined = words.join("");
    var visible = explanation.visible_text || joined;
    var start = joined ? visible.indexOf(joined) : -1;
    if (start > 0) {
      text.appendChild(document.createTextNode(visible.slice(0, start)));
    }
    words.forEach(function (word, index) {
      var value = values[index] || 0;
      var mark = el("span", "mark-word " + pushClass(value), word);
      var strength = largest > 0 ? 0.75 * Math.abs(value) / largest : 0;
      mark.style.setProperty("--strength", strength.toFixed(2));
      text.appendChild(mark);
    });
    if (start !== -1 && start + joined.length < visible.length) {
      text.appendChild(document.createTextNode(visible.slice(start + joined.length)));
    }
    card.appendChild(text);

    if (explanation.was_cut) {
      card.appendChild(el("p", "why-intro",
        "This email is long. BERT only reads the start of it, so only that part is shown: " +
        "the rest couldn't change the answer."));
    }

    var ranked = [];
    words.forEach(function (word, index) {
      var cleaned = cleanWord(word);
      if (cleaned && values[index]) {
        ranked.push({ word: cleaned, value: values[index] });
      }
    });

    function wordList(items, heading) {
      if (!items.length) { return; }
      var block = el("div", "word-list");
      block.appendChild(el("h4", null, heading));
      items.forEach(function (item) {
        block.appendChild(el("span", "word-chip " + pushClass(item.value),
                             item.word + " (" + pushStrength(item.value) + ")"));
      });
      card.appendChild(block);
    }

    wordList(ranked.filter(function (item) { return item.value > 0; })
                   .sort(function (a, b) { return b.value - a.value; })
                   .slice(0, TOP_EMAIL_WORDS),
             "Words that pushed towards phishing");
    wordList(ranked.filter(function (item) { return item.value < 0; })
                   .sort(function (a, b) { return a.value - b.value; })
                   .slice(0, TOP_EMAIL_WORDS),
             "Words that pushed towards legitimate");

    card.appendChild(methodNote(
      "Method: " + explanation.method + ", " + explanation.max_evals + " re-readings, " +
      Number(explanation.seconds).toFixed(1) + " seconds. Hidden words were replaced with BERT's " +
      "[MASK] token, and with a limited budget neighbouring words can share credit. Values are in " +
      "log-odds: starting score " + formatScore(explanation.base_value) + ", final score " +
      formatScore(explanation.margin) + "."));
    container.appendChild(card);
  }

  // --- The email tab -------------------------------------------------------------

  var emailForm = byId("email-form");
  var emailSubject = byId("email-subject");
  var emailBody = byId("email-body");
  var emailCheck = byId("email-check");
  var emailResult = byId("email-result");
  var emailExplainBlock = byId("email-explain-block");
  var emailExplain = byId("email-explain");
  var emailExplanation = byId("email-explanation");

  emailForm.addEventListener("submit", function (event) {
    event.preventDefault();
    clear(emailExplanation);
    emailExplainBlock.hidden = true;

    var payload = { subject: emailSubject.value, body: emailBody.value };
    if (!payload.subject.trim() && !payload.body.trim()) {
      renderError(emailResult, "Paste a subject or a message first, then press Check this email.");
      return;
    }

    var done = setBusy(emailCheck, "Checking…");
    request("/api/check-email", payload, CHECK_TIMEOUT_MS)
      .then(function (result) {
        renderVerdict(emailResult, result, []);
        emailExplainBlock.hidden = false;
      })
      .catch(function (error) { renderError(emailResult, error.message); })
      .finally(done);
  });

  emailExplain.addEventListener("click", function () {
    var payload = { subject: emailSubject.value, body: emailBody.value };
    var done = setBusy(emailExplain, "Explaining…");
    request("/api/explain-email", payload, EXPLAIN_TIMEOUT_MS)
      .then(function (explanation) { renderEmailExplanation(emailExplanation, explanation); })
      .catch(function (error) { renderError(emailExplanation, error.message); })
      .finally(done);
  });

  // --- The link tab ----------------------------------------------------------------

  var urlForm = byId("url-form");
  var urlInput = byId("url-input");
  var urlCheck = byId("url-check");
  var urlResult = byId("url-result");
  var urlExplanation = byId("url-explanation");

  urlForm.addEventListener("submit", function (event) {
    event.preventDefault();
    clear(urlExplanation);

    var payload = { url: urlInput.value };
    if (!payload.url.trim()) {
      renderError(urlResult, "Paste a web address first, then press Check this link.");
      return;
    }

    var done = setBusy(urlCheck, "Checking…");
    request("/api/check-url", payload, CHECK_TIMEOUT_MS)
      .then(function (result) {
        renderVerdict(urlResult, result, result.warning_signs || []);
        renderLinkExplanation(urlExplanation, result.explanation);
      })
      .catch(function (error) { renderError(urlResult, error.message); })
      .finally(done);
  });

  // --- Examples ----------------------------------------------------------------------

  Array.prototype.forEach.call(document.querySelectorAll("[data-example]"), function (button) {
    button.addEventListener("click", function () {
      var example = EXAMPLES[button.getAttribute("data-example")];
      if (example.url !== undefined) {
        urlInput.value = example.url;
        urlForm.requestSubmit();
      } else {
        emailSubject.value = example.subject;
        emailBody.value = example.body;
        emailForm.requestSubmit();
      }
    });
  });

  // --- Which models answer, and is the server there? -----------------------------------

  // The footer: which models answer, their measured F1, and the honest comparison
  // with any baseline that scored higher on the same test.
  function describeModels(models) {
    var f1 = function (value) { return Number(value).toFixed(4); };
    var served = [];
    var higher = [];
    [["email", "emails"], ["url", "links"]].forEach(function (pair) {
      var model = models[pair[0]];
      if (!model) { return; }
      served.push(pair[1] + " by " + model.name + " (test F1 " + f1(model.test_f1) + ")");
      if (model.best_other_name) {
        higher.push(model.best_other_name + " " + f1(model.best_other_f1) + " for " + pair[1]);
      }
    });
    var text = "";
    if (served.length) {
      text = "Checked with the project's proposed BERT + XGBoost system: " + served.join(", ") + ".";
    }
    if (higher.length) {
      text += " On the same tests, simpler baselines scored slightly higher (" + higher.join(", ") + ").";
    }
    return text;
  }

  request("/api/health", null, CHECK_TIMEOUT_MS)
    .then(function (health) {
      byId("model-info").textContent = describeModels(health.models || {});
    })
    .catch(function () {
      var status = byId("server-status");
      status.textContent = "The model server isn't connected, so checks won't work yet. " +
                           "Start the model server, then reload this page.";
      status.hidden = false;
    });
})();

// Open the link tab when the page is reached as Checker.html#url (the homepage's
// "Check a link" button). Moved here from the bottom of the HTML page.
(function () {
  "use strict";
  if (location.hash === "#url" && window.bootstrap) {
    bootstrap.Tab.getOrCreateInstance(document.getElementById("url-tab")).show();
  }
})();
