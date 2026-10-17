"""Procedural pixel-art textures of the great galleon.

  galleon.png       512x512 atlas (hull, castles, roof, sails...), regions in REGIONS
  galleon_flag.png  64x64 flags (texture #1 of the model): the emblem can be replaced
                    by a resource pack without touching the model

Every region is (texture index, u, v, w, h) so the model generator and the
textures stay in sync.
"""
import random

from PIL import Image

from galley_texture import _fill, _jitter, _planks, _rgb

SIZE = 512
FLAG_SIZE = 64

REGIONS = {
    # wood
    "hull_dark":   (0, 0, 0, 64, 32),
    "hull_mid":    (0, 64, 0, 64, 32),
    "hull_light":  (0, 128, 0, 64, 32),
    "red_paint":   (0, 192, 0, 64, 32),
    "wale":        (0, 256, 0, 64, 16),
    "dark_wood":   (0, 256, 16, 32, 16),
    "end_grain":   (0, 288, 16, 16, 16),
    "iron":        (0, 304, 16, 16, 16),
    "gold":        (0, 320, 0, 32, 32),
    "rail":        (0, 352, 0, 64, 16),
    "rope":        (0, 352, 16, 16, 16),
    "blue_paint":  (0, 368, 16, 32, 16),
    "glow":        (0, 400, 16, 16, 16),
    "lantern":     (0, 416, 0, 16, 16),
    "gunport":     (0, 432, 0, 16, 16),
    "mast":        (0, 448, 0, 64, 32),
    "deck":        (0, 0, 32, 64, 64),
    "roof":        (0, 64, 32, 64, 64),
    "window":      (0, 128, 32, 32, 32),
    "glow_window": (0, 160, 32, 32, 32),
    "door":        (0, 192, 32, 32, 32),
    "grating":     (0, 224, 32, 32, 32),
    "panel":       (0, 256, 32, 64, 32),
    "cloth_roll":  (0, 320, 32, 64, 16),
    "carving":     (0, 320, 48, 32, 16),
    # sails
    "course":      (0, 0, 128, 256, 192),
    "topsail":     (0, 256, 128, 160, 128),
    "lateen":      (0, 256, 256, 160, 128),
    "jib":         (0, 416, 128, 96, 96),
    # flag texture
    "flag":        (1, 0, 0, 64, 40),
    "pennant":     (1, 0, 40, 64, 8),
}


def _tri_inside(pts, x, y):
    (ax, ay), (bx, by), (cx, cy) = pts

    def side(x1, y1, x2, y2):
        return (x - x2) * (y1 - y2) - (x1 - x2) * (y - y2)
    d1, d2, d3 = side(ax, ay, bx, by), side(bx, by, cx, cy), side(cx, cy, ax, ay)
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))


def _cloth(px, region, rng, mask=None, cross=False, seams_vertical=True):
    _, u, v, w, h = region
    cloth, shade, seam = _rgb("efe6d2"), _rgb("ddd1b6"), _rgb("bfae8c")
    red = _rgb("b3221c")
    for y in range(h):
        for x in range(w):
            if mask is not None and not mask(x + 0.5, y + 0.5, w, h):
                continue
            panel = (x // 16) if seams_vertical else (y // 16)
            c = shade if panel % 2 else cloth
            if seams_vertical and x % 16 == 15 or not seams_vertical and y % 16 == 15:
                c = seam
            if rng.random() < 0.08:
                c = _jitter(c, rng, 8)
            if cross:
                cw = max(6, w // 9)
                if abs(x - w / 2) < cw / 2 or abs(y - h * 0.45) < cw / 2:
                    c = _jitter(red, rng, 6)
            if y < 3:
                c = _rgb("b89a62")  # bolt rope along the head
            if mask is None and (x < 2 or x >= w - 2 or y >= h - 2):
                c = _rgb("b89a62")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def make_textures(path, flag_path, lateen_tri, jib_tri):
    rng = random.Random(1588)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()

    def reg(name):
        return REGIONS[name][1:]

    _planks(img, reg("hull_dark"), _rgb("5a3a1e"), _rgb("2f1d0e"), 4, rng)
    _planks(img, reg("hull_mid"), _rgb("80542a"), _rgb("4a3018"), 4, rng)
    _planks(img, reg("hull_light"), _rgb("b07a3c"), _rgb("6e4a22"), 4, rng)
    _planks(img, reg("red_paint"), _rgb("8f1f1b"), _rgb("561110"), 4, rng)
    _planks(img, reg("wale"), _rgb("2e221a"), _rgb("17110c"), 4, rng, joints=False)
    _planks(img, reg("dark_wood"), _rgb("4e321a"), _rgb("2b1a0c"), 4, rng)
    _planks(img, reg("deck"), _rgb("a87542"), _rgb("5c3c1e"), 4, rng)
    _planks(img, reg("rail"), _rgb("9a6a36"), _rgb("5e3f1d"), 8, rng, joints=False)
    _planks(img, reg("mast"), _rgb("7a4f27"), _rgb("4a2e15"), 8, rng, joints=False, vertical=True)
    _planks(img, reg("blue_paint"), _rgb("27407a"), _rgb("17264a"), 4, rng, joints=False)
    _fill(img, reg("iron"), _rgb("3b3b3f"), rng, 8)
    _fill(img, reg("end_grain"), _rgb("8c5e30"), rng, 10)

    # gold: carved trim with highlights
    u, v, w, h = reg("gold")
    for y in range(h):
        for x in range(w):
            c = _rgb("d4aa45") if (x + 2 * y) % 7 else _rgb("f2d27a")
            if (x * 3 + y) % 11 == 0:
                c = _rgb("9c7426")
            px[u + x, v + y] = _jitter(c, rng, 8) + (255,)
    u, v, w, h = reg("carving")
    for y in range(h):
        for x in range(w):
            scroll = ((x - 8 * (y // 8)) % 16) < 3 or y in (0, h - 1)
            c = _rgb("f0cf6f") if scroll else _rgb("b88a2e")
            px[u + x, v + y] = _jitter(c, rng, 6) + (255,)
    # rope
    u, v, w, h = reg("rope")
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = (_rgb("b9935a") if (x + y) % 3 else _rgb("7d6136")) + (255,)
    # roof tiles (red, overlapping rows)
    u, v, w, h = reg("roof")
    for y in range(h):
        for x in range(w):
            row = y // 6
            off = 4 if row % 2 else 0
            edge = y % 6 == 5 or (x + off) % 8 == 0
            c = _rgb("7e1a14") if edge else _rgb("b8352a")
            if not edge and y % 6 == 0:
                c = _rgb("d0523f")
            px[u + x, v + y] = _jitter(c, rng, 7) + (255,)
    # windows: leaded glass in a gold frame; glowing variant (lit cabin)
    for name, glass, glass2 in (("window", "37506b", "4f7092"), ("glow_window", "f2c25a", "ffe9a3")):
        u, v, w, h = reg(name)
        for y in range(h):
            for x in range(w):
                if x < 3 or x >= w - 3 or y < 3 or y >= h - 3:
                    c = _rgb("c9a043")
                elif (x - 3) % 7 == 6 or (y - 3) % 7 == 6:
                    c = _rgb("2c2a26")
                else:
                    c = _rgb(glass2) if (x + y) % 9 < 2 else _rgb(glass)
                px[u + x, v + y] = c + (255,)
    # door: planks, iron bands, frame
    u, v, w, h = reg("door")
    for y in range(h):
        for x in range(w):
            if x < 2 or x >= w - 2 or y < 2:
                c = _rgb("c9a043")
            elif y in (8, 9, 22, 23):
                c = _rgb("3b3b3f")
            else:
                c = _rgb("5a3a1c") if (x // 5) % 2 else _rgb("4a2e15")
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    # grating (hatches)
    u, v, w, h = reg("grating")
    for y in range(h):
        for x in range(w):
            c = _rgb("1a120a") if (x % 6 > 1 and y % 6 > 1) else _rgb("8a5e30")
            px[u + x, v + y] = c + (255,)
    # painted panel: red field, gold frame, blue medallion
    u, v, w, h = reg("panel")
    for y in range(h):
        for x in range(w):
            fx, fy = x % 32, y
            if fx < 2 or fx > 29 or fy < 2 or fy > h - 3:
                c = _rgb("d4aa45")
            elif (fx - 15.5) ** 2 + (fy - 15.5) ** 2 < 40:
                c = _rgb("27407a") if (fx - 15.5) ** 2 + (fy - 15.5) ** 2 < 28 else _rgb("d4aa45")
            else:
                c = _rgb("8f1f1b")
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    # rolled (furled) canvas on the yards
    u, v, w, h = reg("cloth_roll")
    for y in range(h):
        for x in range(w):
            c = _rgb("d9cdb2") if (x + y // 2) % 5 else _rgb("b8a888")
            px[u + x, v + y] = c + (255,)
    # lantern frame and glow
    u, v, w, h = reg("lantern")
    for y in range(h):
        for x in range(w):
            border = x in (0, w - 1) or y in (0, h - 1) or x == w // 2
            px[u + x, v + y] = (_rgb("2c2a26") if border else _rgb("f2c25a")) + (255,)
    u, v, w, h = reg("glow")
    for y in range(h):
        for x in range(w):
            d = abs(x - w / 2 + 0.5) + abs(y - h / 2 + 0.5)
            px[u + x, v + y] = (_rgb("fff1a8") if d < 5 else _rgb("ffc94a")) + (255,)
    # gun port: dark opening with a thick frame
    u, v, w, h = reg("gunport")
    for y in range(h):
        for x in range(w):
            frame = x < 2 or x >= w - 2 or y < 2 or y >= h - 2
            px[u + x, v + y] = (_rgb("5e3f1d") if frame else _rgb("120c08")) + (255,)

    # sails: courses carry a red cross, topsails plain, triangles with transparent outside
    _cloth(px, REGIONS["course"], rng, cross=True)
    _cloth(px, REGIONS["topsail"], rng)
    _, u, v, w, h = REGIONS["lateen"]
    tri = [(p[0] * w, p[1] * h) for p in lateen_tri]
    _cloth(px, REGIONS["lateen"], rng, mask=lambda x, y, w_, h_: _tri_inside(tri, x, y), seams_vertical=False)
    _, u, v, w, h = REGIONS["jib"]
    tri2 = [(p[0] * w, p[1] * h) for p in jib_tri]
    _cloth(px, REGIONS["jib"], rng, mask=lambda x, y, w_, h_: _tri_inside(tri2, x, y), seams_vertical=False)
    img.save(path)

    # ---- flags: blue field, gold border, gold fleur-de-lis; red / gold pennant
    flag = Image.new("RGBA", (FLAG_SIZE, FLAG_SIZE), (0, 0, 0, 0))
    fp = flag.load()
    _, u, v, w, h = REGIONS["flag"]
    lis = [
        "......##......",
        ".....####.....",
        "....######....",
        "....######....",
        ".....####.....",
        ".##...##...##.",
        "####..##..####",
        "#####.##.#####",
        ".############.",
        "..##########..",
        "......##......",
        "..##########..",
        "....##..##....",
        "...##....##...",
        "..##......##..",
    ]
    lh, lw = len(lis), len(lis[0])
    scale = 2
    ox, oy = (w - lw * scale) // 2, (h - lh * scale) // 2
    for y in range(h):
        for x in range(w):
            c = _jitter(_rgb("1f3f8f"), rng, 6)
            if x < 2 or x >= w - 2 or y < 2 or y >= h - 2:
                c = _rgb("d4aa45")
            lx, ly = (x - ox) // scale, (y - oy) // scale
            if 0 <= lx < lw and 0 <= ly < lh and lis[ly][lx] == "#":
                c = _jitter(_rgb("e8c35a"), rng, 8)
            fp[u + x, v + y] = c + (255,)
    _, u, v, w, h = REGIONS["pennant"]
    for y in range(h):
        for x in range(w):
            c = _rgb("b3221c") if (y < h // 2) else _rgb("d4aa45")
            fp[u + x, v + y] = _jitter(c, rng, 6) + (255,)
    flag.save(flag_path)
    return img, flag


def make_item_icon(path):
    """16x16 inventory icon: galleon seen from the side."""
    icon = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = icon.load()
    hull = _rgb("6b4423")
    dark = _rgb("3e2614")
    red = _rgb("9b2220")
    gold = _rgb("d4aa45")
    sail = _rgb("efe6d2")
    cross = _rgb("b3221c")
    mast = _rgb("4a2e15")
    roof = _rgb("b8352a")
    # hull
    for x in range(1, 15):
        p[x, 12] = hull + (255,)
    for x in range(2, 14):
        p[x, 13] = dark + (255,)
    for x in range(4, 12):
        p[x, 14] = dark + (255,)
    for x in range(0, 15):
        p[x, 11] = red + (255,) if 3 < x < 11 else hull + (255,)
    # castles
    for y in (9, 10):
        for x in range(0, 4):
            p[x, y] = hull + (255,)
        for x in range(12, 15):
            p[x, y] = hull + (255,)
    for x in range(0, 4):
        p[x, 8] = gold + (255,)
    for x in range(1, 3):
        p[x, 7] = roof + (255,)
    p[13, 8] = gold + (255,)
    # bowsprit
    p[15, 9] = mast + (255,)
    # masts and sails
    for y in range(1, 11):
        p[8, y] = mast + (255,)
    for y in range(3, 11):
        p[12, y] = mast + (255,)
    for y in range(7, 11):
        p[3, y] = mast + (255,)
    for y in range(3, 9):
        for x in range(6, 11):
            p[x, y] = (cross if x == 8 or y == 5 else sail) + (255,)
    for y in range(1, 3):
        for x in range(7, 10):
            p[x, y] = sail + (255,)
    for y in range(4, 8):
        for x in range(11, 14):
            p[x, y] = sail + (255,)
    p[8, 0] = _rgb("1f3f8f") + (255,)
    p[9, 0] = gold + (255,)
    icon.save(path)
