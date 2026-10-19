#!/usr/bin/env python3
"""Generates the Nautilus (nautilus) Blockbench model, its texture, its item icon and its interior grid.

Usage:  python3 tools/generate_nautilus.py

Outputs:
  blockbench/nautilus.bbmodel                                            (editable, texture embedded)
  src/main/resources/assets/medievalships/models/entity/nautilus.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/nautilus.png
  src/main/resources/assets/medievalships/textures/item/nautilus.png
  src/main/resources/assets/medievalships/interiors/nautilus.grid         (collisions, dry rooms, ladders, doors)

Reference: the Minecraft sheet of the Nautilus (side, top, front, rear and perspective views; see
docs/NAUTILUS_PLAN.md for the measurements). A long spindle of aged copper plates, darker low on
the hull, a steel ram at the bow, a crest of spikes climbing from the bow to the wheelhouse, a
raised casing along the top with a second crest of spikes, the great round salon window with its
ring of lights on each side, a row of portholes low on the fore half, two keels under the hull,
a tail cone with rings carrying the propeller and a fish-tail fin crossed by two horizontal fins.

The hull is a body with elliptical sections built from tilted panels (no staircase); around the
windows the panels are cut finer and left open over the glass, so the sea is seen from inside.
The casing, the wheelhouse and the projector cage, and inside every wall, floor and ceiling, are
drawn exactly on the boundaries of the interior grid (tools/nautilus_interior.py): what is drawn
is what collides. Room surfaces are named "lit*" (lit by the Nautilus's own lamps).

Bones used by the mod (keep their names when editing in Blockbench):
  propeller (propeller: played with the signed speed)    door_<k> (door k: 0 = closed, 1 = open)
"""
import math
import os
import sys
import uuid

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import generate_galleon as gn  # noqa: E402
import generate_galley as gg  # noqa: E402
import nautilus_shape as ns  # noqa: E402
import nautilus_interior as ni  # noqa: E402
import nautilus_texture as nt  # noqa: E402
import nautilus_decor as nd  # noqa: E402
import nautilus_furniture as nf  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/nautilus/%d" % _uuid_counter[0]))


gg.new_uuid = new_uuid
gn.new_uuid = new_uuid
gn.REGIONS = {k: (0,) + r for k, r in nt.REGIONS.items()}
gn.SIZE = nt.SIZE

v3, norm, Bone, add_cube, beam, board = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam, gg.board
rx, ry, rz = gg.rx, gg.ry, gg.rz
EYE = np.eye(3)
SIDES = (1, -1)

NAZ = 56
HULL_S = [-1.0, -0.985, -0.95, -0.9, -0.83, -0.74, -0.63, -0.5, -0.36, -0.22, -0.08, 0.0, 0.08, 0.2, 0.33, 0.46,
          0.58, 0.69, 0.78, 0.86, 0.92, 0.96, 0.985, 1.0]
FINE = 0.3  # size of the panels cut around the windows


def hull_z(s):
    return s * ns.BOW_Z if s >= 0 else -s * ns.STERN_Z


def P(z, az_deg, out=0.0):
    a = math.radians(az_deg)
    w, h = ns.half_width(z) + out, ns.half_height(z) + out
    return v3(math.sin(a) * w, ns.AXIS_Y + math.cos(a) * h, z)


def on_hull(z, y, side, out=0.0):
    """Point of the hull surface at (z, y) on one side, pushed out along the normal."""
    w, h = ns.half_width(z), ns.half_height(z)
    dy = max(-h, min(h, y - ns.AXIS_Y))
    x = side * w * math.sqrt(max(0.0, 1.0 - (dy / h) ** 2))
    n = norm(v3(x / max(w, 1e-6) ** 2, dy / max(h, 1e-6) ** 2, 0))
    return v3(x, y, z) + n * out, n


def stretched(cube):
    for f in cube.faces.values():
        if f is not None:
            f["stretch"] = True
    return cube


def panel(bone, name, a0, a1, b0, b1, th, region, outward, overlap=1.04):
    return stretched(board(bone, name, a0, a1, b0, b1, th, region, outward, overlap=overlap))


# windows cut in the hull: (z, y, radius) on both sides
# (z, y, radius, side: 1 port, -1 starboard, 0 both)
WINDOWS = [(ns.SALON_WINDOW[0], ns.SALON_WINDOW[1], ns.SALON_WINDOW[2] - 0.2, 0)] + \
          [(z, ns.SMALL_WINDOWS_Y, 0.45, side) for z in ns.SMALL_WINDOWS_Z for side in (1, -1) if ns.porthole_on(z, side)] + \
          [(z, y, 0.45, 0) for z, y in ns.CABIN_PORTHOLES]
# the airlock's way out through the starboard hull: (z0, z1, y0, y1)
AIRLOCK_MOUTH = (ni.AIRLOCK_TUNNEL[4], ni.AIRLOCK_TUNNEL[5], ni.AIRLOCK_TUNNEL[2], ni.AIRLOCK_TUNNEL[3])


def on_side(x, side):
    return abs(x) > 2.0 and (side == 0 or x * side > 0)


def in_window(p, pad=0.0):
    for z, y, r, side in WINDOWS:
        if (p[2] - z) ** 2 + (p[1] - y) ** 2 < (r + pad) ** 2 and on_side(p[0], side):
            return True
    z0, z1, y0, y1 = AIRLOCK_MOUTH
    return p[0] < -2.0 and z0 < p[2] < z1 and y0 < p[1] < y1


def near_window(points):
    zs = [p[2] for p in points]
    ys = [p[1] for p in points]
    xs = [p[0] for p in points]
    for z, y, r, side in WINDOWS:
        if min(zs) - r < z < max(zs) + r and min(ys) - r < y < max(ys) + r and any(on_side(x, side) for x in xs):
            return True
    z0, z1, y0, y1 = AIRLOCK_MOUTH
    return min(xs) < -2.0 and min(zs) - 0.5 < z1 and max(zs) + 0.5 > z0 and min(ys) - 0.5 < y1 and max(ys) + 0.5 > y0


def hull(bone):
    n = 0
    for i in range(len(HULL_S) - 1):
        za, zb = hull_z(HULL_S[i]), hull_z(HULL_S[i + 1])
        for j in range(NAZ):
            a0, a1 = 360.0 * j / NAZ, 360.0 * (j + 1) / NAZ
            am = (a0 + a1) / 2
            outward = v3(math.sin(math.radians(am)), math.cos(math.radians(am)), 0)
            region = "plate" if math.cos(math.radians(am)) > -0.12 else "plate_dark"  # dark below the belt, as in the reference
            corners = [P(za, a0), P(za, a1), P(zb, a0), P(zb, a1)]
            if not near_window(corners):
                panel(bone, "hull_%d_%d" % (i, j), *corners, 0.12, region, outward)
                n += 1
                continue
            # around a window: finer panels, left open over the glass
            nz_ = max(1, int(math.ceil(abs(zb - za) / FINE)))
            na_ = max(1, int(math.ceil(np.linalg.norm(corners[1] - corners[0]) / FINE)))
            for p in range(nz_):
                for q in range(na_):
                    z0, z1 = za + (zb - za) * p / nz_, za + (zb - za) * (p + 1) / nz_
                    b0, b1 = a0 + (a1 - a0) * q / na_, a0 + (a1 - a0) * (q + 1) / na_
                    c = P((z0 + z1) / 2, (b0 + b1) / 2)
                    if in_window(c):
                        continue
                    sub = panel(bone, "hull_%d_%d_%d_%d" % (i, j, p, q), P(z0, b0), P(z0, b1), P(z1, b0), P(z1, b1), 0.12, region,
                                outward)
                    for f in sub.faces.values():
                        if f is not None:
                            f["sub"] = (p / nz_, q / na_, (p + 1) / nz_, (q + 1) / na_)
                    n += 1
    return n


def round_bezel(bone, name, center, normal, r, half, region, n=24, th=0.04):
    """A flat plate in a wall's plane that fills the space between a circle of radius r and the
    square of half size `half` round it (covers the corners of a square hole behind a round frame)."""
    normal = norm(normal)
    e1 = norm(np.cross(normal, v3(0, 1, 0))) if abs(normal[1]) < 0.9 else v3(1, 0, 0)
    e2 = np.cross(e1, normal)
    def on_square(a):
        c, s_ = math.cos(a), math.sin(a)
        k = half / max(abs(c), abs(s_))
        return center + (e1 * c + e2 * s_) * max(k, r + 0.02)
    def on_circle(a):
        return center + (e1 * math.cos(a) + e2 * math.sin(a)) * r
    for j in range(n):
        a0, a1 = 2 * math.pi * j / n, 2 * math.pi * (j + 1) / n
        panel(bone, "%s_%d" % (name, j), on_circle(a0), on_circle(a1), on_square(a0), on_square(a1), th, region, normal, overlap=1.03)


def ring(bone, name, center, normal, r, th, region, n=16, width=None):
    normal = norm(normal)
    e1 = norm(np.cross(normal, v3(0, 0, 1) if abs(normal[2]) < 0.9 else v3(1, 0, 0)))
    e2 = np.cross(normal, e1)
    for k in range(n):
        t0, t1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        p0 = center + (e1 * math.cos(t0) + e2 * math.sin(t0)) * r
        p1 = center + (e1 * math.cos(t1) + e2 * math.sin(t1)) * r
        beam(bone, "%s_%d" % (name, k), p0, p1, th, region, width=width, up=normal, extend=th * 0.3)


def windows(bone, lights):
    wz, wy, wr = ns.SALON_WINDOW
    for side in SIDES:
        sn = "p" if side > 0 else "s"
        c, nrm = on_hull(wz, wy, side, 0.08)
        ring(bone, "salon_frame_%s" % sn, c, nrm, wr - 0.05, 0.3, "brass", n=32, width=0.36)
        ring(bone, "salon_iris_%s" % sn, c, nrm, wr * 0.7, 0.06, "brass", n=32, width=0.1)
        for k in range(8):
            t = 2 * math.pi * (k + 0.5) / 8
            zz, yy = wz + math.cos(t) * (wr + 0.45), wy + math.sin(t) * (wr + 0.45)
            p, nn = on_hull(zz, yy, side, 0.12)
            add_cube(lights, "glow_salon_lamp_%s%d" % (sn, k), p, EYE, (0.3, 0.3, 0.3), "glow")
            add_cube(bone, "salon_lamp_socket_%s%d" % (sn, k), on_hull(zz, yy, side, 0.02)[0], EYE, (0.42, 0.42, 0.42), "brass")
        for z, y in [(z, ns.SMALL_WINDOWS_Y) for z in ns.SMALL_WINDOWS_Z if ns.porthole_on(z, side)] + list(ns.CABIN_PORTHOLES):
            # a round bolted collar, its inner lip and a ring of bolts
            name = "porthole_%s_%d_%d" % (sn, int(z * 10), int(y * 10))
            c, nrm = on_hull(z, y, side, 0.07)
            ring(bone, name, c, nrm, 0.56, 0.14, "brass", n=20, width=0.2)
            ring(bone, name + "_lip", c + nrm * 0.04, nrm, 0.45, 0.08, "brass", n=16, width=0.06)
            e1 = norm(np.cross(nrm, v3(0, 0, 1)))
            e2 = np.cross(nrm, e1)
            for k in range(8):
                t = 2 * math.pi * k / 8
                add_cube(bone, "%s_bolt%d" % (name, k), c + nrm * 0.08 + (e1 * math.cos(t) + e2 * math.sin(t)) * 0.56, EYE,
                         (0.07, 0.07, 0.07), "steel")
            # an eyebrow over it, the rain lip of a ship's porthole
            for k in range(7):
                t0, t1 = math.radians(25 + 130 * k / 7), math.radians(25 + 130 * (k + 1) / 7)
                beam(bone, "%s_brow%d" % (name, k), c + nrm * 0.1 + (e1 * math.cos(t0) + e2 * math.sin(t0)) * 0.76,
                     c + nrm * 0.1 + (e1 * math.cos(t1) + e2 * math.sin(t1)) * 0.76, 0.06, "brass", width=0.16, up=nrm, extend=0.01)
    # a riveted brass frame round the airlock's way out, on the starboard hull
    z0, z1, y0, y1 = AIRLOCK_MOUTH
    corners = [on_hull(z, y, -1, 0.06)[0] for z, y in ((z0 - 0.1, y0 - 0.1), (z1 + 0.1, y0 - 0.1), (z1 + 0.1, y1 + 0.1), (z0 - 0.1, y1 + 0.1))]
    for k in range(4):
        a_, b_ = corners[k], corners[(k + 1) % 4]
        beam(bone, "airlock_mouth_frame_%d" % k, a_, b_, 0.16, "brass", width=0.24, up=on_hull((z0 + z1) / 2, (y0 + y1) / 2, -1)[1],
             extend=0.12)
    # brass frames of the wheelhouse windows, outside and inside
    wy0, wy1 = ns.TOWER_WINDOWS_Y
    yc, r = (wy0 + wy1) / 2, (wy1 - wy0) / 2 + 0.05
    half = max((ns.TOWER_FRONT_WINDOWS_X[0][1] - ns.TOWER_FRONT_WINDOWS_X[0][0]) / 2, (wy1 - wy0) / 2) + 0.06
    for k, (x0, x1) in enumerate(ns.TOWER_FRONT_WINDOWS_X):
        zin = (ns.TOWER_Z[0] + ns.TOWER_Z[1]) / 2 + ns.wheelhouse_wall_z((x0 + x1) / 2) - 0.04
        for z, tag, nz in ((ns.TOWER_Z[1] + 0.16, "out", 1), (zin, "in", -1)):
            c = v3((x0 + x1) / 2, yc, z)
            ring(bone, "tower_window_%d_%s" % (k, tag), c, v3(0, 0, 1), r, 0.12, "brass", n=8, width=0.16)
            round_bezel(bone, "lit_tower_bezel_%d_%s" % (k, tag), c - v3(0, 0, nz * 0.05), v3(0, 0, nz), r - 0.02, half,
                        "wall_engine" if tag == "in" else "hull_light", n=8)
    for side in SIDES:
        xin = ns.wheelhouse_wall_x(sum(ns.TOWER_SIDE_WINDOW_Z) / 2) - 0.04
        for x, tag, nx in ((side * (ns.TOWER_HALF_WIDTH + 0.16), "out", side), (side * xin, "in", -side)):
            c = v3(x, yc, sum(ns.TOWER_SIDE_WINDOW_Z) / 2)
            ring(bone, "tower_window_side_%d_%s" % (side > 0, tag), c, v3(1, 0, 0), r, 0.12, "brass", n=8, width=0.16)
            round_bezel(bone, "lit_tower_bezel_side_%d_%s" % (side > 0, tag), c - v3(nx * 0.05, 0, 0), v3(nx, 0, 0), r - 0.02, half,
                        "wall_engine" if tag == "in" else "hull_light", n=8)


def ram(bone):
    y = ns.AXIS_Y
    segs = ((ns.BOW_Z - 3.0, ns.BOW_Z + 1.0, 1.3), (ns.BOW_Z + 1.0, ns.BOW_Z + 3.5, 0.9), (ns.BOW_Z + 3.5, ns.RAM_TIP_Z - 1.0, 0.55),
            (ns.RAM_TIP_Z - 1.0, ns.RAM_TIP_Z, 0.22))
    # a round spear tapering to its point, brass rings at the joints
    stations = [(ns.BOW_Z - 3.0, 0.68), (ns.BOW_Z + 1.0, 0.52), (ns.BOW_Z + 3.5, 0.42), (ns.RAM_TIP_Z - 1.0, 0.26), (ns.RAM_TIP_Z, 0.03)]
    for k in range(len(stations) - 1):
        (z0, r0), (z1, r1) = stations[k], stations[k + 1]
        nf.tube(bone, "ram_%d" % k, v3(0, y, z0), v3(0, y, z1), r0, r1, "steel", n=12)
        if k < len(stations) - 2:
            ring(bone, "ram_ring_%d" % k, v3(0, y, z1), v3(0, 0, 1), r1 + 0.04, 0.16, "brass", n=14, width=0.14)
    # a flange on top and under the ram, with teeth
    beam(bone, "ram_fin_top", v3(0, y + 0.3, ns.BOW_Z - 1.0), v3(0, y + 0.1, ns.RAM_TIP_Z - 1.2), 0.12, "steel", width=0.5, up=v3(1, 0, 0))
    beam(bone, "ram_fin_bottom", v3(0, y - 0.3, ns.BOW_Z - 1.0), v3(0, y - 0.1, ns.RAM_TIP_Z - 1.2), 0.12, "steel", width=0.5, up=v3(1, 0, 0))
    for k, z in enumerate(np.arange(ns.BOW_Z - 0.5, ns.RAM_TIP_Z - 1.5, 1.2)):
        for s, yy in ((1, 0.55), (-1, -0.55)):
            add_cube(bone, "ram_tooth_%d_%d" % (k, s > 0), v3(0, y + s * (0.42 - 0.03 * k), z), rx(math.radians(45)), (0.1, 0.3, 0.3), "steel")


def spike(bone, name, base, up, h, w, region="plate_dark"):
    """A tapering spike from base along up (two crossed tapered plates)."""
    up = norm(up)
    for k in range(3):
        f = k / 3
        c = base + up * h * (f + 1 / 6)
        s = w * (1 - f) * 0.9 + 0.06
        add_cube(bone, "%s_%d" % (name, k), c, gg.frame_from(up, v3(0, 0, 1)), (h / 3 + 0.02, s, s), region)


def crests(bone):
    # fore crest: a curved band from the hull top near the bow to the top of the wheelhouse front, spikes on it
    z0, z1 = ns.FORE_CREST
    p0 = v3(0, ns.hull_top(z0) - 0.2, z0)
    p2 = v3(0, ns.TOWER_TOP_Y - 0.2, z1)
    p1 = v3(0, ns.TOWER_TOP_Y + 0.2, (z0 + z1) / 2 + 2.5)
    pts = [(1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2 for t in np.linspace(0, 1, 19)]
    for k in range(len(pts) - 1):
        beam(bone, "crest_fore_%d" % k, pts[k], pts[k + 1], 0.7, "plate_dark", width=0.42, up=v3(1, 0, 0), extend=0.05)
        for sd in (1, -1):  # riveted straps on both faces
            beam(bone, "crest_fore_strap_%d_%d" % (k, sd > 0), pts[k] + v3(sd * 0.22, 0.12, 0), pts[k + 1] + v3(sd * 0.22, 0.12, 0), 0.03, "seam",
                 width=0.16, up=v3(sd, 0, 0), extend=0.03)
        beam(bone, "crest_fore_edge_%d" % k, pts[k] - v3(0, 0.3, 0), pts[k + 1] - v3(0, 0.3, 0), 0.08, "brass", width=0.36, up=v3(1, 0, 0),
             extend=0.03)
        if k % 2 == 0:
            d = norm(pts[k + 1] - pts[k])
            up = norm(np.cross(d, v3(1, 0, 0)))
            if up[1] < 0:
                up = -up
            spike(bone, "crest_fore_spike_%d" % k, (pts[k] + pts[k + 1]) / 2 + up * 0.2, norm(up + d * 0.35), 0.9, 0.35)
    # the lamp hung under the top end of the arch, in front of the wheelhouse (reference sheet)
    lamp = p2 + v3(0, -0.75, 0.55)
    nf.ellipsoid(bone, "glow_arch_lamp", lamp, (0.38, 0.38, 0.38), EYE, "glow", nlat=4, nlon=12)
    ring(bone, "arch_lamp_cage_h", lamp, v3(0, 1, 0), 0.42, 0.06, "brass", n=14, width=0.06)
    ring(bone, "arch_lamp_cage_v", lamp, v3(1, 0, 0), 0.42, 0.06, "brass", n=14, width=0.06)
    beam(bone, "arch_lamp_hanger", lamp + v3(0, 0.4, 0), p2 + v3(0, -0.2, 0.3), 0.08, "brass")
    # a ridge of small spikes along the back of the bow, from the ram to the foot of the arch
    for k, z in enumerate(np.arange(z0 + 1.2, ns.BOW_Z - 0.5, 1.1)):
        spike(bone, "bow_ridge_spike_%d" % k, v3(0, ns.hull_top(z) - 0.05, z), v3(0, 1, 0.45), 0.55 - 0.03 * k, 0.24)
    # and a row of spikes under the bow, along its keel line, as in the reference sheet
    for k, z in enumerate(np.arange(ns.BOW_Z - 1.0, 22.0, -1.3)):
        foot = bow_blade_foot(z) if z >= 26.0 else ns.hull_bottom(z)
        spike(bone, "bow_keel_spike_%d" % k, v3(0, foot + 0.05, z), v3(0, -1, 0.5), 0.6 - 0.015 * k, 0.26)
    # aft crest: spikes along the casing
    za, zb = ns.AFT_CREST
    for k, z in enumerate(np.linspace(za, zb, 11)):
        h = 1.7 - 0.6 * k / 10  # tallest behind the wheelhouse, smaller towards the stern
        spike(bone, "crest_aft_spike_%d" % k, v3(0, ns.CASING_TOP_Y, z), v3(0, 1, 0.3), h, 0.5)
    beam(bone, "crest_aft_band", v3(0, ns.CASING_TOP_Y + 0.15, za + 0.5), v3(0, ns.CASING_TOP_Y + 0.15, zb - 0.5), 0.3, "steel", width=0.3)
    # a row of smaller spikes along the casing edges, fore of the wheelhouse
    for k, z in enumerate(np.arange(ns.TOWER_Z[1] + 1.0, ns.CASING_Z[1] - 0.5, 1.4)):
        for s in SIDES:
            spike(bone, "casing_spike_%d_%d" % (k, s > 0), v3(s * (ns.CASING_HALF_WIDTH - 0.2), ns.CASING_TOP_Y, z), v3(s * 0.4, 1, 0.3),
                  0.6, 0.25)


def keels(bone):
    """Bilge keels as faired fins: a rounded trapezoid section that grows out of the hull, deepest in
    the middle and fading into the hull at both ends."""
    for k, (z0, z1) in enumerate(ns.KEELS):
        zs = np.linspace(z0 - 1.5, z1 + 1.5, 22)
        sections = []
        for z in zs:
            t = (z - (z0 - 1.5)) / (z1 - z0 + 3.0)
            d = ns.KEEL_DEPTH * math.sin(math.pi * t) ** 0.6
            hb = ns.hull_bottom(z)
            pts = []
            for x, kind in ((-0.75, "root"), (-0.3, "foot"), (-0.12, "sole"), (0.12, "sole"), (0.3, "foot"), (0.75, "root")):
                if kind == "root":
                    yy = ns.hull_bottom(z, x) + 0.25
                elif kind == "foot":
                    yy = hb - d * 0.85
                else:
                    yy = hb - d
                pts.append(v3(x, yy, z))
            sections.append(pts)
        for i in range(len(sections) - 1):
            for j in range(len(sections[i]) - 1):
                a0, a1 = sections[i][j], sections[i][j + 1]
                b0, b1 = sections[i + 1][j], sections[i + 1][j + 1]
                mid = (a0 + a1 + b0 + b1) / 4
                out = mid - v3(0, ns.AXIS_Y + 2.0, mid[2])
                panel(bone, "keel_%d_%d_%d" % (k, i, j), a0, a1, b0, b1, 0.08, "steel" if j == 2 else "plate_dark", out, overlap=1.02)


def loft(bone, name, sections, region, centre, th=0.08, closed=False, skip=None):
    """Panels between consecutive sections (lists of points of the same length), facing away from
    centre(point). skip(i, j, mid) -> True leaves a hole (windows)."""
    n = 0
    for i in range(len(sections) - 1):
        A, B = sections[i], sections[i + 1]
        m = len(A) if closed else len(A) - 1
        for j in range(m):
            a0, a1 = A[j], A[(j + 1) % len(A)]
            b0, b1 = B[j], B[(j + 1) % len(B)]
            if np.linalg.norm(a1 - a0) < 1e-4 and np.linalg.norm(b1 - b0) < 1e-4:
                continue
            if np.linalg.norm(b0 - a0) < 1e-4 and np.linalg.norm(b1 - a1) < 1e-4:
                continue
            mid = (a0 + a1 + b0 + b1) / 4
            if skip is not None and skip(i, j, mid):
                continue
            panel(bone, "%s_%d_%d" % (name, i, j), a0, a1, b0, b1, th, region, mid - centre(mid), overlap=1.03)
            n += 1
    return n


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


BAY_WALL_X = 3.5  # the salon's side walls


def bay_sleeves(bone):
    """The alcoves of the two great windows of the salon, seen from the room: a round sleeve of dark
    panelling from the wall to the glass with gilded ribs, framed on the wall by a wide gilded
    moulding (instead of the stepped hole the grid cuts through the wall)."""
    wz, wy, wr = ns.SALON_WINDOW
    r = wr - 0.25
    n = 32
    for side in SIDES:
        sn = "p" if side > 0 else "s"
        wall = side * BAY_WALL_X

        def P(x, rr, a):
            return v3(x, wy + math.sin(a) * rr, wz + math.cos(a) * rr)

        def glass_x(a):
            return on_hull(wz + math.cos(a) * r, wy + math.sin(a) * r, side, -0.12)[0][0]

        for j in range(n):
            a0, a1 = 2 * math.pi * j / n, 2 * math.pi * (j + 1) / n
            am = (a0 + a1) / 2
            g0, g1 = glass_x(a0), glass_x(a1)
            panel(bone, "lit_bay_%s_sleeve%d" % (sn, j), P(wall - side * 0.02, r, a0), P(wall - side * 0.02, r, a1), P(g0, r, a0), P(g1, r, a1),
                  0.06, "organ_wood", v3(0, math.sin(am), math.cos(am)), overlap=1.03)
            # gilded ribs along the sleeve, and the wide moulding round its mouth on the wall
            for t, w in ((0.0, 0.55), (0.5, 0.1), (0.92, 0.12)):
                x0 = wall + (g0 - wall) * t
                x1 = wall + (g1 - wall) * t
                rr = r + (0.22 if t == 0 else -0.03)
                beam(bone, "lit_bay_%s_rib%d_%d" % (sn, int(t * 100), j), P(x0 - side * (0.04 if t == 0 else 0), rr, a0),
                     P(x1 - side * (0.04 if t == 0 else 0), rr, a1), 0.08 if t == 0 else 0.06, "gold",
                     width=w, up=v3(side, 0, 0) if t == 0 else v3(0, math.sin(am), math.cos(am)), extend=0.02)
            if j % 4 == 2:
                add_cube(bone, "lit_bay_%s_rosette%d" % (sn, j), P(wall - side * 0.12, r + 0.22, am), EYE, (0.1, 0.12, 0.12), "gold")


def porthole_sleeves(bone, fx, g):
    """Seen from the rooms, each porthole is a bronze sleeve narrowing through the hull to its glass,
    framed on the wall by a bolted brass collar (instead of a square hole in the wall)."""
    ports = [(z, ns.SMALL_WINDOWS_Y) for z in ns.SMALL_WINDOWS_Z] + list(ns.CABIN_PORTHOLES)
    C = ni.CELL
    count = 0
    for z, y in ports:
        for side in SIDES:
            if y == ns.SMALL_WINDOWS_Y and not ns.porthole_on(z, side):
                continue
            def kind(x, yy):
                return g.k[int((x - ni.X0) / C), int((yy - ni.Y0) / C), int((z - ni.Z0) / C)]
            glass = wall = None
            for x in np.arange(1.0, 8.0, C / 2) * side:
                if kind(x, y) == ni.WINDOW:
                    glass = x
                    break
            if glass is not None:
                # back from the glass along the tunnel until the room opens above it: the wall's face
                x = glass
                while abs(x) > 1.0 and kind(x, y + 0.75) not in (ni.DRY, ni.FURNITURE, ni.LADDER, ni.AIRLOCK):
                    x -= side * C / 2
                i_room = int((x - ni.X0) / C)
                wall = ni.X0 + (i_room + 1) * C if side > 0 else ni.X0 + i_room * C  # the wall's face on the room
            if wall is None or glass is None:
                continue
            glass = glass + side * C if abs(glass) - abs(wall) < 0.3 else glass  # thin wall: the glass in the hull's skin
            n = 20
            name = "porthole_%d_%d_%d" % (int(z * 10), int(y * 10), side > 0)
            for j in range(n):
                a0, a1 = 2 * math.pi * j / n, 2 * math.pi * (j + 1) / n
                def P(x, r, a):
                    return v3(x, y + math.sin(a) * r, z + math.cos(a) * r)
                am = (a0 + a1) / 2
                panel(bone, "lit_%s_sleeve%d" % (name, j), P(wall - side * 0.02, 0.74, a0), P(wall - side * 0.02, 0.74, a1), P(glass, 0.45, a0),
                      P(glass, 0.45, a1), 0.05,
                      "hull_light", v3(0, -math.sin(am), -math.cos(am)), overlap=1.04)
                beam(bone, "lit_%s_collar%d" % (name, j), P(wall - side * 0.06, 0.68, a0), P(wall - side * 0.06, 0.68, a1), 0.08, "brass",
                     width=0.2, up=v3(side, 0, 0), extend=0.01)
                if j % 4 == 0:
                    add_cube(bone, "lit_%s_bolt%d" % (name, j), P(wall - side * 0.1, 0.68, am), EYE, (0.04, 0.045, 0.045), "brass")
            # four dogs clamping the glass frame, a hinge on one side
            for k in range(4):
                am = math.pi / 4 + k * math.pi / 2
                add_cube(bone, "lit_%s_dog%d" % (name, k), P(wall - side * 0.09, 0.56, am), EYE, (0.05, 0.06, 0.06), "brass")
            add_cube(bone, "lit_%s_hinge" % name, P(wall - side * 0.09, 0.62, math.pi), EYE, (0.05, 0.16, 0.06), "brass")
            # the corners of the square opening, hidden by a round bezel on the wall round the collar
            round_bezel(bone, "lit_%s_bezel" % name, v3(wall - side * 0.02, y, z), v3(-side, 0, 0), 0.6, 0.56, "brass", n=16)
            add_cube(fx, "lit_%s_glass" % name, v3(glass + side * 0.1, y, z), EYE, (0.02, 0.9, 0.9), "glassfx")
            count += 1
    return count


def spiral_stair(bone):
    """The central spiral staircase (panel 9): open treads of dark wood with brass nosings on iron
    brackets, round the column, a helical handrail on balusters (the grid's slab cells stop the
    players, these are what is drawn)."""
    scx, scz = ni.SPIRAL_CENTER
    r0, r1 = ni.SPIRAL_R
    steps = int(round((ni.M0 - ni.L0) / ni.CELL))
    c = v3(scx, 0, scz)
    def at(a_deg, r, y):
        a = math.radians(a_deg)
        return v3(scx + math.sin(a) * r, y, scz + math.cos(a) * r)
    for k in range(steps):
        top = ni.L0 + (k + 1) * ni.CELL
        a0, a1 = 360.0 * k / steps, 360.0 * (k + 1) / steps
        for q in range(3):  # a tread in three slices: its outer edge follows the circle
            b0, b1 = a0 + (a1 - a0) * q / 3, a0 + (a1 - a0) * (q + 1) / 3
            panel(bone, "lit_stair_tread_%d_%d" % (k, q), at(b0, r0, top), at(b0, r1, top), at(b1, r0, top), at(b1, r1, top), 0.1,
                  "floor", v3(0, 1, 0), overlap=1.03)
        beam(bone, "lit_stair_nosing_%d" % k, at(a0 + 1, r0 + 0.05, top - 0.03), at(a0 + 1, r1 - 0.02, top - 0.03), 0.07, "brass", width=0.08)
        beam(bone, "lit_stair_bracket_%d" % k, at((a0 + a1) / 2, r0, top - 0.25), at((a0 + a1) / 2, r1 - 0.2, top - 0.12), 0.08, "iron")
        # baluster and handrail segment
        bt = at(a0 + 20, r1 - 0.08, top)
        beam(bone, "lit_stair_baluster_%d" % k, bt, bt + v3(0, 0.95, 0), 0.05, "iron")
        h0 = at(a0, r1 - 0.08, top + 0.95)
        h1 = at(a1, r1 - 0.08, top + 0.95 + ni.CELL)
        mid = at((a0 + a1) / 2, r1 - 0.08, top + 0.95 + ni.CELL / 2)
        beam(bone, "lit_stair_rail_%d_a" % k, h0, mid, 0.08, "brass")
        beam(bone, "lit_stair_rail_%d_b" % k, mid, h1, 0.08, "brass")
    # the column: round, iron with brass rings
    n = 12
    rc = r0 - 0.02
    for j in range(n):
        a0, a1 = 360.0 * j / n, 360.0 * (j + 1) / n
        out = at((a0 + a1) / 2, 1.0, 0) - c
        panel(bone, "lit_stair_column_%d" % j, at(a0, rc, ni.L0), at(a1, rc, ni.L0), at(a0, rc, ni.M1), at(a1, rc, ni.M1), 0.06, "wall_engine",
              v3(out[0], 0, out[2]), overlap=1.04)
    for y in (ni.L0 + 0.1, ni.L0 + 2.0, ni.M0 + 0.1, ni.M1 - 0.2):
        for j in range(n):
            a0, a1 = 360.0 * j / n, 360.0 * (j + 1) / n
            beam(bone, "lit_stair_column_ring_%d_%d" % (int(y * 10), j), at(a0, rc + 0.05, y), at(a1, rc + 0.05, y), 0.1, "brass", width=0.06)


def casing_fairing(bone):
    """The casing on the back of the hull, faired: a flat deck (the walkway) on rounded shoulders
    that melt into the hull, and long sloping ends (the grid's box under it keeps the collisions)."""
    z0, z1 = ns.CASING_Z
    top = ns.CASING_TOP_Y + 0.01
    ramp = 4.0
    zs = np.concatenate([np.arange(z0 - ramp, z0, 0.5), np.arange(z0, z1, 1.0), np.arange(z1, z1 + ramp + 0.01, 0.5)])
    left, right, deck = [], [], []
    for z in zs:
        f = smoothstep(1 - (z0 - z) / ramp) if z < z0 else smoothstep(1 - (z - z1) / ramp) if z > z1 else 1.0
        ht = ns.hull_top(z)
        dy = ht + (top - ht) * f
        hw = 1.75 * (0.3 + 0.7 * f)
        xb = min(3.5, ns.half_width(z) * 0.85) * (0.55 + 0.45 * f)
        yb = ns.hull_top(z, xb) - 0.2
        sh = [v3(hw + (xb - hw) * math.sin(t), yb + (dy - yb) * math.cos(t), z) for t in np.linspace(0, math.pi / 2, 7)]
        right.append(sh)
        left.append([v3(-p[0], p[1], p[2]) for p in sh])
        deck.append((z, hw, dy))
    centre = lambda p: v3(0, ns.AXIS_Y + 3.0, p[2])
    # a row of slot windows along both shoulders, under the deck edge (reference sheet), and a riveted seam
    for z in np.arange(z0 + 1.0, z1 - 0.5, 1.6):
        if ns.TOWER_Z[0] - 0.8 < z < ns.TOWER_Z[1] + 0.8 or ns.LIFEBOAT_RECESS[0] - 0.5 < z < ns.LIFEBOAT_RECESS[1] + 0.5:
            continue
        hw = 1.75
        xb = min(3.5, ns.half_width(z) * 0.85)
        yb = ns.hull_top(z, xb) - 0.2
        t = 0.55
        for side in SIDES:
            pt = v3(side * (hw + (xb - hw) * math.sin(t)), yb + (top - yb) * math.cos(t), z)
            tan = norm(v3(side * (xb - hw) * math.cos(t), -(top - yb) * math.sin(t), 0))
            nrm = norm(np.cross(tan, v3(0, 0, 1))) * (-side)  # out of the shoulder
            R = np.column_stack([v3(0, 0, 1), tan, nrm])
            if np.linalg.det(R) < 0:
                R[:, 1] = -R[:, 1]
            c = pt + nrm * 0.05
            add_cube(bone, "slot_%d_%d" % (int(z * 10), side > 0), c, R, (0.6, 0.2, 0.04), "glass")
            for k, (dz, dv, sz, sv) in enumerate(((0, 0.14, 0.74, 0.07), (0, -0.14, 0.74, 0.07), (0.34, 0, 0.07, 0.22), (-0.34, 0, 0.07, 0.22))):
                add_cube(bone, "slot_%d_%d_f%d" % (int(z * 10), side > 0, k), c + R[:, 0] * dz + R[:, 1] * dv + nrm * 0.02, R, (sz, sv, 0.06),
                         "brass")
    for side in SIDES:
        for i in range(len(zs) - 1):
            pa, pb = right[i][2], right[i + 1][2]
            if side < 0:
                pa, pb = v3(-pa[0], pa[1], pa[2]), v3(-pb[0], pb[1], pb[2])
            beam(bone, "shoulder_seam_%d_%d" % (side > 0, i), pa, pb, 0.05, "seam", width=0.14,
                 up=norm(pa - v3(0, ns.AXIS_Y + 3.0, pa[2])), extend=0.05)
    loft(bone, "casing_shoulder_p", right, "hull_light", centre)
    loft(bone, "casing_shoulder_s", left, "hull_light", centre)
    # the deck: plates between the shoulders, with holes for the wheelhouse and the projector cage
    # (they stand on it), the lifeboat recess and the main hatch
    holes = [(-2.6, 2.6, ns.TOWER_Z[0] - 0.1, ns.TOWER_Z[1] + 0.1),
             (-1.3, 1.3, ns.LIFEBOAT_RECESS[0], ns.LIFEBOAT_RECESS[1]),
             (ns.HATCH_DECK[0], ns.HATCH_DECK[1], ns.HATCH_DECK[2], ns.HATCH_DECK[3])]
    for i in range(len(deck) - 1):
        za, hwa, ya = deck[i]
        zb, hwb, yb_ = deck[i + 1]
        xs = list(np.linspace(-max(hwa, hwb), max(hwa, hwb), 8))
        for j in range(len(xs) - 1):
            xm, zm = (xs[j] + xs[j + 1]) / 2, (za + zb) / 2
            if any(h[0] < xm < h[1] and h[2] < zm < h[3] for h in holes):
                continue
            ca = lambda x: max(-hwa, min(hwa, x))
            cb = lambda x: max(-hwb, min(hwb, x))
            panel(bone, "casing_deck_%d_%d" % (i, j), v3(ca(xs[j]), ya, za), v3(ca(xs[j + 1]), ya, za), v3(cb(xs[j]), yb_, zb),
                  v3(cb(xs[j + 1]), yb_, zb), 0.06, "deck", v3(0, 1, 0), overlap=1.02)
    # the lifeboat's well
    rz0, rz1 = ns.LIFEBOAT_RECESS
    for x in (-1.3, 1.3):
        add_cube(bone, "boat_well_side_%d" % (x > 0), v3(x, top - 0.45, (rz0 + rz1) / 2), EYE, (0.06, 0.9, rz1 - rz0), "steel")
    for z in (rz0, rz1):
        add_cube(bone, "boat_well_end_%d" % (z > rz0), v3(0, top - 0.45, z), EYE, (2.6, 0.9, 0.06), "steel")


def superellipse(a, b, n, count, zc):
    pts = []
    for k in range(count):
        t = 2 * math.pi * k / count
        c, sn = math.cos(t), math.sin(t)
        pts.append((a * math.copysign(abs(c) ** (2 / n), c), zc + b * math.copysign(abs(sn) ** (2 / n), sn)))
    return pts


def tower_shell(bone):
    """The wheelhouse as one rounded shell (corners and roof rounded), its four windows left open."""
    a, b = ns.TOWER_HALF_WIDTH + 0.08, (ns.TOWER_Z[1] - ns.TOWER_Z[0]) / 2 + 0.08
    zc = (ns.TOWER_Z[0] + ns.TOWER_Z[1]) / 2
    plan = superellipse(a, b, ns.TOWER_SHELL_N, 64, zc)
    wy0, wy1 = ns.TOWER_WINDOWS_Y
    levels = [ns.CASING_TOP_Y, wy0, wy1, ns.TOWER_TOP_Y]
    sections = [[v3(x, yy, z) for x, z in plan] for yy in levels]

    def window(i, j, mid):
        if i != 1:
            return False
        front = mid[2] > zc + b * 0.85 and any(x0 - 0.05 < mid[0] < x1 + 0.05 for x0, x1 in ns.TOWER_FRONT_WINDOWS_X)
        side = abs(mid[0]) > a * 0.85 and ns.TOWER_SIDE_WINDOW_Z[0] - 0.05 < mid[2] < ns.TOWER_SIDE_WINDOW_Z[1] + 0.05
        return front or side
    centre = lambda p: v3(0, p[1], zc)
    loft(bone, "tower_wall", sections, "hull_light", centre, closed=True, skip=window)
    # the roof, gently domed
    roof = []
    for k, (sc, dyr) in enumerate(((1.0, 0.0), (0.96, 0.25), (0.86, 0.5), (0.68, 0.72), (0.42, 0.86), (0.04, 0.92))):
        roof.append([v3(x * sc, ns.TOWER_TOP_Y + dyr, zc + (z - zc) * sc) for x, z in plan])
    loft(bone, "tower_roof", roof, "hull_light", lambda p: v3(0, ns.TOWER_TOP_Y - 2.0, zc), closed=True)
    # riveted vertical straps between the windows
    for k in range(0, len(plan), 8):
        x, z = plan[k]
        mid = v3(x, (ns.CASING_TOP_Y + ns.TOWER_TOP_Y) / 2, z)
        if window(1, k, v3(x * 0.99, (wy0 + wy1) / 2, z)):
            continue
        out = norm(v3(x, 0, z - zc))
        beam(bone, "tower_strap_%d" % k, v3(x, ns.CASING_TOP_Y + 0.1, z) + out * 0.06, v3(x, ns.TOWER_TOP_Y - 0.05, z) + out * 0.06, 0.05, "seam",
             width=0.16, up=out)
    # brass bands at the foot and under the roof
    for yy, tag in ((ns.CASING_TOP_Y + 0.08, "foot"), (ns.TOWER_TOP_Y - 0.05, "eave")):
        for k in range(len(plan)):
            (x0, z0), (x1, z1) = plan[k], plan[(k + 1) % len(plan)]
            beam(bone, "tower_band_%s_%d" % (tag, k), v3(x0 * 1.02, yy, zc + (z0 - zc) * 1.02), v3(x1 * 1.02, yy, zc + (z1 - zc) * 1.02),
                 0.14, "brass", width=0.1)


def aft_fairing(bone):
    """The fairing that slopes down from the back of the wheelhouse roof to the casing deck (the
    diagonal behind the wheelhouse in the reference sheet): a rounded hood of plating, riveted ribs
    across it, a ridge with small spikes, a handrail up its side and a vent cowl."""
    z0, z1 = ns.AFT_FAIRING_Z
    zs = np.linspace(z0, z1, 14)
    n = 20
    sections = []
    for z in zs:
        w, top = ns.aft_fairing(z)
        h = max(0.05, top - ns.CASING_TOP_Y)
        ring_ = []
        for k in range(n + 1):
            t = math.pi * k / n
            c, s_ = math.cos(t), math.sin(t)
            ring_.append(v3(w * math.copysign(abs(c) ** (2 / 3), c), ns.CASING_TOP_Y + h * abs(s_) ** (2 / 3), z))
        sections.append(ring_)
    loft(bone, "aft_fairing", sections, "hull_light", lambda p: v3(0, ns.CASING_TOP_Y, p[2]))
    # its ribs, every other section, and the ridge
    for i in range(1, len(zs) - 1, 2):
        for k in range(n):
            beam(bone, "aft_fairing_rib_%d_%d" % (i, k), sections[i][k] + v3(0, 0.03, 0), sections[i][k + 1] + v3(0, 0.03, 0), 0.05, "seam",
                 width=0.14, extend=0.02)
    for i in range(len(zs) - 1):
        a_, b_ = sections[i][n // 2], sections[i + 1][n // 2]
        beam(bone, "aft_fairing_ridge_%d" % i, a_ + v3(0, 0.06, 0), b_ + v3(0, 0.06, 0), 0.12, "brass", width=0.18, extend=0.03)
        if i % 2 == 1:
            spike(bone, "aft_fairing_spike_%d" % i, (a_ + b_) / 2 + v3(0, 0.08, 0), v3(0, 1, -0.4), 0.55, 0.24)
    # a handrail up the starboard side, on stanchions
    pts = []
    for z in np.linspace(z0 + 0.6, z1 - 0.4, 5):
        w, top = ns.aft_fairing(z)
        pts.append(v3(-w * 0.75, ns.CASING_TOP_Y + (top - ns.CASING_TOP_Y) * 0.78, z))
    for k, q in enumerate(pts):
        beam(bone, "aft_fairing_post_%d" % k, q, q + v3(-0.1, 0.55, 0), 0.06, "brass")
        if k:
            beam(bone, "aft_fairing_rail_%d" % k, pts[k - 1] + v3(-0.1, 0.55, 0), q + v3(-0.1, 0.55, 0), 0.06, "brass")
    # a vent cowl on the port side, turned aft
    w, top = ns.aft_fairing(z0 + 2.2)
    base = v3(w * 0.55, ns.CASING_TOP_Y + (top - ns.CASING_TOP_Y) * 0.75, z0 + 2.2)
    nf.tube(bone, "aft_vent_stem", base, base + v3(0, 0.7, 0), 0.16, 0.16, "brass", n=10)
    nf.tube(bone, "aft_vent_mouth", base + v3(0, 0.7, 0), base + v3(0, 0.95, -0.35), 0.17, 0.3, "brass", n=10)


def deck_fittings(bone):
    """On the casing deck: stanchions and a rail along both edges, mooring bollards, vent cowls."""
    top = ns.CASING_TOP_Y
    edge = ns.CASING_HALF_WIDTH - 0.2
    skip = [(ns.LIFEBOAT_RECESS[0] - 0.5, ns.LIFEBOAT_RECESS[1] + 0.5), (ns.AFT_FAIRING_Z[0] - 0.3, ns.TOWER_Z[1] + 0.3), (-10.0, -7.0)]
    zs = [z for z in np.arange(ns.CASING_Z[0] + 1.5, ns.TOWER_Z[1] + 0.5, 1.5) if not any(a <= z <= b for a, b in skip)]
    for side in SIDES:
        prev = None
        for k, z in enumerate(zs):
            p = v3(side * edge, top, z)
            beam(bone, "deck_post_%d_%d" % (side > 0, k), p, p + v3(0, 0.75, 0), 0.06, "brass")
            if prev is not None and abs(prev[2] - z) < 1.6:
                beam(bone, "deck_rail_%d_%d" % (side > 0, k), prev + v3(0, 0.75, 0), p + v3(0, 0.75, 0), 0.05, "brass")
                beam(bone, "deck_rail_low_%d_%d" % (side > 0, k), prev + v3(0, 0.4, 0), p + v3(0, 0.4, 0), 0.04, "iron")
            prev = p
    for k, z in enumerate((-23.5, -12.0, -3.0, 5.0)):
        for side in SIDES:
            c = v3(side * 1.1, top, z)
            nf.tube(bone, "bollard_%d_%d" % (k, side > 0), c, c + v3(0, 0.35, 0), 0.14, 0.12, "steel", n=8)
            nf.ellipsoid(bone, "bollard_cap_%d_%d" % (k, side > 0), c + v3(0, 0.38, 0), (0.18, 0.06, 0.18), EYE, "steel", nlat=2, nlon=8)
    for k, (x, z) in enumerate(((1.2, -5.0), (-1.2, 2.0))):
        c = v3(x, top, z)
        nf.tube(bone, "deck_vent_%d" % k, c, c + v3(0, 0.6, 0), 0.15, 0.15, "brass", n=10)
        nf.tube(bone, "deck_vent_mouth_%d" % k, c + v3(0, 0.6, 0), c + v3(0, 0.85, 0.3), 0.16, 0.28, "brass", n=10)


def wheelhouse_lining(bone):
    """The inside of the wheelhouse, rounded as in panel 6: a smooth wall of dark panelling following its
    plan, with the four windows left open (their octagonal frames are set on it, see windows())."""
    a, b, n = ns.WHEELHOUSE_PLAN
    zc = (ns.TOWER_Z[0] + ns.TOWER_Z[1]) / 2
    plan = superellipse(a + 0.02, b + 0.02, n, 48, zc)
    wy0, wy1 = ns.TOWER_WINDOWS_Y
    levels = [ns.CASING_TOP_Y, wy0, wy1, ns.TOWER_TOP_Y - 0.5]
    sections = [[v3(x, yy, z) for x, z in plan] for yy in levels]

    def window(i, j, mid):
        if i != 1:
            return False
        front = mid[2] > zc + b * 0.8 and any(x0 - 0.05 < mid[0] < x1 + 0.05 for x0, x1 in ns.TOWER_FRONT_WINDOWS_X)
        side = abs(mid[0]) > a * 0.8 and ns.TOWER_SIDE_WINDOW_Z[0] - 0.05 < mid[2] < ns.TOWER_SIDE_WINDOW_Z[1] + 0.05
        return front or side
    loft(bone, "lit_wheelhouse_lining", sections, "wall_wood", lambda p: v3(0, p[1], zc), closed=True, skip=window)
    # a skirting board and a brass rail round it
    for yy, region, w in ((ns.CASING_TOP_Y + 0.12, "organ_wood", 0.24), (wy0 - 0.12, "brass", 0.06)):
        for k in range(len(plan)):
            (x0, z0), (x1, z1) = plan[k], plan[(k + 1) % len(plan)]
            mid = v3((x0 + x1) / 2, yy, (z0 + z1) / 2)
            if region == "brass" and window(1, k, v3(mid[0], (wy0 + wy1) / 2, mid[2])):
                continue
            beam(bone, "lit_wheelhouse_%s_%d" % ("skirt" if region != "brass" else "rail", k), v3(x0 * 0.985, yy, zc + (z0 - zc) * 0.985),
                 v3(x1 * 0.985, yy, zc + (z1 - zc) * 0.985), w, region, width=0.06)


def cage_hood(bone):
    """The projector's lantern on the wheelhouse roof (reference sheet: a small round housing over the
    wheelhouse, the lens looking ahead): a copper drum with brass bands, a domed cap with its vent, the
    lens in a heavy brass ring at the front."""
    r = ns.LAMP_CAGE_HALF_WIDTH
    zc = (ns.LAMP_CAGE_Z[0] + ns.LAMP_CAGE_Z[1]) / 2
    y0, y1 = ns.TOWER_TOP_Y + 0.3, ns.LAMP_CAGE_TOP_Y - 0.45
    n = 28
    lens_a = ns.LENS_Y
    def ring_pts(y, rr):
        return [v3(math.sin(2 * math.pi * k / n) * rr, y, zc + math.cos(2 * math.pi * k / n) * rr) for k in range(n)]
    ys = np.linspace(y0, y1, 6)
    sections = [ring_pts(y, r) for y in ys]
    def lens_hole(i, j, mid):
        return mid[2] > zc + r * 0.6 and abs(mid[0]) < 0.62 and abs(mid[1] - lens_a) < 0.62
    loft(bone, "lantern_drum", sections, "hull_light", lambda p: v3(0, p[1], zc), closed=True, skip=lens_hole)
    cap = [ring_pts(y1 + 0.45 * math.sin(t), r * math.cos(t) + 0.02) for t in np.linspace(0, math.pi / 2 - 0.08, 5)]
    loft(bone, "lantern_cap", cap, "hull_light", lambda p: v3(0, y1 - 1.0, zc), closed=True)
    for yy, tag in ((y0 + 0.05, "foot"), (y1, "eave"), ((y0 + y1) / 2 - 0.55, "mid")):
        ring(bone, "lantern_band_%s" % tag, v3(0, yy, zc), v3(0, 1, 0), r + 0.04, 0.12, "brass", n=n, width=0.1)
    add_cube(bone, "lantern_vent", v3(0, ns.LAMP_CAGE_TOP_Y + 0.02, zc), ry(math.pi / 4), (0.3, 0.16, 0.3), "brass")
    add_cube(bone, "lantern_vent_top", v3(0, ns.LAMP_CAGE_TOP_Y + 0.14, zc), EYE, (0.4, 0.05, 0.4), "brass")
    # a skirt down to the domed roof of the wheelhouse
    skirt = [ring_pts(y, r + 0.12 * (1 - (y - ns.TOWER_TOP_Y + 0.2) / 0.6)) for y in np.linspace(ns.TOWER_TOP_Y - 0.2, y0 + 0.05, 3)]
    loft(bone, "lantern_skirt", skirt, "hull_light", lambda p: v3(0, p[1], zc), closed=True)


SEAM_AZ_STEP = 3      # a longitudinal seam every 3 panels round the hull
SEAM_Z = 2.0          # a ring of butt straps every 2 blocks along it


def hull_seams(bone):
    """The plating of the hull as in the reference sheet: large plates (about 3 blocks long) outlined by
    riveted straps standing a little proud of the skin, without the panel-by-panel grid; and the belt,
    a heavy riveted strake along each side under the great windows."""
    z0, z1 = hull_z(-0.95), hull_z(0.93)
    zs = np.linspace(z0, z1, 90)
    n = 0
    for j in range(0, NAZ, SEAM_AZ_STEP):
        az = 360.0 * j / NAZ
        if abs(((az + 180) % 360) - 180) < 30:
            continue  # under the casing
        for i in range(len(zs) - 1):
            a, b = P(zs[i], az, 0.05), P(zs[i + 1], az, 0.05)
            if in_window(a, 0.45) or in_window(b, 0.45):
                continue
            beam(bone, "seam_l_%d_%d" % (j, i), a, b, 0.05, "seam" if math.cos(math.radians(az)) > -0.12 else "seam_dark", width=0.14, up=norm(a - v3(0, ns.AXIS_Y, a[2])), extend=0.02)
            n += 1
    for zc in np.arange(math.ceil(z0 / SEAM_Z) * SEAM_Z, z1, SEAM_Z):
        for j in range(0, NAZ, 2):
            a0, a1 = 360.0 * j / NAZ, 360.0 * (j + 2) / NAZ
            if abs(((a0 + 180) % 360) - 180) < 30 or abs(((a1 + 180) % 360) - 180) < 30:
                continue
            a, b = P(zc, a0, 0.05), P(zc, a1, 0.05)
            if in_window(a, 0.45) or in_window(b, 0.45) or in_window((a + b) / 2, 0.45):
                continue
            dark = math.cos(math.radians((a0 + a1) / 2)) <= -0.12
            beam(bone, "seam_r_%d_%d" % (int(zc * 10), j), a, b, 0.05, "seam_dark" if dark else "seam", width=0.14, up=norm((a + b) / 2 - v3(0, ns.AXIS_Y, zc)),
                 extend=0.02)
            n += 1
    # the belt
    for side in SIDES:
        az = 97.0 if side > 0 else 263.0
        for i in range(len(zs) - 1):
            a, b = P(zs[i], az, 0.1), P(zs[i + 1], az, 0.1)
            if in_window(a, 0.45) or in_window(b, 0.45):
                continue
            beam(bone, "belt_%d_%d" % (side > 0, i), a, b, 0.14, "seam", width=0.3, up=norm(a - v3(0, ns.AXIS_Y, a[2])), extend=0.03)
            n += 1
    return n


def hull_details(bone, lights):
    """What the reference sheet shows along both flanks: the bow diving planes, a row of small
    rectangular deadlights high on the hull, the gilded N of the Nautilus near the bow, the navigation
    lights (red to port, green to starboard) on the wheelhouse."""
    for side in SIDES:
        sn = "p" if side > 0 else "s"
        # bow diving planes: a rounded fin on a pivot boss
        zp = ns.BOW_Z - 9.0
        hp, nrm = on_hull(zp, ns.AXIS_Y - 0.6, side, 0.0)
        nf.ellipsoid(bone, "plane_%s" % sn, hp + v3(side * 1.05, 0, 0), (1.15, 0.09, 0.85), EYE, "plate_dark", nlat=3, nlon=16)
        nf.ellipsoid(bone, "plane_boss_%s" % sn, hp + v3(side * 0.05, 0, 0), (0.25, 0.3, 0.3), EYE, "brass", nlat=3, nlon=10)
        beam(bone, "plane_edge_%s" % sn, hp + v3(side * 0.3, 0, 0.75), hp + v3(side * 1.95, 0, 0.3), 0.06, "brass", width=0.08)
        # deadlights: small rectangular windows in brass frames, high on the hull
        for z in np.arange(-30.0, 40.0, 4.0):
            yy = ns.AXIS_Y + ns.half_height(z) * 0.6
            p_, n_ = on_hull(z, yy, side, 0.05)
            if in_window(p_, 0.6) or abs(z) < 4.5 or ns.TOWER_Z[0] - 1 < z < ns.TOWER_Z[1] + 1:
                continue
            R = np.column_stack([v3(0, 0, 1), norm(np.cross(n_, v3(0, 0, 1))) * (1 if side < 0 else -1), n_])
            if np.linalg.det(R) < 0:
                R[:, 1] = -R[:, 1]
            add_cube(bone, "deadlight_%s_%d" % (sn, int(z * 10)), p_, R, (0.6, 0.36, 0.04), "glass")
            for k, (dz, dv, sz, sv) in enumerate(((0, 0.22, 0.76, 0.08), (0, -0.22, 0.76, 0.08), (0.34, 0, 0.08, 0.36), (-0.34, 0, 0.08, 0.36))):
                add_cube(bone, "deadlight_%s_%d_f%d" % (sn, int(z * 10), k), p_ + R[:, 0] * dz + R[:, 1] * dv + n_ * 0.03, R, (sz, sv, 0.07),
                         "brass")
        # the N, gilded, in a ring near the bow
        zn = ns.BOW_Z - 4.5
        c, n_ = on_hull(zn, ns.AXIS_Y + 1.4, side, 0.08)
        ring(bone, "emblem_ring_%s" % sn, c, n_, 0.55, 0.08, "gold", n=20, width=0.1)
        e_up = norm(v3(0, 1, 0) - n_ * n_[1])
        e_al = norm(np.cross(e_up, n_)) * (-1 if side > 0 else 1)
        for k, (a_, b_) in enumerate((((-0.2, -0.28), (-0.2, 0.28)), ((-0.2, 0.28), (0.2, -0.28)), ((0.2, -0.28), (0.2, 0.28)))):
            pa = c + n_ * 0.04 + e_al * a_[0] + e_up * a_[1]
            pb = c + n_ * 0.04 + e_al * b_[0] + e_up * b_[1]
            beam(bone, "emblem_n_%s_%d" % (sn, k), pa, pb, 0.05, "gold", width=0.09, up=n_, extend=0.03)
        # the great window of the salon in an octagonal bronze plate, riveted, with a cross of ribs
        wz, wy, wr = ns.SALON_WINDOW
        c0, n0 = on_hull(wz, wy, side, 0.1)
        e_up = norm(v3(0, 1, 0) - n0 * n0[1])
        e_al = v3(0, 0, 1)
        for k in range(8):
            a0, a1 = 2 * math.pi * (k + 0.5) / 8, 2 * math.pi * (k + 1.5) / 8
            def oc(a, rr):
                return c0 + (e_al * math.cos(a) + e_up * math.sin(a)) * rr
            panel(bone, "salon_octa_%s_%d" % (sn, k), oc(a0, wr - 0.05), oc(a1, wr - 0.05), oc(a0, wr + 1.0), oc(a1, wr + 1.0), 0.12,
                  "plate_dark", n0, overlap=1.02)
            beam(bone, "salon_octa_rim_%s_%d" % (sn, k), oc(a0, wr + 1.05) + n0 * 0.05, oc(a1, wr + 1.05) + n0 * 0.05, 0.12, "brass",
                 width=0.16, up=n0, extend=0.06)
            for q in range(3):
                t = (q + 0.5) / 3
                add_cube(bone, "salon_octa_rivet_%s_%d_%d" % (sn, k, q), oc(a0, wr + 0.85) * (1 - t) + oc(a1, wr + 0.85) * t + n0 * 0.08, EYE,
                         (0.08, 0.08, 0.08), "brass")
        for k in range(4):  # a thin brass cross over the glass, as in the reference sheet
            a = math.pi / 2 * k + math.pi / 4
            beam(bone, "salon_glass_bar_%s_%d" % (sn, k), c0 + n0 * 0.02, c0 + (e_al * math.cos(a) + e_up * math.sin(a)) * (wr - 0.1) + n0 * 0.02,
                 0.06, "brass", width=0.08, up=n0)
        ring(bone, "salon_glass_hub_%s" % sn, c0 + n0 * 0.03, n0, 0.45, 0.06, "brass", n=16, width=0.08)
        for k in range(4):
            a = math.pi / 2 * k
            beam(bone, "salon_cross_%s_%d" % (sn, k), c0 + (e_al * math.cos(a) + e_up * math.sin(a)) * (wr + 1.0) + n0 * 0.08,
                 c0 + (e_al * math.cos(a) + e_up * math.sin(a)) * (wr + 2.0) + n0 * 0.02, 0.14, "brass", width=0.22, up=n0)
        # a row of rectangular windows low on the hull, in brass frames
        for z in np.arange(-28.0, 38.0, 5.0):
            yy = ns.AXIS_Y - ns.half_height(z) * 0.62
            p_, n_ = on_hull(z, yy, side, 0.05)
            if in_window(p_, 0.6) or abs(z) < 4.0:
                continue
            u_ = v3(0, 0, 1)
            w_ = norm(np.cross(n_, u_))
            R = np.column_stack([u_, w_, np.cross(u_, w_)])
            add_cube(bone, "lowlight_%s_%d" % (sn, int(z * 10)), p_, R, (0.9, 0.4, 0.04), "glass")
            for k, (dz, dv, sz, sv) in enumerate(((0, 0.24, 1.06, 0.08), (0, -0.24, 1.06, 0.08), (0.49, 0, 0.08, 0.4), (-0.49, 0, 0.08, 0.4),
                                                  (0, 0, 0.05, 0.4))):
                add_cube(bone, "lowlight_%s_%d_f%d" % (sn, int(z * 10), k), p_ + u_ * dz + w_ * dv + n_ * 0.03, R, (sz, sv, 0.07), "brass")
        # a lamp on each front corner of the wheelhouse, and on each side of the bow (front view of the sheet)
        for k, lp in enumerate((v3(side * 2.15, ns.TOWER_TOP_Y - 0.45, ns.TOWER_Z[1] - 0.35),
                                on_hull(ns.BOW_Z - 7.0, ns.AXIS_Y + 1.2, side, 0.45)[0])):
            nf.ellipsoid(lights, "glow_front_lamp_%s%d" % (sn, k), lp, (0.26, 0.26, 0.26), EYE, "glow", nlat=3, nlon=10)
            ring(bone, "front_lamp_cage_%s%d" % (sn, k), lp, v3(0, 0, 1), 0.3, 0.05, "brass", n=12, width=0.05)
            ring(bone, "front_lamp_cage_h_%s%d" % (sn, k), lp, v3(0, 1, 0), 0.3, 0.05, "brass", n=12, width=0.05)
            back = lp - v3(side * 0.4, 0, 0) if k == 1 else lp - v3(side * 0.3, 0, 0.1)
            beam(bone, "front_lamp_bracket_%s%d" % (sn, k), lp - v3(side * 0.26, 0, 0), back, 0.08, "brass")
        # navigation light on the wheelhouse side, in its brass box
        zl = ns.TOWER_Z[0] + 1.2
        pl = v3(side * (ns.TOWER_HALF_WIDTH + 0.12), ns.TOWER_TOP_Y - 0.9, zl)
        add_cube(bone, "navlight_box_%s" % sn, pl, EYE, (0.2, 0.42, 0.42), "brass")
        add_cube(lights, "glow_navlight_%s" % sn, pl + v3(side * 0.11, 0, 0), EYE, (0.04, 0.3, 0.3), "coral_red" if side > 0 else "green_leather")


def bow_blade_foot(z):
    """Foot of the cutwater under the bow at z (it deepens towards the bow, then rises to the ram)."""
    if z <= ns.BOW_Z:
        return ns.hull_bottom(max(z, 26.0)) - 0.9 * smoothstep((z - 26.0) / (ns.BOW_Z - 26.0))
    t = min(1.0, (z - ns.BOW_Z) / 3.0)
    return bow_blade_foot(ns.BOW_Z) * (1 - t) + (ns.AXIS_Y - 0.45) * t


def bow_blade(bone):
    """The cutwater under the bow (front view of the sheet): a deep blade from under the hull to the
    ram, a brass edge along its foot."""
    zs = np.linspace(26.0, ns.BOW_Z + 3.0, 16)
    foot = bow_blade_foot

    def head(z):
        return min(ns.AXIS_Y - 0.2, ns.hull_bottom(z) + 0.6) if z <= ns.BOW_Z else ns.AXIS_Y - 0.25
    for k in range(len(zs) - 1):
        za, zb = zs[k], zs[k + 1]
        panel(bone, "bow_blade_%d" % k, v3(0, head(za), za), v3(0, foot(za), za), v3(0, head(zb), zb), v3(0, foot(zb), zb), 0.22, "plate_dark",
              v3(1, 0, 0), overlap=1.03)
        beam(bone, "bow_blade_edge_%d" % k, v3(0, foot(za), za), v3(0, foot(zb), zb), 0.14, "brass", width=0.26, up=v3(1, 0, 0), extend=0.03)
    return foot


def prop_shroud(bone):
    """A ring round the propeller on four struts from the tail cone (rear view of the sheet)."""
    y = ns.AXIS_Y
    r = ns.PROP_R + 0.3
    n = 36
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        def C(z, a):
            return v3(math.sin(a) * r, y + math.cos(a) * r, z)
        panel(bone, "prop_shroud_%d" % k, C(ns.PROP_Z + 0.35, a0), C(ns.PROP_Z + 0.35, a1), C(ns.PROP_Z - 0.35, a0), C(ns.PROP_Z - 0.35, a1), 0.12,
              "plate_dark", v3(math.sin((a0 + a1) / 2), math.cos((a0 + a1) / 2), 0), overlap=1.04)
    for z in (ns.PROP_Z + 0.38, ns.PROP_Z - 0.38):
        ring(bone, "prop_shroud_rim_%d" % (z > ns.PROP_Z), v3(0, y, z), v3(0, 0, 1), r, 0.1, "brass", n=n, width=0.1)
    # the tail boss behind the propeller, on which the fins stand, and tie rods from the ring to the fins
    zb0, zb1 = ns.PROP_Z - 0.55, ns.FIN_NOTCH_Z - 0.4
    nf.tube(bone, "tail_boss", v3(0, y, zb0), v3(0, y, zb1), 0.75, 0.32, "plate_dark", n=16)
    nf.ellipsoid(bone, "tail_boss_cap", v3(0, y, zb1), (0.32, 0.32, 0.5), EYE, "brass", nlat=3, nlon=12, lat0=-90.0, lat1=90.0)
    for zz in (zb0 + 0.3, (zb0 + zb1) / 2):
        rr = 0.75 + (0.32 - 0.75) * (zz - zb0) / (zb1 - zb0)
        ring(bone, "tail_boss_ring_%d" % int(-zz * 10), v3(0, y, zz), v3(0, 0, 1), rr + 0.04, 0.12, "brass", n=16, width=0.12)
    for k in (0, 2):  # the two lobes, above and below
        a = k * math.pi / 2
        d = v3(math.sin(a), math.cos(a), 0)
        beam(bone, "fin_tie_%d" % k, v3(0, y, ns.PROP_Z - 0.38) + d * r, v3(0, y, ns.FIN_Z0 - 0.2) + d * (r + 0.6), 0.16, "plate_dark", width=0.22,
             up=v3(0, 0, 1))
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        d = v3(math.sin(a), math.cos(a), 0)
        beam(bone, "prop_strut_%d" % k, v3(0, y, ns.TAIL_CONE_Z + 0.4) + d * 0.6, v3(0, y, ns.PROP_Z + 0.3) + d * (r - 0.05), 0.14, "steel",
             width=0.2, up=v3(0, 0, 1))


def tail(bone, root):
    y = ns.AXIS_Y
    # cone with rings from the end of the hull to the propeller
    zs = np.linspace(ns.STERN_Z + 2.0, ns.TAIL_CONE_Z, 6)
    rs = np.linspace(1.6, 0.5, 6)
    for k in range(len(zs) - 1):
        for j in range(24):
            a0, a1 = 15.0 * j, 15.0 * (j + 1)
            am = math.radians((a0 + a1) / 2)
            outward = v3(math.sin(am), math.cos(am), 0)

            def C(z, r, a):
                return v3(math.sin(math.radians(a)) * r, y + math.cos(math.radians(a)) * r, z)
            panel(bone, "tail_cone_%d_%d" % (k, j), C(zs[k], rs[k], a0), C(zs[k], rs[k], a1), C(zs[k + 1], rs[k + 1], a0),
                  C(zs[k + 1], rs[k + 1], a1), 0.1, "plate_dark", outward)
        ring(bone, "tail_ring_%d" % k, v3(0, y, zs[k]), v3(0, 0, 1), rs[k] + 0.05, 0.16, "brass", n=24, width=0.22)
    beam(bone, "shaft", v3(0, y, ns.TAIL_CONE_Z + 0.3), v3(0, y, ns.PROP_Z - 0.6), 0.36, "steel")
    prop = Bone("propeller", origin=(0, y, ns.PROP_Z), parent=root)
    hub = v3(0, y, ns.PROP_Z)
    nf.ellipsoid(prop, "prop_hub", hub, (0.45, 0.45, 0.4), EYE, "brass", nlat=4, nlon=12)
    nf.ellipsoid(prop, "prop_cap", hub + v3(0, 0, -0.35), (0.3, 0.3, 0.35), EYE, "brass", nlat=3, nlon=12, lat0=-90.0, lat1=90.0)
    pitch = math.radians(28)
    for k in range(4):
        a = 2 * math.pi * k / 4 + math.pi / 4
        d = v3(math.sin(a), math.cos(a), 0)
        side = np.cross(v3(0, 0, 1), d)
        w = side * math.cos(pitch) + v3(0, 0, 1) * math.sin(pitch)
        n = np.cross(d, w)
        axes = np.column_stack([d, w, n])
        # a twisted blade: the pitch eases off and the chord swells then narrows towards the tip
        for q, (r0, r1, ch, pt) in enumerate(((0.4, 1.0, 0.6, 34), (1.0, 1.6, 1.0, 30), (1.6, 2.2, 1.25, 26), (2.2, 2.7, 1.15, 22),
                                              (2.7, ns.PROP_R, 0.75, 18))):
            pr = math.radians(pt)
            wq = side * math.cos(pr) + v3(0, 0, 1) * math.sin(pr)
            ax = np.column_stack([d, wq, np.cross(d, wq)])
            add_cube(prop, "prop_blade_%d_%d" % (k, q), hub + d * ((r0 + r1) / 2), ax, (r1 - r0 + 0.04, ch, 0.12 - 0.015 * q), "brass")
    # fish-tail fin (vertical lobes) and the horizontal fins, as strips between the swept edges
    def lobes(name, axis_dir, top, le_fn=None):
        span = abs(top)
        for k, f in enumerate(np.arange(0.25, span, 0.5)):
            le = ns.FIN_Z0 - max(0.0, f - 1.0) / (span - 1.0) * (ns.FIN_Z0 - ns.FIN_TIP_LE_Z)
            te = ns.FIN_NOTCH_Z - f / span * (ns.FIN_NOTCH_Z - ns.FIN_TIP_TE_Z)
            pass
        # the lobe as one smooth plate, thick at the root and thin at the tip, its strips following
        # the swept edges (no steps)
        normal = v3(1, 0, 0) if axis_dir[1] else v3(0, 1, 0)
        fs = np.linspace(0.6, span, 20)

        def edges(f):
            le = ns.FIN_Z0 - max(0.0, f - 1.0) / (span - 1.0) * (ns.FIN_Z0 - ns.FIN_TIP_LE_Z)
            if le_fn is not None:
                le = min(ns.FIN_Z0, le_fn(f))
            te = ns.FIN_NOTCH_Z - f / span * (ns.FIN_NOTCH_Z - ns.FIN_TIP_TE_Z)
            c = v3(0, y, 0) + axis_dir * math.copysign(f, top)
            return c + v3(0, 0, le), c + v3(0, 0, te)
        # each strip an airfoil: two skins bulging out from the leading to the trailing edge
        cs = (0.0, 0.12, 0.3, 0.55, 0.8, 1.0)
        half = (0.0, 0.7, 1.0, 0.85, 0.45, 0.08)
        for k in range(len(fs) - 1):
            a_le, a_te = edges(fs[k])
            b_le, b_te = edges(fs[k + 1])
            ta = 0.3 - 0.18 * (fs[k] / span)
            tb = 0.3 - 0.18 * (fs[k + 1] / span)
            for sgn in (1, -1):
                for i in range(len(cs) - 1):
                    def pt(le, te, t, c, h):
                        return le + (te - le) * c + normal * (sgn * t * h)
                    panel(bone, "%s_%d_%d_%d" % (name, k, sgn > 0, i), pt(a_le, a_te, ta, cs[i], half[i]), pt(a_le, a_te, ta, cs[i + 1], half[i + 1]),
                          pt(b_le, b_te, tb, cs[i], half[i]), pt(b_le, b_te, tb, cs[i + 1], half[i + 1]), 0.04, "hull_light", normal * sgn,
                          overlap=1.04)
        # brass ribs fanning out over both faces of the lobe
        for c_ in (0.3, 0.55, 0.8):
            a_le, a_te = edges(fs[0])
            b_le, b_te = edges(fs[-1])
            ra, rb = a_le + (a_te - a_le) * c_, b_le + (b_te - b_le) * c_
            for sgn in (1, -1):
                beam(bone, "%s_rib_%d_%d" % (name, int(c_ * 100), sgn > 0), ra + normal * (sgn * 0.2), rb + normal * (sgn * 0.08), 0.06, "brass",
                     width=0.1, up=normal)
        for f in fs[2::3]:  # riveted butt straps across the lobe
            le, te = edges(f)
            for sgn in (1, -1):
                beam(bone, "%s_strap_%d_%d" % (name, int(f * 10), sgn > 0), le + normal * (sgn * 0.17), te + normal * (sgn * 0.05), 0.04, "seam",
                     width=0.14, up=normal * sgn)
        tip_le = v3(0, y, ns.FIN_TIP_LE_Z) + axis_dir * top
        tip_te = v3(0, y, ns.FIN_TIP_TE_Z) + axis_dir * top
        root_le = v3(0, y, ns.FIN_Z0) + axis_dir * math.copysign(1.0, top)
        notch = v3(0, y, ns.FIN_NOTCH_Z)
        beam(bone, name + "_leading", root_le, tip_le, 0.34, "plate_dark", width=0.34)
        beam(bone, name + "_tip", tip_le, tip_te, 0.3, "plate_dark", width=0.3)
        beam(bone, name + "_trailing", notch, tip_te, 0.26, "plate_dark", width=0.26)
    skeg_za = -31.0
    skeg_ya = ns.hull_top(skeg_za) - y

    def skeg_z(tip):  # the z of the skeg's leading edge at a height f above (below) the axis
        return lambda f: skeg_za + (f - skeg_ya) / (tip - skeg_ya) * (ns.FIN_TIP_LE_Z - skeg_za)
    lobes("fin_top", v3(0, 1, 0), ns.FIN_TOP, skeg_z(ns.FIN_TOP))
    lobes("fin_bottom", v3(0, 1, 0), ns.FIN_BOTTOM, skeg_z(-ns.FIN_BOTTOM))
    # only the two lobes of the fish tail, as in the reference sheet; they grow out of the hull: a skeg
    # above and one below carry the line of the back and of the belly over the propeller ring to the
    # leading edge of each lobe
    cone_z0, cone_z1 = ns.STERN_Z + 2.0, ns.TAIL_CONE_Z
    def body(z):  # radius of the hull / tail cone at z
        if z >= ns.STERN_Z + 2.0:
            return ns.hull_top(z) - y
        t = min(1.0, max(0.0, (z - cone_z0) / (cone_z1 - cone_z0)))
        return 1.6 + (0.5 - 1.6) * t
    ring_r = ns.PROP_R + 0.3
    for sgn, tip in ((1, ns.FIN_TOP), (-1, -ns.FIN_BOTTOM)):
        za = -31.0
        ya = body(za)
        def le(z):
            return ya + (tip - ya) * (z - za) / (ns.FIN_TIP_LE_Z - za)
        zs_ = list(np.linspace(za, ns.PROP_Z + 0.4, 26)) + [ns.PROP_Z, ns.PROP_Z - 0.4, ns.FIN_Z0 + 0.05]
        for k in range(len(zs_) - 1):
            z0_, z1_ = zs_[k], zs_[k + 1]
            over_ring = z0_ <= ns.PROP_Z + 0.4 + 1e-6 and z0_ >= ns.PROP_Z + 0.4 - 1e-6 or z0_ < ns.PROP_Z + 0.39
            lo0 = ring_r + 0.15 if over_ring else body(z0_) - 0.1
            lo1 = ring_r + 0.15 if over_ring else body(z1_) - 0.1
            a0, a1 = v3(0, y + sgn * lo0, z0_), v3(0, y + sgn * le(z0_), z0_)
            b0, b1 = v3(0, y + sgn * lo1, z1_), v3(0, y + sgn * le(z1_), z1_)
            panel(bone, "skeg_%d_%d" % (sgn > 0, k), a0, a1, b0, b1, 0.26, "hull_light", v3(1, 0, 0), overlap=1.03)
            beam(bone, "skeg_edge_%d_%d" % (sgn > 0, k), a1, b1, 0.3, "plate_dark", width=0.32, up=v3(1, 0, 0), extend=0.04)
            for sd in (1, -1):
                beam(bone, "skeg_strap_%d_%d_%d" % (sgn > 0, k, sd > 0), (a0 + a1) / 2 + v3(sd * 0.14, 0, 0), (b0 + b1) / 2 + v3(sd * 0.14, 0, 0),
                     0.03, "seam", width=0.14, up=v3(sd, 0, 0))


# ---------------------------------------------------------------- surfaces of the grid
OPEN_KINDS = (ni.DRY, ni.LADDER, ni.AIRLOCK)
MAX_TILE = 4  # cells (2 blocks): the texture regions are 32 px

LUX = ("wall_lux", "floor_lux", "ceil_lux")
STEEL = ("wall_steel", "floor_grate", "ceil_steel")
ROOM_MATERIALS = {
    "salon": LUX, "library": LUX, "dining": LUX, "cabin_aronnax": LUX,
    "corridor_fore": ("wall_wood", "carpet", "ceil_wood"), "coursive": ("wall_steel", "carpet", "ceil_steel"),
    "cabin_nemo": ("wall_wood", "floor", "ceil_wood"), "wheelhouse": ("wall_engine", "floor", "ceil_wood"),
    "crew": ("wall_wood", "floor", "ceil_wood"), "store_port": ("wall_steel", "floor", "ceil_steel"),
    "store_stbd": ("wall_steel", "floor", "ceil_steel"), "corridor_aft": ("wall_steel", "carpet", "ceil_steel"),
    "junction": ("wall_steel", "carpet", "ceil_steel"), "cross_fore": ("wall_steel", "carpet", "ceil_steel"),
    "kitchen": ("wall_steel", "floor_tile", "ceil_steel"), "engine_room": ("wall_engine", "floor_grate", "ceil_steel"),
    "stair_hall": ("wall_wood", "floor", "ceil_wood"), "airlock": ("wall_engine", "floor_grate", "ceil_steel"),
}


def room_at(x, y, z):
    for name, (x0, x1, y0, y1, z0, z1) in ni.ROOMS.items():
        if x0 - 0.01 <= x <= x1 + 0.01 and y0 - 0.01 <= y <= y1 + 0.01 and z0 - 0.01 <= z <= z1 + 0.01:
            return name
    return None


def greedy(mask, key, align_i=False, align_j=False):
    """Rectangles (i0, j0, i1, j1) covering a 2D mask with the same key, at most MAX_TILE cells a side;
    an aligned axis never crosses a multiple of MAX_TILE (the texture repeats there)."""
    m = mask.copy()
    out = []
    ni_, nj_ = m.shape
    for i in range(ni_):
        j = 0
        while j < nj_:
            if not m[i, j]:
                j += 1
                continue
            kk = key[i, j]
            j1 = j
            while j1 + 1 < nj_ and m[i, j1 + 1] and key[i, j1 + 1] == kk and j1 + 1 - j < MAX_TILE and not (
                    align_j and (j1 + 1) % MAX_TILE == 0):
                j1 += 1
            i1 = i
            while i1 + 1 < ni_ and i1 + 1 - i < MAX_TILE and not (align_i and (i1 + 1) % MAX_TILE == 0) and m[i1 + 1, j:j1 + 1].all() and (
                    key[i1 + 1, j:j1 + 1] == kk).all():
                i1 += 1
            m[i:i1 + 1, j:j1 + 1] = False
            out.append((i, j, i1, j1, kk))
            j = j1 + 1
    return out


def surfaces(rooms_bone, outside_bone, g):
    k = g.k
    solid = k == ni.SOLID
    opened = np.isin(k, OPEN_KINDS) | (k >= ni.DOOR) | (k == ni.WINDOW) | (k == ni.FURNITURE)
    out = k == ni.OUT
    body = g.inside(0.0)
    C = ni.CELL
    origin = (ni.X0, ni.Y0, ni.Z0)
    # material of the open cells: index into a list of (wall, floor, ceiling)
    mats = [STEEL] + list(dict.fromkeys(ROOM_MATERIALS.values()))
    mat_index = np.zeros(k.shape, dtype=np.int16)
    for x0, x1 in ((-8.0, -3.4), (3.4, 8.0)):  # the bay windows' alcoves are part of the salon
        mat_index[g.sel(x0, x1, -1.0, 6.0, -3.2, 3.2)] = mats.index(ROOM_MATERIALS["salon"])
    for name, box in ni.ROOMS.items():
        if name in ROOM_MATERIALS:
            mat_index[g.sel(*[b + d for b, d in zip(box, (-0.01, 0.01, -0.01, 0.01, -0.01, 0.01))])] = mats.index(ROOM_MATERIALS[name])
    wz, wy, wr = ns.SALON_WINDOW
    alcove = (np.abs(g.X) > 3.4) & ((g.Z - wz) ** 2 + (g.Y - wy) ** 2 < (wr + 0.15) ** 2)
    # the walls of the wheelhouse (its plan is rounded): lined by wheelhouse_lining, the grid's steps not drawn
    wheel_walls = (np.abs(g.X) < 2.6) & (g.Y > ns.CASING_TOP_Y) & (g.Y < ns.TOWER_TOP_Y) & (g.Z > ns.TOWER_Z[0] - 0.1) & \
        (g.Z < ns.TOWER_Z[1] + 0.1)
    # the tunnels of the portholes through the hull: lined by porthole_sleeves, their square sides not drawn
    tunnel = np.zeros_like(alcove)
    dry = k == ni.DRY
    for z, y in [(z, ns.SMALL_WINDOWS_Y) for z in ns.SMALL_WINDOWS_Z]:
        near = (np.abs(g.Z - z) < 0.6) & (np.abs(g.Y - y) < 0.6) & dry
        tunnel |= near & ((g.X > 4.85) | (g.X < -4.55))
    for z, y in ns.CABIN_PORTHOLES:
        tunnel |= (np.abs(g.Z - z) < 0.6) & (np.abs(g.Y - y) < 0.6) & dry & (np.abs(g.X) > 5.05)
    count = 0
    for a in range(3):
        for s in (1, -1):
            src = [slice(None)] * 3
            dst = [slice(None)] * 3
            if s > 0:
                dst[a], src[a] = slice(0, -1), slice(1, None)
            else:
                dst[a], src[a] = slice(1, None), slice(0, -1)
            nb_open = np.zeros_like(opened)
            nb_open[tuple(dst)] = opened[tuple(src)] & (k[tuple(src)] != ni.WINDOW)
            nb_out = np.zeros_like(out)
            nb_out[tuple(dst)] = out[tuple(src)]
            nb_mat = np.zeros_like(mat_index)
            nb_mat[tuple(dst)] = mat_index[tuple(src)]
            nb_tunnel = np.zeros_like(tunnel)
            nb_tunnel[tuple(dst)] = tunnel[tuple(src)]
            inner = solid & nb_open & ~alcove  # the bay windows' alcoves: lined by bay_sleeves instead
            if a != 0:
                inner &= ~nb_tunnel
            if a != 1:
                inner &= ~wheel_walls  # lined by wheelhouse_lining instead
            outer = solid & nb_out & ~body
            slot = 1 if (a == 1 and s > 0) else 2 if a == 1 else 0
            others = [b for b in range(3) if b != a]
            for layer, kind in ((inner, "lit"),):  # outside: the faired shells (casing_fairing, tower_shell...)
                key = nb_mat if kind == "lit" else np.zeros_like(nb_mat)
                for idx in range(layer.shape[a]):
                    sl = [slice(None)] * 3
                    sl[a] = idx
                    m2 = layer[tuple(sl)]
                    if not m2.any():
                        continue
                    plane = origin[a] + (idx + (1 if s > 0 else 0)) * C
                    # walls: aligned along the horizontal axis; floors and ceilings along both
                    al_i = a == 1 or a == 2
                    al_j = a == 1 or a == 0
                    for (i0, j0, i1, j1, kk) in greedy(m2, key[tuple(sl)], al_i, al_j):
                        lo, hi = [0.0] * 3, [0.0] * 3
                        b0, b1 = others
                        lo[b0], hi[b0] = origin[b0] + i0 * C, origin[b0] + (i1 + 1) * C
                        lo[b1], hi[b1] = origin[b1] + j0 * C, origin[b1] + (j1 + 1) * C
                        lo[a] = hi[a] = plane + s * 0.005
                        center = [(lo[q] + hi[q]) / 2 for q in range(3)]
                        size = [max(0.01, hi[q] - lo[q]) for q in range(3)]
                        size[a] = 0.01
                        face = ("+" if s > 0 else "-") + str(a + 1)
                        if a == 1:
                            udir, vdir = v3(1, 0, 0), v3(0, 0, 1)
                        else:
                            udir, vdir = (v3(0, 0, 1) if a == 0 else v3(1, 0, 0)), v3(0, -1, 0)
                        if kind == "lit":
                            region = mats[kk][slot]
                            cube = add_cube(rooms_bone, "lit_%s_%d" % (region, count), center, EYE, size, {face: region}, u_dir=udir, v_dir=vdir)
                            # world-aligned texture: the part of the 2-block pattern this tile covers; on a
                            # wall the pattern spans the room's height (rail and wainscot at the same height)
                            if a == 1:
                                sub = ((i0 % MAX_TILE) / MAX_TILE, (j0 % MAX_TILE) / MAX_TILE,
                                       (i1 % MAX_TILE + 1) / MAX_TILE, (j1 % MAX_TILE + 1) / MAX_TILE)
                            else:
                                hz0, hz1 = (j0, j1) if a == 0 else (i0, i1)
                                y_lo, y_hi = lo[1], hi[1]
                                room = room_at(center[0] + s * 0.3 if a == 0 else center[0], center[1],
                                               center[2] + s * 0.3 if a == 2 else center[2])
                                ry0, ry1 = (ni.ROOMS[room][2], ni.ROOMS[room][3]) if room else (y_lo, y_hi)
                                if room == "salon":
                                    ry1 = ni.SALON_TOP
                                hgt = max(0.5, ry1 - ry0)
                                v0 = min(1.0, max(0.0, (ry1 - y_hi) / hgt))
                                v1 = min(1.0, max(v0 + 0.01, (ry1 - y_lo) / hgt))
                                sub = ((hz0 % MAX_TILE) / MAX_TILE, v0, (hz1 % MAX_TILE + 1) / MAX_TILE, v1)
                            for f in cube.faces.values():
                                if f is not None:
                                    f["sub"] = sub
                        else:
                            region = "deck" if (a == 1 and s > 0) else "hull_light"
                            add_cube(outside_bone, "casing_%d" % count, center, EYE, size, {face: region}, u_dir=udir, v_dir=vdir)
                        count += 1
    return count


def ladders(bone):
    for name, (box, pillar) in ni.LADDERS.items():
        x0, x1, y0, y1, z0, z1 = box
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        if pillar is not None:
            px_, pz_ = (pillar[0] + pillar[1]) / 2, (pillar[4] + pillar[5]) / 2
        else:
            px_, pz_ = cx, z1 + 1
        if abs(px_ - cx) > abs(pz_ - cz):
            sgn = 1 if px_ > cx else -1
            wall = x1 if sgn > 0 else x0
            p_a, p_b = (lambda y: v3(wall - sgn * 0.08, y, z0 + 0.12)), (lambda y: v3(wall - sgn * 0.08, y, z1 - 0.12))
        else:
            sgn = 1 if pz_ > cz else -1
            wall = z1 if sgn > 0 else z0
            p_a, p_b = (lambda y: v3(x0 + 0.12, y, wall - sgn * 0.08)), (lambda y: v3(x1 - 0.12, y, wall - sgn * 0.08))
        beam(bone, "lit_ladder_%s_rail_a" % name, p_a(y0), p_a(y1), 0.07, "rung")
        beam(bone, "lit_ladder_%s_rail_b" % name, p_b(y0), p_b(y1), 0.07, "rung")
        y, i = y0 + 0.25, 0
        while y < y1 - 0.1:
            beam(bone, "lit_ladder_%s_rung_%d" % (name, i), p_a(y), p_b(y), 0.06, "rung")
            y += 0.5
            i += 1


def doors(root, g):
    anims = []
    for d, (name, box) in ni.DOORS.items():
        if box is None:
            m = g.k == ni.DOOR + d
            xs, ys, zs = g.X[m], g.Y[m], g.Z[m]
            h = ni.CELL / 2
            box = (xs.min() - h, xs.max() + h, ys.min() - h, ys.max() + h, zs.min() - h, zs.max() + h)
        x0, x1, y0, y1, z0, z1 = box
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        flat = sy <= min(sx, sz) + 1e-6
        if flat:
            hinge = v3((x0 + x1) / 2, y1, z0)
            axis_rot = (-110, 0, 0)
        elif sx < sz:  # door in a wall across x: hinge on its fore edge, swings about y
            hinge = v3((x0 + x1) / 2, y0, z1)
            axis_rot = (0, 100, 0)
        else:
            hinge = v3(x1, y0, (z0 + z1) / 2)
            axis_rot = (0, 100, 0)
        thin = 0.16
        if not flat and d != 9:
            # a riveted brass frame round the opening, on both faces of the wall
            along_z = sx < sz
            depth = (sx if along_z else sz) + 0.12
            w = 0.14
            p0, p1 = (z0, z1) if along_z else (x0, x1)
            for k, at in enumerate((p0 - w / 2, p1 + w / 2)):
                c = v3((x0 + x1) / 2, (y0 + y1 + w) / 2, at) if along_z else v3(at, (y0 + y1 + w) / 2, (z0 + z1) / 2)
                size = (depth, sy + w, w) if along_z else (w, sy + w, depth)
                add_cube(root, "lit_door_%d_jamb_%d" % (d, k), c, EYE, size, "brass")
            c = v3((x0 + x1) / 2, y1 + w / 2, (z0 + z1) / 2)
            size = (depth, w, sz + 2 * w) if along_z else (sx + 2 * w, w, depth)
            add_cube(root, "lit_door_%d_lintel" % d, c, EYE, size, "brass")
        faces = {"all": "steel", "+1": "door", "-1": "door", "+2": "hatch", "-2": "hatch", "+3": "door", "-3": "door"}
        if not flat and d != 9 and max(sx, sz) > 1.5:
            # a wide door: two leaves hinged on the jambs, swinging the same way
            tracks = []
            along_z = sx < sz
            for leaf, sgn in (("a", 1), ("b", -1)):
                if along_z:
                    zh = z1 if sgn > 0 else z0
                    hinge = v3((x0 + x1) / 2, y0, zh)
                    c = v3((x0 + x1) / 2, (y0 + y1) / 2, zh - sgn * sz / 4)
                    size = (thin, sy, sz / 2 - 0.02)
                else:
                    xh = x1 if sgn > 0 else x0
                    hinge = v3(xh, y0, (z0 + z1) / 2)
                    c = v3(xh - sgn * sx / 4, (y0 + y1) / 2, (z0 + z1) / 2)
                    size = (sx / 2 - 0.02, sy, thin)
                bone = Bone("door_%d_%s" % (d, leaf), origin=tuple(hinge), parent=root)
                big = ("+1", "-1") if along_z else ("+3", "-3")
                add_cube(bone, "lit_door_%d_%s" % (d, leaf), c, EYE, size, {"all": "steel", big[0]: "door_leaf", big[1]: "door_leaf"},
                         stretch=True, u_dir=v3(0, 0, 1) if along_z else v3(1, 0, 0), v_dir=v3(0, -1, 0))
                tracks.append((bone, [gg.rot_kf(0.0, (0, 0, 0)), gg.rot_kf(1.0, (0, sgn * 100, 0))]))
            anims.append(gg.animation("door_%d" % d, 1.0, "hold", tracks))
            continue
        bone = Bone("door_%d" % d, origin=tuple(hinge), parent=root)
        c = v3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        size = (sx if sx > thin * 2 else thin, sy if not flat else thin, sz if sz > thin * 2 else thin)
        if flat:
            add_cube(bone, "lit_door_%d" % d, c, EYE, size, {"all": "steel", "+2": "hatch", "-2": "hatch"}, stretch=True,
                     u_dir=v3(1, 0, 0), v_dir=v3(0, 0, 1))
        elif d == 9:
            size = (thin, sy, sz)
            add_cube(bone, "lit_door_%d" % d, c, EYE, size, {"all": "steel", "+1": "door_leaf", "-1": "door_leaf"}, stretch=True,
                     u_dir=v3(0, 0, 1), v_dir=v3(0, -1, 0))
        else:
            add_cube(bone, "lit_door_%d" % d, c, EYE, size, faces)
        anims.append(gg.animation("door_%d" % d, 1.0, "hold", [(bone, [gg.rot_kf(0.0, (0, 0, 0)), gg.rot_kf(1.0, axis_rot)])]))
    return anims


SHUTTER_SHIFT = 3.6  # the salon panels slide fore and aft along the hull by this much to open


def shutters(root, outside):
    """Iron panels outside the two great windows of the salon (Verne: they open and close like
    shutters): two flat leaves per window, in the plane tangent to the hull at the window, that meet
    at the window's centre when closed and slide fore and aft on brass rails when open (the hull is a
    cylinder there, so they keep their distance to it). Animation "shutters": 0 open .. 1 closed."""
    wz, wy, wr = ns.SALON_WINDOW
    half = wr + 0.35
    out = 0.42  # clear of the window frame
    tracks = []
    for side in SIDES:
        sn = "p" if side > 0 else "s"
        c0, n = on_hull(wz, wy, side, 0.0)
        ez = v3(0, 0, 1)
        et = norm(np.cross(n, ez))
        if et[1] < 0:
            et = -et
        R = np.column_stack([ez, et, np.cross(ez, et)])  # a rotation on both sides (n may point the other way)
        for leaf, sgn in (("fore", 1), ("aft", -1)):
            bone = Bone("shutter_%s_%s" % (sn, leaf), parent=root)
            c = c0 + n * out + ez * (sgn * half / 2)
            add_cube(bone, "shutter_%s_%s" % (sn, leaf), c, R, (half, 2 * half, 0.1), "plate")  # copper plates like the hull
            for k, t in enumerate((-0.5, 0.0, 0.5)):  # stiffeners
                add_cube(bone, "shutter_%s_%s_rib%d" % (sn, leaf, k), c + et * (t * 2 * half * 0.8) + n * 0.07, R,
                         (half - 0.1, 0.12, 0.06), "brass")
            add_cube(bone, "shutter_%s_%s_edge" % (sn, leaf), c0 + n * (out + 0.07) + ez * (sgn * 0.06), R, (0.12, 2 * half, 0.06), "brass")
            open_dz = sgn * SHUTTER_SHIFT
            tracks.append((bone, [gg.kf("position", 0.0, (0, 0, -open_dz * 16)), gg.kf("position", 1.0, (0, 0, 0))]))
        # the rails, top and bottom: from the hull out to the leaves, all along their travel
        span = 2 * (half + SHUTTER_SHIFT) + 0.2
        for tag, t in (("top", 1), ("bottom", -1)):
            edge = c0 + n * out + et * (t * (half + 0.08))
            hull_p, _ = on_hull(wz, edge[1], side, 0.0)
            gap = float(np.dot(edge - hull_p, n))
            mid = edge - n * (gap / 2)
            add_cube(outside, "shutter_rail_%s_%s" % (sn, tag), mid, R, (span, 0.16, max(0.12, gap + 0.12)), "brass")
    return [gg.animation("shutters", 1.0, "hold", tracks)]


def projector_beam(root):
    """The projector: its lens dark (off) or lit, and the beam it throws forward, a translucent cone
    fading away (tilted up a little so that it clears the wheelhouse roof)."""
    lens_c = v3(0, ns.LENS_Y, ns.LAMP_CAGE_Z[1] + 0.04)
    off = Bone("lens_off", parent=root)
    add_cube(off, "lens_glass", lens_c, EYE, (1.15, 1.15, 0.04), "glass")
    lens = Bone("fx_lens", parent=root)
    add_cube(lens, "glow_projector_lens", lens_c + v3(0, 0, 0.01), EYE, (1.15, 1.15, 0.04), "glow")
    beam_bone = Bone("fx_beam", parent=root)
    length, r0, r1, n = 34.0, 0.5, 3.4, 10
    tilt = math.atan((r1 - r0) / length)  # the lower edge stays level
    axis = norm(v3(0, math.sin(tilt), math.cos(tilt)))
    e1 = v3(1, 0, 0)
    e2 = norm(np.cross(axis, e1))
    start = lens_c + v3(0, 0, 0.05)
    seg = 4
    for k in range(seg):
        t0, t1 = k / seg, (k + 1) / seg
        c0, c1 = start + axis * length * t0, start + axis * length * t1
        ra, rb = r0 + (r1 - r0) * t0, r0 + (r1 - r0) * t1
        for q in range(n):
            a0, a1 = 2 * math.pi * q / n, 2 * math.pi * (q + 1) / n
            d0 = e1 * math.cos(a0) + e2 * math.sin(a0)
            d1 = e1 * math.cos(a1) + e2 * math.sin(a1)
            dm = e1 * math.cos((a0 + a1) / 2) + e2 * math.sin((a0 + a1) / 2)
            panel(beam_bone, "glow_beam_%d_%d" % (k, q), c0 + d0 * ra, c0 + d1 * ra, c1 + d0 * rb, c1 + d1 * rb, 0.02,
                  "beam%d" % k, dm, overlap=1.0)


def airlock_water(root, g):
    """Water of the airlock: rises from the floor with the level (animation "airlock_water", 0 .. 1)."""
    m = g.k == ni.AIRLOCK
    floor, top = g.Y[m].min() - ni.CELL / 2, g.Y[m].max() + ni.CELL / 2
    fx = Bone("fx_airlock", parent=root)
    x0, x1, _, _, z0, z1 = ni.ROOMS["airlock"]
    room = Bone("airlock_water_room", origin=(0, floor, 0), parent=fx)
    add_cube(room, "lit_airlock_water", v3((x0 + x1) / 2, (floor + top) / 2, (z0 + z1) / 2), EYE,
             (x1 - x0 - 0.04, top - floor - 0.04, z1 - z0 - 0.04), "water")
    tx0, tx1, ty0, ty1, tz0, tz1 = ni.AIRLOCK_TUNNEL
    tm = m & (g.Z > tz0) & (g.Z < tz1) & (g.X < x0)
    tx0 = g.X[tm].min() - ni.CELL / 2
    tunnel = Bone("airlock_water_tunnel", origin=(0, floor, 0), parent=fx)
    add_cube(tunnel, "lit_airlock_water_tunnel", v3((tx0 + x0) / 2, (ty0 + ty1) / 2, (tz0 + tz1) / 2), EYE,
             (x0 - tx0 + 0.02, ty1 - ty0 - 0.04, tz1 - tz0 - 0.04), "water")
    k_t = (ty1 - ty0) / (top - floor)  # the tunnel is full when the water reaches its ceiling
    return [gg.animation("airlock_water", 1.0, "hold", [
        (room, [gg.kf("scale", 0.0, (1, 0.001, 1)), gg.kf("scale", 1.0, (1, 1, 1))]),
        (tunnel, [gg.kf("scale", 0.0, (1, 0.001, 1)), gg.kf("scale", k_t, (1, 1, 1)), gg.kf("scale", 1.0, (1, 1, 1))]),
    ])]


def fallbacks(root):
    """Stand-ins of the decoration blocks, shown only when their mod is missing on a client."""
    for i, b in enumerate(nd.BLOCKS):
        x0, x1, y0, y1, z0, z1 = nd.footprint(b["block"], b["x"], b["y"], b["z"], b["yaw"], b["scale"])
        bone = Bone("fallback_%d" % i, parent=root)
        region = nd.FALLBACK_REGION.get(b["block"], "floor")
        add_cube(bone, "lit_fallback_%d" % i, v3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), EYE,
                 (max(0.04, x1 - x0), max(0.04, y1 - y0), max(0.04, z1 - z0)), region)


def build(g):
    root = Bone("nautilus")
    hull_bone = Bone("hull", parent=root)
    outside = Bone("superstructure", parent=root)
    rooms = Bone("rooms", parent=root)
    fittings = Bone("fittings", parent=root)
    lights = Bone("lights", parent=root)
    detail = Bone("detail", parent=root)  # small exterior details, not drawn from far away (ShipRenderer)
    n = hull(hull_bone)
    windows(outside, lights)
    ram(outside)
    crests(outside)
    keels(outside)
    spiral_stair(fittings)
    porthole_sleeves(fittings, Bone("fx_portholes", parent=root), g)
    bay_sleeves(fittings)
    casing_fairing(outside)
    tower_shell(outside)
    cage_hood(outside)
    wheelhouse_lining(rooms)
    aft_fairing(outside)
    deck_fittings(detail)
    tail(outside, root)
    hull_seams(detail)
    hull_details(detail, lights)
    bow_blade(outside)
    prop_shroud(outside)
    m = surfaces(rooms, outside, g)
    ladders(fittings)
    fallbacks(root)
    furniture = Bone("furniture", parent=root)
    for k, (builder, kwargs, solid) in enumerate(nd.CUSTOM):
        kw = dict(kwargs)
        kw.setdefault("name", "%s_%d" % (builder, k))
        fn = getattr(nf, builder)
        if builder in ("engine_block", "helm"):
            fn(furniture, root, **kw)
        elif builder == "lifeboat":
            fn(Bone("lifeboat", parent=root), **kw)  # hidden while the boat is on the water
        else:
            fn(furniture, **kw)
    # the projector lens at the front of the cage, over the wheelhouse roof, and its beam
    projector_beam(root)
    ring(outside, "projector_rim", v3(0, ns.LENS_Y, ns.LAMP_CAGE_Z[1] + 0.06), v3(0, 0, 1), 0.66, 0.14, "brass", n=20, width=0.18)
    # lamps on the ceilings of the rooms
    for name, (x0, x1, y0, y1, z0, z1) in ni.ROOMS.items():
        if name in ("crawlway", "airlock"):
            continue
        step = 4.0
        zc = np.arange(z0 + step / 2, z1, step) if z1 - z0 > step else [(z0 + z1) / 2]
        if name in ("dining", "library", "salon", "cabin_aronnax"):
            continue  # lit by their chandeliers
        for z in zc:
            nf.ceiling_lamp(lights, "lamp_%s_%d" % (name, int(z * 10)), v3((x0 + x1) / 2, y1, z))
    return root, n, m


def build_animations(root, g):
    anims = []
    prop = gg.find(root, "propeller")
    anims.append(gg.animation("propeller", 2.0, "loop", [(prop, [
        gg.rot_kf(t, (0, 0, a)) for t, a in ((0.0, 0), (0.5, 270), (1.0, 540), (1.5, 810), (2.0, 1080))])]))
    # the engine runs with the propeller (same signed phase): the shaft and the flywheel turn, the pistons rise and fall
    tracks = []
    spin = [gg.rot_kf(t, (0, 0, a)) for t, a in ((0.0, 0), (0.5, 270), (1.0, 540), (1.5, 810), (2.0, 1080))]
    for name in ("engine_shaft", "engine_flywheel"):
        b = gg.find(root, name)
        if b is not None:
            tracks.append((b, spin))
    for k in range(8):
        b = gg.find(root, "engine_piston_%d" % k)
        if b is None:
            continue
        keys = []
        for i in range(13):
            t = 2.0 * i / 12
            keys.append(gg.kf("position", t, (0, 0.35 * 16 * math.sin(3 * math.pi * t + k * math.pi / 2), 0)))
        tracks.append((b, keys))
    for k in range(2):
        b = gg.find(root, "engine_gear_%d" % k)
        if b is not None:
            sgn = 1 if k else -1  # the two wheels mesh: opposite turns
            tracks.append((b, [gg.rot_kf(t, (sgn * a * 0.8, 0, 0)) for t, a in ((0.0, 0), (0.5, 270), (1.0, 540), (1.5, 810), (2.0, 1080))]))
    if tracks:
        anims.append(gg.animation("engine", 2.0, "loop", tracks))
    wheel = gg.find(root, "helm_wheel")
    if wheel is not None:
        anims.append(gg.animation("steer", 2.0, "hold", [(wheel, [gg.rot_kf(0.0, (0, 0, -120)), gg.rot_kf(1.0, (0, 0, 0)),
                                                                  gg.rot_kf(2.0, (0, 0, 120))])]))
    return anims


def main():
    g = ni.build()
    nd.build()
    nd.apply_to_grid(g)
    nd.write(os.path.join(ROOT, nd.DECOR_PATH))
    size = g.write(os.path.join(ROOT, ni.GRID_PATH))
    reached, total = ni.walkable_report(g)
    unreachable = [name for name, n in reached.items() if not n]
    print("decor blocks:", len(nd.BLOCKS), "seats:", len(nd.SEATS), "standing places:", total, "unreachable rooms:", unreachable)
    root, n, m = build(g)
    anims = build_animations(root, g)
    anims += doors(root, g)
    anims += shutters(root, gg.find(root, "superstructure"))
    anims += airlock_water(root, g)
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    tex_path = os.path.join(tex_dir, "entity/nautilus.png")
    nt.make_texture(tex_path)
    nt.make_item_icon(os.path.join(tex_dir, "item/nautilus.png"))
    with open(tex_path, "rb") as f:
        png = f.read()
    textures = [gn.texture_entry("nautilus.png", nt.SIZE, png, "entity", "nautilus.png")]
    textures[0]["id"] = "0"
    model = gn.export(root, anims, textures, [
        os.path.join(ROOT, "blockbench/nautilus.bbmodel"),
        os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/nautilus.bbmodel"),
    ], name="nautilus", visible_box=(100, 30, 0), extra={"medievalships_cull_thin_plates": True})
    print("grid bytes:", size, "hull panels:", n, "grid surfaces:", m, "cubes:", len(model["elements"]),
          "animations:", len(model["animations"]))


if __name__ == "__main__":
    main()
