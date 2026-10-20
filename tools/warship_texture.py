"""Procedural pixel-art textures of the great warship.

  warship.png       512x512 atlas (hull bands, gun ports, stern carvings, sails...)
  warship_flag.png  64x64 flags (texture #1 of the model): white field, blue fleur-de-lis,
                    replaceable by a resource pack

Every region is (texture index, u, v, w, h).
"""
import math
import random

from PIL import Image

import interior_texture

from galley_texture import (_jitter, _mix, _ramp, _rgb, _scale, end_grain, fine_wood, hammered_iron,
                            paint_lamp_glass, painted_planks, polished_metal, twisted_rope)
from galleon_texture import _canvas, _patch_corners, _tri_inside

SIZE = 512
FLAG_SIZE = 64

REGIONS = {
    "hull_dark":   (0, 0, 0, 64, 32),
    "hull_black":  (0, 64, 0, 64, 32),
    "ochre":       (0, 128, 0, 64, 32),
    "white_bottom": (0, 192, 0, 64, 32),
    "wale":        (0, 256, 0, 64, 16),
    "dark_wood":   (0, 256, 16, 32, 16),
    "end_grain":   (0, 288, 16, 16, 16),
    "iron":        (0, 304, 16, 16, 16),
    "gold":        (0, 320, 0, 32, 32),
    "rail":        (0, 352, 0, 64, 16),
    "rope":        (0, 352, 16, 16, 16),
    "glow":        (0, 400, 16, 16, 16),
    "lantern":     (0, 416, 0, 16, 16),
    "gunport":     (0, 432, 0, 16, 16),
    "mast":        (0, 448, 0, 64, 32),
    "deck":        (0, 0, 32, 64, 64),
    "window":      (0, 128, 32, 32, 32),
    "glow_window": (0, 160, 32, 32, 32),
    "door":        (0, 192, 32, 32, 32),
    "grating":     (0, 224, 32, 32, 32),
    "panel":       (0, 256, 32, 64, 32),
    "cloth_roll":  (0, 320, 32, 64, 16),
    "carving":     (0, 320, 48, 32, 16),
    "arch_window": (0, 352, 48, 16, 24),
    "pilaster":    (0, 368, 48, 8, 32),
    "cannon":      (0, 376, 48, 16, 16),
    "hull_light":  (0, 64, 32, 64, 32),
    "red_paint":   (0, 64, 64, 64, 32),
    "garland":     (0, 448, 48, 32, 32),
    "mast_dark":   (0, 416, 32, 64, 16),
    "gold_relief": (0, 416, 48, 32, 32),
    "hull_ochre_dark": (0, 128, 64, 64, 32),
    # finer details (second pass)
    "lid":         (0, 0, 96, 16, 16),     # inside of a gun port lid (red)
    "compass":     (0, 16, 96, 16, 16),    # compass card in the binnacle
    "festoon":     (0, 32, 96, 32, 16),    # gilded swag of leaves and fruit (transparent around)
    "curtain":     (0, 64, 96, 32, 32),    # red damask curtains in the great cabin
    "bronze":      (0, 96, 96, 16, 16),    # ship's bell, binnacle hood
    "figure":      (0, 112, 96, 16, 32),   # gilded carved figure (drapery folds)
    "volute":      (0, 128, 96, 16, 16),   # gilded scroll seen end-on (spiral)
    "boat_wood":   (0, 144, 96, 64, 16),   # varnished clinker planks of the ship's boat
    "lion":        (0, 208, 96, 32, 32),   # carved mane / fur, gilded
    "bore":        (0, 240, 96, 16, 16),   # muzzle of a gun seen end-on
    # sails (plain canvas, like the reference)
    "window_in": (0, 0, 384, 32, 32),
    "rug": (0, 32, 384, 64, 32),
    "books": (0, 96, 384, 32, 32),
    "chart": (0, 128, 384, 32, 32),
    "bedding": (0, 160, 384, 32, 16),
    "painting": (0, 192, 384, 32, 32),
    "arch_window_in": (0, 224, 384, 16, 24),
    "course":      (0, 0, 128, 256, 192),
    "topsail":     (0, 256, 128, 160, 128),
    "lateen":      (0, 256, 256, 160, 128),
    "jib":         (0, 416, 128, 96, 96),
    # flag texture
    "flag":        (1, 0, 0, 64, 40),
    "pennant":     (1, 0, 40, 64, 8),
}

LIS = [
    "......##......",
    ".....####.....",
    "....######....",
    "....######....",
    ".....####.....",
    ".##...##...##.",
    "####..##..####",
    "#####.##.#####",
    ".############.",
    "..##########..",
    "......##......",
    "..##########..",
    "....##..##....",
    "...##....##...",
    "..##......##..",
]

GOLD_STOPS = [(0.0, (104, 72, 24)), (0.25, (160, 116, 40)), (0.5, (206, 162, 68)), (0.78, (234, 198, 104)), (1.0, (246, 222, 150))]
IRON_STOPS = [(0.0, (16, 16, 18)), (0.35, (34, 34, 38)), (0.7, (58, 58, 64)), (0.9, (96, 96, 104)), (1.0, (140, 140, 150))]
BRONZE_STOPS = [(0.0, (70, 44, 16)), (0.3, (128, 86, 34)), (0.6, (178, 128, 58)), (0.85, (220, 176, 98)), (1.0, (248, 222, 160))]


def _relief(px, region, height, rng, stops=GOLD_STOPS, k=1.5, base=0.5, amp=0.42, cut=None, noise=2):
    """Carved and gilded relief: height(x, y) in [0, 1] (None = transparent), lit from the top left;
    deep recesses (height < cut) fall into shadow."""
    u, v, w, h = region
    H = [[height(x, y) for x in range(w)] for y in range(h)]

    def at(x, y):
        x, y = min(w - 1, max(0, x)), min(h - 1, max(0, y))
        val = H[y][x]
        return 0.0 if val is None else val
    for y in range(h):
        for x in range(w):
            hv = H[y][x]
            if hv is None:
                continue
            dx = (at(x + 1, y) - at(x - 1, y)) / 2
            dy = (at(x, y + 1) - at(x, y - 1)) / 2
            t = base + amp * (hv - 0.5) + k * 0.6 * (dx + dy)
            if cut is not None and hv < cut:
                t = min(t, 0.18)
            px[u + x, v + y] = _jitter(_ramp(stops, max(0.0, min(1.0, t))), rng, noise) + (255,)


def _spiral(x, y, cx, cy, hand, pitch, radius):
    """Ridge height of a spiral scroll (volute) centred on cx, cy; 0 outside radius."""
    dx, dy = x + 0.5 - cx, y + 0.5 - cy
    r = math.hypot(dx, dy)
    if r > radius:
        return 0.0
    th = math.atan2(dy, dx) * hand
    ridge = 0.5 + 0.5 * math.cos(2 * math.pi * r / pitch - th)
    env = 1.0 - (r / radius) ** 2
    return ridge * (0.45 + 0.55 * env) + 0.25 * env


def _leaded(px, region, glass_a, glass_b, rng, frame="d4aa45", pitch=6, arch=False, glow=True):
    """Window with leaded diamond panes: gilded frame, a mullion and transom, glass shading from
    glass_a (middle) to glass_b (edges), a light catch on a few panes."""
    u, v, w, h = region
    fr = _rgb(frame)
    for y in range(h):
        for x in range(w):
            if arch:
                r = ((x + 0.5 - w / 2) ** 2 + (y + 0.5 - w / 2) ** 2) ** 0.5
                if y < w / 2 and r > w / 2:
                    continue
                edge = x < 2 or x >= w - 2 or y >= h - 2 or (y < w / 2 and r > w / 2 - 2)
            else:
                edge = x < 2 or x >= w - 2 or y < 2 or y >= h - 2
            if edge:
                k = 1.12 if (x < 1 or y < 1) else (0.8 if (x >= w - 1 or y >= h - 1) else 1.0)
                c = _scale(fr, k)
            elif abs(x + 0.5 - w / 2) < 1.0 or (not arch and abs(y + 0.5 - h * 0.45) < 1.0) or (arch and y == int(h * 0.6)):
                c = _scale(fr, 0.75) if glow else _rgb("3b2a18")
            elif (x + y) % pitch == 0 or (x - y) % pitch == 0:
                c = _mix(_rgb(glass_b), _rgb("2a2622"), 0.6)
            else:
                d = math.hypot((x + 0.5 - w / 2) / w, (y + 0.5 - h / 2) / h) * 2
                c = _mix(_rgb(glass_a), _rgb(glass_b), d)
                cell = ((x + y) // pitch, (x - y) // pitch)
                if (cell[0] * 3 + cell[1] * 5) % 7 == 0:
                    c = _scale(c, 1.08)
                if not glow and (x - y + h) % 11 in (0, 1):
                    c = _mix(c, (220, 232, 240), 0.35)
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _sail_canvas(px, region, rng):
    """Square sail: cloths of slightly different tone with stitched seams, three reef bands with their
    points, a soft shaded belly, a weathered foot, corner patches and the bolt rope."""
    _, u, v, w, h = region
    base = (244, 237, 221)
    cloth_tone = [1.0 - 0.03 * rng.random() for _ in range(w // 12 + 2)]
    blot = [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(8, 22)) for _ in range(6)]
    bands = (0.11, 0.21, 0.31)
    for y in range(h):
        fy = y / h
        for x in range(w):
            fx = x / w
            k = cloth_tone[x // 12] * (1.0 - 0.07 * abs(fy - 0.45)) - 0.04 * max(0.0, fy - 0.78)
            k -= 0.08 * (2 * abs(fx - 0.5)) ** 2 + 0.05 * max(0.0, 0.1 - fy) / 0.1
            if (x * 7 + y * 3) % 17 == 0:
                k -= 0.025
            for bx, by, br in blot:
                d = math.hypot(x - bx, y - by)
                if d < br:
                    k -= 0.02 * (1 - d / br)
            c = [int(b * k) for b in base]
            c[2] = int(c[2] * (1.0 - 0.035 * fy))
            c = tuple(c)
            if x % 12 == 11:
                c = _scale(c, 0.86)
            elif x % 12 == 10:
                c = _scale(c, 1.03)
            elif x % 12 == 0 and y % 3 == 1:
                c = _scale(c, 0.93)
            for band in bands:
                yb = int(h * band)
                if y in (yb, yb + 1):
                    c = _scale((226, 216, 192), 1.0 - 0.02 * (y - yb))
                if y == yb + 2:
                    c = _scale(c, 0.94)
                if x % 7 == 3 and yb - 1 <= y <= yb + 4 and y not in (yb, yb + 1):
                    c = (150, 128, 92) if y > yb else (172, 150, 112)   # reef points hanging from the band
            corner = min(x, w - 1 - x) + min(y, h - 1 - y)
            if corner < 14:
                c = _scale(c, 0.93)
                if corner == 13 and (x + y) % 2 == 0:
                    c = (160, 140, 104)
            if y < 3 or x < 2 or x >= w - 2 or y >= h - 2:
                c = (186, 160, 112) if (x + y) % 3 else (160, 136, 94)
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def make_textures(path, flag_path, lateen_tri, jib_tri):
    rng = random.Random(1665)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()

    def reg(name):
        return REGIONS[name][1:]

    # ---- painted hull: brushed paint along the planks, lit plank edges, dark seams, a few chips
    painted_planks(img, reg("hull_black"), (40, 35, 31), (12, 10, 9), 4, rng, wood=(70, 50, 32), wear=0.006)
    painted_planks(img, reg("hull_dark"), (74, 50, 32), (34, 22, 13), 4, rng, wood=(104, 72, 42), wear=0.006, joints=True)
    painted_planks(img, reg("ochre"), (214, 168, 70), (126, 90, 34), 4, rng, wood=(160, 112, 56), wear=0.006)
    painted_planks(img, reg("hull_ochre_dark"), (170, 126, 48), (100, 70, 26), 4, rng, wood=(120, 84, 40), wear=0.006)
    painted_planks(img, reg("white_bottom"), (232, 228, 214), (182, 176, 160), 4, rng, wood=(196, 186, 160), wear=0.006)
    painted_planks(img, reg("wale"), (34, 30, 27), (10, 9, 8), 4, rng, wood=(64, 46, 30), wear=0.006)
    painted_planks(img, reg("red_paint"), (150, 36, 28), (78, 16, 13), 4, rng, wood=(112, 64, 34), wear=0.006)
    # the white stuff (tallow and sulphur) is streaked and greyer towards the keel
    u, v, w, h = reg("white_bottom")
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[u + x, v + y]
            k = 1.0 - 0.05 * (y / h) - (0.02 if (x * 5 + y * 11) % 23 == 0 else 0.0)
            px[u + x, v + y] = (int(r * k), int(g * k), int(b * (k - 0.01)), a)
    # ---- bare wood with a fine grain
    fine_wood(img, reg("dark_wood"), (84, 55, 30), (38, 24, 12), 4, rng)
    fine_wood(img, reg("deck"), (176, 126, 74), (84, 56, 30), 4, rng, knots=0.1)
    fine_wood(img, reg("hull_light"), (180, 126, 66), (98, 66, 32), 4, rng)
    fine_wood(img, reg("rail"), (156, 108, 56), (90, 60, 28), 8, rng, joints=False)
    fine_wood(img, reg("mast"), (130, 86, 44), (74, 48, 22), 8, rng, joints=False, vertical=True, knots=0.25)
    fine_wood(img, reg("mast_dark"), (66, 45, 26), (32, 21, 11), 8, rng, joints=False, vertical=True)
    fine_wood(img, reg("boat_wood"), (196, 140, 76), (110, 72, 34), 4, rng, knots=0.05, shade=0.07)
    hammered_iron(img, reg("iron"), (50, 50, 55), rng)
    end_grain(img, reg("end_grain"), (150, 104, 56), (72, 46, 22), rng)
    twisted_rope(img, reg("rope"), (156, 126, 84), (70, 52, 33), rng)
    polished_metal(img, reg("gold"), GOLD_STOPS, rng, seed=0.7)
    polished_metal(img, reg("cannon"), IRON_STOPS, rng, fx=0.5, fy=0.2, seed=1.9)
    polished_metal(img, reg("bronze"), BRONZE_STOPS, rng, fx=0.6, fy=0.45, seed=3.1)

    # ---- carved and gilded work
    def acanthus(x, y):
        w, h = 32, 32
        hv = max(_spiral(x, y, 8.5, 12, 1, 4.2, 8.5), _spiral(x, y, 24.5, 21, -1, 4.2, 8.5))
        # the stalk winding between the two scrolls, with leaves along it
        yc = 16.5 + 7 * math.sin(2 * math.pi * (x + 0.5) / w + 0.4)
        d = abs(y + 0.5 - yc)
        if d < 2.6:
            hv = max(hv, 0.85 - 0.25 * d)
        leaf = 0.5 + 0.5 * math.cos(2 * math.pi * (x + 0.5) / 8 + 1.5 * math.sin((y + 0.5) / 5))
        if d < 6:
            hv = max(hv, leaf * (0.7 - d / 10))
        return min(1.0, hv + 0.06 * math.sin(x * 1.7 + y * 2.3))
    _relief(px, reg("gold_relief"), acanthus, rng, cut=0.08)

    def running_scroll(x, y):
        w, h = 32, 16
        hv = max(_spiral(x, y, 7.5, 10.5, 1, 3.4, 5.5), _spiral(x, y, 23.5, 5.5, -1, 3.4, 5.5))
        yc = 8 - 4.5 * math.sin(2 * math.pi * (x + 0.5) / w)
        d = abs(y + 0.5 - yc)
        if d < 2.0:
            hv = max(hv, 0.9 - 0.3 * d)
        if y in (0, h - 1):
            hv = 0.95
        elif y in (1, h - 2):
            hv = 0.3
        return hv
    _relief(px, reg("carving"), running_scroll, rng, cut=0.1)

    def fluted(x, y):
        w, h = 8, 32
        if y < 6:   # capital: a small volute each side
            return max(_spiral(x, y, 1.5, 3, 1, 2.0, 2.6), _spiral(x, y, 6.5, 3, -1, 2.0, 2.6), 0.55 if y in (4, 5) else 0.2)
        if y >= h - 4:   # base mouldings
            return 0.9 if y in (h - 4, h - 2) else 0.55
        if x in (0, w - 1):
            return 0.95
        return 0.75 - 0.45 * abs(math.sin(math.pi * (x - 0.5) / 3.0))
    _relief(px, reg("pilaster"), fluted, rng, k=2.0)

    def volute(x, y):
        return _spiral(x, y, 8, 8, 1, 3.0, 8.2) + 0.1
    _relief(px, reg("volute"), volute, rng, cut=0.12)

    def drapery(x, y):
        # folds falling down the robe of a carved figure, a belt, a face lighter at the top
        if y < 7:
            return 0.8 - 0.06 * abs(x - 7.5) if 3 <= x <= 12 else 0.4
        if y in (14, 15):
            return 0.95
        return 0.55 + 0.35 * math.sin((x + 0.5) * 1.3 + 0.08 * y * (x - 8) / 8)
    _relief(px, reg("figure"), drapery, rng)

    def mane(x, y):
        # locks of a carved mane: overlapping curls
        a = 0.5 + 0.5 * math.sin((x + 0.5) * 0.9 + math.sin((y + 0.5) * 0.45) * 2.0)
        b = 0.5 + 0.5 * math.cos((y + 0.5) * 0.7 + math.sin((x + 0.5) * 0.35) * 2.2)
        return 0.15 + 0.85 * a * b
    _relief(px, reg("lion"), mane, rng, k=2.0)

    # gilded garland (wreath) around the upper gun ports: overlapping laurel leaves, a ribbon at the top
    def wreath(x, y):
        w = h = 32
        dx, dy = x + 0.5 - w / 2, y + 0.5 - h / 2
        r = math.hypot(dx, dy)
        if not 9.0 < r < 15.8:
            return None
        a = math.atan2(dy, dx)
        if abs(a + math.pi / 2) < 0.28:
            return 0.95 - 0.3 * abs(r - 12.4) / 3.4   # the ribbon tie
        leaf = (a * 8 / math.pi) % 1.0
        return max(0.1, math.sin(math.pi * leaf) * (1 - ((r - 12.4) / 3.6) ** 2))
    _relief(px, reg("garland"), wreath, rng)

    # swag (festoon) of leaves and fruit hanging between two knots, transparent around it
    def swag(x, y):
        w, h = 32, 16
        yc = 3.0 + 8.0 * math.sin(math.pi * (x + 0.5) / w)
        half = 1.6 + 2.2 * math.sin(math.pi * (x + 0.5) / w)
        d = abs(y + 0.5 - yc)
        if x < 3 or x > w - 4:
            return 0.9 if y < 5 else None
        if d > half:
            return None
        fruit = 0.5 + 0.5 * math.cos((x + 0.5) * 1.6) * math.cos((y + 0.5 - yc) * 1.4)
        return 0.35 + 0.6 * fruit * (1 - (d / half) ** 2)
    _relief(px, reg("festoon"), swag, rng)

    # ---- fittings
    u, v, w, h = reg("cloth_roll")
    for y in range(h):
        for x in range(w):
            fold = 0.5 + 0.5 * math.sin((x + 0.5) * 0.55 + (y + 0.5) * 0.9)
            k = 0.86 + 0.14 * fold - (0.06 if (x + 2 * y) % 9 == 0 else 0.0)
            px[u + x, v + y] = _jitter(_scale((226, 214, 188), k), rng, 2) + (255,)
    _leaded(px, reg("window"), "4f7092", "263a52", rng, glow=False)
    _leaded(px, reg("glow_window"), "ffeaa0", "e8a848", rng)
    _leaded(px, reg("arch_window"), "ffeaa0", "e8a848", rng, pitch=4, arch=True)
    # cabin door: vertical planks, two iron strap hinges with nails, a ring, gilded frame
    u, v, w, h = reg("door")
    planks = [_jitter((92, 60, 30), rng, 6) for _ in range(w // 4 + 1)]
    for y in range(h):
        for x in range(w):
            if x < 2 or x >= w - 2 or y < 2:
                c = _scale(_rgb("d4aa45"), 1.1 if (x < 1 or y < 1) else 0.9)
            elif y in (8, 9, 22, 23) and x < w - 8:
                c = (58, 58, 64) if y in (8, 22) else (36, 36, 40)
                if x % 5 == 3:
                    c = (110, 110, 118)
            elif (x - 2) % 4 == 3:
                c = (44, 28, 14)
            else:
                tone = planks[(x - 2) // 4]
                c = _scale(tone, 1.0 + 0.06 * math.sin(y * 0.5 + x) + (0.05 if (x - 2) % 4 == 0 else 0.0))
            if (x - (w - 7)) ** 2 + (y - 16) ** 2 in (4, 5):
                c = (150, 120, 60)
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)
    # hatch grating: crossing battens over a dark hold
    u, v, w, h = reg("grating")
    for y in range(h):
        for x in range(w):
            if x % 4 == 0 or y % 4 == 0:
                c = (150, 104, 56) if y % 4 == 0 else (124, 84, 44)
                if x % 4 == 0 and y % 4 == 0:
                    c = (168, 118, 64)
            else:
                depth = min(x % 4, y % 4)
                c = (26, 17, 9) if depth > 1 else (52, 34, 18)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    # black panel with a gold frame and a gold medallion (stern and quarter decoration)
    u, v, w, h = reg("panel")
    for y in range(h):
        for x in range(w):
            fx = x % 32
            r2 = (fx - 15.5) ** 2 + (y - 15.5) ** 2
            if fx < 2 or fx > 29 or y < 2 or y > h - 3:
                c = _ramp(GOLD_STOPS, 0.75 if (fx < 1 or y < 1) else 0.5)
            elif r2 < 40:
                c = _rgb("27407a") if r2 < 26 else _ramp(GOLD_STOPS, 0.85 - 0.3 * ((fx + y) % 3 == 0))
            else:
                c = _scale(_rgb("1f1b18"), 1.0 + 0.1 * (fx in (2, 3) or y in (2, 3)))
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    u, v, w, h = reg("lantern")
    paint_lamp_glass(px, u, v, w, h)
    u, v, w, h = reg("glow")
    for y in range(h):
        for x in range(w):
            d = abs(x - w / 2 + 0.5) + abs(y - h / 2 + 0.5)
            px[u + x, v + y] = (_rgb("fff1a8") if d < 5 else _rgb("ffc94a")) + (255,)
    # gun port: gilded edge, red lining in shade at the top and the left, dark gun deck behind
    u, v, w, h = reg("gunport")
    for y in range(h):
        for x in range(w):
            ring = min(x, y, w - 1 - x, h - 1 - y)
            if ring < 1:
                c = _ramp(GOLD_STOPS, 0.8 if (x == 0 or y == 0) else 0.45)
            elif ring < 4:
                c = (150, 34, 26) if (x >= w - 4 or y >= h - 4) else (96, 20, 16)
            else:
                c = _mix((40, 26, 16), (8, 6, 5), (y - 4) / (h - 8))
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)
    # inside of a gun port lid: red planks, a dark rim, the ring bolt of the lid tackle
    u, v, w, h = reg("lid")
    for y in range(h):
        for x in range(w):
            if min(x, y, w - 1 - x, h - 1 - y) < 1:
                c = (60, 14, 11)
            elif x % 5 == 0:
                c = (110, 24, 19)
            else:
                c = _scale((158, 38, 30), 1.0 + 0.05 * math.sin(y * 0.8 + x))
            if (x - 7.5) ** 2 + (y - 4.5) ** 2 < 2.5:
                c = (70, 70, 76)
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)
    # compass card: a cream disc with a sixteen-point rose, north in red
    u, v, w, h = reg("compass")
    for y in range(h):
        for x in range(w):
            dx, dy = x + 0.5 - w / 2, y + 0.5 - h / 2
            r = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            if r > 7.6:
                c = (70, 50, 26)
            elif r > 6.8:
                c = _ramp(BRONZE_STOPS, 0.7)
            else:
                star = abs(math.cos(4 * a)) ** 3 * 6.5
                c = (236, 226, 196)
                if r < star:
                    c = (40, 50, 90) if (a < 0) else (180, 40, 30)
                if r < 1.1:
                    c = (200, 160, 60)
            px[u + x, v + y] = c + (255,)
    # muzzle face: a lit iron ring round the dark bore
    u, v, w, h = reg("bore")
    for y in range(h):
        for x in range(w):
            r = math.hypot(x + 0.5 - w / 2, y + 0.5 - h / 2)
            c = _mix((5, 4, 4), (52, 52, 58), min(1.0, (r / 7.5) ** 1.5))
            px[u + x, v + y] = c + (255,)
    # red damask: a soft repeating flower, folds
    u, v, w, h = reg("curtain")
    for y in range(h):
        for x in range(w):
            fold = 0.82 + 0.18 * math.sin((x + 0.5) * 2 * math.pi / 8)
            fl = math.cos((x % 16 - 7.5) * 0.7) * math.cos((y % 16 - 7.5) * 0.7)
            c = (148, 30, 30) if fl < 0.55 else (176, 50, 44)
            if y < 3:
                c = _ramp(GOLD_STOPS, 0.6 + 0.2 * (x % 2))
            px[u + x, v + y] = _jitter(_scale(c, fold), rng, 2) + (255,)

    _sail_canvas(px, REGIONS["course"], rng)
    _sail_canvas(px, REGIONS["topsail"], rng)
    _, u, v, w, h = REGIONS["lateen"]
    tri = [(p[0] * w, p[1] * h) for p in lateen_tri]
    _canvas(px, REGIONS["lateen"], rng, mask=lambda x, y, w_, h_: _tri_inside(tri, x, y), vertical=False)
    _, u, v, w, h = REGIONS["jib"]
    tri2 = [(p[0] * w, p[1] * h) for p in jib_tri]
    _canvas(px, REGIONS["jib"], rng, mask=lambda x, y, w_, h_: _tri_inside(tri2, x, y), vertical=False)
    _patch_corners(px, REGIONS["lateen"], tri, rng)
    _patch_corners(px, REGIONS["jib"], tri2, rng)
    interior_texture.paint(px, {k: r[1:] for k, r in REGIONS.items() if r[0] == 0})
    img.save(path)

    # flags: red field with a white cross (like the reference picture); red / white pennant.
    # A resource pack can replace warship_flag.png with any emblem.
    flag = Image.new("RGBA", (FLAG_SIZE, FLAG_SIZE), (0, 0, 0, 0))
    fp = flag.load()
    _, u, v, w, h = REGIONS["flag"]
    for y in range(h):
        for x in range(w):
            cross = abs(x - w * 0.36 + 0.5) < 3.5 or abs(y - h / 2 + 0.5) < 3.5
            c = _jitter(_rgb("f3efe6") if cross else _rgb("c22a22"), rng, 5)
            fp[u + x, v + y] = c + (255,)
    _, u, v, w, h = REGIONS["pennant"]
    for y in range(h):
        for x in range(w):
            c = _rgb("f3efe6") if y < h // 2 else _rgb("c22a22")
            fp[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    flag.save(flag_path)


def make_item_icon(path):
    """16x16 inventory icon: three-decker seen from the side."""
    icon = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = icon.load()
    black, ochre, white = _rgb("26221f"), _rgb("c79a3c"), _rgb("e6e1d3")
    sail, mast, gold, blue = _rgb("efe6d2"), _rgb("4a2e15"), _rgb("d4aa45"), _rgb("23439a")
    for x in range(1, 15):
        p[x, 10] = black + (255,)
        p[x, 11] = (ochre if x % 2 else black) + (255,)
        p[x, 12] = black + (255,)
    for x in range(2, 14):
        p[x, 13] = (ochre if x % 2 == 0 else black) + (255,)
    for x in range(3, 13):
        p[x, 14] = white + (255,)
    for y in (8, 9):
        for x in range(0, 4):
            p[x, y] = black + (255,)
    for x in range(0, 4):
        p[x, 7] = gold + (255,)
    p[15, 8] = mast + (255,)
    p[14, 9] = mast + (255,)
    for mx, top in ((4, 2), (8, 0), (12, 3)):
        for y in range(top, 10):
            p[mx, y] = mast + (255,)
        for y in range(top + 1, 9, 3):
            for x in range(mx - 1, mx + 2):
                p[x, y] = sail + (255,)
                p[x, y + 1] = sail + (255,)
        p[mx, top] = blue + (255,)
    icon.save(path)
