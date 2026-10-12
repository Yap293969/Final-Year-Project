// Is this a scam? -- colour theme setting (Default, Dark, Light).
//
// Loaded in <head> on every page, before the page is drawn, so the chosen
// theme is in place from the first frame (no flash of the wrong colours).
//
// 1. Reads the visitor's choice from this browser's storage ("default" if none).
// 2. Puts it on <html data-theme="...">; css/theme.css holds the colours.
//    It also sets Bootstrap's own data-bs-theme, so form fields and alerts
//    follow along.
// 3. Adds a "Theme" button to the top-right corner of the page. It opens a
//    small panel with the three choices.
//
// The choice is only remembered in this browser. If storage is blocked (some
// private windows), the theme still changes, it is just not remembered.

(function () {
  "use strict";

  var STORAGE_KEY = "isthisascam-theme";

  var THEMES = [
    { id: "default", label: "Default", hint: "Navy blue, the original", bar: "#0a0f1f" },
    { id: "dark", label: "Dark", hint: "Near-black, less blue", bar: "#060607" },
    { id: "light", label: "Light", hint: "Bright, for daylight", bar: "#f4f6fb" }
  ];

  var root = document.documentElement;

  function isTheme(id) {
    return THEMES.some(function (t) { return t.id === id; });
  }

  function readSaved() {
    try {
      var saved = window.localStorage.getItem(STORAGE_KEY);
      return isTheme(saved) ? saved : "default";
    } catch (err) {
      return "default";
    }
  }

  function save(id) {
    try {
      window.localStorage.setItem(STORAGE_KEY, id);
    } catch (err) {
      // Storage blocked: the theme still applies for this visit.
    }
  }

  function apply(id) {
    var theme = THEMES.filter(function (t) { return t.id === id; })[0] || THEMES[0];
    root.setAttribute("data-theme", theme.id);
    root.setAttribute("data-bs-theme", theme.id === "light" ? "light" : "dark");
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", theme.bar);
  }

  // --- 1 + 2. Apply straight away --------------------------------------------------

  var current = readSaved();
  apply(current);

  // --- 3. The settings button --------------------------------------------------------

  var ICON_GEAR =
    '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="3"/>' +
    '<path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 ' +
    '1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 ' +
    '1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 ' +
    '1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 ' +
    '1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 ' +
    '1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/></svg>';

  var ICON_CHECK = '<svg class="theme-check" viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg>';

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function buildControl() {
    var wrap = el("div", "theme-settings");

    var toggle = el("button", "theme-toggle");
    toggle.type = "button";
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-controls", "theme-panel");
    toggle.setAttribute("aria-label", "Theme settings");
    toggle.innerHTML = ICON_GEAR; // fixed markup written above, never user input
    toggle.appendChild(el("span", "theme-toggle-label", "Theme"));

    var panel = el("div", "theme-panel");
    panel.id = "theme-panel";
    panel.hidden = true;
    panel.appendChild(el("p", "theme-panel-title", "Appearance"));
    panel.appendChild(el("p", "theme-panel-note", "Saved in this browser."));

    var group = el("div", "theme-options");
    group.setAttribute("role", "radiogroup");
    group.setAttribute("aria-label", "Colour theme");

    var buttons = THEMES.map(function (theme) {
      var option = el("button", "theme-option");
      option.type = "button";
      option.setAttribute("role", "radio");
      option.setAttribute("data-theme-choice", theme.id);

      option.appendChild(el("span", "theme-swatch theme-swatch--" + theme.id));
      var text = el("span", "theme-option-text");
      text.appendChild(el("span", null, theme.label));
      text.appendChild(el("span", "theme-option-hint", theme.hint));
      option.appendChild(text);
      option.insertAdjacentHTML("beforeend", ICON_CHECK);

      option.addEventListener("click", function () { choose(theme.id); });
      group.appendChild(option);
      return option;
    });

    panel.appendChild(group);
    wrap.appendChild(toggle);
    wrap.appendChild(panel);

    function markChecked() {
      buttons.forEach(function (b) {
        var on = b.getAttribute("data-theme-choice") === current;
        b.setAttribute("aria-checked", on ? "true" : "false");
        b.tabIndex = on ? 0 : -1; // one tab stop for the group; arrows move inside it
      });
    }

    function choose(id) {
      if (id === current) return;
      current = id;
      save(id);
      var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      // A soft cross-fade where the browser supports it; an instant switch elsewhere.
      if (document.startViewTransition && !reduce) {
        document.startViewTransition(function () { apply(id); });
      } else {
        apply(id);
      }
      markChecked();
    }

    function open() {
      panel.hidden = false;
      toggle.setAttribute("aria-expanded", "true");
      var checked = buttons.filter(function (b) { return b.getAttribute("aria-checked") === "true"; })[0];
      if (checked) checked.focus();
    }

    function close(returnFocus) {
      if (panel.hidden) return;
      panel.hidden = true;
      toggle.setAttribute("aria-expanded", "false");
      if (returnFocus) toggle.focus();
    }

    toggle.addEventListener("click", function () {
      if (panel.hidden) open(); else close(false);
    });

    // Arrow keys move between the three choices (and pick them), like radio buttons.
    group.addEventListener("keydown", function (event) {
      var step = { ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1 }[event.key];
      if (!step) return;
      event.preventDefault();
      var index = THEMES.map(function (t) { return t.id; }).indexOf(current);
      var next = (index + step + THEMES.length) % THEMES.length;
      choose(THEMES[next].id);
      buttons[next].focus();
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") close(true);
    });

    document.addEventListener("click", function (event) {
      if (!wrap.contains(event.target)) close(false);
    });

    // Another tab of this site changed the theme: follow it.
    window.addEventListener("storage", function (event) {
      if (event.key === STORAGE_KEY && isTheme(event.newValue)) {
        current = event.newValue;
        apply(current);
        markChecked();
      }
    });

    markChecked();
    document.body.appendChild(wrap);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", buildControl);
  } else {
    buildControl();
  }
})();
