"""Furniture of the Royal Lion Ship (P1: the essentials; the decoration phase furnishes every room): blocks of the decoration mods (drawn by the ship where they
stand, moving with it; never placed in the world), furniture modelled for the ship (drawn by
tools/generate_royal_lion.py with the builders of tools/corsair_furniture.py and generate_corsair.py), and
the seats.

  src/main/resources/assets/medievalships/interiors/royal_lion_ship_decor.json

Same format as tools/corsair_decor.py (read by fr.medievalships.core.InteriorDecor). A block whose mod
is missing on a client is replaced by its stand-in, a box of the same size in the model (bone
"fallback_<i>"). The solid furniture is added to the interior grid (FURNITURE cells): the players walk
round the desk, the bed, the guns and the cargo.

The mods' blocks first (catalog /tmp/claude-0/mods_catalog/catalog.json: Farmhouse Decorations,
Furnish, Farmer's Delight, Lands of Icaria), modelled pieces only for what they lack (the framed sea
charts, the chart and compass on the desk, the telescope, sea chests, rope coils, the guns on their
carriages). Kept clear (checked by RoyalLionShipTest): the cabin door, the stairs, the centre line of the hold,
the seats' stand-up spots.
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
CUSTOM = []   # furniture drawn by generate_royal_lion: (builder name, kwargs, solid box or None)

M, L, C, Q, F = fs.MAIN_DECK_Y, fs.LOWER_FLOOR_Y, fs.CABIN_FLOOR_Y, fs.QUARTERDECK_Y, fs.FORECASTLE_Y
HOLD_CEIL, CABIN_CEIL, STATE_CEIL = M - fs.SLAB, Q - fs.SLAB, fs.ROUNDHOUSE_CEIL_Y


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
    """Cabine du capitaine (main deck level, under the quarterdeck): the bed against the port side, the desk on
    the starboard side with the captain's chair, a bookcase by the door, a rug, lanterns from the beams."""
    block(FD + "double_bed", 3.0, C, -17.6, "bow", centre=True)
    block(FD + "night_stand", 1.7, C, -18.6, "bow", centre=True)
    block(FD + "kerosene_lantern", 1.7, C + 0.625, -18.55, "bow", solid=False)
    block(FD + "desk", -3.4, C, -15.0, "port", centre=True)
    block(FU + "dark_oak_chair", -2.2, C, -15.0, "starboard", solid=False, centre=True)
    seat(-2.25, C + 0.56, -15.0, -1.25, C, -15.0)
    block(FD + "tall_bookshelf", 3.4, C, -11.5, "stern", centre=True)
    block(FD + "rug_3x_3", 0.0, C, -14.5, "stern", solid=False, centre=True)
    lantern(0.0, CABIN_CEIL, -13.0)
    lantern(0.0, CABIN_CEIL, -17.5)


def stateroom():
    """Salle d'apparat (the roundhouse on the quarterdeck, under the blue roof): a dining table with chairs on
    both sides, a lantern from the ceiling."""
    block(FU + "dark_oak_square_table", 0.0, Q, -18.2, "stern")
    for x, facing, dx in ((1.0, "starboard", 1.9), (-1.0, "port", -1.9)):
        block(FU + "dark_oak_chair", x, Q, -18.2, facing, solid=False, centre=True)
        seat(x, Q + 0.56, -18.2, dx, Q, -18.2)
    lantern(0.0, STATE_CEIL, -17.3)


def crew_quarters():
    """Quartiers de l'equipage (lower deck, aft): sea chests and benches along the sides, a table, lanterns."""
    block(FU + "dark_oak_square_table", 3.4, L, -9.0, "stern")
    block(FU + "spruce_bench", 3.4, L, -10.0, "stern", solid=False)
    seat(3.4, L + 0.562, -10.0, 2.4, L, -10.0)
    block(FU + "spruce_bench", 3.4, L, -8.0, "bow", solid=False)
    seat(3.4, L + 0.562, -8.0, 2.4, L, -8.0)
    custom("chest", solid=(-4.4, -3.4, L, L + 0.65, -12.3, -11.75), name="crew_chest_0", p=(-3.9, L, -12.0))
    custom("chest", solid=(-4.4, -3.4, L, L + 0.65, -10.3, -9.75), name="crew_chest_1", p=(-3.9, L, -10.0))
    lantern(0.0, HOLD_CEIL, -9.0)


def hold():
    """Cale (lower deck, forward): barrels and crates along the sides; the centre line stays clear."""
    x = -4.2
    block(LI + "cypress_barrel", x, L, 1.0, "port")
    block(LI + "cypress_barrel", x, L, 2.0, "port")
    block(FU + "spruce_crate", x, L, 4.5, "port")
    block(FU + "dark_oak_crate", x, L, 5.5, "port")
    block(FR + "rice_bag", x, L, 10.0, "port")
    block(FU + "spruce_crate", 4.0, L, 9.5, "starboard")
    block(FU + "dark_oak_crate", 4.0, L, 10.5, "starboard")
    block(LI + "fir_barrel", 4.2, L, -1.0, "starboard")
    for z in (0.5, 8.0, 12.5):
        lantern(0.0 if abs(z - fs.FORE_MAST_Z) > 1.5 and abs(z - fs.MAIN_MAST_Z) > 1.5 else 1.2, HOLD_CEIL, z)


def deck():
    """Pont principal, gaillards: benches against the bulwarks forward of the main mast, the deck cargo of the
    references (stacked crates, barrels, sacks) against the bulwarks, clear of the stairs, the hatches, the
    capstan, the gangplank's stairs (starboard, z 1.5..4.5) and the centre line."""
    for side in (1, -1):
        x = side * 4.45
        block(FU + "spruce_bench", x, M, -0.2, "bow", solid=False)
        seat(x, M + 0.562, -0.2, x - side * 0.9, M, -0.2)
    # port, aft of the main mast: crates two high, a barrel, a sack
    block(FU + "spruce_crate", 4.25, M, -5.6, "port")
    block(FU + "dark_oak_crate", 4.25, M, -4.6, "port")
    block(FU + "spruce_crate", 4.25, M + 1.0, -5.1, "port", solid=False, scale=0.85)
    block(LI + "cypress_barrel", 3.25, M, -5.6, "port")
    block(FR + "rice_bag", 3.25, M, -4.6, "port")
    # starboard, forward of the gangplank: crates and barrels by the fore mast
    block(FU + "spruce_crate", -3.9, M, 7.0, "starboard")
    block(FU + "dark_oak_crate", -3.9, M, 8.0, "starboard")
    block(FU + "spruce_crate", -3.9, M + 1.0, 7.5, "starboard", solid=False, scale=0.85)
    block(LI + "cypress_barrel", -2.9, M, 7.0, "starboard")
    block(FR + "rice_bag", -2.9, M, 8.0, "starboard")
    # port, forward of the hold's companionway
    block(LI + "cypress_barrel", 4.0, M, 9.2, "port")
    block(LI + "fir_barrel", 4.0, M, 10.2, "port")
    block(FU + "dark_oak_crate", 3.0, M, 9.7, "port")
    # the forecastle: barrels and a crate by the bulwarks
    block(LI + "cypress_barrel", 2.9, F, 15.0, "port")
    block(FU + "spruce_crate", -2.9, F, 15.0, "starboard")
    block(FR + "rice_bag", -2.9, F + 1.0, 15.0, "starboard", solid=False, scale=0.75)


def build():
    BLOCKS.clear()
    SEATS.clear()
    CUSTOM.clear()
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


DECOR_PATH = "src/main/resources/assets/medievalships/interiors/royal_lion_ship_decor.json"
