"""Furniture of the Sky Leviathan (phase 1: the key pieces): blocks of the decoration mods (drawn by the
airship where they stand, moving with it; never placed in the world), the furniture made for it,
and the seats.

  src/main/resources/assets/medievalships/interiors/sky_leviathan_decor.json

Same format and same rules as the Nautilus (tools/nautilus_decor.py, whose block measurements are
reused): each mod block is given by the centre of its bottom face (ship-local) and the direction its
front faces; its footprint becomes solid cells of the interior grid; a block whose mod is missing on a
client is replaced by its stand-in, a box of the same size in the model (bone "fallback_<i>").

Mods used: farmhouse_decorations (Farmhouse Decorations).
"""
import json
import math

import leviathan_interior as li
import leviathan_shape as ls
import nautilus_decor as nd

FACING = nd.FACING
BOUNDS = nd.BOUNDS
FALLBACK_REGION = {"farmhouse_decorations:double_bed": "bedding", "farmhouse_decorations:desk": "organ_wood",
                   "farmhouse_decorations:tall_bookshelf": "books", "farmhouse_decorations:dining_chair": "organ_wood",
                   "farmhouse_decorations:wardrobe": "organ_wood", "farmhouse_decorations:kerosene_lantern": "lantern"}

BLOCKS = []    # dicts: block, x, y, z, yaw, solid, scale
SEATS = []     # dicts: x, y, z, dx, dy, dz
CUSTOM = []    # furniture made for the airship: (builder name, kwargs, solid box or None)
PAINTINGS = []
SWITCHES = []

FD = "farmhouse_decorations:"
M0, LO, HO, CASTLE = li.M0, li.LO, li.HO, li.CASTLE


def block(bid, x, y, z, facing="stern", solid=True, scale=1.0):
    yaw = FACING[facing] if isinstance(facing, str) else float(facing)
    BLOCKS.append({"block": bid, "x": x, "y": y, "z": z, "yaw": yaw, "solid": solid, "scale": scale})
    return len(BLOCKS) - 1


def custom(builder, solid=None, **kwargs):
    """Furniture of generate_leviathan.py (FURNITURE_BUILDERS); solid = (x0, x1, y0, y1, z0, z1) added to the grid."""
    CUSTOM.append((builder, kwargs, solid))


def seat(x, y, z, dx, dy, dz):
    """A seat: sitting point (x, y = seat height, z) and where to stand up (dx, dy, dz)."""
    SEATS.append({"x": x, "y": y, "z": z, "dx": dx, "dy": dy, "dz": dz})


# ---------------------------------------------------------------- rooms
def common_room():
    """Salle commune (reference panel 2): a long heavy table on trestles down the middle, a bench on
    each side, a red rug, lanterns over the table."""
    zt0, zt1 = 6.0, 9.5          # the table, along the ship
    custom("table", solid=(-0.5, 0.5, LO, LO + 0.9, zt0, zt1), p=(0.0, LO, (zt0 + zt1) / 2), length=zt1 - zt0, width=1.0)
    for x in (-1.25, 1.25):
        custom("bench", solid=None, p=(x, LO, (zt0 + zt1) / 2), length=zt1 - zt0 - 0.4, along="z")
        for z in (6.6, 7.75, 8.9):
            seat(x, LO + 0.45, z, x + (0.75 if x > 0 else -0.75), LO + 0.02, z)
    custom("rug", p=(0.0, LO, (zt0 + zt1) / 2), w=3.4, l=5.4)
    for z in (6.6, 8.9):
        custom("hanging_lantern", p=(0.0, M0 - 0.5, z), drop=0.6, name="common_lantern_%d" % (z > 8))


def captain():
    """Cabine du capitaine (panel 3): a big bed with a dark red blanket in the bedroom, the desk with
    its chair and charts in the office, a bookshelf."""
    block(FD + "double_bed", 2.4, M0, -17.2, "stern")
    block(FD + "desk", -0.5, M0, -11.3, "bow")
    block(FD + "dining_chair", 0.0, M0, -10.4, "stern", solid=False)
    seat(0.0, M0 + 0.45, -10.4, 0.0, M0 + 0.02, -9.4)
    block(FD + "tall_bookshelf", -3.3, M0, -9.0, "port")
    custom("chart_sheet", p=(-0.4, M0 + 1.02, -11.3), yaw=0.2)
    custom("rug", p=(0.0, M0, -15.6), w=2.4, l=3.0)
    for z in (-10.2, -15.6):
        custom("hanging_lantern", p=(0.0, CASTLE - 0.5, z), drop=0.5, name="captain_lantern_%d" % (z < -12))


def deck_benches():
    """Benches along the bulwarks of the main deck, facing inboard."""
    for x in (-3.95, 3.95):
        custom("bench", solid=(x - 0.3, x + 0.3, M0, M0 + 0.5, -2.6, -0.4), p=(x, M0, -1.5), length=2.0, along="z")
        for z in (-2.0, -1.0):
            seat(x, M0 + 0.45, z, x - math.copysign(0.8, x), M0 + 0.02, z)


def build():
    BLOCKS.clear()
    SEATS.clear()
    CUSTOM.clear()
    PAINTINGS.clear()
    SWITCHES.clear()
    common_room()
    captain()
    deck_benches()
    return BLOCKS, SEATS


def footprint(b):
    return nd.footprint(b["block"], b["x"], b["y"], b["z"], b["yaw"], b["scale"])


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
        g.set(li.FURNITURE, x0 + 0.05, x1 - 0.05, b["y"] + 0.01, y1, z0 + 0.05, z1 - 0.05, where=g.k == li.DRY)


def write(path):
    data = {"blocks": [], "seats": [{k: round(v, 4) for k, v in s.items()} for s in SEATS], "paintings": PAINTINGS,
            "switches": SWITCHES}
    for i, b in enumerate(BLOCKS):
        data["blocks"].append({"block": b["block"], "x": round(b["x"], 4), "y": round(b["y"], 4), "z": round(b["z"], 4),
                               "yaw": b["yaw"], "scale": b["scale"], "fallback": "fallback_%d" % i})
    with open(path, "w") as f:
        json.dump(data, f, indent=1)


DECOR_PATH = "src/main/resources/assets/medievalships/interiors/sky_leviathan_decor.json"
