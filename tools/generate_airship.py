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

On board (visual only, the walkway down the middle stays clear): inner frames with curved knees and
a shelf under the gunwale, a runner rug, a hatch grating, benches with buttoned leather cushions,
turned legs and padded backrests, a turned helm pedestal with a gear housing, a gauge column, an
engine telegraph and the pilot's stool, crates, a barrel, sacks, a rope coil, lanterns on the
pillar; at the boiler a glowing firebox with its door open, gauges, a water glass, twin cylinders
with piston and connecting rods, copper steam pipes and a valve, whistle, safety valve, coal
scuttle and shovel. Outside: a copper-sheathed bottom, brass-rimmed portholes, gilded scrolls and
beading, hanging sandbags, crow's feet spreading each suspension line over the hoop and the net.
Round instrument faces (gauges, portholes, telegraph) are painted discs in front of a brass rim.

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
STRAKES = ["copper_plate"] * 3 + ["hull", "hull", "hull", "hull_light"]   # copper-sheathed bottom
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


def face_frame(normal, up=(0, 1, 0)):
    """Axes (right, up, normal) of a flat part facing along normal."""
    n = norm(v3(*normal))
    up = v3(*up)
    if abs(np.dot(up, n)) > 0.95:
        up = v3(0, 0, 1)
    u = norm(up - np.dot(up, n) * n)
    return np.column_stack([np.cross(u, n), u, n])


def dial(bone, name, c, normal, r, face="gauge", rim="brass", depth=0.06, sides=12):
    """Round instrument (gauge, porthole...): a brass rim (thin regular prism) with a painted round
    face just in front of it (the region is drawn whole, transparent outside the circle)."""
    n = norm(v3(*normal))
    c = v3(*c)
    disc(bone, name + "_rim", c, n, r, depth, rim, sides=sides)
    add_cube(bone, name, c + n * (depth / 2 + 0.03), face_frame(n), (1.9 * r, 1.9 * r, 0.012), {"all": None, "+3": face, "-3": face},
             stretch=True)


def handwheel(bone, name, c, axis, r, region="brass", spokes=2):
    """Small valve handwheel: a ring of bars and crossed spokes."""
    axis = norm(v3(*axis))
    c = v3(*c)
    ring(bone, name + "_rim", c, axis, r, 0.035, region, n=8)
    e1 = norm(np.cross(axis, v3(0, 1, 0) if abs(axis[1]) < 0.9 else v3(1, 0, 0)))
    e2 = np.cross(axis, e1)
    for k in range(spokes):
        a = math.pi * k / spokes
        d = e1 * math.cos(a) + e2 * math.sin(a)
        beam(bone, "%s_spoke_%d" % (name, k), c - d * r, c + d * r, 0.025, region)
    disc(bone, name + "_hub", c, axis, 0.035, 0.05, "gold", sides=8)


def hull_pt(z, y, side, out=0.0):
    """Point on the outside of the gondola planking (out: distance along the outward normal)."""
    e = 0.05
    dw = (outer_x(z + e, y) - outer_x(z - e, y)) / (2 * e)
    n = norm(v3(side, 0, -dw))
    return v3(side * outer_x(z, y), y, z) + n * out, n


def hull_curve(bone, name, pts2, side, th, wd, region, out=0.03):
    """Flat moulding (gilded scroll...) laid on the planking along (z, y) points."""
    P3 = [hull_pt(z, y, side, out + th / 2) for z, y in pts2]
    for k in range(len(P3) - 1):
        (p0, n0), (p1, n1) = P3[k], P3[k + 1]
        beam(bone, "%s_%d" % (name, k), p0, p1, th, region, width=wd, up=norm(n0 + n1), extend=wd * 0.45)


def scroll_pts(zc, yc, r0, turns, direction, tail, m=14, a0=math.pi / 2):
    """A spiral curling inwards from radius r0 around (zc, yc), starting at angle a0, preceded by a
    sweeping tail [(z, y), ...] ending at the start of the spiral; direction = +1 / -1 sense of turn."""
    spiral = []
    for j in range(m + 1):
        t = j / m
        a = a0 + direction * 2 * math.pi * turns * t
        r = r0 * (1 - 0.78 * t)
        spiral.append((zc + math.cos(a) * r, yc + math.sin(a) * r))
    return list(tail) + spiral


def turned_leg(bone, name, p0, p1, d, region="dark_wood"):
    """Turned wooden leg: a hexagonal bar with a small bulb near the top and a round foot."""
    p0, p1 = v3(*p0), v3(*p1)
    tube(bone, name, p0, p1, d, region)
    u = norm(p1 - p0)
    L = np.linalg.norm(p1 - p0)
    tube(bone, name + "_bulb", p0 + u * (L * 0.62), p0 + u * (L * 0.78), d * 1.5, region, sides=8)
    tube(bone, name + "_foot", p0, p0 + u * 0.05, d * 1.4, "brass", sides=8)


def lantern(bone, name, c, w, h, bail=True):
    """Ship's lantern centred on c: glowing glass between four brass corner posts, a stepped brass
    foot, a stepped octagonal roof with a gold finial and, when hung, a bail ring on top."""
    c = v3(*c)
    up = v3(0, 1, 0)
    add_cube(bone, name, c, EYE, (w * 0.86, h, w * 0.86), {"all": "lantern", "+2": None, "-2": None}, stretch=True)
    for k, (ex, ez) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        q = c + v3(ex * w * 0.44, 0, ez * w * 0.44)
        tube(bone, "%s_post_%d" % (name, k), q - up * (h / 2 + 0.01), q + up * (h / 2 + 0.01), 0.04, "brass", sides=4)
    yb, yt = c[1] - h / 2, c[1] + h / 2
    disc(bone, name + "_foot", v3(c[0], yb - 0.025, c[2]), up, w * 0.6, 0.05, "brass", sides=8, phase=math.pi / 8)
    disc(bone, name + "_foot_b", v3(c[0], yb - 0.07, c[2]), up, w * 0.36, 0.05, "gold", sides=8, phase=math.pi / 8)
    for k, (dy, r, t) in enumerate(((0.025, 0.66, 0.05), (0.075, 0.5, 0.05), (0.12, 0.34, 0.05))):
        disc(bone, "%s_roof_%d" % (name, k), v3(c[0], yt + dy, c[2]), up, w * r, t, "brass", sides=8, phase=math.pi / 8)
    disc(bone, name + "_finial", v3(c[0], yt + 0.17, c[2]), up, max(0.035, w * 0.14), 0.07, "gold", sides=8)
    if bail:
        ring(bone, name + "_bail", v3(c[0], yt + 0.25, c[2]), (1, 0, 0), 0.06, 0.025, "brass", n=6)


def blade_width(r):
    """Width of a propeller blade at radius r: narrow at the shank, widest at 1.7, round tip."""
    if r < 1.7:
        t = (1.7 - r) / 0.75
        return 0.22 + 0.5 * math.sqrt(max(0.0, 1 - t * t))
    t = (r - 1.7) / (asp.PROP_R - 1.7 + 0.02)
    return 0.72 * math.sqrt(max(0.0, 1 - t * t)) + 0.04


def blade_sweep(r):
    return 0.22 * ((r - 0.95) / (asp.PROP_R - 0.95)) ** 2


def blade_axes(d, side, r):
    """Frame (along, chord, normal) of a blade at radius r: swept back and twisted (34 to 14 degrees)."""
    pitch = math.radians(34 - 20 * (r - 0.95) / (asp.PROP_R - 0.95))
    dr = 0.01
    along = norm(d * 2 * dr + side * (blade_sweep(r + dr) - blade_sweep(r - dr)))
    sd = norm(side - np.dot(side, along) * along)
    w = sd * math.cos(pitch) + v3(0, 0, 1) * math.sin(pitch)
    return np.column_stack([along, w, np.cross(along, w)])


def blade_point(hub, d, side, r):
    return hub + d * r + side * blade_sweep(r), blade_axes(d, side, r)


def bench(deck, name, c, along, inward, length, back=True):
    """Bench seat at c (top of the plank at c.y + 0.46) with a buttoned leather cushion, turned legs
    and, against the hull, a curved backrest with a padded leather back."""
    along, inward = norm(v3(*along)), norm(v3(*inward))
    up = v3(0, 1, 0)
    axes = np.column_stack([inward, up, along])
    c = v3(*c)
    seat_y = c[1] + 0.42
    add_cube(deck, name, v3(c[0], seat_y, c[2]), axes, (0.46, 0.08, length), {"all": "dark_wood", "+2": "wood"})
    for e in (1, -1):
        tube(deck, "%s_edge_%d" % (name, e > 0), v3(c[0], seat_y, c[2]) + inward * e * 0.23 - along * length / 2,
             v3(c[0], seat_y, c[2]) + inward * e * 0.23 + along * length / 2, 0.08, "wood")
    cy = seat_y + 0.04 + 0.04
    add_cube(deck, name + "_cushion", v3(c[0], cy, c[2]), axes, (0.38, 0.08, length - 0.12), "leather")
    add_cube(deck, name + "_cushion_top", v3(c[0], cy + 0.045, c[2]), axes, (0.3, 0.02, length - 0.2), "leather")
    for e in (1, -1):
        tube(deck, "%s_piping_%d" % (name, e > 0), v3(c[0], cy + 0.035, c[2]) + inward * e * 0.17 - along * (length / 2 - 0.08),
             v3(c[0], cy + 0.035, c[2]) + inward * e * 0.17 + along * (length / 2 - 0.08), 0.04, "leather_dark", sides=4)
    legs = []
    for ea in (1, -1):
        for ei in (1, -1):
            p = v3(c[0], c[1], c[2]) + along * ea * (length / 2 - 0.16) + inward * ei * 0.15
            turned_leg(deck, "%s_leg_%d%d" % (name, ea > 0, ei > 0), p, p + up * 0.38, 0.07)
            legs.append(p)
    for ei in (1, -1):
        p = v3(c[0], c[1] + 0.12, c[2]) + inward * ei * 0.15
        tube(deck, "%s_stretcher_%d" % (name, ei > 0), p - along * (length / 2 - 0.16), p + along * (length / 2 - 0.16), 0.045,
             "dark_wood", sides=4)
    if not back:
        return
    # backrest: two curved posts sweeping back from the outer edge, a round top rail and a leather pad
    out = -inward
    for ea in (1, -1):
        b0 = v3(c[0], seat_y, c[2]) + out * 0.2 + along * ea * (length / 2 - 0.1)
        pts = bezier(b0, b0 + up * 0.3 + out * 0.02, b0 + up * 0.55 + out * 0.09, 3)
        polyline(deck, "%s_back_post_%d" % (name, ea > 0), pts, 0.07, "dark_wood")
    t0 = v3(c[0], seat_y + 0.55, c[2]) + out * 0.29
    tube(deck, name + "_back_rail", t0 - along * (length / 2 - 0.02), t0 + along * (length / 2 - 0.02), 0.09, "dark_wood")
    for ea in (1, -1):
        disc(deck, "%s_back_knob_%d" % (name, ea > 0), t0 + along * ea * (length / 2 + 0.02), along, 0.06, 0.05, "brass", sides=8)
    a0 = v3(c[0], seat_y + 0.12, c[2]) + out * 0.22
    a1 = v3(c[0], seat_y + 0.48, c[2]) + out * 0.27
    board(deck, name + "_back_pad", a0 - along * (length / 2 - 0.16), a1 - along * (length / 2 - 0.16),
          a0 + along * (length / 2 - 0.16), a1 + along * (length / 2 - 0.16), 0.06, "leather", inward, overlap=1.0)


def benches(deck, main_y):
    for z in asp.BENCH_Z:
        for side, sn in SIDES:
            bench(deck, "bench_%s%d" % (sn, asp.BENCH_Z.index(z)), (side * 1.05, main_y, z), (0, 0, 1), (-side, 0, 0), 1.3)
    bench(deck, "bow_bench", (0, main_y, asp.BOW_SEAT_Z), (1, 0, 0), (0, 0, -1), 1.4, back=False)


def helm(deck, main_y):
    """Steering post: a turned pedestal with a brass gear housing, the wheel (bone helm_wheel), an
    instrument column with two gauges to starboard and an engine telegraph to port, the pilot's stool."""
    hz = asp.HELM_Z
    up = v3(0, 1, 0)
    disc(deck, "helm_base", (0, main_y + 0.03, hz), up, 0.27, 0.06, "brass")
    disc(deck, "helm_plinth", (0, main_y + 0.12, hz), up, 0.2, 0.12, "dark_wood")
    tube(deck, "helm_pedestal", (0, main_y + 0.16, hz), (0, main_y + 1.0, hz), 0.22, "dark_wood", sides=8)
    for k, (y, d) in enumerate(((0.32, 0.3), (0.62, 0.28), (0.9, 0.3))):
        tube(deck, "helm_pedestal_ring_%d" % k, (0, main_y + y - 0.03, hz), (0, main_y + y + 0.03, hz), d, "brass", sides=8)
    hc = v3(0, main_y + 1.12, hz - 0.2)
    # gear housing on top of the pedestal, carrying the wheel shaft
    tube(deck, "helm_housing", (0, hc[1], hz + 0.16), (0, hc[1], hz - 0.1), 0.34, "brass", sides=12)
    disc(deck, "helm_housing_cap", (0, hc[1], hz + 0.17), (0, 0, 1), 0.12, 0.04, "gold", sides=8)
    tube(deck, "helm_housing_foot", (0, main_y + 0.98, hz), (0, hc[1] - 0.1, hz), 0.18, "brass", sides=8)
    tube(deck, "helm_shaft", (0, hc[1], hz - 0.1), hc + v3(0, 0, 0.02), 0.07, "iron", sides=8)
    wheel = Bone("helm_wheel", origin=tuple(hc), parent=deck)
    ring(wheel, "helm_rim", hc, (0, 0, 1), 0.42, 0.07, "brass", n=16, round_=True)
    ring(wheel, "helm_rim_in", hc + v3(0, 0, 0.005), (0, 0, 1), 0.36, 0.045, "wood", n=16, phase=math.pi / 16)
    for k in range(5):
        a = math.pi * k / 5
        d = v3(math.cos(a), math.sin(a), 0)
        tube(wheel, "helm_spoke_%d" % k, hc - d * 0.42, hc + d * 0.42, 0.05, "wood")
        for e in (1, -1):
            tube(wheel, "helm_handle_%d_%d" % (k, e > 0), hc + d * e * 0.45, hc + d * e * 0.6, 0.055, "wood")
            disc(wheel, "helm_knob_%d_%d" % (k, e > 0), hc + d * e * 0.62, d, 0.045, 0.05, "wood", sides=8)
    disc(wheel, "helm_hub", hc, (0, 0, 1), 0.11, 0.12, "brass")
    disc(wheel, "helm_hub_cap", hc - v3(0, 0, 0.07), (0, 0, 1), 0.06, 0.04, "gold", sides=8)
    # instrument column (starboard): two gauges facing the pilot
    ix, iz = -0.66, hz + 0.05
    disc(deck, "gauge_column_base", (ix, main_y + 0.03, iz), up, 0.16, 0.06, "brass", sides=8)
    tube(deck, "gauge_column", (ix, main_y, iz), (ix, main_y + 1.05, iz), 0.1, "brass", sides=8)
    tube(deck, "gauge_column_arm", (ix, main_y + 1.05, iz), (ix + 0.12, main_y + 1.05, iz), 0.07, "brass", sides=4)
    for k, (dx, y, r) in enumerate(((0.0, 1.2, 0.1), (0.0, 0.9, 0.08))):
        dial(deck, "gauge_helm_%d" % k, (ix + dx, main_y + y, iz - 0.02), (0, 0, -1), r, depth=0.04)
    tube(deck, "speaking_tube", (ix, main_y + 1.36, iz), (ix, main_y + 1.48, iz - 0.05), 0.06, "copper", sides=6)
    tube(deck, "speaking_tube_mouth", (ix, main_y + 1.48, iz - 0.05), (ix, main_y + 1.52, iz - 0.16), 0.13, "brass", sides=8)
    # engine order telegraph (port): a round dial head on a column, with a lever
    tx, tz = 0.66, hz + 0.05
    disc(deck, "telegraph_base", (tx, main_y + 0.03, tz), up, 0.18, 0.06, "brass", sides=8)
    tube(deck, "telegraph_column", (tx, main_y, tz), (tx, main_y + 0.95, tz), 0.14, "brass", sides=8)
    tube(deck, "telegraph_collar", (tx, main_y + 0.5, tz), (tx, main_y + 0.56, tz), 0.2, "gold", sides=8)
    th = v3(tx, main_y + 1.12, tz)
    tube(deck, "telegraph_head", th + v3(0, 0, 0.06), th - v3(0, 0, 0.06), 0.34, "brass", sides=12)
    for e in (1, -1):
        add_cube(deck, "telegraph_face_%d" % (e > 0), th + v3(0, 0, e * 0.09), EYE, (0.3, 0.3, 0.01),
                 {"all": None, "+3": "telegraph", "-3": "telegraph"}, stretch=True)
    lever_top = th + v3(-0.05, 0.3, -0.12)
    tube(deck, "telegraph_lever", th - v3(0, 0, 0.1), lever_top, 0.04, "iron", sides=4)
    disc(deck, "telegraph_grip", lever_top, (0, 1, 0), 0.04, 0.1, "wood", sides=8)
    disc(deck, "telegraph_cap", th + v3(0, 0.22, 0), (0, 1, 0), 0.06, 0.04, "gold", sides=8)
    # pilot's stool: a round leather seat on a brass post
    sz = asp.PILOT_Z
    disc(deck, "stool_base", (0, main_y + 0.025, sz), up, 0.24, 0.05, "brass")
    tube(deck, "stool_post", (0, main_y, sz), (0, main_y + 0.6, sz), 0.1, "brass", sides=8)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        d = v3(math.cos(a), 0, math.sin(a))
        tube(deck, "stool_leg_%d" % k, v3(0, main_y + 0.3, sz) + d * 0.04, v3(0, main_y + 0.03, sz) + d * 0.22, 0.05, "brass", sides=4)
    disc(deck, "stool_seat", (0, main_y + 0.63, sz), up, 0.24, 0.07, "dark_wood")
    disc(deck, "stool_cushion", (0, main_y + 0.69, sz), up, 0.22, 0.06, "leather")
    disc(deck, "stool_cushion_top", (0, main_y + 0.73, sz), up, 0.15, 0.03, "leather")


def engine_room(engine, ec, main_y):
    """Boiler front (firebox with a glowing grate and an open door, gauges, water glass), twin
    cylinders on top with copper steam pipes, piston and connecting rods to the gear and the flywheel,
    a whistle, a coal scuttle and a shovel."""
    ez0, ez1 = asp.ENGINE_Z
    fz = ez1 - 0.04 + 0.02     # front face of the boiler end
    # firebox: an iron frame with a brass rim around the glowing grate, the door swung open
    fy = ec[1] - 0.27
    add_cube(engine, "firebox_plate", v3(0, fy, fz + 0.02), EYE, (0.6, 0.4, 0.05), "iron")
    for k, (a, b) in enumerate((((-0.3, -0.2), (0.3, -0.2)), ((0.3, 0.2), (-0.3, 0.2)), ((-0.3, -0.2), (-0.3, 0.2)), ((0.3, -0.2), (0.3, 0.2)))):
        beam(engine, "firebox_rim_%d" % k, v3(a[0], fy + a[1], fz + 0.055), v3(b[0], fy + b[1], fz + 0.055), 0.05, "brass",
             width=0.04, up=v3(0, 0, 1), extend=0.025)
    add_cube(engine, "glow_firebox", v3(0, fy + 0.01, fz + 0.048), EYE, (0.44, 0.26, 0.012), {"all": None, "+3": "fire", "-3": "fire"},
             stretch=True)
    hinge = v3(0.25, fy + 0.01, fz + 0.07)
    tube(engine, "firebox_hinge", hinge - v3(0, 0.14, 0), hinge + v3(0, 0.14, 0), 0.04, "brass", sides=4)
    op = math.radians(115)
    dd = v3(-math.cos(op), 0, math.sin(op))
    dax = np.column_stack([dd, v3(0, 1, 0), np.cross(dd, v3(0, 1, 0))])
    add_cube(engine, "firebox_door", hinge + dd * 0.23, dax, (0.44, 0.27, 0.035), {"all": "iron", "+3": "boiler_door", "-3": "boiler_door"},
             stretch=True)
    disc(engine, "firebox_door_handle", hinge + dd * 0.4 + np.cross(dd, v3(0, 1, 0)) * 0.035, np.cross(dd, v3(0, 1, 0)), 0.035, 0.05,
         "brass", sides=8)
    # ash pan with its slotted damper
    add_cube(engine, "ashpan", v3(0, main_y + 0.17, fz + 0.03), EYE, (0.5, 0.1, 0.07), {"all": "iron", "+3": "grate", "-3": "grate"},
             stretch=True)
    # gauges and water glass
    for k, x in enumerate((-0.24, 0.24)):
        dial(engine, "gauge_boiler_%d" % k, (x, ec[1] + 0.27, fz + 0.03), (0, 0, 1), 0.12)
        polyline(engine, "gauge_pipe_%d" % k, [v3(x, ec[1] + 0.39, fz + 0.03), v3(x, ec[1] + 0.5, fz + 0.0), v3(x * 0.6, ec[1] + 0.56, fz - 0.12)],
                 0.035, "copper", sides=4)
    gx = 0.0
    for k, y in enumerate((ec[1] - 0.02, ec[1] + 0.13)):
        disc(engine, "water_glass_fitting_%d" % k, (gx, y, fz + 0.04), (0, 1, 0), 0.045, 0.05, "brass", sides=8)
    add_cube(engine, "water_glass", v3(gx, ec[1] + 0.055, fz + 0.04), EYE, (0.05, 0.12, 0.05), "glass", stretch=True)
    # twin cylinders on the boiler, with piston rods, crossheads and connecting rods
    cz = ez0 + 0.6
    for side, sn in SIDES:
        x = side * 0.42
        top_y = ec[1] + math.sqrt(0.7 ** 2 - x ** 2) - 0.08
        tube(engine, "cylinder_" + sn, v3(x, top_y, cz), v3(x, top_y + 0.55, cz), 0.3, "copper", sides=8)
        for k, y in enumerate((top_y + 0.02, top_y + 0.56)):
            disc(engine, "cylinder_cap_%s%d" % (sn, k), v3(x, y, cz), (0, 1, 0), 0.19, 0.05, "brass", sides=8)
        for k in range(4):
            a = math.pi / 4 + math.pi / 2 * k
            add_cube(engine, "cylinder_bolt_%s%d" % (sn, k), v3(x + math.cos(a) * 0.16, top_y + 0.59, cz + math.sin(a) * 0.16), EYE,
                     (0.035, 0.03, 0.035), "gold")
        rod_top = v3(x, top_y + 0.85, cz)
        tube(engine, "piston_rod_" + sn, v3(x, top_y + 0.58, cz), rod_top, 0.05, "iron", sides=4)
        add_cube(engine, "crosshead_" + sn, rod_top, EYE, (0.1, 0.08, 0.1), "brass")
        # guide bars on either side of the crosshead
        for e in (1, -1):
            tube(engine, "guide_%s%d" % (sn, e > 0), v3(x, top_y + 0.58, cz + e * 0.07), v3(x, top_y + 0.95, cz + e * 0.07), 0.03,
                 "iron", sides=4)
        crank = v3(0.84, ec[1] + 0.5, ec[2] + 0.22) if side > 0 else v3(-0.78, ec[1] + 0.42, ec[2] + 0.5)
        tube(engine, "conrod_" + sn, rod_top, crank, 0.06, "iron", sides=6)
        disc(engine, "crank_pin_" + sn, crank, (1, 0, 0), 0.05, 0.1, "brass", sides=8)
    # steam pipes from the dome to the cylinders, with a stop valve
    dt = ec + v3(0, 1.02, 0.2)
    tube(engine, "steam_riser", dt - v3(0, 0.06, 0), dt + v3(0, 0.22, 0), 0.1, "copper", sides=6)
    handwheel(engine, "steam_valve", dt + v3(0, 0.27, 0), (0, 1, 0), 0.1)
    for side, sn in SIDES:
        x = side * 0.42
        top_y = ec[1] + math.sqrt(0.7 ** 2 - x ** 2) - 0.08
        pts = catmull([dt + v3(0, 0.14, 0), v3(side * 0.22, dt[1] + 0.14, dt[2] - 0.05), v3(x, top_y + 0.42, cz + 0.2),
                       v3(x, top_y + 0.42, cz + 0.13)], 2)
        polyline(engine, "steam_pipe_" + sn, pts, 0.08, "copper", sides=6, extend=0.03)
    # whistle and safety valve on the boiler top, forward of the dome
    wb = v3(-0.22, ec[1] + 0.66, ez1 - 0.2)
    tube(engine, "whistle_pipe", wb, wb + v3(0, 0.36, 0), 0.05, "brass", sides=4)
    tube(engine, "whistle_bell", wb + v3(0, 0.36, 0), wb + v3(0, 0.56, 0), 0.11, "brass", sides=8)
    disc(engine, "whistle_cap", wb + v3(0, 0.58, 0), (0, 1, 0), 0.07, 0.04, "gold", sides=8)
    beam(engine, "whistle_cord", wb + v3(0, 0.3, 0), wb + v3(0.15, 0.32, 0.25), 0.015, "rope")
    sv = v3(0.22, ec[1] + 0.66, ez1 - 0.2)
    tube(engine, "safety_valve", sv, sv + v3(0, 0.2, 0), 0.09, "brass", sides=8)
    beam(engine, "safety_valve_lever", sv + v3(0, 0.2, 0), sv + v3(0, 0.24, 0.3), 0.03, "iron")
    disc(engine, "safety_valve_weight", sv + v3(0, 0.2, 0.3), (0, 1, 0), 0.05, 0.08, "iron", sides=8)
    # coal scuttle and shovel by the firebox
    sc = v3(-0.86, main_y, ez1 + 0.32)
    tube(engine, "coal_scuttle", sc, sc + v3(0, 0.3, 0), 0.34, "copper", sides=8)
    tube(engine, "coal_scuttle_rim", sc + v3(0, 0.27, 0), sc + v3(0, 0.31, 0), 0.38, "brass", sides=8)
    disc(engine, "coal_heap", sc + v3(0, 0.3, 0), (0, 1, 0), 0.15, 0.06, "coal", sides=8)
    add_cube(engine, "coal_lump", sc + v3(0.04, 0.35, -0.03), ry(0.5) @ rx(0.4), (0.09, 0.07, 0.08), "coal")
    polyline(engine, "coal_scuttle_handle", bezier(sc + v3(-0.17, 0.3, 0), sc + v3(0, 0.62, 0), sc + v3(0.17, 0.3, 0), 4), 0.03, "brass",
             sides=4)
    s0, s1 = v3(0.86, main_y + 0.04, ez1 + 0.42), v3(0.62, main_y + 0.98, ez1 + 0.18)
    tube(engine, "shovel_shaft", s0 + norm(s1 - s0) * 0.2, s1, 0.05, "wood", sides=6)
    beam(engine, "shovel_grip", s1, s1 + v3(0.08, 0, -0.08), 0.04, "dark_wood", extend=0.04)
    ds = norm(s1 - s0)
    sax = np.column_stack([np.cross(ds, v3(0.7, 0, 0.7)), ds, v3(0.7, 0, 0.7)])
    add_cube(engine, "shovel_blade", s0 + ds * 0.1, sax, (0.2, 0.24, 0.02), "iron")


def outfit(gondola, deck, engine, lanterns, ropes, main_y):
    """Details of the gondola: inner frames and shelf, a runner rug, a hatch grating, crates and a barrel,
    hanging lanterns on the pillar, portholes, gilded scrolls and a gold beading on the hull, sandbags."""
    # ---- inner frames (ribs with a curved knee onto the deck) and a shelf plank under the gunwale
    for z in (-4.4, -3.0, -1.8, -0.2, 2.1, 4.2, 5.0):
        for side, sn in SIDES:
            top = sheer(z) - 0.2
            pts = []
            for y in (top, top * 0.6 + 0.08, 0.32):
                pts.append(v3(side * (outer_x(z, y) - 0.15), y, z))
            xin = outer_x(z, 0.2) - 0.15
            pts += [v3(side * (xin - 0.04), 0.13, z), v3(side * (xin - 0.22), main_y + 0.04, z)]
            for k in range(len(pts) - 1):
                beam(gondola, "frame_%s%d_%d" % (sn, int(z * 10 + 100), k), pts[k], pts[k + 1], 0.08, "dark_wood", width=0.1,
                     up=v3(0, 0, 1), extend=0.035)
    for side, sn in SIDES:
        zz = [z for z in STATIONS if -6.4 <= z <= 6.4]
        for i in range(len(zz) - 1):
            pa = v3(side * (outer_x(zz[i], sheer(zz[i]) - 0.12) - 0.15), sheer(zz[i]) - 0.12, zz[i])
            pb = v3(side * (outer_x(zz[i + 1], sheer(zz[i + 1]) - 0.12) - 0.15), sheer(zz[i + 1]) - 0.12, zz[i + 1])
            beam(gondola, "shelf_%s%d" % (sn, i), pa, pb, 0.1, "dark_wood", width=0.08, extend=0.04)
    # ---- runner rug down the middle of the deck (in tiles, so the pattern repeats), gold end bars
    for k, (za, zb, nt) in enumerate(((-3.2, -1.55, 2), (-0.65, 3.85, 4))):
        for t in range(nt):
            z0 = za + (zb - za) * t / nt
            z1 = za + (zb - za) * (t + 1) / nt
            add_cube(deck, "rug_%d_%d" % (k, t), (0, main_y + 0.012, (z0 + z1) / 2), EYE, (0.72, 0.024, z1 - z0 + 0.002),
                     {"all": "rug_edge", "+2": "rug"}, stretch=True)
        for e, zz in enumerate((za, zb)):
            tube(deck, "rug_bar_%d_%d" % (k, e), (-0.38, main_y + 0.025, zz), (0.38, main_y + 0.025, zz), 0.04, "gold", sides=4)
    # ---- hatch grating before the bow seat
    gz = 4.62
    add_cube(deck, "hatch_grating", (0, main_y + 0.012, gz), EYE, (0.7, 0.024, 0.62), {"all": "dark_wood", "+2": "grate"}, stretch=True)
    for k, (a, b) in enumerate((((-0.38, -0.34), (0.38, -0.34)), ((-0.38, 0.34), (0.38, 0.34)), ((-0.38, -0.34), (-0.38, 0.34)),
                                ((0.38, -0.34), (0.38, 0.34)))):
        beam(deck, "hatch_coaming_%d" % k, (a[0], main_y + 0.03, gz + a[1]), (b[0], main_y + 0.03, gz + b[1]), 0.06, "wood", width=0.07,
             extend=0.035)
    for e in (1, -1):
        ring(deck, "hatch_ring_%d" % (e > 0), v3(e * 0.2, main_y + 0.03, gz), (0, 1, 0), 0.05, 0.02, "brass", n=6)
    # ---- crates and a barrel between the pillar and the helm, against the sides
    cz = -2.35
    for k, (x, y, s, a) in enumerate(((1.12, 0.0, 0.5, 0.12), (1.1, 0.5, 0.36, -0.2))):
        c = v3(x, main_y + y + s / 2, cz + (0.05 if k else 0.0))
        R = ry(a)
        add_cube(deck, "crate_%d" % k, c, R, (s, s, s), "crate", stretch=True)
        for e in (1, -1):
            for f in (1, -1):
                # iron corner straps along the vertical edges
                add_cube(deck, "crate_strap_%d_%d%d" % (k, e > 0, f > 0), c + R @ v3(e * s / 2, 0, f * s / 2), R, (0.04, s + 0.01, 0.04),
                         "iron")
    bc = v3(-1.12, main_y, cz)
    for j, (y0, y1, d) in enumerate(((0.0, 0.12, 0.44), (0.12, 0.5, 0.5), (0.5, 0.62, 0.44))):
        tube(deck, "barrel_%d" % j, bc + v3(0, y0, 0), bc + v3(0, y1, 0), d, "barrel", sides=12, phase=0.13)
    for j, y in enumerate((0.12, 0.5)):
        tube(deck, "barrel_hoop_%d" % j, bc + v3(0, y - 0.025, 0), bc + v3(0, y + 0.025, 0), 0.53, "iron", sides=12, phase=0.13)
    disc(deck, "barrel_lid", bc + v3(0, 0.62, 0), (0, 1, 0), 0.19, 0.02, "end_grain", phase=0.13)
    disc(deck, "barrel_bung", bc + v3(0.06, 0.64, 0.05), (0, 1, 0), 0.03, 0.03, "brass", sides=8)
    # sacks of ballast sand and a coil of rope by the bow bench
    for k, (x, z, a) in enumerate(((0.55, 5.95, 0.3), (-0.55, 5.95, -0.4))):
        sc = v3(x, main_y + 0.13, z)
        add_cube(deck, "sack_%d" % k, sc, ry(a), (0.3, 0.22, 0.24), "burlap")
        add_cube(deck, "sack_top_%d" % k, sc + v3(0, 0.13, 0), ry(a + 0.3), (0.2, 0.06, 0.16), "burlap")
        add_cube(deck, "sack_neck_%d" % k, sc + v3(0, 0.19, 0), ry(a), (0.07, 0.08, 0.07), "rope")
    rc = v3(-1.2, main_y, -0.62)
    for j in range(3):
        ring(deck, "rope_coil_%d" % j, rc + v3(0, 0.04 + 0.06 * j, 0), (0, 1, 0), 0.22 - 0.035 * j, 0.07, "rope", n=8, phase=0.3 * j)
    # ---- lanterns hanging from the pillar on curled brass brackets
    pz = asp.PILLAR_Z
    for side, sn in SIDES:
        b0 = v3(side * 0.26, 2.25, pz)
        pts = bezier(b0, b0 + v3(side * 0.25, 0.32, 0), b0 + v3(side * 0.42, 0.1, 0), 4)
        polyline(lanterns, "pillar_lantern_bracket_" + sn, pts, 0.05, "brass", sides=4)
        disc(lanterns, "pillar_lantern_scroll_" + sn, b0 + v3(side * 0.1, -0.1, 0), (0, 0, 1), 0.07, 0.03, "brass", sides=8)
        tube(lanterns, "pillar_lantern_hook_" + sn, pts[-1], pts[-1] - v3(0, 0.08, 0), 0.03, "iron", sides=4)
        lantern(lanterns, "pillar_lantern_" + sn, pts[-1] - v3(0, 0.38, 0), 0.22, 0.28, bail=False)
    # ---- hull: portholes with brass rims under the deck line, gilded scrolls, gold beading, sandbags
    for side, sn in SIDES:
        for k, z in enumerate((-3.3, -0.6, 1.0, 3.3)):
            p, n = hull_pt(z, 0.06, side, 0.0)
            dial(gondola, "porthole_%s%d" % (sn, k), p, n, 0.17, face="porthole", depth=0.08)
        # gold beading just under the gunwale, following the sheer
        zz = [z for z in STATIONS if -6.6 <= z <= 6.6]
        pts = [(z, sheer(z) - 0.1) for z in zz]
        hull_curve(gondola, "beading_" + sn, pts, side, 0.035, 0.05, "gold", out=0.01)
        # gilded scrolls at the bow and the stern, on the upper strake
        for e, zc in ((1, 5.15), (-1, -5.25)):
            yb = upper_y(zc, 0.62)
            yc = (yb + sheer(zc) - 0.1) / 2 + 0.02
            r0 = (sheer(zc) - 0.1 - yb) * 0.42
            tail = [(zc - e * 2.1, upper_y(zc - e * 2.1, 0.8)), (zc - e * 1.4, upper_y(zc - e * 1.4, 0.83)),
                    (zc - e * 0.8, yc - r0 * 0.4), (zc - e * 0.3, yc + r0 * 1.0)]
            pts = scroll_pts(zc, yc, r0, 1.15, -e, tail, m=12)
            hull_curve(gondola, "scroll_%s%d" % (sn, e > 0), pts, side, 0.045, 0.09, "gold")
            # a smaller counter-curl and a leaf on the tail
            S = tail[2]
            lc = (S[0] - e * 0.3, S[1] - r0 * 0.35)
            leaf = scroll_pts(lc[0], lc[1], math.hypot(S[0] - lc[0], S[1] - lc[1]), 0.85, -e, [], m=8,
                              a0=math.atan2(S[1] - lc[1], S[0] - lc[0]))
            hull_curve(gondola, "scroll_leaf_%s%d" % (sn, e > 0), leaf, side, 0.035, 0.055, "gold")
            p, n = hull_pt(zc, yc, side, 0.05)
            disc(gondola, "scroll_boss_%s%d" % (sn, e > 0), p, n, 0.06, 0.05, "brass", sides=8)
        # sandbags hanging over the side on short lines: round sacks tied at the neck
        for k, z in enumerate((-3.0, 0.4, 3.9)):
            g, n = hull_pt(z, sheer(z) + 0.08, side, 0.0)
            bag, _ = hull_pt(z, sheer(z) - 0.42, side, 0.17)
            tube(gondola, "sandbag_line_%s%d" % (sn, k), g, bag + v3(0, 0.15, 0), 0.04, "rope", sides=4)
            tube(gondola, "sandbag_%s%d" % (sn, k), bag - v3(0, 0.2, 0), bag + v3(0, 0.02, 0), 0.27, "burlap", sides=8, phase=0.2)
            tube(gondola, "sandbag_b_%s%d" % (sn, k), bag - v3(0, 0.25, 0), bag - v3(0, 0.19, 0), 0.2, "burlap", sides=8, phase=0.2)
            tube(gondola, "sandbag_top_%s%d" % (sn, k), bag + v3(0, 0.02, 0), bag + v3(0, 0.08, 0), 0.19, "burlap", sides=8, phase=0.2)
            tube(gondola, "sandbag_tie_%s%d" % (sn, k), bag + v3(0, 0.08, 0), bag + v3(0, 0.13, 0), 0.08, "rope", sides=6)
            tube(gondola, "sandbag_tuft_%s%d" % (sn, k), bag + v3(0, 0.13, 0), bag + v3(0, 0.17, 0), 0.12, "burlap", sides=6)
        # brass chain plates on the planking under each suspension line, bolted twice
        for k, s_ in enumerate(HOOP_S[1:]):
            z = max(-asp.HALF_LENGTH + 1.0, min(asp.HALF_LENGTH - 1.0, zs(s_)))
            hull_curve(gondola, "chainplate_%s%d" % (sn, k), [(z, sheer(z) + 0.02), (z, sheer(z) - 0.32), (z, sheer(z) - 0.62)], side, 0.03,
                       0.11, "brass", out=0.035)
            for j, dy in enumerate((0.2, 0.5)):
                p, nn = hull_pt(z, sheer(z) - dy, side, 0.07)
                disc(gondola, "chainplate_bolt_%s%d_%d" % (sn, k, j), p, nn, 0.04, 0.03, "gold", sides=8)
            p, nn = hull_pt(z, sheer(z) - 0.66, side, 0.06)
            disc(gondola, "chainplate_end_%s%d" % (sn, k), p, nn, 0.08, 0.04, "brass", sides=8)
        # winged gear emblem on the bow, either side of the stem
        ez, ey = 6.95, 1.75
        p, nn = hull_pt(ez, ey, side, 0.05)
        disc(gondola, "emblem_gear_" + sn, p, nn, 0.22, 0.05, "brass", sides=12)
        R = face_frame(nn)
        for t in range(10):
            a = 2 * math.pi * t / 10
            q = p + (R[:, 0] * math.cos(a) + R[:, 1] * math.sin(a)) * 0.24
            add_cube(gondola, "emblem_tooth_%s%d" % (sn, t), q, R @ rz(a), (0.08, 0.07, 0.05), "brass")
        disc(gondola, "emblem_ring_" + sn, p + nn * 0.02, nn, 0.13, 0.04, "gold", sides=8)
        disc(gondola, "emblem_boss_" + sn, p + nn * 0.045, nn, 0.06, 0.04, "brass", sides=8)
        # the wing: five gilded feathers fanning aft over the bow planking, longest in the middle
        for f, (ang, ln) in enumerate(((0.55, 0.75), (0.28, 1.0), (0.0, 1.15), (-0.27, 1.0), (-0.52, 0.72))):
            pts = []
            for j in range(5):
                t = j / 4
                L = 0.22 + ln * t
                aa = ang * (1 + 0.35 * t)
                pts.append((ez - L * math.cos(aa), ey + L * math.sin(aa) + 0.12 * t * t))
            for j in range(len(pts) - 1):
                (za_, ya_), (zb_, yb_) = pts[j], pts[j + 1]
                (pa, na), (pb, nb) = hull_pt(za_, ya_, side, 0.045), hull_pt(zb_, yb_, side, 0.045)
                wd = 0.13 * (1 - 0.55 * (j / 3)) if j else 0.1
                beam(gondola, "emblem_feather_%s%d_%d" % (sn, f, j), pa, pb, 0.03, "gold", width=wd, up=norm(na + nb), extend=wd * 0.4)


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
            # a strap clamped round the hoop, with a round domed boss
            add_cube(balloon, "clasp_%d_%d" % (h, k), p - R[:, 1] * 0.02, R, (0.36, 0.1, 0.42), "gold")
            disc(balloon, "clasp_%d_%d_boss" % (h, k), p + R[:, 1] * 0.06, R[:, 1], 0.14, 0.08, "brass", sides=8)
            disc(balloon, "clasp_%d_%d_cap" % (h, k), p + R[:, 1] * 0.11, R[:, 1], 0.07, 0.04, "gold", sides=4, phase=math.pi / 4)

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
    for k in range(asp.PROP_BLADES):
        a = 2 * math.pi * k / asp.PROP_BLADES
        d = v3(math.sin(a), math.cos(a), 0)
        side = np.cross(v3(0, 0, 1), d)
        # a wooden paddle: round shank from a brass sleeve, then a swept oval blade, twisted (steeper at
        # the root), with a rounded tip, dark edge strips hiding the steps and a brass-sheathed tip
        axes0 = blade_axes(d, side, 0.95)
        tube(prop, "prop_shank_%d" % k, hub + d * 0.3, hub + d * 1.05, 0.2, "prop")
        add_cube(prop, "prop_sleeve_%d" % k, hub + d * 0.5, axes0, (0.3, 0.32, 0.22), "brass")
        tube(prop, "prop_sleeve_ring_%d" % k, hub + d * 0.64, hub + d * 0.7, 0.26, "gold", sides=8)
        rs = [0.95 + (asp.PROP_R - 0.95) * (j / 14) ** 0.9 for j in range(15)]
        edges = ([], [])
        for j in range(len(rs) - 1):
            r_a, r_b = rs[j], rs[j + 1]
            rm = (r_a + r_b) / 2
            wd = blade_width(rm)
            c, ax = blade_point(hub, d, side, rm)
            reg = "brass" if rm > asp.PROP_R - 0.2 else "prop"
            add_cube(prop, "prop_blade_%d_%d" % (k, j), c, ax, (r_b - r_a + 0.03, wd, 0.09 - 0.03 * (rm - 0.95) / 1.45 - 0.003 * (j % 2)), reg)
        for j in range(13):
            r = 0.98 + (asp.PROP_R - 0.03 - 0.98) * j / 12
            c, ax = blade_point(hub, d, side, r)
            for e in (0, 1):
                edges[e].append(c + ax[:, 1] * (1 if e else -1) * blade_width(r) / 2)
        for e in (0, 1):
            pts = edges[e]
            for j in range(len(pts) - 1):
                c, ax = blade_point(hub, d, side, 0.98 + (asp.PROP_R - 1.01) * (j + 0.5) / 12)
                beam(prop, "prop_edge_%d_%d_%d" % (k, e, j), pts[j], pts[j + 1], 0.05, "dark_wood" if j < 10 else "brass",
                     width=0.1 - 0.02 * (j / 12), up=ax[:, 2], extend=0.03)
        add_cube(prop, "prop_blade_bolt_%d" % k, hub + d * 1.05 + axes0[:, 2] * 0.06, axes0, (0.1, 0.1, 0.04), "brass")
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
    benches(deck, main_y)
    # central round post up to the balloon, brass collars and a round brass plate with struts under the balloon
    bottom = BY - BR
    pz = asp.PILLAR_Z
    tube(deck, "pillar", (0, main_y, pz), (0, bottom + 0.3, pz), 0.55, "dark_wood", sides=12)
    for k, y in enumerate((main_y + 0.12, 2.6, bottom - 0.6)):
        tube(deck, "pillar_collar_%d" % k, (0, y - 0.09, pz), (0, y + 0.09, pz), 0.7, "brass", sides=12)
    disc(deck, "pillar_plate", (0, bottom - 0.05, pz), (0, 1, 0), 0.75, 0.14, "brass")
    for k, (dx, dz) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        tube(deck, "pillar_strut_%d" % k, (0, bottom - 1.3, pz), (dx * 0.6, bottom - 0.1, pz + dz * 0.6), 0.09, "brass")
    # helm: a small wheel on a turned pedestal (bone helm_wheel turns with "steer"), instruments
    helm(deck, main_y)

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
    engine_room(engine, ec, main_y)
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
    fc = v3(-0.72, main_y + 0.9, ec[2] + 0.32)
    ring(engine, "flywheel_rim", fc, (1, 0, 0), 0.4, 0.11, "gold", n=16, round_=True)
    for t in range(3):
        a = math.pi * t / 3
        d = v3(0, math.cos(a), math.sin(a))
        tube(engine, "flywheel_spoke_%d" % t, fc - d * 0.39, fc + d * 0.39, 0.06, "iron")
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
            # braided line from a crow's foot under the hoop down to a short chain of big gold links made
            # fast to the rail; the crow's foot spreads the load over the hoop and the net with three legs
            g = top - dl * 1.25
            tube(ropes, "line_%s%d" % (sn, k), g, rail + dl * 1.12, 0.22, "rope", extend=0.04)
            ring(ropes, "line_thimble_%s%d" % (sn, k), g, dl, 0.15, 0.07, "gold", n=8)
            tube(ropes, "line_seizing_%s%d" % (sn, k), g - dl * 0.08, g - dl * 0.3, 0.27, "rope_dark", sides=8)
            az = side * 150
            for j, (dz, da, out) in enumerate(((0.0, 0.0, 0.2), (0.75, side * 5, 0.16), (-0.75, -side * 5, 0.16))):
                q = P(z + dz, az + da, out)
                tube(ropes, "line_leg_%s%d_%d" % (sn, k, j), g + dl * 0.05, q, 0.1, "rope", extend=0.03)
                nq = norm(q - v3(0, BY, q[2]))
                disc(ropes, "line_toggle_%s%d_%d" % (sn, k, j), q + nq * 0.02, nq, 0.1 if j else 0.15, 0.06, "gold", sides=8)
            ring(ropes, "line_ring_%s%d" % (sn, k), rail + dl * 1.5, dl, 0.19, 0.08, "gold", n=8)
            p1 = norm(np.cross(dl, v3(0, 0, 1)))
            p2 = np.cross(dl, p1)
            for c in range(3):
                ring(ropes, "line_link_%s%d_%d" % (sn, k, c), rail + dl * (0.22 + 0.33 * c), p1 if c % 2 else p2, 0.16, 0.055,
                     "gold", n=8)
            disc(ropes, "line_clamp_%s%d" % (sn, k), rail, (0, 1, 0), 0.12, 0.14, "brass", sides=8)

    # ---------------------------------------------------------------- lanterns, anchor
    for side, sn in SIDES:
        z = -asp.HALF_LENGTH + 0.4
        base = v3(side * (hw(z) - 0.05), sheer(z) + 0.1, z)
        polyline(lanterns, "stern_lantern_bracket_" + sn, bezier(base, base + v3(side * 0.05, 0.4, -0.05), base + v3(side * 0.32, 0.38, -0.1), 3),
                 0.06, "brass")
        tube(lanterns, "stern_lantern_hook_" + sn, base + v3(side * 0.32, 0.38, -0.1), base + v3(side * 0.32, 0.31, -0.1), 0.03, "iron",
             sides=4)
        lantern(lanterns, "stern_lantern_" + sn, base + v3(side * 0.32, 0.0, -0.1), 0.26, 0.32, bail=False)
    bz_ = asp.HALF_LENGTH - 0.6
    bb = v3(0, sheer(bz_) + 0.1, bz_)
    tube(lanterns, "bow_lantern_post", bb, bb + v3(0, 0.45, 0), 0.07, "brass")
    tube(lanterns, "bow_lantern_collar", bb + v3(0, 0.06, 0), bb + v3(0, 0.12, 0), 0.12, "gold", sides=8)
    lantern(lanterns, "bow_lantern", bb + v3(0, 0.66, 0), 0.26, 0.34)
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
    outfit(gondola, deck, engine, lanterns, ropes, main_y)
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
