# export_models.py -- save the two trained XGBoost models so the model server can use them.
#
# HOW TO RUN IT
# -------------
# In Anti_phishing_prototype.ipynb, AFTER section 12.3 has finished ("Both predictors
# are built and ready to answer."), add a new cell with this one line and run it:
#
#     %run -i server/export_models.py
#
# The "-i" matters: it runs this file INSIDE the notebook, so it can see PREDICTORS,
# MODEL_NAME and the other things the notebook has already built. Nothing is retrained.
#
# WHAT IT WRITES (into server/models/)
# ------------------------------------
#   email_bert.json        the email XGBoost model (BERT features -> phishing / legitimate)
#   url_bert_lexical.json  the URL XGBoost model   (BERT + 35 lexical features)
#   models_info.json       which model is which, its measured test F1/accuracy, and the
#                          library versions it was trained with
#
# BERT itself is NOT saved here. It is the public, frozen "bert-base-uncased", and
# the server downloads exactly the same model the first time it starts.
#
# THE CHECK AT THE END
# --------------------
# Each saved model is loaded back from disk and asked the same questions as the
# model in memory. If any answer differs, the export is wrong and this cell stops
# with an error, so a broken file can never reach the server unnoticed.

import json
import os

import numpy as np
import torch
import transformers
import xgboost
from xgboost import XGBClassifier

EXPORT_FOLDER = os.path.join("server", "models")
os.makedirs(EXPORT_FOLDER, exist_ok=True)

if "PREDICTORS" not in globals():
    raise RuntimeError("PREDICTORS does not exist. Run the notebook up to the end of "
                       "section 12.3 first, then run: %run -i server/export_models.py")

info = {
    "bert_model_name": MODEL_NAME,
    "pooling": POOLING,
    "trained_with": {
        "xgboost": xgboost.__version__,
        "torch": torch.__version__,
        "transformers": transformers.__version__,
    },
    "models": {},
}

for task in ["email", "url"]:
    predictor = PREDICTORS[task]
    if predictor["kind"] != "bert_xgb":
        raise ValueError("The server only serves the proposed BERT + XGBoost models, "
                         "but the %s predictor is %r." % (task, predictor["kind"]))

    file_name = predictor["name"] + ".json"
    predictor["model"].save_model(os.path.join(EXPORT_FOLDER, file_name))

    info["models"][task] = {
        "name": predictor["name"],
        "file": file_name,
        "representation": predictor["representation"],
        "test_f1": predictor["test_f1"],
        "test_accuracy": predictor["test_accuracy"],
        "best_other_name": predictor["best_other_name"],
        "best_other_f1": predictor["best_other_f1"],
    }
    print("Saved %-18s -> %s" % (predictor["name"], os.path.join(EXPORT_FOLDER, file_name)))

with open(os.path.join(EXPORT_FOLDER, "models_info.json"), "w", encoding="utf-8") as handle:
    json.dump(info, handle, indent=2)
print("Saved models_info.json")

# --- Check: the saved files must answer exactly like the models in memory -----------
CHECK_INPUTS = {
    "email": [prepare_email_input("Your account has been suspended",
                                  "Verify your password within 24 hours."),
              prepare_email_input("Lecture notes", "Slides are in the shared folder.")],
    "url": [prepare_url_input("http://paypa1-secure-login.verify-account.com/signin"),
            prepare_url_input("https://github.com/pandas-dev/pandas")],
}

for task in ["email", "url"]:
    predictor = PREDICTORS[task]
    reloaded = XGBClassifier()
    reloaded.load_model(os.path.join(EXPORT_FOLDER, info["models"][task]["file"]))
    for text in CHECK_INPUTS[task]:
        row = features_for_query(predictor, text)
        in_memory = predictor["model"].predict_proba(row)[0]
        from_file = reloaded.predict_proba(row)[0]
        if not np.allclose(in_memory, from_file, atol=1e-6):
            raise AssertionError("The saved %s model answers differently from the one in "
                                 "memory (%s vs %s)." % (task, in_memory, from_file))
    print("Check passed: the saved %s model answers exactly like the one in memory." % task)

print("")
print("Done. Copy the server/models folder to wherever the model server runs.")
