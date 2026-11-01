"""Texture atlas of the workshops of agent B (workshops_b.png, 512x512): the cook, the alchemist and the enchanter.

Minecraft-like (16 px per block on the wood, planks and stone): the same woods as the carts (wood, wood_dark,
plank...), stone bricks, cobble and smooth stone, iron, black iron (the cauldron), copper and brass, fire and embers,
food (apples, bread, garlic, herbs, peppers, stew, cheese), clay jars, books (spines of seven colours, pages,
parchment), potions and crystals (lit), candles, purple cloth and its gold-trimmed valance, purple banners with gold
emblems (star, compass, flask), the purple rug with gold borders, the enchanting altar (dark stone, cyan corners,
cloth with gold points), the golden arcane circle, ivy and vines, and the "Enchanteur" sign (gold letters, book icon).

Every region is (u, v, w, h) in pixels, packed automatically (deterministic order) into REGIONS; shared by
tools/workshops/wslib_b.py and the three generators. Regions drawn with transparent pixels (fire, bunches, ivy,
banners, valance, arcane circle, quill) are cut out in game (the models are drawn with a cutout layer).
Run any generator of agent B to (re)write it (deterministic).
"""
import math
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "tents"))
sys.path.insert(0, os.path.join(HERE, "..", "carts"))
from galley_texture import _rgb, _jitter, _mix, _scale, fine_wood, hammered_iron, twisted_rope, end_grain, paint_lamp_glass, polished_metal, GOLD_STOPS  # noqa: E402,E501
import tent_texture as tt  # noqa: E402
import cart_texture as ct  # noqa: E402

SIZE = 512
NAME = "workshops_b.png"

# (name, w, h) in packing order: big ones first
_LAYOUT = [
    ("cloth_purple", 64, 64), ("rug", 64, 64), ("arcane", 64, 64), ("ivy", 32, 64), ("banner_star", 32, 64),
    ("banner_compass", 32, 64), ("banner_flask", 32, 64), ("sign", 176, 40),
    ("wood", 64, 16), ("wood_dark", 64, 16), ("plank", 64, 16), ("plank_dark", 64, 16), ("wood_purple", 64, 16),
    ("stone_bricks", 64, 32), ("cobble", 32, 32), ("stone_slab", 32, 32), ("altar_stone", 32, 32), ("cauldron", 32, 32),
    ("valance", 64, 16), ("altar_cloth", 64, 24), ("fire", 32, 32), ("embers", 32, 32), ("stew", 16, 16), ("potion_brew", 16, 16),
    ("barrel", 32, 32), ("barrel_top", 32, 32), ("crate", 32, 32), ("chest_front", 32, 16), ("chest_top", 32, 16),
    ("chest_side", 16, 16), ("sack", 32, 32), ("bark", 32, 32), ("log_end", 16, 16), ("apples", 32, 32),
    ("bread", 16, 8), ("bread_top", 16, 8), ("garlic", 16, 32), ("herbs", 16, 32), ("peppers", 16, 32), ("vines", 16, 48),
    ("cheese", 16, 16), ("jar", 16, 16), ("jar_top", 16, 16), ("bowl", 16, 16), ("pages", 32, 16), ("parchment", 16, 16),
    ("quill", 16, 32), ("leather", 16, 16), ("cloth_red", 16, 16), ("linen", 16, 16), ("onion", 8, 8), ("apple", 8, 8),
    ("book_red", 8, 16), ("book_blue", 8, 16), ("book_green", 8, 16), ("book_purple", 8, 16), ("book_brown", 8, 16),
    ("book_teal", 8, 16), ("book_yellow", 8, 16), ("book_top", 8, 16),
    ("potion_green", 8, 8), ("potion_red", 8, 8), ("potion_pink", 8, 8), ("potion_blue", 8, 8), ("potion_purple", 8, 8),
    ("potion_yellow", 8, 8), ("potion_teal", 8, 8), ("potion_orange", 8, 8), ("glass", 8, 8),
    ("crystal_purple", 8, 16), ("crystal_blue", 8, 16), ("diamond", 16, 16), ("wax", 8, 16), ("flame", 8, 8),
    ("end_grain", 16, 16), ("rope", 16, 16), ("iron", 16, 16), ("iron_dark", 16, 16), ("gold", 16, 16), ("copper", 16, 16),
    ("brass", 16, 16), ("lantern", 16, 16), ("glow", 16, 16), ("cork", 8, 8), ("ink", 8, 8), ("feather", 8, 8),
    ("spark", 8, 8), ("leaf", 16, 16), ("clay", 16, 16), ("purple_paint", 16, 16),
]


def _pack(layout, size):
    regions, x, y, row_h = {}, 0, 0, 0
    for name, w, h in layout:
        if x + w > size:
            x, y, row_h = 0, y + row_h, 0
        regions[name] = (x, y, w, h)
        x += w
        row_h = max(row_h, h)
    assert y + row_h <= size, "atlas full"
    return regions


REGIONS = _pack(_LAYOUT, SIZE)

PURPLE = _rgb("5a2a82")
PURPLE_DARK = _rgb("3a1858")
GOLD = _rgb("e0b040")
GOLD_DARK = _rgb("8a6418")
CLEAR = (0, 0, 0, 0)


def _put(px, u, v, x, y, c, a=255):
    px[u + x, v + y] = tuple(c[:3]) + (a,)


def _mottled(img, region, base, rng, dark_k=0.78, light_k=1.15, cell=2, noise=5):
    """Pixel-art cloth / stone mottling: cells of `cell` px, each a little darker or lighter."""
    u, v, w, h = region
    px = img.load()
    for cy in range(0, h, cell):
        for cx in range(0, w, cell):
            r = rng.random()
            k = dark_k if r < 0.18 else light_k if r > 0.88 else 1.0 + rng.uniform(-0.04, 0.04)
            for y in range(cy, min(h, cy + cell)):
                for x in range(cx, min(w, cx + cell)):
                    _put(px, u, v, x, y, _jitter(_scale(base, k), rng, noise))


def _stone_bricks(img, region, rng, base=_rgb("7e7e7a"), course=8, brick=16):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        row = y // course
        off = (brick // 2) * (row % 2)
        for x in range(w):
            bx = (x + off) // brick
            tone = _scale(base, 0.8 + 0.32 * ((bx * 7 + row * 13) % 5) / 4)
            yy, xx = y % course, (x + off) % brick
            if yy == course - 1 or xx == brick - 1:
                c = _scale(base, 0.55)
            elif yy == 0 or xx == 0:
                c = _scale(tone, 1.12)
            else:
                c = _scale(tone, 1.0 + 0.08 * math.sin(x * 1.3 + y * 0.7) * math.sin(y * 0.9))
                if rng.random() < 0.08:
                    c = _scale(c, 0.85)
            _put(px, u, v, x, y, _jitter(c, rng, 5))


def _cobble(img, region, rng, base=_rgb("85857f")):
    u, v, w, h = region
    px = img.load()
    seeds = [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(0.82, 1.12)) for _ in range(w * h // 22)]
    for y in range(h):
        for x in range(w):
            ds = sorted(((math.hypot(x - sx, y - sy), k) for sx, sy, k in seeds))
            d0, k = ds[0]
            d1 = ds[1][0]
            if d1 - d0 < 1.0:
                c = _scale(base, 0.5)
            else:
                c = _scale(base, k * (1.08 if d0 < 1.5 else 1.0))
            _put(px, u, v, x, y, _jitter(c, rng, 6))


def _slab(img, region, rng, base=_rgb("a3a39d")):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            k = 1.0 + 0.05 * math.sin(x * 0.4 + y * 0.3)
            if x in (0, w - 1) or y in (0, h - 1):
                k = 0.72
            elif x == 1 or y == 1:
                k = 1.1
            _put(px, u, v, x, y, _jitter(_scale(base, k), rng, 6))


def _altar_stone(img, region, rng):
    u, v, w, h = region
    px = img.load()
    base = _rgb("2a2032")
    for y in range(h):
        for x in range(w):
            k = 1.0 + 0.25 * (math.sin(x * 0.7 + y * 0.4) * math.sin(y * 0.5 - x * 0.2))
            c = _scale(base, k)
            if rng.random() < 0.06:
                c = _rgb("4a3462")
            if x in (0, w - 1) or y in (0, h - 1):
                c = _scale(base, 0.6)
            _put(px, u, v, x, y, _jitter(c, rng, 4))


def _diamond(img, region, rng):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            d = abs(x - w / 2 + 0.5) + abs(y - h / 2 + 0.5)
            t = d / w
            c = _mix(_rgb("e8ffff"), _rgb("2ab8c0"), min(1.0, t * 1.6))
            if x in (0, w - 1) or y in (0, h - 1):
                c = _rgb("1a7a86")
            if (x + y) % 5 == 0 and t > 0.3:
                c = _scale(c, 0.85)
            _put(px, u, v, x, y, _jitter(c, rng, 4))


def _valance(img, region, rng, points=8):
    """Purple valance with gold-trimmed points hanging down (transparent between the points)."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            ph = (x % points + 0.5) / points            # 0..1 across one point
            depth = h * (1 - abs(ph - 0.5) * 2) * 0.55 + h * 0.42   # cloth reaches lower at the point's middle
            if y >= depth:
                _put(px, u, v, x, y, CLEAR, 0)
                continue
            if y >= depth - 2.2 or y < 2:
                c = _mix(GOLD, _rgb("fff0a0"), 0.25 if (x + y) % 3 == 0 else 0.0)
                if y >= depth - 1.0:
                    c = GOLD_DARK
            else:
                c = _scale(PURPLE, 1.0 + (0.06 if (x // 2 + y // 2) % 2 else -0.05) - 0.12 * (y / h))
            _put(px, u, v, x, y, _jitter(c, rng, 4))


def _altar_cloth(img, region, rng):
    """The altar's cloth: purple with a gold border and three big points at the bottom."""
    u, v, w, h = region
    px = img.load()
    n = 3
    for y in range(h):
        for x in range(w):
            ph = ((x * n / w) % 1.0)
            depth = h * 0.45 + h * 0.55 * (1 - abs(ph - 0.5) * 2)
            if y >= depth:
                _put(px, u, v, x, y, CLEAR, 0)
                continue
            if y >= depth - 3 or y < 2:
                c = GOLD if y < depth - 1 else GOLD_DARK
            elif y < 3:
                c = GOLD_DARK
            else:
                c = _scale(PURPLE, 1.0 + (0.07 if (x // 2 + y // 2) % 2 else -0.05))
                # a small gold diamond in each point
                cx = (math.floor(x * n / w) + 0.5) * w / n
                if abs(x - cx) + abs(y - h * 0.5) < 2.5:
                    c = GOLD
            _put(px, u, v, x, y, _jitter(c, rng, 4))


def _banner(img, region, rng, emblem):
    """A purple banner, gold border inset, pointed bottom (transparent below the V), and a gold emblem."""
    u, v, w, h = region
    px = img.load()
    vee = 10
    for y in range(h):
        for x in range(w):
            tip = h - vee + vee * (1 - abs(x - (w - 1) / 2) / ((w - 1) / 2))
            if y > tip:
                _put(px, u, v, x, y, CLEAR, 0)
                continue
            border = x in (2, 3, w - 3, w - 4) and y >= 2 or y in (2, 3) or (tip - 3.5 < y <= tip - 2)
            c = _scale(PURPLE, 1.0 + (0.06 if (x // 2 + y // 2) % 2 else -0.06) - 0.1 * (y / h))
            if x < 2 or x >= w - 2 or y < 2 or y > tip - 1.2:
                c = _scale(PURPLE_DARK, 1.0)
            elif border and 2 <= x < w - 2:
                c = GOLD
            _put(px, u, v, x, y, _jitter(c, rng, 4))
    cx, cy = (w - 1) / 2, h * 0.43
    if emblem in ("star", "compass"):
        from PIL import ImageDraw
        layer = Image.new("RGBA", (w * 4, h * 4), (0, 0, 0, 0))
        dr = ImageDraw.Draw(layer)
        C = (cx * 4 + 2, cy * 4 + 2)
        if emblem == "compass":
            dr.ellipse([C[0] - 38, C[1] - 38, C[0] + 38, C[1] + 38], outline=GOLD + (255,), width=6)
        pts = []
        for k in range(16):
            a = -math.pi / 2 + k * math.pi / 8
            r = (56 if k % 4 == 0 else 30 if k % 2 == 0 else 10) * (0.85 if emblem == "compass" and k % 4 == 0 else 1.0)
            pts.append((C[0] + r * math.cos(a), C[1] + r * math.sin(a)))
        dr.polygon(pts, fill=GOLD + (255,))
        # the lit half of each point
        for k in range(0, 16, 2):
            a0 = -math.pi / 2 + k * math.pi / 8
            r = 56 if k % 4 == 0 else 30
            if emblem == "compass" and k % 4 == 0:
                r *= 0.85
            a1 = a0 + math.pi / 8
            dr.polygon([C, (C[0] + r * math.cos(a0), C[1] + r * math.sin(a0)), (C[0] + 9 * math.cos(a1), C[1] + 9 * math.sin(a1))],
                       fill=(250, 226, 130, 255))
        dr.ellipse([C[0] - 5, C[1] - 5, C[0] + 5, C[1] + 5], fill=(255, 246, 200, 255))
        small = layer.resize((w, h), Image.BOX)
        sp = small.load()
        for y in range(h):
            for x in range(w):
                c = sp[x, y]
                if c[3] > 110:
                    _put(px, u, v, x, y, _jitter(c[:3], rng, 3))
    elif emblem == "flask":
        for y in range(h):
            for x in range(w):
                dx, dy = x - cx, y - (cy + 4)
                body = math.hypot(dx, dy) < 7.5
                neck = abs(dx) < 2.2 and -14 < dy < -5
                rim = abs(dx) < 3.6 and -15.5 < dy < -13.5
                if body or neck or rim:
                    edge = (abs(math.hypot(dx, dy) - 7.0) < 1.0 and body) or (neck and abs(dx) > 1.2) or rim
                    if edge:
                        c = _rgb("e8e4f0")
                    elif body and dy > -1:
                        c = _mix(_rgb("60d8d0"), _rgb("2a9a98"), (dy + 1) / 8)
                    else:
                        c = _rgb("b8b0d8")
                    _put(px, u, v, x, y, _jitter(c, rng, 3))


def _rug(img, region, rng):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            c = _scale(_rgb("5c2486"), 1.0 + (0.06 if (x // 2 + y // 2) % 2 else -0.05))
            if e < 2:
                c = _rgb("40185e")
            elif e in (3, 4) or e == 8:
                c = GOLD if (x + y) % 6 else _rgb("f2d070")
            elif 4 < e < 8:
                c = _rgb("4a1c6e")
                if (x + y) % 4 == 0:
                    c = GOLD_DARK
            else:
                # inner pattern: a gold lozenge and swirls
                dx, dy = abs(x - w / 2 + 0.5) / (w / 2 - 9), abs(y - h / 2 + 0.5) / (h / 2 - 9)
                d = dx + dy
                if abs(d - 0.75) < 0.05 or abs(d - 0.45) < 0.04:
                    c = GOLD
                elif d < 0.12:
                    c = _rgb("f2d070")
                elif abs(math.sin(x * 0.5) * math.cos(y * 0.5)) > 0.93 and d > 0.85:
                    c = _mix(c, GOLD, 0.6)
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _arcane(img, region, rng):
    """The golden arcane circle: two rings, runes between them, a star of lines and a centre (transparent elsewhere)."""
    u, v, w, h = region
    px = img.load()
    cx, cy = (w - 1) / 2, (h - 1) / 2
    R = w / 2 - 1
    for y in range(h):
        for x in range(w):
            dx, dy = x - cx, y - cy
            r = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            hit = False
            if abs(r - R + 1) < 1.3 or abs(r - R * 0.78) < 0.9 or abs(r - R * 0.3) < 0.9:
                hit = True
            elif R * 0.8 < r < R - 2.5 and (int((a + math.pi) / (2 * math.pi) * 24) % 2 == 0) and (x + y) % 3 != 0:
                hit = True                                   # runes in the band
            elif r < R * 0.78:
                for k in range(6):                            # six spokes (a hexagram of lines)
                    t = a - k * math.pi / 3
                    if abs(r * math.sin(t)) < 0.7 and math.cos(t) > 0:
                        hit = True
                for k in range(3):                            # triangle lines
                    ang = k * 2 * math.pi / 3 + math.pi / 2
                    nx, ny = math.cos(ang), math.sin(ang)
                    if abs(dx * nx + dy * ny - R * 0.39) < 0.7:
                        hit = True
            if r < 2.4:
                hit = True
            if hit and r < R + 0.5:
                c = GOLD if (x + y) % 4 else _rgb("fff0a0")
                _put(px, u, v, x, y, _jitter(c, rng, 3))
            else:
                _put(px, u, v, x, y, CLEAR, 0)


# 5x7 glyphs for the sign's lettering
_GLYPHS = {
    "E": ["#####", "##...", "##...", "####.", "##...", "##...", "#####"],
    "n": [".....", ".....", "####.", "##..#", "##..#", "##..#", "##..#"],
    "c": [".....", ".....", ".###.", "##...", "##...", "##...", ".###."],
    "h": ["##...", "##...", "####.", "##..#", "##..#", "##..#", "##..#"],
    "a": [".....", ".....", ".###.", "....#", ".####", "#...#", ".####"],
    "t": [".##..", ".##..", "####.", ".##..", ".##..", ".##.#", "..##."],
    "e": [".....", ".....", ".###.", "#...#", "#####", "#....", ".###."],
    "u": [".....", ".....", "#..##", "#..##", "#..##", "#..##", ".##.#"],
    "r": [".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."],
}


def _sign(img, region, rng, text="Enchanteur"):
    """The sign's board: purple, a thin gold frame, the book icon at left and the gold lettering (2x pixel font,
    with a dark shadow)."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            c = _scale(PURPLE, 0.92 + (0.06 if (x // 2 + y // 2) % 2 else -0.04))
            if e < 1:
                c = GOLD_DARK
            elif e < 3:
                c = GOLD
            elif e == 3:
                c = _scale(PURPLE_DARK, 0.9)
            _put(px, u, v, x, y, _jitter(c, rng, 3))
    # book icon (open book, gold lines), 26 x 18 at left
    bx, by = 8, h // 2 - 9
    for y in range(18):
        for x in range(26):
            mid = abs(x - 12.5)
            top = 3 + int(mid * 0.18)           # pages curve up from the spine
            bot = 15 + int(mid * 0.1)
            on = False
            if top <= y <= bot and 1 <= x <= 24:
                if y in (top, bot) or x in (1, 24) or abs(x - 12.5) < 0.7:
                    on = True
                elif (y - top) % 3 == 1 and 4 <= mid <= 10:
                    on = True                    # lines of text
                if on:
                    _put(px, u, v, bx + x, by + y, GOLD if (x + y) % 5 else _rgb("fff0a0"))
                else:
                    _put(px, u, v, bx + x, by + y, _scale(PURPLE, 0.75))
    # lettering
    s = 2
    total = sum(5 * s + s for ch in text) - s
    x0 = bx + 26 + max(4, (w - (bx + 26) - total) // 2 - 2)
    y0 = (h - 7 * s) // 2 + 1
    for ch in text:
        g = _GLYPHS[ch]
        for gy, row in enumerate(g):
            for gx, cell in enumerate(row):
                if cell != "#":
                    continue
                for sy in range(s):
                    for sx in range(s):
                        X, Y = x0 + gx * s + sx, y0 + gy * s + sy
                        _put(px, u, v, X + 1, Y + 1, _rgb("1e0c2e"))           # shadow
        for gy, row in enumerate(g):
            for gx, cell in enumerate(row):
                if cell != "#":
                    continue
                for sy in range(s):
                    for sx in range(s):
                        X, Y = x0 + gx * s + sx, y0 + gy * s + sy
                        c = _rgb("fff0b0") if sy == 0 and gy < 3 else GOLD
                        _put(px, u, v, X, Y, c)
        x0 += 5 * s + s


def _fire(img, region, rng):
    """Flames (cut out): tongues rising from the bottom, white-yellow core, orange, red tips."""
    u, v, w, h = region
    px = img.load()
    tongues = [(rng.uniform(2, w - 3), rng.uniform(0.45, 0.95), rng.uniform(2.5, 4.5)) for _ in range(6)]
    for y in range(h):
        for x in range(w):
            t = 1 - y / (h - 1)      # 0 bottom, 1 top
            best = 0.0
            for cx, height, width in tongues:
                hw = width * (1 - t / height) if t < height else 0
                d = abs(x - cx - 1.5 * math.sin(t * 5 + cx))
                if d < hw:
                    best = max(best, 1 - d / max(0.5, hw) * 0.6 - t / height * 0.5)
            if best <= 0:
                _put(px, u, v, x, y, CLEAR, 0)
            else:
                c = _mix(_rgb("c8381a"), _rgb("ffa020"), min(1, best * 1.2))
                if best > 0.75:
                    c = _mix(_rgb("ffd84a"), _rgb("fff8c8"), (best - 0.75) * 3)
                _put(px, u, v, x, y, _jitter(c, rng, 6))


def _embers(img, region, rng):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            r = rng.random()
            c = _rgb("3a1a10") if r < 0.25 else _rgb("ff8a20") if r > 0.82 else _rgb("d84a14") if r > 0.55 else _rgb("8a2a10")
            if r > 0.95:
                c = _rgb("ffe070")
            _put(px, u, v, x, y, c)


def _bunch(img, region, rng, kind):
    """A hanging bunch (cut out): a string at the top, the bunch below (herbs: green sprigs, garlic: white bulbs,
    peppers: red pods)."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            _put(px, u, v, x, y, CLEAR, 0)
    for y in range(0, 6):
        _put(px, u, v, w // 2, y, _rgb("c9ad7a"))
    _put(px, u, v, w // 2 - 1, 5, _rgb("8a6a3a"))
    _put(px, u, v, w // 2 + 1, 5, _rgb("8a6a3a"))
    if kind == "herbs":
        for _ in range(26):
            x0 = w / 2 + rng.uniform(-1, 1)
            ang = rng.uniform(-0.75, 0.75)
            L = rng.uniform(10, h - 6)
            c = rng.choice([_rgb("4a8a2a"), _rgb("5a9a34"), _rgb("3a7020"), _rgb("6aaa3a")])
            for i in range(int(L)):
                x = int(round(x0 + math.sin(ang) * i * 0.8))
                y = 6 + i
                if 0 <= x < w and y < h:
                    _put(px, u, v, x, y, _jitter(c, rng, 8))
                    if i > 4 and i % 3 == 0 and 0 <= x + 1 < w:
                        _put(px, u, v, x + (1 if ang > 0 else -1), y, _jitter(_scale(c, 1.2), rng, 8))
    elif kind in ("garlic", "peppers"):
        items = []
        for i in range(9 if kind == "garlic" else 11):
            y = 9 + i * (h - 13) / (8 if kind == "garlic" else 10)
            x = w / 2 + (2.6 if i % 2 else -2.6) * (0.6 + 0.4 * (i / 8))
            items.append((x, y))
        for x0, y0 in items:
            if kind == "garlic":
                for y in range(int(y0 - 3), int(y0 + 4)):
                    for x in range(int(x0 - 3), int(x0 + 4)):
                        d = math.hypot(x - x0, (y - y0) * 1.1)
                        if d < 3.2 and 0 <= x < w and 0 <= y < h:
                            c = _rgb("f0ead8") if d < 2.2 else _rgb("c8bca0")
                            if x == int(x0) and y < y0:
                                c = _rgb("b8a888")
                            _put(px, u, v, x, y, _jitter(c, rng, 5))
            else:
                for i in range(6):
                    for dx in (-1, 0, 1):
                        x, y = int(x0 + dx * (1 - i / 6)), int(y0 + i)
                        if 0 <= x < w and 0 <= y < h:
                            c = _rgb("d02818") if dx else _rgb("e84a28")
                            _put(px, u, v, x, y, _jitter(c, rng, 8))
                _put(px, u, v, int(x0), int(y0) - 1, _rgb("3a7020"))
        for y in range(6, h - 3):
            _put(px, u, v, w // 2, y, _rgb("a88a5a") if y % 3 else _rgb("8a6a3a"))


def _ivy(img, region, rng, dense=0.5):
    """Ivy / vines (cut out): stems with leaves of several greens."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            _put(px, u, v, x, y, CLEAR, 0)
    stems = max(2, w // 7)
    for s in range(stems):
        x = rng.uniform(1, w - 2)
        L = rng.uniform(h * 0.55, h)
        for y in range(int(L)):
            x += rng.uniform(-0.6, 0.6)
            xi = int(max(0, min(w - 1, x)))
            _put(px, u, v, xi, y, _rgb("4a5a22"))
            if rng.random() < dense:
                cx, cy = xi + rng.choice((-2, 2)), y
                c = rng.choice([_rgb("5a8a2a"), _rgb("6a9e30"), _rgb("4a7a24"), _rgb("7ab038"), _rgb("3a6a1e")])
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        if abs(dx) + abs(dy) < 2 or rng.random() < 0.4:
                            X, Y = cx + dx, cy + dy
                            if 0 <= X < w and 0 <= Y < h:
                                _put(px, u, v, X, Y, _jitter(c, rng, 8))


def _quill(img, region, rng):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            _put(px, u, v, x, y, CLEAR, 0)
    for y in range(h):
        t = y / (h - 1)
        half = 5.5 * math.sin(math.pi * min(1, t * 1.1)) if t < 0.85 else 0
        for x in range(w):
            d = x - w / 2 + 0.5
            if abs(d) < 0.6:
                _put(px, u, v, x, y, _rgb("d8d0c0") if t < 0.85 else _rgb("4a3a2a"))
            elif abs(d) < half and (y + int(abs(d))) % 3 != 0:
                _put(px, u, v, x, y, _jitter(_rgb("f4f0e6") if d < 0 else _rgb("dcd6c8"), rng, 4))


def _pages(img, region, rng):
    """An open book seen from above: two cream pages, lines of writing, a fold in the middle, a glowing tint."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            mid = abs(x - w / 2 + 0.5)
            c = _mix(_rgb("fff4dc"), _rgb("e8d2b0"), min(1, mid / (w / 2)) * 0.5)
            if mid < 1:
                c = _rgb("b89870")
            elif 3 <= mid <= w / 2 - 2 and 2 <= y <= h - 3 and y % 2 == 0 and rng.random() < 0.8:
                c = _rgb("7a4ab0") if rng.random() < 0.3 else _rgb("6a5040")
            if x in (0, w - 1) or y in (0, h - 1):
                c = _rgb("c8b090")
            _put(px, u, v, x, y, c)


def _parchment(img, region, rng):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("e2cc9a"), 0.95 + 0.07 * math.sin(x * 0.6 + y * 0.3))
            if 2 <= x <= w - 3 and y % 3 == 1 and 2 <= y <= h - 3 and rng.random() < 0.75:
                c = _rgb("5a4030")
            if x in (0, w - 1):
                c = _rgb("b89a62")
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _book(img, region, rng, color):
    """A book spine: leather of `color`, two gold bands, darker edges."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            k = 0.78 if x in (0, w - 1) else (1.12 if x == 1 else 1.0)
            c = _scale(color, k)
            if y in (2, 3, h - 4, h - 3):
                c = GOLD if x not in (0, w - 1) else GOLD_DARK
            elif 6 <= y <= h - 7 and x in (3, 4) and y % 3 == 0:
                c = _mix(c, GOLD, 0.6)
            _put(px, u, v, x, y, _jitter(c, rng, 4))


def _book_top(img, region, rng):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = _rgb("ece0c4") if y % 2 else _rgb("d8caa8")
            if x in (0, w - 1):
                c = _rgb("6a3a2a")
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _potion(img, region, rng, color):
    """A potion bottle's body: liquid colour, lighter top-left highlight, darker bottom, a glass rim."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            k = 1.25 - 0.45 * (y / (h - 1))
            c = _scale(color, k)
            if y == 0:
                c = _mix(color, _rgb("e8f0f4"), 0.5)
            if x == 1 and 1 <= y <= h - 3:
                c = _mix(c, (255, 255, 255), 0.55)
            if x in (0, w - 1):
                c = _scale(c, 0.8)
            _put(px, u, v, x, y, c)


def _crystal(img, region, rng, color):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            k = 1.35 - 0.5 * (y / h) + (0.25 if x < w // 2 else -0.05)
            c = _scale(color, k)
            if x == w // 2:
                c = _scale(color, 0.85)
            if y < 2:
                c = _mix(color, (255, 255, 255), 0.6)
            _put(px, u, v, x, y, _jitter(c, rng, 4))


def _wax(img, region, rng):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("efe4c4"), 1.06 - 0.12 * (y / h))
            if y < 3 and (x * 3 + y) % 4 == 0:
                c = _rgb("fff8e0")
            if x in (0, w - 1):
                c = _scale(c, 0.9)
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _flame(img, region, rng):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            d = math.hypot((x - w / 2 + 0.5) * 1.3, (y - h * 0.6))
            c = _rgb("fffbe0") if d < 1.8 else _rgb("ffd040") if d < 3.0 else _rgb("ff9020")
            _put(px, u, v, x, y, c)


def _bread(img, region, rng, top=False):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("c08a40"), 1.05 - 0.2 * (y / h)) if not top else _scale(_rgb("b47a34"), 1.0)
            if top and (x + 2 * y) % 6 == 0:
                c = _rgb("e8c88a")                    # the scored cuts
            _put(px, u, v, x, y, _jitter(c, rng, 6))


def _jar(img, region, rng, top=False):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("b8693a"), 1.08 - 0.18 * (y / h))
            if not top and y in (3, 4):
                c = _rgb("d8c8a0")                   # a cloth band / label
            if top:
                d = math.hypot(x - w / 2 + 0.5, y - h / 2 + 0.5)
                c = _rgb("6a4628") if d < w / 2 - 3 else _scale(_rgb("b8693a"), 0.9)
                if d < w / 2 - 4:
                    c = _rgb("d8c8a0")               # the cloth lid
            _put(px, u, v, x, y, _jitter(c, rng, 5))


def make_texture(path):
    rng = random.Random(2031)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    R = REGIONS
    # wood (same tones as the carts and tents)
    fine_wood(img, R["wood"], _rgb("a07546"), _rgb("5a3c1e"), 8, rng, joints=False, knots=0.25, grain=0.1, shade=0.07)
    fine_wood(img, R["wood_dark"], _rgb("6e4c2c"), _rgb("36220e"), 8, rng, joints=False, knots=0.2, grain=0.1, shade=0.07)
    fine_wood(img, R["plank"], _rgb("9a7044"), _rgb("4e341a"), 4, rng, joints=True, knots=0.2, grain=0.1, shade=0.08)
    fine_wood(img, R["plank_dark"], _rgb("74502e"), _rgb("3a2410"), 4, rng, joints=True, knots=0.15, grain=0.1, shade=0.08)
    fine_wood(img, R["wood_purple"], _rgb("5a3a3e"), _rgb("2a1824"), 4, rng, joints=True, knots=0.1, grain=0.1, shade=0.08)
    end_grain(img, R["end_grain"], _rgb("b08656"), _rgb("5e4022"), rng)
    twisted_rope(img, R["rope"], _rgb("c9ad7a"), _rgb("6e5634"), rng)
    hammered_iron(img, R["iron"], _rgb("4a4a50"), rng)
    hammered_iron(img, R["iron_dark"], _rgb("2a2a2e"), rng)
    hammered_iron(img, R["cauldron"], _rgb("26262a"), rng, dent=0.12)
    polished_metal(img, R["gold"], GOLD_STOPS, rng)
    polished_metal(img, R["copper"], [(0.0, _rgb("6a3418")), (0.4, _rgb("b06030")), (0.8, _rgb("e09058")), (1.0, _rgb("f8c090"))], rng)
    polished_metal(img, R["brass"], [(0.0, _rgb("6a5020")), (0.4, _rgb("a88838")), (0.8, _rgb("d8b860")), (1.0, _rgb("f0dc98"))], rng)
    u, v, w, h = R["lantern"]
    paint_lamp_glass(img.load(), u, v, w, h)
    tt._fill(img, R["glow"], _rgb("ffd27a"), rng, noise=6)
    tt._fill(img, R["purple_paint"], PURPLE, rng, noise=5)
    # stone
    _stone_bricks(img, R["stone_bricks"], rng)
    _cobble(img, R["cobble"], rng)
    _slab(img, R["stone_slab"], rng)
    _altar_stone(img, R["altar_stone"], rng)
    _diamond(img, R["diamond"], rng)
    # cloth
    _mottled(img, R["cloth_purple"], PURPLE, rng)
    _valance(img, R["valance"], rng)
    _altar_cloth(img, R["altar_cloth"], rng)
    _banner(img, R["banner_star"], rng, "star")
    _banner(img, R["banner_compass"], rng, "compass")
    _banner(img, R["banner_flask"], rng, "flask")
    _rug(img, R["rug"], rng)
    _arcane(img, R["arcane"], rng)
    _sign(img, R["sign"], rng)
    tt._weave(img, R["sack"], _rgb("a89060"), rng, seams=0, patches=0, stains=3, tears=1)
    tt._weave(img, R["cloth_red"], _rgb("8f2b22"), rng, seams=0, patches=0, stains=1, tears=0)
    tt._weave(img, R["linen"], _rgb("e0d6c0"), rng, seams=0, patches=0, stains=1, tears=0)
    tt._fill(img, R["leather"], _rgb("6e4a2a"), rng, noise=9)
    # fire
    _fire(img, R["fire"], rng)
    _embers(img, R["embers"], rng)
    _mottled(img, R["stew"], _rgb("9a5a24"), rng, dark_k=0.7, light_k=1.35, cell=2, noise=8)
    _mottled(img, R["potion_brew"], _rgb("58e040"), rng, dark_k=0.8, light_k=1.3, cell=2, noise=8)
    # containers
    ct._barrel(img, R["barrel"], rng)
    ct._barrel_top(img, R["barrel_top"], rng)
    tt._crate(img, R["crate"], rng)
    fine_wood(img, R["chest_front"], _rgb("8e6236"), _rgb("4a3018"), 4, rng, joints=False, knots=0.1, grain=0.1, shade=0.06)
    fine_wood(img, R["chest_top"], _rgb("8e6236"), _rgb("4a3018"), 4, rng, joints=False, knots=0.1, grain=0.1, shade=0.06)
    fine_wood(img, R["chest_side"], _rgb("8e6236"), _rgb("4a3018"), 4, rng, joints=False, knots=0.1, grain=0.1, shade=0.06)
    px = img.load()
    for key in ("chest_front", "chest_top", "chest_side"):
        u, v, w, h = R[key]
        for y in range(h):
            for x in range(w):
                band = x < 2 or x >= w - 2 or (key != "chest_side" and abs(x - w / 2 + 0.5) < 1.5 and key == "chest_top") \
                    or y < 1 or y >= h - 1 or (key == "chest_side" and abs(x - w / 2 + 0.5) < 1.2)
                if band:
                    px[u + x, v + y] = _jitter(_rgb("4a4a50") if (x + y) % 5 else _rgb("8a8a90"), rng, 4) + (255,)
        if key == "chest_front":
            for y in range(4, 11):
                for x in range(w // 2 - 3, w // 2 + 3):
                    c = _rgb("6a6a70") if y in (4, 10) or x in (w // 2 - 3, w // 2 + 2) else _rgb("9a9aa0")
                    if x in (w // 2 - 1, w // 2) and y in (7, 8):
                        c = _rgb("1a1a1a")
                    px[u + x, v + y] = c + (255,)
    ct._bark(img, R["bark"], rng)
    end_grain(img, R["log_end"], _rgb("b89060"), _rgb("5e4022"), rng)
    # food
    ct._produce(img, R["apples"], rng, [_rgb("b8261c"), _rgb("c8321e"), _rgb("9a1c14"), _rgb("d84a2a")], leaf=_rgb("4a7a20"))
    _potion(img, R["apple"], rng, _rgb("c02a1c"))
    _bread(img, R["bread"], rng)
    _bread(img, R["bread_top"], rng, top=True)
    _bunch(img, R["garlic"], rng, "garlic")
    _bunch(img, R["herbs"], rng, "herbs")
    _bunch(img, R["peppers"], rng, "peppers")
    _ivy(img, R["ivy"], rng, dense=0.75)
    _ivy(img, R["vines"], rng, dense=0.6)
    _slab(img, R["cheese"], rng, base=_rgb("e8c050"))
    _jar(img, R["jar"], rng)
    _jar(img, R["jar_top"], rng, top=True)
    fine_wood(img, R["bowl"], _rgb("a87a48"), _rgb("5a3c1e"), 4, rng, joints=False, knots=0.0, grain=0.1, shade=0.05)
    _potion(img, R["onion"], rng, _rgb("c8904a"))
    tt._fill(img, R["clay"], _rgb("a85e34"), rng, noise=6)
    # books, writing
    _pages(img, R["pages"], rng)
    _parchment(img, R["parchment"], rng)
    _quill(img, R["quill"], rng)
    for name, col in (("red", "7a2420"), ("blue", "2a3e7a"), ("green", "2e5a2a"), ("purple", "5a2a7a"), ("brown", "6a4424"),
                      ("teal", "1e5a5a"), ("yellow", "a07a1e")):
        _book(img, R["book_" + name], rng, _rgb(col))
    _book_top(img, R["book_top"], rng)
    # potions, crystals, candles
    for name, col in (("green", "48d040"), ("red", "d02a3a"), ("pink", "e060b0"), ("blue", "3a7ae0"), ("purple", "9a40d8"),
                      ("yellow", "e0c030"), ("teal", "30c8b0"), ("orange", "e07a20")):
        _potion(img, R["potion_" + name], rng, _rgb(col))
    _potion(img, R["glass"], rng, _rgb("b8d0d8"))
    _crystal(img, R["crystal_purple"], rng, _rgb("9a4ae0"))
    _crystal(img, R["crystal_blue"], rng, _rgb("4a8af0"))
    _wax(img, R["wax"], rng)
    _flame(img, R["flame"], rng)
    tt._fill(img, R["cork"], _rgb("a07a4a"), rng, noise=10)
    tt._fill(img, R["ink"], _rgb("141418"), rng, noise=4)
    tt._fill(img, R["feather"], _rgb("f0ece0"), rng, noise=4)
    tt._fill(img, R["spark"], _rgb("d890ff"), rng, noise=10)
    _mottled(img, R["leaf"], _rgb("4a8a2a"), rng, dark_k=0.7, light_k=1.25, cell=2, noise=8)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return img


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/agent_ws_b/workshops_b.png"
    make_texture(out)
    print("wrote", out, len(REGIONS), "regions")
