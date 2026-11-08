#!/usr/bin/env python3
"""tente_militaire — Tente militaire / Military Tent (1.24.0, camp militaire; reference S/ref/tente_militaire_ref.png).

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
ARCH_Y = 3.7           # top of the entrance arch (under the ridge)
NPC_SPOTS = ((-0.5, -2.7, 0.5, -1.7), (-0.5, -0.6, 0.5, 0.4))   # x0, z0, x1, z1: free 1 x 1 x 2.2 places for NPCs
WINDOW = (0.35, 1.4, 0.62, 1.55)   # z0, z1, y0, y1 of the window in the left wall

# ---------------------------------------------------------------- colours
OLIVE = (84, 100, 36)
OLIVE_D = (50, 63, 22)
OLIVE_L = (112, 128, 50)
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


def _olive(w, h, seed, folds=0, fold_dir="v", seams=0):
    """Mottled olive canvas: soft darker patches and lighter ones, a fine weave, fold shadows, seams."""
    n = _noise(w, h, seed, scale=7.0)
    m = _noise(w, h, seed + 7, scale=3.0)
    t = np.clip((n - 0.36) * 2.6, 0, 1)
    col = np.array(OLIVE_D)[None, None, :] * (1 - t[..., None]) + np.array(OLIVE)[None, None, :] * t[..., None]
    hi = np.clip((n - 0.66) * 2.2, 0, 1)[..., None] * 0.7
    col = col * (1 - hi) + np.array(OLIVE_L)[None, None, :] * hi
    col *= (0.93 + 0.14 * m)[..., None]
    yy, xx = np.mgrid[0:h, 0:w]
    col *= (1.0 + 0.03 * (((xx + yy) % 2) * 2 - 1))[..., None]
    rng = np.random.default_rng(seed + 3)
    col *= (1.0 + rng.integers(-6, 7, (h, w, 1)) / 100.0)
    if folds:
        coord = xx if fold_dir == "v" else yy
        span = w if fold_dir == "v" else h
        f = np.sin(coord / span * math.pi * 2 * folds + 0.6 + 0.5 * np.sin(coord * 0.37))
        col *= (1.0 + 0.10 * f - 0.12 * np.exp(-((f + 1.0) / 0.08) ** 2))[..., None]
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
    """The front curtains: olive with deep vertical folds (along v), a beige edging along the inner edge (right)."""
    w, h = img.size
    col = _olive(w, h, 2403, folds=3, fold_dir="v")
    xx = np.arange(w)[None, :]
    edge = xx >= w - 5
    col[np.broadcast_to(edge, (h, w))] = np.array(BEIGE) * 1.0
    col[:, w - 6, :] = np.array(BEIGE_D)
    col[:, w - 1, :] = np.array(BEIGE_D)
    rng = np.random.default_rng(2413)
    col[:, w - 5:, :] += rng.integers(-8, 9, (h, 5, 1))
    _put(img, col)


def paint_gable(img):
    """The back gable: an olive triangle (cut out above the roof line)."""
    w, h = img.size
    col = _olive(w, h, 2404, folds=4, fold_dir="v")
    yy, xx = np.mgrid[0:h, 0:w]
    inside = yy >= np.abs(xx - (w - 1) / 2) / ((w - 1) / 2) * (h - 1) - 0.5
    _put(img, col, np.where(inside, 255, 0))


def paint_banner(img):
    """Green banner, gold border, pointed bottom, a gold sword point down in a laurel wreath."""
    w, h = img.size    # 64 x 96
    rng = np.random.default_rng(2405)
    n = _noise(w, h, 2415, scale=6.0)
    col = np.array(GREEN_B)[None, None, :] * (0.88 + 0.24 * n[..., None])
    col += rng.integers(-4, 5, (h, w, 1))
    yy, xx = np.mgrid[0:h, 0:w]
    body = h - 22
    tip = body + (1 - np.abs(xx - (w - 1) / 2) / ((w - 1) / 2)) * 21
    alpha = np.where(yy <= tip, 255, 0)
    # border: 4 px beige-gold along the sides, the top and the V
    dist_side = np.minimum(xx, w - 1 - xx)
    dist_v = tip - yy
    border = (dist_side < 4) | (yy < 4) | ((yy > body - 4) & (dist_v < 4.5))
    col[border] = np.array(GOLD) * 1.0
    col[border & ((dist_side == 3) | (yy == 3) | ((dist_v >= 3.5) & (dist_v < 4.5) & (yy > body - 4)))] = np.array(GOLD_D) * 1.0
    col[border] += rng.integers(-10, 11, (int(border.sum()), 1))
    from PIL import Image, ImageDraw
    em = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(em)
    cx, cy = w / 2 - 0.5, 44
    g, gd = GOLD + (255,), GOLD_D + (255,)
    # laurel wreath: two arcs of leaves
    for side in (-1, 1):
        for k in range(7):
            th = math.radians(105 + k * 23)
            r = 19
            px_, py_ = cx + side * -r * math.cos(th), cy + 4 + r * math.sin(th) * 0.95
            d.ellipse([px_ - 3.4, py_ - 1.9, px_ + 3.4, py_ + 1.9], fill=g, outline=gd)
        d.line([(cx + side * -r * math.cos(math.radians(105)), cy + 4 + r * 0.95 * math.sin(math.radians(105))), (cx, cy + 24)], fill=gd, width=2)
    # sword, point down: pommel, grip, guard, blade
    d.ellipse([cx - 3, 14, cx + 3, 20], fill=g, outline=gd)
    d.rectangle([cx - 1.5, 20, cx + 1.5, 28], fill=gd)
    d.rectangle([cx - 11, 28, cx + 11, 31], fill=g, outline=gd)
    d.polygon([(cx - 3, 31), (cx + 3, 31), (cx + 3, 64), (cx, 70), (cx - 3, 64)], fill=(236, 214, 140, 255), outline=gd)
    d.line([(cx, 32), (cx, 66)], fill=gd)
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
    bars = ((xx % 10) < 2) | ((yy % 10) < 2) | (xx >= w - 2) | (yy >= h - 2)
    col[bars] = wood * (0.85 + 0.25 * _noise(w, h, 2419, scale=3.0)[bars][:, None])
    col[bars & (((xx % 10) == 1) | ((yy % 10) == 1))] *= 0.78
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
    """The draped valance: olive with folds, a beige edging along a scalloped lower edge (cut out below)."""
    w, h = img.size
    col = _olive(w, h, 2414, folds=4, fold_dir="v")
    yy, xx = np.mgrid[0:h, 0:w]
    bottom = h - 1 - 3 * (1 - np.abs(np.sin(xx / w * math.pi * 4)))
    band = (yy > bottom - 5) & (yy <= bottom)
    col[band] = np.array(BEIGE) * (0.92 + 0.1 * _noise(w, h, 2424, scale=3.0)[band][:, None])
    col[(yy > bottom - 6) & (yy <= bottom - 5)] = np.array(BEIGE_D) * 1.0
    _put(img, col, np.where(yy <= bottom, 255, 0))


def add_regions(atlas):
    atlas.add("mil_roof", 128, 64, paint_roof)
    atlas.add("mil_wall", 128, 32, paint_wall)
    atlas.add("mil_curtain", 48, 96, paint_curtain)
    atlas.add("mil_gable", 96, 48, paint_gable)
    atlas.add("mil_banner", 64, 96, paint_banner)
    atlas.add("mil_rug", 48, 64, paint_rug)
    atlas.add("mil_blanket", 32, 32, paint_blanket)
    atlas.add("mil_map", 32, 24, paint_map)
    atlas.add("mil_lattice", 32, 32, paint_lattice)
    atlas.add("mil_band", 32, 8, paint_band)
    atlas.add("mil_post", 64, 16, paint_post)
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
        loft(sh, "roof_%d" % k, P, 7, 4, "mil_roof", th=0.04)
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
        loft(sh, "wall_%d" % k, P, 6, 2, "mil_wall", th=0.035)
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
    # the flap rolled up above the window, and a small sloping hood
    def A(s, t):
        return v3(xw + 0.03 - 0.5 * t, y1 + 0.38 - 0.3 * t - 0.05 * math.sin(math.pi * t), z0 - 0.18 + (z1 - z0 + 0.36) * s)
    loft(sh, "window_hood", A, 2, 1, "mil_wall", th=0.03)
    beam(sh, "window_roll", (xw - 0.5, y1 + 0.03, z0 - 0.2), (xw - 0.5, y1 + 0.03, z1 + 0.2), 0.14, "mil_curtain", width=0.14)
    for j, z in enumerate((z0 - 0.05, z1 + 0.05)):
        beam(det, "window_tie_%d" % j, (xw - 0.02, y1 + 0.4, z), (xw - 0.5, y1 + 0.0, z), 0.04, "rope", width=0.04)


def gables(sh, det):
    """The closed back (wall + gable triangle) and the front: two curtains pulled back, tied, with a beige edging,
    draping from under the ridge in a curve over the entrance."""
    # back wall and gable
    def B(s, t):
        x = -HX + 2 * HX * s
        return v3(x, EAVE_Y + 0.02 - (EAVE_Y + 0.02) * t, -HL - 0.04 - 0.05 * math.sin(math.pi * t) + 0.03 * math.sin(x * 2.0))
    loft(sh, "back_wall", B, 4, 2, "mil_wall", th=0.035)
    ml.plate(sh, "back_gable", (0, (EAVE_Y + RIDGE_Y) / 2 - 0.02, -HL - 0.06), 2 * HX + 0.1, RIDGE_Y - EAVE_Y + 0.02, "mil_gable", normal=(0, 0, -1),
             th=0.02)
    collide((-HX, 0.0, -HL - 0.15, HX, EAVE_Y, -HL + 0.02))
    collide((-1.4, EAVE_Y, -HL - 0.15, 1.4, 3.3, -HL + 0.02))
    # front curtains
    s_e = EAVE_Y / (EAVE_Y + math.hypot(HX, RIDGE_Y - EAVE_Y))
    for k, sx in enumerate((-1, 1)):
        def outer(s, sx=sx):
            if s <= s_e:
                return v3(sx * (FOOT_X - (FOOT_X - HX) * (s / s_e)), EAVE_Y * s / s_e, HL + 0.04)
            q = (s - s_e) / (1 - s_e)
            return v3(sx * HX * (1 - q), EAVE_Y + (RIDGE_Y - 0.06 - EAVE_Y) * q, HL + 0.04)

        def inner(s, sx=sx):
            x = DOOR_X * (1 - s ** 2.6) * (1 - 0.15 * s) + 0.5 * math.exp(-((s - 0.28) / 0.13) ** 2)   # tied back near s = 0.28
            y = ARCH_Y * (s ** 0.9)
            return v3(sx * x, y, HL + 0.1)

        def P(a, b, sx=sx):
            s = 1.0 - b                       # loft t runs down: s = 1 at the top
            o, i = outer(s), inner(s)
            p = o * (1 - a) + i * a
            gather = math.exp(-((s - 0.28) / 0.16) ** 2)
            p[2] += 0.1 * math.sin(math.pi * a) * (1 - 0.5 * s) + 0.07 * math.sin(a * math.pi * 3.0 + s * 2.0) * (1 - gather * 0.5)
            p[2] += 0.12 * gather * a
            return p
        loft(sh, "curtain_%d" % k, P, 3, 7, "mil_curtain", th=0.035)
        # the tie round the gathered curtain
        tp = inner(0.28) * 0.65 + outer(0.28) * 0.35
        add_cube(det, "curtain_tie_%d" % k, tp + v3(0, 0, 0.18), EYE, (0.5, 0.07, 0.07), "rope")
        collide((min(sx * DOOR_X, sx * HX) if sx > 0 else -HX - 0.05, 0.0, HL - 0.05, (HX + 0.05) if sx > 0 else -DOOR_X - 0.05, EAVE_Y, HL + 0.3))
    # the inner valance swag under the ridge: a curved strip with the beige edging, across the top of the entrance
    def V(s, t):
        x = -0.95 + 1.9 * s
        y = ARCH_Y + 0.25 - 0.32 * t - 0.12 * math.sin(math.pi * s) * t
        return v3(x, y, HL + 0.14 + 0.05 * t)
    loft(sh, "front_swag", V, 3, 1, "mil_curtain", th=0.03)
    # the heavy draped valance along the front edge of the roof, from under the ridge down past the entrance posts
    for k, sx in enumerate((-1, 1)):
        def D(s, t, sx=sx):
            x = sx * (0.15 + (HX + 0.1) * s)
            ytop = RIDGE_Y - 0.12 - (RIDGE_Y - EAVE_Y - 0.1) * s - 0.18 * math.sin(math.pi * s)
            drop = 0.55 + 0.25 * math.sin(math.pi * s)
            z = HL + OV + 0.04 + 0.1 * t + 0.04 * math.sin(s * math.pi * 5)
            return v3(x, ytop - drop * t - 0.12 * t * abs(math.sin(s * math.pi * 2.5)), z)
        loft(sh, "valance_%d" % k, D, 5, 1, "mil_valance", th=0.03)


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
         {"all": "mil_post", "+1": "end_grain", "-1": "end_grain"})
    # ridge-end posts sticking out above the roof
    for k, (z, foot) in enumerate(((zf + 0.04, ARCH_Y + 0.1), (zb - 0.04, 0.0))):
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
    for j, z in enumerate((-2.3, -0.4, 1.5)):
        box(det, "ridge_strap_%d" % j, (-0.16, RIDGE_Y - 0.02, z - 0.08), (0.16, RIDGE_Y + 0.25, z + 0.08), "mil_band", stretch=True)
    # the cross beam under the front ridge carrying the banner
    yb = ARCH_Y + 0.05
    beam(sh, "banner_beam", (-1.15, yb, zf + 0.12), (1.15, yb, zf + 0.12), 0.18, {"all": "mil_post", "+1": "end_grain", "-1": "end_grain"})
    for k, sx in enumerate((-1, 1)):
        box(det, "banner_beam_band_%d" % k, (sx * 0.95 - 0.07, yb - 0.11, zf + 0.01), (sx * 0.95 + 0.07, yb + 0.11, zf + 0.23), "mil_band",
            stretch=True)
        beam(sh, "banner_brace_%d" % k, (sx * 1.15, yb, zf + 0.1), (sx * POST_X * 0.95, 2.7 if sx < 0 else 2.6, zf + 0.06), 0.12, "mil_post")


def banner_and_lantern(sh, det):
    zf = HL + 0.24
    yb = ARCH_Y + 0.05
    ml.banner(sh, "banner", (0.0, yb - 0.08, zf + 0.26), 1.12, 1.62, normal=(0, 0, 1), region="mil_banner", rod=True, wave=0.03,
              rod_region="mil_post", knobs="iron")
    lx, lz = -0.62, HL - 0.05
    ml.lantern(sh, "lamp_entrance", (lx, 2.55, lz), size=0.34, metal="iron", chain_to=(lx, ARCH_Y - 0.18, lz))


def guy_ropes(sh, det):
    """Six beige twisted guy ropes with a slight sag to wooden pegs with iron caps."""
    ropes = (((-POST_X, 3.1, HL + 0.3), (-3.95, 0.0, HL + 0.75)),
             ((POST_X, 2.85, HL + 0.3), (3.6, 0.0, HL + 1.2)),
             ((-HX - 0.05, EAVE_Y - 0.05, 1.3), (-4.0, 0.0, 1.6)),
             ((HX + 0.05, EAVE_Y - 0.05, 1.3), (4.0, 0.0, 1.6)),
             ((-HX - 0.05, EAVE_Y - 0.05, -2.2), (-4.0, 0.0, -2.5)),
             ((HX + 0.05, EAVE_Y - 0.05, -2.2), (4.0, 0.0, -2.5)))
    for k, (a, b) in enumerate(ropes):
        bb = v3(*b) + UP * 0.32
        ml.rope(det if k >= 2 else sh, "guy_%d" % k, a, bb, d=0.07, sag=0.07, segs=3, region="rope")
        p = v3(*b)
        box(sh, "peg_%d" % k, p + v3(-0.09, 0.0, -0.09), p + v3(0.09, 0.38, 0.09), {"all": "mil_post", "+2": "end_grain"})
        box(det, "peg_%d_cap" % k, p + v3(-0.115, 0.3, -0.115), p + v3(0.115, 0.44, 0.115), "mil_band", stretch=True)
    # the light ropes inside the entrance (curtain ties down to the ground)
    for k, sx in enumerate((-1, 1)):
        ml.rope(det, "door_rope_%d" % k, (sx * 1.25, 3.05, HL + 0.12), (sx * 1.85, 0.05, HL - 0.25), d=0.06, sag=0.02, segs=2, region="rope")


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
    ml.rug(sh, "rug", -1.2, 1.2, 1.0, HL + 0.15, y=0.0, region="mil_rug")
    # a few planks at the threshold under the rug
    for k in range(5):
        x = -1.25 + 0.5 * k + 0.25
        box(det, "threshold_%d" % k, (x - 0.24, 0.0, HL - 0.05 + 0.03 * (k % 2)), (x + 0.24, 0.05, HL + 0.45), "plank", stretch=True)


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
