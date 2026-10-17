"""Texture of the elven sailboat (elven_sailboat).

  elven_sailboat.png   512x512 atlas, regions in REGIONS (u, v, w, h)

Colours and symbols from the reference picture: turquoise hull with gold filigree and a
deep blue bottom, glowing turquoise gems set in gold, pale honey deck, cream sails with a
blue border and fine gold seams: a gold eight-pointed star with a blue heart on the mainsail,
a gold crescent moon with small stars on the foresail, a star on the topsail.
"""
import math
import random

from PIL import Image

from galley_texture import _fill, _jitter, _planks, _rgb

SIZE = 512

REGIONS = {
    "hull_teal":   (0, 0, 64, 32),
    "hull_navy":   (64, 0, 64, 32),
    "ornament":    (128, 0, 128, 32),
    "gold":        (256, 0, 32, 32),
    "gem":         (288, 0, 16, 16),
    "silver":      (304, 0, 16, 16),
    "gold_relief": (320, 0, 32, 32),
    "deck":        (0, 32, 64, 64),
    "mast":        (64, 32, 64, 16),
    "dark_wood":   (64, 48, 32, 16),
    "rope":        (96, 48, 16, 16),
    "lantern":     (112, 48, 16, 16),
    "glow":        (128, 32, 16, 16),
    "hull_light":  (144, 32, 64, 32),
    "pennant":     (208, 32, 64, 16),
    "cloth_roll":  (208, 48, 64, 16),
    "cushion":     (272, 32, 32, 16),
    "sail_main":   (0, 128, 192, 192),
    "sail_jib":    (192, 128, 192, 192),
    "sail_top":    (384, 128, 128, 128),
}

CREAM = _rgb("f3ead6")
BLUE = _rgb("2b5fa8")
GOLD = _rgb("d9ad45")
GOLD_HI = _rgb("f6d77a")


def _tri_inside(tri, x, y):
    (ax, ay), (bx, by), (cx, cy) = tri

    def side(x1, y1, x2, y2):
        return (x - x2) * (y1 - y2) - (x1 - x2) * (y - y2)
    d1, d2, d3 = side(ax, ay, bx, by), side(bx, by, cx, cy), side(cx, cy, ax, ay)
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))


def _edge_dist(tri, x, y):
    d = 1e9
    for i in range(3):
        (x1, y1), (x2, y2) = tri[i], tri[(i + 1) % 3]
        ex, ey = x2 - x1, y2 - y1
        L2 = ex * ex + ey * ey
        t = max(0.0, min(1.0, ((x - x1) * ex + (y - y1) * ey) / L2))
        px, py = x1 + ex * t, y1 + ey * t
        d = min(d, math.hypot(x - px, y - py))
    return d


def _star(x, y, cx, cy, r_out, r_in, points, rot=0.0):
    """Inside a star polygon?"""
    dx, dy = x - cx, y - cy
    r = math.hypot(dx, dy)
    if r > r_out:
        return False
    a = (math.atan2(dy, dx) - rot) % (2 * math.pi / points)
    half = math.pi / points
    # radius of the star outline at this angle (linear between tip and notch)
    f = abs(a - half) / half
    edge = r_in + (r_out - r_in) * f
    return r <= edge


def _paint_sail(px, region, tri_unit, symbol, rng):
    u, v, w, h = region
    tri = [(p[0] * w, p[1] * h) for p in tri_unit]
    cx = sum(p[0] for p in tri) / 3
    cy = sum(p[1] for p in tri) / 3
    # the symbol sits a little towards the wide part of the sail
    size = min(w, h)
    small = [(cx + size * dx, cy + size * dy) for dx, dy in ((-0.2, -0.17), (0.17, -0.2), (0.22, 0.14), (-0.12, 0.2), (0.02, -0.3))]
    for y in range(h):
        for x in range(w):
            if not _tri_inside(tri, x + 0.5, y + 0.5):
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            d = _edge_dist(tri, x + 0.5, y + 0.5)
            k = 1.0 - 0.05 * ((x * 7 + y * 3) % 11 == 0)
            c = tuple(int(q * k) for q in CREAM)
            if (x + 2 * y) % 24 == 0:
                c = _rgb("e4d6b4")  # seam
            if d < 1.2:
                c = _rgb("8a6a3a")  # bolt rope
            elif d < 5.5:
                c = BLUE
            elif d < 7.0:
                c = GOLD
            elif symbol == "star":
                if _star(x, y, cx, cy, size * 0.21, size * 0.11, 8, rot=math.pi / 8):
                    c = GOLD_HI if _star(x, y, cx, cy, size * 0.17, size * 0.09, 8, rot=math.pi / 8) else _rgb("b58a2e")
                    if _star(x, y, cx, cy, size * 0.095, size * 0.035, 4):
                        c = BLUE
                    if math.hypot(x - cx, y - cy) < size * 0.025:
                        c = _rgb("bfe9f2")
                elif any(_star(x, y, sx, sy, size * 0.035, size * 0.012, 4) for sx, sy in small):
                    c = GOLD
            elif symbol == "moon":
                r = size * 0.17
                inside = math.hypot(x - cx, y - cy) < r and math.hypot(x - (cx + r * 0.45), y - (cy - r * 0.25)) > r * 0.86
                if inside:
                    c = GOLD if math.hypot(x - cx, y - cy) < r - 2 else _rgb("b58a2e")
                elif any(_star(x, y, sx, sy, size * 0.035, size * 0.012, 4) for sx, sy in small):
                    c = GOLD
            elif symbol == "small_star":
                if _star(x, y, cx, cy, size * 0.16, size * 0.06, 8, rot=math.pi / 8):
                    c = GOLD
                    if _star(x, y, cx, cy, size * 0.07, size * 0.03, 4):
                        c = BLUE
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def make_texture(path, tris):
    """tris: name -> triangle of the sail in [0,1] region coordinates (from the generator)."""
    rng = random.Random(1954)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    _planks(img, REGIONS["hull_teal"], _rgb("2c8290"), _rgb("17525c"), 4, rng)
    _planks(img, REGIONS["hull_navy"], _rgb("1d3f63"), _rgb("10243c"), 4, rng)
    _planks(img, REGIONS["deck"], _rgb("caa060"), _rgb("8a6634"), 4, rng)
    _planks(img, REGIONS["mast"], _rgb("d8c4a0"), _rgb("a48c66"), 8, rng, joints=False)
    _planks(img, REGIONS["dark_wood"], _rgb("6a4a2a"), _rgb("3e2a14"), 4, rng)
    _planks(img, REGIONS["hull_light"], _rgb("d2b88a"), _rgb("9a8058"), 4, rng)
    _fill(img, REGIONS["silver"], _rgb("c9d3dc"), rng, 8)
    px = img.load()

    def reg(name):
        return REGIONS[name]

    # gold, and gold carved in relief (leaves and scrolls)
    u, v, w, h = reg("gold")
    for y in range(h):
        for x in range(w):
            c = GOLD_HI if (x * 3 + y * 5) % 11 == 0 or y % 16 == 1 else GOLD
            px[u + x, v + y] = _jitter(c, rng, 8) + (255,)
    u, v, w, h = reg("gold_relief")
    for y in range(h):
        for x in range(w):
            s = math.sin(x * 0.55) * math.cos(y * 0.4) + 0.5 * math.sin((x + y) * 0.3)
            c = GOLD_HI if s > 0.6 else (GOLD if s > -0.4 else _rgb("8f6a22"))
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    # filigree band: turquoise with gold scrolls and a gold line along both edges
    u, v, w, h = reg("ornament")
    for y in range(h):
        for x in range(w):
            c = _rgb("2c8290")
            if y in (0, 1, h - 2, h - 1):
                c = GOLD
            else:
                yy = (y - h / 2) / (h / 2 - 2)
                wave = math.sin(x * 2 * math.pi / 32) * 0.55
                curl = math.hypot((x % 32) - 16, (y - h / 2) - wave * 8)
                if abs(yy - wave) < 0.13 or (6 < curl < 8.2 and (x % 32) > 12):
                    c = GOLD
                elif (x % 32 == 0 and abs(yy) < 0.3):
                    c = _rgb("6fd6e3")
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    # faceted turquoise gem
    u, v, w, h = reg("gem")
    for y in range(h):
        for x in range(w):
            d = abs(x - 7.5) + abs(y - 7.5)
            c = _rgb("d9fbff") if d < 3 else (_rgb("4fd4e4") if d < 6 else _rgb("1f8fa6"))
            if (x - y) % 5 == 0 and d > 3:
                c = _rgb("8deaf2")
            px[u + x, v + y] = c + (255,)
    # rope, lantern, glow
    u, v, w, h = reg("rope")
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = (_rgb("cdb98f") if (x + y) % 3 else _rgb("9c875f")) + (255,)
    u, v, w, h = reg("lantern")
    for y in range(h):
        for x in range(w):
            border = x in (0, w - 1) or y in (0, h - 1) or x == w // 2
            px[u + x, v + y] = (GOLD if border else _rgb("ffd98a")) + (255,)
    u, v, w, h = reg("glow")
    for y in range(h):
        for x in range(w):
            d = abs(x - w / 2 + 0.5) + abs(y - h / 2 + 0.5)
            px[u + x, v + y] = (_rgb("fff6c8") if d < 5 else _rgb("ffd76a")) + (255,)
    # pennant: white with a blue stripe and a gold edge
    u, v, w, h = reg("pennant")
    for y in range(h):
        for x in range(w):
            c = CREAM
            if abs(y - h / 2 + 0.5) < 2:
                c = BLUE
            if y in (0, h - 1):
                c = GOLD
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    u, v, w, h = reg("cloth_roll")
    for y in range(h):
        for x in range(w):
            c = CREAM if (x + y // 2) % 5 else _rgb("d8cdb2")
            if y in (0, h - 1):
                c = BLUE
            px[u + x, v + y] = c + (255,)
    u, v, w, h = reg("cushion")
    for y in range(h):
        for x in range(w):
            c = _rgb("2b5fa8") if (x // 4 + y // 4) % 2 else _rgb("3a72c0")
            if y in (0, h - 1) or x in (0, w - 1):
                c = GOLD
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    # the three sails and their symbols
    _paint_sail(px, reg("sail_main"), tris["sail_main"], "star", rng)
    _paint_sail(px, reg("sail_jib"), tris["sail_jib"], "moon", rng)
    _paint_sail(px, reg("sail_top"), tris["sail_top"], "small_star", rng)
    img.save(path)


def make_item_icon(path):
    """16x16 inventory icon: turquoise hull, cream triangular sails, gold star."""
    icon = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = icon.load()
    for x in range(1, 16):
        lift = 2 if x > 13 else (1 if x < 3 or x > 11 else 0)
        for y in range(11 - lift, 14):
            p[x, y] = (_rgb("2c8290") if y < 13 else _rgb("1d3f63")) + (255,)
        p[x, 11 - lift] = GOLD + (255,)
    for y in range(1, 11):
        p[7, y] = _rgb("d8c4a0") + (255,)
    for y in range(2, 10):
        for x in range(2, 7):
            if x >= 7 - (y - 1) * 0.6:
                p[x, y] = CREAM + (255,)
        for x in range(8, 14):
            if x <= 8 + (y - 1) * 0.7:
                p[x, y] = CREAM + (255,)
    p[4, 7] = GOLD + (255,)
    p[10, 6] = GOLD + (255,)
    icon.save(path)
