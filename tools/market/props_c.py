"""Shared helpers of the group C market tents (1.26.0, the three "balance" (scales) tents of Lion Port and the cities):
tente_balance_chapiteau (048), tente_balance_fer (050) and tente_balance_bourse (154).

Built on merchantlib / tentlib (imported, never edited): one block = the whole tent, one static .bbmodel, its own atlas
(merchantlib.Atlas + the regions below), collisions through merchantlib.collide, mod blocks through merchantlib.Decor.

  - painters: painter(img) on a PIL RGBA image of the region's size (atlas.add(name, w, h, painter)): woven striped
    cloth (roof slopes with "flame" stripes or plain stripes, walls, awnings), dagged valances (square steps, points,
    rounded scallops), banners with the gold SCALES (stepped or V point, laurel, gold fringe), carpets (medallion,
    scroll border, dotted field), rolled carpets, flags, bunting pennants, hanging signs (coin purse, scroll), warm
    post wood, riveted iron bands, wrought iron and its filigree, burlap, chest wood, table runners, cloth bolts;
  - geometry: iron-banded posts, marquee roof skirts (steep at the top, flat at the eave, soft folds), curved swag
    valances, straight valances, tied-back drapes, hanging walls, flags, bunting, rolled carpets, standing / lying cloth
    bolts, chests, sacks, scrolls, open books, potion rows, lantern brackets.

Coordinates: tent-local blocks, y up, +z = the open front, the anchor block's centre at (0, 0, 0) on the ground.
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "merchant"))
sys.path.insert(0, os.path.join(HERE, "..", "tents"))
sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402

v3, norm, add_cube, beam, loft, Bone = ml.v3, ml.norm, ml.add_cube, ml.beam, ml.loft, ml.Bone
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ry, rx, rz = ml.ry, ml.rx, ml.rz
box, collide = ml.box, ml.collide
_rgb, _jitter, _scale, _mix = ml._rgb, ml._jitter, ml._scale, ml._mix


# ---------------------------------------------------------------- palettes
class Pal:
    """A tent's colours (RGB tuples)."""

    def __init__(self, red, red_dark, red_light, cream, gold, gold_dark, gold_light):
        self.red, self.red_dark, self.red_light = _rgb(red), _rgb(red_dark), _rgb(red_light)
        self.cream, self.gold, self.gold_dark, self.gold_light = _rgb(cream), _rgb(gold), _rgb(gold_dark), _rgb(gold_light)


# ---------------------------------------------------------------- painting helpers
def weave(img, c, rng, stains=1, box_=None):
    w, h = img.size
    ml._weave(img, box_ or (0, 0, w, h), c, rng, stains=stains)


def _put(px, x, y, c, a=255):
    px[x, y] = tuple(int(max(0, min(255, k))) for k in c[:3]) + (a,)


def overlay(img, box_, draw, S=4):
    """Draws vector shapes over the box (x, y, w, h) of img: the box is upscaled S times (nearest), draw(d, W, H, S)
    paints on it with PIL.ImageDraw, then it is box-filtered back down (soft edges blended with the real background)
    and pasted back; transparent pixels of img stay transparent."""
    from PIL import Image, ImageDraw
    x0, y0, w, h = box_
    sub = img.crop((x0, y0, x0 + w, y0 + h))
    alpha = sub.getchannel("A")
    big = sub.convert("RGB").resize((w * S, h * S), Image.NEAREST)
    draw(ImageDraw.Draw(big), w * S, h * S, S)
    small = big.resize((w, h), Image.BOX).convert("RGBA")
    small.putalpha(alpha)
    img.paste(small, (x0, y0))


def draw_scales(d, cx, cy, W, H, col, dark, light, S=4, cross=True, chains=True):
    """The gold balance (scales of justice) of the banners and signs, centred on (cx, cy), W x H (upscaled px): a
    pillar with a small cross on top, the beam with knobs, two pans on strings, a stepped base; a dark shadow offset
    down-right and a light edge up-left."""
    def shape(ox, oy, c):
        lw = max(S, W * 0.075)
        top, base = cy - H * 0.46, cy + H * 0.4
        d.rectangle((cx - lw / 2 + ox, top + oy, cx + lw / 2 + ox, base + oy), fill=c)
        if cross:
            d.rectangle((cx - W * 0.12 + ox, top + H * 0.05 + oy, cx + W * 0.12 + ox, top + H * 0.05 + lw * 0.9 + oy), fill=c)
        by = cy - H * 0.22
        d.rectangle((cx - W * 0.42 + ox, by + oy, cx + W * 0.42 + ox, by + lw * 0.85 + oy), fill=c)
        d.ellipse((cx - lw * 0.9 + ox, by - lw * 0.5 + oy, cx + lw * 0.9 + ox, by + lw * 1.3 + oy), fill=c)
        for sx in (-1, 1):
            ex = cx + sx * W * 0.36
            d.ellipse((ex - lw * 0.6 + ox, by - lw * 0.3 + oy, ex + lw * 0.6 + ox, by + lw * 1.1 + oy), fill=c)
            py = cy + H * 0.08
            if chains:
                d.line((ex + ox, by + lw + oy, ex - W * 0.15 + ox, py + oy), fill=c, width=int(max(S * 0.75, lw * 0.4)))
                d.line((ex + ox, by + lw + oy, ex + W * 0.15 + ox, py + oy), fill=c, width=int(max(S * 0.75, lw * 0.4)))
            d.chord((ex - W * 0.2 + ox, py - H * 0.09 + oy, ex + W * 0.2 + ox, py + H * 0.09 + oy), 0, 180, fill=c)
            d.rectangle((ex - W * 0.2 + ox, py - lw * 0.25 + oy, ex + W * 0.2 + ox, py + lw * 0.35 + oy), fill=c)
        d.polygon([(cx - W * 0.1 + ox, base - H * 0.08 + oy), (cx + W * 0.1 + ox, base - H * 0.08 + oy), (cx + W * 0.2 + ox, base + oy),
                   (cx - W * 0.2 + ox, base + oy)], fill=c)
        d.rectangle((cx - W * 0.27 + ox, base + oy, cx + W * 0.27 + ox, base + H * 0.06 + oy), fill=c)
    shape(S * 0.9, S * 0.9, dark)
    shape(-S * 0.5, -S * 0.5, light)
    shape(0, 0, col)


def draw_laurel(d, cx, cy, W, H, col, dark, S=4):
    """Two laurel branches curving up and out from a knot at the bottom (the banner of the wrought-iron pavilion): a stem
    each and six pointed leaves along it, alternately outside and inside."""
    def leaf(x, y, ang, ln, wd, c):
        ca, sa = math.cos(ang), math.sin(ang)
        pts = []
        for k in range(12):
            t = 2 * math.pi * k / 12
            u, v = math.cos(t) * ln / 2, math.sin(t) * wd / 2 * (1 - 0.35 * math.cos(t))
            pts.append((x + u * ca - v * sa, y + u * sa + v * ca))
        d.polygon(pts, fill=c)
    rx_, ry_ = W * 0.4, H * 0.48
    bot = cy + H * 0.46
    for sx in (-1, 1):
        prev = None
        for k in range(7):
            t = k / 6
            a = math.pi / 2 + sx * (0.25 + 1.55 * t)      # from the bottom up the side
            px_ = cx + math.cos(a) * rx_ * -1 * -1
            px_ = cx - sx * 0 + math.cos(a) * rx_
            py_ = bot - ry_ + math.sin(a) * ry_
            if prev is not None:
                d.line((prev[0], prev[1], px_, py_), fill=dark, width=int(S * 1.4))
                d.line((prev[0], prev[1], px_, py_), fill=col, width=int(S * 0.9))
            prev = (px_, py_)
            if k == 0:
                continue
            tang = a + sx * math.pi / 2
            for side in (1, -1):
                ang = tang + side * 0.7 * sx
                lx, ly = px_ + math.cos(ang) * W * 0.06, py_ + math.sin(ang) * W * 0.06
                leaf(lx + S * 0.6, ly + S * 0.6, ang, W * 0.15, W * 0.07, dark)
                leaf(lx, ly, ang, W * 0.15, W * 0.07, col)
    d.ellipse((cx - W * 0.06, bot - H * 0.07, cx + W * 0.06, bot + H * 0.05), fill=col)


def draw_purse(d, cx, cy, W, H, col, dark, light, S=4):
    """A gold coin purse: round bottom narrowing to the tied neck, a frilled top; outline, light on the upper left."""
    def bag(ox, oy, c, inset=0.0):
        d.ellipse((cx - W * (0.44 - inset) + ox, cy - H * (0.04 - inset) + oy, cx + W * (0.44 - inset) + ox, cy + H * (0.5 - inset) + oy), fill=c)
        d.polygon([(cx - W * (0.18 - inset) + ox, cy - H * 0.16 + oy), (cx + W * (0.18 - inset) + ox, cy - H * 0.16 + oy),
                   (cx + W * (0.38 - inset) + ox, cy + H * 0.14 + oy), (cx - W * (0.38 - inset) + ox, cy + H * 0.14 + oy)], fill=c)
        d.ellipse((cx - W * (0.26 - inset) + ox, cy - H * (0.46 - inset) + oy, cx + W * (0.26 - inset) + ox, cy - H * (0.2 + inset) + oy), fill=c)
    bag(S, S, dark)
    bag(0, 0, dark)
    bag(0, 0, col, inset=0.04)
    d.ellipse((cx - W * 0.3, cy + H * 0.02, cx - W * 0.06, cy + H * 0.22), fill=light)
    d.rectangle((cx - W * 0.2, cy - H * 0.22, cx + W * 0.2, cy - H * 0.15), fill=dark)
    d.line((cx + W * 0.06, cy - H * 0.17, cx + W * 0.18, cy - H * 0.02), fill=dark, width=int(S))


def draw_coins(d, cx, base, W, n, col, dark, light, S=4, rh=None):
    """A stack of n gold coins (seen from the side, a little from above) standing on `base`."""
    rw = W / 2
    rh = rh or W * 0.22
    step = rh * 0.9
    for k in range(n):
        y = base - k * step
        d.ellipse((cx - rw, y - rh + S, cx + rw, y + rh + S), fill=dark)
        d.rectangle((cx - rw, y - S * 0.2, cx + rw, y + S), fill=dark)
        d.ellipse((cx - rw, y - rh, cx + rw, y + rh), fill=col)
        d.ellipse((cx - rw * 0.7, y - rh * 0.65, cx + rw * 0.7, y + rh * 0.65), outline=light, width=int(S * 0.75))


def draw_scroll(d, cx, cy, W, H, col, dark, light, S=4):
    """A rolled parchment lying across (diagonal), its two curls, a ribbon (the sign of the cloth / record merchant)."""
    a = -0.45
    ca, sa = math.cos(a), math.sin(a)

    def P(x, y):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca)
    L, R_ = W * 0.42, H * 0.17
    body = [P(-L, -R_), P(L, -R_), P(L, R_), P(-L, R_)]
    d.polygon([(x + S, y + S) for x, y in body], fill=dark)
    d.polygon(body, fill=col)
    for sx in (-1, 1):
        ex, ey = P(sx * L, 0)
        d.ellipse((ex - R_ * 1.15 + S, ey - R_ * 1.15 + S, ex + R_ * 1.15 + S, ey + R_ * 1.15 + S), fill=dark)
        d.ellipse((ex - R_ * 1.15, ey - R_ * 1.15, ex + R_ * 1.15, ey + R_ * 1.15), fill=col)
        d.ellipse((ex - R_ * 0.55, ey - R_ * 0.55, ex + R_ * 0.55, ey + R_ * 0.55), fill=dark)
    d.line([P(-L * 0.6, -R_ * 0.4), P(L * 0.6, -R_ * 0.4)], fill=light, width=int(S))
    rx_, ry_ = P(L * 0.15, R_ * 1.0)
    d.polygon([(rx_ - W * 0.04, ry_), (rx_ + W * 0.04, ry_), (rx_ + W * 0.07, ry_ + H * 0.26), (rx_, ry_ + H * 0.2), (rx_ - W * 0.07, ry_ + H * 0.26)],
              fill=dark)


# ---------------------------------------------------------------- painters
def stripes_painter(cols, n, seed, fold=0.12, seam=0.78, grad=(0.9, 1.04), hem=None, hem_h=0, top_band=None, top_h=0.0,
                    flame=None, step=1, stains=1, ratio=0.5):
    """n vertical stripes across u (colours `cols` in turn), v from the top (ridge) to the bottom (eave): a weave, dark
    seams, a soft fold in each stripe, a vertical gradient; flame=(v0, v1): the stripes of the 2nd colour narrow to a
    point upwards between v0 and v1 (a flame / chevron crown, stepped by `step` px), the 1st colour above; top_band = a
    colour band along the top (top_h of the height); hem = a band at the bottom (hem_h px); ratio = the share of the
    2nd colour in each pair of stripes."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        acc, edges = 0.0, [0]
        for k in range(n):
            acc += (2 * (1 - ratio) if k % 2 == 0 else 2 * ratio) if len(cols) > 1 else 1.0
            edges.append(acc)
        edges = [int(round(e * w / acc)) for e in edges]
        for k in range(n):
            weave(img, cols[k % len(cols)], rng, stains=stains, box_=(edges[k], 0, edges[k + 1] - edges[k], h))
        px = img.load()
        if flame:
            v0, v1 = flame
            base = (0, 0, w, h)
            fill = Image_new_like(img)
            weave(fill, cols[0], random.Random(seed + 7), stains=stains, box_=base)
            fpx = fill.load()
            for k in range(n):
                if k % 2 == 0:
                    continue
                x0, x1 = edges[k], edges[k + 1]
                cxk, half = (x0 + x1) / 2.0, (x1 - x0) / 2.0
                for y in range(h):
                    t = (y / h - v0) / max(1e-6, v1 - v0)
                    t = max(0.0, min(1.0, t))
                    hw = half * t
                    hw = math.floor(hw / step) * step if step > 1 else hw
                    for x in range(x0, x1):
                        if abs(x + 0.5 - cxk) > hw:
                            px[x, y] = fpx[x, y]
        owner = [max(i for i in range(n) if edges[i] <= x) for x in range(w)]
        for y in range(h):
            g = grad[0] + (grad[1] - grad[0]) * (y / max(1, h - 1))
            for x in range(w):
                r, gg_, b, a = px[x, y]
                k = g
                if x in edges or x + 1 in edges:
                    k *= seam
                o = owner[x]
                fx = (x - edges[o]) / max(1, edges[o + 1] - edges[o])
                k *= 1.0 - fold / 2 + fold * math.sin(math.pi * fx)
                if y < 2:
                    k *= 0.82
                px[x, y] = _scale((r, gg_, b), k) + (255,)
        if top_band is not None:
            th_ = int(round(h * top_h))
            weave(img, top_band, random.Random(seed + 3), stains=0, box_=(0, 0, w, th_))
            for x in range(w):
                for y in range(th_ - 1, th_ + 1):
                    if 0 <= y < h:
                        r, gg_, b, a = px[x, y]
                        px[x, y] = _scale((r, gg_, b), 0.7) + (255,)
        if hem is not None:
            for y in range(h - hem_h, h):
                for x in range(w):
                    _put(px, x, y, _jitter(hem if y > h - hem_h else _scale(hem, 0.7), rng, 8))
    return paint


def crown_painter(red, cream, n, seed, band=(0.5, 0.16), zig=0.08, ratio=0.4, ridge=0.05, step=3, fold=0.16, grad=(0.86, 1.04)):
    """A marquee slope in the pixel style of the great scales marquee (u across, v from the ridge down): deep red with a
    cream ridge band, a cream band across the lower half with a stepped zigzag upper edge (band = (v of its top, its
    height), zig = the zigzag's height), and below it red / cream stripes down to the eave (ratio = cream's share);
    dark seams and soft folds every 1/n."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, red, rng, stains=1)
        cr = Image_new_like(img)
        weave(cr, cream, random.Random(seed + 1), stains=0)
        px, cpx = img.load(), cr.load()
        sw = w / n
        for x in range(w):
            lx = (x % sw) / sw
            tri = 1.0 - abs(2.0 * lx - 1.0)
            top = band[0] + zig * math.floor(tri * 3.999) / 3.0 - zig / 2
            topp = int(top * h) // step * step
            botp = int((top + band[1]) * h)
            stripe = lx >= 1.0 - ratio
            for y in range(h):
                v = y
                use_cr = v < ridge * h or (topp <= v < botp) or (v >= botp and stripe)
                if use_cr:
                    px[x, y] = cpx[x, y]
        for y in range(h):
            g = grad[0] + (grad[1] - grad[0]) * (y / max(1, h - 1))
            for x in range(w):
                r, gg_, b, a = px[x, y]
                fx = (x % sw) / sw
                k = g * (1.0 - fold / 2 + fold * math.sin(math.pi * fx))
                if int(x % sw) == 0:
                    k *= 0.78
                if y < 2:
                    k *= 0.82
                px[x, y] = _scale((r, gg_, b), k) + (255,)
    return paint


def Image_new_like(img):
    from PIL import Image
    return Image.new("RGBA", img.size, (0, 0, 0, 0))


def valance_painter(cols, n_tabs, seed, kind="square", edge=None, edge_dark=None, solid=0.45, motif=None, top=None, stripes_per_tab=1):
    """A dagged valance strip (cut-out): n_tabs tabs (colours `cols` in turn, stripes_per_tab stripes each), a band at
    the top (top colour, or none), the bottom edge: kind "square" (two stepped square teeth per tab), "point" (one
    pointed dag per tab), "scallop" (one rounded lobe per tab, a small point between) or "straight"; the edge outlined
    in `edge` (gold) 2 px; motif = a colour for little lozenges in each tab."""
    def bottom_of(x, w, h):
        tw = w / n_tabs
        lx = (x % tw) / tw
        sol = h * solid
        if kind == "square":
            tri = 1.0 - abs(2.0 * ((lx * 2.0) % 1.0) - 1.0)
            st = math.floor(tri * 3.999) / 3.0
            return int(sol + (h - 3 - sol) * st)
        if kind == "point":
            tri = 1.0 - abs(2.0 * lx - 1.0)
            return int(sol + (h - 2 - sol) * tri)
        if kind == "scallop":
            c = abs(2.0 * lx - 1.0)
            lobe = math.sqrt(max(0.0, 1.0 - c * c))
            v = sol + (h - 3 - sol) * lobe
            if c > 0.9:
                v = max(v, sol + (h - 3 - sol) * 0.55 * (c - 0.9) / 0.1)
            return int(v)
        return h - 1

    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        n = n_tabs * stripes_per_tab
        edges = [int(round(k * w / n)) for k in range(n + 1)]
        for k in range(n):
            weave(img, cols[k % len(cols)], rng, stains=0, box_=(edges[k], 0, edges[k + 1] - edges[k], h))
        px = img.load()
        e1 = edge or (230, 170, 50)
        e0 = edge_dark or _scale(e1, 0.62)
        bots = [bottom_of(x, w, h) for x in range(w)]
        for x in range(w):
            b = bots[x]
            for y in range(h):
                if y > b:
                    px[x, y] = (0, 0, 0, 0)
                elif edge is not None and y >= b - 1:
                    _put(px, x, y, _jitter(e1 if y == b - 1 else e0, rng, 8))
                elif y < 2:
                    r, g, bb, a = px[x, y]
                    px[x, y] = _scale((r, g, bb), 0.75) + (255,)
            if edge is not None:
                for xn in (x - 1, x + 1):
                    if 0 <= xn < w and bots[xn] < b:
                        for y in range(bots[xn] - 1, b + 1):
                            _put(px, x, y, _jitter(e1, rng, 8))
            if x in edges:
                for y in range(2, b - 1):
                    r, g, bb, a = px[x, y]
                    px[x, y] = _scale((r, g, bb), 0.8) + (255,)
        if top is not None:
            for y in range(0, 3):
                for x in range(w):
                    _put(px, x, y, _jitter(top if y < 2 else _scale(top, 0.65), rng, 8))
        if motif is not None:
            tw = w / n_tabs
            for t in range(n_tabs):
                cx, cy = int(t * tw + tw / 2), int(h * solid * 0.55) + 1
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        if abs(dx) + abs(dy) <= 2 and 0 <= cx + dx < w and 0 <= cy + dy < h and px[cx + dx, cy + dy][3]:
                            _put(px, cx + dx, cy + dy, _jitter(motif if abs(dx) + abs(dy) < 2 else _scale(motif, 0.7), rng, 6))
    return paint


def banner_painter(base, dark, gold, gold_dark, gold_light, seed, point="v", laurel=False, fringe=False, border=3, emblem="scales",
                   emblem_y=0.36, emblem_w=0.74, inner_line=True, body=0.74):
    """A banner (cut-out): base colour woven, a gold border, the gold emblem (scales / purse), optional laurel wreath
    under it; bottom: point "v" (a V point edged in gold), "steps" (a stepped V point in gold blocks), "flat"; fringe =
    a gold fringe along the bottom edge."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, base, rng, stains=1)
        px = img.load()
        bodyh = int(h * body) if point != "flat" else h - (6 if fringe else 0)
        for y in range(h):
            for x in range(w):
                dx = abs(x + 0.5 - w / 2)
                if y >= bodyh and point != "flat":
                    t = (y - bodyh) / max(1, h - bodyh - 1)
                    half = (w / 2) * (1 - t)
                    if point == "steps":
                        half = math.ceil(half / 3.0) * 3.0
                    if dx > half:
                        px[x, y] = (0, 0, 0, 0)
                        continue
                    if dx > half - border - (1 if point == "steps" else 0):
                        _put(px, x, y, _jitter(gold if (int(dx) + y) % 7 else gold_light, rng, 9))
                        continue
                    if inner_line and dx > half - border - 1.5:
                        _put(px, x, y, _jitter(dark, rng, 4))
                    continue
                if point == "flat" and fringe and y >= bodyh:
                    on = (x % 2 == 0) or y < bodyh + 2
                    if on:
                        _put(px, x, y, _jitter(gold if x % 4 else gold_dark, rng, 10))
                    else:
                        px[x, y] = (0, 0, 0, 0)
                    continue
                e = min(x, w - 1 - x, y)
                if point == "flat":
                    e = min(e, bodyh - 1 - y)
                if e < border:
                    _put(px, x, y, _jitter(gold if e > 0 else gold_dark, rng, 9))
                elif inner_line and e == border:
                    _put(px, x, y, _jitter(dark, rng, 4))
        if fringe and point != "flat":
            pass
        ew = int(w * emblem_w)
        eh = int(ew * (1.0 if emblem == "scales" else 1.0))
        cyc = int(h * emblem_y)

        def draw(d, W, H, S):
            cx, cy = W / 2, cyc * S
            if emblem == "scales":
                draw_scales(d, cx, cy, ew * S, eh * S, gold, gold_dark, gold_light, S=S)
            elif emblem == "purse":
                draw_purse(d, cx, cy, ew * S, eh * S, gold, gold_dark, gold_light, S=S)
            if laurel:
                draw_laurel(d, cx, cy + eh * S * 0.95, ew * S * 0.95, eh * S * 0.7, gold, gold_dark, S=S)
        overlay(img, (0, 0, w, h), draw)
    return paint


def carpet_painter(base, dark, gold, gold_dark, seed, style="medallion", fringe=True):
    """A rug lying on the ground (v from its back edge to its front edge): base field, dark outer border, gold lines,
    a gold pattern (medallion: a big lozenge medallion and corner pieces; scroll: a scroll border and a dark round
    centre; dots: a speckled field in a gold Greek-key border); fringe = gold tassels at the two ends (cut-out)."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, base, rng, stains=2)
        px = img.load()
        fr = 4 if fringe else 0
        for y in range(h):
            for x in range(w):
                if y < fr or y >= h - fr:
                    on = x % 3 != 2
                    if on:
                        _put(px, x, y, _jitter(gold if x % 3 == 0 else gold_dark, rng, 10))
                    else:
                        px[x, y] = (0, 0, 0, 0)
                    continue
                e = min(x, w - 1 - x, y - fr, h - 1 - fr - y)
                if e < 2:
                    _put(px, x, y, _jitter(dark, rng, 5))
                elif e in (3, 4):
                    _put(px, x, y, _jitter(gold, rng, 10))
                elif style == "scroll" and 6 <= e <= 13:
                    ph = (x + y) if (x < 14 or x > w - 15) else x
                    yy = e - 6
                    wave = 3.5 + 3.0 * math.sin((x if (y < 20 + fr or y > h - 21 - fr) else y) * 0.45)
                    if abs(yy - wave) < 1.0:
                        _put(px, x, y, _jitter(gold, rng, 10))
                    elif (int(ph) % 9 == 0 and 2 < yy < 6):
                        _put(px, x, y, _jitter(_scale(gold, 0.85), rng, 10))
                elif style == "dots" and 6 <= e <= 9:
                    lx, ly = (x + y) % 6, e - 6
                    if (lx < 3 and ly in (0, 3)) or (lx == 0) :
                        _put(px, x, y, _jitter(gold, rng, 10))
                elif e == 7 and style == "medallion":
                    _put(px, x, y, _jitter(_scale(gold, 0.9), rng, 10))
        cx, cy = w / 2, h / 2
        if style == "medallion":
            for y in range(fr, h - fr):
                for x in range(w):
                    dx, dy = abs(x + 0.5 - cx) / (w * 0.3), abs(y + 0.5 - cy) / (h * 0.26)
                    m = dx + dy
                    if 0.92 < m < 1.0 or 0.56 < m < 0.64:
                        _put(px, x, y, _jitter(gold, rng, 10))
                    elif m < 0.3:
                        _put(px, x, y, _jitter(gold if m > 0.2 else dark, rng, 8))
                    elif 0.64 <= m <= 0.92 and (x + y) % 5 == 0:
                        _put(px, x, y, _jitter(_mix(base, gold, 0.6), rng, 8))
            for sx in (0, 1):
                for sy in (0, 1):
                    ox = 12 if sx == 0 else w - 13
                    oy = 12 + fr if sy == 0 else h - 13 - fr
                    for dy in range(-4, 5):
                        for dx in range(-4, 5):
                            if abs(dx) + abs(dy) in (3, 4):
                                _put(px, ox + dx, oy + dy, _jitter(gold, rng, 10))
        elif style == "scroll":
            for y in range(fr, h - fr):
                for x in range(w):
                    r = math.hypot((x + 0.5 - cx) / (w * 0.22), (y + 0.5 - cy) / (h * 0.18))
                    if r < 0.8:
                        _put(px, x, y, _jitter(_scale(dark, 1.1), rng, 6))
                    elif r < 1.0:
                        _put(px, x, y, _jitter(gold if (int(math.atan2(y - cy, x - cx) * 6) % 2) else gold_dark, rng, 10))
            for k in range(26):
                x, y = rng.randrange(16, w - 16), rng.randrange(16 + fr, h - 16 - fr)
                if math.hypot((x - cx) / (w * 0.22), (y - cy) / (h * 0.18)) > 1.3:
                    for dx in (-1, 0, 1):
                        _put(px, x + dx, y, _jitter(_scale(gold, 0.8), rng, 10))
        elif style == "dots":
            for y in range(12 + fr, h - 12 - fr):
                for x in range(12, w - 12):
                    if rng.random() < 0.07:
                        _put(px, x, y, _jitter(_mix(base, gold, 0.65) if rng.random() < 0.6 else dark, rng, 8))
            for y in range(fr, h - fr):
                for x in range(w):
                    e = min(x, w - 1 - x, y - fr, h - 1 - fr - y)
                    if e == 11:
                        _put(px, x, y, _jitter(gold, rng, 10))
    return paint


def roll_painter(base, gold, seed, bands=3):
    """The wound surface of a rolled carpet (u along the roll): the field with a few gold bands across and a dark wrap
    line every few pixels round it."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, base, rng, stains=1)
        px = img.load()
        for y in range(h):
            for x in range(w):
                lx = x / w
                on_band = any(abs(lx - (k + 0.5) / bands) < 0.06 for k in range(bands)) or lx < 0.05 or lx > 0.95
                if on_band:
                    _put(px, x, y, _jitter(gold, rng, 10))
                elif (x // 3 + y // 3) % 5 == 0:
                    _put(px, x, y, _jitter(_mix(base, gold, 0.5), rng, 8))
                if y % 6 == 0:
                    r, g, b, a = px[x, y]
                    px[x, y] = _scale((r, g, b), 0.72) + (255,)
    return paint


def spiral_painter(base, gold, core=(200, 160, 110)):
    """The end of a roll: a spiral of the cloth (base / gold layers) round a light core."""
    def paint(img):
        rng = random.Random(sum(base))
        w, h = img.size
        px = img.load()
        cx, cy = w / 2, h / 2
        for y in range(h):
            for x in range(w):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                r = math.hypot(dx, dy)
                a = math.atan2(dy, dx)
                if r < w * 0.1:
                    c = core
                elif r < w * 0.15:
                    c = _scale(core, 0.5)
                else:
                    ph = (r * 5.0 / w - a / (2 * math.pi)) % 1.0
                    c = _scale(base, 0.55) if ph < 0.22 else (gold if ph < 0.4 else base)
                _put(px, x, y, _jitter(c, rng, 4))
    return paint


def flag_painter(base, dark, gold, seed, notch=0.32, border=False, patches=True):
    """A swallow-tailed flag (u along the fly from the pole, v down): woven base, darker blotches (pixel style),
    optional gold border, the notch cut out."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, base, rng, stains=0)
        px = img.load()
        for y in range(h):
            for x in range(w):
                n0 = 1.0 - notch
                if x > w * n0 and abs(y + 0.5 - h / 2) < (x - w * n0) * (h / 2) / (w * notch):
                    px[x, y] = (0, 0, 0, 0)
                    continue
                if border and (y < 2 or y >= h - 2 or x < 2):
                    _put(px, x, y, _jitter(gold, rng, 10))
                elif patches and ((x // 4) * 7 + (y // 4) * 13 + seed) % 11 == 0:
                    _put(px, x, y, _jitter(dark, rng, 6))
                elif patches and ((x // 4) * 5 + (y // 4) * 3 + seed) % 17 == 0:
                    _put(px, x, y, _jitter(_mix(base, gold, 0.45), rng, 6))
    return paint


def pennant_painter(base, edge, seed):
    """A triangular bunting pennant pointing down (cut-out), an edge colour along the two slanted sides, a small mark."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, base, rng, stains=0)
        px = img.load()
        for y in range(h):
            half = (w / 2) * (1 - y / h)
            for x in range(w):
                dx = abs(x + 0.5 - w / 2)
                if dx > half:
                    px[x, y] = (0, 0, 0, 0)
                elif dx > half - 1.6 or y < 2:
                    _put(px, x, y, _jitter(edge, rng, 8))
        cx = w // 2
        for dy in range(-1, 2):
            if px[cx, h // 3 + dy][3]:
                _put(px, cx, h // 3 + dy, _jitter(edge, rng, 8))
    return paint


def wood_painter(base, dark, seed, vertical=False):
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        ml.fine_wood(img, (0, 0, w, h), _rgb(base), _rgb(dark), h if not vertical else 8, rng, joints=False, knots=0.08, grain=0.14, shade=0.08,
                     **({"vertical": True} if vertical else {}))
    return paint


def band_painter(seed, base="5a5c62", light="8a8c92", shade="34363a"):
    """Grey riveted iron bands: hammered iron, a lighter top edge, a big square rivet in the middle, small ones."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _rgb(base)
                if y == 0:
                    c = _rgb(light)
                elif y == h - 1:
                    c = _rgb(shade)
                _put(px, x, y, _jitter(c, rng, 7))
        for cx, r in ((w // 2, 2), (4, 1), (w - 5, 1)):
            for y in range(max(1, h // 2 - r), min(h - 1, h // 2 + r + 1)):
                for x in range(cx - r, cx + r + 1):
                    _put(px, x, y, (40, 40, 44) if (x == cx + r or y == h // 2 + r) else (176, 178, 184))
    return paint


def iron_painter(seed, base="2e2c2e", hi="5a5658", brass=None):
    """Wrought iron: near-black hammered iron, a lighter edge line, a few warm brass glints (optional)."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _rgb(base)
                if y in (0, h - 1):
                    c = _scale(c, 0.8)
                elif y == 1:
                    c = _rgb(hi)
                k = 1.0 + 0.1 * math.sin(x * 0.9 + y * 0.3)
                _put(px, x, y, _jitter(_scale(c, k), rng, 6))
        if brass:
            for x in range(3, w, 9):
                _put(px, x, h // 2, _rgb(brass))
    return paint


def filigree_painter(seed, iron="2a2828", hi="6a6062", brass="b8862a", kind="arch"):
    """A cut-out wrought-iron scroll panel (the spandrels of the arches): C and S scrolls, a central lozenge with a
    brass rosette, leaf tips; transparent between the bars."""
    def paint(img):
        from PIL import Image, ImageDraw
        w, h = img.size
        S = 4
        big = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        W, H = w * S, h * S
        lw = int(S * 1.6)
        c = _rgb(iron) + (255,)
        # two big C scrolls back to back, two smaller ones above, a lozenge in the middle
        for sx in (-1, 1):
            cx = W / 2 + sx * W * 0.24
            d.arc((cx - W * 0.2, H * 0.2, cx + W * 0.2, H * 0.95), 0 if sx > 0 else 180, 360 if sx > 0 else 540, fill=c, width=lw)
            d.arc((cx - W * 0.09, H * 0.38, cx + W * 0.09, H * 0.7), 90, 400, fill=c, width=lw)
            d.arc((cx - W * 0.13, H * 0.02, cx + W * 0.13, H * 0.42), 180 if sx > 0 else 0, 300 if sx > 0 else 120, fill=c, width=lw)
            d.ellipse((cx + sx * W * 0.16 - S * 2, H * 0.12 - S * 2, cx + sx * W * 0.16 + S * 2, H * 0.12 + S * 2), fill=c)
        d.polygon([(W / 2, H * 0.12), (W / 2 + W * 0.08, H * 0.5), (W / 2, H * 0.88), (W / 2 - W * 0.08, H * 0.5)], outline=c, width=lw)
        d.ellipse((W / 2 - S * 3, H * 0.5 - S * 3, W / 2 + S * 3, H * 0.5 + S * 3), fill=_rgb(brass) + (255,))
        d.line((0, H - lw / 2, W, H - lw / 2), fill=c, width=lw)
        small = big.resize((w, h), Image.BOX)
        px = small.load()
        rng = random.Random(seed)
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a < 90:
                    px[x, y] = (0, 0, 0, 0)
                else:
                    col = (r, g, b) if (r, g, b) != (0, 0, 0) else _rgb(iron)
                    if a < 255 and (r, g, b) == tuple(_rgb(iron)):
                        col = _rgb(hi)
                    _put(px, x, y, _jitter(col, rng, 5))
        img.paste(small, (0, 0))
    return paint


def burlap_painter(base, seed, straps=None):
    """A sack's burlap: coarse weave, darker fold streaks, a lighter middle; straps = a colour for two bands."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        ml._weave(img, (0, 0, w, h), _rgb(base), rng, stains=0)
        px = img.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                k = 0.86 + 0.2 * math.sin(math.pi * (x + 0.5) / w) - 0.08 * (abs(math.sin(x * 0.55 + y * 0.08)) > 0.93)
                c = _scale((r, g, b), k)
                if straps is not None and (abs(x - w * 0.3) < 2 or abs(x - w * 0.7) < 2):
                    c = _scale(straps, 0.9 + 0.1 * (y % 3 == 0))
                px[x, y] = c + (255,)
    return paint


def chest_painter(seed, base="8a5a2c", dark="4a2c12", corners=None):
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        ml.fine_wood(img, (0, 0, w, h), _rgb(base), _rgb(dark), 8, rng, joints=False, knots=0.1, grain=0.12, shade=0.06)
        px = img.load()
        if corners:
            for y in range(h):
                for x in range(w):
                    if (x < 4 or x >= w - 4) and (y < 4 or y >= h - 4):
                        _put(px, x, y, _jitter(corners, rng, 10))
    return paint


def runner_painter(base, dark, gold, seed, motif="meander", top_col=None, fringe=False, emblem=None, gold_dark=None, gold_light=None):
    """A table runner hanging over a counter's front: base colour, gold border; motif "meander" (a gold Greek key
    band), "diamond" (a top band of top_col with a big lozenge pointing down into the base), "scales" (the emblem);
    fringe = gold fringe at the bottom (cut-out)."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, base, rng, stains=0)
        px = img.load()
        fr = 4 if fringe else 0
        for y in range(h):
            for x in range(w):
                if y >= h - fr:
                    if x % 2 == 0:
                        _put(px, x, y, _jitter(gold, rng, 10))
                    else:
                        px[x, y] = (0, 0, 0, 0)
                    continue
                e = min(x, w - 1 - x, y, h - 1 - fr - y)
                if motif == "diamond":
                    dx = abs(x + 0.5 - w / 2) / (w / 2)
                    top_h = h * 0.42
                    lim = top_h + (h * 0.38) * (1 - dx)
                    if y < lim:
                        c = top_col
                        if abs(y - lim) < 2:
                            c = gold
                        _put(px, x, y, _jitter(c, rng, 5))
                    dd = abs(x + 0.5 - w / 2) + abs(y + 0.5 - h * 0.6)
                    if dd < 5:
                        _put(px, x, y, _jitter(gold if dd < 3 else base, rng, 6))
                    if 5 <= dd < 7:
                        _put(px, x, y, _jitter(gold, rng, 6))
                if e < 2:
                    _put(px, x, y, _jitter(gold, rng, 10))
                elif e == 2:
                    _put(px, x, y, _jitter(dark, rng, 5))
                elif motif == "meander" and h - fr - 12 <= y <= h - fr - 5:
                    ly, lx = y - (h - fr - 12), x % 8
                    on = (ly in (0, 7)) or (lx == 0 and ly < 6) or (lx == 5 and ly > 1) or (ly == 3 and 1 <= lx <= 5)
                    if on:
                        _put(px, x, y, _jitter(gold, rng, 10))
        if emblem == "scales":
            s = int(min(w, h) * 0.62)

            def draw(d, W, H, S):
                draw_scales(d, W / 2, H * 0.44, s * S, s * S, gold, gold_dark or _scale(gold, 0.6), gold_light or _scale(gold, 1.2), S=S)
            overlay(img, (0, 0, w, h), draw)
    return paint


def pages_painter(seed):
    """An open book seen from above: two cream pages with lines of writing, the dark gutter in the middle."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _rgb("efe2c4")
                if abs(x + 0.5 - w / 2) < 1.2:
                    c = _rgb("8a7050")
                elif y in (0, h - 1) or x in (0, w - 1):
                    c = _rgb("6a4020")
                elif 3 <= y <= h - 4 and y % 2 == 1 and 2 < (x % (w // 2)) < w // 2 - 2 and rng.random() < 0.8:
                    c = _rgb("6a5a48")
                _put(px, x, y, _jitter(c, rng, 4))
    return paint


FABRICS = {   # cloth bolts: base, pattern colour
    "red": ("a82a2a", "d4a040"), "blue": ("2e4a8a", "7090c0"), "green": ("3e6e34", "9ab060"), "cream": ("e2d2b0", "b89a70"),
    "orange": ("c8702a", "f0b050"), "olive": ("6e6a34", "a8a060"), "wine": ("6a1a2a", "b0605a"), "teal": ("2a6a6e", "70a8a8"),
}


def fabric_painter(col):
    base, pat = (_rgb(c) for c in FABRICS[col])

    def paint(img):
        rng = random.Random(sum(map(ord, col)))
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _scale(base, 1.0 + (0.035 if (x + y) % 2 == 0 else -0.035) + 0.04 * math.sin(x * 0.37 + y * 0.11))
                if (x + y) % 8 == 0 or (x - y) % 8 == 0:
                    c = _mix(c, pat, 0.35)
                if y % 4 == 0:
                    c = _scale(c, 0.84)
                if x in (0, w - 1):
                    c = _scale(pat, 0.9)
                _put(px, x, y, _jitter(c, rng, 4))
    return paint


def bolt_end_painter(col):
    base = _rgb(FABRICS[col][0])

    def paint(img):
        rng = random.Random(7 + sum(map(ord, col)))
        w, h = img.size
        px = img.load()
        cx, cy = w / 2, h / 2
        for y in range(h):
            for x in range(w):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                r = math.hypot(dx, dy)
                a = math.atan2(dy, dx)
                if r < w * 0.12:
                    c = _rgb("c8a070")
                elif r < w * 0.17:
                    c = _rgb("6a4a2a")
                else:
                    ph = (r * 6.0 / w - a / (2 * math.pi)) % 1.0
                    c = _scale(base, 0.55 if ph < 0.25 else (1.12 if ph < 0.5 else 1.0))
                _put(px, x, y, _jitter(c, rng, 3))
    return paint


def sign_painter(kind, seed, board="6e4628", board_dark="3a2412", frame="4a2e14", gold=(236, 176, 52), gold_dark=(140, 88, 20),
                 gold_light=(252, 224, 130), clip=0, frame_col=None):
    """A hanging sign board (u across, v down): dark planks in a frame (frame_col: a gold frame line), clipped corners
    (clip px, transparent), the painted emblem: "purse" (a gold purse beside a stack of coins) or "scroll"."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        ml.fine_wood(img, (0, 0, w, h), _rgb(board), _rgb(board_dark), 8, rng, joints=False, knots=0.1, grain=0.12, shade=0.06)
        px = img.load()
        for y in range(h):
            for x in range(w):
                e = min(x, y, w - 1 - x, h - 1 - y)
                cor = min(x, w - 1 - x) + min(y, h - 1 - y)
                if clip and cor < clip:
                    px[x, y] = (0, 0, 0, 0)
                    continue
                if e < 3 or (clip and cor < clip + 3):
                    _put(px, x, y, _jitter(_rgb(frame), rng, 5))
                elif frame_col is not None and (e == 4 or (clip and clip + 4 <= cor <= clip + 4)):
                    _put(px, x, y, _jitter(frame_col, rng, 8))
                elif e == 3:
                    _put(px, x, y, _jitter(_scale(_rgb(frame), 0.6), rng, 4))

        def draw(d, W, H, S):
            if kind == "purse":
                draw_purse(d, W * 0.42, H * 0.5, W * 0.48, H * 0.56, gold, gold_dark, gold_light, S=S)
                draw_coins(d, W * 0.73, H * 0.74, W * 0.24, 4, gold, gold_dark, gold_light, S=S)
            elif kind == "scroll":
                draw_scroll(d, W * 0.5, H * 0.48, W * 0.8, H * 0.5, gold, gold_dark, gold_light, S=S)
        overlay(img, (0, 0, w, h), draw)
        for (x, y) in ((5, 5), (w - 6, 5), (5, h - 6), (w - 6, h - 6)):
            if px[x, y][3]:
                _put(px, x, y, (170, 170, 176))
    return paint


def gore_painter(base, dark, gold, seed, ornament=True, faded=0.0, edge=None):
    """A cone-roof gore (u across, v from the apex down): woven cloth, a dark seam at both sides, gold filigree scrolls
    (ornament) on the coloured gores, faded blotches (weathered), an edge line (gold piping) at the bottom."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, base, rng, stains=2)
        px = img.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                k = 0.86 + 0.18 * math.sin(math.pi * (x + 0.5) / w) + 0.06 * (y / h)
                if x in (0, w - 1):
                    k *= 0.72
                c = _scale((r, g, b), k)
                if faded and rng.random() < faded * (0.4 + 0.6 * math.sin(x * 0.13 + y * 0.07) ** 2):
                    c = _mix(c, (225, 205, 170), 0.18)
                px[x, y] = c + (255,)
        if ornament:
            def draw(d, W, H, S):
                cx = W / 2
                lw = int(S * 1.3)
                for k in range(3):
                    y0 = H * (0.3 + 0.2 * k)
                    r = W * (0.16 + 0.04 * k)
                    for sx in (-1, 1):
                        d.arc((cx + sx * r * 0.8 - r, y0 - r, cx + sx * r * 0.8 + r, y0 + r), 200 if sx < 0 else -20, 340 if sx < 0 else 160,
                              fill=gold, width=lw)
                        d.ellipse((cx + sx * r * 1.6 - S * 1.5, y0 - S * 1.5, cx + sx * r * 1.6 + S * 1.5, y0 + S * 1.5), fill=gold)
                    d.line((cx, y0 - r * 0.9, cx, y0 + r * 0.9), fill=gold, width=lw)
                d.line((cx - W * 0.4, H * 0.86, cx + W * 0.4, H * 0.86), fill=gold, width=lw)
            overlay(img, (0, 0, w, h), draw)
        if edge is not None:
            for y in range(h - 3, h):
                for x in range(w):
                    _put(px, x, y, _jitter(edge if y < h - 1 else _scale(edge, 0.6), rng, 8))
    return paint


def solid_painter(c, noise=6, seed=0):
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                _put(px, x, y, _jitter(_rgb(c) if isinstance(c, str) else c, rng, noise))
    return paint


def add_regions(atlas, regions, size=None):
    """Adds the (name, w, h, painter) regions tallest first (fewest wasted rows); checks the atlas size."""
    for name, w, h, p in sorted(regions, key=lambda r: (-r[2], -r[1])):
        atlas.add(name, w, h, p)
    if size is not None and atlas.size != size:
        raise AssertionError("the atlas grew to %d px (expected %d): repack the regions" % (atlas.size, size))


# ---------------------------------------------------------------- geometry
def roof_drop(t, a=0.45):
    """Fraction of the drop at t (0 = ridge / apex, 1 = eave): steep at the top, flatter at the eave (a marquee)."""
    return a * t + (1 - a) * (1 - (1 - t) ** 2)


def skirt(bone, name, top, bot, region, nx, ny, a=0.45, folds=0, sag=0.06, belly=0.08, th=0.035, overlap=0.03):
    """A marquee roof skirt between a top curve top(s) (on the ridge / apex) and an eave curve bot(s), s in [0, 1]:
    linear in plan, the height falling steeply from the top and flattening to the eave (roof_drop); the cloth bellies
    down by `belly` mid-slope and by `sag` between `folds` seams (soft, not boxy). Returns P(s, t)."""
    def P(s, t):
        a0, b0 = top(s), bot(s)
        p = a0 + (b0 - a0) * t
        y = a0[1] - (a0[1] - b0[1]) * roof_drop(t, a)
        dip = belly * math.sin(math.pi * t)
        if folds:
            frac = (s * folds) % 1.0
            dip += sag * math.sin(math.pi * frac) * math.sin(math.pi * min(1.0, t * 1.15))
        return v3(p[0], y - dip, p[2])
    loft(bone, name, P, nx, ny, region, th=th, overlap=overlap)
    return P


def surface_offset(P, s, t, d, eps=1e-3):
    """The point P(s, t) pushed d along the surface's upward normal."""
    p = P(s, t)
    du = P(min(1.0, s + eps), t) - P(max(0.0, s - eps), t)
    dv = P(s, min(1.0, t + eps)) - P(s, max(0.0, t - eps))
    n = np.cross(du, dv)
    if np.linalg.norm(n) < 1e-9:
        return p + UP * d
    n = norm(n)
    if n[1] < 0:
        n = -n
    return p + n * d


def swag(bone, name, a, b, h, region, out=(0, 0, 1), sag=0.25, droop=0.0, nx=3, th=0.025, curl=0.05):
    """A curved valance swag hanging from the edge a - b (its top, drooping by `droop` in the middle): the bottom edge
    curves down by `sag` between the ends (the dags of the region follow it), flaring a little towards `out`."""
    a, b, out = v3(*a), v3(*b), norm(v3(*out))

    def P(s, t):
        e = a + (b - a) * s - UP * (droop * math.sin(math.pi * s))
        hh = h + sag * math.sin(math.pi * s)
        return e - UP * (hh * t) + out * (0.02 + curl * t * math.sin(math.pi * s) + 0.03 * t)
    loft(bone, name, P, nx, 2, region, th=th)
    return P


def valance(bone, name, c0, c1, out, h=0.5, region="valance", n=None, th=0.025):
    """A straight dagged valance from c0 to c1 (its top edge), flaring a little out (towards `out`)."""
    c0, c1, out = v3(*c0), v3(*c1), v3(*out)

    def V(s, t):
        e = c0 + (c1 - c0) * s
        return e + UP * 0.02 - UP * (h * t) + out * (0.03 + 0.05 * t)
    L = np.linalg.norm(c1 - c0)
    loft(bone, name, V, n or max(1, int(round(L / 2.5))), 1, region, th=th)


def drape(bone, det, name, top_a, top_b, tie, bot_a, bot_b, normal, region, nx=3, tie_region="rope"):
    """A curtain tied back: hangs from the edge top_a - top_b, gathered at `tie` (a cord band), flaring again below to
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


def wall(bone, name, a, b, y0, y1, out, region, nx=6, fold=0.05, ny=2):
    """A hanging canvas wall from a (left) to b on the ground line, y0..y1, soft vertical folds towards `out`."""
    a, b, out = v3(*a), v3(*b), v3(*out)

    def P(s, t):
        p = a + (b - a) * s
        return v3(p[0], y1 - (y1 - y0) * t, p[2]) + out * (fold * math.sin(s * math.pi * nx) * (0.4 + 0.6 * t))
    loft(bone, name, P, nx, ny, region, th=0.03)


def band(bone, name, x, z, half, y, h, region="c_band"):
    """An iron band round a squared post (centre x, z): a riveted face on each side, plain iron on top and below."""
    box(bone, name, (x - half, y, z - half), (x + half, y + h, z + half), {"all": region, "+2": "iron", "-2": "iron"}, stretch=True)


def banded_post(shell, det, name, x, z, top, d=0.5, foot_h=0.55, foot="stone", bands=(), cap=None, collide_to=None, wood="c_post",
                band_region="c_band", foot_w=None):
    """A big squared post: a foot block (stone or dark wood, an iron band on it), the post (warm wood), riveted iron
    bands at the heights `bands`, an optional cap block (size, height) on top; collides up to collide_to (default top)."""
    fw = foot_w or (d / 2 + 0.08)
    if foot:
        box(shell, name + "_foot", (x - fw, 0.0, z - fw), (x + fw, foot_h, z + fw), {"all": foot, "+2": "stone_top" if foot == "stone" else "end_grain"})
        band(det, name + "_fband", x, z, fw + 0.015, foot_h - 0.14, 0.1, band_region)
    beam(shell, name, (x, foot_h if foot else 0.0, z), (x, top, z), d, {"all": wood, "+1": "end_grain", "-1": "end_grain"})
    for k, y in enumerate(bands):
        band(det, "%s_band_%d" % (name, k), x, z, d / 2 + 0.025, y, 0.16, band_region)
    if cap:
        cw, chh = cap
        box(shell, name + "_cap", (x - cw / 2, top, z - cw / 2), (x + cw / 2, top + chh, z + cw / 2), {"all": "wood", "+2": "end_grain"})
    hc = max(fw, d / 2)
    collide((x - hc, 0.0, z - hc, x + hc, collide_to if collide_to is not None else top, z + hc))


def flag(bone, name, top, direction, length, height, region, wave=0.1, droop=0.08, nx=4):
    """A swallow-tail flag flying from the pole point `top` towards `direction` (horizontal), waving."""
    d = norm(v3(*direction) * v3(1, 0, 1))
    side = norm(np.cross(UP, d))
    top = v3(*top)

    def P(s, t):
        return top + d * (length * s) - UP * (height * t + droop * s * s) + side * (wave * math.sin(2.2 * math.pi * s) * s)
    loft(bone, name, P, nx, 1, region, th=0.02, u_hint=d, v_hint=-UP)


def bunting(bone, name, a, b, n, regions, sag=0.15, size=(0.2, 0.32), rope_d=0.025, rope_region="rope"):
    """A rope from a to b sagging by `sag`, with n triangular pennants (regions in turn) hanging from it."""
    a, b = v3(*a), v3(*b)
    ml.rope(bone, name + "_rope", a, b, d=rope_d, sag=sag, segs=3, region=rope_region)
    dirn = norm(b - a)
    nrm = norm(np.cross(dirn, UP)) if abs(dirn[1]) < 0.95 else Z
    if nrm[2] < 0:
        nrm = -nrm
    for i in range(n):
        t = (i + 0.5) / n
        p = a + (b - a) * t - UP * (4 * sag * t * (1 - t))
        ml.plate(bone, "%s_%d" % (name, i), p - UP * (size[1] / 2 + 0.01), size[0], size[1], regions[i % len(regions)], normal=nrm, up=UP, th=0.008)


def octo_bar(bone, name, p0, p1, r, region, end=None):
    """A round bar from p0 to p1 (octagonal: two boxes turned 45 degrees), `end` on its two ends."""
    p0, p1 = v3(*p0), v3(*p1)
    d = norm(p1 - p0)
    L = np.linalg.norm(p1 - p0)
    e1 = norm(np.cross(d, UP)) if abs(d[1]) < 0.9 else X
    e2 = np.cross(d, e1)
    for k, ang in enumerate((0.0, math.pi / 4)):
        aa = e1 * math.cos(ang) + e2 * math.sin(ang)
        bb = np.cross(d, aa)
        add_cube(bone, "%s_%d" % (name, k), (p0 + p1) / 2, np.column_stack([d, aa, bb]), (L, 2 * r * 0.93, 2 * r * 0.93),
                 {"all": region, "+1": end or region, "-1": end or region}, u_dir=d, stretch=True)


def carpet_roll(bone, name, p0, p1, r, surf, end):
    """A rolled carpet lying from p0 to p1 (octagonal), its spiral on the two ends."""
    octo_bar(bone, name, p0, p1, r, surf, end=end)


def bolt(bone, name, p0, p1, r, col, prefix="c_"):
    """A bolt of cloth (standing or lying) from p0 to p1, the wound fabric round it, its spiral on the ends."""
    octo_bar(bone, name, p0, p1, r, prefix + "fab_" + col, end=prefix + "end_" + col)


def scroll(bone, name, c, length=0.4, r=0.055, yaw=0.0, region="beige", end="white"):
    """A rolled scroll lying on its side (two boxes turned 45 degrees about its axis), along yaw."""
    c = v3(*c)
    for k, a in enumerate((0.0, math.pi / 4)):
        add_cube(bone, "%s_%d" % (name, k), c, ry(yaw) @ rx(a), (length, 2 * r * 0.83, 2 * r * 0.83), {"all": region, "+1": end, "-1": end},
                 stretch=True)


def book(bone, name, foot, size=(0.24, 0.07, 0.32), yaw=0.0, cover="leather"):
    f = v3(*foot)
    add_cube(bone, name, f + UP * size[1] / 2, ry(yaw), size, {"all": "white", "+2": cover, "-2": cover, "-1": cover}, stretch=True)


def book_stack(bone, name, foot, n, rng, covers=("cloth_red", "leather", "cloth_blue", "leather_dark", "cloth_dark"), w=0.26, d=0.34):
    f = v3(*foot)
    y = 0.0
    for k in range(n):
        th = 0.06 + 0.03 * rng.random()
        book(bone, "%s_%d" % (name, k), f + UP * y, size=(w * rng.uniform(0.85, 1.05), th, d * rng.uniform(0.85, 1.0)), yaw=rng.uniform(-0.25, 0.25),
             cover=covers[k % len(covers)])
        y += th
    return y


def open_book(bone, name, foot, w=0.5, d=0.34, yaw=0.0, pages="c_pages", tilt=0.0):
    """An open book lying on foot: the cover (a dark board), the two page blocks rising a little to the gutter."""
    f = v3(*foot)
    R = ry(yaw) @ rx(-tilt)
    add_cube(bone, name + "_cover", f + R @ v3(0, 0.015, 0), R, (w + 0.04, 0.03, d + 0.03), "leather_dark", stretch=True)
    add_cube(bone, name + "_pages", f + R @ v3(0, 0.05, 0), R, (w, 0.04, d), {"all": "white", "+2": pages}, stretch=True, u_dir=R[:, 0], v_dir=R[:, 2])


def chest(shell, det, name, foot, size=(0.9, 0.62, 0.6), yaw=0.0, wood="c_chest", metal="iron", domed=True, solid=True, trim="gold"):
    """An iron-banded chest: the body, a domed lid (two stepped boxes) or flat, metal bands over body and lid, corner
    plates, a lock plate; collides when solid."""
    f = v3(*foot)
    R = ry(yaw)
    w, h, d = size
    bh = h * 0.64
    add_cube(shell, name + "_body", f + UP * bh / 2, R, (w, bh, d), {"all": wood, "-2": "plank_dark"}, stretch=True)
    if domed:
        add_cube(shell, name + "_lid", f + UP * (bh + (h - bh) * 0.32), R, (w + 0.02, (h - bh) * 0.64, d + 0.02), wood, stretch=True)
        add_cube(shell, name + "_lid_top", f + UP * (h - (h - bh) * 0.17), R, (w, (h - bh) * 0.34, d * 0.66), wood, stretch=True)
    else:
        add_cube(shell, name + "_lid", f + UP * (bh + (h - bh) / 2), R, (w + 0.03, h - bh, d + 0.03), wood, stretch=True)
    for k, sx in enumerate((-0.36, 0.0, 0.36) if w > 0.7 else (-0.3, 0.3)):
        add_cube(det, "%s_band_%d" % (name, k), f + R @ v3(sx * w, h * 0.5, 0), R, (0.06, h + 0.02, d + 0.03), metal, stretch=True)
    add_cube(det, name + "_rim", f + UP * bh, R, (w + 0.04, 0.05, d + 0.04), metal, stretch=True)
    add_cube(det, name + "_lock", f + R @ v3(0, bh - 0.02, d / 2 + 0.02), R, (0.13, 0.17, 0.03), trim)
    if solid:
        ex = abs(math.cos(yaw)) * w / 2 + abs(math.sin(yaw)) * d / 2
        ez = abs(math.sin(yaw)) * w / 2 + abs(math.cos(yaw)) * d / 2
        collide((f[0] - ex, f[1], f[2] - ez, f[0] + ex, f[1] + h, f[2] + ez))


def iron_crate(shell, det, name, foot, size=(0.7, 0.6, 0.6), yaw=0.0, region="crate", top="crate_top", content=None, solid=True,
               metal="iron", bands=2):
    """A crate with metal bands round it (two horizontal bands, or vertical corner straps)."""
    if not hasattr(size, "__len__"):
        size = (size, size, size)
    f = v3(*foot)
    ml.crate(shell, name, f, size=size, yaw=yaw, region=region, top=top, content=content, solid=solid)
    R = ry(yaw)
    w, h, d = size
    for k in range(bands):
        y = h * (0.2 + 0.6 * k / max(1, bands - 1)) if bands > 1 else h * 0.5
        add_cube(det, "%s_band_%d" % (name, k), f + UP * y, R, (w + 0.025, 0.06, d + 0.025), metal, stretch=True)


def big_sack(shell, det, name, foot, yaw=0.0, w=0.72, h=1.0, region="c_burlap", tie="rope", solid=True):
    """A big tied burlap sack: a tall bulging body narrowing upwards, a tied neck, a flared bunched top."""
    f = v3(*foot)
    R = ry(yaw)
    for k, (y0, y1, s) in enumerate(((0.0, 0.1, 0.84), (0.1, 0.42, 1.0), (0.42, 0.62, 0.86), (0.62, 0.76, 0.62))):
        for j in range(2):
            q = 0.84 if j else 1.0
            add_cube(shell, "%s_%d_%d" % (name, k, j), f + UP * (h * (y0 + y1) / 2), R @ ry(math.pi / 4 * j + 0.06 * k),
                     (w * s * q, h * (y1 - y0), w * s * q), region, stretch=True)
    add_cube(shell, name + "_neck", f + UP * (h * 0.81), R, (w * 0.32, h * 0.1, w * 0.32), region, stretch=True)
    add_cube(det, name + "_tie", f + UP * (h * 0.8), R, (w * 0.38, 0.07, w * 0.38), tie)
    for j in range(2):
        add_cube(shell, "%s_top_%d" % (name, j), f + UP * (h * 0.92), R @ ry(0.4 + math.pi / 4 * j), (w * 0.5, h * 0.16, w * 0.46), region, stretch=True)
    if solid:
        collide((f[0] - w / 2, f[1], f[2] - w / 2, f[0] + w / 2, f[1] + h * 0.8, f[2] + w / 2))


def square_sack(shell, det, name, foot, size=(0.8, 0.75, 0.6), yaw=0.0, region="c_burlap", solid=True):
    """A plump boxy grain sack (as in the pixel pictures): a body, a rounded top roll, a bunched tied top."""
    f = v3(*foot)
    R = ry(yaw)
    w, h, d = size
    add_cube(shell, name + "_body", f + UP * (h * 0.4), R, (w, h * 0.8, d), region, stretch=True)
    add_cube(shell, name + "_top", f + UP * (h * 0.86), R, (w * 0.86, h * 0.14, d * 0.84), region, stretch=True)
    add_cube(det, name + "_knot", f + UP * (h * 0.97), R, (w * 0.3, h * 0.12, d * 0.3), region, stretch=True)
    if solid:
        ex = abs(math.cos(yaw)) * w / 2 + abs(math.sin(yaw)) * d / 2
        ez = abs(math.sin(yaw)) * w / 2 + abs(math.cos(yaw)) * d / 2
        collide((f[0] - ex, f[1], f[2] - ez, f[0] + ex, f[1] + h * 0.9, f[2] + ez))


def potion_row(det, name, x0, x1, y, z, rng, colours, n=None, glow=False, rmin=0.055, rmax=0.08):
    """A row of potion bottles standing on a board from x0 to x1 at height y (round, tall, flask shapes in turn)."""
    n = n or max(2, int((x1 - x0) / 0.19))
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n + rng.uniform(-0.02, 0.02)
        r = rng.uniform(rmin, rmax)
        shape = ("round", "tall", "round", "flask")[i % 4]
        ml.bottle(det, "%s_%d" % (name, i), (x, y, z + rng.uniform(-0.04, 0.04)), colours[i % len(colours)], r=r, h=r * rng.uniform(2.2, 3.0),
                  shape=shape, neck_h=0.06, glow=glow)


def lantern_bracket(shell, det, name, mount, out, drop=0.45, size=0.36, metal="iron", arm=0.42, brace=True):
    """A hanging lantern on an iron bracket from a post face: the arm along `out`, a brace under it, the lantern
    hanging from its tip on a short chain."""
    mount, out = v3(*mount), norm(v3(*out))
    tip = mount + out * arm
    beam(det, name + "_arm", mount, tip, 0.05, metal, extend=0.02)
    if brace:
        beam(det, name + "_brace", mount - UP * 0.32, tip - UP * 0.02, 0.04, metal)
    add_cube(det, name + "_hook", tip - UP * 0.05, EYE, (0.06, 0.1, 0.06), metal)
    ml.lantern(shell, name, tip - UP * drop, size=size, metal=metal, chain_to=tip - UP * 0.06)


def standing_lantern(shell, det, name, foot, size=0.34, metal="iron"):
    """A lantern standing on a barrel / counter: a metal base, the lit lantern body (rebuilt lit), a ring on top."""
    f = v3(*foot)
    add_cube(det, name + "_base", f + UP * 0.03, EYE, (size * 1.05, 0.06, size * 1.05), metal)
    ml.lantern(shell, name, f + UP * (0.06 + size * 0.65), size=size, metal=metal)


def herbs_rod(shell, det, name, a, b, n, kinds=("herbs", "herbs_dry"), length=(0.42, 0.6), width=0.32, rng=None, rod_region="wood_dark"):
    """A rod from a to b with n bunches of herbs hanging from it."""
    a, b = v3(*a), v3(*b)
    rng = rng or random.Random(5)
    beam(det, name + "_rod", a, b, 0.05, rod_region)
    for i in range(n):
        t = (i + 0.5) / n
        p = a + (b - a) * t
        ml.hanging_bunch(det, "%s_%d" % (name, i), p - UP * 0.02, kind=kinds[i % len(kinds)], length=rng.uniform(*length), width=width,
                         string=rng.uniform(0.04, 0.12))


def ivy_hang(det, name, top, length, width, normal=(0, 0, 1)):
    ml.vine(det, name, top, length, width, normal=normal, region="ivy")


def ivy_bush(det, name, foot, h=0.6, w=0.6, rng=None):
    """A little bush of ivy at a post foot (crossed cut-out planes)."""
    f = v3(*foot)
    ml.crossed(det, name, f + UP * h / 2, w, h, "ivy", yaw=(rng.uniform(0, 1) if rng else 0.3))


def guy(det, name, top, ground, sag=0.05, d=0.05, peg_region="wood_dark"):
    """A guy rope from a post top to a peg driven into the ground (the peg is added; merchant atlases have no "peg")."""
    ml.rope(det, name, top, ground, d=d, sag=sag, segs=2)
    p, towards = v3(*ground), v3(*top)
    away = towards - p
    away[1] = 0
    away = -norm(away) if np.linalg.norm(away) > 1e-6 else v3(0, 0, 1)
    beam(det, name + "_peg", p - UP * 0.1 - away * 0.04, p + UP * 0.32 + away * 0.15, 0.09, {"all": peg_region, "+1": "end_grain", "-1": "end_grain"})


def rope_coil(det, name, x, z, y, half, n=2, region="rope"):
    for k in range(n):
        yy = y - 0.12 * k
        box(det, "%s_%d" % (name, k), (x - half, yy, z - half), (x + half, yy + 0.1, z + half), region)
