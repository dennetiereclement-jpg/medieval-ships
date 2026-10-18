"""Procedural pixel-art textures of the great galleon.

  galleon.png       512x512 atlas (hull, castles, roof, sails...), regions in REGIONS
  galleon_flag.png  64x64 flags (texture #1 of the model): the emblem can be replaced
                    by a resource pack without touching the model

Every region is (texture index, u, v, w, h) so the model generator and the
textures stay in sync.
"""
import math
import random

from PIL import Image

import interior_texture

from galley_texture import _fill, _jitter, _planks, _rgb, paint_lamp_glass

SIZE = 512
FLAG_SIZE = 64

REGIONS = {
    # wood
    "hull_dark":   (0, 0, 0, 64, 32),
    "hull_mid":    (0, 64, 0, 64, 32),
    "hull_light":  (0, 128, 0, 64, 32),
    "red_paint":   (0, 192, 0, 64, 32),
    "wale":        (0, 256, 0, 64, 16),
    "dark_wood":   (0, 256, 16, 32, 16),
    "end_grain":   (0, 288, 16, 16, 16),
    "iron":        (0, 304, 16, 16, 16),
    "gold":        (0, 320, 0, 32, 32),
    "rail":        (0, 352, 0, 64, 16),
    "rope":        (0, 352, 16, 16, 16),
    "blue_paint":  (0, 368, 16, 32, 16),
    "glow":        (0, 400, 16, 16, 16),
    "lantern":     (0, 416, 0, 16, 16),
    "gunport":     (0, 432, 0, 16, 16),
    "mast":        (0, 448, 0, 64, 32),
    "deck":        (0, 0, 32, 64, 64),
    "roof":        (0, 64, 32, 64, 64),
    "window":      (0, 128, 32, 32, 32),
    "glow_window": (0, 160, 32, 32, 32),
    "door":        (0, 192, 32, 32, 32),
    "grating":     (0, 224, 32, 32, 32),
    "panel":       (0, 256, 32, 64, 32),
    "cloth_roll":  (0, 320, 32, 64, 16),
    "carving":     (0, 320, 48, 32, 16),
    "frieze":      (0, 0, 320, 64, 16),
    "shield_a":    (0, 64, 320, 16, 20),
    "shield_b":    (0, 80, 320, 16, 20),
    "pilaster":    (0, 96, 320, 8, 32),
    "arch_window": (0, 104, 320, 16, 24),
    "wood_honey":  (0, 128, 320, 64, 32),
    "wood_trim":   (0, 192, 320, 64, 32),
    # sails
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


def _tri_inside(pts, x, y):
    (ax, ay), (bx, by), (cx, cy) = pts

    def side(x1, y1, x2, y2):
        return (x - x2) * (y1 - y2) - (x1 - x2) * (y - y2)
    d1, d2, d3 = side(ax, ay, bx, by), side(bx, by, cx, cy), side(cx, cy, ax, ay)
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))


def _cloth(px, region, rng, mask=None, cross=False, seams_vertical=True):
    _, u, v, w, h = region
    cloth, shade, seam = _rgb("efe6d2"), _rgb("ddd1b6"), _rgb("bfae8c")
    red = _rgb("b3221c")
    for y in range(h):
        for x in range(w):
            if mask is not None and not mask(x + 0.5, y + 0.5, w, h):
                continue
            panel = (x // 16) if seams_vertical else (y // 16)
            c = shade if panel % 2 else cloth
            if seams_vertical and x % 16 == 15 or not seams_vertical and y % 16 == 15:
                c = seam
            if rng.random() < 0.08:
                c = _jitter(c, rng, 8)
            # weathering: slightly darker towards the foot, reef points in rows under the head
            fy = y / h
            c = tuple(max(0, int(k * (1 - 0.07 * fy))) for k in c)
            if mask is None and int(h * 0.16) <= y <= int(h * 0.16) + 1 and x % 10 in (4, 5):
                c = _rgb("8a7a5a")
            if mask is None and int(h * 0.3) <= y <= int(h * 0.3) + 1 and x % 10 in (4, 5):
                c = _rgb("8a7a5a")
            if cross:
                cw = max(6, w // 9)
                if abs(x - w / 2) < cw / 2 or abs(y - h * 0.45) < cw / 2:
                    c = _jitter(red, rng, 6)
            if y < 3:
                c = _rgb("b89a62")  # bolt rope along the head
            if mask is None and (x < 2 or x >= w - 2 or y >= h - 2):
                c = _rgb("b89a62")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _canvas(px, region, rng, mask=None, vertical=True):
    """Warm cream canvas: thin seams, reef bands with their points, bolt ropes, soft weathering."""
    _, u, v, w, h = region
    base = (243, 236, 220)
    for y in range(h):
        for x in range(w):
            if mask is not None and not mask(x + 0.5, y + 0.5, w, h):
                continue
            fy = y / h
            # soft vertical gradient (lighter in the belly) and a little grain
            k = 1.0 - 0.06 * abs(fy - 0.45) - (0.03 if (x * 7 + y * 3) % 17 == 0 else 0)
            c = tuple(int(b * k) for b in base)
            seam = (x % 12 == 11) if vertical else (y % 12 == 11)
            if seam:
                c = tuple(int(b * 0.9) for b in c)
            if mask is None:
                for band in (0.14, 0.27):
                    yb = int(h * band)
                    if y == yb or y == yb + 1:
                        c = (222, 212, 188)
                    if y == yb and x % 8 == 4:
                        c = (150, 130, 95)
                if y < 3 or x < 2 or x >= w - 2 or y >= h - 2:
                    c = (186, 160, 112)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _gold(px, region, rng):
    """Polished gilding: soft rounded highlights and shadows instead of a regular pattern."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            t = 0.55 * math.sin(x * 0.42 + math.sin(y * 0.3) * 1.5) + 0.45 * math.cos(y * 0.36 + x * 0.12)
            t -= 0.25 * ((y % 16) / 16.0)
            if t > 0.62:
                c = _rgb("fbe7a1")
            elif t > 0.2:
                c = _rgb("e6bf5a")
            elif t > -0.35:
                c = _rgb("cfa23f")
            elif t > -0.75:
                c = _rgb("a97f2a")
            else:
                c = _rgb("7c5a1c")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _sail_cloth(px, region, rng):
    """Square sail: cloths of slightly different tone, weathered foot, reef bands with points,
    reinforcing patches at the four corners, bolt rope."""
    _, u, v, w, h = region
    base = (243, 236, 220)
    cloth_tone = [1.0 - 0.025 * rng.random() for _ in range(w // 12 + 2)]
    blot = [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(8, 22)) for _ in range(6)]
    for y in range(h):
        fy = y / h
        for x in range(w):
            k = cloth_tone[x // 12] * (1.0 - 0.07 * abs(fy - 0.4)) - 0.04 * max(0.0, fy - 0.75)
            if (x * 7 + y * 3) % 17 == 0:
                k -= 0.03
            for bx, by, br in blot:  # faint weathering stains
                d = math.hypot(x - bx, y - by)
                if d < br:
                    k -= 0.025 * (1 - d / br)
            c = [int(b * k) for b in base]
            c[2] = int(c[2] * (1.0 - 0.03 * fy))  # the foot yellows a little
            c = tuple(c)
            if x % 12 == 11:
                c = tuple(int(q * 0.9) for q in c)
            elif x % 12 == 10:
                c = tuple(min(255, int(q * 1.03)) for q in c)
            for band in (0.14, 0.27):
                yb = int(h * band)
                if y == yb or y == yb + 1:
                    c = (222, 212, 188)
                if y == yb + 2 and x % 8 == 4:
                    c = (150, 130, 95)
                if y == yb + 3 and x % 8 == 4:
                    c = (175, 155, 118)
            corner = min(x, w - 1 - x) + min(y, h - 1 - y)
            if corner < 14:
                c = tuple(int(q * 0.93) for q in c)
                if corner == 13 and (x + y) % 2 == 0:
                    c = (160, 140, 104)  # stitching of the patch
            if y < 3 or x < 2 or x >= w - 2 or y >= h - 2:
                c = (186, 160, 112)
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _patch_corners(px, region, tri, rng):
    """Reinforcing patches at the three corners of a triangular sail, and a bolt rope."""
    _, u, v, w, h = region
    for y in range(h):
        for x in range(w):
            if not _tri_inside(tri, x + 0.5, y + 0.5):
                continue
            r, g, b, a = px[u + x, v + y]
            dmin = min(math.hypot(x + 0.5 - cx, y + 0.5 - cy) for cx, cy in tri)
            if dmin < 16:
                k = 0.93
                if 15 <= dmin and (x + y) % 2 == 0:
                    r, g, b, k = 160, 140, 104, 1.0
                px[u + x, v + y] = (int(r * k), int(g * k), int(b * k), a)
            inside_edge = all(_tri_inside(tri, x + 0.5 + dx, y + 0.5 + dy) for dx, dy in ((1.5, 0), (-1.5, 0), (0, 1.5), (0, -1.5)))
            if not inside_edge:
                px[u + x, v + y] = (186, 160, 112, a)


def make_textures(path, flag_path, lateen_tri, jib_tri):
    rng = random.Random(1588)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()

    def reg(name):
        return REGIONS[name][1:]

    _planks(img, reg("hull_dark"), _rgb("5a3a1e"), _rgb("2f1d0e"), 4, rng)
    _planks(img, reg("hull_mid"), _rgb("8f5f2e"), _rgb("553719"), 4, rng)
    # natural golden wood of the reference (hull, castles) and its lighter trim beams
    _planks(img, reg("wood_honey"), _rgb("c58f4a"), _rgb("7f5426"), 4, rng)
    _planks(img, reg("wood_trim"), _rgb("e0b56a"), _rgb("a07a3a"), 8, rng, joints=False)
    _planks(img, reg("hull_light"), _rgb("b07a3c"), _rgb("6e4a22"), 4, rng)
    _planks(img, reg("red_paint"), _rgb("8f1f1b"), _rgb("561110"), 4, rng)
    _planks(img, reg("wale"), _rgb("2e221a"), _rgb("17110c"), 4, rng, joints=False)
    _planks(img, reg("dark_wood"), _rgb("4e321a"), _rgb("2b1a0c"), 4, rng)
    _planks(img, reg("deck"), _rgb("a87542"), _rgb("5c3c1e"), 4, rng)
    _planks(img, reg("rail"), _rgb("9a6a36"), _rgb("5e3f1d"), 8, rng, joints=False)
    _planks(img, reg("mast"), _rgb("7a4f27"), _rgb("4a2e15"), 8, rng, joints=False, vertical=True)
    _planks(img, reg("blue_paint"), _rgb("27407a"), _rgb("17264a"), 4, rng, joints=False)
    _fill(img, reg("iron"), _rgb("3b3b3f"), rng, 8)
    _fill(img, reg("end_grain"), _rgb("8c5e30"), rng, 10)

    # gold: carved trim with highlights
    _gold(px, reg("gold"), rng)
    u, v, w, h = reg("carving")
    for y in range(h):
        for x in range(w):
            scroll = ((x - 8 * (y // 8)) % 16) < 3 or y in (0, h - 1)
            c = _rgb("f0cf6f") if scroll else _rgb("b88a2e")
            px[u + x, v + y] = _jitter(c, rng, 6) + (255,)
    # rope
    u, v, w, h = reg("rope")
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = (_rgb("4a3a2a") if (x + y) % 3 else _rgb("2a2018")) + (255,)
    # roof tiles (red, overlapping rows)
    u, v, w, h = reg("roof")
    for y in range(h):
        for x in range(w):
            row = y // 6
            off = 4 if row % 2 else 0
            edge = y % 6 == 5 or (x + off) % 8 == 0
            c = _rgb("7e1a14") if edge else _rgb("b8352a")
            if not edge and y % 6 == 0:
                c = _rgb("d0523f")
            px[u + x, v + y] = _jitter(c, rng, 7) + (255,)
    # windows: leaded glass in a gold frame; glowing variant (lit cabin)
    for name, glass, glass2 in (("window", "37506b", "4f7092"), ("glow_window", "f0a63c", "ffd98a")):
        u, v, w, h = reg(name)
        for y in range(h):
            for x in range(w):
                if x < 3 or x >= w - 3 or y < 3 or y >= h - 3:
                    c = _rgb("5a3a1c") if name == "glow_window" else _rgb("c9a043")
                elif (x + y) % 6 == 0 or (x - y) % 6 == 0:
                    c = _rgb("2c2018")  # diamond lattice
                else:
                    d = abs(x - w / 2) + abs(y - h / 2)
                    c = _rgb(glass2) if d < w * 0.35 else _rgb(glass)
                px[u + x, v + y] = c + (255,)
    # door: planks, iron bands, frame
    u, v, w, h = reg("door")
    for y in range(h):
        for x in range(w):
            if x < 2 or x >= w - 2 or y < 2:
                c = _rgb("c9a043")
            elif y in (8, 9, 22, 23):
                c = _rgb("3b3b3f")
            else:
                c = _rgb("5a3a1c") if (x // 5) % 2 else _rgb("4a2e15")
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
    # grating (hatches)
    u, v, w, h = reg("grating")
    for y in range(h):
        for x in range(w):
            c = _rgb("1a120a") if (x % 6 > 1 and y % 6 > 1) else _rgb("8a5e30")
            px[u + x, v + y] = c + (255,)
    # painted panel: red field, gold frame, blue medallion
    u, v, w, h = reg("panel")
    for y in range(h):
        for x in range(w):
            fx, fy = x % 32, y
            if fx < 2 or fx > 29 or fy < 2 or fy > h - 3:
                c = _rgb("d4aa45")
            elif (fx - 15.5) ** 2 + (fy - 15.5) ** 2 < 40:
                c = _rgb("27407a") if (fx - 15.5) ** 2 + (fy - 15.5) ** 2 < 28 else _rgb("d4aa45")
            else:
                c = _rgb("8f1f1b")
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    # rolled (furled) canvas on the yards
    u, v, w, h = reg("cloth_roll")
    for y in range(h):
        for x in range(w):
            c = _rgb("d9cdb2") if (x + y // 2) % 5 else _rgb("b8a888")
            px[u + x, v + y] = c + (255,)
    # lantern frame and glow
    u, v, w, h = reg("lantern")
    paint_lamp_glass(px, u, v, w, h)
    u, v, w, h = reg("glow")
    for y in range(h):
        for x in range(w):
            d = abs(x - w / 2 + 0.5) + abs(y - h / 2 + 0.5)
            px[u + x, v + y] = (_rgb("fff1a8") if d < 5 else _rgb("ffc94a")) + (255,)
    # gun port: dark opening with a thick frame
    u, v, w, h = reg("gunport")
    for y in range(h):
        for x in range(w):
            frame = x < 2 or x >= w - 2 or y < 2 or y >= h - 2
            px[u + x, v + y] = (_rgb("5e3f1d") if frame else _rgb("120c08")) + (255,)

    # painted frieze: gold borders, red lozenges on blue
    u, v, w, h = reg("frieze")
    for y in range(h):
        for x in range(w):
            if y < 2 or y >= h - 2:
                c = _rgb("d4aa45")
            else:
                d = abs((x % 16) - 7.5) / 7.5 + abs(y - h / 2 + 0.5) / (h / 2 - 2)
                c = _rgb("b3221c") if d < 0.75 else (_rgb("e8c35a") if d < 0.95 else _rgb("27407a"))
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    # heraldic shields (pavises) along the castles: argent / gules chevron, azure / or bend
    for name, field, charge in (("shield_a", "b3221c", "eeeae0"), ("shield_b", "27407a", "e8c35a")):
        u, v, w, h = reg(name)
        for y in range(h):
            for x in range(w):
                half = w / 2
                inside = y < h * 0.55 or abs(x + 0.5 - half) < half * (1 - (y - h * 0.55) / (h * 0.45)) ** 0.7
                if not inside:
                    continue
                edge = x == 0 or x == w - 1 or y == 0
                if name == "shield_a":
                    on = abs(abs(x + 0.5 - half) - (h * 0.75 - y) * 0.7) < 2.2
                else:
                    on = abs((x + 0.5) - y * 0.8) < 2.2
                c = _rgb("d4aa45") if edge else (_rgb(charge) if on else _rgb(field))
                px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    # carved pilaster and arched window
    u, v, w, h = reg("pilaster")
    for y in range(h):
        for x in range(w):
            c = _rgb("f0cf6f") if x in (1, w - 2) or y % 8 == 0 else _rgb("b88a2e")
            px[u + x, v + y] = _jitter(c, rng, 5) + (255,)
    u, v, w, h = reg("arch_window")
    for y in range(h):
        for x in range(w):
            r = ((x + 0.5 - w / 2) ** 2 + (y + 0.5 - w / 2) ** 2) ** 0.5
            if y < w / 2 and r > w / 2:
                continue
            frame = x < 2 or x >= w - 2 or y >= h - 2 or (y < w / 2 and r > w / 2 - 2)
            if frame:
                c = _rgb("d4aa45")
            elif (x - 2) % 6 == 5 or y % 6 == 5:
                c = _rgb("2c2a26")
            else:
                c = _rgb("ffe9a3") if (x + y) % 7 < 2 else _rgb("f2c25a")
            px[u + x, v + y] = c + (255,)

    # sails: courses carry a red cross, topsails plain, triangles with transparent outside
    _sail_cloth(px, REGIONS["course"], rng)
    _sail_cloth(px, REGIONS["topsail"], rng)
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

    # ---- flags: white field, blue fleur-de-lis; white / red pennant
    flag = Image.new("RGBA", (FLAG_SIZE, FLAG_SIZE), (0, 0, 0, 0))
    fp = flag.load()
    _, u, v, w, h = REGIONS["flag"]
    lis = [
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
    lh, lw = len(lis), len(lis[0])
    scale = 2
    ox, oy = (w - lw * scale) // 2, (h - lh * scale) // 2
    for y in range(h):
        for x in range(w):
            # white field like the reference, blue fleur-de-lis
            c = _jitter(_rgb("f1efe8"), rng, 4)
            lx, ly = (x - ox) // scale, (y - oy) // scale
            if 0 <= lx < lw and 0 <= ly < lh and lis[ly][lx] == "#":
                c = _jitter(_rgb("23439a"), rng, 6)
            fp[u + x, v + y] = c + (255,)
    _, u, v, w, h = REGIONS["pennant"]
    for y in range(h):
        for x in range(w):
            c = _rgb("f1efe8") if (y < h // 2) else _rgb("b3221c")
            fp[u + x, v + y] = _jitter(c, rng, 6) + (255,)
    flag.save(flag_path)
    return img, flag


def make_item_icon(path):
    """16x16 inventory icon: galleon seen from the side."""
    icon = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = icon.load()
    hull = _rgb("6b4423")
    dark = _rgb("3e2614")
    red = _rgb("9b2220")
    gold = _rgb("d4aa45")
    sail = _rgb("efe6d2")
    cross = _rgb("b3221c")
    mast = _rgb("4a2e15")
    roof = _rgb("b8352a")
    # hull
    for x in range(1, 15):
        p[x, 12] = hull + (255,)
    for x in range(2, 14):
        p[x, 13] = dark + (255,)
    for x in range(4, 12):
        p[x, 14] = dark + (255,)
    for x in range(0, 15):
        p[x, 11] = red + (255,) if 3 < x < 11 else hull + (255,)
    # castles
    for y in (9, 10):
        for x in range(0, 4):
            p[x, y] = hull + (255,)
        for x in range(12, 15):
            p[x, y] = hull + (255,)
    for x in range(0, 4):
        p[x, 8] = gold + (255,)
    for x in range(1, 3):
        p[x, 7] = roof + (255,)
    p[13, 8] = gold + (255,)
    # bowsprit
    p[15, 9] = mast + (255,)
    # masts and sails
    for y in range(1, 11):
        p[8, y] = mast + (255,)
    for y in range(3, 11):
        p[12, y] = mast + (255,)
    for y in range(7, 11):
        p[3, y] = mast + (255,)
    for y in range(3, 9):
        for x in range(6, 11):
            p[x, y] = (cross if x == 8 or y == 5 else sail) + (255,)
    for y in range(1, 3):
        for x in range(7, 10):
            p[x, y] = sail + (255,)
    for y in range(4, 8):
        for x in range(11, 14):
            p[x, y] = sail + (255,)
    p[8, 0] = _rgb("1f3f8f") + (255,)
    p[9, 0] = gold + (255,)
    icon.save(path)
