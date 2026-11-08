"""Props of the market tents of group A (1.26.0, Lion Port): tente_lion_pavillon, tente_lion_longue, tente_imperiale.

The three tents are royal blue, cream and gold, with the golden lion of Lion Port. This module holds what they share
(merchantlib and tentlib are used as they are, never edited):

  - the palette (BLUE / CREAM / GOLD) and setup(name), which points merchantlib's shell colours at it for this process
    (the shell regions "cloth", "cloth_beige", "trim_gold"... then match the tent);
  - heraldry painted at 8x and reduced to crisp pixel art: the lion rampant, the fleur-de-lis, the cross fleury;
  - region painters (each returns painter(img) for merchantlib's Atlas.add): striped cloth / gores with soft folds,
    dagged valances (square tabs edged in gold, pointed tabs), the gold valance with blue fleurs-de-lis, lion banners
    (V point, fringe, dagged), the lion crest shield, cream pennants, the blue rug with gold scrolls or a lion medallion,
    the dagged counter cloth, drapes and curtains, stone, book spines, cloth-roll ends, a map, chest wood;
  - geometry: posts on stone feet with iron bands, the bell-shaped hipped roof (gores), valances, tied-back drapes,
    hanging walls, pennant bunting, triangular cut-out plates (gables), chests, books, cloth rolls, potions, gold
    bars, hanging brass scales, ivy planters, lantern brackets.

    import props_a as pa
    pa.setup("tente_x")                       # ml.setup + palette
    atlas = ml.Atlas("tente_x", colour="blue")
    pa.add_regions(atlas, "pv", ["roof", "valance", ...])   # regions "<prefix>_<name>" from REGIONS
    ...
Coordinates: tent-local blocks (y up, +z = the open front, the anchor block's centre at (0, 0, 0) on the ground).
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "merchant"))
sys.path.insert(0, os.path.join(HERE, "..", "tents"))
import merchantlib as ml  # noqa: E402

v3, norm, add_cube, beam, loft, Bone = ml.v3, ml.norm, ml.add_cube, ml.beam, ml.loft, ml.Bone
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ry, rx, rz = ml.ry, ml.rx, ml.rz
collide = ml.collide
_rgb, _jitter, _scale, _mix = ml._rgb, ml._jitter, ml._scale, ml._mix

# ---------------------------------------------------------------- palette (the pictures' royal blue, warm cream, orange gold)
BLUE, BLUE_D, BLUE_L = _rgb("323f92"), _rgb("1a2160"), _rgb("4a5cbc")
CREAM, CREAM_D, CREAM_L = _rgb("eedbb2"), _rgb("bfa27a"), _rgb("faf0d6")
GOLD, GOLD_D, GOLD_L = _rgb("eba52e"), _rgb("8c5410"), _rgb("ffd774")
CLEAR = (0, 0, 0, 0)


def setup(name):
    """ml.setup(name) + merchantlib's shell colours pointed at this palette (process-local, the library is untouched)."""
    ml.setup(name)
    ml.COLOURS["blue"] = (BLUE, BLUE_D, BLUE_L)
    ml.BEIGE = CREAM
    ml.GOLD, ml.GOLD_DARK = GOLD, GOLD_D


# ================================================================ heraldry (masks drawn at 8x, reduced, outlined)
def _mask(draw, w, h, S=8, thr=118):
    """A w x h boolean mask (numpy) of the shape drawn by draw(d, P) in unit coordinates (x right, y down)."""
    from PIL import Image, ImageDraw
    big = Image.new("L", (w * S, h * S), 0)
    d = ImageDraw.Draw(big)
    W, H = w * S, h * S

    def P(x, y):
        return (x * W, y * H)
    draw(d, P, W)
    small = big.resize((w, h), Image.LANCZOS)
    return np.asarray(small) > thr


def _lion_draw(d, P, W):
    """A lion rampant facing left (the viewer's left), heraldic: raised fore paws, jagged mane, tail curled up."""
    def line(pts, wd):
        d.line([P(*p) for p in pts], fill=255, width=max(1, int(wd * W)), joint="curve")
        for p in (pts[0], pts[-1]):
            r = wd * W / 2
            x, y = P(*p)
            d.ellipse((x - r, y - r, x + r, y + r), fill=255)

    def disc(x, y, rx_, ry_):
        (a, b), (c, e) = P(x - rx_, y - ry_), P(x + rx_, y + ry_)
        d.ellipse((a, b, c, e), fill=255)
    d.polygon([P(0.37, 0.28), P(0.53, 0.25), P(0.66, 0.41), P(0.72, 0.6), P(0.63, 0.72), P(0.47, 0.65), P(0.39, 0.47)], fill=255)
    cx, cy = 0.38, 0.21
    pts = [P(cx, cy)]
    for k in range(15):
        a = math.radians(-125 + k * 16.5)
        r = 0.155 if k % 2 == 0 else 0.11
        pts.append(P(cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=255)
    disc(0.31, 0.2, 0.085, 0.08)
    disc(0.22, 0.24, 0.06, 0.047)
    d.polygon([P(0.32, 0.11), P(0.36, 0.035), P(0.4, 0.115)], fill=255)
    d.polygon([P(0.17, 0.25), P(0.23, 0.27), P(0.2, 0.31)], fill=255)          # the tongue
    line([(0.45, 0.33), (0.32, 0.3), (0.21, 0.2)], 0.075)
    disc(0.18, 0.17, 0.05, 0.045)
    line([(0.45, 0.43), (0.31, 0.47), (0.2, 0.42)], 0.07)
    disc(0.17, 0.41, 0.045, 0.04)
    line([(0.53, 0.6), (0.43, 0.74), (0.34, 0.87)], 0.095)
    line([(0.34, 0.88), (0.21, 0.9)], 0.06)
    line([(0.64, 0.64), (0.69, 0.8), (0.63, 0.93)], 0.095)
    line([(0.63, 0.94), (0.51, 0.96)], 0.06)
    line([(0.7, 0.58), (0.8, 0.53), (0.87, 0.41), (0.83, 0.28)], 0.045)
    d.polygon([P(0.83, 0.3), P(0.77, 0.22), P(0.8, 0.11), P(0.86, 0.17), P(0.9, 0.09), P(0.92, 0.22), P(0.88, 0.3)], fill=255)


def _fdl_draw(d, P, W):
    """A fleur-de-lis: tall middle petal, two curling side petals, the band, three small lobes below."""
    d.polygon([P(0.5, 0.02), P(0.6, 0.15), P(0.63, 0.32), P(0.58, 0.5), P(0.5, 0.6), P(0.42, 0.5), P(0.37, 0.32), P(0.4, 0.15)], fill=255)
    for s in (1, -1):
        def Q(x, y, s=s):
            return P(0.5 + s * (x - 0.5), y)
        d.polygon([Q(0.45, 0.6), Q(0.36, 0.42), Q(0.24, 0.29), Q(0.1, 0.29), Q(0.02, 0.4), Q(0.05, 0.53), Q(0.15, 0.56),
                   Q(0.13, 0.45), Q(0.2, 0.43), Q(0.3, 0.52), Q(0.38, 0.65)], fill=255)
        d.polygon([Q(0.41, 0.67), Q(0.3, 0.78), Q(0.19, 0.83), Q(0.23, 0.73), Q(0.33, 0.67)], fill=255)
    d.rectangle([P(0.27, 0.58), P(0.73, 0.68)], fill=255)
    d.polygon([P(0.42, 0.67), P(0.58, 0.67), P(0.56, 0.8), P(0.5, 0.93), P(0.44, 0.8)], fill=255)


def _cross_draw(d, P, W):
    """A cross fleury: four arms ending in trefoils."""
    d.rectangle([P(0.42, 0.14), P(0.58, 0.86)], fill=255)
    d.rectangle([P(0.14, 0.42), P(0.86, 0.58)], fill=255)
    for (ex, ey, ux, uy) in ((0.5, 0.12, 0, -1), (0.5, 0.88, 0, 1), (0.12, 0.5, -1, 0), (0.88, 0.5, 1, 0)):
        for (along, perp, r) in ((0.0, 0.0, 0.085), (-0.06, 0.1, 0.07), (-0.06, -0.1, 0.07)):
            cx, cy = ex + ux * along + uy * perp, ey + uy * along + ux * perp
            (a, b), (c, e) = P(cx - r, cy - r), P(cx + r, cy + r)
            d.ellipse((a, b, c, e), fill=255)
    (a, b), (c, e) = P(0.36, 0.36), P(0.64, 0.64)
    d.ellipse((a, b, c, e), fill=255)


def _scales_draw(d, P, W):
    """A balance (the merchant's scales): post, beam, two hanging pans."""
    d.rectangle([P(0.47, 0.12), P(0.53, 0.86)], fill=255)
    d.rectangle([P(0.3, 0.84), P(0.7, 0.92)], fill=255)
    d.rectangle([P(0.1, 0.2), P(0.9, 0.26)], fill=255)
    (a, b), (c, e) = P(0.43, 0.06), P(0.57, 0.18)
    d.ellipse((a, b, c, e), fill=255)
    for cx in (0.18, 0.82):
        d.line([P(cx, 0.24), P(cx - 0.13, 0.55)], fill=255, width=max(1, int(0.03 * W)))
        d.line([P(cx, 0.24), P(cx + 0.13, 0.55)], fill=255, width=max(1, int(0.03 * W)))
        d.chord([P(cx - 0.17, 0.42), P(cx + 0.17, 0.66)], 0, 180, fill=255)


HERALDRY = {"lion": _lion_draw, "fdl": _fdl_draw, "cross": _cross_draw, "scales": _scales_draw}


def stamp(img, box, kind, fill=GOLD, outline=GOLD_D, light=GOLD_L, rng=None, flip=False, eye=True):
    """Paints the emblem `kind` (lion, fdl, cross, scales) in box (x, y, w, h) of a PIL image: a light-to-dark fill and
    a dark outline round it; flip mirrors it (the lion then faces right)."""
    x0, y0, w, h = (int(round(v)) for v in box)
    if w < 3 or h < 3:
        return
    m = _mask(HERALDRY[kind], w, h)
    if flip:
        m = m[:, ::-1]
    px = img.load()
    rng = rng or random.Random(5)
    H_, W_ = m.shape
    dil = m.copy()
    dil[1:, :] |= m[:-1, :]
    dil[:-1, :] |= m[1:, :]
    dil[:, 1:] |= m[:, :-1]
    dil[:, :-1] |= m[:, 1:]
    for y in range(H_):
        for x in range(W_):
            X_, Y_ = x0 + x, y0 + y
            if not (0 <= X_ < img.size[0] and 0 <= Y_ < img.size[1]):
                continue
            if m[y, x]:
                # light on the upper left of each part (a pixel with free space above-left), dark below-right
                edge_tl = (y == 0 or not m[y - 1, x]) or (x == 0 or not m[y, x - 1])
                edge_br = (y == H_ - 1 or not m[y + 1, x]) or (x == W_ - 1 or not m[y, x + 1])
                c = light if edge_tl and w >= 12 else (_scale(fill, 0.8) if edge_br and w >= 12 else fill)
                px[X_, Y_] = _jitter(c, rng, 7) + (255,)
            elif dil[y, x]:
                px[X_, Y_] = _jitter(outline, rng, 4) + (255,)
    if kind == "lion" and eye and w >= 16:
        ex = x0 + int(round((0.7 if flip else 0.3) * w))
        ey = y0 + int(round(0.185 * h))
        if 0 <= ex < img.size[0] and 0 <= ey < img.size[1]:
            px[ex, ey] = (50, 26, 10, 255)


# ================================================================ cloth painting
def weave(img, c, rng, stains=1, box=None):
    w, h = img.size
    ml._weave(img, box or (0, 0, w, h), c, rng, stains=stains)


def _fold(x, period, depth=0.13):
    """Soft fold shading across a stripe / fold of `period` px: light in the middle, darker at the creases."""
    f = (x % period) / period
    return 1.0 - depth + depth * 1.6 * math.sin(math.pi * f) - 0.12 * (min(f, 1 - f) < 0.06)


def stripes(colours, n, seed, seam=None, fold=0.13, shade=(0.9, 1.05), stains=1):
    """n vertical stripes across the image in `colours` taken in turn, a weave, soft folds (light in the middle of each
    stripe, darker at the seams), a slight shade from top to bottom; seam = a colour for a thin seam line (gold)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        edges = [int(round(k * w / n)) for k in range(n + 1)]
        for k in range(n):
            weave(img, colours[k % len(colours)], rng, stains=stains, box=(edges[k], 0, max(1, edges[k + 1] - edges[k]), h))
        px = img.load()
        sw = w / n
        for y in range(h):
            sh = shade[0] + (shade[1] - shade[0]) * (y / max(1, h - 1))
            for x in range(w):
                r, g, b, a = px[x, y]
                k = sh * _fold(x, sw, fold)
                px[x, y] = _scale((r, g, b), k) + (255,)
        if seam is not None:
            for e in edges[1:-1]:
                for y in range(h):
                    px[min(w - 1, e), y] = _jitter(seam, rng, 8) + (255,)
    return p


def dag_valance(n, seed, cloth=BLUE, edge=GOLD, shape="square", band=0.48, top=GOLD, alt=None, emblem=None):
    """A dagged valance: a cloth band (a gold top line), n tabs below edged in gold, cut out between them. shape:
    square (crenel tabs), point (pennant tabs), round (scallops). alt: a second cloth colour for every other tab;
    emblem: a small gold emblem in each tab (fdl, cross)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, cloth, rng)
        px = img.load()
        tw = w / n
        b = int(h * band)
        for x in range(w):
            k = int(x // tw)
            lx = (x - k * tw) / tw
            col = alt if (alt is not None and k % 2 == 1) else cloth
            for y in range(h):
                ty = (y - b) / max(1, h - b)    # 0 at the band's bottom, 1 at the tabs' tips
                if shape == "square":
                    inside = y <= b or 0.14 <= lx <= 0.86
                    border = (y > b and (abs(lx - 0.14) * tw < 1.6 or abs(lx - 0.86) * tw < 1.6)) or y >= h - 2
                elif shape == "point":
                    half = 0.5 * (1 - ty)
                    inside = y <= b or abs(lx - 0.5) <= half
                    border = y > b and abs(lx - 0.5) > half - 1.8 / tw
                else:  # round
                    rr = 0.5
                    dy = ty * 1.0
                    inside = y <= b or (lx - 0.5) ** 2 + (dy * 0.9) ** 2 <= rr * rr
                    border = y > b and abs(math.hypot(lx - 0.5, dy * 0.9) - rr) * tw < 1.7
                if not inside:
                    px[x, y] = CLEAR
                    continue
                c = col
                if y < 2:
                    c = top if y == 1 else _scale(top, 0.6)
                elif y == b and not (shape == "square" and 0.14 <= lx <= 0.86):
                    c = edge
                elif border:
                    c = edge
                elif y > b:
                    c = _scale(col, 1.0 + 0.08 * (0.5 - lx))
                else:
                    c = _scale(col, 0.94 + 0.08 * math.sin(math.pi * lx))
                px[x, y] = _jitter(c, rng, 6) + (255,)
        if emblem:
            s = int(min(tw * 0.55, (h - b) * 0.8))
            for k in range(n):
                cx = int(k * tw + tw / 2 - s / 2)
                stamp(img, (cx, b + max(1, int((h - b - s) * 0.3)), s, s), emblem, rng=rng)
    return p


def gold_valance(n, seed, glyph="fdl", glyph_col=BLUE, teeth=None):
    """The imperial valance: a gold band with a row of blue glyphs (fleurs-de-lis), dark-gold rules, square gold teeth
    below (cut out between them)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        b = int(h * 0.72)
        nt = teeth or n * 3
        tw = w / nt
        for y in range(h):
            for x in range(w):
                lx = (x % tw) / tw
                if y > b and not (0.2 <= lx <= 0.8):
                    px[x, y] = CLEAR
                    continue
                c = GOLD
                if y < 2 or y == b - 1:
                    c = GOLD_D
                elif y == 2 or y == b - 2:
                    c = GOLD_L
                elif y > b and (abs(lx - 0.2) * tw < 1.2 or abs(lx - 0.8) * tw < 1.2 or y == h - 1):
                    c = GOLD_D
                k = 1.0 + 0.05 * math.sin(x * 0.6)
                px[x, y] = _jitter(_scale(c, k), rng, 8) + (255,)
        gw = w / n
        s = int(min(gw * 0.6, b - 6))
        for k in range(n):
            stamp(img, (int(k * gw + gw / 2 - s / 2), 3 + (b - 6 - s) // 2, s, s), glyph, fill=glyph_col, outline=BLUE_D,
                  light=BLUE_L, rng=rng)
    return p


def torn_valance(seed, cloth=CREAM):
    """A worn cream under-valance: cloth with a ragged, torn bottom edge (cut out)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, cloth, rng, stains=2)
        px = img.load()
        bottom = [h * (0.45 + 0.5 * abs(math.sin(x * 0.37 + rng.random() * 0.4))) for x in range(w)]
        for x in range(w):
            for y in range(h):
                if y > bottom[x]:
                    px[x, y] = CLEAR
                else:
                    r, g, b, a = px[x, y]
                    px[x, y] = _scale((r, g, b), 0.9 + 0.12 * math.sin(math.pi * ((x % 9) / 9))) + (255,)
    return p


def banner(seed, field=BLUE, border=GOLD, emblem="lion", bottom="point", inner=None, emblem_col=GOLD, flip=False,
           box=(0.14, 0.12, 0.86, 0.64), fold=True):
    """A hanging banner: field, gold border (and an inner dark rule), the emblem, a shaped bottom (cut out):
    point (V), fringe (straight with a gold fringe), pointfringe (V with fringe), dagged (three teeth), swallow (a
    swallow-tail notch), flat."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, field, rng)
        px = img.load()
        bw = max(2, w // 14)
        body = h * (0.76 if bottom in ("point", "pointfringe") else 0.82 if bottom in ("dagged", "swallow") else 0.9)
        for y in range(h):
            for x in range(w):
                cx = abs(x + 0.5 - w / 2)
                if bottom in ("point", "pointfringe") and y >= body:
                    half = (w / 2) * (1 - (y - body) / (h - body))
                    if cx > half:
                        px[x, y] = CLEAR
                        continue
                    if cx > half - bw - 0.5:
                        px[x, y] = _jitter(border, rng, 8) + (255,)
                        if bottom == "pointfringe" and cx > half - 1.0 and (x % 2 == 0):
                            px[x, y] = _jitter(GOLD_L, rng, 8) + (255,)
                        continue
                elif bottom == "fringe" and y >= body:
                    if (x % 2 == 0) or y < body + 2:
                        px[x, y] = _jitter(GOLD if x % 4 else GOLD_L, rng, 10) + (255,)
                    else:
                        px[x, y] = CLEAR
                    continue
                elif bottom == "dagged" and y >= body:
                    lx = (x % (w / 3)) / (w / 3)
                    half = 0.5 * (1 - (y - body) / (h - body))
                    if abs(lx - 0.5) > half:
                        px[x, y] = CLEAR
                        continue
                    if abs(lx - 0.5) > half - 0.12:
                        px[x, y] = _jitter(border, rng, 8) + (255,)
                        continue
                elif bottom == "swallow" and y >= body:
                    notch = (y - body) / (h - body) * (w / 2)
                    if cx < notch:
                        px[x, y] = CLEAR
                        continue
                    if cx < notch + bw or x < bw or x >= w - bw:
                        px[x, y] = _jitter(border, rng, 8) + (255,)
                        continue
                e = min(x, w - 1 - x, y)
                if e < bw or (bottom == "flat" and y >= h - bw):
                    px[x, y] = _jitter(border, rng, 8) + (255,)
                elif e == bw and inner is not None:
                    px[x, y] = _jitter(inner, rng, 5) + (255,)
                elif fold:
                    r, g, b, a = px[x, y]
                    px[x, y] = _scale((r, g, b), 0.9 + 0.14 * math.sin(math.pi * (x + 0.5) / w)) + (255,)
        if emblem:
            x0, y0, x1, y1 = box
            stamp(img, (w * x0, h * y0, w * (x1 - x0), h * (y1 - y0)), emblem, fill=emblem_col, rng=rng, flip=flip)
    return p


def crest(seed, field=BLUE, rim=GOLD):
    """The lion crest: a heater shield (flat top, straight sides, curved to a point), gold rim, blue field, the lion."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, field, rng)
        px = img.load()
        rimw = max(2, w // 12)

        def half(y):
            t = y / h
            if t < 0.5:
                return w / 2
            u = (t - 0.5) / 0.5
            return (w / 2) * math.sqrt(max(0.0, 1 - u ** 1.6))
        for y in range(h):
            hw = half(y + 0.5)
            for x in range(w):
                cx = abs(x + 0.5 - w / 2)
                if cx > hw:
                    px[x, y] = CLEAR
                elif cx > hw - rimw or y < rimw:
                    c = GOLD_L if (y < 1 or cx > hw - 1) else GOLD
                    px[x, y] = _jitter(c, rng, 8) + (255,)
                elif cx > hw - rimw - 1 or y == rimw:
                    px[x, y] = _jitter(BLUE_D, rng, 4) + (255,)
                else:
                    r, g, b, a = px[x, y]
                    px[x, y] = _scale((r, g, b), 0.92 + 0.12 * math.sin(math.pi * (x + 0.5) / w)) + (255,)
        stamp(img, (w * 0.13, h * 0.1, w * 0.74, h * 0.66), "lion", rng=rng)
    return p


def pennant(seed, field=CREAM, border=GOLD, emblem="fdl", emblem_col=GOLD, dag=True):
    """A cream pennant hanging from its top: gold border, the emblem, the bottom cut in a point (dag)."""
    return banner(seed, field=field, border=border, emblem=emblem, bottom="point" if dag else "flat", emblem_col=emblem_col,
                  box=(0.2, 0.16, 0.8, 0.6))


def bunting_flag(seed, field, edge=GOLD, swallow=False):
    """A small bunting pennant (triangle, or swallow-tailed), a gold top hem."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, field, rng)
        px = img.load()
        for y in range(h):
            for x in range(w):
                cx = abs(x + 0.5 - w / 2)
                t = y / h
                if swallow:
                    inside = t < 0.65 or cx > (t - 0.65) / 0.35 * (w / 2)
                else:
                    inside = t < 0.45 or cx <= (w / 2) * (1 - (t - 0.45) / 0.55)
                if not inside:
                    px[x, y] = CLEAR
                elif y < 2:
                    px[x, y] = _jitter(edge, rng, 8) + (255,)
                elif x == 0 or x == w - 1:
                    px[x, y] = _jitter(_scale(field, 0.75), rng, 5) + (255,)
    return p


def lion_flag(seed, field=BLUE, edge=GOLD, tail=True):
    """A long pennon flag (along u): blue, gold border, a gold lion near the hoist, tapering to a swallow tail."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, field, rng)
        px = img.load()
        for y in range(h):
            for x in range(w):
                t = x / w
                half = (h / 2) * (1.0 if t < 0.4 else 1.0 - 0.55 * (t - 0.4) / 0.6)
                cy = abs(y + 0.5 - h / 2)
                notch = tail and t > 0.8 and cy < (t - 0.8) / 0.2 * (h * 0.32)
                if cy > half or notch:
                    px[x, y] = CLEAR
                elif cy > half - 2 or x < 2:
                    px[x, y] = _jitter(edge, rng, 8) + (255,)
                elif 0.4 < t and abs(cy - half * 0.3) < 0.6 and x % 6 < 3:
                    px[x, y] = _jitter(GOLD, rng, 8) + (255,)
        s = int(h * 0.82)
        stamp(img, (int(w * 0.06), (h - s) // 2, s, s), "lion", rng=rng, flip=True)
    return p


def rug(seed, field=BLUE, medallion=None, scrolls=True):
    """A rug: dark border, gold lines, gold scroll motifs in rows on the field (scrolls), or a big gold lion
    medallion (medallion="lion"), gold fringe dots on the short ends; reads from the front (top of the texture at -z)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, field, rng, stains=2)
        px = img.load()
        for y in range(h):
            for x in range(w):
                e = min(x, y, w - 1 - x, h - 1 - y)
                if e < 2:
                    c = GOLD if (y < 2 or y >= h - 2) and x % 3 == 0 else BLUE_D
                    px[x, y] = _jitter(c, rng, 6) + (255,)
                elif e in (3, 4) or e == 9:
                    px[x, y] = _jitter(GOLD, rng, 10) + (255,)
                elif 5 <= e <= 8:
                    if (x + y) % 6 < 2:
                        px[x, y] = _jitter(_mix(field, GOLD, 0.7), rng, 8) + (255,)
                    else:
                        px[x, y] = _jitter(BLUE_D, rng, 5) + (255,)
        if medallion:
            s = int(min(w, h) * 0.56)
            from PIL import ImageDraw
            d = ImageDraw.Draw(img)
            cx, cy = w // 2, h // 2
            d.ellipse((cx - s * 0.62, cy - s * 0.55, cx + s * 0.62, cy + s * 0.55), outline=GOLD + (255,), width=2)
            stamp(img, (cx - s // 2, cy - s // 2, s, s), medallion, rng=rng)
            # corner fleurs
            q = max(8, int(min(w, h) * 0.13))
            for (fx, fy) in ((14, 14), (w - 14 - q, 14), (14, h - 14 - q), (w - 14 - q, h - 14 - q)):
                stamp(img, (fx, fy, q, q), "fdl", rng=rng)
        elif scrolls == "lattice":
            # a dense gold lattice of curved lines (an arabesque) with a dot in each cell
            for y in range(12, h - 12):
                for x in range(12, w - 12):
                    v = math.sin(x * 0.42) + math.sin(y * 0.42)
                    c4 = math.cos(x * 0.42) + math.cos(y * 0.42)
                    if abs(v) < 0.2 or (abs(c4 - 2) < 0.12):
                        px[x, y] = _jitter(_scale(GOLD, 0.92), rng, 10) + (255,)
            for y in range(11, h - 11):
                for x in range(11, w - 11):
                    if min(x - 11, y - 11, w - 12 - x, h - 12 - y) == 0:
                        px[x, y] = _jitter(GOLD, rng, 8) + (255,)
        elif scrolls:
            # gold scroll / leaf motifs in staggered rows
            motif = ("0110110", "1001001", "1011101", "0101010", "0011100")
            for r_, cy in enumerate(range(18, h - 14, 16)):
                for cx in range(18 + (r_ % 2) * 9, w - 16, 18):
                    for j, row in enumerate(motif):
                        for i, ch in enumerate(row):
                            if ch == "1":
                                px[cx + i - 3, cy + j - 2] = _jitter(GOLD, rng, 12) + (255,)
            for y in range(13, h - 13):
                for x in range(13, w - 13):
                    if min(x - 13, y - 13, w - 14 - x, h - 14 - y) == 0:
                        px[x, y] = _jitter(_scale(GOLD, 0.9), rng, 8) + (255,)
    return p


def counter_cloth(seed, n_dags=3, emblem="fdl", field=BLUE):
    """The counter's hanging cloth: blue, a gold border, n pointed dags along the bottom (cut out), a gold emblem in
    each dag."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, field, rng)
        px = img.load()
        body = int(h * 0.42)
        tw = w / n_dags
        for y in range(h):
            for x in range(w):
                lx = (x % tw) / tw
                if y > body:
                    half = 0.5 * (1 - (y - body) / (h - body))
                    if abs(lx - 0.5) > half:
                        px[x, y] = CLEAR
                        continue
                    if abs(lx - 0.5) > half - 2.2 / tw:
                        px[x, y] = _jitter(GOLD, rng, 8) + (255,)
                        continue
                if y < 2 or (y <= body and (x < 2 or x >= w - 2)):
                    px[x, y] = _jitter(GOLD, rng, 8) + (255,)
                elif y in (3, body - 1):
                    px[x, y] = _jitter(GOLD, rng, 10) + (255,)
        s = int(min(tw * 0.5, (h - body) * 0.62))
        for k in range(n_dags):
            stamp(img, (int(k * tw + tw / 2 - s / 2), body + 1, s, s), emblem, rng=rng)
    return p


def drape(seed, cloth=CREAM, pattern=GOLD, hem=GOLD, folds=4, motif="fdl"):
    """A drape: soft vertical folds, a faint pattern of small motifs (fleurs) in rows, a gold hem at the bottom."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, cloth, rng)
        px = img.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                k = _fold(x, w / folds, 0.18)
                if y >= h - 3:
                    px[x, y] = _jitter(hem if y >= h - 2 else _scale(hem, 0.7), rng, 8) + (255,)
                else:
                    px[x, y] = _scale((r, g, b), k) + (255,)
        if motif and pattern:
            s = max(5, w // 5)
            for j, cy in enumerate(range(4, h - s - 4, s * 2)):
                for cx in range(2 + (j % 2) * s, w - s, s * 2):
                    stamp(img, (cx, cy, s, s), motif, fill=_mix(cloth, pattern, 0.75), outline=_mix(cloth, pattern, 0.35),
                          light=_mix(cloth, pattern, 0.85), rng=rng)
    return p


def plain(seed, c, folds=0, depth=0.15, noise=True):
    def p(img):
        rng = random.Random(seed)
        weave(img, c, rng)
        if folds:
            w, h = img.size
            px = img.load()
            for y in range(h):
                for x in range(w):
                    r, g, b, a = px[x, y]
                    px[x, y] = _scale((r, g, b), _fold(x, w / folds, depth)) + (255,)
    return p


def stone(seed, base=_rgb("8e8c86")):
    """Grey dressed stone: noisy, a darker outline, a crack or two."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                e = min(x, y, w - 1 - x, h - 1 - y)
                k = 0.72 if e == 0 else 1.12 if (e == 1 and (x < 2 or y < 2)) else 1.0
                k *= 1.0 + 0.06 * math.sin(x * 1.3 + y * 0.7) + 0.04 * rng.random()
                px[x, y] = _jitter(_scale(base, k), rng, 6) + (255,)
        for _ in range(2):
            x, y = rng.randrange(3, w - 3), rng.randrange(3, h - 3)
            for k in range(rng.randrange(3, 7)):
                if 0 <= x < w and 0 <= y < h:
                    px[x, y] = _scale(base, 0.6) + (255,)
                x += rng.choice((-1, 0, 1))
                y += 1
    return p


def books(seed):
    """A row of book spines (u along the row): leather colours, gold bands, a lighter top line."""
    cols = [_rgb(c) for c in ("8e2420", "2c3c8c", "5a3418", "1e5a34", "7a1a40", "c8a050", "3a2a5a", "a03a1a")]

    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        x = 0
        while x < w:
            bw = rng.randint(3, 6)
            c = rng.choice(cols)
            top = rng.randint(0, max(0, h // 4))
            for xx in range(x, min(w, x + bw)):
                for y in range(h):
                    if y < top:
                        px[xx, y] = CLEAR
                        continue
                    k = 0.8 if xx == x + bw - 1 else (1.15 if xx == x else 1.0)
                    cc = _scale(c, k)
                    if (y - top) in (2, h - 4) or (y - top) == (h - top) // 2:
                        cc = GOLD
                    px[xx, y] = _jitter(cc, rng, 5) + (255,)
            x += bw
    return p


def roll_end(seed, c, core=CREAM):
    """The end of a cloth roll: a spiral of the cloth's colour round a light core."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        cx, cy = (w - 1) / 2, (h - 1) / 2
        for y in range(h):
            for x in range(w):
                r = math.hypot(x - cx, y - cy) / (w / 2)
                a = math.atan2(y - cy, x - cx)
                spiral = (r * 5 + a / (2 * math.pi)) % 1.0
                c2 = core if r < 0.2 else (_scale(c, 0.65) if spiral < 0.2 else c)
                px[x, y] = _jitter(c2, rng, 6) + (255,)
    return p


def parchment(seed, kind="map"):
    """An open map / document: parchment, darker edges, ink lines (coast lines, a compass rose) or text lines."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        base = _rgb("e8d4a4")
        for y in range(h):
            for x in range(w):
                e = min(x, y, w - 1 - x, h - 1 - y)
                k = 0.78 if e == 0 else 0.9 if e == 1 else 1.0
                px[x, y] = _jitter(_scale(base, k * (0.96 + 0.06 * math.sin(x * 0.4 + y * 0.3))), rng, 5) + (255,)
        ink = (110, 70, 36, 255)
        if kind == "map":
            for k in range(3):
                x, y = rng.randrange(3, w // 2), rng.randrange(3, h - 3)
                for i in range(w // 2):
                    if 1 < x < w - 2 and 1 < y < h - 2:
                        px[x, y] = ink
                    x += 1
                    y += rng.choice((-1, 0, 0, 1))
            cx, cy = int(w * 0.75), int(h * 0.35)
            for d in range(-3, 4):
                for (xx, yy) in ((cx + d, cy), (cx, cy + d)):
                    if 0 <= xx < w and 0 <= yy < h:
                        px[xx, yy] = (150, 40, 30, 255)
        else:
            for y in range(4, h - 3, 3):
                for x in range(3, w - 3 - rng.randrange(0, 6)):
                    if rng.random() < 0.7:
                        px[x, y] = ink
    return p


def post_wood(seed, base=_rgb("8a5a30"), dark=_rgb("4a2c14")):
    """Warm medium-brown post wood, grain along u (squared posts)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        ml.fine_wood(img, (0, 0, w, h), base, dark, h, rng, joints=False, knots=0.08, grain=0.14, shade=0.08)
    return p


def wood(seed, base=_rgb("7a4c26"), dark=_rgb("3e2410"), planks=4, joints=True):
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        ml.fine_wood(img, (0, 0, w, h), base, dark, max(4, h // planks), rng, joints=joints, knots=0.1, grain=0.12, shade=0.06)
    return p


def chest_wood(seed, base=_rgb("8a5426"), trim=GOLD):
    """A chest face: warm planks, gold corner plates (the bands are boxes)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        ml.fine_wood(img, (0, 0, w, h), base, _scale(base, 0.5), 8, rng, joints=False, knots=0.1, grain=0.12, shade=0.06)
        px = img.load()
        for y in range(h):
            for x in range(w):
                if (x < 4 or x >= w - 4) and (y < 4 or y >= h - 4):
                    px[x, y] = _jitter(trim, rng, 10) + (255,)
                elif min(x, y, w - 1 - x, h - 1 - y) == 0:
                    px[x, y] = _jitter(_scale(base, 0.55), rng, 5) + (255,)
    return p


# ================================================================ geometry
def box(bone, name, lo, hi, region, solid=False, stretch=True, u_dir=None, v_dir=None):
    return ml.box(bone, name, lo, hi, region, solid=solid, stretch=stretch, u_dir=u_dir, v_dir=v_dir)


def band(bone, name, x, z, half, y, h, region="iron"):
    box(bone, name, (x - half, y, z - half), (x + half, y + h, z + half), region)


def post(shell, det, name, x, z, top, d=0.36, stone_w=0.62, stone_h=0.5, bands=(1.3, 2.4), cap=0.5, cap_region="wood",
         finial=None, collide_top=None, stone_region="stone", post_region="post"):
    """A dark-wood post on a grey stone foot block: iron bands, a squared cap block on top, an optional gold finial
    (spike) above; collides from the ground to collide_top (default the top)."""
    if stone_w:
        box(shell, name + "_foot", (x - stone_w / 2, 0.0, z - stone_w / 2), (x + stone_w / 2, stone_h, z + stone_w / 2),
            {"all": stone_region}, stretch=True)
        box(det, name + "_foot_cap", (x - stone_w / 2 + 0.05, stone_h, z - stone_w / 2 + 0.05),
            (x + stone_w / 2 - 0.05, stone_h + 0.08, z + stone_w / 2 - 0.05), {"all": stone_region}, stretch=True)
    y0 = stone_h if stone_w else 0.0
    beam(shell, name, (x, y0, z), (x, top, z), d, {"all": post_region, "+1": "end_grain", "-1": "end_grain"})
    for k, y in enumerate(bands):
        band(det, "%s_band_%d" % (name, k), x, z, d / 2 + 0.025, y, 0.12)
    if cap:
        box(shell, name + "_cap", (x - cap / 2, top, z - cap / 2), (x + cap / 2, top + 0.2, z + cap / 2), {"all": cap_region, "+2": "end_grain"},
            stretch=False)
        box(det, name + "_cap_top", (x - cap / 2 + 0.07, top + 0.2, z - cap / 2 + 0.07), (x + cap / 2 - 0.07, top + 0.28, z + cap / 2 - 0.07),
            {"all": "wood_dark", "+2": "end_grain"}, stretch=False)
    if finial:
        ft = top + (0.28 if cap else 0.0)
        finial_spike(det if finial == "small" else shell, name + "_finial", (x, ft, z), h=0.55 if finial == "small" else 0.85)
    hw = max(d / 2, 0.2)
    collide((x - hw, 0.0, z - hw, x + hw, top if collide_top is None else collide_top, z + hw))


def finial_spike(bone, name, foot, h=0.8, w=0.22):
    """A gold finial: a collar, a bulb (two turned boxes), a pointed spike."""
    f = v3(*foot)
    add_cube(bone, name + "_collar", f + UP * 0.05, EYE, (w, 0.1, w), "gold")
    for k, a in enumerate((0.0, math.pi / 4)):
        add_cube(bone, "%s_bulb_%d" % (name, k), f + UP * (0.1 + h * 0.18), ry(a), (w * 0.85, h * 0.3, w * 0.85), "gold")
    add_cube(bone, name + "_neck", f + UP * (0.1 + h * 0.4), EYE, (w * 0.45, h * 0.14, w * 0.45), "gold")
    for k, (s, y) in enumerate(((0.6, 0.55), (0.38, 0.72), (0.18, 0.88))):
        add_cube(bone, "%s_spike_%d" % (name, k), f + UP * (0.1 + h * y), ry(math.pi / 4), (w * s, h * 0.18, w * s), "gold")


def bell(t, a=0.3, pw=2.0):
    """The roofs' profile: the fraction of the drop from the apex (t = 0) to the eave (t = 1); steep at the apex, flaring
    out flat at the eave (a bell); a higher pw makes the flare stronger (a more concave roof)."""
    return a * t + (1 - a) * (1 - (1 - t) ** pw)


def hip_roof(bone, name, apex, corners, region, nx=6, ny=6, a=0.3, droop=0.1, th=0.04, regions=None, bulge=0.0, pw=2.0):
    """A bell-shaped hipped (pyramid) roof: four faces from `apex` down to the eave corners (FL, FR, BR, BL in order),
    the cloth sagging between the hips; each face maps `region` (or regions[k]) across it (vertical stripes in the
    texture become gores converging at the apex). Returns roof_y(x, z) (the cloth height above a point inside)."""
    A = v3(*apex)
    C = [v3(*c) for c in corners]
    ey = C[0][1]

    def pt(c0, c1, s, t):
        e = c0 + (c1 - c0) * s
        if bulge:   # the eave bows out between the corners (a rounder marquee)
            mid = (c0 + c1) / 2 - A
            mid[1] = 0.0
            e = e + norm(mid) * (bulge * math.sin(math.pi * s))
        p = A * (1 - t) + e * t
        p[1] = A[1] - (A[1] - ey) * bell(t, a, pw) - droop * math.sin(math.pi * s) * math.sin(math.pi * t)
        return p
    for k in range(4):
        c0, c1 = C[k], C[(k + 1) % 4]
        loft(bone, "%s_%d" % (name, k), lambda s, t, c0=c0, c1=c1: pt(c0, c1, s, t), nx, ny, regions[k] if regions else region, th=th,
             overlap=0.02)

    def roof_y(x, z):
        # which face: compare |x| / W and |z| / D
        W, D = abs(C[1][0] - A[0]), abs(C[0][2] - A[2])
        dx, dz = x - A[0], z - A[2]
        t = max(abs(dx) / W, abs(dz) / D)
        return A[1] - (A[1] - ey) * bell(min(t, 1.0), a, pw)
    return roof_y


def valance(bone, name, c0, c1, out, h=0.56, region="valance", segs=None, flare=0.06, sag=0.0, bulge=0.0):
    """A valance hanging from the edge c0-c1 (its top), flaring out towards `out`; sag lowers its middle a little (a
    curved swag)."""
    c0, c1, out = v3(*c0), v3(*c1), v3(*out)
    L = np.linalg.norm(c1 - c0)
    n = segs or max(1, int(round(L / 1.2)))

    def V(s, t):
        e = c0 + (c1 - c0) * s - UP * (sag * math.sin(math.pi * s)) + out * (bulge * math.sin(math.pi * s))
        return e + UP * 0.03 - UP * (h * t) + out * (0.03 + flare * t)
    loft(bone, name, V, n, 1, region, th=0.025)


def drape_tied(bone, det, name, top_a, top_b, tie, bot_a, bot_b, normal, region, nx=3):
    """A curtain tied back: hangs from top_a - top_b, gathered at `tie` (a rope band), flaring again below to
    bot_a - bot_b; soft folds (ripples along `normal`)."""
    top_a, top_b, tie, bot_a, bot_b, n = (v3(*p) for p in (top_a, top_b, tie, bot_a, bot_b, normal))
    side = norm(top_b - top_a)

    def U(s, t):
        tt = t ** 0.85
        a = top_a + (top_b - top_a) * s
        b = tie + side * ((s - 0.5) * 0.16)
        return a * (1 - tt) + b * tt + n * (0.07 * math.sin(s * math.pi * 3) * (1 - t) + 0.05 * math.sin(math.pi * t))

    def Lw(s, t):
        a = tie + side * ((s - 0.5) * 0.16)
        b = bot_a + (bot_b - bot_a) * s
        return a * (1 - t) + b * t + n * (0.05 * math.sin(s * math.pi * 3 + 0.5) * t)
    loft(bone, name + "_up", U, nx, 3, region, th=0.03)
    loft(bone, name + "_lo", Lw, nx, 1, region, th=0.03)
    add_cube(det, name + "_tie", tie, np.column_stack([side, UP, np.cross(side, UP)]), (0.24, 0.08, 0.15), "rope")
    add_cube(det, name + "_tassel", tie - UP * 0.16 + n * 0.04, EYE, (0.06, 0.2, 0.06), "gold")


def wall(bone, name, a, b, y0, y1, out, region, nx=6, fold=0.05, ny=2):
    """A hanging canvas wall from a (left) to b on the ground line, y0..y1, soft vertical folds towards `out`."""
    a, b, out = v3(*a), v3(*b), v3(*out)

    def P(s, t):
        p = a + (b - a) * s
        return v3(p[0], y1 - (y1 - y0) * t, p[2]) + out * (fold * math.sin(s * math.pi * nx) * (0.4 + 0.6 * t))
    loft(bone, name, P, nx, ny, region, th=0.03)


def plate(bone, name, center, w, h, region, normal=(0, 0, 1), up=(0, 1, 0), th=0.02, edge=None):
    return ml.plate(bone, name, center, w, h, region, normal=normal, up=up, th=th, edge=edge)


def bunting(bone, det, name, a, b, n, regions, sag=0.3, size=(0.26, 0.42), rope_d=0.035):
    """A rope from a to b sagging by `sag`, n pennants hanging from it (regions taken in turn), facing the rope's normal."""
    a, b = v3(*a), v3(*b)
    ml.rope(det, name + "_rope", a, b, d=rope_d, sag=sag, segs=4)
    d = norm(b - a)
    nrm = norm(np.cross(d, UP))
    for i in range(n):
        t = (i + 0.5) / n
        p = a + (b - a) * t - UP * (4 * sag * t * (1 - t))
        plate(bone, "%s_%d" % (name, i), p - UP * (size[1] / 2 + 0.01), size[0], size[1], regions[i % len(regions)], normal=nrm, th=0.01)


def roof_plaque(bone, name, roof_y, x0, x1, z_top, z_eave, hang, region, offset=0.07, nx=2, ny=5, out=0.12):
    """A cloth plaque (a crest, a pennant) lying on a roof's front face from z_top down to the eave z_eave, then hanging
    straight down by `hang` in front of the valance; roof_y(x, z) = the roof cloth's height (hip_roof's return)."""
    def seg_len(xm):
        n = 8
        L = 0.0
        for i in range(n):
            za, zb = z_top + (z_eave - z_top) * i / n, z_top + (z_eave - z_top) * (i + 1) / n
            L += math.hypot(zb - za, roof_y(xm, zb) - roof_y(xm, za))
        return L
    L1 = seg_len((x0 + x1) / 2)
    t1 = L1 / (L1 + hang)

    def P(s, t):
        x = x0 + (x1 - x0) * s
        if t <= t1:
            z = z_top + (z_eave - z_top) * (t / t1)
            return v3(x, roof_y(x, z) + offset, z + 0.02)
        y0 = roof_y(x, z_eave) + offset
        u = (t - t1) / (1 - t1)
        return v3(x, y0 - hang * u, z_eave + 0.02 + out * min(1.0, u * 3.0))
    loft(bone, name, P, nx, ny, region, th=0.02, u_hint=X, v_hint=-UP)


def burlap(seed, base=_rgb("dcc49a")):
    """Pale burlap: a coarse weave, darker vertical fold streaks, lighter in the middle."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        ml._weave(img, (0, 0, w, h), base, rng, stains=0)
        px = img.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                k = 0.84 + 0.22 * math.sin(math.pi * (x + 0.5) / w) - 0.09 * (abs(math.sin(x * 0.55 + y * 0.08)) > 0.92)
                px[x, y] = _scale((r, g, b), k) + (255,)
    return p


def tri_painter(pts, n, seed, colours, dark=0.74, seam=None):
    """Paints a triangle (pts: apex, base_a, base_b in the unit square, y down) cut out of its rectangle, in n gores
    radiating from the apex (colours in turn), darker seams and edges."""
    (cx, cy), (ax, ay), (bx, by) = pts

    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        det_ = (ay - by) * (cx - bx) + (bx - ax) * (cy - by)
        for y in range(h):
            for x in range(w):
                X_, Y_ = (x + 0.5) / w, (y + 0.5) / h
                l1 = ((ay - by) * (X_ - bx) + (bx - ax) * (Y_ - by)) / det_
                l2 = ((by - cy) * (X_ - bx) + (cx - bx) * (Y_ - by)) / det_
                l3 = 1.0 - l1 - l2
                e = min(l1, l2, l3)
                if e < -0.004:
                    px[x, y] = CLEAR
                    continue
                base = l2 + l3
                sb = l3 / base if base > 1e-6 else 0.5
                k = min(n - 1e-6, max(0.0, sb * n))
                c = colours[int(k) % len(colours)]
                f = (0.86 + 0.18 * base) * (0.92 + 0.12 * math.sin(math.pi * (k % 1.0)))
                if (n > 1 and min(k % 1.0, 1.0 - k % 1.0) < 0.03 / max(base, 0.05)):
                    c = seam if seam is not None else c
                    f *= 1.0 if seam is not None else dark
                elif e < 0.014:
                    f *= dark
                px[x, y] = _jitter(_scale(c, f), rng, 5) + (255,)
    return p


def tri_plate(bone, atlas, name, apex, a, b, n=2, size=64, seed=0, colours=(BLUE, CREAM), th=0.03, seam=None, region=None):
    """A flat triangle apex-a-b as ONE plate cut out by its own texture (clean straight edges), painted in n gores from
    the apex; both faces textured. Adds its region "tri_<name>" to the atlas (or reuses `region`)."""
    A, B, C = v3(*a), v3(*b), v3(*apex)
    u = norm(B - A)
    nrm = norm(np.cross(B - A, C - A))
    vv = np.cross(nrm, u)
    uv = [(float(np.dot(q - A, u)), float(np.dot(q - A, vv))) for q in (C, A, B)]
    u0, u1 = min(q[0] for q in uv), max(q[0] for q in uv)
    v0, v1 = min(q[1] for q in uv), max(q[1] for q in uv)
    W, H = u1 - u0, v1 - v0
    unit = [((q[0] - u0) / W, (v1 - q[1]) / H) for q in uv]
    reg = region or "tri_" + name
    if reg not in atlas.regions:
        atlas.add(reg, size, max(16, int(size * H / W)), tri_painter(unit, n, seed, colours, seam=seam))
    centre = A + u * ((u0 + u1) / 2) + vv * ((v0 + v1) / 2)
    add_cube(bone, name, centre, np.column_stack([u, vv, nrm]), (W, H, th), {"all": None, "+3": reg, "-3": reg}, stretch=True,
             u_dir=u, v_dir=-vv)


def chest(shell, det, name, foot, w=0.9, d=0.6, h=0.62, yaw=0.0, region="chest", trim="gold", solid=True):
    """A trimmed chest: body, domed lid (two boxes), two vertical bands, a rim, a lock plate."""
    foot = v3(*foot)
    R = ry(yaw)
    add_cube(shell, name + "_body", foot + UP * (h * 0.36), R, (w, h * 0.72, d), {"all": region}, stretch=True)
    add_cube(shell, name + "_lid", foot + UP * (h * 0.8), R, (w + 0.02, h * 0.18, d + 0.02), {"all": region}, stretch=True)
    add_cube(shell, name + "_lid_top", foot + UP * (h * 0.94), R, (w, h * 0.12, d * 0.72), {"all": region}, stretch=True)
    for k, s in enumerate((-0.3, 0.3)):
        add_cube(det, "%s_band_%d" % (name, k), foot + R @ v3(s * w, h * 0.52, 0), R, (0.07, h * 1.0 + 0.02, d + 0.03), trim)
    add_cube(det, name + "_rim", foot + UP * (h * 0.71), R, (w + 0.04, 0.05, d + 0.04), trim)
    add_cube(det, name + "_lock", foot + R @ v3(0, h * 0.62, d / 2 + 0.02), R, (0.14, 0.18, 0.04), trim)
    if solid:
        hx = abs(math.cos(yaw)) * w / 2 + abs(math.sin(yaw)) * d / 2
        hz = abs(math.sin(yaw)) * w / 2 + abs(math.cos(yaw)) * d / 2
        collide((foot[0] - hx, foot[1], foot[2] - hz, foot[0] + hx, foot[1] + h, foot[2] + hz))


def book_stack(bone, name, foot, n=3, yaw=0.0, rng=None, w=0.32, d=0.24, th=0.07):
    """Books lying in a pile (leather colours, white page edges), each turned a little."""
    rng = rng or random.Random(3)
    foot = v3(*foot)
    regs = ("cloth_red", "cloth_blue", "leather", "leather_dark", "cloth_dark")
    y = 0.0
    for k in range(n):
        R = ry(yaw + rng.uniform(-0.25, 0.25))
        bw, bd, bt = w * rng.uniform(0.85, 1.1), d * rng.uniform(0.85, 1.1), th * rng.uniform(0.8, 1.3)
        add_cube(bone, "%s_%d" % (name, k), foot + UP * (y + bt / 2), R, (bw, bt, bd), {"all": "white", "+2": regs[(k + rng.randrange(5)) % 5],
                 "-2": regs[k % 5], "-1": regs[k % 5]})
        y += bt


def book_row(bone, name, x0, x1, y, z, depth=0.2, h=0.3, region="books", lean_end=True):
    """A row of upright books as one textured box (spines to the front), a leaning book at the end."""
    box(bone, name, (x0, y, z - depth / 2), (x1, y + h, z + depth / 2), {"all": "leather_dark", "+3": region, "+2": "white", "-3": "leather"},
        u_dir=X, v_dir=-UP)
    if lean_end:
        c = v3(x1 + 0.1, y + h * 0.42, z)
        add_cube(bone, name + "_lean", c, rz(-0.45), (0.07, h * 0.95, depth * 0.9), {"all": "cloth_red", "+2": "white"})


def cloth_roll(bone, name, c, length=0.9, r=0.12, yaw=0.0, region="cloth_blue", end=None):
    """A cloth roll lying on its side along yaw (an octagonal prism: two boxes turned 45 degrees), its ends `end`."""
    c = v3(*c)
    for k, a in enumerate((0.0, math.pi / 4)):
        add_cube(bone, "%s_%d" % (name, k), c, ry(yaw) @ rx(a), (length, 2 * r * 0.83, 2 * r * 0.83),
                 {"all": region, "+1": end or region, "-1": end or region}, stretch=True)


def potion_row(bone, name, x0, x1, y, z, colours, rng, n=None, glow_every=0):
    """Potion bottles standing in a row on a shelf (round, tall and flask shapes), colours taken in turn."""
    n = n or max(2, int((x1 - x0) / 0.2))
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        shape = ("round", "tall", "flask", "round")[(i + rng.randrange(4)) % 4]
        ml.bottle(bone, "%s_%d" % (name, i), (x, y, z + rng.uniform(-0.04, 0.04)), colours[i % len(colours)],
                  r=0.06 + 0.02 * rng.random(), h=0.15 + 0.07 * rng.random(), shape=shape, neck_h=0.06,
                  glow=bool(glow_every) and i % glow_every == 0)


def gold_bars(bone, name, foot, rows=2, yaw=0.0, bar=(0.3, 0.09, 0.13)):
    """A small pyramid of gold ingots on `foot` (rows of 3, 2, ...)."""
    foot = v3(*foot)
    R = ry(yaw)
    for r_ in range(rows):
        n = 3 - r_
        for i in range(n):
            off = R @ v3(0, bar[1] * (r_ + 0.5), (i - (n - 1) / 2) * (bar[2] + 0.02))
            add_cube(bone, "%s_%d_%d" % (name, r_, i), foot + off, R, bar, {"all": "gold_ingot"}, stretch=True)


def chain(bone, name, a, b, link=0.09, region="iron"):
    """A chain from a to b: alternating flat links (thin boxes turned 90 degrees)."""
    a, b = v3(*a), v3(*b)
    L = np.linalg.norm(b - a)
    n = max(1, int(L / link))
    d = norm(b - a)
    axes0 = ml.gg.frame_from(d, UP if abs(d[1]) < 0.9 else X)
    for k in range(n):
        c = a + d * (link * (k + 0.5))
        axes = axes0 if k % 2 == 0 else np.column_stack([axes0[:, 0], axes0[:, 2], -axes0[:, 1]])
        add_cube(bone, "%s_%d" % (name, k), c, axes, (link * 1.1, link * 0.55, 0.02), region)


def scales(bone, det, name, hook, span=0.6, drop=0.5, pan_drop=0.3, metal="gold"):
    """Hanging brass scales: a chain from the hook, the pivot, the beam with knobs and a pointer, two pans on three
    cords each."""
    h = v3(*hook)
    chain(det, name + "_chain", h, h - UP * (drop - 0.08), link=0.08, region=metal)
    piv = h - UP * drop
    add_cube(bone, name + "_ring", piv + UP * 0.05, EYE, (0.06, 0.08, 0.03), metal)
    beam(bone, name + "_beam", piv - X * span / 2, piv + X * span / 2, 0.035, metal)
    beam(det, name + "_pointer", piv, piv + UP * 0.15, 0.025, metal)
    for k, sx in enumerate((-1, 1)):
        end = piv + X * sx * span / 2
        add_cube(det, "%s_knob_%d" % (name, k), end, EYE, (0.05, 0.05, 0.05), metal)
        pan = end - UP * pan_drop
        for j, a in enumerate((0.0, 2.1, 4.2)):
            q = pan + v3(math.cos(a) * 0.1, 0.02, math.sin(a) * 0.1)
            beam(det, "%s_cord_%d_%d" % (name, k, j), end, q, 0.012, metal)
        ml.octo(bone, "%s_pan_%d" % (name, k), pan - UP * 0.02, 0.12, 0.035, {"all": metal})


def ivy_planter(shell, det, name, mount, out, w=0.6, rng=None):
    """A wooden planter box on an iron bracket (from the post point `mount` towards `out`), ivy spilling over and
    hanging down in strips."""
    m, o = v3(*mount), norm(v3(*out))
    c = m + o * (0.2 + w * 0.25)
    side = norm(np.cross(UP, o))
    R = np.column_stack([side, UP, np.cross(side, UP)])
    add_cube(shell, name + "_box", c, R, (w, 0.24, 0.32), {"all": "plank_dark", "+2": "ivy"}, stretch=True)
    beam(det, name + "_bracket", m - UP * 0.25, c - UP * 0.12, 0.04, "iron")
    for k in range(3):
        sp = (k - 1) * w * 0.32
        ml.vine(det, "%s_ivy_%d" % (name, k), c + side * sp + np.cross(side, UP) * 0.17 * (1 if k != 1 else -1) - UP * 0.05,
                0.6 + 0.25 * (k % 2), 0.3, normal=np.cross(side, UP) * (1 if k != 1 else -1))
    ml.crossed(det, name + "_leaves", c + UP * 0.22, w * 0.9, 0.3, "ivy")


def lantern_bracket(det, shell, name, mount, out, y_drop=0.5, size=0.36, arm=0.45):
    """An iron bracket arm from the post point `mount` out along `out`, a brace under it, and a lit lantern hanging
    from its tip."""
    m, o = v3(*mount), norm(v3(*out))
    tip = m + o * arm
    beam(det, name + "_arm", m, tip, 0.05, "iron", extend=0.02)
    beam(det, name + "_brace", m - UP * 0.35, tip - UP * 0.02, 0.04, "iron")
    add_cube(det, name + "_scroll", tip + UP * 0.06, EYE, (0.06, 0.12, 0.06), "iron")
    ml.lantern(shell, name, tip - UP * y_drop, size=size, metal="iron", chain_to=tip)


def rope_coil_post(det, name, x, z, y0, y1, d=0.36, turns=6):
    """A rope wound in a spiral round a squared post from y0 to y1 (small tilted rope boxes)."""
    n = turns * 2
    for k in range(n):
        y = y0 + (y1 - y0) * (k + 0.5) / n
        side = k % 4
        off = [v3(0, 0, d / 2 + 0.03), v3(d / 2 + 0.03, 0, 0), v3(0, 0, -d / 2 - 0.03), v3(-d / 2 - 0.03, 0, 0)][side]
        along = [X, -Z, -X, Z][side]
        axes = np.column_stack([along, UP, np.cross(along, UP)])
        add_cube(det, "%s_%d" % (name, k), v3(x, y, z) + off, axes @ rz(-0.35)[:3, :3], (d + 0.1, 0.08, 0.07), "rope")


def sack_big(shell, det, name, foot, yaw=0.0, w=0.62, h=0.9, region="sack"):
    """A big tied burlap sack: a bulging body narrowing upwards (octagonal), a tied neck, a flared top."""
    foot = v3(*foot)
    R = ry(yaw)
    for k, (y0, y1, s) in enumerate(((0.0, 0.12, 0.86), (0.12, 0.46, 1.0), (0.46, 0.66, 0.84), (0.66, 0.78, 0.6))):
        for j in range(2):
            q = 0.84 if j else 1.0
            add_cube(shell, "%s_%d_%d" % (name, k, j), foot + UP * (h * (y0 + y1) / 2), R @ ry(math.pi / 4 * j + 0.06 * k),
                     (w * s * q, h * (y1 - y0), w * s * q), region, stretch=True)
    add_cube(shell, name + "_neck", foot + UP * (h * 0.82), R, (w * 0.3, h * 0.08, w * 0.3), region, stretch=True)
    add_cube(det, name + "_tie", foot + UP * (h * 0.81), R, (w * 0.36, 0.06, w * 0.36), "rope")
    add_cube(shell, name + "_top", foot + UP * (h * 0.92), R @ ry(0.4), (w * 0.5, h * 0.14, w * 0.46), region, stretch=True)


def add_regions(atlas, prefix, specs):
    """Adds the regions specs = [(name, w, h, painter), ...] as "<prefix>_<name>"."""
    for name, w, h, painter in specs:
        atlas.add("%s_%s" % (prefix, name), w, h, painter)
