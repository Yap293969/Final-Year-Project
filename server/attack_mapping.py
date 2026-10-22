# attack_mapping.py -- names the KIND of trick behind a phishing answer, using two public
# MITRE catalogues. Used by app.py; it never changes a verdict or a SHAP value.
#
# WHAT THIS FILE DOES, in plain words
# -----------------------------------
# SHAP (notebook section 12.4) says WHICH clues pushed the model towards "phishing".
# This file looks at those clues and says which well-known attack technique each
# one belongs to, so a reader can connect the model's reason to a recognised name:
#
#   MITRE ATT&CK (version 20)  -- techniques attackers use, e.g. T1566.002
#                                 "Phishing: Spearphishing Link".
#   MITRE CAPEC  (version 3.9) -- attack patterns, e.g. CAPEC-632 "Homograph Attack
#                                 via Homoglyphs" (look-alike characters in a name).
#
# Every ID, name and web address below was checked against attack.mitre.org and
# capec.mitre.org on 2026-10-22.
#
# WHY NOT CVE
# -----------
# A CVE is a flaw in one piece of software. A phishing link or email usually exploits
# a person, not a software flaw, so there is normally no CVE to name. ATT&CK and CAPEC
# describe phishing itself, so the mapping can be stated honestly.
#
# HOW A TECHNIQUE IS CHOSEN (fixed rules, not a model)
# ----------------------------------------------------
# 1. Only when the answer is "phishing". A legitimate answer gets no techniques, so a
#    normal link is never labelled with an attack name.
# 2. From the verdict alone: the general technique that ANY phishing link (or email)
#    belongs to. These are marked basis "verdict".
# 3. From SHAP: a more specific technique, but only when BOTH
#      a. the clue is really there (e.g. the website name really uses punycode), and
#      b. SHAP says that clue pushed the answer towards phishing by at least
#         MIN_LINK_PUSH (links) or was among the strongest phishing words (emails).
#    These are marked basis "shap", and carry the clue as evidence.
#
# The rules and word lists were written from what each technique describes, before
# looking at any result, like SUSPICIOUS_WORDS in notebook section 7.1. They name the
# kind of trick; they do not prove an attack, and the page says so.
#
# STATED LIMITATION
# -----------------
# The 768 BERT numbers ("the overall pattern of the link/email") have no individual
# meaning, so they are never mapped to a technique. Typosquatting (CAPEC-630, e.g.
# "paypa1.com") is also NOT claimed: the model has no brand list (section 7.1 left it
# out on purpose), so nothing it computes can show which brand a name imitates.

ATTACK_VERSION = "MITRE ATT&CK v20"
CAPEC_VERSION = "MITRE CAPEC 3.9"

# One entry per technique: which catalogue, its official name, its official page, and
# a one-sentence meaning written for a young reader.
TECHNIQUES = {
    "T1566": {
        "framework": "ATT&CK", "name": "Phishing",
        "url": "https://attack.mitre.org/techniques/T1566/",
        "meaning": "Sending a message that tricks you into doing something harmful.",
    },
    "T1566.001": {
        "framework": "ATT&CK", "name": "Phishing: Spearphishing Attachment",
        "url": "https://attack.mitre.org/techniques/T1566/001/",
        "meaning": "Sending a message with a harmful file attached.",
    },
    "T1566.002": {
        "framework": "ATT&CK", "name": "Phishing: Spearphishing Link",
        "url": "https://attack.mitre.org/techniques/T1566/002/",
        "meaning": "Sending a message with a link that leads to a harmful or fake page.",
    },
    "T1598": {
        "framework": "ATT&CK", "name": "Phishing for Information",
        "url": "https://attack.mitre.org/techniques/T1598/",
        "meaning": "Tricking you into giving away passwords, card numbers or other "
                   "personal details.",
    },
    "T1598.003": {
        "framework": "ATT&CK", "name": "Phishing for Information: Spearphishing Link",
        "url": "https://attack.mitre.org/techniques/T1598/003/",
        "meaning": "Using a link to a fake page that collects passwords or personal "
                   "details.",
    },
    "T1204.001": {
        "framework": "ATT&CK", "name": "User Execution: Malicious Link",
        "url": "https://attack.mitre.org/techniques/T1204/001/",
        "meaning": "Relying on you to click the link yourself.",
    },
    "T1204.002": {
        "framework": "ATT&CK", "name": "User Execution: Malicious File",
        "url": "https://attack.mitre.org/techniques/T1204/002/",
        "meaning": "Relying on you to open a harmful file yourself.",
    },
    "T1684.001": {
        "framework": "ATT&CK", "name": "Social Engineering: Impersonation",
        "url": "https://attack.mitre.org/techniques/T1684/001/",
        "meaning": "Pretending to be someone you trust, such as a bank, a shop or a "
                   "support team.",
    },
    "CAPEC-98": {
        "framework": "CAPEC", "name": "Phishing",
        "url": "https://capec.mitre.org/data/definitions/98.html",
        "meaning": "Pretending to be a trusted organisation, usually with an urgent "
                   "request, so you hand over information.",
    },
    "CAPEC-543": {
        "framework": "CAPEC", "name": "Counterfeit Websites",
        "url": "https://capec.mitre.org/data/definitions/543.html",
        "meaning": "A fake website made to look like a real one.",
    },
    "CAPEC-632": {
        "framework": "CAPEC", "name": "Homograph Attack via Homoglyphs",
        "url": "https://capec.mitre.org/data/definitions/632.html",
        "meaning": "A website name written with look-alike characters, so it reads "
                   "like a familiar name but is a different address.",
    },
}

# --- Links ---------------------------------------------------------------------------

# The general techniques any phishing link belongs to (basis "verdict").
LINK_VERDICT_TECHNIQUES = ["T1566.002", "T1204.001", "CAPEC-98"]

# The smallest SHAP push (log-odds) that counts. 0.1 on its own moves a 50% answer to
# about 52.5%: small, but clearly more than noise. Below it a clue is not mapped.
MIN_LINK_PUSH = 0.1

# (section 7.1 feature, value it must reach, techniques, the clue in plain words).
# Every feature name must exist in FEATURE_NAMES (notebook 7.1); the self-test in
# test_attack_mapping.py checks that, because a mistyped name would silently never
# match. Thresholds for host_subdomain_count and host_has_punycode / host_is_ip are the
# same as URL_WARNING_RULES in notebook 12.1.
LINK_RULES = [
    ("host_has_punycode", 1, ["CAPEC-632"],
     "The website name uses look-alike (punycode) characters."),
    ("host_is_ip", 1, ["CAPEC-543"],
     "The link goes to a raw IP number instead of a website name."),
    ("host_subdomain_count", 3, ["CAPEC-543"],
     "Extra subdomains push the real website name out of view."),
    ("host_hyphen_count", 2, ["CAPEC-543"],
     "Several hyphens in the website name, a common way to build a fake, "
     "official-looking name."),
    ("suspicious_word_count", 1, ["T1598.003"],
     "Words such as 'login', 'verify' or 'password' suggest a page made to collect "
     "sign-in details."),
]

# --- Emails --------------------------------------------------------------------------

EMAIL_VERDICT_TECHNIQUES = ["T1566", "CAPEC-98"]

# How many of the strongest phishing words are compared with the word groups below.
TOP_EMAIL_WORDS_FOR_MATCHING = 10

# (words, techniques, what the words show). Lower case, whole words only.
EMAIL_WORD_GROUPS = [
    (["password", "passwords", "login", "signin", "verify", "verification", "confirm",
      "credentials", "pin", "otp", "card", "ssn", "identity", "details"],
     ["T1598"], "asks for passwords or personal details"),
    (["click", "link", "visit", "url", "http", "https", "www"],
     ["T1566.002", "T1204.001"], "pushes you to click a link"),
    (["attachment", "attached", "download", "invoice", "document", "pdf", "zip"],
     ["T1566.001", "T1204.002"], "points you to a file"),
    (["bank", "support", "security", "department", "administrator", "admin",
      "official", "helpdesk"],
     ["T1684.001"], "speaks as a trusted organisation"),
    (["urgent", "immediately", "suspended", "locked", "expire", "expires", "expired",
      "final", "warning", "unusual", "closed", "limited"],
     ["CAPEC-98"], "creates urgency or fear"),
]


# --- Helpers -------------------------------------------------------------------------

def technique_entry(technique_id, basis):
    """A copy of one catalogue entry, ready to send to the page."""
    entry = dict(TECHNIQUES[technique_id])
    entry["id"] = technique_id
    entry["basis"] = basis          # "shap" or "verdict"
    entry["evidence"] = []          # the clues (shap) that point to it
    entry["push"] = None            # the largest SHAP push among those clues
    return entry


def add_match(found, technique_id, evidence, push):
    """Record one clue for one technique, merging clues that point to the same one."""
    if technique_id not in found:
        found[technique_id] = technique_entry(technique_id, "shap")
    entry = found[technique_id]
    if evidence not in entry["evidence"]:
        entry["evidence"].append(evidence)
    if entry["push"] is None or push > entry["push"]:
        entry["push"] = round(float(push), 4)


def finish(found, verdict_ids):
    """SHAP matches first (strongest push first), then the general verdict techniques."""
    matched = sorted(found.values(), key=lambda entry: entry["push"], reverse=True)
    general = [technique_entry(technique_id, "verdict") for technique_id in verdict_ids
               if technique_id not in found]
    return matched + general


def not_applicable(reason):
    return {"applies": False, "reason": reason, "techniques": [],
            "catalogues": [ATTACK_VERSION, CAPEC_VERSION]}


def clean_word(word):
    """Lower-case a SHAP word and drop the spaces and punctuation stuck to it."""
    return "".join(character for character in str(word).lower() if character.isalnum())


# --- The two public functions -----------------------------------------------------------

def map_link(verdict, explanation, url_features):
    """Techniques for one checked link.

    verdict      -- "phishing" or "legitimate", from classify() (notebook 12.1)
    explanation  -- the dictionary from explain_link() (notebook 12.4), or None
    url_features -- extract_url_features() (notebook 7.1) for the same prepared link:
                    the real values, so a rule checks the clue is truly there
    """
    if verdict != "phishing":
        return not_applicable("The link was judged legitimate, so no attack technique "
                              "is named.")

    found = {}
    reasons = (explanation or {}).get("reasons", [])
    by_feature = {reason.get("feature"): reason for reason in reasons}

    for feature, at_least, technique_ids, clue in LINK_RULES:
        reason = by_feature.get(feature)
        if reason is None:
            continue
        if float(url_features.get(feature, 0)) < at_least:
            continue
        if reason["value"] < MIN_LINK_PUSH:
            continue
        for technique_id in technique_ids:
            add_match(found, technique_id, clue, reason["value"])

    return {"applies": True, "reason": "",
            "techniques": finish(found, LINK_VERDICT_TECHNIQUES),
            "catalogues": [ATTACK_VERSION, CAPEC_VERSION]}


def map_email(explanation):
    """Techniques for one explained email.

    explanation -- the dictionary from explain_email() (notebook 12.4), or None. Its
                   'margin' is the model's raw score: above 0 means "phishing", the
                   same 50% cut classify() uses.
    """
    if not explanation:
        return not_applicable("There was nothing to explain.")
    if explanation.get("margin", 0.0) <= 0.0:
        return not_applicable("The email was judged legitimate, so no attack technique "
                              "is named.")

    # The strongest words that pushed towards phishing, as SHAP measured them.
    pushes = []
    for word, value in zip(explanation.get("words", []), explanation.get("values", [])):
        cleaned = clean_word(word)
        if cleaned and value > 0:
            pushes.append((float(value), cleaned))
    pushes.sort(reverse=True)
    strongest = pushes[:TOP_EMAIL_WORDS_FOR_MATCHING]

    found = {}
    for words, technique_ids, shows in EMAIL_WORD_GROUPS:
        for value, word in strongest:
            if word in words:
                for technique_id in technique_ids:
                    add_match(found, technique_id,
                              "'%s' %s." % (word, shows), value)

    return {"applies": True, "reason": "",
            "techniques": finish(found, EMAIL_VERDICT_TECHNIQUES),
            "catalogues": [ATTACK_VERSION, CAPEC_VERSION]}
