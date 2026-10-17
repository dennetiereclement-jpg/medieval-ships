"""Procedural pixel-art textures of the great warship.

  warship.png       512x512 atlas (hull bands, gun ports, stern carvings, sails...)
  warship_flag.png  64x64 flags (texture #1 of the model): white field, blue fleur-de-lis,
                    replaceable by a resource pack

Every region is (texture index, u, v, w, h).
"""
import math
import random

from PIL import Image

from galley_texture import _fill, _jitter, _planks, _rgb
from galleon_texture import _cloth, _tri_inside

SIZE = 512
FLAG_SIZE = 64

REGIONS = {
    "hull_dark":   (0, 0, 0, 64, 32),
    "hull_black":  (0, 64, 0, 64, 32),
    "ochre":       (0, 128, 0, 64, 32),
    "white_bottom": (0, 192, 0, 64, 32),
    "wale":        (0, 256, 0, 64, 16),
    "dark_wood":   (0, 256, 16, 32, 16),
    "end_grain":   (0, 288, 16, 16, 16),
    "iron":        (0, 304, 16, 16, 16),
    "gold":        (0, 320, 0, 32, 32),
    "rail":        (0, 352, 0, 64, 16),
    "rope":        (0, 352, 16, 16, 16),
    "glow":        (0, 400, 16, 16, 16),
    "lantern":     (0, 416, 0, 16, 16),
    "gunport":     (0, 432, 0, 16, 16),
    "mast":        (0, 448, 0, 64, 32),
    "deck":        (0, 0, 32, 64, 64),
    "window":      (0, 128, 32, 32, 32),
    "glow_window": (0, 160, 32, 32, 32),
    "door":        (0, 192, 32, 32, 32),
    "grating":     (0, 224, 32, 32, 32),
    "panel":       (0, 256, 32, 64, 32),
    "cloth_roll":  (0, 320, 32, 64, 16),
    "carving":     (0, 320, 48, 32, 16),
    "arch_window": (0, 352, 48, 16, 24),
    "pilaster":    (0, 368, 48, 8, 32),
    "cannon":      (0, 376, 48, 16, 16),
    "hull_light":  (0, 64, 32, 64, 32),
    "red_paint":   (0, 64, 64, 64, 32),
    "garland":     (0, 448, 48, 32, 32),
    "mast_dark":   (0, 416, 32, 64, 16),
    "gold_relief": (0, 416, 48, 32, 32),
    "hull_ochre_dark": (0, 128, 64, 64, 32),
    # sails (plain canvas, like the reference)
    "course":      (0, 0, 128, 256, 192),
    "topsail":     (0, 256, 128, 160, 128),
    "lateen":      (0, 256, 256, 160, 128),
    "jib":         (0, 416, 128, 96, 96),
    # flag texture
    "flag":        (1, 0, 0, 64, 40),
    "pennant":     (1, 0, 40, 64, 8),
}

LIS = [
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


def _canvas(px, region, rng, mask=None, vertical=True):
    """Warm cream canvas: thin seams, reef bands with their points, bolt ropes, soft weathering."""
    _, u, v, w, h = region
    base = (243, 236, 220)
    for y in range(h):
        for x in range(w):
            if mask is not None and not mask(x + 0.5, y + 0.5, w, h):
                continue
            fy = y / h
            # soft vertical gradient (lighter in the belly) and a little grain
            k = 1.0 - 0.06 * abs(fy - 0.45) - (0.03 if (x * 7 + y * 3) % 17 == 0 else 0)
            c = tuple(int(b * k) for b in base)
            seam = (x % 12 == 11) if vertical else (y % 12 == 11)
            if seam:
                c = tuple(int(b * 0.9) for b in c)
            if mask is None:
                for band in (0.14, 0.27):
                    yb = int(h * band)
                    if y == yb or y == yb + 1:
                        c = (222, 212, 188)
                    if y == yb and x % 8 == 4:
                        c = (150, 130, 95)
                if y < 3 or x < 2 or x >= w - 2 or y >= h - 2:
                    c = (186, 160, 112)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def make_textures(path, flag_path, lateen_tri, jib_tri):
    rng = random.Random(1665)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()

    def reg(name):
        return REGIONS[name][1:]

    _planks(img, reg("hull_dark"), _rgb("4a3020"), _rgb("2a1a10"), 4, rng)
    _planks(img, reg("hull_black"), _rgb("221e1b"), _rgb("110f0d"), 4, rng, joints=False)
    _planks(img, reg("ochre"), _rgb("d1a440"), _rgb("9a7228"), 4, rng, joints=False)
    _planks(img, reg("hull_ochre_dark"), _rgb("a87d2c"), _rgb("6e5018"), 4, rng, joints=False)
    _planks(img, reg("white_bottom"), _rgb("e6e1d3"), _rgb("b8b2a2"), 4, rng)
    _planks(img, reg("wale"), _rgb("1d1a17"), _rgb("0e0c0b"), 4, rng, joints=False)
    _planks(img, reg("dark_wood"), _rgb("4e321a"), _rgb("2b1a0c"), 4, rng)
    _planks(img, reg("deck"), _rgb("a87542"), _rgb("5c3c1e"), 4, rng)
    _planks(img, reg("hull_light"), _rgb("b07a3c"), _rgb("6e4a22"), 4, rng)
    _planks(img, reg("red_paint"), _rgb("8f1f1b"), _rgb("561110"), 4, rng)
    _planks(img, reg("rail"), _rgb("9a6a36"), _rgb("5e3f1d"), 8, rng, joints=False)
    _planks(img, reg("mast"), _rgb("7a4f27"), _rgb("4a2e15"), 8, rng, joints=False, vertical=True)
    _planks(img, reg("mast_dark"), _rgb("3e2a18"), _rgb("22160c"), 8, rng, joints=False, vertical=True)
    _fill(img, reg("iron"), _rgb("2f2f33"), rng, 6)
    _fill(img, reg("end_grain"), _rgb("8c5e30"), rng, 10)

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
            px[u + x, v + y] = _jitter(_rgb("f0cf6f") if scroll else _rgb("b88a2e"), rng, 6) + (255,)
    u, v, w, h = reg("rope")
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = (_rgb("4a3a2a") if (x + y) % 3 else _rgb("2a2018")) + (255,)
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
    u, v, w, h = reg("grating")
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = (_rgb("1a120a") if (x % 6 > 1 and y % 6 > 1) else _rgb("8a5e30")) + (255,)
    # black panel with a gold frame and a gold medallion (stern and quarter decoration)
    u, v, w, h = reg("panel")
    for y in range(h):
        for x in range(w):
            fx = x % 32
            r2 = (fx - 15.5) ** 2 + (y - 15.5) ** 2
            if fx < 2 or fx > 29 or y < 2 or y > h - 3:
                c = _rgb("d4aa45")
            elif r2 < 40:
                c = _rgb("27407a") if r2 < 26 else _rgb("d4aa45")
            else:
                c = _rgb("1f1b18")
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    u, v, w, h = reg("cloth_roll")
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = (_rgb("d9cdb2") if (x + y // 2) % 5 else _rgb("b8a888")) + (255,)
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
    u, v, w, h = reg("gunport")
    for y in range(h):
        for x in range(w):
            frame = x < 2 or x >= w - 2 or y < 2 or y >= h - 2
            px[u + x, v + y] = (_rgb("3a2a18") if frame else _rgb("0b0807")) + (255,)
    # cannon barrel: dark bronze-iron with rings
    u, v, w, h = reg("cannon")
    for y in range(h):
        for x in range(w):
            c = _rgb("3a3a3e") if y % 5 else _rgb("5a5a60")
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    u, v, w, h = reg("pilaster")
    for y in range(h):
        for x in range(w):
            c = _rgb("f0cf6f") if x in (1, w - 2) or y % 8 == 0 else _rgb("b88a2e")
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    u, v, w, h = reg("arch_window")
    for y in range(h):
        for x in range(w):
            r = ((x + 0.5 - w / 2) ** 2 + (y + 0.5 - w / 2) ** 2) ** 0.5
            if y < w / 2 and r > w / 2:
                continue
            frame = x < 2 or x >= w - 2 or y >= h - 2 or (y < w / 2 and r > w / 2 - 2)
            if frame:
                c = _rgb("d4aa45")
            elif (x - 2) % 6 == 5 or y % 6 == 5:
                c = _rgb("2c2a26")
            else:
                c = _rgb("ffe9a3") if (x + y) % 7 < 2 else _rgb("f2c25a")
            px[u + x, v + y] = c + (255,)

    # gilded garland (wreath) around the upper gun ports, transparent centre
    u, v, w, h = reg("garland")
    for y in range(h):
        for x in range(w):
            r = ((x + 0.5 - w / 2) ** 2 + (y + 0.5 - h / 2) ** 2) ** 0.5
            if 9.5 < r < 15.5:
                leaf = ((math.atan2(y - h / 2, x - w / 2) * 6 / math.pi) % 1) < 0.5
                c = _rgb("f0cf6f") if leaf else _rgb("b88a2e")
                px[u + x, v + y] = _jitter(c, rng, 6) + (255,)
    # gold relief (scrolls, acanthus) for the stern and bow carvings
    u, v, w, h = reg("gold_relief")
    for y in range(h):
        for x in range(w):
            t = math.sin(x * 0.55) * 3 + math.cos(y * 0.5) * 3
            c = _rgb("f5d77d") if t > 2.2 else (_rgb("d4aa45") if t > -1.5 else _rgb("8f6a22"))
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)

    _canvas(px, REGIONS["course"], rng)
    _canvas(px, REGIONS["topsail"], rng)
    _, u, v, w, h = REGIONS["lateen"]
    tri = [(p[0] * w, p[1] * h) for p in lateen_tri]
    _canvas(px, REGIONS["lateen"], rng, mask=lambda x, y, w_, h_: _tri_inside(tri, x, y), vertical=False)
    _, u, v, w, h = REGIONS["jib"]
    tri2 = [(p[0] * w, p[1] * h) for p in jib_tri]
    _canvas(px, REGIONS["jib"], rng, mask=lambda x, y, w_, h_: _tri_inside(tri2, x, y), vertical=False)
    img.save(path)

    # flags: white field, blue fleur-de-lis (like the reference); white / blue pennant
    flag = Image.new("RGBA", (FLAG_SIZE, FLAG_SIZE), (0, 0, 0, 0))
    fp = flag.load()
    _, u, v, w, h = REGIONS["flag"]
    lh, lw = len(LIS), len(LIS[0])
    scale = 2
    ox, oy = (w - lw * scale) // 2, (h - lh * scale) // 2
    for y in range(h):
        for x in range(w):
            c = _jitter(_rgb("f1efe8"), rng, 4)
            lx, ly = (x - ox) // scale, (y - oy) // scale
            if 0 <= lx < lw and 0 <= ly < lh and LIS[ly][lx] == "#":
                c = _jitter(_rgb("23439a"), rng, 6)
            fp[u + x, v + y] = c + (255,)
    _, u, v, w, h = REGIONS["pennant"]
    for y in range(h):
        for x in range(w):
            c = _rgb("f1efe8") if y < h // 2 else _rgb("23439a")
            fp[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    flag.save(flag_path)


def make_item_icon(path):
    """16x16 inventory icon: three-decker seen from the side."""
    icon = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = icon.load()
    black, ochre, white = _rgb("26221f"), _rgb("c79a3c"), _rgb("e6e1d3")
    sail, mast, gold, blue = _rgb("efe6d2"), _rgb("4a2e15"), _rgb("d4aa45"), _rgb("23439a")
    for x in range(1, 15):
        p[x, 10] = black + (255,)
        p[x, 11] = (ochre if x % 2 else black) + (255,)
        p[x, 12] = black + (255,)
    for x in range(2, 14):
        p[x, 13] = (ochre if x % 2 == 0 else black) + (255,)
    for x in range(3, 13):
        p[x, 14] = white + (255,)
    for y in (8, 9):
        for x in range(0, 4):
            p[x, y] = black + (255,)
    for x in range(0, 4):
        p[x, 7] = gold + (255,)
    p[15, 8] = mast + (255,)
    p[14, 9] = mast + (255,)
    for mx, top in ((4, 2), (8, 0), (12, 3)):
        for y in range(top, 10):
            p[mx, y] = mast + (255,)
        for y in range(top + 1, 9, 3):
            for x in range(mx - 1, mx + 2):
                p[x, y] = sail + (255,)
                p[x, y + 1] = sail + (255,)
        p[mx, top] = blue + (255,)
    icon.save(path)
