"""Props of the fishmonger's stall (1.17.0, agent F): tente_poissonnier.

The longer gabled market stall of merchantlib.stall in blue and white; this module adds what makes it a fish stall:
its own atlas regions (painted into the free band of the tent's atlas with atlas.add, named "m9_..." plus the few
shared ones of props_m1 it needs) and the geometry of the goods.

    import props_m9 as p9
    p9.add_regions(atlas, p9.FISH_REGIONS)                 # before export
    p9.hanging_fish(bone, det, "f0", top, "cod", length=0.8)   # a fish hung by the mouth on a chain from `top`
    p9.lying_fish(bone, "f1", foot, "salmon", length=0.6, yaw=0.3)
    p9.ice_bed(...), p9.net_swag(...), p9.lobster_trap(...), p9.anchor(...), p9.crab(...), p9.lobster(...),
    p9.seaweed(...), p9.price_sign(...), p9.rope_wrap(...), p9.salmon_steak(...)

Fish kinds: cod (grey-green, spotted), blue (blue-grey), silver (mackerel: dark wavy bars on the back), red (red
snapper), salmon (orange-pink). Coordinates: tent-local blocks (y up, +z = the open front). Cubes named "glow..." are
drawn full bright.
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

wb = p1.wb
v3, norm, add_cube, beam, loft = ml.v3, ml.norm, ml.add_cube, ml.beam, ml.loft
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ry, rx, rz = ml.ry, ml.rx, ml.rz
_rgb, _mix, _jitter, _scale = ml._rgb, ml._mix, ml._jitter, ml._scale
CLEAR = (0, 0, 0, 0)

# back, belly, fin colours of each fish kind
FISH = {
    "cod":    (_rgb("6e7468"), _rgb("e4e2d6"), _rgb("8a8a78")),
    "blue":   (_rgb("3e5684"), _rgb("d6dce6"), _rgb("5a6e98")),
    "silver": (_rgb("2e4a6a"), _rgb("e8ecf0"), _rgb("7a8a9a")),
    "red":    (_rgb("b8342a"), _rgb("f0a888"), _rgb("d2523a")),
    "salmon": (_rgb("d8683e"), _rgb("f6b890"), _rgb("c05a36")),
}


# ================================================================ painters (img = the region, w x h RGBA)
def _noise(base, seed, n=6):
    def p(img):
        rng = random.Random(seed)
        px = img.load()
        for y in range(img.height):
            for x in range(img.width):
                px[x, y] = _jitter(base, rng, n) + (255,)
    return p


def _half_width(t):
    """The fish's profile: half its depth (in fractions of the image width) at t (0 = the mouth, 1 = the tail tip)."""
    if t < 0.07:
        return 0.15 + 0.18 * t / 0.07
    if t < 0.36:
        return 0.33 + 0.13 * (t - 0.07) / 0.29
    if t < 0.8:
        return 0.46 - 0.35 * ((t - 0.36) / 0.44) ** 1.1
    if t < 0.85:
        return 0.11
    return 0.11 + 0.27 * (t - 0.85) / 0.15


def _fish_colour(kind, xf, t, rng):
    """The colour at (xf across: 0 = back, 1 = belly; t along)."""
    back, belly, fin = FISH[kind]
    c = _mix(back, belly, max(0.0, min(1.0, (xf - 0.25) / 0.5)) ** 1.1)
    if kind == "cod" and xf < 0.55 and rng.random() < 0.16:
        c = _scale(c, 0.62)
    if kind == "blue" and xf < 0.5 and rng.random() < 0.1:
        c = _mix(c, (230, 236, 246), 0.5)
    if kind == "silver" and xf < 0.46 and math.sin(t * 46 + xf * 9) > 0.45:
        c = _scale(c, 0.55)
    if kind == "salmon" and xf < 0.5 and rng.random() < 0.08:
        c = _scale(c, 0.7)
    if kind in ("silver", "blue", "cod") and abs(xf - 0.5) < 0.05:
        c = _mix(c, (240, 240, 236), 0.35)       # the lateral line
    return c


def _fish_side(kind, seed):
    """A whole fish seen from the side, hung head up (cut-out): the mouth at the top, the forked tail at the bottom,
    the dorsal fin on the left (the back), pectoral and anal fins on the right (the belly), an eye, the gill."""
    back, belly, fin = FISH[kind]

    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            t = (y + 0.5) / h
            hw = _half_width(t)
            for x in range(w):
                xf = (x + 0.5) / w
                d = abs(xf - 0.5)
                inside = d <= hw
                if t > 0.93 and d < (t - 0.93) * 3.0:            # the fork of the tail
                    inside = False
                c = None
                if inside:
                    c = _fish_colour(kind, xf, t, rng)
                    if t > 0.85:
                        c = _mix(fin, back, 0.3) if (x + y) % 3 else _scale(fin, 0.8)
                    if d > hw - 0.07 and t < 0.85:
                        c = _scale(c, 0.82)
                elif 0.36 < t < 0.62 and xf < 0.5 and d <= hw + 0.08 * math.sin(math.pi * (t - 0.36) / 0.26):
                    c = _scale(fin, 0.9 if y % 2 else 0.75)          # the dorsal fin
                elif 0.56 < t < 0.68 and xf > 0.5 and d <= hw + 0.07 * math.sin(math.pi * (t - 0.56) / 0.12):
                    c = _scale(fin, 0.95 if y % 2 else 0.8)          # the anal fin
                elif 0.2 < t < 0.3 and xf > 0.5 and d <= hw + 0.1 * math.sin(math.pi * (t - 0.2) / 0.1):
                    c = _scale(fin, 1.0 if y % 2 else 0.82)          # the pectoral fin
                px[x, y] = CLEAR if c is None else _jitter(c, rng, 6) + (255,)
        # the eye and the gill
        ex, ey = int(w * 0.42), int(h * 0.075)
        for (dx, dy, c) in ((0, 0, (20, 20, 22)), (1, 0, (20, 20, 22)), (0, 1, (20, 20, 22)), (1, 1, (40, 40, 44)), (-1, 0, (230, 220, 190)),
                            (2, 0, (230, 220, 190)), (0, -1, (230, 220, 190)), (1, 2, (230, 220, 190))):
            if 0 <= ex + dx < w and 0 <= ey + dy < h:
                px[ex + dx, ey + dy] = c + (255,)
        gy = int(h * 0.19)
        for x in range(int(w * 0.24), int(w * 0.74)):
            yy = gy - int(2.0 * math.sin(math.pi * (x - w * 0.24) / (w * 0.5)))
            if px[x, yy][3]:
                px[x, yy] = _scale(px[x, yy][:3], 0.6) + (255,)
        # the mouth
        for x in range(int(w * 0.44), int(w * 0.58)):
            if px[x, 1][3]:
                px[x, 1] = (60, 40, 40, 255)
    return p


def _fish_body(kind, seed):
    """The fish's flank for the body box (u across: back -> belly), scaled."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                xf = 0.28 + 0.44 * (x + 0.5) / w
                c = _fish_colour(kind, xf, 0.3 + 0.32 * y / h, rng)
                if (x + 2 * (y // 2)) % 4 == 0:
                    c = _scale(c, 0.9)                         # scales
                px[x, y] = _jitter(c, rng, 5) + (255,)
    return p


def _ice_chunk(seed):
    """One loose block of ice: white with a pale blue body, bright top-left edges, blue shaded bottom-right."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _mix(_rgb("eef8ff"), _rgb("a8d0ec"), (x + y) / (w + h))
                if x == 0 or y == 0:
                    c = (255, 255, 255)
                elif x == w - 1 or y == h - 1:
                    c = _rgb("7aa8cc")
                elif abs(x - y) < 1 and rng.random() < 0.7:
                    c = _mix(c, (255, 255, 255), 0.6)
                px[x, y] = _jitter(c, rng, 4) + (255,)
    return p


def _ice(seed, side=False):
    """Crushed ice blocks (a grid of chunky cubes): white / pale blue, bright top-left, shaded bottom-right, blue gaps."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        cell = 8
        for y in range(h):
            for x in range(w):
                cx, cy = x % cell, y % cell
                tone = random.Random((x // cell) * 31 + (y // cell) * 7 + seed).uniform(0.9, 1.06)
                c = _scale(_rgb("d8ecf6") if not side else _rgb("bcdcee"), tone)
                if cx == 0 or cy == 0:
                    c = _rgb("88b4d4")
                elif cx == 1 or cy == 1:
                    c = _mix(c, (255, 255, 255), 0.7)
                elif cx == cell - 1 or cy == cell - 1:
                    c = _scale(c, 0.8)
                if rng.random() < 0.04:
                    c = (255, 255, 255)
                px[x, y] = _jitter(c, rng, 4) + (255,)
    return p


def _net(seed, arch=False):
    """A fishing net (cut-out): a diamond mesh of tarred brown cord, darker knots, a thick rope along the top and the
    bottom (arch: a half disc with a rope rim, for the lobster trap's ends)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        m = 8
        for y in range(h):
            for x in range(w):
                on = (x + y) % m == 0 or (x - y) % m == 0
                knot = (x + y) % m == 0 and (x - y) % m == 0
                c = None
                if on:
                    c = _rgb("5a3e1e") if knot else _scale(_rgb("b08a48"), 0.8 + 0.25 * rng.random())
                if not arch and (y < 2 or y >= h - 2):
                    c = _rgb("8a6a3e") if (x + y) % 3 else _rgb("5e4628")
                if arch:
                    r = math.hypot((x + 0.5 - w / 2) / (w / 2), (h - y - 0.5) / h)
                    if r > 1.0:
                        c = None
                    elif r > 0.88 or y >= h - 2:
                        c = _rgb("8a6a3e") if (x + y) % 3 else _rgb("5e4628")
                px[x, y] = CLEAR if c is None else _jitter(c, rng, 6) + (255,)
    return p


def _kelp(seed):
    """Hanging seaweed (cut-out): a few wavy olive / dark green ribbons with frilled edges and little bladders."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                px[x, y] = CLEAR
        greens = [_rgb("4a6a22"), _rgb("5a7a2a"), _rgb("3a5a1e"), _rgb("6a8a30"), _rgb("2e4a1a")]
        for s in range(5):
            x0 = rng.uniform(1.5, w - 2.5)
            L = h * rng.uniform(0.55, 1.0)
            ph, amp, bw = rng.uniform(0, 6), rng.uniform(0.8, 2.0), rng.uniform(1.0, 2.2)
            c0 = rng.choice(greens)
            for y in range(int(L)):
                xc = x0 + amp * math.sin(y * 0.35 + ph)
                hw = bw * (1.0 - 0.4 * y / h) + 0.5 * math.sin(y * 1.3 + s)
                for x in range(int(xc - hw), int(xc + hw) + 1):
                    if 0 <= x < w:
                        edge = abs(x - xc) > hw - 1
                        c = _scale(c0, 0.75) if edge else _scale(c0, 1.0 + 0.1 * math.sin(y * 0.7))
                        px[x, y] = _jitter(c, rng, 8) + (255,)
                if y % 7 == 3 and 0 <= int(xc) < w:
                    px[int(xc), y] = _rgb("8a9a3a") + (255,)
    return p


def _heap(kind_cols, seed, bg=_rgb("cfe4f0"), n=10, crabs=False):
    """A heap seen from above: fish lying every which way on crushed ice (or red crabs and lobster tails)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = bg if (x % 6 and y % 6) else _scale(bg, 0.8)
                px[x, y] = _jitter(c, rng, 6) + (255,)
        for _ in range(n):
            cx, cy = rng.uniform(2, w - 3), rng.uniform(2, h - 3)
            back, belly, _f = kind_cols[rng.randrange(len(kind_cols))]
            if crabs:
                r = rng.uniform(3.0, 4.5)
                for y in range(int(cy - r - 3), int(cy + r + 3)):
                    for x in range(int(cx - r - 3), int(cx + r + 3)):
                        if 0 <= x < w and 0 <= y < h:
                            d = math.hypot((x - cx) / 1.2, y - cy)
                            if d < r:
                                c = _mix(back, belly, 0.4 * (y - cy + r) / (2 * r))
                                if d < 1.2:
                                    c = _mix(c, (255, 200, 160), 0.4)
                                px[x, y] = _jitter(c, rng, 8) + (255,)
                            elif d < r + 2.2 and abs(y - cy) < 1.2 and (x - cx) % 2 == 0:
                                px[x, y] = _jitter(_scale(back, 0.8), rng, 8) + (255,)   # legs
                for sx in (-1, 1):   # claws
                    for y in range(int(cy - r - 2), int(cy - r + 1)):
                        for x in (int(cx + sx * r * 0.7), int(cx + sx * r * 0.7) + sx):
                            if 0 <= x < w and 0 <= y < h:
                                px[x, y] = _jitter(_scale(back, 1.1), rng, 8) + (255,)
                continue
            a = rng.uniform(0, math.pi)
            L, W = rng.uniform(7, 11), rng.uniform(1.8, 2.6)
            ca, sa = math.cos(a), math.sin(a)
            for y in range(h):
                for x in range(w):
                    u, v = (x - cx) * ca + (y - cy) * sa, -(x - cx) * sa + (y - cy) * ca
                    t = (u + L / 2) / L
                    if 0 <= t <= 1.15:
                        hwid = W * (math.sin(math.pi * min(t, 1.0)) ** 0.7) if t <= 1.0 else W * 0.9 * (t - 1.0) / 0.15
                        if abs(v) <= hwid:
                            c = _mix(back, belly, (v + hwid) / (2 * hwid + 1e-6))
                            if t < 0.12 and abs(v) < 0.8:
                                c = (24, 24, 26)
                            px[x, y] = _jitter(c, rng, 6) + (255,)
    return p


def _shell(seed, base=_rgb("c8321e")):
    """A crab / lobster shell: glossy red-orange, darker speckles, a lighter rim."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _scale(base, 1.0 + 0.12 * math.sin(x * 1.1) * math.sin(y * 0.9))
                if rng.random() < 0.12:
                    c = _scale(c, 0.7)
                if y == 0 or x == 0:
                    c = _mix(c, (250, 180, 120), 0.4)
                px[x, y] = _jitter(c, rng, 6) + (255,)
    return p


def _salmon_flesh(seed):
    """Salmon flesh (a steak's cut face): orange with the white curved fat lines, a silver skin rim."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _mix(_rgb("f08a5a"), _rgb("e46a3e"), rng.random() * 0.5)
                if (x + int(2.5 * math.sin(y * 0.5))) % 4 == 0:
                    c = _rgb("f8d0b4")
                e = min(x, y, w - 1 - x, h - 1 - y)
                if e < 1:
                    c = _rgb("9aa2aa")
                px[x, y] = _jitter(c, rng, 5) + (255,)
    return p


def _sign(seed):
    """A small wooden price board: light planks, a dark border, chalk scribbles."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _rgb("b8915a") if y != h // 2 else _rgb("9a764a")
                e = min(x, y, w - 1 - x, h - 1 - y)
                if e < 1:
                    c = _rgb("6a4a28")
                px[x, y] = _jitter(c, rng, 6) + (255,)
        for x in range(3, w - 3):
            if rng.random() < 0.6:
                px[x, h // 2 - 1] = (70, 50, 30, 255)
    return p


def _green_jar(seed):
    """A green glass jar of pickled fish: green glass, a lighter streak, dark contents."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                c = _mix(_rgb("4a8a4a"), _rgb("2a5a32"), y / h)
                if x == w // 4:
                    c = _mix(c, (220, 255, 220), 0.5)
                if y > h * 0.45 and rng.random() < 0.3:
                    c = _mix(c, _rgb("b0a080"), 0.4)
                px[x, y] = _jitter(c, rng, 6) + (255,)
    return p


def _stone(seed):
    return _noise(_rgb("8e9094"), seed, 10)


PAINTERS = {
    "m9_ice": (128, 32, _ice(901)),
    "m9_ice_side": (32, 16, _ice(902, side=True)),
    "m9_ice_chunk": (8, 8, _ice_chunk(915)),
    "m9_net": (64, 32, _net(903)),
    "m9_net_arch": (32, 16, _net(904, arch=True)),
    "m9_kelp": (16, 48, _kelp(905)),
    "m9_fish_heap": (32, 32, _heap([FISH["silver"], FISH["blue"], FISH["cod"]], 906, n=11)),
    "m9_salmon_heap": (32, 32, _heap([FISH["salmon"], FISH["silver"]], 907, n=9)),
    "m9_crab_heap": (32, 32, _heap([(_rgb("c8321e"), _rgb("e86a3a"), None), (_rgb("a82818"), _rgb("d8582e"), None)], 908, n=9,
                                   bg=_rgb("5a3a20"), crabs=True)),
    "m9_shell": (8, 8, _shell(909)),
    "m9_shell_dark": (8, 8, _shell(910, base=_rgb("8e2416"))),
    "m9_salmon_flesh": (16, 16, _salmon_flesh(911)),
    "m9_sign": (16, 8, _sign(912)),
    "m9_jar_green": (8, 16, _green_jar(913)),
    "m9_bone": (8, 8, _noise(_rgb("e6dcc4"), 914, 6)),
}
for _k, _kind in enumerate(FISH):
    PAINTERS["m9_fish_" + _kind] = (16, 48, _fish_side(_kind, 920 + _k))
    PAINTERS["m9_body_" + _kind] = (8, 16, _fish_body(_kind, 930 + _k))

_M1 = ("iron_dark", "jar", "jar_top", "linen", "pot_clay", "soil", "sprout", "vines")
FISH_REGIONS = [n for n in PAINTERS] + list(_M1)


def add_regions(atlas, names):
    """Adds the named regions to the tent's atlas (merchantlib.Atlas), skipping the shell's own."""
    for n in names:
        if n in atlas.regions and n not in atlas.painters:
            continue
        w, h, f = PAINTERS[n] if n in PAINTERS else p1.PAINTERS[n]
        atlas.add(n, w, h, f)


# ================================================================ shared
def box(bone, name, lo, hi, region, yaw=0.0, stretch=True):
    lo, hi = v3(*lo), v3(*hi)
    return add_cube(bone, name, (lo + hi) / 2, ry(yaw), np.abs(hi - lo), region, stretch=stretch)


def hook(bone, name, top, drop=0.3, link=0.1):
    """An iron chain from the rail down to an S-hook (returns the hook's lowest point)."""
    top = v3(*top)
    wb.chain(bone, name + "_chain", top, top - UP * drop, link=link)
    add_cube(bone, name + "_hook", top - UP * (drop + 0.04), EYE, (0.03, 0.09, 0.03), "iron_dark")
    return top - UP * (drop + 0.08)


# ================================================================ fish
def _fish_axes(normal, along):
    """Rotation (columns u, v, n): n = the side the fish shows, v = from the tail to the head."""
    n = norm(v3(*normal))
    v = v3(*along)
    v = norm(v - np.dot(v, n) * n)
    u = np.cross(v, n)
    return np.column_stack([u, v, n])


def fish(bone, name, head, kind="cod", length=0.7, normal=(0, 0, 1), along=(0, 1, 0), th=None):
    """A whole fish: the cut-out side silhouette (both faces) and a body box giving it thickness, its mouth at `head`,
    lying along -`along` from there, its side facing `normal`."""
    head = v3(*head)
    R = _fish_axes(normal, along)
    u, v, n = R[:, 0], R[:, 1], R[:, 2]
    w = length / 3.0
    c = head - v * (length / 2)
    add_cube(bone, name, c, R, (w, length, 0.012), {"all": None, "+3": "m9_fish_" + kind, "-3": "m9_fish_" + kind}, stretch=True,
             u_dir=-u, v_dir=-v)
    th = th if th is not None else max(0.05, length * 0.11)
    # the body box: from behind the gill to before the tail, across the middle of the flank
    add_cube(bone, name + "_body", head - v * (length * 0.4), R, (w * 0.5, length * 0.42, th),
             {"all": "m9_body_" + kind}, stretch=True, u_dir=-u, v_dir=-v)


def hanging_fish(bone, det, name, top, kind="cod", length=0.75, drop=0.25, yaw=0.0):
    """A fish hung head up by the mouth on a chain and an S-hook from `top` (the rail's underside); its side faces the
    front (turned by yaw)."""
    t = hook(det, name + "_hk", top, drop=drop)
    fish(bone, name, t + UP * 0.02, kind, length, normal=ry(yaw) @ Z, along=UP)
    return t - UP * length


def lying_fish(bone, name, foot, kind="cod", length=0.6, yaw=0.0, tilt=0.0):
    """A fish lying on its side on a surface (foot = the middle of its belly on the surface), the head towards
    +x turned by yaw."""
    foot = v3(*foot)
    along = ry(yaw) @ X
    n = rx(0) @ UP
    if tilt:
        n = norm(UP + ry(yaw) @ Z * tilt)
    th = max(0.05, length * 0.11)
    fish(bone, name, foot + along * (length / 2) + UP * (th / 2 + 0.005), kind, length, normal=n, along=along, th=th)


def fish_row(bone, name, x0, x1, y, z, kinds, rng, length=(0.45, 0.6), yaw=0.0, spread=0.05):
    """Fish lying side by side across a tray (head to the front-right), kinds in turn."""
    n = max(1, int((x1 - x0) / 0.17))
    for k in range(n):
        x = x0 + (x1 - x0) * (k + 0.5) / n
        lying_fish(bone, "%s_%d" % (name, k), (x, y, z + rng.uniform(-spread, spread)), kinds[k % len(kinds)],
                   length=rng.uniform(*length), yaw=yaw + math.pi / 2 + rng.uniform(-0.2, 0.2))


# ================================================================ ice, crates of fish
def ice_bed(bone, det, name, x0, x1, z0, z1, y, rng, chunks=6, tilt=0.0, size=(0.1, 0.16), front=0.5):
    """A bed of crushed ice (x0..x1, z0..z1, its top at y; tilt raises the back by `tilt`) and a few loose ice blocks
    on it (`front`: the fraction of them along the front edge)."""
    cz = (z0 + z1) / 2
    d = z1 - z0
    a = math.atan2(tilt, d) if tilt else 0.0
    R = rx(a)
    th = 0.12
    c = v3((x0 + x1) / 2, y + tilt / 2 - th / 2, cz)
    add_cube(bone, name, c, R, (x1 - x0, th, math.hypot(d, tilt)), {"all": "m9_ice_side", "+2": "m9_ice"}, stretch=True)
    for k in range(chunks):
        s = rng.uniform(*size)
        nf = int(chunks * front)
        if k < nf:
            xx, zz = x0 + 0.08 + (x1 - x0 - 0.16) * (k + rng.uniform(0.2, 0.8)) / nf, z1 - rng.uniform(0.04, 0.12)
        else:
            xx, zz = rng.uniform(x0 + 0.1, x1 - 0.1), rng.uniform(z0 + 0.08, z1 - 0.08)
        yy = y + tilt * (z1 - zz) / d if tilt else y
        add_cube(det, "%s_cube_%d" % (name, k), (xx, yy + s * 0.25, zz), ry(rng.uniform(0, 1.5)) @ R, (s, s * 0.8, s),
                 {"all": "m9_ice_chunk"}, stretch=True)
    return lambda zz: y + (tilt * (z1 - zz) / d if tilt else 0.0)


def fish_crate(bone, name, foot, size, content="m9_fish_heap", yaw=0.0, solid=True):
    """An iron-banded crate heaped with fish on ice (content: m9_fish_heap, m9_salmon_heap, m9_crab_heap)."""
    return ml.crate(bone, name, foot, size=size, yaw=yaw, content=content, solid=solid)


# ================================================================ net, seaweed, ropes
def net_swag(bone, name, a, b, depth=0.6, top_sag=0.08, nx=4, bulge=0.06, rope_d=0.045):
    """A fishing net hung in a festoon between the points a and b (under the eave): the cut-out mesh sagging between
    them, deepest in the middle, a thick rope along its bottom edge."""
    a, b = v3(*a), v3(*b)
    side = norm(b - a)
    out = norm(np.cross(side, UP))
    if out[2] < 0:
        out = -out

    def top(s):
        return a + (b - a) * s - UP * (top_sag * math.sin(math.pi * s))

    def dep(s):
        return 0.06 + depth * math.sin(math.pi * s) ** 0.85

    def P(s, t):
        return top(s) - UP * (dep(s) * t) + out * (bulge * math.sin(math.pi * s) * math.sin(math.pi * t * 0.7))
    loft(bone, name, P, nx, 1, "m9_net", th=0.006, u_hint=side, v_hint=-UP)
    pts = [P(k / nx, 1.0) for k in range(nx + 1)]
    for k in range(nx):
        beam(bone, "%s_rope_%d" % (name, k), pts[k], pts[k + 1], rope_d, "rope", extend=rope_d * 0.5)


def hanging_net(bone, name, top, w, h, normal=(0, 0, 1)):
    """A net hanging straight (draped over a post or a side beam)."""
    top = v3(*top)
    return ml.plate(bone, name, top - UP * h / 2, w, h, "m9_net", normal=normal, th=0.006)


def seaweed(bone, name, top, length=0.6, width=0.25, normal=(0, 0, 1)):
    """A strip of seaweed hanging from `top` (a crate's edge, a post), facing `normal`."""
    top = v3(*top)
    return ml.plate(bone, name, top - UP * length / 2, width, length, "m9_kelp", normal=normal, th=0.004)


def rope_wrap(bone, name, x, z, y, side=0.4, h=0.14):
    """A few turns of rope wound round a squared post (a band slightly wider than the post)."""
    add_cube(bone, name, (x, y, z), EYE, (side + 0.06, h, side + 0.06), "rope", stretch=False)


def rope_coil(bone, name, foot, r=0.22, h=0.12):
    """A coiled rope lying on the ground / a crate."""
    foot = v3(*foot)
    wb.octo(bone, name, foot, r, h, {"all": "rope"}, stretch=False)
    add_cube(bone, name + "_hole", foot + UP * (h + 0.002), EYE, (r * 0.7, 0.004, r * 0.7), "wood_dark")


# ================================================================ crabs, lobsters, the trap
def crab(bone, name, foot, s=0.2, yaw=0.0):
    """A red crab: the round shell, two claws held forward."""
    foot = v3(*foot)
    R = ry(yaw)
    add_cube(bone, name, foot + UP * s * 0.22, R, (s, s * 0.42, s * 0.78), {"all": "m9_shell_dark", "+2": "m9_shell"}, stretch=True)
    for k, sx in enumerate((-1, 1)):
        add_cube(bone, "%s_claw_%d" % (name, k), foot + R @ v3(sx * s * 0.42, s * 0.2, s * 0.5), R @ ry(sx * 0.4),
                 (s * 0.24, s * 0.26, s * 0.4), {"all": "m9_shell", "-2": "m9_shell_dark"}, stretch=True)


def lobster(bone, name, foot, L=0.5, yaw=0.0):
    """A red lobster lying flat: the carapace, the tail in two segments and the fan, two big claws forward."""
    foot = v3(*foot)
    R = ry(yaw)
    f = R @ X
    w = L * 0.26
    add_cube(bone, name, foot + f * (L * 0.12) + UP * w * 0.4, R, (L * 0.36, w * 0.8, w), {"all": "m9_shell", "-2": "m9_shell_dark"},
             stretch=True)
    add_cube(bone, name + "_tail", foot - f * (L * 0.18) + UP * w * 0.32, R, (L * 0.3, w * 0.62, w * 0.82), "m9_shell", stretch=True)
    add_cube(bone, name + "_fan", foot - f * (L * 0.38) + UP * w * 0.2, R, (L * 0.14, w * 0.3, w * 1.1), "m9_shell_dark", stretch=True)
    for k, sz in enumerate((-1, 1)):
        add_cube(bone, "%s_claw_%d" % (name, k), foot + f * (L * 0.45) + R @ Z * (sz * w * 0.65) + UP * w * 0.4, R @ ry(-sz * 0.35),
                 (L * 0.32, w * 0.55, w * 0.5), "m9_shell", stretch=True)


def lobster_trap(bone, det, name, foot, w=1.0, d=0.8, h=0.82, yaw=0.0, solid=True):
    """The lobster trap at the front: a wooden frame, its lower part a box of rope mesh, a rounded top of mesh over
    three rope hoops, the ends closed by half discs of mesh; a lobster inside."""
    foot = v3(*foot)
    R = ry(yaw)
    ax, az = R @ X, R @ Z
    hb = h * 0.42
    r = d / 2
    # the wooden frame: four sills, four corner posts
    for k, sz in enumerate((-1, 1)):
        beam(bone, "%s_sill_%d" % (name, k), foot - ax * (w / 2) + az * (sz * r) + UP * 0.03, foot + ax * (w / 2) + az * (sz * r) + UP * 0.03,
             0.06, "wood_dark", extend=0.03)
    for k, sx in enumerate((-1, 1)):
        beam(bone, "%s_end_%d" % (name, k), foot + ax * (sx * w / 2) - az * r + UP * 0.03, foot + ax * (sx * w / 2) + az * r + UP * 0.03,
             0.06, "wood_dark", extend=0.03)
    for k, (sx, sz) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        beam(det, "%s_post_%d" % (name, k), foot + ax * (sx * w / 2) + az * (sz * r), foot + ax * (sx * w / 2) + az * (sz * r) + UP * hb,
             0.05, "wood")
    # the mesh sides of the lower box
    for k, sz in enumerate((-1, 1)):
        ml.plate(bone, "%s_side_%d" % (name, k), foot + az * (sz * r) + UP * (hb / 2), w, hb, "m9_net", normal=az * sz, th=0.006)
    for k, sx in enumerate((-1, 1)):
        ml.plate(bone, "%s_endnet_%d" % (name, k), foot + ax * (sx * w / 2) + UP * (hb / 2), d, hb, "m9_net", normal=ax * sx, th=0.006)
        ml.plate(bone, "%s_arch_%d" % (name, k), foot + ax * (sx * w / 2) + UP * (hb + (h - hb) / 2), d, h - hb, "m9_net_arch",
                 normal=ax * sx, th=0.006)
    # the rounded top: mesh over the arc (half an ellipse from the front sill to the back one), three rope hoops
    rh = h - hb
    base = foot + UP * hb

    def P(s, t):
        a = math.pi * t
        return base - ax * (w / 2) + ax * (w * s) + az * (r * math.cos(a)) + UP * (rh * math.sin(a))
    loft(bone, name + "_dome", P, 1, 4, "m9_net", th=0.006, u_hint=ax, v_hint=-az)
    for j, s in enumerate((0.02, 0.5, 0.98)):
        pts = [P(s, k / 3) for k in range(4)]
        for k in range(3):
            beam(det, "%s_hoop_%d_%d" % (name, j, k), pts[k], pts[k + 1], 0.04, "rope", extend=0.02)
    beam(det, name + "_ridge", P(0, 0.5) + UP * 0.01, P(1, 0.5) + UP * 0.01, 0.04, "rope", extend=0.02)
    lobster(det, name + "_lobster", foot + UP * 0.06 + ax * 0.05, L=w * 0.48, yaw=yaw + 0.3)
    if solid:
        ml.collide((foot[0] - max(w, d) / 2, foot[1], foot[2] - max(w, d) / 2, foot[0] + max(w, d) / 2, foot[1] + h, foot[2] + max(w, d) / 2))


# ================================================================ the anchor
def anchor(bone, det, name, crown, top, s=1.0, region="black_iron"):
    """An iron anchor leaning from its crown (on the ground) up to the ring at `top`: the shank, the stock across near
    the top, the ring, two arms curving up from the crown ending in flat flukes."""
    crown, top = v3(*crown), v3(*top)
    up = norm(top - crown)
    side = norm(np.cross(up, v3(0, 0, 1)) if abs(up[2]) < 0.9 else np.cross(up, X))
    if side[0] < 0:
        side = -side
    beam(bone, name + "_shank", crown, top - up * 0.12 * s, 0.1 * s, region, width=0.08 * s, up=np.cross(side, up), extend=0.03)
    # the stock: a bar across, near the top, at right angles to the arms
    out = norm(np.cross(side, up))
    st = top - up * 0.3 * s
    beam(bone, name + "_stock", st - side * 0.38 * s, st + side * 0.38 * s, 0.08 * s, "wood_dark", width=0.1 * s, up=up, extend=0.03)
    for k, sx in enumerate((-1, 1)):
        add_cube(det, "%s_stock_band_%d" % (name, k), st + side * (sx * 0.12 * s), EYE, (0.1 * s, 0.12 * s, 0.12 * s), region)
    # the ring: four short bars in a diamond above the shank
    rc = top - up * 0.02 * s
    rr = 0.13 * s
    pts = [rc + up * rr, rc + out * rr, rc - up * rr, rc - out * rr]
    for k in range(4):
        beam(det, "%s_ring_%d" % (name, k), pts[k], pts[(k + 1) % 4], 0.035 * s, region, extend=0.02)
    # the arms and their flukes
    for k, sx in enumerate((-1, 1)):
        a0 = crown + side * (sx * 0.04 * s)
        a1 = crown + side * (sx * 0.32 * s) + up * 0.06 * s
        a2 = crown + side * (sx * 0.52 * s) + up * 0.3 * s
        a3 = crown + side * (sx * 0.6 * s) + up * 0.52 * s
        beam(bone, "%s_arm_%d_0" % (name, k), a0, a1, 0.085 * s, region, width=0.075 * s, up=out, extend=0.03)
        beam(bone, "%s_arm_%d_1" % (name, k), a1, a2, 0.08 * s, region, width=0.07 * s, up=out, extend=0.03)
        beam(det, "%s_arm_%d_2" % (name, k), a2, a3, 0.06 * s, region, width=0.06 * s, up=out, extend=0.02)
        dv = norm(a3 - a1)
        Rf = np.column_stack([np.cross(dv, out), dv, out])
        add_cube(bone, "%s_fluke_%d" % (name, k), a2 + dv * 0.02 * s + side * (sx * 0.02 * s), Rf, (0.24 * s, 0.26 * s, 0.035 * s), region)
    add_cube(bone, name + "_crown", crown + up * 0.02 * s, np.column_stack([side, up, out]), (0.16 * s, 0.1 * s, 0.1 * s), region)


# ================================================================ counter things
def salmon_steak(bone, name, foot, w=0.4, d=0.26, th=0.08, yaw=0.0):
    """A thick salmon steak lying flat (the orange cut face with its white lines up, silver skin round it)."""
    foot = v3(*foot)
    add_cube(bone, name, foot + UP * th / 2, ry(yaw), (w, th, d), {"all": "m9_body_silver", "+2": "m9_salmon_flesh", "-2": "m9_salmon_flesh"},
             stretch=True)


def price_sign(bone, name, foot, h=0.36, w=0.24, yaw=0.0):
    """A little wooden price board on a stick stuck in the ice."""
    foot = v3(*foot)
    R = ry(yaw)
    add_cube(bone, name + "_stick", foot + UP * h / 2, R, (0.025, h, 0.025), "wood_dark")
    add_cube(bone, name, foot + UP * (h + 0.05), R, (w, 0.13, 0.025), {"all": "wood_dark", "+3": "m9_sign", "-3": "m9_sign"}, stretch=True)


def green_jar(bone, name, foot, r=0.09, h=0.22):
    """A green glass jar with a cork lid."""
    foot = v3(*foot)
    wb.octo(bone, name, foot, r, h, {"all": "m9_jar_green", "+2": "jar_top"}, stretch=True)
    add_cube(bone, name + "_lid", foot + UP * (h + 0.02), EYE, (r * 1.3, 0.04, r * 1.3), "cork", stretch=True)


def potted_plant(bone, name, foot, r=0.1, h=0.16, plant="sprout"):
    """A small clay pot with a green plant (the pots on the barrel at the left)."""
    foot = v3(*foot)
    wb.octo(bone, name, foot, r, h, {"all": "pot_clay", "+2": "soil"}, stretch=True)
    ml.crossed(bone, name + "_plant", foot + UP * (h + 0.12), r * 2.4, 0.26, plant)
