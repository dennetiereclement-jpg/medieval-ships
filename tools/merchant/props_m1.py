"""Props of the alchemist's and the herbalist's merchant tents (agent M1): tente_alchimiste, tente_herboriste.

Geometry reuses the workshops' helpers (tools/workshops/wslib_b.py: bottle, crystal_cluster, cauldron, open_book,
candle, crossed, hanging_bunch, vine, jar...) drawn with THIS tent's atlas: add_regions(atlas, names) adds the
regions those helpers need (painted with the workshops' painters, tools/workshops/ws_texture_b.py, plus a few of
our own: dried herbs, lavender, potted flowers, terracotta pots, soil, moss, purple brew) to the merchant atlas
before use. Every function takes tent-local coordinates (y up, +z = the open front).
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, "..")
for p in (HERE, TOOLS, os.path.join(TOOLS, "workshops"), os.path.join(TOOLS, "tents"), os.path.join(TOOLS, "carts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import wslib_b as wb  # noqa: E402
import ws_texture_b as wt  # noqa: E402
import tent_texture as tt  # noqa: E402
from galley_texture import _rgb, _jitter, _scale, _mix, hammered_iron, polished_metal, fine_wood, end_grain, twisted_rope  # noqa: E402,E501

v3, norm, add_cube, beam = wb.v3, wb.norm, wb.add_cube, wb.beam
EYE, UP, X, Z = wb.EYE, wb.UP, wb.X, wb.Z
ry = wb.ry
CLEAR = (0, 0, 0, 0)


# ================================================================ painters (img = the region, w x h)
def _ws(fn, *args, seed=0, **kw):
    """Adapter: a ws_texture_b / tent_texture painter fn(img, region, rng, ...) painting the whole small image."""
    def p(img):
        fn(img, (0, 0, img.width, img.height), random.Random(seed), *args, **kw)
    return p


def _clear(img):
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            px[x, y] = CLEAR
    return px


def _bunch_painter(stems, heads=None, seed=0, n=24, head_every=0.0):
    """A hanging bunch of dried plants (cut out): a string at the top, sprigs fanning down, coloured heads."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = _clear(img)
        for y in range(0, 5):
            px[w // 2, y] = _rgb("c9ad7a") + (255,)
        px[w // 2 - 1, 4] = _rgb("8a6a3a") + (255,)
        px[w // 2 + 1, 4] = _rgb("8a6a3a") + (255,)
        for _ in range(n):
            x0 = w / 2 + rng.uniform(-1, 1)
            ang = rng.uniform(-0.7, 0.7)
            L = rng.uniform(h * 0.45, h - 5)
            c = rng.choice(stems)
            for i in range(int(L)):
                x = int(round(x0 + math.sin(ang) * i * 0.8))
                y = 5 + i
                if 0 <= x < w and y < h:
                    px[x, y] = _jitter(c, rng, 8) + (255,)
                    if i > 3 and i % 3 == 0 and 0 <= x + (1 if ang > 0 else -1) < w:
                        q = heads and rng.random() < head_every
                        cc = rng.choice(heads) if q else _scale(c, 1.18)
                        px[x + (1 if ang > 0 else -1), y] = _jitter(cc, rng, 8) + (255,)
            if heads:
                xe = int(round(x0 + math.sin(ang) * (L - 1) * 0.8))
                for dy in range(-3, 1):
                    for dx in (-1, 0, 1):
                        X_, Y_ = xe + dx, int(5 + L + dy)
                        if 0 <= X_ < w and 0 <= Y_ < h and (dx == 0 or rng.random() < 0.55):
                            px[X_, Y_] = _jitter(rng.choice(heads), rng, 10) + (255,)
        # the tie
        for x in range(w // 2 - 2, w // 2 + 3):
            px[x, 6] = _rgb("7a5a30") + (255,)
    return p


def _flowers_painter(petals, seed=0, n_flowers=7, leaves=("3e7a28", "4e8e30", "2e6a20"), spikes=False):
    """A potted plant seen from the side (cut out): leafy stems from the bottom, blossoms of `petals` on top (spikes:
    tall lavender / iris spikes)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = _clear(img)
        lv = [_rgb(c) for c in leaves]
        pt = [_rgb(c) for c in petals]
        for k in range(n_flowers + 3):
            x = w / 2 + rng.uniform(-w * 0.38, w * 0.38)
            top = rng.uniform(1, h * 0.45) if k < n_flowers else rng.uniform(h * 0.35, h * 0.7)
            for y in range(int(top), h):
                xi = int(round(x + (y - h) * (x - w / 2) * 0.02))
                if 0 <= xi < w:
                    px[xi, y] = _jitter(rng.choice(lv), rng, 6) + (255,)
                    if y > h * 0.55 and rng.random() < 0.5:
                        for dx in (-1, 1):
                            if 0 <= xi + dx < w:
                                px[xi + dx, y] = _jitter(rng.choice(lv), rng, 8) + (255,)
            if k < n_flowers:
                xc, yc = int(round(x)), int(top)
                if spikes:
                    for y in range(yc, min(h, yc + int(h * 0.35))):
                        for dx in (-1, 0, 1):
                            if 0 <= xc + dx < w and (dx == 0 or rng.random() < 0.6):
                                px[xc + dx, y] = _jitter(rng.choice(pt), rng, 10) + (255,)
                else:
                    c = rng.choice(pt)
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if abs(dx) + abs(dy) <= 1 or rng.random() < 0.4:
                                X_, Y_ = xc + dx, yc + dy
                                if 0 <= X_ < w and 0 <= Y_ < h:
                                    px[X_, Y_] = _jitter(c, rng, 8) + (255,)
                    if 0 <= xc < w and 0 <= yc < h:
                        px[xc, yc] = _rgb("f0d040") + (255,)
    return p


def _ivy_painter(seed=0, stems_per_px=0.22, dense=0.85, fade=0.5):
    """Dense ivy (cut out): many stems hanging from the top edge, the longest ones a few, leaves of five greens
    thick at the top and thinning down."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = _clear(img)
        greens = [_rgb("5a8a2a"), _rgb("6a9e30"), _rgb("4a7a24"), _rgb("7ab038"), _rgb("3a6a1e")]
        for s in range(max(3, int(w * stems_per_px))):
            x = rng.uniform(0, w - 1)
            L = h * (rng.uniform(0.25, 0.6) if rng.random() < 0.7 else rng.uniform(0.7, 1.0))
            for y in range(int(L)):
                x += rng.uniform(-0.6, 0.6)
                xi = int(max(0, min(w - 1, x)))
                px[xi, y] = _rgb("4a5a22") + (255,)
                if rng.random() < dense * (1.0 - fade * y / h):
                    cx, cy = xi + rng.choice((-2, -1, 1, 2)), y
                    c = rng.choice(greens)
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            if abs(dx) + abs(dy) < 2 or rng.random() < 0.4:
                                X_, Y_ = cx + dx, cy + dy
                                if 0 <= X_ < w and 0 <= Y_ < h:
                                    px[X_, Y_] = _jitter(c, rng, 8) + (255,)
    return p


def _ivy_patch_painter(seed=0):
    """A patch of ivy lying on the roof (cut out): a ragged blob of leaves, thicker at the bottom (the eave)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = _clear(img)
        greens = [_rgb("5a8a2a"), _rgb("6a9e30"), _rgb("4a7a24"), _rgb("7ab038"), _rgb("3a6a1e")]
        for _ in range(int(w * h * 0.3)):
            x, y = rng.uniform(0, w), rng.uniform(0, h)
            nx, ny = (x - w / 2) / (w / 2), (y - h) / h
            if nx * nx + ny * ny * 0.9 > rng.uniform(0.5, 1.0):
                continue
            c = rng.choice(greens)
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    if abs(dx) + abs(dy) < 2 or rng.random() < 0.35:
                        X_, Y_ = int(x) + dx, int(y) + dy
                        if 0 <= X_ < w and 0 <= Y_ < h:
                            px[X_, Y_] = _jitter(c, rng, 8) + (255,)
    return p


def _pot_painter(seed=0):
    """A terracotta pot's side: orange clay, a thicker rim band at the top, darker bottom."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _scale(_rgb("b4643a"), 1.1 - 0.25 * y / h)
                if y < max(2, h // 5):
                    c = _scale(_rgb("c87448"), 1.05)
                if y == max(2, h // 5):
                    c = _rgb("7a3a20")
                px[x, y] = _jitter(c, rng, 5) + (255,)
    return p


def _soil_painter(seed=0):
    def p(img):
        rng = random.Random(seed)
        px = img.load()
        for y in range(img.height):
            for x in range(img.width):
                c = _rgb("4a3020") if rng.random() < 0.7 else _rgb("2e1e12")
                if rng.random() < 0.12:
                    c = _rgb("3e6a24")
                px[x, y] = _jitter(c, rng, 6) + (255,)
    return p


def _moss_painter(seed=0):
    def p(img):
        rng = random.Random(seed)
        px = img.load()
        for y in range(img.height):
            for x in range(img.width):
                c = rng.choice([_rgb("4a7a24"), _rgb("5a8a2a"), _rgb("3a6a1e"), _rgb("6a9a30")])
                px[x, y] = _jitter(c, rng, 8) + (255,)
    return p


def _brew_painter(base, seed=0):
    """A bubbling potion surface: mottled, light bubbles."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _scale(base, rng.choice((0.85, 1.0, 1.12)))
                px[x, y] = _jitter(c, rng, 6) + (255,)
        for _ in range(7):
            cx, cy, r = rng.uniform(1, w - 2), rng.uniform(1, h - 2), rng.uniform(1.0, 2.2)
            for y in range(h):
                for x in range(w):
                    d = math.hypot(x - cx, y - cy)
                    if abs(d - r) < 0.6:
                        px[x, y] = _mix(base, (255, 240, 255), 0.6) + (255,)
    return p


def _plain(color, noise=6, seed=0):
    def p(img):
        tt._fill(img, (0, 0, img.width, img.height), _rgb(color), random.Random(seed), noise=noise)
    return p


def _cloth_painter(base, trim=None, seed=0):
    """A counter cloth: woven tent-colour, a gold band near the bottom edge when trim."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _scale(base, 1.0 + 0.06 * ((x + y) % 2) - 0.04 * ((x // 4 + y // 3) % 2))
                if trim and (h - 5 <= y <= h - 3):
                    c = _rgb("e0b040") if (x + y) % 3 else _rgb("b08020")
                if trim and y == h - 1:
                    c = _scale(base, 0.7)
                px[x, y] = _jitter(c, rng, 4) + (255,)
    return p


POTIONS = {"purple": "9a40d8", "blue": "3a7ae0", "green": "48d040", "red": "d02a3a", "pink": "e060b0",
           "orange": "e07a20", "cyan": "30c8b0", "yellow": "e0c030", "violet": "6a3ad0"}

# name -> (w, h, painter); added to the tent's atlas only when missing (the shell may already have some)
PAINTERS = {
    "glass": (8, 8, _ws(wt._potion, _rgb("b8d0d8"), seed=1)),
    "cork": (8, 8, _plain("a07a4a", 10, 2)),
    "crystal_purple": (8, 16, _ws(wt._crystal, _rgb("9a4ae0"), seed=3)),
    "cauldron": (16, 16, lambda img: hammered_iron(img, (0, 0, img.width, img.height), _rgb("26262a"), random.Random(4), dent=0.12)),
    "iron_dark": (16, 16, lambda img: hammered_iron(img, (0, 0, img.width, img.height), _rgb("2a2a2e"), random.Random(5))),
    "brass": (16, 16, lambda img: polished_metal(img, (0, 0, img.width, img.height),
                                                 [(0.0, _rgb("6a5020")), (0.4, _rgb("a88838")), (0.8, _rgb("d8b860")), (1.0, _rgb("f0dc98"))],
                                                 random.Random(6))),
    "brew_purple": (16, 16, _brew_painter(_rgb("a040e0"), seed=7)),
    "book_top": (8, 16, _ws(wt._book_top, seed=8)),
    "pages": (32, 16, _ws(wt._pages, seed=9)),
    "wax": (8, 16, _ws(wt._wax, seed=10)),
    "flame": (8, 8, _ws(wt._flame, seed=11)),
    "herbs": (16, 32, _ws(wt._bunch, "herbs", seed=12)),
    "herbs_dry": (16, 32, _bunch_painter([_rgb("8a8a2a"), _rgb("9a9030"), _rgb("6a7a24"), _rgb("a89a40")],
                                         heads=[_rgb("c8a848"), _rgb("d8b858"), _rgb("b89040")], seed=13, head_every=0.3)),
    "lavender": (16, 32, _bunch_painter([_rgb("5a7a3a"), _rgb("4a6a30")], heads=[_rgb("9a6ac8"), _rgb("8a58b8"), _rgb("b088d8")],
                                        seed=14, n=18, head_every=0.5)),
    "herbs_red": (16, 32, _bunch_painter([_rgb("6a5a2a"), _rgb("7a6a30")], heads=[_rgb("b84a2a"), _rgb("c86a30"), _rgb("9a3a20")],
                                         seed=15, n=18, head_every=0.45)),
    "ivy_m1": (32, 48, _ivy_painter(seed=16)),
    "vines": (16, 48, _ivy_painter(seed=17, stems_per_px=0.3, dense=0.7)),
    "leaves": (32, 32, _ivy_patch_painter(seed=18)),
    "flowers_white": (16, 16, _flowers_painter(["f4f4ec", "e8e8f0", "ffffff"], seed=19)),
    "flowers_purple": (16, 16, _flowers_painter(["8a4ac0", "a060d0", "6a38a8"], seed=20, spikes=True)),
    "flowers_red": (16, 16, _flowers_painter(["c82a2a", "e04040", "a81e20"], seed=21)),
    "sprout": (16, 16, _flowers_painter(["4e8e30"], seed=22, n_flowers=0)),
    "pot_clay": (16, 16, _pot_painter(seed=23)),
    "soil": (8, 8, _soil_painter(seed=24)),
    "moss": (16, 16, _moss_painter(seed=25)),
    "jar": (16, 16, _ws(wt._jar, seed=26)),
    "jar_top": (16, 16, _ws(wt._jar, top=True, seed=27)),
    "linen": (16, 16, lambda img: tt._weave(img, (0, 0, img.width, img.height), _rgb("e0d6c0"), random.Random(28), seams=0, patches=0,
                                            stains=1, tears=0)),
    "stone_slab": (16, 16, _plain("a3a39d", 7, 29)),
    "parchment": (16, 16, _ws(wt._parchment, seed=30)),
    "cloth_purple_m1": (32, 16, _cloth_painter(_rgb("5a2a82"), trim=True, seed=31)),
    "cloth_green_m1": (32, 16, _cloth_painter(_rgb("3e6a2a"), trim=True, seed=32)),
    "mushroom": (8, 8, _plain("b83a2a", 10, 33)),
}
for _c, _hex in POTIONS.items():
    PAINTERS["potion_" + _c] = (8, 8, _ws(wt._potion, _rgb(_hex), seed=40 + len(_c)))
for _c, _hex in (("purple", "5a2a7a"), ("red", "7a2420"), ("brown", "6a4424"), ("green", "2e5a2a"), ("blue", "2a3e7a")):
    PAINTERS["book_" + _c] = (8, 16, _ws(wt._book, _rgb(_hex), seed=60 + len(_c)))


def add_regions(atlas, names):
    """Adds the named regions (PAINTERS) to the tent's atlas (merchantlib.Atlas), skipping the shell's own."""
    for n in names:
        if n in atlas.regions and n not in atlas.painters:
            continue
        w, h, painter = PAINTERS[n]
        atlas.add(n, w, h, painter)


ALCH_REGIONS = ["glass", "cork", "crystal_purple", "cauldron", "iron_dark", "brass", "brew_purple", "book_top", "pages", "wax",
                "flame", "herbs", "herbs_dry", "herbs_red", "lavender", "jar", "jar_top", "linen", "parchment", "stone_slab",
                "book_purple", "book_red", "book_brown", "book_green", "book_blue"] + ["potion_" + c for c in POTIONS]
HERB_REGIONS = ["herbs", "herbs_dry", "lavender", "herbs_red", "ivy_m1", "vines", "leaves", "flowers_white", "flowers_purple",
                "flowers_red", "sprout", "pot_clay", "soil", "moss", "jar", "jar_top", "linen", "iron_dark", "brass"]


# ================================================================ shared small props
def collide(box):
    wb.collide(box)


def bottle(bone, name, foot, color, r=0.07, h=0.17, shape="round", neck_h=0.07, glow=True):
    wb.bottle(bone, name, foot, color, r=r, h=h, neck_h=neck_h, shape=shape, glow=glow)


def bottle_row(bone, name, x0, x1, y, z, rng, colors, rmin=0.055, rmax=0.085, gap=0.035, shapes=("round", "round", "tall", "flask")):
    """A row of potion bottles on a board (top face at y) from x0 to x1, centred at depth z."""
    x = x0 + rmax
    k = 0
    while x < x1 - rmin:
        r = rng.uniform(rmin, rmax)
        if x + r > x1:
            break
        shape = rng.choice(shapes)
        h = r * rng.uniform(2.0, 2.8) if shape != "tall" else r * rng.uniform(3.0, 3.8)
        bottle(bone, "%s_%d" % (name, k), (x, y, z + rng.uniform(-0.03, 0.03)), rng.choice(colors), r=r, h=h, shape=shape,
               neck_h=r * 0.9)
        x += 2 * r + gap * rng.uniform(0.6, 1.4) + (0.07 if shape == "flask" else 0.0)
        k += 1
    return k


def pot(bone, name, foot, r=0.1, h=0.16, plant="flowers_white", ph=None, pw=None, yaw=0.0):
    """A terracotta flower pot (octagonal, slightly wider rim) with soil and a plant (two crossed cut-out planes)."""
    foot = v3(*foot)
    wb.octo(bone, name, foot, r * 0.85, h * 0.8, {"all": "pot_clay", "+2": "soil"}, stretch=True)
    add_cube(bone, name + "_rim", foot + UP * (h * 0.88), ry(yaw), (2 * r, h * 0.2, 2 * r), {"all": "pot_clay", "+2": "soil"},
             stretch=True)
    if plant:
        ph = ph or r * 4.0
        pw = pw or r * 3.8
        wb.crossed(bone, name + "_plant", foot + UP * (h * 0.95 + ph / 2 - 0.01), pw, ph, plant, yaw=yaw)


def herb_line(bone, name, a, b, n, kinds, rng, length=(0.6, 0.9), width=0.36, string=(0.03, 0.12)):
    """n bunches of dried herbs hanging from the bar a..b (kinds picked in turn), a cord along the bar."""
    a, b = v3(*a), v3(*b)
    for k in range(n):
        t = (k + 0.5) / n
        p = a + (b - a) * t
        wb.hanging_bunch(bone, "%s_%d" % (name, k), p, kinds[k % len(kinds)], length=rng.uniform(*length),
                         width=width * rng.uniform(0.85, 1.1), string=rng.uniform(*string))


def cloth_cover(bone, name, x0, x1, z0, z1, y, hang, region, sides=True, th=0.02):
    """A cloth on a counter top (x0..x1, z0..z1 at y) hanging down the front (+z) by `hang` (and the two ends)."""
    add_cube(bone, name + "_top", ((x0 + x1) / 2, y + th / 2, (z0 + z1) / 2), EYE, (x1 - x0 + 0.04, th, z1 - z0 + 0.04),
             {"all": region}, stretch=True, u_dir=X, v_dir=Z)
    wb.plate(bone, name + "_front", ((x0 + x1) / 2, y + th - hang / 2, z1 + 0.025), x1 - x0 + 0.04, hang, region, normal=(0, 0, 1),
             th=th)
    if sides:
        for s, xx in ((-1, x0), (1, x1)):
            wb.plate(bone, "%s_side_%d" % (name, (s + 1) // 2), (xx + s * 0.025, y + th - hang * 0.4, (z0 + z1) / 2), z1 - z0 + 0.04,
                     hang * 0.8, region, normal=(s, 0, 0), th=th)


# ================================================================ alchemist
def cauldron_crystal(bone, detail, foot, rng, r=0.5, h=0.58):
    """The bubbling purple cauldron on its three legs, a big glowing amethyst cluster growing out of the brew, little
    crystals round it; collides."""
    foot = v3(*foot)
    wb.cauldron(bone, "cauldron", foot, r=r, h=h, content="brew_purple", legs=True, glow_content=True)
    top = foot + UP * (0.1 + h - 0.1)
    wb.crystal_cluster(bone, "amethyst", top, "purple", rng, n=9, h=0.95, w=0.2, spread=0.24, lean=0.5)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 1.1
        wb.crystal_cluster(detail, "amethyst_s%d" % k, top + v3(math.cos(a), 0, math.sin(a)) * r * 0.55, "purple", rng, n=3,
                           h=0.26, w=0.08, spread=0.06)
    collide((foot[0] - r - 0.08, foot[1], foot[2] - r - 0.08, foot[0] + r + 0.08, foot[1] + h + 0.1, foot[2] + r + 0.08))


def shelf_potions(detail, levels, rng, colors=("purple", "blue", "green", "red", "pink", "orange", "teal", "violet", "purple", "blue")):
    """Bottles of every colour on the shelf boards (x0, x1, y, z_front, z_back)."""
    for i, (x0, x1, y, zf, zb) in enumerate(levels):
        z = (zf + zb) / 2
        bottle_row(detail, "shelf_pot_%d" % i, x0 + 0.03, x1 - 0.03, y, z, rng, colors, rmin=0.06, rmax=0.09, gap=0.05)


def big_flasks(bone, detail, pts, colors):
    """Big round flasks with long necks (the orange, green and red ones on the front counter)."""
    for k, (p, c) in enumerate(zip(pts, colors)):
        p = v3(*p)
        wb.octo(bone, "glow_flask_%d" % k, p, 0.13, 0.22, {"all": "potion_" + c}, stretch=True, k=0.88)
        add_cube(bone, "flask_%d_neck" % k, p + UP * 0.3, EYE, (0.08, 0.17, 0.08), "glass", stretch=True)
        add_cube(detail, "flask_%d_cork" % k, p + UP * 0.4, EYE, (0.085, 0.045, 0.085), "cork", stretch=True)


# ================================================================ herbalist
def ivy_valance(bone, L, rng, front=True, sides=True, back=False, drop=(0.35, 0.95), step=0.55, y_off=-0.05, out=0.0):
    """Ivy strands hanging from the eave all round (in front of the valance), random lengths."""
    hw, hd, ey = L.half_w + out, L.half_d + out, L.eave_y + y_off
    runs = []
    if front:
        runs.append(((-hw, hd), (hw, hd), (0, 0, 1)))
    if back:
        runs.append(((hw, -hd), (-hw, -hd), (0, 0, -1)))
    if sides:
        runs.append(((-hw, -hd), (-hw, hd), (-1, 0, 0)))
        runs.append(((hw, hd), (hw, -hd), (1, 0, 0)))
    k = 0
    for (ax, az), (bx, bz), n in runs:
        length = math.hypot(bx - ax, bz - az)
        m = max(2, int(length / step))
        for i in range(m):
            if rng.random() < 0.25:
                continue
            t = (i + rng.uniform(0.2, 0.8)) / m
            x, z = ax + (bx - ax) * t, az + (bz - az) * t
            d = rng.uniform(*drop)
            wb.vine(bone, "ivy_v_%d" % k, (x + n[0] * 0.03, ey, z + n[2] * 0.03), d, rng.uniform(0.35, 0.6), normal=n,
                    region="ivy" if k % 3 else "vines")
            k += 1
    return k


def ivy_post(bone, name, x, z, y0, y1, normal, w=0.3, region="ivy"):
    """A strip of ivy climbing a post (a plate on its face)."""
    n = v3(*normal)
    wb.plate(bone, name, (x + n[0] * 0.16, (y0 + y1) / 2, z + n[2] * 0.16), w, y1 - y0, region, normal=n, th=0.004)


def mossy_crate(bone, detail, name, foot, s=0.8, yaw=0.0, pots=(), rng=None):
    """An iron-banded crate (the shell's crate) with moss on top, ivy down its front and flower pots on it."""
    import merchantlib as ml
    foot = v3(*foot)
    ml.crate(bone, name, foot, size=s, yaw=yaw)
    R = ry(yaw)
    add_cube(bone, name + "_moss", foot + UP * (s + 0.012), R, (s * 0.92, 0.025, s * 0.92), "moss", stretch=True)
    wb.plate(detail, name + "_ivy", foot + R @ v3(-s * 0.18, s * 0.72, s / 2 + 0.012), s * 0.5, s * 0.55, "vines", normal=R @ v3(0, 0, 1),
             th=0.004)
    for k, (dx, dz, plant, r) in enumerate(pots):
        pot(detail, "%s_pot_%d" % (name, k), foot + R @ v3(dx, 0, dz) + UP * (s + 0.025), r=r, h=r * 1.5, plant=plant, yaw=yaw)


def roof_point(L, side, s, t, droop=0.1, ov=0.34):
    """A point of the shell's roof (mirrors merchantlib.pavilion's roof_point): side 0 front, 1 right, 2 back, 3 left;
    s along the eave (0..1), t from the apex (0) to the eave (1)."""
    W, D = L.half_w + ov, L.half_d + ov
    ey = L.eave_y + 0.02
    rc = [v3(-W, ey, D), v3(W, ey, D), v3(W, ey, -D), v3(-W, ey, -D)]
    c0, c1 = rc[side], rc[(side + 1) % 4]
    e = c0 + (c1 - c0) * s
    dd = 0.4 * t + 0.6 * (1 - (1 - t) ** 2)
    p = v3(0, L.apex_y, 0) * (1 - t) + e * t
    p[1] = L.apex_y - (L.apex_y - ey) * dd - droop * math.sin(math.pi * s) * math.sin(math.pi * t)
    return p


def roof_ivy(bone, L, rng, sides=(0, 1, 3), per_side=4, region="leaves", lift=0.045):
    """Patches of ivy creeping up the roof from the eave: cut-out plates lying on the slope (tangent, a little above
    the canvas)."""
    k = 0
    for side in sides:
        for i in range(per_side):
            s = (i + rng.uniform(0.25, 0.75)) / per_side
            t = rng.uniform(0.72, 0.86)
            p = roof_point(L, side, s, t)
            ds = roof_point(L, side, min(1, s + 0.01), t) - roof_point(L, side, max(0, s - 0.01), t)
            dt = roof_point(L, side, s, min(1, t + 0.01)) - roof_point(L, side, s, max(0, t - 0.01))
            n = norm(np.cross(ds, dt))
            if n[1] < 0:
                n = -n
            up = -norm(dt)
            h = rng.uniform(0.8, 1.15)
            # the patch's lower edge near the eave: centre half a patch up the slope
            c = p + up * (h * 0.15) + n * lift
            wb.plate(bone, "roof_ivy_%d" % k, c, rng.uniform(1.0, 1.4), h, region, normal=n, up=up, th=0.004)
            k += 1
    return k


def herb_rope(bone, name, a, b, n, kinds, rng, sag=0.08, **kw):
    """A rope strung from a to b (sagging) with n bunches of herbs hanging from it."""
    import tentlib as tl
    a, b = v3(*a), v3(*b)
    tl.rope(bone, name + "_rope", a, b, d=0.03, sag=sag, segs=3)
    for k in range(n):
        t = (k + 0.5) / n
        p = a + (b - a) * t - UP * (4 * sag * t * (1 - t)) - UP * 0.02
        wb.hanging_bunch(bone, "%s_%d" % (name, k), p, kinds[k % len(kinds)], length=rng.uniform(0.55, 0.85),
                         width=rng.uniform(0.3, 0.38), string=rng.uniform(0.0, 0.06))


PLANTS = ("flowers_white", "flowers_purple", "flowers_red", "sprout")


def pot_row(bone, name, x0, x1, y, z, rng, plants=PLANTS, rmin=0.09, rmax=0.13, gap=0.05):
    """A row of flower pots on a board (top at y) from x0 to x1 at depth z."""
    x = x0 + rmax
    k = 0
    while x < x1 - rmin:
        r = rng.uniform(rmin, rmax)
        if x + r > x1:
            break
        pot(bone, "%s_%d" % (name, k), (x, y, z + rng.uniform(-0.04, 0.04)), r=r, h=r * 1.5, plant=rng.choice(plants),
            yaw=rng.uniform(-0.4, 0.4))
        x += 2 * r + gap * rng.uniform(0.6, 1.4)
        k += 1
    return k
