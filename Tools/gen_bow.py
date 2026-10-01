"""Bow variant of the Swordsman sheets.

Idle/Walk/Run reuse the craftpix layers and put a bow in the hand that holds the sword.
Attack is a custom draw-and-release pose built on the first Idle frame of each direction.
Writes Assets/Sprites/Swordsman/Swordsman_Bow_{Idle,Walk,Run,Attack}.png; run
gen_mounted_rider.py afterwards for the riding versions.
"""
import os
from PIL import Image

import gen_cape
import gen_guandao as g

PREFIX = "Swordsman_Bow"
F = g.F

STRING = (196, 188, 168, 255)
SKIN = (225, 178, 110, 255)
FLETCH = g.RED

# Hex keys of colours only the bow uses, so gen_mounted_rider.py keeps them below the saddle line.
COLOR_KEYS = {"%02x%02x%02x" % STRING[:3]}

BOW_HALF = 6
BOW_BEND = 2.5
HAND_RADIUS = 1.6

# Shooting pose, one entry per frame: string pull in pixels, or None when no arrow is nocked.
SHOT_PULL = [None, 1, 2, 3, None, None]
RELEASE_FRAME = 4
ROWS = ("down", "left", "right", "up")


def _outline(core, skip=()):
    out = dict(core)
    for (x, y), c in core.items():
        if c in skip:
            continue
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in core:
                out[q] = g.OUTLINE
    return {p: c for p, c in out.items() if 0 <= p[0] < F and 0 <= p[1] < F}


def _line(core, a, b, color):
    steps = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 2) + 1
    for i in range(steps + 1):
        t = i / steps
        p = (int(round(a[0] + (b[0] - a[0]) * t)), int(round(a[1] + (b[1] - a[1]) * t)))
        core.setdefault(p, color)


def _bow(grip, axis, bulge, pull=0, arrow_len=0, half=BOW_HALF):
    """Bow whose grip (the most bent point) sits at `grip`.

    axis: unit vector along the limbs, bulge: unit vector toward the target.
    pull: how far the string is drawn back, arrow_len: 0 for no arrow.
    """
    core = {}
    for i in range(-half * 4, half * 4 + 1):
        s = i / 4
        bend = BOW_BEND * ((s / half) ** 2)
        p = (grip[0] + axis[0] * s - bulge[0] * bend, grip[1] + axis[1] * s - bulge[1] * bend)
        tip = abs(s) > half - 1.2
        core[(int(round(p[0])), int(round(p[1])))] = g.WOOD_DARK if tip else g.WOOD
    tips = [(grip[0] + axis[0] * k * half - bulge[0] * BOW_BEND,
             grip[1] + axis[1] * k * half - bulge[1] * BOW_BEND) for k in (-1, 1)]
    nock = (grip[0] - bulge[0] * (BOW_BEND + pull), grip[1] - bulge[1] * (BOW_BEND + pull))

    arrow = {}
    if arrow_len:
        head = (nock[0] + bulge[0] * arrow_len, nock[1] + bulge[1] * arrow_len)
        _line(arrow, nock, head, g.WOOD)
        for k in (0, 1):
            arrow[(int(round(head[0] - bulge[0] * k)), int(round(head[1] - bulge[1] * k)))] = g.STEEL_EDGE if k == 0 else g.STEEL_MAIN
        arrow[(int(round(nock[0])), int(round(nock[1])))] = FLETCH
    pixels = _outline({**core, **arrow})

    string = {}
    for t in tips:
        _line(string, t, nock, STRING)
    for p, c in string.items():
        if p not in core and p not in arrow:
            pixels[p] = c
    return pixels


def bow_parts(grip, d, body_center):
    """Bow carried upright in the hand, bent away from the body."""
    side = grip[0] - body_center[0]
    sx = (1 if side > 0 else -1) if abs(side) >= 1.5 else (1 if d[0] >= 0 else -1)
    pixels = _bow(grip, (0, 1), (sx, 0))
    under, rest = {}, {}
    for p, c in pixels.items():
        near = (p[0] - grip[0]) ** 2 + (p[1] - grip[1]) ** 2 <= HAND_RADIUS ** 2
        (under if near else rest)[p] = c
    return under, rest


def _hand(pixels, p):
    x, y = int(round(p[0])), int(round(p[1]))
    for q in ((x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)):
        pixels[q] = SKIN


def shot_frame(direction, layers, frame):
    head, body = layers["head"], layers["body"]
    hx, hb = gen_cape._anchor(head)
    head_top = min(p[1] for p in head)
    body_x0 = min(p[0] for p in body)
    body_x1 = max(p[0] for p in body)
    pull = SHOT_PULL[frame]
    arrow_len = 0 if pull is None else 7 + pull
    pull = pull or 0
    if frame == RELEASE_FRAME:
        pull = -1

    behind, front = {}, {}
    if direction == "down":
        grip = (hx, 41)
        bow = _bow(grip, (1, 0), (0, 1), pull, arrow_len)
        front.update(bow)
        _hand(front, (grip[0] - 0.5, grip[1] - 0.5))
        if arrow_len:
            _hand(front, (grip[0] - 0.5, grip[1] - BOW_BEND - pull - 1))
    elif direction == "up":
        grip = (hx, head_top + 3)
        behind.update(_bow(grip, (1, 0), (0, -1), pull, arrow_len + 3 if arrow_len else 0, half=9))
    else:
        sx = 1 if direction == "right" else -1
        grip = (body_x1 + 2 if sx > 0 else body_x0 - 2, 37)
        front.update(_bow(grip, (0, 1), (sx, 0), pull, arrow_len))
        _hand(front, (grip[0] - 0.5, grip[1] - 0.5))
        if arrow_len:
            _hand(front, (grip[0] - sx * (BOW_BEND + pull + 1) - 0.5, grip[1] - 0.5))
    return behind, front


def process_attack():
    layers = {name: g.load(f"Idle_{name}") for name in ("shadow", "body", "head")}
    sheet = Image.new("RGBA", (F * len(SHOT_PULL), F * len(ROWS)))
    for cy, direction in enumerate(ROWS):
        px = {name: g.frame_pixels(img, 0, cy) for name, img in layers.items()}
        for cx in range(len(SHOT_PULL)):
            cape_back, cape_over = gen_cape.build("Attack", cy, cx, len(SHOT_PULL), px["head"])
            behind, front = shot_frame(direction, px, cx)
            frame = g.compose((px["shadow"], cape_back, behind, px["body"], cape_over, px["head"], front))
            sheet.paste(frame, (cx * F, cy * F))
    out_path = os.path.join(g.OUT, f"{PREFIX}_Attack.png")
    sheet.save(out_path)
    return out_path, sheet


if __name__ == "__main__":
    for key in ("Idle", "Walk", "Run"):
        path, sheet = g.process(key, bow_parts, PREFIX, keep_unmatched_sword=False)
        print("wrote", path, sheet.size)
    path, sheet = process_attack()
    print("wrote", path, sheet.size)
