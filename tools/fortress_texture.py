"""Procedural pixel-art textures of the Fortress Ship (fortress_ship): a 512x512 atlas of the hull, the castle, the
fittings and the rooms (fortress_ship.png) and a 512x512 atlas of the sails (fortress_ship_sails.png), so that the
castle-tower emblems keep their resolution.

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

from PIL import Image

from galley_texture import _jitter, _rgb, paint_lamp_glass
import corsair_texture as ct
import frigate_texture as ftx

SIZE = 512
SAIL_SIZE = 512

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
    "studs":        (272, 32, 16, 32),  # dark planks with two rows of iron studs (under the stone belt)
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
    "banner":       (0, 176, 32, 64),   # red banner with the white tower, pointed foot (transparent around it)
    "shield":       (32, 176, 32, 40),  # heater shield: red field, white tower, gold rim (transparent around it)
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
    "stud_post":    (256, 336, 16, 32), # the dark wooden posts with iron studs that frame the red panels beside each rib
    "rib_plate":    (272, 336, 16, 64), # the black iron plate with big studs on the face of each stone rib
    "arch_lit":     (288, 336, 32, 48), # a lit arched window (third reference): dark wooden frame, mullion, transom
    "arch_ring":    (320, 336, 48, 64), # the stone arch (voussoirs, jambs, sill) round it, open in the middle
    "keep_panel":   (368, 336, 32, 48), # a framed red panel with iron studs on the keep's timber walls
    "arch_dark":    (400, 336, 32, 48), # an unlit arched window (the inside of the windows)
}
# single stone blocks (16 x 16, a joint along their right and bottom edges, bevelled): a tone each
STONE_TILES = {"stone": ["sb_%d" % k for k in range(6)], "stone_stud": ["sb_0", "sbs_0", "sb_2", "sbs_1", "sb_4", "sbs_2"],
               "stone_dark": ["sbd_%d" % k for k in range(4)], "stone_light": ["sbl_%d" % k for k in range(3)],
               "beak": ["sb_1", "sbs_0", "sb_3", "sbs_2"]}
for _k in range(6):
    REGIONS["sb_%d" % _k] = (16 * _k, 336, 16, 16)
for _k in range(3):
    REGIONS["sbs_%d" % _k] = (96 + 16 * _k, 336, 16, 16)
for _k in range(4):
    REGIONS["sbd_%d" % _k] = (144 + 16 * _k, 336, 16, 16)
for _k in range(3):
    REGIONS["sbl_%d" % _k] = (208 + 16 * _k, 336, 16, 16)
# regions mapped one block = 16 px from the face's corner (joints and studs aligned with the cube's edges)
ALIGNED = ("stone", "stone_dark", "stone_stud", "stone_light", "beak", "red_panel", "studs", "stud_post", "rib_plate")
STONE_TONES = ("7d766e", "726c65", "877f76", "6a645e", "79726a", "6f6962")
STONE_DARK = ("5c5650", "524d48", "635d57", "4b4743")
STONE_LIGHT = ("998f85", "8f877d", "a2998e")
STONE_MORTAR = "1d1915"
# names used by the shared helpers (ship_details, generate_galleon, corsair_furniture): the same pixels
for _alias, _src in (("hull_mid", "wood_mid"), ("hull_light", "wood_light"), ("hull_dark", "wood_dark"), ("wood_trim", "wood_dark"),
                     ("wood_honey", "wood_mid"), ("blue_paint", "navy"), ("pilaster", "wood_dark"), ("velvet", "red_paint"),
                     ("cushion", "red_paint"), ("brass", "bronze"), ("organ_wood", "wood_dark"), ("steel", "iron"), ("stripe", "white_paint"),
                     ("patch_wood", "wood_light"), ("repair", "wood_mid"), ("plate", "iron"), ("hearth_stone", "stone"), ("soot", "iron"),
                     ("stone_floor", "stone"), ("carving", "gold"), ("hull_blue", "red_panel")):
    REGIONS[_alias] = REGIONS[_src]

# the sails (second texture): one region each, cloth blocks of 16 px (8 on the small sails)
SAIL_REGIONS = {
    "main_course":    (0, 0, 288, 176),
    "fore_course":    (288, 0, 224, 144),
    "mizzen_course":  (288, 144, 192, 128),
    "main_topsail":   (0, 176, 192, 96),
    "fore_topsail":   (0, 272, 160, 80),
    "jib":            (192, 272, 128, 160),
}
SAIL_CELLS = {  # (columns, rows) of cloth blocks drawn in each sail region
    "main_course": (20, 11), "fore_course": (16, 8), "mizzen_course": (12, 8), "main_topsail": (8, 3), "fore_topsail": (6, 3),
    "jib": (8, 10),
}
# which sails carry the castle-tower emblem (the courses of the fore and main masts, as on the references)
EMBLEM_SAILS = ("main_course",)   # the tower on the main course only, as on all three references

_mix, _scale, _planks, _blocks, _fill = ct._mix, ct._scale, ct._planks, ct._blocks, ct._fill

RED = ("a82226", "9a1e22", "b2282c", "9f2125", "901b1f")      # deep crimson (the references' sails are darker than pure red)
WHITE = ("d2d2cc", "c4c5bf", "dcdcd6", "b9bab4")
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
def _stone_block(px, u, v, bw, bh, base, rng, mortar, stud=False, x0=0, y0=0, clip=None):
    """One bevelled stone block (the voxel masonry of the references): a bright top and left edge, a shadowed bottom
    and right edge, a dark joint along the right and bottom, a slow tone drift, a few darker grains; stud: an iron stud
    with a pale glint."""
    mortar = _rgb(mortar)
    sx, sy = rng.randrange(4, bw - 6), rng.randrange(4, bh - 6)
    grains = {(rng.randrange(1, bw - 2), rng.randrange(1, bh - 2)) for _ in range(4)}
    ph = rng.uniform(0, 6.3)
    for y in range(bh):
        for x in range(bw):
            X, Y = x0 + x, y0 + y
            if clip and not (0 <= X < clip[0] and 0 <= Y < clip[1]):
                continue
            if x == bw - 1 or y == bh - 1:
                c = mortar
            else:
                k = 1.0 + (0.26 if y == 0 else 0.1 if y == 1 else 0) - (0.32 if y == bh - 2 else 0.14 if y == bh - 3 else 0) \
                    + (0.14 if x == 0 else 0.04 if x == 1 else 0) - (0.28 if x == bw - 2 else 0.1 if x == bw - 3 else 0) \
                    + 0.05 * math.sin(x * 0.45 + y * 0.3 + ph)
                c = _scale(base, k)
                if (x, y) in grains:
                    c = _scale(base, 0.8)
                if stud and sx <= x <= sx + 2 and sy <= y <= sy + 2:
                    c = _rgb("262628") if (x, y) != (sx, sy) else _rgb("9a9a9e")
            px[u + X, v + Y] = _jitter(c, rng, 3) + (255,)


def _stone(px, region, rng, tones=STONE_TONES, mortar=STONE_MORTAR, studs=False, bh=16, bw=16, bevel=True):
    """Grey stone blocks a block square (16 px), each a tone of its own (a little warm), bevelled (see _stone_block);
    rows staggered by half a block; studs: an iron stud in some blocks. bevel=False: the flatter dressed stone inside
    the keep."""
    u, v, w, h = region
    for by in range(0, h, bh):
        off = (bw // 2) if (by // bh) % 2 else 0
        for bx in range(-off, w, bw):
            base = _scale(_rgb(rng.choice(tones)), rng.uniform(0.94, 1.06))
            if bevel:
                _stone_block(px, u, v, bw, bh, base, rng, mortar, stud=studs and rng.random() < 0.55, x0=bx, y0=by, clip=(w, h))
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
                            - (0.06 if x == bw - 1 else 0) + 0.03 * math.sin(x * 1.3 + y * 0.7)
                        c = _scale(base, k)
                    px[u + X, v + Y] = _jitter(c, rng, 4) + (255,)


def _stone_tiles(px, rng):
    """The single blocks of STONE_TILES (normal, studded, dark, light)."""
    for k in range(6):
        u, v, w, h = REGIONS["sb_%d" % k]
        _stone_block(px, u, v, w, h, _scale(_rgb(STONE_TONES[k]), rng.uniform(0.96, 1.04)), rng, STONE_MORTAR)
    for k in range(3):
        u, v, w, h = REGIONS["sbs_%d" % k]
        _stone_block(px, u, v, w, h, _scale(_rgb(STONE_TONES[(2 * k + 1) % 6]), rng.uniform(0.96, 1.04)), rng, STONE_MORTAR, stud=True)
    for k in range(4):
        u, v, w, h = REGIONS["sbd_%d" % k]
        _stone_block(px, u, v, w, h, _rgb(STONE_DARK[k]), rng, "151210")
    for k in range(3):
        u, v, w, h = REGIONS["sbl_%d" % k]
        _stone_block(px, u, v, w, h, _rgb(STONE_LIGHT[k]), rng, "3a352f")


def _red_panel(px, region, rng):
    """The red panels between the ribs (main reference): red boards laid in block-sized panes, a grid of red blocks
    with dark joints along their right and bottom edges, a lit top edge, a board seam across the middle, worn spots."""
    u, v, w, h = region
    for by in range(0, h, 16):
        for bx in range(0, w, 16):
            base = _scale(_rgb(rng.choice(("a3282b", "98242a", "ad2c2f", "92222a", "9e2629"))), rng.uniform(0.95, 1.05))
            worn = {(rng.randrange(2, 13), rng.randrange(2, 13)) for _ in range(3)}
            for y in range(16):
                for x in range(16):
                    if x == 15 or y == 15:
                        c = _rgb("380b0d")
                    else:
                        k = 1.0 + (0.16 if y == 0 else 0.06 if y == 1 else 0) - (0.2 if y == 14 else 0) + (0.08 if x == 0 else 0) \
                            - (0.16 if x == 14 else 0) - (0.12 if y == 7 else 0) + 0.04 * math.sin(x * 0.7 + y * 0.2)
                        c = _scale(base, k)
                        if (x, y) in worn:
                            c = _mix(c, _rgb("5a2a22"), 0.45)
                    px[u + bx + x, v + by + y] = _jitter(c, rng, 3) + (255,)


def _stud_post(px, region, rng):
    """Dark vertical boards with two big iron studs a block (the frame posts beside the ribs)."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("3c2716"), 1.0 + 0.06 * math.sin(y * 0.9 + x * 0.3) + (0.08 if x == 1 else 0) - (0.12 if x == w - 2 else 0))
            if x in (0, w - 1) or x == w // 2 - 1:
                c = _rgb("1c1108")
            if y % 16 in (3, 4, 5, 11, 12, 13) and x in (4, 5, 6, 10, 11, 12):
                c = _rgb("2c2c2f")
                if y % 16 in (3, 11) and x in (4, 10):
                    c = _rgb("a2a2a6")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _rib_plate(px, region, rng):
    """The black iron plate on a stone rib: dark iron, a lighter top-left bevel, a big domed stud in each block."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("2c2c30"), 1.0 + 0.06 * math.sin(y * 0.4 + x))
            if x == 0 or y % 16 == 0:
                c = _rgb("4c4c52")
            elif x == w - 1 or y % 16 == 15:
                c = _rgb("131315")
            dy, dx = y % 16 - 7.5, x - 7.5
            r = math.hypot(dx, dy)
            if r < 3.2:
                c = _scale(_rgb("5a5a60"), 1.25 - 0.12 * r - 0.06 * (dx + dy))
            elif r < 3.9:
                c = _rgb("18181a")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _arch_inside(x, y, w, h, r=None):
    """Inside an arch w wide (round top of radius w / 2) and h high?"""
    r = w / 2 if r is None else r
    cx = (w - 1) / 2
    if y >= r:
        return abs(x - cx) <= w / 2
    return (x - cx) ** 2 + (y - r) ** 2 <= r * r


def _arch_window(px, region, rng, lit=True):
    """An arched window (third reference): a heavy dark wooden frame following the round top, a mullion and a transom,
    warm light (brighter low in the middle) or dark panes; transparent outside the arch."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            if not _arch_inside(x + 0.5 - 0.5, y + 0.5, w, h):
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            inner = _arch_inside(x - 3, y - 3, w - 6, h - 6) and 3 <= x < w - 3 and 3 <= y < h - 3
            bar = abs(x - (w - 1) / 2) < 1.2 or abs(y - h * 0.58) < 1.2
            if not inner:
                c = _rgb("3a2414") if _arch_inside(x - 1, y - 1, w - 2, h - 2) and 1 <= x < w - 1 else _rgb("1e1209")
            elif bar:
                c = _rgb("4a2e18")
            elif lit:
                d = math.hypot(x - w / 2 + 0.5, (y - h * 0.66) * 0.8) / (w / 2)
                c = _mix(_rgb("fff0b0"), _rgb("e8902c"), min(1.0, d * 1.1))
            else:
                c = _mix(_rgb("3a3020"), _rgb("2a2418"), y / h)
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _arch_ring(px, region, rng):
    """The stone surround of an arched window: wedge-shaped voussoirs round the top, jamb blocks down the sides, a sill
    at the foot; open (transparent) where the window is."""
    u, v, w, h = region
    R, r = w / 2, w / 2 - 8          # outer and inner radius of the arch
    cx, cy = (w - 1) / 2, R
    sill = h - 5
    tones = [_scale(_rgb(rng.choice(STONE_LIGHT)), rng.uniform(0.86, 1.0)) for _ in range(16)]
    for y in range(h):
        for x in range(w):
            outer = _arch_inside(x, y, w, h)
            hole = y < sill and (abs(x - cx) < r if y >= cy else (x - cx) ** 2 + (y - cy) ** 2 < r * r)
            if not outer or hole:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            if y >= sill:
                k = 1.0 + (0.2 if y == sill else 0) - (0.25 if y == h - 1 else 0)
                c = _scale(tones[0], k) if x % 12 != 11 else _rgb("3a352f")
            elif y < cy:   # voussoirs: wedges every 22.5 degrees
                a = math.degrees(math.atan2(cy - y, x - cx))
                seg = int(a // 22.5)
                d = math.hypot(x - cx, y - cy)
                c = _scale(tones[seg % 16], 1.0 + 0.18 * (d > R - 1.5) - 0.2 * (d < r + 1.2))
                if abs((a % 22.5)) < 2.2 or abs((a % 22.5) - 22.5) < 2.2:
                    c = _rgb("3a352f")
            else:          # jambs: blocks 12 px high
                seg = int((y - cy) // 12)
                c = _scale(tones[(seg + 5 + (x > cx) * 3) % 16], 1.0 + (0.2 if (y - cy) % 12 < 1 else 0) - (0.22 if (y - cy) % 12 >= 11 else 0))
                if (y - cy) % 12 >= 11:
                    c = _rgb("3a352f")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _keep_panel(px, region, rng):
    """A red panel framed in dark wood with an iron stud in each corner (the keep's walls)."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            fr = x < 4 or x >= w - 4 or y < 4 or y >= h - 4
            if fr:
                c = _scale(_rgb("2e1d10"), 1.0 + 0.06 * math.sin(x + y * 0.5))
                if x in (0, w - 1) or y in (0, h - 1):
                    c = _rgb("170e06")
                if (x in (1, 2) or x in (w - 3, w - 2)) and (y in (1, 2) or y in (h - 3, h - 2)):
                    c = _rgb("8a8a8e") if (x, y) in ((1, 1), (w - 3, 1), (1, h - 3), (w - 3, h - 3)) else _rgb("2a2a2c")
            else:
                bx, by = (x - 4) % 8, (y - 4) % 12
                c = _scale(_rgb(("a3282b", "98242a", "ad2c2f")[((x - 4) // 8 + (y - 4) // 12) % 3]),
                           1.0 + (0.12 if by == 0 else 0) - (0.16 if by == 10 else 0) - (0.1 if bx == 6 else 0))
                if bx == 7 or by == 11:
                    c = _rgb("380b0d")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _studs(px, region, rng):
    """Dark planks along u with a row of big iron studs across the middle of each block (the band under the stone
    belt, main reference)."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("3e2818"), 1.0 + 0.05 * math.sin(x * 0.3 + y * 1.1) + (0.08 if y % 16 == 0 else 0))
            if y % 8 == 7:
                c = _rgb("1c120a")
            if y % 16 in (6, 7, 8) and x % 16 in (6, 7, 8):
                c = _rgb("2a2a2c") if not (y % 16 == 6 and x % 16 == 6) else _rgb("a2a2a6")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _iron_strap(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            c = _scale(_rgb("2e2e31"), 1.0 + 0.07 * math.sin(y * 0.5 + x))
            if x in (0, w - 1):
                c = _rgb("161618")
            if y % 8 in (3, 4) and x in (6, 7, 8, 9):
                c = _rgb("6a6a6e") if (y % 8 == 3 and x in (6, 7)) else _rgb("4a4a4e")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _roof_tile(px, region, rng):
    """Rows of red rounded tiles (8 px high), each tile 8 px wide, shifted every row, darker at their lower lip."""
    u, v, w, h = region
    for y in range(h):
        row = y // 8
        for x in range(w):
            off = 4 if row % 2 else 0
            tx = ((x + off) % 8)
            ly = y % 8
            base = _rgb(("a8302a", "b33a30", "9a2a26", "bd4234")[((x + off) // 8 + row * 3) % 4])
            c = _scale(base, 1.08 - 0.05 * ly + 0.06 * math.cos((tx - 3.5) / 4 * math.pi / 2))
            if ly == 7:
                c = _rgb("3e1410")
            elif tx == 0:
                c = _scale(base, 0.7)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _tile_edge(px, region, rng):
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            if y < 4:
                c = _scale(_rgb("a8302a"), 1.0 - 0.04 * y)
            else:
                c = _scale(_rgb(("a3a29c", "8f8e88", "b2b1aa")[(x // 16) % 3]), 1.0 + (0.08 if y == 4 else 0) - (0.1 if y == h - 1 else 0))
                if x % 16 == 0:
                    c = _rgb("4a4946")
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _timber(px, region, rng):
    """Dark vertical boards with a darker post at each side (the turret's walls)."""
    u, v, w, h = region
    for x in range(w):
        base = _scale(_rgb(rng.choice(("4a3020", "432b1c", "513524"))), rng.uniform(0.95, 1.05)) if x % 4 == 0 else base
        for y in range(h):
            c = _scale(base, 1.0 + 0.05 * math.sin(y * 0.5 + x))
            if x % 4 == 3:
                c = _rgb("21140a")
            if x < 3 or x >= w - 3:
                c = _scale(_rgb("2e1d10"), 1.0 + 0.04 * math.sin(y))
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _window(px, region, rng, lit=True):
    """A window in a heavy dark wooden frame, four panes; lit: warm light, brighter low in the middle."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            frame = x < 4 or x >= w - 4 or y < 4 or y >= h - 4
            bar = abs(x - w / 2 + 0.5) < 1.5 or abs(y - h / 2 + 0.5) < 1.5
            if frame:
                c = _rgb("3a2414") if not (x in (0, w - 1) or y in (0, h - 1)) else _rgb("1e1209")
            elif bar:
                c = _rgb("4a2e18")
            elif lit:
                d = math.hypot(x - w / 2 + 0.5, (y - h * 0.62) * 0.9) / (w / 2)
                c = _mix(_rgb("fff0b0"), _rgb("e8902c"), min(1.0, d * 1.15))
            else:
                c = _mix(_rgb("3a3020"), _rgb("2a2418"), y / h)
            px[u + x, v + y] = _jitter(c, rng, 2) + (255,)


def _banner(px, region, rng, shield=False):
    """Red banner with a beige / white tower, a pale border, a pointed foot (transparent around the point); or a
    heater shield (round-bottomed point) with a gold rim."""
    u, v, w, h = region
    red, rim = _rgb("b02529"), _rgb("e0d4b8") if not shield else _rgb("d8a63a")
    mw = int(w * (0.62 if shield else 0.6))
    mask = tower_mask(mw, mw + mw // 6)
    mx, my = (w - mask.width) // 2, int(h * (0.24 if shield else 0.18))
    for y in range(h):
        for x in range(w):
            fx = (x + 0.5) / w
            if shield:
                t = max(0.0, (y - h * 0.45) / (h * 0.55))
                half = 0.5 * math.sqrt(max(0.0, 1 - t ** 1.8))
                inside = abs(fx - 0.5) <= half and y < h - 1
                edge = inside and (abs(fx - 0.5) > half - 3.0 / w or y < 3 or y >= h - 4)
            else:
                foot = h * 0.78
                half = 0.5 if y < foot else 0.5 * (1 - (y - foot) / (h - foot))
                inside = abs(fx - 0.5) <= half + 1e-9
                edge = inside and (abs(fx - 0.5) > half - 2.5 / w or y < 3)
            if not inside:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            c = _scale(red, 1.0 + 0.05 * math.sin(x * 0.7 + y * 0.3) - 0.08 * (y / h))
            if edge:
                c = rim
            elif mx <= x < mx + mask.width and my <= y < my + mask.height and mask.getpixel((x - mx, y - my)):
                c = _rgb(BEIGE) if not shield else _rgb("e8e6e0")
            if not shield and y < 3:
                c = _rgb("3a2414")   # the rod sleeve
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _pennant(px, region, rng):
    """Red pennant, long swallow tail cut in steps (transparent notch), darker at the hoist."""
    u, v, w, h = region
    for y in range(h):
        for x in range(w):
            fx = x / w
            notch = fx > 0.62 and abs(y - h / 2 + 0.5) < (fx - 0.62) / 0.38 * (h / 2 - 1)
            taper = abs(y - h / 2 + 0.5) > (h / 2) * (1 - 0.45 * fx)
            if notch or taper:
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            c = _scale(_rgb("b8262b"), 1.0 + 0.06 * math.sin(x * 0.5) - 0.05 * (x < 3))
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
    _stone(px, R["stone"], rng)
    _stone(px, R["stone_dark"], rng, tones=STONE_DARK, mortar="151210")
    _stone(px, R["stone_stud"], rng, studs=True)
    _stone(px, R["stone_light"], rng, tones=STONE_LIGHT, mortar="3a352f")
    _stone(px, R["beak"], rng, studs=True)
    _stone_tiles(px, random.Random(5150))
    _stud_post(px, R["stud_post"], rng)
    _rib_plate(px, R["rib_plate"], rng)
    _arch_window(px, R["arch_lit"], rng, lit=True)
    _arch_window(px, R["arch_dark"], rng, lit=False)
    _arch_ring(px, R["arch_ring"], rng)
    _keep_panel(px, R["keep_panel"], rng)
    _planks(px, R["hull_brown"], ("3e2616", "36200f", "462c1a", "3a2414"), "1a0f06", rng, plank_h=4, joints=2, grain=0.05)
    _planks(px, R["wood_dark"], ("4e321c", "452c18", "573820", "4a2f1a"), "1e130a", rng)
    _planks(px, R["wood_mid"], ("7a5130", "6e482a", "855a36", "73502e"), "33210f", rng)
    _planks(px, R["wood_light"], ("9a6a3e", "a87644", "8e6038", "b07e4a"), "4a2f17", rng)
    _planks(px, R["rail"], ("5a3a20", "4e321c"), "24170c", rng, plank_h=8, joints=1)
    _planks(px, R["mast"], ("6e4a2a", "634226", "7a5230"), "33210f", rng, plank_h=4, joints=0, grain=0.1)
    _planks(px, R["deck"], ("7a5838", "6e5032", "86603e", "735436", "634a2e"), "2e1f12", rng, plank_h=4, joints=2)
    _planks(px, R["dark_wood"], ("40281a", "38231a"), "1a110a", rng, plank_h=4, joints=1)
    _planks(px, R["cloth_roll"], ("b02529", "a32226", "bb2c30"), "6e1418", rng, plank_h=4, joints=0)
    _red_panel(px, R["red_panel"], rng)
    _studs(px, R["studs"], rng)
    _iron_strap(px, R["iron_strap"], rng)
    _roof_tile(px, R["roof_tile"], rng)
    _tile_edge(px, R["tile_edge"], rng)
    _timber(px, R["timber"], rng)
    ftx._strake(px, R["strake_brown"], ("3e2616", "3a2414"), "160c04", rng, grain=0.07)
    ftx._strake(px, R["strake_brown2"], ("46291a", "402617"), "160c04", rng, grain=0.07)
    ftx._gold(px, R["gold"], rng)
    ct._rope(px, R["rope"], "b0925e", "735a36", rng)
    ct._rope(px, R["rope_light"], "c4a46a", "86683c", rng)
    ct._rope(px, R["rope_dark"], "c8a258", "8a6a30", rng)   # the golden hemp of the rope ladders (main reference)
    _fill(px, R["iron"], "38393c", rng, 6)
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
    u, v, w, h = R["lantern"]
    paint_lamp_glass(px, u, v, w, h)
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
def _sail(px, region, cols, rows, rng, style, emblem=False, tri=None):
    """Red blocky sail (one tone per cloth block, lit in the belly, shadowed at the leeches) with white wool:
    style "course": broad white bands down both leeches, white corners at the head (the main reference); "topsail": a white frame all round; "striped": two white
    stripes (the mizzen); "jib": white with a red band along the foot. The foot of the square sails is ragged
    (the stepped, worn foot of the references: transparent notches). emblem: the castle tower in the middle."""
    u, v, w, h = region
    cw, ch = w / cols, h / rows
    tone = []
    for r in range(rows):
        row = []
        for c in range(cols):
            dx = abs((c + 0.5) / cols - 0.5) * 2
            dy = (r + 0.5) / rows
            k = 1.0 + 0.07 * (1 - dx * dx) - 0.14 * dx * dx - 0.05 * dy
            row.append((rng.random(), k * rng.uniform(0.97, 1.03)))
        tone.append(row)
    rag = [rng.choice((0, 0, 1, 1, 2)) for _ in range(cols)] if style in ("course", "striped", "topsail") else [0] * cols
    mask = None
    if emblem:
        # big and centred (third reference: a third of the sail's width); the cells a little wider than high, the yard
        # being braced round on the side views
        cell_h = max(2, int(h * 0.58) // 14)
        cell = max(2, int(w * 0.36) // 12)
        mask = tower_mask(12 * cell, 14 * cell_h, cell, cell_h)
        mx, my = (w - mask.width) // 2, int(h * 0.48 - mask.height / 2)
    for y in range(h):
        for x in range(w):
            fx, fy = (x + 0.5) / w, (y + 0.5) / h
            if tri is not None and not ct._tri_inside(tri, fx, fy):
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            c_, r_ = min(cols - 1, int(x / cw)), min(rows - 1, int(y / ch))
            # the ragged foot: the last row of cloths is cut short by 0..2 eighths of a row, column by column
            if r_ == rows - 1 and (y - r_ * ch) > ch * (1 - 0.3 * rag[c_]):
                px[u + x, v + y] = (0, 0, 0, 0)
                continue
            t, k = tone[r_][c_]
            white = False
            if style == "course":   # broad white leeches (about a seventh of the sail each), a red head with white corners
                nw = max(2, int(round(cols * 0.14)))
                white = c_ < nw or c_ >= cols - nw or (r_ == 0 and (c_ <= nw or c_ >= cols - 1 - nw))
            elif style == "topsail":
                white = c_ in (0, cols - 1) or r_ == 0
            elif style == "striped":
                white = c_ in (0, cols - 1) or r_ == 0 or c_ in (cols // 3, cols - 1 - cols // 3)
            elif style == "jib":
                white = not (fy > 0.62 and fy - 0.62 < 0.22 + 0.0 * fx)
            base = _rgb(WHITE[int(t * len(WHITE)) % len(WHITE)]) if white else _rgb(RED[int(t * len(RED)) % len(RED)])
            col = _scale(base, k)
            lx, ly = x - c_ * cw, y - r_ * ch
            if lx < 1 or ly < 1:
                col = _scale(col, 0.88)       # the edges of the cloth blocks
            elif (x * 7 + y * 13) % 31 == 0:
                col = _scale(col, 0.94)
            if mask is not None and mx <= x < mx + mask.width and my <= y < my + mask.height and mask.getpixel((x - mx, y - my)):
                col = _scale(_rgb(BEIGE), 1.0 - 0.06 * ((x // 6 + y // 6) % 2))
            px[u + x, v + y] = _jitter(col, rng, 3) + (255,)


def make_sail_texture(path, tris=None):
    rng = random.Random(1291)
    img = Image.new("RGBA", (SAIL_SIZE, SAIL_SIZE), (0, 0, 0, 0))
    px = img.load()
    styles = {"main_course": "course", "fore_course": "course", "mizzen_course": "striped", "main_topsail": "topsail",
              "fore_topsail": "topsail", "jib": "jib"}
    for name, (cols, rows) in SAIL_CELLS.items():
        tri = None
        if name == "jib":
            tri = (tris or {}).get(name) or [(0.0, 0.0), (1.0, 0.0), (0.62, 1.0)]
        _sail(px, SAIL_REGIONS[name], cols, rows, rng, styles[name], emblem=name in EMBLEM_SAILS, tri=tri)
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
