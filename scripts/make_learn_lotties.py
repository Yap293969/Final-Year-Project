"""Builds the Lottie (JSON) animations for web/Learn.html.

Same hand-made approach as make_shield_lottie.py: every shape is written out
here, so the animations need no design tool and can be rebuilt at any time.

    python scripts/make_learn_lotties.py web/animations

writes seven files, one per part of the page:

    learn-phone.json      hero: messages pop up on a phone, the last one is a scam
    learn-hook.json       01 What is phishing: an email on a fishing hook
    learn-alarm.json      02 Why it works: a shaking alarm clock, time running out
    learn-magnifier.json  03 Red flags: a magnifier finds the warning signs
    learn-link.json       04 Read the link: the real owner of a web address
    learn-gift.json       05 Common baits: a "free gift" with a hook inside
    learn-shield.json     06 What to do: a shield draws itself and ticks

All are 160 x 160 at 30 fps and loop. learn-shield.json draws itself in frames
0-48, then loops 48-120 (js/learn.js reads that from data-loop-from in the HTML).
"""
import json
import os
import sys

FPS = 30
W = H = 160

# Colours, matching css/theme.css (Default theme). In the Light theme the page
# darkens the animations with a CSS filter, as the homepage does for its shield.
BLUE = [0.494, 0.651, 1.0, 1]     # #7ea6ff  accent
LIGHT = [0.780, 0.847, 1.0, 1]    # #c7d8ff  outlines
RED = [1.0, 0.302, 0.369, 1]      # #ff4d5e  towards phishing
AMBER = [1.0, 0.580, 0.251, 1]    # #ff9440  warning sign
GREEN = [0.204, 0.827, 0.600, 1]  # #34d399  safe


# --- Small helpers ---------------------------------------------------------------

def static(v):
    return {"a": 0, "k": v}


EASES = {
    "io": ([0.42], [0.0], [0.58], [1.0]),    # ease in-out
    "out": ([0.2], [0.6], [0.3], [1.0]),     # fast start, soft stop
    "pop": ([0.3], [0.0], [0.35], [1.45]),   # overshoots a little, for popping in
    "lin": ([0.0], [0.0], [1.0], [1.0]),
}


def anim(keys, ease="io"):
    """keys: list of (frame, value). A value may be a number or a list."""
    out = []
    for n, (t, v) in enumerate(keys):
        v = v if isinstance(v, list) else [v]
        k = {"t": t, "s": v}
        if n < len(keys) - 1:
            ox, oy, ix, iy = EASES[ease]
            k["o"] = {"x": ox * len(v), "y": oy * len(v)}
            k["i"] = {"x": ix * len(v), "y": iy * len(v)}
        out.append(k)
    return {"a": 1, "k": out}


def val(v, dims):
    """A static value, or an animation passed through unchanged."""
    if isinstance(v, dict):
        return v
    if dims == 1:
        return static(v)
    return static(list(v))


def tr(p=(0, 0), a=(0, 0), s=(100, 100), r=0, o=100):
    return {"ty": "tr", "nm": "Transform", "p": val(p, 2), "a": val(a, 2),
            "s": val(s, 2), "r": val(r, 1), "o": val(o, 1),
            "sk": static(0), "sa": static(0)}


def grp(name, items, **t):
    return {"ty": "gr", "nm": name, "it": items + [tr(**t)]}


def rect(w, h, r=0, p=(0, 0)):
    return {"ty": "rc", "nm": "rect", "p": static(list(p)), "s": static([w, h]), "r": static(r)}


def ell(w, h=None, p=(0, 0)):
    return {"ty": "el", "nm": "ellipse", "p": static(list(p)), "s": static([w, h or w])}


def path_data(v, i=None, o=None, closed=False):
    z = [[0, 0]] * len(v)
    return {"c": closed, "v": [list(x) for x in v],
            "i": [list(x) for x in (i or z)], "o": [list(x) for x in (o or z)]}


def path(v, i=None, o=None, closed=False):
    return {"ty": "sh", "nm": "path", "ks": static(path_data(v, i, o, closed))}


def stroke(c, w, o=100):
    return {"ty": "st", "nm": "stroke", "c": val(c, 4) if isinstance(c, dict) else static(c),
            "o": val(o, 1), "w": static(w), "lc": 2, "lj": 2, "ml": 4}


def fill(c, o=100):
    return {"ty": "fl", "nm": "fill", "c": c if isinstance(c, dict) else static(c),
            "o": val(o, 1), "r": 1}


def trim(e, s=0):
    return {"ty": "tm", "nm": "trim", "s": val(s, 1), "e": val(e, 1), "o": static(0), "m": 1}


def layer(ind, name, shapes, op, mask=None):
    lay = {"ddd": 0, "ind": ind, "ty": 4, "nm": name, "sr": 1,
           "ks": {"o": static(100), "r": static(0), "p": static([0, 0, 0]),
                  "a": static([0, 0, 0]), "s": static([100, 100, 100])},
           "ao": 0, "shapes": shapes, "ip": 0, "op": op, "st": 0, "bm": 0}
    if mask:
        lay["hasMask"] = True
        lay["masksProperties"] = [{"inv": False, "mode": "a", "pt": static(mask),
                                   "o": static(100), "x": static(0), "nm": "mask"}]
    return lay


def build(name, op, groups, masks=None):
    """groups: list of shape groups, drawn top first, one layer each."""
    masks = masks or {}
    layers = [layer(n + 1, g["nm"], [g], op, masks.get(g["nm"])) for n, g in enumerate(groups)]
    return {"v": "5.7.4", "fr": FPS, "ip": 0, "op": op, "w": W, "h": H, "nm": name,
            "ddd": 0, "assets": [], "layers": layers, "markers": []}


def pop_in(t, end_fade, start_fade=None):
    """Scale and opacity keys: pops in at frame t, fades out before end_fade."""
    start_fade = start_fade or end_fade - 14
    s = anim([(0, [0, 0]), (t, [0, 0]), (t + 10, [100, 100]),
              (start_fade, [100, 100]), (end_fade, [92, 92])], "pop")
    o = anim([(0, 0), (t, 0), (t + 5, 100), (start_fade, 100), (end_fade, 0)])
    return s, o


# --- Hero: a phone, messages arriving, the last one is a scam ---------------------

def phone():
    op = 150
    groups = []
    rows = [(46, BLUE, 12), (74, BLUE, 42), (102, RED, 72)]
    for n, (y, colour, t) in enumerate(rows):
        s, o = pop_in(t, 146, 132)
        items = [
            grp("bubble", [rect(60, 21, 8), fill(colour, 20), stroke(colour, 1.5)]),
            grp("dot", [ell(7, p=(-20, 0)), fill(colour)]),
            grp("line1", [rect(28, 3, 1.5, p=(3, -4)), fill(colour, 75)]),
            grp("line2", [rect(20, 3, 1.5, p=(-1, 4)), fill(colour, 55)]),
        ]
        groups.append(grp("message-%d" % (n + 1), items, p=(80, y), s=s, o=o))
    # Warning ring around the scam message, pulsing twice.
    ring_s = anim([(0, [100, 100]), (84, [100, 100]), (106, [118, 128]),
                   (107, [100, 100]), (130, [118, 128])], "out")
    ring_o = anim([(0, 0), (84, 0), (86, 90), (106, 0), (108, 90), (130, 0)], "lin")
    groups.insert(0, grp("scam-ring", [rect(62, 23, 9), stroke(RED, 2)],
                         p=(80, 102), s=ring_s, o=ring_o))
    groups.append(grp("notch", [rect(22, 4, 2, p=(80, 21)), fill(LIGHT, 60)]))
    groups.append(grp("home-bar", [rect(26, 3, 1.5, p=(80, 139)), fill(LIGHT, 45)]))
    groups.append(grp("phone", [rect(80, 134, 15, p=(80, 80)), fill(BLUE, 8), stroke(LIGHT, 3)]))
    return build("learn-phone", op, groups)


# --- 01: an email hanging on a fishing hook ---------------------------------------

def hook():
    op = 120
    swing = anim([(0, -7), (60, 7), (120, -7)])
    rig = grp("rig", [
        grp("line", [path([(80, 4), (80, 70)]), stroke(LIGHT, 2, 70)]),
        grp("hook", [path([(80, 70), (80, 102), (63, 102), (63, 92)],
                          i=[(0, 0), (0, 0), (0, 11), (0, 0)],
                          o=[(0, 0), (0, 11), (0, 0), (0, 0)]),
                     stroke(LIGHT, 4)]),
        grp("barb", [path([(63, 92), (68, 97)]), stroke(LIGHT, 3.5)]),
        grp("envelope-flap", [path([(55, 109), (72, 121), (89, 109)]), stroke(BLUE, 2)]),
        grp("envelope", [rect(34, 23, 3, p=(72, 119)), fill(BLUE, 28), stroke(BLUE, 2)]),
    ], p=(80, 4), a=(80, 4), r=swing)
    groups = [rig]
    for n, (x0, x1, y0, size, t0) in enumerate([(116, 122, 148, 9, 0), (42, 36, 150, 6, 50),
                                               (124, 130, 150, 5, 80)]):
        t1 = t0 + 60
        p = anim([(0, [x0, y0]), (t0, [x0, y0]), (t1, [x1, y0 - 80]),
                  (120, [x1, y0 - 80])], "out")
        o = anim([(0, 0), (t0, 0), (t0 + 6, 80), (t1 - 12, 60), (t1, 0)])
        groups.append(grp("bubble-%d" % (n + 1), [ell(size), stroke(LIGHT, 1.5)], p=p, o=o))
    return build("learn-hook", op, groups)


# --- 02: an alarm clock shaking, with time running out ----------------------------

def alarm():
    op = 90
    shake = anim([(0, 0), (5, -10), (10, 10), (15, -10), (20, 10), (25, -10),
                  (30, 6), (36, 0), (90, 0)])
    spin = anim([(0, 0), (90, 360)], "lin")
    half_bell = path([(-13, 0), (13, 0)], i=[(0, 0), (0, -17)], o=[(0, -17), (0, 0)], closed=True)
    clock = grp("clock", [
        grp("minute-hand", [path([(80, 86), (80, 64)]), stroke(LIGHT, 3)],
            p=(80, 86), a=(80, 86), r=spin),
        grp("hour-hand", [path([(80, 86), (93, 94)]), stroke(LIGHT, 4)]),
        grp("centre", [ell(8, p=(80, 86)), fill(RED)]),
        grp("face", [ell(82, p=(80, 86)), fill(BLUE, 12), stroke(LIGHT, 4)]),
        grp("bell-left", [half_bell, fill(LIGHT, 90)], p=(52, 49), r=-35),
        grp("bell-right", [half_bell, fill(LIGHT, 90)], p=(108, 49), r=35),
        grp("legs", [path([(56, 121), (48, 133)]), path([(104, 121), (112, 133)]),
                     stroke(LIGHT, 4)]),
    ], p=(80, 86), a=(80, 86), r=shake)
    buzz_o = anim([(0, 0), (3, 100), (32, 100), (38, 0), (90, 0)], "lin")
    buzz = grp("buzz", [
        path([(26, 72), (17, 67)]), path([(24, 88), (14, 88)]), path([(26, 104), (17, 109)]),
        path([(134, 72), (143, 67)]), path([(136, 88), (146, 88)]), path([(134, 104), (143, 109)]),
        stroke(AMBER, 3)], o=buzz_o)
    countdown = grp("countdown", [ell(104, p=(80, 86)), trim(anim([(0, 100), (90, 0)], "lin")),
                                  stroke(RED, 3, 85)], p=(80, 86), a=(80, 86), r=-90)
    track = grp("track", [ell(104, p=(80, 86)), stroke(LIGHT, 3, 15)])
    return build("learn-alarm", op, [buzz, clock, countdown, track])


# --- 03: a magnifier finds the red flags in a message ------------------------------

def flag(x, y, t):
    s, o = pop_in(t, 146, 134)
    return grp("flag", [
        grp("cloth", [path([(0, -22), (15, -17), (0, -12)], closed=True), fill(RED)]),
        grp("pole", [path([(0, -22), (0, 0)]), stroke(LIGHT, 2)]),
    ], p=(x, y), s=s, o=o)


def magnifier():
    op = 150
    lens_p = anim([(0, [42, 60]), (34, [100, 74]), (66, [100, 74]),
                   (96, [60, 116]), (126, [60, 116]), (150, [42, 60])])
    lens = grp("magnifier", [
        grp("handle", [path([(13, 13), (25, 25)]), stroke(LIGHT, 6)]),
        grp("glass", [ell(32), fill(LIGHT, 12), stroke(LIGHT, 4)]),
    ], p=lens_p)
    hl_o = anim([(0, 0), (36, 0), (42, 40), (134, 40), (146, 0)])
    btn_o = anim([(0, 0), (98, 0), (104, 100), (134, 100), (146, 0)])
    groups = [
        lens,
        flag(128, 70, 40),
        flag(86, 112, 102),
        grp("button-ring", [rect(48, 18, 9, p=(56, 118)), stroke(RED, 2)], o=btn_o),
        grp("highlight", [rect(76, 9, 3, p=(72, 74)), fill(RED)], o=hl_o),
        grp("button", [rect(40, 12, 6, p=(56, 118)), fill(RED, 70)]),
        grp("text", [rect(80, 4, 2, p=(74, 62)), rect(70, 4, 2, p=(69, 74)),
                     rect(76, 4, 2, p=(72, 86)), rect(50, 4, 2, p=(59, 98)), fill(LIGHT, 55)]),
        grp("header", [rect(40, 4, 2, p=(68, 36)), rect(26, 3, 1.5, p=(61, 43)), fill(LIGHT, 60)]),
        grp("avatar", [ell(14, p=(38, 39)), fill(BLUE, 60)]),
        grp("card", [rect(108, 122, 11, p=(76, 82)), fill(BLUE, 8), stroke(LIGHT, 2.5)]),
    ]
    return build("learn-magnifier", op, groups)


# --- 04: who really owns a web address ---------------------------------------------

def link():
    op = 150
    box_p = anim([(0, [72, 70]), (52, [72, 70]), (68, [109, 70]), (150, [109, 70])])
    box_s = anim([(0, [100, 100]), (52, [100, 100]), (68, [106, 100]), (150, [106, 100])])
    box_c = anim([(0, AMBER), (56, AMBER), (66, RED), (150, RED)])
    box_o = anim([(0, 0), (10, 0), (18, 100), (134, 100), (146, 0)])
    tag_s, tag_o = pop_in(74, 146, 134)
    owner_o = anim([(0, 45), (60, 45), (68, 100), (134, 100), (146, 45)])
    fake_o = anim([(0, 70), (60, 70), (68, 35), (134, 35), (146, 70)])
    groups = [
        grp("owner-tag", [
            grp("caret", [path([(-5, -8), (0, -14), (5, -8)], closed=True), fill(RED, 85)]),
            grp("tag", [rect(52, 16, 8), fill(RED, 85)]),
            grp("tag-text", [rect(30, 3, 1.5), fill([1, 1, 1, 1], 90)]),
        ], p=(109, 102), s=tag_s, o=tag_o),
        grp("highlighter", [rect(40, 17, 5), stroke(box_c, 2)], p=box_p, s=box_s, o=box_o),
        grp("path", [rect(14, 5, 2.5, p=(138, 70)), fill(LIGHT, 40)]),
        grp("real-owner", [rect(34, 5, 2.5, p=(109, 70)), fill(LIGHT)], o=owner_o),
        grp("looks-real", [rect(32, 5, 2.5, p=(72, 70)), fill(LIGHT)], o=fake_o),
        grp("https", [rect(14, 5, 2.5, p=(46, 70)), fill(LIGHT, 40)]),
        grp("lock", [
            grp("shackle", [path([(-3.5, 0), (3.5, 0)], i=[(0, 0), (0, -5)], o=[(0, -5), (0, 0)]),
                            stroke(LIGHT, 1.8, 70)], p=(26, 68)),
            grp("lock-body", [rect(10, 8, 2, p=(26, 72)), fill(LIGHT, 70)]),
        ]),
        grp("address-bar", [rect(142, 30, 15, p=(80, 70)), fill(BLUE, 10), stroke(LIGHT, 2.5)]),
    ]
    return build("learn-link", op, groups)


# --- 05: a free gift, with a hook inside -------------------------------------------

def sparkle(x, y, t, size=7):
    s, o = pop_in(t, 84, 70)
    d = size
    star = path([(0, -d), (d * 0.28, -d * 0.28), (d, 0), (d * 0.28, d * 0.28),
                 (0, d), (-d * 0.28, d * 0.28), (-d, 0), (-d * 0.28, -d * 0.28)], closed=True)
    return grp("sparkle", [star, fill(AMBER)], p=(x, y), s=s, o=o)


def gift():
    op = 120
    lid_p = anim([(0, [80, 89]), (20, [80, 89]), (34, [72, 60]), (82, [72, 60]), (96, [80, 89]),
                  (120, [80, 89])])
    lid_r = anim([(0, 0), (20, 0), (34, -16), (82, -16), (96, 0), (120, 0)])
    lid = grp("lid", [
        grp("bow", [ell(15, 10, p=(73, 74)), ell(15, 10, p=(87, 74)), stroke(AMBER, 2.5)]),
        grp("lid-ribbon", [rect(10, 14, 0, p=(80, 83)), fill(AMBER, 85)]),
        grp("lid-box", [rect(82, 14, 4, p=(80, 83)), fill(BLUE, 30), stroke(LIGHT, 2.5)]),
    ], p=lid_p, a=(80, 89), r=lid_r)
    hook_p = anim([(0, [80, 140]), (30, [80, 140]), (46, [80, 64]), (70, [80, 64]),
                   (86, [80, 140]), (120, [80, 140])], "out")
    hook_shape = grp("scam-hook", [
        grp("line", [path([(0, -60), (0, -10)]), stroke(RED, 2, 60)]),
        grp("hook", [path([(0, -10), (0, 14), (-14, 14), (-14, 6)],
                          i=[(0, 0), (0, 0), (0, 9), (0, 0)],
                          o=[(0, 0), (0, 9), (0, 0), (0, 0)]), stroke(RED, 4)]),
        grp("barb", [path([(-14, 6), (-10, 10)]), stroke(RED, 3.5)]),
    ], p=hook_p)
    groups = [
        lid,
        grp("ribbon", [rect(10, 46, 0, p=(80, 113)), fill(AMBER, 85)]),
        grp("box", [rect(72, 46, 4, p=(80, 113)), fill(BLUE, 22), stroke(LIGHT, 2.5)]),
        hook_shape,
        sparkle(38, 62, 32), sparkle(124, 50, 36, 6), sparkle(126, 92, 40, 5),
    ]
    # The hook only shows above the box, as if it comes out of it.
    above_box = path_data([(0, 0), (160, 0), (160, 90), (0, 90)], closed=True)
    return build("learn-gift", op, groups, masks={"scam-hook": above_box})


# --- 06: a shield draws itself, then ticks -----------------------------------------

SHIELD = path_data(
    [(80, 26), (117, 40), (117, 72), (80, 128), (43, 72), (43, 40)],
    i=[(-15, 0), (-11, -6), (0, 0), (24, -11), (0, 28), (0, 0)],
    o=[(15, 0), (0, 0), (0, 28), (-24, -11), (0, 0), (11, -6)], closed=True)


def shield():
    op = 120
    shield_shape = {"ty": "sh", "nm": "path", "ks": static(SHIELD)}
    groups = [
        grp("tick", [path([(64, 76), (76, 88), (98, 62)]),
                     trim(anim([(0, 0), (30, 0), (46, 100)], "out")), stroke(GREEN, 6)]),
        grp("outline", [shield_shape, trim(anim([(0, 0), (30, 100)])), stroke(LIGHT, 4)]),
        grp("fill", [shield_shape, fill(BLUE, anim([(0, 0), (12, 0), (30, 14)]))]),
        grp("ring", [ell(92), stroke(GREEN, 2)], p=(80, 76),
            s=anim([(0, [80, 80]), (48, [80, 80]), (120, [140, 140])], "out"),
            o=anim([(0, 0), (46, 0), (48, 70), (120, 0)])),
    ]
    return build("learn-shield", op, groups)


ANIMATIONS = {
    "learn-phone.json": phone, "learn-hook.json": hook, "learn-alarm.json": alarm,
    "learn-magnifier.json": magnifier, "learn-link.json": link,
    "learn-gift.json": gift, "learn-shield.json": shield,
}

if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join("web", "animations")
    os.makedirs(out_dir, exist_ok=True)
    for name, make in ANIMATIONS.items():
        target = os.path.join(out_dir, name)
        with open(target, "w") as fh:
            json.dump(make(), fh, separators=(",", ":"))
        print("wrote", target)
