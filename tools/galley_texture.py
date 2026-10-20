"""Procedural pixel-art texture for the medieval galley (256x256).

Every region used by the model is declared in REGIONS (u, v, w, h) so the
model generator and the texture stay in sync.
"""
import math
import random
from PIL import Image

SIZE = 256

REGIONS = {
    "hull_dark":  (0, 0, 64, 32),
    "hull_mid":   (64, 0, 64, 32),
    "red":        (128, 0, 64, 16),
    "hull_light": (128, 16, 64, 16),
    "dark_wood":  (192, 0, 32, 32),
    "gold":       (224, 0, 16, 16),
    "rope":       (240, 0, 8, 32),
    "transparent": (248, 0, 8, 8),
    "deck":       (0, 32, 64, 64),
    "mast":       (64, 32, 64, 16),
    "oar":        (64, 48, 64, 16),
    "canopy":     (64, 64, 32, 32),
    "valance":    (96, 64, 32, 16),
    "flag":       (128, 32, 32, 16),
    "lantern":    (160, 32, 16, 16),
    "glow":       (176, 32, 16, 16),
    "rail":       (192, 32, 64, 16),
    "end_grain":  (192, 48, 16, 16),
    "iron":       (208, 48, 16, 16),
    "rug":        (128, 64, 64, 32),
    "chart":      (192, 64, 32, 32),
    "sail":       (0, 160, 160, 80),
}


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _jitter(c, rng, amount):
    d = rng.randint(-amount, amount)
    return tuple(max(0, min(255, x + d)) for x in c)


def _planks(img, region, base, dark, plank_h, rng, joints=True, vertical=False):
    u, v, w, h = region
    px = img.load()
    if vertical:
        # planks run vertically (mast, oars): grain along v
        for x in range(w):
            col = _jitter(base, rng, 6) if x % plank_h else dark
            for y in range(h):
                c = col if x % plank_h else dark
                if c != dark and rng.random() < 0.18:
                    c = _jitter(base, rng, 14)
                px[u + x, v + y] = c + (255,)
        return
    rows = h // plank_h
    for r in range(rows):
        tone = _jitter(base, rng, 9)
        joint = rng.randint(6, w - 6)
        for y in range(plank_h):
            yy = v + r * plank_h + y
            for x in range(w):
                if y == plank_h - 1:
                    c = dark
                elif joints and x == joint:
                    c = dark
                else:
                    c = tone
                    if rng.random() < 0.22:
                        c = _jitter(tone, rng, 12)
                    if y == 0:
                        c = tuple(min(255, k + 14) for k in c)
                px[u + x, yy] = c + (255,)


def _fill(img, region, color, rng, noise=8):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = _jitter(color, rng, noise) + (255,)


# ---------------------------------------------------------------- finer materials
# (new helpers: _planks, _fill, _jitter and paint_lamp_glass above are shared by the other ships
# and stay as they are; these are used by the galley and the other small boats)
def _mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def _scale(c, k):
    return tuple(max(0, min(255, int(round(x * k)))) for x in c)


def _ramp(stops, t):
    """Colour on a gradient: stops = [(t0, colour0), (t1, colour1), ...] sorted by t."""
    if t <= stops[0][0]:
        return stops[0][1]
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            return _mix(c0, c1, (t - t0) / max(1e-6, t1 - t0))
    return stops[-1][1]


def fine_wood(img, region, base, dark, plank_h, rng, joints=True, vertical=False, knots=0.15, grain=0.11,
              pegs=True, shade=0.05):
    """Planks with a fine wavy grain: each plank its own tone, two or three grain streaks wandering
    along it, a long soft light variation, an occasional knot with the grain bending round it, a lit
    upper edge, a dark caulked seam, butt joints with two treenails. vertical=True: grain along v."""
    u, v, w, h = region
    px = img.load()
    L, H = (h, w) if vertical else (w, h)
    rows = max(1, -(-H // plank_h))
    for r in range(rows):
        tone = _jitter(base, rng, 7)
        f1, p1 = rng.uniform(0.05, 0.13), rng.uniform(0, 6.3)
        lines = [(rng.uniform(0.6, plank_h - 1.4), rng.uniform(0.25, 0.8), rng.uniform(0.08, 0.3), rng.uniform(0, 6.3),
                  rng.uniform(0.6, 1.0)) for _ in range(2 if plank_h <= 4 else 3)]
        joint = rng.randint(5, L - 6) if (joints and L > 14) else -99
        knot = (rng.uniform(3, L - 4), rng.uniform(0.8, max(1.0, plank_h - 1.8))) if rng.random() < knots else None
        for a in range(L):
            for b in range(plank_h):
                yy = r * plank_h + b
                if yy >= H:
                    break
                if b == plank_h - 1 and plank_h > 1:
                    c = dark
                elif a == joint:
                    c = _mix(dark, tone, 0.2)
                else:
                    k = 1.0 + shade * math.sin(a * f1 + p1)
                    for c0, amp, fr, ph, strength in lines:
                        yl = c0 + amp * math.sin(a * fr + ph)
                        if knot:
                            dk = a - knot[0]
                            if abs(dk) < 3.5:
                                push = 1.2 * math.cos(dk / 3.5 * math.pi / 2)
                                yl += push if yl > knot[1] else -push
                        if abs(b + 0.5 - yl) < 0.5:
                            k -= grain * strength
                    if knot:
                        d = math.hypot((a + 0.5 - knot[0]) / 1.5, b + 0.5 - knot[1])
                        if d < 0.75:
                            k -= 0.3
                        elif d < 1.5:
                            k -= 0.1
                    if b == 0:
                        k += 0.07
                    elif b == plank_h - 2:
                        k -= 0.04
                    c = _scale(tone, k)
                    if pegs and joint >= 0 and abs(a - joint) == 2 and b in (1, plank_h - 3) and plank_h >= 4:
                        c = _mix(c, dark, 0.55)
                    c = _jitter(c, rng, 2)
                x, y = (yy, a) if vertical else (a, yy)
                px[u + x, v + y] = c + (255,)


def polished_metal(img, region, stops, rng, fx=0.42, fy=0.33, swirl=1.5, seed=0.0, noise=2):
    """Polished metal (gold, brass, bronze, iron): soft rounded reflections on a continuous colour
    ramp (stops from shadow to highlight), never a regular pattern."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = 0.5 * math.sin(x * fx + math.sin(y * fy * 0.9 + seed) * swirl + seed) + 0.32 * math.cos(y * fy + x * 0.11 + seed * 1.7) \
                + 0.18 * math.sin((x - y) * 0.23 + seed * 0.6)
            px[u + x, v + y] = _jitter(_ramp(stops, 0.5 + 0.5 * t), rng, noise) + (255,)


def hammered_iron(img, region, base, rng, dent=0.07, noise=3):
    """Forged iron: a dark surface with soft hammer dents, lighter where they catch the light."""
    u, v, w, h = region
    px = img.load()
    cells = [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(1.5, 3.2)) for _ in range(max(3, w * h // 18))]
    for y in range(h):
        for x in range(w):
            k = 1.0
            for cx, cy, r in cells:
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                d = math.hypot(dx, dy)
                if d < r:
                    k += dent * (dy / r - dx / r * 0.4) * (1 - d / r)
            if y == 0 or x == 0:
                k += 0.06
            px[u + x, v + y] = _jitter(_scale(base, k), rng, noise) + (255,)


def painted_planks(img, region, paint, seam, plank_h, rng, wood=None, wear=0.05, joints=False):
    """Painted planks: brush strokes along the grain, a lit upper edge, dark seams, a few chips
    where the bare wood shows through."""
    u, v, w, h = region
    px = img.load()
    for r in range(-(-h // plank_h)):
        tone = _jitter(paint, rng, 5)
        strokes = [(rng.uniform(0.06, 0.2), rng.uniform(0, 6.3)) for _ in range(3)]
        joint = rng.randint(5, w - 6) if joints and w > 14 else -99
        for b in range(plank_h):
            yy = r * plank_h + b
            if yy >= h:
                break
            for x in range(w):
                if b == plank_h - 1:
                    c = seam
                elif x == joint:
                    c = _mix(seam, tone, 0.3)
                else:
                    k = 1.0 + sum(0.025 * math.sin(x * f + p + b * 1.3) for f, p in strokes)
                    if b == 0:
                        k += 0.08
                    elif b == plank_h - 2:
                        k -= 0.05
                    c = _scale(tone, k)
                    if wood is not None and rng.random() < wear * (2.2 if b in (0, plank_h - 2) else 0.4):
                        c = wood
                    c = _jitter(c, rng, 2)
                px[u + x, v + yy] = c + (255,)


def woven(img, region, base, rng, k_weave=0.035, folds=None, noise=2):
    """Cloth: a fine two-thread weave; folds=(period, depth) adds soft shading folds along v."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            k = 1.0 + (k_weave if (x + y) % 2 == 0 else -k_weave) * (0.6 if x % 3 else 1.0)
            if folds:
                period, depth = folds
                k += depth * math.sin(2 * math.pi * x / period) - depth * 0.3 * math.sin(4 * math.pi * x / period + 1)
            px[u + x, v + y] = _jitter(_scale(base, k), rng, noise) + (255,)


def twisted_rope(img, region, light, dark, rng):
    """Laid rope: three strands twisting diagonally, each strand lit on one side."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = ((x + y * 1.0) % 4) / 4.0
            c = _ramp([(0.0, dark), (0.3, light), (0.6, _mix(light, dark, 0.35)), (1.0, dark)], t)
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


GOLD_STOPS = [(0.0, (112, 78, 26)), (0.25, (170, 125, 42)), (0.5, (214, 170, 72)), (0.75, (240, 206, 112)),
              (0.92, (252, 236, 170)), (1.0, (255, 248, 214))]


def end_grain(img, region, base, dark, rng):
    """Sawn end of a log: growth rings round a slightly off-centre pith, a few radial checks."""
    u, v, w, h = region
    px = img.load()
    cx, cy = w * 0.47, h * 0.53
    for y in range(h):
        for x in range(w):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(dx, dy) * (1 + 0.06 * math.sin(math.atan2(dy, dx) * 3))
            k = 1.0 + 0.09 * math.sin(r * 2.1)
            c = _scale(base, k)
            if abs(math.sin(math.atan2(dy, dx) * 2.5 + 0.7)) < 0.06 and r > 2:
                c = dark
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def make_texture(path, sail_triangle):
    """sail_triangle: three (fu, fv) points in [0,1] sail-region coordinates."""
    rng = random.Random(1907)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    fine_wood(img, REGIONS["hull_dark"], _rgb("6b4423"), _rgb("3a2312"), 4, rng)
    fine_wood(img, REGIONS["hull_mid"], _rgb("8a5a2b"), _rgb("4a2f18"), 4, rng)
    fine_wood(img, REGIONS["hull_light"], _rgb("b07a3c"), _rgb("6a4520"), 4, rng)
    # red painted strake, a little worn along the seams
    painted_planks(img, REGIONS["red"], _rgb("9e2420"), _rgb("4e1010"), 4, rng, wood=_rgb("7a4f27"), wear=0.012)
    fine_wood(img, REGIONS["deck"], _rgb("a87542"), _rgb("5a3a1c"), 4, rng, knots=0.2)
    fine_wood(img, REGIONS["rail"], _rgb("c08a48"), _rgb("8a5e30"), 8, rng, joints=False, grain=0.08, shade=0.07)
    fine_wood(img, REGIONS["mast"], _rgb("7a4f27"), _rgb("5a3818"), 8, rng, joints=False, knots=0.3, shade=0.07)
    fine_wood(img, REGIONS["oar"], _rgb("a0703a"), _rgb("7a5229"), 8, rng, joints=False, knots=0.1, shade=0.06)
    fine_wood(img, REGIONS["dark_wood"], _rgb("5a3a1c"), _rgb("2e1d0c"), 4, rng)
    polished_metal(img, REGIONS["gold"], GOLD_STOPS, rng)
    hammered_iron(img, REGIONS["iron"], _rgb("3d3d42"), rng)
    end_grain(img, REGIONS["end_grain"], _rgb("94653a"), _rgb("5a3a1c"), rng)
    twisted_rope(img, REGIONS["rope"], _rgb("6a5438"), _rgb("2a2018"), rng)
    px = img.load()

    # canopy cloth: deep red, soft folds between the hoops, a fine weave
    woven(img, REGIONS["canopy"], _rgb("a32520"), rng, folds=(10, 0.07))
    # valance: a gold braid along the top, red cloth with a gold lozenge band, scalloped edge and a fringe
    u, v, w, h = REGIONS["valance"]
    for y in range(h):
        for x in range(w):
            xm = (x % 8) + 0.5
            edge = h - 4 + 3.2 * math.sqrt(max(0.0, 1 - ((xm - 4) / 4.2) ** 2))  # round scallops
            if y >= edge:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            if y < 2:
                c = _ramp(GOLD_STOPS, 0.85 if (x + y) % 3 else 0.45)
            elif y == 2:
                c = _rgb("6e1612")
            else:
                c = _scale(_rgb("b02c26"), 1.0 + (0.03 if (x + y) % 2 else -0.03))
                if abs(abs(xm - 4) + abs(y - 6.5) - 2.2) < 0.55:
                    c = _ramp(GOLD_STOPS, 0.7)  # lozenge embroidered in gold
                if y >= edge - 1.2:
                    c = _ramp(GOLD_STOPS, 0.55 if x % 2 else 0.8)  # gold fringe
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    # flag: red with a gold border and a soft fold
    u, v, w, h = REGIONS["flag"]
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("c4231d"), 1 + 0.06 * math.sin(x * 0.45))
            if y in (0, h - 1):
                c = _ramp(GOLD_STOPS, 0.7)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    # lantern frame and glow
    u, v, w, h = REGIONS["lantern"]
    paint_lamp_glass(px, u, v, w, h)
    u, v, w, h = REGIONS["glow"]
    for y in range(h):
        for x in range(w):
            d = abs(x - w / 2 + 0.5) + abs(y - h / 2 + 0.5)
            c = _rgb("fff1a8") if d < 5 else _rgb("ffc94a")
            px[u + x, v + y] = c + (255,)

    # sail: triangular cloth inside a transparent rectangle; the two free edges (leech and foot)
    # are cut with a slight convex roach, so they curve instead of running ruler-straight
    u, v, w, h = REGIONS["sail"]
    tri = [(p[0] * w, p[1] * h) for p in sail_triangle]
    cxt, cyt = sum(p[0] for p in tri) / 3, sum(p[1] for p in tri) / 3
    poly = []
    for i in range(3):
        (x1, y1), (x2, y2) = tri[i], tri[(i + 1) % 3]
        straight = i == 0  # the head along the yard stays straight
        nx_, ny_ = y2 - y1, -(x2 - x1)
        ln = math.hypot(nx_, ny_)
        nx_, ny_ = nx_ / ln, ny_ / ln
        if nx_ * ((x1 + x2) / 2 - cxt) + ny_ * ((y1 + y2) / 2 - cyt) < 0:
            nx_, ny_ = -nx_, -ny_
        for j in range(24):
            t = j / 24
            bulge = 0.0 if straight else 2.6 * math.sin(math.pi * t)
            poly.append((x1 + (x2 - x1) * t + nx_ * bulge, y1 + (y2 - y1) * t + ny_ * bulge))

    def inside(x, y):
        c = False
        for i in range(len(poly)):
            (x1, y1), (x2, y2) = poly[i], poly[i - 1]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                c = not c
        return c

    def edge_dist(x, y):
        d = 1e9
        for i in range(len(poly)):
            (x1, y1), (x2, y2) = poly[i - 1], poly[i]
            ex, ey = x2 - x1, y2 - y1
            t = max(0.0, min(1.0, ((x - x1) * ex + (y - y1) * ey) / max(1e-9, ex * ex + ey * ey)))
            d = min(d, math.hypot(x - x1 - ex * t, y - y1 - ey * t))
        return d

    reef_rows = (int(h * 0.28), int(h * 0.48))
    for y in range(h):
        for x in range(w):
            if not inside(x + 0.5, y + 0.5):
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            ed = edge_dist(x + 0.5, y + 0.5)
            # cream canvas, light in the belly and shade towards the edges
            k = 1.0 - 0.06 * abs(y / h - 0.45)
            k -= 0.07 * max(0.0, 1.0 - ed / 16.0)
            c = _scale((243, 234, 214), k)
            if x % 12 == 11:
                c = _scale(c, 0.86)
            elif x % 12 == 0 and y % 3 == 1:
                c = _scale(c, 0.93)  # stitching of the seam
            for ry_ in reef_rows:  # reef bands: a doubled strip and its row of reef points
                if ry_ <= y <= ry_ + 1:
                    c = _scale(c, 0.9 if y == ry_ else 0.95)
                if x % 7 == 3 and ry_ + 2 <= y <= ry_ + 3:
                    c = _rgb("8a6a3a") if y == ry_ + 2 else _rgb("a8875a")
            # reinforcing patches at the three corners
            dc = min(math.hypot(x + 0.5 - qx, y + 0.5 - qy) for qx, qy in tri)
            if dc < 9:
                c = _scale(c, 0.95)
                if 8.2 < dc < 9:
                    c = _scale(c, 0.88)
            if ed < 1.6:
                c = _rgb("b89a62") if ed < 0.9 else _rgb("c8ad7a")  # bolt rope
            if y < 2:
                c = _rgb("b89a62")  # reinforced head along the yard
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)
    import interior_texture
    interior_texture.paint(px, REGIONS)
    img.save(path)
    return img


def paint_lamp_glass(px, u, v, w, h):
    """Lantern glass: thin dark iron frame and a glazing bar, warm light brighter round the flame
    (shared by every ship: the lanterns are drawn full bright, see tools/lanterns.py)."""
    for y in range(h):
        for x in range(w):
            if x in (0, w - 1) or y in (0, h - 1):
                c = (42, 44, 48)
            elif x == w // 2:
                c = (58, 60, 64)
            else:
                d = ((x - w / 2 + 0.5) ** 2 + ((y - h * 0.55) * 0.8) ** 2) ** 0.5
                c = (255, 246, 200) if d < 2.6 else (255, 215, 122) if d < 4.6 else (242, 172, 68) if d < 6.4 else (217, 138, 44)
            px[u + x, v + y] = c + (255,)
