"""Defensive stake (pieu_defensif, 1.24.0): ONE sharpened stake planted in the ground, leaning ~40 degrees, its point
towards the BACK of the prop (local -z: away from the player who placed it, who stands inside the camp and plants
stakes facing outward). A single thick worn dark-brown trunk (about 0.6 across: two crossed boxes per section, so its
corners read rounded), sunk in a low ring of disturbed earth clods with a few grey stones round its foot, a thick
dark iron band with big square bolts where the point starts, a torn red cloth knotted round the trunk just below the
band with three ragged tails hanging straight down, and a long very sharp light-wood point (stepped sections of
crossed boxes narrowing to the tip, dark red stains near its base). About 3.2 blocks long (2.85 above the ground),
the tip about 1.85 high: a mob walking towards the stake meets the point at body height.

The stake uses the decorations' family and helpers (tools/deco/decolib.py: Bone, beam, collisions, export rules) but
its OWN small atlas textures/entity/pieu_defensif.png (64 x 64, painted below), so the shared decorations atlas does
not change. Small things (bolts, clods, stones, grass, cloth tails) are under the bone "detail" (hidden beyond 32
blocks).

JSON (decorations/pieu_defensif.json): the extent is one block across (|x| < 0.5) so stakes can be planted side by
side one block apart (the area check only looks at the anchor's column); the collision boxes are three stepped boxes
along the trunk (the point has none); "hazard" = the point's last block (inflated a little) in model space, with the
model's damage, knockback and cooldown: the Java ticker (TentBlockEntity / StakeHazard) hurts hostile mobs touching it.

    python3 tools/deco/generate_pieu_defensif.py        # model, JSON, atlas, icon
    PIEU_OUT=/tmp/x.bbmodel python3 ...                  # only the model (previews)
"""
import json
import math
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decolib as dl  # noqa: E402

NAME = "pieu_defensif"
ATLAS = NAME + ".png"
SIZE = 64

# ---------------------------------------------------------------- geometry (prop-local blocks, +z = front)
ANGLE = math.radians(40.0)                              # lean above the ground
AX = np.array([0.0, math.sin(ANGLE), -math.cos(ANGLE)])  # the stake's axis, from the foot to the tip (towards -z)
UPV = np.array([0.0, math.cos(ANGLE), math.sin(ANGLE)])  # perpendicular to the axis, upwards
XV = np.array([1.0, 0.0, 0.0])
ZG = 0.05                                               # where the axis enters the ground
G = np.array([0.0, 0.0, ZG])
S_TRUNK = (-0.30, 1.55)      # trunk, along the axis (s = 0 at the ground)
S_BAND = (1.45, 1.71)        # iron band
S_CLOTH = (1.10, 1.42)       # red cloth knotted below the band
S_POINT = (1.62, 2.85)       # the light-wood point; its tip at s = 2.85
TRUNK = 0.58                 # trunk thickness
POINT_R = 0.27               # half thickness of the point at its base
HAZARD_LEN = 1.0             # the hazard: the point's last block
HAZARD = {"damage": 4.0, "knockback": 0.4, "cooldown": 20}


def P(s):
    return G + AX * s


def up_rolled(roll_deg):
    r = math.radians(roll_deg)
    return UPV * math.cos(r) + XV * math.sin(r)


# ---------------------------------------------------------------- atlas
def _rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _mix(a, b, t):
    return tuple(int(round(a[k] + (b[k] - a[k]) * t)) for k in range(3))


def _clamp(c):
    return tuple(max(0, min(255, int(v))) for v in c)


def p_bark(img, rng):
    """Worn dark-brown trunk: long streaks along u (the trunk's length), each row its own tone, dark cracks, pale wear."""
    w, h = img.size
    base, dark, light = _rgb("64432a"), _rgb("2e1d10"), _rgb("94683e")
    rows, t = [], 0.0
    for y in range(h):
        t = 0.55 * t + rng.uniform(-0.6, 0.6)
        rows.append(t)
    for y in range(h):
        for x in range(w):
            n = rows[y] + 0.22 * math.sin(x * 0.45 + y * 1.7) + rng.uniform(-0.18, 0.18)
            c = _mix(base, light if n > 0 else dark, min(1.0, abs(n) * 0.8))
            img.putpixel((x, y), _clamp(c) + (255,))
    for _ in range(10):  # long dark cracks along the grain
        y, x0, ln = rng.randrange(h), rng.randrange(w), rng.randint(8, 26)
        for x in range(x0, min(w, x0 + ln)):
            img.putpixel((x, y), dark + (255,))
            if rng.random() < 0.12:
                y = min(h - 1, y + 1)
    for _ in range(8):  # pale worn streaks
        y, x0, ln = rng.randrange(h), rng.randrange(w), rng.randint(4, 12)
        for x in range(x0, min(w, x0 + ln)):
            img.putpixel((x, y), _mix(light, _rgb("a27a4c"), rng.random()) + (255,))


def p_bark_dark(img, rng):
    p_bark(img, rng)
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = img.getpixel((x, y))
            img.putpixel((x, y), (int(r * 0.72), int(g * 0.7), int(b * 0.68), 255))


def p_band(img, rng):
    """Dark hammered iron, lighter rims at the two edges (u = along the stake)."""
    w, h = img.size
    base, dark, light = _rgb("3c3c40"), _rgb("232326"), _rgb("6a6a70")
    for y in range(h):
        for x in range(w):
            c = _mix(base, dark if rng.random() < 0.5 else light, rng.uniform(0, 0.35))
            if x in (0, w - 1):
                c = light
            elif x in (1, w - 2):
                c = _mix(base, light, 0.4)
            img.putpixel((x, y), _clamp(c) + (255,))
    for _ in range(5):  # rust specks
        img.putpixel((rng.randrange(2, w - 2), rng.randrange(h)), _rgb("5a3a28") + (255,))


def p_bolt(img, rng):
    w, h = img.size
    for y in range(h):
        for x in range(w):
            edge = x in (0, w - 1) or y in (0, h - 1)
            c = _rgb("2a2a2e") if edge else _mix(_rgb("6e6e74"), _rgb("8a8a90"), (x + y) / (w + h))
            img.putpixel((x, y), c + (255,))
    img.putpixel((1, 1), _rgb("a0a0a6") + (255,))


def p_point(stains):
    def paint(img, rng):
        """Light beige freshly cut wood, darker grain along u, optional dark red stains."""
        w, h = img.size
        base, dark, light = _rgb("c8a476"), _rgb("8a6a44"), _rgb("e2c89a")
        rows = [rng.uniform(-0.5, 0.5) for _ in range(h)]
        for y in range(h):
            for x in range(w):
                n = rows[y] * 0.6 + rng.uniform(-0.25, 0.25)
                c = _mix(base, light if n > 0 else dark, min(1.0, abs(n) * 0.7))
                img.putpixel((x, y), _clamp(c) + (255,))
        for _ in range(4):
            y = rng.randrange(h)
            for x in range(w):
                if rng.random() < 0.8:
                    img.putpixel((x, y), _mix(dark, base, 0.3) + (255,))
        if stains:
            red, red_dark = _rgb("7a1a14"), _rgb("4a0e0a")
            for _ in range(stains):
                cx, cy, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(1.5, 3.2)
                for y in range(h):
                    for x in range(w):
                        d = math.hypot((x - cx) * 0.35, y - cy)
                        if d < r * rng.uniform(0.7, 1.2):
                            img.putpixel((x, y), (red_dark if d < r * 0.4 else red) + (255,))
    return paint


def p_cloth(img, rng):
    """Red worn cloth, folds across (along v), a few darker creases."""
    w, h = img.size
    base, dark, light = _rgb("9a2620"), _rgb("5c1410"), _rgb("b83a2e")
    for y in range(h):
        for x in range(w):
            f = math.sin(x * 1.3 + math.sin(y * 0.5)) * 0.5 + rng.uniform(-0.25, 0.25)
            c = _mix(base, light if f > 0 else dark, min(1.0, abs(f) * 0.8))
            img.putpixel((x, y), _clamp(c) + (255,))


def p_tail(img, rng):
    """A hanging cloth tail (v = downwards): red with vertical folds, a ragged torn bottom (cut-out)."""
    w, h = img.size
    base, dark, light = _rgb("9a2620"), _rgb("5c1410"), _rgb("b83a2e")
    cut = [h - rng.randint(1, 4) for _ in range(w)]
    for x in range(w):
        if rng.random() < 0.35:
            cut[x] = h - rng.randint(4, 7)  # a deeper tear
    for y in range(h):
        for x in range(w):
            if y >= cut[x]:
                img.putpixel((x, y), (0, 0, 0, 0))
                continue
            f = math.sin(x * 1.6) * 0.5 + rng.uniform(-0.2, 0.2)
            c = _mix(base, light if f > 0 else dark, min(1.0, abs(f) * 0.8))
            if y >= cut[x] - 1:
                c = _mix(c, dark, 0.5)
            img.putpixel((x, y), _clamp(c) + (255,))


def p_dirt(img, rng):
    w, h = img.size
    cols = [_rgb("6a4a2e"), _rgb("5a3c24"), _rgb("7e5a38"), _rgb("4a301c"), _rgb("8a6440")]
    for y in range(h):
        for x in range(w):
            img.putpixel((x, y), rng.choice(cols) + (255,))


def p_stone(img, rng):
    w, h = img.size
    for y in range(h):
        for x in range(w):
            c = _mix(_rgb("8a8a88"), _rgb("5e5e5c") if rng.random() < 0.5 else _rgb("a4a4a0"), rng.uniform(0, 0.6))
            img.putpixel((x, y), c + (255,))


def p_grass(img, rng):
    """Cut-out tuft of tall grass blades (v = downwards)."""
    w, h = img.size
    for y in range(h):
        for x in range(w):
            img.putpixel((x, y), (0, 0, 0, 0))
    for _ in range(9):
        x = rng.randrange(w)
        top = rng.randint(0, h // 2)
        col = rng.choice([_rgb("6a9a2e"), _rgb("82b03a"), _rgb("4e7a22"), _rgb("9ac04a")])
        for y in range(top, h):
            xx = int(round(x + (h - y) * rng.uniform(-0.15, 0.15)))
            if 0 <= xx < w:
                img.putpixel((xx, y), col + (255,))


BASE = [  # (name, w, h, painter): packed in rows
    ("bark", 48, 16, p_bark), ("band", 16, 16, p_band),
    ("bark_dark", 32, 16, p_bark_dark), ("point", 16, 16, p_point(0)), ("point_stain", 16, 16, p_point(4)),
    ("cloth", 16, 16, p_cloth), ("dirt", 16, 16, p_dirt), ("grass", 16, 16, p_grass), ("tail", 8, 16, p_tail),
    ("stone", 8, 8, p_stone), ("bolt", 8, 8, p_bolt),
]
REGIONS = {}


def _pack():
    x = y = row = 0
    for name, w, h, _ in BASE:
        if x + w > SIZE:
            x, y, row = 0, y + row, 0
        REGIONS[name] = (x, y, w, h)
        x += w
        row = max(row, h)
    assert y + row <= SIZE, "atlas full"


_pack()


def make_texture(path):
    from PIL import Image
    import zlib
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    for name, w, h, painter in BASE:
        sub = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        painter(sub, random.Random(zlib.crc32(name.encode())))
        u, v, _, _ = REGIONS[name]
        img.paste(sub, (u, v))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


# ---------------------------------------------------------------- model
def seg(bone, name, s0, s1, th, w, region, roll=0.0, stretch=False, ends=None):
    """A box along the axis from s0 to s1 (th across in the vertical plane, w across in x), rolled about the axis."""
    reg = {"all": region, "+1": ends or region, "-1": ends or region}
    return dl.beam(bone, name, P(s0), P(s1), th, reg, width=w, up=up_rolled(roll), stretch=stretch)


def cross(bone, name, s0, s1, size, region, roll=0.0, stretch=False, ratio=0.74):
    """Two crossed boxes (size x size*ratio and size*ratio x size): a section with rounded-looking corners."""
    seg(bone, name + "_a", s0, s1, size, size * ratio, region, roll, stretch)
    seg(bone, name + "_b", s0, s1, size * ratio, size, region, roll, stretch)


def plate(bone, name, center, u, v, w, h, th, region, stretch=True, vdir=None):
    """A thin plate centred at `center`, w along u, h along v (unit vectors), th thick; the texture's v runs along
    vdir (default -v: the region's top at the plate's +v end)."""
    u, v = dl.norm(np.asarray(u, float)), dl.norm(np.asarray(v, float))
    n = np.cross(u, v)
    return dl.add_cube(bone, name, center, np.column_stack([u, v, n]), (w, h, th), region, stretch=stretch, u_dir=u,
                       v_dir=-v if vdir is None else vdir)


def build(root, det):
    rng = random.Random(7)
    # the trunk: two sections of crossed boxes, slightly different and rolled (a worn, irregular log)
    cross(root, "trunk_low", S_TRUNK[0], 0.82, TRUNK + 0.02, "bark", roll=2.0)
    cross(root, "trunk_high", 0.78, S_TRUNK[1], TRUNK - 0.01, "bark", roll=-3.0)
    # a few raised bark slabs breaking the outline
    for k, (s0, s1, side, off, w) in enumerate(((0.15, 0.6, XV, 0.06, 0.2), (0.55, 1.05, UPV, -0.08, 0.22),
                                               (0.95, 1.3, -XV, -0.04, 0.18), (0.3, 0.75, -UPV, 0.05, 0.2))):
        perp = np.cross(AX, side)
        c = P((s0 + s1) / 2) + side * (TRUNK / 2 + 0.012) + perp * off
        plate(det, "bark_slab_%d" % k, c, AX, perp, s1 - s0, w, 0.035, "bark_dark", stretch=False)
    # the iron band and its big square bolts (one per face, staggered)
    seg(root, "band", S_BAND[0], S_BAND[1], TRUNK + 0.1, TRUNK + 0.1, "band", stretch=True)
    sm = (S_BAND[0] + S_BAND[1]) / 2
    for k, (side, off) in enumerate(((UPV, -0.1), (XV, 0.08), (-UPV, 0.1), (-XV, -0.08))):
        perp = np.cross(side, AX)
        c = P(sm) + side * ((TRUNK + 0.1) / 2 + 0.03) + perp * off
        dl.add_cube(det, "bolt_%d" % k, c, np.column_stack([AX, perp, side]), (0.13, 0.13, 0.07), "bolt", stretch=True)
    # the point: stepped sections of crossed boxes narrowing to the tip, stained near the band
    n = 11
    L = S_POINT[1] - S_POINT[0]
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        r = POINT_R * (1.0 - (t0 + t1) / 2)
        reg = "point_stain" if k < 4 else "point"
        cross(root if k < 5 else det, "point_%d" % k, S_POINT[0] + L * t0 - 0.008, S_POINT[0] + L * t1 + 0.008, max(0.03, 2 * r), reg,
              roll=(-2.0, 2.0)[k % 2], stretch=True, ratio=0.7)
    seg(det, "point_tip", S_POINT[1] - 0.1, S_POINT[1], 0.03, 0.03, "point", stretch=True)
    # the red cloth: two askew wraps, a knot on the +x side, three ragged tails hanging straight down
    seg(root, "cloth_wrap", S_CLOTH[0], S_CLOTH[0] + 0.24, TRUNK + 0.07, TRUNK + 0.06, "cloth", roll=7.0, stretch=True)
    seg(root, "cloth_fold", S_CLOTH[0] + 0.16, S_CLOTH[1], TRUNK + 0.05, TRUNK + 0.08, "cloth", roll=-6.0, stretch=True)
    knot = P(S_CLOTH[0] + 0.18) + XV * (TRUNK / 2 + 0.07) + UPV * 0.1
    dl.add_cube(det, "cloth_knot", knot, np.column_stack([AX, np.cross(XV, AX), XV]), (0.2, 0.16, 0.12), "cloth", stretch=True)
    dl.add_cube(det, "cloth_knot_loop", knot + AX * 0.12 - UPV * 0.05 + XV * 0.02,
                np.column_stack([AX, np.cross(XV, AX), XV]), (0.14, 0.1, 0.08), "cloth", stretch=True)
    down = np.array([0.0, -1.0, 0.0])
    for k, (anchor, length, width, sway, side) in enumerate((
            (knot + XV * 0.02, 0.86, 0.17, 0.06, 1.0),
            (P(S_CLOTH[0] + 0.05) + XV * (TRUNK / 2 + 0.04) - UPV * 0.12, 0.62, 0.15, -0.08, 1.0),
            (P(S_CLOTH[0] + 0.14) - XV * (TRUNK / 2 + 0.04) - UPV * 0.1, 0.55, 0.15, 0.05, -1.0))):
        v = dl.norm(down + np.array([0.0, 0.0, sway]))
        u = np.array([0.0, 0.0, 1.0]) - v * v[2]
        c = anchor + v * (length / 2) + XV * 0.0
        plate(det, "cloth_tail_%d" % k, c, dl.norm(u), v, width, length, 0.025, {"all": "tail", "+1": "cloth", "-1": "cloth"}, vdir=v)
    # the ground: a patch of disturbed earth, a ring of clods round the trunk's foot, a few stones, grass tufts
    for k, (x, z, sx, sz, yaw) in enumerate(((0.0, ZG + 0.05, 0.62, 1.12, 0), (-0.2, ZG + 0.38, 0.5, 0.42, 25), (0.2, ZG - 0.4, 0.5, 0.44, -20),
                                              (0.22, ZG + 0.42, 0.42, 0.36, -35), (-0.22, ZG - 0.36, 0.44, 0.4, 30))):
        dl.add_cube(det, "earth_patch_%d" % k, (x, 0.006 + 0.004 * k, z), dl.ry(math.radians(yaw)), (sx, 0.012, sz), "dirt")
    for k in range(13):
        a = 2 * math.pi * k / 13 + rng.uniform(-0.15, 0.15)
        rx, rz = 0.36 * rng.uniform(0.85, 1.1), 0.58 * rng.uniform(0.85, 1.1)
        x = max(-0.42, min(0.42, rx * math.cos(a)))
        z = ZG + rz * math.sin(a)
        sx, sz, sy = rng.uniform(0.12, 0.2), rng.uniform(0.12, 0.22), rng.uniform(0.05, 0.12)
        dl.add_cube(det, "clod_%d" % k, (x, sy / 2, z), dl.ry(rng.uniform(-0.6, 0.6)), (sx, sy, sz), "dirt")
    for k, (x, z, s, hgt) in enumerate(((-0.33, ZG + 0.6, 0.2, 0.13), (0.37, ZG - 0.32, 0.12, 0.08), (-0.25, ZG - 0.66, 0.11, 0.07),
                                        (0.3, ZG + 0.6, 0.1, 0.06))):
        dl.add_cube(det, "stone_%d" % k, (x, hgt / 2, z), dl.ry(rng.uniform(-0.7, 0.7)), (s, hgt, s * 0.9), "stone")
    for k, (x, z, hgt) in enumerate(((0.38, ZG + 0.3, 0.32), (-0.4, ZG - 0.15, 0.28), (0.14, ZG + 0.62, 0.24))):
        for j, yaw in enumerate((45, -45)):
            R = dl.ry(math.radians(yaw + 10 * k))
            plate(det, "grass_%d_%d" % (k, j), (x, hgt / 2, z), R @ XV, np.array([0.0, 1.0, 0.0]), 0.3, hgt, 0.01,
                  {"all": None, "+3": "grass", "-3": "grass"})


def colliders():
    """Three stepped boxes along the trunk (ground to the band), none on the point."""
    out = []
    half_y, half_z = TRUNK / 2 * UPV[1], TRUNK / 2 * UPV[2]
    for s0, s1 in ((0.0, 0.6), (0.6, 1.1), (1.1, 1.6)):
        a, b = P(s0), P(s1)
        y0 = max(0.0, a[1] - half_y)
        y1 = b[1] + half_y + (0.1 if s0 == 0.0 else 0.0)   # the first box too high to step onto (0.6)
        out.append([-TRUNK / 2, y0, b[2] - half_z, TRUNK / 2, y1, a[2] + half_z])
    return [[round(v, 3) for v in box] for box in out]


def hazard_box():
    """The point's last block, inflated by 0.12: the box where a hostile mob gets hurt (model space)."""
    s0, s1 = S_POINT[1] - HAZARD_LEN, S_POINT[1]
    t = (s0 - S_POINT[0]) / (S_POINT[1] - S_POINT[0])
    r = POINT_R * (1 - t) + 0.12
    a, b = P(s0), P(s1)
    lo = np.minimum(a, b) - np.array([r, r * UPV[1], r * UPV[2]])
    hi = np.maximum(a, b) + np.array([r, r * UPV[1], r * UPV[2]])
    lo[1], hi[1], lo[2] = lo[1], b[1] + 0.12, b[2] - 0.12
    return [round(float(v), 3) for v in (lo[0], lo[1], lo[2], hi[0], hi[1], hi[2])]


def draw_icon(put):
    bark, dark, light, iron, red = (88, 58, 36), (52, 34, 20), (206, 172, 124), (64, 64, 70), (160, 38, 32)
    for k in range(16):
        x, y = 1 + k * 0.85, 14 - k * 0.8
        for d in (-1, 0, 1):
            xi, yi = int(round(x + d * 0.6)), int(round(y + d * 0.6))
            if k < 8:
                put(xi, yi, bark if d else dark)
            elif k < 10:
                put(xi, yi, iron)
            elif k < 15 and abs(d) <= (1 if k < 12 else 0):
                put(xi, yi, light if d <= 0 else (170, 136, 92))
    put(14, 1, light)
    put(15, 0, light)
    for y in (8, 9, 10, 11):
        put(6, y, red)
    put(7, 8, red)
    put(5, 12, red)
    for x in (0, 1, 2, 3, 4):
        put(x, 15, (110, 78, 48))
    put(4, 14, (128, 128, 124))


def export():
    dl.setup(NAME)
    dl.gn.REGIONS = {k: (0,) + r for k, r in REGIONS.items()}
    dl.gn.SIZE = SIZE
    dl.gg.REGIONS = dict(REGIONS)
    dl.gg.SIZE = SIZE
    root = dl.Bone(NAME)
    det = dl.Bone("detail", parent=root)
    build(root, det)
    out_model = os.environ.get("PIEU_OUT")
    tex_path = os.path.join(dl.ASSETS, "textures/entity", ATLAS) if not out_model else os.path.join(os.path.dirname(out_model), ATLAS)
    make_texture(tex_path)
    with open(tex_path, "rb") as f:
        png = f.read()
    textures = [dl.gn.texture_entry(ATLAS, SIZE, png, "entity", ATLAS)]
    textures[0]["id"] = "0"
    ext = list(dl.tl.extent(root))
    model_ext = list(ext)
    # one block across: stakes stand side by side one block apart (the model's clods may overhang a little)
    ext[0], ext[3] = max(ext[0], -0.49), min(ext[3], 0.49)
    outs = [out_model] if out_model else [os.path.join(dl.ROOT, "blockbench/%s.bbmodel" % NAME),
                                          os.path.join(dl.ASSETS, "models/entity/%s.bbmodel" % NAME)]
    model = dl.gn.export(root, [], textures, outs, name=NAME, visible_box=(4, 3, 0))
    if not out_model:
        data = {
            "model": "models/entity/%s.bbmodel" % NAME,
            "texture": "textures/entity/" + ATLAS,
            "decor": None,
            "extent": [round(float(v), 3) for v in ext],
            "colliders": colliders(),
            "light": 0,
            "hazard": dict(box=hazard_box(), **HAZARD),
        }
        path = os.path.join(dl.ASSETS, "decorations/%s.json" % NAME)
        with open(path, "w") as f:
            json.dump(data, f, indent=1)
        dl.icon(os.path.join(dl.ASSETS, "textures/item/%s.png" % NAME), draw_icon)
    print("%s: %d cubes, model box %s, extent x %.2f..%.2f, tip %s, hazard %s" % (
        NAME, len(model["elements"]), ["%.2f" % v for v in model_ext], ext[0], ext[3], ["%.2f" % v for v in P(S_POINT[1])], hazard_box()))
    return model


if __name__ == "__main__":
    export()
