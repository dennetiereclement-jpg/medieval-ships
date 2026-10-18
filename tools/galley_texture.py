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


def make_texture(path, sail_triangle):
    """sail_triangle: three (fu, fv) points in [0,1] sail-region coordinates."""
    rng = random.Random(1907)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    _planks(img, REGIONS["hull_dark"], _rgb("6b4423"), _rgb("3e2614"), 4, rng)
    _planks(img, REGIONS["hull_mid"], _rgb("8a5a2b"), _rgb("4e321a"), 4, rng)
    _planks(img, REGIONS["hull_light"], _rgb("b07a3c"), _rgb("6e4a22"), 4, rng)
    _planks(img, REGIONS["red"], _rgb("9b2220"), _rgb("5e1212"), 4, rng, joints=False)
    _planks(img, REGIONS["deck"], _rgb("a87542"), _rgb("5c3c1e"), 4, rng)
    _planks(img, REGIONS["rail"], _rgb("c08a48"), _rgb("7a5229"), 8, rng, joints=False)
    _planks(img, REGIONS["mast"], _rgb("7a4f27"), _rgb("4a2e15"), 8, rng, joints=False)
    _planks(img, REGIONS["oar"], _rgb("a0703a"), _rgb("6a4520"), 8, rng, joints=False)
    _planks(img, REGIONS["dark_wood"], _rgb("5a3a1c"), _rgb("33200e"), 4, rng)
    # polished gilding: soft rounded reflections
    u, v, w, h = REGIONS["gold"]
    gpx = img.load()
    for y in range(h):
        for x in range(w):
            t = 0.55 * math.sin(x * 0.42 + math.sin(y * 0.3) * 1.5) + 0.45 * math.cos(y * 0.36 + x * 0.12)
            c = _rgb("fbe7a1") if t > 0.62 else _rgb("e6bf5a") if t > 0.2 else _rgb("cfa23f") if t > -0.35 else _rgb("a97f2a")
            gpx[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    _fill(img, REGIONS["iron"], _rgb("3b3b3f"), rng, 8)
    _fill(img, REGIONS["end_grain"], _rgb("8c5e30"), rng, 10)

    # rope: twisted strands
    u, v, w, h = REGIONS["rope"]
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = _rgb("4a3a2a") if (x + y) % 3 else _rgb("2a2018")
            px[u + x, v + y] = c + (255,)

    # canopy cloth: red with folds
    u, v, w, h = REGIONS["canopy"]
    for y in range(h):
        for x in range(w):
            c = _rgb("a8261f") if (x // 4) % 2 == 0 else _rgb("8c1d18")
            px[u + x, v + y] = _jitter(c, rng, 6) + (255,)
    # valance with scalloped lower edge
    u, v, w, h = REGIONS["valance"]
    for y in range(h):
        for x in range(w):
            edge = h - 4 + (2 if (x % 8) in (0, 1, 6, 7) else 0)
            if y < edge:
                c = _rgb("b3302a") if y > 2 else _rgb("d8b25a")
                px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    # flag
    u, v, w, h = REGIONS["flag"]
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = _jitter(_rgb("c4231d"), rng, 10) + (255,)
    # lantern frame and glow
    u, v, w, h = REGIONS["lantern"]
    paint_lamp_glass(px, u, v, w, h)
    u, v, w, h = REGIONS["glow"]
    for y in range(h):
        for x in range(w):
            d = abs(x - w / 2 + 0.5) + abs(y - h / 2 + 0.5)
            c = _rgb("fff1a8") if d < 5 else _rgb("ffc94a")
            px[u + x, v + y] = c + (255,)

    # sail: triangular cloth inside a transparent rectangle
    u, v, w, h = REGIONS["sail"]
    (au, av), (bu, bv), (cu, cv) = [(p[0] * w, p[1] * h) for p in sail_triangle]

    def inside(x, y):
        def side(x1, y1, x2, y2):
            return (x - x2) * (y1 - y2) - (x1 - x2) * (y - y2)
        d1 = side(au, av, bu, bv)
        d2 = side(bu, bv, cu, cv)
        d3 = side(cu, cv, au, av)
        neg = d1 < 0 or d2 < 0 or d3 < 0
        pos = d1 > 0 or d2 > 0 or d3 > 0
        return not (neg and pos)

    tri = ((au, av), (bu, bv), (cu, cv))

    def edge_dist(x, y):
        d = 1e9
        for i in range(3):
            (x1, y1), (x2, y2) = tri[i], tri[(i + 1) % 3]
            ex, ey = x2 - x1, y2 - y1
            t = max(0.0, min(1.0, ((x - x1) * ex + (y - y1) * ey) / (ex * ex + ey * ey)))
            d = min(d, math.hypot(x - x1 - ex * t, y - y1 - ey * t))
        return d

    cloth = _rgb("efe6d2")
    for y in range(h):
        for x in range(w):
            if inside(x + 0.5, y + 0.5):
                # clean cream canvas: cloths sewn across the yard, soft light in the belly
                k = 1.0 - 0.07 * abs(y / h - 0.45) - (0.03 if (x * 7 + y * 3) % 17 == 0 else 0)
                # light in the belly, shade towards the edges of the triangle
                k -= 0.08 * max(0.0, 1.0 - edge_dist(x + 0.5, y + 0.5) / 18.0)
                c = tuple(int(b * k) for b in (243, 234, 214))
                if x % 12 == 11:
                    c = tuple(int(b * 0.85) for b in c)
                elif x % 12 == 0 and y % 3 == 1:
                    c = tuple(int(b * 0.93) for b in c)  # stitching of the seam
                if edge_dist(x + 0.5, y + 0.5) < 1.5:
                    c = _rgb("c8ad7a")  # bolt rope
                if y < 2:
                    c = _rgb("b89a62")  # reinforced head along the yard
                px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
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
