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

NAZ = 40
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
WINDOWS = [(ns.SALON_WINDOW[0], ns.SALON_WINDOW[1], ns.SALON_WINDOW[2] - 0.2)] + \
          [(z, ns.SMALL_WINDOWS_Y, 0.45) for z in ns.SMALL_WINDOWS_Z] + [(z, y, 0.45) for z, y in ns.CABIN_PORTHOLES]


def in_window(p):
    for z, y, r in WINDOWS:
        if (p[2] - z) ** 2 + (p[1] - y) ** 2 < r * r and abs(p[0]) > 2.0:
            return True
    return False


def near_window(points):
    zs = [p[2] for p in points]
    ys = [p[1] for p in points]
    xs = [p[0] for p in points]
    for z, y, r in WINDOWS:
        if min(zs) - r < z < max(zs) + r and min(ys) - r < y < max(ys) + r and max(abs(x) for x in xs) > 2.0:
            return True
    return False


def hull(bone):
    n = 0
    for i in range(len(HULL_S) - 1):
        za, zb = hull_z(HULL_S[i]), hull_z(HULL_S[i + 1])
        for j in range(NAZ):
            a0, a1 = 360.0 * j / NAZ, 360.0 * (j + 1) / NAZ
            am = (a0 + a1) / 2
            outward = v3(math.sin(math.radians(am)), math.cos(math.radians(am)), 0)
            region = "plate" if math.cos(math.radians(am)) > -0.3 else "plate_dark"
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
        ring(bone, "salon_frame_%s" % sn, c, nrm, wr - 0.05, 0.3, "brass", n=16, width=0.36)
        ring(bone, "salon_iris_%s" % sn, c, nrm, wr * 0.7, 0.06, "brass", n=16, width=0.1)
        for k in range(8):
            t = 2 * math.pi * (k + 0.5) / 8
            zz, yy = wz + math.cos(t) * (wr + 0.45), wy + math.sin(t) * (wr + 0.45)
            p, nn = on_hull(zz, yy, side, 0.12)
            add_cube(lights, "glow_salon_lamp_%s%d" % (sn, k), p, EYE, (0.3, 0.3, 0.3), "glow")
            add_cube(bone, "salon_lamp_socket_%s%d" % (sn, k), on_hull(zz, yy, side, 0.02)[0], EYE, (0.42, 0.42, 0.42), "brass")
        for z, y in [(z, ns.SMALL_WINDOWS_Y) for z in ns.SMALL_WINDOWS_Z] + list(ns.CABIN_PORTHOLES):
            c, nrm = on_hull(z, y, side, 0.06)
            ring(bone, "porthole_%s_%d_%d" % (sn, int(z * 10), int(y * 10)), c, nrm, 0.5, 0.12, "brass", n=8, width=0.16)
    # brass frames of the wheelhouse windows, outside and inside
    wy0, wy1 = ns.TOWER_WINDOWS_Y
    yc, r = (wy0 + wy1) / 2, (wy1 - wy0) / 2 + 0.05
    for k, (x0, x1) in enumerate(ns.TOWER_FRONT_WINDOWS_X):
        for z, tag in ((ns.TOWER_Z[1] + 0.16, "out"), (ns.TOWER_Z[1] - 0.56, "in")):
            ring(bone, "tower_window_%d_%s" % (k, tag), v3((x0 + x1) / 2, yc, z), v3(0, 0, 1), r, 0.12, "brass", n=8, width=0.14)
    for side in SIDES:
        for x, tag in ((side * (ns.TOWER_HALF_WIDTH + 0.16), "out"), (side * (ns.TOWER_HALF_WIDTH - 0.56), "in")):
            ring(bone, "tower_window_side_%d_%s" % (side > 0, tag), v3(x, yc, sum(ns.TOWER_SIDE_WINDOW_Z) / 2), v3(1, 0, 0), r, 0.12,
                 "brass", n=8, width=0.14)


def ram(bone):
    y = ns.AXIS_Y
    segs = ((ns.BOW_Z - 3.0, ns.BOW_Z + 1.0, 1.3), (ns.BOW_Z + 1.0, ns.BOW_Z + 3.5, 0.9), (ns.BOW_Z + 3.5, ns.RAM_TIP_Z - 1.0, 0.55),
            (ns.RAM_TIP_Z - 1.0, ns.RAM_TIP_Z, 0.22))
    for k, (z0, z1, r) in enumerate(segs):
        add_cube(bone, "ram_%d" % k, v3(0, y, (z0 + z1) / 2), rz(math.pi / 4), (r, r, z1 - z0 + 0.05), "steel")
    # a flange on top and under the ram, with teeth
    beam(bone, "ram_fin_top", v3(0, y + 0.3, ns.BOW_Z - 1.0), v3(0, y + 0.1, ns.RAM_TIP_Z - 1.2), 0.12, "steel", width=0.5, up=v3(1, 0, 0))
    beam(bone, "ram_fin_bottom", v3(0, y - 0.3, ns.BOW_Z - 1.0), v3(0, y - 0.1, ns.RAM_TIP_Z - 1.2), 0.12, "steel", width=0.5, up=v3(1, 0, 0))
    for k, z in enumerate(np.arange(ns.BOW_Z - 0.5, ns.RAM_TIP_Z - 1.5, 1.2)):
        for s, yy in ((1, 0.55), (-1, -0.55)):
            add_cube(bone, "ram_tooth_%d_%d" % (k, s > 0), v3(0, y + s * (0.42 - 0.03 * k), z), rx(math.radians(45)), (0.1, 0.3, 0.3), "steel")


def spike(bone, name, base, up, h, w, region="steel"):
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
    pts = [(1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2 for t in np.linspace(0, 1, 11)]
    for k in range(len(pts) - 1):
        beam(bone, "crest_fore_%d" % k, pts[k], pts[k + 1], 0.55, "steel", width=0.3, up=v3(1, 0, 0), extend=0.05)
        if k % 1 == 0:
            d = norm(pts[k + 1] - pts[k])
            up = norm(np.cross(d, v3(1, 0, 0)))
            if up[1] < 0:
                up = -up
            spike(bone, "crest_fore_spike_%d" % k, (pts[k] + pts[k + 1]) / 2 + up * 0.2, norm(up + d * 0.35), 0.9, 0.35)
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


def porthole_sleeves(bone, fx, g):
    """Seen from the rooms, each porthole is a bronze sleeve narrowing through the hull to its glass,
    framed on the wall by a bolted brass collar (instead of a square hole in the wall)."""
    ports = [(z, ns.SMALL_WINDOWS_Y) for z in ns.SMALL_WINDOWS_Z] + list(ns.CABIN_PORTHOLES)
    C = ni.CELL
    count = 0
    for z, y in ports:
        for side in SIDES:
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
                while abs(x) > 1.0 and kind(x, y + 0.75) not in (ni.DRY, ni.FURNITURE, ni.LADDER):
                    x -= side * C / 2
                i_room = int((x - ni.X0) / C)
                wall = ni.X0 + (i_room + 1) * C if side > 0 else ni.X0 + i_room * C  # the wall's face on the room
            if wall is None or glass is None:
                continue
            glass = glass + side * C if abs(glass) - abs(wall) < 0.3 else glass  # thin wall: the glass in the hull's skin
            n = 10
            name = "porthole_%d_%d_%d" % (int(z * 10), int(y * 10), side > 0)
            for j in range(n):
                a0, a1 = 2 * math.pi * j / n, 2 * math.pi * (j + 1) / n
                def P(x, r, a):
                    return v3(x, y + math.sin(a) * r, z + math.cos(a) * r)
                am = (a0 + a1) / 2
                panel(bone, "lit_%s_sleeve%d" % (name, j), P(wall - side * 0.02, 0.74, a0), P(wall - side * 0.02, 0.74, a1), P(glass, 0.45, a0),
                      P(glass, 0.45, a1), 0.05,
                      "copper", v3(0, -math.sin(am), -math.cos(am)), overlap=1.04)
                beam(bone, "lit_%s_collar%d" % (name, j), P(wall - side * 0.06, 0.68, a0), P(wall - side * 0.06, 0.68, a1), 0.1, "brass",
                     width=0.22, up=v3(side, 0, 0))
                if j % 2 == 0:
                    add_cube(bone, "lit_%s_bolt%d" % (name, j), P(wall - side * 0.12, 0.68, am), EYE, (0.06, 0.06, 0.06), "steel")
            # a square brass plate on the wall round the collar: it covers the edges of the opening
            for k, (dy, dz, sy, sz) in enumerate(((0.6, 0, 0.2, 1.4), (-0.6, 0, 0.2, 1.4), (0, 0.6, 1.0, 0.2), (0, -0.6, 1.0, 0.2))):
                add_cube(bone, "lit_%s_plate%d" % (name, k), v3(wall - side * 0.025, y + dy, z + dz), EYE, (0.05, sy, sz), "brass")
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
    loft(bone, "casing_shoulder_p", right, "hull_light", centre)
    loft(bone, "casing_shoulder_s", left, "hull_light", centre)
    # the deck: plates between the shoulders, with holes for the wheelhouse and the projector cage
    # (they stand on it), the lifeboat recess and the main hatch
    holes = [(-2.6, 2.6, ns.LAMP_CAGE_Z[0] - 0.1, ns.TOWER_Z[1] + 0.1),
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
    plan = superellipse(a, b, 6, 56, zc)
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
    for k, (sc, dyr) in enumerate(((1.0, 0.0), (0.93, 0.22), (0.75, 0.4), (0.45, 0.5), (0.04, 0.53))):
        roof.append([v3(x * sc, ns.TOWER_TOP_Y + dyr, zc + (z - zc) * sc) for x, z in plan])
    loft(bone, "tower_roof", roof, "hull_light", lambda p: v3(0, ns.TOWER_TOP_Y - 2.0, zc), closed=True)
    # brass bands at the foot and under the roof
    for yy, tag in ((ns.CASING_TOP_Y + 0.08, "foot"), (ns.TOWER_TOP_Y - 0.05, "eave")):
        for k in range(len(plan)):
            (x0, z0), (x1, z1) = plan[k], plan[(k + 1) % len(plan)]
            beam(bone, "tower_band_%s_%d" % (tag, k), v3(x0 * 1.02, yy, zc + (z0 - zc) * 1.02), v3(x1 * 1.02, yy, zc + (z1 - zc) * 1.02),
                 0.14, "brass", width=0.1)


def cage_hood(bone):
    """The projector's cage behind the wheelhouse: a hood rounded over the top."""
    w = ns.LAMP_CAGE_HALF_WIDTH + 0.08
    top = ns.LAMP_CAGE_TOP_Y + 0.08
    r = 1.3
    prof = [(-w, ns.CASING_TOP_Y)]
    prof += [(-w, top - r)]
    prof += [(-w + r - r * math.cos(t), top - r + r * math.sin(t)) for t in np.linspace(0, math.pi / 2, 5)[1:]]
    prof += [(w - r + r * math.sin(t), top - r + r * math.cos(t)) for t in np.linspace(0, math.pi / 2, 5)[:-1]]
    prof += [(w, top - r), (w, ns.CASING_TOP_Y)]
    z0, z1 = ns.LAMP_CAGE_Z[0] - 0.08, ns.TOWER_Z[0] + 0.02
    sections = [[v3(x, yy, z) for x, yy in prof] for z in np.linspace(z0, z1, 6)]
    loft(bone, "cage_hood", sections, "hull_light", lambda p: v3(0, ns.CASING_TOP_Y + 2.0, p[2]))
    # its aft end and the part of its front above the wheelhouse roof (round the lens)
    for z, tag, lens in ((z0, "aft", False), (z1, "front", True)):
        ys = np.linspace(ns.CASING_TOP_Y if not lens else ns.TOWER_TOP_Y, top, 9)
        for k in range(len(ys) - 1):
            ym = (ys[k] + ys[k + 1]) / 2
            dy = ym - (top - r)
            hw = w if dy <= 0 else w - r + math.sqrt(max(0.0, r * r - dy * dy))
            spans = [(-hw, hw)]
            if lens and ns.LENS_Y - 0.6 < ym < ns.LENS_Y + 0.6:
                spans = [(-hw, -0.85), (0.85, hw)]
            for q, (xa, xb) in enumerate(spans):
                if xb - xa < 0.05:
                    continue
                add_cube(bone, "cage_%s_%d_%d" % (tag, k, q), v3((xa + xb) / 2, ym, z), EYE, (xb - xa, ys[k + 1] - ys[k] + 0.02, 0.06),
                         "hull_light")


def tail(bone, root):
    y = ns.AXIS_Y
    # cone with rings from the end of the hull to the propeller
    zs = np.linspace(ns.STERN_Z + 2.0, ns.TAIL_CONE_Z, 6)
    rs = np.linspace(1.6, 0.5, 6)
    for k in range(len(zs) - 1):
        for j in range(12):
            a0, a1 = 30.0 * j, 30.0 * (j + 1)
            am = math.radians((a0 + a1) / 2)
            outward = v3(math.sin(am), math.cos(am), 0)

            def C(z, r, a):
                return v3(math.sin(math.radians(a)) * r, y + math.cos(math.radians(a)) * r, z)
            panel(bone, "tail_cone_%d_%d" % (k, j), C(zs[k], rs[k], a0), C(zs[k], rs[k], a1), C(zs[k + 1], rs[k + 1], a0),
                  C(zs[k + 1], rs[k + 1], a1), 0.1, "plate_dark", outward)
        ring(bone, "tail_ring_%d" % k, v3(0, y, zs[k]), v3(0, 0, 1), rs[k] + 0.05, 0.16, "brass", n=12, width=0.22)
    beam(bone, "shaft", v3(0, y, ns.TAIL_CONE_Z + 0.3), v3(0, y, ns.PROP_Z - 0.6), 0.36, "steel")
    prop = Bone("propeller", origin=(0, y, ns.PROP_Z), parent=root)
    hub = v3(0, y, ns.PROP_Z)
    add_cube(prop, "prop_hub", hub, EYE, (0.8, 0.8, 0.7), "brass")
    add_cube(prop, "prop_cap", hub + v3(0, 0, -0.45), rz(math.pi / 4), (0.5, 0.5, 0.3), "brass")
    pitch = math.radians(28)
    for k in range(4):
        a = 2 * math.pi * k / 4 + math.pi / 4
        d = v3(math.sin(a), math.cos(a), 0)
        side = np.cross(v3(0, 0, 1), d)
        w = side * math.cos(pitch) + v3(0, 0, 1) * math.sin(pitch)
        n = np.cross(d, w)
        axes = np.column_stack([d, w, n])
        add_cube(prop, "prop_root_%d" % k, hub + d * 0.8, axes, (0.8, 0.6, 0.14), "brass")
        add_cube(prop, "prop_blade_%d" % k, hub + d * 2.0, axes, (1.7, 1.25, 0.12), "brass")
        add_cube(prop, "prop_tip_%d" % k, hub + d * (ns.PROP_R - 0.2), axes, (0.45, 0.85, 0.12), "brass")
    # fish-tail fin (vertical lobes) and the horizontal fins, as strips between the swept edges
    def lobes(name, axis_dir, top):
        span = abs(top)
        for k, f in enumerate(np.arange(0.25, span, 0.5)):
            le = ns.FIN_Z0 - max(0.0, f - 1.0) / (span - 1.0) * (ns.FIN_Z0 - ns.FIN_TIP_LE_Z)
            te = ns.FIN_NOTCH_Z - f / span * (ns.FIN_NOTCH_Z - ns.FIN_TIP_TE_Z)
            pass
        # the lobe as one smooth plate, thick at the root and thin at the tip, its strips following
        # the swept edges (no steps)
        normal = v3(1, 0, 0) if axis_dir[1] else v3(0, 1, 0)
        fs = np.linspace(0.6, span, 12)

        def edges(f):
            le = ns.FIN_Z0 - max(0.0, f - 1.0) / (span - 1.0) * (ns.FIN_Z0 - ns.FIN_TIP_LE_Z)
            te = ns.FIN_NOTCH_Z - f / span * (ns.FIN_NOTCH_Z - ns.FIN_TIP_TE_Z)
            c = v3(0, y, 0) + axis_dir * math.copysign(f, top)
            return c + v3(0, 0, le), c + v3(0, 0, te)
        for k in range(len(fs) - 1):
            a_le, a_te = edges(fs[k])
            b_le, b_te = edges(fs[k + 1])
            th = 0.34 - 0.22 * (fs[k] / span)
            panel(bone, "%s_%d" % (name, k), a_le, a_te, b_le, b_te, th, "plate_dark", normal, overlap=1.02)
        tip_le = v3(0, y, ns.FIN_TIP_LE_Z) + axis_dir * top
        tip_te = v3(0, y, ns.FIN_TIP_TE_Z) + axis_dir * top
        root_le = v3(0, y, ns.FIN_Z0) + axis_dir * math.copysign(1.0, top)
        notch = v3(0, y, ns.FIN_NOTCH_Z)
        beam(bone, name + "_leading", root_le, tip_le, 0.34, "steel", width=0.34)
        beam(bone, name + "_tip", tip_le, tip_te, 0.3, "steel", width=0.3)
        beam(bone, name + "_trailing", notch, tip_te, 0.26, "steel", width=0.26)
    lobes("fin_top", v3(0, 1, 0), ns.FIN_TOP)
    lobes("fin_bottom", v3(0, 1, 0), ns.FIN_BOTTOM)
    lobes("fin_port", v3(1, 0, 0), ns.FIN_SPAN)
    lobes("fin_starboard", v3(1, 0, 0), -ns.FIN_SPAN)


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
            inner = solid & nb_open
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
                add_cube(bone, "lit_door_%d_%s" % (d, leaf), c, EYE, size, faces)
                tracks.append((bone, [gg.rot_kf(0.0, (0, 0, 0)), gg.rot_kf(1.0, (0, sgn * 100, 0))]))
            anims.append(gg.animation("door_%d" % d, 1.0, "hold", tracks))
            continue
        bone = Bone("door_%d" % d, origin=tuple(hinge), parent=root)
        c = v3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        size = (sx if sx > thin * 2 else thin, sy if not flat else thin, sz if sz > thin * 2 else thin)
        if d == 9:
            size = (thin, sy, sz)
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
        R = np.column_stack([ez, et, n])
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
    lens_c = v3(0, ns.LENS_Y, ns.TOWER_Z[0] + 0.48)
    off = Bone("lens_off", parent=root)
    add_cube(off, "lens_glass", lens_c, EYE, (1.6, 1.1, 0.04), "glass")
    lens = Bone("fx_lens", parent=root)
    add_cube(lens, "glow_projector_lens", lens_c + v3(0, 0, 0.01), EYE, (1.6, 1.1, 0.04), "glow")
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
    n = hull(hull_bone)
    windows(outside, lights)
    ram(outside)
    crests(outside)
    keels(outside)
    spiral_stair(fittings)
    porthole_sleeves(fittings, Bone("fx_portholes", parent=root), g)
    casing_fairing(outside)
    tower_shell(outside)
    cage_hood(outside)
    tail(outside, root)
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
    ring(outside, "projector_rim", v3(0, ns.LENS_Y, ns.TOWER_Z[0] + 0.52), v3(0, 0, 1), 0.85, 0.14, "brass", n=12, width=0.18)
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
    ], name="nautilus", visible_box=(100, 30, 0))
    print("grid bytes:", size, "hull panels:", n, "grid surfaces:", m, "cubes:", len(model["elements"]),
          "animations:", len(model["animations"]))


if __name__ == "__main__":
    main()
