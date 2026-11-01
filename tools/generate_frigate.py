#!/usr/bin/env python3
"""Generates the Blue-Sailed Frigate (blue_frigate) Blockbench model, its textures, its item icon, its
interior grid and its furniture.

Usage:  python3 tools/generate_frigate.py

Outputs:
  blockbench/blue_frigate.bbmodel                                             (editable, textures embedded)
  src/main/resources/assets/medievalships/models/entity/blue_frigate.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/blue_frigate.png
  src/main/resources/assets/medievalships/textures/entity/blue_frigate_sails.png
  src/main/resources/assets/medievalships/textures/item/blue_frigate.png
  src/main/resources/assets/medievalships/interiors/blue_frigate.grid         (collisions, dry rooms, doors)
  src/main/resources/assets/medievalships/interiors/blue_frigate_decor.json   (furniture of the mods, seats)

Reference: the picture of the "Grand navire aux voiles bleues" (docs/FRIGATE_PLAN.md): a big three-masted
ship with a royal blue hull between a gold band at the waterline and a gold planksheer, dark wood below the
water, a row of red gun-port lids in gold frames, a gold balustrade along the waist, a tall stern castle with
gold-framed lit windows and lanterns at its corners, a raked bow with gold head rails and a long bowsprit,
two big masts with three pale blue square sails each (navy fleurs-de-lis on the topsails and topgallants), a
short mizzen with a topsail and a spanker, two jibs, rope ladders to the tops, tricolour flags at the
mastheads. Inside, the captain's cabin under the quarterdeck and the hold under the main deck; their walls,
floors and ceilings are drawn on the boundaries of the interior grid (tools/frigate_interior.py): what is
drawn is what collides.

Bones used by the mod (keep their names when editing in Blockbench):
  sail_* (sail_wind, sail_furl)  helm_wheel, rudder (steer)  flag_*, flag_*_tip (flag_wave)
  lantern_* (lantern_sway)       door_<k> (door k: 0 = closed, 1 = open)   rooms, furniture, fittings, detail
  rope_slack_* (rope_sway: x axis along the rope, rotated about it)
"""
import math
import os
import sys
import uuid

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import generate_galleon as gn  # noqa: E402
import generate_galley as gg  # noqa: E402
import generate_corsair as gc  # noqa: E402   (generic helpers only: lanterns, sail patches, ladders, flags, slack ropes, furniture)
import ship_details as sd  # noqa: E402
import corsair_furniture as cf  # noqa: E402
import frigate_shape as fs  # noqa: E402
import frigate_interior as fi  # noqa: E402
import frigate_texture as ft  # noqa: E402
import frigate_decor as fd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/blue_frigate/%d" % _uuid_counter[0]))


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
lantern, patch_sail, ladder, flag, grating, slack_rope = gc.lantern, gc.patch_sail, gc.ladder, gc.flag, gc.grating, gc.slack_rope
EYE = np.eye(3)
SIDES = ((1, "p"), (-1, "s"))
DECK_AXES = np.column_stack([v3(0, 0, 1), v3(0, 1, 0), v3(-1, 0, 0)])

M, L, Q, C = fs.MAIN_DECK_Y, fs.LOWER_FLOOR_Y, fs.QUARTERDECK_Y, fs.CABIN_FLOOR_Y
CF = fs.CABIN_FRONT_Z
TZ = fs.TRANSOM_Z
BOW_Z = fs.FORE_SCALE - 0.02   # where the planking closes on the stem
BRACE = math.radians(32)       # square yards braced round (port arms aft): the sails show their faces on the side view
TAFF_RISE = 0.5                # the quarterdeck rail rises by this much from the castle front to the taffrail (visual sheer)


def qd_rail_y(z):
    """Height of the quarterdeck rail foot at z: level with the quarterdeck at the castle front, rising aft."""
    return Q + TAFF_RISE * min(1.0, max(0.0, (CF - z) / (CF - TZ))) ** 1.4


# ---------------------------------------------------------------- hull geometry
def lift(z):
    """Rise of the sheer above its middle height at z."""
    return fs.sheer_y(z) - fs.SHEER_BASE


def band_lift(z, k):
    """Rise of the gold bands: they follow the sheer, and sweep up into the stem at the bow."""
    bow = min(1.0, max(0.0, (z - 11.0) / (BOW_Z - 11.0))) ** 1.7
    return k * lift(z) + (1.6 if k > 0.6 else 1.1) * bow


def hull_rows(z):
    """Points (x, y) of the outer hull section at z (one side, keel to sheer) and the region of each strake:
    dark wood up to the gold band a block above the water, royal blue up to the gold planksheer."""
    ys = fs.sheer_y(min(z, BOW_Z))
    pts = []
    for fx, fy in ((0.0, 1.0), (0.45, 0.9), (0.8, 0.55), (0.97, 0.12)):
        y = fy * fs.keel_y(min(z, fs.HALF_LENGTH + 0.6))
        zz = z - fs.rake(z, y)
        w, yk = fs.half_width(zz), fs.keel_y(min(zz, fs.HALF_LENGTH + 0.6))
        pts.append((max(0.16, fx * w), fy * yk))
    regs = ["hull_brown", "hull_brown", "hull_brown"]
    lo, hi = band_lift(z, 0.35), band_lift(z, 0.8)
    # above the water: one strake a board (stretched: the planking follows the sheer), dark wood, the gold
    # band, three royal blue strakes darker low and brighter high, the gold planksheer
    levels = [(0.3, "strake_brown2"), (0.75 + lo, "strake_brown"), (1.35 + lo, "gold_band"), (2.9 + hi * 0.5, "strake_lo"),
              (4.45 + hi * 0.7, "strake_mid"), (ys - 0.5, "strake_hi"), (ys, "gold_band")]
    for y, reg in levels:
        y = min(y, ys - 0.06 * (len(levels) - len(regs)))
        y = max(y, pts[-1][1] + 0.08)
        pts.append((max(0.16, fs.hull_x(z, y)), y))
        regs.append(reg)
    return pts, regs


STRETCHED = ("strake_lo", "strake_mid", "strake_hi", "strake_brown", "strake_brown2", "gold_band", "castle_panel", "taffrail", "carving")


def strake(bone, name, a0, a1, b0, b1, th, region, outward, overlap=1.03, inner=None):
    """A hull board whose outer face shows its whole texture region (one strake, its seams on its edges)
    when the region is one of the stretched ones; a plain tiled board otherwise."""
    cube = board(bone, name, a0, a1, b0, b1, th, region, outward, overlap=overlap, inner=inner)
    if region in STRETCHED:
        for f, spec in cube.faces.items():
            if spec is not None and spec["region"] == region:
                spec["stretch"] = True
                spec["v_dir"] = v3(0, -1, 0)
    return cube


STATIONS = [TZ, -17.4, -16.6, -15.6, -14.4, -13.0, -11.5, -10.0, -8.5, -7.0, -5.5, -4.0, -2.5, -1.0, 0.5, 2.0, 3.5, 5.0, 6.5, 8.0,
            9.5, 11.0, 12.3, 13.5, 14.6, 15.6, 16.5, 17.3, 17.9, 18.3, BOW_Z, 19.0, 19.5, 20.0, 20.5, 21.0, 21.5, 22.0, 22.4]


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
                mid = (a0 + a1 + b0 + b1) / 4
                t = (a1 + b1) - (a0 + b0)
                outward = norm(v3(side * t[1], -side * t[0], 0) + v3(0, 0, 0.6 * max(0.0, mid[2] - 13) / 6))
                strake(bone, "hull_%s%d_%d" % (sn, i, k), a0, a1, b0, b1, 0.14, regs[k], outward, overlap=1.03,
                       inner="hull_brown" if k < 4 else "hold_wall")
                n += 1
    # keel and its shoe, rising into the stem
    for i in range(len(STATIONS) - 2):
        za, zb = STATIONS[i], STATIONS[i + 1]
        if zb > fs.HALF_LENGTH + 0.2:
            break
        beam(bone, "keel_%d" % i, (0, fs.keel_y(za) - 0.08, za), (0, fs.keel_y(zb) - 0.08, zb), 0.3, "dark_wood", width=0.36, extend=0.06)
    return n


def gold_rail(bone, name, path, h, posts_every=0.5, big_every=0, post_region="gold"):
    """Open gold balustrade along a path: a bottom rail, square gold balusters, a gold cap rail; every
    `big_every` balusters a stout post with a knob (the gold posts of the reference's waist)."""
    k = 0
    for i, (a, b) in enumerate(polyline(path)):
        beam(bone, "%s_cap_%d" % (name, i), a + v3(0, h, 0), b + v3(0, h, 0), 0.14, "rail", width=0.3, extend=0.07)
        beam(bone, "%s_foot_%d" % (name, i), a + v3(0, 0.09, 0), b + v3(0, 0.09, 0), 0.16, "gold", width=0.24, extend=0.05)
        seg = np.linalg.norm(b - a)
        n = max(1, int(round(seg / posts_every)))
        for j in range(n + (1 if i == len(path) - 2 else 0)):
            p = a + (b - a) * (j / n)
            if big_every and k % big_every == 0:
                add_cube(bone, "%s_post_%d" % (name, k), p + v3(0, (h + 0.3) / 2, 0), EYE, (0.3, h + 0.3, 0.3), post_region)
                add_cube(bone, "%s_post_cap_%d" % (name, k), p + v3(0, h + 0.38, 0), EYE, (0.4, 0.16, 0.4), "gold")
                add_cube(bone, "%s_post_knob_%d" % (name, k), p + v3(0, h + 0.53, 0), EYE, (0.22, 0.14, 0.22), "gold")
            else:
                add_cube(bone, "%s_baluster_%d" % (name, k), p + v3(0, h / 2 + 0.05, 0), EYE, (0.12, h - 0.1, 0.12), "gold")
            k += 1


def stern(bone, castle, lights):
    """Flat transom below the castle (dark wood, gold band, blue), and the stern of the castle above it:
    three lit windows of the captain's cabin in gold frames between gold posts, gold fleur-de-lis emblems
    between them, a gold carved band under the quarterdeck, its balustrade and the corner lanterns."""
    z = TZ
    pts, regs = hull_rows(z)
    for k in range(len(pts) - 1):
        (xa, ya), (xb, yb) = pts[k], pts[k + 1]
        for j in range(4):
            fa0, fa1 = -1 + j / 2, -1 + (j + 1) / 2
            strake(bone, "transom_%d_%d" % (k, j), v3(fa0 * xa, ya, z), v3(fa0 * xb, yb, z), v3(fa1 * xa, ya, z), v3(fa1 * xb, yb, z),
                   0.16, regs[k], v3(0, 0, -1), overlap=1.02, inner="hull_brown")
    # the stern of the castle, from the sheer to the quarterdeck: a gold band, the blue panelled wall
    # carrying the windows, a carved gold cornice under the quarterdeck
    ys = fs.sheer_y(z)
    rows = [(ys, ys + 0.3, "gold_band"), (ys + 0.3, Q - 0.45, "castle_panel"), (Q - 0.45, Q - 0.1, "carving"), (Q - 0.1, Q + 0.3, "gold_band")]
    for k, (ya, yb, reg) in enumerate(rows):
        xa, xb = fs.hull_x(z, ya), fs.hull_x(z, yb)
        for j in range(4):
            fa0, fa1 = -1 + j / 2, -1 + (j + 1) / 2
            strake(castle, "stern_wall_%d_%d" % (k, j), v3(fa0 * xa, ya, z), v3(fa0 * xb, yb, z), v3(fa1 * xa, ya, z),
                   v3(fa1 * xb, yb, z), 0.16, reg, v3(0, 0, -1), overlap=1.02, inner="wall_wood")
    # five lit windows of the great cabin across the stern, in gold frames with a continuous gold sill
    # and head rail (the stern gallery of the reference)
    wy = 6.95
    xs = (-2.7, -1.35, 0.0, 1.35, 2.7)
    for j, x in enumerate(xs):
        add_cube(castle, "glow_stern_window_%d" % j, (x, wy, z - 0.1), EYE, (1.05, 1.1, 0.04), "glow_window", stretch=True)
        for s in (1, -1):
            add_cube(castle, "stern_window_jamb_%d_%d" % (j, s > 0), (x + s * 0.6, wy, z - 0.13), EYE, (0.15, 1.3, 0.12), "gold")
        add_cube(castle, "stern_window_in_%d" % j, (x, wy, z + 0.1), EYE, (1.05, 1.1, 0.03), {"all": None, "+3": "window_in"}, stretch=True)
    add_cube(castle, "stern_window_head", (0, wy + 0.62, z - 0.16), EYE, (7.0, 0.16, 0.18), "carving", stretch=True)
    add_cube(castle, "stern_window_sill", (0, wy - 0.62, z - 0.17), EYE, (7.0, 0.16, 0.2), "gold")
    # gold corner pilasters of the castle, carved consoles under the gallery
    for j, x in enumerate((-3.35, 3.35)):
        add_cube(castle, "stern_post_%d" % j, (x, (ys + Q) / 2, z - 0.14), EYE, (0.3, Q - ys, 0.16), "gold")
        add_cube(castle, "stern_console_%d" % j, (x * 0.72, ys + 0.5, z - 0.22), EYE, (0.4, 0.5, 0.3), "carving")
    # the taffrail: a solid carved gold rail across the stern over a blue panel, rising at the stern
    # (the sheer of the reference's high stern), the gold fleur-de-lis emblem in its middle, the great
    # stern lantern on it and two hanging lanterns at its corners
    xq = fs.hull_x(z, Q + 0.5)
    tb, tt = Q + 0.3, Q + TAFF_RISE + 1.35
    add_cube(castle, "taffrail_panel", (0, (tb + tt - 0.35) / 2, z + 0.12), EYE, (2 * xq - 0.3, tt - 0.35 - tb, 0.2),
             {"all": "castle_panel", "-3": "castle_panel", "+3": "wall_wood"}, stretch=True)
    add_cube(castle, "taffrail_carved", (0, tt - 0.18, z + 0.1), EYE, (2 * xq - 0.1, 0.34, 0.26), "taffrail", stretch=True)
    add_cube(castle, "taffrail_cap", (0, tt + 0.06, z + 0.1), EYE, (2 * xq + 0.1, 0.14, 0.4), "rail")
    add_cube(castle, "taffrail_emblem", (0, (tb + tt - 0.35) / 2, z - 0.02), EYE, (1.3, 1.3, 0.06), {"all": "navy", "-3": "stern_lily"},
             stretch=True)
    for j, x in enumerate((-2.2, 2.2)):
        add_cube(castle, "taffrail_emblem_%d" % j, (x, (tb + tt - 0.35) / 2, z - 0.02), EYE, (0.8, 0.8, 0.06), {"all": "navy", "-3": "stern_lily"},
                 stretch=True)
    gn.g_great_lantern(castle, "great_stern_lantern", (0, tt + 0.13, z + 0.1), 1.25, metal="gold")


def waist(bone, detail):
    """The waist from the castle to the bow: the solid blue bulwark strip over the gold planksheer, the
    open gold balustrade on it (stout gold posts with knobs every few balusters), the gold wales along the
    hull, the bow closing round the stem with the head rails sweeping up."""
    zs = [z for z in STATIONS if CF - 0.6 <= z <= 22.4]
    for side, sn in SIDES:
        for i in range(len(zs) - 1):
            za, zb = zs[i], zs[i + 1]
            ya, yb = fs.sheer_y(za), fs.sheer_y(zb)
            ra, rb = fs.rail_y(za), fs.rail_y(zb)
            # solid blue band from the sheer up 0.45, thick (inner face near the collision)
            board(bone, "bulwark_%s%d" % (sn, i), hp(za, ya, side), hp(za, ya + 0.45, side), hp(zb, yb, side), hp(zb, yb + 0.45, side),
                  0.42, "hull_blue", v3(side, 0, 0), overlap=1.03, inner="hull_blue")
            # gold cap rail at the rail height, a little inboard
            beam(bone, "rail_cap_%s%d" % (sn, i), hp(za, ra, side, -0.18), hp(zb, rb, side, -0.18), 0.16, "rail", width=0.42, extend=0.08)
            # the gold wales: under the sheer and along the lower band
            gn.wale_bar(bone, "wale_%s%d" % (sn, i), hp(za, ya - 0.3, side, 0.06), hp(zb, yb - 0.3, side, 0.06), 0.2, 0.16, "gold", extend=0.05)
            if za < BOW_Z - 0.5:
                la, lb = 1.05 + band_lift(za, 0.35), 1.05 + band_lift(zb, 0.35)
                gn.wale_bar(bone, "wale_low_%s%d" % (sn, i), hp(za, la, side, 0.05), hp(min(zb, BOW_Z), lb, side, 0.05), 0.18, 0.14, "gold",
                            extend=0.04)
            seg = np.linalg.norm(hp(zb, ra, side) - hp(za, ra, side))
            if za >= 15.5:
                # the bow: a closed blue bulwark up to the rail
                board(bone, "bow_bulwark_%s%d" % (sn, i), hp(za, ya + 0.43, side), hp(za, ra, side), hp(zb, yb + 0.43, side), hp(zb, rb, side),
                      0.3, "hull_blue", v3(side, 0, 0), overlap=1.03, inner="hull_blue")
                continue
            nb = max(1, int(round(seg / 0.4)))
            for j in range(nb):
                t = (j + 0.5) / nb
                z = za + (zb - za) * t
                y0, y1 = fs.sheer_y(z) + 0.45, fs.rail_y(z) - 0.07
                p0, p1 = hp(z, y0, side, -0.2), hp(z, y1, side, -0.2)
                # turned gold balusters: a slim shaft with a bulb low down and a collar under the cap
                add_cube(detail, "baluster_%s%d_%d" % (sn, i, j), (p0 + p1) / 2, EYE, (0.13, y1 - y0, 0.13), "gold")
                add_cube(detail, "baluster_bulb_%s%d_%d" % (sn, i, j), p0 + (p1 - p0) * 0.3, EYE, (0.24, 0.2, 0.24), "gold")
                add_cube(detail, "baluster_collar_%s%d_%d" % (sn, i, j), p0 + (p1 - p0) * 0.86, EYE, (0.2, 0.1, 0.2), "gold")
    # stout gold posts with knobs along the waist (every ~2.4 blocks), as on the reference
    for side, sn in SIDES:
        for j, z in enumerate(np.arange(CF + 1.2, 15.5, 2.4)):
            r = fs.rail_y(z)
            p = hp(z, r, side, -0.2)
            add_cube(bone, "rail_post_%s%d" % (sn, j), p + v3(0, -0.3, 0), EYE, (0.32, 1.1, 0.32), "gold")
            add_cube(bone, "rail_post_cap_%s%d" % (sn, j), p + v3(0, 0.33, 0), EYE, (0.44, 0.16, 0.44), "gold")
            add_cube(bone, "rail_post_knob_%s%d" % (sn, j), p + v3(0, 0.5, 0), EYE, (0.24, 0.18, 0.24), "gold")
    # the stem head: the two rails meet on a gold knighthead carrying the bow emblem
    zt = 22.3
    yt = fs.rail_y(zt) + 0.1
    add_cube(bone, "knighthead", (0, yt, zt), EYE, (0.9, 0.8, 0.9), "gold")
    add_cube(bone, "knighthead_cap", (0, yt + 0.5, zt), EYE, (1.1, 0.2, 1.1), "gold")
    for side, sn in SIDES:
        add_cube(bone, "bow_lily_" + sn, (side * 0.37, yt - 0.05, zt), EYE, (0.03, 0.5, 0.5), {"all": None, ("+1" if side > 0 else "-1"): "stern_lily"},
                 stretch=True)


def decks(bone, castle):
    """Main deck planking (fore and aft), with the companion hatch left open; the quarterdeck."""
    zs = list(np.arange(CF - 0.5, 21.0, 1.0)) + [21.0]
    cx0, cx1 = fs.COMPANION_X
    cz0, cz1 = fs.COMPANION_Z
    for j in range(len(zs) - 1):
        za, zb = zs[j], zs[j + 1]
        w = min(fs.hull_x(za, M), fs.hull_x(zb, M)) - 0.12
        if w < 0.3:
            continue
        spans = [(-w, w)]
        if za < cz1 - 1e-6 and zb > cz0 + 1e-6:
            spans = [(-w, cx0), (cx1, w)]
        for k, (x0, x1) in enumerate(spans):
            add_cube(bone, "deck_%d_%d" % (j, k), ((x0 + x1) / 2, M - 0.08, (za + zb) / 2), DECK_AXES, (zb - za + 0.01, 0.16, x1 - x0),
                     {"all": "deck", "-2": "dark_wood"})
    # the quarterdeck over the cabin
    zs = list(np.arange(TZ, CF + 1e-6, 1.0))
    if zs[-1] < CF:
        zs.append(CF)
    for j in range(len(zs) - 1):
        za, zb = zs[j], zs[j + 1]
        w = min(fs.hull_x(za, Q), fs.hull_x(zb, Q)) - 0.1
        add_cube(castle, "qdeck_%d" % j, (0, Q - 0.08, (za + zb) / 2), DECK_AXES, (zb - za + 0.01, 0.16, 2 * w), {"all": "deck", "-2": "ceil"})


def castle(bone, lights):
    """The stern castle sides (from the sheer to the quarterdeck): blue boards between gold posts, three
    lit windows of the captain's cabin in gold frames, a gold carved band and a gold wale under the
    quarterdeck, the quarterdeck balustrade; the front bulkhead with the cabin door, its windows and the
    guard rail between the two stairs."""
    zs = [z for z in STATIONS if TZ <= z <= CF] + [CF]
    zs = sorted(set(round(z, 3) for z in zs))
    for side, sn in SIDES:
        for i in range(len(zs) - 1):
            za, zb = zs[i], zs[i + 1]
            ya, yb = fs.sheer_y(za), fs.sheer_y(zb)
            for r, (fa, fb, reg) in enumerate(((0.0, 0.12, "gold_band"), (0.12, 0.72, "castle_panel"), (0.72, 0.86, "carving"),
                                               (0.86, 1.0, "gold_band"))):
                y0a, y1a = ya + (Q + 0.3 - ya) * fa, ya + (Q + 0.3 - ya) * fb
                y0b, y1b = yb + (Q + 0.3 - yb) * fa, yb + (Q + 0.3 - yb) * fb
                strake(bone, "castle_wall_%s%d_%d" % (sn, i, r), hp(za, y0a, side), hp(za, y1a, side), hp(zb, y0b, side), hp(zb, y1b, side),
                       0.16, reg, v3(side, 0, 0), overlap=1.03, inner="wall_wood")
            # the blue bulwark of the quarterdeck over the castle wall, rising aft with the rail
            board(bone, "qd_bulwark_%s%d" % (sn, i), hp(za, Q + 0.3, side), hp(za, qd_rail_y(za) + 0.45, side), hp(zb, Q + 0.3, side),
                  hp(zb, qd_rail_y(zb) + 0.45, side), 0.3, "hull_blue", v3(side, 0, 0), overlap=1.03, inner="hull_blue")
            gn.wale_bar(bone, "castle_wale_%s%d" % (sn, i), hp(za, Q - 0.05, side, 0.06), hp(zb, Q - 0.05, side, 0.06), 0.24, 0.18,
                        "gold", extend=0.05)
            gn.wale_bar(bone, "castle_wale_low_%s%d" % (sn, i), hp(za, ya - 0.3, side, 0.06), hp(zb, yb - 0.3, side, 0.06), 0.2, 0.16,
                        "gold", extend=0.05)
        # gold posts between the windows
        for j, z in enumerate((TZ + 0.25, -16.3, -14.35, -12.45, CF + 0.1)):
            y0 = fs.sheer_y(z)
            p0, p1 = hp(z, y0, side, 0.05), hp(z, Q, side, 0.05)
            add_cube(bone, "castle_post_%s%d" % (sn, j), (p0 + p1) / 2, EYE, (0.26, Q - y0, 0.26), "gold")
        # lit windows of the cabin in gold frames
        for j, z in enumerate((-15.3, -13.4, -11.5)):
            hull_decal(bone, "castle_window_%s%d" % (sn, j), z, 6.95, side, 1.15, 1.05, "glow_window", out=0.02, glow=True)
            hull_decal(bone, "castle_window_head_%s%d" % (sn, j), z, 7.55, side, 1.4, 0.14, "gold", out=0.03, th=0.1, stretch=False)
            hull_decal(bone, "castle_window_sill_%s%d" % (sn, j), z, 6.35, side, 1.4, 0.14, "gold", out=0.03, th=0.1, stretch=False)
            for s in (1, -1):
                hull_decal(bone, "castle_window_jamb_%s%d_%d" % (sn, j, s > 0), z + s * 0.64, 6.95, side, 0.12, 1.34, "gold", out=0.03, th=0.1,
                           stretch=False)
            p, u, v, n = side_frame(z, 6.95, side)
            add_cube(bone, "castle_window_in_%s%d" % (sn, j), p - n * 0.2, np.column_stack([u, v, n]), (1.15, 1.05, 0.03),
                     {"all": None, "-3": "window_in"}, stretch=True)
        # the quarter gallery: a gilded bay on the castle side aft of the windows, two lit lights in it,
        # a carved gold cornice and a moulded base (the reference's stern is rich with gilt work)
        gz0, gz1 = TZ + 0.4, -16.5
        gy0, gy1 = 6.25, 7.75
        gp0, _, _, gn0 = side_frame((gz0 + gz1) / 2, (gy0 + gy1) / 2, side)
        out = 0.42
        gc = gp0 + gn0 * (out / 2 + 0.02)
        frame = np.column_stack([v3(0, 0, -side), v3(0, 1, 0), v3(side, 0, 0)])
        add_cube(bone, "gallery_%s" % sn, gc, frame, (gz1 - gz0, gy1 - gy0, out), {"all": "castle_panel", "-3": None}, stretch=True)
        add_cube(bone, "gallery_cornice_%s" % sn, gc + v3(0, (gy1 - gy0) / 2 + 0.1, 0) + gn0 * 0.06, frame, (gz1 - gz0 + 0.3, 0.22, out + 0.14),
                 "carving", stretch=True)
        add_cube(bone, "gallery_base_%s" % sn, gc - v3(0, (gy1 - gy0) / 2 + 0.1, 0) + gn0 * 0.0, frame, (gz1 - gz0 + 0.2, 0.22, out + 0.04),
                 "gold")
        for j, gz in enumerate((gz0 + 0.5, gz1 - 0.5)):
            wc = v3(0, (gy0 + gy1) / 2, gz) + v3(gc[0], 0, 0) + gn0 * (out / 2 + 0.03)
            add_cube(bone, "glow_gallery_window_%s%d" % (sn, j), wc, frame, (0.7, 0.9, 0.04), "glow_window", stretch=True)
            add_cube(bone, "gallery_window_frame_%s%d" % (sn, j), wc + gn0 * 0.01, frame, (0.9, 0.12, 0.08), "gold")
        # quarterdeck balustrade, rising aft to the taffrail
        path = [hp(z, qd_rail_y(z) + 0.4, side, -0.22) for z in np.linspace(TZ + 0.2, CF - 0.05, 6)]
        gold_rail(bone, "qd_rail_" + sn, path, 0.95, posts_every=0.5, big_every=4)
    # front bulkhead (main deck -> quarterdeck), cabin door frame, two small windows
    bz = CF - 0.08
    wq = fs.hull_x(CF, M) - 0.2
    for side, sn in SIDES:
        x0, x1 = 1.0, wq
        add_cube(bone, "bulkhead_" + sn, (side * (x0 + x1) / 2, (M + Q) / 2, bz), EYE, (x1 - x0, Q - M, 0.16),
                 {"all": "hull_blue2", "-3": "wall_wood"})
        add_cube(bone, "bulkhead_jamb_" + sn, (side * 1.1, (M + Q - 0.5) / 2, CF + 0.04), EYE, (0.2, Q - 0.5 - M + 0.2, 0.14), "gold")
        add_cube(bone, "glow_bulkhead_window_" + sn, (side * 2.7, 6.9, CF + 0.02), EYE, (0.8, 0.7, 0.04), "glow_window", stretch=True)
        add_cube(bone, "bulkhead_window_frame_" + sn, (side * 2.7, 7.32, CF + 0.04), EYE, (1.0, 0.12, 0.1), "gold")
        add_cube(bone, "bulkhead_window_sill_" + sn, (side * 2.7, 6.48, CF + 0.04), EYE, (1.0, 0.12, 0.1), "gold")
    add_cube(bone, "bulkhead_lintel", (0, Q - 0.4, CF + 0.04), EYE, (2.4, 0.3, 0.16), "gold")
    add_cube(bone, "bulkhead_band", (0, Q - 0.05, CF + 0.05), EYE, (2 * wq, 0.2, 0.14), "carving")
    # guard rail along the front of the quarterdeck, between the stairs
    x0 = fs.QD_STAIR_X[0] - 0.05
    gold_rail(bone, "qd_front_rail", [v3(-x0, Q, CF - 0.22), v3(x0, Q, CF - 0.22)], 0.95, posts_every=0.45, big_every=5)
    # stairs to the quarterdeck (as the grid: 6 steps of 0.5), with a hand rail on their inner side
    n = int(round((Q - M) / 0.5))
    for side, sn in SIDES:
        xa, xb = fs.QD_STAIR_X
        for k in range(1, n + 1):
            za = fs.QD_STAIR_Z[0] - k * 0.5
            top = M + k * 0.5
            add_cube(bone, "qd_step_%s%d" % (sn, k), (side * (xa + xb) / 2, (M + top) / 2, za + 0.25), EYE, (xb - xa, top - M, 0.5),
                     {"all": "wood_dark", "+2": "deck"})
        round_bar(bone, "qd_handrail_" + sn, (side * xa, M + 1.0, fs.QD_STAIR_Z[0] + 0.2), (side * xa, Q + 1.0, CF), 0.1, "rail")
        for k, t in enumerate((0.05, 0.5, 0.95)):
            z = fs.QD_STAIR_Z[0] + 0.2 + (CF - fs.QD_STAIR_Z[0] - 0.2) * t
            yb = M + (Q - M) * t
            add_cube(bone, "qd_handrail_post_%s%d" % (sn, k), (side * xa, yb + 0.5, z), EYE, (0.12, 1.0, 0.12), "gold")
    # lanterns under the quarterdeck front, on each side of the door
    for side, sn in SIDES:
        beam(bone, "lantern_bulkhead_arm_" + sn, v3(side * 1.6, Q - 0.6, CF + 0.02), v3(side * 1.6, Q - 0.6, CF + 0.55), 0.08, "iron")
        lantern(lights, "lantern_bulkhead_" + sn, v3(side * 1.6, Q - 0.62, CF + 0.5), drop=0.25, s=0.9)


def bow(bone, lights):
    """Stem, the gold head rails sweeping up to the bowsprit, the catheads with their lanterns, the
    bowsprit (a heavy gold-brown spar rising from the bow) with its cap and the jib-boom."""
    # stem post following the closing bow, from the forefoot to the head
    pts = []
    for j in range(9):
        t = j / 8
        y = fs.keel_y(fs.HALF_LENGTH) - 0.1 + (fs.rail_y(fs.HALF_LENGTH) + 0.3 - fs.keel_y(fs.HALF_LENGTH) + 0.1) * t
        z = BOW_Z + fs.rake(BOW_Z, y) + 0.05 - 0.6 * (1 - t) ** 2.2
        pts.append(v3(0, y, z))
    for j, (a, b) in enumerate(polyline(pts)):
        beam(bone, "stem_%d" % j, a, b, 0.42, "wood_dark", width=0.4, extend=0.08)
    sa, sb = v3(*fs.BOWSPRIT_FOOT), v3(*fs.BOWSPRIT_TIP)
    d = norm(sb - sa)
    cap = sa + d * 7.6
    # the bowsprit is gilded on the reference (a heavy gold spar): gold with dark wooldings
    round_bar(bone, "bowsprit", sa - d * 1.2, cap + d * 0.3, 0.6, "gold")
    for k, t in enumerate((0.6, 2.0, 3.4, 4.8, 6.2)):
        round_bar(bone, "bowsprit_band_%d" % k, sa + d * (t - 0.09), sa + d * (t + 0.09), 0.68, "wood_dark")
    add_cube(bone, "bowsprit_cap", cap + d * 0.15 + v3(0, 0.18, 0), gg.frame_from(d, v3(0, 1, 0)), (0.36, 0.8, 0.5), "gold")
    round_bar(bone, "jib_boom", cap - d * 1.6 + v3(0, 0.36, 0), sb + v3(0, 0.36, 0), 0.32, "mast")
    beam(bone, "dolphin_striker", cap + v3(0, -0.1, 0), cap + v3(0, -1.6, 0.15), 0.12, "wood_dark")
    # the gilded figurehead on the stem head, under the bowsprit: a rearing crowned lion (galleon helper)
    head = v3(0, fs.rail_y(22.3) + 0.1, 22.3)
    gn.lion_figurehead(bone, head + v3(0, -0.75, 0.3), 0.85)
    # the gold head rails: from the waist rail, curving down and forward to the stem head and up again
    # along the bowsprit (the curved gold prow of the reference), four rails one above the other
    for side, sn in SIDES:
        for k, (dy, name, th) in enumerate(((0.0, "head_rail", 0.5), (-0.5, "head_rail_mid", 0.4), (-1.0, "head_rail_low", 0.42),
                                            (-1.5, "head_rail_cheek", 0.4))):
            p0 = hp(14.8, fs.rail_y(14.8) + dy, side, 0.08)
            c = v3(side * 2.6, fs.rail_y(19.0) + dy - 0.5, 19.4)
            p1 = head + v3(side * 0.32, dy + 0.05, -0.15 - 0.25 * k)
            pts_ = bezier(p0, c, p1, 8)
            for q, (a, b) in enumerate(polyline(pts_)):
                cap_rail(bone, "%s_%s%d" % (name, sn, q), a, b, th, th * 1.2, "gold", extend=0.06)
        for q, z in enumerate((16.2, 17.7, 19.2, 20.6, 21.7)):
            a = bezier(hp(14.8, fs.rail_y(14.8), side, 0.08), v3(side * 2.6, fs.rail_y(19.0) - 0.5, 19.4), head + v3(side * 0.32, 0.05, -0.15), 20)
            idx = min(20, max(0, int(round((z - 14.8) / (22.3 - 14.8) * 20))))
            top = a[idx]
            add_cube(bone, "head_rail_post_%s%d" % (sn, q), top + v3(0, -0.62, 0), EYE, (0.26, 1.3, 0.26), "gold")
        # cathead and its lantern (the reference's bow lantern hangs on the side of the bow)
        z = 15.8
        y = fs.rail_y(z) - 0.1
        base = hp(z, y, side, -0.3)
        tip = hp(z + 0.5, y + 0.15, side, 0.9)
        beam(bone, "cathead_" + sn, base, tip, 0.3, "wood_dark", width=0.3)
        disc(bone, "cathead_sheave_" + sn, tip + v3(0, -0.02, 0), v3(0, 0, 1), 0.1, 0.32, "iron")
        lantern(lights, "lantern_cathead_" + sn, tip + v3(0, -0.1, 0), drop=0.6, s=1.4)
        x = side * (fs.hull_x(z + 0.6, 3.0) + 0.25)
        gn.g_anchor(bone, "anchor_" + sn, (x, y - 0.4, z + 0.5), (x, 2.4, z + 0.3), (0, 0, 1))
        disc(bone, "hawse_" + sn, side_frame(16.8, 4.6, side)[0] + v3(side * 0.03, 0, 0), (side, 0, 0), 0.16, 0.06, "iron")
    return sa, sb, cap


# ---------------------------------------------------------------- masts, yards, sails
# Three masts (docs/FRIGATE_PLAN.md): the fore and main masts carry a course, a topsail and a topgallant,
# the short mizzen a topsail and the spanker.
MASTS = {
    # name: (z, lower top y, topmast crosstrees y, masthead y, lower mast diameter)
    "fore": (fs.FORE_MAST_Z, 16.0, 23.6, fs.FORE_MAST_TOP, 0.92),
    "main": (fs.MAIN_MAST_Z, 17.2, 25.0, fs.MAIN_MAST_TOP, 0.96),
    "mizzen": (fs.MIZZEN_Z, 14.8, None, fs.MIZZEN_TOP, 0.72),
}
MAST_FOOT = {"fore": L - 0.4, "main": L - 0.4, "mizzen": Q}
# square sails: mast, name, yard y, foot y, half width at the head, at the foot, belly, texture region
SQUARE_SAILS = [
    ("fore", "fore_course", 15.4, 8.4, 8.0, 8.6, 1.8, "fore_course"),
    ("fore", "fore_topsail", 22.6, 16.6, 6.4, 7.2, 1.45, "fore_topsail"),
    ("fore", "fore_topgallant", 27.6, 23.4, 4.8, 5.6, 1.1, "fore_topgallant"),
    ("main", "main_course", 16.6, 9.0, 8.2, 8.8, 1.85, "main_course"),
    ("main", "main_topsail", 24.0, 17.8, 6.6, 7.4, 1.45, "main_topsail"),
    ("main", "main_topgallant", 29.1, 24.8, 4.9, 5.7, 1.1, "main_topgallant"),
    ("mizzen", "mizzen_topsail", 19.6, 15.6, 4.4, 5.0, 0.95, "mizzen_topsail"),
]


def yard_step(mast_name, name):
    """(z of the mast that carries the yard, offset of the yard before it): the courses on the lower mast,
    the topsails on the topmast (stepped 0.45 before it), the topgallants on the topgallant mast (0.75
    before); the yard hangs just before its mast."""
    z, d = MASTS[mast_name][0], MASTS[mast_name][4]
    if mast_name == "mizzen":
        return z + 0.4, d * 0.62 / 2 + 0.17
    if "topsail" in name:
        return z + 0.45, d * 0.66 / 2 + 0.17
    if "topgallant" in name:
        return z + 0.75, d * 0.66 * 0.62 / 2 + 0.17
    return z, d / 2 + 0.17


GAFF = (v3(0, 15.0, fs.MIZZEN_Z - 0.4), v3(0, 19.0, -18.6))    # throat, peak
BOOM = (v3(0, 10.7, fs.MIZZEN_Z - 0.4), v3(0, fs.BOOM_Y, fs.BOOM_END_Z))     # gooseneck, end


def mast(root, fittings, name):
    z, top1, top2, head, d = MASTS[name]
    foot = MAST_FOOT[name]
    deck = Q if name == "mizzen" else M
    mb = Bone("mast_" + name, origin=(0, deck, z), parent=root)
    # below the main deck the mast is drawn with the rooms (lit by their lamps)
    if foot < deck:
        round_bar(fittings, "lit_mast_%s_below" % name, (0, foot, z), (0, deck, z), d + 0.05, "mast")
        disc(fittings, "lit_mast_%s_collar" % name, (0, L + 0.15, z), (0, 1, 0), d / 2 + 0.16, 0.3, "wood_dark", n=3)
    round_bar(mb, name + "_lower", (0, deck - 0.1, z), (0, top1 + 0.9, z), d, "mast")
    disc(mb, name + "_partners", (0, deck + 0.12, z), (0, 1, 0), d / 2 + 0.22, 0.24, "wood_dark", n=3)
    # gold bands (the reference's masts are banded)
    for k, y in enumerate(np.arange(deck + 1.6, top1 - 0.6, 1.9)):
        round_bar(mb, "%s_band_%d" % (name, k), (0, y - 0.09, z), (0, y + 0.09, z), d + 0.08, "gold")
    # the top: a square platform on trestle trees, with a low rim
    s = 1.2 + d * 0.4
    add_cube(mb, name + "_top", (0, top1 + 0.06, z - 0.15), EYE, (2 * s, 0.14, 2 * s * 0.8), {"all": "wood_dark", "+2": "deck"})
    for sx in (1, -1):
        beam(mb, "%s_trestle_%d" % (name, sx > 0), (sx * d * 0.45, top1 - 0.12, z - s), (sx * d * 0.45, top1 - 0.12, z + s * 0.7), 0.2,
             "wood_dark", width=0.16)
        beam(mb, "%s_crosstree_%d" % (name, sx > 0), (-s, top1 - 0.06, z + sx * 0.5), (s, top1 - 0.06, z + sx * 0.5), 0.14, "wood_dark",
             width=0.14)
    for k, (a, b) in enumerate(polyline([v3(-s, 0, z - 0.15 - s * 0.8), v3(s, 0, z - 0.15 - s * 0.8), v3(s, 0, z - 0.15 + s * 0.8),
                                         v3(-s, 0, z - 0.15 + s * 0.8)], closed=True)):
        beam(mb, "%s_top_rim_%d" % (name, k), a + v3(0, top1 + 0.3, 0), b + v3(0, top1 + 0.3, 0), 0.32, "gold", width=0.1, extend=0.05)
    add_cube(mb, name + "_cap", (0, top1 + 0.95, z + 0.2), EYE, (d + 0.2, 0.3, 1.4), "gold")
    if top2 is not None:
        d2 = d * 0.66
        round_bar(mb, name + "_topmast", (0, top1 - 0.5, z + 0.45), (0, top2 + 0.8, z + 0.45), d2, "mast")
        for k, y in enumerate((top1 + 2.5, top1 + 5.0)):
            round_bar(mb, "%s_topmast_band_%d" % (name, k), (0, y - 0.07, z + 0.45), (0, y + 0.07, z + 0.45), d2 + 0.06, "gold")
        s2 = 0.95
        for sx in (1, -1):
            beam(mb, "%s_crosstree2_%d" % (name, sx > 0), (-s2, top2, z + 0.45 + sx * 0.3), (s2, top2, z + 0.45 + sx * 0.3), 0.12,
                 "wood_dark", width=0.12)
        add_cube(mb, name + "_cap2", (0, top2 + 0.85, z + 0.6), EYE, (d2 + 0.16, 0.24, 1.0), "gold")
        round_bar(mb, name + "_topgallant_mast", (0, top2 - 0.4, z + 0.75), (0, head, z + 0.75), d2 * 0.62, "mast")
        disc(mb, name + "_truck", (0, head + 0.05, z + 0.75), (0, 1, 0), 0.2, 0.14, "gold", n=3)
        mz = z + 0.75
    else:
        round_bar(mb, name + "_topmast", (0, top1 - 0.5, z + 0.4), (0, head, z + 0.4), d * 0.62, "mast")
        disc(mb, name + "_truck", (0, head + 0.05, z + 0.4), (0, 1, 0), 0.18, 0.14, "gold", n=3)
        mz = z + 0.4
    return mb, mz


def square_sail(mb, sails_info, name, z, y_top, y_foot, half_top, half_foot, belly, region, off=0.42):
    """Yard (braced round with its sail) and the sail billowed forward."""
    br = Bone("brace_" + name, origin=(0, y_top, z), parent=mb)
    zz = z + off
    round_bar(br, name + "_yard", (-half_top - 0.5, y_top, zz), (half_top + 0.5, y_top, zz), 0.28, "gold", extend=0.05)
    add_cube(br, name + "_sling", (0, y_top, zz - 0.1), EYE, (0.42, 0.38, 0.38), "rope")
    for sx in (1, -1):
        add_cube(br, "%s_yardarm_%d" % (name, sx > 0), (sx * (half_top + 0.35), y_top, zz), EYE, (0.12, 0.34, 0.34), "gold")
    beam(br, name + "_roll", (-half_top * 0.94, y_top - 0.22, zz + 0.05), (half_top * 0.94, y_top - 0.22, zz + 0.05), 0.26, "cloth_roll")
    sb = Bone("sail_" + name, origin=(0, y_top, zz), parent=br)
    height = y_top - y_foot
    cols, rows = ft.SAIL_CELLS[region]
    origin = v3(0, y_top - 0.14, zz + 0.05)

    def P(s, t):
        half = half_top + (half_foot - half_top) * t
        x = (2 * s - 1) * half
        bel = belly * math.sin(math.pi * min(1.0, t * 0.78)) * (0.35 + 0.65 * (1 - (2 * s - 1) ** 2))
        drop = t * height * (1 - 0.05 * t * t * (1 - (2 * s - 1) ** 2))
        return origin + v3(x, -drop, bel)
    patch_sail(sb, name, P, v3(0, 0, 1), region, cols, rows)
    sails_info.append((sb, False))
    br.rot = ry(BRACE)
    return br


def quad_sail(bone, name, throat, peak, tack, clew, belly, N, region):
    """Fore-and-aft four sided sail (spanker): head along the gaff, luff on the mast, foot on the boom."""
    cols, rows = ft.SAIL_CELLS[region]

    def P(s, t):
        top = throat + (peak - throat) * s
        bot = tack + (clew - tack) * s
        p = top + (bot - top) * t
        return p + N * belly * math.sin(math.pi * s) ** 0.8 * math.sin(math.pi * min(1.0, t * 0.9 + 0.05))
    patch_sail(bone, name, P, N, region, cols, rows)


def tri_sail(bone, name, head, tack, clew, belly, N, region):
    """Triangular sail; the jibs share one triangle of their texture region (the clew is slid along the luff)."""
    clew = gn.jib_clew(head, tack, clew)
    cols, rows = ft.SAIL_CELLS[region]
    return gn.g_tri_sail(bone, name, head, tack, clew, belly, N, region, cols, rows, round_=0.45), clew


def stays(bowsprit):
    """Ends of the stays (name -> (upper end, lower end)): the fore stays to the bowsprit, the cap and
    the jib-boom end (the jibs are set on the topmast and topgallant stays), the main stays forward to the
    fore mast, the mizzen stays to the main mast."""
    sa, sb, cap = bowsprit
    d = norm(sb - sa)
    F, N_, Z_ = MASTS["fore"], MASTS["main"], MASTS["mizzen"]
    fz, mz, zz = F[0], N_[0], Z_[0]
    return {
        "fore_stay": (v3(0, F[1] - 0.25, fz + 0.3), sa + d * 3.0 + v3(0, 0.25, 0)),
        "fore_topmast_stay": (v3(0, F[2] - 0.2, fz + 0.6), cap + v3(0, 0.3, 0)),
        "fore_tg_stay": (v3(0, F[3] - 1.3, fz + 0.9), sb + v3(0, 0.3, 0)),
        "main_stay": (v3(0, N_[1] - 0.2, mz + 0.45), v3(0, M + 0.25, fz - 2.2)),
        "main_topmast_stay": (v3(0, N_[2] - 0.2, mz + 0.6), v3(0, F[1] + 0.45, fz - 0.35)),
        "main_tg_stay": (v3(0, N_[3] - 1.3, mz + 0.9), v3(0, F[2] + 0.25, fz + 0.3)),
        "mizzen_stay": (v3(0, Z_[1] - 0.3, zz + 0.3), v3(0, M + 6.0, mz - 0.5)),
        "mizzen_topmast_stay": (v3(0, Z_[3] - 1.2, zz + 0.5), v3(0, N_[1] + 0.4, mz - 0.4)),
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
    # the mizzen gaff and boom with the spanker
    zmb = masts["mizzen"][0]
    round_bar(zmb, "gaff", GAFF[0], GAFF[1] + norm(GAFF[1] - GAFF[0]) * 0.3, 0.22, "mast")
    round_bar(zmb, "boom", BOOM[0], BOOM[1] + norm(BOOM[1] - BOOM[0]) * 0.2, 0.28, "mast")
    for k, p in enumerate((GAFF[0], BOOM[0])):
        add_cube(zmb, "gaff_jaws_%d" % k, p + v3(0, 0, 0.12), EYE, (0.5, 0.3, 0.3), "wood_dark")
    for k, t in enumerate(np.linspace(0.12, 0.92, 6)):
        p = GAFF[0] + (GAFF[1] - GAFF[0]) * t
        add_cube(zmb, "gaff_lacing_%d" % k, p - v3(0, 0.12, 0), gg.frame_from(norm(GAFF[1] - GAFF[0]), v3(0, 1, 0)), (0.12, 0.3, 0.3), "rope")
    sp = Bone("sail_spanker", origin=tuple(GAFF[0]), parent=zmb)
    quad_sail(sp, "spanker", GAFF[0] + v3(0, -0.15, -0.15), GAFF[1] + v3(0, -0.15, 0.2), BOOM[0] + v3(0, 0.15, -0.15),
              BOOM[1] + v3(0, 0.15, 1.2), 0.8, v3(-1, 0, 0), "spanker")
    sails_info.append((sp, True))
    # two jibs on the fore topmast and topgallant stays, flying over the bowsprit
    st_ = stays(bowsprit)
    jb = Bone("sail_jibs", origin=tuple(cap), parent=root)
    jib_tri, outer_clew = tri_sail(jb, "jib_outer", on(st_["fore_tg_stay"], 0.2), on(st_["fore_tg_stay"], 0.9), v3(0, 14.0, 15.6), 0.95,
                                   v3(-1, 0, 0), "jib")
    _, inner_clew = tri_sail(jb, "jib_inner", on(st_["fore_topmast_stay"], 0.18), on(st_["fore_topmast_stay"], 0.9), v3(0, 11.6, 12.8), 0.85,
                             v3(-1, 0, 0), "jib")
    sails_info.append((jb, True))
    return {"jib": jib_tri, "jib_clews": (outer_clew, inner_clew)}


# ---------------------------------------------------------------- rigging
def channel_point(z, side, out=0.48, dy=-0.3):
    y = fs.rail_y(z) + dy
    if z < CF:
        y = Q + 0.7 + dy
    return hp(z, y, side, out)


def rigging(bone, hull_bone, masts, bowsprit, sails):
    sa, sb, cap = bowsprit
    d = norm(sb - sa)
    for mname, (z, top1, top2, head, dm) in MASTS.items():
        for side, sn in SIDES:
            # the channel: a ledge on the hull side carrying the deadeyes of the lower shrouds
            za, zb = z - (3.6 if mname != 'mizzen' else 2.7), z + 0.4
            y0 = (fs.rail_y((za + zb) / 2) if z > CF else Q + 0.7) - 0.3
            pa, pb = hp(za, y0, side, 0.3), hp(zb, y0, side, 0.3)
            beam(hull_bone, "channel_%s_%s" % (mname, sn), pa, pb, 0.14, "wood_dark", width=0.6, extend=0.05)
            for j, zk in enumerate((za + 0.3, zb - 0.3)):
                beam(hull_bone, "channel_knee_%s_%s%d" % (mname, sn, j), hp(zk, y0 - 0.7, side, 0.02), hp(zk, y0 - 0.05, side, 0.5), 0.12,
                     "wood_dark", width=0.12)
            feet, tops = [], []
            nsh = 5 if mname != "mizzen" else 3
            zf = np.linspace(z + 0.1, za + 0.35, nsh)
            for k, zz in enumerate(zf):
                foot = channel_point(zz, side, 0.52, -0.05)
                feet.append(foot + v3(0, 0.36, 0))
                tops.append(v3(side * (dm / 2 + 0.05 + 0.08 * k), top1 - 0.15, z - 0.1 * k))
                disc(bone, "deadeye_%s_%s%d" % (mname, sn, k), foot + v3(0, 0.36, 0), (side, 0, 0), 0.12, 0.08, "dark_wood")
                disc(bone, "deadeye_low_%s_%s%d" % (mname, sn, k), foot, (side, 0, 0), 0.12, 0.08, "dark_wood")
                beam(bone, "lanyard_%s_%s%d" % (mname, sn, k), foot + v3(0, 0.05, 0), foot + v3(0, 0.31, 0), 0.05, "rope")
                beam(bone, "chain_%s_%s%d" % (mname, sn, k), foot - v3(0, 0.06, 0), hp(zz, foot[1] - 1.1, side, 0.04), 0.06, "iron")
            ladder(bone, "%s_lower_%s" % (mname, sn), tops, feet, step=0.5, region="rope_dark", th=0.095)
            # futtock shrouds under the top
            s = 1.2 + dm * 0.4
            for k in range(2):
                beam(bone, "futtock_%s_%s%d" % (mname, sn, k), v3(side * s * 0.95, top1 + 0.05, z - 0.4 - 0.6 * k),
                     v3(side * dm * 0.5, top1 - 1.5, z - 0.1 * k), 0.05, "rope")
            if top2 is None:
                # mizzen: topmast shrouds straight to the crosstrees, and a backstay
                r2 = dm * 0.31
                for k in range(2):
                    beam(bone, "%s_topshroud_%s%d" % (mname, sn, k), v3(side * (r2 + 0.04), head - 1.6, z + 0.4),
                         v3(side * (s - 0.1 - 0.5 * k), top1 + 0.32, z - 0.2 - 0.6 * k), 0.05, "rope")
                beam(bone, "%s_backstay_%s" % (mname, sn), v3(side * 0.2, head - 1.3, z + 0.4), channel_point(za - 1.6, side, 0.36, 0.0), 0.05, "rope")
                continue
            # topmast shrouds (a smaller ladder from the rim of the top to the crosstrees)
            r2 = dm * 0.33
            t2 = [v3(side * (r2 + 0.04), top2 - 0.1, z + 0.45) for _ in range(3)]
            f2 = [v3(side * (s - 0.08), top1 + 0.32, z - 0.15 - 0.7 * k) for k in range(3)]
            ladder(bone, "%s_top_%s" % (mname, sn), t2, f2, step=0.45, region="rope_dark", th=0.07)
            # topgallant shrouds
            beam(bone, "%s_tg_shroud_%s" % (mname, sn), v3(side * 0.22, head - 1.6, z + 0.75), v3(side * 0.95, top2 + 0.05, z + 0.45), 0.05,
                 "rope")
            # the topmast backstays: long rope ladders from the crosstrees down to the rail well aft of the
            # mast (the diagonal ladders of the reference), and the topgallant backstays
            zb1 = za - (4.2 if mname == "fore" else 2.2)
            ladder(bone, "%s_backstay_%s" % (mname, sn), [v3(side * (r2 + 0.04), top2 + 0.3, z + 0.4), v3(side * (r2 + 0.08), top2 + 0.1, z + 0.3)],
                   [channel_point(zb1, side, 0.36, 0.0), channel_point(zb1 - 0.7, side, 0.36, 0.0)], step=0.5, region="rope_dark", th=0.07)
            beam(bone, "%s_tg_backstay_%s" % (mname, sn), v3(side * 0.22, head - 1.2, z + 0.75), channel_point(zb1 - 1.6, side, 0.4, 0.0),
                 0.05, "rope")
    fz, mz, zz = fs.FORE_MAST_Z, fs.MAIN_MAST_Z, fs.MIZZEN_Z
    ropes = [(name, a, b) for name, (a, b) in stays(bowsprit).items()]
    peak = GAFF[1] + norm(GAFF[1] - GAFF[0]) * 0.25
    ropes += [
        ("bobstay", cap - d * 0.6 + v3(0, -0.15, 0), v3(0, 1.2, BOW_Z + fs.rake(BOW_Z, 1.2) + 0.1)),
        ("martingale", cap + v3(0, -1.55, 0.15), sb + v3(0, 0.2, 0)),
        ("martingale_back", cap + v3(0, -1.55, 0.15), v3(0, 4.6, BOW_Z + fs.rake(BOW_Z, 4.6) + 0.1)),
        ("peak_halyard", v3(0, fs.MIZZEN_TOP - 0.6, zz + 0.4), GAFF[0] + (GAFF[1] - GAFF[0]) * 0.72 + v3(0, 0.12, 0)),
        ("throat_halyard", v3(0, MASTS["mizzen"][1] + 1.2, zz + 0.4), GAFF[0] + (GAFF[1] - GAFF[0]) * 0.3 + v3(0, 0.12, 0)),
        ("spanker_sheet", BOOM[1] + v3(0, -0.1, 0.4), v3(0, Q + 1.0, TZ + 0.3)),
        ("main_stay_ring", v3(0, M + 0.1, fz - 2.2), v3(0, M + 0.25, fz - 2.2)),
    ]
    outer_clew, inner_clew = sails["jib_clews"]
    for side, sn in SIDES:
        ropes.append(("jib_guy_" + sn, sb + v3(0, 0.25, 0), hp(17.2, fs.rail_y(17.2), side, 0.2)))
        ropes.append(("bowsprit_shroud_" + sn, sa + d * 4.0, hp(18.2, 3.6, side, 0.05)))
        ropes.append(("jib_sheet_outer_" + sn, outer_clew, hp(12.6, fs.rail_y(12.6), side, -0.1)))
        ropes.append(("jib_sheet_inner_" + sn, inner_clew, hp(10.6, fs.rail_y(10.6), side, -0.1)))
        # braces: the fore yard's lead aft to the main mast, the main yard's to the mizzen, the mizzen
        # topsail's to the quarterdeck rail
        y, half = SQUARE_SAILS[0][2], SQUARE_SAILS[0][4]
        fo = yard_step("fore", "fore_course")[1]
        arm = gn.braced((side * (half + 0.3), y, fz + fo), fz, BRACE)
        ropes.append(("fore_brace_" + sn, arm, v3(side * 0.6, MASTS["main"][1] - 2.0, mz + 0.2)))
        y, half = SQUARE_SAILS[3][2], SQUARE_SAILS[3][4]
        mo = yard_step("main", "main_course")[1]
        arm = gn.braced((side * (half + 0.3), y, mz + mo), mz, BRACE)
        ropes.append(("main_brace_" + sn, arm, v3(side * 0.5, MASTS["mizzen"][1] - 1.5, zz + 0.2)))
        y, half = SQUARE_SAILS[6][2], SQUARE_SAILS[6][4]
        zo = yard_step("mizzen", "mizzen_topsail")[1]
        arm = gn.braced((side * (half + 0.3), y, zz + zo), zz, BRACE)
        ropes.append(("mizzen_brace_" + sn, arm, hp(-17.5, Q + 1.0, side, -0.25)))
        # sheets of the courses from their clews down to the rail
        for k, (mname, idx) in enumerate((("fore", 0), ("main", 3))):
            sq = SQUARE_SAILS[idx]
            off = yard_step(mname, sq[1])[1]
            mzz = MASTS[mname][0]
            clew = gn.braced((side * (sq[5] + 0.1), sq[3] + 0.1, mzz + off + 0.3), mzz, BRACE)
            ropes.append(("%s_sheet_%s" % (mname, sn), clew, hp(mzz - 4.0, fs.rail_y(mzz - 4.0), side, -0.15)))
    for name, a, b in ropes:
        if name in SLACK:
            slack_rope(bone, name, a, b, SLACK[name][0])
        else:
            beam(bone, "rope_" + name, a, b, 0.06, "rope")


# Running rigging and the stays between the masts hang slack and sway a little about the line joining
# their two ends (animation rope_sway; the ends stay made fast): rope -> (sag as a fraction of its length,
# swing amplitude in degrees)
SLACK = {
    "fore_brace_p": (0.035, 18), "fore_brace_s": (0.035, 18),
    "main_brace_p": (0.035, 16), "main_brace_s": (0.035, 16),
    "main_topmast_stay": (0.03, 14), "main_tg_stay": (0.03, 14),
    "mizzen_topmast_stay": (0.03, 14),
    "jib_guy_p": (0.03, 15), "jib_guy_s": (0.03, 15),
}
gc.SLACK = dict(gc.SLACK, **SLACK)   # gc.slack_rope reads nothing from it, but keep the two tables consistent


# ---------------------------------------------------------------- flags
def flags(root, masts):
    """Tricolour flags at the three mastheads (the biggest on the fore mast, as on the reference)."""
    for name, w, h in (("fore", 3.2, 2.0), ("main", 2.8, 1.8), ("mizzen", 2.4, 1.5)):
        mb, mz = masts[name]
        head = MASTS[name][3]
        top = v3(0, head + 0.1, mz)
        beam(mb, "%s_flagstaff" % name, top, top + v3(0, h + 0.4, 0), 0.08, "wood_dark")
        disc(mb, "%s_flagstaff_knob" % name, top + v3(0, h + 0.45, 0), (0, 1, 0), 0.08, 0.1, "gold")
        flag(mb, name, top + v3(0, h + 0.35, 0), w, h)


# ---------------------------------------------------------------- helm, rudder
def helm(bone):
    hz = fs.HELM_Z
    hub = v3(0, Q + 1.05, hz)
    disc(bone, "helm_pedestal_base", (0, Q + 0.06, hz + 0.1), (0, 1, 0), 0.32, 0.12, "wood_dark", n=3)
    turned(bone, "helm_pedestal", (0, Q + 0.1, hz + 0.1), (0, hub[1] + 0.1, hz + 0.1),
           [(0, 0.36), (0.12, 0.26), (0.5, 0.3), (0.9, 0.3), (1, 0)], "wood_dark")
    round_bar(bone, "helm_axle", (0, hub[1], hz + 0.2), (0, hub[1], hz - 0.14), 0.1, "iron")
    wheel = Bone("helm_wheel", origin=tuple(hub), parent=bone)
    r = 0.66
    zax = v3(0, 0, 1)
    disc(wheel, "helm_hub", hub, zax, 0.14, 0.22, "gold", n=3)
    for k in range(8):
        a = 2 * math.pi * k / 8
        dv = v3(math.cos(a), math.sin(a), 0)
        round_bar(wheel, "helm_spoke_%d" % k, hub + dv * 0.1, hub + dv * r, 0.07, "wood_mid")
        turned(wheel, "helm_handle_%d" % k, hub + dv * (r + 0.04), hub + dv * (r + 0.3), [(0, 0.07), (0.3, 0.1), (0.7, 0.07), (1, 0)],
               "gold")
    for k in range(16):
        a, a2 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
        p0, p1 = hub + v3(math.cos(a), math.sin(a), 0) * r, hub + v3(math.cos(a2), math.sin(a2), 0) * r
        beam(wheel, "helm_rim_%d" % k, p0, p1, 0.1, "wood_dark", width=0.1, up=zax, extend=0.02)
    # binnacle and a compass beside the wheel
    bn = v3(1.1, Q, hz + 0.3)
    disc(bone, "binnacle", bn + v3(0, 0.45, 0), (0, 1, 0), 0.24, 0.9, "wood_mid")
    disc(bone, "binnacle_top", bn + v3(0, 0.93, 0), (0, 1, 0), 0.26, 0.06, "gold")
    disc(bone, "binnacle_card", bn + v3(0, 0.97, 0), (0, 1, 0), 0.17, 0.02, {"all": "gold", "+2": "compass"})


def rudder(root):
    piv = v3(0, 0.0, TZ - 0.15)
    rb = Bone("rudder", origin=tuple(piv), parent=root)
    zf = TZ - 0.18
    y_top, y_bot = fs.sheer_y(TZ) - 0.5, fs.keel_y(TZ) - 0.05
    bands = list(np.linspace(y_top, y_bot, 7))

    def back(y):
        t = (y_top - y) / (y_top - y_bot)
        return zf - 0.5 - 0.6 * t ** 0.8
    for k in range(len(bands) - 1):
        y0, y1 = bands[k], bands[k + 1]
        board(rb, "rudder_blade_%d" % k, v3(0.1, y0, zf), v3(0.1, y0, back(y0)), v3(0.1, y1, zf), v3(0.1, y1, back(y1)), 0.2, "wood_dark",
              v3(1, 0, 0), overlap=1.0)
    for k, y in enumerate(np.linspace(y_top - 0.4, y_bot + 0.4, 4)):
        for s in (1, -1):
            add_cube(rb, "rudder_strap_%d_%d" % (k, s > 0), (s * 0.12, y, (zf + back(y)) / 2 + 0.05), EYE, (0.03, 0.1, abs(back(y) - zf)),
                     "iron")
    round_bar(rb, "rudder_stock", (0, y_bot, zf - 0.08), (0, fs.sheer_y(TZ) + 0.3, zf - 0.08), 0.26, "wood_dark")


# ---------------------------------------------------------------- deck fittings, gun ports
def deck_fittings(bone, detail):
    # hatches before the fore mast and between the masts; the capstan abaft the fore mast
    grating(bone, "grating_fore", 0.0, 12.5, 2.0, 2.0, M)
    grating(bone, "grating_main", 0.0, 1.0, 2.0, 2.0, M)
    gn.g_capstan(bone, "capstan", (0, M, 9.5))
    # the eye bolt of the main stay on the deck
    disc(bone, "main_stay_eyebolt", (0, M + 0.04, fs.FORE_MAST_Z - 2.2), (0, 1, 0), 0.16, 0.08, "iron")
    # coaming and a light gold rail round the companion hatch (open: the stair goes down to the hold)
    x0, x1 = fs.COMPANION_X
    z0, z1 = fs.COMPANION_Z
    for k, (a, b) in enumerate(((v3(x0, M, z0), v3(x0, M, z1)), (v3(x1, M, z0), v3(x1, M, z1)), (v3(x0, M, z0), v3(x1, M, z0)))):
        beam(bone, "companion_coaming_%d" % k, a + v3(0, 0.1, 0), b + v3(0, 0.1, 0), 0.2, "wood_dark", width=0.14, extend=0.07)
    for k, (x, z) in enumerate(((x0, z0), (x1, z0), (x0, z1 - 0.1))):
        add_cube(bone, "companion_post_%d" % k, (x, M + 0.5, z), EYE, (0.12, 1.0, 0.12), "gold")
    beam(bone, "companion_rail_0", (x0, M + 0.95, z0), (x1, M + 0.95, z0), 0.09, "rail", extend=0.05)
    beam(bone, "companion_rail_1", (x0, M + 0.95, z0), (x0, M + 0.95, z1 - 0.1), 0.09, "rail", extend=0.05)
    sd.bell(gg, bone, "bell", (0.0, M, fs.FORE_MAST_Z + 1.7), metal="bronze", wood="wood_dark")
    # the fife rails round the two big masts (belaying pins for the running rigging)
    for z in (fs.FORE_MAST_Z, fs.MAIN_MAST_Z):
        sd.fife_rail(gg, detail, "fife_%d" % int(z + 20), 0.0, z - 1.0, M, half=0.95, wood="wood_dark", pin="gold", rope="rope")


def gun_ports(bone):
    """The row of red gun-port lids in their gold frames along each side (closed, decorative)."""
    for side, sn in SIDES:
        for k, z in enumerate(fs.GUNPORT_Z):
            y = fs.GUNPORT_Y + band_lift(z, 0.8) * 0.6
            # the open port (gold frame round the dark opening), its red lid raised above it, hinged at the
            # top and leaning out, and the gun's muzzle run out through it
            hull_decal(bone, "gunport_%s%d" % (sn, k), z, y, side, 1.15, 1.1, "gunport_open", out=0.02, th=0.06)
            p, u, v, n = side_frame(z, y + 0.6, side)
            lid_axes = np.column_stack([u, norm(v + n * 1.1), norm(np.cross(u, norm(v + n * 1.1)))])
            if np.dot(lid_axes[:, 2], n) < 0:
                lid_axes[:, 2] = -lid_axes[:, 2]
                lid_axes[:, 0] = -lid_axes[:, 0]
            lc = p + n * 0.06 + lid_axes[:, 1] * 0.5
            add_cube(bone, "gunport_lid_%s%d" % (sn, k), lc, lid_axes, (1.15, 1.0, 0.08), {"all": "gunport_lid", "-3": "wood_dark"},
                     stretch=True, u_dir=u, v_dir=-lid_axes[:, 1])
            add_cube(bone, "gunport_hinge_%s%d" % (sn, k), p + n * 0.05, np.column_stack([u, v, n]), (1.25, 0.1, 0.1), "iron")
            # the muzzle: a dark bronze gun run out half a block, its bore in its end
            m0, m1 = hp(z, y - 0.08, side, -0.3), hp(z, y - 0.08, side, 0.55)
            round_bar(bone, "muzzle_%s%d" % (sn, k), m0, m1, 0.3, "cannon")
            disc(bone, "muzzle_ring_%s%d" % (sn, k), hp(z, y - 0.08, side, 0.48), (side, 0, 0), 0.19, 0.08, "cannon", n=3)
            disc(bone, "bore_%s%d" % (sn, k), hp(z, y - 0.08, side, 0.56), (side, 0, 0), 0.1, 0.02, "bore", n=3)


def f_cannon(bone, name, side, z, base_y, deck_y):
    """A gun on its carriage (galleon helper), run out through the side; inside the hold it stands behind a
    red lid, on the main deck between the balusters."""
    gn.g_cannon(bone, "lit_" + name if deck_y < M else name, side, z, base_y, deck_y, fs.hull_x)


CUSTOM_BUILDERS = dict(gc.CUSTOM_BUILDERS)
CUSTOM_BUILDERS["cannon"] = f_cannon


# ---------------------------------------------------------------- the rooms, on the interior grid
MAX_TILE = 8   # cells (4 blocks): the room regions are 64 px, 16 px a block
WOOD_ROOM = ("wall_wood", "floor", "ceil")
ROOM_MATERIALS = {"cabin": WOOD_ROOM, "hold": ("hold_wall", "hold_floor", "ceil")}


def room_at(x, y, z):
    for name, (x0, x1, y0, y1, z0, z1) in fi.ROOMS.items():
        if x0 - 0.01 <= x <= x1 + 0.01 and y0 - 0.51 <= y <= y1 + 0.01 and z0 - 0.01 <= z <= z1 + 0.01:
            return name
    return None


def surfaces(rooms_bone, g):
    """Walls, floors, ceilings, stairs of the rooms: every face between a solid cell and an open cell
    (dry, door, furniture) is drawn, in the material of the room; the masts are drawn round instead."""
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
                        sub = ((i0 % MAX_TILE) / MAX_TILE, (j0 % MAX_TILE) / MAX_TILE, (i1 % MAX_TILE + 1) / MAX_TILE,
                               (j1 % MAX_TILE + 1) / MAX_TILE)
                    else:
                        hz0, hz1 = (j0, j1) if a == 0 else (i0, i1)
                        y_lo, y_hi = lo[1], hi[1]
                        room = room_at(center[0] + s * 0.3 if a == 0 else center[0], center[1],
                                       center[2] + s * 0.3 if a == 2 else center[2])
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
    """Deck beams under the main deck and the quarterdeck, across the rooms."""
    for name, (x0, x1, y0, y1, z0, z1) in fi.ROOMS.items():
        for k, z in enumerate(np.arange(z0 + 1.0, z1 - 0.4, 2.0)):
            w = min(x1, fs.hull_x(z, y1) - 0.5) - 0.02
            xa = max(x0, -(fs.hull_x(z, y1) - 0.5)) + 0.02
            beam(bone, "lit_beam_%s_%d" % (name, k), (xa, y1 - 0.12, z), (w, y1 - 0.12, z), 0.24, "wood_dark", width=0.3)


def doors(root, g):
    anims = []
    for d, (name, box) in fi.DOORS.items():
        x0, x1, y0, y1, z0, z1 = box
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        along_z = sx < sz           # a door in a wall across x
        thin = 0.14
        depth = (sx if along_z else sz) + 0.1
        w = 0.16
        p0, p1 = (z0, z1) if along_z else (x0, x1)
        for k, at in enumerate((p0 - w / 2, p1 + w / 2)):
            c = v3((x0 + x1) / 2, (y0 + y1 + w) / 2, at) if along_z else v3(at, (y0 + y1 + w) / 2, (z0 + z1) / 2)
            size = (depth, sy + w, w) if along_z else (w, sy + w, depth)
            add_cube(root, "lit_door_%d_jamb_%d" % (d, k), c, EYE, size, "gold")
        c = v3((x0 + x1) / 2, y1 + w / 2, (z0 + z1) / 2)
        add_cube(root, "lit_door_%d_lintel" % d, c, EYE, (depth, w, sz + 2 * w) if along_z else (sx + 2 * w, w, depth), "gold")
        tracks = []
        for leaf, sgn in (("a", 1), ("b", -1)):
            xh = x1 if sgn > 0 else x0
            hinge = v3(xh, y0, (z0 + z1) / 2)
            c = v3(xh - sgn * sx / 4, (y0 + y1) / 2, (z0 + z1) / 2)
            size = (sx / 2 - 0.02, sy, thin)
            bone = Bone("door_%d_%s" % (d, leaf), origin=tuple(hinge), parent=root)
            add_cube(bone, "lit_door_%d_%s" % (d, leaf), c, EYE, size, {"all": "wood_dark", "+3": "door", "-3": "door"},
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
    root = Bone("blue_frigate")
    hull_bone = Bone("hull", parent=root)
    castle_bone = Bone("sterncastle", parent=root)
    deck_bone = Bone("deck", parent=root)
    bow_bone = Bone("bow", parent=root)
    ropes = Bone("ropes", parent=root)
    lights = Bone("lanterns", parent=root)
    detail = Bone("detail", parent=root)
    rooms = Bone("rooms", parent=root)
    fittings = Bone("fittings", parent=root)
    furniture = Bone("furniture", parent=root)
    n = hull(hull_bone)
    stern(hull_bone, castle_bone, lights)
    waist(hull_bone, detail)
    gun_ports(detail)
    decks(deck_bone, castle_bone)
    castle(castle_bone, lights)
    bowsprit = bow(bow_bone, lights)
    masts = {name: mast(root, fittings, name) for name in MASTS}
    sails_info = []
    sails = sails_and_spars(root, masts, sails_info, bowsprit)
    rigging(ropes, hull_bone, masts, bowsprit, sails)
    flags(root, masts)
    helm(castle_bone)
    rudder(root)
    deck_fittings(deck_bone, detail)
    # lanterns: under the jib-boom, on the stern corners (hanging from arms, as on the reference)
    sa, sb, cap = bowsprit
    lantern(lights, "lantern_jibboom", sb + v3(0, 0.15, -0.5), drop=0.45, s=1.1)
    for side, sn in SIDES:
        x = side * (fs.hull_x(TZ, Q + 0.5) - 0.25)
        yt = Q + TAFF_RISE + 1.35
        add_cube(castle_bone, "stern_lantern_post_" + sn, (x, yt + 0.45, TZ + 0.3), EYE, (0.24, 0.9, 0.24), "gold")
        add_cube(castle_bone, "stern_lantern_knob_" + sn, (x, yt + 0.98, TZ + 0.3), EYE, (0.3, 0.16, 0.3), "gold")
        beam(castle_bone, "stern_lantern_arm_" + sn, v3(x, yt + 0.8, TZ + 0.3), v3(x + side * 0.35, yt + 0.8, TZ - 0.55), 0.1, "iron")
        lantern(lights, "lantern_stern_" + sn, v3(x + side * 0.35, yt + 0.75, TZ - 0.55), drop=0.3, s=1.5)
    # the rooms, their door, the beams, the furniture made for the ship
    m = surfaces(rooms, g)
    beams_below(fittings)
    for builder, kwargs, solid in fd.CUSTOM:
        kw = dict(kwargs)
        if builder == "cannon":
            f_cannon(furniture if kw["deck_y"] < M else deck_bone, **kw)
        else:
            CUSTOM_BUILDERS[builder](furniture, **kw)
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
        """Keyframes of a looping animation from 0 to its length included (equal values at both ends: the
        mod's sampler holds the first and last values outside them, so a wrapped phase would jump)."""
        return [rot_kf(round(period * i / n, 4), fn(period * i / n), "catmullrom") for i in range(n + 1)]

    tracks = []
    for k, name in enumerate(("fore", "main", "mizzen")):
        f, ft_ = find(root, "flag_" + name), find(root, "flag_%s_tip" % name)
        w, sh = 2 * math.pi / 1.2, 0.2 * k
        # the wave runs from the hoist to the fly: the fly half lags the root half
        tracks.append((f, loop_kfs(lambda t, sh=sh: (0, 10 * math.cos(w * (t - sh)), 0), 1.2)))
        tracks.append((ft_, loop_kfs(lambda t, sh=sh: (0, -18 * math.cos(w * (t - sh) - 1.75), 0), 1.2)))
    anims.append(animation("flag_wave", 1.2, "loop", tracks))
    tracks = []

    def lanterns_of(b):
        out = []
        if b.name.startswith("lantern_") and b.name != "lanterns":
            out.append(b)
        for c in b.children:
            out += lanterns_of(c)
        return out
    for k, b in enumerate(lanterns_of(root)):
        a, w, ph = 5, 2 * math.pi / 2.4, 0.35 * k
        tracks.append((b, loop_kfs(lambda t, ph=ph: (a * math.cos(w * (t - ph)), 0, a * 0.6 * math.sin(w * (t - ph))), 2.4)))
    anims.append(animation("lantern_sway", 2.4, "loop", tracks))
    # the slack ropes swing slowly about their chord, each with its own phase
    tracks = []
    period = 4.8

    def slack_of(b):
        out = [b] if b.name.startswith("rope_slack_") else []
        for c in b.children:
            out += slack_of(c)
        return out
    for k, b in enumerate(slack_of(root)):
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
    paths = [os.path.join(tex_dir, "entity/blue_frigate.png"), os.path.join(tex_dir, "entity/blue_frigate_sails.png")]
    ft.make_texture(paths[0])
    ft.make_sail_texture(paths[1], {"jib": sails["jib"]})
    ft.make_item_icon(os.path.join(tex_dir, "item/blue_frigate.png"))
    textures = []
    for k, (p, size_) in enumerate(zip(paths, (ft.SIZE, ft.SAIL_SIZE))):
        with open(p, "rb") as f:
            png = f.read()
        t = gn.texture_entry(os.path.basename(p), size_, png, "entity", "blue_frigate.png")
        t["id"] = str(k)
        textures.append(t)
    model = gn.export(root, anims, textures, [
        os.path.join(ROOT, "blockbench/blue_frigate.bbmodel"),
        os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/blue_frigate.bbmodel"),
    ], name="blue_frigate", visible_box=(56, 40, 0))
    print("grid bytes:", size, "hull boards:", n, "grid surfaces:", m, "cubes:", len(model["elements"]),
          "animations:", [a["name"] for a in model["animations"]])


if __name__ == "__main__":
    main()
