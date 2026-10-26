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

from galley_texture import _jitter, _rgb, _mix, _scale, _ramp, fine_wood, polished_metal, hammered_iron, woven, twisted_rope, \
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
    "shingle":      (0, 256, 64, 32),    # dark wooden shingles of the galleries' awning (rows along u)
    "glass_round":  (64, 256, 16, 16),   # round porthole of pale glass reflecting the sky (transparent outside)
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
    """Aged turquoise plates in strips along u (the reference's weathered copper-green envelope): each
    strip cut into plates of their own tone (jade, teal, olive, faded), a blue-green seam under each
    strip, butt joints with rivets, pale streaks of wear and rust-brown stains."""
    u, v, w, h = region
    nz = _noise(w, h, 5, rng)
    nz2 = _noise(w, h, 11, rng)
    palette = [base, _mix(base, (62, 104, 90), 0.55), _mix(base, (128, 158, 126), 0.45), _mix(base, (112, 108, 72), 0.5),
               _scale(base, 0.86), _mix(base, (84, 128, 128), 0.5)]
    for r in range(h // strip):
        x = -rng.randint(0, 8)
        while x < w:
            ln = rng.randint(9, 20)
            tone = _jitter(rng.choice(palette), rng, 5)
            for dx in range(ln):
                xx = x + dx
                if xx < 0 or xx >= w:
                    continue
                for b in range(strip):
                    y = r * strip + b
                    if b == strip - 1:
                        c = _scale(seam, 1.0 + 0.08 * nz[y][xx])
                    elif dx == 0:
                        c = _mix(seam, tone, 0.45)
                    else:
                        k = 1.0 + 0.07 * nz[y][xx] + 0.04 * nz2[y][xx] + (0.07 if b == 0 else -0.06 if b == strip - 2 else 0.0)
                        c = _scale(tone, k)
                        t = nz2[y][xx] * 0.5 + 0.5
                        if t > 0.8:
                            c = _mix(c, light, (t - 0.8) * 3.0 * wear * 2)
                        elif t < 0.14:
                            c = _mix(c, (92, 66, 40), (0.14 - t) * 4.0 * wear * 2.5)   # rust-brown stains
                        if dx in (2, ln - 2) and b in (2, strip - 3):
                            c = _scale(seam, 0.8)
                    _put(px, u, v, xx, y, _jitter(c, rng, 3))
            x += ln


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
    _plank_field(px, REGIONS["deck"], _rgb("7c5434"), _rgb("3a2414"), rng, plank_w=4, along_u=True, repairs=0.14, lengths=(14, 32),
                 tone_var=12, nail_p=0.8)
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


def _shingles(px, region, base, rng, row=4, width=(3, 6)):
    """Overlapping wooden shingles in rows along u: each its own tone, a pale lit lower edge, a dark gap
    between neighbours and a shadow under the row above."""
    u, v, w, h = region
    for r in range(h // row):
        x = -rng.randint(0, 3)
        while x < w:
            sw = rng.randint(*width)
            tone = _jitter(_scale(base, rng.uniform(0.85, 1.18)), rng, 6)
            for dx in range(sw):
                xx = x + dx
                if not 0 <= xx < w:
                    continue
                for dy in range(row):
                    c = tone
                    if dx == sw - 1:
                        c = _scale(base, 0.45)
                    elif dy == 0:
                        c = _scale(tone, 0.62)
                    elif dy == row - 1:
                        c = _scale(tone, 1.22)
                    elif (xx * 3 + dy * 5) % 7 == 0:
                        c = _scale(tone, 0.9)
                    _put(px, u, v, xx, r * row + dy, _jitter(c, rng, 3))
            x += sw


def _iron_patches(px, region, rng, n):
    """Repairs: riveted iron plates nailed over the planks."""
    u, v, w, h = region
    for _ in range(n):
        pw, ph = rng.randint(5, 8), rng.randint(4, 6)
        x0, y0 = rng.randint(1, w - pw - 1), rng.randint(1, h - ph - 1)
        for y in range(y0, y0 + ph):
            for x in range(x0, x0 + pw):
                edge = x in (x0, x0 + pw - 1) or y in (y0, y0 + ph - 1)
                c = (54, 52, 50) if not edge else (36, 34, 33)
                if edge and (x + y) % 2 == 0:
                    c = (92, 88, 82)
                _put(px, u, v, x, y, _jitter(c, rng, 3))


def make_texture(path):
    rng = random.Random(9)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    # ---- balloon
    _plates(px, REGIONS["plate"], _rgb("62846c"), _rgb("2e5e66"), _rgb("a4bea6"), rng, strip=8, wear=0.35)
    _plates(px, REGIONS["plate_dark"], _rgb("526e5a"), _rgb("264e54"), _rgb("8aa490"), rng, strip=8, wear=0.45)
    _plank_field(px, REGIONS["wood_panel"], _rgb("7e5232"), _rgb("3a2412"), rng, plank_w=4, along_u=True, repairs=0.18, lengths=(8, 18),
                 tone_var=14, nail_p=0.6)
    _blocks(px, REGIONS["hoop"], _rgb("8a5a36"), _rgb("2e1c10"), rng)
    end_grain(img, REGIONS["hoop_end"], _rgb("8a6440"), _rgb("4a3020"), rng)
    _strap(px, REGIONS["strap"], _rgb("2c2a2a"), rng)
    fine_wood(img, REGIONS["band"], _rgb("5a3a22"), _rgb("26170b"), 8, rng, knots=0.0)
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
    # the reference's hull: weathered mid-brown planks, rather grey, many boards of their own tone (some
    # replaced by paler, greyer or darker ones), dark caulked seams
    weathered = [_rgb("967454"), _rgb("664630"), _rgb("85725c"), _rgb("a07a50")]
    _plank_field(px, REGIONS["hull"], _rgb("845c3e"), _rgb("3a2818"), rng, plank_w=4, along_u=True, repairs=0.16, lengths=(14, 34),
                 tone_var=10, nail_p=0.5, patch_cols=weathered)
    _plank_field(px, REGIONS["hull_low"], _rgb("745034"), _rgb("342216"), rng, plank_w=4, along_u=True, repairs=0.14, lengths=(14, 34),
                 tone_var=9, nail_p=0.4, patch_cols=weathered)
    fine_wood(img, REGIONS["wale"], _rgb("33261c"), _rgb("15100b"), 4, rng, knots=0.0)
    fine_wood(img, REGIONS["rail"], _rgb("583820"), _rgb("22140a"), 4, rng, knots=0.0)
    fine_wood(img, REGIONS["dark_wood"], _rgb("462c18"), _rgb("1c1008"), 4, rng, knots=0.0)
    fine_wood(img, REGIONS["wood"], _rgb("7a5232"), _rgb("2e1c0e"), 4, rng, knots=0.1)
    _plank_field(px, REGIONS["transom"], _rgb("845840"), _rgb("342216"), rng, plank_w=4, along_u=True, repairs=0.15, lengths=(12, 30),
                 patch_cols=weathered)
    _shingles(px, REGIONS["shingle"], _rgb("4a3628"), rng)
    _round(px, REGIONS["glass_round"], lambda rr, dx, dy: (34, 30, 28) if rr > 0.84 else
           _mix((214, 226, 232), (120, 146, 170), min(1.0, max(0.0, 0.5 + 0.6 * (dy + dx * 0.3)))) if abs(dx + dy * 0.6 + 0.25) > 0.12
           else (240, 246, 250))
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


# ================================================================ interior atlas (second texture)
SIZE_IN = 512
# sky_leviathan_interior.png: the rooms and their furniture, 16 px per block like the decoration mods
REGIONS_IN = {
    # room surfaces: walls span the room height (v from the ceiling down to the floor), 2 block tiles
    "in_wall":        (0, 0, 32, 48),     # worn horizontal planks between a beam and a skirting board
    "in_wall_panel":  (32, 0, 32, 48),    # the captain's panelling: dark wainscot, red fabric, gilt rail
    "in_wall_engine": (64, 0, 32, 48),    # planks with riveted iron straps, soot towards the top
    "in_wall_hold":   (96, 0, 32, 48),    # rough planks, patched, darker
    "in_floor":       (128, 0, 32, 32),   # worn plank floor (planks along z)
    "in_floor_hold":  (160, 0, 32, 32),   # rough hold floor
    "in_floor_iron":  (192, 0, 32, 32),   # riveted iron plates of the engine room
    "in_ceil":        (224, 0, 32, 32),   # ceiling planks between dark joists
    "in_ceil_soot":   (256, 0, 32, 32),   # sooty ceiling of the engine room
    "in_rug":         (288, 0, 64, 64),   # big red rug, gold borders, pattern
    "in_runner":      (352, 0, 32, 64),   # red runner of the coursive, gold border, a medallion
    "in_blanket":     (384, 0, 32, 32),   # dark red quilted blanket with a gold hem
    "in_beam":        (416, 0, 32, 16),   # dark oak timber (posts and beams), grain along u
    "in_beam_end":    (448, 0, 16, 16),
    "in_plank":       (464, 0, 32, 16),   # lighter worn plank (furniture, shelves)
    "in_chest":       (416, 16, 32, 16),  # chest planks (grain along u)
    "in_chest_lid":   (448, 16, 32, 16),
    "in_staves":      (480, 16, 32, 16),  # barrel staves (grain along v)
    "in_barrel_lid":  (464, 32, 16, 16),
    "in_iron":        (480, 32, 16, 16),  # blackened iron (bands, brackets, rails)
    "in_rivets":      (496, 32, 16, 16),  # riveted iron plate
    "in_brass":       (0, 48, 16, 16),
    "in_gold":        (16, 48, 16, 16),   # gilded brass bands of the boiler
    "in_copper":      (32, 48, 16, 16),
    "in_boiler":      (0, 64, 64, 64),    # riveted dark iron plates of the boiler, warm sheen
    "in_boiler_band": (64, 64, 64, 16),   # riveted gilded band
    "in_brick":       (64, 80, 32, 16),   # fire bricks
    "in_fire":        (96, 80, 16, 16),   # the firebox glow
    "in_coal":        (112, 80, 16, 16),
    "in_window":      (128, 64, 32, 48),  # leaded window seen from inside (daylight, blue diamonds)
    "in_porthole":    (160, 64, 16, 16),  # round porthole glass from inside
    "in_jars":        (176, 64, 64, 16),  # a row of jars and bottles on a shelf
    "in_jars2":       (176, 80, 64, 16),
    "in_books":       (240, 64, 64, 32),  # two shelves of leather spines
    "in_chart":       (304, 64, 32, 32),  # sea chart
    "in_map_wall":    (336, 64, 48, 32),  # a big map pinned on the wall
    "in_gauge":       (384, 64, 16, 16),
    "in_dial_red":    (400, 64, 16, 16),  # gauge with a red zone
    "in_rope":        (416, 64, 16, 16),
    "in_sack":        (432, 64, 16, 16),
    "in_canvas":      (448, 64, 16, 16),
    "in_bedding":     (464, 64, 16, 16),  # white linen
    "in_red_cloth":   (480, 64, 16, 16),
    "in_glass_green": (496, 64, 16, 16),
    "in_grate":       (304, 96, 32, 32),  # catwalk grating (open holes)
    "in_globe":       (336, 96, 64, 32),  # world map for the globe
    "in_tools":       (400, 96, 48, 16),  # tools hung on a board
    "in_lamp":        (448, 96, 16, 16),  # lantern glass (lit)
    "in_glow":        (464, 96, 16, 16),
    "in_paper":       (480, 96, 16, 16),
    "in_candle":      (496, 96, 16, 16),
    "in_steam":       (0, 128, 32, 32),   # (reserved)
    "in_floor_capt":  (32, 128, 32, 32),  # darker polished planks (captain's quarters)
    "in_wall_chart":  (64, 128, 32, 48),  # chart room walls: panelling with maps
    "in_cushion":     (96, 128, 16, 16),  # red velvet cushion
    "in_leather":     (112, 128, 16, 16),
    "in_slate":       (128, 128, 16, 16),
}


def _wood_px(base, dark, rng, a, b, plank_w, seed_tone, grain_lines, knot=None):
    """One pixel of a plank (a along the grain, b across it, inside a plank of width plank_w)."""
    k = 1.0
    for c0, amp, fr, ph, s in grain_lines:
        yl = c0 + amp * math.sin(a * fr + ph)
        if abs(b + 0.5 - yl) < 0.5:
            k -= 0.09 * s
    if knot is not None:
        d = math.hypot((a + 0.5 - knot[0]) / 1.4, b + 0.5 - knot[1])
        if d < 0.8:
            k -= 0.32
        elif d < 1.5:
            k -= 0.1
    if b == 0:
        k += 0.08
    elif b == plank_w - 2:
        k -= 0.05
    return _scale(seed_tone, k)


def _plank_field(px, region, base, dark, rng, plank_w=4, along_u=True, repairs=0.12, nails=True, wear=None, tone_var=12,
                 seam=None, lengths=(10, 26), patch_cols=None, nail_p=1.0):
    """Worn planks: each board its own tone (some replaced by boards of another colour), butt joints at
    random lengths with two nails each side, a dark caulked seam between the boards, the grain, knots, and
    an optional wear function (x, y) -> lightening factor (paths worn pale)."""
    u, v, w, h = region
    L, W = (w, h) if along_u else (h, w)
    seam = seam or dark
    patch_cols = patch_cols or [_scale(base, 1.22), _scale(base, 0.78), _mix(base, (128, 112, 92), 0.35)]
    rows = -(-W // plank_w)
    for r in range(rows):
        a = 0
        while a < L:
            ln = rng.randint(*lengths)
            tone = _jitter(base, rng, tone_var)
            if rng.random() < repairs:
                tone = _jitter(rng.choice(patch_cols), rng, 5)
            lines = [(rng.uniform(0.6, plank_w - 1.2), rng.uniform(0.2, 0.7), rng.uniform(0.1, 0.35), rng.uniform(0, 6.3), rng.uniform(0.5, 1.0))
                     for _ in range(2)]
            knot = (rng.uniform(2, max(3, ln - 2)), rng.uniform(1, plank_w - 1.5)) if rng.random() < 0.2 else None
            nailed = nails and rng.random() < nail_p
            for da in range(ln):
                aa = a + da
                if aa >= L:
                    break
                for b in range(plank_w):
                    bb = r * plank_w + b
                    if bb >= W:
                        break
                    if b == plank_w - 1:
                        c = seam
                    elif da == 0:
                        c = _mix(seam, tone, 0.3)
                    else:
                        c = _wood_px(base, dark, rng, da, b, plank_w, tone, lines, knot)
                        if nailed and (da in (1, ln - 2)) and b == plank_w // 2 - 1:
                            c = (46, 40, 36)
                    x, y = (aa, bb) if along_u else (bb, aa)
                    if wear is not None and b != plank_w - 1:
                        c = _mix(c, _scale(c, 1.25), wear(x, y))
                    _put(px, u, v, x, y, _jitter(c, rng, 2))
            a += ln


def _rivet_plate(px, region, base, rng, pw=16, ph=16, seam=None, rivet=(90, 84, 78), soot=0.0, sheen=None):
    u, v, w, h = region
    seam = seam or _scale(base, 0.55)
    nz = _noise(w, h, 6, rng)
    for y in range(h):
        for x in range(w):
            k = 1.0 + 0.08 * nz[y][x]
            if sheen:
                k += sheen * math.sin(x / w * math.pi * 2 + 0.6)
            c = _scale(base, k)
            if x % pw == 0 or y % ph == 0:
                c = seam
            elif x % pw == pw - 1 or y % ph == ph - 1:
                c = _scale(base, 1.12 * k)
            elif (x % pw in (2, pw - 3) and y % 3 == 1) or (y % ph in (2, ph - 3) and x % 3 == 1):
                c = rivet if (x + y) % 2 else _scale(rivet, 0.8)
            if soot:
                c = _mix(c, (20, 18, 16), soot * (1 - y / h) * (0.6 + 0.4 * nz[y][x]))
            _put(px, u, v, x, y, _jitter(c, rng, 2))


def _rug_big(px, region, rng, field="7a1814", border="a87a34", dark="3a0e0b", accent="561410"):
    """A big red rug: a dark edge, a thin gold border, a band of small gold motifs, the deep red field with
    a faint lozenge medallion and corner flowers."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            fld = _scale(_rgb(field), 1.0 + 0.05 * math.sin(x * 0.7) * math.sin(y * 0.9))
            if e < 1:
                c = _rgb(dark)
            elif e < 2:
                c = _rgb(border)
            elif e < 6:
                c = _rgb(accent)
                if e in (3, 4) and (x + y) % 4 == 0:
                    c = _mix(_rgb(border), _rgb(accent), 0.25)
            elif e < 7:
                c = _rgb(border)
            else:
                c = fld
                dx, dy = (x - w / 2 + 0.5) / (w / 2 - 7), (y - h / 2 + 0.5) / (h / 2 - 7)
                d = abs(dx) + abs(dy)
                if abs(d - 0.45) < 0.035:
                    c = _mix(_rgb(border), fld, 0.35)
                elif d < 0.16:
                    c = _mix(_rgb(border), fld, 0.4)
                elif d < 0.45 and (x + y) % 5 == 0:
                    c = _mix(fld, _rgb(accent), 0.6)
                for cx, cy in ((11, 11), (w - 12, 11), (11, h - 12), (w - 12, h - 12)):
                    if abs(x - cx) + abs(y - cy) < 2:
                        c = _mix(_rgb(border), fld, 0.3)
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _runner(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            e = min(x, w - 1 - x)
            if e < 1:
                c = _rgb("3e0f0c")
            elif e < 3:
                c = _rgb("c9973a") if (y % 4) else _rgb("9a6e28")
            elif e < 4:
                c = _rgb("3e0f0c")
            else:
                c = _scale(_rgb("8a1d18"), 1.0 + 0.05 * math.sin(y * 0.8))
                if (y % 12) in (0, 1) and abs(x - w / 2 + 0.5) < 6:
                    c = _rgb("6a1410")
                dx, dy = abs(x - w / 2 + 0.5), abs(y - h / 2 + 0.5)
                if dx / 7 + dy / 9 < 1.0 and dx / 7 + dy / 9 > 0.75:
                    c = _rgb("c9973a")
                if dx + dy < 2.5:
                    c = _rgb("c9973a")
            _put(px, u, v, x, y, _jitter(c, rng, 4))


def _jars(px, region, rng, seed_cols):
    """A shelf board with jars, bottles and crocks in front of a dark wall."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _rgb("1e140c") if y < h - 3 else (_rgb("6a4a2c") if y == h - 3 else _rgb("4a301c"))
            _put(px, u, v, x, y, _jitter(c, rng, 3))
    x = 1
    while x < w - 3:
        kind = rng.random()
        col = _rgb(rng.choice(seed_cols))
        if kind < 0.35:      # bottle: narrow neck
            bw, top = 3, rng.randint(1, 4)
            for xx in range(x, x + bw):
                for y in range(top + 4, h - 3):
                    _put(px, u, v, xx, y, _scale(col, 1.25 if xx == x else 0.9))
            for y in range(top, top + 4):
                _put(px, u, v, x + 1, y, _scale(col, 0.8))
            _put(px, u, v, x + 1, top, (70, 50, 30))
        elif kind < 0.7:     # jar with a lid
            bw, top = rng.randint(4, 5), rng.randint(5, 8)
            for xx in range(x, x + bw):
                for y in range(top, h - 3):
                    c = _scale(col, 1.2 if xx == x + 1 else 0.85 if xx == x + bw - 1 else 1.0)
                    if y == top:
                        c = (150, 130, 100)
                    _put(px, u, v, xx, y, c)
        else:                # crock
            bw, top = rng.randint(4, 6), rng.randint(6, 9)
            col = _rgb(rng.choice(["8a6a4a", "a08060", "6a5040", "b09a78"]))
            for xx in range(x, x + bw):
                for y in range(top, h - 3):
                    c = _scale(col, 1.15 if xx == x + 1 else 0.85 if xx == x + bw - 1 else 1.0)
                    if y == top + 2:
                        c = _scale(col, 0.7)
                    _put(px, u, v, xx, y, c)
        x += bw + rng.randint(0, 2)


def make_interior_texture(path):
    rng = random.Random(77)
    img = Image.new("RGBA", (SIZE_IN, SIZE_IN), (0, 0, 0, 0))
    px = img.load()
    R = REGIONS_IN
    oak, oak_dark = _rgb("7c4c26"), _rgb("3a2010")

    # ---- walls: horizontal planks, a joist band at the top, a skirting board at the bottom
    def wall(region, base, dark, top=None, bottom=None, repairs=0.14, straps=False, soot=0.0, panel=False):
        u, v, w, h = region
        _plank_field(px, region, base, dark, rng, plank_w=4, along_u=True, repairs=repairs, lengths=(20, 44), nail_p=0.35)
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[u + x, v + y]
                c = (r, g, b)
                if y < 4:   # the beam under the ceiling
                    c = _scale(_rgb("3a2414"), 1.0 + (0.12 if y == 0 else -0.1 if y == 3 else 0.0) + 0.04 * math.sin(x * 0.7))
                elif y >= h - 4:   # skirting board
                    c = _scale(_rgb("3a2414"), 1.0 + (0.1 if y == h - 4 else 0.0))
                if panel:
                    if 4 <= y < 7:
                        c = _scale(_rgb("6b1a16"), 1.0 + 0.05 * ((x + y) % 2))
                    elif y == 7:
                        c = _rgb("b88a3a")
                    elif y >= h - 18 and y < h - 4:   # wainscot panels
                        px_ = x % 16
                        c = _scale(_rgb("4a2c18"), 1.0 + (0.12 if px_ in (1, 2) or y == h - 18 else -0.15 if px_ in (14, 15) or y == h - 5 else 0.0))
                    elif y == h - 19:
                        c = _rgb("b88a3a")
                if straps and x in (14, 15, 16, 17) and 4 <= y < h - 4:
                    c = _rgb("2a2826") if x in (15, 16) else _rgb("3a3633")
                    if y % 6 == 2 and x in (15, 16):
                        c = (110, 100, 88)
                if soot:
                    c = _mix(c, (24, 20, 16), soot * max(0.0, 1 - y / (h * 0.55)))
                _put(px, u, v, x, y, c)
    wall(R["in_wall"], oak, oak_dark)
    wall(R["in_wall_panel"], _rgb("70421f"), oak_dark, panel=True, repairs=0.05)
    wall(R["in_wall_engine"], _rgb("704626"), oak_dark, straps=True, soot=0.35)
    wall(R["in_wall_hold"], _rgb("724a28"), oak_dark, repairs=0.25)
    wall(R["in_wall_chart"], _rgb("70421f"), oak_dark, panel=True, repairs=0.05)

    # ---- floors (planks along u = z), worn paler along the middle
    def worn(w):
        return lambda x, y: 0.35 * max(0.0, 1 - abs(y - 16) / 10.0) * (0.6 + 0.4 * math.sin(x * 0.3))
    _plank_field(px, R["in_floor"], _rgb("64401f"), _rgb("3a2210"), rng, plank_w=4, along_u=True, repairs=0.15, lengths=(14, 30), nail_p=0.5)
    _plank_field(px, R["in_floor_hold"], _rgb("5e3c20"), _rgb("341e0e"), rng, plank_w=4, along_u=True, repairs=0.25, lengths=(10, 24),
                 nail_p=0.5)
    _plank_field(px, R["in_floor_capt"], _rgb("583418"), _rgb("2e1a0a"), rng, plank_w=4, along_u=True, repairs=0.04, lengths=(18, 34),
                 nail_p=0.3)
    _rivet_plate(px, R["in_floor_iron"], _rgb("4a4440"), rng, pw=16, ph=16, sheen=0.05)
    # ---- ceilings: planks along u with a dark joist every block
    for name, base, soot in (("in_ceil", _rgb("4e301a"), 0.0), ("in_ceil_soot", _rgb("46301c"), 0.35)):
        u, v, w, h = R[name]
        _plank_field(px, R[name], base, oak_dark, rng, plank_w=4, along_u=True, repairs=0.1, lengths=(12, 30))
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[u + x, v + y]
                c = (r, g, b)
                if x % 16 in (0, 1, 2, 3):
                    c = _scale(_rgb("2e1c0e"), 1.0 + (0.12 if x % 16 == 0 else -0.1 if x % 16 == 3 else 0.0))
                if soot:
                    c = _mix(c, (22, 18, 15), soot * (0.5 + 0.5 * math.sin(x * 0.2 + y * 0.13)))
                _put(px, u, v, x, y, _jitter(c, rng, 2))

    # ---- textiles
    _rug_big(px, R["in_rug"], rng)
    _runner(px, R["in_runner"], rng)
    u, v, w, h = R["in_blanket"]
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("7a1612"), 1.0 + 0.1 * math.sin(x * 0.9) * math.sin(y * 0.9) - (0.12 if (x % 8 == 0 or y % 8 == 0) else 0.0))
            if y < 2 or y > h - 3 or x < 2 or x > w - 3:
                c = _rgb("b8893a")
            _put(px, u, v, x, y, _jitter(c, rng, 3))
    for name, col, fold in (("in_red_cloth", "7a1a16", 0.06), ("in_cushion", "8e1e18", 0.1), ("in_bedding", "e6dccb", 0.04),
                            ("in_canvas", "b8a27a", 0.05), ("in_sack", "a08458", 0.08), ("in_leather", "5a3420", 0.05),
                            ("in_paper", "e0cfa0", 0.03), ("in_candle", "efe2c0", 0.02), ("in_slate", "3a3a3e", 0.04)):
        u, v, w, h = R[name]
        for y in range(h):
            for x in range(w):
                k = 1.0 + fold * math.sin(x * 0.8 + y * 0.4) + (0.04 if (x + y) % 2 else -0.02)
                if name == "in_sack" and (x + 2 * y) % 5 == 0:
                    k -= 0.12
                _put(px, u, v, x, y, _jitter(_scale(_rgb(col), k), rng, 3))

    # ---- wood for the furniture
    fine_wood(img, R["in_beam"], _rgb("553218"), _rgb("2a170a"), 16, rng, joints=False, knots=0.4, grain=0.14)
    end_grain(img, R["in_beam_end"], _rgb("6a4628"), _rgb("2e1c10"), rng)
    fine_wood(img, R["in_plank"], _rgb("8a5a32"), _rgb("3a2210"), 4, rng, knots=0.15)
    fine_wood(img, R["in_chest"], _rgb("74482a"), _rgb("2e180a"), 4, rng, knots=0.1)
    fine_wood(img, R["in_chest_lid"], _rgb("603a1e"), _rgb("28160a"), 4, rng, knots=0.1)
    fine_wood(img, R["in_staves"], _rgb("845630"), _rgb("3a2210"), 4, rng, vertical=True, knots=0.0)
    end_grain(img, R["in_barrel_lid"], _rgb("7a5432"), _rgb("3a2414"), rng)
    hammered_iron(img, R["in_iron"], _rgb("2c2a28"), rng)
    _rivet_plate(px, R["in_rivets"], _rgb("3a3634"), rng, pw=8, ph=8)
    polished_metal(img, R["in_brass"], [(0.0, (88, 60, 22)), (0.5, (168, 124, 50)), (1.0, (230, 192, 104))], rng)
    polished_metal(img, R["in_gold"], GOLD_STOPS, rng)
    polished_metal(img, R["in_copper"], [(0.0, (86, 40, 20)), (0.5, (164, 90, 48)), (1.0, (222, 146, 96))], rng)

    # ---- the boiler: riveted plates with a warm sheen, gilded riveted bands, fire bricks, the glow
    _rivet_plate(px, R["in_boiler"], _rgb("3c3430"), rng, pw=16, ph=16, rivet=(150, 116, 62), sheen=0.08)
    u, v, w, h = R["in_boiler_band"]
    for y in range(h):
        for x in range(w):
            t = 0.5 + 0.5 * math.sin(x * 0.25) * 0.4 + (0.3 if y < 4 else -0.25 if y > h - 5 else 0.0)
            c = _ramp(GOLD_STOPS, max(0.0, min(1.0, t)))
            if y in (0, h - 1):
                c = (70, 48, 18)
            if x % 6 == 3 and y in (h // 2 - 1, h // 2):
                c = (90, 64, 26)
            _put(px, u, v, x, y, _jitter(c, rng, 3))
    u, v, w, h = R["in_brick"]
    for y in range(h):
        for x in range(w):
            row = y // 4
            off = 4 if row % 2 else 0
            c = _jitter(_rgb("8a3a24"), rng, 10)
            if y % 4 == 3 or (x + off) % 8 == 7:
                c = _rgb("3a2a22")
            _put(px, u, v, x, y, c)
    u, v, w, h = R["in_fire"]
    for y in range(h):
        for x in range(w):
            t = y / h
            c = _mix((255, 240, 150), (230, 90, 20), 1 - t + 0.25 * math.sin(x * 1.4 + y * 0.6))
            _put(px, u, v, x, y, _jitter(c, rng, 8))
    u, v, w, h = R["in_coal"]
    for y in range(h):
        for x in range(w):
            k = 1.0 + 0.4 * math.sin(x * 2.1 + y * 1.3) * math.sin(y * 1.7)
            _put(px, u, v, x, y, _jitter(_scale((40, 36, 34), k), rng, 6))

    # ---- windows from inside: wooden frame, leaded diamond panes of a blue sky
    u, v, w, h = R["in_window"]
    for y in range(h):
        for x in range(w):
            if x < 3 or x >= w - 3 or y < 3 or y >= h - 3:
                c = _scale(_rgb("4a2e18"), 1.0 + (0.12 if x == 0 or y == 0 else 0.0))
            elif (x + y) % 7 == 0 or (x - y) % 7 == 0:
                c = _rgb("3a3430")
            elif abs(x - w / 2 + 0.5) < 1.0:
                c = _rgb("4a2e18")
            else:
                t = y / h
                c = _mix(_rgb("8eaac4"), _rgb("4e6a8e"), t)
                if (x * 3 + y) % 11 == 0:
                    c = _scale(c, 1.12)
            _put(px, u, v, x, y, _jitter(c, rng, 3))
    _round(px, R["in_porthole"], lambda rr, dx, dy: (60, 44, 24) if rr > 0.86 else _mix(_rgb("c4dcec"), _rgb("6a8cb4"), (dy + 1) / 2)
           if abs(dx) > 0.07 else (70, 60, 50))
    _jars(px, R["in_jars"], rng, ["2e6a3a", "7a2a1e", "3a5a7a", "a07a2a", "4a7a5a", "8a5a2a", "5a3a6a"])
    _jars(px, R["in_jars2"], rng, ["2e5a2e", "6a4a1e", "8a2a1e", "2a4a6a", "b08a3a", "4a6a2a"])
    # books
    u, v, w, h = R["in_books"]
    cols = ["7a1f1c", "1f3a5a", "2f5a2a", "6a4a20", "3a2a4a", "8a6a2a", "5a1a1a", "2a4a4a", "9a7a4a"]
    for y in range(h):
        for x in range(w):
            _put(px, u, v, x, y, _rgb("1a100a"))
    for row in range(2):
        x = 1
        y0, y1 = row * 16 + 1, row * 16 + 14
        while x < w - 2:
            bw = rng.choice((2, 2, 3, 3, 4))
            top = y0 + rng.randint(1, 4)
            col = _rgb(rng.choice(cols))
            lean = rng.random() < 0.08
            for xx in range(x, min(w - 1, x + bw)):
                for y in range(top + (1 if lean and xx > x else 0), y1):
                    c = _scale(col, 1.18 if xx == x else 0.82 if xx == x + bw - 1 else 1.0)
                    if y in (top + 2, y1 - 3) and bw > 2:
                        c = _rgb("c8a24a")
                    _put(px, u, v, xx, y, _jitter(c, rng, 3))
            x += bw
        for y in (y1, y1 + 1):
            for x in range(w):
                _put(px, u, v, x, y, _jitter(_rgb("5a3a20"), rng, 3))
    # sea chart and the wall map
    for name in ("in_chart", "in_map_wall"):
        u, v, w, h = R[name]
        cx, cy = w * 0.64, h * 0.56
        for y in range(h):
            for x in range(w):
                c = _jitter(_rgb("c8ae7a"), rng, 6)
                land = y < h * 0.3 + 4 * math.sin(x / 4.0) and x < w * 0.55 or (x - w * 0.2) ** 2 + (y - h * 0.8) ** 2 < (h * 0.12) ** 2
                if land:
                    c = _jitter(_rgb("a88a58"), rng, 6)
                coast = abs(y - (h * 0.3 + 4 * math.sin(x / 4.0))) < 0.7 and x < w * 0.55
                if coast:
                    c = _rgb("6b4a2a")
                ang = math.atan2(y - cy, x - cx)
                if abs(math.sin(4 * ang)) < 0.05 and not land:
                    c = _rgb("a88a5c")
                if (x - cx) ** 2 + (y - cy) ** 2 < 5:
                    c = _rgb("8b1e1e")
                if abs(x - 0.45 * w - 0.3 * (y - h * 0.5)) < 0.5 and h * 0.4 < y < h * 0.75:
                    c = _rgb("8b1e1e")   # a route in red
                e = min(x, y, w - 1 - x, h - 1 - y)
                if e == 0:
                    c = _rgb("9a7a48")
                _put(px, u, v, x, y, c)
    _round(px, R["in_gauge"], lambda rr, dx, dy: (40, 30, 18) if rr > 0.85 else (34, 28, 24) if abs(dx + dy * 0.6) < 0.09 and dy < 0.2 and dx < 0.3
           else (236, 226, 198) if rr < 0.8 or (int((math.atan2(dy, dx) + 4) * 5) % 2) else (60, 50, 40))
    _round(px, R["in_dial_red"], lambda rr, dx, dy: (40, 30, 18) if rr > 0.85 else (34, 28, 24) if abs(dx - dy * 0.5) < 0.09 and dy < 0.2
           else (176, 40, 30) if (rr > 0.55 and dx > 0.2 and dy < 0) else (236, 226, 198))
    twisted_rope(img, R["in_rope"], _rgb("b4945e"), _rgb("6e5432"), rng)
    u, v, w, h = R["in_glass_green"]
    for y in range(h):
        for x in range(w):
            _put(px, u, v, x, y, _jitter(_scale(_rgb("2e5a32"), 1.0 + 0.25 * math.sin(x * 0.6)), rng, 4))
    # grating: an iron lattice with open holes (cutout)
    u, v, w, h = R["in_grate"]
    for y in range(h):
        for x in range(w):
            if x % 4 == 0 or y % 8 == 0:
                c = _scale(_rgb("3a3634"), 1.0 + (0.15 if y % 8 == 0 else 0.0))
                _put(px, u, v, x, y, _jitter(c, rng, 3))
            else:
                _put(px, u, v, x, y, (0, 0, 0), 0)
    # globe map: ocean with continents
    u, v, w, h = R["in_globe"]
    cont = [(rng.uniform(0, w), rng.uniform(h * 0.2, h * 0.8), rng.uniform(3, 8)) for _ in range(9)]
    for y in range(h):
        for x in range(w):
            land = any(((x - cx) / r) ** 2 + ((y - cy) / (r * 0.7)) ** 2 < 1 for cx, cy, r in cont)
            c = _rgb("c8b07a") if land else _rgb("5a7a8a")
            if y % 8 == 0 or x % 8 == 0:
                c = _scale(c, 0.85)
            _put(px, u, v, x, y, _jitter(c, rng, 4))
    # tools on a board
    u, v, w, h = R["in_tools"]
    for y in range(h):
        for x in range(w):
            _put(px, u, v, x, y, _jitter(_rgb("5a3a22"), rng, 4))
    for k in range(7):
        x0 = 3 + k * 6
        for y in range(2, h - 2):
            c = _rgb("6a6866") if k % 2 else _rgb("4a3020")
            if y < 6 and k % 3 == 0:
                c = _rgb("8a8884")
            _put(px, u, v, x0, y, c)
            if k % 2 == 0 and y < 5:
                _put(px, u, v, x0 + 1, y, _rgb("8a8884"))
    paint_lamp_glass(px, *R["in_lamp"])
    u, v, w, h = R["in_glow"]
    for y in range(h):
        for x in range(w):
            _put(px, u, v, x, y, _jitter((255, 210, 120), rng, 6))
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
