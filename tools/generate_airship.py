#!/usr/bin/env python3
"""Generates the steampunk airship (steampunk_airship) Blockbench model, its texture and animations.

Usage:  python3 tools/generate_airship.py

Outputs:
  blockbench/steampunk_airship.bbmodel                                   (editable, texture embedded)
  src/main/resources/assets/medievalships/models/entity/steampunk_airship.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/steampunk_airship.png
  src/main/resources/assets/medievalships/textures/item/steampunk_airship.png

Reference (picture with 8 views): a long cream balloon, round in the middle and tapering to both
ends, with a blue-grey nose cap and blue-grey bands along it, under a brown rope net held by orange
rope hoops with gold clasps; a brass rod at the nose; at the tail a lattice cone carrying the shaft
of a wooden propeller, and three triangular cream fins on wooden spars (one on top, two below at the
sides); under it, a long dark wooden gondola with raised bow and stern hanging on rope lines with
gold rings, a central post up to the balloon, an engine with a gear wheel and a curved exhaust pipe
at the stern, lanterns and an anchor.

The balloon is a body of revolution built from tilted panels (no staircase): 24 gores between 20
cross sections that follow airship_shape.balloon_radius; the net is a transparent textured shell
just outside it; only the main ropes are real geometry.

Bones used by the mod (keep their names when editing in Blockbench):
  propeller (propeller: three turns per loop, played with the signed speed)
  fin_top, helm_wheel (steer)   fin_port, fin_starboard (elevator: 0 = descending, 1 = level, 2 = climbing)
"""
import math
import os
import sys
import uuid

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import generate_galleon as gn  # noqa: E402
import generate_galley as gg  # noqa: E402
import airship_shape as asp  # noqa: E402
import airship_texture as at  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/steampunk_airship/%d" % _uuid_counter[0]))


gg.new_uuid = new_uuid
gn.new_uuid = new_uuid
gn.gs = asp
gn.REGIONS = {k: (0,) + r for k, r in at.REGIONS.items()}
gn.SIZE = at.SIZE

v3, norm, Bone, add_cube, beam, board = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam, gg.board
rx, ry, rz = gg.rx, gg.ry, gg.rz
EYE = np.eye(3)
SIDES = ((1, "p"), (-1, "s"))

BY, BZ, BH, BR = asp.BALLOON_Y, asp.BALLOON_Z, asp.BALLOON_HALF, asp.BALLOON_R
# balloon cross sections (fraction of the half length, denser towards the ends)
BALLOON_S = [-asp.BALLOON_REAR_T, -0.87, -0.8, -0.71, -0.6, -0.47, -0.33, -0.18, -0.06, 0.06, 0.18, 0.33, 0.47, 0.6, 0.71,
             0.8, 0.87, 0.93, 0.97, 0.995]
NAZ = 24
BAND_AZ = (0.0, 45.0, -45.0, 90.0, -90.0, 135.0, -135.0)
HOOP_S = (-0.87, -0.6, -0.06, 0.33, 0.71)
NOSE_S = 0.7          # the blue-grey nose cap starts here
TAIL_RING_S = -0.85   # and a blue-grey ring closes the cloth at the tail
NET_S = (-0.6, 0.6)   # the net covers the middle of the balloon, between the inner hoops


def zs(s):
    return BZ + BH * s


def P(z, az_deg, out=0.0):
    return v3(*asp.balloon_point(z, math.radians(az_deg), out))


def stretched(cube):
    for f in cube.faces.values():
        if f is not None:
            f["stretch"] = True
    return cube


def panel(bone, name, a0, a1, b0, b1, th, region, outward, inner=None, overlap=1.04):
    """Tilted panel between two cross sections; its texture region is drawn whole on it."""
    return stretched(board(bone, name, a0, a1, b0, b1, th, region, outward, overlap=overlap, inner=inner))


# ---------------------------------------------------------------- gondola hull
FORE_END, AFT_END = asp.FORE_SCALE - 0.02, -asp.AFT_SCALE + 0.02
STATIONS = [AFT_END, -7.2, -6.8, -6.2, -5.4, -4.4, -3.2, -1.8, -0.6, 0.6, 1.8, 3.2, 4.4, 5.4, 6.2, 6.8, 7.2, FORE_END]
UPPER = [0.0, 0.35, 0.7, 1.0]
STRAKES = ["hull"] * 4 + ["hull", "hull", "hull_light"]


def hw(z):
    return asp.half_width(z)


def sheer(z):
    return asp.sheer_y(z)


def upper_y(z, f):
    return 0.15 + (sheer(z) - 0.15) * f


def outer_x(z, y):
    w = hw(z)
    if y <= 0.15:
        return 0.97 * w
    f = min(1.0, (y - 0.15) / max(0.05, sheer(z) - 0.15))
    return w * (0.97 + 0.03 * f)


gn.outer_x = outer_x
gn.hw = hw


def section(z, side):
    w, yk = hw(z), asp.keel_y(z)
    pts = [(0.05, yk)]
    for fx, fy in asp.BOTTOM_SECTION[1:]:
        pts.append((fx * w, fy * yk))
    for f in UPPER:
        y = upper_y(z, f)
        pts.append((outer_x(z, y), y))
    return [v3(side * max(x, 0.05), y, z) for x, y in pts]


def ring(bone, name, c, axis, r, th, region, n=8, phase=0.0):
    """Ring of n beams around centre c, in the plane normal to axis."""
    axis = norm(v3(*axis))
    e1 = norm(np.cross(axis, v3(0, 1, 0) if abs(axis[1]) < 0.9 else v3(1, 0, 0)))
    e2 = np.cross(axis, e1)
    for k in range(n):
        a0, a1 = phase + 2 * math.pi * k / n, phase + 2 * math.pi * (k + 1) / n
        p0 = c + (e1 * math.cos(a0) + e2 * math.sin(a0)) * r
        p1 = c + (e1 * math.cos(a1) + e2 * math.sin(a1)) * r
        beam(bone, "%s_%d" % (name, k), p0, p1, th, region, extend=th * 0.4)


def disc(bone, name, c, axis, r, th, region):
    """Round plate: two crossed square plates."""
    axis = norm(v3(*axis))
    e1 = norm(np.cross(axis, v3(0, 1, 0) if abs(axis[1]) < 0.9 else v3(1, 0, 0)))
    e2 = np.cross(axis, e1)
    for k, a in enumerate((0.0, math.pi / 4)):
        u = e1 * math.cos(a) + e2 * math.sin(a)
        w = np.cross(axis, u)
        add_cube(bone, "%s_%d" % (name, k), c, np.column_stack([u, w, axis]), (1.6 * r, 1.6 * r, th), region)


def build():
    root = Bone("steampunk_airship")
    balloon = Bone("balloon", parent=root)
    net = Bone("net", parent=root)
    tail = Bone("tail", parent=root)
    gondola = Bone("gondola", parent=root)
    deck = Bone("deck", parent=root)
    engine = Bone("engine", parent=root)
    ropes = Bone("suspension", parent=root)
    lanterns = Bone("lanterns", parent=root)

    # ---------------------------------------------------------------- balloon
    for i in range(len(BALLOON_S) - 1):
        za, zb = zs(BALLOON_S[i]), zs(BALLOON_S[i + 1])
        sm = (BALLOON_S[i] + BALLOON_S[i + 1]) / 2
        region = "balloon_blue" if sm > NOSE_S or sm < TAIL_RING_S else "balloon"
        for j in range(NAZ):
            a0, a1 = 360.0 * j / NAZ, 360.0 * (j + 1) / NAZ
            am = (a0 + a1) / 2
            outward = v3(math.sin(math.radians(am)), math.cos(math.radians(am)), 0)
            panel(balloon, "gore_%d_%d" % (i, j), P(za, a0), P(za, a1), P(zb, a0), P(zb, a1), 0.1, region, outward,
                  inner="balloon_in")
    # nose: brass cap and the rod with its rings and ball
    front = zs(1.0)
    disc(balloon, "nose_cap", v3(0, BY, front - 0.05), (0, 0, 1), 0.42, 0.14, "brass")
    disc(balloon, "nose_dome", v3(0, BY, front - 0.2), (0, 0, 1), 0.62, 0.3, "iron")
    ring(balloon, "nose_hub_ring", v3(0, BY, front - 0.14), (0, 0, 1), 0.66, 0.1, "gold", n=12)
    # brass ribs on the blue cap, from the hub back to a gold collar where the cream cloth begins
    zc = zs(NOSE_S)
    for k in range(8):
        az = 22.5 + 45 * k
        pts = [P(zs(s_), az, 0.07) for s_ in (NOSE_S, 0.8, 0.88, 0.94, 0.975)]
        for j in range(len(pts) - 1):
            beam(balloon, "nose_rib_%d_%d" % (k, j), pts[j], pts[j + 1], 0.08, "brass", extend=0.04)
    ring(balloon, "nose_collar", v3(0, BY, zc), (0, 0, 1), asp.balloon_radius(zc) + 0.1, 0.16, "gold", n=24)
    beam(balloon, "nose_rod", v3(0, BY, front - 0.2), v3(0, BY, asp.NOSE_ROD_Z), 0.14, "brass")
    for k, z in enumerate((front + 0.5, front + 1.2)):
        add_cube(balloon, "nose_rod_ring_%d" % k, v3(0, BY, z), EYE, (0.24, 0.24, 0.1), "gold")
    add_cube(balloon, "nose_ball", v3(0, BY, asp.NOSE_ROD_Z), rz(math.pi / 4), (0.22, 0.22, 0.22), "gold")
    # blue-grey bands along the balloon (over the gores)
    for k, az in enumerate(BAND_AZ):
        for i in range(len(BALLOON_S) - 1):
            sa, sb = BALLOON_S[i], BALLOON_S[i + 1]
            if sb <= TAIL_RING_S or sa >= NOSE_S:
                continue
            za, zb = zs(sa), zs(sb)
            ra, rb = asp.balloon_radius(za), asp.balloon_radius(zb)
            da, db = math.degrees(0.22 / max(ra, 0.3)), math.degrees(0.22 / max(rb, 0.3))
            outward = v3(math.sin(math.radians(az)), math.cos(math.radians(az)), 0)
            panel(balloon, "band_%d_%d" % (k, i), P(za, az - da, 0.06), P(za, az + da, 0.06), P(zb, az - db, 0.06),
                  P(zb, az + db, 0.06), 0.05, "band", outward)
    # rope net: a transparent shell just outside the cloth, two diamonds per panel
    for i in range(len(BALLOON_S) - 1):
        sa, sb = BALLOON_S[i], BALLOON_S[i + 1]
        if sa < NET_S[0] - 1e-6 or sb > NET_S[1] + 1e-6:
            continue
        za, zb = zs(sa), zs(sb)
        for j in range(NAZ):
            a0, a1 = 360.0 * j / NAZ, 360.0 * (j + 1) / NAZ
            am = (a0 + a1) / 2
            outward = v3(math.sin(math.radians(am)), math.cos(math.radians(am)), 0)
            c = panel(net, "net_%d_%d" % (i, j), P(za, a0, 0.13), P(za, a1, 0.13), P(zb, a0, 0.13), P(zb, a1, 0.13), 0.02, "net",
                      outward, overlap=1.0)
            for f in ("up", "down", "east", "west"):
                c.faces[f] = None
    # rope hoops with gold clasps where they cross the bands
    for h, s in enumerate(HOOP_S):
        z = zs(s)
        r = asp.balloon_radius(z) + 0.18
        ring(balloon, "hoop_%d" % h, v3(0, BY, z), (0, 0, 1), r, 0.24, "rope", n=24)
        for k, az in enumerate(BAND_AZ):
            p = P(z, az, 0.24)
            add_cube(balloon, "clasp_%d_%d" % (h, k), p, rz(-math.radians(az)), (0.34, 0.14, 0.4), "gold")

    # ---------------------------------------------------------------- tail: lattice cone, shaft, propeller
    rear = zs(BALLOON_S[0])
    r0 = asp.balloon_radius(rear)
    for k in range(6):
        a = math.radians(60 * k + 30)
        d = v3(math.sin(a), math.cos(a), 0)
        beam(tail, "tail_spar_%d" % k, v3(0, BY, rear + 0.3) + d * (r0 - 0.1), v3(0, BY, asp.TAIL_END_Z) + d * 0.3, 0.16, "band")
    cone = [(rear + 0.2, r0 + 0.02), (rear - 1.6, r0 * 0.66), (rear - 3.2, r0 * 0.36), (asp.TAIL_END_Z, 0.32)]
    for i in range(len(cone) - 1):
        (za, ra), (zb, rb) = cone[i], cone[i + 1]
        for j in range(12):
            a0, a1 = math.radians(30 * j), math.radians(30 * (j + 1))
            am = (a0 + a1) / 2
            pa0 = v3(math.sin(a0) * ra, BY + math.cos(a0) * ra, za)
            pa1 = v3(math.sin(a1) * ra, BY + math.cos(a1) * ra, za)
            pb0 = v3(math.sin(a0) * rb, BY + math.cos(a0) * rb, zb)
            pb1 = v3(math.sin(a1) * rb, BY + math.cos(a1) * rb, zb)
            c = panel(tail, "tail_net_%d_%d" % (i, j), pa0, pa1, pb0, pb1, 0.02, "net", v3(math.sin(am), math.cos(am), 0), overlap=1.0)
            for f in ("up", "down", "east", "west"):
                c.faces[f] = None
        if i > 0:
            ring(tail, "tail_ring_%d" % i, v3(0, BY, za), (0, 0, 1), ra + 0.05, 0.1, "brass", n=12)
    beam(tail, "shaft", v3(0, BY, rear + 1.0), v3(0, BY, asp.PROP_Z - 0.1), 0.24, "iron")
    add_cube(tail, "shaft_bearing", v3(0, BY, asp.TAIL_END_Z - 0.1), EYE, (0.62, 0.62, 0.5), "brass")
    add_cube(tail, "shaft_bearing_b", v3(0, BY, asp.TAIL_END_Z - 0.1), rz(math.pi / 4), (0.62, 0.62, 0.42), "brass")
    prop = Bone("propeller", origin=(0, BY, asp.PROP_Z), parent=root)
    hub = v3(0, BY, asp.PROP_Z)
    add_cube(prop, "prop_hub", hub, EYE, (0.62, 0.62, 0.56), "brass")
    add_cube(prop, "prop_hub_b", hub, rz(math.pi / 4), (0.62, 0.62, 0.5), "brass")
    add_cube(prop, "prop_spinner", hub + v3(0, 0, -0.38), rz(math.pi / 4), (0.36, 0.36, 0.3), "gold")
    add_cube(prop, "prop_spinner_tip", hub + v3(0, 0, -0.6), EYE, (0.16, 0.16, 0.18), "gold")
    pitch = math.radians(20)
    for k in range(asp.PROP_BLADES):
        a = 2 * math.pi * k / asp.PROP_BLADES
        d = v3(math.sin(a), math.cos(a), 0)
        side = np.cross(v3(0, 0, 1), d)
        # pitch: the blade is turned about its own length
        w = side * math.cos(pitch) + v3(0, 0, 1) * math.sin(pitch)
        n = np.cross(d, w)
        axes = np.column_stack([d, w, n])
        # a wooden paddle: narrow shank from a brass sleeve, then a blade widening to a pointed tip
        add_cube(prop, "prop_shank_%d" % k, hub + d * 0.72, axes, (0.7, 0.3, 0.12), "prop")
        add_cube(prop, "prop_sleeve_%d" % k, hub + d * 0.5, axes, (0.3, 0.38, 0.18), "brass")
        for j, (r0, r1, wd) in enumerate(((1.0, 1.55, 0.5), (1.55, 2.05, 0.66))):
            add_cube(prop, "prop_blade_%d_%d" % (k, j), hub + d * ((r0 + r1) / 2), axes, (r1 - r0 + 0.02, wd, 0.1), "prop")
        add_cube(prop, "prop_blade_tip_%d" % k, hub + d * (asp.PROP_R - 0.2), axes, (0.3, 0.42, 0.1), "prop")
        add_cube(prop, "prop_blade_point_%d" % k, hub + d * (asp.PROP_R - 0.02), axes, (0.08, 0.2, 0.1), "prop")
        add_cube(prop, "prop_blade_bolt_%d" % k, hub + d * 1.05 + n * 0.06, axes, (0.1, 0.1, 0.04), "brass")
    ring(prop, "prop_hub_ring", hub + v3(0, 0, 0.05), (0, 0, 1), 0.46, 0.09, "gold", n=10)

    # ---------------------------------------------------------------- fins
    fin_tri = None
    for az, name in zip(asp.FIN_AZIMUTHS, ("fin_top", "fin_port", "fin_starboard")):
        rad = v3(math.sin(math.radians(az)), math.cos(math.radians(az)), 0)
        A = P(asp.FIN_ROOT_Z[0], az, -0.05)
        B = P(asp.FIN_ROOT_Z[1], az, -0.05)
        C = v3(0, BY, asp.FIN_TIP_Z) + rad * (asp.balloon_radius(asp.FIN_TIP_Z + 2.5) + asp.FIN_SPAN)
        origin = (A + B) / 2
        fb = Bone(name, origin=tuple(origin), parent=root)
        nrm = norm(np.cross(v3(0, 0, 1), rad))
        tri = gn.tri_sail(fb, name + "_cloth", C, A, B, 0.02, nrm, "fin", nx=3, ny=7)
        fin_tri = fin_tri or tri
        # wooden spars on the edges and a middle rib, brass hinges and the brass disc at the tip
        # a fan: ribs radiating from the brass disc at the tip to the root along the balloon
        ribs = [(A, C), (B, C)]
        for f in (0.25, 0.5, 0.75):
            ribs.append((P(asp.FIN_ROOT_Z[0] + (asp.FIN_ROOT_Z[1] - asp.FIN_ROOT_Z[0]) * f, az, -0.05), C))
        ribs.append((A, B))
        for k, (p0, p1) in enumerate(ribs):
            beam(fb, "%s_spar_%d" % (name, k), p0, p1, 0.13 if k < 2 else 0.08, "wood", up=nrm, extend=0.05)
        disc(fb, name + "_tip_disc", C, nrm, 0.26, 0.1, "brass")
        add_cube(fb, name + "_tip_boss", C, EYE, (0.14, 0.14, 0.14), "gold")
        for k, p in enumerate((A, B)):
            disc(fb, "%s_hinge_%d" % (name, k), p + rad * 0.12, nrm, 0.18, 0.12, "brass")

    # ---------------------------------------------------------------- gondola hull
    for side, sn in SIDES:
        for i in range(len(STATIONS) - 1):
            za, zb = STATIONS[i], STATIONS[i + 1]
            A_, B_ = section(za, side), section(zb, side)
            for k, reg in enumerate(STRAKES):
                mid = (A_[k] + A_[k + 1] + B_[k] + B_[k + 1]) / 4
                outward = norm(v3(side, -0.7 if k < 4 else 0.0, 0) + v3(0, 0, 0.35 * np.sign(mid[2])))
                board(gondola, "hull_%s%d_%d" % (sn, i, k), A_[k], A_[k + 1], B_[k], B_[k + 1], 0.1, reg, outward,
                      inner="hull_light" if k >= 5 else None)
            pa, pb = v3(side * hw(za), sheer(za) + 0.06, za), v3(side * hw(zb), sheer(zb) + 0.06, zb)
            beam(gondola, "gunwale_%s%d" % (sn, i), pa, pb, 0.12, "hull_light", width=0.26, extend=0.04)
            for j, (f, reg, th) in enumerate(((0.62, "brass", 0.08), (0.3, "dark_wood", 0.1))):
                ya, yb = upper_y(za, f), upper_y(zb, f)
                qa, qb = v3(side * (outer_x(za, ya) + 0.04), ya, za), v3(side * (outer_x(zb, yb) + 0.04), yb, zb)
                beam(gondola, "rub_%s%d_%d" % (sn, i, j), qa, qb, th, reg, width=0.06, extend=0.04)
            if i % 2 == 0 and 0 < i < len(STATIONS) - 2:
                for k, y in enumerate((upper_y(za, 0.62) + 0.12, upper_y(za, 0.62) - 0.12)):
                    add_cube(gondola, "rivet_%s%d_%d" % (sn, i, k), v3(side * (outer_x(za, y) + 0.08), y, za), EYE, (0.06, 0.06, 0.06),
                             "gold")
    for i in range(len(STATIONS) - 1):
        za, zb = STATIONS[i], STATIONS[i + 1]
        beam(gondola, "keel_%d" % i, (0, asp.keel_y(za) - 0.05, za), (0, asp.keel_y(zb) - 0.05, zb), 0.2, "dark_wood", width=0.24,
             extend=0.05)
    for k, z in enumerate((-4.8, -2.4, 0.0, 2.4, 4.8)):
        top, bot = asp.keel_y(z) + 0.05, max(asp.LOWEST_Y, asp.keel_y(z) - 0.3)
        add_cube(gondola, "foot_%d" % k, (0, (top + bot) / 2, z), EYE, (0.5, top - bot, 0.7), "dark_wood")
    # stem and stern posts rising a little above the rail, with brass caps
    for s, tag in ((1, "stem"), (-1, "stern")):
        z0 = s * (asp.HALF_LENGTH + 0.2)
        top = sheer(z0) + 0.4
        beam(gondola, tag + "_post", (0, asp.keel_y(z0) - 0.05, z0), (0, top, z0 + s * 0.35), 0.28, "dark_wood", width=0.3, extend=0.05)
        add_cube(gondola, tag + "_cap", (0, top + 0.08, z0 + s * 0.35), EYE, (0.36, 0.14, 0.36), "brass")

    # ---------------------------------------------------------------- deck, benches, pillar, helm
    main_y = asp.MAIN_DECK_Y
    n = 32
    z0, z1 = -asp.HALF_LENGTH + 0.4, asp.HALF_LENGTH - 0.4
    for j in range(n):
        za = z0 + (z1 - z0) * j / n
        zb = z0 + (z1 - z0) * (j + 1) / n
        w = min(asp.inner_half_width(za), asp.inner_half_width(zb)) + 0.1
        add_cube(deck, "deck_%d" % j, (0, main_y - 0.06, (za + zb) / 2), EYE, (2 * w, 0.12, zb - za + 0.02),
                 {"all": "deck", "-2": "dark_wood"})
    for k, z in enumerate(asp.BENCH_Z):
        for side, sn in SIDES:
            x = side * 1.05
            add_cube(deck, "bench_%s%d" % (sn, k), (x, main_y + 0.42, z), EYE, (0.5, 0.08, 1.3), {"all": "dark_wood", "+2": "wood"})
            for dz in (-0.5, 0.5):
                add_cube(deck, "bench_leg_%s%d_%d" % (sn, k, dz > 0), (x, main_y + 0.19, z + dz), EYE, (0.4, 0.38, 0.08), "dark_wood")
    add_cube(deck, "bow_bench", (0, main_y + 0.42, asp.BOW_SEAT_Z), EYE, (1.4, 0.08, 0.5), {"all": "dark_wood", "+2": "wood"})
    for dx in (-0.5, 0.5):
        add_cube(deck, "bow_bench_leg_%d" % (dx > 0), (dx, main_y + 0.19, asp.BOW_SEAT_Z), EYE, (0.08, 0.38, 0.4), "dark_wood")
    # central post up to the balloon, brass collars and a brass plate with struts under the balloon
    bottom = BY - BR
    pz = asp.PILLAR_Z
    beam(deck, "pillar", (0, main_y, pz), (0, bottom + 0.3, pz), 0.55, "dark_wood")
    for k, y in enumerate((main_y + 0.12, 2.6, bottom - 0.6)):
        add_cube(deck, "pillar_collar_%d" % k, (0, y, pz), EYE, (0.7, 0.18, 0.7), "brass")
    add_cube(deck, "pillar_plate", (0, bottom - 0.05, pz), EYE, (1.5, 0.14, 1.5), "brass")
    for k, (dx, dz) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        beam(deck, "pillar_strut_%d" % k, (0, bottom - 1.3, pz), (dx * 0.65, bottom - 0.1, pz + dz * 0.65), 0.09, "brass")
    # helm: a small wheel on a pedestal (bone helm_wheel turns with "steer")
    hz = asp.HELM_Z
    add_cube(deck, "helm_pedestal", (0, main_y + 0.45, hz), EYE, (0.28, 0.9, 0.28), "dark_wood")
    add_cube(deck, "helm_pedestal_cap", (0, main_y + 0.92, hz), EYE, (0.34, 0.08, 0.34), "brass")
    hc = v3(0, main_y + 1.12, hz - 0.2)
    wheel = Bone("helm_wheel", origin=tuple(hc), parent=deck)
    ring(wheel, "helm_rim", hc, (0, 0, 1), 0.42, 0.07, "brass", n=10)
    for k in range(5):
        a = math.pi * k / 5
        d = v3(math.cos(a), math.sin(a), 0)
        beam(wheel, "helm_spoke_%d" % k, hc - d * 0.55, hc + d * 0.55, 0.05, "wood")
    add_cube(wheel, "helm_hub", hc, EYE, (0.14, 0.14, 0.12), "brass")

    # ---------------------------------------------------------------- engine at the stern
    ez0, ez1 = asp.ENGINE_Z
    ec = v3(0, main_y + 0.75, (ez0 + ez1) / 2)
    add_cube(engine, "boiler", ec, EYE, (1.3, 1.5, ez1 - ez0), "boiler")
    add_cube(engine, "boiler_dome", ec + v3(0, 0.85, 0.2), EYE, (0.8, 0.3, 0.8), "brass")
    add_cube(engine, "boiler_dome_b", ec + v3(0, 0.85, 0.2), ry(math.pi / 4), (0.8, 0.3, 0.8), "brass")
    for k, y in enumerate((0.2, 1.3)):
        add_cube(engine, "boiler_band_%d" % k, v3(0, main_y + y, ec[2]), EYE, (1.36, 0.1, ez1 - ez0 + 0.06), "brass")
    add_cube(engine, "firebox_door", ec + v3(0, -0.25, (ez1 - ez0) / 2 + 0.02), EYE, (0.5, 0.45, 0.04), "iron")
    add_cube(engine, "glow_firebox", ec + v3(0, -0.28, (ez1 - ez0) / 2 + 0.045), EYE, (0.3, 0.12, 0.02), "glow")
    # gear wheels on the port side, meshed
    for k, (dz, dy, r) in enumerate(((0.0, 0.15, 0.62), (0.75, 0.75, 0.32))):
        gc = v3(0.72, main_y + 0.75 + dy, ec[2] + dz)
        disc(engine, "gear_%d" % k, gc, (1, 0, 0), r, 0.1, "brass")
        add_cube(engine, "gear_axle_%d" % k, gc + v3(0.06, 0, 0), EYE, (0.12, 0.18, 0.18), "iron")
        for t in range(12 if k == 0 else 8):
            a = 2 * math.pi * t / (12 if k == 0 else 8)
            d = v3(0, math.cos(a), math.sin(a))
            add_cube(engine, "gear_tooth_%d_%d" % (k, t), gc + d * (r + 0.08), rx(-a), (0.1, 0.12, 0.1), "brass")
    # flywheel on the starboard side: a spoked wheel with a gold rim on a brass bearing
    fc = v3(-0.8, main_y + 0.85, ec[2] - 0.1)
    ring(engine, "flywheel_rim", fc, (1, 0, 0), 0.6, 0.14, "gold", n=12)
    for t in range(3):
        a = math.pi * t / 3
        d = v3(0, math.cos(a), math.sin(a))
        beam(engine, "flywheel_spoke_%d" % t, fc - d * 0.58, fc + d * 0.58, 0.07, "iron")
    add_cube(engine, "flywheel_bearing", fc + v3(0.08, 0, 0), EYE, (0.2, 0.24, 0.24), "brass")
    # curved exhaust pipe: up from the boiler, bending back, flared mouth facing aft
    pts = [v3(0, main_y + 1.4, ez0 + 0.45), v3(0, 3.0, ez0 + 0.45), v3(0, 3.9, ez0 + 0.4), v3(0, 4.45, ez0 + 0.15),
           v3(0, 4.75, ez0 - 0.3), v3(0, 4.85, ez0 - 0.8)]
    for k in range(len(pts) - 1):
        beam(engine, "exhaust_%d" % k, pts[k], pts[k + 1], 0.44, "brass", extend=0.1)
    for k, p in enumerate((pts[1], pts[3])):
        add_cube(engine, "exhaust_ring_%d" % k, p, EYE, (0.54, 0.1, 0.54), "iron")
    add_cube(engine, "exhaust_mouth", pts[-1] + v3(0, 0, -0.1), EYE, (0.64, 0.64, 0.16), "brass")
    add_cube(engine, "exhaust_soot", pts[-1] + v3(0, 0, -0.19), EYE, (0.34, 0.34, 0.02), "iron")

    # ---------------------------------------------------------------- suspension: ropes, gold rings, chains
    att_s = HOOP_S[1:]
    for side, sn in SIDES:
        for k, s in enumerate(att_s):
            z = zs(s)
            top = P(z, side * 150, 0.2)
            zr = max(-asp.HALF_LENGTH + 1.0, min(asp.HALF_LENGTH - 1.0, z))
            rail = v3(side * hw(zr), sheer(zr) + 0.12, zr)
            dl = norm(top - rail)
            # braided line from the hoop down to a short chain of big gold links made fast to the rail
            beam(ropes, "line_%s%d" % (sn, k), top, rail + dl * 1.12, 0.21, "rope", extend=0.04)
            ring(ropes, "line_ring_%s%d" % (sn, k), rail + dl * 1.5, dl, 0.19, 0.08, "gold", n=8)
            p1 = norm(np.cross(dl, v3(0, 0, 1)))
            p2 = np.cross(dl, p1)
            for c in range(3):
                ring(ropes, "line_link_%s%d_%d" % (sn, k, c), rail + dl * (0.22 + 0.33 * c), p1 if c % 2 else p2, 0.17, 0.07,
                     "gold", n=6)
            add_cube(ropes, "line_clamp_%s%d" % (sn, k), rail, EYE, (0.16, 0.12, 0.3), "brass")
            add_cube(ropes, "line_clasp_%s%d" % (sn, k), top, rz(-math.radians(side * 150)), (0.28, 0.14, 0.3), "gold")

    # ---------------------------------------------------------------- lanterns, anchor
    for side, sn in SIDES:
        z = -asp.HALF_LENGTH + 0.4
        base = v3(side * (hw(z) - 0.05), sheer(z) + 0.1, z)
        beam(lanterns, "stern_lantern_bracket_" + sn, base, base + v3(side * 0.3, 0.35, -0.1), 0.06, "brass")
        add_cube(lanterns, "stern_lantern_" + sn, base + v3(side * 0.32, 0.05, -0.1), EYE, (0.28, 0.4, 0.28),
                 {"all": "lantern", "+2": "brass", "-2": "brass"}, stretch=True)
    bz_ = asp.HALF_LENGTH - 0.6
    bb = v3(0, sheer(bz_) + 0.1, bz_)
    beam(lanterns, "bow_lantern_post", bb, bb + v3(0, 0.45, 0), 0.07, "brass")
    add_cube(lanterns, "bow_lantern", bb + v3(0, 0.68, 0), EYE, (0.26, 0.38, 0.26), {"all": "lantern", "+2": "brass", "-2": "brass"},
             stretch=True)
    # anchor hanging on a chain at the starboard quarter, clear of the ground under the keel
    az = -asp.HALF_LENGTH + 1.4
    ax_ = -(hw(az) + 0.22)
    top = v3(ax_, sheer(az) - 0.05, az)
    for c in range(5):
        add_cube(engine, "anchor_chain_%d" % c, top - v3(0, 0.12 + 0.2 * c, 0), ry(c * math.pi / 2), (0.05, 0.18, 0.1), "iron")
    shank_top = top - v3(0, 1.1, 0)
    beam(engine, "anchor_shank", shank_top, shank_top - v3(0, 0.7, 0), 0.1, "iron")
    beam(engine, "anchor_stock", shank_top + v3(0, -0.05, -0.3), shank_top + v3(0, -0.05, 0.3), 0.07, "iron")
    crown = shank_top - v3(0, 0.7, 0)
    for s in (1, -1):
        beam(engine, "anchor_arm_%d" % (s > 0), crown, crown + v3(0, 0.3, s * 0.35), 0.09, "iron")
    add_cube(engine, "anchor_ring", top - v3(0, 1.05, 0), EYE, (0.04, 0.14, 0.14), "gold")
    return root, fin_tri


def build_animations(root):
    kf, rot_kf, animation, find = gg.kf, gg.rot_kf, gg.animation, gg.find
    anims = []
    prop = find(root, "propeller")
    anims.append(animation("propeller", 2.0, "loop", [(prop, [
        rot_kf(t, (0, 0, a)) for t, a in ((0.0, 0), (0.5, 270), (1.0, 540), (1.5, 810), (2.0, 1080))])]))
    wheel, rudder = find(root, "helm_wheel"), find(root, "fin_top")
    anims.append(animation("steer", 2.0, "hold", [
        (wheel, [rot_kf(0.0, (0, 0, -150)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 0, 150))]),
        (rudder, [rot_kf(0.0, (0, 12, 0)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, -12, 0))])]))
    anims.append(animation("elevator", 2.0, "hold", [
        (find(root, name), [rot_kf(0.0, (-9, 0, 0)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (9, 0, 0))])
        for name in ("fin_port", "fin_starboard")]))
    return anims


def main():
    root, fin_tri = build()
    anims = build_animations(root)
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    tex_path = os.path.join(tex_dir, "entity/steampunk_airship.png")
    at.make_texture(tex_path, fin_tri)
    at.make_item_icon(os.path.join(tex_dir, "item/steampunk_airship.png"))
    with open(tex_path, "rb") as f:
        png = f.read()
    textures = [gn.texture_entry("steampunk_airship.png", at.SIZE, png, "entity", "steampunk_airship.png")]
    textures[0]["id"] = "0"
    model = gn.export(root, anims, textures, [
        os.path.join(ROOT, "blockbench/steampunk_airship.bbmodel"),
        os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/steampunk_airship.bbmodel"),
    ], name="steampunk_airship", visible_box=(32, 24, 0))
    print("cubes:", len(model["elements"]), "animations:", [a["name"] for a in model["animations"]])


if __name__ == "__main__":
    main()
