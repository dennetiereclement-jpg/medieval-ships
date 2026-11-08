"""Shared helpers of the group-D market tents (1.26.0): tente_balance_auvent and tente_balance_pignon.

Both are red / cream merchant tents with the gold SCALES (balance) emblem, built on merchantlib / tentlib (never edited:
what they need is copied or adapted here, as tools/tents/generate_tente_marchande.py does):

  - painters (PIL, for ml.Atlas.add): woven stripes with soft folds, the scales emblem, banners (V, stepped or shield
    point, corner stars, a diamond), dagged valances, a red-and-gold rug, the counter runner, warm wood, iron bands,
    golden finials, cut-out flowers and lavender, burlap, grain, an open book, a ribboned parcel, a gold-trimmed chest;
  - geometry: squared posts on foot blocks with riveted iron bands, a cap (wood or a gilded collar) and the small
    golden knob finial of the pictures, rope wraps and tassels, dagged valances, tied-back drapes, hanging canvas walls,
    a flower box, a chest, scrolls, an open book, a ribboned parcel, an open grain sack, a banner laid along a roof
    slope; loft_down(), a striped-roof variant of tentlib.loft whose strips keep the stripes straight down the slope;
  - shift_all(): moves the whole built tent (cubes, collision boxes, mod blocks) so that its extent is centred on the
    anchor block.

Coordinates as everywhere: tent-local blocks, y up (y = 0 = top of the ground block), +z = the open front.
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "merchant"))
import merchantlib as ml  # noqa: E402

v3, norm, add_cube, beam, loft, Bone = ml.v3, ml.norm, ml.add_cube, ml.beam, ml.loft, ml.Bone
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ry, rx, rz = ml.ry, ml.rx, ml.rz
box, collide = ml.box, ml.collide
_rgb, _jitter, _scale, _mix = ml._rgb, ml._jitter, ml._scale, ml._mix


class Pal:
    """A tent's palette: cream, red (main, dark, light), gold (main, dark, light), wood (main, dark), finial gold."""

    def __init__(self, cream, red, red_dark, red_light, gold, gold_dark, gold_light, wood, wood_dark, finial):
        self.cream, self.red, self.red_dark, self.red_light = _rgb(cream), _rgb(red), _rgb(red_dark), _rgb(red_light)
        self.gold, self.gold_dark, self.gold_light = _rgb(gold), _rgb(gold_dark), _rgb(gold_light)
        self.wood, self.wood_dark, self.finial = _rgb(wood), _rgb(wood_dark), _rgb(finial)


# ---------------------------------------------------------------- painting
def weave(img, c, rng, stains=1, box_=None):
    w, h = img.size
    ml._weave(img, box_ or (0, 0, w, h), c, rng, stains=stains)


def _harden(im):
    """Alpha to 0 / 255 (crisp pixel-art edges after a smooth downscale)."""
    a = im.getchannel("A").point(lambda q: 255 if q > 110 else 0)
    im.putalpha(a)
    return im


def stripes_painter(pal, widths, seed, fold=0.14, seam=True, light_bottom=0.12, top_dark=2, red_tone=None):
    """Stripes running down the image (u across, v from the ridge down): widths = [(fraction, "r" | "c" | "d"), ...]
    (red, cream, dark red); a soft fold in each stripe, dark seams between them, a little lighter at the bottom."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        tot = sum(f for f, _ in widths)
        edges, x = [0], 0.0
        for f, _ in widths:
            x += f / tot * w
            edges.append(int(round(x)))
        edges[-1] = w
        cols = {"r": red_tone or pal.red, "c": pal.cream, "d": pal.red_dark}
        for k, (f, c) in enumerate(widths):
            if edges[k + 1] > edges[k]:
                weave(img, cols[c], rng, stains=1, box_=(edges[k], 0, edges[k + 1] - edges[k], h))
        px = img.load()
        for k in range(len(widths)):
            x0, x1 = edges[k], edges[k + 1]
            for x in range(x0, x1):
                fx = (x - x0 + 0.5) / max(1, x1 - x0)
                kf = 1.0 - fold * 0.5 + fold * math.sin(math.pi * fx) * 0.9
                for y in range(h):
                    r, g, b, a = px[x, y]
                    kk = kf * (1.0 - light_bottom * 0.5 + light_bottom * (y / h))
                    if seam and (x == x0 or x == x1 - 1):
                        kk *= 0.8
                    if y < top_dark:
                        kk *= 0.78
                    px[x, y] = _scale((r, g, b), kk) + (255,)
    return paint


def draw_scales(img, box_, gold=(240, 168, 52), gold_d=(130, 70, 14), gold_l=(255, 222, 120), S=4):
    """The gold balance (scales) in box_ (x, y, w, h) of img: a stepped foot, a central post with a knob, the beam with
    curled ends, chains down to two pans."""
    from PIL import Image, ImageDraw
    x0, y0, w, h = box_
    W, H = w * S, h * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lw = max(S, int(W * 0.075))

    def P(x, y):
        return (W * x, H * y)

    def shape(fill, grow):
        g = grow * S
        # foot: two steps
        d.rectangle((W * 0.3 - g, H * 0.88 - g, W * 0.7 + g, H * 0.97 + g), fill=fill)
        d.rectangle((W * 0.4 - g, H * 0.8 - g, W * 0.6 + g, H * 0.9 + g), fill=fill)
        # post
        d.rectangle((W * 0.5 - lw / 2 - g, H * 0.12 - g, W * 0.5 + lw / 2 + g, H * 0.86 + g), fill=fill)
        # knob on top
        d.ellipse((W * 0.5 - lw * 1.1 - g, H * 0.03 - g, W * 0.5 + lw * 1.1 + g, H * 0.03 + lw * 2.2 + g), fill=fill)
        # beam, a little arched
        d.line([P(0.1, 0.27), P(0.5, 0.22), P(0.9, 0.27)], fill=fill, width=int(lw * 0.9 + 2 * g), joint="curve")
        for sx in (0.1, 0.9):
            d.ellipse((W * sx - lw * 0.7 - g, H * 0.27 - lw * 0.7 - g, W * sx + lw * 0.7 + g, H * 0.27 + lw * 0.7 + g), fill=fill)
            # chains (a V to the pan's rim)
            cw = max(S, int(lw * 0.42)) + int(2 * g)
            d.line([P(sx, 0.28), P(sx - 0.11, 0.56)], fill=fill, width=cw)
            d.line([P(sx, 0.28), P(sx + 0.11, 0.56)], fill=fill, width=cw)
            # pan: a shallow bowl
            d.chord((W * (sx - 0.15) - g, H * 0.47 - g, W * (sx + 0.15) + g, H * 0.67 + g), 0, 180, fill=fill)
    shape(gold_d, 1.0)
    shape(gold, 0.0)
    # highlights on the left of the post and the pans
    d.rectangle((W * 0.5 - lw / 2, H * 0.14, W * 0.5 - lw / 2 + max(S, lw // 3), H * 0.8), fill=gold_l)
    for sx in (0.1, 0.9):
        d.line([P(sx - 0.1, 0.58), P(sx + 0.02, 0.6)], fill=gold_l, width=max(S, lw // 3))
    im = _harden(im.resize((w, h), Image.LANCZOS))
    img.alpha_composite(im, (x0, y0))


def _star(px, cx, cy, c, cd):
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        px[cx + dx, cy + dy] = c + (255,)
    for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
        px[cx + dx, cy + dy] = cd + (255,)


def banner_painter(pal, seed, point="v", emblem="scales", border=3, stars=False, diamond=False, body=0.72, faded=False,
                   gold=None):
    """A red banner: gold border, a darker inner line, the bottom cut out as a V point ("v"), a stepped point ("step"),
    or a shield point with a gold rim ("shield"); the gold scales (emblem "scales"; faded = barely visible, darker),
    gold stars in the four corners, a gold diamond above the point."""
    def paint(img):
        rng = random.Random(seed)
        g = gold or pal.gold
        weave(img, pal.red, rng)
        w, h = img.size
        px = img.load()
        by = int(h * body)
        cx = (w - 1) / 2.0
        for y in range(h):
            for x in range(w):
                dx = abs(x - cx)
                if y >= by:
                    f = (y - by) / max(1, (h - by))
                    if point == "step":
                        half = (w / 2.0) * (1 - math.floor(f * 4.0 + 1e-6) / 4.0 * 0.92)
                    else:
                        half = (w / 2.0) * (1 - f)
                    if dx > half:
                        px[x, y] = (0, 0, 0, 0)
                        continue
                    if dx > half - border:
                        px[x, y] = _jitter(g, rng, 9) + (255,)
                        continue
                    if point == "step" and y < h - 1:
                        f2 = (y + 1 - by) / max(1, (h - by))
                        half2 = (w / 2.0) * (1 - math.floor(f2 * 4.0 + 1e-6) / 4.0 * 0.92)
                        if dx > half2 - border:
                            px[x, y] = _jitter(g, rng, 9) + (255,)
                            continue
                    if dx > half - border - 1:
                        px[x, y] = _jitter(pal.red_dark, rng, 5) + (255,)
                    continue
                if x < border or x >= w - border or y < border:
                    px[x, y] = _jitter(g, rng, 9) + (255,)
                elif x < border + 1 or x >= w - border - 1 or y < border + 1:
                    px[x, y] = _jitter(pal.red_dark, rng, 5) + (255,)
        if emblem == "scales":
            s = int(w * 0.72)
            ey = int(h * 0.16) if body < 0.8 else int(h * 0.2)
            if faded:
                draw_scales(img, ((w - s) // 2, ey, s, int(s * 1.05)), gold=_mix(pal.red, g, 0.45), gold_d=pal.red_dark,
                            gold_l=_mix(pal.red, g, 0.6))
            else:
                draw_scales(img, ((w - s) // 2, ey, s, int(s * 1.05)), gold=g, gold_d=pal.gold_dark, gold_l=pal.gold_light)
        if stars:
            for sx, sy in ((border + 4, border + 4), (w - border - 5, border + 4), (border + 4, int(h * 0.62)),
                           (w - border - 5, int(h * 0.62))):
                _star(px, sx, sy, g, pal.gold_dark)
        if diamond:
            dy0 = by + int((h - by) * 0.08)
            r = max(3, w // 9)
            for y in range(-r, r + 1):
                for x in range(-r, r + 1):
                    if abs(x) + abs(y) <= r and 0 <= dy0 + y < h:
                        c = g if abs(x) + abs(y) >= r - 1 or (x == 0 and y == 0) else pal.red_dark
                        px[int(cx) + x, dy0 + y] = _jitter(c, rng, 6) + (255,)
    return paint


def valance_painter(pal, seed, tabs, shape="square", band=0.42, edge=True, gold_edge=None, band_colour=None, band_line=None):
    """A dagged valance (cut-out): a band on top (band_colour "r" | "c" | "g" | "d", or None: each tab's own colour
    runs up into it), below it hanging tabs: tabs = [(width fraction, "r" | "c" | "g" | "d", length 0..1), ...] across
    the image; shape "square" (straight tabs) or "step" (stepped points); a dark line under the band, edges a shade
    darker; gold_edge = colour of a thin rim along the tabs' bottoms (None: none); band_line = colour of a thin line
    along the middle of the band (None: none)."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        cols = {"r": pal.red, "c": pal.cream, "g": pal.gold, "d": pal.red_dark}
        tot = sum(t[0] for t in tabs)
        bh = int(h * band)
        xs, x = [], 0.0
        for f, c, ln in tabs:
            xs.append((int(round(x / tot * w)), int(round((x + f) / tot * w)), c, ln))
            x += f
        for (x0, x1, c, ln) in xs:
            base = cols[c]
            weave(img, base, rng, stains=0, box_=(x0, 0, max(1, x1 - x0), h))
            if band_colour is not None:
                weave(img, cols[band_colour], rng, stains=0, box_=(x0, 0, max(1, x1 - x0), bh + 1))
                if band_line is not None:
                    for xx in range(x0, x1):
                        for yy in (bh // 2, bh // 2 + 1):
                            px[xx, yy] = _jitter(band_line, rng, 8) + (255,)
            tw = max(1, x1 - x0)
            for xx in range(x0, x1):
                lx = (xx - x0 + 0.5) / tw
                if shape == "step":
                    tri = 1.0 - abs(2.0 * lx - 1.0)
                    stp = math.floor(tri * 3.999) / 3.0
                    bottom = int(bh + (h - 2 - bh) * ln * (0.35 + 0.65 * stp))
                else:
                    inset = 0.08 <= lx <= 0.92
                    bottom = int(bh + (h - 2 - bh) * ln) if inset else bh
                for y in range(h):
                    if y > bottom:
                        px[xx, y] = (0, 0, 0, 0)
                        continue
                    r_, g_, b_, a_ = px[xx, y]
                    k = 1.0
                    if y == bh:
                        k = 0.7
                    elif y < 2:
                        k = 0.78
                    elif y >= bottom - 1 or xx in (x0, x1 - 1):
                        k = 0.8
                    col = _scale((r_, g_, b_), k)
                    if gold_edge is not None and y > bh and (y >= bottom - 1):
                        col = _jitter(gold_edge, rng, 8)
                    px[xx, y] = col + (255,)
            if gold_edge is not None and shape == "step":
                # gold on the risers of the steps
                for xx in range(x0, x1):
                    lx = (xx - x0 + 0.5) / tw
                    tri = 1.0 - abs(2.0 * lx - 1.0)
                    stp = math.floor(tri * 3.999) / 3.0
                    bottom = int(bh + (h - 2 - bh) * ln * (0.35 + 0.65 * stp))
                    for xn in (xx - 1, xx + 1):
                        if x0 <= xn < x1:
                            ln2 = (xn - x0 + 0.5) / tw
                            tri2 = 1.0 - abs(2.0 * ln2 - 1.0)
                            b2 = int(bh + (h - 2 - bh) * ln * (0.35 + 0.65 * math.floor(tri2 * 3.999) / 3.0))
                            if b2 < bottom:
                                for y in range(b2 - 1, bottom + 1):
                                    px[xx, y] = _jitter(gold_edge, rng, 8) + (255,)
        if edge:
            for xx in range(w):
                px[xx, 0] = _scale(px[xx, 0][:3], 0.85) + (255,)
    return paint


def rug_painter(pal, seed, motif="key", field=None, glyphs=True, stains=2):
    """A red rug: dark rim, a gold border band with a pixel motif ("key": little meander hooks, "chain": gold crosses
    in a row), a thin gold frame round the field, gold glyphs in rows on the field (glyphs=False: a plain mottled
    field, as the gabled tent's rug)."""
    def paint(img):
        rng = random.Random(seed)
        weave(img, field or pal.red, rng, stains=stains)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                e = min(x, y, w - 1 - x, h - 1 - y)
                if e < 2:
                    px[x, y] = _jitter(pal.red_dark, rng, 5) + (255,)
                elif e in (2, 3) or e in (12, 13):
                    px[x, y] = _jitter(pal.gold, rng, 9) + (255,)
                elif 4 <= e <= 11:
                    lx = (x if min(y, h - 1 - y) <= min(x, w - 1 - x) else y) % 8
                    ly = e - 4
                    if motif == "key":
                        on = (ly in (0, 7)) or (lx == 0 and ly < 6) or (lx == 5 and ly > 1) or (ly == 3 and 1 <= lx <= 5)
                    else:
                        on = (lx in (3, 4) and 1 <= ly <= 6) or (ly in (3, 4) and 1 <= lx <= 6)
                    if on:
                        px[x, y] = _jitter(_scale(pal.gold, 0.96), rng, 9) + (255,)
                    else:
                        px[x, y] = _jitter(_scale(field or pal.red, 0.86), rng, 5) + (255,)
        motif_ = ("0010100", "0111110", "1101011", "0111110", "0010100")
        for r_, cy in enumerate(range(26, h - 22, 22) if glyphs else ()):
            for cx in range(26 + (r_ % 2) * 11, w - 22, 22):
                for j, row in enumerate(motif_):
                    for i, ch in enumerate(row):
                        if ch == "1":
                            px[cx + i - 3, cy + j - 2] = _jitter(pal.gold, rng, 12) + (255,)
        for y in range(16, h - 16):
            for x in range(16, w - 16):
                if min(x - 16, y - 16, w - 17 - x, h - 17 - y) == 0:
                    px[x, y] = _jitter(_scale(pal.gold, 0.9), rng, 8) + (255,)
    return paint


def runner_painter(pal, seed, point="v", diamond=True, meander=True):
    """The counter runner hanging down the counter's front: red, gold border, a V or stepped point at the bottom
    (cut-out), a gold meander band and a gold diamond above the point."""
    base = banner_painter(pal, seed, point=point, emblem=None, border=2, diamond=diamond, body=0.74)

    def paint(img):
        base(img)
        if not meander:
            return
        rng = random.Random(seed + 1)
        w, h = img.size
        px = img.load()
        y0 = int(h * 0.1)
        for y in range(y0, y0 + 6):
            for x in range(3, w - 3):
                ly, lx = y - y0, (x - 3) % 6
                on = ly in (0, 5) or (lx == 0 and ly < 4) or (lx == 3 and ly > 1)
                if on:
                    px[x, y] = _jitter(pal.gold, rng, 9) + (255,)
    return paint


def wood_painter(base, dark, seed, plank=None, vertical=False):
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        ml.fine_wood(img, (0, 0, w, h), base, dark, plank or h, rng, joints=False, vertical=vertical, knots=0.08, grain=0.14,
                     shade=0.08)
    return paint


def band_painter(seed):
    """Grey iron bands: hammered dark iron, a lighter top edge, a big square rivet in the middle, small ones near the
    ends."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _rgb("5a5c62")
                if y == 0:
                    c = _rgb("8a8c92")
                elif y == h - 1:
                    c = _rgb("34363a")
                px[x, y] = _jitter(c, rng, 7) + (255,)
        for cx, r in ((w // 2, 2), (4, 1), (w - 5, 1)):
            for y in range(max(1, h // 2 - r), min(h - 1, h // 2 + r + 1)):
                for x in range(cx - r, cx + r + 1):
                    px[x, y] = (40, 40, 44, 255) if (x == cx + r or y == h // 2 + r) else (176, 178, 184, 255)
    return paint


def finial_painter(pal, seed):
    """The golden finials: gilded wood, lit on top, darker at the bottom, a few darker grain lines."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                k = 1.15 - 0.4 * (y / h) + (0.06 if x % 5 == 0 else 0.0) - (0.1 if (x * 7 + y * 3) % 11 == 0 else 0.0)
                px[x, y] = _jitter(_scale(pal.finial, k), rng, 8) + (255,)
    return paint


def flowers_painter(petal, petal_dark, centre, seed, n=6, leaf=(64, 140, 52), leaf_dark=(34, 84, 30), lavender=False):
    """Cut-out flowers on green stems (petal colour, a yellow centre) or lavender spikes (lavender=True)."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for x in range(w):
            for y in range(h):
                px[x, y] = (0, 0, 0, 0)
        # leaves and stems
        for k in range(n * 3):
            x = rng.randint(1, w - 2)
            top = rng.randint(int(h * (0.45 if not lavender else 0.25)), h - 3)
            for y in range(top, h):
                px[x, y] = (leaf if (y + k) % 3 else leaf_dark) + (255,)
                if not lavender and y > h * 0.65 and rng.random() < 0.35 and 0 < x < w - 1:
                    px[x + rng.choice((-1, 1)), y] = leaf + (255,)
        for k in range(n):
            cx = int((k + 0.5) * w / n + rng.uniform(-1.5, 1.5))
            cx = min(max(cx, 3), w - 4)
            cy = rng.randint(3, int(h * (0.45 if not lavender else 0.3)))
            for y in range(cy, h):
                px[cx, y] = leaf_dark + (255,)
            if lavender:
                for y in range(cy - 2, cy + int(h * 0.45)):
                    for dx in (-1, 0, 1):
                        if 0 <= y < h and (dx == 0 or (y + cx) % 2 == 0):
                            c = petal if (y + dx) % 3 else petal_dark
                            px[cx + dx, y] = _jitter(c, rng, 10) + (255,)
            else:
                for dx, dy in ((0, -2), (-2, 0), (2, 0), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1), (0, -1), (-1, 0), (1, 0), (0, 1)):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < w and 0 <= y < h:
                        c = petal if abs(dx) + abs(dy) <= 1 or (dx and dy) else petal_dark
                        px[x, y] = _jitter(c, rng, 10) + (255,)
                px[cx, cy] = centre + (255,)
    return paint


def burlap_painter(seed, base="c8a678"):
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        ml._weave(img, (0, 0, w, h), _rgb(base), rng, stains=0)
        px = img.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                k = 0.86 + 0.2 * math.sin(math.pi * (x + 0.5) / w) - 0.08 * (abs(math.sin(x * 0.55 + y * 0.08)) > 0.93)
                px[x, y] = _scale((r, g, b), k) + (255,)
    return paint


def grain_painter(seed, base="e8c060"):
    """A heap of grain / corn kernels: little lit dots on a golden ground."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        b = _rgb(base)
        for y in range(h):
            for x in range(w):
                c = _scale(b, 0.78)
                if (x + 2 * y) % 3 == 0:
                    c = _scale(b, 1.12)
                elif (x * 3 + y) % 5 == 0:
                    c = _scale(b, 0.92)
                px[x, y] = _jitter(c, rng, 10) + (255,)
    return paint


def book_painter(seed):
    """An open book seen from above: two cream pages with lines of dark text, a darker gutter, a leather rim."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                e = min(x, y, w - 1 - x, h - 1 - y)
                c = _rgb("efe0bc")
                if e < 1:
                    c = _rgb("5a3418")
                elif abs(x - w / 2) < 1:
                    c = _rgb("b8a07a")
                elif y % 3 == 0 and 3 <= y <= h - 4 and (3 <= x < w / 2 - 2 or w / 2 + 2 < x <= w - 4) and rng.random() < 0.8:
                    c = _rgb("6a5a48")
                px[x, y] = _jitter(c, rng, 5) + (255,)
    return paint


def parcel_painter(seed, cloth="e8d8c0", ribbon="b02a26"):
    """A cloth-wrapped parcel: cream cloth with a red ribbon cross."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _rgb(cloth)
                if abs(x - w / 2 + 0.5) < w * 0.12 or abs(y - h / 2 + 0.5) < h * 0.12:
                    c = _rgb(ribbon)
                elif (x + y) % 4 == 0:
                    c = _scale(c, 0.9)
                px[x, y] = _jitter(c, rng, 6) + (255,)
    return paint


def chest_painter(pal, seed):
    """A chest's wood: warm planks, gold corner plates."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        ml.fine_wood(img, (0, 0, w, h), _rgb("8a5a2c"), _rgb("4a2c12"), 8, rng, joints=False, knots=0.1, grain=0.12, shade=0.06)
        px = img.load()
        for y in range(h):
            for x in range(w):
                if (x < 4 or x >= w - 4) and (y < 4 or y >= h - 4):
                    px[x, y] = _jitter(pal.gold, rng, 10) + (255,)
    return paint


def canvas_painter(pal, seed, base=None, folds=6, hem=None, bottom_red=0):
    """A hanging canvas wall: cream (or base) cloth, soft vertical folds, a darker bottom, an optional red band at the
    bottom (bottom_red px) and a hem colour."""
    def paint(img):
        rng = random.Random(seed)
        c0 = base or pal.cream
        weave(img, c0, rng, stains=2)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                k = 0.86 + 0.14 * math.sin(math.pi * ((x * folds / w) % 1.0)) - 0.12 * (y / h) ** 2
                c = _scale((r, g, b), k)
                if bottom_red and y >= h - bottom_red:
                    c = _jitter(_scale(pal.red, k), rng, 6)
                if hem and y >= h - 2:
                    c = _jitter(hem, rng, 6)
                px[x, y] = c + (255,)
    return paint


# ---------------------------------------------------------------- geometry
def band(bone, name, x, z, half, y, h, region="pd_band"):
    """An iron band round a squared post (centre x, z): riveted faces on the sides, plain iron top and bottom."""
    box(bone, name, (x - half, y, z - half), (x + half, y + h, z + half), {"all": region, "+2": "iron", "-2": "iron"}, stretch=True)


def finial(shell, det, name, x, y, z, w=0.42, region="pd_finial", cap_region="pd_post", tall=1.0):
    """A cap block on a post top at height y (wood, or a gilded collar with cap_region="pd_finial"), then the small
    golden knob finial of the pictures: a narrow neck, a wider knob, a short spire and its tip (no big cone); returns
    the tip's height."""
    box(shell, name + "_cap", (x - w / 2, y, z - w / 2), (x + w / 2, y + 0.16, z + w / 2),
        {"all": cap_region, "+2": cap_region if cap_region == region else "end_grain"})
    yy = y + 0.16
    for k, (f, hh) in enumerate(((0.34, 0.11 * tall), (0.62, 0.13), (0.32, 0.13 * tall), (0.14, 0.08 * tall))):
        bone = shell if k < 2 else det
        box(bone, "%s_pt_%d" % (name, k), (x - w * f / 2, yy, z - w * f / 2), (x + w * f / 2, yy + hh, z + w * f / 2), region)
        yy += hh
    return yy


def post(shell, det, name, x, z, top, d=0.36, foot=(0.55, 0.5), bands=(), eave=None, cap_w=None, finial_on=True,
         region="pd_post", collide_top=None, tall=1.0, foot_region="wood_dark", base=None, solid=True, cap_region="pd_post"):
    """A squared wooden post from a foot block to `top`: iron bands (heights in `bands`), a collar, a cap (cap_region:
    wood, or "pd_finial" for a gilded collar) and the small golden knob finial; collides (foot width) from the ground
    to collide_top (default the post top) when solid; base = the height its shaft starts at (default the foot's top: a
    king post on a beam starts higher). Returns the finial's tip height (or the top)."""
    fh, fw = foot
    if fh > 0:
        box(shell, name + "_foot", (x - fw / 2, 0.0, z - fw / 2), (x + fw / 2, fh, z + fw / 2), {"all": foot_region, "+2": "end_grain"})
        band(det, name + "_fband", x, z, fw / 2 + 0.015, fh - 0.14, 0.1)
    beam(shell, name, (x, fh if base is None else base, z), (x, top, z), d, {"all": region, "+1": "end_grain", "-1": "end_grain"})
    for k, y in enumerate(bands):
        band(det, "%s_band_%d" % (name, k), x, z, d / 2 + 0.02, y, 0.12)
    band(det, name + "_collar", x, z, d / 2 + 0.025, top - 0.14, 0.12)
    tip = top
    if finial_on:
        tip = finial(shell, det, name + "_fin", x, top, z, w=cap_w or d + 0.1, tall=tall, cap_region=cap_region)
    hw = max(fw, d) / 2 if fh > 0 else d / 2
    if solid:
        collide((x - hw, 0.0, z - hw, x + hw, collide_top if collide_top is not None else top, z + hw))
    return tip


def rope_wrap(det, name, x, z, y, half, turns=2, region="rope"):
    """A rope wound round a squared post (rings of rope)."""
    for k in range(turns):
        yy = y - 0.1 * k
        box(det, "%s_%d" % (name, k), (x - half - 0.04, yy, z - half - 0.04), (x + half + 0.04, yy + 0.08, z + half + 0.04), region)


def tassel(det, name, top, length=0.45, region="rope", tuft="trim_gold"):
    """A rope end hanging from `top` with a tassel."""
    top = v3(*top)
    beam(det, name + "_cord", top, top - UP * length, 0.05, region)
    add_cube(det, name + "_knot", top - UP * (length + 0.02), EYE, (0.1, 0.07, 0.1), region)
    add_cube(det, name + "_tuft", top - UP * (length + 0.14), EYE, (0.11, 0.18, 0.11), tuft, stretch=True)


def loft_down(bone, name, P, nx, ny, region, th=0.03, overlap=0.004, both=True, u_hint=None, v_hint=None):
    """tentlib.loft adapted for striped roofs whose stripes run DOWN the slope (t): each tilted strip keeps its sides
    on the slope lines (v from the cell's left and right edges, u made square to it) instead of keeping its top and
    bottom on the cell's edges. On a roof whose ridge or eave curves (the cells are slanted trapezoids), tentlib's
    strips lean sideways and the stripes come out jagged; these keep them straight (the small slant moves to the
    row seams, which lie inside one stripe colour)."""
    for i in range(nx):
        for j in range(ny):
            s0, s1, t0, t1 = i / nx, (i + 1) / nx, j / ny, (j + 1) / ny
            a1, b1, a0, b0 = P(s0, t0), P(s1, t0), P(s0, t1), P(s1, t1)   # a = left, b = right, 1 = top, 0 = bottom
            c = (a0 + a1 + b0 + b1) / 4
            vp = ((a0 - a1) + (b0 - b1)) / 2
            H = np.linalg.norm(vp)
            if H < 1e-5:
                continue
            v = vp / H
            up_ = ((b0 + b1) - (a0 + a1)) / 2
            up_ = up_ - np.dot(up_, v) * v
            L = np.linalg.norm(up_)
            if L < 1e-5:
                continue
            u = up_ / L
            # the strip spans the cell's mean width measured square to the slope
            L = (np.linalg.norm(np.cross(b1 - a1, v)) + np.linalg.norm(np.cross(b0 - a0, v))) / 2
            n = np.cross(u, v)
            axes = np.column_stack([u, v, n])
            regions = {"all": None, "+3": region, "-3": region} if both else {"all": None, "+3": region}
            cube = add_cube(bone, "%s_%d_%d" % (name, i, j), c, axes, (L + overlap, H + overlap, th), regions, stretch=True,
                            u_dir=u if u_hint is None else u_hint, v_dir=v if v_hint is None else v_hint)
            ml.tl.gn.set_sub(cube, (s0, t0, s1, t1))
    return None


def valance(bone, name, c0, c1, out, h=0.5, region="pd_valance", tab_len=2.4, flare=0.06, droop=0.0):
    """A dagged valance from c0 to c1 (its top edge), flaring out a little towards `out`; one strip per tab_len (at
    least 4 when it droops); droop = how much its top edge sags in the middle (a curved valance)."""
    c0, c1, out = v3(*c0), v3(*c1), v3(*out)

    def V(s, t):
        e = c0 + (c1 - c0) * s - UP * (droop * math.sin(math.pi * s))
        return e + UP * 0.03 - UP * (h * t) + out * (0.03 + flare * t)
    L = np.linalg.norm(c1 - c0)
    n = max(1, int(round(L / tab_len)))
    if droop > 0:
        n = max(4, n)
    loft(bone, name, V, n, 1, region, th=0.025)


def drape(bone, det, name, top_a, top_b, tie, bot_a, bot_b, normal, region="pd_drape", nx=3, tie_region="rope"):
    """A curtain tied back: hangs from the edge top_a - top_b, gathered at `tie` (a rope band), flaring again below to
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
    add_cube(det, name + "_tie", tie, np.column_stack([side, UP, np.cross(side, UP)]), (0.26, 0.08, 0.16), tie_region)


def wall(bone, name, a, b, y0, y1, out, region="pd_wall", nx=6, fold=0.05, flare=0.0):
    """A hanging canvas wall from a (left) to b on the ground line, y0..y1, soft vertical folds towards `out`; flare
    pushes its bottom outwards (a cloth spreading on the ground)."""
    a, b, out = v3(*a), v3(*b), v3(*out)

    def P(s, t):
        p = a + (b - a) * s
        return v3(p[0], y1 - (y1 - y0) * t, p[2]) + out * (fold * math.sin(s * math.pi * nx) * (0.4 + 0.6 * t) + flare * t * t)
    loft(bone, name, P, nx, 2, region, th=0.03)


def slope_banner(bone, name, top, down, w, h, region, lift=0.05, nx=1, ny=3, curve=None):
    """A banner laid along a roof slope: its top edge centred at `top`, running `h` along `down` (a unit vector down
    the slope), `w` wide across; lift = its height above the cloth (along the slope's normal); curve(t) -> extra lift
    (the banner following a concave slope)."""
    top, down = v3(*top), norm(v3(*down))
    side = norm(np.cross(UP, down)) if abs(down[1]) < 0.99 else X
    if side[0] < 0:
        side = -side
    n = np.cross(side, down)
    if n[1] < 0:
        n = -n

    def P(s, t):
        p = top + side * ((s - 0.5) * w) + down * (h * t) + n * lift
        if curve is not None:
            p = p + curve(t)
        return p
    loft(bone, name, P, nx, ny, region, th=0.02, u_hint=side, v_hint=down)


def scroll(bone, name, c, length=0.4, r=0.055, yaw=0.0, region="beige", end="white"):
    """A rolled scroll lying on its side (two boxes turned 45 degrees about its axis), along yaw."""
    c = v3(*c)
    for k, a in enumerate((0.0, math.pi / 4)):
        add_cube(bone, "%s_%d" % (name, k), c, ry(yaw) @ rx(a), (length, 2 * r * 0.83, 2 * r * 0.83), {"all": region, "+1": end, "-1": end},
                 stretch=True)


def open_book(det, name, c, yaw=0.0, w=0.36, d=0.26, region="pd_book"):
    """An open book lying on a table: a leather cover and two pages raised a little towards the spine."""
    c = v3(*c)
    R = ry(yaw)
    add_cube(det, name + "_cover", c + UP * 0.012, R, (w + 0.03, 0.024, d + 0.03), "leather_dark")
    for k, s in enumerate((-1, 1)):
        Rp = R @ rz(s * 0.12)
        add_cube(det, "%s_page_%d" % (name, k), c + R @ v3(s * w / 4, 0.045, 0), Rp, (w / 2, 0.03, d),
                 {"all": "white", "+2": region}, stretch=True, u_dir=R @ X, v_dir=R @ Z)


def parcel(det, name, foot, size=(0.36, 0.22, 0.28), yaw=0.0, region="pd_parcel"):
    """A cloth-wrapped parcel tied with a red ribbon."""
    foot = v3(*foot)
    add_cube(det, name, foot + UP * size[1] / 2, ry(yaw), size, region, stretch=True)
    add_cube(det, name + "_bow", foot + UP * (size[1] + 0.03), ry(yaw + 0.5), (0.1, 0.06, 0.06), "cloth_red")


def grain_sack(shell, det, name, foot, r=0.36, h=0.62, yaw=0.0, region="pd_burlap", grain="pd_grain"):
    """An open burlap sack, its top rolled down, heaped with grain."""
    foot = v3(*foot)
    for k, (y0, y1, s) in enumerate(((0.0, 0.12, 0.86), (0.12, 0.7, 1.0), (0.7, 0.92, 0.94))):
        for j in range(2):
            add_cube(shell, "%s_%d_%d" % (name, k, j), foot + UP * (h * (y0 + y1) / 2), ry(yaw + math.pi / 4 * j),
                     (2 * r * s * 0.86, h * (y1 - y0), 2 * r * s * 0.86), region, stretch=True)
    add_cube(det, name + "_rim", foot + UP * (h * 0.94), ry(yaw), (2 * r * 0.98, h * 0.1, 2 * r * 0.98), region, stretch=True)
    for j in range(2):
        add_cube(shell, "%s_heap_%d" % (name, j), foot + UP * (h * 0.96), ry(yaw + math.pi / 4 * j + 0.2), (2 * r * 0.72, 0.1, 2 * r * 0.72),
                 {"all": grain}, stretch=True)
    add_cube(det, name + "_top", foot + UP * (h + 0.04), ry(yaw + 0.3), (r * 0.9, 0.08, r * 0.9), {"all": grain}, stretch=True)


def chest(shell, det, name, foot, w=0.9, d=0.6, h=0.62, yaw=0.0, region="pd_chest", trim="gold"):
    """A gold-trimmed chest: wooden body, domed lid (two boxes), bands and corners, a lock plate."""
    foot = v3(*foot)
    R = ry(yaw)
    add_cube(shell, name + "_body", foot + UP * (h * 0.36), R, (w, h * 0.72, d), {"all": region}, stretch=True)
    add_cube(shell, name + "_lid", foot + UP * (h * 0.8), R, (w + 0.02, h * 0.18, d + 0.02), {"all": region}, stretch=True)
    add_cube(shell, name + "_lid_top", foot + UP * (h * 0.94), R, (w, h * 0.12, d * 0.72), {"all": region}, stretch=True)
    for k, s in enumerate((-0.3, 0.3)):
        add_cube(det, "%s_band_%d" % (name, k), foot + R @ v3(s * w, h * 0.52, 0), R, (0.07, h * 1.0 + 0.02, d + 0.03), trim)
    add_cube(det, name + "_rim", foot + UP * (h * 0.71), R, (w + 0.04, 0.05, d + 0.04), trim)
    add_cube(det, name + "_lock", foot + R @ v3(0, h * 0.62, d / 2 + 0.02), R, (0.14, 0.18, 0.04), trim)


def flower_box(shell, det, name, foot, w=1.1, d=0.55, h=0.55, yaw=0.0, flowers="pd_flowers", fh=0.7, solid=True):
    """A wooden planter box (iron-banded crate) full of flowers (crossed cut-out planes along its length)."""
    foot = v3(*foot)
    R = ry(yaw)
    ml.rbox(shell, name, foot, (w, h, d), yaw, {"all": "crate", "+2": "produce", "-2": "crate_top"}, solid=solid, stretch=True)
    add_cube(det, name + "_soil", foot + UP * (h - 0.03), R, (w * 0.9, 0.04, d * 0.86), "coal", stretch=True)
    n = max(2, int(round(w / 0.42)))
    for k in range(n):
        p = foot + R @ v3(-w / 2 + w * (k + 0.5) / n, h + fh / 2 - 0.06, 0.04 * (-1) ** k)
        ml.crossed(det, "%s_fl_%d" % (name, k), p, w / n + 0.18, fh, flowers, yaw=yaw + 0.25 * (-1) ** k)


def shift_all(root, decor, dx, dz):
    """Moves the whole tent by (dx, 0, dz): every cube (bones without rotation), the collision boxes, the mod blocks."""
    d = v3(dx, 0.0, dz)

    def walk(b):
        if not np.allclose(b.rot, np.eye(3)) or np.linalg.norm(b.origin) > 1e-9:
            raise AssertionError("shift_all needs unrotated bones at the origin (%s)" % b.name)
        for c in b.cubes:
            c.center = np.asarray(c.center, dtype=float) + d
        for ch in b.children:
            walk(ch)
    walk(root)
    for i, (x0, y0, z0, x1, y1, z1) in enumerate(ml.COLLIDERS):
        ml.COLLIDERS[i] = (x0 + dx, y0, z0 + dz, x1 + dx, y1, z1 + dz)
    if decor is not None:
        for b in decor.blocks:
            b["x"] += dx
            b["z"] += dz


def centre_offsets(root, decor=None, pad=0.05):
    """(dx, dz) that centre the extent of the model (and the mod blocks' boxes) on the anchor block, rounded to 0.05."""
    e = ml.tl.extent(root, pad=pad)
    x0, x1, z0, z1 = e[0], e[3], e[2], e[5]
    if decor is not None:
        for b in decor.blocks:
            f = decor.footprint(b)
            x0, x1, z0, z1 = min(x0, f[0]), max(x1, f[3]), min(z0, f[2]), max(z1, f[5])
    return round(-(x0 + x1) / 2 / 0.05) * 0.05, round(-(z0 + z1) / 2 / 0.05) * 0.05
