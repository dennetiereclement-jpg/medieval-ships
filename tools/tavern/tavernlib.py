"""Atlas, props and export of the NOMAD TAVERN (1.19.0, taverne_nomade): one block, static, drawn like the carts /
merchant tents / training areas from a .bbmodel (TentType JSON group "carts", tab "Charrettes").

Built on tools/merchant/merchantlib.py (the shell atlas regions, banner, barrel, crate, sack, bottle, plate...),
tools/carts/cartlib.py (wheels, barrels), tools/tents/tentlib.py (Bone, beam, loft, lantern, collide, Decor) and
tools/workshops/wslib_b.py (cauldron, fire, chest, chain). Nothing of those files is changed: the tavern's own paint
code (the beer-mug emblem and banners, the hanging sign, the patched canvas, the striped dagged awning, the patterned
rug, chimney bricks, pavers, lattice window, tankards, bottle rows) lives here.

A generator (tools/tavern/generate_taverne_nomade.py) does, in this order:

    import tavernlib as tv
    tv.setup("taverne_nomade")                  # resets collisions / uuids / seats (call first)
    atlas = tv.Atlas("taverne_nomade")          # merchantlib shell (darkred) + the tavern regions
    root = tv.Bone("taverne_nomade"); detail = tv.Bone("detail", parent=root)
    ... tv.table / tv.mug / tv.keg / tv.mug_banner / tv.hanging_sign / tv.campfire / tv.tripod_cauldron ...
    decor = tv.Decor()
    tv.stool(decor, x, y, z, yaw_deg)           # furnish:spruce_stool + its stand-in + a seat (contract B)
    tv.export(root, "taverne_nomade", atlas, decor=decor, particles=[...], icon=fn)

Coordinates: prop-local blocks, y up (y = 0 = top of the ground block), +z = the FRONT (towards the player who placed
it), the anchor block's centre (0, 0, 0). Small things go under the bone "detail" (hidden beyond the decor distance).
Cubes whose name starts with "glow" are drawn full bright; a cube whose 4 sides use the "lantern" region is rebuilt as
a lit lantern on export (tools/lanterns.py).

Seats (contract B of the 1.19.0 brief): carts/<id>.json gets "seats": [{"pos": [x, y, z], "yaw": deg}, ...], pos = the
centre of the seat SURFACE (top of the stool) prop-local, yaw = the direction the sitter faces (0 = +z, 90 = -x,
180 = -z, 270 = +x), turned with the prop's facing by the Java side.
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
sys.path.insert(0, os.path.join(TOOLS, "merchant"))
sys.path.insert(0, os.path.join(TOOLS, "workshops"))
import merchantlib as ml  # noqa: E402
import wslib_b as wl  # noqa: E402

tl, gg, gn, cl = ml.tl, ml.gg, ml.gn, ml.cl
v3, norm, Bone, add_cube, beam, loft = ml.v3, ml.norm, ml.Bone, ml.add_cube, ml.beam, ml.loft
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ASSETS, ROOT = ml.ASSETS, ml.ROOT
collide, collide_segment, rope, COLLIDERS = ml.collide, ml.collide_segment, ml.rope, ml.COLLIDERS
ry, rx, rz = ml.ry, ml.rx, ml.rz
_rgb, _jitter, _mix, _scale = ml._rgb, ml._jitter, ml._mix, ml._scale
fine_wood, hammered_iron, end_grain = ml.fine_wood, ml.hammered_iron, ml.end_grain
box, rbox, octo, plate, crossed = ml.box, ml.rbox, ml.octo, ml.plate, ml.crossed
GROUP = "carts"

WINE = _rgb("7c1e22")          # the banners' and the canvas' wine red
WINE_DARK = _rgb("4a0e12")
BEIGE = ml.BEIGE
GOLD, GOLD_DARK = ml.GOLD, ml.GOLD_DARK
CREAM = _rgb("f2e8cc")
AMBER = _rgb("d8902a")
OUTLINE = _rgb("3a2414")

SEATS = []
STOOL = "furnish:spruce_stool"          # seat_height 0.5625 (catalog), footprint 0.625 x 0.625
STOOL_TOP = 0.5625
STOOL_HALF = 0.3125


def setup(name):
    """Resets the collision list, the uuids, the region tables and the seats (call first)."""
    ml.setup(name)
    SEATS.clear()


# ---------------------------------------------------------------- painting (each painter gets a w x h RGBA image)
def _seed(s):
    return sum((i + 1) * ord(c) for i, c in enumerate(s)) * 7919 % 1000003


def _px(img, x, y, c, a=255):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((int(x), int(y)), tuple(int(k) for k in c[:3]) + (a,))


def _full(img):
    return (0, 0, img.width, img.height)


# the beer mug emblem, 16 x 16 pixel art: o outline, f foam, F foam shade, a amber beer, A dark amber, h highlight,
# c the glass / pewter wall (cream), . transparent
MUG = [
    "................",
    "....ff.fff......",
    "..fffffffFff....",
    ".ffffffffffff...",
    ".fFffffFfffFf...",
    ".cfFffFfaFfFc...",
    ".chaaAaaaaaAccc.",
    ".chaaAaaaaaAc.cc",
    ".chaaAaaaaaAc..c",
    ".chaaAaaaaaAc..c",
    ".chaaAaaaaaAc.cc",
    ".chaaAaaaaaAccc.",
    ".chaaAaaaaaAc...",
    ".cAAAAAAAAAAc...",
    ".cccccccccccc...",
    "................",
]


def draw_mug(img, x0, y0, scale=1, rng=None, wall=CREAM):
    """Draws the 16 x 16 mug emblem at (x0, y0), each pixel scale x scale."""
    pal = {"f": _rgb("fbf6ea"), "F": _rgb("d8cfb8"), "a": AMBER, "A": _rgb("9a5a14"), "h": _rgb("f2c060"), "c": wall,
           "o": OUTLINE}
    for j, row in enumerate(MUG):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            c = pal[ch]
            if rng is not None:
                c = _jitter(c, rng, 5)
            for dy in range(scale):
                for dx in range(scale):
                    _px(img, x0 + i * scale + dx, y0 + j * scale + dy, c)
    # a dark outline round the drawn pixels
    pts = set()
    for j, row in enumerate(MUG):
        for i, ch in enumerate(row):
            if ch != ".":
                pts.add((i, j))
    for (i, j) in list(pts):
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (i + di, j + dj)
            if q not in pts and 0 <= q[0] < 16 and 0 <= q[1] < 16 and MUG[q[1]][q[0]] == ".":
                if (q[0] in (13, 14) and 7 <= q[1] <= 10):
                    continue      # the hole of the handle stays open (shows the field)
                for dy in range(scale):
                    for dx in range(scale):
                        _px(img, x0 + q[0] * scale + dx, y0 + q[1] * scale + dy, OUTLINE)


def paint_banner_mug(img, rng):
    """Wine-red hanging banner, a dark sleeve at the top, thin dark side edges, the mug emblem, a GOLD dagged hem at the
    bottom (square dags, cut out between them)."""
    w, h = img.width, img.height
    ml._weave(img, _full(img), WINE, rng, stains=1)
    hem = int(h * 0.80)       # gold band from here, dags below
    dag_w = max(3, w // 6)
    for y in range(h):
        for x in range(w):
            if y < 3:
                _px(img, x, y, _jitter(WINE_DARK, rng, 4))
            elif x < 2 or x >= w - 2:
                _px(img, x, y, _jitter(_scale(WINE, 0.7), rng, 4))
            if y >= hem:
                k = (x // dag_w) % 2
                bottom = h - 1 if k == 0 else h - 1 - int(h * 0.09)
                if y > bottom:
                    _px(img, x, y, (0, 0, 0), 0)
                elif y < hem + 2 or y > bottom - 2 or x % dag_w in (0, dag_w - 1):
                    _px(img, x, y, _jitter(GOLD_DARK, rng, 8))
                else:
                    _px(img, x, y, _jitter(GOLD, rng, 10))
            elif y == hem - 1:
                _px(img, x, y, _jitter(_scale(WINE, 0.6), rng, 4))
    s = max(1, (w - 6) // 16)
    draw_mug(img, (w - 16 * s) // 2 + s, int(h * 0.22), s, rng)


def paint_sign(img, rng):
    """The hanging tavern sign: a frame of dark wood with iron corner plates and rivets, a plank field, the mug."""
    w, h = img.width, img.height
    fine_wood(img, _full(img), _rgb("7a5232"), _rgb("3e2814"), 6, rng, joints=False, knots=0.1, grain=0.1, shade=0.06, vertical=True)
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            if e < 3:
                _px(img, x, y, _jitter(_rgb("3a2412"), rng, 5))
            elif e == 3:
                _px(img, x, y, _jitter(_rgb("2a180a"), rng, 3))
            corner = (x < 7 or x >= w - 7) and (y < 7 or y >= h - 7)
            if corner and e < 5:
                _px(img, x, y, _jitter(_rgb("4a4a50"), rng, 6))
    for (x, y) in ((2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)):
        _px(img, x, y, _rgb("a8a8b0"))
    s = max(1, (w - 10) // 16)
    draw_mug(img, (w - 16 * s) // 2 + s // 2, (h - 16 * s) // 2 + s // 2, s, rng)


def _patched(img, rng, base, patch_tones, n=6, seams=0):
    w, h = img.width, img.height
    ml._weave(img, _full(img), base, rng, seams=seams, seam_dir="v", stains=3)
    for _ in range(n):
        pw, ph = rng.randint(w // 8, w // 4), rng.randint(h // 6, h // 3)
        x0, y0 = rng.randint(0, w - pw), rng.randint(0, h - ph)
        tone = rng.choice(patch_tones)
        for y in range(ph):
            for x in range(pw):
                edge = x in (0, pw - 1) or y in (0, ph - 1)
                c = _scale(tone, 0.66) if edge and (x + y) % 2 == 0 else _jitter(_scale(tone, 1.0 + 0.04 * ((x + y) % 2)), rng, 5)
                _px(img, x0 + x, y0 + y, c)
    # soft folds along v (the hoops)
    for y in range(h):
        for x in range(w):
            r, g, b, a = img.getpixel((x, y))
            k = 0.92 + 0.12 * math.sin(math.pi * (x / w) * 3) ** 2
            img.putpixel((x, y), _scale((r, g, b), k) + (255,))


def paint_canvas_red(img, rng):
    _patched(img, rng, WINE, [_rgb("8e2a26"), _rgb("6a1a1c"), _rgb("9a3a2a"), _rgb("5e2018")], n=7, seams=21)


def paint_canvas_beige(img, rng):
    _patched(img, rng, _rgb("e2d4b0"), [_rgb("d4c49c"), _rgb("efe4c8"), _rgb("c8b48a"), _rgb("e8d8b8")], n=7, seams=21)
    w, h = img.width, img.height
    for _ in range(5):        # grey-brown weather stains
        cx, cy, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(4, 9)
        for y in range(h):
            for x in range(w):
                d = math.hypot(x - cx, (y - cy) * 1.3) / r
                if d < 1:
                    c = img.getpixel((x, y))
                    img.putpixel((x, y), _mix(c[:3], _rgb("8a7a5a"), 0.18 * (1 - d)) + (255,))


def paint_awning(img, rng, n=6):
    """Awning cloth: n stripes along v (wine red / beige in turn), patched and stitched."""
    w, h = img.width, img.height
    sw = w // n
    for k in range(n):
        base = WINE if k % 2 == 0 else _rgb("e6d8b6")
        sub = img.crop((0, 0, sw, h))
        ml._weave(sub, (0, 0, sw, h), base, rng, stains=1)
        img.paste(sub, (k * sw, 0))
        for y in range(h):
            for x in (k * sw, k * sw + sw - 1):
                c = img.getpixel((x, y))
                img.putpixel((x, y), _scale(c[:3], 0.72) + (255,))
    for _ in range(4):
        pw, ph = rng.randint(5, 9), rng.randint(5, 10)
        x0, y0 = rng.randint(1, w - pw - 1), rng.randint(1, h - ph - 1)
        for y in range(ph):
            for x in range(pw):
                c = img.getpixel((x0 + x, y0 + y))
                edge = x in (0, pw - 1) or y in (0, ph - 1)
                img.putpixel((x0 + x, y0 + y), (_scale(c[:3], 0.7) if edge and (x + y) % 2 else _scale(c[:3], 0.9)) + (255,))


def paint_valance(img, rng, n=6):
    """Dagged valance: n panels (wine / beige in turn) whose bottom is cut in ragged pointed tatters (cut-out)."""
    w, h = img.width, img.height
    pw = w // n
    for k in range(n):
        base = WINE if k % 2 == 0 else _rgb("e6d8b6")
        sub = img.crop((0, 0, pw, h))
        ml._weave(sub, (0, 0, pw, h), base, rng, stains=0)
        img.paste(sub, (k * pw, 0))
    solid = int(h * 0.55)
    for x in range(w):
        lx = x % pw
        # three pointed tatters per panel, of uneven length
        t = (lx % (pw / 3)) / (pw / 3)
        tip = 1 - abs(2 * t - 1)
        r = random.Random(x // max(1, int(pw / 3)) * 31 + 7).uniform(0.7, 1.0)
        bottom = solid + int((h - 1 - solid) * tip * r)
        for y in range(h):
            if y > bottom:
                _px(img, x, y, (0, 0, 0), 0)
            elif y < 2:
                _px(img, x, y, _jitter(_rgb("3a2412"), rng, 4))
            elif lx in (0, pw - 1):
                c = img.getpixel((x, y))
                _px(img, x, y, _scale(c[:3], 0.7))


def paint_rug(img, rng):
    """A rectangular red patterned rug: dark border, gold and beige bands, a row of small diamonds, a field of
    wine red with three diamond medallions and corner motifs."""
    w, h = img.width, img.height
    ml._weave(img, _full(img), _rgb("8a2420"), rng, stains=2)
    navy, gold, cream, dark = _rgb("2a2238"), _rgb("c89a3a"), _rgb("e8dcbc"), _rgb("4a1410")
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            if e < 2:
                _px(img, x, y, _jitter(dark, rng, 4))
            elif e < 3:
                _px(img, x, y, _jitter(gold, rng, 8))
            elif e < 8:
                # border band: navy with small cream / gold diamonds
                p = (x + y) if (y < 8 or y >= h - 8) else (y + x)
                cx = ((x if (y < 8 or y >= h - 8) else y) % 6) - 2.5
                cy = e - 5
                if abs(cx) + abs(cy) < 2.2:
                    _px(img, x, y, _jitter(gold if p % 12 < 6 else cream, rng, 6))
                else:
                    _px(img, x, y, _jitter(navy, rng, 5))
            elif e < 9:
                _px(img, x, y, _jitter(gold, rng, 8))
            elif e < 10:
                _px(img, x, y, _jitter(dark, rng, 4))
    # medallions along the long axis
    for k, fx in enumerate((0.25, 0.5, 0.75)):
        cx, cy = w * fx, h / 2
        R = h * (0.26 if k == 1 else 0.18)
        for y in range(h):
            for x in range(w):
                d = abs(x - cx) / 1.0 + abs(y - cy) * 1.0
                if d < R:
                    if d > R - 2:
                        c = gold
                    elif d > R - 4:
                        c = navy
                    elif d < R * 0.3:
                        c = cream
                    elif d < R * 0.45:
                        c = gold
                    else:
                        c = _rgb("a83a2a")
                    _px(img, x, y, _jitter(c, rng, 6))
    # small corner motifs
    for cx, cy in ((14, 14), (w - 15, 14), (14, h - 15), (w - 15, h - 15)):
        for y in range(-3, 4):
            for x in range(-3, 4):
                if abs(x) + abs(y) <= 3:
                    _px(img, cx + x, cy + y, _jitter(gold if abs(x) + abs(y) == 3 else navy, rng, 6))


def paint_stone_bricks(img, rng):
    """Dark grey chimney bricks (courses of 4 px, bricks of 8 px)."""
    w, h = img.width, img.height
    base = _rgb("5e5c5a")
    for y in range(h):
        row = y // 4
        off = 4 * (row % 2)
        for x in range(w):
            bx = (x + off) // 8
            tone = _scale(base, 0.8 + 0.4 * ((bx * 7 + row * 13) % 5) / 4)
            if y % 4 == 3 or (x + off) % 8 == 7:
                c = _scale(base, 0.5)
            elif y % 4 == 0:
                c = _scale(tone, 1.12)
            else:
                c = tone
            _px(img, x, y, _jitter(c, rng, 6))


def paint_stone_top(img, rng):
    w, h = img.width, img.height
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            c = _rgb("6a6866") if e > 1 else _rgb("4a4846")
            _px(img, x, y, _jitter(c, rng, 8))


def paint_cobble(img, rng, base=_rgb("8a8780")):
    """Rounded grey stones with dark joints (the fire ring)."""
    w, h = img.width, img.height
    seeds = [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(0.8, 1.15)) for _ in range(max(6, w * h // 40))]
    for y in range(h):
        for x in range(w):
            ds = sorted((math.hypot(x - sx, y - sy), k) for sx, sy, k in seeds)
            d0, k = ds[0]
            d1 = ds[1][0]
            c = _scale(base, 0.45) if d1 - d0 < 1.0 else _scale(base, k * (1.1 if d0 < 2 else 1.0))
            _px(img, x, y, _jitter(c, rng, 6))


def paint_pavers(img, rng):
    """Stone pavers lying in the grass (cut-out: the gaps show the ground), irregular rectangles, mossy edges."""
    w, h = img.width, img.height
    for y in range(h):
        for x in range(w):
            _px(img, x, y, (0, 0, 0), 0)
    y = 0
    while y < h:
        rh = rng.randint(5, 8)
        x = rng.randint(-3, 2)
        while x < w:
            rw = rng.randint(6, 11)
            if rng.random() < 0.86:
                tone = _scale(_rgb("8e8a82"), rng.uniform(0.78, 1.12))
                for yy in range(y, min(h, y + rh - 1)):
                    for xx in range(max(0, x), min(w, x + rw - 1)):
                        e = min(xx - x, yy - y, x + rw - 2 - xx, y + rh - 2 - yy)
                        c = _scale(tone, 0.82) if e == 0 else tone
                        if e == 0 and rng.random() < 0.25:
                            c = _rgb("5a6a34")
                        _px(img, xx, yy, _jitter(c, rng, 7))
            x += rw
        y += rh
    # a ragged outline: drop stones near the edges of the region
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            if e < 6 and rng.random() < (6 - e) / 7.0:
                _px(img, x, y, (0, 0, 0), 0)


def paint_window(img, rng):
    """A lit lattice window with an arched top (cut-out above the arch): amber glow, dark diamond lattice."""
    w, h = img.width, img.height
    cx = (w - 1) / 2
    for y in range(h):
        for x in range(w):
            r = w / 2
            if y < r and math.hypot(x - cx, (r - y) - 0.5) > r:
                _px(img, x, y, (0, 0, 0), 0)
                continue
            glow = _mix(_rgb("ffd27a"), _rgb("f09a2a"), min(1, abs(x - cx) / w + y / h * 0.4))
            lat = ((x + y) % 5 == 0) or ((x - y) % 5 == 0)
            edge = x in (0, w - 1) or y == h - 1 or (y < r and math.hypot(x - cx, (r - y) - 0.5) > r - 1.2)
            if edge:
                _px(img, x, y, _rgb("2a1a0c"))
            elif lat:
                _px(img, x, y, _rgb("4a3018"))
            else:
                _px(img, x, y, _jitter(glow, rng, 6))


def paint_door(img, rng):
    """A plank door: vertical dark planks, two iron strap hinges, a ring handle."""
    w, h = img.width, img.height
    fine_wood(img, _full(img), _rgb("5e3e22"), _rgb("2a1a0a"), 6, rng, joints=False, knots=0.1, grain=0.12, shade=0.08, vertical=True)
    for y in range(h):
        for x in range(w):
            if x in (0, w - 1) or y in (0, h - 1):
                _px(img, x, y, _rgb("24160a"))
    for yy in (int(h * 0.22), int(h * 0.78)):
        for x in range(1, int(w * 0.75)):
            for dy in (0, 1):
                _px(img, x, yy + dy, _jitter(_rgb("3a3a40"), rng, 6))
        _px(img, int(w * 0.75), yy, _rgb("6a6a70"))
    for (x, y) in ((int(w * 0.8), int(h * 0.52)), (int(w * 0.8) + 1, int(h * 0.52)), (int(w * 0.8), int(h * 0.52) + 1)):
        _px(img, x, y, _rgb("8a8a90"))


def paint_mug_side(img, rng):
    """A wooden tankard: light staves, two dark iron bands."""
    w, h = img.width, img.height
    for y in range(h):
        for x in range(w):
            c = _rgb("a8784a") if (x // 3) % 2 else _rgb("94683e")
            if y in (2, 3, h - 4, h - 3):
                c = _rgb("3e3e44")
            _px(img, x, y, _jitter(c, rng, 6))


def paint_foam(img, rng):
    w, h = img.width, img.height
    for y in range(h):
        for x in range(w):
            c = _rgb("fbf6ea") if rng.random() > 0.2 else _rgb("e4dac2")
            _px(img, x, y, _jitter(c, rng, 4))


def paint_bottle_row(img, rng):
    """A row of bottles seen from the front (cut-out): green, brown, wine and amber glass, corks, highlights."""
    w, h = img.width, img.height
    for y in range(h):
        for x in range(w):
            _px(img, x, y, (0, 0, 0), 0)
    cols = [_rgb("2e6a30"), _rgb("5a3418"), _rgb("6e1a22"), _rgb("b0701e"), _rgb("2a4a2a"), _rgb("3a5a7a")]
    x = 1
    while x < w - 4:
        bw = rng.choice((4, 4, 5, 6))
        c = rng.choice(cols)
        bh = rng.randint(int(h * 0.55), int(h * 0.75))
        neck = rng.randint(3, 5)
        top = h - bh - neck
        for yy in range(h - bh, h):
            for xx in range(x, x + bw):
                k = 1.35 if xx == x + 1 else 0.75 if xx == x + bw - 1 else 1.0
                _px(img, xx, yy, _jitter(_scale(c, k), rng, 4))
        nx = x + bw // 2 - 1
        for yy in range(top, h - bh):
            for xx in (nx, nx + 1):
                _px(img, xx, yy, _scale(c, 1.1))
        for xx in (nx, nx + 1):
            _px(img, xx, top - 1, _rgb("a87c50"))
            _px(img, xx, top - 2, _rgb("a87c50"))
        x += bw + rng.choice((0, 1, 1))


def paint_chest_front(img, rng):
    w, h = img.width, img.height
    fine_wood(img, _full(img), _rgb("6a4628"), _rgb("2e1c0a"), 5, rng, joints=False, knots=0.1, grain=0.1, shade=0.06)
    iron = _rgb("3c3c42")
    for y in range(h):
        for x in range(w):
            if x < 2 or x >= w - 2 or y < 2 or y >= h - 2 or abs(x - w * 0.25) < 1.5 or abs(x - w * 0.75) < 1.5:
                _px(img, x, y, _jitter(iron, rng, 6))
    for y in range(int(h * 0.3), int(h * 0.62)):
        for x in range(int(w / 2 - 3), int(w / 2 + 3)):
            _px(img, x, y, _jitter(_rgb("b08a3a"), rng, 8))
    _px(img, int(w / 2), int(h * 0.48), _rgb("1a1a1a"))


def paint_chest_side(img, rng):
    w, h = img.width, img.height
    fine_wood(img, _full(img), _rgb("6a4628"), _rgb("2e1c0a"), 5, rng, joints=False, knots=0.1, grain=0.1, shade=0.06)
    for y in range(h):
        for x in range(w):
            if x < 2 or x >= w - 2 or y < 2 or y >= h - 2:
                _px(img, x, y, _jitter(_rgb("3c3c42"), rng, 6))


def paint_keg_end(img, rng):
    w, h = img.width, img.height
    end_grain(img, _full(img), _rgb("9a6a3e"), _rgb("4a3018"), rng)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - cy)
            if d > w / 2:
                _px(img, x, y, _rgb("3a3a3e"))
            elif d > w / 2 - 1.5:
                _px(img, x, y, _rgb("4a4a50"))


def paint_stew(img, rng):
    w, h = img.width, img.height
    for y in range(h):
        for x in range(w):
            r = rng.random()
            c = _rgb("8a4a1c") if r < 0.5 else _rgb("a8602a") if r < 0.8 else _rgb("c88a3a")
            if r > 0.95:
                c = _rgb("5a7a2a")
            _px(img, x, y, c)


def paint_fire(img, rng):
    import ws_texture_b as wt
    wt._fire(img, _full(img), rng)


def paint_bark(img, rng):
    import cart_texture as ct
    ct._bark(img, _full(img), rng)


def paint_log_end(img, rng):
    end_grain(img, _full(img), _rgb("b89060"), _rgb("5e4022"), rng)


def paint_iron_dark(img, rng):
    hammered_iron(img, _full(img), _rgb("2a2a2e"), rng)


def paint_cauldron(img, rng):
    hammered_iron(img, _full(img), _rgb("26262a"), rng, dent=0.12)


def paint_dark_planks(img, rng):
    """The wagon's walls: dark brown horizontal planks with visible joints."""
    fine_wood(img, _full(img), _rgb("5a3a20"), _rgb("261608"), 5, rng, joints=True, knots=0.15, grain=0.12, shade=0.1)


def paint_timber(img, rng):
    """Light-brown squared timber (posts, beams) with grain along u."""
    fine_wood(img, _full(img), _rgb("8a5e36"), _rgb("4a3018"), 16, rng, joints=False, knots=0.25, grain=0.12, shade=0.08)


IVY_GREENS = [_rgb("2e5a1e"), _rgb("3e7228"), _rgb("4f8a32"), _rgb("2a4a1a"), _rgb("5e9a3a"), _rgb("6aa848")]


def _leaf(img, x, y, c, rng):
    """A small ivy leaf: a 3 x 3 blob with a lighter top-left and a darker bottom-right pixel."""
    for dx, dy, k in ((0, 0, 1.0), (1, 0, 1.08), (-1, 0, 0.92), (0, 1, 0.85), (0, -1, 1.15), (1, 1, 0.8), (-1, -1, 1.1)):
        if rng.random() < 0.9:
            _px(img, x + dx, y + dy, _jitter(_scale(c, k), rng, 6))


def paint_ivy_mat(img, rng):
    """A dense mat of ivy lying on the canvas (cut-out): leaves almost everywhere in the middle, thinning out towards
    ragged edges, a few stems."""
    w, h = img.width, img.height
    for y in range(h):
        for x in range(w):
            _px(img, x, y, (0, 0, 0), 0)
    # the mat's outline: a few overlapping blobs inside the region (organic edges, not a rectangle)
    blobs = [(rng.uniform(0.25, 0.75) * w, rng.uniform(0.2, 0.8) * h, rng.uniform(0.18, 0.32) * min(w, h)) for _ in range(9)]
    for _ in range(int(w * h / 3.0)):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        inside = max(1.0 - math.hypot(x - bx, y - by) / br for bx, by, br in blobs)
        if rng.random() < (0.92 if inside > 0.15 else 0.5 if inside > 0 else 0.04):
            _leaf(img, int(x), int(y), rng.choice(IVY_GREENS), rng)
    for _ in range(6):
        x, y = rng.uniform(0, w), 0.0
        while y < h:
            _px(img, x, y, _rgb("5a4a26"))
            x += rng.choice((-1, 0, 1))
            y += 1


def paint_ivy_hang(img, rng):
    """Hanging ivy strands (cut-out): a dense band at the top, 4-6 strands of leaves of uneven length below."""
    w, h = img.width, img.height
    for y in range(h):
        for x in range(w):
            _px(img, x, y, (0, 0, 0), 0)
    for _ in range(int(w * 2.2)):
        x, y = rng.uniform(0, w), rng.uniform(0, h * 0.1)
        _leaf(img, int(x), int(y), rng.choice(IVY_GREENS), rng)
    for k in range(4):
        x = (k + 0.5) * w / 4 + rng.uniform(-2, 2)
        L = rng.uniform(0.4, 1.0) * h
        y = 0.0
        while y < L:
            _px(img, x, y, _rgb("5a4a26"))
            if rng.random() < 0.42:
                _leaf(img, int(x + rng.choice((-2, 2))), int(y), rng.choice(IVY_GREENS), rng)
            x += rng.choice((-1, 0, 0, 1)) * 0.6
            y += 1


def paint_smoke(img, rng):
    w, h = img.width, img.height
    for y in range(h):
        for x in range(w):
            _px(img, x, y, (0, 0, 0), 0)
    for k in range(9):
        cx = w / 2 + math.sin(k * 0.9) * w * 0.18
        cy = h - 1 - k * h / 9
        r = 2.2 + k * 0.45
        for y in range(h):
            for x in range(w):
                d = math.hypot(x - cx, y - cy)
                if d < r:
                    g = int(200 + 30 * (1 - d / r) - k * 4)
                    _px(img, x, y, (g, g, g - 6), 255)


_TAVERN = [  # (name, w, h, painter)
    ("tv_banner", 32, 56, paint_banner_mug),
    ("tv_sign", 32, 32, paint_sign),
    ("tv_canvas_red", 128, 64, paint_canvas_red),
    ("tv_canvas_beige", 96, 64, paint_canvas_beige),
    ("tv_awning", 96, 64, paint_awning),
    ("tv_valance", 96, 16, paint_valance),
    ("tv_rug", 96, 72, paint_rug),
    ("tv_bricks", 32, 32, paint_stone_bricks),
    ("tv_stone_top", 16, 16, paint_stone_top),
    ("tv_cobble", 32, 32, paint_cobble),
    ("tv_pavers", 96, 96, paint_pavers),
    ("tv_window", 16, 24, paint_window),
    ("tv_door", 24, 40, paint_door),
    ("tv_mug", 16, 16, paint_mug_side),
    ("tv_foam", 16, 16, paint_foam),
    ("tv_bottles", 64, 16, paint_bottle_row),
    ("tv_planks", 64, 32, paint_dark_planks),
    ("tv_timber", 64, 16, paint_timber),
    ("tv_keg_end", 16, 16, paint_keg_end),
    ("tv_smoke", 16, 32, paint_smoke),
    ("tv_ivy", 64, 64, paint_ivy_mat),
    ("tv_ivy_hang", 32, 64, paint_ivy_hang),
    # the regions of the wslib_b cauldron / fire / chest / chain (painted here, same looks)
    ("chest_front", 32, 20, paint_chest_front),
    ("chest_side", 16, 16, paint_chest_side),
    ("chest_top", 32, 16, paint_chest_side),
    ("cauldron", 32, 32, paint_cauldron),
    ("iron_dark", 16, 16, paint_iron_dark),
    ("fire", 32, 32, paint_fire),
    ("bark", 32, 32, paint_bark),
    ("log_end", 16, 16, paint_log_end),
    ("stew", 16, 16, paint_stew),
]


def _painter(name, fn):
    def paint(img):
        fn(img, random.Random(_seed(name)))
    return paint


class Atlas(ml.Atlas):
    """merchantlib.Atlas (the shell regions, darkred) + the tavern regions (see the module doc)."""

    def __init__(self, name, colour="darkred", size=512):
        super().__init__(name, colour=colour, size=size)
        for n, w, h, fn in _TAVERN:
            self.add(n, w, h, _painter(n, fn))


# ---------------------------------------------------------------- props
def stool_model(bone, name, foot, yaw=0.0, top=STOOL_TOP, half=STOOL_HALF):
    """A square wooden stool (the stand-in of furnish:spruce_stool, same footprint and seat height): a thick plank
    seat, four square legs slightly splayed, two stretchers."""
    f = v3(*foot)
    R = ry(yaw)
    th = 0.1
    add_cube(bone, name + "_seat", f + UP * (top - th / 2), R, (2 * half, th, 2 * half), {"all": "plank", "+2": "plank", "-2": "wood_dark"})
    leg = 0.11
    i = half - leg / 2 - 0.02
    for k, (sx, sz) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        a = f + R @ v3(sx * i, 0, sz * i)
        b = f + R @ v3(sx * (i - 0.03), top - th, sz * (i - 0.03))
        beam(bone, "%s_leg_%d" % (name, k), a, b, leg, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"}, width=leg, up=X)
    for k, sx in enumerate((1, -1)):
        a, b = f + R @ v3(sx * (i - 0.01), 0.16, -i), f + R @ v3(sx * (i - 0.01), 0.16, i)
        beam(bone, "%s_rail_%d" % (name, k), a, b, 0.05, "wood_dark", width=0.05, up=UP)


def stool(decor, x, y, z, yaw_deg, bone_parent=None):
    """A stool where a player can sit: furnish:spruce_stool (vanilla stand-in: none; stand-in bone: stool_model),
    its low collision box, and a seat (contract B) at the centre of its top, the sitter facing yaw_deg."""
    i = decor.block(STOOL, x, y, z, facing=(yaw_deg + 180.0) % 360.0, fallback="plank", builder=lambda b, n: stool_model(
        b, n, (x, y, z), yaw=math.radians(yaw_deg)))
    SEATS.append({"pos": [round(x, 4), round(y + STOOL_TOP, 4), round(z, 4)], "yaw": float(yaw_deg) % 360.0})
    return i


def table(bone, det, name, center, w, d, h=0.84, yaw=0.0, solid=True):
    """A chunky square-legged tavern table: a thick top of planks along its length with a darker rim, four thick legs,
    aprons under the top, a low stretcher. center = the floor point under its middle."""
    c = v3(*center)
    R = ry(yaw)
    top_th = 0.12
    add_cube(bone, name + "_top", c + UP * (h - top_th / 2), R, (w, top_th, d), {"all": "plank", "+2": "plank"}, u_dir=R[:, 0])
    leg = 0.15
    for k, (sx, sz) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        p = c + R @ v3(sx * (w / 2 - leg / 2 - 0.05), 0, sz * (d / 2 - leg / 2 - 0.05))
        add_cube(bone, "%s_leg_%d" % (name, k), p + UP * (h - top_th) / 2, R, (leg, h - top_th, leg),
                 {"all": "wood", "+2": "end_grain", "-2": "end_grain"})
    for k, sz in enumerate((1, -1)):
        add_cube(det, "%s_apron_%d" % (name, k), c + R @ v3(0, h - top_th - 0.06, sz * (d / 2 - 0.1)), R, (w - 0.2, 0.1, 0.05), "wood_dark")
    add_cube(det, name + "_stretcher", c + R @ v3(0, 0.16, 0), R, (w - 0.3, 0.07, 0.07), "wood_dark")
    if solid:
        ex = abs(math.cos(yaw)) * w / 2 + abs(math.sin(yaw)) * d / 2
        ez = abs(math.sin(yaw)) * w / 2 + abs(math.cos(yaw)) * d / 2
        collide((c[0] - ex, 0.0, c[2] - ez, c[0] + ex, h, c[2] + ez))
    return c[1] + h


def mug(bone, name, foot, yaw=0.0, r=0.065, h=0.16, foam=True):
    """A wooden tankard of beer: staved body with iron bands, a head of foam spilling over, a handle."""
    f = v3(*foot)
    R = ry(yaw)
    add_cube(bone, name, f + UP * h / 2, R, (2 * r, h, 2 * r), {"all": "tv_mug", "+2": "tv_foam", "-2": "tv_mug"}, stretch=True)
    if foam:
        add_cube(bone, name + "_foam", f + UP * (h + 0.015), R @ ry(0.4), (2 * r * 1.05, 0.04, 2 * r * 1.05), "tv_foam", stretch=True)
    add_cube(bone, name + "_handle", f + UP * (h * 0.55) + R @ v3(r + 0.025, 0, 0), R, (0.035, h * 0.6, 0.03), "wood_dark")


def standing_lantern(bone, name, foot, size=0.24):
    """A lantern standing on a table (rebuilt lit on export)."""
    f = v3(*foot)
    tl.lantern(bone, name, f + UP * (size * 0.65 + 0.005), size=size)


def keg(bone, det, name, center, r=0.2, L=0.42, axis="z", tap=True):
    """A small keg lying on its side (axis z: its end with the tap towards +z), on two little chocks."""
    c = v3(*center)
    ax = {"z": Z, "x": X}[axis]
    cl.barrel(bone, name, c - ax * L / 2, r=r, h=L, staves=8, axis=axis, solid=False)
    if tap:
        add_cube(det, name + "_tap", c + ax * (L / 2 + 0.05) - UP * r * 0.35, EYE, (0.05, 0.05, 0.1) if axis == "z" else (0.1, 0.05, 0.05), "brass")
        add_cube(det, name + "_spout", c + ax * (L / 2 + 0.09) - UP * r * 0.45, EYE, (0.035, 0.08, 0.035), "brass")
    for s in (-1, 1):
        side = X if axis == "z" else Z
        add_cube(det, "%s_chock_%d" % (name, (s + 1) // 2), c - UP * (r - 0.03) + side * s * r * 0.55, EYE,
                 (0.08, 0.08, L * 0.7) if axis == "z" else (L * 0.7, 0.08, 0.08), "wood_dark")


def mug_banner(bone, name, top_center, w=0.72, h=1.3, normal=(0, 0, 1), rod=True):
    """A wine-red banner with the gold beer mug and a gold dagged hem, hanging from a rod with gold knobs."""
    ml.banner(bone, name, top_center, w, h, normal=normal, region="tv_banner", rod=rod, wave=0.035)


def hanging_sign(bone, det, name, hook0, hook1, size=0.75, drop=0.32, normal=(0, 0, 1)):
    """The square tavern sign hanging under an arm by two chains from hook0 / hook1 (points under the arm)."""
    h0, h1 = v3(*hook0), v3(*hook1)
    n = norm(v3(*normal))
    mid = (h0 + h1) / 2
    c = mid - UP * (drop + size / 2)
    add_cube(bone, name, c, np.column_stack([np.cross(UP, n), UP, n]), (size, size, 0.07),
             {"all": "wood_dark", "+3": "tv_sign", "-3": "tv_sign"}, stretch=True, u_dir=np.cross(UP, n), v_dir=-UP)
    side = norm(h1 - h0)
    for k, hk in enumerate((h0, h1)):
        bottom = c + UP * size / 2 + side * ((-1) ** (k + 1)) * size * 0.36
        wl.chain(det, "%s_chain_%d" % (name, k), hk, bottom, link=0.08)
        add_cube(det, "%s_eye_%d" % (name, k), bottom + UP * 0.02, EYE, (0.05, 0.06, 0.09), "iron_dark")


def chimney(bone, det, name, foot, top_y, s=0.56):
    """A square stone chimney from foot (its base, inside the roof) up to top_y: brick shaft, a wider band and a
    capstone at the top."""
    f = v3(*foot)
    H = top_y - f[1]
    add_cube(bone, name, f + UP * H / 2, EYE, (s, H, s), {"all": "tv_bricks", "+2": "tv_stone_top", "-2": "tv_stone_top"})
    add_cube(bone, name + "_band", v3(f[0], top_y - 0.32, f[2]), EYE, (s + 0.1, 0.12, s + 0.1), {"all": "tv_bricks", "+2": "tv_stone_top"})
    add_cube(bone, name + "_cap", v3(f[0], top_y - 0.04, f[2]), EYE, (s + 0.14, 0.1, s + 0.14), "tv_stone_top")
    add_cube(bone, name + "_flue", v3(f[0], top_y + 0.02, f[2]), EYE, (s - 0.2, 0.04, s - 0.2), "coal")
    add_cube(det, name + "_pot", v3(f[0], top_y + 0.1, f[2]), EYE, (0.24, 0.16, 0.24), {"all": "tv_bricks", "+2": "coal"})


def stone_ring(bone, name, center, r=0.72, n=10, size=(0.36, 0.26, 0.3), solid=True):
    """A ring of rough stones round a fire pit (center = ground point)."""
    c = v3(*center)
    for k in range(n):
        a = 2 * math.pi * k / n + 0.15
        p = c + v3(math.cos(a), 0, math.sin(a)) * r
        hgt = size[1] * (0.85 + 0.3 * ((k * 7) % 3) / 2)
        add_cube(bone, "%s_%d" % (name, k), p + UP * hgt / 2, ry(-a), (size[0], hgt, size[2] * (1.0 + 0.2 * (k % 2))),
                 {"all": "tv_cobble", "+2": "tv_stone_top"}, stretch=True)
    if solid:
        e = r + size[0] / 2
        collide((c[0] - e, 0.0, c[2] - e, c[0] + e, size[1], c[2] + e))


def campfire(bone, det, name, center, r=0.72):
    """The camp fire: the stone ring, crossed logs, embers, lit flames (wslib_b.fire)."""
    stone_ring(bone, name + "_ring", center, r=r)
    wl.fire(bone, name + "_fire", center, s=0.62, logs=3, flames=True)


def tripod_cauldron(bone, det, name, center, span=1.6, h=1.85, axis="x", cauldron_y=0.42, r=0.32):
    """Two A-frame trestles (along `axis`, `span` apart) with a crossbar at height h; a black cauldron hangs on a chain
    from the middle of the bar over the fire (wslib_b.cauldron). The trestle legs collide."""
    c = v3(*center)
    ax = X if axis == "x" else Z
    side = Z if axis == "x" else X
    for k, s in enumerate((-1, 1)):
        top = c + ax * s * span / 2 + UP * h
        for j, t in enumerate((-1, 1)):
            foot = c + ax * s * (span / 2 + 0.05) + side * t * 0.42
            beam(bone, "%s_leg_%d_%d" % (name, k, j), foot, top + side * t * 0.04, 0.13, {"all": "wood", "+1": "end_grain", "-1": "end_grain"},
                 up=ax, extend=0.06)
            collide_segment(foot, top, 0.14, segs=2)
        beam(det, "%s_brace_%d" % (name, k), c + ax * s * span / 2 + UP * 0.75 - side * 0.3, c + ax * s * span / 2 + UP * 0.75 + side * 0.3,
             0.07, "wood_dark", up=ax, extend=0.04)
    a, b = c - ax * (span / 2 + 0.16) + UP * (h + 0.04), c + ax * (span / 2 + 0.16) + UP * (h + 0.04)
    beam(bone, name + "_bar", a, b, 0.13, {"all": "wood", "+1": "end_grain", "-1": "end_grain"}, up=UP)
    for k, s in enumerate((-1, 1)):
        add_cube(det, "%s_lash_%d" % (name, k), c + ax * s * span / 2 + UP * (h + 0.02), EYE, (0.16, 0.17, 0.16), "rope")
    hook = c + UP * (h - 0.05)
    foot = c + UP * cauldron_y
    wl.cauldron(bone, name + "_pot", foot, r=r, h=0.42, content="stew", legs=False, bail_to=foot + UP * 0.72, glow_content=False, detail=det)
    wl.chain(det, name + "_chain", hook, foot + UP * 0.72, link=0.09)


def pavers(bone, name, center, w, d, yaw=0.0, y=0.0):
    """A patch of stone pavers lying on the ground (cut-out plate, no collision: players walk on the real ground)."""
    c = v3(*center)
    R = ry(yaw)
    return add_cube(bone, name, c + UP * (y + 0.012), R, (w, 0.02, d), {"all": None, "+2": "tv_pavers"}, stretch=True,
                    u_dir=R[:, 0], v_dir=R[:, 2])


def rug(bone, name, x0, x1, z0, z1, y=0.03):
    """The red patterned rug (lying on the ground or the pavers; no collision)."""
    return add_cube(bone, name, ((x0 + x1) / 2, y + 0.012, (z0 + z1) / 2), EYE, (x1 - x0, 0.022, z1 - z0),
                    {"all": "cloth", "+2": "tv_rug", "-2": None}, stretch=True, u_dir=X, v_dir=Z)


def bottle(bone, name, foot, colour="green", h=0.24):
    """A wine bottle (green / brown glass): square body, narrow neck, cork."""
    reg = {"green": "potion_green", "brown": "potion_orange", "red": "potion_red"}.get(colour, colour)
    f = v3(*foot)
    r = 0.055
    add_cube(bone, name, f + UP * (h * 0.32), ry(0.3), (2 * r, h * 0.64, 2 * r), reg, stretch=True)
    add_cube(bone, name + "_shoulder", f + UP * (h * 0.68), ry(0.3), (r * 1.3, h * 0.1, r * 1.3), reg, stretch=True)
    add_cube(bone, name + "_neck", f + UP * (h * 0.85), ry(0.3), (r * 0.65, h * 0.24, r * 0.65), reg, stretch=True)
    add_cube(bone, name + "_cork", f + UP * (h + 0.012), ry(0.3), (r * 0.7, 0.03, r * 0.7), "cork")


# ---------------------------------------------------------------- decor (mod blocks with modelled stand-ins)
class Decor(ml.Decor):
    """merchantlib.Decor + a `builder(bone, name)` per block that models its stand-in (bone fallback_<i>) instead of
    a plain box: the stools' stand-ins are real stools at the same height as the mod's, so the seats stay true."""

    def __init__(self):
        super().__init__()
        self.builders = {}

    def block(self, bid, x, y, z, facing="front", scale=1.0, glow=False, alt=None, fallback="crate", solid=True, bounds=None,
              builder=None):
        i = super().block(bid, x, y, z, facing=facing, scale=scale, glow=glow, alt=alt, fallback=fallback, solid=solid, bounds=bounds)
        if builder is not None:
            self.builders[i] = builder
        return i

    def fallbacks(self, root):
        if self._fb_done:
            return
        self._fb_done = True
        plain = []
        for i, b in enumerate(self.blocks):
            if i in self.builders:
                self.builders[i](Bone("fallback_%d" % i, parent=root), "fb_%d" % i)
            else:
                plain.append(i)
        if plain:
            keep = self.blocks
            for i in plain:     # the plain stand-in boxes of tentlib, one bone each (same names)
                b = keep[i]
                x0, y0, z0, x1, y1, z1 = self.footprint(b)
                bone = Bone("fallback_%d" % i, parent=root)
                pre = "glow" if b["glow"] else "fb"
                add_cube(bone, "%s_fallback_%d" % (pre, i), v3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), EYE,
                         (max(0.04, x1 - x0), max(0.04, y1 - y0), max(0.04, z1 - z0)), b["fallback_region"], stretch=True)


# ---------------------------------------------------------------- export
def export(root, name, atlas, decor=None, icon=None, particles=None, visible_box=(14, 7, 0)):
    """Writes carts/<id>.json (model, texture, decor, extent, colliders, particles, seats), models/entity/<id>.bbmodel,
    blockbench/<id>.bbmodel, textures/entity/<id>.png, textures/item/<id>.png (icon: a function(path)),
    interiors/<id>_decor.json. TAVERN_OUT=<file.bbmodel>: writes only the model (and its atlas next to it) there, for
    previews."""
    out_model = os.environ.get("TAVERN_OUT")
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
    data = {
        "model": "models/entity/%s.bbmodel" % name,
        "texture": "textures/entity/%s" % tex_name,
        "decor": "/assets/medievalships/" + decor_path if decor_path else None,
        "extent": [round(float(v), 3) for v in ext],
        "colliders": [[round(float(v), 3) for v in (b[0], max(0.0, b[1]), b[2], b[3], b[4], b[5])] for b in COLLIDERS],
    }
    if particles:
        data["particles"] = particles
    data["seats"] = list(SEATS)
    if not out_model:
        path = os.path.join(ASSETS, "%s/%s.json" % (GROUP, name))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=1)
        if callable(icon):
            icon(os.path.join(ASSETS, "textures/item/%s.png" % name))
    else:
        with open(os.path.splitext(out_model)[0] + ".json", "w") as f:
            json.dump(data, f, indent=1)
    print("%s: %d cubes, extent %s, %d collision boxes, %d mod blocks, %d seats" % (
        name, len(model["elements"]), ["%.2f" % v for v in ext], len(COLLIDERS), 0 if decor is None else len(decor.blocks), len(SEATS)))
    return model


def particle(kind, pos, chance=0.3, count=1):
    """A particle source for export(particles=[...]) (TentType.Particle; vanilla types, see TentType.PARTICLE_TYPES)."""
    return ml.particle(kind, pos, chance=chance, count=count)


# ---------------------------------------------------------------- wagon parts
def wheel_z(bone, name, center, radius, width=0.22, spokes=10, segs=16, felloe=0.16, hub_d=0.32, hub_len=0.46, spoke_d=0.085,
            region="wood_dark", spoke_region="wood", tyre="iron", detail=None, solid=True):
    """cartlib.wheel turned a quarter: a round spoked wheel in the x-y plane turning about z (the axle across a wagon
    whose length runs along x), touching the ground when center y == radius: a polygon rim of tilted felloe segments
    (outer face an iron tyre), an octagonal hub with iron caps, `spokes` spokes. Collides as one box."""
    c = v3(*center)
    r_mid = radius - felloe / 2
    pts = [c + v3(r_mid * math.cos(2 * math.pi * k / segs), r_mid * math.sin(2 * math.pi * k / segs), 0) for k in range(segs)]
    for k in range(segs):
        p0, p1 = pts[k], pts[(k + 1) % segs]
        mid = (p0 + p1) / 2
        d = norm(p1 - p0)
        n = np.cross(d, Z)
        out = "+3" if np.dot(n, mid - c) > 0 else "-3"
        faces = {"all": region}
        if tyre:
            faces[out] = tyre
        beam(bone, "%s_rim_%d" % (name, k), p0, p1, width, faces, width=felloe, up=Z, extend=felloe * math.tan(math.pi / segs) + 0.01)
    sb = detail if detail is not None else bone
    for k in range(spokes):
        a = 2 * math.pi * (k + 0.5) / spokes
        dr = v3(math.cos(a), math.sin(a), 0)
        beam(sb, "%s_spoke_%d" % (name, k), c + dr * (hub_d * 0.4), c + dr * (radius - felloe * 0.8), spoke_d, spoke_region,
             width=spoke_d * 0.8, up=Z)
    for k, ang in enumerate((0.0, math.pi / 4)):
        add_cube(bone, "%s_hub_%d" % (name, k), c, rz(ang), (hub_d, hub_d, hub_len), {"all": region, "+3": "end_grain", "-3": "end_grain"})
    for s in (1, -1):
        add_cube(bone, "%s_cap_%d" % (name, (s + 1) // 2), c + Z * s * (hub_len / 2 + 0.02), rz(math.pi / 8),
                 (hub_d * 0.75, hub_d * 0.75, 0.05), tyre or "iron")
        add_cube(sb, "%s_pin_%d" % (name, (s + 1) // 2), c + Z * s * (hub_len / 2 + 0.06), EYE, (0.07, 0.07, 0.04), "iron_dark")
    if solid:
        h = radius * 0.8
        collide((c[0] - h, max(0.0, c[1] - radius), c[2] - width / 2 - 0.02, c[0] + h, c[1] + radius * 0.92, c[2] + width / 2 + 0.02))


def bolt(bone, name, p, normal, s=0.09):
    """A small square iron plate with a bolt head on a timber face (normal = the face's outward axis)."""
    n = norm(v3(*normal))
    size = tuple(0.025 if abs(n[i]) > 0.5 else s for i in range(3))
    add_cube(bone, name, v3(*p) + n * 0.012, EYE, size, "iron")


def icon_tavern(path):
    """16x16 item icon: the wagon from the side, a rounded wine-red / beige canvas roof, two big wheels, the mug
    banner, the chimney, the lit counter, a little table."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()

    def put(x, y, c):
        if 0 <= x < 16 and 0 <= y < 16:
            p[x, y] = tuple(int(k) for k in c) + (255,)

    wine, beige, wood, dark = (124, 30, 34), (226, 212, 176), (128, 88, 50), (66, 42, 22)
    for x in range(1, 14):        # the rounded roof
        d = abs(x - 7.0) / 6.5
        top = int(round(2 + 3.0 * d * d))
        for y in range(top, 7):
            c = beige if x < 4 or x > 11 else wine
            if y == top:
                c = tuple(int(k * 0.75) for k in c)
            put(x, y, c)
    for y in range(0, 3):         # chimney
        put(10, y, (90, 88, 86))
        put(11, y, (70, 68, 66))
    put(10, 0, (200, 200, 200))
    for x in range(1, 14):        # body
        for y in range(7, 11):
            put(x, y, wood if (x + y) % 4 else dark)
    for x in range(5, 10):        # the counter opening, lit
        put(x, 8, (240, 180, 80))
    for y in range(7, 11):        # banner
        put(3, y, wine)
    put(3, 8, (240, 200, 90))
    for y in range(11, 16):       # wheels
        for x in range(0, 16):
            for cx in (3.5, 11.0):
                dd = math.hypot(x - cx, y - 12.5)
                if 1.6 <= dd <= 2.6:
                    put(x, y, dark)
                elif dd < 1.0:
                    put(x, y, (70, 70, 76))
    for x in range(13, 16):       # a little table
        put(x, 12, wood)
    put(13, 13, dark)
    put(15, 13, dark)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
