"""Shared atlas, props and export of the three medieval TRAINING AREAS (1.18.0): one block each, static, drawn like the
tents / carts / workshops / merchant tents from a .bbmodel (TentType JSON group "training", tab "Entraînement").

Built on tools/merchant/merchantlib.py (its shell atlas regions, barrel, crate, sword, bottle, shelf_unit, banner...)
and tools/tents/tentlib.py (Bone, beam, loft, canvas_panel, lantern, collide, Decor). Nothing of those files is
changed: the training paint code (floors, straw, punching bag, round shields, banners with crossed swords / lotus /
heraldic shield, awnings) lives here.

A generator (tools/training/generate_<id>.py) does, in this order:

    import traininglib as tr
    tr.setup("training_area_x")                       # resets collisions / uuids (call first)
    atlas = tr.Atlas("training_area_x", colour="red")  # merchantlib colour of the shell (red, blue, seablue, ...)
    A = tr.area("training_area_x", atlas)             # A.root, A.shell (big things), A.detail (bone "detail")
    floor = tr.floor_region(atlas, "floor", 7.0, 7.0, kind="earth")         # or kind="tatami" (border=, motif=)
    tr.floor(A.shell, "floor", -3.5, 3.5, -3.5, 3.5, floor)
    F = tr.fence_ring(A, -3.4, 3.4, -3.4, 3.4, entrance=("front", 1.4, 1.6), stone="corners")
    tr.dummy(A, "dummy_0", (x, 0, z), height=1.75, yaw=0.0)                 # helmet=True, sword="pos_x", shield="neg_x"
    tr.punching_bag(A, "bag", (x, 0, z))
    tr.sword_rack(A, "rack", (x0, 0, z), (x1, 0, z), normal=(0, 0, 1))
    roof, val = tr.awning_regions(atlas, "red")                             # or ("blue", stripe="beige")
    S = tr.awning(A, "stall", x0, x1, z0, z1, roof, val)
    ban = tr.banner_region(atlas, "red", "crossed_swords")                  # lotus, heraldic_shield
    tr.post_banner(A, "banner_0", F.posts["front_left"], ban, normal=(0, 0, 1))
    tr.lantern_post(A, "lamp_0", (x, 0, z))
    ... tr.barrel / tr.crate / tr.bench / tr.round_shield / tr.helmet / tr.staff / tr.wooden_sword / tr.flower_pot ...
    decor = tr.Decor(); decor.block("furnish:spruce_crate", x, y, z, facing="front", alt="minecraft:barrel")
    tr.export(A.root, "training_area_x", atlas, decor=decor, icon=dict(kind="dummy", colour="red"))

Coordinates: area-local blocks, y up (y = 0 = top of the ground block), +z = the FRONT (towards the player who
placed it), the anchor block's centre (0, 0, 0) = centre of the footprint. Small things go under A.detail (hidden
beyond 32 blocks). Budget: <= ~900 cubes per area.

Collisions: fence bays collide 1.5 high (like vanilla fences; the entrance gap stays free), posts, dummies, the
punching-bag frame, racks, benches, barrels, crates, awning posts. The floor plate (<= 0.05 thick) does NOT collide:
players walk on the real ground under it.

Atlas regions added to the merchantlib shell (every training atlas has them):
  t_straw (32x32, vertical stalks: dummy bodies), t_straw_end (16x16), t_straw_rope (16x16, straw wound with rope),
  t_bag (16x64, the punching bag: straw-canvas with rope bands), t_bag_end (16x16, leather), t_stone_brick (32x32,
  grey stone bricks), t_stone_cap (16x16), t_pale_wood (32x16, light training wood), t_shield_round (32x32, cut-out
  round shield: red and white rings, iron rim, painted boss), t_shield_back (32x32, cut-out round planks),
  t_flowers (32x32, cut-out pink flowers), t_jar (16x16, glazed ceramic), t_terracotta (16x16), t_rivet_wood
  (64x16, fence post wood with an iron band and rivets at the top).
On demand: floor_region (earth + stones, or tatami mats with a red border and a centre motif, painted at `ppb`
pixels per block so it maps 1:1), banner_region (colour + emblem crossed_swords / lotus / heraldic_shield, ragged
bottom), awning_regions (plain or striped roof + scalloped valance).
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
import merchantlib as ml  # noqa: E402

tl, gg, gn, cl = ml.tl, ml.gg, ml.gn, ml.cl
v3, norm, Bone, add_cube, beam, loft = ml.v3, ml.norm, ml.Bone, ml.add_cube, ml.beam, ml.loft
EYE, UP, X, Z = ml.EYE, ml.UP, ml.X, ml.Z
ASSETS, ROOT = ml.ASSETS, ml.ROOT
collide, collide_segment, rope, COLLIDERS = ml.collide, ml.collide_segment, ml.rope, ml.COLLIDERS
ry, rx, rz = ml.ry, ml.rx, ml.rz
_rgb, _jitter, _mix, _scale = ml._rgb, ml._jitter, ml._mix, ml._scale
fine_wood, hammered_iron, twisted_rope, polished_metal = ml.fine_wood, ml.hammered_iron, ml.twisted_rope, ml.polished_metal
COLOURS, BEIGE, GOLD, GOLD_DARK = ml.COLOURS, ml.BEIGE, ml.GOLD, ml.GOLD_DARK

# the merchantlib helpers re-exported (same signatures)
box, rbox, octo, plate, lantern, crossed = ml.box, ml.rbox, ml.octo, ml.plate, ml.lantern, ml.crossed
barrel, crate, sack, basket, bottle, sword, axe, spear = ml.barrel, ml.crate, ml.sack, ml.basket, ml.bottle, ml.sword, ml.axe, ml.spear
shelf_unit, counter, weapon_rack, hanging_bunch = ml.shelf_unit, ml.counter, ml.weapon_rack, ml.hanging_bunch
Decor = ml.Decor
GROUP = "training"

FENCE_H = 1.15          # top of a fence post (the rails at 0.38 and 0.86)
FENCE_COLLIDE_H = 1.5   # like vanilla fences: players use the entrance


def setup(name):
    """Resets the collision list, the uuids and the region tables for one area (call first)."""
    ml.setup(name)


def _seed(s):
    return sum((i + 1) * ord(c) for i, c in enumerate(s))


# ---------------------------------------------------------------- painters
def _px(img, x, y, c, a=255):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((int(x), int(y)), tuple(int(k) for k in c[:3]) + (a,))


def _full(img):
    return (0, 0, img.width, img.height)


def paint_straw(img, rng, base=_rgb("cfae5e"), dark=_rgb("8a6a2c"), light=_rgb("ead08a")):
    """Straw stalks running down (v), light and dark stalks, a few knots."""
    w, h = img.size
    for x in range(w):
        col = _jitter(_mix(base, light if rng.random() < 0.35 else dark, rng.random() * 0.35), rng, 6)
        off = rng.randint(0, 5)
        for y in range(h):
            k = 1.0 + 0.1 * math.sin((y + off) * 0.9) - (0.18 if (x + (y // 7)) % 4 == 0 else 0)
            _px(img, x, y, _jitter(_scale(col, k), rng, 4))
    for _ in range(w * h // 60):
        x, y = rng.randrange(w), rng.randrange(h)
        _px(img, x, y, _scale(dark, 0.9))


def paint_straw_end(img, rng):
    w, h = img.size
    for y in range(h):
        for x in range(w):
            c = _rgb("b8913e") if (x * 3 + y * 5) % 7 < 3 else _rgb("d9b968")
            _px(img, x, y, _jitter(c, rng, 10))


def paint_straw_rope(img, rng):
    paint_straw(img, rng)
    w, h = img.size
    for y in range(h):
        for x in range(w):
            t = (x + y * 2) % 8
            if t < 3:
                _px(img, x, y, _jitter(_rgb("a88a58") if t else _rgb("6e5634"), rng, 6))


def paint_bag(img, rng):
    """The punching bag: tan straw-canvas, vertical seams, three rope bands, darker top and bottom."""
    w, h = img.size
    ml.tt._weave(img, _full(img), _rgb("c4a26a"), rng, seams=0, patches=1, stains=2, tears=0, noise=5)
    for y in range(h):
        for x in range(w):
            if x % 8 == 0:
                _px(img, x, y, _rgb("8a6a3a"))
    for yc in (int(h * 0.12), int(h * 0.5), int(h * 0.86)):
        for y in range(yc - 2, yc + 3):
            for x in range(w):
                t = (x + y * 2) % 6
                _px(img, x, y, _jitter(_rgb("7a5e36") if t == 0 else _rgb("b09468"), rng, 6))
    for y in list(range(0, 3)) + list(range(h - 3, h)):
        for x in range(w):
            _px(img, x, y, _jitter(_rgb("5a3a20"), rng, 6))


def paint_leather(img, rng):
    w, h = img.size
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            _px(img, x, y, _jitter(_rgb("5a3a20") if e > 1 else _rgb("3a2412"), rng, 6))


def paint_stone_brick(img, rng):
    """Grey stone bricks (2 courses per 32 px), dark mortar, each brick its own tone, chipped corners."""
    w, h = img.size
    ch = max(4, h // 4)
    for row in range(0, h, ch):
        off = (row // ch % 2) * (w // 4)
        bw = w // 2
        for x0 in range(-bw, w + bw, bw):
            xs = x0 + off
            tone = _jitter(_rgb("8c8a86"), rng, 14)
            for y in range(row, min(h, row + ch)):
                for x in range(max(0, xs), min(w, xs + bw)):
                    if y == row + ch - 1 or x == xs + bw - 1:
                        _px(img, x, y, _jitter(_rgb("4a4846"), rng, 5))
                    else:
                        k = 1.08 if y == row else (0.86 if y == row + ch - 2 else 1.0)
                        _px(img, x, y, _jitter(_scale(tone, k), rng, 7))
    for _ in range(w * h // 40):
        _px(img, rng.randrange(w), rng.randrange(h), _jitter(_rgb("6e6c68"), rng, 6))
    for _ in range(w * h // 120):   # a little moss
        _px(img, rng.randrange(w), rng.randrange(h), _jitter(_rgb("5a6e3a"), rng, 8))


def paint_stone_cap(img, rng):
    w, h = img.size
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            _px(img, x, y, _jitter(_rgb("9a9894") if e > 0 else _rgb("5a5856"), rng, 9))


def paint_pale_wood(img, rng):
    fine_wood(img, _full(img), _rgb("b98c56"), _rgb("6e4a24"), img.height, rng, joints=False, knots=0.05, grain=0.1, shade=0.05)


def paint_post_wood(img, rng):
    """Fence post wood (grain along u) with an iron band and rivets at the u-end (the top of a post drawn with u up)."""
    fine_wood(img, _full(img), _rgb("7a5232"), _rgb("3a2412"), img.height, rng, joints=False, knots=0.12, grain=0.12, shade=0.08)
    w, h = img.size
    for x in range(w - 9, w - 3):
        for y in range(h):
            _px(img, x, y, _jitter(_rgb("4a4a50"), rng, 6))
    for y in (3, h - 4):
        _px(img, w - 6, y, _rgb("b4b6bc"))


def paint_round_shield(img, rng, rings=(_rgb("a42a24"), _rgb("e8e0cc"), _rgb("a42a24"), _rgb("e8e0cc")), rim=_rgb("6a6c72")):
    """A round shield seen from the front: concentric rings (outside first), an iron rim with rivets, the centre left
    for the boss (painted dark iron); cut-out outside the disc."""
    w, h = img.size
    cx, cy, R = (w - 1) / 2, (h - 1) / 2, w / 2
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - cy)
            if d > R - 0.3:
                _px(img, x, y, (0, 0, 0), 0)
                continue
            if d > R - 2.4:
                c = _scale(rim, 1.15 if (x + y) % 5 else 0.8)
            elif d < R * 0.2:
                c = _rgb("4a4a50") if d > R * 0.13 else _rgb("8a8c92")
            else:
                t = (d - R * 0.2) / (R - 2.4 - R * 0.2)
                k = min(len(rings) - 1, int((1 - t) * len(rings)))
                c = rings[k]
            _px(img, x, y, _jitter(c, rng, 7))
    for k in range(10):
        a = 2 * math.pi * k / 10
        _px(img, cx + math.cos(a) * (R - 1.3), cy + math.sin(a) * (R - 1.3), _rgb("c8cad0"))


def paint_shield_back(img, rng):
    w, h = img.size
    cx, cy, R = (w - 1) / 2, (h - 1) / 2, w / 2
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - cy)
            if d > R - 0.3:
                _px(img, x, y, (0, 0, 0), 0)
            elif d > R - 2.4:
                _px(img, x, y, _jitter(_rgb("5a5c62"), rng, 6))
            else:
                c = _rgb("8a6038") if (x // 5) % 2 else _rgb("74502c")
                if x % 5 == 0:
                    c = _rgb("4a301a")
                _px(img, x, y, _jitter(c, rng, 6))
    for y in range(int(cy) - 1, int(cy) + 2):
        for x in range(4, w - 4):
            if math.hypot(x - cx, y - cy) < R - 2.4:
                _px(img, x, y, _jitter(_rgb("4a2a16"), rng, 4))


def paint_flowers(img, rng, petals=(_rgb("e88ab8"), _rgb("f2a6c8"), _rgb("d0609a"))):
    """Cut-out bushy plant: green leaves at the bottom, pink blossoms above."""
    w, h = img.size
    for y in range(h):
        for x in range(w):
            _px(img, x, y, (0, 0, 0), 0)
    greens = [_rgb("3e7228"), _rgb("2e5a1e"), _rgb("4f8a32")]
    for _ in range(14):
        x = rng.uniform(4, w - 5)
        top = rng.uniform(h * 0.25, h * 0.6)
        for y in range(int(top), h):
            _px(img, x + math.sin(y * 0.4) * 0.8, y, greens[1])
            if rng.random() < 0.45:
                for dx in (-1, 1):
                    _px(img, x + dx * rng.randint(1, 2), y, _jitter(rng.choice(greens), rng, 8))
    for _ in range(12):
        cx, cy, r = rng.uniform(4, w - 5), rng.uniform(3, h * 0.6), rng.uniform(1.8, 3.2)
        c = rng.choice(petals)
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                d = math.hypot(x - cx, y - cy)
                if d <= r:
                    _px(img, x, y, _rgb("f6e070") if d < 0.8 else _jitter(_scale(c, 1.15 - 0.3 * d / r), rng, 6))


def paint_jar(img, rng):
    w, h = img.size
    for y in range(h):
        for x in range(w):
            k = 1.2 - 0.5 * abs(x - w * 0.35) / w
            c = _rgb("6a7a8a") if 3 <= y <= 5 else _rgb("c8b89a")
            _px(img, x, y, _jitter(_scale(c, k), rng, 5))


def paint_terracotta(img, rng):
    w, h = img.size
    for y in range(h):
        for x in range(w):
            c = _rgb("a85a34") if y > 2 else _rgb("c8784a")
            _px(img, x, y, _jitter(c, rng, 8))


# ---------------------------------------------------------------- emblems (banners)
def draw_emblem(img, box, kind, colour=(236, 226, 200), scale=1.0):
    """Paints an emblem in box (x, y, w, h) of img: crossed_swords (two swords crossed, points up, cream / silver),
    lotus (gold lotus flower over a base line), heraldic_shield (gold heater shield with a darker border and a
    cross), flower_knot (a round red knot, for floors)."""
    from PIL import Image, ImageDraw
    bx, by, w, h = box
    S = 4
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    W, H = w * S, h * S

    def P(x, y):
        return (W / 2 + (x - 0.5) * W * scale, H / 2 + (y - 0.5) * H * scale)

    col = tuple(colour[:3])
    dark = tuple(int(c * 0.55) for c in col)
    lw = max(2, int(W * scale * 0.06))
    if kind == "crossed_swords":
        for sgn in (1, -1):
            tip, pom = P(0.5 - 0.42 * sgn, 0.06), P(0.5 + 0.36 * sgn, 0.92)
            gx, gy = P(0.5 + 0.22 * sgn, 0.72)
            d.line([tip, (gx, gy)], fill=dark, width=int(lw * 1.9))
            d.line([tip, (gx, gy)], fill=col, width=int(lw * 1.2))
            # crossguard, perpendicular to the blade
            vx, vy = gx - tip[0], gy - tip[1]
            L = math.hypot(vx, vy)
            px, py = -vy / L, vx / L
            g = 0.17 * W * scale
            d.line([(gx - px * g, gy - py * g), (gx + px * g, gy + py * g)], fill=col, width=int(lw * 1.3))
            d.line([(gx, gy), pom], fill=dark, width=int(lw * 1.1))
            r = lw * 1.0
            d.ellipse([pom[0] - r, pom[1] - r, pom[0] + r, pom[1] + r], fill=col)
    elif kind == "lotus":
        cxp, base = P(0.5, 0.0)[0], P(0, 0.78)[1]
        sc = W * scale

        def petal(angle, length, width):
            pts = []
            for k in range(21):
                t = k / 20
                r = length * t
                off = width * math.sin(math.pi * t) * (1 - 0.3 * t)
                for sgn in (1,):
                    pass
                pts.append((t, r, off))
            left = [(cxp + math.sin(angle) * r + math.cos(angle) * off, base - math.cos(angle) * r + math.sin(angle) * off) for t, r, off in pts]
            right = [(cxp + math.sin(angle) * r - math.cos(angle) * off, base - math.cos(angle) * r - math.sin(angle) * off) for t, r, off in pts]
            poly = left + right[::-1]
            d.polygon(poly, fill=col, outline=dark)
        for ang, ln, wd in ((-1.15, 0.42, 0.1), (1.15, 0.42, 0.1), (-0.6, 0.55, 0.12), (0.6, 0.55, 0.12), (0.0, 0.7, 0.14)):
            petal(ang, ln * sc, wd * sc)
        d.line([P(0.18, 0.8), P(0.82, 0.8)], fill=col, width=int(lw * 1.2))
        d.line([P(0.3, 0.88), P(0.7, 0.88)], fill=col, width=int(lw * 0.9))
    elif kind == "heraldic_shield":
        pts = []
        for k in range(21):
            t = k / 20
            pts.append(P(0.5 + 0.38 * (1 - max(0.0, t - 0.45) ** 2 / 0.3025) * (-1), 0.08 + 0.84 * t))
        outline = [P(0.12, 0.08), P(0.88, 0.08)]
        for k in range(21):
            t = k / 20
            yy = 0.08 + 0.42 + 0.42 * t
            xx = 0.38 * math.sqrt(max(0.0, 1 - t * t))
            outline.append(P(0.5 + xx, yy))
        for k in range(21):
            t = 1 - k / 20
            yy = 0.08 + 0.42 + 0.42 * t
            xx = 0.38 * math.sqrt(max(0.0, 1 - t * t))
            outline.append(P(0.5 - xx, yy))
        d.polygon(outline, fill=dark)
        inner = [(W / 2 + (x - W / 2) * 0.8, H / 2 + (y - H / 2) * 0.8 + H * 0.01) for x, y in outline]
        d.polygon(inner, fill=col)
        d.line([P(0.5, 0.2), P(0.5, 0.8)], fill=dark, width=int(lw * 1.1))
        d.line([P(0.27, 0.42), P(0.73, 0.42)], fill=dark, width=int(lw * 1.1))
    elif kind == "flower_knot":
        cx, cy = P(0.5, 0.5)
        R = 0.42 * W * scale
        for k in range(8):
            a = 2 * math.pi * k / 8
            px, py = cx + math.cos(a) * R * 0.55, cy + math.sin(a) * R * 0.55
            r = R * 0.42
            d.ellipse([px - r, py - r, px + r, py + r], outline=col, width=int(lw * 0.9))
        d.ellipse([cx - R * 0.3, cy - R * 0.3, cx + R * 0.3, cy + R * 0.3], fill=col)
        d.ellipse([cx - R * 0.12, cy - R * 0.12, cx + R * 0.12, cy + R * 0.12], fill=dark)
    else:
        raise KeyError(kind)
    im = im.resize((w, h), Image.LANCZOS)
    base = img.crop((bx, by, bx + w, by + h))
    base.alpha_composite(im)
    img.paste(base, (bx, by))


def paint_banner(img, rng, colour, emblem, emblem_colour):
    """Hanging banner: cloth in `colour`, a darker border and a light inner line, the emblem in the upper part,
    a ragged bottom (three points, small tears) cut out."""
    main, dark, light = COLOURS[colour] if isinstance(colour, str) else colour
    w, h = img.size
    ml.tt._weave(img, _full(img), main, rng, seams=0, patches=0, stains=2, tears=0, noise=4)
    body = int(h * 0.8)
    cuts = [rng.uniform(-2, 2) for _ in range(w)]
    for y in range(h):
        for x in range(w):
            if y >= body:
                # three points with a few ragged tears
                ph = (x / (w - 1)) * 3
                f = 1 - abs((ph % 1) - 0.5) * 2
                lim = body + (h - body) * f + cuts[x] - 1
                if y > lim or (x % 7 == 3 and y > body + 2):
                    _px(img, x, y, (0, 0, 0), 0)
                    continue
            e = min(x, w - 1 - x, y)
            if e < 2:
                _px(img, x, y, _jitter(dark, rng, 5))
            elif e == 3 and y < body - 1:
                _px(img, x, y, _jitter(_mix(light, BEIGE, 0.4), rng, 6))
    s = int(min(w - 8, body * 0.75))
    draw_emblem(img, ((w - s) // 2, int(body * 0.12), s, s), emblem, colour=emblem_colour)


def paint_awning_roof(img, rng, colour, stripe=None, n=6):
    """Awning cloth: plain `colour` (a soft weave, vertical seams) or stripes colour / stripe running down (v)."""
    main, dark, light = COLOURS[colour]
    w, h = img.size
    if stripe is None:
        ml.tt._weave(img, _full(img), main, rng, seams=w // 3, patches=0, stains=2, tears=0, seam_dir="v", noise=4)
    else:
        sc = BEIGE if stripe == "beige" else COLOURS[stripe][0]
        sw = w // n
        for k in range(n):
            ml.tt._weave(img, (k * sw, 0, sw if k < n - 1 else w - k * sw, h), main if k % 2 == 0 else sc, rng, seams=0, patches=0,
                         stains=1, tears=0, noise=4)
    for y in range(h):
        for x in range(w):
            r, g, b, a = img.getpixel((x, y))
            k = 0.9 + 0.12 * (y / h)
            img.putpixel((x, y), _scale((r, g, b), k) + (255,))


def paint_awning_valance(img, rng, colour, stripe=None, n=6, scallops=8):
    """The valance hanging under the awning edge: scalloped bottom (cut-out), a darker hem at the top, gold piping."""
    main, dark, light = COLOURS[colour]
    w, h = img.size
    paint_awning_roof(img, rng, colour, stripe=stripe, n=n)
    sw = w / scallops
    for x in range(w):
        lx = (x % sw) / sw
        bottom = h * 0.55 + h * 0.42 * math.sin(math.pi * lx)
        for y in range(h):
            if y > bottom:
                _px(img, x, y, (0, 0, 0), 0)
            elif y >= bottom - 1.5:
                _px(img, x, y, _jitter(GOLD, rng, 10))
            elif y < 2:
                _px(img, x, y, _jitter(dark, rng, 5))


def paint_earth_floor(img, rng):
    """Trodden earth mixed with stones: a dense cobble of rounded grey / brown stones with dirt between them,
    worn bare patches, a few pebbles and straw bits."""
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = _jitter(_mix(_rgb("6e5034"), _rgb("8a6a46"), rng.random()), rng, 8)
            px[x, y] = c + (255,)
    stones = [_rgb("8a847a"), _rgb("9a948a"), _rgb("7a746c"), _rgb("8c7a66"), _rgb("a49c90"), _rgb("6e6a64")]
    # bare earth patches where the stones are missing
    bare = [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(5, 12)) for _ in range(max(2, w * h // 2200))]
    step = 6
    for gy in range(-step, h + step, step):
        for gx in range(-step, w + step, step):
            cx, cy = gx + rng.uniform(-1.5, 1.5) + (step / 2 if (gy // step) % 2 else 0), gy + rng.uniform(-1.5, 1.5)
            if any(math.hypot(cx - bx, cy - by) < br for bx, by, br in bare) and rng.random() < 0.8:
                continue
            rx_, ry_ = rng.uniform(2.0, 3.2), rng.uniform(1.8, 2.8)
            c = rng.choice(stones)
            for y in range(int(cy - ry_ - 1), int(cy + ry_ + 2)):
                for x in range(int(cx - rx_ - 1), int(cx + rx_ + 2)):
                    if not (0 <= x < w and 0 <= y < h):
                        continue
                    d = math.hypot((x - cx) / rx_, (y - cy) / ry_)
                    if d <= 1.0:
                        k = 1.14 - 0.3 * d - (0.12 if (x - cx) + (y - cy) > 1 else 0)
                        px[x, y] = _jitter(_scale(c, k), rng, 6) + (255,)
                    elif d <= 1.25:
                        px[x, y] = _jitter(_rgb("4a3624"), rng, 5) + (255,)
    for _ in range(w * h // 90):
        x, y = rng.randrange(w), rng.randrange(h)
        px[x, y] = _jitter(rng.choice([_rgb("c9a85a"), _rgb("5a4630"), _rgb("a49c90")]), rng, 8) + (255,)


def paint_tatami_floor(img, rng, w_blocks, d_blocks, ppb, border=0.5, border_colour="red", motif="flower_knot",
                       motif_colour=None, mat=_rgb("d8c48e")):
    """A tatami floor seen from above (texture top = the back of the area): beige woven mats of 1 x 2 blocks laid in
    the classic staggered pattern, dark cloth edges (heri) along their long sides, a `border` (blocks) of
    `border_colour` cloth all round with gold piping, and a centre motif (flower_knot or lotus) in red."""
    main, dark, light = COLOURS[border_colour]
    w, h = img.size
    px = img.load()
    b = int(round(border * ppb))
    # mats
    ix0, iy0, ix1, iy1 = b, b, w - b, h - b
    mw, mh = ppb, 2 * ppb
    for y in range(h):
        for x in range(w):
            px[x, y] = (0, 0, 0, 255)
    mats = []
    row = 0
    y = iy0
    while y < iy1:
        horizontal = row % 2 == 1
        if horizontal:
            x = ix0
            hh = ppb
            while x < ix1:
                mats.append((x, y, min(ix1, x + 2 * ppb), min(iy1, y + hh), "h"))
                x += 2 * ppb
            y += hh
        else:
            x = ix0
            hh = 2 * ppb
            while x < ix1:
                mats.append((x, y, min(ix1, x + mw), min(iy1, y + hh), "v"))
                x += mw
            y += hh
        row += 1
    for (x0, y0, x1, y1, o) in mats:
        tone = _jitter(mat, rng, 8)
        for y in range(y0, y1):
            for x in range(x0, x1):
                along = y if o == "v" else x
                across = x if o == "v" else y
                k = 1.0 + (0.07 if along % 2 == 0 else -0.05) + (0.03 if across % 3 == 0 else 0)
                c = _scale(tone, k)
                e_long = (x - x0 if o == "v" else y - y0), (x1 - 1 - x if o == "v" else y1 - 1 - y)
                if min(e_long) < max(1, ppb // 16):
                    c = _rgb("3a3028")
                elif min(x - x0, y - y0, x1 - 1 - x, y1 - 1 - y) == 0:
                    c = _scale(tone, 0.7)
                px[x, y] = _jitter(c, rng, 3) + (255,)
    # border with gold piping
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            if e < b:
                c = main
                if e < 1 or e == b - 1:
                    c = dark
                elif e == max(2, b // 4) or e == b - 1 - max(2, b // 4):
                    c = GOLD
                px[x, y] = _jitter(c, rng, 5) + (255,)
    if motif:
        s = int(min(w, h) * 0.22)
        draw_emblem(img, (w // 2 - s // 2, h // 2 - s // 2, s, s), motif, colour=motif_colour or main)


# ---------------------------------------------------------------- the atlas
_TRAINING = [  # (name, w, h, painter(img, rng))
    ("t_rivet_wood", 64, 16, paint_post_wood),
    ("t_pale_wood", 32, 16, paint_pale_wood),
    ("t_straw", 32, 32, paint_straw),
    ("t_straw_end", 16, 16, paint_straw_end),
    ("t_straw_rope", 16, 16, paint_straw_rope),
    ("t_bag", 16, 64, paint_bag),
    ("t_bag_end", 16, 16, paint_leather),
    ("t_stone_brick", 32, 32, paint_stone_brick),
    ("t_stone_cap", 16, 16, paint_stone_cap),
    ("t_shield_round", 32, 32, paint_round_shield),
    ("t_shield_back", 32, 32, paint_shield_back),
    ("t_flowers", 32, 32, paint_flowers),
    ("t_jar", 16, 16, paint_jar),
    ("t_terracotta", 16, 16, paint_terracotta),
]


def _painter(name, fn, *args, **kw):
    def paint(img):
        fn(img, random.Random(_seed(name)), *args, **kw)
    return paint


class Atlas(ml.Atlas):
    """merchantlib.Atlas (the shell regions in `colour`) + the training regions (see the module doc)."""

    def __init__(self, name, colour="red", size=512, banner_colour=None, rug_colour=None):
        super().__init__(name, colour=colour, size=size, banner_colour=banner_colour, rug_colour=rug_colour)
        for n, w, h, fn in _TRAINING:
            self.add(n, w, h, _painter(n, fn))


def floor_region(atlas, name, w_blocks, d_blocks, kind="earth", ppb=16, **kw):
    """Adds a floor texture of w_blocks x d_blocks at ppb pixels per block (maps 1:1 on floor()); kind "earth"
    (earth + stones) or "tatami" (kw: border=0.5, border_colour="red", motif="flower_knot" | "lotus" | None,
    motif_colour=None, mat=rgb). Returns the region name."""
    w, h = int(round(w_blocks * ppb)), int(round(d_blocks * ppb))
    if kind == "earth":
        atlas.add(name, w, h, _painter(name, paint_earth_floor))
    elif kind == "tatami":
        atlas.add(name, w, h, _painter(name, paint_tatami_floor, w_blocks, d_blocks, ppb, **kw))
    else:
        raise KeyError(kind)
    return name


def banner_region(atlas, colour, emblem, emblem_colour=None, w=32, h=64):
    """Adds (once) a hanging banner texture: colour (a COLOURS name), emblem crossed_swords | lotus | heraldic_shield;
    emblem_colour default cream for the swords, gold otherwise. Returns the region name."""
    name = "t_banner_%s_%s" % (colour, emblem)
    if emblem_colour is None:
        emblem_colour = (236, 226, 200) if emblem == "crossed_swords" else (232, 186, 70)
    if name not in atlas.regions:
        atlas.add(name, w, h, _painter(name, paint_banner, colour, emblem, emblem_colour))
    return name


def awning_regions(atlas, colour, stripe=None, n=6):
    """Adds (once) an awning roof (64x48) and its scalloped valance (64x16): plain `colour`, or stripes of colour and
    `stripe` ("beige" or a COLOURS name). Returns (roof_region, valance_region)."""
    key = "%s_%s" % (colour, stripe or "plain")
    roof, val = "t_awning_" + key, "t_valance_" + key
    if roof not in atlas.regions:
        atlas.add(roof, 64, 48, _painter(roof, paint_awning_roof, colour, stripe=stripe, n=n))
        atlas.add(val, 64, 16, _painter(val, paint_awning_valance, colour, stripe=stripe, n=n))
    return roof, val


# ---------------------------------------------------------------- the area
class Area:
    pass


def area(name, atlas):
    """The bones of an area: A.root (named after the area), A.shell (fences, floor, big props), A.detail (bone
    "detail": small things, hidden beyond 32 blocks), A.atlas."""
    A = Area()
    A.name, A.atlas = name, atlas
    A.root = Bone(name)
    A.shell = Bone("shell", parent=A.root)
    A.detail = Bone("detail", parent=A.root)
    return A


def floor(bone, name, x0, x1, z0, z1, region, y=0.0, th=0.04, edge="t_stone_cap"):
    """The floor plate lying on the ground (top at y + th, region mapped 1:1 when made by floor_region; texture top =
    the back, -z). No collision: players walk on the real ground under it."""
    return add_cube(bone, name, ((x0 + x1) / 2, y + th / 2 + 0.002, (z0 + z1) / 2), EYE, (x1 - x0, th, z1 - z0),
                    {"all": edge, "+2": region, "-2": None}, stretch=True, u_dir=X, v_dir=Z)


# ---------------------------------------------------------------- fences
class Fence:
    pass


def _side_points(x0, x1, z0, z1):
    """The four sides as (name, start, end) going round: front (+z) left to right, right side front to back, back
    right to left, left side back to front."""
    return [("front", v3(x0, 0, z1), v3(x1, 0, z1)), ("right", v3(x1, 0, z1), v3(x1, 0, z0)),
            ("back", v3(x1, 0, z0), v3(x0, 0, z0)), ("left", v3(x0, 0, z0), v3(x0, 0, z1))]


def fence_post(A, name, foot, h=FENCE_H, d=0.26, stone=False, pillar=False, caps=True):
    """One fence post at foot (x, 0, z): squared wood with an iron cap and band (t_rivet_wood); stone=True puts it
    on a stone-brick base (0.62 wide, 0.5 high), pillar=True makes it a stone pillar (0.5 wide, h + 0.25 high, stone
    cap). Returns the top point (x, y_top, z)."""
    foot = v3(*foot)
    if pillar:
        ph = h + 0.25
        box(A.shell, name + "_pillar", foot + v3(-0.25, 0, -0.25), foot + v3(0.25, ph, 0.25), "t_stone_brick", stretch=True)
        box(A.shell, name + "_pcap", foot + v3(-0.3, ph, -0.3), foot + v3(0.3, ph + 0.1, 0.3), "t_stone_cap", stretch=True)
        collide((foot[0] - 0.3, 0.0, foot[2] - 0.3, foot[0] + 0.3, max(FENCE_COLLIDE_H, ph + 0.1), foot[2] + 0.3))
        return foot + UP * (ph + 0.1)
    y0 = 0.0
    if stone:
        y0 = 0.5
        box(A.shell, name + "_base", foot + v3(-0.31, 0, -0.31), foot + v3(0.31, y0, 0.31), "t_stone_brick", stretch=True)
        box(A.detail, name + "_base_cap", foot + v3(-0.34, y0 - 0.06, -0.34), foot + v3(0.34, y0, 0.34), "t_stone_cap", stretch=True)
        h = h + 0.25
        d = d + 0.04
    top = foot + UP * (y0 + h)
    beam(A.shell, name, foot + UP * y0, top, d, {"all": "t_rivet_wood", "+1": "end_grain", "-1": "end_grain"})
    if caps:
        box(A.detail, name + "_cap", top + v3(-d / 2 - 0.025, -0.02, -d / 2 - 0.025), top + v3(d / 2 + 0.025, 0.05, d / 2 + 0.025), "iron")
    collide((foot[0] - d / 2 - (0.06 if stone else 0), 0.0, foot[2] - d / 2 - (0.06 if stone else 0),
             foot[0] + d / 2 + (0.06 if stone else 0), max(FENCE_COLLIDE_H, y0 + h), foot[2] + d / 2 + (0.06 if stone else 0)))
    return top + UP * 0.05


def fence_bay(A, name, p0, p1, h=FENCE_H, rails=(0.38, 0.86), solid=True):
    """The two plank rails between two post feet p0, p1 (and the 1.5-high collision of the bay)."""
    p0, p1 = v3(*p0), v3(*p1)
    d = norm(p1 - p0)
    for i, r in enumerate(rails):
        y = r * h / FENCE_H
        beam(A.shell, "%s_rail_%d" % (name, i), p0 + UP * y, p1 + UP * y, 0.1, "plank", width=0.2, up=UP, extend=0.02)
    if solid:
        lo, hi = np.minimum(p0, p1), np.maximum(p0, p1)
        t = 0.14
        collide((lo[0] - (t if abs(d[0]) < 0.5 else 0), 0.0, lo[2] - (t if abs(d[2]) < 0.5 else 0),
                 hi[0] + (t if abs(d[0]) < 0.5 else 0), FENCE_COLLIDE_H, hi[2] + (t if abs(d[2]) < 0.5 else 0)))


def fence_ring(A, x0, x1, z0, z1, entrance=("front", 0.0, 1.6), post_every=1.4, h=FENCE_H, stone="corners", gaps=()):
    """A post-and-rail fence round the rectangle x0..x1, z0..z1 with an entrance gap: entrance = (side, centre along
    that side's axis (x for front / back, z for left / right), width >= 1.5) or None. stone = "corners" (stone bases
    under the corner posts), "pillars" (stone pillars at the corners and both sides of the entrance), or None.
    gaps = extra (side, centre, width) openings without gate posts (e.g. where a stall's back stands).
    Returns F: F.posts (dict corner name -> top point: front_left, front_right, back_left, back_right, gate_left,
    gate_right), F.tops (every post top), F.entrance (x0, z0, x1, z1 of the free gap), F.box."""
    F = Fence()
    F.posts, F.tops = {}, []
    F.box = (x0, z0, x1, z1)
    corners = {"front_left": v3(x0, 0, z1), "front_right": v3(x1, 0, z1), "back_right": v3(x1, 0, z0), "back_left": v3(x0, 0, z0)}
    for cn, p in corners.items():
        top = fence_post(A, "post_" + cn, p, h=h, stone=stone == "corners", pillar=stone == "pillars")
        F.posts[cn] = top
        F.tops.append(top)
    F.entrance = None
    openings = []
    if entrance:
        openings.append((entrance, True))
    openings += [(g, False) for g in gaps]
    for side, a, b in _side_points(x0, x1, z0, z1):
        L = np.linalg.norm(b - a)
        dvec = (b - a) / L
        axis = 0 if side in ("front", "back") else 2
        cuts = []
        for (es, ec, ew), gate in openings:
            if es != side:
                continue
            # the gap's start / end as distances along this side
            t0 = (ec - ew / 2 - a[axis]) / dvec[axis]
            t1 = (ec + ew / 2 - a[axis]) / dvec[axis]
            t0, t1 = min(t0, t1), max(t0, t1)
            cuts.append((t0, t1, gate))
        cuts.sort()
        # runs of fence between the corners and the gaps
        runs, s = [], 0.0
        for t0, t1, gate in cuts:
            runs.append((s, t0, gate))
            s = t1
        runs.append((s, L, False))
        for ri, (s0, s1, gate_end) in enumerate(runs):
            if s1 - s0 < 0.05:
                continue
            n = max(1, int(math.ceil((s1 - s0) / post_every)))
            pts = [a + dvec * (s0 + (s1 - s0) * k / n) for k in range(n + 1)]
            for k, p in enumerate(pts):
                is_corner = (k == 0 and s0 == 0.0) or (k == n and abs(s1 - L) < 1e-6)
                if is_corner:
                    continue
                gate_post = (k == n and gate_end) or (k == 0 and ri > 0 and cuts[ri - 1][2])
                pname = "post_%s_%d_%d" % (side, ri, k)
                top = fence_post(A, pname, p, h=h, pillar=(stone == "pillars" and gate_post))
                F.tops.append(top)
                if gate_post:
                    F.posts["gate_left" if "gate_left" not in F.posts else "gate_right"] = top
            for k in range(n):
                fence_bay(A, "bay_%s_%d_%d" % (side, ri, k), pts[k], pts[k + 1], h=h)
        for t0, t1, gate in cuts:
            if gate:
                g0, g1 = a + dvec * t0, a + dvec * t1
                lo, hi = np.minimum(g0, g1), np.maximum(g0, g1)
                F.entrance = (lo[0], lo[2], hi[0], hi[2])
    return F


# ---------------------------------------------------------------- dummies
def dummy(A, name, foot, height=1.75, yaw=0.0, helmet=False, sword=None, shield=None, shield_region="t_shield_round",
          body="t_straw", arms_up=0.0, solid=True):
    """A straw-and-wood training dummy standing on foot (x, 0, z), facing +z turned by yaw (radians): a dark wooden
    cross foot, the post, a straw body bound with rope, horizontal straw arms (a cross) with rope wraps, a straw head
    with a rope at the neck. height = top of the head. helmet=True: an iron nasal helmet on the head; sword = "pos_x"
    | "neg_x" (local side of the arm holding an upright sword, raised forward); shield = "pos_x" | "neg_x" (a round
    shield strapped to that arm, facing forward). Returns a dict of attachment points (head_top, arm_l, arm_r,
    chest)."""
    foot = v3(*foot)
    R = ry(yaw)

    def P(x, y, z):
        return foot + R @ v3(x, y, z)

    sh, det = A.shell, A.detail
    s = height / 1.75
    head = 0.34 * s
    body_h = 0.62 * s
    neck_y = height - head
    body_top = neck_y - 0.05 * s
    body_bot = body_top - body_h
    arm_y = body_top - 0.15 * s
    # foot: two crossing planks and a block
    add_cube(sh, name + "_foot_a", P(0, 0.06, 0), R, (0.8, 0.12, 0.16), "wood_dark")
    add_cube(sh, name + "_foot_b", P(0, 0.06, 0), R, (0.16, 0.12, 0.8), "wood_dark")
    add_cube(sh, name + "_foot_c", P(0, 0.16, 0), R, (0.26, 0.14, 0.26), {"all": "wood", "+2": "end_grain"})
    # post (visible under the body)
    add_cube(sh, name + "_post", P(0, (0.2 + body_bot + 0.1) / 2, 0), R, (0.13, body_bot - 0.1, 0.13), "wood")
    # body, rope bands, a straw skirt at the bottom
    add_cube(sh, name + "_body", P(0, (body_bot + body_top) / 2, 0), R, (0.5 * s, body_h, 0.34 * s),
             {"all": body, "+2": "t_straw_end", "-2": "t_straw_end"}, stretch=True)
    add_cube(det, name + "_skirt", P(0, body_bot - 0.06 * s, 0), R, (0.42 * s, 0.14 * s, 0.28 * s), body, stretch=True)
    for k, t in enumerate((0.3, 0.62)):
        y = body_bot + body_h * t
        add_cube(det, "%s_band_%d" % (name, k), P(0, y, 0), R, (0.52 * s, 0.06, 0.36 * s), "rope")
    # arms (a cross), rope wraps near the ends, little straw fists
    span = 0.98 * s
    add_cube(sh, name + "_arms", P(0, arm_y, 0), R, (span, 0.17 * s, 0.17 * s),
             {"all": "t_straw_rope", "+1": "t_straw_end", "-1": "t_straw_end"}, stretch=True)
    for k, sx in enumerate((-1, 1)):
        add_cube(det, "%s_wrap_%d" % (name, k), P(sx * span * 0.36, arm_y, 0), R, (0.07, 0.19 * s, 0.19 * s), "rope")
    # head and neck rope
    add_cube(sh, name + "_head", P(0, neck_y + head / 2, 0), R, (head, head, head * 0.92),
             {"all": body, "+2": "t_straw_end", "-2": "t_straw_end"}, stretch=True)
    add_cube(det, name + "_neck", P(0, neck_y - 0.01, 0), R, (0.2 * s, 0.07, 0.2 * s), "rope")
    pts = {"head_top": P(0, height, 0), "arm_l": P(-span / 2, arm_y, 0), "arm_r": P(span / 2, arm_y, 0),
           "chest": P(0, (body_bot + body_top) / 2, 0.17 * s)}
    if helmet:
        hc = P(0, height - head * 0.28, 0)
        add_cube(sh, name + "_helm", hc + UP * 0.04, R, (head + 0.06, head * 0.62, head * 0.98), "steel")
        add_cube(det, name + "_helm_top", hc + UP * (head * 0.36 + 0.04), R, (head * 0.7, 0.06, head * 0.7), "steel")
        add_cube(det, name + "_helm_rim", hc - UP * (head * 0.25), R, (head + 0.1, 0.05, head + 0.06), "iron")
        add_cube(det, name + "_helm_nasal", P(0, height - head * 0.55, head * 0.5 + 0.03), R, (0.05, head * 0.42, 0.03), "iron")
        pts["head_top"] = P(0, height + 0.08, 0)
    for side, kind in ((sword, "sword"), (shield, "shield")):
        if side is None:
            continue
        sx = 1 if side == "pos_x" else -1
        hand = P(sx * (span / 2 + 0.02), arm_y, 0)
        if kind == "sword":
            add_cube(det, name + "_fist", hand, R, (0.12, 0.14, 0.14), body, stretch=True)
            up = R @ norm(v3(0, 0.82, 0.57))
            ml.sword(det, name + "_sword", hand - up * 0.13, up=up, facing=R @ v3(1, 0, 0), length=0.95)
        else:
            c = hand + R @ v3(sx * 0.06, -0.02, 0.17)
            add_cube(det, name + "_strap", hand + R @ v3(sx * 0.03, 0, 0.08), R, (0.08, 0.1, 0.16), "leather")
            round_shield(A, name + "_shield", c, R @ v3(sx * 0.25, 0, 1.0), r=0.36, region=shield_region)
    if solid:
        hw = max(0.4, span / 2 + 0.05)
        ex = abs(math.cos(yaw)) * hw + abs(math.sin(yaw)) * 0.25
        ez = abs(math.sin(yaw)) * hw + abs(math.cos(yaw)) * 0.25
        collide((foot[0] - 0.3, 0.0, foot[2] - 0.3, foot[0] + 0.3, height, foot[2] + 0.3))
        collide((foot[0] - ex, body_bot, foot[2] - ez, foot[0] + ex, body_top, foot[2] + ez))
    return pts


def round_shield(A, name, center, normal, r=0.36, region="t_shield_round", back="t_shield_back", boss=True, bone=None):
    """A round shield (cut-out disc, both faces: `region` in front, planks behind) at center facing `normal`, with
    an iron boss in the middle."""
    bone = bone or A.detail
    n = norm(v3(*normal))
    upv = norm(UP - np.dot(UP, n) * n)
    u = np.cross(upv, n)
    axes = np.column_stack([u, upv, n])
    c = v3(*center)
    add_cube(bone, name, c, axes, (2 * r, 2 * r, 0.04), {"all": None, "+3": region, "-3": back}, stretch=True, u_dir=u, v_dir=-upv)
    if boss:
        add_cube(bone, name + "_boss", c + n * 0.04, axes, (r * 0.36, r * 0.36, 0.07), "steel")
    return c


def helmet(A, name, center, size=0.36, yaw=0.0, bone=None):
    """An iron nasal helmet resting at center (its middle; for racks and tables)."""
    bone = bone or A.detail
    R = ry(yaw)
    c = v3(*center)
    add_cube(bone, name, c, R, (size, size * 0.6, size), "steel")
    add_cube(bone, name + "_top", c + UP * size * 0.33, R, (size * 0.7, 0.06, size * 0.7), "steel")
    add_cube(bone, name + "_rim", c - UP * size * 0.28, R, (size + 0.04, 0.05, size + 0.04), "iron")
    add_cube(bone, name + "_nasal", c + R @ v3(0, -size * 0.35, size / 2 + 0.01), R, (0.05, size * 0.4, 0.03), "iron")


# ---------------------------------------------------------------- punching bag, racks, furniture
def punching_bag(A, name, foot, yaw=0.0, span=1.6, h=2.6, bag_h=1.05, bag_r=0.3, coil=True):
    """A heavy punching bag hanging on a chain from a wooden gallows: two posts (span apart along local x) on foot
    blocks, a top beam overhanging both, corner braces, a chain to the straw bag (rope bands, leather ends), a coil
    of rope hung on the left post. foot = the ground point under the bag."""
    foot = v3(*foot)
    R = ry(yaw)

    def P(x, y, z):
        return foot + R @ v3(x, y, z)

    sh, det = A.shell, A.detail
    for k, sx in enumerate((-1, 1)):
        x = sx * span / 2
        tl.post(sh, "%s_post_%d" % (name, k), P(x, 0, 0), P(x, h, 0), d=0.24, region="post")
        add_cube(det, "%s_postfoot_%d" % (name, k), P(x, 0.08, 0), R, (0.4, 0.16, 0.4), "wood_dark")
        beam(det, "%s_brace_%d" % (name, k), P(x - sx * 0.05, h - 0.62, 0), P(x - sx * 0.55, h - 0.1, 0), 0.12, "wood")
    beam(sh, name + "_beam", P(-span / 2 - 0.3, h + 0.1, 0), P(span / 2 + 0.3, h + 0.1, 0), 0.24, {"all": "beam", "+1": "end_grain", "-1": "end_grain"},
         width=0.24)
    add_cube(det, name + "_hook", P(0, h - 0.06, 0), R, (0.1, 0.1, 0.1), "black_iron")
    bag_top = h - 0.48
    beam(det, name + "_chain", P(0, h - 0.04, 0), P(0, bag_top + 0.04, 0), 0.05, "black_iron")
    add_cube(det, name + "_chain_link", P(0, (h + bag_top) / 2, 0), R, (0.09, 0.12, 0.03), "black_iron")
    for k, (a, b) in enumerate(((v3(-0.18, 0, 0), v3(0, 0.18, 0)), (v3(0.18, 0, 0), v3(0, 0.18, 0)))):
        beam(det, "%s_sling_%d" % (name, k), P(*(a + v3(0, bag_top, 0))), P(*(b + v3(0, bag_top, 0))), 0.04, "black_iron")
    by0 = bag_top - bag_h
    octo(sh, name + "_bag", P(0, by0, 0), bag_r, bag_h, {"all": "t_bag", "+2": "t_bag_end", "-2": "t_bag_end"}, yaw=yaw)
    octo(det, name + "_bag_top", P(0, bag_top - 0.02, 0), bag_r * 0.7, 0.08, "t_bag_end", yaw=yaw)
    for k, t in enumerate((0.25, 0.75)):
        octo(det, "%s_bag_rope_%d" % (name, k), P(0, by0 + bag_h * t - 0.03, 0), bag_r + 0.02, 0.06, "rope", yaw=yaw)
    if coil:
        cx = -span / 2
        for k in range(4):
            a0, a1 = 2 * math.pi * k / 4, 2 * math.pi * (k + 1) / 4
            p0 = P(cx + math.cos(a0) * 0.22, h - 0.9 + math.sin(a0) * 0.22, 0.17)
            p1 = P(cx + math.cos(a1) * 0.22, h - 0.9 + math.sin(a1) * 0.22, 0.17)
            beam(det, "%s_coil_%d" % (name, k), p0, p1, 0.08, "rope", extend=0.04)
        add_cube(det, name + "_coil_tie", P(cx, h - 0.62, 0.15), R, (0.1, 0.12, 0.1), "rope")
        # rope wound round the post foot
        add_cube(det, name + "_post_rope", P(span / 2, 0.55, 0), R, (0.29, 0.16, 0.29), "rope")
    lo = np.minimum(P(-span / 2 - 0.2, 0, -0.2), P(span / 2 + 0.2, 0, 0.2))
    hi = np.maximum(P(-span / 2 - 0.2, 0, -0.2), P(span / 2 + 0.2, 0, 0.2))
    collide((foot[0] - bag_r, by0, foot[2] - bag_r, foot[0] + bag_r, bag_top, foot[2] + bag_r))
    collide((lo[0], h - 0.05, lo[2], hi[0], h + 0.25, hi[2]))
    return P(0, by0, 0)


def sword_rack(A, name, p0, p1, normal=(0, 0, 1), h=1.0, swords=5, blade="steel", hilt="iron", grip="leather", solid=True):
    """A wooden sword rack from ground point p0 to p1: two uprights, a slotted base trough, a middle and a top rail;
    `swords` training swords standing in it blade UP (pommels in the trough, tips above the top rail)."""
    p0, p1 = v3(*p0), v3(*p1)
    n = norm(v3(*normal))
    sh, det = A.shell, A.detail
    for k, p in enumerate((p0, p1)):
        beam(sh, "%s_up_%d" % (name, k), p, p + UP * h, 0.1, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    beam(sh, name + "_trough", p0 + UP * 0.08, p1 + UP * 0.08, 0.16, "wood", width=0.3, extend=0.05)
    beam(sh, name + "_rail_mid", p0 + UP * 0.55 + n * 0.02, p1 + UP * 0.55 + n * 0.02, 0.07, "wood", width=0.08, extend=0.05)
    beam(sh, name + "_rail_top", p0 + UP * (h - 0.05), p1 + UP * (h - 0.05), 0.08, "wood_dark", width=0.12, extend=0.08)
    for i in range(swords):
        t = (i + 0.5) / swords
        b = p0 + (p1 - p0) * t + UP * 0.15
        ml.sword(det, "%s_sword_%d" % (name, i), b, up=norm(UP - n * 0.06), facing=n, length=1.0, blade=blade, hilt=hilt, grip=grip)
    if solid:
        lo, hi = np.minimum(p0, p1), np.maximum(p0, p1)
        collide((lo[0] - 0.12, 0.0, lo[2] - 0.12, hi[0] + 0.12, h + 0.15, hi[2] + 0.12))


def shield_rack(A, name, p0, p1, normal=(0, 0, 1), h=1.6, shields=3, rows=1, region="t_shield_round", r=0.34, solid=True):
    """A wooden shield rack (two uprights, cross boards, pegs) from ground point p0 to p1 with `shields` round
    shields per row hung on its `normal` side (rows 1 or 2, overlapping a little)."""
    p0, p1 = v3(*p0), v3(*p1)
    n = norm(v3(*normal))
    sh, det = A.shell, A.detail
    for k, p in enumerate((p0, p1)):
        beam(sh, "%s_up_%d" % (name, k), p, p + UP * h, 0.11, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    ys = [h - r - 0.1] if rows == 1 else [h - r - 0.05, h - 3 * r - 0.05]
    for j, y in enumerate(ys):
        beam(sh, "%s_board_%d" % (name, j), p0 + UP * (y + 0.05), p1 + UP * (y + 0.05), 0.14, "plank", width=0.06, extend=0.06)
        for i in range(shields):
            t = (i + 0.5) / shields
            c = p0 + (p1 - p0) * t + UP * y + n * (0.08 + 0.03 * (i % 2))
            round_shield(A, "%s_shield_%d_%d" % (name, j, i), c, n, r=r, region=region)
    beam(sh, name + "_top", p0 + UP * (h + 0.02), p1 + UP * (h + 0.02), 0.08, "wood", width=0.14, extend=0.1)
    if solid:
        lo, hi = np.minimum(p0, p1), np.maximum(p0, p1)
        collide((lo[0] - 0.1, 0.0, lo[2] - 0.1, hi[0] + 0.1, h + 0.06, hi[2] + 0.1))


def bench(A, name, foot, length=1.4, yaw=0.0, h=0.45, depth=0.36, solid=True):
    """A plank bench (seat, two slab legs, a stretcher) centred on foot, along local x."""
    foot = v3(*foot)
    R = ry(yaw)

    def P(x, y, z):
        return foot + R @ v3(x, y, z)

    add_cube(A.shell, name + "_seat", P(0, h - 0.04, 0), R, (length, 0.08, depth), "plank", u_dir=R @ X)
    for k, sx in enumerate((-1, 1)):
        add_cube(A.shell, "%s_leg_%d" % (name, k), P(sx * (length / 2 - 0.15), (h - 0.08) / 2, 0), R, (0.08, h - 0.08, depth - 0.04), "wood_dark")
    add_cube(A.detail, name + "_stretcher", P(0, 0.14, 0), R, (length - 0.3, 0.06, 0.06), "wood_dark")
    if solid:
        ex = abs(math.cos(yaw)) * length / 2 + abs(math.sin(yaw)) * depth / 2
        ez = abs(math.sin(yaw)) * length / 2 + abs(math.cos(yaw)) * depth / 2
        collide((foot[0] - ex, 0.0, foot[2] - ez, foot[0] + ex, h, foot[2] + ez))


def staff(A, name, foot, top, d=0.06, region="t_pale_wood"):
    """A training staff from foot to top (leaning on a fence), with dark end caps."""
    foot, top = v3(*foot), v3(*top)
    beam(A.detail, name, foot, top, d, region)
    dd = norm(top - foot)
    beam(A.detail, name + "_cap0", foot, foot + dd * 0.08, d * 1.25, "leather_dark")
    beam(A.detail, name + "_cap1", top - dd * 0.08, top, d * 1.25, "leather_dark")


def wooden_sword(A, name, foot, top, facing=(0, 0, 1)):
    """A wooden training sword from its tip on the ground (foot) up to its pommel (top): light wood blade, dark
    guard and grip (leaning on a fence or a rack)."""
    foot, top = v3(*foot), v3(*top)
    d = norm(foot - top)
    ml.sword(A.detail, name, top, up=d, facing=facing, length=np.linalg.norm(top - foot) * 0.95, blade="t_pale_wood", hilt="wood_dark",
             grip="leather")


def flower_pot(A, name, foot, base=True, r=0.2):
    """A terracotta pot of pink flowers, on a stone-brick base (0.5 high) when base=True."""
    foot = v3(*foot)
    y = 0.0
    if base:
        y = 0.5
        box(A.shell, name + "_base", foot + v3(-0.28, 0, -0.28), foot + v3(0.28, y, 0.28), "t_stone_brick", solid=True, stretch=True)
        box(A.detail, name + "_base_cap", foot + v3(-0.31, y - 0.06, -0.31), foot + v3(0.31, y, 0.31), "t_stone_cap", stretch=True)
    octo(A.detail, name + "_pot", foot + UP * y, r, 0.3, {"all": "t_terracotta", "+2": "coal"})
    crossed(A.detail, name + "_flowers", foot + UP * (y + 0.52), 0.7, 0.62, "t_flowers")


def jar(A, name, foot, r=0.1, h=0.22):
    """A glazed ceramic jar with a cork lid (shelves)."""
    foot = v3(*foot)
    octo(A.detail, name, foot, r, h, {"all": "t_jar", "+2": "t_jar"})
    add_cube(A.detail, name + "_lid", foot + UP * (h + 0.025), EYE, (r * 1.1, 0.05, r * 1.1), "cork")


def folded_cloths(A, name, foot, n=3, w=0.36, d=0.26, regions=("cloth_white", "cloth_red", "cloth_beige")):
    """A stack of n folded cloths (towels, belts) on a shelf."""
    foot = v3(*foot)
    for k in range(n):
        add_cube(A.detail, "%s_%d" % (name, k), foot + UP * (0.035 + 0.07 * k) + v3(0.01 * (k % 2), 0, 0), EYE, (w, 0.065, d),
                 regions[k % len(regions)], stretch=True)


# ---------------------------------------------------------------- awning stall, lanterns, banners
def awning(A, name, x0, x1, z0, z1, roof_region, valance_region, h_front=2.1, h_back=2.45, overhang=0.18, sag=0.07,
           valance=0.28, sides=True, posts=True, post_region="post"):
    """A small awning on four posts (front posts at z1, back posts at z0): a sloping cloth roof (roof_region, sagging
    a little), a scalloped valance along the front (and the two sides when sides=True), top beams. The posts collide.
    Returns a dict: posts (name -> top point), front_y, back_y, box (x0, z0, x1, z1)."""
    sh, det = A.shell, A.detail
    pts = {"front_left": v3(x0, 0, z1), "front_right": v3(x1, 0, z1), "back_left": v3(x0, 0, z0), "back_right": v3(x1, 0, z0)}
    tops = {}
    for cn, p in pts.items():
        hh = h_front if cn.startswith("front") else h_back
        if posts:
            tl.post(sh, "%s_post_%s" % (name, cn), p, p + UP * (hh + 0.12), d=0.17, region=post_region)
        tops[cn] = p + UP * hh
    for k, (a, b) in enumerate(((tops["front_left"], tops["front_right"]), (tops["back_left"], tops["back_right"]),
                                (tops["back_left"], tops["front_left"]), (tops["back_right"], tops["front_right"]))):
        beam(sh, "%s_beam_%d" % (name, k), a, b, 0.12, "wood_dark", extend=0.12)
    o = overhang
    t0, t1 = tops["back_left"] + v3(-o, 0.08, -o * 0.5), tops["back_right"] + v3(o, 0.08, -o * 0.5)
    f0, f1 = tops["front_left"] + v3(-o, 0.08, o), tops["front_right"] + v3(o, 0.08, o)
    tl.canvas_panel(sh, name + "_roof", t0, t1, f0, f1, sag=sag, nx=2, ny=2, region=roof_region, ripple=0.02)
    # the valance: front, then the two sides
    edges = [(f0, f1, v3(0, 0, 1))]
    if sides:
        edges += [(t0, f0, v3(-1, 0, 0)), (f1, t1, v3(1, 0, 0))]
    for k, (a, b, n) in enumerate(edges):
        c = (a + b) / 2 - UP * (valance / 2) + n * 0.02
        plate(sh, "%s_valance_%d" % (name, k), c, np.linalg.norm(b - a), valance, valance_region, normal=n, th=0.015)
    return {"posts": tops, "front_y": h_front, "back_y": h_back, "box": (x0, z0, x1, z1)}


def lantern_post(A, name, foot, h=2.5, arm=(0.0, 0.0, 0.42), size=0.3, post_region="post"):
    """A tall lantern post: a squared post on a small foot, an iron arm at the top (towards `arm`) and a hanging
    lantern on a chain (lit on export). The post collides."""
    foot = v3(*foot)
    a = v3(*arm)
    tl.post(A.shell, name + "_post", foot, foot + UP * h, d=0.16, region=post_region)
    add_cube(A.detail, name + "_foot", foot + UP * 0.07, EYE, (0.32, 0.14, 0.32), "wood_dark")
    top = foot + UP * (h - 0.12)
    tip = top + a
    beam(A.detail, name + "_arm", top, tip, 0.05, "black_iron", extend=0.03)
    beam(A.detail, name + "_brace", top - UP * 0.3, tip - a * 0.5, 0.035, "black_iron")
    tl.lantern(A.shell, name + "_lamp", tip - UP * 0.38, size=size, metal="black_iron", chain_to=tip)
    return tip - UP * 0.38


def hanging_lantern(A, name, mount, drop=0.35, size=0.28):
    """A lantern hanging on a short chain under `mount` (a beam, an arm...)."""
    mount = v3(*mount)
    tl.lantern(A.shell, name, mount - UP * (drop + size * 0.65), size=size, metal="black_iron", chain_to=mount)


def post_banner(A, name, top, region, normal=(0, 0, 1), w=0.5, h=0.95, offset=0.16, arm=None, bone=None):
    """A banner hung from a short rod on the `normal` face of a post whose top point is `top` (the banner's top edge
    just under it); arm = (dx, dz): hang it instead from an arm sticking out of the post top by that vector (a small
    gallows bar, as on the back posts). Returns the banner's top centre."""
    top = v3(*top)
    n = norm(v3(*normal))
    bone = bone or A.shell
    if arm is not None:
        a = v3(arm[0], 0, arm[1])
        tip = top - UP * 0.1 + a
        beam(A.detail, name + "_arm", top - UP * 0.1, tip + norm(a) * 0.08, 0.1, "wood_dark", extend=0.03)
        tc = top - UP * 0.16 + a * 0.55
        ml.banner(bone, name, tc, w, h, normal=n, region=region, rod=True, wave=0.03)
        return tc
    tc = top - UP * 0.14 + n * offset
    ml.banner(bone, name, tc, w, h, normal=n, region=region, rod=True, wave=0.025)
    return tc


def tall_post(A, name, foot, h=2.6, d=0.22, stone=False):
    """A tall free-standing squared post (for a banner or a lantern), on a stone base if stone=True; collides.
    Returns its top point."""
    foot = v3(*foot)
    y0 = 0.0
    if stone:
        y0 = 0.45
        box(A.shell, name + "_base", foot + v3(-0.3, 0, -0.3), foot + v3(0.3, y0, 0.3), "t_stone_brick", stretch=True)
    tl.post(A.shell, name, foot + UP * y0, foot + UP * h, d=d, region="post", solid=False)
    box(A.detail, name + "_cap", foot + v3(-d / 2 - 0.03, h - 0.02, -d / 2 - 0.03), foot + v3(d / 2 + 0.03, h + 0.05, d / 2 + 0.03), "iron")
    collide((foot[0] - max(d / 2, 0.3 if stone else 0), 0.0, foot[2] - max(d / 2, 0.3 if stone else 0),
             foot[0] + max(d / 2, 0.3 if stone else 0), h, foot[2] + max(d / 2, 0.3 if stone else 0)))
    return foot + UP * (h + 0.05)


# ---------------------------------------------------------------- icon, export
def icon(path, kind="dummy", colour="red", floor="earth"):
    """16x16 item icon: a fenced yard seen from the front-above, its floor (earth or tatami), a straw dummy in the
    middle (kind dummy / shield: with a round shield) and a banner in `colour` on the left post."""
    from PIL import Image
    main, dark, light = COLOURS[colour]
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    fl = (122, 96, 66) if floor == "earth" else (214, 196, 142)
    for y in range(9, 15):
        for x in range(1, 15):
            c = fl
            if floor == "earth" and (x * 7 + y * 3) % 5 == 0:
                c = (140, 134, 124)
            if floor == "tatami" and (x in (1, 14) or y == 14):
                c = main
            p[x, y] = c + (255,)
    wood, wood_d = (124, 84, 48), (78, 52, 28)
    for x in range(0, 16):   # front fence rails
        p[x, 12] = wood + (255,)
        p[x, 14] = wood_d + (255,)
    for x in (0, 5, 10, 15):  # posts with iron caps
        for y in range(10, 16):
            p[x, y] = wood_d + (255,)
        p[x, 10] = (150, 152, 158, 255)
    for y in range(9, 11):    # back fence
        for x in range(1, 15):
            if y == 9:
                p[x, y] = wood_d + (255,)
    straw, straw_d = (212, 176, 96), (160, 124, 56)
    for y in range(3, 6):     # dummy head
        for x in range(7, 10):
            p[x, y] = straw + (255,)
    for x in range(4, 13):    # arms
        p[x, 6] = straw_d + (255,)
    for y in range(6, 10):    # body
        for x in range(6, 11):
            p[x, y] = (straw if x != 10 else straw_d) + (255,)
    p[7, 8] = p[8, 8] = p[9, 8] = (140, 112, 70, 255)
    for y in range(10, 12):
        p[8, y] = wood_d + (255,)
    if kind == "shield":
        for y in range(5, 9):
            for x in range(11, 15):
                if (x - 12.5) ** 2 + (y - 6.5) ** 2 <= 4.2:
                    p[x, y] = ((164, 42, 36) if (x - 12.5) ** 2 + (y - 6.5) ** 2 > 1.5 else (230, 224, 204)) + (255,)
        for y in range(1, 4):
            for x in range(7, 10):
                p[x, y] = (160, 162, 168, 255)
    for y in range(2, 9):     # banner on the left
        for x in range(1, 4):
            if y < 8 or x == 2:
                p[x, y] = main + (255,)
        p[0, y] = wood_d + (255,)
    p[2, 4] = p[2, 5] = (236, 226, 200, 255) if colour == "red" else (232, 186, 70, 255)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)


def export(root, name, atlas, decor=None, icon=None, particles=None, visible_box=(10, 8, 0)):
    """Writes training/<id>.json (model, texture, decor, extent, colliders), models/entity/<id>.bbmodel,
    blockbench/<id>.bbmodel, textures/entity/<id>.png, textures/item/<id>.png (icon = dict(kind=, colour=, floor=)
    or a function(path)), interiors/<id>_decor.json. TRAINING_OUT=<file.bbmodel>: writes only the model (and its
    atlas next to it) there, for previews."""
    out_model = os.environ.get("TRAINING_OUT")
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
        path = os.path.join(ASSETS, "%s/%s.json" % (GROUP, name))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=1)
        ipath = os.path.join(ASSETS, "textures/item/%s.png" % name)
        if callable(icon):
            icon(ipath)
        else:
            spec = dict(colour=atlas.colour)
            spec.update(icon or {})
            globals()["icon"](ipath, **spec)
    print("%s: %d cubes, extent %s, %d collision boxes, %d mod blocks" % (
        name, len(model["elements"]), ["%.2f" % v for v in ext], len(COLLIDERS), 0 if decor is None else len(decor.blocks)))
    return model


def particle(kind, pos, chance=0.3, count=1):
    """A particle source for export(particles=[...])."""
    return ml.particle(kind, pos, chance=chance, count=count)


def count_cubes(model):
    return len(model["elements"])
