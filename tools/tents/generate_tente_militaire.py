#!/usr/bin/env python3
"""tente_militaire — Tente militaire / Military Tent (1.25.0, camp militaire; reference S/ref/tente_militaire_ref.png).

An olive-green ridge tent (about 6.3 blocks wide x 7.9 long, ridge at 4.7), the ridge running front to back, the open
entrance under the front gable (+z, towards the player who placed it): two sagging roof slopes with folds, low canvas
side walls flaring out at the foot, a small window with a wooden lattice and a rolled flap above it in the left wall,
the closed back wall and gable; thick dark posts with grey riveted iron bands at the corners and both sides of the
entrance, the ridge-end posts sticking out above the roof (cross pieces, iron bands), beige twisted guy ropes (slight
sag) to wooden pegs with iron caps; the front: two canvas curtains pulled back into folds and tied, edged in beige,
draping in a curve from under the ridge, a green banner (gold border, pointed bottom, a gold sword point down in a
laurel wreath) hanging under the front ridge, a glowing lantern hanging in the entrance. Inside: a military bed (wood
frame, green blanket, pillow) at the back right, a table with a map and a stool on the left, a crate at the back left,
a crate behind the table, a small green rug with a beige border at the entrance. Outside: a stack of six burlap sacks
at the front left, an iron-banded crate with a coil of rope on top, a short post on a stone base on the right.

Mod blocks (tentlib.Decor, stand-in boxes when the mod is missing): furnish:spruce_crate (back left, alt
minecraft:barrel), furnish:spruce_stool (at the table). Everything else is the model's own cubes.

Usage:  python3 tools/tents/generate_tente_militaire.py      (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_militaire.json, models/entity + blockbench/tente_militaire.bbmodel,
textures/entity/tente_militaire.png, textures/item/tente_militaire.png, interiors/tente_militaire_decor.json.
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "merchant"))
sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402

NAME = "tente_militaire"
v3, norm, UP, EYE = ml.v3, ml.norm, ml.UP, ml.EYE
add_cube, beam, loft, box, collide = ml.add_cube, ml.beam, ml.loft, ml.box, ml.collide
ry, rx, rz = ml.ry, ml.rx, ml.rz

RIDGE_Y = 4.7          # the ridge (top of the canvas)
EAVE_Y = 2.0           # where the roof meets the side walls
HX = 3.05              # half width at the eaves
FOOT_X = 3.28          # half width at the foot of the side walls (they flare out)
HL = 3.7               # half length: the front gable at z = +HL, the back at -HL
OV = 0.28              # roof overhang beyond the gables
POST_X = 2.35          # the entrance posts
DOOR_X = 1.5           # half width of the entrance at the ground
OPEN_X = 1.75          # half width of the gable cloth's opening (the drapes come in to DOOR_X in front of it)
BANNER_Y = 4.24        # the cross beam carrying the banner, just under the front ridge-post block
NPC_SPOTS = ((-0.5, -2.7, 0.5, -1.7), (-0.5, -0.6, 0.5, 0.4))   # x0, z0, x1, z1: free 1 x 1 x 2.2 places for NPCs
WINDOW = (0.2, 1.4, 0.45, 1.6)     # z0, z1, y0, y1 of the window in the left wall

# ---------------------------------------------------------------- colours
OLIVE = (94, 96, 44)       # olive drab as in the picture (red ~ green, muted), not grass green
OLIVE_D = (74, 78, 35)
OLIVE_DD = (58, 62, 28)
OLIVE_L = (114, 113, 54)
BEIGE = (214, 196, 150)
BEIGE_D = (160, 140, 96)
GREEN_B = (40, 72, 38)       # banner / rug / blanket green
GREEN_BD = (24, 46, 24)
GOLD = (214, 168, 64)
GOLD_D = (138, 98, 30)


def _noise(w, h, seed, scale=8.0, octaves=3):
    """Smooth value noise in [0, 1] (w x h), tiling-free, from blurred random grids."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        s = max(1.0, scale / (2 ** o))
        gw, gh = int(w / s) + 2, int(h / s) + 2
        g = rng.random((gh, gw))
        ys, xs = np.arange(h) / s, np.arange(w) / s
        y0, x0 = np.floor(ys).astype(int), np.floor(xs).astype(int)
        fy, fx = (ys - y0)[:, None], (xs - x0)[None, :]
        fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
        a = g[y0][:, x0]
        b = g[y0][:, x0 + 1]
        c = g[y0 + 1][:, x0]
        d = g[y0 + 1][:, x0 + 1]
        out += amp * ((a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy)
        tot += amp
        amp *= 0.5
    return out / tot


def _put(img, arr, alpha=None):
    from PIL import Image
    a = np.clip(arr, 0, 255).astype(np.uint8)
    h, w = a.shape[:2]
    al = np.full((h, w), 255, np.uint8) if alpha is None else np.clip(alpha, 0, 255).astype(np.uint8)
    img.paste(Image.fromarray(np.dstack([a, al]), "RGBA"), (0, 0))


def _noise2(w, h, seed, sx, sy, octaves=3):
    """Value noise in [0, 1] (w x h) with different feature sizes along x (sx) and y (sy)."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        ax, ay = max(1.0, sx / (2 ** o)), max(1.0, sy / (2 ** o))
        gw, gh = int(w / ax) + 2, int(h / ay) + 2
        g = rng.random((gh, gw))
        ys, xs = np.arange(h) / ay, np.arange(w) / ax
        y0, x0 = np.floor(ys).astype(int), np.floor(xs).astype(int)
        fy, fx = (ys - y0)[:, None], (xs - x0)[None, :]
        fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
        out += amp * ((g[y0][:, x0] * (1 - fx) + g[y0][:, x0 + 1] * fx) * (1 - fy) + (g[y0 + 1][:, x0] * (1 - fx) + g[y0 + 1][:, x0 + 1] * fx) * fy)
        tot += amp
        amp *= 0.45
    return out / tot


def _olive(w, h, seed, folds=0, fold_dir="v", seams=0, along="u"):
    """Mottled olive canvas as in the picture: crisp blocky patches of four olive shades (pixel-art camouflage, the
    patches stretched along the cloth: u for the roof and walls, v for hanging cloth), a fine weave, fold shadows,
    seams."""
    sx, sy = (7.0, 3.0) if along == "u" else (3.0, 7.0)
    n = _noise2(w, h, seed, sx, sy)
    rng = np.random.default_rng(seed + 3)
    n = n + rng.uniform(-0.03, 0.03, n.shape)    # dithered patch edges (crisp texels, no blur)
    lv = np.digitize(n, [0.37, 0.48, 0.62])
    pal = np.array([OLIVE_DD, OLIVE_D, OLIVE, OLIVE_L], float)
    col = pal[lv]
    m = _noise(w, h, seed + 7, scale=3.0)
    col *= (0.95 + 0.1 * m)[..., None]
    yy, xx = np.mgrid[0:h, 0:w]
    col *= (1.0 + 0.025 * (((xx + yy) % 2) * 2 - 1))[..., None]
    col *= (1.0 + rng.integers(-4, 5, (h, w, 1)) / 100.0)
    if folds:
        coord = xx if fold_dir == "v" else yy
        span = w if fold_dir == "v" else h
        f = np.sin(coord / span * math.pi * 2 * folds + 0.6 + 0.5 * np.sin(coord * 0.37))
        col *= (1.0 + 0.12 * f - 0.16 * np.exp(-((f + 1.0) / 0.1) ** 2))[..., None]
    if seams:
        for k in range(1, seams + 1):
            s = int(k * (h if fold_dir == "v" else w) / (seams + 1))
            if fold_dir == "v":
                col[s, :, :] *= 0.8
                col[min(h - 1, s + 1), :, :] *= 1.06
            else:
                col[:, s, :] *= 0.8
                col[:, min(w - 1, s + 1), :] *= 1.06
    return col


def paint_roof(img):
    w, h = img.size
    col = _olive(w, h, 2401, folds=5, fold_dir="v", seams=2)
    # a darker band at the ridge and along the lower edge (wet, dirty)
    yy = np.arange(h)[:, None, None]
    col *= 1.0 - 0.18 * np.exp(-yy / 3.0) - 0.12 * np.exp(-(h - 1 - yy) / 4.0)
    _put(img, col)


def paint_wall(img):
    w, h = img.size
    col = _olive(w, h, 2402, folds=7, fold_dir="v")
    yy = np.arange(h)[:, None, None]
    col *= 1.0 - 0.25 * np.exp(-(h - 1 - yy) / 3.0) - 0.1 * np.exp(-yy / 2.0)   # muddy foot, shadow under the eave
    _put(img, col)


def paint_curtain(img):
    """The front curtains and swags: olive with deep folds (along v), a slightly darker hem; no beige (as in the
    picture: the drapes are plain olive, only the banner and the rug have beige borders)."""
    w, h = img.size
    col = _olive(w, h, 2403, folds=4, fold_dir="v", along="v") * 0.74    # the gable cloth, in the shade of the roof
    col[:, :1, :] *= 0.8
    col[:, w - 1:, :] *= 0.8
    _put(img, col)


def paint_drape(img):
    """The curtains pulled aside beside the entrance posts: olive, deep vertical folds, a darker hem."""
    w, h = img.size
    col = _olive(w, h, 2423, folds=4, fold_dir="v", along="v") * 0.92
    col[h - 3:, :, :] *= 0.75
    _put(img, col)


def paint_gable(img):
    """The back gable: an olive triangle (cut out above the roof line)."""
    w, h = img.size
    col = _olive(w, h, 2404, folds=4, fold_dir="v")
    yy, xx = np.mgrid[0:h, 0:w]
    inside = yy >= np.abs(xx - (w - 1) / 2) / ((w - 1) / 2) * (h - 1) - 0.5
    _put(img, col, np.where(inside, 255, 0))


def paint_banner(img):
    """Green banner as in the picture: a cream-gold border, a stepped (dagged) pointed bottom, a gold sword point down
    between two laurel branches that meet under its point."""
    w, h = img.size    # 64 x 112
    rng = np.random.default_rng(2405)
    n = _noise(w, h, 2415, scale=6.0)
    col = np.array(GREEN_B)[None, None, :] * (0.88 + 0.24 * n[..., None])
    col += rng.integers(-4, 5, (h, w, 1))
    yy, xx = np.mgrid[0:h, 0:w]
    body = h - 26
    dx = np.abs(xx - (w - 1) / 2)
    tip = body + np.floor((1 - dx / ((w - 1) / 2)) * 25 / 4.0) * 4.0 + 1      # stepped V (4 px steps)
    alpha = np.where(yy <= tip, 255, 0)
    dist_side = np.minimum(xx, w - 1 - xx)
    border = (dist_side < 4) | (yy < 4) | ((yy > body - 6) & (tip - yy < 5))
    trim = np.array((222, 198, 140))
    col[border] = trim * 1.0
    col[border & ((dist_side == 3) | (yy == 3))] = np.array((168, 140, 86)) * 1.0
    col[border] += rng.integers(-10, 9, (int(border.sum()), 1))
    from PIL import Image, ImageDraw
    em = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(em)
    cx = w / 2 - 0.5
    g, gd, gl = GOLD + (255,), GOLD_D + (255,), (240, 206, 120, 255)
    # laurel: two branches rising from a point under the sword, curving out and up, paired leaves along them
    for side in (-1, 1):
        pts = []
        for k in range(9):
            a = math.radians(-90 + k * 17.5)
            pts.append((cx + side * 15.5 * math.cos(a), 60 - 23 * math.sin(a)))
        d.line(pts, fill=gd, width=2)
        for k in range(2, len(pts), 1):
            x0, y0 = pts[k - 1]
            x1, y1 = pts[k]
            tx, ty = x1 - x0, y1 - y0
            L = math.hypot(tx, ty) or 1.0
            tx, ty = tx / L, ty / L
            for o in (-1, 1):            # a leaf on each side of the stem, pointing along it
                nx_, ny_ = -ty * o, tx * o
                lx, ly = x1 + nx_ * 3.2, y1 + ny_ * 3.2
                d.polygon([(lx - tx * 3.0, ly - ty * 3.0), (lx + nx_ * 1.7, ly + ny_ * 1.7), (lx + tx * 3.4, ly + ty * 3.4),
                           (lx - nx_ * 1.7, ly - ny_ * 1.7)], fill=gl, outline=g)
        tx_, ty_ = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]   # a leaf at the tip of the branch
        d.polygon([(pts[-1][0], pts[-1][1]), (pts[-1][0] + tx_ * 0.9 - 1.5, pts[-1][1] + ty_ * 0.9), (pts[-1][0] + tx_ * 1.6, pts[-1][1] + ty_ * 1.6),
                   (pts[-1][0] + tx_ * 0.9 + 1.5, pts[-1][1] + ty_ * 0.9)], fill=gl, outline=g)
    # sword, point down: pommel, grip, guard, blade with a fuller
    d.polygon([(cx, 9), (cx + 3, 13), (cx, 17), (cx - 3, 13)], fill=gl, outline=gd)
    d.rectangle([cx - 1.5, 17, cx + 1.5, 25], fill=g, outline=gd)
    d.rectangle([cx - 10, 25, cx + 10, 28], fill=gl, outline=gd)
    d.polygon([(cx - 3, 29), (cx + 3, 29), (cx + 3, 70), (cx, 77), (cx - 3, 70)], fill=gl, outline=gd)
    d.line([(cx, 30), (cx, 72)], fill=gd)
    ea = np.array(em).astype(float)
    m = ea[..., 3:4] / 255.0
    col = col * (1 - m) + ea[..., :3] * m
    _put(img, col, alpha)


def paint_rug(img):
    w, h = img.size
    rng = np.random.default_rng(2406)
    n = _noise(w, h, 2416, scale=5.0)
    col = np.array(GREEN_B)[None, None, :] * (0.85 + 0.25 * n[..., None]) + rng.integers(-4, 5, (h, w, 1))
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    col[(d >= 2) & (d < 6)] = np.array(BEIGE) * 1.0
    col[(d == 4)] = np.array(GOLD_D) * 1.0
    col[(d < 2)] = np.array(GREEN_BD) * 1.0
    col[(d == 9)] = np.array(BEIGE_D) * 1.0
    col += rng.integers(-5, 6, (h, w, 1))
    _put(img, col)


def paint_blanket(img):
    w, h = img.size
    rng = np.random.default_rng(2407)
    n = _noise(w, h, 2417, scale=5.0)
    col = np.array(GREEN_B)[None, None, :] * (0.95 + 0.3 * n[..., None]) * 1.15 + rng.integers(-5, 6, (h, w, 1))
    yy, xx = np.mgrid[0:h, 0:w]
    col[(yy % 12 == 2)] *= 0.7
    col[(xx < 2) | (xx > w - 3)] *= 0.75
    _put(img, col)


def paint_map(img):
    w, h = img.size
    rng = np.random.default_rng(2408)
    n = _noise(w, h, 2418, scale=6.0)
    col = np.array((222, 200, 150))[None, None, :] * (0.92 + 0.12 * n[..., None]) + rng.integers(-5, 6, (h, w, 1))
    land = _noise(w, h, 2428, scale=7.0) > 0.52
    col[land] = col[land] * 0.55 + np.array((96, 120, 60)) * 0.45
    yy, xx = np.mgrid[0:h, 0:w]
    col[(np.abs(yy - h * 0.5 - 4 * np.sin(xx / 4.0)) < 0.6)] = np.array((130, 70, 40)) * 1.0
    col[(np.abs(xx - w * 0.62 - 3 * np.sin(yy / 3.0)) < 0.6)] = np.array((60, 90, 140)) * 1.0
    col[(xx < 1) | (yy < 1) | (xx > w - 2) | (yy > h - 2)] = np.array((150, 118, 74)) * 1.0
    col[3:6, 4:7] = np.array((160, 30, 30))
    _put(img, col)


def paint_lattice(img):
    """The window: a dark opening behind a wooden lattice (3 x 3 panes) in a wooden frame."""
    w, h = img.size
    rng = np.random.default_rng(2409)
    col = np.zeros((h, w, 3)) + np.array((34, 28, 18)) + rng.integers(-3, 4, (h, w, 1))
    yy, xx = np.mgrid[0:h, 0:w]
    wood = np.array((150, 112, 62))
    bars = ((xx % 8) < 2) | ((yy % 8) < 2) | (xx >= w - 2) | (yy >= h - 2)
    col[bars] = wood * (0.85 + 0.25 * _noise(w, h, 2419, scale=3.0)[bars][:, None])
    col[bars & (((xx % 8) == 1) | ((yy % 8) == 1))] *= 0.78
    _put(img, col)


def paint_band(img):
    """Grey iron band with big square rivets."""
    w, h = img.size
    rng = np.random.default_rng(2410)
    col = np.zeros((h, w, 3)) + np.array((120, 122, 126)) + rng.integers(-8, 9, (h, w, 1))
    col[0, :] *= 1.2
    col[h - 1, :] *= 0.65
    for x0 in range(3, w, 10):
        col[2:h - 2, x0:x0 + 4] = np.array((70, 72, 76))
        col[2, x0:x0 + 4] = np.array((176, 178, 182))
        col[2:h - 2, x0] = np.array((160, 162, 166))
    _put(img, col)


def paint_post(img):
    """Thick dark weathered post wood, the grain along u."""
    w, h = img.size
    rng = np.random.default_rng(2411)
    n = _noise(w, h, 2421, scale=6.0)
    yy, xx = np.mgrid[0:h, 0:w]
    streak = np.sin(yy * 1.9 + 0.8 * np.sin(xx / 7.0)) * 0.5 + 0.5
    col = np.array((92, 60, 34))[None, None, :] * (0.72 + 0.28 * n[..., None] + 0.12 * streak[..., None]) + rng.integers(-5, 6, (h, w, 1))
    col[(yy % 5) == 0] *= 0.8
    _put(img, col)


def paint_ridge(img):
    """The light wooden ridge beam of the picture: pale weathered wood, the grain along u."""
    w, h = img.size
    rng = np.random.default_rng(2425)
    n = _noise(w, h, 2426, scale=5.0)
    yy, xx = np.mgrid[0:h, 0:w]
    streak = np.sin(yy * 2.1 + 0.9 * np.sin(xx / 6.0)) * 0.5 + 0.5
    col = np.array((162, 134, 90))[None, None, :] * (0.8 + 0.2 * n[..., None] + 0.08 * streak[..., None]) + rng.integers(-6, 7, (h, w, 1))
    col[(yy % 8) == 0] *= 0.82
    col[:, (xx[0] % 32) == 0] *= 0.7
    _put(img, col)


def paint_strap(img):
    """Dark olive canvas straps holding the roof to the ridge beam, with stitching."""
    w, h = img.size
    rng = np.random.default_rng(2427)
    col = np.zeros((h, w, 3)) + np.array((50, 56, 30)) + rng.integers(-5, 6, (h, w, 1))
    yy, xx = np.mgrid[0:h, 0:w]
    col[(xx == 1) | (xx == w - 2)] *= 1.3
    col[(yy % 4 == 0) & ((xx == 1) | (xx == w - 2))] *= 0.6
    _put(img, col)


def paint_burlap(img):
    """Burlap of a stuffed sack: coarse weave, lighter in the bulging middle, darker towards the seams."""
    w, h = img.size
    rng = np.random.default_rng(2412)
    n = _noise(w, h, 2422, scale=5.0)
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.maximum(np.abs(xx - (w - 1) / 2) / (w / 2), np.abs(yy - (h - 1) / 2) / (h / 2))
    col = np.array((182, 162, 120))[None, None, :] * (0.8 + 0.18 * n[..., None]) * (1.08 - 0.3 * r[..., None] ** 2.5)
    col *= (1.0 + 0.08 * (((xx // 2 + yy // 2) % 2) * 2 - 1))[..., None]
    col += rng.integers(-8, 9, (h, w, 1))
    _put(img, col)


def paint_valance(img):
    """The heavy swag along the front edge of the roof: olive folds, a lighter crest where the rolled cloth catches
    the light, a darker hem along a gently scalloped lower edge (cut out below)."""
    w, h = img.size
    col = _olive(w, h, 2414, folds=5, fold_dir="v")
    yy, xx = np.mgrid[0:h, 0:w]
    bottom = h - 1 - 2 * (1 - np.abs(np.sin(xx / w * math.pi * 4)))
    col *= (1.0 + 0.3 * np.exp(-((yy - h * 0.3) / (h * 0.14)) ** 2) - 0.42 * (yy / h) ** 2)[..., None]
    col[(yy > bottom - 2) & (yy <= bottom)] *= 0.55
    _put(img, col, np.where(yy <= bottom, 255, 0))


def _inside(painter, f=0.62):
    """The same cloth seen from inside the tent: darker and a little warmer (the picture's dim interior, lit by the
    lantern), alpha kept."""
    def paint(img):
        painter(img)
        a = np.array(img).astype(float)
        a[..., :3] *= np.array((f * 1.08, f, f * 0.86))
        _put(img, a[..., :3], a[..., 3])
    return paint


def loft_io(bone, name, P, nx, ny, region, region_in, th=0.03, overlap=0.004, ref=(0.0, 1.2, 0.0)):
    """tentlib.loft with the face that looks into the tent (towards ref) painted region_in, the outer one region."""
    ref = v3(*ref)
    for i in range(nx):
        for j in range(ny):
            s0, s1, t0, t1 = i / nx, (i + 1) / nx, j / ny, (j + 1) / ny
            a1, b1, a0, b0 = P(s0, t0), P(s1, t0), P(s0, t1), P(s1, t1)
            c = (a0 + a1 + b0 + b1) / 4
            u = ((b0 + b1) - (a0 + a1)) / 2
            L = np.linalg.norm(u)
            if L < 1e-5:
                u, L = v3(1, 0, 0), 1e-3
            u = u / L
            vp = ((a0 - a1) + (b0 - b1)) / 2
            H = np.linalg.norm(vp)
            if H < 1e-5:
                continue
            v = norm(vp - np.dot(vp, u) * u)
            n = np.cross(u, v)
            out = np.dot(n, c - ref) > 0
            regions = {"all": None, "+3": region if out else region_in, "-3": region_in if out else region}
            cube = add_cube(bone, "%s_%d_%d" % (name, i, j), c, np.column_stack([u, v, n]), (L + overlap, H + overlap, th), regions,
                            stretch=True, u_dir=u, v_dir=v)
            ml.tl.gn.set_sub(cube, (s0, t0, s1, t1))


def add_regions(atlas):
    atlas.add("mil_roof", 128, 64, paint_roof)
    atlas.add("mil_wall", 128, 32, paint_wall)
    atlas.add("mil_roof_in", 128, 64, _inside(paint_roof))
    atlas.add("mil_wall_in", 128, 32, _inside(paint_wall))
    atlas.add("mil_gable_in", 96, 48, _inside(paint_gable))
    atlas.add("mil_curtain", 48, 96, paint_curtain)
    atlas.add("mil_drape", 32, 64, paint_drape)
    atlas.add("mil_gable", 96, 48, paint_gable)
    atlas.add("mil_banner", 64, 112, paint_banner)
    atlas.add("mil_rug", 48, 64, paint_rug)
    atlas.add("mil_blanket", 32, 32, paint_blanket)
    atlas.add("mil_map", 32, 24, paint_map)
    atlas.add("mil_lattice", 32, 32, paint_lattice)
    atlas.add("mil_band", 32, 8, paint_band)
    atlas.add("mil_post", 64, 16, paint_post)
    atlas.add("mil_ridge", 64, 16, paint_ridge)
    atlas.add("mil_strap", 8, 16, paint_strap)
    atlas.add("mil_burlap", 32, 32, paint_burlap)
    atlas.add("mil_valance", 64, 24, paint_valance)


# ---------------------------------------------------------------- structure
def iron_post(sh, det, name, x, z, top, d=0.42, bands=(0.35, 1.3, None), cap=True, solid=True):
    """A thick dark post with grey riveted iron bands (the last band just under the top)."""
    beam(sh, name, (x, 0.0, z), (x, top, z), d, {"all": "mil_post", "+1": "end_grain", "-1": "end_grain"})
    for k, y in enumerate(bands):
        y = top - 0.32 if y is None else y
        box(sh if k == 0 else det, "%s_band_%d" % (name, k), (x - d / 2 - 0.025, y, z - d / 2 - 0.025), (x + d / 2 + 0.025, y + 0.16, z + d / 2 + 0.025),
            "mil_band", stretch=True)
    if cap:
        box(sh, name + "_cap", (x - d / 2 + 0.04, top, z - d / 2 + 0.04), (x + d / 2 - 0.04, top + 0.08, z + d / 2 - 0.04), "iron")
    if solid:
        collide((x - d / 2, 0.0, z - d / 2, x + d / 2, top, z + d / 2))


def roof(sh):
    """Two sagging slopes from the ridge to the eaves, folds running down the slope, the front edge drooping in a
    curve (the draped look of the picture)."""
    z0, z1 = -HL - OV, HL + OV
    for k, sx in enumerate((-1, 1)):
        def P(s, t, sx=sx):
            z = z0 + (z1 - z0) * s if sx < 0 else z1 - (z1 - z0) * s
            x = sx * (0.04 + (HX + 0.06) * t)
            y = RIDGE_Y - (RIDGE_Y - EAVE_Y) * t
            edge = max(0.0, abs(z) - (HL - 0.6)) / (OV + 0.6)          # 0 inside, 1 at the gable edge
            y -= 0.17 * math.sin(math.pi * t) * (1.0 - 0.6 * edge)      # the cloth bellies between the ridge and the eave
            y -= 0.07 * math.sin(math.pi * t) * abs(math.sin(z * 1.35))  # folds down the slope
            y -= 0.22 * edge * edge * math.sin(math.pi * min(1.0, t * 1.2))   # the edge droops at the gables
            return v3(x, y, z)
        loft_io(sh, "roof_%d" % k, P, 7, 4, "mil_roof", "mil_roof_in", th=0.04)
    # a canvas strip over the ridge pole
    beam(sh, "ridge_cap", (0, RIDGE_Y + 0.02, z0 + 0.05), (0, RIDGE_Y + 0.02, z1 - 0.05), 0.08, "mil_roof", width=0.3)


def side_walls(sh, det):
    """Low canvas walls from the eaves down to the ground, flaring out, folds; the window in the left wall."""
    for k, sx in enumerate((-1, 1)):
        def P(s, t, sx=sx):
            z = -HL + 2 * HL * s if sx < 0 else HL - 2 * HL * s
            x = sx * (HX + (FOOT_X - HX) * t * t + 0.05 * math.sin(math.pi * t))
            x += sx * 0.035 * math.sin(z * 2.3) * t
            return v3(x, EAVE_Y + 0.04 - (EAVE_Y + 0.04) * t, z)
        loft_io(sh, "wall_%d" % k, P, 6, 2, "mil_wall", "mil_wall_in", th=0.035)
        collide((min(sx * HX, sx * FOOT_X) - 0.05, 0.0, -HL, max(sx * HX, sx * FOOT_X) + 0.05, EAVE_Y, HL))
    # the window: dark opening, lattice, frame, and the rolled-up flap above it
    z0, z1, y0, y1 = WINDOW
    t0, t1 = 1 - y1 / (EAVE_Y + 0.04), 1 - y0 / (EAVE_Y + 0.04)
    xw = -(HX + (FOOT_X - HX) * ((t0 + t1) / 2) ** 2 + 0.05 * math.sin(math.pi * (t0 + t1) / 2)) - 0.04
    tilt = math.atan2(FOOT_X - HX, EAVE_Y) * 0.8
    R = rz(-tilt)
    zc, yc = (z0 + z1) / 2, (y0 + y1) / 2
    n = R @ v3(-1, 0, 0)
    axes = np.column_stack([R @ v3(0, 0, -1), R @ v3(0, 1, 0), n])
    add_cube(sh, "window_lattice", (xw, yc, zc), axes, (z1 - z0, y1 - y0, 0.04), {"all": "mil_post", "+3": "mil_lattice", "-3": "mil_lattice"},
             stretch=True, u_dir=v3(0, 0, -1), v_dir=-UP)
    fr = 0.08
    for j, (a, b) in enumerate((((z0 - fr, y1), (z1 + fr, y1)), ((z0 - fr, y0), (z1 + fr, y0)), ((z0, y0), (z0, y1)), ((z1, y0), (z1, y1)))):
        pa = v3(xw - 0.03, a[1], a[0])
        pb = v3(xw - 0.03, b[1], b[0])
        pa[0] -= (a[1] - yc) * math.tan(tilt) * -1
        pb[0] -= (b[1] - yc) * math.tan(tilt) * -1
        beam(det, "window_frame_%d" % j, pa, pb, 0.08, "mil_post", width=0.08, extend=0.04)
    # the awning: the canvas flap propped out over the window (sloping, sagging a little), its thick rolled hem,
    # two cheeks closing its sides, and a fold of canvas under the window (the sill)
    def A(s, t):
        return v3(xw + 0.06 - 0.62 * t, y1 + 0.34 - 0.26 * t - 0.05 * math.sin(math.pi * t) * math.sin(math.pi * s),
                  z0 - 0.22 + (z1 - z0 + 0.44) * s)
    loft(sh, "window_hood", A, 3, 2, "mil_wall", th=0.06)
    beam(sh, "window_roll", (xw - 0.58, y1 + 0.06, z0 - 0.24), (xw - 0.58, y1 + 0.06, z1 + 0.24), 0.11, "mil_wall", width=0.13)
    for j, z in enumerate((z0 - 0.2, z1 + 0.2)):
        add_cube(det, "window_cheek_%d" % j, v3(xw - 0.27, y1 + 0.14, z), rz(0.35), (0.5, 0.26, 0.04), "mil_wall", stretch=True)
    beam(det, "window_sill", (xw - 0.06, y0 - 0.06, z0 - 0.15), (xw - 0.06, y0 - 0.06, z1 + 0.15), 0.12, "mil_wall", width=0.16)


def gables(sh, det):
    """The closed back (wall + gable triangle) and the front: two curtains pulled back, tied, with a beige edging,
    draping from under the ridge in a curve over the entrance."""
    # back wall and gable
    def B(s, t):
        x = -HX + 2 * HX * s
        return v3(x, EAVE_Y + 0.02 - (EAVE_Y + 0.02) * t, -HL - 0.04 - 0.05 * math.sin(math.pi * t) + 0.03 * math.sin(x * 2.0))
    loft_io(sh, "back_wall", B, 4, 2, "mil_wall", "mil_wall_in", th=0.035)
    # the back gable: its outer face looks out (-z), the inner one (+z) is the darker inside
    gu, gup, gnorm = v3(-1, 0, 0), v3(0, 1, 0), v3(0, 0, -1)
    add_cube(sh, "back_gable", v3(0, (EAVE_Y + RIDGE_Y) / 2 - 0.02, -HL - 0.06), np.column_stack([gu, gup, gnorm]),
             (2 * HX + 0.1, RIDGE_Y - EAVE_Y + 0.02, 0.02), {"all": None, "+3": "mil_gable", "-3": "mil_gable_in"}, stretch=True,
             u_dir=gu, v_dir=-gup)
    collide((-HX, 0.0, -HL - 0.15, HX, EAVE_Y, -HL + 0.02))
    collide((-1.4, EAVE_Y, -HL - 0.15, 1.4, 3.3, -HL + 0.02))
    # the front gable cloth, in horizontal bands: from the outline of the tent (foot of the wall, eave, roof edge) in
    # to the opening, which has straight sides (x = +-OPEN_X) up to the swags, closes in a curve under the banner beam
    # and is shut above it (behind the beam and the banner)
    top_y = BANNER_Y - 0.02
    rows = (0.0, 1.0, 2.0, 2.7, 3.25, 3.7, top_y - 0.05, RIDGE_Y - 0.06)
    for k, sx in enumerate((-1, 1)):
        def P(a, b, sx=sx):
            q = (1.0 - b) * (len(rows) - 1)   # loft t runs down
            j = min(int(q), len(rows) - 2)
            y = rows[j] + (rows[j + 1] - rows[j]) * (q - j)
            if y <= EAVE_Y:
                xo = FOOT_X - (FOOT_X - HX) * (y / EAVE_Y)
            else:
                xo = HX * (RIDGE_Y - 0.06 - y) / (RIDGE_Y - 0.06 - EAVE_Y)
            if y <= 2.6:
                xi = OPEN_X
            elif y < top_y:
                xi = 0.3 + (OPEN_X - 0.3) * math.cos(math.pi / 2 * (y - 2.6) / (top_y - 2.6))
            else:
                xi = 0.0
            xi = max(0.0, min(xi, xo - 0.12))
            x = xo + (xi - xo) * a
            z = HL + 0.04 + 0.04 * a + 0.06 * math.sin(math.pi * a) + 0.05 * math.sin(a * math.pi * 3.0 + y * 0.9)
            return v3(sx * x, y, z)
        loft(sh, "curtain_%d" % k, P, 3, len(rows) - 1, "mil_curtain", th=0.035)
        collide((min(sx * DOOR_X, sx * HX) if sx > 0 else -HX - 0.05, 0.0, HL - 0.05, (HX + 0.05) if sx > 0 else -DOOR_X - 0.05, EAVE_Y, HL + 0.3))

        # the curtain pulled aside: a heavy drape hanging from under the swags to the ground beside the entrance post,
        # deep vertical folds, gathered and tied at hip height
        def C(a, b, sx=sx):
            y = 3.05 * (1 - b)
            g = math.exp(-((y - 1.15) / 0.38) ** 2)
            xi = DOOR_X - 0.03 + 0.32 * g + 0.08 * (y / 3.05)
            xo = POST_X - 0.2
            x = xi + (xo - xi) * a
            z = HL + 0.28 + 0.1 * math.sin(a * math.pi * 3.0 + 0.4) * (1 - 0.6 * g) + 0.05 * g
            return v3(sx * x, y, z)
        loft(sh, "drape_%d" % k, C, 3, 4, "mil_drape", th=0.05)
        add_cube(det, "drape_tie_%d" % k, v3(sx * (DOOR_X + 0.42), 1.15, HL + 0.36), ry(0.1 * sx), (0.62, 0.08, 0.1), "rope")

        # the swags: two heavy rolled folds of canvas looped from under the ridge to the entrance post, one under the
        # other (the lower one hangs over the top of the opening)
        for j, (xa, ya, xb, yb, dep, sag, zz) in enumerate(((0.42, BANNER_Y - 0.25, POST_X + 0.05, 3.0, 0.34, 0.26, HL + 0.22),
                                                            (0.4, BANNER_Y - 0.72, POST_X - 0.1, 2.72, 0.3, 0.2, HL + 0.3))):
            def S(a, b, sx=sx, xa=xa, ya=ya, xb=xb, yb=yb, dep=dep, sag=sag, zz=zz):
                x = xa + (xb - xa) * a
                top = ya + (yb - ya) * a - 0.1 * math.sin(math.pi * a)
                y = top - (dep + sag * math.sin(math.pi * a)) * b
                z = zz + 0.22 * math.sin(math.pi * b) * (0.55 + 0.45 * math.sin(math.pi * a)) + 0.04 * math.sin(a * math.pi * 4)
                return v3(sx * x, y, z)
            loft(sh, "swag_%d_%d" % (k, j), S, 5, 2, "mil_valance", th=0.08)
    # the heavy draped valance along the front edge of the roof, from under the ridge down past the entrance posts
    for k, sx in enumerate((-1, 1)):
        def D(s, t, sx=sx):
            x = sx * (0.15 + (HX + 0.1) * s)
            ytop = RIDGE_Y - 0.12 - (RIDGE_Y - EAVE_Y - 0.1) * s - 0.18 * math.sin(math.pi * s)
            drop = 0.28 + 0.12 * math.sin(math.pi * s)
            z = HL + OV + 0.04 + 0.05 * t + 0.13 * math.sin(math.pi * t) + 0.03 * math.sin(s * math.pi * 5)
            return v3(x, ytop - drop * t - 0.1 * t * abs(math.sin(s * math.pi * 2.5)), z)
        loft(sh, "valance_%d" % k, D, 6, 2, "mil_valance", th=0.04)


def frame(sh, det):
    """Posts, ridge pole, ridge-end posts with cross pieces and iron bands, the cross beam carrying the banner."""
    zf, zb = HL + 0.24, -HL - 0.24
    iron_post(sh, det, "post_front_l", -POST_X, zf, 3.3, d=0.52)
    iron_post(sh, det, "post_front_r", POST_X, zf, 3.05, d=0.5)
    iron_post(sh, det, "post_back_l", -POST_X, zb, 3.05)
    iron_post(sh, det, "post_back_r", POST_X, zb, 3.05)
    for k, (sx, sz) in enumerate(((-1, -1), (1, -1))):
        iron_post(sh, det, "post_corner_%d" % k, sx * (HX + 0.12), sz * (HL - 0.05), EAVE_Y + 0.35, d=0.34, bands=(0.3, None))
    beam(sh, "ridge_pole", (0, RIDGE_Y + 0.1, -HL - OV - 0.1), (0, RIDGE_Y + 0.1, HL + OV + 0.1), 0.22,
         {"all": "mil_ridge", "+1": "end_grain", "-1": "end_grain"})
    # ridge-end posts sticking out above the roof
    for k, (z, foot) in enumerate(((zf + 0.04, BANNER_Y - 0.1), (zb - 0.04, 0.0))):
        top = RIDGE_Y + 0.85
        beam(sh, "ridge_post_%d" % k, (0, foot, z), (0, top, z), 0.36, {"all": "mil_post", "+1": "end_grain", "-1": "end_grain"})
        box(sh, "ridge_post_%d_cross" % k, (-0.42, RIDGE_Y + 0.12, z - 0.17), (0.42, RIDGE_Y + 0.42, z + 0.17),
            {"all": "mil_post", "+1": "end_grain", "-1": "end_grain"}, stretch=True)
        box(sh, "ridge_post_%d_block" % k, (-0.24, RIDGE_Y - 0.4, z - 0.22), (0.24, RIDGE_Y - 0.05, z + 0.22), "mil_post", stretch=True)
        for j, y in enumerate((RIDGE_Y + 0.55, RIDGE_Y - 0.36)):
            box(det, "ridge_post_%d_band_%d" % (k, j), (-0.205, y, z - 0.205), (0.205, y + 0.14, z + 0.205), "mil_band", stretch=True)
        box(sh, "ridge_post_%d_cap" % k, (-0.15, top, z - 0.15), (0.15, top + 0.07, z + 0.15), "iron")
        if foot == 0.0:
            collide((-0.18, 0.0, z - 0.18, 0.18, EAVE_Y + 0.6, z + 0.18))
    # beams on the ridge with iron straps (as in the picture)
    for j, z in enumerate((-3.0, -1.6, -0.2, 1.2, 2.6)):
        box(det, "ridge_strap_%d" % j, (-0.17, RIDGE_Y - 0.06, z - 0.09), (0.17, RIDGE_Y + 0.25, z + 0.09), "mil_strap", stretch=True)
    # the cross beam under the front ridge carrying the banner
    yb = BANNER_Y
    beam(sh, "banner_beam", (-0.78, yb, zf + 0.14), (0.78, yb, zf + 0.14), 0.18, {"all": "mil_post", "+1": "end_grain", "-1": "end_grain"})
    for k, sx in enumerate((-1, 1)):
        box(det, "banner_beam_band_%d" % k, (sx * 0.62 - 0.06, yb - 0.11, zf + 0.03), (sx * 0.62 + 0.06, yb + 0.11, zf + 0.25), "mil_band",
            stretch=True)


def banner_and_lantern(sh, det):
    zf = HL + 0.24
    yb = BANNER_Y
    # the banner: about 1 x 1.75 like the picture, its point at 2.45 (players walk in under it)
    ml.banner(sh, "banner", (0.0, yb - 0.07, zf + 0.28), 0.96, 1.72, normal=(0, 0, 1), region="mil_banner", rod=True, wave=0.03,
              rod_region="mil_post", knobs="iron")
    lx, lz = -0.7, HL + 0.02
    ml.lantern(sh, "lamp_entrance", (lx, 2.66, lz), size=0.34, metal="iron", chain_to=(lx, 3.95, lz))


def guy_ropes(sh, det):
    """Six beige twisted guy ropes with a slight sag to wooden pegs with iron caps."""
    ropes = (((-POST_X, 3.1, HL + 0.3), (-3.95, 0.0, HL + 0.75)),
             ((POST_X, 2.85, HL + 0.3), (3.6, 0.0, HL + 1.2)),
             ((-HX - 0.05, EAVE_Y - 0.05, 2.0), (-4.0, 0.0, 2.35)),
             ((HX + 0.05, EAVE_Y - 0.05, 2.0), (4.0, 0.0, 2.35)),
             ((-HX - 0.05, EAVE_Y - 0.05, -2.2), (-4.0, 0.0, -2.5)),
             ((HX + 0.05, EAVE_Y - 0.05, -2.2), (4.0, 0.0, -2.5)))
    for k, (a, b) in enumerate(ropes):
        bb = v3(*b) + UP * 0.32
        ml.rope(det if k >= 2 else sh, "guy_%d" % k, a, bb, d=0.1, sag=0.07, segs=3, region="rope")
        p = v3(*b)
        box(sh, "peg_%d" % k, p + v3(-0.09, 0.0, -0.09), p + v3(0.09, 0.38, 0.09), {"all": "mil_post", "+2": "end_grain"})
        box(det, "peg_%d_cap" % k, p + v3(-0.115, 0.3, -0.115), p + v3(0.115, 0.44, 0.115), "mil_band", stretch=True)
    # the light ropes inside the entrance (curtain ties down to the ground)
    for k, sx in enumerate((-1, 1)):
        ml.rope(det, "door_rope_%d" % k, (sx * 1.15, 2.95, HL + 0.14), (sx * 1.7, 0.05, HL - 0.3), d=0.08, sag=0.02, segs=2, region="rope")


# ---------------------------------------------------------------- furniture
def bed(sh, det):
    x0, x1, z0, z1 = 1.35, 2.5, -3.45, -1.35
    h = 0.5
    for k, (x, z) in enumerate(((x0 + 0.06, z0 + 0.06), (x1 - 0.06, z0 + 0.06), (x0 + 0.06, z1 - 0.06), (x1 - 0.06, z1 - 0.06))):
        top = 1.0 if z < -3 else 0.62
        box(sh, "bed_leg_%d" % k, (x - 0.07, 0.0, z - 0.07), (x + 0.07, top, z + 0.07), "mil_post", stretch=True)
    box(sh, "bed_frame", (x0, 0.22, z0 + 0.05), (x1, 0.36, z1 - 0.05), {"all": "mil_post", "+2": "plank"}, stretch=True)
    box(sh, "bed_headboard", (x0 + 0.05, 0.4, z0 + 0.02), (x1 - 0.05, 0.92, z0 + 0.1), "plank", stretch=True)
    box(sh, "bed_mattress", (x0 + 0.06, 0.36, z0 + 0.12), (x1 - 0.06, h, z1 - 0.08), {"all": "cloth_beige"}, stretch=True)
    box(sh, "bed_blanket", (x0 + 0.02, h - 0.08, z0 + 0.75), (x1 - 0.02, h + 0.05, z1 - 0.05), "mil_blanket", stretch=True)
    box(det, "bed_blanket_fold", (x0 + 0.01, h - 0.02, z0 + 0.72), (x1 - 0.01, h + 0.09, z0 + 0.92), "mil_blanket", stretch=True)
    add_cube(sh, "bed_pillow", ((x0 + x1) / 2, h + 0.08, z0 + 0.38), rx(-0.12), (0.8, 0.16, 0.42), "cloth_beige", stretch=True)
    collide((x0, 0.0, z0, x1, 0.6, z1))


def table(sh, det, decor):
    x0, x1, z0, z1, ty = -2.5, -1.35, -1.25, -0.25, 0.92
    box(sh, "table_top", (x0, ty - 0.08, z0), (x1, ty, z1), {"all": "mil_post", "+2": "plank"}, stretch=True)
    for k, (x, z) in enumerate(((x0 + 0.1, z0 + 0.1), (x1 - 0.1, z0 + 0.1), (x0 + 0.1, z1 - 0.1), (x1 - 0.1, z1 - 0.1))):
        box(sh, "table_leg_%d" % k, (x - 0.06, 0.0, z - 0.06), (x + 0.06, ty - 0.08, z + 0.06), "mil_post", stretch=True)
    box(det, "table_rail", (x0 + 0.1, 0.25, (z0 + z1) / 2 - 0.04), (x1 - 0.1, 0.33, (z0 + z1) / 2 + 0.04), "mil_post", stretch=True)
    add_cube(sh, "table_map", ((x0 + x1) / 2 + 0.02, ty + 0.012, (z0 + z1) / 2), ry(0.08), (0.92, 0.02, 0.72), {"all": "mil_map"}, stretch=True,
             u_dir=v3(1, 0, 0), v_dir=v3(0, 0, 1))
    add_cube(det, "table_scroll", (x0 + 0.25, ty + 0.05, z0 + 0.15), ry(0.4), (0.4, 0.08, 0.08), "cloth_beige", stretch=True)
    add_cube(det, "table_dagger", (x1 - 0.25, ty + 0.03, z1 - 0.2), ry(-0.6), (0.34, 0.03, 0.05), "steel", stretch=True)
    collide((x0, 0.0, z0, x1, ty, z1))
    decor.block("furnish:spruce_stool", (x0 + x1) / 2, 0.0, z1 + 0.45, facing="back", fallback="wood_dark", solid=True)


def interior(sh, det, decor):
    bed(sh, det)
    table(sh, det, decor)
    decor.block("furnish:spruce_crate", -2.3, 0.0, -2.9, facing="front", alt="minecraft:barrel", fallback="crate")
    ml.crate(sh, "crate_back", (-2.45, 0.0, -1.95), size=(0.62, 0.55, 0.62), yaw=0.2)
    ml.crate(sh, "crate_bed", (2.6, 0.0, -0.75), size=(0.55, 0.5, 0.55), yaw=-0.15)
    ml.rug(sh, "rug", -1.2, 1.2, 1.0, HL + 0.5, y=0.05, region="mil_rug")
    # a few planks at the threshold under the rug, sticking out in front of it
    for k in range(5):
        x = -1.25 + 0.5 * k + 0.25
        box(det, "threshold_%d" % k, (x - 0.24, 0.0, HL - 0.1 + 0.03 * (k % 2)), (x + 0.24, 0.05, HL + 0.72 - 0.04 * (k % 3)), "plank", stretch=True)


def sacks(sh, det):
    """Six burlap sacks lying in a stack at the front left (3 + 2 + 1)."""
    x0, z0 = -3.75, HL + 0.62
    w, h, d = 0.7, 0.34, 0.56
    spots = [(0, 0, 0.1, 0.12), (1, 0, -0.05, -0.08), (2, 0, 0.15, 0.1), (0.5, 1, 0.05, -0.15), (1.5, 1, 0.12, 0.2), (1.0, 2, 0.08, -0.05)]
    for k, (i, j, dz, yaw) in enumerate(spots):
        c = v3(x0 + w / 2 + i * w * 0.95, h / 2 + j * h * 0.86, z0 + d / 2 + dz * d)
        R = ry(yaw) @ rz(0.06 * (1 if k % 2 else -1))
        add_cube(sh, "sack_%d" % k, c, R, (w, h * 0.8, d), "mil_burlap", stretch=True)
        add_cube(sh, "sack_%d_puff" % k, c + UP * 0.03, R, (w * 0.84, h, d * 0.8), "mil_burlap", stretch=True)
        add_cube(det, "sack_%d_mid" % k, c + UP * 0.015, R, (w * 0.94, h * 0.92, d * 0.9), "mil_burlap", stretch=True)
        add_cube(det, "sack_%d_end" % k, c + R @ v3(w / 2 + 0.05, 0, 0), R, (0.12, h * 0.45, d * 0.45), "mil_burlap", stretch=True)
        add_cube(det, "sack_%d_tie" % k, c + R @ v3(w / 2 + 0.01, 0, 0), R, (0.04, h * 0.55, d * 0.55), "rope")
    collide((x0, 0.0, z0, x0 + 3 * w * 0.95, 0.8, z0 + d + 0.1))


def rope_coil(det, c, r=0.27, turns=2):
    c = v3(*c)
    n = 8
    for j in range(turns):
        rr = r - 0.06 * j
        for k in range(n):
            a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
            p0 = c + v3(rr * math.cos(a0), 0.06 + 0.1 * j, rr * math.sin(a0))
            p1 = c + v3(rr * math.cos(a1), 0.06 + 0.1 * j, rr * math.sin(a1))
            beam(det, "coil_%d_%d" % (j, k), p0, p1, 0.12, "rope", width=0.12, extend=0.04)


def outside(sh, det):
    sacks(sh, det)
    cx, cz, s = -1.38, HL + 0.95, 0.8
    ml.crate(sh, "crate_front", (cx, 0.0, cz), size=(s, 0.78, s), yaw=0.05)
    for k, dx in enumerate((-0.3, 0.3)):
        box(det, "crate_front_strap_%d" % k, (cx + dx - 0.05, 0.0, cz - s / 2 - 0.02), (cx + dx + 0.05, 0.78, cz + s / 2 + 0.02), "mil_band",
            stretch=True)
    rope_coil(det, (cx, 0.78, cz))
    add_cube(sh, "coil_core", (cx, 0.82, cz), EYE, (0.5, 0.08, 0.5), "rope", stretch=True)
    # the short post on a stone base at the front right
    px, pz = 2.55, HL + 0.75
    box(sh, "stump_base", (px - 0.3, 0.0, pz - 0.3), (px + 0.3, 0.32, pz + 0.3), {"all": "stone", "+2": "stone_top"}, stretch=True)
    beam(sh, "stump", (px, 0.32, pz), (px, 1.25, pz), 0.36, {"all": "mil_post", "+1": "end_grain", "-1": "end_grain"})
    box(det, "stump_band", (px - 0.2, 0.95, pz - 0.2), (px + 0.2, 1.08, pz + 0.2), "mil_band", stretch=True)
    box(sh, "stump_cap", (px - 0.22, 1.25, pz - 0.22), (px + 0.22, 1.33, pz + 0.22), "mil_post", stretch=True)
    collide((px - 0.3, 0.0, pz - 0.3, px + 0.3, 1.33, pz + 0.3))


def icon(path):
    """16x16 item icon: the olive ridge tent from the front, the dark entrance, the green banner with a gold sword."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    wood = (92, 60, 34)
    for y in range(2, 15):
        half = 1.0 + (y - 2) * 0.62
        for x in range(16):
            dx = abs(x - 7.5)
            if dx <= half:
                c = OLIVE if (x + y) % 3 else OLIVE_D
                if abs(dx - half) < 0.7:
                    c = OLIVE_D
                if y >= 8 and dx < 2.6 - (0 if y > 9 else 1):
                    c = (36, 28, 18)
                p[x, y] = c + (255,)
    for y in range(0, 4):
        p[7, y] = p[8, y] = wood + (255,)
    for y in range(4, 10):
        for x in (6, 7, 8, 9):
            p[x, y] = GREEN_B + (255,)
        p[7, y] = p[8, y] = (GOLD if 5 <= y <= 8 else GREEN_B) + (255,)
    p[6, 6] = p[9, 6] = GOLD + (255,)
    p[7, 10] = p[8, 10] = GREEN_B + (255,)
    for y in range(7, 15):
        p[3, y] = p[12, y] = wood + (255,)
    p[3, 9] = p[12, 9] = (130, 132, 136, 255)
    for x in range(1, 15):
        p[x, 15] = (70, 96, 40, 255)
    p[5, 9] = (255, 200, 90, 255)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)


def build():
    ml.setup(NAME)
    random.seed(2400)
    atlas = ml.Atlas(NAME, colour="green")
    add_regions(atlas)
    root = ml.Bone(NAME)
    sh = ml.Bone("shell", parent=root)
    det = ml.Bone("detail", parent=root)
    decor = ml.Decor()
    roof(sh)
    side_walls(sh, det)
    gables(sh, det)
    frame(sh, det)
    banner_and_lantern(sh, det)
    guy_ropes(sh, det)
    interior(sh, det, decor)
    outside(sh, det)
    return ml.export(root, NAME, atlas, decor=decor, icon=icon, light=12)


if __name__ == "__main__":
    build()
