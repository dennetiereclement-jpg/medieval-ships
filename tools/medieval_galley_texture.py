"""Texture of the red medieval galley (medieval_galley).

  medieval_galley.png   256x256 atlas, regions in REGIONS (u, v, w, h)

Colours taken from the reference picture: red hull with dark brown planking, blue trim
along the sheer, gold mouldings, red round shields with a white cross and a gold rim,
red and white vertical stripes on the sail, red dragon heads with gold eyes.
"""
import math
import random

from PIL import Image

from galley_texture import _fill, _jitter, _planks, _rgb

SIZE = 256

REGIONS = {
    "hull_dark":   (0, 0, 64, 32),
    "hull_red":    (64, 0, 64, 32),
    "blue_trim":   (128, 0, 64, 16),
    "wale":        (128, 16, 64, 16),
    "gold":        (192, 0, 32, 32),
    "ivory":       (224, 0, 16, 16),
    "eye":         (240, 0, 16, 16),
    "iron":        (224, 16, 16, 16),
    "glow":        (240, 16, 16, 16),
    "deck":        (0, 32, 64, 64),
    "dark_wood":   (64, 32, 32, 16),
    "end_grain":   (96, 32, 16, 16),
    "lantern":     (112, 32, 16, 16),
    "rope":        (64, 48, 16, 16),
    "cloth_roll":  (80, 48, 48, 16),
    "oar":         (128, 32, 64, 16),
    "mast":        (128, 48, 64, 16),
    "dragon":      (192, 32, 32, 32),
    "dragon_dark": (224, 32, 32, 32),
    "shield":      (64, 64, 32, 32),
    "flag":        (96, 64, 32, 16),
    "hull_light":  (128, 64, 64, 32),
    "red_paint":   (192, 64, 64, 16),
    "sail":        (0, 128, 128, 128),
}


def make_texture(path):
    rng = random.Random(1066)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    _planks(img, REGIONS["hull_dark"], _rgb("4b2d18"), _rgb("2b190c"), 4, rng)
    _planks(img, REGIONS["hull_red"], _rgb("a8261d"), _rgb("5e110c"), 4, rng)
    _planks(img, REGIONS["wale"], _rgb("3a2212"), _rgb("22140a"), 8, rng, joints=False)
    _planks(img, REGIONS["deck"], _rgb("b07a42"), _rgb("6a4522"), 4, rng)
    _planks(img, REGIONS["dark_wood"], _rgb("5a3a1c"), _rgb("33200e"), 4, rng)
    _planks(img, REGIONS["oar"], _rgb("d6a35c"), _rgb("9a6c34"), 8, rng, joints=False)
    _planks(img, REGIONS["mast"], _rgb("7a4f27"), _rgb("4a2e15"), 8, rng, joints=False)
    _planks(img, REGIONS["hull_light"], _rgb("a0703a"), _rgb("6a4520"), 4, rng)
    _planks(img, REGIONS["red_paint"], _rgb("b3261d"), _rgb("7a1712"), 8, rng, joints=False)
    _fill(img, REGIONS["iron"], _rgb("3b3b3f"), rng, 8)
    _fill(img, REGIONS["end_grain"], _rgb("8c5e30"), rng, 10)
    px = img.load()

    def reg(name):
        return REGIONS[name]

    # blue trim with a thin gold line along both edges
    u, v, w, h = reg("blue_trim")
    for y in range(h):
        for x in range(w):
            c = _rgb("d4aa45") if y in (0, 1, h - 2, h - 1) else _rgb("2c5b9c")
            if 2 < y < h - 3 and (x + y) % 16 == 0:
                c = _rgb("3f75b8")
            px[u + x, v + y] = _jitter(c, rng, 6) + (255,)
    # gold with carved highlights
    u, v, w, h = reg("gold")
    for y in range(h):
        for x in range(w):
            c = _rgb("f0cf6f") if (x * 3 + y * 5) % 11 == 0 else _rgb("c9a043")
            px[u + x, v + y] = _jitter(c, rng, 8) + (255,)
    _fill(img, REGIONS["ivory"], _rgb("efe6cf"), rng, 6)
    # dragon eye: gold iris, slit pupil
    u, v, w, h = reg("eye")
    for y in range(h):
        for x in range(w):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
            c = _rgb("1a0f08") if abs(x - 7.5) < 1.2 and d < 6 else (_rgb("ffd23f") if d < 6.5 else _rgb("b3261d"))
            px[u + x, v + y] = c + (255,)
    # dragon skin: overlapping red scales, darker variant for the crest and the jaw
    for name, base, edge, light in (("dragon", "c0281f", "6e120d", "e04a36"), ("dragon_dark", "8e1a14", "4a0907", "b3261d")):
        u, v, w, h = reg(name)
        for y in range(h):
            for x in range(w):
                row = y // 4
                off = 2 if row % 2 else 0
                fx, fy = (x + off) % 4, y % 4
                if fy == 3 or (fx == 0 and fy > 1):
                    c = _rgb(edge)
                elif fy == 0 and fx in (1, 2):
                    c = _rgb(light)
                else:
                    c = _rgb(base)
                px[u + x, v + y] = _jitter(c, rng, 6) + (255,)
    # rope
    u, v, w, h = reg("rope")
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = (_rgb("3a2a1a") if (x + y) % 3 else _rgb("22180e")) + (255,)
    # furled canvas
    u, v, w, h = reg("cloth_roll")
    for y in range(h):
        for x in range(w):
            stripe = (x // 6) % 2 == 0
            c = _rgb("b3221c") if stripe else _rgb("eee6d3")
            if (x + y // 2) % 5 == 0:
                c = tuple(int(k * 0.85) for k in c)
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
    # round shield: gold rim, red field, white cross, iron boss; transparent outside the disc
    u, v, w, h = reg("shield")
    for y in range(h):
        for x in range(w):
            dx, dy = x - w / 2 + 0.5, y - h / 2 + 0.5
            r = (dx * dx + dy * dy) ** 0.5
            if r > w / 2 - 0.3:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            if r > w / 2 - 3:
                c = _rgb("d4aa45") if (int(math.degrees(math.atan2(dy, dx))) // 30) % 2 else _rgb("b98d2f")
            elif r < 3:
                c = _rgb("c9a043") if r < 2 else _rgb("7a5a1e")
            elif abs(dx) < 2.6 or abs(dy) < 2.6:
                c = _rgb("f2ede2")
            else:
                c = _rgb("b3221c")
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    # flag: red with a white cross
    u, v, w, h = reg("flag")
    for y in range(h):
        for x in range(w):
            cross = abs(x - w * 0.38) < 2 or abs(y - h / 2 + 0.5) < 2
            px[u + x, v + y] = _jitter(_rgb("f2ede2") if cross else _rgb("c4231d"), rng, 6) + (255,)
    # sail: nine vertical cloths, red and white alternately (red at both edges), seams,
    # a darker reinforced head along the yard and a bolt rope round the edges
    u, v, w, h = reg("sail")
    n = 9
    for y in range(h):
        for x in range(w):
            k = int(x * n / w)
            red = k % 2 == 0
            c = _rgb("c32a22") if red else _rgb("f1ead9")
            shade = 1.0 - 0.06 * abs(y / h - 0.5) - (0.04 if (x * 5 + y * 3) % 23 == 0 else 0)
            c = tuple(int(min(255, k_ * shade)) for k_ in c)
            if abs(x * n / w - round(x * n / w)) < 0.06 and 0 < x < w - 1:
                c = tuple(int(k_ * 0.8) for k_ in c)  # seam between two cloths
            if y < 3:
                c = _rgb("8a1b15") if red else _rgb("c9bfa6")
            if x < 1 or x >= w - 1 or y >= h - 1:
                c = _rgb("6b4a2a")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    img.save(path)


def make_item_icon(path):
    """16x16 inventory icon: red galley with its striped sail."""
    icon = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = icon.load()
    for x in range(1, 15):
        lift = 2 if x < 3 or x > 12 else (1 if x < 4 or x > 11 else 0)
        for y in range(12 - lift, 14):
            p[x, y] = _rgb("a8261d" if y < 13 else "4b2d18") + (255,)
        if 3 <= x <= 12 and x % 2 == 1:
            p[x, 12 - lift] = _rgb("e8e2d0") + (255,)
    for y in range(9, 12):
        p[0, y] = _rgb("c0281f") + (255,)
        p[15, y] = _rgb("c0281f") + (255,)
    for y in range(2, 12):
        p[8, y] = _rgb("5a3a1c") + (255,)
    for x in range(4, 13):
        for y in range(3, 9):
            p[x, y] = (_rgb("c32a22") if (x // 2) % 2 == 0 else _rgb("f1ead9")) + (255,)
    p[8, 1] = _rgb("c4231d") + (255,)
    p[9, 1] = _rgb("c4231d") + (255,)
    icon.save(path)
