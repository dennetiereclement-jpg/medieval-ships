#!/usr/bin/env python3
"""tent_chief — the chief's pavilion (reference: scratchpad/ref/tent6_chief_ref.png).

A decagonal pavilion ~9 x 9 x 7: ten slightly leaning wooden pillars under an eave ring, rafters up to a tall pointed
cone roof striped beige / red / dark, a scalloped torn valance all round the eave, hanging wall panels (beige, red,
dark) between the pillars with the front bay open and its curtains gathered against the entrance pillars, a gold
finial and pennant at the apex, guy ropes to pegs, a plank floor, red banners and shields inside, a lantern
chandelier under the apex; the furniture of the decoration mods (round red rug, two tables, the high-backed throne
and two chairs, a golden chest, crates, a sack, a bookshelf, barrels at the entrance, two glowing lanterns), stand-in
boxes when the mods are missing.

Usage:  python3 tools/tents/generate_tent_chief.py      (TENT_OUT=<file>: write only the model there, for previews)
Writes: blockbench/tent_chief.bbmodel, the assets copy, textures/entity/tents.png, textures/item/tent_chief.png,
        interiors/tent_chief_decor.json, tents/tent_chief.json (extent + collision boxes for TentType).
Tent-local coordinates: y up, +z = front (entrance), the anchor block at (0, 0, 0).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tentlib as tl  # noqa: E402
from tentlib import v3, UP, EYE  # noqa: E402

NAME = "tent_chief"
N = 10                                  # bays (pillars / roof wedges)
R_EAVE = 3.75                           # radius of the eave ring (pillar tops)
EAVE_Y = 2.8
APEX = (0.0, 6.9, 0.0)
FLOOR_Y = 0.12
PHASE = math.pi / 2 - math.pi / N       # bay 0 is centred on +z: the entrance

ROOF_N = 2 * N                          # roof wedges: two per bay (the many narrow scallops of the reference)
ROOF_STRIPES = ["canvas", "canvas_b", "canvas_red", "canvas", "canvas_b", "canvas_dark", "canvas", "canvas", "canvas_red", "canvas_b",
                "canvas", "canvas_dark", "canvas_b", "canvas", "canvas_red", "canvas", "canvas_b", "canvas", "canvas_dark", "canvas_b"]
WALL_CLOTH = {1: "canvas_red", 2: "canvas_b", 3: "canvas", 4: "canvas_dark", 5: "canvas_b", 6: "canvas", 7: "canvas_b", 8: "canvas_red", 9: "canvas"}
FRINGE_OF = {"canvas_red": "fringe_red", "canvas_dark": "fringe_dark"}
# a little irregularity per pillar: (tangential lean of the top, radial offset of the foot)
LEAN = [(0.10, 0.25), (-0.08, 0.30), (0.12, 0.20), (0.0, 0.32), (-0.14, 0.22), (0.06, 0.28), (-0.10, 0.26), (0.14, 0.18), (-0.06, 0.30), (0.08, 0.24)]


def ang(k):
    return PHASE + 2 * math.pi * k / N


def radial(a):
    return v3(math.cos(a), 0, math.sin(a))


def tangent(a):
    return v3(-math.sin(a), 0, math.cos(a))


def pillar_top(k):
    a = ang(k)
    return radial(a) * R_EAVE + UP * (EAVE_Y + 0.1) + tangent(a) * LEAN[k][0]


def pillar_foot(k):
    a = ang(k)
    return radial(a) * (R_EAVE + LEAN[k][1]) - UP * 0.05


def build():
    # the cloth strips overlap a little more than the default: the narrow roof wedges would otherwise show sky slits
    # along the rafters when seen from inside
    _loft = tl.loft
    tl.loft = lambda *a, **k: _loft(*a, **dict(k, overlap=max(0.05, k.get("overlap", 0.0))))
    root = tl.Bone(NAME)
    frame = tl.Bone("frame", parent=root)
    cloth = tl.Bone("canvas", parent=root)
    detail = tl.Bone("detail", parent=root)
    furn = tl.Bone("furniture", parent=root)

    # ---- frame: ten leaning pillars, the eave ring, the rafters, the finial pole
    tops = [pillar_top(k) for k in range(N)]
    for k in range(N):
        tl.post(frame, "pillar_%d" % k, pillar_foot(k), tops[k], d=0.22)
        tl.pole(frame, "ring_%d" % k, tops[k] - UP * 0.06, tops[(k + 1) % N] - UP * 0.06, d=0.14, extend=0.05)
        tl.pole(frame, "rafter_%d" % k, v3(*APEX) - UP * 0.1, tops[k] + UP * 0.12, d=0.12, extend=0.1)
        # a rope lashing at each pillar head
        tl.rope(detail, "lash_%d" % k, tops[k] - tangent(ang(k)) * 0.18 - UP * 0.25, tops[k] + tangent(ang(k)) * 0.18 - UP * 0.05, d=0.07)
    tl.pole(frame, "finial_pole", (0, APEX[1] - 0.3, 0), (0, APEX[1] + 1.1, 0), d=0.11, region="wood_dark")
    tl.add_cube(detail, "finial_ball", (0, APEX[1] + 0.5, 0), EYE, (0.34, 0.34, 0.34), "gold")
    tl.add_cube(detail, "finial_tip", (0, APEX[1] + 1.05, 0), EYE, (0.2, 0.2, 0.2), "gold")
    tl.add_cube(detail, "finial_collar", (0, APEX[1] + 0.02, 0), EYE, (0.42, 0.14, 0.42), "gold")
    tl.pennant(detail, "pennant", (0.06, APEX[1] + 0.95, 0), length=0.9, width=0.3, direction=(1, 0, 0.35))

    # ---- roof: the striped cone, sagging between the rafters, torn scalloped edge
    tl.cone_roof(cloth, "roof", APEX, (0, EAVE_Y + 0.22, 0), R_EAVE + 0.45, n=ROOF_N, sag=0.1, ny=5, fringe=0.3, drop=0.2,
                 stripes=ROOF_STRIPES, phase=PHASE)
    # the valance: a short sagging band hanging all round the eave with a ragged fringe (over the wall tops)
    for k in range(N):
        a0, a1 = ang(k), ang(k + 1)
        out = radial((a0 + a1) / 2)
        t0, t1 = tops[k] + radial(a0) * 0.3, tops[(k + 1) % N] + radial(a1) * 0.3
        tl.canvas_panel(cloth, "valance_%d" % k, t0, t1, t0 - UP * 0.5 + out * 0.08, t1 - UP * 0.5 + out * 0.08, sag=0.1, nx=3, ny=1,
                        region="canvas" if k % 2 else "canvas_b", fringe=0.32, ripple=0.03, sag_dir=out)

    # ---- walls: hanging panels between the pillars (bay 0 = entrance left open), bellying outwards
    for k in range(1, N):
        a0, a1 = ang(k), ang(k + 1)
        out = radial((a0 + a1) / 2)
        reg = WALL_CLOTH[k]
        t0, t1 = tops[k] + radial(a0) * 0.14 - UP * 0.35, tops[(k + 1) % N] + radial(a1) * 0.14 - UP * 0.35
        b0 = radial(a0) * (R_EAVE + 0.2) + UP * 0.38
        b1 = radial(a1) * (R_EAVE + 0.2) + UP * 0.38
        tl.canvas_panel(cloth, "wall_%d" % k, t0, t1, b0, b1, sag=0.14, nx=3, ny=4, region=reg, fringe=0.26,
                        fringe_region=FRINGE_OF.get(reg, "fringe"), ripple=0.05, sag_dir=out)
    # the entrance curtains, gathered against the two front pillars (narrow at the bottom, well crumpled)
    for k, s in ((0, 1), (1, -1)):
        a = ang(k)
        along = tangent(a) * s          # towards the middle of the entrance bay
        top0 = tops[k] + radial(a) * 0.1 - UP * 0.35
        top1 = top0 + along * 0.75
        bot0 = radial(a) * (R_EAVE + 0.15) + UP * 0.4 + along * 0.1
        bot1 = bot0 + along * 0.4
        if s < 0:
            top0, top1, bot0, bot1 = top1, top0, bot1, bot0
        tl.canvas_panel(cloth, "curtain_%d" % k, top0, top1, bot0, bot1, sag=0.12, nx=2, ny=4, region="canvas_red", fringe=0.25,
                        fringe_region="fringe_red", ripple=0.12, sag_dir=radial(a))
        tl.rope(detail, "curtain_tie_%d" % k, bot0 + UP * 1.0 - along * 0.15, bot1 + UP * 1.05 + along * 0.12, d=0.06)

    # ---- guy ropes from the side and back pillars, pegs in the ground
    for k in (2, 3, 4, 5, 6, 7, 8, 9):
        a = ang(k)
        tl.guy(detail, "guy_%d" % k, tops[k] + radial(a) * 0.12, radial(a) * (R_EAVE + 1.15) + tangent(a) * (0.25 if k % 2 else -0.2))

    # ---- floor: a plank decagon (a square and two cross strips), flagstones at the entrance
    tl.platform(root, "floor", -2.7, 2.7, -2.7, 2.7, FLOOR_Y, th=0.1, plank_w=0.6, along="z")
    tl.platform(root, "floor_x", -3.55, 3.55, -1.5, 1.5, FLOOR_Y, th=0.1, plank_w=0.6, along="x", joists=False)
    tl.platform(root, "floor_z", -1.5, 1.5, -3.55, 3.55, FLOOR_Y, th=0.1, plank_w=0.6, along="z", joists=False)
    for k, (x, z, w, d) in enumerate(((-0.7, 3.75, 1.0, 0.8), (0.5, 3.9, 1.1, 0.7), (-0.1, 4.6, 1.2, 0.8), (1.3, 4.5, 0.8, 0.6))):
        tl.add_cube(detail, "flag_%d" % k, (x, 0.03, z), EYE, (w, 0.06, d), "stone")

    # ---- decorations of the model: red banners with a gold bar inside the back bays, round shields on the side
    # pillars, a lantern chandelier under the apex, two lanterns outside the entrance pillars
    for k in (4, 7):
        a = (ang(k) + ang(k + 1)) / 2
        inward = -radial(a)
        c = radial(a) * (R_EAVE - 0.35) + UP * (EAVE_Y - 0.55)
        tl.pole(detail, "banner_bar_%d" % k, c - tangent(a) * 0.5, c + tangent(a) * 0.5, d=0.07, region="gold")
        tl.canvas_panel(detail, "banner_%d" % k, c - tangent(a) * 0.4 + inward * 0.05, c + tangent(a) * 0.4 + inward * 0.05,
                        c - tangent(a) * 0.3 - UP * 1.7 + inward * 0.1, c + tangent(a) * 0.3 - UP * 1.7 + inward * 0.1, sag=0.04, nx=1, ny=3,
                        region="canvas_red", fringe=0.0, ripple=0.02, sag_dir=inward)
        tl.add_cube(detail, "banner_emblem_%d" % k, c - UP * 0.8 + inward * 0.12, EYE, (0.36, 0.36, 0.36), "gold")
    for k in (2, 9):
        a = ang(k)
        inward = -radial(a)
        p = radial(a) * (R_EAVE - 0.02) + UP * 1.75 + inward * 0.2
        R = tl.gg.ry(-a)
        tl.add_cube(detail, "shield_%d" % k, p, R, (0.1, 0.8, 0.8), {"all": "red_paint", "+2": "wood_dark", "-2": "wood_dark"})
        tl.add_cube(detail, "shield_boss_%d" % k, p + inward * 0.07, R, (0.08, 0.26, 0.26), "iron")
    tl.rope(detail, "chandelier_chain", (0, APEX[1] - 0.5, 0), (0, 4.0, 0), d=0.05, region="iron")
    tl.pole(detail, "chandelier_bar_a", (-0.6, 3.95, 0), (0.6, 3.95, 0), d=0.07, region="iron")
    tl.pole(detail, "chandelier_bar_b", (0, 3.95, -0.6), (0, 3.95, 0.6), d=0.07, region="iron")
    for i, (x, z) in enumerate(((0.6, 0), (-0.6, 0), (0, 0.6), (0, -0.6))):
        tl.lantern(detail, "chandelier_lamp_%d" % i, (x, 3.6, z), size=0.26, chain_to=(x, 3.95, z))
    for k, s in ((0, -1), (1, 1)):
        a = ang(k)
        p = tops[k] + radial(a) * 0.55 - UP * 0.85
        tl.pole(detail, "lamp_arm_%d" % k, tops[k] - UP * 0.4, tops[k] + radial(a) * 0.6 - UP * 0.4, d=0.07, region="wood_dark")
        tl.lantern(detail, "lamp_%d" % k, p, size=0.3, chain_to=tops[k] + radial(a) * 0.55 - UP * 0.4)

    # ---- furniture of the decoration mods (drawn in place; vanilla alt or stand-in when a mod is missing)
    decor = tl.Decor()
    decor.block("farmhouse_decorations:rug_3x_3", 0.0, FLOOR_Y, 0.3, facing="front", scale=1.35, alt="minecraft:red_carpet",
                fallback="blanket", solid=False)
    decor.block("furnish:dark_oak_table", -0.5, FLOOR_Y, -1.75, facing="front", fallback="plank")
    decor.block("furnish:dark_oak_table", 0.5, FLOOR_Y, -1.75, facing="front", fallback="plank")
    decor.block("furnish:dark_oak_chair", 0.0, FLOOR_Y, -2.75, facing="front", fallback="leather")
    decor.block("furnish:spruce_chair", -1.65, FLOOR_Y, -1.75, facing="pos_x", fallback="leather")
    decor.block("furnish:spruce_chair", 1.65, FLOOR_Y, -1.75, facing="neg_x", fallback="leather")
    decor.block("mebahelcreaturesdwarven:dwemer_chest", 2.35, FLOOR_Y, -2.45, facing="front", fallback="crate")
    decor.block("furnish:spruce_crate", -2.45, FLOOR_Y, -2.3, facing="front", scale=0.9, fallback="crate")
    decor.block("furnish:oak_crate", -2.45, FLOOR_Y + 0.9, -2.3, facing="neg_x", scale=0.75, fallback="crate")
    decor.block("farmersdelight:rice_bag", -1.55, FLOOR_Y, -2.75, facing="front", scale=0.75, fallback="sack")
    decor.block("farmhouse_decorations:tall_bookshelf", -2.95, FLOOR_Y, 0.4, facing="pos_x", alt="minecraft:bookshelf", fallback="books")
    decor.block("furnish:dark_oak_stool", 2.7, FLOOR_Y, 0.9, facing="front", fallback="plank")
    decor.block("landsoficaria:cypress_barrel", 3.25, 0.0, 3.4, facing="front", alt="minecraft:barrel", fallback="barrel")
    decor.block("landsoficaria:cypress_barrel", -3.3, 0.0, 3.25, facing="neg_x", alt="minecraft:barrel", fallback="barrel")
    decor.block("farmersdelight:carrot_crate", -3.0, 0.0, 4.2, facing="front", scale=0.85, fallback="crate")
    # two glowing lanterns hanging from the eave ring just inside the entrance pillars
    for k, s in ((0, -1), (1, 1)):
        p = tops[k] - radial(ang(k)) * 0.45 + tangent(ang(k)) * s * 0.3
        decor.block("farmhouse_decorations:chained_kerosene_lantern", float(p[0]), EAVE_Y - 0.95, float(p[2]), facing="front", glow=True,
                    fallback="lantern", solid=False)
    decor.fallbacks(root)
    tl.loft = _loft
    return root, decor


def icon(path):
    tl.icon_aframe(path, red=(143, 43, 34), cone=True)


def main():
    tl.setup(NAME)
    root, decor = build()
    tl.export(root, NAME, decor, icon=icon, visible_box=(10, 8, 0))


if __name__ == "__main__":
    main()
