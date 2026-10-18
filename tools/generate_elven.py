#!/usr/bin/env python3
"""Generates the elven sailboat (elven_sailboat) Blockbench model, its texture and animations.

Usage:  python3 tools/generate_elven.py

Outputs:
  blockbench/elven_sailboat.bbmodel                                   (editable, texture embedded)
  src/main/resources/assets/medievalships/models/entity/elven_sailboat.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/elven_sailboat.png
  src/main/resources/assets/medievalships/textures/item/elven_sailboat.png

Reference: long slender turquoise hull with gold filigree and set gems, a very fine prow
ending in a carved gold scroll with a hanging lantern, a raised curved stern with another
lantern, one tall mast with three cream triangular sails edged in blue: the mainsail with a
gold eight-pointed star, the foresail with a gold crescent moon, a small topsail with a star.

Bones used by the mod (keep their names when editing in Blockbench):
  sail_main, sail_jib, sail_top (sail_wind, sail_furl)   helm_wheel, rudder (steer)
  flag, flag_tip (flag_wave)   lantern_* (lantern_sway)
"""
import math
import os
import sys
import uuid

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import elven_shape as es  # noqa: E402
import elven_texture as et  # noqa: E402
import generate_galleon as gn  # noqa: E402
import generate_galley as gg  # noqa: E402
import ship_details as sd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/elven_sailboat/%d" % _uuid_counter[0]))


gg.new_uuid = new_uuid
gn.new_uuid = new_uuid
gn.gs = es
gn.REGIONS = {k: (0,) + r for k, r in et.REGIONS.items()}
gn.SIZE = et.SIZE

v3, norm, Bone, add_cube, beam, board = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam, gg.board
rx, ry, rz = gg.rx, gg.ry, gg.rz
EYE = np.eye(3)
SIDES = ((1, "p"), (-1, "s"))

FORE_END, AFT_END = es.FORE_SCALE - 0.05, -es.AFT_SCALE + 0.05
STATIONS = [AFT_END, -12.4, -11.8, -11.0, -10.0, -8.6, -7.0, -5.0, -3.0, -1.0, 1.0, 3.0, 5.0, 7.0, 8.8, 10.2, 11.2, 12.0,
            12.6, FORE_END]
UPPER = [0.25, 0.55, 0.8, 1.0]
STRAKES = ["hull_navy"] * 4 + ["hull_navy", "hull_teal", "ornament", "hull_teal"]


def hw(z):
    return es.half_width(z)


def sheer(z):
    return es.sheer_y(z)


def upper_y(z, f):
    """Strakes above the waterline follow the sheer (they sweep up to the prow and the stern)."""
    return 0.15 + (sheer(z) - 0.15) * f


def outer_x(z, y):
    w = hw(z)
    if y <= 0.15:
        return w
    f = min(1.0, (y - 0.15) / max(0.05, sheer(z) - 0.15))
    return w * (1.0 - 0.06 * f * f)   # gentle tumblehome: a rounded, elegant section


gn.outer_x = outer_x
gn.hw = hw


def section(z, side):
    w, yk = hw(z), es.keel_y(z)
    pts = [(0.05, yk)]
    for fx, fy in es.BOTTOM_SECTION[1:]:
        pts.append((fx * w, fy * yk))
    pts.append((outer_x(z, 0.15), 0.15))
    for f in UPPER:
        y = upper_y(z, f)
        pts.append((outer_x(z, y), y))
    return [v3(side * max(x, 0.05), y, z) for x, y in pts]


def curve(points, n=6):
    """Catmull-Rom points through the given control points (smooth carved ends)."""
    pts = [points[0]] + points + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(points[-1])
    return out


def hanging_lantern(parent, name, hook, drop=0.7, s=1.0):
    """Lantern on a short chain, its own bone so that it sways (lantern_sway)."""
    b = Bone(name, origin=tuple(hook), parent=parent)
    beam(b, name + "_chain", hook, hook - v3(0, drop, 0), 0.04, "gold")
    c = hook - v3(0, drop + 0.22 * s, 0)
    add_cube(b, name + "_body", c, EYE, (0.3 * s, 0.4 * s, 0.3 * s), {"all": "lantern", "+2": "gold", "-2": "gold"}, stretch=True)
    add_cube(b, "glow_" + name, c, EYE, (0.2 * s, 0.3 * s, 0.2 * s), "glow", stretch=True)
    add_cube(b, name + "_cap", c + v3(0, 0.25 * s, 0), EYE, (0.2 * s, 0.1 * s, 0.2 * s), "gold")
    add_cube(b, name + "_finial", c - v3(0, 0.26 * s, 0), EYE, (0.08 * s, 0.12 * s, 0.08 * s), "gold")
    return b


def stem_web(bone, name, post, z_in, join_y, th=0.32):
    """Fills the space between the end of the planking (z_in) and the curved post (points from the
    keel upwards) with horizontal teal planks capped by a gold rail, so the post grows out of the hull
    instead of standing apart from it."""
    sgn = 1 if z_in > 0 else -1
    rising = [post[0]]
    for q in post[1:]:
        if q[1] <= rising[-1][1]:
            break
        rising.append(q)
    ys = [q[1] for q in rising]
    zs = [q[2] for q in rising]
    join_z = float(np.interp(join_y, ys, zs))
    top_in = sheer(z_in) + 0.02
    y, dy = ys[0] + 0.05, 0.22
    k = 0
    while y < join_y - 0.02:
        ym = min(y + dy, join_y) - min(dy, join_y - y) / 2
        h = min(dy, join_y - y)
        z_front = float(np.interp(ym, ys, zs)) - sgn * 0.12
        z_back = z_in - sgn * 0.2
        if ym > top_in:  # above the hull side: the web ends under the rail rising to the post
            z_back = z_in + (join_z - z_in) * (ym - top_in) / (join_y - top_in)
        L = (z_front - z_back) * sgn
        if L > 0.05:
            reg = "hull_navy" if ym < 0.15 else "hull_teal"
            add_cube(bone, "%s_%d" % (name, k), (0, ym, (z_front + z_back) / 2), EYE, (th, h + 0.01, L), reg)
        y += dy
        k += 1
    beam(bone, name + "_rail", v3(0, top_in + 0.04, z_in), v3(0, join_y + 0.04, join_z - sgn * 0.1), 0.12, "gold",
         width=th + 0.12, extend=0.06)


def build():
    root = Bone("elven_sailboat")
    hull = Bone("hull", parent=root)
    deck = Bone("deck", parent=root)
    bow = Bone("bow", parent=root)
    stern = Bone("stern", parent=root)
    ropes = Bone("ropes", parent=root)
    lanterns = Bone("lanterns", parent=root)
    main_y = es.MAIN_DECK_Y

    # ---- hull: navy bottom, turquoise sides, a gold filigree band, gold mouldings and gems
    for side, sn in SIDES:
        for i in range(len(STATIONS) - 1):
            za, zb = STATIONS[i], STATIONS[i + 1]
            A, B = section(za, side), section(zb, side)
            for k, reg in enumerate(STRAKES):
                mid = (A[k] + A[k + 1] + B[k] + B[k + 1]) / 4
                outward = norm(v3(side, -0.7 if k < 4 else 0.0, 0) + v3(0, 0, 0.35 * np.sign(mid[2])))
                board(hull, "hull_%s%d_%d" % (sn, i, k), A[k], A[k + 1], B[k], B[k + 1], 0.1, reg, outward,
                      inner="hull_light" if k >= 6 else None)
            pa, pb = v3(side * outer_x(za, sheer(za)), sheer(za) + 0.04, za), v3(side * outer_x(zb, sheer(zb)), sheer(zb) + 0.04, zb)
            beam(hull, "gunwale_%s%d" % (sn, i), pa, pb, 0.1, "gold", width=0.22, extend=0.04)
            for j, f in enumerate((0.55, 0.8, 0.25)):
                ya, yb = upper_y(za, f), upper_y(zb, f)
                pa, pb = v3(side * (outer_x(za, ya) + 0.03), ya, za), v3(side * (outer_x(zb, yb) + 0.03), yb, zb)
                beam(hull, "moulding_%s%d_%d" % (sn, i, j), pa, pb, 0.06, "gold", width=0.05, extend=0.04)
        for k, z in enumerate((-9.0, -5.5, -2.0, 1.5, 5.0, 8.4)):
            y = upper_y(z, 0.675)
            p, u, v, n = gn.side_frame(z, y, side)
            axes = np.column_stack([u, v, n])
            add_cube(hull, "gem_setting_%s%d" % (sn, k), p + n * 0.03, axes, (0.42, 0.42, 0.05), "gold_relief")
            add_cube(hull, "glow_gem_%s%d" % (sn, k), p + n * 0.07, axes @ rz(math.pi / 4), (0.22, 0.22, 0.06), "gem", stretch=True)
        # large carved gold arabesques along the upper hull, between the gems
        for k, z in enumerate((-7.25, -3.75, -0.25, 3.25, 6.7)):
            y = upper_y(z, 0.5)
            gn.decal(hull, "swirl_%s%d" % (sn, k), z, y, side, 2.6, 1.0, "swirl", out=0.04, th=0.02)
        # carved gold wings sweeping back from the prow, a smaller pair at the stern
        for name, z, f, w_, h_, fwd in (("bow_wing", 9.9, 0.62, 3.4, 1.6, 1), ("stern_wing", -10.3, 0.6, 2.2, 1.0, -1)):
            p, u, v, n = gn.side_frame(z, upper_y(z, f), side)
            # the root of the wing towards the end of the ship, the feathers sweeping inboard
            add_cube(hull, "%s_%s" % (name, sn), p + n * 0.07, np.column_stack([u, v, n]), (w_, h_, 0.02), "wing", stretch=True,
                     u_dir=u * fwd, v_dir=v3(0, -1, 0))
    for i in range(len(STATIONS) - 1):
        za, zb = STATIONS[i], STATIONS[i + 1]
        beam(hull, "keel_%d" % i, (0, es.keel_y(za) - 0.05, za), (0, es.keel_y(zb) - 0.05, zb), 0.18, "hull_navy", width=0.22,
             extend=0.05)

    # ---- prow: the stem rises into a long, fine gold scroll with a big gem; a lantern hangs from it
    py, pz = es.PROW_TIP
    # the beak sweeps far forward and slightly up, then curls back into a scroll
    ctrl = [v3(0, es.keel_y(FORE_END) - 0.05, FORE_END - 0.3), v3(0, 0.7, FORE_END + 0.2), v3(0, 1.9, 13.9), v3(0, 2.9, 14.9),
            v3(0, 3.7, 15.8), v3(0, py - 0.25, pz - 0.35), v3(0, py, pz), v3(0, py + 0.5, pz - 0.05), v3(0, py + 0.45, pz - 0.5),
            v3(0, py + 0.1, pz - 0.45)]
    pts = curve(ctrl, 4)
    stem_web(bow, "prow_web", pts, 12.6, 3.7)
    for j in range(len(pts) - 1):
        t = j / (len(pts) - 1)
        th = 0.5 * (1 - t) + 0.16 * t
        reg = "hull_teal" if t < 0.18 else ("gold_relief" if t < 0.8 else "gold")
        beam(bow, "prow_%d" % j, pts[j], pts[j + 1], th, reg, width=th * 0.85, extend=0.05)
        if 0.15 < t < 0.6 and j % 2 == 0:
            # gold fins on both sides of the stem
            for side in (1, -1):
                q = pts[j] + v3(side * 0.12, 0, 0)
                add_cube(bow, "prow_fin_%d_%d" % (j, side > 0), q + v3(side * 0.05, 0.1, -0.25), ry(side * 0.2) @ rx(0.6),
                         (0.04, 0.5, 0.6), "gold_relief")
    for side in (1, -1):
        c = v3(side * 0.24, 2.7, 14.75)
        add_cube(bow, "prow_gem_setting_%d" % (side > 0), c, ry(side * 0.25), (0.08, 0.7, 0.7), "gold")
        add_cube(bow, "glow_prow_gem_%d" % (side > 0), c + v3(side * 0.05, 0, 0), ry(side * 0.25) @ rx(math.pi / 4), (0.06, 0.38, 0.38),
                 "gem", stretch=True)
    hanging_lantern(lanterns, "lantern_prow", v3(0, py - 0.12, pz + 0.12), drop=0.6, s=1.25)
    # bowsprit for the foresail tack, along the top of the stem
    sprit_a, sprit_b = v3(0, sheer(11.5) + 0.2, 11.0), v3(0, 3.45, 15.3)
    beam(bow, "bowsprit", sprit_a, sprit_b, 0.18, "mast")

    # ---- stern: rises and curls inwards, with its own lantern
    sy, sz = es.STERN_TIP
    ctrl = [v3(0, es.keel_y(AFT_END) - 0.05, AFT_END + 0.25), v3(0, 0.8, AFT_END - 0.3), v3(0, 2.2, -13.6), v3(0, 3.6, -14.15),
            v3(0, sy, sz), v3(0, sy + 0.4, sz + 0.35), v3(0, sy + 0.2, sz + 0.75), v3(0, sy - 0.15, sz + 0.6)]
    pts = curve(ctrl, 4)
    stem_web(stern, "stern_web", pts, -12.4, 3.5, th=0.28)
    for j in range(len(pts) - 1):
        t = j / (len(pts) - 1)
        th = 0.4 * (1 - t) + 0.13 * t
        reg = "hull_teal" if t < 0.25 else ("gold_relief" if t < 0.85 else "gold")
        beam(stern, "stern_post_%d" % j, pts[j], pts[j + 1], th, reg, width=th * 0.85, extend=0.05)
    hanging_lantern(lanterns, "lantern_stern", v3(0, sy - 0.1, sz - 0.05), drop=0.5, s=1.1)
    rudder = Bone("rudder", origin=(0, 0.4, AFT_END + 0.2), parent=root)
    add_cube(rudder, "rudder_blade", (0, -0.9, AFT_END - 0.25), EYE, (0.14, 1.6, 0.8), {"all": "hull_navy", "+1": "hull_teal"})

    # ---- deck, benches with cushions, a few chests and coils
    n = 32
    for j in range(n):
        za = es.DECK_MIN_Z - 0.4 + (es.DECK_MAX_Z - es.DECK_MIN_Z + 0.8) * j / n
        zb = es.DECK_MIN_Z - 0.4 + (es.DECK_MAX_Z - es.DECK_MIN_Z + 0.8) * (j + 1) / n
        w = min(es.inner_half_width(za), es.inner_half_width(zb)) + 0.1
        add_cube(deck, "deck_%d" % j, (0, main_y - 0.06, (za + zb) / 2), EYE, (2 * w, 0.12, zb - za + 0.02),
                 {"all": "deck", "-2": "dark_wood"})
    for k, (x, z) in enumerate(((1.9, -5.5), (-1.9, -5.5), (1.9, -2.0), (-1.9, -2.0), (1.75, 4.6), (-1.75, 4.6))):
        s = 1 if x > 0 else -1
        add_cube(deck, "bench_%d" % k, (x + s * 0.12, main_y + 0.22, z), EYE, (0.55, 0.44, 1.0), {"all": "gold_relief", "+2": "cushion"})
        add_cube(deck, "bench_back_%d" % k, (x + s * 0.45, main_y + 0.65, z), EYE, (0.1, 0.5, 1.0), "gold_relief")
    add_cube(deck, "bow_bench", (0, main_y + 0.22, 8.4), EYE, (1.0, 0.44, 0.55), {"all": "gold_relief", "+2": "cushion"})
    add_cube(deck, "chest", (0.0, main_y + 0.25, -7.4), EYE, (0.9, 0.5, 0.6), {"all": "hull_teal", "+2": "gold_relief"})
    add_cube(deck, "chest_band", (0.0, main_y + 0.3, -7.4), EYE, (0.94, 0.08, 0.64), {"all": "gold", "+2": None, "-2": None})
    sd.rope_coil(gg, deck, "coil_0", (-1.0, main_y, 9.6), r=0.26, rope="rope")
    sd.rope_coil(gg, deck, "coil_1", (1.0, main_y, -9.0), r=0.26, rope="rope")

    # ---- helm: carved wheel on a gold pedestal
    hub = v3(0, main_y + 1.15, es.HELM_Z)
    add_cube(deck, "helm_pedestal", (0, main_y + 0.55, es.HELM_Z + 0.1), EYE, (0.26, 1.1, 0.26), "gold_relief")
    wheel = Bone("helm_wheel", origin=tuple(hub), parent=deck)
    add_cube(wheel, "helm_hub", hub, EYE, (0.18, 0.18, 0.18), "gold")
    for k in range(8):
        a = 2 * math.pi * k / 8
        d = v3(math.cos(a), math.sin(a), 0)
        beam(wheel, "helm_spoke_%d" % k, hub, hub + d * 0.6, 0.05, "gold", up=v3(0, 0, 1))
        a2 = 2 * math.pi * (k + 1) / 8
        beam(wheel, "helm_rim_%d" % k, hub + d * 0.46, hub + v3(math.cos(a2), math.sin(a2), 0) * 0.46, 0.06, "mast", width=0.07,
             up=v3(0, 0, 1), extend=0.03)

    # ---- mast, boom, the three triangular sails, the pennant
    mz = es.MAST_Z
    mast = Bone("mast", origin=(0, main_y, mz), parent=root)
    beam(mast, "mast_lower", (0, main_y - 0.2, mz), (0, 11.0, mz), 0.34, "mast")
    beam(mast, "mast_upper", (0, 10.6, mz), (0, es.MAST_TOP, mz), 0.24, "mast")
    for k, y in enumerate((3.0, 6.5, 10.8, 15.0)):
        add_cube(mast, "mast_band_%d" % k, (0, y, mz), EYE, (0.4, 0.14, 0.4), "gold")
    add_cube(mast, "mast_partners", (0, main_y + 0.1, mz), EYE, (0.7, 0.2, 0.7), "gold_relief")
    add_cube(mast, "mast_finial", (0, es.MAST_TOP + 0.15, mz), EYE, (0.26, 0.3, 0.26), "gold")
    add_cube(mast, "mast_finial_top", (0, es.MAST_TOP + 0.4, mz), ry(math.pi / 4), (0.16, 0.24, 0.16), "gold")
    boom_a, boom_b = v3(0, es.BOOM_Y, mz - 0.15), v3(0, es.BOOM_Y + 0.15, es.BOOM_END_Z)
    beam(mast, "boom", boom_a, boom_b, 0.16, "mast")
    beam(mast, "boom_roll", boom_a + v3(0, 0.15, -0.6), boom_b + v3(0, 0.15, 0.6), 0.16, "cloth_roll")

    tris = {}
    sails = []
    # mainsail aft of the mast: luff on the mast, foot on the boom
    sb = Bone("sail_main", origin=(0, 10.0, mz - 0.2), parent=mast)
    tris["sail_main"] = gn.tri_sail(sb, "sail_main", v3(0, 15.2, mz - 0.22), v3(0, es.BOOM_Y + 0.25, mz - 0.22),
                                    boom_b + v3(0, 0.2, 0.3), 1.2, v3(1, 0, 0), "sail_main", nx=6, ny=9)
    sails.append(sb)
    # foresail with the moon: from high on the mast to the prow, clew aft near the mast
    jb = Bone("sail_jib", origin=tuple(sprit_b), parent=root)
    head = v3(0, 16.4, mz + 0.25)
    tris["sail_jib"] = gn.tri_sail(jb, "sail_jib", head, sprit_b + v3(0, 0.12, -0.15), v3(0.05, 2.9, 2.6), 1.1, v3(1, 0, 0),
                                   "sail_jib", nx=6, ny=9)
    sails.append(jb)
    # small topsail with a star, aft of the upper mast
    tb = Bone("sail_top", origin=(0, 18.0, mz - 0.2), parent=mast)
    tris["sail_top"] = gn.tri_sail(tb, "sail_top", v3(0, es.MAST_TOP - 0.25, mz - 0.18), v3(0, 15.6, mz - 0.18),
                                   v3(0, 16.0, mz - 4.0), 0.45, v3(1, 0, 0), "sail_top", nx=4, ny=6)
    sails.append(tb)
    beam(ropes, "rope_top_yard", v3(0, 16.0, mz - 0.2), v3(0, 16.05, mz - 4.1), 0.06, "mast")

    fb = Bone("flag", origin=(0, es.MAST_TOP + 0.3, mz), parent=mast)
    root_pt = v3(0, es.MAST_TOP + 0.35, mz)
    w, h = 2.6, 0.42
    c1 = add_cube(fb, "flag_a", root_pt + v3(0, -h / 2, -w / 4), EYE, (0.03, h, w / 2), {"all": None, "+1": "pennant", "-1": "pennant"},
                  stretch=True, u_dir=v3(0, 0, -1), v_dir=v3(0, -1, 0))
    tip_root = root_pt + v3(0, 0, -w / 2)
    ft = Bone("flag_tip", origin=tuple(tip_root), parent=fb)
    c2 = add_cube(ft, "flag_b", tip_root + v3(0, -h / 2 + 0.05, -w / 4), EYE, (0.03, h * 0.6, w / 2),
                  {"all": None, "+1": "pennant", "-1": "pennant"}, stretch=True, u_dir=v3(0, 0, -1), v_dir=v3(0, -1, 0))
    gn.set_sub(c1, (0, 0, 0.5, 1), faces=("west", "east"))
    gn.set_sub(c2, (0.5, 0, 1, 1), faces=("west", "east"))

    # ---- lantern posts on the gunwale (lanterns hang from gold swan-neck arms)
    for k, (x, z) in enumerate(((1, -7.4), (-1, -7.4), (1, 6.4), (-1, 6.4))):
        base = v3(x * outer_x(z, sheer(z)) * 0.97, sheer(z) + 0.05, z)
        beam(lanterns, "lantern_post_%d" % k, base, base + v3(0, 1.3, 0), 0.08, "gold")
        beam(lanterns, "lantern_arm_%d" % k, base + v3(0, 1.3, 0), base + v3(x * 0.4, 1.45, 0), 0.06, "gold")
        hanging_lantern(lanterns, "lantern_%d" % k, base + v3(x * 0.42, 1.42, 0), drop=0.25, s=0.85)

    # ---- rigging (few, fine ropes)
    top = v3(0, es.MAST_TOP - 0.6, mz)
    rig = [("forestay", head + v3(0, 0.2, 0), sprit_b), ("backstay_p", top, v3(hw(-11.2) * 0.9, sheer(-11.2), -11.2)),
           ("backstay_s", top, v3(-hw(-11.2) * 0.9, sheer(-11.2), -11.2)),
           ("main_sheet", boom_b, v3(0, main_y + 0.2, es.BOOM_END_Z + 0.4)),
           ("jib_sheet_p", v3(0.05, 2.9, 2.6), v3(hw(2.0) * 0.95, sheer(2.0), 2.0)),
           ("jib_sheet_s", v3(0.05, 2.9, 2.6), v3(-hw(2.0) * 0.95, sheer(2.0), 2.0))]
    for side, sn in SIDES:
        for k, z in enumerate((0.0, -1.0)):
            rig.append(("shroud_%s%d" % (sn, k), v3(side * 0.12, 11.0, mz), v3(side * hw(z) * 0.97, sheer(z), z)))
    for name, a, b in rig:
        beam(ropes, "rope_" + name, a, b, 0.045, "rope")
    return root, tris, sails


def build_animations(root, sails):
    kf, rot_kf, animation, find = gg.kf, gg.rot_kf, gg.animation, gg.find
    anims = []
    tracks = []
    for k, b in enumerate(sails):
        ph = 0.4 * k
        tracks.append((b, [kf("scale", t, (s, 1, 1), "catmullrom") for t, s in ((0, 1.0), (0.9 + ph * 0.2, 1.12), (1.8, 0.94),
                                                                                (2.7, 1.06), (3.6, 1.0))] +
                       [rot_kf(t, (0, 0, a), "catmullrom") for t, a in ((0, 0), (1.2, 0.8), (2.4, -0.6), (3.6, 0))]))
    anims.append(animation("sail_wind", 3.6, "loop", tracks))
    anims.append(animation("sail_furl", 1.0, "hold", [(b, [kf("scale", 0.0, (1, 1, 1)), kf("scale", 1.0, (0, 0, 0))]) for b in sails]))
    hwb, rudder = find(root, "helm_wheel"), find(root, "rudder")
    anims.append(animation("steer", 2.0, "hold", [
        (hwb, [rot_kf(0.0, (0, 0, -120)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 0, 120))]),
        (rudder, [rot_kf(0.0, (0, -30, 0)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 30, 0))])]))
    f, ft = find(root, "flag"), find(root, "flag_tip")
    anims.append(animation("flag_wave", 1.2, "loop", [
        (f, [rot_kf(0, (0, 12, 0), "catmullrom"), rot_kf(0.6, (0, -12, 0), "catmullrom"), rot_kf(1.2, (0, 12, 0), "catmullrom")]),
        (ft, [rot_kf(0, (0, -22, 0), "catmullrom"), rot_kf(0.6, (0, 22, 0), "catmullrom"), rot_kf(1.2, (0, -22, 0), "catmullrom")])]))
    # hanging lanterns swing gently, each with its own phase
    tracks = []
    for k, name in enumerate(["lantern_prow", "lantern_stern", "lantern_0", "lantern_1", "lantern_2", "lantern_3"]):
        b = find(root, name)
        a = 6 if k < 2 else 4
        ph = 0.35 * k
        kfs = [rot_kf((ph + t) % 2.4, (a * math.cos(2 * math.pi * t / 2.4), 0, a * 0.6 * math.sin(2 * math.pi * t / 2.4)), "catmullrom")
               for t in (0.0, 0.6, 1.2, 1.8)]
        kfs.sort(key=lambda q: q["time"])
        tracks.append((b, kfs))
    anims.append(animation("lantern_sway", 2.4, "loop", tracks))
    return anims


def main():
    root, tris, sails = build()
    anims = build_animations(root, sails)
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    tex_path = os.path.join(tex_dir, "entity/elven_sailboat.png")
    et.make_texture(tex_path, tris)
    et.make_item_icon(os.path.join(tex_dir, "item/elven_sailboat.png"))
    with open(tex_path, "rb") as f:
        png = f.read()
    textures = [gn.texture_entry("elven_sailboat.png", et.SIZE, png, "entity", "elven_sailboat.png")]
    textures[0]["id"] = "0"
    model = gn.export(root, anims, textures, [
        os.path.join(ROOT, "blockbench/elven_sailboat.bbmodel"),
        os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/elven_sailboat.bbmodel"),
    ], name="elven_sailboat", visible_box=(34, 24, 0))
    print("cubes:", len(model["elements"]), "animations:", [a["name"] for a in model["animations"]])


if __name__ == "__main__":
    main()
