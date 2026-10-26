"""Furniture of the Dragon Junk: blocks of the user's decoration mods (drawn by the junk where they stand, moving
with it; never placed in the world), the furniture made for the ships (tools/leviathan_furniture.py, reused) and
the seats, room by room after the interior views of the reference sheet (main deck with its grating and lanterns,
the deck before the stern house, the main room with the big map table on the red rug, the storage with its pillars,
crates and barrels, the bedroom with the red bed, a night stand, shelves and a rug), plus the stern cabin.

  src/main/resources/assets/medievalships/interiors/dragon_junk_decor.json

Same format and same rules as the Nautilus and the Sky Leviathan (tools/leviathan_decor.py): each mod block is
given by the centre of its bottom face (ship-local) and the direction its front faces; its footprint becomes solid
cells of the interior grid (chairs, stools, benches and small things on tables are not solid); a block whose mod is
missing on a client is replaced by its stand-in, a box of the same size in the model (bone "fallback_<i>").

Mods used: farmhouse_decorations (Farmhouse Decorations), furnish (Furnish), farmersdelight (Farmer's Delight),
landsoficaria (Lands of Icaria). Block measurements: the default state's model bounds (x east, z south, front
north), from the mods' files (/tmp/claude-0/mods_catalog/catalog.json).
"""
import json
import math

import junk_interior as ji
import junk_shape as js
import leviathan_decor as ld
import nautilus_decor as nd

FACING = nd.FACING   # stern 0, starboard 90, bow 180, port 270 (the block's north = its front)

FD = "farmhouse_decorations:"
FU = "furnish:"
FR = "farmersdelight:"
IC = "landsoficaria:"

BOUNDS = dict(ld.BOUNDS)
BOUNDS.update({
    FD + "sofa_left": (0.0, 0.875, 0.0, 0.875, 0.188, 1.0),
    FD + "sofa_middle": (0.0, 1.0, 0.062, 0.781, 0.219, 0.984),
    FD + "sofa_right": (0.125, 1.0, 0.0, 0.875, 0.188, 1.0),
    FD + "round_table": (-0.062, 1.062, 0.0, 1.0, -0.062, 1.062),
    FD + "lamp": (0.156, 0.844, 0.0, 0.969, 0.156, 0.844),
    FU + "crimson_table": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FU + "crimson_stool": (0.188, 0.812, 0.0, 0.562, 0.125, 0.75),
    FU + "spruce_bench": (0.0, 1.0, 0.0, 0.562, 0.25, 0.75),
    FU + "dark_oak_log_bench": (0.0, 1.0, 0.0, 0.625, 0.188, 0.812),
    IC + "loaded_fir_barrel": (0.047, 0.953, 0.0, 0.906, 0.0, 1.0),
    IC + "cypress_rack": (0.0, 1.0, 0.0, 0.25, 0.0, 1.0),
    FR + "canvas_rug": (-0.5, 1.5, 0.0, 0.062, -0.5, 1.5),
    FD + "rocking_chair": (0.0, 1.0, 0.0, 1.522, 0.0, 1.183),
    FD + "coffee_table": (-0.062, 1.062, 0.0, 0.5, -0.062, 1.062),
    FU + "dark_oak_bedside_table": (0.0, 1.0, 0.0, 1.0, -0.062, 1.0),
    FU + "rare_chinese_plate": (0.062, 0.938, 0.0, 0.062, 0.062, 0.938),
    FU + "mangrove_table": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    FU + "mangrove_stool": (0.188, 0.812, 0.0, 0.562, 0.125, 0.75),
    FU + "dark_oak_bench": (0.0, 1.0, 0.0, 0.562, 0.25, 0.75),
    IC + "triple_fir_barrel_rack": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
})
SEAT_H = dict(ld.SEAT_H)
SEAT_H.update({FU + "mangrove_stool": 0.562, FU + "dark_oak_bench": 0.562, FU + "crimson_stool": 0.562, FU + "spruce_bench": 0.562, FD + "sofa_left": 0.344, FD + "sofa_middle": 0.344,
               FD + "sofa_right": 0.344, FU + "dark_oak_log_bench": 0.625, FD + "rocking_chair": 0.625})
FALLBACK_REGION = dict(ld.FALLBACK_REGION)
FALLBACK_REGION.update({FD + "sofa_left": "in_cushion", FD + "sofa_middle": "in_cushion", FD + "sofa_right": "in_cushion",
                        FU + "crimson_table": "in_lacquer", FU + "crimson_stool": "in_cushion", FD + "round_table": "in_plank",
                        FD + "lamp": "in_lamp", FU + "spruce_bench": "in_plank", IC + "loaded_fir_barrel": "barrel",
                        IC + "cypress_rack": "in_plank", FR + "canvas_rug": "in_canvas", FU + "dark_oak_log_bench": "in_beam",
                        FD + "rocking_chair": "in_plank", FD + "coffee_table": "in_plank", FU + "dark_oak_bedside_table": "in_plank",
                        FU + "rare_chinese_plate": "pearl", FU + "mangrove_table": "in_plank", FU + "mangrove_stool": "in_plank",
                        FU + "dark_oak_bench": "in_beam", IC + "triple_fir_barrel_rack": "barrel"})
GLOWING_FALLBACK = ld.GLOWING_FALLBACK + (FD + "lamp",)

BLOCKS = []    # dicts: block, x, y, z, yaw, solid, scale
SEATS = []     # dicts: x, y, z, dx, dy, dz
CUSTOM = []    # furniture made for the ships: (builder name, kwargs, solid box or None)
PAINTINGS = []
SWITCHES = []

M0, QD, LO, BR = ji.M0, ji.QD, ji.LO, ji.BR
CEIL_LO = M0 - js.SLAB          # ceiling of the lower deck (-0.5)
CEIL_BR = QD - js.SLAB          # ceiling of the bedroom (2.0)
CEIL_HC = js.HOUSE_CEIL_Y       # ceiling of the stern cabin (6.0)

# lanterns on posts and bollards on the open decks (drawn by tools/generate_junk.py deck_fittings, solid in the grid)
DECK_LANTERNS = [("lamp_bow_p", (js.hull_x(17.3, 0.3) - 0.8, M0, 17.3)), ("lamp_bow_s", (-(js.hull_x(17.3, 0.3) - 0.8), M0, 17.3)),
                 ("lamp_waist_p", (js.hull_x(5.4, 0.3) - 0.8, M0, 5.4)), ("lamp_waist_s", (-(js.hull_x(3.2, 0.3) - 0.8), M0, 3.2)),
                 ("lamp_qd_p", (3.45, QD, -2.4)), ("lamp_qd_s", (-3.6, QD, -2.7))]
BOLLARDS = [(side, z) for side in (1, -1) for z in (12.4, 7.8)]

_GRID = []


def grid():
    if not _GRID:
        _GRID.append(ji.build())
    return _GRID[0]


def wall_x(y, z, side, x_from=0.0):
    """Inner face of the side wall (side +1: port, -1: starboard) at height y and z, scanning outwards from x_from."""
    g = grid()
    j = int(math.floor((y - ji.Y0) / ji.CELL))
    l = int(math.floor((z - ji.Z0) / ji.CELL))
    i = int(math.floor((x_from - ji.X0) / ji.CELL))
    while 0 <= i < g.nx:
        if g.k[i, j, l] in (ji.SOLID, ji.OUT):
            return ji.X0 + (i if side > 0 else i + 1) * ji.CELL
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
    w = min([v for v in ws if v is not None], key=abs)
    cx = w - side * ((x1 - x0) / 2 + gap)
    return at(bid, cx, y, z, facing, solid, scale)


def block_axis(facing):
    """Ship-local direction of the block's east (+x) once turned to `facing` (to line up multi-block furniture)."""
    yaw = FACING[facing]
    a = nd.to_ship(None, 0, 0, 0, yaw, 1.5, 0, 0.5)
    b = nd.to_ship(None, 0, 0, 0, yaw, 0.5, 0, 0.5)
    return (a[0] - b[0], a[2] - b[2])


def custom(builder, solid=None, **kwargs):
    """Furniture of generate_junk.py's FURNITURE_BUILDERS (the Sky Leviathan's builders); solid = (x0, x1, y0, y1, z0, z1)
    added to the grid."""
    CUSTOM.append((builder, kwargs, solid))


def seat(x, y, z, dx, dy, dz):
    SEATS.append({"x": x, "y": y, "z": z, "dx": dx, "dy": dy, "dz": dz})


def chair(bid, x, floor, z, facing, dx, dz, solid=False):
    """A chair, stool or bench block centred at (x, z) and its seat."""
    at(bid, x, floor, z, facing, solid=solid)
    seat(x, floor + SEAT_H[bid] - 0.12, z, dx, floor + 0.02, dz)


def sofa(x, floor, z, facing, n_mid=1, seats=True, dismount=0.65):
    """A Farmhouse sofa (right end, middles, left end) centred at (x, z) and turned to `facing`, its seats."""
    ex, ez = block_axis(facing)
    pieces = ["sofa_right"] + ["sofa_middle"] * n_mid + ["sofa_left"]
    n = len(pieces)
    fx, fz = FACING_DIR[facing]
    for k, p in enumerate(pieces):
        off = k - (n - 1) / 2
        px, pz = x + ex * off, z + ez * off
        at(FD + p, px, floor, pz, facing, solid=False)
        if seats:
            seat(px - fx * 0.05, floor + SEAT_H[FD + p] - 0.06, pz - fz * 0.05, px + fx * dismount, floor + 0.02, pz + fz * dismount)


FACING_DIR = {"stern": (0.0, -1.0), "bow": (0.0, 1.0), "port": (1.0, 0.0), "starboard": (-1.0, 0.0)}


def painting(name, motive, center, normal, w, h):
    custom("painting_frame", name=name, center=center, normal=normal, w=w, h=h)
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


def frame_room(name, floor, ceil, zs, sides=(-1, 1), x_from=0.0, beams=True):
    """The timber frame of a room: posts against the side walls, beams across the ceiling."""
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


# ---------------------------------------------------------------- rooms
def main_room():
    """Salle principale (reference panel 3): the big heavy table in the middle with a sea chart spread on it, on the red
    rug with its gold border; stools round it, lanterns over it; the red sofa along the starboard wall, shelves of
    bottles and jars on the port wall (aft of them the companion stair comes down), a writing table with a lantern by
    a porthole, a sea chest, the timber frame."""
    f = LO
    for x in (-0.5, 0.5):
        for z in (2.5, 3.5, 4.5):
            piece = "dining_table_side" if z in (2.5, 4.5) else "dining_table_middle"
            block(FD + piece, x, f, z, "port" if z == 4.5 else "starboard")
    custom("rug", name="main_rug", p=(0.0, f, 3.4), w=4.6, l=5.8)
    t = f + 1.0
    custom("chart_sheet", name="main_chart", p=(0.0, t, 3.5), yaw=0.05, w=1.5, l=2.2)
    custom("compass", name="main_compass", p=(0.55, t + 0.01, 4.4))
    custom("dividers", name="main_dividers", p=(-0.3, t + 0.012, 3.0), yaw=0.6)
    custom("candle", name="main_candle_0", p=(-0.7, t, 2.2))
    custom("candle", name="main_candle_1", p=(0.7, t, 4.8))
    custom("map_roll", name="main_map_roll", p=(0.6, t + 0.05, 2.3), yaw=1.2, l=0.6)
    for k, (x, z) in enumerate(((1.45, 3.0), (1.45, 4.0), (0.0, 1.55), (0.0, 5.45))):
        chair(FU + "spruce_stool", x, f, z, "starboard" if x > 0 else "bow" if z < 3 else "stern", x + (0.55 if x > 0 else 0.0),
              z + (0 if x > 0 else -0.8 if z < 3 else 0.8))
    for z in (2.6, 4.4):
        hanging(0.0, CEIL_LO, z, drop=0.05)
    # the red sofa along the starboard wall, facing the table
    w = max(wall_min(f, f + 1.0, z, -1) for z in (3.7, 4.6, 5.5))
    sofa(w + 0.45, f, 4.6, "port", n_mid=1)
    custom("rug", name="main_sofa_rug", p=(w + 1.2, f, 4.6), w=0.9, l=2.6, region="in_runner")
    # port wall forward of the stair: shelves of bottles and jars, a liquor cabinet
    for z in (4.2, 6.2):
        wp = wall_min(f, CEIL_LO, z, 1)
        custom("jar_shelf", solid=(wp - 0.4, wp, f, f + 2.1, z - 0.5, z + 0.5), name="main_jars_%d" % int(z), p=(wp - 0.02, f, z),
               normal=(-1, 0, 0), w=1.0, h=2.1, rows=4)
    against(FD + "kitchen_wall_shelf", 1, f + 1.25, 7.0, solid=False)
    # the fore bulkhead either side of the storage door: a dresser and a sea chest
    at(FD + "dresser", 2.2, f, 7.12, "stern")
    block(FD + "wine_bottle", 2.0, f + 1.02, 7.1, "stern", solid=False)
    block(FD + "red_wine_bottle", 2.35, f + 1.02, 7.15, "stern", solid=False)
    wc = max(wall_min(f, f + 0.7, z, -1) for z in (6.8, 7.3))
    custom("sea_chest", solid=(wc + 0.05, wc + 1.15, f, f + 0.62, 6.75, 7.35), name="main_chest", p=(wc + 0.6, f, 7.05), facing="stern", w=1.0, d=0.55)
    # the writing table by the starboard porthole aft, its lantern
    ws = wall_min(f, f + 1.0, -0.3, -1)
    at(FU + "dark_oak_square_table", ws + 0.55, f, -0.3, "stern")
    block(FD + "kerosene_lantern", ws + 0.45, f + 1.0, -0.15, "stern", solid=False)
    block(FD + "pile_of_books", ws + 0.65, f + 1.0, -0.6, "port", solid=False)
    chair(FU + "spruce_chair", ws + 1.35, f, -0.3, "starboard", ws + 1.35, 0.55)
    for k, z in enumerate((-0.3, 2.4, 5.6)):
        w = wall_x(f + 1.45, z, -1)
        custom("porthole_in", name="main_porthole_s%d" % k, center=(w + 0.01, f + 1.45, z), normal=(1, 0, 0))
    w = wall_x(f + 1.45, 6.9, 1)
    wall_lantern("main_wall_lantern_0", -1, f + 1.95, 1.0)
    wall_lantern("main_wall_lantern_1", 1, f + 1.95, 5.2)
    painting("main_painting", "sea", (-1.6, f + 1.5, 7.48), (0, 0, -1), 1.2, 0.6)
    frame_room("main", f, CEIL_LO, zs=[-1.25, 1.0, 5.2, 7.25])


def storage():
    """Réserve (reference panel 4): heavy square pillars on stone bases with lanterns hanging by them, crates stacked two
    high along both sides, barrels on their racks, piles of rice bags and sacks, crates of the harvest, shelves of
    bottles and jars, the ladder up to the hatch in the main deck."""
    f = LO
    for k, z in enumerate((9.5, 13.5)):   # on the grid's cell corners: the pillar's solid is the 2x2 cells around it
        custom("timber", name="storage_pillar_%d" % k, solid=(-0.5, 0.5, f, CEIL_LO, z - 0.5, z + 0.5), a=(0.0, f, z), b=(0.0, CEIL_LO, z), w=0.6)
        custom("timber", name="storage_pillar_base_%d" % k, a=(0.0, f, z), b=(0.0, f + 0.35, z), w=0.8)
        custom("timber", name="storage_beam_%d" % k, a=(-3.6, CEIL_LO - 0.14, z), b=(3.6, CEIL_LO - 0.14, z), w=0.3)
        hanging(0.62 if k == 0 else -0.62, CEIL_LO, z, drop=0.1)
    # port side: crates stacked two high, harvest crates, rice bags piled up, sacks
    for k, (z, bid, top) in enumerate(((8.65, FU + "spruce_crate", FU + "dark_oak_crate"), (10.55, FU + "dark_oak_crate", FU + "spruce_crate"),
                                       (11.6, FR + "potato_crate", FR + "carrot_crate"))):
        x = wall_min(f, f + 2.0, z, 1) - 0.55
        at(bid, x, f, z, "starboard")
        if top:
            at(top, x + 0.02, f + 1.0, z, "starboard", scale=0.9)
    xr = wall_min(f, f + 1.0, 12.55, 1) - 0.55
    at(FR + "rice_bag", xr, f, 12.55, "starboard")
    at(FR + "rice_bag", xr + 0.05, f + 1.0, 12.55, "starboard", scale=0.8, solid=False)
    custom("sack", name="storage_sack_0", p=(xr - 0.7, f, 12.2), yaw=0.6)
    custom("sack", name="storage_sack_1", p=(1.2, f, 9.6), yaw=-0.4, s=0.8)
    # starboard side: a rack of barrels, barrels lying in their cradles, upright barrels, a stack of crates, a rope coil
    x = wall_min(f, f + 1.0, 8.75, -1) + 0.5
    at(IC + "triple_fir_barrel_rack", x, f, 8.75, "port")
    for k, z in enumerate((10.95, 11.85)):
        x = wall_min(f, f + 1.0, z, -1) + 0.45
        custom("barrel", solid=(x - 0.4, x + 0.4, f, f + 0.95, z - 0.4, z + 0.4), name="storage_barrel_%d" % k, p=(x, f, z))
    custom("rope_coil", name="storage_rope", p=(-1.0, f, 11.4), r=0.36)
    x = wall_min(f, f + 1.0, 12.75, -1) + 0.5
    at(IC + "loaded_fir_barrel", x, f, 12.75, "port")
    # forward, where the hull narrows: a sack and the shelf of jars on the bow bulkhead
    custom("sack", name="storage_sack_2", p=(-0.7, f, 15.2), yaw=1.1, s=0.85)
    custom("jar_shelf", name="storage_jars", p=(0.0, f, 15.6), normal=(0, 0, -1), w=1.2, h=1.9, rows=4)
    # shelves of bottles on the walls over the crates
    for k, (side, z) in enumerate(((1, 10.2), (-1, 10.4))):
        against(FU + "dark_oak_shelf", side, f + 1.9, z, solid=False, top=0.3)
        w = wall_x(f + 2.0, z, side)
        for j, dz in enumerate((-0.25, 0.05, 0.3)):
            block(FD + ("wine_bottle" if j != 1 else "red_wine_bottle"), w - side * 0.24, f + 2.15, z + dz, "stern", solid=False, scale=0.8)
    frame_room("storage", f, CEIL_LO, zs=[8.25, 11.8, 15.0])


def bedroom():
    """Chambre (reference panel 5): the bed under its red blanket along the port side under the window, a night stand with
    a lantern at its head, a sea chest at its foot; on the starboard side the desk with its chair and lantern under a
    shelf of bottles, the dresser and the wardrobe; a bookshelf on the aft bulkhead, the red rug in the middle, a rocking
    chair by a low table forward, lanterns."""
    f = BR
    wp = max(wall_min(f, f + 1.3, z, 1) for z in (-7.6, -6.6, -5.6))
    bed_x, bed_z = wp - 1.0, -6.6
    i = at(FD + "double_bed", bed_x, f, bed_z, "bow")
    b = BLOCKS[i]
    custom("bed_blanket", name="bed_blanket", x=b["x"], y=b["y"], z=b["z"], yaw_deg=b["yaw"])
    wn = wall_min(f, f + 0.7, -8.1, 1)
    at(FD + "night_stand", wn - 0.36, f, -8.1, "starboard")
    block(FD + "kerosene_lantern", wn - 0.36, f + 0.63, -8.1, "stern", solid=False)
    custom("window_in", name="bedroom_window_p", center=(wall_x(f + 1.45, -6.6, 1) - 0.01, f + 1.45, -6.6), normal=(-1, 0, 0), w=0.8, h=0.8)
    custom("window_in", name="bedroom_window_s", center=(wall_x(f + 1.45, -4.6, -1) + 0.01, f + 1.45, -4.6), normal=(1, 0, 0), w=0.8, h=0.8)
    custom("sea_chest", solid=(bed_x - 0.5, bed_x + 0.5, f, f + 0.62, -5.3, -4.75), name="bedroom_chest", p=(bed_x, f, -5.02), facing="bow", w=1.0,
           d=0.55)
    against(FD + "wall_shelf", 1, f + 1.15, -8.1, solid=False)
    # the starboard side: the desk and its chair under a shelf of bottles, a lantern on it; the dresser aft, the wardrobe
    ws = max(wall_min(f, f + 1.0, z, -1) for z in (-7.6, -6.3, -5.0))
    at(FD + "desk", ws + 0.55, f, -6.3, "port")
    block(FD + "kerosene_lantern", ws + 0.45, f + 1.02, -7.2, "stern", solid=False)
    block(FD + "pile_of_books", ws + 0.5, f + 1.02, -5.5, "port", solid=False)
    custom("chart_sheet", name="bedroom_letter", p=(ws + 0.6, f + 1.03, -6.3), yaw=0.2, w=0.5, l=0.4)
    chair(FU + "dark_oak_chair", ws + 1.45, f, -6.3, "starboard", ws + 1.45, -5.2)
    against(FU + "dark_oak_shelf", -1, f + 1.75, -6.3, solid=False, top=0.3)
    w = wall_x(f + 1.8, -6.3, -1)
    for j, dz in enumerate((-0.3, 0.0, 0.3)):
        block(FD + ("wine_bottle" if j != 1 else "red_wine_bottle"), w + 0.24, f + 2.0, -6.3 + dz, "stern", solid=False, scale=0.8)
    against(FD + "dresser", -1, f, -8.3)
    block(FD + "pile_of_books", wall_x(f + 0.5, -8.3, -1) + 0.4, f + 1.02, -8.45, "port", solid=False)
    custom("candle", name="bedroom_candle", p=(wall_x(f + 0.5, -8.3, -1) + 0.45, f + 1.02, -8.0))
    against(FD + "wardrobe", -1, f, -3.5)
    custom("book_shelf", name="bedroom_shelf", p=(0.0, f + 1.45, -8.98), normal=(0, 0, 1), w=1.6, h=0.5)
    custom("rug", name="bedroom_rug", p=(-0.3, f, -5.4), w=2.2, l=3.4)
    # forward: a rocking chair by a low table with a chess board, a coat rack and a clock by the door
    chair(FD + "rocking_chair", 2.6, f, -3.3, "starboard", 1.6, -4.1)
    at(FD + "coffee_table", 1.5, f, -2.7, "stern")
    block(FU + "chess_board", 1.5, f + 0.5, -2.7, "stern", solid=False, scale=0.8)
    at(FD + "coat_hanger", -1.95, f, -2.6, "stern")
    block(FD + "cuckoo_clock", 1.6, f + 1.15, -2.52, "stern", solid=False)
    hanging(0.0, CEIL_BR, -5.6, drop=0.0)
    wall_lantern("bedroom_wall_lantern", 1, f + 1.75, -4.4)
    frame_room("bedroom", f, CEIL_BR, zs=[-2.25, -5.6, -8.75])


def stern_cabin():
    """La cabine de poupe (the stern house): oriental timber framing, a low red lacquered table on a rug with stools, the
    captain's desk and chair facing the door, tall bookshelves, the red sofa, a liquor cabinet and jars, lattice
    windows, lanterns."""
    f = QD
    # the table and its stools
    for z in (-12.2, -13.2):
        for x in (-0.5, 0.5):
            block(FU + "mangrove_table", x, f, z, "stern")
    custom("rug", name="cabin_rug", p=(0.0, f, -12.7), w=3.6, l=4.0)
    for k, (x, z, fc) in enumerate(((-1.4, -12.2, "port"), (-1.4, -13.2, "port"), (1.4, -12.2, "starboard"), (1.4, -13.2, "starboard"))):
        chair(FU + "mangrove_stool", x, f, z, fc, x + (-0.8 if x < 0 else 0.8), z)
    t = f + 1.0
    block(FD + "kerosene_lantern", 0.0, t, -12.7, "stern", solid=False)
    block(FU + "rare_chinese_plate", -0.5, t, -12.3, "stern", solid=False, scale=0.55)
    block(FU + "rare_chinese_plate", 0.5, t, -13.1, "stern", solid=False, scale=0.55)
    block(FD + "wine_glass", 0.4, t, -12.3, "stern", solid=False, scale=0.85)
    block(FD + "red_wine_bottle", -0.3, t, -13.0, "stern", solid=False)
    # the captain's desk aft, facing the door, his chair behind it
    at(FD + "desk", 0.0, f, -16.2, "bow")
    chair(FU + "dark_oak_chair", 0.0, f, -17.5, "bow", 1.4, -17.6)
    custom("chart_sheet", name="cabin_chart", p=(-0.6, f + 1.02, -16.2), yaw=0.1, w=0.9, l=0.6)
    custom("inkwell", name="cabin_inkwell", p=(0.6, f + 1.02, -16.0))
    custom("hourglass", name="cabin_hourglass", p=(1.1, f + 1.02, -16.3))
    block(FD + "pile_of_books", -1.2, f + 1.02, -16.3, "bow", solid=False)
    # bookshelves in the aft corners
    for side in (-1, 1):
        x = wall_min(f, f + 2.0, -18.3, side) - side * 0.52
        at(FD + "tall_bookshelf", x, f, -18.55, "bow")
    # the sofa along the port wall, a liquor cabinet and jars on the starboard wall
    wp = wall_min(f, f + 1.0, -11.0, 1)
    sofa(wp - 0.42, f, -11.0, "starboard", n_mid=1)
    against(FD + "liquor_cabinet", -1, f, -11.0)
    ws = wall_min(f, CEIL_HC, -14.6, -1)
    custom("jar_shelf", solid=(ws, ws + 0.4, f, f + 2.4, -15.1, -14.1), name="cabin_jars", p=(ws + 0.02, f, -14.6), normal=(1, 0, 0), w=1.0,
           h=2.4, rows=5)
    against(FD + "dresser", 1, f, -14.6)
    block(FD + "cigar_box", wall_x(f + 0.5, -14.6, 1) - 0.4, f + 1.02, -14.6, "starboard", solid=False)
    # the lattice windows seen from inside (the house's side and back walls, as drawn outside)
    for side in (-1, 1):
        for k, z in enumerate((-9.5, -15.5)):
            w = wall_x(f + 1.75, z, side)
            custom("window_in", name="cabin_window_%d_%d" % (side > 0, k), center=(w - side * 0.01, f + 1.85, z), normal=(-side, 0, 0), w=1.0,
                   h=1.2)
    for k, x in enumerate((-2.3, 2.3)):
        custom("window_in", name="cabin_back_window_%d" % k, center=(x, f + 1.85, -18.99), normal=(0, 0, 1), w=0.9, h=1.2)
    for k, x in enumerate((-2.45, 2.45)):
        custom("window_in", name="cabin_front_window_%d" % k, center=(x, f + 1.85, -8.51), normal=(0, 0, -1), w=0.9, h=1.2)
    painting("cabin_painting", "wanderer", (0.0, f + 2.3, -18.98), (0, 0, 1), 0.6, 1.1)
    for z in (-10.6, -14.6):
        hanging(0.0, CEIL_HC, z, drop=0.4)
    wall_lantern("cabin_wall_lantern_0", -1, f + 2.4, -17.2)
    wall_lantern("cabin_wall_lantern_1", 1, f + 2.4, -16.6)
    frame_room("cabin", f, CEIL_HC, zs=[-8.75, -11.75, -14.75, -17.75])


def companion():
    """The companion house: a lantern on its wall over the stair, a coil of rope."""
    custom("rope_coil", name="companion_rope", p=(3.45, M0, 3.2), r=0.3)
    wall_lantern("companion_lantern", 1, M0 + 2.2, 1.6)


def decks():
    """Pont principal (reference panels 1 and 2): crates and barrels by the bulwarks and at the stern house's door, coils
    of rope by the mast, benches along the bulwarks, a sea chest on the quarterdeck."""
    f = M0
    for side in (1, -1):
        x = side * (js.hull_x(15.4, 0.3) - 1.0)
        at(FU + "spruce_crate", x, f, 15.4, "stern")
        at(FU + "dark_oak_crate", x, f + 1.0, 15.4, "stern", scale=0.8) if side > 0 else None
        xb = side * (js.hull_x(13.5, 0.3) - 0.95)
        custom("barrel", solid=(xb - 0.4, xb + 0.4, f, f + 0.95, 13.1, 13.9), name="deck_barrel_%d" % (side > 0), p=(xb, f, 13.5))
        for k, z in enumerate((9.6, 10.6)):
            xs = side * (js.hull_x(z, 0.3) - 0.85)
            chair(FU + "dark_oak_bench", xs, f, z, "stern", xs - side * 0.85, z)
    custom("rope_coil", name="deck_rope_0", p=(1.25, f, 17.3), r=0.4)
    custom("rope_coil", name="deck_rope_1", p=(-1.3, f, 14.2), r=0.34)
    # the quarterdeck: crates and barrels either side of the stern house's door (reference panel 2), a sea chest
    q = QD
    for side in (1, -1):
        x = side * 2.4
        at(FU + "spruce_crate", x, q, -7.4, "bow")
        xb = side * 3.4
        custom("barrel", solid=(xb - 0.38, xb + 0.38, q, q + 0.95, -7.65, -6.95), name="qd_barrel_%d" % (side > 0), p=(xb, q, -7.3), r=0.34)
    custom("sea_chest", solid=(2.6, 3.65, q, q + 0.62, -4.4, -3.8), name="qd_chest", p=(3.12, q, -4.1), facing="starboard", w=1.0, d=0.55)
    # the deck lanterns' posts and the bollards are drawn by the model; their footprints are solid
    for name, (x, y, z) in DECK_LANTERNS:
        custom("none", solid=(x - 0.3, x + 0.3, y, y + 1.9, z - 0.3, z + 0.3))
    for side, z in BOLLARDS:
        x = side * (js.hull_x(z, 0.2) - 0.75)
        custom("none", solid=(x - 0.2, x + 0.2, M0, M0 + 0.85, z - 0.2, z + 0.2))


def build():
    BLOCKS.clear()
    SEATS.clear()
    CUSTOM.clear()
    PAINTINGS.clear()
    SWITCHES.clear()
    main_room()
    storage()
    bedroom()
    stern_cabin()
    companion()
    decks()
    return BLOCKS, SEATS


def footprint(b):
    return _footprint(b["block"], b["x"], b["y"], b["z"], b["yaw"], b["scale"])


def apply_to_grid(g):
    """Solid cells for the footprints of the solid furniture."""
    for builder, kwargs, solid in CUSTOM:
        if solid is not None:
            x0, x1, y0, y1, z0, z1 = solid
            g.set(ji.FURNITURE, x0 + 0.05, x1 - 0.05, y0 + 0.01, y1, z0 + 0.05, z1 - 0.05, where=(g.k == ji.DRY) | (g.k == ji.OUT))
    for b in BLOCKS:
        if not b["solid"]:
            continue
        x0, x1, y0, y1, z0, z1 = footprint(b)
        g.set(ji.FURNITURE, x0 + 0.05, x1 - 0.05, b["y"] + 0.01, y1, z0 + 0.05, z1 - 0.05, where=(g.k == ji.DRY) | (g.k == ji.OUT))


def write(path):
    data = {"blocks": [], "seats": [{k: round(v, 4) for k, v in s.items()} for s in SEATS],
            "paintings": [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in q.items()} for q in PAINTINGS], "switches": SWITCHES}
    for i, b in enumerate(BLOCKS):
        data["blocks"].append({"block": b["block"], "x": round(b["x"], 4), "y": round(b["y"], 4), "z": round(b["z"], 4),
                               "yaw": b["yaw"], "scale": b["scale"], "fallback": "fallback_%d" % i})
    with open(path, "w") as f:
        json.dump(data, f, indent=1)


DECOR_PATH = "src/main/resources/assets/medievalships/interiors/dragon_junk_decor.json"
