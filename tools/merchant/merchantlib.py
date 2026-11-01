"""Shared shell, props, atlas and export of the six merchant tents (1.14.0): one block each, static, drawn like the
tents / carts / workshops from a .bbmodel (TentType JSON group "tents").

A generator (tools/merchant/generate_<id>.py) does, in this order:

    import merchantlib as ml
    ml.setup("tente_x")                          # resets the collisions / uuids for this tent (call first)
    atlas = ml.Atlas("tente_x", colour="red")    # red, purple, green, blue, yellow, teal, burgundy, darkred, navy,
                                                 # charcoal; banner_colour= / rug_colour= (optional) override the
                                                 # banners + flag + pennants / the rug
    atlas.add("my_region", w, h, painter)        # optional, BEFORE export: w x h px in the free band of this tent's
                                                 # atlas; painter(img) paints a PIL RGBA image of size w x h
    root = ml.Bone("tente_x")
    L = ml.pavilion(root, atlas, emblem="swords", flag_corner="back_left", side_banners=2, rug=True, lanterns=2,
                    front_counter=True, back_shelves=True, ivy=False)
    ... ml.barrel / ml.crate / ml.sack / ml.basket / ml.bottle / ml.hanging_bunch / ml.weapon_rack / ml.lantern ...
    decor = ml.Decor(); decor.block("furnish:spruce_crate", x, y, z, facing="front", alt="minecraft:barrel")
    ml.export(root, "tente_x", atlas, decor=decor, icon=dict(colour="red", emblem="swords"))

Coordinates: tent-local blocks, y up (y = 0 = top of the ground block), +z = the open FRONT (towards the player who
placed it), the anchor block's centre (0, 0, 0) = centre of the footprint. Small things go under L.detail (the bone
named "detail", hidden beyond 32 blocks). Cubes whose name starts with "glow" are drawn full bright; a cube whose 4
sides use the "lantern" region is rebuilt as a lit lantern on export (tools/lanterns.py).

pavilion() options: emblem in EMBLEMS (swords, flask, leaf, anvil, cheese, scroll; 1.15.0: lyre, muskets, bow, star,
shield, cannon); roof_rise (apex height above the eaves, default 3.2: lower = flatter roof); flag_corner back_left |
back_right; side_banners 0 (none), 1 (left side), 2 (both sides); lanterns 0, 2 (front posts) or 4 (all posts);
front_counter False | True (= "right") | "right" | "left" | "both" (an L: a piece along the front, a return along the
side); back_shelves True: a 4-level shelf unit along the back wall; ivy True: ivy strips on the valance and posts.
The Layout it returns: half_w, half_d, eave_y, apex_y, counter_top_y, counter_boxes [(x0, y, z0, x1, y, z1) top
surfaces], shelf_levels [(x0, x1, y, z_front, z_back) board tops], floor (x0, z0, x1, z1), front_left /
front_right (ground points (x, 0, z) beside the front posts, for barrels / crates), rug_box (x0, z0, x1, z1),
detail (Bone), shell (Bone), atlas, colour, emblem.

1.16.0 (backward compatible: the eleven earlier tents regenerate byte-identically): emblems poison (a skull above a
flask) and cleavers (two crossed cleavers); pavilion(..., flags=False) drops the flag poles, flags and pennants
(rug=False already drops the rug); stall(root, atlas, ...) (or pavilion(..., roof="gable")) builds the GABLED market
stall instead of the pointed pavilion: four squared posts with gold caps above the roof, the ridge along x, two
slightly sagging roof slopes with stripes running down the slope, striped gable-end triangles, the dagged valance
edged in gold on all four sides, the big banner hanging from a rod on a front post, lanterns on the front posts, a long
counter along the front, back shelves, a dark plank back wall, a hanging rail under the eaves (L.hang_y, L.hang_z);
no flags, no rug by default (see stall()); its own regions stall_roof, stall_valance, stall_valance_end, stall_gable,
stall_wall are added to the atlas when it is built; icon(..., shape="stall") draws the stall's item icon.

Shell atlas regions (every tent's atlas has them; colour-dependent ones in the tent's colour):
  wood, wood_dark, plank, plank_dark, post (carved dark post, grain along u), beam (carved eave beam), trim_gold,
  leather, leather_dark (64x16 strips); 16x16: end_grain, rope, iron, gold, lantern, glow, brass, steel, white,
  black_iron, flame, glass, cork, wax, ingot, gold_ingot, coal, embers, stone, stone_top, potion_red, potion_blue,
  potion_green, potion_purple, potion_yellow, potion_orange, potion_pink, potion_cyan, cloth_red, cloth_blue,
  cloth_white, cloth_dark; 32x32: crate, crate_top, barrel, barrel_top, sack, basket, basket_top, straw, herbs,
  herbs_dry (cut-out bunches), ivy (cut-out leaves), cloth (tent colour), cloth_beige, cloth_hang (tent colour,
  gold band and fringe at the bottom, cut-out), apples, produce (mixed vegetables), canvas, beige;
  big: roof (6 stripes colour / beige), valance (6 dagged tabs, gold edge, cut-out), wall, counter (front panel),
  banner (tent colour, gold border, emblem, V point, cut-out), flag (swallow-tail, emblem), pennant, pennant_beige,
  rug (tent colour, gold borders, emblem), shield (blank heater shield, cut-out).
"""
import json
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TOOLS, "tents"))
sys.path.insert(0, os.path.join(TOOLS, "carts"))
sys.path.insert(0, os.path.join(TOOLS, "workshops"))
sys.path.insert(0, TOOLS)
import tentlib as tl  # noqa: E402
import cartlib as cl  # noqa: E402
from galley_texture import _rgb, _jitter, _mix, _scale, fine_wood, hammered_iron, twisted_rope, end_grain, paint_lamp_glass, polished_metal  # noqa: E402,F401
import tent_texture as tt  # noqa: E402
import ws_texture_a as wta  # noqa: E402

gg, gn = tl.gg, tl.gn
v3, norm, Bone, add_cube, beam, loft = tl.v3, tl.norm, tl.Bone, tl.add_cube, tl.beam, tl.loft
EYE, UP = tl.EYE, tl.UP
X, Z = np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0])
ASSETS, ROOT = tl.ASSETS, tl.ROOT
collide, collide_segment, rope, COLLIDERS = tl.collide, tl.collide_segment, tl.rope, tl.COLLIDERS
ry, rx, rz = gg.ry, gg.rx, gg.rz

# ---------------------------------------------------------------- colours
BEIGE = _rgb("e8dcbc")
GOLD = _rgb("d9a93a")
GOLD_DARK = _rgb("8a6418")
COLOURS = {   # main, dark (shadows, edges), light
    "red":    (_rgb("a42a24"), _rgb("5e1410"), _rgb("c8463a")),
    "purple": (_rgb("5e2c8a"), _rgb("321650"), _rgb("7c48aa")),
    "green":  (_rgb("3f6a2c"), _rgb("213a16"), _rgb("5a8a3e")),
    "blue":   (_rgb("27386e"), _rgb("141d3e"), _rgb("3a5096")),
    "yellow": (_rgb("c9951e"), _rgb("7a560c"), _rgb("e2b648")),
    "teal":   (_rgb("1f7c84"), _rgb("0f454a"), _rgb("36a0a6")),
    # 1.15.0 (merchant tents II)
    "burgundy": (_rgb("6e1a2c"), _rgb("3a0c16"), _rgb("8e2e42")),
    "darkred":  (_rgb("7a1c16"), _rgb("400c08"), _rgb("9a3026")),
    "navy":     (_rgb("1c2850"), _rgb("0e142c"), _rgb("2e3e72")),
    "charcoal": (_rgb("3a3634"), _rgb("1c1a1a"), _rgb("56504c")),
}
# the paint seed of each colour (the 1.14.0 ones keep their former seeds: their atlases regenerate identically)
_SEED = {c: k for k, c in enumerate(("blue", "green", "purple", "red", "teal", "yellow", "burgundy", "darkred", "navy", "charcoal"))}
EMBLEMS = ("swords", "flask", "leaf", "anvil", "cheese", "scroll", "lyre", "muskets", "bow", "star", "shield", "cannon", "poison",
           "cleavers")
EMBLEM_ICON = {"swords": (220, 222, 228), "flask": (150, 200, 240), "leaf": (230, 226, 200), "anvil": (220, 222, 228),
               "cheese": (246, 210, 80), "scroll": (240, 228, 196), "lyre": (232, 186, 70), "muskets": (220, 222, 228),
               "bow": (232, 186, 70), "star": (232, 186, 70), "shield": (200, 206, 216), "cannon": (236, 226, 196),
               "poison": (236, 226, 200), "cleavers": (220, 222, 228)}
GOLD_STOPS = [(0, (120, 84, 26)), (0.5, (214, 170, 72)), (1, (250, 230, 160))]
STEEL_STOPS = [(0.0, (72, 74, 80)), (0.45, (140, 144, 150)), (0.8, (196, 200, 206)), (1.0, (236, 238, 242))]
POTIONS = {"red": "c42c2c", "blue": "2e5ed2", "green": "2ea24e", "purple": "9a3ccc", "yellow": "e2c23a", "orange": "e27a2a",
           "pink": "e070b4", "cyan": "3cc4d4"}

_NAME = ["tente"]


def setup(name):
    """Resets the collision list, the uuids and the region tables for one tent (call first)."""
    _NAME[0] = name
    tl.setup(name)


# ---------------------------------------------------------------- atlas
_SHELL = [  # (name, w, h) in packing order (rows of equal height)
    ("wood", 64, 16), ("wood_dark", 64, 16), ("plank", 64, 16), ("plank_dark", 64, 16), ("post", 64, 16), ("beam", 64, 16),
    ("leather", 64, 16), ("trim_gold", 64, 16),
] + [(n, 16, 16) for n in (
    "end_grain", "rope", "iron", "gold", "lantern", "glow", "brass", "steel", "white", "black_iron", "flame", "glass", "cork",
    "wax", "ingot", "gold_ingot", "coal", "embers", "stone", "stone_top", "potion_red", "potion_blue", "potion_green",
    "potion_purple", "potion_yellow", "potion_orange", "potion_pink", "potion_cyan", "cloth_red", "cloth_blue", "cloth_white",
    "cloth_dark")] + [(n, 32, 32) for n in (
    "crate", "crate_top", "barrel", "barrel_top", "sack", "basket", "basket_top", "straw", "herbs", "herbs_dry", "ivy", "cloth",
    "cloth_beige", "cloth_hang", "apples", "produce")] + [
    ("roof", 192, 96), ("banner", 64, 96), ("rug", 144, 96), ("canvas", 64, 64), ("beige", 48, 48), ("leather_dark", 48, 16),
    ("valance", 192, 32), ("flag", 64, 32), ("wall", 128, 64), ("counter", 64, 32), ("pennant", 32, 16), ("pennant_beige", 32, 16),
    ("shield", 32, 32),
]


class Atlas:
    """The atlas of one tent: the shared shell regions (painted in the tent's colour) + the regions added by the tent
    (atlas.add). Painted on export (textures/entity/<id>.png)."""

    def __init__(self, name, colour="red", size=512, banner_colour=None, rug_colour=None):
        for c in (colour, banner_colour or colour, rug_colour or colour):
            if c not in COLOURS:
                raise KeyError("colour must be one of %s" % ", ".join(COLOURS))
        self.name, self.colour, self.size = name, colour, size
        self.banner_colour = banner_colour   # None: the tent colour (banners, flag, pennants)
        self.rug_colour = rug_colour         # None: the tent colour
        self.emblem = "swords"
        self.regions = {}
        self.painters = {}
        self._x = self._y = self._row = 0
        for n, w, h in _SHELL:
            self.regions[n] = self._alloc(w, h)
        self.free_y = self._y + self._row   # the free band starts on the next row
        self._apply()

    def _alloc(self, w, h):
        if self._x + w > self.size:
            self._x, self._y, self._row = 0, self._y + self._row, 0
        if self._y + h > self.size:
            # the free band is full: double the atlas (existing regions keep their pixels), continue below
            self.size *= 2
            self._x, self._y, self._row = 0, self.size // 2, 0
        r = (self._x, self._y, w, h)
        self._x += w
        self._row = max(self._row, h)
        return r

    def add(self, name, w, h, painter):
        """Allocates w x h px for `name` in the free band; painter(img) paints a PIL RGBA image of that size."""
        if name in self.regions and name not in self.painters:
            raise KeyError("region %s is a shell region" % name)
        if name not in self.regions:
            self.regions[name] = self._alloc(int(w), int(h))
        self.painters[name] = painter
        self._apply()
        return self.regions[name]

    def _apply(self):
        gn.REGIONS = {k: (0,) + r for k, r in self.regions.items()}
        gn.SIZE = self.size
        gg.REGIONS = dict(self.regions)
        gg.SIZE = self.size

    @property
    def main(self):
        return COLOURS[self.colour][0]

    def make(self, path):
        from PIL import Image
        img = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
        _paint_shell(img, self.regions, self.colour, self.emblem, banner_colour=self.banner_colour, rug_colour=self.rug_colour)
        for name, painter in self.painters.items():
            u, v, w, h = self.regions[name]
            sub = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            painter(sub)
            img.paste(sub, (u, v))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        img.save(path)
        return img


# ---------------------------------------------------------------- painting
def _px(img, R, x, y, c, a=255):
    img.putpixel((R[0] + x, R[1] + y), tuple(int(k) for k in c[:3]) + (a,))


def _fill(img, R, c, rng, noise=6):
    tt._fill(img, R, c, rng, noise=noise)


def _clear(img, R):
    for y in range(R[3]):
        for x in range(R[2]):
            img.putpixel((R[0] + x, R[1] + y), (0, 0, 0, 0))


def _weave(img, R, c, rng, seams=0, seam_dir="h", stains=1, patches=0):
    tt._weave(img, R, c, rng, seams=seams, patches=patches, stains=stains, tears=0, seam_dir=seam_dir, noise=4)


def _carved(img, R, base, dark, rng, diamonds=True):
    """Dark carved wood along u: two grooves, a row of carved diamonds between them."""
    fine_wood(img, R, base, dark, R[3], rng, joints=False, knots=0.05, grain=0.12, shade=0.06)
    u, v, w, h = R
    for x in range(w):
        for y in (2, h - 3):
            _px(img, R, x, y, _scale(dark, 0.8))
            _px(img, R, x, y + 1, _scale(base, 1.18))
        if diamonds:
            cx = (x % 10) - 5
            for y in range(4, h - 4):
                cy = y - h / 2 + 0.5
                if abs(cx) + abs(cy) * 1.2 < 3.2:
                    k = 1.15 if cx < 0 else 0.7
                    _px(img, R, x, y, _scale(base, k))


def _stripes_roof(img, R, colour, rng):
    """The roof: 6 vertical stripes (colour, beige ...), a weave, dark seams between the stripes, a soft shade."""
    main, dark, light = COLOURS[colour]
    u, v, w, h = R
    sw = w // 6
    for k in range(6):
        c = main if k % 2 == 0 else BEIGE
        _weave(img, (u + k * sw, v, sw, h), c, rng, stains=2)
    for y in range(h):
        sh = 0.92 + 0.1 * (y / h)
        for x in range(w):
            r, g, b, a = img.getpixel((u + x, v + y))
            k = sh
            if x % sw in (0, sw - 1):
                k *= 0.78
            img.putpixel((u + x, v + y), _scale((r, g, b), k) + (255,))


def _valance(img, R, colour, rng):
    """6 dagged tabs (colour / beige in turn), a gold band at the top, gold edging round the square dags; cut-out."""
    main, dark, light = COLOURS[colour]
    u, v, w, h = R
    tw = w // 6
    solid = int(h * 0.55)
    for k in range(6):
        c = main if k % 2 == 0 else BEIGE
        _weave(img, (u + k * tw, v, tw, h), c, rng)
    for x in range(w):
        lx = x % tw
        tooth = (lx // (tw // 4)) % 2 == 0 if tw >= 8 else True
        inset = lx % (tw // 4)
        bottom = h - 2 if tooth and 0 < inset else solid
        if lx % (tw // 4) == 0:
            bottom = solid
        for y in range(h):
            if y > bottom:
                _px(img, R, x, y, (0, 0, 0), 0)
            elif y >= bottom - 1 or y < 3:
                _px(img, R, x, y, _jitter(GOLD if y != 0 else GOLD_DARK, rng, 8))
        # gold vertical edges of each tooth
        if lx % (tw // 4) in (1,) or lx % (tw // 4) == (tw // 4) - 1:
            if tooth:
                for y in range(solid, bottom + 1):
                    _px(img, R, x, y, _jitter(GOLD, rng, 8))


def _emblem(img, box, kind, colour, scale=1.0, faded=False):
    """Draws the emblem `kind` in the box (u, v, w, h) of the atlas (gold, silver, white, as on the banners)."""
    from PIL import Image, ImageDraw
    u, v, w, h = box
    S = 4
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    W, H = w * S, h * S

    def P(x, y):   # unit square (0..1) centred, scaled
        return (W / 2 + (x - 0.5) * W * scale, H / 2 + (y - 0.5) * H * scale)

    silver, silver_d = (214, 218, 224), (120, 124, 132)
    gold, gold_d = (232, 186, 70), (140, 96, 24)
    white = (240, 232, 210)
    lw = max(2, int(W * scale * 0.035))
    if kind == "swords":
        for sgn in (1, -1):
            a, b = P(0.5 - 0.36 * sgn, 0.12), P(0.5 + 0.28 * sgn, 0.8)
            d.line([a, b], fill=silver_d, width=lw * 3)
            d.line([a, b], fill=silver, width=lw * 2)
            # guard and grip near b
            gx, gy = P(0.5 + 0.2 * sgn, 0.7)
            d.line([(gx - 0.12 * W * scale, gy - 0.1 * H * scale * sgn * 0 - 0.08 * H * scale), (gx + 0.12 * W * scale, gy + 0.08 * H * scale)][::1],
                   fill=gold, width=lw * 2)
            ex, ey = P(0.5 + 0.34 * sgn, 0.9)
            d.line([b, (ex, ey)], fill=gold_d, width=lw * 2)
            d.ellipse([ex - lw * 1.6, ey - lw * 1.6, ex + lw * 1.6, ey + lw * 1.6], fill=gold)
    elif kind == "flask":
        cx, cy = P(0.5, 0.64)
        r = 0.27 * W * scale
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(220, 236, 244), outline=silver_d, width=lw)
        d.chord([cx - r + lw, cy - r + lw, cx + r - lw, cy + r - lw], 10, 170, fill=(70, 140, 230))
        nx0, ny0 = P(0.43, 0.14)
        nx1, ny1 = P(0.57, 0.42)
        d.rectangle([nx0, ny0, nx1, ny1], fill=(220, 236, 244), outline=silver_d, width=lw)
        d.rectangle([nx0 - lw, ny0 - lw * 2, nx1 + lw, ny0 + lw], fill=(150, 100, 60))
        hx, hy = P(0.4, 0.56)
        d.ellipse([hx - lw * 1.5, hy - lw * 2.5, hx + lw * 1.5, hy + lw * 2.5], fill=(255, 255, 255))
    elif kind == "leaf":
        c0, c1 = (232, 226, 200), (150, 160, 110)
        stem = [P(0.5, 0.9), P(0.5, 0.12)]
        d.line(stem, fill=c1, width=lw * 2)
        for k in range(4):
            y = 0.25 + k * 0.16
            for sgn in (-1, 1):
                pts = [P(0.5, y + 0.08), P(0.5 + sgn * 0.18, y - 0.02), P(0.5 + sgn * 0.36, y - 0.06), P(0.5 + sgn * 0.2, y + 0.06)]
                d.polygon(pts, fill=c0, outline=c1)
        d.polygon([P(0.5, 0.04), P(0.42, 0.18), P(0.5, 0.26), P(0.58, 0.18)], fill=c0, outline=c1)
    elif kind == "anvil":
        c, cd = (226, 228, 232), (120, 124, 130)
        pts = [P(0.08, 0.3), P(0.92, 0.3), P(0.92, 0.42), P(0.68, 0.48), P(0.6, 0.62), P(0.74, 0.8), P(0.26, 0.8), P(0.4, 0.62),
               P(0.32, 0.48), P(0.2, 0.46), P(0.08, 0.38)]
        d.polygon(pts, fill=c, outline=cd)
        d.rectangle([*P(0.2, 0.8), *P(0.8, 0.88)], fill=c, outline=cd)
    elif kind == "cheese":
        c, cd, hole = (246, 210, 80), (170, 120, 30), (200, 150, 40)
        top = [P(0.12, 0.42), P(0.62, 0.2), P(0.9, 0.36), P(0.42, 0.56)]
        front = [P(0.12, 0.42), P(0.42, 0.56), P(0.42, 0.82), P(0.12, 0.7)]
        side = [P(0.42, 0.56), P(0.9, 0.36), P(0.9, 0.64), P(0.42, 0.82)]
        d.polygon(side, fill=c, outline=cd)
        d.polygon(front, fill=_scale(c, 0.86), outline=cd)
        d.polygon(top, fill=_scale(c, 1.05), outline=cd)
        for (x, y, r) in ((0.6, 0.55, 0.05), (0.76, 0.6, 0.035), (0.25, 0.62, 0.04), (0.55, 0.36, 0.03), (0.68, 0.7, 0.03)):
            cx, cy = P(x, y)
            rr = r * W * scale
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=hole)
    elif kind == "scroll":
        c, cd = (240, 228, 196), (150, 120, 80)
        d.rectangle([*P(0.22, 0.2), *P(0.78, 0.82)], fill=c, outline=cd, width=lw)
        for (y0, y1) in ((0.12, 0.24), (0.78, 0.9)):
            d.rounded_rectangle([*P(0.12, y0), *P(0.88, y1)], radius=lw * 2, fill=_scale(c, 0.92), outline=cd, width=lw)
        for k in range(5):
            y = 0.32 + k * 0.1
            d.line([P(0.3, y), P(0.7 - 0.08 * (k % 2), y)], fill=cd, width=max(1, lw // 2 + 1))
    elif kind == "lyre":
        # gold lyre: two curved arms ending in scrolls, a crossbar, a round sound box, strings
        for sgn in (-1, 1):
            arm = [P(0.5 + sgn * 0.13, 0.84), P(0.5 + sgn * 0.27, 0.74), P(0.5 + sgn * 0.33, 0.58), P(0.5 + sgn * 0.3, 0.42),
                   P(0.5 + sgn * 0.22, 0.3), P(0.5 + sgn * 0.24, 0.18), P(0.5 + sgn * 0.34, 0.12)]
            d.line(arm, fill=gold_d, width=lw * 4, joint="curve")
            d.line(arm, fill=gold, width=lw * 2 + 1, joint="curve")
            sx, sy = P(0.5 + sgn * 0.36, 0.14)
            d.ellipse([sx - lw * 2.2, sy - lw * 2.2, sx + lw * 2.2, sy + lw * 2.2], fill=gold, outline=gold_d, width=max(1, lw // 2))
        d.line([P(0.25, 0.27), P(0.75, 0.27)], fill=gold_d, width=lw * 3)
        d.line([P(0.25, 0.27), P(0.75, 0.27)], fill=gold, width=lw * 2)
        for k in range(5):
            x = 0.38 + k * 0.06
            d.line([P(x, 0.28), P(x, 0.8)], fill=(250, 232, 170), width=max(1, lw // 2 + 1))
        d.chord([*P(0.3, 0.7), *P(0.7, 0.94)], 180, 360, fill=gold, outline=gold_d, width=lw)
        d.rectangle([*P(0.32, 0.8), *P(0.68, 0.86)], fill=gold, outline=gold_d, width=max(1, lw // 2))
    elif kind == "muskets":
        # two crossed muskets (steel barrel, wooden stock with a pale outline), muzzles up
        wood, wood_d = (176, 120, 70), (96, 60, 30)
        for sgn in (1, -1):
            a, b = P(0.5 - 0.36 * sgn, 0.08), P(0.5 + 0.2 * sgn, 0.66)   # barrel: muzzle a -> breech b
            d.line([a, b], fill=silver_d, width=lw * 3)
            d.line([a, b], fill=silver, width=lw * 2)
            # stock: from the breech down to the butt (wider)
            c, e = P(0.5 + 0.3 * sgn, 0.78), P(0.5 + 0.4 * sgn, 0.92)
            d.line([b, c], fill=wood_d, width=lw * 4)
            d.line([b, c], fill=wood, width=lw * 3)
            d.polygon([P(0.5 + 0.25 * sgn, 0.8), P(0.5 + 0.36 * sgn, 0.72), P(0.5 + 0.48 * sgn, 0.9), P(0.5 + 0.38 * sgn, 0.97)],
                      fill=wood, outline=wood_d)
            tx, ty = P(0.5 + 0.2 * sgn, 0.66)
            d.ellipse([tx - lw * 1.4, ty - lw * 1.4, tx + lw * 1.4, ty + lw * 1.4], fill=silver_d)
    elif kind == "bow":
        # a gold recurve bow (arc on the left) with its string, an arrow across (white fletching)
        x0, y0 = P(0.12, 0.1)
        x1, y1 = P(0.88, 0.9)
        d.arc([x0, y0, x1 + (x1 - x0) * 0.1, y1], 112, 248, fill=gold_d, width=lw * 4)
        d.arc([x0, y0, x1 + (x1 - x0) * 0.1, y1], 112, 248, fill=gold, width=lw * 2 + 1)
        cx, cy = (x0 + x1 + (x1 - x0) * 0.1) / 2, (y0 + y1) / 2
        rx_, ry_ = (x1 + (x1 - x0) * 0.1 - x0) / 2, (y1 - y0) / 2
        ends = [(cx + rx_ * math.cos(math.radians(a)), cy + ry_ * math.sin(math.radians(a))) for a in (112, 248)]
        d.line(ends, fill=(250, 236, 190), width=max(1, lw // 2 + 1))
        # the arrow: from bottom-left (fletching) to top-right (head)
        a, b = P(0.16, 0.86), P(0.84, 0.16)
        d.line([a, b], fill=gold_d, width=lw * 2)
        d.line([a, b], fill=gold, width=lw)
        hx, hy = b
        d.polygon([(hx + lw * 3, hy - lw * 3), (hx - lw * 3.5, hy - lw * 0.5), (hx + lw * 0.5, hy + lw * 3.5)], fill=gold, outline=gold_d)
        fx, fy = P(0.2, 0.82)
        for k in range(3):
            o = k * lw * 1.6
            d.line([(fx + o, fy - o), (fx + o - lw * 3, fy - o - lw * 1)], fill=white, width=lw)
            d.line([(fx + o, fy - o), (fx + o + lw * 1, fy - o + lw * 3)], fill=white, width=lw)
    elif kind == "star":
        # a gold eight-pointed star (long and short rays) round a small ring
        cx, cy = P(0.5, 0.5)
        R0 = 0.46 * W * scale
        pts = []
        for k in range(16):
            ang = math.pi / 8 * k - math.pi / 2
            r = R0 * (1.0 if k % 4 == 0 else 0.62 if k % 2 == 0 else 0.2)
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        d.polygon(pts, fill=gold, outline=gold_d)
        for k in range(0, 16, 2):
            ang = math.pi / 8 * k - math.pi / 2
            r = R0 * (1.0 if k % 4 == 0 else 0.62)
            d.line([(cx, cy), (cx + r * math.cos(ang), cy + r * math.sin(ang))], fill=gold_d, width=max(1, lw // 2))
        r = 0.12 * W * scale
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=gold_d)
        r2 = r * 0.6
        d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=(250, 232, 170))
    elif kind == "shield":
        # a heater shield, silver rim, quartered blue / silver field
        blue, blue_d = (52, 86, 168), (26, 44, 96)
        pts = [P(0.18, 0.12), P(0.82, 0.12), P(0.82, 0.5), P(0.76, 0.68), P(0.64, 0.82), P(0.5, 0.92), P(0.36, 0.82), P(0.24, 0.68),
               P(0.18, 0.5)]
        d.polygon(pts, fill=silver)
        q = Image.new("L", (W, H), 0)
        ImageDraw.Draw(q).polygon(pts, fill=255)
        quarters = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dq = ImageDraw.Draw(quarters)
        mx, my = P(0.5, 0.48)
        dq.rectangle([0, 0, mx, my], fill=blue + (255,))
        dq.rectangle([mx, my, W, H], fill=blue + (255,))
        dq.rectangle([mx, 0, W, my], fill=(226, 230, 236, 255))
        dq.rectangle([0, my, mx, H], fill=(226, 230, 236, 255))
        im.paste(quarters, (0, 0), q)
        d.line(pts + [pts[0]], fill=silver_d, width=lw * 2)
        d.line([P(0.5, 0.12), P(0.5, 0.92)], fill=silver_d, width=lw)
        d.line([P(0.18, 0.48), P(0.82, 0.48)], fill=silver_d, width=lw)
    elif kind == "cannon":
        # two crossed cannons (pale barrels, muzzle rings, cascabel knobs) above three cannonballs
        pale, pale_d = (236, 226, 196), (130, 116, 88)
        for sgn in (1, -1):
            a, b = P(0.5 - 0.36 * sgn, 0.1), P(0.5 + 0.3 * sgn, 0.62)   # muzzle a -> breech b
            d.line([a, b], fill=pale_d, width=int(lw * 4.5))
            d.line([a, b], fill=pale, width=int(lw * 3.4))
            for t in (0.06, 0.55, 0.92):
                mx, my = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                rr = lw * (2.6 if t != 0.92 else 2.9)
                d.ellipse([mx - rr, my - rr, mx + rr, my + rr], fill=pale, outline=pale_d, width=max(1, lw // 2))
            kx, ky = P(0.5 + 0.35 * sgn, 0.66)
            d.ellipse([kx - lw * 1.5, ky - lw * 1.5, kx + lw * 1.5, ky + lw * 1.5], fill=pale, outline=pale_d)
        for (x, y) in ((0.5, 0.71), (0.4, 0.86), (0.6, 0.86)):
            cx, cy = P(x, y)
            r = 0.085 * W * scale
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=pale, outline=pale_d, width=lw)
    elif kind == "poison":
        # 1.16.0: a bone-white skull above a round flask of orange poison, a little crossed bone each side of the neck
        bone, bone_d = (236, 226, 200), (96, 72, 52)
        hole = COLOURS[colour][1]
        cx, cy = P(0.5, 0.22)
        rx_, ry_ = 0.21 * W * scale, 0.19 * H * scale
        d.ellipse([cx - rx_, cy - ry_, cx + rx_, cy + ry_], fill=bone, outline=bone_d, width=lw)
        d.rounded_rectangle([*P(0.37, 0.3), *P(0.63, 0.47)], radius=lw * 2, fill=bone, outline=bone_d, width=lw)
        d.rectangle([*P(0.36, 0.28), *P(0.64, 0.34)], fill=bone)
        for sx in (0.415, 0.585):
            ex, ey = P(sx, 0.24)
            r = 0.062 * W * scale
            d.ellipse([ex - r, ey - r * 0.95, ex + r, ey + r * 1.05], fill=hole)
        d.polygon([P(0.5, 0.31), P(0.465, 0.365), P(0.535, 0.365)], fill=hole)
        for tx in (0.44, 0.5, 0.56):
            d.line([P(tx, 0.395), P(tx, 0.465)], fill=bone_d, width=max(1, lw // 2 + 1))
        for sgn in (-1, 1):   # the small crossed bones beside the flask neck
            bx = 0.5 + sgn * 0.27
            for a, b in ((P(bx - 0.07, 0.5), P(bx + 0.07, 0.62)), (P(bx - 0.07, 0.62), P(bx + 0.07, 0.5))):
                d.line([a, b], fill=bone, width=lw * 2)
                for q in (a, b):
                    d.ellipse([q[0] - lw * 1.3, q[1] - lw * 1.3, q[0] + lw * 1.3, q[1] + lw * 1.3], fill=bone)
        glass, liquid = (226, 222, 210), (226, 128, 40)
        fx, fy = P(0.5, 0.8)
        r = 0.18 * W * scale
        d.rectangle([*P(0.45, 0.52), *P(0.55, 0.68)], fill=glass, outline=bone_d, width=lw)
        d.ellipse([fx - r, fy - r, fx + r, fy + r], fill=glass, outline=bone_d, width=lw)
        r2 = r - lw * 1.5
        d.chord([fx - r2, fy - r2, fx + r2, fy + r2], 0, 180, fill=liquid)
        d.line([(fx - r2 * 0.95, fy), (fx + r2 * 0.95, fy)], fill=(250, 180, 90), width=lw)
        d.rectangle([*P(0.435, 0.5), *P(0.565, 0.535)], fill=(150, 100, 60))
        hx, hy = P(0.42, 0.74)
        d.ellipse([hx - lw * 1.2, hy - lw * 2, hx + lw * 1.2, hy + lw * 2], fill=(255, 255, 255))
    elif kind == "cleavers":
        # 1.16.0: two crossed butcher's cleavers: broad steel blades in the two upper corners (edges outwards), the
        # wooden handles crossing below the middle
        wood, wood_d = (168, 112, 62), (88, 54, 26)
        for sgn in (-1, 1):
            tip = np.array(P(0.5 + sgn * 0.37, 0.08), dtype=float)
            end = np.array(P(0.5 - sgn * 0.3, 0.93), dtype=float)
            L = float(np.linalg.norm(end - tip))
            dd = (end - tip) / L
            n = np.array([-dd[1], dd[0]])
            if np.sign(n[0]) != sgn:
                n = -n
            bw = 0.27 * W * scale

            def Q(t, o, tip=tip, dd=dd, n=n, L=L):
                p = tip + dd * (L * t) + n * o
                return (float(p[0]), float(p[1]))
            d.line([Q(0.44, bw * 0.12), Q(1.0, bw * 0.12)], fill=wood_d, width=lw * 5)
            d.line([Q(0.44, bw * 0.12), Q(1.0, bw * 0.12)], fill=wood, width=lw * 3)
            for t in (0.62, 0.86):
                c = Q(t, bw * 0.12)
                d.ellipse([c[0] - lw, c[1] - lw, c[0] + lw, c[1] + lw], fill=silver_d)
            blade = [Q(0.0, -bw * 0.12), Q(0.46, -bw * 0.12), Q(0.46, bw * 0.55), Q(0.4, bw), Q(0.0, bw)]
            d.polygon(blade, fill=silver, outline=silver_d)
            d.line([Q(0.01, bw * 0.94), Q(0.39, bw * 0.94)], fill=(252, 252, 255), width=lw * 2)
            d.line([Q(0.0, -bw * 0.06), Q(0.46, -bw * 0.06)], fill=silver_d, width=lw)
            hc = Q(0.09, bw * 0.22)
            d.ellipse([hc[0] - lw * 1.8, hc[1] - lw * 1.8, hc[0] + lw * 1.8, hc[1] + lw * 1.8], fill=COLOURS[colour][1])
    im = im.resize((w, h), Image.LANCZOS)
    if faded:
        a = im.getchannel("A").point(lambda q: int(q * 0.55))
        im.putalpha(a)
    base = img.crop((u, v, u + w, v + h))
    base.alpha_composite(im)
    img.paste(base, (u, v))


def _banner(img, R, colour, emblem, rng):
    """Hanging banner: tent colour, gold border, V point at the bottom (cut-out), the emblem in the middle."""
    main, dark, light = COLOURS[colour]
    u, v, w, h = R
    _weave(img, R, main, rng)
    body = int(h * 0.74)
    for y in range(h):
        for x in range(w):
            if y >= body:
                half = (w / 2) * (1 - (y - body) / (h - body))
                dx = abs(x - (w - 1) / 2)
                if dx > half:
                    _px(img, R, x, y, (0, 0, 0), 0)
                    continue
                if dx > half - 3:
                    _px(img, R, x, y, _jitter(GOLD, rng, 10))
                continue
            if x < 3 or x >= w - 3 or y < 3:
                _px(img, R, x, y, _jitter(GOLD, rng, 10))
            elif x < 5 or x >= w - 5 or y < 5:
                _px(img, R, x, y, _jitter(dark, rng, 5))
    _emblem(img, (u + 6, v + int(h * 0.18), w - 12, w - 12), emblem, colour, scale=0.95)


def _flag(img, R, colour, emblem, rng):
    main, dark, light = COLOURS[colour]
    u, v, w, h = R
    _weave(img, R, main, rng)
    for y in range(h):
        for x in range(w):
            notch = x > w * 0.68 and abs(y - (h - 1) / 2) < (x - w * 0.68) * (h / 2) / (w * 0.32)
            if notch:
                _px(img, R, x, y, (0, 0, 0), 0)
            elif y < 2 or y >= h - 2 or x < 2:
                _px(img, R, x, y, _jitter(GOLD, rng, 10))
    _emblem(img, (u + 6, v + 3, h - 6, h - 6), emblem, colour, scale=0.95)


def _pennant(img, R, c, rng, edge=GOLD):
    u, v, w, h = R
    _weave(img, R, c, rng)
    for y in range(h):
        for x in range(w):
            half = (h / 2) * (1 - x / w)
            dy = abs(y - (h - 1) / 2)
            if dy > half:
                _px(img, R, x, y, (0, 0, 0), 0)
            elif dy > half - 1.5 or x < 2:
                _px(img, R, x, y, _jitter(edge, rng, 8))


def _rug(img, R, colour, emblem, rng):
    main, dark, light = COLOURS[colour]
    u, v, w, h = R
    _weave(img, R, main, rng, stains=2)
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            if e < 3:
                _px(img, R, x, y, _jitter(dark, rng, 5))
            elif e in (5, 6) or e == 11:
                _px(img, R, x, y, _jitter(GOLD, rng, 10))
            elif 7 <= e <= 10 and (x + y) % 6 < 2:
                _px(img, R, x, y, _jitter(_mix(main, GOLD, 0.5), rng, 6))
    # a medallion round the emblem
    cx, cy, r = w / 2, h / 2, h * 0.3
    for y in range(h):
        for x in range(w):
            dd = math.hypot((x - cx) / 1.25, y - cy)
            if abs(dd - r) < 1.0:
                _px(img, R, x, y, _jitter(GOLD, rng, 10))
    s = int(h * 0.42)
    _emblem(img, (u + int(cx - s / 2), v + int(cy - s / 2), s, s), emblem, colour, scale=1.0, faded=True)


def _counter(img, R, rng):
    """Counter front panel: vertical planks, a dark frame, iron corner brackets."""
    fine_wood(img, R, _rgb("8a6038"), _rgb("442a12"), 8, rng, joints=False, knots=0.1, grain=0.1, shade=0.08, vertical=True)
    u, v, w, h = R
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            if e < 3:
                _px(img, R, x, y, _jitter(_rgb("4a301a"), rng, 5))
            if (x < 6 or x >= w - 6) and (y < 6 or y >= h - 6) and e < 3:
                _px(img, R, x, y, _jitter(_rgb("3a3a40"), rng, 6))
    for (x, y) in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)):
        _px(img, R, x, y, (150, 150, 156))


def _cutout_bunch(img, R, cols, rng, stem=(110, 84, 50)):
    """A hanging bunch (cut-out): a string at the top, stems, leaves in `cols`, narrowing upwards."""
    _clear(img, R)
    u, v, w, h = R
    for y in range(0, 4):
        _px(img, R, w // 2, y, (170, 140, 90))
    for k in range(9):
        x0 = w / 2 + rng.uniform(-3, 3)
        x1 = w / 2 + rng.uniform(-w * 0.42, w * 0.42)
        for i in range(h - 4):
            t = i / (h - 5)
            x = int(round(x0 + (x1 - x0) * t))
            y = 3 + i
            if 0 <= x < w:
                _px(img, R, x, y, stem)
            if i > 4 and rng.random() < 0.55:
                for dx in (-1, 0, 1):
                    xx = x + dx + rng.choice((-1, 1))
                    if 0 <= xx < w:
                        _px(img, R, xx, y, _jitter(rng.choice(cols), rng, 10))


def _ivy(img, R, rng):
    _clear(img, R)
    u, v, w, h = R
    greens = [_rgb("2e5a1e"), _rgb("3e7228"), _rgb("4f8a32"), _rgb("2a4a1a")]
    for k in range(5):
        x = rng.randint(3, w - 4)
        length = rng.randint(h // 2, h)
        for y in range(length):
            x += rng.choice((-1, 0, 0, 1))
            x = max(1, min(w - 2, x))
            _px(img, R, x, y, (70, 60, 30))
            if rng.random() < 0.6:
                for dx in range(-2, 3):
                    for dy in range(-1, 2):
                        if abs(dx) + abs(dy) < 3 and 0 <= x + dx < w and 0 <= y + dy < h and rng.random() < 0.8:
                            _px(img, R, x + dx, y + dy, _jitter(rng.choice(greens), rng, 8))


def _potion(img, R, c, rng):
    u, v, w, h = R
    for y in range(h):
        for x in range(w):
            dd = math.hypot(x - 6, y - 6) / 11
            k = 1.25 - 0.55 * dd
            col = _scale(c, k)
            if 3 <= x <= 4 and 3 <= y <= 6:
                col = _mix(col, (255, 255, 255), 0.6)
            _px(img, R, x, y, _jitter(col, rng, 4))


def _wicker(img, R, rng, base=_rgb("b48a52")):
    u, v, w, h = R
    for y in range(h):
        for x in range(w):
            k = 1.0 + (0.14 if ((x // 3) + (y // 3)) % 2 == 0 else -0.12) + (0.1 if y % 3 == 0 else 0)
            _px(img, R, x, y, _jitter(_scale(base, k), rng, 6))


def _heap(img, R, cols, rng, bg=_rgb("6a4a28"), r=3):
    """A heap of round produce seen from above (apples, vegetables...)."""
    _fill(img, R, bg, rng)
    u, v, w, h = R
    for k in range(int(w * h / (r * r * 2.2))):
        cx, cy, c = rng.uniform(0, w), rng.uniform(0, h), rng.choice(cols)
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                d = math.hypot(x - cx, y - cy)
                if d <= r and 0 <= x < w and 0 <= y < h:
                    k = 1.2 - 0.5 * d / r - (0.15 if (x - cx) + (y - cy) > 0 else 0)
                    _px(img, R, x, y, _jitter(_scale(c, k), rng, 5))


def _cloth_hang(img, R, colour, rng):
    main, dark, light = COLOURS[colour]
    u, v, w, h = R
    _weave(img, R, main, rng)
    for y in range(h):
        for x in range(w):
            if h - 9 <= y < h - 6:
                _px(img, R, x, y, _jitter(GOLD, rng, 10))
            elif y >= h - 6:
                if x % 3 == 2 or (y >= h - 2 and x % 3 == 1):
                    _px(img, R, x, y, (0, 0, 0), 0)
                else:
                    _px(img, R, x, y, _jitter(GOLD, rng, 14))


def _shield(img, R, rng):
    """A blank heater shield outline (iron rim), the field left for the tent to paint over (cut-out outside)."""
    u, v, w, h = R
    for y in range(h):
        for x in range(w):
            t = y / (h - 1)
            half = (w / 2) * (1.0 if t < 0.5 else math.sqrt(max(0.0, 1 - ((t - 0.5) / 0.5) ** 2)))
            dx = abs(x - (w - 1) / 2)
            if dx > half:
                _px(img, R, x, y, (0, 0, 0), 0)
            elif dx > half - 2 or y < 2:
                _px(img, R, x, y, _jitter(_rgb("8a8c92"), rng, 8))
            else:
                _px(img, R, x, y, _jitter(_rgb("a42a24"), rng, 6))


def _paint_shell(img, R, colour, emblem, banner_colour=None, rug_colour=None):
    rng = random.Random(1140 + _SEED[colour])
    main, dark, light = COLOURS[colour]
    fine_wood(img, R["wood"], _rgb("8a6038"), _rgb("442a12"), 4, rng, joints=True, knots=0.15, grain=0.11, shade=0.06)
    fine_wood(img, R["wood_dark"], _rgb("5a3c22"), _rgb("24160a"), 4, rng, joints=False, knots=0.1, grain=0.12, shade=0.06)
    fine_wood(img, R["plank"], _rgb("9c7246"), _rgb("4e3218"), 4, rng, joints=True, knots=0.15, grain=0.1, shade=0.08)
    fine_wood(img, R["plank_dark"], _rgb("6a4628"), _rgb("2e1c0a"), 4, rng, joints=True, knots=0.15, grain=0.1, shade=0.08)
    _carved(img, R["post"], _rgb("5e3e22"), _rgb("261608"), rng)
    _carved(img, R["beam"], _rgb("6a4628"), _rgb("2a1a0a"), rng)
    tt._fill(img, R["leather"], _rgb("7a4a26"), rng, noise=7)
    tt._fill(img, R["leather_dark"], _rgb("4a2a16"), rng, noise=7)
    polished_metal(img, R["trim_gold"], GOLD_STOPS, rng, fx=0.6, fy=0.4)
    end_grain(img, R["end_grain"], _rgb("8a6038"), _rgb("4a3018"), rng)
    twisted_rope(img, R["rope"], _rgb("c9ad7a"), _rgb("6e5634"), rng)
    hammered_iron(img, R["iron"], _rgb("3c3c42"), rng)
    polished_metal(img, R["gold"], GOLD_STOPS, rng)
    u, v, w, h = R["lantern"]
    paint_lamp_glass(img.load(), u, v, w, h)
    _fill(img, R["glow"], _rgb("ffd27a"), rng)
    polished_metal(img, R["brass"], wta.BRASS_STOPS, rng)
    polished_metal(img, R["steel"], STEEL_STOPS, rng, fx=0.3, fy=0.5)
    _fill(img, R["white"], _rgb("ece6d8"), rng, noise=3)
    hammered_iron(img, R["black_iron"], _rgb("2a2a2e"), rng, dent=0.09)
    _fill(img, R["flame"], _rgb("ffcf6a"), rng, noise=10)
    _fill(img, R["glass"], _rgb("b9d4dc"), rng, noise=5)
    _fill(img, R["cork"], _rgb("a87c50"), rng)
    _fill(img, R["wax"], _rgb("e8dcc0"), rng, noise=4)
    polished_metal(img, R["ingot"], STEEL_STOPS, rng, fx=0.6, fy=0.4)
    polished_metal(img, R["gold_ingot"], GOLD_STOPS, rng, fx=0.6, fy=0.4)
    _fill(img, R["coal"], _rgb("222222"), rng, noise=10)
    u, v, w, h = R["embers"]
    for y in range(h):
        for x in range(w):
            _px(img, R["embers"], x, y, _jitter(_mix(_rgb("ffb040"), _rgb("b02a10"), rng.random()), rng, 10))
    _fill(img, R["stone"], _rgb("7a7672"), rng, noise=12)
    _fill(img, R["stone_top"], _rgb("8a8680"), rng, noise=8)
    for n, c in POTIONS.items():
        _potion(img, R["potion_" + n], _rgb(c), rng)
    _weave(img, R["cloth_red"], _rgb("9a2a22"), rng)
    _weave(img, R["cloth_blue"], _rgb("2f4f86"), rng)
    _weave(img, R["cloth_white"], _rgb("e4ddcc"), rng)
    _weave(img, R["cloth_dark"], _rgb("3a3030"), rng)
    wta._banded(img, R["crate"], _rgb("94683a"), _rgb("4e3218"), rng)
    wta._banded(img, R["crate_top"], _rgb("8a6036"), _rgb("4a2e16"), rng, bands=(0, 1, 30, 31), vertical_bands=(0, 1, 15, 16, 30, 31))
    fine_wood(img, R["barrel"], _rgb("8e5e34"), _rgb("4a3018"), 4, rng, joints=False, knots=0.08, grain=0.1, shade=0.08, vertical=True)
    for y in (3, 4, 14, 15, 26, 27):
        for x in range(32):
            _px(img, R["barrel"], x, y, _jitter(_rgb("3a3a3e"), rng, 5))
    fine_wood(img, R["barrel_top"], _rgb("9a6a3e"), _rgb("4a3018"), 6, rng, joints=False, knots=0.0, grain=0.1, shade=0.05)
    for x in range(32):
        for y in (0, 1, 30, 31):
            _px(img, R["barrel_top"], x, y, _rgb("3a3a3e"))
            _px(img, R["barrel_top"], y, x, _rgb("3a3a3e"))
    _weave(img, R["sack"], _rgb("a89060"), rng, stains=3)
    _wicker(img, R["basket"], rng)
    _wicker(img, R["basket_top"], rng, base=_rgb("8a6a3a"))
    tt._straw(img, R["straw"], rng)
    _cutout_bunch(img, R["herbs"], [_rgb("4a7a2e"), _rgb("5e9238"), _rgb("3a6224")], rng)
    _cutout_bunch(img, R["herbs_dry"], [_rgb("8a6a2e"), _rgb("a07a3a"), _rgb("7a4a2a"), _rgb("6a7a3a")], rng)
    _ivy(img, R["ivy"], rng)
    _weave(img, R["cloth"], main, rng)
    _weave(img, R["cloth_beige"], BEIGE, rng)
    _cloth_hang(img, R["cloth_hang"], colour, rng)
    _heap(img, R["apples"], [_rgb("c42a22"), _rgb("a81e1a"), _rgb("d8482a"), _rgb("8aa030")], rng)
    _heap(img, R["produce"], [_rgb("e07a20"), _rgb("c42a22"), _rgb("6a9a30"), _rgb("d8c050"), _rgb("8a4a8a")], rng)
    _weave(img, R["canvas"], main, rng, seams=16, seam_dir="v", stains=3)
    _weave(img, R["beige"], BEIGE, rng, seams=16, seam_dir="v", stains=2)
    _stripes_roof(img, R["roof"], colour, rng)
    _valance(img, R["valance"], colour, rng)
    _weave(img, R["wall"], _scale(main, 0.82), rng, seams=21, seam_dir="v", stains=4, patches=1)
    _counter(img, R["counter"], rng)
    _banner(img, R["banner"], banner_colour or colour, emblem, rng)
    _flag(img, R["flag"], banner_colour or colour, emblem, rng)
    _pennant(img, R["pennant"], COLOURS[banner_colour][0] if banner_colour else main, rng)
    _pennant(img, R["pennant_beige"], BEIGE, rng)
    _rug(img, R["rug"], rug_colour or colour, emblem, rng)
    _shield(img, R["shield"], rng)


# ---------------------------------------------------------------- geometry helpers
def box(bone, name, lo, hi, region, solid=False, stretch=False, u_dir=None, v_dir=None):
    """An axis-aligned box from lo to hi (tent-local); collides when solid."""
    lo, hi = v3(*lo), v3(*hi)
    c = add_cube(bone, name, (lo + hi) / 2, EYE, hi - lo, region, stretch=stretch, u_dir=u_dir, v_dir=v_dir)
    if solid:
        collide((lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]))
    return c


def rbox(bone, name, foot, size, yaw, region, solid=False, stretch=False):
    """A box standing on `foot` (bottom centre), turned by yaw (radians) about y; collides (its bounding box) when solid."""
    foot = v3(*foot)
    c = add_cube(bone, name, foot + UP * size[1] / 2, ry(yaw), size, region, stretch=stretch)
    if solid:
        hx, hz = size[0] / 2, size[2] / 2
        ex = abs(math.cos(yaw)) * hx + abs(math.sin(yaw)) * hz
        ez = abs(math.sin(yaw)) * hx + abs(math.cos(yaw)) * hz
        collide((foot[0] - ex, foot[1], foot[2] - ez, foot[0] + ex, foot[1] + size[1], foot[2] + ez))
    return c


def octo(bone, name, foot, r, h, region, yaw=0.0, stretch=True):
    """An upright octagonal prism (two boxes turned 45 degrees) of radius r, height h, standing on foot."""
    foot = v3(*foot)
    for k, a in enumerate((yaw, yaw + math.pi / 4)):
        add_cube(bone, "%s_%d" % (name, k), foot + UP * h / 2, ry(a), (2 * r * 0.83, h, 2 * r * 0.83), region, stretch=stretch)


def plate(bone, name, center, w, h, region, normal=(0, 0, 1), up=(0, 1, 0), th=0.02, edge=None):
    """A thin flat thing (both faces `region`, u to the viewer's right, v down), edges `edge` (None: none)."""
    n = norm(v3(*normal))
    upv = v3(*up)
    upv = norm(upv - np.dot(upv, n) * n)
    u = np.cross(upv, n)
    axes = np.column_stack([u, upv, n])
    return add_cube(bone, name, center, axes, (w, h, th), {"all": edge, "+3": region, "-3": region}, stretch=True,
                    u_dir=u, v_dir=-upv)


def lantern(bone, name, p, size=0.3, metal="iron", chain_to=None):
    """A lantern body at p (rebuilt lit on export) and its chain up to chain_to (tentlib.lantern)."""
    return tl.lantern(bone, name, p, size=size, metal=metal, chain_to=chain_to)


def banner(bone, name, top_center, w, h, normal=(0, 0, 1), region="banner", rod=True, wave=0.04, rod_region="wood_dark",
           knobs="gold"):
    """A hanging banner (both faces, cut-out point) from a rod: top_center = the middle of its top edge; normal = the
    side it faces (it reads unmirrored from there)."""
    top = v3(*top_center)
    n = norm(v3(*normal))
    side = norm(np.cross(UP, n))

    def P(s, t):
        return top + side * ((s - 0.5) * w) - UP * (h * t) + n * (wave * math.sin(math.pi * t) * (0.6 + 0.4 * math.sin(math.pi * s)))
    loft(bone, name, P, 1, 3, region, th=0.02, u_hint=side, v_hint=-UP)
    if rod:
        a, b = top - side * (w / 2 + 0.1) + n * 0.02 + UP * 0.03, top + side * (w / 2 + 0.1) + n * 0.02 + UP * 0.03
        beam(bone, name + "_rod", a, b, 0.06, rod_region, width=0.06)
        if knobs:
            for k, p in enumerate((a, b)):
                add_cube(bone, "%s_knob_%d" % (name, k), p, EYE, (0.09, 0.09, 0.09), knobs)


def rug(bone, name, x0, x1, z0, z1, y=0.0, region="rug", th=0.03):
    """A rug lying on the ground (its texture reads from the front: top of the texture at -z)."""
    return add_cube(bone, name, ((x0 + x1) / 2, y + th / 2, (z0 + z1) / 2), EYE, (x1 - x0, th, z1 - z0),
                    {"all": "cloth", "+2": region, "-2": None}, stretch=True, u_dir=X, v_dir=Z)


def vine(bone, name, top, length, width, normal=(0, 0, 1), region="ivy"):
    """A hanging strip of ivy / vines (cut-out plane, both faces) from `top`, facing `normal`."""
    top = v3(*top)
    return plate(bone, name, top - UP * length / 2, width, length, region, normal=normal, th=0.004)


def crossed(bone, name, center, w, h, region, glow=False, yaw=0.0):
    """Two crossed cut-out planes (plants, bunches) of size w x h centred at center."""
    center = v3(*center)
    pre = "glow_" if glow else ""
    for k, a in enumerate((yaw + math.pi / 4, yaw - math.pi / 4)):
        R = ry(a)
        add_cube(bone, "%s%s_%d" % (pre, name, k), center, R, (w, h, 0.004), {"all": None, "+3": region, "-3": region}, stretch=True,
                 u_dir=R[:, 0], v_dir=-UP)


# ---------------------------------------------------------------- small props
def barrel(bone, name, foot, r=0.34, h=0.85, staves=8, axis="y", content=None, solid=True):
    """An iron-hooped barrel (cartlib geometry): standing (axis y) or lying (x / z, foot = centre of one end);
    content = a region shown filling the open top (apples, produce...) of a standing barrel."""
    cl.barrel(bone, name, foot, r=r, h=h, staves=staves, axis=axis, solid=solid)
    if content and axis == "y":
        foot = v3(*foot)
        for k, a in enumerate((0.0, math.pi / 4)):
            add_cube(bone, "%s_content_%d" % (name, k), foot + UP * (h - 0.02), ry(a), (2 * r * 0.8, 0.08, 2 * r * 0.8 * 0.42 * 2 ** 0.5),
                     {"all": content}, stretch=True)


def crate(bone, name, foot, size=0.7, yaw=0.0, region="crate", top="crate_top", content=None, solid=True):
    """An iron-banded crate standing on foot (size: a float = cube, or (w, h, d)); content = a region heaped in the
    open top (apples, produce, straw...)."""
    if not hasattr(size, "__len__"):
        size = (size, size, size)
    foot = v3(*foot)
    c = rbox(bone, name, foot, size, yaw, {"all": region, "+2": top if content is None else region, "-2": top}, solid=solid, stretch=True)
    if content:
        rbox(bone, name + "_content", foot + UP * (size[1] - 0.06), (size[0] * 0.9, 0.1, size[2] * 0.9), yaw, {"all": content}, stretch=True)
    return c


def sack(bone, name, foot, s=0.45, yaw=0.0, region="sack", solid=False):
    """A tied sack (bulging body, gathered neck, rope tie)."""
    foot = v3(*foot)
    R = ry(yaw)
    add_cube(bone, name, foot + UP * s * 0.45, R, (s, s * 0.9, s * 0.82), region, stretch=True)
    add_cube(bone, name + "_top", foot + UP * s * 0.98, R @ ry(0.3), (s * 0.7, s * 0.18, s * 0.6), region, stretch=True)
    add_cube(bone, name + "_neck", foot + UP * s * 1.14, R, (s * 0.3, s * 0.16, s * 0.3), region, stretch=True)
    add_cube(bone, name + "_tie", foot + UP * s * 1.1, R, (s * 0.34, 0.04, s * 0.34), "rope")
    if solid:
        collide((foot[0] - s / 2, foot[1], foot[2] - s / 2, foot[0] + s / 2, foot[1] + s, foot[2] + s / 2))


def basket(bone, name, foot, r=0.26, h=0.22, content=None, handle=True, solid=False):
    """A wicker basket (octagonal), filled with `content` (a region, e.g. "apples") or empty, with a handle."""
    foot = v3(*foot)
    octo(bone, name, foot, r, h, {"all": "basket", "+2": content or "basket_top", "-2": "basket"})
    if handle:
        for k, (a, b) in enumerate(((v3(-r * 0.8, h, 0), v3(-r * 0.5, h + r * 0.7, 0)), (v3(-r * 0.5, h + r * 0.7, 0), v3(r * 0.5, h + r * 0.7, 0)),
                                    (v3(r * 0.5, h + r * 0.7, 0), v3(r * 0.8, h, 0)))):
            beam(bone, "%s_handle_%d" % (name, k), foot + a, foot + b, 0.035, "basket", extend=0.015)
    if solid:
        collide((foot[0] - r, foot[1], foot[2] - r, foot[0] + r, foot[1] + h, foot[2] + r))


def bottle(bone, name, foot, colour="red", r=0.06, h=0.15, neck_h=0.06, shape="round", glow=False, cork=True):
    """A potion bottle (regions potion_<colour>: red, blue, green, purple, yellow, orange, pink, cyan): body (round:
    octagonal, tall: square, flask: wide and low), glass neck, cork. glow = drawn full bright."""
    foot = v3(*foot)
    reg = "potion_" + colour if ("potion_" + colour) in gg.REGIONS else colour
    pre = "glow_" if glow else ""
    if shape == "tall":
        add_cube(bone, pre + name, foot + UP * h / 2, EYE, (2 * r, h, 2 * r), {"all": reg}, stretch=True)
    else:
        if shape == "flask":
            h, r = h * 0.75, r * 1.3
        octo(bone, pre + name, foot, r, h, {"all": reg})
    add_cube(bone, name + "_neck", foot + UP * (h + neck_h / 2), EYE, (r * 0.7, neck_h, r * 0.7), "glass", stretch=True)
    if cork:
        add_cube(bone, name + "_cork", foot + UP * (h + neck_h + 0.02), EYE, (r * 0.8, 0.04, r * 0.8), "cork", stretch=True)


def hanging_bunch(bone, name, top, kind="herbs", length=0.5, width=0.28, string=0.08):
    """A bunch (regions herbs, herbs_dry, or your own cut-out) hanging from `top` on a string of `string` length."""
    top = v3(*top)
    if string > 0:
        beam(bone, name + "_string", top, top - UP * (string + 0.04), 0.02, "rope")
    crossed(bone, name, top - UP * (string + length / 2), width, length, kind)


def sword(bone, name, base, up=(0, 1, 0), facing=(0, 0, 1), length=1.0, blade="steel", hilt="gold", grip="leather"):
    """A sword from `base` (the pommel end) along `up`: grip, crossguard, blade, tip; the flat faces `facing`."""
    base, d = v3(*base), norm(v3(*up))
    f = norm(v3(*facing) - np.dot(v3(*facing), d) * d)
    side = np.cross(d, f)
    axes = np.column_stack([side, d, f])
    gl, bl = length * 0.2, length * 0.74
    add_cube(bone, name + "_pommel", base + d * 0.03, axes, (0.07, 0.06, 0.07), hilt)
    add_cube(bone, name + "_grip", base + d * (0.06 + gl / 2), axes, (0.045, gl, 0.045), grip)
    add_cube(bone, name + "_guard", base + d * (0.06 + gl + 0.025), axes, (0.26, 0.05, 0.06), hilt)
    add_cube(bone, name + "_blade", base + d * (0.11 + gl + bl / 2), axes, (0.08, bl, 0.02), blade, stretch=True)
    add_cube(bone, name + "_tip", base + d * (0.11 + gl + bl + 0.03), axes @ rz(math.pi / 4)[:3, :3], (0.055, 0.055, 0.018), blade)


def axe(bone, name, base, up=(0, 1, 0), facing=(0, 0, 1), length=1.1, head="steel"):
    """A long axe from `base` (the butt) along `up`: wooden haft, a steel head (blade towards `facing` x up)."""
    base, d = v3(*base), norm(v3(*up))
    f = norm(v3(*facing) - np.dot(v3(*facing), d) * d)
    side = np.cross(d, f)
    beam(bone, name + "_haft", base, base + d * length, 0.05, "wood_dark")
    axes = np.column_stack([side, d, f])
    add_cube(bone, name + "_head", base + d * (length - 0.14) + side * 0.1, axes, (0.2, 0.24, 0.025), head, stretch=True)
    add_cube(bone, name + "_edge", base + d * (length - 0.14) + side * 0.21, axes, (0.04, 0.32, 0.03), head, stretch=True)


def spear(bone, name, base, up=(0, 1, 0), length=2.0, head="steel"):
    """A spear / halberd shaft from `base` along `up` with a diamond steel head."""
    base, d = v3(*base), norm(v3(*up))
    beam(bone, name + "_shaft", base, base + d * length, 0.045, "wood")
    tip = base + d * (length + 0.12)
    beam(bone, name + "_head", base + d * (length - 0.04), tip, 0.08, head, width=0.02, up=X)
    add_cube(bone, name + "_ring", base + d * (length - 0.05), EYE, (0.07, 0.04, 0.07), "iron")


def weapon_rack(bone, name, p0, p1, h=1.7, normal=(0, 0, 1), items=("sword", "axe", "sword", "spear", "sword"), detail=None,
                solid=True):
    """A wooden weapon rack standing from ground point p0 to p1 (its two uprights), the weapons on its `normal` side:
    items in turn ("sword", "axe", "spear", or None for an empty slot), standing in the rack. Collides as a thin wall."""
    p0, p1 = v3(*p0), v3(*p1)
    n = norm(v3(*normal))
    det = detail if detail is not None else bone
    for k, p in enumerate((p0, p1)):
        beam(bone, "%s_up_%d" % (name, k), p, p + UP * h, 0.1, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    for k, y in enumerate((0.18, h * 0.62, h - 0.06)):
        beam(bone, "%s_rail_%d" % (name, k), p0 + UP * y + n * 0.05, p1 + UP * y + n * 0.05, 0.07, "wood", width=0.1, extend=0.06)
    nI = len(items)
    for i, it in enumerate(items):
        if it is None:
            continue
        t = (i + 0.5) / nI
        b = p0 + (p1 - p0) * t + n * 0.12
        nm = "%s_%s_%d" % (name, it, i)
        if it == "sword":
            sword(det, nm, b + UP * (h * 0.62 + 0.2), up=(0, -1, 0), facing=n, length=min(1.0, h * 0.62 + 0.1))
        elif it == "axe":
            axe(det, nm, b + UP * 0.12, facing=n, length=min(1.3, h - 0.25))
        elif it == "spear":
            spear(det, nm, b + UP * 0.12, length=h + 0.2)
        else:
            raise KeyError(it)
    if solid:
        lo, hi = np.minimum(p0, p1), np.maximum(p0, p1)
        collide((lo[0] - 0.08 + min(0, n[0]) * 0.1, 0.0, lo[2] - 0.08 + min(0, n[2]) * 0.1,
                 hi[0] + 0.08 + max(0, n[0]) * 0.15, h, hi[2] + 0.08 + max(0, n[2]) * 0.15))


def counter(bone, name, x0, x1, z0, z1, h=1.0, detail=None, solid=True):
    """A wooden counter (panelled body, overhanging plank top, dark corner posts); returns its top surface box
    (x0, y, z0, x1, y, z1)."""
    det = detail if detail is not None else bone
    top_th = 0.1
    along_x = (x1 - x0) >= (z1 - z0)
    box(bone, name + "_body", (x0 + 0.05, 0.0, z0 + 0.05), (x1 - 0.05, h - top_th, z1 - 0.05),
        {"all": "counter", "+2": None, "-2": None}, stretch=True)
    box(bone, name + "_top", (x0 - 0.04, h - top_th, z0 - 0.04), (x1 + 0.04, h, z1 + 0.04), {"all": "plank"},
        u_dir=X if along_x else Z)
    for k, (x, z) in enumerate(((x0, z0), (x1, z0), (x0, z1), (x1, z1))):
        cx, cz = x + (0.05 if x == x0 else -0.05), z + (0.05 if z == z0 else -0.05)
        box(det, "%s_leg_%d" % (name, k), (cx - 0.06, 0.0, cz - 0.06), (cx + 0.06, h - top_th, cz + 0.06), "wood_dark")
    box(det, name + "_kick", (x0 + 0.02, 0.0, z0 + 0.02), (x1 - 0.02, 0.1, z1 - 0.02), "wood_dark")
    if solid:
        collide((x0 - 0.04, 0.0, z0 - 0.04, x1 + 0.04, h, z1 + 0.04))
    return (x0 - 0.04, h, z0 - 0.04, x1 + 0.04, h, z1 + 0.04)


def shelf_unit(bone, name, x0, x1, z_back, z_front, levels=(0.5, 1.1, 1.7, 2.3), h=2.6, back=True, uprights=4, detail=None, solid=True):
    """A wooden shelf unit along x (boards at the `levels` heights, uprights, a back panel); returns the shelf levels
    [(x0, x1, y_top_of_board, z_front, z_back)]."""
    out = []
    th = 0.06
    for k, y in enumerate(levels):
        box(bone, "%s_board_%d" % (name, k), (x0, y - th, z_back), (x1, y, z_front), "plank", u_dir=X)
        out.append((x0 + 0.06, x1 - 0.06, y, z_front, z_back))
    for k in range(uprights):
        x = x0 + (x1 - x0) * k / (uprights - 1)
        x = min(max(x, x0 + 0.05), x1 - 0.05)
        box(bone, "%s_up_%d" % (name, k), (x - 0.05, 0.0, z_back - 0.02), (x + 0.05, h, z_front + 0.02),
            {"all": "wood_dark", "+2": "end_grain"})
    box(bone, name + "_cornice", (x0 - 0.05, h, z_back - 0.04), (x1 + 0.05, h + 0.1, z_front + 0.05), "wood_dark", u_dir=X)
    if back:
        box(bone, name + "_back", (x0, 0.0, z_back - 0.03), (x1, h, z_back), "plank_dark", u_dir=UP)
    if solid:
        collide((x0 - 0.05, 0.0, z_back - 0.04, x1 + 0.05, h, z_front + 0.03))
    return out


def table_cloth(bone, name, x0, x1, z0, z1, y, hang=0.35, region="cloth", edge="cloth_hang", sides=("front",)):
    """A cloth over a counter top at height y: the top sheet and hanging flaps (sides among front, back, left,
    right; the flap region `edge` hangs `hang` down)."""
    box(bone, name, (x0, y, z0), (x1, y + 0.015, z1), {"all": region}, stretch=True, u_dir=X)
    for s in sides:
        if s == "front":
            c, w, n = v3((x0 + x1) / 2, y - hang / 2 + 0.01, z1 + 0.012), x1 - x0, Z
        elif s == "back":
            c, w, n = v3((x0 + x1) / 2, y - hang / 2 + 0.01, z0 - 0.012), x1 - x0, -Z
        elif s == "left":
            c, w, n = v3(x0 - 0.012, y - hang / 2 + 0.01, (z0 + z1) / 2), z1 - z0, -X
        else:
            c, w, n = v3(x1 + 0.012, y - hang / 2 + 0.01, (z0 + z1) / 2), z1 - z0, X
        plate(bone, "%s_%s" % (name, s), c, w + 0.02, hang + 0.02, edge, normal=n, th=0.012, edge=region)


# ---------------------------------------------------------------- the pavilion
class Layout:
    pass


def _post(bone, det, name, x, z, eave_y, ivy):
    top = eave_y + 0.75
    box(bone, name + "_plinth", (x - 0.28, 0.0, z - 0.28), (x + 0.28, 0.3, z + 0.28), {"all": "wood_dark", "+2": "end_grain"})
    beam(bone, name, (x, 0.3, z), (x, top, z), 0.36, {"all": "post", "+1": "end_grain", "-1": "end_grain"})
    for k, y in enumerate((0.26, 1.2, 2.35)):
        box(det, "%s_band_%d" % (name, k), (x - 0.205, y, z - 0.205), (x + 0.205, y + 0.08, z + 0.205), "iron")
    box(bone, name + "_capital", (x - 0.25, eave_y - 0.5, z - 0.25), (x + 0.25, eave_y - 0.34, z + 0.25), {"all": "wood_dark", "+2": "end_grain"})
    box(bone, name + "_cap", (x - 0.24, top, z - 0.24), (x + 0.24, top + 0.1, z + 0.24), "iron")
    octo(det, name + "_finial", (x, top + 0.1, z), 0.09, 0.14, "gold")
    add_cube(det, name + "_finial_tip", (x, top + 0.3, z), ry(math.pi / 4) @ rx(math.pi / 4), (0.1, 0.1, 0.1), "gold")
    collide((x - 0.2, 0.0, z - 0.2, x + 0.2, eave_y, z + 0.2))
    if ivy:
        for k, (dx, dz) in enumerate(((0.19, 0), (-0.19, 0), (0, 0.19), (0, -0.19))):
            vine(det, "%s_ivy_%d" % (name, k), (x + dx * 1.02, eave_y - 0.3 - 0.4 * (k % 2), z + dz * 1.02), 1.4 + 0.5 * (k % 2), 0.34,
                 normal=(np.sign(dx), 0, np.sign(dz)))
    return top


def pavilion(root, atlas, emblem="swords", flag_corner="back_left", side_banners=0, rug=True, lanterns=2, front_counter=True,
             back_shelves=True, ivy=False, half_w=3.1, half_d=2.8, eave_y=3.4, apex_y=6.6, roof_rise=None, flags=True, roof="pointed",
             **stall_kw):
    """Builds the shared shell (see the module doc) and returns its Layout. roof_rise (blocks, optional): the apex
    height above the eaves (overrides apex_y = eave_y + roof_rise; default 3.2), e.g. 2.2 for a lower, flatter roof.
    1.16.0: flags=False drops the flag poles, flags and pennants; roof="gable" builds the gabled market stall instead
    (stall(): ridge along x, no flags, no rug unless asked; the stall's own options may be passed as keywords)."""
    if roof == "gable":
        kw = dict(emblem=emblem, lanterns=lanterns, front_counter=front_counter, back_shelves=back_shelves, ivy=ivy,
                  half_w=half_w, rug=rug)
        if roof_rise is not None:
            kw["roof_rise"] = roof_rise
        kw.update(stall_kw)
        return stall(root, atlas, **kw)
    if roof != "pointed":
        raise KeyError("roof must be pointed or gable")
    if roof_rise is not None:
        apex_y = eave_y + float(roof_rise)
    if emblem not in EMBLEMS:
        raise KeyError("emblem must be one of %s" % ", ".join(EMBLEMS))
    atlas.emblem = emblem
    L = Layout()
    L.atlas, L.colour, L.emblem = atlas, atlas.colour, emblem
    L.half_w, L.half_d, L.eave_y, L.apex_y = half_w, half_d, eave_y, apex_y
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)
    L.shell, L.detail = shell, det
    hw, hd = half_w, half_d
    # ---- posts and beams
    corners = [(-hw, hd), (hw, hd), (hw, -hd), (-hw, -hd)]
    tops = {}
    for k, (x, z) in enumerate(corners):
        tops[k] = _post(shell, det, "post_%d" % k, x, z, eave_y, ivy)
    by = eave_y - 0.17
    for k in range(4):
        (xa, za), (xb, zb) = corners[k], corners[(k + 1) % 4]
        beam(shell, "eave_%d" % k, (xa, by, za), (xb, by, zb), 0.32, {"all": "beam", "+1": "end_grain", "-1": "end_grain"}, width=0.26,
             extend=0.12)
    # knee braces: front and the two sides
    for k, (p, q) in enumerate((((-hw + 0.16, eave_y - 1.15, hd), (-hw + 0.95, by - 0.12, hd)), ((hw - 0.16, eave_y - 1.15, hd), (hw - 0.95, by - 0.12, hd)),
                                ((-hw, eave_y - 1.15, hd - 0.16), (-hw, by - 0.12, hd - 0.95)), ((hw, eave_y - 1.15, hd - 0.16), (hw, by - 0.12, hd - 0.95)),
                                ((-hw, eave_y - 1.15, -hd + 0.16), (-hw, by - 0.12, -hd + 0.95)), ((hw, eave_y - 1.15, -hd + 0.16), (hw, by - 0.12, -hd + 0.95)))):
        beam(shell, "brace_%d" % k, p, q, 0.14, "wood_dark", extend=0.05)
    # ---- roof: 4 concave sides, 6 stripes each
    ov = 0.34
    W, D = hw + ov, hd + ov
    ey = eave_y + 0.02
    apex = v3(0, apex_y, 0)
    rc = [v3(-W, ey, D), v3(W, ey, D), v3(W, ey, -D), v3(-W, ey, -D)]
    outs = [Z, X, -Z, -X]

    def roof_point(c0, c1, s, t, droop=0.1):
        e = c0 + (c1 - c0) * s
        dd = 0.4 * t + 0.6 * (1 - (1 - t) ** 2)
        p = apex * (1 - t) + e * t
        p[1] = apex_y - (apex_y - ey) * dd - droop * math.sin(math.pi * s) * math.sin(math.pi * t)
        return p

    for k in range(4):
        c0, c1 = rc[k], rc[(k + 1) % 4]
        loft(shell, "roof_%d" % k, lambda s, t, c0=c0, c1=c1: roof_point(c0, c1, s, t), 6, 8, "roof", th=0.04)
        # the valance: dagged tabs hanging from the roof edge, flaring out a little
        o = outs[k]

        def V(s, t, c0=c0, c1=c1, o=o):
            e = c0 + (c1 - c0) * s
            return e + UP * 0.05 - UP * (0.66 * t) + o * (0.03 + 0.05 * t)
        loft(shell, "valance_%d" % k, V, 6, 1, "valance", th=0.025)
        if ivy:
            for i in range(7):
                s = (i + 0.5) / 7
                e = c0 + (c1 - c0) * s
                vine(det, "valance_ivy_%d_%d" % (k, i), e + o * 0.1 + UP * 0.12, 0.7 + 0.45 * ((i * 7 + k) % 3) / 2, 0.42, normal=o)
    # apex finial
    box(shell, "apex_collar", (-0.18, apex_y - 0.12, -0.18), (0.18, apex_y + 0.12, 0.18), "wood_dark")
    octo(shell, "apex_ball", (0, apex_y + 0.12, 0), 0.13, 0.22, "gold")
    beam(shell, "apex_spike", (0, apex_y + 0.3, 0), (0, apex_y + 0.75, 0), 0.07, "gold")
    # ---- flag pole (swallow-tail flag) and the small flag at the other back corner
    if flags:
        _flags(shell, det, flag_corner, hw, hd, apex_y, tops)
    # ---- banners
    banner(shell, "banner_front", (0, eave_y + 0.14, D + 0.1), 1.35, 2.0, normal=(0, 0, 1))
    if side_banners >= 1:
        banner(shell, "banner_left", (-W - 0.1, eave_y + 0.1, 0.75), 0.9, 1.5, normal=(-1, 0, 0))
    if side_banners >= 2:
        banner(shell, "banner_right", (W + 0.1, eave_y + 0.1, 0.75), 0.9, 1.5, normal=(1, 0, 0))
    # ---- walls: the back and the back half of the sides (tent colour)
    tl.canvas_panel(shell, "wall_back", (-hw - 0.05, eave_y - 0.05, -hd - 0.22), (hw + 0.05, eave_y - 0.05, -hd - 0.22),
                    (-hw - 0.05, 0.02, -hd - 0.26), (hw + 0.05, 0.02, -hd - 0.26), sag=0.06, nx=3, ny=3, region="wall", ripple=0.03,
                    sag_dir=(0, 0, -1))
    for k, sx in enumerate((-1, 1)):
        x = sx * (hw + 0.22)
        tl.canvas_panel(shell, "wall_side_%d" % k, (x, eave_y - 0.05, -hd - 0.05), (x, eave_y - 0.05, -0.25),
                        (x + sx * 0.04, 0.02, -hd - 0.05), (x + sx * 0.04, 0.02, -0.15), sag=0.05, nx=2, ny=3, region="wall", ripple=0.03,
                        sag_dir=(sx, 0, 0))
    # ---- lanterns on the posts
    lpost = [(0, 1), (0, 1, 2, 3)][1 if lanterns >= 4 else 0] if lanterns else ()
    for k in lpost:
        x, z = corners[k]
        o = 1 if z > 0 else -1
        y = 2.3
        mount = v3(x, y + 0.42, z + o * 0.18)
        tip = v3(x, y + 0.42, z + o * 0.46)
        beam(det, "lamp_arm_%d" % k, mount, tip, 0.05, "iron", extend=0.02)
        beam(det, "lamp_brace_%d" % k, v3(x, y + 0.05, z + o * 0.18), tip - UP * 0.02, 0.04, "iron")
        lantern(shell, "lamp_%d" % k, (x, y, z + o * 0.46), size=0.36, metal="iron", chain_to=tip)
    # ---- rug
    L.rug_box = None
    if rug:
        rug_box = (-1.55, hd + 0.55, 1.55, hd + 2.55)
        globals()["rug"](shell, "rug", rug_box[0], rug_box[2], rug_box[1], rug_box[3], y=0.0)
        L.rug_box = rug_box
    # ---- counters and shelves
    L.counter_top_y = 1.0
    L.counter_boxes = []
    fc = "right" if front_counter is True else front_counter
    if fc:
        for sx in ((1,) if fc == "right" else (-1,) if fc == "left" else (1, -1)):
            xa, xb = sorted((sx * 0.75, sx * (hw - 0.35)))
            L.counter_boxes.append(counter(shell, "counter_front_%d" % (sx + 1), xa, xb, hd - 1.35, hd - 0.65, h=1.0, detail=det))
            xc, xd = sorted((sx * (hw - 1.05), sx * (hw - 0.35)))
            L.counter_boxes.append(counter(shell, "counter_side_%d" % (sx + 1), xc, xd, -0.55, hd - 1.39, h=1.0, detail=det))
    L.shelf_levels = []
    if back_shelves:
        L.shelf_levels = shelf_unit(shell, "shelves", -hw + 0.55, hw - 0.55, -hd + 0.25, -hd + 0.72, detail=det)
    L.floor = (-hw + 0.35, (-hd + 0.8) if back_shelves else (-hd + 0.35), hw - 0.35, hd - 0.2)
    L.front_left = (-hw + 0.05, 0.0, hd + 0.72)
    L.front_right = (hw - 0.05, 0.0, hd + 0.72)
    return L


def _flags(shell, det, flag_corner, hw, hd, apex_y, tops):
    """The pavilion's flag pole (swallow-tail flag) at a back corner, the small flag at the other one, the pennants on
    a rope from the apex spike to the main pole."""
    side = -1 if flag_corner == "back_left" else 1
    fx, fz = side * hw, -hd
    pole_top = apex_y + 1.4
    beam(shell, "flagpole", (fx, tops[3 if side < 0 else 2], fz), (fx, pole_top, fz), 0.12, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    octo(shell, "flagpole_ball", (fx, pole_top, fz), 0.08, 0.14, "gold")
    _flag_cloth(shell, "flag", v3(fx, pole_top - 0.12, fz), v3(side, 0, 0.25), 1.35, 0.72)
    ox = -side * hw
    small_top = apex_y + 0.5
    beam(shell, "flagpole_small", (ox, tops[2 if side < 0 else 3], fz), (ox, small_top, fz), 0.09, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    octo(shell, "flagpole_small_ball", (ox, small_top, fz), 0.06, 0.1, "gold")
    _flag_cloth(shell, "flag_small", v3(ox, small_top - 0.1, fz), v3(-side, 0, 0.3), 0.8, 0.42)
    # pennants on a rope from the apex spike to the main pole
    a, b = v3(0, apex_y + 0.62, 0), v3(fx, pole_top - 0.9, fz)
    tl.rope(det, "pennant_rope", a, b, d=0.03, sag=0.18, segs=3)
    dirn = norm(b - a)
    nrm = norm(np.cross(dirn, UP))
    for i in range(4):
        t = (i + 0.7) / 5
        p = a + (b - a) * t - UP * (4 * 0.18 * t * (1 - t))
        plate(det, "pennant_%d" % i, p - UP * 0.2, 0.22, 0.38, "pennant" if i % 2 == 0 else "pennant_beige", normal=nrm, up=UP, th=0.01)


def _flag_cloth(bone, name, top, direction, length, height):
    """A swallow-tail flag flying from the pole point `top` towards `direction`."""
    d = norm(v3(*direction) * v3(1, 0, 1))
    side = norm(np.cross(UP, d))

    def P(s, t):
        return top + d * (length * s) - UP * (height * t + 0.08 * s * s) + side * (0.1 * math.sin(2.4 * math.pi * s) * s)
    loft(bone, name, P, 4, 1, "flag", th=0.02, u_hint=d, v_hint=-UP)


# ---------------------------------------------------------------- 1.16.0: the gabled market stall
def _stall_drop(t, a=0.55):
    """The stall roof's profile: the fraction of the drop from the ridge (t = 0) to the eave (t = 1); steeper at the
    ridge, flatter at the eave (the cloth sags a little between them)."""
    return a * t + (1 - a) * (1 - (1 - t) ** 2)


def _stripes(img, colour, n, rng, stains=2):
    """n vertical stripes (tent colour, beige ...) across the whole image (a woven cloth); returns their edges in px."""
    w, h = img.size
    main = COLOURS[colour][0]
    edges = [int(round(k * w / n)) for k in range(n + 1)]
    for k in range(n):
        _weave(img, (edges[k], 0, edges[k + 1] - edges[k], h), main if k % 2 == 0 else BEIGE, rng, stains=stains)
    return edges


def _stall_roof_painter(colour, n, seed):
    """The stall's roof slopes: n stripes running down the slope (u across, v from the ridge down to the eave), dark
    seams between them, a soft fold in each stripe, a little lighter at the eave."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        edges = _stripes(img, colour, n, rng)
        px = img.load()
        sw = w / n
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                k = 0.9 + 0.14 * (y / h)
                if x in edges or x + 1 in edges:
                    k *= 0.76
                fx = (x % sw) / sw
                k *= 1.0 + 0.05 * math.sin(2 * math.pi * fx)
                if y < 2:
                    k *= 0.8
                px[x, y] = _scale((r, g, b), k) + (255,)
    return paint


def _stall_valance_painter(colour, n, seed):
    """n dagged tabs (tent colour / beige, as the stripes above them): stepped square dags, edged in gold; cut-out."""
    def bottom_of(x, w, h):
        tw = w / n
        lx = (x % tw) / tw
        tri = 1.0 - abs(2.0 * ((lx * 2.0) % 1.0) - 1.0)        # two teeth per tab
        step = math.floor(tri * 3.999) / 3.0                     # in square steps
        solid = int(h * 0.42)
        return int(solid + (h - 3 - solid) * step)

    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        edges = _stripes(img, colour, n, rng, stains=1)
        px = img.load()
        for x in range(w):
            bottom = bottom_of(x, w, h)
            for y in range(h):
                if y > bottom:
                    px[x, y] = (0, 0, 0, 0)
                elif y >= bottom - 1:
                    px[x, y] = _jitter(GOLD, rng, 8) + (255,)
                elif y < 2:
                    r, g, b, a = px[x, y]
                    px[x, y] = _scale((r, g, b), 0.78) + (255,)
            # gold on the vertical risers of the steps
            for xn in (x - 1, x + 1):
                if 0 <= xn < w:
                    b2 = bottom_of(xn, w, h)
                    if b2 < bottom:
                        for y in range(b2 - 1, bottom + 1):
                            px[x, y] = _jitter(GOLD, rng, 8) + (255,)
            if x in edges:
                for y in range(2, bottom - 1):
                    r, g, b, a = px[x, y]
                    px[x, y] = _scale((r, g, b), 0.8) + (255,)
    return paint


def _stall_gable_painter(colour, n, seed):
    """A gable end: n vertical stripes, cut out above the roof profile (the apex at the top middle), a dark hem along
    the two slopes."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        _stripes(img, colour, n, rng)
        px = img.load()
        for x in range(w):
            t = abs((x + 0.5) / w * 2.0 - 1.0)
            top = _stall_drop(t) * h            # px from the top where the roof passes
            for y in range(h):
                r, g, b, a = px[x, y]
                if y + 0.5 < top - 0.5:
                    px[x, y] = (0, 0, 0, 0)
                elif y + 0.5 < top + 2.0:
                    px[x, y] = _scale((r, g, b), 0.72) + (255,)
                else:
                    px[x, y] = _scale((r, g, b), 0.84 + 0.12 * (y / h)) + (255,)
    return paint


def _stall_wall_painter(seed):
    """The stall's back wall: dark vertical planks, a nailed batten across near the top and the bottom."""
    def paint(img):
        rng = random.Random(seed)
        w, h = img.size
        fine_wood(img, (0, 0, w, h), _rgb("5e4024"), _rgb("281a0c"), 8, rng, joints=False, vertical=True, knots=0.12, grain=0.12,
                  shade=0.08)
        px = img.load()
        for yb in (5, h - 9):
            for y in range(yb, yb + 4):
                for x in range(w):
                    c = _rgb("4a301a") if y in (yb, yb + 3) else _rgb("6a4628")
                    px[x, y] = _jitter(c, rng, 5) + (255,)
            for x in range(3, w, 8):
                px[x, yb + 1] = (150, 150, 156, 255)
    return paint


def _stall_post(bone, det, name, x, z, eave_y, top, ivy=False):
    """A stall corner post: a big iron-banded foot block, the squared post, iron bands, an iron collar and a gold cap
    above the roof; collides (the foot's width, up to the eave)."""
    box(bone, name + "_plinth", (x - 0.29, 0.0, z - 0.29), (x + 0.29, 0.72, z + 0.29), {"all": "wood_dark", "+2": "end_grain"})
    for k, y in enumerate((0.05, 0.57)):
        box(det, "%s_pband_%d" % (name, k), (x - 0.3, y, z - 0.3), (x + 0.3, y + 0.09, z + 0.3), "iron")
    beam(bone, name, (x, 0.72, z), (x, top, z), 0.4, {"all": "wood", "+1": "end_grain", "-1": "end_grain"})
    for k, y in enumerate((1.5, eave_y - 0.62)):
        box(det, "%s_band_%d" % (name, k), (x - 0.215, y, z - 0.215), (x + 0.215, y + 0.08, z + 0.215), "iron")
    box(bone, name + "_collar", (x - 0.23, top - 0.1, z - 0.23), (x + 0.23, top, z + 0.23), "iron")
    box(bone, name + "_cap", (x - 0.25, top, z - 0.25), (x + 0.25, top + 0.26, z + 0.25), "gold")
    collide((x - 0.29, 0.0, z - 0.29, x + 0.29, eave_y, z + 0.29))
    if ivy:
        for k, (dx, dz) in enumerate(((0.21, 0), (-0.21, 0))):
            vine(det, "%s_ivy_%d" % (name, k), (x + dx, eave_y - 0.2, z + dz), 1.6 + 0.4 * k, 0.34, normal=(np.sign(dx), 0, 0))


def stall(root, atlas, emblem="poison", lanterns=2, front_counter=True, back_shelves=True, banner_side="left", rug=False, ivy=False,
          half_w=2.65, half_d=2.4, eave_y=3.65, roof_rise=1.5, walls=True, hang_rail=True, stripes=7, end_stripes=5,
          counter_x=None, counter_h=1.05, hang_z=None, banner_size=(1.2, 1.72), lantern_size=0.42):
    """1.16.0: the gabled market stall (tente_poison, tente_boucher): 4 squared corner posts with gold caps above the
    roof, eave beams all round, the ridge along x (ridge pole, king posts and rafters at the ends), two slightly
    sagging roof slopes front and back with `stripes` stripes running down the slope, striped gable-end triangles
    (`end_stripes`), a dagged valance edged in gold on all four sides, a big banner with the emblem hanging from a rod
    on the front `banner_side` post (left / right / None), lanterns on the front posts (lanterns=2; 4 = all posts; 0),
    a long counter along the front (front_counter: True, or False; counter_x = (x0, x1)), a shelf unit along the back
    (back_shelves), a dark plank back wall and the back half of the sides (walls), a hanging rail along x under the
    eaves at hang_z (default half_d - 0.6) for hams, herbs ... (hang_rail). No flags, no pennants; rug=True lays the
    pavilion's rug in front. Returns the Layout (as pavilion(): half_w, half_d, eave_y, apex_y (= ridge_y), ridge_y,
    counter_top_y, counter_boxes, shelf_levels, floor, front_left, front_right, rug_box, detail, shell, atlas, colour,
    emblem; plus hang_y (the rail's underside), hang_z, hang_x (x0, x1), banner_box (x0, y0, x1, y1, z))."""
    if emblem not in EMBLEMS:
        raise KeyError("emblem must be one of %s" % ", ".join(EMBLEMS))
    atlas.emblem = emblem
    colour = atlas.colour
    seed = 1160 + _SEED[colour]
    hw, hd = half_w, half_d
    ridge_y = eave_y + roof_rise
    ov, ovx = 0.42, 0.3
    W, D = hw + ovx, hd + ov
    ey = eave_y + 0.02
    atlas.add("stall_roof", 32 * stripes, 96, _stall_roof_painter(colour, stripes, seed))
    atlas.add("stall_valance", 32 * stripes, 32, _stall_valance_painter(colour, stripes, seed + 1))
    atlas.add("stall_valance_end", 32 * end_stripes, 32, _stall_valance_painter(colour, end_stripes, seed + 2))
    atlas.add("stall_gable", 32 * end_stripes, 48, _stall_gable_painter(colour, end_stripes, seed + 3))
    atlas.add("stall_wall", 64, 64, _stall_wall_painter(seed + 4))
    L = Layout()
    L.atlas, L.colour, L.emblem = atlas, colour, emblem
    L.half_w, L.half_d, L.eave_y, L.apex_y, L.ridge_y = hw, hd, eave_y, ridge_y, ridge_y
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)
    L.shell, L.detail = shell, det
    # ---- posts, eave beams, braces
    corners = [(-hw, hd), (hw, hd), (hw, -hd), (-hw, -hd)]
    top = eave_y + 0.62
    for k, (x, z) in enumerate(corners):
        _stall_post(shell, det, "post_%d" % k, x, z, eave_y, top, ivy=ivy and z > 0)
    by = eave_y - 0.18
    for k in range(4):
        (xa, za), (xb, zb) = corners[k], corners[(k + 1) % 4]
        along_x = k in (0, 2)
        beam(shell, "eave_%d" % k, (xa, by, za), (xb, by, zb), 0.34, {"all": "wood", "+1": "end_grain", "-1": "end_grain"}, width=0.3,
             extend=0.34 if along_x else 0.14)
        if along_x:
            for s in (-1, 1):
                box(det, "eave_%d_tip_%d" % (k, (s + 1) // 2), (s * (hw + 0.34) - 0.03, by - 0.18, za - 0.16),
                    (s * (hw + 0.34) + 0.03, by + 0.18, za + 0.16), "gold")
                box(det, "eave_%d_strap_%d" % (k, (s + 1) // 2), (s * (hw - 0.3) - 0.05, by - 0.18, za - 0.16),
                    (s * (hw - 0.3) + 0.05, by + 0.18, za + 0.16), "iron")
    for k, (p, q) in enumerate((((-hw + 0.2, eave_y - 1.1, hd), (-hw + 0.9, by - 0.12, hd)), ((hw - 0.2, eave_y - 1.1, hd), (hw - 0.9, by - 0.12, hd)),
                                ((-hw, eave_y - 1.1, hd - 0.2), (-hw, by - 0.12, hd - 0.9)), ((hw, eave_y - 1.1, hd - 0.2), (hw, by - 0.12, hd - 0.9)),
                                ((-hw, eave_y - 1.1, -hd + 0.2), (-hw, by - 0.12, -hd + 0.9)), ((hw, eave_y - 1.1, -hd + 0.2), (hw, by - 0.12, -hd + 0.9)))):
        beam(shell, "brace_%d" % k, p, q, 0.15, "wood_dark", extend=0.05)
    # ---- the ridge: pole, king posts and rafters at the two ends (under the cloth)
    beam(shell, "ridge_pole", (-W + 0.06, ridge_y - 0.13, 0), (W - 0.06, ridge_y - 0.13, 0), 0.18,
         {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    for k, sx in enumerate((-1, 1)):
        x = sx * hw
        beam(shell, "king_post_%d" % k, (x, by + 0.17, 0), (x, ridge_y - 0.2, 0), 0.16, "wood_dark")
        for j, sz in enumerate((-1, 1)):
            beam(shell, "rafter_%d_%d" % (k, j), (x, by + 0.1, sz * (hd + 0.05)), (x, ridge_y - 0.16, 0), 0.14, "wood_dark", extend=0.05)
    # ---- the roof: two sagging slopes, stripes running down the slope
    droop = 0.07

    def roof_pt(s, t, sgn):
        x = -W + 2 * W * s
        y = ridge_y - (ridge_y - ey) * _stall_drop(t) - droop * math.sin(math.pi * s) * math.sin(math.pi * t)
        return v3(x if sgn > 0 else -x, y, sgn * D * t)
    loft(shell, "roof_front", lambda s, t: roof_pt(s, t, 1), stripes, 4, "stall_roof", th=0.04)
    loft(shell, "roof_back", lambda s, t: roof_pt(s, t, -1), stripes, 4, "stall_roof", th=0.04)
    # the gable-end triangles (cut out to the roof profile)
    for k, sx in enumerate((-1, 1)):
        plate(shell, "gable_%d" % k, (sx * (W - 0.03), (ey + ridge_y) / 2, 0), 2 * D, ridge_y - ey, "stall_gable", normal=(sx, 0, 0),
              th=0.02)
    # the valance all round: dagged tabs as the stripes above them, flaring out a little
    vh = 0.62
    sides = ((v3(-W, ey, D), v3(W, ey, D), Z, "stall_valance"), (v3(W, ey, -D), v3(-W, ey, -D), -Z, "stall_valance"),
             (v3(-W, ey, -D), v3(-W, ey, D), -X, "stall_valance_end"), (v3(W, ey, D), v3(W, ey, -D), X, "stall_valance_end"))
    for k, (c0, c1, o, reg) in enumerate(sides):
        def V(s, t, c0=c0, c1=c1, o=o):
            e = c0 + (c1 - c0) * s
            return e + UP * 0.04 - UP * (vh * t) + o * (0.03 + 0.05 * t)
        loft(shell, "valance_%d" % k, V, 1, 1, reg, th=0.025)
    # ---- the hanging rail
    L.hang_z = hd - 0.6 if hang_z is None else hang_z
    L.hang_y = eave_y - 0.12 - 0.08
    L.hang_x = (-hw + 0.25, hw - 0.25)
    if hang_rail:
        beam(shell, "hang_rail", (-hw - 0.05, eave_y - 0.12, L.hang_z), (hw + 0.05, eave_y - 0.12, L.hang_z), 0.16, "wood_dark")
    # ---- the banner from a rod on a front post
    L.banner_box = None
    if banner_side:
        sx = -1 if banner_side == "left" else 1
        x0 = sx * hw
        zr, yr = D + 0.2, eave_y + 0.02
        box(det, "banner_arm", (x0 - 0.05, yr - 0.05, hd + 0.18), (x0 + 0.05, yr + 0.05, zr + 0.05), "iron")
        xa, xb = x0 + sx * 0.12, x0 - sx * (banner_size[0] + 0.75)   # from the post inwards
        beam(shell, "banner_rod", (xa, yr, zr), (xb, yr, zr), 0.08, "wood_dark")
        for k, xx in enumerate((xa, xb)):
            add_cube(shell, "banner_rod_knob_%d" % k, (xx, yr, zr), EYE, (0.12, 0.12, 0.12), "gold")
        bw, bh = banner_size
        bx = x0 - sx * (0.45 + bw / 2)
        banner(shell, "banner_front", (bx, yr - 0.04, zr + 0.01), bw, bh, normal=(0, 0, 1), rod=False)
        for k, xx in enumerate((bx - bw / 2 + 0.08, bx + bw / 2 - 0.08)):
            add_cube(det, "banner_ring_%d" % k, (xx, yr, zr), EYE, (0.1, 0.15, 0.13), "gold")
        L.banner_box = (bx - bw / 2, yr - bh, bx + bw / 2, yr, zr)
    # ---- the back wall and the back half of the sides (dark planks)
    if walls:
        box(shell, "wall_back", (-hw, 0.0, -hd - 0.1), (hw, by - 0.17, -hd - 0.02), {"all": "stall_wall"}, stretch=True)
        collide((-hw, 0.0, -hd - 0.1, hw, by - 0.17, -hd - 0.02))
        for k, sx in enumerate((-1, 1)):
            x = sx * hw
            box(shell, "wall_side_%d" % k, (x - 0.04, 0.0, -hd), (x + 0.04, by - 0.17, -0.45), {"all": "stall_wall"}, stretch=True)
            collide((x - 0.04, 0.0, -hd, x + 0.04, by - 0.17, -0.45))
    # ---- lanterns on the posts (front face)
    lpost = [(0, 1), (0, 1, 2, 3)][1 if lanterns >= 4 else 0] if lanterns else ()
    for k in lpost:
        x, z = corners[k]
        o = 1 if z > 0 else -1
        y = 2.45
        mount = v3(x, y + 0.5, z + o * 0.2)
        tip = v3(x, y + 0.5, z + o * 0.52)
        beam(det, "lamp_arm_%d" % k, mount, tip, 0.05, "iron", extend=0.02)
        beam(det, "lamp_brace_%d" % k, v3(x, y + 0.05, z + o * 0.2), tip - UP * 0.02, 0.04, "iron")
        lantern(shell, "lamp_%d" % k, (x, y, z + o * 0.52), size=lantern_size, metal="iron", chain_to=tip)
    # ---- rug (optional)
    L.rug_box = None
    if rug:
        rug_box = (-1.55, hd + 0.55, 1.55, hd + 2.55)
        globals()["rug"](shell, "rug", rug_box[0], rug_box[2], rug_box[1], rug_box[3], y=0.0)
        L.rug_box = rug_box
    # ---- the counter along the front and the shelves along the back
    L.counter_top_y = counter_h
    L.counter_boxes = []
    if front_counter:
        cx0, cx1 = counter_x or (-0.6, hw - 0.35)
        L.counter_boxes.append(counter(shell, "counter_front", cx0, cx1, hd - 1.05, hd - 0.35, h=counter_h, detail=det))
    L.shelf_levels = []
    if back_shelves:
        L.shelf_levels = shelf_unit(shell, "shelves", -hw + 0.4, hw - 0.4, -hd + 0.12, -hd + 0.6, levels=(0.55, 1.15, 1.75, 2.35),
                                    h=2.7, back=not walls, uprights=4, detail=det)
    L.floor = (-hw + 0.3, (-hd + 0.7) if back_shelves else (-hd + 0.3), hw - 0.3, hd - 0.2)
    L.front_left = (-hw, 0.0, hd + 0.45)
    L.front_right = (hw, 0.0, hd + 0.45)
    return L


# ---------------------------------------------------------------- decor, icon, export
class Decor(tl.Decor):
    """tentlib.Decor (furniture of the decoration mods, vanilla `alt`, stand-in fallback bones); fallbacks() is
    idempotent and called by export."""

    def __init__(self):
        super().__init__()
        self._fb_done = False

    def fallbacks(self, root):
        if self._fb_done:
            return
        self._fb_done = True
        super().fallbacks(root)


def icon(path, colour="red", emblem="swords", shape="pavilion"):
    """16x16 item icon: a striped pointed tent in its colour, dagged valance, dark opening, a banner with the emblem
    colour; shape="stall" (1.16.0): the gabled market stall (stall_icon)."""
    if shape == "stall":
        return stall_icon(path, colour=colour, emblem=emblem)
    from PIL import Image
    main, dark, light = COLOURS[colour]
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    wood, wood_d = (110, 74, 40), (70, 46, 24)
    for y in range(1, 9):
        half = 1 + (y - 1) * 0.95
        for x in range(16):
            dx = x - 7.5
            if abs(dx) <= half:
                stripe = int((dx / max(half, 0.5)) * 3 + 3) % 2
                c = main if stripe == 0 else BEIGE
                if abs(abs(dx) - half) < 0.6:
                    c = _scale(c, 0.75)
                p[x, y] = c + (255,)
    p[7, 0] = p[8, 0] = GOLD + (255,)
    for x in range(0, 16):
        p[x, 9] = (main if (x // 2) % 2 == 0 else BEIGE) + (255,)
        if x % 2 == 0:
            p[x, 10] = (main if (x // 2) % 2 == 0 else BEIGE) + (255,)
    for y in range(10, 16):
        for x in (1, 2, 13, 14):
            if y > 10 or x in (1, 14):
                p[x, y] = (wood if x in (1, 13) else wood_d) + (255,)
        for x in range(3, 13):
            if y > 10:
                p[x, y] = (54, 38, 24, 255)
    for y in range(10, 14):
        for x in range(6, 10):
            p[x, y] = (main if y < 13 or x in (7, 8) else (0, 0, 0)) + (255 if (y < 13 or x in (7, 8)) else 0,)
    emblem_col = EMBLEM_ICON[emblem]
    p[7, 11] = p[8, 11] = emblem_col + (255,)
    p[7, 12] = p[8, 12] = _scale(emblem_col, 0.8) + (255,)
    for x in range(2, 14):
        p[x, 15] = _scale(main, 0.8) + (255,)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)


def stall_icon(path, colour="red", emblem="poison"):
    """16x16 item icon of a gabled stall (1.16.0): the striped front slope under its ridge, the dagged valance, two
    posts with gold caps, the dark inside with a counter, the banner with the emblem colour on the left."""
    from PIL import Image
    main, dark, light = COLOURS[colour]
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    wood, wood_d = (124, 84, 44), (72, 48, 24)
    for y in range(2, 8):   # the front slope, widening a little downwards, 7 stripes
        x0, x1 = 2 - (y - 2) // 3, 13 + (y - 2) // 3
        for x in range(x0, x1 + 1):
            k = int((x - x0) / (x1 - x0 + 1) * 7)
            c = main if k % 2 == 0 else BEIGE
            if y == 2:
                c = _scale(c, 0.8)
            p[x, y] = c + (255,)
    for x in range(1, 15):   # the valance, dagged
        c = main if int((x - 1) / 14 * 7) % 2 == 0 else BEIGE
        p[x, 8] = c + (255,)
        if x % 2 == 1:
            p[x, 9] = GOLD + (255,)
    for x in (1, 14):        # posts and gold caps
        p[x, 1] = GOLD + (255,)
        for y in range(2, 16):
            if p[x, y][3] == 0 or y > 8:
                p[x, y] = (wood if x == 1 else wood_d) + (255,)
    for y in range(10, 15):
        for x in range(2, 14):
            p[x, y] = (40, 28, 18, 255)
    for x in range(6, 14):   # the counter
        p[x, 12] = (150, 104, 56, 255)
        for y in (13, 14):
            p[x, y] = (110, 74, 40, 255)
    for y in range(9, 14):   # the banner
        for x in range(3, 6):
            if y < 13 or x == 4:
                p[x, y] = main + (255,)
    ec = EMBLEM_ICON[emblem]
    p[4, 10] = ec + (255,)
    p[4, 11] = _scale(ec, 0.8) + (255,)
    for x in range(1, 15):
        p[x, 15] = _scale(wood_d, 0.9) + (255,)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)


def export(root, name, atlas, decor=None, icon=None, particles=None, visible_box=(10, 8, 0)):
    """Writes tents/<id>.json, models/entity/<id>.bbmodel, blockbench/<id>.bbmodel, textures/entity/<id>.png,
    textures/item/<id>.png (icon=dict(colour=..., emblem=...) or a function(path)), interiors/<id>_decor.json.
    MERCHANT_OUT=<file.bbmodel>: writes only the model (and its atlas next to it) there, for previews."""
    out_model = os.environ.get("MERCHANT_OUT")
    tex_name = "%s.png" % name
    tex_path = os.path.join(ASSETS, "textures/entity", tex_name) if not out_model else os.path.join(os.path.dirname(out_model), tex_name)
    if decor is not None:
        decor.fallbacks(root)
    atlas._apply()
    atlas.make(tex_path)
    with open(tex_path, "rb") as f:
        png = f.read()
    textures = [gn.texture_entry(tex_name, atlas.size, png, "entity", tex_name)]
    textures[0]["id"] = "0"
    decor_path = None
    if decor is not None and decor.blocks:
        decor_path = "interiors/%s_decor.json" % name
        if not out_model:
            decor.write(os.path.join(ASSETS, decor_path))
    ext = tl.extent(root)
    outs = [out_model] if out_model else [os.path.join(ROOT, "blockbench/%s.bbmodel" % name),
                                          os.path.join(ASSETS, "models/entity/%s.bbmodel" % name)]
    model = gn.export(root, [], textures, outs, name=name, visible_box=visible_box)
    if not out_model:
        data = {
            "model": "models/entity/%s.bbmodel" % name,
            "texture": "textures/entity/%s" % tex_name,
            "decor": "/assets/medievalships/" + decor_path if decor_path else None,
            "extent": [round(float(v), 3) for v in ext],
            "colliders": [[round(float(v), 3) for v in (b[0], max(0.0, b[1]), b[2], b[3], b[4], b[5])] for b in COLLIDERS],
        }
        if particles:
            data["particles"] = particles
        path = os.path.join(ASSETS, "tents/%s.json" % name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=1)
        ipath = os.path.join(ASSETS, "textures/item/%s.png" % name)
        if callable(icon):
            icon(ipath)
        else:
            spec = dict(colour=atlas.colour, emblem=atlas.emblem)
            spec.update(icon or {})
            globals()["icon"](ipath, **spec)
    print("%s: %d cubes, extent %s, %d collision boxes, %d mod blocks" % (
        name, len(model["elements"]), ["%.2f" % v for v in ext], len(COLLIDERS), 0 if decor is None else len(decor.blocks)))
    return model


def particle(kind, pos, chance=0.3, count=1):
    """A particle source for export(particles=[...]) (TentType.Particle; vanilla types, see TentType.PARTICLE_TYPES)."""
    return {"type": kind, "pos": [round(float(c), 3) for c in pos], "chance": chance, "count": count}
