"""Props of the blacksmith's and the food merchant's tents (agent M2): tente_forgeron, tente_nourriture.

The shell (posts, roof, valance, flag, banners, lanterns, rug, counter, shelves) comes from merchantlib.pavilion; this
module adds what makes each tent: its own atlas regions (painted into the free band of the tent's atlas with
atlas.add, all named "m2_...") and the geometry of its goods.

    import props_m2 as pm
    pm.add_regions(atlas, "forge")      # or "food": paints the regions this tent needs
    pm.forge(bone, detail, ...)         # stone forge with a lit hearth
    pm.anvil_block(...), pm.sword_rack(...), pm.ingot_stack(...), pm.helmet(...)
    pm.cheese_wheel(...), pm.cheese_block(...), pm.bread(...), pm.ham(...), pm.produce_heap(...), pm.table_cloth(...)

Coordinates: tent-local blocks (y up, +z = the open front). Cubes named "glow..." are drawn full bright.
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, ".."), os.path.join(HERE, "..", "tents"), os.path.join(HERE, "..", "workshops")):
    if p not in sys.path:
        sys.path.insert(0, p)
import tentlib as tl  # noqa: E402
from galley_texture import _rgb, _jitter, _mix, _scale, hammered_iron, polished_metal, fine_wood  # noqa: E402
import ws_texture_a as wta  # noqa: E402
import ws_texture_b as wtb  # noqa: E402

gg = tl.gg
v3, norm, add_cube, beam = tl.v3, tl.norm, tl.add_cube, tl.beam
EYE, UP = tl.EYE, tl.UP
X, Z = v3(1, 0, 0), v3(0, 0, 1)
ry, rx, rz = gg.ry, gg.rx, gg.rz

# names of the shell's regions used by the props (merchantlib's atlas)
SH = {"wood": "wood", "wood_dark": "wood_dark", "plank": "plank", "iron": "iron", "gold": "gold", "rope": "rope",
      "crate": "crate", "barrel": "barrel"}


# ---------------------------------------------------------------- painters (img = the region, w x h RGBA)
def _P(fn, *a, **kw):
    def paint(img):
        seed = sum(ord(ch) * (i + 1) for i, ch in enumerate(fn.__name__)) + 7 * len(a) + 13 * len(kw)
        fn(img, (0, 0, img.size[0], img.size[1]), random.Random(seed), *a, **kw)
    return paint


def _px(img, x, y, c, a=255):
    img.load()[x, y] = tuple(int(max(0, min(255, k))) for k in c) + (a,)


def _stone(img, region, rng, base, mortar):
    wta._bricks(img, region, base, mortar, rng, row_h=(5, 8), brick_w=(7, 14))


def _ingot(img, region, rng, stops):
    polished_metal(img, region, stops, rng, fx=0.6, fy=0.5)
    u, v, w, h = region
    for x in range(w):
        _px(img, u + x, v, _ramp(stops, 0.95))
        _px(img, u + x, v + h - 1, _ramp(stops, 0.1))
    for y in range(h):
        _px(img, u, v + y, _ramp(stops, 0.8))
        _px(img, u + w - 1, v + y, _ramp(stops, 0.15))


def _ramp(stops, t):
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            return _mix(c0, c1, (t - t0) / max(1e-6, t1 - t0))
    return stops[-1][1]


STEEL = [(0.0, (70, 74, 82)), (0.35, (120, 126, 136)), (0.7, (176, 182, 190)), (1.0, (232, 236, 240))]
IRON = [(0.0, (90, 92, 98)), (0.4, (150, 152, 158)), (0.8, (200, 202, 206)), (1.0, (238, 238, 240))]
GOLD = [(0.0, (120, 82, 24)), (0.35, (190, 140, 44)), (0.7, (236, 196, 90)), (1.0, (255, 240, 180))]


def _hiron(img, region, rng, base):
    hammered_iron(img, region, base, rng)


def _pmetal(img, region, rng, stops):
    polished_metal(img, region, stops, rng)


def _blade(img, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            t = 0.25 + 0.7 * (1 - abs(x - (w - 1) / 2) / ((w - 1) / 2 + 0.01))
            c = _ramp(STEEL, t)
            if x == w // 2:
                c = _scale(c, 0.85)   # the fuller
            _px(img, u + x, v + y, _jitter(c, rng, 3))


def _leather(img, region, rng, base=_rgb("5a3a22")):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            k = 1.0 + 0.08 * math.sin(x * 0.9 + y * 2.3)
            if y % 4 == 3:
                k -= 0.2   # the wrapping
            _px(img, u + x, v + y, _jitter(_scale(base, k), rng, 5))


def _cheese_side(img, region, rng):
    """Wax rind of a cheese wheel: warm yellow, lighter on top, a darker band at the bottom."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            t = y / (h - 1)
            c = _mix(_rgb("f4d064"), _rgb("c8962a"), t ** 1.4)
            if y == 0:
                c = _rgb("f8e08a")
            _px(img, u + x, v + y, _jitter(c, rng, 4))


def _cheese_top(img, region, rng):
    u, v, w, h = region
    cx, cy = (w - 1) / 2, (h - 1) / 2
    for y in range(h):
        for x in range(w):
            d = max(abs(x - cx), abs(y - cy)) / (w / 2)
            c = _rgb("f0cc5c") if d < 0.78 else _rgb("d8a83c")
            if 0.55 < d < 0.62:
                c = _rgb("e2b84a")
            _px(img, u + x, v + y, _jitter(c, rng, 4))


def _cheese_cut(img, region, rng):
    """Cut cheese (pale yellow, round holes): the cheese blocks and the wedges' cut faces."""
    u, v, w, h = region
    holes = [(rng.uniform(1, w - 2), rng.uniform(1, h - 2), rng.uniform(0.8, 1.7)) for _ in range(max(3, w * h // 40))]
    for y in range(h):
        for x in range(w):
            c = _rgb("f6dc7a")
            for hx, hy, r in holes:
                d = math.hypot(x + 0.5 - hx, y + 0.5 - hy)
                if d < r:
                    c = _rgb("d4aa44") if (y + 0.5 - hy) < 0 else _rgb("e6c25c")
            if x in (0, w - 1) or y in (0, h - 1):
                c = _scale(c, 0.9)
            _px(img, u + x, v + y, _jitter(c, rng, 3))


def _ham(img, region, rng):
    """Cured ham (stretched on the whole body): glazed brown-red skin, pink lighter at the middle, string lines."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            d = abs(x - (w - 1) / 2) / (w / 2)
            c = _mix(_rgb("e08a76"), _rgb("9a3a2a"), d ** 1.5)
            c = _mix(c, _rgb("b4542e"), 0.25 * (y / h))
            if (x + y) % 6 == 0 or (x - y) % 6 == 0:
                c = _mix(c, _rgb("e8d0a0"), 0.3)  # the netting string
            _px(img, u + x, v + y, _jitter(c, rng, 5))


def _ham_cut(img, region, rng):
    u, v, w, h = region
    cx, cy = (w - 1) / 2, (h - 1) / 2
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - cy) / (w / 2)
            c = _rgb("d65a5a") if d < 0.75 else _rgb("f2dcc8") if d < 0.9 else _rgb("9a3a2a")
            if d < 0.15:
                c = _rgb("f4ecd8")   # the bone
            _px(img, u + x, v + y, _jitter(c, rng, 5))


def _round_heap(img, region, rng, colours, leaf=None, gap=_rgb("3a2414"), r=(1.6, 2.4)):
    """A heap of round fruit seen from above: overlapping shaded discs on a dark gap."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            _px(img, u + x, v + y, gap)
    pts = []
    for _ in range(int(w * h / 7)):
        pts.append((rng.uniform(0, w), rng.uniform(0, h), rng.uniform(*r), rng.choice(colours)))
    for cx, cy, rad, col in pts:
        for y in range(int(cy - rad - 1), int(cy + rad + 2)):
            for x in range(int(cx - rad - 1), int(cx + rad + 2)):
                if 0 <= x < w and 0 <= y < h:
                    d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                    if d < rad:
                        k = 1.15 - 0.45 * (d / rad) + 0.18 * ((cx - x) + (cy - y)) / rad / 2
                        c = _scale(col, k)
                        if d < rad * 0.3 and (x + 0.5 - cx) < 0 and (y + 0.5 - cy) < 0:
                            c = _mix(c, (255, 255, 255), 0.35)
                        _px(img, u + x, v + y, _jitter(c, rng, 4))
        if leaf is not None and rng.random() < 0.6:
            xi, yi = int(cx), int(cy - rad * 0.6)
            if 0 <= xi < w and 0 <= yi < h:
                _px(img, u + xi, v + yi, leaf)


def _greens(img, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            n = math.sin(x * 1.3 + y * 0.4) * math.cos(y * 1.1 - x * 0.7) + rng.uniform(-0.3, 0.3)
            c = _rgb("8ec84a") if n > 0.5 else _rgb("5e9a30") if n > -0.2 else _rgb("3e6e22")
            _px(img, u + x, v + y, _jitter(c, rng, 6))


def _tablecloth(img, region, rng):
    """The ochre cloth of the presentation table, stretched on its hanging front: a gold border, a darker diamond
    pattern, a row of tassels at the bottom (transparent between them)."""
    u, v, w, h = region
    tas = 4
    for y in range(h):
        for x in range(w):
            c = _rgb("d4a030")
            if (x + y) % 8 == 0 or (x - y) % 8 == 0:
                c = _rgb("b8841e")
            if y < 2 or x < 2 or x >= w - 2 or (h - tas - 3 <= y < h - tas - 1):
                c = _rgb("f2d070")
            if y >= h - tas:
                if x % 4 == 1 or (x % 4 in (0, 2) and y < h - 1):
                    c = _rgb("e8b848")
                else:
                    _px(img, u + x, v + y, (0, 0, 0), 0)
                    continue
            _px(img, u + x, v + y, _jitter(c, rng, 4))


def _cloth_top(img, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _rgb("d8a634")
            if x < 1 or y < 1 or x >= w - 1 or y >= h - 1:
                c = _rgb("f2d070")
            _px(img, u + x, v + y, _jitter(c, rng, 4))


def _wicker(img, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            over = ((x // 2) + (y // 2)) % 2 == 0
            c = _rgb("c49a58") if over else _rgb("8e6834")
            if y in (0, h - 1):
                c = _rgb("7a5426")
            _px(img, u + x, v + y, _jitter(c, rng, 5))


def _burlap(img, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _rgb("b89a6a")
            if (x + y) % 2 == 0:
                c = _scale(c, 0.92)
            if y in (2, 3) and x % 3 != 0:
                c = _rgb("8a6a3a")
            _px(img, u + x, v + y, _jitter(c, rng, 5))


def _terracotta(img, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _rgb("b4643a")
            if y < 3:
                c = _rgb("c87a4a")
            _px(img, u + x, v + y, _jitter(c, rng, 5))


def _sausage(img, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _rgb("8a3424") if (x + y * 3) % 5 else _rgb("d8b890")
            _px(img, u + x, v + y, _jitter(c, rng, 5))


def _soot_stone(img, region, rng):
    _stone(img, region, rng, _rgb("5c5a58"), _rgb("2a2826"))


def _anvil_stone(img, region, rng):
    _stone(img, region, rng, _rgb("8c8c88"), _rgb("4c4c4a"))


def _forge_stone(img, region, rng):
    _stone(img, region, rng, _rgb("7a746c"), _rgb("3e3a36"))


REGION_SETS = {
    "forge": [
        ("m2_stone", 32, 32, _P(_forge_stone)),
        ("m2_stone_dark", 32, 32, _P(_soot_stone)),
        ("m2_anvil_stone", 32, 32, _P(_anvil_stone)),
        ("m2_stone_top", 16, 16, _P(wtb._slab)),
        ("m2_fire_back", 16, 16, _P(wta._fire_back)),
        ("m2_embers", 16, 16, _P(wta._embers)),
        ("m2_fire", 32, 32, _P(wta._fire)),
        ("m2_coal", 16, 16, _P(wta._coal)),
        ("m2_black_iron", 16, 16, _P(_hiron, _rgb("34343a"))),
        ("m2_anvil_iron", 16, 16, _P(_hiron, _rgb("6a6a70"))),
        ("m2_steel", 16, 16, _P(_pmetal, STEEL)),
        ("m2_ingot", 16, 8, _P(_ingot, IRON)),
        ("m2_ingot_gold", 16, 8, _P(_ingot, GOLD)),
        ("m2_blade", 8, 16, _P(_blade)),
        ("m2_leather", 8, 16, _P(_leather)),
        ("m2_red_hot", 8, 8, lambda img: [img.putpixel((x, y), (255, 120 + 10 * ((x + y) % 4), 40, 255)) for x in range(8) for y in range(8)]),
    ],
    "food": [
        ("m2_cheese", 16, 16, _P(_cheese_side)),
        ("m2_cheese_top", 16, 16, _P(_cheese_top)),
        ("m2_cheese_cut", 16, 16, _P(_cheese_cut)),
        ("m2_bread", 16, 8, _P(wtb._bread)),
        ("m2_bread_top", 16, 8, _P(wtb._bread, top=True)),
        ("m2_ham", 16, 16, _P(_ham)),
        ("m2_ham_cut", 8, 8, _P(_ham_cut)),
        ("m2_sausage", 8, 8, _P(_sausage)),
        ("m2_apples", 16, 16, _P(_round_heap, [_rgb("c82a1e"), _rgb("b01e18"), _rgb("d84a20"), _rgb("9ab830")], _rgb("4a6a1e"))),
        ("m2_tomatoes", 16, 16, _P(_round_heap, [_rgb("e0381e"), _rgb("d02818"), _rgb("e85a24")], _rgb("3e7a22"))),
        ("m2_oranges", 16, 16, _P(_round_heap, [_rgb("f09a26"), _rgb("e8b030"), _rgb("d87a1e")], _rgb("4a6a1e"))),
        ("m2_greens", 16, 16, _P(_greens)),
        ("m2_tablecloth", 32, 32, _P(_tablecloth)),
        ("m2_cloth_top", 16, 16, _P(_cloth_top)),
        ("m2_wicker", 16, 16, _P(_wicker)),
        ("m2_burlap", 16, 16, _P(_burlap)),
        ("m2_terracotta", 16, 8, _P(_terracotta)),
        ("m2_ivy", 16, 32, _P(wtb._ivy, dense=0.7)),
        ("m2_jar", 16, 16, _P(wtb._jar)),
        ("m2_jar_top", 16, 16, _P(wtb._jar, top=True)),
    ],
}


def add_regions(atlas, which):
    for name, w, h, painter in REGION_SETS[which]:
        atlas.add(name, w, h, painter)


# ---------------------------------------------------------------- generic small shapes
def box(bone, name, lo, hi, region, yaw=0.0, stretch=False):
    lo, hi = v3(*lo), v3(*hi)
    return add_cube(bone, name, (lo + hi) / 2, ry(yaw), np.abs(hi - lo), region, stretch=stretch)


def octo(bone, name, foot, r, h, region, k=0.83, yaw=0.0, **kw):
    """Round-ish upright body (two boxes, the second turned 45 degrees)."""
    foot = v3(*foot)
    c = foot + UP * h / 2
    add_cube(bone, name, c, ry(yaw), (2 * r, h, 2 * r), region, **kw)
    add_cube(bone, name + "_r", c, ry(yaw + math.pi / 4), (2 * r * k, h * 0.998, 2 * r * k), region, **kw)


def plate(bone, name, center, w, h, region, normal=(0, 0, 1), up=(0, 1, 0), th=0.02, edge=None):
    n = norm(v3(*normal))
    upv = v3(*up)
    upv = norm(upv - np.dot(upv, n) * n)
    side = np.cross(upv, n)
    return add_cube(bone, name, center, np.column_stack([side, upv, n]), (w, h, th),
                    {"all": edge, "+3": region, "-3": region}, stretch=True, u_dir=side, v_dir=-upv)


# ---------------------------------------------------------------- the blacksmith
def forge(bone, detail, cx, z_back, w=1.7, d=1.05, collide=True):
    """A stone forge against the back wall, its mouth to +z: a plinth, two cheeks and the back of the hearth, a bed
    of glowing embers and flames (full bright), a stepped arch, a cornice and a hood narrowing to a short chimney
    (under the eaves). cx = centre x, z_back = its back face."""
    x0, x1, z0, z1 = cx - w / 2, cx + w / 2, z_back, z_back + d
    hy, ty = 0.55, 1.3          # hearth floor, top of the mouth
    box(bone, "forge_plinth", (x0 - 0.05, 0, z0), (x1 + 0.05, 0.12, z1 + 0.06), {"all": "m2_stone_top"})
    box(bone, "forge_base", (x0, 0.12, z0), (x1, hy, z1), {"all": "m2_stone", "+2": "m2_stone_top"})
    cheek = 0.36
    box(bone, "forge_cheek_l", (x0, hy, z0), (x0 + cheek, ty, z1), {"all": "m2_stone", "+1": "m2_fire_back"})
    box(bone, "forge_cheek_r", (x1 - cheek, hy, z0), (x1, ty, z1), {"all": "m2_stone", "-1": "m2_fire_back"})
    box(bone, "forge_back", (x0 + cheek, hy, z0), (x1 - cheek, ty, z0 + 0.3), {"all": "m2_stone", "+3": "m2_fire_back"})
    box(bone, "forge_hearth", (x0 + cheek, hy, z0 + 0.3), (x1 - cheek, hy + 0.06, z1), {"all": "m2_stone", "+2": "m2_coal"})
    box(bone, "glow_forge_embers", (x0 + cheek + 0.04, hy + 0.06, z0 + 0.34), (x1 - cheek - 0.04, hy + 0.11, z1 - 0.12), "m2_embers",
        stretch=True)
    box(bone, "glow_forge_heap", (cx - 0.28, hy + 0.1, z0 + 0.42), (cx + 0.26, hy + 0.17, z1 - 0.3), "m2_embers", stretch=True)
    fw = w - 2 * cheek - 0.12
    for k, (dz, hh) in enumerate(((0.45, 0.5), (0.62, 0.42), (0.78, 0.32))):
        plate(bone, "glow_forge_fire_%d" % k, (cx + (k - 1) * 0.04, hy + 0.1 + hh / 2, z0 + dz), fw * (1 - 0.15 * k), hh, "m2_fire",
              th=0.01)
    plate(bone, "glow_forge_fire_x", (cx, hy + 0.1 + 0.2, z0 + 0.6), 0.5, 0.4, "m2_fire", normal=(1, 0, 0), th=0.01)
    # the stepped arch over the mouth, the lintel and the cornice
    for s in (1, -1):
        xa = cx + s * (w / 2 - cheek)
        box(detail, "forge_arch_%d" % s, (min(xa, xa - s * 0.16), ty - 0.16, z1 - 0.32), (max(xa, xa - s * 0.16), ty, z1), "m2_stone")
        box(detail, "forge_arch2_%d" % s, (min(xa - s * 0.16, xa - s * 0.26), ty - 0.08, z1 - 0.32), (max(xa - s * 0.16, xa - s * 0.26), ty, z1),
            "m2_stone")
    box(bone, "forge_lintel", (x0, ty, z0), (x1, ty + 0.38, z1), {"all": "m2_stone"})
    box(bone, "forge_cornice", (x0 - 0.08, ty + 0.38, z0), (x1 + 0.08, ty + 0.48, z1 + 0.08), {"all": "m2_stone_top"})
    steps, y = 5, ty + 0.48
    for k in range(steps):
        t = (k + 1) / steps
        hx = w / 2 - (w / 2 - 0.32) * t
        zz1 = z1 - (d - 0.62) * t
        box(bone, "forge_hood_%d" % k, (cx - hx, y, z0), (cx + hx, y + 0.17, zz1), {"all": "m2_stone_dark"})
        y += 0.17
    box(bone, "forge_chimney", (cx - 0.3, y, z0), (cx + 0.3, y + 0.55, z0 + 0.6), "m2_stone_dark")
    box(bone, "forge_chimney_cap", (cx - 0.36, y + 0.55, z0 - 0.02), (cx + 0.36, y + 0.65, z0 + 0.66), {"all": "m2_stone_top"})
    # a bellows on the left, a poker and tongs on the ledge
    bel = v3(x0 - 0.25, hy - 0.05, z0 + 0.55)
    add_cube(detail, "forge_bellows_a", bel + UP * 0.02, EYE, (0.34, 0.04, 0.55), SH["wood_dark"])
    add_cube(detail, "forge_bellows_l", bel + UP * 0.1, EYE, (0.3, 0.12, 0.5), "m2_leather")
    add_cube(detail, "forge_bellows_b", bel + UP * 0.18, rx(0.12), (0.34, 0.04, 0.55), SH["wood_dark"])
    beam(detail, "forge_bellows_nozzle", bel + UP * 0.1 - Z * 0.3, v3(x0 + 0.02, hy + 0.12, z0 + 0.3), 0.05, SH["iron"])
    beam(detail, "forge_poker", v3(x1 - 0.1, hy + 0.02, z1 + 0.02), v3(cx + 0.1, hy + 0.12, z0 + 0.6), 0.03, SH["iron"])
    if collide:
        tl.collide((x0 - 0.05, 0, z0, x1 + 0.05, ty + 0.48, z1 + 0.06))
        tl.collide((cx - 0.5, ty + 0.48, z0, cx + 0.5, y + 0.65, z0 + 0.66))
    return y + 0.65


def anvil(bone, name, foot, yaw=0.0, s=1.0, detail=None):
    """A black iron anvil (the workshops' anvil with this atlas): stepped foot, waist, face with heel and horn (+x)."""
    foot = v3(*foot)
    R = ry(yaw)

    def b(nm, c, size, reg="m2_anvil_iron", bn=None):
        add_cube(bn or bone, "%s_%s" % (name, nm), foot + R @ (v3(*c) * s), R, v3(*size) * s,
                 {"all": reg, "+2": "m2_steel"} if nm == "face" else reg)
    b("base", (0, 0.06, 0), (0.62, 0.12, 0.44))
    b("base2", (0, 0.16, 0), (0.48, 0.09, 0.34))
    b("waist", (0, 0.29, 0), (0.28, 0.18, 0.24))
    b("neck", (0, 0.41, 0), (0.42, 0.07, 0.3))
    b("face", (-0.04, 0.5, 0), (0.62, 0.12, 0.34))
    b("heel", (-0.38, 0.5, 0), (0.14, 0.1, 0.26))
    b("horn_0", (0.34, 0.5, 0), (0.12, 0.1, 0.24))
    b("horn_1", (0.45, 0.505, 0), (0.12, 0.08, 0.17))
    b("horn_2", (0.55, 0.515, 0), (0.1, 0.06, 0.1))
    b("horn_3", (0.62, 0.52, 0), (0.07, 0.04, 0.05))
    b("hardy", (-0.25, 0.565, 0.0), (0.05, 0.02, 0.05), "m2_steel", bn=detail)


def anvil_block(bone, detail, foot, yaw=0.0, s=1.55, block=(1.05, 0.62, 0.8)):
    """The big anvil of the picture on its block of stone (two courses, a slab top), hammer and tongs on it."""
    foot = v3(*foot)
    bw, bh, bd = block
    box(bone, "anvil_stone_0", foot + v3(-bw / 2, 0, -bd / 2), foot + v3(bw / 2, bh * 0.55, bd / 2), {"all": "m2_anvil_stone"}, yaw=0)
    box(bone, "anvil_stone_1", foot + v3(-bw / 2 + 0.05, bh * 0.55, -bd / 2 + 0.05), foot + v3(bw / 2 - 0.05, bh, bd / 2 - 0.05),
        {"all": "m2_anvil_stone", "+2": "m2_stone_top"})
    top = foot + UP * bh
    anvil(bone, "anvil", top, yaw=yaw, s=s, detail=detail)
    face_y = top[1] + 0.56 * s
    R = ry(yaw)
    # a hammer lying across the face, tongs leaning on the block
    h0 = top + R @ v3(-0.25 * s, 0.56 * s + 0.02, 0.1 * s)
    beam(detail, "anvil_hammer_handle", h0, h0 + R @ v3(0.05, 0, 0.42), 0.04, SH["wood"])
    beam(detail, "anvil_hammer_head", h0 + R @ v3(-0.08, 0.04, 0.42), h0 + R @ v3(0.12, 0.04, 0.42), 0.08, "m2_black_iron")
    t0 = foot + R @ v3(bw / 2 + 0.03, 0.0, 0.15)
    beam(detail, "anvil_tongs_a", t0, t0 + v3(-0.04, 0.55, -0.06), 0.025, SH["iron"])
    beam(detail, "anvil_tongs_b", t0 + v3(0, 0, 0.06), t0 + v3(-0.04, 0.55, 0.0), 0.025, SH["iron"])
    tl.collide((foot[0] - bw / 2, foot[1], foot[2] - bd / 2, foot[0] + bw / 2, face_y, foot[2] + bd / 2))
    return face_y


def sword(bone, name, tip, up=(0, 1, 0), length=0.95, facing=(0, 0, 1), blade="m2_blade", guard=None, grip="m2_leather"):
    """A sword standing point down: tip at `tip`, the hilt above along `up`; the flat of the blade faces `facing`."""
    tip, u = v3(*tip), norm(v3(*up))
    f = norm(v3(*facing))
    side = norm(np.cross(u, f))
    lb = length * 0.72
    beam(bone, name + "_blade", tip, tip + u * lb, 0.02, blade, width=0.075, up=f)
    gd = tip + u * lb
    beam(bone, name + "_guard", gd - side * 0.13, gd + side * 0.13, 0.04, guard or SH["iron"], width=0.04, up=u)
    beam(bone, name + "_grip", gd, gd + u * length * 0.2, 0.04, grip)
    add_cube(bone, name + "_pommel", gd + u * (length * 0.2 + 0.03), EYE, (0.06, 0.06, 0.06), guard or SH["gold"])


def axe(bone, name, foot, up=(0, 1, 0), length=0.9, facing=(0, 0, 1)):
    """A long axe standing on its haft end, the head at the top facing sideways."""
    foot, u = v3(*foot), norm(v3(*up))
    f = norm(v3(*facing))
    side = norm(np.cross(u, f))
    beam(bone, name + "_haft", foot, foot + u * length, 0.045, SH["wood_dark"])
    hd = foot + u * (length - 0.12)
    add_cube(bone, name + "_head", hd + side * 0.1, np.column_stack([side, u, f]), (0.2, 0.2, 0.03), "m2_steel", stretch=True)


def sword_rack(bone, detail, p0, p1, y0=0.0, facing=(0, 0, 1), n=5, kinds=None, h=1.45, tag="r"):
    """A wall rack from ground point p0 to p1 (the rack faces `facing`): two uprights, two rails, n swords (and
    axes) standing point down along it."""
    p0, p1, f = v3(*p0), v3(*p1), norm(v3(*facing))
    p0[1] = p1[1] = y0
    back = -f * 0.08
    d = norm(p1 - p0)
    for k, p in enumerate((p0, p1)):
        beam(bone, "rack_%s_upright_%d" % (tag, k), p + back, p + back + UP * h, 0.08, SH["wood_dark"])
    for k, y in enumerate((0.35, 1.05)):
        beam(bone, "rack_%s_rail_%d" % (tag, k), p0 - d * 0.05 + back * 0.4 + UP * y, p1 + d * 0.05 + back * 0.4 + UP * y, 0.06,
             SH["wood"], width=0.08, up=f)
    kinds = kinds or ["sword"]
    for k in range(n):
        p = p0 + (p1 - p0) * (k + 0.5) / n + f * 0.03
        kind = kinds[k % len(kinds)]
        if kind == "axe":
            axe(detail, "rack_%s_axe_%d" % (tag, k), p + UP * 0.06, length=1.2, facing=f)
        else:
            sword(detail, "rack_%s_sword_%d" % (tag, k), p + UP * 0.1, length=1.15, facing=f, guard=SH["gold"] if k % 2 else SH["iron"])
    return h


def ingot_stack(bone, name, foot, layers=3, yaw=0.0, region="m2_ingot", per=3, s=1.0):
    """Ingots stacked crosswise (each layer turned 90 degrees, one fewer per layer); s scales them."""
    foot = v3(*foot)
    for j in range(layers):
        m = max(1, per - j)
        R = ry(yaw + (math.pi / 2 if j % 2 else 0.0))
        for i in range(m):
            off = (i - (m - 1) / 2) * 0.1 * s
            c = foot + UP * (0.025 + j * 0.05) * s + R @ v3(0, 0, off)
            add_cube(bone, "%s_%d_%d" % (name, j, i), c, R, (0.2 * s, 0.05 * s, 0.085 * s), region, stretch=True)


def helmet(bone, name, foot, yaw=0.0, s=1.0, region="m2_steel", crest=None):
    """A small great-helm on a shelf: the bucket, the dome, the eye slit band and the nose guard."""
    foot = v3(*foot)
    R = ry(yaw)
    add_cube(bone, name, foot + UP * 0.1 * s, R, v3(0.22, 0.2, 0.22) * s, region)
    add_cube(bone, name + "_dome", foot + UP * 0.225 * s, R, v3(0.18, 0.05, 0.18) * s, region)
    add_cube(bone, name + "_slit", foot + UP * 0.13 * s + R @ v3(0, 0, 0.112 * s), R, v3(0.17, 0.025, 0.01) * s, "m2_black_iron")
    if crest:
        add_cube(bone, name + "_crest", foot + UP * 0.27 * s, R, v3(0.03, 0.05, 0.16) * s, crest)


def shield(bone, name, center, normal=(0, 0, 1), w=0.5, h=0.62, face="m2_steel", rim=None):
    """A heater shield (two plates: the body and the point) leaning against something."""
    c = v3(*center)
    plate(bone, name, c, w, h * 0.66, face, normal=normal, th=0.04, edge=rim or SH["iron"])
    plate(bone, name + "_pt", c - UP * h * 0.4, w * 0.55, h * 0.3, face, normal=normal, th=0.04, edge=rim or SH["iron"])


# ---------------------------------------------------------------- the food merchant
def cheese_wheel(bone, name, foot, r=0.2, h=0.13, yaw=0.0):
    octo(bone, name, foot, r, h, {"all": "m2_cheese", "+2": "m2_cheese_top", "-2": "m2_cheese_top"}, yaw=yaw, stretch=True)


def cheese_cut_wheel(bone, name, foot, r=0.2, h=0.13, yaw=0.0):
    """A wheel with a wedge cut out: three quarters (two boxes) showing the holed inside on the cut."""
    foot = v3(*foot)
    R = ry(yaw)
    add_cube(bone, name, foot + UP * h / 2 + R @ v3(-r / 2, 0, 0), R, (r, h, 2 * r), {"all": "m2_cheese", "+1": "m2_cheese_cut",
             "+2": "m2_cheese_top", "-2": "m2_cheese_top"}, stretch=True)
    add_cube(bone, name + "_q", foot + UP * h / 2 + R @ v3(r / 2, 0, -r / 2), R, (r, h, r), {"all": "m2_cheese", "+3": "m2_cheese_cut",
             "-1": "m2_cheese_cut", "+2": "m2_cheese_top"}, stretch=True)


def cheese_block(bone, name, foot, s=0.36, yaw=0.0):
    """A big block of holed cheese (the cubes on the presentation table)."""
    foot = v3(*foot)
    add_cube(bone, name, foot + UP * s * 0.45, ry(yaw), (s, s * 0.9, s * 0.95), "m2_cheese_cut", stretch=True)


def cheese_wedge(bone, name, foot, l=0.3, h=0.16, yaw=0.0):
    """A wedge (two steps narrowing to the point)."""
    foot = v3(*foot)
    R = ry(yaw)
    add_cube(bone, name, foot + UP * h * 0.5 + R @ v3(-l * 0.2, 0, 0), R, (l * 0.6, h, l * 0.5),
             {"all": "m2_cheese_cut", "+1": "m2_cheese_cut", "+2": "m2_cheese_top"}, stretch=True)
    add_cube(bone, name + "_tip", foot + UP * h * 0.35 + R @ v3(l * 0.25, 0, 0), R, (l * 0.4, h * 0.7, l * 0.3), "m2_cheese_cut",
             stretch=True)


def bread(bone, name, c, yaw=0.0, l=0.3, w=0.16, h=0.1):
    c = v3(*c)
    R = ry(yaw)
    add_cube(bone, name, c + UP * h * 0.35, R, (l, h * 0.7, w), {"all": "m2_bread", "+2": "m2_bread_top"}, stretch=True)
    add_cube(bone, name + "_top", c + UP * h * 0.8, R, (l * 0.8, h * 0.35, w * 0.75), {"all": "m2_bread", "+2": "m2_bread_top"}, stretch=True)


def bread_round(bone, name, c, r=0.13, h=0.11):
    c = v3(*c)
    octo(bone, name, c, r, h * 0.7, {"all": "m2_bread", "+2": "m2_bread_top"}, stretch=True)
    add_cube(bone, name + "_top", c + UP * h * 0.8, ry(0.4), (r * 1.3, h * 0.3, r * 1.3), {"all": "m2_bread", "+2": "m2_bread_top"},
             stretch=True)


def ham(bone, name, hook, length=0.62, w=0.34, yaw=0.0, string=0.12):
    """A cured ham hanging under `hook` on a string: the shank (bone end) at the top, the body widening to the
    rounded bottom, the cut face showing at the bottom."""
    hook = v3(*hook)
    R = ry(yaw)
    beam(bone, name + "_string", hook, hook - UP * (string + 0.03), 0.02, SH["rope"])
    top = hook - UP * string
    add_cube(bone, name + "_bone", top - UP * 0.04, R, (0.06, 0.08, 0.06), "m2_ham_cut", stretch=True)
    parts = ((0.1, 0.42, 0.14), (0.24, 0.55, 0.22), (0.42, 0.9, 0.3), (0.64, 1.0, 0.24), (0.86, 0.82, 0.14))
    for k, (t, f, hh) in enumerate(parts):
        c = top - UP * length * t
        add_cube(bone, "%s_%d" % (name, k), c, R @ rx(0.06 * (k - 2)), (w * f, length * hh, w * f * 0.8),
                 {"all": "m2_ham", "-2": "m2_ham_cut"} if k == 4 else "m2_ham", stretch=True)


def sausages(bone, name, a, b, n=5, sag=0.12):
    """A string of sausages hanging in a festoon between a and b."""
    a, b = v3(*a), v3(*b)
    pts = [a + (b - a) * (k / n) - UP * (4 * sag * (k / n) * (1 - k / n)) for k in range(n + 1)]
    for k in range(n):
        beam(bone, "%s_%d" % (name, k), pts[k], pts[k + 1], 0.06, "m2_sausage", extend=-0.01)


def produce_heap(bone, name, foot, size=(0.55, 0.28, 0.42), produce="m2_apples", crate_region=None, yaw=0.0, fruits=4,
                 fruit_r=0.06, colours=None, solid=False):
    """An open crate (or basket) heaped with fruit: the box, its heaped top, a few loose fruit for relief."""
    foot = v3(*foot)
    R = ry(yaw)
    sx, sy, sz = size
    add_cube(bone, name, foot + UP * sy / 2, R, size, {"all": crate_region or SH["crate"], "+2": produce}, stretch=True)
    add_cube(bone, name + "_heap", foot + UP * (sy + 0.035), R, (sx * 0.82, 0.07, sz * 0.78), produce, stretch=True)
    rng = random.Random(len(name) * 31 + int(foot[0] * 100))
    for k in range(fruits):
        p = foot + UP * (sy + 0.07) + R @ v3(rng.uniform(-sx * 0.3, sx * 0.3), 0, rng.uniform(-sz * 0.28, sz * 0.28))
        add_cube(bone, "%s_f%d" % (name, k), p + UP * fruit_r * 0.8, ry(rng.uniform(0, 1.5)), (fruit_r * 2, fruit_r * 1.8, fruit_r * 2),
                 produce, stretch=True)
    if solid:
        tl.collide((foot[0] - sx / 2, foot[1], foot[2] - sz / 2, foot[0] + sx / 2, foot[1] + sy + 0.1, foot[2] + sz / 2))


def basket(bone, name, foot, r=0.2, h=0.18, content=None, handle=True):
    foot = v3(*foot)
    octo(bone, name, foot, r, h, {"all": "m2_wicker", "+2": content or "m2_wicker"}, stretch=True)
    if handle:
        beam(bone, name + "_h0", foot + UP * h + X * r * 0.85, foot + UP * (h + r * 0.75), 0.03, "m2_wicker")
        beam(bone, name + "_h1", foot + UP * (h + r * 0.75), foot + UP * h - X * r * 0.85, 0.03, "m2_wicker")


def sack(bone, name, foot, s=0.42, yaw=0.0, open_top=None):
    foot = v3(*foot)
    R = ry(yaw)
    add_cube(bone, name, foot + UP * s * 0.45, R, (s, s * 0.9, s * 0.8), "m2_burlap", stretch=True)
    if open_top:
        add_cube(bone, name + "_top", foot + UP * s * 0.93, R, (s * 0.86, s * 0.08, s * 0.7), {"all": "m2_burlap", "+2": open_top}, stretch=True)
    else:
        add_cube(bone, name + "_top", foot + UP * s * 0.98, R, (s * 0.6, s * 0.18, s * 0.5), "m2_burlap", stretch=True)
        add_cube(bone, name + "_tie", foot + UP * s * 1.1, R, (s * 0.3, s * 0.08, s * 0.3), SH["rope"])


def cabbage(bone, name, foot, r=0.12):
    octo(bone, name, foot, r, r * 1.5, "m2_greens", yaw=0.3, stretch=True)


def plant_pot(bone, name, foot, r=0.12, h=0.16, leaves=0.32, region="m2_greens"):
    """A terracotta pot with a leafy plant (crossed boxes)."""
    foot = v3(*foot)
    octo(bone, name, foot, r, h, {"all": "m2_terracotta", "+2": "m2_greens"}, stretch=True)
    for k, a in enumerate((0.3, 0.3 + math.pi / 2)):
        add_cube(bone, "%s_leaf_%d" % (name, k), foot + UP * (h + leaves * 0.4), ry(a), (r * 2.4, leaves * 0.8, r * 1.1), region, stretch=True)


def jar(bone, name, foot, r=0.08, h=0.2):
    foot = v3(*foot)
    octo(bone, name, foot, r, h, {"all": "m2_jar", "+2": "m2_jar_top"}, stretch=True)


def table_cloth(bone, name, x0, x1, z0, z1, y, drop=0.62, sides=True):
    """The ochre cloth on a table top (x0..x1, z0..z1 at height y): a top sheet a little over the edges and the
    front drape hanging down with its gold border and tassels; short side drapes."""
    add_cube(bone, name + "_top", v3((x0 + x1) / 2, y + 0.012, (z0 + z1) / 2), EYE, (x1 - x0 + 0.06, 0.024, z1 - z0 + 0.06),
             {"all": "m2_cloth_top"}, stretch=True)
    plate(bone, name + "_front", v3((x0 + x1) / 2, y + 0.02 - drop / 2, z1 + 0.035), x1 - x0 + 0.06, drop, "m2_tablecloth", th=0.015)
    if sides:
        for s, x in ((-1, x0 - 0.035), (1, x1 + 0.035)):
            plate(bone, "%s_side_%d" % (name, (s + 1) // 2), v3(x, y + 0.02 - drop * 0.3, (z0 + z1) / 2), z1 - z0 + 0.06, drop * 0.6,
                  "m2_cloth_top", normal=(s, 0, 0), th=0.015)


def ivy(bone, name, top, length, width, normal=(0, 0, 1)):
    top = v3(*top)
    plate(bone, name, top - UP * length / 2, width, length, "m2_ivy", normal=normal, th=0.004)
