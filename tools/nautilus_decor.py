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
    "landsoficaria:cypress_barrel": (0.0, 1.0, 0.0, 0.91, 0.05, 0.95),
    "landsoficaria:fir_barrel": (0.0, 1.0, 0.0, 0.91, 0.05, 0.95),
    "landsoficaria:green_storage_vase": (0.06, 0.94, 0.0, 1.0, 0.06, 0.94),
    "furnish:oak_crate": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    "furnish:spruce_crate": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    "furnish:oak_square_table": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    "furnish:small_locker": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    "furnish:spruce_stool": (0.19, 0.81, 0.0, 0.56, 0.12, 0.75),
}

# stand-in look when the mod is missing
FALLBACK_REGION = {"furnish:red_showcase": "glass", "farmersdelight:stove": "iron", "farmersdelight:cooking_pot": "iron",
                   "mebahelcreaturesdwarven:dwemer_metal_pipe": "brass", "mebahelcreaturesdwarven:dwemer_metal_pipe_gear": "brass",
                   "furnish:locker": "steel"}

BLOCKS = []   # dicts: block, x, y, z, yaw, solid (bool)
SEATS = []    # dicts: x, y, z, dx, dy, dz
CUSTOM = []   # furniture made for the Nautilus: (builder name, kwargs, solid box or None)


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


def custom(builder, solid=None, **kwargs):
    """Furniture of tools/nautilus_furniture.py; solid = (x0, x1, y0, y1, z0, z1) added to the grid."""
    CUSTOM.append((builder, kwargs, solid))


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
    glasses and bottles, sideboards against the side walls, two chandeliers, paintings, a rug."""
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
    custom("rug", p=(0, m, zt), w=7.4, l=3.4)
    for x in (-1.5, 1.5):
        custom("chandelier", name="dining_chandelier_%d" % (x > 0), hook=(x, ni.M1, zt), r=0.6, n=9, drop=0.8)
    for x in (-2.9, 2.9):
        custom("painting", name="dining_painting_aft_%d" % (x > 0), center=(x, 2.6, 13.0), normal=(0, 0, 1), w=2.2, h=1.5,
               region="painting_sea" if x < 0 else "painting_storm")
        custom("painting", name="dining_painting_fore_%d" % (x > 0), center=(x, 2.9, 18.0), normal=(0, 0, -1), w=1.6, h=1.1,
               region="portrait" if x < 0 else "painting_sea")
    for z in (13.6, 17.4):
        for x in (-4.95, 4.95):
            custom("wall_lamp", name="dining_sconce_%d_%d" % (z > 15, x > 0), p=(x, 2.6, z), normal=(-math.copysign(1, x), 0, 0))


def library():
    """Bibliothèque (panel 2): bookcases up to the ceiling on every wall, green Chesterfield sofas
    round a low table, a desk with a typewriter and a lamp, a globe, standing lamps, a rug."""
    m = ni.M0
    # bookcases two high (Farmhouse Decorations tall bookshelves) along the side walls
    for z in (7.6, 8.6, 9.6, 10.6, 11.6):
        for x, facing in ((4.6, "starboard"), (-4.6, "port")):
            for y in (m, m + 2.0):
                block(FD + "tall_bookshelf", x, y, z, facing)
    # and along the end walls, on each side of the doors
    for x in (-4.0, -3.0, -2.0, 2.0, 3.0, 4.0):
        if abs(x) > 3.5:
            continue
        for y in (m, m + 2.0):
            block(FD + "tall_bookshelf", x, y, 12.1, "stern")
            block(FD + "tall_bookshelf", x, y, 7.4, "bow")
    # reading corner on the starboard side: two Chesterfields facing each other, a low table
    custom("chesterfield", solid=(-3.75, -1.25, m, m + 0.9, 7.95, 8.85), name="library_sofa_a", p=(-2.5, m, 8.4), facing="bow")
    custom("chesterfield", solid=(-3.75, -1.25, m, m + 0.9, 10.75, 11.65), name="library_sofa_b", p=(-2.5, m, 11.2), facing="stern")
    for x in (-3.2, -1.8):
        seat(x, m + 0.5, 8.5, x, 9.3)
        seat(x, m + 0.5, 11.1, x, 10.3)
    block(FD + "coffee_table", -2.5, m, 9.8, "stern")
    block(FD + "pile_of_books", -2.6, m + 0.5, 9.8, "port", solid=False)
    # port side: the desk with its typewriter and lamp, an armchair, the globe, standing lamps
    block(FD + "desk", 3.3, m, 8.5, "bow")
    block(FD + "typewriter", 3.0, m + 1.02, 8.4, "bow", solid=False)
    block(FD + "lamp", 4.0, m + 1.02, 8.3, "bow", solid=False)
    custom("armchair", name="library_desk_chair", p=(3.3, m, 9.6), facing="stern")
    seat(3.3, m + 0.5, 9.6, 2.4, 9.6)
    custom("globe", solid=(2.2, 3.0, m, m + 1.4, 10.8, 11.6), name="library_globe", p=(2.6, m, 11.2))
    block(FD + "standing_lamp", 4.0, m, 11.4, "starboard")
    block(FD + "standing_lamp", -4.0, m, 9.8, "port")
    custom("rug", p=(0, m, 9.8), w=4.0, l=4.2)
    custom("chandelier", name="library_chandelier", hook=(0, ni.M1, 9.8), r=0.55, n=8, drop=0.7)


def salon():
    """Grand salon (panel 3): the monumental organ against the aft wall, showcases of corals, shells
    and pearls, red sofas and armchairs round a central table, paintings in gilded frames, red
    curtains at the two great windows, chandeliers, an oriental rug."""
    m = ni.M0
    custom("organ", solid=(-3.0, 2.0, m, ni.SALON_TOP, -6.5, -4.55), name="organ", base=(-0.5, m, -6.5), normal=(0, 0, 1),
           width=5.0, height=5.3)
    seat(-0.5, m + 0.55, -4.4, -0.5, -3.8)
    # showcases (Furnish), two high, with corals, shells and pearls inside
    k = 0
    for x in (-3.0, 3.0):
        for z in ((4.1, 5.3) if True else ()):
            for y in (m, m + 1.0):
                block(FU + "red_showcase", x, y, z, "stern")
                custom("showcase_contents", name="showcase_%d" % k, center=(x, y + 0.02, z), kind=k % 4)
                k += 1
    for x in (-3.0, 3.0):
        for y in (m, m + 1.0):
            block(FU + "red_showcase", x, y, -3.9, "stern")
            custom("showcase_contents", name="showcase_%d" % k, center=(x, y + 0.02, -3.9), kind=k % 4)
            k += 1
    # the sitting group in the middle: a red sofa (Farmhouse Decorations) and two armchairs round two low tables
    for x, part in ((-1.0, "sofa_right"), (0.0, "sofa_middle"), (1.0, "sofa_left")):
        block(FD + part, x, m, -1.7, "bow")
        seat(x, m + 0.45, -1.6, x, -0.9)
    for x in (-0.55, 0.55):
        block(FD + "coffee_table", x, m, 0.2, "stern")
    block(FD + "gramophone", 0.6, m + 0.5, 0.2, "stern", solid=False)
    for x in (-1.0, 1.0):
        custom("armchair", solid=(x - 0.45, x + 0.45, m, m + 1.0, 1.35, 2.25), name="salon_armchair_%d" % (x > 0), p=(x, m, 1.8),
               facing="stern")
        seat(x, m + 0.5, 1.8, x, 2.6)
    custom("rug", p=(0, m, 0.0), w=5.6, l=9.0)
    # the great windows: red curtains and a gilded pelmet
    for x in (-3.5, 3.5):
        custom("drapes", name="salon_drapes_%d" % (x > 0), center=(x, 2.6, 0.0), normal=(-math.copysign(1, x), 0, 0), w=5.4, h=5.0)
    # paintings over the showcases
    for x in (-3.5, 3.5):
        custom("painting", name="salon_painting_fore_%d" % (x > 0), center=(x, 3.6, 4.7), normal=(-math.copysign(1, x), 0, 0),
               w=2.2, h=1.5, region="painting_sea" if x < 0 else "painting_storm")
        custom("painting", name="salon_painting_aft_%d" % (x > 0), center=(x, 3.6, -4.2), normal=(-math.copysign(1, x), 0, 0),
               w=1.4, h=1.6, region="portrait")
    custom("painting", name="salon_painting_bow", center=(-2.0, 3.4, 6.5), normal=(0, 0, -1), w=2.4, h=1.6, region="painting_storm")
    for z in (-3.2, 3.2):
        custom("chandelier", name="salon_chandelier_%d" % (z > 0), hook=(0, ni.SALON_TOP, z), r=0.9, n=12, drop=0.9)


def cabins():
    """Professor Aronnax's cabin (panel 4, comfortable) and Captain Nemo's (panel 5, austere)."""
    m = ni.M0
    # Aronnax, port side: bed, desk with chair and lamp, shelf with books, dresser, washbasin, rug, porthole
    block(FD + "single_bed", 4.2, m, 25.4, "stern")
    block(FD + "night_stand", 2.9, m, 26.0, "stern")
    block(FD + "lamp", 2.9, m + 0.62, 26.0, "stern", solid=False)
    block(FD + "desk", 3.6, m, 20.6, "bow")
    block(FD + "pile_of_books", 3.0, m + 1.02, 20.5, "bow", solid=False)
    block(FD + "lamp", 4.3, m + 1.02, 20.4, "bow", solid=False)
    block(FD + "dining_chair", 3.6, m, 21.6, "stern", solid=False)
    seat(3.6, m + 0.45, 21.5, 2.6, 21.8)
    block(FD + "wall_shelf", 3.6, m + 2.0, 20.3, "bow", solid=False)
    block(FD + "pile_of_books", 3.4, m + 2.4, 20.3, "bow", solid=False)
    block(FD + "bathroom_sink", 4.5, m, 23.3, "starboard")
    custom("rug", p=(3.3, m, 23.2), w=2.4, l=2.6)
    custom("painting", name="aronnax_painting", center=(2.0, 2.6, 25.5), normal=(1, 0, 0), w=1.0, h=0.8, region="painting_sea")
    custom("drapes", name="aronnax_drapes", center=(5.0, 2.0, 23.2), normal=(-1, 0, 0), w=1.2, h=2.0)
    custom("chandelier", name="aronnax_lamp", hook=(3.5, ni.M1, 23.2), r=0.35, n=6, drop=0.5, tiers=1)
    # Nemo, starboard side: iron bed, raw wood table, iron chair, instruments, charts, a discreet lantern
    custom("iron_bed", solid=(-4.85, -3.75, m, m + 1.1, 24.4, 26.4), name="nemo_bed", p=(-4.3, m, 25.4), facing="stern")
    block(FU + "oak_square_table", -3.3, m, 21.0, "stern")
    block(FD + "kerosene_lantern", -3.1, m + 1.0, 21.1, "stern", solid=False)
    custom("chart_sheet", name="nemo_chart", p=(-3.45, m + 1.0, 20.9))
    custom("metal_chair", name="nemo_chair", p=(-3.3, m, 22.0), facing="stern")
    seat(-3.3, m + 0.5, 22.0, -2.4, 22.2)
    custom("instrument_panel", name="nemo_panel_a", center=(-5.0, 2.4, 21.4), normal=(1, 0, 0), w=1.4, h=1.1)
    custom("instrument_panel", name="nemo_panel_b", center=(-5.0, 2.4, 25.0), normal=(1, 0, 0), w=1.0, h=0.9)
    custom("painting", name="nemo_chart_wall", center=(-3.5, 2.5, 20.0), normal=(0, 0, 1), w=2.0, h=1.4, region="chart")


def corridor_and_coursive():
    m, l = ni.M0, ni.L0
    for z in (20.5, 24.5):
        block(FD + "chained_kerosene_lantern", 0.0, ni.M1 - 1.0, z, "stern", solid=False)
    custom("painting", name="corridor_portrait", center=(0, 2.6, 26.5), normal=(0, 0, -1), w=1.2, h=1.6, region="portrait")
    for z in (7.0, 11.0, 15.0, 19.0, 23.0):
        block(FD + "chained_kerosene_lantern", 3.0, ni.L1 - 1.0, z, "stern", solid=False)
    custom("pipe_run", name="coursive_pipe_a", a=(3.75, ni.L1 - 0.3, 5.0), b=(3.75, ni.L1 - 0.3, 24.2), r=0.12)
    custom("pipe_run", name="coursive_pipe_b", a=(3.75, ni.L1 - 0.65, 5.0), b=(3.75, ni.L1 - 0.65, 24.2), r=0.08, region="brass")
    for z in (-5.0, -1.0, 3.0):
        block(FD + "chained_kerosene_lantern", 0.0, ni.L1 - 1.0, z, "stern", solid=False)


def kitchen_and_crew():
    """Cuisine (panel 11) and the crew's quarters, on the lower level."""
    l = ni.L0
    x = -4.0
    for z, bid in ((7.0, FD + "kitchen_counter"), (8.0, FD + "kitchen_counter"), (9.0, FD + "kitchen_sink"),
                   (10.0, FD + "kitchen_antique_oven"), (11.0, FR + "stove"), (12.0, FR + "stove"), (13.0, FD + "kitchen_counter")):
        block(bid, x, l, z, "port")
    block(FR + "cooking_pot", x, l + 1.0, 11.0, "port", solid=False)
    block(FR + "skillet", x, l + 1.0, 12.0, "port", solid=False)
    block(FR + "cutting_board", x, l + 1.0, 7.0, "port", solid=False)
    for z in (7.0, 8.0, 13.0):
        block(FD + "kitchen_wall_cabinet", x, l + 2.2, z, "port", solid=False)
    block(FD + "seasoning_rack", x, l + 1.0, 13.0, "port", solid=False)
    for z in (10.0, 12.0):
        block(FD + "chained_kerosene_lantern", -1.5, ni.L1 - 1.0, z, "stern", solid=False)
    # a work table in the middle
    for z in (9.5, 10.5, 11.5):
        block(FU + "oak_square_table", -1.6, l, z, "stern")
    block(FR + "cutting_board", -1.6, l + 1.0, 10.5, "stern", solid=False)
    # crew: four bunks, lockers, a table with stools
    for z in (15.6, 17.8):
        block(FD + "single_bed", -3.9, l, z + 1.0, "stern")
    for x in (-0.4, 0.6):
        block(FU + "small_locker", x, l, 22.5, "stern")
    block(FU + "oak_square_table", -1.5, l, 21.5, "stern")
    for x in (-2.3, -0.7):
        block(FU + "spruce_stool", x, l, 21.5, "stern", solid=False)
        seat(x, l + 0.5, 21.5, x, 20.6)
    block(FD + "chained_kerosene_lantern", -1.5, ni.L1 - 1.0, 18.5, "stern", solid=False)


def stores():
    l = ni.L0
    for x0, s_ in ((3.6, 1), (-3.6, -1)):
        for k, z in enumerate((-5.3, -4.3, -3.3, 2.3, 3.3)):
            block("landsoficaria:" + ("cypress_barrel" if k % 2 else "fir_barrel"), x0, l, z, "stern")
        for z in (-1.8, -0.8):
            block(FU + "oak_crate", x0, l, z, "stern")
            block(FU + "spruce_crate", x0, l + 1.0, z, "stern")
        block("landsoficaria:green_storage_vase", x0 - s_ * 1.0, l, 3.3, "stern")


def airlock():
    """Sas des scaphandres (panel 14): diving suits on their stands, air tanks, valves."""
    l = ni.L0
    for k, x in enumerate((-1.4, 0.1, 1.6)):
        custom("diving_suit", solid=(x - 0.35, x + 0.35, l, l + 2.4, 28.1, 28.9), name="suit_%d" % k, p=(x, l, 28.5), facing="stern")
    for k, (x, z) in enumerate(((2.1, 25.6), (2.1, 26.4))):
        custom("tank", solid=(x - 0.35, x + 0.35, l, l + 1.7, z - 0.35, z + 0.35), name="airlock_tank_%d" % k, p=(x, l, z))
    custom("valve_wheel", name="airlock_fill_valve", p=(-0.9, l + 1.6, 25.0), normal=(0, 0, 1))
    custom("valve_wheel", name="airlock_pump_valve", p=(0.9, l + 1.6, 25.0), normal=(0, 0, 1))
    custom("pipe_run", name="airlock_pipe", a=(-2.3, ni.L0 + 3.2, 25.2), b=(2.3, ni.L0 + 3.2, 25.2), r=0.1)


def engine_room():
    """Chambre des machines: section A, the batteries (panel 12); section B, the engine (panel 13)."""
    l, m = ni.L0, ni.M0
    for z in (-14.6, -18.0):
        custom("battery_rack", solid=(-4.6, -3.9, l, l + 2.0, z - 1.6, z + 1.6), name="batteries_stbd_%d" % int(-z), p=(-4.6, l, z),
               normal=(1, 0, 0), cells=6, rows=2)
    custom("battery_rack", solid=(3.0, 3.7, l, l + 2.0, -18.6, -13.4), name="batteries_port", p=(3.7, l, -16.0), normal=(-1, 0, 0),
           cells=10, rows=2)
    custom("instrument_panel", name="engine_board", center=(-2.0, l + 2.0, -21.0), normal=(0, 0, 1), w=2.4, h=1.4)
    custom("engine_block", solid=(-2.9, -0.3, l, l + 3.1, -29.5, -22.5), name="engine", p=(-1.6, l, -26.0), length=7.0, cylinders=4)
    for z in (-24.0, -28.0):
        block(MB + "dwemer_metal_pipe", 3.4, l + 3.2, z, "stern", solid=False)
        block(MB + "dwemer_metal_pipe_gear", 3.4, l + 3.2, z + 1.0, "stern", solid=False)
    custom("pipe_run", name="engine_pipe_a", a=(3.6, l + 0.5, -29.0), b=(3.6, l + 0.5, -13.0), r=0.16)
    custom("pipe_run", name="engine_pipe_b", a=(-4.0, l + 3.4, -28.0), b=(-4.0, l + 3.4, -13.0), r=0.14, region="brass")
    custom("railing", name="catwalk_rail", points=[(1.0, m, -12.6), (1.0, m, -27.9)], h=1.0)
    for z in (-15.0, -19.0, -24.0, -28.0):
        block(FD + "chained_kerosene_lantern", -1.6, ni.M1 - 1.0, z, "stern", solid=False)


def wheelhouse_and_cage():
    """Timonerie (panel 6) and the projector cage behind it (panel 7)."""
    y = ni.ns.CASING_TOP_Y
    custom("helm", name="helm", center=(0, y + 1.35, 21.3))
    custom("binnacle", name="binnacle", p=(-1.0, y, 21.4))
    custom("telegraph", name="telegraph", p=(1.0, y, 21.4), normal=(0, 0, -1))
    custom("lever", name="lever_a", p=(0.9, y, 20.2))
    custom("lever", name="lever_b", p=(1.15, y, 19.9), tilt=-0.4)
    custom("instrument_panel", name="helm_panel_port", center=(2.0, y + 1.9, 16.8), normal=(-1, 0, 0), w=1.4, h=0.9)
    custom("instrument_panel", name="helm_panel_stbd", center=(-2.0, y + 1.9, 16.8), normal=(1, 0, 0), w=1.4, h=0.9)
    custom("instrument_panel", name="helm_panel_fore_port", center=(2.0, y + 1.9, 20.8), normal=(-1, 0, 0), w=1.2, h=0.8)
    custom("instrument_panel", name="helm_panel_fore_stbd", center=(-2.0, y + 1.9, 20.8), normal=(1, 0, 0), w=1.2, h=0.8)
    custom("speaking_tube", name="speaking_tube", p=(-1.7, y + 1.4, 16.1), top=(-1.7, y + 2.9, 16.1))
    block(FD + "chained_kerosene_lantern", 0.0, ni.ns.TOWER_TOP_Y - 1.5, 17.0, "stern", solid=False)
    custom("projector", name="projector", lens_center=(0, ni.ns.LENS_Y, ni.ns.TOWER_Z[0] - 0.05), r=0.55, length=2.4)


def lifeboat():
    custom("lifeboat", name="lifeboat", center=(0, 8.45, -19.0), length=6.4, width=2.4)


def build():
    BLOCKS.clear()
    SEATS.clear()
    CUSTOM.clear()
    dining_room()
    library()
    salon()
    cabins()
    corridor_and_coursive()
    kitchen_and_crew()
    stores()
    airlock()
    engine_room()
    wheelhouse_and_cage()
    lifeboat()
    return BLOCKS, SEATS


def apply_to_grid(g):
    """Solid cells for the footprints of the solid furniture."""
    for builder, kwargs, solid in CUSTOM:
        if solid is not None:
            x0, x1, y0, y1, z0, z1 = solid
            g.set(ni.FURNITURE, x0 + 0.05, x1 - 0.05, y0 + 0.01, y1, z0 + 0.05, z1 - 0.05, where=g.k == ni.DRY)
    for b in BLOCKS:
        if not b["solid"]:
            continue
        x0, x1, y0, y1, z0, z1 = footprint(b["block"], b["x"], b["y"], b["z"], b["yaw"], b["scale"])
        # from the floor under it to its top (a table top is solid down to the floor: no crawling under it)
        g.set(ni.FURNITURE, x0 + 0.05, x1 - 0.05, b["y"] + 0.01, y1, z0 + 0.05, z1 - 0.05, where=g.k == ni.DRY)


def write(path):
    data = {"blocks": [], "seats": SEATS}
    for i, b in enumerate(BLOCKS):
        data["blocks"].append({"block": b["block"], "x": round(b["x"], 4), "y": round(b["y"], 4), "z": round(b["z"], 4),
                               "yaw": b["yaw"], "scale": b["scale"], "fallback": "fallback_%d" % i})
    with open(path, "w") as f:
        json.dump(data, f, indent=1)


DECOR_PATH = "src/main/resources/assets/medievalships/interiors/nautilus_decor.json"
