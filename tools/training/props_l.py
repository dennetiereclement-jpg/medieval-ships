"""Props of the tatami and the sword & shield training areas (1.18.0, agent L): training_area_tatami,
training_area_shield.

The fence ring, the floors, the stalls, the lantern posts and the banners come from traininglib (agent K); this module
adds the atlas regions of the two areas (painted into the free band of the area's atlas with atlas.add, named "l_...",
plus a few shared ones of props_m1 / props_m8) and the geometry of the things only these two areas have:

    import props_l as pl
    pl.add_regions(atlas)                        # before export
    pl.wooden_dummy(bone, det, name, foot, ...)  # the wooden dummy wearing an iron helmet, holding a sword and a round shield
                                                 # (target=tr.target(A, "shield_dummy"): an interactive target, 1.19.0)
    pl.round_shield(...), pl.helmet(...), pl.shield_rack(...), pl.stone_pillar(...)
    pl.staff(...), pl.wooden_sword(...), pl.lean_on_fence(...), pl.practice_rack(...), pl.flower_pot(...),
    pl.folded_stack(...), pl.jar(...), pl.mat_roll(...), pl.floor_knot(...), pl.lantern_gallows(...)
    pl.icon_tatami(path)                         # the tatami area's item icon

Coordinates: area-local blocks (y up, y = 0 = top of the ground block, +z = the front, towards the player who placed
it). Cubes named "glow..." are drawn full bright. Every solid prop declares its collision box (merchantlib.collide).
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, ".."))
for _p in (HERE, os.path.join(TOOLS, "merchant")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import merchantlib as ml  # noqa: E402
import props_m1 as p1  # noqa: E402
import props_m8 as p8  # noqa: E402

v3, norm, add_cube, beam = ml.v3, ml.norm, ml.add_cube, ml.beam
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ry, rx, rz = ml.ry, ml.rx, ml.rz
_rgb, _mix, _jitter, _scale = ml._rgb, ml._mix, ml._jitter, ml._scale
collide = ml.collide
CLEAR = (0, 0, 0, 0)

SHIELD_RED, SHIELD_WHITE = _rgb("a8261e"), _rgb("ece2cc")
IRON, IRON_D, IRON_L = _rgb("7c8088"), _rgb("44474e"), _rgb("b4b8c0")
DUMMY_WOOD, DUMMY_DARK = _rgb("c69a52"), _rgb("7a5426")
ASH, ASH_D = _rgb("dcc08a"), _rgb("9a7a48")
PINK = ["f2a2c8", "e884b4", "f8c4dc", "d8689e"]


# ================================================================ painters (img = the region, w x h RGBA)
def _shield_face(seed, rings=((0.0, "boss"), (0.24, SHIELD_RED), (0.48, SHIELD_WHITE), (0.7, SHIELD_RED), (0.88, "rim"))):
    """The painted face of a round wooden shield (cut out round): from the centre out an iron boss, a red disc, a white
    ring, a red ring, the iron rim with rivets; faint vertical plank seams under the paint."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        cx, cy, R = (w - 1) / 2, (h - 1) / 2, w / 2
        for y in range(h):
            for x in range(w):
                d = math.hypot(x - cx, y - cy) / R
                if d > 1.0:
                    px[x, y] = CLEAR
                    continue
                kind = rings[0][1]
                for r0, k in rings:
                    if d >= r0:
                        kind = k
                if kind == "boss":
                    c = _mix(IRON_L, IRON, min(1.0, d / 0.24 + 0.25 * (x - cx) / R))
                elif kind == "rim":
                    a = math.atan2(y - cy, x - cx)
                    c = IRON_D if d > 0.97 else IRON
                    if abs(math.sin(a * 4)) < 0.16 and 0.9 < d < 0.96:
                        c = IRON_L
                else:
                    c = kind
                    if x % 6 == 0:
                        c = _scale(c, 0.9)
                    edge = min(abs(d - r) for r, _ in rings[1:])
                    if edge < 0.025:
                        c = _scale(c, 0.78)
                px[x, y] = _jitter(c, rng, 6) + (255,)
    return p


def _shield_back(seed):
    """The back of the round shield (cut out round): vertical planks, the iron rim, a leather strap across."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        cx, cy, R = (w - 1) / 2, (h - 1) / 2, w / 2
        for y in range(h):
            for x in range(w):
                d = math.hypot(x - cx, y - cy) / R
                if d > 1.0:
                    px[x, y] = CLEAR
                    continue
                c = _scale(_rgb("8a6034"), 1.0 + 0.08 * math.sin(x * 0.9 + (x // 6) * 2.0))
                if x % 6 == 0:
                    c = _rgb("4e3418")
                if d > 0.9:
                    c = IRON
                if abs(y - cy) < 2.2 and d < 0.8:
                    c = _rgb("5a3a1e")
                px[x, y] = _jitter(c, rng, 6) + (255,)
    return p


def _hammered(seed, base=IRON, rivets=True):
    """Hammered iron (helmets, bosses): mottled grey, light dents, a row of rivets near the bottom."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _scale(base, rng.choice((0.9, 1.0, 1.0, 1.08)) * (1.08 - 0.18 * y / h))
                px[x, y] = _jitter(c, rng, 5) + (255,)
        for _ in range(w * h // 18):
            x, y = rng.randrange(w), rng.randrange(h)
            px[x, y] = _jitter(IRON_L, rng, 8) + (255,)
        if rivets:
            for x in range(1, w, 4):
                px[x, h - 3] = IRON_L + (255,)
                px[x, h - 2] = IRON_D + (255,)
            for x in range(w):
                px[x, h - 1] = IRON_D + (255,)
    return p


def _wood_grain(seed, base, dark, planks=0, knots=2, vertical=True):
    """Light wood: grain along v (vertical) or u, plank seams every w / planks px, a couple of knots and nails."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        phase = [rng.uniform(0, 6) for _ in range(8)]
        for y in range(h):
            for x in range(w):
                a, b = (x, y) if vertical else (y, x)
                k = 1.0 + 0.07 * math.sin(a * 1.7 + phase[a % 8] + 0.15 * b) + 0.04 * math.sin(b * 0.4 + a)
                c = _scale(base, k)
                if planks and (a % max(2, (w if vertical else h) // planks) == 0):
                    c = dark
                px[x, y] = _jitter(c, rng, 5) + (255,)
        for _ in range(knots):
            cx, cy = rng.randrange(1, w - 1), rng.randrange(1, h - 1)
            px[cx, cy] = _scale(dark, 0.9) + (255,)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                px[(cx + dx) % w, (cy + dy) % h] = _mix(base, dark, 0.6) + (255,)
    return p


def _dummy_wood(seed):
    """The wooden dummy's body: light oak boards with dark seams, nail heads at the board ends."""
    def p(img):
        _wood_grain(seed, DUMMY_WOOD, DUMMY_DARK, planks=3, knots=3)(img)
        px = img.load()
        w, h = img.size
        for x in range(w // 6, w, w // 3):
            for y in (2, h - 3):
                px[x, y] = IRON_D + (255,)
    return p


def _stone_top(seed):
    """The top of a stone pillar cap: grey slab, a darker chamfer border."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _scale(_rgb("9c9890"), rng.choice((0.94, 1.0, 1.05)))
                if x in (0, w - 1) or y in (0, h - 1):
                    c = _rgb("6a6660")
                px[x, y] = _jitter(c, rng, 6) + (255,)
    return p


def _knot(seed, colour=_rgb("a8261e"), dark=_rgb("6a1410")):
    """The red decorative motif in the middle of the tatami floor (cut out): a lotus of five petals over a loop knot,
    two curled ribbons on each side."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                px[x, y] = CLEAR
        cx, cy = (w - 1) / 2, h * 0.52

        def put(x, y, c):
            x, y = int(round(x)), int(round(y))
            if 0 <= x < w and 0 <= y < h:
                px[x, y] = _jitter(c, rng, 6) + (255,)
        s = w / 32.0
        for k in range(5):   # petals
            a = math.pi * (0.1 + 0.2 * k) + math.pi
            L = (9 if k == 2 else 7) * s
            for t in np.linspace(0, 1, 30):
                r = L * t
                wid = 2.2 * s * math.sin(math.pi * t)
                bx, by = cx + math.cos(a) * r, cy + math.sin(a) * r
                for q in np.linspace(-wid, wid, 6):
                    put(bx - math.sin(a) * q, by + math.cos(a) * q, colour)
        for t in np.linspace(0, 2 * math.pi, 60):   # the loop knot under it
            put(cx + 4 * s * math.cos(t), cy + 3 * s + 2.2 * s * math.sin(2 * t), dark)
        for sgn in (-1, 1):                          # the ribbons
            for t in np.linspace(0, 1, 40):
                put(cx + sgn * (4 + 9 * t) * s, cy + 3 * s + 3 * s * math.sin(t * 5.5) * (1 - t * 0.4), colour)
                put(cx + sgn * (4 + 9 * t) * s, cy + 3 * s + 3 * s * math.sin(t * 5.5) * (1 - t * 0.4) + 1, dark)
    return p


def _seam_line(seed):
    """A dark mat seam (the inner square drawn on the tatami floor)."""
    def p(img):
        rng = random.Random(seed)
        px = img.load()
        for y in range(img.height):
            for x in range(img.width):
                px[x, y] = _jitter(_rgb("5a4426"), rng, 6) + (255,)
    return p


def _pink_flowers(seed):
    """A bushy clump of pink flowers seen from the side (cut out): leafy stems from the bottom middle, many round
    pink blossoms (light centre) over the upper two thirds."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                px[x, y] = CLEAR
        greens = [_rgb("4e8e30"), _rgb("3e7a28"), _rgb("5a9a36"), _rgb("2e6a20")]
        tops = []
        for k in range(16):
            x0 = w / 2 + rng.uniform(-w * 0.12, w * 0.12)
            x1 = w / 2 + rng.uniform(-w * 0.45, w * 0.45)
            top = rng.uniform(2, h * 0.55)
            tops.append((x1, top))
            for y in range(int(top), h):
                t = (y - top) / max(1.0, h - top)
                xi = int(round(x1 + (x0 - x1) * t))
                if 0 <= xi < w:
                    px[xi, y] = _jitter(rng.choice(greens), rng, 6) + (255,)
                    if rng.random() < 0.35 and y > h * 0.4:
                        for dx in (-2, -1, 1, 2):
                            if 0 <= xi + dx < w and rng.random() < 0.5:
                                px[xi + dx, y] = _jitter(rng.choice(greens), rng, 8) + (255,)
        pinks = [_rgb(c) for c in PINK]
        for k in range(22):
            if k < len(tops):
                cx, cy = tops[k]
            else:
                cx, cy = rng.uniform(w * 0.1, w * 0.9), rng.uniform(h * 0.05, h * 0.6)
            r = rng.uniform(1.6, 2.6)
            c = rng.choice(pinks)
            for y in range(int(cy - r - 1), int(cy + r + 2)):
                for x in range(int(cx - r - 1), int(cx + r + 2)):
                    if 0 <= x < w and 0 <= y < h and math.hypot(x - cx, y - cy) <= r:
                        px[x, y] = _jitter(_scale(c, 1.0 - 0.15 * (y - cy) / r), rng, 8) + (255,)
            xi, yi = int(round(cx)), int(round(cy))
            if 0 <= xi < w and 0 <= yi < h:
                px[xi, yi] = _rgb("f8e070") + (255,)
    return p


REGIONS = {
    "l_shield": (32, 32, _shield_face(501)),
    "l_shield_blue": (32, 32, _shield_face(502, rings=((0.0, "boss"), (0.24, _rgb("2c3f86")), (0.48, SHIELD_WHITE),
                                                         (0.7, _rgb("2c3f86")), (0.88, "rim")))),
    "l_shield_back": (32, 32, _shield_back(503)),
    "l_iron": (16, 16, _hammered(504)),
    "l_iron_plain": (16, 16, _hammered(505, rivets=False)),
    "l_dummy": (32, 32, _dummy_wood(506)),
    "l_dummy_dark": (16, 16, _wood_grain(507, DUMMY_DARK, _scale(DUMMY_DARK, 0.7), knots=1)),
    "l_ash": (16, 16, _wood_grain(508, ASH, ASH_D, knots=1)),
    "l_ash_dark": (16, 16, _wood_grain(509, _rgb("a07848"), _rgb("5a3e1e"), knots=1)),
    "l_stone": (32, 32, p8._stone(510, base=_rgb("8e8a84"), mortar=_rgb("5c5852"), rows=3, cols=2)),
    "l_stone_top": (16, 16, _stone_top(511)),
    "l_flowers": (32, 32, _pink_flowers(512)),
    "l_knot": (48, 48, _knot(513)),
    "l_seam": (8, 8, _seam_line(514)),
}
SHARED = ["jar", "jar_top", "linen", "soil"]   # props_m1 regions


def add_regions(atlas, names=None):
    """Adds this module's regions (all, or `names`) and the props_m1 ones it uses (jars) to the area's atlas."""
    for n in (names or REGIONS):
        w, h, painter = REGIONS[n]
        if n in atlas.regions and n not in atlas.painters:
            continue
        atlas.add(n, w, h, painter)
    p1.add_regions(atlas, SHARED)


# ================================================================ geometry helpers
def _frame(yaw):
    return ry(yaw)


def _to(foot, R, p):
    return v3(*foot) + R @ v3(*p)


def box(bone, name, lo, hi, region, solid=False, **kw):
    return ml.box(bone, name, lo, hi, region, solid=solid, **kw)


def lbox(bone, name, foot, R, lo, hi, region, stretch=True, **kw):
    """A box given in a local frame (foot + R @ p), axis-aligned in that frame."""
    lo, hi = v3(*lo), v3(*hi)
    return add_cube(bone, name, _to(foot, R, (lo + hi) / 2), R, np.abs(hi - lo), region, stretch=stretch, **kw)


# ================================================================ shields, helmets, weapons
def round_shield(bone, name, center, normal=(0, 0, 1), r=0.32, face="l_shield", back="l_shield_back", th=0.045, boss=True,
                 up=(0, 1, 0)):
    """A round wooden shield (cut-out disc, painted face towards `normal`, planked back) with a domed iron boss and its
    iron rim drawn on the face; returns the centre of its back (where the hand / the strap holds it)."""
    c, n = v3(*center), norm(v3(*normal))
    upv = v3(*up)
    upv = norm(upv - np.dot(upv, n) * n)
    side = np.cross(upv, n)
    axes = np.column_stack([side, upv, n])
    add_cube(bone, name, c, axes, (2 * r, 2 * r, th), {"all": None, "+3": face, "-3": back}, stretch=True, u_dir=side, v_dir=-upv)
    if boss:   # a round-ish domed boss: two squares turned 45 degrees about the normal, a smaller cap
        rot = np.column_stack([(side + upv) / 2 ** 0.5, (upv - side) / 2 ** 0.5, n])
        add_cube(bone, name + "_boss", c + n * (th / 2 + 0.02), axes, (r * 0.36, r * 0.36, 0.04), "l_iron_plain")
        add_cube(bone, name + "_boss_r", c + n * (th / 2 + 0.02), rot, (r * 0.36, r * 0.36, 0.038), "l_iron_plain")
        add_cube(bone, name + "_boss_top", c + n * (th / 2 + 0.05), rot, (r * 0.2, r * 0.2, 0.03), "l_iron")
    return c - n * (th / 2)


def helmet(bone, name, head_center, R, s=0.32):
    """An iron helmet over a head of width s centred at head_center (frame R, +z = the face): the bucket over the top
    half of the head, the flat crown, the dark eye slit band, the nose guard and two cheek plates."""
    c = v3(*head_center)
    lbox(bone, name, c, R, (-s * 0.58, -s * 0.02, -s * 0.56), (s * 0.58, s * 0.6, s * 0.56), "l_iron")
    lbox(bone, name + "_crown", c, R, (-s * 0.46, s * 0.6, -s * 0.46), (s * 0.46, s * 0.7, s * 0.46), "l_iron_plain")
    lbox(bone, name + "_slit", c, R, (-s * 0.5, -s * 0.06, s * 0.5), (s * 0.5, s * 0.06, s * 0.6), "black_iron")
    lbox(bone, name + "_nose", c, R, (-s * 0.06, -s * 0.36, s * 0.52), (s * 0.06, s * 0.06, s * 0.62), "l_iron_plain")
    for sg in (-1, 1):
        lbox(bone, "%s_cheek_%d" % (name, (sg + 1) // 2), c, R, (sg * s * 0.5 - s * 0.08, -s * 0.42, -s * 0.2),
             (sg * s * 0.5 + s * 0.08, -s * 0.02, s * 0.5), "l_iron_plain")


def sword(bone, name, base, up=(0, 1, 0), facing=(0, 0, 1), length=0.95, blade="steel", hilt="iron", grip="leather"):
    """A steel sword from the pommel `base` along `up` (merchantlib.sword)."""
    ml.sword(bone, name, base, up=up, facing=facing, length=length, blade=blade, hilt=hilt, grip=grip)


def wooden_sword(bone, name, base, up=(0, 1, 0), facing=(0, 0, 1), length=0.9):
    """A wooden practice sword (bokken): pale ash blade, dark guard, leather-wrapped grip."""
    ml.sword(bone, name, base, up=up, facing=facing, length=length, blade="l_ash", hilt="l_ash_dark", grip="leather")


def staff(bone, name, foot, top, d=0.06, region="l_ash"):
    """A training staff (bo) from foot to top: pale ash, two dark grip bands."""
    foot, top = v3(*foot), v3(*top)
    beam(bone, name, foot, top, d, {"all": region, "+1": "end_grain", "-1": "end_grain"})
    for k, t in enumerate((0.38, 0.62)):
        p = foot + (top - foot) * t
        beam(bone, "%s_band_%d" % (name, k), p - norm(top - foot) * 0.05, p + norm(top - foot) * 0.05, d * 1.25, "leather")


def lean_on_fence(bone, name, items, start, end, rail_y, inward, foot_off=0.32, lengths=None):
    """Training weapons leaning against a fence: their feet on the ground `foot_off` inside the fence, their upper parts
    resting on the top rail (height rail_y); start / end = two ground points ON the fence line; inward = the unit
    vector into the area; items in turn among "staff", "wsword", "sword". No collision (they lean on the fence)."""
    a, b, n = v3(*start), v3(*end), norm(v3(*inward))
    k = len(items)
    for i, it in enumerate(items):
        t = (i + 0.5) / k
        on = a + (b - a) * t
        foot = on + n * foot_off
        rest = on + n * 0.07 + UP * rail_y
        d = norm(rest - foot)
        L = (lengths[i] if lengths else (1.75 if it == "staff" else 0.95))
        nm = "%s_%s_%d" % (name, it, i)
        if it == "staff":
            staff(bone, nm, foot, foot + d * L)
        elif it == "wsword":
            wooden_sword(bone, nm, foot + d * L, up=-d, facing=n, length=L)
        else:
            sword(bone, nm, foot + d * L, up=-d, facing=n, length=L)


def practice_rack(bone, det, name, p0, p1, normal=(0, 0, 1), items=("staff", "wsword", "staff", "wsword", "staff"), h=1.25,
                  solid=True):
    """A floor rack of training weapons from ground point p0 to p1, its open side towards `normal`: two uprights on
    feet, a slotted top rail, a bottom trough; staves and wooden swords stand in it leaning back on the top rail."""
    p0, p1 = v3(*p0), v3(*p1)
    n = norm(v3(*normal))
    along = norm(p1 - p0)
    for k, p in enumerate((p0, p1)):
        beam(bone, "%s_up_%d" % (name, k), p, p + UP * h, 0.09, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
        beam(bone, "%s_foot_%d" % (name, k), p - n * 0.22 + UP * 0.04, p + n * 0.22 + UP * 0.04, 0.08, "wood_dark")
    beam(bone, name + "_rail", p0 + UP * (h - 0.12) - along * 0.05, p1 + UP * (h - 0.12) + along * 0.05, 0.08, "wood",
         width=0.1, extend=0.0)
    beam(bone, name + "_trough", p0 + UP * 0.14 + n * 0.12 - along * 0.05, p1 + UP * 0.14 + n * 0.12 + along * 0.05, 0.12,
         "wood", width=0.22)
    k = len(items)
    for i, it in enumerate(items):
        if it is None:
            continue
        t = (i + 0.5) / k
        base = p0 + (p1 - p0) * t + n * 0.14 + UP * 0.16
        rest = p0 + (p1 - p0) * t + n * 0.03 + UP * (h - 0.06)
        d = norm(rest - base)
        nm = "%s_%s_%d" % (name, it, i)
        if it == "staff":
            staff(det, nm, base, base + d * (h + 0.45))
        elif it == "wsword":
            wooden_sword(det, nm, base + d * 0.02, up=d, facing=n, length=h - 0.05)
        else:
            sword(det, nm, base + d * 0.02, up=d, facing=n, length=h - 0.05)
    if solid:
        lo, hi = np.minimum(p0, p1), np.maximum(p0, p1)
        collide((lo[0] - 0.1 - abs(n[0]) * 0.15, 0.0, lo[2] - 0.1 - abs(n[2]) * 0.15,
                 hi[0] + 0.1 + abs(n[0]) * 0.15, h, hi[2] + 0.1 + abs(n[2]) * 0.15))


def shield_rack(bone, det, name, p0, p1, normal=(0, 0, 1), n=3, h=0.95, r=0.3, faces=None, swords=True, solid=True):
    """A low rack of round shields from ground point p0 to p1, facing `normal`: two uprights, a top rail and a
    bottom rail; n round shields leaning back on the top rail, swords standing point down between them (swords)."""
    p0, p1 = v3(*p0), v3(*p1)
    nn = norm(v3(*normal))
    along = norm(p1 - p0)
    for k, p in enumerate((p0, p1)):
        beam(bone, "%s_up_%d" % (name, k), p, p + UP * h, 0.09, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
        beam(bone, "%s_foot_%d" % (name, k), p - nn * 0.25 + UP * 0.04, p + nn * 0.25 + UP * 0.04, 0.08, "wood_dark")
    for k, y in enumerate((0.2, h - 0.05)):
        beam(bone, "%s_rail_%d" % (name, k), p0 + UP * y - along * 0.06, p1 + UP * y + along * 0.06, 0.07, "wood", width=0.09)
    faces = faces or ["l_shield"]
    tilt = 0.28
    shield_n = norm(nn * math.cos(tilt) + UP * math.sin(tilt))
    for i in range(n):
        t = (i + 0.5) / n
        c = p0 + (p1 - p0) * t + nn * (0.06 + r * math.sin(tilt)) + UP * (0.04 + r * math.cos(tilt))
        round_shield(det, "%s_shield_%d" % (name, i), c, normal=shield_n, r=r, face=faces[i % len(faces)])
    if swords:
        for i in range(n - 1):
            t = (i + 1.0) / n
            b = p0 + (p1 - p0) * t - nn * 0.06 + UP * (h + 0.12)
            sword(det, "%s_sword_%d" % (name, i), b, up=(0, -1, 0), facing=nn, length=h + 0.05)
    if solid:
        lo, hi = np.minimum(p0, p1), np.maximum(p0, p1)
        collide((lo[0] - 0.08 - abs(nn[0]) * 0.25, 0.0, lo[2] - 0.08 - abs(nn[2]) * 0.25,
                 hi[0] + 0.08 + abs(nn[0]) * 0.25, h, hi[2] + 0.08 + abs(nn[2]) * 0.25))


# ================================================================ the wooden dummy
def wooden_dummy(bone, det, name, foot, yaw=0.0, scale=1.0, sword_pose="up", shield_face="l_shield", helmet_on=True,
                 solid=True, target=None):
    """A wooden training dummy (a blocky wooden man on a small plinth), facing +z turned by yaw (radians): feet, legs,
    hips, a boarded torso with a rope belt, broad shoulders, a head under an iron helmet; its RIGHT hand (at -x) holds a
    steel sword (sword_pose "up": raised upright before it, "low": held out forwards and down), its LEFT forearm (at +x)
    carries a round shield strapped on it, turned a little outwards. Everything joins: the grip runs through the
    fist, the shield's back touches the forearm. Returns the top of the helmet (world).

    target (1.19.0): a traininglib.Target ("shield_dummy") that receives the moving parts: its bone (pivot set here: the
    top of the plinth) gets the feet, legs, hips, torso and chest; "_head" (origin at the neck) the neck, head and
    helmet; "_arm_l" / "_arm_r" (origins at the shoulders) the arms; "_shield" (child of arm_l, origin at the grip on the
    back of the shield) the shield; "_sword" (child of arm_r, origin at the grip in the fist) the sword. The plinth stays
    in `bone`. The look at rest is unchanged."""
    R = ry(yaw)
    f = v3(*foot)
    s = scale
    if target is not None:
        target.set_pivot(f + R @ (v3(0.0, 0.08, 0.0) * s))
        body = bdet = target.bone
        hb = target.part("head", f + R @ (v3(0.0, 1.47, 0.0) * s))
        al = target.part("arm_l", f + R @ (v3(0.33, 1.38, 0.0) * s))
        ar = target.part("arm_r", f + R @ (v3(-0.33, 1.38, 0.0) * s))
        target.unhit.add("sword")
    else:
        body, bdet, hb, al, ar = bone, det, bone, bone, bone

    def L(p):
        return f + R @ (v3(*p) * s)

    def lb(nm, lo, hi, region, b=bone):
        lo, hi = v3(*lo) * s, v3(*hi) * s
        add_cube(b, "%s_%s" % (name, nm), f + R @ ((lo + hi) / 2), R, np.abs(hi - lo), region, stretch=True)

    def limb(nm, a, b_, d, region, b=bone):
        beam(b, "%s_%s" % (name, nm), L(a), L(b_), d * s, region, extend=d * s * 0.3)

    lb("plinth", (-0.34, 0.0, -0.26), (0.34, 0.08, 0.26), {"all": "wood_dark", "+2": "plank"})
    for sg, nm in ((-1, "r"), (1, "l")):
        lb("foot_" + nm, (sg * 0.12 - 0.08, 0.08, -0.1), (sg * 0.12 + 0.08, 0.18, 0.16), "l_dummy_dark", b=body)
        lb("leg_" + nm, (sg * 0.12 - 0.075, 0.18, -0.07), (sg * 0.12 + 0.075, 0.74, 0.07), "l_dummy", b=body)
    lb("hips", (-0.22, 0.72, -0.12), (0.22, 0.86, 0.12), "l_dummy_dark", b=body)
    lb("torso", (-0.22, 0.86, -0.13), (0.22, 1.36, 0.13), "l_dummy", b=body)
    lb("belt", (-0.235, 0.88, -0.145), (0.235, 0.94, 0.145), "rope", b=det if target is None else bdet)
    lb("chest", (-0.27, 1.26, -0.14), (0.27, 1.44, 0.14), "l_dummy", b=body)
    lb("neck", (-0.07, 1.44, -0.07), (0.07, 1.5, 0.07), "l_dummy_dark", b=hb)
    head_c = (0.0, 1.64, 0.0)
    lb("head", (-0.15, 1.5, -0.14), (0.15, 1.8, 0.14), "l_dummy", b=hb)
    if helmet_on:
        helmet(hb, name + "_helm", L((0.0, 1.66, 0.0)), R, s=0.3 * s)
    # the right arm: shoulder, elbow by the side, forearm forwards, the fist
    sh_r, el_r = (-0.33, 1.38, 0.0), (-0.35, 1.08, 0.04)
    if sword_pose == "low":
        fi_r = (-0.42, 1.04, 0.34)
    else:
        fi_r = (-0.35, 1.12, 0.32)
    limb("arm_r", sh_r, el_r, 0.13, "l_dummy", b=ar)
    limb("forearm_r", el_r, fi_r, 0.12, "l_dummy", b=ar)
    lb("fist_r", v3(*fi_r) - 0.07, v3(*fi_r) + 0.07, "l_dummy_dark", b=ar)
    lb("shoulder_r", (-0.4, 1.3, -0.1), (-0.26, 1.46, 0.1), "l_dummy_dark", b=ar)
    if sword_pose == "low":
        d = R @ norm(v3(-0.55, -0.35, 0.75))
    else:
        d = R @ norm(v3(0.0, 1.0, 0.12))
    grip_mid = L(fi_r)
    face = R @ v3(0, 0, 1) if sword_pose != "low" else R @ v3(0, 1, 0)
    swb = target.part("sword", grip_mid, parent="arm_r") if target is not None else bone
    sword(swb, name + "_sword", grip_mid - d * (0.15 * s), up=d, facing=face, length=0.95 * s)
    # the left arm: forearm forwards, the round shield strapped on it, turned a little outwards
    sh_l, el_l, fi_l = (0.33, 1.38, 0.0), (0.36, 1.06, 0.04), (0.37, 1.1, 0.2)
    limb("arm_l", sh_l, el_l, 0.13, "l_dummy", b=al)
    limb("forearm_l", el_l, fi_l, 0.12, "l_dummy", b=al)
    lb("fist_l", v3(*fi_l) - 0.07, v3(*fi_l) + 0.07, "l_dummy_dark", b=al)
    lb("shoulder_l", (0.26, 1.3, -0.1), (0.4, 1.46, 0.1), "l_dummy_dark", b=al)
    out = 0.42
    n_sh = R @ v3(math.sin(out), 0.0, math.cos(out))
    r_sh = 0.33 * s
    th = 0.045 * s
    # the fist grips the shield's back: the shield's back plane touches the front of the fist
    c_sh = L(fi_l) + n_sh * (0.1 * s + th / 2)
    shb = target.part("shield", L(fi_l) + n_sh * (0.1 * s), parent="arm_l") if target is not None else bone
    round_shield(shb, name + "_shield", c_sh, normal=n_sh, r=r_sh, face=shield_face, th=th)
    if solid:
        p0, p1 = L((-0.45, 0, -0.3)), L((0.62, 0, 0.62))
        lo, hi = np.minimum(p0, p1), np.maximum(p0, p1)
        q0, q1 = L((-0.45, 0, 0.62)), L((0.62, 0, -0.3))
        lo, hi = np.minimum(lo, np.minimum(q0, q1)), np.maximum(hi, np.maximum(q0, q1))
        collide((lo[0], 0.0, lo[2], hi[0], 1.9 * s, hi[2]))
    return L((0.0, 1.9, 0.0))


# ================================================================ stone, pots, gear
def stone_pillar(bone, det, name, foot, w=0.56, h=1.35, cap=True, courses=3):
    """A pillar of squared grey stones (courses slightly offset) with a flat cap; collides."""
    f = v3(*foot)
    ch = h / courses
    rng = random.Random(hash(name) & 0xffff)
    for k in range(courses):
        dx, dz = rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.02)
        ww = w * (1.0 if k % 2 == 0 else 0.96)
        add_cube(bone, "%s_%d" % (name, k), f + v3(dx, ch * (k + 0.5), dz), EYE, (ww, ch * 0.995, ww), {"all": "l_stone", "+2": "l_stone_top"},
                 stretch=True)
    if cap:
        add_cube(det, name + "_cap", f + UP * (h + 0.04), EYE, (w + 0.08, 0.08, w + 0.08), {"all": "l_stone_top"}, stretch=True)
    collide((f[0] - w / 2, 0.0, f[2] - w / 2, f[0] + w / 2, h + (0.08 if cap else 0.0), f[2] + w / 2))
    return h + (0.08 if cap else 0.0)


def flower_pot(bone, det, name, foot, pedestal=0.62, w=0.62, r=0.26, ph=0.62):
    """A stone pedestal (one squared stone block) carrying a round stone planter of pink flowers; collides."""
    f = v3(*foot)
    add_cube(bone, name + "_ped", f + UP * pedestal / 2, EYE, (w, pedestal, w), {"all": "l_stone", "+2": "l_stone_top"}, stretch=True)
    top = f + UP * pedestal
    ml.octo(bone, name + "_pot", top, r, 0.26, {"all": "stone", "+2": "soil"})
    add_cube(det, name + "_rim", top + UP * 0.25, EYE, (2 * r + 0.04, 0.05, 2 * r + 0.04), {"all": "l_stone_top", "+2": "soil"},
             stretch=True)
    for k, (yaw, sc) in enumerate(((0.0, 1.0), (math.pi / 8, 0.85))):
        ml.crossed(det, "%s_flowers_%d" % (name, k), top + UP * (0.26 + ph * sc / 2 - 0.03), 2 * r * 1.5 * sc, ph * sc, "l_flowers", yaw=yaw)
    collide((f[0] - w / 2, 0.0, f[2] - w / 2, f[0] + w / 2, pedestal + 0.3, f[2] + w / 2))


def jar(bone, name, foot, r=0.09, h=0.2):
    """A glazed ceramic jar (traininglib t_jar when the atlas has it, else props_m1 jar) with a linen cloth tied over
    its mouth."""
    p8.wb.jar(bone, name, foot, r=r, h=h, region="t_jar" if "t_jar" in ml.gg.REGIONS else "jar")


def folded_stack(bone, name, foot, regions, w=0.36, d=0.28, th=0.06, yaw=0.0):
    """A pile of folded cloths (flat boxes, each slightly turned on the one below); returns the top height."""
    f = v3(*foot)
    y = 0.0
    for k, reg in enumerate(regions):
        ml.rbox(bone, "%s_%d" % (name, k), f + UP * y, (w * (1 - 0.05 * k), th, d * (1 - 0.04 * k)), yaw + 0.08 * ((k % 3) - 1),
                {"all": reg}, stretch=True)
        y += th
    return f[1] + y


def mat_roll(bone, name, center, length, r=0.12, direction=(1, 0, 0), region="straw", ends="cloth_beige"):
    """A rolled mat / cushion lying along `direction` (an octagonal roll: two boxes turned 45 degrees about its axis)."""
    c, d = v3(*center), norm(v3(*direction))
    up = UP if abs(d[1]) < 0.9 else X
    side = norm(np.cross(up, d))
    up = np.cross(d, side)
    for k, a in enumerate((0.0, math.pi / 4)):
        u2 = up * math.cos(a) + side * math.sin(a)
        s2 = np.cross(d, u2)
        add_cube(bone, "%s_%d" % (name, k), c, np.column_stack([d, u2, s2]), (length, 2 * r * 0.83, 2 * r * 0.83),
                 {"all": region, "+1": ends, "-1": ends}, stretch=True)


def floor_knot(bone, name, center, size=1.3, y=0.0, frame=2.3, seam=0.05):
    """The red motif in the middle of the tatami floor (a cut-out decal just over the mats) inside a square of dark mat
    seams of side `frame` (lines from its corners to the floor's corners are left to the mats' own seams)."""
    c = v3(*center)
    if size > 0:
        add_cube(bone, name, c + UP * (y + 0.006), EYE, (size, 0.004, size), {"all": None, "+2": "l_knot"}, stretch=True, u_dir=X,
                 v_dir=Z)
    if frame:
        hf = frame / 2
        for k, (dx, dz, lx, lz) in enumerate(((0, -hf, frame, seam), (0, hf, frame, seam), (-hf, 0, seam, frame), (hf, 0, seam, frame))):
            add_cube(bone, "%s_seam_%d" % (name, k), c + v3(dx, y + 0.005, dz), EYE, (lx, 0.004, lz), {"all": None, "+2": "l_seam"},
                     stretch=True)


def lantern_gallows(bone, det, name, foot, h=3.0, arm=(0.6, 0.0, 0.0), d=0.32, size=0.36, solid=True):
    """A tall lantern post as on the pictures: a thick squared post with an iron cap, a wooden arm at the top towards
    `arm` with a diagonal brace, a big lantern hanging from the arm's end on a short chain (lit on export). The post
    collides. Returns the lantern's centre."""
    f, a = v3(*foot), v3(*arm)
    L = np.linalg.norm(a)
    ad = a / L
    top = f + UP * h
    ml.tl.post(bone, name + "_post", f, top, d=d, region="post", solid=solid)
    add_cube(det, name + "_cap", top + UP * 0.03, EYE, (d + 0.06, 0.08, d + 0.06), "iron")
    add_cube(det, name + "_band", top - UP * 0.45, EYE, (d + 0.03, 0.06, d + 0.03), "iron")
    y_arm = top - UP * 0.2
    beam(bone, name + "_arm", y_arm - ad * (d / 2 + 0.06), y_arm + a + ad * 0.08, 0.15,
         {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"}, width=0.13)
    beam(det, name + "_brace", f + UP * (h - 0.85) + ad * (d / 2 - 0.02), y_arm + a * 0.55 - UP * 0.06, 0.08, "wood_dark")
    tip = y_arm + a * 0.92 - UP * 0.08
    c = tip - UP * (0.2 + size * 0.65)
    ml.tl.lantern(bone, name + "_lamp", c, size=size, metal="black_iron", chain_to=tip)
    add_cube(det, name + "_hook", tip, EYE, (0.06, 0.06, 0.06), "black_iron")
    return c


def icon_tatami(path):
    """16x16 item icon of the tatami area: the striped red-and-beige awning at the back, the beige mats with their red
    border and the red knot in the middle, the fence in front, the red lotus banner on the left post."""
    from PIL import Image
    red, red_d = (164, 42, 36), (94, 20, 16)
    beige, mat, mat_d = (232, 220, 188), (216, 196, 142), (150, 126, 80)
    wood, wood_d = (124, 84, 48), (78, 52, 28)
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    for x in range(4, 13):          # the awning (stripes) and its posts
        p[x, 2] = (red if (x // 2) % 2 == 0 else beige) + (255,)
        p[x, 3] = (red if (x // 2) % 2 == 0 else beige) + (255,)
        if x % 2 == 0:
            p[x, 4] = (red if (x // 2) % 2 == 0 else beige) + (255,)
    for y in range(4, 8):
        p[4, y] = wood_d + (255,)
        p[12, y] = wood_d + (255,)
    for x in range(5, 12):
        p[x, 6] = (110, 76, 40, 255)
    for y in range(8, 15):          # the mats, the red border, the knot
        for x in range(1, 15):
            c = mat if (x + y) % 4 else mat_d
            if x in (1, 14) or y in (8, 14):
                c = red
            p[x, y] = c + (255,)
    for (x, y) in ((7, 10), (8, 10), (7, 11), (8, 11), (6, 11), (9, 10)):
        p[x, y] = red_d + (255,)
    for x in range(0, 16):          # the front fence
        p[x, 13] = wood + (255,)
    for x in (0, 5, 10, 15):
        for y in range(11, 16):
            p[x, y] = wood_d + (255,)
        p[x, 11] = (150, 152, 158, 255)
    for y in range(2, 9):           # the lotus banner on the left post
        p[0, y] = wood_d + (255,)
        for x in (1, 2, 3):
            if y < 8 or x == 2:
                p[x, y] = red + (255,)
    p[2, 4] = p[2, 5] = (232, 186, 70, 255)
    p[1, 5] = p[3, 5] = (232, 186, 70, 255)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
