// Is this a scam? -- Login.html behaviour (log in and sign up).
//
// Two forms on one card: "Log in" (email + password) and "Sign up" (first name,
// last name, email, password). Login.html#signup opens the sign-up form.
// Both send JSON to the accounts API (api/login.php, api/signup.php) through
// js/auth.js. On success the visitor goes back to the page they came from
// (?next=Game.html), or to My records (Account.html).
//
// The checks here only save a round trip; api/signup.php checks everything again.
// SAFETY: every message is put on screen with textContent, never as HTML.

(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var PASSWORD_MIN = 8;
  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  // Only go on to one of this site's own pages, never to another website.
  function nextPage() {
    var next = new URLSearchParams(location.search).get("next") || "";
    return /^[A-Za-z]+\.html(#[A-Za-z0-9_-]+)?$/.test(next) && next.indexOf("Login.html") !== 0
      ? next : "Account.html";
  }

  // --- Switching between the two forms -------------------------------------------

  var tabs = { login: $("tab-login"), signup: $("tab-signup") };
  var forms = { login: $("login-form"), signup: $("signup-form") };
  var TITLES = { login: "Welcome back", signup: "Create your account" };

  function show(which, focus) {
    Object.keys(tabs).forEach(function (key) {
      var on = key === which;
      tabs[key].setAttribute("aria-selected", on ? "true" : "false");
      tabs[key].tabIndex = on ? 0 : -1;
      forms[key].hidden = !on;
    });
    $("auth-title").textContent = TITLES[which];
    document.title = (which === "signup" ? "Sign up" : "Log in") + " — Is this a scam?";
    if (history.replaceState) {
      history.replaceState(null, "", location.pathname + location.search + (which === "signup" ? "#signup" : ""));
    }
    if (focus) forms[which].querySelector("input").focus();
  }

  tabs.login.addEventListener("click", function () { show("login", true); });
  tabs.signup.addEventListener("click", function () { show("signup", true); });
  $("tab-login").parentNode.addEventListener("keydown", function (event) {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    var which = tabs.login.getAttribute("aria-selected") === "true" ? "signup" : "login";
    show(which, false);
    tabs[which].focus();
  });
  Array.prototype.forEach.call(document.querySelectorAll("[data-go]"), function (button) {
    button.addEventListener("click", function () { show(button.getAttribute("data-go"), true); });
  });

  // --- Show / hide password ------------------------------------------------------------

  Array.prototype.forEach.call(document.querySelectorAll("[data-toggle-for]"), function (button) {
    var input = $(button.getAttribute("data-toggle-for"));
    button.addEventListener("click", function () {
      var showing = input.type === "text";
      input.type = showing ? "password" : "text";
      button.textContent = showing ? "Show" : "Hide";
      button.setAttribute("aria-pressed", showing ? "false" : "true");
      input.focus();
    });
  });

  // --- Messages next to the fields ---------------------------------------------------

  function setFieldError(form, field, message) {
    var box = $(form + "-" + field + "-error");
    var input = forms[form].querySelector('[name="' + field + '"]');
    if (!box || !input) return;
    box.textContent = message || "";
    box.hidden = !message;
    if (message) input.setAttribute("aria-invalid", "true");
    else input.removeAttribute("aria-invalid");
    if (message) input.setAttribute("aria-errormessage", box.id);
  }

  function clearErrors(form) {
    $(form + "-error").hidden = true;
    Array.prototype.forEach.call(forms[form].querySelectorAll("[name]"), function (input) {
      setFieldError(form, input.name, "");
    });
  }

  function showFormError(form, message) {
    var box = $(form + "-error");
    box.textContent = message;
    box.hidden = false;
  }

  function focusFirstError(form) {
    var bad = forms[form].querySelector('[aria-invalid="true"]');
    if (bad) bad.focus();
  }

  function setBusy(button, busyText) {
    var original = button.textContent;
    button.disabled = true;
    button.textContent = busyText;
    return function () { button.disabled = false; button.textContent = original; };
  }

  function handleFailure(form, error) {
    var fields = (error && error.fields) || {};
    Object.keys(fields).forEach(function (name) { setFieldError(form, name, fields[name]); });
    showFormError(form, (error && error.message) || "Something went wrong. Please try again.");
    focusFirstError(form);
  }

  // --- Log in ----------------------------------------------------------------------------

  forms.login.addEventListener("submit", function (event) {
    event.preventDefault();
    clearErrors("login");
    var email = $("login-email").value.trim();
    var password = $("login-password").value;
    var ok = true;
    if (!EMAIL_RE.test(email)) { setFieldError("login", "email", "Enter the email you signed up with."); ok = false; }
    if (!password) { setFieldError("login", "password", "Enter your password."); ok = false; }
    if (!ok) { focusFirstError("login"); return; }

    var done = setBusy($("login-submit"), "Logging in…");
    Account.request("login.php", { email: email, password: password })
      .then(function () { location.href = nextPage(); })
      .catch(function (error) {
        done();
        handleFailure("login", error);
        $("login-password").select();
      });
  });

  // --- Sign up -----------------------------------------------------------------------------

  forms.signup.addEventListener("submit", function (event) {
    event.preventDefault();
    clearErrors("signup");
    var data = {
      first_name: $("signup-first").value.trim(),
      last_name: $("signup-last").value.trim(),
      email: $("signup-email").value.trim(),
      password: $("signup-password").value
    };
    var ok = true;
    if (!data.first_name) { setFieldError("signup", "first_name", "Enter your first name."); ok = false; }
    if (!data.last_name) { setFieldError("signup", "last_name", "Enter your last name."); ok = false; }
    if (!EMAIL_RE.test(data.email)) {
      setFieldError("signup", "email", "Enter a valid email address, like name@example.com."); ok = false;
    }
    if (data.password.length < PASSWORD_MIN) {
      setFieldError("signup", "password", "Use at least " + PASSWORD_MIN + " characters."); ok = false;
    }
    if (!ok) { focusFirstError("signup"); return; }

    var done = setBusy($("signup-submit"), "Creating your account…");
    Account.request("signup.php", data)
      .then(function () { location.href = nextPage(); })
      .catch(function (error) { done(); handleFailure("signup", error); });
  });

  // --- Start ---------------------------------------------------------------------------------

  show(location.hash === "#signup" ? "signup" : "login", false);

  Account.ready.then(function (user) {
    if (user) {
      location.replace(nextPage()); // already logged in
      return;
    }
    if (user === undefined) {
      var notice = $("server-notice");
      notice.textContent = "Accounts only work when the site is opened through Laragon, with " +
        "Apache and MySQL started and database/schema.sql run once. Everything else on the " +
        "site works without an account.";
      notice.hidden = false;
      $("login-submit").disabled = true;
      $("signup-submit").disabled = true;
    }
  });
})();
