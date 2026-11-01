"""Texture of the trade sloop (trade_sloop).

  trade_sloop.png   512x512 atlas, regions in REGIONS (u, v, w, h)

Colours from the reference picture: dark tarred planking below, a wide band of bright blue painted
strakes along the sides crossed by brown frames, a honey wood wale and cap rail, a pale deck, spar
wood, two light beige sails with plain seams and bolt ropes (no emblem: a modest merchant).
"""
import math
import random

from PIL import Image

from elven_texture import _curved_outline, _poly_dist, _poly_inside
from galley_texture import (_jitter, _mix, _ramp, _rgb, _scale, end_grain, fine_wood, hammered_iron, paint_lamp_glass,
                            painted_planks, polished_metal, twisted_rope, woven)

SIZE = 512

REGIONS = {
    "hull_dark":  (0, 0, 64, 32),
    "hull_blue":  (64, 0, 64, 32),
    "hull_wale":  (128, 0, 64, 32),
    "hull_light": (192, 0, 64, 32),
    "rail":       (256, 0, 64, 16),
    "frame":      (256, 16, 32, 16),
    "truck":      (288, 16, 16, 16),
    "glow":       (304, 16, 16, 16),
    "deck":       (320, 0, 64, 64),
    "mast":       (384, 0, 64, 16),
    "dark_wood":  (384, 16, 32, 16),
    "rope":       (416, 16, 16, 16),
    "lantern":    (432, 16, 16, 16),
    "gold":       (448, 16, 16, 16),
    "iron":       (464, 16, 16, 16),
    "end_grain":  (480, 16, 16, 16),
    "cloth_roll": (384, 32, 64, 16),
    "grating":    (384, 48, 64, 16),
    "canvas":     (448, 32, 64, 32),
    "sail_main":  (0, 128, 256, 256),
    "sail_jib":   (256, 128, 256, 256),
}

BEIGE = _rgb("f2e0b6")
SEAM = _rgb("d4bf92")
BOLT = _rgb("7a5a32")
BLUE = _rgb("2f6fc6")
BLUE_DARK = _rgb("1b4a8c")
BRASS = [(0.0, (92, 66, 22)), (0.3, (160, 120, 44)), (0.55, (214, 170, 74)), (0.8, (244, 214, 130)), (1.0, (255, 240, 190))]


def _cloth(x, y, w, h, rng, d_edge, seam_x):
    """Colour of a point of the cloth: soft shading towards the edges, a seam every `seam_x` pixels."""
    k = 1.0 - 0.06 * max(0.0, 1.0 - d_edge / (0.1 * min(w, h))) - 0.015 * math.sin(x * 0.11) - 0.012 * math.sin(y * 0.07)
    c = _scale(BEIGE, k)
    if x % seam_x == 0:
        c = SEAM
    elif x % seam_x == 1 and rng.random() < 0.5:
        c = _mix(c, SEAM, 0.4)
    return c


def _paint_quad_sail(px, region, rng, hollow=0.025, seam_x=26):
    """Four sided sail mapped bilinearly on its region: u = 0 luff (mast) .. 1 leech, v = 0 head (gaff)
    .. 1 foot (boom). The leech is cut with a gentle hollow (a curved outline), bolt rope all round,
    reinforcing patches at the four corners, a row of reef points above the foot."""
    u, v, w, h = region
    corners = [(0, 0), (w, 0), (w, h), (0, h)]
    for y in range(h):
        t = (y + 0.5) / h
        x_leech = w - hollow * w * math.sin(math.pi * t)
        for x in range(w):
            if x + 0.5 > x_leech:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            d = min(x + 0.5, y + 0.5, h - y - 0.5, x_leech - x - 0.5)
            c = _cloth(x, y, w, h, rng, d, seam_x)
            dc = min(math.hypot(x + 0.5 - cx, y + 0.5 - cy) for cx, cy in corners)
            if dc < w * 0.09:
                c = _scale(c, 0.94)
                if dc > w * 0.09 - 1.3 and (x + y) % 2 == 0:
                    c = _rgb("b8a070")
            # reef band: a line of short dark ties two thirds of the way down
            if abs(y - h * 0.72) < 0.6 and (x // 10) % 2 == 0 and 4 < x < x_leech - 4:
                c = _rgb("8a7048")
            if d < 1.3:
                c = BOLT
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _paint_tri_sail(px, region, tri_unit, rng, seam_x=24):
    """Triangular sail (the jib): the luff straight on its stay, the leech and the foot bowing outwards a
    little, bolt rope, patches at the three corners, seams parallel to the leech."""
    u, v, w, h = region
    tri = [(p[0] * w, p[1] * h) for p in tri_unit]
    size = min(w, h)
    poly = _curved_outline(tri, size * 0.028)
    head, tack, clew = tri
    # seams parallel to the leech (clew - head): distance from the leech line
    lx, ly = clew[0] - head[0], clew[1] - head[1]
    ln = math.hypot(lx, ly)
    nx, ny = -ly / ln, lx / ln
    for y in range(h):
        for x in range(w):
            if not _poly_inside(poly, x + 0.5, y + 0.5):
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            d = _poly_dist(poly, x + 0.5, y + 0.5)
            k = 1.0 - 0.06 * max(0.0, 1.0 - d / (size * 0.1)) - 0.015 * math.sin(x * 0.1) - 0.012 * math.sin(y * 0.08)
            c = _scale(BEIGE, k)
            s = (x + 0.5 - head[0]) * nx + (y + 0.5 - head[1]) * ny
            if int(math.floor(s)) % seam_x == 0:
                c = SEAM
            dc = min(math.hypot(x + 0.5 - qx, y + 0.5 - qy) for qx, qy in tri)
            if dc < size * 0.1:
                c = _scale(c, 0.94)
                if dc > size * 0.1 - 1.3 and (x + y) % 2 == 0:
                    c = _rgb("b8a070")
            if d < 1.3:
                c = BOLT
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def make_texture(path, tris):
    """tris: name -> triangle of the jib in [0,1] region coordinates (from the generator)."""
    rng = random.Random(1721)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    def reg(name):
        return REGIONS[name]
    # tarred dark planking below the blue band; honey wale and light inner planking
    fine_wood(img, reg("hull_dark"), _rgb("5a3b22"), _rgb("2e1c0c"), 8, rng, knots=0.1, grain=0.1, shade=0.07)
    fine_wood(img, reg("hull_wale"), _rgb("8c5e32"), _rgb("4d3016"), 8, rng, knots=0.1, grain=0.1)
    fine_wood(img, reg("hull_light"), _rgb("c9a064"), _rgb("8a6436"), 8, rng, knots=0.08, grain=0.09)
    fine_wood(img, reg("rail"), _rgb("b88a4c"), _rgb("775426"), 8, rng, knots=0.05, grain=0.08, shade=0.04)
    fine_wood(img, reg("frame"), _rgb("5e3d20"), _rgb("30200c"), 16, rng, joints=False, knots=0.0, grain=0.08, vertical=True)
    fine_wood(img, reg("deck"), _rgb("c8a46a"), _rgb("95703f"), 8, rng, knots=0.1, grain=0.09)
    fine_wood(img, reg("mast"), _rgb("b58a4e"), _rgb("7d5a2c"), 8, rng, joints=False, knots=0.08, grain=0.08, shade=0.06, vertical=True)
    fine_wood(img, reg("dark_wood"), _rgb("7a5530"), _rgb("45290f"), 4, rng)
    # the blue strakes: bright blue paint over the planks, dark seams, a few chips showing the wood
    painted_planks(img, reg("hull_blue"), BLUE, BLUE_DARK, 8, rng, wood=_rgb("6a4a28"), wear=0.06, joints=True)
    px = img.load()
    u, v, w, h = reg("hull_blue")
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[u + x, v + y]
            # the paint is glossy: a lighter streak on the upper part of each plank
            if y % 8 in (1, 2):
                r, g, b = _mix((r, g, b), _rgb("6b9ee0"), 0.22)
            px[u + x, v + y] = (r, g, b, a)
    polished_metal(img, reg("gold"), BRASS, rng, fx=0.4, fy=0.3, swirl=1.4)
    hammered_iron(img, reg("iron"), _rgb("4a4c52"), rng)
    end_grain(img, reg("end_grain"), _rgb("b08a52"), _rgb("6a4a24"), rng)
    twisted_rope(img, reg("rope"), _rgb("d2bc8e"), _rgb("8f7a52"), rng)
    woven(img, reg("canvas"), _rgb("d9c9a4"), rng, k_weave=0.03, folds=(16, 0.07))
    u, v, w, h = reg("lantern")
    paint_lamp_glass(px, u, v, w, h)
    u, v, w, h = reg("glow")
    for y in range(h):
        for x in range(w):
            d = abs(x - w / 2 + 0.5) + abs(y - h / 2 + 0.5)
            px[u + x, v + y] = (_rgb("fff6c8") if d < 5 else _rgb("ffd76a")) + (255,)
    # pale painted truck of the mast head
    u, v, w, h = reg("truck")
    for y in range(h):
        for x in range(w):
            c = _rgb("efe6cf") if y % 8 else _rgb("c9bda0")
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    # furled cloth: beige with the gaskets
    u, v, w, h = reg("cloth_roll")
    for y in range(h):
        for x in range(w):
            c = BEIGE if (x + y // 2) % 5 else _rgb("d4c6a2")
            if x % 16 in (7, 8):
                c = _rgb("9a8458")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    # hatch grating: a wooden lattice over dark openings
    u, v, w, h = reg("grating")
    for y in range(h):
        for x in range(w):
            bar = x % 4 == 0 or y % 4 == 0
            c = _jitter(_rgb("a07a46") if (x % 4 == 0) else _rgb("8c6a3c"), rng, 6) if bar else _rgb("241608")
            px[u + x, v + y] = c + (255,)
    _paint_quad_sail(px, reg("sail_main"), rng)
    _paint_tri_sail(px, reg("sail_jib"), tris["sail_jib"], rng)
    img.save(path)


def make_item_icon(path):
    """16x16 inventory icon: brown hull with its blue band, a beige gaff mainsail and jib."""
    icon = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = icon.load()
    for x in range(2, 15):
        lift = 2 if x > 12 else (1 if x < 4 else 0)
        for y in range(11 - lift, 15):
            c = BLUE if y == 12 - lift or y == 13 - lift else (_rgb("8c5e32") if y < 12 - lift else _rgb("5a3b22"))
            p[x, y] = c + (255,)
        p[x, 11 - lift] = _rgb("c9a064") + (255,)
    p[15, 8] = _rgb("b58a4e") + (255,)
    p[14, 9] = _rgb("b58a4e") + (255,)
    for y in range(1, 11):
        p[8, y] = _rgb("b58a4e") + (255,)
    for y in range(2, 10):
        # jib forward (right), gaff mainsail aft (left)
        for x in range(9, 15):
            if x <= 9 + (y - 1) * 0.7:
                p[x, y] = BEIGE + (255,)
        for x in range(2, 8):
            if x >= 7 - (y - 1) * 0.75 and y >= 2:
                p[x, y] = BEIGE + (255,)
    p[7, 2] = SEAM + (255,)
    icon.save(path)
