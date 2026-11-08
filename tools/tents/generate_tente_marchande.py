#!/usr/bin/env python3
"""tente_marchande — Tente marchande / Merchant Tent (1.24.0, camp militaire; reference: scratchpad/ref/tente_marchande_ref.png).

A big medieval-fantasy merchant pavilion, one block (TentType group "tents", list TentTypes.CAMP_TENTS), about 9 blocks
wide (the main tent and its two covered side extensions) and 7.5 deep (the carpet in front included), the flag top at
about 7 blocks:

  - the main gabled roof, ridge along x, WIDE regular red and cream stripes running down the two slopes, soft folds
    between the stripes and a curved eave, striped gable ends, a GOLD crenellated valance along all the eaves,
    decorative twisted ropes draped along the front eave and coiled on the post tops;
  - the dark-wood post frame: big squared posts on iron-banded foot blocks, grey iron bands and rivets, big post caps
    standing above the roof, eave beams with iron straps, braces;
  - a small red-and-gold swallow-tailed FLAG on a pole on the ridge; a HANGING SIGN painted with gold coins on a beam
    at the top right; a RED BANNER with the gold coin purse on the front-left post; glowing LANTERNS on the two front
    posts, inside above the counter and under the right extension;
  - the left extension: a smaller red-and-cream striped awning with gold valance, red-and-cream drapes tied back, a
    gold-trimmed chest on a cross-braced stand, crates and a barrel under it, the big tied burlap sack in front;
  - the right extension: a lower cream awning with fine red stripes on two posts over stacked iron-banded barrels and
    crates;
  - inside: the wooden COUNTER under a red cloth with a gold patterned border (scrolls, a crate of red fruit, small
    crates on it), the back SHELVES (red and blue potions, bottles, books, cloth rolls, small sacks), striped drapes
    tied back at the front corners, the striped back wall and back half of the sides;
  - the RED-AND-GOLD patterned carpet in front of the counter.

The merchant's place (an EasyNPC, 1 x 1 x 2.2 free) is behind the counter (NPC_SPOT); players walk in behind it by the
gap between the front-left post and the counter (under the banner). No trade system, nothing ticks.

Usage:  python3 tools/tents/generate_tente_marchande.py     (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_marchande.json, models/entity + blockbench/tente_marchande.bbmodel,
textures/entity/tente_marchande.png, textures/item/tente_marchande.png, interiors/tente_marchande_decor.json.
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

NAME = "tente_marchande"
v3, norm, add_cube, beam, loft, Bone = ml.v3, ml.norm, ml.add_cube, ml.beam, ml.loft, ml.Bone
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ry, rx, rz = ml.ry, ml.rx, ml.rz
box, collide = ml.box, ml.collide
_rgb, _jitter, _scale, _mix = ml._rgb, ml._jitter, ml._scale, ml._mix
GOLD, GOLD_DARK, BEIGE = ml.GOLD, ml.GOLD_DARK, ml.BEIGE
RED, RED_DARK, RED_LIGHT = ml.COLOURS["red"]

# ---------------------------------------------------------------- dimensions (tent-local blocks, +z = the open front)
HW, HD = 2.7, 2.3            # main posts: x = +-HW, z = +-HD
EAVE, RIDGE = 3.4, 5.35      # eave and ridge heights
W, D = HW + 0.32, HD + 0.48  # the main roof's half length (x) and half depth (z)
EY = EAVE + 0.02
FRONT_TOP, BACK_TOP = 4.95, 5.75   # post tops (above the roof: the big caps)
STRIPES = 7
LX, RX = -4.5, 4.45          # outer post lines of the left / right extensions
COUNTER = (-1.2, 2.0, 1.4, 2.05)   # x0, x1, z0, z1
COUNTER_H = 1.05
NPC_SPOT = (-0.2, -1.25)     # (x0, z0) of the free 1 x 1 x 2.2 place behind the counter (the merchant)
SHELF_Z = (-2.2, -1.7)


# ---------------------------------------------------------------- textures (this tent's own regions)
def _weave_img(img, c, rng, stains=1):
    w, h = img.size
    ml._weave(img, (0, 0, w, h), c, rng, stains=stains)


def paint_valance(img):
    """The gold crenellated valance: a gold band, square tabs below it (cut-out gaps), dark-gold outlines."""
    rng = random.Random(2401)
    w, h = img.size
    px = img.load()
    band = int(h * 0.42)
    tab = w / 14.0
    for x in range(w):
        lx = (x % tab) / tab
        in_tab = 0.14 <= lx <= 0.86
        edge = abs(lx - 0.14) * tab < 1.0 or abs(lx - 0.86) * tab < 1.0
        for y in range(h):
            if y > band and not in_tab:
                px[x, y] = (0, 0, 0, 0)
                continue
            c = GOLD
            if y < 2:
                c = GOLD_DARK
            elif y == 2 or y == band - 1:
                c = _scale(GOLD, 1.12)
            elif y == band:
                c = _scale(GOLD, 0.72)
            elif y >= h - 2 or (y > band and edge):
                c = _scale(GOLD, 0.66)
            k = 1.0 + 0.04 * math.sin(x * 0.7) - (0.08 if (y > band and lx > 0.7) else 0.0)
            px[x, y] = _jitter(_scale(c, k), rng, 9) + (255,)
        if int(x % tab) == int(tab / 2):
            px[x, band // 2] = (120, 84, 30, 255)   # a rivet / stitch in each tab's band


def paint_runner(img):
    """The counter cloth: deep red, a gold border, a gold meander band above a gold hem."""
    rng = random.Random(2402)
    _weave_img(img, _scale(RED, 0.92), rng)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            e = min(x, w - 1 - x, y)
            if e < 2 or y >= h - 3:
                px[x, y] = _jitter(GOLD, rng, 10) + (255,)
            elif e < 3 or y == h - 4:
                px[x, y] = _jitter(RED_DARK, rng, 5) + (255,)
            elif h - 13 <= y <= h - 6:
                # meander: little gold squares with a hook
                ly, lx = y - (h - 13), x % 8
                on = (ly in (0, 7)) or (lx == 0 and ly < 6) or (lx == 5 and ly > 1) or (ly == 3 and 1 <= lx <= 5)
                if on:
                    px[x, y] = _jitter(_scale(GOLD, 0.95), rng, 10) + (255,)


def paint_carpet(img):
    """The red-and-gold carpet: red field, dark border, two gold lines, gold motifs in rows."""
    rng = random.Random(2403)
    _weave_img(img, RED, rng, stains=2)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            if e < 3:
                px[x, y] = _jitter(RED_DARK, rng, 5) + (255,)
            elif e in (4, 5) or e == 10:
                px[x, y] = _jitter(GOLD, rng, 10) + (255,)
            elif 6 <= e <= 9 and (x + y) % 6 < 2:
                px[x, y] = _jitter(_mix(RED, GOLD, 0.55), rng, 6) + (255,)
    # gold glyph motifs in rows on the field
    motif = ("01110", "10101", "11011", "10101", "01110")
    for cy in range(18, h - 14, 14):
        for cx in range(18 + (cy // 14) % 2 * 8, w - 16, 16):
            for j, row in enumerate(motif):
                for i, ch in enumerate(row):
                    if ch == "1":
                        px[cx + i - 2, cy + j - 2] = _jitter(GOLD, rng, 12) + (255,)


def _purse(img, box_, scale=4):
    """A gold coin purse (round bag, tied neck, frilled top) in box_ (x, y, w, h) of img."""
    from PIL import Image, ImageDraw
    x0, y0, w, h = box_
    S = scale
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    W_, H_ = w * S, h * S
    gold, gold_d, gold_l = (232, 178, 56), (138, 92, 22), (252, 222, 130)
    d.ellipse((W_ * 0.12, H_ * 0.36, W_ * 0.88, H_ * 0.98), fill=gold_d)
    d.ellipse((W_ * 0.16, H_ * 0.39, W_ * 0.84, H_ * 0.94), fill=gold)
    d.ellipse((W_ * 0.26, H_ * 0.5, W_ * 0.5, H_ * 0.7), fill=gold_l)
    d.polygon([(W_ * 0.38, H_ * 0.42), (W_ * 0.62, H_ * 0.42), (W_ * 0.56, H_ * 0.3), (W_ * 0.44, H_ * 0.3)], fill=gold)
    d.rectangle((W_ * 0.34, H_ * 0.3, W_ * 0.66, H_ * 0.36), fill=gold_d)
    d.polygon([(W_ * 0.3, H_ * 0.04), (W_ * 0.42, H_ * 0.16), (W_ * 0.5, H_ * 0.02), (W_ * 0.58, H_ * 0.16), (W_ * 0.7, H_ * 0.04),
               (W_ * 0.62, H_ * 0.3), (W_ * 0.38, H_ * 0.3)], fill=gold)
    d.line((W_ * 0.5, H_ * 0.62, W_ * 0.5, H_ * 0.82), fill=gold_d, width=S)
    im = im.resize((w, h), Image.NEAREST)
    img.alpha_composite(im, (x0, y0))


def paint_banner(img):
    """The red banner: gold border, V point (cut-out), the gold coin purse."""
    rng = random.Random(2404)
    _weave_img(img, RED, rng)
    w, h = img.size
    px = img.load()
    body = int(h * 0.74)
    for y in range(h):
        for x in range(w):
            if y >= body:
                half = (w / 2) * (1 - (y - body) / (h - body))
                dx = abs(x - (w - 1) / 2)
                if dx > half:
                    px[x, y] = (0, 0, 0, 0)
                elif dx > half - 3:
                    px[x, y] = _jitter(GOLD, rng, 10) + (255,)
                continue
            if x < 3 or x >= w - 3 or y < 3:
                px[x, y] = _jitter(GOLD, rng, 10) + (255,)
            elif x < 4 or x >= w - 4 or y < 4:
                px[x, y] = _jitter(RED_DARK, rng, 5) + (255,)
    s = w - 14
    _purse(img, (7, int(h * 0.26), s, s))


def paint_flag(img):
    """The small red-and-gold swallow-tailed flag: red, gold border and a gold band across."""
    rng = random.Random(2405)
    _weave_img(img, RED, rng)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            notch = x > w * 0.7 and abs(y - (h - 1) / 2) < (x - w * 0.7) * (h / 2) / (w * 0.3)
            if notch:
                px[x, y] = (0, 0, 0, 0)
            elif y < 3 or y >= h - 3 or x < 3 or abs(y - (h - 1) / 2) < 2.2:
                px[x, y] = _jitter(_mix(GOLD, (230, 120, 30), 0.25), rng, 10) + (255,)


def paint_sign(img):
    """The hanging sign: dark wooden planks in a frame, a stack of gold coins painted on it."""
    rng = random.Random(2406)
    w, h = img.size
    ml.fine_wood(img, (0, 0, w, h), _rgb("7a5230"), _rgb("3a2410"), 8, rng, joints=False, knots=0.1, grain=0.12, shade=0.06)
    px = img.load()
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            if e < 3:
                px[x, y] = _jitter(_rgb("4a2e14"), rng, 5) + (255,)
            elif e == 3:
                px[x, y] = _jitter(_rgb("2a1a0a"), rng, 4) + (255,)
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    gold, gold_d, gold_l = (236, 180, 52), (140, 92, 20), (252, 226, 130)

    def coin(cx, cy, rw=7, rh=3):
        d.ellipse((cx - rw, cy - rh + 2, cx + rw, cy + rh + 2), fill=gold_d)
        d.rectangle((cx - rw, cy, cx + rw, cy + 2), fill=gold_d)
        d.ellipse((cx - rw, cy - rh, cx + rw, cy + rh), fill=gold)
        d.ellipse((cx - rw + 3, cy - rh + 1, cx + rw - 3, cy + rh - 1), outline=gold_l)
    cx, base = w // 2, h - 10
    for k in range(4):
        coin(cx - 9, base - 4 * k)
    for k in range(3):
        coin(cx + 7, base - 4 * k)
    coin(cx - 1, base - 18)
    for (x, y) in ((5, 5), (w - 6, 5), (5, h - 6), (w - 6, h - 6)):
        px[x, y] = (160, 160, 166, 255)


def paint_awning_r(img):
    """The right extension's awning: cream cloth in wide stripes (two creams), a fine red stripe between them."""
    rng = random.Random(2407)
    w, h = img.size
    n = 6
    edges = [int(round(k * w / n)) for k in range(n + 1)]
    for k in range(n):
        ml._weave(img, (edges[k], 0, edges[k + 1] - edges[k], h), ml.BEIGE if k % 2 == 0 else _scale(ml.BEIGE, 0.92), rng, stains=1)
    px = img.load()
    for e in edges[1:-1]:
        for y in range(h):
            for x in (e - 1, e):
                px[x, y] = _jitter(ml.COLOURS["red"][0], rng, 6) + (255,)
    for y in range(h):
        k = 0.9 + 0.12 * (y / h)
        for x in range(w):
            r, g, b, a = px[x, y]
            px[x, y] = _scale((r, g, b), k) + (255,)


def paint_wall(img):
    """Draped walls and curtains: vertical red / cream stripes, darker folds, a gold hem at the bottom."""
    rng = random.Random(2408)
    w, h = img.size
    edges = ml._stripes(img, "red", 6, rng)
    px = img.load()
    sw = w / 6
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            fx = (x % sw) / sw
            k = 0.86 + 0.16 * math.sin(math.pi * fx)
            if x in edges:
                k *= 0.8
            if y >= h - 4:
                px[x, y] = _jitter(GOLD if y >= h - 3 else GOLD_DARK, rng, 8) + (255,)
            else:
                px[x, y] = _scale((r, g, b), k) + (255,)


def paint_drape(img):
    """A tied-back curtain: one wide crimson band and one wide cream band, darker folds, a gold hem."""
    rng = random.Random(2412)
    w, h = img.size
    ml._stripes(img, "red", 2, rng)
    px = img.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            k = 0.84 + 0.18 * math.sin(math.pi * ((x * 2.0 / w) % 1.0))
            if y >= h - 4:
                px[x, y] = _jitter(GOLD if y >= h - 3 else GOLD_DARK, rng, 8) + (255,)
            else:
                px[x, y] = _scale((r, g, b), k) + (255,)


def paint_chest(img):
    """The chest's wood: warm planks, gold corner plates (the gold trim boxes add the bands)."""
    rng = random.Random(2409)
    w, h = img.size
    ml.fine_wood(img, (0, 0, w, h), _rgb("8a5a2c"), _rgb("4a2c12"), 8, rng, joints=False, knots=0.1, grain=0.12, shade=0.06)
    px = img.load()
    for y in range(h):
        for x in range(w):
            if (x < 4 or x >= w - 4) and (y < 4 or y >= h - 4):
                px[x, y] = _jitter(GOLD, rng, 10) + (255,)


CREAM = _rgb("d9c2a2")            # the picture's warm cream (merchantlib's beige is paler)
CRIMSON = (_rgb("9c2430"), _rgb("561018"), _rgb("bc3a44"))   # the picture's deep crimson red


def _recoloured(painter):
    """Runs a merchantlib stripe painter with this tent's cream and crimson (merchantlib itself stays untouched)."""
    def paint(img):
        old_b, old_r = ml.BEIGE, ml.COLOURS["red"]
        ml.BEIGE, ml.COLOURS["red"] = CREAM, CRIMSON
        try:
            painter(img)
        finally:
            ml.BEIGE, ml.COLOURS["red"] = old_b, old_r
    return paint


def paint_post(img):
    """The posts' warm orange-brown wood (lighter than merchantlib's carved dark post), grain along u."""
    rng = random.Random(2411)
    w, h = img.size
    ml.fine_wood(img, (0, 0, w, h), _rgb("b87a40"), _rgb("6a4020"), h, rng, joints=False, knots=0.08, grain=0.14, shade=0.08)


def add_regions(atlas):
    """This tent's regions, in an order that packs them in the free band of the 512 px atlas (no doubling)."""
    seed = 2410
    atlas.add("mv_roof", 32 * STRIPES, 96, _recoloured(ml._stall_roof_painter("red", STRIPES, seed)))
    atlas.add("mv_carpet", 112, 96, paint_carpet)
    atlas.add("mv_banner", 48, 96, paint_banner)
    atlas.add("mv_wall", 128, 64, _recoloured(paint_wall))
    atlas.add("mv_roof_l", 32 * 5, 64, _recoloured(ml._stall_roof_painter("red", 5, seed + 2)))
    atlas.add("mv_awning_r", 128, 64, _recoloured(paint_awning_r))
    atlas.add("mv_runner", 64, 48, paint_runner)
    atlas.add("mv_gable", 32 * 5, 48, _recoloured(ml._stall_gable_painter("red", 5, seed + 1)))
    atlas.add("mv_sign", 64, 44, paint_sign)
    atlas.add("mv_flag", 64, 32, paint_flag)
    atlas.add("mv_chest", 32, 32, paint_chest)
    atlas.add("mv_post", 64, 16, paint_post)
    atlas.add("mv_valance", 224, 24, paint_valance)
    atlas.add("mv_drape", 32, 64, _recoloured(paint_drape))
    if atlas.size != 512:
        raise AssertionError("the atlas grew to %d px: repack the regions" % atlas.size)


# ---------------------------------------------------------------- geometry helpers
def roof_drop(t, a=0.5):
    """The main roof's profile (fraction of the drop at t from the ridge): steep at the ridge, flatter at the eave."""
    return a * t + (1 - a) * (1 - (1 - t) ** 2)


def post(shell, det, name, x, z, top, eave, d=0.42, foot=0.7, cap=0.56, rope_coil=False):
    """A big squared dark-wood post: iron-banded foot block, the post, grey iron bands with rivets, a big cap block on
    top (iron collar under it); collides from the ground up to the eave."""
    box(shell, name + "_foot", (x - 0.3, 0.0, z - 0.3), (x + 0.3, foot, z + 0.3), {"all": "wood_dark", "+2": "end_grain"})
    for k, y in enumerate((0.04, foot - 0.13)):
        box(det, "%s_fband_%d" % (name, k), (x - 0.315, y, z - 0.315), (x + 0.315, y + 0.1, z + 0.315), "iron")
    beam(shell, name, (x, foot, z), (x, top, z), d, {"all": "mv_post", "+1": "end_grain", "-1": "end_grain"})
    for k, y in enumerate((1.55, eave - 0.75)):
        box(det, "%s_band_%d" % (name, k), (x - d / 2 - 0.02, y, z - d / 2 - 0.02), (x + d / 2 + 0.02, y + 0.12, z + d / 2 + 0.02), "iron")
    box(det, name + "_collar", (x - d / 2 - 0.03, top - 0.14, z - d / 2 - 0.03), (x + d / 2 + 0.03, top, z + d / 2 + 0.03), "iron")
    box(shell, name + "_cap", (x - cap / 2, top, z - cap / 2), (x + cap / 2, top + 0.3, z + cap / 2), {"all": "wood", "+2": "end_grain"})
    box(det, name + "_cap_top", (x - cap / 2 + 0.08, top + 0.3, z - cap / 2 + 0.08), (x + cap / 2 - 0.08, top + 0.4, z + cap / 2 - 0.08),
        {"all": "wood_dark", "+2": "end_grain"})
    if rope_coil:
        for k in range(2):
            y = top - 0.42 - 0.12 * k
            box(det, "%s_coil_%d" % (name, k), (x - d / 2 - 0.06, y, z - d / 2 - 0.06), (x + d / 2 + 0.06, y + 0.1, z + d / 2 + 0.06), "rope")
    collide((x - 0.3, 0.0, z - 0.3, x + 0.3, eave, z + 0.3))


def small_post(shell, det, name, x, z, top, d=0.3):
    """An extension post: foot block, squared post, two iron bands, a small cap; collides up to its top."""
    box(shell, name + "_foot", (x - 0.22, 0.0, z - 0.22), (x + 0.22, 0.45, z + 0.22), {"all": "wood_dark", "+2": "end_grain"})
    box(det, name + "_fband", (x - 0.235, 0.32, z - 0.235), (x + 0.235, 0.41, z + 0.235), "iron")
    beam(shell, name, (x, 0.45, z), (x, top, z), d, {"all": "mv_post", "+1": "end_grain", "-1": "end_grain"})
    box(det, name + "_band", (x - d / 2 - 0.02, top - 0.55, z - d / 2 - 0.02), (x + d / 2 + 0.02, top - 0.45, z + d / 2 + 0.02), "iron")
    box(shell, name + "_cap", (x - 0.2, top, z - 0.2), (x + 0.2, top + 0.18, z + 0.2), {"all": "wood", "+2": "end_grain"})
    collide((x - 0.22, 0.0, z - 0.22, x + 0.22, top, z + 0.22))


def valance(bone, name, c0, c1, out, h=0.56, region="mv_valance"):
    """A gold crenellated valance from c0 to c1 (its top edge), flaring out a little towards `out`."""
    c0, c1, out = v3(*c0), v3(*c1), v3(*out)

    def V(s, t):
        e = c0 + (c1 - c0) * s
        return e + UP * 0.03 - UP * (h * t) + out * (0.03 + 0.05 * t)
    L = np.linalg.norm(c1 - c0)
    loft(bone, name, V, max(1, int(round(L / 3.0))), 1, region, th=0.025)


def drape(bone, det, name, top_a, top_b, tie, bot_a, bot_b, normal, region="mv_drape", nx=3):
    """A curtain tied back: hangs from the edge top_a - top_b, gathered at `tie` (a rope band), flaring again below
    to bot_a - bot_b; soft folds (ripples along `normal`)."""
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
    add_cube(det, name + "_tie", tie, np.column_stack([side, UP, np.cross(side, UP)]), (0.26, 0.08, 0.16), "rope")


def wall(bone, name, a, b, y0, y1, out, region="mv_wall", nx=6, fold=0.05):
    """A hanging canvas wall from a (left) to b on the ground line, y0..y1, soft vertical folds towards `out`."""
    a, b, out = v3(*a), v3(*b), v3(*out)

    def P(s, t):
        p = a + (b - a) * s
        return v3(p[0], y1 - (y1 - y0) * t, p[2]) + out * (fold * math.sin(s * math.pi * nx) * (0.4 + 0.6 * t))
    loft(bone, name, P, nx, 2, region, th=0.03)


def scroll(bone, name, c, length=0.4, r=0.055, yaw=0.0, region="beige"):
    """A rolled scroll lying on its side (two boxes turned 45 degrees about its axis), along yaw."""
    c = v3(*c)
    for k, a in enumerate((0.0, math.pi / 4)):
        add_cube(bone, "%s_%d" % (name, k), c, ry(yaw) @ rx(a), (length, 2 * r * 0.83, 2 * r * 0.83), {"all": region, "+1": "white", "-1": "white"},
                 stretch=True)


def roll(bone, name, c, length=0.45, r=0.08, yaw=0.0, region="cloth_red"):
    scroll(bone, name, c, length=length, r=r, yaw=yaw, region=region)


def chest(shell, det, name, foot, w=0.9, d=0.6, h=0.62, yaw=0.0):
    """A gold-trimmed chest: wooden body, domed lid (two boxes), gold bands and corners, a gold lock plate."""
    foot = v3(*foot)
    R = ry(yaw)
    add_cube(shell, name + "_body", foot + UP * (h * 0.36), R, (w, h * 0.72, d), {"all": "mv_chest"}, stretch=True)
    add_cube(shell, name + "_lid", foot + UP * (h * 0.8), R, (w + 0.02, h * 0.18, d + 0.02), {"all": "mv_chest"}, stretch=True)
    add_cube(shell, name + "_lid_top", foot + UP * (h * 0.94), R, (w, h * 0.12, d * 0.72), {"all": "mv_chest"}, stretch=True)
    for k, s in enumerate((-0.3, 0.3)):
        add_cube(det, "%s_band_%d" % (name, k), foot + R @ v3(s * w, h * 0.52, 0), R, (0.07, h * 1.0 + 0.02, d + 0.03), "gold")
    add_cube(det, name + "_rim", foot + UP * (h * 0.71), R, (w + 0.04, 0.05, d + 0.04), "gold")
    add_cube(det, name + "_lock", foot + R @ v3(0, h * 0.62, d / 2 + 0.02), R, (0.14, 0.18, 0.04), "gold")


def big_sack(shell, det, name, foot, yaw=0.0, w=0.72, h=1.05):
    """The big tied burlap sack of the picture: a tall bulging body narrowing upwards, a tied neck, a flared top."""
    foot = v3(*foot)
    R = ry(yaw)
    for k, (y0, y1, s) in enumerate(((0.0, 0.18, 0.86), (0.18, 0.55, 1.0), (0.55, 0.78, 0.86), (0.78, 0.86, 0.6))):
        add_cube(shell, "%s_%d" % (name, k), foot + UP * (h * (y0 + y1) / 2), R @ ry(0.08 * k), (w * s, h * (y1 - y0), w * s * 0.92), "sack",
                 stretch=True)
    add_cube(shell, name + "_neck", foot + UP * (h * 0.9), R, (w * 0.3, h * 0.08, w * 0.3), "sack", stretch=True)
    add_cube(det, name + "_tie", foot + UP * (h * 0.9), R, (w * 0.34, 0.05, w * 0.34), "rope")
    add_cube(shell, name + "_top", foot + UP * (h * 0.98), R @ ry(0.4), (w * 0.52, h * 0.1, w * 0.5), "sack", stretch=True)


# ---------------------------------------------------------------- the build
def build(atlas, decor):
    rng = random.Random(24)
    root = Bone(NAME)
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)
    corners = [(-HW, HD), (HW, HD), (HW, -HD), (-HW, -HD)]   # FL, FR, BR, BL
    tops = [FRONT_TOP, FRONT_TOP, BACK_TOP, BACK_TOP]
    for k, (x, z) in enumerate(corners):
        post(shell, det, "post_%d" % k, x, z, tops[k], EAVE, rope_coil=(k in (0, 3)))
    by = EAVE - 0.2
    # eave beams with iron straps, braces
    for k in range(4):
        (xa, za), (xb, zb) = corners[k], corners[(k + 1) % 4]
        along_x = k in (0, 2)
        beam(shell, "eave_%d" % k, (xa, by, za), (xb, by, zb), 0.34, {"all": "beam", "+1": "end_grain", "-1": "end_grain"}, width=0.3,
             extend=0.36 if along_x else 0.16)
        if along_x:
            for s in (-1, 1):
                box(det, "eave_%d_strap_%d" % (k, (s + 1) // 2), (s * (HW - 0.45) - 0.06, by - 0.19, za - 0.17),
                    (s * (HW - 0.45) + 0.06, by + 0.19, za + 0.17), "iron")
    for k, (p, q) in enumerate((((-HW + 0.2, EAVE - 1.15, HD), (-HW + 0.95, by - 0.12, HD)), ((HW - 0.2, EAVE - 1.15, HD), (HW - 0.95, by - 0.12, HD)),
                                ((-HW, EAVE - 1.15, -HD + 0.2), (-HW, by - 0.12, -HD + 0.95)), ((HW, EAVE - 1.15, -HD + 0.2), (HW, by - 0.12, -HD + 0.95)))):
        beam(shell, "brace_%d" % k, p, q, 0.16, "wood_dark", extend=0.05)
    # tie beam across the middle (the inside lantern hangs from it), the ridge pole, king posts and rafters at the ends
    beam(shell, "tie_beam", (-HW, by, 0.0), (HW, by, 0.0), 0.22, "wood_dark", extend=0.1)
    beam(shell, "ridge_pole", (-W - 0.22, RIDGE - 0.12, 0), (W + 0.22, RIDGE - 0.12, 0), 0.22, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    for k, sx in enumerate((-1, 1)):
        x = sx * HW
        beam(shell, "king_post_%d" % k, (x, by + 0.17, 0), (x, RIDGE - 0.2, 0), 0.18, "wood_dark")
        for j, sz in enumerate((-1, 1)):
            beam(shell, "rafter_%d_%d" % (k, j), (x, by + 0.1, sz * (HD + 0.05)), (x, RIDGE - 0.16, 0), 0.15, "wood_dark", extend=0.05)
        box(det, "ridge_cap_%d" % k, (sx * (W + 0.22) - 0.08, RIDGE - 0.26, -0.15), (sx * (W + 0.22) + 0.08, RIDGE + 0.02, 0.15), "iron")
    # ---- the main roof: two sagging slopes, stripes down the slope, a soft fold in each stripe
    def roof_pt(s, t, sgn):
        x = -W + 2 * W * s
        frac = (s * STRIPES) % 1.0
        y = RIDGE - (RIDGE - EY) * roof_drop(t) - 0.08 * math.sin(math.pi * s) * math.sin(math.pi * t)
        # each stripe bellies a little between its seams (soft folds), pushed in along the slope's normal so that the
        # strips stay flush (no wedge gaps between them)
        dy = -(RIDGE - EY) * (0.5 + 0.5 * 2 * (1 - t))
        nrm = norm(v3(0.0, D, -dy))
        fold = 0.07 * math.sin(math.pi * frac)
        return v3(x if sgn > 0 else -x, y - nrm[1] * fold, sgn * (D * t - nrm[2] * fold))
    loft(shell, "roof_front", lambda s, t: roof_pt(s, t, 1), STRIPES * 2, 4, "mv_roof", th=0.04, overlap=0.03)
    loft(shell, "roof_back", lambda s, t: roof_pt(s, t, -1), STRIPES * 2, 4, "mv_roof", th=0.04, overlap=0.03)
    # the ridge cover: a cream band along the ridge
    box(shell, "ridge_cover", (-W, RIDGE - 0.02, -0.18), (W, RIDGE + 0.06, 0.18), {"all": "cloth_beige"}, stretch=True, u_dir=X)
    for k, sx in enumerate((-1, 1)):
        ml.plate(shell, "gable_%d" % k, (sx * (W - 0.03), (EY + RIDGE) / 2, 0), 2 * D, RIDGE - EY, "mv_gable", normal=(sx, 0, 0), th=0.02)
    # the gold crenellated valance on the four sides
    valance(shell, "valance_front", (-W, EY, D + 0.04), (W, EY, D + 0.04), Z)
    valance(shell, "valance_back", (W, EY, -D - 0.04), (-W, EY, -D - 0.04), -Z)
    valance(shell, "valance_left", (-W - 0.02, EY, -D), (-W - 0.02, EY, D), -X)
    valance(shell, "valance_right", (W + 0.02, EY, D), (W + 0.02, EY, -D), X)
    # decorative twisted ropes draped along the front eave (three swags, knots at the hooks) and along the left gable
    pts = [-W + 0.1, -W / 3, W / 3, W - 0.1]
    for k in range(3):
        ml.rope(det, "eave_rope_%d" % k, (pts[k], EY + 0.02, D + 0.12), (pts[k + 1], EY + 0.02, D + 0.12), d=0.07, sag=0.26, segs=3)
    for k, x in enumerate(pts[1:3]):
        add_cube(det, "rope_knot_%d" % k, (x, EY - 0.02, D + 0.13), EYE, (0.14, 0.16, 0.12), "rope")
    ml.rope(det, "gable_rope", (-W - 0.08, EY + 0.02, D - 0.1), (-W - 0.08, EY + 0.02, -D + 0.1), d=0.07, sag=0.3, segs=3)
    ml.rope(det, "back_rope", (-W + 0.1, EY + 0.02, -D - 0.12), (W - 0.1, EY + 0.02, -D - 0.12), d=0.07, sag=0.3, segs=3)
    # ---- the flag on the ridge
    fx = -0.9
    box(shell, "flag_base", (fx - 0.2, RIDGE - 0.05, -0.2), (fx + 0.2, RIDGE + 0.22, 0.2), {"all": "wood", "+2": "end_grain"})
    box(det, "flag_base_band", (fx - 0.21, RIDGE + 0.1, -0.21), (fx + 0.21, RIDGE + 0.16, 0.21), "iron")
    beam(shell, "flag_pole", (fx, RIDGE + 0.2, 0), (fx, 7.0, 0), 0.13, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    box(shell, "flag_knob", (fx - 0.12, 7.0, -0.12), (fx + 0.12, 7.2, 0.12), "gold")

    def F(s, t):
        return v3(fx + 0.06 + 1.65 * s, 6.92 - 0.78 * t - 0.12 * s + 0.08 * math.sin(s * math.pi * 2.0),
                  0.16 * math.sin(s * math.pi * 1.6) + 0.02 * t)
    loft(shell, "flag", F, 5, 1, "mv_flag", th=0.025)
    # ---- the banner with the gold purse on the front-left post
    bx, bz, byy = -2.28, HD + 0.26, 3.05
    box(det, "banner_arm", (-HW - 0.05, byy - 0.05, HD + 0.2), (-HW + 0.05, byy + 0.05, bz + 0.05), "iron")
    beam(shell, "banner_rod", (-HW - 0.05, byy, bz), (bx + 0.48, byy, bz), 0.08, "wood_dark")
    add_cube(det, "banner_rod_knob", (bx + 0.5, byy, bz), EYE, (0.12, 0.12, 0.12), "gold")
    ml.banner(shell, "banner", (bx, byy - 0.04, bz + 0.01), 0.82, 1.78, normal=(0, 0, 1), region="mv_banner", rod=False)
    # ---- lanterns: front posts (outer sides), inside above the counter, under the right extension
    for k, (x, z, dx, dz) in enumerate(((-HW, HD, -1, 0.6), (HW, HD, 0.35, 1))):
        mount = v3(x + dx * 0.21, 2.95, z + dz * 0.21)
        tip = v3(x + dx * 0.55, 2.95, z + dz * 0.55)
        beam(det, "lamp_arm_%d" % k, mount, tip, 0.05, "iron", extend=0.02)
        beam(det, "lamp_brace_%d" % k, mount - UP * 0.4, tip - UP * 0.02, 0.04, "iron")
        ml.lantern(shell, "lamp_%d" % k, tip - UP * 0.5, size=0.38, metal="iron", chain_to=tip)
    ml.lantern(shell, "lamp_in", (1.0, 2.55, 0.0), size=0.34, metal="iron", chain_to=(1.0, by - 0.1, 0.0))
    # ---- side and back walls (striped, hanging canvas), tied-back drapes at the front corners
    wall(shell, "wall_back", (-HW, 0, -HD - 0.08), (HW, 0, -HD - 0.08), 0.0, by - 0.15, -Z)
    collide((-HW, 0.0, -HD - 0.14, HW, by - 0.15, -HD - 0.02))
    for k, sx in enumerate((-1, 1)):
        x = sx * (HW + 0.02)
        wall(shell, "wall_side_%d" % k, (x, 0, -HD), (x, 0, -0.55), 0.0, by - 0.15, v3(sx, 0, 0), nx=4)
        collide((x - 0.06, 0.0, -HD, x + 0.06, by - 0.15, -0.55))
        # drapes tied back at the front corners (inside the front posts) and at the open middle of the sides
        xa, xb = sx * (HW - 0.2), sx * (HW - 1.0)
        drape(shell, det, "drape_front_%d" % k, (xa, by - 0.15, HD - 0.26), (xb, by - 0.15, HD - 0.26), (sx * (HW - 0.32), 1.45, HD - 0.3),
              (sx * (HW - 0.22), 0.04, HD - 0.3), (sx * (HW - 0.62), 0.04, HD - 0.3), Z)
        drape(shell, det, "drape_side_%d" % k, (x, by - 0.15, -0.5), (x, by - 0.15, 0.45), (x, 1.5, -0.42),
              (x, 0.04, -0.5), (x, 0.04, -0.12), v3(sx, 0, 0), nx=2)
    # ---- the left extension: striped awning, gold valance, posts, tied-back drapes
    lz0, lz1 = -1.85, 2.15
    ly_in, ly_out = 3.2, 2.55
    for k, z in enumerate((lz1, lz0)):
        small_post(shell, det, "lpost_%d" % k, LX, z, ly_out - 0.1)
    beam(shell, "l_beam_front", (-HW, ly_out - 0.2, lz1), (LX, ly_out - 0.2, lz1), 0.22, "beam", extend=0.15)
    beam(shell, "l_beam_back", (-HW, ly_out - 0.2, lz0), (LX, ly_out - 0.2, lz0), 0.22, "beam", extend=0.15)
    beam(shell, "l_beam_side", (LX, ly_out - 0.08, lz0), (LX, ly_out - 0.08, lz1), 0.22, "beam", extend=0.15)

    def LA(s, t):   # s along z (back -> front), t from the main post line out to the outer posts
        z = (lz0 - 0.2) + (lz1 - lz0 + 0.55) * s
        frac = (s * 5) % 1.0
        x = -HW - 0.05 + (LX - 0.3 + HW + 0.05) * t
        y = ly_in - (ly_in - ly_out) * t - 0.1 * math.sin(math.pi * t) - 0.05 * math.sin(math.pi * frac)
        return v3(x, y, z)
    loft(shell, "l_awning", lambda s, t: LA(1 - s, t), 10, 3, "mv_roof_l", th=0.035, overlap=0.03)
    valance(shell, "l_valance_front", (-HW - 0.05, ly_in - 0.02, lz1 + 0.38), (LX - 0.3, ly_out - 0.02, lz1 + 0.38), Z, h=0.4)
    valance(shell, "l_valance_side", (LX - 0.32, ly_out - 0.02, lz1 + 0.35), (LX - 0.32, ly_out - 0.02, lz0 - 0.2), -X, h=0.4)
    drape(shell, det, "l_drape", (LX + 0.18, ly_out - 0.3, lz1 + 0.05), (LX + 0.95, ly_out - 0.32, lz1 + 0.05), (LX + 0.25, 1.25, lz1 + 0.02),
          (LX + 0.18, 0.04, lz1), (LX + 0.6, 0.04, lz1), Z)
    wall(shell, "l_wall_back", (LX, 0, lz0 - 0.05), (-HW, 0, lz0 - 0.05), 0.0, ly_out - 0.3, -Z, nx=3)
    collide((LX, 0.0, lz0 - 0.1, -HW, ly_out - 0.3, lz0))
    # ---- the right extension: lower cream awning with fine red stripes on two posts
    rz0, rz1 = -1.8, 1.95
    ry_in, ry_out = 2.95, 2.4
    for k, z in enumerate((rz1, rz0)):
        small_post(shell, det, "rpost_%d" % k, RX, z, ry_out - 0.1)
    beam(shell, "r_beam_front", (HW, ry_out - 0.2, rz1), (RX, ry_out - 0.2, rz1), 0.22, "beam", extend=0.15)
    beam(shell, "r_beam_back", (HW, ry_out - 0.2, rz0), (RX, ry_out - 0.2, rz0), 0.22, "beam", extend=0.15)
    beam(shell, "r_beam_side", (RX, ry_out - 0.08, rz0), (RX, ry_out - 0.08, rz1), 0.22, "beam", extend=0.15)

    def RA(s, t):
        z = (rz0 - 0.2) + (rz1 - rz0 + 0.55) * s
        frac = (s * 6) % 1.0
        x = HW + 0.05 + (RX + 0.32 - HW - 0.05) * t
        y = ry_in - (ry_in - ry_out) * t - 0.08 * math.sin(math.pi * t) - 0.04 * math.sin(math.pi * frac)
        return v3(x, y, z)
    loft(shell, "r_awning", RA, 12, 3, "mv_awning_r", th=0.035, overlap=0.03)
    valance(shell, "r_valance_front", (HW + 0.05, ry_in - 0.02, rz1 + 0.38), (RX + 0.32, ry_out - 0.02, rz1 + 0.38), Z, h=0.36)
    valance(shell, "r_valance_side", (RX + 0.34, ry_out - 0.02, rz0 - 0.2), (RX + 0.34, ry_out - 0.02, rz1 + 0.35), X, h=0.36)
    ml.rope(det, "r_rope", (HW + 0.1, ry_in - 0.05, rz1 + 0.45), (RX + 0.3, ry_out - 0.05, rz1 + 0.45), d=0.06, sag=0.22, segs=3)
    ml.lantern(shell, "lamp_r", (3.55, 1.72, rz1), size=0.34, metal="iron", chain_to=(3.55, ry_out - 0.3, rz1))
    # ---- the hanging sign with the gold coins, on a beam at the top right
    sy = 4.7
    beam(shell, "sign_beam", (HW, sy, HD), (4.95, sy, HD), 0.26, {"all": "beam", "+1": "end_grain", "-1": "end_grain"}, width=0.26, extend=0.12)
    beam(shell, "sign_brace", (HW + 0.05, sy - 0.95, HD), (HW + 0.95, sy - 0.08, HD), 0.16, "wood_dark", extend=0.04)
    box(det, "sign_strap_0", (HW + 0.25, sy - 0.15, HD - 0.15), (HW + 0.35, sy + 0.15, HD + 0.15), "iron")
    box(det, "sign_strap_1", (4.75, sy - 0.15, HD - 0.15), (4.85, sy + 0.15, HD + 0.15), "iron")
    sx0 = 4.1
    for k, dx in enumerate((-0.38, 0.38)):
        add_cube(det, "sign_ring_%d" % k, (sx0 + dx, sy - 0.22, HD), EYE, (0.06, 0.2, 0.12), "iron")
    box(shell, "sign", (sx0 - 0.55, sy - 1.1, HD - 0.05), (sx0 + 0.55, sy - 0.3, HD + 0.05), {"all": "wood_dark", "+3": "mv_sign", "-3": "mv_sign"},
        stretch=True, u_dir=X, v_dir=-UP)
    # ---- the counter with the red cloth with a gold border, and its goods
    cx0, cx1, cz0, cz1 = COUNTER
    top = ml.counter(shell, "counter", cx0, cx1, cz0, cz1, h=COUNTER_H, detail=det)
    y = top[1]
    zc = (cz0 + cz1) / 2
    box(shell, "runner", (-0.4, y, cz0 + 0.02), (1.45, y + 0.015, cz1 + 0.05), {"all": "cloth_red"}, stretch=True, u_dir=X)
    ml.plate(shell, "runner_front", (0.52, y - 0.43, cz1 + 0.06), 1.85, 0.88, "mv_runner", normal=(0, 0, 1), th=0.012, edge="cloth_red")
    for k, (x, dz, yaw) in enumerate(((-0.95, 0.15, 0.15), (-0.72, -0.05, -0.2), (-0.85, 0.05, 0.05))):
        scroll(det, "scroll_%d" % k, (x, y + 0.06 + 0.1 * (k == 2), zc + dz), length=0.42, r=0.06, yaw=yaw)
    ml.plate(det, "scroll_open", (-0.5, y + 0.012, zc + 0.18), 0.36, 0.26, "beige", normal=(0, 1, 0), up=(0, 0, -1), th=0.008)
    ml.crate(shell, "fruit_crate", (0.6, y + 0.015, zc), size=(0.6, 0.28, 0.42), yaw=0.08, content="apples", solid=False)
    for k, (dx, dz) in enumerate(((-0.12, 0.0), (0.1, 0.06), (0.0, -0.1))):
        add_cube(det, "fruit_%d" % k, (0.6 + dx, y + 0.34, zc + dz), ry(0.4 * k), (0.13, 0.12, 0.13), "cloth_red")
    ml.crate(shell, "small_crate_0", (1.62, y, zc - 0.02), size=(0.42, 0.3, 0.38), yaw=-0.12, solid=False)
    ml.crate(shell, "small_crate_1", (1.6, y + 0.3, zc - 0.02), size=(0.3, 0.22, 0.28), yaw=0.15, solid=False)
    # ---- the back shelves: potions, bottles, books, cloth rolls, small sacks
    levels = ml.shelf_unit(shell, "shelves", -HW + 0.45, HW - 0.45, SHELF_Z[0], SHELF_Z[1], levels=(0.62, 1.22, 1.82, 2.42), h=2.75,
                           back=False, uprights=4, detail=det)
    lv = sorted(levels, key=lambda s: s[2])
    pot = ("blue", "red", "red", "blue", "red", "green", "red", "blue")
    for j, (x0, x1, yy, zf, zb) in enumerate(lv):
        zc = (zf + zb) / 2
        if j in (1, 2):   # potions and bottles
            n = 9
            for i in range(n):
                xx = x0 + 0.15 + (x1 - x0 - 0.3) * i / (n - 1)
                if j == 2 and 4 <= i <= 5:
                    continue
                ml.bottle(det, "pot_%d_%d" % (j, i), (xx, yy, zc + 0.05 * ((i % 2) - 0.5)), pot[(i + j) % len(pot)], r=0.075 + 0.015 * (i % 3 == 0),
                          h=0.2 + 0.04 * (i % 2), shape="round" if i % 3 else "tall", neck_h=0.07)
            if j == 2:
                ml.sack(det, "shelf_sack", ((x0 + x1) / 2 - 0.05, yy, zc), s=0.32, yaw=0.3)
        elif j == 0:      # cloth rolls and a small sack
            for i, (dx, reg) in enumerate(((0.3, "cloth_red"), (0.55, "cloth_blue"), (0.8, "cloth_beige"))):
                roll(det, "roll_%d" % i, (x0 + dx + 0.1, yy + 0.09, zc), length=0.42, r=0.085, yaw=math.pi / 2, region=reg)
            ml.sack(det, "low_sack", (x1 - 0.5, yy, zc), s=0.36, yaw=-0.2)
            ml.crate(det, "low_box", (x0 + 1.8, yy, zc), size=(0.45, 0.3, 0.36), solid=False)
        else:             # books, a jar, a scroll
            xx = x0 + 0.1
            for i in range(10):
                bw = 0.08 + 0.02 * rng.random()
                bh = 0.26 + 0.08 * rng.random()
                reg = ("cloth_red", "cloth_blue", "leather", "cloth_dark", "cloth_red", "leather_dark")[i % 6]
                box(det, "book_%d" % i, (xx, yy, zc - 0.1), (xx + bw, yy + bh, zc + 0.12), {"all": reg, "+2": "white", "-2": "white"})
                xx += bw + 0.01
            ml.bottle(det, "jar_top", (x1 - 0.6, yy, zc), "green", r=0.1, h=0.22, shape="tall", neck_h=0.06)
            scroll(det, "shelf_scroll", (x1 - 0.25, yy + 0.07, zc), length=0.36, r=0.06, yaw=math.pi / 2)
    # ---- the carpet in front of the counter
    ml.rug(shell, "carpet", -1.5, 2.15, 2.2, 4.75, y=0.0, region="mv_carpet")
    # ---- the left extension's goods: the gold-trimmed chest on a cross-braced stand, crates, a barrel; the big sack
    stx, stz = -3.6, 1.35
    box(shell, "stand", (stx - 0.5, 0.0, stz - 0.36), (stx + 0.5, 0.55, stz + 0.36), {"all": "crate", "+2": "plank"}, stretch=True)
    for k, (p, q) in enumerate((((stx - 0.45, 0.05, stz + 0.38), (stx + 0.45, 0.5, stz + 0.38)), ((stx - 0.45, 0.5, stz + 0.38), (stx + 0.45, 0.05, stz + 0.38)))):
        beam(det, "stand_x_%d" % k, p, q, 0.07, "wood_dark", width=0.04)
    collide((stx - 0.5, 0.0, stz - 0.36, stx + 0.5, 0.55, stz + 0.36))
    chest(shell, det, "chest", (stx, 0.55, stz), w=0.86, d=0.58, h=0.6, yaw=0.0)
    collide((stx - 0.45, 0.55, stz - 0.31, stx + 0.45, 1.15, stz + 0.31))
    decor.block("furnish:spruce_crate", -3.65, 0.0, 0.05, facing="front", alt="minecraft:barrel", fallback="crate")
    ml.crate(shell, "l_crate_top", (-3.65, 1.0, 0.05), size=0.55, yaw=0.2, solid=True)
    ml.barrel(shell, "l_barrel", (-3.75, 0.0, -1.15), r=0.34, h=0.85)
    big_sack(shell, det, "big_sack", (-3.55, 0.0, 3.0), yaw=0.25)
    ml.sack(det, "small_sack", (-4.15, 0.0, 2.75), s=0.45, yaw=-0.4)
    collide((-3.95, 0.0, 2.62, -3.15, 0.8, 3.38))
    # the iron-banded barrel in front of the front-left post, a low crate beside the counter
    ml.barrel(shell, "fl_barrel", (-2.68, 0.0, 2.98), r=0.33, h=0.86)
    ml.crate(shell, "fl_crate", (-1.98, 0.0, 3.35), size=(0.5, 0.42, 0.45), yaw=0.1, solid=True)
    # ---- the right extension's goods: stacked barrels and crates
    ml.barrel(shell, "r_barrel_0", (3.35, 0.0, 1.25), r=0.36, h=0.88)
    ml.crate(shell, "r_crate_on_barrel", (3.35, 0.88, 1.25), size=0.55, yaw=-0.1, solid=True)
    ml.barrel(shell, "r_barrel_1", (3.4, 0.0, 0.35), r=0.34, h=0.85)
    ml.crate(shell, "r_crate_0", (4.0, 0.0, 1.35), size=0.72, yaw=0.05, solid=True)
    ml.crate(shell, "r_crate_1", (4.05, 0.72, 1.35), size=0.5, yaw=-0.15, solid=True)
    decor.block("furnish:spruce_crate", 3.95, 0.0, -0.75, facing="front", alt="minecraft:barrel", fallback="crate")
    decor.block("landsoficaria:cypress_barrel", 3.3, 0.0, -0.75, facing="front", alt="minecraft:barrel", fallback="barrel")
    ml.crate(det, "r_box_small", (4.1, 0.0, 2.45), size=(0.4, 0.3, 0.36), yaw=0.3, solid=False)
    return root


def item_icon(path):
    """16x16: the striped stall icon in red (gold emblem dot on the banner) + the flag and the coin sign."""
    from PIL import Image
    ml.stall_icon(path, colour="red", emblem="diamond", banners=1)
    im = Image.open(path).convert("RGBA")
    p = im.load()
    for y in range(0, 2):
        p[6, y] = (90, 60, 30, 255)
    p[7, 0] = p[8, 0] = RED + (255,)
    p[7, 1] = GOLD + (255,)
    for y in range(4, 7):
        for x in range(13, 16):
            p[x, y] = (110, 74, 40, 255)
    p[14, 5] = GOLD + (255,)
    im.save(path)


def main():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="red")
    add_regions(atlas)
    decor = ml.Decor()
    root = build(atlas, decor)
    ml.export(root, NAME, atlas, decor=decor, icon=item_icon, light=13)


if __name__ == "__main__":
    main()
