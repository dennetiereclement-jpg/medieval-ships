"""Furniture of the Crystal Airship: blocks of the user's decoration mods (drawn by the airship where they stand,
moving with it; never placed in the world), the furniture made for it (tools/crystal_furniture.py and the Sky
Leviathan's tools/leviathan_furniture.py) and the seats, room by room after the interior views of the reference
sheet (poste de pilotage, salon, salle des machines, réserve).

  src/main/resources/assets/medievalships/interiors/crystal_airship_decor.json

Same format and rules as the Nautilus and the Sky Leviathan: each mod block is given by the centre of its bottom face
(ship-local) and the direction its front faces; its footprint becomes solid cells of the interior grid (chairs, sofas,
benches and small things on tables are not solid); a block whose mod is missing on a client is replaced by its
stand-in, a box of the same size in the model (bone "fallback_<i>").

Mods used: farmhouse_decorations (Farmhouse Decorations), furnish (Furnish), farmersdelight (Farmer's Delight),
landsoficaria (Lands of Icaria), mebahelcreaturesdwarven (Mebahel Dwarven Automatons). Block measurements: the
default state's model bounds (x east, z south, front north), from the mods' files (catalogue of the decoration mods).
"""
import json
import math

import crystal_interior as ci
import crystal_shape as cs
import leviathan_decor as ld
import nautilus_decor as nd

FACING = nd.FACING   # stern 0, starboard 90, bow 180, port 270 (the block's north = its front)

FD = "farmhouse_decorations:"
FU = "furnish:"
FR = "farmersdelight:"
IC = "landsoficaria:"
MB = "mebahelcreaturesdwarven:"

BOUNDS = dict(ld.BOUNDS)
BOUNDS.update({
    FD + "sofa_left": (0.0, 0.875, 0.0, 0.875, 0.188, 1.0),
    FD + "sofa_middle": (0.0, 1.0, 0.062, 0.781, 0.219, 0.984),
    FD + "sofa_right": (0.125, 1.0, 0.0, 0.875, 0.188, 1.0),
    FD + "coffee_table": (-0.062, 1.062, 0.0, 0.5, -0.062, 1.062),
    FD + "round_table": (-0.062, 1.062, 0.0, 1.0, -0.062, 1.062),
    FD + "rocking_chair": (0.0, 1.0, 0.0, 1.522, 0.0, 1.183),
    FD + "gramophone": (0.047, 0.812, 0.0, 0.973, 0.188, 0.812),
    FD + "piano": (-1.0, 1.031, 0.0, 1.219, 0.312, 1.016),
    FD + "lamp": (0.156, 0.844, 0.0, 0.969, 0.156, 0.844),
    FD + "typewriter": (0.125, 0.875, 0.0, 0.503, 0.031, 0.961),
    FU + "crimson_chair": (0.125, 0.875, -0.038, 1.0, 0.0, 0.75),
    FU + "dark_oak_pedestal_table": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FU + "mangrove_chair": (0.188, 0.812, 0.0, 1.0, 0.062, 0.812),
    FU + "dark_oak_cabinet": (0.0, 1.0, 0.0, 1.0, -0.062, 1.0),
    FU + "crimson_stool": (0.188, 0.812, 0.0, 0.562, 0.125, 0.75),
    FU + "crimson_pedestal_table": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FU + "crimson_drawers": (0.0, 1.0, 0.0, 1.0, -0.062, 1.0),
    FU + "red_showcase": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FU + "spruce_bench": (0.0, 1.0, 0.0, 0.562, 0.25, 0.75),
    IC + "loaded_fir_barrel": (0.047, 0.953, 0.0, 0.906, 0.0, 1.0),
    FD + "radiator": (-0.391, 1.25, 0.0, 0.828, 0.625, 0.938),
})
SEAT_H = dict(ld.SEAT_H)
SEAT_H.update({FD + "sofa_left": 0.344, FD + "sofa_middle": 0.344, FD + "sofa_right": 0.344, FU + "crimson_chair": 0.5,
               FU + "crimson_stool": 0.562, FD + "rocking_chair": 0.625, FU + "spruce_bench": 0.562, FU + "mangrove_chair": 0.562})
FALLBACK_REGION = dict(ld.FALLBACK_REGION)
FALLBACK_REGION.update({
    FD + "sofa_left": "in_sofa", FD + "sofa_middle": "in_sofa", FD + "sofa_right": "in_sofa", FD + "coffee_table": "in_wood_carved",
    FD + "round_table": "in_wood_carved", FD + "rocking_chair": "in_wood_carved", FD + "gramophone": "in_brass_pol", FD + "piano": "in_wood_carved",
    FD + "lamp": "in_lamp", FD + "typewriter": "in_iron", FU + "crimson_chair": "in_sofa", FU + "crimson_stool": "in_sofa",
    FU + "crimson_pedestal_table": "in_wood_carved", FU + "crimson_drawers": "in_wood_carved", FU + "red_showcase": "in_jars2",
    FU + "spruce_bench": "in_plank", IC + "loaded_fir_barrel": "barrel", FD + "radiator": "in_iron",
    FU + "dark_oak_pedestal_table": "in_wood_carved", FU + "dark_oak_cabinet": "in_wood_carved", FU + "dark_oak_stool": "in_sofa_wood",
    FU + "mangrove_chair": "in_sofa",
    FD + "dining_chair": "in_wood_carved", FU + "dark_oak_chair": "in_sofa", FD + "tall_bookshelf": "in_books", FD + "workbench": "in_plank",
})
GLOWING_FALLBACK = ld.GLOWING_FALLBACK + (FD + "lamp",)
nd.BOUNDS = BOUNDS   # nd.to_ship does not read it, footprints below do

BLOCKS = []    # dicts: block, x, y, z, yaw, solid, scale
SEATS = []     # dicts: x, y, z, dx, dy, dz
CUSTOM = []    # furniture made for the airship: (builder name, kwargs, solid box or None)
PAINTINGS = []
SWITCHES = []

M0, LO, HO, L2 = ci.M0, ci.LO, ci.HO, ci.L2
MESS_BACK = -22.0          # the mess's back wall behind its middle (the stern is rounded)
CEIL_L1, CEIL_L2, CEIL_LO, CEIL_HO = ci.CEIL_L1, ci.CEIL_L2, ci.CEIL_LO, ci.CEIL_HO

_GRID = []


def grid():
    if not _GRID:
        _GRID.append(ci.build())
    return _GRID[0]


def wall_x(y, z, side, x_from=0.0):
    """Inner face of the side wall (side +1: port, -1: starboard) at height y and z, scanning outwards from x_from
    (windows count as wall)."""
    g = grid()
    j = int(math.floor((y - ci.Y0) / ci.CELL))
    l = int(math.floor((z - ci.Z0) / ci.CELL))
    i = int(math.floor((x_from - ci.X0) / ci.CELL))
    while 0 <= i < g.nx:
        if g.k[i, j, l] in (ci.SOLID, ci.OUT, ci.WINDOW):
            return ci.X0 + (i if side > 0 else i + 1) * ci.CELL
        i += side
    return None


def wall_min(y0, y1, z, side, x_from=0.0):
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
    yaw = FACING[facing] if isinstance(facing, str) else float(facing)
    BLOCKS.append({"block": bid, "x": x, "y": y, "z": z, "yaw": yaw, "solid": solid, "scale": scale})
    return len(BLOCKS) - 1


def at(bid, cx, y, cz, facing="stern", solid=True, scale=1.0):
    """A mod block placed by the centre (cx, cz) of its footprint."""
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
    w = min([v for v in ws if v is not None], key=abs)
    cx = w - side * ((x1 - x0) / 2 + gap)
    return at(bid, cx, y, z, facing, solid, scale)


def against_z(bid, x, y, zw, nz, solid=True, scale=1.0, gap=0.02):
    """A mod block against a transverse wall whose face is at z = zw, its front facing nz (+1 bow, -1 stern)."""
    facing = "bow" if nz > 0 else "stern"
    yaw = FACING[facing]
    x0, x1, _, _, z0, z1 = _footprint(bid, 0.0, 0.0, 0.0, yaw, scale)
    cz = zw + nz * ((z1 - z0) / 2 + gap)
    return at(bid, x, y, cz, facing, solid, scale)


def custom(builder, solid=None, **kwargs):
    """Furniture of generate_crystal.py (FURNITURE_BUILDERS); solid = (x0, x1, y0, y1, z0, z1) added to the grid."""
    CUSTOM.append((builder, kwargs, solid))


def seat(x, y, z, dx, dy, dz):
    SEATS.append({"x": x, "y": y, "z": z, "dx": dx, "dy": dy, "dz": dz})


def chair(bid, x, floor, z, facing, dx, dz, solid=False):
    """A chair, stool or bench block centred at (x, z) and its seat."""
    at(bid, x, floor, z, facing, solid=solid)
    seat(x, floor + SEAT_H[bid] - 0.12, z, dx, floor + 0.02, dz)


def painting(name, motive, center, normal, w, h):
    custom("painting_frame", name=name, center=center, normal=normal, w=w, h=h, region="in_wood_carved")
    n = math.hypot(normal[0], normal[2])
    PAINTINGS.append({"motive": motive, "x": center[0] + normal[0] / n * 0.02, "y": center[1], "z": center[2] + normal[2] / n * 0.02,
                      "nx": normal[0] / n, "nz": normal[2] / n, "w": w, "h": h})


def hanging(x, ceiling, z, drop=0.0):
    """A Farmhouse chained kerosene lantern hanging from the ceiling (its chain reaches the ceiling)."""
    block(FD + "chained_kerosene_lantern", x, ceiling - 1.0 - drop, z, "stern", solid=False)


def wall_lantern(name, side, y, z, x_from=0.0, arm=0.34):
    w = wall_x(y, z, side, x_from)
    custom("wall_bracket", name=name, p=(w, y, z), normal=(-side, 0, 0), arm=arm)
    block(FD + "kerosene_lantern", w - side * arm, y - 0.52, z, "stern", solid=False)


def wall_lantern_z(name, x, y, zw, nz, arm=0.34):
    custom("wall_bracket", name=name, p=(x, y, zw), normal=(0, 0, nz), arm=arm)
    block(FD + "kerosene_lantern", x, y - 0.52, zw + nz * arm, "stern", solid=False)


def sofa(side, y, z0, n, name):
    """A Farmhouse sofa of n pieces against a side wall (side +1 port, -1 starboard), from z0 forward, its seats."""
    facing = "starboard" if side > 0 else "port"
    # seen from the front, the right end: towards the bow for a sofa on the port side, the stern on the starboard side
    pieces = []
    for k in range(n):
        if k == 0:
            pieces.append("sofa_left" if side > 0 else "sofa_right")
        elif k == n - 1:
            pieces.append("sofa_right" if side > 0 else "sofa_left")
        else:
            pieces.append("sofa_middle")
    w = min([wall_min(y, y + 0.9, z0 + k + 0.5, side) for k in range(n)], key=abs)
    for k, p in enumerate(pieces):
        z = z0 + 0.5 + k
        bid = FD + p
        yaw = FACING[facing]
        x0, x1, _, _, zz0, zz1 = _footprint(bid, 0.0, 0.0, 0.0, yaw)
        cx = w - side * (0.02 + (x1 - x0) / 2)      # the backs flush with the wall
        at(bid, cx, y, z, facing, solid=False)
        sx = w - side * 0.55
        seat(sx, y + 0.3, z, w - side * 1.35, y + 0.02, z)


# ---------------------------------------------------------------- rooms
def cockpit():
    """Poste de pilotage (reference panel 1): the great wheel facing the arched window, brass instrument columns, a big
    gauge on the wall, a blue crystal lamp, lanterns; the chart table aft, bookcases, the globe, a telescope."""
    f = L2
    custom("instrument_column", solid=(-1.85, -1.15, f, f + 1.6, -15.65, -14.95), name="cockpit_column_0", p=(-1.5, f, -15.3), top="dial",
           facing=(0, 0, -1))
    custom("instrument_column", solid=(1.15, 1.85, f, f + 1.6, -15.65, -14.95), name="cockpit_column_1", p=(1.5, f, -15.3), top="globe",
           facing=(0, 0, -1))
    custom("crystal_lamp", solid=(-3.45, -2.85, f, f + 2.0, -21.05, -20.45), name="cockpit_crystal_lamp", p=(-3.15, f, -20.75))
    custom("wall_gauge", name="cockpit_clock", center=(-3.7, f + 1.5, ci.ROOMS["cockpit"][5] + 0.0), normal=(0, 0, -1), r=0.55)
    custom("wall_gauge", name="cockpit_gauge_1", center=(-3.7, f + 0.6, ci.ROOMS["cockpit"][5] + 0.0), normal=(0, 0, -1), r=0.28)
    custom("lever_bank", solid=(-3.98, -3.3, f, f + 0.9, -18.4, -17.4), name="cockpit_levers", p=(-3.64, f, -17.9), normal=(1, 0, 0))
    custom("speaking_tube", name="cockpit_tube", foot=(0.9, f, -15.2), top=(0.9, f + 1.3, -15.2), normal=(-1, 0, 0))
    # the chart table aft: two Furnish dark oak tables, two chairs, the charts and instruments on it
    for x in (-0.5, 0.5):
        at(FU + "dark_oak_table", x, f, -20.3, "stern")
    t = f + 1.0
    custom("chart_sheet", name="cockpit_chart", p=(0.0, t, -20.3), yaw=0.1, w=1.3, l=0.75)
    custom("compass", name="cockpit_compass", p=(-0.65, t, -20.0))
    custom("dividers", name="cockpit_dividers", p=(0.3, t + 0.01, -20.2), yaw=0.6)
    custom("map_roll", name="cockpit_map_roll", p=(0.75, t, -20.55), yaw=1.2, l=0.5)
    block(FD + "kerosene_lantern", -0.7, t, -20.6, "stern", solid=False)
    chair(FU + "mangrove_chair", -1.55, f, -20.3, "port", -2.45, -20.3)
    chair(FU + "mangrove_chair", 1.55, f, -20.3, "starboard", 2.45, -20.3)
    # bookcases against the rounded back wall (under the overhang), the globe, a telescope at a side window
    for x in (-1.5, 1.5):
        against_z(FD + "tall_bookshelf", x, f, ci.STERN_IN2 - 0.1, +1)
    custom("globe", solid=(3.0, 3.8, f, f + 1.3, -21.0, -20.2), name="cockpit_globe", p=(3.4, f, -20.6))
    custom("telescope", name="cockpit_telescope", p=(-3.5, f, -19.5), facing="starboard")
    # a co-pilot's chair by the starboard window, lanterns
    chair(FU + "mangrove_chair", -3.0, f, -16.4, "bow", -2.1, -16.4)
    for x, z in ((-2.6, -16.0), (2.6, -19.0), (0.0, -21.3)):
        hanging(x, CEIL_L2, z)
    custom("rug", name="cockpit_rug", p=(0.0, f, -17.2), w=2.2, l=1.8, region="in_rug_red")


def mess():
    """Carré des officiers (castle, storey 1): a long table and its chairs, a liquor cabinet and shelves, lanterns."""
    f = M0
    for x in (-0.5, 0.5):
        for z in (-20.5, -19.5, -18.5):
            at(FU + "dark_oak_table", x, f, z, "stern")
    custom("rug", name="mess_rug", p=(0.0, f, -19.5), w=4.2, l=4.6, region="in_rug_red")
    for z in (-20.5, -19.5, -18.5):
        chair(FD + "dining_chair", -1.55, f, z, "port", -2.45, z)
        chair(FD + "dining_chair", 1.55, f, z, "starboard", 2.45, z)
    chair(FD + "dining_chair", 0.0, f, -21.5, "bow", -0.95, -21.5)
    t = f + 1.0
    for k, (x, z) in enumerate(((-0.5, -20.6), (0.5, -20.4), (-0.5, -18.4), (0.5, -18.6), (-0.5, -19.5), (0.5, -19.5))):
        block(FU + "plate", x, t, z, "stern", solid=False, scale=0.55)
    block(FD + "red_wine_bottle", 0.05, t, -20.0, "stern", solid=False)
    block(FD + "wine_bottle", -0.1, t, -19.1, "stern", solid=False)
    for x, z in ((-0.75, -20.1), (0.75, -19.0), (-0.75, -18.9)):
        block(FD + "wine_glass", x, t, z, "stern", solid=False, scale=0.85)
    block(FR + "roast_chicken_block", 0.0, t, -19.6, "stern", solid=False, scale=0.6)
    for z in (-20.5, -18.5):
        hanging(0.0, CEIL_L1, z, drop=-0.3)
    against_z(FD + "liquor_cabinet", -2.45, f, MESS_BACK, +1)
    against_z(FD + "wall_shelf", 2.2, f, MESS_BACK, +1)
    block(FD + "pile_of_books", 2.2, f + 1.22, MESS_BACK + 0.3, "bow", solid=False)
    # by the door: a coat hanger, a chest of drawers with the gramophone
    at(FD + "coat_hanger", -3.9, f, -11.3, "port")
    i = against(FU + "dark_oak_cabinet", 1, f, -11.4)
    x0, x1, _, _, _, _ = footprint(BLOCKS[i])
    at(FD + "gramophone", (x0 + x1) / 2, f + 1.0, -11.4, "starboard", solid=False, scale=0.8)
    wall_lantern("mess_lantern_s", -1, f + 1.9, -17.0)
    wall_lantern("mess_lantern_p", 1, f + 1.9, -21.0)
    painting("mess_painting_s", "wanderer", (wall_x(f + 1.3, -20.0, -1) + 0.02, f + 1.3, -20.0), (1, 0, 0), 1.0, 1.0)


def lounge():
    """Salon (reference panel 2): red sofas round a low table on a red rug under the curio shelves, armchairs, the framed
    map, a card table, the piano, a second group of sofas aft, a liquor cabinet, lanterns; the big windows on both sides."""
    f = LO
    # forward: the long sofa against the bulkhead (starboard of the storeroom's door) under shelves of curios, a sofa along
    # the starboard wall, the low table on the rug, two armchairs facing the sofas
    zb = 10.0
    w = wall_x(f + 0.4, 9.5, -1)
    xs = [x for x in (-3.5, -2.5, -1.5, -0.5) if x - 0.5 > w - 0.05]
    for k, x in enumerate(xs):
        piece = "sofa_left" if k == 0 else "sofa_right" if k == len(xs) - 1 else "sofa_middle"
        bid = FD + piece
        x0, x1, _, _, z0, z1 = _footprint(bid, 0.0, 0.0, 0.0, FACING["stern"])
        at(bid, x, f, zb - 0.02 - (z1 - z0) / 2, "stern", solid=False)
        seat(x, f + 0.3, zb - 0.5, x, f + 0.02, zb - 1.35)
    for k, x in enumerate(xs[:3]):
        against_z(FD + "wall_shelf", x, f + 1.0, zb, -1, solid=False)
    sofa(-1, f, 5.0, 3, "lounge_sofa_s")
    custom("rug", name="lounge_rug_fwd", p=(-1.8, f, 7.1), w=4.6, l=4.4, region="in_rug_red")
    at(FD + "coffee_table", -2.1, f, 7.2, "stern")
    block(FD + "kerosene_lantern", -2.3, f + 0.5, 7.0, "stern", solid=False)
    block(FU + "book_pile", -1.9, f + 0.5, 7.5, "stern", solid=False, scale=0.6)
    chair(FU + "mangrove_chair", -0.4, f, 6.6, "starboard", 0.5, 6.6)
    chair(FU + "mangrove_chair", -0.4, f, 7.8, "starboard", 0.5, 7.8)
    custom("world_map", name="lounge_map", center=(wall_x(f + 1.9, 9.1, -1) + 0.02, f + 1.95, 9.1), normal=(1, 0, 0), w=1.2, h=0.9)
    # port, forward: the piano against the wall, its stool; the card table and its chairs
    against(FD + "piano", 1, f, 9.0)
    chair(FU + "dark_oak_stool", 2.8, f, 8.9, "port", 2.0, 8.4)
    at(FU + "dark_oak_pedestal_table", 2.6, f, 4.6, "stern")
    block(FU + "chess_board", 2.6, f + 1.0, 4.6, "stern", solid=False, scale=0.8)
    chair(FU + "mangrove_chair", 2.6, f, 3.65, "bow", 1.6, 3.6)
    chair(FU + "mangrove_chair", 2.6, f, 5.55, "stern", 1.6, 5.6)
    # aft: a sofa of four pieces along the port wall, its low table and armchairs on a rug
    sofa(1, f, -5.0, 4, "lounge_sofa_p")
    custom("rug", name="lounge_rug_aft", p=(2.0, f, -3.0), w=3.4, l=4.6, region="in_rug_red")
    at(FD + "coffee_table", 2.05, f, -3.0, "stern")
    block(FD + "wine_bottle", 1.9, f + 0.5, -3.2, "stern", solid=False)
    block(FD + "wine_glass", 2.2, f + 0.5, -2.8, "stern", solid=False, scale=0.85)
    chair(FU + "mangrove_chair", 1.0, f, -3.7, "port", 0.1, -3.7)
    chair(FU + "mangrove_chair", 1.0, f, -2.3, "port", 0.1, -2.3)
    # starboard, aft: the liquor cabinet on the aft bulkhead, bookcases, a rocking chair by the window, a lamp
    against_z(FD + "liquor_cabinet", -3.0, f, -7.0, +1)
    against(FD + "tall_bookshelf", -1, f, -6.5)
    chair(FD + "rocking_chair", -3.2, f, -2.6, "port", -2.0, -2.6)
    against(FD + "night_stand", -1, f, -4.4)
    block(FD + "lamp", wall_x(f + 0.3, -4.4, -1) + 0.4, f + 0.63, -4.4, "stern", solid=False, scale=0.8)
    # the middle: a round table with two chairs on the starboard side, the aisle along the port side of it
    at(FD + "round_table", -2.6, f, 1.0, "stern")
    block(FD + "pile_of_books", -2.6, f + 1.0, 1.0, "stern", solid=False)
    chair(FD + "dining_chair", -3.6, f, 1.0, "port", -3.6, 2.2)
    chair(FD + "dining_chair", -1.6, f, 1.0, "starboard", -1.6, 2.2)
    # lanterns hanging from the ceiling, on the walls between the windows
    for x, z in ((-2.0, 7.0), (2.4, -3.0), (0.0, 1.0), (2.8, 4.6), (-2.6, -3.0), (-2.6, 1.0)):
        hanging(x, CEIL_LO, z, drop=-0.25)
    for side in (-1, 1):
        for z in (-0.5, 2.5):
            wall_lantern("lounge_lantern_%d_%d" % (side > 0, int(z * 10)), side, f + 2.6, z)
    painting("lounge_painting_p", "sea", (wall_x(f + 2.0, -6.5, 1) - 0.02, f + 2.0, -6.5), (-1, 0, 0), 0.9, 0.9)


def storeroom():
    """Réserve (reference panel 4): crates, barrels, sacks, shelves, chains hanging from the ceiling, lanterns."""
    f = LO
    for z in (11.5, 12.5):
        against(FU + "spruce_crate", -1, f, z)
    against(FU + "dark_oak_crate", -1, f + 1.0, 11.5)
    against(FR + "potato_crate", 1, f, 11.5)
    against(FR + "carrot_crate", 1, f, 12.5)
    against(FR + "onion_crate", 1, f + 1.0, 11.5)
    at(FU + "spruce_crate", 0.0, f, 15.2, "stern")
    at(FU + "spruce_crate", 0.0, f + 1.0, 15.2, "stern", scale=0.7)
    against(IC + "cypress_barrel", -1, f, 14.3, facing="port")
    against(IC + "loaded_cypress_barrel", 1, f, 14.3, facing="starboard")
    against(FR + "rice_bag", -1, f, 15.8)
    against(FR + "wooden_basket", 1, f, 15.8)
    for k, (x, z) in enumerate(((-1.2, 17.6), (1.1, 17.4))):
        custom("barrel", solid=(x - 0.38, x + 0.38, f, f + 0.95, z - 0.38, z + 0.38), name="store_barrel_%d" % k, p=(x, f, z))
    for k, (x, z, yaw) in enumerate(((-2.2, 13.6, 0.3), (2.1, 13.5, -0.4), (0.2, 18.4, 1.0))):
        custom("sack", name="store_sack_%d" % k, p=(x, f, z), yaw=yaw)
    for side in (-1, 1):
        for k, z in enumerate((12.0, 14.0)):
            w = wall_x(f + 2.2, z, side)
            block(FU + "spruce_shelf", w - side * 0.17, f + 2.0, z, "starboard" if side > 0 else "port", solid=False)
    for k, (x, z, L) in enumerate(((-1.0, 13.0, 1.4), (-0.6, 13.3, 1.0), (1.2, 16.5, 1.2), (0.9, 12.2, 0.8))):
        custom("hanging_chain", name="store_chain_%d" % k, top=(x, CEIL_LO, z), length=L)
    hanging(0.0, CEIL_LO, 12.0, drop=-0.25)
    hanging(0.0, CEIL_LO, 16.8, drop=-0.25)


def hold():
    f = HO
    for z in (-3.5, -2.5, -1.5):
        against(FU + "spruce_crate", -1, f, z)
    against(FU + "dark_oak_crate", -1, f + 1.0, -2.5)
    for z in (-2.0, -1.0):
        against(FR + "cabbage_crate", 1, f, z)
    against(FR + "straw_bale", 1, f, 0.5)
    against(FR + "rice_bag", -1, f, 0.5)
    for k, (x, z) in enumerate(((-1.3, 2.6), (0.0, 3.1), (1.3, 2.6))):
        custom("barrel", solid=(x - 0.38, x + 0.38, f, f + 0.95, z - 0.38, z + 0.38), name="hold_barrel_%d" % k, p=(x, f, z))
    custom("sack", name="hold_sack_0", p=(-1.2, f, -4.6), yaw=0.4)
    hanging(0.0, CEIL_HO, -1.0, drop=-0.3)


def engine_room():
    """Salle des machines (reference panel 3): the crystal engine (generate_crystal.crystal_engine), pipes of bronze from
    the dwarven automatons' mod along the walls, metal boxes, the workbench, gauges, lanterns, crystal lamps."""
    f = LO
    # the landing: the workbench on the bulkhead (starboard), lockers and dwarven metal boxes (port), a stool
    against_z(FD + "workbench", -3.0, f, -7.5, -1)
    block(FD + "tool_board", -3.0, f + 1.25, -7.6, "stern", solid=False)
    for x in (2.6, 3.6):
        against_z(MB + "dwemer_metal_block", x, f, -7.5, -1)
    against_z(MB + "dwemer_metal_pipe_gear", 3.1, f + 1.0, -7.5, -1, solid=False)
    chair(FU + "spruce_stool", -1.6, f, -8.6, "stern", -1.6, -9.5)
    custom("crystal_lamp", solid=(1.45, 2.05, f, f + 2.0, -8.6, -8.0), name="engine_crystal_lamp_0", p=(1.75, f, -8.3))
    # the floor: dwarven pipes along both walls, crates in the corners, gauges, crystal lamps
    h = HO
    for z in (-12.0, -13.0):          # the starboard wall (the stair down runs along the port wall)
        w = max(wall_x(h + 0.1, z - 0.4, -1), wall_x(h + 0.1, z + 0.4, -1))
        block(MB + "dwemer_metal_pipe", w + 0.42, h, z, "bow", solid=True)
    w = wall_x(h + 1.6, -12.5, -1)
    block(MB + "dwemer_metal_pipe_gear", w + 0.42, h + 1.0, -12.5, "bow", solid=False)
    at(FU + "dark_oak_crate", -2.15, ci.PLINTH[2], -19.6, "stern")
    at(FU + "small_locker", 2.15, ci.PLINTH[2], -19.6, "stern")
    custom("gauge_board", name="engine_gauges_s", center=(wall_x(h + 2.4, -15.5, -1) + 0.02, h + 2.4, -15.5), normal=(1, 0, 0), w=1.2, h=0.8)
    custom("gauge_board", name="engine_gauges_p", center=(wall_x(h + 2.4, -16.8, 1) - 0.02, h + 2.4, -16.8), normal=(-1, 0, 0), w=1.2, h=0.8)
    for side in (-1, 1):
        wall_lantern("engine_lantern_%d" % (side > 0), side, f + 2.2, -14.0)
    hanging(0.0, CEIL_LO, -9.3, drop=-0.25)
    hanging(0.0, CEIL_LO, -12.8, drop=0.6)


def main_deck():
    """Pont principal: benches along the bulwarks, barrels, crates and coils of rope; the forecastle's telescope."""
    f = M0
    for side in (-1, 1):
        for z in (-5.0, -4.0, 3.0, 4.0):
            w = cs.hull_x(z, 0.5) - cs.SHELL - 0.2
            x = side * (w - 0.6)
            chair(FU + "dark_oak_bench", x, f, z, "stern", x - side * 0.9, z)
    for k, (x, z) in enumerate(((-4.0, 7.2), (-3.2, 7.8))):
        custom("barrel", solid=(x - 0.38, x + 0.38, f, f + 0.95, z - 0.38, z + 0.38), name="deck_barrel_%d" % k, p=(x, f, z))
    at(FU + "spruce_crate", 4.0, f, 7.5, "stern")
    at(FU + "spruce_crate", 4.0, f + 1.0, 7.5, "stern", scale=0.75)
    custom("rope_coil", name="deck_rope_0", p=(3.3, f, -7.0), r=0.4)
    custom("rope_coil", name="deck_rope_1", p=(-3.5, f, 0.8), r=0.36)
    fc = cs.FORECASTLE_Y
    custom("telescope", name="fc_telescope", p=(0.0, fc, 20.8), facing="bow")
    custom("rope_coil", name="fc_rope", p=(-1.6, fc, 18.0), r=0.4)
    at(FU + "spruce_crate", 1.8, fc, 17.6, "stern")


def build():
    BLOCKS.clear()
    SEATS.clear()
    CUSTOM.clear()
    PAINTINGS.clear()
    SWITCHES.clear()
    cockpit()
    mess()
    lounge()
    storeroom()
    hold()
    engine_room()
    main_deck()
    return BLOCKS, SEATS


def footprint(b):
    return _footprint(b["block"], b["x"], b["y"], b["z"], b["yaw"], b["scale"])


def apply_to_grid(g):
    """Solid cells for the footprints of the solid furniture."""
    for builder, kwargs, solid in CUSTOM:
        if solid is not None:
            x0, x1, y0, y1, z0, z1 = solid
            g.set(ci.FURNITURE, x0 + 0.05, x1 - 0.05, y0 + 0.01, y1, z0 + 0.05, z1 - 0.05, where=(g.k == ci.DRY) | (g.k == ci.OUT))
    for b in BLOCKS:
        if not b["solid"]:
            continue
        x0, x1, y0, y1, z0, z1 = footprint(b)
        g.set(ci.FURNITURE, x0 + 0.05, x1 - 0.05, b["y"] + 0.01, y1, z0 + 0.05, z1 - 0.05, where=(g.k == ci.DRY) | (g.k == ci.OUT))


def write(path):
    data = {"blocks": [], "seats": [{k: round(v, 4) for k, v in s.items()} for s in SEATS],
            "paintings": [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in q.items()} for q in PAINTINGS], "switches": SWITCHES}
    for i, b in enumerate(BLOCKS):
        data["blocks"].append({"block": b["block"], "x": round(b["x"], 4), "y": round(b["y"], 4), "z": round(b["z"], 4),
                               "yaw": b["yaw"], "scale": b["scale"], "fallback": "fallback_%d" % i})
    with open(path, "w") as f:
        json.dump(data, f, indent=1)


DECOR_PATH = "src/main/resources/assets/medievalships/interiors/crystal_airship_decor.json"

if __name__ == "__main__":
    build()
    g = ci.build()
    apply_to_grid(g)
    reached, total = ci.walkable_report(g)
    print("blocks", len(BLOCKS), "seats", len(SEATS), "custom", len(CUSTOM), "standing", total)
    for name, n in reached.items():
        print("  %-16s %s" % (name, n if n else "UNREACHABLE"))
