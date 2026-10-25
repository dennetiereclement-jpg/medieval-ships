"""Procedural pixel-art texture of the Old Corsair (old_corsair): one 512x512 atlas.

Colours of the reference sheet: a black planked hull with weathered cream bands, brown upper works
(dark and honey oak), aged red-brown sails made of blocky cloths with faded zones and beige patches,
black pirate flags with a white skull and crossed bones, warm lit windows and lanterns; inside, old
dark wood panelling, plank floors, beams, red runners and rugs, the stone of the kitchen.

Every region is (u, v, w, h); REGIONS is shared with tools/generate_corsair.py.
"""
import math
import random

from PIL import Image

from galley_texture import _jitter, _rgb, paint_lamp_glass

SIZE = 512

REGIONS = {
    # hull and upper works
    "hull_black":  (0, 0, 64, 32),
    "hull_black2": (64, 0, 64, 32),     # the same, more weathered (worn, salt-stained)
    "stripe":      (128, 0, 64, 32),    # the cream bands
    "wood_dark":   (192, 0, 64, 32),
    "wood_mid":    (256, 0, 64, 32),
    "wood_light":  (320, 0, 64, 32),
    "rail":        (384, 0, 64, 16),
    "rope":        (384, 16, 16, 16),
    "iron":        (400, 16, 16, 16),
    "bronze":      (416, 16, 16, 16),
    "glow":        (432, 16, 16, 16),
    "end_grain":   (448, 16, 16, 16),
    "dark_wood":   (464, 16, 32, 16),
    "rope_light":  (496, 16, 16, 16),   # ratlines and shrouds (tarred hemp, pale)
    "mast":        (448, 0, 64, 16),
    "deck":        (0, 32, 64, 64),
    "lantern":     (64, 32, 16, 16),
    "patch_wood":  (64, 48, 16, 16),    # a replaced plank, lighter
    "glow_window": (80, 32, 32, 32),
    "window_in":   (112, 32, 32, 32),
    "door":        (144, 32, 32, 32),
    "grating":     (176, 32, 32, 32),
    "plate":       (208, 32, 32, 32),   # riveted iron repair plate
    "repair":      (240, 32, 64, 32),   # patched planks of other colours
    "cloth_roll":  (304, 32, 64, 16),
    "carving":     (304, 48, 64, 16),
    "flag":        (368, 32, 64, 40),   # black pirate flag: skull and crossed bones
    "boat":        (432, 32, 64, 32),
    "glass":       (496, 32, 16, 16),
    "red_paint":   (496, 48, 16, 16),
    "compass":     (432, 64, 16, 16),
    "chart":       (448, 64, 32, 32),
    "books":       (480, 64, 32, 32),
    # rooms
    "wall_wood":   (0, 96, 64, 64),
    "floor":       (64, 96, 64, 64),
    "ceil":        (128, 96, 64, 64),
    "carpet":      (192, 96, 32, 64),
    "stone_floor": (224, 96, 64, 64),
    "wall_stone":  (288, 96, 64, 64),
    "hold_floor":  (352, 96, 64, 64),
    "hold_wall":   (416, 96, 64, 64),
    "rug":         (480, 96, 32, 64),
    "bedding":     (368, 72, 32, 16),
    "painting":    (400, 72, 32, 24),
    # phase 2: the furniture made for the ship
    "sack":        (64, 64, 16, 16),    # burlap
    "linen":       (80, 64, 16, 16),    # pillows, sheets
    "ham":         (96, 64, 16, 16),    # hams and sausages hanging in the kitchen
    "canvas":      (112, 64, 32, 16),   # hammocks, mattresses
    "hearth_stone": (144, 64, 32, 32),  # the kitchen hearth: dark stone blackened by the smoke
    "soot":        (176, 64, 16, 16),   # the back of the fire opening
    # sails (stretched over the cloth: one block of canvas ~ one cell of the pattern)
    "course":      (0, 160, 192, 128),
    "topsail":     (192, 160, 160, 112),
    "topgallant":  (352, 160, 128, 96),
    "jib":         (0, 288, 128, 128),
    "spanker":     (128, 288, 160, 144),
    "staysail":    (288, 288, 128, 96),
    "main_topgallant": (416, 288, 96, 80),
    "main_topsail": (0, 432, 176, 80),
}

# names used by the shared helpers (ship_details, generate_galleon): the same pixels
for _alias, _src in (("gold", "bronze"), ("hull_mid", "wood_mid"), ("hull_light", "wood_light"), ("hull_dark", "wood_dark"),
                     ("wood_trim", "wood_dark"), ("wood_honey", "wood_mid"), ("blue_paint", "glass"), ("pilaster", "wood_dark"),
                     ("velvet", "red_paint"), ("cushion", "red_paint"), ("brass", "bronze"), ("organ_wood", "wood_dark"), ("steel", "iron")):
    REGIONS[_alias] = REGIONS[_src]

SAIL_CELLS = {  # (columns, rows) of cloth blocks drawn in each sail region
    "course": (15, 8), "topsail": (12, 7), "topgallant": (9, 6), "jib": (10, 10), "spanker": (12, 13),
    "staysail": (6, 9), "main_topgallant": (8, 5), "main_topsail": (11, 7),
}


def _mix(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def _scale(c, k):
    return tuple(max(0, min(255, int(round(x * k)))) for x in c)


def _planks(px, region, tones, seam, rng, plank_h=4, joints=2, grain=0.06, worn=0.0, worn_col=None):
    """Planks along u: a tone per plank (picked in `tones`), grain streaks, dark seams, butt joints."""
    u, v, w, h = region
    seam = _rgb(seam)
    tones = [_rgb(t) for t in tones]
    for r in range(h // plank_h):
        base = rng.choice(tones)
        base = _scale(base, rng.uniform(0.92, 1.08))
        cuts = sorted(rng.sample(range(6, w - 6), joints)) if joints else []
        f1, p1 = rng.uniform(0.08, 0.2), rng.uniform(0, 6.28)
        for y in range(plank_h):
            yy = r * plank_h + y
            for x in range(w):
                if y == plank_h - 1 or x in cuts:
                    c = seam
                else:
                    k = 1.0 + grain * math.sin(x * f1 + p1 + y * 1.7) - (0.05 if y == plank_h - 2 else 0) + (0.05 if y == 0 else 0)
                    c = _scale(base, k)
                    if worn and worn_col and rng.random() < worn:
                        c = _mix(c, _rgb(worn_col), rng.uniform(0.2, 0.5))
                px[u + x, v + yy] = _jitter(c, rng, 3) + (255,)


def _blocks(px, region, tones, edge, rng, bw=16, bh=8, crack=0.0, crack_col="000000"):
    """Block masonry / big boards: a tone per block, a darker edge line, a few cracks."""
    u, v, w, h = region
    edge = _rgb(edge)
    tones = [_rgb(t) for t in tones]
    for by in range(0, h, bh):
        off = (bw // 2) if (by // bh) % 2 else 0
        for bx in range(-off, w, bw):
            base = _scale(rng.choice(tones), rng.uniform(0.93, 1.06))
            cr = rng.random() < crack
            cx, cy = rng.randrange(bw), rng.randrange(bh)
            for y in range(bh):
                for x in range(bw):
                    X, Y = bx + x, by + y
                    if not (0 <= X < w and 0 <= Y < h):
                        continue
                    if x == 0 or y == bh - 1:
                        c = edge
                    else:
                        c = _scale(base, 1.0 + (0.05 if y == 0 else 0) - (0.04 if y == bh - 2 else 0))
                        if cr and abs((x - cx) - (y - cy) * 1.6) < 0.7:
                            c = _rgb(crack_col)
                    px[u + X, v + Y] = _jitter(c, rng, 4) + (255,)


def _fill(px, region, col, rng, noise=4):
    u, v, w, h = region
    col = _rgb(col)
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = _jitter(col, rng, noise) + (255,)


def _sail(px, region, cols, rows, rng, patches=3, tri=None):
    """Aged red-brown sail: blocky cloths (one tone per block, like the terracotta blocks of the
    reference), faded zones, darker worn edges, seams, beige patches stitched on; tri = triangle mask
    (region fractions) for the jibs."""
    u, v, w, h = region
    reds = [_rgb(c) for c in ("a5412d", "9b3a29", "b04a33", "8f3526", "a84530", "963d2b")]
    faded = _rgb("c0644a")
    dark = _rgb("6e2a1f")
    patch = [_rgb(c) for c in ("d9c8a6", "cdbb98", "e2d4b4")]
    cw, ch = w / cols, h / rows
    tone = [[_scale(rng.choice(reds), rng.uniform(0.94, 1.06)) for _ in range(cols)] for _ in range(rows)]
    # faded zones (sun-bleached): soft blobs lighter
    blobs = [(rng.uniform(0, cols), rng.uniform(0, rows), rng.uniform(1.2, 2.6)) for _ in range(3)]
    for r in range(rows):
        for c in range(cols):
            for bx, by, br in blobs:
                d = math.hypot(c + 0.5 - bx, r + 0.5 - by)
                if d < br:
                    tone[r][c] = _mix(tone[r][c], faded, 0.45 * (1 - d / br))
    # patches: rectangles of whole blocks, away from the edges
    pcells = {}
    for _ in range(patches):
        # the large sails carry large patches (two or three cloths), as on the reference
        pw = rng.randint(2, 3) if cols >= 12 else rng.randint(1, 2)
        ph = 2 if rows >= 6 else rng.randint(1, 2)
        pc, pr = rng.randint(1, max(1, cols - pw - 1)), rng.randint(1, max(1, rows - ph - 1))
        col = rng.choice(patch)
        for rr in range(pr, pr + ph):
            for cc in range(pc, pc + pw):
                pcells[(rr, cc)] = (col, pc, pr, pw, ph)
    for y in range(h):
        for x in range(w):
            fx, fy = (x + 0.5) / w, (y + 0.5) / h
            if tri is not None and not _tri_inside(tri, fx, fy):
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            c_, r_ = min(cols - 1, int(x / cw)), min(rows - 1, int(y / ch))
            lx, ly = x - c_ * cw, y - r_ * ch
            if (r_, c_) in pcells:
                col, pc, pr, pw, ph = pcells[(r_, c_)]
                k = 1.0 - 0.06 * ((x + y) % 3 == 0)
                c = _scale(col, k)
                # stitches round the patch
                x0, y0, x1, y1 = pc * cw, pr * ch, (pc + pw) * cw, (pr + ph) * ch
                if min(x - x0, x1 - 1 - x, y - y0, y1 - 1 - y) < 1 and (x + y) % 2 == 0:
                    c = _rgb("6f5a42")
            else:
                c = tone[r_][c_]
                # block edges: a faint darker line (the cloths of the canvas)
                if lx < 1 or ly < 1:
                    c = _scale(c, 0.9)
                if (x * 7 + y * 13) % 23 == 0:
                    c = _scale(c, 0.93)
            # worn, darker edges (bolt rope) and a darker foot
            edge = min(fx, 1 - fx, fy, 1 - fy) if tri is None else min(fy, 1 - fy, 0.5)
            if edge < 0.025:
                c = _mix(c, _rgb("5a3a24"), 0.7)
            elif fy > 0.85:
                c = _mix(c, dark, (fy - 0.85) * 1.6)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    if tri is not None:
        # bolt rope along the three edges
        for y in range(h):
            for x in range(w):
                fx, fy = (x + 0.5) / w, (y + 0.5) / h
                if not _tri_inside(tri, fx, fy):
                    continue
                if not all(_tri_inside(tri, fx + dx / w, fy + dy / h) for dx, dy in ((1.6, 0), (-1.6, 0), (0, 1.6), (0, -1.6))):
                    px[u + x, v + y] = _jitter(_rgb("5a3a24"), rng, 3) + (255,)


def _tri_inside(pts, x, y):
    (ax, ay), (bx, by), (cx, cy) = pts

    def side(x1, y1, x2, y2):
        return (x - x2) * (y1 - y2) - (x1 - x2) * (y - y2)
    d1, d2, d3 = side(ax, ay, bx, by), side(bx, by, cx, cy), side(cx, cy, ax, ay)
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))


SKULL = [
    "......XXXXXX......",
    "....XXXXXXXXXX....",
    "...XXXXXXXXXXXX...",
    "..XXXXXXXXXXXXXX..",
    "..XXX....XX....X..",
    "..XX.....XX.....X.",
    "..XXX...XXXX...XX.",
    "...XXXXXX..XXXXX..",
    "....XXXXX..XXXX...",
    ".....XXXXXXXXX....",
    ".....X.X.X.X.X....",
    "......X.X.X.X.....",
]


def _flag(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _rgb("17171a") if (x + y * 3) % 11 else _rgb("222226")
            if x >= w - 3 and (y * 7 + x) % 5 < 2:
                c = (0, 0, 0)  # tattered fly
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    bone = _rgb("ecebe4")
    # crossed bones behind the skull
    cx, cy = w // 2, h // 2 + 2
    for t in range(-15, 16):
        for dx, dy in ((t, t * 0.62), (t, -t * 0.62)):
            for q in (0, 1):
                X, Y = int(cx + dx), int(cy + dy + q)
                if 0 <= X < w and 0 <= Y < h:
                    px[u + X, v + Y] = bone + (255,)
        if abs(t) >= 13:
            for dx, dy in ((t, t * 0.62), (t, -t * 0.62)):
                for e in (-1, 2):
                    X, Y = int(cx + dx + (1 if t > 0 else -1)), int(cy + dy + e)
                    if 0 <= X < w and 0 <= Y < h:
                        px[u + X, v + Y] = bone + (255,)
    sx, sy = cx - len(SKULL[0]) // 2, 4
    for j, row in enumerate(SKULL):
        for i, ch in enumerate(row):
            X, Y = sx + i, sy + j
            if 0 <= X < w and 0 <= Y < h:
                if ch == "X":
                    px[u + X, v + Y] = _jitter(bone, rng, 4) + (255,)
                elif ch == "." and 3 < j < 9 and 2 < i < 16:
                    px[u + X, v + Y] = _rgb("101012") + (255,)


def _window(px, region, rng, lit=True):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            frame = x < 3 or x >= w - 3 or y < 3 or y >= h - 3
            bar = abs(x - w / 2 + 0.5) < 1.2 or abs(y - h / 2 + 0.5) < 1.2
            if frame:
                c = _rgb("3a2414")
            elif bar:
                c = _rgb("4a2e18")
            elif lit:
                d = math.hypot(x - w / 2 + 0.5, (y - h * 0.6) * 0.9) / (w / 2)
                c = _mix(_rgb("ffe9a8"), _rgb("e88a2c"), min(1.0, d * 1.1))
            else:
                t = y / h
                c = _mix(_rgb("e4f1f8"), _rgb("9cc3dc"), t)
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _door(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("6b4426"), 1.0 + 0.06 * math.sin(x * 0.9)) if (x % 8) else _rgb("3d2715")
            if y in (5, 6, h - 7, h - 6):
                c = _rgb("2c2c30")  # iron straps
            if x < 2 or x >= w - 2 or y < 2:
                c = _rgb("3d2715")
            if 20 <= x <= 22 and 14 <= y <= 17:
                c = _rgb("8a7a40")  # ring handle
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _grating(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            hole = (x % 6 in (2, 3, 4)) and (y % 6 in (2, 3, 4))
            c = _rgb("1b140d") if hole else _scale(_rgb("7a5432"), 1.0 + 0.05 * math.sin(x + y))
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _plate(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("8c8f91"), 1.0 - 0.12 * (y / h) + 0.04 * math.sin(x * 0.7 + y * 0.3))
            if rng.random() < 0.08:
                c = _mix(c, _rgb("8a5a36"), 0.5)  # rust
            if x in (2, w - 3) and y % 6 == 3 or y in (2, h - 3) and x % 6 == 3:
                c = _rgb("44474a")  # rivets
            if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                c = _rgb("55585a")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _rope(px, region, light, dark, rng):
    u, v, w, h = region
    light, dark = _rgb(light), _rgb(dark)
    for y in range(h):
        for x in range(w):
            t = ((x + y) % 4) / 3.0
            px[u + x, v + y] = _jitter(_mix(light, dark, t), rng, 4) + (255,)


def _carpet(px, region, rng, border="9c7a36", field="7e1a1a", centre="4e0e0e"):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            if x < 2 or x >= w - 2:
                c = _rgb(border)
            elif x < 4 or x >= w - 4:
                c = _rgb(centre)
            else:
                c = _rgb(field)
                if (x + y) % 8 == 0 or (x - y) % 8 == 0:
                    c = _scale(c, 0.8)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _rug(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            # deep crimson, a dark border with a thin muted gold line, a lattice of darker motifs (panel 3)
            if x < 1 or x >= w - 1 or y < 1 or y >= h - 1:
                c = _rgb("3e0c0c")
            elif x < 4 or x >= w - 4 or y < 4 or y >= h - 4:
                c = _rgb("5a1212") if (x + y) % 4 else _rgb("74542a")
            elif x == 4 or x == w - 5 or y == 4 or y == h - 5:
                c = _rgb("a8843a")
            else:
                c = _rgb("8c1c1c")
                d = abs(x - w / 2 + 0.5) + abs(y - h / 2 + 0.5) * 0.5
                if (x + y) % 6 == 0 or (x - y) % 6 == 0:
                    c = _rgb("701515")
                if int(d) in (5, 11):
                    c = _rgb("5e1010")
                elif int(d) == 0:
                    c = _rgb("8a6a30")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _wall_wood(px, region, rng):
    """Old panelling: vertical boards, a dark wainscot rail and lower panels, worn."""
    u, v, w, h = region
    for x in range(w):
        tone = _scale(_rgb(rng.choice(("6a4527", "5e3d22", "73492a", "654024"))), rng.uniform(0.92, 1.06)) if x % 8 == 0 else None
        if tone:
            col = tone
        for y in range(h):
            if x % 8 == 7:
                c = _rgb("2e1d10")
            else:
                c = _scale(col, 1.0 + 0.05 * math.sin(y * 0.35 + x))
            if 40 <= y <= 42:
                c = _rgb("3b2512")  # rail
            elif y > 42 and (x % 16 in (2, 13) or y in (46, 61)):
                c = _scale(c, 0.82)  # panel mouldings
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _ceil(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            beam = (y % 32) < 6
            c = _scale(_rgb("3c2716"), 1.0 + 0.05 * math.sin(x * 0.3)) if beam else _scale(_rgb("5a3b21"), 1.0 + 0.04 * math.sin(x * 0.5 + y))
            if (y % 32) == 6 or (y % 8) == 7 and not beam:
                c = _rgb("2a1a0d")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _boat(px, region, rng):
    _planks(px, region, ("8a6038", "7d5532", "936840"), "3d2715", rng, plank_h=4, joints=1)


def _books(px, region, rng):
    u, v, w, h = region
    cols = [_rgb(c) for c in ("6e1d1d", "1f3b5c", "2e5a2a", "7a5a22", "4a2a52", "8a3a1a")]
    for y in range(h):
        for x in range(w):
            shelf = y % 16 >= 13
            if shelf:
                c = _rgb("4a2e18")
            else:
                c = cols[(x // 3 + y // 16 * 2) % len(cols)]
                if x % 3 == 2:
                    c = _scale(c, 0.6)
                if y % 16 in (3, 4):
                    c = _rgb("c9a347")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _chart(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _rgb("d8c79a")
            if 6 < x < 20 and 8 < y < 22 and (x - 13) ** 2 / 40 + (y - 15) ** 2 / 30 < 1:
                c = _rgb("8aa060")  # an island
            if (x + y) % 9 == 0:
                c = _scale(c, 0.9)
            if x < 1 or y < 1 or x >= w - 1 or y >= h - 1:
                c = _rgb("8a7a50")
            if abs(x - 24) + abs(y - 8) == 3:
                c = _rgb("7a2a1a")  # compass rose
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _compass(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - 7.5, y - 7.5)
            c = _rgb("e8dfc4") if d < 6 else _rgb("8a6a2a")
            if d < 6 and (abs(x - 7.5) < 0.8 or abs(y - 7.5) < 0.8):
                c = _rgb("7a1a1a")
            px[u + x, v + y] = c + (255,)


def _painting(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            sea = y > h * 0.55
            c = _mix(_rgb("2b4d6e"), _rgb("16304a"), (y - h * 0.55) / (h * 0.45)) if sea else _mix(_rgb("e0b36a"), _rgb("8aa6c0"), y / (h * 0.55))
            if 10 < x < 20 and h * 0.3 < y < h * 0.58 and (x - 15) ** 2 < (y - h * 0.3) * 1.2:
                c = _rgb("b04a33")  # a red sail on the horizon
            if x < 2 or y < 2 or x >= w - 2 or y >= h - 2:
                c = _rgb("8a6a2a")
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _replaced(px, region, rng, plank_h, n, tones, seam="2b1b0e"):
    """Wear and repairs: planks replaced by others of another wood (fresh, darker, greyed), nailed at
    their ends, as on the reference's deck and rooms."""
    u, v, w, h = region
    for _ in range(n):
        r = rng.randrange(h // plank_h)
        ln = rng.randint(w // 5, w // 2)
        x0 = rng.randrange(0, w - ln)
        base = _scale(_rgb(rng.choice(tones)), rng.uniform(0.95, 1.05))
        ph = rng.uniform(0, 6.28)
        for y in range(plank_h - 1):
            for x in range(x0, x0 + ln):
                c = _rgb(seam) if x in (x0, x0 + ln - 1) else _scale(base, 1 + 0.06 * math.sin(x * 0.35 + ph + y))
                px[u + x, v + r * plank_h + y] = _jitter(c, rng, 3) + (255,)
        for x in (x0 + 2, x0 + ln - 3):
            px[u + x, v + r * plank_h + plank_h // 2 - 1] = (34, 32, 30, 255)


def _replaced_boards(px, region, rng, n, tones, board_w=4):
    """The same on vertical boards (wall panelling): short lengths of other woods, nailed."""
    u, v, w, h = region
    for _ in range(n):
        x0 = rng.randrange(0, w // board_w) * board_w
        ln = rng.randint(h // 5, h // 3)
        y0 = rng.randrange(h // 3, h - ln)
        base = _scale(_rgb(rng.choice(tones)), rng.uniform(0.95, 1.05))
        for y in range(y0, y0 + ln):
            for x in range(x0, x0 + board_w - 1):
                c = _rgb("24170c") if y in (y0, y0 + ln - 1) else _scale(base, 1 + 0.05 * math.sin(y * 0.4 + x))
                px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
        px[u + x0 + 1, v + y0 + 2] = px[u + x0 + 1, v + y0 + ln - 3] = (34, 32, 30, 255)


def _iron_patch(px, region, rng, fx, fy, pw, ph):
    """A small riveted iron plate nailed over a damaged plank."""
    u, v, w, h = region
    x0, y0 = int(fx * (w - pw)), int(fy * (h - ph))
    for y in range(ph):
        for x in range(pw):
            edge = x in (0, pw - 1) or y in (0, ph - 1)
            c = _rgb("2e2f33") if edge else _scale(_rgb("4a4b50"), 1 + 0.08 * ((x + y) % 3 == 0))
            if (x, y) in ((1, 1), (pw - 2, 1), (1, ph - 2), (pw - 2, ph - 2)):
                c = _rgb("8a8a86")
            px[u + x0 + x, v + y0 + y] = _jitter(c, rng, 3) + (255,)


def _weave(px, region, rng, a, b, period=2):
    u, v, w, h = region
    a, b = _rgb(a), _rgb(b)
    for y in range(h):
        for x in range(w):
            c = a if ((x // period) + (y // period)) % 2 else b
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)


def _sooted(px, region, rng, k):
    """Smoke-blackened: darker upwards (v = 0 is the top of the region), in uneven patches."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[u + x, v + y]
            f = 1.0 - k * (1.0 - y / h) * rng.uniform(0.6, 1.0)
            px[u + x, v + y] = (int(r * f), int(g * f), int(b * f), a)


def make_texture(path, tris=None):
    """tris: the triangle (region fractions) of the jibs and of the staysail, as the model cuts them."""
    rng = random.Random(4207)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    R = REGIONS
    # hull: black planks (charcoal, slightly blue-grey highlights), weathered variant
    _planks(px, R["hull_black"], ("23222a", "1c1b20", "2a2930", "201f24"), "0c0c0e", rng, plank_h=4, joints=2, grain=0.05)
    _planks(px, R["hull_black2"], ("27262c", "1e1d22", "302d30", "2b2a2e"), "0c0c0e", rng, plank_h=4, joints=3, grain=0.06,
            worn=0.06, worn_col="5a5550")
    _blocks(px, R["stripe"], ("d9d1bd", "cfc7b2", "e2dbc8", "c6bda6"), "8f877a", rng, bw=16, bh=8, crack=0.35, crack_col="9a9284")
    _planks(px, R["wood_dark"], ("5a3a20", "4e321c", "634126", "553620"), "24170c", rng)
    _planks(px, R["wood_mid"], ("7a5130", "6e482a", "855a36", "73502e"), "33210f", rng)
    _planks(px, R["wood_light"], ("9a6a3e", "a87644", "8e6038", "b07e4a"), "4a2f17", rng)
    _planks(px, R["rail"], ("6e4628", "5e3c22"), "2b1a0c", rng, plank_h=8, joints=1)
    _planks(px, R["mast"], ("7a5532", "6e4c2c", "84603a"), "4a321c", rng, plank_h=4, joints=0, grain=0.1)
    _planks(px, R["deck"], ("8a6340", "7d5838", "936a44", "80603e", "6f5234"), "3a2716", rng, plank_h=4, joints=2)
    _planks(px, R["dark_wood"], ("4a2f1a", "40281a"), "1e140a", rng, plank_h=4, joints=1)
    _planks(px, R["patch_wood"], ("a4835c",), "4a3520", rng, plank_h=4, joints=0)
    _planks(px, R["repair"], ("8a6a48", "6b4a30", "3a3a3e", "9a8a6a", "2a292e", "57422e"), "121012", rng, plank_h=4, joints=3)
    _planks(px, R["cloth_roll"], ("a5412d", "9b3a29", "8f3526"), "5a2418", rng, plank_h=4, joints=0)
    _planks(px, R["carving"], ("6e4628", "5a3a20"), "2b1a0c", rng, plank_h=4, joints=4)
    _rope(px, R["rope"], "a88e62", "6e5a3a", rng)
    _rope(px, R["rope_light"], "c4ab7e", "8e774f", rng)
    _fill(px, R["iron"], "3a3b3e", rng, 6)
    _fill(px, R["bronze"], "9a6e32", rng, 8)
    _fill(px, R["glow"], "ffd27a", rng, 4)
    _fill(px, R["glass"], "b8d4dc", rng, 4)
    _fill(px, R["red_paint"], "8e2a1e", rng, 6)
    _fill(px, R["end_grain"], "8a6a42", rng, 10)
    u, v, w, h = R["lantern"]
    paint_lamp_glass(px, u, v, w, h)
    _window(px, R["glow_window"], rng, lit=True)
    _window(px, R["window_in"], rng, lit=False)
    _door(px, R["door"], rng)
    _grating(px, R["grating"], rng)
    _plate(px, R["plate"], rng)
    _flag(px, R["flag"], rng)
    _boat(px, R["boat"], rng)
    _compass(px, R["compass"], rng)
    _chart(px, R["chart"], rng)
    _books(px, R["books"], rng)
    _painting(px, R["painting"], rng)
    _wall_wood(px, R["wall_wood"], rng)
    _planks(px, R["floor"], ("6e4a2a", "634226", "7a5230", "5a3c22"), "2b1b0e", rng, plank_h=8, joints=2)
    _ceil(px, R["ceil"], rng)
    _carpet(px, R["carpet"], rng)
    _blocks(px, R["stone_floor"], ("6e6a64", "7a766e", "625e58"), "3a3834", rng, bw=16, bh=16)
    _blocks(px, R["wall_stone"], ("7f7a72", "8a857c", "736e66", "6a655e"), "3e3b36", rng, bw=16, bh=8, crack=0.2, crack_col="4a4640")
    _planks(px, R["hold_floor"], ("5e4228", "553b24", "684a2e"), "241810", rng, plank_h=8, joints=3, worn=0.04, worn_col="3a3a30")
    _planks(px, R["hold_wall"], ("4e3420", "5a3c24", "46301c"), "1e140a", rng, plank_h=8, joints=2)
    _rug(px, R["rug"], rng)
    # phase 2: wear and repairs of the deck and the rooms, the furniture's cloths
    _replaced(px, R["deck"], rng, 4, 6, ("a07a4c", "5e4228", "7a4e30", "93744e"), seam="3a2716")
    _replaced(px, R["floor"], rng, 8, 3, ("86603c", "4a3220", "7a4a2e"))
    _replaced(px, R["hold_floor"], rng, 8, 3, ("74563a", "3e2c1c", "6a4630"))
    _replaced_boards(px, R["wall_wood"], rng, 3, ("82603e", "4a3220", "7a4a2e"), board_w=8)
    _replaced_boards(px, R["hold_wall"], rng, 3, ("6e5236", "352416", "60402a"), board_w=8)
    _weave(px, R["sack"], rng, "a98b5e", "8e7349")
    _weave(px, R["canvas"], rng, "ab9a76", "9c8a66", period=1)
    _fill(px, R["linen"], "e6dfcc", rng, 4)
    _blocks(px, R["ham"], ("9a4632", "8a3c2a", "a8543c"), "5a2418", rng, bw=8, bh=4)
    _fill(px, R["bedding"], "8e1c1c", rng, 8)
    for name, (cols, rows) in SAIL_CELLS.items():
        tri = None
        if name in ("jib", "staysail"):
            tri = (tris or {}).get(name) or [(0.0, 0.0), (1.0, 0.0), (0.62, 1.0)]
        _sail(px, R[name], cols, rows, rng, patches=2 if tri else 3, tri=tri)
    # the hearth (own random stream: the regions above keep their pixels)
    rng2 = random.Random(4211)
    _blocks(px, R["hearth_stone"], ("5a544c", "4e4942", "625b52", "46413b"), "26231f", rng2, bw=8, bh=4, crack=0.15, crack_col="2e2a26")
    _sooted(px, R["hearth_stone"], rng2, 0.45)
    _fill(px, R["soot"], "1c1916", rng2, 5)
    _sooted(px, R["soot"], rng2, 0.3)
    img.save(path)
    return img


def make_item_icon(path, model_png=None):
    """16x16 icon: the black hull with its cream band, the two masts of the brig with their red square
    sails, the spanker aft, a black flag at the gaff peak."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    black, cream, wood = _rgb("1f1e24"), _rgb("d9d1bd"), _rgb("7a5130")
    red, red2, mast = _rgb("a5412d"), _rgb("8f3526"), _rgb("4a2f1a")
    for x in range(1, 15):
        for y in range(11, 15):
            if y == 14 and (x < 3 or x > 13):
                continue
            px[x, y] = (cream if y == 12 else black) + (255,)
        px[x, 10] = wood + (255,)
    for x in range(0, 3):
        px[x, 9 - x] = mast + (255,)  # bowsprit
    for x, y in ((3, 4), (3, 5), (3, 6), (2, 6)):
        px[x, y] = red2 + (255,)      # a jib
    for mx, top in ((6, 1), (11, 1)):
        for y in range(top, 10):
            px[mx, y] = mast + (255,)
    # fore mast: topgallant, topsail, course
    for y, x0, x1 in ((2, 5, 7), (3, 5, 7), (4, 4, 8), (5, 4, 8), (6, 4, 8), (7, 4, 8), (8, 4, 8), (9, 4, 8)):
        for x in range(x0, x1 + 1):
            if x != 6:
                px[x, y] = (red if (x + y) % 3 else red2) + (255,)
    # main mast: topgallant, topsail, the bare main yard, the spanker abaft it
    for y, x0, x1 in ((2, 10, 12), (3, 10, 12), (4, 10, 13), (5, 10, 13)):
        for x in range(x0, x1 + 1):
            if x != 11:
                px[x, y] = (red if (x + y) % 3 else red2) + (255,)
    for x in range(9, 14):
        if x != 11:
            px[x, 6] = wood + (255,)
    for y, x1 in ((7, 13), (8, 14), (9, 14)):
        for x in range(12, x1 + 1):
            px[x, y] = (red2 if (x + y) % 3 else red) + (255,)
    px[14, 1] = (20, 20, 22, 255)
    px[15, 1] = (20, 20, 22, 255)
    px[14, 2] = (20, 20, 22, 255)
    px[15, 2] = (230, 230, 225, 255)
    img.save(path)
