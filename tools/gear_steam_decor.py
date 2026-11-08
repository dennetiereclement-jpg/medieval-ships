"""Furniture of the Gear Steamship: blocks of the decoration mods (drawn by the ship where they stand, moving
with it; never placed in the world), furniture modelled for the ship (drawn by tools/generate_gear_steam.py
with the builders of tools/corsair_furniture.py and generate_corsair.py), and the seats.

  src/main/resources/assets/medievalships/interiors/gear_steamship_decor.json

Same format as tools/frigate_decor.py (read by fr.medievalships.core.InteriorDecor). A block whose mod is
missing on a client is replaced by its stand-in, a box of the same size in the model (bone "fallback_<i>").
The solid furniture is added to the interior grid (FURNITURE cells): the players walk round it.

Phase 1 (the builder) furnishes each room with its essentials and the seats; the decoration phase adds the
rest (mods' blocks first, catalog /tmp/claude-0/mods_catalog/catalog.json). Kept clear (checked by
GearSteamShipTest): the doors, the stairs, the ladders, the seats' stand-up spots.
"""
import json
import math

import numpy as np

import gear_steam_interior as gi
import gear_steam_shape as gs
from frigate_decor import BOUNDS, FALLBACK_REGION as _FRIGATE_FALLBACK, FD, FU, FR, LI   # noqa: F401  (shared, read only)

FACING = {"stern": 0.0, "starboard": 90.0, "bow": 180.0, "port": 270.0}
FALLBACK_REGION = dict(_FRIGATE_FALLBACK)
GLOWING = {FD + "kerosene_lantern", FD + "chained_kerosene_lantern"}

BLOCKS = []   # dicts: block, x, y, z, yaw, solid, scale
SEATS = []    # dicts: x, y, z, dx, dy, dz
CUSTOM = []   # furniture drawn by generate_gear_steam: (builder name, kwargs, solid box or None)

M, H, P, B = gs.MAIN_DECK_Y, gs.HOLD_FLOOR_Y, gs.POOP_Y, gs.BRIDGE_Y
HOLD_CEIL, CREW_CEIL, ENGINE_CEIL, CABIN_CEIL = M - gs.SLAB, P - gs.SLAB, gs.ENGINE_ROOF_Y - gs.SLAB, B - gs.SLAB


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
    """Cabine du capitaine (the deckhouse on the poop deck, floor 7.5, z -13.5 -> -7.5): the bunk against the
    port wall, the desk against the front wall with the captain's chair, a sea chest, a lantern."""
    custom("bunk", solid=(1.5, 2.5, P, P + 0.6, -13.45, -11.55), name="captain_bunk", p=(2.0, P, -12.5), l=1.9, w=0.95)
    custom("chest", solid=(1.6, 2.4, P, P + 0.65, -11.1, -10.55), name="captain_chest", p=(2.0, P, -10.82))
    custom("desk", solid=(-2.1, -0.3, P, P + 0.85, -8.58, -7.62), name="captain_desk", p=(-1.2, P, -8.1))
    custom("chair", name="captain_chair", p=(-1.2, P, -9.05), facing=0.0)
    seat(-1.2, P + 0.5, -9.05, -1.2, P, -10.0)
    lantern(0.0, CABIN_CEIL, -10.5)


def crew_quarters():
    """Quartiers de l'equipage (under the poop deck, floor 4.5, z -17 -> -7): the mess table and its two
    benches on the middle line, bunks along both sides, lanterns."""
    custom("long_table", solid=(-0.55, 0.55, M, M + 0.9, -15.0, -11.0), name="crew_table", x0=-0.55, x1=0.55, z0=-15.0, z1=-11.0, y=M)
    for side in (1, -1):
        custom("bench", name="crew_bench_%s" % ("p" if side > 0 else "s"), x=side * 1.0, z0=-15.0, z1=-11.0, y=M)
        for z in (-14.2, -11.8):
            seat(side * 1.0, M + 0.47, z, side * 1.75, M, z)
    for side in (1, -1):
        for k, z in enumerate((-15.4, -9.0)):
            x = side * (gs.hull_x(z, M + 0.5) - 1.1)
            custom("bunk", solid=(x - 0.48, x + 0.48, M, M + 0.6, z - 0.95, z + 0.95), name="crew_bunk_%s%d" % ("p" if side > 0 else "s", k),
                   p=(x, M, z), l=1.9, w=0.95)
    lantern(0.0, CREW_CEIL, -15.8)
    lantern(0.0, CREW_CEIL, -9.2)


def engine_room():
    """Salle des machines (floor 4.5, z -6 -> 4.5): the boiler under the funnel (modelled by the generator,
    FURNITURE in the grid), a stool for the stoker, lanterns."""
    custom("barrel", solid=(3.1, 3.8, M, M + 0.9, 3.2, 3.9), name="engine_oil_barrel", p=(3.45, M, 3.55))
    seat(2.4, M + 0.47, -3.0, 2.4, M, -1.9)
    custom("bench", name="stoker_stool", x=2.4, z0=-3.3, z1=-2.7, y=M)
    lantern(0.0, ENGINE_CEIL, 1.0)
    lantern(2.8, ENGINE_CEIL, -4.5)


def hold():
    """Cale (the lower deck, floor 1.0): crates and barrels along the sides, lanterns from the beams; the
    centre line stays clear."""
    for k, z in enumerate((-12.0, -8.0, 0.5, 3.0, 11.0)):
        for side in (1, -1):
            x = side * (gs.hull_x(z, H + 0.5) - 1.2)
            if side > 0 and gs.COMPANION_Z[0] - 1 < z < gs.COMPANION_Z[1] + 1:
                continue
            custom("barrel", solid=(x - 0.35, x + 0.35, H, H + 0.9, z - 0.35, z + 0.35), name="hold_barrel_%d%s" % (k, "p" if side > 0 else "s"),
                   p=(x, H, z))
    lantern(0.0, HOLD_CEIL, -10.0)
    lantern(0.0, HOLD_CEIL, 1.0)
    lantern(0.0, HOLD_CEIL, 11.0)


def deck():
    """On the forecastle: a bench along the starboard bulwark, aft of the lantern post."""
    F = gs.FORECASTLE_Y
    custom("bench", name="forecastle_bench", x=-1.25, z0=14.4, z1=15.6, y=F)
    seat(-1.25, F + 0.47, 15.0, -0.45, F, 15.0)


def build():
    BLOCKS.clear()
    SEATS.clear()
    CUSTOM.clear()
    captain_cabin()
    crew_quarters()
    engine_room()
    hold()
    deck()
    return BLOCKS, SEATS


def _cells(g, box, min_overlap=0.2):
    x0, x1, y0, y1, z0, z1 = box
    h = gi.CELL / 2
    ox = np.minimum(g.X + h, x1) - np.maximum(g.X - h, x0)
    oy = np.minimum(g.Y + h, y1) - np.maximum(g.Y - h, y0 + 0.01)
    oz = np.minimum(g.Z + h, z1) - np.maximum(g.Z - h, z0)
    return (ox >= min_overlap - 1e-6) & (oz >= min_overlap - 1e-6) & (oy >= min(min_overlap, y1 - y0 - 0.01) - 1e-6)


def apply_to_grid(g):
    """FURNITURE cells under the solid furniture (on the floor of a room, or on a deck)."""
    free = (g.k == gi.DRY) | (g.k == gi.OUT)
    boxes = [(kwargs.get("name", builder), solid) for builder, kwargs, solid in CUSTOM if solid is not None]
    for i, b in enumerate(BLOCKS):
        if b["solid"]:
            x0, x1, y0, y1, z0, z1 = footprint(b["block"], b["x"], b["y"], b["z"], b["yaw"], b["scale"])
            boxes.append(("%s #%d" % (b["block"], i), (x0, x1, b["y"], y1, z0, z1)))
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
