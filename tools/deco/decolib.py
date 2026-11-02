"""Shared atlas, helpers and export of the eight street decorations (1.20.0): one block each, static, drawn like the
tents / carts / workshops from a .bbmodel (TentType JSON group "decorations", folder assets/medievalships/decorations/).

A generator (tools/deco/generate_<id>.py) does, in this order:

    import decolib as dl
    dl.setup("deco_x")                           # the shared atlas becomes the regions, collisions / uuids reset
    root = dl.Bone("deco_x")
    det = dl.Bone("detail", parent=root)         # small things (pegs, knots, chains, floats): hidden beyond 32 blocks
    L = dl.post(root, "post_l", (-2.2, 0, 0), 3.2, bindings=[3.0], bands=[0.25], detail=det)
    R = dl.post(root, "post_r", (2.2, 0, 0), 3.0, bindings=[2.8], bands=[0.25], detail=det)
    line = dl.sag_rope(det, "rope", L.top_front(-0.1), R.top_front(-0.1), sag=0.35)   # line.at(t) -> point
    dl.pennant(root, "flag_0", line.at(0.2), line.at(0.3), 0.7, "pennant_red")
    ... dl.clothes / dl.swag / dl.tail / dl.net / dl.float_buoy / dl.bundle / dl.chain / dl.hanging_lantern
        dl.gallows_arm / dl.banner / dl.sail / dl.lantern ...
    dl.export(root, "deco_x", light=0, icon=lambda put: ...)

export() writes decorations/<id>.json (model, texture "textures/entity/decorations.png", decor null, extent,
colliders, light 0-15), models/entity/<id>.bbmodel, blockbench/<id>.bbmodel, the shared atlas
textures/entity/decorations.png and the 16x16 item icon textures/item/<id>.png. Coordinates: prop-local blocks, y up
(y = 0 = top of the ground block), +z = the FRONT (towards the player who placed it), the anchor block's centre at
(0, 0, 0). Posts collide (thin boxes, post(..., solid=True)); ropes, cloth, nets, lanterns never collide unless the
generator calls collide() itself. light: the anchor block's luminance (vanilla light engine, no tick): 15 = a torch.

Cubes whose name starts with "glow" are drawn full bright; a cube whose four sides use the "lantern" region is rebuilt
on export as a lit lantern (tools/lanterns.py: lit glass, corner posts, cap, ring). Cut-out regions (pennants,
clothes, drapery edges, net, chain, herbs, banner point, lion) are fully transparent outside the shape.

THE ATLAS (textures/entity/decorations.png, 512 x 512, shared by the eight decorations, deterministic: every
generator rewrites the same file). Regions (name: w x h px, what it is, how to map it):
  post 32x64, post_dark 32x64 (upright post sides, grain along v: an axis-aligned upright box reads right on its
  four sides; post() uses it), wood 64x16 (beams, grain along u: beam() maps u along the length), wood_dark 64x16, wood_light 64x16 (pegs),
  plank 64x16 (horizontal beams / arms), end_grain 16x16 (post tops), rope 16x16 (twisted, along u), rope_coil 32x16
  (wrapped rope rings, coils along u), iron 16x16, iron_band 32x8 (dark band, two rivets every 16 px), iron_dark 16x16,
  chain 16x16 (cut-out links), gold 16x16, gold_rod 16x16, stone 32x32 (footing side), stone_top 16x16,
  lantern 16x16 (lit glass, see above), lantern_grid 16x16 (lit glass with a 2 x 2 window grid, use glow_ cubes),
  glow 16x16 (warm light), flame 16x16;
  plain cloths 32x32: cloth_red, cloth_yellow, cloth_blue, cloth_green, cloth_white, cloth_beige, cloth_navy;
  pennant_red, pennant_yellow, pennant_blue 24x32 (cut-out: dagged bottom with three points, darker border);
  clothes 32x48 (cut-out, top = the pegged edge): sheet_white (ragged hem), tunic_stripes (blue, white vertical stripes,
  a band near the hem), cloth_worn (beige, torn bottom, small holes), cloth_red_worn (brick red, ragged hem);
  drape_swag 96x48 (red, small gold dots, gold dagged band along the BOTTOM edge, cut-out teeth), drape_tail 32x64
  (red, gold dagged bottom, cut-out), drape_red 32x32 (plain red with gold dots);
  banner_navy 48x96 (navy, gold border, golden rampant lion facing left, dagged pointed end, cut-out),
  lion 32x32 (the gold lion alone, cut-out), net 64x64 (cut-out diamond rope mesh, knots), net_edge 64x16 (cut-out
  dangling rope ends), float_side 16x16 (white / red band / white / blue, along v), float_small 16x16 (red / white),
  float_top 16x16;
  herbs_green, herbs_lavender, herbs_sage, herbs_white 32x48 (cut-out hanging bundles: tie at the top, the bundle
  widening downwards; map with v down), sail 96x64 (beige canvas, hemmed, stains), sail_edge 64x8 (hem), canvas
  (= sail), fringe 32x16 (beige torn edge).
Look at the atlas: python3 tools/deco/decolib.py (writes it and prints the regions).

EXTENDING THE ATLAS (other modules, e.g. D2's): never edit this file. Put a module tools/deco/atlas_<anything>.py
next to it that defines
    REGIONS = [("my_region", w, h, painter), ...]      # painter(img, rng): img = a w x h RGBA PIL image to paint
Every atlas_*.py module is imported (sorted by file name) when decolib is imported; its regions are allocated after
the base regions (base positions never move), so every generator writes the same complete atlas. Region names must be
new. A region can then be used by name like any other.
"""
import glob
import importlib
import json
import math
import os
import random
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TOOLS, "tents"))
sys.path.insert(0, os.path.join(TOOLS, "carts"))
sys.path.insert(0, os.path.join(TOOLS, "merchant"))
sys.path.insert(0, TOOLS)
import tentlib as tl  # noqa: E402
from galley_texture import _rgb, _jitter, _mix, _scale, _ramp, fine_wood, hammered_iron, twisted_rope, end_grain, paint_lamp_glass, polished_metal  # noqa: E402,F401
import tent_texture as tt  # noqa: E402

gg, gn = tl.gg, tl.gn
v3, norm, Bone, add_cube, beam, loft = tl.v3, tl.norm, tl.Bone, tl.add_cube, tl.beam, tl.loft
EYE, UP = tl.EYE, tl.UP
X, Z = np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0])
ASSETS, ROOT = tl.ASSETS, tl.ROOT
collide, collide_segment, COLLIDERS = tl.collide, tl.collide_segment, tl.COLLIDERS
ry, rx, rz = gg.ry, gg.rx, gg.rz

NAME = "decorations.png"
SIZE = 512
GOLD = _rgb("d9a93a")
GOLD_DARK = _rgb("8a6418")
GOLD_LIGHT = _rgb("f2cf6a")

# ---------------------------------------------------------------- palette (sampled from the reference sheet)
WOOD = _rgb("8a5c36")
WOOD_DARK_C = _rgb("3e2a18")
ROPE_LIGHT, ROPE_DARK = _rgb("d8c08e"), _rgb("8a7048")
RED, RED_DARK = _rgb("a4282a"), _rgb("5e1414")
YELLOW, YELLOW_DARK = _rgb("e0aa2a"), _rgb("9a6a10")
BLUE, BLUE_DARK = _rgb("3a48a8"), _rgb("1e2660")
GREEN, GREEN_DARK = _rgb("4a7a2c"), _rgb("24421a")
WHITE = _rgb("e8e2d2")
BEIGE = _rgb("d8c8a0")
NAVY, NAVY_DARK = _rgb("2a2c78"), _rgb("16173e")


# ---------------------------------------------------------------- painters (img = a w x h RGBA image)
def _P(img, x, y, c, a=255):
    if 0 <= x < img.size[0] and 0 <= y < img.size[1]:
        img.putpixel((int(x), int(y)), tuple(int(k) for k in c[:3]) + (a,))


def _R(img):
    return (0, 0, img.size[0], img.size[1])


def p_wood(base, dark, plank_h=16, knots=0.12):
    def paint(img, rng):
        fine_wood(img, _R(img), base, dark, plank_h, rng, joints=False, knots=knots, grain=0.13, shade=0.07)
        w, h = img.size
        # the squared post's arrises: a lit and a dark line along both long edges
        for x in range(w):
            _P(img, x, 0, _scale(img.getpixel((x, 0)), 1.1))
            _P(img, x, h - 1, _scale(img.getpixel((x, h - 1)), 0.72))
    return paint


def p_post(base, dark):
    """Post sides: the grain vertical (along v), narrow plank-like streaks, so every side of an upright box reads right."""
    def paint(img, rng):
        fine_wood(img, _R(img), base, dark, 8, rng, joints=False, vertical=True, knots=0.1, grain=0.13, shade=0.07)
        w, h = img.size
        for y in range(h):
            for x in range(0, w, 8):
                _P(img, x + 7, y, _mix(img.getpixel((x + 7, y)), dark, 0.35))
    return paint


def p_end_grain(img, rng):
    end_grain(img, _R(img), _rgb("a07850"), _rgb("5a3e22"), rng)
    w, h = img.size
    for k in range(w):
        for (x, y) in ((k, 0), (k, h - 1), (0, k), (w - 1, k)):
            _P(img, x, y, _scale(img.getpixel((x, y)), 0.7))


def p_rope(img, rng):
    twisted_rope(img, _R(img), ROPE_LIGHT, ROPE_DARK, rng)


def p_rope_coil(img, rng):
    """Wrapped rope rings along u: each coil 4 px high, lit on top, dark groove under it, twist lines."""
    w, h = img.size
    for y in range(h):
        r = y % 4
        for x in range(w):
            t = ((x * 0.5 + y * 1.3) % 3) / 3.0
            c = _ramp([(0.0, ROPE_DARK), (0.35, ROPE_LIGHT), (0.7, _mix(ROPE_LIGHT, ROPE_DARK, 0.3)), (1.0, ROPE_DARK)], t)
            k = (1.12, 1.02, 0.9, 0.6)[r]
            _P(img, x, y, _jitter(_scale(c, k), rng, 3))


def p_iron(img, rng):
    hammered_iron(img, _R(img), _rgb("4a4a50"), rng)


def p_iron_dark(img, rng):
    hammered_iron(img, _R(img), _rgb("2e2e34"), rng)


def p_iron_band(img, rng):
    hammered_iron(img, _R(img), _rgb("3e3e44"), rng)
    w, h = img.size
    for x in range(w):
        _P(img, x, 0, _rgb("64646c"))
        _P(img, x, h - 1, _rgb("222226"))
    for x0 in range(4, w, 16):
        for (dx, dy, c) in ((0, 0, "9a9aa2"), (1, 0, "7a7a82"), (0, 1, "5a5a62"), (1, 1, "2a2a30")):
            _P(img, x0 + dx, h // 2 - 1 + dy, _rgb(c))
            _P(img, x0 + 8 + dx, h // 2 - 1 + dy, _rgb(c))


def p_chain(img, rng):
    """Cut-out chain: an oval link face-on (top half) and an edge-on link (bottom half)."""
    w, h = img.size
    for y in range(h):
        for x in range(w):
            _P(img, x, y, (0, 0, 0), 0)
    for y in range(h):
        for x in range(w):
            dx, dy = (x + 0.5 - w / 2) / (w * 0.32), (y + 0.5 - h / 2) / (h * 0.46)
            r = math.hypot(dx, dy)
            if 0.62 < r < 1.0:
                c = _rgb("6a6a72") if dx < 0 else _rgb("3a3a40")
                if dy < -0.5:
                    c = _rgb("8a8a92")
                _P(img, x, y, _jitter(c, rng, 4))


def p_gold(img, rng):
    polished_metal(img, _R(img), [(0, (120, 84, 26)), (0.5, (214, 170, 72)), (1, (250, 230, 160))], rng)


def p_stone(img, rng):
    tt._fill(img, _R(img), _rgb("8e8c86"), rng, noise=10)
    w, h = img.size
    for y in range(h):
        for x in range(w):
            c = img.getpixel((x, y))[:3]
            k = 1.0 + 0.08 * math.sin(x * 0.7 + y * 0.3) * math.sin(y * 0.5)
            if x in (0, w - 1) or y in (0, h - 1):
                k *= 0.7
            elif x == 1 or y == 1:
                k *= 1.12
            _P(img, x, y, _scale(c, k))
    for _ in range(3):   # cracks
        x, y = rng.randint(4, w - 5), rng.randint(4, h - 5)
        for i in range(rng.randint(4, 8)):
            _P(img, x, y, _rgb("55534e"))
            x += rng.choice((-1, 0, 1))
            y += 1
    for _ in range(5):   # moss specks at the bottom
        _P(img, rng.randint(1, w - 2), rng.randint(h - 5, h - 2), _rgb("5a6e34"))


def p_stone_top(img, rng):
    tt._fill(img, _R(img), _rgb("9a9890"), rng, noise=9)
    w, h = img.size
    for k in range(w):
        for (x, y) in ((k, 0), (k, h - 1), (0, k), (w - 1, k)):
            _P(img, x, y, _rgb("6e6c66"))


def p_lantern(img, rng):
    paint_lamp_glass(img.load(), 0, 0, img.size[0], img.size[1])


def p_lantern_grid(img, rng):
    paint_lamp_glass(img.load(), 0, 0, img.size[0], img.size[1])
    w, h = img.size
    for k in range(w):
        _P(img, k, h // 2, _rgb("3a2a1a"))
        _P(img, w // 2, k, _rgb("3a2a1a"))
        _P(img, k, 0, _rgb("2a1e12"))
        _P(img, k, h - 1, _rgb("2a1e12"))
        _P(img, 0, k, _rgb("2a1e12"))
        _P(img, w - 1, k, _rgb("2a1e12"))


def p_glow(img, rng):
    w, h = img.size
    for y in range(h):
        for x in range(w):
            d = math.hypot(x + 0.5 - w / 2, y + 0.5 - h / 2) / (w / 2)
            _P(img, x, y, _mix((255, 236, 170), (240, 160, 60), min(1.0, d)))


def p_flame(img, rng):
    w, h = img.size
    for y in range(h):
        for x in range(w):
            d = math.hypot((x + 0.5 - w / 2) * 1.6, y + 0.5 - h * 0.62) / (h / 2)
            if d < 1:
                _P(img, x, y, _mix((255, 250, 200), (250, 140, 40), d))
            else:
                _P(img, x, y, (0, 0, 0), 0)


def p_cloth(base, stains=1, seams=0):
    def paint(img, rng):
        tt._weave(img, _R(img), base, rng, seams=seams, patches=0, stains=stains, tears=0, noise=4)
    return paint


def _cloth_base(img, rng, base, fold_period=7, fold=0.08, seed=0.0):
    """Woven cloth with soft vertical folds (hanging cloth)."""
    w, h = img.size
    for y in range(h):
        for x in range(w):
            k = 1.0 + (0.03 if (x + y) % 2 == 0 else -0.03)
            k += fold * math.sin(2 * math.pi * x / fold_period + seed + 0.3 * math.sin(y * 0.15))
            _P(img, x, y, _jitter(_scale(base, k), rng, 4))


def p_pennant(base, dark):
    """A pennant: border a shade darker, a small diamond, the bottom dagged into three points (cut-out)."""
    def paint(img, rng):
        w, h = img.size
        _cloth_base(img, rng, base, fold_period=9, fold=0.05)
        body = int(h * 0.74)
        teeth = 3
        tw = w / teeth
        for y in range(h):
            for x in range(w):
                if y >= body:
                    xx = (x + 0.5) % tw
                    half = (tw / 2) * (1 - (y - body) / (h - body))
                    if abs(xx - tw / 2) > half:
                        _P(img, x, y, (0, 0, 0), 0)
                        continue
                    if abs(xx - tw / 2) > half - 1.4:
                        _P(img, x, y, _jitter(dark, rng, 5))
                    continue
                if x < 2 or x >= w - 2 or y < 2:
                    _P(img, x, y, _jitter(dark, rng, 5))
        cx, cy = w / 2, body * 0.5 + 1
        for y in range(h):
            for x in range(w):
                d = abs(x + 0.5 - cx) / (w * 0.22) + abs(y + 0.5 - cy) / (body * 0.3)
                if 0.7 < d < 1.0:
                    _P(img, x, y, _scale(base, 1.18))
        for x in range(w):            # the fold over the rope at the top
            _P(img, x, 0, _scale(dark, 0.8))
    return paint


def _ragged(img, rng, depth, deep=None, holes=0, base=None):
    """Cuts a ragged lower edge (up to `depth` px; `deep` = some deeper tears) and a few small holes."""
    w, h = img.size
    reach = []
    r = h - rng.randint(0, depth)
    for x in range(w):
        r += rng.choice((-1, 0, 0, 1))
        r = max(h - depth, min(h, r))
        rr = r
        if deep and rng.random() < 0.12:
            rr = h - rng.randint(depth, deep)
        reach.append(rr)
    for x in range(w):
        for y in range(reach[x], h):
            _P(img, x, y, (0, 0, 0), 0)
        if reach[x] - 1 >= 0 and base is not None:
            _P(img, x, reach[x] - 1, _scale(base, 0.82))
    for _ in range(holes):
        x0, y0 = rng.randint(3, w - 4), rng.randint(h // 3, h - depth - 3)
        for dy in range(rng.randint(1, 3)):
            for dx in range(rng.randint(1, 2)):
                _P(img, x0 + dx, y0 + dy, (0, 0, 0), 0)


def p_sheet_white(img, rng):
    _cloth_base(img, rng, _rgb("e6e0d0"), fold_period=8, fold=0.07)
    w, h = img.size
    for x in range(w):
        _P(img, x, 1, _rgb("c8c0ac"))
    _ragged(img, rng, 4, deep=7, holes=0, base=_rgb("e6e0d0"))


def p_tunic_stripes(img, rng):
    """A dusty blue tunic: thin pale vertical stripes, a pale band above the hem, darker side seams."""
    base = _rgb("56628e")
    _cloth_base(img, rng, base, fold_period=10, fold=0.07)
    w, h = img.size
    pale = _rgb("cfd0d4")
    for y in range(h):
        for x in range(w):
            if x % 6 == 2:
                _P(img, x, y, _jitter(pale, rng, 6))
            if h - 8 <= y <= h - 7:
                _P(img, x, y, _jitter(pale, rng, 6))
            if x in (0, w - 1):
                _P(img, x, y, _scale(base, 0.7))
    for x in range(w):
        _P(img, x, h - 1, _rgb("2e3660"))
        _P(img, x, 0, _rgb("2e3660"))


def p_cloth_worn(img, rng):
    base = _rgb("d4c098")
    _cloth_base(img, rng, base, fold_period=9, fold=0.07)
    w, h = img.size
    for _ in range(4):   # stains
        cx, cy, r = rng.uniform(4, w - 4), rng.uniform(6, h - 10), rng.uniform(2, 5)
        for y in range(h):
            for x in range(w):
                d = math.hypot(x - cx, y - cy) / r
                if d < 1:
                    _P(img, x, y, _scale(img.getpixel((x, y)), 0.88 + 0.08 * d))
    _ragged(img, rng, 5, deep=12, holes=4, base=base)


def p_cloth_red_worn(img, rng):
    base = _rgb("a2453a")
    _cloth_base(img, rng, base, fold_period=11, fold=0.08)
    w, h = img.size
    for y in range(h):
        _P(img, w // 2, y, _scale(img.getpixel((w // 2, y)), 0.85))
    _ragged(img, rng, 5, deep=9, holes=1, base=base)


def _gold_dots(img, rng, every=8, start=0, top=0, bottom=None):
    w, h = img.size
    bottom = h if bottom is None else bottom
    for y in range(top + 3, bottom, every):
        off = (y // every) % 2 * (every // 2)
        for x in range(start + off + 2, w, every):
            _P(img, x, y, GOLD)
            _P(img, x + 1, y, GOLD_DARK)


def _dagged_band(img, rng, top, band=5, tooth=6, tip=None):
    """A gold band from row `top` (band px high) then gold teeth hanging under it (cut-out between them)."""
    w, h = img.size
    tip = h if tip is None else tip
    for y in range(top, h):
        for x in range(w):
            if y < top + band:
                c = GOLD_LIGHT if y == top else (GOLD if y < top + band - 1 else GOLD_DARK)
                _P(img, x, y, _jitter(c, rng, 8))
                continue
            xx = (x + 0.5) % tooth
            half = (tooth / 2) * (1 - (y - top - band) / max(1, tip - top - band))
            if abs(xx - tooth / 2) <= half and y < tip:
                _P(img, x, y, _jitter(GOLD if abs(xx - tooth / 2) < half - 1 else GOLD_DARK, rng, 8))
            else:
                _P(img, x, y, (0, 0, 0), 0)


def p_drape_swag(img, rng):
    w, h = img.size
    for y in range(h):
        for x in range(w):
            k = 1.0 + 0.1 * math.sin(y * 0.55 + 0.4 * math.sin(x * 0.12)) + (0.03 if (x + y) % 2 else -0.03)
            _P(img, x, y, _jitter(_scale(RED, k), rng, 4))
    _gold_dots(img, rng, every=8, bottom=h - 12)
    _dagged_band(img, rng, h - 11, band=4, tooth=6)


def p_drape_tail(img, rng):
    w, h = img.size
    for y in range(h):
        for x in range(w):
            k = 1.0 + 0.12 * math.sin(2 * math.pi * x / 8 + 0.3 * math.sin(y * 0.1)) + (0.03 if (x + y) % 2 else -0.03)
            _P(img, x, y, _jitter(_scale(RED, k), rng, 4))
    _gold_dots(img, rng, every=8, bottom=h - 12)
    _dagged_band(img, rng, h - 11, band=4, tooth=5)
    for y in range(h - 11):
        _P(img, 0, y, RED_DARK)
        _P(img, w - 1, y, RED_DARK)


def p_drape_red(img, rng):
    _cloth_base(img, rng, RED, fold_period=8, fold=0.08)
    _gold_dots(img, rng, every=8)


def _lion_mask(W, H):
    """A rampant lion facing left (gold heraldry), as polygons on a supersampled canvas: True where gold."""
    from PIL import Image, ImageDraw
    S = 8
    im = Image.new("L", (W * S, H * S), 0)
    d = ImageDraw.Draw(im)

    def P(pts):
        return [(x * W * S, y * H * S) for x, y in pts]
    # body: chest high on the left, haunches low on the right
    d.polygon(P([(0.30, 0.30), (0.48, 0.24), (0.62, 0.42), (0.70, 0.62), (0.62, 0.70), (0.46, 0.60), (0.36, 0.46)]), fill=255)
    # head and mane
    d.ellipse(P([(0.18, 0.08), (0.46, 0.34)]), fill=255)
    d.polygon(P([(0.30, 0.06), (0.52, 0.10), (0.56, 0.28), (0.44, 0.36), (0.32, 0.32)]), fill=255)
    d.polygon(P([(0.12, 0.20), (0.22, 0.18), (0.22, 0.26), (0.10, 0.27)]), fill=255)        # muzzle
    d.polygon(P([(0.13, 0.27), (0.22, 0.27), (0.20, 0.31), (0.14, 0.31)]), fill=255)        # jaw
    # raised fore legs (to the upper left) with claws
    d.polygon(P([(0.34, 0.34), (0.20, 0.36), (0.08, 0.32), (0.06, 0.37), (0.18, 0.42), (0.34, 0.44)]), fill=255)
    d.polygon(P([(0.38, 0.44), (0.24, 0.50), (0.12, 0.50), (0.12, 0.55), (0.26, 0.56), (0.42, 0.52)]), fill=255)
    # hind legs: one forward-down (left), one standing (right)
    d.polygon(P([(0.50, 0.60), (0.40, 0.72), (0.30, 0.82), (0.24, 0.84), (0.26, 0.88), (0.36, 0.86), (0.50, 0.74), (0.58, 0.66)]), fill=255)
    d.polygon(P([(0.62, 0.62), (0.66, 0.78), (0.60, 0.92), (0.54, 0.94), (0.56, 0.97), (0.66, 0.96), (0.74, 0.80), (0.70, 0.60)]), fill=255)
    # tail curling up behind the back, ending in a tuft
    d.line(P([(0.68, 0.64), (0.82, 0.58), (0.86, 0.44), (0.80, 0.32), (0.84, 0.22)]), fill=255, width=int(W * S * 0.05))
    d.ellipse(P([(0.78, 0.12), (0.92, 0.26)]), fill=255)
    small = im.resize((W, H), Image.BOX)
    return [[small.getpixel((x, y)) > 110 for x in range(W)] for y in range(H)]


def _paint_lion(img, rng, x0, y0, W, H):
    m = _lion_mask(W, H)
    for y in range(H):
        for x in range(W):
            if not m[y][x]:
                continue
            edge = not all(0 <= x + dx < W and 0 <= y + dy < H and m[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            lit = (y + 1 < H and not m[y + 1][x]) is False and (x - 1 >= 0 and m[y][x - 1])
            c = GOLD_DARK if edge else (GOLD_LIGHT if (x + y) % 5 == 0 else GOLD)
            if not edge and not lit:
                c = _scale(GOLD, 0.92)
            _P(img, x0 + x, y0 + y, _jitter(c, rng, 6))
    # the eye and a red tongue
    _P(img, x0 + int(W * 0.26), y0 + int(H * 0.17), _rgb("2a1a08"))
    _P(img, x0 + int(W * 0.12), y0 + int(H * 0.28), _rgb("b02020"))


def p_lion(img, rng):
    w, h = img.size
    for y in range(h):
        for x in range(w):
            _P(img, x, y, (0, 0, 0), 0)
    _paint_lion(img, rng, 0, 0, w, h)


def p_banner_navy(img, rng):
    """Navy banner, gold border, golden rampant lion, the lower end cut into a point with stepped gold dags."""
    w, h = img.size
    _cloth_base(img, rng, NAVY, fold_period=12, fold=0.06)
    body = int(h * 0.78)
    for y in range(h):
        for x in range(w):
            if y >= body:
                half = (w / 2) * (1 - (y - body) / (h - body))
                dx = abs(x + 0.5 - w / 2)
                # stepped (dagged) outline: a notch every 4 rows
                half -= 1.5 * ((y - body) % 4 < 2)
                if dx > half:
                    _P(img, x, y, (0, 0, 0), 0)
                elif dx > half - 3:
                    _P(img, x, y, _jitter(GOLD if dx < half - 1 else GOLD_DARK, rng, 8))
                continue
            if x < 3 or x >= w - 3 or y < 3:
                _P(img, x, y, _jitter(GOLD if 0 < x < w - 1 else GOLD_DARK, rng, 8))
            elif x < 4 or x >= w - 4 or y < 4:
                _P(img, x, y, _jitter(NAVY_DARK, rng, 4))
    _paint_lion(img, rng, 5, int(h * 0.16), w - 10, int(h * 0.5))


def p_net(img, rng):
    """Cut-out diamond mesh of chunky rope (cells 16 px, strands 3 px: lit middle, dark edges), knots at the crossings."""
    w, h = img.size
    cell = 16
    for y in range(h):
        for x in range(w):
            a = (x + y) % cell
            b = (x - y) % cell
            on_a, on_b = a < 3, b < 3
            if on_a or on_b:
                k = a if on_a else b
                c = ROPE_LIGHT if k == 1 else _mix(ROPE_LIGHT, ROPE_DARK, 0.55)
                if ((x * 0.7 + y) % 4) < 1:
                    c = _scale(c, 0.85)
                if on_a and on_b:
                    c = _mix(ROPE_LIGHT, ROPE_DARK, 0.3) if (a == 1 and b == 1) else _scale(ROPE_DARK, 0.9)
                _P(img, x, y, _jitter(c, rng, 4))
            else:
                _P(img, x, y, (0, 0, 0), 0)


def p_net_edge(img, rng):
    w, h = img.size
    for y in range(h):
        for x in range(w):
            _P(img, x, y, (0, 0, 0), 0)
    for x0 in range(4, w, 8):
        L = rng.randint(h // 2, h - 1)
        for y in range(L):
            _P(img, x0 + (1 if y > L * 0.6 else 0), y, _jitter(ROPE_LIGHT if y % 3 else ROPE_DARK, rng, 4))


def p_float_side(img, rng):
    w, h = img.size
    for y in range(h):
        c = WHITE if y < 6 else (_rgb("a8282a") if y < 10 else (WHITE if y < 13 else _rgb("3a4a8a")))
        for x in range(w):
            k = 1.0 + 0.12 * math.cos(math.pi * (x + 0.5 - w / 2) / w)
            _P(img, x, y, _jitter(_scale(c, k), rng, 4))


def p_float_small(img, rng):
    w, h = img.size
    for y in range(h):
        c = _rgb("b03030") if y < h // 2 - 1 else (WHITE if y < h - 3 else _rgb("b03030"))
        for x in range(w):
            _P(img, x, y, _jitter(c, rng, 4))


def p_float_top(img, rng):
    tt._fill(img, _R(img), _rgb("e4dccc"), rng, noise=5)


def p_bundle(stem, cols, kind):
    """A hanging bundle (cut-out): a rope tie at the top, stems spreading down, foliage / flowers in `cols`."""
    def paint(img, rng):
        w, h = img.size
        for y in range(h):
            for x in range(w):
                _P(img, x, y, (0, 0, 0), 0)
        tie = 7
        for y in range(tie):
            for x in range(w // 2 - 2, w // 2 + 2):
                _P(img, x, y, ROPE_LIGHT if (x + y) % 3 else ROPE_DARK)
        n = 11
        for k in range(n):
            x1 = w / 2 + (k - (n - 1) / 2) * (w * 0.8 / n) + rng.uniform(-1, 1)
            L = rng.randint(int(h * 0.75), h - 1)
            for y in range(tie, L):
                t = (y - tie) / max(1, L - tie)
                x = w / 2 + (x1 - w / 2) * (t ** 0.8)
                _P(img, x, y, stem)
                if kind == "leaf" and y > tie + 3 and rng.random() < 0.8:
                    for dx in (-2, -1, 1, 2):
                        if rng.random() < 0.55:
                            _P(img, x + dx, y + (abs(dx) - 1), _jitter(rng.choice(cols), rng, 10))
                elif kind == "spike" and t > 0.45:
                    for dx in (-1, 0, 1):
                        if rng.random() < 0.75:
                            _P(img, x + dx, y, _jitter(rng.choice(cols), rng, 12))
                elif kind == "flower" and t > 0.55 and rng.random() < 0.5:
                    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1)):
                        _P(img, x + dx, y + dy, _jitter(rng.choice(cols), rng, 8))
                    if rng.random() < 0.3:
                        _P(img, x, y, _rgb("e8c84a"))
        for y in range(tie - 2, tie):   # the wrap
            for x in range(w // 2 - 3, w // 2 + 3):
                _P(img, x, y, ROPE_DARK)
    return paint


def p_sail(img, rng):
    tt._weave(img, _R(img), _rgb("e4d6b4"), rng, seams=16, patches=1, stains=3, tears=0, seam_dir="v", noise=4)
    w, h = img.size
    for x in range(w):
        for y in (0, 1, h - 2, h - 1):
            _P(img, x, y, _scale(img.getpixel((x, y)), 0.86))
    for y in range(h):
        for x in (0, 1, w - 2, w - 1):
            _P(img, x, y, _scale(img.getpixel((x, y)), 0.86))


def p_sail_edge(img, rng):
    tt._fill(img, _R(img), _rgb("cbbb94"), rng, noise=5)
    w, h = img.size
    for x in range(0, w, 3):
        _P(img, x, h // 2, _rgb("8a7a58"))


def p_fringe(img, rng):
    tt._fringe(img, _R(img), BEIGE, rng)


# ---------------------------------------------------------------- the atlas
BASE = [  # (name, w, h, painter) in packing order (rows of equal height)
    ("wood", 64, 16, p_wood(WOOD, WOOD_DARK_C)), ("wood_dark", 64, 16, p_wood(_rgb("5a3c22"), _rgb("2a1a0c"))),
    ("wood_light", 64, 16, p_wood(_rgb("9a7448"), _rgb("5a4026"))), ("plank", 64, 16, p_wood(_rgb("845a36"), WOOD_DARK_C, plank_h=8)),
    ("rope_coil", 32, 16, p_rope_coil), ("iron_band", 32, 8, p_iron_band),
    ("end_grain", 16, 16, p_end_grain), ("rope", 16, 16, p_rope), ("iron", 16, 16, p_iron), ("iron_dark", 16, 16, p_iron_dark),
    ("chain", 16, 16, p_chain), ("gold", 16, 16, p_gold), ("gold_rod", 16, 16, p_gold), ("stone_top", 16, 16, p_stone_top),
    ("lantern", 16, 16, p_lantern), ("lantern_grid", 16, 16, p_lantern_grid), ("glow", 16, 16, p_glow), ("flame", 16, 16, p_flame),
    ("float_side", 16, 16, p_float_side), ("float_small", 16, 16, p_float_small), ("float_top", 16, 16, p_float_top),
    ("cloth_red", 32, 32, p_cloth(RED)), ("cloth_yellow", 32, 32, p_cloth(YELLOW)), ("cloth_blue", 32, 32, p_cloth(BLUE)),
    ("cloth_green", 32, 32, p_cloth(GREEN)), ("cloth_white", 32, 32, p_cloth(WHITE)), ("cloth_beige", 32, 32, p_cloth(BEIGE)),
    ("cloth_navy", 32, 32, p_cloth(NAVY)), ("drape_red", 32, 32, p_drape_red), ("stone", 32, 32, p_stone), ("lion", 32, 32, p_lion),
    ("fringe", 32, 16, p_fringe), ("sail_edge", 64, 8, p_sail_edge),
    ("pennant_red", 24, 32, p_pennant(RED, RED_DARK)), ("pennant_yellow", 24, 32, p_pennant(YELLOW, YELLOW_DARK)),
    ("pennant_blue", 24, 32, p_pennant(BLUE, BLUE_DARK)),
    ("sheet_white", 32, 48, p_sheet_white), ("tunic_stripes", 32, 48, p_tunic_stripes), ("cloth_worn", 32, 48, p_cloth_worn),
    ("cloth_red_worn", 32, 48, p_cloth_red_worn),
    ("herbs_green", 32, 48, p_bundle(_rgb("4a5a26"), [_rgb("4e8a2a"), _rgb("6aa23a"), _rgb("3a6a1e"), _rgb("8ab84a")], "leaf")),
    ("herbs_lavender", 32, 48, p_bundle(_rgb("5a6a3a"), [_rgb("7a4ab0"), _rgb("9a6ad0"), _rgb("5a3090"), _rgb("b08ae0")], "spike")),
    ("herbs_sage", 32, 48, p_bundle(_rgb("5a6a42"), [_rgb("8aa070"), _rgb("a2b88a"), _rgb("6e8456"), _rgb("b8c8a0")], "leaf")),
    ("herbs_white", 32, 48, p_bundle(_rgb("5a7a3a"), [_rgb("f2eee0"), _rgb("ffffff"), _rgb("d8d4c4"), _rgb("e8e4d4")], "flower")),
    ("net", 64, 64, p_net), ("net_edge", 64, 16, p_net_edge), ("drape_tail", 32, 64, p_drape_tail),
    ("banner_navy", 48, 96, p_banner_navy), ("drape_swag", 96, 48, p_drape_swag), ("sail", 96, 64, p_sail),
    ("post", 32, 64, p_post(WOOD, WOOD_DARK_C)), ("post_dark", 32, 64, p_post(_rgb("5a3c22"), _rgb("2a1a0c"))),
]
ALIASES = {"canvas": "sail", "peg": "wood_light", "metal": "iron"}

REGIONS = {}
PAINTERS = {}
EXTRA_MODULES = []


class _Packer:
    def __init__(self, size):
        self.size, self.x, self.y, self.row = size, 0, 0, 0

    def alloc(self, w, h):
        if self.x + w > self.size:
            self.x, self.y, self.row = 0, self.y + self.row, 0
        if self.y + h > self.size:
            raise ValueError("the decorations atlas is full (%d px): make the regions smaller" % self.size)
        r = (self.x, self.y, w, h)
        self.x += w
        self.row = max(self.row, h)
        return r


def _build_regions():
    REGIONS.clear()
    PAINTERS.clear()
    pk = _Packer(SIZE)
    # the listing order is the packing order: base positions never move
    for name, w, h, painter in BASE:
        REGIONS[name] = pk.alloc(w, h)
        PAINTERS[name] = painter
    pk.x, pk.y, pk.row = 0, pk.y + pk.row, 0   # extensions start on a fresh row
    for path in sorted(glob.glob(os.path.join(HERE, "atlas_*.py"))):
        mod_name = os.path.splitext(os.path.basename(path))[0]
        mod = importlib.import_module(mod_name)
        EXTRA_MODULES.append(mod_name)
        for name, w, h, painter in getattr(mod, "REGIONS", []):
            if name in REGIONS or name in ALIASES:
                raise KeyError("atlas region %s (from %s) already exists" % (name, mod_name))
            REGIONS[name] = pk.alloc(int(w), int(h))
            PAINTERS[name] = painter
    for a, b in ALIASES.items():
        REGIONS[a] = REGIONS[b]


_build_regions()


def make_texture(path):
    """Paints the whole shared atlas (base regions + atlas_*.py extensions) into `path`."""
    from PIL import Image
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    for name, painter in PAINTERS.items():
        u, v, w, h = REGIONS[name]
        sub = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        painter(sub, random.Random(zlib.crc32(name.encode())))
        img.paste(sub, (u, v))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return img


def setup(name):
    """Resets the collisions and uuids for one decoration and points the shared generators at the atlas (call first)."""
    tl.setup(name)
    gn.REGIONS = {k: (0,) + r for k, r in REGIONS.items()}
    gn.SIZE = SIZE
    gg.REGIONS = dict(REGIONS)
    gg.SIZE = SIZE


# ---------------------------------------------------------------- posts
class Post:
    """What post() returns: foot, top (points on the axis), d (section), and helpers for attachment points."""

    def __init__(self, foot, top, d):
        self.foot, self.top, self.d = v3(*foot), v3(*top), d

    def at(self, y, side=(0, 0, 0)):
        """The point at height y on the post's face towards `side` (a direction, e.g. (1, 0, 0)); (0,0,0) = axis."""
        s = v3(*side)
        p = v3(self.foot[0], y, self.foot[2])
        return p + (norm(s) * self.d / 2 if np.linalg.norm(s) > 1e-9 else 0)

    def top_front(self, dy=0.0):
        return self.at(self.top[1] + dy, (0, 0, 1))


def post(bone, name, foot, height, d=0.32, region="post", bindings=(), bands=(), caps=False, footing=None, top="end_grain",
         solid=True, detail=None, ring_h=0.075, rings=3, band_h=0.16):
    """A squared upright post (section d) standing on foot (x, y, z) up to `height` above it, the grain vertical,
    the top end grain. bindings = heights (above the foot) of rope bindings (rings coils of rope wrapped round,
    each slightly askew); bands = heights of iron bands (with rivets); caps = an iron cap on the top; footing =
    (w, h): a stone footing block under the post (the post then starts on it). Collides as a thin box (and the
    footing) when solid. Returns a Post."""
    foot = v3(*foot)
    det = detail if detail is not None else bone
    if footing:
        fw, fh = footing
        add_cube(bone, name + "_footing", foot + UP * fh / 2, EYE, (fw, fh, fw), {"all": "stone", "+2": "stone_top", "-2": "stone_top"})
        if solid:
            collide((foot[0] - fw / 2, foot[1], foot[2] - fw / 2, foot[0] + fw / 2, foot[1] + fh, foot[2] + fw / 2))
        base = foot + UP * fh
    else:
        base = foot
    topp = foot + UP * height
    add_cube(bone, name, (base + topp) / 2, EYE, (d, height - (base[1] - foot[1]), d), {"all": region, "+2": top, "-2": top},
             v_dir=-UP)
    for k, y in enumerate(bindings):
        for i in range(rings):
            yy = foot[1] + y + (i - (rings - 1) / 2) * ring_h * 0.95
            grow = 0.06 + 0.012 * ((i + k) % 2)
            R = ry(0.06 * ((i % 3) - 1)) @ rz(0.035 * (1 if i % 2 else -1))
            add_cube(det if i % 2 else bone, "%s_bind_%d_%d" % (name, k, i), v3(foot[0], yy, foot[2]), R,
                     (d + 2 * grow, ring_h, d + 2 * grow), {"all": "rope_coil", "+2": "rope", "-2": "rope"}, u_dir=X, density=1.5)
    for k, y in enumerate(bands):
        add_cube(bone, "%s_band_%d" % (name, k), v3(foot[0], foot[1] + y, foot[2]), EYE, (d + 0.05, band_h, d + 0.05),
                 {"all": "iron_band", "+2": "iron", "-2": "iron"}, u_dir=X)
    if caps:
        add_cube(bone, name + "_cap", topp + UP * 0.03, EYE, (d + 0.05, 0.06, d + 0.05), {"all": "iron_band", "+2": "iron", "-2": "iron"})
        add_cube(bone, name + "_cap_band", topp - UP * 0.12, EYE, (d + 0.04, 0.08, d + 0.04), {"all": "iron_band", "+2": "iron", "-2": "iron"})
    if solid:
        collide((foot[0] - d / 2, base[1], foot[2] - d / 2, foot[0] + d / 2, topp[1], foot[2] + d / 2))
    return Post(foot, topp, d)


def binding(bone, name, center, d, rings=3, ring_h=0.075, grow=0.06):
    """Rope rings wrapped round a squared post of section d at `center` (e.g. where a rope meets the post)."""
    center = v3(*center)
    for i in range(rings):
        R = ry(0.07 * ((i % 3) - 1)) @ rz(0.04 * (1 if i % 2 else -1))
        add_cube(bone, "%s_%d" % (name, i), center + UP * (i - (rings - 1) / 2) * ring_h * 0.95, R,
                 (d + 2 * grow, ring_h, d + 2 * grow), {"all": "rope_coil", "+2": "rope", "-2": "rope"}, u_dir=X, density=1.5)


def gallows_arm(bone, name, post_, y, length, direction=(1, 0, 0), d=0.24, region="plank", brace=0.9, brace_d=0.16, overhang=0.12,
                caps=True, detail=None):
    """A horizontal arm from a post (Post) at height y (above the post's foot) out by `length` along direction,
    an angled brace from the post (brace blocks below) to the arm (brace blocks out), iron end caps. Returns the
    arm's tip (the point under its end, on its lower face)."""
    dvec = norm(v3(*direction))
    base = v3(post_.foot[0], post_.foot[1] + y, post_.foot[2])
    a = base - dvec * overhang
    b = base + dvec * length
    beam(bone, name, a, b, d, {"all": region, "+1": "end_grain", "-1": "end_grain"}, width=d * 0.9, up=UP)
    if brace:
        p0 = base + dvec * (post_.d / 2) - UP * brace
        p1 = base + dvec * (post_.d / 2 + brace) - UP * (d / 2)
        beam(bone, name + "_brace", p0 - (p1 - p0) * 0.04, p1 + (p1 - p0) * 0.04, brace_d, "wood", width=brace_d, up=np.cross(dvec, UP))
    if caps:
        det = detail if detail is not None else bone
        add_cube(det, name + "_cap", b - dvec * 0.04, frame(dvec), (0.06, d + 0.04, d * 0.9 + 0.04), {"all": "iron_band", "+1": "iron", "-1": "iron"})
        add_cube(det, name + "_band", b - dvec * 0.3, frame(dvec), (0.08, d + 0.03, d * 0.9 + 0.03), {"all": "iron_band", "+1": "iron", "-1": "iron"})
    return b - dvec * 0.12 - UP * (d / 2)


def frame(u, up=UP):
    """Axes (columns u, v, n) of a box whose first axis is u and second as close to `up` as possible."""
    return gg.frame_from(v3(*u), v3(*up))


# ---------------------------------------------------------------- ropes
def catenary(t, k=1.2):
    """Normalised sag shape: 0 at t = 0 and 1, 1 at t = 0.5 (a catenary of stiffness k)."""
    return (math.cosh(k) - math.cosh(k * (2 * t - 1))) / (math.cosh(k) - 1)


class Line:
    """A sagging rope: at(t) = the point on its axis (t in [0, 1]), tangent(t), sag, the ends."""

    def __init__(self, p0, p1, sag, k=1.2):
        self.p0, self.p1, self.sag, self.k = v3(*p0), v3(*p1), sag, k

    def at(self, t):
        return self.p0 + (self.p1 - self.p0) * t - UP * (self.sag * catenary(t, self.k))

    def tangent(self, t):
        e = 1e-3
        return norm(self.at(min(1, t + e)) - self.at(max(0, t - e)))


def sag_rope(bone, name, p0, p1, sag=0.3, segs=8, d=0.06, region="rope", k=1.2):
    """A rope from p0 to p1 sagging by `sag` in the middle along a catenary, in `segs` tilted segments. Returns its
    Line (hang things with line.at(t))."""
    line = Line(p0, p1, sag, k)
    pts = [line.at(i / segs) for i in range(segs + 1)]
    for i in range(segs):
        beam(bone, "%s_%d" % (name, i), pts[i], pts[i + 1], d, region, extend=d * 0.45)
    return line


def knot(bone, name, p, s=0.09, region="rope"):
    """A small knot / lashing lump at p."""
    add_cube(bone, name, p, ry(0.4) @ rx(0.3), (s, s * 0.9, s), region)


# ---------------------------------------------------------------- cloth
def _hang_frame(a, b, out):
    """u = a -> b (along the rope), n = horizontal normal on the `out` side, v = down in the cloth's plane."""
    u = norm(v3(*b) - v3(*a))
    n = v3(*out)
    n = norm(n - np.dot(n, u) * u)
    return u, n


def pennant(bone, name, a, b, length, region, out=(0, 0, 1), flutter=0.04, tilt=0.06, ny=2):
    """A cloth pennant hanging from the rope between a and b (its top edge follows the rope), `length` long,
    swinging a little out of the plane (tilt) and fluttering; cut-out regions give the dagged end. No collision."""
    a, b = v3(*a), v3(*b)
    u, n = _hang_frame(a, b, out)

    def P(s, t):
        top = a + (b - a) * s
        return top - UP * (length * t) + n * (tilt * t + flutter * math.sin(math.pi * t) * math.sin(math.pi * (s + 0.3)))
    loft(bone, name, P, 1, ny, region, th=0.02, u_hint=u, v_hint=-UP)
    return P


def clothes(bone, name, a, b, length, region, out=(0, 0, 1), pegs=2, detail=None, sway=0.05, nx=3, ny=1, taper=0.0,
            peg_region="peg", peg_h=0.24):
    """A piece of laundry pegged on the rope between a and b: the top edge on the rope, the cloth hanging `length`
    with soft vertical folds (sway: each of the nx strips is planar, so the folds read as light and shade), its bottom corners a little narrower by `taper`; `pegs` clothes pegs straddling the rope
    (under detail). No collision."""
    a, b = v3(*a), v3(*b)
    u, n = _hang_frame(a, b, out)
    W = np.linalg.norm(b - a)

    def P(s, t):
        top = a + (b - a) * s
        p = top - UP * (length * t) + u * ((s - 0.5) * -2 * taper * t * W * 0.5)
        return p + n * (sway * math.sin(math.pi * s * 3 + 0.6) * (0.35 + 0.65 * t) + 0.04 * t)
    loft(bone, name, P, nx, ny, region, th=0.02, u_hint=u, v_hint=-UP)
    det = detail if detail is not None else bone
    for k in range(pegs):
        s = 0.12 + 0.76 * k / max(1, pegs - 1) if pegs > 1 else 0.5
        p = a + (b - a) * s
        R = frame(UP, n)
        R = np.column_stack([R[:, 0], R[:, 1], R[:, 2]])
        add_cube(det, "%s_peg_%d" % (name, k), p + UP * (peg_h * 0.28) + n * 0.01, gg.frame_from(UP + u * 0.08 * (1 if k % 2 else -1), n),
                 (peg_h, 0.07, 0.06), {"all": peg_region, "+1": "end_grain", "-1": "end_grain"})
    return P


def swag(bone, name, a, b, h_end, h_mid, region, out=(0, 0, 1), top_sag=0.2, bulge=0.25, folds=0.05, nx=8, ny=2, th=0.03):
    """A swag of cloth hung between a and b (its top corners): the top edge droops by top_sag, the cloth is h_end
    deep at the ends (gathered at the posts) and h_mid deep in the middle, bellying out towards `out` by bulge, with
    soft folds; the region is stretched over it (v down: put the dagged edge at the bottom of the texture)."""
    a, b = v3(*a), v3(*b)
    u, n = _hang_frame(a, b, out)

    def P(s, t):
        c = catenary(s, 1.0)
        top = a + (b - a) * s - UP * (top_sag * c)
        depth = h_end + (h_mid - h_end) * c
        return top - UP * (depth * t) + n * (bulge * c * math.sin(math.pi * 0.5 * t) + folds * math.sin(s * math.pi * 7) * t)
    loft(bone, name, P, nx, ny, region, th=th, u_hint=u, v_hint=-UP)
    return P


def tail(bone, name, top, width, length, region, out=(0, 0, 1), along=(1, 0, 0), gather=0.55, folds=0.05, nx=2, ny=3, th=0.03):
    """A hanging end of cloth (a drapery's tail): gathered at the top (gather x width wide), full width at the bottom,
    folds across; `along` = the horizontal direction of its width."""
    top = v3(*top)
    u = norm(v3(*along))
    n = v3(*out)
    n = norm(n - np.dot(n, u) * u)

    def P(s, t):
        wdt = width * (gather + (1 - gather) * min(1.0, t * 1.6))
        return top + u * ((s - 0.5) * wdt) - UP * (length * t) + n * (folds * math.sin(s * math.pi * 3 + 0.5) * min(1.0, t * 2))
    loft(bone, name, P, nx, ny, region, th=th, u_hint=u, v_hint=-UP)
    return P


def net(bone, name, line, t0, t1, drop, region="net", out=(0, 0, 1), belly=0.12, nx=6, ny=2, edge=True, th=0.012, drop_fn=None,
        tile=None):
    """A slack rope net hanging from the rope `line` (a Line) between t0 and t1: the cut-out mesh texture on a lofted
    panel, `drop` deep in the middle (drop_fn(s) -> depth overrides), bellying out by `belly`; edge = dangling rope
    ends along the bottom. tile = (fu, fv): each of the nx x ny pieces shows the fraction fu x fv of the texture (the
    net region's mesh repeats every quarter, so 0.25 = one diamond per piece) instead of the whole texture being
    stretched over the panel: finer meshes. No collision."""
    u, n = _hang_frame(line.at(t0), line.at(t1), out)

    def depth(s):
        return drop_fn(s) if drop_fn else drop * (0.25 + 0.75 * math.sin(math.pi * s))

    def P(s, t):
        top = line.at(t0 + (t1 - t0) * s) - UP * 0.03
        return top - UP * (depth(s) * t) + n * (belly * math.sin(math.pi * t) * math.sin(math.pi * s))
    first = len(bone.cubes)
    loft(bone, name, P, nx, ny, region, th=th, u_hint=u, v_hint=-UP)
    if tile:
        for c in bone.cubes[first:]:
            gn.set_sub(c, (0.0, 0.0, tile[0], tile[1]))
    if edge:
        def E(s, t):
            return P(s, 1.0) - UP * (0.18 * t)
        loft(bone, name + "_edge", E, nx, 1, "net_edge", th=th, u_hint=u, v_hint=-UP)
    return P


def float_buoy(bone, name, top, r=0.13, h=0.36, region="float_side", string=0.3, detail=None):
    """A net float (an octagonal buoy: white, a red band, blue at the bottom) hanging on a string from `top`."""
    top = v3(*top)
    det = detail if detail is not None else bone
    if string > 0:
        beam(det, name + "_string", top, top - UP * (string + 0.03), 0.025, "rope")
    c = top - UP * (string + h / 2)
    for k, ang in enumerate((0.0, math.pi / 4)):
        add_cube(bone, "%s_%d" % (name, k), c, ry(ang), (2 * r * 0.83, h, 2 * r * 0.83), {"all": region, "+2": "float_top", "-2": "float_top"},
                 stretch=True, u_dir=None, v_dir=-UP)
    add_cube(det, name + "_cap", c + UP * (h / 2 + 0.03), EYE, (r * 0.9, 0.06, r * 0.9), "float_top")
    return c - UP * h / 2


def bundle(bone, name, top, length=0.7, width=0.42, region="herbs_green", string=0.2, yaw=0.0, detail=None):
    """A bundle of herbs / flowers hanging on a string from `top`: two crossed cut-out planes (the tie at the top of
    the texture), a little rope wrap. Returns the bundle's bottom point."""
    top = v3(*top)
    det = detail if detail is not None else bone
    if string > 0:
        beam(det, name + "_string", top + UP * 0.02, top - UP * (string + 0.02), 0.03, "rope")
    c = top - UP * (string + length / 2)
    for k, a in enumerate((yaw + math.pi / 4, yaw - math.pi / 4)):
        R = ry(a)
        add_cube(bone, "%s_%d" % (name, k), c, R, (width, length, 0.004), {"all": None, "+3": region, "-3": region}, stretch=True,
                 u_dir=R[:, 0], v_dir=-UP)
    add_cube(det, name + "_wrap", top - UP * (string + 0.06), ry(yaw), (0.09, 0.08, 0.09), "rope")
    return c - UP * length / 2


def chain(bone, name, top, length, link=0.12, w=0.08, region="chain"):
    """A hanging chain from `top` down by `length`: links alternating face-on and edge-on (cut-out)."""
    top = v3(*top)
    n = max(2, int(round(length / (link * 0.75))))
    step = length / n
    for k in range(n):
        c = top - UP * (step * (k + 0.5))
        nrm = X if k % 2 == 0 else Z
        upv = UP
        u = np.cross(upv, nrm)
        add_cube(bone, "%s_link_%d" % (name, k), c, np.column_stack([u, upv, nrm]), (w, step * 1.3, 0.012),
                 {"all": None, "+3": region, "-3": region}, stretch=True, u_dir=u, v_dir=-UP)
    return top - UP * length


def lantern(bone, name, p, size=0.3, metal="iron", chain_to=None):
    """A lantern body at p (rebuilt lit on export: lit glass, posts, cap, ring) and its rope / chain up to chain_to."""
    return tl.lantern(bone, name, p, size=size, metal=metal, chain_to=chain_to)


def hanging_lantern(bone, name, anchor, drop=0.3, size=0.3, metal="iron", hook=True, detail=None):
    """A lantern hanging on a chain under `anchor` (an arm, a hook on a post): chain `drop` long, then the lantern
    (rebuilt lit). Returns the lantern's centre."""
    anchor = v3(*anchor)
    det = detail if detail is not None else bone
    if hook:
        add_cube(det, name + "_hook", anchor - UP * 0.03, EYE, (0.05, 0.06, 0.05), "iron_dark")
    end = chain(det, name + "_chain", anchor - UP * 0.04, drop)
    c = end - UP * (size * 1.3 / 2 + 0.06)
    tl.lantern(bone, name, c, size=size, metal=metal)
    return c


def wall_lantern(bone, name, post_, y, side=(1, 0, 0), arm=0.22, size=0.26, drop=0.06, detail=None, metal="iron"):
    """A small lantern hanging from a short iron bracket on the face of a post (Post) at height y towards `side`."""
    s = norm(v3(*side))
    base = post_.at(post_.foot[1] + y, s)
    tip = base + s * arm
    det = detail if detail is not None else bone
    beam(det, name + "_arm", base - s * 0.02, tip, 0.04, "iron_dark", up=UP)
    beam(det, name + "_stay", base - UP * 0.16, base + s * arm * 0.6, 0.03, "iron_dark", up=UP)
    c = tip - UP * (drop + size * 1.3 / 2 + 0.03)
    beam(det, name + "_hanger", tip, c + UP * size * 0.7, 0.025, "iron_dark")
    tl.lantern(bone, name, c, size=size, metal=metal)
    return c


def banner(bone, name, top_center, w, h, normal=(0, 0, 1), region="banner_navy", rod="gold_rod", knobs="gold", wave=0.04,
           rod_extra=0.12):
    """A hanging banner from a rod: top_center = the middle of its top edge, `normal` the side it faces (it reads
    unmirrored from there), cloth slightly waving; the rod (region `rod`) with gold knobs. No collision."""
    top = v3(*top_center)
    n = norm(v3(*normal))
    side = norm(np.cross(UP, n))

    def P(s, t):
        return top + side * ((s - 0.5) * w) - UP * (h * t) + n * (wave * math.sin(math.pi * t) * (0.6 + 0.4 * math.sin(math.pi * s)))
    loft(bone, name, P, 1, 3, region, th=0.02, u_hint=side, v_hint=-UP)
    if rod:
        a, b = top - side * (w / 2 + rod_extra) + UP * 0.03, top + side * (w / 2 + rod_extra) + UP * 0.03
        beam(bone, name + "_rod", a, b, 0.07, rod, width=0.07)
        if knobs:
            for k, p in enumerate((a, b)):
                add_cube(bone, "%s_knob_%d" % (name, k), p, EYE, (0.11, 0.11, 0.11), knobs)
    return P


def sail(bone, name, c00, c10, c01, c11, sag=0.25, region="sail", nx=4, ny=3, th=0.03, ripple=0.03):
    """A cloth sail stretched between four corners (c00, c10 = one edge, c01, c11 = the opposite edge), sagging
    by `sag` in the middle (downwards), rippling a little. Returns P(s, t). No collision."""
    c00, c10, c01, c11 = (v3(*c) for c in (c00, c10, c01, c11))

    def P(s, t):
        p = (c00 * (1 - s) + c10 * s) * (1 - t) + (c01 * (1 - s) + c11 * s) * t
        return p - UP * (sag * math.sin(math.pi * s) * math.sin(math.pi * t) + ripple * math.sin(s * 9.0) * math.sin(math.pi * t))
    loft(bone, name, P, nx, ny, region, th=th)
    return P


# ---------------------------------------------------------------- icons
def icon(path, draw):
    """16x16 item icon: draw(put) paints it; put(x, y, (r, g, b)) (out-of-range pixels ignored)."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()

    def put(x, y, c):
        if 0 <= x < 16 and 0 <= y < 16:
            p[int(x), int(y)] = tuple(int(k) for k in c[:3]) + (255,)
    draw(put)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)


def icon_posts(put, xs=(1, 14), top=(2, 3), bottom=15, wood=(122, 82, 50), dark=(62, 42, 24), rope=(216, 192, 142)):
    """Two posts for an icon (x columns, top rows), a rope binding near each top and an iron band at the foot."""
    for x, t in zip(xs, top):
        for y in range(t, bottom + 1):
            put(x, y, wood if y % 4 else dark)
        put(x, t + 1, rope)
        put(x, bottom - 1, (70, 70, 76))


def icon_sag(put, x0, x1, y0, sag, c=(216, 192, 142)):
    """A sagging rope on an icon from column x0 to x1 at row y0, `sag` rows deep in the middle. Returns y(x)."""
    def y_of(x):
        t = (x - x0) / max(1, x1 - x0)
        return int(round(y0 + sag * catenary(t)))
    for x in range(x0, x1 + 1):
        put(x, y_of(x), c)
    return y_of


# ---------------------------------------------------------------- export
def export(root, name, light=0, icon=None, visible_box=(8, 6, 0)):
    """Writes decorations/<id>.json (with "light"), models/entity/<id>.bbmodel, blockbench/<id>.bbmodel, the shared
    atlas textures/entity/decorations.png and textures/item/<id>.png (icon = a draw(put) function, see icon()).
    DECO_OUT=<file.bbmodel>: writes only the model (and the atlas next to it) there, for previews."""
    light = max(0, min(15, int(light)))
    out_model = os.environ.get("DECO_OUT")
    tex_path = os.path.join(ASSETS, "textures/entity", NAME) if not out_model else os.path.join(os.path.dirname(out_model), NAME)
    make_texture(tex_path)
    with open(tex_path, "rb") as f:
        png = f.read()
    textures = [gn.texture_entry(NAME, SIZE, png, "entity", NAME)]
    textures[0]["id"] = "0"
    ext = tl.extent(root)
    outs = [out_model] if out_model else [os.path.join(ROOT, "blockbench/%s.bbmodel" % name),
                                          os.path.join(ASSETS, "models/entity/%s.bbmodel" % name)]
    model = gn.export(root, [], textures, outs, name=name, visible_box=visible_box)
    if not out_model:
        data = {
            "model": "models/entity/%s.bbmodel" % name,
            "texture": "textures/entity/" + NAME,
            "decor": None,
            "extent": [round(float(v), 3) for v in ext],
            "colliders": [[round(float(v), 3) for v in (b[0], max(0.0, b[1]), b[2], b[3], b[4], b[5])] for b in COLLIDERS],
            "light": light,
        }
        path = os.path.join(ASSETS, "decorations/%s.json" % name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=1)
        if icon is not None:
            globals()["icon"](os.path.join(ASSETS, "textures/item/%s.png" % name), icon)
    print("%s: %d cubes, extent %s, %d collision boxes, light %d" % (name, len(model["elements"]), ["%.2f" % v for v in ext],
                                                                       len(COLLIDERS), light))
    return model


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ASSETS, "textures/entity", NAME)
    make_texture(out)
    for k, r in REGIONS.items():
        print("%-16s %s" % (k, r))
    print("extensions:", EXTRA_MODULES or "none")
