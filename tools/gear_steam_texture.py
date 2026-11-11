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

import numpy as np
from PIL import Image

from galley_texture import _jitter, _rgb, paint_lamp_glass, polished_metal
import corsair_texture as ct

# visual upgrade (1.27.1): the atlases are painted at 32 px a block (1024 x 1024) instead of 16 (512 x 512). The regions
# below are laid out in "layout units" (the old 512 atlas, 16 a block); REGIONS / SAIL_REGIONS are the same rectangles
# in texels (x K), and the model generator doubles the UV density of its faces (tools/generate_gear_steam.py).
K = 2
SIZE = 512 * K
SAIL_SIZE = 512 * K
BLK = 16 * K     # texels a block

REGIONS = {
    # hull and upper works
    "plate_a":     (0, 288, 128, 64),   # iron plate mosaic (a plate a block, 8 x 4 plates), the hull sides
    "plate_b":     (128, 288, 128, 64), # the same, a little lighter (castle walls)
    "plate_c":     (256, 288, 128, 64), # the same, darker (the bottom, under the water)
    "dome_gore":   (384, 288, 32, 16),  # one plate of the dome's cap, stretched on each plate: a gore with rivets on its seams
    "gear_bevel":  (416, 288, 16, 16),  # a bevelled brass bar, stretched on each piece of a gear wheel (lit and shadowed edges)
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

# layout units (the old 512 atlas) -> texels
LAYOUT, SAIL_LAYOUT = REGIONS, SAIL_REGIONS
REGIONS = {k: tuple(K * c for c in r) for k, r in LAYOUT.items()}
SAIL_REGIONS = {k: tuple(K * c for c in r) for k, r in SAIL_LAYOUT.items()}

_mix, _scale, _planks, _blocks, _fill = ct._mix, ct._scale, ct._planks, ct._blocks, ct._fill
# the gold of the sails: a warm bronze-gold, as the orange gold of the reference (not a pale lemon yellow)
GOLD = ("7a3e10", "d8902c", "ffc860")
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


def gear_mask(size, teeth=10, spokes=8, rim=(0.7, 0.86), hub=(0.17, 0.31), spoke=0.055):
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
            if rim[0] <= r <= rim[1]:
                on = True     # the rim
            elif rim[1] < r <= 1.0:
                ph = (a / (2 * math.pi) * teeth) % 1.0
                on = 0.18 < ph < 0.62   # the teeth
            elif hub[0] <= r <= hub[1]:
                on = True     # the hub
            elif hub[1] < r < rim[0]:
                for k in range(spokes):
                    sa = 2 * math.pi * k / spokes
                    if abs(math.sin(a - sa)) * r < spoke and math.cos(a - sa) > 0:
                        on = True
            if on:
                px[x, y] = 255
    return img


# ---------------------------------------------------------------- HD painters (1.27.1: 32 px a block, baked light)
# Minecraft lights entities flatly (a face is only darker or lighter by its direction), so the light and the wear are
# painted in: every block bevelled (lit upper and left edges, shadowed lower and right ones, a dark seam), a tone per
# plate or plank, soft mottling, rivets lit from the top left with a small cast shadow, polished metals with their
# reflection and shadow bands, glowing windows in deep orange (the game also darkens their sides).
def _c(h):
    return np.array(_rgb(h), float)


def _nrs(rng):
    return np.random.RandomState(rng.randrange(1 << 30))


def _noise(w, h, cell, rng, cell_y=None):
    """Smooth value noise in [-1, 1], features about `cell` texels wide (cell_y tall)."""
    cy = cell if cell_y is None else cell_y
    g = _nrs(rng).uniform(-1, 1, (int(h / cy) + 2, int(w / cell) + 2))
    xs, ys = np.arange(w) / cell, np.arange(h) / cy
    x0, y0 = xs.astype(int), ys.astype(int)
    fx, fy = xs - x0, ys - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    top = g[y0][:, x0] * (1 - fx) + g[y0][:, x0 + 1] * fx
    bot = g[y0 + 1][:, x0] * (1 - fx) + g[y0 + 1][:, x0 + 1] * fx
    return top * (1 - fy)[:, None] + bot * fy[:, None]


def _grain(w, h, rng, amp):
    return _nrs(rng).uniform(-amp, amp, (h, w))


def _ramp_np(stops, t):
    """Colour ramp over evenly spaced stops for an array t in [0, 1] -> (..., 3)."""
    cs = np.array([_c(s) if isinstance(s, str) else np.asarray(s, float) for s in stops])
    t = np.clip(t, 0, 1) * (len(cs) - 1)
    i = np.minimum(len(cs) - 2, t.astype(int))
    f = (t - i)[..., None]
    return cs[i] * (1 - f) + cs[i + 1] * f


def _put(a, region, col):
    u, v, w, h = region
    a[v:v + h, u:u + w, :3] = np.clip(col, 0, 255)
    a[v:v + h, u:u + w, 3] = 255


def _rivet(img, cx, cy, r, base, shadow=0.5, hi=None, lo=None):
    """A round rivet head lit from the top left, drawn on img (h, w, 3) in place: a lit cap with a bright spot, a dark
    rim on its lower right, a small cast shadow below right."""
    h, w = img.shape[:2]
    base = np.asarray(base, float)
    hi = np.minimum(255, base * 1.6 + 36) if hi is None else np.asarray(hi, float)
    lo = base * 0.42 if lo is None else np.asarray(lo, float)
    for y in range(int(cy - r - 1), int(cy + r + 3)):
        for x in range(int(cx - r - 1), int(cx + r + 3)):
            if not (0 <= x < w and 0 <= y < h):
                continue
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if d <= r:
                lt = -(dx + dy) / (1.414 * r)
                c = base * (1.0 + 0.3 * lt)
                if lt > 0.3 and d < r * 0.75:
                    c = hi
                elif d > r - 0.95 and lt < -0.1:
                    c = lo
                img[y, x] = c
            elif d <= r + 1.6 and dx + dy > 0.5 * r:
                img[y, x] = img[y, x] * shadow


def _bevel(block_w, block_h, light=(3.0, 2.5), dark=(4.0, 3.0), kl=(0.85, 0.45), kd=(0.6, 0.4)):
    """Light and shadow weights of a bevelled block (block_h, block_w): lit upper / left edges, dark lower / right."""
    ys, xs = np.mgrid[0:block_h, 0:block_w].astype(float)
    hl = np.clip(np.clip(1 - (ys - 1) / light[0], 0, 1) * kl[0] + np.clip(1 - (xs - 1) / light[1], 0, 1) * kl[1], 0, 1)
    sh = np.clip(np.clip(1 - (block_h - 2 - ys) / dark[0], 0, 1) * kd[0] + np.clip(1 - (block_w - 2 - xs) / dark[1], 0, 1) * kd[1], 0, 0.78)
    return hl, sh, ys


def _plates_hd(a, region, tones, rng, rivet="503e30", rust=0.14, seam="0e0a08", lit="140c08", lit_k=1.65, rivets="corners",
               brown=0.3, block=BLK, scratches=0, rust_col="6e3c1e", rivet_hi=(1.45, 16), block_h=None, rust_len=(6, 18)):
    """Riveted plates a block each (block wide, block_h tall) with baked light: a tone per plate (some browner), soft
    mottling, each plate a little lighter at its top, a lit bevel on the upper and left edges, a shadowed bevel on the
    lower and right edges, a dark seam, rivet heads (four corners, or columns along the vertical seams), light scratches
    and rust runs."""
    u, v, w, h = region
    bh = block_h or block
    out = np.zeros((h, w, 3))
    mott = _noise(w, h, 7, rng) * 0.07 + _noise(w, h, 2.5, rng) * 0.035 + _grain(w, h, rng, 0.025)
    hl, sh, ys = _bevel(block, bh, light=(5.0, 4.0), dark=(6.0, 5.0), kl=(0.9, 0.5), kd=(0.65, 0.45))
    grad = 1.09 - 0.2 * ys / bh
    seam, litc = _c(seam), _c(lit)
    tones = [_c(t) for t in tones]
    r = rng
    for by in range(0, h, bh):
        for bx in range(0, w, block):
            base = tones[r.randrange(len(tones))] * r.uniform(0.8, 1.22)
            if r.random() < brown:
                base = base * 0.82 + _c("4a3020") * 0.18 * r.uniform(0.6, 1.4)
            m = mott[by:by + bh, bx:bx + block]
            col = base[None, None, :] * (grad * (1 + m))[..., None]
            col = col * (1 - hl[..., None]) + (col * lit_k + litc) * hl[..., None]
            col = col * (1 - sh[..., None])
            # a 2 px seam (1 px vanished at a distance in game: the textures are not mipmapped)
            col[bh - 1, :] = seam
            col[:, block - 1] = seam
            col[bh - 2, :] = seam * 0.6 + col[bh - 2, :] * 0.4
            col[:, block - 2] = seam * 0.6 + col[:, block - 2] * 0.4
            for _ in range(r.randrange(0, scratches + 1)):
                x0, y0 = r.uniform(4, block - 6), r.uniform(5, bh - 6)
                ang = r.uniform(-0.6, 0.6) + (math.pi / 2 if r.random() < 0.3 else 0)
                ln = r.uniform(3, 8)
                for t in np.linspace(0, ln, int(ln * 2)):
                    x, y = int(x0 + t * math.cos(ang)), int(y0 + t * math.sin(ang))
                    if 1 <= x < block - 2 and 1 <= y < bh - 2:
                        col[y, x] = col[y, x] * 1.3 + 7
            if r.random() < rust:
                x0 = r.choice((5, block - 6, r.randrange(6, block - 6)))
                y0 = 7 if x0 in (5, block - 6) else r.randrange(3, 10)
                ln = r.randrange(*rust_len)
                rc = _c(rust_col)
                for t in range(ln):
                    y = y0 + t
                    if y >= bh - 2:
                        break
                    k = 0.6 * (1 - t / ln)
                    for xx in (x0, x0 + (1 if t % 3 else 0), x0 - (1 if t < 3 else 0)):
                        if 1 <= xx < block - 2:
                            col[y, xx] = col[y, xx] * (1 - k) + rc * k
            out[by:by + bh, bx:bx + block] = col
            tile = out[by:by + bh, bx:bx + block]
            rb = _c(rivet) * r.uniform(0.9, 1.1)
            rh = np.minimum(255, rb * rivet_hi[0] + rivet_hi[1])      # soft highlights: the rivets read as relief, not as sparkles
            if rivets == "corners":
                for cx, cy in ((5, 5), (block - 7, 5), (5, bh - 7), (block - 7, bh - 7)):
                    _rivet(tile, cx + 0.5, cy + 0.5, 2.0, rb, shadow=0.6, hi=rh)
            elif rivets == "columns":
                for cy in range(4, bh - 4, 7):
                    _rivet(tile, 3.5, cy + 0.5, 1.5, rb, shadow=0.6, hi=rh)
                    _rivet(tile, block - 5.5, cy + 0.5, 1.5, rb, shadow=0.6, hi=rh)
            elif rivets == "edges":
                # a row of rivets along the upper seam and a column along the left seam (the plates overlap)
                for cx in range(6, block - 4, 8):
                    _rivet(tile, cx + 0.5, 4.5, 1.7, rb, shadow=0.6, hi=rh)
                for cy in range(12, bh - 4, 8):
                    _rivet(tile, 4.5, cy + 0.5, 1.7, rb, shadow=0.6, hi=rh)
    _put(a, region, out)


# ---------------------------------------------------------------- the rooms (1.28.1: painted at 32 px a block too)
# The room walls sample their region 4 blocks wide (MAX_TILE cells of generate_gear_steam.surfaces) and stretched over the
# room's height (the top row of texels is the ceiling line, the bottom row the floor line); the floors tile 4 x 4 blocks.
def _band_rows(col, y0, y1, stops, rng, rivet=None, seg=BLK, refl=0.3):
    """A horizontal metal band painted over rows y0..y1 of col (h, w, 3): a rail, a skirting, a cornice."""
    h, w = col.shape[:2]
    tmp = np.zeros((y1 - y0, w, 4))
    _band_hd(tmp, (0, 0, w, y1 - y0), stops, rng, rivet=rivet, seg=seg, refl=refl)
    col[y0:y1] = tmp[..., :3]


def _wall_iron_hd(a, region, rng, tones, rail=None, skirting=True, cornice=True, rust=0.12, rust_col="6e3c1e", rivets="edges",
                  bilge=0.0, lit="100c0a", lit_k=1.55, rivet="4e4238", brown=0.18, block_h=BLK):
    """A room wall of riveted iron plates (dark warm iron, a lit bevel on each plate, rivet rows along the laps, a few rust
    runs): a dark cornice along the ceiling, a riveted skirting along the floor, a copper hand rail (rail = (row0, row1)),
    and, for the hold, a darker, wetter bilge band at the foot (bilge = fraction of the height)."""
    u, v, w, h = region
    _plates_hd(a, region, tones, rng, rivet=rivet, rust=rust, rust_col=rust_col, lit=lit, lit_k=lit_k, rivets=rivets, brown=brown,
               block_h=block_h, seam="0c0a09", rivet_hi=(1.35, 10))
    col = a[v:v + h, u:u + w, :3]
    if bilge:
        t = np.clip((np.arange(h) / h - (1 - bilge)) / bilge, 0, 1)[:, None, None]
        col[:] = col * (1 - 0.45 * t) + _c("1a1612")[None, None, :] * 0.2 * t
    if cornice:
        _band_rows(col, 0, 5, ("121010", "3a3432", "66605c"), rng, rivet=None, refl=0.2)
    if skirting:
        _band_rows(col, h - 7, h, ("0e0c0b", "2e2a28", "56504c"), rng, rivet="5a4e42", refl=0.18)
    if rail:
        r0, r1 = rail
        _band_rows(col, r0, r1, ("4a1c08", "c45c26", "ffb06a"), rng, rivet="d89050", refl=0.4)
        col[r1] = col[r1] * 0.55     # the rail's shadow on the plates
        col[min(h - 1, r1 + 1)] = col[min(h - 1, r1 + 1)] * 0.8
    _put(a, region, col)


def _checker_hd(a, region, rng, base="2e2b2a", lozenge="4a4642", dark="171514", block=BLK):
    """Dark checker plate (the engine room floor): raised lozenges lit from the top left on a dark warm iron sheet, the
    sheets a block each with a dark joint and a rivet in each corner, worn lighter down the middle of the room."""
    u, v, w, h = region
    ys, xs = np.mgrid[0:h, 0:w].astype(float)
    col = np.zeros((h, w, 3)) + _c(base)[None, None, :] * (1 + 0.08 * _noise(w, h, 9, rng) + _grain(w, h, rng, 0.03))[..., None]
    # lozenges on a staggered grid of 16 texels (two a block: chunky enough to read from eye height)
    period = 16
    cx = (xs % period) - period / 2 + 0.5
    cy = (ys % period) - period / 2 + 0.5
    stag = ((ys // period) % 2) == 1
    cx = np.where(stag, (xs + period / 2) % period - period / 2 + 0.5, cx)
    d = np.abs(cx) * 0.6 + np.abs(cy)
    loz = d < 4.4
    lit_ = (d < 4.4) & ((cx * 0.6 + cy) < -1.2)
    sh = (d < 4.4) & ((cx * 0.6 + cy) > 1.6)
    lc = _c(lozenge)[None, None, :] * (1 + 0.1 * _noise(w, h, 12, rng))[..., None]
    col = np.where(loz[..., None], lc, col)
    col = np.where(lit_[..., None], np.minimum(255, lc * 1.28 + 10), col)
    col = np.where(sh[..., None], lc * 0.62, col)
    # plate joints every block, a rivet in each corner
    for k in range(0, w, block):
        col[:, k] = _c(dark)
        col[:, min(w - 1, k + 1)] = col[:, min(w - 1, k + 1)] * 0.6
        col[:, (k - 1) % w] = col[:, (k - 1) % w] * 0.75
    for k in range(0, h, block):
        col[k, :] = _c(dark)
        col[min(h - 1, k + 1), :] = col[min(h - 1, k + 1), :] * 0.6
    for by in range(0, h, block):
        for bx in range(0, w, block):
            for cx_, cy_ in ((4.5, 4.5), (block - 3.5, 4.5), (4.5, block - 3.5), (block - 3.5, block - 3.5)):
                _rivet(col, bx + cx_, by + cy_, 1.8, _c("5a5048"), shadow=0.65, hi=_c("8a7e72"))
    _put(a, region, col)


def _boiler_front_hd(a, region, rng):
    """The firebox door (drawn full bright): a riveted iron plate round a bevelled brass frame, and behind the grate bars a
    bed of white-hot coals fading to orange and deep red at the edges, flames licking up between the bars."""
    u, v, w, h = region
    ys, xs = np.mgrid[0:h, 0:w].astype(float) + 0.5
    col = np.zeros((h, w, 3)) + _c("2a2624")[None, None, :] * (1 + 0.06 * _noise(w, h, 8, rng) + _grain(w, h, rng, 0.03))[..., None]
    fx0, fx1, fy0, fy1 = w * 0.09, w * 0.91, h * 0.14, h * 0.9      # the brass frame's outer edge
    fw = w * 0.07
    inner = (xs > fx0 + fw) & (xs < fx1 - fw) & (ys > fy0 + fw) & (ys < fy1 - fw)
    frame = (xs > fx0) & (xs < fx1) & (ys > fy0) & (ys < fy1) & ~inner
    # the coals: hottest low in the middle, flames as bright tongues rising
    nx = (xs - w / 2) / ((fx1 - fx0) / 2 - fw)
    ny = (ys - (fy0 + fw + (fy1 - fw - fy0 - fw) * 0.72)) / ((fy1 - fy0) / 2 - fw)
    d = np.hypot(nx * 1.05, ny * 1.3)
    d = d - 0.18 * np.clip(_noise(w, h, 5, rng), -1, 1) - 0.12 * np.clip(np.sin(xs * 1.4 + 2.5 * _noise(w, h, 6, rng)) * (0.5 - ny), 0, 1)
    glow = _ramp_np(("fff8dc", "ffe08a", "ffb038", "ff7a1c", "d83a0c", "7a1408", "3a0c06"), np.clip(d * 0.78, 0, 1))
    bars = ((xs - fx0 - fw) % (w * 0.125)) < w * 0.045
    glow = np.where(bars[..., None], _c("1c1412") * (1 + 0.5 * np.clip(1 - d, 0, 1))[..., None], glow)
    col = np.where(inner[..., None], glow, col)
    ft = 0.55 + 0.35 * np.clip(1 - (ys - fy0) / fw, 0, 1) + 0.25 * np.clip(1 - (xs - fx0) / fw, 0, 1) - 0.3 * np.clip(1 - (fy1 - ys) / fw, 0, 1) \
        - 0.2 * np.clip(1 - (fx1 - xs) / fw, 0, 1)
    col = np.where(frame[..., None], _ramp_np(BRASS, ft + _grain(w, h, rng, 0.04)), col)
    # the plate's rivets round the door
    for cx_ in np.linspace(w * 0.04, w * 0.96, 7):
        _rivet(col, cx_, h * 0.07, 1.8, _c("564a40"), shadow=0.6, hi=_c("8a7a6a"))
        _rivet(col, cx_, h * 0.955, 1.8, _c("564a40"), shadow=0.6, hi=_c("8a7a6a"))
    for cy_ in np.linspace(h * 0.25, h * 0.8, 3):
        _rivet(col, w * 0.04, cy_, 1.8, _c("564a40"), shadow=0.6, hi=_c("8a7a6a"))
        _rivet(col, w * 0.96, cy_, 1.8, _c("564a40"), shadow=0.6, hi=_c("8a7a6a"))
    _put(a, region, col)


def _panel_wall_hd(a, region, tones, seam, rng, rail=None, rail_stops=None, wainscot=None, plank=BLK // 2, grain=0.12, joints=2):
    """A wooden room wall (planks a block long with baked light), a brass or dark rail at hand height, a darker wainscot
    with vertical boards below it."""
    u, v, w, h = region
    _planks_hd(a, region, tones, seam, rng, plank=plank, joints=joints, grain=grain)
    col = a[v:v + h, u:u + w, :3]
    if wainscot:
        # vertical boards: planks painted along u in a (w tall, h - y0 wide) buffer, then transposed
        y0 = wainscot
        tmp = np.zeros((w, h - y0, 4))
        _planks_hd(tmp, (0, 0, h - y0, w), tuple(tones), seam, rng, plank=BLK // 2, joints=0, nails=False, grain=grain * 0.8)
        col[y0:h] = tmp[..., :3].transpose(1, 0, 2) * 0.72
        col[h - 1] = _c(seam) * 0.5
    if rail:
        r0, r1 = rail
        _band_rows(col, r0, r1, rail_stops or ("3a2010", "a8622a", "eeae58"), rng, rivet=None, refl=0.35)
        col[r1] = col[r1] * 0.55
    _put(a, region, col)


def _paint_rooms_hd(a, rng):
    """The rooms again at 32 px a block: dark warm riveted iron for the engine room and the hold (they read as a flat
    blue-grey in the 1.28.0 captures), dark checker plate, a hotter firebox, planks and panelling with baked light."""
    R = REGIONS
    u, v, w, h = R["wall_iron"]
    # the engine room (3.5 high): plates of a block, a copper hand rail a block above the floor, cornice and skirting
    rail = (int(h * (1 - 1.12 / 3.5)), int(h * (1 - 1.12 / 3.5)) + 6)
    _wall_iron_hd(a, R["wall_iron"], rng, ("3a3533", "36312f", "403a37", "332e2c", "3c3835", "443e3a", "35353a", "3a3b40"), rail=rail,
                  rust=0.14, block_h=h // 4)
    u, v, w, h = R["hold_wall"]
    # the hold (3 high, under the waterline): the same iron, rustier, a dark wet bilge band at the foot
    _wall_iron_hd(a, R["hold_wall"], rng, ("34302e", "302c2a", "3a3532", "2e2a28", "363230", "3e3834"), rail=None, rust=0.3,
                  rust_col="7a4420", bilge=0.3, block_h=h // 4, brown=0.3)
    _checker_hd(a, R["floor_iron"], rng)
    _boiler_front_hd(a, R["boiler_front"], rng)
    # the boiler shell: riveted iron plates (rivet columns), a little browner than the walls
    _plates_hd(a, R["boiler"], ("3a3230", "342c2a", "403734", "2e2826"), rng, rivets="columns", rust=0.1, brown=0.35, lit="100c0a", lit_k=1.5,
               rivet="56483c", rivet_hi=(1.35, 10), seam="0c0a09")
    # wood: the crew quarters (planks, a dark wainscot, a bronze rail), the cabin (dark panelling, brass rail), floors, ceiling
    u, v, w, h = R["crew_wall"]
    _panel_wall_hd(a, R["crew_wall"], ("5a3e26", "4e3420", "64462c", "523822"), "1a1008", rng, rail=(int(h * 0.56), int(h * 0.56) + 4),
                   rail_stops=("2a1a0c", "6a4a2c", "a8845a"), wainscot=int(h * 0.62), grain=0.14)
    u, v, w, h = R["wall_wood"]
    _panel_wall_hd(a, R["wall_wood"], ("3c2616", "42291a", "382212", "462e1c"), "160c04", rng, rail=(int(h * 0.6), int(h * 0.6) + 4),
                   rail_stops=("4a2608", "b0702c", "f0bc62"), wainscot=int(h * 0.66), grain=0.1, joints=0, plank=BLK // 2)
    _planks_hd(a, R["floor"], ("5e3e22", "56381e", "664428", "4e3420", "5a3c24"), "22140a", rng, joints=3)
    _planks_hd(a, R["hold_floor"], ("4a3622", "42301e", "523c28", "3e2c1c"), "1a1008", rng, joints=3, grain=0.16)
    # the ceiling: dark planks (the beams are modelled)
    _planks_hd(a, R["ceil"], ("46301a", "402a16", "4c3620", "3c2814"), "1a1008", rng, joints=2, grain=0.1)
    # glowing coals (the "fire" faces of the furniture): a mottled bed from white-hot to deep red
    u, v, w, h = R["fire"]
    t = 0.35 + 0.4 * _noise(w, h, 4, rng) + 0.25 * _noise(w, h, 2, rng) + _grain(w, h, rng, 0.05)
    _put(a, R["fire"], _ramp_np(("fff4cc", "ffd060", "ff8a20", "d83a0a", "6a1406"), np.clip(t, 0, 1)))


def _band_hd(a, region, stops, rng, rivet=None, rivets=2, seg=BLK, patina=0.0, rivet_r=None, refl=0.32):
    """A riveted metal band a block a segment: rounded light across it (a lit upper edge, a bright reflection, a
    shadowed lower edge), each segment's ends bevelled with a dark joint, big rivets lit from the top left."""
    u, v, w, h = region
    dark, mid, light = (_c(s) for s in stops)
    t = (np.arange(h) + 0.5) / h
    prof = 0.8 + 0.3 * np.sin(np.pi * np.clip(t * 1.05, 0, 1)) ** 0.8
    prof = prof + refl * np.exp(-((t - 0.25) / 0.09) ** 2)
    prof = prof - 0.38 * np.clip((t - 0.78) / 0.22, 0, 1) ** 1.4
    n = _noise(w, h, 6, rng, 3) * 0.06 + _grain(w, h, rng, 0.03)
    col = mid[None, None, :] * (prof[:, None] * (1 + n))[..., None]
    col[0] = light
    col[1] = (light + col[1]) / 2
    col[h - 1] = dark * 0.7
    col[h - 2] = (dark * 0.8 + col[h - 2]) / 2
    for x in range(w):
        k = x % seg
        if k == seg - 1:
            col[:, x] = dark * 0.55
        elif k == seg - 2:
            col[:, x] *= 0.7
        elif k == seg - 3:
            col[:, x] *= 0.88
        elif k == 0:
            col[:, x] = col[:, x] * 1.25 + 8
        elif k == 1:
            col[:, x] *= 1.1
    if patina:
        pn = _noise(w, h, 4, rng)
        m = np.clip((pn - (1 - patina)) * 3, 0, 1)[..., None]
        col = col * (1 - 0.35 * m) + _c("3e5a48") * 0.35 * m * (col.mean(axis=2, keepdims=True) / 120)
    if rivet:
        rr = rivet_r or max(1.8, h * 0.09)
        rb = _c(rivet)
        for s0 in range(0, w, seg):
            for j in range(rivets):
                rc = rb * rng.uniform(0.95, 1.04)
                _rivet(col, s0 + (j + 0.5) * seg / rivets, h * 0.5, rr, rc, shadow=0.72, hi=np.minimum(255, rc * 1.16 + 8), lo=rc * 0.6)
    _put(a, region, col)


def _polished_hd(a, region, stops, rng, waves=1.0, streak=0.06, amp=1.0):
    """Polished brass: soft broad reflections on a ramp from shadow to highlight, brushed streaks along u, the lower
    edge darker and the upper edge lit."""
    u, v, w, h = region
    ys, xs = np.mgrid[0:h, 0:w].astype(float)
    t = 0.5 + amp * (0.26 * np.sin(xs * 0.09 * waves + np.sin(ys * 0.16) * 1.3) + 0.18 * np.cos(ys * 0.13 + xs * 0.035 * waves)
                     + 0.12 * np.sin((xs - ys) * 0.11))
    t = t + streak * _noise(w, h, 16, rng, 1.2) + _grain(w, h, rng, 0.02)
    t = t + 0.18 * np.exp(-((ys / h - 0.22) / 0.1) ** 2) - 0.22 * np.clip((ys / h - 0.75) / 0.25, 0, 1)
    col = _ramp_np(stops, t)
    _put(a, region, col)


def _glow_window_hd(a, region, rng):
    """A square window glowing bright orange-yellow (a hot pale core, warm orange edges), four panes behind a 6 px cross
    of dark bronze bars, in a thin bevelled brass frame: two thirds of the cell are glass, so that it reads as a lit
    square from afar (the hull's frame cubes give the heavy frame)."""
    u, v, w, h = region
    fw = max(3, w // 20)
    ys, xs = np.mgrid[0:h, 0:w].astype(float) + 0.5
    col = np.zeros((h, w, 3))
    # glass: a warm glow brighter in the lower middle (the lamp), saturated orange at the edges
    # (1.28.1: a warmer core, the panes amber rather than pale yellow from the quay)
    d = np.hypot((xs - w / 2) / (w / 2), (ys - h * 0.58) / (h / 2))
    glass = _ramp_np(("ffeaa8", "ffcc5e", "ffb040", "ff9a32", "ff8026"), np.clip(d * 0.95, 0, 1))
    col[:] = glass
    # each pane a little darker in its upper outer corner (the frame's shadow on the glass)
    px_ = (xs % (w / 2)) / (w / 2)
    py_ = (ys % (h / 2)) / (h / 2)
    col *= (1 - 0.1 * np.clip(1 - py_ * 3, 0, 1))[..., None]
    # bars: 6 texels wide, on even texel boundaries round the middle (wider than the texels a screen pixel skips at the
    # usual distance, so the cross stays whole: a thinner one broke into T shapes), one dark bronze
    bw = 3.0
    bar = (np.abs(xs - w / 2) < bw) | (np.abs(ys - h / 2) < bw)
    col = np.where(bar[..., None], _c("4e2c12"), col)
    # frame
    inner = (xs > fw) & (xs < w - fw) & (ys > fw) & (ys < h - fw)
    t = np.full((h, w), 0.55)
    t = np.where(ys < fw, 0.9 - 0.05 * ys, t)
    t = np.where(xs < fw, np.maximum(t, 0.75), t)
    t = np.where(ys > h - fw, 0.25, t)
    t = np.where(xs > w - fw, np.minimum(t, 0.35), t)
    t = t + _grain(w, h, rng, 0.04)
    frame = _ramp_np(BRASS, t)
    edge = ((xs < 1) | (ys < 1) | (xs > w - 1) | (ys > h - 1))
    frame = np.where(edge[..., None], _c(BRASS[0]) * 0.7, frame)
    rebate = (~inner) & (xs > fw - 1.0) & (xs < w - fw + 1.0) & (ys > fw - 1.0) & (ys < h - fw + 1.0)
    col = np.where(inner[..., None], col, frame)
    col = np.where(rebate[..., None], _c("2a1608"), col)
    _put(a, region, col)


def _gore_hd(a, region, rng):
    """One copper plate of the dome's cap (stretched on each plate): a soft vertical reflection (the gores of the
    reference), lit upper seam, dark lower seam, a column of brass rivets along each side seam, a little verdigris."""
    u, v, w, h = region
    ys, xs = np.mgrid[0:h, 0:w].astype(float) + 0.5
    s = xs / w
    t = 0.42 + 0.34 * np.exp(-((s - 0.38) / 0.2) ** 2) - 0.22 * np.clip((s - 0.72) / 0.28, 0, 1) - 0.15 * np.clip((0.12 - s) / 0.12, 0, 1)
    t = t + 0.05 * _noise(w, h, 5, rng) + _grain(w, h, rng, 0.025) - 0.08 * ys / h
    col = _ramp_np(("4a1e0c", "843a1a", "b4582a", "dc8044", "f8b484"), t)
    col[0:2] = col[0:2] * 1.25 + 10
    col[h - 2:] = _c("2a1006")
    col[:, w - 1] = _c("2a1006")
    col[:, 0] = col[:, 0] * 1.15
    vn = _noise(w, h, 3, rng)
    m = np.clip((vn - 0.55) * 2.5, 0, 1)[..., None]
    col = col * (1 - 0.45 * m) + _c("4f8a72") * 0.45 * m
    # 1.28.1: a brass rib along the left seam of each gore (the reference's dome shows thick brass ribs between its copper
    # gores), bevelled: lit on its left, shadowed on its right, rivets down its middle
    rw = max(6, w // 7)
    rt = 0.64 + 0.3 * np.clip(1 - xs / 2.5, 0, 1) - 0.38 * np.clip(1 - (rw - xs) / 2.5, 0, 1) - 0.1 * ys / h + _grain(w, h, rng, 0.03)
    rib = _ramp_np(("5e300a", "a8621a", "d48c28", "f4b23c", "ffd878"), rt)
    col[:, :rw] = rib[:, :rw]
    col[:, rw] = col[:, rw] * 0.5
    for cy in np.linspace(h * 0.18, h * 0.82, 3):
        _rivet(col, rw / 2, cy, 1.5, _c("d08c2c"), shadow=0.7, hi=_c("ffe090"))
        _rivet(col, w - 4.0, cy, 1.6, _c(BRASS[2]))
    _put(a, region, col)


def _bevel_brass_hd(a, region, rng):
    """A brass bar seen face on, stretched on each piece of a gear wheel: polished middle, a lit upper and left edge, a
    shadowed lower and right edge, a dark outline (the pieces read in relief)."""
    u, v, w, h = region
    hl, sh, ys = _bevel(w, h, light=(4.0, 4.0), dark=(4.0, 4.0), kl=(1.0, 0.8), kd=(0.85, 0.7))
    t = 0.52 + 0.08 * _noise(w, h, 8, rng) + _grain(w, h, rng, 0.02) - 0.06 * ys / h
    col = _ramp_np(("5e300a", "a8621a", "d48c28", "f4b23c", "ffd878"), t + 0.42 * hl - 0.46 * sh)
    col[h - 1, :] = col[:, w - 1] = _c("4a2608")
    _put(a, region, col)


def _pipe_hd(a, region, rng):
    """A copper pipe: rounded light across it (a bright reflection in its upper third, a dark underside), long brushed
    streaks, a joint ring every block."""
    u, v, w, h = region
    ys, xs = np.mgrid[0:h, 0:w].astype(float) + 0.5
    t = ys / h
    k = 0.18 + 0.7 * np.sin(np.pi * t) ** 0.7 + 0.35 * np.exp(-((t - 0.28) / 0.07) ** 2) - 0.25 * np.clip((t - 0.7) / 0.3, 0, 1)
    k = k + 0.05 * _noise(w, h, 14, rng, 1.5) + _grain(w, h, rng, 0.02)
    col = _ramp_np(("2e1006", "6a2c12", "a84e24", "d87c40", "ffc48e"), k * 0.9)
    for x0 in range(0, w, BLK):
        for dx, f in ((0, 0.55), (1, 1.25), (2, 1.1), (BLK - 1, 0.7)):
            if x0 + dx < w:
                col[:, x0 + dx] *= f
    _put(a, region, col)


def _planks_hd(a, region, tones, seam, rng, plank=BLK // 2, nails=True, grain=0.12, joints=2, vertical=False):
    """Planks with baked light: a tone per plank, fine grain along the plank, a dark seam under each plank and a lit
    upper edge, butt joints with nail heads, a few knots."""
    u, v, w, h = region
    if vertical:
        w, h = h, w
    tones = [_c(t) for t in tones]
    seam = _c(seam)
    out = np.zeros((h, w, 3))
    gn = _noise(w, h, 18, rng, 1.0) * grain + _noise(w, h, 5, rng, 0.7) * grain * 0.5 + _grain(w, h, rng, 0.03)
    r = rng
    for py in range(0, h, plank):
        ph = min(plank, h - py)
        cuts = sorted(r.randrange(6, w - 6) for _ in range(joints)) if joints else []
        edges = [0] + cuts + [w]
        for j in range(len(edges) - 1):
            x0, x1 = edges[j], edges[j + 1]
            base = tones[r.randrange(len(tones))] * r.uniform(0.88, 1.12)
            yy = np.arange(ph)[:, None]
            prof = 1.0 + 0.22 * np.clip(1 - yy / 2.0, 0, 1) - 0.35 * np.clip((yy - (ph - 3)) / 2.0, 0, 1)
            blk = base[None, None, :] * (prof * (1 + gn[py:py + ph, x0:x1]))[..., None]
            if x1 - x0 > 10 and r.random() < 0.25:
                kx, ky = r.randrange(x0 + 3, x1 - 3), r.uniform(1.5, ph - 1.5)
                for yk in range(ph):
                    for xk in range(x0, x1):
                        dd = math.hypot((xk - kx) / 2.2, (yk - ky) / 1.2)
                        if dd < 1.0:
                            blk[yk, xk - x0] *= 0.6
                        elif dd < 1.8:
                            blk[yk, xk - x0] *= 0.85
            out[py:py + ph, x0:x1] = blk
            if x1 < w:
                out[py:py + ph, x1 - 1] = seam
                out[py:py + ph, x1 - 2] *= 0.8
                out[py:py + ph, min(w - 1, x1)] *= 1.15
                if nails:
                    for xn in (x1 - 4, x1 + 2):
                        if 0 <= xn < w:
                            _rivet(out[py:py + ph], xn + 0.5, ph * 0.5, 1.1, _c("3a3836"))
        out[py + ph - 1] = seam
    if vertical:
        out = out.transpose(1, 0, 2)
    _put(a, region, out)


def _bar_hd(a, region, base, rng, seg=BLK):
    """A railing bar: lit top, dark underside, a joint every block, worn lighter edges."""
    u, v, w, h = region
    ys, xs = np.mgrid[0:h, 0:w].astype(float) + 0.5
    t = ys / h
    k = 0.85 + 0.45 * np.clip(1 - t / 0.2, 0, 1) - 0.45 * np.clip((t - 0.7) / 0.3, 0, 1) + 0.08 * _noise(w, h, 10, rng, 2)
    col = _c(base)[None, None, :] * k[..., None]
    for x in range(0, w, seg):
        col[:, x] *= 1.2
        if x > 0:
            col[:, x - 1] *= 0.55
    _put(a, region, col)


def _lamp_hd(a, region, rng):
    """Lantern glass (the lanterns are drawn full bright): a dark iron frame, a glazing bar, a hot core fading to a
    saturated orange."""
    u, v, w, h = region
    ys, xs = np.mgrid[0:h, 0:w].astype(float) + 0.5
    d = np.hypot((xs - w / 2) / (w / 2), (ys - h * 0.56) / (h / 2) * 0.85)
    col = _ramp_np(("fff6d0", "ffd070", "ffa236", "f07a1c", "c85a10"), d)
    fr = max(1, w // 12)
    frame = (xs < fr) | (xs > w - fr) | (ys < fr) | (ys > h - fr) | (np.abs(xs - w / 2) < fr * 0.6)
    col = np.where(frame[..., None], _c("2c2826"), col)
    _put(a, region, col)


def _glow_hd(a, region, rng):
    u, v, w, h = region
    ys, xs = np.mgrid[0:h, 0:w].astype(float) + 0.5
    d = np.hypot((xs - w / 2) / (w / 2), (ys - h / 2) / (h / 2))
    _put(a, region, _ramp_np(("fff0c0", "ffc060", "ff9a30"), d * 0.8))


def _chain_hd(a, region, rng):
    """Dark iron links: oval links alternating face-on and edge-on, lit on their upper edges."""
    u, v, w, h = region
    col = np.zeros((h, w, 3)) + _c("1a1715")
    L = w // 4
    for y in range(h):
        for x in range(w):
            cx = (x // L) * L + L / 2
            cy = (y // L) * L + L / 2
            dx, dy = (x + 0.5 - cx) / (L / 2), (y + 0.5 - cy) / (L / 2)
            if ((x // L) + (y // L)) % 2 == 0:
                rr = math.hypot(dx * 0.9, dy * 1.2)
                if 0.45 < rr < 1.0:
                    lt = -dy
                    col[y, x] = _c("4a423a") * (1 + 0.5 * lt)
            else:
                if abs(dx) < 0.35 and abs(dy) < 1.0:
                    col[y, x] = _c("3a332e") * (1.2 - 0.4 * (dx + 0.35))
    _put(a, region, col)


def _cloth_roll_hd(a, region, rng):
    """Furled black canvas: rolled folds along it (soft light and dark bands), gaskets of light rope every block."""
    u, v, w, h = region
    ys, xs = np.mgrid[0:h, 0:w].astype(float) + 0.5
    k = 0.9 + 0.22 * np.sin(ys / h * math.pi * 3.2 + 0.7 * np.sin(xs * 0.07)) + 0.08 * _noise(w, h, 9, rng, 3) - 0.3 * (ys / h) ** 2
    col = _c("34302e")[None, None, :] * k[..., None]
    for x0 in range(BLK // 2, w, BLK):
        for dx in range(-2, 2):
            x = x0 + dx
            if 0 <= x < w:
                col[:, x] = _c("8a7250") * (1.15 if dx == -2 else 0.8 if dx == 1 else 1.0)
    _put(a, region, col)


def _crate_hd(a, region, rng):
    u, v, w, h = region
    _planks_hd(a, region, ("7a5232", "6e4a2c", "84593a"), "2e1c10", rng, plank=w // 4, joints=0, nails=False)
    col = a[v:v + h, u:u + w, :3].copy()
    ys, xs = np.mgrid[0:h, 0:w].astype(float) + 0.5
    fw = w / 9
    frame = (xs < fw) | (xs > w - fw) | (ys < fw) | (ys > h - fw) | (np.abs(xs - ys) < fw * 0.6)
    fc = _c("5a3a20") * (1 + 0.25 * np.clip(1 - np.minimum(xs, ys) / fw, 0, 1))[..., None] * (1 + _grain(w, h, rng, 0.05))[..., None]
    col = np.where(frame[..., None], fc, col)
    for cx, cy in ((fw / 2, fw / 2), (w - fw / 2, fw / 2), (fw / 2, h - fw / 2), (w - fw / 2, h - fw / 2)):
        _rivet(col, cx, cy, fw * 0.45, _c("3a3a3e"))
    _put(a, region, col)


def _flag_hd(a, region, rng):
    u, v, w, h = region
    ys, xs = np.mgrid[0:h, 0:w].astype(float) + 0.5
    k = 1.0 + 0.1 * np.sin(xs * 0.25 + ys * 0.1) + _grain(w, h, rng, 0.03)
    col = _c("2c2a2c")[None, None, :] * k[..., None]
    gb = max(3, h // 8)
    gold = (ys < gb) | (ys > h - gb) | (xs < gb)
    gt_ = np.where(ys < gb, 0.8 - ys / gb * 0.3, np.where(ys > h - gb, 0.35, 0.6))
    col = np.where(gold[..., None], _ramp_np(GOLD, gt_), col)
    _put(a, region, col)


def _paint_hd(a, rng):
    """Paints the exterior regions again at 32 px a block over the upscaled base (a: SIZE x SIZE x 4 floats)."""
    R = REGIONS
    # charcoal iron: a near-neutral warm charcoal, as the reference's plates (not blue-grey, not brown: the copper and
    # brass bands must stand out of it), the lit bevel kept to about +20 of luminance
    # (1.28.0: a wider, brighter lit bevel and a stronger top light, plates from near-black to a lighter charcoal: the
    # relief and the block-by-block variation of the reference read from the quay, where the rivets and seams vanish)
    soft = dict(lit="0c0a0a", lit_k=1.5, rivet="4a3f36", rivet_hi=(1.3, 8), brown=0.12)
    _plates_hd(a, R["plate_a"], ("2c2927", "292524", "322d2b", "262221", "2f2b29", "3a3531", "2a2625", "231f1e", "2a2b2f", "2f3136"), rng,
               **soft)
    _plates_hd(a, R["plate_b"], ("322e2b", "2d2926", "38332f", "2a2623", "342f2b", "3e3833", "2e3035", "34363c"), rng, **soft)
    # under the copper boot-top: darker, with joints, rivets and rust a third less contrasted (they sparkled at a distance)
    _plates_hd(a, R["plate_c"], ("201c1a", "231e1c", "26211e", "1e1a18"), rng, rust=0.06, rust_col="3e2818", lit="060404", lit_k=1.3,
               seam="15110f", rivet="342c26", rivet_hi=(1.2, 5), brown=0.15)
    # the funnel: browner, a little lighter plates than the hull (the reference's funnel is a sooty brown-grey, not black)
    # with rivet columns along their seams (1.28.1)
    _plates_hd(a, R["funnel"], ("3a302a", "362c26", "40352e", "312824", "453a32", "3c3430"), rng, rivets="columns", rust=0.1, brown=0.45,
               lit="0e0a08", lit_k=1.5, rivet_hi=(1.3, 8), rivet="5a4a3c")
    # the dome's drum: dark brown copper plates
    _plates_hd(a, R["dome_drum"], ("5a3020", "52291a", "613524", "4c2818"), rng, rivet="c8843e", lit="1a0c06", lit_k=1.5, rust=0.0,
               rust_col="3e5a48", brown=0.0)
    _plates_hd(a, R["dome"], ("94481e", "a2522a", "8a4420", "ac5a2c"), rng, rivet="e0a050", lit="201006", lit_k=1.35, rust=0.08,
               rust_col="4f8a72", brown=0.0)
    _gore_hd(a, R["dome_gore"], rng)
    # copper bands and caps, brass bands, the dark beams, iron bands
    # (rivet heads close to the band's colour: pale brass dots read as dust at a distance and shimmered)
    # (1.28.1: a more saturated copper, less blue in it: the bands read brown-grey from the quay next to the gold)
    _band_hd(a, R["copper"], ("4a1a06", "d05e22", "ffb262"), rng, rivet="dc9048", patina=0.07, refl=0.46)
    _band_hd(a, R["copper2"], ("521c06", "d86826", "ffba6c"), rng, rivet="e49850", patina=0.06, refl=0.46)
    # brass: a saturated bright gold (the funnel band, the stem, the window frames: the reference's bold shiny brass)
    _band_hd(a, R["brass_band"], ("6a3810", "d48c2a", "ffd470"), rng, rivet="e0a450", refl=0.44)
    _band_hd(a, R["stone"], ("161210", "3e3029", "6a5444"), rng, rivet="a87c3a", refl=0.18)
    _band_hd(a, R["iron_band"], ("141416", "3a3a3e", "5e5e64"), rng, rivet="5e544a", refl=0.2)
    _polished_hd(a, R["brass"], ("5a2a08", "94501a", "c47a2a", "e8a446", "ffd488"), rng, amp=0.55, streak=0.03)
    _polished_hd(a, R["plaque"], ("5a2e0e", "a8622a", "e09a48", "ffd08a"), rng, waves=0.6)
    _polished_hd(a, R["gear_face"], ("4e280c", "8a4c1c", "c07a34", "f0b060"), rng, waves=2.0)
    _bevel_brass_hd(a, R["gear_bevel"], rng)
    _polished_hd(a, R["bronze"], ("5a2e0e", "8a4c1c", "b0662a", "e09848"), rng, waves=1.5)
    _glow_window_hd(a, R["glow_window"], rng)
    _pipe_hd(a, R["pipe"], rng)
    _bar_hd(a, R["rail"], "8a4624", rng)
    _planks_hd(a, R["wood_dark"], ("3e2a18", "36240f", "44301c", "3a2614"), "140a04", rng)
    _planks_hd(a, R["wood_mid"], ("62422a", "5a3c20", "6a482c"), "24160a", rng)
    _planks_hd(a, R["deck"], ("5e4228", "563a22", "66482c", "50361f", "5a3e26"), "1e140a", rng, joints=3)
    _planks_hd(a, R["dark_wood"], ("30200f", "36240f", "2c1c0c"), "120804", rng, joints=1)
    _planks_hd(a, R["mast"], ("42301c", "4a341e", "3c2a16"), "1c1008", rng, plank=BLK, joints=0, nails=False, grain=0.16)
    _lamp_hd(a, R["lantern"], rng)
    _glow_hd(a, R["glow"], rng)
    _chain_hd(a, R["chain"], rng)
    _cloth_roll_hd(a, R["cloth_roll"], rng)
    _crate_hd(a, R["crate"], rng)
    _flag_hd(a, R["flag"], rng)
    u, v, w, h = R["iron_dark"]
    _put(a, R["iron_dark"], _c("1e1d1e")[None, None, :] * (1 + 0.08 * _noise(w, h, 4, rng) + _grain(w, h, rng, 0.04))[..., None])
    u, v, w, h = R["iron"]
    _put(a, R["iron"], _c("3c3a3a")[None, None, :] * (1 + 0.1 * _noise(w, h, 4, rng) + _grain(w, h, rng, 0.05))[..., None])


def _black_sail_hd(a, name, rng, stripe=0.31, emblem=None):
    """Black blocky sail at 40 px a cloth: a tone per cloth (lighter in the belly, darker at the leeches), a fine weave,
    each cloth rounded like a pillow lit from the left (it reads at a distance), soft broad folds and a top-to-bottom
    gradient, lit and shadowed seams between the cloths, a stitched panel
    seam down each cloth, two stitched reinforcement bands with reef points, a twisted bolt rope round the edges; a gold
    border on the fore leech and along the foot from a vertical gold stripe at `stripe` of the width (lit inner edge,
    shadowed outer edge, stitches); emblem = (centre u, centre v, diameter) fractions of a gold gear, outlined, bevelled
    and shaded."""
    u, v, w, h = SAIL_REGIONS[name]
    cols, rows = SAIL_CELLS[name]
    cw, ch = w / cols, h / rows
    tones = [_c(c) for c in ("2a2423", "332b2a", "3c3331", "252020", "42403f", "4a4746")]
    tone = np.zeros((rows, cols, 3))
    for r_ in range(rows):
        for c_ in range(cols):
            dx = abs((c_ + 0.5) / cols - 0.5) * 2
            dy = (r_ + 0.5) / rows
            k = 1.0 + 0.14 * (1 - dx * dx) - 0.12 * dx * dx - 0.04 * dy
            tone[r_, c_] = tones[rng.randrange(len(tones))] * k * rng.uniform(0.9, 1.12)
    ys, xs = np.mgrid[0:h, 0:w].astype(float) + 0.5
    ci = np.minimum(cols - 1, (xs // cw).astype(int))
    ri = np.minimum(rows - 1, (ys // ch).astype(int))
    lx, ly = xs - ci * cw, ys - ri * ch
    weave = (((xs.astype(int) + ys.astype(int)) % 2) - 0.5) * 0.04 + _grain(w, h, rng, 0.025)
    folds = 0.08 * np.sin(2 * np.pi * xs / (w / 4.3) + 0.9 * np.sin(ys / h * np.pi * 1.2)) + 0.03 * np.sin(2 * np.pi * xs / (w / 10.5) + 1.3)
    # each cloth rounded like a pillow lit from the left (a lit third, a shadowed third, +/- 12 %): broad enough to read
    # at a distance, where the seams and the weave vanish (the reference's sails show each block of cloth)
    folds = folds + 0.15 * np.cos(np.pi * np.clip(lx / cw, 0, 1)) + 0.05 * np.cos(np.pi * np.clip(ly / ch, 0, 1))
    # diagonal folds running up from the clews (the corners where the sheets pull)
    folds = folds - 0.08 * np.clip(1 - np.abs((xs / w - (1 - ys / h) * 0.35) - 0.0) * 9, 0, 1) \
        - 0.08 * np.clip(1 - np.abs((1 - xs / w) - (1 - ys / h) * 0.35) * 9, 0, 1)
    k = (1.1 - 0.26 * ys / h) * (1 + folds + weave + 0.04 * _noise(w, h, 12, rng))
    col = tone[ri, ci] * k[..., None]
    # cloth seams: lit upper / left edge, dark lower / right edge
    col = np.where(((lx < 2.5) | (ly < 2.5))[..., None], col * 1.4, col)
    col = np.where(((lx > cw - 3.0) | (ly > ch - 3.0))[..., None], col * 0.55, col)
    # the panel seam down the middle of each cloth: a dark line and light stitches
    mid = np.abs(lx - cw / 2) < 0.8
    col = np.where(mid[..., None], col * 0.72, col)
    stitch = (np.abs(lx - cw / 2 - 1.6) < 0.6) & ((ys.astype(int) % 5) < 2)
    col = np.where(stitch[..., None], col * 1.35 + 6, col)
    # reinforcement bands at a third and two thirds of the height, with reef points
    for fr in (1 / 3, 2 / 3):
        yb = h * fr
        band = np.abs(ys - yb) < 3.5
        col = np.where(band[..., None], col * 1.3 + 5, col)
        col = np.where((np.abs(np.abs(ys - yb) - 3.0) < 0.6)[..., None], col * 0.7, col)
        reef = (np.abs(ys - yb - 6) < 2.5) & (np.abs((xs % (cw / 2)) - cw / 4) < 0.8)
        col = np.where(reef[..., None], _c("6a5a44") * (1.2 - (ys - yb - 3.5) / 6)[..., None], col)
    # the bolt rope round the edges (twisted: alternating light and dark strands)
    rope_w = 3.0
    edge = np.minimum(np.minimum(xs, w - xs), np.minimum(ys, h - ys))
    strand = (((xs + ys).astype(int) // 2) % 2).astype(float)
    rope = _c("4a4038")[None, None, :] * (0.75 + 0.45 * strand)[..., None]
    col = np.where((edge < rope_w)[..., None], rope, col)
    # the gold border and stripe
    gd, gm, gh = (_c(c) for c in GOLD)
    bw = max(5, int(cw * 0.75))
    sx = int(stripe * w)
    in_leech = xs >= w - bw
    in_foot = (ys >= h - bw) & (xs >= sx)
    in_stripe = (xs >= sx) & (xs < sx + bw)
    gold = in_leech | in_foot | in_stripe
    # distance across the gold strip (0 at its inner / upper-left edge, 1 at its outer edge)
    gt_ = np.where(in_stripe, (xs - sx) / bw, np.where(in_leech, (xs - (w - bw)) / bw, (ys - (h - bw)) / bw))
    gk = 0.55 + 0.45 * np.exp(-((gt_ - 0.22) / 0.16) ** 2) - 0.3 * np.clip((gt_ - 0.75) / 0.25, 0, 1)
    gcol = _ramp_np((gd * 0.7, gd, gm, gh, np.minimum(255, gh * 1.04)), gk + 0.05 * _noise(w, h, 7, rng))
    gstitch = (np.abs(gt_ - 0.5) < 0.05) & (((xs + ys).astype(int) % 6) < 2)
    gcol = np.where(gstitch[..., None], gcol * 0.6, gcol)
    gcol = np.where(((lx > cw - 2.5) | (ly > ch - 2.5))[..., None], gcol * 0.72, gcol)
    col = np.where(gold[..., None], gcol, col)
    # the emblem
    if emblem:
        eu, ev, ed = emblem
        size = int(ed * w)
        mk = np.array(gear_mask(size, rim=(0.64, 0.86), hub=(0.14, 0.34), spoke=0.085)) > 0   # thick: it reads from afar
        cols_map = SAIL_COLUMNS.get(name)
        if cols_map:
            spans, width = cols_map
            ce = min(cols - 1, int(eu * cols))
            te, be = spans[ce]
            wc = te - ev * (te - be)
            rad = ed * width / 2
            tc = np.array([spans[c_][0] for c_ in range(cols)])[ci]
            bc = np.array([spans[c_][1] for c_ in range(cols)])[ci]
            wx = xs / w * width - eu * width
            wy = wc - (tc - ys / h * (tc - bc))
            mx = ((wx / (2 * rad) + 0.5) * size).astype(int)
            my = ((wy / (2 * rad) + 0.5) * size).astype(int)
        else:
            mx = (xs - (eu * w - size / 2)).astype(int)
            my = (ys - (ev * h - size / 2)).astype(int)
        ok = (mx >= 0) & (mx < size) & (my >= 0) & (my < size)
        M = np.zeros((h, w), bool)
        M[ok] = mk[my[ok], mx[ok]]

        def shift(m, dx, dy):
            o = np.zeros_like(m)
            ys0, ys1 = max(0, dy), h + min(0, dy)
            xs0, xs1 = max(0, dx), w + min(0, dx)
            o[ys0:ys1, xs0:xs1] = m[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
            return o
        # the dark outline lies on the cloth round the gold (inside, it thinned the spokes and the rim to nothing in game)
        outline = ~M & (shift(M, 2, 0) | shift(M, -2, 0) | shift(M, 0, 2) | shift(M, 0, -2) | shift(M, 2, 2) | shift(M, -2, -2))
        outline2 = M & ~(shift(M, 1, 0) & shift(M, -1, 0) & shift(M, 0, 1) & shift(M, 0, -1))
        lit = M & ~shift(M, 3, 3)           # the texel 3 up-left is outside: an upper-left edge
        dark = M & ~shift(M, -3, -3)
        radial = np.clip(my / max(1, size) * 1.1, 0, 1)
        ecol = _ramp_np((gh, np.minimum(255, gm * 1.1), gm, gd * 1.15), radial * 0.8 + 0.06 * _noise(w, h, 6, rng))
        ecol = np.where(lit[..., None], np.minimum(255, ecol * 1.12 + 10), ecol)
        ecol = np.where(dark[..., None], ecol * 0.62, ecol)
        ecol = np.where(outline2[..., None], gd * 0.85, ecol)
        col = np.where(M[..., None], ecol, col)
        col = np.where(outline[..., None], _c("1e1008"), col)
    _put(a, (u, v, w, h), col)


def _paint_base():
    """The whole atlas at 16 px a block (layout units, 512 x 512): the rooms, the furniture and the small fittings keep
    this painting (upscaled); the hull, the trims, the metals, the windows, the dome and the funnel are painted again
    at 32 px a block over it (_paint_hd)."""
    rng = random.Random(4721)
    img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    px = img.load()
    R = LAYOUT
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
    return img


def make_texture(path):
    img = _paint_base().resize((SIZE, SIZE), Image.NEAREST)
    a = np.array(img).astype(float)
    _paint_hd(a, random.Random(18741))
    _paint_rooms_hd(a, random.Random(30917))
    img = Image.fromarray(np.clip(np.round(a), 0, 255).astype(np.uint8), "RGBA")
    img.save(path, optimize=True)
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
    a = np.zeros((SAIL_SIZE, SAIL_SIZE, 4))
    _black_sail_hd(a, "main_sail", rng, stripe=0.34, emblem=(0.67, 0.44, 0.33))
    _black_sail_hd(a, "mizzen_sail", rng, stripe=0.25)
    img = Image.fromarray(np.clip(np.round(a), 0, 255).astype(np.uint8), "RGBA")
    img.save(path, optimize=True)
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
