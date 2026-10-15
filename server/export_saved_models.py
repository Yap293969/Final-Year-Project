# export_saved_models.py -- build server/models/ from the models the notebook already saved.
#
# WHY THIS FILE EXISTS
# --------------------
# app.py needs server/models/ (two XGBoost .json files and models_info.json).
# export_models.py makes that folder, but only from inside the notebook, after
# section 12.3 has retrained both models (a few minutes, and every section's
# settings have to be loaded first).
#
# That retraining is not needed. Section 9.4 already saved the same models to
# models/*.joblib: the same training split, the same XGBoost settings and the same
# seed (42) as sections 11 and 12.3. This script proves it instead of assuming it
# (the check below), then writes exactly the files export_models.py would write.
#
# HOW TO RUN IT (from the project folder, in the same Python the notebook uses)
# ---------------------------------------------------------------------------
#     python server/export_saved_models.py
#
# WHAT IT DOES
# ------------
#   1. Picks the model for each task the same way section 12.3 does: the best
#      measured BERT + XGBoost model in the newest section 11 report
#      ("proposed" policy). That is email_bert and url_bert_lexical.
#   2. Loads models/<name>.joblib and re-measures it on the VALIDATION split.
#      The confusion matrix must equal the one section 11 recorded for that
#      model. If it does not, this is not the model that was measured, and the
#      script stops without writing anything.
#   3. Saves each model as XGBoost JSON in server/models/, loads it back, and
#      checks it answers exactly like the .joblib it came from.
#   4. Writes models_info.json, with the measured TEST scores from section 11.
#
# The test split is not opened here. The test scores are copied from the report.

import ast
import glob
import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
import xgboost
from xgboost import XGBClassifier

SERVER_FOLDER = os.path.dirname(os.path.abspath(__file__))
PROJECT_FOLDER = os.path.dirname(SERVER_FOLDER)
SAVED_MODELS_FOLDER = os.path.join(PROJECT_FOLDER, "models")              # section 9.4
EVALUATION_FOLDER = os.path.join(PROJECT_FOLDER, "reports", "evaluation")  # section 11
TRAINING_FOLDER = os.path.join(PROJECT_FOLDER, "reports", "training")      # section 9
FEATURE_ROOT = os.path.join(PROJECT_FOLDER, "data", "features")
NOTEBOOK_PATH = os.path.join(PROJECT_FOLDER, "Anti_phishing_prototype.ipynb")
EXPORT_FOLDER = os.path.join(SERVER_FOLDER, "models")

PROPOSED_KIND = "bert_xgb"                 # the approved architecture (section 12.1)
LEXICAL_TRACE_COLUMNS = ["url", "label"]   # section 9.1: not features
CHECKED_SCORES = ["true_negative", "false_positive", "false_negative", "true_positive"]


def newest(pattern):
    found = sorted(glob.glob(pattern))
    if not found:
        raise FileNotFoundError("Nothing matches %s. Run that notebook section first." % pattern)
    with open(found[-1], "r", encoding="utf-8") as handle:
        return json.load(handle), os.path.basename(found[-1])


def notebook_settings(names):
    """Read MODEL_NAME and POOLING from cell 8.3 without running it (as app.py does)."""
    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as handle:
        notebook = json.load(handle)
    for cell in notebook["cells"]:
        source = cell.get("source", "")
        source = "".join(source) if isinstance(source, list) else str(source)
        if cell.get("cell_type") == "code" and source.lstrip().startswith("# Section 8.3 --"):
            settings = {}
            for node in ast.parse(source).body:
                if (isinstance(node, ast.Assign) and len(node.targets) == 1
                        and isinstance(node.targets[0], ast.Name)
                        and node.targets[0].id in names):
                    settings[node.targets[0].id] = ast.literal_eval(node.value)
            return settings
    raise ValueError("Cell 8.3 not found in the notebook.")


def validation_features(result, bert_tag):
    """The validation matrix for one model, built as section 11.1 builds it."""
    task = result["task"]
    vectors = np.load(os.path.join(FEATURE_ROOT, task, "bert_%s_validation.npy" % bert_tag))
    labels = np.load(os.path.join(FEATURE_ROOT, task,
                                  "bert_%s_validation_labels.npy" % bert_tag))
    if result.get("feature_columns") == vectors.shape[1]:
        return vectors, labels
    # BERT + lexical: glue the 35 lexical columns on the right, as join_features() does.
    frame = pd.read_csv(os.path.join(FEATURE_ROOT, task, "validation.csv"))
    names = [column for column in frame.columns if column not in LEXICAL_TRACE_COLUMNS]
    lexical = frame[names].to_numpy(dtype=np.float32)
    if not np.array_equal(labels, frame["label"].to_numpy(dtype=int)):
        raise ValueError("BERT and lexical validation rows are out of step for %s." % task)
    return np.hstack([vectors, lexical]).astype(np.float32), labels


def confusion(model, values, labels):
    predictions = model.predict(values)
    return {
        "true_negative": int(np.sum((labels == 0) & (predictions == 0))),
        "false_positive": int(np.sum((labels == 0) & (predictions == 1))),
        "false_negative": int(np.sum((labels == 1) & (predictions == 0))),
        "true_positive": int(np.sum((labels == 1) & (predictions == 1))),
    }


report, report_name = newest(os.path.join(EVALUATION_FOLDER, "final_evaluation_*.json"))
training_report, _ = newest(os.path.join(TRAINING_FOLDER, "training_*.json"))
settings = notebook_settings(["MODEL_NAME", "POOLING"])
print("Model choice taken from: %s (policy: proposed)" % report_name)

info = {
    "bert_model_name": settings["MODEL_NAME"],
    "pooling": settings["POOLING"],
    "trained_with": {"xgboost": training_report.get("xgboost_version", xgboost.__version__)},
    "exported_with": {"xgboost": xgboost.__version__,
                      "script": "server/export_saved_models.py",
                      "evaluation_report": report_name},
    "models": {},
}
to_write = []

for task in ["email", "url"]:
    results = [r for r in report["results"] if r["task"] == task]
    proposed = [r for r in results if r["kind"] == PROPOSED_KIND]
    if not proposed:
        sys.exit("No BERT + XGBoost model was measured for %s in %s." % (task, report_name))
    chosen = max(proposed, key=lambda r: r["test_scores"]["f1"])
    best = max([r for r in results if r["kind"] != "majority"],
               key=lambda r: r["test_scores"]["f1"])

    saved_path = os.path.join(SAVED_MODELS_FOLDER, chosen["name"] + ".joblib")
    if not os.path.exists(saved_path):
        sys.exit("Missing %s. Run notebook section 9.4 to save it." % saved_path)
    model = joblib.load(saved_path)
    if not isinstance(model, XGBClassifier):
        sys.exit("%s is a %s, not an XGBoost model." % (saved_path, type(model).__name__))

    # The check that matters: is this the model section 11 measured?
    values, labels = validation_features(chosen, report["bert_run_tags"][task])
    measured_now = confusion(model, values, labels)
    recorded = {key: chosen["validation_scores"][key] for key in CHECKED_SCORES}
    if measured_now != recorded:
        sys.exit("%s does NOT match section 11 on validation (%s now, %s recorded). "
                 "Nothing was written. Use export_models.py from the notebook instead."
                 % (chosen["name"], measured_now, recorded))
    print("%-6s -> %-18s matches section 11 on all %d validation rows (test F1 %.4f)"
          % (task, chosen["name"], len(labels), chosen["test_scores"]["f1"]))

    other = best if best["name"] != chosen["name"] else None
    info["models"][task] = {
        "name": chosen["name"],
        "file": chosen["name"] + ".json",
        "representation": "bert+lexical" if chosen["feature_columns"] > 768 else "bert",
        "test_f1": chosen["test_scores"]["f1"],
        "test_accuracy": chosen["test_scores"]["accuracy"],
        "best_other_name": other["name"] if other else None,
        "best_other_f1": other["test_scores"]["f1"] if other else None,
    }
    to_write.append((task, model, values[:2000]))

# Only now, with both models proven, is anything written.
os.makedirs(EXPORT_FOLDER, exist_ok=True)
for task, model, sample in to_write:
    path = os.path.join(EXPORT_FOLDER, info["models"][task]["file"])
    model.save_model(path)
    reloaded = XGBClassifier()
    reloaded.load_model(path)
    if not np.allclose(model.predict_proba(sample), reloaded.predict_proba(sample), atol=1e-6):
        sys.exit("The saved %s answers differently from the .joblib it came from." % path)
    print("Saved %s (checked: answers exactly like the .joblib)" % path)

with open(os.path.join(EXPORT_FOLDER, "models_info.json"), "w", encoding="utf-8") as handle:
    json.dump(info, handle, indent=2)
print("Saved %s" % os.path.join(EXPORT_FOLDER, "models_info.json"))
print("")
print("Done. Start the server with:  cd server  then  python app.py")
