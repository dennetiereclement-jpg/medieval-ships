"""Props of the baker's stall (1.17.0, agent B): tente_boulanger.

The gabled market stall of merchantlib.stall in brown and beige; this module adds the baker's own atlas regions
(painted into the free band of the tent's atlas with atlas.add, named "m8_..." plus a few shared ones of props_m1)
and the geometry of the goods: round loaves, long loaves, baguettes, buns and brioches, the stone bread oven with
its glowing mouth and chimney hood, open flour sacks with the wheat emblem, a sack of wheat ears, a basket of
baguettes, a wheat sheaf and a string of garlic hanging, the wooden bread peel, the cream counter cloth.

    import props_m8 as p8
    p8.add_regions(atlas)                        # before export
    p8.oven(props, det, cx, z_back, ...)         # the stone oven against the back wall
    p8.loaf_round(...), p8.loaf_long(...), p8.baguette(...), p8.bun(...), p8.flour_sack(...), p8.peel(...)

Coordinates: tent-local blocks (y up, +z = the open front). Cubes named "glow..." are drawn full bright.
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402
import props_m1 as p1  # noqa: E402
import props_m7 as p7  # noqa: E402

wb = p1.wb
v3, norm, add_cube, beam = ml.v3, ml.norm, ml.add_cube, ml.beam
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ry, rx, rz = ml.ry, ml.rx, ml.rz
_rgb, _mix, _jitter, _scale = ml._rgb, ml._mix, ml._jitter, ml._scale
CLEAR = (0, 0, 0, 0)
CRUST, CRUST_D, CRUST_L = _rgb("cc8a38"), _rgb("7a4618"), _rgb("f0c470")
WHEAT, WHEAT_D, WHEAT_L = _rgb("e2b048"), _rgb("9a6a1e"), _rgb("f6dc8a")


# ================================================================ painters (img = the region, w x h RGBA)
def _px(img):
    return img.load()


def _wheat_sprig(px, w, h, cx, y0, y1, col, dark, rng, lean=0.0):
    """A small wheat ear (stem + paired grains + awns) drawn from y0 (top) to y1 (stem foot) around column cx."""
    n = max(3, int((y1 - y0) * 0.45))
    for y in range(int(y0), int(y1)):
        x = int(round(cx + lean * (y1 - y)))
        if 0 <= x < w and 0 <= y < h:
            px[x, y] = _jitter(dark, rng, 6) + (255,)
    for k in range(n):
        y = int(y0 + 1 + k * 1.6)
        x = cx + lean * (y1 - y)
        for s in (-1, 1):
            for dx in (1, 2):
                X_ = int(round(x + s * dx))
                for dy in (0, 1):
                    if 0 <= X_ < w and 0 <= y + dy - (dx - 1) < h:
                        px[X_, y + dy - (dx - 1)] = _jitter(col, rng, 10) + (255,)
            X_ = int(round(x + s * 3))
            if 0 <= X_ < w and 0 <= y - 2 < h and k < n - 1:
                px[X_, y - 2] = _jitter(dark, rng, 6) + (255,)
    if 0 <= int(y0) - 1 < h:
        px[int(round(cx + lean * (y1 - y0))), int(y0) - 1] = _jitter(col, rng, 10) + (255,)


def _crust(seed, top=False):
    """Bread crust: golden brown, darker at the bottom of the sides, a few flour specks (top: lighter)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = _px(img)
        for y in range(h):
            for x in range(w):
                k = 1.08 - 0.28 * (y / h) if not top else 1.06 - 0.12 * abs(x / w - 0.5) - 0.12 * abs(y / h - 0.5)
                c = _scale(CRUST, k)
                if rng.random() < 0.04:
                    c = _rgb("efe2c4")
                px[x, y] = _jitter(c, rng, 7) + (255,)
    return p


def _loaf_top(seed, kind="cross"):
    """The top of a loaf: crust, a darker rim, light scored cuts (cross: a cross; diag: diagonal slashes; bun: a
    glossy egg-washed dome)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = _px(img)
        for y in range(h):
            for x in range(w):
                dx, dy = (x + 0.5) / w - 0.5, (y + 0.5) / h - 0.5
                d = math.hypot(dx, dy) * 2
                if kind == "bun":
                    c = _scale(_rgb("b8662a"), 1.18 - 0.4 * d)
                    if math.hypot(dx + 0.15, dy + 0.15) < 0.12:
                        c = _rgb("f0b070")
                else:
                    c = _scale(CRUST, 1.16 - 0.26 * d)
                    if d > 0.9:
                        c = _scale(CRUST, 0.86)
                    if kind == "cross" and 0.15 < d < 0.8 and (abs((x - w / 2 + 0.5) - (y - h / 2 + 0.5) * 0.4 - 3) < 0.8
                                                               or abs((x - w / 2 + 0.5) - (y - h / 2 + 0.5) * 0.4 + 2) < 0.8):
                        c = CRUST_L if (x + y) % 3 else _rgb("f4dca8")
                    if kind == "diag" and (x * 2 + y * 3) % 9 in (0, 1) and 0.1 < (x + 0.5) / w < 0.9:
                        c = CRUST_L
                    if rng.random() < 0.05:
                        c = _rgb("f2e6cc")
                px[x, y] = _jitter(c, rng, 6) + (255,)
    return p


def _stone(seed, base=_rgb("8a8680"), mortar=_rgb("5a5652"), rows=4, cols=2, soot=0.0):
    """Squared stone blocks in staggered courses (mortar lines), a little soot towards the top."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = _px(img)
        rh = h / rows
        shades = {}
        for y in range(h):
            r = int(y / rh)
            for x in range(w):
                off = (w / cols / 2) * (r % 2)
                c_ = int(((x + off) % w) / (w / cols))
                key = (r, c_)
                if key not in shades:
                    shades[key] = rng.uniform(0.86, 1.1)
                c = _scale(base, shades[key] * (1.0 - soot * (1 - y / h)))
                if y % int(rh) == 0 or int((x + off) % (w / cols)) == 0:
                    c = mortar
                px[x, y] = _jitter(c, rng, 7) + (255,)
    return p


def _fire(seed):
    """The oven's glowing inside: white-yellow at the bottom middle fading to orange and deep red at the vault, tongues
    of flame."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = _px(img)
        for y in range(h):
            for x in range(w):
                t = 1.0 - y / h                        # 0 at the bottom
                dx = abs((x + 0.5) / w - 0.5) * 2
                heat = (1 - t) * 0.8 + (1 - dx) * 0.35 + 0.15 * math.sin(x * 1.3 + rng.random()) * (1 - t)
                c = _mix(_rgb("8a1e08"), _rgb("ff8a1e"), min(1, max(0, heat)))
                if heat > 0.85:
                    c = _mix(_rgb("ff8a1e"), _rgb("fff0a0"), min(1, (heat - 0.85) * 3))
                px[x, y] = _jitter(c, rng, 10) + (255,)
    return p


def _embers(seed):
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = _px(img)
        for y in range(h):
            for x in range(w):
                c = _mix(_rgb("ffcf50"), _rgb("b0300c"), rng.random()) if rng.random() < 0.6 else _rgb("3a2a22")
                px[x, y] = _jitter(c, rng, 10) + (255,)
    return p


def _wheat_bunch(seed, n=11):
    """Cut-out wheat stalks fanning up from the bottom middle, heavy golden ears at the top."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = _px(img)
        for k in range(n):
            top_x = w * (0.12 + 0.76 * k / (n - 1)) + rng.uniform(-1, 1)
            foot_x = w / 2 + rng.uniform(-1.5, 1.5)
            top_y = rng.uniform(1, h * 0.12)
            ear = h * rng.uniform(0.3, 0.38)
            for y in range(int(top_y + ear * 0.6), h):
                t = (y - top_y) / (h - top_y)
                x = int(round(top_x + (foot_x - top_x) * t))
                if 0 <= x < w:
                    px[x, y] = _jitter(_mix(WHEAT_D, WHEAT, 0.5), rng, 8) + (255,)
            lean = (foot_x - top_x) / (h - top_y)
            _wheat_sprig(px, w, h, top_x, top_y, top_y + ear, WHEAT, WHEAT_D, rng, lean=-lean * 0.0)
        for y in range(int(h * 0.8), int(h * 0.86)):      # the band round the sheaf
            for x in range(int(w * 0.36), int(w * 0.64)):
                px[x, y] = _jitter(_rgb("8a5a2a"), rng, 6) + (255,)
    return p


def _garlic(seed):
    """Cut-out braided string of garlic bulbs: a braid down the middle, white bulbs with purple-grey streaks."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = _px(img)
        for y in range(h):
            x = int(w / 2 + math.sin(y * 0.8))
            for xx in (x, x + 1):
                if 0 <= xx < w:
                    px[xx, y] = _jitter(_rgb("a08a5a"), rng, 8) + (255,)
        bulbs = [(w * 0.5, h * 0.12), (w * 0.3, h * 0.3), (w * 0.7, h * 0.34), (w * 0.45, h * 0.5), (w * 0.28, h * 0.66),
                 (w * 0.68, h * 0.68), (w * 0.5, h * 0.84)]
        r = w * 0.2
        for (bx, by) in bulbs:
            for y in range(int(by - r * 1.2), int(by + r * 1.1)):
                for x in range(int(bx - r - 1), int(bx + r + 2)):
                    if not (0 <= x < w and 0 <= y < h):
                        continue
                    dy = (y - by) / (r * (1.15 if y < by else 1.0))
                    dx = (x - bx) / r
                    taper = 1.0 if dy > -0.3 else 1.0 + (dy + 0.3) * 1.4
                    if dx * dx + dy * dy <= 1.0 and abs(dx) <= max(0.15, taper):
                        c = _rgb("f2ece0") if (x - int(bx)) % 3 else _rgb("c8b8c8")
                        c = _scale(c, 1.0 - 0.18 * max(0, dx))
                        px[x, y] = _jitter(c, rng, 5) + (255,)
    return p


def _sack(seed, emblem=True):
    """Burlap (coarse weave) with a stitched seam, the brown wheat emblem in the middle of the face."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = _px(img)
        base = _rgb("c8ac78")
        for y in range(h):
            for x in range(w):
                c = _scale(base, 1.0 + 0.06 * ((x % 2) ^ (y % 2)) - 0.08 * (y / h))
                px[x, y] = _jitter(c, rng, 6) + (255,)
        if emblem:
            cx = w / 2
            _wheat_sprig(px, w, h, cx, h * 0.28, h * 0.78, _rgb("c87a2a"), _rgb("8a4a14"), rng)
            for s in (-1, 1):   # two leaves at the foot
                for k in range(4):
                    x, y = int(cx + s * (1 + k)), int(h * 0.7 - k * 0.7)
                    if 0 <= x < w:
                        px[x, y] = _jitter(_rgb("c87a2a"), rng, 6) + (255,)
    return p


def _grain(seed):
    """Pale golden grain heaped in an open sack (kernels with dark creases)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = _px(img)
        for y in range(h):
            for x in range(w):
                c = _rgb("e8cf8a") if (x + 2 * (y % 2)) % 3 else _rgb("b89048")
                d = math.hypot((x + 0.5) / w - 0.5, (y + 0.5) / h - 0.5) * 2
                px[x, y] = _jitter(_scale(c, 1.06 - 0.16 * d), rng, 10) + (255,)
    return p


def _cloth(seed):
    """The cream counter cloth hanging down the front: cream weave, gold side bands, dagged bottom edged in gold
    (cut-out), the orange-brown wheat sprig in the middle."""
    base = p7._runner(_rgb("eee2c4"), _rgb("d4c4a0"), _rgb("d9a93a"), None, seed)

    def p(img):
        base(img)
        rng = random.Random(seed + 1)
        w, h = img.size
        px = _px(img)
        cx = w / 2
        _wheat_sprig(px, w, h, cx, h * 0.12, h * 0.62, _rgb("c87a2a"), _rgb("8a4a14"), rng)
        for s in (-1, 1):
            for k in range(6):
                x, y = int(cx + s * (1 + k * 0.9)), int(h * 0.58 - k * 1.2)
                for dy in (0, 1):
                    if 0 <= x < w:
                        px[x, y + dy] = _jitter(_rgb("c87a2a"), rng, 6) + (255,)
    return p


def _tart(seed):
    """A berry tart seen from above: a golden pastry rim, red and dark blue berries heaped inside."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = _px(img)
        for y in range(h):
            for x in range(w):
                d = math.hypot((x + 0.5) / w - 0.5, (y + 0.5) / h - 0.5) * 2
                if d > 0.78:
                    c = _scale(CRUST_L, 1.0 - 0.1 * d)
                else:
                    c = rng.choice((_rgb("c42030"), _rgb("e03040"), _rgb("2a2a6a"), _rgb("3a3a8a"), _rgb("f0e6d8")))
                px[x, y] = _jitter(c, rng, 8) + (255,)
    return p


def _cake_side(seed):
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = _px(img)
        for y in range(h):
            for x in range(w):
                c = _rgb("f4ece0") if y < h * 0.35 + 1.5 * math.sin(x * 1.1) else _rgb("a8642a") if y % 5 else _rgb("f0e2c8")
                px[x, y] = _jitter(c, rng, 6) + (255,)
    return p


def _plain(c, seed, n=6):
    return p7._noise(_rgb(c), seed, n)


PAINTERS = {
    "m8_crust": (16, 16, _crust(801)),
    "m8_crust_top": (16, 16, _crust(802, top=True)),
    "m8_loaf_top": (16, 16, _loaf_top(803, "cross")),
    "m8_long_top": (32, 16, _loaf_top(804, "diag")),
    "m8_bun_top": (16, 16, _loaf_top(805, "bun")),
    "m8_stone": (32, 32, _stone(806, base=_rgb("7e7872"), mortar=_rgb("4c4844"))),
    "m8_stone_dark": (32, 32, _stone(807, base=_rgb("625e5a"), mortar=_rgb("3a3634"), soot=0.25)),
    "m8_stone_top": (16, 16, _plain("8e8a84", 808, 8)),
    "m8_fire": (32, 16, _fire(809)),
    "m8_embers": (16, 16, _embers(810)),
    "m8_soot": (16, 16, _plain("2e2826", 811, 6)),
    "m8_wheat": (24, 48, _wheat_bunch(812)),
    "m8_garlic": (16, 48, _garlic(813)),
    "m8_sack": (32, 32, _sack(814)),
    "m8_burlap": (16, 16, _sack(815, emblem=False)),
    "m8_grain": (16, 16, _grain(816)),
    "m8_cloth": (32, 48, _cloth(817)),
    "m8_cloth_top": (32, 32, p7._runner_top(_rgb("eee2c4"), _rgb("d9a93a"), 818)),
    "m8_tart": (16, 16, _tart(819)),
    "m8_cake_side": (16, 16, _cake_side(820)),
    "m8_icing": (16, 16, _plain("f6f0e6", 821, 4)),
    "m8_flour": (8, 8, _plain("f0ead8", 822, 5)),
}
REGIONS = list(PAINTERS) + ["jar", "jar_top", "linen", "iron_dark"]


def add_regions(atlas, names=None):
    """Adds the baker's regions (and the few borrowed from props_m1) to the tent's atlas."""
    for n in names or REGIONS:
        if n in atlas.regions and n not in atlas.painters:
            continue
        w, h, f = PAINTERS[n] if n in PAINTERS else p1.PAINTERS[n]
        atlas.add(n, w, h, f)


# ================================================================ geometry
def box(bone, name, lo, hi, region, yaw=0.0, stretch=True):
    return p7.box(bone, name, lo, hi, region, yaw=yaw, stretch=stretch)


def loaf_round(bone, name, foot, r=0.15, h=0.15, yaw=0.0, top="m8_loaf_top", dome=True):
    """A round loaf (boule): a low octagon of crust (two boxes) and a smaller dome on it, the scored top."""
    foot = v3(*foot)
    add_cube(bone, name, foot + UP * h * 0.26, ry(yaw), (2 * r, h * 0.52, 2 * r * 0.92), {"all": "m8_crust", "+2": "m8_crust_top"},
             stretch=True)
    add_cube(bone, name + "_o", foot + UP * h * 0.3, ry(yaw + math.pi / 4), (1.8 * r, h * 0.6, 1.8 * r),
             {"all": "m8_crust", "+2": "m8_crust_top"}, stretch=True)
    if dome:
        add_cube(bone, name + "_d", foot + UP * h * 0.6, ry(yaw + math.pi / 8), (1.45 * r, h * 0.8, 1.45 * r),
                 {"all": "m8_crust", "+2": top}, stretch=True)


def loaf_long(bone, name, foot, l=0.42, w=0.2, h=0.15, yaw=0.0):
    """A long loaf (batard): a rounded body and a narrower crown with diagonal slashes."""
    foot = v3(*foot)
    R = ry(yaw)
    add_cube(bone, name, foot + UP * h * 0.32, R, (l, h * 0.64, w), {"all": "m8_crust", "+2": "m8_long_top"}, stretch=True,
             u_dir=R[:, 0], v_dir=R[:, 2])
    add_cube(bone, name + "_c", foot + UP * h * 0.72, R, (l * 0.86, h * 0.36, w * 0.72), {"all": "m8_crust", "+2": "m8_long_top"},
             stretch=True, u_dir=R[:, 0], v_dir=R[:, 2])


def baguette(bone, name, a, b, r=0.055):
    """A baguette from a to b (any direction: lying or standing in a basket)."""
    a, b = v3(*a), v3(*b)
    d = norm(b - a)
    up = UP if abs(d[1]) < 0.9 else Z
    beam(bone, name, a, b, 2 * r, {"all": "m8_crust", "+2": "m8_long_top", "-2": "m8_long_top"}, width=2 * r * 0.9, up=up,
         extend=-0.005)


def bun(bone, name, foot, r=0.075, h=0.075, yaw=0.0):
    """A glossy bun / brioche (one squat box, the egg-washed top)."""
    foot = v3(*foot)
    add_cube(bone, name, foot + UP * h * 0.32, ry(yaw), (2 * r, h * 0.64, 2 * r), {"all": "m8_crust", "+2": "m8_bun_top"}, stretch=True)
    add_cube(bone, name + "_d", foot + UP * h * 0.6, ry(yaw + math.pi / 4), (1.45 * r, h * 0.8, 1.45 * r),
             {"all": "m8_crust", "+2": "m8_bun_top"}, stretch=True)


def bun_tray(bone, name, x0, x1, z0, z1, y, rng, r=0.07, rows=2, tray=True):
    """Buns in rows on a flat tray (or straight on a board)."""
    if tray:
        box(bone, name + "_tray", (x0, y, z0), (x1, y + 0.03, z1), "plank")
        y += 0.03
    nx = max(1, int((x1 - x0) / (2.25 * r)))
    for j in range(rows):
        z = z0 + (z1 - z0) * (j + 0.5) / rows
        for i in range(nx):
            x = x0 + (x1 - x0) * (i + 0.5) / nx + rng.uniform(-0.01, 0.01)
            bun(bone, "%s_%d_%d" % (name, j, i), (x, y, z), r=r, h=r * 1.05, yaw=rng.uniform(-0.4, 0.4))


def hook_rope(bone, name, top, drop=0.12):
    top = v3(*top)
    beam(bone, name, top, top - UP * drop, 0.025, "rope")
    return top - UP * drop


def garlic_string(bone, name, top, length=0.85, width=0.3):
    """A braided string of garlic bulbs hanging from `top`."""
    t = hook_rope(bone, name + "_rope", top, 0.1)
    wb.crossed(bone, name, t - UP * (length / 2), width, length, "m8_garlic", yaw=0.3)


def wheat_sheaf(bone, name, top, length=0.95, width=0.48, hanging=True):
    """A sheaf of wheat: hanging ears down from `top` (hanging=True), or standing with the ears up from its foot."""
    top = v3(*top)
    if hanging:
        t = hook_rope(bone, name + "_rope", top, 0.08)
        c = t - UP * (length / 2)
        for k, a in enumerate((0.35, 0.35 + math.pi / 2)):
            R = ry(a)
            add_cube(bone, "%s_%d" % (name, k), c, R, (width, length, 0.004), {"all": None, "+3": "m8_wheat", "-3": "m8_wheat"},
                     stretch=True, u_dir=R[:, 0], v_dir=UP)   # ears at the bottom
        add_cube(bone, name + "_tie", t - UP * 0.16, EYE, (0.1, 0.05, 0.1), "rope")
    else:
        wb.crossed(bone, name, top + UP * (length / 2), width, length, "m8_wheat", yaw=0.2)


def flour_sack(bone, name, foot, s=0.5, yaw=0.0, solid=True):
    """An open sack of grain: the bulging burlap body (the wheat emblem on its front), the rolled-down rim, the heap of
    grain showing in the mouth."""
    foot = v3(*foot)
    R = ry(yaw)
    # a cross of two boxes (a rounder plan): the wide one at the sides, the deep one carries the emblem at the front
    add_cube(bone, name, foot + UP * s * 0.4, R, (s, s * 0.8, s * 0.66), {"all": "m8_burlap"}, stretch=True)
    add_cube(bone, name + "_b", foot + UP * s * 0.43, R, (s * 0.74, s * 0.86, s * 0.9), {"all": "m8_burlap", "+3": "m8_sack"}, stretch=True)
    add_cube(bone, name + "_rim", foot + UP * s * 0.9, R @ ry(math.pi / 4), (s * 0.78, s * 0.13, s * 0.78),
             {"all": "m8_burlap", "+2": "m8_grain"}, stretch=True)
    add_cube(bone, name + "_heap", foot + UP * s * 0.98, R @ ry(0.4), (s * 0.6, s * 0.1, s * 0.56), {"all": "m8_grain"}, stretch=True)
    if solid:
        e = s * 0.55
        ml.collide((foot[0] - e, foot[1], foot[2] - e, foot[0] + e, foot[1] + s, foot[2] + e))


def wheat_sack(bone, name, foot, s=0.5, rng=None):
    """A sack (or tall basket) of wheat ears: an open burlap sack with a bundle of ears standing out of it."""
    foot = v3(*foot)
    flour_sack(bone, name, foot, s=s, solid=False)
    for k in range(2):
        q = foot + UP * (s * 0.92) + v3(0.05 * (k - 0.5), 0, 0.03 * k)
        wb.crossed(bone, "%s_ears_%d" % (name, k), q + UP * 0.28, s * 1.15, 0.56, "m8_wheat", yaw=0.25 + 0.6 * k)


def peel(bone, name, foot, top, blade=(0.3, 0.38)):
    """The baker's wooden peel: a long handle from `foot` up to `top` and the flat blade at the top."""
    foot, top = v3(*foot), v3(*top)
    d = norm(top - foot)
    beam(bone, name + "_handle", foot, top, 0.05, "wood", width=0.05)
    bw, bh = blade
    c = top + d * (bh / 2 - 0.02)
    side = norm(np.cross(d, Z)) if abs(d[2]) < 0.9 else X
    n = norm(np.cross(side, d))
    R = np.column_stack([side, d, n])
    add_cube(bone, name + "_blade", c, R, (bw, bh, 0.03), {"all": "plank"}, stretch=True)
    add_cube(bone, name + "_neck", top + d * 0.0, R, (bw * 0.45, 0.08, 0.035), "plank", stretch=True)


def oven(bone, det, cx, zb, rng, w=1.9, d=1.05, base_h=0.95, body_h=1.25, mouth=(0.86, 0.62), hood_top=4.0):
    """The stone bread oven against the back wall: a stone plinth, the oven body with its arched mouth (voussoirs
    round it) glowing inside with loaves on the hearth, a stone ledge before it, the stepped chimney hood narrowing up
    to a flue under the roof. Collides (plinth and body). Returns the mouth's centre (x, y, z) on the front face."""
    zf = zb + d
    x0, x1 = cx - w / 2, cx + w / 2
    yb = base_h
    yt = base_h + body_h
    mw, mh = mouth
    # plinth (a darker course at the top) and the ledge
    box(bone, "oven_plinth", (x0, 0.0, zb), (x1, yb - 0.1, zf), {"all": "m8_stone", "+2": "m8_stone_top"})
    box(bone, "oven_ledge", (x0 - 0.06, yb - 0.1, zb), (x1 + 0.06, yb, zf + 0.16), {"all": "m8_stone_top"})
    # the body around the mouth: two jambs, the stone above the arch (stepped round it), the back block
    mx0, mx1 = cx - mw / 2, cx + mw / 2
    r = mw / 2
    ha = r * 0.72                      # the arch's rise
    yc = yb + mh - ha                  # the springing line of the arch
    box(bone, "oven_jamb_l", (x0, yb, zf - 0.32), (mx0, yt, zf), "m8_stone")
    box(bone, "oven_jamb_r", (mx1, yb, zf - 0.32), (x1, yt, zf), "m8_stone")
    box(bone, "oven_crown", (mx0, yc + ha, zf - 0.32), (mx1, yt, zf), "m8_stone")
    for k, (t0, t1, f) in enumerate(((0.0, 0.5, 0.9), (0.5, 1.0, 0.62))):
        for j, s_ in enumerate((-1, 1)):
            xa, xb = (mx0, cx - f * r) if s_ < 0 else (cx + f * r, mx1)
            box(bone, "oven_step_%d_%d" % (k, j), (xa, yc + ha * t0, zf - 0.32), (xb, yc + ha * t1, zf), "m8_stone")
    box(bone, "oven_back", (x0, yb, zb), (x1, yt, zf - 0.32), {"all": "m8_stone", "+2": "m8_stone_top"})
    # the arch: voussoirs round the mouth (the keystone a little bigger)
    for k in range(9):
        a = math.pi * k / 8
        p = v3(cx + (r + 0.05) * math.cos(a), yc + (ha + 0.05) * math.sin(a), zf + 0.03)
        tang = math.atan2((ha + 0.05) * math.cos(a), -(r + 0.05) * math.sin(a))
        add_cube(bone, "oven_vous_%d" % k, p, rz(tang), (0.17, 0.12 if k != 4 else 0.17, 0.08), {"all": "m8_stone_dark"}, stretch=True)
    # the glowing inside: the fire at the back, embers on the hearth, the lit side walls
    box(bone, "glow_oven_fire", (mx0, yb, zf - 0.31), (mx1, yc + ha, zf - 0.29), {"all": "m8_fire"})
    box(bone, "glow_oven_hearth", (mx0 + 0.02, yb - 0.005, zf - 0.32), (mx1 - 0.02, yb + 0.02, zf - 0.02), {"all": "m8_embers"})
    for k, s_ in enumerate((-1, 1)):
        box(bone, "glow_oven_wall_%d" % k, (cx + s_ * (r - 0.02) - 0.01, yb, zf - 0.32), (cx + s_ * (r - 0.02) + 0.01, yc, zf - 0.02),
            {"all": "m8_fire"})
    # loaves baking inside (lit by the fire)
    for k, (dx, dz) in enumerate(((-0.24, -0.14), (0.0, -0.18), (0.24, -0.14), (-0.13, 0.02), (0.13, 0.02))):
        q = v3(cx + dx, yb + 0.02, zf - 0.16 + dz)
        add_cube(bone, "glow_oven_loaf_%d" % k, q + UP * 0.06, ry(0.2 * k), (0.2, 0.12, 0.14), {"all": "m8_crust", "+2": "m8_long_top"},
                 stretch=True)
    # the hood: stepped stone courses narrowing to a flue
    y = yt
    steps = ((w + 0.08, 0.3), (w * 0.82, 0.36), (w * 0.62, 0.4), (w * 0.44, 0.34))
    dz = d
    for k, (ww, hh) in enumerate(steps):
        dz = d * (1.0 - 0.14 * k) - 0.05
        box(bone, "oven_hood_%d" % k, (cx - ww / 2, y, zb), (cx + ww / 2, y + hh, zb + dz),
            {"all": "m8_stone_dark" if k else "m8_stone", "+2": "m8_stone_top"})
        y += hh
    fw = w * 0.32
    box(bone, "oven_flue", (cx - fw / 2, y, zb + 0.05), (cx + fw / 2, hood_top, zb + 0.05 + fw), {"all": "m8_stone_dark", "+2": "m8_soot"})
    box(det, "oven_flue_cap", (cx - fw / 2 - 0.04, hood_top - 0.12, zb + 0.01), (cx + fw / 2 + 0.04, hood_top, zb + 0.09 + fw), "m8_stone_top")
    ml.collide((x0 - 0.06, 0.0, zb, x1 + 0.06, yt + 1.5, zf + 0.16))
    return (cx, yb + mh / 2, zf)


def jar(bone, name, foot, r=0.12, h=0.26):
    """A stoneware jar with a cloth tied over its mouth (props_m1 regions)."""
    wb.jar(bone, name, foot, r=r, h=h)
