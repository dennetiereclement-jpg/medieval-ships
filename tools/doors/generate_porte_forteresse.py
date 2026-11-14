#!/usr/bin/env python3
"""porte_forteresse (1.31.0): massive fortress double door, 4 high x 2 wide. References: ref1 top row 4th (stone
arch with moss and vines, arched oak leaves banded with riveted iron, ring handles), ref4 "4x2" 1st (big hinge
straps, round rings), ref5 row 2 1st.

    python3 tools/doors/generate_porte_forteresse.py [--preview]

The stone frame (jambs, voussoirs, keystone, masonry filling the upper corners) is front-only (Z [2, 8]) except
its outer 2 px, so the leaves turned 90 degrees towards the back never go through it.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doorlib_medium as dm  # noqa: E402
from doorlib_medium import rgb, shade, mix  # noqa: E402

WOOD = rgb("8e5326")
WOOD_D = rgb("3e210c")
BACK = rgb("74431f")
IRON = rgb("4f4f56")
IRON_L = rgb("a6a6ae")
STONE = rgb("8f8d88")
WALL = rgb("6f6d69")
MOSS = [rgb("4f8a22"), rgb("6aa82c"), rgb("3a6a1a"), rgb("86c03a")]

SPRING, A, B = 47.0, 12.0, 10.0      # the arch of the opening: half-ellipse centre (0, SPRING), half axes A, B
RING = 1.55                          # outer edge of the voussoirs (in units of the ellipse)
NV = 7                               # voussoirs (the middle one is the keystone)


def leaf_top(x):
    t = min(1.0, abs(x) / A)
    return SPRING + B * math.sqrt(max(0.0, 1 - t * t))


def labels():
    """Stone labels of the frame picture (64 x 32, row 0 = top): -1 opening, 0 mortar, >0 stone ids; and kinds."""
    lab = -np.ones((64, 32), int)
    kind = {}
    nid = [0]

    def new(k):
        nid[0] += 1
        kind[nid[0]] = k
        return nid[0]
    jamb_ids, ring_ids, wall_ids = {}, {}, {}
    for j in range(64):
        Y = 63 - j
        yc = Y + 0.5
        for i in range(32):
            X = i - 16
            xc = X + 0.5
            if abs(xc) < A and yc < leaf_top(xc):
                continue
            dx, dy = xc / A, (yc - SPRING) / B
            r = math.hypot(dx, dy)
            if yc >= SPRING - 0.01 and r < RING:
                th = math.atan2(dy, dx)
                f = th / (math.pi / NV)
                k = int(f)
                k = min(NV - 1, max(0, k))
                near = min(f - k, k + 1 - f) * (math.pi / NV) * r * A
                if (near < 0.5 and 0 < f < NV) or abs(r - RING) < 0.08:
                    lab[j, i] = 0
                    continue
                lab[j, i] = ring_ids.setdefault(k, new("ring"))
                continue
            if abs(xc) < 3.2 and yc > SPRING + B:
                lab[j, i] = ring_ids.setdefault(NV // 2, new("ring"))
                continue
            if abs(xc) >= A and yc < SPRING + 1:
                course = int(Y // 7)
                if Y % 7 == 6:
                    lab[j, i] = 0
                    continue
                side = 0 if X < 0 else 1
                lab[j, i] = jamb_ids.setdefault((side, course), new("jamb"))
                continue
            # masonry of the upper corners: small courses
            course = int((Y - 1) // 5)
            off = 4 if course % 2 else 0
            col = int((X + 16 + off) // 8)
            if (Y - 1) % 5 == 4 or (X + 16 + off) % 8 == 7:
                lab[j, i] = 0
                continue
            lab[j, i] = wall_ids.setdefault((course, col), new("wall"))
    # the keystone: the middle voussoir up to the top
    return lab, kind

ICON = [
    ".....SSSSSS.....",
    "..SSSsSSSSsSSS..",
    ".SGSsSIIIIsSGSS.",
    "SGSsIIWWWWIIsSGS",
    "SGSsIWWIIWWIsSGS",
    "SSSIIWWIIWWIIGSS",
    "GSSIWWWIIWWWISSs",
    "SsSIIIIIIIIIISsS",
    "SSGIWWWIIWWWIGSS",
    "SsSIWWRIIRWWISsS",
    "SSSIWRWRRWRWIGSS",
    "SGSIIIIIIIIIISsS",
    "SSsIWWWIIWWWISSS",
    "SsSIWWWIIWWWISsS",
    "SSSIIIIIIIIIISSS",
    "SsSIIIIIIIIIISsS",
]
ICON_PAL = {"S": rgb("9a9893"), "s": rgb("6a6864"), "G": rgb("5a9a26"), "I": rgb("4c4c54"), "W": rgb("8e5326"), "R": rgb("b0b0b8")}


def build():
    d = dm.Door("porte_forteresse", post=4, top=int(SPRING), seed=23)
    F, B_ = d.F, d.B
    d.material("wood_side", dm.tile_wood(shade(WOOD, 0.85)))
    d.material("stone_side", dm.tile_stone(STONE), 32, 32)
    d.material("iron_side", dm.tile_metal(IRON), 32, 32)
    d.material("ring_side", dm.tile_metal(shade(IRON, 0.75)), 16, 16)
    d.material("batten", lambda c: c.planks_h(0, 0, c.w, c.h, [c.h], shade(BACK, 1.05), joints=0), 64, 3)
    d.material("moss_side", lambda c: c.rect(0, 0, c.w, c.h, MOSS[0], noise=14), 16, 16)
    rng = np.random.default_rng(5)

    lab, kind = labels()
    for P, base, dark in ((F, WOOD, WOOD_D), (B_, BACK, shade(BACK, 0.45))):
        for x0 in (-12, 0):
            P.planks_v(x0, 0, x0 + 12, 58, [3, 3, 3, 3], base, dark, knots=0.06, joints=0.2)
    # ------------------------------------------------------------ stone pictures (front and back)
    for P, k in ((F, 1.0), (B_, 0.82)):
        for kd, col in (("jamb", STONE), ("ring", shade(STONE, 1.06)), ("wall", WALL)):
            sub = lab.copy()
            for sid, kk in kind.items():
                if kk != kd:
                    sub[sub == sid] = -1
            sub[(lab == 0)] = -1
            P.stone_wall(sub, -16, 0, shade(col, k), seed_k=0.04)
        m = lab == 0
        for j, i in zip(*np.nonzero(m)):
            P.put(i - 16, 63 - j, shade(rgb("57534f"), k) + P.rng.normal(0, 3))
    # moss and vines on the front (ref1: along both sides of the arch and down the jambs)
    for j in range(64):
        Y = 63 - j
        for i in range(32):
            X = i - 16
            if lab[j, i] < 0:
                continue
            side_l = X < -6
            side_r = X > 7
            hi = Y > 44
            p = 0.0
            if hi and (side_l or side_r):
                # moss grows on the inner edge of the arch and the tops of the stones
                inner = lab[min(63, j + 1), i] < 0 or lab[min(63, j + 2), i] < 0 or lab[j, min(31, i + 1)] < 0 or lab[j, max(0, i - 1)] < 0
                top_edge = j > 0 and lab[j - 1, i] != lab[j, i]
                p = (0.55 if inner else 0.12 if top_edge else 0.02) * (1.0 if side_l else 0.7)
            if rng.random() < p:
                F.put(X, Y, MOSS[int(rng.integers(0, 4))])
    # hanging vines: wiggly strands down the inner edge of the jambs and the outer edge of the left one
    for x0, y0, y1 in ((-13, 50, 14), (-15, 46, 30), (13, 52, 26), (14, 44, 4), (-12.0, 30, 2)):
        x = x0
        for Y in range(int(y0), int(y1), -1):
            x += rng.choice([-0.4, 0, 0, 0.4])
            xi = int(round(min(15, max(-16, x))))
            if lab[63 - Y, xi + 16] >= 0:
                F.put(xi, Y, MOSS[int(rng.integers(0, 3))])
                if rng.random() < 0.3 and lab[63 - Y, min(31, xi + 17)] >= 0:
                    F.put(xi + 1, Y, MOSS[3])

    # ------------------------------------------------------------ stone cubes
    # Front layer: every stone its own depth (voussoirs and keystone stand out most), mortar recessed; behind it
    # the masonry runs through the whole thickness wherever the leaves never pass (the rebate next to the hinges
    # and the vault swept by the arched leaves stay empty), so the arch is solid and no daylight shows between
    # the stones from any side.
    fr = d.frame
    zf = {}
    for sid, kd in kind.items():
        zf[sid] = (7.5 + 0.5 * (sid % 2 == 0 and sid in (max(kind),))) if kd == "ring" else (6.75 + 0.5 * (sid % 2)) if kd == "jamb" else 6.0 + 0.25 * (sid % 3)
    key = None
    for sid, kd in kind.items():
        if kd == "ring":
            ys = np.nonzero(lab == sid)[0]
            if len(ys) and (key is None or ys.min() < key[1]):
                key = (sid, ys.min())
    zf[key[0]] = 8.0
    ZB = 2.75                                      # back of the front layer (in front of the leaves' relief)
    for sid in kind:
        m = lab == sid
        if not m.any():
            continue
        d.mask_boxes(fr, "stone_%d" % sid, m, -16, 0, ZB, zf[sid], side="stone_side")
    d.mask_boxes(fr, "mortar", lab == 0, -16, 0, ZB, 5.25, side="stone_side")
    # behind: outer 1.5 px of the jambs full depth, then the vault above the swept volume
    for s_ in (-1, 1):
        d.box(fr, "outer_%d" % s_, 16 * s_, 14.5 * s_, 0, 64, -8, ZB, front=None, side="stone_side")
    hs = d.swept_heights(leaf_top, X0=-14.5, X1=14.5, Z0=-8.0, Z1=ZB, step=0.5)
    nx, nz = hs.shape
    for i in range(0, nx, 2):                       # 1 px columns
        col = np.maximum(hs[i], hs[min(nx - 1, i + 1)])
        # bottom of the masonry per 1 px slab of depth: above the highest leaf point + GAP, at least the leaf top
        X = -14.5 + i * 0.5
        bots = []
        for k in range(0, nz, 2):
            h = max(col[k], col[min(nz - 1, k + 1)])
            bots.append(max(0.0, math.ceil((h + dm.GAP) * 4) / 4) if h > 0 else 0.0)
        # monotonic towards the back (the face pairs between slabs then always cover one another)
        k = 0
        zs = [-8.0 + 1.0 * kk for kk in range(len(bots))] + [ZB]
        while k < len(bots):
            k1 = k + 1
            while k1 < len(bots) and abs(bots[k1] - bots[k]) < 1e-6:
                k1 += 1
            if bots[k] < 64 - 0.5:
                d.box(fr, "vault_%d_%d" % (i, k), X, min(14.5, X + 1), bots[k], 64, zs[k], min(ZB, zs[k1]), front=None,
                      back="back", side="stone_side")
            k = k1
    # a few tufts of moss standing out of the stones (detail)
    det = d.detail()
    for k, (x, y, w, h) in enumerate(((-11, 56, 2, 1), (-14, 51, 1, 2), (10, 55, 2, 1), (-13, 44, 1, 3), (13, 47, 1, 2))):
        sid = lab[63 - y, x + 16]
        z = zf.get(sid, 5.25)
        d.box(det, "moss_%d" % k, x + 0.25, x + w - 0.25, y + 0.25, y + h - 0.25, z - 0.5, min(8.0, z + 0.75), front="front",
              back=None, side="moss_side")

    # ------------------------------------------------------------ leaves
    lab2 = lab
    # iron on the front picture: arched border band, hinge-side and seam straps, three bands with big hinges
    band_ys = (8, 24, 40)
    for x0, s in ((-12, -1), (0, 1)):
        for X in range(x0, x0 + 12):
            top = int(math.floor(leaf_top(X + 0.5)))
            for Y in range(top - 2, top):
                F.put(X, Y, shade(IRON, 1.05 if Y == top - 1 else 0.9) + F.rng.normal(0, 3))
            if (X - x0) % 4 == 2:
                F.rivet(X, top - 2, light=IRON_L)
        hx0 = x0 if s < 0 else x0 + 10              # hinge-side strap
        F.strap_v(hx0, 0, int(leaf_top(hx0 + 1)) - 1, 2, IRON, light=IRON_L)
        sx0 = x0 + 10 if s < 0 else x0              # seam strap
        F.strap_v(sx0, 0, int(leaf_top(0)) - 1, 2, IRON, light=IRON_L)
        for y in band_ys:
            F.strap_h(x0, x0 + 12, y, 2, IRON, light=IRON_L)
            # big hinge plate near the hinge, pointed towards the seam
            for X in range(5):
                xx = x0 + X if s < 0 else x0 + 11 - X
                for Y in range(y - 1, y + 3):
                    F.put(xx, Y, shade(IRON, 0.95 + 0.05 * (Y == y + 2)) + F.rng.normal(0, 3))
            F.rivet(x0 + 1 if s < 0 else x0 + 10, y + 1, light=IRON_L)
            F.rivet(x0 + 3 if s < 0 else x0 + 8, y + 1, light=IRON_L)
        F.strap_h(x0, x0 + 12, 0, 2, IRON, light=IRON_L)
    for y in range(0, 58):
        if F.inside(0, y):
            F.scale_px(-1, y, 0.75)
    for leaf, x0, s in ((d.leaf_l, -12, -1), (d.leaf_r, 0, 1)):
        m = np.zeros((64, 12), bool)
        for i in range(12):
            top = leaf_top(x0 + i + 0.5)
            for j in range(64):
                if (63 - j) + 0.5 < top:
                    m[j, i] = True
        d.mask_boxes(leaf, "core", m, x0, 0, -1, 1, side="wood_side")
        # arched iron band (relief), following the top of the leaf
        band = np.zeros_like(m)
        for i in range(12):
            col = np.nonzero(m[:, i])[0]
            band[col[0]:col[0] + 2, i] = True
        d.mask_boxes(leaf, "arch_band", band, x0, 0, 1, 2.5, back=None, side="iron_side")
        hx0 = x0 if s < 0 else x0 + 10
        sx0 = x0 + 10 if s < 0 else x0
        top_h = int(leaf_top(hx0 + 1)) - 1
        d.box(leaf, "strap_hinge", hx0, hx0 + 2, 2, top_h - 1, 1, 2.5, back=None, side="iron_side")
        d.box(leaf, "strap_seam", sx0, sx0 + 2, 2, int(leaf_top(0)) - 2, 1, 2.5, back=None, side="iron_side")
        d.box(leaf, "band_0", x0, x0 + 12, 0, 2, 1, 2.5, back=None, side="iron_side")
        for k, y in enumerate(band_ys):
            d.box(leaf, "band_%d" % (k + 1), x0 + (2 if s < 0 else 0.75), x0 + (11.25 if s < 0 else 10), y, y + 2, 1, 2.75, back=None, side="iron_side")
            xa, xb = (x0 + 0.25, x0 + 5) if s < 0 else (x0 + 7, x0 + 11.75)
            d.box(leaf, "hinge_plate_%d" % k, xa, xb, y - 1, y + 3, 1, 3.0, back=None, side="iron_side")
            px = -12 if s < 0 else 12
            d.knuckle(leaf, "knuckle_%d" % k, px, y - 1, y + 3, "iron_side")
        # round ring handle near the seam (ref4), its own bone handle_0 / handle_1
        hx = -5 if s < 0 else 4
        dm.ring_handle(d, leaf, "ring", hx, 30, "ring_side", shade(IRON, 0.75), shade(IRON, 1.2), Z=2.5, size=5,
                       handle="handle_%d" % (0 if s < 0 else 1))
        # back: three heavy battens and a diagonal brace between the lower two
        for k, y in enumerate((4, 22, 40)):
            d.box(leaf, "batten_%d" % k, x0 + 0.5, x0 + 11.5, y, y + 4, -2.25, -1, front=None, back="batten", side="wood_side")
        a, b = ((x0 + 2, 9), (x0 + 10, 21)) if s < 0 else ((x0 + 10, 9), (x0 + 2, 21))
        d.strap(leaf, "brace", a, b, 3, -2, -1, "batten")
        d.box(leaf, "back_bar_hook", (x0 + 8.5) if s < 0 else (x0 + 1.5), (x0 + 10.5) if s < 0 else (x0 + 3.5), 30, 33, -2.75, -2.25,
              front="iron_side", back="iron_side", side="iron_side")
    d.material("seam_dark", dm.tile_flat(shade(WOOD_D, 0.7), 4), 16, 16)
    d.finalize(top_gap=False, seam_top=57, cover_side="wood_side", seam_mat="seam_dark")
    d.icon_map = (ICON, ICON_PAL)
    return d


REFS = [(dm.REF_DIR + "/ref1.png", (700, 100, 1005, 440)), (dm.REF_DIR + "/ref4.png", (485, 40, 820, 375)),
        (dm.REF_DIR + "/ref5.png", (65, 245, 325, 485))]

if __name__ == "__main__":
    d = build()
    d.export()
    for line in d.bones():
        print(line)
    if "--preview" in sys.argv:
        d.preview(dm.SCRATCH + "/doors_out2/medium_porte_forteresse.png", refs=REFS)
