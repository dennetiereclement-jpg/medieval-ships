"""Shared painters and props of the market tents of group E (1.26.0): tente_draperie, tente_fleur_de_lys, tente_cordages.

Built on merchantlib / tentlib WITHOUT modifying them (what is needed of the camp merchant tent's helpers is copied
here). Every generator of the group does:

    import props_e as pe
    ml = pe.ml
    ml.setup(NAME); atlas = ml.Atlas(NAME, colour="red"); atlas.add(...)   # its own atlas textures/entity/<id>.png
    root = ml.Bone(NAME); shell = ml.Bone("shell", parent=root); det = ml.Bone("detail", parent=root)
    ... pe.post / pe.pyramid_roof / pe.swag / pe.drape / pe.bunting / pe.rolled_carpet / pe.pulley ...
    ml.export(root, NAME, atlas, decor=decor, icon=..., light=13)

Coordinates: tent-local blocks, y up (0 = top of the ground block), +z = the open front, the anchor block's centre
at (0, 0, 0). Small things go under the bone "detail" (hidden beyond the decor distance). Cloth is soft: lofts that
sag, folds, curved hems, dags and fringes cut out of the textures.
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
box, collide = ml.box, ml.collide
_rgb, _jitter, _scale, _mix = ml._rgb, ml._jitter, ml._scale, ml._mix


# ================================================================ painters (PIL RGBA images of the region's size)
def weave(img, c, rng, stains=1):
    w, h = img.size
    ml._weave(img, (0, 0, w, h), c, rng, stains=stains)


def _put(px, w, h, x, y, c, a=255):
    if 0 <= x < w and 0 <= y < h:
        px[x, y] = tuple(int(k) for k in c[:3]) + (a,)


def glyph(px, w, h, cx, cy, kind, col, rng, s=1):
    """A small gold motif centred at (cx, cy): cross, diamond, dot, star, fleur (tiny), arrow."""
    pts = {
        "cross": ((0, -1), (0, 0), (0, 1), (-1, 0), (1, 0)),
        "diamond": ((0, -2), (-1, -1), (1, -1), (-2, 0), (2, 0), (-1, 1), (1, 1), (0, 2)),
        "dot": ((0, 0), (1, 0), (0, 1), (1, 1)),
        "star": ((0, -2), (0, -1), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (0, 1), (-1, 1), (1, 1), (-1, 2), (1, 2)),
        "fleur": ((0, -3), (0, -2), (-1, -2), (1, -2), (0, -1), (-2, -1), (2, -1), (-2, 0), (2, 0), (-1, 0), (0, 0), (1, 0),
                  (0, 1), (-1, 2), (1, 2)),
        "arrow": ((0, -2), (-1, -1), (0, -1), (1, -1), (0, 0), (0, 1)),
    }[kind]
    for dx, dy in pts:
        for i in range(s):
            for j in range(s):
                _put(px, w, h, cx + dx * s + i, cy + dy * s + j, _jitter(col, rng, 10))


def stripes(cols, n, seed, motif=None, motif_col=None, motif_step=(10, 12), fold=0.12, seams=True, hem=None, shade=(0.88, 0.14)):
    """n vertical stripes (cols in turn), soft folds inside each stripe, dark seams, motifs (glyph kind) in a grid on
    the stripes of cols[0]; hem = (colour, px) a band at the bottom. Returns a painter."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        edges = [int(round(k * w / n)) for k in range(n + 1)]
        for k in range(n):
            ml._weave(img, (edges[k], 0, edges[k + 1] - edges[k], h), cols[k % len(cols)], rng, stains=1)
        px = img.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                k = shade[0] + shade[1] * (y / h)
                k_ = (x - edges[min(n - 1, int(x * n / w))]) / max(1.0, w / n)
                k *= 1.0 - fold * 0.5 + fold * math.sin(math.pi * k_)
                if seams and (x in edges or x + 1 in edges):
                    k *= 0.76
                px[x, y] = _scale((r, g, b), k) + (255,)
        if motif:
            mc = motif_col or GOLD
            sx, sy = motif_step
            for k in range(0, n, len(cols)):
                x0, x1 = edges[k], edges[k + 1]
                for row, y in enumerate(range(sy // 2 + 2, h - 4, sy)):
                    off = (sx // 2) if row % 2 else 0
                    for x in range(x0 + 3 + off, x1 - 3, sx):
                        glyph(px, w, h, x, y, motif, mc, rng)
        if hem:
            c, hh = hem
            for y in range(h - hh, h):
                for x in range(w):
                    px[x, y] = _jitter(c if y > h - hh else _scale(c, 0.7), rng, 8) + (255,)
    return paint


def fringe_rows(px, w, h, y0, gold, rng, cut=True, tassel=3):
    """A gold fringe from row y0 to the bottom: hanging threads in groups (gaps cut out), darker tips."""
    for x in range(w):
        gap = (x % tassel) == tassel - 1
        ln = h - y0 - (1 if (x // tassel) % 2 else 0)
        for y in range(y0, h):
            if (gap and y > y0 + 1) or (y - y0) > ln:
                if cut:
                    px[x, y] = (0, 0, 0, 0)
                continue
            k = 1.08 - 0.3 * ((y - y0) / max(1, h - y0)) - (0.12 if x % tassel == 0 else 0.0)
            px[x, y] = _jitter(_scale(gold, k), rng, 10) + (255,)


def fleur(img, box_, col, dark, scale=4):
    """A fleur-de-lis in box_ (x, y, w, h) of img: central lancet petal, two curled side petals, the band, the stem
    and two small lower lobes; a dark outline round it."""
    from PIL import Image, ImageDraw, ImageFilter
    x0, y0, w, h = box_
    S = scale
    W_, H_ = w * S, h * S

    def P(pts):
        return [(W_ * x, H_ * y) for x, y in pts]
    centre = [(0.5, 0.0), (0.58, 0.08), (0.64, 0.22), (0.64, 0.36), (0.58, 0.49), (0.5, 0.56), (0.42, 0.49), (0.36, 0.36),
              (0.36, 0.22), (0.42, 0.08)]
    left = [(0.43, 0.6), (0.36, 0.5), (0.28, 0.38), (0.19, 0.28), (0.09, 0.27), (0.02, 0.33), (0.01, 0.42), (0.06, 0.49),
            (0.13, 0.49), (0.15, 0.43), (0.11, 0.39), (0.13, 0.35), (0.2, 0.37), (0.27, 0.46), (0.33, 0.58), (0.36, 0.62)]
    lobe = [(0.45, 0.66), (0.36, 0.71), (0.28, 0.79), (0.27, 0.88), (0.33, 0.9), (0.36, 0.83), (0.41, 0.77), (0.47, 0.72)]
    stem = [(0.44, 0.64), (0.56, 0.64), (0.53, 0.8), (0.5, 0.98), (0.47, 0.8)]
    mask = Image.new("L", (W_, H_), 0)
    d = ImageDraw.Draw(mask)
    for poly in (centre, left, [(1 - x, y) for x, y in left], lobe, [(1 - x, y) for x, y in lobe], stem):
        d.polygon(P(poly), fill=255)
    d.rectangle((W_ * 0.29, H_ * 0.56, W_ * 0.71, H_ * 0.66), fill=255)
    outline = mask.filter(ImageFilter.MaxFilter(2 * S + 1))
    im = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    im.paste(Image.new("RGBA", (W_, H_), tuple(dark) + (255,)), (0, 0), outline)
    im.paste(Image.new("RGBA", (W_, H_), tuple(col) + (255,)), (0, 0), mask)
    # a light streak on the central petal and the band
    hl = Image.new("L", (W_, H_), 0)
    dh = ImageDraw.Draw(hl)
    dh.polygon(P([(0.47, 0.1), (0.5, 0.06), (0.5, 0.48), (0.46, 0.42)]), fill=255)
    dh.rectangle((W_ * 0.32, H_ * 0.57, W_ * 0.68, H_ * 0.59), fill=255)
    im.paste(Image.new("RGBA", (W_, H_), tuple(_scale(col, 1.18)) + (255,)), (0, 0), hl)
    im = im.resize((w, h), Image.LANCZOS)
    # re-binarise the alpha (cut-out) and keep the colours crisp
    px = im.load()
    for yy in range(h):
        for xx in range(w):
            r, g, b, a = px[xx, yy]
            px[xx, yy] = (r, g, b, 255 if a > 110 else 0) if a > 110 else (0, 0, 0, 0)
    img.alpha_composite(im, (x0, y0))


def diamond_motif(px, w, h, cx, cy, r, col, dark, rng):
    """The draped panels' gold motif: a stepped diamond outline, a dot inside, a little arrow above."""
    for y in range(-r, r + 1):
        for x in range(-r, r + 1):
            dd = abs(x) + abs(y)
            if dd in (r, r - 1):
                _put(px, w, h, cx + x, cy + y, _jitter(col, rng, 8))
            elif dd == r + 1:
                _put(px, w, h, cx + x, cy + y, dark)
    for y in range(-1, 2):
        for x in range(-1, 2):
            _put(px, w, h, cx + x, cy + y, _jitter(col, rng, 8))
    for k in range(3):
        _put(px, w, h, cx, cy - r - 3 - k, _jitter(col, rng, 8))
    _put(px, w, h, cx - 1, cy - r - 4, _jitter(col, rng, 8))
    _put(px, w, h, cx + 1, cy - r - 4, _jitter(col, rng, 8))


def panel(field, seed, border=None, fringe=6, motif="diamond", point=0.0, gold=None, dark=None, key=False, dags=0, motif_col=None,
          weave_stains=1, fold=0.1):
    """A hanging cloth panel / banner (cut-out): field colour, a gold border, optional gold fringe of `fringe` px at
    the bottom, a V point (point = fraction of the height taken by the point), a stepped 'key' border instead of the
    plain one, dags (square tabs at the bottom), and a motif in the middle: diamond, fleur, None."""
    gold = gold or GOLD
    dark = dark or _scale(field, 0.55)

    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, field, rng, stains=weave_stains)
        px = img.load()
        body = h - fringe if fringe else h
        pb = int(body * (1 - point)) if point else body
        tab = max(4, w // max(1, dags)) if dags else 0
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                px[x, y] = _scale((r, g, b), 1.0 - fold * 0.5 + fold * math.sin(math.pi * ((x * 3.0 / w) % 1.0))) + (255,)
        for y in range(h):
            for x in range(w):
                if y >= body:
                    continue
                e = min(x, w - 1 - x, y)
                if point and y >= pb:
                    half = (w / 2) * (1 - (y - pb) / max(1, body - pb))
                    dx = abs(x - (w - 1) / 2)
                    if dx > half + 0.5:
                        px[x, y] = (0, 0, 0, 0)
                        continue
                    e = min(e, int(half - dx))
                if dags and y >= body - 4:
                    lx = x % tab
                    if lx >= tab * 0.62 and y >= body - 4:
                        px[x, y] = (0, 0, 0, 0)
                        continue
                    e = min(e, int(min(lx, tab * 0.62 - 1 - lx)), body - 1 - y)
                elif not point:
                    e = min(e, body - 1 - y)
                bw = 3 if w > 24 else 2
                if e < bw:
                    px[x, y] = _jitter(gold if e > 0 else _scale(gold, 0.72), rng, 9) + (255,)
                elif e == bw:
                    px[x, y] = _jitter(dark, rng, 5) + (255,)
                elif key and e < bw + 4 and ((x // 3 + y // 3) % 3 == 0):
                    px[x, y] = _jitter(_scale(gold, 0.92), rng, 8) + (255,)
        if fringe:
            if point:
                # the fringe follows the V point's lower edges
                for x in range(w):
                    half_t = 1 - abs(x - (w - 1) / 2) / (w / 2)
                    yb = int(pb + (body - pb) * half_t)
                    for y in range(yb, min(h, yb + fringe)):
                        if x % 3 == 2 and y > yb + 1:
                            px[x, y] = (0, 0, 0, 0)
                        else:
                            px[x, y] = _jitter(_scale(gold, 1.05 - 0.3 * (y - yb) / fringe), rng, 10) + (255,)
                    for y in range(yb + fringe, h):
                        px[x, y] = (0, 0, 0, 0)
            else:
                fringe_rows(px, w, h, body, gold, rng)
        mc = motif_col or gold
        if motif == "diamond":
            diamond_motif(px, w, h, w // 2, int(pb * 0.58), max(3, w // 8), mc, dark, rng)
        elif motif == "fleur":
            s = int(w * 0.62)
            fleur(img, ((w - s) // 2, int(pb * 0.5 - s * 0.55), s, int(s * 1.1)), mc, _scale(field, 0.5))
        elif motif == "fleur_top":
            s = int(w * 0.6)
            fleur(img, ((w - s) // 2, int(pb * 0.14), s, int(s * 1.1)), mc, _scale(field, 0.5))
    return paint


def iron_band(seed):
    """Grey riveted iron bands of the posts: hammered iron, lighter top edge, big square rivets."""
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


def wood(base, dark, seed, plank=None, vertical=False):
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        ml.fine_wood(img, (0, 0, w, h), _rgb(base), _rgb(dark), plank or h, rng, joints=False, knots=0.08, grain=0.14, shade=0.08,
                     vertical=vertical)
    return paint


def burlap(base, seed):
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


def bunch(kind, seed):
    """A hanging bunch, cut-out: grapes (purple berries), lavender (violet spikes), garlic (white bulbs on a braid),
    peppers (red chilis), herbs (green sprigs), herbs_flower (green with pink flowers), wheat."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                px[x, y] = (0, 0, 0, 0)
        for y in range(0, 4):
            _put(px, w, h, w // 2, y, (170, 140, 90))
        cx = w / 2
        if kind == "grapes":
            for y in range(4, h - 1):
                t = (y - 4) / (h - 5)
                half = (w * 0.42) * (1 - t) ** 0.7 + 1
                for x in range(w):
                    dx = x - cx + 0.5
                    if abs(dx) <= half:
                        berry = ((x // 2) + (y // 2)) % 2
                        k = 1.15 - 0.35 * (abs(dx) / half) - (0.2 if berry else 0.0)
                        _put(px, w, h, x, y, _jitter(_scale(_rgb("6a2a8a"), k), rng, 10))
            for y in range(3, 7):   # leaves on top
                for x in range(int(cx - 4), int(cx + 4)):
                    if rng.random() < 0.7:
                        _put(px, w, h, x, y, _jitter(_rgb("4a7a2a"), rng, 10))
        elif kind == "garlic":
            for y in range(3, h):
                _put(px, w, h, int(cx), y, (200, 180, 130))
            for k in range(5):
                by = 6 + k * (h - 10) // 5
                bx = cx + (3 if k % 2 else -3)
                for y in range(by - 3, by + 4):
                    for x in range(int(bx - 4), int(bx + 4)):
                        d = math.hypot((x - bx) / 3.6, (y - by) / 3.2)
                        if d < 1:
                            _put(px, w, h, x, y, _jitter(_scale(_rgb("ece6d6"), 1.1 - 0.35 * d - (0.1 if (x - bx) > 1 else 0)), rng, 6))
                _put(px, w, h, int(bx), by - 4, (180, 160, 110))
        elif kind == "peppers":
            for y in range(3, h - 2):
                _put(px, w, h, int(cx), y, (90, 110, 50))
            for k in range(16):
                t = k / 15
                by = int(5 + t * (h - 12))
                bx = cx + rng.uniform(-w * 0.32, w * 0.32) * (0.6 + 0.4 * (1 - t))
                ang = rng.uniform(-0.5, 0.5)
                for i in range(7):
                    x = int(bx + math.sin(ang) * i)
                    y = by + i
                    for dx in (0, 1):
                        _put(px, w, h, x + dx, y, _jitter(_rgb("c8281a") if i < 6 else _rgb("8a1a10"), rng, 12))
                _put(px, w, h, int(bx), by - 1, (70, 110, 40))
        else:
            cols = {"lavender": [_rgb("7a4ab8"), _rgb("9a6ad0"), _rgb("5a3a90")],
                    "herbs": [_rgb("4e8a2e"), _rgb("6aa83a"), _rgb("3a6a22")],
                    "herbs_flower": [_rgb("4e8a2e"), _rgb("6aa83a"), _rgb("d860a8")],
                    "wheat": [_rgb("d8b050"), _rgb("e8c868"), _rgb("b89038")]}[kind]
            stem = (110, 84, 50) if kind != "lavender" else (70, 100, 50)
            for k in range(9):
                x0 = cx + rng.uniform(-2, 2)
                x1 = cx + rng.uniform(-w * 0.44, w * 0.44)
                for i in range(h - 4):
                    t = i / (h - 5)
                    x = int(round(x0 + (x1 - x0) * t))
                    y = 3 + i
                    _put(px, w, h, x, y, stem)
                    if (kind == "lavender" and t > 0.35) or (kind != "lavender" and i > 4 and rng.random() < 0.6):
                        for dx in (-1, 0, 1):
                            if rng.random() < 0.75:
                                _put(px, w, h, x + dx, y, _jitter(rng.choice(cols), rng, 10))
            for y in range(4, 8):   # the tie
                for x in range(int(cx - 2), int(cx + 3)):
                    _put(px, w, h, x, y, (190, 160, 100))
    return paint


def flowers(petals, seed, leaf=None):
    """A plant with flowers, cut-out (crossed planes in a pot or a box): green leaves, round flower heads."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                px[x, y] = (0, 0, 0, 0)
        greens = [_rgb(leaf or "3e7a2a"), _rgb("5a9a36"), _rgb("2e5a1e")]
        for k in range(10):
            x0 = w / 2 + rng.uniform(-w * 0.25, w * 0.25)
            x1 = rng.uniform(2, w - 3)
            top = rng.uniform(h * 0.1, h * 0.5)
            for y in range(int(top), h):
                t = (y - top) / max(1, h - top)
                x = int(x1 + (x0 - x1) * t)
                _put(px, w, h, x, y, _jitter(greens[2], rng, 8))
                if rng.random() < 0.35:
                    for dx in (-2, -1, 1, 2):
                        _put(px, w, h, x + dx, y + (1 if abs(dx) == 2 else 0), _jitter(rng.choice(greens), rng, 10))
            c = rng.choice(petals)
            fx, fy = x1, int(top)
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    if abs(dx) + abs(dy) <= 3:
                        k = 1.15 - 0.12 * (abs(dx) + abs(dy))
                        _put(px, w, h, int(fx + dx), fy + dy, _jitter(_scale(c, k), rng, 8))
            _put(px, w, h, int(fx), fy, (240, 200, 60))
    return paint


def heap(cols, seed, bg="5a3a20", r=3):
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        ml._heap(img, (0, 0, w, h), [_rgb(c) for c in cols], rng, bg=_rgb(bg), r=r)
    return paint


def cheese(seed):
    """Cheese: a creamy yellow paste with small holes, a darker orange rind band at the top and bottom."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _rgb("f0c040")
                if y < 2 or y >= h - 2:
                    c = _rgb("d89a28")
                px[x, y] = _jitter(c, rng, 8) + (255,)
        for _ in range(w * h // 60):
            x, y = rng.randrange(1, w - 1), rng.randrange(3, h - 3)
            px[x, y] = _jitter(_rgb("c8962a"), rng, 6) + (255,)
    return paint


def carpet_roll(field, accent, seed, cream=False):
    """A rolled carpet's outside: the field colour, gold / accent bands and lozenges along its length (v = along)."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, _rgb(field), rng, stains=0)
        px = img.load()
        ac = _rgb(accent)
        for y in range(h):
            for x in range(w):
                ly = y % 12
                if ly in (0, 1):
                    px[x, y] = _jitter(ac, rng, 8) + (255,)
                elif 4 <= ly <= 8 and abs((x % 8) - 4) + abs(ly - 6) <= 2:
                    px[x, y] = _jitter(_mix(ac, _rgb(field), 0.35), rng, 8) + (255,)
                if x % 8 == 0 and not cream:
                    r, g, b, a = px[x, y]
                    px[x, y] = _scale((r, g, b), 0.82) + (255,)
    return paint


def rug(field, border, gold, accent, seed, medallion=True, key=True):
    """An ornate rug: dark outer border with a gold key pattern, an accent band, the field with a stepped diamond
    medallion (gold, accent and dark rings), corner triangles and small motifs. Reads from the front (top = -z)."""
    def paint(img):
        rng = random.Random(seed)
        f, b, g, a = _rgb(field), _rgb(border), _rgb(gold), _rgb(accent)
        w, h = img.size
        weave(img, f, rng, stains=1)
        px = img.load()
        cx, cy = (w - 1) / 2, (h - 1) / 2
        for y in range(h):
            for x in range(w):
                e = min(x, y, w - 1 - x, h - 1 - y)
                c = None
                if e < 2:
                    c = _scale(b, 0.8)
                elif e < 9:
                    c = b
                    if key:
                        lx, ly = (x if min(y, h - 1 - y) <= min(x, w - 1 - x) else y) % 6, e - 2
                        if ly in (1, 5) or (lx == 0 and 1 <= ly <= 5) or (lx == 3 and ly in (2, 3, 4)) or (ly == 3 and lx <= 3):
                            c = g
                elif e < 11:
                    c = g
                elif e < 15:
                    c = a if (x + y) % 4 < 2 else _scale(a, 0.8)
                elif e == 15:
                    c = g
                if c is None and medallion:
                    dd = abs(x - cx) / (w * 0.5) + abs(y - cy) / (h * 0.5)
                    ring = int(dd * 14)
                    if dd < 0.62:
                        c = (g, a, f, b, g, a, _scale(f, 0.85), g, b)[min(8, ring)]
                        if ring == 2 and (x + y) % 3 == 0:
                            c = g
                    else:
                        # corner triangles
                        cdx, cdy = min(x - 15, w - 16 - x), min(y - 15, h - 16 - y)
                        if cdx + cdy < 12:
                            c = a if cdx + cdy < 9 else g
                        elif (x % 10 == 5 and y % 10 == 5):
                            c = g
                if c is not None:
                    px[x, y] = _jitter(c, rng, 7) + (255,)
    return paint


def framed_sign(field, seed, motif="fleur"):
    """A small wall hanging framed in dark wood: the field, a gold inner line, a gold fleur in the middle."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        weave(img, _rgb(field), rng, stains=0)
        px = img.load()
        for y in range(h):
            for x in range(w):
                e = min(x, y, w - 1 - x, h - 1 - y)
                if e < 3:
                    px[x, y] = _jitter(_rgb("4a2e14") if e else _rgb("2a1a0a"), rng, 5) + (255,)
                elif e == 5:
                    px[x, y] = _jitter(GOLD, rng, 8) + (255,)
        s = int(w * 0.56)
        fleur(img, ((w - s) // 2, (h - int(s * 1.1)) // 2, s, int(s * 1.1)), GOLD, _scale(_rgb(field), 0.5))
    return paint


GOLD, GOLD_DARK = _rgb("e8a830"), _rgb("8a5a14")


# ================================================================ geometry
def band(bone, name, x, z, half, y, h, region="e_band"):
    """An iron band round a squared post (centre x, z)."""
    box(bone, name, (x - half, y, z - half), (x + half, y + h, z + half), {"all": region, "+2": "iron", "-2": "iron"}, stretch=True)


def post(shell, det, name, x, z, top, d=0.42, bands=(0.35, 1.6, 2.8), caps=2, cap_w=0.62, foot=0.0, region="e_post",
         solid_to=None, collide_half=None, cap_region="wood"):
    """A big squared post (region e_post: grain along u) from the ground (or a foot block of height `foot`) to `top`,
    iron bands at the `bands` heights, `caps` stacked cap blocks (the lower one widest) on top. Collides from the ground
    to solid_to (default: top)."""
    if foot:
        fh = d / 2 + 0.08
        box(shell, name + "_foot", (x - fh, 0.0, z - fh), (x + fh, foot, z + fh), {"all": "wood_dark", "+2": "end_grain"})
    beam(shell, name, (x, foot, z), (x, top, z), d, {"all": region, "+1": "end_grain", "-1": "end_grain"})
    for k, y in enumerate(bands):
        band(det, "%s_band_%d" % (name, k), x, z, d / 2 + 0.025, y, 0.16)
    y = top
    for k in range(caps):
        cw = cap_w - 0.16 * k
        ch = 0.34 if k == 0 else 0.28
        box(shell, "%s_cap_%d" % (name, k), (x - cw / 2, y, z - cw / 2), (x + cw / 2, y + ch, z + cw / 2), {"all": cap_region, "+2": "end_grain"})
        y += ch
    h = collide_half or (max(d, 0.3) / 2 + 0.02)
    collide((x - h, 0.0, z - h, x + h, solid_to if solid_to is not None else top, z + h))
    return y


def rope_wrap(bone, name, x, z, y, half, turns=2, th=0.09):
    """Rope coiled round a squared post: `turns` rings of thick rope from y upwards."""
    for k in range(turns):
        yy = y + k * (th + 0.01)
        box(bone, "%s_%d" % (name, k), (x - half - th / 2, yy, z - half - th / 2), (x + half + th / 2, yy + th, z + half + th / 2), "rope")


def pyramid_roof(bone, name, eave, top, region, sag=0.25, nx=3, ny=4, regions=None, th=0.035, hang=None, top_regions=None):
    """A four-sided canvas roof: eave = the 4 lower corners (FL, FR, BR, BL), top = the 4 upper corners (a point:
    4 times the same point). Each face sags between the hips (the cloth bellies down in the middle of the face, the
    hips stay straight: faces meet cleanly). regions = the region of each face (front, right, back, left) or one
    region; the texture's v runs from the top down to the eave. hang = (h, regions) a vertical hanging edge of h below
    each eave edge. Returns the faces' point functions."""
    eave = [v3(*p) for p in eave]
    top = [v3(*p) for p in top]
    regs = regions or [region] * 4
    funcs = []
    order = [(0, 1), (1, 2), (2, 3), (3, 0)]   # front (FL -> FR), right, back, left: s increases to the viewer's right
    for k, (i, j) in enumerate(order):
        # seen from outside, the viewer's right of the front face is +x: FL -> FR; of the right face is -z: FR -> BR, etc.
        a0, a1, b0, b1 = top[i], top[j], eave[i], eave[j]
        nrm = norm(np.cross(a1 - a0, b0 - a0) if np.linalg.norm(a1 - a0) > 1e-6 else np.cross(b1 - b0, b0 - a0))
        out = norm(((b0 + b1) / 2 - (a0 + a1) / 2) * v3(1, 0, 1))
        inward = -norm(nrm) if np.dot(nrm, UP) > 0 else norm(nrm)
        if np.dot(-inward, UP) < 0:
            inward = -inward

        def P(s, t, a0=a0, a1=a1, b0=b0, b1=b1, inward=inward, out=out):
            p = (a0 + (a1 - a0) * s) * (1 - t) + (b0 + (b1 - b0) * s) * t
            p = p + inward * (sag * math.sin(math.pi * t) * math.sin(math.pi * s))
            p = p + out * (0.03 * t * t * math.sin(s * math.pi * 4))
            return p
        loft(bone, "%s_%d" % (name, k), P, nx, ny, regs[k], th=th, overlap=0.02)
        funcs.append(P)
        if hang:
            hh, hregs = hang
            hr = hregs[k] if isinstance(hregs, (list, tuple)) else hregs

            def H(s, t, b0=b0, b1=b1, out=out):
                p = b0 + (b1 - b0) * s
                return p - UP * (hh * t) + out * (0.04 * math.sin(math.pi * t) + 0.03 * math.sin(s * math.pi * 5) * t)
            loft(bone, "%s_hang_%d" % (name, k), H, max(1, nx), 1, hr, th=0.025, overlap=0.02)
    return funcs


def swag(bone, name, a, b, drop, depth, out, region, nx=4, th=0.03, belly=0.08):
    """A draped valance between two points a and b (its top edge, on a beam): the cloth hangs `depth` at the ends and
    `depth + drop` in the middle (a curved hem), bellying out by `belly` towards `out`; the region's v runs down (its
    fringe / dags at the bottom)."""
    a, b, out = v3(*a), v3(*b), norm(v3(*out))

    def P(s, t):
        top = a + (b - a) * s
        d = depth + drop * math.sin(math.pi * s)
        p = top - UP * (d * t) + out * (belly * math.sin(math.pi * s) * math.sin(math.pi * t * 0.9) + 0.02 * t)
        return p
    loft(bone, name, P, nx, 2, region, th=th, overlap=0.015)
    return P


def hang_panel(bone, name, top_center, w, h, normal, region, wave=0.04, ny=3):
    """A flat hanging panel / banner (both faces, cut-out), its top edge centred on top_center, facing `normal`."""
    top = v3(*top_center)
    n = norm(v3(*normal))
    side = norm(np.cross(UP, n))

    def P(s, t):
        return top + side * ((s - 0.5) * w) - UP * (h * t) + n * (wave * math.sin(math.pi * t) * (0.6 + 0.4 * math.sin(math.pi * s)))
    loft(bone, name, P, 1, ny, region, th=0.02, u_hint=side, v_hint=-UP)


def drape(bone, det, name, top_a, top_b, tie, bot_a, bot_b, normal, region, nx=3, tie_region="e_gold_band", tie_size=(0.3, 0.12, 0.2)):
    """A curtain tied back: hangs from the edge top_a - top_b, gathered at `tie` (a band), flaring again below to
    bot_a - bot_b; soft folds (ripples along `normal`)."""
    top_a, top_b, tie, bot_a, bot_b, n = (v3(*p) for p in (top_a, top_b, tie, bot_a, bot_b, normal))
    side = norm(top_b - top_a)

    def U(s, t):
        tt = t ** 0.85
        a = top_a + (top_b - top_a) * s
        b = tie + side * ((s - 0.5) * 0.18)
        return a * (1 - tt) + b * tt + n * (0.08 * math.sin(s * math.pi * 3) * (1 - t) + 0.05 * math.sin(math.pi * t))

    def Lw(s, t):
        a = tie + side * ((s - 0.5) * 0.18)
        b = bot_a + (bot_b - bot_a) * s
        return a * (1 - t) + b * t + n * (0.06 * math.sin(s * math.pi * 3 + 0.5) * t)
    yt = (top_a[1] - tie[1])
    yb = (tie[1] - bot_a[1])
    tf = yt / max(1e-3, yt + yb)

    def U2(s, t):   # the texture runs over the whole curtain: upper part takes [0, tf] of v
        return U(s, t)
    loft(bone, name + "_up", U2, nx, 3, region, th=0.03)
    loft(bone, name + "_lo", Lw, nx, 1, region, th=0.03)
    add_cube(det, name + "_tie", tie, np.column_stack([side, UP, np.cross(side, UP)]), tie_size, tie_region)


def wall(bone, name, a, b, y0, y1, out, region, nx=6, fold=0.05):
    """A hanging cloth wall from a (left) to b, y0..y1, soft vertical folds towards `out`."""
    a, b, out = v3(*a), v3(*b), v3(*out)

    def P(s, t):
        p = a + (b - a) * s
        return v3(p[0], y1 - (y1 - y0) * t, p[2]) + out * (fold * math.sin(s * math.pi * nx) * (0.4 + 0.6 * t))
    loft(bone, name, P, nx, 2, region, th=0.03)


def bunting(bone, name, a, b, sag, regions, n=6, size=(0.28, 0.42), rope_d=0.05):
    """A rope from a to b sagging by `sag`, with n pennants (regions in turn, cut-out, V-pointed) hanging from it."""
    a, b = v3(*a), v3(*b)
    ml.rope(bone, name + "_rope", a, b, d=rope_d, sag=sag, segs=4)
    d = norm((b - a) * v3(1, 0, 1))
    n_ = np.cross(d, UP)
    for k in range(n):
        t = (k + 0.5) / n
        p = a + (b - a) * t - UP * (4 * sag * t * (1 - t)) - UP * 0.02
        ml.plate(bone, "%s_%d" % (name, k), p - UP * size[1] / 2, size[0], size[1], regions[k % len(regions)], normal=n_, th=0.01)


def rolled_carpet(bone, name, foot, r, h, region, lean=(0.0, 0.0), end="e_carpet_end"):
    """A rolled carpet standing on its end at foot, leaning by lean = (dx, dz) at the top: an octagonal roll."""
    foot = v3(*foot)
    topp = foot + v3(lean[0], h, lean[1])
    d = norm(topp - foot)
    L = np.linalg.norm(topp - foot)
    side = norm(np.cross(d, Z)) if abs(d[2]) < 0.9 else X
    f = np.cross(side, d)
    for k, a in enumerate((0.0, math.pi / 4)):
        R = np.column_stack([side, d, f]) @ ry(a)
        add_cube(bone, "%s_%d" % (name, k), (foot + topp) / 2, R, (2 * r * 0.83, L, 2 * r * 0.83), {"all": region, "+2": end, "-2": end},
                 stretch=True)


def bolt(bone, name, c, length=0.45, r=0.08, yaw=0.0, region="cloth_red", end="white", pitch=0.0):
    """A rolled cloth bolt / scroll lying on its side (two boxes turned 45 degrees about its axis), along yaw."""
    c = v3(*c)
    for k, a in enumerate((0.0, math.pi / 4)):
        add_cube(bone, "%s_%d" % (name, k), c, ry(yaw) @ rz(pitch) @ rx(a), (length, 2 * r * 0.83, 2 * r * 0.83), {"all": region, "+1": end, "-1": end},
                 stretch=True)


def folded_stack(bone, name, foot, w, d, regions, h=0.07, yaw=0.0):
    """A stack of folded cloth (or books): one flat box per region, slightly offset."""
    foot = v3(*foot)
    y = 0.0
    for k, reg in enumerate(regions):
        off = 0.02 * ((k * 7) % 3 - 1)
        ml.rbox(bone, "%s_%d" % (name, k), foot + v3(off, y, -off), (w, h, d), yaw + 0.04 * ((k * 5) % 3 - 1), {"all": reg, "+2": reg},
                stretch=True)
        y += h
    return y


def cheese_wheel(bone, name, foot, r=0.18, h=0.12, region="e_cheese", top="e_cheese_top"):
    ml.octo(bone, name, foot, r, h, {"all": region, "+2": top, "-2": top})


def cheese_block(bone, name, foot, s=(0.26, 0.2, 0.22), yaw=0.0, region="e_cheese"):
    ml.rbox(bone, name, foot, s, yaw, {"all": region, "+2": "e_cheese_top"}, stretch=True)


def plant(bone, name, foot, w, h, region, pot="basket", pot_r=0.16, pot_h=0.18):
    """A pot / basket (octagonal) of flowers or herbs: crossed cut-out planes above it."""
    foot = v3(*foot)
    if pot:
        ml.octo(bone, name + "_pot", foot, pot_r, pot_h, {"all": pot, "+2": "e_soil", "-2": pot})
    ml.crossed(bone, name + "_leaves", foot + UP * (pot_h + h / 2 - 0.04), w, h, region)
    ml.crossed(bone, name + "_leaves2", foot + UP * (pot_h + h / 2 - 0.06), w * 0.8, h * 0.9, region, yaw=math.pi / 8)


def pulley(bone, name, p, axis=(1, 0, 0), s=0.22, hook=True):
    """A rope pulley block: a wooden shell with an iron strap, the sheave (wheel) inside, a hook below."""
    p = v3(*p)
    a = norm(v3(*axis))
    side = norm(np.cross(UP, a)) if abs(a[1]) < 0.9 else X
    R = np.column_stack([a, UP, np.cross(a, UP)])
    add_cube(bone, name + "_shell", p, R, (s * 0.55, s * 1.2, s * 0.9), {"all": "wood", "+2": "end_grain", "-2": "end_grain"}, stretch=True)
    add_cube(bone, name + "_strap", p, R, (s * 0.6, s * 1.32, s * 0.2), "iron", stretch=True)
    for k, ang in enumerate((0.0, math.pi / 4)):
        add_cube(bone, "%s_wheel_%d" % (name, k), p + UP * s * 0.05, R @ rx(ang), (s * 0.62, s * 0.7, s * 0.7), {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"},
                 stretch=True)
    add_cube(bone, name + "_eye", p + UP * s * 0.75, R, (s * 0.2, s * 0.3, s * 0.12), "iron")
    if hook:
        add_cube(bone, name + "_hook", p - UP * s * 0.78, R, (s * 0.12, s * 0.36, s * 0.12), "iron")
        add_cube(bone, name + "_hook_b", p - UP * s * 0.96 + side * 0.0 + R[:, 2] * s * 0.08, R, (s * 0.12, s * 0.1, s * 0.26), "iron")


def tassel(bone, name, p, h=0.32, w=0.12, region="e_tassel"):
    """A gold tassel hanging from p: a knob, the cord, the flared skirt (crossed planes)."""
    p = v3(*p)
    add_cube(bone, name + "_knob", p - UP * 0.04, EYE, (0.08, 0.08, 0.08), "gold")
    ml.crossed(bone, name, p - UP * (0.08 + h / 2), w, h, region)


def lamp(shell, det, name, p, size=0.34, chain_to=None, metal="iron"):
    return ml.lantern(shell, name, p, size=size, metal=metal, chain_to=chain_to)


def bench_table(shell, det, name, x0, x1, z0, z1, h=0.95, top_region="plank", solid=True):
    """A plain wooden table / stand: plank top, four dark legs, a low shelf."""
    box(shell, name + "_top", (x0, h - 0.08, z0), (x1, h, z1), {"all": top_region}, u_dir=X)
    for k, (x, z) in enumerate(((x0 + 0.08, z0 + 0.08), (x1 - 0.08, z0 + 0.08), (x0 + 0.08, z1 - 0.08), (x1 - 0.08, z1 - 0.08))):
        box(det if k else shell, "%s_leg_%d" % (name, k), (x - 0.06, 0.0, z - 0.06), (x + 0.06, h - 0.08, z + 0.06), "wood_dark")
    box(shell, name + "_shelf", (x0 + 0.06, 0.18, z0 + 0.06), (x1 - 0.06, 0.24, z1 - 0.06), "plank_dark", u_dir=X)
    if solid:
        collide((x0, 0.0, z0, x1, h, z1))
    return h


def potions_row(det, name, x0, x1, y, z, cols, n=None, glow=False, rng=None, big=False):
    """A row of potion bottles on a shelf board from x0 to x1 at height y."""
    rng = rng or random.Random(len(name))
    n = n or max(2, int((x1 - x0) / 0.22))
    for i in range(n):
        xx = x0 + (x1 - x0) * (i + 0.5) / n
        c = cols[i % len(cols)]
        shp = ("round", "tall", "round", "flask")[(i + len(name)) % 4]
        ml.bottle(det, "%s_%d" % (name, i), (xx, y, z + 0.04 * ((i % 2) - 0.5)), c, r=(0.085 if big else 0.07) + 0.01 * (i % 3 == 0),
                  h=(0.24 if big else 0.18) + 0.04 * (i % 2), shape=shp, neck_h=0.06, glow=glow)


def free_box(x0, z0, h=2.2, w=1.0):
    """Asserts nothing: returns the NPC spot box (x0, 0, z0, x0 + w, h, z0 + w) for the tests and the docs."""
    return (x0, 0.0, z0, x0 + w, h, z0 + w)


def check_free(name, spot, extra=()):
    """Prints and raises when a collision box overlaps the NPC spot (x0, y0, z0, x1, y1, z1)."""
    x0, y0, z0, x1, y1, z1 = spot
    bad = [b for b in list(ml.COLLIDERS) + list(extra) if b[0] < x1 and b[3] > x0 and b[2] < z1 and b[5] > z0 and b[1] < y1 and b[4] > y0]
    if bad:
        raise AssertionError("%s: the NPC spot %s is blocked by %s" % (name, spot, bad))


def roof_point(P, coord, t, axis=0, lo=0.0, hi=1.0):
    """The point of a roof face P(s, t) at parameter t whose `axis` coordinate is `coord` (bisection on s; the
    coordinate must vary monotonically along s)."""
    a, b = lo, hi
    inc = P(b, t)[axis] > P(a, t)[axis]
    for _ in range(40):
        m = (a + b) / 2
        if (P(m, t)[axis] < coord) == inc:
            a = m
        else:
            b = m
    return P((a + b) / 2, t)


def drape_over(bone, name, top, edge, w, h, normal, region, wave=0.05, ny=4):
    """A panel draped over a roof edge: it lies on the roof from `top` down to the `edge` (the first row of the loft,
    the top 1/ny of the texture), then hangs `h` straight down, facing `normal` (both faces, cut-out)."""
    top, edge, n = v3(*top), v3(*edge), norm(v3(*normal))
    side = norm(np.cross(UP, n))
    f = 1.0 / ny

    def P(s, t):
        off = side * ((s - 0.5) * w)
        if t <= f:
            return top + (edge - top) * (t / f) + off
        u = (t - f) / (1 - f)
        return edge - UP * (h * u) + off + n * (0.02 + wave * math.sin(math.pi * u) * (0.6 + 0.4 * math.sin(math.pi * s)))
    loft(bone, name, P, 1, ny, region, th=0.02, u_hint=side, v_hint=-UP)


def round_sack(shell, det, name, foot, region="e_sack", yaw=0.0, w=0.62, h=0.8, solid=True):
    """A tied burlap sack that reads round: octagonal bulging body narrowing upwards, a tied neck, a bunched top."""
    foot = v3(*foot)
    R = ry(yaw)
    for k, (y0, y1, s) in enumerate(((0.0, 0.12, 0.84), (0.12, 0.45, 1.0), (0.45, 0.66, 0.84), (0.66, 0.78, 0.58))):
        for j in range(2):
            q = 0.86 if j else 1.0
            add_cube(shell, "%s_%d_%d" % (name, k, j), foot + UP * (h * (y0 + y1) / 2), R @ ry(math.pi / 4 * j + 0.05 * k),
                     (w * s * q, h * (y1 - y0), w * s * q), region, stretch=True)
    add_cube(shell, name + "_neck", foot + UP * (h * 0.83), R, (w * 0.3, h * 0.1, w * 0.3), region, stretch=True)
    add_cube(det, name + "_tie", foot + UP * (h * 0.82), R, (w * 0.36, 0.06, w * 0.36), "rope")
    for j in range(2):
        add_cube(shell, "%s_top_%d" % (name, j), foot + UP * (h * 0.93), R @ ry(0.4 + math.pi / 4 * j), (w * 0.46, h * 0.14, w * 0.42), region,
                 stretch=True)
    if solid:
        collide((foot[0] - w / 2, 0.0, foot[2] - w / 2, foot[0] + w / 2, h, foot[2] + w / 2))


# ================================================================ roof faces with straight radiating stripes
def trap_stripes(cols, n, seed, wfrac, motif=None, motif_col=None, motif_rows=7, motif_per=2, fold=0.14, seams=True):
    """The texture of a roof face drawn in its own (u, t) space (u across the face's BOTTOM width, t from the top
    down): the face is the trapezoid |u - 0.5| <= wfrac(t) / 2 (cut out outside), n stripes radiate from the top
    (stripe k = s in [k/n, (k+1)/n], s = 0.5 + (u - 0.5) / wfrac(t)); cols = colours in turn, or one colour per
    stripe (len(cols) == n); soft folds in each stripe, dark seams, gold glyphs on the stripes of cols[0]."""
    def paint(img):
        from PIL import Image
        rng = random.Random(seed)
        w, h = img.size
        layers = {}
        for c in sorted(set(tuple(c) for c in cols)):
            im = Image.new("RGBA", (w, h))
            ml._weave(im, (0, 0, w, h), c, rng, stains=1)
            layers[c] = im.load()
        px = img.load()
        per = len(cols) == n
        for y in range(h):
            t = (y + 0.5) / h
            f = max(1e-4, wfrac(t))
            for x in range(w):
                u = (x + 0.5) / w
                s = 0.5 + (u - 0.5) / f
                if s < 0.0 or s >= 1.0:
                    px[x, y] = (0, 0, 0, 0)
                    continue
                k = min(n - 1, int(s * n))
                c = tuple(cols[k] if per else cols[k % len(cols)])
                r, g, b, a = layers[c][x, y]
                fk = s * n - k
                kk = (0.88 + 0.14 * t) * (1.0 - fold * 0.5 + fold * math.sin(math.pi * fk))
                if seams and min(fk, 1 - fk) * f * w / n < 0.9:
                    kk *= 0.76
                if min(s, 1 - s) * f * w < 0.9:
                    kk *= 0.8
                px[x, y] = _scale((r, g, b), kk) + (255,)
        if motif:
            mc = motif_col or GOLD
            for j in range(motif_rows):
                t = (j + 0.75) / (motif_rows + 0.5)
                f = wfrac(t)
                for k in range(n):
                    c = cols[k] if per else cols[k % len(cols)]
                    if tuple(c) != tuple(cols[0]):
                        continue
                    m = max(1, int(round(motif_per * (0.3 + 0.7 * t))))
                    for q in range(m):
                        s = (k + (q + 0.5) / m) / n
                        if j % 2 and m > 1:
                            s += 0.25 / (m * n)
                        x = int((0.5 + (s - 0.5) * f) * w)
                        y = int(t * h)
                        if 0 <= x < w and px[x, y][3]:
                            glyph(px, w, h, x, y, motif, mc, rng)
    return paint


def trap_face(bone, name, P, wf, nx, ny, region, th=0.035, overlap=0.012):
    """Lofts a roof face P(s, t) (s between its hips, t from the top down) on a grid of its own (u, t) space (u across
    its bottom width; wf(t) = its width at t / its bottom width): rectangles in (u, t) tile it without overlaps or
    gaps, the region (painted by trap_stripes) cuts the trapezoid out; pieces wholly outside the face are skipped."""
    def Q(u, t):
        f = max(1e-6, wf(t))
        return P(0.5 + (u - 0.5) / f, t)
    for i in range(nx):
        for j in range(ny):
            u0, u1, t0, t1 = i / nx, (i + 1) / nx, j / ny, (j + 1) / ny
            f1 = wf(t1)
            if u1 < 0.5 - f1 / 2 - 0.01 or u0 > 0.5 + f1 / 2 + 0.01:
                continue
            a1, b1, a0, b0 = Q(u0, t0), Q(u1, t0), Q(u0, t1), Q(u1, t1)
            c = (a0 + a1 + b0 + b1) / 4
            uu = ((b0 + b1) - (a0 + a1)) / 2
            L = np.linalg.norm(uu)
            if L < 1e-5:
                continue
            uu = uu / L
            vp = ((a0 - a1) + (b0 - b1)) / 2
            H = np.linalg.norm(vp)
            if H < 1e-5:
                continue
            vv = norm(vp - np.dot(vp, uu) * uu)
            nn = np.cross(uu, vv)
            cube = add_cube(bone, "%s_%d_%d" % (name, i, j), c, np.column_stack([uu, vv, nn]), (L + overlap, H + overlap, th),
                            {"all": None, "+3": region, "-3": region}, stretch=True, u_dir=uu, v_dir=vv)
            ml.gn.set_sub(cube, (u0, t0, u1, t1))


def pyramid_roof2(bone, name, eave, top, regions, sag=0.25, nx=4, ny=8, th=0.035, hang=None):
    """pyramid_roof with straight radiating stripes: each face is lofted by trap_face (regions = (front/back region,
    sides region) or 4 regions, each painted by trap_stripes with roof_wfrac(top width, bottom width) of its face).
    Returns the faces' P(s, t) functions (as pyramid_roof)."""
    eave = [v3(*p) for p in eave]
    top = [v3(*p) for p in top]
    if len(regions) == 2:
        regions = [regions[0], regions[1], regions[0], regions[1]]
    funcs = []
    for k, (i, j) in enumerate([(0, 1), (1, 2), (2, 3), (3, 0)]):
        a0, a1, b0, b1 = top[i], top[j], eave[i], eave[j]
        nrm = norm(np.cross(b1 - b0, (a0 + a1) / 2 - b0))
        inward = nrm if np.dot(nrm, UP) < 0 else -nrm
        out = norm(((b0 + b1) / 2 - (a0 + a1) / 2) * v3(1, 0, 1))
        W, w0 = np.linalg.norm(b1 - b0), np.linalg.norm(a1 - a0)

        def P(s, t, a0=a0, a1=a1, b0=b0, b1=b1, inward=inward, out=out):
            p = (a0 + (a1 - a0) * s) * (1 - t) + (b0 + (b1 - b0) * s) * t
            sc = min(1.0, max(0.0, s))
            # the cloth sags between the hips, less near the narrow top (where the pieces span the whole face)
            taper = min(1.0, 1.6 * t) if w0 < 0.3 * W else 1.0
            p = p + inward * (sag * math.sin(math.pi * t) * taper * math.sin(math.pi * sc))
            p = p + out * (0.03 * t * t * math.sin(sc * math.pi * 4))
            return p

        def wf(t, W=W, w0=w0):
            return (w0 + (W - w0) * t) / W
        trap_face(bone, "%s_%d" % (name, k), P, wf, nx, ny, regions[k], th=th)
        funcs.append(P)
        if hang:
            hh, hregs = hang
            hr = hregs[k] if isinstance(hregs, (list, tuple)) else hregs

            def Hh(s, t, b0=b0, b1=b1, out=out):
                p = b0 + (b1 - b0) * s
                return p - UP * (hh * t) + out * (0.04 * math.sin(math.pi * t) + 0.03 * math.sin(s * math.pi * 5) * t)
            loft(bone, "%s_hang_%d" % (name, k), Hh, max(1, nx), 1, hr, th=0.025, overlap=0.02)
    return funcs


def roof_wfrac(top_w, bottom_w):
    """wfrac(t) of a face whose top edge is top_w wide and bottom edge bottom_w wide (for trap_stripes)."""
    return lambda t: (top_w + (bottom_w - top_w) * t) / bottom_w
