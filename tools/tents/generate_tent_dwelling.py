#!/usr/bin/env python3
"""tent_dwelling — the dwelling tent (references: scratchpad/ref/tent5_dwelling_interior_ref.png, the furnished
interior with its red rug, and tent5b_dwelling_pavilion_ref.png, the open pavilion with tables and benches).

Two parts under one aged beige canvas, ~7 x 5 x 8 blocks:
  * at the back, the dwelling: a gable roof on a ridge pole and leaning corner posts, closed canvas side and
    back walls, a plank floor, a wide entrance between two lantern posts under a closed front gable; inside, a
    red rug, a bed, a small table with a lantern, chests, a cabinet, sacks and crates from the decoration mods;
  * in front, the pavilion: a lower, sagging flat awning with torn fringes on four leaning posts with braces and
    guy ropes, a long rustic table with two benches (part of the model, with plates and bottles from the mods),
    a side table, barrels and crates, lanterns hanging from the beams.

Usage:  python3 tools/tents/generate_tent_dwelling.py      (TENT_OUT=<file>: write only the model there, for previews)
Writes: blockbench/tent_dwelling.bbmodel, the assets copy, textures/entity/tents.png, textures/item/tent_dwelling.png,
        interiors/tent_dwelling_decor.json, tents/tent_dwelling.json (extent + collision boxes for TentType).
Tent-local coordinates: y up, +z = front (entrance and pavilion), the anchor block at (0, 0, 0) under the floor.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tentlib as tl  # noqa: E402

NAME = "tent_dwelling"
RIDGE_Y = 4.55          # ridge of the dwelling
EAVE_Y = 2.5            # eaves of the dwelling roof
HALF_W = 3.3            # half width at the eaves
ZB, ZM, ZF = -4.0, 0.6, 4.3   # back wall, dwelling front / pavilion start, pavilion front
FLOOR_Y = 0.13          # plank floor top (over the anchor block's 2 px slab)
CANOPY_Y = 3.3          # pavilion awning where it meets the dwelling
CANOPY_FRONT_Y = 3.0    # pavilion awning at the front posts


def dwelling(frame, cloth, detail):
    # ---- frame: ridge, eave beams, four leaning corner posts, a king post at the back, rafters and collar ties
    tl.pole(frame, "ridge", (0, RIDGE_Y, ZB - 0.35), (0, RIDGE_Y + 0.06, ZM + 0.4), d=0.17, extend=0.02)
    for s, sn in ((1, "r"), (-1, "l")):
        tl.pole(frame, "eave_%s" % sn, (s * 3.1, EAVE_Y + 0.05, ZB - 0.25), (s * 3.12, EAVE_Y, ZM + 0.25), d=0.14, extend=0.02)
        tl.post(frame, "corner_back_%s" % sn, (s * 2.95, -0.05, ZB + 0.2), (s * 3.15, EAVE_Y + 0.12, ZB + 0.05), d=0.18)
        # the front corners carry the eaves and the pavilion awning: taller
        tl.post(frame, "corner_front_%s" % sn, (s * 2.95, -0.05, ZM - 0.2), (s * 3.2, CANOPY_Y + 0.1, ZM - 0.05), d=0.18)
        # the entrance posts (lanterns hang on them) and their lintel
        tl.post(frame, "door_%s" % sn, (s * 1.35, -0.05, ZM + 0.25), (s * 1.22, 3.25, ZM + 0.2), d=0.15)
        tl.pole(detail, "door_bracket_%s" % sn, (s * 1.25, 2.0, ZM + 0.25), (s * 1.6, 2.15, ZM + 0.65), d=0.07, region="wood_dark")
    tl.pole(frame, "lintel", (-1.35, 3.1, ZM + 0.25), (1.35, 3.1, ZM + 0.25), d=0.12, extend=0.1)
    tl.post(frame, "king", (0.05, -0.05, ZB + 0.3), (0, RIDGE_Y - 0.1, ZB + 0.3), d=0.17)
    for k, z in enumerate((ZB + 1.1, (ZB + ZM) / 2 + 0.1, ZM - 0.75)):
        for s in (1, -1):
            tl.pole(frame, "rafter_%d_%d" % (k, s), (0, RIDGE_Y - 0.12, z), (s * 3.1, EAVE_Y - 0.08, z), d=0.1, extend=0.05)
        tl.pole(frame, "collar_%d" % k, (-1.9, 3.3, z), (1.9, 3.3, z), d=0.1, region="wood_dark", extend=0.05)
        tl.rope(detail, "collar_lash_%d" % k, (-1.85, 3.2, z - 0.1), (-1.75, 3.42, z + 0.1), d=0.06)

    # ---- canvas: two sagging roof panels with torn eaves, closed side and back walls, the front gable and jambs
    for s, sn in ((1, "r"), (-1, "l")):
        reg = "canvas" if s > 0 else "canvas_b"
        tl.canvas_panel(cloth, "roof_%s" % sn, (0, RIDGE_Y + 0.12, ZB - 0.35), (0, RIDGE_Y + 0.12, ZM + 0.4),
                        (s * HALF_W, EAVE_Y - 0.05, ZB - 0.45), (s * (HALF_W + 0.05), EAVE_Y - 0.1, ZM + 0.5), sag=0.26,
                        nx=5, ny=5, region=reg, fringe=0.3, ripple=0.06)
        # side walls hang from under the eaves and flare out a little at the ground
        tl.canvas_panel(cloth, "wall_%s" % sn, (s * 3.05, EAVE_Y - 0.02, ZB - 0.05), (s * 3.05, EAVE_Y - 0.02, ZM - 0.25),
                        (s * 3.35, 0.04, ZB - 0.15), (s * 3.35, 0.04, ZM - 0.2), sag=0.1, nx=5, ny=3,
                        region="canvas_b" if s > 0 else "canvas", ripple=0.03, sag_dir=(s, 0, 0))
        tl.collide((s * 3.0, 0, ZB - 0.15, s * 3.4, EAVE_Y, ZM - 0.2))
        # front jambs either side of the entrance, under the roof slope
        tl.canvas_panel(cloth, "jamb_%s" % sn, (s * 1.95, 3.2, ZM + 0.05), (s * 3.15, 2.45, ZM + 0.05),
                        (s * 1.95, 0.04, ZM + 0.12), (s * 3.35, 0.04, ZM + 0.12), sag=0.06, nx=2, ny=3,
                        region="canvas_b", ripple=0.02, sag_dir=(0, 0, 1))
        tl.collide((s * 1.95, 0, ZM - 0.1, s * 3.4, 3.1, ZM + 0.2))
    # back wall: rectangle and gable, bellying backwards
    tl.canvas_panel(cloth, "back_low", (-3.1, EAVE_Y - 0.02, ZB - 0.1), (3.1, EAVE_Y - 0.02, ZB - 0.1),
                    (-3.35, 0.04, ZB - 0.22), (3.35, 0.04, ZB - 0.22), sag=0.1, nx=5, ny=3, region="canvas", ripple=0.03,
                    sag_dir=(0, 0, -1))
    tl.canvas_panel(cloth, "back_gable", (-0.1, RIDGE_Y, ZB - 0.1), (0.1, RIDGE_Y, ZB - 0.1),
                    (-3.1, EAVE_Y - 0.05, ZB - 0.12), (3.1, EAVE_Y - 0.05, ZB - 0.12), sag=0.07, nx=3, ny=3,
                    region="canvas_b", sag_dir=(0, 0, -1))
    tl.collide((-3.4, 0, ZB - 0.3, 3.4, EAVE_Y + 0.3, ZB + 0.05))
    # front gable: closed triangle above the entrance, its torn hem hanging over the awning junction
    tl.canvas_panel(cloth, "front_gable", (-0.1, RIDGE_Y + 0.02, ZM + 0.3), (0.1, RIDGE_Y + 0.02, ZM + 0.3),
                    (-2.4, 3.05, ZM + 0.32), (2.4, 3.05, ZM + 0.32), sag=0.06, nx=3, ny=2, region="canvas",
                    fringe=0.22, sag_dir=(0, 0, 1))
    # tied-back door flaps either side of the entrance
    for s in (1, -1):
        tl.canvas_panel(cloth, "flap_%d" % s, (s * 1.3, 3.0, ZM + 0.3), (s * 1.55, 3.0, ZM + 0.42),
                        (s * 1.45, 0.3, ZM + 0.55), (s * 1.85, 0.3, ZM + 0.75), sag=0.12, nx=1, ny=3, region="canvas_b",
                        fringe=0.2, sag_dir=(s, 0, 0.6))
        tl.rope(detail, "flap_tie_%d" % s, (s * 1.3, 1.3, ZM + 0.35), (s * 1.75, 1.35, ZM + 0.75), d=0.05)
    tl.pennant(detail, "pennant", (0.1, RIDGE_Y + 0.04, ZM + 0.45), length=0.6, width=0.24, direction=(0.25, 0, 1))

    # ---- guy ropes off the back corners and the eaves
    for s in (1, -1):
        tl.guy(detail, "guy_back_%d" % s, (s * 3.1, EAVE_Y, ZB - 0.1), (s * 3.55, 0, ZB - 0.55))
        tl.guy(detail, "guy_side_%d" % s, (s * 3.15, EAVE_Y, -1.6), (s * 3.7, 0, -1.9), sag=0.03)
        # inside, tie ropes cross the side walls from the eave beam down to the floor corners
        tl.rope(detail, "wall_tie_a_%d" % s, (s * 3.0, EAVE_Y - 0.1, ZB + 0.3), (s * 3.05, FLOOR_Y + 0.1, ZM - 0.6), d=0.045)
        tl.rope(detail, "wall_tie_b_%d" % s, (s * 3.0, EAVE_Y - 0.1, ZM - 0.4), (s * 3.05, FLOOR_Y + 0.1, ZB + 0.5), d=0.045)
    # the back wall's inner frame: a rail and two braces from the king post, as on the reference interior
    tl.pole(detail, "back_rail", (-3.0, 1.45, ZB + 0.14), (3.0, 1.45, ZB + 0.14), d=0.09, region="wood_dark", extend=0.03)
    for s in (1, -1):
        tl.pole(detail, "back_brace_%d" % s, (s * 0.15, 0.3, ZB + 0.16), (s * 2.9, 2.3, ZB + 0.16), d=0.08, region="wood_dark")

    # ---- plank floor (over the anchor block), a stone step at the entrance
    tl.platform(frame, "floor", -3.0, 3.0, ZB + 0.05, ZM + 0.15, FLOOR_Y, th=0.1, plank_w=0.6, along="z")
    tl.add_cube(detail, "step", (0, 0.04, ZM + 0.55), tl.EYE, (2.4, 0.08, 0.7), "stone")


def pavilion(frame, cloth, detail, furn):
    # ---- frame: two leaning front posts, side beams from the dwelling's front corners, a front beam, braces
    for s, sn in ((1, "r"), (-1, "l")):
        tl.post(frame, "pav_post_%s" % sn, (s * 2.85, -0.05, ZF - 0.35), (s * 3.15, CANOPY_FRONT_Y + 0.12, ZF - 0.15), d=0.18)
        tl.pole(frame, "pav_side_beam_%s" % sn, (s * 3.15, CANOPY_Y + 0.02, ZM - 0.1), (s * 3.12, CANOPY_FRONT_Y + 0.05, ZF - 0.1),
                d=0.13, extend=0.1)
        # braces between the post and the beams (as on the reference pavilion)
        tl.pole(detail, "pav_brace_a_%s" % sn, (s * 3.0, 2.2, ZF - 0.25), (s * 3.1, CANOPY_FRONT_Y - 0.05, ZF - 1.0), d=0.08, region="wood_dark")
        tl.pole(detail, "pav_brace_b_%s" % sn, (s * 3.0, 2.2, ZF - 0.25), (s * 2.3, CANOPY_FRONT_Y - 0.02, ZF - 0.2), d=0.08, region="wood_dark")
        tl.pole(detail, "pav_brace_c_%s" % sn, (s * 3.05, 2.3, ZM - 0.1), (s * 3.1, CANOPY_Y - 0.05, ZM + 0.75), d=0.08, region="wood_dark")
        tl.rope(detail, "pav_lash_%s" % sn, (s * 3.0, CANOPY_FRONT_Y - 0.1, ZF - 0.3), (s * 3.25, CANOPY_FRONT_Y + 0.12, ZF - 0.05), d=0.06)
        tl.guy(detail, "guy_pav_%d" % s, (s * 3.1, CANOPY_FRONT_Y, ZF - 0.2), (s * 3.6, 0, ZF + 0.4))
        tl.guy(detail, "guy_pav_side_%d" % s, (s * 3.15, CANOPY_Y - 0.4, 2.3), (s * 3.7, 0, 2.6), sag=0.03)
    tl.pole(frame, "pav_front_beam", (-3.2, CANOPY_FRONT_Y, ZF - 0.2), (3.2, CANOPY_FRONT_Y, ZF - 0.2), d=0.13, extend=0.1)
    tl.pole(frame, "pav_mid_beam", (-3.15, CANOPY_Y - 0.15, 2.4), (3.15, CANOPY_Y - 0.15, 2.4), d=0.1, region="wood_dark", extend=0.05)

    # ---- the awning: one wide sagging sheet, torn along the front and the sides
    tl.canvas_panel(cloth, "awning", (-3.3, CANOPY_Y + 0.08, ZM + 0.05), (3.3, CANOPY_Y + 0.08, ZM + 0.05),
                    (-3.4, CANOPY_FRONT_Y + 0.08, ZF + 0.25), (3.4, CANOPY_FRONT_Y + 0.08, ZF + 0.25), sag=0.3, nx=6, ny=4,
                    region="canvas", fringe=0.32, ripple=0.05)
    for s in (1, -1):
        tl.canvas_panel(cloth, "awning_side_%d" % s, (s * 3.3, CANOPY_Y + 0.08, ZM + 0.05), (s * 3.4, CANOPY_FRONT_Y + 0.08, ZF + 0.25),
                        (s * 3.4, CANOPY_Y - 0.3, ZM + 0.05), (s * 3.5, CANOPY_FRONT_Y - 0.3, ZF + 0.25), sag=0.04, nx=4, ny=1,
                        region="canvas_b", fringe=0.22, ripple=0.02, sag_dir=(s, 0, 0))
    tl.pennant(detail, "pav_pennant", (-3.3, CANOPY_FRONT_Y + 0.1, ZF - 0.1), length=0.5, width=0.2, direction=(-0.4, 0, 1))

    # ---- flagstones under the pavilion
    for k, (x, z, w, d) in enumerate(((-1.9, 1.3, 1.2, 0.9), (0.9, 1.1, 1.0, 0.8), (-0.4, 3.9, 1.3, 0.8), (2.1, 3.3, 1.0, 1.0),
                                      (-2.4, 2.9, 0.9, 0.9), (1.6, 2.1, 0.8, 0.7))):
        tl.add_cube(detail, "flag_%d" % k, (x, 0.025, z), tl.EYE, (w, 0.05, d), "stone")

    # ---- the long table and its two benches (model furniture, solid)
    tx0, tx1, tz0, tz1, ty = -1.8, 1.8, 2.1, 3.0, 0.95
    for k in range(3):
        za = tz0 + k * (tz1 - tz0) / 3
        tl.add_cube(furn, "table_top_%d" % k, (0 + (k % 2) * 0.03, ty - 0.04, za + (tz1 - tz0) / 6), tl.EYE,
                    (tx1 - tx0 - 0.04 * k, 0.08, (tz1 - tz0) / 3 * 0.96), "plank", u_dir=tl.v3(1, 0, 0))
    tl.add_cube(furn, "table_apron", (0, ty - 0.16, (tz0 + tz1) / 2), tl.EYE, (tx1 - tx0 - 0.4, 0.14, tz1 - tz0 - 0.3), "wood_dark")
    for sx in (1, -1):
        for sz in (1, -1):
            tl.pole(furn, "table_leg_%d_%d" % (sx, sz), (sx * (tx1 - 0.3), 0, (tz0 + tz1) / 2 + sz * 0.3),
                    (sx * (tx1 - 0.25), ty - 0.08, (tz0 + tz1) / 2 + sz * 0.33), d=0.13, region="wood_dark")
        tl.pole(furn, "table_stretcher_%d" % sx, (sx * (tx1 - 0.28), 0.3, tz0 + 0.15), (sx * (tx1 - 0.28), 0.3, tz1 - 0.15), d=0.08,
                region="wood_dark")
    tl.collide((tx0, 0, tz0, tx1, ty, tz1))
    for sz, z in ((-1, tz0 - 0.5), (1, tz1 + 0.5)):
        tl.add_cube(furn, "bench_%d" % sz, (0, 0.47, z), tl.EYE, (3.0, 0.07, 0.36), "plank", u_dir=tl.v3(1, 0, 0))
        for sx in (1, -1):
            tl.pole(furn, "bench_leg_%d_%d" % (sz, sx), (sx * 1.25, 0, z), (sx * 1.2, 0.44, z), d=0.1, region="wood_dark")
        tl.collide((-1.5, 0, z - 0.18, 1.5, 0.5, z + 0.18))


def furniture_decor():
    decor = tl.Decor()
    # ---- inside the dwelling: rug, bed, bedside stool, table with a lantern, storage
    decor.block("farmhouse_decorations:rug_3x_3", 0.35, FLOOR_Y, -1.35, facing="front", scale=1.2, alt="minecraft:red_carpet",
                fallback="canvas_red", solid=False)
    decor.block("farmhouse_decorations:single_bed", -2.3, FLOOR_Y, -3.35, facing="back", fallback="blanket")
    decor.block("furnish:spruce_stool", -2.4, FLOOR_Y, -1.2, facing="front", scale=0.9, fallback="crate")
    decor.block("furnish:spruce_square_table", 2.3, FLOOR_Y, -2.55, facing="front", scale=0.9, fallback="plank")
    decor.block("farmhouse_decorations:kerosene_lantern", 2.2, FLOOR_Y + 0.9, -2.5, facing="front", glow=True, fallback="lantern",
                solid=False)
    decor.block("farmersdelight:spruce_cabinet", 2.4, FLOOR_Y, -3.45, facing="front", fallback="crate")
    decor.block("mebahelcreaturesdwarven:dwemer_chest", 0.95, FLOOR_Y, -3.4, facing="front", scale=0.9, fallback="crate")
    decor.block("farmersdelight:rice_bag", 2.55, FLOOR_Y, -1.55, facing="neg_x", scale=0.65, fallback="sack")
    decor.block("furnish:spruce_crate", 2.45, FLOOR_Y, -0.75, facing="neg_x", scale=0.8, fallback="crate")
    decor.block("furnish:dark_oak_crate", -0.9, FLOOR_Y, -3.5, facing="front", scale=0.7, fallback="crate")
    # lanterns hanging from the collar ties and the entrance posts
    for k, z in enumerate((ZB + 1.1, ZM - 0.75)):
        decor.block("farmhouse_decorations:chained_kerosene_lantern", 0.0 if k else -0.6, 2.3, z, facing="front", glow=True,
                    fallback="lantern", solid=False)
    for s in (1, -1):
        decor.block("farmhouse_decorations:chained_kerosene_lantern", s * 1.6, 1.15, ZM + 0.65, facing="front", glow=True,
                    fallback="lantern", solid=False)
    # ---- the pavilion: tableware on the long table, a side table, barrels and crates, hanging lanterns
    decor.block("farmhouse_decorations:kerosene_lantern", 0.0, 0.95, 2.55, facing="front", glow=True, fallback="lantern", solid=False)
    decor.block("furnish:plate", -1.1, 0.95, 2.45, facing="front", scale=0.8, fallback="white", solid=False)
    decor.block("furnish:plate", 1.0, 0.95, 2.7, facing="front", scale=0.8, fallback="white", solid=False)
    decor.block("farmhouse_decorations:red_wine_bottle", -0.6, 0.95, 2.75, facing="front", fallback="glass", solid=False)
    decor.block("farmhouse_decorations:wine_bottle", 1.35, 0.95, 2.35, facing="front", fallback="glass", solid=False)
    decor.block("furnish:spruce_table", -2.55, 0.0, 1.2, facing="front", scale=0.9, fallback="plank")
    decor.block("farmhouse_decorations:kerosene_lantern", -2.55, 0.9, 1.2, facing="front", glow=True, fallback="lantern", solid=False)
    decor.block("landsoficaria:cypress_barrel", 2.55, 0.0, 1.15, facing="front", alt="minecraft:barrel", fallback="barrel")
    decor.block("landsoficaria:loaded_cypress_barrel", 2.6, 0.0, 3.75, facing="neg_x", alt="minecraft:barrel", fallback="barrel")
    decor.block("landsoficaria:cypress_barrel", -2.6, 0.0, 3.8, facing="pos_x", scale=0.9, alt="minecraft:barrel", fallback="barrel")
    decor.block("furnish:spruce_crate", -2.5, 0.0, 2.6, facing="front", scale=0.75, fallback="crate")
    decor.block("farmersdelight:carrot_crate", 2.5, 0.0, 2.45, facing="pos_x", scale=0.8, fallback="crate")
    for x in (-2.6, 2.6):
        decor.block("farmhouse_decorations:chained_kerosene_lantern", x, 2.15, 2.5, facing="front", glow=True, fallback="lantern",
                    solid=False)
    for x in (-1.9, 0.0, 1.9):   # a row of lanterns along the front beam, as on the reference pavilion
        decor.block("farmhouse_decorations:chained_kerosene_lantern", x, 2.0, ZF - 0.2, facing="front", glow=True, fallback="lantern",
                    solid=False)
    return decor


def build():
    root = tl.Bone(NAME)
    frame = tl.Bone("frame", parent=root)
    cloth = tl.Bone("canvas", parent=root)
    detail = tl.Bone("detail", parent=root)
    furn = tl.Bone("furniture", parent=root)
    dwelling(frame, cloth, detail)
    pavilion(frame, cloth, detail, furn)
    decor = furniture_decor()
    decor.fallbacks(root)
    return root, decor


def icon(path):
    tl.icon_aframe(path, cloth=(198, 178, 136), dark=(138, 118, 84), wood=(104, 72, 38))


def main():
    tl.setup(NAME)
    root, decor = build()
    tl.export(root, NAME, decor, icon=icon, visible_box=(9, 6, 0))


if __name__ == "__main__":
    main()
