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
  rotor_p, rotor_s, pod_prop_p, pod_prop_s (propeller: played with the engine's phase, which advances with the signed
  speed: still when parked)   stern_gear, engine_* (engine)   helm_wheel (steer)   flap_p, flap_s (elevator)
  flag, flag_tip (flag_wave)   pennant_* (streamer_wave)   pod_front, pod_rear, pod_*_ring (streamer_wave: the floating
  pods bob and their rings turn)   balloon, straps, gems (streamer_wave: the balloon breathes)   lantern_* (lantern_sway)
  door_<k> (door k: 0 closed, 1 open)
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
                # each panel shows the next quarter of the skin's tile (continuous from panel to panel, no random patches)
                quad(bone, "lobe_%s_%d_%d" % (name, i, j), pts[0], pts[1], pts[2], pts[3], 0.12, region, outward,
                     back="cloth_dark", u_dir=v3(0, 0, 1), v_dir=pts[2] - pts[0], overlap=(1.03, 1.05),
                     sub=((i % 4) / 4, (j % 4) / 4, (i % 4 + 1) / 4, (j % 4 + 1) / 4))
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
            disc(gems, "glow_gem_%s%d" % (sn, j), p + nrm * 0.04, nrm, 0.45, 0.14, "gem", sides=10)
            disc(bone, "gem_setting_%s%d" % (sn, j), p - nrm * 0.04, nrm, 0.62, 0.12, "brass", sides=10)
        for j in range(len(cross_z) - 1):
            za, zb = cross_z[j], cross_z[j + 1]
            for drop, w in ((16.0, 0.2), (8.0, 0.15)):
                pts = []
                for q in range(9):
                    z = za + (zb - za) * q / 8
                    pts.append(LP("c", z, az + side * drop * math.sin(math.pi * q / 8), 0.22))
                polyline(bone, "swag_%s%d_%d" % (sn, j, int(drop)), pts, w, "gold", sides=4)
            zm = (za + zb) / 2
            p = LP("c", zm, az + side * 16.0, 0.3)
            nrm = norm(LP("c", zm, az + side * 16.0, 1.0) - LP("c", zm, az + side * 16.0))
            disc(gems, "glow_gem_swag_%s%d" % (sn, j), p, nrm, 0.3, 0.12, "gem", sides=8)
            disc(bone, "gem_swag_setting_%s%d" % (sn, j), p - nrm * 0.06, nrm, 0.42, 0.08, "brass", sides=8)
            # warm fairy lights hanging under the swag
            for q in range(1, 8):
                if q == 4:
                    continue
                z = za + (zb - za) * q / 8
                pq = LP("c", z, az + side * (16.0 * math.sin(math.pi * q / 8) + 2.5), 0.3)
                nq = norm(LP("c", z, az + side * 18.0, 1.0) - LP("c", z, az + side * 18.0))
                disc(gems, "glow_fairy_%s%d_%d" % (sn, j, q), pq, nq, 0.12, 0.1, "fairy", sides=6)
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
            disc(gems, "glow_gem_s%d_%d" % (k, side > 0), p, nrm, 0.4, 0.14, "gem", sides=10)
            disc(bone, "gem_s_setting_%d_%d" % (k, side > 0), p - nrm * 0.07, nrm, 0.55, 0.1, "brass", sides=10)
    # meridian straps from nose to tail (they read as a net of gilded bands from the ends)
    for name, azs in cs.MERIDIANS.items():
        lb = cs.lobe(name)
        zz = lobe_stations(lb, 22)[1:-1]
        for az0 in azs:
            for sgn in (1, -1):
                az = sgn * az0
                for j in range(len(zz) - 1):
                    pa, pb = LP(name, zz[j], az, 0.1), LP(name, zz[j + 1], az, 0.1)
                    if hidden(pa, name, 0.25) and hidden(pb, name, 0.25):
                        continue
                    nrm = norm(LP(name, (zz[j] + zz[j + 1]) / 2, az, 1.0) - LP(name, (zz[j] + zz[j + 1]) / 2, az))
                    beam(bone, "meridian_%s%d_%d_%d" % (name, int(az0), sgn > 0, j), pa, pb, 0.1, "strap", width=0.32, up=nrm, extend=0.05,
                         u_dir=pb - pa)
    # a strap along the top of the central and the end lobes
    for name in ("c", "f", "r", "fp", "fs", "rp", "rs"):
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
    n = 64
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        p0 = c + v3(0, math.cos(a0), math.sin(a0)) * rm
        p1 = c + v3(0, math.cos(a1), math.sin(a1)) * rm
        am = (a0 + a1) / 2
        rad = v3(0, math.cos(am), math.sin(am))
        beam(bone, "ring_%d" % k, p0, p1, w, "ring_bronze", width=t, up=rad, extend=0.03, u_dir=p1 - p0)
        # a smooth raised bead round both faces (outer and inner edges), a polished brass lip on the outside
        for sx in (1, -1):
            for e, (rr, tag) in enumerate(((ro - 0.14, ""), (ro - w + 0.14, "_in"))):
                q0 = c + v3(sx * (t / 2 + 0.03), 0, 0) + v3(0, math.cos(a0), math.sin(a0)) * rr
                q1 = c + v3(sx * (t / 2 + 0.03), 0, 0) + v3(0, math.cos(a1), math.sin(a1)) * rr
                beam(detail, "ring_bead%s_%d_%d" % (tag, k, sx > 0), q0, q1, 0.1, "bronze", width=0.08, up=rad, extend=0.02, u_dir=q1 - q0)
        q0, q1 = c + v3(0, math.cos(a0), math.sin(a0)) * (ro + 0.02), c + v3(0, math.cos(a1), math.sin(a1)) * (ro + 0.02)
        beam(detail, "ring_lip_%d" % k, q0, q1, 0.08, "brass", width=t * 0.55, up=rad, extend=0.02, u_dir=q1 - q0)
    for k in range(8):
        a = 2 * math.pi * k / 8 + math.pi / 8
        rad = v3(0, math.cos(a), math.sin(a))
        add_cube(detail, "ring_clamp_%d" % k, c + rad * rm, np.column_stack([v3(1, 0, 0), rad, np.cross(v3(1, 0, 0), rad)]),
                 (t + 0.14, w + 0.14, 0.26), "brass")
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
_WIN_EDGES = [z for w in ci.LOUNGE_WINDOWS for z in w]
HULL_ST = sorted(set([cs.STERN_Z, -22.995, -22.985, -22.965, -22.93, -22.88, -22.8, -22.68, -22.52, -22.3, -22.02, -21.68, -21.25, -20.7,
                      -20.0, -19.2, -18.2, -17.0, -15.7, -14.3, -12.9, -11.5, -10.1, -8.7, -7.3, -6.4] + _WIN_EDGES +
                     [9.6, 10.4, 11.2, 12.0, 12.8, 13.5, 14.2, 14.9, 15.6, 16.3, 17.0, 17.7, 18.4, 19.1, 19.8, 20.5, 21.2, 21.9, 22.5, 23.1, 23.6,
                      24.1, 24.5, 24.9, 25.25, 25.55, 25.8, 26.0, 26.15]))
FC_PANEL = (11.6, 0.55)    # the forecastle's green panel: from this z forward, from this y up to under the cap rail


def section_ys(z):
    """Heights of the hull's rows at z, from the keel up to the sheer (fixed count; collapsed where the hull is low):
    the brown strakes along the keel, the green band, the brown gallery band (rows at the windows' sill and head), the
    forecastle's green panel."""
    k = cs.keel_y(z)
    top = cs.sheer_y(z)
    lo = min(max(k, cs.band_low(z)), top)
    b = min(max(lo, cs.band_y(z)), top)
    ys = [k + f * (lo - k) for f in (0.0, 0.08, 0.2, 0.36, 0.56, 0.78, 1.0)]
    ys += [lo + f * (b - lo) for f in (0.25, 0.5, 0.75, 1.0)]
    ys += [min(max(y, b), top) for y in (-3.0, -2.0, -1.0, 0.0, FC_PANEL[1], cs.SHEER_WAIST)]
    ys += [min(max(y, b, cs.SHEER_WAIST), top) for y in (cs.SHEER_WAIST + 0.5 * (top - 0.3 - cs.SHEER_WAIST), top - 0.3, top)]
    return ys


def section(z, side):
    return [v3(side * max(0.03, cs.hull_x(z, y)), y, z) for y in section_ys(z)]


def hull_region(z, y):
    if y < cs.band_low(z) - 0.01:
        return "hull_brown"
    if y < cs.band_y(z) + 0.01:
        return "hull_green"
    if z > FC_PANEL[0] and FC_PANEL[1] - 0.01 < y < cs.sheer_y(z) - 0.29:
        return "hull_green"
    return "hull_brown"


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


def fan_window(bone, detail, side, sn):
    """The bow's fan window (outside only): a quarter fan from its hub at the upper aft corner, in facets following the
    bow's curve, stained panes between dark ribs, a gilded rim; two lit windows aft of it."""
    zh, yh, R = ci.ROSE
    na, nr = 7, 4
    rs = [R * (0.12 + 0.88 * j / nr) for j in range(nr + 1)]

    def P(a, r, out=0.05):
        a = math.radians(a)
        return hull_pt(zh + r * math.cos(a), yh - r * math.sin(a), side, out)
    for i in range(na):
        a0, a1 = 90.0 * i / na, 90.0 * (i + 1) / na
        for j in range(nr):
            p00, n = P(a0, rs[j])
            p10, _ = P(a1, rs[j])
            p01, _ = P(a0, rs[j + 1])
            p11, _ = P(a1, rs[j + 1])
            pm = P((a0 + a1) / 2, rs[j])[0]
            quad(bone, "glow_fan_%s%d_%d" % (sn, i, j), p00, p10, p01, p11, 0.03, "window_fan", n,
                 sub=(i / na, rs[j] / R, (i + 1) / na, rs[j + 1] / R), u_dir=p10 - p00, v_dir=P((a0 + a1) / 2, rs[j + 1])[0] - pm,
                 overlap=(1.02, 1.02))
    rim = [P(a, R + 0.1, 0.1)[0] for a in np.linspace(0, 90, 13)]
    polyline(detail, "fan_rim_%s" % sn, rim, 0.2, "gold", sides=4)
    polyline(detail, "fan_top_%s" % sn, [P(0, r, 0.1)[0] for r in np.linspace(0.0, R + 0.1, 6)], 0.2, "gold", sides=4)
    polyline(detail, "fan_aft_%s" % sn, [P(90, r, 0.1)[0] for r in np.linspace(0.0, R + 0.1, 6)], 0.2, "gold", sides=4)
    disc(detail, "fan_hub_%s" % sn, P(0, 0.0, 0.1)[0], P(0, 0.0)[1], 0.36, 0.12, "gold", sides=8)
    for k, z in enumerate((11.0, 12.4)):
        p, n = hull_pt(z, -3.1, side, 0.04)
        add_cube(bone, "glow_bow_window_%s%d" % (sn, k), p, gl.wall_frame(n), (0.9, 1.8, 0.03),
                 {"all": None, "+3": "window_lit", "-3": "window_lit"}, stretch=True)
        for e, dz in enumerate((-0.52, 0.52)):
            q, m = hull_pt(z + dz, -3.1, side, 0.1)
            box(detail, "bow_window_jamb_%s%d_%d" % (sn, k, e), q, (0.14, 2.0, 0.14), "dark_wood", R=gl.wall_frame(m))
        q, m = hull_pt(z, -2.1, side, 0.12)
        box(detail, "bow_window_head_%s%d" % (sn, k), q, (1.2, 0.14, 0.2), "gold", R=gl.wall_frame(m))


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
                if np.linalg.norm(B[k] - A[k]) + np.linalg.norm(B[k + 1] - A[k + 1]) < 0.02:
                    continue
                region = hull_region(mid[2], mid[1])
                outward = norm(v3(side, -0.5 if k < 6 else 0.0, 0.25 * np.sign(mid[2])))
                quad(bone, "hull_%s%d_%d" % (sn, i, k), A[k], B[k], A[k + 1], B[k + 1], 0.14, region, outward, u_dir=v3(0, 0, 1),
                     stretch=False, back="dark_wood", overlap=(1.03, 1.06))
    # the flat of the bottom between the two sides
    for i in range(len(HULL_ST) - 1):
        za, zb = HULL_ST[i], HULL_ST[i + 1]
        if zb > 25.0:
            break
        xa, xb = cs.hull_x(za, cs.keel_y(za)), cs.hull_x(zb, cs.keel_y(zb))
        ya, yb = cs.keel_y(za), cs.keel_y(zb)
        if xa + xb < 0.05:
            continue
        quad(bone, "bottom_%d" % i, v3(-xa, ya, za), v3(-xb, yb, zb), v3(xa, ya, za), v3(xb, yb, zb), 0.14, "hull_brown", v3(0, -1, 0),
             u_dir=v3(0, 0, 1), stretch=False)
    # the keel and the stem sweeping up to the carved stem head; the stern post behind the medallion
    kp = [v3(0, cs.keel_y(z) - 0.1, z) for z in np.linspace(cs.STERN_Z + 0.15, 26.1, 44)]
    sm = catmull(kp, 2)
    for k in range(len(sm) - 1):
        beam(bone, "keel_%d" % k, sm[k], sm[k + 1], 0.44, "hull_band", width=0.42, up=v3(1, 0, 0), extend=0.08)
    beam(bone, "stern_post", v3(0, cs.keel_y(cs.STERN_Z) - 0.1, cs.STERN_Z - 0.02), v3(0, cs.sheer_y(cs.STERN_Z), cs.STERN_Z - 0.02), 0.44,
         "hull_band", width=0.42, up=v3(1, 0, 0))
    zs_, top = cs.STEM_HEAD
    head0 = v3(0, cs.keel_y(26.1) - 0.1, 26.1)
    head1 = v3(0, top - 0.35, zs_ + 0.05)
    beam(bone, "stem_head", head0, head1, 0.46, "dark_wood", width=0.46, up=v3(1, 0, 0), extend=0.1)
    vol = [head1 + v3(0, 0.3 * (1 - t / 9.5) * math.sin(t) + 0.3, -0.3 * (1 - t / 9.5) * math.cos(t) + 0.0) for t in np.linspace(0, 9.0, 16)]
    polyline(detail, "stem_volute", vol, 0.2, "gold", sides=6)
    beam(detail, "stem_band", head0 + v3(0, 0.4, 0), head0 + v3(0, 0.62, 0), 0.5, "gold", width=0.5, up=v3(1, 0, 0))
    # gilded and dark mouldings following the hull's curves: under the cap rail, the top of the green band, a line on
    # the green, its foot (a dark wale); the forecastle panel's frame; the gallery's head and sill
    zz = list(np.linspace(cs.STERN_Z + 0.08, 26.0, 90))
    for side, sn in SIDES:
        side_curve(bone, "trim_band_" + sn, zz, cs.band_y, side, 0.06, 0.26, 0.12, "trim_gold")
        side_curve(detail, "trim_green_" + sn, zz, lambda z: cs.band_y(z) - 0.5 * (cs.band_y(z) - cs.band_low(z)), side, 0.05, 0.14, 0.1,
                   "trim_gold")
        side_curve(bone, "wale_low_" + sn, zz, cs.band_low, side, 0.05, 0.3, 0.12, "hull_band")
        side_curve(bone, "trim_rail_" + sn, zz, lambda z: cs.sheer_y(z) - 0.22, side, 0.06, 0.2, 0.1, "trim_gold")
        side_curve(bone, "wale_deck_" + sn, [z for z in zz if z < 12.6], lambda z: -0.45, side, 0.07, 0.34, 0.14, "trim_dark")
        side_curve(bone, "fc_moulding_" + sn, [z for z in zz if z > FC_PANEL[0]], lambda z: FC_PANEL[1], side, 0.06, 0.2, 0.12, "trim_gold")
        g0, g1 = ci.LOUNGE_WINDOWS[0][0] - 0.9, ci.LOUNGE_WINDOWS[-1][1] + 0.9
        gz = list(np.linspace(g0, g1, 24))
        side_curve(detail, "gallery_cornice_" + sn, gz, lambda z: ci.WIN_Y[1] + 0.32, side, 0.2, 0.26, 0.4, "cornice")
        side_curve(detail, "gallery_sill_" + sn, gz, lambda z: ci.WIN_Y[0] - 0.24, side, 0.16, 0.22, 0.34, "cornice")
        side_curve(detail, "trim_sill_" + sn, gz, lambda z: ci.WIN_Y[0] - 0.08, side, 0.1, 0.12, 0.12, "trim_gold")
        side_curve(detail, "trim_head_" + sn, gz, lambda z: ci.WIN_Y[1] + 0.1, side, 0.1, 0.12, 0.12, "trim_gold")
    # the gallery of the lounge: six tall lit windows (amber quarries and clear ones: seen through from inside), carved
    # pilasters with gilded capitals and bases between them
    for side, sn in SIDES:
        for k, (z0, z1) in enumerate(ci.LOUNGE_WINDOWS):
            y0, y1 = ci.WIN_Y
            pa, na_ = hull_pt(z0, (y0 + y1) / 2, side, 0.0)
            pb, nb = hull_pt(z1, (y0 + y1) / 2, side, 0.0)
            n = norm(na_ + nb)
            c = (pa + pb) / 2 + n * 0.01
            t = norm((pb - pa) - np.dot(pb - pa, n) * n)
            R = np.column_stack([t, np.cross(n, t), n])
            L = np.linalg.norm(pb - pa)
            add_cube(lights, "glow_gallery_window_%s%d" % (sn, k), c, R, (L, y1 - y0, 0.06),
                     {"all": None, "+3": "window_gallery", "-3": "window_gallery"}, stretch=True, u_dir=pb - pa, v_dir=v3(0, -1, 0))
            for e, (pz, nz) in enumerate(((pa, na_), (pb, nb))):
                add_cube(detail, "window_reveal_%s%d_%d" % (sn, k, e), pz - n * 0.45, R, (0.08, y1 - y0, 0.9), "dark_wood")
            add_cube(detail, "window_reveal_top_%s%d" % (sn, k), c - n * 0.45 + v3(0, (y1 - y0) / 2, 0), R, (L, 0.08, 0.9), "dark_wood")
            add_cube(detail, "window_reveal_bot_%s%d" % (sn, k), c - n * 0.45 - v3(0, (y1 - y0) / 2, 0), R, (L, 0.08, 0.9), "dark_wood")
        edges = sorted(set([z for w in ci.LOUNGE_WINDOWS for z in w]))
        posts = [edges[0] - 0.3] + [(edges[i] + edges[i + 1]) / 2 for i in range(1, len(edges) - 1, 2)] + [edges[-1] + 0.3]
        for k, z in enumerate(posts):
            pts = [hull_pt(z, y, side, 0.14)[0] for y in np.linspace(ci.WIN_Y[0] - 0.2, ci.WIN_Y[1] + 0.25, 4)]
            polyline(detail, "pilaster_%s%d" % (sn, k), pts, 0.34, "dark_wood", sides=4, extend=0.02)
            p, n = hull_pt(z, ci.WIN_Y[1] + 0.2, side, 0.24)
            box(detail, "pilaster_cap_%s%d" % (sn, k), p, (0.46, 0.18, 0.3), "gold", R=gl.wall_frame(n))
            p, n = hull_pt(z, ci.WIN_Y[0] - 0.15, side, 0.24)
            box(detail, "pilaster_base_%s%d" % (sn, k), p, (0.46, 0.16, 0.3), "gold", R=gl.wall_frame(n))
            p, n = hull_pt(z, ci.WIN_Y[0] - 0.75, side, 0.12)
            box(detail, "pilaster_bracket_%s%d" % (sn, k), p, (0.3, 0.5, 0.2), "dark_wood", R=gl.wall_frame(n))
    # the bow's fan windows, gilded spirals on the forecastle's green panels
    for side, sn in SIDES:
        fan_window(lights, detail, side, sn)
        for k, (z, y, sz) in enumerate(((20.4, 1.55, 1.7), (16.2, 1.45, 1.3))):
            p, n = hull_pt(z, y, side, 0.05)
            add_cube(detail, "scroll_%s%d" % (sn, k), p, gl.wall_frame(n), (sz, sz * 0.62, 0.03), {"all": None, "+3": "scroll", "-3": "scroll"},
                     stretch=True, u_dir=v3(0, 0, -side), v_dir=v3(0, -1, 0))
    # the bowsprit: a square spar angled up from the bow, brass bands, a gilded cap, stays to the cutwater
    (bz0, by0), (bz1, by1), bw = cs.BOWSPRIT
    p0, p1 = v3(0, by0, bz0), v3(0, by1, bz1)
    beam(bone, "bowsprit", p0, p1, bw, "dark_wood", width=bw, up=v3(0, 1, 0), extend=0.05, u_dir=p1 - p0)
    d = norm(p1 - p0)
    for k, t in enumerate((0.42, 0.62, 0.84)):
        q = p0 + (p1 - p0) * t
        beam(bone, "bowsprit_band_%d" % k, q - d * 0.08, q + d * 0.08, bw + 0.1, "brass", width=bw + 0.1, up=v3(0, 1, 0))
    tube(bone, "bowsprit_cap", p1 - d * 0.05, p1 + d * 0.3, 0.5, "gold", sides=8)
    disc(bone, "bowsprit_knob", p1 + d * 0.38, d, 0.22, 0.16, "gold", sides=8)
    cut = v3(0, -1.6, 24.0)
    rope(detail, "bowsprit_stay", p1 - d * 0.1, cut + v3(0, 0, 0.35), d=0.08, region="rope_dark", sag=0.15)
    for side, sn in SIDES:
        q, _ = hull_pt(23.2, cs.sheer_y(23.2) - 0.4, side, 0.05)
        rope(detail, "bowsprit_shroud_" + sn, p1 - d * 0.3, q, d=0.07, region="rope_dark", sag=0.1)
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
    n += grid_floor(bone, g, cs.L1_TOP, "deck", "terrace", lit=False, zrange=(cs.STERN_Z, cs.CASTLE_Z + 0.2))
    n += grid_floor(bone, g, cs.L2_TOP, "deck", "roof_deck", lit=False, zrange=(cs.STERN2_Z - 0.5, cs.L2_Z + 0.2))
    # balustrades: along the waist's bulwark, round the forecastle, across its front (gaps at the stairs)
    for side, sn in SIDES:
        zz = np.linspace(cs.CASTLE_Z + 0.4, cs.FORECASTLE_Z - 1.6, 26)
        pts = [(side * (cs.hull_x(z, cs.SHEER_WAIST) - 0.16), cs.sheer_y(z) + 0.1, z) for z in zz]
        gl.balustrade(bone, "waist_rail_" + sn, pts, h=0.62, step=0.42, turned=True, newel=8)
    zz = list(np.linspace(cs.FORECASTLE_Z - 1.6, 25.55, 16))
    port = [(cs.hull_x(z, cs.SHEER_WAIST) - 0.16, cs.sheer_y(z) + 0.1, z) for z in zz] + [(0.0, cs.sheer_y(25.75) + 0.1, 25.75)]
    gl.balustrade(bone, "fc_rail", port + [(-x, y, z) for x, y, z in reversed(port[:-1])], h=0.62, step=0.42, turned=True, newel=6)
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
    za, zb = cs.STERN_Z + 1.2, cs.CASTLE_Z - 0.25
    zz = list(np.linspace(za, zb, 18))
    port = [(cs.castle1_x(z) - 0.25, y, z) for z in zz]
    gl.balustrade(bone, "terrace_rail", port + [(-x, yy, z) for x, yy, z in reversed(port)], h=0.85, step=0.42, turned=True, newel=6)
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


def turret(bone, detail, lights, lanterns_bone):
    """The square lookout at the foot of the forecastle (a chimney-like tower): dark planks with iron bands, a gilded
    band, a moulded cap round its open top, lit loopholes, a lantern on a post beside it."""
    hw, z0, z1, top = cs.TURRET
    body = top - 0.45
    zc = (z0 + z1) / 2
    box(bone, "turret_body", (0, body / 2, zc), (2 * hw, body, z1 - z0), {"all": "turret", "+2": "dark_wood"})
    box(bone, "turret_band", (0, body - 0.75, zc), (2 * hw + 0.08, 0.22, z1 - z0 + 0.08), "gold")
    box(bone, "turret_plinth", (0, 0.15, zc), (2 * hw + 0.16, 0.3, z1 - z0 + 0.16), "cornice")
    # the moulded cap: a projecting cornice, a raised rim round the open top, its dark inside
    box(bone, "turret_cornice", (0, body + 0.08, zc), (2 * hw + 0.36, 0.16, z1 - z0 + 0.36), "cornice")
    box(bone, "turret_cornice_bead", (0, body - 0.04, zc), (2 * hw + 0.24, 0.08, z1 - z0 + 0.24), "gold")
    for sx in (-1, 1):
        box(bone, "turret_rim_x%d" % (sx > 0), (sx * (hw - 0.05), body + 0.3, zc), (0.3, 0.3, z1 - z0 + 0.2), "dark_wood")
        box(bone, "turret_rim_z%d" % (sx > 0), (0, body + 0.3, zc + sx * ((z1 - z0) / 2 - 0.05)), (2 * hw - 0.2, 0.3, 0.3), "dark_wood")
        box(detail, "turret_rim_cap_x%d" % (sx > 0), (sx * (hw - 0.05), body + 0.48, zc), (0.36, 0.06, z1 - z0 + 0.26), "brass")
        box(detail, "turret_rim_cap_z%d" % (sx > 0), (0, body + 0.48, zc + sx * ((z1 - z0) / 2 - 0.05)), (2 * hw - 0.14, 0.06, 0.36), "brass")
    box(bone, "turret_inside", (0, body + 0.17, zc), (2 * hw - 0.4, 0.02, z1 - z0 - 0.4), "iron")
    for sx in (-1, 1):
        for k, z in enumerate((z0 + 0.9, z1 - 0.9)):
            add_cube(lights, "glow_turret_window_%d_%d" % (sx > 0, k), v3(sx * (hw + 0.01), body - 1.5, z), EYE, (0.02, 0.6, 0.4),
                     {"all": None, "+1": "window_lit", "-1": "window_lit"}, stretch=True)
    add_cube(lights, "glow_turret_window_aft", v3(0, body - 1.5, z0 - 0.01), EYE, (0.5, 0.7, 0.02),
             {"all": None, "+3": "window_lit", "-3": "window_lit"}, stretch=True)
    # a lantern on a post beside it
    x, z = hw + 0.55, z1 - 0.4
    tube(detail, "turret_lamp_post", v3(x, 0.0, z), v3(x, body + 0.6, z), 0.14, "dark_wood", sides=6)
    beam(detail, "turret_lamp_arm", v3(x, body + 0.6, z), v3(x, body + 0.6, z + 0.45), 0.06, "iron")
    gl.hanging_lantern(lanterns_bone, "turret", v3(x, body + 0.6, z + 0.45), drop=0.1, w=0.3, h=0.42)


# ================================================================ the stern castle
def plan_outline(cxf, z_end, z_round, z_front, extra=(), n_round=14, step=1.0):
    """Port half of a rounded plan, (x, z) from its stern end on the centreline round the quarter and forward to z_front
    (points dense round the stern, where the outline turns)."""
    p = cs.STERN_ROUND[1]
    pts = []
    for k in range(n_round + 1):
        th = (math.pi / 2) * k / n_round
        u = math.cos(th) ** (2.0 / p)
        z = z_round - u * (z_round - z_end)
        pts.append((0.0 if k == 0 else cxf(z), z))
    zs = sorted(set([float(z) for z in np.arange(z_round + step, z_front, step)] + [z for z in extra if z_round < z < z_front] + [z_front]))
    pts += [(cxf(z), z) for z in zs]
    return pts


def outline_world(half, side, y):
    return [v3(side * x, y, z) for x, z in half]


def seg_normal(a, b, side):
    d = b - a
    return norm(v3(side * d[2], 0, -side * d[0]))


def arc_points(half, side, y, ss):
    """Points and outward normals at arc lengths ss along a half outline (from the stern's centreline)."""
    pts = outline_world(half, side, y)
    cum = [0.0]
    for k in range(len(pts) - 1):
        cum.append(cum[-1] + np.linalg.norm(pts[k + 1] - pts[k]))
    out = []
    for s_ in ss:
        k = max(0, min(len(pts) - 2, int(np.searchsorted(cum, s_) - 1)))
        t = (s_ - cum[k]) / max(1e-6, cum[k + 1] - cum[k])
        out.append((pts[k] + (pts[k + 1] - pts[k]) * t, seg_normal(pts[k], pts[k + 1], side)))
    return out, cum[-1]


def plan_wall(bone, name, half, side, y0, y1, region, holes=(), back="dark_wood", th=0.14):
    """Vertical wall along a half outline from y0 to y1; holes: (z0, z1, ya, yb) left open (windows)."""
    pts = outline_world(half, side, 0.0)
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        n = seg_normal(a, b, side)
        zm = (a[2] + b[2]) / 2
        spans = [(y0, y1)]
        for hz0, hz1, ya, yb in holes:
            if hz0 - 1e-6 <= zm <= hz1 + 1e-6:
                spans = [(y0, ya), (yb, y1)]
        for j, (ya, yb) in enumerate(spans):
            if yb - ya < 0.02:
                continue
            quad(bone, "%s_%s%d_%d" % (name, "p" if side > 0 else "s", k, j), a + v3(0, ya, 0), b + v3(0, ya, 0), a + v3(0, yb, 0),
                 b + v3(0, yb, 0), th, region, n, u_dir=b - a, stretch=False, back=back)


def plan_beam(bone, name, half, side, y, out, h, w, region, up=v3(0, 1, 0)):
    pts = outline_world(half, side, y)
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        n = seg_normal(a, b, side)
        beam(bone, "%s_%s%d" % (name, "p" if side > 0 else "s", k), a + n * out, b + n * out, h, region, width=w, up=up, extend=0.06,
             u_dir=b - a)


def plan_fill(bone, name, half, y, region, normal, z_max=None, th=0.12):
    """A horizontal surface filling a half outline and its mirror (strips across the ship)."""
    pts = [(x, z) for x, z in half if z_max is None or z <= z_max + 1e-6]
    for k in range(len(pts) - 1):
        (xa, za), (xb, zb) = pts[k], pts[k + 1]
        if xa + xb < 0.02:
            continue
        quad(bone, "%s_%d" % (name, k), v3(-xa, y, za), v3(xa, y, za), v3(-xb, y, zb), v3(xb, y, zb), th, region, v3(*normal),
             u_dir=v3(1, 0, 0), stretch=False)


def castle(bone, detail, lights, roof_bone, lanterns_bone):
    """The stern castle in tiers. Storey 1 (the officers' mess) inset from the hull's sides, rounded at the stern with a
    gallery of tall lit windows round it and a balcony on the hull's stern bulwark; storey 2 (the cockpit) narrower,
    overhanging the stern on carved brackets, its back of green panels in gilded frames, see-through windows on its
    sides, the great arch and the terrace door in its front; a flat roof deck behind a balustrade, a green coaming with
    gilded scrolls, a crest and volutes, brass portholes with blue jewels, an ensign spar aft."""
    y1top, y2top = cs.L1_TOP, cs.L2_TOP
    half1 = plan_outline(cs.castle1_x, cs.STERN1_END, cs.STERN_ROUND[0] + 0.15, cs.CASTLE_Z, step=0.9)
    win2 = [z for w in ci.COCKPIT_WINDOWS for z in w]
    half2 = plan_outline(cs.castle2_x, cs.STERN2_Z, cs.STERN2_Z + 4.4, cs.L2_Z, extra=win2, step=0.8)
    stern2_z = cs.STERN2_Z + 4.4
    for side, sn in SIDES:
        # ---- storey 1: walls, a dark plinth, the cornice; tall lit windows round the stern, arched ones along the sides
        plan_wall(bone, "castle1_wall", half1, side, cs.L1_Y, y1top, "wall_wood")
        plan_beam(bone, "castle1_cornice", half1, side, y1top - 0.12, 0.1, 0.24, 0.3, "cornice")
        plan_beam(detail, "castle1_bead", half1, side, y1top - 0.3, 0.06, 0.08, 0.12, "trim_gold")
        stern_len = arc_points(half1, side, 0.0, [0.0])[1]
        marks, _ = arc_points(half1, side, 1.95, [0.55, 1.65, 2.75] + [stern_len - (cs.CASTLE_Z - z) for z in (-11.7, -13.3, -14.9, -16.5, -18.1)])
        for k, (p, n) in enumerate(marks):
            tall = k < 3
            size = (0.78, 1.55, 0.03) if tall else (0.62, 1.25, 0.03)
            p = p if tall else p - v3(0, 0.12, 0)
            add_cube(lights, "glow_castle1_window_%s%d" % (sn, k), p + n * 0.03, gl.wall_frame(n), size,
                     {"all": None, "+3": "window_lit", "-3": "window_lit"}, stretch=True)
            box(detail, "castle1_window_frame_%s%d" % (sn, k), p + n * 0.05 + v3(0, -size[1] / 2 - 0.02, 0), (size[0] + 0.2, 0.1, 0.12), "gold",
                R=gl.wall_frame(n))
            box(detail, "castle1_window_hood_%s%d" % (sn, k), p + n * 0.06 + v3(0, size[1] / 2 + 0.12, 0), (size[0] + 0.24, 0.12, 0.16), "gold",
                R=gl.wall_frame(n))
        posts, _ = arc_points(half1, side, 1.5, [0.0, 1.1, 2.2, 3.3] + [stern_len - (cs.CASTLE_Z - z) for z in (-10.4, -12.5, -14.1, -15.7, -17.3)])
        for k, (p, n) in enumerate(posts):
            if k == 0 and side < 0:
                continue
            box(detail, "castle1_pilaster_%s%d" % (sn, k), p + n * 0.05, (0.2, 2.6, 0.1), "gold", R=gl.wall_frame(n))
        # ---- storey 2: the side walls (open at the see-through windows), the green panelled stern
        holes = [(z0, z1) + tuple(ci.COCKPIT_WIN_Y) for z0, z1 in ci.COCKPIT_WINDOWS]
        aft2 = [(x, z) for x, z in half2 if z <= stern2_z + 1e-6]
        fwd2 = [(x, z) for x, z in half2 if z >= stern2_z - 1e-6]
        plan_wall(bone, "castle2_stern", aft2, side, cs.L1_TOP - cs.DECK_SLAB_C, y2top, "stern_panel")
        plan_wall(bone, "castle2_wall", fwd2, side, cs.L1_TOP - cs.DECK_SLAB_C, y2top, "wall_wood", holes=holes)
        for z0, z1 in ci.COCKPIT_WINDOWS:
            wy0, wy1 = ci.COCKPIT_WIN_Y
            x = side * (cs.castle2_x((z0 + z1) / 2) + 0.01)
            add_cube(bone, "cockpit_window_%s%d" % (sn, int(-z0)), v3(x, (wy0 + wy1) / 2, (z0 + z1) / 2), EYE, (0.06, wy1 - wy0, z1 - z0),
                     {"all": None, "+1": "window_arch", "-1": "window_arch"}, stretch=True, u_dir=v3(0, 0, -side), v_dir=v3(0, -1, 0))
            box(detail, "cockpit_window_sill_%s%d" % (sn, int(-z0)), (x + side * 0.06, wy0 - 0.06, (z0 + z1) / 2), (0.14, 0.1, z1 - z0 + 0.3), "gold")
        plan_beam(bone, "castle2_cornice", half2, side, y2top - 0.12, 0.12, 0.26, 0.34, "cornice")
        plan_beam(detail, "castle2_bead", half2, side, y2top - 0.32, 0.06, 0.08, 0.12, "trim_gold")
        plan_beam(bone, "castle2_plinth", half2, side, cs.L1_TOP + 0.08, 0.06, 0.16, 0.16, "trim_gold")
        for k, z in enumerate((-14.3, -17.25, -19.4)):
            x = side * (cs.castle2_x(z) + 0.05)
            box(detail, "castle2_pilaster_%s%d" % (sn, k), (x, (y1top + y2top) / 2, z), (0.1, y2top - y1top - 0.4, 0.22), "gold")
        # ---- the soffit under storey 2's overhang, carved brackets under it, lanterns at the quarters
        brk, _ = arc_points(half2, side, cs.L1_TOP - cs.DECK_SLAB_C, [0.4, 1.6, 2.8])
        for k, (p, n) in enumerate(brk):
            if cs.castle1_x(p[2]) > abs(p[0]) + 0.3:
                continue
            for j in range(3):
                q = p - n * (0.25 + 0.2 * j) - v3(0, 0.15 + 0.22 * j, 0)
                box(detail, "castle2_bracket_%s%d_%d" % (sn, k, j), q, (0.24, 0.3, 0.6 - 0.18 * j), "dark_wood", R=gl.wall_frame(n))
        q, n = arc_points(half2, side, cs.L1_TOP - cs.DECK_SLAB_C, [2.2])[0][0]
        gl.hanging_lantern(lanterns_bone, "stern_%s" % sn, q - n * 0.2, drop=0.25, w=0.3, h=0.42)
        # ---- the stern balcony on the hull's stern bulwark: a floor, gilded balusters
        yb = cs.sheer_y(cs.STERN_Z)
        halfb = plan_outline(cs.balcony_x, cs.STERN_Z - cs.BALCONY[1], cs.STERN_ROUND[0] - 0.3, cs.STERN_ROUND[0] + 0.5, step=0.5, n_round=12)
        rail = [v3(side * (x - 0.12), yb + 0.1, z) for x, z in halfb]
        gl.balustrade(detail, "balcony_rail_" + sn, rail, h=0.55, step=0.4, post="brass", rail="rail", turned=True, newel=7)
        plan_beam(detail, "balcony_edge", halfb, side, yb - 0.02, -0.1, 0.16, 0.3, "cornice")
    plan_fill(bone, "castle2_soffit", half2, cs.L1_TOP - cs.DECK_SLAB_C - 0.01, "dark_wood", (0, -1, 0), z_max=-20.8)
    halfb = plan_outline(cs.balcony_x, cs.STERN_Z - cs.BALCONY[1], cs.STERN_ROUND[0] - 0.3, cs.STERN_ROUND[0] + 0.5, step=0.5, n_round=12)
    plan_fill(bone, "balcony_floor", halfb, cs.sheer_y(cs.STERN_Z) + 0.06, "deck", (0, 1, 0))
    plan_fill(bone, "balcony_under", halfb, cs.sheer_y(cs.STERN_Z) - 0.12, "dark_wood", (0, -1, 0))
    # ---- fronts: storey 1 at CASTLE_Z (the door: see doors()), storey 2 at L2_Z (the great arch, the terrace door)
    z = cs.CASTLE_Z
    w = cs.castle1_x(z)
    for k, (a_, b_, ya, yb_) in enumerate(((-w, -1.0, cs.L1_Y, y1top), (1.0, w, cs.L1_Y, y1top), (-1.0, 1.0, cs.L1_Y + 2.0, y1top))):
        quad(bone, "castle_front1_%d" % k, v3(a_, ya, z), v3(b_, ya, z), v3(a_, yb_, z), v3(b_, yb_, z), 0.14, "wall_wood", v3(0, 0, 1),
             u_dir=v3(1, 0, 0), stretch=False, back="dark_wood")
    beam(bone, "castle_front1_cornice", v3(-w - 0.1, y1top - 0.12, z + 0.08), v3(w + 0.1, y1top - 0.12, z + 0.08), 0.24, "cornice", width=0.3,
         u_dir=v3(1, 0, 0))
    z = cs.L2_Z
    w = cs.castle2_x(z)
    ax, sill, spring, crown = cs.ARCH
    door = ci.DOORS[ci.TERRACE_DOOR][1]
    xs = sorted(set([-w, door[0], door[1], -ax - 0.3, ax + 0.3, w] + list(np.linspace(-ax, ax, 9))))
    ys = sorted(set([cs.L2_Y, door[3], sill, spring, y2top] + list(np.linspace(spring, crown + 0.3, 6))))
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            x0, x1, ya, yb_ = xs[i], xs[i + 1], ys[j], ys[j + 1]
            xm, ym = (x0 + x1) / 2, (ya + yb_) / 2
            in_arch = abs(xm) < ax and sill < ym < crown and (ym < spring or (xm / ax) ** 2 + ((ym - spring) / (crown - spring)) ** 2 <= 1.0)
            in_door = door[0] < xm < door[1] and ym < door[3]
            if in_arch or in_door:
                continue
            quad(bone, "cockpit_front_%d_%d" % (i, j), v3(x0, ya, z), v3(x1, ya, z), v3(x0, yb_, z), v3(x1, yb_, z), 0.14, "wall_wood",
                 v3(0, 0, 1), u_dir=v3(1, 0, 0), stretch=False, back="dark_wood")
    beam(bone, "castle_front2_cornice", v3(-w - 0.12, y2top - 0.12, z + 0.1), v3(w + 0.12, y2top - 0.12, z + 0.1), 0.26, "cornice", width=0.34,
         u_dir=v3(1, 0, 0))
    add_cube(bone, "cockpit_arch_frame", v3(0, (sill + crown) / 2, z + 0.02), EYE, (2 * ax, crown - sill, 0.06),
             {"all": None, "+3": "window_arch", "-3": "window_arch"}, stretch=True, u_dir=v3(-1, 0, 0), v_dir=v3(0, -1, 0))
    pts = [v3(math.cos(a) * (ax + 0.14), spring + math.sin(a) * (crown - spring + 0.14), z + 0.1) for a in np.linspace(0, math.pi, 17)]
    polyline(detail, "cockpit_arch_moulding", pts, 0.22, "gold", sides=4)
    for sx in (-1, 1):
        beam(detail, "cockpit_arch_jamb_%d" % (sx > 0), v3(sx * (ax + 0.14), sill, z + 0.1), v3(sx * (ax + 0.14), spring, z + 0.1), 0.22, "gold")
    beam(detail, "cockpit_arch_sill", v3(-ax - 0.25, sill - 0.05, z + 0.12), v3(ax + 0.25, sill - 0.05, z + 0.12), 0.14, "gold", width=0.28)
    disc(detail, "cockpit_arch_keystone", v3(0, crown + 0.2, z + 0.14), (0, 0, 1), 0.28, 0.12, "gold", sides=8)
    # ---- the roof deck: a balustrade round its edge, the green coaming with gilded scrolls, its cap, the crest, volutes,
    # brass portholes with blue jewels at the coaming's front corners, pennant poles
    rail2 = []
    for x, zz in half2:
        if zz < cs.L2_Z - 0.3:
            rail2.append((max(0.0, x - 0.22), zz))
    for side, sn in SIDES:
        gl.balustrade(roof_bone, "roof_rail_" + sn, [v3(side * x, y2top, zz) for x, zz in rail2 if x > 0.05 or zz < -23], h=0.55, step=0.42,
                      turned=True, newel=8)
    zc_front = cs.L2_Z - 1.4
    c3 = lambda zz: max(0.0, (cs.plan_hw(zz) - cs.CASTLE_INSET[1] - 0.75) * cs.stern_round(zz, cs.STERN2_Z + 0.75, cs.STERN2_Z + 4.6))  # noqa: E731
    half3 = plan_outline(c3, cs.STERN2_Z + 0.75, cs.STERN2_Z + 4.6, zc_front, step=1.0)
    ycap = cs.ROOF_Y[1]
    for side, sn in SIDES:
        plan_wall(roof_bone, "coaming", half3, side, y2top, ycap, "coaming", back="dark_wood")
        plan_beam(roof_bone, "coaming_cap", half3, side, ycap, 0.08, 0.14, 0.3, "cornice")
        plan_beam(detail, "coaming_foot", half3, side, y2top + 0.06, 0.05, 0.1, 0.12, "trim_gold")
    w3 = c3(zc_front)
    quad(roof_bone, "coaming_front", v3(-w3, y2top, zc_front), v3(w3, y2top, zc_front), v3(-w3, ycap, zc_front), v3(w3, ycap, zc_front), 0.14,
         "coaming", v3(0, 0, 1), u_dir=v3(1, 0, 0), stretch=False, back="dark_wood")
    beam(roof_bone, "coaming_front_cap", v3(-w3 - 0.08, ycap, zc_front + 0.08), v3(w3 + 0.08, ycap, zc_front + 0.08), 0.14, "cornice", width=0.3)
    plan_fill(roof_bone, "coaming_top", half3, ycap + 0.07, "roof_green", (0, 1, 0))
    # the crest: a gilded cartouche with a blue jewel between two volutes, on the coaming's front
    cz = zc_front + 0.12
    disc(detail, "crest_plate", v3(0, ycap + 0.5, cz), (0, 0, 1), 0.5, 0.14, "gold", sides=10)
    disc(lights, "glow_crest_gem", v3(0, ycap + 0.5, cz + 0.08), (0, 0, 1), 0.24, 0.08, "gem", sides=8)
    tube(detail, "crest_finial", v3(0, ycap + 0.95, cz), v3(0, cs.CREST_Y, cz), 0.14, "gold", sides=6)
    disc(detail, "crest_ball", v3(0, cs.CREST_Y, cz), (0, 1, 0), 0.16, 0.2, "gold", sides=8)
    for sx in (-1, 1):
        base = v3(sx * 0.55, ycap + 0.05, cz)
        pts = [base + v3(sx * (0.15 + 0.85 * t), 0.15 + 0.95 * math.sin(math.pi * t) * (1 - 0.3 * t), 0) for t in np.linspace(0, 1, 8)]
        end = pts[-1]
        pts += [end + v3(sx * 0.32 * (1 - a / 9) * math.cos(a), 0.32 * (1 - a / 9) * math.sin(a) - 0.0, 0) for a in np.linspace(0.6, 8.0, 12)]
        polyline(detail, "crest_volute_%d" % (sx > 0), pts, 0.16, "gold", sides=6)
        # brass portholes with a blue jewel at the coaming's front corners
        pc = v3(sx * (w3 - 0.45), (y2top + ycap) / 2 + 0.05, zc_front + 0.1)
        disc(detail, "roof_porthole_%d" % (sx > 0), pc, (0, 0, 1), 0.36, 0.14, "brass", sides=12)
        disc(lights, "glow_roof_porthole_gem_%d" % (sx > 0), pc + v3(0, 0, 0.08), (0, 0, 1), 0.2, 0.06, "gem", sides=8)
        # the aft volutes over the stern
        base = v3(sx * 0.9, ycap + 0.05, cs.STERN2_Z + 1.4)
        pts = [base + v3(sx * 0.2 * t, 0.5 * math.sin(math.pi * t / 2), -0.6 * t) for t in np.linspace(0, 1, 5)]
        end = pts[-1]
        pts += [end + v3(0, 0.28 * (1 - a / 9) * math.sin(a), -0.28 * (1 - a / 9) * math.cos(a)) for a in np.linspace(0.6, 8.0, 10)]
        polyline(detail, "aft_volute_%d" % (sx > 0), pts, 0.14, "gold", sides=6)
    # the ensign spar aft over the overhang, a rope stay down to the stern
    s0 = v3(0, ycap - 0.2, cs.STERN2_Z + 1.2)
    s1 = s0 + v3(0, math.sin(math.radians(15)), -math.cos(math.radians(15))) * 4.6
    beam(roof_bone, "ensign_spar", s0, s1, 0.28, "dark_wood", width=0.28, extend=0.05, u_dir=s1 - s0)
    for k, t in enumerate((0.45, 0.75)):
        q = s0 + (s1 - s0) * t
        beam(detail, "ensign_spar_band_%d" % k, q - norm(s1 - s0) * 0.06, q + norm(s1 - s0) * 0.06, 0.36, "brass", width=0.36)
    disc(detail, "ensign_spar_cap", s1, norm(s1 - s0), 0.2, 0.2, "gold", sides=8)
    rope(detail, "ensign_stay", s1, v3(0, cs.L1_TOP + 0.2, cs.STERN2_Z + 0.02), d=0.07, region="rope_dark", sag=0.25)
    return s1


# ================================================================ engines
NACELLE_ST = [cs.NACELLE[2], -24.5, -24.35, -24.1, -23.8, -23.45, -23.05, -22.6, -22.35, -22.1, -21.8, -21.0, -20.0, -19.0, -18.0, -17.0, -16.2,
              -15.4, -15.0, -14.6, -14.3, -14.0, -13.3, -12.6, -12.25, -11.85, -11.4, -10.95, -10.5, -10.1, -9.8, cs.NACELLE[3] - 0.02]


def body_of_revolution(bone, name, axis_pt, rfn, z0, z1, n_st, naz, region_fn, phase=0.0, skip=None):
    """Panels of a body of revolution about a line parallel to z through axis_pt (x, y), radius rfn(z); n_st: a count of
    even stations or the list of their z. skip(z, azimuth): leave that panel out (hidden in the hull)."""
    zs = list(np.linspace(z0, z1, n_st + 1)) if isinstance(n_st, int) else sorted(n_st)
    ax, ay = axis_pt
    for i in range(len(zs) - 1):
        za, zb = zs[i], zs[i + 1]
        ra, rb = rfn(za), rfn(zb)
        for j in range(naz):
            a0, a1 = phase + 2 * math.pi * j / naz, phase + 2 * math.pi * (j + 1) / naz
            am = (a0 + a1) / 2
            if skip is not None and skip((za + zb) / 2, am):
                continue
            pa0 = v3(ax + math.sin(a0) * ra, ay + math.cos(a0) * ra, za)
            pb0 = v3(ax + math.sin(a0) * rb, ay + math.cos(a0) * rb, zb)
            pa1 = v3(ax + math.sin(a1) * ra, ay + math.cos(a1) * ra, za)
            pb1 = v3(ax + math.sin(a1) * rb, ay + math.cos(a1) * rb, zb)
            out = v3(math.sin(am), math.cos(am), (ra - rb) / max(1e-3, zb - za) * 0.5)
            reg = region_fn((za + zb) / 2, am)
            quad(bone, "%s_%d_%d" % (name, i, j), pa0, pb0, pa1, pb1, 0.14, reg, norm(out), u_dir=v3(0, 0, 1),
                 stretch=reg.startswith("plate_"), overlap=(1.03, 1.05))


def nacelle_pt(side, z, az_deg, out=0.0):
    """Point of a nacelle's surface at z and azimuth (degrees from the top, + outboard), pushed out by `out`."""
    x, y = cs.NACELLE[0], cs.NACELLE[1]
    a = math.radians(az_deg)
    r = cs.nacelle_r(z) + out
    return v3(side * (x + math.sin(a) * r), y + math.cos(a) * r, z)


def nacelles(bone, detail, lights, root):
    """The ornate engines on the aft sides, against the hull: a winged brass helmet with a spike, a louvered grille, the
    big drum of warm brass round the glowing crystal eye (a toothed bezel), a cowl of green-bronze petals, copper tanks
    and pipes, fairing plates to the hull, a domed and ribbed iron cap with a small fan at the tail."""
    x, y, z0, z1, r = cs.NACELLE
    rn, zb, zd = cs.NACELLE_NOSE
    za, zc, rc = cs.NACELLE_TAIL
    for side, sn in SIDES:
        cx = side * x

        def reg(z, a):
            if z < zc:
                return "cap_iron"
            if z > z1 - rn * 0.75:
                return "brass"           # the helmet's dome: polished, no seams converging on its nose
            if z > zb:
                return "plate_helmet"
            return "plate_bronze" if math.cos(a) < -0.55 or z < za - 0.6 else "plate_brass"

        body_of_revolution(bone, "nacelle_%s" % sn, (cx, y), cs.nacelle_r, z0, z1, NACELLE_ST, 24,
                           reg, skip=lambda z, a, side=side: cs.inside_hull(cx + math.sin(a) * cs.nacelle_r(z), y + math.cos(a) * cs.nacelle_r(z), z, 0.3))
        # gilded bands: the helmet's rim, the neck, the drum's edges
        for k, z in enumerate((z1 - rn + 0.1, zb + 0.05, zd - 0.1)):
            ring(detail, "nacelle_band_%s%d" % (sn, k), v3(cx, y, z), (0, 0, 1), cs.nacelle_r(z) + 0.1, 0.24, "gold", n=24)
        # the helmet: a spike, a crest along its top, rivets
        tube(bone, "nacelle_spike_%s" % sn, v3(cx, y, z1 - 0.1), v3(cx, y, z1 + 1.1), 0.36, "brass", sides=6)
        tube(bone, "nacelle_spike_tip_%s" % sn, v3(cx, y, z1 + 1.1), v3(cx, y, z1 + 1.55), 0.16, "gold", sides=6)
        crest = [nacelle_pt(side, z, 0.0, 0.12) for z in np.linspace(z1 - 0.25, zb, 7)]
        for k in range(len(crest) - 1):
            beam(detail, "nacelle_crest_%s%d" % (sn, k), crest[k], crest[k + 1], 0.32, "gold", width=0.12, up=v3(0, 1, 0), extend=0.04)
        for k in range(8):
            a = 45.0 * k + 22.5
            p = nacelle_pt(side, zb + 0.3, a, 0.04)
            disc(detail, "nacelle_rivet_%s%d" % (sn, k), p, norm(p - v3(cx, y, p[2])), 0.1, 0.08, "gold", sides=6)
        # two swept wings of brass feathers on the helmet, fanning back and up: one over the eye, a smaller one on top
        for wing, (az, tilt, lens, z_root) in enumerate(((52.0, 28.0, (4.4, 4.0, 3.5, 2.9, 2.3), -11.4), (8.0, 62.0, (3.4, 3.0, 2.5), -11.0))):
            root_pt = nacelle_pt(side, z_root, az, -0.1)
            o = norm(v3(side * math.cos(math.radians(tilt)), math.sin(math.radians(tilt)), 0))
            nw = norm(np.cross(v3(0, 0, -1), o))
            for k, L in enumerate(lens):
                th = math.radians(6 + 13 * k)
                d = norm(v3(0, 0, -1) * math.cos(th) + o * math.sin(th))
                wv = norm(np.cross(nw, d))
                c = root_pt + d * (L / 2) + nw * (0.05 * k)
                add_cube(bone, "nacelle_feather_%s%d_%d" % (sn, wing, k), c, np.column_stack([d, wv, np.cross(d, wv)]),
                         (L, 0.72 - 0.05 * k, 0.08), {"all": "brass", "+3": "feather", "-3": "feather"}, u_dir=d)
            disc(detail, "nacelle_wing_boss_%s%d" % (sn, wing), root_pt + nw * 0.12, nw, 0.38, 0.16, "gold", sides=8)
        # the louvered grille ahead of and under the eye: sloped brass slats stepping down the drum
        for k in range(6):
            az = 112.0 + 9.0 * k
            zz0, zz1 = -13.9 - 0.25 * k, -17.0 - 0.35 * k
            p0, p1 = nacelle_pt(side, zz0, az, 0.12), nacelle_pt(side, zz1, az, 0.12)
            n = norm(nacelle_pt(side, (zz0 + zz1) / 2, az, 1.0) - nacelle_pt(side, (zz0 + zz1) / 2, az))
            t = norm(p1 - p0)
            w = norm(np.cross(n, t))
            up = n * 0.55 + w * 0.83
            up = norm(up - np.dot(up, t) * t)
            R = np.column_stack([t, up, np.cross(t, up)])
            add_cube(detail, "nacelle_louver_%s%d" % (sn, k), (p0 + p1) / 2 + n * 0.08, R, (np.linalg.norm(p1 - p0), 0.06, 0.55),
                     {"all": "brass", "+3": "louver", "-3": "louver"}, u_dir=t)
        # the crystal eye on the outer face: a heavy brass bezel ringed with teeth, a riveted gilded ring, spokes, the
        # glowing core
        ze, re = cs.NACELLE_EYE
        n = v3(side, 0, 0)
        c = v3(cx + side * (r + 0.02), y, ze)
        disc(bone, "nacelle_eye_bezel_%s" % sn, c, n, re + 0.8, 0.34, "brass", sides=24)
        teeth = 22
        e1, e2 = v3(0, 1, 0), v3(0, 0, 1)
        for k in range(teeth):
            a = 2 * math.pi * (k + 0.5) / teeth
            d = e1 * math.cos(a) + e2 * math.sin(a)
            t = np.cross(n, d)
            add_cube(detail, "nacelle_eye_tooth_%s%d" % (sn, k), c + d * (re + 0.95), np.column_stack([d, t, n]), (0.36, 0.34, 0.3), "brass")
        ring(detail, "nacelle_eye_ring_%s" % sn, c + n * 0.18, n, re + 0.42, 0.24, "gold", n=24)
        ring(detail, "nacelle_eye_ring_in_%s" % sn, c + n * 0.2, n, re + 0.08, 0.14, "bronze", n=20)
        add_cube(lights, "glow_nacelle_eye_%s" % sn, c + n * 0.22, ga.face_frame(n), (2 * re, 2 * re, 0.02),
                 {"all": None, "+3": "crystal_core", "-3": "crystal_core"}, stretch=True)
        for k in range(12):
            a = 2 * math.pi * k / 12
            d = e1 * math.cos(a) + e2 * math.sin(a)
            disc(detail, "nacelle_eye_rivet_%s%d" % (sn, k), c + n * 0.3 + d * (re + 0.42), n, 0.07, 0.06, "brass", sides=6)
        # the turbine cowl: pointed green-bronze petals round the top and the outer side of the drum's taper, laid back
        for k in range(6):
            az = 2.0 + 30.0 * k
            p0, p1 = nacelle_pt(side, -19.9, az, 0.08), nacelle_pt(side, -23.3, az, 0.35)
            nn = norm(nacelle_pt(side, -21.6, az, 1.0) - nacelle_pt(side, -21.6, az))
            t = norm(p1 - p0)
            wd = norm(np.cross(nn, t))
            wd = wd * math.cos(0.75) + nn * math.sin(0.75)            # half open, like a flower's petals
            wd = norm(wd - np.dot(wd, t) * t)
            add_cube(bone, "nacelle_petal_%s%d" % (sn, k), (p0 + p1) / 2 + nn * 0.25, np.column_stack([wd, t, np.cross(wd, t)]),
                     (0.9, np.linalg.norm(p1 - p0), 0.06), {"all": None, "+3": "petal", "-3": "petal"}, stretch=True, u_dir=wd, v_dir=-t)
        # two brass exhaust stacks raked back on the drum's top, copper collars
        for k, (az, zz) in enumerate(((-12.0, -19.4), (14.0, -20.3))):
            b0 = nacelle_pt(side, zz, az, -0.2)
            b1 = b0 + v3(side * 0.15, 1.7, -0.5)
            tube(bone, "nacelle_stack_%s%d" % (sn, k), b0, b1, 0.42, "brass", sides=8)
            tube(detail, "nacelle_stack_lip_%s%d" % (sn, k), b1 - v3(0, 0.12, 0), b1 + v3(0, 0.08, 0), 0.56, "copper", sides=8)
        # the iron cap: raised ribs, a brass ring at its foot, a spinning finial at its point (bone rotor_*: the propeller)
        for k in range(6):
            az = 60.0 * k + 30.0
            pts = [nacelle_pt(side, z, az, 0.03) for z in np.linspace(zc - 0.05, z0 + 0.45, 5)]
            for j in range(len(pts) - 1):
                beam(detail, "nacelle_cap_rib_%s%d_%d" % (sn, k, j), pts[j], pts[j + 1], 0.08, "cap_iron", width=0.1,
                     up=norm(pts[j] - v3(cx, y, pts[j][2])), extend=0.03)
        # glowing blue crystals set in brass cups round the drum's aft edge and the helmet (the sheet's blue sparks)
        for k, (az, zz, d_out, d_z) in enumerate(((35.0, -20.1, 0.8, -0.6), (105.0, -20.1, 0.8, -0.6), (175.0, -20.1, 0.8, -0.6),
                                                   (300.0, -20.1, 0.8, -0.6), (70.0, -11.6, 0.7, 0.7), (150.0, -11.6, 0.7, 0.7))):
            p = nacelle_pt(side, zz, az, 0.0)
            nn = norm(nacelle_pt(side, zz, az, 1.0) - p)
            disc(detail, "nacelle_crystal_cup_%s%d" % (sn, k), p + nn * 0.08, nn, 0.3, 0.16, "brass", sides=8)
            crystal(lights, "nacelle_crystal_%s%d" % (sn, k), p + nn * 0.1, nn * d_out + v3(0, 0, d_z), 0.75, 0.2)
        rc_ = v3(cx, y, z0 + 0.1)
        rb = Bone("rotor_" + sn, origin=tuple(rc_), parent=root)
        tube(rb, "rotor_spike_%s" % sn, rc_, rc_ - v3(0, 0, 0.7), 0.22, "brass", sides=6)
        disc(rb, "rotor_hub_%s" % sn, rc_ - v3(0, 0, 0.1), (0, 0, 1), 0.2, 0.2, "gold", sides=8)
        for k in range(4):
            a = 2 * math.pi * k / 4 + 0.3
            d = v3(math.cos(a), math.sin(a), 0)
            t = np.cross(v3(0, 0, 1), d)
            tw = norm(t * math.cos(0.6) + v3(0, 0, 1) * math.sin(0.6))
            R = np.column_stack([d, tw, np.cross(d, tw)])
            add_cube(rb, "rotor_blade_%s%d" % (sn, k), rc_ - v3(0, 0, 0.25) + d * 0.32, R, (0.42, 0.22, 0.04), "brass")
        # the elevator fin: a brass feather on the cowl's upper outer side (bone flap_*: tilts with the climb)
        fp = nacelle_pt(side, -21.2, 48.0, 0.1)
        fb = Bone("flap_" + sn, origin=tuple(fp), parent=root)
        d = norm(v3(side * 0.74, 0.67, 0))
        Rf = np.column_stack([d, np.cross(v3(0, 0, 1), d) * (1 if side > 0 else -1), v3(0, 0, 1)])
        Rf[:, 1] = norm(np.cross(Rf[:, 2], Rf[:, 0]))
        add_cube(fb, "nacelle_flap_%s" % sn, fp + d * 0.5 + v3(0, 0, -0.7), Rf, (1.0, 0.08, 1.7), {"all": "brass", "+2": "feather", "-2": "feather"},
                 u_dir=v3(0, 0, -1))
        # copper tanks under the drum, with brass bands and rivets
        for k, tz in enumerate((-15.0, -18.6)):
            p = v3(cx + side * 1.0, y - r + 0.05, tz)
            tube(bone, "nacelle_tank_%s%d" % (sn, k), p + v3(0, 0, 1.45), p - v3(0, 0, 1.45), 1.6, "copper", sides=10)
            disc(bone, "nacelle_tank_end_%s%d" % (sn, k), p + v3(0, 0, 1.5), (0, 0, 1), 0.62, 0.12, "brass", sides=10)
            disc(bone, "nacelle_tank_end2_%s%d" % (sn, k), p - v3(0, 0, 1.5), (0, 0, 1), 0.62, 0.12, "brass", sides=10)
            for e in (-1, 0, 1):
                tube(detail, "nacelle_tank_band_%s%d_%d" % (sn, k, e + 1), p + v3(0, 0, e * 0.95 - 0.07), p + v3(0, 0, e * 0.95 + 0.07), 1.72, "brass",
                     sides=10)
        # copper pipes along the belly, into the hull
        for k, (dx, dy) in enumerate(((0.45, -0.9), (-0.35, -0.95))):
            pts = [v3(cx + side * dx * r, y + dy * r - 0.1, z) for z in (-11.6, -16.8, -21.4)]
            pts = [v3(side * (cs.hull_x(-10.6, y + dy * r + 0.4) - 0.1), y + dy * r + 0.4, -10.6)] + pts
            polyline(detail, "nacelle_pipe_%s%d" % (sn, k), pts, 0.28, "copper", sides=6)
            for j, q in enumerate(pts[1:-1]):
                tube(detail, "nacelle_pipe_fl_%s%d_%d" % (sn, k, j), q - v3(0, 0, 0.06), q + v3(0, 0, 0.06), 0.42, "brass", sides=6)
        # fairing plates bolting the engine to the hull's side (under it, and over it where there is a gap)
        for k, (az, yh) in enumerate(((-150.0, -3.6), (-35.0, 0.6))):
            zz = list(np.linspace(-11.4, -21.6, 9))
            for j in range(len(zz) - 1):
                pa = v3(side * (x - math.sin(math.radians(abs(az))) * cs.nacelle_r(zz[j])), y + math.cos(math.radians(az)) * cs.nacelle_r(zz[j]), zz[j])
                pb = v3(side * (x - math.sin(math.radians(abs(az))) * cs.nacelle_r(zz[j + 1])), y + math.cos(math.radians(az)) * cs.nacelle_r(zz[j + 1]),
                        zz[j + 1])
                ha = v3(side * (cs.hull_x(zz[j], yh) - 0.05), yh, zz[j])
                hb = v3(side * (cs.hull_x(zz[j + 1], yh) - 0.05), yh, zz[j + 1])
                if abs(pa[0]) - abs(ha[0]) < 0.15 and abs(pb[0]) - abs(hb[0]) < 0.15:
                    continue
                nrm = v3(0, -1, 0) if k == 0 else v3(0, 1, 0)
                quad(bone, "nacelle_fairing_%s%d_%d" % (sn, k, j), ha, hb, pa, pb, 0.12, "engine_brass", nrm, u_dir=v3(0, 0, 1), stretch=False)
            beam(detail, "nacelle_fairing_edge_%s%d" % (sn, k), v3(side * (cs.hull_x(-11.4, yh) - 0.02), yh, -11.4),
                 v3(side * (cs.hull_x(-21.6, yh) - 0.02), yh, -21.6), 0.14, "gold", width=0.14)


def stern_medallion(bone, detail, lights, root):
    """The brass gear medallion on the rounded stern (flush): a toothed brass outer ring on a dark-bronze dish, a dark
    ring, a riveted brass ring, a gear turning slowly behind the porthole (bone stern_gear: the engine animation), the
    blue-grey porthole with its glowing heart."""
    my, mz, mr = cs.MEDALLION
    n = v3(0, 0, -1)
    c = v3(0, my, mz)
    disc(bone, "medal_dish", c + v3(0, 0, 0.12), n, mr + 0.05, 0.62, "bronze", sides=28)
    teeth = 26
    e1, e2 = v3(0, 1, 0), v3(1, 0, 0)
    for k in range(teeth):
        a = 2 * math.pi * (k + 0.5) / teeth
        d = e1 * math.cos(a) + e2 * math.sin(a)
        t = np.cross(n, d)
        add_cube(detail, "medal_tooth_%d" % k, c + d * (mr + 0.16) - n * 0.02, np.column_stack([d, t, n]), (0.4, 0.42, 0.44), "brass")
    ring(bone, "medal_rim", c + n * 0.22, n, mr - 0.2, 0.42, "brass", n=28)
    disc(bone, "medal_dark", c + n * 0.2, n, mr - 0.5, 0.12, "iron", sides=24)
    ring(detail, "medal_ring_mid", c + n * 0.3, n, mr - 0.95, 0.3, "engine_brass", n=24)
    for k in range(16):
        a = 2 * math.pi * k / 16
        d = e1 * math.cos(a) + e2 * math.sin(a)
        disc(detail, "medal_rivet_%d" % k, c + n * 0.46 + d * (mr - 0.95), n, 0.09, 0.06, "gold", sides=6)
        if k % 2 == 0:
            disc(detail, "medal_rivet_out_%d" % k, c + n * 0.44 + d * (mr - 0.2), n, 0.11, 0.06, "gold", sides=6)
    gb = Bone("stern_gear", origin=tuple(c + n * 0.34), parent=root)
    gl.gear(gb, "medal_gear", c + n * 0.34, n, 1.55, 0.16, teeth=14, region="brass", spokes=7, rim="bronze")
    add_cube(lights, "glow_medal_glass", c + n * 0.52, ga.face_frame(n), (2.3, 2.3, 0.02), {"all": None, "+3": "medal_glass", "-3": "medal_glass"},
             stretch=True)
    ring(detail, "medal_porthole_rim", c + n * 0.5, n, 1.18, 0.18, "gold", n=20)
    # a gilded strap from the medallion up to the stern's top, a pendant under it
    beam(detail, "medal_strap_up", c + v3(0, mr + 0.3, 0.05), v3(0, cs.sheer_y(cs.STERN_Z) - 0.1, mz - 0.05), 0.3, "gold", width=0.12)
    tube(detail, "medal_pendant", c - v3(0, mr + 0.25, -0.05), c - v3(0, mr + 0.9, -0.05), 0.24, "gold", sides=6)
    disc(lights, "glow_medal_drop", c - v3(0, mr + 1.05, -0.05), (0, 1, 0), 0.2, 0.3, "gem", sides=8)


def prop_pods(bone, detail, lights, root):
    for side, sn in SIDES:
        rp, hub, ax = cs.pod_frame(side)
        rp, hub, ax = v3(*rp), v3(*hub), v3(*ax)
        tube(bone, "pod_body_%s" % sn, rp, hub - ax * 0.4, 2.3, "bronze", sides=10)
        tube(bone, "pod_cap_%s" % sn, rp - ax * 0.3, rp + ax * 0.3, 2.5, "brass", sides=10)
        tube(bone, "pod_nose_%s" % sn, hub - ax * 0.45, hub - ax * 0.05, 1.8, "gold", sides=10)
        for k, t in enumerate((0.35, 0.6, 0.82)):
            p = rp + (hub - rp) * t
            tube(lights, "glow_pod_crystal_band_%s%d" % (sn, k), p - ax * 0.2, p + ax * 0.2, 2.42, "crystal", sides=10)
            tube(detail, "pod_band_%s%d" % (sn, k), p - ax * 0.32, p - ax * 0.21, 2.5, "gold", sides=10)
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
            L = cs.PROP_BLADE
            # a long curved frond bunched round the axis (a closed golden claw): two segments bending outward
            base = hub + ax * 0.2 + d * 0.3
            mid = base + norm(d * 0.42 + ax) * (L * 0.52)
            tip = mid + norm(d * 0.85 + ax) * (L * 0.5)
            t = norm(np.cross(ax, d))
            for j, (p0, p1, w0) in enumerate(((base, mid, 1.0), (mid, tip, 0.8))):
                dd = norm(p1 - p0)
                tw = t * math.cos(0.45) + ax * math.sin(0.45)
                tw = norm(tw - np.dot(tw, dd) * dd)
                Rb = np.column_stack([tw, dd, np.cross(tw, dd)])
                cube = add_cube(pb, "pod_blade_%s%d_%d" % (sn, k, j), (p0 + p1) / 2, Rb, (0.95 * w0, np.linalg.norm(p1 - p0) + 0.06, 0.05),
                                {"all": None, "+3": "blade", "-3": "blade"}, stretch=True, u_dir=tw, v_dir=-dd)
                set_sub(cube, (0.0, 0.5, 1.0, 1.0) if j == 0 else (0.0, 0.0, 1.0, 0.52))


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
    crystal(lights, "bottom_big", c - v3(0, 0.2, 0), (0, -1, 0), py - tip - 0.2, 1.05, sides=6)
    for k, (dx, dz, h, r, tilt) in enumerate(((0, 0, 2.2, 0.8, 0), (1.1, 0.6, 1.6, 0.55, 0.35), (-1.0, 0.7, 1.7, 0.55, 0.35), (0.5, -1.1, 1.5, 0.5, 0.4),
                                              (-0.8, -0.9, 1.4, 0.48, 0.35), (1.5, -0.5, 1.1, 0.4, 0.5), (-1.6, 0.0, 1.2, 0.42, 0.5))):
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
        yt = cs.keel_y(zz) + (0.3 if x == 0 else 1.0)
        top = v3(0.0 if x == 0 else math.copysign(cs.hull_x(zz, yt) - 0.1, x), yt, zz)
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
        crystal(lights, "castle_lamp_%d" % k, v3(x, y - 0.2, zz), (0, 1, 0), 1.4, 0.4)
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
        # the ring lies across the ship (seen edge-on from the side, a cross from above), the crystals point fore and aft
        gl.gear(rb, "pod_%s_gear" % name, p, (0, 0, 1), R, 0.32, teeth=16, region="copper" if big else "brass", spokes=6,
                rim="copper" if big else "brass")
        ring(rb, "pod_%s_ring_in" % name, p, (0, 0, 1), R * 0.62, 0.18, "gold", n=12)
        disc(rb, "pod_%s_disc" % name, p, (0, 0, 1), R * 0.5, 0.36, "engine_plate", sides=12)
        crystal(pb, "pod_%s_core" % name, p - v3(0, 0.55 * R, 0), (0, 1, 0), 1.1 * R, 0.28 * R)
        for s in (1, -1):
            crystal(pb, "pod_%s_side_%d" % (name, s > 0), p + v3(0, 0, s * 0.3), (0, 0, s), 1.05 * R, 0.42)
            tube(pb, "pod_%s_axle_%d" % (name, s > 0), p, p + v3(0, 0, s * 0.45), 0.6, "brass", sides=8)
            for e in (-1, 1):
                crystal(pb, "pod_%s_tip_%d_%d" % (name, s > 0, e > 0), p + v3(e * R * 0.95, 0, s * 0.15), (0, 0, s), 0.45 * R, 0.2)
    # ropes holding the pods
    fp, rpod = v3(*cs.FRONT_POD), v3(*cs.REAR_POD)
    fl, rl = cs.lobe("f"), cs.lobe("r")
    rope(detail, "pod_front_rope_up", fp + v3(0, cs.POD_R, 0), LP("f", fl[3] + fl[6] * 0.75, 180, 0.0), d=0.06, region="rope_dark")
    rope(detail, "pod_front_rope_bow", fp - v3(0, cs.POD_R, 0), v3(0, cs.BEAK[1][1] + 0.1, cs.BEAK[1][0] - 0.2), d=0.06, region="rope_dark", sag=0.3)
    tail = v3(0, rl[2], rl[3] - rl[6])
    beam(bone, "rear_spar", tail + v3(0, 0, 0.6), tail + v3(0, 0, -2.8), 0.22, "dark_wood")
    disc(bone, "rear_spar_cap", tail + v3(0, 0, 0.2), (0, 0, 1), 0.7, 0.3, "gold", sides=10)
    rope(detail, "pod_rear_rope_up", rpod + v3(0, 1.25 * cs.POD_R, 0), tail + v3(0, 0, -2.0), d=0.06, region="rope_dark")
    rope(detail, "pod_rear_rope_down", rpod - v3(0, 1.25 * cs.POD_R, 0), v3(0, cs.ROOF_Y[1] + 0.1, cs.STERN2_Z + 1.6), d=0.06, region="rope_dark",
         sag=0.4)
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
            zt = max(cs.CASTLE_Z + 0.5, min(cs.FORECASTLE_Z + 8.0, z * 1.45 + 1.0))   # the shrouds fan out towards the ends
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
                    q = v3(side * (cs.castle1_x(zt) - 0.15), cs.L1_TOP + 0.05, zt)
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


def pennants(root, tail, ensign):
    """Red pennants: on two poles at the front corners of the roof deck's coaming, at the tail of the aft lobe, on the
    forecastle."""
    pb = Bone("pennants", parent=root)
    zc = cs.L2_Z - 1.4
    for side, sn in SIDES:
        x = side * (cs.castle2_x(zc) - 0.6)
        base = v3(x, cs.L2_TOP, zc - 0.25)
        top = base + v3(0, 3.0, 0)
        tube(pb, "pennant_pole_%s" % sn, base, top, 0.14, "dark_wood", sides=6)
        disc(pb, "pennant_pole_ball_%s" % sn, top + v3(0, 0.08, 0), (0, 1, 0), 0.12, 0.16, "gold", sides=6)
        flag(pb, "pennant_" + sn, top - v3(0, 0.12, 0), 2.6, 0.55)
    flag(pb, "pennant_tail", tail + v3(0, 0.1, -2.7), 2.4, 0.6)
    x, y, z = ci.POSTS[4]
    flag(pb, "pennant_bow", v3(x, 4.6, z), 1.6, 0.4)
    tube(pb, "pennant_bow_pole", v3(x, y, z), v3(x, 4.75, z), 0.12, "dark_wood", sides=6)
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
    "mess": ("in_wall_lounge", "in_floor_lounge", "in_ceil"),
    "cockpit": ("in_stone", "in_floor_capt", "in_ceil"),
    "lounge": ("in_wall_lounge", "in_floor_lounge", "in_ceil"),
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
    c = v3(ex, e0 + 2.3, ez)
    box(eb, "lit_engine_bed", (ex, e0 + 0.3, ez), (3.9, 0.6, 3.8), {"all": "in_rivets", "+2": "in_iron"})
    for sx in (-1, 1):
        box(eb, "lit_engine_foot_%d" % (sx > 0), (ex + sx * 1.0, e0 + 0.9, ez), (0.5, 0.7, 3.2), "in_iron")
    tube(eb, "lit_engine_drum", c - v3(0, 0, 1.6), c + v3(0, 0, 1.4), 3.5, "in_boiler", sides=14)
    for k, dz in enumerate((-1.5, -0.4, 0.6, 1.3)):
        tube(eb, "lit_engine_drum_band_%d" % k, c + v3(0, 0, dz - 0.08), c + v3(0, 0, dz + 0.08), 3.66, "in_gold", sides=14)
    disc(eb, "lit_engine_bezel", c + v3(0, 0, 1.45), (0, 0, 1), 1.5, 0.3, "in_brass_pol", sides=18)
    add_cube(eb, "glow_engine_core", c + v3(0, 0, 1.62), EYE, (2.3, 2.3, 0.02), {"all": None, "+3": "in_core", "-3": "in_core"}, stretch=True)
    ring(eb, "lit_engine_bezel_ring", c + v3(0, 0, 1.64), (0, 0, 1), 1.28, 0.16, "in_gold", n=18)
    tube(eb, "lit_engine_dome", c + v3(0, 1.45, -0.2), c + v3(0, 2.3, -0.2), 1.9, "in_brass_pol", sides=12)
    tube(eb, "lit_engine_dome_top", c + v3(0, 2.3, -0.2), c + v3(0, 2.7, -0.2), 1.1, "in_gold", sides=12)
    tube(eb, "lit_engine_stack", c + v3(0, 2.7, -0.2), v3(ex, ci.CEIL_LO - 0.02, ez - 0.2), 0.6, "in_copper", sides=8)
    for s in (1, -1):
        gb = Bone("engine_gear_%d" % (s > 0), origin=tuple(c + v3(s * 1.85, 0.2, -0.3)), parent=root)
        lf.gear(gb, "lit_engine_gear_%d" % (s > 0), c + v3(s * 1.85, 0.2, -0.3), (1, 0, 0), 1.25, 0.18, teeth=18, region="in_brass", spokes=6)
        for k, dz in enumerate((-0.7, 0.5)):
            pb = Bone("engine_piston_%d_%d" % (s > 0, k), origin=tuple(c + v3(s * 1.05, 1.5, dz)), parent=eb)
            tube(eb, "lit_engine_cyl_%d_%d" % (s > 0, k), c + v3(s * 1.05, 1.05, dz), c + v3(s * 1.05, 1.75, dz), 0.5, "in_copper", sides=8)
            tube(pb, "lit_engine_rod_%d_%d" % (s > 0, k), c + v3(s * 1.05, 1.75, dz), c + v3(s * 1.05, 2.5, dz), 0.12, "in_iron", sides=4)
            box(pb, "lit_engine_crosshead_%d_%d" % (s > 0, k), c + v3(s * 1.05, 2.55, dz), (0.28, 0.14, 0.28), "in_brass")
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
    centre = (0.0, cs.CY, cs.MAST_Z)   # the balloon breathes about the cluster's centre
    bal = Bone("balloon", origin=centre, parent=root)
    strp = Bone("straps", origin=centre, parent=root)
    detail = Bone("detail", parent=root)
    gems = Bone("gems", origin=centre, parent=root)
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
    turret(turret_b, detail, lights, lanterns_b)
    ensign = castle(castle_b, detail, lights, roof_b, lanterns_b)
    nacelles(eng, detail, lights, root)
    stern_medallion(eng, detail, lights, root)
    prop_pods(eng, detail, lights, root)
    tail = crystals(crys, lights, detail, root, lanterns_b)
    rigging(rig, girdle)
    pennants(root, tail, ensign)
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
    tracks = [(find(root, n), spin) for n in ("rotor_p", "rotor_s", "pod_prop_p", "pod_prop_s")]
    anims.append(animation("propeller", 2.0, "loop", tracks))
    # the gear behind the stern medallion's porthole turns slowly (seven-fold: a seventh of a turn per loop)
    tracks = [(find(root, "stern_gear"), [rot_kf(t, (0, 0, 360.0 / 7 * t / 2.0)) for t in (0.0, 0.5, 1.0, 1.5, 2.0)])]
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
    # the balloon breathes: its lobes, straps and jewels swell a little and bob
    for name in ("balloon", "straps", "gems"):
        b = find(root, name)
        tracks.append((b, [kf("scale", t, (1 + 0.006 * (1 - math.cos(w * t)),) * 3) for t, _ in _loop_keys(3.0, 8, lambda t: 0)] +
                       [kf("position", t, (0, 16 * 0.05 * math.sin(w * t), 0)) for t, _ in _loop_keys(3.0, 8, lambda t: 0)]))
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
        stem = os.path.splitext(out_paths[0])[0]       # preview: the textures next to the preview model
        tex_path, in_path = stem + "_tex.png", stem + "_tex_in.png"
    ct.make_texture(tex_path)
    ct.make_interior_texture(in_path, in_path if write_resources else os.path.splitext(in_path)[0] + "_base.png")
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
