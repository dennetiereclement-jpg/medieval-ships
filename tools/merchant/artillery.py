"""Helpers of the artillery props (1.16.0: the medieval cannon canon_medieval), one block each, drawn like the tents
from a .bbmodel (TentType JSON group "artillery", tab "Artillerie").

The cannon reuses the tents' chain (tools/tents/tentlib.py through tools/merchant/merchantlib.py: Bone, add_cube,
beam, collide, extent) and the carts' wheel and axle (tools/carts/cartlib.py: wheel, axle) with its own small atlas
(Atlas below -> textures/entity/<id>.png) and its own export (artillery/<id>.json with the extra "muzzle" point and
"muzzle_dir" direction read by the Java TentType.Muzzle, for the future firing system). Kept out of merchantlib.py on
purpose (the merchant tents' library stays byte-stable).

A generator (tools/merchant/generate_<id>.py) does, in this order:

    import artillery as ar
    ar.setup("canon_x")                       # collisions / uuids reset (call first)
    atlas = ar.Atlas("canon_x")               # wood, wood_dark, plank, end_grain, iron, strap, gunmetal, ring, bore,
                                              # ball, brass, rope
    root = ar.Bone("canon_x")
    ... ar.lathe (round barrel, staves) / ar.cylinder_x / ar.ball / cl.wheel / cl.axle / ar.box ...
    ar.export(root, "canon_x", atlas, muzzle=(x, y, z), muzzle_dir=(dx, dy, dz), icon=fn)

Coordinates: prop-local blocks, y up (y = 0 = top of the ground block), +z = the side facing the player who placed it
(the cannon's breech: its muzzle points to -z, where that player was looking), the anchor block's centre at (0, 0, 0).
Bones: the cannon's moving parts each have their own bone, pivot at their axis (see generate_canon_medieval.py);
small things go under a bone named "detail" (hidden beyond tentDecorDistance), the cannonballs under "furniture".
"""
import json
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402  (puts tools/, tools/tents and tools/carts on the path)
import cartlib as cl  # noqa: E402
from galley_texture import _rgb, _jitter, _mix, _scale, fine_wood, hammered_iron, end_grain, polished_metal, twisted_rope  # noqa: E402

tl, gg, gn = ml.tl, ml.gg, ml.gn
v3, norm, Bone, add_cube, beam = ml.v3, ml.norm, ml.Bone, ml.add_cube, ml.beam
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ASSETS, ROOT = ml.ASSETS, ml.ROOT
collide, COLLIDERS = ml.collide, ml.COLLIDERS
rx, ry, rz = gg.rx, gg.ry, gg.rz
box = ml.box


def setup(name):
    """Resets the collision list and the uuids for one prop (call first)."""
    ml.setup(name)


# ---------------------------------------------------------------- atlas
OAK = _rgb("8a5a2c")
OAK_DARK = _rgb("3c2410")
IRON = _rgb("3e3e44")
GUNMETAL = _rgb("38383e")

_REGIONS = [  # (name, w, h) packed in rows
    ("wood", 64, 16), ("wood_dark", 64, 16), ("plank", 64, 64), ("gunmetal", 64, 64),
    ("end_grain", 16, 16), ("iron", 32, 16), ("ring", 32, 16), ("bore", 16, 16), ("ball", 16, 16), ("brass", 16, 16),
    ("rope", 16, 16), ("strap", 8, 32), ("strap_h", 32, 8), ("tyre", 32, 8), ("plank_end", 32, 32),
]


class Atlas:
    """The atlas of one artillery prop (256 x 256): oak beams and planks, end grain, forged iron (straps, tyres, hub
    bands), the black gun metal of the barrel and its rings, the dark bore, cannonball iron. Painted on export."""

    def __init__(self, name, size=256):
        self.name, self.size = name, size
        self.regions = {}
        x = y = row = 0
        for n, w, h in _REGIONS:
            if x + w > size:
                x, y, row = 0, y + row, 0
            self.regions[n] = (x, y, w, h)
            x += w
            row = max(row, h)
        if y + row > size:
            raise ValueError("atlas too small")
        self._apply()

    def _apply(self):
        gn.REGIONS = {k: (0,) + r for k, r in self.regions.items()}
        gn.SIZE = self.size
        gg.REGIONS = dict(self.regions)
        gg.SIZE = self.size

    def make(self, path):
        from PIL import Image
        img = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
        _paint(img, self.regions)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        img.save(path)
        return img


def _gunmetal(img, R, base, rng, streak=0.06, light=0.0):
    """Cast black iron: a near-black surface, faint streaks along u (the casting direction), soft lighter blotches."""
    u, v, w, h = R
    px = img.load()
    blot = [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(2, 6)) for _ in range(max(4, w * h // 90))]
    rows = [1.0 + rng.uniform(-streak, streak) for _ in range(h)]
    for y in range(h):
        for x in range(w):
            k = rows[y] + light
            for cx, cy, r in blot:
                d = math.hypot((x + 0.5 - cx) / 1.6, y + 0.5 - cy)
                if d < r:
                    k += 0.16 * (1 - d / r)
            if rng.random() < 0.05:
                k += rng.choice((-0.12, 0.14))
            px[u + x, v + y] = _jitter(_scale(base, k), rng, 2) + (255,)


def _bolts(img, R, spots, head=_rgb("6a6c72"), dark=_rgb("1c1c20")):
    u, v = R[0], R[1]
    px = img.load()
    for (x, y) in spots:
        px[u + x, v + y] = head + (255,)
        px[u + x + 1, v + y] = _scale(head, 0.8) + (255,)
        px[u + x, v + y + 1] = _scale(head, 0.75) + (255,)
        px[u + x + 1, v + y + 1] = dark + (255,)


def _paint(img, R):
    rng = random.Random(1160)
    fine_wood(img, R["wood"], OAK, OAK_DARK, 4, rng, knots=0.12)
    fine_wood(img, R["wood_dark"], _scale(OAK, 0.82), _scale(OAK_DARK, 0.8), 4, rng, knots=0.1)
    fine_wood(img, R["plank"], OAK, OAK_DARK, 5, rng, knots=0.18)
    fine_wood(img, R["plank_end"], _scale(OAK, 0.9), OAK_DARK, 8, rng, vertical=True)
    end_grain(img, R["end_grain"], _rgb("b98a52"), _rgb("6e4a26"), rng)
    hammered_iron(img, R["iron"], IRON, rng, dent=0.09)
    _bolts(img, R["iron"], [(3, 3), (13, 4), (24, 3), (7, 11), (19, 11), (28, 10)])
    _gunmetal(img, R["gunmetal"], GUNMETAL, rng)
    _gunmetal(img, R["ring"], _scale(GUNMETAL, 1.25), rng, streak=0.04, light=0.05)
    u, v, w, h = R["ring"]
    px = img.load()
    for x in range(w):   # a worn lighter edge on both sides of a ring band
        for y in (0, h - 1):
            px[u + x, v + y] = _jitter(_scale(GUNMETAL, 1.7), rng, 3) + (255,)
    u, v, w, h = R["bore"]
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = _jitter((14, 13, 14), rng, 2) + (255,)
    u, v, w, h = R["ball"]
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - 5, y - 5) / 11
            px[u + x, v + y] = _jitter(_scale(_rgb("3a3b42"), 1.35 - 0.5 * min(1, d)), rng, 4) + (255,)
    polished_metal(img, R["brass"], [(0, (90, 60, 20)), (0.5, (170, 120, 50)), (1, (226, 190, 110))], rng)
    twisted_rope(img, R["rope"], _rgb("c9a46a"), _rgb("7a5a30"), rng)
    # vertical strap (8 x 32, stretched over each strap face): forged band with three bolt heads
    hammered_iron(img, R["strap"], _scale(IRON, 1.05), rng, dent=0.08)
    _bolts(img, R["strap"], [(3, 3), (3, 15), (3, 27)])
    hammered_iron(img, R["strap_h"], _scale(IRON, 1.05), rng, dent=0.08)
    _bolts(img, R["strap_h"], [(3, 3), (15, 3), (27, 3)])
    # tyre: iron band with a rivet every 8 px
    hammered_iron(img, R["tyre"], _scale(IRON, 1.1), rng, dent=0.06)
    _bolts(img, R["tyre"], [(3 + 8 * k, 3) for k in range(4)])


# ---------------------------------------------------------------- geometry
def _frame(a):
    """Two unit vectors perpendicular to the unit axis a (e0, e1 with a = e0 x e1 orientation)."""
    ref = v3(0, 1, 0) if abs(a[1]) < 0.9 else v3(1, 0, 0)
    e0 = norm(ref - np.dot(ref, a) * a)
    e1 = np.cross(a, e0)
    return e0, e1


def lathe(bone, name, origin, axis, segments, n=16, th=0.12, region="gunmetal", inner="bore", phase=0.5, overlap=0.004):
    """A round (n-sided) body of revolution about `axis` (unit) through `origin`: segments = [(s0, s1, r0, r1, region
    or None, th or None)], s along the axis, r the apothem of the polygon (flat to flat). Each segment is n staves
    (tilted boxes) whose outer faces make the polygon and whose end faces close the steps between segments (give a
    thick stave, th = r - bore, for the mouth so its end face is the annulus round the bore and its inner faces the
    bore). Returns the number of cubes."""
    origin, axis = v3(*origin), norm(v3(*axis))
    e0, e1 = _frame(axis)
    count = 0
    for k, seg in enumerate(segments):
        s0, s1, r0, r1 = seg[:4]
        reg = seg[4] if len(seg) > 4 and seg[4] else region
        t = seg[5] if len(seg) > 5 and seg[5] else th
        rm = (r0 + r1) / 2
        width = 2 * rm * math.tan(math.pi / n) + overlap
        for i in range(n):
            ang = 2 * math.pi * (i + phase) / n
            e = e0 * math.cos(ang) + e1 * math.sin(ang)
            p0 = origin + axis * s0 + e * r0
            p1 = origin + axis * s1 + e * r1
            d = p1 - p0
            L = np.linalg.norm(d)
            u = d / L
            nn = norm(e - np.dot(e, u) * u)
            vv = np.cross(nn, u)
            c = (p0 + p1) / 2 - nn * (t / 2)
            add_cube(bone, "%s_%d_%d" % (name, k, i), c, np.column_stack([u, vv, nn]), (L + overlap, width, t),
                     {"all": reg, "-3": inner}, u_dir=axis)
            count += 1
    return count


def disc(bone, name, center, axis, r, th, region, n=8, phase=0.5):
    """A flat round plate (n-gon of apothem r, thickness th along `axis`): n//4 square boxes turned about the axis."""
    center, axis = v3(*center), norm(v3(*axis))
    e0, e1 = _frame(axis)
    k = max(1, n // 4)
    side = 2 * r
    for i in range(k):
        ang = math.pi / 2 * (i + phase) / k
        a = e0 * math.cos(ang) + e1 * math.sin(ang)
        b = np.cross(axis, a)
        add_cube(bone, "%s_%d" % (name, i), center, np.column_stack([a, b, axis]), (side, side, th), region)


def cylinder_x(bone, name, x0, x1, y, z, r, region, n=8, cap=None):
    """A short round bar along x (trunnions, axle arms): n//4 square bars turned about x (an n-gon outline)."""
    k = max(1, n // 4)
    for i in range(k):
        R = rx(math.pi / 2 * i / k)
        add_cube(bone, "%s_%d" % (name, i), ((x0 + x1) / 2, y, z), R, (abs(x1 - x0), 2 * r, 2 * r),
                 {"all": region, "+1": cap or region, "-1": cap or region})


def ball(bone, name, center, r, region="ball"):
    """A cannonball: a faceted sphere of three stacked octagonal prisms about y (a wide belt, a taller middle, a
    narrow full-height core: a stepped round outline from every side, six boxes)."""
    c = v3(*center)
    for k, (w, h) in enumerate(((0.86, 0.60), (0.66, 0.86), (0.40, 1.0))):
        for i, a in enumerate((0.0, math.pi / 4)):
            add_cube(bone, "%s_%d_%d" % (name, k, i), c, ry(a + k * math.pi / 8), (2 * r * w, 2 * r * h, 2 * r * w), region)


def ball_pile(bone, name, foot, r=0.13, solid=True):
    """A small pyramid of cannonballs on the ground: three touching balls and one on top."""
    f = v3(*foot)
    pts = []
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.3
        pts.append(f + v3(math.cos(a), 0, math.sin(a)) * (r * 1.16) + UP * r)
    pts.append(f + UP * (r + r * 1.63))
    for k, p in enumerate(pts):
        ball(bone, "%s_%d" % (name, k), p, r)
    if solid:
        e = r * 2.2
        collide((f[0] - e, 0.0, f[2] - e, f[0] + e, r * 3.5, f[2] + e))


# ---------------------------------------------------------------- export
def export(root, name, atlas, muzzle, muzzle_dir, icon=None, visible_box=(6, 4, 0)):
    """Writes artillery/<id>.json (model, texture, extent, colliders, muzzle, muzzle_dir), models/entity/<id>.bbmodel,
    blockbench/<id>.bbmodel, textures/entity/<id>.png and textures/item/<id>.png (icon(path)).
    ARTILLERY_OUT=<file.bbmodel>: writes only the model (and its atlas next to it) there, for previews."""
    out_model = os.environ.get("ARTILLERY_OUT")
    tex_name = "%s.png" % name
    tex_path = os.path.join(ASSETS, "textures/entity", tex_name) if not out_model else os.path.join(os.path.dirname(out_model), tex_name)
    atlas._apply()
    atlas.make(tex_path)
    with open(tex_path, "rb") as f:
        png = f.read()
    textures = [gn.texture_entry(tex_name, atlas.size, png, "entity", tex_name)]
    textures[0]["id"] = "0"
    ext = tl.extent(root)
    outs = [out_model] if out_model else [os.path.join(ROOT, "blockbench/%s.bbmodel" % name),
                                          os.path.join(ASSETS, "models/entity/%s.bbmodel" % name)]
    model = gn.export(root, [], textures, outs, name=name, visible_box=visible_box)
    d = norm(v3(*muzzle_dir))
    if not out_model:
        data = {
            "model": "models/entity/%s.bbmodel" % name,
            "texture": "textures/entity/%s" % tex_name,
            "decor": None,
            "extent": [round(float(v), 3) for v in ext],
            "colliders": [[round(float(v), 3) for v in (b[0], max(0.0, b[1]), b[2], b[3], b[4], b[5])] for b in COLLIDERS],
            "muzzle": [round(float(c), 3) for c in muzzle],
            "muzzle_dir": [round(float(c), 4) for c in d],
        }
        path = os.path.join(ASSETS, "artillery/%s.json" % name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=1)
        if icon is not None:
            icon(os.path.join(ASSETS, "textures/item/%s.png" % name))
    print("%s: %d cubes, extent %s, %d collision boxes, muzzle %s dir %s" % (
        name, len(model["elements"]), ["%.2f" % v for v in ext], len(COLLIDERS), ["%.2f" % c for c in muzzle], ["%.3f" % c for c in d]))
    return model
