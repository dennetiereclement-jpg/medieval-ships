"""Furniture of the Royal Lion Ship (decoration phase): blocks of the decoration mods (drawn by the ship where they
stand, moving with it; never placed in the world), furniture modelled for the ship (drawn by
tools/generate_royal_lion.py with the builders of tools/royal_lion_furniture.py and of tools/corsair_furniture.py),
the vanilla paintings in their gold frames, and the seats.

  src/main/resources/assets/medievalships/interiors/royal_lion_ship_decor.json

Same format as tools/corsair_decor.py (read by fr.medievalships.core.InteriorDecor). A block whose mod is missing on
a client is replaced by its stand-in, a box of the same size in the model (bone "fallback_<i>"). The solid furniture
is added to the interior grid (FURNITURE cells): the players walk round the desk, the bed, the tables, the bunks and
the cargo.

The mods' blocks first (catalog /tmp/claude-0/mods_catalog/catalog.json: Farmhouse Decorations, Furnish, Farmer's
Delight, Lands of Icaria), modelled pieces only for what they lack or what must be royal (the blue carpets with the gold
lion, the gold chandeliers and candelabra, the window seat, the inside of the arched windows, the lion tapestries, the
open strongbox, the globe, the purser's desk, the white canvas bales of reference 044, the bolts of cloth, the
halberds of the guard, the hammocks and bunks of the crew).

Kept clear (checked here and by RoyalLionShipTest): the doors and their approaches, the stairs and the companionways
with their feet, the centre lines of the cabin, the crew quarters and the hold, the main deck within 1.9 of the centre
line (the boarding spots), the gangplank's stairs and lever (starboard, z 1.2..5.3), the seats' stand-up spots, the
places where the game test stands in each room. Nothing pokes through the hull (checked by apply_to_grid).
"""
import json
import math

import numpy as np

import royal_lion_interior as fi
import royal_lion_shape as fs

# front faces: yaw of the block about the vertical (its model's north is its front)
FACING = {"stern": 0.0, "starboard": 90.0, "bow": 180.0, "port": 270.0}

FD = "farmhouse_decorations:"
FU = "furnish:"
FR = "farmersdelight:"
LI = "landsoficaria:"

# model bounds of the default state (block space, x east, z south, the front is north; element and
# blockstate rotations applied), from the mods catalog ("bounds")
BOUNDS = {
    FD + "desk": (-0.953, 1.984, 0, 1.016, -0.031, 1.031),
    FD + "dining_chair": (0.125, 0.875, 0, 1.563, 0, 0.973),
    FD + "double_bed": (-0.984, 0.984, 0, 1.203, 0.016, 1.984),
    FD + "tall_bookshelf": (0, 1, 0, 1.969, 0.188, 1),
    FD + "night_stand": (0.188, 0.812, 0, 0.625, 0.5, 1),
    FD + "kerosene_lantern": (0.37, 0.63, 0, 0.484, 0.375, 0.625),
    FD + "chained_kerosene_lantern": (0.37, 0.63, 0.328, 1, 0.375, 0.625),
    FD + "pile_of_books": (0.283, 0.643, 0.002, 0.234, 0.403, 0.732),
    FD + "cigar_box": (0.25, 0.75, 0, 0.547, 0.312, 0.734),
    FD + "wine_bottle": (0.391, 0.547, 0, 0.328, 0.422, 0.578),
    FD + "red_wine_bottle": (0.391, 0.547, 0, 0.328, 0.422, 0.578),
    FD + "wine_glass": (0.438, 0.562, 0, 0.25, 0.438, 0.562),
    FD + "liquor_cabinet": (-1, 1, 0, 1, 0.297, 1),
    FD + "coat_hanger": (0.078, 0.922, -0.048, 1.953, 0.078, 0.922),
    FD + "wardrobe": (-0.844, 0.844, 0, 1.984, 0.156, 1),
    FD + "dresser": (0, 1, 0, 1.016, 0.25, 1),
    FD + "dining_table_side": (0, 1, -0.016, 1, 0.016, 0.984),
    FD + "dining_table_middle": (0, 1, 0.797, 1, 0.016, 0.984),
    FD + "kitchen_counter": (0, 1, 0, 1, 0.078, 1),
    FD + "cuckoo_clock": (0.203, 0.797, 0.172, 0.969, 0.812, 1),
    FD + "typewriter": (0.125, 0.875, 0, 0.503, 0.031, 0.961),
    FU + "dark_oak_chair": (0.062, 0.938, 0, 1.875, 0, 0.812),
    FU + "crimson_chair": (0.125, 0.875, -0.038, 1, 0, 0.75),
    FU + "crimson_stool": (0.188, 0.812, 0, 0.562, 0.125, 0.75),
    FU + "picture_frame": (0.25, 0.75, 0.002, 0.609, 0.219, 0.632),
    FU + "rare_english_plate": (0.062, 0.938, 0, 0.062, 0.062, 0.938),
    FU + "plate": (0.062, 0.938, 0, 0.062, 0.062, 0.938),
    FU + "book_pile": (0.167, 0.88, 0.013, 0.394, 0.182, 0.865),
    FU + "spruce_crate": (0, 1, 0, 1, 0, 1),
    FU + "dark_oak_crate": (0, 1, 0, 1, 0, 1),
    FU + "spruce_stool": (0.188, 0.812, 0, 0.562, 0.125, 0.75),
    FU + "spruce_bench": (0, 1, 0, 0.562, 0.25, 0.75),
    FU + "dark_oak_bench": (0, 1, 0, 0.562, 0.25, 0.75),
    FU + "amphora": (0, 1, 0, 1, 0.125, 0.875),
    FU + "blue_amphora": (0, 1, 0, 1, 0.125, 0.875),
    FU + "yellow_amphora": (0, 1, 0, 1, 0.125, 0.875),
    FR + "potato_crate": (0, 1, 0, 1, 0, 1),
    FR + "carrot_crate": (0, 1, 0, 1, 0, 1),
    FR + "cabbage_crate": (0, 1, 0, 1, 0, 1),
    FR + "onion_crate": (0, 1, 0, 1, 0, 1),
    FR + "rice_bag": (0, 1, 0, 1, 0, 1),
    FR + "straw_bale": (0, 1, 0, 1, 0, 1),
    FR + "stove": (0, 1, 0, 1, 0, 1),
    FR + "cooking_pot": (0, 1, 0, 0.904, 0.125, 0.875),
    FR + "cutting_board": (0.062, 0.938, 0, 0.062, 0.062, 0.938),
    FR + "roast_chicken_block": (0.062, 0.938, 0, 0.5, 0.062, 0.938),
    LI + "cypress_barrel": (0.047, 0.953, 0, 0.906, 0, 1),
    LI + "fir_barrel": (0.047, 0.953, 0, 0.906, 0, 1),
    LI + "loaded_cypress_barrel": (0.047, 0.953, 0, 0.906, 0, 1),
    LI + "loaded_fir_barrel": (0.047, 0.953, 0, 0.906, 0, 1),
    LI + "tapped_cypress_barrel": (0.047, 0.953, 0, 0.906, -0.246, 1),
    LI + "simple_cypress_rack": (0, 1, 0, 0.125, 0.125, 0.875),
    LI + "spelt_bale_block": (0, 1, 0, 1, 0, 1),
    LI + "storage_vase": (0.062, 0.938, 0, 1, 0.062, 0.938),
    LI + "blue_storage_vase": (0.062, 0.938, 0, 1, 0.062, 0.938),
}

# stand-in look when the mod is missing (default: a box of mid brown wood)
FALLBACK_REGION = {FD + "chained_kerosene_lantern": "lantern", FD + "kerosene_lantern": "lantern", FD + "wine_bottle": "glass",
                   FD + "red_wine_bottle": "glass", FD + "wine_glass": "glass", FD + "pile_of_books": "books", FU + "book_pile": "books",
                   FR + "rice_bag": "sack", FD + "tall_bookshelf": "books", FU + "spruce_crate": "wood_light", FU + "dark_oak_crate": "wood_dark",
                   FU + "dark_oak_bench": "wood_dark", FD + "desk": "wood_dark", FD + "liquor_cabinet": "wood_dark", FD + "wardrobe": "wood_dark",
                   FD + "dresser": "wood_dark", FD + "dining_table_side": "wood_dark", FD + "dining_table_middle": "wood_dark",
                   LI + "storage_vase": "red_paint", LI + "blue_storage_vase": "hull_blue", FU + "amphora": "red_paint",
                   FU + "blue_amphora": "hull_blue", FU + "yellow_amphora": "gold", FD + "cigar_box": "red_paint", FD + "double_bed": "bedding",
                   FU + "dark_oak_chair": "wood_dark", FU + "crimson_chair": "gold", FU + "crimson_stool": "gold", FD + "coat_hanger": "wood_dark",
                   FU + "rare_english_plate": "white_paint", FU + "plate": "white_paint", FR + "straw_bale": "rope_light",
                   LI + "spelt_bale_block": "rope_light", FR + "stove": "wall_stone", FR + "cooking_pot": "iron", FD + "kitchen_counter": "wood_dark",
                   FR + "roast_chicken_block": "ham", FU + "picture_frame": "gold", FD + "cuckoo_clock": "wood_dark", LI + "simple_cypress_rack": "wood_dark"}

GLOWING = {FD + "kerosene_lantern", FD + "chained_kerosene_lantern"}   # drawn full-bright while the lamps are lit
SEAT_H = {FU + "dark_oak_chair": 0.562, FU + "crimson_chair": 0.5, FU + "crimson_stool": 0.562, FU + "spruce_stool": 0.562,
          FU + "spruce_bench": 0.562, FU + "dark_oak_bench": 0.562}

BLOCKS = []     # dicts: block, x, y, z, yaw, solid, scale
SEATS = []      # dicts: x, y, z, dx, dy, dz
CUSTOM = []     # furniture drawn by generate_royal_lion: (builder name, kwargs, solid box or None)
PAINTINGS = []  # vanilla paintings: motive, centre, normal, size

M, L, C, Q, F = fs.MAIN_DECK_Y, fs.LOWER_FLOOR_Y, fs.CABIN_FLOOR_Y, fs.QUARTERDECK_Y, fs.FORECASTLE_Y
HOLD_CEIL, CABIN_CEIL, STATE_CEIL = M - fs.SLAB, Q - fs.SLAB, fs.ROUNDHOUSE_CEIL_Y

_GRID = []


def grid():
    """The interior grid without the furniture (built once), to find the faces of the walls."""
    if not _GRID:
        _GRID.append(fi.build())
    return _GRID[0]


def wall_x(z, y, side):
    """x of the inner face of the side wall (side +1 port, -1 starboard) at (z, y): the outer edge of the outermost open
    cell going out from the centre line."""
    g = grid()
    x = 0.25
    while x < 7.0:
        if g.at(side * x, y, z) == fi.SOLID:
            return side * (x - 0.25)
        x += 0.5
    raise ValueError("no wall at z %s y %s" % (z, y))


def wall_z(x, y, z_from, direction):
    """z of the inner face of the end wall met going from z_from along direction (-1 aft, +1 forward) at (x, y)."""
    g = grid()
    z = math.floor(z_from / fi.CELL) * fi.CELL + fi.CELL / 2
    while abs(z) < 30:
        if g.at(x, y, z) in (fi.SOLID,) or g.at(x, y, z) >= fi.DOOR:
            return z - direction * fi.CELL / 2
        z += direction * fi.CELL
    raise ValueError("no wall at x %s y %s" % (x, y))


def to_ship(x, y, z, yaw, px, py, pz, scale=1.0):
    """Ship-local point of a point (px, py, pz) of the block model placed at (x, y, z) with yaw (degrees),
    the same transform as the renderer: translate, rotate about y, scale, then (-0.5, 0, -0.5)."""
    qx, qz = (px - 0.5) * scale, (pz - 0.5) * scale
    a = math.radians(yaw)
    c, s = math.cos(a), math.sin(a)
    return x + qx * c + qz * s, y + py * scale, z - qx * s + qz * c


def footprint(bid, x, y, z, yaw, scale=1.0):
    b = BOUNDS[bid]
    pts = [to_ship(x, y, z, yaw, px, py, pz, scale) for px in (b[0], b[1]) for py in (b[2], b[3]) for pz in (b[4], b[5])]
    xs, ys, zs = zip(*pts)
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def block(bid, x, y, z, facing="stern", solid=True, scale=1.0, centre=False):
    """A mod block. centre=True: (x, z) is the centre of its footprint (multi-block models whose
    bounds overflow their block on one side), otherwise the centre of its block."""
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


def painting(name, motive, center, normal, w, h):
    """A vanilla painting (drawn by the renderer with the game's own texture) in a carved gold frame."""
    custom("painting_frame", name=name, center=center, normal=normal, w=w, h=h)
    n = math.hypot(normal[0], normal[2])
    PAINTINGS.append({"motive": motive, "x": center[0] + normal[0] / n * 0.03, "y": center[1], "z": center[2] + normal[2] / n * 0.03,
                      "nx": normal[0] / n, "nz": normal[2] / n, "w": w, "h": h})


def side_window(name, side, z, y, w, h):
    """The inside of an arched window of a side wall."""
    custom("inner_window", name=name, c=(wall_x(z, y, side), y, z), normal=(-side, 0, 0), w=w, h=h)


def crate_stack(x, y, z, n=2, facing="port", ids=(FU + "spruce_crate", FU + "dark_oak_crate")):
    for k in range(n):
        block(ids[k % len(ids)], x, y + k, z, facing)


def barrel_on_rack(x, y, z, along_x=False, bid=LI + "loaded_cypress_barrel"):
    """A barrel lying on its stand (along z, or along x)."""
    facing = "starboard" if along_x else "stern"
    block(LI + "simple_cypress_rack", x, y, z, facing, solid=False)
    block(bid, x, y + 0.12, z, facing)


# ---------------------------------------------------------------- the rooms
def captain_cabin():
    """Cabine du capitaine (main deck level, under the quarterdeck): the cushioned window seat under the four arched
    stern windows (the inside of every window shown), the double bed against the port side under a lion tapestry, the
    open strongbox of gold at its foot, a dresser and the tall bookcase by the door; the desk on the starboard side
    with the captain's chair, the chart, the compass, books and coins, a sea chart on the wall, the telescope at the
    stern windows, the globe and the wardrobe by the door; the royal blue carpet with the gold lion in the middle, the
    gold chandelier, lanterns on the walls, a gold-framed painting on the bulkhead."""
    zw = wall_z(0.0, C + 1.0, -15.0, -1)                    # the stern wall (-19.5)
    # the window seat and the stern windows
    custom("window_seat", solid=(-3.5, 3.5, C, C + 0.5, zw, zw + 0.62), name="cabin_window_seat", x0=-3.5, x1=3.5, z_wall=zw, y=C)
    for x in (-1.0, 1.0):
        seat(x, C + 0.48, zw + 0.32, x, C, zw + 1.05)
    for j, x in enumerate((-2.85, -0.95, 0.95, 2.85)):
        custom("inner_window", name="cabin_stern_window_%d" % j, c=(x, 6.35, zw), normal=(0, 0, 1), w=0.95, h=1.55)
    for side in (1, -1):
        for j, z in enumerate((-18.4, -15.75, -13.15)):
            side_window("cabin_window_%s%d" % ("p" if side > 0 else "s", j), side, z, 6.35, 1.0, 1.5)
    zb = wall_z(0.0, C + 1.0, -15.0, 1)                     # the forward bulkhead (-11.0)
    for side in (1, -1):
        custom("inner_window", name="cabin_bulkhead_window_%s" % ("p" if side > 0 else "s"), c=(side * 1.9, 6.0, zb), normal=(0, 0, -1),
               w=0.75, h=1.2)
    # port: the bed under the lion tapestry, the night stand, the strongbox at the foot of the bed, the dresser, the bookcase
    block(FD + "double_bed", 3.45, C, -17.0, "bow", centre=True)
    block(FD + "night_stand", 1.95, C, -18.2, "bow", centre=True)
    block(FD + "kerosene_lantern", 1.95, C + 0.625, -18.15, "bow", solid=False)
    custom("tapestry", name="cabin_tapestry", center=(wall_x(-17.1, 6.3, 1), 6.3, -17.1), normal=(-1, 0, 0), w=0.9, h=1.2)
    custom("strongbox", solid=(2.95, 3.95, C, C + 0.55, -15.8, -15.2), name="cabin_strongbox", p=(3.45, C, -15.5), yaw=0.0)
    block(FD + "dresser", 4.55, C, -13.2, "starboard", centre=True)
    block(FD + "cigar_box", 4.55, C + 1.016, -13.45, "starboard", solid=False)
    block(FU + "picture_frame", 4.6, C + 1.016, -12.85, "starboard", solid=False)
    block(FD + "tall_bookshelf", 4.5, C, -11.55, "starboard", centre=True)
    # starboard: the desk and the captain's chair, what lies on the desk, the sea chart on the wall, the telescope
    block(FD + "desk", -4.0, C, -15.0, "port", centre=True)
    top = C + 1.016
    chair(FU + "dark_oak_chair", -2.75, C, -15.0, "starboard", (-1.85, -15.0))
    custom("chart_sheet", name="cabin_chart", p=(-4.05, top, -15.05), yaw=0.15)
    custom("compass_box", name="cabin_compass", p=(-3.95, top, -15.95))
    custom("coin_stacks", name="cabin_coins", pts=[(-3.8, top, -14.2), (-3.95, top, -14.0), (-3.7, top, -13.95)])
    block(FD + "pile_of_books", -4.25, top, -16.2, "port", solid=False)
    block(FD + "kerosene_lantern", -4.3, top, -13.85, "port", solid=False)
    block(FD + "red_wine_bottle", -4.3, top, -14.4, "port", solid=False)
    block(FD + "wine_glass", -4.05, top, -14.55, "port", solid=False)
    xw = wall_x(-17.1, 6.2, -1)
    custom("wall_chart", name="cabin_sea_chart", center=(xw, 6.25, -17.1), normal=(1, 0, 0), w=0.95, h=0.7)
    custom("telescope", name="cabin_telescope", p=(-3.55, C, -18.45), facing="starboard")
    # forward starboard: the wardrobe against the bulkhead, the globe
    block(FD + "wardrobe", -3.6, C, zb - 0.43, "stern", centre=True)
    custom("globe", solid=(-3.25, -2.65, C, C + 1.3, -12.45, -11.85), name="cabin_globe", p=(-2.95, C, -12.15))
    # the middle: the carpet, the chandelier, lanterns on the walls, the painting on the bulkhead
    custom("royal_rug", name="cabin_rug", p=(0.0, C, -15.2), w=3.0, l=4.0)
    custom("chandelier", name="chandelier_cabin", hook=(0.0, CABIN_CEIL, -15.4), drop=0.5, r=0.5, n=6)
    lantern(-3.6, CABIN_CEIL, -15.5)
    for side in (1, -1):
        wall_lantern(side, 6.0, -14.45)
    painting("cabin_painting", "sea", (3.2, 6.3, zb), (0, 0, -1), 1.1, 0.6)


def stateroom():
    """Salle d'apparat (the roundhouse on the quarterdeck, under the blue roof): the long dining table across the room
    with three gold-trimmed velvet chairs on the stern side and two high-backed thrones at its ends, laid with fine
    plates, glasses, a roast and a gold candelabra; the liquor cabinet and two dressers along the side walls, the
    royal tapestry between the middle stern windows, gold-framed portraits beside the door, the gold chandelier, the
    inside of every arched window."""
    f = Q
    zw = wall_z(0.0, f + 1.0, -17.5, -1)                    # the stern wall (-19.5)
    zf = wall_z(0.0, f + 1.0, -17.5, 1)                     # the front wall (-16.5)
    wy, ww, wh = f + 1.6, 0.85, 1.3
    for j, x in enumerate((-2.7, -0.9, 0.9, 2.7)):
        custom("inner_window", name="state_stern_window_%d" % j, c=(x, wy, zw), normal=(0, 0, 1), w=ww, h=wh)
    for side in (1, -1):
        for j, z in enumerate((-19.0, -17.5)):
            side_window("state_window_%s%d" % ("p" if side > 0 else "s", j), side, z, wy, 0.8, wh)
        custom("inner_window", name="state_front_window_%s" % ("p" if side > 0 else "s"), c=(side * 2.75, wy, zf), normal=(0, 0, -1), w=ww,
               h=wh)
    # the table: two ends with turned legs, a middle leaf
    zt = -18.0
    block(FD + "dining_table_side", 1.0, f, zt, "port")
    block(FD + "dining_table_middle", 0.0, f, zt, "stern")
    block(FD + "dining_table_side", -1.0, f, zt, "starboard")
    for x in (-1.0, 0.0, 1.0):
        chair(FU + "crimson_chair", x, f, zw + 0.42, "bow", (x, zw + 0.42))
    for side in (1, -1):
        chair(FU + "dark_oak_chair", side * 2.25, f, zt, "starboard" if side > 0 else "port", (side * 2.3, zt + 1.0))
    custom("royal_rug", name="state_rug", p=(0.0, f, zt), w=2.3, l=3.4, yaw=math.pi / 2)
    top = f + 1.0
    custom("candelabra", name="state_candelabra", p=(0.0, top, zt + 0.12))
    for x in (-1.0, 0.0, 1.0):
        block(FU + "rare_english_plate", x, top, zt - 0.22, "stern", solid=False, scale=0.5)
        block(FD + "wine_glass", x + 0.28, top, zt - 0.3, "stern", solid=False)
    for side in (1, -1):
        block(FU + "rare_english_plate", side * 1.25, top, zt, "stern", solid=False, scale=0.5)
    block(FR + "roast_chicken_block", -0.55, top, zt + 0.18, "stern", solid=False, scale=0.55)
    block(FD + "red_wine_bottle", 0.5, top, zt + 0.22, "stern", solid=False)
    block(FD + "wine_bottle", 0.72, top, zt + 0.1, "stern", solid=False)
    # along the walls: the liquor cabinet (port), two dressers (starboard) with a candelabra and a framed picture
    xp = wall_x(-17.5, f + 0.5, 1)
    block(FD + "liquor_cabinet", xp - 0.36, f, -17.6, "starboard", centre=True)
    xs = wall_x(-17.5, f + 0.5, -1)
    block(FD + "dresser", xs + 0.38, f, -17.05, "port", centre=True)
    block(FD + "dresser", xs + 0.38, f, -18.05, "port", centre=True)
    custom("candelabra", name="state_candelabra_side", p=(xs + 0.4, f + 1.016, -17.05))
    block(FU + "picture_frame", xs + 0.42, f + 1.016, -18.1, "port", solid=False)
    # the royal tapestry over the middle chair, the portraits beside the door, the chandelier, lanterns
    custom("tapestry", name="state_tapestry", center=(0.0, f + 1.75, zw), normal=(0, 0, 1), w=0.5, h=0.85)
    painting("state_portrait_p", "bust", (1.75, f + 1.6, zf), (0, 0, -1), 0.6, 0.6)
    painting("state_portrait_s", "wanderer", (-1.75, f + 1.55, zf), (0, 0, -1), 0.45, 0.85)
    custom("chandelier", name="chandelier_state", hook=(0.0, STATE_CEIL, zt + 0.05), drop=0.45, r=0.45, n=6)
    for side in (1, -1):
        wall_lantern(side, f + 2.1, -18.25)


def crew_quarters():
    """Quartiers de l'equipage (lower deck, aft): the mess table on the port side with its benches, plates and tankards;
    double bunks against the hull aft with sea chests at their feet, two hammocks slung on the starboard side over
    more sea chests; the galley corner forward on the port side (the stove and its pot, a counter, the pots and pans
    hanging from a rail, water casks), the halberds of the guard on the bulkhead, a coat rack, provisions, lanterns."""
    f = L
    # the mess: the long table along the ship, a bench on each side
    xt = 3.65
    block(FD + "dining_table_side", xt, f, -10.5, "stern")
    block(FD + "dining_table_middle", xt, f, -9.5, "starboard")
    block(FD + "dining_table_side", xt, f, -8.5, "bow")
    for z in (-10.5, -9.5, -8.5):
        block(FU + "spruce_bench", 2.55, f, z, "port", solid=False)
        block(FU + "spruce_bench", 4.75, f, z, "port", solid=False)
    for z in (-10.4, -8.6):
        seat(2.55, f + 0.562, z, 1.65, f, z)
        seat(4.75, f + 0.562, z, 4.75, f, z)
    custom("mess_ware", name="crew_mess", pts=[(xt - 0.25, f + 1.0, -10.6), (xt + 0.25, f + 1.0, -9.9), (xt - 0.25, f + 1.0, -8.9),
                                               (xt + 0.25, f + 1.0, -8.3)])
    block(FD + "kerosene_lantern", xt, f + 1.0, -9.45, "stern", solid=False)
    lantern(xt, HOLD_CEIL, -9.5)
    # the bunks against the hull aft, the sea chests at their feet
    for side in (1, -1):
        x = side * 4.4
        custom("bunk2", solid=(x - 0.5, x + 0.5, f, f + 2.4, -14.15, -12.25), name="crew_bunk_%s" % ("p" if side > 0 else "s"),
               p=(x, f, -13.2), l=1.9, w=1.0)
        custom("chest", solid=(x - 0.5, x + 0.5, f, f + 0.65, -11.98, -11.42), name="crew_chest_%s" % ("p" if side > 0 else "s"),
               p=(x, f, -11.7))
    # starboard: two hammocks slung along the ship, sea chests under them
    for k, x in enumerate((-3.25, -4.55)):
        custom("hammock", name="crew_hammock_%d" % k, a=(x, HOLD_CEIL - 0.12, -11.0 + 0.2 * k), b=(x, HOLD_CEIL - 0.12, -7.7 + 0.2 * k),
               sag=0.75, width=0.75)
    custom("chest", solid=(-5.0, -4.0, f, f + 0.65, -9.88, -9.32), name="crew_chest_h0", p=(-4.5, f, -9.6))
    custom("chest", solid=(-3.75, -2.75, f, f + 0.65, -8.98, -8.42), name="crew_chest_h1", p=(-3.25, f, -8.7), yaw=0.0)
    # the galley corner (port, forward): the stove and its pot, a counter with a cutting board, pans on a rail, casks
    xg = 4.6
    block(FD + "kitchen_counter", xg, f, -7.0, "starboard")
    block(FR + "cutting_board", xg, f + 1.0, -7.0, "starboard", solid=False)
    block(FR + "stove", xg, f, -6.0, "starboard")
    block(FR + "cooking_pot", xg, f + 1.0, -6.0, "starboard", solid=False)
    custom("pot_rack", name="crew_pot_rack", p=(xg - 0.55, HOLD_CEIL, -6.5), l=1.3)
    block(LI + "tapped_cypress_barrel", xg, f, -4.95, "starboard")
    block(LI + "tapped_cypress_barrel", xg, f, -3.95, "starboard")
    # starboard forward: the halberds of the guard on the bulkhead, a coat rack, a cask, a sack
    zb = wall_z(-3.5, f + 1.0, -5.0, 1)
    custom("halberd_rack", name="crew_halberds", p=(-3.9, f, zb), normal=(0, 0, -1), n=4)
    block(FD + "coat_hanger", -2.75, f, -3.6, "stern", solid=False)
    barrel_on_rack(-4.6, f, -5.4, along_x=False)
    block(FR + "rice_bag", -4.6, f, -6.6, "starboard")
    lantern(0.6, HOLD_CEIL, -12.5)
    lantern(0.6, HOLD_CEIL, -5.5)


def hold():
    """Cale (lower deck, forward): the purser's desk against the bulkhead (ledger, scales, coins) and his stool; the
    trade goods along the sides: bolts of cloth on a rack, white canvas bales, crates two high, provisions crates,
    barrels on their stands in pyramids, sacks, straw and spelt bales, amphoras and storage jars at the bow; the
    centre line, the stair's foot and the bulkhead door stay clear; lanterns from the beams."""
    f = L
    # the purser (starboard, against the bulkhead)
    zb = wall_z(-3.5, f + 1.0, 0.0, -1)                     # the bulkhead's forward face (-2.5)
    custom("purser_desk", solid=(-4.15, -3.05, f, f + 1.1, zb, zb + 0.66), name="hold_purser", p=(-3.6, f, zb + 0.33), yaw=0.0)
    chair(FU + "spruce_stool", -3.6, f, zb + 1.1, "stern", (-2.6, zb + 1.1))
    lantern(-2.9, HOLD_CEIL, -0.6)
    # starboard: crates two high, provisions, the crates at z 4.5 (kept solid: RoyalLionShipTest), the cloth
    crate_stack(-4.75, f, 0.3, 2)
    crate_stack(-4.75, f, 1.3, 2, ids=(FU + "dark_oak_crate", FU + "spruce_crate"))
    block(FR + "potato_crate", -3.75, f, 0.3, "starboard")
    block(FR + "carrot_crate", -3.75, f, 1.3, "starboard")
    block(FR + "cabbage_crate", -3.75, f + 1.0, 0.8, "starboard", solid=False, scale=0.9)
    crate_stack(-4.6, f, 4.5, 2)
    block(FU + "spruce_crate", -4.6, f, 5.5, "starboard")
    block(FU + "dark_oak_crate", -3.6, f, 4.5, "starboard")
    custom("bale", solid=(-5.1, -4.1, f + 1.0, f + 1.8, 5.05, 5.95), name="hold_bale_0", p=(-4.6, f + 1.0, 5.5), w=1.0, h=0.8, d=0.9)
    custom("cloth_bolts", solid=(-4.45, -3.35, f, f + 1.1, 6.75, 8.25), name="hold_cloth", p=(-3.9, f, 7.5), yaw=math.pi / 2, rows=3, cols=3,
           l=1.4)
    custom("bale", solid=(-4.3, -3.1, f, f + 0.85, 9.0, 10.0), name="hold_bale_1", p=(-3.7, f, 9.5), w=1.2, h=0.85, d=1.0)
    custom("bale", solid=(-4.15, -3.25, f + 0.85, f + 1.55, 9.1, 9.9), name="hold_bale_2", p=(-3.7, f + 0.85, 9.5), yaw=0.3, w=0.9, h=0.7,
           d=0.8)
    block(FR + "rice_bag", -3.4, f, 10.7, "starboard")
    custom("counted_sacks", solid=(-3.75, -2.6, f, f + 0.65, 11.5, 12.1), name="hold_spices", p=(-3.2, f, 11.8), yaw=math.pi / 2, n=3)
    block(LI + "storage_vase", -2.9, f, 13.1, "stern")
    block(LI + "blue_storage_vase", -2.0, f, 13.6, "stern")
    # port: barrels on stands (two below, one on top), crates, sacks by the stair, straw, white bales, amphoras
    for z in (-1.75, -0.65):
        barrel_on_rack(4.65, f, z)
        barrel_on_rack(3.7, f, z)
        block(LI + "loaded_fir_barrel", 4.18, f + 0.92, z, "stern", solid=False)
    crate_stack(4.75, f, 0.6, 2, ids=(FR + "potato_crate", FU + "spruce_crate"))
    block(FU + "dark_oak_crate", 3.75, f, 0.6, "port")
    block(FU + "spruce_crate", 4.75, f, 1.6, "port")
    block(FR + "rice_bag", 4.75, f, 2.75, "port")
    block(FR + "rice_bag", 4.75, f + 1.0, 2.75, "port", solid=False, scale=0.8)
    block(FR + "straw_bale", 4.2, f, 7.8, "port")
    block(LI + "spelt_bale_block", 3.2, f, 7.8, "port")
    block(FR + "straw_bale", 4.2, f + 1.0, 7.8, "port", solid=False, scale=0.9)
    custom("bale", solid=(3.0, 4.2, f, f + 0.85, 9.6, 10.6), name="hold_bale_3", p=(3.6, f, 10.1), w=1.2, h=0.85, d=1.0)
    custom("strongbox", solid=(2.95, 3.85, f, f + 0.55, 11.15, 11.75), name="hold_strongbox", p=(3.4, f, 11.45), yaw=math.pi)
    block(FU + "amphora", 3.1, f, 12.6, "stern")
    block(FU + "blue_amphora", 2.25, f, 13.4, "stern")
    block(FU + "yellow_amphora", 3.2, f, 13.55, "stern", scale=0.8)
    for z in (1.5, 6.0, 11.5):
        lantern(0.0, HOLD_CEIL, z)


def deck():
    """Pont principal, gaillards: the deck cargo of the references (044, 071): crates two high under white canvas
    lashed down, white bales of cloth, barrels, sacks, coils of rope at the masts; the benches against the bulwarks
    forward of the main mast and on the quarterdeck under the awning; clear of the stairs, the hatches, the capstan,
    the gangplank's stairs and lever (starboard, z 1.2..5.3) and of the boarding strip within 1.9 of the centre line."""
    for side in (1, -1):
        x = side * 4.45
        block(FU + "spruce_bench", x, M, -0.2, "bow", solid=False)
        seat(x, M + 0.562, -0.2, x - side * 0.9, M, -0.2)
    # port, aft of the main mast: four crates, two more on the outboard pair under a white canvas, a sack, two barrels
    for z in (-5.3, -4.3):
        crate_stack(4.35, M, z, 2)
        block(FU + "dark_oak_crate" if z < -5 else FU + "spruce_crate", 3.35, M, z, "port")
    custom("tarp_stack", name="deck_tarp_0", p=(4.35, M + 1.0, -4.8), yaw=math.pi / 2, w=2.0, d=1.0, h=1.0)
    block(FR + "rice_bag", 3.35, M + 1.0, -5.3, "port", solid=False, scale=0.75)
    custom("barrel", solid=(2.6, 3.3, M, M + 0.9, -3.45, -2.75), name="deck_barrel_0", p=(2.95, M, -3.1))
    custom("barrel", solid=(3.45, 4.15, M, M + 0.9, -3.05, -2.35), name="deck_barrel_1", p=(3.8, M, -2.7))
    # starboard, aft of the main mast (outboard of the crew companionway): crates, a white bale, a coil of rope
    crate_stack(-4.4, M, -5.3, 2)
    block(FU + "spruce_crate", -4.4, M, -4.3, "starboard")
    block(FU + "dark_oak_crate", -3.4, M, -5.3, "starboard")
    custom("bale", solid=(-3.85, -2.95, M, M + 0.8, -4.55, -3.75), name="deck_bale_s", p=(-3.4, M, -4.15), w=0.9, h=0.8, d=0.8)
    custom("coil", name="deck_coil_0", p=(-3.3, M, -2.6), r=0.32)
    # port, forward of the main mast: the white bales of 044, a barrel
    custom("bale", solid=(3.8, 4.9, M, M + 0.85, 0.45, 1.45), name="deck_bale_0", p=(4.35, M, 0.95), w=1.1, h=0.85, d=1.0)
    custom("bale", solid=(3.8, 4.9, M, M + 0.85, 1.55, 2.55), name="deck_bale_1", p=(4.35, M, 2.05), w=1.1, h=0.85, d=1.0)
    custom("bale", solid=(3.9, 4.8, M + 0.85, M + 1.55, 1.1, 1.9), name="deck_bale_2", p=(4.35, M + 0.85, 1.5), yaw=0.2, w=0.9, h=0.7, d=0.8)
    custom("barrel", solid=(2.75, 3.45, M, M + 0.9, 0.85, 1.55), name="deck_barrel_2", p=(3.1, M, 1.2))
    custom("coil", name="deck_coil_1", p=(1.15, M, -2.1), r=0.3)
    # starboard, forward of the gangplank: crates two high under canvas, a barrel and a sack
    for z in (6.4, 7.4):
        crate_stack(-4.2, M, z, 2, facing="starboard")
    block(FU + "spruce_crate", -3.2, M, 6.4, "starboard")
    custom("tarp_stack", name="deck_tarp_1", p=(-4.2, M + 1.0, 6.9), yaw=math.pi / 2, w=2.0, d=1.0, h=1.0)
    block(LI + "cypress_barrel", -3.2, M, 7.5, "starboard")
    block(FR + "rice_bag", -3.2, M + 1.0, 6.4, "starboard", solid=False, scale=0.75)
    # port, forward: barrels lying, a crate, a coil; starboard forward: white bales and a sack
    block(LI + "cypress_barrel", 4.0, M, 9.2, "port")
    block(LI + "fir_barrel", 4.0, M, 10.2, "port")
    block(FU + "dark_oak_crate", 3.0, M, 9.7, "port")
    custom("coil", name="deck_coil_2", p=(1.2, M, 8.3), r=0.3)
    custom("bale", solid=(-4.35, -3.25, M, M + 0.85, 8.85, 9.85), name="deck_bale_3", p=(-3.8, M, 9.35), w=1.1, h=0.85, d=1.0)
    block(FR + "rice_bag", -3.9, M, 10.4, "starboard")
    # the forecastle: barrels, a crate and a white bale by the bulwarks
    block(LI + "cypress_barrel", 2.9, F, 15.0, "port")
    block(FU + "spruce_crate", -2.9, F, 15.0, "starboard")
    custom("bale", solid=(-3.25, -2.45, F + 1.0, F + 1.6, 14.65, 15.35), name="deck_bale_fc", p=(-2.85, F + 1.0, 15.0), w=0.8, h=0.6, d=0.7)
    custom("coil", name="deck_coil_fc", p=(1.6, F, 16.2), r=0.3)
    # the quarterdeck: benches against the balustrade under the awning
    for side in (1, -1):
        x = side * 3.85
        for z in (-13.6, -12.6):
            block(FU + "dark_oak_bench", x, Q, z, "port", solid=False)
        seat(x, Q + 0.562, -13.1, x - side * 0.95, Q, -13.1)


def build():
    BLOCKS.clear()
    SEATS.clear()
    CUSTOM.clear()
    PAINTINGS.clear()
    captain_cabin()
    stateroom()
    crew_quarters()
    hold()
    deck()
    return BLOCKS, SEATS


def _cells(g, box, min_overlap=0.2):
    """The grid cells under a solid box: the cells it overlaps by min_overlap or more on each axis (by
    its whole height if it is thinner, a rack)."""
    x0, x1, y0, y1, z0, z1 = box
    h = fi.CELL / 2
    ox = np.minimum(g.X + h, x1) - np.maximum(g.X - h, x0)
    oy = np.minimum(g.Y + h, y1) - np.maximum(g.Y - h, y0 + 0.01)
    oz = np.minimum(g.Z + h, z1) - np.maximum(g.Z - h, z0)
    return (ox >= min_overlap - 1e-6) & (oz >= min_overlap - 1e-6) & (oy >= min(min_overlap, y1 - y0 - 0.01) - 1e-6)


def _boxes():
    """(name, box) of every piece of furniture: the solid custom pieces and every mod block (solid or not)."""
    boxes = [(kwargs.get("name", builder), solid, True) for builder, kwargs, solid in CUSTOM if solid is not None]
    for i, b in enumerate(BLOCKS):
        x0, x1, y0, y1, z0, z1 = footprint(b["block"], b["x"], b["y"], b["z"], b["yaw"], b["scale"])
        boxes.append(("%s #%d" % (b["block"], i), (x0, x1, b["y"], max(y1, b["y"] + 0.05), z0, z1), b["solid"]))
    return boxes


def apply_to_grid(g):
    """FURNITURE cells under the solid furniture (on the floor of a room, or on a deck). Every solid piece must be solid
    somewhere (a piece standing over cell boundaries keeps the cells it covers); no piece may stand in the walls, the
    decks or the hull (more than 0.3 into a solid cell), nor on the stairs."""
    free = (g.k == fi.DRY) | (g.k == fi.OUT)
    solid_hull = g.k == fi.SOLID
    poking = [name for name, box, _ in _boxes() if (_cells(g, box, 0.3) & solid_hull).any()]
    assert not poking, "furniture in the walls or the hull: %s" % poking
    boxes = [(name, box) for name, box, solid in _boxes() if solid]
    for name, box in boxes:
        g.k[_cells(g, box) & free] = fi.FURNITURE
    hollow = [name for name, box in boxes if not (_cells(g, box) & (g.k == fi.FURNITURE)).any()]
    assert not hollow, "solid furniture with no FURNITURE cell: %s" % hollow


def write(path):
    data = {"blocks": [], "seats": [{k: round(v, 4) for k, v in s.items()} for s in SEATS],
            "paintings": [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in q.items()} for q in PAINTINGS], "switches": []}
    for i, b in enumerate(BLOCKS):
        data["blocks"].append({"block": b["block"], "x": round(b["x"], 4), "y": round(b["y"], 4), "z": round(b["z"], 4),
                               "yaw": b["yaw"], "scale": b["scale"], "fallback": "fallback_%d" % i})
        if b["glow"]:
            data["blocks"][-1]["glow"] = True
    with open(path, "w") as f:
        json.dump(data, f, indent=1)


DECOR_PATH = "src/main/resources/assets/medievalships/interiors/royal_lion_ship_decor.json"
