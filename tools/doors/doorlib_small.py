"""Shared helpers of the three SMALL doors of 1.31.0 (2 blocks high x 1 wide, one leaf): porte_chene, porte_prison,
porte_vapeur. Written for tools/doors/generate_<id>.py; the medium / large doors have their own libraries.

How a small door is built (see generate_porte_chene.py for a complete example):

    import doorlib_small as ds
    d = ds.Door("porte_chene", size=256)          # own atlas, root bone + "frame" + "leaf_l" (pivot x -13/32, z 0)
    F, B, FF, FB = d.F, d.B, d.FF, d.FB            # pictures: leaf front / back, frame front / back (model coords)
    d.material("wood_side", ds.tile_wood(...))     # 32 x 64 tiles for the other faces (world-aligned UVs)
    d.build_frame("iron_side")                     # the rebated frame (front stops, rebate behind the hinge)
    d.core("wood_side", hole=...)                  # the leaf core z [-cz, cz]
    d.relief(d.leaf, "band", x0, x1, y0, y1, d.cz, 1 / 32, "iron_side")   # a piece ON a face (contact face left out)
    ds.ring_handle(...), ds.cube_gear(...)         # animated children (handle_<n>, gear_a/b_<n>): all opaque cubes
    d.export()                                     # bbmodel (models/entity + blockbench), texture, 16x16 icon

1.32.0 rules (checked by tools/doors/door_audit_small.py, which must report 0 defects): no hole seen through the
closed door or the leaf, no face mapping a transparent texel, no two drawn faces coplanar and overlapping (closed,
mechanisms moved, opened backwards), the leaf turning backwards by 90 degrees goes through nothing. Hence: front relief
stays inside the part of the leaf left visible by the stops (d.vx0..d.vx1, d.vy0..d.vy1, 1/64 off), parallel faces of
crossing cubes are at least 1/64 apart, contact faces inside a moving part are left out by Door.auto_hide(), and
export() refuses a model in which tools/zfight.py would still find a pair (that pass would push faces by 0.012).

THE PROJECTION. The front picture (FRONT, 32 px per block) covers the whole opening x in [-0.5, 0.5], y in [0, 2] seen
from the front; every face of a cube that looks to +z shows the part of the picture in front of it, so a band of iron
painted on the picture shows on the raised cube of the band, a rivet painted on it shows on the band, etc. The back
picture is painted in model coordinates too (B mirrors x internally: what is painted at x = 0.4 shows on the back of
the cube at x = 0.4, i.e. on the LEFT when seen from behind). Side faces (+-x, +-y) use material regions (32 x 32
tiles: "wood_side", "iron_side", ...) declared with d.material(name, painter).

Repere (contract of the doors): blocks, origin = middle of the bottom of the opening and of the thickness, +x = right
seen from the front, +y up, +z = the front face. Everything inside x [-0.5, 0.5], y [0, 2], z [-0.5, 0.5]. The leaf is
3/16 - 4/16 thick centred on z = 0 (relief included, z in [-0.125, 0.125]); its pivot is on its hinge edge, z = 0.
Animated children: gear_a_<n> / gear_b_<n> (pivot = centre, turn round z), bolt_<n> (slides along x), piston_<n>
(slides along y). Cubes named glow* are drawn full bright.

Previews: d.preview(out_png, refs=[(ref_png, box), ...]) renders front / three-quarter / back / open (leaf at 90 degrees
backwards) / open from behind / edge views with Minecraft face shading next to the reference crops.
"""
import base64
import io
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

gg, gn = tl.gg, tl.gn
Bone, EYE, v3 = tl.Bone, tl.EYE, tl.v3
ASSETS, ROOT = tl.ASSETS, tl.ROOT
PPB = 32          # pixels per block of the pictures and the material tiles
W, H = 1.0, 2.0   # the opening of a small door
REF_DIR = "/tmp/claude-0/-home-user-medieval-ships/2a9b6be4-7c0a-5b40-ad8d-40cfe82b9e67/scratchpad/doors_ref"


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(int(round(a[k] + (b[k] - a[k]) * t)) for k in range(3))


def shade(c, k):
    return tuple(max(0, min(255, int(round(v * k)))) for v in c[:3])


# ---------------------------------------------------------------- painting (numpy RGBA, y down)
class Canvas:
    """Paints a sub-rectangle of the atlas. Coordinates: model blocks (x, y up) mapped to pixels by (X0, X1, Y0, Y1)
    at PPB px per block; mirror=True for the back picture (x grows to the left of the picture)."""

    def __init__(self, arr, u0, v0, w, h, X0=0.0, X1=None, Y0=0.0, Y1=None, mirror=False, seed=1):
        self.a, self.u0, self.v0, self.w, self.h = arr, u0, v0, w, h
        self.X0, self.Y0 = X0, Y0
        self.X1 = X0 + w / PPB if X1 is None else X1
        self.Y1 = Y0 + h / PPB if Y1 is None else Y1
        self.mirror = mirror
        self.rng = random.Random(seed)

    # model -> pixel index ranges
    def pu(self, x):
        return (self.X1 - x) * PPB if self.mirror else (x - self.X0) * PPB

    def pv(self, y):
        return (self.Y1 - y) * PPB

    def span(self, x0, x1, y0, y1):
        a, b = sorted((self.pu(x0), self.pu(x1)))
        c, d = sorted((self.pv(y0), self.pv(y1)))
        i0, i1 = int(round(a)), int(round(b))
        j0, j1 = int(round(c)), int(round(d))
        i0, i1 = max(0, i0), min(self.w, i1)
        j0, j1 = max(0, j0), min(self.h, j1)
        return i0, i1, j0, j1

    def put(self, i, j, c, a=255):
        """Pixel (i, j) of the picture (pixel coordinates, y down)."""
        if 0 <= i < self.w and 0 <= j < self.h:
            self.a[self.v0 + j, self.u0 + i, :3] = c[:3]
            self.a[self.v0 + j, self.u0 + i, 3] = a

    def get(self, i, j):
        return tuple(int(v) for v in self.a[self.v0 + j, self.u0 + i, :3])

    def pix(self, x, y):
        """Pixel indices of the model point (x, y)."""
        return int(math.floor(self.pu(x) - (1e-6 if self.mirror else 0))), int(math.floor(self.pv(y)))

    def fill(self, x0, x1, y0, y1, c, noise=0):
        i0, i1, j0, j1 = self.span(x0, x1, y0, y1)
        for j in range(j0, j1):
            for i in range(i0, i1):
                k = 1 + (self.rng.random() - 0.5) * noise / 50.0 if noise else 1
                self.put(i, j, shade(c, k))

    def fill_px(self, i0, i1, j0, j1, c, noise=0, a=255):
        for j in range(max(0, j0), min(self.h, j1)):
            for i in range(max(0, i0), min(self.w, i1)):
                k = 1 + (self.rng.random() - 0.5) * noise / 50.0 if noise else 1
                self.put(i, j, shade(c, k), a)

    def planks_v(self, x0, x1, y0, y1, n, base, dark, grain=0.10, knots=2, seam=None):
        """Vertical planks: n planks across, dark seams, grain streaks along y, a few knots."""
        i0, i1, j0, j1 = self.span(x0, x1, y0, y1)
        seam = seam or shade(dark, 0.85)
        wpx = (i1 - i0) / n
        for p in range(n):
            a, b = int(round(i0 + p * wpx)), int(round(i0 + (p + 1) * wpx))
            tint = 1 + (self.rng.random() - 0.5) * 0.16
            col = shade(base, tint)
            streak = [1 + (self.rng.random() - 0.5) * grain * 2 for _ in range(b - a)]
            for j in range(j0, j1):
                for i in range(a, b):
                    k = streak[i - a] * (1 + (self.rng.random() - 0.5) * 0.06)
                    if self.rng.random() < 0.035:
                        k *= 0.82
                    c = shade(col, k)
                    if i == a:
                        c = seam
                    elif i == a + 1:
                        c = shade(col, 1.12)
                    elif i == b - 1:
                        c = shade(col, 0.86)
                    self.put(i, j, c)
            for _ in range(knots if b - a > 4 else 0):
                if self.rng.random() < 0.6:
                    ki = self.rng.randint(a + 2, max(a + 2, b - 3))
                    kj = self.rng.randint(j0 + 3, max(j0 + 3, j1 - 4))
                    self.put(ki, kj, shade(dark, 1.05))
                    self.put(ki, kj + 1, shade(col, 0.75))
                    self.put(ki + 1, kj, shade(col, 0.78))

    def metal(self, x0, x1, y0, y1, base, noise=10, bevel=True, rust=None, rust_p=0.0):
        """Hammered metal plate with a light top / left edge and a dark bottom / right edge."""
        i0, i1, j0, j1 = self.span(x0, x1, y0, y1)
        for j in range(j0, j1):
            for i in range(i0, i1):
                k = 1 + (self.rng.random() - 0.5) * noise / 50.0
                c = shade(base, k)
                if rust and self.rng.random() < rust_p:
                    c = shade(rust, 0.9 + self.rng.random() * 0.25)
                self.put(i, j, c)
        if bevel and i1 - i0 >= 2 and j1 - j0 >= 2:
            for i in range(i0, i1):
                self.put(i, j0, shade(self.get(i, j0), 1.28))
                self.put(i, j1 - 1, shade(self.get(i, j1 - 1), 0.62))
            for j in range(j0 + 1, j1 - 1):
                self.put(i0, j, shade(self.get(i0, j), 1.15))
                self.put(i1 - 1, j, shade(self.get(i1 - 1, j), 0.72))

    def rivet(self, x, y, light=(205, 200, 196), dark=(40, 36, 38), big=False):
        i, j = self.pix(x, y)
        if big:
            self.put(i, j, light)
            self.put(i + 1, j, shade(light, 0.8))
            self.put(i, j + 1, shade(light, 0.75))
            self.put(i + 1, j + 1, dark)
        else:
            self.put(i, j, light)
            self.put(i + 1, j + 1, dark)
            self.put(i + 1, j, shade(light, 0.6))

    def rivets_h(self, x0, x1, y, n, **kw):
        for k in range(n):
            self.rivet(x0 + (x1 - x0) * (k + 0.5) / n, y, **kw)

    def rivets_v(self, x, y0, y1, n, **kw):
        for k in range(n):
            self.rivet(x, y0 + (y1 - y0) * (k + 0.5) / n, **kw)

    def glow(self, x0, x1, y0, y1, hot=(255, 236, 150), warm=(246, 160, 44), edge=(170, 84, 20)):
        """Lit glass: hot centre, warm body, darker rim (pixel steps, no smooth gradient)."""
        i0, i1, j0, j1 = self.span(x0, x1, y0, y1)
        cx, cy = (i0 + i1 - 1) / 2, (j0 + j1 - 1) / 2
        rx, ry = max(1, (i1 - i0) / 2), max(1, (j1 - j0) / 2)
        for j in range(j0, j1):
            for i in range(i0, i1):
                d = max(abs(i - cx) / rx, abs(j - cy) / ry)
                c = hot if d < 0.45 else warm if d < 0.85 else edge
                self.put(i, j, c)

    def disc(self, cx, cy, r, c, noise=0, ring=None):
        """Filled pixel disc (model centre / radius); ring=(width_px, colour) paints its rim."""
        i0, i1, j0, j1 = self.span(cx - r, cx + r, cy - r, cy + r)
        ci, cj = self.pu(cx), self.pv(cy)
        rp = r * PPB
        for j in range(j0, j1):
            for i in range(i0, i1):
                d = math.hypot(i + 0.5 - ci, j + 0.5 - cj)
                if d <= rp:
                    col = c
                    if ring and d > rp - ring[0]:
                        col = ring[1]
                    k = 1 + (self.rng.random() - 0.5) * noise / 50.0 if noise else 1
                    self.put(i, j, shade(col, k))


# ---------------------------------------------------------------- atlas
class _Packer:
    def __init__(self, size):
        self.size, self.x, self.y, self.row = size, 0, 0, 0

    def alloc(self, w, h):
        if self.x + w > self.size:
            self.x, self.y, self.row = 0, self.y + self.row, 0
        if self.y + h > self.size:
            raise ValueError("door atlas full")
        r = (self.x, self.y, w, h)
        self.x += w
        self.row = max(self.row, h)
        return r


# ---------------------------------------------------------------- the door
G = 1 / 64        # gap between the leaf and the frame (and the minimal offset between two parallel faces)
LIP = 1 / 32      # how far the front stops of the frame overlap the leaf edges
HINGE_X = -13 / 32  # the pivot of leaf_l (DoorTypes: hingeX 0.40625, checked by a JUnit test): never change it


class Door:
    """A small door: own atlas, root bone + "frame" + "leaf_l".

    The frame is REBATED for a leaf that opens backwards (-z, the default): front stops (z in [zl, zf]) overlap the
    leaf edges by LIP, so no slit is seen through the 1/64 gaps round the leaf; behind the hinge the jamb stops at
    z = G, so the leaf turned by 90 degrees (x in [hinge - cz, hinge + cz], z in [-0.81, 0]) touches nothing. The leaf
    core is z in [-cz, cz]; relief on it sits on its faces (the contact face is left out by auto_hide)."""

    def __init__(self, name, size=256, sill=2 / 32, lintel=3 / 32, cz=2 / 32, zf=9 / 32, zb=-9 / 32, seed=7):
        tl.setup(name)
        self.name, self.size = name, size
        self.arr = np.zeros((size, size, 4), np.uint8)
        self.pk = _Packer(size)
        self.regions = {}
        self.sheets = {}
        self.seed = seed
        self.F = self.sheet("front", -W / 2, W / 2, 0.0, H, mirror=False)    # leaf, seen from the front
        self.B = self.sheet("back", -W / 2, W / 2, 0.0, H, mirror=True)      # leaf, seen from the back
        self.FF = self.sheet("ffront", -W / 2, W / 2, 0.0, H, mirror=False)  # frame, front
        self.FB = self.sheet("fback", -W / 2, W / 2, 0.0, H, mirror=True)    # frame, back
        self.root = Bone(name)
        self.frame = Bone("frame", parent=self.root)
        self.fw, self.sill, self.lintel = W / 2 + HINGE_X, sill, lintel
        self.lx0, self.lx1 = HINGE_X, -HINGE_X
        self.ly0, self.ly1 = sill, H - lintel
        self.cz, self.zf, self.zb = cz, zf, zb
        self.zl = cz + G                      # back of the front stops
        # the part of the leaf front left visible by the stops (front relief must stay inside it, 1/64 off)
        self.vx0, self.vx1 = self.lx0 + LIP, self.lx1 - LIP
        self.vy0, self.vy1 = self.ly0 + LIP, self.ly1 - LIP
        self.leaf = Bone("leaf_l", origin=(HINGE_X, 0.0, 0.0), parent=self.root)
        self._detail = {}
        self.moving = {}                      # bone name -> kind, for the audit

    def detail(self, parent):
        if parent.name not in self._detail:
            self._detail[parent.name] = Bone("detail", origin=tuple(parent.origin), parent=parent)
        return self._detail[parent.name]

    def part(self, name, origin, parent):
        """An animated child bone (gear_a_<n>, gear_b_<n>, bolt_<n>, piston_<n>, handle_<n>)."""
        b = Bone(name, origin=origin, parent=parent)
        self.moving[name] = b
        return b

    def region(self, name, w, h):
        r = self.pk.alloc(w, h)
        self.regions[name] = r
        return r

    def sheet(self, name, X0, X1, Y0, Y1, mirror=False):
        w, h = int(round((X1 - X0) * PPB)), int(round((Y1 - Y0) * PPB))
        u, v, _, _ = self.region(name, w, h)
        c = Canvas(self.arr, u, v, w, h, X0, X1, Y0, Y1, mirror, seed=self.seed + len(self.regions) * 31)
        self.sheets[name] = (c, X0, X1, Y0, Y1, mirror)
        return c

    def material(self, name, painter, w=32, h=64):
        """A tiled material for side faces: painter(Canvas) paints a w x h tile (model coords x [0, w/32], y [0, h/32])."""
        u, v, _, _ = self.region(name, w, h)
        c = Canvas(self.arr, u, v, w, h, seed=self.seed + len(self.regions) * 17)
        painter(c)
        return c

    # ------------------------------------------------------------ cubes
    def _sub_sheet(self, sheet, x0, x1, y0, y1):
        c, X0, X1, Y0, Y1, mirror = self.sheets[sheet]
        if mirror:
            su0, su1 = (X1 - x1) / (X1 - X0), (X1 - x0) / (X1 - X0)
        else:
            su0, su1 = (x0 - X0) / (X1 - X0), (x1 - X0) / (X1 - X0)
        sv0, sv1 = (Y1 - y1) / (Y1 - Y0), (Y1 - y0) / (Y1 - Y0)
        return [su0, sv0, su1, sv1]

    def _sub_tile(self, region, a0, a1, b0, b1):
        """World-aligned sub-rectangle of a tile for a face spanning [a0, a1] x [b0, b1] (blocks) along its u / v axes,
        so that neighbouring faces continue each other; faces larger than the tile are stretched."""
        _, _, rw, rh = self.regions[region]
        fu, fv = min(1.0, (a1 - a0) * PPB / rw), min(1.0, (b1 - b0) * PPB / rh)
        ou = ((a0 * PPB) % rw) / rw
        ov = ((-b1 * PPB) % rh) / rh
        # whole texel offsets, never past the end of the tile (a face may span a fraction of a texel)
        ou = min(round(ou * rw), math.floor((1.0 - fu) * rw + 1e-9)) / rw
        ov = min(round(ov * rh), math.floor((1.0 - fv) * rh + 1e-9)) / rh
        return [ou, ov, ou + fu, ov + fv]

    def box(self, bone, name, x0, x1, y0, y1, z0, z1, side="iron_side", front="front", back="back", top=None,
            bottom=None, sides=None, hide=()):
        """Axis-aligned cube (model coordinates, closed pose). front / back: a sheet name (projected) or a material
        (tiled) for the +z / -z faces; side: material of the other faces (top / bottom / sides override it);
        hide: faces left out among '+x','-x','+y','-y','+z','-z'."""
        x0, x1 = sorted((x0, x1))
        y0, y1 = sorted((y0, y1))
        z0, z1 = sorted((z0, z1))
        assert x1 - x0 > 1e-6 and y1 - y0 > 1e-6 and z1 - z0 > 1e-6, name
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        spec = {"+3": front, "-3": back, "+2": top or side, "-2": bottom or side,
                "+1": sides or side, "-1": sides or side}
        names = {"+1": "+x", "-1": "-x", "+2": "+y", "-2": "-y", "+3": "+z", "-3": "-z"}
        regions = {k: (None if names[k] in hide or v is None else v) for k, v in spec.items()}
        c = gg.add_cube(bone, name, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), EYE, (sx, sy, sz), regions)
        c.mbox = (x0, x1, y0, y1, z0, z1)
        for sem, bb in gg.SEMANTIC_FACE.items():
            f = c.faces[bb]
            if f is None:
                continue
            reg = f["region"]
            if reg in self.sheets:
                f["sub"] = self._sub_sheet(reg, x0, x1, y0, y1)
            else:
                a0, a1, b0, b1 = {"+1": (z0, z1, y0, y1), "-1": (z0, z1, y0, y1), "+2": (x0, x1, z0, z1),
                                  "-2": (x0, x1, z0, z1), "+3": (x0, x1, y0, y1), "-3": (x0, x1, y0, y1)}[sem]
                f["sub"] = self._sub_tile(reg, a0, a1, b0, b1)
        return c

    def relief(self, bone, name, x0, x1, y0, y1, zbase, h, side, face=None, hide=()):
        """A raised piece sitting on a face at z = zbase: h > 0 grows to the front (its +z face shows `face`, default
        the front picture), h < 0 to the back (the back picture). The contact face is left out."""
        if h > 0:
            return self.box(bone, name, x0, x1, y0, y1, zbase, zbase + h, side=side, front=face or "front",
                            back=None, hide=hide)
        return self.box(bone, name, x0, x1, y0, y1, zbase + h, zbase, side=side, front=None, back=face or "back",
                        hide=hide)

    # ------------------------------------------------------------ the frame and the leaf core
    def build_frame(self, side, inner=None, top=None):
        """The rebated frame (see the class doc) as non-overlapping cells: x / y / z grids round the leaf with its gaps
        and stops; a cell face is drawn only where it borders an empty cell, so no face is ever coplanar with another
        one. side: material of the reveals, inner: of the faces that look into the opening (default side)."""
        p, q = self.lx0, self.lx1
        xs = [-0.5, p - G, p + LIP, q - LIP, q + G, 0.5]
        ys = [0.0, self.ly0 - G, self.ly0 + LIP, self.ly1 - LIP, self.ly1 + G, H]
        zs = [self.zb, G, self.zl, self.zf]

        def solid(i, j, k):
            if not (0 <= i < 5 and 0 <= j < 5 and 0 <= k < 3):
                return False
            if k == 2:                       # the front stops: everything but the visible middle of the leaf
                return not (i == 2 and j == 2)
            outer = i in (0, 4) or j in (0, 4)
            if k == 1:                       # z [G, zl]: round the leaf and its gaps
                return outer
            return outer and not (i == 0 and j in (1, 2, 3))   # z [zb, G]: rebate behind the hinge
        # vertical runs of cells with the same neighbourhood are merged into one cube
        n = 0
        for k in range(3):
            for i in range(5):
                j = 0
                while j < 5:
                    if not solid(i, j, k):
                        j += 1
                        continue
                    sig = lambda jj: (solid(i - 1, jj, k), solid(i + 1, jj, k), solid(i, jj, k - 1), solid(i, jj, k + 1))
                    j1 = j
                    while j1 + 1 < 5 and solid(i, j1 + 1, k) and sig(j1 + 1) == sig(j):
                        j1 += 1
                    nx, px_, nz, pz = sig(j)
                    hide = [h for h, s in (("-x", nx), ("+x", px_), ("-z", nz), ("+z", pz)) if s]
                    if solid(i, j - 1, k):
                        hide.append("-y")
                    if solid(i, j1 + 1, k):
                        hide.append("+y")
                    sd = side
                    if inner and i in (1, 2, 3) and j in (1, 2, 3):
                        sd = inner
                    self.box(self.frame, "frame_%d_%d_%d" % (k, i, j), xs[i], xs[i + 1], ys[j], ys[j1 + 1],
                             zs[k], zs[k + 1], side=sd, front="ffront", back="fback", top=top, hide=tuple(hide))
                    n += 1
                    j = j1 + 1
        return n

    def core(self, side, hole=None, top=None, bottom=None):
        """The leaf core z in [-cz, cz], whole or in four cubes round a rectangular hole (hx0, hx1, hy0, hy1)."""
        x0, x1, y0, y1, cz = self.lx0, self.lx1, self.ly0, self.ly1, self.cz
        kw = dict(side=side, top=top, bottom=bottom)
        if hole is None:
            self.box(self.leaf, "core", x0, x1, y0, y1, -cz, cz, **kw)
            return
        hx0, hx1, hy0, hy1 = hole
        self.box(self.leaf, "core_bottom", x0, x1, y0, hy0, -cz, cz, side=side, bottom=bottom)
        self.box(self.leaf, "core_top", x0, x1, hy1, y1, -cz, cz, side=side, top=top)
        self.box(self.leaf, "core_left", x0, hx0, hy0, hy1, -cz, cz, side=side, hide=("+y", "-y"))
        self.box(self.leaf, "core_right", hx1, x1, hy0, hy1, -cz, cz, side=side, hide=("+y", "-y"))

    # ------------------------------------------------------------ hidden faces
    def rigid_groups(self):
        """Cubes grouped by the moving part that carries them (detail bones belong to their parent's part)."""
        groups = {}

        def walk(b, key):
            if b.name in self.moving or b.name == "leaf_l":
                key = b.name
            groups.setdefault(key, []).extend(b.cubes)
            for ch in b.children:
                walk(ch, key)
        walk(self.root, "frame")
        return groups

    def auto_hide(self):
        """Leaves out every face that lies on a face of opposite direction of another cube of the same moving part and
        is contained in it (a contact face, never seen, and coplanar with its neighbour); returns the count."""
        n = 0
        axes = {"+1": (0, 1), "-1": (0, -1), "+2": (1, 1), "-2": (1, -1), "+3": (2, 1), "-3": (2, -1)}
        for cubes in self.rigid_groups().values():
            for a in cubes:
                for sem, (k, s) in axes.items():
                    bb = gg.SEMANTIC_FACE[sem]
                    if a.faces.get(bb) is None:
                        continue
                    A = a.mbox
                    plane = A[2 * k + (1 if s > 0 else 0)]
                    o = [j for j in range(3) if j != k]
                    for b in cubes:
                        if b is a:
                            continue
                        Bx = b.mbox
                        bplane = Bx[2 * k + (0 if s > 0 else 1)]  # b's face looking the other way
                        if abs(bplane - plane) > 1e-6:
                            continue
                        if all(Bx[2 * j] <= A[2 * j] + 1e-6 and A[2 * j + 1] <= Bx[2 * j + 1] + 1e-6 for j in o):
                            a.faces[bb] = None
                            n += 1
                            break
        return n

    # ------------------------------------------------------------ export
    def texture_path(self):
        return os.path.join(ASSETS, "textures/entity/%s.png" % self.name)

    def export(self, icon=None):
        hidden = self.auto_hide()
        import zfight  # the shared pass would push faces by 0.012: the doors are built so that it finds nothing
        pairs, flat = zfight.find(self.root)
        if pairs or flat:
            for f, g in pairs[:20]:
                print("  zfight (shared pass) %s %s <-> %s %s" % (f["cube"].name, f["sem"], g["cube"].name, g["sem"]))
            raise SystemExit("%s: %d coplanar pairs for tools/zfight.py, fix the model" % (self.name, len(pairs)))
        tex = self.texture_path()
        os.makedirs(os.path.dirname(tex), exist_ok=True)
        Image.fromarray(self.arr, "RGBA").save(tex)
        with open(tex, "rb") as f:
            png = f.read()
        gn.REGIONS = {k: (0,) + r for k, r in self.regions.items()}
        gn.SIZE = self.size
        gg.REGIONS = dict(self.regions)
        gg.SIZE = self.size
        textures = [gn.texture_entry(self.name + ".png", self.size, png, "entity", self.name + ".png")]
        textures[0]["id"] = "0"
        outs = [os.path.join(ROOT, "blockbench/%s.bbmodel" % self.name),
                os.path.join(ASSETS, "models/entity/%s.bbmodel" % self.name)]
        model = gn.export(self.root, [], textures, outs, name=self.name, visible_box=(2, 3, 0))
        self.model = model
        ip = os.path.join(ASSETS, "textures/item/%s.png" % self.name)
        (icon or self.default_icon)(ip)
        if not self.check_bounds(model):
            raise SystemExit("%s: out of the opening" % self.name)
        nf = sum(1 for e in model["elements"] for f in e["faces"].values() if f.get("texture") is not None)
        print("%s: %d cubes, %d faces (%d contact faces left out), texture %dx%d" % (
            self.name, len(model["elements"]), nf, hidden, self.size, self.size))
        return model

    def default_icon(self, path):
        """16x16 icon: the model seen from the front (gears, glow included) reduced to 9 x 16, contrast raised, a dark
        outline, centred."""
        quads = pv.build_mesh(json.loads(json.dumps(self.model)), {})
        tex = [self.arr.astype(float)]
        im = render(quads, tex, W=90, H=160, eye=(0, 1.0, 30), target=(0, 1.0, 0), ortho=1.0, bg=(255, 0, 255))
        a = np.array(im).astype(float)
        bgm = (a[..., 0] > 250) & (a[..., 1] < 5) & (a[..., 2] > 250)
        rgba = np.dstack([a, np.where(bgm, 0, 255)]).astype(np.uint8)
        small = np.array(Image.fromarray(rgba, "RGBA").resize((9, 16), Image.BOX)).astype(float)
        small[..., :3] = np.clip((small[..., :3] - 110) * 1.3 + 118, 0, 255)
        small[..., 3] = np.where(small[..., 3] > 100, 255, 0)
        out = np.zeros((16, 16, 4), np.uint8)
        out[:, 4:13] = small.astype(np.uint8)
        for j in range(16):
            for i in range(4, 13):
                if out[j, i, 3] and (i in (4, 12) or j in (0, 15)):
                    out[j, i, :3] = (out[j, i, :3] * 0.55).astype(np.uint8)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        Image.fromarray(out, "RGBA").save(path)

    def check_bounds(self, model):
        lo, hi = np.full(3, 1e9), np.full(3, -1e9)
        for e in model["elements"]:
            f, t = np.array(e["from"]), np.array(e["to"])
            for p in (f, t):
                q = np.array([-p[0] / 16, p[1] / 16, -p[2] / 16])
                lo, hi = np.minimum(lo, q), np.maximum(hi, q)
        e = 1e-6
        ok = lo[0] >= -0.5 - e and hi[0] <= 0.5 + e and lo[1] >= -e and hi[1] <= 2 + e and lo[2] >= -0.5 - e and hi[2] <= 0.5 + e
        print("bounds x [%.4f, %.4f] y [%.4f, %.4f] z [%.4f, %.4f] %s" % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2],
                                                                         "OK" if ok else "OUT OF THE OPENING"))
        return ok

    # ------------------------------------------------------------ previews
    def preview(self, out, refs=(), open_deg=90.0):
        model = json.loads(json.dumps(self.model))
        tex = [np.array(Image.fromarray(self.arr, "RGBA")).astype(float)]
        closed = pv.build_mesh(model, {})
        _set_rot(model["outliner"], "leaf_l", [0, open_deg, 0])
        opened = pv.build_mesh(model, {})
        bg = (44, 42, 46)
        views = [
            ("face", closed, dict(W=260, H=520, eye=(0, 1.0, 30), target=(0, 1.0, 0), ortho=1.25)),
            ("3/4", closed, dict(W=300, H=520, eye=(-2.6, 2.1, 3.4), target=(0, 1.0, 0), fov=40)),
            ("dos", closed, dict(W=260, H=520, eye=(0, 1.0, -30), target=(0, 1.0, 0), ortho=1.25)),
            ("ouverte 90 (arriere)", opened, dict(W=300, H=520, eye=(2.4, 2.0, 3.6), target=(0, 1.0, -0.2), fov=40)),
            ("ouverte, de dos", opened, dict(W=300, H=520, eye=(-1.8, 3.0, -2.8), target=(0, 0.9, -0.3), fov=40)),
            ("chant", closed, dict(W=200, H=520, eye=(3.4, 1.6, 1.2), target=(0, 1.0, 0), fov=40)),
        ]
        ims = []
        for title, quads, kw in views:
            im = render(quads, tex, bg=bg, **kw)
            ImageDraw.Draw(im).text((6, 4), title, fill=(235, 225, 200))
            ims.append(im)
        for path, box in refs:
            im = Image.open(path).convert("RGB").crop(box)
            s = 500 / im.size[1]
            im = im.resize((max(1, int(im.size[0] * s)), 500), Image.NEAREST)
            canvas = Image.new("RGB", (im.size[0], 520), bg)
            canvas.paste(im, (0, 10))
            ImageDraw.Draw(canvas).text((6, 4), "ref " + os.path.basename(path), fill=(235, 225, 200))
            ims.append(canvas)
        Wt = sum(i.size[0] for i in ims) + 6 * (len(ims) - 1)
        sheet = Image.new("RGB", (Wt, 520), (20, 20, 22))
        x = 0
        for i in ims:
            sheet.paste(i, (x, 0))
            x += i.size[0] + 6
        os.makedirs(os.path.dirname(out), exist_ok=True)
        sheet.save(out)
        print("wrote", out)
        return sheet


def _set_rot(groups, name, rot):
    for g in groups:
        if isinstance(g, dict):
            if g["name"] == name:
                g["rotation"] = rot
            _set_rot(g["children"], name, rot)


def render(quads, texs, W, H, eye, target, fov=None, ortho=None, bg=(28, 33, 48), cov=False):
    """tools/preview.py's rasteriser with Minecraft face shading (top 1.0, z sides 0.8, x sides 0.6, bottom 0.5);
    cov=True also returns the coverage mask (pixels where a face was drawn)."""
    eye, target = np.array(eye, float), np.array(target, float)
    fwd = target - eye
    fwd /= np.linalg.norm(fwd)
    up = np.array([0, 1, 0.0]) if abs(fwd[1]) < 0.99 else np.array([0, 0, 1.0])
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
            s = H / (2 * ortho)
            return np.array([W / 2 + x * s, H / 2 - y * s, z])
        f = (H / 2) / math.tan(math.radians(fov) / 2)
        return np.array([W / 2 + x * f / z, H / 2 - y * f / z, z])

    for corners, uvs, glow, ti in quads:
        tex = texs[ti if ti < len(texs) else 0]
        tw, th = tex.shape[1], tex.shape[0]
        P = [project(c) for c in corners]
        n = np.cross(corners[1] - corners[0], corners[3] - corners[0])
        nn = np.linalg.norm(n)
        if nn < 1e-9:
            continue
        n /= nn
        if glow:
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
            mask &= z < sub
            if not mask.any():
                continue
            sub[mask] = z[mask]
            region = img[ymin:ymax + 1, xmin:xmax + 1]
            region[mask] = col[..., :3][mask] * sh
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    return (im, np.isfinite(zbuf)) if cov else im


# ---------------------------------------------------------------- shared pieces
def tile_wood(base, dark):
    def p(c):
        c.planks_v(0, c.X1, 0, c.Y1, 4, base, dark, knots=1)
    return p


def tile_metal(base, rust=None, p=0.0):
    def f(c):
        c.metal(0, c.X1, 0, c.Y1, base, noise=12, bevel=False, rust=rust, rust_p=p)
    return f


def tile_flat(col, noise=8):
    def f(c):
        c.fill(0, c.X1, 0, c.Y1, col, noise=noise)
    return f


def ring_handle(d, parent, name, cx, cy, zbase, metal_side, s=1, big=True, colours=None):
    """Iron ring handle on a face at z = zbase (s = 1 front, -1 back), in its own bone `name` (pivot = the boss, it
    turns about z when the door is unlocked): a square plate, a boss, a staple and an octagonal ring (9 px, or 7 px
    when big=False) hanging 1/64 in front of the plate. The four corner blocks of the ring stand 1/64 proud of its bars
    so that no two faces are ever coplanar. The cubes show their own little picture (sheet `name`)."""
    P = 1 / 32
    light, mid, dark = colours or ((206, 200, 196), (124, 114, 116), (46, 40, 42))
    pr = (2.5 if big else 2.0) * P
    ro, ri = (4.5, 2.5) if big else (4.0, 2.5)          # ring outer / inner half size (px)
    ry = cy - (7.0 if big else 6.5) * P                 # ring centre
    X0, X1, Y0, Y1 = cx - 5 * P, cx + 5 * P, ry - 5 * P, cy + 3 * P
    sh = d.sheet(name, X0, X1, Y0, Y1, mirror=s < 0)
    sh.fill(X0, X1, Y0, Y1, mid)
    sh.metal(cx - pr, cx + pr, cy - pr, cy + pr, mid, noise=8)
    sh.metal(cx - P, cx + P, cy - P, cy + P, light, noise=4)
    sh.metal(cx - P, cx + P, ry + (ro - 1) * P, cy - P, shade(mid, 0.9), noise=4, bevel=False)
    sh.metal(cx - ro * P, cx + ro * P, ry + ri * P, ry + ro * P, light, noise=6, bevel=False)          # top bar
    sh.metal(cx - ro * P, cx + ro * P, ry - ro * P, ry - ri * P, shade(mid, 0.75), noise=6, bevel=False)  # bottom
    sh.metal(cx - ro * P, cx - ri * P, ry - ri * P, ry + ri * P, shade(light, 0.9), noise=6, bevel=False)
    sh.metal(cx + ri * P, cx + ro * P, ry - ri * P, ry + ri * P, shade(mid, 0.85), noise=6, bevel=False)
    b = d.part(name, (cx, cy, zbase), parent)
    face = dict(face=name)
    d.relief(b, name + "_plate", cx - pr, cx + pr, cy - pr, cy + pr, zbase, s * P, metal_side, **face)
    d.relief(b, name + "_boss", cx - P, cx + P, cy - P, cy + P, zbase + s * P, s * (P + 3 * G), metal_side, **face)
    za0 = zbase + s * (P + G)
    fr, bk = (name, None) if s > 0 else (None, name)

    def rb(nm, a0, a1, b0, b1, dz=0.0):
        z0, z1 = sorted((za0 + s * dz, za0 + s * (dz + P)))
        d.box(b, name + nm, cx + a0 * P, cx + a1 * P, ry + b0 * P, ry + b1 * P, z0, z1, side=metal_side, front=fr,
              back=bk)
    # staple from the boss down to the ring (front of the plate, 1/64 off it)
    d.box(b, name + "_staple", cx - 0.5 * P, cx + 0.5 * P, ry + (ro - 0.5) * P, cy - 0.5 * P,
          *sorted((za0 + s * G, za0 + s * (P + G))), side=metal_side, front=fr, back=bk)
    c = ri + 0.5
    rb("_ring_t", -c + 0.5, c - 0.5, ri, ro)
    rb("_ring_d", -c + 0.5, c - 0.5, -ro, -ri)
    rb("_ring_l", -ro, -ri, -c + 0.5, c - 0.5)
    rb("_ring_r", ri, ro, -c + 0.5, c - 0.5)
    for k, (sx, sy) in enumerate(((-1, 1), (1, 1), (-1, -1), (1, -1))):
        a0, a1 = sorted((sx * (ri - 1), sx * (ro - 1)))
        b0, b1 = sorted((sy * (ri - 1), sy * (ro - 1)))
        rb("_ring_c%d" % k, a0, a1, b0, b1, dz=G)
    return b


def frame_picture(C, base, edge_dark, rivet_l, rivet_d, lx0, lx1, ly0, ly1, noise=12, rivets=9, big=True):
    """Paints a frame picture (front or back): metal everywhere, a dark line along the edge of the opening (the front
    stops end LIP inside the leaf), riveted jambs and lintel."""
    C.metal(-0.5, 0.5, 0, 2, base, noise=noise, bevel=False)
    e0, e1, f0, f1 = lx0 + LIP, lx1 - LIP, ly0 + LIP, ly1 - LIP
    C.fill(e0 - 1 / 32, e0, f0, f1, shade(base, 1.18))
    C.fill(e1, e1 + 1 / 32, f0, f1, shade(base, 0.7))
    C.fill(e0, e1, f1, f1 + 1 / 32, shade(base, 0.7))
    C.fill(e0, e1, f0 - 1 / 32, f0, shade(base, 1.18))
    C.fill(-0.5, 0.5, 2 - 1 / 32, 2, shade(base, 1.25))
    C.fill(-0.5, -0.5 + 1 / 32, 0, 2, shade(base, 1.12))
    C.fill(0.5 - 1 / 32, 0.5, 0, 2, shade(base, 0.72))
    C.fill(-0.5, 0.5, 0, 1 / 32, shade(base, 0.6))
    xl, xr = (-0.5 + e0) / 2, (e1 + 0.5) / 2
    for xr_ in (xl, xr):
        C.rivets_v(xr_ - 1 / 64, 0.06, 1.9, rivets, light=rivet_l, dark=rivet_d, big=big)
    C.rivets_h(xl + 0.12, xr - 0.08, (f1 + 2) / 2, 4, light=rivet_l, dark=rivet_d, big=big)


def paint_gear(c, teeth, base, light, dark, hole=(0, 0, 0), spokes=4, tooth_depth=2.0, rim_w=2.0, hub=2.0):
    """Cut-out pixel gear on a sprite canvas (the whole canvas = the gear's bounding square): teeth (tooth_depth px),
    a rim (rim_w px), spokes, a hub with a dark axle hole; 1 px dark outline, light upper-left."""
    n = c.w
    R = n / 2.0
    mask = [[None] * n for _ in range(n)]
    for j in range(n):
        for i in range(n):
            dx, dy = i + 0.5 - R, j + 0.5 - R
            d = math.hypot(dx, dy)
            th = math.atan2(dy, dx)
            col = None
            if d <= R - tooth_depth:
                if d > R - tooth_depth - rim_w:
                    col = base
                elif d <= hub:
                    col = light if d > hub * 0.45 else hole
                else:
                    for k in range(spokes):
                        a = k * 2 * math.pi / spokes
                        perp = abs(-math.sin(a) * dx + math.cos(a) * dy)
                        along = math.cos(a) * dx + math.sin(a) * dy
                        if perp < 1.0 and along > 0:
                            col = base
            elif d <= R - 0.1 and math.cos(teeth * th) > 0.15:
                col = base
            if col is not None and col is not hole and col is not light:
                col = shade(col, 1.08 if dx + dy < -2 else 0.94 if dx + dy > 2 else 1.0)
            mask[j][i] = col
    for j in range(n):
        for i in range(n):
            col = mask[j][i]
            if col is None:
                continue
            edge = any(not (0 <= i + di < n and 0 <= j + dj < n) or mask[j + dj][i + di] is None
                       for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            dd = math.hypot(i + 0.5 - R, j + 0.5 - R)
            if edge and col is not hole:
                if dd > R - tooth_depth - 0.6:
                    col = shade(col, 0.62) if (i + 0.5 - R) + (j + 0.5 - R) > -2 else shade(col, 1.15)
                else:
                    col = shade(col, 0.8)
            c.put(i, j, col)


def paint_gear_face(c, cx, cy, R, base, light, dark, recess, spokes=4):
    """Paints the face of a cube gear (body radius R px, centre cx, cy in model blocks) on its sheet: teeth and rim in
    the metal, a lit upper-left edge, spokes, dark recesses between them, a hub with a dark axle. Opaque everywhere."""
    P = 1 / 32
    c.fill(c.X0, c.X1, c.Y0, c.Y1, base, noise=6)
    ci, cj = c.pu(cx), c.pv(cy)
    for j in range(c.h):
        for i in range(c.w):
            dx, dy = i + 0.5 - ci, j + 0.5 - cj
            r = math.hypot(dx, dy)
            col = None
            if r > R + 0.2:                                   # teeth: lit / shaded by side
                col = shade(base, 1.15 if dx + dy < 0 else 0.8)
            elif r > R - 1.4:                                 # rim
                col = shade(light, 1.0 if dx + dy < -1 else 0.86) if r > R - 0.7 else base
            elif r <= 1.0:
                col = dark                                    # axle
            elif r <= 2.2:
                col = light                                   # hub
            else:
                a = math.atan2(dy, dx)
                on = any(abs(math.sin(a - k * math.pi / spokes * 2 + math.pi / 4 * 0)) * r < 0.85 and
                         math.cos(a - k * 2 * math.pi / spokes) > 0 for k in range(spokes))
                col = shade(base, 1.08 if dx + dy < 0 else 0.92) if on else recess
            c.put(i, j, col)


def cube_gear(d, parent, name, cx, cy, R, zbase, side, base, light, dark, recess, depth=2 / 32, spokes=4,
              tooth_w=3.0, diag=3.0, cc=None):
    """An animated gear made of cubes (bone `name`, pivot = its centre, turns about z): a stepped disc of radius R px
    (centred strips: every contact face is covered by its neighbour), 8 teeth 1/64 thinner on each face than the disc
    (so that no face is coplanar with the disc), a hub. All opaque, its own picture (sheet `name`)."""
    P = 1 / 32
    span = R + 4
    sh = d.sheet(name, cx - span * P, cx + span * P, cy - span * P, cy + span * P)
    paint_gear_face(sh, cx, cy, R, base, light, dark, recess, spokes)
    b = d.part(name, (cx, cy, zbase), parent)
    # disc: strips 2 px high, centred, merged when equally wide
    rows = []
    k = -R
    while k < R:
        k1 = min(R, k + 2)
        mid = (k + k1) / 2
        hw = int(round(math.sqrt(max(0.0, R * R - mid * mid))))
        if rows and rows[-1][2] == hw:
            rows[-1] = (rows[-1][0], k1, hw)
        else:
            rows.append((k, k1, hw))
        k = k1
    for n, (y0, y1, hw) in enumerate(rows):
        d.relief(b, "%s_disc%d" % (name, n), cx - hw * P, cx + hw * P, cy + y0 * P, cy + y1 * P, zbase, depth, side,
                 face=name)
    za, zb_ = zbase + G, zbase + depth - G
    t, dd = tooth_w / 2, R + 2.0
    for n, (ax, ay) in enumerate(((1, 0), (0, 1), (-1, 0), (0, -1))):
        if ax:
            a0, a1 = sorted((ax * (R - 0.5), ax * dd))
            b0, b1 = -t, t
        else:
            a0, a1 = -t, t
            b0, b1 = sorted((ay * (R - 0.5), ay * dd))
        d.box(b, "%s_tooth%d" % (name, n), cx + a0 * P, cx + a1 * P, cy + b0 * P, cy + b1 * P, za, zb_, side=side,
              front=name, back=name)
    cc = cc if cc is not None else round((R + 0.6) / math.sqrt(2) * 2) / 2   # diagonal teeth centre (px)
    for n, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        a0, a1 = sorted((sx * (cc - diag / 2), sx * (cc + diag / 2)))
        b0, b1 = sorted((sy * (cc - diag / 2), sy * (cc + diag / 2)))
        d.box(b, "%s_tooth%d" % (name, n + 4), cx + a0 * P, cx + a1 * P, cy + b0 * P, cy + b1 * P, za, zb_, side=side,
              front=name, back=name)
    d.relief(b, name + "_hub", cx - 1.5 * P, cx + 1.5 * P, cy - 1.5 * P, cy + 1.5 * P, zbase + depth, P, side, face=name)
    return b
