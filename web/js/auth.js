// Is this a scam? -- accounts, shared by every page.
//
// Logging in is optional: every page works the same without an account. When the
// visitor is logged in, their checks (Checker.html) and games (Game.html) are also
// saved to the MySQL database through the PHP API in api/ (see api/README.md).
//
// What this file does:
// 1. Asks api/me.php whether someone is logged in.
// 2. Adds one link to the site header: "Log in" when nobody is, or the person's
//    first name (to My records, Account.html) when they are.
//    If the accounts API can't be reached (for example on Netlify, which has no PHP),
//    nothing is added and the site behaves exactly as before.
// 3. Gives the other scripts window.Account:
//      Account.ready        a promise of the user ({first_name, ...}), null when
//                           logged out, or undefined when the API isn't there
//      Account.request(path, payload)   a call to the API (GET without payload)
//      Account.saveScan(record)         used by js/checker.js
//      Account.saveGame(record)         used by js/game.js
//      Account.logout()
//      Account.avatarUrl(user)          the person's profile picture, or the default
//                                       one (img/default-avatar.jpg) when they have none
//      Account.uploadAvatar(file)       used by js/account.js
//      Account.removeAvatar()           used by js/account.js
//    saveScan and saveGame do nothing (and never throw) when nobody is logged in.
//
// SAFETY: names are put on screen with textContent, never as HTML.

(function () {
  "use strict";

  var BASE = ((window.APP_CONFIG && window.APP_CONFIG.accountApiUrl) || "../api").replace(/\/+$/, "");
  var TIMEOUT_MS = 8000;

  function AccountError(message, status, fields) {
    this.message = message;
    this.status = status;
    this.fields = fields || {};
  }

  function request(path, payload) {
    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, TIMEOUT_MS);
    var options = {
      method: payload ? "POST" : "GET",
      credentials: "same-origin",
      signal: controller.signal,
      headers: { "Accept": "application/json" }
    };
    if (payload) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(payload);
    }
    return fetch(BASE + "/" + path, options)
      .then(function (response) {
        var type = response.headers.get("Content-Type") || "";
        if (type.indexOf("application/json") === -1) {
          // A web server with no PHP (Netlify, or a plain file server) answers with
          // a page or the PHP source as text: treat that as "no accounts here".
          throw new AccountError("The accounts server isn't available here.", 0);
        }
        return response.json().then(function (data) {
          if (!response.ok || !data.ok) {
            throw new AccountError(data.error || "Something went wrong. Please try again.",
                                   response.status, data.fields);
          }
          return data;
        });
      }, function (error) {
        if (error && error.name === "AbortError") {
          throw new AccountError("The accounts server took too long to answer.", 0);
        }
        throw new AccountError("Couldn't reach the accounts server. Is Laragon running?", 0);
      })
      .finally(function () { clearTimeout(timer); });
  }

  // Uploads (FormData) and DELETE. The X-Requested-With header is checked by
  // api/avatar.php: another website can't add it without asking the server first.
  function send(method, path, formData) {
    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, 30000);
    return fetch(BASE + "/" + path, {
      method: method,
      credentials: "same-origin",
      signal: controller.signal,
      headers: { "Accept": "application/json", "X-Requested-With": "fetch" },
      body: formData || undefined
    })
      .then(function (response) {
        var type = response.headers.get("Content-Type") || "";
        if (type.indexOf("application/json") === -1) {
          throw new AccountError("The accounts server isn't available here.", response.status);
        }
        return response.json().then(function (data) {
          if (!response.ok || !data.ok) {
            throw new AccountError(data.error || "Something went wrong. Please try again.",
                                   response.status);
          }
          return data;
        });
      }, function (error) {
        if (error && error.name === "AbortError") {
          throw new AccountError("The upload took too long. Please try again.", 0);
        }
        throw new AccountError("Couldn't reach the accounts server. Is Laragon running?", 0);
      })
      .finally(function () { clearTimeout(timer); });
  }

  var DEFAULT_AVATAR = "img/default-avatar.jpg";

  function avatarUrl(user) {
    if (user && user.avatar_version) {
      return BASE + "/avatar.php?v=" + encodeURIComponent(user.avatar_version);
    }
    return DEFAULT_AVATAR;
  }

  // An <img> for a profile picture. If the picture can't be loaded it falls back
  // to the default one, so a broken-image icon is never shown.
  function avatarImage(user, className, alt) {
    var img = document.createElement("img");
    img.className = className;
    img.alt = alt || "";
    img.decoding = "async";
    img.addEventListener("error", function () {
      if (img.getAttribute("src") !== DEFAULT_AVATAR) img.src = DEFAULT_AVATAR;
    });
    img.src = avatarUrl(user);
    return img;
  }

  // After a new picture is saved (or removed), show it in the header too.
  function refreshHeaderAvatar(user) {
    current = user;
    var img = document.querySelector(".site-account-avatar");
    if (img) img.src = avatarUrl(user);
  }

  var current; // undefined until known

  var ready = request("me.php")
    .then(function (data) { current = data.user || null; return current; })
    .catch(function () { current = undefined; return undefined; });

  function saveIfLoggedIn(path, record) {
    return ready.then(function (user) {
      if (!user) return null;
      return request(path, record).catch(function (error) {
        if (window.console) console.warn("Not saved to My records:", error.message);
        return null;
      });
    });
  }

  // --- The header link ------------------------------------------------------------

  var ICON_USER =
    '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4"/>' +
    '<path d="M4.5 20.5c1.2-3.6 4.1-5.5 7.5-5.5s6.3 1.9 7.5 5.5"/></svg>';

  function thisPage() {
    var name = location.pathname.split("/").pop() || "Homepage.html";
    return name + location.hash;
  }

  function addHeaderLink(user) {
    var list = document.querySelector(".site-links");
    if (!list || user === undefined || list.querySelector(".site-account")) return;

    var page = location.pathname.split("/").pop();
    var item = document.createElement("li");
    var link = document.createElement("a");
    link.className = "site-account";
    if (user) {
      link.classList.add("has-avatar");
      link.appendChild(avatarImage(user, "site-account-avatar", ""));
    } else {
      link.innerHTML = ICON_USER; // fixed markup written above, never user input
    }
    var label = document.createElement("span");
    label.className = "site-account-label";

    if (user) {
      link.href = "Account.html";
      label.textContent = user.first_name;
      link.setAttribute("aria-label", "My records (" + user.first_name + ")");
      link.title = "My records";
      if (page === "Account.html") link.setAttribute("aria-current", "page");
    } else {
      var next = page === "Login.html" ? "" : "?next=" + encodeURIComponent(thisPage());
      link.href = "Login.html" + next;
      label.textContent = "Log in";
      link.setAttribute("aria-label", "Log in");
      if (page === "Login.html") link.setAttribute("aria-current", "page");
    }
    link.appendChild(label);
    item.appendChild(link);
    list.appendChild(item);
  }

  function onReady(fn) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }

  ready.then(function (user) { onReady(function () { addHeaderLink(user); }); });

  window.Account = {
    ready: ready,
    request: request,
    Error: AccountError,
    user: function () { return current; },
    saveScan: function (record) { return saveIfLoggedIn("scans.php", record); },
    saveGame: function (record) { return saveIfLoggedIn("game-attempts.php", record); },
    logout: function () { return request("logout.php", {}); },
    avatarUrl: avatarUrl,
    avatarImage: avatarImage,
    uploadAvatar: function (file) {
      var form = new FormData();
      form.append("avatar", file);
      return send("POST", "avatar.php", form).then(function (data) {
        refreshHeaderAvatar(data.user);
        return data.user;
      });
    },
    removeAvatar: function () {
      return send("DELETE", "avatar.php").then(function (data) {
        refreshHeaderAvatar(data.user);
        return data.user;
      });
    }
  };
})();
