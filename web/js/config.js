// Where the page finds the model server (the web API that runs BERT + XGBoost).
//
// ""  -> the same website as this page, e.g. https://your-site.netlify.app/api/...
// a full address -> a model server hosted somewhere else,
//                   e.g. "https://your-model-server.example.com"
//
// This is the only line to change when the model server moves.
window.APP_CONFIG = {
  apiBaseUrl: "https://importantly-holder-fed-andrea.trycloudflare.com"
};
