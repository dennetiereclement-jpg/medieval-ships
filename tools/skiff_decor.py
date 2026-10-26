"""Furniture of the Rustic Skyskiff: blocks of the user's decoration mods (drawn by the skiff where they stand,
moving with it; never placed in the world), the few pieces made for it (tools/generate_skiff.py draws them) and
the seats, room by room after the interior views of the reference sheet (the fore deck, the cabin's front and the
pilot post, the bedroom, the storage hold).

  src/main/resources/assets/medievalships/interiors/rustic_skiff_decor.json

Same format and same rules as the Nautilus, the Old Corsair and the Sky Leviathan (tools/leviathan_decor.py):
each mod block is given by the centre of its bottom face (ship-local) and the direction its front faces; its
footprint becomes solid cells of the interior grid (chairs, benches and small things on tables are not solid); a
block whose mod is missing on a client is replaced by its stand-in, a box of the same size in the model (bone
"fallback_<i>"). Modest, rustic furniture: old wood, barrels, crates, lanterns, worn cloth.

Mods used: farmhouse_decorations (Farmhouse Decorations), furnish (Furnish), farmersdelight (Farmer's Delight),
landsoficaria (Lands of Icaria). Block measurements: the default state's model bounds (x east, z south, front
north), from the mods' files (the same tables as the Corsair and the Leviathan, plus a few blocks).
"""
import json
import math

import numpy as np

import corsair_decor as cd
import leviathan_decor as ld
import nautilus_decor as nd
import skiff_interior as si
import skiff_shape as ss

FACING = nd.FACING   # stern 0, starboard 90, bow 180, port 270 (the block's north = its front)
FD = "farmhouse_decorations:"
FU = "furnish:"
FR = "farmersdelight:"
IC = "landsoficaria:"

BOUNDS = dict(cd.BOUNDS)
BOUNDS.update(ld.BOUNDS)
BOUNDS.update({
    FU + "spruce_bench": (0.0, 1.0, 0.0, 0.562, 0.25, 0.75),
    FU + "spruce_cabinet": (0.0, 1.0, 0.0, 1.0, -0.062, 1.0),
    FU + "spruce_bedside_table": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FD + "rug_3x_3": (-0.625, 1.625, 0.0, 0.031, -0.625, 1.625),
    FD + "kitchen_wall_shelf": (0.0, 1.0, 0.0, 1.0, 0.375, 1.0),
})
SEAT_H = dict(ld.SEAT_H)
SEAT_H[FU + "spruce_bench"] = 0.562

# look of the stand-in (fallback box) when the mod is missing (regions of tools/skiff_texture.py); lanterns glow
FALLBACK_REGION = {
    FD + "single_bed": "bedding", FD + "tall_bookshelf": "books", FD + "wall_shelf": "books", FD + "kitchen_wall_shelf": "light_wood",
    FD + "kerosene_lantern": "lantern", FD + "chained_kerosene_lantern": "lantern", FD + "wine_bottle": "glass", FD + "red_wine_bottle": "red_paint",
    FD + "wine_glass": "glass", FD + "pile_of_books": "books", FU + "book_pile": "books", FD + "tool_board": "dark_wood", FU + "plate": "linen",
    FR + "rice_bag": "sack", FR + "canvas_rug": "cloth", FD + "rug_3x_3": "carpet", FU + "spruce_crate": "light_wood", FU + "dark_oak_crate": "dark_wood",
    IC + "cypress_barrel": "wood", IC + "loaded_cypress_barrel": "wood", IC + "storage_vase": "red_paint", IC + "brown_storage_vase": "wood",
    FU + "small_locker": "iron", FD + "workbench": "dark_wood", FD + "dresser": "dark_wood", FU + "spruce_table": "wood", FU + "spruce_chair": "wood",
    FU + "spruce_bench": "wood", FU + "spruce_cabinet": "dark_wood", FU + "spruce_shelf": "wood", FR + "wooden_basket": "light_wood",
    FD + "night_stand": "dark_wood", FD + "coat_hanger": "dark_wood",
}
GLOWING = {FD + "kerosene_lantern", FD + "chained_kerosene_lantern"}

BLOCKS = []    # dicts: block, x, y, z, yaw, solid, scale, glow
SEATS = []     # dicts: x, y, z, dx, dy, dz
CUSTOM = []    # furniture drawn by generate_skiff: (builder name, kwargs, solid box or None)

M0, PY, HO = si.M0, si.PY, si.HO
CEIL_C = PY - si.SLAB      # ceiling of the cabin (2.5)
CEIL_H = M0 - si.SLAB      # ceiling of the hold (-0.5)

_GRID = []


def grid():
    if not _GRID:
        _GRID.append(si.build())
    return _GRID[0]


def wall_x(y, z, side, x_from=0.0):
    """Inner face of the side wall (side +1: port, -1: starboard) at height y and z, scanning outwards from x_from."""
    g = grid()
    j = int(math.floor((y - si.Y0) / si.CELL))
    l = int(math.floor((z - si.Z0) / si.CELL))
    i = int(math.floor((x_from - si.X0) / si.CELL))
    while 0 <= i < g.nx:
        if g.k[i, j, l] in (si.SOLID, si.OUT, si.WINDOW):
            return si.X0 + (i if side > 0 else i + 1) * si.CELL
        i += side
    return None


def wall_min(y0, y1, z, side, x_from=0.0):
    xs = [wall_x(y, z, side, x_from) for y in [y0 + 0.1 + 0.5 * k for k in range(int((y1 - y0) / 0.5) + 1)] if y < y1]
    xs = [x for x in xs if x is not None]
    return min(xs, key=abs) if xs else None


def to_ship(x, y, z, yaw, px, py, pz, scale=1.0):
    qx, qz = (px - 0.5) * scale, (pz - 0.5) * scale
    a = math.radians(yaw)
    c, s = math.cos(a), math.sin(a)
    return x + qx * c + qz * s, y + py * scale, z - qx * s + qz * c


def footprint(bid, x, y, z, yaw, scale=1.0):
    b = BOUNDS[bid]
    pts = [to_ship(x, y, z, yaw, px, py, pz, scale) for px in (b[0], b[1]) for py in (b[2], b[3]) for pz in (b[4], b[5])]
    xs, ys, zs = zip(*pts)
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def block(bid, x, y, z, facing="stern", solid=True, scale=1.0):
    yaw = FACING[facing] if isinstance(facing, str) else float(facing)
    BLOCKS.append({"block": bid, "x": round(x, 4), "y": round(y, 4), "z": round(z, 4), "yaw": yaw, "solid": solid, "scale": scale,
                   "glow": bid in GLOWING})
    return len(BLOCKS) - 1


def at(bid, cx, y, cz, facing="stern", solid=True, scale=1.0):
    """A mod block placed by the centre (cx, cz) of its footprint."""
    yaw = FACING[facing] if isinstance(facing, str) else float(facing)
    x0, x1, _, _, z0, z1 = footprint(bid, 0.0, 0.0, 0.0, yaw, scale)
    return block(bid, cx - (x0 + x1) / 2, y, cz - (z0 + z1) / 2, facing, solid, scale)


def against(bid, side, y, z, facing=None, solid=True, scale=1.0, gap=0.02, x_from=0.0, top=None):
    """A mod block standing against a side wall (side +1: port, -1: starboard), its front turned inboard."""
    facing = facing or ("starboard" if side > 0 else "port")
    yaw = FACING[facing]
    x0, x1, y0, y1, z0, z1 = footprint(bid, 0.0, 0.0, 0.0, yaw, scale)
    h = top if top is not None else (y1 - y0)
    ws = [wall_min(y, y + h, zz, side, x_from) for zz in (z - (z1 - z0) / 2 + 0.06, z, z + (z1 - z0) / 2 - 0.06)]
    w = min([v for v in ws if v is not None], key=abs)
    cx = w - side * ((x1 - x0) / 2 + gap)
    return at(bid, cx, y, z, facing, solid, scale)


def custom(builder, solid=None, **kwargs):
    CUSTOM.append((builder, kwargs, solid))


def seat(x, y, z, dx, dy, dz):
    """A seat: sitting point (x, y = seat height, z) and where to stand up (dx, dy = floor, dz)."""
    SEATS.append({"x": x, "y": y, "z": z, "dx": dx, "dy": dy + 0.02, "dz": dz})


def chair(bid, x, floor, z, facing, dx, dz, solid=False):
    at(bid, x, floor, z, facing, solid=solid)
    seat(x, floor + SEAT_H[bid] - 0.12, z, dx, floor, dz)


def hanging(x, ceiling, z, drop=0.0):
    """A chained kerosene lantern hanging from the ceiling (its chain reaches the ceiling)."""
    block(FD + "chained_kerosene_lantern", x, ceiling - 1.0 - drop, z, "stern", solid=False)


def wall_lantern(side, y, z, arm=0.3, x_from=0.0):
    """A kerosene lantern on an iron bracket against a side wall."""
    w = wall_x(y, z, side, x_from)
    custom("bracket", name="bracket_%d" % len(CUSTOM), p=(w - side * 0.04, y, z), side=side)
    block(FD + "kerosene_lantern", w - side * arm, y + 0.12, z, "stern", solid=False)


def barrel(name, x, y, z, h=0.95, r=0.36):
    custom("barrel", solid=(x - r, x + r, y, y + h, z - r, z + r), name=name, p=(x, y, z), h=h, r=r)


def crate(name, x, y, z, s=0.8, yaw=0.0, solid=True):
    custom("crate", solid=(x - s / 2, x + s / 2, y, y + s, z - s / 2, z + s / 2) if solid else None, name=name, p=(x, y, z), s=s, yaw=yaw)


# ---------------------------------------------------------------- the rooms
def common_room():
    """The cabin's common room: a table with two chairs and a lantern over it, a cabinet against the partition, a
    barrel and a crate in the corners, a shelf of jars over the hold stair, a runner from the door to the bedroom."""
    f = M0
    at(FU + "spruce_table", -2.2, f, -5.2, "stern")
    block(FU + "plate", -2.05, f + 1.0, -5.0, "stern", solid=False, scale=0.8)
    block(FD + "red_wine_bottle", -2.5, f + 1.0, -5.45, "stern", solid=False)
    block(FD + "wine_glass", -1.95, f + 1.0, -5.45, "stern", solid=False)
    chair(FU + "spruce_chair", -2.2, f, -4.25, "stern", -1.1, -4.25)
    chair(FU + "spruce_chair", -2.2, f, -6.15, "bow", -1.1, -6.15)
    hanging(-2.2, CEIL_C, -5.2)
    at(FU + "spruce_cabinet", -2.9, f, -7.0, "bow")
    block(FD + "kerosene_lantern", -3.1, f + 1.0, -7.05, "bow", solid=False)
    block(FD + "pile_of_books", -2.7, f + 1.0, -7.0, "bow", solid=False)
    crate("common_crate", -3.05, f, -3.95, s=0.7)
    barrel("common_barrel_door", 2.95, f, -3.95, h=0.85, r=0.32)
    against(FD + "kitchen_wall_shelf", 1, f + 1.35, -5.0, solid=False)
    for k, z in enumerate((-5.3, -4.75)):
        block(IC + ("storage_vase" if k else "brown_storage_vase"), 3.05, f + 1.73, z, "starboard", solid=False, scale=0.3)
    custom("rug", name="common_runner", p=(-0.5, f, -5.5), w=0.9, l=3.8, region="carpet")
    wall_lantern(-1, f + 1.75, -6.4)


def bedroom():
    """The bedroom (reference panel 3): the bed with its red blanket under the port window, a chest at its foot, the
    tall bookcase in the aft starboard corner, the desk with open books, a chart and a lantern, its chair, a dresser by
    the door, the red rug, lanterns."""
    f = M0
    against(FD + "single_bed", 1, f, -11.35, facing="bow")
    custom("chest", solid=(2.0, 3.0, f, f + 0.65, -10.05, -9.55), name="bed_chest", p=(2.5, f, -9.8))
    against(FD + "tall_bookshelf", -1, f, -12.0)
    at(FU + "spruce_table", -2.55, f, -10.2, "port")
    custom("chart_sheet", name="desk_chart", p=(-2.5, f + 1.01, -10.05), yaw=0.2)
    block(FD + "pile_of_books", -2.75, f + 1.0, -10.55, "port", solid=False)
    block(FD + "kerosene_lantern", -2.8, f + 1.0, -9.85, "port", solid=False)
    chair(FU + "spruce_chair", -1.6, f, -10.2, "starboard", -0.7, -10.2)
    against(FD + "dresser", -1, f, -8.55, facing="port")
    block(FD + "wine_bottle", -2.95, f + 1.02, -8.4, "port", solid=False)
    block(FD + "rug_3x_3", 0.15, f, -10.6, "stern", solid=False)
    hanging(0.2, CEIL_C, -10.4)
    wall_lantern(1, f + 1.75, -8.6)
    against(FD + "wall_shelf", 1, f + 1.15, -12.1, solid=False)


def hold():
    """The storage hold (reference panel 4): a low corridor under the decks with a red runner, barrels, crates, sacks,
    lockers ("the doors on the right"), a workbench with its tool board, shelves of jars, lanterns on brackets."""
    f = HO
    for k, (z0, z1) in enumerate(((-9.9, -7.2), (-3.6, 0.9), (2.9, 4.0))):
        custom("rug", name="hold_runner_%d" % k, p=(-0.15, f, (z0 + z1) / 2), w=0.8, l=z1 - z0, region="carpet")
    # port side (the stair lands between z -6 and -7)
    against(IC + "cypress_barrel", 1, f, 3.55, facing="starboard")
    against(FD + "workbench", 1, f, -0.3, facing="starboard")
    against(FD + "tool_board", 1, f + 0.95, -0.3, facing="starboard", solid=False)
    against(FU + "spruce_crate", 1, f, -2.6)
    crate("hold_crate_top", 1.55, f + 1.0, -2.6, s=0.6, solid=False)
    barrel("hold_barrel_p1", 1.55, f, -8.1, h=0.9, r=0.34)
    against(FR + "rice_bag", 1, f, -9.6, scale=0.8)
    # starboard side
    against(FU + "small_locker", -1, f, 3.5, facing="port")
    against(FU + "spruce_crate", -1, f, 0.2)
    against(FU + "spruce_crate", -1, f, -0.85, scale=0.8)
    against(FU + "small_locker", -1, f, -2.6, facing="port")
    against(FU + "small_locker", -1, f, -3.65, facing="port")
    barrel("hold_barrel_s1", -1.55, f, -5.3, h=0.9, r=0.34)
    barrel("hold_barrel_s2", -1.6, f, -6.15, h=0.85, r=0.32)
    against(FU + "dark_oak_crate", -1, f, -8.3)
    against(FR + "rice_bag", -1, f, -9.6, scale=0.8)
    # shelves of jars along both walls, lanterns on brackets
    for side, zs in ((1, (-4.2, -9.0)), (-1, (2.3, -7.2))):
        for z in zs:
            against(FU + "spruce_shelf", side, f + 1.2, z, solid=False, x_from=0.0)
            w = wall_x(f + 1.25, z, side)
            for j, dz in enumerate((-0.25, 0.2)):
                block(IC + ("storage_vase" if j else "brown_storage_vase"), w - side * 0.32, f + 1.45, z + dz, "stern", solid=False, scale=0.28)
    for side, z in ((1, 2.0), (-1, -1.8), (1, -6.9), (-1, -9.9)):
        wall_lantern(side, f + 1.45, z, arm=0.28)


def fore_deck():
    """The open fore deck (reference panel 1): crates and a barrel by the cabin front, a coil of rope, a bench on the
    port bulwark; under the bow's lean-to the storage corner (crates, barrels, sacks, a chest), a lantern under its
    ridge."""
    f = M0
    crate("deck_crate_0", 2.75, f, -2.45, s=0.85)
    crate("deck_crate_1", 2.7, f + 0.85, -2.5, s=0.6, yaw=0.3, solid=False)
    barrel("deck_barrel_0", 2.85, f, -1.25, h=0.9, r=0.33)
    custom("coil", name="deck_coil", p=(-1.9, f, 4.6), r=0.32)
    at(FU + "spruce_bench", 3.05, f, 3.6, "starboard")
    seat(3.05, f + 0.44, 3.6, 2.0, f, 3.6)
    # the storage corner under the lean-to
    crate("bow_crate_0", -1.05, f, 8.4, s=0.8)
    crate("bow_crate_1", -1.0, f + 0.8, 8.45, s=0.55, yaw=0.4, solid=False)
    against(IC + "cypress_barrel", 1, f, 8.55, facing="starboard")
    block(FR + "rice_bag", -0.8, 0.5, 10.6, "bow", scale=0.6)
    block(FR + "rice_bag", 0.8, 0.5, 10.55, "bow", scale=0.6)
    custom("chest", solid=(-0.45, 0.45, 1.0, 1.6, 11.6, 12.1), name="bow_chest", p=(0.0, 1.0, 11.85), w=0.9, d=0.5)
    custom("coil", name="bow_coil", p=(0.9, f, 9.4), r=0.28)
    block(FD + "chained_kerosene_lantern", 0.0, 2.65, 8.4, "stern", solid=False)


def pilot_deck():
    """The pilot deck: benches along the aft balustrade and the sides, a barrel and a crate."""
    f = PY
    for x in (-1.55, 1.55):
        chair(FU + "spruce_bench", x, f, -12.55, "bow", x, -11.7)
    for side in (1, -1):
        chair(FU + "spruce_bench", side * 3.6, f, -9.6, "starboard" if side > 0 else "port", side * 2.75, -9.6)
    barrel("pilot_barrel", 3.45, f, -6.6, h=0.85, r=0.32)
    crate("pilot_crate", -3.45, f, -6.6, s=0.7)


def build():
    BLOCKS.clear()
    SEATS.clear()
    CUSTOM.clear()
    common_room()
    bedroom()
    hold()
    fore_deck()
    pilot_deck()
    return BLOCKS, SEATS


def _cells(g, box, min_overlap=0.2):
    x0, x1, y0, y1, z0, z1 = box
    h = si.CELL / 2
    ox = np.minimum(g.X + h, x1) - np.maximum(g.X - h, x0)
    oy = np.minimum(g.Y + h, y1) - np.maximum(g.Y - h, y0 + 0.01)
    oz = np.minimum(g.Z + h, z1) - np.maximum(g.Z - h, z0)
    return (ox >= min_overlap - 1e-6) & (oz >= min_overlap - 1e-6) & (oy >= min(min_overlap, y1 - y0 - 0.01) - 1e-6)


def solid_boxes():
    boxes = [(kwargs.get("name", builder), solid) for builder, kwargs, solid in CUSTOM if solid is not None]
    for i, b in enumerate(BLOCKS):
        if b["solid"]:
            x0, x1, y0, y1, z0, z1 = footprint(b["block"], b["x"], b["y"], b["z"], b["yaw"], b["scale"])
            boxes.append(("%s #%d" % (b["block"], i), (x0, x1, b["y"], y1, z0, z1)))
    return boxes


def apply_to_grid(g):
    """FURNITURE cells under the solid furniture. Every solid piece must be solid somewhere."""
    free = (g.k == si.DRY) | (g.k == si.OUT)
    boxes = solid_boxes()
    for name, box in boxes:
        g.k[_cells(g, box) & free] = si.FURNITURE
    hollow = [name for name, box in boxes if not (_cells(g, box) & (g.k == si.FURNITURE)).any()]
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


DECOR_PATH = "src/main/resources/assets/medievalships/interiors/rustic_skiff_decor.json"
