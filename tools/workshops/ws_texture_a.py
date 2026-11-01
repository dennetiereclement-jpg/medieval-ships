"""Texture atlas of the workshops of agent A (workshops_a.png, 256x256): the blacksmith, the leatherworker, the
tailor and the engineer, Minecraft-like (16 px per block on the planks and the stone).

Wood, dark wood, planks, end grain, rope, iron, gold, lantern glass (the lanterns are rebuilt lit by
tools/lanterns.py), forge stone bricks and the darker hood stone, cobble, fire (transparent flame tongues, drawn full
bright), embers, black iron (anvil), chain links, steel, brass, copper, water, coal, a red-hot ingot, leather (light,
dark, a reddish drape with a ragged edge), a stretched hide (transparent outline with lacing holes), cloths (white,
blue, red, linen) and their ragged hanging versions, cloth roll ends, warp threads (transparent between the threads),
the woven blue and white cloth, the blue runner with its gold fringe, a linen tunic, a leather jacket, iron-banded
crate and chest, barrel, metal crate, brass box with a gear emblem, brass gear (transparent between the teeth),
blueprint, parchment, herbs, thread spools, sack, straw.

Every region is (u, v, w, h) in pixels; REGIONS is shared by tools/workshops/wslib_a.py and the four generators.
Deterministic: run any of the four generators to (re)write it.
"""
import math
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "tents"))
from galley_texture import _rgb, _jitter, _mix, _scale, fine_wood, hammered_iron, twisted_rope, end_grain, paint_lamp_glass, polished_metal  # noqa: E402
import tent_texture as tt  # noqa: E402

SIZE = 256
NAME = "workshops_a.png"

REGIONS = {
    # wood (16 px per block, grain along u)
    "wood":         (0, 0, 64, 16),
    "wood_dark":    (64, 0, 64, 16),
    "plank":        (128, 0, 64, 16),
    "plank_dark":   (192, 0, 64, 16),
    # small materials
    "end_grain":    (0, 16, 16, 16),
    "rope":         (16, 16, 16, 16),
    "iron":         (32, 16, 16, 16),
    "gold":         (48, 16, 16, 16),
    "lantern":      (64, 16, 16, 16),
    "glow":         (80, 16, 16, 16),
    "brass":        (96, 16, 16, 16),
    "copper":       (112, 16, 16, 16),
    "black_iron":   (128, 16, 16, 16),
    "chain":        (144, 16, 16, 16),   # one link (transparent outside and inside the ring)
    "steel":        (160, 16, 16, 16),
    "white":        (176, 16, 16, 16),
    "water":        (192, 16, 16, 16),
    "coal":         (208, 16, 16, 16),
    "embers":       (224, 16, 16, 16),   # glowing coals (drawn full bright)
    "red_hot":      (240, 16, 16, 16),   # a red-hot iron bar
    # stone
    "stone":        (0, 32, 64, 64),     # forge bricks
    "stone_dark":   (64, 32, 64, 64),    # hood and chimney, darker rough stone
    "hide":         (128, 32, 64, 64),   # the stretched hide (transparent outline)
    "fire":         (192, 32, 32, 32),   # flame tongues (transparent)
    "cobble":       (224, 32, 32, 32),
    "fire_back":    (192, 64, 32, 32),   # the glowing back of the hearth
    "stone_top":    (224, 64, 32, 32),   # smooth slab top
    # leather and cloth
    "leather":      (0, 96, 32, 32),
    "leather_dark": (32, 96, 32, 32),
    "leather_red":  (64, 96, 32, 32),
    "cloth_white":  (96, 96, 32, 32),
    "cloth_blue":   (128, 96, 32, 32),
    "cloth_red":    (160, 96, 32, 32),
    "linen":        (192, 96, 32, 32),
    "sack":         (224, 96, 32, 32),
    # furniture
    "crate":        (0, 128, 32, 32),    # iron-banded crate side
    "crate_top":    (32, 128, 32, 32),
    "chest":        (64, 128, 32, 32),   # chest front: bands and a lock plate
    "barrel":       (96, 128, 32, 32),
    "barrel_top":   (128, 128, 32, 32),
    "blueprint":    (160, 128, 32, 32),
    "parchment":    (192, 128, 32, 32),
    "warp":         (224, 128, 32, 32),  # loom warp threads (transparent between)
    # hanging and woven cloth
    "woven":        (0, 160, 32, 32),    # blue and white woven cloth
    "runner":       (32, 160, 32, 32),   # blue runner, gold band, gold fringe at the bottom (transparent tassels)
    "drape":        (64, 160, 32, 32),   # reddish leather drape, ragged bottom
    "rag_white":    (96, 160, 32, 32),   # white hanging cloth, ragged bottom
    "rag_blue":     (128, 160, 32, 32),  # blue hanging cloth, ragged bottom
    "roll_blue":    (160, 160, 16, 16),  # cloth roll ends (spiral)
    "roll_white":   (176, 160, 16, 16),
    "roll_red":     (160, 176, 16, 16),
    "roll_beige":   (176, 176, 16, 16),
    "gear":         (192, 160, 32, 32),  # brass gear (transparent between the teeth and in the holes)
    "gear_iron":    (224, 160, 32, 32),
    "tunic":        (0, 192, 32, 32),
    "jacket":       (32, 192, 32, 32),
    "metal_crate":  (64, 192, 32, 32),
    "brass_box":    (96, 192, 32, 32),
    "herbs":        (128, 192, 32, 32),
    "spools":       (160, 192, 32, 32),
    "straw":        (192, 192, 32, 32),
    "rag_grey":     (224, 192, 32, 32),
    "books":        (0, 224, 32, 32),
    "hide_light":   (32, 224, 32, 32),
    "leather_tan":  (64, 224, 32, 32),
    "bread":        (96, 224, 32, 32),
    "pot_green":    (128, 224, 32, 32),
    "ingot":        (160, 224, 16, 16),
    "glass":        (176, 224, 16, 16),
    "candle":       (160, 240, 16, 16),
    "flame":        (176, 240, 16, 16),
    "slate":        (192, 224, 32, 32),
    "hide_frame":   (224, 224, 32, 32),
}


def _put(px, u, v, x, y, c, a=255):
    px[u + x, v + y] = tuple(int(max(0, min(255, k))) for k in c) + (a,)


def _bricks(img, region, base, mortar, rng, row_h=(5, 7), brick_w=(6, 13), bevel=0.14, tint=0.1):
    """Minecraft-like irregular stone bricks: rows of different heights, bricks of different widths, each brick
    its own tone (some browner), lit top-left edges, dark bottom-right, dark mortar, a few cracks."""
    u, v, w, h = region
    px = img.load()
    y = 0
    while y < h:
        rh = min(h - y, rng.randint(*row_h))
        x = -rng.randint(0, brick_w[1] - 1)
        while x < w:
            bw = rng.randint(*brick_w)
            tone = _scale(base, rng.uniform(0.82, 1.14))
            if rng.random() < tint:
                tone = _mix(tone, _rgb("7a6450"), 0.35)
            for yy in range(y, y + rh):
                for xx in range(max(0, x), min(w, x + bw)):
                    lx, ly = xx - x, yy - y
                    if ly == rh - 1 or lx == bw - 1:
                        c = mortar
                    else:
                        k = 1.0
                        if ly == 0 or lx == 0:
                            k += bevel
                        elif ly == rh - 2 or lx == bw - 2:
                            k -= bevel * 0.7
                        k += 0.05 * math.sin(lx * 1.3 + ly * 2.1 + x)
                        c = _jitter(_scale(tone, k), rng, 6)
                    _put(px, u, v, xx, yy, c)
            if rng.random() < 0.18 and bw > 6 and rh > 3:   # a crack
                cx = max(0, x) + rng.randint(1, max(1, min(w - 1, x + bw - 2) - max(0, x)))
                for yy in range(y + 1, y + rh - 1):
                    cx2 = min(w - 1, max(0, cx + rng.choice((-1, 0, 0, 1))))
                    _put(px, u, v, cx2, yy, _scale(mortar, 1.1))
            x += bw
        y += rh


def _cobble(img, region, base, rng, n=16):
    """Cobblestone: rounded stones (nearest-centre cells), each lit on its upper left, dark gaps between."""
    u, v, w, h = region
    px = img.load()
    pts = [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(0.8, 1.15)) for _ in range(n)]
    for y in range(h):
        for x in range(w):
            ds = []
            for cx, cy, t in pts:
                dx = min(abs(x - cx), w - abs(x - cx))
                dy = min(abs(y - cy), h - abs(y - cy))
                ds.append((math.hypot(dx, dy), cx, cy, t))
            ds.sort()
            d0, cx, cy, t = ds[0]
            edge = ds[1][0] - d0
            if edge < 1.0:
                c = _scale(base, 0.5)
            else:
                k = t * (1.0 + 0.12 * ((cx - x) + (cy - y)) / 6.0)
                c = _scale(base, k)
            _put(px, u, v, x, y, _jitter(c, rng, 6))


def _fire(img, region, rng):
    """Flame tongues rising from the bottom: white-yellow cores, orange, red tips; transparent elsewhere."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = (0, 0, 0, 0)
    tongues = [(rng.uniform(1, w - 2), rng.uniform(0.45, 0.95) * h, rng.uniform(2.2, 4.2)) for _ in range(9)]
    for y in range(h):
        for x in range(w):
            best = 0.0
            for cx, th, hw in tongues:
                t = (h - y) / th
                if t > 1:
                    continue
                half = hw * (1 - t) ** 0.7 * (0.9 + 0.2 * math.sin(y * 0.7 + cx))
                dx = abs(x + 0.5 - cx - 1.2 * math.sin(t * 3 + cx))
                if dx < half:
                    best = max(best, (1 - dx / max(0.5, half)) * (1 - t * 0.6))
            if best > 0.05:
                c = _rgb("fff6c8") if best > 0.72 else _rgb("ffd04a") if best > 0.5 else _rgb("ff9a22") if best > 0.28 else _rgb("e0521a")
                _put(px, u, v, x, y, _jitter(c, rng, 6))


def _embers(img, region, rng):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            n = math.sin(x * 1.7 + y * 0.9) * math.sin(y * 1.3 - x * 0.6) + rng.uniform(-0.35, 0.35)
            c = _rgb("ffe08a") if n > 0.75 else _rgb("ff9c2a") if n > 0.25 else _rgb("c4401a") if n > -0.3 else _rgb("4a1e10")
            _put(px, u, v, x, y, _jitter(c, rng, 8))


def _fire_back(img, region, rng):
    """The back and sides of a lit hearth: soot-black bricks lit orange from below."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = y / (h - 1)
            c = _mix(_rgb("2a1a14"), _rgb("e0782a"), t ** 1.6)
            if y % 6 == 5 or (x + (y // 6) * 5) % 9 == 8:
                c = _scale(c, 0.55)
            _put(px, u, v, x, y, _jitter(c, rng, 7))


def _coal(img, region, rng):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            k = 0.7 + 0.5 * abs(math.sin(x * 1.9 + y * 1.1) * math.cos(y * 1.4 - x * 0.5))
            _put(px, u, v, x, y, _jitter(_scale(_rgb("2c2a2a"), k), rng, 6))


def _chain(img, region, rng):
    """One oval chain link: an iron ring (transparent outside and in the middle)."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            dx, dy = (x + 0.5 - w / 2) / (w * 0.42), (y + 0.5 - h / 2) / (h * 0.48)
            r = math.hypot(dx, dy)
            if 0.4 < r < 1.0:
                k = 1.2 if dx < 0 and dy < 0 else 0.85
                _put(px, u, v, x, y, _jitter(_scale(_rgb("4a4a50"), k), rng, 5))
            else:
                px[u + x, v + y] = (0, 0, 0, 0)


def _hide(img, region, rng, base, holes=True):
    """A stretched animal hide: an irregular outline with four leg lobes, a neck and a tail (transparent outside),
    darker edges, lacing holes along the border."""
    u, v, w, h = region
    px = img.load()
    cx, cy = w / 2, h / 2

    def radius(a):
        r = 0.3 + 0.03 * math.sin(a * 7 + 0.5) + 0.02 * math.sin(a * 13)
        for la in (0.6, math.pi - 0.6, math.pi + 0.75, -0.75):                           # the four legs
            d = math.atan2(math.sin(a - la), math.cos(a - la))
            r += 0.19 * math.exp(-(d / 0.16) ** 2)
        for la, amp in ((-math.pi / 2, 0.14), (math.pi / 2, 0.1)):                       # neck and tail
            d = math.atan2(math.sin(a - la), math.cos(a - la))
            r += amp * math.exp(-(d / 0.15) ** 2)
        for k in range(9):                                                                # small scallops
            la = 2 * math.pi * k / 9 + 0.3
            d = math.atan2(math.sin(a - la), math.cos(a - la))
            r += 0.025 * math.exp(-(d / 0.08) ** 2)
        return r * w
    for y in range(h):
        for x in range(w):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            a = math.atan2(dy, dx)
            rr, R = math.hypot(dx, dy), radius(a)
            if rr > R:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            t = rr / R
            k = 1.08 - 0.25 * t ** 3 + 0.05 * math.sin(x * 0.4) * math.sin(y * 0.3)
            if t > 0.93:
                k *= 0.72
            c = _scale(base, k)
            if rng.random() < 0.06:
                c = _scale(c, 0.9)
            _put(px, u, v, x, y, _jitter(c, rng, 4))
    if holes:
        for i in range(28):
            a = 2 * math.pi * i / 28
            R = radius(a) - 3.2
            x, y = int(cx + R * math.cos(a)), int(cy + R * math.sin(a))
            if 0 <= x < w and 0 <= y < h:
                _put(px, u, v, x, y, _rgb("2a1a0e"))


def _gear(img, region, rng, stops, teeth=12):
    """A gear seen face on: toothed rim, a ring of holes between the spokes, a hub; transparent outside / holes."""
    u, v, w, h = region
    px = img.load()
    cx, cy = w / 2, h / 2
    for y in range(h):
        for x in range(w):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(dx, dy) / (w / 2)
            a = math.atan2(dy, dx)
            tooth = (math.cos(a * teeth) > 0.1)
            outer = 0.98 if tooth else 0.82
            if r > outer:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            hole = 0.32 < r < 0.62 and math.cos(a * 5) > 0.35
            if hole or r < 0.1:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            t = 0.5 + 0.35 * math.sin(a * 2 + 0.6) - (0.25 if 0.7 < r < 0.78 else 0) + (0.2 if 0.12 < r < 0.22 else 0)
            from galley_texture import _ramp
            _put(px, u, v, x, y, _jitter(_ramp(stops, max(0, min(1, t))), rng, 4))


BRASS_STOPS = [(0.0, (92, 62, 20)), (0.3, (150, 106, 36)), (0.55, (196, 148, 56)), (0.8, (228, 190, 96)), (1.0, (246, 222, 150))]
IRON_STOPS = [(0.0, (40, 40, 44)), (0.4, (70, 70, 76)), (0.7, (104, 104, 110)), (1.0, (150, 150, 156))]
COPPER_STOPS = [(0.0, (90, 40, 22)), (0.35, (150, 72, 38)), (0.65, (196, 106, 60)), (0.9, (226, 150, 100)), (1.0, (240, 186, 140))]


def _banded(img, region, wood, dark, rng, bands=(0, 1, 2, 13, 14, 15, 29, 30, 31), rivets=True, vertical_bands=(0, 1, 30, 31)):
    """Wood (vertical planks) with dark iron bands (rows `bands`, columns vertical_bands) and rivets."""
    u, v, w, h = region
    fine_wood(img, region, wood, dark, 8, rng, joints=False, knots=0.2, grain=0.1, shade=0.06, vertical=True)
    px = img.load()
    iron = _rgb("3c3a3a")
    for y in range(h):
        for x in range(w):
            if y in bands or x in vertical_bands:
                k = 1.15 if (y in bands and (y == min(b for b in bands if abs(b - y) < 3))) else 0.95
                _put(px, u, v, x, y, _jitter(_scale(iron, k), rng, 5))
    if rivets:
        for y in bands[1::3]:
            for x in range(3, w - 2, 7):
                _put(px, u, v, x, y, _rgb("8a8a8e"))


def _chest(img, region, rng):
    _banded(img, region, _rgb("94683a"), _rgb("4e3218"), rng, bands=(0, 1, 11, 12, 30, 31), vertical_bands=(0, 1, 7, 8, 23, 24, 30, 31))
    u, v, w, h = region
    px = img.load()
    for y in range(9, 19):
        for x in range(12, 20):
            edge = y in (9, 18) or x in (12, 19)
            _put(px, u, v, x, y, _jitter(_rgb("2e2c2c") if edge else _rgb("8c8c90"), rng, 4))
    for y in (13, 14):
        _put(px, u, v, 15, y, _rgb("141414"))
        _put(px, u, v, 16, y, _rgb("141414"))


def _metal_crate(img, region, rng):
    """An iron-clad crate face: grey hammered plates, a dark iron frame, two vertical straps, rivets, a hasp."""
    u, v, w, h = region
    hammered_iron(img, region, _rgb("6a6a6e"), rng, dent=0.06)
    px = img.load()
    for y in range(h):
        for x in range(w):
            if x < 3 or x >= w - 3 or y < 3 or y >= h - 3 or x in (9, 10, 21, 22):
                _put(px, u, v, x, y, _jitter(_rgb("2e2e32"), rng, 4))
    for x, y in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2), (9, 6), (22, 6), (9, h - 7), (22, h - 7)):
        _put(px, u, v, x, y, _rgb("a8a8ae"))
    for y in range(11, 20):
        for x in range(13, 19):
            _put(px, u, v, x, y, _rgb("1e1e20") if x in (13, 18) or y in (11, 19) else _rgb("8a8a90"))


def _brass_box(img, region, rng):
    polished_metal(img, region, BRASS_STOPS, rng, fx=0.3, fy=0.25)
    u, v, w, h = region
    px = img.load()
    cx, cy = w / 2, h / 2
    for y in range(h):
        for x in range(w):
            if x < 2 or x >= w - 2 or y < 2 or y >= h - 2:
                _put(px, u, v, x, y, _rgb("5a3c14"))
                continue
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            R = 8 + (2 if math.cos(a * 8) > 0.2 else 0)
            if r < R and r > 3.5:
                _put(px, u, v, x, y, _scale(px[u + x, v + y][:3], 0.62))


def _blueprint(img, region, rng):
    """A pinned plan: parchment with brown ink gear drawings and lines, a dark pin at the top corners."""
    u, v, w, h = region
    px = img.load()
    base = _rgb("dcc89a")
    for y in range(h):
        for x in range(w):
            k = 0.94 + 0.06 * math.sin(x * 0.3 + y * 0.2) - (0.12 if x in (0, w - 1) or y in (0, h - 1) else 0)
            _put(px, u, v, x, y, _jitter(_scale(base, k), rng, 4))
    ink = _rgb("6a4a2a")
    for gx, gy, gr in ((9, 9, 5.5), (22, 9, 5.0), (9, 23, 5.0), (22, 23, 5.5)):
        for k in range(48):
            a = 2 * math.pi * k / 48
            rr = gr + (1.2 if math.cos(a * 8) > 0.3 else 0)
            _put(px, u, v, int(gx + rr * math.cos(a)), int(gy + rr * math.sin(a)), ink)
        for k in range(16):
            a = 2 * math.pi * k / 16
            _put(px, u, v, int(gx + 2 * math.cos(a)), int(gy + 2 * math.sin(a)), ink)
    for x in range(3, w - 3, 2):
        _put(px, u, v, x, 16, _scale(ink, 1.2))
    for (x, y) in ((1, 1), (w - 2, 1)):
        _put(px, u, v, x, y, _rgb("3a3a3a"))


def _parchment(img, region, rng):
    u, v, w, h = region
    px = img.load()
    base = _rgb("e2d2a8")
    for y in range(h):
        for x in range(w):
            k = 0.93 + 0.07 * math.sin(x * 0.25 + y * 0.35)
            c = _scale(base, k)
            if y % 4 == 2 and 3 < x < w - 4 and rng.random() < 0.7:
                c = _rgb("6a5038")
            _put(px, u, v, x, y, _jitter(c, rng, 4))


def _warp(img, region, rng):
    """Loom warp threads along v (every other column a thread, transparent between)."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            if x % 2 == 0:
                k = 1.0 + 0.08 * math.sin(y * 0.8 + x)
                _put(px, u, v, x, y, _jitter(_scale(_rgb("e6dfcf"), k), rng, 5))
            else:
                px[u + x, v + y] = (0, 0, 0, 0)


def _woven(img, region, rng):
    """Woven cloth on the loom: white with two blue bands, fine weave."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            blue = 8 <= x < 14 or 20 <= x < 23
            base = _rgb("2f4f86") if blue else _rgb("e6e0d2")
            k = 1.0 + (0.06 if (x + y) % 2 == 0 else -0.06)
            _put(px, u, v, x, y, _jitter(_scale(base, k), rng, 4))


def _runner(img, region, rng):
    """Blue runner hanging over the table: blue cloth with a thin gold edge, a gold band near the bottom, gold
    tassels (transparent gaps) at the very bottom."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            if y >= h - 3:
                if x % 3 == 2 or (y == h - 1 and x % 3 == 1):
                    px[u + x, v + y] = (0, 0, 0, 0)
                    continue
                c = _rgb("d4a83a")
            elif y in (h - 5, h - 6) or x in (1, w - 2):
                c = _rgb("d8ae42")
            else:
                c = _rgb("2e4a80")
                c = _scale(c, 1.0 + (0.05 if (x + y) % 2 == 0 else -0.05) + 0.06 * math.sin(x * 0.5))
            _put(px, u, v, x, y, _jitter(c, rng, 5))


def _rag(img, region, base, rng, edge=None, depth=6):
    """A hanging cloth with a ragged bottom edge (transparent notches) and soft vertical folds."""
    u, v, w, h = region
    px = img.load()
    cut = [h - rng.randint(0, depth) if x % 4 in (0, 1) else h - rng.randint(0, 2) for x in range(w)]
    for x in range(w):
        if rng.random() < 0.25:
            cut[x] = h - rng.randint(depth // 2, depth)
    for y in range(h):
        for x in range(w):
            if y >= cut[x]:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            k = 1.0 + 0.1 * math.sin(2 * math.pi * x / 8) + (0.03 if (x + y) % 2 == 0 else -0.03)
            c = _scale(base, k)
            if edge is not None and (y < 2):
                c = edge
            _put(px, u, v, x, y, _jitter(c, rng, 5))


def _roll_end(img, region, base, rng):
    """The end of a cloth roll: a spiral of the cloth, a light wooden core."""
    u, v, w, h = region
    px = img.load()
    cx, cy = w / 2, h / 2
    for y in range(h):
        for x in range(w):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            if r < 1.6:
                c = _rgb("b08656")
            else:
                ph = (r - a / (2 * math.pi) * 2.0) % 2.0
                c = _scale(base, 0.68 if ph < 0.6 else 1.05)
            _put(px, u, v, x, y, _jitter(c, rng, 4))


def _tunic(img, region, rng):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            k = 1.0 + 0.07 * math.sin(2 * math.pi * x / 6) + (0.03 if (x + y) % 2 == 0 else -0.03)
            c = _scale(_rgb("dcd4c2"), k)
            if 18 <= y < 21:
                c = _rgb("5a3a20") if not (14 <= x < 18) else _rgb("b8963c")   # belt and buckle
            if y < 3 and 11 <= x < 21:
                c = _rgb("a89c84")                                           # collar
            if x == 15 and 3 <= y < 9:
                c = _rgb("8a7a60")                                           # laced opening
            _put(px, u, v, x, y, _jitter(c, rng, 4))


def _jacket(img, region, rng):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            k = 1.0 + 0.08 * math.sin(x * 0.7) * math.sin(y * 0.3) + rng.uniform(-0.04, 0.04)
            c = _scale(_rgb("7a4a28"), k)
            if x in (15, 16):
                c = _rgb("4a2a14")
            if y in (12, 13, 22, 23) and x not in (15, 16):
                c = _rgb("3e2412")                                           # straps
            if y in (12, 13, 22, 23) and x in (10, 11, 20, 21):
                c = _rgb("b8a070")                                           # buckles
            _put(px, u, v, x, y, c)


def _herbs(img, region, rng):
    tt._fill(img, region, _rgb("3a5a22"), rng, noise=10)
    u, v, w, h = region
    px = img.load()
    for _ in range(80):
        x, y = rng.randrange(w), rng.randrange(h)
        _put(px, u, v, x, y, rng.choice((_rgb("6a9a3a"), _rgb("4a7a2a"), _rgb("8aa84a"))))


def _spools(img, region, rng):
    """Thread spools side by side (wooden rims, coloured thread), 4 px each."""
    u, v, w, h = region
    px = img.load()
    cols = [_rgb(c) for c in ("2e4a80", "b02a22", "e6e0d2", "c8a040", "3a6a2a", "6a3a7a", "d07a2a", "2e4a80")]
    for y in range(h):
        for x in range(w):
            c = cols[(x // 4) % len(cols)]
            if y < 3 or y >= h - 3:
                c = _rgb("a07a4a")
            elif y % 2 == 0:
                c = _scale(c, 0.85)
            _put(px, u, v, x, y, _jitter(c, rng, 4))


def _books(img, region, rng):
    u, v, w, h = region
    px = img.load()
    cols = [_rgb(c) for c in ("6b2f22", "2f4a6b", "4a5a2a", "6b5a2a", "3a2a22", "7a3a5a")]
    x = 0
    while x < w:
        bw = rng.randint(3, 5)
        c = rng.choice(cols)
        for xx in range(x, min(w, x + bw)):
            for y in range(h):
                k = 0.72 if xx == x else 1.0
                if y in (4, 5, h - 6):
                    c2 = _rgb("c8a040")
                else:
                    c2 = _scale(c, k)
                _put(px, u, v, xx, y, _jitter(c2, rng, 5))
        x += bw


def _candle(img, region, rng):
    tt._fill(img, region, _rgb("e8dcb8"), rng, noise=4)


def _slate(img, region, rng):
    """Dark stone blocks (the anvil pedestal, the bases): large smooth blocks with bevelled edges."""
    _bricks(img, region, _rgb("4a4846"), _rgb("262524"), rng, row_h=(8, 12), brick_w=(10, 18), bevel=0.16, tint=0.0)


def make_texture(path):
    rng = random.Random(1313)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    R = REGIONS
    # wood, the same tones as the carts / tents so the workshops sit with them
    fine_wood(img, R["wood"], _rgb("8a5e34"), _rgb("4a3014"), 8, rng, joints=False, knots=0.25, grain=0.12, shade=0.08)
    fine_wood(img, R["wood_dark"], _rgb("5c3c20"), _rgb("2c1a0a"), 8, rng, joints=False, knots=0.2, grain=0.12, shade=0.08)
    fine_wood(img, R["plank"], _rgb("8a5e34"), _rgb("442a12"), 4, rng, joints=True, knots=0.2, grain=0.1, shade=0.08)
    fine_wood(img, R["plank_dark"], _rgb("5e3e22"), _rgb("2e1c0a"), 4, rng, joints=True, knots=0.15, grain=0.1, shade=0.08)
    end_grain(img, R["end_grain"], _rgb("a87c4c"), _rgb("5a3c1e"), rng)
    twisted_rope(img, R["rope"], _rgb("c9ad7a"), _rgb("6e5634"), rng)
    hammered_iron(img, R["iron"], _rgb("3c3c40"), rng)
    polished_metal(img, R["gold"], [(0, (120, 84, 26)), (0.5, (214, 170, 72)), (1, (250, 230, 160))], rng)
    u, v, w, h = R["lantern"]
    paint_lamp_glass(img.load(), u, v, w, h)
    tt._fill(img, R["glow"], _rgb("ffd27a"), rng, noise=6)
    polished_metal(img, R["brass"], BRASS_STOPS, rng)
    polished_metal(img, R["copper"], COPPER_STOPS, rng, fx=0.5, fy=0.2)
    hammered_iron(img, R["black_iron"], _rgb("2e2e32"), rng, dent=0.09)
    _chain(img, R["chain"], rng)
    polished_metal(img, R["steel"], IRON_STOPS, rng, fx=0.3, fy=0.5)
    tt._fill(img, R["white"], _rgb("ece6d8"), rng, noise=3)
    u, v, w, h = R["water"]
    px = img.load()
    for y in range(h):
        for x in range(w):
            k = 1.0 + 0.12 * math.sin(x * 0.9 + y * 0.4) * math.sin(y * 0.7)
            _put(px, u, v, x, y, _jitter(_scale(_rgb("3a5e8a"), k), rng, 4))
    _coal(img, R["coal"], rng)
    _embers(img, R["embers"], rng)
    u, v, w, h = R["red_hot"]
    for y in range(h):
        for x in range(w):
            _put(px, u, v, x, y, _jitter(_mix(_rgb("ffcc60"), _rgb("e0401a"), abs(x - 7.5) / 8), rng, 6))
    # stone
    _bricks(img, R["stone"], _rgb("55514c"), _rgb("221f1c"), rng, tint=0.25)
    _bricks(img, R["stone_dark"], _rgb("4c4846"), _rgb("1e1c1a"), rng, row_h=(4, 6), brick_w=(5, 10), tint=0.15)
    _hide(img, R["hide"], rng, _rgb("a2602e"))
    _fire(img, R["fire"], rng)
    _cobble(img, R["cobble"], _rgb("7a7672"), rng)
    _fire_back(img, R["fire_back"], rng)
    _bricks(img, R["stone_top"], _rgb("68645e"), _rgb("4a4846"), rng, row_h=(15, 16), brick_w=(15, 17), bevel=0.08, tint=0.0)
    # leather and cloth
    tt._fill(img, R["leather"], _rgb("8a5a30"), rng, noise=7)
    tt._fill(img, R["leather_dark"], _rgb("5a3a20"), rng, noise=7)
    _rag(img, R["leather_red"], _rgb("8a4a30"), rng, depth=3)
    tt._weave(img, R["cloth_white"], _rgb("e4ddcc"), rng, seams=0, patches=0, stains=1, tears=0)
    tt._weave(img, R["cloth_blue"], _rgb("2f4f86"), rng, seams=0, patches=0, stains=1, tears=0)
    tt._weave(img, R["cloth_red"], _rgb("9a2a22"), rng, seams=0, patches=0, stains=1, tears=0)
    tt._weave(img, R["linen"], _rgb("d8ceb4"), rng, seams=0, patches=0, stains=2, tears=0)
    tt._weave(img, R["sack"], _rgb("a89060"), rng, seams=0, patches=0, stains=3, tears=1)
    # furniture
    _banded(img, R["crate"], _rgb("94683a"), _rgb("4e3218"), rng)
    _banded(img, R["crate_top"], _rgb("8a6036"), _rgb("4a2e16"), rng, bands=(0, 1, 30, 31), vertical_bands=(0, 1, 15, 16, 30, 31))
    _chest(img, R["chest"], rng)
    fine_wood(img, R["barrel"], _rgb("8e5e34"), _rgb("4a3018"), 4, rng, joints=False, knots=0.08, grain=0.1, shade=0.08, vertical=True)
    for y in (3, 4, 14, 15, 26, 27):
        for x in range(32):
            _put(px, R["barrel"][0], R["barrel"][1], x, y, _jitter(_rgb("3a3a3e"), rng, 5))
    fine_wood(img, R["barrel_top"], _rgb("9a6a3e"), _rgb("4a3018"), 6, rng, joints=False, knots=0.0, grain=0.1, shade=0.05)
    _blueprint(img, R["blueprint"], rng)
    _parchment(img, R["parchment"], rng)
    _warp(img, R["warp"], rng)
    _woven(img, R["woven"], rng)
    _runner(img, R["runner"], rng)
    _rag(img, R["drape"], _rgb("7e4026"), rng, depth=7)
    _rag(img, R["rag_white"], _rgb("dcd6c8"), rng, depth=6)
    _rag(img, R["rag_blue"], _rgb("2e4a80"), rng, depth=6, edge=_rgb("24395e"))
    _rag(img, R["rag_grey"], _rgb("8a8a86"), rng, depth=5)
    _roll_end(img, R["roll_blue"], _rgb("2f4f86"), rng)
    _roll_end(img, R["roll_white"], _rgb("e4ddcc"), rng)
    _roll_end(img, R["roll_red"], _rgb("9a2a22"), rng)
    _roll_end(img, R["roll_beige"], _rgb("cbb894"), rng)
    _gear(img, R["gear"], rng, BRASS_STOPS)
    _gear(img, R["gear_iron"], rng, IRON_STOPS, teeth=10)
    _tunic(img, R["tunic"], rng)
    _jacket(img, R["jacket"], rng)
    _metal_crate(img, R["metal_crate"], rng)
    _brass_box(img, R["brass_box"], rng)
    _herbs(img, R["herbs"], rng)
    _spools(img, R["spools"], rng)
    tt._straw(img, R["straw"], rng)
    _books(img, R["books"], rng)
    _hide(img, R["hide_light"], rng, _rgb("c89a68"), holes=False)
    tt._fill(img, R["leather_tan"], _rgb("a87448"), rng, noise=8)
    tt._fill(img, R["bread"], _rgb("b8823e"), rng, noise=8)
    tt._fill(img, R["pot_green"], _rgb("4a6a3a"), rng, noise=8)
    polished_metal(img, R["ingot"], IRON_STOPS, rng, fx=0.6, fy=0.4)
    tt._fill(img, R["glass"], _rgb("b9d4dc"), rng, noise=5)
    _candle(img, R["candle"], rng)
    tt._fill(img, R["flame"], _rgb("ffd27a"), rng, noise=10)
    _slate(img, R["slate"], rng)
    fine_wood(img, R["hide_frame"], _rgb("7a5432"), _rgb("3e2814"), 8, rng, joints=False, knots=0.3, grain=0.14, shade=0.1)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return img


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/agent_ws_a/workshops_a.png"
    make_texture(out)
    print("wrote", out)
