#!/usr/bin/env python3
"""tente_forgeron — Tente du forgeron / Blacksmith Merchant Tent (reference: scratchpad/ref/tente_forgeron_ref.png).

The shared merchant pavilion (merchantlib.pavilion) in navy blue and beige with the anvil banner, dressed as a
smith's stall: a stone forge with a glowing hearth at the back left, a big grey anvil on a stone block at the front,
a sword rack along the left wall, helmets, shields, tools and ingots on the back shelves and the counters, barrels
and iron-banded crates by the front posts, a tool board (Farmhouse Decorations) on the right wall.

Usage:  python3 tools/merchant/generate_tente_forgeron.py      (MERCHANT_OUT=<file.bbmodel>: only the model)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import merchantlib as ml  # noqa: E402
import props_m2 as pm  # noqa: E402

NAME = "tente_forgeron"
v3, UP = pm.v3, pm.UP


def main():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="blue")
    pm.add_regions(atlas, "forge")
    root = ml.Bone(NAME)
    L = ml.pavilion(root, atlas, emblem="anvil", flag_corner="back_left", side_banners=0, rug=True, lanterns=2,
                    front_counter="right", back_shelves=False)
    det = L.detail
    smithy = ml.Bone("smithy", parent=root)
    decor = ml.Decor()
    hw, hd = L.half_w, L.half_d

    # ---- the forge at the back left, its fire glowing towards the front
    pm.forge(smithy, det, -1.85, -hd + 0.15, w=1.8, d=1.05)

    # ---- the shelves at the back right: helmets, shields, ingots, tools
    levels = ml.shelf_unit(smithy, "shelves", -0.7, hw - 0.5, -hd + 0.25, -hd + 0.72, levels=(0.55, 1.15, 1.75, 2.35), h=2.65,
                           uprights=4, detail=det)
    (ax0, ax1, y0, zf, zb), (bx0, bx1, y1, _, _), (cx0, cx1, y2, _, _), (dx0, dx1, y3, _, _) = levels
    zm = (zf + zb) / 2
    for k, x in enumerate((ax0 + 0.3, ax0 + 1.0, ax1 - 0.9, ax1 - 0.25)):
        ml.crate(det, "shelf_crate_%d" % k, (x, y0, zm), size=(0.4, 0.3, 0.36), solid=False, content="m2_ingot" if k % 2 else None)
    for k in range(5):
        x = bx0 + 0.25 + k * (bx1 - bx0 - 0.5) / 4
        pm.helmet(det, "helm_b_%d" % k, (x, y1, zm), s=1.25, crest="gold" if k == 2 else None)
    for k in range(4):
        x = cx0 + 0.35 + k * (cx1 - cx0 - 0.7) / 3
        if k % 2 == 0:
            pm.shield(det, "shield_c_%d" % k, (x, y2 + 0.3, zb + 0.08), normal=(0, 0.35, 1), w=0.42, h=0.52, face="steel")
        else:
            pm.ingot_stack(det, "ingots_c_%d" % k, (x, y2, zm), layers=3, s=1.2, region="m2_ingot_gold" if k == 3 else "m2_ingot")
    for k in range(4):
        x = dx0 + 0.3 + k * (dx1 - dx0 - 0.6) / 3
        pm.helmet(det, "helm_d_%d" % k, (x, y3, zm), s=1.1, yaw=0.2 * (k - 1.5))
    # hammers and tongs on hooks under the top shelf
    for k in range(4):
        x = cx0 + 0.25 + k * 0.38
        ml.beam(det, "tool_hook_%d" % k, v3(x, y3 - 0.1, zb + 0.05), v3(x, y3 - 0.1, zb + 0.15), 0.03, "iron")

    # ---- the sword rack along the left wall and a second one on the right of the forge
    ml.weapon_rack(smithy, "rack_left", (-hw + 0.3, 0, -1.45), (-hw + 0.3, 0, 0.3), h=1.8, normal=(1, 0, 0),
                   items=("sword", "axe", "sword", "spear", "sword"), detail=det)
    ml.weapon_rack(smithy, "rack_back", (-0.85, 0, -hd + 1.05), (0.15, 0, -hd + 1.05), h=1.6, normal=(0, 0, 1),
                   items=("sword", "spear", "sword"), detail=det)

    # ---- the big anvil on its stone block at the front, a quench tub beside it
    pm.anvil_block(smithy, det, (-0.95, 0, hd - 0.2), yaw=0.0, s=1.8, block=(1.15, 0.66, 0.85), sz=1.35)

    # ---- the right counter (shell): big ingots, a helmet, tongs; the return: hammers, a shield, a chest of ingots
    (fx0, fy, fz0, fx1, _, fz1) = L.counter_boxes[0]
    (sx0, sy, sz0, sx1, _, sz1) = L.counter_boxes[1]
    for k, x in enumerate((fx0 + 0.3, fx0 + 0.75, fx0 + 1.2, fx1 - 0.35)):
        pm.ingot_stack(det, "ingots_f_%d" % k, (x, fy, (fz0 + fz1) / 2 + (0.08 if k % 2 else -0.06)), layers=3 - (k % 2), s=2.2,
                       yaw=0.15 * k, region="m2_ingot_gold" if k == 2 else "m2_ingot")
    pm.helmet(det, "helm_counter", (fx1 - 0.35, fy + 0.0, fz0 + 0.18), s=1.2, yaw=-0.4)
    for k, z in enumerate((sz0 + 0.3, sz0 + 0.7)):
        ml.beam(det, "counter_hammer_h_%d" % k, v3((sx0 + sx1) / 2 - 0.05, sy + 0.025, z), v3((sx0 + sx1) / 2 + 0.25, sy + 0.025, z + 0.1), 0.04,
                "wood")
        ml.beam(det, "counter_hammer_%d" % k, v3((sx0 + sx1) / 2 - 0.08, sy + 0.04, z - 0.09), v3((sx0 + sx1) / 2 - 0.08, sy + 0.04, z + 0.1),
                0.08, "black_iron")
    pm.shield(det, "shield_counter", ((sx0 + sx1) / 2, sy + 0.32, sz1 - 0.35), normal=(-1, 0.3, 0), w=0.44, h=0.56, face="steel")
    ml.crate(smithy, "counter_crate", ((sx0 + sx1) / 2, sy, sz0 + 1.3), size=(0.5, 0.32, 0.44), solid=False, content="m2_ingot")

    # ---- the left front bench (behind the barrels): crates of ore and horseshoes, tongs
    top = ml.counter(smithy, "bench_left", -hw + 0.35, -1.25, hd - 1.35, hd - 0.65, h=0.85, detail=det)
    ml.crate(det, "bench_crate_0", (-hw + 0.75, top[1], hd - 1.0), size=(0.5, 0.36, 0.45), solid=False, content="coal")
    ml.crate(det, "bench_crate_1", (-hw + 1.3, top[1], hd - 1.0), size=(0.45, 0.3, 0.4), yaw=0.2, solid=False)
    pm.ingot_stack(det, "bench_ingots", (-1.6, top[1], hd - 0.95), layers=2, s=1.4)

    # ---- barrels and crates by the front posts (mod furniture, vanilla fallback), a modelled barrel of swords
    flx, _, flz = L.front_left
    frx, _, frz = L.front_right
    ml.barrel(smithy, "barrel_0", (flx + 0.8, 0.0, flz - 0.05), r=0.42, h=1.0)
    ml.barrel(smithy, "barrel_1", (flx - 0.35, 0.0, flz - 0.6), r=0.36, h=0.9)
    ml.crate(det, "barrel_0_crate", (flx + 0.8, 1.0, flz - 0.05), size=(0.42, 0.22, 0.36), yaw=0.3, solid=False, content="m2_ingot")
    decor.block("landsoficaria:cypress_barrel", -hw + 0.5, 0.0, 0.88, facing="pos_x", scale=0.85, alt="minecraft:barrel",
                fallback="barrel")
    decor.block("furnish:spruce_crate", flx - 0.35, 0.0, flz + 0.45, facing="front", scale=0.7, fallback="crate")
    decor.block("furnish:spruce_crate", frx + 0.2, 0.0, frz - 0.1, facing="front", scale=0.75, fallback="crate")
    decor.block("furnish:spruce_crate", frx + 0.2, 0.75, frz - 0.1, facing="front", scale=0.55, fallback="crate")
    bx, bz = frx - 0.85, frz - 0.2
    ml.barrel(smithy, "sword_barrel", (bx, 0, bz), r=0.3, h=0.8)
    for k, (dx, dz, lean) in enumerate(((-0.1, -0.05, -0.12), (0.08, 0.06, 0.1), (0.0, 0.1, 0.02))):
        up = pm.norm(v3(lean, 1, lean * 0.5))
        ml.sword(det, "barrel_sword_%d" % k, v3(bx + dx, 0.62, bz + dz) + up * 0.5, up=up, length=0.9)
    # the tool board on the right wall (Farmhouse Decorations; a stand-in board without the mod)
    decor.block("farmhouse_decorations:tool_board", hw - 0.3, 1.25, -1.45, facing="neg_x", fallback="plank_dark", solid=False)

    particles = [ml.particle("flame", (-1.85, 0.75, -hd + 0.75), 0.25), ml.particle("smoke", (-1.85, 3.2, -hd + 0.45), 0.2)]
    ml.export(root, NAME, atlas, decor=decor, icon=dict(colour="blue", emblem="anvil"), particles=particles)


if __name__ == "__main__":
    main()
