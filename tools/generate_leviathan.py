#!/usr/bin/env python3
"""Generates the Sky Leviathan (sky_leviathan) Blockbench model, its texture, its item icon, its interior
grid and its furniture file.

Usage:  python3 tools/generate_leviathan.py

Outputs:
  blockbench/sky_leviathan.bbmodel                                            (editable, texture embedded)
  src/main/resources/assets/medievalships/models/entity/sky_leviathan.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/sky_leviathan.png
  src/main/resources/assets/medievalships/textures/item/sky_leviathan.png
  src/main/resources/assets/medievalships/interiors/sky_leviathan.grid         (collisions, ladders, doors)
  src/main/resources/assets/medievalships/interiors/sky_leviathan_decor.json   (mod furniture, seats)

Reference: the Minecraft sheet "Le Léviathan des Cieux" (side, front, back, top, perspective, details
and six interior views; measurements in docs/LEVIATHAN_PLAN.md). A huge egg-shaped balloon, a little
flattened, of aged turquoise strips, with big brown wooden panels on its sides, four wooden hoops of
stacked blocks that follow its curve, dark bands converging on a spiked iron nose fitting carrying a
gear emblem and a spike; black cloth swags draped along its sides under chains, tattered black
banners and lanterns hanging under it; an observation deck with a flag mast and the pirate flag on
top; at the tail a hub with a spike carrying black bat-wing fins (ribs, scalloped trailing edges,
three holes near the tip): a dorsal fin, two upper fins, two side fins and a lower fin. Under it, on
chains, ropes and rope nets, a dark pirate ship with a long beakhead and bowsprit, a gear wheel at the
head, a forecastle, a stern castle with leaded windows, portholes, black wales, a central tower with
a big gear up to the balloon, black sails hanging from the rigging and a ventral bat-wing fin under
the keel.

The balloon is a body built from tilted panels between 31 sections of 48 sides (no staircase); the
ship's hull follows leviathan_shape.hull_x the same way. The decks, the walls, floors and ceilings of
the rooms are drawn on the boundaries of the interior grid (tools/leviathan_interior.py): what is drawn
is what collides. Room surfaces are named "lit*" (lit by the airship's own lamps).

Bones used by the mod (keep their names when editing in Blockbench):
  helm_wheel, rudder, fin_dorsal, fin_lower (steer)   fin_side_p, fin_side_s (elevator)
  flag, flag_tip (flag_wave)   lantern_* (lantern_sway)   pennants_*, black_sail_* (streamer_wave)
  tower_gear, engine_* (engine: played with the signed speed)   door_<k> (door k: 0 = closed, 1 = open)
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
import leviathan_shape as ls  # noqa: E402
import leviathan_interior as li  # noqa: E402
import leviathan_texture as lt  # noqa: E402
import leviathan_decor as ld  # noqa: E402
import nautilus_furniture as nf  # noqa: E402
import leviathan_furniture as lf  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/sky_leviathan/%d" % _uuid_counter[0]))


gg.new_uuid = new_uuid
gn.new_uuid = new_uuid
REGIONS = dict(lt.REGIONS)
REGIONS.update({"prop": lt.REGIONS["wood"], "hull_light": lt.REGIONS["wood"], "plank_light": lt.REGIONS["wood"],
                "silver": lt.REGIONS["steel"]})
gn.REGIONS = {k: (0,) + r for k, r in REGIONS.items()}
gn.REGIONS.update({k: (1,) + r for k, r in lt.REGIONS_IN.items()})   # the rooms and their furniture: second texture
gn.REGIONS["globe"] = (1,) + lt.REGIONS_IN["in_globe"]                 # the Nautilus's globe, with this texture's map
gn.SIZE = lt.SIZE

v3, norm, Bone, add_cube, beam = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam
rx, ry, rz = gg.rx, gg.ry, gg.rz
tube, disc, ring, prism, polyline, catmull, bezier = ga.tube, ga.disc, ga.ring, ga.prism, ga.polyline, ga.catmull, ga.bezier
EYE = np.eye(3)
SIDES = ((1, "p"), (-1, "s"))
BY = ls.BALLOON_Y
NAZ = 48


# ================================================================ helpers
def P(z, az, out=0.0):
    return v3(*ls.balloon_point(z, az, out))


def wall_frame(n):
    """Axes (right, up, normal) of a part on a wall whose outward normal is n (made horizontal)."""
    nh = norm(v3(n[0], 0, n[2]))
    return np.column_stack([np.cross(v3(0, 1, 0), nh), v3(0, 1, 0), nh])


def set_sub(cube, sub):
    for f in cube.faces.values():
        if f is not None:
            f["sub"] = sub


def quad(bone, name, p00, p10, p01, p11, th, region, normal, sub=None, u_dir=None, v_dir=None, side=None, back=None,
         overlap=(1.0, 1.0), stretch=True, density=1.0):
    """A thin plate through four corners (p00 at (u0, v0), p10 at (u1, v0), p01 at (u0, v1), p11 at (u1, v1));
    its outer face (+3) on the surface, facing `normal`. sub: the part (u0, v0, u1, v1) of the region drawn on it
    (texture u along p00 -> p10 as given by u_dir, v by v_dir)."""
    p00, p10, p01, p11 = (np.asarray(p, dtype=float) for p in (p00, p10, p01, p11))
    U = ((p10 + p11) - (p00 + p01)) / 2
    L = np.linalg.norm(U)
    if L < 1e-4:
        return None
    u = U / L
    V = ((p01 + p11) - (p00 + p10)) / 2
    Vp = V - np.dot(V, u) * u
    W = np.linalg.norm(Vp)
    if W < 1e-4:
        return None
    v = Vp / W
    n = np.cross(u, v)
    if np.dot(n, normal) < 0:
        u, n = -u, -n
    c = (p00 + p10 + p01 + p11) / 4 - n * th / 2
    regions = {"all": side, "+3": region, "-3": back if back is not None else region}
    cube = add_cube(bone, name, c, np.column_stack([u, v, n]), (L * overlap[0] + 0.01, W * overlap[1] + 0.01, th), regions,
                    stretch=stretch, u_dir=u_dir, v_dir=v_dir, density=density)
    if sub is not None:
        set_sub(cube, sub)
    return cube


def box(bone, name, c, size, region, R=EYE, **kw):
    return add_cube(bone, name, v3(*c), R, size, region, **kw)


def sag_points(p0, p1, sag, n, down=(0, -1, 0)):
    p0, p1, d = v3(*p0), v3(*p1), v3(*down)
    return [p0 + (p1 - p0) * (k / n) + d * sag * 4 * (k / n) * (1 - k / n) for k in range(n + 1)]


def outside_balloon(p, margin=0.3):
    """The point, pushed out of the balloon (along its section's radius) if it lies inside it."""
    p = v3(*p)
    w, h = ls.balloon_hw(p[2]) + margin, ls.balloon_hh(p[2]) + margin
    if w <= margin + 0.05:
        return p
    dx, dy = p[0], p[1] - BY
    k = (dx / w) ** 2 + (dy / h) ** 2
    if k >= 1.0 or k < 1e-9:
        return p
    f = 1.0 / math.sqrt(k)
    return v3(dx * f, BY + dy * f, p[2])


def rope(bone, name, p0, p1, d=0.1, sag=0.0, n=4, region="rope", clear=False):
    pts = sag_points(p0, p1, sag, n) if sag else [v3(*p0), v3(*p1)]
    if clear:
        pts = [outside_balloon(p) for p in pts]
    polyline(bone, name, pts, d, region, sides=4, extend=d * 0.4)
    return pts


def chain(bone, name, p0, p1, link=0.24, th=0.055, region="chain"):
    """Chain of alternating links between two points."""
    p0, p1 = v3(*p0), v3(*p1)
    d = p1 - p0
    L = np.linalg.norm(d)
    u = d / L
    e1 = norm(np.cross(u, v3(0, 1, 0) if abs(u[1]) < 0.9 else v3(1, 0, 0)))
    e2 = np.cross(u, e1)
    n = max(1, int(L / link))
    for k in range(n):
        c = p0 + u * (L * (k + 0.5) / n)
        side = e1 if k % 2 == 0 else e2
        add_cube(bone, "%s_%d" % (name, k), c, np.column_stack([u, side, np.cross(u, side)]), (L / n + 0.06, th * 2.4, th), region)


def hanging_lantern(bone, name, hook, drop=0.6, w=0.34, h=0.48, chained=True, sway=True):
    """A ship's lantern hanging on a chain from `hook`; in its own bone (lantern_*, swung by lantern_sway)."""
    hook = v3(*hook)
    lb = Bone("lantern_" + name, origin=tuple(hook), parent=bone) if sway else bone
    body = hook - v3(0, drop + h / 2 + 0.12, 0)
    if chained:
        chain(lb, name + "_chain", hook, body + v3(0, h / 2 + 0.16, 0), link=0.16, th=0.035)
    add_cube(lb, name, body, EYE, (w, h, w), {"all": "lantern", "+2": "iron", "-2": "iron"}, stretch=True)
    return lb


def gear(bone, name, c, axis, r, th, teeth=12, region="gear_iron", spokes=6, rim="iron"):
    """A gear wheel: a rim, square teeth, spokes, a hub."""
    axis = norm(v3(*axis))
    c = v3(*c)
    ring(bone, name + "_rim", c, axis, r * 0.86, th, rim, n=max(12, teeth), round_=False)
    e1 = norm(np.cross(axis, v3(0, 1, 0) if abs(axis[1]) < 0.9 else v3(1, 0, 0)))
    e2 = np.cross(axis, e1)
    for k in range(teeth):
        a = 2 * math.pi * (k + 0.5) / teeth
        d = e1 * math.cos(a) + e2 * math.sin(a)
        t = np.cross(axis, d)
        add_cube(bone, "%s_tooth_%d" % (name, k), c + d * (r * 0.97), np.column_stack([d, t, axis]),
                 (r * 0.22, 2 * math.pi * r / teeth * 0.5, th * 0.9), region)
    for k in range(spokes):
        a = 2 * math.pi * k / spokes
        d = e1 * math.cos(a) + e2 * math.sin(a)
        beam(bone, "%s_spoke_%d" % (name, k), c + d * r * 0.18, c + d * r * 0.82, th * 0.8, region, width=r * 0.14, up=axis)
    disc(bone, name + "_hub", c, axis, r * 0.24, th * 1.4, "brass", sides=8)


def ship_wheel(bone, name, c, axis, r=0.6, region="wood"):
    """A ship's wheel: a rim, eight spokes going on into handles, a brass hub."""
    axis = norm(v3(*axis))
    c = v3(*c)
    ring(bone, name + "_rim", c, axis, r, 0.1, region, n=16, round_=True)
    ring(bone, name + "_rim_in", c, axis, r * 0.55, 0.06, region, n=12, round_=True)
    e1 = norm(np.cross(axis, v3(0, 1, 0) if abs(axis[1]) < 0.9 else v3(1, 0, 0)))
    e2 = np.cross(axis, e1)
    for k in range(8):
        a = 2 * math.pi * k / 8
        d = e1 * math.cos(a) + e2 * math.sin(a)
        tube(bone, "%s_spoke_%d" % (name, k), c, c + d * (r + 0.05), 0.06, region)
        tube(bone, "%s_handle_%d" % (name, k), c + d * (r + 0.05), c + d * (r + 0.3), 0.08, region)
    disc(bone, name + "_hub", c, axis, 0.12, 0.16, "brass")


def balustrade(bone, name, pts, h=1.0, step=0.6, post="dark_wood", rail="rail", lit=False):
    """Posts and two rails along a polyline of base points."""
    pre = "lit_" if lit else ""
    pts = [v3(*p) for p in pts]
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        L = np.linalg.norm(b - a)
        if L < 1e-3:
            continue
        beam(bone, "%s%s_rail_%d" % (pre, name, k), a + v3(0, h, 0), b + v3(0, h, 0), 0.12, rail, width=0.16, extend=0.06)
        beam(bone, "%s%s_mid_%d" % (pre, name, k), a + v3(0, h * 0.45, 0), b + v3(0, h * 0.45, 0), 0.07, rail, extend=0.03)
        n = max(1, int(round(L / step)))
        for j in range(n + (1 if k == len(pts) - 2 else 0)):
            p = a + (b - a) * j / n
            tube(bone, "%s%s_post_%d_%d" % (pre, name, k, j), p, p + v3(0, h, 0), 0.1, post, sides=4)


def arrowhead(bone, name, base, d, length, width, region="iron"):
    """A flat diamond spear head (two crossed plates) from base along d."""
    d = norm(v3(*d))
    base = v3(*base)
    e1 = norm(np.cross(d, v3(0, 1, 0) if abs(d[1]) < 0.9 else v3(1, 0, 0)))
    e2 = np.cross(d, e1)
    for k, e in enumerate((e1, e2)):
        for j in range(3):
            t0, t1 = j / 3, (j + 1) / 3
            wmid = width * (1 - abs((t0 + t1) / 2 - 0.3) / 0.7) if (t0 + t1) / 2 > 0.3 else width * (0.4 + 0.6 * (t0 + t1) / 2 / 0.3)
            add_cube(bone, "%s_%d_%d" % (name, k, j), base + d * length * (t0 + t1) / 2, np.column_stack([d, e, np.cross(d, e)]),
                     (length / 3 + 0.02, max(0.06, wmid), 0.05), region)


# ================================================================ balloon
def balloon_stations():
    s = [-1.0, -0.996, -0.985, -0.965, -0.935, -0.895, -0.845, -0.785, -0.715, -0.64, -0.55, -0.45, -0.34, -0.22, -0.1, 0.0,
         0.1, 0.22, 0.34, 0.45, 0.55, 0.64, 0.72, 0.79, 0.85, 0.9, 0.94, 0.968, 0.986, 0.996, 1.0]
    zs = [ls.BALLOON_Z + (ls.BALLOON_FRONT if t >= 0 else ls.BALLOON_REAR) * t for t in s]
    keep = list(ls.WOOD_Z) + [ls.NOSE_COLLAR_Z]
    zs = [z for z in zs if all(abs(z - k) > 0.7 for k in keep)] + keep
    return sorted(zs)


def in_wood(zm, am):
    return ls.WOOD_Z[1] <= zm <= ls.WOOD_Z[0] and ls.WOOD_AZ[0] - 2.5 <= abs(am) <= ls.WOOD_AZ[1] + 2.5


def balloon(bone, hoops, detail):
    zs = balloon_stations()
    for i in range(len(zs) - 1):
        za, zb = zs[i], zs[i + 1]
        zm = (za + zb) / 2
        for j in range(NAZ):
            a0, a1 = 360.0 * j / NAZ - 180.0, 360.0 * (j + 1) / NAZ - 180.0
            am = (a0 + a1) / 2
            wood = in_wood(zm, am)
            if zm > ls.NOSE_Z - 0.35 or zm < ls.TAIL_Z + 0.9:
                region = "iron"
            elif wood:
                region = "wood_panel"
            elif abs(am) > 135 or zm > ls.NOSE_COLLAR_Z or zm > ls.HOOPS_Z[0] + 0.3 or zm < ls.HOOPS_Z[3] - 0.3:
                region = "plate_dark"
            else:
                region = "plate"
            out = 0.07 if wood else 0.0
            outward = v3(math.sin(math.radians(am)), math.cos(math.radians(am)), 0)
            quad(bone, "gore_%d_%d" % (i, j), P(za, a0, out), P(zb, a0, out), P(za, a1, out), P(zb, a1, out), 0.14, region, outward,
                 back="plate_in", u_dir=v3(0, 0, 1), v_dir=None, stretch=region == "iron", overlap=(1.02, 1.04))
    # dark wooden bands along the balloon converging on the nose (and on the tail), not over the wood panels
    for az in (0, 45, 90, 135, 180, -45, -90, -135):
        for i in range(len(zs) - 1):
            za, zb = zs[i], zs[i + 1]
            zm = (za + zb) / 2
            if zm > ls.NOSE_COLLAR_Z or zm < ls.TAIL_Z + 0.6:
                continue
            front = zm > ls.HOOPS_Z[0] or zm < ls.HOOPS_Z[3]
            if not front and az % 90 != 0:
                continue
            if in_wood(zm, az) or (az == 0 and ls.TOP_DECK_Z[0] - 0.5 < zm < ls.TOP_DECK_Z[1] + 0.5):
                continue
            ra, rb = max(0.4, ls.balloon_hw(za)), max(0.4, ls.balloon_hw(zb))
            hw_ = 0.42 if az % 90 == 0 else 0.26
            da, db = math.degrees(hw_ / ra), math.degrees(hw_ / rb)
            outward = v3(math.sin(math.radians(az)), math.cos(math.radians(az)), 0)
            quad(detail, "band_%d_%d" % (az, i), P(za, az - da, 0.1), P(zb, az - db, 0.1), P(za, az + da, 0.1), P(zb, az + db, 0.1), 0.09,
                 "band", outward, side="dark_wood", u_dir=v3(0, 0, 1))
    # black iron straps along the upper and lower edges of the wood panels, with round rivet heads
    zw = [z for z in zs if ls.WOOD_Z[1] - 1e-6 <= z <= ls.WOOD_Z[0] + 1e-6]
    for az0 in ls.WOOD_AZ:
        for s in (1, -1):
            az = s * az0
            for i in range(len(zw) - 1):
                za, zb = zw[i], zw[i + 1]
                outward = norm(v3(*P((za + zb) / 2, az, 1.0)) - v3(*P((za + zb) / 2, az)))
                quad(bone, "strap_%d_%d" % (int(az), i), P(za, az - 1.3, 0.12), P(zb, az - 1.3, 0.12), P(za, az + 1.3, 0.12),
                     P(zb, az + 1.3, 0.12), 0.08, "strap", outward, side="iron", u_dir=v3(0, 0, 1))
                for k in range(3):
                    z = za + (zb - za) * (k + 0.5) / 3
                    q = P(z, az, 0.2)
                    nrm = norm(q - P(z, az))
                    disc(detail, "rivet_%d_%d_%d" % (int(az), i, k), q, nrm, 0.07, 0.06, "iron", sides=6)
    # hoops: a band of wood following the section, crowned with stacked blocks that jut out in turn
    for h, z in enumerate(ls.HOOPS_Z):
        for j in range(NAZ):
            a0, a1 = 360.0 * j / NAZ, 360.0 * (j + 1) / NAZ
            am = (a0 + a1) / 2
            p0, p1 = P(z, a0, 0.3), P(z, a1, 0.3)
            nrm = norm(P(z, am, 1.0) - P(z, am))
            beam(hoops, "hoop_%d_%d" % (h, j), p0, p1, 0.6, "hoop", width=1.15, up=nrm, extend=0.03)
            t = norm(p1 - p0)
            R = np.column_stack([t, nrm, np.cross(t, nrm)])
            jut = 0.42 if j % 2 == 0 else 0.2
            wz = 1.45 if j % 2 == 0 else 1.25
            add_cube(hoops, "hoop_%d_%d_block" % (h, j), P(z, am, 0.6 + jut / 2), R, (np.linalg.norm(p1 - p0) * 0.92, jut + 0.2, wz),
                     {"all": "hoop", "+1": "hoop_end", "-1": "hoop_end"})
    # the nose collar: a black iron ring with rivets
    z = ls.NOSE_COLLAR_Z
    for j in range(NAZ):
        a0, a1 = 360.0 * j / NAZ, 360.0 * (j + 1) / NAZ
        am = (a0 + a1) / 2
        nrm = norm(P(z, am, 1.0) - P(z, am))
        beam(hoops, "collar_%d" % j, P(z, a0, 0.15), P(z, a1, 0.15), 0.3, "iron", width=0.55, up=nrm, extend=0.03)
        if j % 2 == 0:
            disc(detail, "collar_rivet_%d" % j, P(z, am, 0.32), nrm, 0.07, 0.06, "brass", sides=6)


def nose(bone):
    """The spiked nose fitting: an iron stem out of the cap, the gear emblem with radial spikes, the spike."""
    z0 = ls.NOSE_Z - 0.3
    gz = ls.NOSE_GEAR_Z
    c = v3(0, BY, gz)
    tube(bone, "nose_stem", (0, BY, z0), (0, BY, gz - 0.1), 0.9, "iron", sides=8)
    tube(bone, "nose_stem_ring", (0, BY, z0 + 0.4), (0, BY, z0 + 0.6), 1.15, "brass", sides=8)
    r = ls.NOSE_GEAR_R
    gear(bone, "nose_gear", c, (0, 0, 1), r, 0.3, teeth=12, region="steel", spokes=6, rim="steel")
    gear(bone, "nose_gear_side", c + v3(0, 0, 0.3), (1, 0, 0), r * 0.8, 0.22, teeth=10, region="steel", spokes=4, rim="steel")
    for k in range(6):
        a = 2 * math.pi * (k + 0.5) / 6
        d = v3(0, math.sin(a), math.cos(a))
        tube(bone, "nose_side_spike_%d" % k, c + v3(0, 0, 0.3) + d * r * 0.75, c + v3(0, 0, 0.3) + d * (r * 0.8 + 0.9), 0.12, "steel", sides=4)
    # radial spikes in the gear's plane between the teeth (the "snowflake" of the reference) and
    # four spikes raked forwards
    for k in range(8):
        a = 2 * math.pi * (k + 0.25) / 8
        d = v3(math.cos(a), math.sin(a), 0)
        tube(bone, "nose_spike_%d" % k, c + d * r * 0.9, c + d * (r + 0.8), 0.14, "steel", sides=4)
        tube(bone, "nose_spike_tip_%d" % k, c + d * (r + 0.8), c + d * (r + 1.15), 0.07, "steel", sides=4)
    for k in range(4):
        a = 2 * math.pi * (k + 0.5) / 4
        d = v3(math.cos(a), math.sin(a), 0)
        tube(bone, "nose_rake_%d" % k, c + d * 0.5, c + d * 1.2 + v3(0, 0, 1.1), 0.12, "iron", sides=4)
    # the spike: a long iron rod with gold rings, a spear head
    tip = ls.NOSE_SPIKE_Z
    tube(bone, "nose_rod", c, (0, BY, tip - 0.9), 0.26, "iron", sides=6)
    for k, z in enumerate((gz + 0.8, gz + 2.0, tip - 1.4)):
        tube(bone, "nose_rod_ring_%d" % k, (0, BY, z - 0.08), (0, BY, z + 0.08), 0.38, "gold", sides=8)
    arrowhead(bone, "nose_head", (0, BY, tip - 0.95), (0, 0, 1), 1.0, 0.7)


def tail(bone):
    """The hub behind the balloon: wooden blocks in iron bands, the emblem plate, the tail spike."""
    z0, z1 = ls.HUB_Z
    r = ls.HUB_R
    tube(bone, "hub", (0, BY, z0 + 0.3), (0, BY, z1), 2 * r, "hoop", sides=12)
    for k, z in enumerate((z0 + 0.1, (z0 + z1) / 2, z1 + 0.15)):
        tube(bone, "hub_band_%d" % k, (0, BY, z - 0.12), (0, BY, z + 0.12), 2 * r + 0.18, "iron", sides=12)
    add_cube(bone, "hub_emblem", v3(0, BY, z1 - 0.04), EYE, (1.6, 1.6, 0.06), {"all": None, "+3": "emblem", "-3": "emblem"}, stretch=True)
    tube(bone, "tail_rod", (0, BY, z1), (0, BY, ls.TAIL_SPIKE_Z + 0.9), 0.24, "iron", sides=6)
    tube(bone, "tail_rod_ring", (0, BY, z1 - 0.8), (0, BY, z1 - 0.6), 0.36, "gold", sides=8)
    arrowhead(bone, "tail_head", (0, BY, ls.TAIL_SPIKE_Z + 0.95), (0, 0, -1), 1.0, 0.65)


# ================================================================ fins
def fin(root, frame, name, region, root_u, camber=0.25, holes=True, keel=False):
    """A bat-wing fin; keel=True: the ventral fin, its root kept under the hull's bottom (never up into the hold)."""
    o, c, s, n, lp, lq = frame
    o, c, s, n = v3(*o), v3(*c), v3(*s), v3(*n)
    origin = o + c * lp * root_u * 0.5
    fb = Bone(name, origin=tuple(origin), parent=root)
    poly = ls.fin_outline(root_u)

    def F(u, v):
        bend = camber * math.sin(math.pi * min(1.0, u)) * v ** 1.5
        p = o + c * u * lp + s * v * lq + n * bend
        if keel:
            p = v3(p[0], min(p[1], ls.keel_y(p[2]) + 0.12), p[2])
        return p
    nu, nv = 10, 10
    for i in range(nu):
        for j in range(nv):
            u0, u1, v0, v1 = i / nu, (i + 1) / nu, j / nv, (j + 1) / nv
            samples = [(u0 + (u1 - u0) * a, v0 + (v1 - v0) * b) for a in (0.02, 0.5, 0.98) for b in (0.02, 0.5, 0.98)]
            if not any(ls.point_in_poly(a, b, poly) for a, b in samples):
                continue
            quad(fb, "%s_web_%d_%d" % (name, i, j), F(u0, v0), F(u1, v0), F(u0, v1), F(u1, v1), 0.04, region, n,
                 sub=(u0, 1 - v1, u1, 1 - v0), u_dir=c, v_dir=-s)
    # ribs from the root to the tip and to the rib tips, the leading-edge spar, the root plate
    for k, (a, b) in enumerate(ls.fin_ribs(root_u)):
        pts = [F(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) + n * 0.03 for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
        polyline(fb, "%s_rib_%d" % (name, k), pts, 0.13 if k else 0.17, "iron", sides=4, extend=0.04)
    lead = [ls._bezier2((0.0, 0.0), (0.06, 0.78), ls.FIN_TIP, j / 8) for j in range(9)]
    polyline(fb, name + "_spar", [F(u, v) + n * 0.02 for u, v in lead], 0.22, "iron", sides=6, extend=0.05)
    beam(fb, name + "_root", F(0, 0.02), F(root_u, 0.02), 0.32, "iron", width=0.3, up=s, extend=0.1)
    disc(fb, name + "_hinge", F(0.02, 0.03), n, 0.22, 0.4, "brass", sides=8)
    if holes:
        for k, (hu, hv) in enumerate(ls.fin_holes()):
            q = F(hu, hv)
            ring(fb, "%s_hole_%d" % (name, k), q, n, ls.FIN_HOLE_R * lq * 0.95, 0.06, "iron", n=8, round_=False)
    return fb


def fins(root):
    out = {}
    for f in ls.FINS:
        out[f[0]] = fin(root, ls.fin_frame(f), f[0], "fin", ls.FIN_ROOT_U, camber=0.3 if f[0] != "fin_dorsal" else 0.15)
    out["fin_keel"] = fin(root, ls.keel_fin_frame(), "fin_keel", "fin_keel", ls.KEEL_FIN_ROOT_U, camber=0.0, holes=False, keel=True)
    # the fins' roots on the hub: iron brackets
    for f in ls.FINS[1:]:
        o, c, s, n, lp, lq = ls.fin_frame(f)
        a = math.radians(f[1])
        rad = v3(math.sin(a), math.cos(a), 0)
        p0 = v3(0, BY, f[2] - 0.3) + rad * (ls.HUB_R - 0.1)
        beam(root, f[0] + "_bracket", p0, v3(*o) + v3(*c) * lp * ls.FIN_ROOT_U * 0.5, 0.25, "iron", width=0.5, up=v3(*n))
    return out


# ================================================================ top deck
def flag(parent, name, root_pt, w, h, region="flag", n=3):
    """Flag in two bones (flag, flag_tip), each half of n strips following a soft wave."""
    root_pt = v3(*root_pt)
    fb = Bone(name, origin=tuple(root_pt), parent=parent)
    ft = Bone(name + "_tip", origin=tuple(root_pt + v3(0, 0, -w / 2)), parent=fb)
    amp = min(0.18, 0.07 * w)

    def Pf(s):
        return root_pt + v3(amp * math.sin(2 * math.pi * s) * (0.35 + s), 0, -w * s)
    for half, bone in enumerate((fb, ft)):
        for k in range(n):
            s0, s1 = (half + k / n) / 2, (half + (k + 1) / n) / 2
            a, b = Pf(s0), Pf(s1)
            d = norm(b - a)
            axes = np.column_stack([np.cross(v3(0, 1, 0), d), v3(0, 1, 0), d])
            cube = add_cube(bone, "%s_%s%d" % (name, "ab"[half], k), (a + b) / 2 + v3(0, -h / 2, 0), axes,
                            (0.03, h, np.linalg.norm(b - a) + 0.015), {"all": None, "+1": region, "-1": region},
                            stretch=True, u_dir=v3(0, 0, -1), v_dir=v3(0, -1, 0))
            for f in cube.faces.values():
                if f is not None:
                    f["sub"] = (s0, 0, s1, 1)
    return fb


def top_deck(bone, root, g):
    y = ls.TOP_DECK_Y
    z0, z1 = ls.TOP_DECK_Z
    # the planking, on the grid cells (what is walked on)
    grid_floor(bone, g, y, "deck", "top_deck", lit=False)
    # a dark skirt from the deck's edge down to the balloon, and a beam along the edge
    perim = deck_perimeter(48)
    for k in range(len(perim) - 1):
        (xa, za), (xb, zb) = perim[k], perim[k + 1]
        ba = deck_skirt_bottom(xa, za)
        bb = deck_skirt_bottom(xb, zb)
        mid = v3((xa + xb) / 2, y, (za + zb) / 2)
        outward = norm(v3(mid[0], 0, (mid[2] - (z0 + z1) / 2) * 0.3))
        quad(bone, "skirt_%d" % k, v3(xa, ba, za), v3(xb, bb, zb), v3(xa, y, za), v3(xb, y, zb), 0.12, "band", outward,
             u_dir=v3(xb - xa, 0, zb - za), v_dir=v3(0, -1, 0), stretch=False)
        beam(bone, "deck_edge_%d" % k, v3(xa, y - 0.15, za), v3(xb, y - 0.15, zb), 0.3, "dark_wood", width=0.3, extend=0.08)
    # the railing round the deck, on the grid's rail cells
    rail_pts = [(x * (1 - 0.25 / max(0.5, abs(x))) if abs(x) > 0.3 else x, y, z) for x, z in deck_perimeter(40, inset=0.25)]
    balustrade(bone, "top_rail", rail_pts, h=0.95, step=0.7)
    # the flag mast with its gilded crown, the pirate flag, the stays
    mz = ls.MAST_Z
    tube(bone, "mast", (0, y, mz), (0, ls.MAST_TOP - 0.6, mz), 0.36, "dark_wood", sides=8)
    for k, yy in enumerate((y + 0.3, y + 3.0, ls.MAST_TOP - 2.2)):
        tube(bone, "mast_band_%d" % k, (0, yy - 0.1, mz), (0, yy + 0.1, mz), 0.46, "iron", sides=8)
    top = v3(0, ls.MAST_TOP - 0.6, mz)
    disc(bone, "mast_cap", top, (0, 1, 0), 0.32, 0.16, "gold", sides=8)
    for k in range(4):
        a = math.pi / 2 * k + math.pi / 4
        d = v3(math.cos(a), 0, math.sin(a))
        polyline(bone, "mast_crown_%d" % k, [top, top + d * 0.3 + v3(0, 0.3, 0), top + d * 0.18 + v3(0, 0.6, 0)], 0.08, "gold", sides=4)
    disc(bone, "mast_finial", top + v3(0, 0.62, 0), (0, 1, 0), 0.1, 0.18, "gold", sides=8)
    tube(bone, "yardarm", top - v3(0, 1.5, 0) + v3(0, 0, 0.0), top - v3(0, 1.5, 1.6), 0.12, "dark_wood", sides=4)
    flag(bone, "flag", top - v3(0, 0.75, 0.15), 3.6, 1.8)
    for k, (zz, xx) in enumerate(((z1 - 0.6, 0.0), (z0 + 0.8, 1.4), (z0 + 0.8, -1.4))):
        rope(bone, "stay_%d" % k, top - v3(0, 0.2, 0), (xx, y + 0.9, zz), d=0.07, sag=0.15)
    # a rope from the mast to the dorsal fin's tip
    tip = v3(*ls.fin_point(ls.fin_frame(ls.FINS[0]), *ls.FIN_TIP))
    rope(bone, "stay_fin", top - v3(0, 2.6, 0), tip, d=0.08, sag=0.6)
    # the great wheel standing on the deck (an ornament, facing the sides) and a capstan
    wz = -4.6
    for e in (1, -1):
        tube(bone, "wheel_post_%d" % (e > 0), (e * 0.22, y, wz), (e * 0.22, y + 1.55, wz), 0.16, "dark_wood", sides=4)
    ship_wheel(bone, "deck_wheel", (0, y + 1.75, wz), (1, 0, 0), r=0.95)
    cz = 4.5
    tube(bone, "capstan", (0, y, cz), (0, y + 0.8, cz), 0.6, "dark_wood", sides=8)
    disc(bone, "capstan_head", (0, y + 0.85, cz), (0, 1, 0), 0.42, 0.14, "iron")
    for k in range(4):
        a = math.pi / 2 * k
        tube(bone, "capstan_bar_%d" % k, (0, y + 0.7, cz), (math.cos(a) * 0.95, y + 0.7, cz + math.sin(a) * 0.95), 0.07, "wood", sides=4)
    # a little davit with a block, beside the capstan (the "crane" of the reference)
    tube(bone, "davit", (1.6, y, cz + 0.6), (1.6, y + 1.6, cz + 0.6), 0.14, "iron", sides=4)
    polyline(bone, "davit_arm", [v3(1.6, y + 1.6, cz + 0.6), v3(1.6, y + 1.9, cz + 1.0), v3(1.6, y + 1.8, cz + 1.5)], 0.1, "iron", sides=4)
    box(bone, "davit_block", (1.6, y + 1.55, cz + 1.5), (0.14, 0.22, 0.18), "dark_wood")
    # the hatch's frame round the shaft
    hx, (hz0, hz1) = ls.SHAFT_X, ls.SHAFT_Z
    for k, (a, b) in enumerate((((-hx, hz0), (hx, hz0)), ((hx, hz0), (hx, hz1)), ((hx, hz1), (-hx, hz1)), ((-hx, hz1), (-hx, hz0)))):
        beam(bone, "hatch_coaming_%d" % k, v3(a[0], y + 0.06, a[1]), v3(b[0], y + 0.06, b[1]), 0.12, "dark_wood", width=0.14, extend=0.07)


def deck_perimeter(n, inset=0.0):
    z0, z1 = ls.TOP_DECK_Z
    zc, hl = (z0 + z1) / 2, (z1 - z0) / 2
    pts = []
    for k in range(n + 1):
        t = 2 * math.pi * k / n
        c, s = math.cos(t), math.sin(t)
        e = 2.0 / ls.TOP_DECK_N
        x = (ls.TOP_DECK_HALF - inset) * math.copysign(abs(s) ** e, s)
        z = zc + (hl - inset) * math.copysign(abs(c) ** e, c)
        pts.append((x, z))
    return pts


def deck_skirt_bottom(x, z):
    w, h = ls.balloon_hw(z), ls.balloon_hh(z)
    if w <= abs(x) + 0.05:
        return ls.BALLOON_Y
    return ls.BALLOON_Y + h * math.sqrt(1 - (x / w) ** 2) - 0.25


# ================================================================ rigging on the balloon
def drape_az(f, top=True):
    """Azimuth of the top / bottom edge of a black swag at the fraction f of its length."""
    return 94.0 + 20.0 * math.sin(math.pi * f) if top else 107.0 + 33.0 * math.sin(math.pi * f)


SWAG_Z = (13.6, 6.3, -7.7, -16.6)


def rigging(bone, pennants_root, lanterns_root):
    for side, sn in SIDES:
        # the black cloth swags draped along the side, between their knots
        for k in range(len(SWAG_Z) - 1):
            za, zb = SWAG_Z[k], SWAG_Z[k + 1]
            nu, nv = 10, 3
            for i in range(nu):
                for j in range(nv):
                    f0, f1 = i / nu, (i + 1) / nu
                    pt = []
                    for f, t in ((f0, j / nv), (f1, j / nv), (f0, (j + 1) / nv), (f1, (j + 1) / nv)):
                        z = za + (zb - za) * f
                        az = drape_az(f) + (drape_az(f, False) - drape_az(f)) * t
                        bulge = 0.3 + 0.35 * math.sin(math.pi * f) * math.sin(math.pi * t) + 0.08 * math.sin(f * 9 * math.pi) * t
                        pt.append(P(z, side * az, bulge))
                    nrm = norm(pt[0] - v3(0, BY, pt[0][2]))
                    quad(bone, "swag_%s%d_%d_%d" % (sn, k, i, j), pt[0], pt[1], pt[2], pt[3], 0.05, "cloth", nrm,
                         u_dir=v3(0, -1, 0), stretch=False)
            # the chain along the top of the swag, the knot
            pts = [P(za + (zb - za) * f, side * (drape_az(f) - 2), 0.42) for f in np.linspace(0, 1, 7)]
            for i in range(len(pts) - 1):
                chain(bone, "swag_chain_%s%d_%d" % (sn, k, i), pts[i], pts[i + 1], link=0.2, th=0.05)
        for k, z in enumerate(SWAG_Z):
            q = P(z, side * 94, 0.45)
            nrm = norm(q - v3(0, BY, z))
            disc(bone, "swag_knot_%s%d" % (sn, k), q, nrm, 0.3, 0.2, "iron", sides=8)
            # the tail of cloth hanging from the knot
            for j in range(4):
                a0, a1 = 96 + 9 * j, 96 + 9 * (j + 1)
                quad(bone, "swag_tail_%s%d_%d" % (sn, k, j), P(z - 0.35, side * a0, 0.5), P(z + 0.35, side * a0, 0.5), P(z - 0.3, side * a1, 0.55),
                     P(z + 0.3, side * a1, 0.55), 0.05, "cloth", nrm, stretch=False)
        # the upper chain garland along the side: from the hoop to posts and on to the rear hoop
        anchors = [ls.HOOPS_Z[1], 6.3, -2.0, -11.9, ls.HOOPS_Z[2]]
        for k in range(len(anchors) - 1):
            za, zb = anchors[k], anchors[k + 1]
            pts = [P(za + (zb - za) * f, side * (54 + 9 * math.sin(math.pi * f)), 0.35) for f in np.linspace(0, 1, 9)]
            polyline(bone, "garland_%s%d" % (sn, k), pts, 0.16, "rope", sides=4, extend=0.05)
        for k, z in enumerate((6.3, -11.9)):
            pts = [P(z, side * a, 0.38) for a in np.linspace(56, 94, 6)]
            for i in range(len(pts) - 1):
                chain(bone, "drop_chain_%s%d_%d" % (sn, k, i), pts[i], pts[i + 1], link=0.22, th=0.07, region="steel")
            disc(bone, "garland_ring_%s%d" % (sn, k), P(z, side * 54, 0.38), norm(P(z, side * 54, 1) - P(z, side * 54)), 0.16, 0.1, "brass")
        # tattered black banners on ropes under the nose, the front hoops and the rear hoop
        for k, (pa, pb, depth, sag) in enumerate((
                ((ls.NOSE_Z - 0.6, 128), (ls.HOOPS_Z[0] - 1.2, 160), 2.3, 0.5),
                ((ls.HOOPS_Z[0] - 2.2, 165), (ls.HOOPS_Z[1] - 2.5, 172), 2.6, 0.6),
                ((ls.HOOPS_Z[3] + 4.8, 160), (ls.HOOPS_Z[3] - 0.6, 150), 1.9, 0.4))):
            a = P(pa[0], side * pa[1], 0.5)
            b = P(pb[0], side * pb[1], 0.5)
            pb_ = Bone("pennants_%s%d" % (sn, k), origin=tuple(a), parent=pennants_root)
            pts = rope(pb_, "banner_rope_%s%d" % (sn, k), a, b, d=0.08, sag=sag, n=8, clear=True)
            for i in range(len(pts) - 1):
                t0, t1 = pts[i], pts[i + 1]
                d = norm(t1 - t0)
                nrm = norm(np.cross(d, v3(0, -1, 0)))
                if nrm[0] * side < 0:
                    nrm = -nrm
                quad(pb_, "banner_%s%d_%d" % (sn, k, i), t0 - v3(0, 0.05, 0), t1 - v3(0, 0.05, 0), t0 - v3(0, depth, 0), t1 - v3(0, depth, 0),
                     0.03, "banner", nrm, sub=((i % 4) / 4, 0, (i % 4 + 1) / 4, 1), u_dir=d, v_dir=v3(0, -1, 0))
        # small pennants on strings from under the balloon to the top of the tower
        for k, (za, zt) in enumerate(((ls.HOOPS_Z[1] - 0.5, ls.TOWER_Z[1]), (ls.HOOPS_Z[2] + 0.5, ls.TOWER_Z[0]))):
            a = P(za, side * 168, 0.3)
            b = v3(side * ls.TOWER_X, 7.6, zt)
            pb_ = Bone("pennants_%s%d" % (sn, k + 3), origin=tuple(a), parent=pennants_root)
            pts = rope(pb_, "pennant_rope_%s%d" % (sn, k), a, b, d=0.05, sag=0.9, n=10, clear=True)
            for i in range(1, len(pts) - 1, 1):
                t0 = pts[i]
                d = norm(pts[i + 1] - pts[i - 1])
                nrm = norm(np.cross(d, v3(0, -1, 0)))
                quad(pb_, "pennant_%s%d_%d" % (sn, k, i), t0 - d * 0.2, t0 + d * 0.2, t0 - d * 0.2 - v3(0, 0.75, 0), t0 + d * 0.2 - v3(0, 0.75, 0),
                     0.03, "pennant", nrm, u_dir=d, v_dir=v3(0, -1, 0))
        # lanterns hanging under the balloon (two under the front, one at the tail) and from the nose
        for k, (z, az, drop) in enumerate(((19.6, 150, 1.0), (17.8, 158, 1.4), (-24.2, 140, 0.7))):
            hook = P(z, side * az, 0.2)
            hanging_lantern(lanterns_root, "balloon_%s%d" % (sn, k), hook, drop=drop)
    hanging_lantern(lanterns_root, "nose", v3(0, BY - 1.0, ls.NOSE_Z + 1.5), drop=1.6)
    # lanterns hanging from the ends of the front hoops, on the flanks (the front view)
    for side, sn in SIDES:
        for k, (z, az, drop) in enumerate(((ls.HOOPS_Z[1], 100, 1.2), (ls.HOOPS_Z[1], 125, 0.9), (ls.HOOPS_Z[2], 105, 1.0))):
            hanging_lantern(lanterns_root, "flank_%s%d" % (sn, k), P(z, side * az, 0.95), drop=drop)


# ================================================================ the hanging ship's hull
HULL_ST = [-19.8, -19.5, -19.0, -18.3, -17.4, -16.3, -15.0, -13.5, -12.0, -10.5, -9.0, -7.5, -6.0, -4.5, -3.0, -1.5, 0.0, 1.5, 3.0, 4.5,
           6.0, 7.5, 9.0, 10.3, 11.5, 12.6, 13.5, 14.3, 14.9, 15.4, 15.8, 16.2, 16.6, 17.0, 17.4, 17.8, 18.1, 18.35, 18.55, 18.6]
ETA = [0.0, 0.035, 0.08, 0.14, 0.22, 0.31, 0.41, 0.52, 0.64, 0.76, 0.88, 1.0]
UPPER = [0.0, 0.25, 0.5, 0.75, 1.0]   # from the waist sheer up to the hull's sheer (castles)


def hull_section(z, side):
    k = ls.keel_y(z)
    pts = []
    for e in ETA:
        y = k + e * (ls.SHEER_WAIST - k)
        pts.append(v3(side * max(0.02, ls.hull_x(z, y)), y, z))
    top = ls.sheer_y(z)
    for t in UPPER[1:]:
        y = ls.SHEER_WAIST + t * (top - ls.SHEER_WAIST)
        pts.append(v3(side * max(0.02, ls.hull_x(z, y)), y, z))
    return pts


def hull_pt(z, y, side, out=0.0):
    x = ls.hull_x(z, y)
    e = 0.05
    dx = (ls.hull_x(z + e, y) - ls.hull_x(z - e, y)) / (2 * e)
    dy = (ls.hull_x(z, y + e) - ls.hull_x(z, y - e)) / (2 * e)
    n = norm(v3(side, -dy, -dx))
    return v3(side * x, y, z) + n * out, n


def hull(bone, detail, lights):
    for side, sn in SIDES:
        for i in range(len(HULL_ST) - 1):
            za, zb = HULL_ST[i], HULL_ST[i + 1]
            A, B = hull_section(za, side), hull_section(zb, side)
            for k in range(len(A) - 1):
                if abs(A[k + 1][1] - A[k][1]) < 0.02 and abs(B[k + 1][1] - B[k][1]) < 0.02:
                    continue
                mid = (A[k] + A[k + 1] + B[k] + B[k + 1]) / 4
                region = "hull_low" if k < 5 else "hull"
                outward = norm(v3(side, -0.6 if k < 4 else 0.0, 0.3 * np.sign(mid[2])))
                quad(bone, "hull_%s%d_%d" % (sn, i, k), A[k], B[k], A[k + 1], B[k + 1], 0.12, region, outward, u_dir=v3(0, 0, 1),
                     stretch=False, back="dark_wood", overlap=(1.03, 1.06))
    # the flat of the bottom between the two sides
    for i in range(len(HULL_ST) - 1):
        za, zb = HULL_ST[i], HULL_ST[i + 1]
        xa, xb = ls.hull_x(za, ls.keel_y(za)), ls.hull_x(zb, ls.keel_y(zb))
        ya, yb = ls.keel_y(za), ls.keel_y(zb)
        quad(bone, "bottom_%d" % i, v3(-xa, ya, za), v3(-xb, yb, zb), v3(xa, ya, za), v3(xb, yb, zb), 0.12, "hull_low", v3(0, -1, 0),
             u_dir=v3(0, 0, 1), stretch=False)
    # the keel and the cutwater curving forward under the beakhead
    # the keel, the stem (raked, along the bottom of the bow) and the cutwater curving forward under the head
    def bow_bottom(z):
        if z <= ls.HULL_BOW_Z:
            return ls.keel_y(z)
        y0, y1 = ls.BOW_RAKE_Y
        return y0 + (y1 - y0) * (z - ls.HULL_BOW_Z) / ls.BOW_RAKE
    kpts = [v3(0, ls.keel_y(z) - 0.15, z) for z in np.linspace(ls.HULL_STERN_Z + 3.5, 15.8, 14)]
    kpts += [v3(0, -0.6, 18.4), v3(0, 0.5, 20.0), v3(0, ls.CUTWATER_TIP[1], ls.CUTWATER_TIP[0])]
    sm = catmull(kpts, 2)
    for k in range(len(sm) - 1):
        beam(bone, "keel_%d" % k, sm[k], sm[k + 1], 0.55, "dark_wood", width=0.4, up=v3(1, 0, 0), extend=0.08)
    stem = [v3(0, bow_bottom(z) + 0.1, z) for z in np.linspace(15.0, ls.HULL_BOW_Z + ls.BOW_RAKE, 7)]
    for k in range(len(stem) - 1):
        beam(bone, "stem_%d" % k, stem[k], stem[k + 1], 0.45, "dark_wood", width=0.36, up=v3(1, 0, 0), extend=0.06)
    # a dark knee filling between the cutwater and the stem
    for k in range(len(sm) - 1):
        a, b = sm[k], sm[k + 1]
        if a[2] < 15.0:
            continue
        ta, tb = bow_bottom(min(a[2], ls.HULL_BOW_Z + ls.BOW_RAKE)), bow_bottom(min(b[2], ls.HULL_BOW_Z + ls.BOW_RAKE))
        if a[2] > ls.HULL_BOW_Z + ls.BOW_RAKE:
            ta = max(a[1] + 0.3, ta)
        if b[2] > ls.HULL_BOW_Z + ls.BOW_RAKE:
            tb = max(b[1] + 0.3, tb)
        if ta - a[1] < 0.05 and tb - b[1] < 0.05:
            continue
        quad(bone, "stem_web_%d" % k, a, b, v3(0, max(ta, a[1] + 0.05), a[2]), v3(0, max(tb, b[1] + 0.05), b[2]), 0.3, "dark_wood", v3(1, 0, 0),
             stretch=False)
    # wales: black bands along the hull
    for w_i, (yw, z0, z1) in enumerate(((-0.75, -19.6, 17.1), (-3.15, -18.6, 14.9), (-4.55, -16.8, 12.4), (2.0, -19.6, -6.6), (2.0, 9.6, 18.0))):
        for side, sn in SIDES:
            zz = [z for z in np.linspace(z0, z1, max(4, int((z1 - z0) / 1.2)))]
            for k in range(len(zz) - 1):
                if ls.keel_y(zz[k]) > yw - 0.2 or ls.keel_y(zz[k + 1]) > yw - 0.2 or yw > ls.sheer_y(zz[k]) - 0.2 or yw > ls.sheer_y(zz[k + 1]) - 0.2:
                    continue
                pa, na = hull_pt(zz[k], yw, side, 0.07)
                pb, nb = hull_pt(zz[k + 1], yw, side, 0.07)
                beam(bone, "wale_%d_%s%d" % (w_i, sn, k), pa, pb, 0.34, "wale", width=0.16, up=v3(0, 1, 0), extend=0.08)
    # dark frames (stanchions) on the upper hull, from the main wale up to the sheer, and the engine room's vents
    for side, sn in SIDES:
        for k, z in enumerate(np.arange(-19.2, 15.0, 1.6)):
            y0, y1 = -0.6, ls.sheer_y(z) - 0.05
            if y1 - y0 < 0.6:
                continue
            pts = [hull_pt(z, y, side, 0.05)[0] for y in np.linspace(y0, y1, 4)]
            polyline(detail, "frame_%s%d" % (sn, k), pts, 0.16, "wale", sides=4, extend=0.02)
        for k, z in enumerate((-13.0, -12.2)):
            p, n = hull_pt(z, -1.0, side, 0.0)
            tube(detail, "vent_%s%d" % (sn, k), p, p + n * 0.3, 0.3, "copper", sides=8)
            tube(detail, "vent_mouth_%s%d" % (sn, k), p + n * 0.3, p + n * 0.38, 0.42, "brass", sides=8)
    # cap rail along the sheer of the hull
    for side, sn in SIDES:
        zz = list(np.linspace(ls.HULL_STERN_Z + 0.1, ls.HULL_BOW_Z + ls.BOW_RAKE - 0.15, 76))
        for k in range(len(zz) - 1):
            ya, yb = ls.sheer_y(zz[k]), ls.sheer_y(zz[k + 1])
            pa = v3(side * (ls.hull_x(zz[k], ya) - 0.15), ya + 0.06, zz[k])
            pb = v3(side * (ls.hull_x(zz[k + 1], yb) - 0.15), yb + 0.06, zz[k + 1])
            beam(bone, "cap_%s%d" % (sn, k), pa, pb, 0.14, "rail", width=0.42, extend=0.04)
    # the inner side of the waist bulwark (seen from the main deck)
    for side, sn in SIDES:
        zz = list(np.linspace(-7.4, 9.0, 23))
        for k in range(len(zz) - 1):
            za, zb = zz[k], zz[k + 1]
            ta, tb = ls.sheer_y(za), ls.sheer_y(zb)
            ya, yb = ls.deck_y(za + 0.01), ls.deck_y(zb - 0.01)
            if ya > 0.1 or yb > 0.1:
                continue
            xa0, xa1 = ls.hull_x(za, 0.0) - ls.SHELL, ls.hull_x(za, ta) - ls.SHELL
            xb0, xb1 = ls.hull_x(zb, 0.0) - ls.SHELL, ls.hull_x(zb, tb) - ls.SHELL
            quad(bone, "bulwark_in_%s%d" % (sn, k), v3(side * xa0, 0.0, za), v3(side * xb0, 0.0, zb), v3(side * xa1, ta, za),
                 v3(side * xb1, tb, zb), 0.08, "hull", v3(-side, 0, 0), u_dir=v3(0, 0, 1), stretch=False)
    # the transom: planks, the stern windows of the captain's bedroom and of the chart room, lanterns
    z = ls.HULL_STERN_Z
    ys = [ls.keel_y(z)] + list(np.linspace(-1.5, ls.sheer_y(z), 8))
    for k in range(len(ys) - 1):
        y0, y1 = ys[k], ys[k + 1]
        x0, x1 = ls.hull_x(z, y0), ls.hull_x(z, y1)
        quad(bone, "transom_%d" % k, v3(-x0, y0, z), v3(x0, y0, z), v3(-x1, y1, z), v3(x1, y1, z), 0.14, "transom", v3(0, 0, -1),
             u_dir=v3(-1, 0, 0), stretch=False)
    for k, (x, y, w, h) in enumerate([(xx, 0.7, 0.75, 1.15) for xx in (-2.4, -1.2, 1.2, 2.4)] + [(xx, 3.6, 0.7, 1.0) for xx in (-1.6, 0.0, 1.6)]):
        add_cube(lights, "glow_stern_window_%d" % k, v3(x, y + h / 2, z - 0.09), EYE, (w, h, 0.04), {"all": None, "+3": "window", "-3": "window"},
                 stretch=True)
        for e in (-1, 1):
            box(detail, "stern_window_frame_%d_%d" % (k, e > 0), (x + e * (w / 2 + 0.06), y + h / 2, z - 0.1), (0.12, h + 0.12, 0.1), "dark_wood")
        box(detail, "stern_window_sill_%d" % k, (x, y - 0.05, z - 0.12), (w + 0.3, 0.1, 0.16), "dark_wood")
        box(detail, "stern_window_head_%d" % k, (x, y + h + 0.07, z - 0.12), (w + 0.3, 0.14, 0.16), "dark_wood")
    # the slanted roof over the stern gallery (the "awning" of the reference)
    for side, sn in SIDES:
        pass
    yr = 2.15
    xr = ls.hull_x(z, yr)
    quad(bone, "stern_roof", v3(-xr, yr + 0.35, z), v3(xr, yr + 0.35, z), v3(-xr - 0.2, yr - 0.15, z - 0.9), v3(xr + 0.2, yr - 0.15, z - 0.9),
         0.1, "dark_wood", v3(0, 1, -0.4), u_dir=v3(1, 0, 0), stretch=False)
    # side windows of the stern castle (the captain's quarters), leaded and lit
    for side, sn in SIDES:
        for k, zc in enumerate((-11.2, -12.6, -14.0, -15.4, -16.8)):
            p, n = hull_pt(zc, 1.1, side, 0.04)
            R = wall_frame(n)
            n = R[:, 2]
            add_cube(lights, "glow_side_window_%s%d" % (sn, k), p, R, (0.85, 1.1, 0.04), {"all": None, "+3": "window", "-3": "window"},
                     stretch=True)
            for e in (-1, 1):
                add_cube(detail, "side_window_post_%s%d_%d" % (sn, k, e > 0), p + R[:, 0] * e * 0.5 + n * 0.04, R, (0.14, 1.3, 0.12), "dark_wood")
            add_cube(detail, "side_window_sill_%s%d" % (sn, k), p - v3(0, 0.62, 0) + n * 0.06, R, (1.1, 0.12, 0.18), "dark_wood")
        # the gallery's moulding above the windows
        for k, (za, zb) in enumerate(((-10.4, -13.3), (-13.3, -17.6))):
            pa, na = hull_pt(za, 1.85, side, 0.1)
            pb, nb = hull_pt(zb, 1.85, side, 0.1)
            beam(detail, "gallery_moulding_%s%d" % (sn, k), pa, pb, 0.16, "dark_wood", width=0.2, extend=0.06)
        # portholes along the lower deck and the hold, brass rims, lit
        for k, zc in enumerate((8.6, 6.6, 4.6, 2.6, -0.6, -2.6, -4.6, -6.6)):
            p, n = hull_pt(zc, -1.65, side, 0.02)
            add_cube(lights, "glow_porthole_%s%d" % (sn, k), p + n * 0.03, wall_frame(n),
                     (0.46, 0.46, 0.02), {"all": None, "+3": "porthole", "-3": "porthole"}, stretch=True)
            ring(detail, "porthole_rim_%s%d" % (sn, k), p + n * 0.05, n, 0.27, 0.08, "brass", n=10, round_=True)
        # chain plates and deadeyes along the waist
        for k, zc in enumerate((-5.5, -3.5, 3.5, 5.5)):
            p, n = hull_pt(zc, 0.3, side, 0.1)
            box(detail, "chainplate_%s%d" % (sn, k), p, (0.08, 0.9, 0.12), "iron", R=wall_frame(n))


def rudder(root):
    z = ls.HULL_STERN_Z
    rb = Bone("rudder", origin=(0, -1.2, z - 0.2), parent=root)
    y0, y1 = ls.keel_y(z) - 2.6, -1.2
    for k in range(2):
        ya, yb = y0 + (y1 - y0) * k / 2, y0 + (y1 - y0) * (k + 1) / 2
        wa, wb = 0.85 + 0.25 * k, 0.85 + 0.25 * (k + 1)
        quad(rb, "rudder_blade_%d" % k, v3(0, ya, z - 0.25), v3(0, ya, z - 0.25 - wa), v3(0, yb, z - 0.25), v3(0, yb, z - 0.25 - wb), 0.22,
             "hull_low", v3(1, 0, 0), side="dark_wood", u_dir=v3(0, 0, -1), stretch=False)
    tube(rb, "rudder_stock", (0, y0, z - 0.2), (0, 0.4, z - 0.2), 0.26, "dark_wood", sides=6)
    for k, y in enumerate(np.linspace(y0 + 0.4, y1 - 0.2, 4)):
        box(rb, "rudder_strap_%d" % k, (0, y, z - 0.75), (0.28, 0.12, 1.1), "iron")
    return rb


def beakhead(bone, detail, lights):
    """The head of the ship: rails curving from the bow to the cutwater, a grating, the gear wheel at the
    head, the bowsprit with its spear head and a hanging lantern."""
    tip = v3(0, ls.CUTWATER_TIP[1], ls.CUTWATER_TIP[0])
    for side, sn in SIDES:
        for k, (y0, x0) in enumerate(((1.6, 1.7), (2.6, 1.3), (3.5, 0.9))):
            pts = catmull([v3(side * x0 * 0.8, y0, 17.2), v3(side * x0 * 0.55, y0 - 0.2, 18.8), v3(side * 0.25, y0 - 0.1 * k + 0.15, 20.3),
                           v3(side * 0.1, ls.BOW_GEAR[1] - 0.4 + 0.25 * k, ls.BOW_GEAR[0] - 0.7)], 2)
            polyline(bone, "head_rail_%s%d" % (sn, k), pts, 0.16, "dark_wood", sides=4)
        # the curved knees between the rails and the cutwater
        for k, z in enumerate((18.7, 19.5, 20.2)):
            pts = catmull([v3(side * 1.1 * (1 - (z - 18) / 3.5), 3.2, z), v3(side * 0.5 * (1 - (z - 18) / 4), 2.0, z + 0.2),
                           v3(0, max(0.2, (z - 20.0) * 0.6 + 0.9), z + 0.3)], 2)
            polyline(bone, "head_knee_%s%d" % (sn, k), pts, 0.14, "dark_wood", sides=4)
    # scrollwork at the head: a spiral under the gear
    gz, gy, gr = ls.BOW_GEAR
    pts = ga.scroll_pts(gz - 0.6, gy - 1.2, 0.55, 1.2, 1, [(gz - 1.8, gy - 1.9), (gz - 1.1, gy - 1.6)], m=12)
    for side in (0.12, -0.12):
        polyline(detail, "head_scroll_%d" % (side > 0), [v3(side, y, z) for z, y in pts], 0.12, "dark_wood", sides=4)
    gear(bone, "bow_gear", (0, gy, gz), (1, 0, 0), gr, 0.18, teeth=10, region="gear_iron", spokes=5)
    tube(bone, "bow_gear_axle", (-0.2, gy, gz), (0.2, gy, gz), 0.2, "brass", sides=8)
    # the bowsprit: from the forecastle out over the head, iron bands, a spear head with two barbs
    (za, ya), (zb, yb) = ls.BOWSPRIT
    a, b = v3(0, ya, za), v3(0, yb, zb)
    d = norm(b - a)
    tube(bone, "bowsprit", a, b - d * 0.9, 0.42, "dark_wood", sides=8)
    for k, t in enumerate((0.25, 0.5, 0.72)):
        p = a + (b - a) * t
        tube(bone, "bowsprit_band_%d" % k, p - d * 0.1, p + d * 0.1, 0.52, "iron", sides=8)
    arrowhead(bone, "bowsprit_head", b - d * 0.95, d, 1.0, 0.6)
    for e in (1, -1):
        up = norm(np.cross(d, v3(1, 0, 0))) * e
        tube(bone, "bowsprit_barb_%d" % (e > 0), b - d * 0.9, b - d * 1.3 + up * 0.45, 0.08, "iron", sides=4)
    rope(bone, "bobstay", a + (b - a) * 0.75, tip, d=0.08)
    hook = a + (b - a) * 0.87
    return hook


# ================================================================ decks, stairs, the tower
def grid_floor(bone, g, y, region, name, lit=True, zrange=None):
    """Top faces of the solid cells at height y that are walked on (open or room cells above them),
    tiled in 2 block tiles (world-aligned texture)."""
    j = int(round((y - li.Y0) / li.CELL))
    below = g.k[:, j - 1, :]
    above = g.k[:, j, :]
    mask = (below == li.SOLID) & ((above == li.OUT) | (above == li.DRY) | (above == li.FURNITURE) | (above >= li.DOOR))
    if zrange is not None:
        zc = g.zs
        mask &= ((zc >= zrange[0]) & (zc <= zrange[1]))[None, :]
    key = np.zeros(mask.shape, dtype=np.int16)
    count = 0
    for (i0, j0, i1, j1, kk) in greedy(mask, key, True, True):
        x0, x1 = li.X0 + i0 * li.CELL, li.X0 + (i1 + 1) * li.CELL
        z0, z1 = li.Z0 + j0 * li.CELL, li.Z0 + (j1 + 1) * li.CELL
        cube = add_cube(bone, "%s%s_%d" % ("lit_" if lit else "", name, count), v3((x0 + x1) / 2, y - 0.005, (z0 + z1) / 2), EYE,
                        (x1 - x0, 0.01, z1 - z0), {"+2": region}, u_dir=v3(0, 0, 1), v_dir=v3(1, 0, 0))
        set_sub(cube, ((j0 % MAX_TILE) / MAX_TILE, (i0 % MAX_TILE) / MAX_TILE, (j1 % MAX_TILE + 1) / MAX_TILE, (i1 % MAX_TILE + 1) / MAX_TILE))
        count += 1
    return count


def decks(bone, g):
    n = grid_floor(bone, g, ls.MAIN_DECK_Y, "deck", "main_deck", lit=False, zrange=(ls.QUARTERDECK_Z - 1.0, ls.FORECASTLE_Z + 1.0))
    n += grid_floor(bone, g, ls.FORECASTLE_Y, "deck", "forecastle_deck", lit=False, zrange=(ls.FORECASTLE_Z - 0.6, 30))
    n += grid_floor(bone, g, ls.QUARTERDECK_Y, "deck", "quarterdeck", lit=False, zrange=(ls.POOP_Z - 0.6, ls.QUARTERDECK_Z + 0.6))
    n += grid_floor(bone, g, ls.POOP_Y, "deck", "poop_deck", lit=False, zrange=(-30, ls.POOP_Z + 0.6))
    # the balustrades of the castles: along the sides, across their fronts (gaps at the stairs), the stern
    for side, sn in SIDES:
        for k, (z0, z1, y) in enumerate(((ls.FORECASTLE_Z + 0.1, ls.HULL_BOW_Z + ls.BOW_RAKE - 0.4, ls.FORECASTLE_Y), (ls.POOP_Z + 0.1, ls.QUARTERDECK_Z - 0.4, ls.QUARTERDECK_Y),
                                         (ls.HULL_STERN_Z + 0.3, ls.POOP_Z - 0.1, ls.POOP_Y))):
            zz = np.linspace(z0, z1, max(3, int((z1 - z0) / 1.0) + 1))
            pts = [(side * (ls.hull_x(z, y + 0.5) - 0.25), y, z) for z in zz]
            balustrade(bone, "castle_rail_%s%d" % (sn, k), pts, h=1.0, step=0.55)
    stair_gaps = {st[0]: (st[1], st[2]) for st in li.STAIRS}
    for k, (zc, y, gaps) in enumerate(((ls.FORECASTLE_Z + 0.25, ls.FORECASTLE_Y, ("fc_port", "fc_stbd")),
                                       (ls.QUARTERDECK_Z - 0.25, ls.QUARTERDECK_Y, ("qd_port", "qd_stbd")),
                                       (ls.POOP_Z - 0.25, ls.POOP_Y, ("poop",)))):
        w = ls.hull_x(zc, y + 0.5) - 0.5
        cuts = sorted([stair_gaps[s] for s in gaps])
        x = -w
        segs = []
        for a, b in cuts:
            if a > x:
                segs.append((x, a))
            x = b
        segs.append((x, w))
        for s_i, (a, b) in enumerate(segs):
            if b - a < 0.3:
                continue
            balustrade(bone, "front_rail_%d_%d" % (k, s_i), [(a, y, zc), (b, y, zc)], h=1.0, step=0.5)
    zt = ls.HULL_STERN_Z + 0.3
    w = ls.hull_x(zt, ls.POOP_Y + 0.5) - 0.3
    balustrade(bone, "stern_rail", [(-w, ls.POOP_Y, zt), (w, ls.POOP_Y, zt)], h=1.0, step=0.5)
    # the companion's rails on the main deck
    x0, x1, z0, z1 = li.COMPANION_HOLE
    balustrade(bone, "companion_rail", [(x0 - 0.25, 0.0, z1), (x0 - 0.25, 0.0, z0 - 0.25), (x1 + 0.25, 0.0, z0 - 0.25), (x1 + 0.25, 0.0, z1)],
               h=1.0, step=0.6)
    return n


def stairs(outside, inside):
    for st in li.STAIRS:
        name, x0, x1, zs, d, y0, n = st
        interior = n < 0
        bone = inside if interior else outside
        pre = "lit_" if interior else ""
        for k, (sx0, sx1, sz0, sz1, top) in enumerate(li.stair_steps(st)):
            bottom = top - 0.5 if interior else y0
            if top <= bottom + 1e-6:
                continue
            c = v3((sx0 + sx1) / 2, (top + bottom) / 2, (sz0 + sz1) / 2)
            add_cube(bone, "%sstair_%s_%d" % (pre, name, k), c, EYE, (sx1 - sx0, top - bottom, sz1 - sz0),
                     {"all": "dark_wood", "+2": "deck"}, u_dir=v3(1, 0, 0))
            add_cube(bone, "%sstair_%s_%d_nose" % (pre, name, k), v3(c[0], top - 0.04, sz1 if d > 0 else sz0) if not interior else
                     v3(c[0], top - 0.04, sz0 if d < 0 and n < 0 else sz1), EYE, (sx1 - sx0 + 0.02, 0.08, 0.08), "rail")
        # a hand rail on the open side of the outside stairs
        if not interior:
            steps = li.stair_steps(st)
            xin = x0 if abs(x0) < abs(x1) else x1
            pts = [(xin, s[4], (s[2] + s[3]) / 2) for s in steps]
            balustrade(bone, "stair_rail_" + name, [pts[0], pts[-1]], h=0.95, step=0.7)


def tower(bone, root, lights):
    """The central tower from the main deck to the balloon: a timber frame with iron corner posts, a lit
    lantern room at its foot with the door to the ladder shaft, a big gear on its front and back (the
    engine turns it), a capital of brackets under the balloon."""
    x, (z0, z1) = ls.TOWER_X, ls.TOWER_Z
    top = ls.BALLOON_Y - ls.BALLOON_HH + 0.6
    for ex in (1, -1):
        for ez, zc in ((1, z1), (-1, z0)):
            tube(bone, "tower_post_%d_%d" % (ex > 0, ez > 0), (ex * x, 0.0, zc), (ex * x, top, zc), 0.34, "iron", sides=4)
    # planked walls (the outer faces of the grid's tower cells)
    for k, (a, b, nrm) in enumerate((((x, z0), (x, z1), (1, 0, 0)), ((-x, z1), (-x, z0), (-1, 0, 0)), ((-x, z0), (x, z0), (0, 0, -1)))):
        quad(bone, "tower_wall_%d" % k, v3(a[0], 0.0, a[1]), v3(b[0], 0.0, b[1]), v3(a[0], 8.2, a[1]), v3(b[0], 8.2, b[1]), 0.08, "wall_wood",
             v3(*nrm), u_dir=v3(b[0] - a[0], 0, b[1] - a[1]), stretch=False)
    # front wall above the door
    quad(bone, "tower_wall_front", v3(-x, 2.0, z1), v3(x, 2.0, z1), v3(-x, 8.2, z1), v3(x, 8.2, z1), 0.08, "wall_wood", v3(0, 0, 1),
         u_dir=v3(1, 0, 0), stretch=False)
    for ex in (1, -1):
        quad(bone, "tower_wall_front_%d" % (ex > 0), v3(ex * 1.0, 0.0, z1), v3(ex * x, 0.0, z1), v3(ex * 1.0, 2.0, z1), v3(ex * x, 2.0, z1),
             0.08, "wall_wood", v3(0, 0, 1), u_dir=v3(1, 0, 0), stretch=False)
    # the lantern room's windows (sides and back), lit
    for k, (c, n) in enumerate(((v3(x + 0.02, 1.5, (z0 + z1) / 2), v3(1, 0, 0)), (v3(-x - 0.02, 1.5, (z0 + z1) / 2), v3(-1, 0, 0)),
                                (v3(0, 1.5, z0 - 0.02), v3(0, 0, -1)))):
        R = np.column_stack([np.cross(v3(0, 1, 0), n), v3(0, 1, 0), n])
        add_cube(lights, "glow_tower_window_%d" % k, c, R, (1.6, 1.4, 0.03), {"all": None, "+3": "window", "-3": "window"}, stretch=True)
        add_cube(bone, "tower_window_frame_%d" % k, c + n * 0.03 - v3(0, 0.78, 0), R, (1.9, 0.14, 0.12), "dark_wood")
        add_cube(bone, "tower_window_head_%d" % k, c + n * 0.03 + v3(0, 0.78, 0), R, (1.9, 0.16, 0.14), "dark_wood")
    # cornices and iron bands round the tower
    for k, y in enumerate((0.15, 2.4, 3.0, 5.9, 7.2)):
        for ez in (1, -1):
            beam(bone, "tower_band_z_%d_%d" % (k, ez > 0), v3(-x - 0.1, y, (z0 + z1) / 2 + ez * (x + 0.1)),
                 v3(x + 0.1, y, (z0 + z1) / 2 + ez * (x + 0.1)), 0.18, "iron" if k % 2 else "dark_wood", width=0.16)
        for ex in (1, -1):
            beam(bone, "tower_band_x_%d_%d" % (k, ex > 0), v3(ex * (x + 0.1), y, z0 - 0.1), v3(ex * (x + 0.1), y, z1 + 0.1), 0.18,
                 "iron" if k % 2 else "dark_wood", width=0.16)
    # the big gear on each side (bone tower_gear_<k>, turned by the engine) and its small pinion
    gy, off, gr = ls.TOWER_GEAR[1], ls.TOWER_GEAR[2], ls.TOWER_GEAR[3]
    zc = (z0 + z1) / 2
    for k, nx in enumerate((1, -1)):
        xf = nx * (x + off)
        gb = Bone("tower_gear_%d" % k, origin=(xf, gy, zc), parent=root)
        gear(gb, "tower_gear_%d" % k, (xf, gy, zc), (nx, 0, 0), gr, 0.22, teeth=14, region="brass", spokes=6, rim="brass")
        tube(bone, "tower_gear_axle_%d" % k, (nx * x, gy, zc), (xf + nx * 0.2, gy, zc), 0.3, "iron", sides=8)
        gear(bone, "tower_pinion_%d" % k, (xf - nx * 0.05, gy + gr + 0.4, zc + 0.6), (nx, 0, 0), 0.45, 0.18, teeth=8, region="gear_iron",
             spokes=4)
    # pipes up the tower into the balloon (steam to the envelope)
    for k, ex in enumerate((1, -1)):
        pts = [v3(ex * (x + 0.3), 2.4, z0 + 0.4), v3(ex * (x + 0.3), 6.0, z0 + 0.4), v3(ex * (x + 0.15), 7.6, z0 + 0.2),
               v3(ex * 0.8, top + 0.6, z0 - 0.3)]
        polyline(bone, "tower_pipe_%d" % k, catmull(pts, 2), 0.2, "copper", sides=6)
    # the capital: diagonal iron brackets from the tower into the balloon's belly, a bearing plate
    for ex in (1, -1):
        for ez, zc in ((1, z1), (-1, z0)):
            p0 = v3(ex * x, 6.6, zc)
            p1 = v3(ex * (x + 1.8), top + 0.3, zc + ez * 1.8)
            tube(bone, "tower_bracket_%d_%d" % (ex > 0, ez > 0), p0, p1, 0.2, "iron", sides=4)
    disc(bone, "tower_plate", (0, top - 0.1, (z0 + z1) / 2), (0, 1, 0), 2.6, 0.2, "iron", sides=12)
    hanging_lantern(root.children[0] if False else bone, "tower_front", v3(x + 0.35, 3.0, z1 + 0.35), drop=0.3, sway=False)


def suspension(bone, sails_root):
    """Ropes, chains, rope nets and pulleys from the balloon to the ship; the black sails."""
    bottom = lambda z, az: P(z, az, 0.15)  # noqa: E731
    for side, sn in SIDES:
        # load-bearing chains from the middle hoops down to the castles
        for k, (zb, zr, yr) in enumerate(((ls.HOOPS_Z[1], 13.0, ls.FORECASTLE_Y + 1.0), (ls.HOOPS_Z[2], -17.0, ls.POOP_Y + 1.0))):
            a = P(zb, side * 160, 0.6)
            b = v3(side * (ls.hull_x(zr, yr) - 0.1), yr, zr)
            chain(bone, "load_chain_%s%d" % (sn, k), a, b, link=0.3, th=0.08)
            disc(bone, "load_chain_plate_%s%d" % (sn, k), b, (0, 1, 0), 0.25, 0.12, "iron", sides=8)
        # suspension ropes with pulley blocks
        for k, (zb, az, zr) in enumerate(((11.0, 158, 8.0), (8.5, 165, 4.8), (3.0, 170, 1.2), (-4.5, 170, -4.0), (-10.0, 165, -9.5),
                                          (-14.0, 160, -13.5))):
            yr = ls.sheer_y(zr) + (1.0 if ls.deck_y(zr) > 0 else 0.05)
            a = P(zb, side * az, 0.15)
            b = v3(side * (ls.hull_x(zr, min(yr, 5.0)) - 0.15), yr, zr)
            blk = a + (b - a) * 0.72
            tube(bone, "susp_rope_%s%d" % (sn, k), a, blk, 0.1, "rope", sides=4)
            tube(bone, "susp_rope_b_%s%d" % (sn, k), blk, b, 0.08, "rope", sides=4)
            d = norm(b - a)
            Rp = gg.frame_from(d, v3(1, 0, 0))
            box(bone, "pulley_%s%d" % (sn, k), blk, (0.34, 0.22, 0.17), "dark_wood", R=Rp)
            disc(bone, "pulley_sheave_%s%d" % (sn, k), blk, Rp[:, 2], 0.12, 0.25, "brass", sides=8)
        # rope nets (ratlines) from the balloon down to the rail, fore and aft
        for k, (za, zb, yb) in enumerate(((8.75, 5.25, ls.SHEER_WAIST), (-7.6, -11.9, ls.QUARTERDECK_Y + 1.0))):
            xb = lambda z: side * (ls.hull_x(z, 1.0) - 0.2)  # noqa: E731
            top_a, top_b = P(za + 0.3, side * 162, 0.1), P(zb - 0.3, side * 162, 0.1)
            bot_a, bot_b = v3(xb(za), yb, za), v3(xb(zb), yb, zb)
            nv = int((top_a[1] - yb) / 0.55)
            for e, (t, b_) in enumerate(((top_a, bot_a), (top_b, bot_b))):
                tube(bone, "net_side_%s%d_%d" % (sn, k, e), t, b_, 0.17, "rope", sides=4)
            for j in range(1, nv):
                f = j / nv
                pa = top_a + (bot_a - top_a) * f
                pb = top_b + (bot_b - top_b) * f
                pts = sag_points(pa, pb, 0.18, 4)
                polyline(bone, "net_rung_%s%d_%d" % (sn, k, j), pts, 0.11, "rope", sides=4, extend=0.03)
            for i in range(1, 4):
                f = i / 4
                tube(bone, "net_vert_%s%d_%d" % (sn, k, i), top_a + (top_b - top_a) * f, bot_a + (bot_b - bot_a) * f, 0.09, "rope", sides=4)
        # the black sails hanging from yards under the balloon, a little curved, ragged
        for k, (zf, za) in enumerate(((4.2, 1.6), (-5.0, -7.6))):
            yt = ls.BALLOON_Y - ls.balloon_hh((zf + za) / 2) * 0.97 - 0.4
            xs = side * 2.7
            sb = Bone("black_sail_%s%d" % (sn, k), origin=(xs, yt, (zf + za) / 2), parent=sails_root)
            tube(sb, "sail_yard_%s%d" % (sn, k), v3(xs, yt, zf + 0.3), v3(xs, yt, za - 0.3), 0.14, "dark_wood", sides=4)
            for e, zz in ((0, zf + 0.15), (1, za - 0.15)):
                rope(sb, "sail_sling_%s%d_%d" % (sn, k, e), v3(xs, yt, zz), P(zz, side * 172, 0.1), d=0.06)
            h = yt - 2.6
            nu, nv = 4, 5
            for i in range(nu):
                for j in range(nv):
                    u0, u1, v0, v1 = i / nu, (i + 1) / nu, j / nv, (j + 1) / nv

                    def S(u, v):
                        return v3(xs + side * 0.45 * math.sin(math.pi * u) * math.sin(math.pi * 0.85 * v), yt - (yt - h) * v,
                                  zf + (za - zf) * u)
                    quad(sb, "black_sail_%s%d_%d_%d" % (sn, k, i, j), S(u0, v0), S(u1, v0), S(u0, v1), S(u1, v1), 0.03, "sail_black",
                         v3(side, 0, 0), sub=(u0, v0, u1, v1), u_dir=v3(0, 0, za - zf), v_dir=v3(0, -1, 0))
            # sheets from the clews to the rail
            for e, zz in ((0, zf), (1, za)):
                rope(sb, "sail_sheet_%s%d_%d" % (sn, k, e), v3(xs, h + 0.1, zz), v3(side * (ls.hull_x(zz, 1.0) - 0.2), 1.05, zz), d=0.05)


def ship_lanterns(lanterns_root, hook):
    hanging_lantern(lanterns_root, "bowsprit", hook, drop=0.9)
    for side, sn in SIDES:
        z = ls.HULL_STERN_Z - 0.2
        x = ls.hull_x(z, ls.POOP_Y) + 0.1
        base = v3(side * x, ls.POOP_Y + 0.6, z + 0.6)
        polyline(lanterns_root, "stern_bracket_" + sn, [base, base + v3(side * 0.4, 0.3, -0.3), base + v3(side * 0.6, 0.15, -0.6)], 0.09, "iron",
                 sides=4)
        hanging_lantern(lanterns_root, "stern_" + sn, base + v3(side * 0.6, 0.15, -0.6), drop=0.3)
        for k, z in enumerate((ls.FORECASTLE_Z + 0.4, ls.QUARTERDECK_Z - 0.4, 13.0, -11.0, ls.POOP_Z - 0.4, -18.6, 6.5, 2.5, -2.5,
                               -6.0)):
            y = ls.deck_y(z) + (1.0 if ls.deck_y(z) > 0 else ls.sheer_y(z) - ls.deck_y(z) + 0.05)
            x = ls.hull_x(z, y) - 0.25
            box(lanterns_root, "rail_lantern_post_%s%d" % (sn, k), (side * x, y + 0.2, z), (0.1, 0.4, 0.1), "iron")
            add_cube(lanterns_root, "rail_lantern_%s%d" % (sn, k), v3(side * x, y + 0.65, z), EYE, (0.3, 0.42, 0.3),
                     {"all": "lantern", "+2": "iron", "-2": "iron"}, stretch=True)
    for k, z in enumerate((-2.1, -7.85)):
        hanging_lantern(lanterns_root, "keel_%d" % k, v3(0, ls.keel_y(z) - 0.3, z), drop=1.0)


# ================================================================ rooms (grid surfaces), ladders, doors
OPEN_KINDS = (li.DRY, li.LADDER)
MAX_TILE = 4
ROOM_MATERIALS = {
    "captain_office": ("in_wall_panel", "in_floor_capt", "in_ceil"), "captain_bedroom": ("in_wall_panel", "in_floor_capt", "in_ceil"),
    "chart_room": ("in_wall_chart", "in_floor_capt", "in_ceil"), "bosun_store": ("in_wall_hold", "in_floor_hold", "in_ceil"),
    "common_room": ("in_wall", "in_floor", "in_ceil"), "coursive": ("in_wall", "in_floor", "in_ceil"),
    "crew_room": ("in_wall", "in_floor", "in_ceil"), "storeroom": ("in_wall", "in_floor", "in_ceil"),
    "hold": ("in_wall_hold", "in_floor_hold", "in_ceil"), "engine_room": ("in_wall_engine", "in_floor_iron", "in_ceil_soot"),
}
SHAFT_MAT = ("in_wall", "in_floor", "in_ceil")


def room_at(x, y, z):
    for name, (x0, x1, y0, y1, z0, z1) in li.ROOMS.items():
        if x0 - 0.01 <= x <= x1 + 0.01 and y0 - 0.01 <= y <= y1 + 0.01 and z0 - 0.01 <= z <= z1 + 0.01:
            return name
    return None


def greedy(mask, key, align_i=False, align_j=False):
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
            while j1 + 1 < nj_ and m[i, j1 + 1] and key[i, j1 + 1] == kk and j1 + 1 - j < MAX_TILE and not (align_j and (j1 + 1) % MAX_TILE == 0):
                j1 += 1
            i1 = i
            while i1 + 1 < ni_ and i1 + 1 - i < MAX_TILE and not (align_i and (i1 + 1) % MAX_TILE == 0) and m[i1 + 1, j:j1 + 1].all() and (
                    key[i1 + 1, j:j1 + 1] == kk).all():
                i1 += 1
            m[i:i1 + 1, j:j1 + 1] = False
            out.append((i, j, i1, j1, kk))
            j = j1 + 1
    return out


def surfaces(rooms_bone, g):
    """Walls, floors and ceilings of the rooms on the cell boundaries (solid next to a room cell)."""
    k = g.k
    solid = k == li.SOLID
    roomish = np.isin(k, OPEN_KINDS) | (k >= li.DOOR)
    near = roomish.copy()
    for a in range(3):
        for s in (1, -1):
            near |= np.roll(roomish, s, axis=a)
    opened = roomish | ((k == li.FURNITURE) & near)
    C = li.CELL
    origin = (li.X0, li.Y0, li.Z0)
    mats = [SHAFT_MAT] + [m for m in dict.fromkeys(ROOM_MATERIALS.values()) if m != SHAFT_MAT]
    mat_index = np.zeros(k.shape, dtype=np.int16)
    for name, box_ in li.ROOMS.items():
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
                for (i0, j0, i1, j1, kk) in greedy(m2, nb_mat[tuple(sl)], al_i, al_j):
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
                        ry0, ry1 = (li.ROOMS[room][2], li.ROOMS[room][3]) if room else (lo[1], hi[1])
                        hgt = max(0.5, ry1 - ry0)
                        v0 = min(1.0, max(0.0, (ry1 - hi[1]) / hgt))
                        v1 = min(1.0, max(v0 + 0.01, (ry1 - lo[1]) / hgt))
                        sub = ((hz0 % MAX_TILE) / MAX_TILE, v0, (hz1 % MAX_TILE + 1) / MAX_TILE, v1)
                    set_sub(cube, sub)
                    count += 1
    return count


def ladders(bone):
    for name, (x0, x1, y0, y1, z0, z1) in li.LADDERS.items():
        wall = z0
        pa = lambda y: v3(x0 + 0.15, y, wall + 0.08)  # noqa: E731
        pb = lambda y: v3(x1 - 0.15, y, wall + 0.08)  # noqa: E731
        beam(bone, "lit_ladder_%s_rail_a" % name, pa(y0), pa(y1), 0.08, "rung")
        beam(bone, "lit_ladder_%s_rail_b" % name, pb(y0), pb(y1), 0.08, "rung")
        y, i = y0 + 0.25, 0
        while y < y1 - 0.1:
            beam(bone, "lit_ladder_%s_rung_%d" % (name, i), pa(y), pb(y), 0.07, "rung")
            y += 0.5
            i += 1


def doors(root, g):
    anims = []
    for d, (name, box_) in li.DOORS.items():
        x0, x1, y0, y1, z0, z1 = box_
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        flat = sy <= min(sx, sz) + 1e-6
        pre = "" if d in (li.TOWER_DOOR, li.TOP_HATCH) else "lit_"
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
            add_cube(root, "%sdoor_%d_jamb_%d" % (pre, d, k), c, EYE, size, "dark_wood")
        c = v3((x0 + x1) / 2, y1 + w / 2, (z0 + z1) / 2)
        size = (depth, w, sz + 2 * w) if along_z else (sx + 2 * w, w, depth)
        add_cube(root, "%sdoor_%d_lintel" % (pre, d), c, EYE, size, "dark_wood")
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


# ================================================================ furniture made for the airship (tools/leviathan_furniture.py)
def _named(fn):
    return lambda bone_, **kw: fn(bone_, kw.pop("name"), **kw)


def lantern_post(bone, name, p, arm=(0, 0, 1), h=2.1):
    """A wooden post with an iron arm at its top, where a lantern of the mods hangs."""
    p = v3(*p)
    lf.timber(bone, name, p, p + v3(0, h, 0), w=0.2)
    box(bone, "lit_%s_foot" % name, p + v3(0, 0.08, 0), (0.34, 0.16, 0.34), "in_iron")
    a = v3(*arm)
    tip = p + v3(0, h - 0.05, 0) + a * 0.42
    beam(bone, "lit_%s_arm" % name, p + v3(0, h - 0.05, 0), tip, 0.06, "in_iron")
    beam(bone, "lit_%s_brace" % name, p + v3(0, h - 0.35, 0), p + v3(0, h - 0.05, 0) + a * 0.25, 0.04, "in_iron")
    box(bone, "lit_%s_cap" % name, p + v3(0, h + 0.03, 0), (0.26, 0.06, 0.26), "in_iron")


FURNITURE_BUILDERS = {
    "rug": _named(lf.rug),
    "chart_sheet": _named(lf.chart_sheet),
    "timber": _named(lf.timber),
    "knee": _named(lf.knee),
    "sea_chest": _named(lf.sea_chest),
    "barrel": _named(lf.barrel),
    "rope_coil": _named(lf.rope_coil),
    "sack": _named(lf.sack),
    "coal_heap": _named(lf.coal_heap),
    "bed_blanket": _named(lf.bed_blanket),
    "candle": _named(lf.candle),
    "window_in": _named(lf.window_in),
    "porthole_in": _named(lf.porthole_in),
    "painting_frame": _named(lf.painting_frame),
    "wall_map": _named(lf.wall_map),
    "compass": _named(lf.compass),
    "sextant": _named(lf.sextant),
    "dividers": _named(lf.dividers),
    "map_roll": _named(lf.map_roll),
    "inkwell": _named(lf.inkwell),
    "hourglass": _named(lf.hourglass),
    "jar_shelf": _named(lf.jar_shelf),
    "book_shelf": _named(lf.book_shelf),
    "wall_bracket": _named(lf.wall_bracket),
    "lever_bank": _named(lf.lever_bank),
    "pressure_tank": _named(lf.pressure_tank),
    "railing": _named(lf.railing),
    "pipe": _named(lf.pipe),
    "valve": _named(lf.valve),
    "gauge": _named(lf.gauge),
    "gauge_board": _named(lf.gauge_board),
    "globe": _named(nf.globe),
    "telescope": _named(nf.telescope),
    "lantern_post": _named(lantern_post),
}


def helm(root, bone):
    """The helm on the quarterdeck: a turned pedestal, the wheel (bone helm_wheel), a binnacle."""
    z = ls.HELM_Z
    y = li.CASTLE
    tube(bone, "helm_pedestal", (0, y, z - 0.1), (0, y + 1.0, z - 0.1), 0.34, "dark_wood", sides=8)
    for k, yy in enumerate((y + 0.1, y + 0.55, y + 0.95)):
        tube(bone, "helm_pedestal_ring_%d" % k, (0, yy - 0.05, z - 0.1), (0, yy + 0.05, z - 0.1), 0.42, "brass", sides=8)
    c = v3(0, y + 1.25, z - 0.35)
    tube(bone, "helm_shaft", (0, y + 1.25, z - 0.1), c, 0.1, "iron", sides=6)
    wb = Bone("helm_wheel", origin=tuple(c), parent=root)
    ship_wheel(wb, "helm", c, (0, 0, 1), r=0.62)
    tube(bone, "binnacle", (1.1, y, z + 0.1), (1.1, y + 1.0, z + 0.1), 0.36, "organ_wood", sides=8)
    disc(bone, "binnacle_bowl", (1.1, y + 1.08, z + 0.1), (0, 1, 0), 0.28, 0.16, "brass")


def boiler(root, bone):
    """The engine room (reference panel 6): the big riveted boiler with its gilded ribs and bands, the round
    hatch with its spoked emblem, two glowing fireboxes, gauges, the stack into the ceiling, the pipes from
    its dome to the walls with their valves; aft of it the piston engine (bones engine_piston_<k>, its
    flywheel engine_gear_0) and gear trains on the walls (engine_gear_1..4), all turned by the engine."""
    bx, bz, br, b0, b1 = li.BOILER
    r = br - 0.12
    c = v3(bx, b0, bz)
    top = lf.boiler(root, bone, Bone, c, r=r)
    lf.boiler_front(bone, c, r, 3.0)
    # the stack: up through the ceiling, banded
    tube(bone, "lit_boiler_stack", top, v3(bx, ls.MAIN_DECK_Y - 0.4, bz), 2 * li.CHIMNEY_R - 0.06, "in_rivets", sides=8)
    for k, y in enumerate((top[1] + 0.15, top[1] + 0.85, ls.MAIN_DECK_Y - 0.75)):
        tube(bone, "lit_boiler_stack_band%d" % k, v3(bx, y - 0.06, bz), v3(bx, y + 0.06, bz), 2 * li.CHIMNEY_R + 0.06, "in_gold", sides=8)
    # side drums high on the boiler, pipes from them and from the dome up to the walls
    for k, ex in enumerate((1, -1)):
        d0 = v3(bx + ex * (r * 0.85), b0 + 2.55, bz)
        tube(bone, "lit_boiler_drum%d" % k, d0, d0 + v3(ex * 0.75, 0, 0), 0.6, "in_boiler", sides=8)
        tube(bone, "lit_boiler_drum_cap%d" % k, d0 + v3(ex * 0.72, 0, 0), d0 + v3(ex * 0.82, 0, 0), 0.68, "in_gold", sides=8)
        wx = ex * 3.75
        lf.pipe(bone, "boiler_pipe_up%d" % k, [v3(bx + ex * 0.45, top[1] - 0.15, bz + 0.25), v3(bx + ex * 1.4, top[1] + 0.55, bz + 0.6),
                                                v3(wx - ex * 0.2, top[1] + 1.1, bz + 0.6), v3(wx - ex * 0.2, top[1] + 1.1, bz - 1.8)], d=0.24)
        lf.pipe(bone, "boiler_pipe_drum%d" % k, [d0 + v3(ex * 0.82, 0, 0), v3(wx - ex * 0.15, b0 + 2.55, bz), v3(wx - ex * 0.15, b0 + 2.55, bz + 1.6)],
                d=0.2, region="in_brass", flange="in_iron")
        lf.valve(bone, "boiler_valve%d" % k, v3(bx + ex * 1.4, top[1] + 0.55, bz + 0.6), (0, 0, 1), r=0.2)
    lf.valve(bone, "boiler_valve_front", v3(bx + 0.75, b0 + 1.05, bz + r + 0.2), (0, 0, 1), r=0.17)
    # the piston engine aft of the boiler: two cylinders, rods and crossheads (moving), a flywheel (turning)
    ez = bz - br - 0.42
    box(bone, "lit_engine_bed", (bx, b0 + 0.15, ez), (1.8, 0.3, 0.85), {"all": "in_iron", "+2": "in_rivets"})
    for k, ex in enumerate((0.5, -0.5)):
        tube(bone, "lit_engine_cyl_%d" % k, (bx + ex, b0 + 0.3, ez), (bx + ex, b0 + 1.35, ez), 0.5, "in_brass", sides=8)
        tube(bone, "lit_engine_cyl_cap_%d" % k, (bx + ex, b0 + 1.33, ez), (bx + ex, b0 + 1.45, ez), 0.58, "in_iron", sides=8)
        pb = Bone("engine_piston_%d" % k, origin=(bx + ex, b0 + 1.45, ez), parent=root)
        tube(pb, "lit_engine_rod_%d" % k, (bx + ex, b0 + 1.45, ez), (bx + ex, b0 + 2.15, ez), 0.1, "steel", sides=4)
        box(pb, "lit_engine_crosshead_%d" % k, (bx + ex, b0 + 2.2, ez), (0.22, 0.14, 0.22), "in_brass")
    gb = Bone("engine_gear_0", origin=(bx, b0 + 2.55, ez - 0.25), parent=root)
    lf.gear(gb, "lit_engine_gear", (bx, b0 + 2.55, ez - 0.25), (0, 0, 1), 0.75, 0.16, teeth=14, region="in_brass", spokes=6)
    tube(bone, "lit_engine_axle", (bx, b0 + 2.55, ez - 0.35), (bx, b0 + 2.55, ez + 0.3), 0.14, "in_iron", sides=6)
    # gear trains on the walls (visible from the landing): a big wheel and its pinion on each side
    GEAR_TRAINS.clear()
    for k, (x, y, z, rr, nrm) in enumerate(((3.9, -1.55, -13.6, 0.75, (-1, 0, 0)), (3.9, -1.0, -12.35, 0.42, (-1, 0, 0)),
                                             (-3.9, -1.25, -14.6, 0.7, (1, 0, 0)), (-3.9, -0.95, -13.4, 0.4, (1, 0, 0)))):
        w = ld.wall_x(y, z, 1 if x > 0 else -1)
        xx = w + nrm[0] * 0.14
        name = "engine_gear_%d" % (k + 1)
        gb = Bone(name, origin=(xx, y, z), parent=root)
        lf.gear(gb, "lit_" + name, (xx, y, z), nrm, rr, 0.12, teeth=14 if rr > 0.5 else 9, region="in_brass" if k % 2 == 0 else "gear_iron",
                spokes=6 if rr > 0.5 else 4, rim="in_brass" if k % 2 == 0 else "gear_iron")
        tube(bone, "lit_%s_axle" % name, (w, y, z), (xx + nrm[0] * 0.1, y, z), 0.16, "in_iron", sides=6)
        GEAR_TRAINS.append((name, -1 if k % 2 else 1, 14 if rr > 0.5 else 9))


GEAR_TRAINS = []   # (bone, direction, teeth) of the wall gears, for the engine animation


def fallbacks(root):
    """Stand-ins of the decoration blocks, shown only when their mod is missing on a client."""
    for i, b in enumerate(ld.BLOCKS):
        x0, x1, y0, y1, z0, z1 = ld.footprint(b)
        bone = Bone("fallback_%d" % i, parent=root)
        pre = "glow" if b["block"] in ld.GLOWING_FALLBACK else "lit"
        add_cube(bone, "%s_fallback_%d" % (pre, i), v3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), EYE,
                 (max(0.04, x1 - x0), max(0.04, y1 - y0), max(0.04, z1 - z0)), ld.FALLBACK_REGION.get(b["block"], "in_plank"),
                 stretch=True)


# ================================================================ build
def build(g):
    root = Bone("sky_leviathan")
    bal = Bone("balloon", parent=root)
    hoops = Bone("hoops", parent=root)
    detail = Bone("detail", parent=root)
    nose_b = Bone("nose", parent=root)
    tail_b = Bone("tail", parent=root)
    top = Bone("top_deck", parent=root)
    rig = Bone("rigging", parent=root)
    pennants = Bone("pennants", parent=root)
    lanterns = Bone("lanterns", parent=root)
    hull_b = Bone("hull", parent=root)
    deck_b = Bone("decks", parent=root)
    head = Bone("beakhead", parent=root)
    tower_b = Bone("tower", parent=root)
    susp = Bone("suspension", parent=root)
    sails = Bone("black_sails", parent=root)
    lights = Bone("lights", parent=root)
    rooms = Bone("rooms", parent=root)
    fittings = Bone("fittings", parent=root)
    furniture = Bone("furniture", parent=root)
    balloon(bal, hoops, detail)
    nose(nose_b)
    tail(tail_b)
    fins(root)
    top_deck(top, root, g)
    rigging(rig, pennants, lanterns)
    hull(hull_b, detail, lights)
    rudder(root)
    hook = beakhead(head, detail, lights)
    decks(deck_b, g)
    stairs(deck_b, fittings)
    tower(tower_b, root, lights)
    suspension(susp, sails)
    ship_lanterns(lanterns, hook)
    m = surfaces(rooms, g)
    ladders(fittings)
    helm(root, fittings)
    boiler(root, fittings)
    fallbacks(root)
    for k, (builder, kwargs, solid) in enumerate(ld.CUSTOM):
        kw = dict(kwargs)
        kw.setdefault("name", "%s_%d" % (builder, k))
        FURNITURE_BUILDERS[builder](furniture, **kw)
    return root, m


def build_animations(root):
    kf, rot_kf, animation, find = gg.kf, gg.rot_kf, gg.animation, gg.find
    anims = []
    spin = [rot_kf(t, (0, 0, a)) for t, a in ((0.0, 0), (0.5, 90), (1.0, 180), (1.5, 270), (2.0, 360))]
    tracks = []
    for k in range(2):
        b = find(root, "tower_gear_%d" % k)
        tracks.append((b, [rot_kf(t, (0, 0, a * (1 if k == 0 else -1))) for t, a in ((0.0, 0), (0.5, 45), (1.0, 90), (1.5, 135), (2.0, 180))]))
    tracks.append((find(root, "engine_gear_0"), spin))
    for name, sgn, teeth in GEAR_TRAINS:
        turn = sgn * 180.0 * (14.0 / teeth)
        tracks.append((find(root, name), [rot_kf(t, (turn * t / 2.0, 0, 0)) for t in (0.0, 0.5, 1.0, 1.5, 2.0)]))
    for k in range(2):
        b = find(root, "engine_piston_%d" % k)
        tracks.append((b, [kf("position", 2.0 * i / 12, (0, 0.3 * 16 * math.sin(2 * math.pi * i / 6 + k * math.pi), 0)) for i in range(13)]))
    anims.append(animation("engine", 2.0, "loop", tracks))
    anims.append(animation("steer", 2.0, "hold", [
        (find(root, "helm_wheel"), [rot_kf(0.0, (0, 0, -150)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 0, 150))]),
        (find(root, "rudder"), [rot_kf(0.0, (0, -25, 0)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 25, 0))]),
        (find(root, "fin_dorsal"), [rot_kf(0.0, (0, -10, 0)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 10, 0))]),
        (find(root, "fin_lower"), [rot_kf(0.0, (0, -10, 0)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 10, 0))])]))
    anims.append(animation("elevator", 2.0, "hold", [
        (find(root, name), [rot_kf(0.0, (-8, 0, 0)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (8, 0, 0))]) for name in ("fin_side_p", "fin_side_s")]))
    f, ft = find(root, "flag"), find(root, "flag_tip")
    anims.append(animation("flag_wave", 1.2, "loop", [
        (f, [rot_kf(0.0, (0, 8, 0), "catmullrom"), rot_kf(0.6, (0, -8, 0), "catmullrom"), rot_kf(1.2, (0, 8, 0), "catmullrom")]),
        (ft, [rot_kf(0.0, (0, -16, 0), "catmullrom"), rot_kf(0.6, (0, 16, 0), "catmullrom"), rot_kf(1.2, (0, -16, 0), "catmullrom")])]))
    tracks = []
    lan = find(root, "lanterns")
    for k, b in enumerate(c for c in lan.children if c.name.startswith("lantern_")):
        sh = (0.37 * k) % 4.0
        keys = [rot_kf(t, (5 * math.sin(2 * math.pi * (t + sh) / 4.0), 0, 4 * math.cos(2 * math.pi * (t + sh) / 4.0))) for t in (0.0, 1.0, 2.0, 3.0, 4.0)]
        tracks.append((b, keys))
    anims.append(animation("lantern_sway", 4.0, "loop", tracks))
    tracks = []
    for k, b in enumerate(c for c in find(root, "pennants").children):
        sh = 0.7 * k
        tracks.append((b, [rot_kf(t, (3 * math.sin(2 * math.pi * t / 3.0 + sh), 0, 2 * math.cos(2 * math.pi * t / 3.0 + sh)))
                           for t in (0.0, 0.75, 1.5, 2.25, 3.0)]))
    for k, b in enumerate(c for c in find(root, "black_sails").children):
        sh = 1.1 * k
        tracks.append((b, [rot_kf(t, (0, 0, 4 * math.sin(2 * math.pi * t / 3.0 + sh))) for t in (0.0, 0.75, 1.5, 2.25, 3.0)]))
    anims.append(animation("streamer_wave", 3.0, "loop", tracks))
    return anims


def check_axes(root):
    """Names of the cubes whose axes are not a rotation (they would be drawn sheared)."""
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


def main():
    if os.environ.get("LEVIATHAN_FAST"):   # quick previews: no z-fighting pass
        import zfight
        zfight.fix = lambda root: 0
    g = li.build()
    ld.build()
    ld.apply_to_grid(g)
    ld.write(os.path.join(ROOT, ld.DECOR_PATH))
    size = g.write(os.path.join(ROOT, li.GRID_PATH))
    reached, total = li.walkable_report(g)
    unreachable = [name for name, n in reached.items() if not n]
    print("decor blocks:", len(ld.BLOCKS), "seats:", len(ld.SEATS), "standing places:", total, "unreachable:", unreachable)
    root, m = build(g)
    anims = build_animations(root)
    anims += doors(root, g)
    bad = check_axes(root)
    if bad:
        print("WARNING: %d cubes with skewed axes, e.g." % len(bad), bad[:8])
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    tex_path = os.path.join(tex_dir, "entity/sky_leviathan.png")
    lt.make_texture(tex_path)
    lt.make_item_icon(os.path.join(tex_dir, "item/sky_leviathan.png"))
    with open(tex_path, "rb") as f:
        png = f.read()
    in_path = os.path.join(tex_dir, "entity/sky_leviathan_interior.png")
    lt.make_interior_texture(in_path)
    with open(in_path, "rb") as f:
        png_in = f.read()
    textures = [gn.texture_entry("sky_leviathan.png", lt.SIZE, png, "entity", "sky_leviathan.png"),
                gn.texture_entry("sky_leviathan_interior.png", lt.SIZE_IN, png_in, "entity", "sky_leviathan.png")]
    textures[0]["id"] = "0"
    textures[1]["id"] = "1"
    model = gn.export(root, anims, textures, [
        os.path.join(ROOT, "blockbench/sky_leviathan.bbmodel"),
        os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/sky_leviathan.bbmodel"),
    ], name="sky_leviathan", visible_box=(70, 50, 0))
    print("grid bytes:", size, "grid surfaces:", m, "cubes:", len(model["elements"]), "animations:", len(model["animations"]))


if __name__ == "__main__":
    main()
