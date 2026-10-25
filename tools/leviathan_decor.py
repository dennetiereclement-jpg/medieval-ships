"""Furniture of the Sky Leviathan: blocks of the user's decoration mods (drawn by the airship where they
stand, moving with it; never placed in the world), the furniture made for it (tools/leviathan_furniture.py)
and the seats, room by room after the interior views of the reference sheet (pont principal, salle
commune, cabine du capitaine, cale / stockage, coursive, salle des machines).

  src/main/resources/assets/medievalships/interiors/sky_leviathan_decor.json

Same format and same rules as the Nautilus (tools/nautilus_decor.py): each mod block is given by the
centre of its bottom face (ship-local) and the direction its front faces; its footprint becomes solid
cells of the interior grid (chairs, benches and small things on tables are not solid); a block whose mod
is missing on a client is replaced by its stand-in, a box of the same size in the model (bone
"fallback_<i>").

Mods used: farmhouse_decorations (Farmhouse Decorations), furnish (Furnish), farmersdelight (Farmer's
Delight), landsoficaria (Lands of Icaria), mebahelcreaturesdwarven (Mebahel Dwarven Automatons).
Block measurements: the default state's model bounds (x east, z south, front north), from the mods' files.
"""
import json
import math

import leviathan_interior as li
import leviathan_shape as ls
import nautilus_decor as nd

FACING = nd.FACING   # stern 0, starboard 90, bow 180, port 270 (the block's north = its front)

FD = "farmhouse_decorations:"
FU = "furnish:"
FR = "farmersdelight:"
IC = "landsoficaria:"
MB = "mebahelcreaturesdwarven:"

# default-state model bounds (minX, maxX, minY, maxY, minZ, maxZ) in block space, front = north (-z)
BOUNDS = {
    FD + "double_bed": (-0.984, 0.984, 0.0, 1.203, 0.016, 1.984),
    FD + "single_bed": (-0.109, 1.109, 0.0, 1.141, 0.016, 1.984),
    FD + "dining_table_side": (0.0, 1.0, -0.016, 1.0, 0.016, 0.984),
    FD + "dining_table_middle": (0.0, 1.0, 0.797, 1.0, 0.016, 0.984),
    FD + "desk": (-0.953, 1.984, 0.0, 1.016, -0.031, 1.031),
    FD + "tall_bookshelf": (0.0, 1.0, 0.0, 1.969, 0.188, 1.0),
    FD + "wall_shelf": (0.0, 1.0, 0.0, 1.219, 0.559, 1.0),
    FD + "kitchen_wall_shelf": (0.0, 1.0, 0.0, 1.0, 0.375, 1.0),
    FD + "liquor_cabinet": (-1.0, 1.0, 0.0, 1.0, 0.297, 1.0),
    FD + "dining_chair": (0.125, 0.875, 0.0, 1.563, 0.0, 0.973),
    FD + "wardrobe": (-0.844, 0.844, 0.0, 1.984, 0.156, 1.0),
    FD + "dresser": (0.0, 1.0, 0.0, 1.016, 0.25, 1.0),
    FD + "night_stand": (0.188, 0.812, 0.0, 0.625, 0.5, 1.0),
    FD + "kerosene_lantern": (0.37, 0.63, 0.0, 0.484, 0.375, 0.625),
    FD + "chained_kerosene_lantern": (0.37, 0.63, 0.328, 1.0, 0.375, 0.625),
    FD + "wine_bottle": (0.391, 0.547, 0.0, 0.328, 0.422, 0.578),
    FD + "red_wine_bottle": (0.391, 0.547, 0.0, 0.328, 0.422, 0.578),
    FD + "wine_glass": (0.438, 0.562, 0.0, 0.25, 0.438, 0.562),
    FD + "pile_of_books": (0.283, 0.643, 0.002, 0.234, 0.403, 0.732),
    FD + "cigar_box": (0.25, 0.75, 0.0, 0.547, 0.312, 0.734),
    FD + "cuckoo_clock": (0.203, 0.797, 0.172, 0.969, 0.812, 1.0),
    FD + "coat_hanger": (0.078, 0.922, -0.048, 1.953, 0.078, 0.922),
    FD + "workbench": (-0.875, 0.875, 0.0, 1.25, 0.078, 1.0),
    FD + "tool_board": (-0.844, 0.844, 0.219, 0.844, 0.9, 1.0),
    FD + "kitchen_counter": (0.0, 1.0, 0.0, 1.0, 0.078, 1.0),
    FD + "seasoning_rack": (0.125, 0.875, 0.0, 0.781, 0.688, 1.0),
    FD + "acoustic_guitar": (0.25, 0.75, 0.013, 1.185, 0.431, 0.999),
    FU + "spruce_table": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FU + "dark_oak_table": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FU + "dark_oak_bench": (0.0, 1.0, 0.0, 0.562, 0.25, 0.75),
    FU + "spruce_chair": (0.188, 0.812, 0.0, 1.375, 0.062, 0.812),
    FU + "dark_oak_chair": (0.062, 0.938, 0.0, 1.875, 0.0, 0.812),
    FU + "spruce_stool": (0.188, 0.812, 0.0, 0.562, 0.125, 0.75),
    FU + "dark_oak_stool": (0.188, 0.812, 0.0, 0.562, 0.125, 0.75),
    FU + "spruce_crate": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FU + "dark_oak_crate": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FU + "spruce_shelf": (0.0, 1.0, 0.0, 0.25, 0.688, 1.0),
    FU + "dark_oak_shelf": (0.0, 1.0, 0.002, 0.25, 0.688, 1.022),
    FU + "plate": (0.062, 0.938, 0.0, 0.062, 0.062, 0.938),
    FU + "book_pile": (0.167, 0.88, 0.013, 0.394, 0.182, 0.865),
    FU + "picture_frame": (0.25, 0.75, 0.002, 0.609, 0.219, 0.632),
    FU + "small_locker": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FU + "spruce_square_table": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FU + "dark_oak_square_table": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FU + "chess_board": (0.125, 0.875, 0.0, 0.062, 0.125, 0.875),
    FR + "stove": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FR + "cooking_pot": (0.0, 1.0, 0.0, 0.904, 0.125, 0.875),
    FR + "skillet": (0.062, 0.938, 0.0, 0.25, 0.062, 1.688),
    FR + "cutting_board": (0.062, 0.938, 0.0, 0.062, 0.062, 0.938),
    FR + "potato_crate": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FR + "carrot_crate": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FR + "onion_crate": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FR + "cabbage_crate": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FR + "beetroot_crate": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FR + "rice_bag": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FR + "wooden_basket": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FR + "roast_chicken_block": (0.062, 0.938, 0.0, 0.5, 0.062, 0.938),
    FR + "honey_glazed_ham_block": (0.062, 0.938, 0.0, 0.625, 0.062, 1.0),
    FR + "straw_bale": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FR + "apple_pie": (0.125, 0.875, 0.0, 0.25, 0.125, 0.875),
    IC + "cypress_barrel": (0.047, 0.953, 0.0, 0.906, 0.0, 1.0),
    IC + "loaded_cypress_barrel": (0.047, 0.953, 0.0, 0.906, 0.0, 1.0),
    IC + "tapped_cypress_barrel": (0.047, 0.953, 0.0, 0.906, -0.246, 1.0),
    IC + "populus_barrel": (0.047, 0.953, 0.0, 0.906, 0.0, 1.0),
    IC + "cypress_rack": (0.0, 1.0, 0.0, 0.25, 0.0, 1.0),
    IC + "storage_vase": (0.062, 0.938, 0.0, 1.0, 0.062, 0.938),
    MB + "dwemer_metal_pipe": (0.125, 0.875, 0.125, 0.875, 0.125, 1.0),
    MB + "dwemer_metal_pipe_gear": (0.125, 0.875, 0.125, 0.875, 0.0, 1.0),
    MB + "dwemer_metal_block": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    MB + "dwemer_chest": (0.003, 1.003, 0.0, 0.938, 0.069, 0.931),
}
# seat surface height of the seats (the passenger sits a little lower, on the cushion)
SEAT_H = {FU + "dark_oak_bench": 0.562, FU + "spruce_chair": 0.562, FU + "dark_oak_chair": 0.562, FU + "spruce_stool": 0.562,
          FU + "dark_oak_stool": 0.562, FD + "dining_chair": 0.625}

# look of the stand-in (fallback box) when the mod is missing; lanterns glow
FALLBACK_REGION = {
    FD + "double_bed": "in_blanket", FD + "single_bed": "in_bedding", FD + "tall_bookshelf": "in_books", FD + "wall_shelf": "in_books",
    FD + "kitchen_wall_shelf": "in_jars", FD + "liquor_cabinet": "in_jars2", FD + "kerosene_lantern": "in_lamp",
    FD + "chained_kerosene_lantern": "in_lamp", FD + "wine_bottle": "in_glass_green", FD + "red_wine_bottle": "coral_red",
    FD + "wine_glass": "glass", FD + "pile_of_books": "in_books", FU + "book_pile": "in_books", FD + "tool_board": "in_tools",
    FU + "plate": "in_bedding", FR + "stove": "in_brick", FR + "cooking_pot": "in_iron", FR + "skillet": "in_iron",
    FR + "rice_bag": "in_sack", FR + "straw_bale": "in_canvas", FR + "wooden_basket": "in_plank", FR + "potato_crate": "crate",
    FR + "carrot_crate": "crate", FR + "onion_crate": "crate", FR + "cabbage_crate": "crate", FR + "beetroot_crate": "crate",
    FU + "spruce_crate": "crate", FU + "dark_oak_crate": "crate", IC + "cypress_barrel": "barrel", IC + "loaded_cypress_barrel": "barrel",
    IC + "tapped_cypress_barrel": "barrel", IC + "populus_barrel": "barrel", IC + "storage_vase": "coral_red",
    MB + "dwemer_metal_pipe": "in_brass", MB + "dwemer_metal_pipe_gear": "in_brass", MB + "dwemer_metal_block": "in_brass",
    MB + "dwemer_chest": "in_gold", FU + "small_locker": "in_rivets", FU + "chess_board": "in_paper", FD + "cuckoo_clock": "in_beam",
    FR + "roast_chicken_block": "in_canvas", FR + "honey_glazed_ham_block": "in_canvas", FR + "apple_pie": "in_canvas",
    FD + "kitchen_counter": "in_plank", FD + "seasoning_rack": "in_jars", FU + "picture_frame": "in_map_wall",
}
GLOWING_FALLBACK = (FD + "kerosene_lantern", FD + "chained_kerosene_lantern")

BLOCKS = []    # dicts: block, x, y, z, yaw, solid, scale
SEATS = []     # dicts: x, y, z, dx, dy, dz
CUSTOM = []    # furniture made for the airship: (builder name, kwargs, solid box or None)
PAINTINGS = []
SWITCHES = []

M0, LO, HO, EO, CASTLE, POOP = li.M0, li.LO, li.HO, li.EO, li.CASTLE, li.POOP
CEIL_LO = M0 - li.SLAB          # ceiling of the lower deck (-0.5)
CEIL_M = CASTLE - li.SLAB       # ceiling under the castles (2.5)
CEIL_C = POOP - li.SLAB         # ceiling of the chart room (5.0)
CEIL_H = LO - li.SLAB           # ceiling of the hold (-3.5)
STERN_WALL = -19.5              # inner face of the transom (the rooms under the castles end there)

_GRID = []


def grid():
    if not _GRID:
        _GRID.append(li.build())
    return _GRID[0]


def wall_x(y, z, side, x_from=0.0):
    """Inner face of the side wall (side +1: port, -1: starboard) at height y and z, scanning outwards from x_from."""
    g = grid()
    j = int(math.floor((y - li.Y0) / li.CELL))
    l = int(math.floor((z - li.Z0) / li.CELL))
    i = int(math.floor((x_from - li.X0) / li.CELL))
    while 0 <= i < g.nx:
        if g.k[i, j, l] in (li.SOLID, li.OUT):
            return li.X0 + (i if side > 0 else i + 1) * li.CELL
        i += side
    return None


def wall_min(y0, y1, z, side, x_from=0.0):
    """The wall's innermost face between heights y0 and y1."""
    xs = [wall_x(y, z, side, x_from) for y in [y0 + 0.1 + 0.5 * k for k in range(int((y1 - y0) / 0.5) + 1)] if y < y1]
    xs = [x for x in xs if x is not None]
    return min(xs, key=abs) if xs else None


# ---------------------------------------------------------------- placing
def _footprint(bid, x, y, z, yaw, scale=1.0):
    bb = BOUNDS[bid]
    pts = [nd.to_ship(bid, x, y, z, yaw, px, py, pz, scale) for px in (bb[0], bb[1]) for py in (bb[2], bb[3]) for pz in (bb[4], bb[5])]
    xs, ys, zs = zip(*pts)
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def block(bid, x, y, z, facing="stern", solid=True, scale=1.0):
    """A mod block by the centre of its bottom face (x, y, z) and the direction its front faces."""
    yaw = FACING[facing] if isinstance(facing, str) else float(facing)
    BLOCKS.append({"block": bid, "x": x, "y": y, "z": z, "yaw": yaw, "solid": solid, "scale": scale})
    return len(BLOCKS) - 1


def at(bid, cx, y, cz, facing="stern", solid=True, scale=1.0):
    """A mod block placed by the centre (cx, cz) of its footprint (its model may overflow its block)."""
    yaw = FACING[facing] if isinstance(facing, str) else float(facing)
    x0, x1, _, _, z0, z1 = _footprint(bid, 0.0, 0.0, 0.0, yaw, scale)
    return block(bid, cx - (x0 + x1) / 2, y, cz - (z0 + z1) / 2, facing, solid, scale)


def against(bid, side, y, z, facing=None, solid=True, scale=1.0, gap=0.02, x_from=0.0, top=None):
    """A mod block standing against a side wall (side +1: port, -1: starboard), its front turned inboard."""
    facing = facing or ("starboard" if side > 0 else "port")
    yaw = FACING[facing]
    x0, x1, y0, y1, z0, z1 = _footprint(bid, 0.0, 0.0, 0.0, yaw, scale)
    h = top if top is not None else (y1 - y0)
    ws = [wall_min(y, y + h, zz, side, x_from) for zz in (z - (z1 - z0) / 2 + 0.06, z, z + (z1 - z0) / 2 - 0.06)]
    w = min([v for v in ws if v is not None], key=abs)     # the innermost face along the block's length
    cx = w - side * ((x1 - x0) / 2 + gap)
    return at(bid, cx, y, z, facing, solid, scale)


def custom(builder, solid=None, **kwargs):
    """Furniture of generate_leviathan.py (FURNITURE_BUILDERS); solid = (x0, x1, y0, y1, z0, z1) added to the grid."""
    CUSTOM.append((builder, kwargs, solid))


def seat(x, y, z, dx, dy, dz):
    """A seat: sitting point (x, y = seat height, z) and where to stand up (dx, dy, dz)."""
    SEATS.append({"x": x, "y": y, "z": z, "dx": dx, "dy": dy, "dz": dz})


def chair(bid, x, floor, z, facing, dx, dz, solid=False):
    """A chair, stool or bench block centred at (x, z) and its seat."""
    at(bid, x, floor, z, facing, solid=solid)
    seat(x, floor + SEAT_H[bid] - 0.12, z, dx, floor + 0.02, dz)


def painting(name, motive, center, normal, w, h):
    """A vanilla painting (drawn by the renderer with the game's own texture) in a dark wooden frame."""
    custom("painting_frame", name=name, center=center, normal=normal, w=w, h=h)
    n = math.hypot(normal[0], normal[2])
    PAINTINGS.append({"motive": motive, "x": center[0] + normal[0] / n * 0.02, "y": center[1], "z": center[2] + normal[2] / n * 0.02,
                      "nx": normal[0] / n, "nz": normal[2] / n, "w": w, "h": h})


def hanging(x, ceiling, z, drop=0.0):
    """A Farmhouse chained kerosene lantern hanging from the ceiling (its chain reaches the ceiling)."""
    block(FD + "chained_kerosene_lantern", x, ceiling - 1.0 - drop, z, "stern", solid=False)


def wall_lantern(name, side, y, z, x_from=0.0, arm=0.34):
    """A kerosene lantern hung on an iron bracket on a side wall."""
    w = wall_x(y, z, side, x_from)
    p = (w, y, z)
    custom("wall_bracket", name=name, p=p, normal=(-side, 0, 0), arm=arm)
    block(FD + "kerosene_lantern", w - side * arm, y - 0.52, z, "stern", solid=False)


def wall_lantern_z(name, x, y, zw, nz, arm=0.34):
    """A kerosene lantern on a bracket on a transverse wall (face at z = zw, facing nz = +1 / -1)."""
    custom("wall_bracket", name=name, p=(x, y, zw), normal=(0, 0, nz), arm=arm)
    block(FD + "kerosene_lantern", x, y - 0.52, zw + nz * arm, "stern", solid=False)


def frame_room(name, z0, z1, floor, ceil, step=2.0, sides=(-1, 1), x_from=0.0, beams=True, zs=None):
    """The timber frame of a room: posts against the side walls, beams across the ceiling, knees."""
    zs = zs if zs is not None else [z0 + step / 2 + step * k for k in range(int((z1 - z0) / step))]
    for k, z in enumerate(zs):
        xs = {}
        for side in sides:
            w = wall_min(floor, ceil, z, side, x_from)
            if w is None:
                continue
            x = w - side * 0.13
            xs[side] = x
            custom("timber", name="%s_post_%d_%d" % (name, k, side > 0), a=(x, floor, z), b=(x, ceil, z), w=0.26)
        if beams and len(xs) == 2:
            custom("timber", name="%s_beam_%d" % (name, k), a=(xs[-1] - 0.13, ceil - 0.14, z), b=(xs[1] + 0.13, ceil - 0.14, z), w=0.28)
            for side, x in xs.items():
                custom("knee", name="%s_knee_%d_%d" % (name, k, side > 0), corner=(x, ceil - 0.28, z), along=(-side, 0, 0), down=(0, -1, 0))


# ---------------------------------------------------------------- rooms
def common_room():
    """Salle commune (reference panel 2): a long heavy table on the red rug in the middle, chunky benches
    along it and chairs at its ends, bottles, plates, a feast and a lantern on it; shelves of bottles and
    jars, a bar of bottles and casks on tap at the bow end, lanterns over the table, portraits."""
    f = LO
    zt0, zt1 = 5.5, 9.5                  # the table: two rows of Farmhouse dining table pieces along the ship,
    for x in (-0.5, 0.5):                # its turned legs at both ends only (the ends' outer side is the model's east)
        for z in (6.0, 7.0, 8.0, 9.0):
            piece = "dining_table_side" if z in (6.0, 9.0) else "dining_table_middle"
            block(FD + piece, x, f, z, "port" if z == 9.0 else "starboard")
    custom("rug", p=(0.0, f, 7.5), w=4.8, l=6.4)
    # benches (Furnish dark oak benches turned along the ship) and their seats
    for side in (-1, 1):
        for z in (6.0, 7.0, 8.0, 9.0):
            x = side * 1.5
            chair(FU + "dark_oak_bench", x, f, z, "port", x + side * 0.85, z - (0.5 if z > 8.5 else 0.0))   # (clear of the shelves)
    # chairs at the ends of the table
    for x in (-0.5, 0.5):
        chair(FD + "dining_chair", x, f, 4.85, "stern", x, 4.05)
        chair(FD + "dining_chair", x, f, 10.15, "bow", x, 10.95)
    # on the table
    t = f + 1.0
    block(FD + "kerosene_lantern", 0.0, t, 7.5, "stern", solid=False)
    for k, (x, z) in enumerate(((-0.55, 6.1), (0.55, 6.1), (-0.55, 8.9), (0.55, 8.9), (-0.55, 7.0), (0.55, 8.0))):
        block(FU + "plate", x, t, z, "stern", solid=False, scale=0.55)
    block(FR + "roast_chicken_block", 0.05, t, 6.5, "stern", solid=False, scale=0.7)
    block(FR + "honey_glazed_ham_block", -0.1, t, 8.6, "bow", solid=False, scale=0.6)
    for k, (x, z, bid) in enumerate(((0.25, 7.0, FD + "wine_bottle"), (-0.3, 7.9, FD + "wine_bottle"), (0.35, 8.25, FD + "red_wine_bottle"),
                                     (-0.25, 6.7, FD + "red_wine_bottle"))):
        block(bid, x, t, z, "stern", solid=False)
    for k, (x, z) in enumerate(((-0.75, 6.5), (0.75, 7.6), (-0.75, 8.4), (0.75, 6.4))):
        block(FD + "wine_glass", x, t, z, "stern", solid=False, scale=0.85)
    custom("candle", name="common_candle_0", p=(0.2, t, 6.0))
    custom("candle", name="common_candle_1", p=(-0.2, t, 9.0))
    # lanterns over the table
    for z in (6.0, 7.5, 9.0):
        hanging(0.0, CEIL_LO, z, drop=0.05)
    # the bow end: the bar (liquor cabinet), bottles on the wall shelves, casks on tap on their racks
    block(FD + "liquor_cabinet", 0.0, f, 12.2, "stern")
    block(FD + "kitchen_wall_shelf", -0.55, f + 1.25, 12.3, "stern", solid=False)
    block(FD + "kitchen_wall_shelf", 0.55, f + 1.25, 12.3, "stern", solid=False)
    for side in (-1, 1):
        x = side * 1.9
        custom("cask", solid=(x - 0.4, x + 0.4, f, f + 0.9, 11.05, 11.95), name="common_cask_%d" % (side > 0), p=(x, f, 11.5),
               facing=(0, 0, -1))
    # side walls: shelf units of bottles and jars between the portholes, standing shelves, chests
    for side in (-1, 1):
        for z in (5.6, 7.6):
            w = wall_min(f, CEIL_LO, z, side)
            custom("jar_shelf", solid=(min(w, w - side * 0.4), max(w, w - side * 0.4), f, f + 2.2, z - 0.5, z + 0.5),
                   name="common_jars_%d_%d" % (side > 0, int(z)), p=(w - side * 0.02, f, z),
                   normal=(-side, 0, 0), w=1.0, h=2.2, rows=4)
        for z in (2.6, 4.6, 6.6, 8.6):
            w = wall_x(f + 1.35, z, side)
            custom("porthole_in", name="common_porthole_%d_%d" % (side > 0, int(z * 10)), center=(w - side * 0.01, f + 1.35, z),
                   normal=(-side, 0, 0))
    against(FD + "wall_shelf", -1, f, 3.6, solid=True)
    against(FD + "wall_shelf", -1, f, 9.4, solid=True)
    against(FD + "dresser", 1, f, 9.4, solid=True)
    block(FD + "pile_of_books", 3.05, f + 1.02, 9.4, "starboard", solid=False)
    custom("sea_chest", solid=(-3.85, -3.3, f, f + 0.6, 4.25, 5.15), name="common_chest_0", p=(-3.55, f, 4.7), facing="port", w=0.9, d=0.55)
    # a side table for cards in the starboard aft corner, its stools
    at(FU + "spruce_square_table", -2.9, f, 2.0, "stern")
    block(FU + "chess_board", -2.9, f + 1.0, 2.0, "stern", solid=False, scale=0.8)
    chair(FU + "spruce_stool", -2.9, f, 2.95, "stern", -2.0, 3.0)
    chair(FU + "spruce_stool", -1.95, f, 2.0, "stern", -1.95, 2.9)
    # the portraits on the aft bulkhead, either side of the door
    painting("common_portrait_a", "bust", (-2.6, f + 1.55, 1.0), (0, 0, 1), 0.9, 0.9)
    painting("common_portrait_b", "burning_skull", (2.9, f + 1.75, 1.0), (0, 0, 1), 0.8, 0.8)
    painting("common_portrait_c", "sea", (-3.0, f + 1.6, 10.6), (0.6, 0, -0.8), 0.9, 0.45)
    wall_lantern("common_wall_lantern_0", -1, f + 2.0, 6.6)
    wall_lantern("common_wall_lantern_1", 1, f + 2.0, 6.6)
    wall_lantern("common_wall_lantern_2", -1, f + 2.0, 2.6)
    frame_room("common", 1.0, 13.0, f, CEIL_LO, zs=[1.6, 3.6, 5.6, 7.6, 9.6, 11.6])


def captain():
    """Cabine du capitaine (reference panel 3): the office under the quarterdeck (the captain's desk and
    throne, the chart table with its instruments, chests under it, bookshelves, a cuckoo clock, a rug,
    paintings) and the bedroom aft (the big bed under a dark red blanket, a night stand and its lamp, a
    wardrobe, a dresser, a table with a chart and a lantern, a sea chest at the foot of the bed, a globe,
    a coat hanger, a red rug, lanterns)."""
    f = M0
    # ---- office (z -12.5 .. -8)
    # bookshelves on the fore bulkhead either side of the door
    for x in (-2.25, -3.25, 2.25, 3.25):
        at(FD + "tall_bookshelf", x, f, -8.0 - 0.43, "stern")
    # the captain's desk (starboard), its plain back to the door, the knee-hole on his side, his throne
    dx = -2.59                          # (a little smaller: the hull side leans in above it)
    at(FD + "desk", dx, f, -10.6, "stern", scale=0.94)
    at(FU + "dark_oak_chair", dx, f, -11.65, "bow")
    seat(dx, f + 0.45, -11.6, -1.5, f + 0.02, -11.7)
    block(FD + "kerosene_lantern", dx - 0.95, f + 0.96, -10.5, "stern", solid=False)
    block(FD + "cigar_box", dx + 0.85, f + 0.96, -10.55, "bow", solid=False, scale=0.8)
    block(FU + "book_pile", dx - 0.5, f + 0.96, -10.7, "bow", solid=False, scale=0.7)
    custom("chart_sheet", name="captain_desk_chart", p=(dx + 0.15, f + 0.96, -10.55), yaw=0.15, w=0.7, l=0.5)
    custom("inkwell", name="captain_inkwell", p=(dx + 0.55, f + 0.96, -10.85))
    # the chart table (port), with its instruments, chests under it
    for z in (-10.0, -11.0):             # a Farmhouse dining table of two end pieces (legs at its ends only)
        at(FD + "dining_table_side", 3.35, f, z, "port" if z > -10.5 else "starboard")
    custom("chart_sheet", name="captain_chart", p=(3.3, f + 1.0, -10.5), yaw=-0.12, w=0.85, l=1.3)
    custom("compass", name="captain_compass", p=(3.55, f + 1.0, -10.0))
    custom("sextant", name="captain_sextant", p=(3.1, f + 1.0, -11.15), yaw=0.6)
    custom("dividers", name="captain_dividers", p=(3.0, f + 1.01, -10.4), yaw=0.4)
    custom("map_roll", name="captain_map_roll", p=(3.65, f + 1.0, -11.25), yaw=0.2, l=0.55)
    block(FD + "kerosene_lantern", 3.6, f + 1.0, -9.7, "stern", solid=False)
    custom("sea_chest", solid=None, name="captain_chest_0", p=(3.4, f, -10.0), facing="starboard", w=0.8, d=0.55, h=0.55)
    custom("sea_chest", solid=None, name="captain_chest_1", p=(3.4, f, -11.0), facing="starboard", w=0.8, d=0.55, h=0.55, region="in_chest_lid")
    chair(FU + "spruce_chair", 2.35, f, -10.5, "port", 1.5, -10.0)
    # the windows of the castle's sides, seen from inside
    for side in (-1, 1):
        for zc in (-11.2, -12.6, -14.0, -15.4, -16.8):
            w = wall_x(f + 1.1, zc, side)
            custom("window_in", name="captain_window_%d_%d" % (side > 0, int(-zc * 10)), center=(w - side * 0.01, f + 1.1, zc),
                   normal=(-side, 0, 0), w=0.8, h=1.05)
    custom("rug", name="captain_office_rug", p=(0.0, f, -10.25), w=2.2, l=3.4)
    painting("captain_office_painting", "wanderer", (-1.75, f + 1.55, -12.5), (0, 0, 1), 0.6, 1.1)
    at(FD + "cuckoo_clock", 1.75, f + 1.35, -12.4, "bow", solid=False)
    hanging(0.0, CEIL_M, -9.4, drop=0.05)
    hanging(0.0, CEIL_M, -11.4, drop=0.05)
    frame_room("office", -12.5, -8.0, f, CEIL_M, zs=[-12.3, -8.2], beams=True)
    # ---- bedroom (z -19.8 .. -13)
    bed_x, bed_z = 1.85, -18.45
    i = at(FD + "double_bed", bed_x, f, bed_z, "bow")
    b = BLOCKS[i]
    custom("bed_blanket", name="captain_blanket", x=b["x"], y=b["y"], z=b["z"], yaw_deg=b["yaw"])
    at(FD + "night_stand", 0.35, f, -19.2, "bow")
    block(FD + "kerosene_lantern", 0.35, f + 0.63, -19.2, "stern", solid=False)
    custom("sea_chest", solid=(1.35, 2.45, f, f + 0.6, -17.35, -16.75), name="captain_bed_chest", p=(1.9, f, -17.05), facing="bow", w=1.0,
           d=0.55)
    # the writing table with a chart and a lantern (reference: by the bed)
    at(FD + "dining_table_side", 3.0, f, -15.6, "starboard")
    at(FD + "dining_table_side", 3.0, f, -14.6, "port")
    custom("chart_sheet", name="captain_bed_chart", p=(3.0, f + 1.0, -15.2), yaw=0.25, w=0.8, l=0.6)
    for k, z in enumerate((-15.6, -14.6)):
        custom("sea_chest", name="captain_table_chest_%d" % k, p=(3.2, f, z), facing="starboard", w=0.6, d=0.5, h=0.55,
               region="in_chest" if k else "in_chest_lid")
    block(FD + "kerosene_lantern", 3.25, f + 1.0, -14.45, "stern", solid=False)
    block(FD + "pile_of_books", 2.75, f + 1.0, -15.85, "starboard", solid=False)
    custom("hourglass", name="captain_hourglass", p=(3.3, f + 1.0, -15.75))
    chair(FD + "dining_chair", 2.05, f, -15.1, "port", 1.2, -14.4)
    # starboard: the wardrobe, the dresser, a bookshelf, the globe
    against(FD + "wardrobe", -1, f, -14.4)
    against(FD + "dresser", -1, f, -16.0)
    block(FD + "pile_of_books", -3.1, f + 1.02, -15.85, "port", solid=False)
    against(FD + "tall_bookshelf", -1, f, -17.6)
    against(FD + "tall_bookshelf", -1, f, -18.6)
    custom("globe", solid=(-2.05, -1.25, f, f + 1.4, -19.5, -18.8), name="captain_globe", p=(-1.65, f, -19.15))
    custom("rug", name="captain_bed_rug", p=(-0.1, f, -16.1), w=2.4, l=3.2)
    # the stern windows from inside
    for k, x in enumerate((-2.4, -1.2, 1.2, 2.4)):
        custom("window_in", name="captain_stern_window_%d" % k, center=(x, 0.7 + 0.575, STERN_WALL + 0.01), normal=(0, 0, 1), w=0.75,
               h=1.1)
    painting("captain_bed_painting", "skull_and_roses", (-2.5, f + 1.5, -13.0), (0, 0, -1), 0.9, 0.9)
    painting("captain_bed_painting_b", "sea", (2.6, f + 1.55, -13.0), (0, 0, -1), 1.2, 0.6)
    hanging(0.0, CEIL_M, -15.0, drop=0.05)
    hanging(0.5, CEIL_M, -17.8, drop=0.05)
    wall_lantern("captain_bed_lantern_0", -1, f + 1.95, -15.2)
    wall_lantern("captain_bed_lantern_1", 1, f + 1.95, -17.4)
    wall_lantern("captain_office_lantern", -1, f + 1.95, -9.4)
    frame_room("bedroom", -19.8, -13.0, f, CEIL_M, zs=[-13.2, -16.6], beams=True)


def chart_room():
    """Salle des cartes (under the poop): the chart table with charts and instruments, bookshelves of logs
    and charts, a telescope at the stern windows, rolled charts in a basket, a lantern."""
    f = CASTLE
    for x in (-0.5, 0.5):                # a Farmhouse dining table of two end pieces (legs at its ends only)
        block(FD + "dining_table_side", x, f, -17.6, "stern" if x > 0 else "bow")
    custom("chart_sheet", name="chart_table_chart", p=(0.0, f + 1.0, -17.6), yaw=0.05, w=1.5, l=0.85)
    custom("compass", name="chart_compass", p=(0.6, f + 1.0, -17.35))
    custom("dividers", name="chart_dividers", p=(-0.3, f + 1.01, -17.5), yaw=1.1)
    custom("sextant", name="chart_sextant", p=(-0.7, f + 1.0, -17.85), yaw=-0.4)
    block(FD + "kerosene_lantern", 0.75, f + 1.0, -17.9, "stern", solid=False)
    chair(FU + "spruce_stool", -0.5, f, -16.6, "stern", -1.4, -16.3)
    chair(FU + "spruce_stool", 0.5, f, -16.6, "stern", 1.4, -16.3)
    for side in (-1, 1):
        for z in (-16.5, -17.5):
            against(FD + "tall_bookshelf", side, f, z)
    custom("telescope", solid=(1.4, 2.2, f, f + 1.3, -19.5, -18.8), name="chart_telescope", p=(1.8, f, -19.15), facing="stern")
    block(FR + "wooden_basket", -1.9, f, -19.1, "stern", solid=True, scale=0.75)
    for k, (dx, dz, yw) in enumerate(((0.0, 0.0, 0.3), (0.12, 0.1, 1.2), (-0.1, 0.12, 2.0))):
        custom("map_roll", name="chart_roll_%d" % k, p=(-1.9 + dx, f + 0.75, -19.1 + dz), yaw=yw, l=0.5)
    for k, x in enumerate((-2.25, 2.25)):
        custom("wall_map", name="chart_wall_map_%d" % k, center=(x, f + 1.3, ls.POOP_Z - 0.5), normal=(0, 0, -1), w=1.2, h=0.8)
    for k, x in enumerate((-1.6, 0.0, 1.6)):
        custom("window_in", name="chart_stern_window_%d" % k, center=(x, 3.6 + 0.5, STERN_WALL + 0.01), normal=(0, 0, 1), w=0.7, h=1.0)
    hanging(0.0, CEIL_C, -17.6, drop=0.0)


def bosun_store():
    """Magasin du maître d'équipage (under the forecastle): crates, barrels, sacks, coils of rope, the
    carpenter's bench and its tools, a lantern."""
    f = M0
    for z in (10.25, 11.25):
        against(FU + "spruce_crate", -1, f, z)
    against(FU + "dark_oak_crate", -1, f + 1.0, 10.25, solid=True)
    against(FR + "potato_crate", -1, f, 12.4)
    against(FR + "rice_bag", -1, f + 1.0, 11.25)
    against(FD + "workbench", 1, f, 11.0)
    block(FD + "kerosene_lantern", 2.95, f + 1.25, 10.4, "stern", solid=False)
    w = wall_x(f + 1.6, 11.0, 1)
    at(FD + "tool_board", w - 0.07, f + 1.25, 11.0, "starboard", solid=False)
    custom("barrel", solid=(1.25, 2.05, f, f + 1.0, 12.1, 12.9), name="bosun_barrel_0", p=(1.65, f, 12.5))
    custom("barrel", solid=(-2.15, -1.35, f, f + 1.0, 13.25, 14.05), name="bosun_barrel_1", p=(-1.75, f, 13.65))
    custom("rope_coil", name="bosun_rope_0", p=(0.6, f, 14.3), r=0.45)
    custom("rope_coil", name="bosun_rope_1", p=(-0.45, f, 15.4), r=0.36)
    # the forward half (reference: cale / stockage): shelves of jars and bottles on both walls, crates and
    # barrels in the corners of the bow, a sea chest under the tool board on the forward bulkhead
    for side in (-1, 1):
        z = 14.0
        w = wall_min(f, CEIL_M, z, side)
        custom("jar_shelf", solid=(min(w, w - side * 0.36), max(w, w - side * 0.36), f, f + 1.9, z - 0.5, z + 0.5),
               name="bosun_jars_%d" % (side > 0), p=(w - side * 0.02, f, z), normal=(-side, 0, 0), w=1.0, h=1.9, rows=4)
    c = BLOCKS[against(FU + "dark_oak_crate", -1, f, 15.0, facing="port", scale=0.8)]
    at(FU + "spruce_crate", c["x"] + 0.02, f + 0.8, 15.0, "stern", scale=0.6)
    for k, (x, z, r) in enumerate(((1.55, 15.0, 0.34), (1.0, 15.7, 0.3))):
        custom("barrel", solid=(x - r, x + r, f, f + 0.95, z - r, z + r), name="bosun_barrel_%d" % (k + 2), p=(x, f, z), r=r)
    custom("sea_chest", solid=(-0.45, 0.45, f, f + 0.6, 15.95, 16.45), name="bosun_chest", p=(0.0, f, 16.2), facing="stern", w=0.9, d=0.5)
    at(FD + "tool_board", 0.0, f + 1.2, 16.44, "stern", solid=False)
    custom("sack", name="bosun_sack_0", p=(1.6, f, 13.7), yaw=0.4)
    custom("sack", name="bosun_sack_1", p=(1.9, f, 13.1), yaw=-0.3, s=0.9)
    hanging(0.0, CEIL_M, 12.0, drop=0.05)
    frame_room("bosun", 9.5, 16.0, f, CEIL_M, zs=[10.0, 13.0], beams=True)


def coursive():
    """Coursive (reference panel 5): a long corridor with a red runner, lanterns on brackets along both
    walls, its timber frame, a narrow console with a lantern, a small crate, framed pictures."""
    f = LO
    custom("rug", name="coursive_runner_a", p=(0.0, f, -2.45), w=1.25, l=5.7, region="in_runner")
    custom("rug", name="coursive_runner_b", p=(0.0, f, -7.75), w=1.25, l=2.1, region="in_runner")
    for k, (side, z) in enumerate(((-1, -1.0), (1, -1.9), (-1, -6.8), (1, -7.6))):
        wall_lantern("coursive_lantern_%d" % k, side, f + 2.05, z)
    at(FD + "night_stand", -0.68, f, -2.2, "port", solid=True)
    block(FD + "kerosene_lantern", -0.75, f + 0.63, -2.25, "stern", solid=False)
    at(FU + "spruce_crate", 0.72, f, -6.95, "stern", scale=0.55)
    painting("coursive_painting_a", "wanderer", (1.0, f + 1.4, -0.7), (-1, 0, 0), 0.45, 0.9)
    painting("coursive_painting_b", "kebab", (-1.0, f + 1.45, -7.9), (1, 0, 0), 0.6, 0.6)
    for z in (-3.0, -5.7, -8.4):
        hanging(0.0, CEIL_LO, z, drop=-0.2)
    frame_room("coursive", -9.0, 0.5, f, CEIL_LO, zs=[0.25, -2.75, -5.25, -8.75], x_from=0.0)


def crew_room():
    """Poste d'équipage (starboard, off the coursive): bunks, sea chests, a table with stools, a guitar,
    lockers, a lantern."""
    f = LO
    xf = -2.0
    for k, (z, fc) in enumerate(((-1.15, "stern"), (-7.35, "bow"))):
        i = against(FD + "single_bed", -1, f, z, facing=fc, x_from=xf)
        b = BLOCKS[i]       # the dark red blanket over the bed's pale sheets
        custom("bed_blanket", name="crew_blanket_%d" % k, x=b["x"], y=b["y"], z=b["z"], yaw_deg=b["yaw"], xc=8.0, half=8.9)
    custom("sea_chest", solid=(-3.35, -2.5, f, f + 0.6, -2.75, -2.2), name="crew_chest_0", p=(-2.9, f, -2.45), facing="port", w=0.85, d=0.5)
    custom("sea_chest", solid=(-3.82, -2.98, f, f + 0.6, -6.35, -5.85), name="crew_chest_1", p=(-3.4, f, -6.1), facing="bow", w=0.85, d=0.5)
    t = BLOCKS[against(FU + "spruce_square_table", -1, f, -4.0, facing="stern", x_from=xf)]
    block(FD + "kerosene_lantern", t["x"] - 0.1, f + 1.0, -3.8, "stern", solid=False)
    block(FD + "red_wine_bottle", t["x"] + 0.2, f + 1.0, -4.25, "stern", solid=False)
    chair(FU + "spruce_stool", -2.75, f, -3.55, "stern", -2.1, -3.0)
    chair(FU + "spruce_stool", -2.75, f, -4.45, "stern", -2.1, -5.0)
    against(FD + "acoustic_guitar", -1, f, -5.25, x_from=xf, solid=False)
    hanging(-3.0, CEIL_LO, -4.0, drop=-0.15)
    for k, z in enumerate((-0.6, -6.6)):
        w = wall_x(f + 1.35, z, -1, xf)
        custom("porthole_in", name="crew_porthole_%d" % k, center=(w + 0.01, f + 1.35, z), normal=(1, 0, 0))


def storeroom():
    """Cambuse (port, off the coursive): the cook's stove with its pot and pan, a counter with a cutting
    board, spices and plates on the wall, crates of vegetables, sacks, a cask on tap, baskets."""
    f = LO
    xf = 2.0
    against(FR + "stove", 1, f, -1.0, x_from=xf)
    i = BLOCKS[-1]
    block(FR + "cooking_pot", i["x"], f + 1.0, i["z"], "starboard", solid=False)
    against(FD + "kitchen_counter", 1, f, -2.0, x_from=xf)
    c = BLOCKS[-1]
    block(FR + "cutting_board", c["x"], f + 1.0, c["z"], "starboard", solid=False)
    block(FR + "skillet", c["x"] - 0.05, f + 1.0, c["z"] + 0.25, "starboard", solid=False, scale=0.6)
    w = wall_x(f + 1.6, -1.5, 1, xf)
    at(FD + "kitchen_wall_shelf", w - 0.33, f + 1.35, -1.5, "starboard", solid=False)
    at(FD + "seasoning_rack", w - 0.13, f + 1.35, -2.6, "starboard", solid=False)
    against(FR + "carrot_crate", 1, f, -6.0, x_from=xf)
    against(FR + "cabbage_crate", 1, f, -7.0, x_from=xf)
    against(FR + "onion_crate", 1, f + 1.0, -6.0, x_from=xf, solid=True)
    against(FR + "rice_bag", 1, f, -8.0, x_from=xf)
    custom("cask", solid=(1.9, 2.6, f, f + 0.9, -8.25, -7.35), name="store_cask", p=(2.25, f, -7.8), facing=(0, 0, 1))
    custom("sack", name="store_sack_0", p=(3.1, f + 1.0, -7.0), yaw=0.3, s=0.8)
    at(FR + "wooden_basket", 2.0, f, -0.55, "stern", scale=0.7)
    hanging(3.0, CEIL_LO, -4.0, drop=-0.15)
    for k, z in enumerate((-0.6, -4.6)):
        w = wall_x(f + 1.35, z, 1, xf)
        custom("porthole_in", name="store_porthole_%d" % k, center=(w - 0.01, f + 1.35, z), normal=(-1, 0, 0))
    chair(FU + "spruce_stool", 2.35, f, -3.2, "stern", 2.4, -4.1)


def hold():
    """Cale / stockage (reference panel 4): a workbench with its lantern and tools, upright barrels and
    casks on racks, stacked crates and sacks, shelves of jars and bottles along the wall, chests, the
    treasure chest, posts and beams; the aisle and the ladder stay clear."""
    f = HO
    # starboard side (x < -1)
    against(FD + "workbench", -1, f, -0.9)
    block(FD + "kerosene_lantern", -2.35, f + 1.25, -0.4, "stern", solid=False)
    block(FR + "cutting_board", -2.4, f + 1.25, -1.35, "port", solid=False, scale=0.7)
    w = wall_x(f + 1.6, -0.9, -1)
    at(FD + "tool_board", w + 0.07, f + 1.2, -0.9, "port", solid=False)
    for k, z in enumerate((-3.0, -3.85)):
        x = wall_min(f, f + 0.95, z, -1) + 0.42
        custom("barrel", solid=(x - 0.4, x + 0.4, f, f + 0.95, z - 0.4, z + 0.4), name="hold_barrel_%d" % k, p=(x, f, z))
    x = wall_min(f, f + 0.95, -2.15, -1) + 0.36
    custom("barrel", solid=(x - 0.34, x + 0.34, f, f + 0.95, -2.49, -1.81), name="hold_barrel_2", p=(x, f, -2.15), r=0.32)
    # casks lying on their cradles, apart, their lids and taps turned to the aisle
    for k, z in enumerate((1.45, 2.5, 3.55)):
        x = max(wall_min(f, f + 0.9, zz, -1) for zz in (z - 0.35, z + 0.35)) + 0.47
        custom("cask", solid=(x - 0.45, x + 0.45, f, f + 0.9, z - 0.38, z + 0.38), name="hold_cask_%d" % k, p=(x, f, z), facing=(1, 0, 0),
               tap=k != 1)
    c = BLOCKS[against(FU + "spruce_crate", -1, f, 4.6, facing="stern")]
    against(FU + "spruce_crate", -1, f, 5.65, facing="stern", scale=0.7)     # (the bilge rises forward)
    at(FU + "dark_oak_crate", c["x"] - 0.05, f + 1.0, 4.6, "stern", scale=0.85)
    against(FR + "rice_bag", -1, f, -7.9, facing="stern")
    against(FR + "straw_bale", -1, f, -6.9, facing="stern")
    custom("sack", name="hold_sack_0", p=(-1.6, f, -8.4), yaw=0.5)
    # port side (x > 1)
    for k, z in enumerate((0.4, 1.4)):
        w = wall_min(f, CEIL_H, z, 1)
        custom("jar_shelf", solid=(w - 0.4, w, f, f + 1.95, z - 0.5, z + 0.5), name="hold_jars_%d" % k, p=(w - 0.02, f, z), normal=(-1, 0, 0),
               w=1.0, h=1.95, rows=4)
    for k, (z, bid, sc) in enumerate(((3.2, FR + "potato_crate", 1.0), (4.2, FR + "carrot_crate", 1.0), (5.3, FR + "beetroot_crate", 0.7))):
        against(bid, 1, f, z, facing="stern", scale=sc)
    c = BLOCKS[-3]
    at(FR + "cabbage_crate", c["x"] - 0.05, f + 1.0, 3.7, "stern", scale=0.9)
    at(MB + "dwemer_chest", 2.0, f, -7.9, "starboard")
    custom("sea_chest", solid=(1.4, 2.5, f, f + 0.6, -6.85, -6.25), name="hold_chest_0", p=(1.95, f, -6.55), facing="starboard", w=1.0, d=0.55)
    custom("sea_chest", solid=(1.4, 2.5, f, f + 0.6, -5.85, -5.25), name="hold_chest_1", p=(1.95, f, -5.55), facing="starboard", w=1.0, d=0.55,
           region="in_chest_lid")
    for k, z in enumerate((-2.2, -3.2)):
        custom("barrel", solid=(1.4, 2.2, f, f + 0.95, z - 0.4, z + 0.4), name="hold_barrel_p%d" % k, p=(1.8, f, z))
    at(IC + "storage_vase", 2.12, f, -4.2, "stern", scale=0.85)
    block(FD + "kerosene_lantern", 1.8, f + 0.95, -2.2, "stern", solid=False)
    # lanterns on the posts, the frame
    wall_lantern("hold_lantern_0", -1, f + 1.75, -5.6)
    wall_lantern("hold_lantern_1", 1, f + 1.75, 2.4)
    wall_lantern("hold_lantern_2", -1, f + 1.75, 4.1)
    wall_lantern("hold_lantern_3", 1, f + 1.75, -4.3)
    frame_room("hold", -9.0, 6.5, f, CEIL_H, zs=[-8.75, -4.6, -1.6, 2.0, 6.0])


def engine_room():
    """Salle des machines (reference panel 6): the boiler is built by generate_leviathan.boiler (its
    grid cells by leviathan_interior.BOILER); around it: the pressure tanks, the pipes from the boiler
    to the walls with their valves and gauges, bronze conduits and gearboxes of the dwarven mod along the
    walls, gauge boards, the levers, crates and a coal heap, the engineer's workbench, the railings of
    the landing, of the stair and of the catwalk along the starboard wall, warm lanterns."""
    f = EO
    up = LO     # landing / catwalk level
    # crates on the landing (the reference's foreground), on its port side by the barrel: the starboard side
    # stays clear, the way onto the catwalk; the levers by its rail
    at(FU + "dark_oak_crate", 3.05, up, -10.6, "stern", scale=0.8)
    at(FU + "spruce_crate", 3.05, up + 0.8, -10.6, "stern", scale=0.6)
    custom("lever_bank", solid=(-2.05, -1.25, up, up + 0.9, -11.35, -10.85), name="engine_levers", p=(-1.65, up, -11.1), normal=(0, 0, 1))
    custom("barrel", solid=(2.65, 3.35, up, up + 0.9, -10.15, -9.55), name="engine_landing_barrel", p=(3.0, up, -9.85), r=0.32, h=0.85)
    # the railings: the landing, the stair's open side, the catwalk
    custom("railing", name="engine_landing_rail", pts=[(-2.25, up, -11.25), (0.95, up, -11.25)], h=1.0)
    custom("railing", name="engine_landing_rail_p", pts=[(2.55, up, -11.25), (3.7, up, -11.25)], h=1.0)
    custom("railing", name="engine_stair_rail", pts=[(1.05, up, -11.35), (1.05, f, -13.4)], h=1.0, step=0.8)
    custom("railing", name="engine_catwalk_rail", pts=[(-2.25, li.CATWALK_Y, -11.25), (-2.25, li.CATWALK_Y, -16.3)], h=1.0)
    # steam mains under the ceiling along both walls, bronze gearboxes of the dwarven mod on them
    for side in (-1, 1):
        x = side * 3.45
        custom("pipe", name="engine_main_%d" % (side > 0), pts=[(x, -0.85, -16.3), (x, -0.85, -9.7)], d=0.26)
        custom("pipe", name="engine_main_b_%d" % (side > 0), pts=[(x - side * 0.35, -0.75, -16.3), (x - side * 0.35, -0.75, -9.7)], d=0.18,
               region="in_brass", flange="in_iron")
        for z in (-15.2, -11.9):
            block(MB + "dwemer_metal_pipe_gear", x - side * 0.05, -1.25, z, "stern", solid=False, scale=0.5)
        block(MB + "dwemer_metal_pipe", x - side * 0.05, -1.22, -13.55, "stern", solid=False, scale=0.45)
    # gearboxes of bronze on the starboard catwalk wall and by the stair
    against(MB + "dwemer_metal_block", -1, li.CATWALK_Y, -15.7, solid=True, scale=0.8, x_from=-2.6)
    against(MB + "dwemer_metal_pipe_gear", -1, li.CATWALK_Y + 0.8, -15.7, solid=False, scale=0.6, x_from=-2.6)
    # the engineer's corner at the foot of the stair (port): workbench, tool board, a locker
    against(FD + "workbench", 1, f, -15.25, x_from=1.5)
    block(FD + "kerosene_lantern", 2.6, f + 1.25, -15.7, "stern", solid=False)
    w = wall_x(f + 1.9, -15.25, 1, 1.5)
    at(FD + "tool_board", w - 0.07, f + 1.45, -15.25, "starboard", solid=False)
    # starboard floor: the pressure tank, the coal heap by the firebox, a coal crate
    custom("pressure_tank", solid=(-2.85, -2.05, f, f + 1.95, -15.9, -15.1), name="engine_tank_0", p=(-2.45, f, -15.5), r=0.4, h=1.6)
    custom("coal_heap", name="engine_coal", p=(-2.1, f, -12.0), r=0.55)
    at(FU + "dark_oak_crate", -2.45, f, -10.6, "stern")
    # gauge boards and valves
    custom("gauge_board", name="engine_board_stbd", center=(wall_x(li.CATWALK_Y + 1.4, -13.5, -1) + 0.01, li.CATWALK_Y + 1.4, -13.5),
           normal=(1, 0, 0), w=1.3, h=0.8)
    custom("gauge_board", name="engine_board_port", center=(wall_x(f + 3.3, -14.6, 1) - 0.01, f + 3.3, -14.6), normal=(-1, 0, 0), w=1.1,
           h=0.75, gauges=((-0.25, 0.1, 0.15, True), (0.25, 0.1, 0.15, False), (0.0, -0.2, 0.1, False)))
    # vertical pipes down the walls to valves, a second tank under the landing
    for k, (side, z) in enumerate(((1, -14.9), (-1, -12.4))):
        x = wall_x(f + 2.0, z, side) - side * 0.2
        custom("pipe", name="engine_drop_%d" % k, pts=[(x, -0.95, z), (x, f + 0.3, z)], d=0.2)
        custom("valve", name="engine_drop_valve_%d" % k, p=(x, f + 1.3, z), normal=(-side, 0, 0), r=0.18)
        custom("gauge", name="engine_drop_gauge_%d" % k, p=(x - side * 0.12, f + 1.85, z), normal=(-side, 0, 0), r=0.12, red=k == 0)
    custom("pressure_tank", name="engine_tank_1", p=(1.95, f, -10.3), r=0.36, h=1.0)
    custom("coal_heap", name="engine_coal_1", p=(-1.6, f, -10.4), r=0.5)
    # warm lanterns
    hanging(-2.0, CEIL_LO, -13.0, drop=-0.1)
    hanging(-2.0, CEIL_LO, -15.6, drop=-0.1)
    hanging(2.2, CEIL_LO, -10.3, drop=0.0)
    wall_lantern("engine_lantern_port", 1, f + 2.6, -13.0)
    wall_lantern("engine_lantern_aft", 1, f + 2.2, -16.0)
    wall_lantern("engine_lantern_stbd", -1, f + 1.9, -14.4)
    frame_room("engine", -16.5, -9.5, f, CEIL_LO, zs=[-16.3, -9.7], beams=False)


def main_deck():
    """Pont principal (reference panel 1): crates and barrels along the bulwarks, the navigator's table
    with its instruments, coils of rope, lanterns on posts, barrels on the castles."""
    f = M0
    # starboard bulwark, forward of the bench
    at(FU + "spruce_crate", -3.85, f, 1.2, "stern")
    at(FU + "dark_oak_crate", -3.85, f, 2.2, "stern")
    at(FU + "spruce_crate", -3.85, f + 1.0, 1.7, "stern", scale=0.8)
    custom("barrel", solid=(-4.25, -3.45, f, f + 0.95, 3.0, 3.8), name="deck_barrel_0", p=(-3.85, f, 3.4))
    custom("barrel", solid=(-3.45, -2.65, f, f + 0.95, 3.55, 4.35), name="deck_barrel_1", p=(-3.05, f, 3.95), r=0.34)
    # the navigator's table by the starboard bulwark aft (reference: a small table with instruments)
    at(FU + "dark_oak_square_table", -3.85, f, -3.1, "stern", scale=0.8)
    custom("compass", name="deck_compass", p=(-3.95, f + 0.8, -2.95))
    custom("sextant", name="deck_sextant", p=(-3.7, f + 0.8, -3.25), yaw=0.9)
    custom("map_roll", name="deck_map_roll", p=(-4.0, f + 0.8, -3.3), yaw=1.4, l=0.4)
    # coils of rope, a barrel on the port bulwark forward
    custom("rope_coil", name="deck_rope_0", p=(-1.6, f, 5.6), r=0.4)
    custom("rope_coil", name="deck_rope_1", p=(3.85, f, 0.7), r=0.36)
    custom("barrel", solid=(3.6, 4.4, f, f + 0.95, 4.9, 5.7), name="deck_barrel_2", p=(4.0, f, 5.3), r=0.34)
    # lanterns on posts at the foot of the castles
    for k, (x, z) in enumerate(((-1.6, -7.2), (1.6, -7.2), (-1.6, 8.7), (1.6, 8.7))):
        custom("lantern_post", name="deck_lantern_post_%d" % k, p=(x, f, z), arm=(0, 0, 1 if z < 0 else -1))
        block(FD + "chained_kerosene_lantern", x, f + 2.05 - 1.0 + 0.02, z + (0.38 if z < 0 else -0.38), "stern", solid=False)
    # quarterdeck: barrels by the starboard rail, a chest
    q = CASTLE
    custom("barrel", solid=(-3.75, -2.95, q, q + 0.95, -9.5, -8.7), name="qd_barrel_0", p=(-3.35, q, -9.1))
    custom("barrel", solid=(-3.75, -2.95, q, q + 0.95, -10.4, -9.6), name="qd_barrel_1", p=(-3.35, q, -10.0), r=0.34)
    custom("sea_chest", solid=(-3.85, -3.25, q, q + 0.6, -12.6, -11.6), name="qd_chest", p=(-3.55, q, -12.1), facing="port", w=0.95, d=0.55)
    # forecastle: a coil of rope, crates
    fc = ls.FORECASTLE_Y
    custom("rope_coil", name="fc_rope_0", p=(1.4, fc, 13.0), r=0.42)
    at(FU + "spruce_crate", -2.3, fc, 12.0, "stern")
    custom("barrel", solid=(-2.75, -1.95, fc, fc + 0.95, 13.0, 13.8), name="fc_barrel_0", p=(-2.35, fc, 13.4), r=0.35)


def deck_benches():
    """Benches along the bulwarks of the main deck (phase 1), now the mods' benches."""
    for x in (-3.95, 3.95):
        side = 1 if x > 0 else -1
        for z in (-2.0, -1.0):
            chair(FU + "dark_oak_bench", x, M0, z, "stern", x - side * 0.8, z)


def build():
    BLOCKS.clear()
    SEATS.clear()
    CUSTOM.clear()
    PAINTINGS.clear()
    SWITCHES.clear()
    common_room()
    captain()
    chart_room()
    bosun_store()
    coursive()
    crew_room()
    storeroom()
    hold()
    engine_room()
    main_deck()
    deck_benches()
    return BLOCKS, SEATS


def footprint(b):
    return _footprint(b["block"], b["x"], b["y"], b["z"], b["yaw"], b["scale"])


def apply_to_grid(g):
    """Solid cells for the footprints of the solid furniture."""
    for builder, kwargs, solid in CUSTOM:
        if solid is not None:
            x0, x1, y0, y1, z0, z1 = solid
            g.set(li.FURNITURE, x0 + 0.05, x1 - 0.05, y0 + 0.01, y1, z0 + 0.05, z1 - 0.05, where=(g.k == li.DRY) | (g.k == li.OUT))
    for b in BLOCKS:
        if not b["solid"]:
            continue
        x0, x1, y0, y1, z0, z1 = footprint(b)
        # from the floor under it to its top (a table top is solid down to the floor: no crawling under it)
        g.set(li.FURNITURE, x0 + 0.05, x1 - 0.05, b["y"] + 0.01, y1, z0 + 0.05, z1 - 0.05, where=(g.k == li.DRY) | (g.k == li.OUT))


def write(path):
    data = {"blocks": [], "seats": [{k: round(v, 4) for k, v in s.items()} for s in SEATS],
            "paintings": [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in q.items()} for q in PAINTINGS], "switches": SWITCHES}
    for i, b in enumerate(BLOCKS):
        data["blocks"].append({"block": b["block"], "x": round(b["x"], 4), "y": round(b["y"], 4), "z": round(b["z"], 4),
                               "yaw": b["yaw"], "scale": b["scale"], "fallback": "fallback_%d" % i})
    with open(path, "w") as f:
        json.dump(data, f, indent=1)


DECOR_PATH = "src/main/resources/assets/medievalships/interiors/sky_leviathan_decor.json"
