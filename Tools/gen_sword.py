"""Long broadsword variant of the Swordsman sheets: wide blade with a flat, squared-off tip.

Writes Assets/Sprites/Swordsman/Swordsman_Sword_{Idle,Walk,Run,Attack}.png; run
gen_mounted_rider.py afterwards for the riding versions. Only uses colours from the
glaive palette, so gen_mounted_rider.py already keeps them below the saddle line.
"""
import gen_guandao as g

PREFIX = "Swordsman_Sword"

POMMEL_LEN = 1
GRIP_LEN = 3
GUARD_HALF = 3
BLADE_LEN = 15
BLADE_HALF = 1.5


def build_sword(grip, d):
    n = (-d[1], d[0])
    core = {}

    def put(t, s, color):
        x = grip[0] + d[0] * t + n[0] * s
        y = grip[1] + d[1] * t + n[1] * s
        core[(int(round(x)), int(round(y)))] = color

    t = -GRIP_LEN - POMMEL_LEN
    while t <= 0:
        put(t, 0, g.GOLD if t < -GRIP_LEN else g.WOOD_DARK)
        t += 0.25

    s = -GUARD_HALF
    while s <= GUARD_HALF:
        put(1, s, g.GOLD)
        s += 0.25

    blade_start = 2
    t = blade_start
    while t <= blade_start + BLADE_LEN:
        s = -BLADE_HALF
        while s <= BLADE_HALF:
            if abs(s) >= BLADE_HALF - 0.25:
                c = g.STEEL_EDGE
            elif abs(s) < 0.4 and t < blade_start + BLADE_LEN - 2:
                c = g.STEEL_BACK
            else:
                c = g.STEEL_MAIN
            put(t, s, c)
            s += 0.25
        t += 0.25

    outlined = dict(core)
    for (x, y) in core:
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in core:
                outlined[q] = g.OUTLINE
    return {p: c for p, c in outlined.items() if 0 <= p[0] < g.F and 0 <= p[1] < g.F}


def sword_parts(grip, d, body_center):
    under, rest = {}, {}
    for p, c in build_sword(grip, d).items():
        along = (p[0] - grip[0]) * d[0] + (p[1] - grip[1]) * d[1]
        (under if along <= g.HAND_RADIUS - 2 else rest)[p] = c
    return under, rest


if __name__ == "__main__":
    for key in g.ANIMS:
        path, sheet = g.process(key, sword_parts, PREFIX, keep_unmatched_sword=False)
        print("wrote", path, sheet.size)
