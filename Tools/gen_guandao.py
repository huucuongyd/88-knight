"""Replace the Swordsman lvl3 sword with a long wooden-handled guandao.

Reads the layered parts from the craftpix pack and writes recomposed sheets to
Assets/Sprites/Swordsman/Swordsman_{Idle,Walk,Run,Attack}.png.
"""
import math
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "craftpix-net-180537-free-swordsman-1-3-level-pixel-top-down-sprite-character",
                     "PNG", "Swordsman_lvl3", "Parts")
OUT = os.path.join(ROOT, "Assets", "Sprites", "Swordsman")
F = 64

ANIMS = {"Idle": "Idle", "Walk": "Walk", "Run": "Run", "Attack": "attack"}

STEEL = {(113, 120, 143), (143, 173, 194), (171, 225, 242), (97, 99, 121), (116, 133, 151), (132, 164, 186)}
OUTLINE_SRC = (57, 56, 69)
GUARD_SRC = (85, 45, 36)

OUTLINE = (40, 30, 34, 255)
WOOD = (150, 96, 50, 255)
WOOD_DARK = (110, 66, 34, 255)
STEEL_MAIN = (150, 178, 200, 255)
STEEL_EDGE = (205, 236, 248, 255)
STEEL_BACK = (100, 108, 132, 255)
GOLD = (232, 186, 70, 255)
RED = (196, 40, 44, 255)
RED_DARK = (140, 24, 32, 255)

BUTT_LEN = 7
SHAFT_LEN = 9
BLADE_EDGE = [1, 2, 2, 3, 3, 3, 3, 2, 1]
HAND_RADIUS = 2.5


def load(name):
    path = os.path.join(PARTS, f"Swordsman_lvl3_{name}.png")
    return Image.open(path).convert("RGBA") if os.path.exists(path) else None


def frame_pixels(img, cx, cy):
    out = {}
    if img is None:
        return out
    for y in range(F):
        for x in range(F):
            sx, sy = cx * F + x, cy * F + y
            if sx < img.width and sy < img.height:
                p = img.getpixel((sx, sy))
                if p[3] > 0:
                    out[(x, y)] = p
    return out


def largest_component(points):
    points = set(points)
    best = []
    while points:
        stack = [points.pop()]
        comp = []
        while stack:
            p = stack.pop()
            comp.append(p)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (p[0] + dx, p[1] + dy)
                    if q in points:
                        points.remove(q)
                        stack.append(q)
        if len(comp) > len(best):
            best = comp
    return best


def principal_axis(points):
    n = len(points)
    mx = sum(p[0] for p in points) / n
    my = sum(p[1] for p in points) / n
    sxx = sum((p[0] - mx) ** 2 for p in points)
    syy = sum((p[1] - my) ** 2 for p in points)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in points)
    angle = 0.5 * math.atan2(2 * sxy, sxx - syy)
    return (mx, my), (math.cos(angle), math.sin(angle))


def centroid(points):
    pts = list(points)
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def build_weapon(grip, d, body_center):
    """Returns pixels of the new weapon, keyed by position."""
    n = (-d[1], d[0])
    if abs(n[1]) > 0.35:
        if n[1] > 0:
            n = (-n[0], -n[1])
    elif (n[0] * (grip[0] - body_center[0])) < 0:
        n = (-n[0], -n[1])

    core = {}

    def put(t, s, color):
        x = grip[0] + d[0] * t + n[0] * s
        y = grip[1] + d[1] * t + n[1] * s
        core[(int(round(x)), int(round(y)))] = color

    t = -BUTT_LEN
    while t <= SHAFT_LEN:
        put(t, 0, WOOD if int((t + 100) * 2) % 3 else WOOD_DARK)
        t += 0.25
    for t in (-BUTT_LEN, -BUTT_LEN + 0.5):
        put(t, 0, STEEL_BACK)

    blade_start = SHAFT_LEN + 1
    for i, edge in enumerate(BLADE_EDGE):
        for sub in (0.0, 0.25, 0.5, 0.75):
            t = blade_start + i + sub
            s = -0.5
            while s <= edge:
                if s >= edge - 0.5:
                    c = STEEL_EDGE
                elif s <= 0:
                    c = STEEL_BACK
                else:
                    c = STEEL_MAIN
                put(t, s, c)
                s += 0.5
    for s in (-1, 0, 1, 2):
        put(blade_start - 0.5, s, GOLD)

    for k, c in ((1, RED), (2, RED), (3, RED_DARK)):
        put(blade_start - 1.5, -k * 0.8, c)
        put(blade_start - 2.0, -k * 0.8 - 0.5, c)

    outlined = dict(core)
    for (x, y) in core:
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in core:
                outlined[q] = OUTLINE
    return {p: c for p, c in outlined.items() if 0 <= p[0] < F and 0 <= p[1] < F}


def process(anim_key):
    src = ANIMS[anim_key]
    layers = {name: load(f"{src}_{name}") for name in ("shadow", "sword_back", "body", "head", "sword", "swing")}
    width = max(img.width for img in layers.values() if img is not None)
    height = max(img.height for img in layers.values() if img is not None)
    sheet = Image.new("RGBA", (width, height))

    for cy in range(height // F):
        for cx in range(width // F):
            px = {name: frame_pixels(img, cx, cy) for name, img in layers.items()}
            front_steel = [p for p, c in px["sword"].items() if c[:3] in STEEL]
            back_steel = [p for p, c in px["sword_back"].items() if c[:3] in STEEL]
            weapon_layer = "sword" if len(front_steel) >= len(back_steel) else "sword_back"
            steel = largest_component(front_steel if weapon_layer == "sword" else back_steel)

            weapon_front, weapon_back, under_body = {}, {}, {}
            leftovers = {}
            for name in ("sword", "sword_back"):
                for p, c in px[name].items():
                    if c[:3] not in STEEL and c[:3] != OUTLINE_SRC and c[:3] != GUARD_SRC:
                        leftovers[p] = c

            if len(steel) >= 4 and px["body"]:
                center, d = principal_axis(steel)
                proj = [((p[0] - center[0]) * d[0] + (p[1] - center[1]) * d[1], p) for p in steel]
                lo = centroid([p for t, p in proj if t <= min(proj)[0] + 1])
                hi = centroid([p for t, p in proj if t >= max(proj)[0] - 1])

                body_center = centroid(px["body"].keys())
                guards = [p for name in ("sword", "sword_back") for p, c in px[name].items() if c[:3] == GUARD_SRC]
                anchor = centroid(guards) if guards else body_center
                hand_end, tip = (lo, hi) if dist(lo, anchor) <= dist(hi, anchor) else (hi, lo)
                length = dist(hand_end, tip) or 1.0
                d = ((tip[0] - hand_end[0]) / length, (tip[1] - hand_end[1]) / length)
                grip = (hand_end[0] - d[0] * 1.5, hand_end[1] - d[1] * 1.5)

                for p, c in build_weapon(grip, d, body_center).items():
                    along = (p[0] - grip[0]) * d[0] + (p[1] - grip[1]) * d[1]
                    if along <= HAND_RADIUS:
                        under_body[p] = c
                    elif weapon_layer == "sword":
                        weapon_front[p] = c
                    else:
                        weapon_back[p] = c
            else:
                for name, target in (("sword", weapon_front), ("sword_back", weapon_back)):
                    for p, c in px[name].items():
                        target[p] = c

            frame = Image.new("RGBA", (F, F))
            for group in (px["shadow"], weapon_back, under_body, px["body"], px["head"],
                          weapon_front, leftovers, px["swing"]):
                for (x, y), c in group.items():
                    if c[3] == 255:
                        frame.putpixel((x, y), c)
                    else:
                        base = frame.getpixel((x, y))
                        a = c[3] / 255
                        if base[3] == 0:
                            frame.putpixel((x, y), c)
                        else:
                            frame.putpixel((x, y), tuple(int(c[i] * a + base[i] * (1 - a)) for i in range(3)) + (255,))
            sheet.paste(frame, (cx * F, cy * F))

    os.makedirs(OUT, exist_ok=True)
    out_path = os.path.join(OUT, f"Swordsman_{anim_key}.png")
    sheet.save(out_path)
    return out_path, sheet


if __name__ == "__main__":
    import sys
    previews = []
    for key in ANIMS:
        path, sheet = process(key)
        print("wrote", path, sheet.size)
        previews.append(sheet)
    if len(sys.argv) > 1:
        w = max(s.width for s in previews)
        h = sum(s.height for s in previews)
        prev = Image.new("RGBA", (w, h), (120, 160, 110, 255))
        y = 0
        for s in previews:
            prev.alpha_composite(s, (0, y))
            y += s.height
        prev.save(sys.argv[1])
