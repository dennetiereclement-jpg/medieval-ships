"""Furniture of the Blue-Sailed Frigate: blocks of the decoration mods (drawn by the ship where they
stand, moving with it; never placed in the world), furniture modelled for the ship (drawn by
tools/generate_frigate.py with the builders of tools/corsair_furniture.py and generate_corsair.py), and
the seats.

  src/main/resources/assets/medievalships/interiors/blue_frigate_decor.json

Same format as tools/corsair_decor.py (read by fr.medievalships.core.InteriorDecor). A block whose mod
is missing on a client is replaced by its stand-in, a box of the same size in the model (bone
"fallback_<i>"). The solid furniture is added to the interior grid (FURNITURE cells): the players walk
round the desk, the bed, the guns and the cargo.

The mods' blocks first (catalog /tmp/claude-0/mods_catalog/catalog.json: Farmhouse Decorations,
Furnish, Farmer's Delight, Lands of Icaria), modelled pieces only for what they lack (the framed sea
charts, the chart and compass on the desk, the telescope, sea chests, rope coils, the guns on their
carriages). Kept clear (checked by FrigateTest): the cabin door, the stairs, the centre line of the hold,
the seats' stand-up spots.
"""
import json
import math

import numpy as np

import frigate_interior as fi
import frigate_shape as fs

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
    FU + "dark_oak_chair": (0.062, 0.938, 0, 1.875, 0, 0.812),
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
    FD + "rug_3x_3": (-0.625, 1.625, 0, 0.031, -0.625, 1.625),
    FD + "liquor_cabinet": (-1, 1, 0, 1, 0.297, 1),
    FD + "coat_hanger": (0.078, 0.922, -0.048, 1.953, 0.078, 0.922),
    FD + "workbench": (-0.875, 0.875, 0, 1.25, 0.078, 1),
    FD + "tool_board": (-0.844, 0.844, 0.219, 0.844, 0.9, 1),
    FU + "spruce_shelf": (0, 1, 0, 0.25, 0.688, 1),
    FU + "dark_oak_shelf": (0, 1, 0.002, 0.25, 0.688, 1.022),
    FU + "chess_board": (0.125, 0.875, 0, 0.062, 0.125, 0.875),
    FU + "book_pile": (0.167, 0.88, 0.013, 0.394, 0.182, 0.865),
    FU + "spruce_crate": (0, 1, 0, 1, 0, 1),
    FU + "dark_oak_crate": (0, 1, 0, 1, 0, 1),
    FU + "spruce_stool": (0.188, 0.812, 0, 0.562, 0.125, 0.75),
    FU + "dark_oak_stool": (0.188, 0.812, 0, 0.562, 0.125, 0.75),
    FU + "spruce_bench": (0, 1, 0, 0.562, 0.25, 0.75),
    FU + "dark_oak_bench": (0, 1, 0, 0.562, 0.25, 0.75),
    FU + "dark_oak_square_table": (0, 1, 0, 1, 0, 1),
    FU + "amphora": (0, 1, 0, 1, 0.125, 0.875),
    FR + "potato_crate": (0, 1, 0, 1, 0, 1),
    FR + "carrot_crate": (0, 1, 0, 1, 0, 1),
    FR + "cabbage_crate": (0, 1, 0, 1, 0, 1),
    FR + "rice_bag": (0, 1, 0, 1, 0, 1),
    FR + "wooden_basket": (0, 1, 0, 1, 0, 1),
    FR + "canvas_rug": (-0.5, 1.5, 0, 0.062, -0.5, 1.5),
    LI + "cypress_barrel": (0.047, 0.953, 0, 0.906, 0, 1),
    LI + "fir_barrel": (0.047, 0.953, 0, 0.906, 0, 1),
    LI + "loaded_fir_barrel": (0.047, 0.953, 0, 0.906, 0, 1),
    LI + "loaded_cypress_barrel": (0.047, 0.953, 0, 0.906, 0, 1),
    LI + "cypress_rack": (0, 1, 0, 0.25, 0, 1),
    LI + "storage_vase": (0.062, 0.938, 0, 1, 0.062, 0.938),
    LI + "brown_storage_vase": (0.062, 0.938, 0, 1, 0.062, 0.938),
}

# stand-in look when the mod is missing (default: a box of mid brown wood)
FALLBACK_REGION = {FD + "chained_kerosene_lantern": "lantern", FD + "kerosene_lantern": "lantern", FD + "wine_bottle": "glass",
                   FD + "red_wine_bottle": "glass", FD + "wine_glass": "glass", FD + "pile_of_books": "books", FU + "book_pile": "books",
                   FR + "rice_bag": "sack", FD + "rug_3x_3": "rug", FR + "canvas_rug": "sack", FD + "tall_bookshelf": "books",
                   FU + "spruce_crate": "wood_light", FU + "dark_oak_crate": "wood_dark", FU + "dark_oak_bench": "wood_dark",
                   FU + "dark_oak_stool": "wood_dark", FD + "desk": "wood_dark", FD + "liquor_cabinet": "wood_dark",
                   LI + "storage_vase": "red_paint", LI + "brown_storage_vase": "wood_mid", FU + "amphora": "red_paint",
                   FD + "cigar_box": "red_paint", FD + "double_bed": "bedding", FU + "dark_oak_chair": "wood_dark", FU + "chess_board": "stripe",
                   FD + "coat_hanger": "wood_dark"}

GLOWING = {FD + "kerosene_lantern", FD + "chained_kerosene_lantern"}   # drawn full-bright while the lamps are lit

BLOCKS = []   # dicts: block, x, y, z, yaw, solid, scale
SEATS = []    # dicts: x, y, z, dx, dy, dz
CUSTOM = []   # furniture drawn by generate_frigate: (builder name, kwargs, solid box or None)

M, L, C, Q = fs.MAIN_DECK_Y, fs.LOWER_FLOOR_Y, fs.CABIN_FLOOR_Y, fs.QUARTERDECK_Y
HOLD_CEIL, CABIN_CEIL = M - fs.SLAB, Q - fs.SLAB


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


def gun(side, z, where):
    """A gun on its carriage, run out to a port: in the hold (behind a red lid) or on the main deck."""
    deck_y = L if where == "hold" else M
    base_y = (fs.GUNPORT_Y - 0.05) if where == "hold" else M + 1.05
    xo = fs.hull_x(z, base_y)
    x_in, x_out = side * (xo - 1.6), side * (xo - 0.35)
    box = (min(x_in, x_out), max(x_in, x_out), deck_y, deck_y + 1.0, z - 0.45, z + 0.45)
    custom("cannon", solid=box, name="gun_%s_%s%d" % (where, "p" if side > 0 else "s", int(round(z + 20))), side=side, z=z, base_y=base_y,
           deck_y=deck_y)


# ---------------------------------------------------------------- the rooms
def captain_cabin():
    """Cabine du capitaine: the double bed against the port side and the stern, a night stand with its
    lantern at its head, a sea chest at its foot; the desk along the starboard side with the chart, the
    compass, books, a bottle and a lantern, the captain's high chair before it; framed sea charts on the
    bulkhead, the bookcase, the liquor cabinet and the coat rack by the door, a small table with a chess
    board and a stool, a rug, the telescope aimed at the stern windows, lanterns from the beams."""
    block(FD + "double_bed", 2.25, C, -16.35, "bow", centre=True)
    block(FD + "night_stand", 0.95, C, -17.05, "bow", centre=True)
    block(FD + "kerosene_lantern", 0.95, C + 0.625, -17.0, "bow", solid=False)
    custom("chest", solid=(1.75, 2.75, C, C + 0.65, -15.15, -14.6), name="captain_chest", p=(2.25, C, -14.88))
    # the desk along the starboard side, the captain's chair before it
    block(FD + "desk", -2.65, C, -14.0, "port", centre=True)
    custom("chart_sheet", name="captain_chart", p=(-2.6, C + 1.02, -14.3), yaw=0.25)
    block(FD + "kerosene_lantern", -2.85, C + 1.02, -15.1, "port", solid=False)
    block(FD + "pile_of_books", -2.85, C + 1.02, -12.9, "port", solid=False)
    block(FD + "red_wine_bottle", -2.45, C + 1.02, -13.05, "port", solid=False)
    block(FD + "wine_glass", -2.3, C + 1.02, -13.3, "port", solid=False)
    block(FD + "cigar_box", -2.9, C + 1.02, -14.95, "port", solid=False, scale=0.8)
    custom("compass_box", name="captain_compass", p=(-2.3, C + 1.02, -14.95))
    block(FU + "dark_oak_chair", -1.45, C, -14.0, "starboard", solid=False, centre=True)
    seat(-1.5, C + 0.56, -14.0, -0.5, C, -14.0)
    custom("wall_chart", name="captain_wall_chart", center=(-3.3, C + 1.85, -14.0), normal=(1, 0, 0), w=1.3, h=0.85)
    # by the door: the bookcase and the coat rack (port), the liquor cabinet (starboard), charts on the bulkhead
    block(FD + "tall_bookshelf", 2.7, C, -10.45, "stern", centre=True)
    block(FD + "coat_hanger", 1.6, C, -10.5, "stern", centre=True)
    block(FD + "liquor_cabinet", -2.5, C, -10.35, "stern", centre=True)
    block(FD + "kerosene_lantern", -3.1, C + 1.0, -10.35, "stern", solid=False)
    block(FD + "wine_bottle", -1.85, C + 1.0, -10.3, "stern", solid=False)
    custom("wall_chart", name="captain_bulkhead_chart", center=(-2.4, C + 1.95, -10.03), normal=(0, 0, -1), w=1.1, h=0.7)
    custom("wall_chart", name="captain_bulkhead_chart_2", center=(2.4, C + 2.1, -10.03), normal=(0, 0, -1), w=1.0, h=0.5)
    # a small table with a chess board and its stool, on the port side before the bed
    block(FU + "dark_oak_square_table", 2.9, C, -12.3, "stern")
    block(FU + "chess_board", 2.9, C + 1.0, -12.3, "stern", solid=False, scale=0.8)
    block(FU + "dark_oak_stool", 1.9, C, -12.3, "starboard", solid=False, centre=True)
    seat(1.9, C + 0.56, -12.3, 1.0, C, -12.3)
    # shelves of books and bottles over the desk and over the bed
    block(FU + "dark_oak_shelf", -3.1, C + 1.45, -12.4, "port", solid=False, centre=True)
    block(FU + "book_pile", -3.1, C + 1.7, -12.6, "port", solid=False, scale=0.7)
    block(FD + "wine_bottle", -3.1, C + 1.7, -12.1, "port", solid=False)
    block(FU + "dark_oak_shelf", 2.4, C + 1.65, -17.05, "bow", solid=False, centre=True)
    block(FD + "pile_of_books", 2.1, C + 1.9, -17.05, "bow", solid=False, scale=0.8)
    block(FD + "red_wine_bottle", 2.7, C + 1.9, -17.05, "bow", solid=False)
    wall_lantern(3.0, C + 1.3, -13.6, 1)
    block(FD + "rug_3x_3", 0.0, C, -12.9, "stern", solid=False, centre=True)
    custom("telescope", name="captain_telescope", p=(-0.9, C, -16.6), facing="stern")
    lantern(0.0, CABIN_CEIL, -11.6)
    lantern(0.0, CABIN_CEIL, -15.6)


def hold():
    """Cale: the guns on their carriages behind the red ports (four a side), barrels on their cradles,
    upright barrels, crates stacked along the sides, sacks, jars and amphorae forward, a workbench, the
    carpenter's tool board, a small table with a stool, lanterns from the beams; the centre line stays
    clear from the foot of the companionway to the bow."""
    for side in (1, -1):
        for z in (-7.5, -4.5, 7.5, 10.5):
            gun(side, z, "hold")
    f_in = {1: "starboard", -1: "port"}
    # starboard: barrels on cradles, crates, provisions
    x = -3.05
    for k, z in enumerate((-1.3, -0.2)):
        block(LI + "cypress_rack", x, L, z, "port")
        block(LI + ("loaded_fir_barrel" if k else "loaded_cypress_barrel"), x, L + 0.25, z, "port")
    block(LI + "fir_barrel", x + 0.1, L + 1.15, -0.75, "port", solid=False, scale=0.9)
    block(FU + "spruce_crate", x, L, 1.1, f_in[-1])
    block(FU + "dark_oak_crate", x, L, 2.2, f_in[-1])
    block(FU + "spruce_crate", x + 0.1, L + 1.0, 1.65, f_in[-1], solid=False, scale=0.9)
    block(FR + "potato_crate", x, L, 3.6, f_in[-1])
    block(FR + "rice_bag", x, L, 4.7, f_in[-1])
    block(FR + "rice_bag", x + 0.1, L + 0.95, 4.6, f_in[-1], solid=False, scale=0.75)
    block(FR + "cabbage_crate", x, L, 8.9, f_in[-1])
    block(FR + "wooden_basket", x, L + 1.0, 8.9, f_in[-1], solid=False, scale=0.6)
    # port, after the companionway: barrels and crates, the workbench forward
    x = 3.05
    block(LI + "cypress_barrel", x, L, -2.5, f_in[1])
    block(LI + "cypress_barrel", x, L, -1.5, f_in[1])
    block(LI + "fir_barrel", x - 0.05, L + 0.9, -2.0, f_in[1], solid=False, scale=0.85)
    block(FU + "dark_oak_crate", x, L, 5.1, f_in[1])
    block(FU + "spruce_crate", x, L, 6.2, f_in[1])
    block(FU + "spruce_crate", x - 0.1, L + 1.0, 5.6, f_in[1], solid=False, scale=0.85)
    block(FD + "workbench", 2.95, L, 8.8, "starboard", centre=True)
    block(FD + "tool_board", 3.7, L + 1.3, 8.8, "starboard", solid=False, centre=True)
    # forward of the fore mast: jars, amphorae, sacks and a sea chest; a rug on the floor
    block(LI + "storage_vase", -2.2, L, 10.4, "stern", scale=0.9)
    block(LI + "brown_storage_vase", -3.0, L, 10.3, "stern", scale=0.85)
    block(FU + "amphora", 2.2, L, 10.5, "bow", scale=0.75)
    block(FR + "rice_bag", 0.0, L, 10.6, "stern")
    block(FR + "rice_bag", -1.0, L, 10.7, "stern", solid=False, scale=0.7)
    custom("chest", solid=(0.7, 1.7, L, L + 0.65, 10.25, 10.85), name="hold_chest", p=(1.2, L, 10.55))
    block(FR + "canvas_rug", 0.0, L, 7.8, "stern", solid=False)
    # a small table and its stool, starboard forward
    block(FU + "dark_oak_square_table", -2.8, L, 6.5, "stern")
    block(FD + "kerosene_lantern", -2.8, L + 1.0, 6.5, "stern", solid=False)
    block(FU + "spruce_stool", -1.9, L, 6.5, "starboard", solid=False, centre=True)
    seat(-1.9, L + 0.56, 6.5, -1.0, L, 6.5)
    custom("coil", name="hold_coil_0", p=(2.4, L, 0.9), r=0.36)
    custom("coil", name="hold_coil_1", p=(-1.9, L, -7.9), r=0.32)
    # shelves of jars on the hull between the guns
    for z in (-6.6, -5.9):
        block(FU + "spruce_shelf", 3.7, L + 1.9, z, "starboard", solid=False, centre=True)
    for k, z in enumerate((-5.8, -5.3, -4.8)):
        block(LI + ("storage_vase" if k % 2 else "brown_storage_vase"), 3.7, L + 2.15, z, "starboard", solid=False, scale=0.3)
    for z in (-6.0, -1.5, 3.0, 8.5):
        lantern(0.0 if abs(z - fs.FORE_MAST_Z) > 1.5 and abs(z - fs.MAIN_MAST_Z) > 1.5 else 1.2, HOLD_CEIL, z)


def deck():
    """Pont principal et gaillard: three guns a side run out through the balustrade, two benches a side
    abaft the main mast, barrels and crates against the bulwarks, rope coils; on the quarterdeck two
    benches by the stern rail. The walking areas, the stairs, the hatches and the centre line stay clear."""
    for side in (1, -1):
        for z in (-1.5, 8.0, 12.0):
            gun(side, z, "deck")
        x = side * 3.7
        for z in (-5.5, -4.5):
            block(FU + "spruce_bench", x, M, z, "bow", solid=False)
            seat(x, M + 0.562, z, x - side * 0.9, M, z)
        xq = side * 2.8
        block(FU + "dark_oak_bench", xq, Q, -16.8, "bow", solid=False)
        seat(xq, Q + 0.562, -16.8, xq - side * 0.9, Q, -16.8)
    block(LI + "cypress_barrel", 3.65, M, 6.0, "starboard")
    block(LI + "cypress_barrel", -3.6, M, 5.0, "port")
    block(LI + "cypress_barrel", -3.6, M, 5.95, "port")
    block(LI + "fir_barrel", -3.6, M + 0.9, 5.45, "port", solid=False, scale=0.85)
    block(FU + "spruce_crate", -3.1, M, 14.3, "port")
    block(FU + "dark_oak_crate", 3.1, M, 14.3, "starboard")
    block(FU + "spruce_crate", 3.1, M + 1.0, 14.3, "bow", solid=False, scale=0.7)
    custom("coil", name="deck_coil_0", p=(1.4, M, fs.MAIN_MAST_Z - 1.5), r=0.34)
    custom("coil", name="deck_coil_1", p=(-1.3, M, fs.FORE_MAST_Z - 1.3), r=0.34)
    custom("coil", name="deck_coil_2", p=(1.3, M, fs.FORE_MAST_Z + 1.4), r=0.3)
    custom("telescope", name="deck_telescope", p=(-2.4, Q, -13.3), facing="starboard")


def build():
    BLOCKS.clear()
    SEATS.clear()
    CUSTOM.clear()
    captain_cabin()
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


def apply_to_grid(g):
    """FURNITURE cells under the solid furniture (on the floor of a room, or on a deck). Every solid
    piece must be solid somewhere (a piece standing over cell boundaries keeps the cells it covers)."""
    free = (g.k == fi.DRY) | (g.k == fi.OUT)
    boxes = [(kwargs.get("name", builder), solid) for builder, kwargs, solid in CUSTOM if solid is not None]
    for i, b in enumerate(BLOCKS):
        if b["solid"]:
            x0, x1, y0, y1, z0, z1 = footprint(b["block"], b["x"], b["y"], b["z"], b["yaw"], b["scale"])
            boxes.append(("%s #%d" % (b["block"], i), (x0, x1, b["y"], y1, z0, z1)))
    for name, box in boxes:
        g.k[_cells(g, box) & free] = fi.FURNITURE
    hollow = [name for name, box in boxes if not (_cells(g, box) & (g.k == fi.FURNITURE)).any()]
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


DECOR_PATH = "src/main/resources/assets/medievalships/interiors/blue_frigate_decor.json"
