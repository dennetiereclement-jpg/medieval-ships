"""Props of the archery merchant's and the mage merchant's tents (agent M5, 1.15.0): tente_archer, tente_mage.

The shell (posts, roof, valance, flag, banner, lanterns, rug, counters, shelves) comes from merchantlib.pavilion; this
module adds the atlas regions these two tents need (atlas.add; names "m5_...", plus the crystal / page / book painters
of props_m1, reused as they are) and the geometry of their goods:

    import props_m5 as pm
    pm.add_regions(atlas, pm.ARCHER_REGIONS)          # or pm.MAGE_REGIONS
    archery: pm.bow, pm.crossbow, pm.arrow_bunch, pm.arrow_bundle, pm.quiver, pm.target_easel, pm.bow_wall,
             pm.arrow_box
    magic:   pm.staff, pm.orb_stand, pm.grimoire, pm.lectern_book, pm.chest, pm.hanging_flask, pm.crystal_pendant,
             pm.wands

Coordinates: tent-local blocks (y up, +z = the open front). Cubes named "glow..." are drawn full bright (the crystals,
the orb, the potions: no particles).
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402
import props_m1 as p1  # noqa: E402  (painters only: crystals, pages, books, glass, cork)

_rgb, _jitter, _mix, _scale = ml._rgb, ml._jitter, ml._mix, ml._scale
v3, norm, add_cube, beam = ml.v3, ml.norm, ml.add_cube, ml.beam
box, plate, octo, collide = ml.box, ml.plate, ml.octo, ml.collide
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ry, rx, rz = ml.ry, ml.rx, ml.rz
CLEAR = (0, 0, 0, 0)

RED, CREAM = _rgb("b42e28"), _rgb("ece0c2")
STRAW, STRAW_D, STRAW_L = _rgb("c9a466"), _rgb("8a6834"), _rgb("e0c488")
GOLD, GOLD_D = _rgb("e0b048"), _rgb("8a6418")


# ================================================================ painters (img = the region, w x h RGBA)
def _put(px, x, y, c, a=255):
    px[x, y] = tuple(int(max(0, min(255, k))) for k in c[:3]) + (a,)


def _straw_px(d, ang, R, rng):
    """Coiled straw (the archery target): rings of rope every ~2.4 px, radial stitches every 20 degrees."""
    s = (d * R) % 2.4
    c = STRAW if s > 0.9 else (STRAW_L if s > 0.45 else STRAW_D)
    if abs(((ang / (2 * math.pi)) * 18) % 1.0 - 0.5) < 0.05:
        c = _scale(c, 0.78)
    return _jitter(c, rng, 7)


def _target_face(img):
    """The front of the round target: straw rim, then red / cream / red / cream / red bull's-eye; cut out round."""
    w, h = img.size
    px = img.load()
    rng = random.Random(501)
    cx, cy, R = (w - 1) / 2, (h - 1) / 2, w / 2 - 0.4
    bands = ((0.19, RED), (0.335, CREAM), (0.48, RED), (0.625, CREAM), (0.77, RED), (1.0, None))
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - cy) / R
            if d > 1.0:
                px[x, y] = CLEAR
                continue
            ang = math.atan2(y - cy, x - cx)
            for k, (r, c) in enumerate(bands):
                if d <= r:
                    break
            if c is None:
                c = _straw_px(d, ang, R, rng)
            else:
                c = _jitter(c, rng, 6)
                # soft light from the top left, a dark hairline at each ring's outer edge
                c = _scale(c, 1.0 + 0.08 * (-(x - cx) - (y - cy)) / R)
                if (r - d) * R < 0.9:
                    c = _scale(c, 0.7)
            if d > 0.985:
                c = _scale(c, 0.75)
            _put(px, x, y, c)


def _target_back(img):
    w, h = img.size
    px = img.load()
    rng = random.Random(502)
    cx, cy, R = (w - 1) / 2, (h - 1) / 2, w / 2 - 0.4
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - cy) / R
            if d > 1.0:
                px[x, y] = CLEAR
            else:
                _put(px, x, y, _scale(_straw_px(d, math.atan2(y - cy, x - cx), R, rng), 0.9))


def _arrows(fan=True, n=9, seed=0, heads=False):
    """A bunch of arrows (cut-out): pale shafts, white fletching at the top, dark nocks; fan = the tops spread out
    from a narrow foot (in a quiver / a box), else parallel with steel heads at the bottom (a bundle)."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        for y in range(h):
            for x in range(w):
                px[x, y] = CLEAR
        order = list(range(n))
        for i in order:
            if fan:
                xt = 2.5 + (i + 0.5) / n * (w - 5) + rng.uniform(-0.8, 0.8)
                xb = w / 2 + (xt - w / 2) * 0.25
            else:
                xt = xb = 1.5 + (i + 0.5) / n * (w - 3)
            yt = rng.randint(0, 3) if fan else rng.randint(0, 1)
            fl = max(6, int(h * 0.24))
            for y in range(yt, h):
                t = (y - yt) / max(1, h - 1 - yt)
                x = int(round(xt + (xb - xt) * t))
                if y < yt + 2:
                    _put(px, x, y, _rgb("4a3420"))
                elif y < yt + fl:
                    # fletching: three white vanes round the shaft, a grey stripe across
                    k = y - yt
                    half = 1 if (k < 4 or k > fl - 2) else 2
                    grey = (k == fl // 2)
                    for dx in range(-half, half + 1):
                        if 0 <= x + dx < w:
                            c = _rgb("f4f0e6") if dx != 0 else _rgb("d8d2c4")
                            if grey:
                                c = _rgb("9a8a7a") if i % 2 else _rgb("b0402e")
                            _put(px, x + dx, y, _jitter(c, rng, 6))
                elif heads and y >= h - 4:
                    half = 0 if y == h - 1 else 1
                    for dx in range(-half, half + 1):
                        if 0 <= x + dx < w:
                            _put(px, x + dx, y, _jitter(_rgb("a8acb4") if dx <= 0 else _rgb("6a6e76"), rng, 5))
                else:
                    if 0 <= x < w:
                        _put(px, x, y, _jitter(_rgb("c49a5e"), rng, 8))
    return p


def _honey_wood(seed=0, base="c08a44", dark="6a4418"):
    """Polished light wood (bows, staves): long streaks of grain along u, a sheen band."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        px = img.load()
        b, d = _rgb(base), _rgb(dark)
        rows = [rng.uniform(0, 1) for _ in range(h)]
        for y in range(h):
            for x in range(w):
                c = _mix(b, d, 0.25 * rows[y] + 0.12 * math.sin(x * 0.7 + y * 2.1))
                if y == h // 3:
                    c = _scale(c, 1.15)
                _put(px, x, y, _jitter(c, rng, 5))
    return p


def _plain(color, noise=6, seed=0):
    def p(img):
        rng = random.Random(seed)
        px = img.load()
        for y in range(img.height):
            for x in range(img.width):
                _put(px, x, y, _jitter(_rgb(color), rng, noise))
    return p


def _orb(img):
    """The glowing orb: violet, a bright core at the upper left, pale swirls."""
    w, h = img.size
    px = img.load()
    rng = random.Random(503)
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - w * 0.38, y - h * 0.36) / w
            c = _mix(_rgb("f0d8ff"), _rgb("8a3ad8"), min(1.0, d * 1.9))
            if abs(math.sin((x + y * 0.6) * 0.55 + d * 6)) > 0.93:
                c = _mix(c, (255, 255, 255), 0.45)
            _put(px, x, y, _jitter(c, rng, 5))


def _star(d, cx, cy, r_out, r_in, n, fill, outline=None, rot=-math.pi / 2):
    pts = []
    for k in range(2 * n):
        r = r_out if k % 2 == 0 else r_in
        a = rot + math.pi * k / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=fill, outline=outline)


def _grimoire(img):
    """The grimoire's cover: purple leather, a gold frame with corner pieces, a gold circle round an eight-pointed star."""
    from PIL import Image, ImageDraw
    w, h = img.size
    rng = random.Random(504)
    px = img.load()
    for y in range(h):
        for x in range(w):
            _put(px, x, y, _jitter(_mix(_rgb("5c2a86"), _rgb("3a1858"), 0.3 * (y / h) + 0.15 * ((x * 7 + y * 3) % 5) / 5), rng, 5))
    S = 4
    im = Image.new("RGBA", (w * S, h * S), CLEAR)
    d = ImageDraw.Draw(im)
    lw = S
    d.rectangle([2 * S, 2 * S, (w - 2) * S - 1, (h - 2) * S - 1], outline=GOLD + (255,), width=lw)
    for (x, y) in ((2, 2), (w - 6, 2), (2, h - 6), (w - 6, h - 6)):
        d.rectangle([x * S, y * S, (x + 4) * S, (y + 4) * S], fill=GOLD + (255,))
    cx, cy, r = w * S / 2, h * S / 2, min(w, h) * S * 0.33
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GOLD + (255,), width=lw)
    _star(d, cx, cy, r * 0.86, r * 0.36, 8, GOLD + (255,))
    d.ellipse([cx - r * 0.16, cy - r * 0.16, cx + r * 0.16, cy + r * 0.16], fill=_rgb("c070ff") + (255,))
    im = im.resize((w, h), Image.LANCZOS)
    base = img.copy()
    base.alpha_composite(im)
    img.paste(base, (0, 0))


def _chest(part):
    """Chest sides: dark planks along u, iron bands at the ends; the front has a gold lock plate; the lid's top."""
    def p(img):
        rng = random.Random(505 + len(part))
        w, h = img.size
        px = img.load()
        for y in range(h):
            plank = y // 5
            tone = 0.9 + 0.12 * ((plank * 37) % 5) / 5
            for x in range(w):
                c = _scale(_rgb("7a4e2a"), tone + 0.06 * math.sin(x * 0.5 + plank))
                if y % 5 == 4:
                    c = _scale(c, 0.7)
                if x < 3 or x >= w - 3 or (part == "top" and (x in (w // 3, 2 * w // 3))):
                    c = _rgb("4a4a52") if (x + y) % 7 else _rgb("8a8a92")
                if (part != "top") and (y < 2 or y >= h - 2):
                    c = _rgb("44444c")
                _put(px, x, y, _jitter(c, rng, 6))
        if part == "front":
            for y in range(1, 8):
                for x in range(w // 2 - 3, w // 2 + 3):
                    c = GOLD if (x, y) != (w // 2, 5) else _rgb("2a1a0a")
                    _put(px, x, y, _jitter(c, rng, 8))
    return p


def _leather_band(img):
    """Quiver leather: brown, a stitched seam, a darker band near the top."""
    w, h = img.size
    px = img.load()
    rng = random.Random(506)
    for y in range(h):
        for x in range(w):
            c = _rgb("7a4a26")
            if y < 3:
                c = _rgb("4a2c14")
            if x == w // 2 and y % 3 == 0:
                c = _rgb("d8c090")
            _put(px, x, y, _jitter(c, rng, 7))


PAINTERS = {
    "m5_target": (64, 64, _target_face),
    "m5_target_back": (32, 32, _target_back),
    "m5_arrows": (32, 48, _arrows(fan=True, n=9, seed=11)),
    "m5_arrows_flat": (16, 64, _arrows(fan=False, n=6, seed=12, heads=True)),
    "m5_bow": (16, 16, _honey_wood(seed=13, base="d49a4c", dark="7a5020")),
    "m5_string": (4, 4, _plain("e8e0c8", 5, 14)),
    "m5_quiver": (16, 32, _leather_band),
    "m5_orb": (16, 16, _orb),
    "m5_grimoire": (32, 40, _grimoire),
    "m5_chest_side": (32, 16, _chest("side")),
    "m5_chest_front": (32, 16, _chest("front")),
    "m5_chest_top": (32, 16, _chest("top")),
    "crystal_blue": (8, 16, p1._ws(p1.wt._crystal, _rgb("4a8cf0"), seed=507)),
    "crystal_violet": (8, 16, p1._ws(p1.wt._crystal, _rgb("8a5cf0"), seed=508)),
}

ARCHER_REGIONS = ["m5_target", "m5_target_back", "m5_arrows", "m5_arrows_flat", "m5_bow", "m5_string", "m5_quiver"]
MAGE_REGIONS = ["m5_orb", "m5_grimoire", "m5_chest_side", "m5_chest_front", "m5_chest_top", "crystal_blue", "crystal_violet",
                "crystal_purple", "pages", "book_top", "book_purple", "book_blue", "book_red", "book_brown", "parchment", "wax",
                "m5_string", "m5_bow"]


def add_regions(atlas, names):
    """Adds the named regions (ours, else props_m1's) to the tent's atlas, skipping the shell's own."""
    for n in names:
        if n in atlas.regions and n not in atlas.painters:
            continue
        if n in PAINTERS:
            w, h, painter = PAINTERS[n]
            atlas.add(n, w, h, painter)
        else:
            p1.add_regions(atlas, [n])


# ================================================================ archery
def _frame(up, facing):
    d = norm(v3(*up))
    f = v3(*facing)
    f = norm(f - np.dot(f, d) * d)
    return d, f, np.cross(d, f)


def bow(bone, name, center, up=(0, 1, 0), facing=(1, 0, 0), length=1.4, wood="m5_bow", grip="leather_dark",
        string="m5_string", th=0.045):
    """A strung recurve bow, its grip at `center`, along `up`, the belly (away from the string) towards `facing`:
    seven limb pieces (the tips curling forward again) and a straight string. 8 cubes."""
    c = v3(*center)
    d, f, s = _frame(up, facing)
    L = length
    prof = ((-1.0, 0.09), (-0.8, 0.035), (-0.48, 0.1), (-0.13, 0.15), (0.13, 0.15), (0.48, 0.1), (0.8, 0.035), (1.0, 0.09))
    P = [c + d * (t * L / 2) + f * ((o - 0.15) * L) for t, o in prof]
    for i in range(len(P) - 1):
        g = i == 3
        beam(bone, "%s_%d" % (name, i), P[i], P[i + 1], th * (1.5 if g else 1.0), grip if g else wood,
             width=th * (1.5 if g else 1.25), up=f, extend=0.014)
    a = c + d * (-0.84 * L / 2) + f * ((0.045 - 0.15) * L)
    b = c + d * (0.84 * L / 2) + f * ((0.045 - 0.15) * L)
    beam(bone, name + "_string", a, b, 0.014, string, width=0.014, up=f)


def crossbow(bone, name, butt, forward, up=(0, 1, 0), length=0.72, prod=0.66, wood="wood_dark", prod_region="m5_bow",
             string="m5_string"):
    """A crossbow from the butt of its stock along `forward`, `up` = the rail's side: stock, a bent prod across the
    front, the drawn string in a V back to the nut, a stirrup. 8 cubes."""
    b = v3(*butt)
    fw, u, s = _frame(forward, up)          # fw along the stock, u up from the rail
    beam(bone, name + "_butt", b, b + fw * 0.3, 0.1, wood, width=0.075, up=u)
    beam(bone, name + "_rail", b + fw * 0.28, b + fw * length, 0.065, wood, width=0.06, up=u)
    front = b + fw * (length - 0.07) + u * 0.02
    half = prod / 2
    pts = [front - s * half - fw * 0.13, front - s * half * 0.42, front + s * half * 0.42, front + s * half - fw * 0.13]
    for i in range(3):
        beam(bone, "%s_prod_%d" % (name, i), pts[i], pts[i + 1], 0.045, prod_region, width=0.05, up=u, extend=0.015)
    nut = b + fw * (length * 0.42) + u * 0.04
    for i, tip in enumerate((pts[0], pts[3])):
        beam(bone, "%s_string_%d" % (name, i), tip, nut, 0.014, string, width=0.014, up=u)
    add_cube(bone, name + "_stirrup", b + fw * (length + 0.04), np.column_stack([s, u, fw]), (0.13, 0.02, 0.1), "iron")


def arrow_bunch(bone, name, foot, h=0.8, w=0.42, planes=3, yaw=0.0, up=(0, 1, 0), region="m5_arrows"):
    """Arrows standing in a quiver / a box: `planes` cut-out planes turned about the axis (the fan of shafts and white
    fletching), their foot at `foot`."""
    foot = v3(*foot)
    d = norm(v3(*up))
    ref = X if abs(d[0]) < 0.9 else Z
    for k in range(planes):
        a = yaw + math.pi * k / planes
        e0 = norm(np.cross(d, ref))
        e1 = np.cross(e0, d)
        u = e0 * math.cos(a) + e1 * math.sin(a)
        n = np.cross(u, d)
        add_cube(bone, "%s_%d" % (name, k), foot + d * (h / 2), np.column_stack([u, d, n]), (w, h, 0.004),
                 {"all": None, "+3": region, "-3": region}, stretch=True, u_dir=u, v_dir=-d)


def arrow_bundle(bone, name, center, axis, length=0.8, w=0.16, region="m5_arrows_flat"):
    """A bundle of arrows lying along `axis` (fletching at the +axis end), tied in the middle. 3 cubes."""
    c = v3(*center)
    a = norm(v3(*axis))
    side = norm(np.cross(UP, a))
    plate(bone, name + "_0", c + UP * 0.03, w, length, region, normal=UP, up=a, th=0.004)
    plate(bone, name + "_1", c + UP * 0.05, w * 0.7, length, region, normal=side, up=a, th=0.004)
    add_cube(bone, name + "_tie", c + UP * 0.045, np.column_stack([a, UP, side]), (0.04, 0.08, w * 0.6), "rope")


def quiver(bone, name, foot, h=0.72, r=0.12, up=(0, 1, 0), arrows=0.42, region="m5_quiver", strap=True):
    """A leather quiver standing / leaning from `foot` along `up`, full of arrows (white fletching). 5-6 cubes."""
    foot = v3(*foot)
    d = norm(v3(*up))
    beam(bone, name, foot, foot + d * h, 2 * r, {"all": region, "+1": "leather_dark", "-1": "leather_dark"}, width=2 * r,
         up=X if abs(d[0]) < 0.9 else Z, stretch=True)
    add_cube(bone, name + "_rim", foot + d * (h - 0.03), np.column_stack([norm(np.cross(d, Z if abs(d[2]) < 0.9 else X)), d,
             np.cross(norm(np.cross(d, Z if abs(d[2]) < 0.9 else X)), d)]), (2 * r + 0.03, 0.06, 2 * r + 0.03), "brass")
    arrow_bunch(bone, name + "_arrows", foot + d * (h - 0.25), h=arrows + 0.25, w=2 * r * 1.9, planes=2, up=d, yaw=0.4)
    if strap:
        side = norm(np.cross(d, Z if abs(d[2]) < 0.9 else X))
        beam(bone, name + "_strap", foot + d * 0.12 + side * (r + 0.01), foot + d * (h - 0.08) + side * (r + 0.01), 0.025, "leather_dark",
             width=0.06, up=side)


def arrow_box(bone, det, name, foot, size=(0.6, 0.45, 0.5), arrows=0.8, yaw=0.0, solid=True, planes=3):
    """A wooden box (crate) of arrows: the fan of white-fletched arrows rising from it."""
    foot = v3(*foot)
    ml.crate(bone, name, foot, size=size, yaw=yaw, solid=solid)
    arrow_bunch(det, name + "_arrows", foot + UP * (size[1] - 0.2), h=arrows + 0.2, w=max(size[0], size[2]) * 1.15,
                planes=planes, yaw=yaw + 0.2)


def target_easel(bone, det, name, foot, yaw=0.0, r=0.72, th=0.2, h=1.28, lean=0.14, solid=True):
    """The round straw training target (painted rings) on a wooden A-frame easel: `foot` = the ground point under the
    target's centre, the face towards ry(yaw) * (+z), leaning back by `lean`. 19 cubes."""
    foot = v3(*foot)
    n0, s = ry(yaw) @ Z, ry(yaw) @ X
    n = n0 * math.cos(lean) + UP * math.sin(lean)
    up = UP * math.cos(lean) - n0 * math.sin(lean)
    c = foot + UP * h
    plate(bone, name + "_face", c + n * (th / 2 + 0.006), 2 * r, 2 * r, "m5_target", normal=n, up=up, th=0.008)
    plate(bone, name + "_back", c - n * (th / 2 + 0.006), 2 * r, 2 * r, "m5_target_back", normal=-n, up=up, th=0.008)
    seg = 2 * r * math.tan(math.pi / 12)
    for k in range(12):
        a = 2 * math.pi * k / 12
        e = s * math.cos(a) + up * math.sin(a)
        t = -s * math.sin(a) + up * math.cos(a)
        add_cube(bone, "%s_rim_%d" % (name, k), c + e * (r - 0.05), np.column_stack([t, e, n]), (seg + 0.004, 0.1, th), "straw",
                 stretch=True)
    # the easel: two front legs behind the target, splayed, a back leg, the ledge it rests on, a low bar
    top = c + up * (r * 0.62) - n * (th / 2 + 0.05)
    legs = []
    for sgn in (-1, 1):
        g = foot + s * (sgn * 0.62) + n0 * 0.16
        t_ = top + s * (sgn * 0.16)
        beam(bone, "%s_leg_%d" % (name, (sgn + 1) // 2), g, t_ + (t_ - g) * 0.08, 0.085,
             {"all": "wood", "+1": "end_grain", "-1": "end_grain"}, up=n0)
        legs.append((g, t_))
    beam(bone, name + "_leg_back", top - n0 * 0.02 + UP * 0.08, foot - n0 * 0.78, 0.075, {"all": "wood_dark", "+1": "end_grain"}, up=s)

    def on_leg(k, y):
        g, t_ = legs[k]
        return g + (t_ - g) * ((y - g[1]) / (t_[1] - g[1]))
    yl = (c - up * r)[1] - 0.04
    pa, pb = on_leg(0, yl), on_leg(1, yl)
    mid = (pa + pb) / 2
    ledge_c = v3(mid[0], yl, mid[2]) + n0 * 0.06
    add_cube(bone, name + "_ledge", ledge_c, np.column_stack([s, UP, n0]), (np.linalg.norm(pb - pa) + 0.16, 0.07, th + 0.14), "wood_dark")
    pa, pb = on_leg(0, 0.42), on_leg(1, 0.42)
    beam(bone, name + "_bar", pa - s * 0.06, pb + s * 0.06, 0.06, "wood", width=0.05, up=UP)
    if solid:
        pts = [foot + s * 0.72 + n0 * 0.3, foot - s * 0.72 + n0 * 0.3, foot + s * 0.72 - n0 * 0.82, foot - s * 0.72 - n0 * 0.82]
        xs, zs = [p[0] for p in pts], [p[2] for p in pts]
        collide((min(xs), 0.0, min(zs), max(xs), h + r * 0.95, max(zs)))


def bow_wall(bone, det, name, x0, x1, z, y1=3.05, rails=(0.98, 1.72, 2.5), uprights=5, solid=True):
    """The wooden display wall at the back: vertical dark planks, posts and three rails (the bows hang on them).
    Returns the z of its front face."""
    box(bone, name + "_planks", (x0, 0.0, z - 0.05), (x1, y1, z), "plank", u_dir=UP)
    for k in range(uprights):
        x = x0 + 0.07 + (x1 - x0 - 0.14) * k / (uprights - 1)
        box(bone, "%s_post_%d" % (name, k), (x - 0.07, 0.0, z), (x + 0.07, y1, z + 0.12), {"all": "wood_dark", "+2": "end_grain"})
    for k, y in enumerate(rails):
        box(bone, "%s_rail_%d" % (name, k), (x0, y - 0.06, z + 0.0), (x1, y + 0.06, z + 0.16), "wood_dark", u_dir=X)
    box(bone, name + "_cap", (x0 - 0.04, y1, z - 0.06), (x1 + 0.04, y1 + 0.1, z + 0.15), "wood_dark", u_dir=X)
    if solid:
        collide((x0, 0.0, z - 0.06, x1, y1, z + 0.16))
    return z + 0.16


def peg(bone, name, p, z_wall, size=0.05):
    p = v3(*p)
    box(bone, name, (p[0] - size / 2, p[1] - size / 2, z_wall), (p[0] + size / 2, p[1] + size / 2, p[2] + 0.04), "wood_dark")


# ================================================================ magic
def staff(bone, name, foot, top, head="purple", claws=True, crystal_h=0.3, crystal_w=0.12):
    """A mage staff from `foot` to `top`: dark wooden shaft, a gold collar, gold claws holding a glowing crystal
    (crystal_<head>): a long diamond (body, upper and lower points). 6-8 cubes."""
    foot, top = v3(*foot), v3(*top)
    d = norm(top - foot)
    side = norm(np.cross(d, Z if abs(d[2]) < 0.9 else X))
    beam(bone, name, foot, top, 0.08, {"all": "m5_bow", "+1": "end_grain", "-1": "end_grain"})
    beam(bone, name + "_grip", foot + (top - foot) * 0.55, foot + (top - foot) * 0.68, 0.1, "leather_dark")
    add_cube(bone, name + "_collar", top, np.column_stack([side, d, np.cross(side, d)]), (0.13, 0.08, 0.13), "gold")
    c0 = top + d * 0.06
    reg = {"all": "crystal_" + head}
    up45 = norm(side + np.cross(side, d))
    beam(bone, "glow_%s_low" % name, c0, c0 + d * crystal_h * 0.22, crystal_w * 0.6, reg, width=crystal_w * 0.6, up=up45, stretch=True)
    beam(bone, "glow_%s_body" % name, c0 + d * crystal_h * 0.2, c0 + d * crystal_h * 0.78, crystal_w, reg, width=crystal_w, up=up45,
         stretch=True)
    beam(bone, "glow_%s_tip" % name, c0 + d * crystal_h * 0.76, c0 + d * crystal_h * 1.05, crystal_w * 0.5, reg, width=crystal_w * 0.5,
         up=up45, stretch=True)
    if claws:
        for k, sg in enumerate((-1, 1)):
            beam(bone, "%s_claw_%d" % (name, k), top + side * (sg * 0.05), c0 + d * crystal_h * 0.55 + side * (sg * (crystal_w * 0.66)),
                 0.032, "gold", width=0.032)


def orb_stand(bone, det, name, foot, h=1.3, r=0.2, solid=True):
    """The glowing orb on its stand: a turned wooden pedestal, a gold cup, the orb (three lit cubes turned against
    each other) in a gold armillary ring. ~17 cubes."""
    foot = v3(*foot)
    box(bone, name + "_base", (foot[0] - 0.24, 0.0, foot[2] - 0.24), (foot[0] + 0.24, 0.12, foot[2] + 0.24), {"all": "wood_dark", "+2": "end_grain"})
    octo(bone, name + "_column", foot + UP * 0.12, 0.09, h - 0.42, "wood")
    box(bone, name + "_knot", (foot[0] - 0.12, h * 0.45, foot[2] - 0.12), (foot[0] + 0.12, h * 0.45 + 0.1, foot[2] + 0.12), "wood_dark")
    cup_y = h - 0.3
    box(bone, name + "_plate", (foot[0] - 0.17, cup_y, foot[2] - 0.17), (foot[0] + 0.17, cup_y + 0.06, foot[2] + 0.17), "gold")
    oc = foot + UP * (cup_y + 0.06 + r)
    # a voxel sphere: three crossed boxes (long on x, y, z in turn), a little turned towards the front left
    for k, sz in enumerate(((2 * r, 1.3 * r, 1.3 * r), (1.3 * r, 2 * r, 1.3 * r), (1.3 * r, 1.3 * r, 2 * r))):
        add_cube(bone, "glow_%s_orb_%d" % (name, k), oc, ry(0.4), sz, "m5_orb", stretch=True)
    # gold ring round the orb (8 pieces, turned to face the front-left a little), 4 claws
    rr = r + 0.06
    a0 = 0.5
    s, n = ry(a0) @ X, ry(a0) @ Z
    for k in range(8):
        a = 2 * math.pi * k / 8
        e = s * math.cos(a) + UP * math.sin(a)
        t = -s * math.sin(a) + UP * math.cos(a)
        add_cube(det, "%s_ring_%d" % (name, k), oc + e * rr, np.column_stack([t, e, n]), (2 * rr * math.tan(math.pi / 8) + 0.01, 0.03, 0.035), "gold")
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        e = v3(math.cos(a), 0, math.sin(a))
        beam(det, "%s_claw_%d" % (name, k), foot + UP * (cup_y + 0.05) + e * 0.12, oc + e * (r * 0.75) - UP * (r * 0.1), 0.03, "gold")
    if solid:
        collide((foot[0] - 0.25, 0.0, foot[2] - 0.25, foot[0] + 0.25, cup_y + 0.06 + 2 * r, foot[2] + 0.25))


def grimoire(bone, name, foot, yaw=0.0, w=0.46, h=0.6, th=0.12, lean=0.42):
    """A big closed grimoire propped up (leaning back by `lean`), its cover (m5_grimoire) towards ry(yaw)*(+z), on a
    small wooden wedge. 3 cubes."""
    foot = v3(*foot)
    R = ry(yaw) @ rx(-lean)
    c = foot + R @ v3(0, h / 2, 0) + ry(yaw) @ v3(0, 0, -0.02)
    add_cube(bone, name, c, R, (w, h, th), {"all": "book_top", "+3": "m5_grimoire", "-3": "book_purple", "-1": "book_purple"},
             stretch=True)
    add_cube(bone, name + "_clasp", c + R @ v3(w / 2 + 0.01, 0, 0), R, (0.03, 0.1, th + 0.02), "gold")
    back = foot + ry(yaw) @ v3(0, 0, -(h * math.sin(lean)) - 0.04)
    add_cube(bone, name + "_wedge", back + UP * 0.08, ry(yaw), (w * 0.6, 0.16, 0.18), "wood_dark")


def lectern_book(bone, name, foot, yaw=0.0, w=0.62, d=0.42, h=0.2, tilt=0.38, cover="book_brown"):
    """A small slanted wooden book rest on a counter and an open book on it (pages towards ry(yaw)*(+z)). 5 cubes."""
    foot = v3(*foot)
    R = ry(yaw)
    add_cube(bone, name + "_rest", foot + R @ v3(0, h / 2, -0.06), R, (w * 0.75, h, d * 0.5), "wood_dark")
    add_cube(bone, name + "_lip", foot + R @ v3(0, 0.04, d * 0.42), R, (w * 0.8, 0.06, 0.05), "wood_dark")
    p1.wb.open_book(bone, name, foot + UP * (h * 0.45), w=w, d=d, yaw=yaw, cover=cover, glow=False, tilt=tilt, lift=0.0)


def chest(bone, name, foot, w=0.85, h=0.62, d=0.55, yaw=0.0, solid=True):
    """An iron-banded wooden chest with a gold lock, its front towards ry(yaw)*(+z): body, lid, rounded top, two
    straps. 5 cubes."""
    foot = v3(*foot)
    R = ry(yaw)
    hb = h * 0.62
    add_cube(bone, name, foot + UP * (hb / 2), R, (w, hb, d), {"all": "m5_chest_side", "+3": "m5_chest_front", "+2": "m5_chest_top",
                                                                "-2": "m5_chest_top"}, stretch=True)
    add_cube(bone, name + "_lid", foot + UP * (hb + (h - hb) * 0.35), R, (w + 0.03, (h - hb) * 0.7, d + 0.03),
             {"all": "m5_chest_side", "+2": "m5_chest_top"}, stretch=True)
    add_cube(bone, name + "_lid_top", foot + UP * (h - (h - hb) * 0.15), R, (w + 0.02, (h - hb) * 0.3, d * 0.7),
             {"all": "m5_chest_top"}, stretch=True)
    for s in (-1, 1):
        add_cube(bone, "%s_strap_%d" % (name, (s + 1) // 2), foot + R @ v3(s * w * 0.3, h / 2 + 0.005, 0), R, (0.05, h + 0.02, d + 0.05),
                 "iron")
    if solid:
        ex = abs(math.cos(yaw)) * w / 2 + abs(math.sin(yaw)) * d / 2
        ez = abs(math.sin(yaw)) * w / 2 + abs(math.cos(yaw)) * d / 2
        collide((foot[0] - ex, 0.0, foot[2] - ez, foot[0] + ex, foot[1] + h, foot[2] + ez))


def hanging_flask(bone, name, top, colour="purple", drop=0.3, r=0.08, h=0.17, shape="round"):
    """A potion bottle hanging from `top` by a string round its neck (lit)."""
    top = v3(*top)
    neck = top - UP * drop
    beam(bone, name + "_string", top, neck + UP * 0.02, 0.015, "rope")
    ml.bottle(bone, name, neck - UP * (h + 0.07), colour=colour, r=r, h=h, neck_h=0.07, shape=shape, glow=True, cork=True)


def crystal_pendant(bone, name, top, colour="purple", drop=0.28, w=0.1, hh=0.24):
    """A crystal hanging on a string (a lit diamond: two points)."""
    top = v3(*top)
    c = top - UP * (drop + hh / 2)
    beam(bone, name + "_string", top, c + UP * hh / 2, 0.015, "rope")
    reg = {"all": "crystal_" + colour}
    up45 = v3(1, 0, 1)
    beam(bone, "glow_%s_a" % name, c + UP * (hh / 2), c - UP * 0.02, w, reg, width=w, up=up45, stretch=True)
    beam(bone, "glow_%s_b" % name, c, c - UP * (hh / 2), w * 0.55, reg, width=w * 0.55, up=up45, stretch=True)


def wands(bone, name, foot, n=6, h=0.55, spread=0.13, seed=0, tips=("crystal_violet", "white", "crystal_blue")):
    """A bunch of wands standing in a barrel / a box from `foot` (fanning out a little), each with a small tip."""
    foot = v3(*foot)
    rng = random.Random(seed)
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.3, 0.3)
        e = v3(math.cos(a), 0, math.sin(a))
        b = foot + e * (spread * 0.4)
        t = foot + e * spread + UP * (h * rng.uniform(0.85, 1.1))
        beam(bone, "%s_%d" % (name, k), b, t, 0.035, "m5_bow" if k % 2 else "wood")
        tip = tips[k % len(tips)]
        add_cube(bone, ("glow_" if tip.startswith("crystal") else "") + "%s_tip_%d" % (name, k), t + norm(t - b) * 0.03, ry(a),
                 (0.05, 0.07, 0.05), tip)
