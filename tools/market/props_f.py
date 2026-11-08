"""Shared helpers of the group F market tents (1.26.0): tente_frontiere (frontier merchant, red canvas under furs and
hides, a horned skull on top), tente_sylvestre (sylvan merchant, green elven pavilion on a frame of living branches) and
tente_arsenal (arsenal merchant, steampunk orange-and-cream marquee with gears, copper pipes and a boiler).

Built on merchantlib / tentlib WITHOUT modifying them (same prop system as the other one-block tents: one static
.bbmodel drawn from the anchor block, collision boxes in tents/<id>.json, small things under the bone "detail").

Contents:
  painters (factories returning painter(img) for Atlas.add): canvas(), patchwork(), stripes(), fur(), bark(), wood(),
  steel(), metal(), banner(), rug(), crate_face(), gear_disc(), wisteria(), skull_face(), dags(), crenels(), flames();
  emblem drawers for banner() / rug() / crate_face(): rune(), crossed_axes(), tree(), leaf_rune(), gear_emblem();
  geometry: curve() (Catmull-Rom points), branch() (tapering curved branch), octa() (octagonal beam), pipe()
  (copper pipe through points, elbows, flanges), roof_face() (a sagging canvas slope, straight or concave, returns its
  surface function), flap() (a hanging edge under a slope), drape_on() (a cloth or hide lying on a surface and hanging
  past its edge), valance(), hang_wall() (a hanging canvas wall with folds), tied_drape() (a curtain gathered by a
  tie), gear_plate() (a gear plate with a hub), bull_skull(), crystal(), candle(), iron_chest(), lantern_arm().

Coordinates: tent-local blocks, y up, +z = the open front (towards the player who placed it), the anchor block's
centre (0, 0, 0) at ground level; -x = the left side as seen from the front.
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


# ======================================================================== painters
def _weave(img, c, rng, stains=1, noise=4):
    w, h = img.size
    ml._weave(img, (0, 0, w, h), c, rng, stains=stains)


def _blobs(w, h, rng, n, rmin, rmax, wobble=0.35):
    """n irregular blobs (centre, radius, wobble phases) for patches and spots."""
    return [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(rmin, rmax), [rng.uniform(0, 6.3) for _ in range(3)], wobble) for _ in range(n)]


def _in_blob(x, y, b, sx=1.0, sy=1.0):
    cx, cy, r, ph, wob = b
    dx, dy = (x - cx) / sx, (y - cy) / sy
    a = math.atan2(dy, dx)
    rr = r * (1 + wob * (0.5 * math.sin(3 * a + ph[0]) + 0.3 * math.sin(5 * a + ph[1]) + 0.2 * math.sin(7 * a + ph[2])))
    return math.hypot(dx, dy) < rr


def canvas(base, seed, stains=2, shade=(0.9, 1.04), folds=0, fold_k=0.14, hem=None, hem_px=3):
    """Plain woven canvas of colour base, darker towards the top (shade = factor at top, bottom), soft vertical folds
    (folds per width), an optional hem colour at the bottom."""
    def paint(img):
        rng = random.Random(seed)
        _weave(img, base, rng, stains=stains)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                k = shade[0] + (shade[1] - shade[0]) * y / max(1, h - 1)
                if folds:
                    k *= 1.0 - fold_k / 2 + fold_k / 2 * math.sin(2 * math.pi * folds * (x + 0.5) / w)
                if hem and y >= h - hem_px:
                    px[x, y] = _jitter(hem, rng, 8) + (255,)
                else:
                    px[x, y] = _scale((r, g, b), k) + (255,)
    return paint


def patchwork(base, seed, patches=(), stitches=True, stains=3, shade=(0.88, 1.04), folds=0, rags=0):
    """Canvas of colour base with irregular patches [(colour, count, rmin, rmax)] (hide patches, moss, mended
    cloth) edged by darker stitches, stains, soft folds; rags > 0: a ragged cut-out bottom edge of that many px."""
    def paint(img):
        rng = random.Random(seed)
        _weave(img, base, rng, stains=stains)
        w, h = img.size
        px = img.load()
        blobs = []
        for col, n, r0, r1 in patches:
            for b in _blobs(w, h, rng, n, r0, r1):
                blobs.append((col, b))
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                c = (r, g, b)
                for col, bl in blobs:
                    if _in_blob(x, y, bl, 1.0, 0.7):
                        c = _jitter(_scale(col, 0.97 + 0.06 * math.sin(x * 0.7 + y * 0.4)), rng, 6)
                        if stitches and not _in_blob(x, y, (bl[0], bl[1], bl[2] - 1.4, bl[3], bl[4]), 1.0, 0.7):
                            c = _scale(c, 0.7)
                k = shade[0] + (shade[1] - shade[0]) * y / max(1, h - 1)
                if folds:
                    k *= 0.93 + 0.07 * math.sin(2 * math.pi * folds * (x + 0.5) / w)
                px[x, y] = _scale(c, k) + (255,)
        if rags:
            for x in range(w):
                cut = rags * (0.35 + 0.65 * abs(math.sin(x * 0.37 + 1.3) * math.sin(x * 0.11)))
                if rng.random() < 0.15:
                    cut = rng.uniform(0, rags)
                for y in range(h):
                    if y > h - 1 - cut:
                        px[x, y] = (0, 0, 0, 0)
    return paint


def stripes(colours, seed, n=None, mottle=None, mottle_n=0, seams=True, shade=(0.9, 1.05), fold=0.1, rags=0, dag=0):
    """Vertical stripes cycling through colours (n stripes, default len(colours)), dark seams, a soft fold in each
    stripe; mottle = (colour_a, colour_b): patches of the other colour on each stripe (the sylvan camouflage);
    rags: a ragged cut-out bottom; dag: square-ish leaf dags of that many px at the bottom (cut-out)."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        nn = n or len(colours)
        edges = [int(round(k * w / nn)) for k in range(nn + 1)]
        for k in range(nn):
            sub = img.crop((edges[k], 0, edges[k + 1], h))
            ml._weave(sub, (0, 0, sub.size[0], h), colours[k % len(colours)], rng, stains=2)
            img.paste(sub, (edges[k], 0))
        px = img.load()
        blobs = _blobs(w, h, rng, mottle_n, 3, 9, wobble=0.5) if mottle else []
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                c = (r, g, b)
                k = 0
                while k < nn and x >= edges[k + 1]:
                    k += 1
                if mottle:
                    for bl in blobs:
                        if _in_blob(x, y, bl, 1.0, 1.3):
                            other = mottle[1] if colours[k % len(colours)] == mottle[0] else mottle[0]
                            c = _jitter(_mix(other, c, 0.15), rng, 6)
                frac = (x - edges[k]) / max(1, edges[k + 1] - edges[k])
                kk = shade[0] + (shade[1] - shade[0]) * y / max(1, h - 1)
                kk *= 1.0 - fold / 2 + fold / 2 * math.sin(math.pi * frac)
                if seams and x in (edges[k], edges[k + 1] - 1):
                    kk *= 0.8
                px[x, y] = _scale(c, kk) + (255,)
        if rags:
            for x in range(w):
                cut = rags * (0.3 + 0.7 * abs(math.sin(x * 0.41 + 0.7) * math.sin(x * 0.13 + 2.0)))
                for y in range(h):
                    if y > h - 1 - cut:
                        px[x, y] = (0, 0, 0, 0)
        if dag:
            tw = max(4, w // (nn * 3))
            for x in range(w):
                lx = (x % tw) / tw
                depth = dag * (1.0 - abs(lx - 0.5) * 2) ** 0.6
                for y in range(h):
                    if y > h - 1 - dag + depth:
                        px[x, y] = (0, 0, 0, 0)
    return paint


def fur(base, dark, seed, spots=None, shag=10, tuft_top=True, hide_shape=True):
    """A shaggy fur hide (cut-out): a hide outline with leg lobes, long locks of fur hanging at the bottom (shag px),
    combed light / dark strands, optional dark spots (cowhide). Reads on both faces."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        locks = [rng.uniform(0, 6.3) for _ in range(w)]
        for x in range(w):
            for y in range(h):
                strand = 0.8 + 0.3 * math.sin(x * 1.7 + locks[x] + y * 0.15) * math.sin(x * 0.45 + 0.3)
                strand += 0.14 * math.sin(y * 0.9 + x * 0.3) + 0.12 * math.sin(x * 0.23 + y * 0.31)
                c = _mix(dark, base, 0.35 + 0.65 * max(0.0, min(1.0, strand)))
                px[x, y] = _jitter(c, rng, 6) + (255,)
        if spots:
            for b in _blobs(w, h, rng, spots[1], spots[2], spots[3], wobble=0.55):
                for y in range(h):
                    for x in range(w):
                        if _in_blob(x, y, b, 1.2, 1.0):
                            px[x, y] = _jitter(_scale(spots[0], 0.9 + 0.2 * math.sin(x + y)), rng, 8) + (255,)
        # the outline: a hide (wide body, leg lobes at the corners) with a long shaggy fringe below
        for x in range(w):
            fx = (x + 0.5) / w
            lock = shag * (0.45 + 0.55 * abs(math.sin(x * 0.9 + locks[x]))) * (0.6 + 0.4 * rng.random())
            bottom = h - 1 - (shag - lock)
            if hide_shape:
                # leg lobes: deeper at 0.12 and 0.88, notches between
                bottom -= shag * 0.5 * (1 - math.exp(-((fx - 0.12) ** 2) / 0.004)) * (1 - math.exp(-((fx - 0.88) ** 2) / 0.004)) * (0.4 + 0.6 * (0.2 < fx < 0.8))
            top = 0
            if tuft_top:
                top = 1.5 + 1.5 * math.sin(x * 1.3 + locks[x])
            side = min(x, w - 1 - x)
            for y in range(h):
                edge_in = side < 2 + 1.5 * math.sin(y * 0.8 + x)
                if y > bottom or y < top or edge_in:
                    px[x, y] = (0, 0, 0, 0)
                elif y > bottom - 2.5:
                    r, g, b, a = px[x, y]
                    px[x, y] = _scale((r, g, b), 1.08) + (255,)
    return paint


def bark(base, dark, seed, moss=None, moss_n=6):
    """Gnarled bark: wandering vertical fissures (v along the branch), lighter ridges, knots, optional moss patches."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        ph = [rng.uniform(0, 6.3) for _ in range(8)]
        for y in range(h):
            for x in range(w):
                f = math.sin(x * 0.9 + 1.4 * math.sin(y * 0.21 + ph[0]) + ph[1]) + 0.5 * math.sin(x * 2.3 + y * 0.13 + ph[2])
                k = 0.78 + 0.28 * (f + 1.5) / 3.0
                if f < -0.9:
                    c = _scale(dark, 0.85)
                else:
                    c = _scale(base, k)
                px[x, y] = _jitter(c, rng, 5) + (255,)
        for _ in range(max(1, w * h // 700)):
            kx, ky = rng.uniform(2, w - 2), rng.uniform(2, h - 2)
            for y in range(h):
                for x in range(w):
                    d = math.hypot((x - kx) * 1.3, y - ky)
                    if d < 1.4:
                        px[x, y] = _scale(dark, 0.7) + (255,)
                    elif d < 2.4:
                        r, g, b, a = px[x, y]
                        px[x, y] = _scale((r, g, b), 1.12) + (255,)
        if moss:
            for b in _blobs(w, h, rng, moss_n, 2, 5, wobble=0.6):
                for y in range(h):
                    for x in range(w):
                        if _in_blob(x, y, b, 1.0, 1.4):
                            px[x, y] = _jitter(_scale(moss, 0.85 + 0.3 * rng.random()), rng, 8) + (255,)
    return paint


def wood(base, dark, seed, plank=8, vertical=False, knots=0.1, iron_corners=False):
    """Plain planks / beams (galley_texture.fine_wood); iron_corners: dark iron corner plates."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        ml.fine_wood(img, (0, 0, w, h), base, dark, plank, rng, joints=False, knots=knots, grain=0.13, shade=0.07, vertical=vertical)
        if iron_corners:
            px = img.load()
            for y in range(h):
                for x in range(w):
                    if (x < 4 or x >= w - 4) and (y < 4 or y >= h - 4):
                        px[x, y] = _jitter(_rgb("4a4a50"), rng, 6) + (255,)
    return paint


def steel(base, seed, rivets=8, plates=2, rust=None, rust_n=0):
    """Dark riveted steel plates: hammered surface, plate seams, a row of rivets near each plate edge."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        ml.hammered_iron(img, (0, 0, w, h), base, rng)
        px = img.load()
        pw = w / plates
        for x in range(w):
            if int(x % pw) == 0:
                for y in range(h):
                    px[x, y] = _scale(base, 0.55) + (255,)
        for k in range(plates):
            for j in range(rivets):
                cx = int(k * pw + (j + 0.5) * pw / rivets)
                for cy in (2, h - 3):
                    if 0 <= cx < w:
                        px[cx, cy] = _scale(base, 1.6) + (255,)
                        if cx + 1 < w:
                            px[cx + 1, cy + 1] = _scale(base, 0.5) + (255,)
        if rust:
            for b in _blobs(w, h, rng, rust_n, 1.5, 4):
                for y in range(h):
                    for x in range(w):
                        if _in_blob(x, y, b):
                            r, g, b2, a = px[x, y]
                            px[x, y] = _mix((r, g, b2), rust, 0.55) + (255,)
    return paint


def metal(stops, seed, rivets=False):
    """Polished metal (brass, copper, gold, bronze) on a colour ramp of stops; optional rivets in the corners."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        ml.polished_metal(img, (0, 0, w, h), stops, rng)
        if rivets:
            px = img.load()
            for cx, cy in ((2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)):
                px[cx, cy] = (255, 236, 170, 255)
                px[cx + 1, cy + 1] = (90, 60, 20, 255)
    return paint


def banner(field, border, emblem, seed, fringe=None, point="dags", border_px=3, emblem_box=(0.12, 0.14, 0.88, 0.62)):
    """A hanging banner (cut-out): woven field, border, the emblem (drawer(draw, x0, y0, x1, y1, S)) in emblem_box
    (fractions of the image), the bottom: point="dags" (three V dags with a fringe) or "v" (one V point) or "swallow"."""
    def paint(img):
        from PIL import Image, ImageDraw
        rng = random.Random(seed)
        _weave(img, field, rng, stains=1)
        w, h = img.size
        px = img.load()
        body = int(h * 0.8)
        fr = fringe or border
        for y in range(h):
            for x in range(w):
                fx = (x + 0.5) / w
                if point == "dags":
                    k = (fx * 3) % 1.0
                    cut = body + (h - body) * (1 - abs(k - 0.5) * 2)
                elif point == "v":
                    cut = body + (h - body) * (1 - abs(fx - 0.5) * 2)
                else:
                    cut = h - (h - body) * (1 - abs(fx - 0.5) * 2)
                if y > cut:
                    px[x, y] = (0, 0, 0, 0)
                elif y > cut - 3 and y >= body - 1:
                    # the fringe along the cut edge: little tassels
                    px[x, y] = _jitter(fr if (x % 2 == 0 or y > cut - 2) else _scale(fr, 0.8), rng, 10) + (255,)
                elif x < border_px or x >= w - border_px or y < border_px:
                    px[x, y] = _jitter(border, rng, 8) + (255,)
        S = 4
        x0, y0, x1, y1 = (int(emblem_box[0] * w), int(emblem_box[1] * h), int(emblem_box[2] * w), int(emblem_box[3] * h))
        big = Image.new("RGBA", ((x1 - x0) * S, (y1 - y0) * S), (0, 0, 0, 0))
        emblem(ImageDraw.Draw(big), 0, 0, (x1 - x0) * S, (y1 - y0) * S, S)
        img.alpha_composite(big.resize((x1 - x0, y1 - y0), Image.LANCZOS), (x0, y0))
        # crisp alpha (cut-out): no half-transparent pixels
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                px[x, y] = (r, g, b, 255 if a > 127 else 0)
    return paint


def rug(field, border, accent, seed, motif=None, rings=0, fringe=None):
    """A rug: field, a dark border with an accent band, `rings` concentric accent ovals (the frontier's) or a motif
    drawer in the middle; fringe colour along the two short ends."""
    def paint(img):
        from PIL import Image, ImageDraw
        rng = random.Random(seed)
        _weave(img, field, rng, stains=2)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                e = min(x, y, w - 1 - x, h - 1 - y)
                if fringe and (y < 2 or y >= h - 2) and x % 2 == 0:
                    px[x, y] = _jitter(fringe, rng, 8) + (255,)
                elif e < 4:
                    px[x, y] = _jitter(border, rng, 6) + (255,)
                elif e in (5, 6) or e == 11:
                    px[x, y] = _jitter(accent, rng, 8) + (255,)
                elif 7 <= e <= 10 and (x + y) % 5 < 2:
                    px[x, y] = _jitter(_mix(field, accent, 0.5), rng, 6) + (255,)
                if rings:
                    dx, dy = (x - w / 2) / (w * 0.36), (y - h / 2) / (h * 0.32)
                    d = math.hypot(dx, dy)
                    ring = abs((d * rings * 2 + 0.5) % 2 - 1)
                    if d < 1.0 and ring > 0.84:
                        px[x, y] = _jitter(accent, rng, 8) + (255,)
                    elif d < 1.0 and ring > 0.72 and (x + y) % 3:
                        px[x, y] = _jitter(_mix(field, accent, 0.35), rng, 6) + (255,)
                    if abs(dx) + abs(dy) * 0.8 < 0.2:
                        px[x, y] = _jitter(accent if abs(dx) + abs(dy) * 0.8 > 0.1 else _mix(field, accent, 0.5), rng, 8) + (255,)
        if motif:
            S = 4
            mw, mh = int(w * 0.5), int(h * 0.56)
            big = Image.new("RGBA", (mw * S, mh * S), (0, 0, 0, 0))
            motif(ImageDraw.Draw(big), 0, 0, mw * S, mh * S, S)
            img.alpha_composite(big.resize((mw, mh), Image.LANCZOS), ((w - mw) // 2, (h - mh) // 2))
            for y in range(h):
                for x in range(w):
                    r, g, b, a = px[x, y]
                    px[x, y] = (r, g, b, 255)
    return paint


def crate_face(wood_base, wood_dark, seed, emblem=None, iron=(70, 70, 76), emblem_frac=0.56):
    """A crate / chest face: planks, a dark frame, iron corner plates with rivets, an emblem in the middle."""
    def paint(img):
        from PIL import Image, ImageDraw
        rng = random.Random(seed)
        w, h = img.size
        ml.fine_wood(img, (0, 0, w, h), wood_base, wood_dark, max(4, h // 5), rng, joints=False, knots=0.1, grain=0.12, shade=0.06,
                     vertical=True)
        px = img.load()
        for y in range(h):
            for x in range(w):
                e = min(x, y, w - 1 - x, h - 1 - y)
                if (x < 6 or x >= w - 6) and (y < 6 or y >= h - 6):
                    px[x, y] = _jitter(iron, rng, 6) + (255,)
                elif e < 3:
                    px[x, y] = _jitter(_scale(wood_dark, 1.1), rng, 5) + (255,)
        for cx, cy in ((3, 3), (w - 4, 3), (3, h - 4), (w - 4, h - 4)):
            px[cx, cy] = (200, 160, 70, 255)
        if emblem:
            S = 4
            s = int(min(w, h) * emblem_frac)
            big = Image.new("RGBA", (s * S, s * S), (0, 0, 0, 0))
            emblem(ImageDraw.Draw(big), 0, 0, s * S, s * S, S)
            img.alpha_composite(big.resize((s, s), Image.LANCZOS), ((w - s) // 2, (h - s) // 2))
            for y in range(h):
                for x in range(w):
                    r, g, b, a = px[x, y]
                    px[x, y] = (r, g, b, 255)
    return paint


def gear_disc(colour, dark, seed, teeth=10, spokes=4, hole=True):
    """A cut-out gear: toothed rim, spokes, a hub with a hole, brass shading."""
    def paint(img):
        from PIL import Image, ImageDraw
        w, h = img.size
        S = 4
        big = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
        gear_emblem(ImageDraw.Draw(big), 0, 0, w * S, h * S, S, colour=colour, dark=dark, teeth=teeth, spokes=spokes, hole=hole)
        big = big.resize((w, h), Image.LANCZOS)
        img.alpha_composite(big)
        rng = random.Random(seed)
        px = img.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a > 127:
                    k = 1.0 + 0.18 * ((w - x) + (h - y) - w) / w
                    px[x, y] = _jitter(_scale((r, g, b), k), rng, 4) + (255,)
                else:
                    px[x, y] = (0, 0, 0, 0)
    return paint


def wisteria(seed, petals=((176, 112, 226), (204, 150, 244), (134, 78, 196), (226, 190, 250))):
    """A hanging wisteria cluster (cut-out): a cone of small purple / lilac florets, widest at the top, green stem."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                px[x, y] = (0, 0, 0, 0)
        for y in range(h):
            t = y / h
            half = (w / 2 - 1) * (1 - t) ** 0.8 * (0.85 + 0.15 * math.sin(y * 0.7))
            for x in range(w):
                if abs(x + 0.5 - w / 2) < half and rng.random() < 0.86:
                    c = petals[rng.randrange(len(petals))]
                    if (x + y) % 3 == 0:
                        c = _scale(c, 0.78)
                    px[x, y] = c + (255,)
        for y in range(0, max(2, h // 8)):
            px[w // 2, y] = (70, 110, 40, 255)
            if w // 2 + 1 < w:
                px[w // 2 + 1, y] = (90, 130, 50, 255)
    return paint


def skull_face(seed, bone_c=(232, 222, 196), dark=(46, 34, 26)):
    """The front of a horned animal skull: bone, two deep eye sockets, a nasal cavity, a darker snout tip with teeth."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                k = 0.86 + 0.18 * math.sin((x + 0.5) / w * math.pi) - 0.08 * (y / h)
                px[x, y] = _jitter(_scale(bone_c, k), rng, 6) + (255,)
        for sx in (-1, 1):
            cx, cy = w / 2 + sx * w * 0.24, h * 0.3
            for y in range(h):
                for x in range(w):
                    d = math.hypot((x - cx) / (w * 0.13), (y - cy) / (h * 0.12))
                    if d < 1.0:
                        px[x, y] = _jitter(dark, rng, 4) + (255,)
                    elif d < 1.35:
                        r, g, b, a = px[x, y]
                        px[x, y] = _scale((r, g, b), 0.82) + (255,)
        for y in range(int(h * 0.55), int(h * 0.75)):
            for x in range(w):
                if abs(x + 0.5 - w / 2) < w * 0.07 * (1 + (y - h * 0.55) / (h * 0.3)):
                    px[x, y] = _jitter(dark, rng, 4) + (255,)
        for y in range(int(h * 0.84), h):
            for x in range(int(w * 0.22), int(w * 0.78)):
                px[x, y] = (dark if (x % 3 == 0 or y == h - 1) else _scale(bone_c, 0.94)) + (255,)
        # cracks
        for k in range(3):
            x, y = rng.uniform(w * 0.2, w * 0.8), rng.uniform(0, h * 0.2)
            for s in range(6):
                if 0 <= int(x) < w and 0 <= int(y) < h:
                    px[int(x), int(y)] = _scale(bone_c, 0.7) + (255,)
                x += rng.uniform(-1, 1)
                y += 1
    return paint


def dags(base, edge, seed, n=8, depth=0.45, alt=None):
    """A valance of n pointed dags (V tabs) along u, a band at the top, edged in `edge`; alt: every other tab in it."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        band = int(h * (1 - depth))
        tw = w / n
        for x in range(w):
            k = int(x / tw)
            lx = (x % tw) / tw
            c0 = alt if (alt and k % 2) else base
            cut = band + (h - band) * (1 - abs(lx - 0.5) * 2)
            for y in range(h):
                if y > cut:
                    px[x, y] = (0, 0, 0, 0)
                elif y > cut - 2.2 or y < 2:
                    px[x, y] = _jitter(edge, rng, 8) + (255,)
                else:
                    px[x, y] = _jitter(_scale(c0, 0.95 + 0.08 * math.sin(x * 0.6)), rng, 5) + (255,)
    return paint


def crenels(colours, edge, seed, n=12, depth=0.45, deco=None, deco_every=3):
    """A crenellated valance: n square tabs cycling through colours, a top band, dark edges; deco(draw, x0, y0, x1,
    y1, S) painted on every deco_every-th tab (the arsenal's little gears)."""
    def paint(img):
        from PIL import Image, ImageDraw
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        band = int(h * (1 - depth))
        tw = w / n
        for x in range(w):
            k = int(x / tw)
            lx = (x % tw) / tw
            c0 = colours[k % len(colours)]
            in_tab = 0.1 <= lx <= 0.9
            for y in range(h):
                if y > band and not in_tab:
                    px[x, y] = (0, 0, 0, 0)
                elif y < 2 or y >= h - 2 or (y > band and (lx < 0.16 or lx > 0.84)) or y == band:
                    px[x, y] = _jitter(edge, rng, 6) + (255,)
                else:
                    px[x, y] = _jitter(_scale(c0, 0.93 + 0.1 * (y / h)), rng, 6) + (255,)
        if deco:
            S = 4
            for k in range(0, n, deco_every):
                s = int(min(tw * 0.7, h * 0.7))
                big = Image.new("RGBA", (s * S, s * S), (0, 0, 0, 0))
                deco(ImageDraw.Draw(big), 0, 0, s * S, s * S, S)
                img.alpha_composite(big.resize((s, s), Image.LANCZOS), (int(k * tw + (tw - s) / 2), int((h - s) / 2)))
            for y in range(h):
                for x in range(w):
                    r, g, b, a = px[x, y]
                    px[x, y] = (r, g, b, 255 if a > 127 else 0)
    return paint


def flames(seed):
    """A candle flame / glowing lamp glass (drawn full bright by the "glow" cube names)."""
    def paint(img):
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                d = math.hypot((x + 0.5 - w / 2) / (w / 2), (y + 0.5 - h * 0.6) / (h * 0.6))
                c = _mix((255, 248, 200), (240, 150, 40), min(1.0, d))
                px[x, y] = c + (255,)
    return paint


def crystal_tex(light, dark, seed):
    """A glowing crystal: facets light / dark in bands, a bright core."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                f = ((x * 2 + y) // 5) % 3
                c = _mix(dark, light, 0.35 + 0.3 * f)
                if abs(x - w / 2) < w * 0.15:
                    c = _mix(c, (255, 255, 255), 0.35)
                px[x, y] = _jitter(c, rng, 6) + (255,)
    return paint


# ---------------------------------------------------------------- emblems (drawers on an ImageDraw, box x0 y0 x1 y1, S = scale)
def rune(d, x0, y0, x1, y1, S, colour=(244, 236, 214), dark=(150, 120, 90)):
    """The frontier banners' white rune: a diamond with a hollow centre, four arrow points and side hooks."""
    w, h = x1 - x0, y1 - y0
    cx, cy = x0 + w / 2, y0 + h / 2
    r = min(w, h) * 0.3
    lw = max(2, int(min(w, h) * 0.07))
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], outline=colour, width=lw)
    d.polygon([(cx, cy - r * 0.32), (cx + r * 0.32, cy), (cx, cy + r * 0.32), (cx - r * 0.32, cy)], fill=colour)
    for a in range(4):
        ang = a * math.pi / 2
        ux, uy = math.cos(ang), math.sin(ang)
        px_, py_ = cx + ux * r * 1.05, cy + uy * r * 1.05
        tip = (cx + ux * r * 1.55, cy + uy * r * 1.55)
        d.line([(px_, py_), tip], fill=colour, width=lw)
        vx, vy = -uy, ux
        d.line([(tip[0] - ux * r * 0.25 + vx * r * 0.22, tip[1] - uy * r * 0.25 + vy * r * 0.22), tip,
                (tip[0] - ux * r * 0.25 - vx * r * 0.22, tip[1] - uy * r * 0.25 - vy * r * 0.22)], fill=colour, width=lw)
    for a in range(4):
        ang = math.pi / 4 + a * math.pi / 2
        ux, uy = math.cos(ang), math.sin(ang)
        p = (cx + ux * r * 0.95, cy + uy * r * 0.95)
        d.ellipse([p[0] - lw, p[1] - lw, p[0] + lw, p[1] + lw], fill=colour)


def crossed_axes(d, x0, y0, x1, y1, S, head=(222, 220, 214), haft=(150, 104, 60), edge=(90, 70, 50)):
    """Two crossed bearded axes (heads up), wooden hafts."""
    w, h = x1 - x0, y1 - y0
    lw = max(2, int(min(w, h) * 0.07))
    for sgn in (-1, 1):
        a = (x0 + w * (0.5 - 0.36 * sgn), y0 + h * 0.92)
        b = (x0 + w * (0.5 + 0.3 * sgn), y0 + h * 0.12)
        d.line([a, b], fill=edge, width=lw + 2 * S)
        d.line([a, b], fill=haft, width=lw)
        hx, hy = b
        poly = [(hx - sgn * w * 0.02, hy - h * 0.06), (hx + sgn * w * 0.22, hy - h * 0.14), (hx + sgn * w * 0.28, hy + h * 0.06),
                (hx + sgn * w * 0.2, hy + h * 0.2), (hx - sgn * w * 0.04, hy + h * 0.1)]
        d.polygon(poly, fill=head, outline=edge)


def tree(d, x0, y0, x1, y1, S, colour=(52, 96, 44), dark=(30, 60, 26)):
    """The sylvan banner's tree: a trunk with roots and a rounded crown of branching limbs."""
    w, h = x1 - x0, y1 - y0
    cx = x0 + w / 2
    lw = max(2, int(w * 0.08))
    d.line([(cx, y0 + h * 0.92), (cx, y0 + h * 0.36)], fill=colour, width=lw + S)
    for sgn in (-1, 1):
        d.line([(cx, y0 + h * 0.86), (cx + sgn * w * 0.2, y0 + h * 0.96)], fill=colour, width=lw)
        for k, (yy, dx, dy) in enumerate(((0.62, 0.3, -0.16), (0.48, 0.34, -0.18), (0.36, 0.26, -0.2))):
            a = (cx, y0 + h * yy)
            b = (cx + sgn * w * dx, y0 + h * (yy + dy))
            d.line([a, b], fill=colour, width=max(2, lw - k * S))
            d.line([b, (b[0] + sgn * w * 0.06, b[1] - h * 0.08)], fill=colour, width=max(2, lw - (k + 1) * S))
            d.line([b, (b[0] - sgn * w * 0.04, b[1] - h * 0.1)], fill=colour, width=max(2, lw - (k + 1) * S))
    d.line([(cx, y0 + h * 0.4), (cx, y0 + h * 0.06)], fill=colour, width=lw)
    d.line([(cx, y0 + h * 0.22), (cx - w * 0.12, y0 + h * 0.08)], fill=colour, width=max(2, lw - S))
    d.line([(cx, y0 + h * 0.22), (cx + w * 0.12, y0 + h * 0.08)], fill=colour, width=max(2, lw - S))


def leaf_rune(d, x0, y0, x1, y1, S, colour=(214, 176, 72)):
    """The sylvan drape's golden rune: a stem with three pointed leaves and a diamond foot."""
    w, h = x1 - x0, y1 - y0
    cx = x0 + w / 2
    lw = max(2, int(w * 0.06))
    d.line([(cx, y0 + h * 0.15), (cx, y0 + h * 0.85)], fill=colour, width=lw)
    for sgn in (-1, 1):
        d.polygon([(cx, y0 + h * 0.5), (cx + sgn * w * 0.3, y0 + h * 0.3), (cx + sgn * w * 0.18, y0 + h * 0.52)], fill=colour)
    d.polygon([(cx, y0 + h * 0.05), (cx + w * 0.1, y0 + h * 0.22), (cx, y0 + h * 0.34), (cx - w * 0.1, y0 + h * 0.22)], fill=colour)
    d.polygon([(cx, y0 + h * 0.8), (cx + w * 0.08, y0 + h * 0.88), (cx, y0 + h * 0.96), (cx - w * 0.08, y0 + h * 0.88)], fill=colour)


def gear_emblem(d, x0, y0, x1, y1, S, colour=(226, 166, 52), dark=(130, 84, 22), teeth=10, spokes=4, hole=True):
    """A gear: toothed rim, spokes, hub (the arsenal emblem)."""
    w, h = x1 - x0, y1 - y0
    cx, cy = x0 + w / 2, y0 + h / 2
    R = min(w, h) * 0.5
    ro, ri = R * 0.98, R * 0.78
    pts = []
    for k in range(teeth * 4):
        a = 2 * math.pi * k / (teeth * 4)
        r = ro if (k % 4) in (1, 2) else ri
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=colour, outline=dark)
    d.ellipse([cx - ri * 0.72, cy - ri * 0.72, cx + ri * 0.72, cy + ri * 0.72], fill=(0, 0, 0, 0) if hole else _scale(colour, 0.7))
    for k in range(spokes):
        a = 2 * math.pi * k / spokes + math.pi / 4
        d.line([(cx, cy), (cx + ri * 0.8 * math.cos(a), cy + ri * 0.8 * math.sin(a))], fill=colour, width=max(2, int(R * 0.18)))
    d.ellipse([cx - R * 0.24, cy - R * 0.24, cx + R * 0.24, cy + R * 0.24], fill=colour, outline=dark, width=max(1, S))
    d.ellipse([cx - R * 0.08, cy - R * 0.08, cx + R * 0.08, cy + R * 0.08], fill=dark)


# ======================================================================== geometry
def curve(pts, n):
    """n+1 points on the Catmull-Rom curve through pts (ends repeated)."""
    P = [v3(*p) for p in pts]
    P = [P[0]] + P + [P[-1]]
    out = []
    segs = len(pts) - 1
    for k in range(n + 1):
        t = k / n * segs
        i = min(int(t), segs - 1)
        u = t - i
        p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    return out


def octa(bone, name, p0, p1, r, region, extend=0.0, ends=None):
    """An octagonal beam (two square beams turned 45 degrees about the axis) of radius r from p0 to p1."""
    p0, p1 = v3(*p0), v3(*p1)
    d = norm(p1 - p0)
    up = UP if abs(d[1]) < 0.95 else X
    s0 = norm(np.cross(d, up))
    u0 = np.cross(s0, d)
    reg = region if ends is None else {"all": region, "+1": ends, "-1": ends}
    for k, u in enumerate((u0, norm(u0 + s0))):
        beam(bone, "%s_%d" % (name, k), p0, p1, 2 * r * 0.83, reg, width=2 * r * 0.83, up=u, extend=extend)


def branch(bone, name, pts, d0, d1, region, n=6, octagonal=False, ends="end_grain"):
    """A tapering curved branch through pts (Catmull-Rom, n segments), thickness d0 at the start to d1 at the end."""
    P = curve(pts, n)
    for k in range(n):
        d = d0 + (d1 - d0) * (k + 0.5) / n
        if octagonal:
            octa(bone, "%s_%d" % (name, k), P[k], P[k + 1], d / 2, region, extend=d * 0.18)
        else:
            beam(bone, "%s_%d" % (name, k), P[k], P[k + 1], d, {"all": region, "+1": ends, "-1": ends} if k in (0, n - 1) else region,
                 extend=d * 0.22)
    return P


def pipe(bone, det, name, pts, r, region="ar_copper", flange="ar_brass", elbow=True):
    """A metal pipe through the corner points pts (straight runs), an elbow block and two flanges at each corner,
    a flange at each end."""
    P = [v3(*p) for p in pts]
    for k in range(len(P) - 1):
        a, b = P[k], P[k + 1]
        dd = norm(b - a)
        octa(bone, "%s_run_%d" % (name, k), a + dd * (r * 0.9 if k > 0 else 0), b - dd * (r * 0.9 if k < len(P) - 2 else 0), r, region)
        for j, (p, s) in enumerate(((a, 1), (b, -1))):
            fl = p + dd * s * (r * 1.3 if ((j == 0 and k > 0) or (j == 1 and k < len(P) - 2)) else 0.06)
            octa(det, "%s_fl_%d_%d" % (name, k, j), fl - dd * 0.04, fl + dd * 0.04, r * 1.35, flange)
    if elbow:
        for k in range(1, len(P) - 1):
            add_cube(bone, "%s_elbow_%d" % (name, k), P[k], EYE, (r * 2.1, r * 2.1, r * 2.1), region, stretch=True)


def profile(t, concave):
    """Vertical fraction of a slope's drop at t (0 = top, 1 = eave): straight (0) .. steep top / flat eave (1)."""
    return (1 - concave) * t + concave * (1 - (1 - t) ** 2)


def roof_face(bone, name, top_a, top_b, eave_a, eave_b, region, nx=4, ny=4, sag=0.12, concave=0.0, folds=0, fold=0.0,
              th=0.035, overlap=0.03, centre=(0.0, 0.0, 0.0), build=True, droop=0.0):
    """A canvas slope from the top edge top_a-top_b (a ridge, or one point for a pavilion face) down to the eave
    edge eave_a-eave_b: straight or concave profile, sagging between its edges by `sag` (towards the inside), `folds`
    soft folds across (bulges of `fold`), the eave edge drooping by `droop` between its ends. Returns P(s, t) (s across
    from a to b, t from the top down)."""
    top_a, top_b, eave_a, eave_b, centre = (v3(*p) for p in (top_a, top_b, eave_a, eave_b, centre))
    mid_top, mid_eave = (top_a + top_b) / 2, (eave_a + eave_b) / 2
    across = eave_b - eave_a
    down = mid_eave - mid_top
    nrm = norm(np.cross(down, across))
    if np.dot(nrm, (mid_top + mid_eave) / 2 - centre) < 0:
        nrm = -nrm

    def P(s, t):
        tp = top_a + (top_b - top_a) * s
        ev = eave_a + (eave_b - eave_a) * s
        hz = tp + (ev - tp) * t
        y = tp[1] + (ev[1] - tp[1]) * profile(t, concave)
        p = v3(hz[0], y - droop * math.sin(math.pi * s) * t * t, hz[2])
        p = p - nrm * (sag * math.sin(math.pi * s) * math.sin(math.pi * min(t, 1.0)))
        if folds:
            p = p - nrm * (fold * math.sin(math.pi * ((s * folds) % 1.0)) * min(1.0, t * 1.5))
        return p
    if build:
        loft(bone, name, P, nx, ny, region, th=th, overlap=overlap)
    return P


def flap(bone, name, P, length, region, nx=4, out=0.06, th=0.03, s0=0.0, s1=1.0, sway=0.03):
    """A hanging edge under a slope P (its eave t = 1): falls `length` straight down, leaning out a little."""
    e0, e1 = P(s0, 1.0), P(s1, 1.0)
    side = norm(e1 - e0)
    outv = norm(np.cross(side, UP))
    mid = P((s0 + s1) / 2, 0.0)
    if np.dot(outv, (e0 + e1) / 2 - mid) < 0:
        outv = -outv

    def F(s, t):
        ss = s0 + (s1 - s0) * s
        return P(ss, 1.0) - UP * (length * t) + outv * (out * t + sway * math.sin(ss * 17.0) * t)
    loft(bone, name, F, nx, 1, region, th=th)
    return F


def drape_on(bone, name, P, s0, s1, t0, t1, region, nx=3, ny=3, lift=0.05, hang=0.0, hang_region=None, centre=(0, 0, 0),
             sway=0.06, th=0.035):
    """A cloth / hide lying on the surface P over s0..s1, t0..t1 (lifted `lift` off it), then hanging `hang` straight
    down past t1 (its own row, region hang_region or the same)."""
    centre = v3(*centre)

    def nrm_at(s, t):
        e = 0.02
        a = P(min(1, s + e), t) - P(max(0, s - e), t)
        b = P(s, min(1, t + e)) - P(s, max(0, t - e))
        n = norm(np.cross(b, a))
        if np.dot(n, P(s, t) - centre) < 0:
            n = -n
        return n

    def Q(u, v):
        s = s0 + (s1 - s0) * u
        t = t0 + (t1 - t0) * v
        return P(s, t) + nrm_at(s, t) * lift
    loft(bone, name, Q, nx, ny, region, th=th)
    if hang > 0:
        def H(u, v):
            s = s0 + (s1 - s0) * u
            e = Q(u, 1.0)
            out = nrm_at(s, t1)
            out[1] = 0
            return e - UP * (hang * v) + norm(out) * (0.04 * v + sway * v * math.sin(u * 9.0))
        loft(bone, name + "_hang", H, nx, 1, hang_region or region, th=th)
    return Q


def valance(bone, name, a, b, out, h, region, nx=None, flare=0.06, sag=0.0):
    """A hanging valance (dags / crenels, cut-out region) whose top edge runs from a to b, flaring out towards out."""
    a, b, out = v3(*a), v3(*b), v3(*out)

    def V(s, t):
        e = a + (b - a) * s - UP * (sag * math.sin(math.pi * s))
        return e - UP * (h * t) + out * (0.02 + flare * t)
    L = np.linalg.norm(b - a)
    loft(bone, name, V, nx or max(1, int(round(L / 2.2))), 1, region, th=0.025)


def hang_wall(bone, name, a, b, y0, y1, out, region, nx=4, fold=0.05, flare=0.0, ny=2):
    """A hanging canvas wall from ground point a to b, from y1 (top) down to y0, soft vertical folds towards out,
    the foot flaring out by `flare`."""
    a, b, out = v3(*a), v3(*b), v3(*out)

    def P(s, t):
        p = a + (b - a) * s
        return v3(p[0], y1 - (y1 - y0) * t, p[2]) + out * (fold * math.sin(s * math.pi * nx) * (0.4 + 0.6 * t) + flare * t * t)
    loft(bone, name, P, nx, ny, region, th=0.03)
    return P


def tied_drape(bone, det, name, top_a, top_b, tie, bot_a, bot_b, normal, region, nx=3, tie_region="rope"):
    """A curtain hanging from top_a-top_b, gathered at `tie` (a band), flaring again below to bot_a-bot_b."""
    top_a, top_b, tie, bot_a, bot_b, n = (v3(*p) for p in (top_a, top_b, tie, bot_a, bot_b, normal))
    side = norm(top_b - top_a)

    def U(s, t):
        tt = t ** 0.85
        a = top_a + (top_b - top_a) * s
        b = tie + side * ((s - 0.5) * 0.18)
        return a * (1 - tt) + b * tt + n * (0.07 * math.sin(s * math.pi * 3) * (1 - t) + 0.05 * math.sin(math.pi * t))

    def Lw(s, t):
        a = tie + side * ((s - 0.5) * 0.18)
        b = bot_a + (bot_b - bot_a) * s
        return a * (1 - t) + b * t + n * (0.05 * math.sin(s * math.pi * 3 + 0.5) * t)
    loft(bone, name + "_up", U, nx, 3, region, th=0.03)
    loft(bone, name + "_lo", Lw, nx, 2, region, th=0.03)
    add_cube(det, name + "_tie", tie, np.column_stack([side, UP, np.cross(side, UP)]), (0.28, 0.08, 0.17), tie_region)


def gear_plate(bone, det, name, center, normal, r, plate_region, hub_region, th=0.06):
    """A gear: a cut-out toothed plate (plate_region) facing `normal`, a hub block and a bolt."""
    c, n = v3(*center), norm(v3(*normal))
    ml.plate(bone, name, c, 2 * r, 2 * r, plate_region, normal=n, th=th)
    side = norm(np.cross(UP, n)) if abs(n[1]) < 0.9 else X
    axes = np.column_stack([side, np.cross(n, side), n])
    add_cube(det, name + "_hub", c + n * (th / 2 + 0.03), axes, (r * 0.42, r * 0.42, 0.08), hub_region)
    add_cube(det, name + "_bolt", c + n * (th / 2 + 0.08), axes, (r * 0.16, r * 0.16, 0.05), "iron")


def bull_skull(bone, det, name, base, facing=(0, 0, 1), s=1.0, tilt=0.0, face="fr_skull", bone_reg="fr_bone"):
    """A horned bull skull, its back at `base` (the middle of the cranium's back), facing `facing`, tilted forward by
    `tilt` (radians): a cranium, a tapering snout with the painted face, cheek bones, two big crescent horns curving
    out, up and a little forward."""
    base = v3(*base)
    f = norm(v3(*facing))
    side = norm(np.cross(UP, f))
    up = np.cross(f, side)
    # forward tilt: rotate f and up about side
    ct, st = math.cos(tilt), math.sin(tilt)
    f, up = f * ct - up * st, up * ct + f * st
    R = np.column_stack([side, up, f])

    def at(x, y, z):
        return base + side * (x * s) + up * (y * s) + f * (z * s)
    add_cube(bone, name + "_cranium", at(0, 0.0, 0.2), R, (0.72 * s, 0.48 * s, 0.42 * s), {"all": bone_reg, "+3": bone_reg})
    add_cube(bone, name + "_brow", at(0, 0.14, 0.44), R, (0.78 * s, 0.22 * s, 0.1 * s), bone_reg)
    add_cube(bone, name + "_face", at(0, -0.26, 0.46), R, (0.62 * s, 0.86 * s, 0.18 * s), {"all": bone_reg, "+3": face}, stretch=True)
    add_cube(bone, name + "_snout", at(0, -0.8, 0.44), R, (0.42 * s, 0.32 * s, 0.16 * s), {"all": bone_reg, "+3": face}, stretch=True)
    for sx in (-1, 1):
        add_cube(det, "%s_cheek_%d" % (name, sx), at(sx * 0.33, -0.16, 0.4), R @ rz(sx * 0.25), (0.09 * s, 0.38 * s, 0.13 * s), bone_reg)
        # the horn: out from the side of the cranium, then curving up and forward into a point
        pts = [at(sx * 0.28, 0.08, 0.2), at(sx * 0.62, 0.12, 0.22), at(sx * 0.95, 0.32, 0.25), at(sx * 1.12, 0.72, 0.3), at(sx * 1.05, 1.1, 0.4),
               at(sx * 0.9, 1.3, 0.48)]
        P = curve(pts, 7)
        for k in range(7):
            d = (0.27 - 0.03 * k) * s
            beam(bone if k < 4 else det, "%s_horn_%d_%d" % (name, sx, k), P[k], P[k + 1], d, bone_reg, extend=d * 0.3)
        add_cube(det, "%s_horn_ring_%d" % (name, sx), P[1], R, (0.1 * s, 0.25 * s, 0.25 * s), "leather_dark")


def crystal(bone, name, foot, h, w, region, tilt=(0.0, 0.0), yaw=0.0):
    """A glowing crystal (full bright): a long hexagonal-ish prism (two turned boxes) with a pointed tip."""
    foot = v3(*foot)
    R = ry(yaw) @ rx(tilt[0]) @ rz(tilt[1])
    up = R[:, 1]
    for k, a in enumerate((0.0, math.pi / 4)):
        add_cube(bone, "glow_%s_%d" % (name, k), foot + up * (h * 0.4), R @ ry(a), (w, h * 0.8, w * 0.8), region, stretch=True)
    add_cube(bone, "glow_%s_tip" % name, foot + up * (h * 0.86), R @ ry(math.pi / 8) @ rx(0.0), (w * 0.62, h * 0.24, w * 0.62), region, stretch=True)


def candle(bone, name, foot, h=0.14, r=0.035, wax="wax", flame="f_flame"):
    """A small candle: a wax stick and a full-bright flame."""
    foot = v3(*foot)
    add_cube(bone, name, foot + UP * h / 2, EYE, (2 * r, h, 2 * r), wax)
    add_cube(bone, "glow_" + name + "_flame", foot + UP * (h + 0.035), ry(math.pi / 4), (r * 1.2, 0.07, r * 1.2), flame)


def iron_chest(shell, det, name, foot, w=0.9, d=0.6, h=0.62, yaw=0.0, face="crate", wood_reg="crate", band="iron", lid_round=True,
               solid=True):
    """An iron-banded chest: body (front face painted), a rounded lid (two boxes), iron bands and corners, a lock."""
    foot = v3(*foot)
    R = ry(yaw)
    add_cube(shell, name + "_body", foot + UP * (h * 0.34), R, (w, h * 0.68, d), {"all": wood_reg, "+3": face}, stretch=True)
    add_cube(shell, name + "_lid", foot + UP * (h * 0.77), R, (w + 0.02, h * 0.2, d + 0.02), wood_reg, stretch=True)
    if lid_round:
        add_cube(shell, name + "_lid_top", foot + UP * (h * 0.92), R, (w, h * 0.12, d * 0.7), wood_reg, stretch=True)
    for k, sx in enumerate((-0.42, 0.42)):
        add_cube(det, "%s_band_%d" % (name, k), foot + R @ v3(sx * w, h * 0.5, 0), R, (0.07, h + 0.02, d + 0.03), band)
    add_cube(det, name + "_rim", foot + UP * (h * 0.68), R, (w + 0.04, 0.05, d + 0.04), band)
    add_cube(det, name + "_lock", foot + R @ v3(0, h * 0.6, d / 2 + 0.02), R, (0.14, 0.17, 0.04), "gold")
    if solid:
        ex = abs(math.cos(yaw)) * w / 2 + abs(math.sin(yaw)) * d / 2
        ez = abs(math.sin(yaw)) * w / 2 + abs(math.cos(yaw)) * d / 2
        collide((foot[0] - ex, foot[1], foot[2] - ez, foot[0] + ex, foot[1] + h, foot[2] + ez))


def lantern_arm(shell, det, name, mount, out, drop=0.5, size=0.38, metal="iron", length=0.42):
    """An iron arm from mount (on a post) out along `out`, a brace under it and a lantern hanging from its tip."""
    mount, out = v3(*mount), norm(v3(*out))
    tip = mount + out * length
    beam(det, name + "_arm", mount, tip, 0.05, "iron", extend=0.03)
    beam(det, name + "_brace", mount - UP * 0.32, tip - UP * 0.02, 0.04, "iron")
    add_cube(det, name + "_hook", tip + UP * 0.03, EYE, (0.07, 0.07, 0.07), "iron")
    ml.lantern(shell, name, tip - UP * drop, size=size, metal=metal, chain_to=tip)
    return tip


def leaning_pole(bone, name, foot, top, d=0.07, region="wood_dark", wrap=None, head=None, solid=False):
    """A pole / spear / staff leaning from foot to top; wrap: a leather grip region near the middle; head: a steel
    spear head region at the top."""
    foot, top = v3(*foot), v3(*top)
    beam(bone, name, foot, top, d, {"all": region, "+1": "end_grain", "-1": "end_grain"})
    dd = norm(top - foot)
    L = np.linalg.norm(top - foot)
    if wrap:
        beam(bone, name + "_wrap", foot + dd * L * 0.45, foot + dd * L * 0.62, d * 1.35, wrap)
    if head:
        beam(bone, name + "_head", top - dd * 0.02, top + dd * 0.3, d * 1.6, head, width=d * 0.4)
    if solid:
        ml.collide_segment(foot, top, d, segs=2)


def guy(bone, name, top, ground, sag=0.05, d=0.06, peg_region="wood_dark"):
    """A guy rope from a post top to a wooden peg in the ground (tentlib.peg with a region of the merchant atlas)."""
    ml.rope(bone, name, top, ground, d=d, sag=sag, segs=2)
    ml.tl.peg(bone, name + "_peg", ground, top, region=peg_region)
