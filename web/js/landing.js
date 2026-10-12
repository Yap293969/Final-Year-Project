// Is this a scam? -- landing page motion.
//
// 1. The word in the headline follows the monitor: "link" or "email".
// 2. The four figures count up when the page opens.
// 3. The scan monitor loops through three illustrative examples: it types the
//    input, plays the Lottie shield (animations/shield-scan.json) while
//    "scanning", then shows the verdict and the reasons.
// 4. A few points of light drift in the background.
//
// The examples are illustrations of what a result looks like, not live model
// output; the monitor says so on screen. Text is set with textContent only.
// With "reduce motion" switched on, the page stays still on the first example.

(function () {
  "use strict";

  var reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function wait(ms) {
    return new Promise(function (resolve) { setTimeout(resolve, ms); });
  }

  // --- 1. Headline word -------------------------------------------------------------
  // Follows the scan monitor: "link" while it checks a URL, "email" for an email.

  var heroWord = document.getElementById("hero-word");

  function setHeroWord(word) {
    if (!heroWord || heroWord.textContent === word) return;
    heroWord.classList.add("is-out");
    setTimeout(function () {
      heroWord.textContent = word;
      heroWord.classList.remove("is-out");
    }, 380);
  }

  // --- 2. Count-up figures -------------------------------------------------------------

  function countUp() {
    var items = document.querySelectorAll("[data-count]");
    if (reduceMotion) return;
    items.forEach(function (el) {
      var target = parseFloat(el.getAttribute("data-count"));
      var decimals = parseInt(el.getAttribute("data-decimals"), 10) || 0;
      var duration = 1400;
      var start = null;
      el.textContent = (0).toFixed(decimals);
      function frame(now) {
        if (start === null) start = now;
        var t = Math.min((now - start) / duration, 1);
        var eased = 1 - Math.pow(1 - t, 3);
        el.textContent = (target * eased).toFixed(decimals);
        if (t < 1) requestAnimationFrame(frame);
      }
      setTimeout(function () { requestAnimationFrame(frame); }, 650);
    });
  }

  // --- 3. Scan monitor -------------------------------------------------------------------

  // Reason labels follow the wording the real explanations use (notebook 12.4).
  var EXAMPLES = [
    {
      kind: "URL",
      input: "paypal-secure-login.xyz",
      score: 97,
      tone: "phish",
      verdict: "Phishing",
      flash: "Strongest push: hyphens in the website name",
      reasons: [
        ["phish", "Hyphens in the website name: 2"],
        ["phish", "Suspicious words: secure, login"],
        ["warn", "Website name length: 23 characters"],
        ["warn", "BERT + XGBoost: 97% phishing probability"]
      ]
    },
    {
      kind: "EMAIL",
      input: "Your account has been suspended",
      score: 94,
      tone: "phish",
      verdict: "Phishing",
      flash: "Strongest push: the word “suspended”",
      reasons: [
        ["phish", "“suspended” pushes towards phishing"],
        ["phish", "“verify” pushes towards phishing"],
        ["warn", "“immediately” pushes towards phishing"],
        ["warn", "BERT + XGBoost: 94% phishing probability"]
      ]
    },
    {
      kind: "URL",
      input: "en.wikipedia.org/wiki/Phishing",
      score: 3,
      tone: "safe",
      verdict: "Legitimate",
      flash: "No strong warning signs found",
      reasons: [
        ["safe", "No hyphens or digits in the website name"],
        ["safe", "No suspicious words in the address"],
        ["safe", "Short, ordinary website name"],
        ["safe", "BERT + XGBoost: 3% phishing probability"]
      ]
    }
  ];

  var monitor = {
    body: document.getElementById("monitor-body"),
    kind: document.getElementById("monitor-kind"),
    text: document.getElementById("monitor-text"),
    score: document.getElementById("monitor-score"),
    scoreNum: document.getElementById("monitor-score-num"),
    pill: document.getElementById("monitor-pill"),
    flash: document.getElementById("monitor-flash"),
    flashText: document.getElementById("monitor-flash-text"),
    reasons: document.getElementById("monitor-reasons")
  };

  var shield = null;

  function loadShield() {
    var holder = document.getElementById("scan-lottie");
    if (!holder || !window.lottie) return;
    try {
      shield = window.lottie.loadAnimation({
        container: holder,
        renderer: "svg",
        loop: false,
        autoplay: false,
        path: "animations/shield-scan.json"
      });
      // After the shield has drawn itself (frames 0-30), keep looping the scan.
      shield.addEventListener("complete", function () {
        shield.playSegments([30, 120], true);
      });
    } catch (err) {
      shield = null;
    }
  }

  function playShield() {
    if (!shield) return;
    shield.resetSegments(true);
    shield.goToAndPlay(0, true);
  }

  function stopShield() {
    if (shield) shield.pause();
  }

  function typeInto(el, value) {
    el.textContent = "";
    var chars = Array.from(value);
    var i = 0;
    return new Promise(function (resolve) {
      (function next() {
        if (i >= chars.length) { resolve(); return; }
        el.textContent += chars[i++];
        setTimeout(next, 38 + Math.random() * 45);
      })();
    });
  }

  function countScore(target) {
    var start = null;
    var duration = 700;
    return new Promise(function (resolve) {
      function frame(now) {
        if (start === null) start = now;
        var t = Math.min((now - start) / duration, 1);
        monitor.scoreNum.textContent = String(Math.round(target * (1 - Math.pow(1 - t, 3))));
        if (t < 1) requestAnimationFrame(frame); else resolve();
      }
      requestAnimationFrame(frame);
    });
  }

  function showResult(example) {
    monitor.score.setAttribute("data-tone", example.tone);
    monitor.pill.setAttribute("data-tone", example.tone);
    monitor.flash.setAttribute("data-tone", example.tone);
    monitor.pill.textContent = example.verdict;
    monitor.flashText.textContent = example.flash;

    monitor.reasons.textContent = "";
    example.reasons.forEach(function (reason, index) {
      var li = document.createElement("li");
      li.setAttribute("data-tone", reason[0]);
      li.textContent = reason[1];
      li.className = "is-new";
      li.style.setProperty("--i", String(index));
      monitor.reasons.appendChild(li);
    });

    monitor.body.setAttribute("data-state", "result");
    return countScore(example.score);
  }

  async function runMonitor() {
    if (!monitor.body || reduceMotion) return;
    loadShield();
    await wait(1600); // let the first, static example be read
    var index = 1;
    for (;;) {
      var example = EXAMPLES[index];

      monitor.body.setAttribute("data-state", "scanning");
      monitor.kind.textContent = example.kind;
      setHeroWord(example.kind === "EMAIL" ? "email" : "link");
      playShield();
      await typeInto(monitor.text, example.input);
      await wait(1300);
      stopShield();

      await showResult(example);
      await wait(4200);

      index = (index + 1) % EXAMPLES.length;
    }
  }

  // --- 4. Background points of light -----------------------------------------------------

  function stars() {
    var holder = document.getElementById("bg-stars");
    if (!holder || reduceMotion) return;
    for (var i = 0; i < 28; i++) {
      var s = document.createElement("span");
      s.style.left = (Math.random() * 100).toFixed(2) + "%";
      s.style.top = (Math.random() * 100).toFixed(2) + "%";
      s.style.setProperty("--t", (4 + Math.random() * 6).toFixed(2) + "s");
      s.style.setProperty("--delay", (Math.random() * 6).toFixed(2) + "s");
      holder.appendChild(s);
    }
  }

  countUp();
  stars();
  runMonitor();
})();
