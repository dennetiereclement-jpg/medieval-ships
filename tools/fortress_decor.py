"""Furniture of the Fortress Ship (decoration phase): blocks of the decoration mods (drawn by the ship where they stand,
moving with it; never placed in the world), furniture modelled for the ship (drawn by tools/generate_fortress.py with
the builders of tools/fortress_furniture.py and of tools/corsair_furniture.py / generate_corsair.py), and the seats.

  src/main/resources/assets/medievalships/interiors/fortress_ship_decor.json

Same format as tools/frigate_decor.py (read by fr.medievalships.core.InteriorDecor). A block whose mod is missing on a
client is replaced by its stand-in, a box of the same size in the model (bone "fallback_<i>"). The solid furniture is
added to the interior grid (FURNITURE cells): the players walk round the desk, the bed, the tables, the bunks, the
racks and the cargo.

The mods' blocks first (catalog /tmp/claude-0/mods_catalog/catalog.json: Farmhouse Decorations, Furnish, Farmer's
Delight, Lands of Icaria), modelled pieces only for what they lack or what must carry the arms of Havre-Fort (the red
carpets and banners with the white tower, the heater shields, the armour stands in their surcoats, the weapon racks,
the barrels of arrows, the campaign map of the council table, the iron chandeliers, the window seat, the inside of the
castle's windows, the armourer's anvil, the signal brazier, the cut stone and timber for the fort, the lashed canvas).

A fortress at sea: the captain's cabin (desk facing the door, the stern windows behind the captain's chair), the
council room in the keep (the war table and its seven chairs), the lookout's turret, the crew's mess and its galley,
the crew quarters (bunks, hammocks, sea chests, a gaming table), the hold (provisions, the armoury, the stone and timber
for the fort, spare sail), the deck cargo of the references (crates two high, barrels, sacks, rope coils), benches.

Kept clear (checked here by check() and by FortressShipTest): the doors and their approaches, the stairs and the
companionway with their feet, the hatch to the keep's roof, the centre lines of the cabin, the hold and the crew
quarters, the main deck within 2.3 of the centre line (the boarding spots), the gangplank's stairs and lever
(starboard, z -0.8..3.4), the seats' stand-up spots, the places where the game test stands in each room. Nothing pokes
through the hull, the walls or the decks (checked by apply_to_grid).
"""
import json
import math

import numpy as np

import fortress_interior as fi
import fortress_shape as fs
import frigate_decor as fdx

FACING = fdx.FACING
FD, FU, FR, LI = fdx.FD, fdx.FU, fdx.FR, fdx.LI

# model bounds of the default state (block space, x east, z south, the front is north; element and blockstate rotations
# applied), from the mods catalog ("bounds"): the frigate's list and the pieces this ship adds
BOUNDS = dict(fdx.BOUNDS)
BOUNDS.update({
    FD + "wardrobe": (-0.844, 0.844, 0, 1.984, 0.156, 1),
    FD + "dresser": (0, 1, 0, 1.016, 0.25, 1),
    FD + "dining_table_side": (0, 1, -0.016, 1, 0.016, 0.984),
    FD + "dining_table_middle": (0, 1, 0.797, 1, 0.016, 0.984),
    FD + "kitchen_counter": (0, 1, 0, 1, 0.078, 1),
    FD + "seasoning_rack": (0.125, 0.875, 0, 0.781, 0.688, 1),
    FU + "crimson_chair": (0.125, 0.875, -0.038, 1, 0, 0.75),
    FU + "plate": (0.062, 0.938, 0, 0.062, 0.062, 0.938),
    FU + "dark_oak_square_table": (0, 1, 0, 1, 0, 1),
    FU + "gray_amphora": (0, 1, 0, 1, 0.125, 0.875),
    FR + "stove": (0, 1, 0, 1, 0, 1),
    FR + "cooking_pot": (0, 1, 0, 0.904, 0.125, 0.875),
    FR + "cutting_board": (0.062, 0.938, 0, 0.062, 0.062, 0.938),
    FR + "roast_chicken_block": (0.062, 0.938, 0, 0.5, 0.062, 0.938),
    FR + "apple_pie": (0.125, 0.875, 0, 0.25, 0.125, 0.875),
    FR + "onion_crate": (0, 1, 0, 1, 0, 1),
    FR + "beetroot_crate": (0, 1, 0, 1, 0, 1),
    FR + "straw_bale": (0, 1, 0, 1, 0, 1),
    LI + "tapped_cypress_barrel": (0.047, 0.953, 0, 0.906, -0.246, 1),
    LI + "simple_cypress_rack": (0, 1, 0, 0.125, 0.125, 0.875),
    LI + "spelt_bale_block": (0, 1, 0, 1, 0, 1),
    LI + "gray_storage_vase": (0.062, 0.938, 0, 1, 0.062, 0.938),
    LI + "red_storage_vase": (0.062, 0.938, 0, 1, 0.062, 0.938),
})

# stand-in look when the mod is missing (default: a box of mid brown wood)
FALLBACK_REGION = dict(fdx.FALLBACK_REGION)
FALLBACK_REGION.update({FD + "wardrobe": "wood_dark", FD + "dresser": "wood_dark", FD + "dining_table_side": "wood_dark",
                        FD + "dining_table_middle": "wood_dark", FD + "kitchen_counter": "wood_dark", FD + "seasoning_rack": "wood_dark",
                        FU + "crimson_chair": "velvet_red", FU + "plate": "white_paint", FU + "dark_oak_square_table": "wood_dark",
                        FU + "gray_amphora": "stone", FR + "stove": "stone", FR + "cooking_pot": "iron", FR + "cutting_board": "wood_light",
                        FR + "roast_chicken_block": "ham", FR + "apple_pie": "bread", FR + "straw_bale": "rope_light", FR + "onion_crate": "wood_light",
                        FR + "beetroot_crate": "wood_light", LI + "spelt_bale_block": "rope_light", LI + "simple_cypress_rack": "wood_dark",
                        LI + "gray_storage_vase": "stone", LI + "red_storage_vase": "red_paint", FU + "spruce_stool": "wood_mid",
                        FU + "spruce_bench": "wood_mid"})
GLOWING = fdx.GLOWING
SEAT_H = {FU + "dark_oak_chair": 0.562, FU + "crimson_chair": 0.5, FU + "spruce_stool": 0.562, FU + "dark_oak_stool": 0.562,
          FU + "spruce_bench": 0.562, FU + "dark_oak_bench": 0.562}

BLOCKS = []   # dicts: block, x, y, z, yaw, solid, scale
SEATS = []    # dicts: x, y, z, dx, dy, dz
CUSTOM = []   # furniture drawn by generate_fortress: (builder name, kwargs, solid box or None)

M, L, C, Q, F, K = fs.MAIN_DECK_Y, fs.LOWER_FLOOR_Y, fs.CABIN_FLOOR_Y, fs.QUARTERDECK_Y, fs.FORECASTLE_Y, fs.KEEP_Y
HOLD_CEIL, CABIN_CEIL, KEEP_CEIL, MESS_CEIL = M - fs.SLAB, Q - fs.SLAB, K - fs.SLAB, F - fs.SLAB
TURRET_CEIL = fi.ROOMS["turret"][3]

to_ship = fdx.to_ship


def footprint(bid, x, y, z, yaw, scale=1.0):
    """Ship-local bounding box (x0, x1, y0, y1, z0, z1) of a mod block placed at (x, y, z) with yaw (degrees)."""
    b = BOUNDS[bid]
    pts = [to_ship(x, y, z, yaw, px, py, pz, scale) for px in (b[0], b[1]) for py in (b[2], b[3]) for pz in (b[4], b[5])]
    xs, ys, zs = zip(*pts)
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)

_GRID = []


def grid():
    """The interior grid without the furniture (built once), to find the faces of the walls."""
    if not _GRID:
        _GRID.append(fi.build())
    return _GRID[0]


def wall_x(z, y, side, h=1.0, dz=0.4):
    """x of the inner face of the side wall (side +1 port, -1 starboard) at (z, y): the outer edge of the outermost open
    cell going out from the centre line, the nearest over the heights y..y+h and z-dz..z+dz (the castle's walls lean in
    over the cabin's floor, the hull narrows towards the ends)."""
    g = grid()
    best = 7.0
    for yy in np.arange(y, y + h + 1e-6, 0.5):
        for zz in (z - dz, z, z + dz):
            x = 0.25
            while x < 7.0:
                if g.at(side * x, yy, zz) == fi.SOLID and abs(x) > 1.0:
                    best = min(best, x - 0.25)
                    break
                x += 0.5
    if best >= 7.0:
        raise ValueError("no wall at z %s y %s" % (z, y))
    return side * best


def wall_z(x, y, z_from, direction):
    """z of the inner face of the end wall met going from z_from along direction (-1 aft, +1 forward) at (x, y)."""
    g = grid()
    z = math.floor(z_from / fi.CELL) * fi.CELL + fi.CELL / 2
    while abs(z) < 30:
        if g.at(x, y, z) == fi.SOLID or g.at(x, y, z) >= fi.DOOR:
            return z - direction * fi.CELL / 2
        z += direction * fi.CELL
    raise ValueError("no wall at x %s y %s" % (x, y))


def bulwark_x(z, y, side):
    """x of the inner face of the bulwark or parapet (side +1 port, -1 starboard) at (z, y), found from outside the
    hull inwards (past the stairs, the masts and the turret that wall_x would meet first)."""
    g = grid()
    x = 6.75
    while x > 0 and g.at(side * x, y, z) != fi.SOLID:
        x -= 0.5
    while x > 0 and g.at(side * x, y, z) == fi.SOLID:
        x -= 0.5
    return side * (x + 0.25)


def block(bid, x, y, z, facing="stern", solid=True, scale=1.0, centre=False):
    """A mod block. centre=True: (x, z) is the centre of its footprint (multi-block models whose bounds overflow their
    block on one side), otherwise the centre of its block."""
    yaw = FACING[facing] if isinstance(facing, str) else float(facing)
    if centre:
        x0, x1, _, _, z0, z1 = footprint(bid, x, y, z, yaw, scale)
        x, z = x - ((x0 + x1) / 2 - x), z - ((z0 + z1) / 2 - z)
    BLOCKS.append({"block": bid, "x": round(x, 4), "y": round(y, 4), "z": round(z, 4), "yaw": yaw, "solid": solid, "scale": scale,
                   "glow": bid in GLOWING})
    return len(BLOCKS) - 1


def custom(builder, solid=None, **kwargs):
    CUSTOM.append((builder, kwargs, solid))


def seat(x, y, z, dx, dy, dz):
    """A seat: where the passenger sits (seat height y) and where he stands up (dx, dy = floor, dz)."""
    SEATS.append({"x": x, "y": y, "z": z, "dx": dx, "dy": dy + 0.02, "dz": dz})


def chair(bid, x, floor, z, facing, stand):
    """A chair (not solid) centred at (x, z) and its seat; stand: where the sitter stands up (x, z)."""
    block(bid, x, floor, z, facing, solid=False, centre=True)
    seat(x, floor + SEAT_H[bid], z, stand[0], floor, stand[1])


def lantern(x, ceiling, z):
    """A kerosene lantern hanging on its chain from the beams (the chain reaches the ceiling)."""
    block(FD + "chained_kerosene_lantern", x, ceiling - 1.0, z, "stern", solid=False)


def wall_lantern(side, y, z):
    """A kerosene lantern on an iron bracket against a side wall (side +1 port, -1 starboard)."""
    w = wall_x(z, y, side)
    custom("bracket", name="bracket_%d" % len(CUSTOM), p=(w - side * 0.18, y, z), side=side)
    block(FD + "kerosene_lantern", w - side * 0.18, y, z, "stern", solid=False)


def crate_stack(x, y, z, n=2, facing="port", ids=(FU + "spruce_crate", FU + "dark_oak_crate")):
    for k in range(n):
        block(ids[k % len(ids)], x, y + k, z, facing)


def barrel_on_rack(x, y, z, along_x=False, bid=LI + "loaded_cypress_barrel"):
    """A barrel lying on its stand (along z, or along x)."""
    facing = "starboard" if along_x else "stern"
    block(LI + "simple_cypress_rack", x, y, z, facing, solid=False)
    block(bid, x, y + 0.12, z, facing)


def side_shield(name, side, z, y, behind="swords"):
    custom("wall_shield", name=name, center=(wall_x(z, y, side), y, z), normal=(-side, 0, 0), behind=behind)


# ---------------------------------------------------------------- the rooms
def captain_cabin():
    """Cabine du capitaine (under the quarterdeck, behind the castle's double door): the desk across the cabin facing
    the door, the captain's high-backed chair behind it against the three stern windows (the inside of every window
    drawn), two velvet chairs before it; the bed against the port side aft with the captain's chest at its foot, a
    dresser and the shield with crossed swords; his armour on its stand in the starboard corner aft, the sea chart,
    another dresser, the bookcase and the wardrobe; a weapon rack by the door; the red carpet with the white tower,
    an iron chandelier."""
    zw = wall_z(0.0, C + 1.0, -15.0, -1)                    # the stern wall (-19.0)
    zb = wall_z(0.0, C + 1.0, -15.0, 1)                     # the forward bulkhead (-9.5)
    for j, x in enumerate((-2.5, 0.0, 2.5)):
        custom("inner_window", name="cabin_stern_window_%d" % j, c=(x, 6.3, zw), normal=(0, 0, 1), w=1.0, h=1.25)
    for side in (1, -1):
        custom("inner_window", name="cabin_bulkhead_window_%s" % ("p" if side > 0 else "s"), c=(side * 2.4, 6.3, zb), normal=(0, 0, -1),
               w=0.8, h=0.9)
    # the desk facing the door, the captain's chair behind it, two guest chairs before it
    zd = -17.3
    block(FD + "desk", 0.0, C, zd, "stern", centre=True)
    top = C + 1.016
    chair(FU + "dark_oak_chair", 0.0, C, -18.45, "bow", (1.9, -18.55))
    for side in (1, -1):
        chair(FU + "crimson_chair", side * 0.75, C, -15.95, "stern", (side * 1.75, -15.6))
    custom("chart_sheet", name="cabin_chart", p=(-0.15, top, zd - 0.05), yaw=0.12)
    custom("compass_box", name="cabin_compass", p=(-0.95, top, zd + 0.05))
    custom("inkwell", name="cabin_ink", p=(0.85, top, zd + 0.1))
    custom("hourglass", name="cabin_hourglass", p=(1.2, top, zd - 0.2))
    block(FD + "kerosene_lantern", -1.25, top, zd - 0.2, "bow", solid=False)
    block(FD + "pile_of_books", 0.75, top, zd - 0.3, "bow", solid=False)
    block(FD + "red_wine_bottle", -0.65, top, zd - 0.35, "bow", solid=False)
    block(FD + "wine_glass", -0.45, top, zd - 0.2, "bow", solid=False)
    # port: the bed (head to the stern), the captain's chest at its foot, a dresser under the middle window, the shield
    block(FD + "double_bed", 3.45, C, -17.2, "bow", centre=True)
    custom("chest", solid=(2.95, 3.95, C, C + 0.65, -15.85, -15.25), name="captain_chest", p=(3.45, C, -15.55))
    xp = wall_x(-14.75, C + 0.5, 1)
    block(FD + "dresser", xp - 0.38, C, -14.4, "starboard", centre=True)
    block(FD + "cigar_box", xp - 0.4, C + 1.016, -14.65, "starboard", solid=False)
    custom("candlestick", name="cabin_candle_p", p=(xp - 0.4, C + 1.016, -14.1))
    side_shield("cabin_shield_p", 1, -12.45, 6.35)
    # port forward: a sea chest under the window, the weapon rack against the bulkhead
    xp2 = wall_x(-11.1, C + 0.5, 1)
    custom("chest", solid=(xp2 - 0.6, xp2 - 0.05, C, C + 0.65, -11.6, -10.6), name="cabin_chest_fwd", p=(xp2 - 0.33, C, -11.1), yaw=math.pi / 2)
    custom("weapon_rack", solid=(2.95, 4.65, C, C + 1.6, zb - 0.38, zb), name="cabin_rack", p=(3.8, C, zb), normal=(0, 0, -1), l=1.7, top=1.5,
           items=("halberd", "sword", "spear", "sword", "halberd"))
    # starboard: the armour stand in the corner aft, the sea chart between the windows, a dresser, the bookcase, the wardrobe
    custom("armour_stand", solid=(-3.85, -3.15, C, C + 1.9, -17.95, -17.25), name="cabin_armour", p=(-3.5, C, -17.6), facing="port",
           held="spear")
    xs = wall_x(-16.0, 6.3, -1)
    custom("wall_chart", name="cabin_sea_chart", center=(xs, 6.35, -16.05), normal=(1, 0, 0), w=0.8, h=0.62)
    xs2 = wall_x(-14.75, C + 0.5, -1)
    block(FD + "dresser", xs2 + 0.38, C, -14.4, "port", centre=True)
    block(FU + "book_pile", xs2 + 0.42, C + 1.016, -14.6, "port", solid=False)
    custom("candlestick", name="cabin_candle_s", p=(xs2 + 0.4, C + 1.016, -14.05))
    xs3 = wall_x(-12.4, C + 0.5, -1)
    block(FD + "tall_bookshelf", xs3 + 0.41, C, -12.4, "port", centre=True)
    block(FD + "wardrobe", -3.85, C, zb - 0.43, "stern", centre=True)
    # the middle: the carpet, the chandelier, a lantern by the door
    custom("tower_rug", name="cabin_rug", p=(0.0, C, -12.9), w=2.4, l=3.6)
    custom("iron_chandelier", name="chandelier_cabin", hook=(0.0, CABIN_CEIL, -13.6), drop=0.35, r=0.5, n=6)
    lantern(2.0, CABIN_CEIL, -10.6)


def keep_room():
    """La salle du conseil (the officers' room in the keep, on the quarterdeck): the war table across the room with the
    campaign map, its tokens and candlesticks, the commander's high-backed chair between two velvet chairs on the stern
    side, three more before it and one at its head; the tower banner on the stern wall between the windows, the
    bookcase, a shield with crossed spears between the starboard windows, an armour stand by the door, a weapon rack
    behind the stair; the stair to the battlements along the port side stays clear; an iron chandelier over the table."""
    f = Q
    zw = wall_z(0.0, f + 1.0, -16.0, -1)                    # the stern wall (-19.0)
    zf = wall_z(0.0, f + 1.0, -16.0, 1)                     # the front wall (-13.5)
    for j, x in enumerate((-2.2, 2.2)):
        custom("inner_window", name="keep_stern_window_%d" % j, c=(x, f + 1.35, zw), normal=(0, 0, 1), w=0.9, h=1.15)
    for j, x in enumerate((-2.6, 2.6)):
        custom("inner_window", name="keep_front_window_%d" % j, c=(x, f + 1.4, zf), normal=(0, 0, -1), w=0.8, h=1.0)
    custom("wall_banner", name="keep_banner", center=(0.0, f + 1.35, zw), normal=(0, 0, 1), w=1.0, h=1.8)
    # the war table: two ends with legs, a middle leaf, along x; the map, the candlesticks, a bottle and goblets
    zt, xt = -16.4, -1.9
    block(FD + "dining_table_side", xt + 1.0, f, zt, "port")
    block(FD + "dining_table_middle", xt, f, zt, "stern")
    block(FD + "dining_table_side", xt - 1.0, f, zt, "starboard")
    top = f + 1.0
    custom("war_map", name="keep_map", p=(xt, top, zt), w=2.3, l=0.72)
    block(FD + "red_wine_bottle", xt + 1.2, top, zt + 0.32, "stern", solid=False)
    block(FD + "wine_glass", xt + 0.95, top, zt + 0.38, "stern", solid=False)
    block(FD + "wine_glass", xt - 1.15, top, zt - 0.38, "stern", solid=False)
    # the chairs: the commander between two officers aft, three forward, one at the head (starboard end)
    for k, dx in enumerate((-1.0, 0.0, 1.0)):
        x = xt + dx
        stand = (x + 0.3 if dx < 0 else x, -18.45)
        if dx == 0.0:
            chair(FU + "dark_oak_chair", x, f, zt - 1.13, "bow", stand)
        else:
            chair(FU + "crimson_chair", x, f, zt - 1.1, "bow", stand)
        chair(FU + "crimson_chair", x, f, zt + 1.1, "stern", (x, -14.2))
    chair(FU + "crimson_chair", xt - 2.15, f, zt, "port", (xt - 2.1, -14.95))
    # starboard: the bookcase against the stern wall, the shield with crossed spears, the armour stand by the door
    block(FD + "tall_bookshelf", -3.55, f, zw + 0.41, "bow", centre=True)
    side_shield("keep_shield_s", -1, -16.85, f + 1.35, behind="swords")
    custom("armour_stand", solid=(-4.6, -3.9, f, f + 1.9, -14.55, -13.85), name="keep_armour", p=(-4.25, f, -14.2), facing="port", held="shield")
    # port, behind the stair's top: a weapon rack against the stern wall
    custom("weapon_rack", solid=(2.65, 3.95, f, f + 1.4, zw, zw + 0.38), name="keep_rack", p=(3.3, f, zw), normal=(0, 0, 1), l=1.3, top=1.3,
           items=("spear", "halberd", "spear", "halberd"))
    custom("iron_chandelier", name="chandelier_keep", hook=(xt, KEEP_CEIL, zt), drop=0.22, r=0.55, n=8)
    lantern(4.25, KEEP_CEIL, -16.2)


def turret_room():
    """La tourelle (on the keep's roof): the lookout's table with the chart and a lantern, his stool, the telescope on
    its tripod at the port window, the chest of signal flags, the inside of the windows, the tower banner aft."""
    zw = fi.ROOMS["turret"][4]                               # the stern wall (-18.5)
    xw = fi.ROOMS["turret"][1]                               # the side walls (+-2.0)
    for side in (1, -1):
        for j, z in enumerate((fs.TURRET_Z[0] + 1.1, fs.TURRET_Z[1] - 1.1)):
            custom("inner_window", name="turret_window_%s%d" % ("p" if side > 0 else "s", j), c=(side * xw, K + 2.0, z), normal=(-side, 0, 0),
                   w=0.8, h=1.0)
    for j, x in enumerate((-1.1, 1.1)):
        custom("inner_window", name="turret_back_window_%d" % j, c=(x, K + 2.0, zw), normal=(0, 0, 1), w=0.7, h=1.0)
    custom("wall_banner", name="turret_banner", center=(0.0, K + 1.85, zw), normal=(0, 0, 1), w=0.6, h=1.2)
    block(FU + "dark_oak_square_table", -1.45, K, -17.95, "stern")
    custom("chart_sheet", name="turret_chart", p=(-1.5, K + 1.0, -17.95), yaw=-0.2)
    block(FD + "kerosene_lantern", -1.7, K + 1.0, -18.2, "stern", solid=False)
    chair(FU + "spruce_stool", -1.45, K, -16.95, "stern", (-0.45, -16.95))
    custom("telescope", name="turret_telescope", p=(1.3, K, -17.6), facing="port")
    custom("flag_chest", solid=(1.1, 1.6, K, K + 0.5, -16.4, -15.7), name="turret_flags", p=(1.35, K, -16.05), yaw=math.pi / 2)
    lantern(0.0, TURRET_CEIL, -17.0)


def mess():
    """Le réfectoire de l'équipage (under the forecastle): the long table down the middle with a bench each side and a
    stool at its head, laid with plates, tankards, bread and cheese, a roast and wine; the galley in the port corner aft
    (the counter with its cutting board and spice rack, the stove and its pot, pans hanging over it, a tapped cask,
    hams); provisions in the starboard corner (vegetable crates, a cask, sacks); casks at the bow; the inside of the
    bulkhead's windows; lanterns."""
    f = M
    zb = wall_z(2.0, f + 1.0, 10.0, -1)                     # the aft bulkhead (6.5), beside the fore mast
    for side in (1, -1):
        custom("inner_window", name="mess_window_%s" % ("p" if side > 0 else "s"), c=(side * 3.3, 5.7, zb), normal=(0, 0, 1), w=0.7, h=0.7)
    # the long table along the ship: two ends and a middle leaf; a bench each side, a stool at the head
    block(FD + "dining_table_side", 0.0, f, 13.0, "stern")
    block(FD + "dining_table_middle", 0.0, f, 14.0, "starboard")
    block(FD + "dining_table_side", 0.0, f, 15.0, "bow")
    for z in (13.0, 14.0, 15.0):
        for side in (1, -1):
            block(FU + "spruce_bench", side * 1.05, f, z, "port", solid=False)
            seat(side * 1.05, f + 0.562, z, side * 1.95, f, z)
    chair(FU + "spruce_stool", 0.0, f, 16.05, "stern", (1.0, 16.2))
    top = f + 1.0
    for k, (x, z) in enumerate(((0.28, 12.8), (-0.28, 13.2), (0.28, 14.25), (-0.28, 14.75), (0.28, 15.25))):
        block(FU + "plate", x, top, z, "stern", solid=False, scale=0.45)
    custom("tankards", name="mess_tankards", pts=[(0.32, top, 13.15), (-0.3, top, 13.5), (0.3, top, 14.6), (-0.32, top, 15.15)])
    custom("bread_cheese", name="mess_bread", p=(0.0, top, 13.75))
    block(FR + "roast_chicken_block", 0.0, top, 14.4, "stern", solid=False, scale=0.5)
    block(FD + "wine_bottle", -0.25, top, 15.4, "stern", solid=False)
    # the galley (port, aft): counter, stove and pot, tapped cask, spice rack, pans, hams
    xg = wall_x(7.5, f + 0.5, 1)
    block(FD + "kitchen_counter", xg - 0.46, f, 7.0, "starboard", centre=True)
    block(FR + "cutting_board", xg - 0.7, top, 6.9, "starboard", solid=False, scale=0.6)
    block(FD + "seasoning_rack", xg - 0.5, top, 7.15, "starboard", solid=False)
    block(FR + "stove", xg - 0.5, f, 8.0, "starboard")
    block(FR + "cooking_pot", xg - 0.5, top, 8.0, "starboard", solid=False)
    block(LI + "tapped_cypress_barrel", xg - 0.5, f, 9.1, "starboard")
    custom("pot_rack", name="mess_pot_rack", p=(xg - 0.62, MESS_CEIL, 6.95), l=0.8)
    custom("hams", name="mess_hams", x0=xg - 1.5, x1=xg - 0.6, y=MESS_CEIL - 0.05, z=10.35, n=3)
    # provisions (starboard, aft): vegetable crates, a cask, a sack
    xs = wall_x(7.5, f + 0.5, -1)
    block(FR + "cabbage_crate", xs + 0.5, f, 7.0, "port")
    block(FR + "onion_crate", xs + 0.5, f, 8.0, "port")
    block(LI + "loaded_fir_barrel", xs + 0.5, f, 9.1, "port")
    block(FR + "rice_bag", xs + 1.5, f, 8.0, "port")
    # casks at the bow end
    for side in (1, -1):
        block(LI + "cypress_barrel", side * 2.35, f, 16.25, "stern")
    lantern(0.0, MESS_CEIL, 14.0)
    wall_lantern(-1, f + 1.15, 10.6)


def crew_quarters():
    """Les quartiers de l'équipage (lower deck, forward): double bunks along both sides, hammocks slung over the sea
    chests aft, the gaming table (dice and cards, tankards, a candle) with two stools, a coat rack; the fore mast
    through the middle; lanterns."""
    f = L
    for side in (1, -1):
        sn = "p" if side > 0 else "s"
        for z in (9.8, 12.05):
            w = wall_x(z, f + 0.5, side)
            x = w - side * 0.55
            custom("bunk2", solid=(min(x - side * 0.5, x + side * 0.5), max(x - side * 0.5, x + side * 0.5), f, f + 2.4, z - 0.95, z + 0.95),
                   name="crew_bunk_%s%d" % (sn, int(z * 10)), p=(x, f, z))
        w = wall_x(7.3, f + 0.5, side)
        for k, z in enumerate((6.85, 8.0)):
            x = w - side * 0.33
            custom("chest", solid=(min(x - side * 0.28, x + side * 0.28), max(x - side * 0.28, x + side * 0.28), f, f + 0.65, z - 0.5, z + 0.5),
                   name="crew_chest_%s%d" % (sn, k), p=(x, f, z), yaw=math.pi / 2)
        custom("hammock", name="crew_hammock_%s" % sn, a=(w - side * 0.75, HOLD_CEIL - 0.1, 6.25), b=(w - side * 0.75, HOLD_CEIL - 0.1, 8.65),
               sag=0.62, width=0.72)
    # the gaming table (port, by the door) and its stools
    block(FU + "dark_oak_square_table", 2.55, f, 7.4, "stern")
    custom("dice_cards", name="crew_dice", p=(2.5, f + 1.0, 7.4))
    custom("tankards", name="crew_tankards", pts=[(2.8, f + 1.0, 7.15), (2.3, f + 1.0, 7.7)])
    custom("candle", name="crew_candle", p=(2.85, f + 1.0, 7.7))
    chair(FU + "spruce_stool", 2.55, f, 6.5, "bow", (1.6, 6.5))
    chair(FU + "spruce_stool", 2.55, f, 8.3, "stern", (1.6, 8.35))
    block(FD + "coat_hanger", -2.5, f, 6.5, "stern", solid=False)
    lantern(0.0, HOLD_CEIL, 10.7)
    lantern(0.0, HOLD_CEIL, 12.9)


def hold():
    """La cale (lower deck, aft): the provisions (casks in pyramids on their stands, crates, vegetable crates, sacks,
    bales, baskets, jars), the armoury (weapon racks along the starboard side, shields with crossed swords on the
    aft wall, an armour stand, barrels of arrows, the armourer's anvil), the supplies for Havre-Fort (pallets of cut
    stone, squared timber), a spare red sail, crates under a lashed canvas; the centre line, the companionway's foot
    and the crew door stay clear; lanterns from the beams."""
    f = L
    za = wall_z(0.0, f + 1.0, -10.0, -1)                    # the aft wall (-15.0)
    # port, aft: casks lying on their stands in pyramids, then casks upright
    xw = wall_x(-12.0, f + 0.5, 1)
    for z in (-14.35, -13.25, -12.15):
        barrel_on_rack(xw - 0.55, f, z)
        barrel_on_rack(xw - 1.5, f, z)
        block(LI + "loaded_fir_barrel", xw - 1.02, f + 0.92, z, "stern", solid=False)
    for z in (-10.95, -9.9):
        block(LI + "fir_barrel", xw - 0.55, f, z, "port")
        block(LI + "cypress_barrel", xw - 1.5, f, z, "port")
    # port, before the companionway's foot: crates two high, provisions
    crate_stack(xw - 0.5, f, -8.6, 2)
    crate_stack(xw - 0.5, f, -7.55, 2, ids=(FU + "dark_oak_crate", FU + "spruce_crate"))
    block(FR + "potato_crate", xw - 1.5, f, -8.6, "port")
    block(FR + "carrot_crate", xw - 1.5, f, -7.55, "port")
    # port, forward of the companionway: sacks, bales, vegetable crates, baskets, jars
    xw2 = wall_x(1.0, f + 0.5, 1)
    block(FR + "rice_bag", xw2 - 0.5, f, -0.7, "port")
    block(FR + "rice_bag", xw2 - 0.5, f, 0.3, "port")
    block(FR + "rice_bag", xw2 - 0.5, f + 1.0, -0.2, "port", solid=False, scale=0.85)
    block(FR + "straw_bale", xw2 - 1.5, f, -0.7, "port")
    block(LI + "spelt_bale_block", xw2 - 1.5, f, 0.3, "port")
    block(FR + "cabbage_crate", xw2 - 0.5, f, 1.6, "port")
    block(FR + "onion_crate", xw2 - 1.5, f, 1.6, "port")
    block(FR + "beetroot_crate", xw2 - 0.5, f, 2.6, "port")
    block(FR + "wooden_basket", xw2 - 1.5, f, 2.6, "port")
    block(FR + "potato_crate", xw2 - 0.5, f + 1.0, 2.1, "port", solid=False, scale=0.9)
    block(LI + "storage_vase", xw2 - 0.5, f, 3.75, "stern")
    block(LI + "red_storage_vase", xw2 - 1.45, f, 3.8, "stern")
    block(FU + "amphora", xw2 - 0.5, f, 4.75, "stern")
    # starboard, aft: the armoury
    xs = wall_x(-12.0, f + 0.5, -1)
    custom("weapon_rack", solid=(xs, xs + 0.4, f, f + 1.7, -14.55, -12.75), name="hold_rack_0", p=(xs, f, -13.65), normal=(1, 0, 0), l=1.8, top=1.6,
           items=("spear", "halberd", "spear", "halberd", "spear", "halberd"))
    custom("weapon_rack", solid=(xs, xs + 0.4, f, f + 1.7, -12.3, -10.7), name="hold_rack_1", p=(xs, f, -11.5), normal=(1, 0, 0), l=1.6, top=1.6,
           items=("sword", "spear", "sword", "spear", "sword"))
    for k, x in enumerate((-2.2, -3.7)):
        custom("wall_shield", name="hold_shield_%d" % k, center=(x, f + 1.9, za), normal=(0, 0, 1), behind="swords")
    custom("armour_stand", solid=(-2.85, -2.15, f, f + 1.9, -14.55, -13.85), name="hold_armour", p=(-2.5, f, -14.2), facing="bow", held="spear")
    custom("arrow_barrel", solid=(xs + 0.2, xs + 0.8, f, f + 0.8, -10.15, -9.55), name="hold_arrows_0", p=(xs + 0.5, f, -9.85), seed=0)
    custom("arrow_barrel", solid=(xs + 0.95, xs + 1.55, f, f + 0.8, -10.15, -9.55), name="hold_arrows_1", p=(xs + 1.25, f, -9.85), seed=1)
    custom("anvil", solid=(-3.45, -2.75, f, f + 0.85, -12.2, -11.4), name="hold_anvil", p=(-3.1, f, -11.8), facing="bow")
    # starboard, middle: the stone and the timber for the fort, the spare sail
    custom("stone_pallet", solid=(xs + 0.05, xs + 1.25, f, f + 1.18, -8.75, -7.55), name="hold_stone_0", p=(xs + 0.65, f, -8.15))
    custom("stone_pallet", solid=(xs + 0.05, xs + 1.25, f, f + 1.18, -7.35, -6.15), name="hold_stone_1", p=(xs + 0.65, f, -6.75), yaw=0.04)
    custom("stone_pallet", solid=(xs + 1.45, xs + 2.65, f, f + 0.65, -8.75, -7.55), name="hold_stone_2", p=(xs + 2.05, f, -8.15), layers=1)
    custom("timber_stack", solid=(xs + 0.05, xs + 1.1, f, f + 0.8, -5.2, -2.6), name="hold_timber", p=(xs + 0.58, f, -3.9), l=2.5)
    custom("sail_roll", solid=(xs + 1.3, xs + 1.8, f, f + 0.45, -5.0, -2.8), name="hold_sail", p=(xs + 1.55, f, -3.9), l=2.2)
    # starboard, forward: crates under a lashed canvas, crates two high, jars, a sea chest, a coil of rope
    xs2 = wall_x(1.0, f + 0.5, -1)
    for z in (-0.4, 0.6):
        block(FU + "spruce_crate", xs2 + 0.5, f, z, "starboard")
        block(FU + "dark_oak_crate", xs2 + 1.5, f, z, "starboard")
    custom("tarp_stack", name="hold_tarp", p=(xs2 + 1.0, f, 0.1), w=2.0, d=2.0, h=1.0)
    crate_stack(xs2 + 0.5, f, 1.8, 2, facing="starboard")
    block(FU + "spruce_crate", xs2 + 1.5, f, 1.8, "starboard")
    block(LI + "gray_storage_vase", xs2 + 0.5, f, 3.0, "stern")
    block(FU + "gray_amphora", xs2 + 1.45, f, 3.05, "stern")
    custom("chest", solid=(xs2 + 0.05, xs2 + 0.6, f, f + 0.65, 3.85, 4.85), name="hold_chest", p=(xs2 + 0.33, f, 4.35), yaw=math.pi / 2)
    custom("coil", name="hold_coil", p=(xs2 + 1.4, f, 4.4), r=0.34)
    for z in (-12.0, -6.0, 2.5):
        lantern(0.0, HOLD_CEIL, z)


def deck():
    """Pont principal, gaillard, dunette, toit du donjon: the deck cargo of the references (crates two high, a crate
    lashed under canvas, barrels, sacks, rope coils at the masts) along the bulwarks of the waist; benches; on the
    quarterdeck a bench and a table under the awning, a cask and a coil; on the forecastle casks, crates and the
    anchor cable's coil; on the keep's roof a rack of spears by the battlements, a barrel of arrows, the signal brazier.
    Clear of the stairs, the companionway, the gangplank's stairs and lever, the capstan and the gratings, and of the
    boarding strip within 2.3 of the centre line."""
    # port waist, between the companionway and the forecastle stair: crates two high, a lashed crate, a cask, a sack
    xw = bulwark_x(0.5, M + 0.5, 1)
    crate_stack(xw - 0.5, M, -0.65, 2)
    crate_stack(xw - 0.5, M, 0.35, 2, ids=(FU + "dark_oak_crate", FU + "spruce_crate"))
    block(FU + "spruce_crate", xw - 1.5, M, 0.9, "port")
    custom("tarp_stack", name="deck_tarp_p", p=(xw - 1.5, M, 0.9), w=1.04, d=1.04, h=1.04)
    block(LI + "cypress_barrel", xw - 0.5, M, 1.4, "port")
    block(FR + "rice_bag", xw - 0.5, M + 0.91, 1.4, "port", solid=False, scale=0.7)
    custom("coil", name="deck_coil_p", p=(xw - 1.6, M, 1.9), r=0.32)
    # port, outboard of the quarterdeck stair: crates; outboard of the forecastle stair: casks
    xq = bulwark_x(-7.5, M + 0.5, 1)
    block(FU + "spruce_crate", xq - 0.5, M, -8.45, "port")
    block(FU + "dark_oak_crate", xq - 0.5, M, -7.4, "port")
    block(FU + "spruce_crate", xq - 0.5, M + 1.0, -7.95, "port", solid=False, scale=0.85)
    xf = bulwark_x(4.9, M + 0.5, 1)
    for z in (4.4, 5.4):
        block(LI + "fir_barrel", xf - 0.5, M, z, "port")
    # port bench beside the companionway
    block(FU + "spruce_bench", xw - 0.55, M, -2.6, "bow", solid=False)
    seat(xw - 0.55, M + 0.562, -2.6, xw - 0.55, M, -3.45)
    # starboard waist aft (before the gangplank's lever): crates two high, a cask, a bench
    xs = bulwark_x(-3.0, M + 0.5, -1)
    crate_stack(xs + 0.5, M, -3.6, 2, facing="starboard")
    block(FU + "spruce_crate", xs + 1.5, M, -3.6, "starboard")
    block(LI + "cypress_barrel", xs + 0.5, M, -2.6, "starboard")
    block(FU + "spruce_bench", xs + 1.6, M, -2.4, "port", solid=False)
    seat(xs + 1.6, M + 0.562, -2.4, xs + 2.45, M, -2.4)
    # starboard, outboard of the quarterdeck stair: crates and a sack; outboard of the forecastle stair: casks
    xq2 = bulwark_x(-7.5, M + 0.5, -1)
    block(FU + "dark_oak_crate", xq2 + 0.5, M, -8.45, "starboard")
    block(FU + "spruce_crate", xq2 + 0.5, M, -7.4, "starboard")
    block(FR + "rice_bag", xq2 + 0.5, M, -6.4, "starboard")
    xf2 = bulwark_x(4.9, M + 0.5, -1)
    for z in (4.4, 5.4):
        block(LI + "cypress_barrel", xf2 + 0.5, M, z, "starboard")
    # coils of rope at the main mast and by the capstan
    custom("coil", name="deck_coil_mast", p=(1.45, M, -2.0), r=0.3)
    custom("coil", name="deck_coil_capstan", p=(-1.5, M, 5.1), r=0.3)
    # the quarterdeck: under the awning (starboard) two benches against the parapet; a cask and a coil (port)
    xa = bulwark_x(-12.0, Q + 0.5, -1)
    for z in (-12.5, -11.5):
        block(FU + "dark_oak_bench", xa + 0.3, Q, z, "port", solid=False)
        seat(xa + 0.3, Q + 0.562, z, xa + 1.25, Q, z)
    xa2 = bulwark_x(-12.0, Q + 0.5, 1)
    block(LI + "loaded_cypress_barrel", xa2 - 0.5, Q, -12.4, "port")
    custom("coil", name="qd_coil", p=(xa2 - 1.45, Q, -12.5), r=0.3)
    # the forecastle: casks (port), crates two high and a sack (starboard), the anchor cable's coil at the bow
    for z in (10.4, 11.45):
        block(LI + "cypress_barrel" if z < 11 else LI + "fir_barrel", bulwark_x(z, F + 0.5, 1) - 0.5, F, z, "port")
    xc = bulwark_x(10.9, F + 0.5, -1)
    crate_stack(xc + 0.5, F, 10.4, 2, facing="starboard")
    block(FU + "spruce_crate", xc + 0.5, F, 11.45, "starboard")
    block(FR + "rice_bag", xc + 1.5, F, 10.4, "starboard")
    custom("coil", name="fc_coil_p", p=(2.6, F, 12.7), r=0.3)
    custom("coil", name="fc_cable", p=(0.0, F, 15.3), r=0.45)
    # the keep's roof (starboard walkway and front corner): a spear rack by the battlements, a barrel of arrows, the brazier
    xr = bulwark_x(-16.5, K + 0.5, -1)
    custom("weapon_rack", solid=(xr, xr + 0.4, K, K + 1.5, -17.2, -15.8), name="roof_rack", p=(xr, K, -16.5), normal=(1, 0, 0), l=1.4, top=1.3,
           items=("spear", "spear", "halberd", "spear"))
    custom("arrow_barrel", solid=(-3.55, -2.95, K, K + 0.8, -18.65, -18.05), name="roof_arrows", p=(-3.25, K, -18.35), seed=2)
    custom("brazier", solid=(-4.6, -3.8, K, K + 1.1, -14.6, -13.8), name="roof_brazier", p=(-4.2, K, -14.2))


def build():
    BLOCKS.clear()
    SEATS.clear()
    CUSTOM.clear()
    captain_cabin()
    keep_room()
    turret_room()
    mess()
    crew_quarters()
    hold()
    deck()
    return BLOCKS, SEATS


def _cells(g, box, min_overlap=0.2):
    """The grid cells under a solid box: the cells it overlaps by min_overlap or more on each axis (by its whole height if
    it is thinner, a rack)."""
    x0, x1, y0, y1, z0, z1 = box
    h = fi.CELL / 2
    ox = np.minimum(g.X + h, x1) - np.maximum(g.X - h, x0)
    oy = np.minimum(g.Y + h, y1) - np.maximum(g.Y - h, y0 + 0.01)
    oz = np.minimum(g.Z + h, z1) - np.maximum(g.Z - h, z0)
    return (ox >= min_overlap - 1e-6) & (oz >= min_overlap - 1e-6) & (oy >= min(min_overlap, y1 - y0 - 0.01) - 1e-6)


def _boxes():
    """(name, box, solid) of every piece of furniture: the solid custom pieces and every mod block (solid or not)."""
    boxes = [(kwargs.get("name", builder), solid, True) for builder, kwargs, solid in CUSTOM if solid is not None]
    for i, b in enumerate(BLOCKS):
        x0, x1, y0, y1, z0, z1 = footprint(b["block"], b["x"], b["y"], b["z"], b["yaw"], b["scale"])
        boxes.append(("%s #%d" % (b["block"], i), (x0, x1, b["y"], max(y1, b["y"] + 0.05), z0, z1), b["solid"]))
    return boxes


def apply_to_grid(g):
    """FURNITURE cells under the solid furniture (on the floor of a room, or on a deck). Every solid piece must be solid
    somewhere; no piece may stand in the walls, the decks or the hull (more than 0.3 into a solid cell), nor on the
    stairs; then the clearances of check()."""
    free = (g.k == fi.DRY) | (g.k == fi.OUT)
    solid_hull = g.k == fi.SOLID
    poking = [name for name, box, _ in _boxes() if (_cells(g, box, 0.3) & solid_hull).any()]
    assert not poking, "furniture in the walls or the hull: %s" % poking
    boxes = [(name, box) for name, box, solid in _boxes() if solid]
    for name, box in boxes:
        g.k[_cells(g, box) & free] = fi.FURNITURE
    hollow = [name for name, box in boxes if not (_cells(g, box) & (g.k == fi.FURNITURE)).any()]
    assert not hollow, "solid furniture with no FURNITURE cell: %s" % hollow
    check(g)


# places that stay free of solid furniture (x0, x1, y, z0, z1): a player (0.6 x 1.8) stands anywhere in them
CA, QA, CX = fs.QD_STAIR_X, fs.FC_STAIR_X, fs.COMPANION_X
KEEP_CLEAR = {
    "cabin door and centre line": (-0.8, 0.8, C, -16.1, -9.8),
    "keep door to the stair": (-0.8, 3.9, Q, -15.1, -13.6),
    "keep's stair foot": (fs.KEEP_STAIR_X[0], fs.KEEP_STAIR_X[1], Q, -15.4, -14.2),
    "keep, beside the table (game test)": (-0.2, 0.6, Q, -18.4, -14.0),
    "turret door and middle": (-0.6, 0.6, K, -17.8, -15.6),
    "keep's roof, front": (-1.8, 1.8, K, -14.9, -13.7),
    "mess door and aisle": (-1.3, 1.3, M, 6.6, 11.9),
    "crew door and aisle": (-1.3, 1.3, L, 6.1, 13.4),
    "hold aisle": (-1.2, 1.2, L, -14.4, 4.9),
    "companionway's foot": (CX[0] - 0.3, CX[1] + 0.3, L, -6.6, -5.1),
    "waist boarding strip": (-2.3, 2.3, M, -8.4, 4.4),
    "companionway's head (main deck)": (CX[0], CX[1], M, -1.4, -0.3),
    "quarterdeck stairs' feet (port)": (CA[0], CA[1], M, -5.3, -4.4),
    "quarterdeck stairs' feet (starboard)": (-CA[1], -CA[0], M, -5.3, -4.4),
    "forecastle stairs' feet (port)": (QA[0], QA[1], M, 2.4, 3.4),
    "forecastle stairs' feet (starboard)": (-QA[1], -QA[0], M, 2.4, 3.4),
    "gangplank stairs and landing": (-5.5, -3.0, M, -0.1, 3.3),
    "gangplank lever": (-5.3, -4.6, M, -0.7, 0.0),
    "quarterdeck, port of the mizzen": (1.2, 2.6, Q, -12.4, -10.0),
    "quarterdeck front": (-2.9, 2.9, Q, -10.4, -9.6),
    "forecastle middle": (-1.6, 1.6, F, 9.0, 13.2),
    "forecastle stairs' heads": (-QA[1], QA[1], F, 6.1, 6.9),
}


def _player_free(g, x, y, z, half=0.3, height=1.8):
    """No solid, furniture or window cell in the player's box standing at (x, y, z)."""
    sel = (np.abs(g.X - x) < half + fi.CELL / 2 - 1e-6) & (np.abs(g.Z - z) < half + fi.CELL / 2 - 1e-6) & (g.Y > y) & (g.Y < y + height)
    k = g.k[sel]
    return not ((k == fi.SOLID) | (k == fi.FURNITURE) | (k == fi.WINDOW)).any()


def check(g):
    """The clearances: the KEEP_CLEAR places hold no furniture cell; every seat's stand-up spot is free and on a floor;
    every room is still reachable from the main deck (doors open)."""
    blocked = []
    for name, (x0, x1, y, z0, z1) in KEEP_CLEAR.items():
        m = 0.3 + fi.CELL / 2 - 1e-6                         # the cells a player's box (0.6 wide) touches anywhere in the place
        sel = (g.X > x0 - m) & (g.X < x1 + m) & (g.Z > z0 - m) & (g.Z < z1 + m) & (g.Y > y) & (g.Y < y + 1.8)
        if (g.k[sel] == fi.FURNITURE).any():
            blocked.append(name)
    assert not blocked, "furniture in the places kept clear: %s" % blocked
    bad = []
    for i, s in enumerate(SEATS):
        dy = s["dy"] - 0.02
        under = g.at(s["dx"], dy - 0.25, s["dz"])
        if not _player_free(g, s["dx"], dy, s["dz"]) or under not in (fi.SOLID, fi.FURNITURE):
            bad.append((i, s["dx"], dy, s["dz"]))
    assert not bad, "seats whose stand-up spot is blocked or not on a floor: %s" % bad
    reached, _ = fi.walkable_report(g)
    lost = [k for k, v in reached.items() if not v]
    assert not lost, "rooms no longer reachable with the furniture: %s" % lost


def write(path):
    data = {"blocks": [], "seats": [{k: round(v, 4) for k, v in s.items()} for s in SEATS], "paintings": [], "switches": []}
    for i, b in enumerate(BLOCKS):
        data["blocks"].append({"block": b["block"], "x": round(b["x"], 4), "y": round(b["y"], 4), "z": round(b["z"], 4),
                               "yaw": b["yaw"], "scale": b["scale"], "fallback": "fallback_%d" % i})
        if b["glow"]:
            data["blocks"][-1]["glow"] = True
    with open(path, "w") as f:
        json.dump(data, f, indent=1)


DECOR_PATH = "src/main/resources/assets/medievalships/interiors/fortress_ship_decor.json"
