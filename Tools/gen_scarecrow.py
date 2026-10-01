"""Generate the training scarecrow sprite (single image, pivot bottom-center, PPU 24)."""
from PIL import Image
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Assets", "Sprites", "Scarecrow")
os.makedirs(OUT, exist_ok=True)
W, H = 32, 44

C = {
    "O": (40, 28, 24, 255),
    "D": (122, 82, 48, 255),   # wood
    "d": (86, 56, 34, 255),
    "S": (214, 190, 140, 255),  # sack
    "s": (176, 150, 104, 255),
    "E": (30, 22, 22, 255),
    "Y": (228, 188, 92, 255),   # straw
    "y": (184, 140, 60, 255),
    "R": (178, 52, 48, 255),
    "B": (92, 112, 152, 255),   # shirt
    "b": (64, 78, 112, 255),
    "P": (150, 104, 60, 255),   # patch
    "T": (120, 92, 60, 255),    # rope
}
SHADOW = (20, 14, 24, 89)


class Layer:
    def __init__(self):
        self.p = {}

    def px(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            self.p[(x, y)] = C[c]

    def rect(self, x0, y0, x1, y1, c):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for x in range(min(x0, x1), max(x0, x1) + 1):
                self.px(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                if ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2 <= 1:
                    self.px(x, y, c)

    def outlined(self):
        out = {}
        for (x, y) in self.p:
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) not in self.p and 0 <= nx < W and 0 <= ny < H:
                    out[(nx, ny)] = C["O"]
        out.update(self.p)
        return out


def main():
    img = Image.new("RGBA", (W, H))

    shadow = Layer()
    shadow.ellipse(16, 42, 8, 1, "O")
    for k in shadow.p:
        img.putpixel(k, SHADOW)

    parts = []

    pole = Layer()
    pole.rect(15, 16, 16, 41, "D")
    pole.rect(16, 16, 16, 41, "d")
    parts.append(pole)

    bar = Layer()
    bar.rect(3, 17, 28, 18, "D")
    bar.rect(3, 18, 28, 18, "d")
    parts.append(bar)

    straw = Layer()
    for x, y in ((2, 16), (1, 18), (2, 19), (3, 20), (29, 16), (30, 18), (29, 19), (28, 20)):
        straw.px(x, y, "Y")
    for x in range(9, 23, 2):
        straw.rect(x, 30, x, 32 + (x % 3), "Y")
        straw.px(x + 1, 31, "y")
    parts.append(straw)

    shirt = Layer()
    shirt.rect(5, 15, 26, 20, "B")
    shirt.rect(9, 15, 22, 30, "B")
    for x in range(9, 23):
        if x % 3 == 0:
            shirt.px(x, 31, "B")
    shirt.rect(5, 20, 26, 20, "b")
    shirt.rect(20, 16, 22, 30, "b")
    shirt.rect(11, 23, 13, 25, "P")
    shirt.px(12, 24, "y")
    shirt.rect(9, 26, 22, 26, "T")
    parts.append(shirt)

    head = Layer()
    head.ellipse(16, 10, 5, 5, "S")
    head.rect(19, 7, 21, 13, "s")
    head.rect(13, 15, 19, 15, "T")
    head.px(13, 9, "E")
    head.px(14, 9, "E")
    head.px(18, 9, "E")
    head.px(19, 9, "E")
    for x in range(13, 20):
        head.px(x, 12, "E" if x % 2 else "s")
    parts.append(head)

    hat = Layer()
    hat.rect(7, 5, 25, 6, "Y")
    hat.rect(7, 6, 25, 6, "y")
    hat.ellipse(16, 2, 5, 2, "Y")
    hat.rect(11, 3, 21, 4, "Y")
    hat.rect(11, 4, 21, 4, "R")
    hat.px(6, 6, "Y")
    hat.px(26, 6, "Y")
    parts.append(hat)

    for layer in parts:
        for k, col in layer.outlined().items():
            img.putpixel(k, col)

    img.save(os.path.join(OUT, "Scarecrow.png"))
    print("wrote Scarecrow.png")


if __name__ == "__main__":
    main()
