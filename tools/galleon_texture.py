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
    # deck fittings, helm, cabin (free band under the interior regions)
    "bronze": (0, 0, 416, 32, 16),
    "compass": (0, 32, 416, 16, 16),
    "velvet": (0, 48, 416, 32, 16),
    "curtain": (0, 80, 416, 32, 32),
    "boat": (0, 112, 416, 64, 32),
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
            fx = x / w
            # the belly catches the light, the leeches and the head fall into shade
            k = cloth_tone[x // 12] * (1.0 - 0.07 * abs(fy - 0.4)) - 0.04 * max(0.0, fy - 0.75)
            k -= 0.09 * (2 * abs(fx - 0.5)) ** 2 + 0.05 * max(0.0, 0.12 - fy) / 0.12
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
                c = tuple(int(q * 0.84) for q in c)
            elif x % 12 == 10:
                c = tuple(min(255, int(q * 1.04)) for q in c)
            elif x % 12 == 0 and y % 3 == 1:
                c = tuple(int(q * 0.93) for q in c)  # stitching of the seam
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


# ---------------------------------------------------------------- finer materials (second pass)
def _mix(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def _scale(c, k):
    return tuple(max(0, min(255, int(round(x * k)))) for x in c)


def _streaks(rng, w):
    """Smooth 1D brightness profile along a plank row: long soft waves and a few dark grain streaks."""
    f1, f2 = rng.uniform(0.05, 0.12), rng.uniform(0.18, 0.35)
    p1, p2 = rng.uniform(0, 6.3), rng.uniform(0, 6.3)
    prof = [0.045 * math.sin(x * f1 + p1) + 0.025 * math.sin(x * f2 + p2) for x in range(w)]
    for _ in range(max(1, w // 18)):
        x0, n = rng.randrange(w), rng.randint(3, 11)
        d = rng.uniform(0.06, 0.12)
        for k in range(n):
            prof[(x0 + k) % w] -= d * math.sin(math.pi * (k + 0.5) / n)
    return prof


def _wood(px, region, base, dark, rng, plank_h=4, joints=True, nails=False, knots=0.25, caulk=None, light=0.09):
    """Fine wood planking: per plank tone, smooth grain streaks along the plank, a rounded edge highlight,
    a dark seam (caulking), staggered butt joints with their nails, a few knots."""
    u, v, w, h = region
    base, dark = _rgb(base), _rgb(dark)
    caulk = _rgb(caulk) if caulk else dark
    for r in range(h // plank_h):
        k = rng.uniform(0.93, 1.07)
        hue = rng.uniform(-6, 6)
        tone = tuple(max(0, min(255, int(c))) for c in (base[0] * k + hue, base[1] * k, base[2] * k - hue * 0.5))
        joint = rng.randint(8, w - 8) if joints else None
        profs = [_streaks(rng, w) for _ in range(plank_h)]
        knot = rng.randrange(w) if rng.random() < knots else None
        for y in range(plank_h):
            yy = r * plank_h + y
            for x in range(w):
                if y == plank_h - 1:
                    c = caulk
                elif joint is not None and x == joint:
                    c = _mix(caulk, tone, 0.45)
                else:
                    kk = 1.0 + profs[y][x]
                    if y == 0:
                        kk += light          # rounded upper edge catches the light
                    elif y == plank_h - 2:
                        kk -= 0.05           # and the lower edge falls into shade
                    if joint is not None and abs(x - joint) <= 2:
                        kk -= 0.03 * (3 - abs(x - joint)) / 3
                    c = _scale(tone, kk)
                    if knot is not None and plank_h > 3:
                        d = ((x - knot) / 2.2) ** 2 + (y - (plank_h - 1) / 2 + 0.5) ** 2
                        if d < 0.6:
                            c = _scale(dark, 1.05)
                        elif d < 1.8:
                            c = _scale(tone, 0.8)
                    if nails and joint is not None and abs(x - joint) == 2 and y == 1:
                        c = _mix(_rgb("2a2622"), tone, 0.5)
                px[u + x, v + yy] = _jitter(c, rng, 2) + (255,)


def _moulding(px, region, base, rng, profile):
    """Moulded trim: the brightness follows a row profile (repeated), grain streaks along the length."""
    u, v, w, h = region
    base = _rgb(base)
    profs = [_streaks(rng, w) for _ in range(h)]
    for y in range(h):
        k0 = profile[y % len(profile)]
        for x in range(w):
            px[u + x, v + y] = _jitter(_scale(base, k0 + profs[y][x] * 0.7), rng, 2) + (255,)


def _mast_wood(px, region, base, rng):
    """Spar timber: long grain streaks along the length (u), no cross bands."""
    u, v, w, h = region
    base = _rgb(base)
    profs = [_streaks(rng, w) for _ in range(h)]
    for y in range(h):
        for x in range(w):
            k = 1.0 + profs[y][x] * 1.2 + 0.03 * math.sin(y * 1.3)
            px[u + x, v + y] = _jitter(_scale(base, k), rng, 2) + (255,)


def _gold_rich(px, region, rng):
    """Gilded carving: bands of mouldings (a bright bead line, a row of carved beads, a shadowed cove),
    with soft burnished highlights."""
    u, v, w, h = region
    hi, br, mid, lo, deep = _rgb("fff0b8"), _rgb("f2cf6a"), _rgb("d9a93e"), _rgb("a87a24"), _rgb("6e4a14")
    for y in range(h):
        for x in range(w):
            ry_ = y % 8
            sheen = 0.5 + 0.5 * math.sin(x * 0.21 + y * 0.09 + math.sin(y * 0.5) * 0.8)
            if ry_ == 0:
                c = _mix(br, hi, sheen)
            elif ry_ == 1:
                c = _mix(mid, br, sheen)
            elif ry_ in (2, 3, 4):
                bx = (x + (2 if (y // 8) % 2 else 0)) % 4      # carved beads
                d = (bx - 1.5) ** 2 + (ry_ - 3) ** 2
                c = hi if d < 0.6 else (br if d < 1.6 else (lo if bx == 3 else mid))
                c = _mix(c, mid, 0.15 * (1 - sheen))
            elif ry_ == 5:
                c = _mix(lo, mid, sheen)
            elif ry_ == 6:
                c = deep
            else:
                c = _mix(mid, br, sheen * 0.6)
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _carving_rich(px, region, rng):
    """Gilded scrollwork on a dark red ground: a running S-scroll with curls and bead borders."""
    u, v, w, h = region
    ground = _rgb("4e1810")
    for y in range(h):
        for x in range(w):
            c = _scale(ground, 1.0 + 0.08 * math.sin(x * 0.7) * math.sin(y * 0.9))
            if y < 2 or y >= h - 2:
                c = _rgb("f6dc8a") if (x + y) % 2 == 0 else _rgb("b98a2c")
            else:
                ph = 2 * math.pi * x / 16
                yc = h / 2 - 0.5 + 3.6 * math.sin(ph)
                d = abs(y - yc)
                cx = round((x - 4) / 8) * 8 + 4
                cy = h / 2 - 0.5 - 3.0 * math.sin(2 * math.pi * cx / 16)
                ring = math.hypot(x - cx, (y - cy) * 1.2)
                if d < 1.3:
                    c = _mix(_rgb("e2b34c"), _rgb("fff0b0"), 0.5 + 0.5 * math.cos(ph))
                elif d < 1.9:
                    c = _rgb("8a5e1c")
                elif 1.4 < ring < 2.5 and d > 2.2:
                    c = _rgb("e8c35a") if y < cy else _rgb("a87a24")
                elif ring <= 0.9 and d > 2.2:
                    c = _rgb("fff0b0")
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _leaded_window(px, region, rng, lit):
    """Window: bevelled frame, wooden cross mullion, diamond leaded panes with a reflection (or a warm glow)."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            edge = min(x, y, w - 1 - x, h - 1 - y)
            if edge < 3:
                ramp = [_rgb("7a5426"), _rgb("5a3a1c"), _rgb("3e2812")] if lit else [_rgb("f2d27a"), _rgb("c9a043"), _rgb("8a6a24")]
                c = ramp[edge]
                c = _scale(c, 1.12) if (x < 3 or y < 3) and x + y < w else _scale(c, 0.85)
            elif abs(x - (w - 1) / 2) < 1.0 or abs(y - (h - 1) / 2) < 1.0:
                c = _rgb("6a4520") if lit else _rgb("4a3018")
            elif (x + y) % 6 == 0 or (x - y) % 6 == 0:
                c = _rgb("3a2a1a") if lit else _rgb("2a2622")
            elif lit:
                d = math.hypot(x - w / 2, y - h * 0.55) / (w * 0.6)
                c = _mix(_rgb("fff0b0"), _rgb("e0901f"), min(1.0, d * 1.2))
            else:
                c = _mix(_rgb("8fb4cf"), _rgb("2c4660"), min(1.0, (x + y) / (w + h) * 1.4))
                if 0.25 < (x - y + h) / (w + h) < 0.33:
                    c = _mix(c, _rgb("e8f4fa"), 0.6)   # diagonal reflection
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _red_paint(px, region, rng):
    """Red painted planks: deep crimson with a soft sheen, dark seams, a little wear showing the wood."""
    u, v, w, h = region
    base = _rgb("9c1f1b")
    for r in range(h // 4):
        k = rng.uniform(0.95, 1.05)
        prof = _streaks(rng, w)
        for y in range(4):
            for x in range(w):
                if y == 3:
                    c = _rgb("3e0c0a")
                else:
                    c = _scale(base, k * (1.0 + prof[x] * 0.5 + (0.1 if y == 0 else (-0.06 if y == 2 else 0.0))))
                    if rng.random() < 0.01:
                        c = _rgb("6a4020")
                px[u + x, v + r * 4 + y] = _jitter(c, rng, 2) + (255,)


def _grating_rich(px, region, rng):
    """Hatch grating: raised lattice of light battens (lit on top, shaded below) over dark holes."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            gx, gy = x % 5, y % 5
            if gx < 2 and gy < 2:
                c = _rgb("c48f4f") if gx == 0 and gy == 0 else _rgb("a8763e")
            elif gy < 2:
                c = _rgb("9a6a36") if gy == 0 else _rgb("7e5428")
            elif gx < 2:
                c = _rgb("94653a") if gx == 0 else _rgb("74502a")
            else:
                c = _rgb("140d07") if gy == 2 else _rgb("22170d")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _door_rich(px, region, rng):
    """Plank door: vertical planks with grain, gilt frame, iron strap hinges with nails, ring handle."""
    u, v, w, h = region
    tones = [_scale(_rgb("6a4420"), rng.uniform(0.92, 1.06)) for _ in range(8)]
    profs = [_streaks(rng, h) for _ in range(w)]
    for y in range(h):
        for x in range(w):
            if x < 2 or x >= w - 2 or y < 2:
                c = _rgb("e2bd5c") if (x == 0 or y == 0) else _rgb("a87a24")
            elif (x - 2) % 5 == 4:
                c = _rgb("2e1c0c")
            else:
                c = _scale(tones[(x - 2) // 5], 1.0 + profs[x][y])
                if y in (7, 8, 22, 23) and x < w - 6:
                    c = _rgb("3c3c40") if y in (7, 22) else _rgb("26262a")
                    if x % 4 == 1 and y in (7, 22):
                        c = _rgb("6a6a70")
                rr = (x - (w - 8)) ** 2 + (y - 15.5) ** 2
                if 1.5 < rr < 4.5:
                    c = _rgb("d4aa45")
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _iron_rich(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("3c3b3a"), 1.0 + 0.08 * math.sin(x * 0.9 + y * 0.4) * math.cos(y * 0.7 - x * 0.2))
            if rng.random() < 0.06:
                c = _scale(c, 0.8)
            if y == 0:
                c = _scale(c, 1.25)
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _rope_rich(px, region, rng):
    """Tarred laid rope: diagonal strands, each lit on one side."""
    u, v, w, h = region
    cols = [_rgb("74604a"), _rgb("5a4834"), _rgb("44362a"), _rgb("2e241a"), _rgb("2e241a")]
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = _jitter(cols[(x + 2 * y) % 5], rng, 2) + (255,)


def _bronze(px, region, rng):
    """Cast bronze of the guns: brown-gold metal, a burnished highlight band, dark green patina spots."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            t = y / (h - 1)
            c = _scale(_rgb("a27a3a"), 0.75 + 0.5 * math.exp(-((t - 0.3) / 0.18) ** 2) - 0.15 * t)
            if rng.random() < 0.03:
                c = _mix(c, _rgb("4a6a4a"), 0.3)
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _compass(px, region, rng):
    """Compass card under glass: white card, black and red points, brass ring."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            dx, dy = x - (w - 1) / 2, y - (h - 1) / 2
            r, a = math.hypot(dx, dy), math.atan2(dy, dx)
            if r > w / 2 - 1.5:
                c = _rgb("d4aa45") if r < w / 2 + 0.5 else _rgb("8a6a24")
            else:
                c = _rgb("efe9d8")
                if r < (w / 2 - 2) * (1 - 0.85 * abs(math.sin(2 * a))) ** 2 + 0.8:
                    c = _rgb("b3221c") if abs(a + math.pi / 2) < 0.4 else _rgb("2a2622")
                elif r < 1.0:
                    c = _rgb("d4aa45")
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _velvet(px, region, rng):
    """Red velvet cushion: soft folds, gold piping on the edges, buttons."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            if y == 0 or y == h - 1:
                c = _rgb("e2bd5c")
            else:
                c = _scale(_rgb("8e1a22"), 1.0 + 0.12 * math.sin(x * 0.8) * math.sin(y * 0.6) - 0.08 * abs(y - h / 2) / (h / 2))
                if x % 8 == 4 and y == h // 2:
                    c = _rgb("d4aa45")
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _curtain(px, region, rng):
    """Draped curtain: vertical folds of crimson cloth, a gold fringe at the foot and a tie-back."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("9a1c22"), 0.82 + 0.25 * (0.5 + 0.5 * math.sin(x * 2 * math.pi / 6 + 0.3 * math.sin(y * 0.2))))
            if y < 2 or abs(y - h * 0.62) < 1.2:
                c = _rgb("d4aa45")
            elif y >= h - 3:
                c = _rgb("e2bd5c") if (x + y) % 2 else _rgb("a87a24")
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def make_textures(path, flag_path, lateen_tri, jib_tri):
    rng = random.Random(1588)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()

    def reg(name):
        return REGIONS[name][1:]

    # fine planking: grain streaks, rounded edges, caulked seams, butt joints with nails, knots
    _wood(px, reg("hull_dark"), "5a3a1e", "2f1d0e", rng, nails=True)
    _wood(px, reg("hull_mid"), "8f5f2e", "553719", rng, nails=True)
    # natural golden wood of the reference (hull, castles) and its lighter trim beams
    _wood(px, reg("wood_honey"), "c58f4a", "7f5426", rng, nails=True, caulk="5e3b1a")
    _moulding(px, reg("wood_trim"), "e0b56a", rng, (1.14, 1.06, 1.0, 0.96, 0.9, 0.72, 0.95, 0.8))
    _wood(px, reg("hull_light"), "b07a3c", "6e4a22", rng)
    _red_paint(px, reg("red_paint"), rng)
    _moulding(px, reg("wale"), "2e221a", rng, (1.25, 1.12, 1.0, 0.85))
    _wood(px, reg("dark_wood"), "4e321a", "2b1a0c", rng, knots=0.15)
    _wood(px, reg("deck"), "a87542", "5c3c1e", rng, nails=True, caulk="5e4228", knots=0.2, light=0.06)
    # treenails: pairs of pegs across every plank at the deck beams
    u, v, w, h = reg("deck")
    for y in range(0, h, 4):
        for x in range((y // 4) * 5 % 16, w, 16):
            for yy in (y, y + 2):
                r, g, b, a = px[u + x, v + yy]
                px[u + x, v + yy] = (int(r * 0.78), int(g * 0.76), int(b * 0.74), 255)
    _moulding(px, reg("rail"), "9a6a36", rng, (1.18, 1.1, 1.02, 1.0, 0.97, 0.92, 0.85, 0.72))
    _mast_wood(px, reg("mast"), "7a4f27", rng)
    _wood(px, reg("blue_paint"), "27407a", "17264a", rng, joints=False, knots=0.0)
    _iron_rich(px, reg("iron"), rng)
    _fill(img, reg("end_grain"), _rgb("8c5e30"), rng, 10)
    u, v, w, h = reg("end_grain")   # growth rings
    for y in range(h):
        for x in range(w):
            r_ = math.hypot(x - w / 2 + 0.5, y - h / 2 + 0.5)
            if int(r_ * 1.1) % 3 == 0:
                c = px[u + x, v + y]
                px[u + x, v + y] = (int(c[0] * 0.8), int(c[1] * 0.78), int(c[2] * 0.76), 255)

    # gold: carved mouldings with burnished highlights; scrollwork friezes
    _gold_rich(px, reg("gold"), rng)
    _carving_rich(px, reg("carving"), rng)
    _rope_rich(px, reg("rope"), rng)
    _bronze(px, reg("bronze"), rng)
    _compass(px, reg("compass"), rng)
    _velvet(px, reg("velvet"), rng)
    _curtain(px, reg("curtain"), rng)
    # ship's boat: white-painted strakes with a red sheer strake
    _wood(px, reg("boat"), "d9cfb8", "8a7a62", rng, joints=False, knots=0.0)
    u, v, w, h = reg("boat")
    for y in range(h - 8, h):
        for x in range(w):
            c = px[u + x, v + y]
            px[u + x, v + y] = (min(255, int(c[0] * 0.75)), int(c[1] * 0.2), int(c[2] * 0.2), 255)
    # roof tiles (red, overlapping rows)
    u, v, w, h = reg("roof")
    for y in range(h):
        for x in range(w):
            row = y // 6
            off = 4 if row % 2 else 0
            # rounded tiles: lit on their crown, shaded at their sides and under the next row
            tx = ((x + off) % 8) / 8.0
            ty = (y % 6) / 6.0
            k = 0.82 + 0.3 * math.sin(math.pi * tx) - 0.18 * ty
            c = _scale(_rgb("b8352a"), k)
            if y % 6 == 5 or (x + off) % 8 == 0:
                c = _rgb("6a140f")
            elif y % 6 == 0:
                c = _mix(c, _rgb("e2735a"), 0.4)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    # windows: leaded diamond panes in a bevelled gilt frame; glowing variant (lit cabin)
    _leaded_window(px, reg("window"), rng, lit=False)
    _leaded_window(px, reg("glow_window"), rng, lit=True)
    _door_rich(px, reg("door"), rng)
    _grating_rich(px, reg("grating"), rng)
    # painted panel: red field, bevelled gold frame, blue medallion with a gilt ring and a fleuron
    u, v, w, h = reg("panel")
    for y in range(h):
        for x in range(w):
            fx, fy = x % 32, y
            edge = min(fx, fy, 31 - fx, h - 1 - fy)
            r2 = (fx - 15.5) ** 2 + (fy - 15.5) ** 2
            if edge < 3:
                c = [_rgb("f2d27a"), _rgb("d4aa45"), _rgb("8a6a24")][edge]
                if fx > fy and 31 - fx > h - 1 - fy:
                    c = _scale(c, 0.9)
            elif r2 < 46:
                if r2 < 26:
                    c = _rgb("27407a") if r2 > 4 and not (abs(fx - 15.5) < 0.6 or abs(fy - 15.5) < 0.6) else _rgb("e8c35a")
                elif r2 < 34:
                    c = _rgb("f2d27a")
                else:
                    c = _rgb("a87a24")
            else:
                c = _scale(_rgb("8f1f1b"), 1.0 + 0.06 * math.sin(fx * 0.5 + fy * 0.3) - (0.12 if edge == 3 else 0.0))
                if edge == 5 and (fx + fy) % 2 == 0:
                    c = _rgb("c9a043")      # gilt fillet inside the frame
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)
    # rolled (furled) canvas on the yards: soft spiral folds with gaskets
    u, v, w, h = reg("cloth_roll")
    for y in range(h):
        for x in range(w):
            k = 0.86 + 0.16 * math.sin(2 * math.pi * (x + y * 0.6) / 7.0) - 0.1 * abs(y - h / 2) / (h / 2)
            c = _scale(_rgb("e2d6bb"), k)
            if x % 21 in (0, 1):
                c = _rgb("6a5640")      # gasket
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)
    # lantern frame and glow
    u, v, w, h = reg("lantern")
    paint_lamp_glass(px, u, v, w, h)
    u, v, w, h = reg("glow")
    for y in range(h):
        for x in range(w):
            d = abs(x - w / 2 + 0.5) + abs(y - h / 2 + 0.5)
            px[u + x, v + y] = (_rgb("fff1a8") if d < 5 else _rgb("ffc94a")) + (255,)
    # gun port: bevelled frame, red-painted lining, dark opening (darker towards the top)
    u, v, w, h = reg("gunport")
    for y in range(h):
        for x in range(w):
            edge = min(x, y, w - 1 - x, h - 1 - y)
            if edge < 2:
                c = _rgb("7a5226") if edge == 0 else _rgb("5e3f1d")
                if y > x and h - 1 - y < w - 1 - x:
                    c = _scale(c, 0.8)
            elif edge == 2:
                c = _rgb("8f1f1b") if y > 2 else _rgb("5a1210")
            else:
                c = _mix(_rgb("060403"), _rgb("1e140c"), y / h)
            px[u + x, v + y] = c + (255,)

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
            # fluted shaft (lit flutes, dark grooves), volute capital on top, moulded base
            if y < 4 or y >= h - 4:
                yy = y if y < 4 else h - 1 - y
                c = [_rgb("fff0b8"), _rgb("e2b34c"), _rgb("a87a24"), _rgb("f2cf6a")][yy]
                if y < 4 and (x in (0, w - 1)) and yy in (1, 2):
                    c = _rgb("fff0b8")     # volutes
            else:
                c = [_rgb("8a6a24"), _rgb("f2cf6a"), _rgb("d4aa45"), _rgb("7a5a1c"), _rgb("f2cf6a"), _rgb("d4aa45"),
                     _rgb("7a5a1c"), _rgb("6e4a14")][x % 8]
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)
    u, v, w, h = reg("arch_window")
    for y in range(h):
        for x in range(w):
            r = ((x + 0.5 - w / 2) ** 2 + (y + 0.5 - w / 2) ** 2) ** 0.5
            if y < w / 2 and r > w / 2:
                continue
            frame = x < 2 or x >= w - 2 or y >= h - 2 or (y < w / 2 and r > w / 2 - 2)
            if frame:
                c = _rgb("f2d27a") if (x < 2 and x == 0) or (y < w / 2 and r > w / 2 - 1) else _rgb("b98a2c")
            elif abs(x - (w - 1) / 2) < 0.6 or y == w // 2:
                c = _rgb("5a3a1c")       # mullion and transom
            elif (x + y) % 4 == 0 or (x - y) % 4 == 0:
                c = _rgb("3a2a1a")       # diamond leading
            else:
                d = math.hypot(x + 0.5 - w / 2, y - h * 0.6) / h
                c = _mix(_rgb("fff0b0"), _rgb("e8962a"), min(1.0, d * 2.0))
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
