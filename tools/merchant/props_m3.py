"""Props of the cloth merchant's tent (tente_tissus, agent M3): rolls of coloured fabric, a bolt rack, stacks of
folded cloth, hanging cloths with ragged hems, a mannequin in a cream dress, teal and rose table cloths with a gold
border, a small teal patterned hanging. Region painters are added to the tent's atlas by register(atlas) (merchantlib
Atlas.add), the geometry reuses tentlib / wslib_a helpers (octo, loft, hanging_cloth, draped, rbox).
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "tents"))
sys.path.insert(0, os.path.join(HERE, "..", "workshops"))
sys.path.insert(0, os.path.join(HERE, ".."))
import tentlib as tl  # noqa: E402
import wslib_a as wl  # noqa: E402

v3, norm, UP, EYE = tl.v3, tl.norm, tl.UP, tl.EYE
add_cube, beam, loft = tl.add_cube, tl.beam, tl.loft
ry = tl.gg.ry

# ---------------------------------------------------------------- palette
FABRICS = {   # body colour, pattern colour (None: plain), pattern kind
    "red": ("a8262f", "d8ae42", "lozenge"),
    "gold": ("cf8a2c", "f0c25a", "stripe"),
    "yellow": ("dcb43c", "f2dc7a", "dots"),
    "purple": ("6a3a92", "c9a0e0", "lozenge"),
    "lilac": ("ab95cf", "e8dcf4", "dots"),
    "blue": ("3f5f9c", "a9bde0", "stripe"),
    "pink": ("c8607a", "f0b0c0", "dots"),
    "teal": ("1f7d80", "d8ae42", "lozenge"),
    "cream": ("e6dcc2", "c8b48a", "stripe"),
}
GOLD, GOLD_DK = "d8ae42", "9c7426"


def _rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _scale(c, k):
    return tuple(max(0, min(255, int(round(v * k)))) for v in c)


def _mix(a, b, t):
    return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(3))


def _jit(c, rng, n):
    return tuple(max(0, min(255, v + rng.randint(-n, n))) for v in c)


def _put(px, x, y, c, a=255):
    px[x, y] = tuple(int(max(0, min(255, k))) for k in c) + (a,)


def _weave(x, y):
    return 1.0 + (0.035 if (x + y) % 2 == 0 else -0.035) + 0.04 * math.sin(x * 0.37 + y * 0.11)


def _pattern(kind, x, y, w, h):
    """True where the pattern colour shows."""
    if kind == "lozenge":
        a, b = (x + y) % 8, (x - y) % 8
        return a == 0 or b == 0
    if kind == "dots":
        return (x % 6 == 2 and y % 6 == 2) or (x % 6 == 5 and y % 6 == 5)
    if kind == "stripe":
        return x % 8 in (0, 1)
    return False


# ---------------------------------------------------------------- painters (painter(img) on a w x h RGBA image)
def fabric_painter(colour):
    """The wound surface of a roll (u along the roll, v round it): the cloth with its pattern, darker wrap lines
    every few pixels across v (the layers), a gold or darker selvedge at both ends."""
    base, pat, kind = FABRICS[colour]
    base, pat = _rgb(base), _rgb(pat)

    def paint(img):
        w, h = img.size
        px = img.load()
        rng = random.Random(sum(map(ord, colour)))
        for y in range(h):
            for x in range(w):
                c = _scale(base, _weave(x, y))
                if _pattern(kind, x, y, w, h):
                    c = _mix(c, pat, 0.55)
                if y in (0, h - 1):
                    c = _scale(c, 0.86)
                if x in (0, w - 1):
                    c = _scale(_rgb(GOLD) if colour in ("red", "purple", "teal") else base, 0.85)
                _put(px, x, y, _jit(c, rng, 4))
    return paint


def end_painter(colour):
    """The end of a roll: the cloth's spiral round a light wooden core."""
    base = _rgb(FABRICS[colour][0])

    def paint(img):
        w, h = img.size
        px = img.load()
        rng = random.Random(7 + sum(map(ord, colour)))
        cx, cy = w / 2, h / 2
        for y in range(h):
            for x in range(w):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                r = math.hypot(dx, dy)
                a = math.atan2(dy, dx)
                if r < w * 0.12:
                    c = _rgb("c8a070")
                elif r < w * 0.17:
                    c = _rgb("6a4a2a")
                else:
                    ph = (r * 6.0 / w - a / (2 * math.pi)) % 1.0
                    c = _scale(base, 0.55 if ph < 0.25 else (1.12 if ph < 0.5 else 1.0))
                _put(px, x, y, _jit(c, rng, 3))
    return paint


def rag_painter(colour, border=None, motif=False, seed=0):
    """A hanging cloth: soft vertical folds, the pattern, a band of `border` near the top and above the hem, a
    ragged bottom edge (transparent notches)."""
    base, pat, kind = FABRICS[colour]
    base, pat = _rgb(base), _rgb(pat)
    bd = _rgb(border) if border else None

    def paint(img):
        w, h = img.size
        px = img.load()
        rng = random.Random(31 + seed)
        cut = []
        for x in range(w):
            c = h - (rng.randint(2, 5) if x % 4 in (0, 1) else rng.randint(0, 1))
            cut.append(c)
        for y in range(h):
            for x in range(w):
                if y >= cut[x]:
                    px[x, y] = (0, 0, 0, 0)
                    continue
                k = 1.0 + 0.11 * math.sin(2 * math.pi * x / 8) + (0.03 if (x + y) % 2 == 0 else -0.03)
                c = _scale(base, k)
                if _pattern(kind, x, y, w, h) and 4 < y < h - 10:
                    c = _mix(c, pat, 0.5)
                if motif:
                    # a gold medallion in the middle
                    d = math.hypot(x + 0.5 - w / 2, (y + 0.5 - h * 0.45) * 0.9)
                    if 3.0 < d < 4.6 or d < 1.6:
                        c = _scale(_rgb(GOLD), k)
                if bd is not None and (1 <= y <= 2 or h - 9 <= y <= h - 7):
                    c = _scale(bd, k)
                _put(px, x, y, _jit(c, rng, 4))
    return paint


def tablecloth_painter(colour, border=GOLD, fringe=True):
    """A cloth laid on a table and hanging over its edge (the hem at the bottom of the region): the cloth, a gold
    border along the sides and the hem, a gold band above the hem, a fringe of tassels at the very bottom."""
    base, pat, kind = FABRICS[colour]
    base, bd = _rgb(base), _rgb(border)

    def paint(img):
        w, h = img.size
        px = img.load()
        rng = random.Random(53 + len(colour))
        for y in range(h):
            for x in range(w):
                if fringe and y >= h - 3:
                    if x % 3 == 2 or (y == h - 1 and x % 3 == 1):
                        px[x, y] = (0, 0, 0, 0)
                        continue
                    _put(px, x, y, _jit(_scale(bd, 0.95), rng, 5))
                    continue
                c = _scale(base, _weave(x, y))
                if x in (1, w - 2) or y in (h - 5, h - 6) or y == h - 9:
                    c = _scale(bd, _weave(x, y))
                _put(px, x, y, _jit(c, rng, 4))
    return paint


def dress_painter(part):
    """The cream dress: 'bodice' (laced front, a brown belt with a brass buckle at the bottom, a gathered neckline)
    or 'skirt' (soft vertical folds, a darker hem)."""
    base = _rgb("e8dfc6")

    def paint(img):
        w, h = img.size
        px = img.load()
        rng = random.Random(77 if part == "bodice" else 78)
        for y in range(h):
            for x in range(w):
                k = 1.0 + (0.08 if part == "skirt" else 0.04) * math.sin(2 * math.pi * x / (6 if part == "skirt" else 9))
                k += 0.025 if (x + y) % 2 == 0 else -0.025
                c = _scale(base, k)
                if part == "bodice":
                    cx = w // 2
                    if y < 3 and abs(x - cx) < w * 0.32:
                        c = _scale(base, 0.86)                    # neckline
                    if 3 <= y < h - 6 and abs(x - cx) <= 1 and (y % 3 != 0):
                        c = _rgb("7a5a3a")                       # lacing
                    if 3 <= y < h - 6 and abs(x - cx) == 2 and y % 3 == 0:
                        c = _rgb("7a5a3a")
                    if h - 5 <= y < h - 1:
                        c = _rgb("5a3a20") if abs(x - cx) > 2 else _rgb("c9a046")   # belt and buckle
                else:
                    if y >= h - 3:
                        c = _scale(base, 0.82)
                    if y == h - 5:
                        c = _scale(_rgb(GOLD), 0.95)
                _put(px, x, y, _jit(c, rng, 3))
    return paint


def small_banner_painter(colour="teal"):
    """A narrow hanging of the tent's colour: gold border, a gold lozenge lattice, a V-cut bottom (transparent)."""
    base = _rgb(FABRICS[colour][0])
    gold = _rgb(GOLD)

    def paint(img):
        w, h = img.size
        px = img.load()
        rng = random.Random(91)
        for y in range(h):
            for x in range(w):
                vy = h - 1 - abs(x + 0.5 - w / 2) * (6.0 / (w / 2))
                if y > vy:
                    px[x, y] = (0, 0, 0, 0)
                    continue
                c = _scale(base, _weave(x, y))
                if x in (0, w - 1) or y in (0, 1) or y > vy - 1.5:
                    c = gold
                elif ((x + y) % 6 == 0 or (x - y) % 6 == 0) and 2 < x < w - 3:
                    c = _mix(c, gold, 0.6)
                _put(px, x, y, _jit(c, rng, 4))
    return paint


ROLL_COLOURS = ("red", "gold", "yellow", "purple", "lilac", "blue", "pink", "teal", "cream")


def register(atlas):
    """Adds every region of the cloth merchant to the tent's atlas (merchantlib.Atlas.add)."""
    for c in ROLL_COLOURS:
        atlas.add("tis_fab_" + c, 32, 16, fabric_painter(c))
        atlas.add("tis_end_" + c, 16, 16, end_painter(c))
    atlas.add("tis_rag_red", 16, 32, rag_painter("red", border=GOLD, seed=1))
    atlas.add("tis_rag_lilac", 16, 32, rag_painter("lilac", border="6a3a92", seed=2))
    atlas.add("tis_rag_purple", 16, 32, rag_painter("purple", border=GOLD, motif=True, seed=3))
    atlas.add("tis_rag_cream", 16, 32, rag_painter("cream", border="a8262f", seed=4))
    atlas.add("tis_rag_teal", 16, 32, rag_painter("teal", border=GOLD, seed=5))
    atlas.add("tis_cloth_teal", 32, 32, tablecloth_painter("teal"))
    atlas.add("tis_cloth_pink", 32, 32, tablecloth_painter("pink"))
    atlas.add("tis_dress", 16, 16, dress_painter("bodice"))
    atlas.add("tis_skirt", 32, 16, dress_painter("skirt"))
    atlas.add("tis_hanging", 16, 32, small_banner_painter("teal"))


# ---------------------------------------------------------------- geometry
TIP = 1.31   # wslib_a.octo = two squares turned 45 degrees: its tips reach 1.31 r from the axis


def roll(bone, name, p0, p1, r, colour):
    """A roll of cloth lying from p0 to p1 (octagonal prism, its tips TIP * r from the axis), the spiral on its ends."""
    wl.octo(bone, name, p0, p1, r, "tis_fab_" + colour, end="tis_end_" + colour)


def roll_stack(bone, name, x0, x1, z, y0, colours, r=0.13, jitter=0.05, seed=0):
    """Rolls lying along x stacked one on the other from y0 (a tall bolt rack's load): the ends a little uneven."""
    rng = random.Random(seed)
    y = y0
    for k, col in enumerate(colours):
        rr = r * rng.uniform(0.9, 1.08)
        dz = (0.035 if k % 2 else -0.035)
        a = x0 + rng.uniform(-jitter, jitter)
        b = x1 + rng.uniform(-jitter, jitter)
        roll(bone, "%s_%d" % (name, k), (a, y + rr * TIP, z + dz), (b, y + rr * TIP, z + dz), rr, col)
        y += 2 * rr * TIP + 0.008
    return y


def bolt_pyramid(bone, name, cx, cz, y, colours, r=0.085, length=0.42, rows=(4, 3, 2)):
    """Short bolts of cloth lying front to back (ends to the front) piled in a pyramid on a table top at y."""
    k = 0
    for j, n in enumerate(rows):
        yy = y + r * TIP + j * 2 * r * TIP * 0.8
        for i in range(n):
            x = cx + (i - (n - 1) / 2) * 2 * r * TIP * 1.01
            col = colours[k % len(colours)]
            zz = cz + (0.02 if (i + j) % 2 else -0.02)
            roll(bone, "%s_%d" % (name, k), (x, yy, zz - length / 2), (x, yy, zz + length / 2), r, col)
            k += 1


def folded_stack(bone, name, foot, colours, w=0.42, d=0.34, th=0.07, yaw=0.0):
    """A pile of folded cloths (flat boxes, slightly turned one on the other)."""
    foot = v3(*foot)
    y = 0.0
    for k, col in enumerate(colours):
        wl.rbox(bone, "%s_%d" % (name, k), foot + UP * y, (w * (1 - 0.04 * k), th, d * (1 - 0.03 * k)), yaw + 0.07 * ((k % 3) - 1),
                "tis_fab_" + col, stretch=True)
        y += th
    return foot[1] + y


def hanging_row(bone, detail, name, a, b, cloths, length, rod_region="wood_dark", gap=0.06, sway=0.035):
    """A rod from a to b and cloths hanging from it side by side (regions `cloths`, each its share of the rod)."""
    a, b = v3(*a), v3(*b)
    beam(bone, name + "_rod", a, b, 0.05, rod_region, extend=0.06)
    n = len(cloths)
    L = np.linalg.norm(b - a)
    d = (b - a) / L
    w = (L - gap * (n + 1)) / n
    out = []
    for k, (reg, ln) in enumerate(cloths):
        s0 = gap + k * (w + gap)
        p0, p1 = a + d * s0 - UP * 0.02, a + d * (s0 + w) - UP * 0.02
        wl.hanging_cloth(bone, "%s_%d" % (name, k), p0, p1, length * ln, reg, sway=sway, nx=2, ny=2)
        out.append((p0, p1))
    return out


def drape(bone, name, a0, a1, back, edge, y_top, hang, region, axis="z", nx=3, curl=0.04, th=0.02):
    """A cloth lying on a table top and hanging over one edge. axis "z": the cloth spans x from a0 to a1, lies from
    z = back to the edge z = edge and hangs over it (towards +z if edge > back); axis "x": spans z from a0 to a1, lies
    from x = back to x = edge. The region spans the whole cloth (its bottom = the hem)."""
    flat = abs(edge - back)
    sgn = 1.0 if edge > back else -1.0
    total = flat + hang

    def P(s, t):
        a = a0 + (a1 - a0) * s
        d = t * total
        if d <= flat:
            w, y = back + sgn * d, y_top + 0.012
        else:
            dd = d - flat
            w, y = edge + sgn * (0.025 + curl * math.sin(s * math.pi * 2) * dd / hang), y_top + 0.012 - dd
        return v3(a, y, w) if axis == "z" else v3(w, y, a)
    loft(bone, name, P, nx, 3, region, th=th)


def mannequin(bone, detail, name, c, yaw=0.0, collide=None):
    """A dress mannequin: a square wooden plinth, a pole, a cream dress (laced bodice, short puffed sleeves, a flared
    skirt to the knee), a wooden neck knob. Faces +z turned by yaw. Returns its collision box."""
    c = v3(*c)
    R = ry(yaw)
    fwd = R @ v3(0, 0, 1)
    side = R @ v3(1, 0, 0)
    # the foot: a wide board plate, a square plinth, the post
    add_cube(bone, "%s_plate" % name, c + UP * 0.035, R, (0.56, 0.07, 0.56), {"all": "wood_dark", "+2": "wood"})
    add_cube(bone, "%s_plinth" % name, c + UP * 0.17, R, (0.34, 0.2, 0.34), "wood_dark")
    beam(bone, "%s_pole" % name, c + UP * 0.27, c + UP * 0.8, 0.08, "wood")
    # the skirt: a flared octagonal frustum lofted from the waist down to the hem
    waist_y, hem_y = 1.32, 0.66
    rw, rh = 0.19, 0.34
    nseg = 8
    for k in range(nseg):
        a0, a1 = 2 * math.pi * k / nseg, 2 * math.pi * (k + 1) / nseg

        def P(s, t, a0=a0, a1=a1):
            a = a0 + (a1 - a0) * s
            r = rw + (rh - rw) * (t ** 0.8)
            r *= 1.0 + 0.06 * math.sin(a * 4 + 0.3) * t      # soft folds
            rad = side * math.cos(a) * 1.0 + fwd * math.sin(a) * 0.82
            return c + UP * (waist_y + (hem_y - waist_y) * t) + rad * r
        loft(bone, "%s_skirt_%d" % (name, k), P, 1, 2, "tis_skirt", th=0.025, u_hint=None)
    # the bodice, shoulders, puffed short sleeves
    tc = c + UP * 1.58
    add_cube(bone, "%s_bodice" % name, tc, R, (0.4, 0.56, 0.24), {"all": "tis_dress", "-3": "tis_skirt"}, stretch=True,
             u_dir=side, v_dir=-UP)
    add_cube(bone, "%s_shoulders" % name, tc + UP * 0.25, R, (0.52, 0.1, 0.26), "tis_skirt", stretch=True)
    for s in (1, -1):
        p0 = tc + side * (s * 0.27) + UP * 0.2
        p1 = tc + side * (s * 0.36) + UP * 0.0
        beam(bone, "%s_sleeve_%d" % (name, s), p0, p1, 0.16, "tis_skirt", width=0.17)
        beam(detail, "%s_cuff_%d" % (name, s), p1, p1 - UP * 0.03 + side * s * 0.01, 0.17, "tis_fab_cream", width=0.18)
    add_cube(bone, "%s_neck" % name, tc + UP * 0.34, R, (0.1, 0.1, 0.1), "wood")
    add_cube(bone, "%s_head" % name, tc + UP * 0.48, R, (0.18, 0.2, 0.18), {"all": "wood", "+2": "wood_dark"})
    return (c[0] - 0.36, 0.0, c[2] - 0.36, c[0] + 0.36, 1.95, c[2] + 0.36)


def spools(bone, name, foot, colours, step=0.11, r=0.04, h=0.1, yaw=0.0):
    """A row of thread spools (small rolls standing up, wooden rims)."""
    foot = v3(*foot)
    d = ry(yaw) @ v3(1, 0, 0)
    for k, col in enumerate(colours):
        p = foot + d * (k * step)
        wl.octo(bone, "%s_%d" % (name, k), p + UP * 0.012, p + UP * (h - 0.012), r, "tis_fab_" + col, end="tis_end_" + col)
        add_cube(bone, "%s_rim_%d" % (name, k), p + UP * 0.006, EYE, (2.5 * r, 0.012, 2.5 * r), "wood")
        add_cube(bone, "%s_rimt_%d" % (name, k), p + UP * (h - 0.006), EYE, (2.5 * r, 0.012, 2.5 * r), "wood")
