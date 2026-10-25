"""Furniture of the Old Corsair: blocks of the decoration mods (drawn by the ship where they stand,
moving with it; never placed in the world), furniture modelled for the ship (tools/generate_corsair.py
draws it), and the seats.

  src/main/resources/assets/medievalships/interiors/old_corsair_decor.json

Same format as tools/nautilus_decor.py (read by fr.medievalships.core.InteriorDecor). A block whose
mod is missing on a client is replaced by its stand-in, a box of the same size in the model (bone
"fallback_<i>"). The solid furniture is added to the interior grid (FURNITURE cells): the players
walk round the tables and the stove.

Phase 1: the key pieces of each room (the big table and benches of the common room, the captain's
bed, desk and chair, the stove of the kitchen, barrels and crates in the hold, lanterns, runners and
rugs) and the seats; the full decoration comes in phase 2.
"""
import json

import corsair_interior as ci
import corsair_shape as cs
import nautilus_decor as nd

FACING = nd.FACING
BOUNDS = nd.BOUNDS
FALLBACK_REGION = {"farmersdelight:stove": "iron", "farmersdelight:cooking_pot": "iron", "landsoficaria:fir_barrel": "wood_mid",
                   "landsoficaria:cypress_barrel": "wood_mid", "furnish:spruce_crate": "wood_light", "furnish:oak_crate": "wood_light",
                   "farmhouse_decorations:chained_kerosene_lantern": "lantern"}

BLOCKS = []   # dicts: block, x, y, z, yaw, solid, scale
SEATS = []    # dicts: x, y, z, dx, dy, dz
CUSTOM = []   # furniture drawn by generate_corsair: (builder name, kwargs, solid box or None)

FD = "farmhouse_decorations:"
FU = "furnish:"
FR = "farmersdelight:"
LI = "landsoficaria:"

M, L, H, C = cs.MAIN_DECK_Y, cs.LOWER_FLOOR_Y, cs.HOLD_FLOOR_Y, cs.CABIN_FLOOR_Y


def block(bid, x, y, z, facing="stern", solid=True, scale=1.0):
    yaw = FACING[facing] if isinstance(facing, str) else float(facing)
    BLOCKS.append({"block": bid, "x": x, "y": y, "z": z, "yaw": yaw, "solid": solid, "scale": scale})
    return len(BLOCKS) - 1


def custom(builder, solid=None, **kwargs):
    CUSTOM.append((builder, kwargs, solid))


def seat(x, y, z, dx, dy, dz):
    """A seat: where the passenger sits (seat height y) and where he stands up (dx, dy = floor, dz)."""
    SEATS.append({"x": x, "y": y, "z": z, "dx": dx, "dy": dy + 0.02, "dz": dz})


def common_room():
    """Salle commune (reference panel 2): a long rustic table along the starboard side with a bench on
    each side, barrels, lanterns hanging from the beams, a rug under the table."""
    x0, x1, z0, z1 = -2.9, -1.5, -0.2, 7.2
    custom("long_table", solid=(x0, x1, L, L + 0.85, z0, z1), name="common_table", x0=x0, x1=x1, z0=z0, z1=z1, y=L)
    for k, (bx, sit_dx) in enumerate(((-3.55, -0.0), (-0.85, 0.0))):
        custom("bench", name="common_bench_%d" % k, x=bx, z0=z0 + 0.2, z1=z1 - 0.2, y=L)
        for z in (0.6, 2.4, 4.2, 6.0):
            # facing the table: the stand-up spot is away from it
            seat(bx, L + 0.47, z, bx, L, z)
    custom("rug", name="common_rug", p=(-2.2, L, 3.5), w=3.6, l=8.4, region="rug")
    for z in (1.0, 5.5):
        block(FD + "chained_kerosene_lantern", -2.2, M - 0.5 - 1.0, z, "stern", solid=False)
    for k, (x, z) in enumerate(((3.6, 6.9), (3.6, 7.6), (2.9, 7.6))):
        block(LI + "fir_barrel", x, L, z, "stern")


def captain_cabin():
    """Cabine du capitaine (panel 3): the bed with its red blanket against the port side, the desk with
    its sea chart and the captain's chair, a chest, a red rug, a lantern."""
    custom("bunk", solid=(2.6, 4.1, C, C + 0.7, -20.3, -18.2), name="captain_bed", p=(3.35, C, -19.25), l=2.0, w=1.3)
    custom("desk", solid=(-3.6, -1.8, C, C + 0.8, -18.6, -17.6), name="captain_desk", p=(-2.7, C, -18.1))
    custom("chair", name="captain_chair", p=(-2.7, C, -17.2), facing=3.14159)
    seat(-2.7, C + 0.47, -17.2, -2.7, C, -16.4)
    custom("chest", solid=(2.8, 3.9, C, C + 0.6, -17.4, -16.8), name="captain_chest", p=(3.35, C, -17.1))
    custom("rug", name="captain_rug", p=(0.0, C, -17.6), w=3.0, l=3.6, region="rug")
    block(FD + "chained_kerosene_lantern", 0.0, cs.QUARTERDECK_Y - 0.5 - 1.0, -17.5, "stern", solid=False)


def kitchen():
    """Cuisine (panel 5): the stone hearth with its fire against the bow bulkhead, a work table, the
    stove and pot of Farmer's Delight, barrels of provisions."""
    custom("hearth", solid=(-1.6, 1.6, L, L + 2.6, 12.9, 14.0), name="kitchen_hearth", p=(0.0, L, 13.45), w=3.2)
    custom("work_table", solid=(-2.9, -1.7, L, L + 0.9, 9.4, 11.6), name="kitchen_table", p=(-2.3, L, 10.5), w=1.2, l=2.2)
    block(FR + "stove", 2.9, L, 12.4, "port")
    block(FR + "cooking_pot", 2.9, L + 1.0, 12.4, "port", solid=False)
    for k, z in enumerate((9.2, 10.2)):
        block(LI + "fir_barrel", 3.2, L, z, "stern")
    block(FD + "chained_kerosene_lantern", 0.0, M - 0.5 - 1.0, 10.5, "stern", solid=False)


def hold():
    """Cale (panel 4): crates and barrels stowed along the sides, between the pillars."""
    for k, z in enumerate((-12.0, -11.0, -10.0, 6.0, 7.0, 8.0)):
        block(LI + ("fir_barrel" if k % 2 else "cypress_barrel"), 3.0, H, z, "stern")
        block(FU + ("spruce_crate" if k % 2 else "oak_crate"), -3.0, H, z, "stern")
    for k, z in enumerate((-6.0, 0.0)):
        block(FD + "chained_kerosene_lantern", 0.0, L - 0.5 - 1.0, z + 3.0 * (k == 1), "stern", solid=False)


def coursive_and_crew():
    """Coursive (panel 6): a red runner along the centre line, lanterns; the crew quarters: bunks."""
    custom("rug", name="coursive_runner", p=(0.0, L, -7.5), w=1.0, l=10.5, region="carpet")
    for z in (-11.0, -6.0, -3.0):
        block(FD + "chained_kerosene_lantern", 0.0, M - 0.5 - 1.0, z, "stern", solid=False)
    for side in (1, -1):
        for k, z in enumerate((-12.0, -9.6)):
            x = side * 3.6
            custom("bunk", solid=(x - 0.5, x + 0.5, L, L + 0.7, z - 0.95, z + 0.95), name="crew_bunk_%d_%d" % (side > 0, k), p=(x, L, z),
                   l=1.9, w=1.0)


def deck():
    """Main deck seats: two benches against the bulwarks, amidships between the two masts."""
    for side in (1, -1):
        x = side * 3.75
        custom("bench", name="deck_bench_%d" % (side > 0), x=x, z0=-2.4, z1=-0.4, y=M)
        for z in (-1.9, -0.9):
            seat(x, M + 0.47, z, x - side * 0.8, M, z)
    custom("boat", solid=(-0.8, 0.8, cs.QUARTERDECK_Y, cs.QUARTERDECK_Y + 0.9, -20.4, -17.2), name="boat", c=(0, cs.QUARTERDECK_Y + 0.3, -18.8))


def build():
    BLOCKS.clear()
    SEATS.clear()
    CUSTOM.clear()
    common_room()
    captain_cabin()
    kitchen()
    hold()
    coursive_and_crew()
    deck()
    return BLOCKS, SEATS


def apply_to_grid(g):
    """FURNITURE cells under the solid furniture (on the floor of a room, or on a deck)."""
    for builder, kwargs, solid in CUSTOM:
        if solid is not None:
            x0, x1, y0, y1, z0, z1 = solid
            g.set(ci.FURNITURE, x0 + 0.05, x1 - 0.05, y0 + 0.01, y1, z0 + 0.05, z1 - 0.05, where=(g.k == ci.DRY) | (g.k == ci.OUT))
    for b in BLOCKS:
        if not b["solid"]:
            continue
        x0, x1, y0, y1, z0, z1 = nd.footprint(b["block"], b["x"], b["y"], b["z"], b["yaw"], b["scale"])
        g.set(ci.FURNITURE, x0 + 0.05, x1 - 0.05, b["y"] + 0.01, y1, z0 + 0.05, z1 - 0.05, where=g.k == ci.DRY)


def write(path):
    data = {"blocks": [], "seats": [{k: round(v, 4) for k, v in s.items()} for s in SEATS], "paintings": [], "switches": []}
    for i, b in enumerate(BLOCKS):
        data["blocks"].append({"block": b["block"], "x": round(b["x"], 4), "y": round(b["y"], 4), "z": round(b["z"], 4),
                               "yaw": b["yaw"], "scale": b["scale"], "fallback": "fallback_%d" % i})
    with open(path, "w") as f:
        json.dump(data, f, indent=1)


DECOR_PATH = "src/main/resources/assets/medievalships/interiors/old_corsair_decor.json"
