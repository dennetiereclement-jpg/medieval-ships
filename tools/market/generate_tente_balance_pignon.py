#!/usr/bin/env python3
"""tente_balance_pignon — Tente à pignon à la balance / Gabled Scales Tent (1.26.0, market tents group D; reference:
scratchpad/ref2/tente_balance_pignon_ref.png, picture 097).

A red-and-cream gabled merchant pavilion of the scales (balance) merchants, one block (TentType group "tents"), with two
side awnings, seen in the picture from the front (a little from the left):

  - the MAIN TENT: four tall squared corner posts that rise well above the eaves, with iron bands, coiled ropes,
    gilded collars and small golden knob finials; a gabled roof (ridge along x) in regular broad red and cream stripes
    running straight down the slopes (props_d.loft_down), the ridge rising in a soft curve to a raised middle (the
    "pignon"): a short crossbar resting on it, its gilded ends with small knob finials, from which the big red SCALES
    BANNER hangs down the front slope (gold border, stepped point, gold diamond); striped gable ends; a deep stepped
    dagged valance edged in gold along the eaves, curving between the posts; thick ropes from the front posts up to the
    crossbar and down to the side awnings' posts, with tassels; the walls a dusky canvas in the shade of the roof;
  - under the front eave three banners: two red scales banners (left of the middle, and under the right awning by the
    front-right post) and a middle banner with a faded emblem;
  - the two SIDE AWNINGS sloping out from the gable ends to outer posts with finials, striped red and cream, edged with
    the same dagged gold-edged valance;
  - inside: the COUNTER along the front under a cream top cloth dripping over its edge in gold-edged points and a red
    runner (gold border, meander, stepped point, diamond), with an open book, three bottles, a scroll and a blue book;
    back shelves of bottles and potions with two sacks; a lantern hanging at the front left (and one inside at the
    back);
  - under the left awning the produce: a big iron-banded crate under a crate of red apples, stacked crates of tomatoes
    and cabbages (Farmer's Delight crates when installed), a crate of lavender, an open crate of grain, rice sacks, a
    barrel by the front-left post;
  - under the right awning: crates and chests stacked (a gold-trimmed chest, a chest of blue gems, a dwarven chest when
    the mod is installed), a sack;
  - the RED rug with its gold border in front of the counter.

The merchant's place (an EasyNPC, 1 x 1 x 2.2 free) is behind the counter (NPC); players walk round the counter's left
end (between it and the front-left post). No trade system, nothing ticks.

Usage:  python3 tools/market/generate_tente_balance_pignon.py   (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_balance_pignon.json, models/entity + blockbench/tente_balance_pignon.bbmodel,
textures/entity/tente_balance_pignon.png, textures/item/tente_balance_pignon.png, interiors/tente_balance_pignon_decor.json.
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import props_d as pd  # noqa: E402

ml = pd.ml
NAME = "tente_balance_pignon"
v3, norm, add_cube, beam, loft, Bone = pd.v3, pd.norm, pd.add_cube, pd.beam, pd.loft, pd.Bone
EYE, UP, X, Z = pd.EYE, pd.UP, pd.X, pd.Z
ry, rx, rz = pd.ry, pd.rx, pd.rz
box, collide = pd.box, pd.collide
_rgb, _jitter, _scale, _mix = pd._rgb, pd._jitter, pd._scale, pd._mix

PAL = pd.Pal(cream="ecb880", red="8e2620", red_dark="561410", red_light="b03a30", gold="f0a030", gold_dark="8a5010",
             gold_light="ffd27a", wood="8a5028", wood_dark="442410", finial="f0a83a")

# ---------------------------------------------------------------- dimensions (design coordinates, +z = the front; the
# whole tent is moved at the end so that its extent is centred on the anchor block)
HW = 2.6                          # main posts at x = +-HW
ZF, ZB = 1.9, -2.1                # main posts' z (front, back)
ZR = (ZF + ZB) / 2                # the ridge line
EAVE = 3.7                        # top of the eave beams
EY = EAVE + 0.02                  # the roof's eave line
OV = 0.35                         # the roof's overhang in front and behind
W = HW + 0.05                     # the roof's half length (it ends at the posts)
D = ZF + OV - ZR                  # the roof's half depth (ridge to eave)
RY_END, RY_MID = 5.15, 5.95       # the ridge at its ends and in the raised middle
POST_TOP = 5.6                    # the corner posts' tops (above the ridge ends)
DROOP = 0.2                       # the eaves sag between the posts
LX, RX = -5.0, 4.9                # the side awnings' outer posts (x)
AZ0, AZ1 = -1.5, ZF               # the side awnings' back and front posts (z)
L_OUT, R_OUT = 3.66, 3.62         # the side awnings' outer edges (their cloth starts on the gable profile)
COUNTER = (-1.45, 1.6, 0.55, 1.25)   # x0, x1, z0, z1 (along the front, facing +z)
COUNTER_H = 1.05
RUG = (-1.1, 2.5, 1.45, 4.15)     # x0, x1, z0, z1
NPC = (-0.5, -1.05)               # (x0, z0) of the merchant's free 1 x 1 x 2.2 place (design coordinates)
STRIPES = 11


def drop(t, a=0.42):
    """The roof's profile (fraction of the drop at t from the ridge): steep at the ridge, flatter at the eave."""
    return a * t + (1 - a) * (1 - (1 - t) ** 2)


def ridge_y(x):
    """The ridge's height at x: low at the gable ends, rising in a soft curve to the raised middle."""
    u = min(1.0, abs(x) / W)
    return RY_END + (RY_MID - RY_END) * 0.5 * (1 + math.cos(math.pi * u))


# ---------------------------------------------------------------- textures
def paint_gable(img):
    """A gable end: 5 vertical stripes, cut out above the roof profile (the ridge end at the top middle), a dark hem
    along the two slopes."""
    rng = random.Random(9701)
    pd.stripes_painter(PAL, [(1, "r"), (1, "c"), (1, "r"), (1, "c"), (1, "r")], 9702, fold=0.1, seam=True, top_dark=0)(img)
    w, h = img.size
    px = img.load()
    for x in range(w):
        t = abs((x + 0.5) / w * 2.0 - 1.0)
        top = drop(t) * h
        for y in range(h):
            r, g, b, a = px[x, y]
            if y + 0.5 < top - 0.5:
                px[x, y] = (0, 0, 0, 0)
            elif y + 0.5 < top + 2.0:
                px[x, y] = _scale((r, g, b), 0.7) + (255,)
            else:
                px[x, y] = _jitter(_scale((r, g, b), 0.86 + 0.12 * (y / h)), rng, 2) + (255,)


def paint_gems(img):
    rng = random.Random(9703)
    w, h = img.size
    ml._heap(img, (0, 0, w, h), [_rgb("3a8ae8"), _rgb("6ac0ff"), _rgb("2050b0"), _rgb("e8f4ff")], rng, bg=_rgb("8a6a20"), r=2)


def produce_crate_painter(cols, seed):
    """Stand-in of a Farmer's Delight crate (drawn only without the mod): crate planks, produce on the upper third."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        ml.fine_wood(img, (0, 0, w, h), _rgb("8a5a2c"), _rgb("4a2c12"), 8, rng, joints=False, knots=0.1, grain=0.12, shade=0.06)
        ml._heap(img, (0, 0, w, h // 3 + 2), cols, rng, bg=_rgb("4a3a20"), r=3)
        px = img.load()
        for x in range(w):
            for y in (0, h - 1):
                px[x, y] = (60, 40, 22, 255)
            for y in range(h // 3 + 2, h // 3 + 4):
                px[x, y] = (70, 46, 24, 255)
    return paint


def add_regions(atlas):
    """This tent's regions, packed by hand in rows of the 512 px atlas (no doubling)."""
    s = 9710
    stripes = [(1, "r" if k % 2 == 0 else "c") for k in range(STRIPES)]
    # row 1 (y 224, after the shell regions): 96 high
    atlas.add("pd_roof", 28 * STRIPES, 96, pd.stripes_painter(PAL, stripes, s + 1, fold=0.16))
    atlas.add("pd_banner_peak", 48, 96, pd.banner_painter(PAL, s + 2, point="step", diamond=True, border=3, body=0.7))
    atlas.add("pd_banner", 32, 80, pd.banner_painter(PAL, s + 3, point="step", diamond=True, border=2, body=0.68))
    atlas.add("pd_finial", 16, 16, pd.finial_painter(PAL, s + 4))
    # row 2: 96 high
    # (chunkier pixels than the other regions: the picture's rug has a bold border of big gold squares)
    atlas.add("pd_rug", 120, 80, pd.rug_painter(PAL, s + 5, motif="chain", glyphs=False, stains=5))
    atlas.add("pd_awning", 160, 64, pd.stripes_painter(PAL, [(1, "r" if k % 2 == 0 else "c") for k in range(7)], s + 6, fold=0.14))
    atlas.add("pd_gable", 160, 48, paint_gable)
    atlas.add("pd_banner_mid", 32, 80, pd.banner_painter(PAL, s + 7, point="step", diamond=True, border=2, body=0.68, faded=True))
    # row 3: 64 high
    atlas.add("pd_runner", 48, 64, pd.runner_painter(PAL, s + 8, point="step"))
    # (the walls are in the shade of the roof and the awnings in the picture: a dusky canvas, not bright cream)
    atlas.add("pd_wall", 96, 64, pd.canvas_painter(PAL, s + 9, base=_mix(_mix(PAL.cream, PAL.red, 0.12), PAL.wood_dark, 0.42), folds=5,
                                                   hem=PAL.red_dark, bottom_red=6))
    atlas.add("pd_valance", 224, 32, pd.valance_painter(PAL, s + 10, [(1, "r" if k % 2 == 0 else "c", 1.0) for k in range(STRIPES)], shape="step",
                                                        band=0.4, gold_edge=PAL.gold))
    atlas.add("pd_valance_aw", 128, 32, pd.valance_painter(PAL, s + 11, [(1, "r" if k % 2 == 0 else "c", 1.0) for k in range(7)], shape="step",
                                                           band=0.4, gold_edge=PAL.gold))
    # row 4: 32 high
    atlas.add("pd_chest", 32, 32, pd.chest_painter(PAL, s + 12))
    atlas.add("pd_lavender", 32, 32, pd.flowers_painter(_rgb("9a5ad0"), _rgb("643a9a"), _rgb("c8a0f0"), s + 13, n=7, lavender=True))
    atlas.add("pd_burlap", 32, 32, pd.burlap_painter(s + 14, base="b89262"))
    atlas.add("pd_gems", 16, 16, paint_gems)
    atlas.add("pd_post", 64, 16, pd.wood_painter(PAL.wood, PAL.wood_dark, s + 15))
    atlas.add("pd_grain", 32, 16, pd.grain_painter(s + 16, base="eee0b8"))
    atlas.add("pd_book", 32, 16, pd.book_painter(s + 17))
    atlas.add("pd_band", 32, 8, pd.band_painter(s + 18))
    atlas.add("pd_fb_red", 32, 32, produce_crate_painter([_rgb("e03a22"), _rgb("f05a30"), _rgb("a01a10")], s + 19))
    atlas.add("pd_fb_green", 32, 32, produce_crate_painter([_rgb("7ab83a"), _rgb("5a9a2a"), _rgb("9ad04a")], s + 20))
    atlas.add("pd_fb_orange", 32, 32, produce_crate_painter([_rgb("f08a20"), _rgb("e06a10"), _rgb("ffb040")], s + 21))
    atlas.add("pd_cream", 32, 16, lambda img: pd.weave(img, PAL.cream, random.Random(s + 23), stains=1))
    atlas.add("pd_drip", 64, 16, pd.valance_painter(PAL, s + 22, [(1, "c", 0.55), (1, "c", 1.0)] * 6, shape="step", band=0.45,
                                                    gold_edge=PAL.gold))
    if atlas.size != 512:
        raise AssertionError("the atlas grew to %d px: repack the regions" % atlas.size)


# ---------------------------------------------------------------- roof geometry
def roof_face(sgn, folds=STRIPES, depth=0.05, sag=0.16):
    """The front (sgn = 1) or back (sgn = -1) roof face: s along x (left to right as seen from its side), t from the
    ridge down to the eave."""
    def P(s, t):
        x = (-W + 2 * W * s) * sgn
        top = ridge_y(x)
        bot = EY - DROOP * math.sin(math.pi * s)
        y = top - (top - bot) * drop(t) - sag * math.sin(math.pi * t) * math.sin(math.pi * s)
        z = ZR + sgn * D * t
        p = v3(x, y, z)
        frac = (s * folds) % 1.0
        n = norm(v3(0, D, sgn * (top - bot) * (1.4 - t)))
        return p - n * depth * math.sin(math.pi * frac) * math.sin(math.pi * min(1.0, t * 1.4))
    return P


FRONT = roof_face(1)


def front_at(x, t):
    return FRONT((x + W) / (2 * W), t)


def front_normal(x, t):
    p0, p1 = front_at(x, max(0.0, t - 0.02)), front_at(x, min(1.0, t + 0.02))
    q0, q1 = front_at(x - 0.05, t), front_at(x + 0.05, t)
    n = norm(np.cross(q1 - q0, p1 - p0))
    return -n if n[1] < 0 else n


# ---------------------------------------------------------------- the build
def gable_y(z):
    """The main roof's profile at its gable ends: the ridge end height at the ridge line down to the eave."""
    return RY_END - (RY_END - EY) * drop(min(1.0, abs(z - ZR) / D))


def awning(shell, det, name, sx, x_out, y_out, region="pd_awning"):
    """A side awning sweeping out of the gable end (x = sx * HW) to the outer posts at x_out: its cloth starts on the
    main roof's gable profile (high at the ridge line, low at the eaves) and falls in a concave curve to the outer edge
    at y_out, so that its front edge runs level with the main eave, as in the picture; striped, a stepped valance on its
    front and outer edges, posts and beams, a canvas back wall."""
    for k, z in enumerate((AZ1, AZ0)):
        pd.post(shell, det, "%s_post_%d" % (name, k), x_out, z, y_out + 0.3, d=0.32, foot=(0.42, 0.44), bands=(1.0, y_out - 0.55),
                collide_top=y_out + 0.3)
        pd.rope_wrap(det, "%s_coil_%d" % (name, k), x_out, z, y_out + 0.1, 0.16, turns=2)
    fb = y_out - 0.12
    beam(shell, name + "_beam_out", (x_out, fb, AZ0), (x_out, fb, AZ1), 0.2, {"all": "pd_post", "+1": "end_grain", "-1": "end_grain"}, extend=0.22)
    for k, z in enumerate((AZ1, AZ0)):
        beam(shell, "%s_beam_%d" % (name, k), (sx * HW, min(fb, gable_y(z) - 0.25), z), (x_out, fb, z), 0.18, "pd_post", extend=0.1)
    x0, x1 = sx * (HW + 0.03), x_out + sx * 0.3
    z0, z1 = AZ0 - 0.25, ZF + OV
    ye = y_out + 0.02

    def A(s, t):   # s along z (u across the stripes), t from the gable out
        z = z1 + (z0 - z1) * s if sx < 0 else z0 + (z1 - z0) * s
        x = x0 + (x1 - x0) * t
        yi = gable_y(z)
        f = 1.0 - (1.0 - t) ** 1.9
        frac = (s * 7) % 1.0
        y = yi + (ye - yi) * f - 0.06 * math.sin(math.pi * t) * (yi - ye) - 0.035 * math.sin(math.pi * frac) * math.sin(math.pi * t)
        return v3(x, y, z)
    loft(shell, name, A, 14, 4, region, th=0.035, overlap=0.05)
    pd.valance(shell, name + "_val_front", (x0, EY, z1 + 0.02), (x1, ye, z1 + 0.02), Z, h=0.72, region="pd_valance_aw", tab_len=1.2, droop=0.06)
    pd.valance(shell, name + "_val_out", (x1 + sx * 0.02, ye, z1), (x1 + sx * 0.02, ye, z0), v3(sx, 0, 0), h=0.72, region="pd_valance_aw", tab_len=1.3,
               droop=0.06)
    # a canvas wall at the back of the awning
    pd.wall(shell, name + "_wall", (x_out, 0, AZ0 - 0.06), (sx * HW, 0, AZ0 - 0.06), 0.0, fb - 0.12, -Z, region="pd_wall", nx=4, fold=0.05, flare=0.12)
    lo, hi = min(x_out, sx * HW), max(x_out, sx * HW)
    collide((lo, 0.0, AZ0 - 0.2, hi, fb - 0.12, AZ0 - 0.02))
    return ye


def build(atlas, decor):
    rng = random.Random(97)
    root = Bone(NAME)
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)

    # ---- the four tall corner posts, eave beams, side tie beams, braces, king posts, the curved ridge pole
    corners = [(-HW, ZF), (HW, ZF), (HW, ZB), (-HW, ZB)]   # FL, FR, BR, BL
    tops = []
    for k, (x, z) in enumerate(corners):
        tip = pd.post(shell, det, "post_%d" % k, x, z, POST_TOP, d=0.46, foot=(0.7, 0.68), bands=(1.3, 2.6, EAVE - 0.05, POST_TOP - 0.62),
                      collide_top=EAVE, cap_w=0.56, tall=1.25, cap_region="pd_finial")
        tops.append(v3(x, POST_TOP + 0.08, z))
        pd.rope_wrap(det, "post_coil_%d" % k, x, z, POST_TOP - 0.36, 0.23, turns=1)
        pd.rope_wrap(det, "post_coil_low_%d" % k, x, z, EAVE + 0.32, 0.23, turns=2)
    by = EAVE - 0.26
    for k in range(4):
        (xa, za), (xb, zb) = corners[k], corners[(k + 1) % 4]
        beam(shell, "eave_%d" % k, (xa, by, za), (xb, by, zb), 0.26, {"all": "pd_post", "+1": "end_grain", "-1": "end_grain"}, width=0.24, extend=0.18)
    for k, x in enumerate((-HW + 0.75, HW - 0.75, -0.6, 0.6)):
        box(det, "eave_strap_%d" % k, (x - 0.06, by - 0.16, ZF - 0.15), (x + 0.06, by + 0.16, ZF + 0.15), "iron")
    for k, (p, q) in enumerate((((-HW + 0.2, EAVE - 1.2, ZF), (-HW + 1.0, by - 0.12, ZF)), ((HW - 0.2, EAVE - 1.2, ZF), (HW - 1.0, by - 0.12, ZF)),
                                ((-HW, EAVE - 1.2, ZB + 0.2), (-HW, by - 0.12, ZB + 1.0)), ((HW, EAVE - 1.2, ZB + 0.2), (HW, by - 0.12, ZB + 1.0)))):
        beam(shell, "brace_%d" % k, p, q, 0.16, "wood_dark", extend=0.05)
    for k, sx in enumerate((-1, 1)):
        x = sx * HW
        beam(shell, "king_%d" % k, (x, by + 0.12, ZR), (x, RY_END - 0.15, ZR), 0.2, "wood_dark")
    pts = [v3(x, ridge_y(x) - 0.14, ZR) for x in np.linspace(-W, W, 7)]
    for i in range(6):
        beam(shell, "ridge_pole_%d" % i, pts[i], pts[i + 1], 0.2, "wood_dark", extend=0.05)
    # inside: rafters under the cloth in the middle, the hanging rail of the lanterns
    for k, x in enumerate((-1.3, 1.3)):
        for j, sg in enumerate((1, -1)):
            ps = []
            for t in (0.05, 0.4, 0.75, 0.93):
                p = front_at(x, t) - UP * 0.17
                ps.append(v3(p[0], p[1], ZR + sg * (p[2] - ZR)))
            for i in range(3):
                beam(shell, "rafter_%d_%d_%d" % (k, j, i), ps[i], ps[i + 1], 0.12, "wood_dark", extend=0.03)

    # ---- the roof: two faces, the striped gables, the ridge cover, the stepped valance
    pd.loft_down(shell, "roof_front", FRONT, 2 * STRIPES, 5, "pd_roof", th=0.04, overlap=0.05)
    pd.loft_down(shell, "roof_back", roof_face(-1), 2 * STRIPES, 5, "pd_roof", th=0.04, overlap=0.05)
    for k, sx in enumerate((-1, 1)):
        ml.plate(shell, "gable_%d" % k, (sx * (W - 0.02), (EY + RY_END) / 2, ZR), 2 * D, RY_END - EY, "pd_gable", normal=(sx, 0, 0), th=0.02)
    rc = [v3(x, ridge_y(x) + 0.02, ZR) for x in np.linspace(-W, W, 9)]
    for i in range(8):
        beam(shell, "ridge_cover_%d" % i, rc[i], rc[i + 1], 0.06, "pd_post", width=0.16, extend=0.04)
    pd.valance(shell, "valance_front", (-W - 0.02, EY, ZF + OV + 0.02), (W + 0.02, EY, ZF + OV + 0.02), Z, h=0.75, region="pd_valance", droop=DROOP,
               tab_len=1.0)
    pd.valance(shell, "valance_back", (W + 0.02, EY, ZB - OV - 0.02), (-W - 0.02, EY, ZB - OV - 0.02), -Z, h=0.75, region="pd_valance", droop=DROOP,
               tab_len=1.0)

    # ---- the raised middle: two small posts on the ridge, the crossbar, finials, the big scales banner down the slope
    yc = RY_MID + 0.42
    # (as in the picture: the crossbar sits right on the raised middle, its two ends capped in gold with small upright
    # knob finials; the short posts under it stop at the bar)
    for k, x in enumerate((-0.62, 0.62)):
        beam(shell, "peak_post_%d" % k, (x, ridge_y(x) - 0.2, ZR), (x, yc - 0.06, ZR), 0.16, {"all": "pd_post", "+1": "end_grain", "-1": "end_grain"})
    beam(shell, "peak_bar", (-0.85, yc, ZR + 0.02), (0.85, yc, ZR + 0.02), 0.13, {"all": "pd_post", "+1": "end_grain", "-1": "end_grain"})
    for k, x in enumerate((-0.86, 0.86)):
        add_cube(shell, "peak_bar_cap_%d" % k, (x, yc, ZR + 0.02), EYE, (0.2, 0.2, 0.2), "pd_finial")
        pd.finial(shell, det, "peak_fin_%d" % k, x, yc + 0.1, ZR + 0.02, w=0.22, tall=0.85, cap_region="pd_finial")
    bw, blen = 1.05, 1.95
    path = [v3(0, yc - 0.04, ZR + 0.1), v3(0, RY_MID + 0.1, ZR + 0.1)]
    for t in np.linspace(0.04, 0.9, 12):
        path.append(front_at(0.0, t) + front_normal(0.0, t) * 0.08)
    seg = [np.linalg.norm(path[i + 1] - path[i]) for i in range(len(path) - 1)]
    cum = np.concatenate([[0.0], np.cumsum(seg)])

    def along(L):
        L = min(L, cum[-1])
        i = min(int(np.searchsorted(cum, L, side="right")) - 1, len(seg) - 1)
        f = (L - cum[i]) / max(seg[i], 1e-6)
        return path[i] + (path[i + 1] - path[i]) * f

    loft(shell, "peak_banner", lambda s, t: along(t * blen) + X * ((s - 0.5) * bw), 1, 6, "pd_banner_peak", th=0.02, u_hint=X)
    for k, x in enumerate((-bw / 2 + 0.1, bw / 2 - 0.1)):
        add_cube(det, "peak_ring_%d" % k, (x, yc - 0.02, ZR + 0.1), EYE, (0.07, 0.14, 0.07), "iron")
    # thick ropes: front posts up to the crossbar, front posts down to the side awnings' front posts; tassels
    for k, sx in enumerate((-1, 1)):
        ml.rope(det, "peak_rope_%d" % k, tops[0 if sx < 0 else 1], (sx * 0.9, yc, ZR + 0.02), d=0.1, sag=0.18, segs=5)

    # ---- the side awnings
    ye_l = awning(shell, det, "awn_l", -1, LX, L_OUT)
    ye_r = awning(shell, det, "awn_r", 1, RX, R_OUT)
    # short brackets from the tall front posts' tops back over the gable ends (the beam at the top of the picture's gable)
    for k, sx in enumerate((-1, 1)):
        beam(shell, "gable_bracket_%d" % k, (sx * HW, POST_TOP - 0.42, ZF), (sx * HW, POST_TOP - 0.42, ZF - 0.9), 0.22, {"all": "pd_post",
             "+1": "end_grain", "-1": "end_grain"}, extend=0.12)
        beam(det, "gable_bracket_brace_%d" % k, (sx * HW, POST_TOP - 1.05, ZF - 0.1), (sx * HW, POST_TOP - 0.5, ZF - 0.75), 0.12, "wood_dark")
    for k, (sx, xo, yo) in enumerate(((-1, LX, L_OUT), (1, RX, R_OUT))):
        a = tops[0 if sx < 0 else 1]
        b = v3(xo, yo + 0.5, AZ1)
        ml.rope(det, "side_rope_%d" % k, a, b, d=0.09, sag=0.35, segs=6)
        pd.tassel(det, "tassel_out_%d" % k, b + v3(sx * 0.2, -0.05, 0.1), length=0.55)
        pd.tassel(det, "tassel_in_%d" % k, a + v3(sx * 0.25, -0.35, 0.12), length=0.75)

    # ---- the three banners under the front eave
    for k, (x, w, h, reg) in enumerate(((-1.75, 0.6, 1.3, "pd_banner"), (0.45, 0.78, 1.32, "pd_banner_mid"), (3.05, 0.52, 1.12, "pd_banner"))):
        top_y = by - 0.06 if k < 2 else R_OUT - 0.32
        zb = ZF + 0.17 if k < 2 else AZ1 + 0.2
        ml.banner(shell, "eave_banner_%d" % k, (x, top_y, zb), w, h, normal=(0, 0, 1), region=reg, rod=True, wave=0.03, rod_region="pd_post",
                  knobs="pd_finial")

    # ---- walls: the back wall, the back half of the sides (canvas)
    wy = by - 0.14
    pd.wall(shell, "wall_back", (HW, 0, ZB - 0.07), (-HW, 0, ZB - 0.07), 0.0, wy, -Z, region="pd_wall", nx=6, fold=0.05, flare=0.12)
    collide((-HW, 0.0, ZB - 0.2, HW, wy, ZB - 0.03))
    for k, sx in enumerate((-1, 1)):
        x = sx * (HW + 0.06)
        pd.wall(shell, "wall_side_%d" % k, (x, 0, ZB), (x, 0, AZ0 - 0.06), 0.0, wy, v3(sx, 0, 0), region="pd_wall", nx=2, fold=0.04)
        collide((x - 0.06, 0.0, ZB, x + 0.06, wy, AZ0))

    # ---- lanterns: hanging at the front left inside, and from the ridge pole at the back
    ml.lantern(shell, "lamp_front", (-1.0, 2.5, ZF - 0.02), size=0.38, metal="iron", chain_to=(-1.0, by - 0.13, ZF - 0.02))
    ml.lantern(shell, "lamp_back", (1.2, 2.55, ZR - 0.2), size=0.34, metal="iron", chain_to=(1.2, ridge_y(1.2) - 0.3, ZR - 0.2))

    # ---- the counter along the front with its runner and goods
    cx0, cx1, cz0, cz1 = COUNTER
    top = ml.counter(shell, "counter", cx0, cx1, cz0, cz1, h=COUNTER_H, detail=det)
    y = top[1]
    box(shell, "counter_cloth", (-0.35, y, cz1 - 0.45), (1.25, y + 0.015, cz1 + 0.05), {"all": "cloth_red"}, stretch=True, u_dir=X)
    ml.plate(shell, "runner", (0.45, y - 0.44, cz1 + 0.06), 1.6, 0.9, "pd_runner", normal=(0, 0, 1), th=0.012, edge="cloth_red")
    # the cream cloth on the counter top dripping over its front edge in gold-edged points (picture)
    box(shell, "counter_top_cloth", (cx0 - 0.05, y, cz0 + 0.1), (cx1 + 0.05, y + 0.012, cz1 + 0.05), {"all": "pd_cream"}, stretch=True, u_dir=X)
    ml.plate(shell, "counter_drip", ((cx0 + cx1) / 2, y - 0.1, cz1 + 0.05), cx1 - cx0 + 0.1, 0.22, "pd_drip", normal=(0, 0, 1), th=0.01)
    zc = (cz0 + cz1) / 2
    for k, (x, col, h) in enumerate(((-1.15, "green", 0.24), (-0.92, "orange", 0.2), (-0.7, "red", 0.17))):
        ml.bottle(det, "bottle_%d" % k, (x, y, zc + 0.05 * (k % 2)), col, r=0.065, h=h, shape="tall" if k != 1 else "round", neck_h=0.09)
    pd.open_book(det, "book", (-0.18, y + 0.015, zc + 0.05), yaw=0.08)
    pd.scroll(det, "counter_scroll", (0.42, y + 0.06, zc - 0.05), length=0.48, r=0.065, yaw=0.15)
    box(det, "blue_book", (0.62, y, zc - 0.05), (0.92, y + 0.08, zc + 0.18), {"all": "cloth_blue", "+2": "cloth_blue", "-2": "white"})
    box(det, "blue_book_clasp", (0.74, y + 0.08, zc - 0.05), (0.8, y + 0.085, zc + 0.18), "gold")
    pd.scroll(det, "counter_scroll_2", (0.78, y + 0.13, zc + 0.05), length=0.36, r=0.055, yaw=-0.3)
    ml.crate(det, "counter_box", (1.3, y, zc), size=(0.36, 0.2, 0.3), yaw=-0.15, solid=False)

    # ---- the back shelves: bottles and potions, two sacks on top
    levels = ml.shelf_unit(shell, "shelves", -HW + 0.45, HW - 0.45, ZB + 0.15, ZB + 0.65, levels=(0.55, 1.15, 1.75, 2.35), h=2.65,
                           back=True, uprights=4, detail=det)
    cols = ("green", "red", "orange", "green", "red", "cyan", "orange", "green", "red")
    for j, (x0, x1, yy, zf, zb_) in enumerate(levels):
        zc2 = (zf + zb_) / 2
        if j in (1, 2):
            n = 11
            for i in range(n):
                xx = x0 + 0.15 + (x1 - x0 - 0.3) * i / (n - 1)
                tall = i % 3 != 1
                ml.bottle(det, "pot_%d_%d" % (j, i), (xx, yy, zc2 + 0.05 * ((i % 2) - 0.5)), cols[(i + 2 * j) % len(cols)], r=0.07,
                          h=0.26 if tall else 0.18, shape="tall" if tall else "round", neck_h=0.1 if tall else 0.06)
        elif j == 3:
            ml.sack(det, "top_sack_0", (x1 - 0.5, yy, zc2), s=0.42, yaw=0.2, region="pd_burlap")
            ml.sack(det, "top_sack_1", (x1 - 1.0, yy, zc2), s=0.38, yaw=-0.3, region="pd_burlap")
            for i in range(5):
                ml.bottle(det, "jar_%d" % i, (x0 + 0.2 + 0.28 * i, yy, zc2), ("orange", "green", "red")[i % 3], r=0.09, h=0.2, shape="round",
                          neck_h=0.05)
        else:
            for i, (dx, reg) in enumerate(((0.3, "cloth_red"), (0.55, "cloth_beige"), (0.8, "cloth_blue"))):
                pd.scroll(det, "roll_%d" % i, (x0 + dx, yy + 0.09, zc2), length=0.42, r=0.085, yaw=math.pi / 2, region=reg)
            ml.crate(det, "low_box", (x1 - 0.7, yy, zc2), size=(0.5, 0.34, 0.38), solid=False)
            decor.block("farmhouse_decorations:pile_of_books", x0 + 1.9, yy, zc2, facing="front", scale=1.0, fallback="leather", solid=False)

    # ---- the rug in front of the counter
    ml.rug(shell, "rug", RUG[0], RUG[1], RUG[2], RUG[3], y=0.0, region="pd_rug")

    # ---- under the left awning: produce
    ml.crate(shell, "l_big_crate", (-3.85, 0.0, 1.2), size=0.95, yaw=0.05, solid=True)
    for j, s_ in enumerate((-1, 1)):
        add_cube(det, "l_big_crate_band_%d" % j, (-3.85 + s_ * 0.3, 0.475, 1.2), ry(0.05), (0.07, 0.97, 0.97), "iron")
    ml.crate(shell, "l_apples", (-3.85, 0.95, 1.22), size=(0.86, 0.36, 0.66), yaw=0.05, content="apples", solid=True)
    decor.block("furnish:spruce_crate", -4.0, 0.0, 0.05, facing="front", scale=0.95, alt="minecraft:barrel", fallback="crate")
    decor.block("farmersdelight:tomato_crate", -4.2, 0.95, 0.1, facing="front", scale=0.5, fallback="pd_fb_orange")
    decor.block("farmersdelight:cabbage_crate", -3.75, 0.95, 0.15, facing="front", scale=0.44, fallback="pd_fb_green")
    ml.crate(shell, "l_lav_crate", (-3.05, 0.0, 0.55), size=0.62, yaw=-0.1, solid=True)
    pd.flower_box(shell, det, "lavender", (-3.05, 0.62, 0.55), w=0.55, d=0.45, h=0.36, yaw=-0.1, flowers="pd_lavender", fh=0.62, solid=True)
    ml.crate(shell, "l_grain_crate", (-3.1, 0.0, 2.15), size=(0.72, 0.72, 0.62), yaw=0.08, content="pd_grain", solid=True)
    for j, s_ in enumerate((-1, 1)):
        add_cube(det, "l_grain_band_%d" % j, (-3.1, 0.36 + s_ * 0.24, 2.15), ry(0.08), (0.74, 0.06, 0.64), "iron")
    add_cube(det, "l_grain_heap", (-3.1, 0.76, 2.15), ry(0.3), (0.42, 0.1, 0.36), "pd_grain", stretch=True)
    decor.block("farmersdelight:rice_bag", -4.7, 0.0, 1.35, facing="front", scale=0.78, fallback="pd_burlap")
    decor.block("farmersdelight:rice_bag", -4.72, 0.0, 0.45, facing="pos_x", scale=0.7, fallback="pd_burlap")
    ml.barrel(shell, "barrel", (-1.95, 0.0, 2.62), r=0.36, h=0.92)

    # ---- under the right awning: crates and chests
    ml.crate(shell, "r_big_crate", (3.5, 0.0, 0.3), size=0.9, yaw=-0.06, solid=True)
    for j, s_ in enumerate((-1, 1)):
        add_cube(det, "r_big_crate_band_%d" % j, (3.5 + s_ * 0.28, 0.45, 0.3), ry(-0.06), (0.07, 0.92, 0.92), "iron")
    pd.chest(shell, det, "r_chest_top", (3.5, 0.9, 0.3), w=0.8, d=0.56, h=0.58, yaw=-0.06)
    collide((3.1, 0.9, 0.02, 3.9, 1.48, 0.58))
    pd.chest(shell, det, "r_gem_chest", (3.55, 0.0, 1.45), w=0.82, d=0.56, h=0.5, yaw=0.04)
    add_cube(det, "r_gems", (3.55, 0.52, 1.45), ry(0.04), (0.66, 0.08, 0.42), "pd_gems", stretch=True)
    collide((3.13, 0.0, 1.16, 3.97, 0.6, 1.74))
    decor.block("furnish:spruce_crate", 4.4, 0.0, 0.55, facing="front", scale=0.85, alt="minecraft:barrel", fallback="crate")
    decor.block("mebahelcreaturesdwarven:dwemer_chest", 4.4, 0.85, 0.55, facing="front", scale=0.62, alt="minecraft:chest", fallback="pd_chest")
    ml.crate(shell, "r_crate_small", (4.35, 0.0, 1.55), size=(0.6, 0.5, 0.55), yaw=0.15, solid=True)
    ml.sack(shell, "r_sack", (4.35, 0.5, 1.55), s=0.42, yaw=0.4, region="pd_burlap")
    ml.crate(det, "r_box", (2.95, 0.0, 2.35), size=(0.42, 0.32, 0.38), yaw=-0.25, solid=False)
    return root


def item_icon(path):
    """16x16: the striped gabled pavilion between its two tall posts with finials, the scales banner at the peak, the
    side awnings sweeping out to their posts, the gold dagged valance, the dark inside with the counter and runner."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    red, cream, gold, dark = PAL.red, PAL.cream, PAL.gold, (40, 26, 16)
    wood, wood_d = (132, 80, 40), (88, 52, 24)

    def put(x, y, c):
        if 0 <= x < 16 and 0 <= y < 16:
            p[x, y] = tuple(c) + (255,)
    for y in range(2, 8):          # the main roof: from the raised middle down to the eave, in stripes
        x0, x1 = 4 - (y - 2) // 3, 11 + (y - 2) // 3
        for x in range(x0, x1 + 1):
            put(x, y, red if (x // 1) % 2 == 0 else cream)
    for x in range(6, 10):         # the raised middle
        put(x, 1, red if x % 2 == 0 else cream)
    for y in range(0, 6):          # the peak banner
        put(7, y, red)
        put(8, y, red)
    put(6, 0, gold)
    put(9, 0, gold)
    put(7, 2, gold)
    put(8, 2, gold)
    put(7, 3, gold)
    for x in range(0, 4):          # the side awnings sweeping out
        y = 4 + x * 0 + (3 - x) // 2 + 1
        for yy in range(y, 8):
            put(x, yy, red if x % 2 == 0 else cream)
            put(15 - x, yy, red if x % 2 else cream)
    for x in range(0, 16):         # the valance all along the front: stripes, gold dags
        put(x, 8, red if x % 2 == 0 else cream)
        if x % 2 == 0:
            put(x, 9, gold)
    for y in range(10, 15):        # the dark inside
        for x in range(4, 12):
            put(x, y, dark)
    for x in range(5, 11):         # the counter and its runner
        put(x, 12, (172, 116, 60))
        put(x, 13, wood_d)
        put(x, 14, wood_d)
    put(8, 13, red)
    put(8, 14, red)
    put(9, 13, red)
    put(6, 11, (240, 200, 80))     # the lantern
    for x in (3, 12):              # the tall posts and their finials
        put(x, 0, gold)
        for y in range(1, 16):
            put(x, y, wood)
        put(x, 4, (190, 160, 110))  # a rope coil
    for x in (0, 15):              # the awning posts
        for y in range(9, 16):
            put(x, y, wood_d)
    put(1, 14, (210, 70, 40))      # produce, a chest
    put(2, 14, (90, 160, 50))
    put(13, 14, (150, 96, 40))
    put(14, 14, (220, 170, 60))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)


SHIFT = None


def main():
    global SHIFT
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="red")
    add_regions(atlas)
    decor = ml.Decor()
    root = build(atlas, decor)
    SHIFT = pd.centre_offsets(root, decor)
    pd.shift_all(root, decor, *SHIFT)
    print("shift %.2f %.2f -> NPC place x %.2f..%.2f z %.2f..%.2f" % (SHIFT[0], SHIFT[1], NPC[0] + SHIFT[0], NPC[0] + SHIFT[0] + 1,
                                                                      NPC[1] + SHIFT[1], NPC[1] + SHIFT[1] + 1))
    ml.export(root, NAME, atlas, decor=decor, icon=item_icon, light=12)


if __name__ == "__main__":
    main()
