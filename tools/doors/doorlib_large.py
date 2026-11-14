"""Shared helpers of the three LARGE doors (6 blocks high x 4 wide, two leaves): porte_chateau,
porte_vapeur_grande, porte_entrepot. Used by tools/doors/generate_<id>.py (the small / medium doors have their own
libraries, doorlib_small.py / doorlib_medium.py). Audited on export by tools/doors/door_audit_large.py.

    import doorlib_large as dl
    d = dl.LargeDoor("porte_chateau", jamb=6)     # own 256 px atlas; bones root > frame, leaf_l, leaf_r
    F, B = d.F, d.B                               # FRONT / BACK pictures of the whole door (16 px per block)
    F.planks_v(*F.R(-26, 0, 0, 80), widths, base, dark)   # paint in DOOR PIXELS (see below)
    d.material("iron_side", painter)              # 64 x 64 tiles for the side faces
    X0, X1 = d.leaf_x("l")                        # leaf body X range (GAP from the hinge and the seam)
    d.box(d.leaf_l, "body", X0, X1, dl.GAP, 80, -dl.BODY, dl.BODY, side="wood_side")
    sw = dl.Sweep(d)                              # where the leaves swing (frame parts above / beside them)
    d.jamb_courses(-1, courses)                   # jamb: front stop, middle, rear rebate for the hinges
    d.export(icon=painter16)                      # resolve() faces, bbmodel (models/entity + blockbench),
                                                  # texture, 16x16 icon, then the audit (must print DEFECTS = 0)
    d.preview(out_png, refs)                      # control sheet next to the reference crops

DOOR PIXELS. Every coordinate given to this library is in 1/16 block, in the contract's frame: X in [-32, 32]
(+X = right seen from the front), Y in [0, 96] (up), Z in [-8, 8] (+Z = the front face). The leaves stay within
Z in [-2, 2]; leaf_l pivots on its hinge edge X = -32 + jamb, leaf_r on X = 32 - jamb (Z = 0).

THE PROJECTION. The front picture F (64 x 96 px) is the whole door seen from the front: every +Z face of a box shows
the part of F in front of it. B is the door seen from behind, painted in door pixels too (B mirrors X internally).
Faces looking along X or Y use material tiles; small cut-out pictures (gears, banners, rings, flames) are sprites
on cubes named cut_* / glow_cut_* (the only cubes allowed to show transparent texels).

1.32.0 RULES (no air gap, no z-fighting): see LargeDoor.
"""
import copy
import json
import math
import os
import random
import sys
import zlib

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(TOOLS, "tents"))
sys.path.insert(0, TOOLS)
import tentlib as tl  # noqa: E402
import preview as pv  # noqa: E402
from galley_texture import paint_lamp_glass  # noqa: E402

gg, gn = tl.gg, tl.gn
Bone, EYE, v3 = tl.Bone, tl.EYE, tl.v3
ASSETS, ROOT = tl.ASSETS, tl.ROOT
SCRATCH = "/tmp/claude-0/-home-user-medieval-ships/2a9b6be4-7c0a-5b40-ad8d-40cfe82b9e67/scratchpad"
REF_DIR = os.path.join(SCRATCH, "doors_ref")
WPX, HPX = 64, 96          # the opening in door pixels
P = 1.0 / 16


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(int(round(a[k] + (b[k] - a[k]) * t)) for k in range(3))


def shade(c, k):
    return tuple(max(0, min(255, int(round(v * k)))) for v in c[:3])


# palette sampled on the reference sheets
WOOD, WOOD_L, WOOD_D = rgb("7a4422"), rgb("9a5a2c"), rgb("3b2211")
IRON, IRON_L, IRON_D = rgb("4d4447"), rgb("7e6b6d"), rgb("2a2427")
STONE, STONE_L, STONE_D = rgb("8b7f80"), rgb("a99d9c"), rgb("3c3536")
COPPER, COPPER_L, COPPER_D = rgb("b4693a"), rgb("e8944a"), rgb("5f2a14")
BRASS, BRASS_L, BRASS_D = rgb("b8862e"), rgb("ecc35a"), rgb("5e3f10")
RIVET_L, RIVET_D = rgb("d8d0cc"), rgb("241f22")


# ---------------------------------------------------------------- pixel painter
class Px:
    """Paints a w x h view (numpy float RGBA, j down). i1 / j1 are exclusive."""

    def __init__(self, arr, u0, v0, w, h, seed=1):
        self.a, self.u0, self.v0, self.w, self.h = arr, u0, v0, w, h
        self.rng = random.Random(seed)

    def put(self, i, j, c, a=255):
        i, j = int(i), int(j)
        if 0 <= i < self.w and 0 <= j < self.h:
            self.a[self.v0 + j, self.u0 + i] = (c[0], c[1], c[2], a)

    def get(self, i, j):
        i, j = min(self.w - 1, max(0, int(i))), min(self.h - 1, max(0, int(j)))
        return tuple(int(v) for v in self.a[self.v0 + j, self.u0 + i, :3])

    def jit(self, c, n):
        if n <= 0:
            return c
        d = self.rng.randint(-n, n)
        return tuple(max(0, min(255, v + d)) for v in c)

    def rect(self, i0, i1, j0, j1, c, noise=0, a=255):
        for j in range(int(j0), int(j1)):
            for i in range(int(i0), int(i1)):
                self.put(i, j, self.jit(c, noise), a)

    def clear(self, i0, i1, j0, j1):
        self.rect(i0, i1, j0, j1, (0, 0, 0), a=0)

    def planks_v(self, i0, i1, j0, j1, widths, base, dark, grain=0.10, knots=0.5, joints=False):
        """Vertical planks (grain along j): widths = list of plank widths in px (repeated)."""
        i, k = int(i0), 0
        while i < i1:
            pw = widths[k % len(widths)]
            tone = self.jit(base, 9)
            streaks = [self.rng.uniform(0.5, pw - 0.5) for _ in range(2)]
            ph = [self.rng.uniform(0, 6.3) for _ in range(2)]
            knot = (self.rng.uniform(1, pw - 1), self.rng.uniform(j0 + 3, j1 - 3)) if self.rng.random() < knots else None
            joint = self.rng.randint(int(j0) + 6, max(int(j0) + 7, int(j1) - 6)) if joints and j1 - j0 > 20 else None
            for di in range(pw):
                ii = i + di
                if ii >= i1:
                    break
                for j in range(int(j0), int(j1)):
                    if di == pw - 1:
                        c = dark
                    elif di == 0:
                        c = shade(tone, 1.10)
                    else:
                        kk = 1.0 + 0.05 * math.sin(j * 0.21 + ph[0])
                        for s, p in zip(streaks, ph):
                            if abs(di + 0.5 - (s + 0.6 * math.sin(j * 0.17 + p))) < 0.45:
                                kk -= grain
                        if knot and math.hypot(di + 0.5 - knot[0], (j - knot[1]) / 1.6) < 0.9:
                            kk -= 0.35
                        c = shade(tone, kk)
                    if joint is not None and j == joint and di < pw - 1:
                        c = mix(dark, tone, 0.3)
                    self.put(ii, j, self.jit(c, 3))
            i += pw
            k += 1

    def planks_h(self, i0, i1, j0, j1, heights, base, dark, grain=0.10, knots=0.3, outline=None):
        """Horizontal planks / a beam (grain along i)."""
        j, k = int(j0), 0
        while j < j1:
            ph_ = heights[k % len(heights)]
            tone = self.jit(base, 9)
            streaks = [self.rng.uniform(0.5, ph_ - 0.5) for _ in range(2)]
            ph = [self.rng.uniform(0, 6.3) for _ in range(2)]
            knot = (self.rng.uniform(i0 + 3, i1 - 3), self.rng.uniform(1, ph_ - 1)) if self.rng.random() < knots else None
            for dj in range(ph_):
                jj = j + dj
                if jj >= j1:
                    break
                for i in range(int(i0), int(i1)):
                    if dj == ph_ - 1:
                        c = dark
                    elif dj == 0:
                        c = shade(tone, 1.12)
                    else:
                        kk = 1.0 + 0.05 * math.sin(i * 0.19 + ph[0])
                        for s, p in zip(streaks, ph):
                            if abs(dj + 0.5 - (s + 0.6 * math.sin(i * 0.15 + p))) < 0.45:
                                kk -= grain
                        if knot and math.hypot((i - knot[0]) / 1.6, dj + 0.5 - knot[1]) < 0.9:
                            kk -= 0.35
                        c = shade(tone, kk)
                    self.put(i, jj, self.jit(c, 3))
            j += ph_
            k += 1
        if outline:
            self.outline(i0, i1, j0, j1, outline)

    def outline(self, i0, i1, j0, j1, c):
        for i in range(int(i0), int(i1)):
            self.put(i, j0, c)
            self.put(i, j1 - 1, c)
        for j in range(int(j0), int(j1)):
            self.put(i0, j, c)
            self.put(i1 - 1, j, c)

    def metal(self, i0, i1, j0, j1, base, noise=6, bevel=True, dents=True, rust=0.0):
        cells = [(self.rng.uniform(i0, i1), self.rng.uniform(j0, j1), self.rng.uniform(1.5, 3.0))
                 for _ in range(max(1, int((i1 - i0) * (j1 - j0) / 20)))] if dents else []
        for j in range(int(j0), int(j1)):
            for i in range(int(i0), int(i1)):
                k = 1.0
                for cx, cy, r in cells:
                    d = math.hypot(i + 0.5 - cx, j + 0.5 - cy)
                    if d < r:
                        k += 0.07 * ((j + 0.5 - cy) / r - (i + 0.5 - cx) / r * 0.4) * (1 - d / r)
                c = shade(base, k)
                if rust > 0 and self.rng.random() < rust:
                    c = mix(c, rgb("7a3a1c"), 0.45)
                self.put(i, j, self.jit(c, noise))
        if bevel and i1 - i0 >= 2 and j1 - j0 >= 2:
            for i in range(int(i0), int(i1)):
                self.put(i, j0, mix(self.get(i, j0), (235, 225, 225), 0.25))
                self.put(i, j1 - 1, shade(self.get(i, j1 - 1), 0.55))
            for j in range(int(j0), int(j1)):
                self.put(i0, j, mix(self.get(i0, j), (235, 225, 225), 0.18))
                self.put(i1 - 1, j, shade(self.get(i1 - 1, j), 0.6))

    def rivet(self, i, j, big=False, light=RIVET_L, dark=RIVET_D, mid=None):
        mid = mid or mix(light, dark, 0.45)
        if big:
            self.put(i, j, light)
            self.put(i + 1, j, mid)
            self.put(i, j + 1, mid)
            self.put(i + 1, j + 1, dark)
        else:
            self.put(i, j, light)
            self.put(i + 1, j + 1, dark)

    def rivets_h(self, i0, i1, j, step, big=False, **kw):
        n = max(1, int(round((i1 - i0) / step)))
        for k in range(n):
            self.rivet(int(i0 + (k + 0.5) * (i1 - i0) / n), j, big, **kw)

    def rivets_v(self, i, j0, j1, step, big=False, **kw):
        n = max(1, int(round((j1 - j0) / step)))
        for k in range(n):
            self.rivet(i, int(j0 + (k + 0.5) * (j1 - j0) / n), big, **kw)

    def stone(self, i0, i1, j0, j1, base=STONE, mortar=STONE_D, moss=0.0):
        """One dressed stone: speckled face, lit top/left edge, dark mortar line right/bottom."""
        tone = self.jit(base, 10)
        for j in range(int(j0), int(j1)):
            for i in range(int(i0), int(i1)):
                if i == i1 - 1 or j == j1 - 1:
                    c = mortar
                elif j == j0 or i == i0:
                    c = mix(tone, (230, 224, 220), 0.35)
                elif i == i1 - 2 or j == j1 - 2:
                    c = shade(tone, 0.82)
                else:
                    r = self.rng.random()
                    c = shade(tone, 0.88) if r < 0.18 else mix(tone, (220, 212, 210), 0.2) if r < 0.3 else tone
                    if moss > 0 and self.rng.random() < moss * (1 - (j - j0) / max(1, j1 - j0)):
                        c = rgb("5d7a2c")
                self.put(i, j, self.jit(c, 4))

    def glow(self, i0, i1, j0, j1, hot=(255, 236, 150), warm=(246, 160, 44), edge=(178, 88, 22)):
        ci, cj = (i0 + i1) / 2, (j0 + j1) / 2
        rr = max(1.0, min(i1 - i0, j1 - j0) / 2)
        for j in range(int(j0), int(j1)):
            for i in range(int(i0), int(i1)):
                d = math.hypot((i + 0.5 - ci) / max(1, (i1 - i0) / 2), (j + 0.5 - cj) / max(1, (j1 - j0) / 2))
                c = mix(hot, warm, min(1, d * 1.1)) if d < 0.9 else mix(warm, edge, min(1, (d - 0.9) * 2.5))
                self.put(i, j, c)
        del rr

    def disc(self, ci, cj, r, c, ring=None, noise=0, r_in=0.0):
        for j in range(int(cj - r - 1), int(cj + r + 2)):
            for i in range(int(ci - r - 1), int(ci + r + 2)):
                d = math.hypot(i + 0.5 - ci, j + 0.5 - cj)
                if r_in <= d <= r:
                    col = ring if (ring and d > r - 1.0) else c
                    self.put(i, j, self.jit(col, noise))

    def line(self, i0, j0, i1, j1, w, c, noise=0):
        L = max(1e-6, math.hypot(i1 - i0, j1 - j0))
        ux, uy = (i1 - i0) / L, (j1 - j0) / L
        for j in range(int(min(j0, j1) - w), int(max(j0, j1) + w + 1)):
            for i in range(int(min(i0, i1) - w), int(max(i0, i1) + w + 1)):
                px, py = i + 0.5 - i0, j + 0.5 - j0
                t = px * ux + py * uy
                d = abs(-px * uy + py * ux)
                if 0 <= t <= L and d <= w / 2:
                    self.put(i, j, self.jit(c, noise))


class Picture(Px):
    """A whole-door picture in door pixels: R(X0, X1, Y0, Y1) -> pixel rect (i0, i1, j0, j1); mirror for the back."""

    def __init__(self, arr, u0, v0, mirror=False, seed=1):
        super().__init__(arr, u0, v0, WPX, HPX, seed)
        self.mirror = mirror

    def R(self, X0, X1, Y0, Y1):
        if self.mirror:
            return (32 - X1, 32 - X0, HPX - Y1, HPX - Y0)
        return (X0 + 32, X1 + 32, HPX - Y1, HPX - Y0)

    def I(self, X):
        return (31 - X) if self.mirror else (X + 32)

    def J(self, Y):
        return HPX - 1 - Y

    def pt(self, X, Y):
        """Continuous pixel coordinates of the door point (X, Y)."""
        return ((32 - X) if self.mirror else (X + 32), HPX - Y)

    def snapshot(self):
        return self.a[self.v0:self.v0 + HPX, self.u0:self.u0 + WPX].copy()

    def restore(self, snap, mask):
        """Puts back the snapshot's pixels where mask(X, Y) (door pixels) is true."""
        for Y in range(HPX):
            for X in range(-32, 32):
                if mask(X, Y):
                    i, j = self.I(X), self.J(Y)
                    self.a[self.v0 + j, self.u0 + i] = snap[j, i]


# ---------------------------------------------------------------- atlas
class Atlas:
    def __init__(self, size):
        self.size = size
        self.arr = np.zeros((size, size, 4), dtype=float)
        self.x = self.y = self.shelf = 0
        self.regions = {}

    def alloc(self, name, w, h):
        if self.x + w > self.size:
            self.x, self.y, self.shelf = 0, self.y + self.shelf, 0
        if self.y + h > self.size:
            raise RuntimeError("atlas full (%s %dx%d): use a bigger size" % (name, w, h))
        r = (self.x, self.y, w, h)
        self.x += w
        self.shelf = max(self.shelf, h)
        self.regions[name] = r
        return r


# ---------------------------------------------------------------- material tile painters (Px over a w x h tile)
def tile_wood_v(base=WOOD, dark=WOOD_D, widths=(5, 4, 6)):
    def paint(px):
        px.planks_v(0, px.w, 0, px.h, list(widths), base, dark, knots=0.2)
    return paint


def tile_wood_h(base=WOOD, dark=WOOD_D, heights=(5, 4, 6)):
    def paint(px):
        px.planks_h(0, px.w, 0, px.h, list(heights), base, dark, knots=0.2)
    return paint


def tile_end_grain(base=WOOD, dark=WOOD_D):
    def paint(px):
        for j in range(px.h):
            for i in range(px.w):
                r = math.hypot((i % 8) - 3.5, (j % 8) - 3.5)
                c = shade(base, 0.85 + 0.12 * math.cos(r * 1.6))
                if i % 8 == 7 or j % 8 == 7:
                    c = shade(dark, 1.1)
                px.put(i, j, px.jit(c, 3))
    return paint


def tile_metal(base=IRON, noise=6, rust=0.0):
    def paint(px):
        px.metal(0, px.w, 0, px.h, base, noise=noise, bevel=False, rust=rust)
    return paint


def tile_stone(base=STONE, mortar=STONE_D, course=8):
    def paint(px):
        for r in range(px.h // course + 1):
            off = (r % 2) * 5
            i = -off
            while i < px.w:
                bw = px.rng.choice((7, 8, 9, 10))
                px.stone(max(0, i), min(px.w, i + bw), r * course, min(px.h, (r + 1) * course), base, mortar)
                i += bw
    return paint


def tile_copper(base=COPPER, light=COPPER_L, dark=COPPER_D, vertical=True):
    """Round pipe shading across the tile (columns along j when vertical)."""
    def paint(px):
        n = px.w if vertical else px.h
        for a in range(n):
            t = (a % 4) / 3.0
            c = mix(light, base, abs(t - 0.3) * 1.6) if t < 0.66 else mix(base, dark, (t - 0.66) * 3)
            for b in range(px.h if vertical else px.w):
                i, j = (a, b) if vertical else (b, a)
                px.put(i, j, px.jit(c, 4))
    return paint


def tile_flat(c, noise=4):
    def paint(px):
        px.rect(0, px.w, 0, px.h, c, noise)
    return paint


# ---------------------------------------------------------------- sprite painters (cut-out, alpha outside)
def sprite_gear(teeth=10, base=BRASS, light=BRASS_L, dark=BRASS_D, spokes=4, hole=True):
    """A crisp gear seen from the front, filling the w x h sprite: teeth, rim, spokes and hub, lit from the top
    left, dark edge bottom right (alpha 0 elsewhere)."""
    def paint(px):
        px.clear(0, px.w, 0, px.h)
        R = px.w / 2.0
        tooth_h = 2.0 if px.w >= 12 else 1.5
        r_root = R - tooth_h
        rim_w = 2.0 if px.w >= 12 else 1.4
        r_rim_in = r_root - rim_w
        r_hub = 2.2 if px.w >= 12 else 1.6
        mask = {}
        for j in range(px.h):
            for i in range(px.w):
                x, y = i + 0.5 - R, j + 0.5 - R
                d = math.hypot(x, y)
                a = math.atan2(y, x)
                tooth = math.cos(a * teeth) > 0.0
                if d <= r_root or (d <= R and tooth):
                    if d > r_rim_in or d < r_hub:
                        mask[(i, j)] = "solid"
                    else:
                        ang = (a + math.pi / 4) % (2 * math.pi / spokes)
                        dist = min(ang, 2 * math.pi / spokes - ang) * d
                        if dist < 0.85:
                            mask[(i, j)] = "spoke"
        for (i, j), kind in mask.items():
            x, y = i + 0.5 - R, j + 0.5 - R
            lit = -(x + y) / (R * 1.42)
            c = mix(base, light, max(0.0, lit) * 0.8) if lit > 0 else mix(base, dark, -lit * 0.55)
            if kind == "spoke":
                c = shade(c, 0.92)
            d = math.hypot(x, y)
            if hole and d < 1.0:
                c = rgb("1a1210")
            elif d < r_hub and d > r_hub - 1.0:
                c = mix(c, dark, 0.45)
            # edges: bottom / right neighbours empty -> dark, top / left empty -> light
            if (i + 1, j) not in mask or (i, j + 1) not in mask:
                c = mix(c, dark, 0.6)
            elif (i - 1, j) not in mask or (i, j - 1) not in mask:
                c = mix(c, light, 0.5)
            px.put(i, j, c)
    return paint


def sprite_half_wheel(side, teeth=14, base=BRASS, light=BRASS_L, dark=BRASS_D, spokes=6):
    """Half of a big wheel cut on its vertical diameter (side -1: the left half): the two halves meet on the seam."""
    full = sprite_gear(teeth, base, light, dark, spokes)

    def paint(px):
        w2 = px.w * 2
        tmp = np.zeros((px.h, w2, 4))
        full(Px(tmp, 0, 0, w2, px.h, 5))
        part = tmp[:, :px.w] if side < 0 else tmp[:, px.w:]
        px.a[px.v0:px.v0 + px.h, px.u0:px.u0 + px.w] = part
    return paint


def sprite_banner(cloth=rgb("2a3478"), trim=rgb("d9a93a"), emblem=True):
    def paint(px):
        px.clear(0, px.w, 0, px.h)
        w, h = px.w, px.h
        for j in range(h):
            for i in range(w):
                tip = h - 1 - abs(i + 0.5 - w / 2) * (h * 0.22) / (w / 2)
                if j > tip:
                    continue
                c = cloth
                if i == 0 or i == w - 1 or j > tip - 1.2 or j < 1:
                    c = trim
                else:
                    c = shade(cloth, 1.0 + 0.12 * math.sin(i * 1.3))
                px.put(i, j, px.jit(c, 3))
        if emblem:
            cx = w // 2
            for (di, dj) in ((0, 0), (-1, 1), (0, 1), (1, 1), (0, 2), (-1, 3), (1, 3), (0, -1)):
                px.put(cx + di - (1 if w % 2 == 0 else 0) + (0 if w % 2 else 1) * 0, h // 3 + dj, trim)
        # rod on top
        for i in range(w):
            px.put(i, 0, rgb("6b4a1c"))
    return paint


def sprite_ring(base=IRON_L, dark=IRON_D):
    def paint(px):
        px.clear(0, px.w, 0, px.h)
        R = px.w / 2.0
        for j in range(px.h):
            for i in range(px.w):
                d = math.hypot(i + 0.5 - R, j + 0.5 - R)
                if R - 1.6 <= d <= R:
                    px.put(i, j, base if (i + j) < px.w else dark)
    return paint


# ---------------------------------------------------------------- the door
GAP = 0.25            # px: leaf / frame and leaf / leaf clearance (1/64 block), hidden behind the stops
BODY = 1.5            # px: half thickness of a leaf body (3/16 block)
RELIEF = 2.0          # px: the leaf envelope (front relief up to +2, back battens down to -2)
STOP_Z = 2.25         # px: the frame stops in front of the leaves start here (a backwards swing never reaches it)
REBATE = 2.5          # px: rear rebate cut in the jambs beside the hinges (the leaf's back swings into it)
AXES6 = {"+1": (0, 1), "-1": (0, -1), "+2": (1, 1), "-2": (1, -1), "+3": (2, 1), "-3": (2, -1)}
MIN_GAP = 1.0 / 64
POSES = [{}, {"leaf_l": 90.0, "leaf_r": -90.0}, {"leaf_l": -90.0, "leaf_r": 90.0}]


class LargeDoor:
    """A large door. Geometry rules of 1.32.0 (checked by tools/doors/door_audit_large.py on export):
    - leaf bodies X in [-26 + GAP, -GAP] (leaf_l) / [GAP, 26 - GAP] (leaf_r), Z in [-BODY, BODY]; reliefs
      embedded in the body, never beyond Z = +-RELIEF; leaf_r carries the astragal over the seam;
    - the frame covers the clearances: stops in front of the leaf edges (Z >= STOP_Z), a rear rebate beside
      the hinges (the leaf's back swings into it), the lintel / arch soffit above the swept leaf;
    - resolve() (run on export) removes the faces hidden in a contact and moves faces so that no two
      parallel overlapping faces are closer than 1/64 block, closed and open both ways, inside the envelopes."""

    def __init__(self, name, jamb=6, size=256, seed=7, leaf_z=2):
        self.name, self.jamb, self.size, self.leaf_z = name, jamb, size, leaf_z
        tl.setup(name)
        self.atlas = Atlas(size)
        self.seed = seed
        self.root = Bone(name)
        self.frame = Bone("frame", parent=self.root)
        self.leaf_l = Bone("leaf_l", origin=((-32 + jamb) * P, 0, 0), parent=self.root)
        self.leaf_r = Bone("leaf_r", origin=((32 - jamb) * P, 0, 0), parent=self.root)
        fr = self.atlas.alloc("front", WPX, HPX)
        bk = self.atlas.alloc("back", WPX, HPX)
        self.F = Picture(self.atlas.arr, fr[0], fr[1], False, seed)
        self.B = Picture(self.atlas.arr, bk[0], bk[1], True, seed + 1)
        self.materials = {}
        self.sprites = {}
        self.counts = {}
        self._details = {}
        self.notches = []
        hx = 32 - jamb
        self.leaf_env = {"leaf_l": ((-hx + GAP) * P, -GAP * P), "leaf_r": (-0.75 * P, (hx - GAP) * P)}

    # ------------------------------------------------ regions
    def material(self, name, painter, w=64, h=64):
        r = self.atlas.alloc(name, w, h)
        painter(Px(self.atlas.arr, r[0], r[1], w, h, zlib.crc32(name.encode())))
        self.materials[name] = r
        return name

    def sprite(self, name, w, h, painter):
        r = self.atlas.alloc(name, w, h)
        painter(Px(self.atlas.arr, r[0], r[1], w, h, zlib.crc32(name.encode())))
        self.sprites[name] = r
        return name

    def region_px(self, name, w, h):
        """A free region to paint by hand: returns a Px over it."""
        r = self.atlas.alloc(name, w, h)
        self.sprites[name] = r
        return Px(self.atlas.arr, r[0], r[1], w, h, zlib.crc32(name.encode()))

    def detail(self, parent):
        if id(parent) not in self._details:
            self._details[id(parent)] = Bone("detail", origin=tuple(parent.origin), parent=parent)
        return self._details[id(parent)]

    def leaf_x(self, tag):
        hx = 32 - self.jamb
        return (-hx + GAP, -GAP) if tag == "l" else (GAP, hx - GAP)

    # ------------------------------------------------ cubes
    def _face_uv(self, spec, cube_name, bbface, X0, X1, Y0, Y1, du, dv):
        """spec -> uv rect [u0, v0, u1, v1] in atlas px."""
        if spec == "F":
            r = self.atlas.regions["front"]
            return [r[0] + X0 + 32, r[1] + HPX - Y1, r[0] + X1 + 32, r[1] + HPX - Y0]
        if spec == "B":
            r = self.atlas.regions["back"]
            return [r[0] + 32 - X1, r[1] + HPX - Y1, r[0] + 32 - X0, r[1] + HPX - Y0]
        if isinstance(spec, tuple):            # (sprite, mirror) or (sprite, (s0, t0, s1, t1))
            r = self.sprites[spec[0]]
            if len(spec) > 1 and spec[1] is True:
                return [r[0] + r[2], r[1], r[0], r[1] + r[3]]
            if len(spec) > 1 and isinstance(spec[1], (tuple, list)):
                s0, t0, s1, t1 = spec[1]
                return [r[0] + s0 * r[2], r[1] + t0 * r[3], r[0] + s1 * r[2], r[1] + t1 * r[3]]
            return [r[0], r[1], r[0] + r[2], r[1] + r[3]]
        if spec in self.sprites:
            r = self.sprites[spec]
            return [r[0], r[1], r[0] + r[2], r[1] + r[3]]
        r = self.materials[spec]
        su, sv = min(r[2], max(1.0, du)), min(r[3], max(1.0, dv))
        seed = zlib.crc32((cube_name + bbface).encode())
        ou = seed % max(1, int(r[2] - su) + 1)
        ov = (seed // 97) % max(1, int(r[3] - sv) + 1)
        return [r[0] + ou, r[1] + ov, r[0] + ou + su, r[1] + ov + sv]

    def box(self, bone, name, X0, X1, Y0, Y1, Z0, Z1, side="iron_side", front="F", back="B", top=None, bottom=None,
            left=None, right=None, glow=False):
        """Axis-aligned box in door pixels. Faces: +Z front (default: front picture), -Z back (back picture),
        +-X right/left and +-Y top/bottom (default: side material). A face spec is "F", "B", a material name, a
        sprite name, (sprite, True) mirrored, (sprite, (s0, t0, s1, t1)) part of a sprite, or None (no face)."""
        X0, X1 = min(X0, X1), max(X0, X1)
        Y0, Y1 = min(Y0, Y1), max(Y0, Y1)
        Z0, Z1 = min(Z0, Z1), max(Z0, Z1)
        nm = ("glow_" if glow and not name.startswith("glow") else "") + name
        nm = self._unique(nm)
        specs = {"+3": front, "-3": back, "+1": right if right is not None else side,
                 "-1": left if left is not None else side, "+2": top if top is not None else side,
                 "-2": bottom if bottom is not None else side}
        for key, val in (("+1", right), ("-1", left), ("+2", top), ("-2", bottom)):
            if val is False:
                specs[key] = None
        dx, dy, dz = X1 - X0, Y1 - Y0, Z1 - Z0
        sizes = {"+3": (dx, dy), "-3": (dx, dy), "+1": (dz, dy), "-1": (dz, dy), "+2": (dx, dz), "-2": (dx, dz)}
        c = gg.add_cube(bone, nm, ((X0 + X1) / 2 * P, (Y0 + Y1) / 2 * P, (Z0 + Z1) / 2 * P), EYE,
                        (max(dx, 0.25) * P, max(dy, 0.25) * P, max(dz, 0.25) * P), {"all": "_"})
        for sem, bbface in gg.SEMANTIC_FACE.items():
            sp = specs[sem]
            if sp is None:
                c.faces[bbface] = None
                continue
            uv = self._face_uv(sp, nm, bbface, X0, X1, Y0, Y1, *sizes[sem])
            c.faces[bbface] = {"region": "_", "u_dir": None, "v_dir": None, "stretch": True, "density": 1.0,
                               "uv": [round(float(x), 4) for x in uv]}
        return c

    def rbox(self, bone, name, p0, p1, thick, Z0, Z1, face, side="iron_side", back=None, glow=False):
        """A box rotated about Z from p0 to p1 (door px, its axis), thickness `thick` px in the door plane, Z0..Z1;
        the front face (and back, default = the same) shows `face` (a sprite stretched along the length)."""
        p0, p1 = np.array(p0, float), np.array(p1, float)
        d = p1 - p0
        L = float(np.linalg.norm(d))
        ang = math.atan2(d[1], d[0])
        u = v3(math.cos(ang), math.sin(ang), 0)
        vv = v3(-math.sin(ang), math.cos(ang), 0)
        axes = np.column_stack([u, vv, v3(0, 0, 1)])
        cen = (p0 + p1) / 2
        nm = self._unique(("glow_" if glow else "") + name)
        c = gg.add_cube(bone, nm, (cen[0] * P, cen[1] * P, (Z0 + Z1) / 2 * P), axes, (L * P, thick * P, (Z1 - Z0) * P),
                        {"all": "_"})
        dz = Z1 - Z0
        sizes = {"+3": (L, thick), "-3": (L, thick), "+1": (dz, thick), "-1": (dz, thick), "+2": (L, dz), "-2": (L, dz)}
        specs = {"+3": face, "-3": back or face, "+1": side, "-1": side, "+2": side, "-2": side}
        for sem, bbface in gg.SEMANTIC_FACE.items():
            sp = specs[sem]
            if sp is None:
                c.faces[bbface] = None
                continue
            uv = self._face_uv(sp, nm, bbface, 0, 0, 0, 0, *sizes[sem])
            if sem == "-3" and isinstance(sp, str) and sp in self.sprites:
                uv = [uv[2], uv[1], uv[0], uv[3]]   # the back sees the sprite mirrored: un-mirror it
            c.faces[bbface] = {"region": "_", "u_dir": None, "v_dir": None, "stretch": True, "density": 1.0,
                               "uv": [round(float(x), 4) for x in uv]}
        return c

    def sprite_box(self, bone, name, cx, cy, w, h, Z0, Z1, sprite, edge=None, glow=False):
        """A flat cut-out (gear, banner, ring): the sprite on its front and back, no side faces unless edge. Its
        name starts with cut_ (the audit allows transparent texels there); keep it >= 1/64 block (0.25 px) away
        from any parallel face and in front of an opaque surface."""
        return self.box(bone, ("glow_cut_" if glow else "cut_") + name, cx - w / 2, cx + w / 2, cy - h / 2,
                        cy + h / 2, Z0, Z1, side=edge, front=sprite, back=(sprite, True))

    def lantern(self, bone, name, cx, cy, cz, w=4, h=5, metal="iron"):
        """A lit lantern (tools/lanterns.py rebuilds it on export: glass drawn full bright, posts, cap, ring).
        Its rebuilt cap / ring rise about 0.45 h above the box centre + h/2: keep it under the top of the door."""
        return gg.add_cube(bone, self._unique(name), (cx * P, cy * P, cz * P), EYE, (w * P, h * P, w * P),
                           {"all": "lantern", "+2": metal, "-2": metal}, stretch=True)

    def _unique(self, nm):
        k = self.counts.get(nm, 0)
        self.counts[nm] = k + 1
        return nm if k == 0 else "%s_%d" % (nm, k)

    def leaf_strips(self, bone, tag, X0, X1, top_fn, step, Z0=None, Z1=None, side="wood_side", top="wood_end",
                    front="F", back="B"):
        """A leaf body cut in vertical strips of `step` px whose tops follow top_fn(Xcentre) (arched leaves)."""
        Z0 = -BODY if Z0 is None else Z0
        Z1 = BODY if Z1 is None else Z1
        X = X0
        k = 0
        while X < X1 - 1e-6:
            Xn = min(X1, X + step)
            if X1 - Xn < 0.6:
                Xn = X1
            Yt = top_fn((X + Xn) / 2)
            self.box(bone, "%s_%d" % (tag, k), X, Xn, GAP, Yt, Z0, Z1, side=side, top=top, front=front, back=back)
            X = Xn
            k += 1

    def jamb_courses(self, side, courses, X_out=32, front_z=(8, 7.25), back_z=(8, 7.25), mat="stone_side", name="jamb",
             front_top=None):
        """A jamb (left side -1, right +1) as courses [(Y0, Y1), ...]: per course a front block reaching over the
        leaf edge (the stop, Z >= STOP_Z, to |X| = hinge - 1), a middle block (Z 0 .. STOP_Z) and a back block
        leaving the rear rebate free (|X| >= hinge + REBATE). Alternate courses stand out (front_z / back_z)."""
        hx = 32 - self.jamb
        sg = -1 if side < 0 else 1
        tag = "l" if side < 0 else "r"
        out = []
        for k, (y0, y1) in enumerate(courses):
            zf = front_z[k % len(front_z)]
            zb = back_z[k % len(back_z)]
            a, b = sorted((sg * X_out, sg * (hx - 1)))
            out.append(self.box(self.frame, "%s_%s_f%d" % (name, tag, k), a, b, y0, y1, STOP_Z, zf, side=mat))
            a, b = sorted((sg * X_out, sg * hx))
            out.append(self.box(self.frame, "%s_%s_m%d" % (name, tag, k), a, b, y0, y1, 0, STOP_Z, side=mat))
            a, b = sorted((sg * X_out, sg * (hx + REBATE)))
            out.append(self.box(self.frame, "%s_%s_b%d" % (name, tag, k), a, b, y0, y1, -zb, 0, side=mat))
        return out

    def sill(self, mat="stone_side", front="F", z1=4.0):
        """The threshold in front of the leaves (their bottoms stand GAP above the ground): covers that sliver
        seen from the front or the back, never met by a leaf swinging backwards."""
        hx = 32 - self.jamb - 1
        return self.box(self.frame, "sill", -hx, hx, 0, 0.75, STOP_Z, z1, side=mat, front=front, back=mat,
                        top=mat, bottom=mat)

    # ------------------------------------------------ export
    def _install(self):
        S = self.size
        gn.SIZE = S
        gg.SIZE = S
        regions = {}
        for k, r in list(self.materials.items()) + list(self.sprites.items()):
            regions[k] = (0,) + tuple(r)
        regions["_"] = (0, 0, 0, 1, 1)
        gn.REGIONS = regions
        gg.REGIONS = {k: v[1:] for k, v in regions.items()}
        orig = getattr(gn, "_orig_face_uv", None) or gn.face_uv
        gn._orig_face_uv = orig

        def face_uv(cube, bbface, spec, seed):
            if "uv" in spec:
                return list(spec["uv"]), 0
            return orig(cube, bbface, spec, seed)
        gn.face_uv = face_uv

    def fill_pictures(self, c=(46, 40, 42)):
        """Every texel of the front / back pictures opaque (a solid face must never map alpha < 255)."""
        for reg in ("front", "back"):
            u, v, w, h = self.atlas.regions[reg]
            sub = self.atlas.arr[v:v + h, u:u + w]
            m = sub[..., 3] < 255
            sub[m] = (c[0], c[1], c[2], 255)

    def texture_png(self):
        return Image.fromarray(np.clip(self.atlas.arr, 0, 255).astype(np.uint8), "RGBA")

    # ------------------------------------------------ faces, contacts, coplanar faces
    def _top(self, bone):
        b = bone
        while b is not None:
            if b.name in ("frame", "leaf_l", "leaf_r"):
                return b.name
            b = b.parent
        return "frame"

    def _rig(self, bone):
        b = bone
        while b is not None:
            if b.name in ("frame", "leaf_l", "leaf_r") or b.name.startswith(("gear_", "bolt_", "piston_", "handle_")):
                return id(b)
            b = b.parent
        return 0

    def _cube_faces(self, c, pose, center=None, size=None):
        top = self._top(c.bone)
        R = c.bone.frame_rot() @ np.asarray(c.axes, float)
        C = c.bone.to_world(np.asarray(c.center if center is None else center, float))
        a = pose.get(top, 0.0)
        if a:
            t = math.radians(a)
            Ry = np.array([[math.cos(t), 0, math.sin(t)], [0, 1, 0], [-math.sin(t), 0, math.cos(t)]])
            piv = np.asarray((self.leaf_l if top == "leaf_l" else self.leaf_r).origin, float)
            C = Ry @ (C - piv) + piv
            R = Ry @ R
        h = np.asarray(c.size if size is None else size, float) / 2
        out = []
        rig = self._rig(c.bone)
        for sem, (k, s) in AXES6.items():
            bb = gg.SEMANTIC_FACE[sem]
            if c.faces.get(bb) is None:
                continue
            o = [j for j in range(3) if j != k]
            n = R[:, k] * s
            p = C + n * h[k]
            e1, e2 = R[:, o[0]] * h[o[0]], R[:, o[1]] * h[o[1]]
            area = 4 * h[o[0]] * h[o[1]]
            if area < 1e-9:
                continue
            sg = 1
            for x in n:
                if abs(x) > 1e-3:
                    sg = 1 if x > 0 else -1
                    break
            cn = n * sg
            out.append(dict(cube=c, sem=sem, bb=bb, k=k, s=s, n=n, centre=p, area=area, uuid=id(c), top=top,
                            rig=rig, el=c.name, key=tuple(np.round(cn * 2000).astype(int)), cd=float(np.dot(cn, p)),
                            corners=np.array([p - e1 - e2, p + e1 - e2, p + e1 + e2, p - e1 + e2])))
        return out

    def _pose_faces(self, pose):
        out = []
        for c in tl._all_cubes(self.root):
            out.extend(self._cube_faces(c, pose))
        return out

    @staticmethod
    def _index(faces):
        idx = {}
        for f in faces:
            idx.setdefault(f["key"], [[], None])[0].append(f)
        for ent in idx.values():
            ent[1] = np.array([f["cd"] for f in ent[0]])
        return idx

    def _reindex(self, indexes, cubes):
        """Replaces the faces of `cubes` in the three pose indexes (after a move / split / deletion)."""
        uids = {id(c) for c in cubes}
        for idx, pose in zip(indexes, POSES):
            touched = set()
            for key, ent in idx.items():
                if any(f["uuid"] in uids for f in ent[0]):
                    ent[0] = [f for f in ent[0] if f["uuid"] not in uids]
                    touched.add(key)
            for c in cubes:
                for f in self._cube_faces(c, pose):
                    idx.setdefault(f["key"], [[], None])[0].append(f)
                    touched.add(f["key"])
            for key in touched:
                idx[key][1] = np.array([f["cd"] for f in idx[key][0]])

    @staticmethod
    def _conflicts(faces, index, uid):
        import door_audit_large as A
        n = 0
        for f in faces:
            ent = index.get(f["key"])
            if ent is None or not len(ent[0]):
                continue
            for i in np.nonzero(np.abs(ent[1] - f["cd"]) < MIN_GAP - 1e-6)[0]:
                g = ent[0][i]
                if g["uuid"] == uid or abs(float(np.dot(f["n"], g["n"]))) < 0.99999:
                    continue
                if A.overlap(f, g):
                    n += 1
        return n

    @staticmethod
    def _aabb(c, center=None, size=None):
        R = c.bone.frame_rot() @ np.asarray(c.axes, float)
        C = c.bone.to_world(np.asarray(c.center if center is None else center, float))
        h = np.abs(R) @ (np.asarray(c.size if size is None else size, float) / 2)
        return C - h, C + h

    def _foreign(self):
        boxes = {"frame": [], "leaf_l": [], "leaf_r": []}
        for c in tl._all_cubes(self.root):
            boxes[self._top(c.bone)].append(self._aabb(c))
        return boxes

    def _in_contact(self, w):
        """Is the face (closed pose) touched from outside by another cube of its rigid group? Shrinking it would
        open a seam."""
        c = w["cube"]
        face = next((h for h in self._cube_faces(c, {}) if h["sem"] == w["sem"]), None)
        if face is None:
            return False
        cs = face["corners"]
        pts = [cs[0] * (1 - a) * (1 - b) + cs[1] * a * (1 - b) + cs[2] * a * b + cs[3] * (1 - a) * b
               for a in (0.02, 0.5, 0.98) for b in (0.02, 0.5, 0.98)]
        pts = np.array(pts) + face["n"] * 1e-3
        rig = face["rig"]
        for o in tl._all_cubes(self.root):
            if o is c or self._rig(o.bone) != rig:
                continue
            R = o.bone.frame_rot() @ np.asarray(o.axes, float)
            C = o.bone.to_world(np.asarray(o.center, float))
            h = np.asarray(o.size, float) / 2
            loc = (pts - C) @ R
            if np.any(np.all(np.abs(loc) < h - 1e-6, axis=1)):
                return True
        return False

    def _valid_move(self, w, m, foreign, covered=False):
        c, k, s = w["cube"], w["k"], w["s"]
        if m < 0 and self._in_contact(w):
            return None
        size = np.asarray(c.size, float).copy()
        if size[k] + m < MIN_GAP - 1e-9:
            return None
        size[k] += m
        ax = np.asarray(c.axes, float)[:, k]
        center = np.asarray(c.center, float) + ax * s * m / 2
        lo, hi = self._aabb(c, center, size)
        top = w["top"]
        if top == "frame":
            elo, ehi = np.array([-2, 0, -0.5]), np.array([2, 6, 0.5])
        else:
            x0, x1 = self.leaf_env[top]
            elo, ehi = np.array([x0, 0, -RELIEF * P]), np.array([x1, 6, RELIEF * P])
        if np.any(lo < elo - 1e-6) or np.any(hi > ehi + 1e-6):
            return None
        olo, ohi = self._aabb(c)
        if m < 0 and not covered and np.allclose(np.asarray(c.axes, float)[:, k] ** 2, np.eye(3)[k], atol=1e-9):
            # never pull a face off the envelope (the silhouette / a leaf edge would open a sliver)
            pos = s * np.asarray(c.axes, float)[k, k] > 0
            face = ohi[k] if pos else olo[k]
            bound = (6.0 if pos else 0.0) if k == 1 else (2.0 if pos else -2.0) if k == 0 else None
            if bound is not None and abs(face - bound) < 1e-6:
                return None
        for g, lst in foreign.items():
            if g == top:
                continue
            for a, b in lst:
                new = np.prod(np.clip(np.minimum(hi, b) - np.maximum(lo, a), 0, None))
                if new > 1e-12:
                    old = np.prod(np.clip(np.minimum(ohi, b) - np.maximum(olo, a), 0, None))
                    if new > old + 1e-12:
                        return None
        return center, size

    def _split(self, c, axis, q):
        """Cuts the axis-aligned cube c in two at door coordinate q (blocks) along `axis`, keeping every face's
        texture in place (uv rects cut in proportion). False if it cannot."""
        if not np.allclose(np.asarray(c.axes, float), EYE):
            return False
        if any(fc is not None and "uv" not in fc for fc in c.faces.values()):
            return False
        cen, siz = np.asarray(c.center, float), np.asarray(c.size, float)
        lo, hi = cen - siz / 2, cen + siz / 2
        if not (lo[axis] + MIN_GAP - 1e-6 < q < hi[axis] - MIN_GAP + 1e-6):
            return False                     # never leave a part thinner than 1/64 block
        sgn = np.array([-16.0, 16.0, -16.0])
        cb, hb = cen * sgn, siz * 8.0
        fb, tb = cb - hb, cb + hb

        def part(a, b):
            plo, phi = lo.copy(), hi.copy()
            plo[axis], phi[axis] = a, b
            qa, qb = sorted((a * sgn[axis], b * sgn[axis]))
            faces = {}
            for bb, fc in c.faces.items():
                if fc is None:
                    faces[bb] = None
                    continue
                nfc = dict(fc)
                u1, v1, u2, v2 = fc["uv"]
                _, ud, vd = pv.FACES[bb]
                for d_, (i1, i2) in ((ud, (0, 2)), (vd, (1, 3))):
                    if d_[axis] == 0:
                        continue
                    st, en = (fb[axis], tb[axis]) if d_[axis] > 0 else (tb[axis], fb[axis])
                    s2, e2 = (qa, qb) if d_[axis] > 0 else (qb, qa)
                    w1, w2 = fc["uv"][i1], fc["uv"][i2]
                    U = lambda x: w1 + (w2 - w1) * (x - st) / (en - st)  # noqa: E731
                    uv = list(nfc["uv"])
                    uv[i1], uv[i2] = round(U(s2), 4), round(U(e2), 4)
                    nfc["uv"] = uv
                del u1, v1, u2, v2
                faces[bb] = nfc
            return (plo + phi) / 2, phi - plo, faces
        c1, s1, f1 = part(lo[axis], q)
        c2, s2, f2 = part(q, hi[axis])
        c.center, c.size, c.faces = c1, s1, f1
        self._last_new = gg.Cube(c.bone, self._unique(c.name + "_p"), c2, np.asarray(c.axes, float).copy(), s2, f2)
        return True

    def _try_split(self, f, g):
        """Partial contact: cut the cube of one face along an edge of the other so that the contact becomes a
        containment (then the hidden face goes)."""
        for a, b in ((f, g), (g, f)) if f["area"] <= g["area"] else ((g, f), (f, g)):
            k = a["k"]
            for j in [x for x in range(3) if x != k]:
                alo, ahi = a["corners"][:, j].min(), a["corners"][:, j].max()
                blo, bhi = b["corners"][:, j].min(), b["corners"][:, j].max()
                for q in (blo, bhi):
                    if alo + 1e-3 < q < ahi - 1e-3 and self._split(a["cube"], j, q):
                        return True
        return False

    def _fix_pair(self, f, g, dd, foreign, indexes, closed=True):
        import door_audit_large as A
        opp = float(np.dot(f["n"], g["n"])) < 0
        if dd <= A.COP and f["rig"] == g["rig"]:
            # same plane, one rigid group: a face inside the other one is hidden (contact) or drawn twice (same
            # direction): it goes; a partial overlap is first cut so that it becomes a containment
            for a, b in ((f, g), (g, f)):
                if A.contains(a, b) and (opp or not A.is_cut(b["el"])):
                    a["cube"].faces[a["bb"]] = None
                    return "deleted"
            if closed and self._try_split(f, g):
                return "split"
        best = None
        for w, s_ in ((f, g), (g, f)):
            c = w["cube"]
            before = sum(self._conflicts(self._cube_faces(c, pose), indexes[i], id(c)) for i, pose in enumerate(POSES))
            sigma = float(np.dot(w["centre"] - s_["centre"], w["n"]))
            grow, shrink = MIN_GAP - sigma, -MIN_GAP - sigma
            cross = w["rig"] != s_["rig"]
            if opp and not cross:
                # a contact inside one rigid group: only close it further (a shrink would open a see-through seam)
                cands = [grow, grow + MIN_GAP, grow + 2 * MIN_GAP, grow + 4 * MIN_GAP]
            else:
                pref = [shrink, grow] if opp else sorted((grow, shrink), key=abs)
                cands = pref + [grow + MIN_GAP, shrink - MIN_GAP, grow + 2 * MIN_GAP, shrink - 2 * MIN_GAP,
                                grow + 4 * MIN_GAP, shrink - 4 * MIN_GAP]
            covered = (not opp) and A.contains(w, s_)
            for rank, m in enumerate(cands):
                mv = self._valid_move(w, m, foreign, covered)
                if mv is None:
                    continue
                after = sum(self._conflicts(self._cube_faces(c, pose, *mv), indexes[i], id(c))
                            for i, pose in enumerate(POSES))
                if after >= before:
                    continue
                score = (after, 0 if A.is_cut(w["el"]) else 1, rank, w["area"])
                if best is None or score < best[0]:
                    best = (score, c, mv)
                if after == 0:
                    break
        if best is None:
            return None
        c, (center, size) = best[1], best[2]
        c.center, c.size = center, size
        return "moved"

    def resolve(self, passes=40, verbose=True):
        """Contact faces hidden inside one rigid group are removed; any other pair of parallel overlapping faces
        closer than 1/64 block (closed, open backwards, open forwards) is separated by moving one face along its
        normal (grow or shrink): the move that removes the most conflicts without creating any, never out of the
        door box / leaf envelope nor into another group's cubes (a contact inside a group is only ever closed
        further, so no seam opens)."""
        import door_audit_large as A
        stats = {"deleted": 0, "moved": 0, "split": 0, "stuck": 0}

        def current(f, pose):
            for h in self._cube_faces(f["cube"], pose):
                if h["sem"] == f["sem"]:
                    return h
            return None
        for it in range(passes):
            total = stuck = 0
            changed = False
            for pi, pose in enumerate(POSES):
                faces = self._pose_faces(pose)
                pairs = A.parallel_pairs(faces)
                total += len(pairs)
                if not pairs:
                    continue
                indexes = [self._index(self._pose_faces(p)) for p in POSES]
                foreign = self._foreign()
                pairs.sort(key=lambda p: -max(p[0]["area"], p[1]["area"]))
                for f0, g0, _ in pairs:
                    f, g = current(f0, pose), current(g0, pose)
                    if f is None or g is None:
                        continue
                    dd = abs(f["cd"] - g["cd"])
                    if dd >= MIN_GAP - 1e-6 or not A.overlap(f, g):
                        continue
                    self._last_new = None
                    act = self._fix_pair(f, g, dd, foreign, indexes, closed=(pi == 0))
                    if act:
                        stats[act] += 1
                        changed = True
                        cubes = [f["cube"], g["cube"]] + ([self._last_new] if self._last_new is not None else [])
                        self._reindex(indexes, cubes)
                        if act in ("moved", "split"):
                            foreign = self._foreign()
                    else:
                        stuck += 1
            if verbose:
                print("  resolve pass %d: %d pairs, %d stuck" % (it + 1, total, stuck), flush=True)
            if total == 0 or not changed:
                break
        stats["stuck"] = stuck
        stats["left"] = total
        stats["passes"] = it + 1
        return stats

    def export(self, icon=None):
        import zfight
        door = self
        saved = zfight.fix

        def fix(root, passes=30):
            st = door.resolve()
            print("resolve:", st)
            return st["moved"]
        zfight.fix = fix
        for need in ("lantern", "gold", "iron"):
            if need not in self.materials and need not in self.sprites:
                if need == "lantern":
                    r = self.atlas.alloc("lantern", 16, 16)
                    tmp = Image.new("RGBA", (16, 16))
                    paint_lamp_glass(tmp.load(), 0, 0, 16, 16)
                    self.atlas.arr[r[1]:r[1] + 16, r[0]:r[0] + 16] = np.array(tmp, dtype=float)
                    self.sprites["lantern"] = r
                elif need == "gold":
                    self.material("gold", tile_metal(BRASS_L, noise=8), 16, 16)
                else:
                    self.material("iron", tile_metal(IRON, noise=6), 16, 16)
        self.fill_pictures()
        self._install()
        tex_rel = "%s.png" % self.name
        tex_path = os.path.join(ASSETS, "textures/entity", tex_rel)
        os.makedirs(os.path.dirname(tex_path), exist_ok=True)
        self.texture_png().save(tex_path)
        with open(tex_path, "rb") as f:
            png = f.read()
        textures = [gn.texture_entry(tex_rel, self.size, png, "entity", tex_rel)]
        textures[0]["id"] = "0"
        outs = [os.path.join(ROOT, "blockbench/%s.bbmodel" % self.name),
                os.path.join(ASSETS, "models/entity/%s.bbmodel" % self.name)]
        try:
            model = gn.export(self.root, [], textures, outs, name=self.name, visible_box=(4, 6, 0))
        finally:
            zfight.fix = saved
        if icon is not None:
            im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
            icon(Px(np.zeros((16, 16, 4)), 0, 0, 16, 16, 3), im)
            p = os.path.join(ASSETS, "textures/item/%s.png" % self.name)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            im.save(p)
        self.model = model
        print("%s: %d cubes, texture %dx%d" % (self.name, len(model["elements"]), self.size, self.size))
        import door_audit_large as A
        self.report = A.audit(model, np.array(self.texture_png()), self.notches, verbose=True,
                              dump=os.path.join(SCRATCH, "doors_out2/audit_" + self.name))
        return model

    # ------------------------------------------------ previews
    def preview(self, out, refs=()):
        model = self.model
        tex = np.array(self.texture_png()).astype(float)
        closed = pv.build_mesh(model, {})
        opened = pv.build_mesh(_with_rot(model, {"leaf_l": [0, 90, 0], "leaf_r": [0, -90, 0]}), {})
        half = pv.build_mesh(_with_rot(model, {"leaf_l": [0, 50, 0], "leaf_r": [0, -50, 0]}), {})
        H = 460
        views = [
            ("face", render(closed, tex, 320, H, eye=(0, 3, 40), target=(0, 3, 0), ortho=4.3)),
            ("3/4", render(closed, tex, 380, H, eye=(-7.5, 5.0, 9.5), target=(0, 2.9, 0), fov=40)),
            ("dos", render(closed, tex, 320, H, eye=(0, 3, -40), target=(0, 3, 0), ortho=4.3)),
            ("ouverte 90 (arriere)", render(opened, tex, 380, H, eye=(-7.0, 4.5, 9.0), target=(0, 2.9, -0.8), fov=44)),
            ("mi-ouverte, dos", render(half, tex, 380, H, eye=(6.5, 4.2, -9.0), target=(0, 2.9, -0.8), fov=44)),
            ("de chant (ouverte)", render(opened, tex, 300, H, eye=(9.5, 3.2, 1.5), target=(0, 3.0, -0.6), fov=42)),
        ]
        ref_imgs = []
        for path in refs:
            im = Image.open(path).convert("RGB")
            k = H / im.size[1]
            ref_imgs.append(im.resize((max(1, int(im.size[0] * k)), H), Image.LANCZOS))
        Wt = sum(v[1].size[0] for v in views) + sum(r.size[0] for r in ref_imgs) + 8 * (len(views) + len(ref_imgs))
        sheet = Image.new("RGB", (Wt, H + 30), (24, 26, 32))
        x = 0
        dr = ImageDraw.Draw(sheet)
        for title, im in views:
            sheet.paste(im, (x, 30))
            dr.text((x + 6, 8), title, fill=(235, 225, 200))
            x += im.size[0] + 8
        for k, im in enumerate(ref_imgs):
            sheet.paste(im, (x, 30))
            dr.text((x + 6, 8), "ref %s" % os.path.basename(refs[k]), fill=(200, 220, 235))
            x += im.size[0] + 8
        os.makedirs(os.path.dirname(out), exist_ok=True)
        sheet.save(out)
        print("preview:", out)


def _with_rot(model, rots):
    m = copy.deepcopy(model)

    def walk(g):
        if g["name"] in rots:
            g["rotation"] = list(rots[g["name"]])
        for c in g["children"]:
            if isinstance(c, dict):
                walk(c)
    for g in m["outliner"]:
        walk(g)
    return m


def render(quads, tex, W, H, eye, target, fov=None, ortho=None, bg=(32, 34, 40)):
    """Same rasteriser as tools/preview.py, with Minecraft face shading (top 1.0, z sides 0.8, x sides 0.6,
    bottom 0.5) and full bright glow* cubes."""
    eye, target = np.array(eye, float), np.array(target, float)
    fwd = target - eye
    fwd /= np.linalg.norm(fwd)
    up = np.array([0, 1, 0.0])
    right = np.cross(fwd, up)
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    img = np.zeros((H, W, 3), float)
    img[:] = bg
    zbuf = np.full((H, W), np.inf)

    def project(p):
        d = p - eye
        x, y, z = d @ right, d @ up, d @ fwd
        if ortho:
            s = H / ortho / 1.5
            return np.array([W / 2 + x * s, H / 2 - y * s, z])
        f = (H / 2) / math.tan(math.radians(fov) / 2)
        return np.array([W / 2 + x * f / z, H / 2 - y * f / z, z])

    tw, th = tex.shape[1], tex.shape[0]
    for corners, uvs, glow, _ti in quads:
        Pp = [project(c) for c in corners]
        n = np.cross(corners[1] - corners[0], corners[3] - corners[0])
        nn = np.linalg.norm(n)
        if nn < 1e-12:
            continue
        n /= nn
        sh = 1.0 if glow else (0.6 * n[0] ** 2 + 0.8 * n[2] ** 2 + (1.0 if n[1] > 0 else 0.5) * n[1] ** 2)
        for tri in ((0, 1, 2), (0, 2, 3)):
            a, b, c = (Pp[i] for i in tri)
            if min(a[2], b[2], c[2]) <= 0.05:
                continue
            ua, ub, uc = (np.array(uvs[i]) for i in tri)
            xmin, xmax = int(max(0, math.floor(min(a[0], b[0], c[0])))), int(min(W - 1, math.ceil(max(a[0], b[0], c[0]))))
            ymin, ymax = int(max(0, math.floor(min(a[1], b[1], c[1])))), int(min(H - 1, math.ceil(max(a[1], b[1], c[1]))))
            if xmin > xmax or ymin > ymax:
                continue
            xs, ys = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
            det = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(det) < 1e-9:
                continue
            w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / det
            w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / det
            w2 = 1 - w0 - w1
            mask = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not mask.any():
                continue
            if ortho:
                z = w0 * a[2] + w1 * b[2] + w2 * c[2]
                uu = w0 * ua[0] + w1 * ub[0] + w2 * uc[0]
                vv = w0 * ua[1] + w1 * ub[1] + w2 * uc[1]
            else:
                iz = w0 / a[2] + w1 / b[2] + w2 / c[2]
                z = 1 / iz
                uu = (w0 * ua[0] / a[2] + w1 * ub[0] / b[2] + w2 * uc[0] / c[2]) * z
                vv = (w0 * ua[1] / a[2] + w1 * ub[1] / b[2] + w2 * uc[1] / c[2]) * z
            tx = np.clip(np.floor(uu).astype(int), 0, tw - 1)
            ty = np.clip(np.floor(vv).astype(int), 0, th - 1)
            col = tex[ty, tx]
            mask &= col[..., 3] > 127
            sub = zbuf[ymin:ymax + 1, xmin:xmax + 1]
            mask &= z < sub - 1e-5
            if not mask.any():
                continue
            sub[mask] = z[mask]
            region = img[ymin:ymax + 1, xmin:xmax + 1]
            region[mask] = col[..., :3][mask] * sh
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def standard_materials(d, wood=WOOD, wood_dark=WOOD_D, iron=IRON, stone=STONE):
    """The side tiles most doors need: wood_side (grain along v), wood_h (grain along u), wood_end, iron_side,
    stone_side, copper_v / copper_h, iron (lantern metal), gold."""
    d.material("wood_side", tile_wood_v(wood, wood_dark))
    d.material("wood_h", tile_wood_h(wood, wood_dark), 64, 32)
    d.material("wood_end", tile_end_grain(wood, wood_dark), 32, 16)
    d.material("iron_side", tile_metal(iron), 64, 32)
    d.material("stone_side", tile_stone(stone), 32, 64)
    d.material("iron", tile_metal(iron, noise=5), 16, 16)
    d.material("gold", tile_metal(BRASS_L, noise=8), 16, 16)


# ---------------------------------------------------------------- swept volume of the leaves
class Sweep:
    """Where the leaves go while they swing 0 -> 90 degrees backwards (the default) - and, if forwards=True, also
    forwards: top(x0, x1, z0, z1) = the highest leaf point (door px) that ever passes over that frame footprint
    (door px), -1 if none. Built from the leaf cubes (axis-aligned bounding boxes), 0.25 px grid, 0.5 degree."""

    def __init__(self, door, forwards=False, res=0.25):
        self.res = res
        self.nx, self.nz = int(64 / res), int(16 / res)
        self.grid = np.full((self.nx, self.nz), -1.0)
        dirs = (1, -1) if forwards else (1,)
        for leaf, sg in ((door.leaf_l, 1), (door.leaf_r, -1)):
            piv = np.asarray(leaf.origin, float) * 16
            pts = []
            for c in tl._all_cubes(leaf):
                lo, hi = door._aabb(c)
                lo, hi = lo * 16, hi * 16
                xs = np.arange(lo[0], hi[0] + 1e-6, res / 2)
                zs = np.arange(lo[2], hi[2] + 1e-6, res / 2)
                X, Z = np.meshgrid(xs, zs, indexing="ij")
                pts.append(np.column_stack([X.ravel() - piv[0], Z.ravel() - piv[2], np.full(X.size, hi[1])]))
            pts = np.vstack(pts)
            for dsg in dirs:
                for deg in np.arange(0, 90.01, 0.5):
                    t = math.radians(deg) * sg * dsg
                    ct, st = math.cos(t), math.sin(t)
                    x = piv[0] + pts[:, 0] * ct + pts[:, 1] * st
                    z = piv[2] - pts[:, 0] * st + pts[:, 1] * ct
                    i = np.clip(((x + 32) / res).astype(int), 0, self.nx - 1)
                    k = np.clip(((z + 8) / res).astype(int), 0, self.nz - 1)
                    np.maximum.at(self.grid, (i, k), pts[:, 2])

    def top(self, x0, x1, z0, z1, margin=0.25):
        i0 = max(0, int(math.floor((x0 - margin + 32) / self.res)))
        i1 = min(self.nx, int(math.ceil((x1 + margin + 32) / self.res)))
        k0 = max(0, int(math.floor((z0 - margin + 8) / self.res)))
        k1 = min(self.nz, int(math.ceil((z1 + margin + 8) / self.res)))
        if i0 >= i1 or k0 >= k1:
            return -1.0
        return float(self.grid[i0:i1, k0:k1].max())
