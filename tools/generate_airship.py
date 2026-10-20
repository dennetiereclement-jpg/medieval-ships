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

The balloon is a body of revolution built from tilted panels (no staircase): 32 gores between 32
cross sections (denser at the rounded nose and at the small tail dome) that follow
airship_shape.balloon_radius; the net is a transparent textured shell just outside it; only the
main ropes are real geometry. Round parts (ropes, hoops, rails, pillar, boiler, pipe, hubs, discs)
are regular prisms made of a few turned boxes (prism/tube/disc); the fins have hollowed curved
edges (the texture follows the curves); the gondola sections follow a smooth curve.

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
# balloon cross sections (fraction of the half length, denser towards the rounded ends); the cloth
# goes on behind BALLOON_REAR_T as a small blue tail dome inside the lattice cone
BALLOON_S = [-0.99, -0.975, -0.95, -asp.BALLOON_REAR_T, -0.885, -0.85, -0.81, -0.76, -0.7, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1,
             0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.76, 0.81, 0.855, 0.895, 0.93, 0.957, 0.977, 0.99, 0.997]
NAZ = 32
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


def perp_frame(u):
    u = norm(v3(*u))
    ref = v3(0, 1, 0) if abs(u[1]) < 0.9 else v3(1, 0, 0)
    e1 = norm(ref - np.dot(ref, u) * u)
    return u, e1, np.cross(u, e1)


def prism(bone, name, c, u, e1, length, R, sides, region, phase=0.0, **kw):
    """Regular prism of axis u: sides // 2 flat boxes of width 2R cos(pi/sides) and thickness
    2R sin(pi/sides), turned by 180/(sides/2) degrees about the axis; their union is exactly the
    regular polygon of circumradius R (sides = 4: one square box). Lengths differ by a hair so the
    end caps do not fight."""
    u = norm(u)
    e1 = norm(e1 - np.dot(e1, u) * u)
    e2 = np.cross(u, e1)
    if sides == 4:
        k, a, b = 1, 2 * R * math.cos(math.pi / 4), 2 * R * math.cos(math.pi / 4)
    else:
        k, a, b = sides // 2, 2 * R * math.cos(math.pi / sides), 2 * R * math.sin(math.pi / sides)
    out = []
    for j in range(k):
        ang = phase + math.pi * j / k
        v = e1 * math.cos(ang) + e2 * math.sin(ang)
        out.append(add_cube(bone, name if j == 0 else "%s_r%d" % (name, j), c, np.column_stack([u, v, np.cross(u, v)]),
                            (max(0.01, length + 0.014 * (j - (k - 1) / 2)), a, b), region, **kw))
    return out


def tube(bone, name, p0, p1, d, region, sides=6, extend=0.0, phase=0.0, **kw):
    """Round bar of mean diameter d from p0 to p1: a regular prism (hexagonal by default)."""
    p0, p1 = v3(*p0), v3(*p1)
    u, e1, e2 = perp_frame(p1 - p0)
    R = d / (1 + math.cos(math.pi / sides))
    return prism(bone, name, (p0 + p1) / 2, u, e1, np.linalg.norm(p1 - p0) + 2 * extend, R, sides, region, phase=phase, **kw)


def polyline(bone, name, pts, d, region, sides=6, extend=None):
    for k in range(len(pts) - 1):
        tube(bone, "%s_%d" % (name, k), pts[k], pts[k + 1], d, region, sides=sides, extend=d * 0.3 + 0.03 if extend is None else extend)


def catmull(pts, m):
    """Catmull-Rom curve through the points, m sub-segments per segment (the ends are kept)."""
    pts = [np.asarray(p, dtype=float) for p in pts]
    ext = [2 * pts[0] - pts[1]] + pts + [2 * pts[-1] - pts[-2]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for j in range(m):
            t = j / m
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1])
    return out


def bezier(p0, p1, p2, m):
    p0, p1, p2 = v3(*p0), v3(*p1), v3(*p2)
    return [(1 - t) ** 2 * p0 + 2 * t * (1 - t) * p1 + t * t * p2 for t in (j / m for j in range(m + 1))]


# ---------------------------------------------------------------- gondola hull
FORE_END, AFT_END = asp.FORE_SCALE - 0.02, -asp.AFT_SCALE + 0.02
_ST = [AFT_END, -7.2, -6.8, -6.2, -5.4, -4.4, -3.2, -1.8, -0.6, 0.6, 1.8, 3.2, 4.4, 5.4, 6.2, 6.8, 7.2, FORE_END]
STATIONS = _ST
UPPER = [0.0, 0.35, 0.7, 1.0]
STRAKES = ["hull"] * 4 + ["hull", "hull", "hull_light"]
SUB = 2   # each strake of the section is split in two along a smooth curve (rounder bilge)


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
    pts = catmull(pts, SUB)
    return [v3(side * max(x, 0.05), y, z) for x, y in pts]


def ring(bone, name, c, axis, r, th, region, n=8, phase=0.0, round_=False):
    """Ring of n bars around centre c, in the plane normal to axis (round bars if round_)."""
    axis = norm(v3(*axis))
    e1 = norm(np.cross(axis, v3(0, 1, 0) if abs(axis[1]) < 0.9 else v3(1, 0, 0)))
    e2 = np.cross(axis, e1)
    for k in range(n):
        a0, a1 = phase + 2 * math.pi * k / n, phase + 2 * math.pi * (k + 1) / n
        p0 = c + (e1 * math.cos(a0) + e2 * math.sin(a0)) * r
        p1 = c + (e1 * math.cos(a1) + e2 * math.sin(a1)) * r
        if round_:
            tube(bone, "%s_%d" % (name, k), p0, p1, th, region, extend=th * 0.3)
        else:
            beam(bone, "%s_%d" % (name, k), p0, p1, th, region, extend=th * 0.4)


def disc(bone, name, c, axis, r, th, region, sides=12, phase=0.0):
    """Round plate of radius r (a thin regular prism)."""
    axis = norm(v3(*axis))
    e1 = norm(np.cross(axis, v3(0, 1, 0) if abs(axis[1]) < 0.9 else v3(1, 0, 0)))
    return prism(bone, name, v3(*c), axis, e1, th, 2 * r / (1 + math.cos(math.pi / sides)), sides, region, phase=phase)


def dome(bone, name, c, axis, r, h, region, steps=3):
    """Rounded cap: stacked discs shrinking along axis (a quarter ellipse of radius r, height h)."""
    axis = norm(v3(*axis))
    for k in range(steps):
        t0, t1 = k / steps, (k + 1) / steps
        rr = r * math.sqrt(max(0.0, 1 - t0 * t0))
        disc(bone, "%s_%d" % (name, k), c + axis * (h * (t0 + t1) / 2), axis, rr, h / steps + 0.01, region)


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
    # tail dome closing the cloth around the shaft
    tail_end = zs(BALLOON_S[0])
    disc(balloon, "tail_dome_cap", v3(0, BY, tail_end - 0.02), (0, 0, 1), asp.balloon_radius(tail_end) + 0.06, 0.1, "brass")
    # nose: a rounded iron dome with a brass cap, the rod with its rings and ball
    front = zs(1.0)
    dome(balloon, "nose_dome", v3(0, BY, front - 0.36), (0, 0, 1), 0.62, 0.36, "iron")
    dome(balloon, "nose_cap", v3(0, BY, front - 0.06), (0, 0, 1), 0.34, 0.18, "brass", steps=2)
    ring(balloon, "nose_hub_ring", v3(0, BY, front - 0.3), (0, 0, 1), 0.64, 0.1, "gold", n=16, round_=True)
    # brass ribs on the blue cap, following the curve from a gold collar where the cream cloth begins to the hub
    zc = zs(NOSE_S)
    for k in range(8):
        az = 22.5 + 45 * k
        pts = [P(zs(s_), az, 0.07) for s_ in (NOSE_S, 0.76, 0.81, 0.855, 0.895, 0.93, 0.957, 0.975)]
        for j in range(len(pts) - 1):
            beam(balloon, "nose_rib_%d_%d" % (k, j), pts[j], pts[j + 1], 0.08, "brass", extend=0.04)
    ring(balloon, "nose_collar", v3(0, BY, zc), (0, 0, 1), asp.balloon_radius(zc) + 0.1, 0.16, "gold", n=24, round_=True)
    tube(balloon, "nose_rod", v3(0, BY, front - 0.2), v3(0, BY, asp.NOSE_ROD_Z), 0.14, "brass")
    for k, z in enumerate((front + 0.5, front + 1.2)):
        disc(balloon, "nose_rod_ring_%d" % k, v3(0, BY, z), (0, 0, 1), 0.14, 0.1, "gold")
    nb = v3(0, BY, asp.NOSE_ROD_Z)
    disc(balloon, "nose_ball", nb, (0, 0, 1), 0.14, 0.14, "gold")
    disc(balloon, "nose_ball_b", nb, (0, 1, 0), 0.12, 0.2, "gold", sides=8)
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
    # rope net: a transparent shell just outside the cloth
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
    # round braided rope hoops with gold clasps where they cross the bands
    for h, s in enumerate(HOOP_S):
        z = zs(s)
        r = asp.balloon_radius(z) + 0.18
        ring(balloon, "hoop_%d" % h, v3(0, BY, z), (0, 0, 1), r, 0.26, "rope", n=24, round_=True)
        for k, az in enumerate(BAND_AZ):
            p = P(z, az, 0.24)
            R = rz(-math.radians(az))
            add_cube(balloon, "clasp_%d_%d" % (h, k), p, R, (0.3, 0.16, 0.4), "gold")
            add_cube(balloon, "clasp_%d_%d_b" % (h, k), p - R[:, 1] * 0.02, R, (0.38, 0.1, 0.32), "gold")

    # ---------------------------------------------------------------- tail: curved lattice cone, shaft, propeller
    rear = zs(-asp.BALLOON_REAR_T)
    r0 = asp.balloon_radius(rear)
    zc0, zc1 = rear + 0.2, asp.TAIL_END_Z

    def cone_r(f):
        return 0.32 + (r0 + 0.02 - 0.32) * (1 - f) ** 1.4

    NC = 7
    cone = [(zc0 + (zc1 - zc0) * i / (NC - 1), cone_r(i / (NC - 1))) for i in range(NC)]
    for k in range(6):
        a = math.radians(60 * k + 30)
        d = v3(math.sin(a), math.cos(a), 0)
        pts = [v3(0, BY, rear + 0.3) + d * (r0 - 0.1)] + [v3(0, BY, z) + d * (r - 0.06) for z, r in cone[1:-1]] + \
              [v3(0, BY, asp.TAIL_END_Z) + d * 0.3]
        polyline(tail, "tail_spar_%d" % k, pts, 0.15, "band")
    for i in range(len(cone) - 1):
        (za, ra), (zb, rb) = cone[i], cone[i + 1]
        for j in range(16):
            a0, a1 = math.radians(22.5 * j), math.radians(22.5 * (j + 1))
            am = (a0 + a1) / 2
            pa0 = v3(math.sin(a0) * ra, BY + math.cos(a0) * ra, za)
            pa1 = v3(math.sin(a1) * ra, BY + math.cos(a1) * ra, za)
            pb0 = v3(math.sin(a0) * rb, BY + math.cos(a0) * rb, zb)
            pb1 = v3(math.sin(a1) * rb, BY + math.cos(a1) * rb, zb)
            c = panel(tail, "tail_net_%d_%d" % (i, j), pa0, pa1, pb0, pb1, 0.02, "net", v3(math.sin(am), math.cos(am), 0), overlap=1.0)
            for f in ("up", "down", "east", "west"):
                c.faces[f] = None
        if i in (2, 4):
            ring(tail, "tail_ring_%d" % i, v3(0, BY, za), (0, 0, 1), ra + 0.05, 0.1, "brass", n=12, round_=True)
    tube(tail, "shaft", v3(0, BY, rear + 1.0), v3(0, BY, asp.PROP_Z - 0.1), 0.24, "iron")
    sb = v3(0, BY, asp.TAIL_END_Z - 0.1)
    tube(tail, "shaft_bearing", sb + v3(0, 0, 0.25), sb - v3(0, 0, 0.25), 0.66, "brass", sides=12)
    ring(tail, "shaft_bearing_rim", sb + v3(0, 0, 0.22), (0, 0, 1), 0.34, 0.08, "gold", n=12, round_=True)
    prop = Bone("propeller", origin=(0, BY, asp.PROP_Z), parent=root)
    hub = v3(0, BY, asp.PROP_Z)
    tube(prop, "prop_hub", hub + v3(0, 0, 0.28), hub - v3(0, 0, 0.28), 0.66, "brass", sides=12)
    # pointed round spinner
    for j, (z0, z1, dd) in enumerate(((-0.28, -0.44, 0.5), (-0.44, -0.58, 0.36), (-0.58, -0.7, 0.2))):
        tube(prop, "prop_spinner_%d" % j, hub + v3(0, 0, z0), hub + v3(0, 0, z1), dd, "gold", sides=8)
    pitch = math.radians(20)
    for k in range(asp.PROP_BLADES):
        a = 2 * math.pi * k / asp.PROP_BLADES
        d = v3(math.sin(a), math.cos(a), 0)
        side = np.cross(v3(0, 0, 1), d)
        # pitch: the blade is turned about its own length
        w = side * math.cos(pitch) + v3(0, 0, 1) * math.sin(pitch)
        n = np.cross(d, w)
        axes = np.column_stack([d, w, n])
        # a wooden paddle: round shank from a brass sleeve, then an oval blade with a rounded tip
        tube(prop, "prop_shank_%d" % k, hub + d * 0.3, hub + d * 1.05, 0.2, "prop")
        add_cube(prop, "prop_sleeve_%d" % k, hub + d * 0.5, axes, (0.3, 0.32, 0.22), "brass")
        rs = [0.95, 1.15, 1.35, 1.55, 1.75, 1.95, 2.12, 2.26, 2.36, asp.PROP_R]
        for j in range(len(rs) - 1):
            r_a, r_b = rs[j], rs[j + 1]
            rm = (r_a + r_b) / 2
            t = (rm - 1.65) / 0.78
            wd = 0.24 + 0.46 * math.sqrt(max(0.0, 1 - t * t)) if rm < 1.65 else 0.7 * math.sqrt(max(0.0, 1 - t * t)) + 0.06
            add_cube(prop, "prop_blade_%d_%d" % (k, j), hub + d * rm, axes, (r_b - r_a + 0.02, wd, 0.1 - 0.004 * (j % 2)), "prop")
        add_cube(prop, "prop_blade_bolt_%d" % k, hub + d * 1.05 + n * 0.06, axes, (0.1, 0.1, 0.04), "brass")
    ring(prop, "prop_hub_ring", hub + v3(0, 0, 0.05), (0, 0, 1), 0.44, 0.09, "gold", n=14, round_=True)

    # ---------------------------------------------------------------- fins (swept, with curved edges)
    fin_tri = None
    fin_curve = None
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
        # the leading edge (C-A) and the trailing edge (C-B) are hollowed into curves (the texture follows)
        curves = []
        for k, (E0, E1, sag) in enumerate(((C, A, FIN_SAG_LEAD), (C, B, FIN_SAG_TRAIL))):
            e = E1 - E0
            other = B if k == 0 else A
            inward = norm(np.cross(nrm, e))
            if np.dot(inward, other - E0) < 0:
                inward = -inward
            curves.append((E0, e, inward, sag))
            pts = [E0 + e * t + inward * sag * math.sin(math.pi * t) for t in (j / 8 for j in range(9))]
            polyline(fb, "%s_spar_%d" % (name, k), pts, 0.13, "wood")
        if fin_curve is None:
            fin_curve = (C, A, B, curves)
        # a fan of ribs from the brass disc at the tip to the root along the balloon
        for k, f in enumerate((0.25, 0.5, 0.75)):
            p0 = P(asp.FIN_ROOT_Z[0] + (asp.FIN_ROOT_Z[1] - asp.FIN_ROOT_Z[0]) * f, az, -0.05)
            tube(fb, "%s_spar_%d" % (name, k + 2), p0, C, 0.08, "wood", extend=0.04)
        tube(fb, "%s_spar_5" % name, A, B, 0.1, "wood", extend=0.05)
        disc(fb, name + "_tip_disc", C, nrm, 0.28, 0.1, "brass")
        disc(fb, name + "_tip_boss", C, nrm, 0.12, 0.2, "gold", sides=8)
        for k, p in enumerate((A, B)):
            disc(fb, "%s_hinge_%d" % (name, k), p + rad * 0.12, nrm, 0.18, 0.12, "brass")

    # ---------------------------------------------------------------- gondola hull
    for side, sn in SIDES:
        for i in range(len(STATIONS) - 1):
            za, zb = STATIONS[i], STATIONS[i + 1]
            A_, B_ = section(za, side), section(zb, side)
            for k in range(len(A_) - 1):
                ko = k // SUB
                reg = STRAKES[ko]
                mid = (A_[k] + A_[k + 1] + B_[k] + B_[k + 1]) / 4
                outward = norm(v3(side, -0.7 if ko < 4 else 0.0, 0) + v3(0, 0, 0.35 * np.sign(mid[2])))
                board(gondola, "hull_%s%d_%d" % (sn, i, k), A_[k], A_[k + 1], B_[k], B_[k + 1], 0.1, reg, outward,
                      inner="hull_light" if ko >= 5 else None)
            # rounded gunwale: a flat plank capped by a round rail
            pa, pb = v3(side * hw(za), sheer(za) + 0.04, za), v3(side * hw(zb), sheer(zb) + 0.04, zb)
            beam(gondola, "gunwale_%s%d" % (sn, i), pa, pb, 0.08, "hull_light", width=0.28, extend=0.04)
            tube(gondola, "gunwale_cap_%s%d" % (sn, i), pa + v3(0, 0.07, 0), pb + v3(0, 0.07, 0), 0.16, "dark_wood", extend=0.05)
            for j, (f, reg, th) in enumerate(((0.62, "brass", 0.08), (0.3, "dark_wood", 0.1))):
                ya, yb = upper_y(za, f), upper_y(zb, f)
                qa, qb = v3(side * (outer_x(za, ya) + 0.04), ya, za), v3(side * (outer_x(zb, yb) + 0.04), yb, zb)
                if j == 0:
                    tube(gondola, "rub_%s%d_%d" % (sn, i, j), qa, qb, th, reg, extend=0.04)
                else:
                    beam(gondola, "rub_%s%d_%d" % (sn, i, j), qa, qb, th, reg, width=0.06, extend=0.04)
            if i % 2 == 0 and 1 < i < len(STATIONS) - 3:
                for k, y in enumerate((upper_y(za, 0.62) + 0.12, upper_y(za, 0.62) - 0.12)):
                    add_cube(gondola, "rivet_%s%d_%d" % (sn, i, k), v3(side * (outer_x(za, y) + 0.06), y, za), rz(math.pi / 4),
                             (0.06, 0.06, 0.06), "gold")
    for i in range(len(STATIONS) - 1):
        za, zb = STATIONS[i], STATIONS[i + 1]
        tube(gondola, "keel_%d" % i, (0, asp.keel_y(za) - 0.05, za), (0, asp.keel_y(zb) - 0.05, zb), 0.24, "dark_wood", extend=0.05)
    for k, z in enumerate((-4.8, -2.4, 0.0, 2.4, 4.8)):
        top, bot = asp.keel_y(z) + 0.05, max(asp.LOWEST_Y, asp.keel_y(z) - 0.3)
        # rounded skid: an octagonal block along the keel
        tube(gondola, "foot_%d" % k, (0, (top + bot) / 2, z - 0.35), (0, (top + bot) / 2, z + 0.35), max(0.4, top - bot), "dark_wood",
             phase=math.pi / 8)
    # stem and stern posts sweeping up in a curve past the rail and ending in a scroll, brass knob
    for s, tag in ((1, "stem"), (-1, "stern")):
        z0 = s * (asp.HALF_LENGTH + 0.2)
        top = sheer(z0) + 0.55
        p0 = v3(0, asp.keel_y(z0) - 0.05, z0)
        p2 = v3(0, top, z0 + s * 0.55)
        p1 = v3(0, (p0[1] + top) * 0.45, z0 + s * 0.85)
        pts = bezier(p0, p1, p2, 7)
        polyline(gondola, tag + "_post", pts, 0.28, "dark_wood")
        # the scroll: a shrinking spiral curling inboard and down from the head of the post
        rr = 0.22
        cs = p2 - v3(0, rr, 0)
        scroll = [cs + v3(0, math.sin(a) * rr * (1 - 0.09 * j), -s * math.cos(a) * rr * (1 - 0.09 * j))
                  for j, a in enumerate(math.pi / 2 + 0.7 * j for j in range(8))]
        polyline(gondola, tag + "_scroll", scroll, 0.17, "dark_wood")
        disc(gondola, tag + "_cap", cs, (1, 0, 0), 0.09, 0.32, "brass", sides=8)

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
            add_cube(deck, "bench_%s%d" % (sn, k), (x, main_y + 0.42, z), EYE, (0.46, 0.08, 1.3), {"all": "dark_wood", "+2": "wood"})
            for e in (1, -1):
                tube(deck, "bench_edge_%s%d_%d" % (sn, k, e > 0), (x + e * 0.23, main_y + 0.42, z - 0.65), (x + e * 0.23, main_y + 0.42, z + 0.65),
                     0.08, "wood")
            for dz in (-0.5, 0.5):
                add_cube(deck, "bench_leg_%s%d_%d" % (sn, k, dz > 0), (x, main_y + 0.19, z + dz), EYE, (0.4, 0.38, 0.08), "dark_wood")
    add_cube(deck, "bow_bench", (0, main_y + 0.42, asp.BOW_SEAT_Z), EYE, (1.4, 0.08, 0.46), {"all": "dark_wood", "+2": "wood"})
    for e in (1, -1):
        tube(deck, "bow_bench_edge_%d" % (e > 0), (-0.7, main_y + 0.42, asp.BOW_SEAT_Z + e * 0.23), (0.7, main_y + 0.42, asp.BOW_SEAT_Z + e * 0.23),
             0.08, "wood")
    for dx in (-0.5, 0.5):
        add_cube(deck, "bow_bench_leg_%d" % (dx > 0), (dx, main_y + 0.19, asp.BOW_SEAT_Z), EYE, (0.08, 0.38, 0.4), "dark_wood")
    # central round post up to the balloon, brass collars and a round brass plate with struts under the balloon
    bottom = BY - BR
    pz = asp.PILLAR_Z
    tube(deck, "pillar", (0, main_y, pz), (0, bottom + 0.3, pz), 0.55, "dark_wood", sides=12)
    for k, y in enumerate((main_y + 0.12, 2.6, bottom - 0.6)):
        tube(deck, "pillar_collar_%d" % k, (0, y - 0.09, pz), (0, y + 0.09, pz), 0.7, "brass", sides=12)
    disc(deck, "pillar_plate", (0, bottom - 0.05, pz), (0, 1, 0), 0.75, 0.14, "brass")
    for k, (dx, dz) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        tube(deck, "pillar_strut_%d" % k, (0, bottom - 1.3, pz), (dx * 0.6, bottom - 0.1, pz + dz * 0.6), 0.09, "brass")
    # helm: a small wheel on a round pedestal (bone helm_wheel turns with "steer")
    hz = asp.HELM_Z
    tube(deck, "helm_pedestal", (0, main_y, hz), (0, main_y + 0.9, hz), 0.28, "dark_wood")
    disc(deck, "helm_pedestal_cap", (0, main_y + 0.92, hz), (0, 1, 0), 0.2, 0.08, "brass")
    hc = v3(0, main_y + 1.12, hz - 0.2)
    wheel = Bone("helm_wheel", origin=tuple(hc), parent=deck)
    ring(wheel, "helm_rim", hc, (0, 0, 1), 0.42, 0.07, "brass", n=16, round_=True)
    for k in range(5):
        a = math.pi * k / 5
        d = v3(math.cos(a), math.sin(a), 0)
        tube(wheel, "helm_spoke_%d" % k, hc - d * 0.55, hc + d * 0.55, 0.05, "wood")
        for e in (1, -1):
            disc(wheel, "helm_handle_%d_%d" % (k, e > 0), hc + d * e * 0.55, d, 0.04, 0.08, "wood", sides=8)
    disc(wheel, "helm_hub", hc, (0, 0, 1), 0.08, 0.12, "brass")

    # ---------------------------------------------------------------- engine at the stern: a round riveted boiler
    ez0, ez1 = asp.ENGINE_Z
    ec = v3(0, main_y + 0.75, (ez0 + ez1) / 2)
    tube(engine, "boiler", v3(0, ec[1], ez0 + 0.08), v3(0, ec[1], ez1 - 0.08), 1.4, "boiler", sides=12)
    for e, zend in ((-1, ez0 + 0.08), (1, ez1 - 0.08)):
        dome(engine, "boiler_end_%d" % (e > 0), v3(0, ec[1], zend), (0, 0, e), 0.6, 0.12, "iron", steps=2)
    for k, z in enumerate((ez0 + 0.25, (ez0 + ez1) / 2, ez1 - 0.25)):
        tube(engine, "boiler_band_%d" % k, v3(0, ec[1], z - 0.05), v3(0, ec[1], z + 0.05), 1.48, "brass", sides=12)
    tube(engine, "boiler_dome", ec + v3(0, 0.55, 0.2), ec + v3(0, 0.86, 0.2), 0.6, "brass", sides=12)
    dome(engine, "boiler_dome_top", ec + v3(0, 0.86, 0.2), (0, 1, 0), 0.32, 0.16, "brass", steps=2)
    tube(engine, "boiler_saddle", v3(0, main_y + 0.02, ec[2]), v3(0, main_y + 0.16, ec[2]), 1.0, "dark_wood")
    add_cube(engine, "firebox_door", v3(0, ec[1] - 0.25, ez1 + 0.06), EYE, (0.46, 0.42, 0.04), "iron")
    add_cube(engine, "glow_firebox", v3(0, ec[1] - 0.28, ez1 + 0.085), EYE, (0.3, 0.12, 0.02), "glow")
    # gear wheels on the port side, meshed
    for k, (dz, dy, r) in enumerate(((0.0, 0.15, 0.62), (0.75, 0.75, 0.32))):
        gc = v3(0.74, main_y + 0.75 + dy, ec[2] + dz)
        disc(engine, "gear_%d" % k, gc, (1, 0, 0), r, 0.1, "brass")
        disc(engine, "gear_axle_%d" % k, gc + v3(0.06, 0, 0), (1, 0, 0), 0.1, 0.12, "iron", sides=8)
        for t in range(12 if k == 0 else 8):
            a = 2 * math.pi * t / (12 if k == 0 else 8)
            d = v3(0, math.cos(a), math.sin(a))
            add_cube(engine, "gear_tooth_%d_%d" % (k, t), gc + d * (r + 0.06), rx(-a), (0.1, 0.12, 0.1), "brass")
    # flywheel on the starboard side: a spoked wheel with a round gold rim on a brass bearing
    fc = v3(-0.82, main_y + 0.85, ec[2] - 0.1)
    ring(engine, "flywheel_rim", fc, (1, 0, 0), 0.6, 0.14, "gold", n=16, round_=True)
    for t in range(3):
        a = math.pi * t / 3
        d = v3(0, math.cos(a), math.sin(a))
        tube(engine, "flywheel_spoke_%d" % t, fc - d * 0.58, fc + d * 0.58, 0.07, "iron")
    disc(engine, "flywheel_bearing", fc + v3(0.08, 0, 0), (1, 0, 0), 0.13, 0.2, "brass")
    # curved round exhaust pipe: up from the boiler, bending back in a smooth arc, flared mouth facing aft
    ctrl = [v3(0, main_y + 1.3, ez0 + 0.45), v3(0, 3.0, ez0 + 0.45), v3(0, 3.9, ez0 + 0.4), v3(0, 4.45, ez0 + 0.15),
            v3(0, 4.75, ez0 - 0.3), v3(0, 4.85, ez0 - 0.8)]
    pts = catmull(ctrl, 2)
    polyline(engine, "exhaust", pts, 0.44, "brass", sides=8, extend=0.08)
    for k, p in enumerate((ctrl[1], ctrl[3])):
        i = min(range(len(pts)), key=lambda j: np.linalg.norm(pts[j] - p))
        d = norm(pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)])
        tube(engine, "exhaust_ring_%d" % k, p - d * 0.05, p + d * 0.05, 0.54, "iron", sides=8)
    m = pts[-1]
    tube(engine, "exhaust_mouth", m + v3(0, 0, -0.04), m + v3(0, 0, -0.18), 0.6, "brass", sides=12)
    tube(engine, "exhaust_lip", m + v3(0, 0, -0.18), m + v3(0, 0, -0.24), 0.7, "brass", sides=12)
    disc(engine, "exhaust_soot", m + v3(0, 0, -0.2), (0, 0, 1), 0.24, 0.1, "iron")

    # ---------------------------------------------------------------- suspension: round ropes, gold rings, chains
    att_s = HOOP_S[1:]
    for side, sn in SIDES:
        for k, s in enumerate(att_s):
            z = zs(s)
            top = P(z, side * 150, 0.2)
            zr = max(-asp.HALF_LENGTH + 1.0, min(asp.HALF_LENGTH - 1.0, z))
            rail = v3(side * hw(zr), sheer(zr) + 0.12, zr)
            dl = norm(top - rail)
            # braided line from the hoop down to a short chain of big gold links made fast to the rail
            tube(ropes, "line_%s%d" % (sn, k), top, rail + dl * 1.12, 0.22, "rope", extend=0.04)
            ring(ropes, "line_ring_%s%d" % (sn, k), rail + dl * 1.5, dl, 0.19, 0.08, "gold", n=8)
            p1 = norm(np.cross(dl, v3(0, 0, 1)))
            p2 = np.cross(dl, p1)
            for c in range(3):
                ring(ropes, "line_link_%s%d_%d" % (sn, k, c), rail + dl * (0.22 + 0.33 * c), p1 if c % 2 else p2, 0.17, 0.07,
                     "gold", n=6)
            disc(ropes, "line_clamp_%s%d" % (sn, k), rail, (0, 1, 0), 0.12, 0.14, "brass", sides=8)
            add_cube(ropes, "line_clasp_%s%d" % (sn, k), top, rz(-math.radians(side * 150)), (0.28, 0.14, 0.3), "gold")

    # ---------------------------------------------------------------- lanterns, anchor
    for side, sn in SIDES:
        z = -asp.HALF_LENGTH + 0.4
        base = v3(side * (hw(z) - 0.05), sheer(z) + 0.1, z)
        polyline(lanterns, "stern_lantern_bracket_" + sn, bezier(base, base + v3(side * 0.05, 0.4, -0.05), base + v3(side * 0.32, 0.38, -0.1), 3),
                 0.06, "brass")
        add_cube(lanterns, "stern_lantern_" + sn, base + v3(side * 0.32, 0.05, -0.1), EYE, (0.28, 0.4, 0.28),
                 {"all": "lantern", "+2": "brass", "-2": "brass"}, stretch=True)
    bz_ = asp.HALF_LENGTH - 0.6
    bb = v3(0, sheer(bz_) + 0.1, bz_)
    tube(lanterns, "bow_lantern_post", bb, bb + v3(0, 0.45, 0), 0.07, "brass")
    add_cube(lanterns, "bow_lantern", bb + v3(0, 0.68, 0), EYE, (0.26, 0.38, 0.26), {"all": "lantern", "+2": "brass", "-2": "brass"},
             stretch=True)
    # anchor hanging on a chain at the starboard quarter, clear of the ground under the keel
    az = -asp.HALF_LENGTH + 1.4
    ax_ = -(hw(az) + 0.22)
    top = v3(ax_, sheer(az) - 0.05, az)
    for c in range(5):
        add_cube(engine, "anchor_chain_%d" % c, top - v3(0, 0.12 + 0.2 * c, 0), ry(c * math.pi / 2), (0.05, 0.18, 0.1), "iron")
    shank_top = top - v3(0, 1.1, 0)
    tube(engine, "anchor_shank", shank_top, shank_top - v3(0, 0.7, 0), 0.1, "iron")
    tube(engine, "anchor_stock", shank_top + v3(0, -0.05, -0.3), shank_top + v3(0, -0.05, 0.3), 0.07, "iron")
    crown = shank_top - v3(0, 0.7, 0)
    for s in (1, -1):
        polyline(engine, "anchor_arm_%d" % (s > 0), bezier(crown, crown + v3(0, 0.0, s * 0.3), crown + v3(0, 0.32, s * 0.36), 3), 0.09, "iron")
    ring(engine, "anchor_ring", top - v3(0, 1.05, 0), (1, 0, 0), 0.07, 0.04, "gold", n=6)
    return root, fin_tri, fin_curve


FIN_SAG_LEAD, FIN_SAG_TRAIL = 0.45, 0.75


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
    root, fin_tri, fin_curve = build()
    anims = build_animations(root)
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    tex_path = os.path.join(tex_dir, "entity/steampunk_airship.png")
    at.make_texture(tex_path, fin_tri, fin_curve)
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
