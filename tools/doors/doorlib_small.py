"""Shared helpers of the three SMALL doors of 1.31.0 (2 blocks high x 1 wide, one leaf): porte_chene, porte_prison,
porte_vapeur. Written for tools/doors/generate_<id>.py; the medium / large doors have their own libraries.

How a small door is built (see generate_porte_chene.py for a complete example):

    import doorlib_small as ds
    d = ds.Door("porte_chene", size=256)          # own atlas, root bone + "frame" + "leaf_l" (hinge on the left)
    F, B = d.F, d.B                                # painters of the FRONT and BACK pictures (model coordinates)
    F.planks_v(x0, x1, y0, y1, n, base, dark)      # ... paint the whole door, seen from the front, like the reference
    d.box(d.leaf, "core", x0, x1, y0, y1, z0, z1, side="wood_side")   # cubes: +z faces show the front picture,
                                                    # -z faces the back picture (projected), the others a material
    d.export(icon=...)                             # bbmodel (models/entity + blockbench), texture, 16x16 icon

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

Previews: d.preview(out_png, refs=[(ref_png, box), ...]) renders front / three-quarter / open (leaf at 90 degrees) /
back views with Minecraft face shading (top 1.0, z sides 0.8, x sides 0.6, bottom 0.5) next to the reference crops.
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
class Door:
    def __init__(self, name, size=256, frame_w=3 / 32, sill=0.0, lintel=3 / 32, seed=7):
        tl.setup(name)
        self.name, self.size = name, size
        self.arr = np.zeros((size, size, 4), np.uint8)
        self.pk = _Packer(size)
        self.regions = {}
        self.sheets = {}
        self.seed = seed
        self.F = self.sheet("front", -W / 2, W / 2, 0.0, H, mirror=False)
        self.B = self.sheet("back", -W / 2, W / 2, 0.0, H, mirror=True)
        self.root = Bone(name)
        self.frame = Bone("frame", parent=self.root)
        self.fw, self.sill, self.lintel = frame_w, sill, lintel
        # the leaf fills the frame: x [-0.5 + fw, 0.5 - fw], y [sill, 2 - lintel]
        self.lx0, self.lx1 = -W / 2 + frame_w, W / 2 - frame_w
        self.ly0, self.ly1 = sill, H - lintel
        self.leaf = Bone("leaf_l", origin=(self.lx0, 0.0, 0.0), parent=self.root)
        self._detail = {}

    def detail(self, parent):
        if parent.name not in self._detail:
            self._detail[parent.name] = Bone("detail", origin=tuple(parent.origin), parent=parent)
        return self._detail[parent.name]

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

    def material(self, name, painter, w=32, h=32):
        """A tiled material for side faces: painter(Canvas) paints a w x h tile."""
        u, v, _, _ = self.region(name, w, h)
        c = Canvas(self.arr, u, v, w, h, seed=self.seed + len(self.regions) * 17)
        painter(c)
        return c

    def sprite(self, name, w, h, painter):
        """A free picture (gears...): painter(Canvas) with model coords x in [0, w/PPB], y in [0, h/PPB]."""
        u, v, _, _ = self.region(name, w, h)
        c = Canvas(self.arr, u, v, w, h, seed=self.seed + len(self.regions) * 13)
        painter(c)
        return c

    # ------------------------------------------------------------ cubes
    def _sub_sheet(self, sheet, x0, x1, y0, y1, back):
        c, X0, X1, Y0, Y1, mirror = self.sheets[sheet]
        if mirror:
            su0, su1 = (X1 - x1) / (X1 - X0), (X1 - x0) / (X1 - X0)
        else:
            su0, su1 = (x0 - X0) / (X1 - X0), (x1 - X0) / (X1 - X0)
        sv0, sv1 = (Y1 - y1) / (Y1 - Y0), (Y1 - y0) / (Y1 - Y0)
        return [su0, sv0, su1, sv1]

    def _sub_tile(self, region, du, dv, ou=0.0, ov=0.0):
        _, _, rw, rh = self.regions[region]
        fu = min(1.0, du * PPB / rw)
        fv = min(1.0, dv * PPB / rh)
        ou = min(ou, 1.0 - fu)
        ov = min(ov, 1.0 - fv)
        return [ou, ov, ou + fu, ov + fv]

    def box(self, bone, name, x0, x1, y0, y1, z0, z1, side="iron_side", front="front", back="back", top=None,
            bottom=None, sides=None, hide=()):
        """Axis-aligned cube (model coordinates, closed pose). front / back: a sheet name (projected) or a material
        (tiled) for the +z / -z faces; side: material of the other faces (top / bottom / sides override it);
        hide: faces left out among '+x','-x','+y','-y','+z','-z'."""
        x0, x1 = sorted((x0, x1))
        y0, y1 = sorted((y0, y1))
        z0, z1 = sorted((z0, z1))
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        spec = {"+3": front, "-3": back, "+2": top or side, "-2": bottom or side,
                "+1": sides or side, "-1": sides or side}
        names = {"+1": "+x", "-1": "-x", "+2": "+y", "-2": "-y", "+3": "+z", "-3": "-z"}
        regions = {k: (None if names[k] in hide or v is None else v) for k, v in spec.items()}
        c = gg.add_cube(bone, name, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), EYE, (sx, sy, sz), regions)
        h = zlib.crc32(name.encode()) % 997 / 997.0
        for sem, bb in gg.SEMANTIC_FACE.items():
            f = c.faces[bb]
            if f is None:
                continue
            reg = f["region"]
            if reg in self.sheets:
                f["sub"] = self._sub_sheet(reg, x0, x1, y0, y1, sem == "-3")
            else:
                du, dv = {"+1": (sz, sy), "-1": (sz, sy), "+2": (sx, sz), "-2": (sx, sz),
                          "+3": (sx, sy), "-3": (sx, sy)}[sem]
                f["sub"] = self._sub_tile(reg, du, dv, ou=h * 0.6, ov=(h * 7 % 1) * 0.6)
        return c

    def sprite_box(self, bone, name, cx, cy, r, z0, z1, sprite, side=None):
        """Square cube centred on (cx, cy), half size r, whose +z and -z faces show the whole sprite (cut-out);
        side faces left out unless side is given."""
        c = self.box(bone, name, cx - r, cx + r, cy - r, cy + r, z0, z1, side=side, front=sprite, back=sprite)
        for sem in ("+3", "-3"):
            f = c.faces[gg.SEMANTIC_FACE[sem]]
            f["sub"] = [0.0, 0.0, 1.0, 1.0] if sem == "+3" else [1.0, 0.0, 0.0, 1.0]
        return c

    # ------------------------------------------------------------ export
    def texture_path(self):
        return os.path.join(ASSETS, "textures/entity/%s.png" % self.name)

    def export(self, icon=None):
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
        if self.clamp(model):  # zfight pushes faces by 0.012: keep everything inside the opening
            for p in outs:
                with open(p, "w") as f:
                    gn.json_dump(model, f, compact="resources" in p)
        self.model = model
        ip = os.path.join(ASSETS, "textures/item/%s.png" % self.name)
        (icon or self.default_icon)(ip)
        self.check_bounds(model)
        print("%s: %d cubes, texture %dx%d" % (self.name, len(model["elements"]), self.size, self.size))
        self.model = model
        return model

    def clamp(self, model):
        """Clamps every (unrotated) element into x [-0.5, 0.5], y [0, 2], z [-0.5, 0.5] (bb pixels); returns the count."""
        lim = [(-8.0, 8.0), (0.0, 32.0), (-8.0, 8.0)]
        n = 0
        for e in model["elements"]:
            if e.get("rotation"):
                continue
            for ax in range(3):
                for key in ("from", "to"):
                    v = e[key][ax]
                    c = min(max(v, lim[ax][0]), lim[ax][1])
                    if abs(c - v) > 1e-6:
                        e[key][ax] = c
                        n += 1
        if n:
            print("clamped %d element faces back into the opening" % n)
        return n

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
        # dark outline on the outer pixels of the door
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
        ok = lo[0] >= -0.5 - 0.02 and hi[0] <= 0.5 + 0.02 and lo[1] >= -0.02 and hi[1] <= 2.02 and lo[2] >= -0.52 and hi[2] <= 0.52
        print("bounds x [%.3f, %.3f] y [%.3f, %.3f] z [%.3f, %.3f] %s" % (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2],
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
            ("ouverte 90", opened, dict(W=300, H=520, eye=(2.4, 2.0, 3.6), target=(0, 1.0, -0.2), fov=40)),
            ("arriere", closed, dict(W=260, H=520, eye=(0, 1.0, -30), target=(0, 1.0, 0), ortho=1.25)),
            ("ouverte dessus", opened, dict(W=300, H=520, eye=(-1.8, 3.4, -2.6), target=(0, 0.9, -0.3), fov=40)),
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


def render(quads, texs, W, H, eye, target, fov=None, ortho=None, bg=(28, 33, 48)):
    """tools/preview.py's rasteriser with Minecraft face shading (top 1.0, z sides 0.8, x sides 0.6, bottom 0.5)."""
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
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


# ---------------------------------------------------------------- shared pieces
def tile_wood(base, dark):
    def p(c):
        c.planks_v(0, 1, 0, 1, 4, base, dark, knots=1)
    return p


def tile_metal(base, rust=None, p=0.0):
    def f(c):
        c.metal(0, 1, 0, 1, base, noise=12, bevel=False, rust=rust, rust_p=p)
    return f


def tile_flat(col, noise=8):
    def f(c):
        c.fill(0, 1, 0, 1, col, noise=noise)
    return f


def ring_handle(d, bone, cx, cy, z, metal_side, plate=0.06, ring=0.075, th=1 / 32, back=False):
    """Iron ring handle: a square back plate + a pixel ring hanging under it (cubes)."""
    s = -1 if back else 1
    zb = z
    zf = z + s * th
    d.box(bone, "ring_plate" + ("_b" if back else ""), cx - plate / 2, cx + plate / 2, cy - plate / 2, cy + plate / 2,
          zb, zf, side=metal_side)
    zr0, zr1 = zf, zf + s * th
    r, t = ring / 2, 1 / 32
    d.box(bone, "ring_staple" + ("_b" if back else ""), cx - t, cx + t, cy - plate / 2 - t, cy + plate / 2 - t,
          zf, zf + s * th * 1.5, side=metal_side)
    top = cy - plate / 2 + t
    cyr = top - r
    nm = "ring" + ("_b" if back else "")
    d.box(bone, nm + "_t", cx - r + t, cx + r - t, top - t, top, zr0, zr1, side=metal_side)
    d.box(bone, nm + "_d", cx - r + t, cx + r - t, cyr - r, cyr - r + t, zr0, zr1, side=metal_side)
    d.box(bone, nm + "_l", cx - r, cx - r + t, cyr - r + t, top - t, zr0, zr1, side=metal_side)
    d.box(bone, nm + "_r", cx + r - t, cx + r, cyr - r + t, top - t, zr0, zr1, side=metal_side)
    return cyr


def paint_ring(canvas, cx, cy, plate, ring, light, mid, dark):
    """Paints the ring handle (plate + ring) on a picture at the same place as ring_handle()."""
    canvas.metal(cx - plate / 2, cx + plate / 2, cy - plate / 2, cy + plate / 2, mid, noise=8)
    canvas.rivet(cx - 1 / 64, cy + 1 / 64, light=light, dark=dark)
    r, t = ring / 2, 1 / 32
    top = cy - plate / 2 + t
    cyr = top - r
    canvas.metal(cx - r + t, cx + r - t, top - t, top, light, noise=4, bevel=False)
    canvas.metal(cx - r + t, cx + r - t, cyr - r, cyr - r + t, dark, noise=4, bevel=False)
    canvas.metal(cx - r, cx - r + t, cyr - r + t, top - t, mid, noise=4, bevel=False)
    canvas.metal(cx + r - t, cx + r, cyr - r + t, top - t, shade(mid, 0.8), noise=4, bevel=False)


def core_with_hole(d, bone, x0, x1, y0, y1, hx0, hx1, hy0, hy1, cz, side, **kw):
    """The leaf core (z in [-cz, cz]) in four cubes round a rectangular hole (judas, porthole)."""
    d.box(bone, "core_bottom", x0, x1, y0, hy0, -cz, cz, side=side, **kw)
    d.box(bone, "core_top", x0, x1, hy1, y1, -cz, cz, side=side, **kw)
    d.box(bone, "core_left", x0, hx0, hy0, hy1, -cz, cz, side=side, **kw)
    d.box(bone, "core_right", hx1, x1, hy0, hy1, -cz, cz, side=side, **kw)


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


def gear(d, parent, name, cx, cy, r, z0, sprite, side):
    """An animated gear (bone `name`, pivot at its centre): a thin cut-out sprite in front of a thick body cross."""
    b = Bone(name, origin=(cx, cy, z0), parent=parent)
    rr = r * 0.74
    t = r * 0.42
    d.box(b, name + "_body_h", cx - rr, cx + rr, cy - t, cy + t, z0, z0 + 1 / 32, side=side, hide=("+z", "-z"))
    d.box(b, name + "_body_v", cx - t, cx + t, cy - rr, cy + rr, z0, z0 + 1 / 32, side=side, hide=("+z", "-z"))
    d.sprite_box(b, name + "_teeth", cx, cy, r, z0 + 1 / 32, z0 + 1.6 / 32, sprite)
    return b
