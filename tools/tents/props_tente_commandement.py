"""Painters of the military command tent's own atlas regions (tente_commandement, camp militaire 1.24.0).

Every painter(img) paints a PIL RGBA image of its region's size (merchantlib.Atlas.add): the mottled olive canvas
of the roof (camo bands at its ends and along the eave), the walls (vertical folds), the gable (cut out above the
roof profile), the dagged beige-and-olive camo valances, the camo curtains, the green banner (gold border, pointed
bottom, crossed swords in a laurel wreath), the plain olive swallow-tailed flag, the red ornate carpet, the map,
parchment, crates marked with crossed swords, the knight's helmet, book spines, quill, chest and riveted iron bands.
Nothing here edits the shared libraries; it only uses their colour helpers.
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from galley_texture import fine_wood, polished_metal  # noqa: E402

OLIVE = np.array((68, 82, 40), float)
OLIVE_D = np.array((54, 66, 30), float)
OLIVE_L = np.array((84, 98, 48), float)
CAMO = [np.array(c, float) for c in ((66, 76, 32), (104, 106, 48), (156, 136, 76), (200, 176, 110))]
GOLD = (222, 176, 64)
GOLD_D = (136, 94, 26)
GREEN = np.array((50, 78, 34), float)
GREEN_D = np.array((30, 50, 20), float)
RED = np.array((128, 28, 24), float)
STEEL = [(0.0, (70, 72, 78)), (0.45, (138, 142, 150)), (0.8, (196, 200, 206)), (1.0, (238, 240, 244))]


# ---------------------------------------------------------------- numpy helpers
def vnoise(w, h, cell, rng):
    """Smooth value noise in [0, 1] of size h x w, features about `cell` px."""
    gw, gh = int(w / cell) + 3, int(h / cell) + 3
    g = rng.random((gh, gw))
    ys, xs = np.arange(h) / cell, np.arange(w) / cell
    y0, x0 = ys.astype(int), xs.astype(int)
    fy, fx = (ys - y0)[:, None], (xs - x0)[None, :]
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a, b = g[y0][:, x0], g[y0][:, x0 + 1]
    c, d = g[y0 + 1][:, x0], g[y0 + 1][:, x0 + 1]
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy


def weave(arr, amount=0.035):
    """A fine checker weave over an h x w x 3 array."""
    h, w = arr.shape[:2]
    k = 1.0 + amount * np.where((np.arange(h)[:, None] + np.arange(w)[None, :]) % 2 == 0, 1.0, -1.0)
    return arr * k[:, :, None]


def olive(w, h, rng):
    """Mottled olive canvas: darker and lighter patches, a weave, a little per-pixel noise."""
    n = 0.55 * vnoise(w, h, 9, rng) + 0.3 * vnoise(w, h, 4, rng) + 0.15 * rng.random((h, w))
    arr = np.where((n < 0.38)[:, :, None], OLIVE_D, np.where((n > 0.66)[:, :, None], OLIVE_L, OLIVE))
    arr = arr * (0.95 + 0.1 * n)[:, :, None]
    arr = arr + rng.integers(-4, 5, (h, w, 1))
    return weave(arr)


def camo(w, h, rng, block=3, beige=0.0):
    """Blocky, stepped tan / khaki / olive camouflage (flat pixel blocks of `block` px, the picture's "digital" camo);
    beige > 0 shifts it towards the tans."""
    n = 0.62 * vnoise(w, h, 2.6 * block, rng) + 0.38 * vnoise(w, h, 1.3 * block, rng) + beige
    n = n[::block, ::block].repeat(block, 0).repeat(block, 1)[:h, :w]
    arr = np.select([(n < 0.36)[:, :, None], (n < 0.5)[:, :, None], (n < 0.64)[:, :, None]], CAMO[:3], CAMO[3])
    arr = arr + rng.integers(-3, 4, (h, w, 1))
    return weave(arr, 0.025)


def jag(n, block, amp, rng):
    """A stepped edge offset: one random value in {0, block, ..., amp} per `block` px, length n."""
    steps = rng.integers(0, amp // block + 1, n // block + 2) * block
    return steps.repeat(block)[:n]


def put(img, arr, alpha=None):
    """Writes an h x w x 3 array (and an optional h x w alpha mask) into the PIL image."""
    from PIL import Image
    a = np.clip(arr, 0, 255).astype(np.uint8)
    al = np.full(a.shape[:2], 255, np.uint8) if alpha is None else np.clip(alpha, 0, 255).astype(np.uint8)
    img.paste(Image.fromarray(np.dstack([a, al]), "RGBA"), (0, 0))


# ---------------------------------------------------------------- canvas
def roof_painter(seed, rafters_s, end_band=14, eave_band=16):
    """The roof slopes (u along the ridge from the front, v from the ridge down to the eave): mottled olive, seams
    running down the slope, darker folds in the sag between the rafters (at u fractions rafters_s), lighter over
    the rafters, beige-and-olive camo bands at the two ends and along the eave."""
    def paint(img):
        rng = np.random.default_rng(seed)
        w, h = img.size
        arr = olive(w, h, rng)
        u = (np.arange(w) + 0.5) / w
        v = (np.arange(h) + 0.5) / h
        # sag shading: lighter on the rafters, darker in the middle of each bay (strongest mid-slope)
        bayk = np.zeros(w)
        for a, b in zip(rafters_s[:-1], rafters_s[1:]):
            m = (u >= a) & (u <= b)
            bayk[m] = np.sin(np.pi * (u[m] - a) / (b - a))
        mid = np.sin(np.pi * v)
        arr *= (1.08 - 0.22 * bayk[None, :] * (0.4 + 0.6 * mid[:, None]))[:, :, None]
        # folds: dark streaks fanning down from the rafters into the sag
        for a in rafters_s:
            for k, du in enumerate((-0.05, -0.025, 0.025, 0.05)):
                for y in range(h):
                    x = int((a + du * (0.3 + 1.2 * v[y]) * (1 + 0.15 * k)) * w)
                    if 0 <= x < w - 2:
                        arr[y, x] *= 0.78
                        arr[y, x + 1] *= 0.9
                        arr[y, x + 2] *= 1.08
        # seams down the slope, every ~40 px
        for x in range(20, w, 40):
            arr[:, x] *= 0.82
            arr[:, (x + 2) % w] *= 0.88
        # camo bands: ends and eave, a dark line on their inner edge
        band = camo(w, h, rng, block=4, beige=0.05)
        m = np.zeros((h, w), bool)
        jf, jb, je = jag(h, 4, 12, rng), jag(h, 4, 12, rng), jag(w, 4, 8, rng)
        for y in range(h):
            m[y, :end_band - 6 + jf[y]] = True
            m[y, w - end_band + 6 - jb[y]:] = True
        for x in range(w):
            m[h - eave_band + 2 - je[x]:, x] = True
        arr = np.where(m[:, :, None], band, arr)
        arr[:2, :] *= 0.75   # the ridge
        put(img, arr)
    return paint


def wall_painter(seed, folds=12):
    """The canvas walls (u along the wall, v down): mottled olive, soft vertical folds, a shadow under the eave,
    a dirty hem at the bottom."""
    def paint(img):
        rng = np.random.default_rng(seed)
        w, h = img.size
        arr = olive(w, h, rng)
        arr = arr * 0.45 + OLIVE * (0.92 + 0.16 * vnoise(w, h, 14, rng))[:, :, None] * 0.55   # calmer mottling than the roof
        x = np.arange(w)
        ph = rng.random() * 6
        f = np.sin(2 * np.pi * x * folds / w + ph) + 0.4 * np.sin(2 * np.pi * x * folds * 2.3 / w)
        arr *= (1.0 + 0.07 * f)[None, :, None]
        y = (np.arange(h) + 0.5) / h
        arr *= (0.86 + 0.14 * np.clip(y * 6, 0, 1))[:, None, None]
        dirt = np.clip((y - 0.86) / 0.14, 0, 1)
        arr = arr * (1 - 0.45 * dirt[:, None, None]) + np.array((90, 70, 40)) * 0.45 * dirt[:, None, None]
        for xs in range(w // 6, w, w // 3):
            arr[:, xs] *= 0.84
        put(img, arr)
    return paint


def gable_painter(seed, half_w, y0, y1, roof_y):
    """A gable end (u from -half_w to +half_w, v from y1 down to y0): mottled olive, cut out above roof_y(|x|) - a
    hair, a dark hem and a camo band under the slope."""
    def paint(img):
        rng = np.random.default_rng(seed)
        w, h = img.size
        arr = olive(w, h, rng)
        band = camo(w, h, rng, block=4, beige=0.05)
        jg = jag(w, 4, 8, rng)
        alpha = np.full((h, w), 255.0)
        for x in range(w):
            X = -half_w + 2 * half_w * (x + 0.5) / w
            top = roof_y(abs(X)) - 0.02
            for y in range(h):
                Y = y1 - (y1 - y0) * (y + 0.5) / h
                d = (top - Y) / (y1 - y0) * h   # px under the slope
                if d < 0:
                    alpha[y, x] = 0
                elif d < 1.5:
                    arr[y, x] *= 0.6
                elif d < 9 + jg[x]:
                    arr[y, x] = band[y, x]
        arr[h - 3:, :] *= 0.8
        put(img, arr, alpha)
    return paint


def dag_painter(seed, teeth, solid=0.45, beige=0.0):
    """A dagged valance band: camo cloth, a hem at the top, zigzag teeth along the bottom (cut-out), a dark edge."""
    def paint(img):
        rng = np.random.default_rng(seed)
        w, h = img.size
        arr = camo(w, h, rng, beige=beige)
        alpha = np.full((h, w), 255.0)
        tw = w / teeth
        s = int(h * solid)
        for x in range(w):
            lx = (x % tw) / tw
            tri = 1.0 - abs(2.0 * lx - 1.0)
            bottom = int(round(s + (h - 1 - s) * tri))
            alpha[bottom + 1:, x] = 0
            arr[max(0, bottom - 1):bottom + 1, x] *= 0.62
        arr[:2, :] = arr[:2, :] * 0.55 + OLIVE_D * 0.45
        arr[2, :] *= 0.85
        put(img, arr, alpha)
    return paint


def curtain_painter(seed, beige=0.12):
    """A tied-back curtain (u across, v down): beige camo, vertical folds, darker edges."""
    def paint(img):
        rng = np.random.default_rng(seed)
        w, h = img.size
        arr = camo(w, h, rng, beige=beige)
        x = np.arange(w)
        arr *= (1.0 + 0.12 * np.sin(2 * np.pi * x * 4 / w))[None, :, None]
        arr[:, :2] *= 0.7
        arr[:, w - 2:] *= 0.7
        arr[:3, :] = arr[:3, :] * 0.5 + OLIVE_D * 0.5
        put(img, arr)
    return paint


# ---------------------------------------------------------------- banner, flag, carpet
def _laurel_swords(w, h, scale=4):
    """Gold crossed swords (points up) in a gold laurel wreath, on transparency, w x h px (drawn big, shrunk)."""
    from PIL import Image, ImageDraw
    W, H = w * scale, h * scale
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy, r = W / 2, H * 0.52, min(W, H) * 0.4
    gold, gold_d, gold_l = GOLD + (255,), GOLD_D + (255,), (250, 222, 140, 255)
    blade, blade_d = (232, 226, 200, 255), (150, 140, 110, 255)
    # the wreath: two laurel branches curving up the sides from a tie at the bottom, open at the top: a thin stem and
    # pairs of pointed leaves along it, each leaf an ellipse turned along the stem
    lw = max(2, int(r * 0.05))
    for side in (-1, 1):
        a0, a1 = math.radians(-80), math.radians(62)
        n = 9
        pts = [(cx + side * r * math.cos(a0 + (a1 - a0) * k / 24), cy - r * math.sin(a0 + (a1 - a0) * k / 24)) for k in range(25)]
        d.line(pts, fill=gold_d, width=lw)
        for k in range(n):
            a = a0 + (a1 - a0) * (k + 0.6) / n
            px, py = cx + side * r * math.cos(a), cy - r * math.sin(a)
            tx, ty = -side * math.sin(a), -math.cos(a)          # tangent, going up the branch
            for sgn in (-1, 1):                                  # a leaf outside and a leaf inside the stem
                nx, ny = side * math.cos(a) * sgn, -math.sin(a) * sgn
                L, Wd = r * 0.2, r * 0.075
                ox, oy = px + nx * L * 0.45 + tx * L * 0.25, py + ny * L * 0.45 + ty * L * 0.25
                ang = math.atan2(ny * 0.8 + ty * 0.6, nx * 0.8 + tx * 0.6)
                poly = []
                for j in range(10):
                    q = 2 * math.pi * j / 10
                    ex, ey = math.cos(q) * L * 0.5, math.sin(q) * Wd
                    poly.append((ox + ex * math.cos(ang) - ey * math.sin(ang), oy + ex * math.sin(ang) + ey * math.cos(ang)))
                d.polygon(poly, fill=gold if sgn > 0 else gold_l, outline=gold_d)
    d.ellipse([cx - r * 0.1, cy + r * 0.9, cx + r * 0.1, cy + r * 1.04], fill=gold, outline=gold_d)
    # the crossed swords
    bw = max(3, int(r * 0.13))
    for sgn in (-1, 1):
        tip = (cx + sgn * r * 0.62, cy - r * 0.78)
        hilt = (cx - sgn * r * 0.42, cy + r * 0.5)
        d.line([tip, hilt], fill=blade_d, width=bw + 4)
        d.line([tip, hilt], fill=blade, width=bw)
        # the fuller
        d.line([(tip[0] * 0.8 + hilt[0] * 0.2, tip[1] * 0.8 + hilt[1] * 0.2), hilt], fill=(200, 192, 160, 255), width=max(1, bw // 3))
        # crossguard perpendicular to the blade near the hilt
        dx, dy = tip[0] - hilt[0], tip[1] - hilt[1]
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        gx, gy = hilt[0] + ux * r * 0.12, hilt[1] + uy * r * 0.12
        px_, py_ = -uy * r * 0.24, ux * r * 0.24
        d.line([(gx - px_, gy - py_), (gx + px_, gy + py_)], fill=gold_d, width=bw + 2)
        d.line([(gx - px_, gy - py_), (gx + px_, gy + py_)], fill=gold, width=bw - 1)
        ex, ey = hilt[0] - ux * r * 0.2, hilt[1] - uy * r * 0.2
        d.line([hilt, (ex, ey)], fill=(110, 70, 34, 255), width=bw)
        d.ellipse([ex - bw, ey - bw, ex + bw, ey + bw], fill=gold_l)
    return im.resize((w, h), Image.LANCZOS)


def banner_painter(seed):
    """The green banner: woven green, a gold border and a dark inner line, a pointed (V) bottom cut out, the gold
    crossed swords in a laurel wreath."""
    def paint(img):
        rng = np.random.default_rng(seed)
        w, h = img.size
        n = vnoise(w, h, 7, rng)
        arr = GREEN * (0.9 + 0.2 * n)[:, :, None] + rng.integers(-3, 4, (h, w, 1))
        arr = weave(arr)
        alpha = np.full((h, w), 255.0)
        body = int(h * 0.74)
        gold = np.array(GOLD, float)
        for y in range(h):
            for x in range(w):
                dx = abs(x - (w - 1) / 2)
                if y >= body:
                    half = (w / 2) * (1 - (y - body) / (h - body))
                    if dx > half:
                        alpha[y, x] = 0
                    elif dx > half - 3.2:
                        arr[y, x] = gold * (0.92 + 0.12 * n[y, x])
                    elif dx > half - 4.6:
                        arr[y, x] = GREEN_D
                    continue
                if x < 3 or x >= w - 3 or y < 3:
                    arr[y, x] = gold * (0.92 + 0.12 * n[y, x])
                elif x < 5 or x >= w - 5 or y < 5:
                    arr[y, x] = GREEN_D
        put(img, arr, alpha)
        em = _laurel_swords(w - 12, w - 12)
        img.alpha_composite(em, (6, int(h * 0.2)))
    return paint


def flag_painter(seed):
    """The small olive swallow-tailed flag (no emblem), a darker hoist and hem."""
    def paint(img):
        rng = np.random.default_rng(seed)
        w, h = img.size
        arr = olive(w, h, rng) * 0.92
        alpha = np.full((h, w), 255.0)
        for y in range(h):
            for x in range(w):
                if x > w * 0.62 and abs(y - (h - 1) / 2) < (x - w * 0.62) * (h / 2) / (w * 0.38):
                    alpha[y, x] = 0
        arr[:, :3] *= 0.7
        arr[:2, :] *= 0.8
        arr[h - 2:, :] *= 0.8
        for x in range(8, w, 11):
            arr[:, x] *= 0.86
        put(img, arr, alpha)
    return paint


def carpet_painter(seed):
    """The red ornate carpet (u across x, v along z from the back): a deep red field, a beige border band with a red
    step pattern, gold lines, a lozenge medallion and corner ornaments, a little wear."""
    def paint(img):
        rng = np.random.default_rng(seed)
        w, h = img.size
        n = vnoise(w, h, 6, rng)
        arr = RED * (0.88 + 0.22 * n)[:, :, None] + rng.integers(-4, 5, (h, w, 1))
        arr = weave(arr, 0.05)
        beige, gold, dark = np.array((214, 190, 140), float), np.array(GOLD, float), np.array((70, 14, 12), float)
        for y in range(h):
            for x in range(w):
                e = min(x, y, w - 1 - x, h - 1 - y)
                if e < 2:
                    arr[y, x] = dark
                elif e < 10:
                    # the beige band with a red stepped meander
                    along = (x if min(y, h - 1 - y) <= min(x, w - 1 - x) else y)
                    k = along % 8
                    depth = e - 2
                    step = (k < 4 and depth in (2, 3, 4)) or (k >= 4 and depth in (3, 4, 5)) or (k in (0, 4) and 2 <= depth <= 5)
                    arr[y, x] = RED * 1.05 if step else beige * (0.92 + 0.12 * n[y, x])
                elif e in (10, 11):
                    arr[y, x] = gold * 0.95
                elif e in (15,):
                    arr[y, x] = dark * 1.4
        cx, cy = (w - 1) / 2, (h - 1) / 2
        for y in range(h):
            for x in range(w):
                dd = abs(x - cx) / (w * 0.26) + abs(y - cy) / (h * 0.24)
                if dd < 0.08:
                    arr[y, x] = gold
                elif dd < 0.55:
                    arr[y, x] = RED * 1.25 if (x + y) % 4 else gold * 0.9
                elif dd < 0.66:
                    arr[y, x] = beige
                elif dd < 0.74:
                    arr[y, x] = gold * 0.9
                # corner ornaments
                for qx, qy in ((20, 20), (w - 21, 20), (20, h - 21), (w - 21, h - 21)):
                    q = abs(x - qx) + abs(y - qy)
                    if q < 4:
                        arr[y, x] = beige if q < 2 else gold * 0.9
        put(img, arr)
    return paint


# ---------------------------------------------------------------- small things
def map_painter(seed):
    """A campaign map: parchment, a blue sea, green and tan lands, a coast line, red routes, town marks, a border."""
    def paint(img):
        rng = np.random.default_rng(seed)
        w, h = img.size
        n = 0.7 * vnoise(w, h, 10, rng) + 0.3 * vnoise(w, h, 4, rng)
        parch = np.array((226, 206, 158), float)
        arr = np.where((n < 0.42)[:, :, None], np.array((112, 158, 184), float),
                       np.where((n < 0.6)[:, :, None], np.array((150, 172, 96), float), np.array((196, 176, 118), float)))
        coast = (np.abs(n - 0.42) < 0.018)
        arr[coast] = (90, 70, 40)
        arr = arr * 0.85 + parch * 0.15 + rng.integers(-4, 5, (h, w, 1))
        r = random.Random(seed)
        for _ in range(3):
            x, y = r.randint(6, w - 7), r.randint(6, h - 7)
            for k in range(14):
                x = min(w - 4, max(3, x + r.choice((-1, 0, 1, 1))))
                y = min(h - 4, max(3, y + r.choice((-1, 0, 1))))
                if k % 3 != 2:
                    arr[y, x] = (170, 40, 30)
        for _ in range(6):
            x, y = r.randint(5, w - 6), r.randint(5, h - 6)
            arr[y:y + 2, x:x + 2] = (60, 40, 24)
        arr[:2, :] = arr[h - 2:, :] = (120, 90, 50)
        arr[:, :2] = arr[:, w - 2:] = (120, 90, 50)
        put(img, arr)
    return paint


def parch_painter(seed):
    def paint(img):
        rng = np.random.default_rng(seed)
        w, h = img.size
        arr = np.array((228, 210, 166), float) * (0.92 + 0.12 * vnoise(w, h, 4, rng))[:, :, None]
        for y in range(2, h, 3):
            arr[y, 2:w - 2] *= 0.9
        put(img, arr)
    return paint


def crate_x_painter(seed):
    """A crate side: planks, a dark frame, iron corners, crossed swords painted in beige."""
    def paint(img):
        from PIL import ImageDraw
        r = random.Random(seed)
        w, h = img.size
        fine_wood(img, (0, 0, w, h), (150, 104, 58), (78, 50, 24), 8, r, joints=False, knots=0.2, grain=0.1, shade=0.06)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, w - 1, h - 1], outline=(70, 46, 22, 255), width=3)
        for (x, y) in ((0, 0), (w - 6, 0), (0, h - 6), (w - 6, h - 6)):
            d.rectangle([x, y, x + 5, y + 5], fill=(128, 128, 134, 255))
            d.point([(x + 2, y + 2), (x + 3, y + 3)], fill=(196, 196, 200, 255))
        for a, b in (((8, 7), (24, 24)), ((24, 7), (8, 24))):
            d.line([a, b], fill=(212, 196, 150, 255), width=2)
        for (x, y) in ((11, 20), (21, 20)):
            d.line([(x - 2, y - 2), (x + 2, y + 2)][::1], fill=(196, 172, 110, 255), width=1)
        d.line([(12, 21), (9, 24)], fill=(196, 172, 110, 255), width=2)
        d.line([(20, 21), (23, 24)], fill=(196, 172, 110, 255), width=2)
    return paint


def helmet_painter(seed):
    """A knight's helm: polished steel, a dark eye slit, breathing holes on the right, rivets, a central ridge."""
    def paint(img):
        from PIL import ImageDraw
        r = random.Random(seed)
        w, h = img.size
        polished_metal(img, (0, 0, w, h), STEEL, r, fx=0.35, fy=0.3)
        d = ImageDraw.Draw(img)
        d.rectangle([3, 11, w - 4, 13], fill=(26, 26, 30, 255))
        d.line([(3, 14), (w - 4, 14)], fill=(210, 212, 218, 255))
        d.line([(w // 2, 0), (w // 2, h - 1)], fill=(220, 222, 228, 255))
        for y in (18, 21, 24):
            for x in range(w // 2 + 3, w - 4, 3):
                d.point((x, y), fill=(30, 30, 34, 255))
        for x in range(2, w, 5):
            d.point((x, h - 3), fill=(230, 232, 236, 255))
            d.point((x, 2), fill=(230, 232, 236, 255))
    return paint


def books_painter(seed):
    """Book spines on three shelves."""
    def paint(img):
        r = random.Random(seed)
        w, h = img.size
        px = img.load()
        cols = [(130, 32, 28), (40, 60, 120), (44, 90, 48), (110, 72, 36), (60, 40, 30), (150, 120, 60), (90, 30, 60)]
        rows = 3
        rh = h // rows
        for k in range(rows):
            x = 0
            while x < w:
                bw = r.choice((2, 2, 3, 3, 4))
                c = r.choice(cols)
                top = k * rh + r.randint(1, 3)
                for xx in range(x, min(w, x + bw)):
                    for y in range(k * rh, (k + 1) * rh):
                        if y < top:
                            px[xx, y] = (40, 26, 14, 255)
                        elif y >= (k + 1) * rh - 2:
                            px[xx, y] = (92, 62, 32, 255)
                        else:
                            kk = 1.15 if xx == x else (0.8 if xx == x + bw - 1 else 1.0)
                            cc = tuple(max(0, min(255, int(v * kk))) for v in c)
                            if y in (top + 2, (k + 1) * rh - 5):
                                cc = (200, 170, 80)
                            px[xx, y] = cc + (255,)
                x += bw
    return paint


def quill_painter(seed):
    """A white quill feather on transparency (the shaft from the bottom left)."""
    def paint(img):
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                t = y / (h - 1)
                cx = w * 0.5 + (0.5 - t) * w * 0.15
                half = w * 0.36 * math.sin(math.pi * min(1.0, (1 - t) * 1.25)) if t > 0.05 else 0
                if abs(x - cx) < 0.7 and t > 0.0:
                    px[x, y] = (150, 140, 120, 255)
                elif abs(x - cx) < half and t < 0.8:
                    k = 0.9 + 0.1 * ((x + y) % 3 == 0)
                    px[x, y] = (int(238 * k), int(234 * k), int(224 * k), 255)
    return paint


def chest_painter(seed):
    """A chest side: dark planks, an iron rim and two iron bands with rivets, a gold lock plate."""
    def paint(img):
        from PIL import ImageDraw
        r = random.Random(seed)
        w, h = img.size
        fine_wood(img, (0, 0, w, h), (108, 70, 38), (52, 32, 16), 8, r, joints=False, knots=0.15, grain=0.1, shade=0.06)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, w - 1, h - 1], outline=(70, 70, 76, 255), width=2)
        for x in (7, w - 9):
            d.rectangle([x, 0, x + 2, h - 1], fill=(86, 86, 92, 255))
            for y in range(3, h, 6):
                d.point((x + 1, y), fill=(190, 190, 196, 255))
        d.rectangle([w // 2 - 3, 2, w // 2 + 2, 9], fill=GOLD + (255,), outline=GOLD_D + (255,))
        d.point((w // 2, 6), fill=(30, 20, 10, 255))
    return paint


def band_painter(seed):
    """Riveted grey iron (the posts' bands and plates)."""
    def paint(img):
        rng = np.random.default_rng(seed)
        w, h = img.size
        arr = np.array((132, 134, 140), float) * (0.9 + 0.16 * vnoise(w, h, 3, rng))[:, :, None]
        arr[:2, :] *= 1.18
        arr[h - 2:, :] *= 0.62
        for x in range(3, w, 8):
            arr[h // 2 - 1:h // 2 + 1, x:x + 2] = (210, 210, 214)
            arr[h // 2 + 1, x:x + 2] = (60, 60, 66)
        put(img, arr)
    return paint


def stone_painter(seed):
    """A grey anchor stone block (cobbled)."""
    def paint(img):
        rng = np.random.default_rng(seed)
        w, h = img.size
        n = vnoise(w, h, 4, rng)
        arr = np.array((128, 126, 122), float) * (0.78 + 0.34 * n)[:, :, None] + rng.integers(-6, 7, (h, w, 1))
        cracks = np.abs(vnoise(w, h, 5, rng) - 0.5) < 0.03
        arr[cracks] *= 0.6
        put(img, arr)
    return paint


def icon(path):
    """16x16 item icon: the olive marquee from the front, beige camo edges, the dagged valance, the dark entrance,
    the green banner with its gold emblem on the gable, the flag on top."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    olive, olive_d, beige, wood = (86, 96, 42, 255), (58, 68, 28, 255), (196, 178, 118, 255), (104, 70, 38, 255)
    green, gold, gold_d = (50, 78, 34, 255), (222, 176, 64, 255), (136, 94, 26, 255)
    for y in range(3, 10):          # the gable roof
        half = 0.6 + (y - 3) * 1.12
        for x in range(16):
            d = abs(x - 7.5)
            if d <= half:
                p[x, y] = beige if half - d < 1.2 else olive
    for x in range(0, 16):          # the valance
        p[x, 9] = beige if (x // 2) % 2 == 0 else olive_d
        if x % 2 == 0:
            p[x, 10] = beige
    for y in range(10, 15):         # the walls and the entrance
        for x in range(1, 15):
            if y > 10 or x % 2 == 1:
                p[x, y] = olive if not (5 <= x <= 10 and y >= 11) else (40, 30, 18, 255)
        for x in (1, 14, 5, 10):
            p[x, y] = wood
    for y in range(4, 9):           # the banner: green, a gold rod, a gold emblem, a pointed bottom
        for x in range(6, 10):
            p[x, y] = green
    for x in range(5, 11):
        p[x, 4] = gold_d
    p[7, 9] = p[8, 9] = green
    p[7, 6] = p[8, 7] = gold
    p[8, 6] = p[7, 7] = gold
    for y in range(0, 4):           # the pole and the flag
        p[7, y] = wood
    p[8, 0] = p[9, 0] = p[10, 1] = p[8, 1] = p[9, 1] = olive_d
    for x in range(1, 15):
        p[x, 15] = (70, 56, 34, 255)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
