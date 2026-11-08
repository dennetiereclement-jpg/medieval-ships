"""Shared helpers of the market tents of group B (1.26.0): tente_lion_drapee, tente_lion_chapiteau, tente_balance_bleue.

The three Lion Port tents are royal blue and cream with warm orange gold: the same one-block prop chain as the merchant
tents (tools/merchant/merchantlib.py: setup, Atlas, export, the shell regions, props) without modifying it; this module
adds the group's own painters (pixel-art lion rampant and balance scales emblems, blue/cream striped cloth with soft
folds, dagged and crenellated gold valances, banners, flags, rugs, curtains, warm wood, stone feet, iron bands) and
geometry helpers (squared posts on stone feet, concave hipped roofs, valances, tied-back drapes, rope swags, lanterns on
iron brackets, an iron-banded chest, big sacks, scrolls, an armillary sphere, potion shelves, planters, the gallows
sign). Every function takes tent-local coordinates (blocks, y up, +z = the open front, the anchor block at (0, 0, 0)).

Each generator calls add_regions(atlas, names) with the regions it uses (REGIONS below, plus the props_m1 regions
listed in M1_REGIONS for flowers, herbs, potions and books), before building.
"""
import bisect
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, ".."))
for p in (os.path.join(TOOLS, "merchant"), os.path.join(TOOLS, "tents"), os.path.join(TOOLS, "workshops"), TOOLS):
    if p not in sys.path:
        sys.path.insert(0, p)
import merchantlib as ml  # noqa: E402
import props_m1 as p1  # noqa: E402
import wslib_b as wb  # noqa: E402

v3, norm, add_cube, beam, loft, Bone = ml.v3, ml.norm, ml.add_cube, ml.beam, ml.loft, ml.Bone
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ry, rx, rz = ml.ry, ml.rx, ml.rz
box, collide = ml.box, ml.collide
_rgb, _jitter, _scale, _mix = ml._rgb, ml._jitter, ml._scale, ml._mix

# ---------------------------------------------------------------- the pictures' palette (Lion Port blue, cream, orange gold)
NAVY, NAVY_D, NAVY_L = _rgb("323c82"), _rgb("1a1f4c"), _rgb("4a58a8")
CREAM, CREAM_D, CREAM_L = _rgb("f0dcc0"), _rgb("c8ae8a"), _rgb("fbecd6")
GOLD, GOLD_D, GOLD_L = _rgb("eea42c"), _rgb("8e520e"), _rgb("ffd877")
WOOD, WOOD_D = _rgb("a8703c"), _rgb("5e3a1c")
WOOD_DARK, WOOD_DARK_D = _rgb("6e4424"), _rgb("2e1a0c")


# ================================================================ painting helpers
def weave(img, c, rng, stains=1, box_=None):
    """A woven cloth fill of colour c (merchantlib/tent_texture weave) over the image (or box_ x, y, w, h)."""
    w, h = img.size
    ml._weave(img, box_ or (0, 0, w, h), c, rng, stains=stains)


def _mask(w, h, draw_fn, S=8):
    """Coverage mask (w x h floats 0..1) of the shapes draw_fn(draw, W, H) paints white at S x resolution."""
    from PIL import Image, ImageDraw
    big = Image.new("L", (w * S, h * S), 0)
    draw_fn(ImageDraw.Draw(big), w * S, h * S)
    a = np.asarray(big, dtype=float).reshape(h, S, w, S).mean(axis=(1, 3)) / 255.0
    return a


def stamp(img, mask, fill, outline=None, light=None, x0=0, y0=0, thr=0.42, shade=None):
    """Pixel-art stamp of a coverage mask on img at (x0, y0): fill where covered, a 1 px outline round it, a light
    edge on the upper-left inner pixels, a darker shade on the lower-right inner pixels."""
    px = img.load()
    h, w = mask.shape
    on = mask > thr
    W, H = img.size

    def inside(i, j):
        return 0 <= i < w and 0 <= j < h and on[j, i]
    for j in range(h):
        for i in range(w):
            X_, Y_ = x0 + i, y0 + j
            if not (0 <= X_ < W and 0 <= Y_ < H):
                continue
            if on[j, i]:
                c = fill
                if light is not None and (not inside(i - 1, j) or not inside(i, j - 1)):
                    c = light
                elif shade is not None and (not inside(i + 1, j) or not inside(i, j + 1)):
                    c = shade
                px[X_, Y_] = tuple(int(k) for k in c[:3]) + (255,)
            elif outline is not None and (inside(i - 1, j) or inside(i + 1, j) or inside(i, j - 1) or inside(i, j + 1)):
                px[X_, Y_] = tuple(int(k) for k in outline[:3]) + (255,)


def _lion_parts(facing=-1):
    """The heraldic lion rampant (looking left: head up, fore paws raised, tail curled up behind) as layered parts,
    back to front: each part is (draw(d, P, W), shade) drawn and stamped in turn so that its outline separates it
    from the parts behind it."""
    def poly(d, P, pts):
        d.polygon([P(*q) for q in pts], fill=255)

    def line(d, P, W, pts, w):
        d.line([P(*q) for q in pts], fill=255, width=max(1, int(w * W)), joint="curve")
        for q in pts:
            r = w * W / 2
            c = P(*q)
            d.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=255)

    def ell(d, P, x0, y0, x1, y1):
        a, b = P(x0, y0), P(x1, y1)
        d.ellipse((min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])), fill=255)

    def tail(d, P, W):
        line(d, P, W, [(0.70, 0.62), (0.84, 0.56), (0.88, 0.40), (0.82, 0.26)], 0.05)
        poly(d, P, [(0.76, 0.28), (0.80, 0.12), (0.85, 0.20), (0.92, 0.14), (0.90, 0.28), (0.82, 0.32)])

    def far_hind(d, P, W):
        line(d, P, W, [(0.66, 0.68), (0.74, 0.82), (0.68, 0.92)], 0.08)
        poly(d, P, [(0.58, 0.90), (0.72, 0.88), (0.73, 0.96), (0.58, 0.97)])

    def far_fore(d, P, W):
        line(d, P, W, [(0.46, 0.44), (0.32, 0.47), (0.20, 0.42)], 0.07)
        poly(d, P, [(0.12, 0.38), (0.22, 0.37), (0.23, 0.45), (0.12, 0.46)])

    def body(d, P, W):
        poly(d, P, [(0.42, 0.30), (0.56, 0.26), (0.66, 0.44), (0.72, 0.62), (0.62, 0.74), (0.50, 0.66), (0.42, 0.48)])
        ell(d, P, 0.52, 0.52, 0.76, 0.76)

    def near_hind(d, P, W):
        line(d, P, W, [(0.58, 0.66), (0.46, 0.78), (0.34, 0.86)], 0.09)
        poly(d, P, [(0.24, 0.84), (0.36, 0.82), (0.38, 0.91), (0.24, 0.92)])

    def mane(d, P, W):
        pts = []
        for k in range(11):
            a = math.pi * (-0.55 + 1.25 * k / 10)
            r = 0.17 if k % 2 == 0 else 0.13
            pts.append((0.47 + r * math.cos(a), 0.20 + r * math.sin(a) * 1.05))
        pts.append((0.40, 0.36))
        poly(d, P, pts)

    def head(d, P, W):
        ell(d, P, 0.30, 0.06, 0.50, 0.26)
        poly(d, P, [(0.20, 0.10), (0.34, 0.08), (0.36, 0.18), (0.22, 0.18)])       # upper jaw
        poly(d, P, [(0.24, 0.20), (0.36, 0.20), (0.34, 0.26), (0.26, 0.25)])       # lower jaw
        poly(d, P, [(0.42, 0.06), (0.45, 0.00), (0.49, 0.08)])                      # ear

    def near_fore(d, P, W):
        line(d, P, W, [(0.46, 0.33), (0.32, 0.31), (0.20, 0.24)], 0.075)
        poly(d, P, [(0.10, 0.20), (0.21, 0.19), (0.22, 0.28), (0.10, 0.28)])

    return [(tail, 0.86), (far_hind, 0.8), (far_fore, 0.8), (body, 1.0), (near_hind, 1.0), (mane, 0.92), (head, 1.0),
            (near_fore, 1.0)]


def lion_shapes(d, W, H, facing=-1):
    """The whole lion in white on a W x H canvas (one mask, e.g. for a faded rug figure)."""
    def P(x, y):
        return ((x if facing < 0 else 1.0 - x) * W, y * H)
    for part, _ in _lion_parts(facing):
        part(d, P, W)


def draw_lion(img, x0, y0, w, h, fill=GOLD, outline=GOLD_D, light=GOLD_L, facing=-1, eye=True):
    """Stamps the lion rampant in pixel art (gold, dark-gold outlines between the parts, light upper edges)."""
    for part, k in _lion_parts(facing):
        def fn(d, W, H, part=part):
            def P(x, y):
                return ((x if facing < 0 else 1.0 - x) * W, y * H)
            part(d, P, W)
        m = _mask(w, h, fn)
        stamp(img, m, _scale(fill, k), outline, _scale(light, k) if k >= 1.0 else None, x0, y0, shade=_scale(fill, 0.8 * k))
    if eye and w >= 14:
        ex = x0 + int(round((0.36 if facing < 0 else 0.64) * w))
        ey = y0 + int(round(0.13 * h))
        if 0 <= ex < img.size[0] and 0 <= ey < img.size[1]:
            img.putpixel((ex, ey), _rgb("3a1c08") + (255,))


def scales_shapes(d, W, H):
    """Balance scales in white: a pillar on a stepped foot, a knob, the beam, two pans on cords."""
    def P(x, y):
        return (x * W, y * H)
    lw = max(1, int(0.05 * W))
    d.rectangle((*P(0.46, 0.16), *P(0.54, 0.84)), fill=255)                       # pillar
    d.polygon([P(0.30, 0.94), P(0.70, 0.94), P(0.62, 0.84), P(0.38, 0.84)], fill=255)  # foot
    d.rectangle((*P(0.26, 0.93), *P(0.74, 0.98)), fill=255)
    d.ellipse((*P(0.42, 0.06), *P(0.58, 0.20)), fill=255)                       # knob
    d.line([P(0.10, 0.28), P(0.50, 0.22), P(0.90, 0.28)], fill=255, width=lw)   # beam (a little arched)
    for cx in (0.14, 0.86):
        d.ellipse((*P(cx - 0.04, 0.24), *P(cx + 0.04, 0.32)), fill=255)
        d.line([P(cx, 0.30), P(cx - 0.13, 0.58)], fill=255, width=max(1, lw // 2))
        d.line([P(cx, 0.30), P(cx + 0.13, 0.58)], fill=255, width=max(1, lw // 2))
        d.chord((*P(cx - 0.16, 0.48), *P(cx + 0.16, 0.70)), 0, 180, fill=255)     # pan


def draw_scales(img, x0, y0, w, h, fill=GOLD, outline=GOLD_D, light=GOLD_L):
    m = _mask(w, h, scales_shapes)
    stamp(img, m, fill, outline, light, x0, y0, shade=_scale(fill, 0.8))


def stripes(img, n, cols, rng, fold=0.14, seam=None, seam_w=1, stains=1, offset=0):
    """n vertical stripes across the image in the colours cols (in turn), woven, each with a soft fold (lighter middle,
    darker edges); seam = colour of a line between the stripes (gold trims)."""
    w, h = img.size
    edges = [int(round(k * w / n)) for k in range(n + 1)]
    for k in range(n):
        weave(img, cols[(k + offset) % len(cols)], rng, stains=stains, box_=(edges[k], 0, max(1, edges[k + 1] - edges[k]), h))
    px = img.load()
    for k in range(n):
        a, b = edges[k], edges[k + 1]
        for x in range(a, b):
            f = (x - a + 0.5) / max(1, b - a)
            kk = 1.0 - fold + 2 * fold * math.sin(math.pi * f) ** 0.7
            for y in range(h):
                r, g, bb, al = px[x, y]
                px[x, y] = _scale((r, g, bb), kk) + (255,)
    if seam is not None:
        for e in edges[1:-1]:
            for y in range(h):
                for x in range(e - seam_w, e + seam_w):
                    if 0 <= x < w:
                        px[x, y] = _jitter(seam if x >= e - seam_w + 1 or seam_w == 1 else _scale(seam, 0.75), rng, 8) + (255,)
    return edges


def gold_border(img, rng, width=2, inner=None, sides="tlrb"):
    """A gold border (width px, a darker line inside it when inner is a colour) on the given sides."""
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                continue
            e = []
            if "t" in sides:
                e.append(y)
            if "b" in sides:
                e.append(h - 1 - y)
            if "l" in sides:
                e.append(x)
            if "r" in sides:
                e.append(w - 1 - x)
            m = min(e) if e else 99
            if m < width:
                c = GOLD_L if m == 0 and width > 2 else GOLD
                px[x, y] = _jitter(c if m < width - 1 or width < 3 else _scale(GOLD, 0.86), rng, 8) + (255,)
            elif inner is not None and m == width:
                px[x, y] = _jitter(inner, rng, 4) + (255,)


def cut_point(img, start_frac, rng, edge=3, stepped=False):
    """Cuts the bottom of a banner into a V point from start_frac of the height, with a gold edge of `edge` px (a stepped
    edge when stepped: the pictures' pixel steps)."""
    w, h = img.size
    px = img.load()
    body = int(h * start_frac)
    for y in range(body, h):
        t = (y - body) / max(1, (h - body))
        half = (w / 2) * (1 - t)
        if stepped:
            half = math.floor(half / 2) * 2 + 1
        for x in range(w):
            dx = abs(x + 0.5 - w / 2)
            if dx > half:
                px[x, y] = (0, 0, 0, 0)
            elif dx > half - edge:
                px[x, y] = _jitter(GOLD if dx > half - edge + 1 else _scale(GOLD, 0.82), rng, 8) + (255,)


# ================================================================ region painters
def paint_post(base=WOOD, dark=WOOD_D, seed=1):
    def p(img):
        w, h = img.size
        ml.fine_wood(img, (0, 0, w, h), base, dark, h, random.Random(seed), joints=False, knots=0.08, grain=0.16, shade=0.1)
    return p


def paint_stone(img):
    """Light grey stone blocks (the posts' feet): two courses, offset joints, chipped light edges."""
    rng = random.Random(201)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = _rgb("9a9a98")
            c = _scale(c, 1.0 + 0.1 * math.sin(x * 0.9 + y * 1.7) * 0.5 + rng.uniform(-0.07, 0.07))
            px[x, y] = c + (255,)
    course = h // 2
    for y in range(h):
        for x in range(w):
            row = y // course
            off = (w // 2) * (row % 2)
            if y % course == 0 or (x + off) % w == 0 or (x + off) % w == w // 2 and row % 2 == 0:
                px[x, y] = _jitter(_rgb("5e5e5c"), rng, 5) + (255,)
            elif y % course == 1:
                px[x, y] = _jitter(_rgb("bcbcb8"), rng, 5) + (255,)


def paint_band(img):
    """Grey iron bands with a big square rivet in the middle and small ones near the ends."""
    rng = random.Random(202)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = _rgb("6a6c72")
            if y == 0:
                c = _rgb("9a9ca2")
            elif y == h - 1:
                c = _rgb("3a3c40")
            px[x, y] = _jitter(c, rng, 7) + (255,)
    for cx, r in ((w // 2, 1), (3, 0), (w - 4, 0)):
        for y in range(max(1, h // 2 - r), min(h - 1, h // 2 + r + 1)):
            for x in range(cx - r, cx + r + 1):
                px[x, y] = (44, 44, 48, 255) if (x == cx + r and r) else (186, 188, 194, 255)


def paint_roof(n, seed, cols=(NAVY, CREAM), seam=None, hem=0, fold=0.15, offset=0, hem_col=None):
    """A striped roof cloth: n stripes down the slope, soft folds, optional gold seams and a hem at the bottom (gold, or
    a band of hem_col under a gold line)."""
    def p(img):
        rng = random.Random(seed)
        stripes(img, n, cols, rng, fold=fold, seam=seam, seam_w=1 if seam is not None else 1, offset=offset)
        w, h = img.size
        px = img.load()
        for y in range(h):
            k = 0.92 + 0.12 * (y / h)
            for x in range(w):
                r, g, b, a = px[x, y]
                px[x, y] = _scale((r, g, b), k) + (255,)
        if hem and hem_col is None:
            for y in range(h - hem, h):
                for x in range(w):
                    px[x, y] = _jitter(GOLD if y > h - hem else GOLD_D, rng, 8) + (255,)
        elif hem:
            for y in range(h - hem, h):
                for x in range(w):
                    c = GOLD if y < h - hem + 2 else _scale(hem_col, 0.9 + 0.1 * math.sin(x * 0.4))
                    px[x, y] = _jitter(c, rng, 7) + (255,)
    return p


def paint_valance(n, seed, cols=(CREAM, NAVY), shape="dag", band=0.4, tabs_per=1, offset=0):
    """A valance: n segments in the colours cols in turn, a band on top, tabs hanging below (shape "dag": stepped
    pointed dags; "square": square tabs; "crenel": a blue band with gold square crenels), gold edges, cut-out gaps."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        seg = w / n
        bh = int(h * band)
        ntab = n * tabs_per
        tab = w / ntab
        for x in range(w):
            k = int(x / seg)
            c = cols[(k + offset) % len(cols)]
            lx = (x % tab) / tab
            for y in range(h):
                if shape == "dag":
                    # stepped point: the tab narrows in 2 px steps towards its tip
                    t = (y - bh) / max(1, h - bh)
                    half = 0.5 * (1 - t) if y > bh else 0.5
                    half = math.floor(half * tab / 2) * 2 / tab + 0.5 / tab
                    inside = abs(lx - 0.5) <= half and y > bh or y <= bh
                    edge = inside and (abs(lx - 0.5) > half - 2.2 / tab and y > bh or y >= h - 1)
                elif shape == "square":
                    inside = y <= bh or 0.1 <= lx <= 0.9
                    edge = inside and y > bh and (lx < 0.1 + 1.6 / tab or lx > 0.9 - 1.6 / tab or y >= h - 2)
                elif shape == "pent":
                    # the pictures' dags: a square tab ending in a short stepped point, gold edged, narrow gaps between
                    yp = bh + int((h - bh) * 0.5)
                    t = (y - yp) / max(1, h - yp)
                    half = 0.44 if y <= yp else 0.44 * (1 - 0.8 * t)
                    half = math.floor(half * tab / 2) * 2 / tab + 0.5 / tab
                    inside = y <= bh or abs(lx - 0.5) <= half
                    edge = inside and y > bh and (abs(lx - 0.5) > half - 2.2 / tab or y >= h - 1)
                else:   # crenel: blue band, a thick gold square-wave line, blue merlons hanging below with gold edges
                    inside = y <= bh or 0.2 <= lx <= 0.8
                    edge = False
                if not inside:
                    px[x, y] = (0, 0, 0, 0)
                    continue
                cc = c
                if shape == "crenel":
                    merlon = 0.2 <= lx <= 0.8
                    y_line = int(bh * 0.25) if merlon else int(bh * 0.62)
                    cc = NAVY
                    if y < 2:
                        cc = GOLD_D
                    elif y_line <= y < y_line + 3:
                        cc = GOLD
                    elif (abs(lx - 0.2) * tab < 1.6 or abs(lx - 0.8) * tab < 1.6) and int(bh * 0.25) <= y < int(bh * 0.62) + 3:
                        cc = GOLD
                    elif y > bh and (lx < 0.2 + 2.0 / tab or lx > 0.8 - 2.0 / tab or y >= h - 2):
                        cc = GOLD
                    elif bh - 1 <= y <= bh and not merlon:
                        cc = GOLD
                elif edge:
                    cc = GOLD
                elif y < 2:
                    cc = GOLD_D
                elif y == bh and shape != "dag":
                    cc = _scale(c, 0.8)
                kk = 1.0 + 0.05 * math.sin(x * 0.6) - 0.08 * (y > bh and lx > 0.7)
                px[x, y] = _jitter(_scale(cc, kk), rng, 7) + (255,)
            if shape != "crenel":
                for y in range(h):
                    if y < h and px[x, y][3] and y == bh - 1:
                        px[x, y] = _jitter(GOLD, rng, 8) + (255,)
    return p


def paint_banner(emblem="lion", seed=10, bottom="point", start=0.72, field=NAVY, stepped=True, tassel=False, facing=-1):
    """A hanging banner: blue woven field, a gold border with a dark blue line inside, the gold emblem (lion or
    scales), the bottom cut into a V point (bottom "point"), castellated dags ("dags") or straight."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, field, rng)
        gold_border(img, rng, width=2 if w < 40 else 3, inner=NAVY_D)
        body = int(h * start) if bottom != "flat" else h
        ew = int(w * 0.72)
        eh = int(min(body * 0.78, ew * 1.25))
        ex = (w - ew) // 2
        ey = max(3, int(body * 0.5 - eh / 2) + 1)
        if emblem == "lion":
            draw_lion(img, ex, ey, ew, eh, facing=facing)
        elif emblem == "scales":
            draw_scales(img, ex, ey, ew, int(ew * 0.95))
        if bottom == "point":
            cut_point(img, start, rng, edge=2 if w < 40 else 3, stepped=stepped)
        elif bottom == "dags":
            px = img.load()
            nt = 4
            for y in range(body, h):
                for x in range(w):
                    lx = (x % (w / nt)) / (w / nt)
                    if not (0.15 <= lx <= 0.85):
                        px[x, y] = (0, 0, 0, 0)
                    elif lx < 0.15 + 2.0 / (w / nt) or lx > 0.85 - 2.0 / (w / nt) or y >= h - 2:
                        px[x, y] = _jitter(GOLD, rng, 8) + (255,)
            for x in range(w):
                for y in (body - 2, body - 1):
                    px[x, y] = _jitter(GOLD, rng, 8) + (255,)
        if tassel:
            px = img.load()
            for y in range(h - 5, h):
                for x in range(w // 2 - 1, w // 2 + 2):
                    px[x, y] = _jitter(GOLD, rng, 8) + (255,)
    return p


def paint_flag(seed=20):
    """The lion flag on the top pole: blue field, gold border top and bottom, the lion near the pole, a gold band and
    a blue end flying free (the right edge ragged)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, NAVY, rng)
        px = img.load()
        for y in range(h):
            for x in range(w):
                if y < 2 or y >= h - 2 or x < 2:
                    px[x, y] = _jitter(GOLD, rng, 8) + (255,)
                elif y == 2 or y == h - 3:
                    px[x, y] = _jitter(NAVY_D, rng, 4) + (255,)
                elif int(w * 0.66) <= x < int(w * 0.66) + 3:
                    px[x, y] = _jitter(GOLD, rng, 8) + (255,)
        for y in range(h):
            for x in range(w - 3, w):
                if (y // 3 + x) % 2 == 0:
                    px[x, y] = (0, 0, 0, 0)
        lw = int(w * 0.5)
        draw_lion(img, int(w * 0.08), 3, lw, h - 6, facing=-1)
    return p


def paint_rug(seed=30, emblem="lion", field=NAVY, faded=0.18):
    """A blue rug: dark blue outer band, two gold lines, a gold pattern band, the emblem (lion: a big faded gold lion;
    "meander": gold key pattern corners and a medallion)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, field, rng, stains=2)
        px = img.load()
        for y in range(h):
            for x in range(w):
                e = min(x, y, w - 1 - x, h - 1 - y)
                if e < 2:
                    px[x, y] = _jitter(GOLD, rng, 10) + (255,)
                elif e < 5:
                    px[x, y] = _jitter(NAVY_D, rng, 5) + (255,)
                elif e in (5, 6):
                    px[x, y] = _jitter(GOLD, rng, 10) + (255,)
                elif 7 <= e <= 10 and ((x + y) // 2) % 3 == 0:
                    px[x, y] = _jitter(_mix(field, GOLD, 0.6), rng, 8) + (255,)
                elif e == 12:
                    px[x, y] = _jitter(_scale(GOLD, 0.9), rng, 8) + (255,)
        if emblem == "lion":
            lw = int(min(w * 0.42, h * 0.62))
            from PIL import Image
            sub = Image.new("RGBA", (lw, lw), (0, 0, 0, 0))
            draw_lion(sub, 0, 0, lw, lw, fill=_mix(GOLD, field, faded), outline=_mix(GOLD_D, field, 0.4 + faded / 2), light=_mix(GOLD, field, faded * 0.6), eye=False)
            img.alpha_composite(sub, ((w - lw) // 2, (h - lw) // 2))
            for (cx, cy) in ((18, 18), (w - 19, 18), (18, h - 19), (w - 19, h - 19)):
                for j in range(-3, 4):
                    for i in range(-3, 4):
                        if abs(i) + abs(j) <= 3 and (abs(i) + abs(j)) % 2 == 1:
                            px[cx + i, cy + j] = _jitter(GOLD, rng, 8) + (255,)
        else:
            # gold key (meander) pattern along the inner band, a gold diamond medallion in the middle
            for y in range(h):
                for x in range(w):
                    e = min(x, y, w - 1 - x, h - 1 - y)
                    if 14 <= e <= 20:
                        lx = ((x if min(y, h - 1 - y) < min(x, w - 1 - x) else y) - 14) % 8
                        ly = e - 14
                        if ly in (0, 6) or (lx == 0 and ly < 5) or (lx == 4 and ly > 1) or (ly == 3 and 1 <= lx <= 4):
                            px[x, y] = _jitter(GOLD, rng, 9) + (255,)
            cx, cy = w // 2, h // 2
            for y in range(h):
                for x in range(w):
                    d = abs(x - cx) / (w * 0.22) + abs(y - cy) / (h * 0.26)
                    if 0.92 <= d <= 1.0 or d <= 0.18:
                        px[x, y] = _jitter(GOLD, rng, 9) + (255,)
    return p


def paint_curtain(base=CREAM, seed=40, folds=4, hem=True, motif=False, edge=None, edge_w=4, motif_size=3, band=False):
    """A curtain: vertical folds (darker valleys), optional gold diamond motifs (the chapiteau's blue curtains), a gold
    hem at the bottom, optional coloured band along the outer edge; band: one gold-edged vertical band of gold diamonds
    down the middle (the picture's curtains) instead of the scattered motifs."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, base, rng)
        px = img.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                f = (x * folds / w) % 1.0
                k = 0.8 + 0.26 * math.sin(math.pi * f) ** 0.8
                px[x, y] = _scale((r, g, b), k) + (255,)
        if band:
            c0 = w // 2
            hb = max(4, w // 10)
            for y in range(h - 3):
                for x in (c0 - hb, c0 + hb):
                    if 0 <= x < w:
                        px[x, y] = _jitter(GOLD, rng, 8) + (255,)
            for cy in range(7, h - 8, 11):
                for j in range(-3, 4):
                    for i in range(-hb + 2, hb - 1):
                        if abs(i) * 1.4 + abs(j) <= 3.2:
                            px[c0 + i, cy + j] = _jitter(GOLD if abs(i) + abs(j) < 3 else GOLD_D, rng, 8) + (255,)
        if motif:
            for cy in range(6, h - 6, 12):
                for cx in range(int(w / folds / 2), w, int(w / folds)):
                    for j in range(-motif_size, motif_size + 1):
                        for i in range(-2, 3):
                            if abs(i) * 1.5 + abs(j) <= motif_size:
                                X_, Y_ = cx + i, cy + j + (6 if (cx // int(w / folds)) % 2 else 0)
                                if 0 <= X_ < w and 0 <= Y_ < h - 4:
                                    px[X_, Y_] = _jitter(GOLD, rng, 10) + (255,)
        if edge is not None:
            for y in range(h):
                for x in range(w - edge_w, w):
                    k = 0.8 + 0.25 * math.sin(math.pi * (x - w + edge_w + 0.5) / edge_w)
                    px[x, y] = _jitter(_scale(edge, k), rng, 5) + (255,)
                px[w - edge_w - 1, y] = _jitter(GOLD, rng, 8) + (255,)
        if hem:
            for y in range(h - 3, h):
                for x in range(w):
                    px[x, y] = _jitter(GOLD if y > h - 3 else GOLD_D, rng, 8) + (255,)
    return p


def paint_runner(emblem="lion", seed=50, field=NAVY, star_dots=False):
    """A counter cloth hanging down the front: blue, gold border, the emblem in the middle, the bottom cut into a V
    point (pentagon), little gold stars when star_dots."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, field, rng)
        gold_border(img, rng, width=2, inner=NAVY_D)
        px = img.load()
        if star_dots:
            for (fx, fy) in ((0.14, 0.2), (0.86, 0.2), (0.14, 0.62), (0.86, 0.62)):
                cx, cy = int(fx * w), int(fy * h)
                for (i, j) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                    px[cx + i, cy + j] = _jitter(GOLD, rng, 8) + (255,)
        ew = int(w * 0.62)
        ex = (w - ew) // 2
        if emblem == "lion":
            draw_lion(img, ex, 4, ew, int(h * 0.62), facing=-1)
        else:
            draw_scales(img, ex, 5, ew, int(h * 0.55))
        cut_point(img, 0.74, rng, edge=2, stepped=True)
    return p


def paint_cloth_top(seed=55, base=CREAM, dags=True):
    """A cream table cloth with a dagged hem (the chapiteau counter's top cloth) and a gold line."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, base, rng)
        px = img.load()
        for y in range(h):
            for x in range(w):
                if y in (h - 7, h - 8):
                    px[x, y] = _jitter(GOLD, rng, 8) + (255,)
                if dags and y > h - 6 and (x // 6) % 2 == 1:
                    px[x, y] = (0, 0, 0, 0)
    return p


def paint_chest(img):
    """Chest wood: warm horizontal planks with dark joints."""
    rng = random.Random(60)
    w, h = img.size
    ml.fine_wood(img, (0, 0, w, h), _rgb("9a6434"), _rgb("4a2c12"), max(4, h // 4), rng, joints=True, knots=0.05, grain=0.14, shade=0.1)


def paint_cheese(img):
    rng = random.Random(61)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = _rgb("f0c858") if (x + y * 3) % 11 else _rgb("d8a838")
            if x == 0 or y == 0:
                c = _rgb("ffe08a")
            px[x, y] = _jitter(c, rng, 8) + (255,)


def paint_burlap(base=_rgb("e6d4b4"), seed=62):
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        ml._weave(img, (0, 0, w, h), base, rng, stains=0)
        px = img.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                k = 0.84 + 0.22 * math.sin(math.pi * (x + 0.5) / w) - 0.07 * (abs(math.sin(x * 0.55 + y * 0.08)) > 0.93)
                px[x, y] = _scale((r, g, b), k) + (255,)
    return p


def paint_roll_red(img):
    """Red cloth rolls with a gold zigzag band (the drapee's left counter)."""
    rng = random.Random(63)
    w, h = img.size
    weave(img, _rgb("a82a24"), rng)
    px = img.load()
    for y in range(h):
        for x in range(w):
            if abs(y - h // 2) <= 1 and (x + y) % 4 < 2 or y in (h // 2 - 3, h // 2 + 3):
                px[x, y] = _jitter(GOLD, rng, 8) + (255,)


def paint_wheat(img):
    """Cut-out wheat sheaf: straw stems, golden ears at the top."""
    rng = random.Random(64)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = (0, 0, 0, 0)
    for k in range(9):
        x = int(w * (0.12 + 0.76 * k / 8))
        top = int(h * rng.uniform(0.0, 0.12))
        lean = rng.uniform(-0.12, 0.12)
        for y in range(top, h):
            xx = int(x + lean * (h - y) * 0.4)
            if 0 <= xx < w:
                ear = y < top + h * 0.32
                c = _rgb("e2b048") if ear else _rgb("c8a040")
                px[xx, y] = _jitter(c, rng, 12) + (255,)
                if ear and (y - top) % 2 == 0:
                    for dx in (-1, 1):
                        if 0 <= xx + dx < w:
                            px[xx + dx, y] = _jitter(_rgb("f0c860"), rng, 12) + (255,)


def paint_globe(img):
    rng = random.Random(65)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            land = (math.sin(x * 0.9) + math.cos(y * 1.1 + x * 0.3)) > 0.6
            px[x, y] = _jitter(_rgb("4a8a4a") if land else _rgb("2a5a9a"), rng, 8) + (255,)


def paint_sign_board(emblem="scales", seed=70):
    """The hanging shield sign: blue field, gold border, the gold scales, a pointed bottom (shield)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, NAVY, rng)
        gold_border(img, rng, width=3, inner=NAVY_D)
        ew = int(w * 0.66)
        draw_scales(img, (w - ew) // 2, int(h * 0.16), ew, int(ew * 0.95))
        cut_point(img, 0.66, rng, edge=3, stepped=True)
    return p


# name -> (w, h, painter)
REGIONS = {
    "b_post": (64, 16, paint_post(WOOD, WOOD_D, 101)),
    "b_post_dark": (64, 16, paint_post(WOOD_DARK, WOOD_DARK_D, 102)),
    "b_stone": (16, 16, paint_stone),
    "b_band": (32, 8, paint_band),
    "b_chest": (32, 16, paint_chest),
    "b_cheese": (8, 8, paint_cheese),
    "b_sack": (32, 32, paint_burlap()),
    "b_roll_red": (16, 16, paint_roll_red),
    "b_wheat": (16, 32, paint_wheat),
    "b_globe": (8, 8, paint_globe),
    "b_drape": (32, 64, paint_curtain(CREAM, 41, folds=3, edge=NAVY, edge_w=5)),
    "b_curtain_blue": (48, 64, paint_curtain(NAVY, 42, folds=4, motif=True, motif_size=2)),
    "b_curtain_band": (48, 64, paint_curtain(NAVY, 43, folds=4, band=True)),
}
M1_REGIONS = ["flowers_purple", "pot_clay", "soil", "sprout", "herbs", "vines", "leaves", "glass", "cork", "pages", "book_top",
              "book_red", "book_blue", "book_green", "book_brown", "book_purple", "parchment", "jar", "jar_top", "linen",
              "potion_purple", "potion_blue", "potion_green", "potion_red", "potion_pink", "potion_orange", "potion_cyan",
              "potion_yellow", "potion_violet"]


def add_regions(atlas, own=(), m1=()):
    """Adds the group regions `own` (names of REGIONS, or (name, w, h, painter) tuples) and the props_m1 regions m1
    (skipping the shell's own), tallest first so that they pack in the atlas' free band without doubling it."""
    todo = []
    for r in own:
        if isinstance(r, tuple):
            todo.append(r)
        else:
            w, h, painter = REGIONS[r]
            todo.append((r, w, h, painter))
    for n in m1:
        if n in atlas.regions and n not in atlas.painters:
            continue
        w, h, painter = p1.PAINTERS[n]
        todo.append((n, w, h, painter))
    todo.sort(key=lambda t: (-t[2], -t[1], t[0]))
    for name, w, h, painter in todo:
        atlas.add(name, w, h, painter)


# ================================================================ geometry
def band(bone, name, x, z, half, y, h, region="b_band"):
    """An iron (or gold) band round a squared post (centre x, z)."""
    cap = "gold" if region == "gold" else "iron"
    box(bone, name, (x - half, y, z - half), (x + half, y + h, z + half), {"all": region, "+2": cap, "-2": cap}, stretch=True)


def squircle(theta, hx, hz, n=4.0):
    """A point (x, z) of the rounded rectangle |x/hx|^n + |z/hz|^n = 1 at the polar angle theta."""
    c, s = math.cos(theta), math.sin(theta)
    return (hx * math.copysign(abs(c) ** (2.0 / n), c), hz * math.copysign(abs(s) ** (2.0 / n), s))


def dome(t, a=0.5):
    """A rounded (dome) profile: the fraction of the drop at t from the top (flatter at the top, steep at the eave)."""
    return a * t + (1 - a) * t * t


def ring_roof(bone, name, top, bottom, region, nx=24, ny=4, a=0.42, droop=0.08, phase=0.0, th=0.04, fold=0.04, profile="concave", fan=True, cover=0.0,
              n=4.0, radial=False):
    """A rounded marquee roof from the ring top = (y, hx, hz) (or a point when hx = hz = 0) down to the ring
    bottom = (y, hx, hz): concave (steep above, flatter below), the cloth sagging a little between the nx strips; the
    region wraps once round it (stripes). Returns P(s, t)."""
    yt, hxt, hzt = top
    yb, hxb, hzb = bottom

    def arc(hx, hz, N=720):
        """s -> the squircle point at the fraction s of its length from `phase` (strips evenly spaced along the ring,
        the stripes keep one width round a long marquee and the top and bottom rings stay matched, no twist)."""
        ths = [phase + 2 * math.pi * k / N for k in range(N + 1)]
        pts = [squircle(a_, hx, hz, n) for a_ in ths]
        cum = [0.0]
        for k in range(N):
            cum.append(cum[-1] + math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]))

        def at(s):
            L = (s % 1.0) * cum[-1]
            i = min(max(bisect.bisect_left(cum, L), 1), N)
            f = (L - cum[i - 1]) / max(1e-9, cum[i] - cum[i - 1])
            return squircle(ths[i - 1] + (ths[i] - ths[i - 1]) * f, hx, hz, n)
        return at
    bot_at = arc(hxb, hzb)
    top_at = arc(hxt, hzt) if hxt > 0 else (lambda s: (0.0, 0.0))
    if radial and hxt > 0:
        # the top ring a scaled copy of the bottom one: every strip runs straight towards the centre (no twist)
        top_at = (lambda s, k=hxt / hxb: tuple(c * k for c in bot_at(s)))

    def P(s, t):
        xt, zt = top_at(s)
        xb, zb = bot_at(s)
        y = yt - (yt - yb) * (concave(t, a) if profile == "concave" else dome(t, a))
        f = (s * nx) % 1.0
        sag = droop * math.sin(math.pi * t) + fold * math.sin(math.pi * f) * t
        k = 1.0 - sag / max(0.5, math.hypot(xb, zb))
        return v3((xt + (xb - xt) * t) * k, y - 0.5 * sag, (zt + (zb - zt) * t) * k)
    if fan:
        fan_loft(bone, name, lambda s, t: P(1.0 - s, t), nx, ny, region, th=th, overlap=0.04, center=(0.0, yb - 1.0, 0.0), cover=cover)
    else:
        loft(bone, name, lambda s, t: P(1.0 - s, t), nx, ny, region, th=th, overlap=0.03)
    return P


def sq_post(shell, det, name, x, z, top, d=0.42, stone=0.0, stone_w=None, bands=(), cap="block", region="b_post", collide_to=None,
            cap_region="wood", band_region="b_band"):
    """A squared wooden post from the ground (or a stone foot block of height `stone`) up to `top`, iron bands at the
    heights `bands`, a cap: "block" (a wider block and a smaller one), "cross" (a T cross-bar along x), "gold" (gold
    finial), None. Collides from the ground up to collide_to (default top)."""
    y0 = 0.0
    if stone > 0:
        sw = stone_w or d + 0.22
        box(shell, name + "_stone", (x - sw / 2, 0.0, z - sw / 2), (x + sw / 2, stone, z + sw / 2), {"all": "b_stone", "+2": "stone_top"},
            stretch=True)
        y0 = stone
    beam(shell, name, (x, y0, z), (x, top, z), d, {"all": region, "+1": "end_grain", "-1": "end_grain"})
    for k, y in enumerate(bands):
        band(det, "%s_band_%d" % (name, k), x, z, d / 2 + 0.025, y, 0.13, region=band_region)
    c = d / 2 + 0.1
    if cap == "block":
        box(shell, name + "_cap", (x - c, top, z - c), (x + c, top + 0.26, z + c), {"all": cap_region, "+2": "end_grain"})
        box(det, name + "_cap_top", (x - c + 0.08, top + 0.26, z - c + 0.08), (x + c - 0.08, top + 0.4, z + c - 0.08),
            {"all": "wood_dark", "+2": "end_grain"})
    elif cap == "cross":
        box(shell, name + "_cap", (x - c, top, z - c), (x + c, top + 0.22, z + c), {"all": cap_region, "+2": "end_grain"})
        box(shell, name + "_cross", (x - 0.42, top + 0.22, z - 0.12), (x + 0.42, top + 0.4, z + 0.12), {"all": "wood", "+1": "end_grain",
                                                                                                        "-1": "end_grain"})
        for s in (-1, 1):
            box(det, "%s_cross_end_%d" % (name, (s + 1) // 2), (x + s * 0.42 - 0.1, top + 0.18, z - 0.15), (x + s * 0.42 + 0.1, top + 0.44, z + 0.15),
                {"all": "wood_dark", "+2": "end_grain"})
        box(det, name + "_cap_top", (x - 0.14, top + 0.42, z - 0.14), (x + 0.14, top + 0.62, z + 0.14), {"all": "wood_dark", "+2": "end_grain"})
    elif cap == "gold":
        box(shell, name + "_cap", (x - c + 0.04, top, z - c + 0.04), (x + c - 0.04, top + 0.16, z + c - 0.04), "gold")
        ml.octo(det, name + "_finial", (x, top + 0.16, z), 0.12, 0.2, "gold")
        add_cube(det, name + "_finial_tip", (x, top + 0.44, z), ry(math.pi / 4) @ rx(math.pi / 4), (0.15, 0.15, 0.15), "gold")
    hh = collide_to if collide_to is not None else top
    hw = max(d / 2, (stone_w or d + 0.22) / 2 if stone > 0 else d / 2)
    collide((x - hw, 0.0, z - hw, x + hw, hh, z + hw))


def concave(t, a=0.42):
    """A roof profile: the fraction of the drop at t from the top (steep at the top, flatter at the eave)."""
    return a * t + (1 - a) * (1 - (1 - t) ** 2)


def fan_loft(bone, name, P, nx, ny, region, th=0.04, overlap=0.03, lift=0.012, center=None, cover=1.0):
    """ml.loft for cloth that widens or narrows down the surface (pyramid sides, round marquees): each strip follows the
    line through the middles of its top and bottom edges, so the radial stripes stay straight and the hips stay clean
    (ml.loft's strips, squared on the mean edge, stick out in saw teeth there); with cover = 1 it covers the wider of its
    two ends and the four corners (no gap; cover = 0: the mean width, as ml.loft), and every other column sits `lift`
    further out (away from `center`) so the overlap of two neighbours never flickers."""
    for i in range(nx):
        for j in range(ny):
            s0, s1, t0, t1 = i / nx, (i + 1) / nx, j / ny, (j + 1) / ny
            a1, b1, a0, b0 = P(s0, t0), P(s1, t0), P(s0, t1), P(s1, t1)   # a = left, b = right, 1 = top, 0 = bottom
            vp = (a0 + b0) / 2 - (a1 + b1) / 2
            H = np.linalg.norm(vp)
            if H < 1e-5:
                continue
            v = vp / H
            uw = ((b0 - a0) + (b1 - a1)) / 2
            u = uw - np.dot(uw, v) * v
            if np.linalg.norm(u) < 1e-6:
                continue
            u = norm(u)
            n = np.cross(u, v)
            corners = (a0, a1, b0, b1)
            pu = [np.dot(p, u) for p in corners]
            pv = [np.dot(p, v) for p in corners]
            pn = [np.dot(p, n) for p in corners]
            mid_u = np.dot((a0 + a1 + b0 + b1) / 4, u)
            w_mean = (abs(np.dot(b1 - a1, u)) + abs(np.dot(b0 - a0, u))) / 2
            w = w_mean + cover * (max(pu) - min(pu) - w_mean)
            mid_u += cover * ((max(pu) + min(pu)) / 2 - mid_u)
            c = u * mid_u + v * (max(pv) + min(pv)) / 2 + n * (sum(pn) / 4)
            if center is not None and lift and i % 2 == 1:
                out = n if np.dot(n, c - v3(*center)) > 0 else -n
                c = c + out * lift
            regions = {"all": None, "+3": region, "-3": region}
            cube = add_cube(bone, "%s_%d_%d" % (name, i, j), c, np.column_stack([u, v, n]),
                            (w + overlap, max(pv) - min(pv) + overlap, th), regions, stretch=True, u_dir=u, v_dir=v)
            ml.tl.gn.set_sub(cube, (s0, t0, s1, t1))


def hip_side(bone, name, apex0, apex1, c0, c1, region, nx=6, ny=5, droop=0.1, a=0.42, edge_sag=0.0, th=0.04, folds=0.0, fan=True):
    """One concave side of a hipped roof from the ridge segment apex0-apex1 (a point for a pyramid) down to the eave
    corners c0-c1: steep at the top, flatter below, the cloth drooping between the corners; edge_sag lowers the middle
    of the eave line (a soft curved edge, corners higher); folds = depth of a soft fold in each of the nx strips.
    Returns P(s, t) (t = 1: the eave line)."""
    apex0, apex1, c0, c1 = (v3(*p) for p in (apex0, apex1, c0, c1))

    def P(s, t):
        top = apex0 + (apex1 - apex0) * s
        e = c0 + (c1 - c0) * s
        p = top * (1 - t) + e * t
        y = top[1] - (top[1] - e[1]) * concave(t, a) - droop * math.sin(math.pi * s) * math.sin(math.pi * t)
        y -= edge_sag * math.sin(math.pi * s) * t ** 2
        if folds:
            y -= folds * math.sin(math.pi * ((s * nx) % 1.0)) * math.sin(math.pi * min(1.0, t * 1.2)) * 0.5
        p[1] = y
        return p
    if fan:
        fan_loft(bone, name, P, nx, ny, region, th=th, overlap=0.03, center=(apex0 + apex1) / 2 - UP * 3.0)
    else:
        loft(bone, name, P, nx, ny, region, th=th, overlap=0.03)
    return P


def valance_curve(bone, name, E, out, h=0.5, region="valance", nx=4, flare=0.06):
    """A valance hanging from the curve E(s) (s in 0..1, e.g. a roof's eave line P(s, 1)), flaring out towards `out`."""
    out = v3(*out)

    def V(s, t):
        return E(s) + UP * 0.02 - UP * (h * t) + out * (0.03 + flare * t)
    loft(bone, name, V, nx, 1, region, th=0.025)


def valance(bone, name, c0, c1, out, h=0.5, region="valance", nx=None, flare=0.06):
    """A valance hanging from the edge c0-c1, flaring out a little towards `out` (a soft curve)."""
    c0, c1, out = v3(*c0), v3(*c1), v3(*out)

    def V(s, t):
        e = c0 + (c1 - c0) * s
        return e + UP * 0.03 - UP * (h * t) + out * (0.02 + flare * t)
    L = np.linalg.norm(c1 - c0)
    loft(bone, name, V, nx or max(1, int(round(L / 2.0))), 1, region, th=0.025)


def drape(bone, det, name, top_a, top_b, tie, bot_a, bot_b, normal, region="b_drape", nx=3, tie_region="rope"):
    """A curtain tied back: hangs from the edge top_a - top_b, gathered at `tie` (a rope band), flaring again below to
    bot_a - bot_b; soft folds along `normal`."""
    top_a, top_b, tie, bot_a, bot_b, n = (v3(*p) for p in (top_a, top_b, tie, bot_a, bot_b, normal))
    side = norm(top_b - top_a)

    def fold(s):
        # accordion folds: the cloth's vertical creases alternately in and out
        return 1.0 if int(round(s * nx)) % 2 else -1.0

    def U(s, t):
        tt = t ** 0.85
        a = top_a + (top_b - top_a) * s
        b = tie + side * ((s - 0.5) * 0.18)
        return a * (1 - tt) + b * tt + n * (0.07 * fold(s) * (1 - t) ** 0.7 + 0.06 * math.sin(math.pi * t))

    def Lw(s, t):
        a = tie + side * ((s - 0.5) * 0.18)
        b = bot_a + (bot_b - bot_a) * s
        return a * (1 - t) + b * t + n * (0.08 * fold(s) * t ** 0.8 + 0.05 * math.sin(math.pi * t))
    fan_loft(bone, name + "_up", U, nx, 3, region, th=0.03, overlap=0.02)
    fan_loft(bone, name + "_lo", Lw, nx, 2, region, th=0.03, overlap=0.02)
    add_cube(det, name + "_tie", tie, np.column_stack([side, UP, np.cross(side, UP)]), (0.3, 0.1, 0.2), tie_region)


def wall(bone, name, a, b, y0, y1, out, region, nx=6, fold=0.05, ny=2):
    """A hanging canvas wall from a (left) to b on the ground line, y0..y1, soft vertical folds towards `out`."""
    a, b, out = v3(*a), v3(*b), v3(*out)

    def P(s, t):
        p = a + (b - a) * s
        return v3(p[0], y1 - (y1 - y0) * t, p[2]) + out * (fold * math.sin(s * math.pi * nx) * (0.4 + 0.6 * t))
    loft(bone, name, P, nx, ny, region, th=0.03)


def swag(det, name, a, b, sag=0.22, d=0.1, segs=4, knots=True, tails=0.0, region="rope"):
    """A twisted decorative rope swag from a to b (knots at both ends, optional hanging tails)."""
    a, b = v3(*a), v3(*b)
    ml.rope(det, name, a, b, d=d, sag=sag, segs=segs, region=region)
    if knots:
        for k, p in enumerate((a, b)):
            add_cube(det, "%s_knot_%d" % (name, k), p, EYE, (d * 1.9, d * 2.0, d * 1.9), region)
            if tails > 0:
                ml.rope(det, "%s_tail_%d" % (name, k), p, p - UP * tails, d=d * 0.75, segs=1)


def bracket_lantern(shell, det, name, mount, out, drop=0.5, size=0.36, arm=0.4):
    """A lantern hanging from an iron arm sticking out of a post at `mount` in the direction `out` (a brace under it)."""
    mount, out = v3(*mount), norm(v3(*out))
    tip = mount + out * arm
    beam(det, name + "_arm", mount, tip, 0.05, "iron", extend=0.02)
    beam(det, name + "_brace", mount - UP * 0.36, tip - UP * 0.02, 0.04, "iron")
    ml.lantern(shell, name, tip - UP * drop, size=size, metal="iron", chain_to=tip)


def chest(shell, det, name, foot, w=0.9, d=0.6, h=0.62, yaw=0.0, solid=True, metal="iron"):
    """An iron-banded wooden chest: body, rounded lid (two boxes), iron bands, corners and a lock plate (front = +z)."""
    foot = v3(*foot)
    R = ry(yaw)
    add_cube(shell, name + "_body", foot + UP * (h * 0.36), R, (w, h * 0.72, d), {"all": "b_chest"}, stretch=True)
    add_cube(shell, name + "_lid", foot + UP * (h * 0.81), R, (w + 0.03, h * 0.2, d + 0.03), {"all": "b_chest"}, stretch=True)
    add_cube(shell, name + "_lid_top", foot + UP * (h * 0.95), R, (w, h * 0.12, d * 0.7), {"all": "b_chest"}, stretch=True)
    for k, s in enumerate((-0.42, 0.42)):
        add_cube(det, "%s_band_%d" % (name, k), foot + R @ v3(s * w, h * 0.5, 0), R, (0.07, h + 0.02, d + 0.04), metal)
    add_cube(det, name + "_rim", foot + UP * (h * 0.72), R, (w + 0.05, 0.05, d + 0.05), metal)
    add_cube(det, name + "_lock", foot + R @ v3(0, h * 0.62, d / 2 + 0.025), R, (0.14, 0.2, 0.04), metal)
    if solid:
        ex = abs(math.cos(yaw)) * w / 2 + abs(math.sin(yaw)) * d / 2
        ez = abs(math.sin(yaw)) * w / 2 + abs(math.cos(yaw)) * d / 2
        collide((foot[0] - ex, foot[1], foot[2] - ez, foot[0] + ex, foot[1] + h, foot[2] + ez))


def big_sack(shell, det, name, foot, yaw=0.0, w=0.62, h=0.85, region="b_sack", solid=False):
    """A big tied sack: an octagonal bulging body narrowing upwards, a tied neck, a flared top."""
    foot = v3(*foot)
    R = ry(yaw)
    for k, (y0, y1, s) in enumerate(((0.0, 0.12, 0.86), (0.12, 0.5, 1.0), (0.5, 0.68, 0.82))):
        for j in range(2):
            q = 0.84 if j else 1.0
            add_cube(shell, "%s_%d_%d" % (name, k, j), foot + UP * (h * (y0 + y1) / 2), R @ ry(math.pi / 4 * j + 0.05 * k),
                     (w * s * q, h * (y1 - y0), w * s * q), region, stretch=True)
    add_cube(shell, name + "_neck", foot + UP * (h * 0.75), R, (w * 0.34, h * 0.12, w * 0.34), region, stretch=True)
    add_cube(det, name + "_tie", foot + UP * (h * 0.74), R, (w * 0.4, 0.07, w * 0.4), "rope")
    add_cube(shell, name + "_top", foot + UP * (h * 0.87), R @ ry(0.4), (w * 0.52, h * 0.16, w * 0.48), region, stretch=True)
    if solid:
        collide((foot[0] - w / 2, foot[1], foot[2] - w / 2, foot[0] + w / 2, foot[1] + h * 0.7, foot[2] + w / 2))


def scroll(bone, name, c, length=0.4, r=0.055, yaw=0.0, region="beige"):
    """A rolled scroll lying on its side (two boxes turned 45 degrees about its axis), along yaw."""
    c = v3(*c)
    for k, a in enumerate((0.0, math.pi / 4)):
        add_cube(bone, "%s_%d" % (name, k), c, ry(yaw) @ rx(a), (length, 2 * r * 0.83, 2 * r * 0.83), {"all": region, "+1": "white", "-1": "white"},
                 stretch=True)


def armillary(shell, det, name, foot, r=0.26):
    """A gold armillary sphere on a turned stand: a base, a stem, three rings (horizon, meridian, tilted ecliptic) of
    thin segments, a small globe in the middle."""
    foot = v3(*foot)
    ml.octo(shell, name + "_base", foot, 0.13, 0.05, "gold")
    beam(shell, name + "_stem", foot + UP * 0.05, foot + UP * (0.14 + r * 0.3), 0.05, "gold")
    c = foot + UP * (0.16 + r)
    n = 10
    for k, R in enumerate((EYE, rx(math.pi / 2), rz(0.41) @ rx(math.pi / 2) @ ry(0.0))):
        pts = [c + R @ v3(r * math.cos(2 * math.pi * i / n), 0, r * math.sin(2 * math.pi * i / n)) for i in range(n)]
        for i in range(n):
            beam(det if k else shell, "%s_ring_%d_%d" % (name, k, i), pts[i], pts[(i + 1) % n], 0.03, "gold", extend=0.012)
    add_cube(shell, name + "_globe", c, ry(0.4), (r * 0.7, r * 0.7, r * 0.7), "b_globe", stretch=True)
    beam(det, name + "_axis", c - rz(0.41) @ UP * (r * 1.15), c + rz(0.41) @ UP * (r * 1.15), 0.025, "gold")


def gold_bars(bone, name, foot, n=3, yaw=0.0):
    """A small pyramid of gold ingots."""
    foot = v3(*foot)
    R = ry(yaw)
    k = 0
    for layer, cnt in enumerate((n, n - 1)):
        for i in range(cnt):
            dx = (i - (cnt - 1) / 2) * 0.13
            add_cube(bone, "%s_%d" % (name, k), foot + R @ v3(dx, 0.035 + 0.06 * layer, 0), R, (0.11, 0.06, 0.2), "gold_ingot", stretch=True)
            k += 1


def potion_rows(det, name, levels, rng, colours, glow_every=3, skip=None):
    """Potion bottles on shelf boards (x0, x1, y, z_front, z_back): a row per level (props_m1.bottle_row; the
    bottles glow)."""
    for i, (x0, x1, y, zf, zb) in enumerate(levels):
        if skip and i in skip:
            continue
        p1.bottle_row(det, "%s_%d" % (name, i), x0 + 0.03, x1 - 0.03, y, (zf + zb) / 2, rng, colours, rmin=0.06, rmax=0.085, gap=0.05)


def planter(shell, det, name, foot, w=0.7, d=0.5, h=0.45, plant="flowers_purple", n=3, solid=True):
    """A wooden planter crate (crate region) full of soil with flowers (crossed cut-out planes)."""
    foot = v3(*foot)
    ml.crate(shell, name, foot, size=(w, h, d), solid=solid, content="soil")
    for i in range(n):
        x = foot[0] + (i - (n - 1) / 2) * (w / n)
        wb.crossed(det, "%s_pl_%d" % (name, i), (x, foot[1] + h + 0.16, foot[2]), 0.36, 0.36, plant, yaw=0.3 * i)


def wheat_bundle(det, name, foot, h=0.6, w=0.36):
    foot = v3(*foot)
    wb.crossed(det, name, foot + UP * (h / 2), w, h, "b_wheat")


def produce_crate(shell, name, foot, size=(0.7, 0.42, 0.55), content="apples", yaw=0.0, solid=True):
    ml.crate(shell, name, foot, size=size, yaw=yaw, solid=solid, content=content)


def cheese_pile(bone, name, foot, n=3):
    foot = v3(*foot)
    for k in range(n):
        dx = (k - (n - 1) / 2) * 0.2
        add_cube(bone, "%s_%d" % (name, k), foot + v3(dx, 0.09, 0.03 * (k % 2)), ry(0.3 * k), (0.18, 0.18, 0.18), "b_cheese", stretch=True)
    if n >= 3:
        add_cube(bone, name + "_top", foot + v3(0, 0.27, 0), ry(0.6), (0.17, 0.17, 0.17), "b_cheese", stretch=True)


def guy_stake(shell, det, name, x, z, h=0.55, region="b_post", gold=False):
    """A short squared stake post the guy ropes are tied to (a band near the top)."""
    beam(shell, name, (x, 0.0, z), (x, h, z), 0.2, {"all": region, "+1": "end_grain", "-1": "end_grain"})
    band(det, name + "_band", x, z, 0.115, h - 0.2, 0.09, region="gold" if gold else "b_band")


def lantern_icon_dot(p, x, y):
    p[x, y] = (255, 210, 110, 255)


def stall_icon(path, roof="pyramid", emblem_col=GOLD, extra=None):
    """16x16 item icon in the group's blue and cream: roof "pyramid" (pointed, a flag), "dome" (rounded marquee, gold
    finial) or "ridge" (short ridge with two posts); the dark inside with a gold emblem on a blue banner."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    wood, wood_d = (150, 98, 52, 255), (90, 56, 26, 255)
    for y in range(2, 9):
        if roof == "pyramid":
            half = 1 + (y - 2) * 1.05
        elif roof == "dome":
            half = 2.2 + 5.6 * math.sin(min(1.0, (y - 1.5) / 7.0) * math.pi / 2)
        else:
            half = 3 + (y - 2) * 0.75
        for x in range(16):
            dx = x - 7.5
            if abs(dx) <= half:
                s = int((dx / max(half, 0.5)) * 3 + 3.5) % 2
                c = NAVY if s == 0 else CREAM
                if abs(abs(dx) - half) < 0.6:
                    c = _scale(c, 0.75)
                p[x, y] = c + (255,)
    for x in range(1, 15):
        p[x, 9] = (CREAM if (x // 2) % 2 else NAVY) + (255,)
        if x % 2 == 0:
            p[x, 10] = GOLD + (255,)
    for y in range(9, 16):
        for x in (1, 14):
            p[x, y] = wood if x == 1 else wood_d
    for y in range(11, 15):
        for x in range(2, 14):
            p[x, y] = (46, 32, 22, 255)
    for y in range(10, 14):
        for x in (6, 7, 8, 9):
            if y < 13 or x in (7, 8):
                p[x, y] = NAVY + (255,)
    p[7, 11] = p[8, 11] = emblem_col + (255,)
    p[7, 12] = _scale(emblem_col, 0.8) + (255,)
    for x in range(2, 14):
        p[x, 15] = (70, 80, 150, 255)
    if roof == "pyramid":
        for y in range(0, 3):
            p[7, y] = wood_d
        p[8, 0] = p[9, 0] = NAVY + (255,)
        p[8, 1] = p[9, 1] = GOLD + (255,)
    elif roof == "dome":
        p[7, 0] = p[8, 0] = GOLD + (255,)
        p[7, 1] = p[8, 1] = GOLD_D + (255,)
    else:
        for y in range(0, 3):
            p[4, y] = wood
            p[11, y] = wood
    if extra:
        extra(p)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
