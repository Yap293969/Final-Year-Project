// Where the page finds its two servers.
//
// apiBaseUrl: the model server (the web API that runs BERT + XGBoost).
//   ""  -> the same website as this page, e.g. https://your-site.netlify.app/api/...
//   a full address -> a model server hosted somewhere else,
//                     e.g. "https://your-model-server.example.com"
//   This is the only line to change when the model server moves.
//
// accountApiUrl: the accounts API (PHP + MySQL, the api/ folder next to web/).
//   "../api" works when the project folder is served by Laragon, e.g.
//   http://localhost/Final-Year-Project/web/Homepage.html -> .../Final-Year-Project/api/
//   On Netlify there is no PHP, so the account features simply stay hidden.
window.APP_CONFIG = {
  apiBaseUrl: "https://importantly-holder-fed-andrea.trycloudflare.com",
  accountApiUrl: "../api"
};
