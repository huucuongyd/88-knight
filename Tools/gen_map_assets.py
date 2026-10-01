"""Cut Assets/Sprites/map.png (AI-generated prop sheet on a dark grid) into transparent sprites.

- Removes the dark background and the grid lines, then splits the sheet into props by
  connected components (nearby pieces such as flower clusters are merged).
- Props are written to Assets/Sprites/Map/<Category>/<Category>_NN.png using CATEGORIES.
- A seamless grass tile is built from the inside of the plain grass sample.

Run `python3 gen_map_assets.py --preview /tmp/props.png` to get a numbered contact sheet
when the source image changes and CATEGORIES needs updating.
"""
import os
import sys
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Assets", "Sprites", "map.png")
OUT = os.path.join(ROOT, "Assets", "Sprites", "Map")

BG = (56, 63, 73)
BG_TOLERANCE = 20
HALO_TOLERANCE = 40
MERGE_GAP = 6
SMALL_PIXELS = 500
MIN_PIXELS = 30
MAX_HOLE = 150
# Grass/dirt samples in the top-left corner are handled separately.
GROUND_AREA = (0, 0, 395, 200)
# Inside of the tufted grass sample (no border), used for the seamless tile.
GRASS_SAMPLE = (12, 112, 86, 186)

# Prop index (from --preview) -> category. Unlisted props are skipped: the ground samples (9),
# the stump carrying the image generator's watermark (69) and loose petals.
CATEGORIES = {
    **{i: "Trees" for i in (10, 11, 19, 20, 21, 22, 23, 45, 46, 47, 48, 49)},
    **{i: "SmallTrees" for i in (4, 16, 17, 18, 28, 43, 44)},
    **{i: "Bushes" for i in (0, 5, 12, 13, 14, 15, 26, 27)},
    **{i: "Plants" for i in (1, 3, 6, 7, 8, 24, 25, 31, 32, 33, 34, 50, 51, 52, 53, 67)},
    **{i: "Flowers" for i in (2, 29, 30, 35, 36, 57, 58, 59, 60, 71, 72, 73, 74)},
    **{i: "Mushrooms" for i in (61, 62, 63, 64, 75, 76, 77, 78, 79)},
    **{i: "Rocks" for i in (65, 66)},
    **{i: "Pebbles" for i in (80, 81)},
    **{i: "Logs" for i in (68, 70, 82, 83, 84, 85, 86)},
}
# Props made of two touching trees stacked vertically, cut at the emptiest row between them.
SPLIT = {22}


def dist2(a, b):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


def is_gridish(p):
    return 65 <= p[0] <= 185 and 3 <= p[1] - p[0] <= 20 and 1 <= p[2] - p[0] <= 20


def background_mask(img):
    w, h = img.size
    px = img.load()
    bg = [[dist2(px[x, y], BG) <= BG_TOLERANCE ** 2 for x in range(w)] for y in range(h)]

    # Grid lines are 1-2px wide: a grid-coloured pixel with background on both sides is grid.
    for _ in range(3):
        changed = False
        for y in range(h):
            for x in range(w):
                if bg[y][x] or not is_gridish(px[x, y]):
                    continue
                horiz = 3 <= x < w - 3 and bg[y][x - 3] and bg[y][x + 3]
                vert = 3 <= y < h - 3 and bg[y - 3][x] and bg[y + 3][x]
                if horiz or vert:
                    bg[y][x] = True
                    changed = True
        if not changed:
            break

    # Anti-aliased halo: background-tinted pixels touching the background.
    halo = []
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if not bg[y][x] and dist2(px[x, y], BG) <= HALO_TOLERANCE ** 2:
                if bg[y][x - 1] or bg[y][x + 1] or bg[y - 1][x] or bg[y + 1][x]:
                    halo.append((x, y))
    for x, y in halo:
        bg[y][x] = True
    fill_holes(bg)
    return bg


def fill_holes(bg):
    """Dark shading inside foliage matches the background colour; small enclosed pockets are not background."""
    h, w = len(bg), len(bg[0])
    seen = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if not bg[y][x] or seen[y][x]:
                continue
            stack, pts, touches_edge = [(x, y)], [], False
            seen[y][x] = True
            while stack:
                cx, cy = stack.pop()
                pts.append((cx, cy))
                if cx in (0, w - 1) or cy in (0, h - 1):
                    touches_edge = True
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and bg[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            if not touches_edge and len(pts) <= MAX_HOLE:
                for px_, py_ in pts:
                    bg[py_][px_] = False


def components(bg, area_skip):
    h, w = len(bg), len(bg[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for y in range(h):
        for x in range(w):
            if bg[y][x] or seen[y][x]:
                continue
            if area_skip[0] <= x < area_skip[2] and area_skip[1] <= y < area_skip[3]:
                continue
            stack, pts = [(x, y)], []
            seen[y][x] = True
            while stack:
                cx, cy = stack.pop()
                pts.append((cx, cy))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < w and 0 <= ny < h and not bg[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            stack.append((nx, ny))
            comps.append(pts)
    return comps


def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def merge_close(comps):
    """Merges small pieces (flower clusters, pebbles) whose boxes are near each other."""
    boxes = [[bbox(c), c] for c in comps]
    merged = True
    while merged:
        merged = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if len(boxes[i][1]) > SMALL_PIXELS and len(boxes[j][1]) > SMALL_PIXELS:
                    continue
                a, b = boxes[i][0], boxes[j][0]
                if a[0] - MERGE_GAP < b[2] and b[0] - MERGE_GAP < a[2] and a[1] - MERGE_GAP < b[3] and b[1] - MERGE_GAP < a[3]:
                    pts = boxes[i][1] + boxes[j][1]
                    boxes[i] = [bbox(pts), pts]
                    del boxes[j]
                    merged = True
                    break
            if merged:
                break
    return [c for _, c in boxes]


def extract_props(img):
    bg = background_mask(img)
    comps = [c for c in components(bg, GROUND_AREA) if len(c) >= 4]
    comps = [c for c in merge_close(comps) if len(c) >= MIN_PIXELS]
    # Reading order: top-to-bottom rows of ~40px, then left-to-right.
    comps.sort(key=lambda c: (bbox(c)[3] // 40, bbox(c)[0]))
    px = img.load()
    props = []
    for pts in comps:
        x0, y0, x1, y1 = bbox(pts)
        sprite = Image.new("RGBA", (x1 - x0, y1 - y0))
        for x, y in pts:
            sprite.putpixel((x - x0, y - y0), px[x, y] + (255,))
        props.append(((x0, y0, x1, y1), sprite))
    return props


def split_pair(sprite):
    w, h = sprite.size
    alpha = sprite.getchannel("A").load()
    counts = [sum(1 for x in range(w) if alpha[x, y]) for y in range(h)]
    cut = min(range(h * 3 // 10, h * 7 // 10), key=lambda y: counts[y])
    parts = []
    for y0, y1 in ((0, cut), (cut, h)):
        half = sprite.crop((0, y0, w, y1))
        parts.append(half.crop(half.getbbox()))
    return parts


def _wrap_rows(img, band):
    """Cross-fades the last `band` rows into the first ones so the bottom edge continues into the top."""
    w, h = img.size
    src = img.load()
    out_h = h - band
    out = Image.new("RGB", (w, out_h))
    dst = out.load()
    for y in range(out_h):
        for x in range(w):
            a = src[x, y + band]
            if y < out_h - band:
                dst[x, y] = a
            else:
                t = (y - (out_h - band) + 1) / (band + 1)
                b = src[x, y - (out_h - band)]
                dst[x, y] = tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))
    return out


def seamless_tile(img):
    band = 14
    tile = _wrap_rows(img.crop(GRASS_SAMPLE), band)
    tile = _wrap_rows(tile.transpose(Image.TRANSPOSE), band).transpose(Image.TRANSPOSE)
    return tile


def preview(props, path):
    draw_img = Image.open(SRC).convert("RGB")
    draw = ImageDraw.Draw(draw_img)
    for i, (box, _) in enumerate(props):
        draw.rectangle(box, outline=(255, 0, 255))
        draw.text((box[0] + 1, box[1] + 1), str(i), fill=(255, 255, 0))
    draw_img.save(path)


def main():
    img = Image.open(SRC).convert("RGB")
    props = extract_props(img)
    if "--preview" in sys.argv:
        preview(props, sys.argv[sys.argv.index("--preview") + 1])
        print(len(props), "props")
        return

    counters = {}
    for i, (_, sprite) in enumerate(props):
        cat = CATEGORIES.get(i)
        if cat is None:
            continue
        folder = os.path.join(OUT, cat)
        os.makedirs(folder, exist_ok=True)
        for part in split_pair(sprite) if i in SPLIT else [sprite]:
            counters[cat] = counters.get(cat, 0) + 1
            part.save(os.path.join(folder, f"{cat}_{counters[cat]:02d}.png"))

    ground = os.path.join(OUT, "Ground")
    os.makedirs(ground, exist_ok=True)
    seamless_tile(img).save(os.path.join(ground, "Grass.png"))
    print("wrote", {k: v for k, v in sorted(counters.items())}, "+ Ground/Grass.png")


if __name__ == "__main__":
    main()
