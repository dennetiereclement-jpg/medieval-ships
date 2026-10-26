#!/usr/bin/env python3
"""Generates the Crystal Airship (crystal_airship, "Le Grand Dirigeable de Cristal") Blockbench model, its textures, its
item icon, its interior grid and its furniture file.

Usage:  python3 tools/generate_crystal.py          (CRYSTAL_FAST=1: no z-fighting pass, for quick previews)

Outputs:
  blockbench/crystal_airship.bbmodel                                            (editable, textures embedded)
  src/main/resources/assets/medievalships/models/entity/crystal_airship.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/crystal_airship.png, crystal_airship_interior.png
  src/main/resources/assets/medievalships/textures/item/crystal_airship.png
  src/main/resources/assets/medievalships/interiors/crystal_airship.grid         (collisions, ladder, doors, windows)
  src/main/resources/assets/medievalships/interiors/crystal_airship_decor.json   (mod furniture, seats)

Reference: the Minecraft sheet "Le Grand Dirigeable de Cristal" (perspective, side, top, front, back views and four
interior views; measurements in docs/CRYSTAL_PLAN.md). A cluster of cream balloon lobes of small knobbly squares (a big
central egg, a fore and an aft lobe on the axis, higher, four side lobes at the corners, lower) bound by gilded straps
and a girdle hung with gold chain swags and blue jewels, a mast and a red pennant on top; ropes down to a luxurious hull
of warm brown wood above and dark olive green planks below with gilded mouldings and scrolls, a row of big windows,
fan windows at the bow, a carved beak, a forecastle with turned balusters and a crenellated turret; the big golden ring
on its pillar amidships; a three-storey stern castle (lit arched windows, a green roof with a gilded eave, a brass
scroll and two pennant poles, the cockpit's great arched window facing the bow); bronze engine nacelles on the aft
sides with a glowing crystal eye, brass feathers, copper pipes and a rotor; a round stern engine with a propeller and a
crystal core; two slanted propeller pods with golden leaf blades under the stern; glowing blue crystals: a platform of
crystals under the keel, crystal lanterns under the bow and on the castle, two floating crystal pods held by ropes.

The lobes are bodies built from tilted panels between elliptical sections (no staircase), hidden where they run into
one another; the hull follows crystal_shape.hull_x the same way. The decks and the walls, floors and ceilings of the
rooms are drawn on the boundaries of the interior grid (tools/crystal_interior.py): what is drawn is what collides.
Room surfaces are named "lit*" (lit by the airship's own lamps), glowing parts "glow*".

Bones used by the mod (keep their names when editing in Blockbench):
  rotor_p, rotor_s, rear_prop, pod_prop_p, pod_prop_s (propeller: played with the engine's phase, which advances with
  the signed speed: still when parked)   helm_wheel (steer)   flap_p, flap_s (elevator)
  flag, flag_tip (flag_wave)   pennant_* (streamer_wave)   pod_front, pod_rear, pod_*_ring (streamer_wave: the floating
  pods bob and their rings turn)   lantern_* (lantern_sway)   engine_* (engine)   door_<k> (door k: 0 closed, 1 open)
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
import generate_leviathan as gl  # noqa: E402  (helpers: quad, rope, chain, lantern, gear, wheel, balustrade, greedy)
import leviathan_furniture as lf  # noqa: E402
import nautilus_furniture as nf  # noqa: E402
import crystal_shape as cs  # noqa: E402
import crystal_interior as ci  # noqa: E402
import crystal_texture as ct  # noqa: E402
import crystal_furniture as cf  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/crystal_airship/%d" % _uuid_counter[0]))


gg.new_uuid = new_uuid
gn.new_uuid = new_uuid
gn.REGIONS = {k: (0,) + r for k, r in ct.REGIONS.items()}
gn.REGIONS.update({k: (1,) + r for k, r in ct.REGIONS_IN.items()})   # the rooms and their furniture: second texture
gn.REGIONS["globe"] = (1,) + ct.REGIONS_IN["in_globe"]
for alias, name in (("organ_wood", "dark_wood"), ("silver", "steel"), ("green_leather", "red_velvet"), ("hull", "hull_brown"),
                    ("crate", "in_chest"), ("barrel", "in_staves")):
    gn.REGIONS.setdefault(alias, gn.REGIONS[name])   # names used by the Nautilus' and the Sky Leviathan's furniture
gn.SIZE = ct.SIZE

v3, norm, Bone, add_cube, beam = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam
tube, disc, ring, polyline, catmull, bezier = ga.tube, ga.disc, ga.ring, ga.polyline, ga.catmull, ga.bezier
quad, box, set_sub, rope, chain = gl.quad, gl.box, gl.set_sub, gl.rope, gl.chain
EYE = np.eye(3)
SIDES = ((1, "p"), (-1, "s"))


def _sm(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def LP(name, z, az, out=0.0):
    return v3(*cs.lobe_point(cs.lobe(name), z, az, out))


def hidden(p, own, inset=0.12):
    """Is the point inside another lobe (so a panel there is never seen)?"""
    return cs.inside_balloon(p[0], p[1], p[2], inset, skip=own)


# ================================================================ balloon
def lobe_stations(lb, n):
    """z of the sections of a lobe: denser towards its rounded ends."""
    out = []
    for k in range(n + 1):
        s = -math.cos(math.pi * k / n)          # -1 .. 1, dense at the ends
        s = math.copysign(abs(s) ** 0.85, s)
        out.append(lb[3] + lb[6] * s * 0.999)
    return out


LOBE_RES = {"c": (30, 44), "f": (20, 32), "r": (22, 34), "fp": (16, 28), "fs": (16, 28), "rp": (16, 28), "rs": (16, 28)}


def balloon(bone):
    count = 0
    for lb in cs.LOBES:
        name = lb[0]
        nst, naz = LOBE_RES[name]
        zs = lobe_stations(lb, nst)
        for i in range(len(zs) - 1):
            za, zb = zs[i], zs[i + 1]
            for j in range(naz):
                a0, a1 = 360.0 * j / naz - 180.0, 360.0 * (j + 1) / naz - 180.0
                am = (a0 + a1) / 2
                pts = [LP(name, za, a0), LP(name, zb, a0), LP(name, za, a1), LP(name, zb, a1)]
                c = sum(pts) / 4
                if hidden(c, name) and all(hidden(p, name, 0.05) for p in pts):
                    continue
                region = "cloth_dark" if abs(am) > 118 else "cloth"
                outward = norm(LP(name, (za + zb) / 2, am, 1.0) - LP(name, (za + zb) / 2, am))
                quad(bone, "lobe_%s_%d_%d" % (name, i, j), pts[0], pts[1], pts[2], pts[3], 0.12, region, outward,
                     back="cloth_dark", u_dir=v3(0, 0, 1), stretch=False, overlap=(1.03, 1.05))
                count += 1
    return count


def lobe_ring_pts(name, z, out, n=48):
    """Points round a lobe's section at z (azimuth from -180), with a flag: hidden inside another lobe."""
    pts = []
    for j in range(n + 1):
        az = 360.0 * j / n - 180.0
        p = LP(name, z, az, out)
        pts.append((az, p, hidden(p, name, 0.25)))
    return pts


def straps(bone, gems):
    """Gilded straps round the lobes, the girdle round the central lobe with its swags of gold chain, blue jewels."""
    k = 0
    for name, t in cs.STRAPS:
        lb = cs.lobe(name)
        z = lb[3] + lb[6] * t
        pts = lobe_ring_pts(name, z, 0.1, 48)
        for j in range(len(pts) - 1):
            (a0, p0, h0), (a1, p1, h1) = pts[j], pts[j + 1]
            if h0 and h1:
                continue
            nrm = norm(LP(name, z, (a0 + a1) / 2, 1.0) - LP(name, z, (a0 + a1) / 2))
            beam(bone, "strap_%d_%d" % (k, j), p0, p1, 0.12, "strap", width=0.42, up=nrm, extend=0.04, u_dir=p1 - p0)
        k += 1
    # the girdle: along both flanks of the central lobe
    zs = list(np.linspace(-14.6, 14.2, 46))
    girdle = {}
    for side, sn in SIDES:
        az = side * cs.GIRDLE_AZ
        line = []
        for z in zs:
            p = LP("c", z, az, 0.12)
            line.append((z, p, hidden(p, "c", 0.25)))
        girdle[side] = line
        for j in range(len(line) - 1):
            (za, pa, ha), (zb, pb, hb) = line[j], line[j + 1]
            if ha and hb:
                continue
            nrm = norm(LP("c", (za + zb) / 2, az, 1.0) - LP("c", (za + zb) / 2, az))
            beam(bone, "girdle_%s_%d" % (sn, j), pa, pb, 0.12, "girdle", width=0.5, up=nrm, extend=0.05)
    # swags of gold chain between the straps along the girdle, a jewel where each strap crosses it
    cross_z = sorted(cs.lobe("c")[3] + cs.lobe("c")[6] * t for n_, t in cs.STRAPS if n_ == "c")
    for side, sn in SIDES:
        az = side * cs.GIRDLE_AZ
        for j, z in enumerate(cross_z):
            p = LP("c", z, az, 0.22)
            nrm = norm(LP("c", z, az, 1.0) - LP("c", z, az))
            disc(gems, "glow_gem_%s%d" % (sn, j), p, nrm, 0.26, 0.12, "gem", sides=8)
            disc(bone, "gem_setting_%s%d" % (sn, j), p - nrm * 0.05, nrm, 0.36, 0.08, "gold", sides=8)
        for j in range(len(cross_z) - 1):
            za, zb = cross_z[j], cross_z[j + 1]
            for drop, w in ((1.2, 0.17), (0.6, 0.13)):
                pts = []
                for q in range(9):
                    z = za + (zb - za) * q / 8
                    sag = drop * math.sin(math.pi * q / 8)
                    p = LP("c", z, az + side * 8 * math.sin(math.pi * q / 8), 0.18 + 0.15 * math.sin(math.pi * q / 8)) - v3(0, sag, 0)
                    pts.append(p)
                polyline(bone, "swag_%s%d_%d" % (sn, j, int(drop * 10)), pts, w, "gold", sides=4)
    # jewels on the other straps (their lowest visible points on the flanks)
    for k, (name, t) in enumerate(cs.STRAPS):
        if name == "c":
            continue
        lb = cs.lobe(name)
        z = lb[3] + lb[6] * t
        for side in (1, -1):
            az = side * 100
            p = LP(name, z, az, 0.22)
            if hidden(p, name, 0.2):
                continue
            nrm = norm(LP(name, z, az, 1.0) - LP(name, z, az))
            disc(gems, "glow_gem_s%d_%d" % (k, side > 0), p, nrm, 0.22, 0.12, "gem", sides=8)
    # a strap along the top of the central and the end lobes
    for name in ("c", "f", "r"):
        lb = cs.lobe(name)
        zz = lobe_stations(lb, 16)[1:-1]
        for j in range(len(zz) - 1):
            pa, pb = LP(name, zz[j], 0.0, 0.1), LP(name, zz[j + 1], 0.0, 0.1)
            if hidden(pa, name, 0.25) and hidden(pb, name, 0.25):
                continue
            beam(bone, "top_strap_%s_%d" % (name, j), pa, pb, 0.12, "strap", width=0.36, up=v3(0, 1, 0), extend=0.05)
    return girdle


def mast(bone, root):
    y0, y1, z = cs.MAST_BASE - 0.4, cs.MAST_TOP, cs.MAST_Z
    tube(bone, "mast", (0, y0, z), (0, y1, z), 0.24, "dark_wood", sides=8)
    disc(bone, "mast_foot", (0, y0 + 0.4, z), (0, 1, 0), 0.7, 0.3, "gold", sides=12)
    disc(bone, "mast_crow", (0, cs.CROW_Y, z), (0, 1, 0), 1.7, 0.28, "brass", sides=16)
    disc(bone, "mast_crow_rim", (0, cs.CROW_Y + 0.18, z), (0, 1, 0), 1.75, 0.12, "gold", sides=16)
    disc(bone, "mast_crow_under", (0, cs.CROW_Y - 0.25, z), (0, 1, 0), 1.1, 0.25, "bronze", sides=12)
    for k in range(4):
        a = math.pi / 2 * k + math.pi / 4
        d = v3(math.cos(a), 0, math.sin(a))
        beam(bone, "mast_crow_strut_%d" % k, v3(0, cs.CROW_Y - 0.9, z), v3(0, cs.CROW_Y, z) + d * 1.4, 0.1, "brass")
    for y in (cs.CROW_Y + 1.4, y1 - 0.4):
        disc(bone, "mast_band_%d" % int(y * 10), (0, y, z), (0, 1, 0), 0.2, 0.12, "gold", sides=8)
    disc(bone, "mast_finial", (0, y1 + 0.1, z), (0, 1, 0), 0.22, 0.2, "gold", sides=8)
    disc(bone, "mast_finial_ball", (0, y1 + 0.3, z), (0, 1, 0), 0.14, 0.2, "gold", sides=8)
    # stays from the crow's nest down to the straps
    for k, (name, t, az) in enumerate((("c", 0.6, 60), ("c", 0.6, -60), ("c", -0.52, 60), ("c", -0.52, -60))):
        lb = cs.lobe(name)
        zz = lb[3] + lb[6] * t
        rope(bone, "mast_stay_%d" % k, v3(0, cs.CROW_Y + 1.5, z), LP(name, zz, az, 0.15), d=0.06, region="rope_dark")
    flag(root, "flag", v3(0, y1 - 0.15, z - 0.12), 6.6, 1.6)


def flag(parent, name, root_pt, w, h, region="flag", n=4, along=(0, 0, -1)):
    """A pennant streaming along `along` in two bones (name, name_tip), each half of n strips following a soft wave."""
    root_pt = v3(*root_pt)
    al = norm(v3(*along))
    side = norm(np.cross(v3(0, 1, 0), al))
    fb = Bone(name, origin=tuple(root_pt), parent=parent)
    ft = Bone(name + "_tip", origin=tuple(root_pt + al * (w / 2)), parent=fb)
    amp = min(0.22, 0.06 * w)

    def Pf(s):
        return root_pt + side * (amp * math.sin(2 * math.pi * s * 1.4) * (0.3 + s)) + al * (w * s)
    for half, bone in enumerate((fb, ft)):
        for k in range(n):
            s0, s1 = (half + k / n) / 2, (half + (k + 1) / n) / 2
            a, b = Pf(s0), Pf(s1)
            d = norm(b - a)
            axes = np.column_stack([np.cross(v3(0, 1, 0), d), v3(0, 1, 0), d])
            cube = add_cube(bone, "%s_%s%d" % (name, "ab"[half], k), (a + b) / 2 + v3(0, -h / 2, 0), axes,
                            (0.03, h, np.linalg.norm(b - a) + 0.015), {"all": None, "+1": region, "-1": region},
                            stretch=True, u_dir=al, v_dir=v3(0, -1, 0))
            set_sub(cube, (s0, 0, s1, 1))
    return fb


# ================================================================ the golden ring
def golden_ring(bone, detail):
    c = v3(0, cs.RING_Y, cs.RING_Z)
    ro, w, t = cs.RING_R, cs.RING_W, cs.RING_T
    rm = ro - w / 2
    n = 48
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        p0 = c + v3(0, math.cos(a0), math.sin(a0)) * rm
        p1 = c + v3(0, math.cos(a1), math.sin(a1)) * rm
        am = (a0 + a1) / 2
        rad = v3(0, math.cos(am), math.sin(am))
        beam(bone, "ring_%d" % k, p0, p1, w, "gold", width=t, up=rad, extend=0.03)
        # a raised bead on both faces and blocky studs round the rim (the reference's chunky gilded ring)
        for sx in (1, -1):
            q0 = c + v3(sx * (t / 2 + 0.04), 0, 0) + v3(0, math.cos(a0), math.sin(a0)) * (ro - 0.12)
            q1 = c + v3(sx * (t / 2 + 0.04), 0, 0) + v3(0, math.cos(a1), math.sin(a1)) * (ro - 0.12)
            beam(detail, "ring_bead_%d_%d" % (k, sx > 0), q0, q1, 0.12, "brass", width=0.1, up=rad, extend=0.02)
            q0 = c + v3(sx * (t / 2 + 0.04), 0, 0) + v3(0, math.cos(a0), math.sin(a0)) * (ro - w + 0.12)
            q1 = c + v3(sx * (t / 2 + 0.04), 0, 0) + v3(0, math.cos(a1), math.sin(a1)) * (ro - w + 0.12)
            beam(detail, "ring_bead_in_%d_%d" % (k, sx > 0), q0, q1, 0.1, "brass", width=0.1, up=rad, extend=0.02)
        if k % 2 == 0:
            add_cube(bone, "ring_stud_%d" % k, c + rad * (ro + 0.06), np.column_stack([v3(1, 0, 0), rad, np.cross(v3(1, 0, 0), rad)]),
                     (t * 0.8, 0.16, 2 * math.pi * ro / n * 0.7), "gold")
    # the pillar: a turned brass column on a plinth, a lattice cage round it, a cradle under the ring
    hw, top = cs.PEDESTAL
    z = cs.RING_Z
    box(bone, "ring_plinth", (0, 0.2, z), (1.6, 0.4, 1.6), {"all": "dark_wood", "+2": "brass"})
    box(bone, "ring_plinth_trim", (0, 0.42, z), (1.3, 0.08, 1.3), "gold")
    tube(bone, "ring_pillar", (0, 0.4, z), (0, top, z), 0.62, "brass", sides=8)
    for k, y in enumerate((0.9, 1.6, top - 0.2)):
        tube(bone, "ring_pillar_band_%d" % k, (0, y - 0.07, z), (0, y + 0.07, z), 0.8, "gold", sides=8)
    for k, (dx, dz) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        p0, p1 = v3(dx * 0.62, 0.4, z + dz * 0.62), v3(dx * 0.3, top, z + dz * 0.3)
        tube(detail, "ring_cage_%d" % k, p0, p1, 0.08, "iron", sides=4)
    for k in range(3):
        y = 0.6 + 0.6 * k
        for e in range(4):
            a, b = [v3(dx * 0.58, y, z + dz * 0.58) for dx, dz in ((1, 1), (1, -1), (-1, -1), (-1, 1), (1, 1))[e:e + 2]]
            beam(detail, "ring_cage_h_%d_%d" % (k, e), a, b, 0.05, "iron")
    # the cradle: two curved brass arms holding the ring's lower arc
    for sx in (1, -1):
        pts = [c + v3(sx * (t / 2 + 0.12), 0, 0) + v3(0, -math.cos(a), math.sin(a)) * (ro + 0.05) for a in np.linspace(-0.6, 0.6, 7)]
        polyline(bone, "ring_cradle_%d" % (sx > 0), pts, 0.16, "brass", sides=4)
    # a rod from the ring's top into the balloon's belly, with a jewel
    tube(bone, "ring_hanger", c + v3(0, ro - 0.1, 0), c + v3(0, ro + 0.9, 0), 0.2, "brass", sides=6)
    disc(bone, "ring_hanger_plate", c + v3(0, ro + 0.85, 0), (0, 1, 0), 0.5, 0.1, "gold", sides=8)


# ================================================================ hull
HULL_ST = sorted(set([cs.STERN_Z, -22.85, -22.6, -22.2, -21.6, -20.8, -19.8, -18.6, -17.2, -15.6, -14.0, -12.4, -10.8, -9.2, -7.5,
                      -6.0, -4.0, -3.0, -1.0, 0.0, 2.0, 3.0, 5.0, 6.0, 8.0, 9.4, 10.6, 11.8, 13.0, 14.2, 15.4, 16.6, 17.8, 19.0,
                      20.1, 21.1, 22.0, 22.8, 23.5, 24.1, 24.6, 25.0, 25.35, 25.65, 25.9, 26.08]))
BOT_F = [0.0, 0.04, 0.1, 0.18, 0.28, 0.4, 0.54, 0.7, 0.85, 1.0]   # fractions from the keel up to the band (y -4)
BAND_Y = -4.0
UP_LEVELS = [-3.0, -2.0, -1.0, 0.0, cs.SHEER_WAIST, 1.6, 2.3, cs.FORECASTLE_Y + cs.RAIL_H]


def section(z, side):
    """Points of the hull's outside at z, from the keel up to the sheer (fixed count: collapsed where the hull is low)."""
    k = cs.keel_y(z)
    top = cs.sheer_y(z)
    yb = max(k, min(BAND_Y, top))
    ys = [k + f * (yb - k) for f in BOT_F] + [min(max(y, yb), top) for y in UP_LEVELS]
    return [v3(side * max(0.03, cs.hull_x(z, y)), y, z) for y in ys]


def hull_pt(z, y, side, out=0.0):
    x = cs.hull_x(z, y)
    e = 0.05
    dx = (cs.hull_x(z + e, y) - cs.hull_x(z - e, y)) / (2 * e)
    dy = (cs.hull_x(z, y + e) - cs.hull_x(z, y - e)) / (2 * e)
    n = norm(v3(side, -dy, -dx))
    return v3(side * x, y, z) + n * out, n


def in_window(z, y):
    return any(z0 - 1e-6 <= z <= z1 + 1e-6 for z0, z1 in ci.LOUNGE_WINDOWS) and ci.WIN_Y[0] - 1e-6 <= y <= ci.WIN_Y[1] + 1e-6


def side_curve(bone, name, zz, yfn, side, out, h, th, region, min_x=0.3):
    pts = []
    for z in zz:
        y = yfn(z)
        if cs.hull_x(z, y) < min_x or y < cs.keel_y(z) + 0.1 or y > cs.sheer_y(z) + 0.01:
            if pts:
                break
            continue
        pts.append(hull_pt(z, y, side, out)[0])
    for k in range(len(pts) - 1):
        beam(bone, "%s_%d" % (name, k), pts[k], pts[k + 1], h, region, width=th, up=v3(0, 1, 0), extend=0.05, u_dir=pts[k + 1] - pts[k])
    return pts


def hull(bone, detail, lights):
    for side, sn in SIDES:
        for i in range(len(HULL_ST) - 1):
            za, zb = HULL_ST[i], HULL_ST[i + 1]
            A, B = section(za, side), section(zb, side)
            for k in range(len(A) - 1):
                if abs(A[k + 1][1] - A[k][1]) < 0.02 and abs(B[k + 1][1] - B[k][1]) < 0.02:
                    continue
                mid = (A[k] + A[k + 1] + B[k] + B[k + 1]) / 4
                if in_window(mid[2], mid[1]):
                    continue
                region = "hull_green" if mid[1] < BAND_Y + 0.01 else "hull_brown"
                outward = norm(v3(side, -0.5 if k < 5 else 0.0, 0.25 * np.sign(mid[2])))
                quad(bone, "hull_%s%d_%d" % (sn, i, k), A[k], B[k], A[k + 1], B[k + 1], 0.14, region, outward, u_dir=v3(0, 0, 1),
                     stretch=False, back="dark_wood", overlap=(1.03, 1.06))
    # the flat of the bottom between the two sides
    for i in range(len(HULL_ST) - 1):
        za, zb = HULL_ST[i], HULL_ST[i + 1]
        if zb > 25.0:
            break
        xa, xb = cs.hull_x(za, cs.keel_y(za)), cs.hull_x(zb, cs.keel_y(zb))
        ya, yb = cs.keel_y(za), cs.keel_y(zb)
        quad(bone, "bottom_%d" % i, v3(-xa, ya, za), v3(-xb, yb, zb), v3(xa, ya, za), v3(xb, yb, zb), 0.14, "hull_green", v3(0, -1, 0),
             u_dir=v3(0, 0, 1), stretch=False)
    # the transom (flat, under the castle), in horizontal strips
    z = cs.STERN_Z
    ys = [cs.keel_y(z) + (cs.SHEER_WAIST - cs.keel_y(z)) * f for f in np.linspace(0, 1, 9)]
    for k in range(len(ys) - 1):
        ya, yb = ys[k], ys[k + 1]
        xa, xb = cs.hull_x(z, ya), cs.hull_x(z, yb)
        quad(bone, "transom_%d" % k, v3(-xa, ya, z), v3(xa, ya, z), v3(-xb, yb, z), v3(xb, yb, z), 0.14,
             "hull_green" if (ya + yb) / 2 < BAND_Y else "hull_brown", v3(0, 0, -1), u_dir=v3(1, 0, 0), stretch=False)
    # the keel and the stem, sweeping up into the carved beak
    kp = [v3(0, cs.keel_y(z) - 0.1, z) for z in np.linspace(cs.STERN_Z + 0.3, 25.6, 30)] + [v3(0, 1.0, 26.15), v3(0, 1.9, 26.2)]
    sm = catmull(kp, 2)
    for k in range(len(sm) - 1):
        beam(bone, "keel_%d" % k, sm[k], sm[k + 1], 0.44, "hull_band", width=0.4, up=v3(1, 0, 0), extend=0.08)
    # gilded mouldings: under the rail, along the top and the bottom of the brown band, under the windows
    zz = list(np.linspace(cs.STERN_Z + 0.05, 26.0, 80))
    for side, sn in SIDES:
        side_curve(bone, "trim_band_" + sn, zz, lambda z: BAND_Y, side, 0.06, 0.26, 0.12, "trim_gold")
        side_curve(bone, "trim_rail_" + sn, zz, lambda z: cs.SHEER_WAIST - 0.22, side, 0.06, 0.2, 0.1, "trim_gold")
        side_curve(bone, "wale_deck_" + sn, zz, lambda z: -0.45, side, 0.07, 0.34, 0.14, "trim_dark")
        side_curve(bone, "wale_low_" + sn, zz, lambda z: -6.6, side, 0.05, 0.3, 0.12, "hull_band")
        side_curve(detail, "trim_sill_" + sn, list(np.linspace(-6.3, 8.3, 20)), lambda z: ci.WIN_Y[0] - 0.12, side, 0.08, 0.16, 0.12,
                   "trim_gold")
        side_curve(detail, "trim_head_" + sn, list(np.linspace(-6.3, 8.3, 20)), lambda z: ci.WIN_Y[1] + 0.12, side, 0.08, 0.16, 0.12,
                   "trim_gold")
        side_curve(bone, "fc_moulding_" + sn, list(np.linspace(cs.FORECASTLE_Z - 0.4, 25.9, 16)), lambda z: cs.sheer_y(z) - 0.3, side,
                   0.06, 0.2, 0.12, "trim_gold")
    # the big windows of the lounge (seen through: frames and mullions), pilasters between them
    for side, sn in SIDES:
        for k, (z0, z1) in enumerate(ci.LOUNGE_WINDOWS):
            y0, y1 = ci.WIN_Y
            pa, na = hull_pt(z0, (y0 + y1) / 2, side, 0.0)
            pb, nb = hull_pt(z1, (y0 + y1) / 2, side, 0.0)
            n = norm(na + nb)
            # the window sits in the hull's thickness: its frame at the outer face, the reveal round it
            c = (pa + pb) / 2 + n * 0.01
            R = np.column_stack([norm(pb - pa), v3(0, 1, 0), n])
            R[:, 1] = norm(np.cross(R[:, 2], R[:, 0]))
            L = np.linalg.norm(pb - pa)
            add_cube(bone, "window_%s%d" % (sn, k), c, R, (L, y1 - y0, 0.06), {"all": None, "+3": "window_frame", "-3": "window_frame"},
                     stretch=True)
            for e, (pz, nz) in enumerate(((pa, na), (pb, nb))):
                add_cube(detail, "window_reveal_%s%d_%d" % (sn, k, e), pz - n * 0.45, R, (0.08, y1 - y0, 0.9), "dark_wood")
            add_cube(detail, "window_reveal_top_%s%d" % (sn, k), c - n * 0.45 + v3(0, (y1 - y0) / 2, 0), R, (L, 0.08, 0.9), "dark_wood")
            add_cube(detail, "window_reveal_bot_%s%d" % (sn, k), c - n * 0.45 - v3(0, (y1 - y0) / 2, 0), R, (L, 0.08, 0.9), "dark_wood")
        edges = sorted(set([z for w in ci.LOUNGE_WINDOWS for z in w]))
        posts = [edges[0]] + [(edges[i] + edges[i + 1]) / 2 for i in range(1, len(edges) - 1, 2)] + [edges[-1]]
        for k, z in enumerate(posts):
            pts = [hull_pt(z, y, side, 0.08)[0] for y in np.linspace(ci.WIN_Y[0] - 0.25, ci.WIN_Y[1] + 0.25, 4)]
            polyline(detail, "pilaster_%s%d" % (sn, k), pts, 0.26, "dark_wood", sides=4, extend=0.02)
            p, n = hull_pt(z, ci.WIN_Y[1] + 0.2, side, 0.16)
            box(detail, "pilaster_cap_%s%d" % (sn, k), p, (0.34, 0.14, 0.34), "gold", R=gl.wall_frame(n))
            p, n = hull_pt(z, ci.WIN_Y[0] - 0.2, side, 0.16)
            box(detail, "pilaster_base_%s%d" % (sn, k), p, (0.34, 0.14, 0.34), "gold", R=gl.wall_frame(n))
    # the fan windows of the bow (lit), small lit windows on the forecastle, gilded scrolls on the green
    zr, yr, rr = ci.ROSE
    for side, sn in SIDES:
        p, n = hull_pt(zr, yr - rr / 2, side, 0.03)
        R = gl.wall_frame(n)
        add_cube(lights, "glow_rose_%s" % sn, p, R, (2 * rr, rr, 0.03), {"all": None, "+3": "window_rose", "-3": "window_rose"}, stretch=True)
        ring_pts = [hull_pt(zr + math.cos(a) * (rr + 0.08), yr - math.sin(a) * (rr + 0.08), side, 0.08)[0] for a in np.linspace(0, math.pi, 13)]
        polyline(detail, "rose_rim_%s" % sn, ring_pts, 0.16, "gold", sides=4)
        for k, z in enumerate((16.4, 18.0)):
            p, n = hull_pt(z, 1.7, side, 0.03)
            add_cube(lights, "glow_fc_window_%s%d" % (sn, k), p, gl.wall_frame(n), (0.6, 0.95, 0.03),
                     {"all": None, "+3": "window_lit", "-3": "window_lit"}, stretch=True)
        for k, (z, y, s) in enumerate(((21.0, 1.3, 1.5), (19.4, -2.0, 1.7), (14.6, -1.6, 1.5), (-9.0, -5.4, 1.6), (-13.0, -5.6, 1.6))):
            p, n = hull_pt(z, y, side, 0.04)
            add_cube(detail, "scroll_%s%d" % (sn, k), p, gl.wall_frame(n), (s, s * 0.6, 0.03), {"all": None, "+3": "scroll", "-3": "scroll"},
                     stretch=True)
    # a carved beak under the forecastle's bow, gilded
    (bz0, by0), (bz1, by1) = cs.BEAK
    pts = [v3(0, by0, bz0), v3(0, by0 + 0.05, (bz0 + bz1) / 2), v3(0, by1, bz1)]
    polyline(bone, "beak", pts, 0.42, "dark_wood", sides=6)
    tube(bone, "beak_tip", v3(0, by1, bz1), v3(0, by1 + 0.05, bz1 + 0.5), 0.26, "gold", sides=6)
    for k, z in enumerate((26.6, 27.3)):
        disc(bone, "beak_band_%d" % k, v3(0, by0 + (by1 - by0) * (z - bz0) / (bz1 - bz0), z), (0, 0, 1), 0.28, 0.1, "gold", sides=6)
    # the inner faces of the bulwarks (seen from the decks), the cap rail
    for side, sn in SIDES:
        zz = list(np.linspace(cs.CASTLE_Z + 0.05, 25.6, 46))
        for k in range(len(zz) - 1):
            za, zb = zz[k], zz[k + 1]
            ta, tb = cs.sheer_y(za), cs.sheer_y(zb)
            da, db = cs.deck_y(za), cs.deck_y(zb)
            xa0, xa1 = cs.hull_x(za, da) - cs.SHELL, cs.hull_x(za, ta) - cs.SHELL
            xb0, xb1 = cs.hull_x(zb, db) - cs.SHELL, cs.hull_x(zb, tb) - cs.SHELL
            if min(xa0, xb0) < 0.3:
                continue
            quad(bone, "bulwark_in_%s%d" % (sn, k), v3(side * xa0, da, za), v3(side * xb0, db, zb), v3(side * xa1, ta, za),
                 v3(side * xb1, tb, zb), 0.08, "panel_green" if za > cs.FORECASTLE_Z else "hull_brown", v3(-side, 0, 0), u_dir=v3(0, 0, 1),
                 stretch=False)
        zz = list(np.linspace(cs.STERN_Z + 0.1, 25.9, 70))
        for k in range(len(zz) - 1):
            ya, yb = cs.sheer_y(zz[k]), cs.sheer_y(zz[k + 1])
            if zz[k + 1] < cs.CASTLE_Z:
                continue
            pa = v3(side * (cs.hull_x(zz[k], ya) - 0.16), ya + 0.06, zz[k])
            pb = v3(side * (cs.hull_x(zz[k + 1], yb) - 0.16), yb + 0.06, zz[k + 1])
            beam(bone, "cap_%s%d" % (sn, k), pa, pb, 0.14, "rail", width=0.42, extend=0.04)
    # the forecastle's face to the main deck: green panels in gilded frames
    zf = cs.FORECASTLE_Z
    w = cs.hull_x(zf, 1.0) - cs.SHELL
    quad(bone, "fc_face", v3(-w, 0.0, zf), v3(w, 0.0, zf), v3(-w, cs.FORECASTLE_Y, zf), v3(w, cs.FORECASTLE_Y, zf), 0.1, "panel_green",
         v3(0, 0, -1), u_dir=v3(1, 0, 0), stretch=False)


# ================================================================ decks, rails, the turret, stairs
MAX_TILE = 4


def grid_floor(bone, g, y, region, name, lit=True, zrange=None):
    """Top faces of the solid cells at height y that are walked on, tiled in 2 block tiles."""
    j = int(round((y - ci.Y0) / ci.CELL))
    below = g.k[:, j - 1, :]
    above = g.k[:, j, :]
    mask = (below == ci.SOLID) & ((above == ci.OUT) | (above == ci.DRY) | (above == ci.FURNITURE) | (above >= ci.DOOR))
    if zrange is not None:
        mask &= ((g.zs >= zrange[0]) & (g.zs <= zrange[1]))[None, :]
    key = np.zeros(mask.shape, dtype=np.int16)
    count = 0
    for (i0, j0, i1, j1, kk) in gl.greedy(mask, key, True, True):
        x0, x1 = ci.X0 + i0 * ci.CELL, ci.X0 + (i1 + 1) * ci.CELL
        z0, z1 = ci.Z0 + j0 * ci.CELL, ci.Z0 + (j1 + 1) * ci.CELL
        cube = add_cube(bone, "%s%s_%d" % ("lit_" if lit else "", name, count), v3((x0 + x1) / 2, y - 0.005, (z0 + z1) / 2), EYE,
                        (x1 - x0, 0.01, z1 - z0), {"+2": region}, u_dir=v3(0, 0, 1), v_dir=v3(1, 0, 0))
        set_sub(cube, ((j0 % MAX_TILE) / MAX_TILE, (i0 % MAX_TILE) / MAX_TILE, (j1 % MAX_TILE + 1) / MAX_TILE, (i1 % MAX_TILE + 1) / MAX_TILE))
        count += 1
    return count


def decks(bone, detail, g):
    n = grid_floor(bone, g, cs.MAIN_DECK_Y, "deck", "main_deck", lit=False, zrange=(cs.CASTLE_Z, cs.FORECASTLE_Z + 0.3))
    n += grid_floor(bone, g, cs.FORECASTLE_Y, "deck", "forecastle_deck", lit=False, zrange=(cs.FORECASTLE_Z - 0.3, 30))
    n += grid_floor(bone, g, cs.L1_TOP, "deck", "terrace", lit=False, zrange=(cs.L2_Z - 0.2, cs.CASTLE_Z + 0.2))
    # balustrades: along the waist's bulwark, round the forecastle, across its front (gaps at the stairs)
    for side, sn in SIDES:
        zz = np.linspace(cs.CASTLE_Z + 0.4, cs.FORECASTLE_Z - 0.9, 26)
        pts = [(side * (cs.hull_x(z, cs.SHEER_WAIST) - 0.16), cs.sheer_y(z) + 0.13, z) for z in zz]
        gl.balustrade(bone, "waist_rail_" + sn, pts, h=0.62, step=0.42, turned=True, newel=8)
    yf = cs.FORECASTLE_Y + cs.RAIL_H
    zz = list(np.linspace(cs.FORECASTLE_Z + 0.2, 25.55, 14))
    port = [(cs.hull_x(z, cs.SHEER_WAIST) - 0.16, yf + 0.12, z) for z in zz] + [(0.0, yf + 0.12, 25.75)]
    gl.balustrade(bone, "fc_rail", port + [(-x, y, z) for x, y, z in reversed(port[:-1])], h=0.66, step=0.42, turned=True, newel=6)
    stair_x = sorted([(st[1], st[2]) for st in ci.STAIRS if st[0].startswith("fc_")])
    w = cs.hull_x(cs.FORECASTLE_Z, cs.SHEER_WAIST) - 0.5
    segs, x = [], -w
    for a, b in stair_x:
        segs.append((x, a))
        x = b
    segs.append((x, w))
    for k, (a, b) in enumerate(segs):
        if b - a > 0.3:
            gl.balustrade(bone, "fc_front_rail_%d" % k, [(a, cs.FORECASTLE_Y, cs.FORECASTLE_Z + 0.25), (b, cs.FORECASTLE_Y, cs.FORECASTLE_Z + 0.25)],
                          h=1.0, step=0.42, turned=True, newel=50)
    # the terrace on the castle's first storey: its balustrade
    y = cs.L1_TOP
    za, zb = cs.L2_Z, cs.CASTLE_Z - 0.25
    xs = cs.castle_x(zb, y) - 0.25
    xa = cs.castle_x(za, y) - 0.25
    gl.balustrade(bone, "terrace_rail", [(xa, y, za), (xs, y, zb), (-xs, y, zb), (-xa, y, za)], h=0.9, step=0.42, turned=True, newel=6)
    return n


def stairs(outside, inside):
    for st in ci.STAIRS:
        name, x0, x1, zs, d, y0, n = st
        interior = not name.startswith("fc_")
        bone = inside if interior else outside
        pre = "lit_" if interior else ""
        for k, (sx0, sx1, sz0, sz1, top) in enumerate(ci.stair_steps(st)):
            bottom = top - 0.5 if interior else y0
            c = v3((sx0 + sx1) / 2, (top + bottom) / 2, (sz0 + sz1) / 2)
            add_cube(bone, "%sstair_%s_%d" % (pre, name, k), c, EYE, (sx1 - sx0, top - bottom, sz1 - sz0),
                     {"all": "dark_wood", "+2": "deck"}, u_dir=v3(1, 0, 0))
            nose_z = sz1 if (d > 0) == (n > 0) else sz0
            add_cube(bone, "%sstair_%s_%d_nose" % (pre, name, k), v3(c[0], top - 0.04, nose_z), EYE, (sx1 - sx0 + 0.02, 0.08, 0.08), "trim_gold")
        if not interior:
            steps = ci.stair_steps(st)
            xin = x0 if abs(x0) < abs(x1) else x1
            pts = [(xin, s[4], (s[2] + s[3]) / 2) for s in steps]
            gl.balustrade(bone, "stair_rail_" + name, [pts[0], pts[-1]], h=0.95, step=0.7)


def turret(bone, detail, lights):
    """The crenellated turret at the foot of the forecastle: dark planks with iron bands, lit loopholes, merlons."""
    hw, z0, z1, top = cs.TURRET
    body = top - 0.7
    box(bone, "turret_body", (0, body / 2, (z0 + z1) / 2), (2 * hw, body, z1 - z0), {"all": "turret", "+2": "dark_wood"})
    box(bone, "turret_cornice", (0, body + 0.1, (z0 + z1) / 2), (2 * hw + 0.3, 0.2, z1 - z0 + 0.3), "cornice")
    for k in range(6):
        for e in (0, 1):
            if k % 2:
                continue
            # merlons along the four sides
            pass
    for sx in (-1, 1):
        for k, z in enumerate(np.linspace(z0 + 0.35, z1 - 0.35, 4)):
            box(bone, "turret_merlon_%d_%d" % (sx > 0, k), (sx * (hw + 0.05), body + 0.45, z), (0.35, 0.5, 0.42), "turret")
    for sz, zz in ((-1, z0), (1, z1)):
        for k, x in enumerate(np.linspace(-hw + 0.35, hw - 0.35, 3)):
            box(bone, "turret_merlon_z%d_%d" % (sz > 0, k), (x, body + 0.45, zz + sz * 0.05), (0.42, 0.5, 0.35), "turret")
    for sx in (-1, 1):
        for k, z in enumerate((z0 + 0.9, z1 - 0.9)):
            add_cube(lights, "glow_turret_window_%d_%d" % (sx > 0, k), v3(sx * (hw + 0.01), body - 0.9, z), EYE, (0.02, 0.6, 0.4),
                     {"all": None, "+1": "window_lit", "-1": "window_lit"}, stretch=True)
    add_cube(lights, "glow_turret_window_aft", v3(0, body - 0.9, z0 - 0.01), EYE, (0.5, 0.7, 0.02),
             {"all": None, "+3": "window_lit", "-3": "window_lit"}, stretch=True)


# ================================================================ the stern castle
def castle(bone, detail, lights, roof_bone):
    """Storey 1 on the main deck, storey 2 (the cockpit) aft of L2_Z: walls of vertical boards between gilded pilasters,
    lit arched windows, the cockpit's see-through side windows and great arch, cornices, the green roof."""
    zs1 = list(np.linspace(cs.STERN_Z, cs.CASTLE_Z, 14))
    for side, sn in SIDES:
        # storey 1 and 2 side walls (storey 2 has holes for its see-through windows)
        for lvl, (y0, y1, z0, z1) in enumerate(((cs.L1_Y, cs.L1_TOP, cs.STERN_Z, cs.CASTLE_Z), (cs.L2_Y, cs.L2_TOP, cs.STERN_Z, cs.L2_Z))):
            cuts = sorted(set([z0, z1] + ([z for w in ci.COCKPIT_WINDOWS for z in w] if lvl == 1 else [])))
            cuts = [z for z in cuts if z0 <= z <= z1]
            for k in range(len(cuts) - 1):
                za, zb = cuts[k], cuts[k + 1]
                win = lvl == 1 and any(abs(za - a) < 1e-6 and abs(zb - b) < 1e-6 for a, b in ci.COCKPIT_WINDOWS)
                xa, xb = side * cs.castle_x(za, y0), side * cs.castle_x(zb, y0)
                if win:
                    wy0, wy1 = ci.COCKPIT_WIN_Y
                    for (ya, yb) in ((y0, wy0), (wy1, y1)):
                        quad(bone, "castle_wall_%s%d_%d_%d" % (sn, lvl, k, int(ya * 10)), v3(xa, ya, za), v3(xb, ya, zb), v3(xa, yb, za),
                             v3(xb, yb, zb), 0.14, "wall_wood", v3(side, 0, 0), u_dir=v3(0, 0, 1), stretch=False, back="dark_wood")
                    c = v3((xa + xb) / 2 + side * 0.01, (wy0 + wy1) / 2, (za + zb) / 2)
                    add_cube(bone, "cockpit_window_%s%d" % (sn, k), c, EYE, (0.06, wy1 - wy0, zb - za),
                             {"all": None, "+1": "window_arch", "-1": "window_arch"}, stretch=True, u_dir=v3(0, 0, -side), v_dir=v3(0, -1, 0))
                    continue
                nseg = max(1, int(round((zb - za) / 1.0)))
                for s in range(nseg):
                    zA, zB = za + (zb - za) * s / nseg, za + (zb - za) * (s + 1) / nseg
                    xA, xB = side * cs.castle_x(zA, y0), side * cs.castle_x(zB, y0)
                    quad(bone, "castle_wall_%s%d_%d_%d" % (sn, lvl, k, s), v3(xA, y0, zA), v3(xB, y0, zB), v3(xA, y1, zA), v3(xB, y1, zB), 0.14,
                         "wall_wood", v3(side, 0, 0), u_dir=v3(0, 0, 1), stretch=False, back="dark_wood")
            # cornice at the top of the storey, a dark plinth at its foot
            zz = list(np.linspace(z0, z1, 8))
            for k in range(len(zz) - 1):
                pa = v3(side * (cs.castle_x(zz[k], y1) + 0.1), y1 - 0.12, zz[k])
                pb = v3(side * (cs.castle_x(zz[k + 1], y1) + 0.1), y1 - 0.12, zz[k + 1])
                beam(bone, "castle_cornice_%s%d_%d" % (sn, lvl, k), pa, pb, 0.24, "cornice", width=0.3, extend=0.06, u_dir=pb - pa)
                pa, pb = pa - v3(0, y1 - y0 - 0.25, 0), pb - v3(0, y1 - y0 - 0.25, 0)
                beam(detail, "castle_plinth_%s%d_%d" % (sn, lvl, k), pa, pb, 0.16, "trim_gold", width=0.16, extend=0.06, u_dir=pb - pa)
        # lit arched windows on storey 1
        for k, z in enumerate((-11.4, -12.2, -13.6, -14.4, -15.9, -16.7, -18.1, -18.9, -20.4, -21.2)):
            x = side * (cs.castle_x(z, 0) + 0.02)
            add_cube(lights, "glow_castle_window_%s%d" % (sn, k), v3(x, 1.45, z), EYE, (0.02, 1.2, 0.5),
                     {"all": None, "+1": "window_lit", "-1": "window_lit"}, stretch=True, u_dir=v3(0, 0, -side), v_dir=v3(0, -1, 0))
            box(detail, "castle_window_sill_%s%d" % (sn, k), (x + side * 0.05, 0.8, z), (0.12, 0.08, 0.62), "gold")
        for k, z in enumerate((-15.4, -22.3)):
            x = side * (cs.castle_x(z, 3.0) + 0.02)
            add_cube(lights, "glow_castle_window2_%s%d" % (sn, k), v3(x, 4.3, z), EYE, (0.02, 1.0, 0.45),
                     {"all": None, "+1": "window_lit", "-1": "window_lit"}, stretch=True, u_dir=v3(0, 0, -side), v_dir=v3(0, -1, 0))
        # gilded pilasters between the windows
        for k, z in enumerate((-10.5, -12.9, -15.1, -17.3, -19.5, -21.7, -22.85)):
            for lvl, (y0, y1) in enumerate(((0.05, cs.L1_TOP - 0.25), (cs.L2_Y + 0.05, cs.L2_TOP - 0.25))):
                if lvl == 1 and z > cs.L2_Z:
                    continue
                if lvl == 1 and any(a - 0.2 < z < b + 0.2 for a, b in ci.COCKPIT_WINDOWS):
                    continue
                x = side * (cs.castle_x(z, y0) + 0.05)
                box(detail, "castle_pilaster_%s%d_%d" % (sn, lvl, k), (x, (y0 + y1) / 2, z), (0.12, y1 - y0, 0.24), "gold")
    # fronts: storey 1 at CASTLE_Z (the door: see doors()), storey 2 at L2_Z (the great arch)
    for (z, y0, y1, hole, name) in ((cs.CASTLE_Z, cs.L1_Y, cs.L1_TOP, (-1.0, 1.0, cs.L1_Y, cs.L1_Y + 2.0), "front1"),
                                    (cs.L2_Z, cs.L2_Y, cs.L2_TOP, None, "front2")):
        w = cs.castle_x(z, y0)
        if hole:
            hx0, hx1, hy0, hy1 = hole
            parts = [(-w, hx0, y0, y1), (hx1, w, y0, y1), (hx0, hx1, hy1, y1)]
        else:
            parts = [(-w, w, y0, y1)]
        for k, (a, b, ya, yb) in enumerate(parts):
            if name == "front2":
                continue
            quad(bone, "castle_%s_%d" % (name, k), v3(a, ya, z), v3(b, ya, z), v3(a, yb, z), v3(b, yb, z), 0.14, "wall_wood", v3(0, 0, 1),
                 u_dir=v3(1, 0, 0), stretch=False, back="dark_wood")
        beam(bone, "castle_%s_cornice" % name, v3(-w - 0.1, y1 - 0.12, z + 0.08), v3(w + 0.1, y1 - 0.12, z + 0.08), 0.24, "cornice", width=0.3,
             u_dir=v3(1, 0, 0))
    # the cockpit's front with the great arch (the arch's glass is the grid's window cells)
    z = cs.L2_Z
    w = cs.castle_x(z, cs.L2_Y)
    ax, sill, spring, crown = cs.ARCH
    n = 12
    for k in range(n):
        x0, x1 = -w + 2 * w * k / n, -w + 2 * w * (k + 1) / n
        for j in range(8):
            y0 = cs.L2_Y + (cs.L2_TOP - cs.L2_Y) * j / 8
            y1 = cs.L2_Y + (cs.L2_TOP - cs.L2_Y) * (j + 1) / 8
            xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
            inside = abs(xm) < ax and sill < ym < crown and (ym < spring or (xm / ax) ** 2 + ((ym - spring) / (crown - spring)) ** 2 <= 1.0)
            if inside:
                continue
            quad(bone, "cockpit_front_%d_%d" % (k, j), v3(x0, y0, z), v3(x1, y0, z), v3(x0, y1, z), v3(x1, y1, z), 0.14, "wall_wood",
                 v3(0, 0, 1), u_dir=v3(1, 0, 0), stretch=False, back="dark_wood")
    add_cube(bone, "cockpit_arch_frame", v3(0, (sill + crown) / 2, z + 0.02), EYE, (2 * ax, crown - sill, 0.06),
             {"all": None, "+3": "window_arch", "-3": "window_arch"}, stretch=True, u_dir=v3(-1, 0, 0), v_dir=v3(0, -1, 0))
    pts = [v3(math.cos(a) * (ax + 0.12), spring + math.sin(a) * (crown - spring + 0.12), z + 0.1) for a in np.linspace(0, math.pi, 15)]
    polyline(detail, "cockpit_arch_moulding", pts, 0.2, "gold", sides=4)
    for sx in (-1, 1):
        beam(detail, "cockpit_arch_jamb_%d" % (sx > 0), v3(sx * (ax + 0.12), sill, z + 0.1), v3(sx * (ax + 0.12), spring, z + 0.1), 0.2, "gold")
    beam(detail, "cockpit_arch_sill", v3(-ax - 0.2, sill - 0.05, z + 0.12), v3(ax + 0.2, sill - 0.05, z + 0.12), 0.14, "gold", width=0.26)
    # the back of the castle: two rows of lit windows, pilasters
    z = cs.STERN_Z
    for lvl, (y0, y1, ny) in enumerate(((cs.L1_Y, cs.L1_TOP, 1.4), (cs.L2_Y, cs.L2_TOP, 4.6))):
        w = cs.castle_x(z, y0)
        quad(bone, "castle_back_%d" % lvl, v3(-w, y0, z), v3(w, y0, z), v3(-w, y1, z), v3(w, y1, z), 0.14, "wall_wood", v3(0, 0, -1),
             u_dir=v3(-1, 0, 0), stretch=False, back="dark_wood")
        for k, x in enumerate(np.linspace(-w + 1.1, w - 1.1, 5)):
            add_cube(lights, "glow_stern_window_%d_%d" % (lvl, k), v3(x, ny, z - 0.02), EYE, (0.62, 1.3, 0.02),
                     {"all": None, "+3": "window_lit", "-3": "window_lit"}, stretch=True)
        beam(bone, "castle_back_cornice_%d" % lvl, v3(-w - 0.1, y1 - 0.12, z - 0.08), v3(w + 0.1, y1 - 0.12, z - 0.08), 0.24, "cornice", width=0.3,
             u_dir=v3(1, 0, 0))
    # the green roof: overhanging slopes from the eaves up to a flat ridge, gilded eaves, a brass scroll, pennant poles
    rz0, rz1 = cs.ROOF_Z
    ry0, ry1 = cs.ROOF_Y
    hw0 = cs.castle_x(-19.0, 3.0) + 0.55
    hw1 = hw0 - 2.4
    inset_z = 1.6
    corners_lo = [v3(hw0, ry0, rz1), v3(hw0, ry0, rz0), v3(-hw0, ry0, rz0), v3(-hw0, ry0, rz1)]
    corners_hi = [v3(hw1, ry1, rz1 - inset_z), v3(hw1, ry1, rz0 + inset_z), v3(-hw1, ry1, rz0 + inset_z), v3(-hw1, ry1, rz1 - inset_z)]
    for k in range(4):
        a, b = corners_lo[k], corners_lo[(k + 1) % 4]
        c, d = corners_hi[k], corners_hi[(k + 1) % 4]
        out = norm(np.cross(b - a, c - a))
        if out[1] < 0:
            out = -out
        for s in range(4):
            t0, t1 = s / 4, (s + 1) / 4
            p00, p10 = a + (b - a) * t0, a + (b - a) * t1
            p01, p11 = c + (d - c) * t0, c + (d - c) * t1
            quad(roof_bone, "roof_%d_%d" % (k, s), p00, p10, p01, p11, 0.16, "roof_green", out, u_dir=b - a, stretch=True, back="dark_wood")
        beam(roof_bone, "roof_eave_%d" % k, a + v3(0, -0.05, 0), b + v3(0, -0.05, 0), 0.22, "trim_gold", width=0.3, extend=0.1, u_dir=b - a)
        beam(detail, "roof_hip_%d" % k, a, c, 0.16, "gold", extend=0.05)
    quad(roof_bone, "roof_top", corners_hi[3], corners_hi[0], corners_hi[2], corners_hi[1], 0.16, "roof_green", v3(0, 1, 0),
         u_dir=v3(1, 0, 0), stretch=True)
    # the scroll on the roof's front: a brass spiral on a stem
    base = v3(0, ry1, rz1 - inset_z - 0.2)
    pts = [base + v3(0, 0.0, 0)] + [base + v3(0, 0.9 + 0.55 * math.sin(a) * (1 - a / 9), 0.8 + 0.55 * math.cos(a) * (1 - a / 9)) for a in np.linspace(0, 8.5, 18)]
    polyline(detail, "roof_scroll", pts, 0.16, "brass", sides=6)
    disc(lights, "glow_roof_gem", base + v3(0, 0.9, 0.8), (0, 0, 1), 0.2, 0.1, "gem", sides=8)
    return hw0


# ================================================================ engines
NACELLE_ST = [cs.NACELLE[2], cs.NACELLE[2] + 1.55, cs.NACELLE[2] + 1.65, -21.6, -21.3, -21.0, -20.0, -18.0, -16.6, -16.0, -15.6, -15.2, -14.8,
              -14.6, -13.0, -11.7, -11.2, -10.6, -10.1, -9.7, -9.4, cs.NACELLE[3] - 0.02]


def body_of_revolution(bone, name, axis_pt, rfn, z0, z1, n_st, naz, region_fn, phase=0.0):
    """Panels of a body of revolution about a line parallel to z through axis_pt (x, y), radius rfn(z); n_st: a count of
    even stations or the list of their z."""
    zs = list(np.linspace(z0, z1, n_st + 1)) if isinstance(n_st, int) else sorted(n_st)
    ax, ay = axis_pt
    for i in range(len(zs) - 1):
        za, zb = zs[i], zs[i + 1]
        ra, rb = rfn(za), rfn(zb)
        for j in range(naz):
            a0, a1 = phase + 2 * math.pi * j / naz, phase + 2 * math.pi * (j + 1) / naz
            pa0 = v3(ax + math.sin(a0) * ra, ay + math.cos(a0) * ra, za)
            pb0 = v3(ax + math.sin(a0) * rb, ay + math.cos(a0) * rb, zb)
            pa1 = v3(ax + math.sin(a1) * ra, ay + math.cos(a1) * ra, za)
            pb1 = v3(ax + math.sin(a1) * rb, ay + math.cos(a1) * rb, zb)
            am = (a0 + a1) / 2
            out = v3(math.sin(am), math.cos(am), (ra - rb) / max(1e-3, zb - za) * 0.5)
            quad(bone, "%s_%d_%d" % (name, i, j), pa0, pb0, pa1, pb1, 0.14, region_fn((za + zb) / 2, am), norm(out), u_dir=v3(0, 0, 1),
                 stretch=False, overlap=(1.03, 1.05))


def nacelles(bone, detail, lights, root):
    x, y, z0, z1, r = cs.NACELLE
    for side, sn in SIDES:
        cx = side * x

        def reg(z, a):
            if z > cs.NACELLE_NOSE[1]:
                return "bronze"
            if z < z0 + 1.6:
                return "engine_dark"
            return "engine_plate"
        body_of_revolution(bone, "nacelle_%s" % sn, (cx, y), cs.nacelle_r, z0, z1, NACELLE_ST, 22, reg)
        # gilded bands, the dome's spike, the mount to the hull
        for k, z in enumerate((z1 - cs.NACELLE_NOSE[0], -12.6, cs.NACELLE_NOSE[1] - 0.1, -16.4, -21.1, z0 + 1.6)):
            rr = cs.nacelle_r(z) + 0.08
            ring(detail, "nacelle_band_%s%d" % (sn, k), v3(cx, y, z), (0, 0, 1), rr, 0.22, "gold", n=20)
        tube(bone, "nacelle_spike_%s" % sn, v3(cx, y, z1 - 0.05), v3(cx, y, z1 + 1.0), 0.32, "brass", sides=6)
        for k in range(6):
            a = 2 * math.pi * k / 6
            d = v3(math.cos(a), math.sin(a), 0)
            p0 = v3(cx, y, z1 - cs.NACELLE_NOSE[0]) + d * cs.NACELLE_NOSE[0] * 0.98
            tube(detail, "nacelle_dome_rib_%s%d" % (sn, k), p0, v3(cx, y, z1 - 0.1) + d * 0.5, 0.16, "gold", sides=4)
        tube(bone, "nacelle_spike_tip_%s" % sn, v3(cx, y, z1 + 1.0), v3(cx, y, z1 + 1.4), 0.14, "gold", sides=6)
        # the crystal eye on the outer face: a glowing core in a riveted brass bezel with spokes
        ze, re = cs.NACELLE_EYE
        n = v3(side, 0, 0)
        c = v3(cx + side * (r + 0.05), y, ze)
        disc(bone, "nacelle_eye_bezel_%s" % sn, c, n, re + 0.55, 0.3, "brass", sides=16)
        ring(detail, "nacelle_eye_ring_%s" % sn, c + n * 0.18, n, re + 0.35, 0.2, "gold", n=16)
        add_cube(lights, "glow_nacelle_eye_%s" % sn, c + n * 0.2, ga.face_frame(n), (2 * re, 2 * re, 0.02),
                 {"all": None, "+3": "crystal_core", "-3": "crystal_core"}, stretch=True)
        for k in range(8):
            a = 2 * math.pi * k / 8
            d = v3(0, math.cos(a), math.sin(a))
            beam(detail, "nacelle_eye_spoke_%s%d" % (sn, k), c + n * 0.22 + d * (re * 0.95), c + n * 0.22 + d * (re + 0.45), 0.08, "brass",
                 width=0.12, up=n)
        # brass feathers sweeping back over the eye (the "wings")
        for k in range(5):
            root_pt = v3(cx + side * (r * 0.62), y + r * 0.72, -14.6 - 0.45 * k)
            tip = root_pt + v3(side * (0.9 + 0.1 * k), 0.7 + 0.3 * k, -3.8 - 0.3 * k)
            R = gg.frame_from(tip - root_pt, v3(side, 1, 0))
            add_cube(bone, "nacelle_feather_%s%d" % (sn, k), (root_pt + tip) / 2, R, (np.linalg.norm(tip - root_pt), 0.08, 1.1 - 0.12 * k),
                     "feather", u_dir=tip - root_pt)
        # copper tanks under the drum, a gear train on its fore face
        for k, dz in enumerate((-16.2, -19.6)):
            p = v3(cx + side * 1.4, y - r + 0.2, dz)
            tube(bone, "nacelle_tank_%s%d" % (sn, k), p + v3(0, 0, 1.2), p - v3(0, 0, 1.2), 1.1, "copper", sides=8)
            for e in (-1, 1):
                tube(detail, "nacelle_tank_band_%s%d_%d" % (sn, k, e > 0), p + v3(0, 0, e * 0.8 - 0.06), p + v3(0, 0, e * 0.8 + 0.06), 1.2, "brass", sides=8)
        gl.gear(detail, "nacelle_gear_%s" % sn, v3(cx + side * (cs.NACELLE_NOSE[0] + 0.35), y - 0.6, -14.0), (side, 0, 0), 0.9, 0.18, teeth=12,
                region="brass", spokes=4, rim="bronze")
        # the elevator flap behind the feathers (bone flap_*: tilts with the climb)
        fp = v3(cx + side * (r + 0.2), y + 0.4, -21.0)
        fb = Bone("flap_" + sn, origin=tuple(fp), parent=root)
        add_cube(fb, "nacelle_flap_%s" % sn, fp + v3(side * 0.9, 0, -0.5), EYE, (1.8, 0.1, 1.4), {"all": "brass", "+2": "feather", "-2": "feather"},
                 u_dir=v3(0, 0, -1))
        # copper pipes along the belly, into the hull
        for k, (dx, dy) in enumerate(((0.5, -0.9), (-0.4, -1.0))):
            pts = [v3(cx + side * dx * r, y + dy * r, z) for z in (-11.0, -16.0, -21.5)]
            pts = [v3(side * 5.0, y + dy * r + 0.4, -10.2)] + pts
            polyline(detail, "nacelle_pipe_%s%d" % (sn, k), pts, 0.26, "copper", sides=6)
            for j, q in enumerate(pts[1:-1]):
                tube(detail, "nacelle_pipe_fl_%s%d_%d" % (sn, k, j), q - v3(0, 0, 0.05), q + v3(0, 0, 0.05), 0.38, "brass", sides=6)
        # struts to the hull
        for k, z in enumerate((-11.0, -20.0)):
            for dy in (0.9, -0.9):
                p0 = v3(cx - side * (r - 0.2), y + dy, z)
                p1 = v3(side * (cs.hull_x(z, y + dy) - 0.1), y + dy, z)
                beam(bone, "nacelle_strut_%s%d_%d" % (sn, k, dy > 0), p0, p1, 0.3, "bronze", width=0.4)
        # the rotor at the tail (bone rotor_*: the propeller animation)
        rc = v3(cx, y, z0 - 0.15)
        rb = Bone("rotor_" + sn, origin=tuple(rc), parent=root)
        ring(detail, "rotor_shroud_%s" % sn, rc + v3(0, 0, -0.2), (0, 0, 1), r * 0.82, 0.28, "iron", n=16)
        disc(rb, "rotor_hub_%s" % sn, rc + v3(0, 0, -0.25), (0, 0, 1), 0.38, 0.4, "brass", sides=8)
        for k in range(4):
            a = 2 * math.pi * k / 4 + 0.3
            d = v3(math.cos(a), math.sin(a), 0)
            t = np.cross(v3(0, 0, 1), d)
            R = np.column_stack([d, norm(t * math.cos(0.5) + v3(0, 0, 1) * math.sin(0.5)), norm(np.cross(d, t * math.cos(0.5) + v3(0, 0, 1) * math.sin(0.5)))])
            add_cube(rb, "rotor_blade_%s%d" % (sn, k), rc + v3(0, 0, -0.25) + d * (r * 0.42), R, (r * 0.7, 0.42, 0.06), "brass")


def rear_engine(bone, detail, lights, root):
    ry, zf, zr, rr = cs.REAR_ENGINE
    c0 = v3(0, ry, zf)

    def reg(z, a):
        return "engine_plate" if z > zr + 0.5 else "bronze"
    body_of_revolution(bone, "rear_engine", (0.0, ry), lambda z: rr if z < zf - 0.6 else rr - 0.4, zr + 0.3, zf, 4, 28, reg)
    # the rim: a heavy gilded ring, the shroud's inside, spokes to the hub, the crystal core
    c = v3(0, ry, zr + 0.3)
    ring(bone, "rear_rim", c, (0, 0, 1), rr - 0.15, 0.4, "gold", n=28)
    ring(detail, "rear_rim_in", c + v3(0, 0, -0.05), (0, 0, 1), rr - 0.75, 0.25, "brass", n=24)
    disc(bone, "rear_engine_back", c + v3(0, 0, 0.9), (0, 0, 1), rr - 0.3, 0.1, "engine_dark", sides=24)
    pb = Bone("rear_prop", origin=tuple(c + v3(0, 0, 0.3)), parent=root)
    disc(pb, "rear_prop_hub", c + v3(0, 0, 0.3), (0, 0, 1), 0.7, 0.5, "brass", sides=12)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        d = v3(math.cos(a), math.sin(a), 0)
        t = np.cross(v3(0, 0, 1), d)
        u2 = norm(t * math.cos(0.55) + v3(0, 0, 1) * math.sin(0.55))
        R = np.column_stack([d, u2, np.cross(d, u2)])
        add_cube(pb, "rear_prop_blade_%d" % k, c + v3(0, 0, 0.4) + d * (rr * 0.48), R, (rr * 0.78, 0.8, 0.07), {"all": "brass", "+3": "blade", "-3": "blade"},
                 stretch=True, u_dir=d)
    add_cube(lights, "glow_rear_core", c + v3(0, 0, 0.05), EYE, (1.3, 1.3, 0.02), {"all": None, "+3": "crystal_core", "-3": "crystal_core"},
             stretch=True)
    # a brass bar down the middle of the stern (the back view), a gilded medallion
    beam(detail, "stern_bar", v3(0, cs.SHEER_WAIST - 0.1, cs.STERN_Z - 0.1), v3(0, ry + rr + 0.1, cs.STERN_Z - 0.1), 0.3, "brass", width=0.3)


def prop_pods(bone, detail, lights, root):
    for side, sn in SIDES:
        rp, hub, ax = cs.pod_frame(side)
        rp, hub, ax = v3(*rp), v3(*hub), v3(*ax)
        tube(bone, "pod_body_%s" % sn, rp, hub - ax * 0.4, 1.8, "bronze", sides=10)
        tube(bone, "pod_cap_%s" % sn, rp - ax * 0.3, rp + ax * 0.3, 2.0, "brass", sides=10)
        tube(bone, "pod_nose_%s" % sn, hub - ax * 0.45, hub - ax * 0.05, 1.4, "gold", sides=10)
        for k, t in enumerate((0.35, 0.6, 0.82)):
            p = rp + (hub - rp) * t
            tube(lights, "glow_pod_crystal_band_%s%d" % (sn, k), p - ax * 0.17, p + ax * 0.17, 1.92, "crystal", sides=10)
            tube(detail, "pod_band_%s%d" % (sn, k), p - ax * 0.28, p - ax * 0.18, 2.0, "gold", sides=10)
        # the hanger to the hull
        top = v3(side * (cs.hull_x(-5.5, -6.0) - 0.3), -6.0, -5.5)
        beam(bone, "pod_hanger_%s" % sn, top, rp + v3(0, 0.6, 0), 0.4, "bronze", width=0.5)
        # the propeller: five long golden leaf blades fanning round the axis (bone pod_prop_*, about the pod's axis)
        R = gg.frame_from(ax, v3(1, 0, 0))            # local x along the axis
        Rz = np.column_stack([R[:, 1], R[:, 2], R[:, 0]])   # local z along the axis
        pod = Bone("pod_" + sn, origin=tuple(hub), rot=Rz, parent=root)
        pb = Bone("pod_prop_" + sn, origin=tuple(hub), parent=pod)
        disc(pb, "pod_prop_hub_%s" % sn, hub, ax, 0.45, 0.6, "brass", sides=8)
        tube(pb, "pod_prop_cone_%s" % sn, hub + ax * 0.3, hub + ax * 0.75, 0.3, "gold", sides=6)
        e1 = norm(np.cross(ax, v3(1, 0, 0)))
        e2 = np.cross(ax, e1)
        for k in range(5):
            a = 2 * math.pi * k / 5
            d = e1 * math.cos(a) + e2 * math.sin(a)
            dd = norm(d + ax * 0.55)            # swept back along the axis, like a flower
            L = cs.PROP_BLADE
            cc = hub + dd * (L / 2 + 0.3)
            t = norm(np.cross(ax, d))
            tw = t * math.cos(0.45) + ax * math.sin(0.45)
            tw = norm(tw - np.dot(tw, dd) * dd)
            Rb = np.column_stack([dd, tw, np.cross(dd, tw)])
            add_cube(pb, "pod_blade_%s%d" % (sn, k), cc, Rb, (L, 1.05, 0.05), {"all": "gold", "+3": "blade", "-3": "blade"}, stretch=True,
                     u_dir=-dd)


# ================================================================ crystals
def crystal(bone, name, base, d, length, r, sides=6):
    """A glowing crystal: a prism along d from base, ending in a point."""
    base, d = v3(*base), norm(v3(*d))
    tube(bone, "glow_" + name, base, base + d * length * 0.68, 2 * r, "crystal", sides=sides)
    for k in range(3):
        t0, t1 = 0.66 + 0.11 * k, 0.66 + 0.11 * (k + 1)
        tube(bone, "glow_%s_tip%d" % (name, k), base + d * length * t0, base + d * length * t1, 2 * r * (1 - (k + 0.5) / 3.2), "crystal", sides=sides)


def crystals(bone, lights, detail, root, lantern_bone):
    # the platform under the keel: a gilded round deck, crystals rising from it, the big crystal hanging under it
    z, py, pr, tip = cs.BOTTOM_CRYSTAL
    c = v3(0, py, z)
    disc(bone, "crystal_platform", c, (0, 1, 0), pr, 0.3, "bronze", sides=16)
    ring(bone, "crystal_platform_rim", c + v3(0, 0.05, 0), (0, 1, 0), pr + 0.05, 0.22, "gold", n=16)
    disc(detail, "crystal_platform_under", c - v3(0, 0.25, 0), (0, 1, 0), pr * 0.6, 0.25, "brass", sides=12)
    for k in range(8):
        a = 2 * math.pi * k / 8
        p = c + v3(math.cos(a) * (pr - 0.2), 0.15, math.sin(a) * (pr - 0.2))
        tube(detail, "crystal_platform_post_%d" % k, p, p + v3(0, 0.6, 0), 0.1, "brass", sides=4)
    crystal(lights, "bottom_big", c - v3(0, 0.2, 0), (0, -1, 0), py - tip - 0.2, 0.75, sides=6)
    for k, (dx, dz, h, r, tilt) in enumerate(((0, 0, 1.6, 0.5, 0), (0.7, 0.4, 1.1, 0.32, 0.3), (-0.6, 0.5, 1.2, 0.34, 0.3), (0.3, -0.7, 1.0, 0.3, 0.35),
                                              (-0.5, -0.5, 0.9, 0.28, 0.3))):
        d = norm(v3(dx * tilt, 1, dz * tilt)) if tilt else v3(0, 1, 0)
        crystal(lights, "bottom_up_%d" % k, c + v3(dx, 0.1, dz), d, h, r)
    keel = cs.keel_y(z)
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        p = c + v3(math.cos(a) * (pr - 0.1), 0.1, math.sin(a) * (pr - 0.1))
        q = v3(math.cos(a) * 2.0, cs.keel_y(z + math.sin(a) * 2.0) + 0.2, z + math.sin(a) * 2.6)
        chain(detail, "crystal_chain_%d" % k, p, q, link=0.3, th=0.06, region="chain")
    # crystal lanterns hanging under the bow
    for k, (x, y, zz) in enumerate(cs.HANGING_CRYSTALS):
        top = v3(x, cs.keel_y(zz) + 0.3 if x == 0 else cs.keel_y(zz) + 1.2, zz)
        lb = Bone("lantern_crystal_%d" % k, origin=tuple(top), parent=lantern_bone)
        cc = v3(x, y, zz)
        chain(lb, "hang_crystal_chain_%d" % k, top, cc + v3(0, 0.7, 0), link=0.25, th=0.05)
        disc(lb, "hang_crystal_cap_%d" % k, cc + v3(0, 0.7, 0), (0, 1, 0), 0.62, 0.18, "brass", sides=8)
        disc(lb, "hang_crystal_base_%d" % k, cc - v3(0, 0.6, 0), (0, 1, 0), 0.56, 0.16, "brass", sides=8)
        for j in range(4):
            a = math.pi / 2 * j + math.pi / 4
            p = cc + v3(math.cos(a) * 0.5, 0, math.sin(a) * 0.5)
            tube(lb, "hang_crystal_post_%d_%d" % (k, j), p - v3(0, 0.6, 0), p + v3(0, 0.7, 0), 0.08, "gold", sides=4)
        crystal(lb, "hang_crystal_%d" % k, cc - v3(0, 0.55, 0), (0, 1, 0), 1.2, 0.36)
        crystal(lb, "hang_crystal_drop_%d" % k, cc - v3(0, 0.65, 0), (0, -1, 0), 0.8, 0.24)
    # crystal lamps on the rail at the castle's front corners
    for k, (x, y, zz) in enumerate(cs.CASTLE_CRYSTALS):
        tube(bone, "castle_lamp_post_%d" % k, v3(x, 0.0, zz), v3(x, y - 0.3, zz), 0.2, "brass", sides=6)
        disc(bone, "castle_lamp_cup_%d" % k, v3(x, y - 0.25, zz), (0, 1, 0), 0.3, 0.15, "gold", sides=8)
        crystal(lights, "castle_lamp_%d" % k, v3(x, y - 0.2, zz), (0, 1, 0), 1.0, 0.26)
        for j in range(3):
            a = 2 * math.pi * j / 3
            tube(detail, "castle_lamp_claw_%d_%d" % (k, j), v3(x, y - 0.2, zz), v3(x + math.cos(a) * 0.3, y + 0.3, zz + math.sin(a) * 0.3), 0.05, "gold",
                 sides=4)
    # the floating crystal pods (bones pod_front / pod_rear, their rings pod_*_ring)
    for name, p, big in (("front", cs.FRONT_POD, False), ("rear", cs.REAR_POD, True)):
        p = v3(*p)
        pb = Bone("pod_" + name, origin=tuple(p), parent=root)
        rb = Bone("pod_%s_ring" % name, origin=tuple(p), parent=pb)
        R = cs.POD_R * (1.25 if big else 1.0)
        gl.gear(rb, "pod_%s_gear" % name, p, (0, 0, 1), R, 0.5, teeth=16, region="copper" if big else "bronze", spokes=6, rim="copper" if big else "brass")
        ring(rb, "pod_%s_ring_in" % name, p, (0, 0, 1), R * 0.62, 0.22, "gold", n=12)
        disc(rb, "pod_%s_disc" % name, p, (0, 0, 1), R * 0.55, 0.3, "engine_plate", sides=12)
        crystal(pb, "pod_%s_core" % name, p - v3(0, 0.55 * R, 0), (0, 1, 0), 1.1 * R, 0.3 * R)
        for s in (1, -1):
            crystal(pb, "pod_%s_side_%d" % (name, s > 0), p + v3(0, 0, s * 0.3), (0, 0, s), 0.9 * R, 0.36)
            tube(pb, "pod_%s_axle_%d" % (name, s > 0), p, p + v3(0, 0, s * 0.45), 0.6, "brass", sides=8)
    # ropes holding the pods
    fp, rpod = v3(*cs.FRONT_POD), v3(*cs.REAR_POD)
    fl, rl = cs.lobe("f"), cs.lobe("r")
    rope(detail, "pod_front_rope_up", fp + v3(0, cs.POD_R, 0), LP("f", fl[3] + fl[6] * 0.75, 180, 0.0), d=0.06, region="rope_dark")
    rope(detail, "pod_front_rope_bow", fp - v3(0, cs.POD_R, 0), v3(0, cs.BEAK[1][1] + 0.1, cs.BEAK[1][0] - 0.2), d=0.06, region="rope_dark", sag=0.3)
    tail = v3(0, rl[2], rl[3] - rl[6])
    beam(bone, "rear_spar", tail + v3(0, 0, 0.6), tail + v3(0, 0, -2.8), 0.22, "dark_wood")
    disc(bone, "rear_spar_cap", tail + v3(0, 0, 0.2), (0, 0, 1), 0.7, 0.3, "gold", sides=10)
    rope(detail, "pod_rear_rope_up", rpod + v3(0, 1.25 * cs.POD_R, 0), tail + v3(0, 0, -2.0), d=0.06, region="rope_dark")
    rope(detail, "pod_rear_rope_down", rpod - v3(0, 1.25 * cs.POD_R, 0), v3(0, cs.ROOF_Y[1], cs.ROOF_Z[0] + 1.0), d=0.06, region="rope_dark", sag=0.4)
    return tail


# ================================================================ rigging, pennants, lanterns
def rigging(bone, girdle):
    """Ropes from the girdle's jewels and the side lobes' undersides down to the rails."""
    count = 0
    for side, sn in SIDES:
        line = girdle[side]
        for j, (z, p, h) in enumerate(line):
            if h or j % 3:
                continue
            zt = max(cs.CASTLE_Z + 0.5, min(cs.FORECASTLE_Z + 8.0, z * 1.05))
            if cs.CASTLE_Z - 0.2 > zt or zt > 24.5:
                continue
            ytop = cs.sheer_y(zt) + 0.75
            q = v3(side * (cs.hull_x(zt, cs.SHEER_WAIST) - 0.15), ytop, zt)
            rope(bone, "shroud_%s%d" % (sn, j), p, q, d=0.07, region="rope_dark")
            count += 1
        for name in ("fp", "rp") if side > 0 else ("fs", "rs"):
            lb = cs.lobe(name)
            for t in (-0.4, 0.1, 0.5):
                z = lb[3] + lb[6] * t
                p = LP(name, z, side * 150, 0.05)
                zt = max(cs.CASTLE_Z - 2.0, min(22.0, z))
                if zt < cs.CASTLE_Z:
                    q = v3(side * (cs.castle_x(zt, 3.0) + 0.1), cs.castle_top(zt) + 0.05, zt)
                else:
                    q = v3(side * (cs.hull_x(zt, cs.SHEER_WAIST) - 0.1), cs.sheer_y(zt) + 0.7, zt)
                rope(bone, "lobe_rope_%s%d" % (name, int(t * 10)), p, q, d=0.07, region="rope_dark")
                count += 1
    # ropes from the ring's top to the girdle (the reference's web round the ring)
    c = v3(0, cs.RING_Y + cs.RING_R, cs.RING_Z)
    for side, sn in SIDES:
        for k, z in enumerate((-4.0, 3.5)):
            rope(bone, "ring_rope_%s%d" % (sn, k), c, LP("c", z, side * 150, 0.05), d=0.06, region="rope_dark")
    return count


def pennants(root, tail):
    pb = Bone("pennants", parent=root)
    rz0, rz1 = cs.ROOF_Z
    for side, sn in SIDES:
        x = side * 2.6
        z = rz1 - 2.2
        base = v3(x, cs.ROOF_Y[1] - 0.3, z)
        top = base + v3(0, 3.2, 0)
        tube(pb, "pennant_pole_%s" % sn, base, top, 0.14, "dark_wood", sides=6)
        disc(pb, "pennant_pole_ball_%s" % sn, top + v3(0, 0.08, 0), (0, 1, 0), 0.12, 0.16, "gold", sides=6)
        flag(pb, "pennant_" + sn, top - v3(0, 0.12, 0), 2.6, 0.55)
    flag(pb, "pennant_tail", tail + v3(0, 0.1, -2.7), 2.4, 0.6)
    x, y, z = ci.POSTS[4]
    flag(pb, "pennant_bow", v3(x, 4.2, z), 1.6, 0.4)
    tube(pb, "pennant_bow_pole", v3(x, y, z), v3(x, 4.35, z), 0.12, "dark_wood", sides=6)
    return pb


def lanterns(lanterns_bone, detail):
    """Lanterns on posts on the forecastle and at the castle's door; hanging under the terrace."""
    for k, (x, y, z) in enumerate(ci.POSTS[:4]):
        top = v3(x, y + 1.9, z)
        tube(detail, "lamp_post_%d" % k, v3(x, y, z), top, 0.12, "dark_wood", sides=6)
        beam(detail, "lamp_arm_%d" % k, top, top + v3(0, 0, 0.4 if z > 0 else 0.4), 0.06, "iron")
        gl.hanging_lantern(lanterns_bone, "post_%d" % k, top + v3(0, 0, 0.4), drop=0.1, w=0.3, h=0.42)
    for k, x in enumerate((-2.0, 2.0)):
        gl.hanging_lantern(lanterns_bone, "terrace_%d" % k, v3(x, cs.L1_TOP - 0.05, cs.CASTLE_Z + 0.35), drop=0.2, w=0.3, h=0.42)


# ================================================================ rooms (grid surfaces), ladders, doors
OPEN_KINDS = (ci.DRY, ci.LADDER)
ROOM_MATERIALS = {
    "mess": ("in_wall_lounge", "in_floor_lounge", "in_ceil_lounge"),
    "cockpit": ("in_stone", "in_floor_capt", "in_ceil"),
    "lounge": ("in_wall_lounge", "in_floor_lounge", "in_ceil_lounge"),
    "storeroom": ("in_wall_store", "in_floor_hold", "in_ceil_store"),
    "engine_room": ("in_wall_works", "in_floor_grate", "in_ceil_soot"),
    "hold": ("in_wall_store", "in_floor_hold", "in_ceil_store"),
}
SHAFT_MAT = ("in_wall", "in_floor", "in_ceil")


def room_at(x, y, z):
    for name, (x0, x1, y0, y1, z0, z1) in ci.ROOMS.items():
        if x0 - 0.01 <= x <= x1 + 0.01 and y0 - 0.01 <= y <= y1 + 0.01 and z0 - 0.01 <= z <= z1 + 0.01:
            return name
    return None


def surfaces(rooms_bone, g):
    """Walls, floors and ceilings of the rooms on the cell boundaries (solid next to a room cell); as in the Sky Leviathan."""
    k = g.k
    solid = k == ci.SOLID
    roomish = np.isin(k, OPEN_KINDS) | (k >= ci.DOOR)
    near = roomish.copy()
    for a in range(3):
        for s in (1, -1):
            near |= np.roll(roomish, s, axis=a)
    opened = roomish | ((k == ci.FURNITURE) & near)
    C = ci.CELL
    origin = (ci.X0, ci.Y0, ci.Z0)
    mats = [SHAFT_MAT] + [m for m in dict.fromkeys(ROOM_MATERIALS.values()) if m != SHAFT_MAT]
    mat_index = np.zeros(k.shape, dtype=np.int16)
    for name, box_ in ci.ROOMS.items():
        mat_index[g.sel(*[b + d for b, d in zip(box_, (-0.01, 0.01, -0.01, 0.01, -0.01, 0.01))])] = mats.index(ROOM_MATERIALS[name])
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
            nb_open[tuple(dst)] = opened[tuple(src)]
            nb_mat = np.zeros_like(mat_index)
            nb_mat[tuple(dst)] = mat_index[tuple(src)]
            inner = solid & nb_open
            slot = 1 if (a == 1 and s > 0) else 2 if a == 1 else 0
            others = [b for b in range(3) if b != a]
            for idx in range(inner.shape[a]):
                sl = [slice(None)] * 3
                sl[a] = idx
                m2 = inner[tuple(sl)]
                if not m2.any():
                    continue
                plane = origin[a] + (idx + (1 if s > 0 else 0)) * C
                al_i = a == 1 or a == 2
                al_j = a == 1 or a == 0
                for (i0, j0, i1, j1, kk) in gl.greedy(m2, nb_mat[tuple(sl)], al_i, al_j):
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
                    region = mats[kk][slot]
                    cube = add_cube(rooms_bone, "lit_%s_%d" % (region, count), center, EYE, size, {face: region}, u_dir=udir, v_dir=vdir)
                    if a == 1:
                        sub = ((i0 % MAX_TILE) / MAX_TILE, (j0 % MAX_TILE) / MAX_TILE, (i1 % MAX_TILE + 1) / MAX_TILE, (j1 % MAX_TILE + 1) / MAX_TILE)
                    else:
                        hz0, hz1 = (j0, j1) if a == 0 else (i0, i1)
                        room = room_at(center[0] + s * 0.3 if a == 0 else center[0], center[1], center[2] + s * 0.3 if a == 2 else center[2])
                        ry0, ry1 = (ci.ROOMS[room][2], ci.ROOMS[room][3]) if room else (lo[1], hi[1])
                        hgt = max(0.5, ry1 - ry0)
                        v0 = min(1.0, max(0.0, (ry1 - hi[1]) / hgt))
                        v1 = min(1.0, max(v0 + 0.01, (ry1 - lo[1]) / hgt))
                        sub = ((hz0 % MAX_TILE) / MAX_TILE, v0, (hz1 % MAX_TILE + 1) / MAX_TILE, v1)
                    set_sub(cube, sub)
                    count += 1
    return count


def ladders(bone):
    for name, (x0, x1, y0, y1, z0, z1) in ci.LADDERS.items():
        wall = z0
        pa = lambda y: v3(x0 + 0.15, y, wall + 0.08)  # noqa: E731
        pb = lambda y: v3(x1 - 0.15, y, wall + 0.08)  # noqa: E731
        beam(bone, "lit_ladder_%s_rail_a" % name, pa(y0), pa(y1), 0.08, "in_beam")
        beam(bone, "lit_ladder_%s_rail_b" % name, pb(y0), pb(y1), 0.08, "in_beam")
        y, i = y0 + 0.25, 0
        while y < y1 - 0.1:
            beam(bone, "lit_ladder_%s_rung_%d" % (name, i), pa(y), pb(y), 0.07, "in_beam")
            y += 0.5
            i += 1


def doors(root):
    anims = []
    for d, (name, box_) in ci.DOORS.items():
        x0, x1, y0, y1, z0, z1 = box_
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        flat = sy <= min(sx, sz) + 1e-6
        pre = "lit_"
        if flat:
            hinge = v3((x0 + x1) / 2, y1, z0)
            bone = Bone("door_%d" % d, origin=tuple(hinge), parent=root)
            add_cube(bone, "%sdoor_%d" % (pre, d), v3((x0 + x1) / 2, y1 - 0.08, (z0 + z1) / 2), EYE, (sx - 0.04, 0.14, sz - 0.04),
                     {"all": "dark_wood", "+2": "hatch", "-2": "hatch"}, stretch=True, u_dir=v3(1, 0, 0), v_dir=v3(0, 0, 1))
            anims.append(gg.animation("door_%d" % d, 1.0, "hold", [(bone, [gg.rot_kf(0.0, (0, 0, 0)), gg.rot_kf(1.0, (-110, 0, 0))])]))
            continue
        along_z = sx < sz
        depth = (sx if along_z else sz) + 0.12
        w = 0.16
        p0, p1 = (z0, z1) if along_z else (x0, x1)
        for k, at in enumerate((p0 - w / 2, p1 + w / 2)):
            c = v3((x0 + x1) / 2, (y0 + y1 + w) / 2, at) if along_z else v3(at, (y0 + y1 + w) / 2, (z0 + z1) / 2)
            size = (depth, sy + w, w) if along_z else (w, sy + w, depth)
            add_cube(root, "%sdoor_%d_jamb_%d" % (pre, d, k), c, EYE, size, "in_wood_carved")
        c = v3((x0 + x1) / 2, y1 + w / 2, (z0 + z1) / 2)
        size = (depth, w, sz + 2 * w) if along_z else (sx + 2 * w, w, depth)
        add_cube(root, "%sdoor_%d_lintel" % (pre, d), c, EYE, size, "in_wood_carved")
        tracks = []
        thin = 0.12
        for leaf, sgn in (("a", 1), ("b", -1)):
            if along_z:
                zh = z1 if sgn > 0 else z0
                hinge = v3((x0 + x1) / 2, y0, zh)
                cc = v3((x0 + x1) / 2, (y0 + y1) / 2, zh - sgn * sz / 4)
                size = (thin, sy, sz / 2 - 0.02)
            else:
                xh = x1 if sgn > 0 else x0
                hinge = v3(xh, y0, (z0 + z1) / 2)
                cc = v3(xh - sgn * sx / 4, (y0 + y1) / 2, (z0 + z1) / 2)
                size = (sx / 2 - 0.02, sy, thin)
            bone = Bone("door_%d_%s" % (d, leaf), origin=tuple(hinge), parent=root)
            big = ("+1", "-1") if along_z else ("+3", "-3")
            add_cube(bone, "%sdoor_%d_%s" % (pre, d, leaf), cc, EYE, size, {"all": "dark_wood", big[0]: "door_leaf", big[1]: "door_leaf"},
                     stretch=True, u_dir=v3(0, 0, 1) if along_z else v3(1, 0, 0), v_dir=v3(0, -1, 0))
            tracks.append((bone, [gg.rot_kf(0.0, (0, 0, 0)), gg.rot_kf(1.0, (0, sgn * 100, 0))]))
        anims.append(gg.animation("door_%d" % d, 1.0, "hold", tracks))
    return anims


def helm(root, bone):
    """The cockpit's helm: a big ship's wheel on a turned brass pedestal (bone helm_wheel), facing the arched window."""
    z = cs.HELM_Z
    y = ci.L2
    tube(bone, "lit_helm_pedestal", (0, y, z - 0.05), (0, y + 1.0, z - 0.05), 0.4, "in_wood_carved", sides=8)
    for k, yy in enumerate((y + 0.08, y + 0.5, y + 0.95)):
        tube(bone, "lit_helm_pedestal_ring_%d" % k, (0, yy - 0.05, z - 0.05), (0, yy + 0.05, z - 0.05), 0.5, "in_brass_pol", sides=8)
    c = v3(0, y + 1.3, z + 0.25)
    tube(bone, "lit_helm_shaft", (0, y + 1.3, z - 0.05), c, 0.12, "in_brass_pol", sides=6)
    wb = Bone("helm_wheel", origin=tuple(c), parent=root)
    gl.ship_wheel(wb, "lit_helm", c, (0, 0, 1), r=0.85, region="in_wood_carved")
    disc(wb, "glow_helm_gem", c + v3(0, 0, 0.1), (0, 0, 1), 0.1, 0.06, "gem", sides=8)


def crystal_engine(root, bone):
    """The engine room's great machine (reference panel 3): a riveted brass drum on its bed with a glowing crystal core in a
    round bezel facing the landing, gears turning on its sides (engine_gear_*), pistons, a dome, pipes to the walls."""
    ex, ez, er, e0, e1 = ci.ENGINE
    pz0, pz1, ptop = ci.PLINTH
    fitted = bone
    eb = Bone("engine_body", origin=(ex, e0, ez), parent=fitted)
    c = v3(ex, e0 + 2.0, ez)
    box(eb, "lit_engine_bed", (ex, e0 + 0.3, ez), (3.6, 0.6, 3.4), {"all": "in_rivets", "+2": "in_iron"})
    tube(eb, "lit_engine_drum", c - v3(0, 0, 1.4), c + v3(0, 0, 1.2), 2.9, "in_boiler", sides=12)
    for k, dz in enumerate((-1.3, -0.2, 1.0)):
        tube(eb, "lit_engine_drum_band_%d" % k, c + v3(0, 0, dz - 0.08), c + v3(0, 0, dz + 0.08), 3.05, "in_gold", sides=12)
    disc(eb, "lit_engine_bezel", c + v3(0, 0, 1.25), (0, 0, 1), 1.25, 0.25, "in_brass_pol", sides=16)
    add_cube(eb, "glow_engine_core", c + v3(0, 0, 1.4), EYE, (1.9, 1.9, 0.02), {"all": None, "+3": "in_core", "-3": "in_core"}, stretch=True)
    ring(eb, "lit_engine_bezel_ring", c + v3(0, 0, 1.42), (0, 0, 1), 1.05, 0.14, "in_gold", n=16)
    tube(eb, "lit_engine_dome", c + v3(0, 1.2, -0.2), c + v3(0, 1.9, -0.2), 1.6, "in_brass_pol", sides=10)
    tube(eb, "lit_engine_dome_top", c + v3(0, 1.9, -0.2), c + v3(0, 2.2, -0.2), 0.9, "in_gold", sides=10)
    for s in (1, -1):
        gb = Bone("engine_gear_%d" % (s > 0), origin=tuple(c + v3(s * 1.55, 0.2, -0.3)), parent=root)
        lf.gear(gb, "lit_engine_gear_%d" % (s > 0), c + v3(s * 1.55, 0.2, -0.3), (1, 0, 0), 1.0, 0.16, teeth=16, region="in_brass", spokes=6)
        for k, dz in enumerate((-0.6, 0.4)):
            pb = Bone("engine_piston_%d_%d" % (s > 0, k), origin=tuple(c + v3(s * 0.9, 1.3, dz)), parent=eb)
            tube(eb, "lit_engine_cyl_%d_%d" % (s > 0, k), c + v3(s * 0.9, 0.9, dz), c + v3(s * 0.9, 1.5, dz), 0.42, "in_copper", sides=8)
            tube(pb, "lit_engine_rod_%d_%d" % (s > 0, k), c + v3(s * 0.9, 1.5, dz), c + v3(s * 0.9, 2.2, dz), 0.1, "in_iron", sides=4)
            box(pb, "lit_engine_crosshead_%d_%d" % (s > 0, k), c + v3(s * 0.9, 2.25, dz), (0.24, 0.12, 0.24), "in_brass")
    # pipes from the machine to the nacelles through the side walls, and up into the ceiling
    for s in (1, -1):
        lf.pipe(fitted, "engine_pipe_side_%d" % (s > 0), [c + v3(s * 1.2, 0.8, 0.4), c + v3(s * 2.6, 1.6, 0.4), v3(s * 4.6, c[1] + 1.6, ez + 0.4)], d=0.34)
        lf.pipe(fitted, "engine_pipe_up_%d" % (s > 0), [c + v3(s * 0.5, 1.6, -1.0), c + v3(s * 0.5, 3.5, -1.0), v3(s * 0.5, ci.CEIL_LO - 0.05, ez - 1.0)],
                d=0.26, region="in_brass")
        lf.valve(fitted, "engine_valve_%d" % (s > 0), c + v3(s * 2.0, 1.4, 0.4), (0, 0, 1), r=0.22)
    lf.gauge_board(fitted, "engine_gauges", v3(0, c[1] + 0.8, pz0 + 0.05), (0, 0, 1), w=1.6, h=0.9)


FURNITURE_BUILDERS = dict(gl.FURNITURE_BUILDERS)
FURNITURE_BUILDERS.update({name: gl._named(getattr(cf, name)) for name in ("instrument_column", "crystal_lamp", "wall_gauge", "world_map",
                                                                       "hanging_chain", "speaking_tube")})
FURNITURE_BUILDERS["painting_frame"] = gl._named(lf.painting_frame)
FURNITURE_BUILDERS["gauge_board"] = gl._named(lf.gauge_board)


def fallbacks(root, decor):
    """Stand-ins of the decoration blocks, shown only when their mod is missing on a client."""
    if decor is None:
        return
    for i, b in enumerate(decor.BLOCKS):
        x0, x1, y0, y1, z0, z1 = decor.footprint(b)
        bone = Bone("fallback_%d" % i, parent=root)
        pre = "glow" if b["block"] in decor.GLOWING_FALLBACK else "lit"
        add_cube(bone, "%s_fallback_%d" % (pre, i), v3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), EYE,
                 (max(0.04, x1 - x0), max(0.04, y1 - y0), max(0.04, z1 - z0)), decor.FALLBACK_REGION.get(b["block"], "in_plank"), stretch=True)


# ================================================================ build
def build(g, decor=None):
    root = Bone("crystal_airship")
    bal = Bone("balloon", parent=root)
    strp = Bone("straps", parent=root)
    detail = Bone("detail", parent=root)
    gems = Bone("gems", parent=root)
    rig = Bone("rigging", parent=root)
    mast_b = Bone("mast", parent=root)
    ring_b = Bone("ring", parent=root)
    hull_b = Bone("hull", parent=root)
    deck_b = Bone("decks", parent=root)
    turret_b = Bone("turret", parent=root)
    castle_b = Bone("castle", parent=root)
    roof_b = Bone("roof", parent=root)
    eng = Bone("engines", parent=root)
    crys = Bone("crystals", parent=root)
    lights = Bone("lights", parent=root)
    lanterns_b = Bone("lanterns", parent=root)
    rooms = Bone("rooms", parent=root)
    fittings = Bone("fittings", parent=root)
    furniture = Bone("furniture", parent=root)
    balloon(bal)
    girdle = straps(strp, gems)
    mast(mast_b, root)
    golden_ring(ring_b, detail)
    hull(hull_b, detail, lights)
    decks(deck_b, detail, g)
    stairs(deck_b, fittings)
    turret(turret_b, detail, lights)
    castle(castle_b, detail, lights, roof_b)
    nacelles(eng, detail, lights, root)
    rear_engine(eng, detail, lights, root)
    prop_pods(eng, detail, lights, root)
    tail = crystals(crys, lights, detail, root, lanterns_b)
    rigging(rig, girdle)
    pennants(root, tail)
    lanterns(lanterns_b, detail)
    m = surfaces(rooms, g)
    ladders(fittings)
    helm(root, fittings)
    crystal_engine(root, fittings)
    fallbacks(root, decor)
    if decor is not None:
        for k, (builder, kwargs, solid) in enumerate(decor.CUSTOM):
            kw = dict(kwargs)
            kw.setdefault("name", "%s_%d" % (builder, k))
            FURNITURE_BUILDERS[builder](furniture, **kw)
    return root, m


def _loop_keys(length, n, fn):
    ts = [length * i / n for i in range(n + 1)]
    return [(t, fn(t if i < n else 0.0)) for i, t in enumerate(ts)]


def build_animations(root):
    """The model's animations (driven by the mod, see ShipRenderer):
    propeller (time = the engine's phase, which only advances with the speed: still when parked) - the nacelles' rotors,
      the stern propeller, the leaf propellers of the pods (three turns per loop);
    engine (the same phase) - the crystal engine's gears and pistons;
    steer (hold, 0..2 = helm from -1 to 1) - the helm wheel; elevator (hold, 0..2 = climb) - the nacelles' flaps;
    flag_wave, streamer_wave, lantern_sway (time = the game time) - the mast's flag; the pennants, the floating pods
      bobbing with their rings turning; the hanging lanterns and crystal lanterns."""
    kf, rot_kf, animation, find = gg.kf, gg.rot_kf, gg.animation, gg.find
    anims = []
    turns = 3
    spin = [rot_kf(t, (0, 0, -360.0 * turns * t / 2.0)) for t in [k * 2.0 / 24 for k in range(25)]]
    tracks = [(find(root, n), spin) for n in ("rotor_p", "rotor_s", "rear_prop", "pod_prop_p", "pod_prop_s")]
    anims.append(animation("propeller", 2.0, "loop", tracks))
    tracks = []
    for k, sgn in ((0, 1), (1, -1)):
        tracks.append((find(root, "engine_gear_%d" % k), [rot_kf(t, (sgn * 180.0 * t, 0, 0)) for t in (0.0, 0.5, 1.0, 1.5, 2.0)]))
    for s in range(2):
        for k in range(2):
            b = find(root, "engine_piston_%d_%d" % (s, k))
            tracks.append((b, [kf("position", t, (0, v, 0)) for t, v in
                               _loop_keys(2.0, 16, lambda t, ph=(s + k) * math.pi / 2: 0.28 * 16 * math.sin(math.pi * t + ph))]))
    anims.append(animation("engine", 2.0, "loop", tracks))
    anims.append(animation("steer", 2.0, "hold", [
        (find(root, "helm_wheel"), [rot_kf(0.0, (0, 0, -150)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 0, 150))])]))
    anims.append(animation("elevator", 2.0, "hold", [
        (find(root, n), [rot_kf(0.0, (-14, 0, 0)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (14, 0, 0))]) for n in ("flap_p", "flap_s")]))
    f, ft = find(root, "flag"), find(root, "flag_tip")
    anims.append(animation("flag_wave", 1.2, "loop", [
        (f, [rot_kf(0.0, (0, 8, 0), "catmullrom"), rot_kf(0.6, (0, -8, 0), "catmullrom"), rot_kf(1.2, (0, 8, 0), "catmullrom")]),
        (ft, [rot_kf(0.0, (0, -16, 0), "catmullrom"), rot_kf(0.6, (0, 16, 0), "catmullrom"), rot_kf(1.2, (0, -16, 0), "catmullrom")])]))
    tracks = []
    w = 2 * math.pi / 3.0
    for k, b in enumerate(c for c in find(root, "pennants").children if c.name.startswith("pennant_") and not c.name.endswith("_tip")
                          and not c.name.startswith("pennant_pole")):
        sh = 0.8 * k
        tracks.append((b, [rot_kf(t, (0, 9 * math.sin(w * t + sh), 0)) for t, _ in _loop_keys(3.0, 8, lambda t: 0)]))
        tip = find(root, b.name + "_tip")
        if tip is not None:
            tracks.append((tip, [rot_kf(t, (0, -14 * math.sin(w * t + sh), 0)) for t, _ in _loop_keys(3.0, 8, lambda t: 0)]))
    for k, name in enumerate(("pod_front", "pod_rear")):
        b = find(root, name)
        tracks.append((b, [kf("position", t, (0, 16 * 0.12 * math.sin(w * t + 1.7 * k), 0)) for t, _ in _loop_keys(3.0, 12, lambda t: 0)]))
        r = find(root, name + "_ring")
        tracks.append((r, [rot_kf(t, (0, 0, (1 if k else -1) * 360.0 * t / 3.0)) for t in [3.0 * i / 12 for i in range(13)]]))
    anims.append(animation("streamer_wave", 3.0, "loop", tracks))
    tracks = []
    lan = find(root, "lanterns")
    for k, b in enumerate(c for c in lan.children if c.name.startswith("lantern_")):
        sh = (0.37 * k) % 4.0
        keys = [rot_kf(t, (5 * math.sin(2 * math.pi * (t + sh) / 4.0), 0, 4 * math.cos(2 * math.pi * (t + sh) / 4.0))) for t in (0.0, 1.0, 2.0, 3.0, 4.0)]
        tracks.append((b, keys))
    anims.append(animation("lantern_sway", 4.0, "loop", tracks))
    return anims


def check_axes(root):
    bad = []
    stack = [root]
    while stack:
        b = stack.pop()
        stack.extend(b.children)
        for c in b.cubes:
            R = np.asarray(c.axes, dtype=float)
            if np.abs(R.T @ R - np.eye(3)).max() > 1e-3 or np.linalg.det(R) < 0:
                bad.append(c.name)
    return bad


def main(out_paths=None, write_resources=True):
    if os.environ.get("CRYSTAL_FAST"):
        import zfight
        zfight.fix = lambda root: 0
    g = ci.build()
    try:
        import crystal_decor as cd
    except ImportError:
        cd = None
    if cd is not None:
        cd.build()
        cd.apply_to_grid(g)
        cd.write(os.path.join(ROOT, cd.DECOR_PATH) if write_resources else os.path.splitext(out_paths[0])[0] + "_decor.json")
    if write_resources:
        size = g.write(os.path.join(ROOT, ci.GRID_PATH))
    else:
        size = 0
    reached, total = ci.walkable_report(g)
    unreachable = [name for name, n in reached.items() if not n]
    print("decor blocks:", len(cd.BLOCKS) if cd else 0, "seats:", len(cd.SEATS) if cd else 0, "standing places:", total,
          "unreachable:", unreachable)
    root, m = build(g, cd)
    anims = build_animations(root)
    anims += doors(root)
    bad = check_axes(root)
    if bad:
        print("WARNING: %d cubes with skewed axes, e.g." % len(bad), bad[:8])
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    if write_resources:
        tex_path = os.path.join(tex_dir, "entity/crystal_airship.png")
        in_path = os.path.join(tex_dir, "entity/crystal_airship_interior.png")
        ct.make_item_icon(os.path.join(tex_dir, "item/crystal_airship.png"))
    else:
        tex_path = "/tmp/claude-0/agent_crystal/tex.png"
        in_path = "/tmp/claude-0/agent_crystal/tex_in.png"
    ct.make_texture(tex_path)
    ct.make_interior_texture(in_path, "/tmp/claude-0/agent_crystal/tex_in_base.png" if not write_resources else in_path)
    with open(tex_path, "rb") as f:
        png = f.read()
    with open(in_path, "rb") as f:
        png_in = f.read()
    textures = [gn.texture_entry("crystal_airship.png", ct.SIZE, png, "entity", "crystal_airship.png"),
                gn.texture_entry("crystal_airship_interior.png", ct.SIZE_IN, png_in, "entity", "crystal_airship.png")]
    textures[0]["id"] = "0"
    textures[1]["id"] = "1"
    out_paths = out_paths or [os.path.join(ROOT, "blockbench/crystal_airship.bbmodel"),
                              os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/crystal_airship.bbmodel")]
    model = gn.export(root, anims, textures, out_paths, name="crystal_airship", visible_box=(60, 48, 0))
    print("grid bytes:", size, "grid surfaces:", m, "cubes:", len(model["elements"]), "animations:", len(model["animations"]))
    return model


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main([sys.argv[1]], write_resources=False)
    else:
        main()
