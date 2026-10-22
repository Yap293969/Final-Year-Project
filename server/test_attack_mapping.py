# test_attack_mapping.py -- self-test for attack_mapping.py. Needs no model and no BERT.
#
#   cd server
#   python test_attack_mapping.py
#
# It checks the mapping rules against the notebook itself (every feature name must be
# one of the 35 in FEATURE_NAMES, cell 7.1) and against hand-made SHAP answers whose
# right result is known in advance.

import json
import os

import attack_mapping as am

SERVER_FOLDER = os.path.dirname(os.path.abspath(__file__))
NOTEBOOK_PATH = os.path.join(SERVER_FOLDER, "Anti_phishing_prototype.ipynb")

passed = 0
failed = 0


def check(condition, description):
    global passed, failed
    if condition:
        passed += 1
    else:
        failed += 1
        print("FAIL:", description)


def load_cell_71():
    """Run notebook cell 7.1 (plain functions only) and return what it defines."""
    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as handle:
        notebook = json.load(handle)
    for cell in notebook["cells"]:
        source = cell.get("source", "")
        source = "".join(source) if isinstance(source, list) else source
        if cell.get("cell_type") == "code" and source.lstrip().startswith("# Section 7.1 --"):
            namespace = {}
            exec(compile(source, "cell 7.1", "exec"), namespace)
            return namespace
    raise RuntimeError("Cell 7.1 not found in the notebook.")


cell = load_cell_71()
FEATURE_NAMES = cell["FEATURE_NAMES"]
extract = cell["extract_url_features"]

# --- 1. The catalogue and the rules are consistent ------------------------------------
for feature, at_least, ids, clue in am.LINK_RULES:
    check(feature in FEATURE_NAMES, "rule feature %r is in FEATURE_NAMES" % feature)
    for technique_id in ids:
        check(technique_id in am.TECHNIQUES, "rule technique %s is in TECHNIQUES" % technique_id)
for ids in [am.LINK_VERDICT_TECHNIQUES, am.EMAIL_VERDICT_TECHNIQUES]:
    for technique_id in ids:
        check(technique_id in am.TECHNIQUES, "verdict technique %s is in TECHNIQUES" % technique_id)
for words, ids, shows in am.EMAIL_WORD_GROUPS:
    for technique_id in ids:
        check(technique_id in am.TECHNIQUES, "email technique %s is in TECHNIQUES" % technique_id)
    for word in words:
        check(word == am.clean_word(word), "email word %r is already clean" % word)
for technique_id, entry in am.TECHNIQUES.items():
    expected_site = ("https://attack.mitre.org/" if entry["framework"] == "ATT&CK"
                     else "https://capec.mitre.org/")
    check(entry["url"].startswith(expected_site), "%s links to its own catalogue" % technique_id)
    if entry["framework"] == "ATT&CK":
        path = technique_id.replace(".", "/")
        check(entry["url"] == "https://attack.mitre.org/techniques/%s/" % path,
              "%s URL matches its ID" % technique_id)
    else:
        number = technique_id.split("-")[1]
        check(entry["url"].endswith("/definitions/%s.html" % number),
              "%s URL matches its ID" % technique_id)


def reasons(pushes):
    """A hand-made explain_link() answer: {feature: SHAP value}."""
    items = [{"label": "BERT", "detail": "", "value": 0.8, "feature": "bert"}]
    for feature, value in pushes.items():
        items.append({"label": feature, "detail": "", "value": value, "feature": feature})
    return {"reasons": items, "base_value": -0.2, "margin": 2.0}


def ids_of(result, basis=None):
    return [t["id"] for t in result["techniques"] if basis is None or t["basis"] == basis]


# --- 2. Links ------------------------------------------------------------------------
punycode_url = "xn--pypal-4ve.com/login"
features = extract(punycode_url)
check(features["host_has_punycode"] == 1, "the punycode example really has punycode")

result = am.map_link("phishing", reasons({"host_has_punycode": 1.2,
                                          "suspicious_word_count": 0.4}), features)
check(result["applies"], "a phishing link gets techniques")
check(ids_of(result, "shap")[:2] == ["CAPEC-632", "T1598.003"],
      "SHAP matches come first, strongest push first: %s" % ids_of(result, "shap"))
check(set(am.LINK_VERDICT_TECHNIQUES) <= set(ids_of(result)),
      "the general phishing-link techniques are always listed")
check(result["techniques"][0]["push"] == 1.2, "the push is carried with the match")

# Legitimate answer: nothing is named, whatever SHAP says.
result = am.map_link("legitimate", reasons({"host_has_punycode": 1.2}), features)
check(not result["applies"] and result["techniques"] == [], "a legitimate link gets none")

# The clue pushed towards LEGITIMATE: not mapped.
result = am.map_link("phishing", reasons({"host_has_punycode": -0.9}), features)
check("CAPEC-632" not in ids_of(result), "a clue pushing towards legitimate is not mapped")

# The clue pushed towards phishing but is too small.
result = am.map_link("phishing", reasons({"host_has_punycode": 0.05}), features)
check("CAPEC-632" not in ids_of(result), "a push below MIN_LINK_PUSH is not mapped")

# SHAP gives a push to a feature whose value is 0 (punycode absent): not mapped.
plain = extract("example.com/home")
result = am.map_link("phishing", reasons({"host_has_punycode": 1.5}), plain)
check("CAPEC-632" not in ids_of(result),
      "a clue that is not really there is not mapped, even with a big push")

# Two clues pointing to the same technique are merged into one entry.
ip_many = extract("a.b.c.d.192-x--y-.com/")
both = am.map_link("phishing", reasons({"host_subdomain_count": 0.5, "host_hyphen_count": 0.7}), ip_many)
check(ids_of(both, "shap").count("CAPEC-543") == 1, "same technique listed once")
entry = [t for t in both["techniques"] if t["id"] == "CAPEC-543"][0]
check(len(entry["evidence"]) == 2 and entry["push"] == 0.7, "merged entry keeps both clues and the largest push")

# No explanation at all (should not happen): still the general techniques, no crash.
result = am.map_link("phishing", None, plain)
check(ids_of(result) == am.LINK_VERDICT_TECHNIQUES, "no explanation -> general techniques only")

# --- 3. Emails -----------------------------------------------------------------------
email = {"words": ["Dear ", "customer, ", "verify ", "your ", "password ", "now. ",
                   "Click ", "the ", "link ", "immediately."],
         "values": [0.01, -0.2, 0.6, 0.0, 0.5, 0.05, 0.3, 0.0, 0.2, 0.4],
         "margin": 2.1}
result = am.map_email(email)
found = ids_of(result, "shap")
check(found[0] == "T1598", "strongest phishing word ('verify') maps first: %s" % found)
for technique_id in ["T1598", "T1566.002", "T1204.001", "CAPEC-98"]:
    check(technique_id in found, "email maps %s" % technique_id)
check("T1566.001" not in found, "no attachment words -> no attachment technique")
t1598 = [t for t in result["techniques"] if t["id"] == "T1598"][0]
check(len(t1598["evidence"]) == 2, "'verify' and 'password' both recorded for T1598")
check(ids_of(result).count("CAPEC-98") == 1, "CAPEC-98 from SHAP is not repeated as a verdict entry")

# A word that pushed towards LEGITIMATE is never mapped.
email_neg = dict(email, values=[0.01, -0.2, -0.6, 0.0, -0.5, 0.05, -0.3, 0.0, -0.2, -0.4])
check(ids_of(am.map_email(email_neg), "shap") == [], "words pushing towards legitimate are not mapped")

# Legitimate email (margin <= 0): nothing named.
check(not am.map_email(dict(email, margin=-1.0))["applies"], "a legitimate email gets none")
check(not am.map_email(None)["applies"], "no explanation -> not applicable")

print("%d passed, %d failed" % (passed, failed))
raise SystemExit(1 if failed else 0)
