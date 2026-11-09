"""Procedural pixel-art textures of the Gear Steamship (gear_steamship): a 512x512 atlas of the hull, the
fittings and the rooms (gear_steamship.png) and a 512x512 atlas of the sails (gear_steamship_sails.png),
so that the gold gear emblem keeps its resolution.

Colours of the reference (one starboard view at sunset): a charcoal iron-plated hull made of riveted
block-sized plates (a slightly blue-grey black, a few rust stains), riveted copper bands and caps, polished
brass trims, copper pipes, brass gear wheels, square windows glowing orange in brass frames, a black
riveted funnel with a brass band, a riveted copper dome banded with brass, dark wood masts and railings
with brass posts, dark iron chains for the rigging, black square sails made of blocky cloths with a gold
border and a big gold gear on the main sail; inside, riveted iron walls and checker plate in the engine
room, dark panelling in the captain's cabin, plank floors and beams.

Every region is (u, v, w, h); REGIONS and SAIL_REGIONS are shared with tools/generate_gear_steam.py.
"""
import math
import random

from PIL import Image

from galley_texture import _jitter, _rgb, paint_lamp_glass, polished_metal
import corsair_texture as ct

SIZE = 512
SAIL_SIZE = 512

REGIONS = {
    # hull and upper works
    "plate_a":     (0, 0, 64, 32),      # iron plate mosaic (16 px a block), the hull sides
    "plate_b":     (64, 0, 64, 32),     # the same, a little lighter (castle walls)
    "plate_c":     (128, 0, 64, 32),    # the same, darker (the bottom, under the water)
    "copper":      (192, 0, 64, 16),    # riveted copper band
    "copper2":     (192, 16, 64, 16),   # riveted copper cap (a warmer tone)
    "brass":       (256, 0, 64, 16),    # polished brass
    "brass_band":  (256, 16, 64, 16),   # riveted brass band
    "stone":       (320, 0, 64, 16),    # dark riveted beam with brass bolts (the engine house and deckhouse roof edges)
    "iron_band":   (320, 16, 64, 16),   # dark iron band with rivets
    "wood_dark":   (384, 0, 64, 32),
    "wood_mid":    (448, 0, 64, 32),
    "deck":        (0, 32, 64, 64),
    "lantern":     (64, 32, 16, 16),
    "rope":        (80, 32, 16, 16),
    "iron":        (96, 32, 16, 16),
    "bronze":      (112, 32, 16, 16),
    "glow":        (64, 48, 16, 16),
    "end_grain":   (80, 48, 16, 16),
    "chain":       (96, 48, 16, 16),    # dark iron links (the rigging of the reference)
    "glass":       (112, 48, 16, 16),
    "glow_window": (128, 32, 32, 32),   # square window glowing orange, four panes, a brass frame
    "window_in":   (160, 32, 32, 32),
    "door":        (192, 32, 32, 32),
    "grating":     (224, 32, 32, 32),
    "funnel":      (256, 32, 64, 32),   # black riveted plates, vertical seams
    "dome":        (320, 32, 64, 32),   # riveted copper plates of the dome
    "dome_drum":   (208, 160, 64, 32),  # the dome's drum: darker, browner copper plates (as on the reference)
    "mast":        (384, 32, 64, 16),
    "rail":        (384, 48, 64, 16),   # dark copper-brown railing bar
    "crate":       (448, 32, 32, 32),
    "pipe":        (480, 32, 32, 16),   # copper pipe with its highlight
    "iron_dark":   (480, 48, 16, 16),
    "wood_light":  (496, 48, 16, 16),
    "dark_wood":   (64, 64, 32, 16),
    "red_paint":   (96, 64, 16, 16),
    "white_paint": (112, 64, 16, 16),
    "navy":        (64, 80, 16, 16),
    "compass":     (80, 80, 16, 16),
    "cloth_roll":  (96, 80, 32, 16),    # furled black canvas
    "boiler_front": (128, 64, 32, 32),  # the firebox door, glowing
    "boiler":      (160, 64, 64, 32),   # riveted boiler shell
    "gauge":       (224, 64, 16, 16),
    "gear_face":   (240, 64, 16, 16),   # brass, worn darker in the middle
    "chart":       (256, 64, 32, 32),
    "books":       (288, 64, 32, 32),
    "bedding":     (320, 64, 32, 16),
    "linen":       (352, 64, 16, 16),
    "sack":        (368, 64, 16, 16),
    "canvas":      (384, 64, 32, 16),
    "coal":        (416, 64, 16, 16),
    "painting":    (432, 64, 32, 24),
    "fire":        (464, 64, 16, 16),   # glowing coals
    "plaque":      (480, 64, 32, 16),   # brass name plate
    "flag":        (464, 80, 48, 16),   # black pennant with a gold edge
    # rooms
    "wall_iron":   (0, 96, 64, 64),     # the engine room: riveted iron, a copper rail
    "floor_iron":  (64, 96, 64, 64),    # checker plate
    "ceil":        (128, 96, 64, 64),
    "floor":       (192, 96, 64, 64),
    "wall_wood":   (256, 96, 64, 64),   # the captain's cabin: dark panelling, a brass rail
    "hold_floor":  (320, 96, 64, 64),
    "hold_wall":   (384, 96, 64, 64),
    "crew_wall":   (448, 96, 64, 64),
    "carpet":      (0, 160, 32, 64),
    "rug":         (32, 160, 32, 64),
    "boat":        (64, 160, 64, 32),
    "ham":         (128, 160, 16, 16),
    "wall_stone":  (144, 160, 64, 32),
}
# names used by the shared helpers (ship_details, generate_galleon, corsair_furniture): the same pixels
for _alias, _src in (("hull_mid", "wood_mid"), ("hull_light", "wood_light"), ("hull_dark", "wood_dark"), ("wood_trim", "wood_dark"),
                     ("wood_honey", "wood_mid"), ("blue_paint", "navy"), ("pilaster", "wood_dark"), ("velvet", "red_paint"),
                     ("cushion", "red_paint"), ("brass_plain", "brass"), ("organ_wood", "wood_dark"), ("steel", "iron"),
                     ("stripe", "white_paint"), ("patch_wood", "wood_light"), ("repair", "wood_mid"), ("plate", "iron"),
                     ("hearth_stone", "wall_stone"), ("soot", "iron_dark"), ("stone_floor", "wall_stone"), ("gold", "brass"),
                     ("rope_dark", "chain"), ("rope_light", "rope"), ("cannon", "iron_dark"), ("bore", "iron_dark"),
                     ("hull_brown", "wood_dark"), ("wood", "wood_mid")):
    REGIONS[_alias] = REGIONS[_src]

# ---- the furniture of the rooms (decoration phase): regions copied pixel for pixel from the Sky Leviathan's
# interior atlas (tools/leviathan_texture.py, read only), under their own names, so that the furniture builders of
# tools/leviathan_furniture.py (barrels, chests, gauges, shelves of jars, tools, maps...) find them here
IN_COPIED = {
    "in_staves":      (0, 224, 32, 16),
    "in_barrel_lid":  (32, 224, 16, 16),
    "in_chest":       (48, 224, 32, 16),
    "in_chest_lid":   (80, 224, 32, 16),
    "in_rivets":      (112, 224, 16, 16),
    "in_dial_red":    (128, 224, 16, 16),
    "in_paper":       (144, 224, 16, 16),
    "in_slate":       (160, 224, 16, 16),
    "in_candle":      (176, 224, 16, 16),
    "in_leather":     (192, 224, 16, 16),
    "in_glass_green": (208, 224, 16, 16),
    "in_porthole":    (224, 224, 16, 16),
    "in_brick":       (240, 224, 32, 16),
    "in_jars":        (272, 224, 64, 16),
    "in_jars2":       (336, 224, 64, 16),
    "in_tools":       (400, 224, 48, 16),
    "in_blanket":     (448, 224, 32, 32),
    "in_map_wall":    (0, 240, 48, 32),
    "in_globe":       (48, 240, 64, 32),
    "in_grate":       (112, 240, 32, 32),
    "in_window":      (144, 240, 32, 48),
}
REGIONS.update(IN_COPIED)
# the other names of those builders: the ship's own metals, woods and cloths
for _alias, _src in (("in_iron", "iron"), ("in_brass", "brass"), ("in_gold", "brass"), ("in_copper", "pipe"), ("in_boiler", "boiler"),
                     ("in_beam", "wood_dark"), ("in_beam_end", "end_grain"), ("in_plank", "wood_mid"), ("in_coal", "coal"), ("in_rope", "rope"),
                     ("in_sack", "sack"), ("in_canvas", "canvas"), ("in_glow", "glow"), ("in_lamp", "lantern"), ("in_fire", "fire"),
                     ("in_chart", "chart"), ("in_books", "books"), ("in_bedding", "linen"), ("in_red_cloth", "red_paint"),
                     ("in_cushion", "red_paint"), ("in_gauge", "gauge"), ("in_rug", "rug"), ("coral_red", "red_paint"),
                     ("gear_iron", "iron_band"), ("in_boiler_band", "brass_band")):
    REGIONS[_alias] = REGIONS[_src]

# the sails (second texture): 20 px a block of canvas
SAIL_REGIONS = {
    "main_sail":   (0, 0, 220, 180),
    "mizzen_sail": (224, 0, 140, 100),
}
SAIL_CELLS = {"main_sail": (11, 9), "mizzen_sail": (7, 5)}
# filled by tools/generate_gear_steam.py (hanging_patch) before the sail atlas is painted: per sail region, the world
# height span (top, bottom) of each column of cloths and the sail's width, so that the emblem is painted round on the
# hanging (slanted) cloths
SAIL_COLUMNS = {}

_mix, _scale, _planks, _blocks, _fill = ct._mix, ct._scale, ct._planks, ct._blocks, ct._fill
# the gold of the sails: a warm bronze-gold, as the orange gold of the reference (not a pale lemon yellow)
GOLD = ("7e4418", "c27a30", "e8a24c")
# the ship's brass (gears, trims, frames, bolts): the bronze-orange of the reference (phase 4: it read pale yellow gold)
BRASS = ("6b3a14", "a8622a", "cf8436", "eeae58")


# ---------------------------------------------------------------- painters
def _plates(px, region, tones, rng, seam="141518", rivet="6e5a44", rust=0.12, block=16):
    """Riveted iron plates a block each (the voxel plates of the reference): a tone per plate, a dark seam
    on two edges and a light bevel on the others, four small rivets, a few rust stains."""
    u, v, w, h = region
    seam = _rgb(seam)
    rivet = _rgb(rivet)
    tones = [_rgb(t) for t in tones]
    for by in range(0, h, block):
        for bx in range(0, w, block):
            base = _scale(rng.choice(tones), rng.uniform(0.92, 1.08))
            stain = rng.random() < rust
            sx, sy = rng.randrange(3, block - 3), rng.randrange(2, block - 6)
            for y in range(block):
                for x in range(block):
                    if x == block - 1 or y == block - 1:
                        c = seam
                    elif x == 0 or y == 0:
                        c = _scale(base, 1.18)
                    else:
                        c = _scale(base, 1.0 + 0.03 * math.sin(x * 0.7 + y * 0.4) - 0.04 * (y / block))
                        if stain and abs(x - sx) < 2 and sy <= y < sy + 6 + (x - sx) % 3:
                            c = _mix(c, _rgb("5a3a22"), 0.45)
                    if (x in (2, block - 3)) and (y in (2, block - 3)):
                        c = rivet
                    px[u + bx + x, v + by + y] = _jitter(c, rng, 3) + (255,)


def _band(px, region, stops, rng, rivet_every=8, rivet="f0d27a", edge_dark=0.55):
    """A riveted metal band along u: polished gradient across v, dark edges, rivets on the middle line,
    plate joints every 16 px."""
    u, v, w, h = region
    for y in range(h):
        t = y / max(1, h - 1)
        for x in range(w):
            k = 0.85 + 0.25 * math.sin(math.pi * min(1.0, t * 1.15))
            c = _scale(_rgb(stops[1]), k)
            if y == 0:
                c = _rgb(stops[2])
            if y == h - 1 or x % 16 == 15:
                c = _scale(_rgb(stops[0]), edge_dark / 0.55 * 0.8)
            if x % rivet_every == rivet_every // 2 and abs(y - h / 2 + 0.5) < 1.1:
                c = _rgb(rivet)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _funnel(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("2a2b2f"), 1.0 + 0.05 * math.sin(x * 0.4) - 0.06 * (y / h))
            if x % 16 == 15:
                c = _rgb("131416")
            elif x % 16 == 0:
                c = _rgb("3c3d42")
            if y % 16 == 15:
                c = _rgb("17181a")
            if (x % 16 in (3, 12)) and (y % 8 == 4):
                c = _rgb("5e5040")
            if rng.random() < 0.02:
                c = _mix(c, _rgb("6a4228"), 0.4)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _dome(px, region, rng, tones=("95481e", "a2522a", "8a4420", "ae5c2c"), edge="d08040", seam="3e1a0a", rivet="e0a050", verdigris=0.03):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            # riveted copper plates (a tone per plate), lit along their upper edge, brass rivets
            pk = ((x // 16) * 7 + (y // 16) * 3) % 4
            c = _scale(_rgb(tones[pk]), 1.0 + 0.1 * math.sin(x * 0.2 + 0.6) - 0.1 * ((y % 16) / 16))
            if x % 16 == 15 or y % 16 == 15:
                c = _rgb(seam)
            elif x % 16 == 0 or y % 16 == 0:
                c = _rgb(edge)
            if (x % 16 in (3, 12)) and (y % 16 in (3, 12)):
                c = _rgb(rivet)
            if rng.random() < verdigris:
                c = _mix(c, _rgb("4f8a72"), 0.35)   # a touch of verdigris
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _glow_window(px, region, rng):
    """A square window glowing orange, four panes behind a cross of dark bars, in a brass frame."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            frame = x < 3 or x >= w - 3 or y < 3 or y >= h - 3
            bar = abs(x - w / 2 + 0.5) < 1.2 or abs(y - h / 2 + 0.5) < 1.2
            if frame:
                c = _mix(_rgb(BRASS[1]), _rgb(BRASS[3]), 0.5 if (x < 2 or y < 2) else 0.0)
            elif bar:
                c = _rgb("3a2a18")
            else:
                d = math.hypot(x - w / 2 + 0.5, (y - h * 0.55) * 0.9) / (w / 2)
                c = _mix(_rgb("ffe6a0"), _rgb("e0701c"), min(1.0, d * 1.15))
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _boiler_front(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("34353a"), 1.0 - 0.1 * y / h)
            if 6 <= x < w - 6 and 12 <= y < h - 5:
                d = math.hypot(x - w / 2 + 0.5, (y - h * 0.7)) / (w / 2)
                c = _mix(_rgb("ffd070"), _rgb("c03a10"), min(1.0, d * 1.2))
                if (x - 6) % 4 == 0:
                    c = _rgb("1c1c1e")   # the grate bars
            if x in (5, w - 6) and 11 <= y < h - 4 or y in (11, h - 5) and 5 <= x < w - 5:
                c = _rgb("b8862e")
            if (x in (2, w - 3)) and y % 6 == 3:
                c = _rgb("8a7458")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _rail(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            # the copper railings of the reference (a warm copper bar, lit on top)
            c = _scale(_rgb("8c4624"), 1.0 + 0.08 * math.sin(x * 0.5) + (0.25 if y < 3 else 0) - (0.2 if y > h - 4 else 0))
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _pipe(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        t = y / (h - 1)
        k = 0.7 + 0.6 * math.sin(math.pi * t) + (0.25 if 0.2 < t < 0.35 else 0)
        for x in range(w):
            c = _scale(_rgb("a8522a"), k)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _crate(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("7a5232"), 1.0 + 0.06 * math.sin(y * 0.9 + x * 0.1))
            if y % 8 == 7:
                c = _rgb("3a2414")
            if x < 3 or x >= w - 3 or y < 3 or y >= h - 3 or abs(x - y) < 2 or abs(x - (w - 1 - y)) < 2:
                c = _scale(_rgb("5e3e22"), 1.0 + 0.05 * math.sin(x + y))
            if (x in (1, w - 2)) and (y in (1, h - 2)):
                c = _rgb("2c2c30")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _chain(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            link = (x // 4 + y // 4) % 2
            c = _rgb("2e2a28") if link else _rgb("4a423a")
            if (x % 4 == 0) or (y % 4 == 0):
                c = _rgb("1a1816")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _checker(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("4a4c50"), 1.0 - 0.05 * ((x // 16 + y // 16) % 2))
            if ((x + 2 * (y // 4)) % 8 in (0, 1)) and (y % 4 in (1, 2)) and ((x // 4 + y // 4) % 2 == 0):
                c = _rgb("6e7076")
            if x % 32 == 31 or y % 32 == 31:
                c = _rgb("232427")
            if (x % 32 in (2, 29)) and (y % 32 in (2, 29)):
                c = _rgb("8a7a5a")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _wall_iron(px, region, rng):
    """Riveted iron wall plates (two rows of plates a block high) with a copper rail at hand height."""
    u, v, w, h = region
    _plates(px, region, ("44464b", "4a4c52", "3f4146"), rng, seam="1e1f22", rivet="8a7458", rust=0.15)
    for x in range(w):
        for y in (22, 23, 24):
            px[u + x, v + y] = _jitter(_scale(_rgb("b0623a"), 1.15 if y == 22 else 0.8 if y == 24 else 1.0), rng, 3) + (255,)


def _cabin_wall(px, region, rng):
    u, v, w, h = region
    _planks(px, region, ("3a2414", "40281a", "362212"), "1a0e06", rng, plank_h=8, joints=0)
    for y in range(h):
        for x in range(w):
            if y in (40, 41):
                px[u + x, v + y] = _jitter(_rgb(BRASS[2]), rng, 4) + (255,)
            elif y > 41 and x % 16 in (0, 15):
                px[u + x, v + y] = _jitter(_rgb("26180c"), rng, 3) + (255,)


def _gear_face(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - w / 2 + 0.5, y - h / 2 + 0.5) / (w / 2)
            c = _mix(_rgb(BRASS[3]), _rgb(BRASS[1]), min(1.0, d))
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def gear_mask(size, teeth=10, spokes=8):
    """Mask (0/255) of a gold gear wheel in a size x size square: square teeth round a rim, spokes, a hub
    with its axle hole (the emblem of the main sail and of the Arsenal)."""
    img = Image.new("L", (size, size), 0)
    px = img.load()
    c = (size - 1) / 2
    R = size / 2
    for y in range(size):
        for x in range(size):
            dx, dy = x - c, y - c
            r = math.hypot(dx, dy) / R
            a = math.atan2(dy, dx)
            on = False
            if 0.7 <= r <= 0.86:
                on = True     # the rim
            elif 0.86 < r <= 1.0:
                ph = (a / (2 * math.pi) * teeth) % 1.0
                on = 0.18 < ph < 0.62   # the teeth
            elif 0.17 <= r <= 0.31:
                on = True     # the hub
            elif 0.31 < r < 0.7:
                for k in range(spokes):
                    sa = 2 * math.pi * k / spokes
                    if abs(math.sin(a - sa)) * r < 0.055 and math.cos(a - sa) > 0:
                        on = True
            if on:
                px[x, y] = 255
    return img


def _black_sail(px, region, cols, rows, rng, stripe=0.31, emblem=None):
    """Black blocky sail: a tone per cloth block, lighter in the belly, darker at the leeches; a gold
    border on the fore leech (right, seen from starboard) and along the foot from a vertical gold stripe
    at `stripe` of the width; emblem = (centre u, centre v, diameter) fractions of a gold gear."""
    u, v, w, h = region
    tones = [_rgb(c) for c in ("292625", "2f2b2a", "34302f", "232020", "393433")]
    cw, ch = w / cols, h / rows
    tone = []
    for r in range(rows):
        row = []
        for c in range(cols):
            dx = abs((c + 0.5) / cols - 0.5) * 2
            dy = (r + 0.5) / rows
            k = 1.0 + 0.12 * (1 - dx * dx) - 0.12 * dx * dx - 0.05 * dy
            row.append(_scale(rng.choice(tones), k * rng.uniform(0.96, 1.04)))
        tone.append(row)
    mask = None
    cols_map = SAIL_COLUMNS.get(next((k for k, r in SAIL_REGIONS.items() if r == region), None))
    if emblem:
        eu, ev, ed = emblem
        size = int(ed * w)
        mask = gear_mask(size).load()
        mx0, my0 = int(eu * w - size / 2), int(ev * h - size / 2)
        if cols_map:
            # the hanging sail: a texel (x, y) of column c lies at the world height top_c - y / h * (top_c - bot_c); the
            # emblem is centred at (eu, ev) of its column and painted round in the world
            spans, width = cols_map
            ce = min(cols - 1, int(eu * cols))
            te, be = spans[ce]
            wc = te - ev * (te - be)
            rad = ed * width / 2

            def emblem_at(x, y):
                c_ = min(cols - 1, int(x / cw))
                tc, bc = spans[c_]
                wx = (x + 0.5) / w * width - eu * width
                wy = wc - (tc - (y + 0.5) / h * (tc - bc))
                mx, my = int((wx / (2 * rad) + 0.5) * size), int((wy / (2 * rad) + 0.5) * size)
                return mx, my
    gold_dark, gold, gold_hi = (_rgb(c) for c in GOLD)
    bw = max(3, int(cw * 0.75))
    sx = int(stripe * w)
    for y in range(h):
        r = min(rows - 1, int(y / ch))
        for x in range(w):
            c_ = min(cols - 1, int(x / cw))
            col = tone[r][c_]
            lx, ly = x - c_ * cw, y - r * ch
            if lx < 1 or ly < 1:
                col = _scale(col, 1.25)
            elif lx > cw - 2 or ly > ch - 2:
                col = _scale(col, 0.7)
            gold_px = (x >= w - bw) or (y >= h - bw and x >= sx) or (sx <= x < sx + bw)
            if gold_px:
                g = gold
                if (x >= w - bw and x == w - bw) or (y == h - bw and x >= sx) or x == sx:
                    g = gold_hi
                if lx > cw - 2 or ly > ch - 2:
                    g = gold_dark
                col = g
            if mask is not None:
                mx, my = emblem_at(x, y) if cols_map else (x - mx0, y - my0)
                if 0 <= mx < size and 0 <= my < size and mask[mx, my]:
                    if cols_map:
                        nb = [emblem_at(x + ox, y + oy) for ox, oy in ((1, 0), (0, 1))]
                    else:
                        nb = [(mx + ox, my + oy) for ox, oy in ((1, 0), (0, 1))]
                    edge = any(not (0 <= a < size and 0 <= b < size and mask[a, b]) for a, b in nb)
                    col = gold_dark if edge else _mix(gold_hi, gold, min(1.0, my / size * 1.3))
            px[u + x, v + y] = _jitter(col, rng, 3) + (255,)


def make_texture(path):
    rng = random.Random(4721)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    R = REGIONS
    # charcoal iron, a warm black (the reference's plates are black-brown, not blue-grey)
    _plates(px, R["plate_a"], ("2d2b2b", "32302f", "373433", "2a2828", "302d2d", "353130"), rng)
    _plates(px, R["plate_b"], ("33302f", "383534", "3d3a38", "302d2d", "363332"), rng)
    _plates(px, R["plate_c"], ("242222", "282625", "2b2928", "212020"), rng, rust=0.2)
    # copper: the deep red-brown copper of the reference (not a new-penny salmon)
    _band(px, R["copper"], ("5a240e", "a04c26", "d88248"), rng, rivet="eaa458")
    _band(px, R["copper2"], ("60270e", "aa5528", "e08c4e"), rng, rivet="eaa458")
    # brass: the bronze-orange of the reference's gears and trims (phase 4; it was a pale yellow gold)
    polished_metal(img, R["brass"], [(0.0, _rgb(BRASS[0])), (0.5, _rgb(BRASS[1])), (0.85, _rgb(BRASS[2])), (1.0, _rgb(BRASS[3]))], rng)
    _band(px, R["brass_band"], ("5e3010", "a65e26", "dc923e"), rng, rivet="f4c272")
    # the roof edges of the engine house and of the deckhouse: a dark riveted beam with brass bolts (the reference
    # shows no grey anywhere: black iron, dark wood, copper and brass)
    _band(px, R["stone"], ("1c1714", "3a2e26", "5a4636"), rng, rivet="d6a848")
    _band(px, R["iron_band"], ("18191b", "3a3b40", "54565c"), rng, rivet="8a7458")
    _planks(px, R["wood_dark"], ("3a2616", "34220f", "40291a"), "160c04", rng, plank_h=8, joints=2)
    _planks(px, R["wood_mid"], ("5e3e22", "56381e", "664428"), "26180c", rng, plank_h=8, joints=2)
    _planks(px, R["deck"], ("5a3e26", "523822", "62442a", "4c3420"), "22160c", rng, plank_h=8, joints=3)
    u, v, w, h = R["lantern"]
    paint_lamp_glass(px, u, v, w, h)
    ct._rope(px, R["rope"], "8a7250", "5a4830", rng)
    _fill(px, R["iron"], "3a3b3f", rng, 6)
    _fill(px, R["bronze"], "a8642a", rng, 8)
    _fill(px, R["glow"], "ffc060", rng, 4)
    _fill(px, R["end_grain"], "6a4a2a", rng, 10)
    _chain(px, R["chain"], rng)
    _fill(px, R["glass"], "a8c4cc", rng, 4)
    _glow_window(px, R["glow_window"], rng)
    ct._window(px, R["window_in"], rng, lit=False)
    ct._door(px, R["door"], rng)
    ct._grating(px, R["grating"], rng)
    _funnel(px, R["funnel"], rng)
    _dome(px, R["dome"], rng)
    _dome(px, R["dome_drum"], rng, tones=("4e2a1c", "573020", "48271a", "5c3322"), edge="7e4426", seam="1e0e08", rivet="c8843e", verdigris=0.02)
    _planks(px, R["mast"], ("3e2a18", "46301c", "382614"), "1c1008", rng, plank_h=16, joints=0, grain=0.09)
    _rail(px, R["rail"], rng)
    _crate(px, R["crate"], rng)
    _pipe(px, R["pipe"], rng)
    _fill(px, R["iron_dark"], "1e1f22", rng, 4)
    _fill(px, R["wood_light"], "8a6440", rng, 6)
    _planks(px, R["dark_wood"], ("2e1e10", "34220f"), "140a04", rng, plank_h=8, joints=1)
    _fill(px, R["red_paint"], "8e2420", rng, 6)
    _fill(px, R["white_paint"], "e4dccc", rng, 5)
    _fill(px, R["navy"], "1c2444", rng, 4)
    ct._compass(px, R["compass"], rng)
    ct._weave(px, R["cloth_roll"], rng, "2e2e33", "222226")
    _boiler_front(px, R["boiler_front"], rng)
    _plates(px, R["boiler"], ("3a3b40", "404147", "36373c"), rng, seam="1a1b1e", rivet="9a8460", rust=0.1)
    _gear_face(px, R["gauge"], rng)
    _gear_face(px, R["gear_face"], rng)
    ct._chart(px, R["chart"], rng)
    ct._books(px, R["books"], rng)
    _fill(px, R["bedding"], "6e2a24", rng, 8)
    _fill(px, R["linen"], "e6dfcc", rng, 4)
    ct._weave(px, R["sack"], rng, "a98b5e", "8e7349")
    ct._weave(px, R["canvas"], rng, "ab9a76", "9c8a66", period=1)
    _blocks(px, R["coal"], ("1a1a1c", "242426", "2e2e30"), "0e0e10", rng, bw=4, bh=4)
    ct._painting(px, R["painting"], rng)
    _fill(px, R["fire"], "ff9a30", rng, 30)
    polished_metal(img, R["plaque"], [(0.0, _rgb(BRASS[0])), (0.6, _rgb(BRASS[2])), (1.0, _rgb(BRASS[3]))], rng)
    u, v, w, h = R["flag"]
    for y in range(h):
        for x in range(w):
            c = _rgb(GOLD[1]) if (y < 2 or y >= h - 2 or x < 2) else _scale(_rgb("2a2a2e"), 1.0 + 0.05 * math.sin(x * 0.6))
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    _wall_iron(px, R["wall_iron"], rng)
    _checker(px, R["floor_iron"], rng)
    ct._ceil(px, R["ceil"], rng)
    _planks(px, R["floor"], ("5e3e22", "56381e", "664428", "4e3420"), "26180c", rng, plank_h=8, joints=2)
    _cabin_wall(px, R["wall_wood"], rng)
    _planks(px, R["hold_floor"], ("4e3a26", "463422", "56402a"), "1e140a", rng, plank_h=8, joints=3, worn=0.04, worn_col="2a2a2a")
    _plates(px, R["hold_wall"], ("3a3b3f", "404146", "35363a"), rng, seam="1a1b1d", rivet="7a6448", rust=0.2)
    _planks(px, R["crew_wall"], ("4a3220", "52381f", "442e1c"), "1e140a", rng, plank_h=8, joints=2)
    ct._carpet(px, R["carpet"], rng, border="c9973a", field="5a1a16", centre="3a0e0c")
    ct._rug(px, R["rug"], rng)
    ct._boat(px, R["boat"], rng)
    _blocks(px, R["ham"], ("9a4632", "8a3c2a"), "5a2418", rng, bw=8, bh=4)
    _blocks(px, R["wall_stone"], ("5e6065", "686a6f", "55575c"), "2e2f32", rng, bw=16, bh=8)
    _copy_interior_regions(img)
    img.save(path)
    return img


def _copy_interior_regions(img):
    """Pastes the furniture regions of the Sky Leviathan's interior atlas (painted by tools/leviathan_texture.py into
    a temporary file) at their places in this atlas (IN_COPIED)."""
    import os
    import shutil
    import tempfile
    import leviathan_texture as lt
    tmp = tempfile.mkdtemp(prefix="gear_steam_tex_")
    try:
        src = lt.make_interior_texture(os.path.join(tmp, "interior.png"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for name, (u, v, w, h) in IN_COPIED.items():
        su, sv, sw, sh = lt.REGIONS_IN[name]
        assert (sw, sh) == (w, h), name
        img.paste(src.crop((su, sv, su + sw, sv + sh)), (u, v))


def make_sail_texture(path):
    rng = random.Random(9187)
    img = Image.new("RGBA", (SAIL_SIZE, SAIL_SIZE), (0, 0, 0, 0))
    px = img.load()
    _black_sail(px, SAIL_REGIONS["main_sail"], *SAIL_CELLS["main_sail"], rng, stripe=0.34, emblem=(0.67, 0.44, 0.33))
    _black_sail(px, SAIL_REGIONS["mizzen_sail"], *SAIL_CELLS["mizzen_sail"], rng, stripe=0.25)
    img.save(path)
    return img


def make_item_icon(path):
    """16x16 icon: the black hull with its copper and brass bands, the funnel, the copper dome, a black
    sail with a gold gear."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    black, copper, brass = _rgb("2c2d31"), _rgb("b0623a"), _rgb("cc8a3a")
    sail, mast, glow = _rgb("2a2a2e"), _rgb("4a3220"), _rgb("ffb040")
    for x in range(1, 15):
        for y in range(10, 15):
            if y == 14 and (x < 3 or x > 13):
                continue
            c = copper if y == 10 else (brass if y == 12 and x > 6 else black)
            px[x, y] = c + (255,)
    px[5, 11] = glow + (255,)
    px[8, 11] = glow + (255,)
    for y in range(4, 10):
        px[4, y] = black + (255,)
        px[5, y] = black + (255,)
    px[4, 6] = brass + (255,)
    px[5, 6] = brass + (255,)
    for x, y in ((7, 8), (8, 8), (9, 8), (7, 7), (8, 7), (9, 7), (8, 6)):
        px[x, y] = copper + (255,)
    for y in range(1, 10):
        px[12, y] = mast + (255,)
    for y in range(2, 8):
        for x in range(10, 15):
            if x != 12:
                px[x, y] = sail + (255,)
    for y in range(2, 8):
        px[14, y] = brass + (255,)
    px[11, 4] = brass + (255,)
    px[13, 5] = brass + (255,)
    px[0, 9] = brass + (255,)
    px[15, 9] = brass + (255,)
    img.save(path)


if __name__ == "__main__":
    import os
    out = os.environ.get("OUT", "/tmp/claude-0/agent_gear_steam")
    os.makedirs(out, exist_ok=True)
    make_texture(os.path.join(out, "gear_steamship.png"))
    make_sail_texture(os.path.join(out, "gear_steamship_sails.png"))
    make_item_icon(os.path.join(out, "icon.png"))
    print("ok")
