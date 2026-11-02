#!/usr/bin/env python3
"""workshop_jeweler — Établi du joaillier / Jeweller's Workbench (1.22.0; reference: the central workbench of the
jeweller's picture, described in the brief — the picture file itself was not available).

A rectangular dark oak workbench, about 2 blocks wide and 1 deep, its top at 1.0 and the machine up to about 1.37:
thick square legs with iron shoes, low stretchers and side braces, a worked plank top framed by a lighter, thicker
edge, riveted iron corner fittings, two front drawers with iron pulls and keyhole plates, a lower shelf near the floor
with gold bits and two gems. A purple runner over the top hangs down the front between the drawers (gold dagged hem,
gold cut-gem symbol). On the top: in the centre a compact cast-iron gem-cutting machine (base, A-frame, axle,
polishing disc, side hand wheel with its crank, a clamp holding a blue gem set in a gold ring against the disc); on
the left a stack of five gold ingots, a precision hammer, jeweller's pliers; scattered cut gems (red, blue, green,
purple, lit); on the right a white stone tray of gems, two rings in progress (one with a stone), a prong stand holding
a gem, a loupe. A pair of pliers and a small hammer hang on hooks under the left end of the top.

Usage:  python3 tools/workshops/generate_workshop_jeweler.py      (WS_OUT=<file>: write only the model there)
Writes: blockbench/workshop_jeweler.bbmodel, the assets copy, textures/entity/workshops_c.png (its own atlas,
        tools/workshops/ws_texture_c.py), textures/item/workshop_jeweler.png, workshops/workshop_jeweler.json.
Workshop-local coordinates: y up, +z = front (the player works from there), the anchor block at (0, 0, 0) under the
middle of the bench.
"""
import json
import math
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wslib_b as wl  # noqa: E402
import ws_texture_c as wt  # noqa: E402

wl.wt = wt   # the helpers of agent B, drawn with this workshop's own atlas (workshops_c.png)

NAME = "workshop_jeweler"
PROFESSION = "jeweler"
UP, v3, X, Z = wl.UP, wl.v3, wl.X, wl.Z
gg = wl.gg

Y_TOP = 1.0          # the top's upper face
X_EDGE, Z_EDGE = 1.02, 0.52   # the top's outer edge (half sizes)
LX, LZ, LEG = 0.83, 0.33, 0.15   # leg centres and section
CASE_Y0 = 0.60       # the bottom of the drawer case under the top
SHELF_Y = 0.27       # the lower shelf's upper face
Z_C = -0.04          # the machine's axle (z)
Y_AXLE = 1.25
DISC_R = 0.12
MACHINE_YAW = -0.6   # the machine turned towards the front right (radians about y)


# ---------------------------------------------------------------- small helpers
def gem(bone, name, foot, color, s=0.06, yaw=0.3):
    """A cut gem (lit): a girdle turned 45 degrees and a smaller crown on it; foot = bottom centre."""
    foot = v3(*foot)
    reg = {"all": "gem_" + color}
    wl.add_cube(bone, "glow_%s" % name, foot + UP * s * 0.25, gg.ry(yaw + math.pi / 4), (s, s * 0.5, s), reg, stretch=True)
    wl.add_cube(bone, "glow_%s_crown" % name, foot + UP * s * 0.6, gg.ry(yaw), (s * 0.62, s * 0.22, s * 0.62), reg, stretch=True)


def ring(bone, name, center, r, normal, segs=6, th=0.012, region="gold", start=0.0):
    """A gold ring: segs short bars round a circle of radius r about `normal`."""
    c = v3(*center)
    n = wl.norm(v3(*normal))
    a = wl.norm(np.cross(n, X if abs(n[0]) < 0.9 else Z))
    b = np.cross(n, a)
    pts = [c + (a * math.cos(start + 2 * math.pi * k / segs) + b * math.sin(start + 2 * math.pi * k / segs)) * r for k in range(segs + 1)]
    for k in range(segs):
        wl.beam(bone, "%s_%d" % (name, k), pts[k], pts[k + 1], th, region, width=th, up=n, extend=th * 0.4)
    return pts


def ingot(bone, name, c, yaw, s=1.0):
    """A small gold ingot lying flat; c = bottom centre."""
    c = v3(*c)
    wl.add_cube(bone, name, c + UP * 0.0225 * s, gg.ry(yaw), (0.17 * s, 0.045 * s, 0.075 * s), {"all": "gold_side", "+2": "gold_ingot"},
                stretch=True)


def pliers(bone, name, pivot, d, side, length=0.2, spread=0.035, th=0.014):
    """Jeweller's pliers: two short steel jaws ahead of the pivot (along d), two arms behind it opening in a V
    (along -d, apart along side) with red leather grips, the pivot rivet."""
    p = v3(*pivot)
    d, side = wl.norm(v3(*d)), wl.norm(v3(*side))
    n = np.cross(d, side)
    for s in (-1, 1):
        wl.beam(bone, "%s_jaw_%d" % (name, (s + 1) // 2), p, p + d * length * 0.28 + side * s * 0.004, th, "steel", width=th * 0.8, up=n)
        end = p - d * length * 0.72 + side * s * spread
        wl.beam(bone, "%s_arm_%d" % (name, (s + 1) // 2), p, end, th, "steel", width=th * 0.8, up=n)
        wl.beam(bone, "%s_grip_%d" % (name, (s + 1) // 2), p + (end - p) * 0.45, end + (end - p) * 0.04, th * 1.5, "leather", width=th * 1.3,
                up=n)
    wl.add_cube(bone, name + "_pivot", p, wl.EYE, (0.022, 0.022, 0.022), "iron")


def hammer(bone, name, grip_end, d, head_up, length=0.24):
    """A small precision hammer: a wooden handle from grip_end along d, a steel head across its far end (along
    head_up x d), a slimmer peen on one side."""
    p0 = v3(*grip_end)
    d = wl.norm(v3(*d))
    hu = wl.norm(v3(*head_up))
    p1 = p0 + d * length
    wl.beam(bone, name + "_handle", p0, p1 + d * 0.01, 0.022, "handle", width=0.02, up=hu)
    across = wl.norm(np.cross(hu, d))
    axes = np.column_stack([across, hu, d])
    wl.add_cube(bone, name + "_head", p1, axes, (0.075, 0.036, 0.036), "steel")
    wl.add_cube(bone, name + "_peen", p1 - across * 0.055, axes, (0.04, 0.022, 0.026), "steel")


# ---------------------------------------------------------------- the bench
def bench(root, detail):
    b = wl.Bone("bench", parent=root)
    th = 0.12
    # the worked top: three planks framed by a thicker, lighter edge (overhanging the legs)
    zi = Z_EDGE - 0.08
    xi = X_EDGE - 0.08
    n = 3
    for k in range(n):
        z0 = -zi + 2 * zi * k / n
        wl.box(b, "top_plank_%d" % k, (-xi, Y_TOP - th, z0), (xi, Y_TOP, z0 + 2 * zi / n), {"all": "plank_top", "+1": "end_grain", "-1": "end_grain"},
               u_dir=X)
    for s, nm in ((1, "front"), (-1, "back")):
        wl.box(b, "edge_" + nm, (-X_EDGE, Y_TOP - 0.14, s * zi), (X_EDGE, Y_TOP, s * Z_EDGE), {"all": "wood_edge"}, u_dir=X)
    for s, nm in ((-1, "left"), (1, "right")):
        wl.box(b, "edge_" + nm, (s * xi, Y_TOP - 0.14, -zi), (s * X_EDGE, Y_TOP, zi), {"all": "wood_edge"}, u_dir=Z)
    # riveted iron caps on the four corners of the top
    for sx in (-1, 1):
        for sz in (-1, 1):
            wl.add_cube(b, "corner_iron_%d_%d" % ((sx + 1) // 2, (sz + 1) // 2), (sx * (X_EDGE - 0.045), Y_TOP - 0.07, sz * (Z_EDGE - 0.045)),
                        wl.EYE, (0.1, 0.155, 0.1), "iron_rivet", stretch=True)
    # thick square legs, iron shoes, iron straps where they meet the drawer case at the front
    for sx in (-1, 1):
        for sz in (-1, 1):
            k = "%d%d" % ((sx + 1) // 2, (sz + 1) // 2)
            wl.add_cube(b, "leg_" + k, (sx * LX, (Y_TOP - th) / 2, sz * LZ), wl.EYE, (LEG, Y_TOP - th, LEG),
                        {"all": "wood_dark", "+2": "end_grain", "-2": "end_grain"}, u_dir=UP)
            wl.add_cube(b, "leg_shoe_" + k, (sx * LX, 0.035, sz * LZ), wl.EYE, (LEG + 0.02, 0.07, LEG + 0.02), "iron_dark")
        wl.add_cube(b, "leg_strap_%d" % ((sx + 1) // 2), (sx * LX, 0.74, LZ + LEG / 2 + 0.006), wl.EYE, (0.1, 0.12, 0.012), "iron_rivet",
                    stretch=True)
    # the drawer case under the top: front, sides, back
    xin = LX - LEG / 2
    wl.box(b, "case_front", (-xin, CASE_Y0, 0.37), (xin, Y_TOP - th, 0.395), "wood_mid", u_dir=X)
    wl.box(b, "case_back", (-xin, CASE_Y0, -0.395), (xin, Y_TOP - th, -0.37), "wood_mid", u_dir=X)
    for s in (-1, 1):
        wl.box(b, "case_side_%d" % ((s + 1) // 2), (s * (LX - 0.02), CASE_Y0, -(LZ - LEG / 2)), (s * (LX + 0.02), Y_TOP - th, LZ - LEG / 2),
               "wood_mid", u_dir=Z)
    # two front drawers (left and right of the runner), iron pulls under their keyhole plates
    for s in (-1, 1):
        k = (s + 1) // 2
        x0, x1 = sorted((s * 0.3, s * 0.72))
        wl.box(b, "drawer_%d" % k, (x0, 0.635, 0.395), (x1, 0.835, 0.42), {"all": "wood_edge", "+3": "drawer"}, stretch=True, u_dir=X, v_dir=-UP)
        xc = (x0 + x1) / 2
        wl.add_cube(detail, "drawer_pull_plate_%d" % k, (xc, 0.7, 0.425), wl.EYE, (0.1, 0.035, 0.01), "iron_dark")
        wl.beam(b, "drawer_pull_%d" % k, (xc - 0.055, 0.69, 0.437), (xc + 0.055, 0.69, 0.437), 0.02, "iron", width=0.018)
    # low stretchers all round, the lower shelf on them, a diagonal brace on each side
    for s in (-1, 1):
        wl.box(b, "stretcher_side_%d" % ((s + 1) // 2), (s * LX - 0.035, 0.17, -(LZ - LEG / 2)), (s * LX + 0.035, 0.25, LZ - LEG / 2), "wood_dark",
               u_dir=Z)
        wl.box(b, "stretcher_%s" % ("front" if s > 0 else "back"), (-xin, 0.2, s * LZ - 0.03), (xin, 0.3, s * LZ + 0.03), "wood_dark", u_dir=X)
    for k in range(2):
        z0 = -(LZ - 0.03) + k * (LZ - 0.03)
        wl.box(b, "shelf_%d" % k, (-xin, SHELF_Y - 0.035, z0), (xin, SHELF_Y, z0 + (LZ - 0.03)), {"all": "plank_top", "+1": "end_grain",
                                                                                               "-1": "end_grain"}, u_dir=X)
    for sx in (-1, 1):
        for sz in (-1, 1):
            p0 = v3(sx * (LX + 0.035), 0.42, sz * (LZ - LEG / 2))
            p1 = v3(sx * (LX + 0.035), CASE_Y0 + 0.02, sz * 0.06)
            wl.beam(b, "brace_%d%d" % ((sx + 1) // 2, (sz + 1) // 2), p0, p1, 0.05, "wood_dark", width=0.04, up=X)
    wl.collide((-X_EDGE, 0.0, -Z_EDGE, X_EDGE, Y_TOP, Z_EDGE))


def runner(root):
    """The purple runner: along the middle of the top from back to front, hanging down the front (between the
    drawers) to below them, a short drop at the back."""
    c = wl.Bone("runner", parent=root)
    w = 0.62
    # no face underneath (it would lie in the planks' plane: tools/zfight.py would push the planks up through it)
    wl.box(c, "runner_top", (-w / 2, Y_TOP + 0.002, -Z_EDGE - 0.005), (w / 2, Y_TOP + 0.013, Z_EDGE + 0.005), {"all": "cloth_purple", "-2": None},
           stretch=True, u_dir=X, v_dir=Z)
    fold_y = Y_TOP - 0.14                       # the edge's bottom: the texture folds at row FOLD of its 64
    h = (Y_TOP + 0.012 - fold_y) * 64 / wt.FOLD
    wl.plate(c, "runner_hang", (0, Y_TOP + 0.012 - h / 2, Z_EDGE + 0.011), w, h, "runner_hang", normal=(0, 0, 1), th=0.012, both=False)
    hb = 0.17
    wl.plate(c, "runner_back", (0, Y_TOP + 0.012 - hb / 2, -Z_EDGE - 0.011), w, hb, "runner_back", normal=(0, 0, -1), th=0.012, both=False)


def machine(root, detail):
    """The gem-cutting / polishing machine in the middle of the top, on the runner, turned a little (MACHINE_YAW) so
    that both the polishing disc and the hand wheel face someone standing in front of the bench. Drawn in its own
    frame (axle along x, the clamp to +z) then turned about its axle's foot."""
    m = wl.Bone("machine", parent=root)
    M = gg.ry(MACHINE_YAW)
    O = v3(0, 0, Z_C)

    def T(x, y, z):
        return O + M @ (v3(x, y, z) - O)

    def cube(name, c, size, region, axes=wl.EYE, **kw):
        for k in ("u_dir", "v_dir"):
            if kw.get(k) is not None:
                kw[k] = M @ kw[k]
        return wl.add_cube(m, name, T(*c), M @ axes, size, region, **kw)

    def bar(name, a, b, th, region, width=None, up=UP):
        return wl.beam(m, name, T(*a), T(*b), th, region, width=width, up=M @ up)

    y0 = Y_TOP + 0.013
    cube("machine_base", (0.01, y0 + 0.019, Z_C + 0.02), (0.42, 0.038, 0.44), {"all": "cast_iron", "+2": "iron"})
    yb = y0 + 0.068
    cube("machine_plinth", (0.0, y0 + 0.053, Z_C - 0.015), (0.3, 0.03, 0.23), "cast_iron")
    # the A-frame on each side of the disc, the bearings, the axle
    for s in (-1, 1):
        k = (s + 1) // 2
        x = s * 0.1
        for j, dz in enumerate((-0.11, 0.11)):
            bar("frame_%d_%d" % (k, j), (x, yb - 0.01, Z_C + dz), (x, Y_AXLE + 0.01, Z_C), 0.032, "cast_iron", width=0.03, up=X)
        cube("bearing_%d" % k, (x, Y_AXLE, Z_C), (0.045, 0.05, 0.055), "iron_dark")
    bar("axle", (-0.14, Y_AXLE, Z_C), (0.2, Y_AXLE, Z_C), 0.022, "steel", width=0.022)
    # the polishing disc: its two round faces (cut out) round a dark octagonal rim
    cube("disc", (0, Y_AXLE, Z_C), (0.04, 2 * DISC_R, 2 * DISC_R), {"all": None, "+1": "disc", "-1": "disc"}, stretch=True,
         u_dir=Z, v_dir=-UP)
    a = DISC_R / math.sqrt(2)
    # (thicknesses 0.024 and 0.008 inside the 0.04 disc: no two faces in one plane, tools/zfight.py leaves them alone)
    for j, (ang, t) in enumerate(((0.0, 0.024), (math.pi / 4, 0.008))):
        cube("disc_rim_%d" % j, (0, Y_AXLE, Z_C), (t, 2 * a, 2 * a), "disc_rim", axes=gg.rx(ang))
    # the hand wheel outside the right frame, its hub and crank handle
    xw = 0.17
    cube("hand_wheel", (xw, Y_AXLE, Z_C), (0.016, 0.2, 0.2), {"all": None, "+1": "wheel", "-1": "wheel"}, stretch=True, u_dir=Z, v_dir=-UP)
    cube("hand_wheel_hub", (xw, Y_AXLE, Z_C), (0.04, 0.04, 0.04), "iron_dark")
    ang = math.radians(50)
    pin = (xw, Y_AXLE + 0.08 * math.sin(ang), Z_C + 0.08 * math.cos(ang))
    bar("crank_pin", pin, (pin[0] + 0.045, pin[1], pin[2]), 0.014, "steel", width=0.014)
    bar("crank_grip", (pin[0] + 0.04, pin[1], pin[2]), (pin[0] + 0.1, pin[1], pin[2]), 0.022, "handle", width=0.022)
    # the clamp: a post at the front of the base, jaws gripping a gold ring whose blue stone touches the disc
    zr = Z_C + DISC_R + 0.01
    zp = Z_C + 0.19
    bar("clamp_post", (0, yb - 0.03, zp), (0, 1.2, zp), 0.032, "cast_iron", width=0.032)
    bar("clamp_arm", (0, 1.195, zp + 0.012), (0, 1.195, zr - 0.006), 0.022, "steel", width=0.03)
    for s in (-1, 1):
        cube("clamp_jaw_%d" % ((s + 1) // 2), (s * 0.022, 1.212, zr), (0.014, 0.03, 0.03), "steel")
    cube("clamp_screw", (0, 1.15, zp + 0.025), (0.03, 0.03, 0.03), "brass")
    ring(m, "held_ring", T(0, Y_AXLE, zr), 0.035, M @ Z, segs=8, th=0.012, start=math.pi / 8)
    gem(m, "held_gem", T(0, Y_AXLE + 0.036, zr - 0.006), "blue", s=0.05, yaw=MACHINE_YAW)
    # one collision box round the machine (its turned base and the disc above the top)
    pts = np.array([T(x, 0, z) for x in (-0.2, 0.27) for z in (Z_C - 0.2, Z_C + 0.24)])
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    wl.collide((lo[0], Y_TOP, lo[2], hi[0], Y_AXLE + DISC_R, hi[2]))


def top_props(root, detail, rng):
    """Everything else on the top: ingots, tools, gems, the tray, rings, the prong stand, the loupe."""
    p = wl.Bone("props", parent=root)
    y = Y_TOP
    # left: a stack of five gold ingots (three below, two across the gaps above)
    base, yaw = v3(-0.66, y, -0.24), 0.12
    R = gg.ry(yaw)
    for k, dz in enumerate((-0.092, 0.0, 0.092)):
        ingot(p, "ingot_%d" % k, base + R @ v3(0.01 * (k % 2), 0, dz), yaw)
    for k, dz in enumerate((-0.046, 0.046)):
        ingot(p, "ingot_top_%d" % k, base + R @ v3(-0.01, 0.045, dz), yaw + 0.06)
    # left front: the precision hammer and the pliers lying on the top
    hammer(detail, "hammer", (-0.42, y + 0.011, 0.36), (-math.cos(0.5), 0, -math.sin(0.5)), (0, 1, 0), length=0.24)
    d = v3(math.cos(2.3), 0, -math.sin(2.3))
    pliers(detail, "pliers", (-0.8, y + 0.008, 0.1), d, np.cross(UP, d), length=0.22, spread=0.035)
    # scattered cut gems (lit)
    for k, (gx, gz, col, s) in enumerate(((-0.4, -0.12, "red", 0.065), (-0.46, 0.14, "blue", 0.06), (-0.88, -0.08, "green", 0.06),
                                          (-0.6, 0.06, "purple", 0.055), (0.38, 0.06, "red", 0.05), (-0.36, 0.42, "green", 0.045))):
        gem(detail, "gem_%d" % k, (gx, y, gz), col, s=s, yaw=rng.uniform(0, 1.5))
    # right back: the white stone tray of gems
    tc, tyaw = v3(0.64, y, -0.2), -0.08
    R = gg.ry(tyaw)
    tw, td = 0.38, 0.26
    wl.add_cube(p, "tray", tc + UP * 0.012, R, (tw, 0.024, td), {"all": "marble", "+2": "marble_dark"})
    for s in (-1, 1):
        wl.add_cube(p, "tray_rim_z%d" % ((s + 1) // 2), tc + R @ v3(0, 0.024, s * (td / 2 - 0.0125)), R, (tw, 0.03, 0.025), "marble")
        wl.add_cube(p, "tray_rim_x%d" % ((s + 1) // 2), tc + R @ v3(s * (tw / 2 - 0.0125), 0.024, 0), R, (0.025, 0.03, td - 0.05), "marble")
    for k, (dx, dz, col) in enumerate(((-0.1, -0.04, "red"), (0.0, 0.05, "blue"), (0.09, -0.05, "green"), (0.12, 0.05, "purple"),
                                       (-0.11, 0.06, "blue"))):
        gem(detail, "tray_gem_%d" % k, tc + R @ v3(dx, 0.024, dz), col, s=0.055, yaw=rng.uniform(0, 1.5))
    # rings in progress: one with a red stone, one plain
    ring(detail, "ring_a", (0.37, y + 0.008, 0.2), 0.046, (0, 1, 0), segs=8, th=0.014, start=math.pi / 8)
    gem(detail, "ring_a_stone", (0.37, y + 0.01, 0.2 + 0.046), "red", s=0.042, yaw=0.2)
    # the other standing in the slot of a small wooden ring block, facing the front
    wl.box(detail, "ring_block", (0.5, y, 0.37), (0.62, y + 0.03, 0.43), {"all": "handle", "+2": "end_grain"})
    ring(detail, "ring_b", (0.56, y + 0.068, 0.4), 0.045, (0, 0, 1), segs=8, th=0.012, start=math.pi / 8)
    # the prong stand holding a green gem
    sc = v3(0.84, y, 0.16)
    wl.octo(detail, "stand_base", sc, 0.045, 0.02, "brass")
    top = sc + UP * 0.09
    wl.beam(detail, "stand_stem", sc + UP * 0.015, top, 0.016, "brass", width=0.016)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        out = v3(math.cos(a), 0, math.sin(a))
        wl.beam(detail, "stand_prong_%d" % k, top, top + out * 0.028 + UP * 0.045, 0.008, "steel", width=0.008)
    gem(detail, "stand_gem", top + UP * 0.008, "green", s=0.05, yaw=0.0)
    # the loupe lying on the top, its lens tilted on the handle
    lc = v3(0.72, y + 0.03, 0.34)
    tilt = 0.3
    Rl = gg.ry(-0.6) @ gg.rx(tilt)
    wl.add_cube(detail, "loupe_lens", lc, Rl, (0.1, 0.01, 0.1), {"all": None, "+2": "lens", "-2": "lens"}, stretch=True)
    hd = Rl @ v3(0, 0, 1)
    wl.beam(detail, "loupe_ferrule", lc + hd * 0.05, lc + hd * 0.075, 0.026, "brass", width=0.026)
    wl.beam(detail, "loupe_handle", lc + hd * 0.07, lc + hd * 0.17 - UP * 0.015, 0.022, "handle", width=0.022)


def hanging_tools(root, detail):
    """Two hooks under the left end of the top: a pair of pliers and a small hammer hang from them."""
    x = -(X_EDGE - 0.06)
    y = Y_TOP - 0.14
    for k, z in enumerate((-0.16, 0.15)):
        wl.beam(detail, "hook_%d" % k, (x, y + 0.005, z), (x, y - 0.07, z), 0.012, "iron_dark", width=0.012)
        wl.beam(detail, "hook_tip_%d" % k, (x, y - 0.07, z), (x - 0.025, y - 0.05, z), 0.012, "iron_dark", width=0.012)
    pliers(detail, "hung_pliers", (x - 0.012, y - 0.15, -0.16), (0, 1, 0), (0, 0, 1), length=0.24, spread=0.045)
    hammer(detail, "hung_hammer", (x - 0.015, y - 0.32, 0.15), (0, 1, 0), (-1, 0, 0), length=0.24)


def shelf_props(root, detail):
    """Gold bits and two gems on the lower shelf."""
    y = SHELF_Y
    ingot(detail, "shelf_ingot_0", (-0.45, y, 0.04), 0.3, s=0.8)
    ingot(detail, "shelf_ingot_1", (-0.3, y, -0.08), -0.5, s=0.8)
    for k, (x, z) in enumerate(((-0.12, 0.08), (-0.06, 0.0), (-0.16, -0.04))):
        wl.add_cube(detail, "nugget_%d" % k, (x, y + 0.015, z), gg.ry(0.5 * k), (0.035, 0.03, 0.03), "nugget", stretch=True)
    gem(detail, "shelf_gem_0", (0.22, y, 0.08), "red", s=0.06, yaw=0.4)
    gem(detail, "shelf_gem_1", (0.38, y, -0.06), "blue", s=0.055, yaw=1.1)


def build():
    rng = random.Random(122)
    root = wl.Bone(NAME)
    detail = wl.Bone("detail", parent=root)
    bench(root, detail)
    runner(root)
    machine(root, detail)
    top_props(root, detail, rng)
    hanging_tools(root, detail)
    shelf_props(root, detail)
    return root


def icon(path):
    """32x32: the bench seen from the front: dark oak top and legs, the purple runner with its gold diamond and
    dagged hem, the grey machine's disc, gold ingots and a red gem."""
    im, d = wl.new_icon(32)
    wood, edge, dark = (92, 60, 34, 255), (160, 116, 72, 255), (52, 34, 18, 255)
    purple, gold = (96, 38, 140, 255), (236, 186, 60, 255)
    # legs, shelf, case and drawers
    d.rectangle([3, 16, 5, 30], fill=dark)
    d.rectangle([26, 16, 28, 30], fill=dark)
    d.rectangle([5, 25, 26, 26], fill=wood)
    d.rectangle([5, 17, 26, 21], fill=wood)
    for x0 in (6, 19):
        d.rectangle([x0, 17, x0 + 6, 21], outline=edge, fill=(110, 74, 44, 255))
        d.point((x0 + 3, 19), fill=(40, 40, 44, 255))
    # the top with its lighter edge and iron corners
    d.rectangle([1, 13, 30, 16], fill=edge)
    d.rectangle([1, 13, 30, 13], fill=(186, 140, 92, 255))
    d.rectangle([1, 13, 2, 16], fill=(52, 52, 58, 255))
    d.rectangle([29, 13, 30, 16], fill=(52, 52, 58, 255))
    # the runner hanging in the middle, gold diamond, dagged hem
    d.rectangle([12, 13, 19, 24], fill=purple)
    for x in range(12, 20):
        d.point((x, 25 if x % 2 else 24), fill=gold)
    d.polygon([(15, 16), (16, 16), (18, 18), (15.5, 22), (13, 18)], outline=gold)
    # the machine: base, frame, disc, hand wheel
    d.rectangle([11, 11, 20, 12], fill=(100, 104, 112, 255))
    d.ellipse([12, 3, 19, 10], fill=(168, 172, 178, 255), outline=(60, 60, 66, 255))
    d.point((15, 6), fill=(40, 40, 44, 255))
    d.ellipse([20, 5, 24, 9], outline=(60, 60, 66, 255))
    d.point((24, 4), fill=(176, 128, 80, 255))
    d.point((15, 10), fill=(60, 120, 240, 255))
    # gold ingots on the left, a red gem and a tray on the right
    d.rectangle([3, 11, 9, 12], fill=gold)
    d.rectangle([4, 9, 8, 10], fill=(250, 224, 138, 255))
    d.rectangle([23, 11, 28, 12], fill=(232, 228, 220, 255))
    d.point((25, 10), fill=(224, 40, 60, 255))
    d.point((27, 10), fill=(34, 192, 96, 255))
    wl.save_icon(im, path)


def main():
    wl.setup(NAME)
    root = build()
    wl.export(root, NAME, particles=[], icon=icon, visible_box=(4, 3, 0))
    if not os.environ.get("WS_OUT"):
        # the profession this workbench belongs to (read by TentType#profession; also the default from the id)
        path = os.path.join(wl.ASSETS, "workshops/%s.json" % NAME)
        with open(path) as f:
            data = json.load(f)
        data["profession"] = PROFESSION
        with open(path, "w") as f:
            json.dump(data, f, indent=1)


if __name__ == "__main__":
    main()
