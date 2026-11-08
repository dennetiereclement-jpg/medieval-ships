#!/usr/bin/env python3
"""Generates the Fortress Ship (fortress_ship) Blockbench model, its textures, its item icon, its interior grid and its
furniture.

Usage:  python3 tools/generate_fortress.py

Outputs:
  blockbench/fortress_ship.bbmodel                                             (editable, textures embedded)
  src/main/resources/assets/medievalships/models/entity/fortress_ship.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/fortress_ship.png
  src/main/resources/assets/medievalships/textures/entity/fortress_ship_sails.png
  src/main/resources/assets/medievalships/textures/item/fortress_ship.png
  src/main/resources/assets/medievalships/interiors/fortress_ship.grid         (collisions, dry rooms, doors)
  src/main/resources/assets/medievalships/interiors/fortress_ship_decor.json   (furniture of the mods, seats)

References: the three pictures of the "Navire forteresse" (docs/Fortress_PLAN.md): a floating castle that keeps a
ship's shape. A massive dark-wood hull clad with grey stone: a stone wale at the waterline, a heavy studded stone
belt at the deck edge, vertical stone ribs between red panels, iron straps; crenellated stone parapets and merlons
along the waist, a raised forecastle with a wooden balustrade and a stone beak at the head of the strongly raked
stem; a two storey stern castle in stone (lit windows, a keep with corbelled battlements) and a turret of dark timber
with a pointed red tiled roof and a lantern on its finial; three masts with red square sails bordered and striped
with white, a beige castle tower with a gate on the fore and main courses, a white jib with a red band, red
swallow-tailed pennants at the mastheads, fighting tops with stone merlons, rope ladders; red banners with the
white tower along the sides and at the stern, heater shields on the bow, a banner from the bowsprit; a cargo crane
with a hanging crate on the mizzen; lanterns on the rails, the castle and the turret. Inside, the captain's cabin
under the quarterdeck, the officers' room in the keep, the turret, the crew's mess under the forecastle, the cargo
hold and the crew quarters on the lower deck; their walls, floors and ceilings are drawn on the boundaries of the
interior grid (tools/fortress_interior.py): what is drawn is what collides.

Bones used by the mod (keep their names when editing in Blockbench):
  sail_* (sail_wind, sail_furl)  helm_wheel, rudder (steer)  flag_*, flag_*_tip (flag_wave: the pennants)
  lantern_* (lantern_sway; the banners and the hanging crate sway with them)   door_<k> (door k: 0 = closed, 1 = open)
  rope_slack_* (rope_sway: x axis along the rope, rotated about it)   rooms, furniture, fittings, detail
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
import generate_corsair as gc  # noqa: E402   (generic helpers only: lanterns, sail patches, ladders, slack ropes, furniture)
import ship_details as sd  # noqa: E402
import fortress_shape as fs  # noqa: E402
import fortress_interior as fi  # noqa: E402
import fortress_texture as ft  # noqa: E402
import fortress_decor as fd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "fortress_ship"
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/%s/%d" % (NAME, _uuid_counter[0])))


gg.new_uuid = new_uuid
gn.new_uuid = new_uuid
gc.new_uuid = new_uuid
REGIONS = {k: (0,) + r for k, r in ft.REGIONS.items()}
REGIONS.update({k: (1,) + r for k, r in ft.SAIL_REGIONS.items()})   # the sails: second texture
gn.REGIONS = REGIONS
gn.SIZE = ft.SIZE

v3, norm, Bone, add_cube, beam, board = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam, gg.board
rx, ry, rz = gg.rx, gg.ry, gg.rz
round_bar, cap_rail, disc, turned, polyline, bezier = gn.round_bar, gn.cap_rail, gn.disc, gn.turned, gn.polyline, gn.bezier
lantern, patch_sail, ladder, grating, slack_rope = gc.lantern, gc.patch_sail, gc.ladder, gc.grating, gc.slack_rope
EYE = np.eye(3)
SIDES = ((1, "p"), (-1, "s"))
DECK_AXES = np.column_stack([v3(0, 0, 1), v3(0, 1, 0), v3(-1, 0, 0)])

M, L, F, Q, K, C = fs.MAIN_DECK_Y, fs.LOWER_FLOOR_Y, fs.FORECASTLE_Y, fs.QUARTERDECK_Y, fs.KEEP_Y, fs.CABIN_FLOOR_Y
CF, KF, FF = fs.CABIN_FRONT_Z, fs.KEEP_FRONT_Z, fs.FC_FRONT_Z
TZ = fs.TRANSOM_Z
BOW_Z = fs.FORE_SCALE - 0.02   # where the planking closes on the stem
HEAD_Z = fs.STEM_HEAD_Z
BRACE = math.radians(38)       # square yards braced round (port arms aft): the sails show their faces on the side views
RNG = random.Random(4242)
GANGPLANK_Z = (-0.2, 3.4)       # starboard: no merlon nor rail over the boarding plank (tools/fortress_gangplank.py)


# ---------------------------------------------------------------- hull geometry
def lift(z):
    """Rise of the sheer above the waist at z (0 aft of the forecastle)."""
    return max(0.0, fs.sheer_y(z) - fs.WAIST_TOP)


def deck_y(z):
    """The open deck inboard of the bulwark at z."""
    if z < KF:
        return K
    if z < CF:
        return Q
    if z > FF:
        return F
    return M


def hull_rows(z):
    """Points (x, y) of the outer hull section at z (one side, keel to sheer) and the region of each strake: dark wood
    under the water, the stone wale's course, a dark strake, the red panels, the studded strake, the stone belt."""
    ys = fs.sheer_y(z)
    pts = []
    for fx, fy in ((0.0, 1.0), (0.5, 0.88), (0.82, 0.5), (0.97, 0.1)):
        y = fy * fs.keel_y(min(z, fs.HALF_LENGTH + 0.6))
        zz = z - fs.rake(z, y)
        w, yk = fs.half_width(zz), fs.keel_y(min(zz, fs.HALF_LENGTH + 0.6))
        pts.append((max(0.16, fx * w), fy * yk))
    regs = ["hull_brown", "hull_brown", "hull_brown"]
    lf = lift(z)
    levels = [(0.2, "strake_brown2"), (0.85 + 0.3 * lf, "strake_brown"), (1.5 + 0.45 * lf, "strake_brown2"), (3.3 + 0.8 * lf, "red_panel"),
              (4.35 + 0.9 * lf, "studs"), (ys, "stone")]
    for y, reg in levels:
        y = min(y, ys - 0.06 * (len(levels) - len(regs) + 3))
        y = max(y, pts[-1][1] + 0.08)
        pts.append((max(0.16, fs.hull_x(z, y)), y))
        regs.append(reg)
    return pts, regs


STRETCHED = ("strake_brown", "strake_brown2")


def strake(bone, name, a0, a1, b0, b1, th, region, outward, overlap=1.03, inner=None):
    cube = board(bone, name, a0, a1, b0, b1, th, region, outward, overlap=overlap, inner=inner)
    if region in STRETCHED:
        for f, spec in cube.faces.items():
            if spec is not None and spec["region"] == region:
                spec["stretch"] = True
                spec["v_dir"] = v3(0, -1, 0)
    return cube


STATIONS = [TZ, -18.9, -18.0, -17.0, -15.8, -14.4, -13.0, -11.5, -10.0, -9.0, -7.5, -6.0, -4.5, -3.0, -1.5, 0.0, 1.5, 3.0, 4.5, 6.0,
            7.5, 9.0, 10.5, 12.0, 13.3, 14.5, 15.5, 16.4, 17.1, 17.7, 18.1, BOW_Z, 19.0, 19.5, 20.0, 20.5, 21.0, 21.5, 22.0, 22.5, 22.8]


def hp(z, y, side, out=0.0):
    """Point on the outer hull surface (or above the sheer, on the bulwark line), pushed out by `out`."""
    return v3(side * (fs.hull_x(z, y) + out), y, z)


def side_frame(z, y, side):
    """Point on the hull side, u along +z (on the surface), v up the surface, n outward."""
    d = 0.05
    p = hp(z, y, side)
    u = norm(hp(z + d, y, side) - hp(z - d, y, side))
    vv = hp(z, y + d, side) - hp(z, y - d, side)
    v = norm(vv - np.dot(vv, u) * u)
    n = np.cross(u, v)
    if np.dot(n, v3(side, 0, 0)) < 0:
        u, n = -u, -n
    return p, u, v, n


def hull_decal(bone, name, z, y, side, w, h, region, out=0.012, th=0.03, glow=False, stretch=True):
    p, u, v, n = side_frame(z, y, side)
    c = p + n * (out + th / 2)
    return add_cube(bone, ("glow_" if glow else "") + name, c, np.column_stack([u, v, n]), (w, h, th), region, stretch=stretch,
                    u_dir=-u if side > 0 else u, v_dir=v3(0, -1, 0))


def stem_clip(z, y):
    """Beyond the raked stem a section point lies on the stem itself (the planking closes on it)."""
    return min(z, BOW_Z + fs.rake(BOW_Z, y))


def hull(bone):
    n = 0
    for side, sn in SIDES:
        for i in range(len(STATIONS) - 1):
            za, zb = STATIONS[i], STATIONS[i + 1]
            A, regs = hull_rows(za)
            B, _ = hull_rows(zb)
            for k in range(len(A) - 1):
                a0, a1 = v3(side * A[k][0], A[k][1], stem_clip(za, A[k][1])), v3(side * A[k + 1][0], A[k + 1][1], stem_clip(za, A[k + 1][1]))
                b0, b1 = v3(side * B[k][0], B[k][1], stem_clip(zb, B[k][1])), v3(side * B[k + 1][0], B[k + 1][1], stem_clip(zb, B[k + 1][1]))
                if np.linalg.norm((b0 + b1) - (a0 + a1)) < 0.02 or np.linalg.norm((a1 + b1) - (a0 + b0)) < 0.02:
                    continue  # closed on the stem: nothing left of this plank
                if max(abs(a0[0]), abs(a1[0]), abs(b0[0]), abs(b1[0])) < 0.3:
                    continue  # a sliver along the stem, inside the stem post
                mid = (a0 + a1 + b0 + b1) / 4
                t = (a1 + b1) - (a0 + b0)
                outward = norm(v3(side * t[1], -side * t[0], 0) + v3(0, 0, 0.6 * max(0.0, mid[2] - 13) / 6))
                strake(bone, "hull_%s%d_%d" % (sn, i, k), a0, a1, b0, b1, 0.14, regs[k], outward, overlap=1.03,
                       inner="hull_brown" if k < 4 else "hold_wall")
                n += 1
    for i in range(len(STATIONS) - 2):
        za, zb = STATIONS[i], STATIONS[i + 1]
        if zb > fs.HALF_LENGTH - 0.3:
            break
        beam(bone, "keel_%d" % i, (0, fs.keel_y(za) - 0.1, za), (0, fs.keel_y(zb) - 0.1, zb), 0.36, "dark_wood", width=0.42, extend=0.06)
    return n


# ---------------------------------------------------------------- the stone cladding
def stone_course(bone, name, side, z0, z1, ylo, yhi, out, region="stone", jitter=0.05, step=1.0, th_in=0.14):
    """A course of stone blocks along the hull side between z0 and z1, from ylo(z) to yhi(z) (functions), standing
    `out` proud of the planking (each block a little more or less: the blocky masonry of the references)."""
    zs = list(np.arange(z0, z1 - 1e-6, step)) + [z1]
    for i in range(len(zs) - 1):
        za, zb = zs[i], zs[i + 1]
        if zb - za < 0.05:
            continue
        o = out + RNG.uniform(-jitter, jitter)
        ya0, ya1, yb0, yb1 = ylo(za), yhi(za), ylo(zb), yhi(zb)
        cza0, cza1, czb0, czb1 = stem_clip(za, ya0), stem_clip(za, ya1), stem_clip(zb, yb0), stem_clip(zb, yb1)
        if czb0 - cza0 < 0.05 and czb1 - cza1 < 0.05:
            continue
        a0, a1 = hp(cza0, ya0, side, o), hp(cza1, ya1, side, o)
        b0, b1 = hp(czb0, yb0, side, o), hp(czb1, yb1, side, o)
        board(bone, "%s_%d" % (name, i), a0, a1, b0, b1, o + th_in, region, v3(side, 0, 0.2 * max(0.0, za - 14) / 6), overlap=1.0)


def cladding(bone, detail):
    """The stone wale at the waterline, the heavy studded stone belt under the gunwale (climbing to the forecastle
    and sweeping up to the beak), the vertical stone ribs between the red panels with an iron strap on each side."""
    for side, sn in SIDES:
        stone_course(bone, "wale_low_" + sn, side, TZ + 0.1, BOW_Z + 0.3, lambda z: -0.05 + 0.3 * lift(z), lambda z: 0.8 + 0.3 * lift(z), 0.24,
                     region="stone_dark", jitter=0.04)
        stone_course(bone, "belt_" + sn, side, TZ + 0.05, HEAD_Z - 0.2, lambda z: fs.sheer_y(z) - 1.12, lambda z: fs.sheer_y(z) - 0.2, 0.34,
                     region="stone_stud", jitter=0.05)
        # the gunwale's cap stones over the belt, from the outer face in to the bulwark's inner face
        zs = list(np.arange(CF - 0.5, HEAD_Z - 0.4, 1.0))
        for i, za in enumerate(zs):
            zb = min(za + 1.0, HEAD_Z - 0.4)
            ym = fs.sheer_y((za + zb) / 2)
            xa, xb = fs.hull_x(stem_clip(za, ym), ym), fs.hull_x(stem_clip(zb, ym), ym)
            if xa < 0.4 and xb < 0.4:
                continue
            x_out, x_in = max(xa, xb) + 0.4, min(xa, xb) - 0.62
            if x_in < 0.1:
                x_in = 0.1
            c = v3(side * (x_out + x_in) / 2, ym - 0.11, (stem_clip(za, ym) + stem_clip(zb, ym)) / 2)
            add_cube(bone, "gunwale_%s%d" % (sn, i), c, EYE, (x_out - x_in, 0.24, max(0.2, stem_clip(zb, ym) - stem_clip(za, ym)) + 0.02),
                     {"all": "stone_light", "+2": "stone"})
        # the ribs
        for j, z in enumerate(fs.RIB_Z):
            y0, y1 = 0.8 + 0.3 * lift(z), fs.sheer_y(z) - 1.12
            n = max(1, int(round(y1 - y0)))
            for k in range(n):
                ya, yb = y0 + (y1 - y0) * k / n, y0 + (y1 - y0) * (k + 1) / n
                p, u, v, nn = side_frame(z, (ya + yb) / 2, side)
                o = 0.3 + RNG.uniform(-0.04, 0.04)
                add_cube(bone, "rib_%s%d_%d" % (sn, j, k), p + nn * (o / 2 - 0.06), np.column_stack([u, v, nn]), (1.0, yb - ya + 0.02, o + 0.12),
                         "stone_stud" if k % 2 else "stone")
            # the rib's foot and head: a wider block (the buttress spreads on the wales)
            p, u, v, nn = side_frame(z, y1 - 0.1, side)
            add_cube(bone, "rib_head_%s%d" % (sn, j), p + nn * 0.16, np.column_stack([u, v, nn]), (1.3, 0.4, 0.46), "stone")
            for s in (1, -1):
                hull_decal(detail, "rib_strap_%s%d_%d" % (sn, j, s > 0), z + s * 0.74, (y0 + y1) / 2, side, 0.44, y1 - y0, "iron_strap", out=0.03,
                           th=0.07, stretch=False)


def merlon(bone, name, c, w=0.9, h=0.85, d=0.55, region="stone"):
    add_cube(bone, name, c + v3(0, h / 2, 0), EYE, (d, h, w) if True else None, {"all": region, "+2": "stone_light"})


def bulwarks(bone, detail, lights):
    """Inside faces of the bulwarks (at the collision face), the stone merlons on the waist's gunwale with a dark
    wooden rail between them, the forecastle's wooden balustrade on its stone curb with stone caps on its posts,
    lanterns on posts."""
    for side, sn in SIDES:
        # inner lining of the bulwarks: from the deck to the gunwale, where the walkers touch it
        zs = list(np.arange(CF, HEAD_Z - 0.9, 0.75))
        for i in range(len(zs) - 1):
            za, zb = zs[i], zs[i + 1]
            dy = deck_y((za + zb) / 2)
            ya, yb = fs.sheer_y(za) - 0.22, fs.sheer_y(zb) - 0.22
            xa, xb = fs.hull_x(stem_clip(za, ya), ya) - 0.6, fs.hull_x(stem_clip(zb, yb), yb) - 0.6
            if min(xa, xb) < 0.3 or ya - dy < 0.1:
                continue
            board(bone, "lining_%s%d" % (sn, i), v3(side * xa, dy, za), v3(side * xa, ya, za), v3(side * xb, dy, zb), v3(side * xb, yb, zb), 0.1,
                  "wood_dark", v3(-side, 0, 0), overlap=1.02)
        # the waist: stone merlons every two blocks on the gunwale, a dark rail between them
        for j, z in enumerate(np.arange(CF + 1.0, FF - 1.4, 2.0)):
            if side < 0 and GANGPLANK_Z[0] - 0.5 < z < GANGPLANK_Z[1] + 0.5:
                continue
            ys = fs.sheer_y(z)
            merlon(detail, "merlon_waist_%s%d" % (sn, j), hp(z, ys, side, -0.24), w=0.9, h=0.85, d=0.62)
        rail_pts = []
        for z in np.arange(CF + 0.3, FF - 1.0, 0.75):
            rail_pts.append(z)
        for i in range(len(rail_pts) - 1):
            za, zb = rail_pts[i], rail_pts[i + 1]
            if side < 0 and za < GANGPLANK_Z[1] and zb > GANGPLANK_Z[0]:
                continue
            beam(detail, "waist_rail_%s%d" % (sn, i), hp(za, fs.sheer_y(za) + 0.5, side, -0.3), hp(zb, fs.sheer_y(zb) + 0.5, side, -0.3), 0.14,
                 "rail", width=0.22, extend=0.04)
        # the forecastle: a wooden balustrade (posts, a top rail, a bottom rail) on the stone curb, stone caps on
        # some posts, where the stone bulwark is lower than the balustrade
        zf = [z for z in np.arange(FF + 0.25, 18.6, 0.55)]
        for j, z in enumerate(zf):
            ys = fs.sheer_y(z)
            top = fs.FC_WALL if hasattr(fs, "FC_WALL") else F + 1.5
            top = F + 1.5
            if ys > top - 0.3:
                break
            p = hp(z, ys, side, -0.3)
            big = j % 4 == 0
            add_cube(detail, "fc_post_%s%d" % (sn, j), p + v3(0, (top - ys) / 2, 0), EYE, (0.2 if not big else 0.32, top - ys, 0.2 if not big else 0.32),
                     "wood_dark")
            if big:
                add_cube(detail, "fc_post_cap_%s%d" % (sn, j), p + v3(0, top - ys + 0.2, 0), EYE, (0.5, 0.4, 0.5), {"all": "stone", "+2": "stone_light"})
        zr = [z for z in np.arange(FF + 0.2, 18.6, 0.6) if fs.sheer_y(z) < F + 1.2]
        for i in range(len(zr) - 1):
            za, zb = zr[i], zr[i + 1]
            for k, (yy, th) in enumerate(((F + 1.5, 0.14), (lambda z: fs.sheer_y(z) + 0.18, 0.1))):
                if callable(yy):
                    ya_, yb_ = yy(za), yy(zb)
                else:
                    ya_ = yb_ = yy
                beam(detail, "fc_rail_%s%d_%d" % (sn, i, k), hp(za, ya_, side, -0.3), hp(zb, yb_, side, -0.3), th, "rail", width=0.2, extend=0.05)
    # lanterns on posts: two along each side of the waist, the forecastle's front corners
    for side, sn in SIDES:
        for j, z in enumerate((-4.0, 2.0)):
            if side < 0 and GANGPLANK_Z[0] - 0.5 < z < GANGPLANK_Z[1] + 0.5:
                z = -1.0
            ys = fs.sheer_y(z)
            p = hp(z, ys, side, -0.3)
            add_cube(detail, "lantern_post_%s%d" % (sn, j), p + v3(0, 0.6, 0), EYE, (0.16, 1.2, 0.16), "wood_dark")
            beam(detail, "lantern_arm_%s%d" % (sn, j), p + v3(0, 1.15, 0), p + v3(side * 0.42, 1.15, 0), 0.08, "iron")
            lantern(lights, "lantern_waist_%s%d" % (sn, j), p + v3(side * 0.42, 1.12, 0), drop=0.18, s=1.1)
        z = FF + 0.25
        p = hp(z, fs.sheer_y(z), side, -0.3)
        add_cube(detail, "lantern_fc_post_%s" % sn, p + v3(0, 1.4, 0), EYE, (0.18, 1.0, 0.18), "wood_dark")
        lantern(lights, "lantern_fc_%s" % sn, p + v3(0, 1.9, 0), hang=False, s=1.2)
        # and the big lantern on a tall post at the bow end of the forecastle (main reference)
        z = 15.4
        p = hp(z, fs.sheer_y(z), side, -0.3)
        add_cube(detail, "lantern_bow_post_%s" % sn, p + v3(0, 0.9, 0), EYE, (0.2, 1.8, 0.2), "wood_dark")
        add_cube(detail, "lantern_bow_cap_%s" % sn, p + v3(0, 1.82, 0), EYE, (0.34, 0.08, 0.34), "iron")
        lantern(lights, "lantern_bow_%s" % sn, p + v3(0, 1.86, 0), hang=False, s=1.45)


def crenels(bone, name, side, z0, z1, y, out=-0.26, spacing=2.0, w=0.9, h=0.8, d=0.62, skip=None):
    """Stone merlons along a parapet top at height y(z), every `spacing` blocks."""
    for j, z in enumerate(np.arange(z0, z1 + 1e-6, spacing)):
        if skip and skip(z):
            continue
        yy = y(z) if callable(y) else y
        merlon(bone, "%s_%s%d" % (name, "p" if side > 0 else "s", j), hp(z, yy, side, out), w=w, h=h, d=d)


def wall(bone, name, side, z0, z1, y0, y1, region="stone", th=0.3, out=0.0, step=1.0):
    """A straight stone wall on the hull line (castle sides), from y0 to y1, `out` proud of it, the inner face at the
    collision face (0.6 inboard)."""
    zs = list(np.arange(z0, z1 - 1e-6, step)) + [z1]
    for i in range(len(zs) - 1):
        za, zb = zs[i], zs[i + 1]
        if zb - za < 0.05:
            continue
        a0, a1, b0, b1 = hp(za, y0, side, out), hp(za, y1, side, out), hp(zb, y0, side, out), hp(zb, y1, side, out)
        board(bone, "%s_%s%d" % (name, "p" if side > 0 else "s", i), a0, a1, b0, b1, th + out, region, v3(side, 0, 0), overlap=1.0,
              inner="wall_stone")


# ---------------------------------------------------------------- the stern castle
WIN_W, WIN_H = 1.0, 1.25


def window(bone, name, z, y, side, w=WIN_W, h=WIN_H, out=0.0):
    """A lit window on the castle side: the glow in a dark wooden frame, a pale stone sill and lintel."""
    hull_decal(bone, name, z, y, side, w, h, "glow_window", out=out + 0.02, glow=True)
    hull_decal(bone, name + "_sill", z, y - h / 2 - 0.08, side, w + 0.3, 0.16, "stone_light", out=out + 0.02, th=0.14, stretch=False)
    hull_decal(bone, name + "_lintel", z, y + h / 2 + 0.08, side, w + 0.3, 0.16, "stone_light", out=out + 0.02, th=0.14, stretch=False)
    p, u, v, n = side_frame(z, y, side)
    add_cube(bone, name + "_in", p - n * 0.62, np.column_stack([u, v, n]), (w, h, 0.03), {"all": None, "-3": "window_in"}, stretch=True)


def castle(bone, detail, lights):
    """The stern castle: its stone sides from the gunwale to the quarterdeck's parapet (and, aft, the keep's walls up
    to its corbelled battlements), lit windows of the captain's cabin and of the officers' room, a string course at
    the quarterdeck, stone merlons; the front bulkhead of the castle with the cabin's double door and two windows, the
    guard parapet of the quarterdeck between its stairs; the keep's front with its door and windows and its parapet;
    the stern with its windows, the corner lanterns and the banners."""
    yb = fs.WAIST_TOP - 0.2
    for side, sn in SIDES:
        # the lower storey (captain's cabin): dark timber walls between stone pilasters, and the stone parapet of the
        # quarterdeck running along the whole castle side (main reference)
        wall(bone, "castle_wall", side, TZ, CF + 0.3, yb, Q - 0.3, th=0.34, region="timber")
        wall(bone, "castle_parapet", side, TZ, CF + 0.3, Q - 0.32, fs.QD_TOP, th=0.34, region="stone_stud", out=0.06)
        # the keep, over the aft part: red panels between the pilasters, its battlements standing out on corbels
        wall(bone, "keep_wall", side, TZ - 0.74, KF + 0.3, fs.QD_TOP - 0.02, K - 0.02, th=0.34, region="red_panel")
        wall(bone, "keep_parapet", side, TZ - 0.93, KF + 0.55, K - 0.05, fs.KEEP_TOP, th=0.34, out=0.3, region="stone_stud")
        for j, z in enumerate(np.arange(TZ + 0.3, KF + 0.3, 1.0)):
            p, u, v, n = side_frame(z, K - 0.35, side)
            add_cube(bone, "keep_corbel_%s%d" % (sn, j), p + n * 0.15, np.column_stack([u, v, n]), (0.5, 0.5, 0.42), "stone_light")
        # the string course at the quarterdeck and the parapet's cap
        for i, (z0, z1, y, o) in enumerate(((TZ, CF + 0.3, Q - 0.15, 0.12), (KF, CF + 0.3, fs.QD_TOP - 0.1, 0.1))):
            wall(detail, "string_%d" % i, side, z0, z1, y - 0.12, y + 0.12, region="stone_light", th=0.16, out=o + 0.2)
        crenels(detail, "qd_merlon", side, KF + 0.7, CF - 0.3, fs.QD_TOP, spacing=1.8)
        crenels(detail, "keep_merlon", side, TZ + 0.45, KF + 0.3, fs.KEEP_TOP, out=0.05, spacing=1.6)
        # windows: three wide ones on the captain's cabin, two on the officers' room, between stone pilasters
        for j, z in enumerate((-17.7, -14.75, -11.1)):
            window(bone, "castle_window_%s%d" % (sn, j), z, 6.35, side, w=1.6, h=1.25, out=0.06)
        for j, z in enumerate((-17.7, -14.75)):
            window(bone, "keep_window_%s%d" % (sn, j), z, Q + 1.4, side, w=1.0, h=1.15, out=0.06)
        for j, z in enumerate((TZ + 0.35, -16.2, KF - 0.25, CF + 0.2)):
            top = fs.KEEP_TOP - 0.9 if z < KF + 0.1 else fs.QD_TOP
            p0, u, v, n = side_frame(z, (yb + top) / 2, side)
            add_cube(detail, "pilaster_%s%d" % (sn, j), p0 + n * 0.14, np.column_stack([u, v, n]), (0.75, top - yb, 0.34),
                     "stone" if j % 2 else "stone_stud")
        # a red banner with the white tower on the castle's side (and one hanging from the keep's battlements aft)
        banner(lights, "banner_castle_" + sn, hp(-13.6, 7.6, side, 0.14), side, 1.5, 3.2)
        banner(lights, "banner_keep_" + sn, hp(-19.0, fs.KEEP_TOP - 0.2, side, 0.62), side, 1.4, 3.4)
    # the front bulkhead of the castle (main deck -> quarterdeck), the cabin's door frame, two windows
    bz = CF - 0.06
    wq = fs.hull_x(CF, M) - 0.2
    for side, sn in SIDES:
        x0, x1 = 1.0, wq
        add_cube(bone, "bulkhead_" + sn, (side * (x0 + x1) / 2, (M + Q) / 2, bz), EYE, (x1 - x0, Q - M, 0.12), {"all": "stone", "-3": "wall_wood"})
        add_cube(detail, "bulkhead_jamb_" + sn, (side * 1.12, (M + Q - 0.5) / 2, CF + 0.06), EYE, (0.24, Q - 0.5 - M + 0.2, 0.16), "stone_light")
        add_cube(detail, "glow_bulkhead_window_" + sn, (side * 2.4, 6.3, CF + 0.02), EYE, (0.8, 0.9, 0.04), "glow_window", stretch=True)
        add_cube(detail, "bulkhead_window_sill_" + sn, (side * 2.4, 5.77, CF + 0.08), EYE, (1.1, 0.14, 0.16), "stone_light")
        add_cube(detail, "bulkhead_window_lintel_" + sn, (side * 2.4, 6.83, CF + 0.08), EYE, (1.1, 0.14, 0.16), "stone_light")
    add_cube(detail, "bulkhead_lintel", (0, Q - 0.4, CF + 0.06), EYE, (2.5, 0.3, 0.18), "stone_light")
    add_cube(detail, "bulkhead_band", (0, Q - 0.1, CF + 0.04), EYE, (2 * wq, 0.2, 0.14), "stone_light")
    # the guard parapet along the front of the quarterdeck, between the stairs (stone, low merlons)
    x0 = fs.QD_STAIR_X[0]
    add_cube(bone, "qd_front_parapet", (0, Q + 0.5, CF - 0.25), EYE, (2 * x0, 1.0, 0.5), {"all": "stone", "+2": "stone_light"})
    for j, x in enumerate((-2.4, 0.0, 2.4)):
        merlon(detail, "qd_front_merlon_%d" % j, v3(x, Q + 1.0, CF - 0.25), w=0.5, h=0.55, d=0.7)
    # the stairs to the quarterdeck (as the grid: 7 steps of 0.5), stone, with a rope hand rail on their inner side
    n = int(round((Q - M) / 0.5))
    for side, sn in SIDES:
        xa, xb = fs.QD_STAIR_X
        for k in range(1, n + 1):
            za = fs.QD_STAIR_Z[0] - k * 0.5
            top = M + k * 0.5
            add_cube(bone, "qd_step_%s%d" % (sn, k), (side * (xa + xb) / 2, (M + top) / 2, za + 0.25), EYE, (xb - xa, top - M, 0.5),
                     {"all": "stone", "+2": "stone_light"})
        round_bar(detail, "qd_handrail_" + sn, (side * xa, M + 1.0, fs.QD_STAIR_Z[0] + 0.1), (side * xa, Q + 1.0, CF), 0.1, "rope")
        for k, t in enumerate((0.05, 0.5, 0.95)):
            z = fs.QD_STAIR_Z[0] + 0.1 + (CF - fs.QD_STAIR_Z[0] - 0.1) * t
            yy = M + (Q - M) * t
            add_cube(detail, "qd_handrail_post_%s%d" % (sn, k), (side * xa, yy + 0.5, z), EYE, (0.12, 1.0, 0.12), "iron")
    # the keep's front (quarterdeck -> keep's roof) with its door, two windows, its parapet with merlons
    kz = KF + 0.06
    wk = fs.hull_x(KF, Q) - 0.2
    for side, sn in SIDES:
        add_cube(bone, "keep_front_" + sn, (side * (1.0 + wk) / 2, (Q + K) / 2, kz), EYE, (wk - 1.0, K - Q, 0.12), {"all": "stone", "-3": "wall_stone"})
        add_cube(detail, "keep_jamb_" + sn, (side * 1.12, (Q + K - 0.5) / 2, KF + 0.06), EYE, (0.24, K - 0.5 - Q + 0.2, 0.16), "stone_light")
        add_cube(detail, "glow_keep_front_window_" + sn, (side * 2.6, Q + 1.4, KF + 0.02), EYE, (0.8, 1.0, 0.04), "glow_window", stretch=True)
        add_cube(detail, "keep_front_sill_" + sn, (side * 2.6, Q + 0.82, KF + 0.08), EYE, (1.1, 0.14, 0.16), "stone_light")
    add_cube(detail, "keep_front_lintel", (0, K - 0.4, KF + 0.06), EYE, (2.5, 0.3, 0.18), "stone_light")
    wp = fs.hull_x(KF, K) + 0.25
    add_cube(bone, "keep_front_parapet", (0, (K + fs.KEEP_TOP) / 2 - 0.05, KF - 0.2), EYE, (2 * wp, fs.KEEP_TOP - K + 0.1, 0.62),
             {"all": "stone_stud", "+2": "stone_light"})
    for j, x in enumerate(np.arange(-wp + 0.45, wp - 0.3, 1.6)):
        merlon(detail, "keep_front_merlon_%d" % j, v3(x, fs.KEEP_TOP, KF - 0.2), w=0.62, d=0.9)
    for j, x in enumerate(np.arange(-wp + 0.5, wp, 1.0)):
        add_cube(detail, "keep_front_corbel_%d" % j, (x, K - 0.35, KF + 0.12), EYE, (0.5, 0.5, 0.4), "stone_light")
    # the stern: the transom from the water to the castle, three lit windows of the cabin, two of the keep, the
    # corbelled battlements across, a big banner in the middle, lanterns on the corners
    z = TZ
    pts, regs = hull_rows(z)
    for k in range(len(pts) - 1):
        (xa, ya), (xb, yb_) = pts[k], pts[k + 1]
        for j in range(4):
            fa0, fa1 = -1 + j / 2, -1 + (j + 1) / 2
            strake(bone, "transom_%d_%d" % (k, j), v3(fa0 * xa, ya, z), v3(fa0 * xb, yb_, z), v3(fa1 * xa, ya, z), v3(fa1 * xb, yb_, z),
                   0.16, regs[k], v3(0, 0, -1), overlap=1.02, inner="hull_brown")
    ys = fs.sheer_y(z)
    xs_ = fs.hull_x(z, ys)
    add_cube(bone, "stern_wall", (0, (ys + K) / 2, z + 0.12), EYE, (2 * xs_ - 0.1, K - ys + 0.4, 0.3), {"all": "stone", "+3": "wall_wood"})
    # the keep's storey hangs out over the transom on a row of big corbels (the castle overhanging the stern of the
    # main reference): red panels between stone corner posts, its battlements standing out further still
    oz = z - 0.45
    add_cube(bone, "stern_overhang", (0, (Q - 0.25 + K) / 2, oz), EYE, (2 * xs_ - 0.2, K - Q + 0.25, 0.62),
             {"all": "red_panel", "+2": "stone", "-2": "stone"})
    for s in (1, -1):
        add_cube(detail, "stern_overhang_post_%d" % (s > 0), (s * (xs_ - 0.35), (Q - 0.25 + K) / 2, oz - 0.05), EYE, (0.6, K - Q + 0.3, 0.66),
                 "stone_stud")
    for j, x in enumerate(np.arange(-xs_ + 0.6, xs_ - 0.4, 1.2)):
        add_cube(detail, "stern_overhang_corbel_%d" % j, (x, Q - 0.55, z - 0.32), EYE, (0.5, 0.6, 0.64), "stone_light")
    add_cube(bone, "stern_parapet", (0, (K + fs.KEEP_TOP) / 2 - 0.05, z - 0.62), EYE, (2 * xs_ + 0.5, fs.KEEP_TOP - K + 0.1, 0.62),
             {"all": "stone_stud", "+2": "stone_light"})
    add_cube(bone, "stern_parapet_floor", (0, K - 0.1, z - 0.22), EYE, (2 * xs_ - 0.2, 0.2, 0.3), "stone_light")
    for j, x in enumerate(np.arange(-xs_ - 0.05, xs_ + 0.1, 1.6)):
        merlon(detail, "stern_merlon_%d" % j, v3(x, fs.KEEP_TOP, z - 0.62), w=0.62, d=0.9)
        add_cube(detail, "stern_corbel_%d" % j, (x, K - 0.35, z - 0.86), EYE, (0.5, 0.5, 0.42), "stone_light")
    for j, x in enumerate((-2.5, 0.0, 2.5)):
        add_cube(detail, "glow_stern_window_%d" % j, (x, 6.3, z - 0.04), EYE, (1.0, 1.25, 0.04), "glow_window", stretch=True)
        add_cube(detail, "stern_window_sill_%d" % j, (x, 5.6, z - 0.1), EYE, (1.3, 0.16, 0.2), "stone_light")
        add_cube(detail, "stern_window_lintel_%d" % j, (x, 7.0, z - 0.1), EYE, (1.3, 0.16, 0.2), "stone_light")
        add_cube(detail, "stern_window_in_%d" % j, (x, 6.3, z + 0.3), EYE, (1.0, 1.25, 0.03), {"all": None, "+3": "window_in"}, stretch=True)
    for j, x in enumerate((-2.2, 2.2)):
        add_cube(detail, "glow_stern_window2_%d" % j, (x, Q + 1.35, oz - 0.33), EYE, (0.9, 1.15, 0.04), "glow_window", stretch=True)
        add_cube(detail, "stern_window2_sill_%d" % j, (x, Q + 0.7, oz - 0.38), EYE, (1.2, 0.16, 0.2), "stone_light")
        add_cube(detail, "stern_window2_lintel_%d" % j, (x, Q + 2.0, oz - 0.38), EYE, (1.2, 0.16, 0.2), "stone_light")
    add_cube(detail, "stern_string", (0, Q - 0.15, z - 0.1), EYE, (2 * xs_ + 0.1, 0.24, 0.2), "stone_light")
    banner(lights, "banner_stern", v3(0, fs.KEEP_TOP - 0.25, z - 0.96), 0, 1.6, 3.6, facing=v3(0, 0, -1))
    for side, sn in SIDES:
        x = side * (xs_ + 0.05)
        beam(detail, "stern_lantern_arm_" + sn, v3(x, K - 0.6, oz), v3(x + side * 0.55, K - 0.6, z - 1.0), 0.1, "iron")
        lantern(lights, "lantern_stern_" + sn, v3(x + side * 0.55, K - 0.65, z - 1.0), drop=0.3, s=1.4)
    # lanterns at the front corners of the quarterdeck and of the keep's battlements
    for side, sn in SIDES:
        p = hp(CF - 0.3, fs.QD_TOP, side, -0.3)
        add_cube(detail, "lantern_qd_post_" + sn, p + v3(0, 0.55, 0), EYE, (0.18, 1.1, 0.18), "wood_dark")
        lantern(lights, "lantern_qd_" + sn, p + v3(0, 1.1, 0), hang=False, s=1.2)
        p = hp(KF + 0.1, fs.KEEP_TOP, side, 0.0)
        lantern(lights, "lantern_keep_" + sn, p + v3(0, 0.85, 0), hang=False, s=1.1)


def banner(parent, name, top, side, w, h, facing=None):
    """A red banner with the white tower hanging from a rod against a wall (side +1 port, -1 starboard, 0: facing
    given): its own bone (it sways a little with the lanterns)."""
    n = facing if facing is not None else v3(side, 0, 0)
    n = norm(n)
    u = np.cross(v3(0, 1, 0), n)
    b = Bone(name, origin=tuple(top), parent=parent)
    axes = np.column_stack([u, v3(0, 1, 0), n])
    add_cube(b, name + "_cloth", top + v3(0, -h / 2 - 0.08, 0) + n * 0.03, axes, (w, h, 0.04), {"all": None, "+3": "banner", "-3": "banner"},
             stretch=True, u_dir=u if side >= 0 else -u, v_dir=v3(0, -1, 0))
    round_bar(b, name + "_rod", top - u * (w / 2 + 0.15) + n * 0.06, top + u * (w / 2 + 0.15) + n * 0.06, 0.1, "wood_dark")
    for s in (1, -1):
        disc(b, name + "_knob_%d" % (s > 0), top + u * s * (w / 2 + 0.2) + n * 0.06, u, 0.08, 0.1, "gold", n=2)
    return b


# ---------------------------------------------------------------- the turret on the keep
def turret(bone, detail, lights):
    """The turret on the keep's roof: dark timber walls between corner posts on a stone base course, two lit windows
    a side, its door forward; the pointed roof of red tiles in steps (as the voxel roof of the reference) over a
    grey stone eave band, a finial with a lantern and a spike."""
    th = fs.TURRET_HALF
    z0, z1 = fs.TURRET_Z
    zc = (z0 + z1) / 2
    yt = fs.TURRET_WALL_TOP
    hz = (z1 - z0) / 2
    # walls (the room's inside is drawn on the grid: these are the outer faces, 0.06 proud)
    for k, (c, size, reg) in enumerate((((th + 0.03, (K + yt) / 2, zc), (0.06, yt - K, 2 * hz), "+1"),
                                        ((-th - 0.03, (K + yt) / 2, zc), (0.06, yt - K, 2 * hz), "-1"),
                                        ((0, (K + yt) / 2, z1 + 0.03), (2 * th, yt - K, 0.06), "+3"),
                                        ((0, (K + yt) / 2, z0 - 0.03), (2 * th, yt - K, 0.06), "-3"))):
        add_cube(bone, "turret_wall_%d" % k, c, EYE, size, "timber")
    add_cube(bone, "turret_base", (0, K + 0.3, zc), EYE, (2 * th + 0.3, 0.6, 2 * hz + 0.3), {"all": "stone", "+2": "stone_light"})
    for sx in (1, -1):
        for sz in (1, -1):
            add_cube(bone, "turret_post_%d_%d" % (sx > 0, sz > 0), (sx * (th + 0.02), (K + yt) / 2 + 0.1, zc + sz * (hz + 0.02)), EYE,
                     (0.36, yt - K - 0.2, 0.36), "wood_dark")
    add_cube(bone, "turret_band", (0, yt - 0.15, zc), EYE, (2 * th + 0.2, 0.3, 2 * hz + 0.2), "wood_dark")
    # windows: two on each side and aft, one each side of the door forward
    for side in (1, -1):
        for j, z in enumerate((z0 + 1.1, z1 - 1.1)):
            add_cube(detail, "glow_turret_window_%d_%d" % (side > 0, j), (side * (th + 0.07), K + 2.0, z), EYE, (0.04, 1.1, 0.8), "glow_window",
                     stretch=True)
            add_cube(detail, "turret_window_sill_%d_%d" % (side > 0, j), (side * (th + 0.1), K + 1.38, z), EYE, (0.16, 0.12, 1.0), "stone_light")
    for j, x in enumerate((-1.1, 1.1)):
        add_cube(detail, "glow_turret_back_window_%d" % j, (x, K + 2.0, z0 - 0.07), EYE, (0.8, 1.1, 0.04), "glow_window", stretch=True)
    for j, x in enumerate((-1.8, 1.8)):
        add_cube(detail, "glow_turret_front_window_%d" % j, (x, K + 2.2, z1 + 0.07), EYE, (0.5, 0.9, 0.04), "glow_window", stretch=True)
    add_cube(detail, "turret_door_lintel", (0, K + 2.65, z1 + 0.08), EYE, (2.4, 0.25, 0.14), "wood_dark")
    # the eaves: a grey stone band, then the stepped roof of red tiles
    ew, ed = th + 0.65, hz + 0.65
    add_cube(bone, "turret_eave", (0, yt + 0.15, zc), EYE, (2 * ew, 0.3, 2 * ed), {"all": "tile_edge", "+2": "roof_tile", "-2": "stone"})
    steps = 8
    y = yt + 0.3
    dh = (fs.TURRET_ROOF_TOP - 0.4 - y) / steps
    for k in range(steps):
        f = 1 - (k + 1) / (steps + 0.6)
        add_cube(bone, "turret_roof_%d" % k, (0, y + dh / 2, zc), EYE, (2 * ew * f + 0.1, dh, 2 * ed * f + 0.1), {"all": "roof_tile", "-2": "wood_dark"})
        y += dh
    add_cube(bone, "turret_roof_cap", (0, y + 0.2, zc), EYE, (0.5, 0.4, 0.5), "stone_light")
    # the finial: a post, a lantern in a little iron cage, a spike with a knob
    add_cube(detail, "finial_post", (0, y + 0.6, zc), EYE, (0.2, 0.5, 0.2), "wood_dark")
    lantern(lights, "lantern_finial", v3(0, y + 0.85, zc), hang=False, s=1.3)
    for sx in (1, -1):
        add_cube(detail, "finial_cage_%d" % (sx > 0), (sx * 0.22, y + 1.15, zc), EYE, (0.05, 0.62, 0.05), "iron")
    add_cube(detail, "finial_roof", (0, y + 1.52, zc), EYE, (0.5, 0.1, 0.5), "iron")
    round_bar(detail, "finial_spike", (0, y + 1.55, zc), (0, y + 2.4, zc), 0.1, "bronze")
    disc(detail, "finial_knob", (0, y + 2.0, zc), (0, 1, 0), 0.12, 0.12, "bronze", n=3)
    add_cube(detail, "finial_cross", (0, y + 2.15, zc), EYE, (0.5, 0.08, 0.08), "bronze")


# ---------------------------------------------------------------- decks
def decks(bone, castle_bone):
    """Main deck planking (with the companion hatch left open), the forecastle, the quarterdeck, the keep's stone roof
    (the stair's hatch left open)."""
    cx0, cx1 = fs.COMPANION_X
    cz0, cz1 = fs.COMPANION_Z

    def planks(bone_, name, z0, z1, y, region, holes=(), under="ceil", inset=0.6):
        zs = list(np.arange(z0, z1 - 1e-6, 1.0)) + [z1]
        for j in range(len(zs) - 1):
            za, zb = zs[j], zs[j + 1]
            if zb - za < 0.05:
                continue
            w = min(fs.hull_x(stem_clip(za, y), y), fs.hull_x(stem_clip(zb, y), y)) - inset + 0.02
            if w < 0.3:
                continue
            spans = [(-w, w)]
            for hx0, hx1, hz0, hz1 in holes:
                if za < hz1 - 1e-6 and zb > hz0 + 1e-6:
                    spans = [s for sp in spans for s in ((sp[0], min(sp[1], hx0)), (max(sp[0], hx1), sp[1])) if s[1] - s[0] > 0.05]
            for k, (x0, x1) in enumerate(spans):
                add_cube(bone_, "%s_%d_%d" % (name, j, k), ((x0 + x1) / 2, y - 0.08, (za + zb) / 2), DECK_AXES, (zb - za + 0.01, 0.16, x1 - x0),
                         {"all": region, "-2": under})
    planks(bone, "deck", CF, FF, M, "deck", holes=[(cx0, cx1, cz0, cz1)])
    planks(bone, "fcdeck", FF, fs.DECK_MAX_Z + 0.5, F, "deck")
    planks(castle_bone, "qdeck", KF, CF, Q, "deck")
    planks(castle_bone, "keeproof", TZ + 0.5, KF, K, "stone_light", holes=[(fs.KEEP_STAIR_X[0], fs.KEEP_STAIR_X[1], fs.KEEP_HATCH_Z[0], fs.KEEP_HATCH_Z[1])],
           under="ceil")
    # the coaming round the hatch of the keep's stair, on the roof
    x0, x1 = fs.KEEP_STAIR_X
    z0, z1 = fs.KEEP_HATCH_Z
    for k, (a, b) in enumerate(((v3(x0, K, z0), v3(x0, K, z1)), (v3(x0, K, z1), v3(x1, K, z1)))):
        beam(castle_bone, "keep_hatch_coaming_%d" % k, a + v3(0, 0.1, 0), b + v3(0, 0.1, 0), 0.2, "wood_dark", width=0.14, extend=0.07)


def forecastle(bone, detail, lights):
    """The forecastle's front bulkhead (main deck -> forecastle) with the mess's door and two windows, the guard rail
    between its stairs, the stairs (as the grid: 5 steps of 0.5), the bell."""
    bz = FF + 0.06
    wq = fs.hull_x(FF, M) - 0.2
    for side, sn in SIDES:
        add_cube(bone, "fc_bulkhead_" + sn, (side * (1.0 + wq) / 2, (M + F) / 2, bz), EYE, (wq - 1.0, F - M, 0.12), {"all": "wood_dark", "+3": "hold_wall"})
        add_cube(detail, "fc_bulkhead_jamb_" + sn, (side * 1.12, (M + F - 0.5) / 2, FF - 0.06), EYE, (0.24, F - 0.5 - M + 0.2, 0.16), "stone_light")
        add_cube(detail, "glow_fc_window_" + sn, (side * 3.3, 5.7, FF - 0.02), EYE, (0.7, 0.7, 0.04), "glow_window", stretch=True)
    add_cube(detail, "fc_bulkhead_lintel", (0, F - 0.4, FF - 0.06), EYE, (2.5, 0.3, 0.18), "stone_light")
    add_cube(detail, "fc_bulkhead_band", (0, F - 0.1, FF - 0.04), EYE, (2 * wq, 0.2, 0.14), "stone")
    x0 = fs.FC_STAIR_X[0]
    gc.gallery_rail(detail, "fc_front_rail", [v3(-x0, F, FF + 0.25), v3(x0, F, FF + 0.25)], 0.95, posts_every=0.5, big_every=4, region="wood_dark",
                    cap="rail")
    n = int(round((F - M) / 0.5))
    for side, sn in SIDES:
        xa, xb = fs.FC_STAIR_X
        for k in range(1, n + 1):
            za = fs.FC_STAIR_Z[0] + (k - 1) * 0.5
            top = M + k * 0.5
            add_cube(bone, "fc_step_%s%d" % (sn, k), (side * (xa + xb) / 2, (M + top) / 2, za + 0.25), EYE, (xb - xa, top - M, 0.5),
                     {"all": "wood_dark", "+2": "deck"})
        round_bar(detail, "fc_handrail_" + sn, (side * xa, M + 1.0, fs.FC_STAIR_Z[0] - 0.1), (side * xa, F + 1.0, FF), 0.1, "rope")
    sd.bell(gg, detail, "bell", (1.6, F, FF + 1.0), metal="bronze", wood="wood_dark")


def bow(bone, detail, lights):
    """The raked stem from the forefoot to the head, the stone beak at its head (blocks stepping forward, as on the main
    reference), heater shields with the tower on both bows, the bowsprit (a heavy banded spar) with its cap, the
    banner hanging from it (third reference), the hawse holes."""
    pts = []
    for j in range(11):
        t = j / 10
        y = fs.keel_y(fs.HALF_LENGTH) - 0.1 + (fs.sheer_y(HEAD_Z) - 0.2 - fs.keel_y(fs.HALF_LENGTH) + 0.1) * t
        z = fs.stem_z(y) + 0.08 - 0.6 * (1 - t) ** 2.2
        pts.append(v3(0, y, min(z, HEAD_Z + 0.25)))
    for j, (a, b) in enumerate(polyline(pts)):
        beam(bone, "stem_%d" % j, a, b, 0.5, "stone" if j >= 2 else "dark_wood", width=0.56, extend=0.1)
    # the stone beak: three blocks stepping forward and down from the head
    yh = fs.sheer_y(HEAD_Z)
    for k, (dz, dy, w, h) in enumerate(((0.0, 0.0, 1.5, 0.9), (0.9, -0.15, 1.2, 0.8), (1.7, -0.35, 0.9, 0.7))):
        add_cube(bone, "beak_%d" % k, (0, yh - 0.35 + dy, HEAD_Z + dz), EYE, (w, h, 1.0), {"all": "beak", "+2": "stone_light"})
    sa, sb = v3(*fs.BOWSPRIT_FOOT), v3(*fs.BOWSPRIT_TIP)
    d = norm(sb - sa)
    round_bar(bone, "bowsprit", sa - d * 0.6, sb, 0.62, "mast")
    for k, t in enumerate(np.arange(1.0, np.linalg.norm(sb - sa) - 0.5, 1.4)):
        round_bar(bone, "bowsprit_band_%d" % k, sa + d * (t - 0.09), sa + d * (t + 0.09), 0.7, "iron")
    cap = sa + d * (np.linalg.norm(sb - sa) - 1.6)
    add_cube(bone, "bowsprit_cap", cap + v3(0, 0.15, 0), gg.frame_from(d, v3(0, 1, 0)), (0.34, 0.8, 0.5), "dark_wood")
    # a cross-tree near the tip carrying the banner (third reference)
    bt = sa + d * (np.linalg.norm(sb - sa) - 2.4)
    beam(bone, "bowsprit_banner_yard", bt + v3(-0.9, -0.25, 0), bt + v3(0.9, -0.25, 0), 0.12, "wood_dark")
    banner(lights, "banner_bowsprit", bt + v3(0, -0.32, 0), 0, 1.3, 2.9, facing=v3(1, 0, 0))
    for side, sn in SIDES:
        # a heater shield with the tower on the bow (third reference), and the hawse hole
        p, u, v, n = side_frame(18.0, 5.3, side)
        add_cube(detail, "bow_shield_" + sn, p + n * 0.36, np.column_stack([u, v, n]), (1.5, 1.9, 0.08), {"all": None, "+3": "shield", "-3": "shield"},
                 stretch=True, u_dir=-u if side > 0 else u, v_dir=v3(0, -1, 0))
        disc(detail, "hawse_" + sn, side_frame(17.4, 3.4, side)[0] + v3(side * 0.28, 0, 0), (side, 0, 0), 0.18, 0.06, "iron")
    return sa, sb, cap


# ---------------------------------------------------------------- masts, yards, sails
MASTS = {
    # name: (z, lower top y, topmast crosstrees y, masthead y, lower mast diameter)
    "fore": (fs.FORE_MAST_Z, 15.9, 21.8, fs.FORE_MAST_TOP, 0.9),
    "main": (fs.MAIN_MAST_Z, 17.3, 24.4, fs.MAIN_MAST_TOP, 0.96),
    "mizzen": (fs.MIZZEN_Z, 20.4, None, fs.MIZZEN_TOP, 0.74),
}
MAST_FOOT = {"fore": L - 0.4, "main": L - 0.4, "mizzen": Q}
# square sails: mast, name, yard y, foot y, half width at the head, at the foot, belly, texture region
SQUARE_SAILS = [
    ("fore", "fore_course", 15.3, 8.9, 7.0, 7.6, 1.9, "fore_course"),
    ("fore", "fore_topsail", 21.2, 16.7, 4.8, 5.4, 1.2, "fore_topsail"),
    ("main", "main_course", 16.7, 7.9, 8.6, 9.2, 2.3, "main_course"),
    ("main", "main_topsail", 23.7, 17.9, 5.8, 6.4, 1.4, "main_topsail"),
    ("mizzen", "mizzen_course", 19.6, 13.4, 4.8, 5.4, 1.3, "mizzen_course"),
]


def yard_step(mast_name, name):
    """(z of the mast that carries the yard, offset of the yard before it)."""
    z, d = MASTS[mast_name][0], MASTS[mast_name][4]
    if "topsail" in name:
        return z + 0.45, d * 0.66 / 2 + 0.17
    return z, d / 2 + 0.17


def mast(root, fittings, name):
    z, top1, top2, head, d = MASTS[name]
    foot = MAST_FOOT[name]
    deck = {"fore": F, "main": M, "mizzen": Q}[name]
    mb = Bone("mast_" + name, origin=(0, deck, z), parent=root)
    if foot < deck:
        round_bar(fittings, "lit_mast_%s_below" % name, (0, foot, z), (0, deck, z), d + 0.05, "mast")
        disc(fittings, "lit_mast_%s_collar" % name, (0, L + 0.15, z), (0, 1, 0), d / 2 + 0.16, 0.3, "wood_dark", n=3)
    round_bar(mb, name + "_lower", (0, deck - 0.1, z), (0, top1 + 0.9, z), d, "mast")
    disc(mb, name + "_partners", (0, deck + 0.12, z), (0, 1, 0), d / 2 + 0.22, 0.24, "wood_dark", n=3)
    for k, y in enumerate(np.arange(deck + 1.4, top1 - 0.6, 1.7)):
        round_bar(mb, "%s_band_%d" % (name, k), (0, y - 0.1, z), (0, y + 0.1, z), d + 0.08, "iron")
    # the fighting top: a square platform on trestle trees, a low stone parapet with merlons at its corners and
    # in the middle of each side (the grey crenellated tops of the main reference)
    s = 1.2 + d * 0.45
    add_cube(mb, name + "_top", (0, top1 + 0.06, z - 0.1), EYE, (2 * s, 0.16, 2 * s * 0.85), {"all": "wood_dark", "+2": "deck"})
    for sx in (1, -1):
        beam(mb, "%s_trestle_%d" % (name, sx > 0), (sx * d * 0.45, top1 - 0.12, z - s), (sx * d * 0.45, top1 - 0.12, z + s * 0.7), 0.2, "wood_dark",
             width=0.16)
    corners = [v3(-s, 0, z - 0.1 - s * 0.85), v3(s, 0, z - 0.1 - s * 0.85), v3(s, 0, z - 0.1 + s * 0.85), v3(-s, 0, z - 0.1 + s * 0.85)]
    for k, (a, b) in enumerate(polyline(corners, closed=True)):
        beam(mb, "%s_top_wall_%d" % (name, k), a + v3(0, top1 + 0.33, 0), b + v3(0, top1 + 0.33, 0), 0.5, "stone", width=0.22, extend=0.11)
        for j, t in enumerate((0.0, 0.5)):
            p = a + (b - a) * t
            add_cube(mb, "%s_top_merlon_%d_%d" % (name, k, j), p + v3(0, top1 + 0.74, 0), EYE, (0.34, 0.32, 0.34), {"all": "stone", "+2": "stone_light"})
    add_cube(mb, name + "_cap", (0, top1 + 0.95, z + 0.2), EYE, (d + 0.2, 0.3, 1.4), "iron")
    if top2 is not None:
        d2 = d * 0.66
        round_bar(mb, name + "_topmast", (0, top1 - 0.5, z + 0.45), (0, top2 + 0.8, z + 0.45), d2, "mast")
        for k, y in enumerate((top1 + 2.2, top1 + 4.4)):
            round_bar(mb, "%s_topmast_band_%d" % (name, k), (0, y - 0.07, z + 0.45), (0, y + 0.07, z + 0.45), d2 + 0.06, "iron")
        s2 = 0.95
        for sx in (1, -1):
            beam(mb, "%s_crosstree2_%d" % (name, sx > 0), (-s2, top2, z + 0.45 + sx * 0.3), (s2, top2, z + 0.45 + sx * 0.3), 0.14, "wood_dark",
                 width=0.14)
        add_cube(mb, name + "_cap2", (0, top2 + 0.85, z + 0.6), EYE, (d2 + 0.16, 0.24, 1.0), "iron")
        round_bar(mb, name + "_topgallant_mast", (0, top2 - 0.4, z + 0.75), (0, head, z + 0.75), d2 * 0.62, "mast")
        disc(mb, name + "_truck", (0, head + 0.05, z + 0.75), (0, 1, 0), 0.2, 0.14, "iron", n=3)
        mz = z + 0.75
    else:
        round_bar(mb, name + "_topmast", (0, top1 - 0.5, z + 0.4), (0, head, z + 0.4), d * 0.62, "mast")
        for sx in (1, -1):
            beam(mb, "%s_crosstree2_%d" % (name, sx > 0), (-0.8, head - 2.2, z + 0.4 + sx * 0.25), (0.8, head - 2.2, z + 0.4 + sx * 0.25), 0.12,
                 "wood_dark", width=0.12)
        disc(mb, name + "_truck", (0, head + 0.05, z + 0.4), (0, 1, 0), 0.18, 0.14, "iron", n=3)
        mz = z + 0.4
    return mb, mz


def square_sail(mb, sails_info, name, z, y_top, y_foot, half_top, half_foot, belly, region, off=0.42):
    """Yard (braced round with its sail, iron bands) and the sail billowed forward."""
    br = Bone("brace_" + name, origin=(0, y_top, z), parent=mb)
    zz = z + off
    round_bar(br, name + "_yard", (-half_top - 0.5, y_top, zz), (half_top + 0.5, y_top, zz), 0.32, "mast", extend=0.05)
    add_cube(br, name + "_sling", (0, y_top, zz - 0.1), EYE, (0.42, 0.4, 0.4), "iron")
    for k, xx in enumerate((-half_top * 0.66, half_top * 0.66, -half_top - 0.3, half_top + 0.3)):
        add_cube(br, "%s_yardband_%d" % (name, k), (xx, y_top, zz), EYE, (0.14, 0.38, 0.38), "iron")
    beam(br, name + "_roll", (-half_top * 0.94, y_top - 0.24, zz + 0.05), (half_top * 0.94, y_top - 0.24, zz + 0.05), 0.28, "cloth_roll")
    sb = Bone("sail_" + name, origin=(0, y_top, zz), parent=br)
    height = y_top - y_foot
    cols, rows = ft.SAIL_CELLS[region]
    origin = v3(0, y_top - 0.15, zz + 0.05)

    def P(s, t):
        half = half_top + (half_foot - half_top) * t
        x = (2 * s - 1) * half
        bel = belly * math.sin(math.pi * min(1.0, t * 0.78)) * (0.35 + 0.65 * (1 - (2 * s - 1) ** 2))
        drop = t * height * (1 + 0.06 * t * t * (1 - (2 * s - 1) ** 2))
        return origin + v3(x, -drop, bel)
    patch_sail(sb, name, P, v3(0, 0, 1), region, cols, rows)
    sails_info.append((sb, False))
    br.rot = ry(BRACE)
    return br


def tri_sail(bone, name, head, tack, clew, belly, N, region):
    clew = gn.jib_clew(head, tack, clew)
    cols, rows = ft.SAIL_CELLS[region]
    return gn.g_tri_sail(bone, name, head, tack, clew, belly, N, region, cols, rows, round_=0.45), clew


def stays(bowsprit):
    sa, sb, cap = bowsprit
    d = norm(sb - sa)
    Fm, Nm, Zm = MASTS["fore"], MASTS["main"], MASTS["mizzen"]
    fz, mz, zz = Fm[0], Nm[0], Zm[0]
    return {
        "fore_stay": (v3(0, Fm[1] - 0.25, fz + 0.3), sa + d * 1.8 + v3(0, 0.25, 0)),
        "fore_topmast_stay": (v3(0, Fm[2] - 0.2, fz + 0.6), cap + v3(0, 0.3, 0)),
        "main_stay": (v3(0, Nm[1] - 0.2, mz + 0.45), v3(0, F + 0.25, fz - 1.6)),
        "main_topmast_stay": (v3(0, Nm[2] - 0.2, mz + 0.6), v3(0, Fm[1] + 0.45, fz - 0.35)),
        "mizzen_stay": (v3(0, Zm[1] - 0.3, zz + 0.3), v3(0, M + 8.5, mz - 0.5)),
        "mizzen_topmast_stay": (v3(0, Zm[3] - 1.2, zz + 0.5), v3(0, Nm[1] + 0.4, mz - 0.4)),
    }


def on(stay, t):
    a, b = stay
    return a + (b - a) * t


def sails_and_spars(root, masts, sails_info, bowsprit):
    sa, sb, cap = bowsprit
    for mast_name, name, yt, yf, ht, hf, bel, reg in SQUARE_SAILS:
        mb, mz = masts[mast_name]
        z, off = yard_step(mast_name, name)
        square_sail(mb, sails_info, name, z, yt, yf, ht, hf, bel, reg, off=off)
    # one jib on the fore topmast stay, its tack at the bowsprit cap (white with a red band, as on the main reference)
    st_ = stays(bowsprit)
    jb = Bone("sail_jibs", origin=tuple(cap), parent=root)
    jib_tri, clew = tri_sail(jb, "jib", on(st_["fore_topmast_stay"], 0.32), on(st_["fore_topmast_stay"], 0.9), v3(0, 10.6, 15.2), 0.9,
                             v3(-1, 0, 0), "jib")
    sails_info.append((jb, True))
    return {"jib": jib_tri, "jib_clew": clew}


# ---------------------------------------------------------------- rigging
def channel_point(z, side, out=0.62, dy=-0.3):
    y = fs.sheer_y(z) + dy
    if z < CF:
        y = fs.QD_TOP + dy
    return hp(z, y, side, out)


def rigging(bone, hull_bone, masts, bowsprit, sails):
    sa, sb, cap = bowsprit
    d = norm(sb - sa)
    for mname, (z, top1, top2, head, dm) in MASTS.items():
        for side, sn in SIDES:
            za, zb = z - (3.4 if mname != "mizzen" else 2.4), z + 0.4
            y0 = (fs.sheer_y((za + zb) / 2) if z > CF else fs.QD_TOP) - 0.3
            pa, pb = hp(za, y0, side, 0.45), hp(zb, y0, side, 0.45)
            beam(hull_bone, "channel_%s_%s" % (mname, sn), pa, pb, 0.16, "wood_dark", width=0.6, extend=0.05)
            feet, tops = [], []
            nsh = 5 if mname != "mizzen" else 3
            zf = np.linspace(z + 0.1, za + 0.35, nsh)
            for k, zz in enumerate(zf):
                foot = channel_point(zz, side, 0.66, -0.05)
                feet.append(foot + v3(0, 0.36, 0))
                tops.append(v3(side * (dm / 2 + 0.05 + 0.08 * k), top1 - 0.15, z - 0.1 * k))
                disc(bone, "deadeye_%s_%s%d" % (mname, sn, k), foot + v3(0, 0.36, 0), (side, 0, 0), 0.12, 0.08, "dark_wood")
                disc(bone, "deadeye_low_%s_%s%d" % (mname, sn, k), foot, (side, 0, 0), 0.12, 0.08, "dark_wood")
                beam(bone, "lanyard_%s_%s%d" % (mname, sn, k), foot + v3(0, 0.05, 0), foot + v3(0, 0.31, 0), 0.05, "rope")
                beam(bone, "chain_%s_%s%d" % (mname, sn, k), foot - v3(0, 0.06, 0), hp(zz, foot[1] - 1.0, side, 0.38), 0.06, "iron")
            ladder(bone, "%s_lower_%s" % (mname, sn), tops, feet, step=0.55, region="rope_dark", th=0.1)
            s = 1.2 + dm * 0.45
            for k in range(2):
                beam(bone, "futtock_%s_%s%d" % (mname, sn, k), v3(side * s * 0.95, top1 + 0.05, z - 0.4 - 0.6 * k),
                     v3(side * dm * 0.5, top1 - 1.5, z - 0.1 * k), 0.05, "rope")
            if top2 is None:
                r2 = dm * 0.31
                for k in range(2):
                    beam(bone, "%s_topshroud_%s%d" % (mname, sn, k), v3(side * (r2 + 0.04), head - 2.0, z + 0.4),
                         v3(side * (s - 0.1 - 0.5 * k), top1 + 0.32, z - 0.2 - 0.6 * k), 0.05, "rope")
                continue
            r2 = dm * 0.33
            t2 = [v3(side * (r2 + 0.04), top2 - 0.1, z + 0.45) for _ in range(3)]
            f2 = [v3(side * (s - 0.08), top1 + 0.32, z - 0.15 - 0.7 * k) for k in range(3)]
            ladder(bone, "%s_top_%s" % (mname, sn), t2, f2, step=0.45, region="rope_dark", th=0.06)
            beam(bone, "%s_tg_shroud_%s" % (mname, sn), v3(side * 0.22, head - 1.4, z + 0.75), v3(side * 0.95, top2 + 0.05, z + 0.45), 0.05, "rope")
            zb1 = za - (2.6 if mname == "fore" else 2.4)
            beam(bone, "%s_backstay_%s" % (mname, sn), v3(side * (r2 + 0.04), top2 + 0.3, z + 0.4), channel_point(zb1, side, 0.5, 0.0), 0.06, "rope")
    fz, mz, zz = fs.FORE_MAST_Z, fs.MAIN_MAST_Z, fs.MIZZEN_Z
    ropes = [(name, a, b) for name, (a, b) in stays(bowsprit).items()]
    ropes += [
        ("bobstay", cap - d * 0.6 + v3(0, -0.15, 0), v3(0, 1.2, fs.stem_z(1.2) + 0.1)),
        ("jib_halyard", v3(0, MASTS["fore"][2] + 0.1, fz + 0.6), on(stays(bowsprit)["fore_topmast_stay"], 0.32) + v3(0, 0.1, 0)),
    ]
    for side, sn in SIDES:
        ropes.append(("bowsprit_shroud_" + sn, sa + d * 3.0, hp(18.6, 4.2, side, 0.1)))
        ropes.append(("jib_sheet_" + sn, sails["jib_clew"], hp(13.6, fs.sheer_y(13.6) + 0.3, side, -0.1)))
        y, half = SQUARE_SAILS[0][2], SQUARE_SAILS[0][4]
        fo = yard_step("fore", "fore_course")[1]
        arm = gn.braced((side * (half + 0.3), y, fz + fo), fz, BRACE)
        ropes.append(("fore_brace_" + sn, arm, v3(side * 0.6, MASTS["main"][1] - 2.0, mz + 0.2)))
        y, half = SQUARE_SAILS[2][2], SQUARE_SAILS[2][4]
        mo = yard_step("main", "main_course")[1]
        arm = gn.braced((side * (half + 0.3), y, mz + mo), mz, BRACE)
        ropes.append(("main_brace_" + sn, arm, v3(side * 0.5, MASTS["mizzen"][1] - 2.5, zz + 0.2)))
        y, half = SQUARE_SAILS[4][2], SQUARE_SAILS[4][4]
        zo = yard_step("mizzen", "mizzen_course")[1]
        arm = gn.braced((side * (half + 0.3), y, zz + zo), zz, BRACE)
        ropes.append(("mizzen_brace_" + sn, arm, hp(-17.0, fs.KEEP_TOP + 0.4, side, -0.3)))
        for k, (mname, idx) in enumerate((("fore", 0), ("main", 2))):
            sq = SQUARE_SAILS[idx]
            off = yard_step(mname, sq[1])[1]
            mzz = MASTS[mname][0]
            clew = gn.braced((side * (sq[5] + 0.1), sq[3] + 0.1, mzz + off + 0.3), mzz, BRACE)
            zt = mzz - 3.6
            ropes.append(("%s_sheet_%s" % (mname, sn), clew, hp(zt, fs.sheer_y(zt) + 0.4, side, -0.2)))
    for name, a, b in ropes:
        if name in SLACK:
            slack_rope(bone, name, a, b, SLACK[name][0])
        else:
            beam(bone, "rope_" + name, a, b, 0.06, "rope")


SLACK = {
    "fore_brace_p": (0.035, 18), "fore_brace_s": (0.035, 18),
    "main_brace_p": (0.035, 16), "main_brace_s": (0.035, 16),
    "main_topmast_stay": (0.03, 14), "mizzen_topmast_stay": (0.03, 14),
}


# ---------------------------------------------------------------- pennants
def pennant(parent, name, root_pt, w, h, region="pennant", n=4, fly=(0, 0, -1)):
    """A long swallow-tailed pennant in two bones (the animation swings the root half and the fly)."""
    root_pt = v3(*root_pt)
    fly = norm(v3(*fly))
    side = np.cross(v3(0, 1, 0), fly)
    fb = Bone("flag_" + name, origin=tuple(root_pt), parent=parent)
    ft_ = Bone("flag_%s_tip" % name, origin=tuple(root_pt + fly * (w / 2)), parent=fb)
    amp = min(0.22, 0.06 * w)

    def P(s):
        return root_pt + side * (amp * math.sin(2 * math.pi * s) * (0.35 + s)) + fly * (w * s) + v3(0, -0.25 * s * s, 0)
    for half, bone in enumerate((fb, ft_)):
        for k in range(n):
            s0, s1 = (half + k / n) / 2, (half + (k + 1) / n) / 2
            a, b = P(s0), P(s1)
            dd = norm(b - a)
            axes = np.column_stack([np.cross(v3(0, 1, 0), dd), v3(0, 1, 0), dd])
            c = add_cube(bone, "flag_%s_%s%d" % (name, "ab"[half], k), (a + b) / 2 + v3(0, -h / 2, 0), axes,
                         (0.03, h, np.linalg.norm(b - a) + 0.015), {"all": None, "+1": region, "-1": region},
                         stretch=True, u_dir=fly, v_dir=v3(0, -1, 0))
            gn.set_sub(c, (s0, 0, s1, 1), faces=("west", "east"))
    return fb


def pennants(root, masts):
    """Long red swallow-tailed pennants at the three mastheads (the longest on the main mast)."""
    for name, w, h in (("fore", 4.0, 1.05), ("main", 5.2, 1.25), ("mizzen", 4.4, 1.05)):
        mb, mz = masts[name]
        head = MASTS[name][3]
        top = v3(0, head + 0.1, mz)
        beam(mb, "%s_flagstaff" % name, top, top + v3(0, 1.4, 0), 0.08, "iron")
        disc(mb, "%s_flagstaff_knob" % name, top + v3(0, 1.45, 0), (0, 1, 0), 0.08, 0.1, "iron")
        pennant(mb, name, top + v3(0, 1.35, 0), w, h)


# ---------------------------------------------------------------- helm, rudder, crane
def helm(bone):
    hz = fs.HELM_Z
    hub = v3(0, Q + 1.05, hz)
    disc(bone, "helm_pedestal_base", (0, Q + 0.06, hz + 0.1), (0, 1, 0), 0.32, 0.12, "wood_dark", n=3)
    turned(bone, "helm_pedestal", (0, Q + 0.1, hz + 0.1), (0, hub[1] + 0.1, hz + 0.1), [(0, 0.36), (0.12, 0.26), (0.5, 0.3), (0.9, 0.3), (1, 0)],
           "wood_dark")
    round_bar(bone, "helm_axle", (0, hub[1], hz + 0.2), (0, hub[1], hz - 0.14), 0.1, "iron")
    wheel = Bone("helm_wheel", origin=tuple(hub), parent=bone)
    r = 0.66
    zax = v3(0, 0, 1)
    disc(wheel, "helm_hub", hub, zax, 0.14, 0.22, "iron", n=3)
    for k in range(8):
        a = 2 * math.pi * k / 8
        dv = v3(math.cos(a), math.sin(a), 0)
        round_bar(wheel, "helm_spoke_%d" % k, hub + dv * 0.1, hub + dv * r, 0.07, "wood_mid")
        turned(wheel, "helm_handle_%d" % k, hub + dv * (r + 0.04), hub + dv * (r + 0.3), [(0, 0.07), (0.3, 0.1), (0.7, 0.07), (1, 0)], "wood_mid")
    for k in range(16):
        a, a2 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
        p0, p1 = hub + v3(math.cos(a), math.sin(a), 0) * r, hub + v3(math.cos(a2), math.sin(a2), 0) * r
        beam(wheel, "helm_rim_%d" % k, p0, p1, 0.1, "wood_dark", width=0.1, up=zax, extend=0.02)
    bn = v3(1.1, Q, hz + 0.2)
    disc(bone, "binnacle", bn + v3(0, 0.45, 0), (0, 1, 0), 0.24, 0.9, "wood_mid")
    disc(bone, "binnacle_top", bn + v3(0, 0.93, 0), (0, 1, 0), 0.26, 0.06, "bronze")
    disc(bone, "binnacle_card", bn + v3(0, 0.97, 0), (0, 1, 0), 0.17, 0.02, {"all": "bronze", "+2": "compass"})


def rudder(root):
    piv = v3(0, 0.0, TZ - 0.2)
    rb = Bone("rudder", origin=tuple(piv), parent=root)
    zf = TZ - 0.2
    y_top, y_bot = fs.sheer_y(TZ) - 0.6, fs.keel_y(TZ) - 0.05
    bands = list(np.linspace(y_top, y_bot, 7))

    def back(y):
        t = (y_top - y) / (y_top - y_bot)
        return zf - 0.8 - 0.8 * t ** 0.8
    for k in range(len(bands) - 1):
        y0, y1 = bands[k], bands[k + 1]
        board(rb, "rudder_blade_%d" % k, v3(0.22, y0, zf), v3(0.22, y0, back(y0)), v3(0.22, y1, zf), v3(0.22, y1, back(y1)), 0.44, "wood_dark",
              v3(1, 0, 0), overlap=1.0)
    for k, y in enumerate(np.linspace(y_top - 0.4, y_bot + 0.4, 4)):
        for s in (1, -1):
            add_cube(rb, "rudder_strap_%d_%d" % (k, s > 0), (s * 0.235, y, (zf + back(y)) / 2 + 0.05), EYE, (0.03, 0.2, abs(back(y) - zf)), "iron")
        disc(rb, "rudder_gudgeon_%d" % k, (0, y, zf - 0.08), (0, 1, 0), 0.27, 0.18, "iron", n=3)
    round_bar(rb, "rudder_stock", (0, y_bot, zf - 0.08), (0, fs.sheer_y(TZ) + 0.2, zf - 0.08), 0.28, "wood_dark")


def crane(mizzen_bone, lights):
    """The cargo crane of the second reference on the mizzen: a horizontal jib over the waist with a diagonal strut, a
    pulley block at its end, the rope and a hanging crate (it sways with the lanterns)."""
    z0 = fs.MIZZEN_Z + 0.45
    y = Q + 3.0
    end = v3(0.0, y, -6.6)
    beam(mizzen_bone, "crane_jib", v3(0, y, z0 - 0.4), end + v3(0, 0, 0.25), 0.32, "wood_dark", width=0.3)
    beam(mizzen_bone, "crane_strut", v3(0, Q + 1.4, z0), v3(0, y - 0.1, -8.6), 0.24, "wood_dark", width=0.22)
    add_cube(mizzen_bone, "crane_collar", (0, y, fs.MIZZEN_Z), EYE, (0.95, 0.4, 0.95), "iron")
    add_cube(mizzen_bone, "crane_strut_collar", (0, Q + 1.4, fs.MIZZEN_Z), EYE, (0.9, 0.3, 0.9), "iron")
    disc(mizzen_bone, "crane_sheave", end + v3(0, -0.12, 0), (1, 0, 0), 0.2, 0.16, "iron", n=3)
    hb = Bone("lantern_crane_load", origin=tuple(end), parent=lights)
    drop = 2.1
    beam(hb, "crane_rope", end + v3(0, -0.2, 0), end + v3(0, -drop, 0), 0.06, "rope")
    c = end + v3(0, -drop - 0.45, 0)
    gn.g_crate(hb, "crane_crate", c - v3(0, 0.45, 0), s=0.9, wood="wood_mid", batten="wood_dark")
    for s in (1, -1):
        beam(hb, "crane_sling_%d" % (s > 0), end + v3(0, -drop, 0), c + v3(s * 0.42, 0.42, 0), 0.04, "rope")


# ---------------------------------------------------------------- deck fittings
def deck_fittings(bone, detail):
    grating(bone, "grating_main", 0.0, 2.6, 2.0, 2.6, M)
    grating(bone, "grating_aft", 0.0, -6.2, 1.6, 1.6, M)
    gn.g_capstan(bone, "capstan", (0, M, 4.6))
    # coaming and a light rail round the companion hatch (open: the stair goes down to the lower deck)
    x0, x1 = fs.COMPANION_X
    z0, z1 = fs.COMPANION_Z
    for k, (a, b) in enumerate(((v3(x0, M, z0), v3(x0, M, z1)), (v3(x1, M, z0), v3(x1, M, z1)), (v3(x0, M, z0), v3(x1, M, z0)))):
        beam(bone, "companion_coaming_%d" % k, a + v3(0, 0.1, 0), b + v3(0, 0.1, 0), 0.2, "wood_dark", width=0.14, extend=0.07)
    for k, (x, z) in enumerate(((x0, z0), (x1, z0), (x0, z1 - 0.1))):
        add_cube(bone, "companion_post_%d" % k, (x, M + 0.5, z), EYE, (0.12, 1.0, 0.12), "iron")
    beam(bone, "companion_rail_0", (x0, M + 0.95, z0), (x1, M + 0.95, z0), 0.09, "rail", extend=0.05)
    beam(bone, "companion_rail_1", (x0, M + 0.95, z0), (x0, M + 0.95, z1 - 0.1), 0.09, "rail", extend=0.05)
    for z in (fs.FORE_MAST_Z, fs.MAIN_MAST_Z):
        y = F if z > FF else M
        sd.fife_rail(gg, detail, "fife_%d" % int(z + 20), 0.0, z - 1.0, y, half=0.95, wood="wood_dark", pin="iron", rope="rope")
    # the quarterdeck's awning (second reference): off-white canvas on four posts, by the stern rail of the open
    # quarterdeck, starboard
    ax, az = -3.4, -12.0
    for k, (dx, dz) in enumerate(((-0.8, -0.7), (0.8, -0.7), (-0.8, 0.7), (0.8, 0.7))):
        add_cube(detail, "awning_post_%d" % k, (ax + dx, Q + 1.1, az + dz), EYE, (0.1, 2.2, 0.1), "wood_dark")
    add_cube(detail, "awning", (ax, Q + 2.25, az), EYE, (1.9, 0.06, 1.7), "awning")
    for s in (1, -1):
        add_cube(detail, "awning_valance_%d" % (s > 0), (ax, Q + 2.05, az + s * 0.85), EYE, (1.9, 0.4, 0.04), "awning")


# ---------------------------------------------------------------- the rooms, on the interior grid
MAX_TILE = 8
WOOD_ROOM = ("wall_wood", "floor", "ceil")
ROOM_MATERIALS = {"cabin": WOOD_ROOM, "keep": ("wall_stone", "floor", "ceil"), "turret": ("wall_stone", "floor", "ceil"),
                  "mess": ("hold_wall", "floor", "ceil"), "hold": ("hold_wall", "hold_floor", "ceil"), "crew": ("hold_wall", "hold_floor", "ceil")}


def room_at(x, y, z):
    for name, (x0, x1, y0, y1, z0, z1) in fi.ROOMS.items():
        if x0 - 0.01 <= x <= x1 + 0.01 and y0 - 0.51 <= y <= y1 + 0.01 and z0 - 0.01 <= z <= z1 + 0.01:
            return name
    return None


def surfaces(rooms_bone, g):
    """Walls, floors, ceilings, stairs of the rooms: every face between a solid cell and an open cell (dry, door,
    furniture) is drawn, in the material of the room; the masts are drawn round instead."""
    k = g.k
    mast_ = np.zeros(k.shape, dtype=bool)
    for z, foot in fi.MASTS:
        mast_ |= (np.abs(g.X) < 0.5) & (np.abs(g.Z - z) < 0.5) & (g.Y > foot)
    solid = (k == fi.SOLID) & ~mast_
    opened = (k == fi.DRY) | (k >= fi.DOOR) | (k == fi.FURNITURE) | (k == fi.LADDER)
    Cl = fi.CELL
    origin = (fi.X0, fi.Y0, fi.Z0)
    mats = [WOOD_ROOM] + [m for m in dict.fromkeys(ROOM_MATERIALS.values()) if m != WOOD_ROOM]
    mat_index = np.zeros(k.shape, dtype=np.int16)
    for name, box in fi.ROOMS.items():
        mat_index[g.sel(*[b + d for b, d in zip(box, (-0.01, 0.01, -0.51, 0.01, -0.01, 0.01))])] = mats.index(ROOM_MATERIALS[name])
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
            layer = solid & nb_open
            slot = 1 if (a == 1 and s > 0) else 2 if a == 1 else 0
            others = [b for b in range(3) if b != a]
            for idx in range(layer.shape[a]):
                sl = [slice(None)] * 3
                sl[a] = idx
                m2 = layer[tuple(sl)]
                if not m2.any():
                    continue
                plane = origin[a] + (idx + (1 if s > 0 else 0)) * Cl
                al_i = a == 1 or a == 2
                al_j = a == 1 or a == 0
                for (i0, j0, i1, j1, kk) in gc.greedy(m2, nb_mat[tuple(sl)], al_i, al_j):
                    lo, hi = [0.0] * 3, [0.0] * 3
                    b0, b1 = others
                    lo[b0], hi[b0] = origin[b0] + i0 * Cl, origin[b0] + (i1 + 1) * Cl
                    lo[b1], hi[b1] = origin[b1] + j0 * Cl, origin[b1] + (j1 + 1) * Cl
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
                        y_lo, y_hi = lo[1], hi[1]
                        room = room_at(center[0] + s * 0.3 if a == 0 else center[0], center[1], center[2] + s * 0.3 if a == 2 else center[2])
                        ry0, ry1 = (fi.ROOMS[room][2], fi.ROOMS[room][3]) if room else (y_lo, y_hi)
                        hgt = max(0.5, ry1 - ry0)
                        v0 = min(1.0, max(0.0, (ry1 - y_hi) / hgt))
                        v1 = min(1.0, max(v0 + 0.01, (ry1 - y_lo) / hgt))
                        sub = ((hz0 % MAX_TILE) / MAX_TILE, v0, (hz1 % MAX_TILE + 1) / MAX_TILE, v1)
                    for f in cube.faces.values():
                        if f is not None:
                            f["sub"] = sub
                    count += 1
    return count


def beams_below(bone):
    """Deck beams under the decks, across the rooms."""
    for name, (x0, x1, y0, y1, z0, z1) in fi.ROOMS.items():
        if name == "turret":
            continue
        for k, z in enumerate(np.arange(z0 + 1.0, z1 - 0.4, 2.0)):
            if any(abs(z - mz) < 0.7 for mz, _ in fi.MASTS):
                continue
            w = min(x1, fs.hull_x(z, y1) - 0.5) - 0.02
            xa = max(x0, -(fs.hull_x(z, y1) - 0.5)) + 0.02
            beam(bone, "lit_beam_%s_%d" % (name, k), (xa, y1 - 0.12, z), (w, y1 - 0.12, z), 0.24, "wood_dark", width=0.3)


def doors(root, g):
    anims = []
    for d, (name, box) in fi.DOORS.items():
        x0, x1, y0, y1, z0, z1 = box
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        w = 0.16
        thin = 0.14
        depth = sz + 0.1
        for k, at in enumerate((x0 - w / 2, x1 + w / 2)):
            add_cube(root, "lit_door_%d_jamb_%d" % (d, k), v3(at, (y0 + y1 + w) / 2, (z0 + z1) / 2), EYE, (w, sy + w, depth), "wood_dark")
        add_cube(root, "lit_door_%d_lintel" % d, v3((x0 + x1) / 2, y1 + w / 2, (z0 + z1) / 2), EYE, (sx + 2 * w, w, depth), "wood_dark")
        tracks = []
        for leaf, sgn in (("a", 1), ("b", -1)):
            xh = x1 if sgn > 0 else x0
            hinge = v3(xh, y0, (z0 + z1) / 2)
            c = v3(xh - sgn * sx / 4, (y0 + y1) / 2, (z0 + z1) / 2)
            bone = Bone("door_%d_%s" % (d, leaf), origin=tuple(hinge), parent=root)
            add_cube(bone, "lit_door_%d_%s" % (d, leaf), c, EYE, (sx / 2 - 0.02, sy, thin), {"all": "wood_dark", "+3": "door", "-3": "door"},
                     stretch=True, u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0))
            tracks.append((bone, [gg.rot_kf(0.0, (0, 0, 0)), gg.rot_kf(1.0, (0, sgn * 100, 0))]))
        anims.append(gg.animation("door_%d" % d, 1.0, "hold", tracks))
    return anims


def fallbacks(root):
    """Stand-ins of the decoration blocks, shown only when their mod is missing on a client."""
    for i, b in enumerate(fd.BLOCKS):
        x0, x1, y0, y1, z0, z1 = fd.footprint(b["block"], b["x"], b["y"], b["z"], b["yaw"], b["scale"])
        bone = Bone("fallback_%d" % i, parent=root)
        region = fd.FALLBACK_REGION.get(b["block"], "wood_mid")
        if region == "lantern":
            add_cube(bone, "lit_fallback_%d" % i, v3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), EYE, (0.3, 0.42, 0.3),
                     {"all": "lantern", "+2": "iron", "-2": "iron"}, stretch=True)
            continue
        add_cube(bone, "lit_fallback_%d" % i, v3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), EYE,
                 (max(0.04, x1 - x0), max(0.04, y1 - y0), max(0.04, z1 - z0)), region)


# ---------------------------------------------------------------- the model
def build(g):
    root = Bone(NAME)
    hull_bone = Bone("hull", parent=root)
    castle_bone = Bone("sterncastle", parent=root)
    tower_bone = Bone("turret", parent=root)
    deck_bone = Bone("deck", parent=root)
    bow_bone = Bone("bow", parent=root)
    ropes = Bone("ropes", parent=root)
    lights = Bone("lanterns", parent=root)
    detail = Bone("detail", parent=root)
    rooms = Bone("rooms", parent=root)
    fittings = Bone("fittings", parent=root)
    furniture = Bone("furniture", parent=root)
    n = hull(hull_bone)
    cladding(hull_bone, detail)
    bulwarks(hull_bone, detail, lights)
    castle(castle_bone, detail, lights)
    turret(tower_bone, detail, lights)
    decks(deck_bone, castle_bone)
    forecastle(deck_bone, detail, lights)
    bowsprit = bow(bow_bone, detail, lights)
    # the banners on the forecastle's sides (main reference: below the forecastle's stone curb)
    for side, sn in SIDES:
        banner(lights, "banner_fc_" + sn, hp(13.4, fs.sheer_y(13.4) - 0.55, side, 0.38), side, 2.0, 4.0)
    masts = {name: mast(root, fittings, name) for name in MASTS}
    sails_info = []
    sails = sails_and_spars(root, masts, sails_info, bowsprit)
    rigging(ropes, hull_bone, masts, bowsprit, sails)
    pennants(root, masts)
    helm(castle_bone)
    rudder(root)
    crane(masts["mizzen"][0], lights)
    deck_fittings(deck_bone, detail)
    m = surfaces(rooms, g)
    beams_below(fittings)
    for builder, kwargs, solid in fd.CUSTOM:
        gc.CUSTOM_BUILDERS[builder](furniture, **kwargs)
    fallbacks(root)
    return root, n, m, sails_info, sails


def build_animations(root, sails_info):
    kf, rot_kf, animation, find = gg.kf, gg.rot_kf, gg.animation, gg.find
    anims = []
    tracks = []
    for k, (b, side_billow) in enumerate(sails_info):
        ph = 0.37 * k
        if side_billow:
            sc = [kf("scale", t, (s, 1, 1), "catmullrom") for t, s in ((0, 1.0), (0.9, 1.12), (1.8, 0.94), (2.7, 1.07), (3.6, 1.0))]
            rt = [rot_kf(t, (0, 0, a), "catmullrom") for t, a in ((0, 0), (1.2, 0.8), (2.4, -0.6), (3.6, 0))]
        else:
            sc = [kf("scale", t, (1, 1, s), "catmullrom") for t, s in ((0, 1.0), (0.9 + ph * 0.1, 1.1), (1.8, 0.93), (2.7, 1.06), (3.6, 1.0))]
            rt = [rot_kf(t, (a, 0, 0), "catmullrom") for t, a in ((0, 0), (1.2, -1.0), (2.4, 0.6), (3.6, 0))]
        tracks.append((b, sc + rt))
    anims.append(animation("sail_wind", 3.6, "loop", tracks))
    tracks = []
    for b, side_billow in sails_info:
        tracks.append((b, [kf("scale", 0.0, (1, 1, 1)), kf("scale", 1.0, (0, 0, 0) if side_billow else (0.95, 0, 0))]))
    anims.append(animation("sail_furl", 1.0, "hold", tracks))
    wheel, rud = find(root, "helm_wheel"), find(root, "rudder")
    anims.append(animation("steer", 2.0, "hold", [
        (wheel, [rot_kf(0.0, (0, 0, -150)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 0, 150))]),
        (rud, [rot_kf(0.0, (0, -28, 0)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 28, 0))])]))

    def loop_kfs(fn, period, n=8):
        return [rot_kf(round(period * i / n, 4), fn(period * i / n), "catmullrom") for i in range(n + 1)]

    tracks = []
    for k, name in enumerate(("fore", "main", "mizzen")):
        f, ft_ = find(root, "flag_" + name), find(root, "flag_%s_tip" % name)
        w, sh = 2 * math.pi / 1.2, 0.2 * k
        tracks.append((f, loop_kfs(lambda t, sh=sh: (0, 10 * math.cos(w * (t - sh)), 0), 1.2)))
        tracks.append((ft_, loop_kfs(lambda t, sh=sh: (0, -18 * math.cos(w * (t - sh) - 1.75), 0), 1.2)))
    anims.append(animation("flag_wave", 1.2, "loop", tracks))
    tracks = []

    def named(b, prefix):
        out = []
        if b.name.startswith(prefix) and b.name != "lanterns":
            out.append(b)
        for c in b.children:
            out += named(c, prefix)
        return out
    for k, b in enumerate(named(root, "lantern_")):
        a, w, ph = 5, 2 * math.pi / 2.4, 0.35 * k
        if b.name == "lantern_crane_load":
            a = 3
        tracks.append((b, loop_kfs(lambda t, ph=ph, a=a: (a * math.cos(w * (t - ph)), 0, a * 0.6 * math.sin(w * (t - ph))), 2.4)))
    for k, b in enumerate(named(root, "banner_")):
        a, w, ph = 2.5, 2 * math.pi / 2.4, 0.5 * k
        tracks.append((b, loop_kfs(lambda t, ph=ph, a=a: (a * math.cos(w * (t - ph)), 0, 0), 2.4)))
    anims.append(animation("lantern_sway", 2.4, "loop", tracks))
    tracks = []
    period = 4.8
    for k, b in enumerate(named(root, "rope_slack_")):
        amp = SLACK[b.name[len("rope_slack_"):]][1]
        ph = 0.61 * k
        tracks.append((b, loop_kfs(lambda t, amp=amp, ph=ph: (amp * math.sin(2 * math.pi * (t - ph) / period), 0, 0), period)))
    anims.append(animation("rope_sway", period, "loop", tracks))
    return anims


def main():
    g = fi.build()
    fd.build()
    fd.apply_to_grid(g)
    fd.write(os.path.join(ROOT, fd.DECOR_PATH))
    size = g.write(os.path.join(ROOT, fi.GRID_PATH))
    reached, total = fi.walkable_report(g)
    print("decor blocks:", len(fd.BLOCKS), "seats:", len(fd.SEATS), "standing places:", total,
          "unreachable rooms:", [k for k, v in reached.items() if not v])
    root, n, m, sails_info, sails = build(g)
    anims = build_animations(root, sails_info)
    anims += doors(gg.find(root, "rooms"), g)
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    paths = [os.path.join(tex_dir, "entity/%s.png" % NAME), os.path.join(tex_dir, "entity/%s_sails.png" % NAME)]
    ft.make_texture(paths[0])
    ft.make_sail_texture(paths[1], {"jib": sails["jib"]})
    ft.make_item_icon(os.path.join(tex_dir, "item/%s.png" % NAME))
    textures = []
    for k, (p, size_) in enumerate(zip(paths, (ft.SIZE, ft.SAIL_SIZE))):
        with open(p, "rb") as f:
            png = f.read()
        t = gn.texture_entry(os.path.basename(p), size_, png, "entity", NAME + ".png")
        t["id"] = str(k)
        textures.append(t)
    model = gn.export(root, anims, textures, [
        os.path.join(ROOT, "blockbench/%s.bbmodel" % NAME),
        os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/%s.bbmodel" % NAME),
    ], name=NAME, visible_box=(60, 44, 0))
    print("grid bytes:", size, "hull boards:", n, "grid surfaces:", m, "cubes:", len(model["elements"]),
          "animations:", [a["name"] for a in model["animations"]])


if __name__ == "__main__":
    main()
