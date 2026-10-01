"""Make "mounted" copies of the Swordsman sheets with the legs and ground shadow removed.

The horse is drawn behind the rider, so the rider's legs must not show below the
saddle. Weapon pixels are kept so the glaive is never hidden by the horse.
"""
from PIL import Image
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Assets", "Sprites", "Swordsman")
SHEETS = ["Idle", "Attack"]
FRAME = 64
LEG_ROW = 39          # first row of the legs inside a frame
HAND_MAX_ROW = 42     # hands gripping the glaive can reach this low

WEAPON = {
    "281e22", "cdecf8", "96b2c8", "646c84", "966032", "6e4222", "e8ba46", "f6ca74",
    "c4282c", "8c1820", "e1eaf2", "4e3a2e",
}
SKIN = {"552d24", "e1b26e", "be865f", "a46f59", "795048"}


def keep(rgba, y):
    if rgba[3] < 255:
        return False
    if y < LEG_ROW:
        return True
    key = "%02x%02x%02x" % rgba[:3]
    return key in WEAPON or (key in SKIN and y <= HAND_MAX_ROW)


def main():
    for name in SHEETS:
        src = Image.open(os.path.join(ROOT, f"Swordsman_{name}.png")).convert("RGBA")
        out = src.copy()
        px = out.load()
        for y in range(out.height):
            fy = y % FRAME
            for x in range(out.width):
                if px[x, y][3] and not keep(px[x, y], fy):
                    px[x, y] = (0, 0, 0, 0)
        out.save(os.path.join(ROOT, f"Swordsman_{name}_Mounted.png"))
        print("wrote", name)


if __name__ == "__main__":
    main()
