"""Texture of the Sky Leviathan (sky_leviathan).

  sky_leviathan.png   512x512 atlas, regions in REGIONS (u, v, w, h)

Colours of the reference sheet: aged turquoise plates on the balloon (long strips with dark seams and
pale streaks of wear), big brown wooden panels on its sides, wooden hoops of stacked blocks, black
iron fittings, black cloth (swags, tattered pennants, sails, the bat-wing fins), a dark brown pirate
hull with black wales, warm lantern light in the windows and portholes; inside, dark planked walls
with beams, worn plank floors, red runners and rugs.
"""
import math
import random

from PIL import Image, ImageDraw

from galley_texture import _jitter, _rgb, _mix, _scale, fine_wood, polished_metal, hammered_iron, woven, twisted_rope, \
    end_grain, paint_lamp_glass, GOLD_STOPS
import leviathan_shape as ls

SIZE = 512

REGIONS = {
    # balloon
    "plate":        (0, 0, 64, 64),     # aged turquoise strips (run along u)
    "plate_dark":   (64, 0, 64, 64),    # the same, darker and more worn (underside, ends)
    "wood_panel":   (128, 0, 64, 64),   # brown planks of the big side panels (along u)
    "hoop":         (192, 0, 32, 16),   # wooden blocks of the hoops
    "hoop_end":     (192, 16, 16, 16),  # end grain of a hoop block
    "strap":        (208, 16, 16, 16),  # riveted black iron strap
    "band":         (224, 0, 32, 16),   # dark wooden band along the balloon
    "plate_in":     (224, 16, 16, 16),  # inside of the balloon skin (never seen)
    "emblem":       (240, 16, 16, 16),  # the end cap of the tail: a gold sigil on black iron
    # metals
    "iron":         (256, 0, 16, 16),
    "steel":        (272, 0, 16, 16),   # pale worn steel (the gear emblem)
    "brass":        (288, 0, 16, 16),
    "gold":         (304, 0, 16, 16),
    "copper":       (320, 0, 16, 16),
    "chain":        (336, 0, 16, 16),
    "rope":         (352, 0, 16, 16),
    "rope_dark":    (368, 0, 16, 16),
    "glow":         (384, 0, 16, 16),
    "lantern":      (400, 0, 16, 16),
    "glass":        (416, 0, 16, 16),
    "gauge":        (432, 0, 16, 16),
    "wax":          (448, 0, 16, 16),
    "pearl":        (464, 0, 16, 16),
    "coral_red":    (480, 0, 16, 16),   # red enamel (valve wheels)
    "organ_wood":   (496, 0, 16, 16),   # dark polished wood
    "steel_dark":   (256, 16, 16, 16),
    "chart":        (272, 16, 32, 16),
    "bedding":      (304, 16, 16, 16),
    "red_velvet":   (320, 16, 16, 16),
    "leather":      (336, 16, 16, 16),
    "coal":         (352, 16, 16, 16),
    "fire":         (368, 16, 16, 16),
    "porthole":     (384, 16, 16, 16),  # round lit porthole (transparent outside the circle)
    "window":       (400, 16, 16, 32),  # leaded lit window of the stern castle
    "end_grain":    (416, 16, 16, 16),
    "burlap":       (432, 16, 16, 16),
    "barrel":       (448, 16, 32, 16),
    "crate":        (480, 16, 32, 32),
    # cloth
    "cloth":        (0, 64, 32, 32),    # black draped cloth, folds along v
    "banner":       (32, 64, 32, 64),   # tattered black banner (ragged lower half, transparent tears)
    "pennant":      (64, 64, 16, 32),   # small tattered pennant
    "sail_black":   (80, 64, 48, 64),   # worn black sail, patched, ragged foot
    "flag":         (128, 64, 64, 32),  # the pirate flag: skull and crossed bones, tattered fly
    "fin":          (192, 64, 112, 128),  # the bat-wing fin (outline, holes, ribs, the spade)
    "fin_keel":     (304, 64, 112, 128),
    # hull and decks
    "hull":         (0, 128, 64, 32),   # dark brown planks along u
    "hull_low":     (0, 160, 64, 32),   # the bottom, darker and tarred
    "wale":         (64, 160, 32, 16),  # black wale
    "rail":         (64, 176, 32, 16),  # dark rail wood
    "dark_wood":    (96, 160, 32, 16),
    "wood":         (96, 176, 32, 16),
    "deck":         (128, 192, 32, 32),  # deck planks along u, 2 blocks
    "transom":      (160, 192, 32, 32),
    "gear_iron":    (416, 64, 16, 16),
    "door_leaf":    (432, 64, 32, 64),   # one leaf of a 2 block door (1 x 2): planks, iron straps
    "hatch":        (464, 64, 32, 32),
    "rung":         (496, 64, 16, 16),
    # rooms (2 block tiles, MAX_TILE cells)
    "wall_wood":    (0, 224, 32, 32),   # dark planks, a beam at the top
    "wall_panel":   (32, 224, 32, 32),  # captain's panelling with a red fabric band
    "wall_engine":  (64, 224, 32, 32),  # planks with iron straps and a copper pipe
    "floor":        (96, 224, 32, 32),  # worn plank floor
    "floor_iron":   (128, 224, 32, 32),  # iron grating
    "carpet":       (160, 224, 32, 32),  # red runner with a gold border
    "ceil_wood":    (192, 224, 32, 32),  # planks between dark beams
    "rug":          (224, 192, 64, 64),  # oriental rug
    "books":        (288, 192, 64, 32),
    "painting":     (288, 224, 32, 32),
}


def _shade(c, k):
    return tuple(max(0, min(255, int(q * k))) for q in c)


def _put(px, u, v, x, y, c, a=255):
    px[u + x, v + y] = tuple(int(q) for q in c[:3]) + (a,)


def _noise(w, h, cells, rng):
    """Smooth value noise in [-1, 1]."""
    grid = [[rng.uniform(-1, 1) for _ in range(cells + 2)] for _ in range(cells + 2)]
    out = [[0.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            gx, gy = x / w * cells, y / h * cells
            i, j = int(gx), int(gy)
            fx, fy = gx - i, gy - j
            fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
            a = grid[j][i] * (1 - fx) + grid[j][i + 1] * fx
            b = grid[j + 1][i] * (1 - fx) + grid[j + 1][i + 1] * fx
            out[y][x] = a * (1 - fy) + b * fy
    return out


def _plates(px, region, base, seam, light, rng, strip=8, wear=0.25):
    """Aged turquoise strips along u: each strip its own tone, a dark seam under it, butt joints with
    rivets, pale streaks of wear and darker rust stains (the reference's weathered copper-green)."""
    u, v, w, h = region
    nz = _noise(w, h, 5, rng)
    nz2 = _noise(w, h, 11, rng)
    for r in range(h // strip):
        tone = _jitter(base, rng, 7)
        joint = rng.randint(6, w - 7)
        for b in range(strip):
            y = r * strip + b
            for x in range(w):
                if b == strip - 1:
                    c = seam
                elif x == joint or x == (joint + w // 2) % w:
                    c = _mix(seam, tone, 0.35)
                else:
                    k = 1.0 + 0.1 * nz[y][x] + 0.05 * nz2[y][x]
                    if b == 0:
                        k += 0.07
                    c = _scale(tone, k)
                    t = nz2[y][x] * 0.5 + 0.5
                    if t > 0.82:
                        c = _mix(c, light, (t - 0.82) * 3.0 * wear * 2)
                    elif t < 0.12:
                        c = _mix(c, (78, 62, 44), (0.12 - t) * 4.0 * wear * 2)   # rust-brown stains
                    if abs(x - joint) in (2,) and b in (2, strip - 3):
                        c = _shade(seam, 1.1)
                c = _jitter(c, rng, 3)
                _put(px, u, v, x, y, c)


def _blocks(px, region, base, dark, rng, bw=8):
    """Stacked wooden blocks (hoops): each block its own tone, dark gaps, lit top edge."""
    u, v, w, h = region
    for i in range(w // bw):
        tone = _jitter(base, rng, 10)
        for x in range(bw):
            for y in range(h):
                if x == bw - 1 or y == h - 1:
                    c = dark
                else:
                    k = 1.0 + 0.06 * math.sin(y * 1.3 + i) + (0.08 if y == 0 or x == 0 else 0)
                    c = _jitter(_scale(tone, k), rng, 4)
                _put(px, u, v, i * bw + x, y, c)


def _strap(px, region, base, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            k = 1.0 + (0.12 if y < 2 else -0.15 if y > h - 3 else 0)
            c = _scale(base, k)
            if x % 8 == 3 and y in (h // 2 - 1, h // 2):
                c = (98, 92, 86)
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _cloth(px, region, base, rng, folds=10.0, alpha_fn=None):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            k = 1.0 + 0.16 * math.sin(2 * math.pi * x / folds) + 0.05 * math.sin(2 * math.pi * x / (folds * 0.37) + 1)
            k += 0.04 * ((x + y) % 2) - 0.02
            c = _jitter(_scale(base, k), rng, 3)
            a = 255
            if alpha_fn is not None and not alpha_fn(x, y):
                a = 0
            _put(px, u, v, x, y, c, a)


def _ragged(w, h, start, rng, teeth=5):
    """Mask of a tattered lower edge: the cloth reaches down to a ragged line with deep tears."""
    edge = []
    for x in range(w):
        e = start + (h - start) * (0.55 + 0.45 * math.sin(x * 1.7 + rng.uniform(0, 0.4)) ** 2)
        edge.append(e)
    for _ in range(teeth):
        x0 = rng.randint(0, w - 1)
        wd = rng.randint(1, 3)
        depth = rng.uniform(0.3, 0.8) * (h - start)
        for x in range(max(0, x0 - wd), min(w, x0 + wd + 1)):
            edge[x] = min(edge[x], start + (h - start) * 0.2 + rng.uniform(0, depth * 0.3))
    holes = [(rng.uniform(0, w), rng.uniform(start * 0.5, h * 0.8), rng.uniform(0.8, 1.8)) for _ in range(2)]

    def inside(x, y):
        if y > edge[x]:
            return False
        for hx, hy, r in holes:
            if math.hypot(x + 0.5 - hx, y + 0.5 - hy) < r:
                return False
        return True
    return inside


def _fin(px, region, root_u, rng, holes=True):
    """The bat-wing fin: black membrane with a soft sheen, darker ribs and leading-edge spar, the
    three holes near the tip, a faint spade emblem; transparent outside the outline."""
    u, v, w, h = region
    poly = ls.fin_outline(root_u)
    ribs = ls.fin_ribs(root_u)
    hole_list = ls.fin_holes() if holes else []
    base = _rgb("2a292f")
    nz = _noise(w, h, 6, rng)

    def seg_dist(p, a, b):
        ax, ay = a
        bx, by = b
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
        return math.hypot((p[0] - ax - dx * t) * w, (p[1] - ay - dy * t) * h)
    lead = [ls._bezier2((0.0, 0.0), (0.06, 0.78), ls.FIN_TIP, j / 24) for j in range(25)]
    for y in range(h):
        for x in range(w):
            fu, fv = (x + 0.5) / w, 1.0 - (y + 0.5) / h
            inside = ls.point_in_poly(fu, fv, poly)
            if inside and holes:
                for hx, hy in hole_list:
                    if (fu - hx) ** 2 + ((fv - hy) * ls.FIN_CHORD) ** 2 < ls.FIN_HOLE_R ** 2:
                        inside = False
                    elif (fu - hx) ** 2 + ((fv - hy) * ls.FIN_CHORD) ** 2 < (ls.FIN_HOLE_R * 1.6) ** 2:
                        inside = inside and True
            if not inside:
                _put(px, u, v, x, y, (0, 0, 0), 0)
                continue
            k = 1.0 + 0.1 * nz[y][x]
            # the membrane sags between the ribs: lighter in the middle of each panel
            d = min(seg_dist((fu, fv), a, b) for a, b in ribs)
            k += 0.12 * min(1.0, d / 6.0) - 0.04
            c = _scale(base, k)
            if d < 1.2:
                c = _rgb("141317")
            ld = min(seg_dist((fu, fv), lead[j], lead[j + 1]) for j in range(24))
            if ld < 2.2:
                c = _rgb("18171b") if ld < 1.4 else _rgb("38363e")
            for hx, hy in hole_list:
                dd = math.hypot((fu - hx) * w, (fv - hy) * h * 1.0)
                if dd < ls.FIN_HOLE_R * w * 1.7:
                    c = _rgb("4a4a52")   # a riveted iron ring round each hole
            # faint spade emblem in the middle of the fin
            ex, ey = (fu - 0.5) * w / 9.0, (fv - 0.45) * h / 9.0
            if holes and abs(ex) < 1.2 and -1.2 < ey < 1.0:
                r1 = math.hypot(ex - 0.45, ey - 0.15)
                r2 = math.hypot(ex + 0.45, ey - 0.15)
                top = ey > 0.15 and abs(ex) < (1.0 - (ey - 0.15) / 0.85) * 0.9
                stem = abs(ex) < 0.18 and -1.1 < ey < 0.0
                if r1 < 0.5 or r2 < 0.5 or top or stem:
                    c = _mix(c, _rgb("595863"), 0.55)
            _put(px, u, v, x, y, _jitter(c, rng, 2))


def _flag(px, region, rng):
    """The pirate flag: black, a white skull over crossed bones, the fly edge in tatters."""
    u, v, w, h = region
    tat = [w - 1 - int(rng.uniform(0, 6) * (0.5 + 0.5 * math.sin(y * 0.9))) for y in range(h)]
    for k in range(3):
        y0 = rng.randint(2, h - 6)
        for y in range(y0, y0 + rng.randint(2, 4)):
            tat[y] -= rng.randint(4, 9)
    for y in range(h):
        for x in range(w):
            if x > tat[y]:
                _put(px, u, v, x, y, (0, 0, 0), 0)
                continue
            c = _scale(_rgb("1e1c1d"), 1.0 + 0.08 * math.sin(x * 0.4) + 0.04 * ((x + y) % 2))
            cx, cy = w * 0.42, h * 0.45
            dx, dy = (x + 0.5 - cx) / (h * 0.22), (y + 0.5 - cy) / (h * 0.22)
            skull = dx * dx + (dy + 0.25) ** 2 < 0.55 or (abs(dx) < 0.45 and 0.1 < dy < 0.75)
            eye = (dx + 0.32) ** 2 + (dy + 0.05) ** 2 < 0.07 or (dx - 0.32) ** 2 + (dy + 0.05) ** 2 < 0.07
            nose = abs(dx) < 0.1 and 0.25 < dy < 0.4
            bone = False
            for s in (1, -1):
                bx, by = dx - s * (dy - 1.1) * 0.0, dy
                t = (dx * s + (dy - 1.05)) / 1.414
                n = (dx * s - (dy - 1.05)) / 1.414
                if abs(n) < 0.16 and abs(t) < 1.25:
                    bone = True
                if abs(t) > 1.05 and abs(t) < 1.35 and abs(n) < 0.3:
                    bone = True
            if (skull and not eye and not nose) or (bone and not skull):
                c = _rgb("e8e2d0") if (x + y) % 5 else _rgb("cfc8b4")
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _round(px, region, paint):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            dx, dy = (x + 0.5) / w * 2 - 1, (y + 0.5) / h * 2 - 1
            rr = math.hypot(dx, dy)
            if rr > 1.0:
                _put(px, u, v, x, y, (0, 0, 0), 0)
            else:
                _put(px, u, v, x, y, paint(rr, dx, dy))


def _window(px, region):
    """Leaded window lit from inside: warm amber panes in a diamond lead grid, a dark frame."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            if x in (0, w - 1) or y in (0, h - 1):
                c = (40, 28, 18)
            else:
                d1, d2 = (x + y) % 6, (x - y) % 6
                if d1 == 0 or d2 == 0:
                    c = (62, 48, 30)
                else:
                    g = 1.0 - 0.25 * abs((y + 0.5) / h - 0.55)
                    c = _scale((255, 200, 112), g)
            _put(px, u, v, x, y, c)


def _door_leaf(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            plank = x // 8
            tone = _scale(_rgb("5a3b25"), 1.0 + 0.06 * math.sin(plank * 2.1))
            c = _scale(tone, 1.0 + 0.05 * math.sin(y * 0.5 + plank))
            if x % 8 == 7:
                c = _rgb("2b1b10")
            if y in (6, 7, h - 8, h - 7) or (abs(y - h // 2) <= 1):
                c = _rgb("2a2a2c") if x % 6 else _rgb("6a6660")
            if x in (0, 1, w - 2, w - 1) or y in (0, 1, h - 2, h - 1):
                c = _rgb("3a2516")
            if x in (w - 6, w - 5) and abs(y - h // 2 - 4) <= 1:
                c = _rgb("8a7a52")   # handle
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _tile_room(img, px, rng):
    """Room surfaces: 2 block tiles (32 px), the walls' pattern spans the room height (v from the
    ceiling down to the floor, see generate_leviathan.surfaces)."""
    # planked wall: vertical planks, a dark beam under the ceiling and a skirting board
    def planked(region, base, top_band=None, mid_band=None, straps=False, pipe=False):
        u, v, w, h = region
        for y in range(h):
            for x in range(w):
                plank = x // 5
                tone = _scale(base, 1.0 + 0.07 * math.sin(plank * 2.7 + 0.4))
                c = _scale(tone, 1.0 + 0.04 * math.sin(y * 0.7 + plank * 1.3))
                if x % 5 == 4:
                    c = _scale(base, 0.55)
                if y < 3:
                    c = _scale(_rgb("2e1d12"), 1.0 + (0.1 if y == 0 else 0))
                if y > h - 3:
                    c = _rgb("33210f")
                if top_band and 6 <= y < 12:
                    c = _scale(top_band, 1.0 + 0.05 * ((x + y) % 2))
                if mid_band and y in (12, 13):
                    c = mid_band
                if straps and (x in (15, 16)):
                    c = _rgb("2c2b2d") if y % 6 else _rgb("77726a")
                if pipe and 14 <= y < 17:
                    c = _scale(_rgb("b06a3a"), 1.15 if y == 14 else 0.8 if y == 16 else 1.0)
                _put(px, u, v, x, y, _jitter(c, rng, 2))
    planked(REGIONS["wall_wood"], _rgb("5b3c25"))
    planked(REGIONS["wall_panel"], _rgb("4c2f1c"), top_band=_rgb("7a1f1c"), mid_band=_rgb("b08a3c"))
    planked(REGIONS["wall_engine"], _rgb("4e3523"), straps=True, pipe=True)
    fine_wood(img, REGIONS["floor"], _rgb("6b4b30"), _rgb("2f2014"), 4, rng, knots=0.2)
    fine_wood(img, REGIONS["deck"], _rgb("7a5838"), _rgb("33241a"), 4, rng, knots=0.15)
    # iron grating
    u, v, w, h = REGIONS["floor_iron"]
    for y in range(h):
        for x in range(w):
            c = _rgb("2a2a2c") if (x % 4 == 0 or y % 4 == 0) else _rgb("4a4846")
            _put(px, u, v, x, y, _jitter(c, rng, 3))
    # red runner with a gold border
    u, v, w, h = REGIONS["carpet"]
    for y in range(h):
        for x in range(w):
            c = _rgb("8a1f1c")
            if (x + y) % 8 == 0 or (x - y) % 8 == 0:
                c = _rgb("6e1715")
            if x in (2, 3, w - 4, w - 3):
                c = _rgb("c49a3c")
            if x < 2 or x > w - 3:
                c = _rgb("5b1210")
            _put(px, u, v, x, y, _jitter(c, rng, 4))
    # ceiling: planks along u, a dark beam across every 2 blocks
    u, v, w, h = REGIONS["ceil_wood"]
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("4a3020"), 1.0 + 0.05 * math.sin(y // 4 * 2.3))
            if y % 4 == 3:
                c = _rgb("24170d")
            if x < 4:
                c = _scale(_rgb("2f1e12"), 1.0 + (0.12 if x == 0 else 0))
            _put(px, u, v, x, y, _jitter(c, rng, 2))
    # oriental rug
    u, v, w, h = REGIONS["rug"]
    for y in range(h):
        for x in range(w):
            ex, ey = min(x, w - 1 - x), min(y, h - 1 - y)
            e = min(ex, ey)
            if e < 3:
                c = _rgb("3b1a12") if e < 1 else _rgb("c79a3e")
            elif e < 8:
                c = _rgb("7a1814") if (x + y) % 4 else _rgb("d4b060")
            else:
                dx, dy = (x - w / 2) / (w / 2 - 8), (y - h / 2) / (h / 2 - 8)
                r = abs(dx) + abs(dy)
                c = _rgb("9a2a20") if r > 0.6 else _rgb("1f2a4a") if r > 0.35 else _rgb("c9a046")
                if (x * 3 + y * 5) % 11 == 0:
                    c = _mix(c, _rgb("e0c890"), 0.5)
            _put(px, u, v, x, y, _jitter(c, rng, 3))
    # books on a shelf
    u, v, w, h = REGIONS["books"]
    x = 0
    cols = ["7a1f1c", "1f3a5a", "2f5a2a", "6a4a20", "3a2a4a", "8a6a2a"]
    while x < w:
        bw = rng.randint(2, 4)
        top = rng.randint(2, 7)
        col = _rgb(rng.choice(cols))
        for xx in range(x, min(w, x + bw)):
            for y in range(h):
                c = _rgb("2a1a10") if y < top else _scale(col, 1.0 + (0.15 if xx == x else 0))
                if y == top + 3 or y == h - 5:
                    c = _rgb("c8a24a") if y >= top else c
                _put(px, u, v, xx, y, _jitter(c, rng, 3))
        x += bw
    # a dark sea painting
    u, v, w, h = REGIONS["painting"]
    for y in range(h):
        for x in range(w):
            t = y / h
            c = _mix(_rgb("c9905a"), _rgb("3a5068"), t * 1.6) if t < 0.55 else _mix(_rgb("2a4058"), _rgb("16222e"), (t - 0.55) * 2)
            if 0.4 < t < 0.62 and abs(x - w * 0.45) < 6 - (t - 0.4) * 20:
                c = _rgb("2a1a10")   # a ship's silhouette
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def make_texture(path):
    rng = random.Random(9)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    # ---- balloon
    _plates(px, REGIONS["plate"], _rgb("6b877a"), _rgb("33463f"), _rgb("9fb8a6"), rng, strip=12, wear=0.35)
    _plates(px, REGIONS["plate_dark"], _rgb("566f63"), _rgb("27362f"), _rgb("8aa090"), rng, strip=12, wear=0.45)
    fine_wood(img, REGIONS["wood_panel"], _rgb("6a4429"), _rgb("2c1a0e"), 4, rng, knots=0.2, grain=0.13)
    _blocks(px, REGIONS["hoop"], _rgb("7c5434"), _rgb("2e1c10"), rng)
    end_grain(img, REGIONS["hoop_end"], _rgb("8a6440"), _rgb("4a3020"), rng)
    _strap(px, REGIONS["strap"], _rgb("2c2a2a"), rng)
    fine_wood(img, REGIONS["band"], _rgb("4e3320"), _rgb("22150b"), 8, rng, knots=0.0)
    hammered_iron(img, REGIONS["plate_in"], _rgb("2a2622"), rng)
    u, v, w, h = REGIONS["emblem"]
    for y in range(h):
        for x in range(w):
            dx, dy = x - 7.5, y - 7.5
            r = math.hypot(dx, dy)
            c = _rgb("1f1e1f")
            if 4.5 < r < 6.0 or (r < 3.2 and (abs(dx) < 0.8 or abs(dy) < 0.8)):
                c = _rgb("b8913c")
            _put(px, u, v, x, y, _jitter(c, rng, 2))
    # ---- metals and small parts
    hammered_iron(img, REGIONS["iron"], _rgb("2e2c2b"), rng)
    polished_metal(img, REGIONS["steel"], [(0.0, (70, 72, 76)), (0.5, (128, 130, 134)), (1.0, (190, 192, 196))], rng)
    polished_metal(img, REGIONS["brass"], [(0.0, (92, 64, 24)), (0.5, (170, 128, 52)), (1.0, (232, 196, 110))], rng)
    polished_metal(img, REGIONS["gold"], GOLD_STOPS, rng)
    polished_metal(img, REGIONS["copper"], [(0.0, (90, 44, 22)), (0.5, (170, 96, 52)), (1.0, (226, 150, 100))], rng)
    hammered_iron(img, REGIONS["steel_dark"], _rgb("3a3a3e"), rng)
    u, v, w, h = REGIONS["chain"]
    for y in range(h):
        for x in range(w):
            ring = (y % 6) in (0, 5) or x in (5, 10)
            inner = 5 < x < 10 and 0 < y % 6 < 5
            c = _rgb("5a5856") if ring and not inner else _rgb("2a2928")
            _put(px, u, v, x, y, _jitter(c, rng, 4))
    twisted_rope(img, REGIONS["rope"], _rgb("b4945e"), _rgb("6e5432"), rng)
    twisted_rope(img, REGIONS["rope_dark"], _rgb("7a6040"), _rgb("3e2e1c"), rng)
    u, v, w, h = REGIONS["glow"]
    for y in range(h):
        for x in range(w):
            _put(px, u, v, x, y, _jitter((255, 214, 130), rng, 6))
    paint_lamp_glass(px, *REGIONS["lantern"])
    u, v, w, h = REGIONS["glass"]
    for y in range(h):
        for x in range(w):
            _put(px, u, v, x, y, _jitter((150, 180, 170), rng, 6))
    _round(px, REGIONS["gauge"], lambda rr, dx, dy: (30, 26, 20) if rr > 0.85 else (34, 30, 26) if abs(dx - dy * 0.3) < 0.08 and dy < 0 else (232, 222, 196))
    for name, col in (("wax", "e8dcc0"), ("pearl", "e6e2da"), ("coral_red", "a4241c"), ("bedding", "e0d8c4"), ("red_velvet", "7a1a18"),
                      ("leather", "5a3420"), ("coal", "1c1a1a"), ("burlap", "9a8058")):
        u, v, w, h = REGIONS[name]
        for y in range(h):
            for x in range(w):
                _put(px, u, v, x, y, _jitter(_scale(_rgb(col), 1.0 + 0.05 * math.sin(x * 0.8 + y * 0.5)), rng, 5))
    polished_metal(img, REGIONS["organ_wood"], [(0.0, (40, 22, 12)), (0.5, (78, 46, 26)), (1.0, (120, 76, 44))], rng)
    u, v, w, h = REGIONS["fire"]
    for y in range(h):
        for x in range(w):
            t = y / h
            c = _mix((255, 236, 140), (220, 80, 20), t + 0.2 * math.sin(x * 1.3))
            _put(px, u, v, x, y, _jitter(c, rng, 10))
    _round(px, REGIONS["porthole"], lambda rr, dx, dy: (40, 30, 20) if rr > 0.86 else _scale((255, 226, 150), 1.05 - 0.25 * rr) if abs(dx) > 0.06 and abs(dy) > 0.06 else (60, 50, 36))
    _window(px, REGIONS["window"])
    end_grain(img, REGIONS["end_grain"], _rgb("8a6440"), _rgb("4a3020"), rng)
    fine_wood(img, REGIONS["barrel"], _rgb("7a5636"), _rgb("2e2014"), 4, rng, vertical=True, knots=0.0)
    fine_wood(img, REGIONS["crate"], _rgb("8a6a44"), _rgb("3a2a18"), 8, rng, knots=0.1)
    u, v, w, h = REGIONS["chart"]
    for y in range(h):
        for x in range(w):
            c = _rgb("d8c79a")
            if (x * 7 + y * 3) % 23 == 0 or abs(math.sin(x * 0.3) * 4 + 8 - y) < 0.6:
                c = _rgb("6a5032")
            _put(px, u, v, x, y, _jitter(c, rng, 4))
    # ---- cloth
    _cloth(px, REGIONS["cloth"], _rgb("2c2826"), rng, folds=8.0)
    w, h = REGIONS["banner"][2:]
    _cloth(px, REGIONS["banner"], _rgb("262322"), rng, folds=6.0, alpha_fn=_ragged(w, h, h * 0.45, rng, teeth=6))
    w, h = REGIONS["pennant"][2:]
    _cloth(px, REGIONS["pennant"], _rgb("2a2726"), rng, folds=5.0, alpha_fn=_ragged(w, h, h * 0.5, rng, teeth=2))
    w, h = REGIONS["sail_black"][2:]
    sail_mask = _ragged(w, h, h * 0.8, rng, teeth=5)
    _cloth(px, REGIONS["sail_black"], _rgb("26221f"), rng, folds=12.0, alpha_fn=sail_mask)
    u, v, w, h = REGIONS["sail_black"]
    for k in range(3):   # patches and seams of a worn sail
        x0, y0 = rng.randint(4, w - 14), rng.randint(4, int(h * 0.6))
        for y in range(y0, y0 + rng.randint(6, 10)):
            for x in range(x0, x0 + rng.randint(6, 10)):
                if sail_mask(x, y):
                    c = _rgb("3a332c") if (x in (x0,) or y == y0) else _scale(_rgb("312b27"), 1.0 + 0.04 * (x % 2))
                    _put(px, u, v, x, y, _jitter(c, rng, 3))
    for y in range(0, h, 16):
        for x in range(w):
            if sail_mask(x, y):
                _put(px, u, v, x, y, _rgb("1a1716"))
    _flag(px, REGIONS["flag"], rng)
    _fin(px, REGIONS["fin"], ls.FIN_ROOT_U, rng, holes=True)
    _fin(px, REGIONS["fin_keel"], ls.KEEL_FIN_ROOT_U, rng, holes=False)
    # ---- hull
    fine_wood(img, REGIONS["hull"], _rgb("6a4a30"), _rgb("21160d"), 4, rng, knots=0.2, grain=0.12)
    fine_wood(img, REGIONS["hull_low"], _rgb("54392a"), _rgb("191109"), 4, rng, knots=0.1, grain=0.1)
    fine_wood(img, REGIONS["wale"], _rgb("2a1d14"), _rgb("110b07"), 4, rng, knots=0.0)
    fine_wood(img, REGIONS["rail"], _rgb("4a301e"), _rgb("1e130a"), 4, rng, knots=0.0)
    fine_wood(img, REGIONS["dark_wood"], _rgb("3e2818"), _rgb("1a1009"), 4, rng, knots=0.0)
    fine_wood(img, REGIONS["wood"], _rgb("6e4c30"), _rgb("2e1e12"), 4, rng, knots=0.1)
    fine_wood(img, REGIONS["transom"], _rgb("5e4230"), _rgb("1f140c"), 4, rng, knots=0.1)
    hammered_iron(img, REGIONS["gear_iron"], _rgb("3a3634"), rng)
    _door_leaf(px, REGIONS["door_leaf"], rng)
    u, v, w, h = REGIONS["hatch"]
    for y in range(h):
        for x in range(w):
            c = _rgb("5a3c26") if (x % 4) else _rgb("2a1a10")
            if x < 2 or y < 2 or x > w - 3 or y > h - 3:
                c = _rgb("2c2a28")
            _put(px, u, v, x, y, _jitter(c, rng, 3))
    u, v, w, h = REGIONS["rung"]
    for y in range(h):
        for x in range(w):
            _put(px, u, v, x, y, _jitter(_scale(_rgb("6a4a2e"), 1.0 + 0.08 * math.sin(x * 0.9)), rng, 3))
    _tile_room(img, px, rng)
    img.save(path)
    return img


def make_item_icon(path):
    """16x16 item icon: the turquoise balloon with its wooden band over a dark hull."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((1, 1, 14, 9), fill=(104, 139, 123, 255), outline=(40, 58, 52, 255))
    d.rectangle((4, 3, 11, 7), fill=(106, 68, 41, 255))
    d.line((4, 1, 4, 9), fill=(124, 84, 52, 255))
    d.line((11, 1, 11, 9), fill=(124, 84, 52, 255))
    d.polygon([(14, 4), (15, 1), (15, 7)], fill=(30, 29, 34, 255))
    d.line((7, 9, 7, 11), fill=(60, 50, 40, 255))
    d.polygon([(2, 11), (13, 11), (12, 14), (4, 14)], fill=(85, 58, 38, 255), outline=(33, 22, 13, 255))
    d.point((1, 11), fill=(60, 40, 26, 255))
    d.point((6, 12), fill=(255, 214, 130, 255))
    d.point((9, 12), fill=(255, 214, 130, 255))
    img.save(path)


if __name__ == "__main__":
    make_texture("/tmp/claude-0/agent_leviathan/tex.png")
    make_item_icon("/tmp/claude-0/agent_leviathan/icon.png")
