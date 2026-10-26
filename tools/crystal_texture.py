"""Textures of the Crystal Airship (crystal_airship).

  crystal_airship.png            512x512 atlas of the outside, regions in REGIONS (u, v, w, h)
  crystal_airship_interior.png   512x512 atlas of the rooms: the Sky Leviathan's room atlas (tools/leviathan_texture.py,
                                 REGIONS_IN: panelling, floors, rugs, books, jars, metals...) with the rooms of this
                                 airship added below it (REGIONS_IN_EXTRA: stone and timber walls of the cockpit, the
                                 lounge's carved panelling, the engine room's riveted walls and floor grates...)
  item/crystal_airship.png       16x16 item icon

Colours of the reference sheet: cream and white balloon lobes of small knobbly squares (the "voxel" look), gilded
brass straps with blue jewels, a warm brown upper hull with gold mouldings and many lit windows, a dark olive
green lower hull, a green roof, bronze and brass engines with copper pipes, glowing blue crystals, red pennants.
"""
import math
import random

from PIL import Image, ImageDraw

from galley_texture import _jitter, _rgb, _mix, _scale, _ramp, fine_wood, polished_metal, hammered_iron, woven, twisted_rope, \
    end_grain, paint_lamp_glass, GOLD_STOPS
import leviathan_texture as lt

SIZE = 512

REGIONS = {
    # balloon
    "cloth":        (0, 0, 64, 64),     # cream quilted squares (the lobes)
    "cloth_dark":   (64, 0, 64, 64),    # the same in the shade (undersides)
    "strap":        (128, 0, 32, 16),   # gilded strap along u
    "girdle":       (128, 16, 32, 16),  # gilded girdle with a twisted edge
    # metals and small parts
    "gold":         (160, 0, 16, 16),
    "brass":        (176, 0, 16, 16),
    "bronze":       (192, 0, 16, 16),
    "copper":       (208, 0, 16, 16),
    "iron":         (224, 0, 16, 16),
    "steel":        (240, 0, 16, 16),
    "chain":        (160, 16, 16, 16),
    "rope":         (176, 16, 16, 16),
    "rope_dark":    (192, 16, 16, 16),
    "glow":         (208, 16, 16, 16),
    "lantern":      (224, 16, 16, 16),
    "glass":        (240, 16, 16, 16),
    "gem":          (256, 0, 16, 16),   # blue jewel in a gold setting (lit)
    "crystal":      (272, 0, 16, 32),   # glowing blue crystal facets (along v)
    "crystal_core": (288, 0, 32, 32),   # round glowing core with rays (transparent outside the circle)
    "gauge":        (320, 0, 16, 16),
    "coral_red":    (336, 0, 16, 16),
    "red_velvet":   (352, 0, 16, 16),
    "dark_wood":    (368, 0, 32, 16),
    "wood":         (400, 0, 32, 16),
    "rail":         (432, 0, 32, 16),
    "gear_iron":    (464, 0, 16, 16),
    "end_grain":    (480, 0, 16, 16),
    "rung":         (496, 0, 16, 16),
    "engine_plate": (256, 32, 32, 32),  # riveted bronze plates
    "engine_dark":  (288, 32, 32, 32),  # riveted dark iron
    "feather":      (320, 32, 32, 16),  # overlapping brass feathers (along u)
    "hull_band":    (320, 48, 32, 16),  # dark brown wale
    "blade":        (352, 16, 16, 32),  # golden propeller blade (leaf, transparent outside)
    "porthole":     (368, 16, 16, 16),  # round lit porthole (transparent outside the circle)
    "pennant_rope": (384, 16, 16, 16),
    # hull
    "hull_brown":   (0, 64, 64, 32),    # warm brown planks along u
    "hull_green":   (0, 96, 64, 32),    # dark olive green planks along u
    "trim_gold":    (64, 64, 32, 16),   # gilded moulding (beads) along u
    "trim_dark":    (64, 80, 32, 16),   # dark moulding with a gilded bead
    "scroll":       (64, 96, 32, 32),   # gilded scroll ornament (transparent outside)
    "deck":         (96, 64, 32, 32),   # deck planks along u
    "roof_green":   (128, 64, 32, 32),  # green roof boards (along v), a gilded eave
    "window_frame": (160, 64, 32, 32),  # big window: dark frame, mullions, open panes (seen through)
    "window_lit":   (192, 64, 16, 32),  # small arched window lit from inside
    "window_rose":  (208, 64, 48, 48),  # the fan window of the bow (a half disc of rays), lit
    "flag":         (256, 64, 64, 32),  # red pennant, the fly cut in steps (transparent)
    "door_leaf":    (320, 64, 32, 64),
    "hatch":        (352, 64, 32, 32),
    "panel_green":  (384, 64, 32, 32),  # green panel in a gilded frame
    "cornice":      (416, 64, 32, 16),  # dark cornice with gilded beads
    "window_arch":  (416, 80, 32, 32),  # the cockpit's arched window seen from outside: frame, open panes
    "wall_wood":    (448, 64, 32, 32),  # castle walls: vertical boards between gilded pilasters
    "turret":       (480, 64, 32, 32),  # the turret's dark planks with iron bands
    # second pass (the stern, the engines, the gallery, the bow's fan window)
    "window_gallery": (0, 128, 16, 32),  # tall arched gallery window: gilded frame, amber lit quarries and clear ones (lit)
    "window_fan":   (16, 128, 64, 32),  # the bow's quarter fan window in polar layout: u = angle, v = radius (lit)
    "brass_olive":  (80, 128, 16, 16),  # warm brass with an olive patina (the engines)
    "engine_brass": (96, 128, 32, 32),  # riveted warm brass plates (the engines' helmet and drum)
    "petal":        (128, 128, 16, 32), # green-bronze petal plate of the turbine cowl (pointed, transparent outside)
    "louver":       (144, 128, 32, 16), # louvered grille slat: dark gap, brass lip
    "coaming":      (176, 128, 64, 16), # green panel of the roof deck's coaming with a gilded scroll, gilded frame
    "stern_panel":  (240, 128, 32, 32), # carved green panel in a gilded frame with a rosette (the castle's back)
    "cap_iron":     (272, 128, 32, 32), # dark ribbed iron (the engines' tail caps): ribs along v, rivets
    "medal_glass":  (304, 128, 32, 32), # the medallion's porthole: blue-grey glass, a glowing blue heart (lit)
    "ring_bronze":  (336, 128, 32, 16), # the great ring: smooth tan bronze along u, a polished highlight
    "fairy":        (368, 128, 16, 16), # warm glowing bead (the fairy lights under the swags)
    "plate_brass":  (384, 128, 16, 16), # one riveted plate of warm brass with an olive patina (drawn whole on a panel)
    "plate_bronze": (400, 128, 16, 16), # the same in dark bronze (the engines' undersides and tapers)
    "plate_helmet": (416, 128, 16, 16), # the same, bright polished brass (the engines' helmets)
}


def _put(px, u, v, x, y, c, a=255):
    px[u + x, v + y] = tuple(int(max(0, min(255, q))) for q in c[:3]) + (a,)


def _noise(w, h, cells, rng):
    return lt._noise(w, h, cells, rng)


BRASS_STOPS = [(0.0, (92, 66, 26)), (0.3, (150, 112, 46)), (0.6, (196, 156, 74)), (0.85, (226, 196, 120)), (1.0, (246, 228, 168))]
BRONZE_STOPS = [(0.0, (70, 46, 24)), (0.3, (120, 80, 40)), (0.6, (164, 116, 58)), (0.85, (200, 154, 88)), (1.0, (226, 190, 130))]
COPPER_STOPS = [(0.0, (90, 40, 22)), (0.35, (150, 70, 38)), (0.65, (196, 108, 62)), (0.9, (228, 156, 104)), (1.0, (246, 196, 150))]
STEEL_STOPS = [(0.0, (70, 72, 76)), (0.4, (120, 122, 126)), (0.75, (168, 170, 172)), (1.0, (214, 216, 216))]


def _quilt(px, region, rng, dark=False):
    """The lobes' skin: warm cream and ivory, knobbly: small raised squares (1-2 px knobs) catching the light here and
    there over a soft mottle, faint seams (no regular grid)."""
    u, v, w, h = region
    tones = [(236, 228, 206), (246, 240, 224), (252, 248, 238), (226, 214, 190), (240, 232, 212), (232, 222, 200)]
    if dark:
        tones = [_mix(_scale(t, 0.8), (178, 160, 130), 0.12) for t in tones]
    nz = _noise(w, h, 4, rng)
    nz2 = _noise(w, h, 9, rng)
    base = [[None] * w for _ in range(h)]
    t = 4
    for ty in range(h // t):
        for tx in range(w // t):
            tone = _jitter(rng.choice(tones), rng, 3)
            for y in range(t):
                for x in range(t):
                    base[ty * t + y][tx * t + x] = tone
    for y in range(h):
        for x in range(w):
            k = 1.0 + 0.045 * nz[y][x] + 0.03 * nz2[y][x]
            if x % 4 == 3 or y % 4 == 3:
                k -= 0.06
            elif x % 4 == 0 or y % 4 == 0:
                k += 0.03
            _put(px, u, v, x, y, _jitter(_scale(base[y][x], k), rng, 2))
    # knobs: small raised cubes, lit on top and shaded below
    for _ in range(w * h // 22):
        x, y = rng.randrange(w - 2), rng.randrange(1, h - 2)
        size = rng.choice((1, 1, 2))
        c = _scale(rng.choice(tones), 1.07 if not dark else 0.95)
        for yy in range(size):
            for xx in range(size):
                _put(px, u, v, x + xx, y + yy, c)
        for xx in range(size):
            cc = px[u + x + xx, v + y + size][:3]
            _put(px, u, v, x + xx, y + size, _scale(cc, 0.9))
    for _ in range(w * h // 40):
        x, y = rng.randrange(w), rng.randrange(h)
        cc = px[u + x, v + y][:3]
        _put(px, u, v, x, y, _scale(cc, 0.93))


def _strap(px, region, rng, chain=False):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            t = 0.5 + 0.45 * math.cos((y + 0.5 - h / 2) / (h / 2) * math.pi / 1.4)
            if y in (0, h - 1):
                t = 0.08
            c = _ramp(GOLD_STOPS, t)
            if chain and (y < 3 or y > h - 4) and (x + (y < 3) * 2) % 4 == 0:
                c = _scale(c, 0.7)
            if not chain and x % 8 == 4 and abs(y - h / 2 + 0.5) < 1.6:
                c = _ramp(GOLD_STOPS, 0.98)
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _gem(px, region):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            dx, dy = (x + 0.5) / w * 2 - 1, (y + 0.5) / h * 2 - 1
            r = math.hypot(dx, dy)
            if r > 0.86 or max(abs(dx), abs(dy)) > 0.9:
                c = _ramp(GOLD_STOPS, 0.55 + 0.3 * dy)
            elif r > 0.7:
                c = _ramp(GOLD_STOPS, 0.85 - 0.3 * dy)
            else:
                g = r / 0.7
                c = _mix((235, 252, 255), (40, 120, 230), min(1.0, g * 1.2))
                if (dx + 0.25) ** 2 + (dy + 0.3) ** 2 < 0.04:
                    c = (255, 255, 255)
            _put(px, u, v, x, y, c)


def _crystal(px, region, rng):
    """Glowing crystal: facets along v (alternating bright and deep blue), white sparks."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            facet = (x * 3 // w)
            k = (0.95, 0.7, 0.85)[facet]
            t = 0.5 + 0.5 * math.sin((x * 0.9 + y * 0.35))
            c = _mix((30, 110, 230), (150, 230, 255), 0.35 + 0.45 * t)
            c = _scale(c, k + 0.15 * (1 - abs(y - h / 2) / (h / 2)))
            if (x * 7 + y * 13) % 29 == 0:
                c = (240, 252, 255)
            _put(px, u, v, x, y, _jitter(c, rng, 4))


def _core(px, region):
    """The crystal eye of the engines: a white-hot centre, blue rays, a deep blue ring (lit)."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            dx, dy = (x + 0.5) / w * 2 - 1, (y + 0.5) / h * 2 - 1
            r = math.hypot(dx, dy)
            if r > 1.0:
                _put(px, u, v, x, y, (0, 0, 0), 0)
                continue
            a = math.atan2(dy, dx)
            ray = 0.5 + 0.5 * math.cos(a * 12)
            if r < 0.22:
                c = (240, 252, 255)
            elif r < 0.85:
                c = _mix((120, 220, 255), (24, 90, 220), (r - 0.22) / 0.63)
                c = _mix(c, (200, 245, 255), 0.45 * ray * (1 - r))
            else:
                c = (16, 50, 140)
            _put(px, u, v, x, y, c)


def _rivets(px, region, stops, rng, pw=16, ph=16, dark=False):
    u, v, w, h = region
    nz = _noise(w, h, 5, rng)
    for y in range(h):
        for x in range(w):
            t = 0.55 + 0.25 * nz[y][x] + 0.15 * math.sin(x * 0.4 + y * 0.2)
            c = _ramp(stops, t)
            if x % pw == 0 or y % ph == 0:
                c = _scale(c, 0.55)
            elif (x % pw in (2, pw - 2)) and (y % 5 == 2):
                c = _scale(_ramp(stops, 0.95), 1.0)
            elif (y % ph in (2, ph - 2)) and (x % 5 == 2):
                c = _scale(_ramp(stops, 0.95), 1.0)
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _feather(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            f = x % 8
            t = 0.35 + 0.08 * f + 0.15 * math.sin(y * 0.6)
            c = _ramp(BRASS_STOPS, min(1.0, t))
            if f == 7:
                c = _scale(c, 0.6)
            if abs(y - h / 2) < 0.6:
                c = _scale(c, 0.8)
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _blade(px, region, rng):
    """A long golden leaf: transparent outside, a dark central vein, lighter edges."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            t = (y + 0.5) / h            # 0 at the tip, 1 at the root
            half = 0.5 * math.sin(math.pi * min(1.0, t * 1.05)) ** 0.8 * (0.55 + 0.45 * t)
            dx = (x + 0.5) / w - 0.5
            if abs(dx) > half * 0.98 or t < 0.02:
                _put(px, u, v, x, y, (0, 0, 0), 0)
                continue
            c = _ramp(GOLD_STOPS, 0.45 + 0.4 * (abs(dx) / max(half, 1e-3)) - 0.15 * t)
            if abs(dx) < 0.045:
                c = _scale(c, 0.65)
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _planks(img, region, base, dark, rng, plank_h=4):
    fine_wood(img, region, base, dark, plank_h, rng, knots=0.08, grain=0.1)


def _green(img, region, rng):
    """Dark olive green planks: painted, worn, the grain showing through, a few repaired planks."""
    u, v, w, h = region
    fine_wood(img, region, _rgb("4f6b3a"), _rgb("22301a"), 4, rng, knots=0.05, grain=0.08)
    px = img.load()
    nz = _noise(w, h, 6, rng)
    for y in range(h):
        for x in range(w):
            c = px[u + x, v + y][:3]
            k = 1.0 + 0.12 * nz[y][x]
            if rng.random() < 0.015:
                k += 0.18
            _put(px, u, v, x, y, _scale(_mix(c, (70, 98, 58), 0.3), k))


def _trim(px, region, rng, base_stops=GOLD_STOPS, dark=False):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            if dark:
                c = _scale(_rgb("3a2414"), 1.0 + 0.1 * math.sin(y * 0.9))
                if h // 2 - 2 <= y <= h // 2 + 1:
                    bead = (x % 4) in (1, 2)
                    c = _ramp(GOLD_STOPS, 0.8 if bead else 0.35)
            else:
                t = 0.5 + 0.4 * math.cos((y + 0.5 - h / 2) / (h / 2) * math.pi)
                c = _ramp(base_stops, t)
                if 3 <= y <= h - 4 and (x % 6) in (0, 5):
                    c = _scale(c, 0.65)
                if y in (0, h - 1):
                    c = _scale(c, 0.5)
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _scroll(px, region, rng):
    """A gilded scroll: two spirals curling away from each other on a stem, transparent around them."""
    u, v, w, h = region
    S = 4
    m = Image.new("L", (w * S, h * S), 0)
    d = ImageDraw.Draw(m)
    for cx, cy, sgn in ((w * 0.3, h * 0.55, 1), (w * 0.7, h * 0.45, -1)):
        pts = []
        for i in range(120):
            t = i / 119
            a = sgn * t * 1.8 * 2 * math.pi
            r = (1 - 0.85 * t) * w * 0.2
            pts.append(((cx + math.cos(a) * r) * S, (cy + math.sin(a) * r) * S))
        d.line(pts, fill=255, width=int(2.2 * S))
    d.line([(w * 0.3 * S, (h * 0.55 + w * 0.2) * S), (w * 0.7 * S, (h * 0.45 - w * 0.2) * S)], fill=255, width=int(2.0 * S))
    m = m.resize((w, h), Image.BILINEAR)
    mp = m.load()
    for y in range(h):
        for x in range(w):
            if mp[x, y] > 100:
                _put(px, u, v, x, y, _jitter(_ramp(GOLD_STOPS, 0.4 + 0.45 * mp[x, y] / 255.0), rng, 4))
            else:
                _put(px, u, v, x, y, (0, 0, 0), 0)


def _window_frame(px, region, rows=2, cols=3, arch=False):
    """A window frame: dark wood with a gilded inner bead, mullions; the panes are left transparent (glass seen
    through: the room or the sky behind it)."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            fx, fy = (x + 0.5) / w, (y + 0.5) / h
            if arch:
                ax = abs(fx - 0.5) / 0.5
                yy = 0.42 - fy
                if yy > 0 and ax ** 2 + (yy / 0.42) ** 2 > 1.0:
                    _put(px, u, v, x, y, (0, 0, 0), 0)
                    continue
                edge = (yy > 0 and ax ** 2 + (yy / 0.42) ** 2 > 0.8) or x < 2 or x > w - 3 or y > h - 3
            else:
                edge = x < 2 or x > w - 3 or y < 2 or y > h - 3
            mull = any(abs(fx - c / cols) < 0.035 for c in range(1, cols)) or any(abs(fy - r / rows) < 0.035 for r in range(1, rows))
            if edge:
                c = _rgb("3a2414") if (x in (0, w - 1) or y in (0, h - 1)) else _ramp(GOLD_STOPS, 0.7)
                _put(px, u, v, x, y, c)
            elif mull:
                _put(px, u, v, x, y, _rgb("4a3020"))
            else:
                _put(px, u, v, x, y, (0, 0, 0), 0)


def _window_lit(px, region):
    """Small arched window lit from inside: a cross of glazing bars, a dark wooden surround."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            fx, fy = (x + 0.5) / w, (y + 0.5) / h
            ax = abs(fx - 0.5) / 0.5
            top = 0.3
            if fy < top and ax ** 2 + ((top - fy) / top) ** 2 > 1.0:
                _put(px, u, v, x, y, (0, 0, 0), 0)
                continue
            border = x in (0, w - 1) or y == h - 1 or (fy < top and ax ** 2 + ((top - fy) / top) ** 2 > 0.62)
            if border:
                c = _rgb("3a2414")
            elif x == w // 2 or y == int(h * 0.55):
                c = _rgb("5a3a1e")
            else:
                g = 1.0 - 0.3 * abs(fy - 0.6)
                c = _scale((255, 206, 118), g)
            _put(px, u, v, x, y, c)


def _rose(px, region):
    """The bow's fan window: a half disc (its flat edge down) of radial lit panes, amber and green, in dark ribs."""
    u, v, w, h = region
    cx, cy = w / 2, h - 0.5
    R = w / 2
    for y in range(h):
        for x in range(w):
            dx, dy = x + 0.5 - cx, cy - (y + 0.5)
            r = math.hypot(dx, dy) / R
            if r > 1.0 or dy < 0:
                _put(px, u, v, x, y, (0, 0, 0), 0)
                continue
            a = math.degrees(math.atan2(dy, dx))
            sector = int(a // 18.0)
            ring_i = int(r / 0.2)
            if r > 0.92 or r < 0.14 or abs(a - (sector + 0.5) * 18.0) > 7.6 or abs(r - 0.2 * round(r / 0.2)) < 0.025:
                c = _rgb("2e1d10") if r < 0.94 else _ramp(GOLD_STOPS, 0.65)
            else:
                pal = [(255, 214, 124), (118, 172, 96), (238, 176, 84), (200, 90, 60), (255, 200, 110), (96, 150, 84)]
                c = pal[(ring_i * 2 + sector) % len(pal)]
            _put(px, u, v, x, y, c)


def _flag(px, region, rng):
    """A long red pennant: folds along its length, the fly cut into stepped tails (transparent)."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            fx, fy = (x + 0.5) / w, (y + 0.5) / h
            # the fly: two tails with a stepped notch, narrowing
            notch = fx > 0.72 and abs(fy - 0.5) < (fx - 0.72) * 1.0
            narrow = abs(fy - 0.5) > 0.5 - 0.18 * max(0.0, fx - 0.4)
            steps = fx > 0.55 and (int(fx * 16) % 2 == 1) and abs(fy - 0.5) > 0.42
            if notch or narrow or steps:
                _put(px, u, v, x, y, (0, 0, 0), 0)
                continue
            k = 1.0 + 0.12 * math.sin(fx * 18 + fy * 2) - 0.12 * (fy > 0.85)
            c = _scale(_rgb("b2221d"), k)
            if x < 2:
                c = _rgb("6e1410")
            _put(px, u, v, x, y, _jitter(c, rng, 4))


def _panel_green(img, region, rng):
    u, v, w, h = region
    _green(img, region, rng)
    px = img.load()
    for y in range(h):
        for x in range(w):
            if x < 2 or y < 2 or x > w - 3 or y > h - 3:
                _put(px, u, v, x, y, _ramp(GOLD_STOPS, 0.4 + 0.4 * ((x + y) % 3) / 2))
            elif x < 3 or y < 3 or x > w - 4 or y > h - 4:
                _put(px, u, v, x, y, _rgb("2c3a20"))


def _wall_wood(img, region, rng):
    u, v, w, h = region
    fine_wood(img, region, _rgb("8a5a30"), _rgb("3a2414"), 4, rng, vertical=True, knots=0.05)
    px = img.load()
    for y in range(h):
        for x in range(w):
            if x < 3 or x > w - 4:
                _put(px, u, v, x, y, _ramp(GOLD_STOPS, 0.35 + 0.3 * math.cos((x - (1 if x < 3 else w - 2)) * 1.2)))
            if y < 2 or y > h - 3:
                _put(px, u, v, x, y, _rgb("3a2414"))


def _hatch(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("6a4426"), 1.0 + 0.06 * math.sin(x // 6 * 1.7) + 0.04 * math.sin(y * 0.5))
            if x % 6 == 5:
                c = _rgb("2c1b0e")
            if y in (5, 6, h - 7, h - 6):
                c = _rgb("2a2a2c")
            if x < 2 or y < 2 or x > w - 3 or y > h - 3:
                c = _rgb("3a2516")
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _window_gallery(px, region):
    """Tall arched gallery window lit from inside: a gilded frame, dark leading, amber quarries alternating with clear
    ones (seen through), a lit transom."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            fx, fy = (x + 0.5) / w, (y + 0.5) / h
            ax = abs(fx - 0.5) / 0.5
            top = 0.22
            if fy < top and ax ** 2 + ((top - fy) / top) ** 2 > 1.0:
                _put(px, u, v, x, y, (0, 0, 0), 0)
                continue
            frame = x in (0, w - 1) or y in (h - 1, h - 2) or (fy < top and ax ** 2 + ((top - fy) / top) ** 2 > 0.7)
            if frame:
                _put(px, u, v, x, y, _ramp(GOLD_STOPS, 0.55 + 0.3 * (x % 2)))
                continue
            if x == w // 2 or y in (int(h * 0.4), int(h * 0.7)) or x in (1, w - 2):
                _put(px, u, v, x, y, _rgb("3a2414"))
                continue
            if fy < 0.4:
                g = 1.0 - 0.25 * abs(fy - 0.3)
                _put(px, u, v, x, y, _scale((255, 206, 118), g))
                continue
            qx, qy = (x - 2) // 3, (y - int(h * 0.4)) // 3
            if (qx + qy) % 2 == 0:
                _put(px, u, v, x, y, _scale((255, 196, 104), 0.95 - 0.2 * (fy - 0.4)))
            else:
                _put(px, u, v, x, y, (0, 0, 0), 0)


def _window_fan(px, region):
    """The bow's quarter fan window, in polar layout (u: the angle from its top edge round to its aft edge, v: the radius
    from the hub): stained panes in amber, green, gold and red between dark radial ribs and leaded arcs, a gilded rim."""
    u, v, w, h = region
    pal = [(255, 210, 120), (120, 176, 96), (238, 176, 80), (196, 86, 56), (255, 226, 150), (98, 150, 84), (230, 150, 70)]
    for y in range(h):
        for x in range(w):
            fa, fr = (x + 0.5) / w, (y + 0.5) / h
            sector = int(fa * 7)
            ring_i = int(fr * 4)
            edge_a = abs(fa * 7 - round(fa * 7)) < 0.09
            edge_r = abs(fr * 4 - round(fr * 4)) < 0.1
            if fr > 0.93:
                c = _ramp(GOLD_STOPS, 0.7)
            elif fr < 0.2:
                c = _ramp(GOLD_STOPS, 0.5) if fr < 0.14 else _rgb("2e1d10")
            elif edge_a or edge_r:
                c = _rgb("2e1d10")
            else:
                c = pal[(ring_i * 3 + sector) % len(pal)]
                c = _scale(c, 0.92 + 0.12 * math.sin(fa * 40 + fr * 9))
            _put(px, u, v, x, y, c)


def _petal(px, region, rng):
    """A pointed petal plate of the engines' turbine cowl: green-bronze, a gilded rim, a rivet row (transparent
    outside its outline; the point at v = 0)."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            t = (y + 0.5) / h
            half = 0.5 * min(1.0, math.sin(math.pi * min(1.0, t * 1.15)) ** 0.6) * (0.65 + 0.35 * t)
            dx = (x + 0.5) / w - 0.5
            if abs(dx) > half:
                _put(px, u, v, x, y, (0, 0, 0), 0)
                continue
            if abs(dx) > half - 0.12:
                c = _ramp(GOLD_STOPS, 0.6)
            else:
                c = _mix(_ramp(BRONZE_STOPS, 0.55 + 0.3 * (0.5 - abs(dx))), (92, 128, 88), 0.45)
                if abs(dx) < 0.05 and y % 5 == 2:
                    c = _ramp(BRASS_STOPS, 0.9)
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _louver(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            if y < 3:
                c = _ramp(BRASS_STOPS, 0.85 - 0.1 * y)
            elif y > h - 3:
                c = _ramp(BRASS_STOPS, 0.4)
            else:
                c = _scale(_mix(_ramp(BRASS_STOPS, 0.45), (40, 30, 20), 0.6), 1.0 - 0.4 * (y - 3) / (h - 5))
            if x % 16 == 0:
                c = _ramp(BRASS_STOPS, 0.95)
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _coaming(img, region, rng):
    """Green panel of the roof deck's coaming with a gilded scroll in the middle and a gilded frame (along u)."""
    u, v, w, h = region
    _green(img, region, rng)
    px = img.load()
    S = 4
    m = Image.new("L", (w * S, h * S), 0)
    d = ImageDraw.Draw(m)
    for cx, sgn in ((w * 0.38, 1), (w * 0.62, -1)):
        pts = []
        for i in range(90):
            t = i / 89
            a = sgn * t * 1.7 * 2 * math.pi + (0 if sgn > 0 else math.pi)
            r = (1 - 0.82 * t) * h * 0.32
            pts.append(((cx + math.cos(a) * r * 1.3) * S, (h * 0.5 + math.sin(a) * r) * S))
        d.line(pts, fill=255, width=int(1.6 * S))
    d.line([(w * 0.18 * S, h * 0.5 * S), (w * 0.82 * S, h * 0.5 * S)], fill=255, width=int(1.2 * S))
    m = m.resize((w, h), Image.BILINEAR)
    mp = m.load()
    for y in range(h):
        for x in range(w):
            if y < 2 or y > h - 3 or x < 1 or x > w - 2:
                _put(px, u, v, x, y, _ramp(GOLD_STOPS, 0.45 + 0.35 * ((x + y) % 3) / 2))
            elif mp[x, y] > 90:
                _put(px, u, v, x, y, _ramp(GOLD_STOPS, 0.45 + 0.4 * mp[x, y] / 255.0))


def _stern_panel(img, region, rng):
    """Carved green panel in a gilded frame, a gilded rosette in its middle (the back of the castle)."""
    u, v, w, h = region
    _green(img, region, rng)
    px = img.load()
    for y in range(h):
        for x in range(w):
            if x < 2 or y < 2 or x > w - 3 or y > h - 3:
                _put(px, u, v, x, y, _ramp(GOLD_STOPS, 0.4 + 0.4 * ((x + y) % 3) / 2))
            elif x < 4 or y < 4 or x > w - 5 or y > h - 5:
                _put(px, u, v, x, y, _rgb("2c3a20"))
            else:
                r = math.hypot(x + 0.5 - w / 2, y + 0.5 - h / 2)
                a = math.atan2(y + 0.5 - h / 2, x + 0.5 - w / 2)
                if r < 2.0 or (r < 5.5 and abs(math.sin(a * 4)) > 0.75 and r > 3.0):
                    _put(px, u, v, x, y, _ramp(GOLD_STOPS, 0.7 - 0.05 * r))


def _cap_iron(px, region, rng):
    """Dark ribbed iron: raised ribs along v, rivets between them, a little rust."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            rib = x % 8
            c = _ramp([(0.0, (44, 40, 38)), (0.5, (82, 74, 64)), (1.0, (134, 122, 104))], 0.38 + (0.42 if rib in (3, 4) else 0.0) - (0.15 if rib == 5 else 0.0))
            if rib in (0, 7) and y % 6 == 3:
                c = (120, 112, 100)
            if rng.random() < 0.03:
                c = _mix(c, (110, 64, 34), 0.5)
            _put(px, u, v, x, y, _jitter(c, rng, 3))


def _medal_glass(px, region):
    """The medallion's porthole: blue-grey glass round a glowing blue heart, transparent outside the circle."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            dx, dy = (x + 0.5) / w * 2 - 1, (y + 0.5) / h * 2 - 1
            r = math.hypot(dx, dy)
            if r > 1.0:
                _put(px, u, v, x, y, (0, 0, 0), 0)
                continue
            if r > 0.88:
                c = _ramp(BRASS_STOPS, 0.8)
            elif r < 0.35:
                c = _mix((235, 250, 255), (70, 160, 240), r / 0.35)
            else:
                c = _mix((96, 136, 176), (60, 84, 120), (r - 0.35) / 0.53)
                if abs(dx - dy) < 0.06 and r > 0.45:
                    c = (170, 200, 220)
            _put(px, u, v, x, y, c)


def _plate(px, region, stops, rng):
    """One riveted metal plate (drawn whole on each panel): a light top edge, a dark seam round it, rivets in the corners
    and along the edges, a soft patina."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            t = 0.62 - 0.22 * (y / (h - 1)) + 0.06 * math.sin(x * 0.9 + y * 0.4)
            if (x * 7 + y * 5) % 17 == 0:
                t -= 0.12
            c = _ramp(stops, t)
            if x == 0 or y == 0:
                c = _ramp(stops, 0.92)
            elif x == w - 1 or y == h - 1:
                c = _ramp(stops, 0.12)
            elif (x in (2, w - 3) and y % 4 == 2) or (y in (2, h - 3) and x % 4 == 2):
                c = _ramp(stops, 0.98)
            _put(px, u, v, x, y, _jitter(c, rng, 2))


def _ring_bronze(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            t = 0.42 + 0.38 * math.cos((y + 0.5 - h * 0.4) / (h / 2) * math.pi / 1.6)
            c = _mix(_ramp(BRASS_STOPS, t), (160, 120, 70), 0.25)
            if y in (0, h - 1):
                c = _scale(c, 0.6)
            _put(px, u, v, x, y, _jitter(c, rng, 2))


def make_texture(path):
    rng = random.Random(11)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    R = REGIONS
    _quilt(px, R["cloth"], rng)
    _quilt(px, R["cloth_dark"], rng, dark=True)
    _strap(px, R["strap"], rng)
    _strap(px, R["girdle"], rng, chain=True)
    polished_metal(img, R["gold"], GOLD_STOPS, rng, seed=0.3)
    polished_metal(img, R["brass"], BRASS_STOPS, rng, seed=1.1)
    polished_metal(img, R["bronze"], BRONZE_STOPS, rng, seed=2.0)
    polished_metal(img, R["copper"], COPPER_STOPS, rng, seed=2.7)
    hammered_iron(img, R["iron"], _rgb("3a3a3e"), rng)
    polished_metal(img, R["steel"], STEEL_STOPS, rng, seed=0.9)
    hammered_iron(img, R["gear_iron"], _rgb("4a4846"), rng)
    u, v, w, h = R["chain"]
    for y in range(h):
        for x in range(w):
            link = (y // 4) % 2
            c = _rgb("6c6a68") if (x in (4, 5, 10, 11) if link else y % 4 in (0, 3)) else _rgb("3a3836")
            _put(px, u, v, x, y, _jitter(c, rng, 4))
    twisted_rope(img, R["rope"], _rgb("a08560"), _rgb("5a4630"), rng)
    twisted_rope(img, R["rope_dark"], _rgb("6a5236"), _rgb("2e2214"), rng)
    twisted_rope(img, R["pennant_rope"], _rgb("8a6e48"), _rgb("4a3824"), rng)
    u, v, w, h = R["glow"]
    for y in range(h):
        for x in range(w):
            _put(px, u, v, x, y, _jitter((255, 214, 130), rng, 6))
    paint_lamp_glass(px, *R["lantern"])
    u, v, w, h = R["glass"]
    for y in range(h):
        for x in range(w):
            _put(px, u, v, x, y, _mix((170, 210, 230), (230, 245, 250), 0.5 + 0.5 * math.sin((x + y) * 0.4)))
    _gem(px, R["gem"])
    _crystal(px, R["crystal"], rng)
    _core(px, R["crystal_core"])
    u, v, w, h = R["gauge"]
    for y in range(h):
        for x in range(w):
            r = math.hypot(x + 0.5 - w / 2, y + 0.5 - h / 2) / (w / 2)
            c = (236, 226, 196) if r < 0.8 else _ramp(BRASS_STOPS, 0.7)
            if r < 0.8 and abs((x + 0.5 - w / 2) - (y + 0.5 - h / 2) * 0.6) < 0.7 and y < h / 2:
                c = (40, 30, 20)
            _put(px, u, v, x, y, c)
    u, v, w, h = R["coral_red"]
    for y in range(h):
        for x in range(w):
            _put(px, u, v, x, y, _jitter(_rgb("a0281e"), rng, 6))
    woven(img, R["red_velvet"], _rgb("8a1c1c"), rng)
    fine_wood(img, R["dark_wood"], _rgb("4a2e18"), _rgb("22140a"), 4, rng)
    fine_wood(img, R["wood"], _rgb("8e5c32"), _rgb("442814"), 4, rng)
    fine_wood(img, R["rail"], _rgb("6a4222"), _rgb("2c1a0c"), 4, rng)
    end_grain(img, R["end_grain"], _rgb("8a5c34"), _rgb("4a2e16"), rng)
    fine_wood(img, R["rung"], _rgb("7a5030"), _rgb("3a2414"), 4, rng)
    _rivets(px, R["engine_plate"], [(0.0, (52, 36, 20)), (0.35, (96, 64, 34)), (0.7, (140, 98, 52)), (1.0, (190, 146, 84))], rng, pw=32, ph=16)
    _rivets(px, R["engine_dark"], [(0.0, (30, 30, 34)), (0.5, (62, 60, 62)), (1.0, (110, 106, 100))], rng, pw=32, ph=16)
    _feather(px, R["feather"], rng)
    fine_wood(img, R["hull_band"], _rgb("3e2614"), _rgb("1c1008"), 4, rng)
    _blade(px, R["blade"], rng)
    lt._round(px, R["porthole"], lambda r, dx, dy: (255, 214, 130) if r < 0.7 else _ramp(BRASS_STOPS, 0.8))
    _planks(img, R["hull_brown"], _rgb("9a6234"), _rgb("4a2c14"), rng)
    _green(img, R["hull_green"], rng)
    _trim(px, R["trim_gold"], rng)
    _trim(px, R["trim_dark"], rng, dark=True)
    _scroll(px, R["scroll"], rng)
    fine_wood(img, R["deck"], _rgb("a0703e"), _rgb("4a3018"), 4, rng)
    u, v, w, h = R["roof_green"]
    fine_wood(img, R["roof_green"], _rgb("4e6e3c"), _rgb("22301a"), 4, rng, vertical=True, knots=0.0)
    for y in range(h - 4, h):
        for x in range(w):
            _put(px, u, v, x, y, _ramp(GOLD_STOPS, 0.4 + 0.15 * (y - h + 4)))
    _window_frame(px, R["window_frame"])
    _window_lit(px, R["window_lit"])
    _rose(px, R["window_rose"])
    _flag(px, R["flag"], rng)
    lt._door_leaf(px, R["door_leaf"], rng)
    _hatch(px, R["hatch"], rng)
    _panel_green(img, R["panel_green"], rng)
    _trim(px, R["cornice"], rng, dark=True)
    _window_frame(px, R["window_arch"], rows=2, cols=4, arch=True)
    _wall_wood(img, R["wall_wood"], rng)
    _window_gallery(px, R["window_gallery"])
    _window_fan(px, R["window_fan"])
    polished_metal(img, R["brass_olive"], [(0.0, (70, 58, 26)), (0.3, (126, 106, 52)), (0.6, (176, 148, 78)), (0.85, (210, 182, 112)),
                                           (1.0, (232, 214, 156))], rng, seed=1.7)
    _rivets(px, R["engine_brass"], [(0.0, (74, 56, 24)), (0.35, (128, 98, 44)), (0.7, (182, 146, 74)), (1.0, (226, 196, 128))], rng, pw=32, ph=16)
    u, v, w, h = R["engine_brass"]
    for y in range(h):
        for x in range(w):
            if (x * 5 + y * 3) % 23 == 0:
                _put(px, u, v, x, y, _mix(px[u + x, v + y][:3], (96, 120, 80), 0.5))
    _petal(px, R["petal"], rng)
    _louver(px, R["louver"], rng)
    _coaming(img, R["coaming"], rng)
    _stern_panel(img, R["stern_panel"], rng)
    _cap_iron(px, R["cap_iron"], rng)
    _medal_glass(px, R["medal_glass"])
    _ring_bronze(px, R["ring_bronze"], rng)
    for name, stops in (("plate_brass", [(0.0, (66, 54, 26)), (0.35, (118, 98, 50)), (0.7, (164, 136, 72)), (1.0, (204, 176, 106))]),
                        ("plate_bronze", [(0.0, (46, 34, 20)), (0.35, (84, 62, 34)), (0.7, (122, 92, 52)), (1.0, (160, 124, 76))]),
                        ("plate_helmet", [(0.0, (92, 70, 30)), (0.35, (150, 118, 54)), (0.7, (198, 164, 86)), (1.0, (236, 214, 150))])):
        _plate(px, R[name], stops, rng)
    lt._round(px, R["fairy"], lambda r, dx, dy: (255, 236, 170) if r < 0.45 else (255, 196, 96) if r < 0.85 else (220, 150, 70))
    u, v, w, h = R["turret"]
    fine_wood(img, R["turret"], _rgb("6e4626"), _rgb("2e1c0e"), 4, rng, vertical=True)
    for y in (6, 7, h - 8, h - 7):
        for x in range(w):
            _put(px, u, v, x, y, _rgb("3a3a3c") if x % 5 else _rgb("7a766e"))
    img.save(path)
    return img


# ================================================================ interior atlas
SIZE_IN = lt.SIZE_IN
REGIONS_IN_EXTRA = {
    "in_stone":        (0, 192, 32, 48),   # cockpit: grey stone blocks between timber posts, a beam on top
    "in_wall_lounge":  (32, 192, 32, 48),  # lounge: carved dark panelling, a gilded frieze, red fabric
    "in_wall_store":   (64, 192, 32, 48),  # storeroom: rough planks and cross braces
    "in_wall_works":   (96, 192, 32, 48),  # engine room: stone blocks, riveted plates, a pipe
    "in_floor_grate":  (128, 192, 32, 32), # engine room: planks with iron grates
    "in_floor_lounge": (160, 192, 32, 32), # polished parquet
    "in_ceil_lounge":  (192, 192, 32, 32), # coffered ceiling with gilded beads
    "in_crystal":      (224, 192, 16, 32), # glowing crystal (lit)
    "in_core":         (240, 192, 32, 32), # the engine's crystal core: rays (lit, transparent outside the circle)
    "in_sofa":         (272, 192, 16, 16), # tufted red velvet
    "in_sofa_wood":    (288, 192, 16, 16), # carved dark wood
    "in_rug_red":      (304, 192, 64, 64), # the lounge's red rug with a gold border
    "in_map_world":    (368, 192, 48, 32), # the framed map (green lands on parchment)
    "in_wood_carved":  (416, 192, 32, 16), # carved dark wood with gilding (furniture)
    "in_brass_pol":    (448, 192, 16, 16), # polished brass (instruments)
    "in_cloth_sack":   (464, 192, 16, 16), # burlap
    "in_ceil_store":   (480, 192, 32, 32), # rough ceiling planks between joists
}
REGIONS_IN = dict(lt.REGIONS_IN)
REGIONS_IN.update(REGIONS_IN_EXTRA)


def _stone(px, region, rng, base=(120, 116, 108), mortar=(70, 66, 60), bh=6, bw=10, post=True):
    u, v, w, h = region
    nz = _noise(w, h, 6, rng)
    for y in range(h):
        row = y // bh
        off = (row % 2) * (bw // 2)
        for x in range(w):
            col = (x + off) // bw
            tone = _jitter(_scale(base, 0.9 + 0.2 * ((row * 7 + col * 13) % 5) / 4), random.Random(row * 31 + col), 6)
            c = _scale(tone, 1.0 + 0.08 * nz[y][x])
            if y % bh == bh - 1 or (x + off) % bw == bw - 1:
                c = mortar
            elif y % bh == 0:
                c = _scale(c, 1.08)
            if post and (x < 3 or x > w - 4):
                c = _scale(_rgb("5a3a20"), 1.0 + 0.06 * math.sin(y * 0.7))
            if post and y < 4:
                c = _scale(_rgb("4a2e18"), 1.0 + 0.05 * math.sin(x * 0.9))
            _put(px, u, v, x, y, _jitter(c, rng, 2))


def make_interior_texture(path, tmp_base):
    """The Sky Leviathan's room atlas (drawn to tmp_base first), then the rooms of the Crystal Airship below it."""
    lt.make_interior_texture(tmp_base)
    img = Image.open(tmp_base).convert("RGBA")
    px = img.load()
    rng = random.Random(23)
    R = REGIONS_IN_EXTRA
    _stone(px, R["in_stone"], rng)
    # lounge panelling: dark carved wainscot below, red fabric panels, a gilded frieze under the ceiling
    u, v, w, h = R["in_wall_lounge"]
    fine_wood(img, R["in_wall_lounge"], _rgb("5a3418"), _rgb("2a160a"), 4, rng, vertical=True, knots=0.0)
    for y in range(h):
        for x in range(w):
            if y < 4:
                c = _ramp(GOLD_STOPS, 0.35 + 0.4 * ((x // 2 + y) % 3) / 2)
            elif 8 <= y < 26 and 3 <= x % 16 < 13:
                c = _scale(_rgb("7a1a18"), 1.0 + 0.08 * math.sin(x * 0.8 + y * 0.3))
                if x % 16 in (3, 12) or y in (8, 25):
                    c = _ramp(GOLD_STOPS, 0.6)
            elif y in (27, 28):
                c = _ramp(GOLD_STOPS, 0.5)
            elif y > 30 and (x % 16 in (2, 13) or y in (31, h - 3)):
                c = _rgb("2a160a")
            else:
                continue
            _put(px, u, v, x, y, _jitter(c, rng, 3))
    # storeroom: rough planks and braces
    fine_wood(img, R["in_wall_store"], _rgb("6e4a2a"), _rgb("2e1c0e"), 4, rng, knots=0.2)
    u, v, w, h = R["in_wall_store"]
    for y in range(h):
        for x in range(w):
            if x < 3 or x > w - 4 or y < 3:
                _put(px, u, v, x, y, _scale(_rgb("4a2e18"), 1.0 + 0.05 * math.sin(y + x)))
            elif abs((x - 3) - (y - 3) * (w - 6) / (h - 6)) < 1.5 and y > 6:
                _put(px, u, v, x, y, _rgb("553620"))
    # engine room: stone blocks below, riveted plates above, a copper pipe along it
    _stone(px, R["in_wall_works"], rng, base=(110, 104, 96), post=False)
    u, v, w, h = R["in_wall_works"]
    for y in range(0, 18):
        for x in range(w):
            c = _ramp([(0.0, (50, 46, 42)), (0.5, (96, 88, 76)), (1.0, (140, 126, 100))], 0.4 + 0.3 * math.sin(x * 0.3 + y * 0.2))
            if y % 9 == 0 or x % 16 == 0:
                c = _scale(c, 0.6)
            elif y % 9 in (2, 7) and x % 4 == 2:
                c = (170, 150, 110)
            _put(px, u, v, x, y, c)
    for y in range(20, 24):
        for x in range(w):
            _put(px, u, v, x, y, _ramp(COPPER_STOPS, 0.2 + 0.25 * (y - 20)))
    # engine room floor: planks with square iron grates
    fine_wood(img, R["in_floor_grate"], _rgb("6a4a2c"), _rgb("2e1e10"), 4, rng)
    u, v, w, h = R["in_floor_grate"]
    for y in range(h):
        for x in range(w):
            gx, gy = x % 16, y % 16
            if 3 <= gx < 13 and 3 <= gy < 13:
                c = _rgb("1c1a18") if (gx + gy) % 3 else _rgb("4a4640")
                _put(px, u, v, x, y, c)
            elif gx in (2, 13) and 2 <= gy <= 13 or gy in (2, 13) and 2 <= gx <= 13:
                _put(px, u, v, x, y, _rgb("6a5a40"))
    fine_wood(img, R["in_floor_lounge"], _rgb("8a5a30"), _rgb("3a2210"), 4, rng, knots=0.0, grain=0.06)
    u, v, w, h = R["in_ceil_lounge"]
    for y in range(h):
        for x in range(w):
            gx, gy = x % 16, y % 16
            if gx < 2 or gy < 2:
                c = _scale(_ramp(GOLD_STOPS, 0.3), 0.8) if (gx == 1 or gy == 1) else _rgb("2a160a")
            else:
                c = _scale(_rgb("5a3418"), 0.9 + 0.1 * math.sin(gx * 0.5) + 0.08 * (gy > 12))
            _put(px, u, v, x, y, _jitter(c, rng, 3))
    _crystal(px, R["in_crystal"], rng)
    _core(px, R["in_core"])
    woven(img, R["in_sofa"], _rgb("8e1e1c"), rng)
    u, v, w, h = R["in_sofa"]
    for y in range(h):
        for x in range(w):
            if (x % 8 == 4 and y % 8 == 4) or (x % 8 == 0 and y % 8 == 0):
                _put(px, u, v, x, y, _rgb("4a0e0c"))
    fine_wood(img, R["in_sofa_wood"], _rgb("4a2a14"), _rgb("1e1008"), 4, rng)
    lt._rug_big(px, R["in_rug_red"], rng, field="8a1c18", border="c89a48", dark="3a0e0b", accent="6a1410")
    u, v, w, h = R["in_map_world"]
    nz = _noise(w, h, 5, rng)
    for y in range(h):
        for x in range(w):
            if x < 2 or y < 2 or x > w - 3 or y > h - 3:
                c = _ramp(GOLD_STOPS, 0.5)
            else:
                land = nz[y][x] > 0.15
                c = (98, 140, 70) if land else (226, 210, 168)
                if abs(nz[y][x] - 0.15) < 0.03:
                    c = (90, 70, 40)
            _put(px, u, v, x, y, _jitter(c, rng, 4))
    fine_wood(img, R["in_wood_carved"], _rgb("4e2c14"), _rgb("22120a"), 4, rng)
    u, v, w, h = R["in_wood_carved"]
    for x in range(w):
        for y in (1, h - 2):
            _put(px, u, v, x, y, _ramp(GOLD_STOPS, 0.6 if x % 3 else 0.3))
    polished_metal(img, R["in_brass_pol"], BRASS_STOPS, rng, seed=3.3)
    woven(img, R["in_cloth_sack"], _rgb("a08a62"), rng)
    fine_wood(img, R["in_ceil_store"], _rgb("5e3e22"), _rgb("2a1a0c"), 4, rng)
    u, v, w, h = R["in_ceil_store"]
    for y in range(h):
        for x in range(w):
            if x % 16 < 3:
                _put(px, u, v, x, y, _scale(_rgb("3a2414"), 1.0 + 0.05 * math.sin(y)))
    img.save(path)
    return img


def make_item_icon(path):
    """16x16 item icon: the cream balloon lobes with a gold strap, the golden ring, the brown and green hull,
    a blue crystal under it."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((0, 1, 6, 6), fill=(232, 224, 204, 255), outline=(150, 140, 120, 255))
    d.ellipse((9, 0, 15, 5), fill=(232, 224, 204, 255), outline=(150, 140, 120, 255))
    d.ellipse((2, 1, 13, 8), fill=(244, 238, 222, 255), outline=(150, 140, 120, 255))
    d.line((6, 1, 6, 8), fill=(214, 170, 72, 255))
    d.line((10, 1, 10, 7), fill=(214, 170, 72, 255))
    d.ellipse((6, 6, 10, 10), outline=(222, 176, 70, 255))
    d.polygon([(0, 10), (15, 10), (14, 12), (11, 14), (4, 14), (1, 12)], fill=(90, 120, 62, 255), outline=(40, 52, 30, 255))
    d.rectangle((2, 10, 13, 11), fill=(150, 98, 52, 255))
    d.rectangle((12, 8, 15, 10), fill=(140, 92, 48, 255))
    for x in (4, 7, 10):
        d.point((x, 11), fill=(255, 214, 130, 255))
    d.point((14, 12), fill=(90, 200, 255, 255))
    d.point((7, 15), fill=(120, 220, 255, 255))
    d.point((8, 15), fill=(60, 150, 240, 255))
    d.point((0, 3), fill=(180, 34, 30, 255))
    img.save(path)


if __name__ == "__main__":
    import os
    import sys
    import tempfile
    out = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix="crystal_tex_")   # preview directory
    os.makedirs(out, exist_ok=True)
    make_texture(os.path.join(out, "tex.png"))
    make_interior_texture(os.path.join(out, "tex_in.png"), os.path.join(out, "tex_in_base.png"))
    make_item_icon(os.path.join(out, "icon.png"))
    print("textures in", out)
