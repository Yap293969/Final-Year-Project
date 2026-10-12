"""Builds web/animations/shield-scan.json, a small hand-made Lottie animation.

A shield outline draws itself, then a scan line sweeps down through it while a
ring pulses outwards. Frames 0-30 are the draw-in; frames 30-120 loop.
"""
import json
import sys

FPS = 60
OP = 120  # total frames (2 s)
W = H = 120

BLUE = [0.431, 0.659, 1.0, 1]      # #6ea8ff
LIGHT = [0.643, 0.784, 1.0, 1]     # #a4c8ff


def static(v):
    return {"a": 0, "k": v}


def ease(n=1):
    return {"x": [0.42] * n, "y": [0] * n}, {"x": [0.58] * n, "y": [1] * n}


def anim(keys):
    """keys: list of (frame, value_list)."""
    out = []
    for idx, (t, v) in enumerate(keys):
        k = {"t": t, "s": v}
        if idx < len(keys) - 1:
            o, i = ease(len(v))
            k["o"], k["i"] = o, i
        out.append(k)
    return {"a": 1, "k": out}


def transform(p=(0, 0), a=(0, 0), s=(100, 100), o=100, r=0):
    return {
        "o": o if isinstance(o, dict) else static(o),
        "r": static(r),
        "p": p if isinstance(p, dict) else static([*p, 0]),
        "a": static([*a, 0]),
        "s": s if isinstance(s, dict) else static([*s, 100]),
    }


def group_tr():
    return {"ty": "tr", "p": static([0, 0]), "a": static([0, 0]), "s": static([100, 100]),
            "r": static(0), "o": static(100), "sk": static(0), "sa": static(0), "nm": "Transform"}


SHIELD = {
    "c": True,
    "v": [[60, 14], [95, 27], [95, 58], [60, 106], [25, 58], [25, 27]],
    "i": [[-14, 0], [-10, -6], [0, 0], [22, -10], [0, 26], [0, 0]],
    "o": [[14, 0], [0, 0], [0, 26], [-22, -10], [0, 0], [10, -6]],
}


def layer(ind, name, shapes, ks=None, extra=None):
    lay = {
        "ddd": 0, "ind": ind, "ty": 4, "nm": name, "sr": 1,
        "ks": ks or transform(), "ao": 0, "shapes": shapes,
        "ip": 0, "op": OP, "st": 0, "bm": 0,
    }
    if extra:
        lay.update(extra)
    return lay


# 1. Shield outline, drawn in with a trim path.
shield_outline = layer(1, "shield-outline", [{
    "ty": "gr", "nm": "outline", "it": [
        {"ty": "sh", "nm": "path", "ks": static(SHIELD)},
        {"ty": "tm", "nm": "trim", "s": static(0),
         "e": anim([(0, [0]), (30, [100])]), "o": static(0), "m": 1},
        {"ty": "st", "nm": "stroke", "c": static(LIGHT), "o": static(100),
         "w": static(4), "lc": 2, "lj": 2, "ml": 4},
        group_tr(),
    ]}])

# 2. Scan line, clipped to the shield with a mask, sweeping down and back.
#    The mask lives in layer space, so the layer stays still and an inner group
#    carries the movement; that keeps the mask fixed on the shield.
scan_line = layer(2, "scan-line", [
    {"ty": "gr", "nm": "glow", "it": [
        {"ty": "rc", "nm": "rect", "p": static([0, -7]), "s": static([80, 14]), "r": static(0)},
        {"ty": "fl", "nm": "fill", "c": static(BLUE), "o": static(22), "r": 1},
        group_tr(),
    ]},
    {"ty": "gr", "nm": "line", "it": [
        {"ty": "rc", "nm": "rect", "p": static([0, 0]), "s": static([80, 3]), "r": static(1.5)},
        {"ty": "fl", "nm": "fill", "c": static(LIGHT), "o": static(100), "r": 1},
        group_tr(),
    ]},
])
moving = {"ty": "gr", "nm": "mover", "it": scan_line["shapes"] + [{
    "ty": "tr", "nm": "Transform",
    "p": anim([(30, [60, 22]), (75, [60, 98]), (120, [60, 22])]),
    "a": static([0, 0]), "s": static([100, 100]), "r": static(0),
    "o": anim([(30, [0]), (38, [100]), (112, [100]), (120, [0])]),
    "sk": static(0), "sa": static(0)}]}
scan_line["shapes"] = [moving]
scan_line["hasMask"] = True
scan_line["masksProperties"] = [{
    "inv": False, "mode": "a", "pt": static(SHIELD), "o": static(100),
    "x": static(0), "nm": "shield-mask"}]

# 3. Soft fill inside the shield, fading in after the draw.
shield_fill = layer(3, "shield-fill", [{
    "ty": "gr", "nm": "fill", "it": [
        {"ty": "sh", "nm": "path", "ks": static(SHIELD)},
        {"ty": "fl", "nm": "fill", "c": static(BLUE), "o": anim([(10, [0]), (30, [14])]), "r": 1},
        group_tr(),
    ]}])

# 4. Pulse ring behind the shield.
ring = layer(4, "pulse-ring", [{
    "ty": "gr", "nm": "ring", "it": [
        {"ty": "el", "nm": "ellipse", "p": static([0, 0]), "s": static([84, 84])},
        {"ty": "st", "nm": "stroke", "c": static(BLUE), "o": static(100),
         "w": static(2), "lc": 2, "lj": 2, "ml": 4},
        group_tr(),
    ]}], ks=transform(
        p=(60, 60),
        s=anim([(30, [80, 80, 100]), (120, [135, 135, 100])]),
        o=anim([(30, [70]), (120, [0])]),
    ))

animation = {
    "v": "5.7.4", "fr": FPS, "ip": 0, "op": OP, "w": W, "h": H,
    "nm": "shield-scan", "ddd": 0, "assets": [],
    "layers": [shield_outline, scan_line, shield_fill, ring],
    "markers": [],
}

with open(sys.argv[1], "w") as fh:
    json.dump(animation, fh, separators=(",", ":"))
print("wrote", sys.argv[1])
