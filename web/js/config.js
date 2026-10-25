// Where the page finds its two servers.
//
// apiBaseUrl: the model server (the web API that runs BERT + XGBoost).
//   It is chosen automatically from where the page is opened:
//   * On your own computer (Laragon: http://localhost/... or http://final-year-project.test/...)
//     the page talks to the model server directly at LOCAL_MODEL_SERVER. No tunnel needed.
//   * Anywhere else (Netlify) it uses TUNNEL_MODEL_SERVER, the trycloudflare.com address
//     printed by "cloudflared tunnel --url http://localhost:8000".
//     Change that line each time cloudflared is restarted (the address changes).
//
// accountApiUrl: the accounts API (PHP + MySQL, the api/ folder next to web/).
//   "../api" works when the project folder is served by Laragon, e.g.
//   http://localhost/Final-Year-Project/web/Homepage.html -> .../Final-Year-Project/api/
//   On Netlify there is no PHP, so the account features simply stay hidden.
(function () {
  var TUNNEL_MODEL_SERVER = "https://cms-being-starring-our.trycloudflare.com";
  var LOCAL_MODEL_SERVER = "http://localhost:8000";

  var host = window.location.hostname;
  var openedLocally = host === "localhost" || host === "127.0.0.1" || /\.test$/.test(host);

  window.APP_CONFIG = {
    apiBaseUrl: openedLocally ? LOCAL_MODEL_SERVER : TUNNEL_MODEL_SERVER,
    accountApiUrl: "../api"
  };
})();
