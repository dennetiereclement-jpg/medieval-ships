#!/usr/bin/env python3
"""Generates the Rustic Skyskiff (rustic_skiff) Blockbench model, its texture, its item icon, its interior grid and
its furniture file.

Usage:  python3 tools/generate_skiff.py        (SKIFF_FAST=1: no z-fighting pass, for quick previews)

Outputs:
  blockbench/rustic_skiff.bbmodel                                            (editable, texture embedded)
  src/main/resources/assets/medievalships/models/entity/rustic_skiff.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/rustic_skiff.png
  src/main/resources/assets/medievalships/textures/item/rustic_skiff.png
  src/main/resources/assets/medievalships/interiors/rustic_skiff.grid         (collisions, ladder, doors)
  src/main/resources/assets/medievalships/interiors/rustic_skiff_decor.json   (mod furniture, seats)

Reference: the Minecraft sheet "Le Navire Volant Rustique" (perspective, side, top, front, back and four interior
views; measurements in docs/SKIFF_PLAN.md): an old, hand-made wooden boat turned into a flying craft. A long,
banana-shaped brown hull of irregular, patched planks with mossy cap rails and reinforcing boards, rising to a raised
bow head with a short bow beam; chains in festoons along its sides from ring bolts, with lanterns hanging under the
hull; a light planked lean-to over the bow (the storage corner); the open fore deck with its grated hatch; the cabin
at the stern with its door, its framed windows and the crate stair up to the pilot deck on its roof, where the wheel
stands behind a rustic balustrade with lanterns; over it the big worn beige canvas roof on splayed poles, its eaves
hanging in torn strips; strings of tattered pennants (beige, red, black) from the bow beam to the roof; two long
inclined derricks at the stern with ropes down to the five bronze tubes fixed on the transom; and four big soft
triangular canvas wings on wooden ribs hanging under the sides, iron spikes at their tips.

The hull is built from tilted panels between stations (rounded, no staircase), following skiff_shape.hull_x; the
decks, the walls, floors and ceilings of the rooms are drawn on the boundaries of the interior grid
(tools/skiff_interior.py): what is drawn is what collides. Room surfaces are named "lit*" (lit by the lanterns).

Bones used by the mod (keep their names when editing in Blockbench):
  helm_wheel (steer)   wing_fore_p, wing_fore_s, wing_aft_p, wing_aft_s (engine: a slow flap while under way; steer:
  the rear wings; elevator: all four)   tube_fan_* (engine: the fans in the tubes' mouths)   lantern_* (lantern_sway)
  pennants_*, fringe_* (streamer_wave)   door_<k> (door k: 0 = closed, 1 = open)
"""
import math
import os
import random
import sys
import uuid

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import generate_galleon as gn  # noqa: E402
import generate_galley as gg  # noqa: E402
import generate_airship as ga  # noqa: E402
import generate_leviathan as gl  # noqa: E402
import skiff_shape as ss  # noqa: E402
import skiff_interior as si  # noqa: E402
import skiff_texture as st  # noqa: E402
import skiff_decor as sd  # noqa: E402
import corsair_furniture as cf  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/rustic_skiff/%d" % _uuid_counter[0]))


# the shared helpers write into these (generate_leviathan set them for itself when imported)
gg.new_uuid = new_uuid
gn.new_uuid = new_uuid
gn.REGIONS = {k: (0,) + r for k, r in st.REGIONS.items()}
gn.SIZE = st.SIZE

v3, norm, Bone, add_cube, beam = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam
tube, disc, ring, polyline, catmull, bezier = ga.tube, ga.disc, ga.ring, ga.polyline, ga.catmull, ga.bezier
quad, box, set_sub, chain, rope, sag_points = gl.quad, gl.box, gl.set_sub, gl.chain, gl.rope, gl.sag_points
balustrade, ship_wheel = gl.balustrade, gl.ship_wheel
EYE = np.eye(3)
SIDES = ((1, "p"), (-1, "s"))
PY, CF = ss.PILOT_Y, ss.CABIN_FRONT_Z


def _sm(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def hanging_lantern(parent, name, hook, drop=0.6, w=0.34, h=0.48, chained=True):
    """A lantern hanging on a short chain from `hook`, in its own bone (lantern_*, swung by lantern_sway)."""
    hook = v3(*hook)
    lb = Bone("lantern_" + name, origin=tuple(hook), parent=parent)
    body = hook - v3(0, drop + h / 2 + 0.12, 0)
    if chained:
        chain(lb, name + "_chain", hook, body + v3(0, h / 2 + 0.16, 0), link=0.16, th=0.035)
    add_cube(lb, name, body, EYE, (w, h, w), {"all": "lantern", "+2": "iron", "-2": "iron"}, stretch=True)
    return lb


def spike(bone, name, base, d, length, r=0.09, region="iron"):
    """A tapering iron spike from base along d (three stacked square segments)."""
    d = norm(v3(*d))
    base = v3(*base)
    for k in range(3):
        a, b = base + d * (length * k / 3), base + d * (length * (k + 1) / 3)
        tube(bone, "%s_%d" % (name, k), a, b, 2 * r * (1.0 - k / 3.2), region, sides=4, extend=0.02)


# ================================================================ hull
HULL_ST = sorted(set([ss.HULL_STERN_Z + 0.001, -12.8, -12.4, -11.8, -11.0, -10.0, -8.8, -7.4, -6.0, -4.5, -3.0, -1.5, 0.0, 1.5, 3.0,
                      3.8, 4.5, 5.2, 6.0, 7.0, 8.0, 9.0, 9.8, 10.6, 11.3, 11.9, 12.4, 12.8, 13.1, 13.3]))
ETA = (0.0, 0.03, 0.08, 0.15, 0.24, 0.35, 0.48, 0.62, 0.77, 0.9, 1.0)
UPPER = (0.0, 0.5, 1.0)
PATCHED = {(3, 6, "p"), (7, 7, "p"), (12, 5, "p"), (16, 8, "p"), (21, 6, "p"), (5, 8, "s"), (10, 6, "s"), (14, 7, "s"), (19, 5, "s"),
           (24, 7, "s"), (1, 9, "p"), (2, 9, "s")}


def hull_top(z):
    """Top of the outer planking: the fore deck's bulwark sweeping up to the bow head; aft, the cabin walls take over
    above the waist."""
    if z <= CF:
        return ss.SHEER_WAIST + 0.15
    return ss.sheer_y(z)


def hull_section(z, side):
    k = ss.keel_y(z)
    top = ss.waist_y(z)
    pts = [v3(side * max(0.03, ss.hull_x(z, k + e * (top - k))), k + e * (top - k), z) for e in ETA]
    yt = hull_top(z)
    if yt > top + 0.05:
        pts += [v3(side * ss.hull_x(z, top + u * (yt - top)), top + u * (yt - top), z) for u in UPPER[1:]]
    return pts


def hull_pt(z, y, side, out=0.0):
    x = ss.hull_x(z, y)
    e = 0.05
    dx = (ss.hull_x(z + e, y) - ss.hull_x(z - e, y)) / (2 * e)
    dy = (ss.hull_x(z, y + e) - ss.hull_x(z, y - e)) / (2 * e)
    n = norm(v3(side, -dy, -dx))
    return v3(side * x, y, z) + n * out, n


def hull(bone, detail):
    for side, sn in SIDES:
        for i in range(len(HULL_ST) - 1):
            za, zb = HULL_ST[i], HULL_ST[i + 1]
            A, B = hull_section(za, side), hull_section(zb, side)
            for k in range(min(len(A), len(B)) - 1):
                if abs(A[k + 1][1] - A[k][1]) < 0.02 and abs(B[k + 1][1] - B[k][1]) < 0.02:
                    continue
                mid = (A[k] + A[k + 1] + B[k] + B[k + 1]) / 4
                region = "hull_patch" if (i, k, sn) in PATCHED else "hull_low" if k < 5 else "hull"
                outward = norm(v3(side, -0.6 if k < 4 else 0.0, 0.3 * np.sign(mid[2])))
                quad(bone, "hull_%s%d_%d" % (sn, i, k), A[k], B[k], A[k + 1], B[k + 1], 0.12, region, outward, u_dir=v3(0, 0, 1),
                     stretch=False, back="dark_wood", overlap=(1.03, 1.06))
    # the keel, sweeping up into the stem and the bow head
    kpts = [v3(0, ss.keel_y(z) - 0.1, z) for z in np.linspace(ss.HULL_STERN_Z + 0.2, 12.6, 16)]
    kpts += [v3(0, ss.keel_y(13.1) - 0.02, 13.25), v3(0, 2.4, 13.62), v3(0, ss.BOW_HEAD[0], ss.BOW_HEAD[1])]
    sm = catmull(kpts, 2)
    for k in range(len(sm) - 1):
        beam(bone, "keel_%d" % k, sm[k], sm[k + 1], 0.42, "dark_wood", width=0.4, up=v3(1, 0, 0), extend=0.08)
    # the bow head: a stout post with a cap, the bow beam (bowsprit) on it, iron bands
    yh, zh = ss.BOW_HEAD
    box(bone, "bow_head", (0, yh + 0.12, zh - 0.15), (0.62, 0.5, 0.62), {"all": "dark_wood", "+2": "moss"})
    box(bone, "bow_head_cap", (0, yh + 0.42, zh - 0.15), (0.42, 0.14, 0.42), "moss")
    (y0, z0), (y1, z1) = ss.BOWSPRIT
    tube(bone, "bowsprit", v3(0, y0, z0), v3(0, y1, z1), 0.36, "pole", sides=8, extend=0.05)
    for k, t in enumerate((0.12, 0.45, 0.9)):
        p = v3(0, y0 + (y1 - y0) * t, z0 + (z1 - z0) * t)
        ring(detail, "bowsprit_band_%d" % k, p, v3(0, y1 - y0, z1 - z0), 0.22, 0.07, "iron", n=6)
    spike(detail, "bowsprit_tip", v3(0, y1, z1), v3(0, -0.08, 1), 0.45, r=0.1)
    # the stern box under the transom (where the rear wings are hinged) and its iron-shod skid
    box(bone, "stern_box", (0, -3.95, -11.2), (2.2, 1.9, 2.9), {"all": "hull_low", "+2": "dark_wood"})
    for sx in (1, -1):
        box(bone, "stern_box_post_%d" % (sx > 0), (sx * 1.08, -3.9, -11.2), (0.18, 2.0, 3.0), "moss_board")
    for k, z in enumerate((-10.0, -12.4)):
        box(detail, "stern_box_band_%d" % k, (0, -3.95, z), (2.28, 1.96, 0.12), "iron")
    # the keel spike under the stern box: a tapering timber, an iron shoe
    yt, zt = ss.SKID_TIP
    top = v3(0, -4.85, -11.3)
    d = norm(v3(0, yt, zt) - top)
    L = np.linalg.norm(v3(0, yt, zt) - top)
    spike(bone, "skid", top, d, L - 0.6, r=0.36, region="dark_wood")
    spike(detail, "skid_shoe", top + d * (L - 0.65), d, 0.65, r=0.13)
    for k, t in enumerate((0.15, 0.5)):
        ring(detail, "skid_band_%d" % k, top + d * (L * t), d, 0.3 - 0.12 * t, 0.08, "iron", n=6)


def transom(bone, detail):
    """The flat transom from the keel up to the pilot deck (planks across), a dark frame round it."""
    z = ss.HULL_STERN_Z - 0.02
    ys = list(np.linspace(ss.keel_y(ss.HULL_STERN_Z), PY - 0.3, 9))
    for k in range(len(ys) - 1):
        ya, yb = ys[k], ys[k + 1]
        xa, xb = ss.hull_x(ss.HULL_STERN_Z, ya), ss.hull_x(ss.HULL_STERN_Z, min(yb, ss.waist_y(ss.HULL_STERN_Z) + 2.5))
        quad(bone, "transom_%d" % k, v3(-xa, ya, z), v3(xa, ya, z), v3(-xb, yb, z), v3(xb, yb, z), 0.12, "hull" if k > 2 else "hull_low",
             v3(0, 0, -1), u_dir=v3(1, 0, 0), stretch=False, back="dark_wood")
    for side, sn in SIDES:
        pts = [v3(side * (ss.hull_x(ss.HULL_STERN_Z, y) - 0.05), y, z - 0.06) for y in np.linspace(ss.keel_y(ss.HULL_STERN_Z) + 0.1, PY - 0.2, 6)]
        polyline(detail, "transom_frame_" + sn, pts, 0.2, "dark_wood", sides=4)
    beam(detail, "transom_rail", v3(-3.4, PY - 0.35, z - 0.1), v3(3.4, PY - 0.35, z - 0.1), 0.24, "moss", width=0.26)


# ---------------------------------------------------------------- bulwarks, caps, boards, chains
CAP_REGION = "moss"
BOARDS_Z = (8.6, 4.2, -0.4, -5.6, -9.8)


def caps(bone, detail):
    """The mossy cap rail along the bulwark (fore deck, sweeping up to the bow head), a mossy ledge along the cabin's
    foot; the inner side of the fore deck's bulwark."""
    for side, sn in SIDES:
        zz = list(np.linspace(CF + 0.05, ss.BOW_HEAD[1] - 0.45, 40))
        for k in range(len(zz) - 1):
            ya, yb = ss.sheer_y(zz[k]), ss.sheer_y(zz[k + 1])
            pa = v3(side * (ss.hull_x(zz[k], ya) - 0.2), ya + 0.12, zz[k])
            pb = v3(side * (ss.hull_x(zz[k + 1], yb) - 0.2), yb + 0.12, zz[k + 1])
            beam(bone, "cap_%s%d" % (sn, k), pa, pb, 0.26, CAP_REGION, width=0.66, extend=0.05)
        # big mossy cap blocks over the reinforcing boards (as on the reference)
        for k, z in enumerate(BOARDS_Z[:3] + (11.0,)):
            y = ss.sheer_y(z)
            box(bone, "cap_block_%s%d" % (sn, k), (side * (ss.hull_x(z, y) - 0.15), y + 0.3, z), (0.82, 0.42, 0.75), "moss",
                R=gg.ry(math.atan2(ss.hull_x(z + 0.3, y) - ss.hull_x(z - 0.3, y), 0.6) * side))
        zz = list(np.linspace(ss.HULL_STERN_Z + 0.05, CF + 0.1, 12))
        y = ss.SHEER_WAIST + 0.15
        for k in range(len(zz) - 1):
            pa = v3(side * (ss.hull_x(zz[k], y) + 0.05), y, zz[k])
            pb = v3(side * (ss.hull_x(zz[k + 1], y) + 0.05), y, zz[k + 1])
            beam(bone, "ledge_%s%d" % (sn, k), pa, pb, 0.22, CAP_REGION, width=0.32, extend=0.04)
        # the inner face of the fore deck's bulwark
        zz = list(np.linspace(CF + 0.02, 11.6, 24))
        for k in range(len(zz) - 1):
            za, zb = zz[k], zz[k + 1]
            fa, fb = ss.deck_y(za + 0.01), ss.deck_y(zb - 0.01)
            if fa != fb:
                fa = fb = max(fa, fb)
            ta, tb = ss.sheer_y(za), ss.sheer_y(zb)
            xa0, xa1 = ss.hull_x(za, fa) - ss.SHELL, ss.hull_x(za, ta) - ss.SHELL
            xb0, xb1 = ss.hull_x(zb, fb) - ss.SHELL, ss.hull_x(zb, tb) - ss.SHELL
            quad(bone, "bulwark_in_%s%d" % (sn, k), v3(side * xa0, fa, za), v3(side * xb0, fb, zb), v3(side * xa1, ta, za),
                 v3(side * xb1, tb, zb), 0.08, "hull", v3(-side, 0, 0), u_dir=v3(0, 0, 1), stretch=False)
        # the top of the bulwark between its inner and outer faces is under the cap


def side_curve(bone, name, zz, yfn, side, out, h, th, region, min_x=0.3):
    pts = []
    for z in zz:
        y = yfn(z)
        if ss.hull_x(z, y) < min_x or y < ss.keel_y(z) + 0.1 or y > hull_top(z) + 0.2:
            if pts:
                break
            continue
        pts.append(hull_pt(z, y, side, out)[0])
    for k in range(len(pts) - 1):
        beam(bone, "%s_%d" % (name, k), pts[k], pts[k + 1], h, region, width=th, up=v3(0, 1, 0), extend=0.06)
    return pts


def boards(bone, detail):
    """Vertical reinforcing boards (moss on their tops), a dark wale along the side, iron straps."""
    for side, sn in SIDES:
        for k, z in enumerate(BOARDS_Z):
            y0 = ss.keel_y(z) + 0.5
            y1 = hull_top(z) - 0.02
            pts = [hull_pt(z, y, side, 0.09)[0] for y in np.linspace(y0, y1, 5)]
            for j in range(len(pts) - 1):
                beam(bone, "board_%s%d_%d" % (sn, k, j), pts[j], pts[j + 1], 0.16, "moss_board" if j == len(pts) - 2 else "dark_wood",
                     width=0.55, up=hull_pt(z, (pts[j][1] + pts[j + 1][1]) / 2, side)[1], extend=0.03)
            for j, y in enumerate((y0 + 0.6, (y0 + y1) / 2 + 0.3)):
                p, n = hull_pt(z, y, side, 0.19)
                box(detail, "board_bolt_%s%d_%d" % (sn, k, j), p, (0.12, 0.12, 0.12), "iron", R=gl.wall_frame(n))
        zz = np.linspace(ss.HULL_STERN_Z + 0.05, 12.8, 50)
        side_curve(bone, "wale_" + sn, zz, lambda z: min(ss.SHEER_WAIST - 1.1 + 0.9 * _sm((z - 7.0) / 6.0), hull_top(z) - 0.4), side, 0.06,
                   0.24, 0.16, "dark_wood")
        side_curve(bone, "wale_low_" + sn, zz, lambda z: ss.keel_y(z) + 0.55 * (ss.waist_y(z) - ss.keel_y(z)), side, 0.05, 0.2, 0.14,
                   "dark_wood")


RINGS_Z = (12.0, 10.2, 8.0, 5.8, 3.6, 1.4)
HULL_LANTERNS = ((10.2, 2.4), (5.8, 3.1), (1.4, 2.0))   # ring z, drop of the chain under the hull side


def ring_y(z):
    return ss.sheer_y(z) - 0.55


def chains(detail, lanterns_root):
    """Ring bolts along the sides with chains hanging between them in festoons, chains with lanterns hanging under
    the hull, the bobstay from the bow beam."""
    for side, sn in SIDES:
        pts = []
        for k, z in enumerate(RINGS_Z):
            p, n = hull_pt(z, ring_y(z), side, 0.05)
            ring(detail, "ring_bolt_%s%d" % (sn, k), p + n * 0.06, n, 0.13, 0.05, "iron", n=6)
            pts.append(p + n * 0.1 - v3(0, 0.13, 0))
        # from the bow beam down to the first ring
        y1, z1 = ss.BOWSPRIT[1]
        tip = v3(0, ss.BOWSPRIT[0][0] + (y1 - ss.BOWSPRIT[0][0]) * 0.55, ss.BOWSPRIT[0][1] + (z1 - ss.BOWSPRIT[0][1]) * 0.55)
        pts = [tip] + pts
        for k in range(len(pts) - 1):
            sag = sag_points(pts[k], pts[k + 1], 0.45 if k else 0.3, 5)
            for j in range(len(sag) - 1):
                # keep the festoons off the planking
                a, b = sag[j], sag[j + 1]
                for q in (a, b):
                    hx = ss.hull_x(q[2], q[1]) + 0.08
                    if abs(q[0]) < hx and q[1] > ss.keel_y(q[2]):
                        q[0] = side * hx
                chain(detail, "festoon_%s%d_%d" % (sn, k, j), a, b, link=0.2, th=0.045)
        for k, (z, drop) in enumerate(HULL_LANTERNS):
            i = RINGS_Z.index(z)
            top = pts[i + 1]
            # the chain runs down outside the hull to the lantern under it
            foot = v3(side * (ss.hull_x(z, ss.keel_y(z) + 0.5) + 0.3), top[1] - drop, z)
            if foot[1] < ss.keel_y(z) - 0.2:
                foot[0] = side * (ss.hull_x(z, ss.keel_y(z) + 0.6) + 0.2)
            chain(detail, "lantern_chain_%s%d" % (sn, k), top, foot, link=0.18, th=0.04)
            hanging_lantern(lanterns_root, "hull_%s%d" % (sn, k), foot, drop=0.05, chained=False)
    # the bobstay: a chain from the bow beam's tip down to the stem
    y1, z1 = ss.BOWSPRIT[1]
    chain(detail, "bobstay", v3(0, y1 - 0.1, z1 - 0.3), v3(0, 0.9, 13.2), link=0.2, th=0.045)
    hanging_lantern(lanterns_root, "bowsprit", v3(0, y1 - 0.15, z1 - 1.6), drop=0.5)


# ================================================================ the bow's lean-to
LEAN_Z = (7.6, 12.7)       # aft (open) end and fore end of the ridge
LEAN_RIDGE = (3.55, 2.95)   # ridge height at those ends


def lean_ridge(z):
    t = (z - LEAN_Z[0]) / (LEAN_Z[1] - LEAN_Z[0])
    return LEAN_RIDGE[0] + (LEAN_RIDGE[1] - LEAN_RIDGE[0]) * t


def lean_to(bone, detail):
    """A shelter of light, weathered planks over the bow: a ridge beam from an A-frame down to the bow head, the two
    sloping sides resting on the cap rails (open aft: the storage corner under it)."""
    zz = list(np.linspace(LEAN_Z[0], LEAN_Z[1], 7))
    for side, sn in SIDES:
        for k in range(len(zz) - 1):
            za, zb = zz[k], zz[k + 1]
            ra, rb = v3(0, lean_ridge(za), za), v3(0, lean_ridge(zb), zb)
            ea = v3(side * (ss.hull_x(za, ss.sheer_y(za)) - 0.22), ss.sheer_y(za) + 0.16, za)
            eb = v3(side * (ss.hull_x(zb, ss.sheer_y(zb)) - 0.22), ss.sheer_y(zb) + 0.16, zb)
            quad(bone, "lean_%s%d" % (sn, k), ea, eb, ra, rb, 0.1, "lean", v3(side, 1, 0), u_dir=v3(0, 0, 1), stretch=False,
                 back="light_wood")
        # the A-frame's leg on this side, from the cap rail up past the ridge (the legs cross above it)
        z = LEAN_Z[0] + 0.1
        foot = v3(side * (ss.hull_x(z, ss.sheer_y(z)) - 0.2), ss.sheer_y(z) + 0.1, z)
        top = v3(-side * 0.45, LEAN_RIDGE[0] + 0.55, z)
        tube(bone, "lean_leg_" + sn, foot, top, 0.24, "pole", sides=6, extend=0.03)
        # battens across the planks
        for k, t in enumerate((0.3, 0.7)):
            za = LEAN_Z[0] + (LEAN_Z[1] - LEAN_Z[0]) * t
            ea = v3(side * (ss.hull_x(za, ss.sheer_y(za)) - 0.22), ss.sheer_y(za) + 0.16, za)
            ra = v3(0, lean_ridge(za), za)
            nn = norm(np.cross(ra - ea, v3(0, 0, 1))) * side
            beam(detail, "lean_batten_%s%d" % (sn, k), ea + nn * 0.07, ra + nn * 0.07, 0.07, "dark_wood", width=0.16, extend=0.02)
    tube(bone, "lean_ridge", v3(0, LEAN_RIDGE[0] + 0.12, LEAN_Z[0] - 0.25), v3(0, LEAN_RIDGE[1] + 0.12, LEAN_Z[1] + 0.2), 0.26, "pole",
         sides=6)
    # a canvas flap rolled up over the open end, tied with rope
    tube(detail, "lean_roll", v3(-1.6, LEAN_RIDGE[0] - 0.65, LEAN_Z[0] - 0.05), v3(1.6, LEAN_RIDGE[0] - 0.65, LEAN_Z[0] - 0.05), 0.3, "cloth",
         sides=6)
    for sx in (-0.9, 0.9):
        ring(detail, "lean_tie_%d" % (sx > 0), v3(sx, LEAN_RIDGE[0] - 0.65, LEAN_Z[0] - 0.05), v3(1, 0, 0), 0.17, 0.05, "rope", n=6)


# ================================================================ decks, the pilot deck
MAX_TILE = 4


def greedy(mask, key, align_i=False, align_j=False):
    return gl.greedy(mask, key, align_i, align_j)


def grid_floor(bone, g, y, region, name, lit=True, zrange=None):
    """Top faces of the solid cells at height y that are walked on (open or room cells above them), in 2 block
    tiles (world-aligned texture)."""
    j = int(round((y - si.Y0) / si.CELL))
    below = g.k[:, j - 1, :]
    above = g.k[:, j, :]
    mask = (below == si.SOLID) & ((above == si.OUT) | (above == si.DRY) | (above == si.FURNITURE) | (above >= si.DOOR))
    if zrange is not None:
        mask &= ((g.zs >= zrange[0]) & (g.zs <= zrange[1]))[None, :]
    key = np.zeros(mask.shape, dtype=np.int16)
    count = 0
    for (i0, j0, i1, j1, kk) in greedy(mask, key, True, True):
        x0, x1 = si.X0 + i0 * si.CELL, si.X0 + (i1 + 1) * si.CELL
        z0, z1 = si.Z0 + j0 * si.CELL, si.Z0 + (j1 + 1) * si.CELL
        cube = add_cube(bone, "%s%s_%d" % ("lit_" if lit else "", name, count), v3((x0 + x1) / 2, y - 0.005, (z0 + z1) / 2), EYE,
                        (x1 - x0, 0.01, z1 - z0), {"+2": region}, u_dir=v3(0, 0, 1), v_dir=v3(1, 0, 0))
        set_sub(cube, ((j0 % MAX_TILE) / MAX_TILE, (i0 % MAX_TILE) / MAX_TILE, (j1 % MAX_TILE + 1) / MAX_TILE, (i1 % MAX_TILE + 1) / MAX_TILE))
        count += 1
    return count


def decks(bone, detail, g):
    n = grid_floor(bone, g, 0.0, "deck", "fore_deck", lit=False, zrange=(CF, 30))
    for k, (z0, h) in enumerate(ss.BOW_STEPS):
        n += grid_floor(bone, g, h, "deck", "bow_step_%d" % k, lit=False, zrange=(z0, 30))
        # the step's riser across the deck
        y0 = ss.BOW_STEPS[k - 1][1] if k else 0.0
        x = ss.hull_x(z0, h) - ss.SHELL
        quad(bone, "bow_riser_%d" % k, v3(-x, y0, z0), v3(x, y0, z0), v3(-x, h, z0), v3(x, h, z0), 0.06, "dark_wood", v3(0, 0, -1),
             u_dir=v3(1, 0, 0), stretch=False)
    n += grid_floor(bone, g, PY, "deck", "pilot_deck", lit=False, zrange=(-30, CF + 1.0))
    # the grated hatch's coaming on the fore deck
    x0, x1, y0, y1, z0, z1 = si.DOORS[si.GRATE_HATCH][1]
    for k, (c, s) in enumerate((((x0 + x1) / 2, (z0 - 0.08)), ((x0 + x1) / 2, (z1 + 0.08)))):
        box(detail, "grate_coaming_%d" % k, (c, 0.04, s), (x1 - x0 + 0.32, 0.08, 0.16), "iron")
    for k, xc in enumerate((x0 - 0.08, x1 + 0.08)):
        box(detail, "grate_coaming_s%d" % k, (xc, 0.04, (z0 + z1) / 2), (0.16, 0.08, z1 - z0), "iron")
    return n


def pilot_deck(bone, detail, lanterns_root):
    """The edge beams of the pilot deck (overhanging the cabin walls), brackets under the overhang, its rustic
    balustrade with mossy corner posts, lanterns."""
    hw = ss.PILOT_HW
    za, zf = ss.PILOT_Z
    yb = PY - 0.25
    # edge beams round the deck
    corners = [v3(hw - 0.2, yb, za + 0.2), v3(hw - 0.2, yb, zf - 0.2), v3(-hw + 0.2, yb, zf - 0.2), v3(-hw + 0.2, yb, za + 0.2)]
    for k in range(4):
        a, b = corners[k], corners[(k + 1) % 4]
        beam(bone, "pilot_edge_%d" % k, a, b, 0.5, "dark_wood", width=0.42, extend=0.2)
    # the underside of the overhang (sides and front)
    for side, sn in SIDES:
        zz = list(np.linspace(za, CF, 8))
        for k in range(len(zz) - 1):
            p0 = v3(side * ss.hull_x(zz[k], PY - 0.5), PY - 0.5, zz[k])
            p1 = v3(side * ss.hull_x(zz[k + 1], PY - 0.5), PY - 0.5, zz[k + 1])
            q0, q1 = v3(side * hw, PY - 0.5, zz[k]), v3(side * hw, PY - 0.5, zz[k + 1])
            quad(bone, "pilot_under_%s%d" % (sn, k), p0, p1, q0, q1, 0.06, "dark_wood", v3(0, -1, 0), u_dir=v3(1, 0, 0), stretch=False)
        # brackets under the overhang
        for k, z in enumerate((-3.6, -6.2, -8.8, -11.4)):
            w = ss.hull_x(z, 1.8)
            beam(detail, "bracket_%s%d" % (sn, k), v3(side * (w + 0.05), 1.6, z), v3(side * (hw - 0.25), PY - 0.55, z), 0.16, "dark_wood",
                 width=0.2, extend=0.05)
    hx = ss.hull_x(CF, PY - 0.5)
    quad(bone, "pilot_under_front", v3(-hw, PY - 0.5, CF), v3(hw, PY - 0.5, CF), v3(-hw, PY - 0.5, zf), v3(hw, PY - 0.5, zf), 0.06,
         "dark_wood", v3(0, -1, 0), u_dir=v3(1, 0, 0), stretch=False)
    # the balustrade: posts and two rails, open over the crate stair
    r = hw - 0.25
    gap = si.PILOT_RAIL_GAP
    ring_pts = [v3(gap[1], PY, zf - 0.25), v3(r, PY, zf - 0.25), v3(r, PY, za + 0.25), v3(-r, PY, za + 0.25), v3(-r, PY, zf - 0.25),
                v3(gap[0], PY, zf - 0.25)]
    balustrade(bone, "pilot_rail", ring_pts, h=ss.RAIL_H, step=0.55, post="dark_wood", rail="wood")
    for k, p in enumerate((ring_pts[1], ring_pts[2], ring_pts[3], ring_pts[4], ring_pts[0], ring_pts[5])):
        tube(bone, "pilot_newel_%d" % k, p, p + v3(0, ss.RAIL_H + 0.2, 0), 0.24, "dark_wood", sides=4)
        box(bone, "pilot_newel_cap_%d" % k, p + v3(0, ss.RAIL_H + 0.27, 0), (0.3, 0.14, 0.3), "moss")
    # lanterns on the front corner posts (iron arms) and at the stair
    for k, p in enumerate((ring_pts[1], ring_pts[4])):
        side = 1 if p[0] > 0 else -1
        arm0 = p + v3(0, ss.RAIL_H + 0.05, 0)
        arm1 = arm0 + v3(side * 0.45, 0.1, 0.1)
        beam(detail, "rail_lamp_arm_%d" % k, arm0, arm1, 0.06, "iron", extend=0.02)
        hanging_lantern(lanterns_root, "rail_%d" % k, arm1, drop=0.25)


# ================================================================ the cabin
WINDOW_Z = si.WINDOWS[0][:2]
WINDOW_Y = si.WINDOWS[0][2:]


def cabin(bone, detail, lanterns_root):
    """The cabin's outer walls (vertical planks on frame posts) from the mossy ledge up to the pilot deck, a framed
    window in each side; the front wall round the door, a lantern on each side of it."""
    y0, y1 = ss.SHEER_WAIST + 0.1, PY - 0.5
    zz = sorted(set(list(np.linspace(ss.HULL_STERN_Z, CF, 11)) + list(WINDOW_Z)))
    ys = [y0, WINDOW_Y[0], WINDOW_Y[1], y1]
    for side, sn in SIDES:
        for i in range(len(zz) - 1):
            za, zb = zz[i], zz[i + 1]
            for j in range(len(ys) - 1):
                ya, yb = ys[j], ys[j + 1]
                if WINDOW_Z[0] <= (za + zb) / 2 <= WINDOW_Z[1] and j == 1:
                    continue   # the window
                p = [v3(side * (ss.hull_x(z, y) + 0.01), y, z) for z, y in ((za, ya), (zb, ya), (za, yb), (zb, yb))]
                quad(bone, "cabin_wall_%s%d_%d" % (sn, i, j), p[0], p[1], p[2], p[3], 0.1, "cabin_wall", v3(side, 0, 0), u_dir=v3(0, 0, 1),
                     v_dir=v3(0, -1, 0), stretch=False)
        # frame posts and a middle rail
        for k, z in enumerate((ss.HULL_STERN_Z + 0.2, -10.3 + 0.0 if False else WINDOW_Z[0] - 0.12, WINDOW_Z[1] + 0.12, ss.PARTITION_Z,
                               -5.4, CF - 0.12)):
            pts = [v3(side * (ss.hull_x(z, y) + 0.08), y, z) for y in (y0 - 0.1, y1 + 0.1)]
            beam(detail, "cabin_post_%s%d" % (sn, k), pts[0], pts[1], 0.22, "dark_wood", width=0.2, up=v3(0, 0, 1), extend=0.02)
        # the window: lit glass with its cross bars, a frame through the wall's thickness, a sill
        zc, yc = sum(WINDOW_Z) / 2, sum(WINDOW_Y) / 2
        wz, wy = WINDOW_Z[1] - WINDOW_Z[0], WINDOW_Y[1] - WINDOW_Y[0]
        xo = ss.hull_x(zc, yc)
        xi = xo - 0.5
        add_cube(bone, "glow_window_" + sn, v3(side * (xo - 0.2), yc, zc), EYE, (0.03, wy, wz), {"all": None, "+1": "window", "-1": "window"},
                 stretch=True, u_dir=v3(0, 0, side), v_dir=v3(0, -1, 0))
        for k, (dy, dz, sy, sz) in enumerate(((wy / 2 + 0.06, 0, 0.12, wz + 0.24), (-wy / 2 - 0.06, 0, 0.12, wz + 0.24),
                                              (0, wz / 2 + 0.06, wy, 0.12), (0, -wz / 2 - 0.06, wy, 0.12))):
            box(bone, "window_frame_%s%d" % (sn, k), (side * (xo - 0.22), yc + dy, zc + dz), (0.62, sy, sz), "dark_wood")
        box(detail, "window_sill_" + sn, (side * (xo + 0.1), WINDOW_Y[0] - 0.1, zc), (0.3, 0.1, wz + 0.4), "moss")
        box(detail, "window_lintel_" + sn, (side * (xo + 0.08), WINDOW_Y[1] + 0.12, zc), (0.22, 0.14, wz + 0.3), "dark_wood")
    # the front wall: planks round the door, posts, a lintel
    z = CF + 0.01
    x_of = lambda y: ss.hull_x(CF, y) - 0.02  # noqa: E731
    dx0, dx1, dy0, dy1 = si.DOORS[si.CABIN_DOOR][1][0], si.DOORS[si.CABIN_DOOR][1][1], 0.0, 2.0
    panels = (((-1, 0.0, y1), (dx0, 0.0, dy1)), ((1, 0.0, y1), (dx1, 0.0, dy1)))
    for side, sn in SIDES:
        xs = dx1 if side > 0 else dx0
        for j, (ya, yb) in enumerate(((ss.SHEER_WAIST, dy1), (dy1, y1))):
            pa = [v3(side * x_of(y), y, z) for y in (ya, yb)]
            qa = [v3(xs, y, z) for y in (ya, yb)]
            quad(bone, "front_wall_%s%d" % (sn, j), qa[0], pa[0], qa[1], pa[1], 0.1, "cabin_wall", v3(0, 0, 1), u_dir=v3(side, 0, 0),
                 v_dir=v3(0, -1, 0), stretch=False)
        # below the waist the bulwark's inner face is the wall
        quad(bone, "front_wall_low_" + sn, v3(xs, 0.0, z), v3(side * x_of(0.0), 0.0, z), v3(xs, ss.SHEER_WAIST, z),
             v3(side * x_of(ss.SHEER_WAIST), ss.SHEER_WAIST, z), 0.1, "cabin_wall", v3(0, 0, 1), u_dir=v3(side, 0, 0), v_dir=v3(0, -1, 0),
             stretch=False)
        for k, x in enumerate((xs + side * 0.14, side * (x_of(1.5) - 0.12))):
            box(detail, "front_post_%s%d" % (sn, k), (x, (y1 + 0.0) / 2, z + 0.1), (0.24, y1 + 0.05, 0.2), "dark_wood")
        # a lantern on an iron bracket each side of the door
        p = v3(side * 1.65, 2.05, z + 0.08)
        beam(detail, "door_lamp_arm_" + sn, p, p + v3(0, 0.05, 0.42), 0.06, "iron", extend=0.02)
        hanging_lantern(lanterns_root, "door_" + sn, p + v3(0, 0.05, 0.42), drop=0.22)
    quad(bone, "front_wall_top", v3(dx0, dy1, z), v3(dx1, dy1, z), v3(dx0, y1, z), v3(dx1, y1, z), 0.1, "cabin_wall", v3(0, 0, 1),
         u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0), stretch=False)
    box(detail, "door_lintel_out", (0, dy1 + 0.1, z + 0.1), (dx1 - dx0 + 0.5, 0.2, 0.22), "dark_wood")


# ================================================================ the canvas roof and its poles
ROOF_NTH = 28
ROOF_T = (0.0, 0.18, 0.36, 0.54, 0.7, 0.84, 0.94, 1.0)


def pole_foot_top(fx, fz, top, side):
    return v3(side * fx, PY, fz), v3(side * top[0], top[1], top[2])


def canopy(bone, detail, fringe_root):
    """The splayed corner poles and the king post (finials above the canvas), the canvas tent over them (stained,
    patched), its eaves hanging in torn strips."""
    for side, sn in SIDES:
        for k, ((fx, fz), top) in enumerate(zip(ss.POLE_FEET, ss.POLE_TOPS)):
            foot, tp = pole_foot_top(fx, fz, top, side)
            d = norm(tp - foot)
            tube(bone, "pole_%s%d" % (sn, k), foot, tp + d * ss.POLE_TIP, 0.34, "pole", sides=6)
            spike(detail, "pole_finial_%s%d" % (sn, k), tp + d * ss.POLE_TIP, d, 0.55, r=0.1)
            ring(detail, "pole_band_%s%d" % (sn, k), foot + d * 1.2, d, 0.21, 0.07, "iron", n=6)
            box(bone, "pole_foot_%s%d" % (sn, k), foot + v3(0, 0.12, 0), (0.5, 0.24, 0.5), "dark_wood")
    kz = ss.CANOPY_Z
    tube(bone, "king_post", v3(0, PY, kz), v3(0, ss.KING_TOP, kz), 0.42, "pole", sides=8)
    spike(detail, "king_finial", v3(0, ss.KING_TOP, kz), v3(0, 1, 0), 0.8, r=0.13)
    box(bone, "king_post_foot", (0, PY + 0.2, kz), (0.7, 0.4, 0.7), "dark_wood")
    for k, h in enumerate((PY + 1.1, ss.APEX_Y - 1.2)):
        ring(detail, "king_band_%d" % k, v3(0, h, kz), v3(0, 1, 0), 0.25, 0.08, "iron", n=6)
    # the canvas
    ths = [2 * math.pi * i / ROOF_NTH for i in range(ROOF_NTH + 1)]
    for i in range(ROOF_NTH):
        for j in range(len(ROOF_T) - 1):
            a0, a1 = ths[i], ths[i + 1]
            t0, t1 = ROOF_T[j], ROOF_T[j + 1]
            p00, p10 = v3(*ss.roof_point(a0, t0)), v3(*ss.roof_point(a1, t0))
            p01, p11 = v3(*ss.roof_point(a0, t1)), v3(*ss.roof_point(a1, t1))
            mid = (p00 + p10 + p01 + p11) / 4
            out = norm(v3(mid[0], 3.0, mid[2] - kz))
            quad(bone, "canvas_%d_%d" % (i, j), p00, p10, p01, p11, 0.06, "canvas", out, back="canvas_under", stretch=False,
                 overlap=(1.04, 1.04))
    # ridges of the canvas over the poles (the cloth is pulled up there): a seam from the apex to each pole top
    for k, a in enumerate(ss.corner_angles()):
        pts = [v3(*ss.roof_point(a, t)) + v3(0, 0.05, 0) for t in (0.05, 0.4, 0.75, 0.94)]
        polyline(detail, "roof_seam_%d" % k, pts, 0.1, "rope_dark", sides=4)
    # the torn strips hanging from the eaves, two staggered rows, in bones that sway (streamer_wave)
    rng = random.Random(77)
    nb = 8
    bones = [Bone("fringe_%d" % b, origin=tuple(v3(*ss.roof_point(2 * math.pi * (b + 0.5) / nb, 1.0))), parent=fringe_root) for b in range(nb)]
    n = 56
    for row, (t, inset, lk) in enumerate(((1.0, 0.0, 1.0), (0.985, 0.12, 0.85), (0.8, 0.0, 0.55), (0.62, 0.0, 0.4))):
        for i in range(n):
            a0, a1 = 2 * math.pi * (i + 0.5 * row) / n, 2 * math.pi * (i + 1 + 0.5 * row) / n
            p0, p1 = v3(*ss.roof_point(a0, t)), v3(*ss.roof_point(a1, t))
            for p in (p0, p1):
                r = math.hypot(p[0], p[2] - kz)
                p[0] -= p[0] / r * inset
                p[2] -= (p[2] - kz) / r * inset
            L = (ss.FRINGE[0] + (ss.FRINGE[1] - ss.FRINGE[0]) * rng.random() ** 1.6) * lk
            q0, q1 = p0 - v3(0, L, 0), p1 - v3(0, L * rng.uniform(0.8, 1.2), 0)
            mid = (p0 + p1) / 2
            out = norm(v3(mid[0], 0, mid[2] - kz))
            b = bones[int(((a0 + a1) / 2) / (2 * math.pi) * nb) % nb]
            if row >= 2 and rng.random() < 0.45:
                continue   # the inner strips hang here and there only
            c = quad(b, "fringe_%d_%d" % (row, i), p0 - v3(0, 0.06, 0), p1 - v3(0, 0.06, 0), q0, q1, 0.02, "fringe", out, stretch=True)
            if c is not None:
                c.faces["up"] = c.faces["down"] = None


def derricks(bone, detail):
    """The two long inclined derricks at the stern, ropes from their tips down to the tubes and to the canopy."""
    for side, sn in SIDES:
        (fx, fy, fz), (tx, ty, tz) = ss.DERRICKS[0]
        foot, tp = v3(side * fx, fy, fz), v3(side * tx, ty, tz)
        d = norm(tp - foot)
        tube(bone, "derrick_" + sn, foot, tp, 0.3, "pole", sides=6)
        spike(detail, "derrick_finial_" + sn, tp, d, 0.5, r=0.09)
        box(bone, "derrick_foot_" + sn, foot + v3(0, 0.15, 0), (0.45, 0.3, 0.45), "dark_wood")
        for k, (x, y) in enumerate(((0.95, 2.55), (0.95, 1.1))):
            end = v3(side * (x + 0.6), y + 0.25, ss.TUBE_Z[1] + 1.2)
            rope(detail, "derrick_rope_%s%d" % (sn, k), tp - d * 0.3, end, d=0.07, sag=0.12)
        # a rope from the tip to the roof's rear pole top
        top = v3(side * ss.POLE_TOPS[1][0], ss.POLE_TOPS[1][1], ss.POLE_TOPS[1][2])
        rope(detail, "derrick_stay_" + sn, tp - d * 0.2, top, d=0.06, sag=0.25)
    # a cross bar between the derricks a third of the way up
    (fx, fy, fz), (tx, ty, tz) = ss.DERRICKS[0]
    t = 0.32
    a = v3(fx + (tx - fx) * t, fy + (ty - fy) * t, fz + (tz - fz) * t)
    beam(bone, "derrick_bar", a, v3(-a[0], a[1], a[2]), 0.18, "dark_wood", width=0.18, extend=0.15)


# ================================================================ pennants
PENNANT_COLOURS = ("pennant_beige", "pennant_beige", "pennant_red", "pennant_black", "pennant_red", "pennant_beige", "pennant_black",
                   "pennant_red", "pennant_beige")


def pennants(root):
    """Strings of tattered pennants from the bow beam's tip to the roof's front poles (each pennant in its own bone)."""
    y1, z1 = ss.BOWSPRIT[1]
    start = v3(0, y1 + 0.05, z1 - 0.15)
    for side, sn in SIDES:
        top = v3(side * ss.POLE_TOPS[0][0], ss.POLE_TOPS[0][1] - 0.2, ss.POLE_TOPS[0][2])
        pts = sag_points(start, top, 1.1, 24)
        bone_s = Bone("pennants_" + sn, parent=root)
        polyline(bone_s, "pennant_rope_" + sn, pts, 0.06, "rope", sides=4)
        n = len(PENNANT_COLOURS)
        for k in range(n):
            f = 0.18 + 0.75 * k / (n - 1)
            idx = f * (len(pts) - 1)
            i0 = int(idx)
            a = pts[i0] + (pts[min(i0 + 1, len(pts) - 1)] - pts[i0]) * (idx - i0)
            d = norm(pts[min(i0 + 1, len(pts) - 1)] - pts[i0])
            w, h = 0.62, 0.95
            pb = Bone("pennant_%s%d" % (sn, k), origin=tuple(a), parent=bone_s)
            p0, p1 = a - d * w / 2, a + d * w / 2
            quad(pb, "pennant_%s%d" % (sn, k), p0, p1, p0 - v3(0, h, 0), p1 - v3(0, h, 0), 0.02, PENNANT_COLOURS[k], v3(side, 0, 0),
                 stretch=True, u_dir=d, v_dir=v3(0, -1, 0))


# ================================================================ the stern tubes
def tubes(bone, detail, fans_root):
    """Five bronze tubes bound with iron on the transom, flared mouths with a glowing throat and a fan inside."""
    z0, z1 = ss.TUBE_Z
    for k, (x, y, r) in enumerate(ss.TUBES):
        end = ss.TUBE_CENTRE_END if r < 0.5 else z1
        a, b = v3(x, y, z0), v3(x, y, end)
        tube(bone, "tube_%d" % k, a, b, 2 * r, "tube", sides=8)
        for j, t in enumerate((0.12, 0.45, 0.78)):
            p = a + (b - a) * t
            ring(detail, "tube_band_%d_%d" % (k, j), p, v3(0, 0, 1), r + 0.03, 0.12, "iron", n=8)
        # the flared mouth
        ring(bone, "tube_lip_%d" % k, b - v3(0, 0, 0.1), v3(0, 0, 1), r * 1.12, 0.22, "bronze", n=10)
        disc(bone, "glow_tube_throat_%d" % k, b + v3(0, 0, 0.35), v3(0, 0, 1), r * 0.82, 0.04, "tube_mouth", sides=10)
        fan = Bone("tube_fan_%d" % k, origin=tuple(b + v3(0, 0, 0.18)), parent=fans_root)
        for j in range(4):
            ang = math.pi / 2 * j + 0.3
            d = v3(math.cos(ang), math.sin(ang), 0)
            add_cube(fan, "tube_fan_%d_%d" % (k, j), b + v3(0, 0, 0.18) + d * r * 0.4, np.column_stack([d, np.cross(v3(0, 0, 1), d), v3(0, 0, 1)]),
                     (r * 0.75, 0.16, 0.04), "iron")
        disc(fan, "tube_fan_hub_%d" % k, b + v3(0, 0, 0.18), v3(0, 0, 1), 0.1, 0.08, "bronze", sides=6)
    # the cradle binding them to the transom: two iron straps round the bundle and a wooden saddle
    for j, z in enumerate((z0 - 0.6, z0 - 3.0)):
        pts = [v3(1.75, 3.35, z), v3(1.75, 0.3, z), v3(-1.75, 0.3, z), v3(-1.75, 3.35, z), v3(1.75, 3.35, z)]
        polyline(detail, "tube_strap_%d" % j, pts, 0.1, "iron", sides=4)
    box(bone, "tube_saddle", (0, 0.2, z0 - 0.7), (3.6, 0.3, 1.2), "dark_wood")


# ================================================================ the wings
WING_BONES = {}


def wing(root, wing_def, side, sn):
    """A big soft wing: the upper spar and the leading spar from the root, ribs fanning out to the scalloped free
    edge, the canvas bellying out between them; iron spikes at the spars' and the ribs' ends."""
    name = wing_def[0]
    R, T, P = (v3(*p) for p in ss.wing_frame(wing_def, side))
    b = Bone("%s_%s" % (name, sn), origin=tuple(R), parent=root)
    WING_BONES[b.name] = b
    n = norm(np.cross(T - R, P - R))
    if n[0] * side < 0:
        n = -n
    rays = [T] + [T + (P - T) * f for f in ss.WING_RIBS] + [P]
    # spars and ribs
    tube(b, "%s_spar_top_%s" % (name, sn), R, T, 0.3, "rib", sides=6, extend=0.08)
    tube(b, "%s_spar_lead_%s" % (name, sn), R, P, 0.32, "rib", sides=6, extend=0.08)
    spike(b, "%s_spike_top_%s" % (name, sn), T, norm(T - R), 0.6, r=0.1)
    spike(b, "%s_spike_tip_%s" % (name, sn), P, norm(P - R), 0.8, r=0.11)
    for k, E in enumerate(rays[1:-1]):
        mid = R + (E - R) * 0.5 + n * ss.WING_BILLOW * 0.5
        polyline(b, "%s_rib_%s%d" % (name, sn, k), [R, mid, E], 0.18, "rib", sides=4)
        spike(b, "%s_rib_spike_%s%d" % (name, sn, k), E, norm(E - R), 0.35, r=0.07)
    # the canvas between consecutive rays
    nu, ns = 4, 6
    for k in range(len(rays) - 1):
        A, B = rays[k], rays[k + 1]
        L = np.linalg.norm(B - A)
        wk = min(1.0, L / max(np.linalg.norm(A - R), np.linalg.norm(B - R)))   # the texture keeps its proportions
        vo = (0.23 * k) % max(1e-6, 1.0 - wk)

        def edge(u, A=A, B=B, L=L):
            p = A + (B - A) * u
            return p + norm(R - p) * (ss.WING_SCALLOP * L * math.sin(math.pi * u))

        def Q(u, s, edge=edge):
            e = edge(u)
            bel = ss.WING_BILLOW * math.sin(math.pi * min(1.0, s * 1.1)) * (0.55 + 0.45 * math.sin(math.pi * u))
            return R + (e - R) * s + n * bel
        for i in range(nu):
            for j in range(ns):
                u0, u1, s0, s1 = i / nu, (i + 1) / nu, j / ns, (j + 1) / ns
                # the quad's long side along the ray (the fan's slivers are sheared: a rectangle along the ray covers them)
                quad(b, "%s_canvas_%s%d_%d_%d" % (name, sn, k, i, j), Q(u0, s0), Q(u0, s1), Q(u1, s0), Q(u1, s1), 0.04, "wing", n,
                     stretch=True, overlap=(1.03, 1.12), sub=(s0, vo + u0 * wk, s1, vo + u1 * wk), u_dir=norm(A + B - 2 * R),
                     v_dir=norm(B - A))
    # the hinge: an iron bracket on the hull
    box(b, "%s_hinge_%s" % (name, sn), R + v3(-side * 0.1, 0.05, 0), (0.42, 0.42, 0.7), "iron")
    return b


def wings(root):
    for wdef in ss.WINGS:
        for side, sn in SIDES:
            wing(root, wdef, side, sn)


# ================================================================ rooms (grid surfaces), ladder, doors, stairs
OPEN_KINDS = (si.DRY, si.LADDER)
ROOM_MATERIALS = {
    "common_room": ("in_wall", "in_floor", "in_ceil"), "bedroom": ("in_wall", "in_floor", "in_ceil"),
    "hold": ("in_wall_hold", "in_floor_hold", "in_ceil"),
}
SHAFT_MAT = ("in_wall_hold", "in_floor_hold", "in_ceil")


def room_at(x, y, z):
    for name, (x0, x1, y0, y1, z0, z1) in si.ROOMS.items():
        if x0 - 0.01 <= x <= x1 + 0.01 and y0 - 0.01 <= y <= y1 + 0.01 and z0 - 0.01 <= z <= z1 + 0.01:
            return name
    return None


def surfaces(rooms_bone, g):
    """Walls, floors and ceilings of the rooms on the cell boundaries (solid next to a room cell)."""
    k = g.k
    solid = k == si.SOLID
    roomish = np.isin(k, OPEN_KINDS) | (k >= si.DOOR)
    near = roomish.copy()
    for a in range(3):
        for s in (1, -1):
            near |= np.roll(roomish, s, axis=a)
    opened = roomish | ((k == si.FURNITURE) & near)
    C = si.CELL
    origin = (si.X0, si.Y0, si.Z0)
    mats = [SHAFT_MAT] + [m for m in dict.fromkeys(ROOM_MATERIALS.values()) if m != SHAFT_MAT]
    mat_index = np.zeros(k.shape, dtype=np.int16)
    for name, box_ in si.ROOMS.items():
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
                        ry0, ry1 = (si.ROOMS[room][2], si.ROOMS[room][3]) if room else (lo[1], hi[1])
                        hgt = max(0.5, ry1 - ry0)
                        v0 = min(1.0, max(0.0, (ry1 - hi[1]) / hgt))
                        v1 = min(1.0, max(v0 + 0.01, (ry1 - lo[1]) / hgt))
                        sub = ((hz0 % MAX_TILE) / MAX_TILE, v0, (hz1 % MAX_TILE + 1) / MAX_TILE, v1)
                    set_sub(cube, sub)
                    count += 1
    return count


def ladders(bone):
    for name, (x0, x1, y0, y1, z0, z1) in si.LADDERS.items():
        wall = z0
        pa = lambda y: v3(x0 + 0.15, y, wall + 0.08)  # noqa: E731
        pb = lambda y: v3(x1 - 0.15, y, wall + 0.08)  # noqa: E731
        beam(bone, "lit_ladder_%s_rail_a" % name, pa(y0), pa(y1 + 0.45), 0.08, "rung")
        beam(bone, "lit_ladder_%s_rail_b" % name, pb(y0), pb(y1 + 0.45), 0.08, "rung")
        y, i = y0 + 0.25, 0
        while y < y1 - 0.1:
            beam(bone, "lit_ladder_%s_rung_%d" % (name, i), pa(y), pb(y), 0.07, "rung")
            y += 0.5
            i += 1


def doors(root):
    anims = []
    for d, (name, box_) in si.DOORS.items():
        x0, x1, y0, y1, z0, z1 = box_
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        flat = sy <= min(sx, sz) + 1e-6
        if flat:
            hinge = v3((x0 + x1) / 2, y1, z0)
            bone = Bone("door_%d" % d, origin=tuple(hinge), parent=root)
            add_cube(bone, "door_%d" % d, v3((x0 + x1) / 2, y1 - 0.06, (z0 + z1) / 2), EYE, (sx - 0.04, 0.1, sz - 0.04),
                     {"all": "iron", "+2": "grate", "-2": "grate"}, stretch=True, u_dir=v3(1, 0, 0), v_dir=v3(0, 0, 1))
            anims.append(gg.animation("door_%d" % d, 1.0, "hold", [(bone, [gg.rot_kf(0.0, (0, 0, 0)), gg.rot_kf(1.0, (-110, 0, 0))])]))
            continue
        along_z = sx < sz
        depth = (sx if along_z else sz) + 0.12
        w = 0.16
        p0, p1 = (z0, z1) if along_z else (x0, x1)
        pre = "" if d == si.CABIN_DOOR else "lit_"
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


def stairs(outside, inside):
    for st_ in si.STAIRS:
        name, x0, x1, zs, d, y0, n = st_
        interior = n < 0
        bone = inside if interior else outside
        pre = "lit_" if interior else ""
        for k, (sx0, sx1, sz0, sz1, top) in enumerate(si.stair_steps(st_)):
            bottom = top - 0.5 if interior else y0
            c = v3((sx0 + sx1) / 2, (top + bottom) / 2, (sz0 + sz1) / 2)
            if interior:
                add_cube(bone, "%sstair_%s_%d" % (pre, name, k), c, EYE, (sx1 - sx0, top - bottom, sz1 - sz0), {"all": "dark_wood", "+2": "in_floor"},
                         u_dir=v3(1, 0, 0))
            else:
                # crate steps: light planked boxes with dark edges (as on the reference)
                add_cube(bone, "%sstair_%s_%d" % (pre, name, k), c, EYE, (sx1 - sx0, top - bottom, sz1 - sz0),
                         {"all": "light_wood", "+2": "deck"}, u_dir=v3(1, 0, 0))
                for j, dx in enumerate((-0.5, 0.5)):
                    box(outside, "stair_%s_%d_edge_%d" % (name, k, j), (c[0] + dx * (sx1 - sx0), top - 0.04, c[2]), (0.08, 0.08, sz1 - sz0 + 0.02),
                        "dark_wood")
        if not interior:
            # a hand rope on posts along the open (inboard) side
            steps = si.stair_steps(st_)
            pts = [v3(x1 + 0.05, s[4] + 0.95, (s[2] + s[3]) / 2) for s in steps[::2]] + [v3(x1 + 0.05, steps[-1][4] + 0.95, steps[-1][2])]
            for k, p in enumerate(pts):
                tube(outside, "stair_post_%s_%d" % (name, k), p - v3(0, 0.95, 0), p, 0.12, "dark_wood", sides=4)
            polyline(outside, "stair_rope_" + name, pts, 0.07, "rope", sides=4)


# ================================================================ helm
def helm(root, bone):
    """The wheel on its pedestal at the front of the pilot deck, facing the bow; a small binnacle beside it."""
    z = ss.HELM_Z
    box(bone, "helm_pedestal", (0, PY + 0.62, z - 0.05), (0.42, 1.24, 0.36), {"all": "dark_wood", "+2": "moss"})
    box(bone, "helm_pedestal_foot", (0, PY + 0.06, z - 0.05), (0.62, 0.12, 0.52), "dark_wood")
    c = v3(0, PY + 1.75, z + 0.22)
    wb = Bone("helm_wheel", origin=tuple(c), parent=root)
    ship_wheel(wb, "helm_wheel", c, (0, 0, 1), r=0.62, region="wood")
    tube(bone, "helm_axle", c - v3(0, 0, 0.3), c + v3(0, 0, 0.06), 0.12, "iron", sides=6)


# ================================================================ furniture made for the skiff
def _named(fn):
    return lambda bone_, **kw: fn(bone_, kw.pop("name"), **kw)


def barrel(bone, name, p, h=0.95, r=0.36):
    """An upright barrel: staves, two iron hoops, a lid."""
    p = v3(*p)
    tube(bone, "lit_" + name, p, p + v3(0, h, 0), 2 * r, "wood", sides=8)
    tube(bone, "lit_" + name + "_belly", p + v3(0, h * 0.3, 0), p + v3(0, h * 0.7, 0), 2 * r + 0.06, "wood", sides=8)
    for k, t in enumerate((0.15, 0.85)):
        tube(bone, "lit_%s_hoop_%d" % (name, k), p + v3(0, h * t - 0.04, 0), p + v3(0, h * t + 0.04, 0), 2 * r + 0.05, "iron", sides=8)
    disc(bone, "lit_" + name + "_lid", p + v3(0, h + 0.01, 0), (0, 1, 0), r * 0.92, 0.03, "end_grain", sides=8)


def crate(bone, name, p, s=0.8, yaw=0.0):
    p = v3(*p)
    R = gg.ry(yaw)
    add_cube(bone, "lit_" + name, p + v3(0, s / 2, 0), R, (s, s, s), "light_wood")
    for k, (a, b) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        add_cube(bone, "lit_%s_edge_%d" % (name, k), p + R @ v3(a * (s / 2 - 0.03), s / 2, b * (s / 2 - 0.03)), R, (0.08, s + 0.02, 0.08), "dark_wood")


def sack(bone, name, p, s=0.5):
    p = v3(*p)
    add_cube(bone, "lit_" + name, p + v3(0, s * 0.4, 0), EYE, (s, s * 0.8, s * 0.8), "sack")
    add_cube(bone, "lit_" + name + "_neck", p + v3(0, s * 0.85, 0), EYE, (s * 0.35, s * 0.2, s * 0.35), "sack")


def coil(bone, name, p, r=0.3):
    p = v3(*p)
    for k in range(3):
        ring(bone, "lit_%s_%d" % (name, k), p + v3(0, 0.05 + 0.07 * k, 0), (0, 1, 0), r - 0.04 * k, 0.08, "rope", n=8)


def rug(bone, name, p, w, l, region="carpet"):
    p = v3(*p)
    add_cube(bone, "lit_" + name, p + v3(0, 0.012, 0), EYE, (w, 0.02, l), {"+2": region}, stretch=True, u_dir=v3(1, 0, 0), v_dir=v3(0, 0, 1))


def bracket(bone, name, p, side):
    p = v3(*p)
    beam(bone, "lit_" + name, p + v3(side * 0.1, 0.3, 0), p + v3(-side * 0.05, 0.62, 0), 0.05, "iron")


def shelf_board(bone, name, p, w, along=(0, 0, 1), d=0.3):
    p = v3(*p)
    a = norm(v3(*along))
    add_cube(bone, "lit_" + name, p, np.column_stack([a, v3(0, 1, 0), np.cross(a, v3(0, 1, 0))]), (w, 0.06, d), "wood")


def bunk_bed(bone, name, p, l=2.0, w=1.0, yaw=0.0):
    cf.captain_bed(bone, name, p, l=l, w=w)


FURNITURE_BUILDERS = {
    "barrel": barrel, "crate": crate, "sack": sack, "coil": coil, "rug": rug, "bracket": bracket, "shelf": shelf_board,
    "bed": _named(cf.captain_bed), "chest": _named(cf.chest), "chart_sheet": _named(cf.chart_sheet),
}


def fallbacks(root):
    """Stand-ins of the decoration blocks, shown only when their mod is missing on a client."""
    for i, b in enumerate(sd.BLOCKS):
        x0, x1, y0, y1, z0, z1 = sd.footprint(b["block"], b["x"], b["y"], b["z"], b["yaw"], b["scale"])
        bone = Bone("fallback_%d" % i, parent=root)
        pre = "glow" if b["glow"] else "lit"
        add_cube(bone, "%s_fallback_%d" % (pre, i), v3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), EYE,
                 (max(0.04, x1 - x0), max(0.04, y1 - y0), max(0.04, z1 - z0)), sd.FALLBACK_REGION.get(b["block"], "wood"), stretch=True)


# ================================================================ build
def build(g):
    root = Bone("rustic_skiff")
    hull_b = Bone("hull", parent=root)
    detail = Bone("detail", parent=root)
    deck_b = Bone("decks", parent=root)
    cabin_b = Bone("cabin", parent=root)
    pilot_b = Bone("pilot", parent=root)
    canopy_b = Bone("canopy", parent=root)
    fringe_b = Bone("fringe", parent=root)
    lean_b = Bone("lean_to", parent=root)
    tubes_b = Bone("tubes", parent=root)
    fans_b = Bone("fans", parent=root)
    lanterns = Bone("lanterns", parent=root)
    rooms = Bone("rooms", parent=root)
    fittings = Bone("fittings", parent=root)
    furniture = Bone("furniture", parent=root)
    hull(hull_b, detail)
    transom(hull_b, detail)
    caps(hull_b, detail)
    boards(hull_b, detail)
    chains(detail, lanterns)
    lean_to(lean_b, detail)
    decks(deck_b, detail, g)
    pilot_deck(pilot_b, detail, lanterns)
    cabin(cabin_b, detail, lanterns)
    canopy(canopy_b, detail, fringe_b)
    derricks(canopy_b, detail)
    pennants(root)
    tubes(tubes_b, detail, fans_b)
    wings(root)
    stairs(deck_b, fittings)
    m = surfaces(rooms, g)
    ladders(fittings)
    helm(root, pilot_b)
    fallbacks(root)
    for k, (builder, kwargs, solid) in enumerate(sd.CUSTOM):
        kw = dict(kwargs)
        kw.setdefault("name", "%s_%d" % (builder, k))
        FURNITURE_BUILDERS[builder](furniture, **kw)
    return root, m


def _loop_keys(length, n, fn):
    ts = [length * i / n for i in range(n + 1)]
    return [(t, fn(t if i < n else 0.0)) for i, t in enumerate(ts)]


WING_FLAP = 7.0       # degrees each way: the wings beat slowly while under way
WING_STEER = 8.0
WING_PITCH = 6.0


def build_animations(root):
    """The model's animations (driven by the mod, see ShipRenderer):
    engine (time = the engine's phase, which only advances with the speed: still when parked) - the fans spinning in
      the tubes' mouths, the four wings beating slowly (out and in about their hinges);
    steer / elevator (hold, 0..2 = helm / climb from -1 to 1) - the helm wheel and the rear wings (rudders); the four
      wings pitching with the climb;
    lantern_sway, streamer_wave (time = the game time) - the hanging lanterns; the pennants and the torn strips of the
      roof's eaves."""
    kf, rot_kf, animation, find = gg.kf, gg.rot_kf, gg.animation, gg.find
    anims = []
    tracks = []
    for k in range(len(ss.TUBES)):
        tracks.append((find(root, "tube_fan_%d" % k), [rot_kf(t, (0, 0, -a)) for t, a in ((0.0, 0), (0.5, 90), (1.0, 180), (1.5, 270), (2.0, 360))]))
    # the wings beat: about the fore-and-aft axis through their hinges, out (tips up and out) then in, port and starboard
    # mirrored (bb x is the ship's -x, so a ship rotation by a about z is a bb rotation by -a)
    for wdef in ss.WINGS:
        for side, sn in SIDES:
            b = find(root, "%s_%s" % (wdef[0], sn))
            ph = 0.0 if wdef[0] == "wing_fore" else 0.6

            def flap(t, side=side, ph=ph):
                return -side * WING_FLAP * math.sin(2 * math.pi * t / 2.0 + ph)
            tracks.append((b, [rot_kf(t, (0, 0, v)) for t, v in _loop_keys(2.0, 16, flap)]))
    anims.append(animation("engine", 2.0, "loop", tracks))
    steer = [(find(root, "helm_wheel"), [rot_kf(0.0, (0, 0, -150)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 0, 150))])]
    for side, sn in SIDES:
        steer.append((find(root, "wing_aft_" + sn), [rot_kf(0.0, (0, -WING_STEER, 0)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, WING_STEER, 0))]))
    anims.append(animation("steer", 2.0, "hold", steer))
    anims.append(animation("elevator", 2.0, "hold", [
        (find(root, "%s_%s" % (w[0], sn)), [rot_kf(0.0, (-WING_PITCH, 0, 0)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (WING_PITCH, 0, 0))])
        for w in ss.WINGS for side, sn in SIDES]))
    tracks = []
    lan = find(root, "lanterns")
    for k, b in enumerate(c for c in lan.children if c.name.startswith("lantern_")):
        sh = (0.37 * k) % 4.0
        keys = [rot_kf(t, (5 * math.sin(2 * math.pi * (t + sh) / 4.0), 0, 4 * math.cos(2 * math.pi * (t + sh) / 4.0))) for t in (0.0, 1.0, 2.0, 3.0, 4.0)]
        tracks.append((b, keys))
    anims.append(animation("lantern_sway", 4.0, "loop", tracks))
    tracks = []
    w = 2 * math.pi / 3.0
    k = 0
    for sn in ("p", "s"):
        for b in find(root, "pennants_" + sn).children:
            sh = 0.7 * k
            k += 1
            tracks.append((b, [rot_kf(t, (6 * math.sin(w * t + sh), 0, 4 * math.cos(w * t + sh))) for t in (0.0, 0.75, 1.5, 2.25, 3.0)]))
    for j, b in enumerate(find(root, "fringe").children):
        sh = 1.1 * j
        tracks.append((b, [rot_kf(t, (2.0 * math.sin(w * t + sh), 0, 1.5 * math.cos(w * t + sh))) for t, _ in _loop_keys(3.0, 8, lambda t: 0)]))
    anims.append(animation("streamer_wave", 3.0, "loop", tracks))
    return anims


def check_axes(root):
    return gl.check_axes(root)


def main():
    if os.environ.get("SKIFF_FAST"):   # quick previews: no z-fighting pass
        import zfight
        zfight.fix = lambda root: 0
    g = si.build()
    sd.build()
    sd.apply_to_grid(g)
    sd.write(os.path.join(ROOT, sd.DECOR_PATH))
    size = g.write(os.path.join(ROOT, si.GRID_PATH))
    reached, total = si.walkable_report(g)
    unreachable = [name for name, n in reached.items() if not n]
    print("decor blocks:", len(sd.BLOCKS), "seats:", len(sd.SEATS), "standing places:", total, "unreachable:", unreachable)
    root, m = build(g)
    anims = build_animations(root)
    anims += doors(root)
    bad = check_axes(root)
    if bad:
        print("WARNING: %d cubes with skewed axes, e.g." % len(bad), bad[:8])
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    tex_path = os.path.join(tex_dir, "entity/rustic_skiff.png")
    st.make_texture(tex_path)
    st.make_item_icon(os.path.join(tex_dir, "item/rustic_skiff.png"))
    with open(tex_path, "rb") as f:
        png = f.read()
    textures = [gn.texture_entry("rustic_skiff.png", st.SIZE, png, "entity", "rustic_skiff.png")]
    textures[0]["id"] = "0"
    out = [os.path.join(ROOT, "blockbench/rustic_skiff.bbmodel"),
           os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/rustic_skiff.bbmodel")]
    if os.environ.get("SKIFF_OUT"):
        out = [os.environ["SKIFF_OUT"]]
    model = gn.export(root, anims, textures, out, name="rustic_skiff", visible_box=(50, 32, 0))
    print("grid bytes:", size, "grid surfaces:", m, "cubes:", len(model["elements"]), "animations:", len(model["animations"]))


if __name__ == "__main__":
    main()
