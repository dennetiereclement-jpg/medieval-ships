"""Texture of the steampunk airship (steampunk_airship).

  steampunk_airship.png   256x256 atlas, regions in REGIONS (u, v, w, h)

Colours of the reference picture: a cream balloon in stitched panels with a blue-grey nose cap and
blue-grey bands, a brown rope net (transparent between the cords), orange braided rope hoops and
suspension lines with gold clasps and rings, triangular cream fins on wooden spars, a wooden
propeller with a brass hub, a dark brown wooden gondola with brass fittings and an iron engine.
"""
import math
import random

from PIL import Image, ImageDraw

from galley_texture import _fill, _jitter, _planks, _rgb, paint_lamp_glass

SIZE = 256

REGIONS = {
    "balloon":     (0, 0, 32, 32),
    "balloon_blue": (32, 0, 32, 32),
    "band":        (64, 0, 32, 16),
    "net":         (96, 0, 32, 32),
    "rope":        (128, 0, 16, 16),
    "gold":        (144, 0, 16, 16),
    "brass":       (160, 0, 32, 32),
    "iron":        (192, 0, 16, 16),
    "copper":      (208, 0, 16, 16),
    "lantern":     (224, 0, 16, 16),
    "glow":        (240, 0, 16, 16),
    "hull":        (0, 32, 64, 32),
    "hull_light":  (64, 32, 64, 16),
    "deck":        (64, 48, 64, 32),
    "dark_wood":   (128, 32, 32, 16),
    "wood":        (128, 48, 64, 16),
    "end_grain":   (160, 32, 16, 16),
    "boiler":      (192, 32, 64, 32),
    "prop":        (0, 64, 64, 16),
    "balloon_in":  (176, 32, 16, 16),
    "fin":         (0, 96, 96, 96),
}

CREAM = _rgb("e9d6ad")
CREAM_DARK = _rgb("c4ac80")
BLUE = _rgb("5e7088")
BLUE_DARK = _rgb("3f4d61")
ROPE = _rgb("b46e33")
ROPE_DARK = _rgb("7a4520")


def _shade(c, k):
    return tuple(max(0, min(255, int(q * k))) for q in c)


def _metal(px, region, shades, rng):
    """Polished metal with soft rounded reflections."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            t = 0.55 * math.sin(x * 0.42 + math.sin(y * 0.3) * 1.5) + 0.45 * math.cos(y * 0.36 + x * 0.12)
            i = 0 if t > 0.65 else 1 if t > 0.2 else 2 if t > -0.35 else 3 if t > -0.75 else 4
            px[u + x, v + y] = _jitter(_rgb(shades[i]), rng, 3) + (255,)


def _panel(px, region, base, seam, rng, weave=0.035):
    """Balloon panel (each panel strip shows the whole region): fabric weave, slight shading,
    stitched seams along both long edges."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            # the cloth bulges between the seams: lighter in the middle of the gore, darker at its edges
            k = 1.0 - weave * ((x + 2 * y) % 3 == 0) - 0.14 * (2 * abs((y + 0.5) / h - 0.5)) ** 2
            c = _shade(base, k)
            if y in (0, h - 1):
                c = seam
            elif y in (1, h - 2) and x % 3 == 1:
                c = _shade(seam, 1.12)   # stitching
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _fin_shape(fin_tri, fin_curve, w, h):
    """(inside, edge distance in pixels) of a fin texture pixel. fin_curve = (C, A, B, curves) from the
    generator: tip, roots and the hollowed edges (start, edge vector, inward normal, sag) in 3D; the
    region maps C + (A - C) u + Vp v (Vp: part of B - C normal to the luff)."""
    def dot(a, b):
        return sum(x * y for x, y in zip(a, b))

    def sub(a, b):
        return [x - y for x, y in zip(a, b)]
    C, A, B, curves = fin_curve
    U = sub(A, C)
    L = math.sqrt(dot(U, U))
    Un = [x / L for x in U]
    BC = sub(B, C)
    Vp = [b - dot(BC, Un) * u for b, u in zip(BC, Un)]
    px_per_block = w / L

    def point(x, y):
        u, v = x / w, y / h
        return [c + uu * u + vv * v for c, uu, vv in zip(C, U, Vp)]
    AB = sub(B, A)
    ab2 = dot(AB, AB)
    # inward normal of the root edge, in the fin plane
    mid = [(a + b) / 2 for a, b in zip(A, B)]
    to_c = sub(C, mid)
    root_in = [c - dot(to_c, AB) / ab2 * e for c, e in zip(to_c, AB)]
    rl = math.sqrt(dot(root_in, root_in))
    root_in = [x / rl for x in root_in]

    def shape(x, y):
        X = point(x, y)
        dmin = dot(sub(X, A), root_in)
        if dmin < 0:
            return False, 0.0
        for E0, e, inward, sag in curves:
            e2 = dot(e, e)
            t = dot(sub(X, E0), e) / e2
            sig = dot(sub(X, E0), inward)
            tt = max(0.0, min(1.0, t))
            d = sig - sag * math.sin(math.pi * tt)
            if d < 0:
                return False, 0.0
            dmin = min(dmin, d)
        return True, dmin * px_per_block
    return shape


def make_texture(path, fin_tri, fin_curve=None):
    """fin_tri: triangle of the fins in [0, 1] region coordinates (from the generator); fin_curve: its
    curved edges (see _fin_shape)."""
    rng = random.Random(1852)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()

    def reg(name):
        return REGIONS[name]

    _panel(px, reg("balloon"), CREAM, CREAM_DARK, rng)
    _panel(px, reg("balloon_blue"), BLUE, BLUE_DARK, rng)
    _fill(img, reg("balloon_in"), _rgb("b8a780"), rng, 6)
    # blue-grey band: stitched edges and a row of brass eyelets
    u, v, w, h = reg("band")
    for y in range(h):
        for x in range(w):
            c = BLUE
            if y in (0, h - 1):
                c = BLUE_DARK
            elif y == h // 2 and x % 8 == 4:
                c = _rgb("d8b25a")
            elif y in (2, h - 3) and x % 3 == 0:
                c = _shade(BLUE, 1.18)
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    # rope net: two diamonds per tile, transparent between the cords, knots where they cross
    u, v, w, h = reg("net")
    for y in range(h):
        for x in range(w):
            a = (x + y) % 16
            b = (x - y) % 16
            on = a == 0 or b == 0
            if on:
                c = ROPE_DARK if a == 0 and b == 0 else _rgb("8c5a30")
                px[u + x, v + y] = _jitter(c, rng, 6) + (255,)
            else:
                px[u + x, v + y] = (0, 0, 0, 0)
    # braided rope
    u, v, w, h = reg("rope")
    for y in range(h):
        for x in range(w):
            c = ROPE if (x + y) % 4 < 2 else ROPE_DARK
            if (x - y) % 4 == 0:
                c = _shade(ROPE, 1.15)
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    _metal(px, reg("gold"), ("fbe7a1", "e6bf5a", "cfa23f", "a97f2a", "7c5a1c"), rng)
    _metal(px, reg("brass"), ("f6dc93", "dcb055", "bf8f34", "906523", "684716"), rng)
    _metal(px, reg("copper"), ("f0b08a", "d08a54", "a8643a", "7e4526", "5a2e18"), rng)
    _fill(img, reg("iron"), _rgb("3a3c40"), rng, 6)
    u, v, w, h = reg("lantern")
    paint_lamp_glass(px, u, v, w, h)
    u, v, w, h = reg("glow")
    for y in range(h):
        for x in range(w):
            d = abs(x - w / 2 + 0.5) + abs(y - h / 2 + 0.5)
            px[u + x, v + y] = (_rgb("fff1a8") if d < 5 else _rgb("ffc94a")) + (255,)
    # wood
    _planks(img, reg("hull"), _rgb("6a4527"), _rgb("2e1d10"), 4, rng)
    _planks(img, reg("hull_light"), _rgb("7a5232"), _rgb("4a301a"), 4, rng)
    _planks(img, reg("deck"), _rgb("8a6644"), _rgb("4e3820"), 4, rng)
    _planks(img, reg("dark_wood"), _rgb("4a301a"), _rgb("281809"), 4, rng)
    _planks(img, reg("wood"), _rgb("b38a58"), _rgb("7a5a34"), 8, rng, joints=False)
    _fill(img, reg("end_grain"), _rgb("8c5e30"), rng, 10)
    _planks(img, reg("prop"), _rgb("8e6038"), _rgb("5a3a1e"), 8, rng, joints=False)
    # boiler: riveted iron plates with a brass band
    u, v, w, h = reg("boiler")
    for y in range(h):
        for x in range(w):
            c = _jitter(_rgb("45484d"), rng, 5)
            if x % 16 == 0 or y % 16 == 0:
                c = _rgb("26282b")
            elif (x % 16 in (2, 13)) and y % 4 == 2:
                c = _rgb("8d9399")
            if 12 <= y <= 15:
                c = _jitter(_rgb("c99a3e"), rng, 6)
            px[u + x, v + y] = c + (255,)
    # fins: cream canvas with a brown bolt rope and seams parallel to the leading edge,
    # transparent outside the triangle
    u, v, w, h = reg("fin")
    tri = [(p[0] * w, p[1] * h) for p in fin_tri]

    def inside(x, y):
        (ax, ay), (bx, by), (cx, cy) = tri

        def side(x1, y1, x2, y2):
            return (x - x2) * (y1 - y2) - (x1 - x2) * (y - y2)
        d1, d2, d3 = side(ax, ay, bx, by), side(bx, by, cx, cy), side(cx, cy, ax, ay)
        return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))

    def edge_dist(x, y):
        d = 1e9
        for i in range(3):
            (x1, y1), (x2, y2) = tri[i], tri[(i + 1) % 3]
            ex, ey = x2 - x1, y2 - y1
            L2 = ex * ex + ey * ey
            t = max(0.0, min(1.0, ((x - x1) * ex + (y - y1) * ey) / L2))
            d = min(d, math.hypot(x - x1 - ex * t, y - y1 - ey * t))
        return d
    shape = _fin_shape(fin_tri, fin_curve, w, h) if fin_curve is not None else None
    for y in range(h):
        for x in range(w):
            if shape is not None:
                ok, d = shape(x + 0.5, y + 0.5)
            else:
                ok = inside(x + 0.5, y + 0.5)
                d = edge_dist(x + 0.5, y + 0.5) if ok else 0.0
            if not ok:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            # canvas: fine weave, a soft shade between the seams that run parallel to the root
            c = _shade(_rgb("efdcae"), 1.0 - 0.04 * ((x * 3 + y) % 7 == 0) - 0.05 * (0.5 - 0.5 * math.cos(2 * math.pi * y / 12)))
            if y % 12 == 0:
                c = _shade(c, 0.86)
            if d < 1.6:
                c = _rgb("6e4a2a")
            elif d < 3.0:
                c = _rgb("d4c296")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    img.save(path)


def make_item_icon(path):
    """16x16 inventory icon: cream balloon with a blue nose, net lines, fin, gondola below."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((2, 2, 14, 9), fill=CREAM + (255,), outline=_rgb("8c6a40") + (255,))
    d.pieslice((9, 2, 15, 9), -90, 90, fill=BLUE + (255,))
    for x in (5, 8, 11):
        d.line((x, 3, x, 8), fill=ROPE + (255,))
    d.line((3, 5, 13, 5), fill=BLUE_DARK + (255,))
    d.polygon([(2, 4), (0, 1), (3, 3)], fill=_rgb("efe2bf") + (255,))
    d.line((0, 6, 2, 6), fill=_rgb("7a5232") + (255,))
    d.line((6, 9, 5, 12), fill=ROPE + (255,))
    d.line((10, 9, 11, 12), fill=ROPE + (255,))
    d.polygon([(3, 12), (13, 12), (12, 14), (4, 14)], fill=_rgb("5a3a22") + (255,))
    d.line((3, 12, 13, 12), fill=_rgb("d8b25a") + (255,))
    img.save(path)
