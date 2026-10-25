"""Furniture of the Old Corsair: blocks of the decoration mods (drawn by the ship where they stand,
moving with it; never placed in the world), furniture modelled for the ship (tools/generate_corsair.py
draws it, builders in tools/corsair_furniture.py), and the seats.

  src/main/resources/assets/medievalships/interiors/old_corsair_decor.json

Same format as tools/nautilus_decor.py (read by fr.medievalships.core.InteriorDecor). A block whose
mod is missing on a client is replaced by its stand-in, a box of the same size in the model (bone
"fallback_<i>"). The solid furniture is added to the interior grid (FURNITURE cells): the players
walk round the tables, the stoves and the cargo.

Phase 2: every room furnished after the interior views of the reference sheet (docs/CORSAIR_PLAN.md
lists the mods' furniture room by room): the mods' blocks first (Farmhouse Decorations, Furnish,
Farmer's Delight, Lands of Icaria), modelled pieces only for what they lack (the captain's bed with its
red blanket, sea chests, the stone hearth, upright barrels, framed sea charts, pillars, hammocks,
rope coils, the telescope...). Kept clear (checked by CorsairTest): the doors, the stairs, the walking
areas of the rooms, the seats' stand-up spots. apply_to_grid checks that every solid piece is solid in
the grid (at least one FURNITURE cell). The lanterns are drawn full-bright while the lamps are lit
("glow" in the json).
"""
import json
import math

import numpy as np

import corsair_interior as ci
import corsair_shape as cs

# front faces: yaw of the block about the vertical (its model's north is its front)
FACING = {"stern": 0.0, "starboard": 90.0, "bow": 180.0, "port": 270.0}

FD = "farmhouse_decorations:"
FU = "furnish:"
FR = "farmersdelight:"
LI = "landsoficaria:"

# model bounds of the default state (block space, x east, z south, the front is north; element and
# blockstate rotations applied), from the mods' files (/tmp mods catalog, "bounds")
BOUNDS = {
    FD + "chained_kerosene_lantern": (0.37, 0.63, 0.328, 1, 0.375, 0.625),
    FD + "kerosene_lantern": (0.37, 0.63, 0, 0.484, 0.375, 0.625),
    FD + "wine_bottle": (0.391, 0.547, 0, 0.328, 0.422, 0.578),
    FD + "red_wine_bottle": (0.391, 0.547, 0, 0.328, 0.422, 0.578),
    FD + "wine_glass": (0.438, 0.562, 0, 0.25, 0.438, 0.562),
    FD + "pile_of_books": (0.283, 0.643, 0.002, 0.234, 0.403, 0.732),
    FD + "cigar_box": (0.25, 0.75, 0, 0.547, 0.312, 0.734),
    FD + "night_stand": (0.188, 0.812, 0, 0.625, 0.5, 1),
    FD + "tall_bookshelf": (0, 1, 0, 1.969, 0.188, 1),
    FD + "desk": (-0.953, 1.984, 0, 1.016, -0.031, 1.031),
    FD + "dining_table_side": (0, 1, -0.016, 1, 0.016, 0.984),
    FD + "dining_table_middle": (0, 1, 0.797, 1, 0.016, 0.984),
    FD + "dining_chair": (0.125, 0.875, 0, 1.563, 0, 0.973),
    FD + "liquor_cabinet": (-1, 1, 0, 1, 0.297, 1),
    FD + "kitchen_counter": (0, 1, 0, 1, 0.078, 1),
    FD + "kitchen_drawers": (0, 1, 0, 1, 0.078, 1),
    FD + "kitchen_wall_shelf": (0, 1, 0, 1, 0.375, 1),
    FD + "kitchen_wall_cabinet": (0, 1, 0, 1, 0.375, 1),
    FD + "seasoning_rack": (0.125, 0.875, 0, 0.781, 0.688, 1),
    FD + "tool_board": (-0.844, 0.844, 0.219, 0.844, 0.9, 1),
    FD + "workbench": (-0.875, 0.875, 0, 1.25, 0.078, 1),
    FD + "acoustic_guitar": (0.25, 0.75, 0.013, 1.185, 0.431, 0.999),
    FD + "coat_hanger": (0.078, 0.922, -0.048, 1.953, 0.078, 0.922),
    FD + "rug_1x_3": (-0.875, 1.875, 0, 0.031, 0, 1),
    FU + "spruce_bench": (0, 1, 0, 0.562, 0.25, 0.75),
    FU + "dark_oak_bench": (0, 1, 0, 0.562, 0.25, 0.75),
    FU + "dark_oak_chair": (0.062, 0.938, 0, 1.875, 0, 0.812),
    FU + "spruce_stool": (0.188, 0.812, 0, 0.562, 0.125, 0.75),
    FU + "dark_oak_stool": (0.188, 0.812, 0, 0.562, 0.125, 0.75),
    FU + "spruce_crate": (0, 1, 0, 1, 0, 1),
    FU + "dark_oak_crate": (0, 1, 0, 1, 0, 1),
    FU + "spruce_shelf": (0, 1, 0, 0.25, 0.688, 1),
    FU + "book_pile": (0.167, 0.88, 0.013, 0.394, 0.182, 0.865),
    FU + "plate": (0.062, 0.938, 0, 0.062, 0.062, 0.938),
    FU + "spruce_square_table": (0, 1, 0, 1, 0, 1),
    FU + "amphora": (0, 1, 0, 1, 0.125, 0.875),
    FU + "chess_board": (0.125, 0.875, 0, 0.062, 0.125, 0.875),
    FR + "stove": (0, 1, 0, 1, 0, 1),
    FR + "cooking_pot": (0, 1, 0, 0.904, 0.125, 0.875),
    FR + "skillet": (0.062, 0.938, 0, 0.25, 0.062, 1.688),
    FR + "cutting_board": (0.062, 0.938, 0, 0.062, 0.062, 0.938),
    FR + "potato_crate": (0, 1, 0, 1, 0, 1),
    FR + "onion_crate": (0, 1, 0, 1, 0, 1),
    FR + "cabbage_crate": (0, 1, 0, 1, 0, 1),
    FR + "carrot_crate": (0, 1, 0, 1, 0, 1),
    FR + "rice_bag": (0, 1, 0, 1, 0, 1),
    FR + "wooden_basket": (0, 1, 0, 1, 0, 1),
    FR + "roast_chicken_block": (0.062, 0.938, 0, 0.5, 0.062, 0.938),
    FR + "canvas_rug": (-0.5, 1.5, 0, 0.062, -0.5, 1.5),
    FR + "spruce_cabinet": (0, 1, 0, 1, 0, 1),
    LI + "cypress_barrel": (0.047, 0.953, 0, 0.906, 0, 1),
    LI + "fir_barrel": (0.047, 0.953, 0, 0.906, 0, 1),
    LI + "loaded_fir_barrel": (0.047, 0.953, 0, 0.906, 0, 1),
    LI + "loaded_cypress_barrel": (0.047, 0.953, 0, 0.906, 0, 1),
    LI + "tapped_cypress_barrel": (0.047, 0.953, 0, 0.906, -0.246, 1),
    LI + "cypress_rack": (0, 1, 0, 0.25, 0, 1),
    LI + "storage_vase": (0.062, 0.938, 0, 1, 0.062, 0.938),
    LI + "brown_storage_vase": (0.062, 0.938, 0, 1, 0.062, 0.938),
}

# stand-in look when the mod is missing (default: a box of mid brown wood)
FALLBACK_REGION = {FR + "stove": "wall_stone", FR + "cooking_pot": "iron", FR + "skillet": "iron", FD + "chained_kerosene_lantern": "lantern",
                   FD + "kerosene_lantern": "lantern", FD + "wine_bottle": "glass", FD + "red_wine_bottle": "glass", FD + "wine_glass": "glass",
                   FD + "pile_of_books": "books", FU + "book_pile": "books", FU + "plate": "stripe", FR + "rice_bag": "sack",
                   FD + "rug_1x_3": "rug", FR + "canvas_rug": "sack", FD + "tall_bookshelf": "books", FD + "wall_shelf": "books",
                   FU + "spruce_crate": "wood_light", FU + "dark_oak_crate": "wood_dark", FU + "dark_oak_bench": "wood_dark", FU + "dark_oak_stool": "wood_dark", FD + "desk": "wood_dark", FD + "liquor_cabinet": "wood_dark",
                   LI + "storage_vase": "red_paint", LI + "brown_storage_vase": "wood_mid", FU + "amphora": "red_paint",
                   FR + "roast_chicken_block": "wood_light", FD + "cigar_box": "red_paint"}

GLOWING = {FD + "kerosene_lantern", FD + "chained_kerosene_lantern"}   # drawn full-bright while the lamps are lit

BLOCKS = []   # dicts: block, x, y, z, yaw, solid, scale
SEATS = []    # dicts: x, y, z, dx, dy, dz
CUSTOM = []   # furniture drawn by generate_corsair: (builder name, kwargs, solid box or None)

M, L, H, C, Q = cs.MAIN_DECK_Y, cs.LOWER_FLOOR_Y, cs.HOLD_FLOOR_Y, cs.CABIN_FLOOR_Y, cs.QUARTERDECK_Y
LOWER_CEIL, HOLD_CEIL, CABIN_CEIL = M - cs.SLAB, L - cs.SLAB, Q - cs.SLAB


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


def lantern(x, ceiling, z):
    """A kerosene lantern hanging on its chain from the beams (the chain reaches the ceiling)."""
    block(FD + "chained_kerosene_lantern", x, ceiling - 1.0, z, "stern", solid=False)


def wall_lantern(x, y, z, side):
    """A kerosene lantern on an iron bracket against a wall (side: +1 port wall, -1 starboard wall)."""
    custom("bracket", name="bracket_%d" % len(CUSTOM), p=(x + side * 0.12, y, z), side=side)
    block(FD + "kerosene_lantern", x, y, z, "stern", solid=False)


def barrel(name, x, y, z, h=0.95, r=0.36):
    """Upright iron-hooped barrel (the reference's barrels stand on their ends; the mods' lie down)."""
    custom("barrel", solid=(x - r, x + r, y, y + h, z - r, z + r), name=name, p=(x, y, z), h=h, r=r)


# ---------------------------------------------------------------- the rooms
def captain_cabin():
    """Cabine du capitaine (reference panel 3): the bed with its red blanket against the port side, a sea
    chest at its foot, the desk with charts, lantern, books and bottles against the starboard side and the
    captain's high chair, a red rug, the bookcase, the coat rack and the liquor cabinet by the door, a framed
    sea chart, the telescope aimed at the stern windows, lanterns."""
    custom("captain_bed", solid=(2.2, 3.5, C, C + 0.75, -20.3, -18.3), name="captain_bed", p=(2.85, C, -19.3), l=2.0, w=1.3)
    custom("chest", solid=(2.35, 3.35, C, C + 0.65, -18.05, -17.45), name="captain_chest", p=(2.85, C, -17.75))
    block(FD + "night_stand", 1.55, C, -20.2, "bow", centre=True)
    block(FD + "kerosene_lantern", 1.55, C + 0.625, -20.15, "bow", solid=False)
    # the desk along the starboard side, the captain's chair before it
    block(FD + "desk", -2.95, C, -19.0, "port", centre=True)
    custom("chart_sheet", name="captain_chart", p=(-2.85, C + 1.02, -19.2), yaw=0.25)
    block(FD + "kerosene_lantern", -3.15, C + 1.02, -20.15, "port", solid=False)
    block(FD + "pile_of_books", -3.15, C + 1.02, -17.95, "port", solid=False)
    block(FD + "red_wine_bottle", -2.7, C + 1.02, -18.1, "port", solid=False)
    block(FD + "wine_glass", -2.55, C + 1.02, -18.35, "port", solid=False)
    block(FD + "cigar_box", -3.2, C + 1.02, -19.9, "port", solid=False, scale=0.8)
    custom("compass_box", name="captain_compass", p=(-2.6, C + 1.02, -19.95))
    block(FD + "dining_chair", -1.75, C, -19.0, "starboard", solid=False, centre=True)
    seat(-1.8, C + 0.52, -19.0, -1.0, C, -19.0)
    custom("wall_chart", name="captain_wall_chart", center=(-3.47, C + 1.85, -19.0), normal=(1, 0, 0), w=1.3, h=0.85)
    # by the door: the bookcase and the coat rack (port), the liquor cabinet (starboard), a second chart
    block(FD + "tall_bookshelf", 2.5, C, -14.95, "stern", centre=True)
    block(FD + "coat_hanger", 3.5, C, -15.0, "stern", centre=True)
    block(FD + "liquor_cabinet", -3.0, C, -14.85, "stern", centre=True)
    block(FD + "kerosene_lantern", -3.6, C + 1.0, -14.85, "stern", solid=False)
    block(FD + "wine_bottle", -2.35, C + 1.0, -14.8, "stern", solid=False)
    custom("wall_chart", name="captain_bulkhead_chart", center=(-2.6, C + 1.75, -14.53), normal=(0, 0, -1), w=1.1, h=0.75)
    custom("chest", solid=(-3.9, -2.9, C, C + 0.65, -16.6, -16.0), name="captain_treasure", p=(-3.4, C, -16.3))
    # a shelf of books over the bed, the rug, the telescope
    block(FU + "spruce_shelf", 3.3, C + 1.45, -18.9, "starboard", solid=False, centre=True)
    block(FU + "book_pile", 3.3, C + 1.7, -19.15, "starboard", solid=False, scale=0.7)
    block(FD + "wine_bottle", 3.3, C + 1.7, -18.55, "starboard", solid=False)
    # shelves of books and bottles on the stern bulkhead, by the bed and over it, a lantern at its foot
    sz = -20.345
    for x, y in ((1.25, C + 1.3), (1.25, C + 1.8), (2.85, C + 1.6)):
        block(FU + "spruce_shelf", x, y, sz, "bow", solid=False, centre=True)
    block(FU + "book_pile", 1.0, C + 1.55, sz, "bow", solid=False, scale=0.7)
    block(FD + "red_wine_bottle", 1.5, C + 1.55, sz, "bow", solid=False)
    block(FD + "pile_of_books", 1.1, C + 2.05, sz, "bow", solid=False, scale=0.8)
    block(FD + "wine_bottle", 1.55, C + 2.05, sz, "bow", solid=False)
    block(FD + "pile_of_books", 2.55, C + 1.85, sz, "bow", solid=False, scale=0.8)
    block(FD + "kerosene_lantern", 3.15, C + 1.85, sz, "bow", solid=False)
    wall_lantern(3.18, C + 1.3, -17.3, 1)
    custom("rug", name="captain_rug", p=(-0.05, C, -17.7), w=2.6, l=3.4, region="rug")
    custom("telescope", name="captain_telescope", p=(-1.1, C, -20.0), facing="stern")
    lantern(0.0, CABIN_CEIL, -17.6)


def common_room():
    """Salle commune (panel 2): the long dark table on the starboard half with a bench on each side and
    two chairs at its head, a red rug under it, the feast on it (roast, plates, bottles, glasses, tankards,
    a lantern), shelves of bottles and a framed chart on the hull, the liquor cabinet and the rum barrels
    beyond the companionway, a sea chest, lanterns hanging from the beams."""
    rows = (-3.0, -2.0)
    zs = [0.25 + k for k in range(6)]
    for x in rows:
        for k, z in enumerate(zs):
            if k == 0:
                block(FD + "dining_table_side", x, L, z, "stern")
            elif k == len(zs) - 1:
                block(FD + "dining_table_side", x, L, z, "bow")
            else:
                block(FD + "dining_table_middle", x, L, z, "starboard")
    for bx, dx in ((-4.05, -4.05), (-0.95, -0.3)):
        for z in zs:
            block(FU + "dark_oak_bench", bx, L, z, "starboard", solid=False)
            seat(bx, L + 0.46, z, dx, L, z)
    for x in rows:
        block(FD + "dining_chair", x, L, 6.3, "stern", solid=False, centre=True)
        seat(x, L + 0.52, 6.3, x, L, 7.3)
    custom("rug", name="common_rug", p=(-2.5, L, 2.7), w=3.5, l=7.6, region="rug")
    top = L + 1.0
    block(FR + "roast_chicken_block", -2.5, top, 2.75, "stern", solid=False, scale=0.8)
    for k, z in enumerate(zs):
        for x, f in ((-3.25, "port"), (-1.75, "starboard")):
            if (k + (x > -2.5)) % 2 == 0 or k in (0, 5):
                block(FU + "plate", x, top, z, f, solid=False, scale=0.42)
    for k, (x, z, b) in enumerate(((-2.6, 0.6, "wine_bottle"), (-2.35, 1.7, "red_wine_bottle"), (-2.7, 4.1, "wine_bottle"),
                                   (-2.4, 4.9, "red_wine_bottle"), (-3.45, 3.4, "wine_glass"), (-1.55, 1.25, "wine_glass"),
                                   (-1.6, 4.3, "wine_glass"))):
        block(FD + b, x, top, z, "stern", solid=False)
    block(FD + "kerosene_lantern", -2.5, top, 3.9, "stern", solid=False)
    custom("tankards", name="common_tankards", pts=((-3.4, top, 1.0), (-1.7, top, 2.3), (-3.3, top, 4.6), (-1.6, top, 5.4), (-2.2, top, 0.2)))
    # on the starboard hull over the outer bench: a framed sea chart and shelves of bottles
    custom("wall_chart", name="common_chart", center=(-4.47, L + 1.95, 1.7), normal=(1, 0, 0), w=1.4, h=0.95)
    for z in (4.0, 5.0):
        block(FU + "spruce_shelf", -4.3, L + 1.6, z, "port", solid=False, centre=True)
    for k, (z, b) in enumerate(((3.65, "wine_bottle"), (3.95, "red_wine_bottle"), (4.3, "wine_bottle"), (4.85, "wine_glass"),
                                (5.15, "red_wine_bottle"), (5.4, "wine_bottle"))):
        block(FD + b, -4.3, L + 1.85, z, "port", solid=False)
    block(FD + "kitchen_wall_shelf", -3.0, L + 1.55, -0.95, "bow", solid=False, centre=True)
    # beyond the companionway (port, forward): the liquor cabinet, mugs over it, the rum barrels
    block(FD + "liquor_cabinet", 4.15, L, 6.0, "starboard", centre=True)
    for z in (5.5, 6.5):
        block(FD + "kitchen_wall_shelf", 4.3, L + 1.5, z, "starboard", solid=False, centre=True)
    block(LI + "tapped_cypress_barrel", 3.95, L, 7.5, "starboard", centre=True)
    block(LI + "cypress_barrel", -3.95, L, 7.45, "port", centre=True)
    block(LI + "fir_barrel", -3.95, L + 0.9, 7.45, "port", centre=True)
    # a sea chest in the corner by the foot of the companionway
    custom("chest", solid=(3.7, 4.25, L, L + 0.65, -0.95, 0.05), name="common_chest", p=(3.97, L, -0.45), yaw=math.pi / 2)
    for x, z in ((-2.5, 0.9), (-2.5, 4.6), (2.6, 6.2), (1.2, 2.5)):
        lantern(x, LOWER_CEIL, z)


def kitchen():
    """Cuisine (panel 5): the stone hearth with its fire and its hood against the bow bulkhead, hams
    hanging; the stoves (pot, skillet) on the port side, barrels of water and provisions; the worktops,
    the cupboard, wall cabinets and the spice rack on the starboard side, sacks and crates of vegetables;
    a block work table in the middle with its stool, pans hanging over it."""
    custom("hearth", solid=(-1.6, 1.6, L, L + 2.6, 12.9, 14.0), name="kitchen_hearth", p=(0.0, L, 13.45), w=3.2)
    # port: the stoves, the barrels
    block(FR + "stove", 3.45, L, 12.6, "starboard")
    block(FR + "cooking_pot", 3.45, L + 1.0, 12.6, "starboard", solid=False)
    block(FR + "stove", 3.45, L, 11.6, "starboard")
    block(FR + "skillet", 3.45, L + 1.0, 11.6, "starboard", solid=False, centre=True, scale=0.9)
    block(FD + "seasoning_rack", 3.85, L + 1.45, 12.6, "starboard", solid=False, centre=True)
    for z in (10.0, 11.0):
        block(FD + "kitchen_wall_shelf", 3.75, L + 1.6, z, "starboard", solid=False, centre=True)
    barrel("kitchen_barrel_0", 3.45, L, 9.4)
    barrel("kitchen_barrel_1", 3.4, L, 10.35, h=0.85, r=0.34)
    block(FR + "rice_bag", 3.45, L + 0.95, 9.4, "starboard", solid=False, scale=0.6)
    # starboard: worktops and cupboard, wall cabinets and shelves over them, provisions in the corner
    for z, b in ((10.5, FR + "spruce_cabinet"), (11.5, FD + "kitchen_drawers"), (12.5, FD + "kitchen_counter"), (13.5, FD + "kitchen_counter")):
        block(b, -3.5, L, z, "port", centre=True)
    block(FR + "cutting_board", -3.45, L + 1.0, 12.5, "port", solid=False, scale=0.8)
    block(FR + "wooden_basket", -3.5, L + 1.0, 13.5, "port", solid=False, scale=0.5)
    block(FR + "cabbage_crate", -3.5, L + 1.0, 11.5, "port", solid=False, scale=0.45)
    block(FD + "kitchen_wall_cabinet", -3.7, L + 1.75, 12.5, "port", solid=False, centre=True)
    block(FD + "kitchen_wall_shelf", -3.7, L + 1.75, 11.5, "port", solid=False, centre=True)
    block(FD + "kitchen_wall_shelf", -3.7, L + 1.75, 10.5, "port", solid=False, centre=True)
    block(FR + "potato_crate", -3.5, L, 9.35, "port")
    block(FR + "rice_bag", -3.5, L + 1.0, 9.35, "port", solid=False, scale=0.8)
    # the block work table in the middle, its stool, pans hanging over it
    # (on the starboard side of the axis: the fire stays in view from the door)
    tx = -1.2
    custom("work_table", solid=(tx - 0.6, tx + 0.6, L, L + 0.9, 10.9, 12.3), name="kitchen_table", p=(tx, L, 11.6), w=1.2, l=1.4)
    block(FR + "cutting_board", tx, L + 0.9, 11.3, "port", solid=False, scale=0.7)
    block(FR + "onion_crate", tx - 0.25, L + 0.9, 12.0, "port", solid=False, scale=0.35)
    block(FU + "dark_oak_stool", tx, L, 10.35, "bow", solid=False, centre=True)
    seat(tx, L + 0.46, 10.35, tx, L, 9.6)
    custom("pot_rack", name="kitchen_pot_rack", p=(tx, LOWER_CEIL, 11.6), l=1.4)
    lantern(1.9, LOWER_CEIL, 9.9)
    lantern(-2.2, LOWER_CEIL, 10.0)


def hold():
    """Cale / stockage (panel 4): pillars on stone footings between the bays, cargo along the sides
    (barrels lying on their cradles, upright barrels, stacked crates, sacks, vegetables), the carpenter's
    workbench and tool board, chests, rope coils, jars on shelves, lanterns hanging from the beams; the
    aisle along the centre line stays clear from the stair to the fore mast."""
    for side in (1, -1):
        for z in (-10.5, -5.5, -0.5, 5.2, 10.2):
            x = side * 2.75
            custom("pillar", solid=(x - 0.2, x + 0.2, H, HOLD_CEIL, z - 0.2, z + 0.2), name="hold_pillar_%d_%d" % (side > 0, int(z + 20)),
                   p=(x, H, z), top=HOLD_CEIL)
    f_in = {1: "starboard", -1: "port"}
    # aft bays (beside the aisle: one block deep, x 2.5 .. 3.5)
    for side in (1, -1):
        x = side * 3.0
        f = f_in[side]
        if side > 0:
            for k, z in enumerate((-9.3, -8.0, -6.7)):
                block(LI + "cypress_rack", x, H, z, f)
                block(LI + ("loaded_fir_barrel" if k % 2 else "loaded_cypress_barrel"), x, H + 0.25, z, f)
            for z in (-8.65, -7.35):
                block(LI + "fir_barrel", x + 0.15, H + 1.15, z, f, solid=False, scale=0.9)
            block(FU + "spruce_crate", x, H, -4.4, f)
            block(FU + "dark_oak_crate", x, H, -3.3, f)
            block(FU + "spruce_crate", x + 0.1, H + 1.0, -3.9, f, solid=False, scale=0.9)
            block(FR + "rice_bag", x, H, -2.0, f)
            block(FR + "rice_bag", x, H + 0.95, -2.0, f, solid=False, scale=0.75)
            barrel("hold_barrel_p0", x, H, 0.4)
        else:
            barrel("hold_barrel_s0", x, H, -9.6)
            barrel("hold_barrel_s1", x, H, -8.75)
            barrel("hold_barrel_s2", x, H, -7.9)
            barrel("hold_barrel_s3", x, H, -7.0, h=0.8, r=0.33)
            block(FR + "potato_crate", x, H, -4.4, f)
            block(FR + "carrot_crate", x, H, -3.3, f)
            block(FU + "spruce_crate", x - 0.1, H + 1.0, -3.85, f, solid=False, scale=0.9)
            custom("chest", solid=(x - 0.3, x + 0.3, H, H + 0.65, -2.4, -1.4), name="hold_chest_s", p=(x, H, -1.9), yaw=math.pi / 2)
            block(LI + "storage_vase", x, H, 0.6, f, scale=0.85)
    # forward hold: two blocks deep on each side (x 1.5 .. 3.5), the aisle round the fore mast
    for side in (1, -1):
        f = f_in[side]
        if side > 0:
            for k, (x, z) in enumerate(((2.0, 2.6), (3.0, 2.6), (3.0, 3.6), (2.0, 3.6))):
                block(FU + ("spruce_crate" if k % 2 else "dark_oak_crate"), x, H, z, f)
            block(FU + "spruce_crate", 3.0, H + 1.0, 3.1, f, solid=False)
            block(FU + "dark_oak_crate", 2.05, H + 1.0, 2.9, f, solid=False, scale=0.8)
            for (x, z, b) in ((3.0, 7.6, "potato_crate"), (2.0, 7.6, "onion_crate"), (3.0, 8.6, "cabbage_crate")):
                block(FR + b, x, H, z, f)
            block(FR + "rice_bag", 2.0, H, 8.6, f)
            block(FR + "rice_bag", 3.0, H + 1.0, 8.1, f, solid=False, scale=0.8)
            block(LI + "storage_vase", 2.0, H, 10.7, f, scale=0.85)
            block(LI + "brown_storage_vase", 2.0, H, 11.6, f, scale=0.8)
            block(FU + "amphora", 1.9, H, 12.4, f, scale=0.7)
        else:
            for k, (x, z) in enumerate(((-3.05, 2.45), (-2.25, 2.45), (-3.05, 3.25), (-2.25, 3.25), (-3.05, 4.05), (-2.25, 4.05))):
                barrel("hold_barrel_f%d" % k, x, H, z, r=0.37)
            block(FD + "workbench", -3.0, H, 8.3, "port", centre=True)
            block(FD + "tool_board", -3.92, H + 1.25, 8.3, "port", solid=False, centre=True)
            custom("chest", solid=(-2.5, -1.5, H, H + 0.65, 10.75, 11.35), name="hold_chest_f", p=(-2.0, H, 11.05))
            custom("coil", name="hold_coil_0", p=(-1.9, H, 12.1), r=0.36)
    # forward of the fore mast, on the centre line: crates and sacks stowed together
    block(FU + "spruce_crate", 0.0, H, 11.9, "stern")
    block(FU + "dark_oak_crate", 0.05, H + 1.0, 11.9, "bow", solid=False, scale=0.85)
    block(FR + "rice_bag", 0.0, H, 10.9, "stern")
    block(FR + "rice_bag", -0.7, H, 10.6, "stern", solid=False, scale=0.7)
    # the stern end, by the foot of the stair
    for side in (1, -1):
        custom("chest", solid=(side * 2.55 - 0.3, side * 2.55 + 0.3, H, H + 0.65, -13.5, -12.5), name="hold_chest_a%d" % (side > 0),
               p=(side * 2.55, H, -13.0), yaw=math.pi / 2)
    custom("coil", name="hold_coil_1", p=(2.3, H + 0.65, -13.0), r=0.3)
    # shelves of jars on the hull over the barrel cradles
    for z in (-9.0, -8.0, -7.0):
        block(FU + "spruce_shelf", 3.85, H + 1.95, z, "starboard", solid=False, centre=True)
    for k, z in enumerate((-9.3, -8.6, -7.8, -7.1, -6.6)):
        block(LI + ("storage_vase" if k % 2 else "brown_storage_vase"), 3.85, H + 2.2, z, "starboard", solid=False, scale=0.3)
    for z in (-10.0, -4.5, 1.0, 9.0):
        lantern(0.0 if abs(z - cs.FORE_MAST_Z) > 1.5 else 1.2, HOLD_CEIL, z)
    lantern(-1.3, HOLD_CEIL, 4.5)


def coursive_and_crew():
    """Coursive (panel 6): red runners along the centre line, lanterns on brackets on both walls,
    posts under the beams; the crew quarters behind their doors: double bunks with sea chests, a hammock,
    a small table with its stool and a lantern, a guitar, rugs, barrels."""
    for k, (z0, z1) in enumerate(((-12.7, -9.8), (-9.0, -5.2), (-4.4, -1.8))):
        custom("rug", name="coursive_runner_%d" % k, p=(0.0, L, (z0 + z1) / 2), w=1.05, l=z1 - z0, region="carpet")
    for k, (z, side) in enumerate(((-12.2, 1), (-10.0, -1), (-4.5, 1), (-2.3, -1))):
        wall_lantern(side * 0.8, L + 2.0, z, side)
    lantern(0.0, LOWER_CEIL, -7.0)
    for side in (1, -1):
        for z in (-13.0, -11.0, -9.0, -5.0, -3.0):
            custom("post", name="coursive_post_%d_%d" % (side > 0, int(z + 20)), p=(side * 0.94, L, z), top=LOWER_CEIL, side=side)
    for side in (1, -1):
        sn = "p" if side > 0 else "s"
        x = side * 3.6
        f_in = "starboard" if side > 0 else "port"
        for k, z in enumerate((-12.0, -9.6)):
            custom("bunk2", solid=(x - 0.5, x + 0.5, L, L + 2.4, z - 0.95, z + 0.95), name="crew_bunk_%s%d" % (sn, k), p=(x, L, z),
                   l=1.9, w=1.0)
        custom("chest", solid=(x - 0.5, x + 0.5, L, L + 0.65, -8.58, -8.02), name="crew_chest_" + sn, p=(x, L, -8.3))
        custom("hammock", name="crew_hammock_" + sn, a=(side * 3.75, L + 2.3, -6.1), b=(side * 3.75, L + 2.3, -3.0), sag=0.6)
        block(FU + "spruce_square_table", side * 3.75, L, -2.2, f_in)
        block(FD + "kerosene_lantern", side * 3.85, L + 1.0, -2.0, f_in, solid=False)
        block(FD + ("wine_bottle" if side > 0 else "red_wine_bottle"), side * 3.55, L + 1.0, -2.45, f_in, solid=False)
        block(FU + "dark_oak_stool", side * 2.85, L, -2.2, "port" if side > 0 else "starboard", solid=False, centre=True)
        seat(side * 2.85, L + 0.46, -2.2, side * 2.05, L, -2.2)
        block(FR + "canvas_rug", side * 2.4, L, -4.7, f_in, solid=False)
        lantern(side * 2.9, LOWER_CEIL, -9.6)
        if side > 0:
            block(FD + "acoustic_guitar", 4.0, L, -4.6, "starboard", solid=False, centre=True)
        else:
            barrel("crew_barrel_s", -3.95, L, -4.9, h=0.85, r=0.33)
            block(FR + "wooden_basket", -3.95, L, -4.0, "port", solid=False, scale=0.7)


def deck():
    """Pont principal (panel 1): barrels and crates against the bulwarks (bow, between the masts, abaft
    the main mast), rope coils, the benches between the masts; on the quarterdeck the telescope beside
    the binnacle. The walking areas, the stairs, the hatches and the centre line stay clear."""
    for side in (1, -1):
        x = side * 3.75
        custom("bench", name="deck_bench_%d" % (side > 0), x=x, z0=-2.4, z1=-0.4, y=M)
        for z in (-1.9, -0.9):
            seat(x, M + 0.47, z, x - side * 0.8, M, z)
    custom("boat", solid=(-0.8, 0.8, Q, Q + 0.9, -20.4, -17.2), name="boat", c=(0, Q + 0.3, -18.8))
    # the bow
    barrel("deck_barrel_b0", 3.05, M, 13.0)
    barrel("deck_barrel_b1", 3.1, M, 12.25, h=0.85, r=0.33)
    block(FU + "spruce_crate", -3.0, M, 13.1, "starboard")
    block(FU + "dark_oak_crate", -3.0, M + 1.0, 13.1, "port", solid=False, scale=0.7)
    custom("coil", name="deck_coil_b", p=(-2.9, M, 14.6), r=0.34)
    # between the masts, before the companionway
    barrel("deck_barrel_m0", 3.45, M, 7.35)
    barrel("deck_barrel_m1", 3.45, M, 8.15)
    barrel("deck_barrel_m2", 2.7, M, 7.75, h=0.85, r=0.33)
    block(LI + "cypress_rack", -3.3, M, 7.6, "port")
    block(LI + "loaded_cypress_barrel", -3.3, M + 0.25, 7.6, "port")
    block(FU + "spruce_crate", -3.4, M, 8.65, "port")
    # abaft the main mast, before the quarterdeck stairs
    block(FU + "dark_oak_crate", 3.45, M, -10.0, "starboard")
    barrel("deck_barrel_a0", -3.45, M, -10.3)
    barrel("deck_barrel_a1", -3.45, M, -9.5, h=0.85, r=0.33)
    custom("coil", name="deck_coil_a", p=(2.6, M, -10.0), r=0.32)
    # the quarterdeck: the telescope by the starboard rail
    custom("telescope", name="deck_telescope", p=(-2.6, Q, -17.8), facing="starboard")


def build():
    BLOCKS.clear()
    SEATS.clear()
    CUSTOM.clear()
    captain_cabin()
    common_room()
    kitchen()
    hold()
    coursive_and_crew()
    deck()
    return BLOCKS, SEATS


def _cells(g, box, min_overlap=0.2):
    """The grid cells under a solid box: the cells it overlaps by min_overlap or more on each axis (by
    its whole height if it is thinner, a rack)."""
    x0, x1, y0, y1, z0, z1 = box
    h = ci.CELL / 2
    ox = np.minimum(g.X + h, x1) - np.maximum(g.X - h, x0)
    oy = np.minimum(g.Y + h, y1) - np.maximum(g.Y - h, y0 + 0.01)
    oz = np.minimum(g.Z + h, z1) - np.maximum(g.Z - h, z0)
    return (ox >= min_overlap - 1e-6) & (oz >= min_overlap - 1e-6) & (oy >= min(min_overlap, y1 - y0 - 0.01) - 1e-6)


def apply_to_grid(g):
    """FURNITURE cells under the solid furniture (on the floor of a room, or on a deck). Every solid
    piece must be solid somewhere (a piece standing over cell boundaries keeps the cells it covers)."""
    free = (g.k == ci.DRY) | (g.k == ci.OUT)
    boxes = [(kwargs.get("name", builder), solid) for builder, kwargs, solid in CUSTOM if solid is not None]
    for i, b in enumerate(BLOCKS):
        if b["solid"]:
            x0, x1, y0, y1, z0, z1 = footprint(b["block"], b["x"], b["y"], b["z"], b["yaw"], b["scale"])
            boxes.append(("%s #%d" % (b["block"], i), (x0, x1, b["y"], y1, z0, z1)))
    for name, box in boxes:
        g.k[_cells(g, box) & free] = ci.FURNITURE
    hollow = [name for name, box in boxes if not (_cells(g, box) & (g.k == ci.FURNITURE)).any()]
    assert not hollow, "solid furniture with no FURNITURE cell: %s" % hollow


def write(path):
    data = {"blocks": [], "seats": [{k: round(v, 4) for k, v in s.items()} for s in SEATS], "paintings": [], "switches": []}
    for i, b in enumerate(BLOCKS):
        data["blocks"].append({"block": b["block"], "x": round(b["x"], 4), "y": round(b["y"], 4), "z": round(b["z"], 4),
                               "yaw": b["yaw"], "scale": b["scale"], "fallback": "fallback_%d" % i})
        if b["glow"]:
            data["blocks"][-1]["glow"] = True
    with open(path, "w") as f:
        json.dump(data, f, indent=1)


DECOR_PATH = "src/main/resources/assets/medievalships/interiors/old_corsair_decor.json"
