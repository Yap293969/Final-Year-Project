"""Builds the Lottie (JSON) animations for web/Game.html ("Scam or Safe?").

Uses the same helpers as make_learn_lotties.py, so both sets look alike.

    python scripts/make_game_lotties.py web/animations

writes four files:

    game-cards.json    start screen: three cards fan out, a question mark bounces (loops)
    game-correct.json  a green circle and tick draw themselves, with a burst (plays once)
    game-wrong.json    a red circle and cross draw themselves, with a shake (plays once)
    game-trophy.json   end screen: a trophy with twinkling stars (loops)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_learn_lotties import (  # noqa: E402  (the path must be set first)
    AMBER, GREEN, LIGHT, RED,
    anim, build, ell, fill, grp, path, pop_in, rect, stroke, trim,
)


# --- Start screen: three cards and a question mark ---------------------------------

CARD = [0.110, 0.149, 0.286, 1]   # solid navy, so the cards hide each other when stacked

QUESTION = dict(
    v=[(-9, -8), (0, -17), (9, -8), (0, 2), (0, 7)],
    o=[(0, -5.5), (5.5, 0), (0, 6), (0, 0), (0, 0)],
    i=[(0, 0), (-5.5, 0), (0, -6), (0, -4), (0, 0)],
)


def card(name, colour, r_keys, p_keys, extra=None):
    items = (extra or []) + [
        grp("face", [rect(54, 74, 9), fill(CARD), stroke(colour, 3)]),
    ]
    return grp(name, items, p=anim(p_keys), a=(0, 30), r=anim(r_keys))


def cards():
    op = 120
    fan = [(0, 0), (24, 1), (60, 1), (84, 0), (120, 0)]

    def keys(angle):
        return [(t, angle * f) for t, f in fan]

    def pos(dx):
        return [(t, [80 + dx * f, 112]) for t, f in fan]

    bounce = anim([(0, [0, 0]), (30, [0, 0]), (40, [0, -6]), (50, [0, 0]), (58, [0, -3]),
                   (64, [0, 0]), (120, [0, 0])], "out")
    mark = grp("question", [
        grp("curl", [path(QUESTION["v"], i=QUESTION["i"], o=QUESTION["o"]), stroke(LIGHT, 5)]),
        grp("dot", [ell(5.5, p=(0, 16)), fill(LIGHT)]),
    ], p=bounce)
    flag = grp("mini-flag", [
        grp("cloth", [path([(0, -8), (10, -5), (0, -2)], closed=True), fill(RED)]),
        grp("pole", [path([(0, -8), (0, 6)]), stroke(LIGHT, 1.8)]),
    ], p=(-2, 0))
    tick = grp("mini-tick", [path([(-7, 0), (-2, 5), (7, -5)]), stroke(GREEN, 3.2)])
    groups = [
        card("card-front", LIGHT, keys(0), pos(0), extra=[mark]),
        card("card-right", GREEN, keys(16), pos(26), extra=[tick]),
        card("card-left", RED, keys(-16), pos(-26), extra=[flag]),
    ]
    sparkle_s, sparkle_o = pop_in(40, 100, 86)
    star = path([(0, -6), (1.7, -1.7), (6, 0), (1.7, 1.7), (0, 6), (-1.7, 1.7),
                 (-6, 0), (-1.7, -1.7)], closed=True)
    groups.insert(0, grp("sparkle-1", [star, fill(AMBER)], p=(122, 46), s=sparkle_s, o=sparkle_o))
    s2, o2 = pop_in(48, 100, 86)
    groups.insert(0, grp("sparkle-2", [star, fill(AMBER)], p=(40, 58), s=s2, o=o2))
    return build("game-cards", op, groups)


# --- Answer feedback: tick or cross ----------------------------------------------------

def burst(colour, start):
    """Eight short lines flying out from the centre."""
    groups = []
    for k in range(8):
        groups.append(grp("ray-%d" % k, [
            path([(0, -46), (0, -56)]),
            trim(anim([(0, 0), (start, 0), (start + 8, 100)], "out"),
                 s=anim([(0, 0), (start + 6, 0), (start + 16, 100)], "out")),
            stroke(colour, 3.5),
        ], p=(80, 80), r=k * 45))
    return groups


def correct():
    op = 45
    groups = [
        grp("tick", [path([(62, 81), (75, 94), (100, 66)]),
                     trim(anim([(0, 0), (12, 0), (26, 100)], "out")), stroke(GREEN, 8)]),
        grp("circle", [ell(78, p=(80, 80)), trim(anim([(0, 0), (16, 100)], "out")), stroke(GREEN, 5)],
            p=(80, 80), a=(80, 80), r=-90),
        grp("glow", [ell(78, p=(80, 80)), fill(GREEN, anim([(0, 0), (14, 0), (22, 18)]))]),
    ] + burst(GREEN, 18)
    return build("game-correct", op, groups)


def wrong():
    op = 45
    shake = anim([(0, [80, 80]), (24, [80, 80]), (27, [73, 80]), (30, [87, 80]), (33, [75, 80]),
                  (36, [84, 80]), (40, [80, 80]), (45, [80, 80])], "lin")
    cross = grp("cross", [
        grp("stroke-1", [path([(-15, -15), (15, 15)]), trim(anim([(0, 0), (12, 0), (20, 100)], "out")),
                         stroke(RED, 8)]),
        grp("stroke-2", [path([(15, -15), (-15, 15)]), trim(anim([(0, 0), (17, 0), (25, 100)], "out")),
                         stroke(RED, 8)]),
    ], p=shake)
    ring = grp("ring", [
        grp("circle", [ell(78), trim(anim([(0, 0), (16, 100)], "out")), stroke(RED, 5)], r=-90),
        grp("glow", [ell(78), fill(RED, anim([(0, 0), (14, 0), (22, 16)]))]),
    ], p=shake)
    return build("game-wrong", op, [cross, ring])


# --- End screen: a trophy -------------------------------------------------------------

def trophy():
    op = 120
    cup = path([(-24, -28), (24, -28), (0, 10)],
               o=[(0, 0), (0, 24), (-17, 0)], i=[(0, 24), (0, 0), (17, 0)], closed=True)
    handle_l = path([(-23, -20), (-21, -2)], o=[(-17, 0), (0, 0)], i=[(-13, 2), (0, 0)])
    handle_r = path([(23, -20), (21, -2)], o=[(17, 0), (0, 0)], i=[(13, 2), (0, 0)])
    rise = anim([(0, [80, 96]), (18, [80, 78]), (120, [80, 78])], "pop")
    trophy_group = grp("trophy", [
        grp("star-mark", [path([(0, -10), (2.9, -3.6), (9.5, -3.1), (4.5, 1.4), (5.9, 8.1),
                                (0, 4.6), (-5.9, 8.1), (-4.5, 1.4), (-9.5, -3.1), (-2.9, -3.6)],
                               closed=True), fill(AMBER)], p=(0, -12)),
        grp("cup", [cup, fill(AMBER, 26), stroke(AMBER, 3.5)]),
        grp("handles", [handle_l, handle_r, stroke(AMBER, 3.5)]),
        grp("stem", [rect(8, 14, 1, p=(0, 17)), fill(AMBER, 80)]),
        grp("base", [rect(40, 9, 3, p=(0, 28)), fill(AMBER, 40), stroke(AMBER, 3)]),
    ], p=rise)
    star = path([(0, -7), (2, -2), (7, 0), (2, 2), (0, 7), (-2, 2), (-7, 0), (-2, -2)], closed=True)
    groups = [trophy_group]
    for k, (x, y, t, c) in enumerate([(34, 46, 20, AMBER), (128, 40, 32, LIGHT), (132, 96, 44, AMBER),
                                      (28, 104, 56, LIGHT), (80, 22, 68, AMBER)]):
        s, o = pop_in(t, t + 50, t + 36)
        groups.append(grp("star-%d" % k, [star, fill(c)], p=(x, y), s=s, o=o))
    groups.append(grp("ring", [ell(104), stroke(AMBER, 2, 30)], p=(80, 78),
                      s=anim([(0, [60, 60]), (18, [60, 60]), (60, [118, 118]), (120, [118, 118])], "out"),
                      o=anim([(0, 0), (18, 70), (60, 0), (120, 0)])))
    return build("game-trophy", op, groups)


ANIMATIONS = {
    "game-cards.json": cards, "game-correct.json": correct,
    "game-wrong.json": wrong, "game-trophy.json": trophy,
}

if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join("web", "animations")
    os.makedirs(out_dir, exist_ok=True)
    for name, make in ANIMATIONS.items():
        target = os.path.join(out_dir, name)
        with open(target, "w") as fh:
            json.dump(make(), fh, separators=(",", ":"))
        print("wrote", target)
