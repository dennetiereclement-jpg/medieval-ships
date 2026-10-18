"""Furniture of the Nautilus: blocks of the decoration mods (drawn by the Nautilus where they stand,
moving with it; never placed in the world) and the seats.

  src/main/resources/assets/medievalships/interiors/nautilus_decor.json

Each block is given by the centre of its bottom face (ship-local) and the direction its front
faces. Its collision footprint is added to the interior grid (solid cells), so players walk around
tables and cabinets; chairs are not solid but are seats. A block whose mod is missing on a client
is replaced by its stand-in, a box of the same size in the Nautilus's model (bone "fallback_<i>").

Mods used (the server owner's decoration mods, see docs/NAUTILUS_PLAN.md):
  farmhouse_decorations (Farmhouse Decorations), furnish (Furnish), farmersdelight (Farmer's Delight),
  landsoficaria (Lands of Icaria), mebahelcreaturesdwarven (Mebahel Dwarven Automatons)
"""
import json
import math

import numpy as np

import nautilus_interior as ni

# front faces: yaw of the block about the vertical (its model's north is its front)
FACING = {"stern": 0.0, "starboard": 90.0, "bow": 180.0, "port": 270.0}

# measured model bounds (block space, x east, z south; the front is north), from the mods' files
BOUNDS = {
    "farmhouse_decorations:dining_chair": (0.12, 0.88, 0.0, 1.56, 0.0, 0.97),
    "farmhouse_decorations:dining_table_middle": (0.0, 1.0, 0.8, 1.0, 0.02, 0.98),
    "farmhouse_decorations:dining_table_side": (0.0, 1.0, 0.0, 1.0, 0.02, 0.98),
    "farmhouse_decorations:sofa_left": (0.0, 0.88, 0.0, 0.88, 0.19, 1.0),
    "farmhouse_decorations:sofa_middle": (0.0, 1.0, 0.06, 0.78, 0.22, 0.98),
    "farmhouse_decorations:sofa_right": (0.12, 1.0, 0.0, 0.88, 0.19, 1.0),
    "farmhouse_decorations:tall_bookshelf": (0.0, 1.0, 0.0, 1.97, 0.19, 1.0),
    "farmhouse_decorations:piano": (-1.0, 1.03, 0.0, 1.22, 0.31, 1.02),
    "farmhouse_decorations:double_bed": (-0.98, 0.98, 0.0, 1.2, 0.02, 1.98),
    "farmhouse_decorations:single_bed": (-0.11, 1.11, 0.0, 1.14, 0.02, 1.98),
    "farmhouse_decorations:desk": (-0.95, 1.98, 0.0, 1.02, -0.03, 1.03),
    "farmhouse_decorations:dresser": (0.0, 1.0, 0.0, 1.02, 0.25, 1.0),
    "farmhouse_decorations:night_stand": (0.19, 0.81, 0.0, 0.62, 0.5, 1.0),
    "farmhouse_decorations:liquor_cabinet": (-1.0, 1.0, 0.0, 1.0, 0.3, 1.0),
    "farmhouse_decorations:lamp": (0.16, 0.84, 0.0, 0.97, 0.16, 0.84),
    "farmhouse_decorations:standing_lamp": (0.19, 0.81, 0.0, 2.0, 0.19, 0.81),
    "farmhouse_decorations:chained_kerosene_lantern": (0.37, 0.63, 0.33, 1.0, 0.38, 0.62),
    "farmhouse_decorations:kerosene_lantern": (0.37, 0.63, 0.0, 0.48, 0.38, 0.62),
    "farmhouse_decorations:rug_3x_3": (-0.62, 1.62, 0.0, 0.03, -0.62, 1.62),
    "farmhouse_decorations:rug_1x_3": (-0.88, 1.88, 0.0, 0.03, 0.0, 1.0),
    "farmhouse_decorations:coffee_table": (-0.06, 1.06, 0.0, 0.5, -0.06, 1.06),
    "farmhouse_decorations:round_table": (-0.06, 1.06, 0.0, 1.0, -0.06, 1.06),
    "farmhouse_decorations:rocking_chair": (0.0, 1.0, 0.0, 1.52, 0.0, 1.18),
    "farmhouse_decorations:wardrobe": (-0.84, 0.84, 0.0, 1.98, 0.16, 1.0),
    "farmhouse_decorations:bathroom_sink": (0.0, 1.0, 0.0, 1.23, 0.0, 1.0),
    "farmhouse_decorations:wall_shelf": (0.0, 1.0, 0.0, 1.22, 0.56, 1.0),
    "farmhouse_decorations:pile_of_books": (0.28, 0.64, 0.0, 0.23, 0.4, 0.73),
    "farmhouse_decorations:wine_glass": (0.44, 0.56, 0.0, 0.25, 0.44, 0.56),
    "farmhouse_decorations:red_wine_bottle": (0.39, 0.55, 0.0, 0.33, 0.42, 0.58),
    "farmhouse_decorations:typewriter": (0.12, 0.88, 0.0, 0.5, 0.03, 0.96),
    "farmhouse_decorations:gramophone": (0.05, 0.81, 0.0, 0.97, 0.19, 0.81),
    "farmhouse_decorations:cuckoo_clock": (0.2, 0.8, 0.17, 0.97, 0.81, 1.0),
    "farmhouse_decorations:kitchen_counter": (0.0, 1.0, 0.0, 1.0, 0.08, 1.0),
    "farmhouse_decorations:kitchen_antique_oven": (0.0, 1.0, 0.0, 1.7, 0.04, 0.99),
    "farmhouse_decorations:kitchen_sink": (0.0, 1.0, 0.0, 1.27, 0.08, 1.0),
    "farmhouse_decorations:kitchen_wall_cabinet": (0.0, 1.0, 0.0, 1.0, 0.38, 1.0),
    "farmhouse_decorations:kitchen_wall_shelf": (0.0, 1.0, 0.0, 1.0, 0.38, 1.0),
    "farmhouse_decorations:seasoning_rack": (0.12, 0.88, 0.0, 0.78, 0.69, 1.0),
    "farmhouse_decorations:radiator": (-0.39, 1.25, 0.0, 0.83, 0.62, 0.94),
    "furnish:red_showcase": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    "furnish:rare_english_plate": (0.06, 0.94, 0.0, 0.06, 0.06, 0.94),
    "furnish:locker": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    "furnish:book_pile": (0.17, 0.88, 0.01, 0.39, 0.18, 0.86),
    "farmersdelight:stove": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    "farmersdelight:cooking_pot": (0.12, 0.88, 0.0, 1.0, 0.0, 1.0),
    "farmersdelight:skillet": (-0.69, 0.94, 0.0, 0.25, 0.06, 0.94),
    "farmersdelight:cutting_board": (0.06, 0.94, 0.0, 0.06, 0.06, 0.94),
    "mebahelcreaturesdwarven:dwemer_metal_pipe": (0.06, 0.94, 0.06, 0.94, 0.0, 1.0),
    "mebahelcreaturesdwarven:dwemer_metal_pipe_gear": (0.12, 0.88, 0.12, 0.88, 0.0, 1.0),
}

# stand-in look when the mod is missing
FALLBACK_REGION = {"furnish:red_showcase": "glass", "farmersdelight:stove": "iron", "farmersdelight:cooking_pot": "iron",
                   "mebahelcreaturesdwarven:dwemer_metal_pipe": "brass", "mebahelcreaturesdwarven:dwemer_metal_pipe_gear": "brass",
                   "furnish:locker": "steel"}

BLOCKS = []   # dicts: block, x, y, z, yaw, solid (bool)
SEATS = []    # dicts: x, y, z, dx, dy, dz


def to_ship(bid, x, y, z, yaw, px, py, pz, scale=1.0):
    """Ship-local point of a point (px, py, pz) of the block model placed at (x, y, z) with yaw (degrees),
    the same transform as the renderer: translate, rotate about y, scale, then (-0.5, 0, -0.5)."""
    qx, qz = (px - 0.5) * scale, (pz - 0.5) * scale
    a = math.radians(yaw)
    c, s = math.cos(a), math.sin(a)
    return x + qx * c + qz * s, y + py * scale, z - qx * s + qz * c


def footprint(bid, x, y, z, yaw, scale=1.0):
    b = BOUNDS[bid]
    pts = [to_ship(bid, x, y, z, yaw, px, py, pz, scale) for px in (b[0], b[1]) for py in (b[2], b[3]) for pz in (b[4], b[5])]
    xs, ys, zs = zip(*pts)
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)


def block(bid, x, y, z, facing="stern", solid=True, scale=1.0):
    yaw = FACING[facing] if isinstance(facing, str) else float(facing)
    BLOCKS.append({"block": bid, "x": x, "y": y, "z": z, "yaw": yaw, "solid": solid, "scale": scale})
    return len(BLOCKS) - 1


def seat(x, y, z, dx, dz):
    """A seat: sitting point (x, y = seat height, z) and where to stand up (dx, dz on the floor)."""
    SEATS.append({"x": x, "y": y, "z": z, "dx": dx, "dy": ni.M0 + 0.02 if y < ni.M0 + 2 else y - 0.45, "dz": dz})


# ---------------------------------------------------------------- rooms
FD = "farmhouse_decorations:"
FU = "furnish:"
FR = "farmersdelight:"
MB = "mebahelcreaturesdwarven:"


def dining_room():
    """Salle à manger (reference panel 1): a long dark table with chairs on both sides, plates,
    glasses and bottles, sideboards against the side walls."""
    m = ni.M0
    zt = 15.5               # table centre line, across the room
    xs = [-2.5, -1.5, -0.5, 0.5, 1.5, 2.5]
    for i, x in enumerate(xs):
        bid = FD + ("dining_table_side" if i in (0, len(xs) - 1) else "dining_table_middle")
        block(bid, x, m, zt, "port" if i == 0 else "starboard" if i == len(xs) - 1 else "stern")
    for x in xs:
        block(FD + "dining_chair", x, m, zt - 1.05, "bow", solid=False)
        seat(x, m + 0.45, zt - 0.95, x, zt - 1.6)
        block(FD + "dining_chair", x, m, zt + 1.05, "stern", solid=False)
        seat(x, m + 0.45, zt + 0.95, x, zt + 1.6)
        block(FU + "rare_english_plate", x, m + 1.0, zt - 0.25, "stern", solid=False, scale=0.45)
        block(FU + "rare_english_plate", x, m + 1.0, zt + 0.25, "stern", solid=False, scale=0.45)
        block(FD + "wine_glass", x + 0.3, m + 1.0, zt - 0.35, "stern", solid=False, scale=0.8)
        block(FD + "wine_glass", x - 0.3, m + 1.0, zt + 0.35, "stern", solid=False, scale=0.8)
    for x in (-1.0, 1.0):
        block(FD + "red_wine_bottle", x, m + 1.0, zt, "stern", solid=False)
    # sideboards (crédences) against the side walls, a dresser in each corner of the bow wall
    block(FD + "liquor_cabinet", 4.65, m, zt, "starboard")
    block(FD + "liquor_cabinet", -4.65, m, zt, "port")
    for x in (-3.5, 3.5):
        block(FD + "dresser", x, m, 17.65, "stern")


def build():
    BLOCKS.clear()
    SEATS.clear()
    dining_room()
    return BLOCKS, SEATS


def apply_to_grid(g):
    """Solid cells for the footprints of the solid furniture."""
    for b in BLOCKS:
        if not b["solid"]:
            continue
        x0, x1, y0, y1, z0, z1 = footprint(b["block"], b["x"], b["y"], b["z"], b["yaw"], b["scale"])
        # from the floor under it to its top (a table top is solid down to the floor: no crawling under it)
        g.set(ni.SOLID, x0 + 0.05, x1 - 0.05, b["y"] + 0.01, y1, z0 + 0.05, z1 - 0.05, where=g.k == ni.DRY)


def write(path):
    data = {"blocks": [], "seats": SEATS}
    for i, b in enumerate(BLOCKS):
        data["blocks"].append({"block": b["block"], "x": round(b["x"], 4), "y": round(b["y"], 4), "z": round(b["z"], 4),
                               "yaw": b["yaw"], "scale": b["scale"], "fallback": "fallback_%d" % i})
    with open(path, "w") as f:
        json.dump(data, f, indent=1)


DECOR_PATH = "src/main/resources/assets/medievalships/interiors/nautilus_decor.json"
