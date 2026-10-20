// Is this a scam? -- Game.html behaviour ("Scam or Safe?").
//
// 1. Start: picks 10 scenarios from js/game-scenarios.js (6 scams and 4 safe
//    messages, in a random order) and shows the first.
// 2. Each round: the card's front shows the situation and the message. The
//    player picks Scam or Safe (a hint is there if they want one). The card
//    flips: the back shows whether they were right, the same message with the
//    clues marked, what each clue means, and the one thing to remember.
// 3. Results: score, a rank, how many scams were caught and real messages
//    trusted, the best streak, and every answer to review.
//    The best score is remembered in this browser (localStorage key
//    "isthisascam-game-best"); if storage is blocked the game still works.
//
// SAFETY: every piece of text is put on screen with textContent, never as
// HTML, the same rule as the rest of the site.
// With "reduce motion" switched on, the card swaps instead of flipping and the
// animations show a still frame.

(function () {
  "use strict";

  var ROUNDS = 10;
  var SCAMS_PER_GAME = 6;
  var BEST_KEY = "isthisascam-game-best";
  var POINTS = 100;        // for a right answer
  var HINT_COST = 50;      // taken off a right answer if the hint was used

  var reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var scenarios = window.GAME_SCENARIOS || [];

  var CHANNEL_NAMES = {
    sms: "Text message", email: "Email", chat: "Chat message", call: "Phone call", web: "Web page"
  };

  var $ = function (id) { return document.getElementById(id); };

  // --- Small helpers ---------------------------------------------------------------

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
  }

  function shuffle(list) {
    var a = list.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  // "[[2|some words]]" -> <mark data-clue="2">some words</mark><span>2</span>, built as DOM nodes.
  // When marked is false the words are plain text, so the clues stay hidden.
  function rich(text, marked) {
    var frag = document.createDocumentFragment();
    var re = /\[\[(\d+)\|([^\]]*)\]\]/g;
    var last = 0, m;
    text = String(text || "");
    while ((m = re.exec(text)) !== null) {
      if (m.index > last) frag.appendChild(document.createTextNode(text.slice(last, m.index)));
      if (marked) {
        var mark = el("mark", "clue-mark", m[2]);
        mark.setAttribute("data-clue", m[1]);
        frag.appendChild(mark);
        var tag = el("span", "clue-tag", m[1]);   // the clue's number, just after the words
        tag.setAttribute("aria-hidden", "true");
        frag.appendChild(tag);
      } else {
        frag.appendChild(document.createTextNode(m[2]));
      }
      last = re.lastIndex;
    }
    if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
    return frag;
  }

  function plain(text) {
    return String(text || "").replace(/\[\[\d+\|([^\]]*)\]\]/g, "$1");
  }

  function richEl(tag, className, text, marked) {
    var node = el(tag, className);
    node.appendChild(rich(text, marked));
    return node;
  }

  function storageGet(key) {
    try { return window.localStorage.getItem(key); } catch (err) { return null; }
  }
  function storageSet(key, value) {
    try { window.localStorage.setItem(key, value); } catch (err) { /* not remembered */ }
  }

  // --- Drawing a message, one function per channel -----------------------------------

  function avatar(name) {
    var letter = plain(name).replace(/[^A-Za-z0-9+]/g, "").charAt(0) || "?";
    return el("span", "msg-avatar", letter === "+" ? "#" : letter.toUpperCase());
  }

  var draw = {
    sms: function (s, marked) {
      var box = el("div", "msg msg--sms");
      var head = el("div", "msg-head");
      head.appendChild(avatar(s.from));
      var who = el("div", "msg-who");
      who.appendChild(richEl("span", "msg-name", s.from, marked));
      who.appendChild(el("span", "msg-meta", "Text message · now"));
      head.appendChild(who);
      box.appendChild(head);
      var thread = el("div", "msg-thread");
      thread.appendChild(richEl("p", "bubble", s.text, marked));
      box.appendChild(thread);
      return box;
    },

    email: function (s, marked) {
      var box = el("div", "msg msg--email");
      var from = el("div", "mail-row");
      from.appendChild(el("span", "mail-label", "From"));
      var who = el("span", "mail-value");
      who.appendChild(el("strong", null, s.fromName + " "));
      var addr = el("span", "mail-address");
      addr.appendChild(document.createTextNode("<"));
      addr.appendChild(rich(s.fromAddress, marked));
      addr.appendChild(document.createTextNode(">"));
      who.appendChild(addr);
      from.appendChild(who);
      box.appendChild(from);

      var subject = el("div", "mail-row");
      subject.appendChild(el("span", "mail-label", "Subject"));
      subject.appendChild(richEl("span", "mail-value mail-subject", s.subject, marked));
      box.appendChild(subject);

      var body = el("div", "mail-body");
      (s.body || []).forEach(function (p) { body.appendChild(richEl("p", null, p, marked)); });
      if (s.button) {
        var fake = el("span", "fake-button", s.button);
        fake.setAttribute("aria-hidden", "true");
        var row = el("p", "fake-button-row");
        row.appendChild(fake);
        body.appendChild(row);
      }
      if (s.linkTarget) {
        var link = el("p", "link-target");
        link.appendChild(document.createTextNode((s.button ? "The button" : "The link") + " goes to: "));
        link.appendChild(richEl("code", null, s.linkTarget, marked));
        body.appendChild(link);
      }
      box.appendChild(body);
      return box;
    },

    chat: function (s, marked) {
      var box = el("div", "msg msg--chat");
      box.appendChild(el("div", "msg-app", s.app || "Chat"));
      var head = el("div", "msg-head");
      head.appendChild(avatar(s.contact));
      var who = el("div", "msg-who");
      who.appendChild(richEl("span", "msg-name", s.contact, marked));
      if (s.contactNote) who.appendChild(richEl("span", "msg-meta", s.contactNote, marked));
      head.appendChild(who);
      box.appendChild(head);
      var thread = el("div", "msg-thread");
      (s.messages || []).forEach(function (m) { thread.appendChild(richEl("p", "bubble", m, marked)); });
      box.appendChild(thread);
      return box;
    },

    call: function (s, marked) {
      var box = el("div", "msg msg--call");
      var head = el("div", "call-head");
      var ring = el("span", "call-icon");
      ring.setAttribute("aria-hidden", "true");
      head.appendChild(ring);
      var who = el("div", "msg-who");
      who.appendChild(richEl("span", "msg-name", s.caller, marked));
      who.appendChild(el("span", "msg-meta", s.label || "Phone call"));
      head.appendChild(who);
      box.appendChild(head);
      var thread = el("div", "msg-thread");
      (s.lines || []).forEach(function (line) {
        var p = el("p", "bubble bubble--call");
        p.appendChild(el("span", "bubble-who", (line.who || "Caller") + ": "));
        p.appendChild(rich(line.text, marked));
        thread.appendChild(p);
      });
      box.appendChild(thread);
      return box;
    },

    web: function (s, marked) {
      var box = el("div", "msg msg--web");
      var bar = el("div", "browser-bar");
      bar.appendChild(el("span", "browser-dots"));
      var url = el("span", "browser-url");
      url.appendChild(el("span", "browser-lock", "🔒"));
      url.appendChild(rich(s.url, marked));
      bar.appendChild(url);
      box.appendChild(bar);
      var page = el("div", "web-page");
      page.appendChild(el("h3", "web-title", s.title));
      (s.body || []).forEach(function (p) { page.appendChild(richEl("p", null, p, marked)); });
      (s.fields || []).forEach(function (f) {
        var field = el("div", "fake-field");
        field.appendChild(richEl("span", "fake-field-label", f, marked));
        field.appendChild(el("span", "fake-field-box"));
        page.appendChild(field);
      });
      if (s.button) {
        var fake = el("span", "fake-button", s.button);
        fake.setAttribute("aria-hidden", "true");
        page.appendChild(fake);
      }
      box.appendChild(page);
      return box;
    }
  };

  function message(s, marked) {
    var wrap = document.createDocumentFragment();
    var chip = el("span", "channel-chip channel-chip--" + s.channel, CHANNEL_NAMES[s.channel] || "Message");
    wrap.appendChild(chip);
    wrap.appendChild((draw[s.channel] || draw.sms)(s, marked));
    return wrap;
  }

  function label(s) {
    var text = { sms: "Text from " + s.from, email: s.subject, chat: "Message from " + s.contact,
      call: "Call from " + s.caller, web: s.title }[s.channel];
    return plain(text);
  }

  // --- Lottie animations ----------------------------------------------------------

  var players = {};

  function loadLottie(name, holderId, opts) {
    var holder = $(holderId);
    if (!holder || !window.lottie) return null;
    try {
      players[name] = window.lottie.loadAnimation({
        container: holder,
        renderer: "svg",
        loop: !!opts.loop && !reduceMotion,
        autoplay: false,
        path: "animations/" + name + ".json"
      });
    } catch (err) {
      players[name] = null;
      return null;
    }
    if (reduceMotion) {
      players[name].addEventListener("DOMLoaded", function () {
        players[name].goToAndStop(opts.still || 0, true);
      });
    }
    return players[name];
  }

  function play(name) {
    var p = players[name];
    if (!p || reduceMotion) return;
    p.goToAndPlay(0, true);
  }
  function stop(name) {
    var p = players[name];
    if (p && !reduceMotion) p.stop();
  }

  // --- Game state -----------------------------------------------------------------

  var game = null;

  function pickRound() {
    var scams = shuffle(scenarios.filter(function (s) { return s.answer === "scam"; }));
    var safes = shuffle(scenarios.filter(function (s) { return s.answer === "safe"; }));
    var nScam = Math.min(SCAMS_PER_GAME, scams.length);
    var nSafe = Math.min(ROUNDS - nScam, safes.length);
    return shuffle(scams.slice(0, nScam).concat(safes.slice(0, nSafe)));
  }

  function show(screen) {
    ["screen-start", "screen-play", "screen-end"].forEach(function (id) {
      $(id).hidden = id !== screen;
    });
    stop("game-cards");
    stop("game-trophy");
    if (screen === "screen-start") play("game-cards");
    if (screen === "screen-end") play("game-trophy");
    window.scrollTo({ top: 0, behavior: "auto" });
  }

  function start() {
    game = { list: pickRound(), index: 0, score: 0, streak: 0, bestStreak: 0, results: [] };
    var dots = $("dots");
    dots.textContent = "";
    game.list.forEach(function (s, n) {
      var dot = el("li", "dot");
      dot.setAttribute("aria-label", "Round " + (n + 1) + ": not played yet");
      dots.appendChild(dot);
    });
    show("screen-play");
    showRound(true);
  }

  // --- A round: the front of the card ------------------------------------------------

  function showRound(first) {
    var s = game.list[game.index];
    var flip = $("flip");

    // Turn the card back to its front without animating.
    flip.classList.add("no-anim");
    flip.classList.remove("is-flipped");
    $("face-front").hidden = false;
    $("face-back").hidden = true;
    void flip.offsetWidth; // apply the change before animations come back
    flip.classList.remove("no-anim");

    $("hud-round").textContent = "Round " + (game.index + 1) + " of " + game.list.length;
    $("front-situation").textContent = s.situation;
    var front = $("front-message");
    front.textContent = "";
    front.appendChild(message(s, false));

    var hintButton = $("hint-button");
    var hintText = $("hint-text");
    hintButton.hidden = false;
    hintButton.setAttribute("aria-expanded", "false");
    hintText.hidden = true;
    hintText.textContent = s.hint || "";
    game.hinted = false;

    $("choose-scam").disabled = false;
    $("choose-safe").disabled = false;

    var dots = $("dots").children;
    for (var i = 0; i < dots.length; i++) dots[i].classList.toggle("is-current", i === game.index);

    // Deal the card in.
    $("face-front").classList.remove("deal");
    void $("face-front").offsetWidth;
    $("face-front").classList.add("deal");

    if (!first) $("front-situation").focus({ preventScroll: true });
    var card = $("flip").getBoundingClientRect();
    if (card.top < 0) $("screen-play").scrollIntoView({ block: "start", behavior: reduceMotion ? "auto" : "smooth" });
  }

  function useHint() {
    game.hinted = true;
    $("hint-text").hidden = false;
    $("hint-button").setAttribute("aria-expanded", "true");
    $("hint-button").hidden = true;
  }

  // --- A round: answering, and the back of the card ------------------------------------

  function answer(choice) {
    var s = game.list[game.index];
    if ($("choose-scam").disabled) return; // already answered
    $("choose-scam").disabled = true;
    $("choose-safe").disabled = true;

    var right = choice === s.answer;
    var points = right ? (game.hinted ? POINTS - HINT_COST : POINTS) : 0;
    game.score += points;
    game.streak = right ? game.streak + 1 : 0;
    game.bestStreak = Math.max(game.bestStreak, game.streak);
    game.results.push({ scenario: s, choice: choice, right: right, hinted: game.hinted, points: points });

    // Progress dot and the score line.
    var dot = $("dots").children[game.index];
    dot.classList.add(right ? "is-right" : "is-wrong");
    dot.setAttribute("aria-label", "Round " + (game.index + 1) + ": " + (right ? "right" : "wrong"));
    $("hud-score").textContent = game.score + " points";
    var streak = $("hud-streak");
    streak.hidden = game.streak < 2;
    streak.textContent = "🔥 " + game.streak + " in a row";

    // The verdict.
    var verdict;
    if (s.answer === "scam") verdict = right ? "Nice catch! It's a scam." : "Careful, this one is a scam.";
    else verdict = right ? "Right! This one is safe." : "Actually, this one is safe.";
    var back = $("face-back");
    back.classList.toggle("is-right", right);
    back.classList.toggle("is-wrong", !right);
    back.classList.toggle("answer-scam", s.answer === "scam");
    back.classList.toggle("answer-safe", s.answer === "safe");
    $("back-verdict").textContent = verdict;
    var sub = s.answer === "scam" ? "Here are the red flags:" : "Here's why it's real:";
    if (right) sub = "+" + points + " points" + (game.hinted ? " (hint used)" : "") + ". " + sub;
    $("back-sub").textContent = sub;

    // The message again, with the clues marked, and what each clue means.
    var marked = $("back-message");
    marked.textContent = "";
    marked.appendChild(message(s, true));
    var list = $("back-clues");
    list.textContent = "";
    s.clues.forEach(function (c) {
      var li = el("li", "clue");
      li.setAttribute("data-clue", c.n);
      li.appendChild(el("span", "clue-no", String(c.n)));
      var text = el("span", "clue-text");
      text.appendChild(el("strong", null, c.title + ". "));
      text.appendChild(document.createTextNode(c.text));
      li.appendChild(text);
      li.addEventListener("mouseenter", function () { highlight(c.n); });
      li.addEventListener("mouseleave", function () { highlight(null); });
      list.appendChild(li);
    });
    $("back-takeaway").textContent = s.takeaway;
    $("back-learn").href = "Learn.html" + (s.learn || "");
    $("next-button").firstChild.textContent =
      game.index + 1 < game.list.length ? "Next message " : "See my results ";

    // Feedback animation.
    $("lottie-correct").hidden = !right;
    $("lottie-wrong").hidden = right;
    play(right ? "game-correct" : "game-wrong");

    $("announce").textContent = verdict + " " + s.takeaway;
    flipToBack();
  }

  function highlight(n) {
    var marks = $("back-message").querySelectorAll(".clue-mark");
    for (var i = 0; i < marks.length; i++) {
      marks[i].classList.toggle("is-active", String(n) === marks[i].getAttribute("data-clue"));
    }
  }

  function flipToBack() {
    var flip = $("flip");
    var front = $("face-front");
    var back = $("face-back");
    back.hidden = false;
    var done = false;
    function finish() {
      if (done) return;
      done = true;
      front.hidden = true;
      $("back-verdict").focus({ preventScroll: true });
      var top = flip.getBoundingClientRect().top;
      if (top < 0) flip.scrollIntoView({ block: "start", behavior: reduceMotion ? "auto" : "smooth" });
    }
    if (reduceMotion) {
      flip.classList.add("no-anim");
      flip.classList.add("is-flipped");
      finish();
      return;
    }
    void flip.offsetWidth;
    flip.classList.add("is-flipped");
    flip.querySelector(".flip-inner").addEventListener("transitionend", finish, { once: true });
    window.setTimeout(finish, 900); // in case the transition event never comes
  }

  function next() {
    game.index += 1;
    if (game.index < game.list.length) showRound(false);
    else finishGame();
  }

  // --- Results ----------------------------------------------------------------------

  var RANKS = [
    { min: 10, rank: "Scam Spotter Pro", line: "A perfect round! Scammers don't stand a chance against you." },
    { min: 8, rank: "Sharp Eyes", line: "Great instincts. Have a look at the one or two that got past you." },
    { min: 6, rank: "Getting There", line: "Good start. A few tricks still got through, so check them below." },
    { min: 0, rank: "Keep Practising", line: "Scams are made to fool people. Read the guide, then try again: you'll get better fast." }
  ];

  function finishGame() {
    var right = game.results.filter(function (r) { return r.right; }).length;
    var total = game.results.length;
    var scamRounds = game.results.filter(function (r) { return r.scenario.answer === "scam"; });
    var safeRounds = game.results.filter(function (r) { return r.scenario.answer === "safe"; });
    var count = function (list) { return list.filter(function (r) { return r.right; }).length; };

    var best = parseInt(storageGet(BEST_KEY) || "0", 10) || 0;
    var newBest = game.score > best;
    if (newBest) { best = game.score; storageSet(BEST_KEY, String(best)); }

    var rank = RANKS.filter(function (r) { return right >= r.min * total / ROUNDS; })[0];
    $("end-rank").textContent = rank.rank;
    $("end-title").textContent = "You got " + right + " out of " + total + " right";
    $("end-line").textContent = rank.line + " (" + game.score + " points" + (newBest ? ", a new best!" : "") + ")";
    $("stat-scams").textContent = count(scamRounds) + " / " + scamRounds.length;
    $("stat-safe").textContent = count(safeRounds) + " / " + safeRounds.length;
    $("stat-streak").textContent = String(game.bestStreak);
    $("stat-best").textContent = best + " points";

    var review = $("review");
    review.textContent = "";
    game.results.forEach(function (r) {
      var s = r.scenario;
      var li = el("li", "review-item " + (r.right ? "is-right" : "is-wrong"));
      li.appendChild(el("span", "review-mark", r.right ? "✓" : "✗"));
      var body = el("div", "review-body");
      var head = el("p", "review-head");
      head.appendChild(el("span", "channel-chip channel-chip--" + s.channel, CHANNEL_NAMES[s.channel]));
      head.appendChild(el("strong", null, label(s)));
      body.appendChild(head);
      body.appendChild(el("p", "review-answer",
        "It was " + (s.answer === "scam" ? "a scam" : "safe") + ". You said " +
        (r.choice === "scam" ? "scam" : "safe") + (r.hinted ? " (with a hint)" : "") + "."));
      body.appendChild(el("p", "review-takeaway", s.takeaway));
      li.appendChild(body);
      review.appendChild(li);
    });

    show("screen-end");
    $("end-title").focus({ preventScroll: true });
  }

  // --- Background points of light (as on the other pages) --------------------------------

  function stars() {
    var holder = $("bg-stars");
    if (!holder || reduceMotion) return;
    for (var i = 0; i < 22; i++) {
      var s = document.createElement("span");
      s.style.left = (Math.random() * 100).toFixed(2) + "%";
      s.style.top = (Math.random() * 100).toFixed(2) + "%";
      s.style.setProperty("--t", (5 + Math.random() * 6).toFixed(2) + "s");
      s.style.setProperty("--delay", (Math.random() * 6).toFixed(2) + "s");
      holder.appendChild(s);
    }
  }

  // --- Start up -------------------------------------------------------------------------

  function init() {
    if (!scenarios.length) {
      $("start-button").disabled = true;
      $("best-line").hidden = false;
      $("best-line").textContent = "The scenarios couldn't be loaded (js/game-scenarios.js).";
      return;
    }
    stars();
    loadLottie("game-cards", "lottie-cards", { loop: true, still: 40 });
    loadLottie("game-correct", "lottie-correct", { still: 44 });
    loadLottie("game-wrong", "lottie-wrong", { still: 44 });
    loadLottie("game-trophy", "lottie-trophy", { loop: true, still: 55 });
    if (players["game-cards"]) {
      players["game-cards"].addEventListener("DOMLoaded", function () {
        if (!$("screen-start").hidden) play("game-cards");
      });
    }

    var best = parseInt(storageGet(BEST_KEY) || "0", 10) || 0;
    if (best > 0) {
      $("best-line").hidden = false;
      $("best-line").textContent = "Your best score so far: " + best + " points";
    }

    $("start-button").addEventListener("click", start);
    $("again-button").addEventListener("click", start);
    $("choose-scam").addEventListener("click", function () { answer("scam"); });
    $("choose-safe").addEventListener("click", function () { answer("safe"); });
    $("hint-button").addEventListener("click", useHint);
    $("next-button").addEventListener("click", next);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
