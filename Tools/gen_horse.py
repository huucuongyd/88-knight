"""Generate horse sprite sheets matching the Swordsman layout.

Each sheet is 64x64 frames, rows top->bottom: down, left, right, up.
The horse is drawn behind the rider, who uses leg-less "mounted" sheets
(Tools/gen_mounted_rider.py), so the rider's dangling legs are painted on the horse.
The rider is expected to be lifted by RIDER_LIFT pixels while mounted
(keep in sync with TopDownSceneSetup.HorseRiderLiftPixels).
"""
from PIL import Image
import math
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Assets", "Sprites", "Horse")
os.makedirs(OUT, exist_ok=True)
N = 64
RIDER_LIFT = 9
DROP = 1          # body sits this many px lower than the original design
GROUND = 45       # bottom row of the hooves
RUN_BOB = [1, 0, -1, -1, 0, 1]  # keep in sync with HorseAnimator.runBob

C = {
    "O": (38, 24, 26, 255),
    "B": (176, 102, 56, 255),
    "b": (128, 70, 40, 255),
    "d": (98, 52, 32, 255),
    "L": (210, 140, 84, 255),
    "M": (52, 32, 28, 255),
    "m": (86, 54, 40, 255),
    "K": (44, 34, 34, 255),
    "k": (84, 70, 66, 255),
    "W": (242, 232, 216, 255),
    "E": (18, 14, 16, 255),
    "S": (190, 40, 44, 255),
    "s": (130, 24, 34, 255),
    "Y": (236, 192, 76, 255),
    "T": (92, 58, 40, 255),
    # rider legs, sampled from the Swordsman sheet
    "P": (88, 121, 183, 255),
    "p": (52, 38, 87, 255),
    "Q": (64, 47, 41, 255),
    "q": (34, 24, 25, 255),
}
SHADOW = (20, 14, 24, 89)


class Layer:
    def __init__(self):
        self.p = {}

    def px(self, x, y, c):
        if 0 <= x < N and 0 <= y < N:
            self.p[(x, y)] = C[c]

    def rect(self, x0, y0, x1, y1, c):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for x in range(min(x0, x1), max(x0, x1) + 1):
                self.px(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c, clip=None):
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                if ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2 <= 1:
                    if clip is None or clip(x, y):
                        self.px(x, y, c)

    def line(self, x0, y0, x1, y1, c, w=1):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        vertical = abs(y1 - y0) >= abs(x1 - x0)
        for i in range(steps + 1):
            t = i / steps
            x = round(x0 + (x1 - x0) * t)
            y = round(y0 + (y1 - y0) * t)
            off = -(w // 2)
            if vertical:
                self.rect(x + off, y, x + off + w - 1, y, c)
            else:
                self.rect(x, y + off, x, y + off + w - 1, c)

    def recolor(self, pred, c):
        for k in list(self.p):
            if pred(*k):
                self.p[k] = C[c]

    def outlined(self):
        out = {}
        for (x, y) in self.p:
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) not in self.p and 0 <= nx < N and 0 <= ny < N:
                    out[(nx, ny)] = C["O"]
        out.update(self.p)
        return out


class Frame:
    def __init__(self):
        self.parts = []

    def add(self, layer, outline=True):
        self.parts.append(layer.outlined() if outline else dict(layer.p))

    def shadow(self, cx, cy, rx, ry):
        l = Layer()
        l.ellipse(cx, cy, rx, ry, "O")
        self.parts.append({k: SHADOW for k in l.p})

    def render(self):
        img = Image.new("RGBA", (N, N))
        for pixels in self.parts:
            for (x, y), col in pixels.items():
                paste(img, x, y, col)
        return img


def paste(img, x, y, col):
    if col[3] == 255:
        img.putpixel((x, y), col)
    elif img.getpixel((x, y))[3] == 0:
        img.putpixel((x, y), col)


# ---------- legs ----------
def leg(l, hx, hy, dx, lift, upper, lower, bend, l1, l2, sock=False, ground=GROUND, toe=1,
        upper_layer=None, upper_w=3):
    """Two-segment leg solved with simple IK.

    bend: +1 joint points to -x (hind hock in a right-facing view),
          -1 joint points to +x (front knee), 0 = straight (front/back views).
    toe:  direction the hoof front points (+1 right, -1 left, 0 symmetric).
    upper_layer: draw the thigh into this layer (e.g. the body) so it has no outline seam.
    """
    fx, fy = hx + dx, ground - lift - 2       # fetlock, just above the hoof
    vx, vy = fx - hx, fy - hy
    d = math.hypot(vx, vy)
    if d >= l1 + l2:
        a, h = d * l1 / (l1 + l2), 0.0
    else:
        a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
        h = math.sqrt(max(l1 * l1 - a * a, 0))
    kx = round(hx + a * vx / d + bend * h * (-vy / d))
    ky = round(hy + a * vy / d + bend * h * (vx / d))

    (upper_layer or l).line(hx, hy, kx, ky, upper, upper_w)
    l.line(kx, ky, fx, fy, lower, 2)
    if sock:
        l.line(kx + (fx - kx) // 2, ky + (fy - ky) // 2, fx, fy, "W", 2)
    # the 2-wide cannon covers fx-1..fx; the hoof is one px wider toward the toe
    x0 = fx - 2 if toe < 0 else fx - 1
    x1 = fx if toe < 0 else fx + 1
    l.rect(x0, fy + 1, x1, fy + 2, "K")
    l.px(x0 if toe < 0 else x1, fy + 1, "k")


def gait(anim, t, phase):
    """Returns (dx, lift) for one leg. t in [0,1)."""
    if anim == "idle":
        return 0, 0
    if anim == "walk":
        amp, stance, max_lift = 2, 0.6, 2
    else:
        amp, stance, max_lift = 3, 0.45, 3
    p = (t + phase) % 1.0
    if p < stance:
        return round(amp - 2 * amp * p / stance), 0
    q = (p - stance) / (1 - stance)
    return round(-amp + 2 * amp * q), round(max_lift * math.sin(math.pi * q))


GALLOP = {"hf": 0.0, "hn": 0.1, "ff": 0.5, "fn": 0.6}
WALK = {"hn": 0.0, "fn": 0.25, "hf": 0.5, "ff": 0.75}


def phases(anim):
    return GALLOP if anim == "run" else WALK


def anim_params(anim, i, count):
    t = i / count
    bob = RUN_BOB[i % len(RUN_BOB)] if anim == "run" else 0
    if anim == "idle":
        sw = [0, 1, 1, 0][i % 4]
        hb = [0, 0, 1, 0][i % 4]
    elif anim == "walk":
        sw = [0, 1, 1, 0, -1, -1][i % 6]
        hb = [0, 1, 0, 0, 1, 0][i % 6]
    else:
        sw = [2, 3, 3, 2, 2, 2][i % 6]
        hb = [1, 0, -1, 0, 1, 1][i % 6]
    return t, bob + DROP, sw, hb


# ---------- SIDE (facing right) ----------
def side(anim, i, count):
    t, b, sw, hb = anim_params(anim, i, count)
    ph = phases(anim)
    f = Frame()
    f.shadow(31, 46, 15, 2)

    far = Layer()
    dx, lift = gait(anim, t, ph["ff"])
    leg(far, 41, 34 + b, dx, lift, "d", "d", -1, 3.9, 4.3)
    dx, lift = gait(anim, t, ph["hf"])
    leg(far, 22, 33 + b, dx, lift, "d", "d", 1, 5.0, 4.6)
    f.add(far)

    tail = Layer()
    if anim == "run":
        tail.line(17, 28 + b, 11, 30 + b + (sw - 2), "M", 3)
        tail.line(11, 30 + b + (sw - 2), 8, 33 + b + (sw - 2), "M", 2)
    else:
        tail.line(17, 28 + b, 14 + sw // 2, 34 + b, "M", 3)
        tail.line(14 + sw // 2, 34 + b, 14 + sw, 40 + b, "M", 2)
    tail.px(15 + sw // 2, 32 + b, "m")
    f.add(tail)

    body = Layer()
    body.ellipse(31, 31 + b, 13, 3, "B")
    body.ellipse(21, 31 + b, 4, 4, "B")
    body.ellipse(41, 31 + b, 4, 3, "B")
    for k in range(4):
        body.ellipse(43 + k, 28 + b - k * 2, 3, 3, "B")
    body.recolor(lambda x, y: y >= 34 + b, "b")
    body.recolor(lambda x, y: y <= 28 + b and x < 41, "L")

    near = Layer()
    dx, lift = gait(anim, t, ph["fn"])
    leg(near, 39, 34 + b, dx, lift, "B", "b", -1, 3.9, 4.3, upper_layer=body)
    dx, lift = gait(anim, t, ph["hn"])
    body.ellipse(22, 34 + b, 3, 2, "B")
    leg(near, 23, 34 + b, dx, lift, "B", "b", 1, 4.6, 4.4, sock=True, upper_layer=body, upper_w=4)
    body.recolor(lambda x, y: x <= 19 and y >= 33 + b, "b")
    f.add(body)

    head = Layer()
    hy = 18 + b + hb
    head.ellipse(50, hy, 3, 3, "B")
    head.ellipse(54, hy + 3, 2, 2, "B")
    head.rect(50, hy + 1, 54, hy + 3, "B")
    head.recolor(lambda x, y: y >= hy + 4, "b")
    head.rect(48, hy - 5, 49, hy - 3, "B")
    head.px(49, hy - 5, "b")
    f.add(head)
    face = Layer()
    face.px(51, hy - 1, "E")
    face.px(52, hy - 1, "E")
    face.px(56, hy + 3, "d")
    face.line(52, hy - 3, 55, hy + 1, "W")
    face.line(52, hy + 3, 46, 24 + b, "T")
    face.line(46, 24 + b, 36, 26 + b, "T")
    f.add(face, outline=False)

    mane = Layer()
    mane.line(47, hy - 2, 40, 26 + b, "M", 2)
    mane.px(50, hy - 3, "M")
    mane.px(51, hy - 3, "M")
    f.add(mane)

    f.add(near)

    saddle = Layer()
    saddle.rect(26, 28 + b, 35, 34 + b, "S")
    saddle.rect(26, 34 + b, 35, 34 + b, "Y")
    saddle.rect(26, 28 + b, 26, 34 + b, "s")
    saddle.rect(27, 26 + b, 34, 28 + b, "s")
    saddle.px(27, 25 + b, "s")
    saddle.px(34, 25 + b, "Y")
    saddle.px(35, 25 + b, "Y")
    f.add(saddle)

    rider = Layer()
    rider.rect(30, 29 + b, 32, 32 + b, "P")
    rider.rect(30, 29 + b, 30, 32 + b, "p")
    rider.rect(30, 33 + b, 33, 34 + b, "Q")
    rider.rect(30, 34 + b, 33, 34 + b, "q")
    rider.rect(30, 35 + b, 33, 35 + b, "Y")
    f.add(rider)
    return f.render()


# ---------- DOWN (facing the camera) ----------
def down(anim, i, count):
    t, b, sw, hb = anim_params(anim, i, count)
    ph = phases(anim)
    f = Frame()
    f.shadow(31, 45, 9, 3)

    tail = Layer()
    tail.rect(30 + sw // 2, 13 + b, 32 + sw // 2, 16 + b, "M")
    f.add(tail)

    rump = Layer()
    rump.ellipse(31, 20 + b, 6, 5, "B")
    rump.recolor(lambda x, y: y <= 17 + b, "L")
    rump.rect(31, 16 + b, 31, 19 + b, "b")
    f.add(rump)

    hind = Layer()
    for key, hx in (("hf", 27), ("hn", 35)):
        _, lift = gait(anim, t, ph[key])
        leg(hind, hx, 30 + b, 0, lift, "d", "d", 0, 4.0, 4.0, ground=GROUND - 3, toe=0)
    f.add(hind)

    body = Layer()
    body.ellipse(31, 27 + b, 7, 5, "B")
    body.ellipse(31, 32 + b, 6, 4, "B")
    body.recolor(lambda x, y: x <= 25 or x >= 37, "b")
    f.add(body)

    saddle = Layer()
    saddle.rect(24, 22 + b, 38, 27 + b, "S")
    saddle.rect(24, 27 + b, 38, 27 + b, "Y")
    saddle.rect(24, 22 + b, 25, 26 + b, "s")
    saddle.rect(37, 22 + b, 38, 26 + b, "s")
    f.add(saddle)

    front_legs = Layer()
    for key, hx, sock in (("ff", 28, False), ("fn", 35, True)):
        _, lift = gait(anim, t, ph[key])
        leg(front_legs, hx, 35 + b, 0, lift, "B", "b", 0, 4.0, 4.0, sock=sock, toe=0)
    f.add(front_legs)

    neck = Layer()
    neck.ellipse(31, 31 + b, 4, 4, "B")
    neck.recolor(lambda x, y: y <= 28 + b, "L")
    f.add(neck)

    head = Layer()
    hy = 35 + b + hb
    head.ellipse(31, hy, 3, 4, "B")
    head.ellipse(31, hy + 4, 2, 2, "L")
    head.rect(28, hy - 6, 28, hy - 4, "B")
    head.rect(34, hy - 6, 34, hy - 4, "B")
    f.add(head)
    face = Layer()
    face.rect(31, hy - 3, 31, hy + 2, "W")
    face.px(28, hy - 2, "E")
    face.px(34, hy - 2, "E")
    face.px(30, hy + 5, "d")
    face.px(32, hy + 5, "d")
    face.rect(29, hy - 4, 33, hy - 4, "M")
    face.line(28, hy + 2, 26, 29 + b, "T")
    face.line(34, hy + 2, 36, 29 + b, "T")
    f.add(face, outline=False)

    return f.render()


# ---------- UP (facing away) ----------
def up(anim, i, count):
    t, b, sw, hb = anim_params(anim, i, count)
    ph = phases(anim)
    f = Frame()
    f.shadow(31, 45, 9, 3)

    head = Layer()
    hy = 7 + b + hb
    head.rect(29, 10 + b, 33, 21 + b, "B")
    head.ellipse(31, hy, 3, 3, "B")
    head.rect(28, hy - 5, 28, hy - 3, "B")
    head.rect(34, hy - 5, 34, hy - 3, "B")
    f.add(head)
    mane = Layer()
    mane.rect(30, hy - 2, 32, 21 + b, "M")
    mane.rect(31, hy - 2, 31, 21 + b, "m")
    f.add(mane, outline=False)

    fore = Layer()
    for key, hx in (("ff", 28), ("fn", 35)):
        _, lift = gait(anim, t, ph[key])
        leg(fore, hx, 30 + b, 0, lift, "d", "d", 0, 4.0, 4.0, ground=GROUND - 3, toe=0)
    f.add(fore)

    body = Layer()
    body.ellipse(31, 23 + b, 7, 5, "B")
    body.recolor(lambda x, y: x <= 25 or x >= 37, "b")
    f.add(body)

    saddle = Layer()
    saddle.rect(24, 20 + b, 38, 26 + b, "S")
    saddle.rect(24, 26 + b, 38, 26 + b, "Y")
    saddle.rect(24, 20 + b, 25, 25 + b, "s")
    saddle.rect(37, 20 + b, 38, 25 + b, "s")
    f.add(saddle)

    hind = Layer()
    for key, hx, sock in (("hf", 28, True), ("hn", 35, False)):
        _, lift = gait(anim, t, ph[key])
        leg(hind, hx, 35 + b, 0, lift, "B", "b", 0, 4.0, 4.0, sock=sock, toe=0)
    f.add(hind)

    rump = Layer()
    rump.ellipse(31, 31 + b, 6, 5, "B")
    rump.recolor(lambda x, y: y <= 28 + b, "L")
    rump.recolor(lambda x, y: y >= 35 + b, "b")
    f.add(rump)

    tail = Layer()
    sx = sw if anim != "run" else 0
    tail.line(31, 28 + b, 31 + sx, 35 + b, "M", 3)
    tail.line(31 + sx, 35 + b, 31 + sx, 40 + b, "M", 3)
    tail.rect(31 + sx, 30 + b, 31 + sx, 39 + b, "m")
    f.add(tail)

    return f.render()


def mirror(img):
    return img.transpose(Image.FLIP_LEFT_RIGHT)


ANIMS = {"Idle": ("idle", 4), "Walk": ("walk", 6), "Run": ("run", 6)}


def main():
    for name, (anim, count) in ANIMS.items():
        sheet = Image.new("RGBA", (N * count, N * 4))
        for i in range(count):
            right = side(anim, i, count)
            rows = [down(anim, i, count), mirror(right), right, up(anim, i, count)]
            for row, img in enumerate(rows):
                sheet.paste(img, (i * N, row * N))
        sheet.save(os.path.join(OUT, f"Horse_{name}.png"))
        print("wrote", name)


if __name__ == "__main__":
    main()
