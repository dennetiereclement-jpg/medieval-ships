#!/usr/bin/env python3
"""Divine steampunk forge, STRUCTURE model (1.34.0): platform and steps, stone body, black reinforcements, gold and
bronze ornaments, the furnace (deep opening, sculpted pointed arch, gold cross, 4-frame fire + craft flames), the big
black anvil, the two heat columns (4-frame light flow each + craft core), two gold gears, every copper pipe, the high
stone/gold gallows (banners and lanterns of the decor model hang there), the work benches and the press socle.

    python3 tools/forge/generate_forge_divine.py [--sheet N]

Writes models/entity/forge_divine.bbmodel (+ blockbench copy), textures/entity/forge_divine.png, the 16x16 item
icon textures/item/forge_divine.png and workshops/forge_divine.json, then runs tools/forge/forge_audit.py (must
print DEFECTS = 0) and draws the comparison sheet next to the reference picture. Calage points: tools/forge/CALAGE.md.
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import forgelib_structure as fl  # noqa: E402
import forge_audit as FA  # noqa: E402

rgb, mix, shade = fl.rgb, fl.mix, fl.shade
NAME = "forge_divine"


def X(s, a, b):
    return (min(s * a, s * b), max(s * a, s * b))


def build():
    f = fl.Forge(NAME, size=512)
    M = f.material
    M("stone", fl.p_bricks(fl.STONE, fl.STONE_L, fl.MORTAR, 16, 8), 128, 128)
    M("stone_dark", fl.p_bricks(fl.DSTONE, fl.DSTONE_L, fl.DMORTAR, 8, 4), 128, 128)
    M("floor", fl.p_floor(fl.STONE, fl.STONE_L, fl.MORTAR), 128, 128)
    M("carved", fl.p_carved(fl.CARVED, fl.CARVED_L, fl.CARVED_D), 64, 64)
    M("iron", fl.p_metal(fl.IRON, fl.IRON_L, fl.IRON_D), 64, 32)
    M("gold", fl.p_gold(fl.GOLD, fl.GOLD_L, fl.GOLD_D), 64, 32)
    M("gold_dark", fl.p_gold(fl.BRONZE, fl.BRONZE_L, fl.BRONZE_D), 64, 32)
    M("bronze", fl.p_metal(fl.BRONZE, fl.BRONZE_L, fl.BRONZE_D, rivet=0, plate=8), 32, 32)
    M("copper_u", fl.p_band(fl.COPPER, fl.COPPER_L, fl.COPPER_D, along_u=True), 64, 8)
    M("copper_v", fl.p_band(fl.COPPER, fl.COPPER_L, fl.COPPER_D, along_u=False), 8, 64)
    M("copper_end", fl.p_ring(fl.COPPER, fl.COPPER_L, fl.COPPER_D), 16, 16)
    M("copper_joint", fl.p_metal(fl.COPPER, fl.COPPER_L, fl.COPPER_D, rivet=4, plate=8), 32, 32)
    M("wood", fl.p_planks(fl.WOOD, fl.WOOD_L, fl.WOOD_D, True), 64, 32)
    M("woodg", fl.p_planks(fl.WOODG, fl.WOODG_L, fl.WOODG_D, True), 64, 32)
    M("drawers", fl.p_drawers(2), 32, 8)
    M("drawers_v", fl.p_drawers(2, cols=False), 16, 12)
    M("black", fl.p_bricks(fl.BLACK, fl.BLACK_L, fl.BLACK_D, 16, 8), 64, 64)
    M("anvil", fl.p_metal(rgb("3b3537"), rgb("6c6264"), rgb("1a1617"), rivet=0), 64, 32)
    M("hot", fl.p_glow_bricks(), 64, 64)
    M("coal", fl.p_coal(), 64, 32)
    M("fire_core", fl.p_fire(fl.FIRE_W, fl.FIRE_Y), 16, 16)
    M("fire_mid", fl.p_fire(fl.FIRE_Y, fl.FIRE_O), 16, 16)
    M("fire_out", fl.p_fire(fl.FIRE_O, fl.FIRE_R), 16, 16)
    M("fire_hot", fl.p_fire(rgb("ffffff"), fl.FIRE_W), 16, 16)
    M("glass", fl.p_glass(), 8, 32)
    M("glass_side", fl.p_fire(fl.FIRE_Y, fl.FIRE_O), 16, 32)
    M("flow", fl.p_fire(fl.FIRE_W, fl.FIRE_Y), 8, 8)
    M("flow_hot", fl.p_fire(rgb("ffffff"), rgb("fff8dc")), 8, 8)
    M("lava", fl.p_lava(), 64, 16)
    M("gem", fl.p_gem(), 8, 8)
    GEM = {k: ("pic", "gem") for k in fl.SEM}

    def bx(bone, name, x, y, z, mat, faces=None, glow=False):
        return f.box(bone, name, (x[0], y[0], z[0]), (x[1], y[1], z[1]), mat, faces, glow)

    plat = f.bone("platform")
    body = f.bone("body")
    furn = f.bone("furnace")
    cols = f.bone("columns")
    pipes = f.bone("pipes")
    pot = f.bone("potences")
    bench = f.bone("benches")
    anv = f.bone("anvil")

    # ------------------------------------------------------------ platform (two steps of 0.25, deck at y = 0.5)
    for k, xr in enumerate(((-6.5, 0.0), (0.0, 6.5))):
        bx(plat, "step_low_%d" % k, xr, (0, 0.25), (-3.0, 3.0), "stone", {"+y": "floor"})
    for k, xr in enumerate(((-6.2, -2.07), (-2.07, 2.07), (2.07, 6.2))):
        bx(plat, "deck_%d" % k, xr, (0.25, 0.5), (-2.75, 2.7), "stone", {"+y": "floor"})
    # front plinths: gold plaques (dark inset) and carved stones standing on the low step
    for s in (-1, 1):
        bx(plat, "plinth_stone", X(s, 2.2, 3.05), (0.125, 0.485), (2.6, 2.95), "carved")
        bx(plat, "plaque", X(s, 3.95, 4.7), (0.125, 0.47), (2.6, 2.93), "gold")
        bx(plat, "plaque_inset", X(s, 4.12, 4.53), (0.2, 0.39), (2.9, 2.96), "iron")
        bx(plat, "corner_gold", X(s, 5.92, 6.26), (0.125, 0.475), (2.56, 2.77), "gold")
        bx(plat, "side_plaque", X(s, 6.15, 6.28), (0.27, 0.46), (-0.4, 0.4), "gold")
    bx(plat, "plaque_c", (-0.42, 0.42), (0.125, 0.47), (2.6, 2.93), "gold")
    bx(plat, "plaque_c_inset", (-0.24, 0.24), (0.2, 0.39), (2.9, 2.96), "iron")
    # lava grid in front of the anvil, in a dark iron frame, gold inlays on its sides
    bx(plat, "lava_frame_b", (-2.0, 2.0), (0.45, 0.56), (1.92, 2.04), "iron")
    bx(plat, "lava_frame_f", (-2.0, 2.0), (0.45, 0.56), (2.5, 2.62), "iron")
    for s in (-1, 1):
        bx(plat, "lava_frame_s", X(s, 1.88, 2.0), (0.45, 0.56), (2.04, 2.5), "iron")
        bx(plat, "floor_gold", X(s, 2.08, 2.2), (0.47, 0.52), (1.9, 2.64), "gold")
    lava = {k: "coal" for k in fl.SEM}
    lava["+y"] = ("pic", "lava")
    bx(plat, "glow_lava", (-1.9, 1.9), (0.45, 0.535), (2.02, 2.52), "coal", lava, glow=True)

    # ------------------------------------------------------------ body (grey stone, dark brick facade)
    for s in (-1, 1):
        bx(body, "body_side", X(s, 1.85, 4.05), (0.5, 6.0), (-2.2, 0.25), "stone", {"+z": "stone_dark"})
        bx(body, "buttress", X(s, 4.0, 4.55), (0.5, 2.85), (-2.0, -0.4), "stone")
        bx(body, "buttress_cap", X(s, 3.95, 4.62), (2.85, 3.0), (-2.05, -0.35), "carved")
        # black reinforcements: back and sides
        bx(body, "strap_back_v", X(s, 1.85, 2.0), (0.5, 6.0), (-2.26, -2.14), "iron")
        bx(body, "strap_back_c", X(s, 3.88, 4.06), (0.5, 6.0), (-2.26, -2.14), "iron")
        bx(body, "strap_side_v", X(s, 4.03, 4.11), (3.0, 6.0), (-1.05, -0.85), "iron")
        bx(body, "strap_front", X(s, 0.62, 0.74), (4.85, 6.0), (0.22, 0.32), "iron")
    bx(body, "strap_back_h", (-4.0, 4.0), (3.0, 3.14), (-2.28, -2.16), "iron")
    bx(body, "body_back_c", (-1.95, 1.95), (0.5, 4.4), (-2.2, -1.55), "stone", {"+z": "stone_dark"})
    bx(body, "body_top_c", (-1.95, 1.95), (4.3, 6.0), (-2.2, 0.25), "stone", {"+z": "stone_dark"})
    for k, xr in enumerate(((-4.2, 0.0), (0.0, 4.2))):
        bx(body, "beam_%d" % k, xr, (6.0, 6.5), (-2.3, 0.7), "stone")
    for s in (-1, 1):
        bx(body, "beam_cap", X(s, 2.6, 3.8), (6.45, 6.56), (-0.3, 0.75), "gold")
    # centre pilaster under the beam, gold cross with a gem on the beam
    bx(body, "pilaster", (-0.42, 0.42), (4.85, 6.0), (0.2, 0.62), "carved")
    bx(body, "pilaster_gold", (-0.1, 0.1), (4.9, 5.95), (0.6, 0.66), "gold")
    bx(body, "beam_cross_v", (-0.12, 0.12), (5.72, 6.46), (0.7, 0.8), "gold")
    bx(body, "beam_cross_h", (-0.32, 0.32), (6.02, 6.2), (0.7, 0.77), "gold")
    bx(body, "glow_beam_gem", (-0.07, 0.07), (6.04, 6.18), (0.78, 0.86), "gem", GEM, glow=True)

    # ------------------------------------------------------------ furnace
    for s in (-1, 1):
        bx(furn, "pillar", X(s, 1.1, 1.95), (0.5, 3.55), (-1.6, 1.0), "stone_dark")
        bx(furn, "glow_lining", X(s, 1.06, 1.16), (0.9, 3.6), (-1.4, 0.92), "hot", glow=True)
        bx(furn, "frame_side", X(s, 1.02, 1.18), (0.92, 3.62), (0.95, 1.08), "iron")
        bx(furn, "plaque", X(s, 1.22, 1.88), (2.92, 3.48), (0.98, 1.1), "gold")
        bx(furn, "glow_plaque_gem", X(s, 1.45, 1.65), (3.1, 3.3), (1.08, 1.16), "gem", GEM, glow=True)
        bx(furn, "strip", X(s, 1.4, 1.7), (1.75, 2.85), (0.98, 1.06), "gold")
        bx(furn, "slot", X(s, 1.5, 1.6), (2.0, 2.6), (1.04, 1.1), "iron")
        bx(furn, "base", X(s, 1.0, 2.05), (0.5, 1.62), (0.88, 1.2), "carved")
        bx(furn, "base_cap", X(s, 0.97, 2.08), (1.55, 1.7), (0.85, 1.23), "carved")
        # pointed arch of sculpted stone
        bx(furn, "arch_shoulder", X(s, 1.55, 2.08), (3.48, 3.98), (0.82, 1.13), "carved")
        a1 = 44.0 if s < 0 else 136.0
        f.rbox(furn, "arch_seg1", (s * 1.49, 4.15, 0.98), a1, (0.95, 0.42, 0.31), "carved")
        a2 = 20.9 if s < 0 else 159.1
        f.rbox(furn, "arch_seg2", (s * 0.72, 4.6, 0.98), a2, (1.2, 0.4, 0.28), "carved")
    bx(furn, "lintel", (-1.95, 1.95), (3.55, 4.35), (-1.6, 1.0), "stone_dark")
    bx(furn, "backing", (-1.95, 1.95), (4.3, 4.9), (0.2, 0.95), "stone_dark")
    bx(furn, "glow_coal", (-1.15, 1.15), (0.5, 0.95), (-1.45, 1.03), "coal", glow=True)
    bx(furn, "glow_back", (-1.15, 1.15), (0.9, 3.6), (-1.6, -1.35), "hot", glow=True)
    bx(furn, "glow_ceiling", (-1.06, 1.06), (3.45, 3.58), (-1.4, 0.92), "hot", glow=True)
    bx(furn, "frame_top", (-1.02, 1.02), (3.48, 3.62), (0.95, 1.08), "iron")
    bx(furn, "keystone", (-0.3, 0.3), (4.55, 4.98), (0.86, 1.16), "carved")
    bx(furn, "key_strip", (-0.09, 0.09), (3.62, 4.33), (1.0, 1.06), "gold")
    # the gold cross above the arch
    bx(furn, "cross_pier", (-0.3, 0.3), (4.85, 5.62), (0.2, 1.02), "carved")
    bx(furn, "cross_v", (-0.16, 0.16), (4.35, 5.55), (1.0, 1.2), "gold")
    bx(furn, "cross_h", (-0.46, 0.46), (4.85, 5.13), (0.97, 1.16), "gold")
    bx(furn, "cross_inset", (-0.08, 0.08), (4.9, 5.08), (1.18, 1.24), "iron")

    # ------------------------------------------------------------ fire: 4 frames of glow cubes with depth
    layers = [(-1.25, [-0.78, -0.39, 0.0, 0.39, 0.78], (1.5, 2.35), 0.36),
              (-0.75, [-0.6, -0.2, 0.2, 0.6], (1.1, 1.85), 0.34),
              (-0.22, [-0.72, -0.25, 0.25, 0.72], (0.6, 1.2), 0.3)]

    def q(v):
        return round(v * 16) / 16.0

    for k in range(4):
        fb = f.bone("fire_f%d" % k)
        rng = random.Random(1000 + 37 * k)
        for li, (z0, xs, (h0, h1), w) in enumerate(layers):
            for ti, x in enumerate(xs):
                x = x + rng.uniform(-0.05, 0.05)
                h = q(rng.uniform(h0, h1) * (1.0 - 0.22 * abs(x)))
                zz = z0 + (ti % 3) * 0.04
                for si, (a, b, ww, mat) in enumerate(((0.0, 0.45, w, "fire_core"), (0.45, 0.75, w * 0.68, "fire_mid"),
                                                      (0.75, 1.0, w * 0.38, "fire_out"))):
                    lean = (rng.uniform(-0.04, 0.04) if si else 0.0)
                    f.box(fb, "glow_fire_%d_%d_%d" % (li, ti, si), (x + lean - ww / 2, 0.88 + q(a * h), zz),
                          (x + lean + ww / 2, 0.88 + q(b * h), zz + 0.24), mat)
    cf = f.bone("craft_fire")
    f.box(cf, "glow_embers", (-1.0, 0.93, -1.3), (1.0, 1.0, 0.88), "fire_core")
    for ti, (x, h) in enumerate(((-0.5, 1.5), (0.02, 2.0), (0.52, 1.45))):
        for si, (a, b, ww, mat) in enumerate(((0.0, 0.5, 0.3, "fire_hot"), (0.5, 0.8, 0.2, "fire_core"),
                                              (0.8, 1.0, 0.11, "fire_mid"))):
            f.box(cf, "glow_hot_%d_%d" % (ti, si), (x - ww / 2, 0.9 + q(a * h), 0.18 + ti * 0.04),
                  (x + ww / 2, 0.9 + q(b * h), 0.4 + ti * 0.04), mat)

    # ------------------------------------------------------------ anvil
    bx(anv, "plinth", (-0.62, 0.62), (0.5, 0.62), (1.15, 1.85), "gold")
    bx(anv, "foot", (-0.45, 0.45), (0.6, 0.85), (1.22, 1.78), "anvil")
    bx(anv, "waist", (-0.22, 0.22), (0.83, 1.27), (1.34, 1.66), "anvil")
    bx(anv, "top", (-0.58, 0.58), (1.25, 1.6), (1.27, 1.73), "anvil")
    for s in (-1, 1):
        bx(anv, "flare", X(s, 0.56, 0.8), (1.34, 1.58), (1.33, 1.67), "anvil")
        bx(anv, "tip", X(s, 0.78, 0.92), (1.4, 1.56), (1.39, 1.61), "anvil")

    # ------------------------------------------------------------ heat columns + mid band
    for s, tag in ((-1, "l"), (1, "r")):
        bx(cols, "core", X(s, 2.75, 3.65), (3.55, 5.5), (-0.2, 0.5), "stone_dark")
        glass = {k: "glass_side" for k in fl.SEM}
        glass["+z"] = ("pic", "glass")
        bx(cols, "glow_glass_" + tag, X(s, 2.98, 3.42), (3.64, 5.5), (0.3, 0.62), "glass_side", glass, glow=True)
        bx(cols, "bar_gold_in", X(s, 2.84, 3.01), (3.6, 5.53), (0.35, 0.74), "gold")
        bx(cols, "bar_gold_out", X(s, 3.39, 3.56), (3.6, 5.53), (0.35, 0.74), "gold")
        bx(cols, "bar_iron_in", X(s, 2.7, 2.86), (3.56, 5.56), (0.3, 0.7), "iron")
        bx(cols, "bar_iron_out", X(s, 3.54, 3.7), (3.56, 5.56), (0.3, 0.7), "iron")
        bx(cols, "top", X(s, 2.66, 3.74), (5.45, 6.02), (-0.28, 0.78), "carved")
        bx(cols, "top_frame", X(s, 2.98, 3.42), (5.52, 5.95), (0.76, 0.83), "gold")
        bx(cols, "glow_top_gem", X(s, 3.09, 3.31), (5.62, 5.84), (0.81, 0.88), "gem", GEM, glow=True)
        bx(cols, "cap", X(s, 2.64, 3.76), (3.52, 3.7), (-0.3, 0.8), "gold")
        bx(cols, "band", X(s, 1.85, 4.08), (2.85, 3.55), (0.1, 0.7), "stone")
        bx(cols, "band_frame", X(s, 2.98, 3.42), (2.95, 3.45), (0.68, 0.76), "gold")
        bx(cols, "glow_band_gem", X(s, 3.09, 3.31), (3.09, 3.31), (0.74, 0.82), "gem", GEM, glow=True)
        bx(cols, "band_latch", X(s, 2.0, 2.18), (2.95, 3.4), (0.68, 0.75), "iron")
        for k in range(4):
            fbn = f.bone("flow_%s_f%d" % (tag, k))
            for j in range(4):
                y0 = 3.72 + 0.4 * j + 0.1 * k
                w = 0.14 if (j + k) % 2 else 0.12
                f.box(fbn, "glow_flow_%d" % j, (s * 3.2 - w, y0, 0.5), (s * 3.2 + w, y0 + 0.2, 0.665), "flow")
        cb = f.bone("craft_flow_" + tag)
        f.box(cb, "glow_core", (s * 3.2 - 0.07, 3.7, 0.5), (s * 3.2 + 0.07, 5.44, 0.70), "flow_hot")

    # ------------------------------------------------------------ gears (pivot at their centre)
    zc = 0.25 + 0.03 + 11.0 / 64
    ga = f.bone("gear_a_0", origin=(-2.0, 5.12, zc))
    f.gear(ga, (-2.0, 5.12, zc))
    gb = f.bone("gear_b_1", origin=(2.0, 5.12, zc))
    f.gear(gb, (2.0, 5.12, zc), phase=0.0)

    # ------------------------------------------------------------ copper pipes
    for s, tag in ((-1, "l"), (1, "r")):
        f.pipe(pipes, "arch_" + tag, [(s * 1.5, 6.45, -1.6), (s * 1.5, 7.2, -1.6), (s * 2.4, 7.2, -1.6),
                                      (s * 2.4, 6.45, -1.6)], cap_start=False, cap_end=False, every=0.36)
        f.pipe(pipes, "vent_" + tag, [(s * 1.95, 7.3, -1.6), (s * 1.95, 7.62, -1.6)], s=0.14, flange=0.04,
               cap_start=False)
        f.pipe(pipes, "front_" + tag, [(s * 1.05, 4.86, 0.46), (s * 1.05, 6.05, 0.46)], cap_start=False,
               cap_end=False, every=0.45)
        f.pipe(pipes, "coltop_" + tag, [(s * 3.7, 5.75, 0.25), (s * 4.42, 5.75, 0.25), (s * 4.42, 5.42, 0.25)],
               s=0.2, flange=0.06, cap_start=False)
    f.pipe(pipes, "side_l", [(-3.6, 3.95, 0.0), (-5.3, 3.95, 0.0), (-5.3, 3.2, 0.0)], cap_start=False, every=0.6)
    f.pipe(pipes, "side_r", [(3.6, 3.95, 0.0), (5.0, 3.95, 0.0), (5.0, 0.45, 0.0)], cap_start=False, cap_end=False,
           every=0.6)
    f.pipe(pipes, "stub_r", [(5.0, 2.8, 0.0), (5.0, 2.8, -0.52)], s=0.14, flange=0.04, cap_start=False)
    bx(pipes, "hook_l", (-5.72, -5.4), (3.36, 3.46), (-0.05, 0.05), "iron")
    bx(pipes, "hook_r", (5.1, 5.72), (3.36, 3.46), (-0.05, 0.05), "iron")
    bx(pipes, "valve", (4.8, 5.2), (1.95, 2.25), (-0.18, 0.2), "bronze")
    bx(pipes, "valve_wheel", (4.82, 5.18), (1.92, 2.28), (0.24, 0.3), "iron")
    bx(pipes, "valve_stem", (4.96, 5.04), (2.06, 2.14), (0.18, 0.26), "iron")

    # ------------------------------------------------------------ high gallows (banners at x = +-5.6, lanterns +-3.6)
    for s in (-1, 1):
        bx(pot, "tower", X(s, 3.5, 4.25), (6.48, 8.45), (-1.35, -0.45), "stone_dark")
        bx(pot, "tower_gold", X(s, 3.46, 4.29), (7.2, 7.32), (-1.39, -0.41), "gold")
        bx(pot, "cross", X(s, 3.72, 4.4), (8.42, 8.8), (-1.45, 0.95), "stone")
        bx(pot, "arm", X(s, 3.25, 6.05), (8.4, 8.62), (0.3, 0.9), "stone")
        bx(pot, "arm_gold", X(s, 3.2, 6.1), (8.62, 8.72), (0.27, 0.93), "gold")
        bx(pot, "arm_end", X(s, 5.95, 6.12), (8.32, 8.6), (0.25, 0.95), "gold")
        bx(pot, "bracket", X(s, 3.8, 4.35), (8.05, 8.42), (0.0, 0.95), "stone")
        bx(pot, "step1", X(s, 3.3, 4.45), (8.8, 9.12), (-0.85, 0.82), "stone")
        bx(pot, "step1_gold", X(s, 3.27, 4.48), (9.12, 9.2), (-0.88, 0.85), "gold")
        bx(pot, "step2", X(s, 2.7, 3.5), (9.05, 9.4), (-0.6, 0.7), "stone")
        bx(pot, "step2_gold", X(s, 2.67, 3.53), (9.4, 9.48), (-0.63, 0.73), "gold")

    # ------------------------------------------------------------ benches, press socle, lantern seats
    def make_bench(tag, x0, x1, z0, z1):
        bx(bench, "top_" + tag, (x0, x1), (0.88, 1.0), (z0, z1), "woodg")
        bx(bench, "rim_" + tag, (x0 - 0.03, x1 + 0.03), (0.9, 0.975), (z0 - 0.03, z1 + 0.03), "gold")
        bx(bench, "cab_" + tag, (x0 + 0.08, x1 - 0.08), (0.5, 0.88), (z0 + 0.08, z1 - 0.08), "wood",
           {"+z": ("pic", "drawers")})
        for i, (xa, xb) in enumerate(((x0 + 0.02, x0 + 0.14), (x1 - 0.14, x1 - 0.02))):
            for j, (za, zb) in enumerate(((z0 + 0.02, z0 + 0.14), (z1 - 0.14, z1 - 0.02))):
                bx(bench, "post_%s_%d%d" % (tag, i, j), (xa, xb), (0.5, 0.88), (za, zb), "gold")
    make_bench("l", -5.6, -3.6, 0.6, 2.0)
    make_bench("lb", -3.5, -2.1, 0.2, 1.2)
    make_bench("r", 2.1, 3.95, 0.2, 1.2)
    bx(bench, "press_low", (4.25, 6.15), (0.5, 0.72), (0.45, 2.15), "black")
    bx(bench, "press_top", (4.35, 6.05), (0.72, 0.9), (0.55, 2.05), "black")
    for s in (-1, 1):
        bx(bench, "seat_low", X(s, 5.15, 6.05), (0.5, 0.72), (-0.4, 0.4), "stone")
        bx(bench, "seat", X(s, 5.25, 5.95), (0.72, 1.2), (-0.3, 0.3), "carved")

    # ------------------------------------------------------------ particle points (empty bones)
    fx = [("fx_spark_0", (0.0, 1.66, 1.5)), ("fx_spark_1", (0.0, 1.25, 0.95)),
          ("fx_ember_0", (-0.45, 1.1, -0.3)), ("fx_ember_1", (0.45, 1.1, -0.65)), ("fx_ember_2", (0.0, 1.05, 0.6)),
          ("fx_steam_0", (-1.95, 7.72, -1.6)), ("fx_steam_1", (1.95, 7.72, -1.6)),
          ("fx_steam_2", (-5.3, 3.02, 0.0)), ("fx_steam_3", (5.0, 2.8, -0.68)),
          ("fx_steam_4", (-4.42, 5.25, 0.25)), ("fx_steam_5", (4.42, 5.25, 0.25))]
    for n, p in fx:
        f.bone(n, origin=p)

    # ------------------------------------------------------------ colliders (simplified, walkable platform)
    C = f.collide
    C((-6.5, 0, -3.0), (6.5, 0.25, 3.0))
    C((-6.2, 0.25, -2.75), (6.2, 0.5, 2.7))
    for s in (-1, 1):
        C((s * 1.85, 0.5, -2.2), (s * 4.05, 6.0, 0.25))           # body sides
        C((s * 4.0, 0.5, -2.0), (s * 4.55, 3.0, -0.4))            # buttresses
        C((s * 1.1, 0.5, -1.6), (s * 1.95, 3.55, 1.0))            # furnace pillars
        C((s * 1.0, 0.5, 1.0), (s * 2.05, 1.7, 1.2))              # pillar bases
        C((s * 1.85, 2.85, 0.25), (s * 4.08, 3.7, 0.8))           # mid band + column caps
        C((s * 2.66, 3.7, -0.3), (s * 3.74, 6.0, 0.8))            # heat columns
        C((s * 3.5, 6.5, -1.35), (s * 4.25, 8.4, -0.45))          # gallows towers
        C((s * 3.25, 8.4, -1.45), (s * 6.1, 8.8, 0.95))           # arms + cross beams
        C((s * 2.7, 8.8, -0.85), (s * 4.45, 9.45, 0.82))          # gallows steps
        C((s * 5.15, 0.5, -0.4), (s * 6.05, 1.2, 0.4))            # lantern seats
    C((-1.95, 0.5, -2.2), (1.95, 0.95, 1.0))                     # hearth
    C((-1.1, 0.95, -1.4), (1.1, 3.55, 0.92))                     # the fire itself (no walking into it)
    C((-1.95, 3.55, -2.2), (1.95, 6.0, 1.0))                     # lintel, arch, upper centre
    C((-4.2, 6.0, -2.3), (4.2, 6.5, 0.7))                        # top beam
    C((-0.82, 0.5, 1.15), (0.82, 1.6, 1.85))                     # anvil
    C((-5.63, 0.5, 0.57), (-3.57, 1.0, 2.03))                    # bench left
    C((-3.53, 0.5, 0.2), (-2.07, 1.0, 1.23))                     # bench back left
    C((2.07, 0.5, 0.2), (3.98, 1.0, 1.23))                       # bench right
    C((4.25, 0.5, 0.45), (6.15, 0.9, 2.15))                      # press socle
    C((4.55, 0.9, 0.85), (5.85, 2.3, 1.75))                      # press mechanism (decor model)
    C((4.86, 0.5, -0.14), (5.14, 3.95, 0.14))                    # right pipe down to the deck
    return f


def icon(model, tex, path):
    q = fl.quads_of(model, 0)
    big = fl.render(q, tex, 256, 256, eye=(0, 5.3, 60), target=(0, 5.3, 0), ortho=9.0, bg=(255, 0, 255))
    a = np.asarray(big).astype(float)
    mask = ~((a[..., 0] > 250) & (a[..., 1] < 5) & (a[..., 2] > 250))
    out = np.zeros((16, 16, 4), np.uint8)
    for j in range(16):
        for i in range(16):
            blk = a[j * 16:(j + 1) * 16, i * 16:(i + 1) * 16]
            m = mask[j * 16:(j + 1) * 16, i * 16:(i + 1) * 16]
            if m.mean() > 0.42:
                c = blk[m].mean(0)
                c = np.clip((c - 128) * 1.25 + 128 + 10, 0, 255)
                out[j, i, :3] = c
                out[j, i, 3] = 255
    # the statue of the decor model, drawn in by hand: gold body, white wings, halo
    W, G, Gd = (236, 228, 214), (246, 196, 72), (176, 120, 30)
    for (i, j, c) in [(7, 0, G), (8, 0, G), (6, 1, W), (7, 1, G), (8, 1, G), (9, 1, W), (5, 1, W), (10, 1, W),
                      (5, 2, W), (6, 2, W), (7, 2, G), (8, 2, G), (9, 2, W), (10, 2, W), (6, 3, W), (7, 3, Gd),
                      (8, 3, Gd), (9, 3, W)]:
        out[j, i, :3] = c
        out[j, i, 3] = 255
    Image.fromarray(out, "RGBA").save(path)


def descriptor(f):
    return {"model": "models/entity/%s.bbmodel" % NAME, "texture": "textures/entity/%s.png" % NAME, "decor": None,
            "extent": [-6.5, 0.0, -3.0, 6.5, 10.0, 3.0], "colliders": f.colliders, "particles": [], "light": 15,
            "extra_models": [{"model": "models/entity/forge_divine_deco.bbmodel",
                              "texture": "textures/entity/forge_divine_deco.png"}]}


def main():
    f = build()
    model = f.export(descriptor=descriptor(f))
    tex = np.array(f.texture_png())
    icon(model, tex, os.path.join(fl.ASSETS, "textures/item/%s.png" % NAME))
    rep = FA.audit(model, tex, dump=os.path.join(fl.OUT, "audit_" + NAME))
    tag = sys.argv[sys.argv.index("--sheet") + 1] if "--sheet" in sys.argv else "it"
    fl.sheet(model, tex, os.path.join(fl.OUT, "structure_%s.png" % tag), title="forge_divine structure (%d cubes)"
             % len(model["elements"]))
    return rep


if __name__ == "__main__":
    main()
