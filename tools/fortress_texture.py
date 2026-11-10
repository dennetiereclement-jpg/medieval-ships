"""Procedural pixel-art textures of the Fortress Ship (fortress_ship): a 512x512 atlas of the hull, the castle, the
fittings and the rooms (fortress_ship.png, 16 px a block; the banners and shields 32) and a 1024x1024 atlas of the
sails (fortress_ship_sails.png, 32 px a block), so that the castle-tower emblems and the cloth keep their resolution.

Phase 5 (visual pass): Minecraft lights an entity flat, face by face, so the light and shade of the references are
painted in: bevelled, mottled, chipped stone blocks over dark joints; planks a tone each with lit edges, dark seams,
butt joints, nail heads and knots; domed iron studs and bosses with a glint and a cast shadow; the planking darker
row by row towards the keel and wet at the waterline, the strakes and the red panels shaded under the stone
overhangs; the sails' cloth blocks bevelled like the voxel sails of the main reference, with stitched seams, reef
bands and points, a bolt rope, folds and a darker foot; the tower emblems outlined, their masonry and bevel drawn.

Phase 6 (after the in-game screenshots): the stone lighter and warmer again with a near-white top bevel; the red panels
square bevelled blocks as on the main reference; the planks within a few per cent of each other, with dark brown nail
heads on every other butt only (no near-black speckle from afar, no nails on the fittings' and furniture's wood); small
dark iron studs, half as many; the rib plates narrower (more stone round them), drawn for their real width.

Phase 7 (the deep visual rework, main reference): the stone lighter and warmer again (base about #bcae9e, a near
white top bevel), smoother faces, bright silver studs; the red panels in dark iron frames with bright rivets (posts and
rails); the sails a deeper crimson, each cloth block its own value, stronger bevels, the head in the yard's shadow and
a lit belly, warmer whites; a gold fringe on the banners, the tower on the pennants.

Colours of the references (docs/Fortress_PLAN.md): a dark brown planked hull clad with light grey stone blocks
(stone wales, vertical stone ribs, crenellated stone parapets, iron studs), red panels between the ribs, iron
straps; the stern castle in grey stone with lit windows in dark wooden frames, the turret of dark timber with a
red tiled roof; bright red sails bordered and striped with white wool, a beige / white crenellated tower with a
gate on the big sails, a white jib with a red band; red banners with the white tower and a pointed foot; red
swallow-tailed pennants; tarred hemp rope ladders; warm lanterns. Inside: dark panelling in the captain's cabin,
stone walls in the keep and the turret, plank floors and beams, the plain planks of the hold and the crew rooms.

Every region is (u, v, w, h); REGIONS and SAIL_REGIONS are shared with tools/generate_fortress.py.
"""
import math
import random

import numpy as np
from PIL import Image

from galley_texture import _jitter, _rgb
import corsair_texture as ct
import frigate_texture as ftx

SIZE = 512
SAIL_SIZE = 1024   # phase 5: 32 px a block (seams, bolt ropes, reef bands, the tower's masonry)

REGIONS = {
    # hull and upper works
    "stone":        (0, 0, 64, 32),     # grey stone blocks, 16 px a block (wales, ribs, castle walls, parapets)
    "stone_dark":   (64, 0, 64, 32),    # the same, weathered and darker (low on the hull, shadowed courses)
    "stone_stud":   (128, 0, 64, 32),   # stone blocks with iron studs (the belt and the ribs)
    "hull_brown":   (192, 0, 64, 32),   # below the waterline
    "wood_dark":    (256, 0, 64, 32),
    "wood_mid":     (320, 0, 64, 32),
    "wood_light":   (384, 0, 64, 32),
    "rail":         (448, 0, 64, 16),   # dark wooden rails
    "mast":         (448, 16, 64, 16),
    "deck":         (0, 32, 64, 64),
    "lantern":      (64, 32, 16, 16),
    "rope":         (80, 32, 16, 16),
    "iron":         (96, 32, 16, 16),
    "bronze":       (112, 32, 16, 16),
    "glow":         (64, 48, 16, 16),
    "end_grain":    (80, 48, 16, 16),
    "rope_light":   (96, 48, 16, 16),
    "glass":        (112, 48, 16, 16),
    "dark_wood":    (64, 64, 32, 16),
    "red_paint":    (96, 64, 16, 16),
    "white_paint":  (112, 64, 16, 16),
    "navy":         (64, 80, 16, 16),
    "compass":      (80, 80, 16, 16),
    "cloth_roll":   (96, 80, 32, 16),   # furled red canvas
    "glow_window":  (128, 32, 32, 32),  # lit window in a dark wooden frame (four panes)
    "window_in":    (160, 32, 32, 32),
    "door":         (192, 32, 32, 32),
    "grating":      (224, 32, 32, 32),
    "iron_strap":   (256, 32, 16, 32),  # a black iron strap with rivets (along the stone ribs)
    "studs":        (192, 464, 64, 32), # dark planks with a row of domed iron studs (under the stone belt), 16 px a block
    "pennant":      (288, 32, 64, 16),  # red swallow-tailed pennant, stepped (the mastheads)
    "awning":       (288, 48, 64, 16),  # off-white canvas (the quarterdeck awning)
    "chart":        (352, 32, 32, 32),
    "books":        (384, 32, 32, 32),
    "gold":         (416, 32, 64, 16),
    "bedding":      (416, 48, 32, 16),
    "linen":        (448, 48, 16, 16),
    "sack":         (464, 48, 16, 16),
    "canvas":       (480, 48, 32, 16),
    "cannon":       (352, 64, 32, 16),
    "bore":         (384, 64, 16, 16),
    "painting":     (480, 64, 32, 24),
    "roof_tile":    (128, 64, 64, 32),  # red tiles of the turret's roof (rows of rounded tiles)
    "red_panel":    (192, 64, 64, 32),  # the red panels between the ribs (red boards, dark seams)
    "strake_brown": (192, 160, 64, 16),
    "strake_brown2": (256, 160, 64, 16),
    "rope_dark":    (368, 160, 16, 16), # shrouds and ratlines (warm hemp, as on the references)
    "stone_light":  (256, 64, 64, 32),  # pale cut stone (quoins, merlon caps, window sills)
    "timber":       (320, 64, 32, 32),  # the turret walls: dark vertical boards
    "banner":       (448, 176, 64, 128),  # red banner with the white tower, pointed foot (transparent around it), 32 px a block
    "shield":       (384, 176, 64, 80),   # heater shield: red field, white tower, gold rim (transparent around it), 32 px a block
    "wall_stone":   (64, 176, 64, 64),  # inside the keep and the turret: dressed stone, a wooden dado
    "tile_edge":    (128, 176, 64, 16), # the roof's eaves: grey stone band with a red tile lip
    "beak":         (128, 192, 64, 32), # the stone beak of the stem head (bigger blocks)
    # rooms
    "wall_wood":    (0, 96, 64, 64),    # the captain's cabin: dark panelling, a red and gold rail
    "floor":        (64, 96, 64, 64),
    "ceil":         (128, 96, 64, 64),
    "hold_floor":   (192, 96, 64, 64),
    "hold_wall":    (256, 96, 64, 64),
    "carpet":       (320, 96, 32, 64),
    "rug":          (352, 96, 32, 64),
    "boat":         (384, 96, 64, 32),
    "ham":          (448, 96, 16, 16),
    # the decoration (tools/fortress_furniture.py)
    "tower_rug":    (0, 240, 64, 96),   # red carpet with the white tower, a grey stone border and a gold band
    "war_map":      (64, 240, 64, 48),  # the campaign map of the council table: parchment, the coast, Havre-Fort, routes
    "surcoat":      (128, 240, 16, 32), # red surcoat with the white tower and a gold hem (the armour stands)
    "candle":       (144, 240, 16, 16),
    "parchment":    (144, 256, 16, 16),
    "bread":        (160, 240, 16, 16),
    "cheese":       (160, 256, 16, 16),
    "fletching":    (176, 240, 16, 16), # white goose feathers with a red band (the arrows)
    "blade":        (176, 256, 16, 16), # bright steel (swords, spear and halberd heads, helmets)
    "leather":      (192, 240, 16, 16),
    "embers":       (192, 256, 16, 16), # glowing coals (the brazier, drawn full bright)
    "mail":         (208, 240, 16, 16), # chain mail (the armour stands)
    "velvet_red":   (208, 256, 16, 16), # red velvet cushions
    # phase 4: block-sized pieces (drawn one block per cube face, see generate_fortress.masonry)
    "stud_post":    (256, 336, 16, 32), # the dark iron posts with bright rivets that frame the red panels beside each rib (phase 7)
    "rib_plate":    (272, 336, 16, 64), # (phases 4-6) the black iron plate of the ribs; unused since phase 7, kept drawn
    "iron_rail":    (304, 440, 48, 8),  # the iron rails with rivets along the top and the foot of each red panel (phase 7)
    "arch_lit":     (288, 336, 32, 48), # a lit arched window (third reference): dark wooden frame, mullion, transom
    "arch_ring":    (320, 336, 48, 64), # the stone arch (voussoirs, jambs, sill) round it, open in the middle
    "keep_panel":   (368, 336, 32, 48), # a framed red panel with iron studs on the keep's timber walls
    "arch_dark":    (400, 336, 32, 48), # an unlit arched window (the inside of the windows)
    # phase 5 (baked shading): the hull's planking darker towards the keel, row by row (the deepest row darkest), the
    # studded band's upper row in the shadow of the stone belt, the grimy stone low on the hull, a domed stud head
    "hull_deep":    (0, 464, 64, 32),
    "hull_low":     (64, 464, 64, 32),
    "studs_top":    (128, 464, 64, 32),
    "stone_grime":  (240, 432, 64, 32),
    "stud_head":    (304, 432, 8, 8),
}
# single stone blocks (16 x 16, a joint along their right and bottom edges, bevelled): a tone each
# (phase 5: twice as many tiles, so that neighbouring blocks seldom repeat; a grimy set for the courses low on the hull)
N_SB, N_SBS, N_SBD, N_SBL, N_SBG = 12, 5, 6, 4, 4
STONE_TILES = {"stone": ["sb_%d" % k for k in range(N_SB)],
               "stone_stud": ["sb_0", "sbs_0", "sb_2", "sbs_1", "sb_4", "sbs_2", "sb_7", "sbs_3", "sb_9", "sbs_4"],
               "stone_dark": ["sbd_%d" % k for k in range(N_SBD)], "stone_light": ["sbl_%d" % k for k in range(N_SBL)],
               "beak": ["sb_1", "sbs_0", "sb_3", "sbs_2", "sb_8", "sbs_3"], "stone_grime": ["sbg_%d" % k for k in range(N_SBG)]}
for _k in range(N_SB):
    REGIONS["sb_%d" % _k] = (16 * _k, 336, 16, 16) if _k < 6 else (16 * (_k - 6), 432, 16, 16)
for _k in range(N_SBS):
    REGIONS["sbs_%d" % _k] = (96 + 16 * _k, 336, 16, 16) if _k < 3 else (96 + 16 * (_k - 3), 432, 16, 16)
for _k in range(N_SBD):
    REGIONS["sbd_%d" % _k] = (144 + 16 * _k, 336, 16, 16) if _k < 4 else (128 + 16 * (_k - 4), 432, 16, 16)
for _k in range(N_SBL):
    REGIONS["sbl_%d" % _k] = (208 + 16 * _k, 336, 16, 16) if _k < 3 else (160, 432, 16, 16)
for _k in range(N_SBG):
    REGIONS["sbg_%d" % _k] = (176 + 16 * _k, 432, 16, 16)
# regions mapped one block = 16 px from the face's corner (joints and studs aligned with the cube's edges)
ALIGNED = ("stone", "stone_dark", "stone_stud", "stone_light", "beak", "stone_grime", "red_panel", "studs", "studs_top", "stud_post",
           "rib_plate")
ALIGNED_V = ("stud_post", "rib_plate")   # these two stretched across their (narrow) face, aligned down it only
# (phase 6: lighter and warmer again, as the main reference's light stone: the hull's sides are lit at about half in game)
# (phase 7: lighter and warmer again, the light stone fortress of 112: base about #b4a696, top bevel near #dcd2c6)
# (phase 8: the chiselled mid grey of 112 instead of cream: base about #a9a39c, top-left bevel #cdc7bf, bottom-right
# bevel #6e6862 over a 2 px joint, each block its own value within 8 %, about one block in six darker, #8e8880)
STONE_TONES = ("a9a39c", "a39d96", "b0aaa3", "9e9891", "aca69f", "a59f98")
STONE_DARKER = "8e8880"
STONE_DARK = ("8a847d", "817b74", "908a83", "77716a")
STONE_LIGHT = ("c9c3bb", "c2bcb4", "d0cac2")
STONE_MORTAR = "2a2420"
# names used by the shared helpers (ship_details, generate_galleon, corsair_furniture): the same pixels
for _alias, _src in (("hull_mid", "wood_mid"), ("hull_light", "wood_light"), ("hull_dark", "wood_dark"), ("wood_trim", "wood_dark"),
                     ("wood_honey", "wood_mid"), ("blue_paint", "navy"), ("pilaster", "wood_dark"), ("velvet", "red_paint"),
                     ("cushion", "red_paint"), ("brass", "bronze"), ("organ_wood", "wood_dark"), ("steel", "iron"), ("stripe", "white_paint"),
                     ("patch_wood", "wood_light"), ("repair", "wood_mid"), ("plate", "iron"), ("hearth_stone", "stone"), ("soot", "iron"),
                     ("stone_floor", "stone"), ("carving", "gold"), ("hull_blue", "red_panel")):
    REGIONS[_alias] = REGIONS[_src]

# the sails (second texture): one region each, cloth blocks of 16 px (8 on the small sails)
SAIL_REGIONS = {
    "main_course":    (0, 0, 576, 352),
    "fore_course":    (576, 0, 448, 288),
    "mizzen_course":  (576, 288, 384, 256),
    "main_topsail":   (0, 352, 384, 192),
    "fore_topsail":   (0, 544, 320, 160),
    "jib":            (320, 544, 256, 320),
}
SAIL_CELLS = {  # (columns, rows) of cloth blocks drawn in each sail region
    "main_course": (20, 11), "fore_course": (16, 8), "mizzen_course": (12, 8), "main_topsail": (8, 3), "fore_topsail": (6, 3),
    "jib": (8, 10),
}
# which sails carry the castle-tower emblem (the courses of the fore and main masts, as on the references)
EMBLEM_SAILS = ("main_course",)   # the tower on the main course only, as on all three references

_mix, _scale, _planks, _blocks, _fill = ct._mix, ct._scale, ct._planks, ct._blocks, ct._fill

RED = ("a21c1f", "961a1d", "ac2024", "8e1719", "9c1b1e")      # deep crimson (phase 7: a shade deeper, as the main reference)
WHITE = ("d6d1c8", "c8c3ba", "dedad1", "bdb8af")       # (phase 7: warmer, the grey-white wool of the main reference)
BEIGE = "e2d2b0"

# ---------------------------------------------------------------- the castle-tower emblem
# A crenellated tower with a gate, drawn by hand in 12 x 14 cells (the blocky emblem of the references): three
# merlons, a parapet a little wider than the tower, two windows, an arched gate at the foot.
TOWER = [
    "XX...XX...XX",
    "XX...XX...XX",
    "XXXXXXXXXXXX",
    "XXXXXXXXXXXX",
    ".XXXXXXXXXX.",
    ".XXXXXXXXXX.",
    ".XXX.XX.XXX.",
    ".XXX.XX.XXX.",
    ".XXXXXXXXXX.",
    ".XXXXXXXXXX.",
    ".XXXX..XXXX.",
    ".XXX....XXX.",
    ".XXX....XXX.",
    ".XXX....XXX.",
]


def tower_mask(w, h, cell=None, cell_h=None):
    """Mask (0/255, w x h) of the TOWER emblem, square cells as big as fit (or `cell` px wide, `cell_h` high), centred."""
    cw, ch = len(TOWER[0]), len(TOWER)
    cell = cell or max(1, min(w // cw, h // ch))
    cell_h = cell_h or cell
    img = Image.new("L", (w, h), 0)
    px = img.load()
    ox, oy = (w - cw * cell) // 2, (h - ch * cell_h) // 2
    for r, row in enumerate(TOWER):
        for c, ch_ in enumerate(row):
            if ch_ != "X":
                continue
            for y in range(cell_h):
                for x in range(cell):
                    X, Y = ox + c * cell + x, oy + r * cell_h + y
                    if 0 <= X < w and 0 <= Y < h:
                        px[X, Y] = 255
    return img


# ---------------------------------------------------------------- painters
# Phase 5 (baked shading): Minecraft lights an entity's faces flat, so the light and shade of the references is painted
# into the textures: every stone block bevelled (a lit top and left edge, a shadowed bottom and right edge over a dark
# joint), mottled, speckled, chipped and now and then cracked; every plank its own tone with a lit upper edge, a dark
# seam, butt joints with nail heads, knots and grain; domed iron studs with a glint and the shadow they cast; the red
# boards and the strakes darker where an overhang shades them, the planking darker towards the keel.
def _hash(x, y, s):
    """A repeatable pseudo-random number in [0, 1) for the lattice point (x, y) and the seed s."""
    h = (int(x) * 374761393 + int(y) * 668265263 + int(s) * 982451653) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65536.0


def _vnoise(x, y, s, cell):
    """Smooth value noise in [0, 1), features about `cell` px across."""
    gx, gy = x / cell, y / cell
    x0, y0 = math.floor(gx), math.floor(gy)
    fx, fy = gx - x0, gy - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = _hash(x0, y0, s), _hash(x0 + 1, y0, s), _hash(x0, y0 + 1, s), _hash(x0 + 1, y0 + 1, s)
    return (a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy


def _fbm(x, y, s, cell=4.0):
    """Two octaves of value noise, in [0, 1)."""
    return 0.62 * _vnoise(x, y, s, cell) + 0.38 * _vnoise(x, y, s + 17, cell / 2.2)


# a small domed iron stud (3 x 3), lit from the top left
STUD = (("eaeaf0", "c4c4cc", "5a5a62"), ("c4c4cc", "9a9aa2", "3e3e44"), ("5a5a62", "3e3e44", "202024"))   # (phase 7: silver)


def _stud_px(dx, dy):
    """Colour of the small stud at (dx, dy) from its top left pixel, or None outside it."""
    if 0 <= dx < 3 and 0 <= dy < 3:
        return _rgb(STUD[dy][dx])
    return None


def _boss(dx, dy, r, base="4c4c52"):
    """A round domed boss of radius r centred on (0, 0), lit from the top left: dark iron with a bright glint, its
    colour, "shadow" where it casts its shadow (down and right of it), or None."""
    d = math.hypot(dx, dy)
    if d <= r:
        if math.hypot(dx + 0.4 * r, dy + 0.4 * r) < max(0.75, 0.26 * r):
            return _rgb("ececf0")
        k = 1.15 - 0.6 * (d / r) ** 1.4 - 0.4 * (dx + dy) / (2 * r)
        return _scale(_rgb(base), max(0.28, k))
    if d <= r + 0.9:
        return _rgb("141416") if dx + dy > -0.5 * r else None
    if math.hypot(dx - 0.9, dy - 0.9) <= r + 0.6:
        return "shadow"
    return None


def _stone_block(px, u, v, bw, bh, base, rng, mortar, stud=False, x0=0, y0=0, clip=None, grime=0.0):
    """One bevelled stone block (the voxel masonry of the references) with its shading painted in: a lit top and left
    edge, a shadowed bottom and right edge over a dark joint (along its right and bottom edges), the lower half a little
    darker, a mottled face, dark and light grains, a chip or two (a pit lit on its lower lip), now and then a hairline
    crack; a slight warm or cool cast of its own. stud: a domed iron stud and its shadow. grime: dirt and moss rising
    from its foot (the courses low on the hull)."""
    mortar = _rgb(mortar)
    s = rng.randrange(1 << 20)
    cast = rng.choice(((6, 3, -2), (0, 0, 0), (-3, 0, 5), (3, 1, 0), (0, 0, 0), (-2, -1, 2)))
    base = tuple(max(0, min(255, base[i] + cast[i])) for i in range(3))
    chips = [(rng.randrange(2, bw - 4), rng.randrange(2, bh - 5), rng.choice((1, 2))) for _ in range(rng.choice((0, 1)))]
    crack = set()
    if rng.random() < 0.15:
        cx, cy, dx = rng.randrange(3, bw - 4), rng.randrange(2, bh - 6), rng.choice((-1, 1))
        for _ in range(rng.randrange(4, 8)):
            crack.add((cx, cy))
            cy += 1
            if rng.random() < 0.5:
                cx += dx
            if not (1 <= cx < bw - 2 and cy < bh - 2):
                break
    sx, sy = rng.randrange(4, bw - 7), rng.randrange(3, bh - 7)
    for y in range(bh):
        for x in range(bw):
            X, Y = x0 + x, y0 + y
            if clip and not (0 <= X < clip[0] and 0 <= Y < clip[1]):
                continue
            if x == bw - 1 or y == bh - 1:
                c = _mix(mortar, base, 0.14 if (u + X + 2 * (v + Y)) % 3 == 0 else 0.0)
            elif x == bw - 2 or y == bh - 2:
                c = _mix(mortar, _scale(base, 0.62), 0.45)      # (phase 8: the joint 2 px wide, its inner px the dark bevel)
            else:
                n = _fbm(u + X, v + Y, s)
                k = 1.0 + 0.14 * (n - 0.5) - 0.06 * y / bh                                   # (phase 7: smoother faces)
                k += (0.21 if y == 0 else 0.1 if y == 1 else 0.04 if y == 2 else 0)       # (phase 8: the lit top-left bevel, + 21 %)
                k += (0.18 if x == 0 else 0.07 if x == 1 else 0)
                k -= (0.3 if y == bh - 3 else 0.12 if y == bh - 4 else 0)                 # (the dark bottom-right bevel, - 35 %)
                k -= (0.26 if x == bw - 3 else 0.1 if x == bw - 4 else 0)
                g = _hash(u + X, v + Y, s + 5)
                k += -0.13 if g > 0.965 else 0.09 if g < 0.03 else 0.0
                c = _scale(base, k)
                for cx, cy, r in chips:
                    if cx <= x <= cx + r and cy <= y < cy + r:
                        c = _scale(base, 0.6)
                    elif cx <= x <= cx + r and y == cy + r:
                        c = _scale(base, 1.22)
                if (x, y) in crack:
                    c = _scale(base, 0.62)
                elif (x - 1, y) in crack:
                    c = _scale(c, 1.08)
                if grime:
                    t = max(0.0, (y - bh * 0.4) / (bh * 0.6))
                    c = _mix(c, _rgb("2e2c22"), min(0.55, grime * t ** 1.4 * (0.5 + n)))
                    if y > bh * 0.55 and _hash(u + X, v + Y, s + 9) < 0.12 * grime:
                        c = _mix(c, _rgb("56622e"), 0.65)
                if stud:
                    sc = _stud_px(x - sx, y - sy)
                    if sc is not None:
                        c = sc
                    elif (x - sx == 3 and 1 <= y - sy <= 3) or (y - sy == 3 and 1 <= x - sx <= 3):
                        c = _scale(c, 0.6)
            px[u + X, v + Y] = _jitter(c, rng, 3) + (255,)


def _stone_tone(rng, tones, darker=None):
    """A block's base tone: one of tones within 8 %, or (darker given) about one block in six that darker tone (phase 8:
    the visibly different cubes of the main reference)."""
    if darker is not None and rng.random() < 1 / 6:
        return _scale(_rgb(darker), rng.uniform(0.95, 1.05))
    return _scale(_rgb(rng.choice(tones)), rng.uniform(0.92, 1.08))


def _stone(px, region, rng, tones=STONE_TONES, mortar=STONE_MORTAR, studs=False, bh=16, bw=16, bevel=True, grime=0.0, darker=None):
    """Grey stone blocks a block square (16 px), each a tone of its own (darker: about one in six that tone), bevelled
    and shaded (see _stone_block); rows staggered by half a block; studs: an iron stud in some blocks. bevel=False: the
    flatter dressed stone inside the keep."""
    u, v, w, h = region
    for by in range(0, h, bh):
        off = (bw // 2) if (by // bh) % 2 else 0
        for bx in range(-off, w, bw):
            base = _stone_tone(rng, tones, darker)
            if bevel:
                _stone_block(px, u, v, bw, bh, base, rng, mortar, stud=studs and rng.random() < 0.55, x0=bx, y0=by, clip=(w, h), grime=grime)
                continue
            for y in range(bh):
                for x in range(bw):
                    X, Y = bx + x, by + y
                    if not (0 <= X < w and 0 <= Y < h):
                        continue
                    if x == 0 or y == bh - 1:
                        c = _rgb(mortar)
                    else:
                        k = 1.0 + (0.1 if y == 0 else 0.05 if y == 1 else 0) - (0.1 if y == bh - 2 else 0) + (0.05 if x == 1 else 0) \
                            - (0.06 if x == bw - 1 else 0) + 0.03 * math.sin(x * 1.3 + y * 0.7) + 0.08 * (_fbm(u + X, v + Y, 31) - 0.5)
                        c = _scale(base, k)
                    px[u + X, v + Y] = _jitter(c, rng, 4) + (255,)


def _stone_tiles(px, rng):
    """The single blocks of STONE_TILES (normal, studded, dark, light, grimy), a tone each."""
    for k in range(N_SB):
        u, v, w, h = REGIONS["sb_%d" % k]
        _stone_block(px, u, v, w, h, _scale(_rgb(STONE_DARKER if k % 6 == 5 else STONE_TONES[k % 6]), rng.uniform(0.92, 1.08)), rng, STONE_MORTAR)
    for k in range(N_SBS):
        u, v, w, h = REGIONS["sbs_%d" % k]
        _stone_block(px, u, v, w, h, _scale(_rgb(STONE_DARKER if k % 6 == 5 else STONE_TONES[(2 * k + 1) % 6]), rng.uniform(0.94, 1.06)), rng,
                     STONE_MORTAR, stud=True)
    for k in range(N_SBD):
        u, v, w, h = REGIONS["sbd_%d" % k]
        _stone_block(px, u, v, w, h, _scale(_rgb(STONE_DARK[k % 4]), rng.uniform(0.95, 1.05)), rng, "151210", grime=0.35)
    for k in range(N_SBL):
        u, v, w, h = REGIONS["sbl_%d" % k]
        _stone_block(px, u, v, w, h, _scale(_rgb(STONE_LIGHT[k % 3]), rng.uniform(0.96, 1.04)), rng, "3a352f")
    for k in range(N_SBG):
        u, v, w, h = REGIONS["sbg_%d" % k]
        _stone_block(px, u, v, w, h, _scale(_rgb(STONE_TONES[(3 * k) % 6]), rng.uniform(0.86, 0.96)), rng, STONE_MORTAR, grime=1.0)


def _boards(px, region, tones, seam, rng, plank_h=4, butt=(22, 46), grain=0.07, nails=True, knots=0.18, shade=None, worn=0.0,
            vertical=False, tint=None, edge=0.11):
    """Planks along u (along v if vertical), plank_h px wide: a tone per plank and per length between its butt joints
    (phase 6: within a few per cent, so that the hull does not speckle from afar), the grain (a streak and a stretched
    noise), a lit upper edge, a dark seam under it, butt joints, a dark brown nail head beside every other one (nails),
    a knot now and then, rubbed spots (worn); shade(fy): a brightness factor down the region (the shading baked in for
    the face it covers); tint: (colour, amount) mixed in down the region (fy) for wet or grimy planks; edge: how much
    lighter the upper edge of each plank is."""
    u, v, w, h = region
    s = rng.randrange(1 << 20)
    seam = _rgb(seam)
    tones = [_rgb(t) for t in tones]
    L, A = (h, w) if vertical else (w, h)
    for r in range((A + plank_h - 1) // plank_h):
        base = _scale(rng.choice(tones), rng.uniform(0.96, 1.04))     # (phase 6: half the spread, less speckle from afar)
        cuts, pos = [], rng.randrange(2, butt[1])
        while pos < L:
            cuts.append(pos)
            pos += rng.randrange(*butt)
        segs = [_scale(base, rng.uniform(0.975, 1.025)) for _ in range(len(cuts) + 1)]
        nailed = cuts[r % 2::2]                                           # nails on every other butt joint
        f1, p1 = rng.uniform(0.12, 0.3), rng.uniform(0, 6.28)
        knot = (rng.randrange(L), rng.uniform(0.8, 1.6)) if rng.random() < knots else None
        for a in range(L):
            seg = sum(1 for c_ in cuts if c_ <= a)
            tone = segs[seg]
            for b in range(plank_h):
                yy = r * plank_h + b
                if yy >= A:
                    continue
                if b == plank_h - 1:
                    c = seam
                elif a in cuts:
                    c = _mix(seam, tone, 0.3)
                else:
                    n = _fbm(a * 0.45, yy * 2.2, s)
                    k = 1.0 + grain * math.sin(a * f1 + p1 + b * 1.9) + 0.13 * (n - 0.5)
                    k += edge if b == 0 else 0
                    k -= 0.08 if b == plank_h - 2 else 0
                    k += 0.06 if (a - 1) in cuts else 0
                    k -= 0.08 if (a + 1) in cuts else 0
                    c = _scale(tone, k)
                    if knot is not None:
                        d = math.hypot((a - knot[0]) * 0.6, b - plank_h / 2 + 0.5)
                        if d < knot[1]:
                            c = _scale(tone, 0.6)
                        elif d < knot[1] + 1.0:
                            c = _scale(tone, 0.84)
                    if nails and b == max(0, plank_h // 2 - 1) and ((a - 2) in nailed or (a + 2) in nailed):
                        c = _mix(seam, tone, 0.35)                        # a dark brown nail head, read as a joint
                    if worn and _hash(a, yy, s + 9) < worn:
                        c = _scale(c, 1.14)
                X, Y = (yy, a) if vertical else (a, yy)
                fy = (Y + 0.5) / h
                if shade is not None:
                    c = _scale(c, shade(fy))
                if tint is not None:
                    c = _mix(c, _rgb(tint[0]), tint[1] * fy)
                px[u + X, v + Y] = _jitter(c, rng, 3) + (255,)


def _strake5(px, region, tones, seam, rng, shade=None, tint=None, wet=None):
    """One hull strake stretched on each board (two planks high): a dark seam along the top, the bottom and between the
    two planks, a lit edge under each seam, the grain, butt joints with nail heads; shade(fy) baked in (the shadow
    under the stone wale), tint (colour, amount) rising towards the foot (the wet planks at the waterline); wet: the
    tint only in that many rows at the foot (phase 6: a narrow wet band, the strake as bright as before above it)."""
    u, v, w, h = region
    s = rng.randrange(1 << 20)
    seam = _rgb(seam)
    tones = [_rgb(t) for t in tones]
    ph = h // 2
    for r in range(2):
        base = _scale(rng.choice(tones), rng.uniform(0.96, 1.04))
        cuts = sorted(rng.sample(range(8, w - 8), 2))
        segs = [_scale(base, rng.uniform(0.97, 1.03)) for _ in range(3)]
        f1, p1 = rng.uniform(0.1, 0.22), rng.uniform(0, 6.28)
        for x in range(w):
            seg = sum(1 for c_ in cuts if c_ <= x)
            for b in range(ph):
                y = r * ph + b
                if b == ph - 1 or (r == 0 and b == 0):
                    c = seam
                elif x in cuts:
                    c = _mix(seam, segs[seg], 0.3)
                else:
                    k = 1.0 + 0.06 * math.sin(x * f1 + p1 + b * 1.3) + 0.12 * (_fbm(x * 0.4, y * 2.0, s) - 0.5)
                    k += 0.1 if b == (1 if r == 0 else 0) else 0
                    k -= 0.07 if b == ph - 2 else 0
                    c = _scale(segs[seg], k)
                    if b == ph // 2 and (x - 2) in cuts:
                        c = _mix(seam, segs[seg], 0.35)
                fy = (y + 0.5) / h
                if shade is not None:
                    c = _scale(c, shade(fy))
                if tint is not None and wet:
                    c = _mix(c, _rgb(tint[0]), tint[1] * max(0.0, (y - (h - 1 - wet)) / wet))
                elif tint is not None:
                    c = _mix(c, _rgb(tint[0]), tint[1] * fy * fy)
                px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


RED_BOARD = ("b52c2f", "aa282d", "bf3033", "a3262c", "b02a2d", "ba2e30")
RED_CELL = "c43826"     # (phase 6-7) the bright warm red of the main reference's panel blocks


def _red_panel(px, region, rng):
    """The red panels between the ribs (main reference, phase 6): square bevelled red blocks, one a block (16 px), a
    value of their own (within 8 %), a lit top and left edge, a dark bottom and right edge, a faintly mottled face, no
    nails; a dark iron border along the panel's top and foot, the top rows in the shade of the studded band and the
    stone belt, the foot a little darker on the stone wale."""
    u, v, w, h = region
    s = rng.randrange(1 << 20)
    base0 = _rgb(RED_CELL)
    for by in range(0, h, 16):
        for bx in range(0, w, 16):
            base = _scale(base0, rng.uniform(0.92, 1.08))
            base = (min(255, base[0] + rng.randint(-4, 4)), base[1], base[2])
            for y in range(16):
                for x in range(16):
                    X, Y = bx + x, by + y
                    n = _fbm(u + X, v + Y, s, cell=5.0)
                    k = 1.0 + 0.12 * (n - 0.5) - 0.05 * y / 16
                    if x == 15 or y == 15:
                        c = _scale(base, 0.42)                  # the dark joint (bottom and right)
                    else:
                        if y == 0 or x == 0:
                            k += 0.2                            # the lit top and left edge
                        elif y == 1 or x == 1:
                            k += 0.07
                        if y == 14 or x == 14:
                            k -= 0.22                           # the shadowed bottom and right edge
                        c = _scale(base, k)
                        if _hash(u + X, v + Y, s + 3) < 0.03:
                            c = _scale(c, 0.85)
                    k2 = 1.0
                    if Y < 2 or Y >= h - 2:
                        c = _rgb("2c2016") if Y in (0, h - 1) else _rgb("3a2c20")    # the walnut border (phase 8)
                    else:
                        if Y < 6:
                            k2 = 0.7 + 0.075 * (Y - 2)
                        if Y >= h - 4:
                            k2 *= 0.88
                    px[u + X, v + Y] = _jitter(_scale(c, k2), rng, 2) + (255,)


def _stud_post(px, region, rng):
    """The frame post beside each rib (phase 8, main reference: the red cells sit in dark walnut frames with silver
    studs): dark walnut with its grain (stretched across the post, a block = 16 px down it), a lit left bevel, a dark
    right edge and a dark joint a block, a column of silver domed studs down the middle, two a block, each with its
    shadow."""
    u, v, w, h = region
    s = rng.randrange(1 << 20)
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("3a2c20"), 1.0 + 0.05 * math.sin(y * 0.9 + x * 0.3) + 0.16 * (_fbm(x * 2, y * 0.5, s) - 0.5)
                       + (0.4 if x == 0 else 0.16 if x == 1 else 0) - (0.3 if x == w - 1 else 0.14 if x == w - 2 else 0)
                       - (0.3 if y % 16 == 15 else 0))
            for cx in (7.5,):
                for cy in (4.5, 12.5):
                    bc = _boss(x - cx, (y % 16) - cy, 1.9, "c4c4cc")
                    if bc == "shadow":
                        c = _scale(c, 0.6)
                    elif bc is not None:
                        c = bc
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _iron_rail(px, region, rng):
    """The iron rail along the top and the foot of a red panel (phase 7): hammered dark iron, a lit top bevel, a dark
    foot, a bright domed rivet every 16 px (one a block when stretched over a three-block panel)."""
    u, v, w, h = region
    s = rng.randrange(1 << 20)
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("34343a"), 1.0 + 0.16 * (_fbm(x * 0.7, y * 2, s) - 0.5) + (0.45 if y == 0 else 0.15 if y == 1 else 0)
                       - (0.35 if y == h - 1 else 0.14 if y == h - 2 else 0))
            bc = _boss((x % 16) - 7.5, y - (h - 1) / 2, 1.9, "9a9aa2")
            if bc == "shadow":
                c = _scale(c, 0.6)
            elif bc is not None:
                c = bc
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


RIB_PLATE_W = 0.42      # (phase 6) the plate's width on the rib (blocks): the region is stretched across it


def _rib_plate(px, region, rng):
    """The black iron plate on a stone rib (stretched across the plate, a block = 16 px down it), drawn for its real
    width RIB_PLATE_W so that its bosses stay round: hammered dark iron, a lit top and left bevel, a dark bottom and
    right edge, a big domed boss in each block with its glint and shadow, a small rivet above and below it, rust
    bleeding from some of them."""
    u, v, w, h = region
    s = rng.randrange(1 << 20)
    sx = RIB_PLATE_W * 16 / w          # physical px per texture px across
    for y in range(h):
        yb = y % 16
        for x in range(w):
            X = (x + 0.5) * sx                       # across the plate, in physical px
            Wp = w * sx
            c = _scale(_rgb("2e2e33"), 1.0 + 0.16 * (_fbm(x * 1.5 * sx, y * 1.5, s) - 0.5))
            if X < 1.0 or yb == 0:
                c = _rgb("5e5e66")
            elif X < 2.0 or yb == 1:
                c = _scale(c, 1.25)
            elif X > Wp - 1.0 or yb == 15:
                c = _rgb("101012")
            elif X > Wp - 2.0 or yb == 14:
                c = _scale(c, 0.72)
            bc = _boss(X - Wp / 2, yb - 7.5, 2.4, "56565e")
            if bc == "shadow":
                c = _scale(c, 0.6)
            elif bc is not None:
                c = bc
            for ry in (2.5, 12.5):
                rc = _boss(X - Wp / 2, yb - ry, 0.9, "4a4a50")
                if rc not in (None, "shadow"):
                    c = rc
                elif abs(X - Wp / 2) < 0.6 and ry < yb <= ry + 2.5 and _hash(x, y // 16 * 16 + int(ry), s) < 0.4:
                    c = _mix(c, _rgb("6a3a1e"), 0.5)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _stud_head(px, region, rng):
    """The face of a stud cube: a domed iron head filling the face."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            bc = _boss(x - (w - 1) / 2, y - (h - 1) / 2, w / 2 - 0.3, "6e6e74")
            c = bc if bc not in (None, "shadow") else _rgb("2a2a2e")
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _arch_inside(x, y, w, h, r=None):
    """Inside an arch w wide (round top of radius w / 2) and h high?"""
    r = w / 2 if r is None else r
    cx = (w - 1) / 2
    if y >= r:
        return abs(x - cx) <= w / 2
    return (x - cx) ** 2 + (y - r) ** 2 <= r * r


def _glow(x, y, w, h, cy=0.66):
    """Warm window light: pale gold low in the middle, deep amber at the edges."""
    d = math.hypot(x - w / 2 + 0.5, (y - h * cy) * 0.8) / (w / 2)
    return _mix(_rgb("fff3bc"), _rgb("d97a22"), min(1.0, d * 1.1))


def _arch_window(px, region, rng, lit=True):
    """An arched window (third reference): a heavy dark wooden frame following the round top (lit on its upper left,
    shadowed on its lower right), a mullion and a transom, leaded panes; warm light, brightest low in the middle of the
    window and in each pane, or dark panes with a faint sheen; transparent outside the arch."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            if not _arch_inside(x, y + 0.5, w, h):
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            inner = _arch_inside(x - 3, y - 3, w - 6, h - 6) and 3 <= x < w - 3 and 3 <= y < h - 3
            bar = abs(x - (w - 1) / 2) < 1.2 or abs(y - h * 0.58) < 1.2
            if not inner:
                rim = _arch_inside(x - 1, y - 1, w - 2, h - 2) and 1 <= x < w - 1
                c = _rgb("3a2414") if rim else _rgb("1e1209")
                if rim and (x < w / 2 - 2 and y < h * 0.7):
                    c = _scale(c, 1.3)
                elif rim and x > w / 2 + 2:
                    c = _scale(c, 0.8)
            elif bar:
                c = _rgb("4a2e18") if (x + y) % 5 else _rgb("5a3a20")
            elif lit:
                c = _glow(x, y, w, h)
                qx, qy = (x - 3) % 5, (y - 3) % 6        # leaded quarries
                if qx == 0 or qy == 0:
                    c = _scale(c, 0.72)
                elif qy == 5:
                    c = _scale(c, 1.06)
            else:
                c = _mix(_rgb("3a3020"), _rgb("221d14"), y / h)
                if (x - y) % 9 == 0:
                    c = _scale(c, 1.25)
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _arch_ring(px, region, rng):
    """The stone surround of an arched window: wedge-shaped voussoirs round the top, jamb blocks down the sides, a sill
    at the foot, each stone mottled, lit on its outer edge and shadowed on its inner one (the reveal); open
    (transparent) where the window is."""
    u, v, w, h = region
    s = rng.randrange(1 << 20)
    R, r = w / 2, w / 2 - 8          # outer and inner radius of the arch
    cx, cy = (w - 1) / 2, R
    sill = h - 5
    tones = [_scale(_rgb(rng.choice(STONE_LIGHT)), rng.uniform(0.84, 1.0)) for _ in range(16)]
    for y in range(h):
        for x in range(w):
            outer = _arch_inside(x, y, w, h)
            hole = y < sill and (abs(x - cx) < r if y >= cy else (x - cx) ** 2 + (y - cy) ** 2 < r * r)
            if not outer or hole:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            n = 1.0 + 0.16 * (_fbm(u + x, v + y, s) - 0.5)
            if y >= sill:
                k = 1.0 + (0.24 if y == sill else 0) - (0.3 if y == h - 1 else 0.12 if y == h - 2 else 0)
                c = _scale(tones[0], k * n) if x % 12 != 11 else _rgb("3a352f")
            elif y < cy:   # voussoirs: wedges every 22.5 degrees
                a = math.degrees(math.atan2(cy - y, x - cx))
                seg = int(a // 22.5)
                d = math.hypot(x - cx, y - cy)
                c = _scale(tones[seg % 16], n * (1.0 + 0.2 * (d > R - 1.5) - 0.3 * (d < r + 1.2) - 0.12 * (d < r + 2.4)))
                if abs((a % 22.5)) < 2.2 or abs((a % 22.5) - 22.5) < 2.2:
                    c = _rgb("3a352f")
            else:          # jambs: blocks 12 px high
                seg = int((y - cy) // 12)
                inside = abs(x - cx) < r + 1.5
                c = _scale(tones[(seg + 5 + (x > cx) * 3) % 16], n * (1.0 + (0.22 if (y - cy) % 12 < 1 else 0) - (0.24 if (y - cy) % 12 >= 10 else 0)
                                                                      - (0.28 if inside else 0)))
                if (y - cy) % 12 >= 11:
                    c = _rgb("3a352f")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _keep_panel(px, region, rng):
    """A red panel framed in dark wood with a domed iron stud in each corner (the keep's walls): the frame lit on its top
    and left, shadowed on its bottom and right; the red boards inside in the frame's shadow along their top and left
    (sunk in the frame)."""
    u, v, w, h = region
    s = rng.randrange(1 << 20)
    for y in range(h):
        for x in range(w):
            fr = x < 4 or x >= w - 4 or y < 4 or y >= h - 4
            if fr:
                c = _scale(_rgb("2e1d10"), 1.0 + 0.06 * math.sin(x + y * 0.5) + 0.12 * (_fbm(x, y, s) - 0.5))
                if x in (0, w - 1) or y in (0, h - 1):
                    c = _rgb("170e06")
                elif y == 1 or x == 1:
                    c = _scale(c, 1.35)
                elif y == h - 2 or x == w - 2:
                    c = _scale(c, 0.7)
                for sx_, sy_ in ((2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)):
                    bc = _boss(x - sx_, y - sy_, 1.3)
                    if bc not in (None, "shadow"):
                        c = bc
            else:
                bx, by = (x - 4) % 8, (y - 4) % 12
                c = _scale(_rgb(("a3282b", "98242a", "ad2c2f")[((x - 4) // 8 + (y - 4) // 12) % 3]),
                           1.0 + (0.12 if by == 0 else 0) - (0.16 if by == 10 else 0) - (0.1 if bx == 6 else 0) + 0.12 * (_fbm(x, y * 3, s + 1) - 0.5))
                if bx == 7 or by == 11:
                    c = _rgb("380b0d")
                if y < 6 or x < 6:
                    c = _scale(c, 0.68 if min(x, y) < 5 else 0.84)
                elif y >= h - 5 or x >= w - 5:
                    c = _scale(c, 1.06)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _studs(px, region, rng, top_shade=False):
    """Dark planks along u (four a block, a tone each, lit upper edges, dark seams) with small domed iron studs (phase 6:
    dark iron with a single glint, one a block, staggered by half a block from one row of blocks to the next) and the
    shadow each casts (the band under the stone belt, main reference); top_shade: the upper row, darker under the stone
    belt that overhangs it."""
    u, v, w, h = region
    s = rng.randrange(1 << 20)
    tones = [_scale(_rgb(rng.choice(("58381f", "503220", "604025", "543622"))), rng.uniform(0.95, 1.05)) for _ in range(h // 4 * (w // 16))]
    for y in range(h):
        for x in range(w):
            b = y // 4
            t = tones[(b * (w // 16) + x // 16) % len(tones)]
            if y % 4 == 3:
                c = _rgb("1a1009")
            elif x % 16 == 15 and (b % 2 == 0):
                c = _rgb("21150b")
            else:
                c = _scale(t, 1.0 + 0.06 * math.sin(x * 0.3 + y * 1.1) + 0.12 * (_fbm(x * 0.5, y * 2, s) - 0.5) + (0.1 if y % 4 == 0 else 0))
            sx_ = 7 if (y // 16) % 2 == 0 else 15
            dx_, dy_ = (x - sx_) % 16, y % 16 - 6
            dx_ = dx_ - 16 if dx_ > 8 else dx_
            sc = _stud_px(dx_, dy_)
            if sc is not None:
                c = sc
            elif (dx_ == 3 and 1 <= dy_ <= 3) or (dy_ == 3 and 1 <= dx_ <= 3):
                c = _scale(c, 0.6)
            if top_shade and y < 7:
                c = _scale(c, 0.55 + 0.065 * y)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _iron_strap(px, region, rng):
    """A black iron strap: hammered iron, a lit left edge and a dark right edge, a domed rivet every half block."""
    u, v, w, h = region
    s = rng.randrange(1 << 20)
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("2e2e31"), 1.0 + 0.07 * math.sin(y * 0.5 + x) + 0.14 * (_fbm(x, y, s) - 0.5))
            if x == 0:
                c = _rgb("5a5a60")
            elif x == w - 1:
                c = _rgb("121214")
            bc = _boss(x - (w - 1) / 2, (y % 8) - 3.5, 1.7)
            if bc == "shadow":
                c = _scale(c, 0.6)
            elif bc is not None:
                c = bc
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _roof_tile(px, region, rng):
    """Rows of red rounded tiles (8 px high), each 8 px wide, shifted every row: each tile lit on its left flank and
    crown, shadowed on its right flank, a dark lip under it (the next row's shadow), a tone of its own, a little
    weathering."""
    u, v, w, h = region
    s = rng.randrange(1 << 20)
    for y in range(h):
        row = y // 8
        for x in range(w):
            off = 4 if row % 2 else 0
            tx, ly = (x + off) % 8, y % 8
            tid = (x + off) // 8 + row * 13
            base = _scale(_rgb(("a8302a", "b33a30", "9a2a26", "bd4234", "a3342c")[int(_hash(tid, row, s) * 5)]), 0.94 + 0.12 * _hash(tid, row, s + 1))
            c = _scale(base, 1.12 - 0.06 * ly + 0.16 * math.cos((tx - 2.5) / 4.0 * math.pi / 1.6) + 0.1 * (_fbm(x, y, s + 2) - 0.5))
            if ly == 7:
                c = _rgb("3a120e")
            elif ly == 6:
                c = _scale(c, 0.7)
            elif tx == 7:
                c = _scale(base, 0.6)
            elif ly == 0:
                c = _scale(c, 1.12)
            if _hash(x, y, s + 3) > 0.97:
                c = _mix(c, _rgb("6a5a40"), 0.4)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _tile_edge(px, region, rng):
    """The roof's eaves: a red tile lip (lit on top, a dark drip edge) over a grey stone band, blocks with joints."""
    u, v, w, h = region
    s = rng.randrange(1 << 20)
    for y in range(h):
        for x in range(w):
            if y < 4:
                c = _scale(_rgb("a8302a"), 1.12 - 0.06 * y + 0.08 * math.cos((x % 8 - 3.5) / 4 * math.pi / 1.6))
                if y == 3:
                    c = _rgb("3a120e")
            else:
                c = _scale(_rgb(("a3a29c", "8f8e88", "b2b1aa")[(x // 16) % 3]), 1.0 + (0.16 if y == 4 else 0) - (0.2 if y == h - 1 else 0.08 if y == h - 2 else 0)
                           + 0.14 * (_fbm(x, y, s) - 0.5) - 0.12 * (y == 5))
                if x % 16 == 0:
                    c = _rgb("3a3936")
                elif x % 16 == 1:
                    c = _scale(c, 1.12)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _timber(px, region, rng):
    """Dark vertical boards (a tone each, the grain, a lit left edge, a dark seam) between darker corner posts (the
    turret's walls), a nail head top and bottom of each board."""
    u, v, w, h = region
    s = rng.randrange(1 << 20)
    base = _rgb("4a3020")
    for x in range(w):
        if x % 4 == 0:
            base = _scale(_rgb(rng.choice(("4a3020", "432b1c", "513524", "3e2818"))), rng.uniform(0.92, 1.08))
        for y in range(h):
            c = _scale(base, 1.0 + 0.05 * math.sin(y * 0.5 + x) + 0.14 * (_fbm(x * 2, y * 0.4, s) - 0.5) + (0.1 if x % 4 == 0 else 0))
            if x % 4 == 3:
                c = _rgb("21140a")
            if x < 3 or x >= w - 3:
                c = _scale(_rgb("2e1d10"), 1.0 + 0.04 * math.sin(y) + (0.18 if x in (0, w - 3) else 0) - (0.2 if x in (2, w - 1) else 0))
            elif x % 4 == 1 and y % 16 in (2, 13):
                c = _rgb("2a1a0e")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _lamp_glass(px, region):
    """The lanterns' glass (phase 8; the game draws it full bright): a thin dark frame, a 2 px pale rim, the pane a warm
    amber glow brighter round the flame, as the big warm lanterns of the main reference."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            if x in (0, w - 1) or y in (0, h - 1):
                c = (40, 36, 34)
            elif x in (1, 2, w - 2, w - 3) or y in (1, 2, h - 2, h - 3):
                c = (255, 216, 144)
            else:
                d = ((x - w / 2 + 0.5) ** 2 + ((y - h * 0.58) * 0.8) ** 2) ** 0.5
                c = (255, 244, 196) if d < 2.2 else (255, 206, 96) if d < 4.0 else (255, 182, 64)
            px[u + x, v + y] = c + (255,)


def _window(px, region, rng, lit=True):
    """A window in a heavy dark wooden frame (lit on its top and left inner edge, shadowed on its bottom and right),
    four panes with leading; lit: warm light, brightest low in the middle of each pane."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            frame = x < 4 or x >= w - 4 or y < 4 or y >= h - 4
            bar = abs(x - w / 2 + 0.5) < 1.5 or abs(y - h / 2 + 0.5) < 1.5
            if frame:
                c = _rgb("3a2414") if not (x in (0, w - 1) or y in (0, h - 1)) else _rgb("1e1209")
                if x in (1, 2) and 0 < y < h - 1 or y in (1, 2) and 0 < x < w - 1:
                    c = _scale(c, 1.3)
                elif x == 3 or y == 3:
                    c = _scale(c, 0.7)
            elif bar:
                c = _rgb("4a2e18")
            elif lit:
                px_, py_ = (x - 4) % ((w - 8) // 2), (y - 4) % ((h - 8) // 2)
                pw, ph_ = (w - 8) // 2, (h - 8) // 2
                c = _mix(_glow(x, y, w, h, 0.62), _glow(px_, py_, pw, ph_, 0.7), 0.4)
                if (x - y) % 4 == 0:
                    c = _scale(c, 0.9)
            else:
                c = _mix(_rgb("3a3020"), _rgb("2a2418"), y / h)
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _tower_shade(mask, x, y, d=2):
    """Bevel of the tower emblem at (x, y) (inside the mask): +1 near its top / left edge, -1 near its bottom / right."""
    W_, H_ = mask.size
    inside = (lambda X, Y: 0 <= X < W_ and 0 <= Y < H_ and mask.getpixel((X, Y)) > 0)
    if not inside(x - d, y) or not inside(x, y - d):
        return 1
    if not inside(x + d, y) or not inside(x, y + d):
        return -1
    return 0


def _banner(px, region, rng, shield=False):
    """Red banner (32 px a block) with a beige tower in a dark outline, its masonry and its bevel painted, cloth folds
    down its length, a pale border with a dark inner line, a dark rod sleeve, a pointed foot (transparent around the
    point); or a heater shield (round-bottomed point): its red field lit on the upper left, the tower in white stone, a
    gold rim with a bright inner line, a dark outer line and rivets."""
    u, v, w, h = region
    s = rng.randrange(1 << 20)
    red = _rgb("b02529")
    mw = int(w * (0.62 if shield else 0.6))
    mask = tower_mask(mw, mw + mw // 6)
    mx, my = (w - mask.width) // 2, int(h * (0.24 if shield else 0.18))
    cell = max(1, min(mask.width // 12, mask.height // 14))
    emb = _rgb(BEIGE) if not shield else _rgb("e8e6e0")

    def in_mask(X, Y):
        return mx <= X < mx + mask.width and my <= Y < my + mask.height and mask.getpixel((X - mx, Y - my)) > 0
    for y in range(h):
        for x in range(w):
            fx = (x + 0.5) / w
            if shield:
                t = max(0.0, (y - h * 0.45) / (h * 0.55))
                half = 0.5 * math.sqrt(max(0.0, 1 - t ** 1.8))
                inside = abs(fx - 0.5) <= half and y < h - 1
                dist = (half - abs(fx - 0.5)) * w if inside else -1
                edge = inside and (dist < 6 or y < 6 or y >= h - 6)
                outer = inside and (dist < 1.5 or y < 1 or y >= h - 2)
            else:
                foot = h * 0.78
                half = 0.5 if y < foot else 0.5 * (1 - (y - foot) / (h - foot))
                inside = abs(fx - 0.5) <= half + 1e-9
                dist = (half - abs(fx - 0.5)) * w
                edge = inside and (dist < 5 or y < 6)
                outer = inside and dist < 1.2
            if not inside:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            fold = math.sin(fx * math.pi * (5 if not shield else 1) + 0.6) if not shield else 0.0
            k = 1.0 + 0.1 * fold - 0.1 * (y / h) + 0.08 * (_fbm(x, y, s) - 0.5)
            if shield:
                k += 0.12 * (1 - fx - y / h)
            c = _scale(red, k)
            if outer:
                c = _rgb("3a1a0e") if shield else _rgb("6a5a40")
            elif edge:
                if shield:
                    c = _scale(_rgb("d8a63a"), 1.0 + (0.3 if 2 <= dist < 3.5 or 1 <= y < 3 else 0) - (0.25 if dist >= 5 or y >= h - 3 else 0))
                    if (x + 3 * y) % 23 == 0 and dist < 4:
                        c = _rgb("6e5210")
                else:   # (phase 7) a gold fringe: a bright line inside a darker edge
                    c = _scale(_rgb("d9b95e"), 1.0 + 0.08 * fold + (0.22 if 1.2 <= dist < 2.6 and y >= 6 else 0) - (0.3 if dist >= 4 or y < 6 else 0))
            elif in_mask(x, y):
                sh = _tower_shade(mask, x - mx, y - my)
                c = _scale(emb, 1.0 + 0.08 * fold + 0.14 * sh)
                ly, lx = (y - my) % (2 * cell), (x - mx + (cell if ((y - my) // (2 * cell)) % 2 else 0)) % (3 * cell)
                if ly == 0 or lx == 0:
                    c = _scale(c, 0.84)
            elif any(in_mask(x + dx, y + dy) for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-2, 0), (0, -2), (2, 0), (0, 2))):
                c = _scale(red, 0.45)       # the outline (and the shadow in the windows and the gate)
            elif mx <= x < mx + mask.width and my + mask.height * 0.35 <= y < my + mask.height:
                c = _scale(c, 0.8)          # inside the windows and the gate: in shadow
            if not shield and y < 6:
                c = _scale(_rgb("3a2414"), 1.25 if y < 2 else 0.85)   # the rod sleeve
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _pennant(px, region, rng):
    """Red pennant, long swallow tail cut in steps (transparent notch), darker at the hoist, soft folds along it, the
    white tower at the hoist in a dark outline (phase 7)."""
    u, v, w, h = region
    mask = tower_mask(12, 14, 1)
    mx, my = 3, (h - 14) // 2
    for y in range(h):
        for x in range(w):
            fx = x / w
            notch = fx > 0.62 and abs(y - h / 2 + 0.5) < (fx - 0.62) / 0.38 * (h / 2 - 1)
            taper = abs(y - h / 2 + 0.5) > (h / 2) * (1 - 0.45 * fx)
            if notch or taper:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            c = _scale(_rgb("b8262b"), 1.0 + 0.12 * math.sin(x * 0.45 + 0.8) - 0.08 * (x < 3) - 0.06 * (y / h))
            if mx <= x < mx + 12 and my <= y < my + 14 and mask.getpixel((x - mx, y - my)):
                c = _rgb("ece6d6")
            elif any(mx <= x + dx < mx + 12 and my <= y + dy < my + 14 and mask.getpixel((x + dx - mx, y + dy - my))
                     for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))):
                c = _scale(c, 0.5)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _gold5(px, region, rng):
    """Gilding: bands across (a dark outline, a bright highlight line, the body, a shadow band low), sparkles."""
    u, v, w, h = region
    s = rng.randrange(1 << 20)
    for y in range(h):
        fy = y / max(1, h - 1)
        for x in range(w):
            c = _mix(_rgb("e6b84a"), _rgb("9c6f22"), min(1.0, max(0.0, fy * 1.2 - 0.1)))
            c = _scale(c, 1.0 + 0.1 * (_fbm(x, y, s) - 0.5) + 0.06 * math.sin(x * 0.7))
            if y == 0 or y == h - 1:
                c = _rgb("5e4410")
            elif y == 1:
                c = _rgb("fbe08a")
            elif y == h - 2:
                c = _rgb("7a5418")
            if _hash(x, y, s + 1) > 0.975:
                c = _rgb("fff0b8")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _iron5(px, region, rng, base="38393c"):
    """Dark iron: hammered (mottled), a lit top row and a dark bottom row."""
    u, v, w, h = region
    s = rng.randrange(1 << 20)
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb(base), 1.0 + 0.18 * (_fbm(x, y, s) - 0.5) + (0.2 if y == 0 else 0) - (0.22 if y == h - 1 else 0))
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _wall_stone(px, region, rng):
    """Inside the keep and the turret: dressed stone blocks over a wooden dado and a skirting board."""
    u, v, w, h = region
    _stone(px, (u, v, w, h), rng, tones=("8e8b84", "807d76", "96938b"), mortar="4a4740", bevel=False)
    for y in range(int(h * 0.62), h):
        for x in range(w):
            c = _scale(_rgb("5a3a20"), 1.0 + 0.05 * math.sin(x * 0.4 + y))
            if x % 16 == 0 or y == int(h * 0.62) or y == h - 1:
                c = _rgb("2a1a0d")
            if y in (int(h * 0.62) + 1, int(h * 0.62) + 2):
                c = _rgb("a8262a")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _tower_rug(px, region, rng):
    """The red carpet of the captain's cabin and the council room: a dark red field, a grey stone-coloured border
    with a gold band inside it, small gold corner squares and the white tower in the middle."""
    u, v, w, h = region
    mask = tower_mask(int(w * 0.5), int(w * 0.5) + int(w * 0.5) // 6)
    mx, my = (w - mask.width) // 2, (h - mask.height) // 2
    for y in range(h):
        for x in range(w):
            d = min(x, y, w - 1 - x, h - 1 - y)
            if d < 1:
                c = _rgb("3a3936")
            elif d < 5:
                c = _rgb(("8f8e88", "a3a29c")[((x // 4) + (y // 4)) % 2])
            elif d < 7:
                c = _rgb("c9981f")
            else:
                c = _scale(_rgb("8e1c20"), 1.0 + 0.05 * math.sin(x * 0.9 + y * 0.6))
                corner = (min(x, w - 1 - x) < 14 and min(y, h - 1 - y) < 14 and min(x, w - 1 - x) >= 9 and min(y, h - 1 - y) >= 9)
                if corner:
                    c = _rgb("c9981f")
                if d == 9 and (x + y) % 4 == 0:
                    c = _rgb("6e1418")
            if mx <= x < mx + mask.width and my <= y < my + mask.height and mask.getpixel((x - mx, y - my)):
                c = _rgb("e2ded2")
            px[u + x, v + y] = _jitter(c, rng, 4) + (255,)


def _war_map(px, region, rng):
    """The campaign map: yellowed parchment, the sea in grey blue on the left with wave strokes, a ragged coast, the
    fort of Havre-Fort (a small red tower) on a cove, dotted routes and a compass rose, a darker worn edge."""
    u, v, w, h = region
    coast = [int(w * 0.42 + 6 * math.sin(y * 0.35) + 4 * math.sin(y * 0.9 + 1.0)) for y in range(h)]
    small = tower_mask(10, 12, 1)
    tx, ty = coast[h // 2] - 2, h // 2 - 6
    for y in range(h):
        for x in range(w):
            edge = min(x, y, w - 1 - x, h - 1 - y)
            if x < coast[y]:
                c = _scale(_rgb("8a9a98"), 1.0 + 0.04 * math.sin(x * 0.5 + y))
                if (x + 3 * (y // 4)) % 9 == 0 and y % 4 == 1:
                    c = _rgb("6a7a7a")
            elif x < coast[y] + 2:
                c = _rgb("5a4a30")
            else:
                c = _scale(_rgb("d8c49a"), 1.0 + 0.05 * math.sin(x * 0.3 + y * 0.2))
                if (x * 7 + y * 13) % 53 == 0:
                    c = _rgb("6a7a3a")
            # routes: dotted lines from the fort out to sea
            for (x0, y0, x1, y1) in ((tx, ty + 6, 4, 6), (tx, ty + 6, 6, h - 8), (tx + 6, ty + 6, w - 8, 10)):
                t = ((x - x0) * (x1 - x0) + (y - y0) * (y1 - y0)) / max(1.0, (x1 - x0) ** 2 + (y1 - y0) ** 2)
                if 0 <= t <= 1:
                    dx, dy = x0 + t * (x1 - x0) - x, y0 + t * (y1 - y0) - y
                    if dx * dx + dy * dy < 0.6 and int(t * 20) % 2 == 0:
                        c = _rgb("6e1418")
            if tx <= x < tx + 10 and ty <= y < ty + 12 and small.getpixel((x - tx, y - ty)):
                c = _rgb("a8262a")
            # compass rose (bottom right)
            cx, cy = w - 9, h - 9
            if (abs(x - cx) <= 4 and y == cy) or (abs(y - cy) <= 4 and x == cx):
                c = _rgb("3a2a1a")
            if edge < 2:
                c = _mix(c, _rgb("7a5a32"), 0.6 if edge == 0 else 0.35)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _surcoat(px, region, rng):
    u, v, w, h = region
    mask = tower_mask(10, 12, 1)
    mx, my = (w - 10) // 2, 5
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("b02529"), 1.0 + 0.06 * math.sin(x * 0.8 + y * 0.4) - 0.1 * (y / h))
            if mx <= x < mx + 10 and my <= y < my + 12 and mask.getpixel((x - mx, y - my)):
                c = _rgb("e2ded2")
            if y >= h - 3:
                c = _rgb("c9981f")
            if y < 2:
                c = _rgb("6e1418")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _shade_fill(px, region, rng, base, dark, light=None, period=4):
    """Small material: a base tone, darker every `period` rows, a lighter top row."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb(base), 1.0 + 0.06 * math.sin(x * 1.1 + y * 0.7))
            if y % period == period - 1:
                c = _mix(c, _rgb(dark), 0.5)
            if light and y == 0:
                c = _rgb(light)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _decor_materials(px, rng):
    R = REGIONS
    _tower_rug(px, R["tower_rug"], rng)
    _war_map(px, R["war_map"], rng)
    _surcoat(px, R["surcoat"], rng)
    _shade_fill(px, R["candle"], rng, "eadfc2", "cfc2a2", "f6efd8", period=16)
    _shade_fill(px, R["parchment"], rng, "e0cfa4", "8a7a5a", period=3)
    _shade_fill(px, R["bread"], rng, "b4783a", "8a5426", "d8a460", period=5)
    _shade_fill(px, R["leather"], rng, "6a4024", "3e2414", period=6)
    _shade_fill(px, R["velvet_red"], rng, "9e1c22", "6e1418", "c02a30", period=8)
    u, v, w, h = R["cheese"]
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("e2b84a"), 1.0 + 0.05 * math.sin(x + y))
            if (x * 5 + y * 3) % 17 == 0:
                c = _rgb("b08a2a")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    u, v, w, h = R["fletching"]
    for y in range(h):
        for x in range(w):
            c = _rgb("e8e6de") if not (5 <= y <= 9) else _rgb("b02529")
            if x % 4 == 0:
                c = _scale(c, 0.85)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    u, v, w, h = R["blade"]
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("aeb2b6"), 1.0 + 0.08 * math.sin(x * 0.6 + y * 0.2))
            if x in (0, w - 1):
                c = _rgb("dfe3e6")
            elif x == w // 2:
                c = _rgb("8a8e92")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)
    u, v, w, h = R["embers"]
    for y in range(h):
        for x in range(w):
            k = rng.random()
            c = _rgb("ffd27a") if k < 0.25 else _rgb("f08a2a") if k < 0.6 else _rgb("b8401a") if k < 0.85 else _rgb("3a1a10")
            px[u + x, v + y] = c + (255,)
    u, v, w, h = R["mail"]
    for y in range(h):
        for x in range(w):
            c = _rgb("6a6e72") if (x + (y % 2)) % 2 else _rgb("3a3c40")
            if y % 2 == 0 and x % 2 == 0:
                c = _rgb("9a9ea2")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _cabin_wall(px, region, rng):
    """The captain's cabin: dark panelling, a red rail and a gold cornice, lower panels."""
    u, v, w, h = region
    col = _rgb("5a3a20")
    for x in range(w):
        if x % 8 == 0:
            col = _scale(_rgb(rng.choice(("5e3c22", "553620", "66422a", "5a3a1e"))), rng.uniform(0.94, 1.06))
        for y in range(h):
            if x % 8 == 7:
                c = _rgb("2a1a0d")
            else:
                c = _scale(col, 1.0 + 0.05 * math.sin(y * 0.35 + x))
            if y in (2, 3):
                c = _rgb("c9981f") if (x + y) % 7 else _rgb("e0b230")
            elif 38 <= y <= 40:
                c = _rgb("a8262a")
            elif y > 40 and (x % 16 in (2, 13) or y in (44, 60)):
                c = _scale(c, 0.8)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def make_texture(path):
    rng = random.Random(1214)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()
    R = REGIONS
    _stone(px, R["stone"], rng, darker=STONE_DARKER)
    _stone(px, R["stone_dark"], rng, tones=STONE_DARK, mortar="151210", grime=0.35)
    _stone(px, R["stone_stud"], rng, studs=True, darker=STONE_DARKER)
    _stone(px, R["stone_light"], rng, tones=STONE_LIGHT, mortar="3a352f")
    _stone(px, R["beak"], rng, studs=True, darker=STONE_DARKER)
    _stone(px, R["stone_grime"], rng, tones=tuple("%02x%02x%02x" % _scale(_rgb(t), 0.92) for t in STONE_TONES), grime=1.0)
    _stone_tiles(px, random.Random(5150))
    _stud_post(px, R["stud_post"], rng)
    _iron_rail(px, R["iron_rail"], rng)
    _rib_plate(px, R["rib_plate"], rng)
    _stud_head(px, R["stud_head"], rng)
    _arch_window(px, R["arch_lit"], rng, lit=True)
    _arch_window(px, R["arch_dark"], rng, lit=False)
    _arch_ring(px, R["arch_ring"], rng)
    _keep_panel(px, R["keep_panel"], rng)
    # the hull's planking under the stone wale, a little darker row by row towards the keel (phase 8: a readable dark
    # oak, base about #5a4030 with lit plank edges, so that the keel area does not go black at the game's half lighting)
    hull_tones = ("5a4030", "523a2c", "624636", "563d2f")
    _boards(px, R["hull_brown"], hull_tones, "20160e", rng, grain=0.06, knots=0.1, shade=lambda fy: 1.0 - 0.05 * fy, edge=0.2)
    _boards(px, R["hull_low"], hull_tones, "1e150d", rng, grain=0.06, knots=0.1, shade=lambda fy: 0.96 - 0.05 * fy, tint=("1f2a1c", 0.06), edge=0.2)
    _boards(px, R["hull_deep"], hull_tones, "1c130c", rng, grain=0.05, nails=False, shade=lambda fy: 0.92 - 0.05 * fy, tint=("1a2618", 0.12), edge=0.2)
    # (phase 6) no nail heads on the wood of the fittings, beams and furniture: stretched on a big face they read as
    # holes punched in the wood
    _boards(px, R["wood_dark"], ("4e321c", "452c18", "573820", "4a2f1a"), "1c1209", rng, nails=False)
    _boards(px, R["wood_mid"], ("7a5130", "6e482a", "855a36", "73502e"), "33210f", rng, nails=False, worn=0.02)
    _boards(px, R["wood_light"], ("9a6a3e", "a87644", "8e6038", "b07e4a"), "4a2f17", rng, nails=False, worn=0.02)
    _boards(px, R["rail"], ("5a3a20", "4e321c"), "24170c", rng, plank_h=8, butt=(40, 64), nails=False, knots=0.1)
    _boards(px, R["mast"], ("6e4a2a", "634226", "7a5230"), "33210f", rng, plank_h=4, butt=(200, 201), nails=False, grain=0.1, knots=0.25)
    _boards(px, R["deck"], ("7a5838", "6e5032", "86603e", "735436", "634a2e"), "2a1c10", rng, plank_h=4, worn=0.025)
    _boards(px, R["dark_wood"], ("40281a", "38231a"), "1a110a", rng, plank_h=4, nails=False, knots=0.1)
    _planks(px, R["cloth_roll"], ("b02529", "a32226", "bb2c30"), "6e1418", rng, plank_h=4, joints=0)
    _red_panel(px, R["red_panel"], rng)
    _studs(px, R["studs"], rng)
    _studs(px, R["studs_top"], rng, top_shade=True)
    _iron_strap(px, R["iron_strap"], rng)
    _roof_tile(px, R["roof_tile"], rng)
    _tile_edge(px, R["tile_edge"], rng)
    _timber(px, R["timber"], rng)
    # the strakes: the one under the stone wale in its shadow, the one at the waterline wet in a narrow band at its foot
    # (phase 8: the same dark oak as the planking, the shadow under the wale lighter)
    _strake5(px, R["strake_brown"], ("5a4030", "523a2c"), "20160e", rng, shade=lambda fy: min(1.0, 0.72 + 0.6 * fy))
    _strake5(px, R["strake_brown2"], ("5c4232", "543b2d"), "20160e", rng, tint=("1c2618", 0.3), wet=3)
    _gold5(px, R["gold"], rng)
    ct._rope(px, R["rope"], "b0925e", "735a36", rng)
    ct._rope(px, R["rope_light"], "c4a46a", "86683c", rng)
    ct._rope(px, R["rope_dark"], "c8a258", "8a6a30", rng)   # the golden hemp of the rope ladders (main reference)
    _iron5(px, R["iron"], rng)
    _fill(px, R["bronze"], "b08a2e", rng, 8)
    _fill(px, R["glow"], "ffd27a", rng, 4)
    _fill(px, R["glass"], "b8d4dc", rng, 4)
    _fill(px, R["red_paint"], "a8262a", rng, 6)
    _fill(px, R["white_paint"], "e6e4dc", rng, 5)
    _fill(px, R["navy"], "1c2340", rng, 4)
    _fill(px, R["end_grain"], "6a4a2a", rng, 10)
    _fill(px, R["bore"], "141210", rng, 3)
    ftx._cannon_tex(px, R["cannon"], rng)
    ct._weave(px, R["awning"], rng, "e4dccb", "cfc6b2", period=2)
    _lamp_glass(px, R["lantern"])
    _window(px, R["glow_window"], rng, lit=True)
    _window(px, R["window_in"], rng, lit=False)
    ct._door(px, R["door"], rng)
    ct._grating(px, R["grating"], rng)
    _pennant(px, R["pennant"], rng)
    _banner(px, R["banner"], rng)
    _banner(px, R["shield"], rng, shield=True)
    ct._compass(px, R["compass"], rng)
    ct._chart(px, R["chart"], rng)
    ct._books(px, R["books"], rng)
    ct._painting(px, R["painting"], rng)
    _cabin_wall(px, R["wall_wood"], rng)
    _wall_stone(px, R["wall_stone"], rng)
    _planks(px, R["floor"], ("6e4a2a", "634226", "7a5230", "5a3c22"), "2b1b0e", rng, plank_h=8, joints=2)
    ct._ceil(px, R["ceil"], rng)
    _planks(px, R["hold_floor"], ("5e4228", "553b24", "684a2e"), "241810", rng, plank_h=8, joints=3, worn=0.04, worn_col="3a3a30")
    _planks(px, R["hold_wall"], ("4e3420", "5a3c24", "46301c"), "1e140a", rng, plank_h=8, joints=2)
    ct._carpet(px, R["carpet"], rng, border="c9981f", field="8e1c20", centre="5e1014")
    ct._rug(px, R["rug"], rng)
    ct._boat(px, R["boat"], rng)
    ct._weave(px, R["sack"], rng, "a98b5e", "8e7349")
    ct._weave(px, R["canvas"], rng, "ab9a76", "9c8a66", period=1)
    _fill(px, R["linen"], "e6dfcc", rng, 4)
    _blocks(px, R["ham"], ("9a4632", "8a3c2a"), "5a2418", rng, bw=8, bh=4)
    _fill(px, R["bedding"], "8e1c20", rng, 8)
    _decor_materials(px, random.Random(2711))
    img.save(path)
    return img


# ---------------------------------------------------------------- the sails
def _shift(a, dx, dy):
    """The boolean array a moved by (dx, dy), False where it comes from outside."""
    out = np.zeros_like(a)
    h, w = a.shape
    xs0, xs1 = max(0, dx), min(w, w + dx)
    ys0, ys1 = max(0, dy), min(h, h + dy)
    out[ys0:ys1, xs0:xs1] = a[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
    return out


def _erode(a, r):
    out = a.copy()
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                out &= _shift(a, dx, dy)
    return out


def _sail(img, region, cols, rows, rng, style, emblem=False, tri=None):
    """Red blocky sail (32 px a block) with white wool, its cloth painted: a tone per cloth block (lit in the belly,
    shadowed at the leeches and darker towards the foot, the head in the shadow of the yard), long soft folds deepening
    towards the foot, double-stitched vertical seams between the cloths, reef bands with their reef points
    (courses and mizzen: two, topsails: one), a twisted bolt rope all round the edge. style "course": broad white bands
    down both leeches, white corners at the head (the main reference); "topsail": a white frame all round; "striped":
    two white stripes (the mizzen); "jib": white with a red band along the foot. The foot of the square sails is ragged
    (the stepped, worn foot of the references: transparent notches). emblem: the castle tower in the middle, beige in a
    dark outline, its masonry and its bevel painted, the windows and the gate in shadow."""
    u, v, w, h = region
    rs = np.random.RandomState(rng.randrange(1 << 30))
    ys, xs = np.mgrid[0:h, 0:w].astype(float)
    xs += 0.5
    ys += 0.5
    fx, fy = xs / w, ys / h
    cw, ch = w / cols, h / rows
    ci = np.minimum(cols - 1, (xs / cw).astype(int))
    ri = np.minimum(rows - 1, (ys / ch).astype(int))
    tsel = rs.rand(rows, cols)
    kc = rs.uniform(0.92, 1.07, (rows, cols))          # (phase 7: each cloth block its own value, the voxel sails of 112)
    white = np.zeros((rows, cols), bool)
    if style == "course":   # broad white leeches (about a seventh of the sail each), a red head with white corners
        nw = max(2, int(round(cols * 0.14)))
        white[:, :nw] = True
        white[:, cols - nw:] = True
        white[0, :nw + 1] = True
        white[0, cols - 1 - nw:] = True
    elif style == "topsail":
        white[:, 0] = white[:, -1] = True
        white[0, :] = True
    elif style == "striped":
        white[:, [0, cols - 1, cols // 3, cols - 1 - cols // 3]] = True
        white[0, :] = True
    wm = white[ri, ci]
    if style == "jib":
        wm = ~((fy > 0.62) & (fy < 0.84))
    redp = np.array([_rgb(c) for c in RED], float)
    whp = np.array([_rgb(c) for c in WHITE], float)
    ti = tsel[ri, ci]
    col = np.where(wm[..., None], whp[(ti * len(WHITE)).astype(int) % len(WHITE)], redp[(ti * len(RED)).astype(int) % len(RED)])
    k = kc[ri, ci].copy()
    dx = np.abs(fx - 0.5) * 2
    k *= 1.0 + 0.08 * (1 - dx ** 2) - 0.13 * dx ** 2 - 0.08 * fy
    k *= 1.0 + 0.12 * np.clip(1 - (2.2 * fy - 1.0) ** 2, 0, 1)                    # (phase 7) the belly catches the light
    k *= 1 - 0.38 * np.clip(1 - ys / (1.6 * ch), 0, 1) ** 1.3                      # the head, in the shadow of the yard
    nf = max(3, cols // 3)
    ph = rs.uniform(0, 6.28, 3)
    fold = 0.65 * np.sin(2 * np.pi * fx * nf + ph[0] + 0.9 * np.sin(fy * 3.0 + ph[1])) + 0.35 * np.sin(2 * np.pi * fx * nf * 2.3 + ph[2])
    k *= 1 + 0.06 * fold * (0.3 + 0.7 * fy)
    xi, yi = xs.astype(int), ys.astype(int)
    k *= 1 + rs.uniform(-0.02, 0.02, (h, w))      # (no fine weave: it sparkles at a distance in game)
    lx, ly = xs - ci * cw, ys - ri * ch
    if style != "jib":
        # each cloth block bevelled like the voxel sails of the main reference: lit along its top and left, shadowed
        # along its bottom and right, a dark groove between the cloths (a double-stitched seam), faint row joints
        k = np.where(ly < 3.0, k * (1.18 - 0.04 * ly), k)
        k = np.where(ly > ch - 3.0, k * (0.86 - 0.04 * (ly - ch + 3.0)), k)
        k = np.where((lx >= 2.0) & (lx < 4.0), k * 1.09, k)
        k = np.where(lx > cw - 3.0, k * 0.8, k)
        k = np.where(lx < 1.2, k * 0.62, k)                                    # the seam between two cloths
        k = np.where((lx >= 1.2) & (lx < 2.0), k * 1.1, k)                     # the lit edge of the overlap
        k = np.where((lx >= 4.5) & (lx < 5.5), k * 0.93, k)                  # its second row of stitches (a line: dots sparkle)
        k = np.where((ly < 1.0) & (lx >= 1.2), k * 0.86, k)                    # the blocks' rows
    else:
        sl = (xs + ys * 0.62) % (w / 5.0)                                      # the jib's cloths, parallel to its leech
        k = np.where(sl < 1.0, k * 0.78, k)
        k = np.where((sl >= 1.0) & (sl < 2.0), k * 1.07, k)
    bands = (0.22, 0.45) if style in ("course", "striped") else (0.5,) if style == "topsail" else ()
    tie = np.zeros((h, w), bool)
    for b in bands:
        yb = b * h
        d = np.abs(ys - yb)
        k = np.where(d < 3.0, k * 0.92, k)
        k = np.where(np.abs(d - 3.0) < 0.6, k * 0.76, k)
        k = np.where(np.abs(d - 1.5) < 0.5, k * 0.9, k)                         # (the stitching along the band)
        tie |= (np.abs(lx - cw / 2) < 1.1) & (ys > yb + 3) & (ys < yb + 10)
    col = np.where(tie[..., None], np.array(_rgb("7a3024"), float), col)
    k = np.where(tie, np.where(lx < cw / 2, 1.1, 0.8), k)
    if emblem:
        cell_h = max(2, int(h * 0.58) // 14)
        cell = max(2, int(w * 0.36) // 12)
        mask = np.array(tower_mask(12 * cell, 14 * cell_h, cell, cell_h)) > 0
        mh, mw = mask.shape
        mx, my = (w - mw) // 2, int(h * 0.48 - mh / 2)
        M = np.zeros((h, w), bool)
        M[my:my + mh, mx:mx + mw] = mask
        out = M.copy()
        for ddx in range(-3, 4):
            for ddy in range(-3, 4):
                if ddx * ddx + ddy * ddy <= 9:
                    out |= _shift(M, ddx, ddy)
        outline = out & ~M
        lit = M & ~(_shift(M, 3, 0) & _shift(M, 0, 3))        # within 3 px of the top or left edge
        dark = M & ~(_shift(M, -3, 0) & _shift(M, 0, -3))     # within 3 px of the bottom or right edge
        box = np.zeros((h, w), bool)
        box[my + int(mh * 0.4):my + mh, mx + cell:mx + mw - cell] = True
        holes = box & ~out
        ly2 = (ys - my) % (2 * cell_h)
        lx2 = (xs - mx + np.where(((ys - my) // (2 * cell_h)) % 2 == 1, cell, 0)) % (3 * cell)
        course = M & ((ly2 < 1.0) | (lx2 < 1.0))
        beige = np.array(_rgb(BEIGE), float)
        col = np.where(M[..., None], beige, col)
        k = np.where(M, 1.0 + 0.04 * fold - 0.05 * fy, k)
        k = np.where(lit, k * 1.1, k)
        k = np.where(dark, k * 0.8, k)
        k = np.where(course, k * 0.84, k)
        k = np.where(outline, k * 0.42, k)
        k = np.where(holes, k * 0.72, k)
    # transparency: the ragged foot of the square sails, outside the jib's triangle
    alpha = np.ones((h, w), bool)
    if style in ("course", "striped", "topsail"):
        rag = np.array([rng.choice((0, 0, 1, 1, 2)) for _ in range(cols)])
        cut = (ri == rows - 1) & (ly > ch * (1 - 0.3 * rag[ci]))
        alpha &= ~cut
    if tri is not None:
        inside = np.vectorize(lambda a, b: ct._tri_inside(tri, a, b))(fx, fy)
        alpha &= inside
    # the bolt rope round the edge (the region's border and the ragged or slanted edges alike)
    rope = alpha & ~_erode(alpha, 3) | (alpha & ((xi < 3) | (xi >= w - 3) | (yi < 3) | (yi >= h - 3)))
    rcol = np.array(_rgb("cbb68c"), float)
    col = np.where(rope[..., None], rcol, col)
    twist = np.where(((xi + yi) // 2) % 3 == 0, 0.78, 1.04)
    k = np.where(rope, twist * np.where(rope & ~_shift(rope, 0, 1) & ~_shift(rope, 1, 0), 0.8, 1.0), k)
    rgb = np.clip(col * k[..., None], 0, 255).astype(np.uint8)
    a = np.where(alpha, 255, 0).astype(np.uint8)
    tile = Image.fromarray(np.dstack([rgb, a]), "RGBA")
    img.paste(tile, (u, v))


def make_sail_texture(path, tris=None):
    rng = random.Random(1291)
    img = Image.new("RGBA", (SAIL_SIZE, SAIL_SIZE), (0, 0, 0, 0))
    styles = {"main_course": "course", "fore_course": "course", "mizzen_course": "striped", "main_topsail": "topsail",
              "fore_topsail": "topsail", "jib": "jib"}
    for name, (cols, rows) in SAIL_CELLS.items():
        tri = None
        if name == "jib":
            tri = (tris or {}).get(name) or [(0.0, 0.0), (1.0, 0.0), (0.62, 1.0)]
        _sail(img, SAIL_REGIONS[name], cols, rows, rng, styles[name], emblem=name in EMBLEM_SAILS, tri=tri)
    img.save(path)
    return img


def make_item_icon(path):
    """16x16 icon: the dark hull with its grey stone belt and red panels, the stern castle with its red roof, three
    masts with red sails bordered in white (a beige tower on the main course), red pennants."""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    stone, red, brown, dark = _rgb("a3a29c"), _rgb("b8262b"), _rgb("3e2616"), _rgb("2a1a0e")
    white, mast, beige, roof = _rgb("dcdcd6"), _rgb("6e4a2a"), _rgb(BEIGE), _rgb("a8302a")
    for x in range(1, 15):
        for y in range(10, 15):
            if y == 14 and (x < 3 or x > 12):
                continue
            c = stone if y == 10 else (red if y in (11, 12) and x % 3 else (brown if y >= 13 else stone))
            px[x, y] = c + (255,)
    for x in (0, 1):
        px[x, 9] = stone + (255,)
    # the stern castle and its turret
    for x in range(11, 15):
        for y in range(7, 10):
            px[x, y] = (stone if (x + y) % 2 else _rgb("8f8e88")) + (255,)
    px[13, 8] = _rgb("ffd27a") + (255,)
    for x, y in ((12, 5), (13, 5), (12, 6), (13, 6)):
        px[x, y] = dark + (255,)
    for x, y in ((12, 4), (13, 4), (11, 5), (14, 5)):
        px[x, y] = roof + (255,)
    for mx, top in ((4, 2), (7, 0), (10, 2)):
        for y in range(top, 10):
            px[mx, y] = mast + (255,)
        px[mx + 1, top] = red + (255,)
        px[mx + 2, top] = red + (255,)
    for y, x0, x1 in ((3, 3, 5), (4, 2, 6), (5, 2, 6), (6, 2, 6), (7, 2, 6)):
        for x in range(x0, x1 + 1):
            if x != 4:
                px[x, y] = (white if x in (x0, x1) else red) + (255,)
    for y, x0, x1 in ((2, 5, 9), (3, 5, 9), (4, 5, 9), (5, 5, 9), (6, 5, 9), (7, 5, 9)):
        for x in range(x0, x1 + 1):
            if x != 7:
                px[x, y] = (white if x in (x0, x1) else red) + (255,)
    px[6, 4] = beige + (255,)
    px[8, 4] = beige + (255,)
    px[6, 5] = beige + (255,)
    px[8, 5] = beige + (255,)
    for y in (4, 5, 6):
        for x in (9, 11):
            px[x, y] = (white if x == 11 else red) + (255,)
    img.save(path)


if __name__ == "__main__":
    import os
    out = os.environ.get("OUT", "/tmp/claude-0/agent_fortress")
    os.makedirs(out, exist_ok=True)
    make_texture(os.path.join(out, "fortress_ship.png"))
    make_sail_texture(os.path.join(out, "fortress_ship_sails.png"))
    make_item_icon(os.path.join(out, "icon.png"))
    print("ok")
