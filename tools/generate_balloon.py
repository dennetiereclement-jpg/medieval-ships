#!/usr/bin/env python3
"""Generates the steampunk hot-air balloon (hot_air_balloon) Blockbench model, its texture, its item icon and its
animations.

Usage:  python3 tools/generate_balloon.py        (BALLOON_FAST=1: no z-fighting pass, for quick previews)

Outputs:
  blockbench/hot_air_balloon.bbmodel                                           (editable, texture embedded)
  src/main/resources/assets/medievalships/models/entity/hot_air_balloon.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/hot_air_balloon.png
  src/main/resources/assets/medievalships/textures/item/hot_air_balloon.png

Reference (one picture, measurements in docs/BALLOON_PLAN.md): a big round balloon, slightly taller than wide, of
24 alternating olive-green and beige gores, a brass load band with gold ornaments round its lower half, gold chains
down its skirt to a load ring at the mouth and from there to a small dark green-stained wooden basket (a boat hull
with dark rims, lit windows along its sides, lanterns hanging under its ends); in the middle of the basket a copper
and brass burner column with a square platform and a lantern half way up, the burner head and its flame rising into
the mouth; a black riveted boiler with its stack and copper pipes aft of the column; a big wooden gear wheel with
its pinion on the port side.

The envelope is a body of revolution about the vertical axis, built from tilted panels (no staircase): 24 gores
between 16 rings following balloon_shape.balloon_radius (denser at the mouth and the crown). Round parts (chains,
rings, column, boiler, stack, lanterns) are regular prisms of a few turned boxes.

Bones used by the mod (keep their names when editing in Blockbench):
  helm_wheel (steer)   burner_flame, burner_core (elevator: 0 = descending, 1 = level, 2 = climbing: the flame
  flares while climbing; flag_wave: its flicker)   side_wheel, pinion (engine: turn with the speed)
  lantern_* (lantern_sway)
"""
import math
import os
import sys
import uuid

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import generate_galleon as gn  # noqa: E402
import generate_galley as gg  # noqa: E402
import generate_airship as ga  # noqa: E402
import generate_leviathan as gl  # noqa: E402
import balloon_shape as bs  # noqa: E402
import balloon_texture as bt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/hot_air_balloon/%d" % _uuid_counter[0]))


gg.new_uuid = new_uuid
gn.new_uuid = new_uuid
gn.REGIONS = {k: (0,) + r for k, r in bt.REGIONS.items()}
gn.SIZE = bt.SIZE

v3, norm, Bone, add_cube, beam, board = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam, gg.board
rx, ry, rz = gg.rx, gg.ry, gg.rz
tube, disc, ring, polyline, catmull, bezier, dome, panel = ga.tube, ga.disc, ga.ring, ga.polyline, ga.catmull, ga.bezier, ga.dome, ga.panel
dial, face_frame, lantern = ga.dial, ga.face_frame, ga.lantern
chain = gl.chain
EYE = np.eye(3)
SIDES = ((1, "p"), (-1, "s"))
UP = v3(0, 1, 0)

# envelope rings (height fractions), denser where the profile curves fast
RINGS = [0.0, 0.03, 0.07, 0.12, 0.18, 0.25, 0.33, 0.42, 0.51, 0.6, 0.69, 0.77, 0.84, 0.9, 0.94, bs.CROWN_F]
LOAD_RING_Y = bs.MOUTH_Y - 0.45
LOAD_RING_R = 1.35


def P(f, az_deg, out=0.0):
    return v3(*bs.balloon_point(f, math.radians(az_deg), out))


def radial(az_deg):
    a = math.radians(az_deg)
    return v3(math.sin(a), 0, math.cos(a))


# ---------------------------------------------------------------- the basket hull
STATIONS = [-5.08, -4.85, -4.5, -4.0, -3.4, -2.6, -1.7, -0.6, 0.6, 1.7, 2.6, 3.4, 4.0, 4.5, 4.85, 5.08]
UPPER = [0.0, 0.4, 0.75, 1.0]
SUB = 2
# strake regions by section point (after the keel point): bottom dark, the middle and the bulwark green, the top band dark
STRAKES = ["hull_dark", "hull_dark", "hull", "hull", "hull", "hull", "rim"]


def hw(z):
    return bs.half_width(z)


def sheer(z):
    return bs.sheer_y(z)


def upper_y(z, f):
    return 0.1 + (sheer(z) - 0.1) * f


def section2d(z):
    w, yk = hw(z), bs.keel_y(z)
    pts = [(0.05, yk)]
    for fx, fy in bs.BOTTOM_SECTION[1:]:
        pts.append((fx * w, fy * yk))
    for f in UPPER:
        pts.append((w * (0.97 + 0.03 * f), upper_y(z, f)))
    return catmull(pts, SUB)


def section(z, side):
    return [v3(side * max(x, 0.05), y, z) for x, y in section2d(z)]


def hull_x(z, y):
    """x of the planking (port side) at height y of station z."""
    pts = section2d(z)
    if y <= pts[0][1]:
        return pts[0][0]
    for k in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[k], pts[k + 1]
        if y0 <= y <= y1 and y1 > y0:
            return x0 + (x1 - x0) * (y - y0) / (y1 - y0)
    return pts[-1][0]


def hull_pt(z, y, side, out=0.0):
    """Point on the outside of the planking and its outward normal."""
    e = 0.04
    dz = (hull_x(z + e, y) - hull_x(z - e, y)) / (2 * e)
    dy = (hull_x(z, y + e) - hull_x(z, y - e)) / (2 * e)
    n = norm(v3(side * 1.0, -dy, -dz))
    return v3(side * hull_x(z, y), y, z) + n * out, n


def gear(bone, name, c, axis, r, th, teeth, region, spokes, spoke_region, hub_r):
    """A wooden gear wheel: a rim of flat segments, square teeth, spokes, a brass hub."""
    axis = norm(v3(*axis))
    c = v3(*c)
    e1 = norm(np.cross(axis, UP if abs(axis[1]) < 0.9 else v3(1, 0, 0)))
    e2 = np.cross(axis, e1)
    n = max(12, teeth)
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        am = (a0 + a1) / 2
        p0 = c + (e1 * math.cos(a0) + e2 * math.sin(a0)) * r
        p1 = c + (e1 * math.cos(a1) + e2 * math.sin(a1)) * r
        beam(bone, "%s_rim_%d" % (name, k), p0, p1, th, region, width=r * 0.24, up=e1 * math.cos(am) + e2 * math.sin(am), extend=r * 0.07)
    for k in range(teeth):
        a = 2 * math.pi * (k + 0.5) / teeth
        d = e1 * math.cos(a) + e2 * math.sin(a)
        t = np.cross(axis, d)
        add_cube(bone, "%s_tooth_%d" % (name, k), c + d * (r * 1.14), np.column_stack([d, t, axis]),
                 (r * 0.2, 2 * math.pi * r / teeth * 0.42, th * 0.85), region)
    for k in range(spokes):
        a = 2 * math.pi * k / spokes
        d = e1 * math.cos(a) + e2 * math.sin(a)
        beam(bone, "%s_spoke_%d" % (name, k), c + d * hub_r * 0.8, c + d * r * 0.92, th * 0.7, spoke_region, width=r * 0.11, up=axis)
    disc(bone, name + "_hub", c, axis, hub_r, th * 1.5, "brass", sides=10)
    disc(bone, name + "_hub_cap", c + axis * th * 0.9, axis, hub_r * 0.45, th * 0.5, "gold", sides=8)


def build():
    root = Bone("hot_air_balloon")
    balloon = Bone("balloon", parent=root)
    rigging = Bone("rigging", parent=root)
    basket = Bone("basket", parent=root)
    fittings = Bone("fittings", parent=root)
    engine = Bone("engine", parent=root)
    lanterns = Bone("lanterns", parent=root)
    burner = Bone("burner", parent=root)

    # ---------------------------------------------------------------- the envelope: 24 gores between the rings
    for i in range(len(RINGS) - 1):
        fa, fb = RINGS[i], RINGS[i + 1]
        fm = (fa + fb) / 2
        for j in range(bs.GORES):
            a0, a1 = 360.0 * j / bs.GORES, 360.0 * (j + 1) / bs.GORES
            am = (a0 + a1) / 2
            region = "gore_green" if j % 2 == 0 else "gore_beige"
            outward = radial(am) + v3(0, 0.6 if fm > 0.58 else -0.3, 0)
            panel(balloon, "gore_%d_%d" % (i, j), P(fa, a0), P(fa, a1), P(fb, a0), P(fb, a1), 0.12, region, outward,
                  inner="balloon_in")
    # the crown: a brass plate closing the cloth, a gold ring, a domed brass cap with a gold finial (the valve)
    yc = bs.fy(bs.CROWN_F)
    rc = bs.R * bs.profile(bs.CROWN_F)
    disc(balloon, "crown_plate", (0, yc + 0.02, 0), UP, rc + 0.1, 0.16, "brass", sides=16)
    ring(balloon, "crown_ring", v3(0, yc + 0.06, 0), UP, rc + 0.12, 0.14, "gold", n=16, round_=True)
    dome(balloon, "crown_dome", v3(0, yc + 0.1, 0), UP, 0.75, 0.3, "brass", steps=3)
    disc(balloon, "crown_finial", (0, yc + 0.48, 0), UP, 0.16, 0.16, "gold", sides=8)
    # the mouth: a brass collar and a gold bead just above it
    ring(balloon, "mouth_collar", v3(0, bs.MOUTH_Y + 0.02, 0), UP, bs.MOUTH_R + 0.1, 0.24, "brass", n=16, round_=True)
    ring(balloon, "mouth_bead", v3(0, bs.fy(0.025), 0), UP, bs.R * bs.profile(0.025) + 0.08, 0.12, "gold", n=16, round_=True)
    # the load band round the lower belly: a riveted brass band, gold shackle plates where the chains hang, bosses between
    fb_ = bs.BAND_F
    for k in range(bs.GORES):
        a0, a1 = 360.0 * k / bs.GORES, 360.0 * (k + 1) / bs.GORES
        am = (a0 + a1) / 2
        beam(rigging, "band_%d" % k, P(fb_, a0, 0.1), P(fb_, a1, 0.1), 0.1, "band", width=0.55, up=radial(am), extend=0.06)
        boss = P(fb_, a0, 0.17)
        add_cube(rigging, "band_boss_%d" % k, boss, ry(-math.radians(a0)), (0.16, 0.2, 0.1), "gold")
    for k, az in enumerate(bs.CHAIN_AZIMUTHS):
        p = P(fb_, az, 0.22)
        R = ry(-math.radians(az))
        add_cube(rigging, "shackle_%d" % k, p, R, (0.5, 0.75, 0.12), "gold")
        disc(rigging, "shackle_boss_%d" % k, p + radial(az) * 0.08, radial(az), 0.17, 0.08, "brass", sides=8)
        add_cube(rigging, "shackle_ear_%d" % k, p - v3(0, 0.46, 0) + radial(az) * 0.02, R, (0.22, 0.2, 0.14), "gold")

    # ---------------------------------------------------------------- suspension: gold chains down the skirt to the
    # load ring at the mouth, then from the ring to the basket's rail; the ring hangs from the burner frame
    ring(rigging, "load_ring", v3(0, LOAD_RING_Y, 0), UP, LOAD_RING_R, 0.18, "brass", n=16, round_=True)
    for k, az in enumerate(bs.CHAIN_AZIMUTHS):
        fs = [fb_ - 0.006] + [fb_ * (1 - t) for t in (0.2, 0.4, 0.55, 0.7, 0.82, 0.92, 1.0)]
        pts = [P(f, az, 0.24) for f in fs[:-1]] + [v3(0, LOAD_RING_Y + 0.12, 0) + radial(az) * (LOAD_RING_R + 0.02)]
        pts[-2] = v3(0, bs.fy(fs[-2]), 0) + radial(az) * (bs.R * bs.profile(fs[-2]) + 0.28)
        for s in range(len(pts) - 1):
            chain(rigging, "skirt_chain_%d_%d" % (k, s), pts[s], pts[s + 1], link=0.3, th=0.065)
        rx_, rz_ = bs.CHAIN_RAIL[k]
        top = v3(0, LOAD_RING_Y - 0.1, 0) + radial(az) * (LOAD_RING_R + 0.02)
        bottom = v3(rx_, sheer(rz_) + 0.16, rz_)
        chain(rigging, "chain_%d" % k, top, bottom, link=0.33, th=0.07)
        disc(rigging, "chain_clamp_%d" % k, bottom - v3(0, 0.04, 0), UP, 0.11, 0.1, "brass", sides=8)
        ring(rigging, "chain_eye_%d" % k, top, radial(az), 0.12, 0.05, "gold", n=6)

    # ---------------------------------------------------------------- the basket: a small planked hull with dark rims
    for side, sn in SIDES:
        for i in range(len(STATIONS) - 1):
            za, zb = STATIONS[i], STATIONS[i + 1]
            A_, B_ = section(za, side), section(zb, side)
            for k in range(len(A_) - 1):
                ko = min(k // SUB, len(STRAKES) - 1)
                reg = STRAKES[ko]
                mid = (A_[k] + A_[k + 1] + B_[k] + B_[k + 1]) / 4
                outward = norm(v3(side, -0.7 if ko < 3 else 0.0, 0) + v3(0, 0, 0.35 * np.sign(mid[2])))
                board(basket, "hull_%s%d_%d" % (sn, i, k), A_[k], A_[k + 1], B_[k], B_[k + 1], 0.1, reg, outward,
                      inner="hull" if ko >= 4 else None)
            # the rims: a flat cap plank on the bulwark and a round rail on it, a dark wale at the deck line
            pa, pb = v3(side * hw(za), sheer(za) + 0.04, za), v3(side * hw(zb), sheer(zb) + 0.04, zb)
            beam(basket, "gunwale_%s%d" % (sn, i), pa, pb, 0.08, "rim", width=0.3, extend=0.04)
            tube(basket, "rail_%s%d" % (sn, i), pa + v3(0, 0.08, 0), pb + v3(0, 0.08, 0), 0.17, "rim", extend=0.05)
            ya, yb = upper_y(za, 0.08), upper_y(zb, 0.08)
            qa, qb = v3(side * (hull_x(za, ya) + 0.05), ya, za), v3(side * (hull_x(zb, yb) + 0.05), yb, zb)
            beam(basket, "wale_%s%d" % (sn, i), qa, qb, 0.1, "rim", width=0.22, extend=0.04)
            ya, yb = upper_y(za, 0.55), upper_y(zb, 0.55)
            qa, qb = v3(side * (hull_x(za, ya) + 0.04), ya, za), v3(side * (hull_x(zb, yb) + 0.04), yb, zb)
            tube(basket, "rub_%s%d" % (sn, i), qa, qb, 0.07, "brass", extend=0.04, sides=4)
    for i in range(len(STATIONS) - 1):
        za, zb = STATIONS[i], STATIONS[i + 1]
        tube(basket, "keel_%d" % i, (0, bs.keel_y(za) - 0.08, za), (0, bs.keel_y(zb) - 0.08, zb), 0.22, "rim", extend=0.05)
    # stem and stern posts rising past the rail to a brass ball
    for s, tag in ((1, "stem"), (-1, "stern")):
        z0 = s * (bs.HALF_LENGTH + 0.3)
        top = sheer(z0) + 0.45
        p0 = v3(0, bs.keel_y(z0) - 0.05, z0)
        p2 = v3(0, top, z0 + s * 0.3)
        p1 = v3(0, (p0[1] + top) * 0.45, z0 + s * 0.55)
        polyline(basket, tag + "_post", bezier(p0, p1, p2, 5), 0.26, "rim")
        disc(basket, tag + "_cap", p2 + v3(0, 0.06, 0), UP, 0.16, 0.08, "brass", sides=8)
        disc(basket, tag + "_ball", p2 + v3(0, 0.2, 0), UP, 0.12, 0.2, "gold", sides=8)
    # the deck
    main_y = bs.MAIN_DECK_Y
    n = 24
    z0, z1 = bs.DECK_MIN_Z, bs.DECK_MAX_Z
    for j in range(n):
        za = z0 + (z1 - z0) * j / n
        zb = z0 + (z1 - z0) * (j + 1) / n
        w = min(bs.inner_half_width(za), bs.inner_half_width(zb)) + 0.12
        add_cube(basket, "deck_%d" % j, (0, main_y - 0.06, (za + zb) / 2), EYE, (2 * w, 0.12, zb - za + 0.02),
                 {"all": "deck", "-2": "hull_dark"})
    # lit windows along the sides, in brass frames
    for side, sn in SIDES:
        for k, z in enumerate((-2.8, -1.7, -0.6, 0.5, 1.6, 2.7)):
            p, nn = hull_pt(z, -0.42, side, 0.0)
            F = face_frame(nn)
            add_cube(basket, "window_frame_%s%d" % (sn, k), p + nn * 0.03, F, (0.6, 0.5, 0.06), "brass")
            add_cube(basket, "glow_window_%s%d" % (sn, k), p + nn * 0.07, F, (0.48, 0.38, 0.012), {"all": None, "+3": "window", "-3": "window"},
                     stretch=True)
        # a gold bead under the rim
        zz = [z for z in STATIONS if -4.6 <= z <= 4.6]
        for i in range(len(zz) - 1):
            ya, yb = sheer(zz[i]) - 0.16, sheer(zz[i + 1]) - 0.16
            qa, _ = hull_pt(zz[i], ya, side, 0.03)
            qb, _ = hull_pt(zz[i + 1], yb, side, 0.03)
            tube(basket, "bead_%s%d" % (sn, i), qa, qb, 0.05, "gold", sides=4, extend=0.03)

    # ---------------------------------------------------------------- the burner column, the platform, the helm
    cz = bs.COLUMN_Z
    disc(fittings, "column_base", (0, main_y + 0.04, cz), UP, 0.55, 0.08, "brass", sides=10)
    tube(fittings, "column", (0, main_y, cz), (0, bs.BURNER_Y - 0.3, cz), 0.44, "copper", sides=10)
    for k, y in enumerate((0.2, 1.15, bs.PLATFORM_Y + 0.12, 3.5)):
        tube(fittings, "column_collar_%d" % k, (0, y - 0.07, cz), (0, y + 0.07, cz), 0.56, "brass", sides=10)
    ph = bs.PLATFORM_HALF
    for k, (dx, dz) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        q = v3(dx * ph, 0, cz + dz * ph)
        tube(fittings, "post_%d" % k, q, q + v3(0, bs.PLATFORM_Y + 0.7, 0), 0.13, "dark_wood", sides=4)
        disc(fittings, "post_cap_%d" % k, q + v3(0, bs.PLATFORM_Y + 0.74, 0), UP, 0.1, 0.06, "brass", sides=8)
        # brace up to the burner frame
        tube(fittings, "brace_%d" % k, q + v3(0, bs.PLATFORM_Y + 0.6, 0), v3(dx * 0.34, bs.BURNER_Y - 0.15, cz + dz * 0.34), 0.07, "brass", sides=4)
    add_cube(fittings, "platform", (0, bs.PLATFORM_Y, cz), EYE, (2 * ph + 0.1, 0.1, 2 * ph + 0.1), {"all": "platform", "-2": "hull_dark"})
    for k, (a, b) in enumerate((((1, 1), (1, -1)), ((1, -1), (-1, -1)), ((-1, -1), (-1, 1)), ((-1, 1), (1, 1)))):
        pa, pb = v3(a[0] * ph, bs.PLATFORM_Y + 0.65, cz + a[1] * ph), v3(b[0] * ph, bs.PLATFORM_Y + 0.65, cz + b[1] * ph)
        tube(fittings, "platform_rail_%d" % k, pa, pb, 0.07, "dark_wood", sides=4)
        tube(fittings, "platform_rail_low_%d" % k, pa - v3(0, 0.35, 0), pb - v3(0, 0.35, 0), 0.05, "iron", sides=4)
        pa2, pb2 = v3(a[0] * ph, bs.PLATFORM_Y + 0.05, cz + a[1] * ph), v3(b[0] * ph, bs.PLATFORM_Y + 0.05, cz + b[1] * ph)
        beam(fittings, "platform_edge_%d" % k, pa2, pb2, 0.1, "rim", width=0.14, extend=0.05)
        # an X of iron rods between the posts below the platform
        beam(fittings, "x_brace_%d_a" % k, v3(a[0] * ph, 0.2, cz + a[1] * ph), v3(b[0] * ph, bs.PLATFORM_Y - 0.1, cz + b[1] * ph), 0.045, "iron")
        beam(fittings, "x_brace_%d_b" % k, v3(b[0] * ph, 0.2, cz + b[1] * ph), v3(a[0] * ph, bs.PLATFORM_Y - 0.1, cz + a[1] * ph), 0.045, "iron")
    # the lantern half way up the column, in a brass bracket on its fore side
    lb = v3(0, 1.75, cz + 0.3)
    tube(fittings, "column_lantern_arm", lb, lb + v3(0, 0, 0.32), 0.05, "brass", sides=4)
    tube(fittings, "column_lantern_hook", lb + v3(0, 0, 0.32), lb + v3(0, -0.08, 0.32), 0.03, "iron", sides=4)
    lantern(fittings, "column_lantern", lb + v3(0, -0.36, 0.32), 0.26, 0.34, bail=False)
    # the burner head: a brass drum, an iron top plate with four jets round a glowing mouth
    by = bs.BURNER_Y
    tube(burner, "burner_body", (0, by - 0.3, cz), (0, by + 0.1, cz), 0.8, "brass", sides=10)
    tube(burner, "burner_band", (0, by - 0.12, cz), (0, by - 0.04, cz), 0.86, "gold", sides=10)
    disc(burner, "burner_top", (0, by + 0.13, cz), UP, 0.42, 0.08, "iron_dark", sides=10)
    disc(burner, "glow_burner_mouth", (0, by + 0.18, cz), UP, 0.24, 0.03, "fire", sides=8)
    for k, (dx, dz) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        q = v3(dx * 0.24, by + 0.15, cz + dz * 0.24)
        tube(burner, "burner_jet_%d" % k, q, q + v3(0, 0.2, 0), 0.11, "brass", sides=6)
    # the struts from the burner to the load ring
    for k in range(4):
        az = 45 + 90 * k
        tube(burner, "ring_strut_%d" % k, v3(0, by - 0.1, cz) + radial(az) * 0.36, v3(0, LOAD_RING_Y, 0) + radial(az) * (LOAD_RING_R - 0.05),
             0.08, "brass", sides=4)
    # the flame: two crossed glowing tongues (bone burner_flame) and a narrower, brighter core (burner_core)
    fh = bs.FLAME_TOP - by - 0.2
    flame = Bone("burner_flame", origin=(0, by + 0.2, cz), parent=burner)
    for k, R in enumerate((EYE, ry(math.pi / 2))):
        add_cube(flame, "glow_flame_%d" % k, (0, by + 0.2 + fh / 2, cz), R, (1.05, fh, 0.012), {"all": None, "+3": "flame", "-3": "flame"},
                 stretch=True)
    core = Bone("burner_core", origin=(0, by + 0.2, cz), parent=burner)
    for k, R in enumerate((ry(math.pi / 4), ry(-math.pi / 4))):
        add_cube(core, "glow_core_%d" % k, (0, by + 0.2 + fh * 0.33, cz), R, (0.55, fh * 0.66, 0.012), {"all": None, "+3": "flame", "-3": "flame"},
                 stretch=True)
    # the helm: a brass control stand on the aft side of the column, a valve wheel (bone helm_wheel), a lever, a gauge
    hz = bs.HELM_Z
    disc(fittings, "helm_base", (0, main_y + 0.03, hz), UP, 0.22, 0.06, "brass", sides=8)
    tube(fittings, "helm_stand", (0, main_y, hz), (0, main_y + 0.95, hz), 0.14, "brass", sides=8)
    add_cube(fittings, "helm_box", (0, main_y + 1.08, hz), EYE, (0.5, 0.3, 0.3), "brass")
    add_cube(fittings, "helm_box_top", (0, main_y + 1.25, hz), EYE, (0.4, 0.05, 0.22), "gold")
    hc = v3(0, main_y + 1.1, hz - 0.2)
    tube(fittings, "helm_shaft", hc + v3(0, 0, 0.06), hc - v3(0, 0, 0.03), 0.06, "iron", sides=4)
    wheel = Bone("helm_wheel", origin=tuple(hc), parent=fittings)
    ring(wheel, "helm_rim", hc, (0, 0, 1), 0.3, 0.055, "brass", n=12, round_=True)
    for k in range(3):
        a = math.pi * k / 3
        d = v3(math.cos(a), math.sin(a), 0)
        tube(wheel, "helm_spoke_%d" % k, hc - d * 0.29, hc + d * 0.29, 0.04, "brass", sides=4)
    disc(wheel, "helm_hub", hc, (0, 0, 1), 0.07, 0.08, "gold", sides=8)
    dial(fittings, "helm_gauge", (0.0, main_y + 1.42, hz), (0, 0, -1), 0.1, depth=0.05)
    tube(fittings, "helm_gauge_stem", (0, main_y + 1.26, hz), (0, main_y + 1.32, hz), 0.05, "brass", sides=4)
    lever = v3(0.2, main_y + 1.24, hz - 0.05)
    tube(fittings, "helm_lever", lever, lever + v3(0.1, 0.3, -0.12), 0.035, "iron", sides=4)
    disc(fittings, "helm_lever_knob", lever + v3(0.1, 0.3, -0.12), norm(v3(0.1, 0.3, -0.12)), 0.04, 0.07, "dark_wood", sides=6)
    # the benches: two along the sides facing inwards, one across the bow facing aft
    for side, sn in SIDES:
        ga.bench(fittings, "bench_" + sn, (side * 1.05, main_y, bs.BENCH_Z), (0, 0, 1), (-side, 0, 0), 1.3)
    ga.bench(fittings, "bow_bench", (0, main_y, bs.BOW_SEAT_Z), (1, 0, 0), (0, 0, -1), 1.3, back=False)
    # ballast sacks and a coil of rope by the stern
    for k, (x, z, a) in enumerate(((-0.95, -3.55, 0.3), (0.95, -3.65, -0.4))):
        sc = v3(x, main_y + 0.13, z)
        add_cube(fittings, "sack_%d" % k, sc, ry(a), (0.3, 0.24, 0.26), "canvas")
        add_cube(fittings, "sack_top_%d" % k, sc + v3(0, 0.14, 0), ry(a + 0.3), (0.2, 0.06, 0.16), "canvas")
        add_cube(fittings, "sack_neck_%d" % k, sc + v3(0, 0.2, 0), ry(a), (0.07, 0.08, 0.07), "rope")
    rc = v3(0.0, main_y, -4.05)
    for j in range(3):
        ring(fittings, "rope_coil_%d" % j, rc + v3(0, 0.04 + 0.06 * j, 0), UP, 0.2 - 0.03 * j, 0.06, "rope", n=8, phase=0.3 * j)

    # ---------------------------------------------------------------- the boiler, its stack and pipes (aft of the column)
    bx, bz = bs.BOILER_X, bs.BOILER_Z
    tube(engine, "boiler_saddle", (bx, main_y + 0.01, bz), (bx, main_y + 0.14, bz), 1.0, "dark_wood", sides=10)
    tube(engine, "boiler", (bx, main_y + 0.14, bz), (bx, main_y + 1.5, bz), 0.92, "boiler", sides=10)
    for k, y in enumerate((0.45, 1.2)):
        tube(engine, "boiler_band_%d" % k, (bx, main_y + y - 0.04, bz), (bx, main_y + y + 0.04, bz), 0.98, "brass", sides=10)
    dome(engine, "boiler_dome", v3(bx, main_y + 1.5, bz), UP, 0.46, 0.3, "iron", steps=3)
    # the firebox door on the fore side, a glowing grate, a brass handle
    fz = bz + 0.47
    add_cube(engine, "firebox_plate", (bx, main_y + 0.55, fz), EYE, (0.5, 0.42, 0.05), "iron")
    add_cube(engine, "glow_firebox", (bx, main_y + 0.5, fz + 0.03), EYE, (0.3, 0.22, 0.012), {"all": None, "+3": "fire", "-3": "fire"}, stretch=True)
    add_cube(engine, "firebox_door", (bx + 0.14, main_y + 0.72, fz + 0.03), EYE, (0.2, 0.08, 0.04), "brass")
    disc(engine, "firebox_handle", (bx - 0.18, main_y + 0.55, fz + 0.05), (0, 0, 1), 0.04, 0.06, "brass", sides=6)
    # the stack: an iron pipe with a flared mouth and a rain cap
    sz = bz - 0.05
    tube(engine, "stack", (bx, main_y + 1.72, sz), (bx, bs.STACK_TOP - 0.2, sz), 0.38, "iron", sides=8)
    tube(engine, "stack_collar", (bx, main_y + 1.78, sz), (bx, main_y + 1.9, sz), 0.46, "brass", sides=8)
    tube(engine, "stack_mouth", (bx, bs.STACK_TOP - 0.2, sz), (bx, bs.STACK_TOP, sz), 0.5, "iron_dark", sides=8)
    for k in range(3):
        a = 2 * math.pi * k / 3
        q = v3(bx + math.cos(a) * 0.2, bs.STACK_TOP, sz + math.sin(a) * 0.2)
        tube(engine, "stack_cap_post_%d" % k, q, q + v3(0, 0.18, 0), 0.03, "iron", sides=4)
    disc(engine, "stack_cap", (bx, bs.STACK_TOP + 0.2, sz), UP, 0.36, 0.06, "iron_dark", sides=8)
    disc(engine, "stack_cap_top", (bx, bs.STACK_TOP + 0.26, sz), UP, 0.2, 0.06, "iron_dark", sides=8)
    # a pressure gauge on the starboard side of the boiler, a whistle and a steam valve on its dome
    dial(engine, "boiler_gauge", (bx + 0.5, main_y + 1.0, bz), (1, 0, 0), 0.12, depth=0.05)
    wb = v3(bx - 0.22, main_y + 1.74, bz + 0.12)
    tube(engine, "whistle_pipe", wb, wb + v3(0, 0.22, 0), 0.05, "brass", sides=4)
    tube(engine, "whistle_bell", wb + v3(0, 0.22, 0), wb + v3(0, 0.4, 0), 0.1, "brass", sides=8)
    disc(engine, "whistle_cap", wb + v3(0, 0.42, 0), UP, 0.065, 0.04, "gold", sides=8)
    ga.handwheel(engine, "steam_valve", (bx + 0.26, main_y + 1.86, bz + 0.1), (0, 1, 0), 0.09)
    tube(engine, "steam_valve_stem", (bx + 0.26, main_y + 1.7, bz + 0.1), (bx + 0.26, main_y + 1.84, bz + 0.1), 0.06, "copper", sides=4)
    # the copper fuel pipe from the boiler up the column to the burner, a stop valve on the way
    pts = catmull([v3(bx + 0.1, main_y + 1.55, bz + 0.25), v3(bx * 0.6, main_y + 1.9, bz + 0.6), v3(0.26, 2.45, cz - 0.32),
                   v3(0.26, 3.4, cz - 0.3), v3(0.22, by - 0.35, cz - 0.3)], 2)
    polyline(engine, "fuel_pipe", pts, 0.1, "copper", sides=6, extend=0.03)
    ga.handwheel(engine, "fuel_valve", v3(0.26, 2.9, cz - 0.3) + v3(0.1, 0, 0), (1, 0, 0), 0.08)
    # a second, smaller copper pipe to the lantern side and a coil of copper tubing on the boiler's port side
    for k in range(3):
        ring(engine, "coil_%d" % k, v3(bx - 0.5, main_y + 0.5 + 0.12 * k, bz), (1, 0, 0), 0.18, 0.05, "copper", n=8, phase=0.2 * k)

    # ---------------------------------------------------------------- the big wooden gear wheel on the starboard side
    ws = bs.WHEEL_SIDE
    wc = v3(bs.WHEEL_X, bs.WHEEL_Y, bs.WHEEL_Z)
    xin = ws * (hull_x(bs.WHEEL_Z, bs.WHEEL_Y) - 0.1)
    tube(engine, "wheel_axle", v3(xin, bs.WHEEL_Y, bs.WHEEL_Z), wc + v3(ws * 0.2, 0, 0), 0.16, "brass", sides=8)
    # the bearing bracket: an iron block on two struts from the planking and a stay from the rail
    bearing = wc - v3(ws * 0.4, 0, 0)
    add_cube(engine, "wheel_bearing", bearing, EYE, (0.3, 0.34, 0.34), "iron")
    for k, (y, dz) in enumerate(((0.25, 0.55), (0.25, -0.55), (1.05, 0.0))):
        p, _ = hull_pt(bs.WHEEL_Z + dz, y, ws, 0.0)
        beam(engine, "wheel_strut_%d" % k, p, bearing, 0.08, "iron", width=0.1, extend=0.05)
    # the wheel itself: a rim of oak segments, square teeth, eight spokes, a brass hub (bone side_wheel, turns under way)
    wb_ = Bone("side_wheel", origin=tuple(wc), parent=engine)
    gear(wb_, "wheel", wc, (1, 0, 0), bs.WHEEL_R, 0.16, 16, "gear_wood", 8, "wood", 0.26)
    disc(wb_, "wheel_crank", wc + v3(ws * 0.14, 0, 0), (1, 0, 0), 0.2, 0.1, "brass", sides=8)
    add_cube(wb_, "wheel_crank_pin", wc + v3(ws * 0.24, 0.12, 0), EYE, (0.1, 0.08, 0.08), "gold")
    # the pinion driving it from the top, on a shaft from the boiler through the bulwark (bone pinion)
    pr = 0.32
    pc = v3(bs.WHEEL_X, bs.WHEEL_Y + bs.WHEEL_R * 1.14 + pr * 1.05, bs.WHEEL_Z)
    pin = Bone("pinion", origin=tuple(pc), parent=engine)
    gear(pin, "pinion", pc, (1, 0, 0), pr, 0.14, 8, "brass", 0, "brass", 0.1)
    tube(engine, "pinion_shaft", v3(ws * (hull_x(bs.WHEEL_Z, 0.9) - 0.1), pc[1], pc[2]), pc + v3(ws * 0.12, 0, 0), 0.09, "iron", sides=6)
    pb = v3(ws * (hull_x(bs.WHEEL_Z, 0.9) + 0.12), pc[1], pc[2])
    add_cube(engine, "pinion_bearing", pb, EYE, (0.14, 0.26, 0.26), "iron")
    tube(engine, "pinion_bearing_post", pb - v3(0, 0.13, 0), v3(pb[0], upper_y(bs.WHEEL_Z, 0.1), pb[2]), 0.07, "iron", sides=4)
    # inside the bulwark: a brass gearbox the shaft comes from, a connecting rod from the boiler
    gbx = ws * (hull_x(bs.WHEEL_Z, 0.9) - 0.45)
    add_cube(engine, "gearbox", (gbx, main_y + 0.9, bs.WHEEL_Z), EYE, (0.5, 0.5, 0.44), "brass")
    add_cube(engine, "gearbox_lid", (gbx, main_y + 1.17, bs.WHEEL_Z), EYE, (0.4, 0.05, 0.34), "gold")
    tube(engine, "gearbox_leg", (gbx, main_y, bs.WHEEL_Z), (gbx, main_y + 0.66, bs.WHEEL_Z), 0.18, "iron", sides=4)
    polyline(engine, "gearbox_rod", [v3(gbx - ws * 0.2, main_y + 1.0, bs.WHEEL_Z + 0.1), v3(bx + ws * 0.42, main_y + 1.0, bz + 0.05)], 0.07, "iron", sides=4)

    # ---------------------------------------------------------------- the lanterns hanging under the basket's ends
    for side, sn in SIDES:
        for s, tag in ((1, "bow"), (-1, "stern")):
            z = s * bs.LANTERN_Z
            hook = v3(side * (hw(z) + 0.3), sheer(z) - 0.02, z)
            p, _ = hull_pt(z, sheer(z) - 0.28, side, 0.0)
            beam(lanterns, "bracket_%s_%s" % (tag, sn), p, hook, 0.06, "iron", width=0.08, extend=0.04)
            beam(lanterns, "bracket_stay_%s_%s" % (tag, sn), v3(side * hw(z), sheer(z) + 0.1, z), hook, 0.05, "iron", width=0.06, extend=0.03)
            gl.hanging_lantern(lanterns, "%s_%s" % (tag, sn), hook, drop=bs.LANTERN_DROP, w=0.32, h=0.46, chained=True)
    return root


def build_animations(root):
    kf, rot_kf, animation, find = gg.kf, gg.rot_kf, gg.animation, gg.find
    anims = []
    wheel = find(root, "helm_wheel")
    anims.append(animation("steer", 2.0, "hold", [
        (wheel, [rot_kf(0.0, (0, 0, -150)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 0, 150))])]))
    # the flame flares while climbing (elevator 0..2 = descending, level, climbing) and flickers all the time
    flame, core = find(root, "burner_flame"), find(root, "burner_core")
    anims.append(animation("elevator", 2.0, "hold", [
        (flame, [kf("scale", 0.0, (0.55, 0.42, 0.55)), kf("scale", 1.0, (0.8, 0.78, 0.8)), kf("scale", 2.0, (1.25, 1.6, 1.25))]),
        (core, [kf("scale", 0.0, (0.5, 0.35, 0.5)), kf("scale", 1.0, (0.85, 0.8, 0.85)), kf("scale", 2.0, (1.2, 1.7, 1.2))])]))
    anims.append(animation("flag_wave", 2.0, "loop", [
        (flame, [kf("scale", 0.0, (1.0, 1.0, 1.0)), kf("scale", 0.4, (1.08, 0.9, 1.05)), kf("scale", 0.9, (0.94, 1.12, 0.96)),
                 kf("scale", 1.5, (1.05, 0.95, 1.06)), kf("scale", 2.0, (1.0, 1.0, 1.0))]),
        (core, [kf("scale", 0.0, (1.0, 1.0, 1.0)), kf("scale", 0.5, (0.92, 1.14, 0.92)), kf("scale", 1.1, (1.1, 0.88, 1.1)),
                kf("scale", 1.6, (0.96, 1.08, 0.96)), kf("scale", 2.0, (1.0, 1.0, 1.0))])]))
    # the gear wheel turns under way (one turn per loop), its pinion the other way, faster
    side_wheel, pinion = find(root, "side_wheel"), find(root, "pinion")
    ratio = bs.WHEEL_R * 1.14 / (0.32 * 1.14)
    anims.append(animation("engine", 4.0, "loop", [
        (side_wheel, [rot_kf(t, (90 * t, 0, 0)) for t in (0.0, 1.0, 2.0, 3.0, 4.0)]),
        (pinion, [rot_kf(t, (-90 * t * ratio, 0, 0)) for t in (0.0, 1.0, 2.0, 3.0, 4.0)])]))
    tracks = []
    lan = find(root, "lanterns")
    for k, b in enumerate(c for c in lan.children if c.name.startswith("lantern_")):
        sh = (0.37 * k) % 4.0
        keys = [rot_kf(t, (5 * math.sin(2 * math.pi * (t + sh) / 4.0), 0, 4 * math.cos(2 * math.pi * (t + sh) / 4.0))) for t in (0.0, 1.0, 2.0, 3.0, 4.0)]
        tracks.append((b, keys))
    anims.append(animation("lantern_sway", 4.0, "loop", tracks))
    return anims


def main():
    if os.environ.get("BALLOON_FAST"):
        import zfight
        zfight.fix = lambda root: 0
    root = build()
    anims = build_animations(root)
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    tex_path = os.path.join(tex_dir, "entity/hot_air_balloon.png")
    bt.make_texture(tex_path)
    bt.make_item_icon(os.path.join(tex_dir, "item/hot_air_balloon.png"))
    with open(tex_path, "rb") as f:
        png = f.read()
    textures = [gn.texture_entry("hot_air_balloon.png", bt.SIZE, png, "entity", "hot_air_balloon.png")]
    textures[0]["id"] = "0"
    out = [os.path.join(ROOT, "blockbench/hot_air_balloon.bbmodel"),
           os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/hot_air_balloon.bbmodel")]
    if os.environ.get("BALLOON_OUT"):
        out = [os.environ["BALLOON_OUT"]]
    model = gn.export(root, anims, textures, out, name="hot_air_balloon", visible_box=(16, 22, 0))
    print("cubes:", len(model["elements"]), "animations:", [a["name"] for a in model["animations"]])


if __name__ == "__main__":
    main()
