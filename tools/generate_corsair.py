#!/usr/bin/env python3
"""Generates the Old Corsair (old_corsair) Blockbench model, its texture, its item icon, its interior
grid and its furniture.

Usage:  python3 tools/generate_corsair.py

Outputs:
  blockbench/old_corsair.bbmodel                                            (editable, texture embedded)
  src/main/resources/assets/medievalships/models/entity/old_corsair.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/old_corsair.png
  src/main/resources/assets/medievalships/textures/item/old_corsair.png
  src/main/resources/assets/medievalships/interiors/old_corsair.grid         (collisions, dry rooms, doors)
  src/main/resources/assets/medievalships/interiors/old_corsair_decor.json   (furniture of the mods, seats)

Reference: the Minecraft sheet of "Le Vieux Corsaire" (side, front, back, top, perspective and detail
views, six interior views; docs/CORSAIR_PLAN.md). An old, patched up brig (two masts, as on the side
and perspective views): a long black hull with two weathered cream bands that rise to the bow, brown
upper works with open balustrades and stout posts, a stern castle with lit windows and galleries, a
bowsprit with its jib-boom and lanterns, red-brown blocky sails with beige patches (course, topsail and
topgallant on the fore mast, lanterns hanging under the fore course; a bare main yard, a topsail, a
topgallant and a great gaff spanker on the main mast; two jibs, a staysail between the masts), rope
ladders up to every top, black pirate flags with a skull at the gaff peak and on the stern. Inside, two decks under the main deck (lower deck and hold) and the captain's
cabin under the quarterdeck; their walls, floors and ceilings are drawn on the boundaries of the
interior grid (tools/corsair_interior.py): what is drawn is what collides.

Bones used by the mod (keep their names when editing in Blockbench):
  sail_* (sail_wind, sail_furl)  helm_wheel, rudder (steer)  flag_*, flag_*_tip (flag_wave)
  lantern_* (lantern_sway)       door_<k> (door k: 0 = closed, 1 = open)   rooms, furniture, fittings, detail
"""
import math
import os
import sys
import uuid

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import generate_galleon as gn  # noqa: E402
import generate_galley as gg  # noqa: E402
import ship_details as sd  # noqa: E402
import corsair_shape as cs  # noqa: E402
import corsair_interior as ci  # noqa: E402
import corsair_texture as ct  # noqa: E402
import corsair_decor as cd  # noqa: E402
import corsair_furniture as cf  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/old_corsair/%d" % _uuid_counter[0]))


gg.new_uuid = new_uuid
gn.new_uuid = new_uuid
gn.REGIONS = {k: (0,) + r for k, r in ct.REGIONS.items()}
gn.SIZE = ct.SIZE

v3, norm, Bone, add_cube, beam, board = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam, gg.board
rx, ry, rz = gg.rx, gg.ry, gg.rz
round_bar, cap_rail, disc, turned, polyline, bezier = gn.round_bar, gn.cap_rail, gn.disc, gn.turned, gn.polyline, gn.bezier
EYE = np.eye(3)
SIDES = ((1, "p"), (-1, "s"))
DECK_AXES = np.column_stack([v3(0, 0, 1), v3(0, 1, 0), v3(-1, 0, 0)])

M, L, H, Q, C = cs.MAIN_DECK_Y, cs.LOWER_FLOOR_Y, cs.HOLD_FLOOR_Y, cs.QUARTERDECK_Y, cs.CABIN_FLOOR_Y
CF = cs.CABIN_FRONT_Z
TZ = cs.TRANSOM_Z
BOW_Z = cs.FORE_SCALE - 0.02   # where the planking closes on the stem
BRACE = math.radians(36)       # square yards braced round (port arms aft): the sails show their faces on the side view


# ---------------------------------------------------------------- hull geometry
def lift(z):
    """Rise of the sheer above its middle height at z."""
    return cs.sheer_y(z) - cs.SHEER_BASE


def band_lift(z, k):
    """Rise of the cream bands: they follow the sheer, and sweep up into the stem at the bow."""
    bow = min(1.0, max(0.0, (z - 13.0) / (BOW_Z - 13.0))) ** 1.7
    return k * lift(z) + (2.3 if k > 0.6 else 1.5) * bow


LOW_BAND = (-0.35, 0.3)     # the cream band at the waterline
HIGH_BAND = (2.0, 2.55)     # the upper cream band, along the lower deck


def hull_rows(z):
    """Points (x, y) of the outer hull section at z (one side, keel to sheer) and the region of each strake."""
    ys = cs.sheer_y(min(z, BOW_Z))
    pts = []
    for fx, fy in ((0.0, 1.0), (0.45, 0.9), (0.8, 0.55), (0.97, 0.12)):
        y = fy * cs.keel_y(min(z, cs.HALF_LENGTH + 0.6))
        zz = z - cs.rake(z, y)
        w, yk = cs.half_width(zz), cs.keel_y(min(zz, cs.HALF_LENGTH + 0.6))
        pts.append((max(0.16, fx * w), fy * yk))
    regs = ["hull_black", "hull_black", "hull_black"]
    lo, hi = band_lift(z, 0.45), band_lift(z, 0.8)
    levels = [(LOW_BAND[0] + lo, "hull_black2"), (LOW_BAND[1] + lo, "stripe"), (1.15 + hi * 0.6, "hull_black"),
              (HIGH_BAND[0] + hi, "hull_black2"), (HIGH_BAND[1] + hi, "stripe"), (3.45 + lift(z) * 0.9, "hull_black"),
              (ys - 0.42, "hull_black2"), (ys, "wood_dark")]
    for y, reg in levels:
        y = min(y, ys - 0.06 * (len(levels) - len(regs)))
        y = max(y, pts[-1][1] + 0.08)
        pts.append((max(0.16, cs.hull_x(z, y)), y))
        regs.append(reg)
    return pts, regs


STATIONS = [TZ, -20.4, -19.6, -18.6, -17.4, -16.0, -14.5, -13.0, -11.5, -10.0, -8.5, -7.0, -5.5, -4.0, -2.5, -1.0, 0.5, 2.0,
            3.5, 5.0, 6.5, 8.0, 9.5, 11.0, 12.4, 13.7, 14.9, 16.0, 17.0, 17.9, 18.7, 19.4, 20.0, 20.5, 20.9, 21.2, 21.42, BOW_Z,
            21.9, 22.3, 22.7, 23.1, 23.5, 23.85, 24.15]


def hp(z, y, side, out=0.0):
    """Point on the outer hull surface (or above the sheer, on the bulwark line), pushed out by `out`."""
    return v3(side * (cs.hull_x(z, y) + out), y, z)


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
    return min(z, BOW_Z + cs.rake(BOW_Z, y))


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
                outward = norm(v3(side * t[1], -side * t[0], 0) + v3(0, 0, 0.6 * max(0.0, mid[2] - 15) / 6))
                board(bone, "hull_%s%d_%d" % (sn, i, k), a0, a1, b0, b1, 0.14, regs[k], outward, overlap=1.03,
                      inner="hull_black" if k < len(A) - 2 else "wood_dark")
                n += 1
    # keel and its shoe, rising into the stem
    for i in range(len(STATIONS) - 2):
        za, zb = STATIONS[i], STATIONS[i + 1]
        if zb > cs.HALF_LENGTH + 0.2:
            break
        beam(bone, "keel_%d" % i, (0, cs.keel_y(za) - 0.08, za), (0, cs.keel_y(zb) - 0.08, zb), 0.3, "dark_wood", width=0.36, extend=0.06)
    return n


def transom_rows():
    """The stern: rows (y, half width, region) from the keel to the quarterdeck rail."""
    z = TZ
    pts, regs = hull_rows(z)
    rows = [(y, x, regs[k] if k < len(regs) else "wood_mid") for k, (x, y) in enumerate(pts)]
    return rows


def stern(bone, castle, lights):
    """Flat transom below the castle (black with the bands), and the stern of the castle above it:
    four lit windows of the captain's cabin behind a stern walk with its balustrade, an upper row of
    small windows, the quarterdeck balustrade with its corner posts and lanterns."""
    z = TZ
    pts, regs = hull_rows(z)
    for k in range(len(pts) - 1):
        (xa, ya), (xb, yb) = pts[k], pts[k + 1]
        for j in range(4):
            fa0, fa1 = -1 + j / 2, -1 + (j + 1) / 2
            board(bone, "transom_%d_%d" % (k, j), v3(fa0 * xa, ya, z), v3(fa0 * xb, yb, z), v3(fa1 * xa, ya, z), v3(fa1 * xb, yb, z),
                  0.16, regs[k], v3(0, 0, -1), overlap=1.02, inner="hull_black")
    # the stern of the castle, from the sheer to the quarterdeck: brown boards, posts, the windows
    ys = cs.sheer_y(z)
    rows = [ys, ys + 0.5, 5.4, 6.4, Q - 0.05, Q + 0.3]
    for k in range(len(rows) - 1):
        ya, yb = rows[k], rows[k + 1]
        xa, xb = cs.hull_x(z, ya), cs.hull_x(z, yb)
        for j in range(4):
            fa0, fa1 = -1 + j / 2, -1 + (j + 1) / 2
            reg = "wood_dark" if k in (0, 4) else "wood_mid"
            board(castle, "stern_wall_%d_%d" % (k, j), v3(fa0 * xa, ya, z), v3(fa0 * xb, yb, z), v3(fa1 * xa, ya, z),
                  v3(fa1 * xb, yb, z), 0.16, reg, v3(0, 0, -1), overlap=1.02, inner="wall_wood")
    # four lit windows of the cabin, with frames, and the stern walk outside them
    for j, x in enumerate((-2.4, -0.8, 0.8, 2.4)):
        add_cube(castle, "glow_stern_window_%d" % j, (x, 5.9, z - 0.1), EYE, (0.9, 0.95, 0.04), "glow_window", stretch=True)
        add_cube(castle, "stern_window_head_%d" % j, (x, 6.45, z - 0.13), EYE, (1.1, 0.14, 0.12), "wood_dark")
        add_cube(castle, "stern_window_sill_%d" % j, (x, 5.38, z - 0.14), EYE, (1.1, 0.12, 0.14), "wood_dark")
        add_cube(castle, "stern_window_in_%d" % j, (x, 5.9, z + 0.1), EYE, (0.9, 0.95, 0.03), {"all": None, "+3": "window_in"},
                 stretch=True)
    for j, x in enumerate((-3.2, -1.6, 0.0, 1.6, 3.2)):
        add_cube(castle, "stern_post_%d" % j, (x, (ys + Q) / 2, z - 0.14), EYE, (0.24, Q - ys, 0.12), "wood_dark")
    # stern walk: a narrow gallery outside the windows, on carved brackets
    bw, bz = 3.6, z - 1.05
    add_cube(castle, "stern_walk_floor", (0, 4.72, (z + bz) / 2), EYE, (2 * bw, 0.16, z - bz), {"all": "wood_dark", "+2": "deck"})
    for j, x in enumerate(np.linspace(-bw + 0.3, bw - 0.3, 6)):
        pts_ = [v3(x, 3.5, z - 0.02), v3(x, 4.0, z - 0.6), v3(x, 4.62, bz + 0.12)]
        for q, (a, b) in enumerate(polyline(pts_)):
            beam(castle, "stern_walk_bracket_%d_%d" % (j, q), a, b, 0.16, "wood_dark", width=0.14, extend=0.05)
    gallery_rail(castle, "stern_walk_rail", [v3(-bw, 4.8, z - 0.05), v3(-bw, 4.8, bz), v3(bw, 4.8, bz), v3(bw, 4.8, z - 0.05)], 0.75,
                 posts_every=0.42)
    # the quarterdeck balustrade on the stern
    xq = cs.hull_x(z, Q + 0.5)
    gallery_rail(castle, "stern_qd_rail", [v3(-xq + 0.2, Q, z + 0.2), v3(xq - 0.2, Q, z + 0.2)], 1.0, posts_every=0.5, big_every=3)


def gallery_rail(bone, name, path, h, posts_every=0.5, big_every=0, region="wood_mid", cap="rail"):
    """Open balustrade along a path: a bottom rail, square balusters, a cap rail; every `big_every`
    balusters a stout post standing above the cap with a block head (the reference's posts)."""
    k = 0
    for i, (a, b) in enumerate(polyline(path)):
        beam(bone, "%s_cap_%d" % (name, i), a + v3(0, h, 0), b + v3(0, h, 0), 0.14, cap, width=0.3, extend=0.07)
        beam(bone, "%s_foot_%d" % (name, i), a + v3(0, 0.09, 0), b + v3(0, 0.09, 0), 0.18, region, width=0.26, extend=0.05)
        seg = np.linalg.norm(b - a)
        n = max(1, int(round(seg / posts_every)))
        for j in range(n + (1 if i == len(path) - 2 else 0)):
            p = a + (b - a) * (j / n)
            if big_every and k % big_every == 0:
                add_cube(bone, "%s_post_%d" % (name, k), p + v3(0, (h + 0.3) / 2, 0), EYE, (0.3, h + 0.3, 0.3), "wood_dark")
                add_cube(bone, "%s_post_cap_%d" % (name, k), p + v3(0, h + 0.38, 0), EYE, (0.4, 0.16, 0.4), "wood_mid")
                add_cube(bone, "%s_post_knob_%d" % (name, k), p + v3(0, h + 0.53, 0), EYE, (0.22, 0.14, 0.22), "wood_dark")
            else:
                add_cube(bone, "%s_baluster_%d" % (name, k), p + v3(0, h / 2 + 0.05, 0), EYE, (0.12, h - 0.1, 0.12), region)
            k += 1


def waist(bone, detail):
    """The waist from the castle to the bow: the brown planksheer, the bulwark (a low solid band and an
    open balustrade on it, stout posts with block heads every few balusters), the bow closing round the
    stem."""
    zs = [z for z in STATIONS if CF - 0.6 <= z <= 23.85]
    for side, sn in SIDES:
        for i in range(len(zs) - 1):
            za, zb = zs[i], zs[i + 1]
            ya, yb = cs.sheer_y(za), cs.sheer_y(zb)
            ra, rb = cs.rail_y(za), cs.rail_y(zb)
            # solid band from the sheer up 0.4, thick (inner face near the collision)
            board(bone, "bulwark_%s%d" % (sn, i), hp(za, ya, side), hp(za, ya + 0.42, side), hp(zb, yb, side), hp(zb, yb + 0.42, side),
                  0.42, "wood_mid", v3(side, 0, 0), overlap=1.03, inner="wood_dark")
            # cap rail at the rail height, a little inboard
            beam(bone, "rail_cap_%s%d" % (sn, i), hp(za, ra, side, -0.18), hp(zb, rb, side, -0.18), 0.14, "rail", width=0.34, extend=0.08)
            # the wale under the sheer (brown, rounded)
            gn.wale_bar(bone, "wale_%s%d" % (sn, i), hp(za, ya - 0.22, side, 0.06), hp(zb, yb - 0.22, side, 0.06), 0.2, 0.16, "wood_dark",
                        extend=0.05)
            # balusters along the segment, and at the bow (forward of 18.5) a closed bulwark instead
            seg = np.linalg.norm(hp(zb, ra, side) - hp(za, ra, side))
            if za >= 18.4:
                board(bone, "bow_bulwark_%s%d" % (sn, i), hp(za, ya + 0.4, side), hp(za, ra, side), hp(zb, yb + 0.4, side), hp(zb, rb, side),
                      0.3, "wood_mid", v3(side, 0, 0), overlap=1.03, inner="wood_dark")
                continue
            nb = max(1, int(round(seg / 0.45)))
            for j in range(nb):
                t = (j + 0.5) / nb
                z = za + (zb - za) * t
                y0, y1 = cs.sheer_y(z) + 0.42, cs.rail_y(z) - 0.07
                p0, p1 = hp(z, y0, side, -0.2), hp(z, y1, side, -0.2)
                add_cube(detail, "baluster_%s%d_%d" % (sn, i, j), (p0 + p1) / 2, EYE, (0.12, y1 - y0, 0.12), "wood_mid")
    # stout posts with block heads along the waist (every ~2.6 blocks), as on the reference
    for side, sn in SIDES:
        for j, z in enumerate(np.arange(CF + 1.4, 18.0, 2.6)):
            r = cs.rail_y(z)
            p = hp(z, r, side, -0.2)
            add_cube(bone, "rail_post_%s%d" % (sn, j), p + v3(0, -0.25, 0), EYE, (0.34, 1.0, 0.34), "wood_dark")
            add_cube(bone, "rail_post_cap_%s%d" % (sn, j), p + v3(0, 0.33, 0), EYE, (0.46, 0.18, 0.46), "wood_mid")
            add_cube(bone, "rail_post_knob_%s%d" % (sn, j), p + v3(0, 0.5, 0), EYE, (0.26, 0.18, 0.26), "wood_dark")
    # the stem head: the two rails meet on a carved knighthead
    zt = 23.9
    add_cube(bone, "knighthead", (0, cs.rail_y(zt) + 0.1, zt), EYE, (0.6, 0.5, 0.6), "wood_dark")


def decks(bone, castle):
    """Main deck planking (fore and aft), with the companion hatch left open; the quarterdeck."""
    zs = list(np.arange(CF - 0.5, 23.0, 1.0)) + [23.0]
    cx0, cx1 = cs.COMPANION_X
    cz0, cz1 = cs.COMPANION_Z
    for j in range(len(zs) - 1):
        za, zb = zs[j], zs[j + 1]
        w = min(cs.hull_x(za, M), cs.hull_x(zb, M)) - 0.12
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
        w = min(cs.hull_x(za, Q), cs.hull_x(zb, Q)) - 0.1
        add_cube(castle, "qdeck_%d" % j, (0, Q - 0.08, (za + zb) / 2), DECK_AXES, (zb - za + 0.01, 0.16, 2 * w), {"all": "deck", "-2": "ceil"})


def castle(bone, lights):
    """The stern castle sides (from the sheer to the quarterdeck): brown boards between dark posts,
    three lit windows of the captain's cabin behind a low gallery balustrade on a ledge, a heavy wale
    at the quarterdeck, the quarterdeck balustrade with stout posts; the front bulkhead with the cabin
    door, its windows and the guard rail between the two stairs."""
    zs = [z for z in STATIONS if TZ <= z <= CF] + [CF]
    zs = sorted(set(round(z, 3) for z in zs))
    for side, sn in SIDES:
        for i in range(len(zs) - 1):
            za, zb = zs[i], zs[i + 1]
            ya, yb = cs.sheer_y(za), cs.sheer_y(zb)
            for r, (fa, fb, reg) in enumerate(((0.0, 0.45, "wood_dark"), (0.45, 1.0, "wood_mid"))):
                y0a, y1a = ya + (Q + 0.3 - ya) * fa, ya + (Q + 0.3 - ya) * fb
                y0b, y1b = yb + (Q + 0.3 - yb) * fa, yb + (Q + 0.3 - yb) * fb
                board(bone, "castle_wall_%s%d_%d" % (sn, i, r), hp(za, y0a, side), hp(za, y1a, side), hp(zb, y0b, side), hp(zb, y1b, side),
                      0.16, reg, v3(side, 0, 0), overlap=1.03, inner="wall_wood")
            gn.wale_bar(bone, "castle_wale_%s%d" % (sn, i), hp(za, Q - 0.05, side, 0.06), hp(zb, Q - 0.05, side, 0.06), 0.24, 0.18,
                        "wood_dark", extend=0.05)
            gn.wale_bar(bone, "castle_wale_low_%s%d" % (sn, i), hp(za, ya - 0.22, side, 0.06), hp(zb, yb - 0.22, side, 0.06), 0.2, 0.16,
                        "wood_dark", extend=0.05)
        # posts between the windows
        for j, z in enumerate((TZ + 0.25, -19.1, -17.3, -15.5, CF + 0.1)):
            y0 = cs.sheer_y(z)
            p0, p1 = hp(z, y0, side, 0.05), hp(z, Q, side, 0.05)
            add_cube(bone, "castle_post_%s%d" % (sn, j), (p0 + p1) / 2, EYE, (0.26, Q - y0, 0.26), "wood_dark")
        # lit windows of the cabin
        for j, z in enumerate((-20.0, -18.2, -16.4)):
            hull_decal(bone, "castle_window_%s%d" % (sn, j), z, 5.85, side, 0.95, 0.9, "glow_window", out=0.02, glow=True)
            hull_decal(bone, "castle_window_head_%s%d" % (sn, j), z, 6.38, side, 1.15, 0.14, "wood_dark", out=0.03, th=0.1, stretch=False)
            p, u, v, n = side_frame(z, 5.85, side)
            add_cube(bone, "castle_window_in_%s%d" % (sn, j), p - n * 0.2, np.column_stack([u, v, n]), (0.95, 0.9, 0.03),
                     {"all": None, "-3": "window_in"}, stretch=True)
        # the low gallery: a ledge on brackets and a balustrade in front of the windows
        ledge = []
        for z in np.linspace(TZ + 0.15, CF - 0.3, 7):
            ledge.append(hp(z, 5.0, side, 0.42))
        for i, (a, b) in enumerate(polyline(ledge)):
            beam(bone, "gallery_ledge_%s%d" % (sn, i), a - v3(side * 0.12, 0.05, 0), b - v3(side * 0.12, 0.05, 0), 0.12, "wood_dark", width=0.5,
                 extend=0.04)
        for j, z in enumerate(np.linspace(TZ + 0.6, CF - 0.6, 4)):
            p = hp(z, 5.0, side, 0.3)
            beam(bone, "gallery_bracket_%s%d" % (sn, j), hp(z, 4.25, side, 0.02), p - v3(0, 0.08, 0), 0.14, "wood_dark", width=0.12)
        gallery_rail(bone, "gallery_rail_" + sn, [v3(q[0], q[1], q[2]) for q in ledge], 0.62, posts_every=0.4, big_every=4)
        # quarterdeck balustrade
        path = [hp(z, Q, side, -0.22) for z in np.linspace(TZ + 0.2, CF - 0.05, 6)]
        gallery_rail(bone, "qd_rail_" + sn, path, 1.0, posts_every=0.5, big_every=3)
    # front bulkhead (main deck -> quarterdeck), cabin door frame, two small windows
    bz = CF - 0.08
    wq = cs.hull_x(CF, M) - 0.2
    for side, sn in SIDES:
        x0, x1 = 1.0, wq
        add_cube(bone, "bulkhead_" + sn, (side * (x0 + x1) / 2, (M + Q) / 2, bz), EYE, (x1 - x0, Q - M, 0.16),
                 {"all": "wood_mid", "-3": "wall_wood"})
        add_cube(bone, "bulkhead_jamb_" + sn, (side * 1.1, (M + Q - 0.5) / 2, CF + 0.04), EYE, (0.2, Q - 0.5 - M + 0.2, 0.14), "wood_dark")
        add_cube(bone, "glow_bulkhead_window_" + sn, (side * 2.6, 5.75, CF + 0.02), EYE, (0.7, 0.6, 0.04), "glow_window", stretch=True)
        add_cube(bone, "bulkhead_window_frame_" + sn, (side * 2.6, 6.12, CF + 0.04), EYE, (0.9, 0.12, 0.1), "wood_dark")
    add_cube(bone, "bulkhead_lintel", (0, Q - 0.4, CF + 0.04), EYE, (2.4, 0.3, 0.16), "wood_dark")
    # guard rail along the front of the quarterdeck, between the stairs
    x0 = cs.QD_STAIR_X[0] - 0.05
    gallery_rail(bone, "qd_front_rail", [v3(-x0, Q, CF - 0.22), v3(x0, Q, CF - 0.22)], 0.95, posts_every=0.45, big_every=4)
    # stairs to the quarterdeck (as the grid: 5 steps of 0.5), with a hand rail on their inner side
    n = int(round((Q - M) / 0.5))
    for side, sn in SIDES:
        xa, xb = cs.QD_STAIR_X
        for k in range(1, n + 1):
            za = cs.QD_STAIR_Z[0] - k * 0.5
            top = M + k * 0.5
            add_cube(bone, "qd_step_%s%d" % (sn, k), (side * (xa + xb) / 2, (M + top) / 2, za + 0.25), EYE, (xb - xa, top - M, 0.5),
                     {"all": "wood_dark", "+2": "deck"})
        round_bar(bone, "qd_handrail_" + sn, (side * xa, M + 1.0, cs.QD_STAIR_Z[0] + 0.2), (side * xa, Q + 1.0, CF), 0.1, "rail")
        for k, t in enumerate((0.05, 0.5, 0.95)):
            z = cs.QD_STAIR_Z[0] + 0.2 + (CF - cs.QD_STAIR_Z[0] - 0.2) * t
            yb = M + (Q - M) * t
            add_cube(bone, "qd_handrail_post_%s%d" % (sn, k), (side * xa, yb + 0.5, z), EYE, (0.12, 1.0, 0.12), "wood_dark")


def quarter_galleries(bone, lights):
    """Closed galleries on the stern corners (the castle is wider than the hull on the back view):
    a bay with lit windows from the gallery ledge to the quarterdeck, a carved corbel under it, a sloping
    roof, lanterns on their corners."""
    qz0, qz1, D, ng = TZ + 0.05, -16.4, 0.8, 6
    ts = np.linspace(0, 1, ng + 1)

    def gp(t, y, d):
        z = qz0 + (qz1 - qz0) * t
        return hp(z, y, side, d * math.sin(math.pi * (0.5 + 0.5 * t)) ** 0.5 if t < 0.999 else 0.0)

    for side, sn in SIDES:
        def ring(tag, y0, d0, y1, d1, reg, th=0.12):
            for i in range(ng):
                a0, a1, b0, b1 = gp(ts[i], y0, d0), gp(ts[i], y1, d1), gp(ts[i + 1], y0, d0), gp(ts[i + 1], y1, d1)
                board(bone, "%s_%s%d" % (tag, sn, i), a0, a1, b0, b1, th, reg, v3(side, 0.3 if y1 > y0 and d1 < d0 else 0, 0), overlap=1.04)
        ring("qgallery_wall", 5.0, D, 6.7, D, "wood_mid")
        ring("qgallery_sill", 4.85, D + 0.08, 5.1, D + 0.08, "wood_dark")
        ring("qgallery_cornice", 6.7, D + 0.12, 6.95, D + 0.12, "wood_dark")
        ring("qgallery_roof", 6.95, D + 0.12, 7.35, 0.05, "wood_dark", th=0.08)
        ring("qgallery_corbel", 4.85, D, 4.0, 0.1, "wood_dark", th=0.08)
        for i in range(1, ng - 1):
            a, b = gp(ts[i], 5.85, D), gp(ts[i + 1], 5.85, D)
            u = norm(b - a)
            n_ = norm(np.cross(u, v3(0, 1, 0)))
            if np.dot(n_, v3(side, 0, 0)) < 0:
                u, n_ = -u, -n_
            add_cube(bone, "glow_qgallery_window_%s%d" % (sn, i), (a + b) / 2 + n_ * 0.02, np.column_stack([u, v3(0, 1, 0), n_]),
                     (np.linalg.norm(b - a) * 0.75, 0.95, 0.04), "glow_window", stretch=True)
        for i in range(1, ng):
            p = gp(ts[i], 5.85, D + 0.06)
            add_cube(bone, "qgallery_post_%s%d" % (sn, i), p, EYE, (0.16, 1.8, 0.16), "wood_dark")
        lantern(lights, "lantern_qgallery_" + sn, gp(0.5, 4.0, 0.9) + v3(0, -0.05, 0), drop=0.25, s=0.9)


def upper_balcony(bone, lights):
    """The stern balcony at the quarterdeck: a floor on brackets beyond the transom, its balustrade, a
    lantern on each corner post (upper gallery of the back view)."""
    bw, bz = 3.4, TZ - 0.9
    add_cube(bone, "upper_balcony_floor", (0, Q - 0.12, (TZ + bz) / 2), EYE, (2 * bw, 0.2, TZ - bz), {"all": "wood_dark", "+2": "deck"})
    for j, x in enumerate(np.linspace(-bw + 0.3, bw - 0.3, 5)):
        beam(bone, "upper_balcony_bracket_%d" % j, v3(x, Q - 1.0, TZ - 0.02), v3(x, Q - 0.2, bz + 0.15), 0.16, "wood_dark", width=0.14)
    gallery_rail(bone, "upper_balcony_rail", [v3(-bw, Q, TZ - 0.05), v3(-bw, Q, bz), v3(bw, Q, bz), v3(bw, Q, TZ - 0.05)], 0.9,
                 posts_every=0.45, big_every=5)
    for side, sn in SIDES:
        add_cube(bone, "upper_balcony_corner_" + sn, (side * bw, Q + 0.7, bz), EYE, (0.3, 1.4, 0.3), "wood_dark")
        lantern(lights, "lantern_balcony_" + sn, v3(side * bw, Q + 1.4, bz), hang=False, s=1.2)


def bow(bone, lights):
    """Stem, cutwater and a short beak, the catheads with their anchors, the bowsprit (a heavy spar
    rising from the bow) with its cap and the lighter jib-boom, the bow lantern on the stem head."""
    # stem post following the closing bow, from the forefoot to the head
    pts = []
    for j in range(9):
        t = j / 8
        y = cs.keel_y(cs.HALF_LENGTH) - 0.1 + (cs.rail_y(cs.HALF_LENGTH) + 0.3 - cs.keel_y(cs.HALF_LENGTH) + 0.1) * t
        z = BOW_Z + cs.rake(BOW_Z, y) + 0.05 - 0.6 * (1 - t) ** 2.2
        pts.append(v3(0, y, z))
    for j, (a, b) in enumerate(polyline(pts)):
        beam(bone, "stem_%d" % j, a, b, 0.42, "wood_dark", width=0.4, extend=0.08)
    sa, sb = v3(*cs.BOWSPRIT_FOOT), v3(*cs.BOWSPRIT_TIP)
    d = norm(sb - sa)
    cap = sa + d * 8.3
    round_bar(bone, "bowsprit", sa - d * 1.2, cap + d * 0.3, 0.56, "mast")
    for k, t in enumerate((1.5, 3.4, 5.4)):
        round_bar(bone, "bowsprit_band_%d" % k, sa + d * (t - 0.08), sa + d * (t + 0.08), 0.62, "iron")
    add_cube(bone, "bowsprit_cap", cap + d * 0.15 + v3(0, 0.18, 0), gg.frame_from(d, v3(0, 1, 0)), (0.36, 0.8, 0.5), "wood_dark")
    round_bar(bone, "jib_boom", cap - d * 1.6 + v3(0, 0.36, 0), sb + v3(0, 0.36, 0), 0.32, "mast")
    beam(bone, "dolphin_striker", cap + v3(0, -0.1, 0), cap + v3(0, -1.6, 0.15), 0.12, "wood_dark")
    for side, sn in SIDES:
        # cathead and anchor
        z = 18.2
        y = cs.rail_y(z) - 0.1
        base = hp(z, y, side, -0.3)
        tip = hp(z + 0.6, y + 0.15, side, 0.9)
        beam(bone, "cathead_" + sn, base, tip, 0.3, "wood_dark", width=0.3)
        disc(bone, "cathead_sheave_" + sn, tip + v3(0, -0.02, 0), v3(0, 0, 1), 0.1, 0.32, "iron")
        x = side * (cs.hull_x(z + 0.6, 3.0) + 0.25)
        gn.g_anchor(bone, "anchor_" + sn, (x, y - 0.25, z + 0.55), (x, 2.1, z + 0.35), (0, 0, 1))
        disc(bone, "hawse_" + sn, side_frame(19.3, 4.0, side)[0] + v3(side * 0.03, 0, 0), (side, 0, 0), 0.16, 0.06, "iron")
    # the bow lantern on the stem head (front view)
    lantern(lights, "lantern_bow", v3(0, cs.rail_y(cs.HALF_LENGTH) + 0.35, BOW_Z + cs.rake(BOW_Z, 7.5) + 0.25), hang=False, s=1.25)
    return sa, sb, cap


def lantern(parent, name, p, hang=True, drop=0.35, s=1.0):
    """A lantern (rebuilt by lanterns.convert): hanging from a hook (own bone "lantern_*" swaying), or
    standing on a post."""
    p = v3(*p)
    if hang:
        b = Bone(name, origin=tuple(p), parent=parent)
        add_cube(b, name + "_chain", p - v3(0, drop / 2, 0), EYE, (0.04, drop, 0.04), "iron")
        c = p - v3(0, drop + 0.22 * s, 0)
    else:
        b = parent
        c = p + v3(0, 0.22 * s, 0)
    add_cube(b, name + "_body", c, EYE, (0.3 * s, 0.44 * s, 0.3 * s), {"all": "lantern", "+2": "iron", "-2": "iron"}, stretch=True)
    return b


# ---------------------------------------------------------------- masts, yards, sails
# A brig, as on the side and perspective views of the reference (docs/CORSAIR_PLAN.md): the fore mast
# carries a course (with its lanterns), a topsail and a topgallant; the main mast, a little taller, a
# bare main yard (the course furled on it), a topsail, a topgallant and the great gaff spanker whose
# boom reaches the stern. Heights measured on the side view: y = 5.6 + (497 - y_px) / 15.5.
MASTS = {
    # name: (z, lower top y, topmast crosstrees y, masthead y, lower mast diameter)
    "fore": (cs.FORE_MAST_Z, 18.3, 27.3, cs.FORE_MAST_TOP, 0.92),
    "main": (cs.MAIN_MAST_Z, 20.2, 28.8, cs.MAIN_MAST_TOP, 0.96),
}
# where each mast is stepped: on the keel (through the rooms) or on the main deck (tools/corsair_interior.py)
MAST_FOOT = {name: next(foot for z, foot in ci.MASTS if abs(z - MASTS[name][0]) < 1e-6) for name in MASTS}
# square sails: mast, name, yard y, foot y, half width at the head, at the foot, belly, texture region
SQUARE_SAILS = [
    ("fore", "fore_course", 17.3, 8.4, 7.9, 8.5, 1.3, "course"),
    ("fore", "fore_topsail", 25.4, 18.9, 6.1, 7.1, 1.05, "topsail"),
    ("fore", "fore_topgallant", 33.0, 27.9, 4.6, 5.6, 0.85, "topgallant"),
    ("main", "main_topsail", 27.3, 20.8, 5.7, 6.5, 1.05, "main_topsail"),
    ("main", "main_topgallant", 33.1, 28.9, 4.1, 4.9, 0.8, "main_topgallant"),
]


def yard_step(mast_name, name):
    """(z of the mast that carries the yard, offset of the yard before it): the courses and the main yard
    on the lower mast, the topsails on the topmast (stepped 0.45 before it), the topgallants on the
    topgallant mast (0.75 before); the yard hangs just before its mast."""
    z, d = MASTS[mast_name][0], MASTS[mast_name][4]
    if "topsail" in name:
        return z + 0.45, d * 0.66 / 2 + 0.17
    if "topgallant" in name:
        return z + 0.75, d * 0.66 * 0.62 / 2 + 0.17
    return z, d / 2 + 0.17
MAIN_YARD = (18.9, 8.2)          # the bare main yard (y, half span): its course is furled on it
GAFF = (v3(0, 19.7, cs.MAIN_MAST_Z - 0.4), v3(0, 26.2, -16.5))    # throat, peak
BOOM = (v3(0, 9.8, cs.MAIN_MAST_Z - 0.4), v3(0, 10.2, -22.5))     # gooseneck, end (beyond the stern balcony)


def mast(root, fittings, name):
    z, top1, top2, head, d = MASTS[name]
    foot = H if MAST_FOOT[name] < M else M
    mb = Bone("mast_" + name, origin=(0, M, z), parent=root)
    # below the main deck the mast is drawn with the rooms (lit by their lamps)
    if foot < M:
        round_bar(fittings, "lit_mast_%s_below" % name, (0, foot - 0.4, z), (0, M, z), d + 0.05, "mast")
        for y in (L + 0.15, H + 0.15):
            disc(fittings, "lit_mast_%s_collar_%d" % (name, int(y * 10)), (0, y, z), (0, 1, 0), d / 2 + 0.16, 0.3, "wood_dark", n=3)
    round_bar(mb, name + "_lower", (0, M - 0.1, z), (0, top1 + 0.9, z), d, "mast")
    disc(mb, name + "_partners", (0, M + 0.12, z), (0, 1, 0), d / 2 + 0.22, 0.24, "wood_dark", n=3)
    # iron bands (grey on the reference) and rope wooldings
    for k, y in enumerate(np.arange(M + 1.6, top1 - 0.6, 1.7)):
        round_bar(mb, "%s_band_%d" % (name, k), (0, y - 0.09, z), (0, y + 0.09, z), d + 0.08, "iron")
    # the top: a square platform on trestle trees (blocky, as in the reference), with a low rim
    s = 1.25 + d * 0.4
    add_cube(mb, name + "_top", (0, top1 + 0.06, z - 0.15), EYE, (2 * s, 0.14, 2 * s * 0.8), {"all": "wood_dark", "+2": "deck"})
    for sx in (1, -1):
        beam(mb, "%s_trestle_%d" % (name, sx > 0), (sx * d * 0.45, top1 - 0.12, z - s), (sx * d * 0.45, top1 - 0.12, z + s * 0.7), 0.2,
             "wood_dark", width=0.16)
        beam(mb, "%s_crosstree_%d" % (name, sx > 0), (-s, top1 - 0.06, z + sx * 0.5), (s, top1 - 0.06, z + sx * 0.5), 0.14, "wood_dark",
             width=0.14)
    for k, (a, b) in enumerate(polyline([v3(-s, 0, z - 0.15 - s * 0.8), v3(s, 0, z - 0.15 - s * 0.8), v3(s, 0, z - 0.15 + s * 0.8),
                                         v3(-s, 0, z - 0.15 + s * 0.8)], closed=True)):
        beam(mb, "%s_top_rim_%d" % (name, k), a + v3(0, top1 + 0.3, 0), b + v3(0, top1 + 0.3, 0), 0.32, "wood_mid", width=0.1,
             extend=0.05)
    add_cube(mb, name + "_cap", (0, top1 + 0.95, z + 0.2), EYE, (d + 0.2, 0.3, 1.4), "wood_dark")
    if top2 is not None:
        d2 = d * 0.66
        round_bar(mb, name + "_topmast", (0, top1 - 0.5, z + 0.45), (0, top2 + 0.8, z + 0.45), d2, "mast")
        for k, y in enumerate((top1 + 2.5, top1 + 5.0)):
            round_bar(mb, "%s_topmast_band_%d" % (name, k), (0, y - 0.07, z + 0.45), (0, y + 0.07, z + 0.45), d2 + 0.06, "iron")
        s2 = 0.95
        for sx in (1, -1):
            beam(mb, "%s_crosstree2_%d" % (name, sx > 0), (-s2, top2, z + 0.45 + sx * 0.3), (s2, top2, z + 0.45 + sx * 0.3), 0.12,
                 "wood_dark", width=0.12)
        add_cube(mb, name + "_cap2", (0, top2 + 0.85, z + 0.6), EYE, (d2 + 0.16, 0.24, 1.0), "wood_dark")
        round_bar(mb, name + "_topgallant_mast", (0, top2 - 0.4, z + 0.75), (0, head, z + 0.75), d2 * 0.62, "mast")
        disc(mb, name + "_truck", (0, head + 0.05, z + 0.75), (0, 1, 0), 0.2, 0.14, "wood_dark", n=3)
        mz = z + 0.75
    else:
        round_bar(mb, name + "_topmast", (0, top1 - 0.5, z + 0.4), (0, head, z + 0.4), d * 0.62, "mast")
        disc(mb, name + "_truck", (0, head + 0.05, z + 0.4), (0, 1, 0), 0.18, 0.14, "wood_dark", n=3)
        mz = z + 0.4
    return mb, mz


def patch_sail(bone, name, P, N, region, nx, ny, th=0.035, overlap=0.03, keep=None):
    """Sail on a curved patch P(s, t) (s across, t from the head down, both 0..1): cells fitted to their
    four corners (as generate_galleon.g_sail), each mapping its own part of the texture region."""
    N = norm(N)
    for i in range(nx):
        for j in range(ny):
            s0, s1, t0, t1 = i / nx, (i + 1) / nx, j / ny, (j + 1) / ny
            if keep is not None and not keep(s0, t0, s1, t1):
                continue
            a0, a1, b0, b1 = P(s0, t1), P(s0, t0), P(s1, t1), P(s1, t0)
            c = (a0 + a1 + b0 + b1) / 4
            u = ((b0 + b1) - (a0 + a1)) / 2
            Lu = np.linalg.norm(u)
            vp = ((a0 - a1) + (b0 - b1)) / 2
            Hv = np.linalg.norm(vp)
            if Lu < 1e-4 or Hv < 1e-4:
                continue
            n = norm(np.cross(b1 - a0, a1 - b0))
            if np.dot(n, N) < 0:
                n = -n
            u = norm(u - np.dot(u, n) * n)
            v = np.cross(n, u)
            if np.dot(v, vp) < 0:
                v = -v
                u = -u
            v = np.cross(n, u)
            axes = np.column_stack([u, v, n])
            if np.linalg.det(axes) < 0:
                axes[:, 1] = -axes[:, 1]
            # the hint directions of the texture: s along U0, t along V0
            U0 = (P(1, (t0 + t1) / 2) - P(0, (t0 + t1) / 2))
            V0 = (P((s0 + s1) / 2, 1) - P((s0 + s1) / 2, 0))
            cube = add_cube(bone, "%s_%d_%d" % (name, i, j), c, axes, (Lu + overlap, Hv + overlap, th),
                            {"all": None, "+3": region, "-3": region}, stretch=True, u_dir=U0, v_dir=V0)
            gn.set_sub(cube, (s0, t0, s1, t1))


def square_sail(mb, sails_info, lights, name, z, y_top, y_foot, half_top, half_foot, belly, region, foot_yard=False, off=0.42):
    """Yard (braced round with its sail), the sail billowed forward, a lower yard on the courses (the
    blocky reference shows a spar along the foot)."""
    br = Bone("brace_" + name, origin=(0, y_top, z), parent=mb)
    zz = z + off
    round_bar(br, name + "_yard", (-half_top - 0.5, y_top, zz), (half_top + 0.5, y_top, zz), 0.26, "mast", extend=0.05)
    add_cube(br, name + "_sling", (0, y_top, zz - 0.1), EYE, (0.42, 0.38, 0.38), "rope")
    for sx in (1, -1):
        add_cube(br, "%s_yardarm_%d" % (name, sx > 0), (sx * (half_top + 0.35), y_top, zz), EYE, (0.12, 0.34, 0.34), "iron")
    beam(br, name + "_roll", (-half_top * 0.94, y_top - 0.22, zz + 0.05), (half_top * 0.94, y_top - 0.22, zz + 0.05), 0.26, "cloth_roll")
    sb = Bone("sail_" + name, origin=(0, y_top, zz), parent=br)
    height = y_top - y_foot
    cols, rows = ct.SAIL_CELLS[region]
    origin = v3(0, y_top - 0.14, zz + 0.05)

    def P(s, t):
        half = half_top + (half_foot - half_top) * t
        x = (2 * s - 1) * half
        bel = belly * math.sin(math.pi * min(1.0, t * 0.78)) * (0.35 + 0.65 * (1 - (2 * s - 1) ** 2))
        drop = t * height * (1 - 0.05 * t * t * (1 - (2 * s - 1) ** 2))
        return origin + v3(x, -drop, bel)
    patch_sail(sb, name, P, v3(0, 0, 1), region, cols, rows)
    sails_info.append((sb, False))
    if foot_yard:
        fy = y_foot - 0.15
        round_bar(br, name + "_foot_yard", (-half_foot - 0.3, fy, zz + 0.25), (half_foot + 0.3, fy, zz + 0.25), 0.22, "mast")
        for k, x in enumerate((-half_foot - 0.1, -half_foot * 0.68, half_foot * 0.68, half_foot + 0.1)):
            lantern(br, "lantern_%s_%d" % (name, k), (x, fy - 0.1, zz + 0.25), drop=0.45, s=1.6)
    br.rot = ry(BRACE)
    return br


def quad_sail(bone, name, throat, peak, tack, clew, belly, N, region):
    """Fore-and-aft four sided sail (spanker): head along the gaff, luff on the mast, foot on the boom."""
    cols, rows = ct.SAIL_CELLS[region]

    def P(s, t):
        top = throat + (peak - throat) * s
        bot = tack + (clew - tack) * s
        p = top + (bot - top) * t
        return p + N * belly * math.sin(math.pi * s) ** 0.8 * math.sin(math.pi * min(1.0, t * 0.9 + 0.05))
    patch_sail(bone, name, P, N, region, cols, rows)


def tri_sail(bone, name, head, tack, clew, belly, N, region, keep_clew=False):
    """Triangular sail; the jibs share one triangle of their texture region (the clew is slid along the
    luff, gn.jib_clew), keep_clew keeps the given clew (the staysail has its own region and triangle)."""
    if not keep_clew:
        clew = gn.jib_clew(head, tack, clew)
    cols, rows = ct.SAIL_CELLS[region]
    return gn.g_tri_sail(bone, name, head, tack, clew, belly, N, region, cols, rows, round_=0.45), clew


def bare_yard(mb, name, z, off, y, half):
    """The main yard without its course (as on the reference): the course is furled on top of it, tied
    with gaskets; braced round like the other yards."""
    br = Bone("brace_" + name, origin=(0, y, z), parent=mb)
    zz = z + off
    round_bar(br, name + "_yard", (-half - 0.5, y, zz), (half + 0.5, y, zz), 0.3, "mast", extend=0.05)
    add_cube(br, name + "_sling", (0, y, zz - 0.1), EYE, (0.44, 0.4, 0.4), "rope")
    for sx in (1, -1):
        add_cube(br, "%s_yardarm_%d" % (name, sx > 0), (sx * (half + 0.35), y, zz), EYE, (0.12, 0.38, 0.38), "iron")
    round_bar(br, name + "_furled", (-half * 0.93, y + 0.27, zz + 0.04), (half * 0.93, y + 0.27, zz + 0.04), 0.36, "cloth_roll")
    for k, x in enumerate(np.linspace(-half * 0.8, half * 0.8, 7)):
        round_bar(br, "%s_gasket_%d" % (name, k), (x - 0.06, y + 0.25, zz + 0.04), (x + 0.06, y + 0.25, zz + 0.04), 0.44, "rope")
    br.rot = ry(BRACE)
    return br


def stays(bowsprit):
    """Ends of the stays (name -> (upper end, lower end)): the fore stays to the bowsprit, the cap and
    the jib-boom end (the jibs are set on the topmast and topgallant stays), the main stays forward to
    the fore mast; the main staysail's stay comes down steeply to the deck between the masts (as on
    the side view)."""
    sa, sb, cap = bowsprit
    d = norm(sb - sa)
    F, N_ = MASTS["fore"], MASTS["main"]
    fz, mz = F[0], N_[0]
    return {
        "fore_stay": (v3(0, F[1] - 0.25, fz + 0.3), sa + d * 3.4 + v3(0, 0.25, 0)),
        "fore_topmast_stay": (v3(0, F[2] - 0.2, fz + 0.6), cap + v3(0, 0.3, 0)),
        "fore_tg_stay": (v3(0, F[3] - 1.3, fz + 0.9), sb + v3(0, 0.3, 0)),
        "main_stay": (v3(0, N_[1] - 0.2, mz + 0.45), v3(0, M + 0.25, -1.9)),
        "main_topmast_stay": (v3(0, N_[2] - 0.2, mz + 0.6), v3(0, F[1] + 0.45, fz - 0.35)),
        "main_tg_stay": (v3(0, N_[3] - 1.3, mz + 0.9), v3(0, F[2] + 0.25, fz + 0.3)),
    }


def on(stay, t):
    a, b = stay
    return a + (b - a) * t


def sails_and_spars(root, lights, masts, sails_info, bowsprit):
    sa, sb, cap = bowsprit
    for mast_name, name, yt, yf, ht, hf, bel, reg in SQUARE_SAILS:
        mb, mz = masts[mast_name]
        z, off = yard_step(mast_name, name)
        square_sail(mb, sails_info, lights, name, z, yt, yf, ht, hf, bel, reg, foot_yard=(name == "fore_course"), off=off)
    mmb = masts["main"][0]
    bare_yard(mmb, "main_yard", *yard_step("main", "main_yard"), *MAIN_YARD)
    # main gaff and boom with the great spanker (its peak high, its clew over the stern)
    round_bar(mmb, "gaff", GAFF[0], GAFF[1] + norm(GAFF[1] - GAFF[0]) * 0.3, 0.26, "mast")
    round_bar(mmb, "boom", BOOM[0], BOOM[1] + norm(BOOM[1] - BOOM[0]) * 0.2, 0.32, "mast")
    for k, p in enumerate((GAFF[0], BOOM[0])):
        add_cube(mmb, "gaff_jaws_%d" % k, p + v3(0, 0, 0.12), EYE, (0.5, 0.3, 0.3), "wood_dark")
    for k, t in enumerate(np.linspace(0.12, 0.92, 7)):
        p = GAFF[0] + (GAFF[1] - GAFF[0]) * t
        add_cube(mmb, "gaff_lacing_%d" % k, p - v3(0, 0.12, 0), gg.frame_from(norm(GAFF[1] - GAFF[0]), v3(0, 1, 0)), (0.12, 0.3, 0.3), "rope")
    sp = Bone("sail_spanker", origin=tuple(GAFF[0]), parent=mmb)
    quad_sail(sp, "spanker", GAFF[0] + v3(0, -0.15, -0.15), GAFF[1] + v3(0, -0.15, 0.2), BOOM[0] + v3(0, 0.15, -0.15),
              BOOM[1] + v3(0, 0.15, 2.8), 1.0, v3(-1, 0, 0), "spanker")
    sails_info.append((sp, True))
    # two jibs on the fore topmast and topgallant stays, flying high over the bowsprit (side view)
    st_ = stays(bowsprit)
    jb = Bone("sail_jibs", origin=tuple(cap), parent=root)
    jib_tri, outer_clew = tri_sail(jb, "jib_outer", on(st_["fore_tg_stay"], 0.27), on(st_["fore_tg_stay"], 0.88),
                                   v3(0, 13.4, 19.6), 0.9, v3(-1, 0, 0), "jib")
    _, inner_clew = tri_sail(jb, "jib_inner", on(st_["fore_topmast_stay"], 0.25), on(st_["fore_topmast_stay"], 0.86),
                             v3(0, 10.8, 16.8), 0.8, v3(-1, 0, 0), "jib")
    sails_info.append((jb, True))
    # the main staysail: a narrow triangle on the main stay, close to the main mast
    ms = st_["main_stay"]
    st = Bone("sail_staysail", origin=tuple(on(ms, 0.12)), parent=root)
    stay_tri, _ = tri_sail(st, "main_staysail", on(ms, 0.14), on(ms, 0.8), v3(0, 8.3, cs.MAIN_MAST_Z + 1.15), 0.6, v3(-1, 0, 0),
                           "staysail", keep_clew=True)
    sails_info.append((st, True))
    return {"jib": jib_tri, "staysail": stay_tri, "jib_clews": (outer_clew, inner_clew)}


# ---------------------------------------------------------------- rigging
def channel_point(z, side, out=0.48, dy=-0.3):
    y = cs.rail_y(z) + dy
    return hp(z, y, side, out)


def ladder(bone, name, tops, feet, step=0.45, region="rope_light", th=0.08):
    """Shrouds from their feet up to a common top, with ratlines across them (the rope ladders of the
    reference): tops/feet are the ends of each shroud."""
    for k, (a, b) in enumerate(zip(tops, feet)):
        beam(bone, "%s_shroud_%d" % (name, k), a, b, th + 0.015, region)
    h = min(a[1] for a in tops) - max(b[1] for b in feet)
    n = int(h / step)
    for j in range(1, n):
        t = j / n
        pa = feet[0] + (tops[0] - feet[0]) * t
        pb = feet[-1] + (tops[-1] - feet[-1]) * t
        beam(bone, "%s_ratline_%d" % (name, j), pa, pb, th, region, extend=0.04)


def rigging(bone, hull_bone, masts, bowsprit, sails):
    sa, sb, cap = bowsprit
    d = norm(sb - sa)
    for mname, (z, top1, top2, head, dm) in MASTS.items():
        for side, sn in SIDES:
            # the channel: a ledge on the hull side carrying the deadeyes of the lower shrouds
            za, zb = z - 2.9, z + 0.4
            y0 = cs.rail_y((za + zb) / 2) - 0.3
            pa, pb = hp(za, y0, side, 0.3), hp(zb, y0, side, 0.3)
            beam(hull_bone, "channel_%s_%s" % (mname, sn), pa, pb, 0.14, "wood_dark", width=0.6, extend=0.05)
            for j, zk in enumerate((za + 0.3, zb - 0.3)):
                beam(hull_bone, "channel_knee_%s_%s%d" % (mname, sn, j), hp(zk, y0 - 0.7, side, 0.02), hp(zk, y0 - 0.05, side, 0.5), 0.12,
                     "wood_dark", width=0.12)
            feet, tops = [], []
            zf = np.linspace(z + 0.1, za + 0.35, 4)
            for k, zz in enumerate(zf):
                foot = channel_point(zz, side, 0.52, -0.05)
                feet.append(foot + v3(0, 0.36, 0))
                tops.append(v3(side * (dm / 2 + 0.05 + 0.08 * k), top1 - 0.15, z - 0.1 * k))
                disc(bone, "deadeye_%s_%s%d" % (mname, sn, k), foot + v3(0, 0.36, 0), (side, 0, 0), 0.12, 0.08, "dark_wood")
                disc(bone, "deadeye_low_%s_%s%d" % (mname, sn, k), foot, (side, 0, 0), 0.12, 0.08, "dark_wood")
                beam(bone, "lanyard_%s_%s%d" % (mname, sn, k), foot + v3(0, 0.05, 0), foot + v3(0, 0.31, 0), 0.05, "rope")
                beam(bone, "chain_%s_%s%d" % (mname, sn, k), foot - v3(0, 0.06, 0), hp(zz, foot[1] - 1.1, side, 0.04), 0.06, "iron")
            ladder(bone, "%s_lower_%s" % (mname, sn), tops, feet)
            # futtock shrouds under the top
            s = 1.25 + dm * 0.4
            for k in range(2):
                beam(bone, "futtock_%s_%s%d" % (mname, sn, k), v3(side * s * 0.95, top1 + 0.05, z - 0.4 - 0.6 * k),
                     v3(side * dm * 0.5, top1 - 1.5, z - 0.1 * k), 0.05, "rope")
            # topmast shrouds (a smaller ladder from the rim of the top to the crosstrees)
            r2 = dm * 0.33
            t2 = [v3(side * (r2 + 0.04), top2 - 0.1, z + 0.45) for _ in range(3)]
            f2 = [v3(side * (s - 0.08), top1 + 0.32, z - 0.15 - 0.7 * k) for k in range(3)]
            ladder(bone, "%s_top_%s" % (mname, sn), t2, f2, step=0.42, th=0.055)
            # topgallant shrouds
            beam(bone, "%s_tg_shroud_%s" % (mname, sn), v3(side * 0.22, head - 1.6, z + 0.75), v3(side * 0.95, top2 + 0.05, z + 0.45), 0.05,
                 "rope")
            # the topmast backstays: long rope ladders from the crosstrees down to the rail well aft of the
            # mast (the diagonal ladders of the side view), and the topgallant backstays
            zb1 = za - (4.6 if mname == "fore" else 2.4)
            ladder(bone, "%s_backstay_%s" % (mname, sn), [v3(side * (r2 + 0.04), top2 + 0.3, z + 0.4), v3(side * (r2 + 0.08), top2 + 0.1, z + 0.3)],
                   [channel_point(zb1, side, 0.36, 0.0), channel_point(zb1 - 0.7, side, 0.36, 0.0)], step=0.5, th=0.06)
            beam(bone, "%s_tg_backstay_%s" % (mname, sn), v3(side * 0.22, head - 1.2, z + 0.75), channel_point(zb1 - 1.6, side, 0.4, 0.0),
                 0.05, "rope")
    fz, mz = cs.FORE_MAST_Z, cs.MAIN_MAST_Z
    ropes = [(name, a, b) for name, (a, b) in stays(bowsprit).items()]
    peak = GAFF[1] + norm(GAFF[1] - GAFF[0]) * 0.25
    ropes += [
        ("bobstay", cap - d * 0.6 + v3(0, -0.15, 0), v3(0, 0.9, BOW_Z + cs.rake(BOW_Z, 0.9) + 0.1)),
        ("martingale", cap + v3(0, -1.55, 0.15), sb + v3(0, 0.2, 0)),
        ("martingale_back", cap + v3(0, -1.55, 0.15), v3(0, 3.6, BOW_Z + cs.rake(BOW_Z, 3.6) + 0.1)),
        # the gaff hoisted by its halyards from the main topmast; its vang down to the ensign staff
        ("peak_halyard", v3(0, MASTS["main"][2] - 0.4, mz + 0.45), GAFF[0] + (GAFF[1] - GAFF[0]) * 0.72 + v3(0, 0.12, 0)),
        ("throat_halyard", v3(0, MASTS["main"][1] + 1.6, mz + 0.45), GAFF[0] + (GAFF[1] - GAFF[0]) * 0.3 + v3(0, 0.12, 0)),
        ("gaff_vang", peak, ENSIGN_TOP),
        ("spanker_sheet", BOOM[1] + v3(0, -0.1, 0.4), v3(0, Q + 1.0, TZ + 0.3)),
        ("main_stay_ring", v3(0, M + 0.1, -1.9), v3(0, M + 0.25, -1.9)),
    ]
    outer_clew, inner_clew = sails["jib_clews"]
    for side, sn in SIDES:
        ropes.append(("jib_guy_" + sn, sb + v3(0, 0.25, 0), hp(19.3, cs.rail_y(19.3), side, 0.2)))
        ropes.append(("bowsprit_shroud_" + sn, sa + d * 4.0, hp(20.4, 2.6, side, 0.05)))
        ropes.append(("jib_sheet_outer_" + sn, outer_clew, hp(14.6, cs.rail_y(14.6), side, -0.1)))
        ropes.append(("jib_sheet_inner_" + sn, inner_clew, hp(12.6, cs.rail_y(12.6), side, -0.1)))
        # braces: the fore yard's lead aft to the main mast, the main yard's to the quarterdeck rail
        y, half = SQUARE_SAILS[0][2], SQUARE_SAILS[0][4]
        fo = yard_step("fore", "fore_course")[1]
        arm = gn.braced((side * (half + 0.3), y, fz + fo), fz, BRACE)
        ropes.append(("fore_brace_" + sn, arm, v3(side * 0.6, MASTS["main"][1] - 2.0, mz + 0.2)))
        arm = gn.braced((side * (MAIN_YARD[1] + 0.3), MAIN_YARD[0], mz + yard_step("main", "main_yard")[1]), mz, BRACE)
        ropes.append(("main_brace_" + sn, arm, hp(-17.6, Q + 1.0, side, -0.25)))
        # the lifts holding the foot spar (with its lanterns) under the fore yard arms, outside the leeches
        top = gn.braced((side * (SQUARE_SAILS[0][4] + 0.4), SQUARE_SAILS[0][2] - 0.05, fz + fo), fz, BRACE)
        foot = gn.braced((side * (SQUARE_SAILS[0][5] + 0.35), SQUARE_SAILS[0][3] - 0.1, fz + fo + 0.25), fz, BRACE)
        ropes.append(("fore_foot_lift_" + sn, top, foot))
        # sheets of the fore course from the ends of its foot spar down to the rail
        clew = gn.braced((side * (SQUARE_SAILS[0][5] + 0.25), SQUARE_SAILS[0][3] - 0.15, fz + fo + 0.25), fz, BRACE)
        ropes.append(("fore_sheet_" + sn, clew, hp(fz - 4.5, cs.rail_y(fz - 4.5), side, -0.15)))
    for name, a, b in ropes:
        beam(bone, "rope_" + name, a, b, 0.06, "rope")


# ---------------------------------------------------------------- flags
def flag(parent, name, root_pt, w, h, n=3, fly=(0, 0, -1)):
    """Flag in two bones (the animation swings the root half and the fly); each half in n strips
    following a soft wave (as generate_galleon's flags). The fly points along `fly` (horizontal; aft by
    default)."""
    root_pt = v3(*root_pt)
    fly = norm(v3(*fly))
    side = np.cross(v3(0, 1, 0), fly)
    fb = Bone("flag_" + name, origin=tuple(root_pt), parent=parent)
    ft = Bone("flag_%s_tip" % name, origin=tuple(root_pt + fly * (w / 2)), parent=fb)
    amp = min(0.16, 0.07 * w)

    def P(s):
        return root_pt + side * (amp * math.sin(2 * math.pi * s) * (0.35 + s)) + fly * (w * s)
    for half, bone in enumerate((fb, ft)):
        for k in range(n):
            s0, s1 = (half + k / n) / 2, (half + (k + 1) / n) / 2
            a, b = P(s0), P(s1)
            dd = norm(b - a)
            axes = np.column_stack([np.cross(v3(0, 1, 0), dd), v3(0, 1, 0), dd])
            c = add_cube(bone, "flag_%s_%s%d" % (name, "ab"[half], k), (a + b) / 2 + v3(0, -h / 2, 0), axes,
                         (0.03, h, np.linalg.norm(b - a) + 0.015), {"all": None, "+1": "flag", "-1": "flag"},
                         stretch=True, u_dir=fly, v_dir=v3(0, -1, 0))
            gn.set_sub(c, (s0, 0, s1, 1), faces=("west", "east"))
    return fb


ENSIGN_BASE = v3(-2.6, Q - 0.02, TZ - 0.6)    # the ensign staff on the starboard side of the stern balcony (back view)
ENSIGN_TOP = ENSIGN_BASE + v3(0, 5.6, -0.25)    # its head: the flag flies above the end of the boom (side view)


def flags(root, masts, castle_bone):
    """The two black pirate flags of the reference: at the peak of the spanker's gaff, on a short staff,
    and on the ensign staff of the stern."""
    mb = masts["main"][0]
    peak = GAFF[1] + norm(GAFF[1] - GAFF[0]) * 0.25
    beam(mb, "gaff_flagstaff", peak, peak + v3(0, 2.0, 0), 0.08, "wood_dark")
    disc(mb, "gaff_flagstaff_knob", peak + v3(0, 2.05, 0), (0, 1, 0), 0.08, 0.1, "bronze")
    flag(mb, "gaff", peak + v3(0, 1.95, 0), 3.0, 1.9)
    round_bar(castle_bone, "ensign_staff", ENSIGN_BASE, ENSIGN_TOP, 0.14, "wood_dark")
    disc(castle_bone, "ensign_staff_knob", ENSIGN_TOP + v3(0, 0.05, 0), (0, 1, 0), 0.1, 0.12, "bronze")
    # the wind from the port quarter blows it out aft and to starboard: seen beyond the clew of the
    # spanker on the side view, and from astern (back view)
    flag(castle_bone, "stern", ENSIGN_TOP + v3(0, -0.1, -0.03), 3.0, 1.9, fly=(-0.5, 0, -0.866))


# ---------------------------------------------------------------- helm, rudder
def helm(bone):
    hz = cs.HELM_Z
    hub = v3(0, Q + 1.05, hz)
    disc(bone, "helm_pedestal_base", (0, Q + 0.06, hz + 0.1), (0, 1, 0), 0.32, 0.12, "wood_dark", n=3)
    turned(bone, "helm_pedestal", (0, Q + 0.1, hz + 0.1), (0, hub[1] + 0.1, hz + 0.1),
           [(0, 0.36), (0.12, 0.26), (0.5, 0.3), (0.9, 0.3), (1, 0)], "wood_dark")
    round_bar(bone, "helm_axle", (0, hub[1], hz + 0.2), (0, hub[1], hz - 0.14), 0.1, "iron")
    wheel = Bone("helm_wheel", origin=tuple(hub), parent=bone)
    r = 0.66
    zax = v3(0, 0, 1)
    disc(wheel, "helm_hub", hub, zax, 0.14, 0.22, "bronze", n=3)
    for k in range(8):
        a = 2 * math.pi * k / 8
        dv = v3(math.cos(a), math.sin(a), 0)
        round_bar(wheel, "helm_spoke_%d" % k, hub + dv * 0.1, hub + dv * r, 0.07, "wood_mid")
        turned(wheel, "helm_handle_%d" % k, hub + dv * (r + 0.04), hub + dv * (r + 0.3), [(0, 0.07), (0.3, 0.1), (0.7, 0.07), (1, 0)],
               "wood_mid")
    for k in range(16):
        a, a2 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
        p0, p1 = hub + v3(math.cos(a), math.sin(a), 0) * r, hub + v3(math.cos(a2), math.sin(a2), 0) * r
        beam(wheel, "helm_rim_%d" % k, p0, p1, 0.1, "wood_dark", width=0.1, up=zax, extend=0.02)
    # binnacle and a compass beside the wheel
    bn = v3(1.1, Q, hz + 0.3)
    disc(bone, "binnacle", bn + v3(0, 0.45, 0), (0, 1, 0), 0.24, 0.9, "wood_mid")
    disc(bone, "binnacle_top", bn + v3(0, 0.93, 0), (0, 1, 0), 0.26, 0.06, "bronze")
    disc(bone, "binnacle_card", bn + v3(0, 0.97, 0), (0, 1, 0), 0.17, 0.02, {"all": "bronze", "+2": "compass"})


def rudder(root):
    piv = v3(0, 0.0, TZ - 0.15)
    rb = Bone("rudder", origin=tuple(piv), parent=root)
    zf = TZ - 0.18
    y_top, y_bot = cs.sheer_y(TZ) - 0.5, cs.keel_y(TZ) - 0.05
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
    round_bar(rb, "rudder_stock", (0, y_bot, zf - 0.08), (0, cs.sheer_y(TZ) + 0.3, zf - 0.08), 0.26, "wood_dark")


# ---------------------------------------------------------------- deck fittings, repairs
def grating(bone, name, cx, cz, w, l, y):
    """Hatch: a low coaming round a grating."""
    add_cube(bone, name, (cx, y + 0.08, cz), EYE, (w, 0.08, l), {"all": "wood_dark", "+2": "grating"}, stretch=True)
    for k, (dx, dz, sx, sz) in enumerate(((0, l / 2, w + 0.2, 0.16), (0, -l / 2, w + 0.2, 0.16), (w / 2, 0, 0.16, l), (-w / 2, 0, 0.16, l))):
        add_cube(bone, "%s_coaming_%d" % (name, k), (cx + dx, y + 0.12, cz + dz), EYE, (sx, 0.24, sz), "wood_dark")


def deck_fittings(bone, detail):
    # hatches before the fore mast, between the masts and abaft the main mast; the capstan before it
    grating(bone, "grating_fore", 0.0, 10.6, 2.0, 2.0, M)
    grating(bone, "grating_main", 0.0, 0.8, 2.0, 2.0, M)
    grating(bone, "grating_aft", 0.0, -10.6, 1.8, 1.6, M)
    gn.g_capstan(bone, "capstan", (0, M, -4.4))
    # the eye bolt of the main stay on the deck
    disc(bone, "main_stay_eyebolt", (0, M + 0.04, -1.9), (0, 1, 0), 0.16, 0.08, "iron")
    # coaming and a light rail round the companion hatch (open: the stair goes down to the common room)
    x0, x1 = cs.COMPANION_X
    z0, z1 = cs.COMPANION_Z
    for k, (a, b) in enumerate(((v3(x0, M, z0), v3(x0, M, z1)), (v3(x1, M, z0), v3(x1, M, z1)), (v3(x0, M, z0), v3(x1, M, z0)))):
        beam(bone, "companion_coaming_%d" % k, a + v3(0, 0.1, 0), b + v3(0, 0.1, 0), 0.2, "wood_dark", width=0.14, extend=0.07)
    for k, (x, z) in enumerate(((x0, z0), (x1, z0), (x0, z1 - 0.1))):
        add_cube(bone, "companion_post_%d" % k, (x, M + 0.5, z), EYE, (0.12, 1.0, 0.12), "wood_dark")
    beam(bone, "companion_rail_0", (x0, M + 0.95, z0), (x1, M + 0.95, z0), 0.09, "rail", extend=0.05)
    beam(bone, "companion_rail_1", (x0, M + 0.95, z0), (x0, M + 0.95, z1 - 0.1), 0.09, "rail", extend=0.05)
    # coils of rope by the masts, a bell at the fore mast
    for k, (x, z) in enumerate(((1.4, cs.MAIN_MAST_Z - 1.4), (-1.3, cs.FORE_MAST_Z - 1.3), (1.2, cs.MAIN_MAST_Z + 1.5), (-1.2, -12.0))):
        sd.rope_coil(gg, detail, "coil_%d" % k, (x, M, z), r=0.34, rope="rope")
    sd.bell(gg, bone, "bell", (0.0, M, cs.FORE_MAST_Z + 1.6), metal="bronze", wood="wood_dark")


def repairs(bone):
    """The patched hull: replaced planks of other woods, riveted iron plates, a cream plate across the
    bands (detail view), small square scuttles along the lower deck."""
    rng = np.random.RandomState(7)
    for side, sn in SIDES:
        for k in range(14):
            z = rng.uniform(-19.5, 17.5)
            y = rng.choice([rng.uniform(-0.9, -0.5), rng.uniform(0.6, 1.7), rng.uniform(2.8, 3.6)])
            w = rng.choice([0.5, 1.0, 1.5])
            reg = "patch_wood" if k % 3 else "repair"
            hull_decal(bone, "repair_%s%d" % (sn, k), z, y, side, w, 0.25, reg, out=0.015, th=0.025)
        for k, (z, y) in enumerate(((-4.0, 1.25), (12.6, 1.05), (-15.4, 1.5), (6.8, 3.3))):
            hull_decal(bone, "iron_plate_%s%d" % (sn, k), z + (0.6 if side < 0 else 0.0), y, side, 0.75, 0.6, "plate", out=0.02, th=0.04)
        z = 2.1 if side > 0 else -6.3
        hull_decal(bone, "cream_plate_" + sn, z, 1.3, side, 0.55, 1.7, "stripe", out=0.025, th=0.05)
        for k, z in enumerate((-18.0, -15.2, -12.0, -9.0, -6.0, -3.0, 6.0, 9.5, 12.5)):
            y = 3.05 + band_lift(z, 0.8) * 0.9
            hull_decal(bone, "scuttle_frame_%s%d" % (sn, k), z, y, side, 0.5, 0.5, "wood_dark", out=0.02, th=0.04, stretch=False)
            hull_decal(bone, "scuttle_%s%d" % (sn, k), z, y, side, 0.3, 0.3, "iron", out=0.045, th=0.02)


# ---------------------------------------------------------------- furniture made for the ship
def f_long_table(bone, name, x0, x1, z0, z1, y):
    add_cube(bone, "lit_" + name + "_top", ((x0 + x1) / 2, y + 0.8, (z0 + z1) / 2), DECK_AXES, (z1 - z0, 0.12, x1 - x0),
             {"all": "wood_dark", "+2": "wood_light"})
    for k, z in enumerate(np.linspace(z0 + 0.4, z1 - 0.4, 3)):
        add_cube(bone, "lit_%s_trestle_%d" % (name, k), ((x0 + x1) / 2, y + 0.38, z), EYE, (x1 - x0 - 0.3, 0.76, 0.16), "wood_dark")
        add_cube(bone, "lit_%s_foot_%d" % (name, k), ((x0 + x1) / 2, y + 0.06, z), EYE, (x1 - x0 - 0.1, 0.12, 0.3), "wood_dark")
    beam(bone, "lit_%s_stretcher" % name, ((x0 + x1) / 2, y + 0.3, z0 + 0.4), ((x0 + x1) / 2, y + 0.3, z1 - 0.4), 0.12, "wood_dark")
    # tankards, plates, bottles on the table
    for k, z in enumerate(np.arange(z0 + 0.6, z1 - 0.3, 1.1)):
        x = (x0 + x1) / 2 + (0.3 if k % 2 else -0.3)
        add_cube(bone, "lit_%s_plate_%d" % (name, k), (x, y + 0.875, z), EYE, (0.34, 0.03, 0.34), "wood_light")
        if k % 2:
            disc(bone, "lit_%s_mug_%d" % (name, k), (x - 0.5 * (1 if k % 2 else -1), y + 0.97, z + 0.3), (0, 1, 0), 0.08, 0.2, "wood_mid")
        else:
            add_cube(bone, "lit_%s_bottle_%d" % (name, k), (x + 0.45, y + 1.0, z + 0.35), EYE, (0.12, 0.3, 0.12), "glass")


def f_bench(bone, name, x, z0, z1, y):
    add_cube(bone, "lit_" + name, (x, y + 0.42, (z0 + z1) / 2), DECK_AXES, (z1 - z0, 0.1, 0.42), {"all": "wood_dark", "+2": "wood_mid"})
    for k, z in enumerate((z0 + 0.25, z1 - 0.25)):
        add_cube(bone, "lit_%s_leg_%d" % (name, k), (x, y + 0.19, z), EYE, (0.36, 0.38, 0.1), "wood_dark")


def f_bunk(bone, name, p, l=1.9, w=0.95):
    p = v3(*p)
    add_cube(bone, "lit_" + name + "_frame", p + v3(0, 0.22, 0), EYE, (w, 0.44, l), "wood_dark")
    add_cube(bone, "lit_" + name + "_blanket", p + v3(0, 0.5, 0.15), EYE, (w - 0.1, 0.14, l - 0.4), {"all": "bedding"}, stretch=True)
    add_cube(bone, "lit_" + name + "_pillow", p + v3(0, 0.52, -l / 2 + 0.3), EYE, (w - 0.3, 0.14, 0.32), "stripe")
    add_cube(bone, "lit_" + name + "_head", p + v3(0, 0.55, -l / 2 + 0.04), EYE, (w, 1.1, 0.08), "wood_dark")
    add_cube(bone, "lit_" + name + "_foot", p + v3(0, 0.38, l / 2 - 0.04), EYE, (w, 0.76, 0.08), "wood_dark")


def f_desk(bone, name, p):
    p = v3(*p)
    add_cube(bone, "lit_" + name + "_top", p + v3(0, 0.78, 0), EYE, (1.8, 0.08, 0.95), {"all": "wood_dark", "+2": "wood_mid"})
    for k, sx in enumerate((-0.6, 0.6)):
        add_cube(bone, "lit_%s_pedestal_%d" % (name, k), p + v3(sx, 0.37, 0), EYE, (0.5, 0.74, 0.85), {"all": "wood_dark", "+3": "door"},
                 stretch=True)
    add_cube(bone, "lit_" + name + "_chart", p + v3(0, 0.83, 0.05), ry(0.15), (0.9, 0.01, 0.6), {"all": None, "+2": "chart"}, stretch=True)
    add_cube(bone, "lit_" + name + "_book", p + v3(0.6, 0.86, -0.2), ry(-0.3), (0.3, 0.08, 0.22), "red_paint")
    add_cube(bone, "lit_" + name + "_candle", p + v3(-0.65, 0.92, -0.2), EYE, (0.06, 0.2, 0.06), "stripe")
    add_cube(bone, "glow_" + name + "_flame", p + v3(-0.65, 1.05, -0.2), EYE, (0.04, 0.06, 0.04), "glow")


def f_chair(bone, name, p, facing=0.0):
    p = v3(*p)
    R = ry(facing)
    add_cube(bone, "lit_" + name + "_seat", p + v3(0, 0.45, 0), R, (0.5, 0.08, 0.5), "wood_mid")
    add_cube(bone, "lit_" + name + "_cushion", p + v3(0, 0.5, 0), R, (0.44, 0.05, 0.44), "red_paint")
    add_cube(bone, "lit_" + name + "_back", p + R @ v3(0, 0.82, -0.23), R, (0.5, 0.7, 0.07), "wood_dark")
    for k, (sx, sz) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        add_cube(bone, "lit_%s_leg_%d" % (name, k), p + R @ v3(sx * 0.2, 0.21, sz * 0.2), R, (0.07, 0.42, 0.07), "wood_dark")


def f_chest(bone, name, p):
    p = v3(*p)
    add_cube(bone, "lit_" + name, p + v3(0, 0.27, 0), EYE, (1.0, 0.54, 0.55), "wood_mid")
    add_cube(bone, "lit_" + name + "_lid", p + v3(0, 0.58, 0), EYE, (1.04, 0.1, 0.59), "wood_dark")
    for k, sx in enumerate((-0.35, 0.35)):
        add_cube(bone, "lit_%s_band_%d" % (name, k), p + v3(sx, 0.32, 0), EYE, (0.06, 0.62, 0.6), "iron")
    add_cube(bone, "lit_" + name + "_lock", p + v3(0, 0.45, 0.29), EYE, (0.12, 0.14, 0.03), "bronze")


def f_rug(bone, name, p, w, l, region="rug"):
    p = v3(*p)
    add_cube(bone, "lit_" + name, p + v3(0, 0.012, 0), EYE, (w, 0.02, l), {"all": None, "+2": region}, stretch=True, u_dir=v3(1, 0, 0),
             v_dir=v3(0, 0, 1))


def f_hearth(bone, lights, name, p, w=3.2):
    """Stone hearth (kitchen panel): a stone block with its fire opening, a mantle, a chimney hood up to
    the deck beams, hams hanging, a pot on the fire."""
    p = v3(*p)
    add_cube(bone, "lit_" + name + "_base", p + v3(0, 0.55, 0.05), EYE, (w, 1.1, 1.0), {"all": "wall_stone"})
    add_cube(bone, "lit_" + name + "_mantle", p + v3(0, 1.2, -0.1), EYE, (w + 0.2, 0.2, 1.1), "wood_dark")
    add_cube(bone, "lit_" + name + "_hood", p + v3(0, 2.15, 0.1), EYE, (w - 0.6, 1.7, 0.8), "wall_stone")
    add_cube(bone, "lit_" + name + "_opening", p + v3(0, 0.45, -0.46), EYE, (1.1, 0.7, 0.04), "iron")
    add_cube(bone, "glow_" + name + "_fire", p + v3(0, 0.3, -0.47), EYE, (0.8, 0.35, 0.04), "glow")
    disc(bone, "lit_" + name + "_pot", p + v3(0, 0.7, -0.3), (0, 1, 0), 0.24, 0.3, "iron")
    for k, x in enumerate((-1.0, -0.6, 0.7, 1.1)):
        beam(bone, "lit_%s_string_%d" % (name, k), p + v3(x, 2.5, -0.45), p + v3(x, 2.1, -0.45), 0.03, "rope")
        add_cube(bone, "lit_%s_ham_%d" % (name, k), p + v3(x, 1.88, -0.45), EYE, (0.2, 0.42, 0.16), "ham")


def f_work_table(bone, name, p, w=1.2, l=2.2):
    p = v3(*p)
    add_cube(bone, "lit_" + name + "_top", p + v3(0, 0.84, 0), DECK_AXES, (l, 0.12, w), {"all": "wood_dark", "+2": "wood_light"})
    add_cube(bone, "lit_" + name + "_body", p + v3(0, 0.4, 0), EYE, (w - 0.1, 0.8, l - 0.1), {"all": "wood_mid"})
    add_cube(bone, "lit_" + name + "_board", p + v3(0.1, 0.92, -0.4), EYE, (0.5, 0.04, 0.7), "wood_light")
    add_cube(bone, "lit_" + name + "_knife", p + v3(0.15, 0.95, 0.3), ry(0.4), (0.06, 0.02, 0.4), "iron")


def f_barrel(bone, name, p, h=0.9, r=0.33):
    gn.g_barrel(bone, name, p, h=h, r=r, wood="wood_mid")


def f_boat(bone, name, c):
    """The ship's boat on the quarterdeck (top view), keel up? no: on two chocks, its oars inside."""
    c = v3(*c)
    for k, dz in enumerate((-1.0, 1.0)):
        add_cube(bone, "%s_chock_%d" % (name, k), c + v3(0, -0.16, dz), EYE, (1.4, 0.3, 0.2), "wood_dark")
    gn.g_boat(bone, name, c, length=3.0, beam_=1.3, depth=0.5)


CUSTOM_BUILDERS = {"long_table": f_long_table, "bench": f_bench, "bunk": f_bunk, "desk": f_desk, "chair": f_chair, "chest": cf.chest,
                   "rug": f_rug, "work_table": f_work_table, "barrel": f_barrel, "captain_bed": cf.captain_bed, "chart_sheet": cf.chart_sheet,
                   "compass_box": cf.compass_box, "wall_chart": cf.wall_chart, "telescope": cf.telescope, "tankards": cf.tankards,
                   "bracket": cf.bracket, "pillar": cf.pillar, "coil": cf.coil, "post": cf.post, "bunk2": cf.bunk2, "hammock": cf.hammock,
                   "pot_rack": cf.pot_rack}


# ---------------------------------------------------------------- the rooms, on the interior grid
MAX_TILE = 8   # cells (4 blocks): the room regions are 64 px, 16 px a block
WOOD_ROOM = ("wall_wood", "floor", "ceil")
ROOM_MATERIALS = {"cabin": WOOD_ROOM, "coursive": WOOD_ROOM, "crew_port": WOOD_ROOM, "crew_stbd": WOOD_ROOM, "common_room": WOOD_ROOM,
                  "kitchen": ("wall_wood", "floor", "ceil"), "hold": ("hold_wall", "hold_floor", "ceil"),
                  "hold_stairs": ("hold_wall", "hold_floor", "ceil")}


def room_at(x, y, z):
    for name, (x0, x1, y0, y1, z0, z1) in ci.ROOMS.items():
        if x0 - 0.01 <= x <= x1 + 0.01 and y0 - 0.51 <= y <= y1 + 0.01 and z0 - 0.01 <= z <= z1 + 0.01:
            return name
    return None


def surfaces(rooms_bone, g):
    """Walls, floors, ceilings, stairs of the rooms: every face between a solid cell and an open cell
    (dry, door, furniture) is drawn, in the material of the room; the masts are drawn round instead."""
    k = g.k
    mast = np.zeros(k.shape, dtype=bool)
    for z, foot in ci.MASTS:
        mast |= (np.abs(g.X) < 0.5) & (np.abs(g.Z - z) < 0.5) & (g.Y > foot)
    solid = (k == ci.SOLID) & ~mast
    opened = (k == ci.DRY) | (k >= ci.DOOR) | (k == ci.FURNITURE) | (k == ci.LADDER)
    Cl = ci.CELL
    origin = (ci.X0, ci.Y0, ci.Z0)
    mats = [WOOD_ROOM] + [m for m in dict.fromkeys(ROOM_MATERIALS.values()) if m != WOOD_ROOM]
    mat_index = np.zeros(k.shape, dtype=np.int16)
    for name, box in ci.ROOMS.items():
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
                for (i0, j0, i1, j1, kk) in greedy(m2, nb_mat[tuple(sl)], al_i, al_j):
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
                        ry0, ry1 = (ci.ROOMS[room][2], ci.ROOMS[room][3]) if room else (y_lo, y_hi)
                        hgt = max(0.5, ry1 - ry0)
                        v0 = min(1.0, max(0.0, (ry1 - y_hi) / hgt))
                        v1 = min(1.0, max(v0 + 0.01, (ry1 - y_lo) / hgt))
                        sub = ((hz0 % MAX_TILE) / MAX_TILE, v0, (hz1 % MAX_TILE + 1) / MAX_TILE, v1)
                    for f in cube.faces.values():
                        if f is not None:
                            f["sub"] = sub
                    count += 1
    return count


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


def beams_below(bone):
    """Deck beams under the main deck and the lower deck, across the rooms (and knees against the sides)."""
    for name, (x0, x1, y0, y1, z0, z1) in ci.ROOMS.items():
        if name in ("hold_stairs", "cabin"):
            continue
        for k, z in enumerate(np.arange(z0 + 1.0, z1 - 0.4, 2.0)):
            w = min(x1, cs.hull_x(z, y1) - 0.5) - 0.02
            xa = max(x0, -(cs.hull_x(z, y1) - 0.5)) + 0.02
            beam(bone, "lit_beam_%s_%d" % (name, k), (xa, y1 - 0.12, z), (w, y1 - 0.12, z), 0.24, "wood_dark", width=0.3)


def doors(root, g):
    anims = []
    for d, (name, box) in ci.DOORS.items():
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
            add_cube(root, "lit_door_%d_jamb_%d" % (d, k), c, EYE, size, "wood_dark")
        c = v3((x0 + x1) / 2, y1 + w / 2, (z0 + z1) / 2)
        add_cube(root, "lit_door_%d_lintel" % d, c, EYE, (depth, w, sz + 2 * w) if along_z else (sx + 2 * w, w, depth), "wood_dark")
        if max(sx, sz) > 1.5:
            tracks = []
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
                add_cube(bone, "lit_door_%d_%s" % (d, leaf), c, EYE, size, {"all": "wood_dark", big[0]: "door", big[1]: "door"},
                         stretch=True, u_dir=v3(0, 0, 1) if along_z else v3(1, 0, 0), v_dir=v3(0, -1, 0))
                tracks.append((bone, [gg.rot_kf(0.0, (0, 0, 0)), gg.rot_kf(1.0, (0, sgn * 100, 0))]))
            anims.append(gg.animation("door_%d" % d, 1.0, "hold", tracks))
            continue
        if along_z:
            hinge = v3((x0 + x1) / 2, y0, z1)
            c = v3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
            size = (thin, sy, sz - 0.02)
            regs = {"all": "wood_dark", "+1": "door", "-1": "door"}
            udir = v3(0, 0, 1)
        else:
            hinge = v3(x1, y0, (z0 + z1) / 2)
            c = v3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
            size = (sx - 0.02, sy, thin)
            regs = {"all": "wood_dark", "+3": "door", "-3": "door"}
            udir = v3(1, 0, 0)
        bone = Bone("door_%d" % d, origin=tuple(hinge), parent=root)
        add_cube(bone, "lit_door_%d" % d, c, EYE, size, regs, stretch=True, u_dir=udir, v_dir=v3(0, -1, 0))
        anims.append(gg.animation("door_%d" % d, 1.0, "hold", [(bone, [gg.rot_kf(0.0, (0, 0, 0)), gg.rot_kf(1.0, (0, 100, 0))])]))
    return anims


def fallbacks(root):
    """Stand-ins of the decoration blocks, shown only when their mod is missing on a client."""
    for i, b in enumerate(cd.BLOCKS):
        x0, x1, y0, y1, z0, z1 = cd.footprint(b["block"], b["x"], b["y"], b["z"], b["yaw"], b["scale"])
        bone = Bone("fallback_%d" % i, parent=root)
        region = cd.FALLBACK_REGION.get(b["block"], "wood_mid")
        if region == "lantern":
            add_cube(bone, "lit_fallback_%d" % i, v3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), EYE, (0.3, 0.42, 0.3),
                     {"all": "lantern", "+2": "iron", "-2": "iron"}, stretch=True)
            continue
        add_cube(bone, "lit_fallback_%d" % i, v3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), EYE,
                 (max(0.04, x1 - x0), max(0.04, y1 - y0), max(0.04, z1 - z0)), region)


# ---------------------------------------------------------------- the model
def build(g):
    root = Bone("old_corsair")
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
    decks(deck_bone, castle_bone)
    castle(castle_bone, lights)
    quarter_galleries(castle_bone, lights)
    upper_balcony(castle_bone, lights)
    bowsprit = bow(bow_bone, lights)
    masts = {name: mast(root, fittings, name) for name in MASTS}
    sails_info = []
    sails = sails_and_spars(root, lights, masts, sails_info, bowsprit)
    rigging(ropes, hull_bone, masts, bowsprit, sails)
    flags(root, masts, castle_bone)
    helm(castle_bone)
    rudder(root)
    deck_fittings(deck_bone, detail)
    repairs(detail)
    # lanterns: under the bowsprit, on the stern corners and the stern, along the castle
    sa, sb, cap = bowsprit
    d = norm(sb - sa)
    lantern(lights, "lantern_jibboom", sb + v3(0, 0.15, -0.5), drop=0.45, s=1.1)
    lantern(lights, "lantern_bowsprit", sa + d * 6.0 + v3(0, -0.2, 0), drop=0.9, s=1.1)
    for side, sn in SIDES:
        x = side * (cs.hull_x(TZ, Q + 0.5) - 0.3)
        add_cube(castle_bone, "stern_lantern_post_" + sn, (x, Q + 0.75, TZ + 0.3), EYE, (0.22, 1.5, 0.22), "wood_dark")
        lantern(lights, "lantern_stern_" + sn, v3(x, Q + 1.5, TZ + 0.3), hang=False, s=1.4)
        lantern(lights, "lantern_gallery_" + sn, hp(-14.8, 6.6, side, 0.55), drop=0.3, s=1.0)
        beam(castle_bone, "lantern_gallery_arm_" + sn, hp(-14.8, 6.6, side, -0.05), hp(-14.8, 6.6, side, 0.6), 0.1, "iron")
    lantern(lights, "lantern_stern_walk", v3(0, 6.55, TZ - 1.0), drop=0.3, s=1.0)
    beam(castle_bone, "lantern_stern_walk_arm", v3(0, 6.6, TZ - 0.05), v3(0, 6.6, TZ - 1.05), 0.1, "iron")
    # the rooms, their doors, the beams, the furniture made for the ship
    m = surfaces(rooms, g)
    beams_below(fittings)
    for builder, kwargs, solid in cd.CUSTOM:
        kw = dict(kwargs)
        if builder == "hearth":
            f_hearth(furniture, lights, **kw)
        elif builder == "boat":
            f_boat(castle_bone, **kw)
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
    tracks = []
    for k, name in enumerate(("gaff", "stern")):
        f, ft = find(root, "flag_" + name), find(root, "flag_%s_tip" % name)
        a = 10
        sh = 0.2 * k
        for b, amp in ((f, a), (ft, -2 * a)):
            kfs = [rot_kf(round((t + sh) % 1.2, 4), (0, amp * math.cos(2 * math.pi * t / 1.2), 0), "catmullrom") for t in (0.0, 0.3, 0.6, 0.9)]
            kfs.sort(key=lambda q: q["time"])
            tracks.append((b, kfs))
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
        a = 5
        ph = 0.35 * k
        kfs = [rot_kf(round((ph + t) % 2.4, 4), (a * math.cos(2 * math.pi * t / 2.4), 0, a * 0.6 * math.sin(2 * math.pi * t / 2.4)),
                      "catmullrom") for t in (0.0, 0.6, 1.2, 1.8)]
        kfs.sort(key=lambda q: q["time"])
        tracks.append((b, kfs))
    anims.append(animation("lantern_sway", 2.4, "loop", tracks))
    return anims


def main():
    g = ci.build()
    cd.build()
    cd.apply_to_grid(g)
    cd.write(os.path.join(ROOT, cd.DECOR_PATH))
    size = g.write(os.path.join(ROOT, ci.GRID_PATH))
    reached, total = ci.walkable_report(g)
    print("decor blocks:", len(cd.BLOCKS), "seats:", len(cd.SEATS), "standing places:", total,
          "unreachable rooms:", [k for k, v in reached.items() if not v])
    root, n, m, sails_info, sails = build(g)
    anims = build_animations(root, sails_info)
    anims += doors(gg.find(root, "rooms"), g)
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    tex_path = os.path.join(tex_dir, "entity/old_corsair.png")
    ct.make_texture(tex_path, {"jib": sails["jib"], "staysail": sails["staysail"]})
    ct.make_item_icon(os.path.join(tex_dir, "item/old_corsair.png"))
    with open(tex_path, "rb") as f:
        png = f.read()
    textures = [gn.texture_entry("old_corsair.png", ct.SIZE, png, "entity", "old_corsair.png")]
    textures[0]["id"] = "0"
    model = gn.export(root, anims, textures, [
        os.path.join(ROOT, "blockbench/old_corsair.bbmodel"),
        os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/old_corsair.bbmodel"),
    ], name="old_corsair", visible_box=(60, 44, 0), extra={"medievalships_cull_thin_plates": True})
    print("grid bytes:", size, "hull boards:", n, "grid surfaces:", m, "cubes:", len(model["elements"]),
          "animations:", [a["name"] for a in model["animations"]])


if __name__ == "__main__":
    main()
