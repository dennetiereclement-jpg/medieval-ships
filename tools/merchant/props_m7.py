"""Props of the poison merchant's and the butcher's stalls (1.16.0, agent T): tente_poison, tente_boucher.

Both are the gabled market stall of merchantlib.stall (posts with gold caps, the striped gabled roof, the dagged
valance, the banner on a rod, lanterns, the long counter, the back shelves, the hanging rail); this module adds what
makes each one: its own atlas regions (painted into the free band of the tent's atlas with atlas.add, named "m7_..."
plus the few shared ones of props_m1 / props_m2 it needs) and the geometry of the goods.

    import props_m7 as p7
    p7.add_regions(atlas, p7.POISON_REGIONS)     # or p7.BUTCHER_REGIONS, before export
    p7.cauldron_on_crate(props, det, foot, rng)  # the black cauldron of glowing green poison on its crate
    p7.ham(...), p7.sausage_string(...), p7.carcass(...), p7.steak(...), p7.chopping_block(...), p7.cleaver(...)

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
import props_m2 as p2  # noqa: E402

wb = p1.wb
v3, norm, add_cube, beam = ml.v3, ml.norm, ml.add_cube, ml.beam
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ry, rx, rz = ml.ry, ml.rx, ml.rz
_rgb, _mix, _jitter, _scale = ml._rgb, ml._mix, ml._jitter, ml._scale
GOLD, GOLD_D = (226, 176, 58), (128, 86, 20)
CLEAR = (0, 0, 0, 0)


# ================================================================ painters (img = the region, w x h RGBA)
def _noise(base, seed, n=6):
    def p(img):
        rng = random.Random(seed)
        px = img.load()
        for y in range(img.height):
            for x in range(img.width):
                px[x, y] = _jitter(base, rng, n) + (255,)
    return p


def _runner(main, dark, edge, ornament, seed, cut=True):
    """A counter runner / cloth hanging down the front: woven `main`, a band of `edge` along the two sides, the bottom
    cut in stepped dags edged with `edge` (cut-out), an `ornament` (a gold fleur) in the middle."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        solid = int(h * 0.74)
        for y in range(h):
            for x in range(w):
                c = _scale(main, 1.0 + 0.05 * ((x + y) % 2) - 0.04 * ((x // 3 + y // 2) % 2))
                if x < 2 or x >= w - 2:
                    c = edge
                elif x < 3 or x >= w - 3:
                    c = dark
                px[x, y] = _jitter(c, rng, 5) + (255,)
        if cut:
            for x in range(w):
                lx = x / w
                tri = 1.0 - abs(2.0 * ((lx * 3.0) % 1.0) - 1.0)          # three dags
                bottom = int(solid + (h - 2 - solid) * math.floor(tri * 3.999) / 3.0)
                for y in range(h):
                    if y > bottom:
                        px[x, y] = CLEAR
                    elif y >= bottom - 1:
                        px[x, y] = _jitter(edge, rng, 8) + (255,)
                for xn in (x - 1, x + 1):
                    if 0 <= xn < w:
                        lx2 = xn / w
                        tri2 = 1.0 - abs(2.0 * ((lx2 * 3.0) % 1.0) - 1.0)
                        b2 = int(solid + (h - 2 - solid) * math.floor(tri2 * 3.999) / 3.0)
                        if b2 < bottom:
                            for y in range(b2 - 1, bottom + 1):
                                px[x, y] = _jitter(edge, rng, 8) + (255,)
        if ornament:
            cx, cy = w / 2, h * 0.5
            pts = [(0, -5), (0, -4), (0, -3), (0, -2), (0, -1), (0, 0), (0, 1), (0, 2), (-1, -3), (1, -3), (-2, -2), (2, -2),
                   (-3, -1), (3, -1), (-3, 0), (3, 0), (-2, 1), (2, 1), (-1, 3), (1, 3), (0, 4), (-2, 4), (2, 4)]
            for dx, dy in pts:
                X_, Y_ = int(cx + dx), int(cy + dy)
                if 0 <= X_ < w and 0 <= Y_ < h:
                    px[X_, Y_] = _jitter(ornament, rng, 8) + (255,)
    return p


def _runner_top(main, edge, seed):
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _scale(main, 1.0 + 0.05 * ((x + y) % 2))
                if x < 2 or x >= w - 2:
                    c = edge
                px[x, y] = _jitter(c, rng, 5) + (255,)
    return p


def _brew(base, light, seed):
    """A glowing bubbling brew seen from above: mottled, bright bubble rings."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                px[x, y] = _jitter(_scale(base, rng.choice((0.82, 0.95, 1.08))), rng, 8) + (255,)
        for _ in range(9):
            cx, cy, r = rng.uniform(1, w - 2), rng.uniform(1, h - 2), rng.uniform(0.8, 2.4)
            for y in range(h):
                for x in range(w):
                    d = math.hypot(x - cx, y - cy)
                    if abs(d - r) < 0.6:
                        px[x, y] = light + (255,)
                    elif d < r - 0.6:
                        px[x, y] = _mix(base, light, 0.35) + (255,)
    return p


def _fumes(seed):
    """Cut-out bubbling foam and green vapour rising (for crossed planes above the cauldron, drawn full bright)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                px[x, y] = CLEAR
        cols = [_rgb("8af03a"), _rgb("a6ff4a"), _rgb("62d22a"), _rgb("c8ff70")]
        # the foam heap at the bottom, the bubbles and wisps rising above it
        for x in range(w):
            top = h - 1 - int((h * 0.38) * math.sin(math.pi * (x + 0.5) / w) ** 0.7 * rng.uniform(0.75, 1.05))
            for y in range(top, h):
                px[x, y] = _jitter(rng.choice(cols), rng, 10) + (255,)
        for _ in range(int(w * 0.9)):
            cx = rng.gauss(w / 2, w * 0.2)
            cy = rng.uniform(h * 0.05, h * 0.7)
            r = rng.uniform(0.6, 1.8) * (0.6 + 0.6 * cy / h)
            for y in range(int(cy - r - 1), int(cy + r + 2)):
                for x in range(int(cx - r - 1), int(cx + r + 2)):
                    if 0 <= x < w and 0 <= y < h and math.hypot(x - cx, y - cy) <= r:
                        px[x, y] = _jitter(rng.choice(cols), rng, 12) + (255,)
    return p


def _steak_top(seed):
    """A raw steak seen from above: red meat with white marbling, a rim of fat."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                e = min(x, y, w - 1 - x, h - 1 - y)
                c = _mix(_rgb("e2626a"), _rgb("c03a46"), rng.random() * 0.6)
                if e < 1:
                    c = _rgb("f0cfc0") if y < h / 2 else _rgb("e8a8a0")
                px[x, y] = _jitter(c, rng, 6) + (255,)
        for _ in range(5):   # marbling streaks
            x, y = rng.uniform(3, w - 4), rng.uniform(3, h - 4)
            a = rng.uniform(0, math.pi)
            for i in range(rng.randint(2, 5)):
                X_, Y_ = int(x + math.cos(a) * i), int(y + math.sin(a) * i)
                if 2 < X_ < w - 3 and 2 < Y_ < h - 3:
                    px[X_, Y_] = _jitter(_rgb("eebcb4"), rng, 8) + (255,)
    return p


def _meat_side(seed):
    """The side of a cut of meat: red with a white fat layer at the top."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _rgb("f0d2c4") if y < 1 else _mix(_rgb("d8545c"), _rgb("a8323a"), y / h)
                px[x, y] = _jitter(c, rng, 6) + (255,)
    return p


def _steak_heap(seed):
    """A heap of raw cuts seen from above (barrel and crate tops)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                px[x, y] = _jitter(_rgb("6a2a20"), rng, 8) + (255,)
        for _ in range(9):
            cx, cy = rng.uniform(2, w - 3), rng.uniform(2, h - 3)
            rw, rh = rng.uniform(4, 7), rng.uniform(3, 5)
            for y in range(int(cy - rh), int(cy + rh) + 1):
                for x in range(int(cx - rw), int(cx + rw) + 1):
                    if 0 <= x < w and 0 <= y < h:
                        e = min(abs(x - cx) - rw, abs(y - cy) - rh)
                        c = _rgb("f0dcc8") if e > -1.2 else _mix(_rgb("d03a3e"), _rgb("a82230"), rng.random())
                        px[x, y] = _jitter(c, rng, 6) + (255,)
    return p


def _ribs(seed):
    """A side of pork / half carcass seen from the inside (cut-out): red meat, a creamy fat rim, white rib bones curving
    out from the spine on the left, the shank narrowing at the top under the hook."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            t = y / (h - 1)
            half = (w / 2) * (0.34 + 0.66 * min(1.0, t / 0.28)) * (1.0 - 0.3 * max(0.0, (t - 0.8) / 0.2))
            for x in range(w):
                dx = abs(x + 0.5 - w / 2)
                if dx > half:
                    px[x, y] = CLEAR
                    continue
                e = half - dx
                if e < 1.0 or y >= h - 1:
                    c = _rgb("f4e6d0")
                elif e < 2.2 or (x > w / 2 and e < 3.5):
                    c = _jitter(_rgb("f0d0c0"), rng, 6)
                else:
                    c = _mix(_rgb("c8404a"), _rgb("9e2632"), rng.random() * 0.8)
                px[x, y] = _jitter(c, rng, 6) + (255,)
        spine = int(w * 0.3)
        for y in range(int(h * 0.2), h - 2):      # the spine, a pale column of vertebrae
            for x in (spine - 1, spine):
                if px[x, y][3]:
                    px[x, y] = _jitter(_rgb("eadccc") if y % 3 else _rgb("c8a898"), rng, 5) + (255,)
        for k in range(6):                          # the ribs curving down and out from the spine
            y0 = h * (0.28 + 0.1 * k)
            for x in range(spine + 1, w - 2):
                f = (x - spine) / (w - spine)
                yy = int(y0 + 5.0 * f * f)
                if 0 <= yy < h and px[x, yy][3] and px[x, yy][:3] != _rgb("f4e6d0"):
                    px[x, yy] = _jitter(_rgb("eedcd2"), rng, 5) + (255,)
                    if yy + 1 < h and px[x, yy + 1][3]:
                        px[x, yy + 1] = _jitter(_rgb("d88a84"), rng, 5) + (255,)
    return p


def _bark(seed):
    """Log bark round the chopping block: dark brown vertical ridges, a pale cut band at the top."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        ridge = [rng.uniform(0.75, 1.15) for _ in range(w)]
        for y in range(h):
            for x in range(w):
                k = ridge[x] * (0.85 if (x + (y // 6)) % 4 == 0 else 1.0)
                c = _scale(_rgb("6a4424"), k)
                if y < 2:
                    c = _rgb("a07a4a")
                px[x, y] = _jitter(c, rng, 7) + (255,)
        for _ in range(4):   # dried blood runs
            x = rng.randrange(w)
            for y in range(2, rng.randint(5, h // 2)):
                px[x, y] = _jitter(_rgb("6a1a18"), rng, 6) + (255,)
    return p


def _log_top(seed):
    """The chopping block's top: growth rings, knife cuts, a dark blood stain."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        cx, cy = w / 2 - 0.5, h / 2 - 0.5
        for y in range(h):
            for x in range(w):
                d = math.hypot(x - cx, y - cy)
                ring = 0.92 + 0.12 * math.sin(d * 1.6)
                c = _scale(_rgb("b88a54"), ring)
                if d > w / 2 - 2:
                    c = _rgb("5a3a1e")
                px[x, y] = _jitter(c, rng, 5) + (255,)
        for _ in range(8):
            a = rng.uniform(0, math.pi)
            x0, y0 = rng.uniform(5, w - 6), rng.uniform(5, h - 6)
            for i in range(-4, 5):
                X_, Y_ = int(x0 + math.cos(a) * i), int(y0 + math.sin(a) * i)
                if 0 <= X_ < w and 0 <= Y_ < h:
                    px[X_, Y_] = _scale(px[X_, Y_][:3], 0.7) + (255,)
        bx, by = w * 0.6, h * 0.42
        for y in range(h):
            for x in range(w):
                if math.hypot((x - bx) / 1.3, y - by) < 4.5 + rng.uniform(-0.8, 0.8):
                    px[x, y] = _jitter(_rgb("7a1c1a"), rng, 8) + (255,)
    return p


def _blade(seed):
    """A cleaver blade: bright steel, darker spine along the top, a polished edge at the bottom, the hanging hole."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                t = y / (h - 1)
                c = _mix(_rgb("8a8e96"), _rgb("e4e8ee"), 0.35 + 0.6 * t)
                if y < 2:
                    c = _rgb("50545c")
                if y >= h - 2:
                    c = _rgb("f8faff")
                px[x, y] = _jitter(c, rng, 4) + (255,)
        for y in range(2, 5):
            for x in range(2, 5):
                px[x, y] = (40, 40, 44, 255)
    return p


def _skull_face(seed):
    """A small skull seen from the front (for the shelves): bone white, dark eye holes and nose, teeth."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                px[x, y] = _jitter(_rgb("e2d6b8"), rng, 6) + (255,)
        for (x, y) in ((3, 6), (4, 6), (3, 7), (4, 7), (11, 6), (12, 6), (11, 7), (12, 7), (3, 8), (4, 8), (11, 8), (12, 8),
                       (5, 7), (10, 7), (7, 10), (8, 10), (7, 11), (8, 11)):
            if x < w and y < h:
                px[x, y] = (40, 30, 26, 255)
        for x in range(4, 12):
            px[x, 13] = (120, 100, 80, 255)
            if x % 2 == 0:
                px[x, 14] = (120, 100, 80, 255)
    return p


def _sausage(seed):
    """A plump sausage link (u along it): glossy red-brown, a light streak along the middle, darker pinched ends."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                t = abs((y + 0.5) / h - 0.4)
                c = _mix(_rgb("d8683a"), _rgb("8a2e1a"), min(1.0, t * 2.2))
                if x < 1 or x >= w - 1:
                    c = _scale(c, 0.7)
                if y == int(h * 0.3) and x % 3 != 0:
                    c = _mix(c, (255, 220, 180), 0.45)
                px[x, y] = _jitter(c, rng, 6) + (255,)
    return p


def _ham_skin(seed):
    """A cured ham's skin (u round it, v down): glossy pink-orange, darker red-brown towards the sides, white fat
    marbling, a little highlight."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                d = abs(x + 0.5 - w / 2) / (w / 2)
                c = _mix(_rgb("f09a7a"), _rgb("b2482e"), d ** 1.2)
                c = _mix(c, _rgb("d0603a"), 0.25 * (y / h))
                if rng.random() < 0.06:
                    c = _mix(c, _rgb("f8e2d0"), 0.7)
                if x == w // 3 and 2 < y < h - 3:
                    c = _mix(c, (255, 236, 220), 0.4)
                px[x, y] = _jitter(c, rng, 5) + (255,)
    return p


def _bunch(stems, heads, seed, n=26, head_every=0.5):
    return p1._bunch_painter([_rgb(c) for c in stems], heads=[_rgb(c) for c in heads], seed=seed, n=n, head_every=head_every)


def _mushroom_cap(base, dots, seed):
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _scale(base, 1.1 - 0.3 * y / h)
                if (x * 3 + y * 5) % 7 == 0:
                    c = dots
                px[x, y] = _jitter(c, rng, 6) + (255,)
    return p


def _glow_drip(seed):
    """Glowing green poison (a drip down the cauldron's side, small vials)."""
    return _noise(_rgb("7ae03a"), seed, 14)


PAINTERS = {
    "m7_runner": (32, 48, _runner(_rgb("5a2a86"), _rgb("341650"), _rgb("d9a93a"), _rgb("e8b848"), 701)),
    "m7_runner_top": (32, 32, _runner_top(_rgb("5a2a86"), _rgb("d9a93a"), 702)),
    "m7_cloth_cream": (32, 48, _runner(_rgb("e8dcbc"), _rgb("c8b898"), _rgb("a42a24"), None, 703)),
    "m7_cloth_cream_top": (32, 32, _runner_top(_rgb("e8dcbc"), _rgb("a42a24"), 704)),
    "m7_brew_green": (16, 16, _brew(_rgb("5ad02a"), (210, 255, 150), 705)),
    "m7_fumes": (32, 32, _fumes(706)),
    "m7_glow_green": (8, 8, _glow_drip(707)),
    "m7_steak": (16, 16, _steak_top(708)),
    "m7_meat_side": (16, 8, _meat_side(709)),
    "m7_steak_heap": (32, 32, _steak_heap(710)),
    "m7_ribs": (32, 48, _ribs(711)),
    "m7_sausage": (16, 8, _sausage(724)),
    "m7_ham": (16, 16, _ham_skin(725)),
    "m7_bark": (32, 32, _bark(712)),
    "m7_log_top": (32, 32, _log_top(713)),
    "m7_blade": (16, 16, _blade(714)),
    "m7_skull": (16, 16, _skull_face(715)),
    "m7_bone": (8, 8, _noise(_rgb("e2d6b8"), 716, 6)),
    "m7_toxic": (16, 32, _bunch(["5a8a24", "6a9a2a", "4a7a1e"], ["c8e040", "b0d830", "e0f060"], 717, n=26, head_every=0.55)),
    "m7_nightshade": (16, 32, _bunch(["4a5a2a", "3a4a22"], ["7a3aa8", "9a52c8", "5a2a86", "2a1a3a"], 718, n=22, head_every=0.6)),
    "m7_mush_red": (8, 8, _mushroom_cap(_rgb("c03a2a"), _rgb("f0e8d8"), 719)),
    "m7_mush_purple": (8, 8, _mushroom_cap(_rgb("7a3aa8"), _rgb("d8c8f0"), 720)),
    "m7_mush_stem": (8, 8, _noise(_rgb("e8dcc4"), 721, 5)),
    "m7_powder": (8, 8, _noise(_rgb("6ac83a"), 722, 18)),
    "m7_salt": (8, 8, _noise(_rgb("ece8e0"), 723, 8)),
}
# regions borrowed from the alchemist (props_m1) and the food merchant (props_m2)
_M1 = ("cauldron", "iron_dark", "herbs", "herbs_dry", "lavender", "herbs_red", "jar", "jar_top", "linen", "parchment",
       "book_purple", "book_brown", "book_green", "pages", "book_top", "stone_slab")
_M2 = ("m2_ham", "m2_ham_cut", "m2_sausage", "m2_burlap", "m2_jar", "m2_jar_top")

POISON_REGIONS = ["m7_runner", "m7_runner_top", "m7_brew_green", "m7_fumes", "m7_glow_green", "m7_skull", "m7_bone", "m7_toxic",
                  "m7_nightshade", "m7_mush_red", "m7_mush_purple", "m7_mush_stem", "m7_powder", "cauldron", "iron_dark", "herbs", "book_brown", "pages",
                  "herbs_dry", "lavender", "jar", "jar_top", "linen", "parchment", "book_purple", "book_green", "book_top",
                  "stone_slab"]
BUTCHER_REGIONS = ["m7_sausage", "m7_ham", "m7_cloth_cream", "m7_cloth_cream_top", "m7_steak", "m7_meat_side", "m7_steak_heap", "m7_ribs", "m7_bark",
                   "m7_log_top", "m7_blade", "m7_bone", "m7_salt", "m2_ham", "m2_ham_cut", "m2_sausage", "m2_burlap", "jar", "jar_top",
                   "linen", "iron_dark", "herbs_dry"]


def add_regions(atlas, names):
    """Adds the named regions to the tent's atlas (merchantlib.Atlas), skipping the shell's own."""
    m2 = {n: (w, h, f) for n, w, h, f in p2.REGION_SETS["food"]}
    for n in names:
        if n in atlas.regions and n not in atlas.painters:
            continue
        if n in PAINTERS:
            w, h, f = PAINTERS[n]
        elif n in m2:
            w, h, f = m2[n]
        else:
            w, h, f = p1.PAINTERS[n]
        atlas.add(n, w, h, f)


# ================================================================ shared
def box(bone, name, lo, hi, region, yaw=0.0, stretch=True):
    lo, hi = v3(*lo), v3(*hi)
    return add_cube(bone, name, (lo + hi) / 2, ry(yaw), np.abs(hi - lo), region, stretch=stretch)


def hook(bone, name, top, drop=0.3):
    """An iron chain from the rail down to an S-hook (returns the hook's lowest point)."""
    top = v3(*top)
    wb.chain(bone, name + "_chain", top, top - UP * drop, link=0.075)
    add_cube(bone, name + "_hook", top - UP * (drop + 0.04), EYE, (0.03, 0.09, 0.03), "iron_dark")
    return top - UP * (drop + 0.08)


def runner(bone, name, x0, x1, z0, z1, y, hang=0.75, region="m7_runner", top_region="m7_runner_top"):
    """A cloth lying across the counter top (x0..x1, z0..z1 at y) and hanging down the front by `hang` (dagged)."""
    add_cube(bone, name + "_top", ((x0 + x1) / 2, y + 0.008, (z0 + z1) / 2), EYE, (x1 - x0, 0.016, z1 - z0 + 0.02),
             {"all": top_region}, stretch=True, u_dir=X, v_dir=Z)
    ml.plate(bone, name + "_front", ((x0 + x1) / 2, y + 0.016 - hang / 2, z1 + 0.018), x1 - x0, hang, region, normal=(0, 0, 1),
             th=0.012)


# ================================================================ poison
def cauldron_on_crate(bone, det, foot, rng, crate=0.82, r=0.44, h=0.52):
    """The black cauldron of glowing green poison on a banded crate: the bubbling surface and a heap of foam and rising
    bubbles drawn full bright, a green drip down its side, a ladle; collides (the crate and the cauldron)."""
    foot = v3(*foot)
    ml.crate(bone, "cauldron_crate", foot, size=crate, yaw=0.0, solid=True)
    top = foot + UP * crate
    wb.cauldron(bone, "cauldron", top, r=r, h=h, content="m7_brew_green", legs=True, glow_content=True)
    surf = top + UP * (0.1 + h - 0.08)
    wb.crossed(bone, "cauldron_fumes", surf + UP * 0.36, r * 2.2, 0.8, "m7_fumes", glow=True)
    wb.crossed(bone, "cauldron_fumes_b", surf + UP * 0.3 + v3(0.06, 0, 0.04), r * 1.9, 0.66, "m7_fumes", glow=True, yaw=0.0)
    wb.crossed(bone, "cauldron_fumes_c", surf + UP * 0.22 + v3(-0.05, 0, -0.03), r * 1.7, 0.5, "m7_fumes", glow=True, yaw=0.39)
    # the foam heaped over the brim
    for k in range(3):
        add_cube(bone, "glow_foam_%d" % k, surf + UP * (0.05 + 0.06 * k), ry(0.4 * k), (r * (1.6 - 0.4 * k), 0.08, r * (1.6 - 0.4 * k)),
                 {"all": "m7_glow_green", "+2": "m7_brew_green"}, stretch=True)
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.4
        q = surf + v3(math.cos(a), 0, math.sin(a)) * r * rng.uniform(0.25, 0.6) + UP * 0.03
        s = rng.uniform(0.06, 0.1)
        add_cube(det, "glow_bubble_%d" % k, q, ry(a), (s, s * 0.8, s), {"all": "m7_glow_green"}, stretch=True)
    # a green drip over the rim
    add_cube(bone, "glow_cauldron_drip", top + v3(0.0, 0.1 + h * 0.62, r + 0.07), EYE, (0.08, h * 0.55, 0.02), {"all": "m7_glow_green"},
             stretch=True)
    beam(det, "ladle_handle", surf + v3(-0.12, 0.0, -0.1), surf + v3(-0.3, 0.55, -0.3), 0.035, "wood_dark")
    ml.collide((foot[0] - r - 0.1, foot[1], foot[2] - r - 0.1, foot[0] + r + 0.1, top[1] + h + 0.15, foot[2] + r + 0.1))


def skull(bone, name, foot, s=0.22, yaw=0.0):
    """A small skull (bone white, the face to +z turned by yaw) with its jaw."""
    foot = v3(*foot)
    R = ry(yaw)
    add_cube(bone, name, foot + UP * (s * 0.62), R, (s, s * 0.8, s * 1.05), {"all": "m7_bone", "+3": "m7_skull"}, stretch=True)
    add_cube(bone, name + "_jaw", foot + UP * (s * 0.14) + R @ v3(0, 0, s * 0.12), R, (s * 0.7, s * 0.28, s * 0.7), "m7_bone", stretch=True)


def mushrooms(bone, name, foot, rng, n=4, cap="m7_mush_red", spread=0.12, s=1.0):
    """A cluster of n small mushrooms (stem + flat cap)."""
    foot = v3(*foot)
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.4, 0.4)
        q = foot + v3(math.cos(a), 0, math.sin(a)) * (spread * rng.uniform(0.2, 1.0) if k else 0.0)
        hh = rng.uniform(0.08, 0.16) * s
        add_cube(bone, "%s_%d_stem" % (name, k), q + UP * hh / 2, ry(a), (0.035 * s, hh, 0.035 * s), "m7_mush_stem", stretch=True)
        cw = rng.uniform(0.08, 0.13) * s
        add_cube(bone, "%s_%d_cap" % (name, k), q + UP * (hh + 0.02 * s), ry(a), (cw, 0.04 * s, cw), "%s" % cap, stretch=True)


def bowl(bone, name, foot, r=0.12, h=0.06, content="m7_powder"):
    foot = v3(*foot)
    wb.octo(bone, name, foot, r, h, {"all": "wood_dark", "+2": content}, stretch=True)


def bottle_rows(bone, levels, rng, colours, rmin=0.08, rmax=0.12, gap=0.05):
    """Rows of round flasks and small bottles on each shelf board (x0, x1, y, z_front, z_back)."""
    n = 0
    for i, (x0, x1, y, zf, zb) in enumerate(levels):
        z = (zf + zb) / 2 + 0.03
        n += p1.bottle_row(bone, "shelf_%d" % i, x0 + 0.04, x1 - 0.04, y, z, rng, colours, rmin=rmin, rmax=rmax, gap=gap,
                           shapes=("round", "round", "round", "tall", "flask"))
    return n


def herb_row(bone, name, x0, x1, y, z, kinds, rng, n=6, length=(0.55, 0.85), width=0.4):
    """n bunches hanging from the rail (y = its underside) between x0 and x1, kinds in turn."""
    for k in range(n):
        x = x0 + (x1 - x0) * (k + 0.5) / n + rng.uniform(-0.08, 0.08)
        wb.hanging_bunch(bone, "%s_%d" % (name, k), (x, y, z + rng.uniform(-0.06, 0.06)), kinds[k % len(kinds)],
                         length=rng.uniform(*length), width=width * rng.uniform(0.85, 1.1), string=rng.uniform(0.04, 0.14))


# ================================================================ butcher
HAM_PROFILE = ((0.0, 0.2), (0.14, 0.34), (0.32, 0.62), (0.52, 0.9), (0.72, 1.0), (0.88, 0.86), (1.0, 0.5))


def ham(bone, name, top, length=0.85, w=0.42, yaw=0.0):
    """A big cured ham hanging from the hook point `top`: the white shank bone and its knuckle at the top, the body a
    teardrop of octagonal slices swelling to the round bottom, the cut face (pink with the bone) underneath."""
    top = v3(*top)
    add_cube(bone, name + "_knuckle", top - UP * 0.03, ry(yaw), (0.09, 0.06, 0.09), "m7_bone", stretch=True)
    add_cube(bone, name + "_bone", top - UP * 0.1, ry(yaw), (0.06, 0.1, 0.06), "m7_bone", stretch=True)
    y0 = top - UP * 0.14
    prof = HAM_PROFILE
    for k in range(len(prof) - 1):
        (t0, f0), (t1, f1) = prof[k], prof[k + 1]
        r = w / 2 * (f0 + f1) / 2
        hh = length * (t1 - t0)
        foot = y0 - UP * (length * t1)
        reg = {"all": "m7_ham", "-2": "m2_ham_cut"} if k == len(prof) - 2 else {"all": "m7_ham"}
        wb.octo(bone, "%s_%d" % (name, k), foot, r, hh + 0.01, reg, stretch=True)


def sausage_string(bone, name, top, n=5, link=0.17, r=0.075, sway=0.02, seed=0):
    """A string of sausages hanging straight down from `top`: n links, each a little turned, tied with string."""
    rng = random.Random(seed)
    top = v3(*top)
    beam(bone, name + "_tie", top, top - UP * 0.06, 0.02, "rope")
    p = top - UP * 0.05
    for k in range(n):
        d = norm(v3(rng.uniform(-sway, sway), -1.0, rng.uniform(-sway, sway)))
        q = p + d * link
        for j, up in enumerate((X, norm(X + Z))):
            beam(bone, "%s_%d_%d" % (name, k, j), p + d * 0.012, q - d * 0.012, r, "m7_sausage", width=r, up=up, extend=-0.005)
        add_cube(bone, "%s_%d_tie" % (name, k), q, EYE, (r * 0.45, 0.03, r * 0.45), "rope")
        p = q


def carcass(bone, name, top, w=0.78, h=1.15, yaw=0.0):
    """A side of pork / half carcass hanging from the hook point `top`: the cut-out rib side (both faces) and a thicker
    meaty back behind it."""
    top = v3(*top)
    n = ry(yaw) @ Z
    c = top - UP * (h / 2)
    ml.plate(bone, name, c, w, h, "m7_ribs", normal=n, th=0.02)
    add_cube(bone, name + "_back", c - n * 0.06 - UP * 0.05, ry(yaw), (w * 0.62, h * 0.72, 0.1), {"all": "m7_meat_side", "+3": "m7_ribs"},
             stretch=True)
    add_cube(bone, name + "_shank", top - UP * 0.08, ry(yaw), (0.1, 0.16, 0.1), "m7_bone", stretch=True)


def steak(bone, name, foot, w=0.34, d=0.22, th=0.06, yaw=0.0):
    """A raw cut lying flat (marbled top, fat rim, red sides)."""
    foot = v3(*foot)
    add_cube(bone, name, foot + UP * th / 2, ry(yaw), (w, th, d), {"all": "m7_meat_side", "+2": "m7_steak", "-2": "m7_meat_side"},
             stretch=True)


def steak_pile(bone, name, foot, rng, n=4, w=0.34, d=0.22, th=0.06):
    """A small pile of steaks (two layers)."""
    foot = v3(*foot)
    for k in range(n):
        layer = 0 if k < max(1, n - 1) else 1
        off = v3(rng.uniform(-0.08, 0.08), 0, rng.uniform(-0.06, 0.06)) if layer else v3((k - (n - 2) / 2) * w * 0.5, 0, rng.uniform(-0.04, 0.04))
        steak(bone, "%s_%d" % (name, k), foot + off + UP * (layer * th * 0.9), w=w * rng.uniform(0.85, 1.05), d=d, th=th,
              yaw=rng.uniform(-0.35, 0.35))


def cleaver(bone, name, edge_mid, yaw=0.0, tilt=0.0, blade=(0.34, 0.2), handle=0.3, sink=0.0):
    """A cleaver: the steel blade (edge down at `edge_mid`, sunk by `sink`), its wooden handle rising behind, tilted by
    `tilt` (radians) about the blade's long axis' normal."""
    edge_mid = v3(*edge_mid)
    R = ry(yaw) @ rz(tilt)
    bl, bh = blade
    c = edge_mid + R @ v3(0, bh / 2 - sink, 0)
    add_cube(bone, name + "_blade", c, R, (bl, bh, 0.025), {"all": "steel", "+3": "m7_blade", "-3": "m7_blade"}, stretch=True)
    a = c + R @ v3(-bl / 2, bh * 0.25, 0)
    b = a + R @ v3(-handle * 0.94, handle * 0.34, 0)
    beam(bone, name + "_handle", a, b, 0.055, "wood_dark", width=0.045, extend=0.01)
    add_cube(bone, name + "_rivet", a + (b - a) * 0.5, R, (0.03, 0.06, 0.05), "iron")


def chopping_block(bone, det, foot, rng, r=0.5, h=0.92):
    """The big round chopping block (a log: bark sides, ringed and blood-stained top) with a cleaver stuck in it."""
    foot = v3(*foot)
    wb.octo(bone, "chop_block", foot, r, h, {"all": "m7_bark", "+2": "m7_log_top", "-2": "m7_log_top"}, stretch=True)
    for k, y in enumerate((0.14, h - 0.24)):
        wb.octo(det, "chop_band_%d" % k, foot + UP * y, r + 0.015, 0.07, "iron_dark", stretch=True)
    cleaver(bone, "chop_cleaver", foot + UP * h + v3(0.02, 0, 0.04), yaw=-0.5, tilt=-0.2, blade=(0.5, 0.36), handle=0.46, sink=0.1)
    ml.collide((foot[0] - r, foot[1], foot[2] - r, foot[0] + r, foot[1] + h, foot[2] + r))


def knife_rack(bone, name, x0, x1, y, z, n=4, normal=(0, 0, 1)):
    """A board on the wall with knives and small cleavers hanging from it."""
    nz = v3(*normal)
    box(bone, name + "_board", (x0, y - 0.04, z), (x1, y + 0.08, z + 0.05 * nz[2]), "plank")
    for k in range(n):
        x = x0 + (x1 - x0) * (k + 0.5) / n
        p = v3(x, y - 0.04, z + 0.06 * nz[2])
        if k % 2 == 0:
            add_cube(bone, "%s_blade_%d" % (name, k), p - UP * 0.2, EYE, (0.16, 0.22, 0.02), {"all": "steel", "+3": "m7_blade", "-3": "m7_blade"},
                     stretch=True)
            add_cube(bone, "%s_handle_%d" % (name, k), p - UP * 0.36, EYE, (0.04, 0.14, 0.04), "wood_dark")
        else:
            add_cube(bone, "%s_blade_%d" % (name, k), p - UP * 0.22, EYE, (0.05, 0.3, 0.015), "steel", stretch=True)
            add_cube(bone, "%s_handle_%d" % (name, k), p - UP * 0.43, EYE, (0.04, 0.13, 0.04), "wood_dark")
