"""Shared helpers of the three LARGE doors of 1.31.0 (6 blocks high x 4 wide, two leaves): porte_chateau,
porte_vapeur_grande, porte_entrepot. Used by tools/doors/generate_<id>.py (the small / medium doors have their own
libraries, doorlib_small.py / doorlib_medium.py).

    import doorlib_large as dl
    d = dl.LargeDoor("porte_chateau", jamb=6)     # own 256 px atlas; bones root > frame, leaf_l, leaf_r
    F, B = d.F, d.B                               # FRONT / BACK pictures of the whole door (16 px per block)
    F.planks_v(*F.R(-26, 0, 0, 80), widths, base, dark)   # paint in DOOR PIXELS (see below)
    d.material("iron_side", painter)              # 64 x 64 tiles for the side faces
    d.box(d.leaf_l, "body", -26, 0, 0, 80, -2, 2, side="wood_side")
    d.export(icon=painter16)                      # bbmodel (models/entity + blockbench), texture, 16x16 icon
    d.preview(out_png, refs)                      # front / 3-4 / open / back renders next to the reference crops

DOOR PIXELS. Every coordinate given to this library is in 1/16 block, in the contract's frame: X in [-32, 32]
(+X = right seen from the front), Y in [0, 96] (up), Z in [-8, 8] (+Z = the front face). The leaves are 4 px thick
(Z in [-2, 2]); leaf_l pivots on its hinge edge X = -32 + jamb, leaf_r on X = 32 - jamb (Z = 0).

THE PROJECTION. The front picture F (64 x 96 px) is the whole door seen from the front: every +Z face of a box shows
the part of F in front of it (so a band painted on F shows on the raised band cube, a stone painted on F shows on the
stone cube...). B is the door seen from behind, painted in door pixels too (B mirrors X internally). Faces looking
along X or Y use 64 x 64 material tiles; small cut-out pictures (gears, banners) are sprites.
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
class LargeDoor:
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
        if right is False:
            specs["+1"] = None
        if left is False:
            specs["-1"] = None
        if top is False:
            specs["+2"] = None
        if bottom is False:
            specs["-2"] = None
        dx, dy, dz = X1 - X0, Y1 - Y0, Z1 - Z0
        sizes = {"+3": (dx, dy), "-3": (dx, dy), "+1": (dz, dy), "-1": (dz, dy), "+2": (dx, dz), "-2": (dx, dz)}
        c = gg.add_cube(bone, nm, ((X0 + X1) / 2 * P, (Y0 + Y1) / 2 * P, (Z0 + Z1) / 2 * P), EYE,
                        (max(dx, 0.2) * P, max(dy, 0.2) * P, max(dz, 0.2) * P), {"all": "_"})
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

    def sprite_box(self, bone, name, cx, cy, w, h, Z0, Z1, sprite, edge=None):
        """A flat cut-out (gear, banner, ring): the sprite on its front and back, no side faces unless edge."""
        return self.box(bone, name, cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2, Z0, Z1, side=edge,
                        front=sprite, back=(sprite, True))

    def lantern(self, bone, name, cx, cy, cz, w=4, h=5, metal="iron"):
        """A lit lantern (tools/lanterns.py rebuilds it on export: glass drawn full bright, posts, cap, ring).
        Its rebuilt cap / ring rise about 0.3 h above the box: keep cy + 0.8 h under the top of the door."""
        return gg.add_cube(bone, self._unique(name), (cx * P, cy * P, cz * P), EYE, (w * P, h * P, w * P),
                           {"all": "lantern", "+2": metal, "-2": metal}, stretch=True)

    def _unique(self, nm):
        k = self.counts.get(nm, 0)
        self.counts[nm] = k + 1
        return nm if k == 0 else "%s_%d" % (nm, k)

    def leaf_strips(self, bone, tag, X0, X1, top_fn, step, Z0=None, Z1=None, side="wood_side", top="wood_end",
                    front="F", back="B"):
        """A leaf body cut in vertical strips of `step` px whose tops follow top_fn(Xcentre) (arched leaves)."""
        Z0 = -self.leaf_z if Z0 is None else Z0
        Z1 = self.leaf_z if Z1 is None else Z1
        X = X0
        k = 0
        while X < X1 - 1e-6:
            Xn = min(X1, X + step)
            Yt = top_fn((X + Xn) / 2)
            self.box(bone, "%s_%d" % (tag, k), X, Xn, 0, Yt, Z0, Z1, side=side, top=top, front=front, back=back)
            X = Xn
            k += 1

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

    def texture_png(self):
        img = Image.fromarray(np.clip(self.atlas.arr, 0, 255).astype(np.uint8), "RGBA")
        return img

    # ------------------------------------------------ hidden faces / z-fighting / bounds
    MOVERS = ("frame", "leaf_l", "leaf_r", "gear_", "bolt_", "piston_")

    def _group(self, bone):
        b = bone
        while b is not None:
            if b.name == "frame" or b.name in ("leaf_l", "leaf_r") or b.name.startswith(("gear_", "bolt_", "piston_")):
                return id(b)
            b = b.parent
        return 0

    def cull_hidden(self):
        """Removes the faces hidden against an opposite face of a cube of the same rigid group (never between a leaf
        and the frame: the faces show when the leaf opens). Fewer coplanar pairs for zfight, fewer triangles."""
        faces = []
        for c in tl._all_cubes(self.root):
            if not np.allclose(np.asarray(c.axes, float), EYE):
                continue
            g = self._group(c.bone)
            lo = np.asarray(c.center, float) - np.asarray(c.size, float) / 2
            hi = np.asarray(c.center, float) + np.asarray(c.size, float) / 2
            for sem, bb in gg.SEMANTIC_FACE.items():
                if c.faces.get(bb) is None:
                    continue
                k = int(sem[1]) - 1
                s = 1 if sem[0] == "+" else -1
                o = [j for j in range(3) if j != k]
                faces.append((g, k, s, hi[k] if s > 0 else lo[k], lo[o], hi[o], c, bb))
        by = {}
        for f in faces:
            by.setdefault((f[0], f[1], round(f[3] * 256)), []).append(f)
        removed = 0
        eps = 1e-4
        for lst in by.values():
            for a in lst:
                for b in lst:
                    if a is b or a[2] == b[2] or a[6] is b[6]:
                        continue
                    if np.all(a[4] >= b[4] - eps) and np.all(a[5] <= b[5] + eps):
                        if a[6].faces.get(a[7]) is not None:
                            a[6].faces[a[7]] = None
                            removed += 1
        return removed

    def clamp(self):
        """After zfight: nothing may leave the 4 x 6 x 1 box, nor the leaves their 4 px."""
        lo_all, hi_all = v3(-2, 0, -0.5), v3(2, 6, 0.5)
        for c in tl._all_cubes(self.root):
            if not np.allclose(np.asarray(c.axes, float), EYE):
                continue
            g = self._group(c.bone)
            lo, hi = lo_all.copy(), hi_all.copy()
            b = c.bone
            while b is not None and b.name not in ("leaf_l", "leaf_r", "frame"):
                b = b.parent
            if b is not None and b.name in ("leaf_l", "leaf_r"):
                lo[2], hi[2] = -self.leaf_z * P, self.leaf_z * P
            cen, siz = np.asarray(c.center, float), np.asarray(c.size, float)
            a, z = np.maximum(cen - siz / 2, lo), np.minimum(cen + siz / 2, hi)
            if np.any(np.abs(a - (cen - siz / 2)) > 1e-9) or np.any(np.abs(z - (cen + siz / 2)) > 1e-9):
                c.center, c.size = (a + z) / 2, np.maximum(z - a, 1e-3)
            del g

    def export(self, icon=None):
        print("hidden faces culled:", self.cull_hidden())
        import zfight
        if not hasattr(zfight, "_orig_fix"):
            zfight._orig_fix = zfight.fix
        door = self

        def fix(root, passes=30):
            n = zfight._orig_fix(root, passes)
            door.clamp()
            return n
        zfight.fix = fix
        for need in ("lantern", "gold", "iron"):
            if need not in self.materials and need not in self.sprites:
                if need == "lantern":
                    r = self.atlas.alloc("lantern", 16, 16)
                    pxl = self.atlas.arr
                    tmp = Image.new("RGBA", (16, 16))
                    paint_lamp_glass(tmp.load(), 0, 0, 16, 16)
                    pxl[r[1]:r[1] + 16, r[0]:r[0] + 16] = np.array(tmp, dtype=float)
                    self.sprites["lantern"] = r
                elif need == "gold":
                    self.material("gold", tile_metal(BRASS_L, noise=8), 16, 16)
                else:
                    self.material("iron", tile_metal(IRON, noise=6), 16, 16)
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
        model = gn.export(self.root, [], textures, outs, name=self.name, visible_box=(4, 6, 0))
        if icon is not None:
            im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
            icon(Px(np.zeros((16, 16, 4)), 0, 0, 16, 16, 3), im)
            p = os.path.join(ASSETS, "textures/item/%s.png" % self.name)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            im.save(p)
        self.model = model
        lo, hi = self.check_bounds(model)
        bones = self.bone_report(model)
        print("%s: %d cubes, texture %dx%d, bounds x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f" % (
            self.name, len(model["elements"]), self.size, self.size, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
        for b in bones:
            print("  bone", b)
        for back in (True, False):
            hits = self.sweep_check(back)
            print("  sweep %s: %d leaf/frame contacts > 0.6 px%s" % ("backwards" if back else "forwards", len(hits),
                  (": " + ", ".join("%s/%s %.1fpx" % h for h in hits[:6])) if hits else ""))
        return model

    def sweep_check(self, backwards=True, tol=0.6):
        """Frame cubes met by a leaf swinging 0 -> 90 degrees (backwards by default): list of
        (leaf cube, frame cube, worst depth px). Contact under `tol` px is ignored (hinges, rebates)."""
        boxes = []
        for c in tl._all_cubes(self.frame):
            if np.allclose(np.asarray(c.axes, float), EYE):
                lo = np.asarray(c.center, float) - np.asarray(c.size, float) / 2
                hi = np.asarray(c.center, float) + np.asarray(c.size, float) / 2
                boxes.append((c.name, lo, hi))
        hits = {}
        for leaf, sg in ((self.leaf_l, 1), (self.leaf_r, -1)):
            piv = np.asarray(leaf.origin, float)
            for c in tl._all_cubes(leaf):
                R = np.asarray(c.axes, float)
                h = np.asarray(c.size, float) / 2
                pts = [np.asarray(c.center, float) + R @ (h * np.array([a, b, e]))
                       for a in (-1, 0, 1) for b in (-1, 0, 1) for e in (-1, 0, 1)]
                for deg in range(5, 91, 5):
                    t = math.radians(deg) * sg * (1 if backwards else -1)
                    ct, st = math.cos(t), math.sin(t)
                    for p in pts:
                        dx, dz = p[0] - piv[0], p[2] - piv[2]
                        q = np.array([piv[0] + dx * ct + dz * st, p[1], piv[2] - dx * st + dz * ct])
                        for name, lo, hi in boxes:
                            if np.all(q > lo) and np.all(q < hi):
                                depth = float(min(np.min(q - lo), np.min(hi - q))) * 16
                                if depth > tol:
                                    k = (c.name, name)
                                    hits[k] = max(hits.get(k, 0.0), depth)
        return sorted(((a, b, round(d, 2)) for (a, b), d in hits.items()), key=lambda x: -x[2])

    @staticmethod
    def check_bounds(model, tol=0.02):
        quads = pv.build_mesh(model, {})
        pts = np.array([c for q in quads for c in q[0]])
        lo, hi = pts.min(0), pts.max(0)
        bad = (lo[0] < -2 - tol or hi[0] > 2 + tol or lo[1] < -tol or hi[1] > 6 + tol or lo[2] < -0.5 - tol or
               hi[2] > 0.5 + tol)
        if bad:
            print("WARNING: out of the 4 x 6 x 1 box:", lo, hi)
        return lo, hi

    @staticmethod
    def bone_report(model):
        out = []
        elements = {e["uuid"]: e for e in model["elements"]}

        def walk(g, depth):
            n = sum(1 for c in g["children"] if not isinstance(c, dict))
            o = g["origin"]
            out.append("%s%s pivot=(%.4f, %.4f, %.4f) cubes=%d" % ("  " * depth, g["name"], -o[0] / 16, o[1] / 16,
                                                                     -o[2] / 16, n))
            for c in g["children"]:
                if isinstance(c, dict):
                    walk(c, depth + 1)
        for g in model["outliner"]:
            walk(g, 0)
        del elements
        return out

    # ------------------------------------------------ previews
    def preview(self, out, refs=(), open_deg=90.0):
        model = self.model
        tex = np.array(self.texture_png()).astype(float)
        closed = pv.build_mesh(model, {})
        opened = pv.build_mesh(_with_rot(model, {"leaf_l": [0, open_deg, 0], "leaf_r": [0, -open_deg, 0]}), {})
        half = pv.build_mesh(_with_rot(model, {"leaf_l": [0, -open_deg * 0.5, 0], "leaf_r": [0, open_deg * 0.5, 0]}), {})
        views = [
            ("face", render(closed, tex, 300, 420, eye=(0, 3, 40), target=(0, 3, 0), ortho=4.6)),
            ("3/4", render(closed, tex, 360, 420, eye=(-7.5, 5.5, 9.5), target=(0, 2.9, 0), fov=40)),
            ("ouverte 90", render(opened, tex, 360, 420, eye=(-7.5, 5.5, 9.5), target=(0, 2.9, -0.6), fov=42)),
            ("mi-ouverte avant", render(half, tex, 360, 420, eye=(6.5, 4.5, 10), target=(0, 2.9, 0.4), fov=42)),
            ("arriere", render(closed, tex, 300, 420, eye=(0, 3, -40), target=(0, 3, 0), ortho=4.6)),
        ]
        ref_imgs = []
        for path in refs:
            im = Image.open(path).convert("RGB")
            k = 420 / im.size[1]
            ref_imgs.append(im.resize((max(1, int(im.size[0] * k)), 420), Image.LANCZOS))
        Wt = sum(v[1].size[0] for v in views) + sum(r.size[0] for r in ref_imgs) + 8 * (len(views) + len(ref_imgs))
        sheet = Image.new("RGB", (Wt, 450), (24, 26, 32))
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
