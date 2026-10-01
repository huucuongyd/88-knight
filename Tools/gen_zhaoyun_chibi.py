from PIL import Image
import os

OUT = "/home/akb/UnityProjects/TopDown2D/Assets/Sprites/ZhaoYun"
os.makedirs(OUT, exist_ok=True)
N = 32

C = {
    "O": (36, 24, 36, 255),
    "W": (250, 250, 246, 255),
    "w": (204, 208, 220, 255),
    "G": (92, 84, 100, 255),
    "R": (214, 44, 52, 255),
    "r": (150, 26, 40, 255),
    "A": (176, 194, 220, 255),
    "a": (118, 134, 166, 255),
    "Y": (240, 198, 72, 255),
    "S": (255, 214, 180, 255),
    "P": (246, 150, 150, 255),
    "E": (28, 24, 40, 255),
    "H": (255, 255, 255, 255),
    "D": (120, 78, 40, 255),
    "T": (232, 238, 250, 255),
}


class Layer:
    def __init__(self):
        self.p = {}

    def px(self, x, y, c):
        if 0 <= x < N and 0 <= y < N:
            self.p[(x, y)] = C[c]

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c, clip=None):
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                if ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2 <= 1:
                    if clip is None or clip(x, y):
                        self.px(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.px(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def outlined(self):
        out = dict(self.p)
        for (x, y) in self.p:
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) not in self.p and 0 <= nx < N and 0 <= ny < N:
                    out[(nx, ny)] = C["O"]
        return out


def compose(layers):
    img = Image.new("RGBA", (N, N))
    for pixels, dy in layers:
        for (x, y), col in pixels.items():
            if 0 <= y + dy < N:
                img.putpixel((x, y + dy), col)
    return img


def spear(s, x, hand_y):
    s.line(x, 4, x, 28, "D")
    s.rect(x, 0, x, 3, "T")
    s.px(x - 1, 2, "T")
    s.px(x + 1, 2, "T")
    s.px(x - 1, 5, "R")
    s.px(x + 1, 5, "R")
    s.px(x - 1, 6, "R")
    s.px(x + 1, 6, "R")


# ---------- DOWN ----------
def down(frame):
    walking = frame != "idle"
    bob = -1 if walking else 0
    lift_l = 1 if frame == "walkA" else 0
    lift_r = 1 if frame == "walkB" else 0

    legs = Layer()
    legs.rect(10, 25, 12, 28 - lift_l, "W")
    legs.rect(10, 29 - lift_l, 12, 29 - lift_l, "G")
    legs.rect(19, 25, 21, 28 - lift_r, "W")
    legs.rect(19, 29 - lift_r, 21, 29 - lift_r, "G")

    h = Layer()
    h.ellipse(16, 21, 9, 5, "W")
    h.rect(8, 23, 24, 25, "w")
    h.rect(6, 17, 9, 21, "R")
    h.rect(23, 17, 26, 21, "R")
    h.rect(6, 21, 9, 21, "Y")
    h.rect(23, 21, 26, 21, "Y")

    hd = Layer()
    hd.ellipse(16, 24, 4, 4, "W")
    hd.rect(14, 27, 18, 28, "w")
    hd.px(15, 27, "a")
    hd.px(17, 27, "a")
    hd.rect(15, 20, 17, 21, "w")
    hd.rect(13, 23, 13, 24, "E")
    hd.rect(19, 23, 19, 24, "E")
    hd.px(12, 19, "W")
    hd.px(20, 19, "W")

    r = Layer()
    r.rect(7, 18, 8, 21, "A")
    r.rect(24, 18, 25, 21, "A")
    r.rect(11, 15, 21, 20, "R")
    r.rect(12, 15, 20, 20, "A")
    r.rect(12, 15, 13, 20, "a")
    r.rect(12, 19, 20, 19, "Y")
    r.rect(9, 15, 10, 17, "A")
    r.rect(22, 15, 23, 17, "A")
    r.ellipse(16, 9, 7, 6, "A")
    r.ellipse(16, 11, 5, 4, "S", clip=lambda x, y: y >= 8)
    r.rect(9, 7, 23, 7, "Y")
    r.rect(9, 8, 10, 13, "a")
    r.rect(22, 8, 23, 13, "a")
    r.rect(12, 10, 13, 12, "E")
    r.rect(19, 10, 20, 12, "E")
    r.px(12, 10, "H")
    r.px(19, 10, "H")
    r.px(11, 13, "P")
    r.px(21, 13, "P")
    r.px(16, 13, "r")
    r.rect(15, 2, 17, 3, "Y")
    r.rect(14, 0, 18, 1, "R")
    r.px(13, 1, "R")
    r.px(19, 1, "R")

    s = Layer()
    spear(s, 25, 16)
    s.rect(23, 15, 24, 16, "A")
    return compose([(legs.outlined(), 0), (h.outlined(), bob), (hd.outlined(), bob),
                    (r.outlined(), bob), (s.p, bob)])


# ---------- UP ----------
def up(frame):
    walking = frame != "idle"
    bob = -1 if walking else 0
    lift_l = 1 if frame == "walkA" else 0
    lift_r = 1 if frame == "walkB" else 0

    legs = Layer()
    legs.rect(10, 25, 12, 28 - lift_l, "w")
    legs.rect(10, 29 - lift_l, 12, 29 - lift_l, "G")
    legs.rect(19, 25, 21, 28 - lift_r, "w")
    legs.rect(19, 29 - lift_r, 21, 29 - lift_r, "G")

    h = Layer()
    h.ellipse(16, 21, 9, 5, "W")
    h.rect(8, 23, 24, 25, "w")
    h.rect(15, 23, 17, 29, "w")
    h.rect(6, 17, 9, 21, "R")
    h.rect(23, 17, 26, 21, "R")
    h.rect(6, 21, 9, 21, "Y")
    h.rect(23, 21, 26, 21, "Y")

    r = Layer()
    r.rect(7, 18, 8, 21, "A")
    r.rect(24, 18, 25, 21, "A")
    r.rect(10, 14, 22, 21, "R")
    r.rect(13, 15, 13, 21, "r")
    r.rect(19, 15, 19, 21, "r")
    r.rect(10, 14, 22, 14, "r")
    r.ellipse(16, 9, 7, 6, "A")
    r.ellipse(16, 9, 7, 6, "a", clip=lambda x, y: x <= 11 or y >= 13)
    r.rect(9, 7, 23, 7, "Y")
    r.rect(15, 10, 17, 15, "R")
    r.rect(15, 2, 17, 3, "Y")
    r.rect(14, 0, 18, 1, "R")
    r.px(13, 1, "R")
    r.px(19, 1, "R")

    s = Layer()
    spear(s, 25, 16)
    s.rect(23, 15, 24, 16, "A")
    return compose([(legs.outlined(), 0), (h.outlined(), bob), (r.outlined(), bob), (s.p, bob)])


# ---------- SIDE (facing right) ----------
SIDE_LEGS = {
    "idle":  [7, 10, 17, 20],
    "walkA": [6, 11, 18, 19],
    "walkB": [8, 9, 16, 21],
}


def side(frame):
    walking = frame != "idle"
    bob = -1 if walking else 0

    legs = Layer()
    for x, shade in zip(SIDE_LEGS[frame], "wWwW"):
        legs.rect(x, 25, x + 1, 28, shade)
        legs.rect(x, 29, x + 1, 29, "G")

    h = Layer()
    h.rect(3, 19, 5, 24, "w")
    h.px(2, 23, "w")
    h.ellipse(13, 22, 9, 4, "W")
    h.rect(6, 24, 21, 25, "w")
    h.rect(10, 18, 17, 22, "R")
    h.rect(10, 22, 17, 22, "Y")

    hd = Layer()
    hd.ellipse(24, 17, 5, 4, "W")
    hd.rect(19, 19, 21, 22, "W")
    hd.rect(26, 19, 29, 21, "w")
    hd.px(29, 19, "O")
    hd.rect(25, 15, 25, 16, "E")
    hd.px(22, 12, "W")
    hd.px(23, 12, "W")
    hd.px(23, 11, "W")
    hd.rect(19, 13, 21, 15, "w")

    r = Layer()
    r.rect(8, 14, 11, 20, "R")
    r.rect(7, 17, 8, 21, "r")
    r.rect(14, 19, 16, 23, "A")
    r.rect(14, 23, 16, 23, "a")
    r.rect(11, 15, 17, 19, "A")
    r.rect(11, 15, 12, 19, "a")
    r.rect(11, 18, 17, 18, "Y")
    r.rect(17, 16, 19, 17, "A")
    r.ellipse(14, 9, 6, 6, "A")
    r.ellipse(16, 11, 4, 4, "S", clip=lambda x, y: x >= 14 and y >= 8)
    r.rect(8, 7, 20, 7, "Y")
    r.rect(9, 8, 12, 13, "a")
    r.rect(18, 10, 19, 12, "E")
    r.px(18, 10, "H")
    r.px(17, 13, "P")
    r.rect(13, 2, 15, 3, "Y")
    r.rect(10, 0, 14, 1, "R")
    r.rect(8, 1, 10, 2, "R")
    r.px(7, 3, "R")

    s = Layer()
    s.line(17, 28, 25, 4, "D")
    s.rect(25, 0, 25, 3, "T")
    s.px(24, 2, "T")
    s.px(26, 2, "T")
    s.px(24, 5, "R")
    s.px(26, 5, "R")
    s.px(24, 6, "R")

    hand = Layer()
    hand.rect(19, 16, 21, 17, "A")
    return compose([(legs.outlined(), 0), (h.outlined(), bob), (s.p, bob), (hd.outlined(), bob),
                    (r.outlined(), bob), (hand.p, bob)])


frames = []
for name, fn in [("Down", down), ("Up", up), ("Side", side)]:
    for f in ["idle", "walkA", "walkB"]:
        img = fn(f)
        img.save(f"{OUT}/ZhaoYun_{name}_{f}.png")
        frames.append(img)

preview = Image.new("RGBA", (N * 9, N), (120, 160, 110, 255))
for i, im in enumerate(frames):
    preview.alpha_composite(im, (i * N, 0))
preview.resize((N * 9 * 4, N * 4), Image.NEAREST).save("/tmp/zhaoyun_preview.png")
big = Image.new("RGBA", (N * 3, N), (120, 160, 110, 255))
for i, im in enumerate(frames[0::3]):
    big.alpha_composite(im, (i * N, 0))
big.resize((N * 3 * 10, N * 10), Image.NEAREST).save("/tmp/zy_big.png")
