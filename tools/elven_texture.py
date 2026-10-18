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
    "swirl":       (352, 0, 64, 32),
    "wing":        (416, 0, 64, 32),
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
    """Inside a star polygon (straight edges from each tip to the notches beside it)?"""
    dx, dy = x - cx, y - cy
    r = math.hypot(dx, dy)
    if r > r_out:
        return False
    if r < r_in:
        return True
    step = 2 * math.pi / points
    a = (math.atan2(dy, dx) - rot) % step
    if a > step / 2:
        a = step - a
    # triangle tip (r_out, 0) - notch (r_in, step / 2): is the point on the centre side of that edge?
    tx, ty = r_out, 0.0
    nx, ny = r_in * math.cos(step / 2), r_in * math.sin(step / 2)
    px, py = r * math.cos(a), r * math.sin(a)
    return (nx - tx) * (py - ty) - (ny - ty) * (px - tx) >= 0


def _compass(x, y, cx, cy, size):
    """Compass-rose star: four long points, four short diagonal ones, each point gold with a light
    and a dark half (carved relief), a blue heart. Returns a colour or None."""
    dx, dy = x - cx, y - cy
    r = math.hypot(dx, dy)
    if r < size * 0.035:
        return _rgb("bfe9f2")
    if r < size * 0.06:
        return BLUE
    for rot, r_out, r_in in ((0.0, size * 0.25, size * 0.05), (math.pi / 4, size * 0.16, size * 0.045)):
        if _star(x, y, cx, cy, r_out, r_in, 4, rot):
            ang = (math.atan2(dy, dx) - rot) % (math.pi / 2)
            return GOLD_HI if ang < math.pi / 4 else _rgb("b58a2e")
    if abs(r - size * 0.1) < 1.0:
        return BLUE
    return None


def _paint_sail(px, region, tri_unit, symbol, rng):
    u, v, w, h = region
    tri = [(p[0] * w, p[1] * h) for p in tri_unit]
    cx = sum(p[0] for p in tri) / 3
    cy = sum(p[1] for p in tri) / 3
    # the symbol sits a little towards the wide part of the sail
    size = min(w, h)
    head = min(tri, key=lambda p: p[1] + 0.001 * p[0])
    others = [p for p in tri if p is not head]
    angs = sorted(math.atan2(p[1] - head[1], p[0] - head[0]) for p in others)
    a0, seam_step = angs[0], (angs[1] - angs[0]) / 9
    small = [(cx + size * dx, cy + size * dy) for dx, dy in ((-0.2, -0.17), (0.17, -0.2), (0.22, 0.14), (-0.12, 0.2), (0.02, -0.3))]
    for y in range(h):
        for x in range(w):
            if not _tri_inside(tri, x + 0.5, y + 0.5):
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            d = _edge_dist(tri, x + 0.5, y + 0.5)
            k = 1.0 - 0.05 * ((x * 7 + y * 3) % 11 == 0)
            c = tuple(int(q * k) for q in CREAM)
            hx, hy = head
            ang = math.atan2(y + 0.5 - hy, x + 0.5 - hx)
            if abs(((ang - a0) / seam_step) - round((ang - a0) / seam_step)) * seam_step * math.hypot(x - hx, y - hy) < 0.6:
                c = _rgb("e2d3ae")  # seams radiating from the head
            dc = min(math.hypot(x + 0.5 - qx, y + 0.5 - qy) for qx, qy in tri)
            if dc < size * 0.11:
                c = tuple(int(q * 0.94) for q in c)  # reinforcing patch at each corner
                if dc > size * 0.11 - 1.2 and (x + y) % 2 == 0:
                    c = _rgb("b49a6a")
            if d < 1.2:
                c = _rgb("8a6a3a")  # bolt rope
            elif d < 5.5:
                c = BLUE
            elif d < 7.0:
                c = GOLD
            elif symbol == "star":
                cc = _compass(x, y, cx, cy, size * 1.25)
                if cc is not None:
                    c = cc
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
                cc = _compass(x, y, cx, cy, size * 1.0)
                if cc is not None:
                    c = cc
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
            # polished gold: soft rounded highlights, never a regular pattern
            t = 0.55 * math.sin(x * 0.4 + math.sin(y * 0.28) * 1.6) + 0.45 * math.cos(y * 0.33 + x * 0.1)
            c = (_rgb("fff0b8") if t > 0.7 else GOLD_HI if t > 0.25 else GOLD if t > -0.4 else _rgb("b38a30"))
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    u, v, w, h = reg("gold_relief")
    for y in range(h):
        for x in range(w):
            # carved leaves: lit tops, shaded hollows, a dark line where two leaves meet
            s = math.sin(x * 0.55) * math.cos(y * 0.4) + 0.5 * math.sin((x + y) * 0.3)
            if abs(s + 0.15) < 0.09:
                c = _rgb("7a5a1c")
            elif s > 0.85:
                c = _rgb("fff0b8")
            elif s > 0.35:
                c = GOLD_HI
            elif s > -0.5:
                c = GOLD
            else:
                c = _rgb("a07a28")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    # night-blue bottom: a scatter of tiny silver stars in the paint
    u, v, w, h = reg("hull_navy")
    for _ in range(w * h // 70):
        x, y = rng.randrange(w), rng.randrange(h)
        if y % 4:
            px[u + x, v + y] = (_rgb("d8e4f0") if rng.random() < 0.6 else _rgb("8fb4dc")) + (255,)
    # pale deck with a thin gold inlay between some planks
    u, v, w, h = reg("deck")
    for y in range(h):
        if y % 16 == 0:
            for x in range(w):
                px[u + x, v + y] = _jitter(_rgb("d9ad45"), rng, 6) + (255,)
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
    # carved gold arabesque (transparent around it): two spirals joined by an S, with leaves
    u, v, w, h = reg("swirl")
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = (0, 0, 0, 0)
    def dot(xx, yy, rad, col):
        for yy2 in range(int(yy - rad - 1), int(yy + rad + 2)):
            for xx2 in range(int(xx - rad - 1), int(xx + rad + 2)):
                if 0 <= xx2 < w and 0 <= yy2 < h and math.hypot(xx2 + 0.5 - xx, yy2 + 0.5 - yy) <= rad:
                    px[u + xx2, v + yy2] = col + (255,)
    for side, (sx, sy) in ((1, (14.0, 16.0)), (-1, (50.0, 16.0))):
        t = 0.0
        while t < 4.6 * math.pi:
            rad = 1.0 + 11.0 * t / (4.6 * math.pi)
            xx = sx + side * rad * math.cos(t)
            yy = sy + rad * math.sin(t) * 0.95
            dot(xx, yy, 1.6 if t > 2 else 1.1, GOLD_HI if math.sin(t) > 0 else GOLD)
            t += 0.05
    for k in range(40):
        f = k / 39
        xx, yy = 14 + 36 * f, 16 + 9 * math.sin(f * 2 * math.pi)
        dot(xx, yy, 1.7, GOLD)
    for lx, ly, s_ in ((25, 8, 1), (39, 24, -1), (32, 5, 1), (32, 27, -1)):
        for k in range(8):
            dot(lx + s_ * k * 0.6, ly - s_ * k * 0.4 + 2 * math.sin(k * 0.6), 1.6 - k * 0.15, GOLD_HI)
    # carved gold wing: feathers fanning out backwards (transparent around them)
    u, v, w, h = reg("wing")
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = (0, 0, 0, 0)
    for k in range(7):
        ang = math.radians(-8 + 9 * k)
        length = 58 - 5 * k
        for t in range(length):
            xx = 60 - t * math.cos(ang)
            yy = 26 - t * math.sin(ang) * 1.9 - 2 * k * (t / length)
            width = 2.6 * (1 - t / length) + 0.8
            dot(xx, yy, width, GOLD_HI if (t // 6 + k) % 2 else GOLD)
        dot(60 - length * math.cos(ang), 26 - length * math.sin(ang) * 1.9 - 2 * k, 1.2, _rgb("6fd6e3"))
    dot(58, 25, 4.0, GOLD)
    dot(58, 25, 2.2, _rgb("4fd4e4"))
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
