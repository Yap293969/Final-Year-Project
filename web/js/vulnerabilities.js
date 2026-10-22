// Is this a scam? -- Vulnerabilities.html behaviour (the "Hidden weak spots" page).
//
// The page's words and facts live in data/vulnerabilities.json, so they can be
// checked against CISA's list (scripts/check_vulnerability_data.py) and edited
// without touching the HTML. This file reads that JSON and builds:
//
//   1. the six words to know (part 01)
//   2. "How to read a CVE ID" (part 01)
//   3. the six real cases, with filters and a "What happened?" button (part 03)
//   4. the quick check, four questions with instant feedback (part 05)
//   5. the footer note saying when the facts were last checked
//
// Animations, fade-ins and the chapter bar come from js/learn.js, as on Learn.html.
//
// SAFETY: everything is put on screen with textContent, never as HTML, and only
// https:// links are made clickable.

(function () {
  "use strict";

  var DATA_URL = "data/vulnerabilities.json";

  var ICONS = {
    document: "📄", // page
    email: "✉️",     // envelope
    archive: "🗂️", // card index dividers (a folder of files)
    phone: "📱",    // mobile phone
    browser: "🌐"   // globe
  };
  var MONTHS = ["January", "February", "March", "April", "May", "June", "July",
                "August", "September", "October", "November", "December"];

  // --- Small helpers ------------------------------------------------------------

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  function monthYear(isoDate) {
    var parts = String(isoDate || "").split("-");
    var month = parseInt(parts[1], 10);
    if (parts.length < 2 || !(month >= 1 && month <= 12)) return String(isoDate || "");
    return MONTHS[month - 1] + " " + parts[0];
  }

  function dayMonthYear(isoDate) {
    var parts = String(isoDate || "").split("-");
    if (parts.length !== 3) return String(isoDate || "");
    return parseInt(parts[2], 10) + " " + monthYear(isoDate);
  }

  function safeLink(url, text) {
    url = String(url || "");
    if (url.indexOf("https://") !== 0) return el("span", null, text);
    var a = el("a", null, text);
    a.href = url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    return a;
  }

  // --- 1. Six words to know ---------------------------------------------------------

  function renderGlossary(list, glossary) {
    (glossary || []).forEach(function (item) {
      var li = el("li", "word");
      li.appendChild(el("h3", null, item.term));
      li.appendChild(el("p", null, item.plain));
      var like = el("p", "word-like");
      like.appendChild(el("span", null, "Like: "));
      like.appendChild(document.createTextNode(item.like));
      li.appendChild(like);
      list.appendChild(li);
    });
  }

  // --- 2. How to read a CVE ID -------------------------------------------------------

  function renderAnatomy(holder, anatomy) {
    if (!anatomy || !anatomy.parts) return;
    var id = el("p", "cve-id");
    id.setAttribute("aria-label", anatomy.id);
    anatomy.parts.forEach(function (part, n) {
      if (n > 0) id.appendChild(el("span", "cve-dash", "-"));
      id.appendChild(el("span", "cve-part cve-part--" + part.role, part.text));
    });
    holder.appendChild(id);

    var keys = el("ul", "cve-keys");
    anatomy.parts.forEach(function (part) {
      var li = el("li", "cve-key cve-key--" + part.role);
      li.appendChild(el("code", null, part.text));
      li.appendChild(el("span", null, part.means));
      keys.appendChild(li);
    });
    holder.appendChild(keys);
  }

  // --- 3. Six real cases ---------------------------------------------------------------

  function renderCase(example, index) {
    var noClick = example.click && example.click.level === "none";
    var li = el("li", "case" + (noClick ? " case--noclick" : ""));
    li.dataset.kind = example.kind;
    li.dataset.noclick = noClick ? "1" : "0";

    var head = el("div", "case-head");
    head.appendChild(el("span", "case-icon", ICONS[example.icon] || "⚠️"));
    var titles = el("div", "case-titles");
    titles.appendChild(el("h3", null, example.nickname));
    titles.appendChild(el("code", "case-id", example.id));
    head.appendChild(titles);
    li.appendChild(head);

    li.appendChild(el("p", "case-app", example.app));

    var facts = el("dl", "case-facts");
    facts.appendChild(el("dt", null, "How it arrived"));
    facts.appendChild(el("dd", null, example.arrived));
    facts.appendChild(el("dt", null, "What you had to do"));
    var click = el("dd");
    click.appendChild(el("span", "click-chip click-chip--" + (noClick ? "none" : "open"),
                         example.click ? example.click.text : ""));
    facts.appendChild(click);
    li.appendChild(facts);

    li.appendChild(el("p", "kev-chip",
                      "On CISA's list since " + monthYear(example.kev && example.kev.dateAdded)));

    var storyId = "case-story-" + index;
    var button = el("button", "case-more", "What happened?");
    button.type = "button";
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("aria-controls", storyId);
    li.appendChild(button);

    var story = el("div", "case-story");
    story.id = storyId;
    story.hidden = true;
    story.appendChild(el("p", null, example.trap));
    var fixed = el("p", "case-fixed");
    fixed.appendChild(el("strong", null, "Fixed by: "));
    fixed.appendChild(document.createTextNode(example.fixed));
    story.appendChild(fixed);
    var lesson = el("p", "case-lesson");
    lesson.appendChild(el("strong", null, "Lesson: "));
    lesson.appendChild(document.createTextNode(example.lesson));
    story.appendChild(lesson);
    if (example.sources && example.sources.length) {
      var sources = el("ul", "case-sources");
      sources.setAttribute("aria-label", "Sources");
      example.sources.forEach(function (source) {
        var item = el("li");
        item.appendChild(safeLink(source.url, source.title));
        sources.appendChild(item);
      });
      story.appendChild(sources);
    }
    li.appendChild(story);

    button.addEventListener("click", function () {
      var open = story.hidden;
      story.hidden = !open;
      li.classList.toggle("is-open", open);
      button.setAttribute("aria-expanded", open ? "true" : "false");
      button.textContent = open ? "Hide the story" : "What happened?";
    });
    return li;
  }

  function renderCases(list, examples) {
    (examples || []).forEach(function (example, n) { list.appendChild(renderCase(example, n)); });
  }

  function setUpFilters(holder, list) {
    var buttons = holder.querySelectorAll(".case-filter");
    buttons.forEach(function (button) {
      button.addEventListener("click", function () {
        var filter = button.dataset.filter;
        buttons.forEach(function (b) {
          var on = b === button;
          b.classList.toggle("is-active", on);
          b.setAttribute("aria-pressed", on ? "true" : "false");
        });
        list.querySelectorAll(".case").forEach(function (card) {
          var show = filter === "all" ||
            (filter === "noclick" ? card.dataset.noclick === "1" : card.dataset.kind === filter);
          card.hidden = !show;
        });
      });
    });
  }

  // --- 4. Quick check ------------------------------------------------------------------

  function renderQuiz(list, scoreLine, quiz) {
    var answered = 0;
    var right = 0;
    (quiz || []).forEach(function (item) {
      var li = el("li", "vq-item");
      li.appendChild(el("p", "vq-question", item.question));
      var options = el("div", "vq-options");
      options.setAttribute("role", "group");
      options.setAttribute("aria-label", item.question);
      var feedback = el("p", "vq-feedback");
      feedback.setAttribute("aria-live", "polite");

      item.options.forEach(function (text, n) {
        var button = el("button", "vq-option", text);
        button.type = "button";
        button.addEventListener("click", function () {
          var correct = n === item.answer;
          options.querySelectorAll("button").forEach(function (b, m) {
            b.disabled = true;
            if (m === item.answer) b.classList.add("is-right");
          });
          if (!correct) button.classList.add("is-wrong");
          li.classList.add(correct ? "got-right" : "got-wrong");
          feedback.textContent = (correct ? "Correct! " : "Not quite. ") + item.explain;
          answered += 1;
          if (correct) right += 1;
          if (answered === quiz.length) {
            scoreLine.textContent = "You got " + right + " out of " + quiz.length + ". " +
              (right === quiz.length ? "Perfect — you know why updates matter."
                                     : "Have a look at the cases above, then try the game.");
          }
        });
        options.appendChild(button);
      });
      li.appendChild(options);
      li.appendChild(feedback);
      list.appendChild(li);
    });
  }

  // --- 5. When the facts were checked ----------------------------------------------------

  function renderSourcesNote(note, data) {
    var catalogue = data.catalogue || {};
    note.textContent = "A guide made for a Final Year Project research prototype. The six cases " +
      "are real. Their facts were checked on " + dayMonthYear(data.checked) + " against ";
    note.appendChild(safeLink(catalogue.url, catalogue.name || "CISA's catalogue"));
    note.appendChild(document.createTextNode(
      " (version " + catalogue.version + ", " + Number(catalogue.count).toLocaleString("en") +
      " entries) and the reports linked on each case."));
  }

  // --- Start ------------------------------------------------------------------------------

  function showError() {
    var box = document.getElementById("data-error");
    if (box) {
      box.textContent = "This page couldn't load its examples. If you opened the file straight " +
        "from your computer, open it through a web server instead (for example Laragon, or the " +
        "Netlify site).";
      box.hidden = false;
    }
    var filters = document.getElementById("case-filters");
    if (filters) filters.hidden = true;
  }

  function start() {
    fetch(DATA_URL)
      .then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status);
        return response.json();
      })
      .then(function (data) {
        renderGlossary(document.getElementById("glossary"), data.glossary);
        renderAnatomy(document.getElementById("anatomy"), data.anatomy);
        var cases = document.getElementById("cases-list");
        renderCases(cases, data.examples);
        setUpFilters(document.getElementById("case-filters"), cases);
        renderQuiz(document.getElementById("quiz-list"), document.getElementById("quiz-score"),
                   data.quiz);
        renderSourcesNote(document.getElementById("sources-note"), data);
      })
      .catch(showError);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
