#!/usr/bin/env python3
"""tent_camp — the rustic triangular camp tent (reference: scratchpad/ref/tent4_camp_ref.png).

A simple A-frame: a ridge pole on a tall front post and a pair of crossed back legs, the beige canvas sagging from the
ridge to the ground on the right, while the left side breaks at an eave pole held by two leaning props and hangs on as
a loose torn flap; the front is open between two leaning posts (a lantern on a bracket of the right one), the back is
closed. Guy ropes to pegs all round, a few flagstones at the entrance; inside, a plank floor with a bedroll and the
decoration mods' crates, sack, basket and barrel (stand-ins when a mod is missing), two crates outside by the door.

Usage:  python3 tools/tents/generate_tent_camp.py      (TENT_OUT=<file>: write only the model there, for previews)
Writes: blockbench/tent_camp.bbmodel, the assets copy, textures/entity/tents.png, textures/item/tent_camp.png,
        interiors/tent_camp_decor.json, tents/tent_camp.json (extent + collision boxes for TentType).
Tent-local coordinates: y up, +z = front (entrance), the anchor block at (0, 0, 0).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tentlib as tl  # noqa: E402

NAME = "tent_camp"
RIDGE_Y = 3.55
BACK_Z, FRONT_Z = -2.7, 2.2
HALF_R = 2.45          # right slope reaches the ground this far out
EAVE_X, EAVE_Y = -2.35, 1.8   # left slope breaks here on the eave pole
FLAP_X, FLAP_Y = -2.95, 0.55  # the loose flap hangs down to here
EDGE_Y = 0.35
FLOOR_Y = 0.12


def build():
    root = tl.Bone(NAME)
    frame = tl.Bone("frame", parent=root)
    cloth = tl.Bone("canvas", parent=root)
    detail = tl.Bone("detail", parent=root)
    furn = tl.Bone("furniture", parent=root)

    # ---- frame: ridge pole (two pieces, a little sag), the tall front post through the ridge, crossed back legs
    tl.pole(frame, "ridge_a", (0, RIDGE_Y + 0.06, BACK_Z - 0.3), (0, RIDGE_Y - 0.04, -0.3), d=0.16, extend=0.02)
    tl.pole(frame, "ridge_b", (0, RIDGE_Y - 0.04, -0.3), (0, RIDGE_Y + 0.08, FRONT_Z + 0.35), d=0.16, extend=0.02)
    tl.post(frame, "front_post", (0.12, -0.05, 2.35), (-0.04, RIDGE_Y + 0.7, 2.2), d=0.18)
    for s, sn in ((1, "r"), (-1, "l")):
        tl.post(frame, "back_leg_%s" % sn, (s * 1.25, -0.05, -2.5), (-s * 0.3, RIDGE_Y + 0.3, -2.65), d=0.17)
        # the door posts lean a little outwards, standing just ahead of the canvas
        tl.post(frame, "door_post_%s" % sn, (s * 1.55, -0.05, 2.55), (s * 1.75, 2.45, 2.4), d=0.16)
        tl.rope(detail, "lash_door_%s" % sn, (s * 1.6, 2.2, 2.3), (s * 1.9, 2.35, 2.55), d=0.07)
    tl.rope(detail, "lash_ridge", (-0.2, RIDGE_Y + 0.1, 2.05), (0.2, RIDGE_Y + 0.25, 2.35), d=0.07)
    tl.rope(detail, "lash_back", (-0.2, RIDGE_Y + 0.05, -2.75), (0.2, RIDGE_Y + 0.2, -2.5), d=0.07)
    # the eave pole of the left flap on two leaning props
    tl.pole(frame, "eave", (EAVE_X, EAVE_Y, BACK_Z - 0.2), (EAVE_X - 0.05, EAVE_Y + 0.05, FRONT_Z + 0.5), d=0.12, extend=0.02)
    tl.post(frame, "prop_front", (-3.45, -0.05, 2.85), (EAVE_X - 0.1, EAVE_Y + 0.12, FRONT_Z + 0.25), d=0.14)
    tl.post(frame, "prop_back", (-3.35, -0.05, -3.0), (EAVE_X - 0.1, EAVE_Y + 0.08, BACK_Z - 0.1), d=0.14)
    tl.rope(detail, "lash_prop_f", (EAVE_X - 0.2, EAVE_Y - 0.05, FRONT_Z + 0.1), (EAVE_X + 0.05, EAVE_Y + 0.15, FRONT_Z + 0.4), d=0.07)
    tl.rope(detail, "lash_prop_b", (EAVE_X - 0.2, EAVE_Y - 0.05, BACK_Z - 0.25), (EAVE_X + 0.05, EAVE_Y + 0.12, BACK_Z + 0.05), d=0.07)
    # the lantern bracket on the right door post
    tl.pole(detail, "bracket", (1.7, 2.2, 2.45), (2.25, 2.3, 2.6), d=0.08, region="wood_dark")

    # ---- canvas: the right slope to the ground, the left slope broken at the eave with a hanging flap, the back
    tl.canvas_panel(cloth, "roof_r", (0, RIDGE_Y + 0.1, BACK_Z), (0, RIDGE_Y + 0.1, FRONT_Z),
                    (HALF_R, EDGE_Y, BACK_Z - 0.1), (HALF_R, EDGE_Y, FRONT_Z + 0.1), sag=0.2, nx=4, ny=5, region="canvas",
                    fringe=0.3, ripple=0.06)
    tl.canvas_panel(cloth, "roof_l", (0, RIDGE_Y + 0.1, BACK_Z), (0, RIDGE_Y + 0.1, FRONT_Z),
                    (EAVE_X, EAVE_Y + 0.08, BACK_Z - 0.15), (EAVE_X, EAVE_Y + 0.08, FRONT_Z + 0.3), sag=0.18, nx=4, ny=4,
                    region="canvas_b", ripple=0.04)
    tl.canvas_panel(cloth, "flap_l", (EAVE_X, EAVE_Y + 0.08, BACK_Z - 0.15), (EAVE_X, EAVE_Y + 0.08, FRONT_Z + 0.3),
                    (FLAP_X, FLAP_Y, BACK_Z - 0.25), (FLAP_X - 0.25, FLAP_Y - 0.1, FRONT_Z + 0.5), sag=0.14, nx=4, ny=3,
                    region="canvas", fringe=0.32, ripple=0.08, sag_dir=(-1, 0, 0))
    # back wall: a closed triangle bellying backwards, torn along the ground
    tl.canvas_panel(cloth, "back", (-0.08, RIDGE_Y + 0.05, BACK_Z - 0.05), (0.08, RIDGE_Y + 0.05, BACK_Z - 0.05),
                    (-EAVE_X, EDGE_Y - 0.05, BACK_Z - 0.2), (HALF_R, EDGE_Y - 0.05, BACK_Z - 0.2), sag=0.08, nx=3, ny=4,
                    region="canvas_b", fringe=0.2, sag_dir=(0, 0, -1))

    # ---- guy ropes and pegs
    tl.guy(detail, "guy_front_r", (0.05, RIDGE_Y + 0.55, 2.3), (2.0, 0, 3.9))
    tl.guy(detail, "guy_front_l", (-0.05, RIDGE_Y + 0.55, 2.3), (-1.6, 0, 4.0))
    tl.guy(detail, "guy_prop_f", (EAVE_X - 0.15, EAVE_Y + 0.1, FRONT_Z + 0.3), (-3.9, 0, 3.4))
    tl.guy(detail, "guy_prop_b", (EAVE_X - 0.15, EAVE_Y + 0.05, BACK_Z - 0.15), (-3.8, 0, -3.5))
    tl.guy(detail, "guy_prop_s", (EAVE_X - 0.15, EAVE_Y + 0.05, 0.1), (-3.9, 0, -0.2), sag=0.02)
    tl.guy(detail, "guy_back_r", (0.1, RIDGE_Y + 0.25, -2.7), (1.7, 0, -3.9))
    tl.guy(detail, "guy_back_l", (-0.1, RIDGE_Y + 0.25, -2.7), (-1.5, 0, -3.9))
    for z in (-1.6, 0.4, 1.9):
        tl.guy(detail, "guy_side_%d" % int(z * 10), (HALF_R, EDGE_Y + 0.02, z), (3.3, 0, z - 0.2), sag=0.0)

    # ---- plank floor inside, flagstones at the entrance
    tl.platform(root, "floor", -2.1, 2.1, -2.5, FRONT_Z, FLOOR_Y, th=0.1, plank_w=0.55, along="z")
    for k, (x, z, w, d) in enumerate(((-0.7, 2.75, 0.9, 0.7), (0.4, 2.9, 1.0, 0.8), (-0.2, 3.6, 1.1, 0.7), (0.9, 3.75, 0.8, 0.6))):
        tl.add_cube(detail, "flag_%d" % k, (x, 0.03, z), tl.EYE, (w, 0.06, d), "stone")

    # ---- furniture: the bedroll of the model, the mods' crates, basket, sack and barrel, the lantern on its bracket
    tl.bedroll(furn, "bedroll", (-1.2, FLOOR_Y, -2.15), (-1.2, FLOOR_Y, -0.15), width=0.85)
    decor = tl.Decor()
    # the small storage along the right wall and at the back
    decor.block("furnish:spruce_crate", 1.35, FLOOR_Y, -1.9, facing="front", scale=0.85, fallback="crate")
    decor.block("farmersdelight:potato_crate", 1.4, FLOOR_Y, -1.0, facing="neg_x", scale=0.7, fallback="crate")
    decor.block("farmersdelight:rice_bag", 0.35, FLOOR_Y, -2.05, facing="pos_x", scale=0.7, fallback="sack")
    decor.block("farmersdelight:wooden_basket", 1.4, FLOOR_Y, 0.0, facing="front", scale=0.6, fallback="crate")
    decor.block("landsoficaria:cypress_barrel", -1.5, FLOOR_Y, 1.3, facing="pos_x", scale=0.8, alt="minecraft:barrel", fallback="barrel")
    # crates either side of the entrance, outside
    decor.block("furnish:dark_oak_crate", -2.25, 0.0, 3.15, facing="front", scale=0.9, fallback="crate")
    decor.block("furnish:oak_crate", -2.25, 0.9, 3.15, facing="neg_x", scale=0.7, fallback="crate")
    decor.block("furnish:spruce_crate", 2.3, 0.0, 3.1, facing="front", fallback="crate")
    decor.block("farmhouse_decorations:chained_kerosene_lantern", 2.25, 1.3, 2.62, facing="front", glow=True,
                fallback="lantern", solid=False)
    decor.fallbacks(root)
    return root, decor


def main():
    tl.setup(NAME)
    root, decor = build()
    tl.export(root, NAME, decor, icon=tl.icon_aframe, visible_box=(8, 5, 0))


if __name__ == "__main__":
    main()
