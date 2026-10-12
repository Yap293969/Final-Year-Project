===============================================================================
 AI-BASED PHISHING DETECTION SYSTEM USING XGBOOST AND BERT TECHNIQUES FOR YOUTH
 Final Year Project (FYP2) -- "Is this a scam?" prototype
===============================================================================

Read this before the presentation. It explains what the project does, how every
part works, where each file is, how to start the system on the day, and the
answers to questions examiners are likely to ask.

Sections
  1. The project in one minute
  2. The big picture (how the parts talk to each other)
  3. How the model was built (the notebook, step by step)
  4. What happens when a user presses "Check"
  5. Explainable AI: how the "Why" part works (SHAP)
  6. The results, and what they honestly mean
  7. Where everything is (folder map)
  8. Running the system (one-time setup, then presentation day)
  9. Why the model server is not on Netlify or Render
 10. Likely examiner questions, with short answers


-------------------------------------------------------------------------------
1. THE PROJECT IN ONE MINUTE
-------------------------------------------------------------------------------

Problem: young people get phishing emails and links and often can't tell they
are fake.

What I built: a web page where a user pastes a suspicious EMAIL (subject + body)
or a LINK, and the system answers "Looks like phishing" or "Looks legitimate",
with a confidence percentage and the reasons behind the decision.

How it decides: a hybrid AI model.
  * BERT (frozen bert-base-uncased) reads the text and turns it into 768 numbers
    that capture its meaning and context ("feature extraction").
  * XGBoost (a gradient-boosted decision-tree classifier) takes those numbers
    and makes the final phishing / legitimate decision.
  * For links, XGBoost also receives 35 hand-engineered URL features
    (length, hyphens, IP address instead of a name, alarm words, ...).
  * SHAP explains each decision, so the page teaches the user WHAT to look for.

Research objectives (approved):
  1. Analyse phishing email and URL characteristics and existing ML/DL approaches.
  2. Design and develop a hybrid BERT + XGBoost anti-phishing system.
  3. Evaluate it with accuracy, precision, recall and F1-score.

Method: CRISP-DM (data collection -> understanding -> preparation -> BERT
feature extraction -> XGBoost -> training -> prototype -> evaluation).


-------------------------------------------------------------------------------
2. THE BIG PICTURE
-------------------------------------------------------------------------------

There are TWO separate programs. Remember this -- it is the key design point.

  +---------------------------+      JSON over HTTPS     +-----------------------------+
  |  WEB PAGE  (web/)         |  --------------------->  |  MODEL SERVER (server/)     |
  |  HTML, CSS, JavaScript,   |                          |  Python: FastAPI + BERT +   |
  |  Bootstrap 5.3            |  <---------------------  |  XGBoost + SHAP             |
  |  Hosted on NETLIFY        |   verdict + reasons      |  Runs on my laptop (or any  |
  |  (static files only)      |                          |  Python host with ~2 GB RAM)|
  +---------------------------+                          +-----------------------------+

Why two programs? Netlify only hosts static pages (and small JavaScript/Go
functions). It cannot run Python, PyTorch or a 440 MB BERT model. So the page
lives on Netlify and sends what the user typed to the model server, which does
the AI work and sends the answer back.

The ONLY setting that connects them is one line in web/js/config.js:

    window.APP_CONFIG = { apiBaseUrl: "https://<model-server-address>" };

The four requests the page makes (full details in web/README.md):

    GET  /api/health         which models are answering + their test F1 (page footer)
    POST /api/check-email    {"subject": "...", "body": "..."}  -> verdict
    POST /api/explain-email  same input -> word-by-word SHAP explanation (slower)
    POST /api/check-url      {"url": "..."} -> verdict + warning signs + SHAP reasons


-------------------------------------------------------------------------------
3. HOW THE MODEL WAS BUILT  (Anti_phishing_prototype.ipynb)
-------------------------------------------------------------------------------

The notebook is the research record. Its sections follow CRISP-DM:

  1  Environment       Python, torch, transformers, xgboost, scikit-learn; seed 42.
  2  Email data        Kaggle "naserabdullahalam/phishing-email-dataset": six
                       corpora (CEAS_08, Enron, Ling, Nazario, Nigerian_Fraud,
                       SpamAssassin). Label 1 = phishing, 0 = legitimate.
  3  Phishing URLs     PhishTank verified-online feed (snapshot pinned by name).
  4  Legitimate URLs   "benign" rows of Kaggle "sid321axn/malicious-urls-dataset".
  5  Inspection        Every dataset measured, not assumed (rows, labels, overlap).
  6  Preprocessing     Email = subject + body, whitespace cleaned, duplicates and
                       blanks removed (80,643 emails kept). URLs: scheme
                       (http://) and trailing "/" removed so the model can't
                       "cheat" on how each source wrote URLs; duplicates removed;
                       legitimate URLs undersampled to 1:1 (140,490 URLs).
                       Stratified split 70 / 15 / 15 (train / validation / test),
                       seed 42, AFTER de-duplication. Leakage check: 0 shared
                       records between any two splits.
  7  URL features      35 lexical/structural numbers per URL (lengths,
                       punctuation counts, host hyphens/digits/subdomains, IP
                       host, port, punycode, path depth, embedded URL,
                       suspicious-word count).
  8  BERT features     bert-base-uncased, FROZEN (not fine-tuned), mean pooling
                       -> 768 numbers per record. Reads up to 256 tokens of an
                       email and 128 tokens of a URL. Full run: 245 min on CPU.
  9  XGBoost           300 trees, max_depth 6, learning_rate 0.1, subsample 0.8,
                       colsample_bytree 0.8, seed 42. Trained on TRAIN only.
                         email_bert        = 768 BERT features
                         url_bert_lexical  = 768 BERT + 35 lexical (the hybrid)
 10  Baselines         TF-IDF + logistic regression, TF-IDF + Naive Bayes,
                       lexical-only models, majority-class floor -- same splits.
 11  Final evaluation  Every model measured ONCE on the untouched test split.
 12  Prototype         The prediction helpers and SHAP explanations that the
                       model server now reuses.

Dataset sizes after the split:
    Email : 56,450 train / 12,096 validation / 12,097 test (51.44% phishing)
    URL   : 98,344 train / 21,074 validation / 21,072 test (50.00% phishing)


-------------------------------------------------------------------------------
4. WHAT HAPPENS WHEN A USER PRESSES "CHECK"
-------------------------------------------------------------------------------

Checking an EMAIL:
  1. The page sends {"subject", "body"} to /api/check-email.
  2. The server prepares it EXACTLY like the training data: joins subject and
     body, cleans the whitespace (the notebook's own section 6 functions).
  3. BERT reads the first 256 tokens and produces 768 numbers.
  4. XGBoost turns those 768 numbers into a phishing probability.
  5. Probability >= 50% -> "Looks like phishing", else "Looks legitimate".
     Confidence = the probability of the answer given.
  6. "Explain why" (optional button) runs SHAP -- see section 5.

Checking a LINK:
  1. The page sends {"url"} to /api/check-url.
  2. The server removes "http(s)://" and a trailing "/" (same as training).
  3. BERT reads the URL text (128 tokens max) -> 768 numbers.
  4. The 35 lexical features are calculated -> 35 more numbers.
  5. XGBoost receives all 803 numbers -> phishing probability.
  6. The answer comes back WITH:
       * "General warning signs" -- fixed rules of thumb (alarm words, IP
         address, many hyphens, ...). These are teaching tips, NOT the model's
         reasons, and the page labels them that way.
       * "Why the model decided this" -- the model's own reasons (SHAP).

Train/serve skew -- an important point to mention:
  A model can fail silently if the live input is prepared even slightly
  differently from the training data. To prevent that, server/app.py does not
  re-type any preprocessing. It loads and runs the notebook's OWN helper cells
  (6.1, 7.1, 8.1, 12.1, 12.4) and reads the settings from cell 8.3. Example
  proof: "https://paypal.com/login/" and "paypal.com/login" give the identical
  result, because both become the same text before the model sees them.

Safety of the page:
  Everything from the user or the server is shown with textContent, never as
  HTML, so pasting "<script>...</script>" is displayed as text and never runs.
  The server has no logins, cookies or stored data; it only answers questions.


-------------------------------------------------------------------------------
5. EXPLAINABLE AI: HOW THE "WHY" PART WORKS (SHAP)
-------------------------------------------------------------------------------

SHAP (SHapley Additive exPlanations) splits one prediction into "pushes": how
much each input moved the score towards phishing (+) or legitimate (-).

  starting score (base value) + all the pushes = the model's final score

Scores are in LOG-ODDS (XGBoost's raw score), not percentages. The page calls
a push of 1.0 or more "strong", 0.3 or more "moderate", smaller "slight".
Red = towards phishing, green = towards legitimate.

  LINKS  -> TreeSHAP built into XGBoost. EXACT and takes milliseconds, so it
            comes with every link check. The 768 BERT pushes are added together
            into ONE line ("the overall pattern of the link's text, as read by
            BERT") because a single BERT number means nothing to a reader; the
            35 lexical features are shown by name (e.g. "Hyphens in the website
            name: 3").

  EMAILS -> SHAP Partition explainer over WORDS. It hides groups of words
            (replaces them with BERT's [MASK] token), re-scores the email, and
            measures how much the score changed. 100 re-scorings on a CPU, so
            it takes several seconds -- that's why it is a separate "Explain
            why" button. It is an APPROXIMATION; with a limited budget,
            neighbouring words can share credit. Only the part BERT actually
            read (256 tokens) is explained.

Honest limit: SHAP shows what the model paid attention to, not proof that the
model is right. The page says this under every explanation.


-------------------------------------------------------------------------------
6. THE RESULTS, AND WHAT THEY HONESTLY MEAN  (test split, measured once)
-------------------------------------------------------------------------------

Email (12,097 test emails)               Accuracy  Precision  Recall    F1
  email_bert  (PROPOSED, BERT+XGBoost)    0.9842    0.9850    0.9842  0.9846
  email_tfidf_logreg (baseline)           0.9864    0.9845    0.9891  0.9868
  email_tfidf_nb     (baseline)           0.9743    0.9862    0.9635  0.9747
  email_majority     (floor)              0.5143    0.5143    1.0000  0.6793

URL (21,072 test URLs)                   Accuracy  Precision  Recall    F1
  url_bert_lexical (PROPOSED hybrid)      0.9642    0.9669    0.9614  0.9641
  url_bert         (BERT only)            0.9588    0.9621    0.9552  0.9587
  url_lexical      (35 features only)     0.9366    0.9361    0.9371  0.9366
  url_tfidf_logreg (baseline)             0.9682    0.9802    0.9557  0.9678
  url_majority     (floor)                0.5000    0.0000    0.0000  0.0000

What I can claim:
  * The proposed system works well: F1 0.9846 (email) and 0.9641 (URL).
  * Objective 2 result: the HYBRID beats each of its own parts on URLs --
    BERT + lexical 0.9641 > BERT only 0.9587 > lexical only 0.9366.
  * Validation and test scores agree closely, so the splits are clean.

What I do NOT claim:
  * That BERT + XGBoost beats the classical baselines. TF-IDF + logistic
    regression was narrowly ahead (by 0.0022 on email, 0.0037 on URL).
    The footer of the web page states this openly.

Measured reasons (not guesses) for that gap:
  * BERT reads only the first 256 tokens of an email; TF-IDF reads the whole email.
  * BERT is frozen, so it never adapts to phishing; character n-grams are very
    strong on URL-shaped text.
  * The BERT models overfit (train F1 about 1.000 vs validation 0.985). They
    were NOT tuned after seeing the test set, because that would make every
    test number invalid.

Why the prototype serves the proposed model and not the top baseline:
  It exists to demonstrate THIS project's system (BERT + XGBoost). Serving
  TF-IDF would mean the prototype contains no BERT and no XGBoost at all. The
  choice is a documented setting (MODEL_SELECTION_POLICY = "proposed", notebook
  12.3) and the comparison is shown on screen, so nothing is hidden.


-------------------------------------------------------------------------------
7. WHERE EVERYTHING IS
-------------------------------------------------------------------------------

  Anti_phishing_prototype.ipynb  the whole research pipeline (sections 1-12)
  CLAUDE.md                      project rules (objectives, methodology)
  docs/FYP_Specification.md      what the system is meant to be
  docs/PROJECT_STATE.md          detailed progress record, results, decisions
  docs/DATASET_SOURCES.md        where every dataset came from
  reports/                       JSON records of every run (features, training,
                                 baselines, final evaluation, prototype)
  data/metadata/                 provenance (size, SHA-256) of raw downloads
  scripts/                       dataset download helpers, Lottie animation maker
  src/data/phishtank.py          PhishTank acquisition module
  netlify.toml                   tells Netlify to publish the web/ folder as-is

  web/                           THE WEB PAGE (hosted on Netlify)
    index.html                   landing page (what it does, test F1 figures)
    check.html                   the checker: Email tab and Link tab
    js/app.js                    sends input to the model server, shows answers
    js/config.js                 apiBaseUrl = where the model server is
    js/theme.js, css/*.css       look and the Default / Dark / Light themes
    README.md                    exact request/response formats

  server/                        THE MODEL SERVER (Python)
    app.py                       FastAPI web API: loads BERT + the two XGBoost
                                 models, reuses the notebook helper cells,
                                 answers the 4 requests
    export_models.py             run once inside the notebook to save the two
                                 trained XGBoost models
    requirements.txt             Python packages, same versions as the notebook
    models/                      (created by export_models.py, not in git)
      email_bert.json, url_bert_lexical.json, models_info.json

  Files not in git (too big, re-creatable): data/raw, data/processed,
  data/features, models/, server/models/. Credentials (kaggle.json, .env) are
  git-ignored and must never be committed.


-------------------------------------------------------------------------------
8. RUNNING THE SYSTEM
-------------------------------------------------------------------------------

A) ONE-TIME: export the trained models from the notebook
   1. Open Anti_phishing_prototype.ipynb in the runtime that has the data
      (data/processed and data/features must exist there).
   2. Run the notebook from the top down to the end of section 12.3 (the order
      is also in docs/PROJECT_STATE.md, "Next Task"). The BERT extraction in
      8.4 re-uses the feature shards already on disk, so it does not redo the
      4-hour run. Wait for 12.3 to print
      "Both predictors are built and ready to answer."
   3. Add a new cell at the end and run:
          %run -i server/export_models.py
      It saves server/models/ and checks that the saved models give exactly the
      same answers as the ones in memory. It must end with "Done.".
   4. If you ran this in Colab, download the server/models folder into
      C:\laragon\www\Final-Year-Project\server\models on the laptop.

B) ONE-TIME: install the server's packages on the laptop
   In a terminal (Command Prompt / PowerShell):
          cd C:\laragon\www\Final-Year-Project\server
          pip install -r requirements.txt
   (If the notebook already runs on this laptop, torch/transformers/xgboost are
   already there; this mainly adds fastapi, uvicorn and shap.)

C) Start the model server
          cd C:\laragon\www\Final-Year-Project\server
          python app.py
   The FIRST start downloads bert-base-uncased (about 440 MB) from Hugging
   Face; later starts use the saved copy. Wait for:
          Model server ready: http://localhost:8000/api/health
   Open that address in a browser -- you should see "status": "ok" and both
   model names. Leave this window open; closing it stops the server.

D) Give the server a public HTTPS address (free, no account, no credit card)
   The Netlify page is on the internet, so it needs a public address for the
   server. Cloudflare's free "quick tunnel" provides one.
   One-time install (either way):
          winget install --id Cloudflare.cloudflared
     or download the Windows installer from Cloudflare's "cloudflared
     downloads" page.
   Then, in a SECOND terminal (server still running in the first):
          cloudflared tunnel --url http://localhost:8000
   It prints an address like  https://four-random-words.trycloudflare.com
   Test it: open  https://<that-address>/api/health  in a browser.

E) Point the Netlify page at the server
   1. Edit web/js/config.js:
          window.APP_CONFIG = { apiBaseUrl: "https://four-random-words.trycloudflare.com" };
      (no "/" at the end)
   2. Commit and push with GitHub Desktop. Netlify re-deploys automatically
      in under a minute.
   3. Open the Netlify site -> check.html. The footer should list email_bert
      and url_bert_lexical. If it says "The model server isn't connected",
      re-check steps C-E.

   Quick local test without the tunnel: leave apiBaseUrl as
   "http://localhost:8000" and open the page from the same laptop (Laragon or
   "python -m http.server" inside web/).

PRESENTATION-DAY CHECKLIST
   [ ] Laptop plugged in; sleep/hibernate turned off.
   [ ] Terminal 1:  python app.py         (wait for "Model server ready")
   [ ] Terminal 2:  cloudflared tunnel --url http://localhost:8000
   [ ] The tunnel address changes EVERY time -> update web/js/config.js,
       push, wait for Netlify to finish deploying.
   [ ] Open the Netlify check.html: footer shows the two models.
   [ ] Run each example button once (warms BERT up; the first answer is slower).
   [ ] Try "Explain why" on the scam email example once (about 10-30 s on CPU).
   [ ] Keep both terminals open until the presentation is over.

TROUBLESHOOTING
   "No trained models in ...server\models"  -> do step A.
   "Can't find the notebook"                -> app.py must stay in the
                                               project's server\ folder.
   Page says server isn't connected          -> server window closed, tunnel
                                               closed, or config.js still has
                                               an old tunnel address.
   "took too long to answer"                -> the server answers one request
                                               at a time; an email explanation
                                               blocks others for a few seconds.
   Error status 422                          -> the input was empty or too long.


-------------------------------------------------------------------------------
9. WHY THE MODEL SERVER IS NOT ON NETLIFY OR RENDER
-------------------------------------------------------------------------------

  * Netlify Functions run JavaScript/TypeScript/Go, with 1024 MB memory and a
    60-second limit -- no Python, no PyTorch. Netlify hosts the PAGE only.
  * Render's free plan gives 512 MB RAM. Measured: PyTorch + libraries take
    hundreds of MB before BERT, and loading bert-base-uncased adds about
    570 MB more, so the server needs well over 1 GB. It does not fit.
  * Hosts with enough free RAM (Google Cloud Run, Modal) require a credit
    card. Hugging Face now charges for Docker/Gradio Spaces except a limited
    ZeroGPU option.
  * So, for a student prototype with no budget: the page is on Netlify, and
    the model server runs on my laptop and is reached through a free
    Cloudflare tunnel. server/app.py is ordinary FastAPI, so the same file
    could be moved to any paid Python host later without changes.


-------------------------------------------------------------------------------
10. LIKELY EXAMINER QUESTIONS
-------------------------------------------------------------------------------

Q: Why BERT AND XGBoost, not just one?
A: BERT understands context and wording; XGBoost is a strong, fast classifier
   on numeric features and can also use the 35 engineered URL features. The
   test results show the combination beats each part alone on URLs.

Q: Did you fine-tune BERT?
A: No. It is frozen and used only as a feature extractor, as the approved
   methodology states. Fine-tuning is the main future-work item.

Q: Your baseline scored higher. Isn't the project a failure?
A: No. The system reaches F1 0.98/0.96. The baseline's lead is small (0.2-0.4
   percentage points), and I report it honestly instead of tuning on the test
   set. The objective-2 finding -- the hybrid beats its parts -- holds.

Q: How do you know there is no data leakage?
A: Duplicates were removed BEFORE splitting; every pair of splits was checked
   for shared records (0 found); vectorisers/scalers were fitted on train only;
   the test split was used once, at the end.

Q: Why remove "http://" from URLs?
A: The phishing and legitimate URLs came from different sources that wrote
   schemes differently. Keeping it would let the model learn the SOURCE instead
   of phishing, so it was removed from both -- and the server removes it too.

Q: How does the website get its answer?
A: The Netlify page sends the text as JSON to the FastAPI model server, which
   runs the same preprocessing, BERT, XGBoost and SHAP code as the notebook,
   and returns the verdict and reasons as JSON (section 2 and 4).

Q: What does the confidence percentage mean?
A: XGBoost's probability for the answer it gave (e.g. 97% phishing). It is
   the model's certainty, not a guarantee.

Q: Are the "General warning signs" the model's reasons?
A: No -- they are fixed teaching rules, labelled as such. The model's reasons
   are the SHAP section. They can disagree (e.g. in this data phishing URLs
   were on average SHORTER than legitimate ones).

Q: Is user data stored?
A: No. The server keeps nothing; it answers and forgets.

Q: Limitations / future work?
A: Fine-tune BERT; let BERT read longer emails; reduce overfitting
   (regularisation); larger and newer datasets; always-on cloud hosting.
