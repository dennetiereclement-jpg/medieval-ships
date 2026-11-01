#!/usr/bin/env python3
"""tent_adventurer — the small adventurer's tent (reference: scratchpad/ref/tent2_small_adventurer_ref.png).

A small beige A-frame on a plank floor: a ridge pole on two pairs of crossed, slightly leaning poles, the canvas
sagging between the ridge and the ground, torn fringes along the ground, the front of the roof lifted as an awning
on two leaning props (the two front openings either side of the ridge), the back closed, guy ropes to pegs, a
lantern hanging under the ridge at the entrance; inside, a bedroll, crates and a barrel from the decoration mods
(stand-ins when the mods are missing), more crates and a barrel outside by the entrance.

Usage:  python3 tools/tents/generate_tent_adventurer.py      (TENT_OUT=<file>: write only the model there, for previews)
Writes: blockbench/tent_adventurer.bbmodel, the assets copy, textures/entity/tents.png, textures/item/tent_adventurer.png,
        interiors/tent_adventurer_decor.json, tents/tent_adventurer.json (extent + collision boxes for TentType).
Tent-local coordinates: y up, +z = front (entrance), the anchor block at (0, 0, 0).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tentlib as tl  # noqa: E402

NAME = "tent_adventurer"
RIDGE_Y = 3.35
BACK_Z, FRONT_Z, AWNING_Z = -2.8, 1.9, 3.3
HALF_W = 2.5
EDGE_Y = 0.35
FLOOR_Y = 0.12


def build():
    root = tl.Bone(NAME)
    frame = tl.Bone("frame", parent=root)
    cloth = tl.Bone("canvas", parent=root)
    detail = tl.Bone("detail", parent=root)
    furn = tl.Bone("furniture", parent=root)

    # ---- frame: ridge pole (two pieces, a little sag), crossed poles front and back, the awning props
    tl.pole(frame, "ridge_a", (0, RIDGE_Y + 0.08, BACK_Z - 0.25), (0, RIDGE_Y - 0.02, -0.4), d=0.16, extend=0.02)
    tl.pole(frame, "ridge_b", (0, RIDGE_Y - 0.02, -0.4), (0, RIDGE_Y + 0.12, AWNING_Z + 0.25), d=0.16, extend=0.02)
    for s, sn in ((1, "r"), (-1, "l")):
        # front shear legs cross under the ridge; the back pair leans a little more
        tl.post(frame, "front_leg_%s" % sn, (s * 1.3, -0.05, 2.45), (-s * 0.28, RIDGE_Y + 0.32, 2.3), d=0.17)
        tl.post(frame, "back_leg_%s" % sn, (s * 1.2, -0.05, -2.55), (-s * 0.3, RIDGE_Y + 0.25, -2.72), d=0.17)
        # the awning props lean outwards, holding the lifted front corner of the canvas
        tl.post(frame, "prop_%s" % sn, (s * 3.0, -0.05, 3.7), (s * 2.7, 2.1, 3.3), d=0.13)
        # a lashing of rope where the legs cross and at the prop heads
        tl.rope(detail, "lash_front_%s" % sn, (s * 0.2, RIDGE_Y + 0.05, 2.18), (-s * 0.2, RIDGE_Y + 0.2, 2.42), d=0.07)
        tl.rope(detail, "lash_prop_%s" % sn, (s * 2.62, 2.0, 3.2), (s * 2.8, 2.12, 3.42), d=0.07)

    # ---- canvas: two sagging roof panels, the lifted awning halves, the closed back
    for s, sn in ((1, "r"), (-1, "l")):
        reg = "canvas" if s > 0 else "canvas_b"
        tl.canvas_panel(cloth, "roof_%s" % sn, (0, RIDGE_Y + 0.1, BACK_Z), (0, RIDGE_Y + 0.1, FRONT_Z),
                        (s * HALF_W, EDGE_Y, BACK_Z - 0.15), (s * HALF_W, EDGE_Y, FRONT_Z), sag=0.2, nx=4, ny=5, region=reg,
                        fringe=0.28, ripple=0.06)
        # the awning: continues the roof, its outer corner lifted onto the prop (a twisted panel)
        tl.canvas_panel(cloth, "awning_%s" % sn, (0, RIDGE_Y + 0.1, FRONT_Z), (0, RIDGE_Y + 0.2, AWNING_Z),
                        (s * HALF_W, EDGE_Y, FRONT_Z), (s * 2.75, 2.1, AWNING_Z + 0.1), sag=0.1, nx=2, ny=4, region=reg,
                        fringe=0.3, ripple=0.04, sag_dir=(0, -1, 0))
    # back wall: a triangle, bellying a little outwards (backwards)
    tl.canvas_panel(cloth, "back", (-0.08, RIDGE_Y + 0.05, BACK_Z - 0.05), (0.08, RIDGE_Y + 0.05, BACK_Z - 0.05),
                    (-HALF_W, EDGE_Y - 0.05, BACK_Z - 0.2), (HALF_W, EDGE_Y - 0.05, BACK_Z - 0.2), sag=0.08, nx=3, ny=4,
                    region="canvas_b", fringe=0.2, sag_dir=(0, 0, -1))
    # a short pennant of red cloth tied at the ridge front
    tl.pennant(detail, "pennant", (0.12, RIDGE_Y + 0.05, AWNING_Z + 0.2), length=0.55, width=0.22, direction=(0.3, 0, 1))

    # ---- guy ropes and pegs
    for s in (1, -1):
        tl.guy(detail, "guy_prop_%d" % s, (s * 2.72, 2.05, 3.35), (s * 3.9, 0, 4.3))
        tl.guy(detail, "guy_front_%d" % s, (s * 0.1, RIDGE_Y + 0.3, 2.35), (s * 2.3, 0, 4.1))
        tl.guy(detail, "guy_back_%d" % s, (s * 0.1, RIDGE_Y + 0.25, -2.7), (s * 1.9, 0, -4.1))
        tl.guy(detail, "guy_side_%d" % s, (s * HALF_W, EDGE_Y + 0.02, -0.5), (s * 3.3, 0, -0.6), sag=0.0)

    # ---- plank floor inside, a few flagstones at the entrance
    tl.platform(root, "floor", -2.2, 2.2, -2.6, FRONT_Z, FLOOR_Y, th=0.1, plank_w=0.55, along="z")
    for k, (x, z, w, d) in enumerate(((-0.6, 2.5, 1.0, 0.8), (0.5, 2.7, 0.9, 0.7), (-0.1, 3.4, 1.1, 0.7))):
        tl.add_cube(detail, "flag_%d" % k, (x, 0.03, z), tl.EYE, (w, 0.06, d), "stone")

    # ---- furniture: the bedroll of the model, the mods' crates, barrels, sack and lantern
    tl.bedroll(furn, "bedroll", (-1.45, FLOOR_Y, -2.2), (-1.45, FLOOR_Y, -0.2), width=0.85)
    decor = tl.Decor()
    decor.block("furnish:spruce_crate", 1.45, FLOOR_Y, -1.75, facing="front", scale=0.9, fallback="crate")
    decor.block("furnish:oak_crate", 1.55, FLOOR_Y, -0.75, facing="neg_x", scale=0.7, fallback="crate")
    decor.block("farmersdelight:rice_bag", 0.55, FLOOR_Y, -2.05, facing="front", scale=0.7, fallback="sack")
    decor.block("landsoficaria:cypress_barrel", -1.6, FLOOR_Y, -2.0, facing="neg_x", scale=0.85, alt="minecraft:barrel", fallback="barrel")
    decor.block("landsoficaria:cypress_barrel", -3.05, 0.0, 2.3, facing="front", alt="minecraft:barrel", fallback="barrel")
    decor.block("farmersdelight:carrot_crate", 3.15, 0.0, 2.1, facing="front", scale=0.85, fallback="crate")
    decor.block("farmhouse_decorations:chained_kerosene_lantern", 0.0, RIDGE_Y - 0.95, 1.55, facing="front", glow=True,
                fallback="lantern", solid=False)
    decor.fallbacks(root)
    return root, decor


def main():
    tl.setup(NAME)
    root, decor = build()
    tl.export(root, NAME, decor, icon=tl.icon_aframe, visible_box=(8, 5, 0))


if __name__ == "__main__":
    main()
