"""Procedural cape layer for the Swordsman sheets, used by gen_guandao.py.

The cape is anchored under the head of every frame so it follows the body bob,
and sways with the animation phase. Facing down/left/right it is drawn behind
the body; facing up it covers the back (drawn over the body, under the head).
"""
import math

F = 64
FEET_Y = 43

OUTLINE = (40, 30, 34, 255)
CAPE_LIGHT = (214, 62, 66, 255)
CAPE_MAIN = (178, 34, 48, 255)
CAPE_DARK = (122, 20, 38, 255)
CAPE_LINING = (92, 16, 32, 255)
CAPE_TRIM = (240, 196, 84, 255)

# Hex keys of every cape colour, so gen_mounted_rider.py keeps the cape below the saddle line.
COLOR_KEYS = {"%02x%02x%02x" % c[:3] for c in (CAPE_LIGHT, CAPE_MAIN, CAPE_DARK, CAPE_LINING, CAPE_TRIM)}

# Per-animation motion: sway amplitude (px) and how far the cape trails behind in side view (degrees).
MOTION = {
    "Idle": (0.5, 14),
    "Walk": (1.0, 22),
    "Run": (1.6, 48),
    "Attack": (1.0, 28),
}

ROWS = ("down", "left", "right", "up")


def _anchor(head):
    xs = [p[0] for p in head]
    ys = [p[1] for p in head]
    return (min(xs) + max(xs)) / 2, max(ys)


def _outline(core):
    out = dict(core)
    for (x, y) in core:
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in core:
                out[q] = OUTLINE
    return {p: c for p, c in out.items() if 0 <= p[0] < F and 0 <= p[1] < F}


def _front_back(hx, neck, amp, phase, lining):
    """Cape seen from the front (lining, peeking out around the body) or from the back."""
    top = int(round(neck)) - 2
    bottom = FEET_Y - (1 if lining else 3)
    core = {}
    for y in range(top, bottom + 1):
        t = (y - top) / max(1, bottom - top)
        half = (4.0 + (4.5 if lining else 2.5) * t) + amp * 0.5 * t * math.sin(phase)
        cx = hx + amp * 0.6 * t * math.sin(phase + 1.2)
        x0, x1 = int(round(cx - half)), int(round(cx + half))
        for x in range(x0, x1 + 1):
            hem = bottom + int(round(0.6 * amp * math.sin(x * 1.4 + phase)))
            if y > hem:
                continue
            edge = x in (x0, x1)
            if lining:
                c = CAPE_MAIN if edge else CAPE_LINING
            elif y >= hem:
                c = CAPE_TRIM
            elif y <= top + 1:
                c = CAPE_LIGHT
            elif t > 0.3 and int(round(x - cx)) in (-2, 2):
                c = CAPE_DARK
            elif edge:
                c = CAPE_DARK
            else:
                c = CAPE_MAIN
            core[(x, y)] = c
    return core


def _side(hx, neck, amp, phase, trail_deg, facing):
    """Cape trailing behind a character facing +x (facing=1) or -x (facing=-1)."""
    top = neck - 2
    length = FEET_Y - 1 - top
    trail = math.radians(trail_deg + 6 * amp * math.sin(phase))
    back = -facing
    core = {}
    steps = 4 * int(length) + 1
    for i in range(steps):
        t = i / (steps - 1)
        y = int(round(top + t * length * math.cos(trail)))
        sway = amp * t * math.sin(phase + t * 3.0)
        cx = hx + back * (2.0 + t * length * math.sin(trail) + sway)
        half = 1.2 + 2.0 * t
        x0, x1 = int(round(cx - half)), int(round(cx + half))
        for x in range(x0, x1 + 1):
            rear = (x - cx) * back > half - 1
            if i == steps - 1:
                c = CAPE_TRIM
            elif rear:
                c = CAPE_DARK
            elif t < 0.15:
                c = CAPE_LIGHT
            else:
                c = CAPE_MAIN
            if core.get((x, y)) != CAPE_TRIM:
                core[(x, y)] = c
    return core


def build(anim_key, row, frame, frame_count, head):
    """Returns (behind_body, over_body) pixel dicts for one frame."""
    if not head or row >= len(ROWS):
        return {}, {}
    amp, trail = MOTION.get(anim_key, (1.0, 20))
    phase = 2 * math.pi * frame / max(1, frame_count)
    hx, neck = _anchor(head)
    direction = ROWS[row]
    if direction == "up":
        return {}, _outline(_front_back(hx, neck, amp, phase, lining=False))
    if direction == "down":
        return _outline(_front_back(hx, neck, amp, phase, lining=True)), {}
    facing = 1 if direction == "right" else -1
    return _outline(_side(hx, neck, amp, phase, trail, facing)), {}
