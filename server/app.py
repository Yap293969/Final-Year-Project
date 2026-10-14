# app.py -- the model server for "Is this a scam?" (FYP2: BERT + XGBoost phishing detection).
#
# WHAT THIS FILE DOES, in plain words
# -----------------------------------
# The web page on Netlify (web/) cannot run Python, so it sends what the user pasted
# to this small web API. This file:
#   1. loads frozen bert-base-uncased (the feature extractor) once, at start-up,
#   2. loads the two trained XGBoost models exported from the notebook
#      (server/models/, written by server/export_models.py),
#   3. answers the four requests listed in web/README.md, as JSON.
#
# WHY IT READS CODE FROM THE NOTEBOOK
# -----------------------------------
# The biggest risk when a model goes behind a web form is TRAIN / SERVE SKEW: the
# server prepares text slightly differently from how the training data was prepared,
# and the model quietly gives wrong answers. To rule that out, this server does not
# re-type any preprocessing. It runs the notebook's OWN helper cells:
#
#   6.1  clean_text, join_subject_and_body, normalise_url    (preprocessing)
#   7.1  extract_url_features, FEATURE_NAMES                 (the 35 lexical features)
#   8.1  embed_texts, load_bert                              (BERT feature extraction)
#   12.1 prepare_*_input, features_for_query, classify, url_warning_signs
#   12.4 explain_link, explain_email                         (SHAP explanations)
#
# and the settings MODEL_NAME, POOLING and TASK_SETTINGS from cell 8.3. So a URL or
# email typed into the page goes through exactly the same code as the training rows.
#
# HOW TO RUN IT
# -------------
#   cd server
#   pip install -r requirements.txt
#   python app.py
# Then open http://localhost:8000/api/health  -- see README.txt for the full steps.

import ast
import json
import os
import threading
import time

import numpy as np
import torch
import xgboost
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from xgboost import XGBClassifier

SERVER_FOLDER = os.path.dirname(os.path.abspath(__file__))
PROJECT_FOLDER = os.path.dirname(SERVER_FOLDER)
NOTEBOOK_PATH = os.environ.get(
    "NOTEBOOK_PATH", os.path.join(PROJECT_FOLDER, "C:/git_project/www/Final-Year-Project/Anti_phishing_prototype.ipynb"))
MODELS_FOLDER = os.environ.get("MODELS_FOLDER", os.path.join(SERVER_FOLDER, "models"))
PORT = int(os.environ.get("PORT", "8000"))

# The server always runs BERT on the CPU. It answers one request at a time, which is
# plenty for a demonstration, and a CPU is what free hosting and a laptop offer.
DEVICE = "cpu"
BATCH_SIZE = 32          # the notebook's CPU batch size (section 8.3)

# Longest input accepted. BERT only reads 256 tokens of an email and 128 of a URL
# anyway; these limits just stop someone pasting a whole book into the form.
MAX_EMAIL_CHARACTERS = 20000
MAX_URL_CHARACTERS = 2000

# The notebook cells this server runs, found by their first line rather than by
# position, so adding a cell elsewhere in the notebook cannot break the server.
HELPER_CELLS = [
    "# Section 6.1 --",    # preprocessing helpers
    "# Section 7.1 --",    # URL lexical feature helpers
    "# Section 8.1 --",    # BERT extraction helpers
    "# Section 12.1 --",   # prototype helpers
    "# Section 12.4 --",   # SHAP explanation helpers
]
SETTINGS_CELL = "# Section 8.3 --"
SETTINGS_FROM_NOTEBOOK = ["MODEL_NAME", "POOLING", "TASK_SETTINGS"]


# --- Step 1: read the helper code and settings out of the notebook -------------------

def read_notebook_cells(path):
    """Return the source of every code cell in the notebook, as a list of strings."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            "Can't find the notebook at %s. The server reuses its helper code, so keep "
            "app.py inside the project's server/ folder (or set NOTEBOOK_PATH)." % path)
    with open(path, "r", encoding="utf-8") as handle:
        notebook = json.load(handle)

    cells = notebook.get("cells", [])
    sources = []
    for cell in cells:
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", "")
        if source is None:
            source = ""
        elif isinstance(source, list):
            source = "".join(source)
        sources.append(str(source))
    return sources


def find_cell(cells, first_line):
    """Return the one code cell that starts with first_line."""
    matches = [source for source in cells if source.lstrip().startswith(first_line)]
    if len(matches) != 1:
        raise ValueError("Expected exactly one notebook cell starting with %r, found %d."
                        % (first_line, len(matches)))
    return matches[0]


def read_settings(cell_source, names):
    """Read simple settings such as TASK_SETTINGS = {...} from a cell, WITHOUT running it.

    Cell 8.3 also checks that the training data is on disk and loads BERT, neither of
    which the server wants, so only the plain assignments listed in `names` are taken.
    """
    settings = {}
    try:
        parsed = ast.parse(cell_source)
    except SyntaxError as exc:
        raise ValueError("The notebook settings cell could not be parsed: %s" % exc) from exc

    for node in parsed.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in names:
                try:
                    settings[target.id] = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    continue
    missing = [name for name in names if name not in settings]
    if missing:
        raise ValueError("Cell 8.3 no longer sets %s." % ", ".join(missing))
    return settings


def load_notebook_helpers(path):
    """Run the notebook's helper cells and return everything they define."""
    cells = read_notebook_cells(path)

    # The same names the notebook's own imports cell (1.3) provides.
    namespace = {"__name__": "notebook_helpers", "os": os, "json": json, "time": time,
                "np": np, "torch": torch, "xgboost": xgboost}

    # 6.1, 7.1 and 8.1 only define functions, so they are run first, in notebook order.
    for first_line in HELPER_CELLS[:3]:
        exec(compile(find_cell(cells, first_line), first_line, "exec"), namespace)

    # The settings 12.1 and 12.4 rely on, then frozen BERT itself.
    namespace.update(read_settings(find_cell(cells, SETTINGS_CELL), SETTINGS_FROM_NOTEBOOK))
    namespace["DEVICE"] = DEVICE
    namespace["BATCH_SIZE"] = BATCH_SIZE
    print("Loading %s (first start downloads about 440 MB) ..." % namespace["MODEL_NAME"])
    started = time.perf_counter()
    namespace["TOKENIZER"], namespace["MODEL"] = namespace["load_bert"](
        namespace["MODEL_NAME"], DEVICE)
    print("  BERT ready in %.1fs" % (time.perf_counter() - started))

    for first_line in HELPER_CELLS[3:]:
        exec(compile(find_cell(cells, first_line), first_line, "exec"), namespace)
    return namespace


# --- Step 2: load the two trained XGBoost models --------------------------------------

def load_predictors(models_folder):
    """Rebuild the PREDICTORS dictionary that notebook section 12.3 builds."""
    info_path = os.path.join(models_folder, "models_info.json")
    if not os.path.exists(info_path):
        raise FileNotFoundError(
            "No trained models in %s. In the notebook, after section 12.3, run "
            "'%%run -i server/export_models.py', then copy server/models here."
            % models_folder)
    with open(info_path, "r", encoding="utf-8") as handle:
        info = json.load(handle)

    trained_with = info.get("trained_with", {}).get("xgboost")
    if trained_with and trained_with != xgboost.__version__:
        print("NOTE: the models were trained with xgboost %s; this server has %s."
              % (trained_with, xgboost.__version__))

    predictors = {}
    for task in ["email", "url"]:
        entry = info["models"][task]
        model = XGBClassifier()
        model.load_model(os.path.join(models_folder, entry["file"]))
        predictors[task] = {
            "name": entry["name"], "task": task, "kind": "bert_xgb", "model": model,
            "representation": entry["representation"],
            "test_f1": entry["test_f1"], "test_accuracy": entry["test_accuracy"],
            "best_other_name": entry["best_other_name"],
            "best_other_f1": entry["best_other_f1"],
        }
        print("  %-5s -> %s (test F1 %.4f)" % (task, entry["name"], entry["test_f1"]))
    return info, predictors


print("Starting the model server ...")
NB = load_notebook_helpers(NOTEBOOK_PATH)
MODELS_INFO, PREDICTORS = load_predictors(MODELS_FOLDER)

if NB["MODEL_NAME"] != MODELS_INFO.get("bert_model_name", NB["MODEL_NAME"]):
    raise ValueError("The models were trained on %s features but the notebook now says %s."
                     % (MODELS_INFO["bert_model_name"], NB["MODEL_NAME"]))

# BERT and SHAP are not built for many requests at once. A lock makes the server
# answer one request at a time; others simply wait their turn.
MODEL_LOCK = threading.Lock()


# --- Step 3: the web API ---------------------------------------------------------------

app = FastAPI(title="Is this a scam? -- model server",
              description="BERT + XGBoost phishing detection for the FYP2 prototype.")

# CORS lets the Netlify page (a different web address) call this server. The API has
# no logins, cookies or secrets, so allowing any page to call it is safe. To lock it to
# your site only, set ALLOWED_ORIGINS, e.g. "https://your-site.netlify.app".
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class EmailRequest(BaseModel):
    subject: str = Field("", max_length=MAX_EMAIL_CHARACTERS)
    body: str = Field("", max_length=MAX_EMAIL_CHARACTERS)


class UrlRequest(BaseModel):
    url: str = Field(..., max_length=MAX_URL_CHARACTERS)


def prepared_email(request):
    text = NB["prepare_email_input"](request.subject, request.body)
    if text == "":
        raise HTTPException(status_code=422, detail="The email is empty.")
    return text


@app.get("/")
def home():
    return {"message": "The model server is running. The web page uses /api/health, "
                       "/api/check-email, /api/explain-email and /api/check-url."}


@app.get("/api/health")
def health():
    """Which models answer, and their measured test scores (shown in the page footer)."""
    models = {}
    for task, predictor in PREDICTORS.items():
        models[task] = {key: predictor[key] for key in
                        ["name", "test_f1", "test_accuracy", "best_other_name",
                         "best_other_f1"]}
    return {"status": "ok", "models": models}


@app.post("/api/check-email")
def check_email(request: EmailRequest):
    """Verdict for an email: classify() from notebook 12.1."""
    text = prepared_email(request)
    with MODEL_LOCK:
        return NB["classify"](PREDICTORS["email"], text)


@app.post("/api/explain-email")
def explain_email(request: EmailRequest):
    """Word-by-word SHAP explanation: explain_email() from 12.4. Takes several seconds."""
    text = prepared_email(request)
    with MODEL_LOCK:
        return NB["explain_email"](PREDICTORS["email"], text)


@app.post("/api/check-url")
def check_url(request: UrlRequest):
    """Verdict for a link, its general warning signs, and its exact TreeSHAP reasons."""
    text = NB["prepare_url_input"](request.url)
    if text == "":
        raise HTTPException(status_code=422, detail="The link is empty.")
    with MODEL_LOCK:
        answer = NB["classify"](PREDICTORS["url"], text)
        answer["warning_signs"] = NB["url_warning_signs"](text)
        answer["explanation"] = NB["explain_link"](PREDICTORS["url"], text)
    return answer


if __name__ == "__main__":
    import uvicorn
    print("Model server ready: http://localhost:%d/api/health" % PORT)
    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=PORT)
