"""Furniture of the Gear Steamship: blocks of the decoration mods (drawn by the ship where they stand, moving
with it; never placed in the world), furniture modelled for the ship (tools/gear_steam_furniture.py, drawn by
tools/generate_gear_steam.py), and the seats.

  src/main/resources/assets/medievalships/interiors/gear_steamship_decor.json

Same format as tools/frigate_decor.py (read by fr.medievalships.core.InteriorDecor). A block whose mod is
missing on a client is replaced by its stand-in, a box of the same size in the model (bone "fallback_<i>").
The solid furniture is added to the interior grid (FURNITURE cells): the players walk round it; chairs, benches,
stools and the small things on the tables are not solid.

The mods' blocks first (catalog /tmp/claude-0/mods_catalog/catalog.json: Farmhouse Decorations, Furnish, Farmer's
Delight, Lands of Icaria); modelled pieces only for what they lack: the steam engine and its
flywheel, the coal bunkers, the steam pipes, valves and gauges, the engine-order telegraph, the windlass, bitts and
ventilators of the decks, the windows seen from inside, the navigator's instruments, spare gears and pipes.

Room by room (docs/GearSteam_PLAN.md, section 10):
  engine room   the boiler (P1), the twin-cylinder engine and its flywheel (port, forward), the workbench, its tool
                board and the lockers (starboard, forward), the coal bunker (starboard, aft), the railing round the
                stair hatch, the steam pipes, the gauge boards, the telegraph repeater, the stoker's stool
  crew quarters the mess table and its benches (8 seats), three bunks, lockers, a wardrobe, the galley range with
                its counter, pot and spice rack, a guitar, a coat rack
  captain       the bed, the desk and the captain's chair, the bookcase, the liquor cabinet, a dresser, a visitor's
                chair, a rug, the wall clock, a chart on the wall, the windows from inside
  hold          crates and sacks along the port side, barrels on the starboard side, the main coal bunkers under
                the engine room, a spare gear wheel, spare pipes, chain and rope
  decks         cargo waiting for the crane on the poop deck, the windlass, bitts, crates and benches of the
                forecastle, the ventilators of the engine house roof, the telegraph and an officers' bench on the
                bridge, barrels on the waist, benches on the stern gallery

Kept clear (checked by GearSteamShipTest and the walkable report): the doors, the stairs, the ladders, the
seats' stand-up spots, the centre line of the hold, the gangplank's step on the starboard waist.
"""
import json
import math

import numpy as np

import gear_steam_interior as gi
import gear_steam_shape as gs
from frigate_decor import BOUNDS as _FRIGATE_BOUNDS, FALLBACK_REGION as _FRIGATE_FALLBACK, FD, FU, FR, LI   # shared, read only

FACING = {"stern": 0.0, "starboard": 90.0, "bow": 180.0, "port": 270.0}

# model bounds of the default state (block space, x east, z south, the front is north; element and blockstate
# rotations applied), from the mods catalog ("bounds")
BOUNDS = dict(_FRIGATE_BOUNDS)
BOUNDS.update({
    FD + "single_bed": (-0.109, 1.109, 0.0, 1.141, 0.016, 1.984),
    FD + "dining_table_side": (0.0, 1.0, -0.016, 1.0, 0.016, 0.984),
    FD + "dining_table_middle": (0.0, 1.0, 0.797, 1.0, 0.016, 0.984),
    FD + "wardrobe": (-0.844, 0.844, 0.0, 1.984, 0.156, 1.0),
    FD + "dresser": (0.0, 1.0, 0.0, 1.016, 0.25, 1.0),
    FD + "cuckoo_clock": (0.203, 0.797, 0.172, 0.969, 0.812, 1.0),
    FD + "kitchen_counter": (0.0, 1.0, 0.0, 1.0, 0.078, 1.0),
    FD + "kitchen_antique_oven_decorated": (-0.018, 1.0, 0.0, 1.703, 0.039, 0.992),
    FD + "seasoning_rack": (0.125, 0.875, 0.0, 0.781, 0.688, 1.0),
    FD + "acoustic_guitar": (0.25, 0.75, 0.013, 1.185, 0.431, 0.999),
    FD + "wall_shelf": (0.0, 1.0, 0.0, 1.219, 0.559, 1.0),
    FD + "dining_chair": (0.125, 0.875, 0.0, 1.563, 0.0, 0.973),
    FD + "workbench": (-0.875, 0.875, 0.0, 1.25, 0.078, 1.0),
    FU + "dark_oak_chair": (0.062, 0.938, 0.0, 1.875, 0.0, 0.812),
    FU + "crimson_chair": (0.125, 0.875, -0.038, 1.0, 0.0, 0.75),
    FU + "locker": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FU + "small_locker": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FU + "plate": (0.062, 0.938, 0.0, 0.062, 0.062, 0.938),
    FU + "picture_frame": (0.25, 0.75, 0.002, 0.609, 0.219, 0.632),
    FR + "onion_crate": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FR + "beetroot_crate": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FR + "tomato_crate": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FR + "cooking_pot": (0.0, 1.0, 0.0, 0.904, 0.125, 0.875),
    FR + "roast_chicken_block": (0.062, 0.938, 0.0, 0.5, 0.062, 0.938),
    LI + "tapped_cypress_barrel": (0.047, 0.953, 0.0, 0.906, -0.246, 1.0),
    LI + "populus_barrel": (0.047, 0.953, 0.0, 0.906, 0.0, 1.0),
    LI + "loaded_populus_barrel": (0.047, 0.953, 0.0, 0.906, 0.0, 1.0),
})

# stand-in look when the mod is missing (default: a box of mid brown wood)
FALLBACK_REGION = dict(_FRIGATE_FALLBACK)
FALLBACK_REGION.update({
    FD + "single_bed": "bedding", FD + "dining_table_side": "wood_dark", FD + "dining_table_middle": "wood_dark", FD + "wardrobe": "wood_dark",
    FD + "dresser": "wood_dark", FD + "cuckoo_clock": "wood_dark", FD + "kitchen_counter": "wood_dark",
    FD + "kitchen_antique_oven_decorated": "iron_dark", FD + "seasoning_rack": "in_jars", FD + "acoustic_guitar": "wood_light",
    FD + "wall_shelf": "in_jars", FU + "dark_oak_chair": "wood_dark", FU + "crimson_chair": "red_paint", FU + "locker": "iron",
    FU + "small_locker": "iron", FU + "plate": "white_paint", FU + "picture_frame": "painting", FU + "dark_oak_bench": "wood_dark",
    FU + "spruce_crate": "crate", FU + "dark_oak_crate": "crate", FR + "potato_crate": "crate", FR + "carrot_crate": "crate",
    FR + "cabbage_crate": "crate", FR + "onion_crate": "crate", FR + "beetroot_crate": "crate", FR + "tomato_crate": "crate",
    FR + "cooking_pot": "iron", FR + "roast_chicken_block": "ham", LI + "cypress_barrel": "in_staves", LI + "loaded_cypress_barrel": "in_staves",
    LI + "loaded_fir_barrel": "in_staves", LI + "tapped_cypress_barrel": "in_staves", LI + "populus_barrel": "in_staves",
    LI + "loaded_populus_barrel": "in_staves", FD + "dining_chair": "wood_dark", FD + "workbench": "wood_mid", FD + "desk": "wood_dark", FD + "tall_bookshelf": "books",
})
GLOWING = {FD + "kerosene_lantern", FD + "chained_kerosene_lantern"}

BLOCKS = []   # dicts: block, x, y, z, yaw, solid, scale
SEATS = []    # dicts: x, y, z, dx, dy, dz
CUSTOM = []   # furniture drawn by generate_gear_steam: (builder name, kwargs, solid box or None)

M, H, P, B, F, E = gs.MAIN_DECK_Y, gs.HOLD_FLOOR_Y, gs.POOP_Y, gs.BRIDGE_Y, gs.FORECASTLE_Y, gs.ENGINE_ROOF_Y
HOLD_CEIL, CREW_CEIL, ENGINE_CEIL, CABIN_CEIL = M - gs.SLAB, P - gs.SLAB, gs.ENGINE_ROOF_Y - gs.SLAB, B - gs.SLAB
SEAT_H = 0.562    # seat height of the Furnish benches, stools and chairs


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


def block(bid, x, y, z, facing="stern", solid=True, scale=1.0, centre=True):
    """A mod block; centre=True: (x, z) is the centre of its footprint (whatever the model's overflow)."""
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


def bench(x, y, z, along_z=False, sit=None):
    """A Furnish dark oak bench (one block long), along x or along z; sit = (dx, dz): a seat on it standing up there."""
    block(FU + "dark_oak_bench", x, y, z, 90.0 if along_z else 0.0, solid=False)
    if sit is not None:
        seat(x, y + SEAT_H, z, sit[0], y, sit[1])


def crate(x, y, z, kind=None, facing="stern"):
    block(kind or FU + "dark_oak_crate", x, y, z, facing)


# ---------------------------------------------------------------- the rooms
def captain_cabin():
    """Cabine du capitaine (the deckhouse on the poop deck, floor 7.5, x -2.5..2.5, z -13.5 -> -7.5, the door aft
    at x -1.25..0.25): the bed against the port wall aft, the desk across the front wall with the captain's chair,
    the bookcase in the starboard aft corner, the liquor cabinet under the starboard windows and a visitor's chair,
    a dresser under the port windows, a rug, the wall clock, a chart on the front wall, the windows seen from inside."""
    y = P
    block(FD + "single_bed", 1.88, y, -12.47, "stern")
    block(FD + "desk", 0.0, y, -8.03, "stern")
    block(FU + "dark_oak_chair", 0.0, y, -9.05, "bow", solid=False)
    seat(0.0, y + SEAT_H, -9.05, 0.0, y, -10.0)
    top = y + 1.016
    block(FD + "kerosene_lantern", 1.05, top, -8.15, "stern", solid=False)
    block(FD + "pile_of_books", -1.1, top, -7.95, "stern", solid=False)
    block(FU + "book_pile", -0.75, top, -7.85, "starboard", solid=False)
    custom("chart_sheet2", name="captain_chart", p=(0.05, top, -8.15), yaw=0.15, w=0.8, l=0.55)
    custom("compass", name="captain_compass", p=(0.6, top, -8.25))
    custom("inkwell", name="captain_inkwell", p=(-0.45, top, -7.8))
    custom("dividers", name="captain_dividers", p=(-0.1, top + 0.012, -8.2), yaw=0.6)
    custom("wall_map", name="captain_wall_chart", center=(0.0, y + 2.05, -7.5), normal=(0, 0, -1), w=1.1, h=0.75)
    block(FD + "tall_bookshelf", -1.98, y, -13.09, "bow")
    block(FD + "liquor_cabinet", -2.15, y, -10.55, "port")
    block(FD + "dining_chair", -1.3, y, -9.35, "bow", solid=False)
    seat(-1.3, y + 0.625, -9.35, -0.7, y, -10.1)
    block(FD + "dresser", 2.12, y, -9.95, "starboard")
    block(FD + "cigar_box", 2.1, y + 1.016, -10.25, "starboard", solid=False)
    block(FU + "picture_frame", 2.15, y + 1.016, -9.7, "starboard", solid=False)
    block(FD + "rug_3x_3", 0.0, y, -10.9, "stern", solid=False)
    block(FD + "cuckoo_clock", 0.85, y + 1.55, -13.4, "bow", solid=False)
    lantern(0.0, CABIN_CEIL, -10.5)
    # the windows seen from inside: three a side, two forward (the outside panes of tools/generate_gear_steam.deckhouse)
    for side in (1, -1):
        for k, z in enumerate((-12.0, -10.0, -8.0)):
            custom("window_in", name="cabin_window_%s%d" % ("p" if side > 0 else "s", k), center=(side * (gs.DECKHOUSE_HALF - 0.5), gs.CABIN_WINDOW_Y - 0.05, z),
                   normal=(-side, 0, 0), w=1.15, h=1.35)
    for k, x in enumerate((-1.3, 1.3)):
        custom("window_in", name="cabin_window_f%d" % k, center=(x, gs.CABIN_WINDOW_Y - 0.05, gs.DECKHOUSE_Z[1] - 0.5), normal=(0, 0, -1), w=1.0, h=1.2)


def crew_quarters():
    """Quartiers de l'equipage (under the poop deck, floor 4.5, z -17 -> -7, 2.5 high; doors: forward port to the
    engine room, aft on the centre line to the gallery): the mess table on the centre line with its benches (eight
    seats), three bunks along the sides clear of the windows, lockers, a wardrobe, the galley range with its counter,
    its pot and spice rack in the starboard aft corner, lanterns."""
    y = M
    # the mess table (Farmhouse dining table, four blocks along z) and its benches
    block(FD + "dining_table_side", 0.0, y, -14.5, "stern")
    block(FD + "dining_table_middle", 0.0, y, -13.5, 90.0)
    block(FD + "dining_table_middle", 0.0, y, -12.5, 90.0)
    block(FD + "dining_table_side", 0.0, y, -11.5, "bow")
    for side in (1, -1):
        for z in (-14.5, -13.5, -12.5, -11.5):
            bench(side * 1.05, y, z, along_z=True, sit=(side * 1.9, z))
    top = y + 1.0
    for k, (x, z) in enumerate(((0.25, -14.4), (-0.25, -13.6), (0.25, -12.4), (-0.25, -11.6))):
        block(FU + "plate", x, top, z, "stern", solid=False, scale=0.42)
    custom("tankards", name="mess_tankards", pts=[(0.3, top, -13.9), (-0.3, top, -14.6), (0.32, top, -11.9), (-0.3, top, -12.9)])
    block(FD + "wine_bottle", 0.05, top, -13.15, "stern", solid=False)
    block(FD + "red_wine_bottle", -0.1, top, -12.0, "stern", solid=False)
    block(FR + "roast_chicken_block", 0.0, top, -12.95, "stern", solid=False, scale=0.7)
    block(FD + "kerosene_lantern", 0.0, top, -14.05, "stern", solid=False)
    # the bunks (Farmhouse single beds), clear of the windows (z -15.6..-12.8) and of the forward port door
    bx = 3.38
    block(FD + "single_bed", bx, y, -11.7, "stern")
    block(FD + "single_bed", -bx, y, -11.7, "stern")
    block(FD + "single_bed", -bx, y, -9.4, "stern")
    # lockers: two along the port wall forward (aside the door's way), two against the forward bulkhead (starboard)
    for z in (-10.0, -9.0):
        block(FU + "locker", 4.0, y, z, "starboard")
    for x in (-3.9, -2.9):
        block(FU + "locker", x, y, -7.5, "stern")
    block(FD + "coat_hanger", -1.9, y, -7.48, "stern")
    block(FD + "acoustic_guitar", -1.05, y, -7.3, "stern", solid=False)
    # the galley in the starboard aft corner: the range, its counter, a pot, the spice rack, the stovepipe
    block(FD + "kitchen_antique_oven_decorated", -2.0, y, -16.52, "bow")
    block(FD + "kitchen_counter", -3.0, y, -16.54, "bow")
    block(FR + "cooking_pot", -3.0, y + 1.0, -16.55, "bow", solid=False)
    block(FD + "seasoning_rack", -3.0, y + 1.25, -16.86, "bow", solid=False)
    custom("stovepipe", name="galley_stovepipe", p0=(-2.0, y + 1.6, -16.82), top=CREW_CEIL, d=0.2)
    # the port aft corner: a wardrobe
    block(FD + "wardrobe", 2.5, y, -16.58, "bow")
    for z in (-13.0, -9.0, -15.5):
        lantern(0.0 if z > -15 else 1.6, CREW_CEIL, z)
    # the windows seen from inside (the hull windows of tools/generate_gear_steam.trims)
    for side in (1, -1):
        for k, z in enumerate((-15.0, -13.4)):
            custom("window_in", name="crew_window_%s%d" % ("p" if side > 0 else "s", k), center=(_wall_x(z, 5.65, side), 5.65, z), normal=(-side, 0, 0),
                   w=1.0, h=1.25)


def _wall_x(z, y, side):
    """x of the inner face of the hull side (the room's wall) at (y, z): the last open cell of the grid."""
    g = _GRID[0]
    j = int((y - gi.Y0) / gi.CELL)
    k = int((z - gi.Z0) / gi.CELL)
    col = g.k[:, j, k]
    open_ = [i for i in range(g.nx) if col[i] in (gi.DRY, gi.FURNITURE) or col[i] >= gi.DOOR]
    i = max(open_) if side > 0 else min(open_)
    return gi.X0 + (i + 1) * gi.CELL if side > 0 else gi.X0 + i * gi.CELL


_GRID = [None]


def engine_room():
    """Salle des machines (floor 4.5, z -6 -> 4.5, 4 high): the boiler under the funnel (modelled by the generator,
    FURNITURE in the grid) with a heap of coal before its firebox and the stoker's stool; the twin-cylinder engine
    and its flywheel on the port side forward; the workbench, its tool board, two lockers and the telegraph repeater
    on the starboard side forward; the coal bunker aft of the stair hatch and the railing round the hatch; the steam
    pipes along the ceiling with their valves, two gauge boards, an oil cask, a toolbox, lanterns."""
    y = M
    ex, ez = 2.1, 1.7
    custom("steam_engine", solid=(1.85, 4.4, y, ENGINE_CEIL - 0.3, ez - 1.2, ez + 1.2), name="engine", x=ex, z=ez, y=y, side=1)
    block(LI + "tapped_cypress_barrel", 3.88, y, 3.85, "starboard")
    custom("sea_chest", solid=(2.1, 3.0, y, y + 0.65, 3.65, 4.35), name="engine_toolbox", p=(2.55, y, 4.0), facing="stern", w=0.85, d=0.55,
           h=0.6)
    # starboard forward: the workbench against the hull, the tool board over it, the lockers by the door
    block(FD + "workbench", -4.04, y, 2.45, "port")
    block(FD + "tool_board", -4.45, y + 1.35, 2.45, "port", solid=False)
    for x in (-2.0, -3.0):
        block(FU + "locker", x, y, 4.0, "stern")
    custom("telegraph", solid=(-1.95, -1.45, y, y + 1.4, 2.65, 3.15), name="engine_telegraph", p=(-1.7, y, 2.9), facing=(0, 0, -1))
    custom("speaking_tube", name="engine_voice_pipe", p=(-1.2, y, 4.32), top=1.55)
    # the stair hatch: an iron railing along both sides; the coal bunker aft of it
    x0, x1 = gs.ENGINE_STAIR_X
    z_top, z_bot = gs.ENGINE_STAIR_Z
    custom("hatch_rail", solid=(x1 + 0.02, x1 + 0.22, y, y + 1.0, z_bot, z_top - 0.3), name="engine_hatch_rail_in",
           pts=[(x1 + 0.12, y, z_top - 0.3), (x1 + 0.12, y, z_bot + 0.05)], h=1.0)
    custom("hatch_rail", solid=(x0 - 0.22, x0 - 0.02, y, y + 1.0, z_bot, z_top - 0.3), name="engine_hatch_rail_out",
           pts=[(x0 - 0.12, y, z_top - 0.3), (x0 - 0.12, y, z_bot + 0.05)], h=1.0)
    custom("coal_bunker", solid=(-4.42, -2.08, y, y + 1.1, -5.97, -4.62), name="engine_bunker", x0=-4.42, x1=-2.08, z0=-5.97, z1=-4.62, y=y,
           h=1.0)
    # before the firebox: a heap of coal, the stoker's stool
    custom("coal_heap_floor", name="firebox_coal", p=(-0.75, y, -3.15), r=0.5)
    block(FU + "dark_oak_stool", 1.2, y, -2.9, "stern", solid=False)
    seat(1.2, y + SEAT_H, -2.9, 1.2, y, -2.0)
    # the steam pipes: from the boiler forward along the ceiling to the engine's steam chest, and to the gauges
    yp = ENGINE_CEIL - 0.48
    custom("pipe", name="steam_main", pts=[(0.75, gs.MAIN_DECK_Y + 3.3, -4.15), (0.75, yp, -3.6), (0.75, yp, 1.38), (3.15, yp, 1.38)], d=0.28)
    custom("valve", name="steam_main_valve", p=(0.75, yp, -0.4), normal=(0, -1, 0), r=0.2)
    custom("pipe", name="steam_gauges", pts=[(-0.75, gs.MAIN_DECK_Y + 3.3, -4.15), (-0.75, yp, -3.6), (-4.15, yp, -3.6), (-4.15, y + 2.55, -3.6)],
           d=0.18)
    custom("valve", name="steam_gauges_valve", p=(-2.6, yp, -3.6), normal=(0, -1, 0), r=0.16)
    custom("gauge_board", name="gauges_s", center=(-4.5, y + 2.15, -2.75), normal=(1, 0, 0), w=1.2, h=0.8)
    custom("gauge_board", name="gauges_p", center=(4.5, y + 2.1, -3.0), normal=(-1, 0, 0), w=1.0, h=0.7)
    custom("lever_bank", name="engine_levers", p=(1.55, y, 3.55), normal=(-1, 0, 0), n_levers=3)
    for x, z in ((0.0, 1.0), (2.8, -4.5), (-2.9, 1.6)):
        lantern(x, ENGINE_CEIL, z)


def hold():
    """Cale (the lower deck, floor 1.0, 3 high): crates and sacks along the port side, barrels lying along the
    starboard side, the main coal bunkers under the engine room, crates over the stair's landing kept clear, forward a
    spare gear wheel, spare pipes, chain and rope; the centre line stays clear; lanterns from the beams."""
    y = H
    kinds = [FU + "dark_oak_crate", FR + "potato_crate", FU + "spruce_crate", FR + "onion_crate", FR + "carrot_crate", FR + "rice_bag",
             FR + "beetroot_crate", FR + "cabbage_crate"]
    # port, aft: two tiers of crates along the hull
    k = 0
    for z in (-14.5, -13.5, -12.5):
        crate(3.48, y, z, kinds[k % len(kinds)])
        k += 1
    for z in (-14.5, -13.5):
        crate(3.48, y + 1.0, z, kinds[(k + 3) % len(kinds)])
        k += 1
    for z in (-10.5, -9.5, -8.5, -7.5, -6.5):
        crate(3.98, y, z, kinds[k % len(kinds)])
        k += 1
    for z in (-10.5, -9.5, -7.5):
        crate(3.98, y + 1.0, z, kinds[(k + 1) % len(kinds)])
        k += 1
    crate(2.95, y, -10.0, FR + "rice_bag")
    crate(2.95, y, -8.0, FR + "rice_bag")
    # starboard, aft: barrels lying, their ends towards the centre line
    for z in (-14.5, -13.5, -12.5):
        block(LI + "loaded_cypress_barrel", -3.5, y, z, "port")
    for z in (-10.5, -9.5, -8.5):
        block(LI + "loaded_fir_barrel" if z != -9.5 else LI + "loaded_populus_barrel", -4.0, y, z, "port")
    block(LI + "tapped_cypress_barrel", -3.88, y, -7.2, "port")
    for z in (-10.0, -9.0):
        block(LI + "populus_barrel", -4.0, y + 0.9, z, "port")
    # under the engine room: the main coal bunkers (port, and starboard forward of the stair from the engine room)
    custom("coal_bunker", solid=(2.58, 4.42, y, y + 1.3, -4.2, 0.8), name="hold_bunker_p", x0=2.58, x1=4.42, z0=-4.2, z1=0.8, y=y, h=1.2)
    custom("coal_bunker", solid=(-4.42, -2.58, y, y + 1.3, -0.45, 2.3), name="hold_bunker_s", x0=-4.42, x1=-2.58, z0=-0.45, z1=2.3, y=y,
           h=1.2)
    # amidships, under the hull windows: one tier of crates and sacks
    for z in (3.0, 4.0, 5.0):
        crate(3.98, y, z, kinds[k % len(kinds)])
        k += 1
    for z in (3.5, 4.5):
        crate(-3.98, y, z, FR + "rice_bag")
    # forward, starboard of the mast: crates in two tiers
    for z in (6.6, 7.6, 8.6):
        crate(-3.45, y, z, FU + "spruce_crate")
    for z in (6.6, 7.6):
        crate(-3.45, y + 1.0, z, FU + "dark_oak_crate")
    crate(-2.6, y, 10.6, FR + "rice_bag")
    crate(-2.6, y, 11.6, FR + "potato_crate")
    # forward, port: a spare gear wheel against the hull, spare pipes; chain and rope coils
    custom("spare_gear", solid=(2.25, 3.05, y, y + 1.9, 11.6, 13.4), name="hold_spare_gear", p=(2.65, y, 12.5), normal=(-1, 0, 0), r=0.85)
    custom("pipe_stack", solid=(1.25, 2.15, y, y + 0.7, 11.0, 14.0), name="hold_spare_pipes", p=(1.7, y, 12.5), along=(0, 0, 1), length=2.6, n=3)
    custom("chain_coil", name="hold_chain", p=(-1.75, y, 13.3), r=0.4, lit=True)
    custom("rope_coil", name="hold_rope", p=(-1.6, y, 9.4), r=0.34)
    for z in (-12.0, -6.0, 0.5, 5.0, 12.0):
        lantern(0.0, HOLD_CEIL, z)


def decks():
    """On the open decks: cargo waiting for the crane on the poop deck (crates, a barrel, a coil of chain) and a
    bench against the deckhouse; the officers' bench and the engine-order telegraph on the bridge; the copper cowl
    ventilators on the engine house roof; barrels by the companion on the waist; the steam windlass, bitts, crates
    and benches on the forecastle; benches on the stern gallery."""
    # poop deck (7.5): crates in the starboard aft corner and on the overhang, a barrel, a coil of chain
    crate(-2.85, P, -16.9)
    crate(-2.85, P, -15.9, FU + "spruce_crate")
    crate(-2.85, P + 1.0, -16.9, FR + "carrot_crate")
    crate(-2.4, P, -18.3, FU + "spruce_crate")
    block(LI + "loaded_fir_barrel", -2.4, P, -19.45, "port")
    custom("chain_coil", name="poop_chain", p=(-1.25, P, -18.9), r=0.38)
    bench(-2.2, P, -14.35, sit=(-1.9, -15.0))
    # bridge (11.0): the officers' bench aft, the telegraph beside the wheel
    bench(-2.0, B, -13.1, sit=(-2.0, -12.25))
    bench(-1.0, B, -13.1, sit=(-1.0, -12.25))
    custom("telegraph", solid=(1.3, 1.8, B, B + 1.4, -8.55, -8.05), name="bridge_telegraph", p=(1.55, B, -8.3), facing=(0, 0, -1), lit=False)
    # engine house roof (9.0): two cowl ventilators forward of the dome
    for side in (1, -1):
        custom("ventilator", solid=(side * 1.7 - 0.25, side * 1.7 + 0.25, E, E + 1.6, 3.15, 3.65), name="vent_%s" % ("p" if side > 0 else "s"),
               p=(side * 1.7, E, 3.4), facing=(0, 0, 1), h=1.25)
    # waist (4.5): two barrels by the companion, against the port bulwark; a coil of rope by the mast
    for z in (6.75, 7.75):
        block(LI + "loaded_cypress_barrel", 3.45, M, z, "bow")
    custom("rope_coil", name="waist_rope", p=(1.0, M, 8.6), r=0.32)
    # forecastle (6.0): the windlass, bitts, two crates to port, benches to starboard, a coil of chain
    custom("windlass", solid=(-0.95, 0.95, F, F + 1.0, 17.45, 18.4), name="windlass", p=(0.0, F, 17.9), width=1.6)
    for side in (1, -1):
        custom("bitts", name="bitts_%s" % ("p" if side > 0 else "s"), p=(side * 1.75, F, 16.85), along=(0, 0, 1))
    crate(2.35, F, 13.9, FU + "spruce_crate")
    crate(2.35, F, 14.9, FR + "tomato_crate")
    for z in (14.4, 15.4):
        bench(-2.05, F, z, along_z=True, sit=(-1.2, z))
    custom("chain_coil", name="fc_chain", p=(1.05, F, 16.3), r=0.32)
    # stern gallery (4.5): three benches along the aft rail
    for x in (-1.0, 0.0, 1.0):
        bench(x, M, -19.7, sit=(x, -18.8))


def build():
    BLOCKS.clear()
    SEATS.clear()
    CUSTOM.clear()
    _GRID[0] = gi.build()
    captain_cabin()
    crew_quarters()
    engine_room()
    hold()
    decks()
    return BLOCKS, SEATS


def _cells(g, box, min_overlap=0.2):
    x0, x1, y0, y1, z0, z1 = box
    h = gi.CELL / 2
    ox = np.minimum(g.X + h, x1) - np.maximum(g.X - h, x0)
    oy = np.minimum(g.Y + h, y1) - np.maximum(g.Y - h, y0 + 0.01)
    oz = np.minimum(g.Z + h, z1) - np.maximum(g.Z - h, z0)
    return (ox >= min_overlap - 1e-6) & (oz >= min_overlap - 1e-6) & (oy >= min(min_overlap, y1 - y0 - 0.01) - 1e-6)


def solid_boxes():
    """(name, box) of every solid piece of furniture (the mods' blocks and the modelled pieces)."""
    boxes = [(kwargs.get("name", builder), solid) for builder, kwargs, solid in CUSTOM if solid is not None]
    for i, b in enumerate(BLOCKS):
        if b["solid"]:
            x0, x1, y0, y1, z0, z1 = footprint(b["block"], b["x"], b["y"], b["z"], b["yaw"], b["scale"])
            boxes.append(("%s #%d" % (b["block"], i), (x0, x1, b["y"], y1, z0, z1)))
    return boxes


def apply_to_grid(g):
    """FURNITURE cells under the solid furniture (on the floor of a room, or on a deck)."""
    free = (g.k == gi.DRY) | (g.k == gi.OUT)
    boxes = solid_boxes()
    for name, box in boxes:
        g.k[_cells(g, box) & free] = gi.FURNITURE
    hollow = [name for name, box in boxes if not (_cells(g, box) & (g.k == gi.FURNITURE)).any()]
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


DECOR_PATH = "src/main/resources/assets/medievalships/interiors/gear_steamship_decor.json"
