"""Shared helpers of the four MEDIUM doors of 1.31.0 (4 blocks high x 2 wide, two leaves of the same width):
porte_grange, porte_forteresse, porte_industrielle, porte_marchande (tools/doors/generate_<id>.py). The small and
large doors have their own libraries (doorlib_small.py, doorlib_large.py).

    import doorlib_medium as dm
    d = dm.Door("porte_grange", post=4, top=54)    # own 256 x 256 atlas; bones <id> > frame, leaf_l, leaf_r
    F, B = d.F, d.B                                # the FRONT and BACK pictures of the whole door (16 px per block)
    F.planks_v(-12, 0, 0, 54, [3, 3, 3, 3], WOOD)  # paint in PIXELS of the model: X in [-16, 16], Y in [0, 64]
    d.box(d.leaf_l, "core", -12, 0, 0, 54, -1, 1, side="wood_side")
    d.export(icon=True)                            # bbmodel (models/entity + blockbench), texture, 16x16 icon
    d.preview(out_png, refs=[...])                 # face / 3/4 / open / back renders next to the reference crops

UNITS: every coordinate given to this library is in model PIXELS (1/16 block): X in [-16, 16] (+X = right seen from
the front), Y in [0, 64], Z in [-8, 8] (+Z = the front face). The model file is in blocks (contract of the doors:
origin = middle of the bottom of the opening, in the middle of the thickness).

THE PROJECTION. F covers the whole opening seen from the front, B the whole opening seen from the back but painted
in model coordinates (B mirrors itself when it is stored). A face of a box that looks to +Z shows the part of F in
front of it, a face that looks to -Z the part of B behind it: an iron band painted on F shows on its raised box, a
rivet on the band, etc. Moving parts that slide or turn over another surface (gears) get their own picture
(d.picture(name)) so the surface under them stays plain. Side faces use tiled materials (d.material).

LEAVES: leaf_l covers X [-16 + post, 0], leaf_r [0, 16 - post]; pivots on the hinge edges (X = -16 + post and
16 - post, Z = 0). A leaf is 2 px of core (Z [-1, 1]) and 1 px of relief on each face, Z in [-2, 2] = 4/16; only
the handles stick out further (far from the hinge). The posts are full depth only outside X = +-(16 - post + 2) so
that the leaf, turned 90 degrees round its hinge, never goes through them (the 2 px strip next to the leaf is
front-only, a door stop).
"""
import json
import math
import os
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
SEM_FACE = {"+1": "west", "-1": "east", "+2": "up", "-2": "down", "+3": "north", "-3": "south"}
GAP = 0.25               # 1/64 block: the smallest clearance between two parts (no z-fighting, no rubbing)
Bone, EYE, v3 = tl.Bone, tl.EYE, tl.v3
ASSETS, ROOT = tl.ASSETS, tl.ROOT
PPB = 16
PW, PH = 32, 64          # the opening in pixels
SCRATCH = "/tmp/claude-0/-home-user-medieval-ships/2a9b6be4-7c0a-5b40-ad8d-40cfe82b9e67/scratchpad"
REF_DIR = SCRATCH + "/doors_ref"


# ---------------------------------------------------------------- colours
def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def shade(c, k):
    return np.clip(np.asarray(c, float) * k, 0, 255)


def mix(a, b, t):
    return np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t


# ---------------------------------------------------------------- pictures
class Canvas:
    """A picture in model pixels: (X, Y) with X in [x0, x0 + w), Y in [y0, y0 + h) (Y up). Pixel (X, Y) is the
    texel covering X..X+1, Y..Y+1. a = h x w x 4 array, row 0 = top."""

    def __init__(self, w, h, x0=-16, y0=0, seed=1):
        self.w, self.h, self.x0, self.y0 = w, h, x0, y0
        self.a = np.zeros((h, w, 4), float)
        self.rng = np.random.default_rng(seed)

    # -- low level
    def _ij(self, X, Y):
        return int(X - self.x0), int(self.h - 1 - (Y - self.y0))

    def inside(self, X, Y):
        i, j = self._ij(X, Y)
        return 0 <= i < self.w and 0 <= j < self.h

    def put(self, X, Y, c, a=255):
        i, j = self._ij(X, Y)
        if 0 <= i < self.w and 0 <= j < self.h:
            self.a[j, i, :3] = c
            self.a[j, i, 3] = a

    def get(self, X, Y):
        i, j = self._ij(X, Y)
        return self.a[j, i, :3].copy()

    def scale_px(self, X, Y, k):
        i, j = self._ij(X, Y)
        if 0 <= i < self.w and 0 <= j < self.h:
            self.a[j, i, :3] = np.clip(self.a[j, i, :3] * k, 0, 255)

    def rect(self, X0, Y0, X1, Y1, c, noise=0, a=255):
        for X in range(int(X0), int(X1)):
            for Y in range(int(Y0), int(Y1)):
                n = self.rng.normal(0, noise) if noise else 0
                self.put(X, Y, np.clip(np.asarray(c, float) + n, 0, 255), a)

    def clear(self, X0, Y0, X1, Y1):
        self.rect(X0, Y0, X1, Y1, (0, 0, 0), a=0)

    # -- materials
    def planks_v(self, X0, Y0, X1, Y1, widths, base, dark=None, light=None, knots=0.05, joints=0.0, seam=True):
        """Vertical planks (widths in px, left to right), dark seams, grain streaks, a few knots."""
        base = np.asarray(base, float)
        dark = shade(base, 0.55) if dark is None else np.asarray(dark, float)
        light = shade(base, 1.18) if light is None else np.asarray(light, float)
        X = X0
        for k, w in enumerate(widths):
            pc = shade(base, 0.9 + 0.2 * self.rng.random())
            streak = [self.rng.random() for _ in range(w)]
            joint = Y0 + int(self.rng.integers(6, max(7, Y1 - Y0 - 4))) if self.rng.random() < joints else None
            for x in range(X, min(X + w, X1)):
                col = x - X
                for y in range(Y0, Y1):
                    c = pc * (0.94 + 0.12 * streak[col]) + self.rng.normal(0, 4)
                    if (y * 7 + x * 13 + k * 5) % 11 == 0:
                        c = c * 0.9
                    if seam and col == 0:
                        c = mix(c, dark, 0.75)
                    elif col == 1 and w > 2:
                        c = mix(c, light, 0.35)
                    if joint is not None and y == joint:
                        c = mix(c, dark, 0.8)
                    self.put(x, y, np.clip(c, 0, 255))
            if knots and self.rng.random() < knots * (Y1 - Y0) / 8 and w >= 3:
                kx, ky = X + 1 + int(self.rng.integers(0, max(1, w - 2))), int(self.rng.integers(Y0 + 2, max(Y0 + 3, Y1 - 2)))
                self.put(kx, ky, dark)
                self.put(kx, ky + 1, mix(dark, pc, 0.5))
            X += w

    def planks_h(self, X0, Y0, X1, Y1, heights, base, dark=None, light=None, joints=0.6):
        """Horizontal planks (heights in px, bottom to top), dark lower seams, lit upper edge, end joints."""
        base = np.asarray(base, float)
        dark = shade(base, 0.55) if dark is None else np.asarray(dark, float)
        light = shade(base, 1.2) if light is None else np.asarray(light, float)
        Y = Y0
        for k, hgt in enumerate(heights):
            pc = shade(base, 0.9 + 0.2 * self.rng.random())
            joint = X0 + int(self.rng.integers(3, max(4, X1 - X0 - 3))) if self.rng.random() < joints else None
            for y in range(Y, min(Y + hgt, Y1)):
                row = y - Y
                for x in range(X0, X1):
                    c = pc * (0.95 + 0.1 * math.sin(x * 0.9 + k * 2.1 + y * 0.3)) + self.rng.normal(0, 4)
                    if row == 0:
                        c = mix(c, dark, 0.7)
                    elif row == hgt - 1 and hgt > 2:
                        c = mix(c, light, 0.4)
                    if joint is not None and x == joint:
                        c = mix(c, dark, 0.8)
                    self.put(x, y, np.clip(c, 0, 255))
            Y += hgt

    def metal(self, X0, Y0, X1, Y1, base, bevel=True, noise=5, rust=None, rust_p=0.0, dents=0.08):
        base = np.asarray(base, float)
        for x in range(X0, X1):
            for y in range(Y0, Y1):
                c = base * (1 + dents * math.sin(x * 1.7 + y * 0.6) * math.cos(y * 1.3 - x * 0.4)) + self.rng.normal(0, noise)
                if rust is not None and self.rng.random() < rust_p:
                    c = mix(c, rust, 0.6)
                if bevel:
                    if y == Y1 - 1:
                        c = c * 1.14
                    elif y == Y0 or x == X1 - 1:
                        c = c * 0.78
                self.put(x, y, np.clip(c, 0, 255))

    def rivet(self, X, Y, light=(196, 196, 202), dark=(40, 40, 44)):
        self.put(X, Y, light)
        if self.inside(X + 1, Y - 1):
            c = self.get(X + 1, Y - 1)
            self.put(X + 1, Y - 1, mix(c, dark, 0.5))

    def strap_h(self, X0, X1, Y0, hgt, base, every=6, phase=2, rivets=True, light=None):
        """A horizontal iron band hgt px high, bevelled, rivets every `every` px along it."""
        self.metal(X0, Y0, X1, Y0 + hgt, base, noise=4)
        if rivets:
            ry = Y0 + hgt // 2
            for x in range(X0 + phase, X1 - 1, every):
                self.rivet(x, ry, light=light if light is not None else shade(base, 2.0))

    def strap_v(self, X0, Y0, Y1, wid, base, every=6, phase=2, rivets=True, light=None):
        self.metal(X0, Y0, X0 + wid, Y1, base, noise=4)
        if rivets:
            rx = X0 + wid // 2
            for y in range(Y0 + phase, Y1 - 1, every):
                self.rivet(rx, y, light=light if light is not None else shade(base, 2.0))

    def line(self, X0, Y0, X1, Y1, wid, base, rivets=4):
        """A painted diagonal band (used on the pictures under a rotated relief strap)."""
        n = int(max(abs(X1 - X0), abs(Y1 - Y0)) * 2) + 1
        for k in range(n + 1):
            t = k / n
            x, y = X0 + (X1 - X0) * t, Y0 + (Y1 - Y0) * t
            for dx in range(-wid // 2, wid - wid // 2):
                self.put(math.floor(x + dx), math.floor(y), shade(base, 0.95 + 0.1 * self.rng.random()))

    def stone_wall(self, labels, X0, Y0, base, light=None, dark=None, mortar=None, seed_k=0.12):
        """Stones from a label image (h x w ints, -1 = nothing, 0 = mortar, >0 = stone id; row 0 = top) placed with
        its bottom-left pixel at (X0, Y0): per stone tint, lit top / left edges, dark lower / right edges, speckles."""
        base = np.asarray(base, float)
        light = shade(base, 1.22) if light is None else light
        dark = shade(base, 0.7) if dark is None else dark
        mortar = shade(base, 0.5) if mortar is None else mortar
        h, w = labels.shape
        tint = {}
        for j in range(h):
            for i in range(w):
                L = labels[j, i]
                if L < 0:
                    continue
                X, Y = X0 + i, Y0 + (h - 1 - j)
                if L == 0:
                    self.put(X, Y, np.asarray(mortar) + self.rng.normal(0, 3))
                    continue
                if L not in tint:
                    tint[L] = 0.86 + 0.26 * ((L * 0.6180339) % 1.0)
                c = base * tint[L] + self.rng.normal(0, 5)
                up = labels[j - 1, i] if j > 0 else -2
                lf = labels[j, i - 1] if i > 0 else -2
                dn = labels[j + 1, i] if j < h - 1 else -2
                rt = labels[j, i + 1] if i < w - 1 else -2
                if up != L or lf != L:
                    c = mix(c, light, 0.55)
                elif dn != L or rt != L:
                    c = mix(c, dark, 0.55)
                if self.rng.random() < seed_k:
                    c = c * (0.85 if self.rng.random() < 0.5 else 1.1)
                self.put(X, Y, np.clip(c, 0, 255))

    def glow_pane(self, X0, Y0, X1, Y1, hot=(255, 236, 160), warm=(255, 184, 72), edge=(214, 118, 34)):
        cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2 - 0.3 * (Y1 - Y0) * 0.2
        rx, ry = max(1, (X1 - X0) / 2), max(1, (Y1 - Y0) / 2)
        for x in range(X0, X1):
            for y in range(Y0, Y1):
                d = math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry)
                c = mix(hot, warm, min(1, d * 1.2)) if d < 0.85 else mix(warm, edge, min(1, (d - 0.85) * 2.5))
                self.put(x, y, np.clip(np.asarray(c) + self.rng.normal(0, 3), 0, 255))

    def fill_from(self, other):
        m = other.a[..., 3] > 0
        self.a[m] = other.a[m]


def label_rows(rows):
    """Label image from strings ('.' = nothing, '#' = mortar, letters / digits = stones)."""
    h, w = len(rows), max(len(r) for r in rows)
    lab = -np.ones((h, w), int)
    ids = {}
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch == ".":
                continue
            if ch == "#":
                lab[j, i] = 0
                continue
            lab[j, i] = ids.setdefault(ch, len(ids) + 1)
    return lab


# ---------------------------------------------------------------- atlas
class _Packer:
    def __init__(self, size):
        self.size, self.x, self.y, self.row = size, 0, 0, 0

    def alloc(self, w, h):
        if self.x + w > self.size:
            self.x, self.y, self.row = 0, self.y + self.row, 0
        if self.y + h > self.size:
            raise ValueError("atlas full")
        r = (self.x, self.y, w, h)
        self.x += w
        self.row = max(self.row, h)
        return r


# ---------------------------------------------------------------- the door
class Door:
    def __init__(self, name, post=4, top=54, size=256, seed=7):
        tl.setup(name)
        self.name, self.size, self.seed = name, size, seed
        self.post, self.top = post, top
        self.pk = _Packer(size)
        self.regions, self.canvases, self.mirror, self.pictures = {}, {}, {}, set()
        self.F = self.picture("front")
        self.B = self.picture("back", mirror=True)
        self.root = Bone(name)
        self.frame = Bone("frame", parent=self.root)
        self.hx = 16 - post                  # hinge X of the right leaf (left leaf: -hx)
        self.leaf_l = Bone("leaf_l", origin=(-self.hx / PPB, 0.0, 0.0), parent=self.root)
        self.leaf_r = Bone("leaf_r", origin=(self.hx / PPB, 0.0, 0.0), parent=self.root)
        self._detail = None
        self.model = None

    def detail(self):
        if self._detail is None:
            self._detail = Bone("detail", parent=self.frame)
        return self._detail

    # -- atlas
    def picture(self, name, w=PW, h=PH, x0=-16, y0=0, mirror=False):
        c = Canvas(w, h, x0, y0, seed=self.seed * 101 + len(self.canvases) * 31)
        self.canvases[name] = c
        self.mirror[name] = mirror
        self.pictures.add(name)
        self.regions[name] = self.pk.alloc(w, h)
        return c

    def material(self, name, painter, w=32, h=64):
        c = Canvas(w, h, 0, 0, seed=self.seed * 7 + len(self.canvases) * 17)
        painter(c)
        self.canvases[name] = c
        self.mirror[name] = False
        self.regions[name] = self.pk.alloc(w, h)
        return c

    def atlas(self):
        arr = np.zeros((self.size, self.size, 4), np.uint8)
        for name, c in self.canvases.items():
            u, v, w, h = self.regions[name]
            a = c.a[:, ::-1] if self.mirror[name] else c.a
            arr[v:v + h, u:u + w] = np.clip(a, 0, 255).astype(np.uint8)
        return arr

    # -- cubes
    def _sub(self, pic, X0, X1, Y0, Y1):
        c = self.canvases[pic]
        if self.mirror[pic]:
            u0, u1 = (c.x0 + c.w - X1) / c.w, (c.x0 + c.w - X0) / c.w
        else:
            u0, u1 = (X0 - c.x0) / c.w, (X1 - c.x0) / c.w
        v0, v1 = (c.y0 + c.h - Y1) / c.h, (c.y0 + c.h - Y0) / c.h
        return [u0, v0, u1, v1]

    def box(self, bone, name, X0, X1, Y0, Y1, Z0, Z1, front="front", back="back", side="wood_side", top=None,
            bottom=None, left=None, right=None):
        """Axis-aligned box in model pixels. front / back: a picture name (projected), a material name (tiled) or
        None (no face); side: material of the four other faces unless top / bottom / left / right say otherwise."""
        X0, X1 = min(X0, X1), max(X0, X1)
        Y0, Y1 = min(Y0, Y1), max(Y0, Y1)
        Z0, Z1 = min(Z0, Z1), max(Z0, Z1)
        regs = {"+3": front, "-3": back, "+2": top if top is not None else side, "-2": bottom if bottom is not None else side,
                "+1": right if right is not None else side, "-1": left if left is not None else side}
        regs = {k: (v if v else None) for k, v in regs.items()}
        c = gg.add_cube(bone, name, ((X0 + X1) / 32, (Y0 + Y1) / 32, (Z0 + Z1) / 32), EYE,
                        ((X1 - X0) / 16, (Y1 - Y0) / 16, (Z1 - Z0) / 16), {"all": None, **regs})
        for sem, bbface in (("+3", "north"), ("-3", "south")):
            r = regs[sem]
            if r in self.pictures:
                c.faces[bbface]["sub"] = self._sub(r, X0, X1, Y0, Y1)
        c._px = [X0, X1, Y0, Y1, Z0, Z1]
        c._regs = regs
        return c

    def rebox(self, c, X0, X1, Y0, Y1, Z0, Z1, name=None, drop=()):
        """Replaces the box c (made by box()) by the same box with new bounds (faces of `drop` removed)."""
        regs = dict(c._regs)
        for sem in drop:
            regs[sem] = None
        for sem, bbface in SEM_FACE.items():          # faces already removed stay removed
            if c.faces.get(bbface) is None:
                regs[sem] = None
        bone = c.bone
        idx = bone.cubes.index(c)
        bone.cubes.remove(c)
        n = self.box(bone, name or c.name, X0, X1, Y0, Y1, Z0, Z1, front=regs["+3"], back=regs["-3"], side=None,
                     top=regs["+2"] or "", bottom=regs["-2"] or "", left=regs["-1"] or "", right=regs["+1"] or "")
        for sem, bbface in SEM_FACE.items():
            if regs[sem] is None:
                n.faces[bbface] = None
        bone.cubes.remove(n)
        bone.cubes.insert(idx, n)
        return n

    def mask_boxes(self, bone, name, mask, X0, Y0, Z0, Z1, **kw):
        """Boxes covering a mask (h x w bools, row 0 = top) whose bottom-left pixel is at (X0, Y0): runs of each row
        merged downwards with identical runs. Returns the boxes."""
        h, w = mask.shape
        used = np.zeros_like(mask, bool)
        out = []
        for j in range(h):
            i = 0
            while i < w:
                if not mask[j, i] or used[j, i]:
                    i += 1
                    continue
                i1 = i
                while i1 < w and mask[j, i1] and not used[j, i1]:
                    i1 += 1
                j1 = j + 1
                while j1 < h and mask[j1, i:i1].all() and not used[j1, i:i1].any():
                    j1 += 1
                used[j:j1, i:i1] = True
                out.append(self.box(bone, "%s_%d" % (name, len(out)), X0 + i, X0 + i1, Y0 + (h - j1), Y0 + (h - j), Z0, Z1, **kw))
                i = i1
        return out

    def strap(self, bone, name, P0, P1, wid, Z0, Z1, region):
        """A straight band from P0 to P1 (model px, in the XY plane) wid px wide between Z0 and Z1: a rotated box,
        its faces tiled with `region` along its length (diagonal braces)."""
        p0, p1 = v3(P0[0], P0[1], 0) / 16, v3(P1[0], P1[1], 0) / 16
        d = p1 - p0
        L = np.linalg.norm(d)
        u = d / L
        vv = v3(-u[1], u[0], 0)
        axes = np.column_stack([u, vv, v3(0, 0, 1)])
        c = (p0 + p1) / 2
        c[2] = (Z0 + Z1) / 32
        regs = dict(region) if isinstance(region, dict) else {"all": region}
        if Z0 >= 1 - 1e-6:          # lying on the front of the core (Z [-1, 1]): its back can never be seen
            regs["-3"] = None
        elif Z1 <= -1 + 1e-6:       # on the back of the core
            regs["+3"] = None
        return gg.add_cube(bone, name, c, axes, (L, wid / 16, (Z1 - Z0) / 16), regs, u_dir=u)

    def gear(self, parent, name, cx, cy, r_out, r_in, teeth, Z0, Z1, metal, hub=None, spokes=4, pic=None):
        """A cut-out gear (bone `name`, pivot = its centre) of radius r_out px with `teeth` teeth of depth
        r_out - r_in, spokes and a hub; painted on its own picture `pic` so the surface behind stays plain."""
        metal = np.asarray(metal, float)
        light, dark = shade(metal, 1.3), shade(metal, 0.6)
        bone = Bone(name, origin=(cx / 16, cy / 16, (Z0 + Z1) / 32), parent=parent)
        if pic is None:
            pic = "pic_" + name
            self.picture(pic)
        C = self.canvases[pic]
        X0, X1 = int(math.floor(cx - r_out)), int(math.ceil(cx + r_out))
        Y0, Y1 = int(math.floor(cy - r_out)), int(math.ceil(cy + r_out))
        w, h = X1 - X0, Y1 - Y0
        mask = np.zeros((h, w), bool)
        hub = hub or 1.6
        inner_hole = r_in - 1.05
        for j in range(h):
            for i in range(w):
                x, y = X0 + i + 0.5 - cx, Y0 + (h - 1 - j) + 0.5 - cy
                r = math.hypot(x, y)
                a = math.atan2(y, x)
                rr = r_out if math.cos(a * teeth) > 0.0 else r_in
                is_spoke = any(abs(math.sin(a - k * math.pi / spokes)) * r < 0.55 for k in range(spokes))
                mask[j, i] = r <= rr and (r > inner_hole or is_spoke or r < hub)
        for j in range(h):
            for i in range(w):
                if not mask[j, i]:
                    continue
                x, y = X0 + i + 0.5 - cx, Y0 + (h - 1 - j) + 0.5 - cy
                r = math.hypot(x, y)
                edge = any(not (0 <= j + dj < h and 0 <= i + di < w) or not mask[j + dj, i + di]
                           for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                c = metal * (0.97 + 0.08 * math.sin(i * 1.3 + j * 0.7))
                if edge:
                    c = mix(c, dark, 0.55) if (x - y) > 0 else mix(c, light, 0.45)
                if r < hub:
                    c = light if (x < 0 < y) else shade(metal, 0.7)
                C.put(X0 + i, Y0 + (h - 1 - j), np.clip(c, 0, 255))
        self.mask_boxes(bone, name + "_c", mask, X0, Y0, Z0, Z1, front=pic, back=None, side="gear_side")
        return bone

    def lantern(self, bone, name, X, Y, Z, size=4, metal="iron"):
        """A lantern centred on (X, Y, Z) (px): lit glass (glow_*), corner posts, base, cap, dome, finial and hanger,
        built here (not by tools/lanterns.py) so that no two faces are closer than GAP. size = the glass width + 1.2;
        the cap is size + 0.2 wide, the whole lantern about 1.9 x size high (glass centre at Y)."""
        g = (size - 1.2) / 2                 # half width of the glass
        hg = 0.7 * size                      # half height of the glass
        m = metal

        def b(n, x0, x1, y0, y1, z0, z1, **kw):
            return self.box(bone, n, X + x0, X + x1, Y + y0, Y + y1, Z + z0, Z + z1, front=kw.get("f", m), back=kw.get("f", m),
                            side=kw.get("s", m), top=kw.get("t"), bottom=kw.get("bt"))
        b("glow_" + name, -g, g, -hg, hg, -g, g, f="lantern", s="lantern", t=m, bt=m)
        for k, (sx, sz) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
            b("%s_post_%d" % (name, k), sx * g - 0.3, sx * g + 0.3, -hg - 0.25, hg + 0.25, sz * g - 0.3, sz * g + 0.3)
        b(name + "_base", -g - 0.6, g + 0.6, -hg - 0.5, -hg, -g - 0.6, g + 0.6)
        b(name + "_cap", -g - 0.7, g + 0.7, hg, hg + 0.5, -g - 0.7, g + 0.7)
        dh = max(0.5, g - 0.6)
        b(name + "_dome", -dh, dh, hg + 0.25, hg + 0.75, -dh, dh)
        b(name + "_hanger", -0.5, 0.5, hg + 0.75, hg + 1.5, -0.25, 0.25)
        return Y + hg + 1.5

    def chain(self, bone, name, X, Y0, Y1, Z, region="chain_side"):
        """A hanging chain of alternating links between Y0 (bottom) and Y1 (top)."""
        y, k = Y0, 0
        while y < Y1 - 0.5:
            h = max(0.5, min(1.5, Y1 - y))
            if k % 2 == 0:
                gg.add_cube(bone, "%s_%d" % (name, k), (X / 16, (y + h / 2) / 16, Z / 16), EYE, (1 / 16, h / 16, 0.5 / 16), region)
            else:
                gg.add_cube(bone, "%s_%d" % (name, k), (X / 16, (y + h / 2) / 16, Z / 16), EYE, (0.5 / 16, h / 16, 1 / 16), region)
            y += max(0.5, h - 0.25)
            k += 1

    # -- clearances of the leaves (1.32.0)
    def finalize(self, top_gap=False, seam_top=None, cover_side="wood_side", cover_back="back", seam_mat=None):
        """Makes the leaves fit the frame and each other without touching (no coplanar faces, nothing that goes
        through anything while both leaves turn 0 -> 90 degrees towards the back), then adds the seam cover.

        - the cores (Z within [-1, 1]) stop GAP/2 short of the seam (X = 0): the two seam edges never touch;
        - a front relief stays inside the circle of radius hx - 0.1 round its hinge (seen from above), so turning
          towards the back it never crosses the seam plane (the front corners of both leaves swing towards it);
        - the back reliefs stop 1 px (leaf_l) / 0.625 px (leaf_r) short of the seam;
        - top_gap: a leaf box reaching the top of the opening of the leaves (self.top) stops GAP below it;
        - the seam cover: a batten on the back of leaf_l, 1.5 px wide on its own leaf, that also runs GAP / 2 + 0.25
          px behind leaf_r (GAP behind its back face): from the front the seam shows it, dark, and no daylight."""
        hx = self.hx
        R = hx - 0.1
        for leaf, s in ((self.leaf_l, -1), (self.leaf_r, 1)):
            for c in list(_all_cubes(leaf)):
                px = getattr(c, "_px", None)
                if px is None or c.name.startswith("seam_"):
                    continue
                X0, X1, Y0, Y1, Z0, Z1 = px
                u0, u1 = (X0 + hx, X1 + hx) if s < 0 else (hx - X1, hx - X0)
                lim = hx - GAP / 2
                if Z1 > 1 + 1e-6:
                    lim = min(lim, math.sqrt(max(0.0, R * R - Z1 * Z1)))
                if Z0 < -1 - 1e-6:
                    lim = min(lim, hx - (1.0 if s < 0 else 0.625))
                Y1n = Y1
                if top_gap and Y1 > self.top - 1e-6:
                    Y1n = self.top - GAP
                if u1 <= lim + 1e-6 and Y1n == Y1:
                    continue
                u1 = min(u1, lim)
                if u1 <= u0 + 0.05 or Y1n <= Y0 + 0.05:
                    c.bone.cubes.remove(c)
                    continue
                if s < 0:
                    X1 = u1 - hx
                else:
                    X0 = hx - u1
                self.rebox(c, X0, X1, Y0, Y1n, Z0, Z1)
        top = seam_top if seam_top is not None else (self.top - (GAP if top_gap else 0))
        mat = seam_mat or cover_side
        self.box(self.leaf_l, "seam_cover", -1.5, GAP / 2 + 0.25, 0, top, -2.5, -1.25, front=mat, back=cover_back,
                 side=cover_side)
        self.box(self.leaf_l, "seam_fill", -1.5, -GAP / 2, 0, top, -1.25, -1, front=None, back=None, side=cover_side)

    def head_stop(self, Z0, Z1, mat, Y0=None, Y1=None, X=None, pic="front"):
        """Door stop of the head, on the frame in front of the top of the leaves (covers the GAP above them)."""
        X = X if X is not None else self.hx
        Y1 = self.top if Y1 is None else Y1
        Y0 = Y1 - 1.0 if Y0 is None else Y0
        return self.box(self.frame, "head_stop", -X, X, Y0, Y1, Z0, Z1, front=pic, back=mat, side=mat)

    def swept_heights(self, leaf_top, X0=-14.5, X1=14.5, Z0=-8.0, Z1=2.75, zl=(-2.5, 3.0), umax=None, step=0.5):
        """Highest leaf point passing over each cell (step px) of the region behind the leaves while both turn 0 -> 90
        degrees towards the back: {(i, k): height} with X = X0 + i * step, Z = Z0 + k * step; leaf_top(X) gives the
        height of the leaf at X (left leaf; the right one is its mirror)."""
        hx = self.hx
        umax = hx + 0.5 if umax is None else umax
        nx, nz = int(round((X1 - X0) / step)), int(round((Z1 - Z0) / step))
        H = np.full((nx, nz), -1.0)
        us = np.arange(0, umax + 1e-6, 0.125)
        zs = np.arange(zl[0], zl[1] + 1e-6, 0.25)
        th = np.radians(np.arange(0, 90.01, 0.5))
        U, Zl, T = np.meshgrid(us, zs, th, indexing="ij")
        hgt = np.vectorize(lambda u: leaf_top(-hx + min(u, hx - 0.01)))(U) + 0.5
        X = -hx + U * np.cos(T) + Zl * np.sin(T)
        Z = -U * np.sin(T) + Zl * np.cos(T)
        for sx in (1, -1):
            XX = X * sx
            i = np.floor((XX - X0) / step).astype(int)
            k = np.floor((Z - Z0) / step).astype(int)
            ok = (i >= 0) & (i < nx) & (k >= 0) & (k < nz)
            np.maximum.at(H, (i[ok], k[ok]), hgt[ok])
        # neighbours too (a cell touched by a corner of a sample)
        Hn = H.copy()
        for di in (-1, 0, 1):
            for dk in (-1, 0, 1):
                Hn = np.maximum(Hn, np.roll(np.roll(H, di, 0), dk, 1))
        return Hn

    def knuckle(self, bone, name, px, Y0, Y1, mat, r=1.35):
        """A round-looking hinge barrel on the hinge axis (X = px, Z = 0): a square and the same square turned 45
        degrees (8 sides), its corners within 1.91 px of the axis so that it turns in place."""
        self.box(bone, name, px - r, px + r, Y0, Y1, -r, r, front=mat, back=mat, side=mat)
        c = math.sqrt(0.5)
        axes = np.array([[c, 0, -c], [0, 1, 0], [c, 0, c]])
        gg.add_cube(bone, name + "_45", (px / 16, (Y0 + Y1) / 32, 0.0), axes, (2 * r / 16, (Y1 - Y0 - 2 * GAP) / 16, 2 * r / 16), mat)

    # -- export
    def export(self, icon=True):
        arr = self.atlas()
        gn.REGIONS = {k: (0,) + r for k, r in self.regions.items()}
        gn.SIZE = self.size
        gg.REGIONS = dict(self.regions)
        gg.SIZE = self.size
        tex_path = os.path.join(ASSETS, "textures/entity", self.name + ".png")
        os.makedirs(os.path.dirname(tex_path), exist_ok=True)
        Image.fromarray(arr, "RGBA").save(tex_path)
        with open(tex_path, "rb") as f:
            png = f.read()
        textures = [gn.texture_entry(self.name + ".png", self.size, png, "entity", self.name + ".png")]
        textures[0]["id"] = "0"
        outs = [os.path.join(ROOT, "blockbench/%s.bbmodel" % self.name),
                os.path.join(ASSETS, "models/entity/%s.bbmodel" % self.name)]
        import zfight
        orig = zfight.fix
        zfight.fix = lambda root, passes=0: _resolve(self, root)
        try:
            self.model = gn.export(self.root, [], textures, outs, name=self.name, visible_box=(4, 6, 0))
        finally:
            zfight.fix = orig
        self.tex = arr
        self.check_bounds()
        if icon:
            self.icon(os.path.join(ASSETS, "textures/item/%s.png" % self.name))
        print("%s: %d cubes, texture %dx%d" % (self.name, len(self.model["elements"]), self.size, self.size))
        return self.model

    def check_bounds(self):
        lo, hi = np.full(3, 1e9), np.full(3, -1e9)
        for e in self.model["elements"]:
            f, t = np.array(e["from"], float), np.array(e["to"], float)
            o = np.array(e.get("origin", [0, 0, 0]), float)
            R = pv.rot_zyx(e.get("rotation", [0, 0, 0]))
            for cx in (f[0], t[0]):
                for cy in (f[1], t[1]):
                    for cz in (f[2], t[2]):
                        p = R @ (np.array([cx, cy, cz]) - o) + o
                        q = np.array([-p[0] / 16, p[1] / 16, -p[2] / 16])
                        lo, hi = np.minimum(lo, q), np.maximum(hi, q)
        ok = lo[0] >= -1.02 and hi[0] <= 1.02 and lo[1] >= -0.02 and hi[1] <= 4.02 and lo[2] >= -0.52 and hi[2] <= 0.52
        print("bounds x [%.3f, %.3f] y [%.3f, %.3f] z [%.3f, %.3f] %s" % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2],
                                                                         "OK" if ok else "OUT OF THE OPENING"))
        return ok

    def bones(self):
        out = []

        def walk(g, depth):
            out.append("%s%s origin(blocks)=(%.4f, %.4f, %.4f) cubes=%d" % (
                "  " * depth, g["name"], -g["origin"][0] / 16, g["origin"][1] / 16, -g["origin"][2] / 16,
                sum(1 for c in g["children"] if not isinstance(c, dict))))
            for c in g["children"]:
                if isinstance(c, dict):
                    walk(c, depth + 1)
        for g in self.model["outliner"]:
            walk(g, 0)
        return out

    # -- icon and previews
    def icon(self, path):
        if getattr(self, "icon_map", None):
            rows, pal = self.icon_map
            assert len(rows) == 16 and all(len(r) == 16 for r in rows), [len(r) for r in rows]
            out = np.zeros((16, 16, 4), np.uint8)
            for j, r in enumerate(rows):
                for i, ch in enumerate(r):
                    if ch != ".":
                        out[j, i, :3] = np.clip(pal[ch], 0, 255)
                        out[j, i, 3] = 255
            os.makedirs(os.path.dirname(path), exist_ok=True)
            Image.fromarray(out, "RGBA").save(path)
            return
        quads = pv.build_mesh(json.loads(json.dumps(self.model)), {})
        big = render(quads, [self.tex.astype(float)], 32, 64, eye=(0, 2, 30), target=(0, 2, 0), ortho=2.0,
                     bg=None, flat=True)
        a = np.array(big).astype(float)
        small = np.zeros((16, 8, 4))
        for j in range(16):
            for i in range(8):
                blk = a[j * 4:j * 4 + 4, i * 4:i * 4 + 4]
                m = blk[..., 3] > 0
                if m.sum() >= 6:
                    small[j, i, :3] = blk[..., :3][m].mean(0)
                    small[j, i, 3] = 255
        # contrast like a hand-made icon: darken the outline, lift the middle
        out = np.zeros((16, 16, 4))
        out[:, 4:12] = small
        for j in range(16):
            for i in range(16):
                if out[j, i, 3] == 0:
                    continue
                edge = any(not (0 <= j + dj < 16 and 0 <= i + di < 16) or out[j + dj, i + di, 3] == 0
                           for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                out[j, i, :3] = np.clip(out[j, i, :3] * (0.62 if edge else 1.12), 0, 255)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        Image.fromarray(out.astype(np.uint8), "RGBA").save(path)

    def preview(self, out, refs=(), open_deg=90.0):
        model = json.loads(json.dumps(self.model))
        tex = [self.tex.astype(float)]
        closed = pv.build_mesh(model, {})
        _set_rot(model["outliner"], "leaf_l", [0, open_deg, 0])
        _set_rot(model["outliner"], "leaf_r", [0, -open_deg, 0])
        opened = pv.build_mesh(model, {})
        bg = (44, 42, 46)
        Hh = 560
        views = [
            ("face", closed, dict(W=290, H=Hh, eye=(0, 2.0, 40), target=(0, 2.0, 0), ortho=2.3)),
            ("3/4", closed, dict(W=330, H=Hh, eye=(-3.6, 3.0, 6.0), target=(0, 1.9, 0), fov=42)),
            ("ouverte 90", opened, dict(W=330, H=Hh, eye=(3.0, 2.8, 6.4), target=(0, 1.9, -0.3), fov=42)),
            ("arriere", closed, dict(W=290, H=Hh, eye=(0, 2.0, -40), target=(0, 2.0, 0), ortho=2.3)),
            ("ouverte dessus", opened, dict(W=330, H=Hh, eye=(-2.4, 6.5, -4.0), target=(0, 1.6, -0.4), fov=42)),
        ]
        ims = []
        for title, quads, kw in views:
            im = render(quads, tex, bg=bg, **kw)
            ImageDraw.Draw(im).text((6, 4), title, fill=(235, 225, 200))
            ims.append(im)
        for path, box in refs:
            im = Image.open(path).convert("RGB").crop(box)
            s = (Hh - 20) / im.size[1]
            im = im.resize((max(1, int(im.size[0] * s)), Hh - 20), Image.NEAREST)
            canvas = Image.new("RGB", (im.size[0], Hh), bg)
            canvas.paste(im, (0, 16))
            ImageDraw.Draw(canvas).text((6, 2), "ref " + os.path.basename(path), fill=(235, 225, 200))
            ims.append(canvas)
        Wt = sum(i.size[0] for i in ims) + 6 * (len(ims) - 1)
        sheet = Image.new("RGB", (Wt, Hh), (20, 20, 22))
        x = 0
        for i in ims:
            sheet.paste(i, (x, 0))
            x += i.size[0] + 6
        os.makedirs(os.path.dirname(out), exist_ok=True)
        sheet.save(out)
        print("wrote", out)
        return sheet


def _covered(f, g, tol=1e-4):
    """Is the face rectangle f inside the face rectangle g (coplanar)?"""
    for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        q = f["p"] + a * f["e1"] + b * f["e2"] - g["p"]
        for e in (g["e1"], g["e2"]):
            L = np.linalg.norm(e)
            if L > 1e-9 and abs(np.dot(q, e / L)) > L + tol:
                return False
    return True


def _all_cubes(b):
    yield from list(b.cubes)
    for ch in b.children:
        yield from _all_cubes(ch)


def _face_list(root):
    import zfight
    return zfight._faces(root)


def _pairs(root, tol=1e-4 / 1.0):
    """Coplanar overlapping face pairs (plane distance < tol blocks, overlap > 1e-4 block), any direction."""
    from collections import defaultdict
    faces = _face_list(root)
    buckets = defaultdict(list)
    for i, f in enumerate(faces):
        n = f["n"]
        sgn = 1
        for x in n:
            if abs(x) > 1e-3:
                sgn = 1 if x > 0 else -1
                break
        f["cn"], f["d"] = n * sgn, float(np.dot(n * sgn, f["p"]))
        buckets[tuple(np.round(n * sgn * 50).astype(int))].append(i)
    out = []
    for idx in buckets.values():
        idx.sort(key=lambda i: faces[i]["d"])
        for a in range(len(idx)):
            f = faces[idx[a]]
            for b in range(a + 1, len(idx)):
                g = faces[idx[b]]
                if g["d"] - f["d"] > tol:
                    break
                if f["cube"] is g["cube"] or abs(np.dot(f["cn"], g["cn"])) < 0.99999:
                    continue
                if _overlap(f, g, 1e-4):
                    out.append((f, g))
    return out


def _overlap(f, g, tol):
    def corners(h):
        return [h["p"] + a * h["e1"] + b * h["e2"] for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    cf, cg = corners(f), corners(g)
    for h in (f, g):
        for e in (h["e1"], h["e2"]):
            L = np.linalg.norm(e)
            if L < 1e-9:
                continue
            ax = e / L
            pf = [np.dot(q, ax) for q in cf]
            pg = [np.dot(q, ax) for q in cg]
            if min(max(pf), max(pg)) - max(min(pf), min(pg)) <= tol:
                return False
    return True


def _split(door, c, g):
    """Cuts the box c (made by box()) along an edge of the face g that crosses it; True when cut."""
    X0, X1, Y0, Y1, Z0, Z1 = c._px
    lo = [X0, Y0, Z0]
    hi = [X1, Y1, Z1]
    gc = [g["p"] + a * g["e1"] + b * g["e2"] for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    gp = np.array([[q[0] * 16, q[1] * 16, q[2] * 16] for q in gc])
    for k in range(3):
        for v in (gp[:, k].min(), gp[:, k].max()):
            v = round(float(v), 4)
            if lo[k] + 1e-3 < v < hi[k] - 1e-3:
                a_hi, b_lo = list(hi), list(lo)
                a_hi[k] = v
                b_lo[k] = v
                name = c.name
                n1 = door.rebox(c, lo[0], a_hi[0], lo[1], a_hi[1], lo[2], a_hi[2], name=name)
                regs = dict(n1._regs)
                n2 = door.box(n1.bone, name + "_s", b_lo[0], hi[0], b_lo[1], hi[1], b_lo[2], hi[2], front=regs["+3"],
                              back=regs["-3"], side=None, top=regs["+2"] or "", bottom=regs["-2"] or "",
                              left=regs["-1"] or "", right=regs["+1"] or "")
                for sem, bbface in SEM_FACE.items():
                    if n1.faces.get(bbface) is None:
                        n2.faces[bbface] = None
                return True
    return False


def _resolve(door, root, max_iter=400):
    """Replaces tools/zfight.fix for the doors. Two boxes of the same bone pressed together: the face covered by the
    other one is removed (it can never be seen); when neither covers the other, the box is cut along the edge of the
    other face first (no face is pushed out: that would make new coplanar faces). Faces of different bones, or
    looking the same way, are left alone and reported: they are fixed in the design (clearance GAP)."""
    import zfight
    removed = cuts = 0
    skip = set()
    for _ in range(max_iter):
        pairs = _pairs(root)
        todo = [(f, g) for f, g in pairs if np.dot(f["n"], g["n"]) < 0 and f["cube"].bone is g["cube"].bone
                and (id(f["cube"]), f["sem"], id(g["cube"]), g["sem"]) not in skip]
        if not todo:
            break
        gone, cut = set(), set()
        for f, g in todo:
            kf, kg = (id(f["cube"]), f["sem"]), (id(g["cube"]), g["sem"])
            if kf in gone or kg in gone or id(f["cube"]) in cut or id(g["cube"]) in cut:
                continue
            if _covered(f, g):
                f["cube"].faces[zfight.SEMANTIC_FACE[f["sem"]]] = None
                gone.add(kf)
                removed += 1
            elif _covered(g, f):
                g["cube"].faces[zfight.SEMANTIC_FACE[g["sem"]]] = None
                gone.add(kg)
                removed += 1
            elif getattr(f["cube"], "_px", None) is not None and _split(door, f["cube"], g):
                cut.add(id(f["cube"]))
                cuts += 1
            elif getattr(g["cube"], "_px", None) is not None and _split(door, g["cube"], f):
                cut.add(id(g["cube"]))
                cuts += 1
            else:
                print("resolve: cannot separate %s %s / %s %s" % (f["cube"].name, f["sem"], g["cube"].name, g["sem"]))
                skip.add((id(f["cube"]), f["sem"], id(g["cube"]), g["sem"]))
        if not gone and not cut:
            break
    left = _pairs(root)
    print("resolve: %d hidden faces removed, %d cuts, %d coplanar pairs left (other bones / same direction)" % (
        removed, cuts, len(left)))
    for f, g in left[:12]:
        print("   left: %s %s (%s)  %s %s (%s)" % (f["cube"].name, f["sem"], f["cube"].bone.name, g["cube"].name, g["sem"],
                                             g["cube"].bone.name))
    return removed


def _set_rot(groups, name, rot):
    for g in groups:
        if isinstance(g, dict):
            if g["name"] == name:
                g["rotation"] = rot
            _set_rot(g["children"], name, rot)


def render(quads, texs, W, H, eye, target, fov=None, ortho=None, bg=(28, 33, 48), flat=False):
    """tools/preview.py's rasteriser with Minecraft face shading (top 1.0, z sides 0.8, x sides 0.6, bottom 0.5);
    glow* faces full bright. bg None = transparent; flat = no shading (icon)."""
    eye, target = np.array(eye, float), np.array(target, float)
    fwd = target - eye
    fwd /= np.linalg.norm(fwd)
    up = np.array([0, 1, 0.0]) if abs(fwd[1]) < 0.99 else np.array([0, 0, 1.0])
    right = np.cross(fwd, up)
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    img = np.zeros((H, W, 4), float)
    if bg is not None:
        img[..., :3] = bg
        img[..., 3] = 255
    zbuf = np.full((H, W), np.inf)

    def project(p):
        d = p - eye
        x, y, z = d @ right, d @ up, d @ fwd
        if ortho:
            s = W / ortho
            return np.array([W / 2 + x * s, H / 2 - y * s, z])
        f = (H / 2) / math.tan(math.radians(fov) / 2)
        return np.array([W / 2 + x * f / z, H / 2 - y * f / z, z])

    for corners, uvs, glow, ti in quads:
        tex = texs[ti if ti < len(texs) else 0]
        tw, th = tex.shape[1], tex.shape[0]
        P = [project(c) for c in corners]
        n = np.cross(corners[1] - corners[0], corners[3] - corners[0])
        nn = np.linalg.norm(n)
        if nn < 1e-12:
            continue
        n /= nn
        if glow or flat:
            sh = 1.0
        else:
            sh = n[0] ** 2 * 0.6 + n[2] ** 2 * 0.8 + n[1] ** 2 * (1.0 if n[1] > 0 else 0.5)
        for tri in ((0, 1, 2), (0, 2, 3)):
            a, b, c = (P[i] for i in tri)
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
            region[..., :3][mask] = col[..., :3][mask] * sh
            region[..., 3][mask] = 255
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA" if bg is None else "RGBA").convert("RGBA" if bg is None else "RGB")


# ---------------------------------------------------------------- common material painters
def tile_wood(base, dark=None):
    def p(c):
        c.planks_v(0, 0, c.w, c.h, [4] * (c.w // 4), base, dark, knots=0.0)
    return p


def tile_metal(base, rust=None, p=0.0):
    def f(c):
        c.metal(0, 0, c.w, c.h, base, bevel=False, rust=rust, rust_p=p)
    return f


def tile_flat(col, noise=6):
    def f(c):
        c.rect(0, 0, c.w, c.h, col, noise=noise)
    return f


def tile_stone(base):
    def f(c):
        rows = ["AAAAAAA#BBBBBBBB", "AAAAAAA#BBBBBBBB", "AAAAAAA#BBBBBBBB", "AAAAAAA#BBBBBBBB", "AAAAAAA#BBBBBBBB",
                "AAAAAAA#BBBBBBBB", "AAAAAAA#BBBBBBBB", "################", "CCCC#DDDDDDDDDDD", "CCCC#DDDDDDDDDDD",
                "CCCC#DDDDDDDDDDD", "CCCC#DDDDDDDDDDD", "CCCC#DDDDDDDDDDD", "CCCC#DDDDDDDDDDD", "CCCC#DDDDDDDDDDD",
                "################"]
        lab = label_rows(rows)
        reps = (-(-c.h // 16), -(-c.w // 16))
        c.stone_wall(np.tile(lab, reps)[:c.h, :c.w], 0, 0, base)     # the whole canvas (no transparent texel)
    return f


def tile_lantern(c):
    img = Image.new("RGBA", (16, 16))
    paint_lamp_glass(img.load(), 0, 0, 16, 16)
    c.a = np.array(img).astype(float)


def tile_gold(c):
    for x in range(c.w):
        for y in range(c.h):
            t = 0.5 + 0.5 * math.sin(x * 0.7 + math.sin(y * 0.5) * 1.5)
            c.put(x, y, mix(rgb("9a6e1c"), rgb("f2cf6a"), t))


def ring_handle(d, bone, name, cx, cy, side_mat, plate_col, ring_col, Z=2.5, size=5, handle=None, round_ring=True):
    """A forged ring handle on the front face (Z = front of the relief under it): a square plate (painted, 0.75 px
    relief, its rivet) and a ring hanging from the plate centre, GAP in front of the plate. The ring is its own bone
    `handle` (pivot = the plate centre: a handle_<n> turns round z while the door unlocks), octagonal when
    round_ring (4 bars + 4 corner bars turned 45 degrees, GAP further forward)."""
    F = d.F
    s = size
    F.metal(cx - 1, cy - 1, cx + 2, cy + 2, plate_col, noise=3)
    F.rivet(cx, cy, light=shade(plate_col, 1.9))
    d.box(bone, name + "_plate", cx - 1.5, cx + 2.5, cy - 1.5, cy + 2.5, Z, Z + 0.75, side=side_mat, back=None)
    zf = Z + 0.75 + GAP
    hb = Bone(handle or (name + "_ring"), origin=((cx + 0.5) / 16, (cy + 0.5) / 16, (zf + 0.5) / 16), parent=bone)
    # the ring's shadow on the leaf
    sh = shade(F.get(cx, cy - 2), 0.55)
    xl, xr = cx + 0.5 - s / 2, cx + 0.5 + s / 2          # outer edges of the ring
    yt, yb = cy + 0.5, cy + 0.5 - s
    for y in range(int(math.floor(yb)), int(math.ceil(yt)) - 1):
        for x in (int(math.floor(xl)) + 1, int(math.ceil(xr)) - 1):
            if F.inside(x, y - 1):
                F.put(x, y - 1, mix(F.get(x, y - 1), sh, 0.5))
    k = 1.0 if round_ring else 0.0
    d.box(hb, name + "_l", xl, xl + 1, yb + k, yt - k, zf, zf + 1, front=side_mat, back=side_mat, side=side_mat)
    d.box(hb, name + "_r", xr - 1, xr, yb + k, yt - k, zf, zf + 1, front=side_mat, back=side_mat, side=side_mat)
    d.box(hb, name + "_b", xl + k, xr - k, yb, yb + 1, zf, zf + 1, front=side_mat, back=side_mat, side=side_mat)
    d.box(hb, name + "_t", xl + k, xr - k, yt - 1, yt, zf, zf + 1, front=side_mat, back=side_mat, side=side_mat)
    if round_ring:
        c = math.sqrt(0.5)
        for j, (x, y, sg) in enumerate(((xl + 0.85, yb + 0.85, 1), (xr - 0.85, yb + 0.85, -1), (xl + 0.85, yt - 0.85, -1),
                                         (xr - 0.85, yt - 0.85, 1))):
            axes = np.array([[c, -sg * c, 0], [sg * c, c, 0], [0, 0, 1]])
            gg.add_cube(hb, "%s_c%d" % (name, j), (x / 16, y / 16, (zf + 0.5 + GAP) / 16), axes, (1.9 / 16, 1 / 16, 1 / 16), side_mat)
    return hb
