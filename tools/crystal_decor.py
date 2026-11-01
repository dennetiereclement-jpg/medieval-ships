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

import numpy as np

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
    FD + "standing_lamp": (0.188, 0.812, -0.048, 2.0, 0.188, 0.812),
    FU + "oak_crate": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FR + "tomato_crate": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    IC + "brown_storage_vase": (0.062, 0.938, 0.0, 1.0, 0.062, 0.938),
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
    FD + "standing_lamp": "in_lamp", FU + "oak_crate": "crate", FR + "tomato_crate": "crate", IC + "cypress_rack": "in_beam",
    FD + "night_stand": "in_wood_carved", FD + "cuckoo_clock": "in_wood_carved", IC + "brown_storage_vase": "in_brick",
})
GLOWING_FALLBACK = ld.GLOWING_FALLBACK + (FD + "lamp", FD + "standing_lamp")
nd.BOUNDS = BOUNDS   # nd.to_ship does not read it, footprints below do

BLOCKS = []    # dicts: block, x, y, z, yaw, solid, scale
SEATS = []     # dicts: x, y, z, dx, dy, dz
CUSTOM = []    # furniture made for the airship: (builder name, kwargs, solid box or None)
PAINTINGS = []
SWITCHES = []

M0, LO, HO, L2 = ci.M0, ci.LO, ci.HO, ci.L2
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


def back_wall_z(y0, y1, x0, x1, z_from):
    """Inner face of the wall aft of a piece spanning x0..x1 and y0..y1, scanning aft from z_from (the stern is round:
    the back wall comes forward towards the sides)."""
    g = grid()
    l = int(math.floor((z_from - ci.Z0) / ci.CELL))
    i0, i1 = int(math.floor((x0 + 0.05 - ci.X0) / ci.CELL)), int(math.floor((x1 - 0.05 - ci.X0) / ci.CELL))
    j0, j1 = int(math.floor((y0 + 0.05 - ci.Y0) / ci.CELL)), int(math.floor((y1 - 0.05 - ci.Y0) / ci.CELL))
    while l > 0:
        cells = g.k[i0:i1 + 1, j0:j1 + 1, l]
        if np.isin(cells, (ci.SOLID, ci.OUT, ci.WINDOW)).any():
            return ci.Z0 + (l + 1) * ci.CELL
        l -= 1
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
def beams_across(name, y_ceil, zs, side_y=None, carved=False, w=0.3, h=0.3):
    """Ceiling beams across a room at each z (from wall to wall, under the ceiling at y_ceil)."""
    yy = y_ceil - 0.2 if side_y is None else side_y
    for k, z in enumerate(zs):
        a, b = wall_x(yy, z, -1), wall_x(yy, z, 1)
        if a is None or b is None:
            continue
        custom("ceiling_beam", name="%s_beam_%d" % (name, k), x0=a + 0.01, x1=b - 0.01, y=y_ceil, z=z, w=w, h=h, carved=carved)


def cockpit():
    """Poste de pilotage (reference panel 1): the great wheel facing the arched window between brass instrument columns (a
    big chronometer on the port one, a green glass dome on the starboard one), the tall blue crystal lamp beside it,
    lanterns flanking the arch and hanging under it, a big wall clock, gauge boards and brass pipes on the stone walls,
    timber posts and ceiling beams, sills under the side windows; the chart table aft, bookcases, the globe, a telescope."""
    f = L2
    zf = ci.ROOMS["cockpit"][5]          # the front wall's face (the arch)
    custom("instrument_column", solid=(1.1, 1.8, f, f + 1.6, -15.6, -14.9), name="cockpit_column_0", p=(1.45, f, -15.25), top="clock",
           facing=(0, 0, -1), h=1.15)
    custom("instrument_column", solid=(-1.7, -1.0, f, f + 1.6, -15.75, -15.05), name="cockpit_column_1", p=(-1.35, f, -15.4), top="gem",
           facing=(0, 0, -1), h=1.2)
    custom("crystal_lamp", solid=(-2.45, -1.85, f, f + 2.1, -15.1, -14.55), name="cockpit_crystal_lamp", p=(-2.15, f, -14.85), h=1.55, r=0.2)
    # the big wall clock over the stair's opening (port of the arch), a gauge under it
    custom("wall_gauge", name="cockpit_clock", center=(3.3, f + 1.85, zf), normal=(0, 0, -1), r=0.5)
    custom("wall_gauge", name="cockpit_gauge_1", center=(3.3, f + 1.05, zf), normal=(0, 0, -1), r=0.24)
    # lanterns flanking the arch (on the front wall) and hanging in it
    wall_lantern_z("cockpit_lantern_arch_p", 2.75, f + 2.45, zf, -1)
    wall_lantern_z("cockpit_lantern_arch_s", -2.72, f + 2.45, zf, -1)
    hanging(0.0, CEIL_L2, -14.95, drop=0.05)
    # the starboard wall: the lever bank under a gauge board, a pipe along the wall into it
    xv = wall_x(f + 0.5, -17.9, -1) + 0.02
    custom("lever_bank", solid=(xv, xv + 0.68, f, f + 0.9, -18.4, -17.4), name="cockpit_levers", p=(xv + 0.34, f, -17.9), normal=(1, 0, 0))
    xg = wall_x(f + 1.6, -17.9, -1)
    custom("gauge_board", name="cockpit_gauges_s", center=(xg + 0.02, f + 1.55, -17.9), normal=(1, 0, 0), w=1.0, h=0.7)
    xp = wall_x(f + 2.5, -18.0, -1) + 0.16
    custom("pipe", name="cockpit_pipe_s", pts=[(xp, f + 2.55, -21.0), (xp, f + 2.55, -16.9), (xp, f + 1.95, -16.9)], d=0.16,
           region="in_brass_pol", flange="in_gold")
    # the port wall aft of the stair: the speaking tube, a gauge board, a pipe
    xs = wall_x(f + 0.5, -19.2, 1) - 0.12
    custom("speaking_tube", name="cockpit_tube", foot=(xs, f, -19.2), top=(xs, f + 1.4, -19.2), normal=(-1, 0, 0))
    xq = wall_x(f + 2.5, -18.4, 1) - 0.16
    custom("pipe", name="cockpit_pipe_p", pts=[(xq, f + 2.55, -21.0), (xq, f + 2.55, -18.7), (xs, f + 1.6, -19.2)], d=0.16,
           region="in_brass_pol", flange="in_gold")
    # sills under the side windows, an hourglass and a compass on them
    for side in (-1, 1):
        for k, (z0, z1) in enumerate(ci.COCKPIT_WINDOWS):
            w = wall_x(ci.COCKPIT_WIN_Y[0] + 0.3, (z0 + z1) / 2, side)
            custom("timber", name="cockpit_sill_%d_%d" % (side > 0, k), a=(w - side * 0.14, ci.COCKPIT_WIN_Y[0] - 0.06, z0 - 0.1),
                   b=(w - side * 0.14, ci.COCKPIT_WIN_Y[0] - 0.06, z1 + 0.1), w=0.12, d=0.3, region="in_wood_carved")
    ws = wall_x(ci.COCKPIT_WIN_Y[0] + 0.3, -15.75, -1)
    custom("hourglass", name="cockpit_hourglass", p=(ws + 0.16, ci.COCKPIT_WIN_Y[0], -15.5))
    # timber posts at the corners and between the side windows, beams across the ceiling
    for side in (-1, 1):
        for k, z in enumerate((-14.75, -17.25, -19.75)):
            if side > 0 and z > -18.0:
                continue          # the stair's opening
            w = wall_x(f + 1.0, z, side)
            custom("wall_post", name="cockpit_post_%d_%d" % (side > 0, k), p=(w, f, z), h=CEIL_L2 - f, normal=(-side, 0, 0), w=0.28, d=0.16,
                   collars=True, region="in_beam")
    beams_across("cockpit", CEIL_L2, (-16.1, -18.2, -20.2, -22.0), w=0.32, h=0.26)
    custom("helm_dais", name="cockpit_dais", p=(0.0, f, cs.HELM_Z), r=0.72)
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
        against_z(FD + "tall_bookshelf", x, f, back_wall_z(f, f + 2.0, x - 0.5, x + 0.5, -20.0), +1)
    xg = min(3.4, wall_x(f + 0.5, -20.6, 1) - 0.5)
    custom("globe", solid=(xg - 0.4, xg + 0.4, f, f + 1.3, -21.0, -20.2), name="cockpit_globe", p=(xg, f, -20.6))
    custom("telescope", name="cockpit_telescope", p=(wall_x(f + 0.5, -19.5, -1) + 0.6, f, -19.5), facing="starboard")
    # a co-pilot's chair by the starboard window, lanterns
    xc = wall_x(f + 0.5, -16.4, -1) + 0.75
    chair(FU + "mangrove_chair", xc, f, -16.4, "bow", xc + 0.9, -16.4)
    for x, z in ((-2.6, -18.5), (2.6, -18.6), (0.0, -21.0)):
        hanging(x, CEIL_L2, z)


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
    zc = back_wall_z(f, f + 1.0, -3.45, -1.45, -20.0)
    against_z(FD + "liquor_cabinet", -2.45, f, zc, +1)
    zs = back_wall_z(f, f + 1.5, 1.5, 2.5, -20.0)
    against_z(FD + "wall_shelf", 2.0, f, zs, +1)
    block(FD + "pile_of_books", 2.0, f + 1.22, zs + 0.3, "bow", solid=False)
    # by the door: a coat hanger, a chest of drawers with the gramophone
    at(FD + "coat_hanger", -3.9, f, -11.3, "port")
    i = against(FU + "dark_oak_cabinet", 1, f, -11.4)
    x0, x1, _, _, _, _ = footprint(BLOCKS[i])
    at(FD + "gramophone", (x0 + x1) / 2, f + 1.0, -11.4, "starboard", solid=False, scale=0.8)
    wall_lantern("mess_lantern_s", -1, f + 1.9, -17.0)
    wall_lantern("mess_lantern_p", 1, f + 1.9, -21.0)
    painting("mess_painting_s", "wanderer", (wall_x(f + 1.3, -20.0, -1) + 0.02, f + 1.3, -20.0), (1, 0, 0), 1.0, 1.0)


def sofa_z(y, zw, x0, n, nz, name):
    """A Farmhouse sofa of n pieces with its back to a transverse wall at z = zw (facing nz: -1 aft, +1 forward), from x0
    towards +x, its seats."""
    facing = "stern" if nz < 0 else "bow"
    for k in range(n):
        x = x0 + 0.5 + k
        if n == 1:
            piece = "sofa_middle"
        elif k == 0:
            piece = "sofa_left" if nz < 0 else "sofa_right"
        elif k == n - 1:
            piece = "sofa_right" if nz < 0 else "sofa_left"
        else:
            piece = "sofa_middle"
        bid = FD + piece
        _, _, _, _, z0, z1 = _footprint(bid, 0.0, 0.0, 0.0, FACING[facing])
        at(bid, x, y, zw + nz * (0.02 + (z1 - z0) / 2), facing, solid=False)
        seat(x, y + 0.3, zw + nz * 0.5, x, y + 0.02, zw + nz * 1.35)


def armchair(x, f, z, facing, dx, dz, name):
    """The lounge's tufted red velvet armchair (crystal_furniture.armchair) and its seat."""
    custom("armchair", name=name, p=(x, f, z), facing=facing)
    seat(x, f + 0.33, z, dx, f + 0.02, dz)


def lounge():
    """Salon (reference panel 2): the forward salon in the starboard bow corner, as on the sheet: a long red sofa under the
    carved curio wall (shelves of books, bottles and curios), a red sofa along the windows, crimson armchairs, the low
    table on the red rug under a hanging lantern, the framed map; along the port side bookcases between the windows, the
    piano, a card table; aft a second group of sofas round a low table, a bar (liquor cabinet, stools), a rocking chair by
    a window, a gramophone; carved beams with gilded scrolls across the coffered ceiling, lanterns between the windows."""
    f = LO
    zb = 10.0
    # ---- forward salon (starboard): long sofa against the bulkhead, the curio wall over it
    xs = [x for x in (-4.5, -3.5, -2.5, -1.5) if x - 0.0 > wall_x(f + 0.4, 9.5, -1) + 0.05]
    sofa_z(f, zb, xs[0] - 0.5, len(xs), -1, "lounge_sofa_fwd")
    for row, y in enumerate((f + 0.95, f + 2.12)):
        for k, x in enumerate((-3.5, -2.5, -1.5)):
            against_z(FD + "wall_shelf", x, y, zb, -1, solid=False)
    custom("curio_frame", name="lounge_curio", p=(-2.5, f + 0.92, zb), normal=(0, 0, -1), w=3.05, h=2.42, crest=False)
    block(FD + "cuckoo_clock", -4.42, f + 1.85, zb - 0.6, "stern", solid=False)
    # along the starboard windows: a sofa of four pieces, lanterns between the windows, the framed map forward
    sofa(-1, f, 4.6, 4, "lounge_sofa_s")
    custom("world_map", name="lounge_map", center=(wall_x(f + 2.2, 9.25, -1) + 0.02, f + 2.15, 9.25), normal=(1, 0, 0), w=0.95, h=0.8)
    custom("rug", name="lounge_rug_fwd", p=(-2.6, f, 6.9), w=4.0, l=4.6, region="in_rug_red")
    at(FD + "coffee_table", -2.7, f, 7.3, "stern")      # clear of the sofas' dismount places
    block(FD + "kerosene_lantern", -2.9, f + 0.5, 7.15, "stern", solid=False)
    block(FU + "book_pile", -2.45, f + 0.5, 7.55, "stern", solid=False, scale=0.6)
    block(FD + "wine_glass", -2.8, f + 0.5, 7.7, "stern", solid=False, scale=0.85)
    armchair(-4.0, f, 3.75, math.pi / 4, -3.3, 3.0, "lounge_armchair_0")
    hanging(-2.7, CEIL_LO, 7.2, drop=0.15)
    # ---- port, forward: bookcases between the windows, the piano, a card table with its chairs, a globe
    for z in (4.0, 6.5):
        against(FD + "tall_bookshelf", 1, f, z)
    against(FD + "piano", 1, f, 8.6)
    chair(FU + "dark_oak_stool", 3.9, f, 8.6, "port", 3.1, 8.0)
    at(FU + "dark_oak_pedestal_table", 2.75, f, 5.3, "stern")
    block(FU + "chess_board", 2.75, f + 1.0, 5.3, "stern", solid=False, scale=0.8)
    chair(FU + "mangrove_chair", 2.75, f, 4.4, "bow", 1.75, 4.4)
    chair(FU + "mangrove_chair", 2.75, f, 6.2, "stern", 1.75, 6.2)
    hanging(2.75, CEIL_LO, 5.3, drop=0.1)
    # ---- the middle (kept free for the aisle): a round table with books on the starboard side, the bar on the port side
    at(FD + "round_table", -2.9, f, 1.5, "stern")
    block(FD + "pile_of_books", -2.9, f + 1.0, 1.4, "stern", solid=False)
    block(FD + "kerosene_lantern", -2.65, f + 1.0, 1.75, "stern", solid=False)
    chair(FD + "dining_chair", -3.9, f, 1.5, "port", -3.9, 2.6)
    chair(FD + "dining_chair", -1.9, f, 1.5, "starboard", -1.9, 2.6)
    against(FD + "tall_bookshelf", 1, f, 1.5)
    against(FD + "liquor_cabinet", 1, f, -0.5)
    block(FD + "red_wine_bottle", wall_x(f + 0.5, -0.5, 1) - 0.4, f + 1.0, -0.95, "stern", solid=False)
    block(FD + "wine_glass", wall_x(f + 0.5, -0.5, 1) - 0.4, f + 1.0, -0.6, "stern", solid=False, scale=0.85)
    for z in (-1.0, 0.0):
        chair(FU + "dark_oak_stool", 3.3, f, z, "port", 2.5, z)
    # ---- aft: a second group of sofas round a low table (starboard), armchairs; a rocking chair, the gramophone (port)
    sofa(-1, f, -5.5, 3, "lounge_sofa_aft")
    custom("rug", name="lounge_rug_aft", p=(-2.7, f, -4.0), w=3.8, l=3.8, region="in_rug_red")
    at(FD + "coffee_table", -2.15, f, -4.0, "stern")    # clear of the sofa's dismount places
    block(FD + "wine_bottle", -2.25, f + 0.5, -4.2, "stern", solid=False)
    block(FU + "chess_board", -2.05, f + 0.5, -3.8, "stern", solid=False, scale=0.6)
    armchair(-1.0, f, -4.75, "starboard", -0.1, -4.75, "lounge_armchair_2")
    armchair(-1.0, f, -3.25, "starboard", -0.1, -3.25, "lounge_armchair_3")
    hanging(-2.15, CEIL_LO, -4.0, drop=0.15)
    against_z(FD + "tall_bookshelf", -3.4, f, -7.0, +1)
    against_z(FD + "tall_bookshelf", -2.4, f, -7.0, +1)
    against_z(FD + "tall_bookshelf", 3.4, f, -7.0, +1)
    at(FD + "standing_lamp", -4.45, f, -6.4, "stern", solid=False)
    chair(FD + "rocking_chair", 3.6, f, -3.0, "starboard", 2.4, -3.0)
    against(FD + "night_stand", 1, f, -4.6)
    block(FD + "gramophone", wall_x(f + 0.3, -4.6, 1) - 0.36, f + 0.62, -4.6, "starboard", solid=False, scale=0.65)
    painting("lounge_painting_p", "sea", (wall_x(f + 2.2, -6.0, 1) - 0.02, f + 2.2, -6.0), (-1, 0, 0), 0.9, 0.9)
    # ---- lanterns between the windows (both walls), carved beams across the ceiling
    for side, zs in ((-1, (-3.5, -1.0, 1.5, 4.0, 6.5)), (1, (-3.5, -1.0))):     # the piers between the windows without a bookcase
        for z in zs:
            wall_lantern("lounge_lantern_%d_%d" % (side > 0, int(round(z * 10))), side, f + 2.75, z)
    beams_across("lounge", CEIL_LO, (-5.5, -2.5, 0.5, 3.5, 5.75, 8.5), carved=True, w=0.3, h=0.32)
    for x, z in ((0.0, -1.0), (0.0, 2.0)):
        hanging(x, CEIL_LO, z, drop=-0.1)


def storeroom():
    """Réserve (reference panel 4), in the round bow: stone walls between timber posts, beams overhead; crates of
    vegetables under its four windows, stacks of crates two high between and forward of them, upright and lying barrels,
    plump sacks and sacks of rice, shelves of jars and bottles, a big crate in the middle and a workbench, chains with
    hooks hanging from the beams, lanterns."""
    f = LO
    # under the windows (the windows run from f + 1 to f + 3): one crate high
    against(FR + "potato_crate", 1, f, 11.1)
    against(FR + "carrot_crate", 1, f, 12.1)
    against(FU + "spruce_crate", -1, f, 11.1)
    against(FR + "cabbage_crate", -1, f, 12.1)
    against(FR + "onion_crate", 1, f, 13.5)
    against(FR + "beetroot_crate", -1, f, 13.5)
    # forward of the windows: stacks of crates two high, a small crate on top, then barrels
    for side in (-1, 1):
        against(FU + "dark_oak_crate", side, f, 14.75)
        against(FU + "spruce_crate", side, f + 1.0, 14.75)
        against(FR + "tomato_crate" if side > 0 else FR + "potato_crate", side, f, 15.75)
        against(FU + "oak_crate", side, f + 1.0, 15.75, scale=0.75)
    # lying barrels on their racks against the curved bow
    for side, z in ((-1, 16.85), (1, 16.85)):
        w = wall_min(f, f + 1.2, z, side)
        x = w - side * 0.55
        at(IC + "cypress_rack", x, f, z, "stern", solid=False)
        at(IC + "loaded_fir_barrel" if side > 0 else IC + "cypress_barrel", x, f + 0.12, z, "stern")
    # upright barrels, sacks along the curved forward wall
    for k, (x, z) in enumerate(((-2.4, 18.05), (2.35, 18.05), (-1.4, 18.75), (1.35, 18.75))):
        custom("barrel", solid=(x - 0.38, x + 0.38, f, f + 0.95, z - 0.38, z + 0.38), name="store_barrel_%d" % k, p=(x, f, z))
    custom("barrel", solid=(-1.78, -1.02, f + 0.95, f + 1.9, 18.37, 19.13), name="store_barrel_top", p=(-1.4, f + 0.95, 18.75), r=0.33, h=0.85)
    at(FR + "rice_bag", -0.35, f, 19.0, "stern")
    at(FR + "rice_bag", 0.45, f, 19.05, "stern", scale=0.8)
    for k, (x, z, yaw, s) in enumerate(((-3.1, 17.45, 0.3, 1.35), (3.05, 17.5, -0.4, 1.3), (0.55, 18.2, 1.0, 1.0), (-0.6, 18.25, -0.6, 1.1),
                                        (3.15, 10.95, 0.6, 1.3), (-2.15, 11.05, 0.2, 1.2), (2.75, 14.4, -0.3, 1.25))):
        custom("plump_sack", name="store_sack_%d" % k, p=(x, f, z), yaw=yaw, s=s)
    # shelves of jars and bottles on the walls over the crate stacks, a jar shelf unit by the door
    for side in (-1, 1):
        for k, (z, y) in enumerate(((15.75, f + 2.1), (16.75, f + 2.1), (15.75, f + 2.7), (16.75, f + 2.7))):
            w = wall_x(y + 0.15, z, side)
            block(FU + "spruce_shelf", w - side * 0.17, y, z, "starboard" if side > 0 else "port", solid=False)
            if k < 2:
                block(FD + "wine_bottle", w - side * 0.2, y + 0.25, z - 0.25, "stern", solid=False)
                block(FD + "red_wine_bottle", w - side * 0.2, y + 0.25, z + 0.05, "stern", solid=False)
                block(FD + "pile_of_books", w - side * 0.2, y + 0.25, z + 0.3, "stern", solid=False, scale=0.8)
            else:
                block(IC + "brown_storage_vase", w - side * 0.24, y + 0.25, z, "stern", solid=False, scale=0.42)
    custom("jar_shelf", solid=(-3.8, -2.6, f, f + 1.9, 10.5, 10.9), name="store_jars", p=(-3.2, f, 10.5), normal=(0, 0, 1), w=1.2, h=1.85, rows=4)
    # the middle: a big crate under a lantern (as on the sheet), stacks of crates either side of it, the workbench
    # forward, upright barrels and plump sacks by the windows
    at(FU + "spruce_crate", 0.0, f, 15.9, "stern")
    for side in (-1, 1):
        at(FU + "dark_oak_crate", side * 2.1, f, 15.6, "stern")
        at(FU + "spruce_crate", side * 2.1, f + 1.0, 15.6, "stern", scale=0.8)
        custom("plump_sack", name="store_sack_mid_%d" % (side > 0), p=(side * 2.15, f, 16.7), yaw=0.4 * side, s=1.25)
    at(FD + "workbench", 0.0, f, 17.45, "stern")
    for k, (x, z) in enumerate(((3.3, 13.45), (-3.3, 13.45))):
        custom("barrel", solid=(x - 0.4, x + 0.4, f, f + 1.05, z - 0.4, z + 0.4), name="store_barrel_win_%d" % k, p=(x, f, z), r=0.4, h=1.05)
    # timber posts between the windows and at the bow, beams across, chains with hooks, lanterns
    for side in (-1, 1):
        for k, z in enumerate((12.75, 14.25, 16.3)):
            w = wall_x(f + 2.6, z, side)
            custom("wall_post", name="store_post_%d_%d" % (side > 0, k), p=(w, f, z), h=CEIL_LO - f, normal=(-side, 0, 0), w=0.3, d=0.18)
    beams_across("store", CEIL_LO, (12.75, 14.25, 16.3, 18.4), w=0.32, h=0.3)
    for k, (x, z, L) in enumerate(((-1.6, 13.4, 1.3), (-1.2, 11.8, 0.9), (1.7, 17.3, 1.1), (1.4, 11.9, 0.8), (-1.6, 15.3, 1.2), (2.3, 15.2, 1.0))):
        custom("hanging_chain", name="store_chain_%d" % k, top=(x, CEIL_LO, z), length=L)
    hanging(0.0, CEIL_LO, 13.5, drop=0.05)
    hanging(0.0, CEIL_LO, 15.6, drop=0.05)
    hanging(-2.6, CEIL_LO, 17.4, drop=-0.1)
    hanging(2.7, CEIL_LO, 11.5, drop=-0.1)


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
    """Salle des machines (reference panel 3): the crystal engine (generate_crystal.crystal_engine) behind a polished brass
    guard rail, iron grates in the floor in front of it, pressure tanks and a dwarven metal chest at its sides, bronze pipes
    of the dwarven automatons' mod along the walls, copper pipes and beams under the ceiling, gauge boards, lanterns on the
    stone walls, crystal lamps; on the landing the workbench and its tool board, lockers, metal boxes."""
    f = LO
    h = ci.EF
    # the landing: the workbench on the bulkhead (starboard), lockers and dwarven metal boxes (port), a stool
    against_z(FD + "workbench", -3.0, f, -7.5, -1)
    block(FD + "tool_board", -3.0, f + 1.25, -7.6, "stern", solid=False)
    for x in (2.6, 3.6):
        against_z(MB + "dwemer_metal_block", x, f, -7.5, -1)
    against_z(MB + "dwemer_metal_pipe_gear", 3.1, f + 1.0, -7.5, -1, solid=False)
    chair(FU + "spruce_stool", -1.6, f, -8.6, "stern", -1.6, -9.5)
    custom("crystal_lamp", solid=(1.45, 2.05, f, f + 2.0, -8.6, -8.0), name="engine_crystal_lamp_0", p=(1.75, f, -8.3))
    # the guard rail in front of the engine (solid), the floor grates in front of it and along the side passages
    zr = -14.55
    custom("brass_rail", solid=(-2.0, 2.0, h, h + 1.0, -15.4, -14.4), name="engine_rail", pts=[(-1.95, h, zr - 0.6), (-1.6, h, zr), (1.6, h, zr),
                                                                                              (1.95, h, zr - 0.6)], h=1.0, step=0.8)
    for k, (x, z, w, l) in enumerate(((-0.75, -13.4, 1.4, 1.6), (0.75, -13.4, 1.4, 1.6), (-0.75, -11.8, 1.4, 1.2), (-2.75, -17.0, 0.9, 1.6),
                                      (2.75, -17.0, 0.9, 1.6))):
        custom("floor_grate", name="engine_grate_%d" % k, p=(x, h, z), w=w, l=l)
    # the starboard side (under the stair from the mess): a pressure tank, the dwarven chest, bronze pipes on the wall
    custom("pressure_tank", solid=(-3.45, -2.55, h, h + 2.0, -13.95, -13.05), name="engine_tank_s", p=(-3.0, h, -13.5), r=0.42, h=1.6)
    at(MB + "dwemer_chest", -2.85, h, -12.05, "port")
    for side in (-1, 1):       # brass and copper pipes up the walls beside the engine, valves on them
        for k, (z, d, reg) in enumerate(((-18.0, 0.22, "in_brass_pol"), (-18.4, 0.16, "in_copper"))):
            x0 = min(wall_x(h + 0.3, z, side), wall_x(h + 1.6, z, side), key=abs) - side * 0.16
            x1 = min(wall_x(-1.2, z, side), wall_x(CEIL_LO - 0.1, z, side), key=abs) - side * 0.16
            custom("pipe", name="engine_wall_pipe_%d_%d" % (side > 0, k), pts=[(x0, h + 0.05, z), (x0, h + 1.6, z), (x1, -1.2, z), (x1, CEIL_LO - 0.02, z)],
                   d=d, region=reg, flange="in_gold")
        xv = min(wall_x(h + 0.3, -18.0, side), wall_x(h + 1.6, -18.0, side), key=abs) - side * 0.16
        custom("valve", name="engine_wall_valve_%d" % (side > 0), p=(xv, h + 1.0, -18.0), normal=(-side, 0, 0), r=0.2)
    # the port side (beside the stair down from the landing): a pressure tank, pipes on the wall
    custom("pressure_tank", solid=(2.6, 3.4, h, h + 1.8, -14.4, -13.6), name="engine_tank_p", p=(3.0, h, -14.0), r=0.38, h=1.4)
    # aft, on the raised floor: a crate and a locker, pressure tanks in the corners
    at(FU + "dark_oak_crate", -1.6, ci.PLINTH[2], -19.6, "stern")
    at(FU + "small_locker", 1.6, ci.PLINTH[2], -19.6, "stern")
    for s in (-1, 1):
        custom("pressure_tank", name="engine_tank_aft_%d" % (s > 0), p=(s * 2.45, ci.PLINTH[2], -19.0), r=0.3, h=1.1, region="in_copper")
    for side in (-1, 1):
        w = wall_x(h + 2.8, -14.9, side)
        custom("gauge_board", name="engine_gauges_%d" % (side > 0), center=(w - side * 0.02, h + 2.8, -14.9), normal=(-side, 0, 0), w=1.1, h=0.75)
    # copper and brass pipes under the ceiling, beams across, lanterns on the walls, a crystal lamp
    yc = CEIL_LO - 0.2
    for k, (x, d, reg) in enumerate(((-2.2, 0.26, "in_copper"), (2.3, 0.22, "in_brass_pol"), (-2.65, 0.16, "in_brass"))):
        custom("pipe", name="engine_ceil_pipe_%d" % k, pts=[(x, yc - 0.05 * k, -20.2), (x, yc - 0.05 * k, -11.3), (x, yc - 0.05 * k - 0.6, -10.9)],
               d=d, region=reg, flange="in_gold" if reg != "in_copper" else "in_brass")
    beams_across("engine", CEIL_LO, (-12.0, -19.0), w=0.3, h=0.3)
    for side in (-1, 1):
        wall_lantern("engine_lantern_%d" % (side > 0), side, f + 2.0, -13.6)
        wall_lantern("engine_lantern_aft_%d" % (side > 0), side, f + 1.6, -19.6)
    hanging(0.0, CEIL_LO, -9.3, drop=-0.25)
    hanging(0.0, CEIL_LO, -12.9, drop=0.5)


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
    # the round bow's forecastle is wide: benches along its bulwarks forward, looking out over the bow
    for side in (-1, 1):
        for z in (21.4, 22.4):
            w = cs.hull_x(z, fc + 0.5) - cs.SHELL - 0.2
            x = side * (w - 0.6)
            chair(FU + "dark_oak_bench", x, fc, z, "stern", x - side * 0.9, z)
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
