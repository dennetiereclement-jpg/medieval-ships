"""Furniture of the Fortress Ship: blocks of the decoration mods (drawn by the ship where they stand, moving with it;
never placed in the world), furniture modelled for the ship (drawn by tools/generate_fortress.py with the builders of
tools/corsair_furniture.py and generate_corsair.py), and the seats.

  src/main/resources/assets/medievalships/interiors/fortress_ship_decor.json

Same format as tools/frigate_decor.py (read by fr.medievalships.core.InteriorDecor); the block bounds come from the
mods catalog (/tmp/claude-0/mods_catalog/catalog.json) through frigate_decor.BOUNDS. A block whose mod is missing on a
client is replaced by its stand-in, a box of the same size in the model (bone "fallback_<i>"). The solid furniture is
added to the interior grid (FURNITURE cells): the players walk round the desk, the bed, the bunks and the cargo.

Phase 1 (the builder) furnishes every room with its essentials and the seats; kept clear (checked by
FortressShipTest): the doors, the stairs, the centre lines, the seats' stand-up spots.
"""
import json
import math

import numpy as np

import fortress_interior as fi
import fortress_shape as fs
import frigate_decor as fdx

FACING = fdx.FACING
FD, FU, FR, LI = fdx.FD, fdx.FU, fdx.FR, fdx.LI
BOUNDS = fdx.BOUNDS
FALLBACK_REGION = dict(fdx.FALLBACK_REGION)
GLOWING = fdx.GLOWING

BLOCKS = []   # dicts: block, x, y, z, yaw, solid, scale
SEATS = []    # dicts: x, y, z, dx, dy, dz
CUSTOM = []   # furniture drawn by generate_fortress: (builder name, kwargs, solid box or None)

M, L, C, Q, F, K = fs.MAIN_DECK_Y, fs.LOWER_FLOOR_Y, fs.CABIN_FLOOR_Y, fs.QUARTERDECK_Y, fs.FORECASTLE_Y, fs.KEEP_Y
HOLD_CEIL, CABIN_CEIL, KEEP_CEIL, MESS_CEIL = M - fs.SLAB, Q - fs.SLAB, K - fs.SLAB, F - fs.SLAB

to_ship, footprint = fdx.to_ship, fdx.footprint


def block(bid, x, y, z, facing="stern", solid=True, scale=1.0, centre=False):
    """A mod block. centre=True: (x, z) is the centre of its footprint, otherwise the centre of its block."""
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


# ---------------------------------------------------------------- the rooms
def captain_cabin():
    """Cabine du capitaine (sous la dunette, derrière la porte double du château) : the bed against the port side
    aft, a sea chest at its foot, the desk along the starboard side with the chart and the compass, the captain's
    chair before it, a table and a stool, lanterns from the beams."""
    block(FD + "double_bed", 3.4, C, -17.2, "bow", centre=True)
    custom("chest", solid=(2.9, 3.9, C, C + 0.65, -15.75, -15.2), name="captain_chest", p=(3.4, C, -15.48))
    block(FD + "desk", -3.6, C, -14.0, "port", centre=True)
    custom("chart_sheet", name="captain_chart", p=(-3.55, C + 1.02, -14.3), yaw=0.25)
    custom("compass_box", name="captain_compass", p=(-3.3, C + 1.02, -14.95))
    block(FD + "kerosene_lantern", -3.8, C + 1.02, -13.1, "port", solid=False)
    block(FU + "dark_oak_chair", -2.4, C, -14.0, "starboard", solid=False, centre=True)
    seat(-2.45, C + 0.56, -14.0, -1.45, C, -14.0)
    block(FU + "dark_oak_square_table", 3.6, C, -12.0, "stern")
    block(FU + "dark_oak_stool", 2.6, C, -12.0, "starboard", solid=False, centre=True)
    seat(2.6, C + 0.56, -12.0, 1.6, C, -12.0)
    block(FD + "rug_3x_3", 0.0, C, -14.5, "stern", solid=False, centre=True)
    lantern(0.0, CABIN_CEIL, -11.5)
    lantern(0.0, CABIN_CEIL, -16.5)


def keep_room():
    """Salle des officiers (le donjon, sur la dunette) : a table with two stools, a bookshelf, a lantern; the stair to
    the battlements along the port side stays clear."""
    block(FU + "dark_oak_square_table", -2.4, Q, -16.0, "stern")
    block(FU + "dark_oak_stool", -2.4, Q, -17.0, "bow", solid=False, centre=True)
    seat(-2.4, Q + 0.56, -17.0, -2.4, Q, -18.0)
    block(FU + "dark_oak_stool", -1.4, Q, -16.0, "port", solid=False, centre=True)
    seat(-1.4, Q + 0.56, -16.0, -0.4, Q, -16.0)
    block(FD + "tall_bookshelf", -3.4, Q, -18.4, "bow", centre=True)
    lantern(0.0, KEEP_CEIL, -15.5)


def turret_room():
    """La tourelle (sur le toit du donjon) : a lookout's stool by the forward window, a lantern."""
    block(FU + "spruce_stool", 0.0, K, -16.6, "bow", solid=False, centre=True)
    seat(0.0, K + 0.56, -16.6, 0.0, K, -17.5)
    lantern(1.2, K + 3.0, -17.5)


def mess():
    """Le réfectoire de l'équipage (sous le gaillard d'avant) : a long table with a bench on each side, lanterns."""
    custom("long_table", solid=(-0.45, 0.45, M, M + 0.8, 12.6, 15.4), name="mess_table", x0=-0.45, x1=0.45, z0=12.6, z1=15.4, y=M)
    for side in (1, -1):
        x = side * 1.05
        custom("bench", name="mess_bench_%d" % (side > 0), x=x, z0=12.7, z1=15.3, y=M)
        for z in (13.3, 14.7):
            seat(x, M + 0.47, z, side * 2.0, M, z)
    lantern(0.0, MESS_CEIL + 0.5, 12.0)


def crew_quarters():
    """Les quartiers de l'équipage (pont inférieur, à l'avant) : bunks along both sides, sea chests, a lantern; the
    fore mast through the middle."""
    for side in (1, -1):
        for z in (9.6, 11.8):
            x = side * 3.25
            custom("bunk2", solid=(min(x - side * 0.5, x + side * 0.5), max(x - side * 0.5, x + side * 0.5), L, L + 2.4, z - 0.95, z + 0.95),
                   name="crew_bunk_%s%d" % ("p" if side > 0 else "s", int(z * 10)), p=(x, L, z))
        custom("chest", solid=(side * 2.2 - 0.5, side * 2.2 + 0.5, L, L + 0.65, 7.0, 7.55), name="crew_chest_%d" % (side > 0), p=(side * 2.2, L, 7.28))
    lantern(0.0, HOLD_CEIL, 10.5)


def hold():
    """La cale (pont inférieur, à l'arrière) : barrels and crates stacked along both sides, sacks, lanterns; the
    centre line stays clear from the foot of the companionway to the stern."""
    f_in = {1: "starboard", -1: "port"}
    for side in (1, -1):
        x = side * 4.0
        for k, z in enumerate((-12.5, -11.4, -10.3)):
            block(LI + ("cypress_barrel" if k % 2 else "fir_barrel"), x, L, z, f_in[side])
        # crates (port: aft of the companionway's foot, which stays clear)
        zc = (-8.2, -7.1, -9.3) if side > 0 else (-7.0, -5.9, -4.8)
        for z in zc[:2]:
            block(FU + "spruce_crate", x, L, z, f_in[side])
        block(FU + "dark_oak_crate", x, L, zc[2], f_in[side])
        block(FU + "spruce_crate", x - side * 0.05, L + 1.0, (zc[0] + zc[1]) / 2, f_in[side], solid=False, scale=0.9)
    block(FR + "rice_bag", -4.0, L, -2.4, "port")
    block(FR + "rice_bag", -4.0, L, -1.4, "port")
    block(FR + "potato_crate", -4.0, L, 2.0, "port")
    for z in (-13.0, -6.0, 2.0):
        lantern(0.0 if abs(z - fs.MAIN_MAST_Z) > 1.5 else 1.2, HOLD_CEIL, z)


def deck():
    """Pont principal : a bench a side by the main mast, barrels and crates against the bulwarks (the cargo of the
    references); the walking areas, the stairs, the hatches and the centre line stay clear."""
    for side in (1, -1):
        x = side * 4.6
        block(FU + "spruce_bench", x, M, -2.6, "bow" if side > 0 else "bow", solid=False)
        seat(x, M + 0.562, -2.6, x - side * 0.9, M, -2.6)
    block(LI + "cypress_barrel", -4.6, M, 5.6, "port")
    block(LI + "fir_barrel", -4.6, M, 4.6, "port")
    block(FU + "spruce_crate", -4.3, M, -6.4, "port")
    block(FU + "dark_oak_crate", 4.3, M, -6.4, "starboard")


def build():
    BLOCKS.clear()
    SEATS.clear()
    CUSTOM.clear()
    captain_cabin()
    keep_room()
    turret_room()
    mess()
    crew_quarters()
    hold()
    deck()
    return BLOCKS, SEATS


def _cells(g, box, min_overlap=0.2):
    x0, x1, y0, y1, z0, z1 = box
    h = fi.CELL / 2
    ox = np.minimum(g.X + h, x1) - np.maximum(g.X - h, x0)
    oy = np.minimum(g.Y + h, y1) - np.maximum(g.Y - h, y0 + 0.01)
    oz = np.minimum(g.Z + h, z1) - np.maximum(g.Z - h, z0)
    return (ox >= min_overlap - 1e-6) & (oz >= min_overlap - 1e-6) & (oy >= min(min_overlap, y1 - y0 - 0.01) - 1e-6)


def apply_to_grid(g):
    """FURNITURE cells under the solid furniture (on the floor of a room, or on a deck)."""
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


DECOR_PATH = "src/main/resources/assets/medievalships/interiors/fortress_ship_decor.json"
