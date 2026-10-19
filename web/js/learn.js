// Is this a scam? -- Learn.html behaviour.
//
// 1. Plays each section's Lottie animation (animations/learn-*.json) only while
//    it is on screen, and loads it just before it scrolls into view.
// 2. Fades each part of the page in as it scrolls into view.
// 3. The chapter bar: highlights the part being read and fills the progress line.
// 4. Practice email (part 03): "Show the red flags" reveals the marks, and
//    picking a flag in the list lights up the matching words.
// 5. Link quiz (part 04): "Reveal" shows who really owns each link.
// 6. A few points of light drift in the background (as on the homepage).
//
// Loaded in <head>, so it can add the "js" class before the page is drawn: the
// fade-in styles only apply when JavaScript runs, so without it nothing is hidden.
// With "reduce motion" switched on, animations show a still frame and nothing fades.
// All text on the page is static HTML; this file never builds HTML from strings.

document.documentElement.classList.add("js");

(function () {
  "use strict";

  var reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var canObserve = "IntersectionObserver" in window;

  // --- 1. Lottie animations ---------------------------------------------------------

  function setUpLottie(holder) {
    if (!window.lottie || holder.dataset.loaded) return null;
    holder.dataset.loaded = "1";
    var loopFrom = parseInt(holder.dataset.loopFrom || "0", 10);
    var still = parseInt(holder.dataset.still || "0", 10);
    var player;
    try {
      player = window.lottie.loadAnimation({
        container: holder,
        renderer: "svg",
        loop: !loopFrom,
        autoplay: false,
        path: holder.dataset.lottie
      });
    } catch (err) {
      return null;
    }
    if (reduceMotion) {
      // One still frame that tells the story, and no movement.
      player.addEventListener("DOMLoaded", function () { player.goToAndStop(still, true); });
      return null;
    }
    if (loopFrom) {
      // Draw in once (frames 0..loopFrom), then keep looping the rest.
      player.addEventListener("complete", function () {
        player.playSegments([loopFrom, player.totalFrames], true);
        player.loop = true;
      });
    }
    return player;
  }

  function lotties() {
    var holders = document.querySelectorAll("[data-lottie]");
    if (!holders.length) return;

    if (!canObserve) {
      holders.forEach(function (h) {
        var p = setUpLottie(h);
        if (p) p.play();
      });
      return;
    }

    // Load a little before it arrives, play only while visible (saves battery).
    var loader = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        loader.unobserve(e.target);
        e.target._player = setUpLottie(e.target);
        if (e.target._player) player.observe(e.target);
      });
    }, { rootMargin: "300px 0px" });

    var player = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var p = e.target._player;
        if (!p) return;
        if (e.isIntersecting) p.play(); else p.pause();
      });
    }, { threshold: 0.15 });

    holders.forEach(function (h) { loader.observe(h); });
  }

  // --- 2. Fade in on scroll ----------------------------------------------------------

  // Anything whose top has come up into the screen is shown -- including parts
  // already scrolled past, so jumping with the chapter bar never leaves gaps.
  function fadeIns() {
    var waiting = Array.prototype.slice.call(document.querySelectorAll(".fade-up"));
    if (reduceMotion) {
      waiting.forEach(function (el) { el.classList.add("is-in"); });
      return;
    }
    waiting.forEach(function (el) {
      // Cards in the same row arrive one after another.
      var row = el.parentElement ? el.parentElement.children : [];
      var index = Array.prototype.indexOf.call(row, el);
      if (index > 0) el.style.transitionDelay = Math.min(index, 5) * 70 + "ms";
    });

    function check() {
      var line = window.innerHeight * 0.92;
      waiting = waiting.filter(function (el) {
        if (el.getBoundingClientRect().top < line) {
          el.classList.add("is-in");
          return false;
        }
        return true;
      });
      if (!waiting.length) window.removeEventListener("scroll", onScroll);
    }
    var queued = false;
    function onScroll() {
      if (queued) return;
      queued = true;
      window.requestAnimationFrame(function () { queued = false; check(); });
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    check();
  }

  // --- 3. Chapter bar ----------------------------------------------------------------

  function chapters() {
    var links = Array.prototype.slice.call(document.querySelectorAll(".chapter"));
    var bar = document.getElementById("read-progress");
    var sections = links.map(function (a) {
      return document.querySelector(a.getAttribute("href"));
    });

    function update() {
      var doc = document.documentElement;
      var max = doc.scrollHeight - window.innerHeight;
      if (bar) bar.style.width = (max > 0 ? Math.min(100, (window.scrollY / max) * 100) : 0) + "%";

      // The current part is the last one whose top has passed a third of the screen.
      var line = window.innerHeight / 3;
      var current = -1;
      sections.forEach(function (s, n) {
        if (s && s.getBoundingClientRect().top <= line) current = n;
      });
      links.forEach(function (a, n) {
        var on = n === current;
        a.classList.toggle("is-current", on);
        if (on) a.setAttribute("aria-current", "true"); else a.removeAttribute("aria-current");
      });
      // On a phone the bar scrolls sideways: keep the current chip in view.
      if (current >= 0 && links[current] !== chapters.last) {
        chapters.last = links[current];
        var strip = links[current].parentElement;
        var left = links[current].offsetLeft - strip.clientWidth / 2 + links[current].clientWidth / 2;
        strip.scrollTo({ left: Math.max(0, left), behavior: reduceMotion ? "auto" : "smooth" });
      }
    }

    var queued = false;
    window.addEventListener("scroll", function () {
      if (queued) return;
      queued = true;
      window.requestAnimationFrame(function () { queued = false; update(); });
    }, { passive: true });
    window.addEventListener("resize", update);
    update();
  }

  // --- 4. Practice email: red flags --------------------------------------------------

  function redFlags() {
    var practice = document.getElementById("practice");
    var toggle = document.getElementById("flags-toggle");
    if (!practice || !toggle) return;
    var items = practice.querySelectorAll(".flag-list button");
    var marks = practice.querySelectorAll("mark.flag");

    function pick(number) {
      items.forEach(function (b) { b.classList.toggle("is-active", b.dataset.flag === number); });
      marks.forEach(function (m) { m.classList.toggle("is-active", m.dataset.flag === number); });
    }

    toggle.addEventListener("click", function () {
      var on = !practice.classList.contains("show-flags");
      practice.classList.toggle("show-flags", on);
      toggle.setAttribute("aria-pressed", on ? "true" : "false");
      toggle.textContent = on ? "Hide the red flags" : "Show the red flags";
      items.forEach(function (b) { b.tabIndex = on ? 0 : -1; });
      if (!on) pick(null);
    });

    items.forEach(function (b) {
      b.tabIndex = -1; // not reachable until the flags are shown
      b.addEventListener("click", function () {
        pick(b.classList.contains("is-active") ? null : b.dataset.flag);
      });
    });
  }

  // --- 5. Link quiz -------------------------------------------------------------------

  function linkQuiz() {
    document.querySelectorAll(".quiz-card").forEach(function (card) {
      var button = card.querySelector(".quiz-reveal");
      var answer = card.querySelector(".quiz-answer");
      if (!button || !answer) return;
      button.addEventListener("click", function () {
        var open = answer.hidden;
        answer.hidden = !open;
        card.classList.toggle("is-revealed", open);
        button.setAttribute("aria-expanded", open ? "true" : "false");
        button.textContent = open ? "Hide" : "Reveal";
      });
    });
  }

  // --- 6. Background points of light ---------------------------------------------------

  function stars() {
    var holder = document.getElementById("bg-stars");
    if (!holder || reduceMotion) return;
    for (var i = 0; i < 26; i++) {
      var s = document.createElement("span");
      s.style.left = (Math.random() * 100).toFixed(2) + "%";
      s.style.top = (Math.random() * 100).toFixed(2) + "%";
      s.style.setProperty("--t", (5 + Math.random() * 6).toFixed(2) + "s");
      s.style.setProperty("--delay", (Math.random() * 6).toFixed(2) + "s");
      holder.appendChild(s);
    }
  }

  function start() {
    stars();
    fadeIns();
    lotties();
    chapters();
    redFlags();
    linkQuiz();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
