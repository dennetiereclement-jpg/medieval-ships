"""Props of the bard merchant's tent (tente_barde) and the gunsmith's tent (tente_fusils), agent M4: lutes, a guitar,
mandolins and a fiddle hanging on a plank wall, a big golden harp, drums (red with a gold rope, natural), closed and
open books, music sheets, flutes, quills, a tied curtain, iron-bound chests; muskets and rifles (standing in a rack or
lying), a steampunk revolver with its brass gears, brass cartridges, ammunition boxes, a powder horn, a table runner
with gold dags. register(atlas, which) adds this file's regions (prefix m4_) to the tent's atlas (merchantlib
Atlas.add); the geometry uses merchantlib / tentlib helpers (add_cube, beam, plate, octo, loft).
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402

v3, norm, UP, EYE, X, Z = ml.v3, ml.norm, ml.UP, ml.EYE, ml.X, ml.Z
add_cube, beam, loft, plate, octo = ml.add_cube, ml.beam, ml.loft, ml.plate, ml.octo
ry, rx, rz = ml.ry, ml.rx, ml.rz


# ---------------------------------------------------------------- painting helpers
def _rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _cl(c):
    return tuple(int(max(0, min(255, round(k)))) for k in c[:3])


def _sc(c, k):
    return _cl([v * k for v in c])


def _mix(a, b, t):
    return _cl([a[i] * (1 - t) + b[i] * t for i in range(3)])


def _jit(c, rng, n):
    return _cl([v + rng.randint(-n, n) for v in c])


def _grain(img, base, dark, rng, along="u", streak=0.22, noise=5):
    """Wood: fine grain lines along u (or v)."""
    w, h = img.size
    px = img.load()
    lines = [rng.random() for _ in range(max(w, h))]
    for y in range(h):
        for x in range(w):
            k = y if along == "u" else x
            t = lines[k]
            c = _mix(base, dark, streak * t + 0.08 * math.sin((x if along == "u" else y) * 0.35 + k))
            px[x, y] = _jit(c, rng, noise) + (255,)


def _big(w, h, S=4):
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def _down(img, big):
    from PIL import Image
    img.alpha_composite(big.resize(img.size, Image.LANCZOS))


def _harden(img, cut=110):
    """Cut-out: alpha 0 or 255 (no half-transparent fringe in game)."""
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255 if a >= cut else 0)


SPRUCE = _rgb("d9a861")
SPRUCE_D = _rgb("9c6a32")
WALNUT = _rgb("7a3e1e")
WALNUT_D = _rgb("4a220e")
GOLD = _rgb("e2b048")
GOLD_D = _rgb("8a5c16")
BRASS = _rgb("c89a3a")
STEEL_D = _rgb("3a3c42")
CREAM = _rgb("efe2c0")
INK = _rgb("3a2a1c")


# ---------------------------------------------------------------- bard painters
def paint_lute_face(img, kind="lute"):
    """The front of a lute / guitar / mandolin / fiddle (cut-out silhouette): soundboard, rosette, bridge, a dark
    edge; the neck runs on from the top."""
    w, h = img.size
    big, d = _big(w, h)
    W, H = big.size
    if kind == "guitar":
        top, wood, dark = SPRUCE, SPRUCE_D, _rgb("6a4020")
    elif kind == "fiddle":
        top, wood, dark = _rgb("b0581e"), _rgb("7a3010"), _rgb("401806")
    elif kind == "mandolin":
        top, wood, dark = _rgb("c8803a"), _rgb("8a4a1a"), _rgb("4a2410")
    else:
        top, wood, dark = _rgb("e0b46a"), _rgb("a87436"), _rgb("5a3416")
    e = max(3, W // 22)
    if kind in ("guitar", "fiddle"):
        # figure-of-eight: upper and lower bouts, a waist
        lb = (W * 0.04, H * 0.42, W * 0.96, H * 0.98)
        ub = (W * 0.14, H * 0.08, W * 0.86, H * 0.56)
        for bx in (lb, ub):
            d.ellipse(bx, fill=dark)
        for bx in (lb, ub):
            d.ellipse((bx[0] + e, bx[1] + e, bx[2] - e, bx[3] - e), fill=top)
        d.rectangle((W * 0.26, H * 0.4, W * 0.74, H * 0.6), fill=top)
        if kind == "guitar":
            r = W * 0.17
            cx, cy = W / 2, H * 0.43
            d.ellipse((cx - r - e, cy - r - e, cx + r + e, cy + r + e), fill=_rgb("b07a30"))
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(30, 18, 10))
            d.rectangle((W * 0.3, H * 0.74, W * 0.7, H * 0.8), fill=dark)
        else:
            for sx in (0.32, 0.68):
                d.line([(W * sx, H * 0.42), (W * (sx + (0.06 if sx < 0.5 else -0.06)), H * 0.52), (W * sx, H * 0.62)], fill=(30, 12, 4), width=e)
            d.rectangle((W * 0.44, H * 0.12, W * 0.56, H * 0.66), fill=(36, 22, 16))   # fingerboard
            d.rectangle((W * 0.36, H * 0.68, W * 0.64, H * 0.71), fill=_rgb("d8b878"))  # bridge
    else:
        # pear: an ellipse narrowing towards the neck
        pts = []
        for k in range(48):
            a = 2 * math.pi * k / 48
            x, y = math.sin(a), -math.cos(a)
            wy = 0.5 + 0.5 * y   # 0 top .. 1 bottom
            rr = 0.48 * (0.55 + 0.45 * math.sqrt(max(0.0, wy)))
            pts.append((W / 2 + x * W * rr, H * 0.56 + y * H * 0.43))
        d.polygon(pts, fill=dark)
        inner = [(W / 2 + (px - W / 2) * 0.9, H * 0.56 + (py - H * 0.56) * 0.92) for px, py in pts]
        d.polygon(inner, fill=top)
        r = W * 0.13
        cx, cy = W / 2, H * 0.46
        d.ellipse((cx - r - e, cy - r - e, cx + r + e, cy + r + e), fill=_sc(wood, 0.9))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(34, 20, 10))
        for k in range(8):
            a = k * math.pi / 4
            d.line([(cx, cy), (cx + math.cos(a) * r, cy + math.sin(a) * r)], fill=_sc(wood, 0.8), width=max(1, e // 2))
        d.rectangle((W * 0.32, H * 0.78, W * 0.68, H * 0.82), fill=dark)
    # strings
    for k in range(4):
        x = W * (0.45 + 0.033 * k)
        d.line([(x, 0), (x, H * 0.8)], fill=(236, 226, 196, 200), width=max(1, e // 3))
    _down(img, big)
    _harden(img)


def paint_lute_back(img):
    """The ribbed bowl of a lute (light and dark staves along v)."""
    rng = random.Random(41)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = _rgb("b87a3a") if (x // 3) % 2 == 0 else _rgb("6a3a18")
            if x % 3 == 0:
                c = _sc(c, 0.7)
            px[x, y] = _jit(_sc(c, 0.9 + 0.12 * math.sin(y / h * math.pi)), rng, 5) + (255,)


def paint_harp(img):
    """Gilded wood (the harp's frame): gold with brown grain and darker carved lines."""
    rng = random.Random(42)
    _grain(img, _rgb("e0a83c"), _rgb("8a5a14"), rng, along="u", streak=0.35, noise=6)
    px = img.load()
    w, h = img.size
    for x in range(w):
        px[x, 1] = _rgb("fff0a0") + (255,)
        px[x, h - 2] = _rgb("7a4c10") + (255,)


def paint_strings(img):
    """Harp strings: thin pale lines on a cut-out background (u = across the strings)."""
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            on = x % 3 == 1
            c = (236, 226, 200) if (x // 3) % 7 else (200, 60, 50)   # a red C string every seventh
            px[x, y] = c + ((255,) if on else (0,))


def paint_drum(img, body, rope, hoop):
    """A drum shell: two hoops (top and bottom), the body colour, a zig-zag rope with small leather tensioners."""
    rng = random.Random(43)
    w, h = img.size
    px = img.load()
    hb = max(3, h // 7)
    for y in range(h):
        for x in range(w):
            if y < hb or y >= h - hb:
                c = _sc(hoop, 1.1 if (y in (0, h - 1)) else 0.95)
                if y == hb - 1 or y == h - hb:
                    c = _sc(hoop, 0.6)
            else:
                c = _sc(body, 0.9 + 0.12 * math.sin((x / w) * math.pi * 8))
            px[x, y] = _jit(c, rng, 5) + (255,)
    # the zig-zag rope
    period = w / 6
    for x in range(w):
        f = (x % period) / period
        t = f * 2 if f < 0.5 else 2 - f * 2
        yy = hb + 1 + t * (h - 2 * hb - 3)
        for dy in (-2, -1, 0, 1, 2):
            y = int(round(yy)) + dy
            if hb <= y < h - hb:
                px[x, y] = _jit(rope if abs(dy) < 2 else _sc(rope, 0.6), rng, 6) + (255,)
    for k in range(6):
        x0 = int(k * period + period / 2) - 1
        for x in range(x0, x0 + 3):
            for y in range(h - hb - 4, h - hb):
                if 0 <= x < w:
                    px[x, y] = _jit(_rgb("5a3416"), rng, 4) + (255,)


def paint_skin(img):
    rng = random.Random(44)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            r = math.hypot(x - (w - 1) / 2, y - (h - 1) / 2) / (w / 2)
            c = _mix(_rgb("eadbb4"), _rgb("b89a68"), max(0.0, r - 0.55) * 1.6)
            px[x, y] = _jit(c, rng, 4) + (255,)


def paint_pages(img):
    """An open book seen from above: two cream pages with lines of text and a little red initial, the dark gutter."""
    rng = random.Random(45)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = _mix(CREAM, _rgb("c8b080"), abs(x - w / 2) / (w / 2) * 0.15 + (0.2 if abs(x - w / 2) < 2 else 0))
            if x in (0, w - 1) or y in (0, h - 1):
                c = _rgb("7a1e1e")
            px[x, y] = _jit(c, rng, 3) + (255,)
    for half in (0, 1):
        x0 = 3 + half * (w // 2)
        x1 = x0 + w // 2 - 6
        for y in range(3, h - 2, 2):
            for x in range(x0, x1):
                if rng.random() < 0.75 and not (y < 7 and x < x0 + 3):
                    px[x, y] = _jit(INK, rng, 10) + (255,)
        for y in range(3, 7):
            for x in range(x0, x0 + 3):
                px[x, y] = (170, 36, 30, 255)


def paint_score(img):
    """A sheet of music: cream paper, two staves of five lines, black notes."""
    rng = random.Random(46)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = _jit(_mix(CREAM, _rgb("d8c494"), y / h * 0.3), rng, 3) + (255,)
    for s0 in (2, h // 2 + 1):
        for k in range(5):
            y = s0 + k
            if y < h:
                for x in range(1, w - 1):
                    if k % 2 == 0 or rng.random() < 0.3:
                        px[x, y] = (90, 80, 70, 255)
        for x in range(3, w - 2, 3):
            y = s0 + rng.randint(0, 4)
            if y < h:
                px[x, y] = (20, 16, 12, 255)
                if y - 1 >= 0:
                    px[x + 1 if x + 1 < w else x, y - 1] = (20, 16, 12, 255)


def paint_spines(img):
    """Book spines side by side (red, blue, green, brown, purple), gold bands."""
    rng = random.Random(47)
    w, h = img.size
    px = img.load()
    cols = [_rgb(c) for c in ("8a1e1e", "1e3a7a", "2a5a2a", "6a3a1a", "5a2a7a", "a85a1a", "2a2a2a")]
    x = 0
    k = 0
    while x < w:
        bw = rng.randint(3, 5)
        c = cols[k % len(cols)]
        for xx in range(x, min(w, x + bw)):
            for y in range(h):
                cc = _sc(c, 1.15 if xx == x else (0.75 if xx == x + bw - 1 else 1.0))
                if y in (2, 3, h - 4, h - 3):
                    cc = GOLD
                px[xx, y] = _jit(cc, rng, 5) + (255,)
        x += bw
        k += 1


def paint_cover(img, colour):
    rng = random.Random(48)
    w, h = img.size
    px = img.load()
    c = _rgb(colour)
    for y in range(h):
        for x in range(w):
            cc = c
            if x in (1, w - 2) or y in (1, h - 2):
                cc = GOLD
            px[x, y] = _jit(cc, rng, 5) + (255,)


def paint_flute(img):
    """A wooden recorder (u along it): pale boxwood, dark finger holes, a darker mouthpiece end."""
    rng = random.Random(49)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = _rgb("e2c98e") if x > w * 0.12 else _rgb("8a5a2a")
            if x % (w // 6 or 1) == 0 and x > w * 0.3 and h // 2 - 1 <= y <= h // 2:
                c = (40, 26, 14)
            px[x, y] = _jit(_sc(c, 0.85 + 0.25 * math.sin((y + 0.5) / h * math.pi)), rng, 4) + (255,)


def paint_feather(img):
    """A white quill feather (cut-out), the vane along v, a pale shaft."""
    w, h = img.size
    big, d = _big(w, h)
    W, H = big.size
    pts = [(W / 2, 0), (W * 0.95, H * 0.3), (W * 0.8, H * 0.7), (W / 2, H * 0.78), (W * 0.2, H * 0.7), (W * 0.05, H * 0.3)]
    d.polygon(pts, fill=(244, 240, 230))
    for k in range(1, 9):
        y = H * k / 10
        d.line([(W / 2, y + H * 0.04), (W * 0.1, y - H * 0.02)], fill=(206, 200, 190), width=2)
        d.line([(W / 2, y + H * 0.04), (W * 0.9, y - H * 0.02)], fill=(206, 200, 190), width=2)
    d.line([(W / 2, 0), (W / 2, H)], fill=(220, 210, 180), width=max(2, W // 12))
    _down(img, big)
    _harden(img)


def paint_chest(img, top=False):
    """An iron-bound chest: warm planks, two iron straps, iron corners, a lock plate on the front."""
    rng = random.Random(50 + top)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            plank = (y * 4 // h) if not top else (x * 4 // w)
            c = _sc(_rgb("a8743a"), 0.85 + 0.08 * (plank % 2))
            if (y * 4 % h == 0 and not top) or (top and x * 4 % w == 0):
                c = _rgb("5a3618")
            px[x, y] = _jit(c, rng, 6) + (255,)
    for x0 in (int(w * 0.18), int(w * 0.74)):
        for x in range(x0, x0 + max(2, w // 10)):
            for y in range(h):
                c = _rgb("5a5c62") if (y % 5) else _rgb("9a9ca2")
                px[x, y] = _jit(c, rng, 4) + (255,)
    for y in range(h):
        for x in range(w):
            if min(x, w - 1 - x) < 2 and min(y, h - 1 - y) < 4 or min(y, h - 1 - y) < 2 and min(x, w - 1 - x) < 4:
                px[x, y] = (70, 72, 78, 255)
    if not top:
        for y in range(int(h * 0.15), int(h * 0.55)):
            for x in range(int(w * 0.44), int(w * 0.56)):
                px[x, y] = (_rgb("c8a040") if (x + y) % 5 else (40, 30, 20)) + (255,)


# ---------------------------------------------------------------- gunsmith painters
def paint_walnut(img):
    rng = random.Random(51)
    _grain(img, _rgb("b0642a"), _rgb("6a3412"), rng, along="u", streak=0.45, noise=6)


def paint_gunmetal(img):
    rng = random.Random(52)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = 0.5 + 0.5 * math.sin((y + 0.5) / h * math.pi)
            c = _mix(_rgb("2a2c32"), _rgb("9a9ea6"), t * 0.85)
            px[x, y] = _jit(c, rng, 4) + (255,)


def paint_bright_steel(img):
    rng = random.Random(53)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = 0.5 + 0.5 * math.sin((x + y * 0.5) / w * math.pi * 1.4)
            c = _mix(_rgb("6a6e76"), _rgb("e0e4ea"), t)
            if (x + 2 * y) % 9 == 0:
                c = _rgb("4a4c52")
            px[x, y] = _jit(c, rng, 4) + (255,)


def paint_banner_dark(img):
    """The gunsmith's banner: charcoal cloth, a gold border and V point (cut-out), crossed ivory muskets."""
    rng = random.Random(54)
    w, h = img.size
    px = img.load()
    main, dark = _rgb("34302e"), _rgb("1e1a18")
    body = int(h * 0.74)
    for y in range(h):
        for x in range(w):
            c = _jit(_sc(main, 0.92 + 0.08 * ((x + y) % 2)), rng, 4)
            a = 255
            if y >= body:
                half = (w / 2) * (1 - (y - body) / (h - body))
                dx = abs(x - (w - 1) / 2)
                if dx > half:
                    a = 0
                elif dx > half - 3:
                    c = _jit(GOLD, rng, 10)
            elif x < 3 or x >= w - 3 or y < 3:
                c = _jit(GOLD, rng, 10)
            elif x < 5 or x >= w - 5 or y < 5:
                c = _jit(dark, rng, 4)
            px[x, y] = c + (a,)
    # gold dots along the V edge (as in the picture)
    for k in range(5):
        y = body + int((h - body) * (k + 0.5) / 6)
        half = (w / 2) * (1 - (y - body) / (h - body))
        for sx in (-1, 1):
            x = int((w - 1) / 2 + sx * (half - 6))
            if 0 <= x < w:
                px[x, y] = GOLD + (255,)
    big, d = _big(w - 10, w - 10)
    W = big.size[0]
    ivory, ivory_d, wood = (236, 226, 200), (150, 136, 110), (214, 196, 160)
    for sgn in (1, -1):
        # stock at the bottom corners, muzzle at the top corners
        a, b = (W / 2 - sgn * W * 0.4, W * 0.1), (W / 2 + sgn * W * 0.3, W * 0.78)
        d.line([a, b], fill=ivory_d, width=int(W * 0.085))
        d.line([a, b], fill=ivory, width=int(W * 0.06))
        bx, by = b
        sx = sgn
        stock = [(bx - sx * W * 0.05, by - W * 0.08), (bx + sx * W * 0.2, by + W * 0.15), (bx + sx * W * 0.1, by + W * 0.26),
                 (bx - sx * W * 0.11, by + W * 0.03)]
        d.polygon(stock, fill=wood, outline=ivory_d)
        gx, gy = (a[0] * 0.3 + b[0] * 0.7, a[1] * 0.3 + b[1] * 0.7)
        d.ellipse((gx - W * 0.035, gy, gx + W * 0.035, gy + W * 0.07), outline=ivory_d, width=3)
    from PIL import Image
    small = big.resize((w - 10, w - 10), Image.LANCZOS)
    img.alpha_composite(small, (5, int(h * 0.12)))


def paint_runner(img):
    """The counter runner: deep red, a gold band, a gold fleuron near the top, the bottom cut in square dags edged
    with gold (cut-out) — v runs from the counter top down the front."""
    rng = random.Random(55)
    w, h = img.size
    px = img.load()
    red, red_d = _rgb("7a1a22"), _rgb("4a0e14")
    dag_h = max(4, h // 6)
    for y in range(h):
        for x in range(w):
            c = _jit(_sc(red, 0.9 + 0.1 * ((x * 3 + y) % 4 == 0)), rng, 5)
            a = 255
            lx = x % 8
            tooth = lx < 5
            bottom = h - 1 if tooth else h - dag_h
            if y > bottom:
                a = 0
            elif y >= bottom - 1 or (tooth and y >= h - dag_h and lx in (0, 4)):
                c = _jit(GOLD, rng, 10)
            elif x < 2 or x >= w - 2:
                c = _jit(GOLD, rng, 10)
            elif x < 4 or x >= w - 4:
                c = _jit(red_d, rng, 4)
            elif y == h - dag_h - 3:
                c = _jit(GOLD, rng, 8)
            px[x, y] = c + (a,)
    big, d = _big(16, 12)
    W, H = big.size
    d.polygon([(W / 2, 0), (W * 0.65, H * 0.4), (W, H / 2), (W * 0.65, H * 0.6), (W / 2, H), (W * 0.35, H * 0.6), (0, H / 2),
               (W * 0.35, H * 0.4)], fill=GOLD)
    from PIL import Image
    img.alpha_composite(big.resize((16, 12), Image.LANCZOS), (w // 2 - 8, int(h * 0.35)))
    for k in range(6):
        x, y = rng.randint(6, w - 7), rng.randint(int(h * 0.55), h - dag_h - 5)
        px[x, y] = GOLD + (255,)


def paint_gear(img):
    """A brass cog (cut-out)."""
    w, h = img.size
    big, d = _big(w, h)
    W, H = big.size
    cx, cy = W / 2, H / 2
    pts = []
    for k in range(48):
        a = 2 * math.pi * k / 48
        r = (0.48 if (k // 3) % 2 == 0 else 0.38) * W
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=(200, 154, 58))
    d.ellipse((cx - W * 0.3, cy - W * 0.3, cx + W * 0.3, cy + W * 0.3), fill=(226, 184, 84))
    d.ellipse((cx - W * 0.1, cy - W * 0.1, cx + W * 0.1, cy + W * 0.1), fill=(60, 44, 20))
    _down(img, big)
    _harden(img)


def paint_ammo_box(img):
    """A small brass-cornered ammunition box (dark wood, brass edges and label)."""
    rng = random.Random(56)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = _sc(_rgb("6a4020"), 0.9 + 0.1 * ((y // 3) % 2))
            if min(x, y, w - 1 - x, h - 1 - y) < 2:
                c = BRASS
            if w * 0.3 < x < w * 0.7 and h * 0.35 < y < h * 0.65:
                c = _rgb("d8c08a")
            px[x, y] = _jit(c, rng, 5) + (255,)


def paint_horn(img):
    """A powder horn: ivory to brown along u, brass rings."""
    rng = random.Random(57)
    w, h = img.size
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = _mix(_rgb("e8dcb8"), _rgb("6a4424"), x / w)
            if x % (w // 4) == 0:
                c = BRASS
            px[x, y] = _jit(c, rng, 5) + (255,)


REGIONS = {
    "barde": [
        ("m4_lute", 32, 48, lambda im: paint_lute_face(im, "lute")),
        ("m4_guitar", 32, 48, lambda im: paint_lute_face(im, "guitar")),
        ("m4_mandolin", 32, 48, lambda im: paint_lute_face(im, "mandolin")),
        ("m4_fiddle", 32, 48, lambda im: paint_lute_face(im, "fiddle")),
        ("m4_lute_back", 32, 16, paint_lute_back),
        ("m4_harp", 64, 16, paint_harp),
        ("m4_strings", 48, 48, paint_strings),
        ("m4_drum_red", 64, 32, lambda im: paint_drum(im, _rgb("9a2a24"), _rgb("e2b048"), _rgb("c89a5a"))),
        ("m4_drum_nat", 64, 32, lambda im: paint_drum(im, _rgb("c08a4a"), _rgb("efe2c0"), _rgb("7a4a22"))),
        ("m4_skin", 16, 16, paint_skin),
        ("m4_pages", 32, 16, paint_pages),
        ("m4_score", 16, 16, paint_score),
        ("m4_spines", 32, 16, paint_spines),
        ("m4_cover_red", 16, 16, lambda im: paint_cover(im, "8a1e1e")),
        ("m4_cover_blue", 16, 16, lambda im: paint_cover(im, "243a7a")),
        ("m4_cover_green", 16, 16, lambda im: paint_cover(im, "2a5a2a")),
        ("m4_cover_brown", 16, 16, lambda im: paint_cover(im, "6a3a1a")),
        ("m4_flute", 32, 8, paint_flute),
        ("m4_feather", 16, 32, paint_feather),
        ("m4_chest", 32, 16, paint_chest),
        ("m4_chest_top", 32, 16, lambda im: paint_chest(im, top=True)),
    ],
    "fusils": [
        ("m4_walnut", 64, 16, paint_walnut),
        ("m4_gunmetal", 32, 8, paint_gunmetal),
        ("m4_bright", 16, 16, paint_bright_steel),
        ("m4_banner_dark", 64, 112, paint_banner_dark),
        ("m4_runner", 64, 48, paint_runner),
        ("m4_gear", 16, 16, paint_gear),
        ("m4_ammo", 16, 16, paint_ammo_box),
        ("m4_horn", 32, 8, paint_horn),
        ("m4_chest", 32, 16, paint_chest),
        ("m4_chest_top", 32, 16, lambda im: paint_chest(im, top=True)),
    ],
}


def register(atlas, which, extra=()):
    """Adds the m4_ regions of `which` ("barde" or "fusils") and the (name, w, h, painter) tuples of `extra`."""
    for name, w, h, painter in list(REGIONS[which]) + list(extra):
        atlas.add(name, w, h, painter)


# ---------------------------------------------------------------- geometry helpers
def frame(normal, up=(0, 1, 0)):
    """Axes (side, up, normal) of a thing facing `normal`, `up` projected perpendicular to it."""
    n = norm(v3(*normal))
    u = v3(*up)
    u = norm(u - np.dot(u, n) * n)
    s = np.cross(u, n)
    return np.column_stack([s, u, n])


def ibox(bone, name, center, axes, size, region, stretch=True, **kw):
    return add_cube(bone, name, v3(*center), axes, size, region, stretch=stretch, **kw)


# ---------------------------------------------------------------- bard props
def lute(bone, det, name, center, normal=(0, 0, 1), kind="lute", s=1.0, tilt=0.0, peg_hook=True):
    """A lute / guitar / mandolin / fiddle hanging flat against a wall: `center` = the middle of its body's front,
    facing `normal`; tilt (radians) leans it sideways. The body (cut-out face + a back slightly smaller), the neck,
    the pegbox (bent back for a lute), the strings; a peg above holds it."""
    c = v3(*center)
    up = rz(tilt) @ UP if abs(normal[2]) > 0.5 else rx(tilt) @ UP
    A = frame(normal, up)
    sd, u, n = A[:, 0], A[:, 1], A[:, 2]
    dims = {"lute": (0.46, 0.62, 0.16, 0.5), "guitar": (0.46, 0.66, 0.1, 0.62), "mandolin": (0.3, 0.42, 0.12, 0.34),
            "fiddle": (0.26, 0.42, 0.08, 0.32)}[kind]
    bw, bh, bd, neck = (k * s for k in dims)
    region = {"lute": "m4_lute", "guitar": "m4_guitar", "mandolin": "m4_mandolin", "fiddle": "m4_fiddle"}[kind]
    plate(bone, name, c, bw, bh, region, normal=n, up=u, th=0.012)
    back = "m4_lute_back" if kind in ("lute", "mandolin") else "wood"
    ibox(bone, name + "_bowl", c - n * (bd / 2 + 0.03) - u * bh * 0.04, A, (bw * 0.78, bh * 0.8, bd), back)
    top = c + u * bh * 0.5
    ibox(bone, name + "_neck", top + u * neck / 2 - n * 0.02, A, (0.07 * s, neck, 0.045 * s), "wood_dark")
    head = top + u * neck
    if kind == "lute":
        pb = head + u * 0.06 * s - n * 0.07 * s
        ibox(det, name + "_head", pb, np.column_stack([sd, norm(u - n * 1.1), np.cross(sd, norm(u - n * 1.1))]), (0.08 * s, 0.2 * s, 0.04 * s),
             "wood_dark")
    else:
        ibox(det, name + "_head", head + u * 0.08 * s - n * 0.02, A, (0.09 * s, 0.16 * s, 0.05 * s), "wood_dark")
    if peg_hook:
        beam(det, name + "_peg", head - n * 0.12, head + n * 0.04 + u * 0.03, 0.035, "iron")
    return c


def harp(bone, det, name, foot, yaw=0.0, h=1.75):
    """A big golden floor harp standing on foot: a carved plinth, the slanted soundbox at the back, the curved neck
    on top, the front pillar (column), the strings between them (cut-out plane), the strings' plane facing x."""
    f = v3(*foot)
    R = ry(yaw)

    def P(x, y, z=0.0):
        return f + R @ v3(x, y, z)
    # plinth
    ibox(bone, name + "_plinth", P(0, 0.07, 0), R, (0.62, 0.14, 0.42), {"all": "m4_harp", "+2": "wood_dark"})
    ibox(det, name + "_plinth2", P(0, 0.17, 0), R, (0.5, 0.08, 0.32), "m4_harp")
    # soundbox: from the plinth back up to the top back (the side of the harp towards -x)
    sb0, sb1 = P(-0.12, 0.2, 0), P(-0.34, h * 0.86, 0)
    beam(bone, name + "_soundbox", sb0, sb1, 0.2, {"all": "m4_harp", "+3": "wood", "-3": "wood"}, width=0.16, up=R @ v3(0, 0, 1))
    # the front pillar (a column), slightly bowed
    p0, p1, p2 = P(0.22, 0.2, 0), P(0.27, h * 0.55, 0), P(0.2, h * 0.98, 0)
    beam(bone, name + "_pillar_0", p0, p1, 0.1, "m4_harp", extend=0.02)
    beam(bone, name + "_pillar_1", p1, p2, 0.09, "m4_harp", extend=0.02)
    ibox(det, name + "_pillar_ring", p1, R, (0.14, 0.06, 0.14), "gold")
    # the neck: a curve from the top of the soundbox to the top of the pillar (S-curve, scroll at the soundbox end)
    pts = [P(-0.42, h * 0.92, 0), P(-0.22, h * 0.86, 0), P(-0.02, h * 0.92, 0), P(0.14, h * 1.03, 0), P(0.26, h * 1.02, 0)]
    for k in range(len(pts) - 1):
        beam(bone, "%s_neck_%d" % (name, k), pts[k], pts[k + 1], 0.12, "m4_harp", width=0.08, up=R @ v3(0, 0, 1), extend=0.03)
    octo(det, name + "_scroll", P(-0.46, h * 0.88, -0.05), 0.07, 0.1, "gold", yaw=yaw)
    # strings: a plane between the soundbox and the pillar (the cut-out region draws thin strings)
    a, b = P(-0.15, 0.3, 0), P(0.18, 0.3, 0)
    c_top = P(-0.05, h * 0.93, 0)
    # two quads: lower (rectangle-ish) and upper (narrowing)
    n = R @ v3(0, 0, 1)

    def S(s, t):
        lo = a + (b - a) * s
        hi_l, hi_r = P(-0.3, h * 0.84, 0), P(0.2, h * 0.98, 0)
        hi = hi_l + (hi_r - hi_l) * s
        return hi + (lo - hi) * t
    loft(det, name + "_strings", S, 2, 2, "m4_strings", th=0.004, u_hint=R @ X, v_hint=-UP)
    ml.collide(tuple(np.minimum(P(-0.4, 0, -0.22), P(0.35, h, 0.22))) + tuple(np.maximum(P(-0.4, 0, -0.22), P(0.35, h, 0.22))))
    return c_top


def drum(bone, det, name, foot, r=0.36, h=0.6, kind="red", top_hoop=True):
    """A rope-tensioned drum standing on foot: octagonal shell (red with a gold rope or natural with a pale rope),
    a skin on top, wooden hoops."""
    f = v3(*foot)
    reg = "m4_drum_red" if kind == "red" else "m4_drum_nat"
    octo(bone, name, f, r, h, {"all": reg, "+2": "m4_skin", "-2": "wood_dark"})
    if top_hoop:
        octo(det, name + "_hoop", f + UP * (h - 0.05), r * 1.06, 0.07, {"all": "wood" if kind == "red" else "wood_dark", "+2": "m4_skin"})
    ml.collide((f[0] - r, f[1], f[2] - r, f[0] + r, f[1] + h, f[2] + r))


def chest(bone, det, name, foot, size=(0.8, 0.55, 0.55), yaw=0.0, solid=True):
    """An iron-bound chest: the body, a slightly wider rounded lid (two boxes), the lock."""
    f = v3(*foot)
    R = ry(yaw)
    w, h, d = size
    bh = h * 0.68
    ibox(bone, name, f + UP * bh / 2, R, (w, bh, d), {"all": "m4_chest", "+2": "m4_chest_top", "-2": "plank_dark"})
    ibox(bone, name + "_lid", f + UP * (bh + (h - bh) * 0.4), R, (w + 0.03, (h - bh) * 0.8, d + 0.03),
         {"all": "m4_chest", "+2": "m4_chest_top"})
    ibox(det, name + "_lid_top", f + UP * (h - 0.03), R, (w * 0.98, 0.06, d * 0.7), {"all": "m4_chest_top"})
    ibox(det, name + "_lock", f + R @ v3(0, bh, d / 2 + 0.02), R, (0.1, 0.13, 0.03), "gold")
    if solid:
        ex = abs(math.cos(yaw)) * w / 2 + abs(math.sin(yaw)) * d / 2
        ez = abs(math.sin(yaw)) * w / 2 + abs(math.cos(yaw)) * d / 2
        ml.collide((f[0] - ex, 0.0, f[2] - ez, f[0] + ex, f[1] + h, f[2] + ez))


def book(bone, name, foot, size=(0.2, 0.06, 0.28), yaw=0.0, cover="m4_cover_red"):
    """A closed book lying on foot (pages on the sides, the cover on top and bottom)."""
    f = v3(*foot)
    w, h, d = size
    ibox(bone, name, f + UP * h / 2, ry(yaw), size, {"all": "white", "+2": cover, "-2": cover, "-1": cover})


def book_row(bone, name, x0, x1, y, z, h=0.26, depth=0.2, normal=(0, 0, 1)):
    """Books standing in a row (one box, their spines towards `normal`)."""
    n = norm(v3(*normal))
    c = v3((x0 + x1) / 2, y + h / 2, z)
    side = norm(np.cross(UP, n))
    A = np.column_stack([side, UP, n])
    ibox(bone, name, c, A, (abs(x1 - x0), h, depth), {"all": "white", "+3": "m4_spines", "+2": "m4_cover_brown"}, u_dir=side, v_dir=-UP)


def open_book(bone, det, name, center, normal=(0, 0.5, 1), w=0.56, d=0.4, cover="m4_cover_red"):
    """An open book lying on a slope facing `normal`: two page blocks in a shallow V, the cover under them."""
    c = v3(*center)
    n = norm(v3(*normal))
    side = norm(np.cross(UP, n)) if abs(n[1]) < 0.99 else X
    side = -side
    up = np.cross(n, side)
    A = np.column_stack([side, up, n])
    ibox(bone, name + "_cover", c - n * 0.02, A, (w + 0.04, d + 0.04, 0.02), cover)
    for k, sx in enumerate((-1, 1)):
        Rk = A @ ry(sx * 0.08)
        ibox(bone, "%s_pages_%d" % (name, k), c + side * sx * w / 4 + n * 0.012, Rk, (w / 2, d, 0.035),
             {"all": "white"}, stretch=True)
    plate(det, name + "_text", c + n * 0.032, w * 0.98, d * 0.96, "m4_pages", normal=n, up=up, th=0.004)


def lectern(bone, det, name, foot, yaw=0.0, h=1.15):
    """A small reading stand on the floor or a counter: a post, a sloped board; returns (centre, normal) of the board."""
    f = v3(*foot)
    R = ry(yaw)
    ibox(bone, name + "_foot", f + UP * 0.03, R, (0.34, 0.06, 0.3), "wood_dark")
    ibox(bone, name + "_post", f + UP * h / 2, R, (0.08, h, 0.08), "wood_dark")
    n = R @ norm(v3(0, 1.0, 0.75))
    c = f + UP * (h + 0.05)
    side = R @ X
    up = np.cross(n, side)
    ibox(bone, name + "_board", c, np.column_stack([side, up, n]), (0.5, 0.36, 0.04), "plank")
    return c + n * 0.03, n


def flutes(bone, name, center, n=6, r=0.16, length=0.7, spread=0.12, seed=0, feather=False):
    """A bundle of recorders / flutes (or quills) standing in a barrel / pot: thin rods fanning out a little."""
    rng = random.Random(seed)
    c = v3(*center)
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.3, 0.3)
        rr = r * (0.3 + 0.7 * ((k * 7) % n) / n)
        base = c + v3(math.cos(a) * rr, 0, math.sin(a) * rr)
        tipd = norm(v3(math.cos(a) * spread, 1, math.sin(a) * spread))
        L = length * rng.uniform(0.8, 1.05)
        if feather:
            beam(bone, "%s_%d" % (name, k), base, base + tipd * L * 0.5, 0.025, "white")
            plate(bone, "%s_vane_%d" % (name, k), base + tipd * L * 0.72, 0.1, L * 0.45, "m4_feather",
                  normal=v3(math.cos(a + 1.2), 0, math.sin(a + 1.2)), up=tipd, th=0.006)
        else:
            beam(bone, "%s_%d" % (name, k), base, base + tipd * L, 0.045, {"all": "m4_flute"}, up=v3(math.cos(a), 0, math.sin(a)), stretch=True)
            beam(bone, "%s_bell_%d" % (name, k), base + tipd * (L - 0.04), base + tipd * (L + 0.02), 0.065, "white")


def curtain(bone, name, top_a, top_b, tie, bottom_y=0.05, region="canvas", region_back=None, nx=3, flare=0.25):
    """A side curtain hanging from the bar top_a-top_b, gathered at `tie` (a point at about a third of its height),
    flaring again below; a rope band at the tie."""
    A, B, T = v3(*top_a), v3(*top_b), v3(*tie)
    ty = T[1]

    def P(s, t):
        y = A[1] + (bottom_y - A[1]) * t
        top = A + (B - A) * s
        # above the tie the cloth narrows from the full bar to the tie point; below it flares again a little
        tt = (A[1] - y) / max(1e-6, A[1] - ty)
        if tt <= 1.0:
            k = tt ** 1.3
            p = top * (1 - k) + (T + (B - A) * (s - 0.5) * 0.12) * k
        else:
            k = (tt - 1.0) / max(1e-6, (A[1] - bottom_y) / (A[1] - ty) - 1.0)
            p = T + (B - A) * (s - 0.5) * (0.12 + flare * k)
        p = v3(p[0], y, p[2])
        p = p + v3(0, 0, 0.03 * math.sin(s * math.pi * 3))
        return p
    loft(bone, name, P, nx, 4, region, th=0.03, u_hint=norm(B - A), v_hint=-UP)
    octo(bone, name + "_tie", T - UP * 0.06, 0.09, 0.12, "rope")


# ---------------------------------------------------------------- gunsmith props
def rifle(bone, det, name, butt, d, side, length=1.6, kind="musket", w=1.0):
    """A long gun from its butt point along d: the butt stock and wrist (walnut), the lock (steel), the trigger guard
    (brass), the forestock, the barrel (dark steel, on top of the stock), brass bands. `side` = the direction of the
    trigger guard (the gun's underside); the flat side faces d x side; w scales the cross-sections."""
    b = v3(*butt)
    d = norm(v3(*d))
    g = norm(v3(*side) - np.dot(v3(*side), d) * d)
    f = np.cross(d, g)
    A = np.column_stack([g, d, f])
    L = length
    wood = "m4_walnut"
    # butt: wide at the end, tapering to the wrist (two boxes)
    ibox(bone, name + "_butt", b + d * L * 0.09 + g * 0.04 * w, A, (0.17 * w, L * 0.18, 0.065 * w), wood)
    ibox(bone, name + "_wrist", b + d * L * 0.24, A, (0.085 * w, L * 0.14, 0.06 * w), wood)
    ibox(det, name + "_buttplate", b + d * 0.01 + g * 0.04 * w, A, (0.175 * w, 0.025, 0.07 * w), "brass")
    ibox(bone, name + "_lock", b + d * L * 0.34 - g * 0.005 * w, A, (0.085 * w, L * 0.07, 0.08 * w), "m4_bright" if kind == "rifle" else "steel")
    ibox(det, name + "_guard", b + d * L * 0.3 + g * 0.065 * w, A, (0.04 * w, L * 0.07, 0.03 * w), "brass")
    # forestock and barrel
    ibox(bone, name + "_fore", b + d * L * 0.58, A, (0.06 * w, L * 0.42, 0.056 * w), wood)
    ibox(bone, name + "_barrel", b + d * L * 0.67 - g * 0.035 * w, A, (0.036 * w, L * 0.66, 0.036 * w), "m4_gunmetal")
    for k, t in enumerate((0.55, 0.78)):
        ibox(det, "%s_band_%d" % (name, k), b + d * L * t - g * 0.012 * w, A, (0.078 * w, 0.03, 0.066 * w), "brass")
    if kind == "rifle":
        ibox(det, name + "_sight", b + d * L * 0.4 - g * 0.065 * w, A, (0.03 * w, L * 0.06, 0.03 * w), "m4_bright")


def revolver(bone, det, name, center, yaw=0.0, s=1.0, long_barrel=0.0):
    """A steampunk revolver lying on its side on a counter: walnut grip, steel frame, a fat cylinder, a long barrel
    with a rib, brass gears and a pipe on the side (centre = middle of the frame at the counter top)."""
    c = v3(*center)
    R = ry(yaw)

    def P(x, y, z=0.0):
        return c + R @ (v3(x, y, z) * s)
    ibox(bone, name + "_frame", P(0, 0.11, 0), R, (0.26 * s, 0.16 * s, 0.11 * s), "m4_bright")
    ibox(bone, name + "_cyl", P(0.05, 0.14, 0), R @ rx(math.pi / 4)[:3, :3], (0.16 * s, 0.13 * s, 0.13 * s), "m4_gunmetal")
    ibox(bone, name + "_grip", P(-0.2, 0.08, 0), R @ rz(0.5)[:3, :3], (0.22 * s, 0.1 * s, 0.09 * s), "m4_walnut")
    bl = 0.42 + long_barrel
    ibox(bone, name + "_barrel", P(0.13 + bl / 2, 0.16, 0), R, (bl * s, 0.06 * s, 0.06 * s), "m4_gunmetal")
    ibox(det, name + "_rib", P(0.13 + bl / 2, 0.205, 0), R, (bl * s, 0.03 * s, 0.03 * s), "brass")
    ibox(det, name + "_hammer", P(-0.1, 0.22, 0), R @ rz(-0.4)[:3, :3], (0.04 * s, 0.08 * s, 0.03 * s), "steel")
    ibox(det, name + "_guard", P(-0.03, 0.03, 0), R, (0.1 * s, 0.03 * s, 0.03 * s), "brass")
    # gears on the side towards the viewer (+z turned by yaw), a brass pipe
    n = R @ Z
    A = np.column_stack([R @ X, UP, n])
    for k, (x, y, r) in enumerate(((-0.04, 0.12, 0.12), (0.1, 0.06, 0.08))):
        add_cube(det, "%s_gear_%d" % (name, k), P(x, y, 0.062), A, (r * s, r * s, 0.01), {"all": None, "+3": "m4_gear", "-3": "m4_gear"},
                 stretch=True)
    beam(det, name + "_pipe", P(-0.12, 0.2, 0.05), P(0.13, 0.2, 0.05), 0.03, "brass")


def cartridges(bone, name, foot, n=4, step=0.09, h=0.24, yaw=0.0):
    """Big brass cartridges / shells standing in a row (brass case, darker tip)."""
    f = v3(*foot)
    R = ry(yaw)
    for k in range(n):
        p = f + R @ v3((k - (n - 1) / 2) * step, 0, 0)
        add_cube(bone, "%s_%d" % (name, k), p + UP * h * 0.4, EYE, (0.06, h * 0.8, 0.06), "brass")
        add_cube(bone, "%s_tip_%d" % (name, k), p + UP * h * 0.9, EYE, (0.045, h * 0.2, 0.045), "gold" if k % 2 else "black_iron")


def ammo_box(bone, name, foot, size=(0.34, 0.16, 0.24), yaw=0.0, lid=True):
    f = v3(*foot)
    R = ry(yaw)
    ibox(bone, name, f + UP * size[1] / 2, R, size, {"all": "m4_ammo", "+2": "m4_ammo"})
    if lid:
        ibox(bone, name + "_lid", f + UP * (size[1] + 0.015), R, (size[0] + 0.02, 0.03, size[2] + 0.02), "brass")


def powder_horn(bone, name, hook, length=0.42):
    """A powder horn hanging from a strap at `hook`: a curved horn (3 tapering pieces), a brass cap and spout."""
    h = v3(*hook)
    pts = [h + v3(-0.15, -0.35, 0.03), h + v3(-0.02, -0.5, 0.03), h + v3(0.12, -0.45, 0.03), h + v3(0.2, -0.3, 0.03)]
    for k, w in enumerate((0.14, 0.11, 0.07)):
        beam(bone, "%s_%d" % (name, k), pts[k], pts[k + 1], w, "m4_horn", extend=0.02, stretch=True)
    beam(bone, name + "_strap_0", h, pts[0], 0.025, "leather")
    beam(bone, name + "_strap_1", h, pts[3], 0.025, "leather")
