#!/usr/bin/env python3
"""Generates the Royal Lion Ship (royal_lion_ship, "Navire royal au lion") Blockbench model, its textures, its item
icon, its interior grid and its furniture.

Usage:  python3 tools/generate_royal_lion.py

Outputs:
  blockbench/royal_lion_ship.bbmodel                                             (editable, textures embedded)
  src/main/resources/assets/medievalships/models/entity/royal_lion_ship.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/royal_lion_ship.png
  src/main/resources/assets/medievalships/textures/entity/royal_lion_ship_sails.png
  src/main/resources/assets/medievalships/textures/item/royal_lion_ship.png
  src/main/resources/assets/medievalships/interiors/royal_lion_ship.grid         (collisions, dry rooms, doors)
  src/main/resources/assets/medievalships/interiors/royal_lion_ship_decor.json   (furniture of the mods, seats)

References (docs/RoyalLion_PLAN.md): four pictures of the same royal merchant ship of Lion Port: a dark wooden
hull with royal blue strakes between gilded wales, a row of royal blue heater shields with a gold rampant lion
along each side and lanterns between them, small lit ports; a gilded stepped beakhead and a leaping gold lion
figurehead under the bowsprit; a raised forecastle; three masts with royal blue square sails bordered in gold (a
big gold rampant lion on the main and fore courses), gold-railed fighting tops with lanterns, rope ladders up to
them, blue and gold swallow-tailed pennants at the mastheads, two blue jibs; a big stern castle: the captain's
cabin under the quarterdeck with arched lit windows and a stern gallery, the roundhouse (the royal state room) on
the quarterdeck with arched windows under a blue mansard roof with gold ridges, finials and a lantern turret, a
blue and white striped awning over the helm; banners with the lion on the castle; lanterns along the rails; deck
cargo. Inside: the captain's cabin, the state room, the crew quarters and the cargo hold; their walls, floors and
ceilings are drawn on the boundaries of the interior grid (tools/royal_lion_interior.py): what is drawn is what
collides.

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
import royal_lion_shape as fs  # noqa: E402
import royal_lion_interior as fi  # noqa: E402
import royal_lion_texture as ft  # noqa: E402
import royal_lion_decor as fd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ID = "royal_lion_ship"
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/%s/%d" % (ID, _uuid_counter[0])))


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

M, L, Q, C, F = fs.MAIN_DECK_Y, fs.LOWER_FLOOR_Y, fs.QUARTERDECK_Y, fs.CABIN_FLOOR_Y, fs.FORECASTLE_Y
CF = fs.CABIN_FRONT_Z
TZ = fs.TRANSOM_Z
RF = fs.ROUNDHOUSE_FRONT_Z
RH1 = fs.ROUNDHOUSE_CEIL_Y
FCZ = fs.FORECASTLE_Z
BOW_Z = fs.FORE_SCALE - 0.02   # where the planking closes on the stem
BRACE = math.radians(-10)       # square yards braced round (port arms aft)
QD_RAIL = fs.QD_BULWARK_TOP + 0.15
FC_RAIL = fs.FC_BULWARK_TOP + 0.15


# ---------------------------------------------------------------- hull geometry
def lift(z):
    return fs.sheer_y(z) - fs.SHEER_BASE


def band_lift(z, k):
    """Rise of the gold wales: they follow the sheer, and sweep up into the stem at the bow."""
    bow = min(1.0, max(0.0, (z - 12.0) / (BOW_Z - 12.0))) ** 1.7
    return k * lift(z) + (1.5 if k > 0.5 else 1.0) * bow


def rail_top(z):
    """Height of the gold cap rail: the sheer line of the rail, raised over the forecastle (its balustrade)."""
    r = fs.rail_y(z)
    f = min(1.0, max(0.0, (z - (FCZ - 1.5)) / 1.5))
    return r + max(0.0, FC_RAIL - r) * f


def hull_rows(z):
    """Points (x, y) of the outer hull section at z (one side, keel to sheer) and the region of each strake: dark
    wood below the water, a band of dark brown blocks, the low gold wale, the lower royal blue band (the lit ports),
    the middle gold wale, the upper royal blue band (the shields), the gold planksheer."""
    ys = fs.sheer_y(min(z, BOW_Z))
    pts = []
    for fx, fy in ((0.0, 1.0), (0.45, 0.9), (0.8, 0.55), (0.97, 0.12)):
        y = fy * fs.keel_y(min(z, fs.HALF_LENGTH + 0.6))
        zz = z - fs.rake(z, y)
        w, yk = fs.half_width(zz), fs.keel_y(min(zz, fs.HALF_LENGTH + 0.6))
        pts.append((max(0.16, fx * w), fy * yk))
    regs = ["hull_brown", "hull_brown", "hull_brown"]
    lo, mid = band_lift(z, 0.3), band_lift(z, 0.6)
    levels = [(0.3, "strake_brown2"), (2.0 + lo, "strake_lo"), (2.32 + lo, "gold_band"), (3.3 + mid, "strake_mid"),
              (3.62 + mid, "gold_band"), (ys - 0.35, "strake_hi"), (ys, "gold_band")]
    for y, reg in levels:
        y = min(y, ys - 0.06 * (len(levels) - len(regs)))
        y = max(y, pts[-1][1] + 0.08)
        pts.append((max(0.16, fs.hull_x(z, y)), y))
        regs.append(reg)
    return pts, regs


STRETCHED = ("strake_brown", "strake_brown2", "gold_band", "castle_panel", "taffrail", "carving", "scroll")
MOSAIC = ("strake_lo", "strake_mid", "strake_hi")


def strake(bone, name, a0, a1, b0, b1, th, region, outward, overlap=1.03, inner=None):
    cube = board(bone, name, a0, a1, b0, b1, th, region, outward, overlap=overlap, inner=inner)
    if region in STRETCHED:
        for f, spec in cube.faces.items():
            if spec is not None and spec["region"] == region:
                spec["stretch"] = True
                spec["v_dir"] = v3(0, -1, 0)
    return cube


STATIONS = [TZ, -19.4, -18.6, -17.6, -16.4, -15.0, -13.5, -12.0, -10.5, -9.0, -7.5, -6.0, -4.5, -3.0, -1.5, 0.0, 1.5, 3.0, 4.5, 6.0, 7.5,
            9.0, 10.5, 12.0, 13.3, 14.5, 15.6, 16.6, 17.5, 18.3, 19.0, 19.6, 20.1, BOW_Z, 21.0, 21.5, 22.0, 22.5, 23.0, 23.5, 24.0]


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


def hull_decal(bone, name, z, y, side, w, h, region, out=0.012, th=0.03, glow=False, stretch=True, faces=None):
    p, u, v, n = side_frame(z, y, side)
    c = p + n * (out + th / 2)
    regs = region if faces is None else {"all": None, "+3": region, "-3": faces}
    return add_cube(bone, ("glow_" if glow else "") + name, c, np.column_stack([u, v, n]), (w, h, th), regs, stretch=stretch,
                    u_dir=-u if side > 0 else u, v_dir=v3(0, -1, 0))


def stem_clip(z, y):
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
                    continue
                mid = (a0 + a1 + b0 + b1) / 4
                t = (a1 + b1) - (a0 + b0)
                outward = norm(v3(side * t[1], -side * t[0], 0) + v3(0, 0, 0.6 * max(0.0, mid[2] - 14) / 6))
                cube = strake(bone, "hull_%s%d_%d" % (sn, i, k), a0, a1, b0, b1, 0.14, regs[k], outward, overlap=1.03,
                              inner="hull_brown" if k < 4 else "hold_wall")
                if regs[k] in MOSAIC:
                    lu = cube.size[0] * 16 / 64
                    u0 = ((za - TZ) * 16 % 64) / 64
                    if u0 + lu > 1:
                        u0 = max(0.0, 1 - lu)
                    for spec in cube.faces.values():
                        if spec is not None and spec["region"] == regs[k]:
                            spec["sub"] = (u0, 0.0, u0 + lu, min(1.0, cube.size[1] * 16 / 32))
                            spec["u_dir"], spec["v_dir"] = v3(0, 0, 1), v3(0, -1, 0)
                n += 1
    for i in range(len(STATIONS) - 2):
        za, zb = STATIONS[i], STATIONS[i + 1]
        if zb > fs.HALF_LENGTH + 0.2:
            break
        beam(bone, "keel_%d" % i, (0, fs.keel_y(za) - 0.08, za), (0, fs.keel_y(zb) - 0.08, zb), 0.3, "dark_wood", width=0.36, extend=0.06)
    return n


def gold_rail(bone, name, path, h, posts_every=0.5, big_every=0, post_region="gold"):
    """Open gold balustrade along a path: a bottom rail, square gold balusters, a gold cap rail; every `big_every`
    balusters a stout post with a knob."""
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


def arch_window(bone, name, c, axes, w, h, lit=True, frame=0.12, inner=None):
    """An arched window on a wall (axes: u along the wall, v up, n out of it): the lit (or dark) panes cut out above
    the round head, a gold frame round it (jambs, sill, a keystone), its inside face when `inner` (a point offset)."""
    c = v3(*c)
    u, v, n = axes[:, 0], axes[:, 1], axes[:, 2]
    add_cube(bone, ("glow_" if lit else "") + name, c + n * 0.03, axes, (w, h, 0.04),
             {"all": None, "+3": "arch_window" if lit else "arch_window_in"}, stretch=True, u_dir=u, v_dir=-v)
    for s in (1, -1):
        add_cube(bone, "%s_jamb_%d" % (name, s > 0), c + u * s * (w / 2 + frame / 2) + v * (-h * 0.1) + n * 0.05, axes,
                 (frame, h * 0.8 + frame, 0.1), "gold")
    add_cube(bone, name + "_sill", c - v * (h / 2 + frame / 2) + n * 0.07, axes, (w + 2.4 * frame, frame, 0.16), "gold")
    add_cube(bone, name + "_key", c + v * (h / 2 + frame * 0.3) + n * 0.06, axes, (0.18, 0.2, 0.12), "gold")
    if inner is not None:
        add_cube(bone, name + "_in", c + v3(*inner), axes, (w, h, 0.03), {"all": None, "-3": "arch_window_in"}, stretch=True, u_dir=u, v_dir=-v)


# ---------------------------------------------------------------- the waist, the forecastle
def waist(bone, detail, lights):
    """The bulwarks from the castle to the bow: the solid royal blue strip over the gold planksheer, the gold
    balustrade on it (stout gold posts with knobs, lanterns on some), the gold wales along the hull, the raised
    forecastle balustrade, the bow closing round the stem."""
    zs = [z for z in STATIONS if CF - 0.6 <= z <= 23.0]
    for side, sn in SIDES:
        for i in range(len(zs) - 1):
            za, zb = zs[i], zs[i + 1]
            ya, yb = fs.sheer_y(za), fs.sheer_y(zb)
            ra, rb = rail_top(za), rail_top(zb)
            board(bone, "bulwark_%s%d" % (sn, i), hp(za, ya, side), hp(za, ya + 0.45, side), hp(zb, yb, side), hp(zb, yb + 0.45, side),
                  0.42, "hull_blue", v3(side, 0, 0), overlap=1.03, inner="hull_blue")
            beam(bone, "rail_cap_%s%d" % (sn, i), hp(za, ra, side, -0.18), hp(zb, rb, side, -0.18), 0.3, "rail", width=0.44, extend=0.08)
            gn.wale_bar(bone, "wale_%s%d" % (sn, i), hp(za, ya - 0.3, side, 0.06), hp(zb, yb - 0.3, side, 0.06), 0.22, 0.18, "gold", extend=0.05)
            if za < BOW_Z - 0.5:
                for k, (kk, y0) in enumerate(((0.3, 2.16), (0.6, 3.46))):
                    la, lb = y0 + band_lift(za, kk), y0 + band_lift(zb, kk)
                    gn.wale_bar(bone, "wale_low%d_%s%d" % (k, sn, i), hp(za, la, side, 0.05), hp(min(zb, BOW_Z), lb, side, 0.05), 0.2, 0.16,
                                "gold", extend=0.04)
            if za >= 17.0:
                board(bone, "bow_bulwark_%s%d" % (sn, i), hp(za, ya + 0.43, side), hp(za, ra, side), hp(zb, yb + 0.43, side), hp(zb, rb, side),
                      0.3, "hull_blue", v3(side, 0, 0), overlap=1.03, inner="hull_blue")
            elif za >= FCZ - 0.6:
                # the forecastle: a closed blue bulwark up to its balustrade's foot
                yt_a, yt_b = max(ya + 0.43, ra - 0.95), max(yb + 0.43, rb - 0.95)
                board(bone, "fc_bulwark_%s%d" % (sn, i), hp(za, ya + 0.43, side), hp(za, yt_a, side), hp(zb, yb + 0.43, side), hp(zb, yt_b, side),
                      0.3, "hull_blue", v3(side, 0, 0), overlap=1.03, inner="hull_blue")
    # the gold balustrade: square gold balusters under the cap rail, every third a stout post with a knob (lanterns
    # on some of them, as along the rails of the references)
    for side, sn in SIDES:
        for j, z in enumerate(np.arange(CF + 0.4, 17.4, 0.75)):
            r = rail_top(z)
            p = hp(z, r, side, -0.2)
            if j % 4 == 1:
                add_cube(bone, "rail_post_%s%d" % (sn, j), p + v3(0, -0.4, 0), EYE, (0.34, 1.0, 0.34), "gold")
                add_cube(bone, "rail_post_cap_%s%d" % (sn, j), p + v3(0, 0.18, 0), EYE, (0.46, 0.16, 0.46), "gold")
                if j % 8 == 5 and not (side < 0 and 0.5 < z < 5.0):
                    lantern(lights, "lantern_rail_%s%d" % (sn, j), p + v3(0, 0.26, 0), hang=False, s=1.0)
                else:
                    add_cube(bone, "rail_post_knob_%s%d" % (sn, j), p + v3(0, 0.35, 0), EYE, (0.26, 0.18, 0.26), "gold")
            else:
                y0 = max(fs.sheer_y(z) + 0.45, r - 1.0 if z > FCZ - 0.6 else 0) if z > FCZ - 0.6 else fs.sheer_y(z) + 0.45
                y1 = r - 0.14
                if y1 - y0 > 0.1:
                    add_cube(detail, "baluster_%s%d" % (sn, j), hp(z, (y0 + y1) / 2, side, -0.2), EYE, (0.18, y1 - y0, 0.18), "gold")


def forecastle(bone, deck_bone):
    """The forecastle deck (6.0) from its aft edge to the bow, its stairs from the main deck (both sides), the gold
    balustrade across its aft edge between them."""
    zs = list(np.arange(FCZ, 21.6, 1.0))
    for j in range(len(zs) - 1):
        za, zb = zs[j], zs[j + 1]
        w = min(fs.hull_x(za, F), fs.hull_x(zb, F)) - 0.12
        if w < 0.3:
            continue
        add_cube(deck_bone, "fc_deck_%d" % j, (0, F - 0.08, (za + zb) / 2), DECK_AXES, (zb - za + 0.01, 0.16, 2 * w),
                 {"all": "deck", "-2": "dark_wood"})
    # the face of the forecastle step over the main deck, a gold moulding along it
    w = fs.hull_x(FCZ, M) - 0.2
    for side, sn in SIDES:
        x0, x1 = fs.FC_STAIR_X[1] + 0.02, w
        add_cube(bone, "fc_front_%s" % sn, (side * (x0 + x1) / 2, (M + F) / 2, FCZ + 0.08), EYE, (x1 - x0, F - M, 0.16), "hull_blue")
    add_cube(bone, "fc_front_mid", (0, (M + F) / 2, FCZ + 0.08), EYE, (2 * fs.FC_STAIR_X[0] - 0.04, F - M, 0.16), "hull_blue")
    add_cube(bone, "fc_front_band", (0, F - 0.06, FCZ - 0.02), EYE, (2 * w, 0.14, 0.12), "carving", stretch=True)
    n = int(round((F - M) / 0.5))
    for side, sn in SIDES:
        xa, xb = fs.FC_STAIR_X
        for k in range(1, n + 1):
            za = fs.FC_STAIR_Z[0] + (k - 1) * 0.5
            top = M + k * 0.5
            add_cube(bone, "fc_step_%s%d" % (sn, k), (side * (xa + xb) / 2, (M + top) / 2, za + 0.25), EYE, (xb - xa, top - M, 0.5),
                     {"all": "wood_dark", "+2": "deck"})
    x0 = fs.FC_STAIR_X[0] - 0.05
    gold_rail(bone, "fc_rail", [v3(-x0, F, FCZ + 0.25), v3(x0, F, FCZ + 0.25)], 0.95, posts_every=0.45, big_every=4)


# ---------------------------------------------------------------- the shields, ports, lanterns, banners on the hull
def hull_ornaments(bone, lights):
    """Along each side: the big royal blue heater shields with the gold lion on the upper blue band (gold bosses at
    their top corners), small lit ports in gold frames on the lower blue band, lanterns hanging from iron brackets
    under the middle wale between the shields."""
    for side, sn in SIDES:
        for k, z in enumerate(fs.SHIELD_Z):
            y = fs.SHIELD_Y + band_lift(z, 0.8) * 0.5
            hull_decal(bone, "shield_%s%d" % (sn, k), z, y, side, 1.8, 2.1, "shield", out=0.09, th=0.05, faces=None)
            # a dark backing board (the shield stands off the planking), gold studs
            p, u, v, nrm = side_frame(z, y + 0.5, side)
            add_cube(bone, "shield_back_%s%d" % (sn, k), p + nrm * 0.045, np.column_stack([u, v, nrm]), (1.2, 0.7, 0.08), "dark_wood")
            for s in (1, -1):
                add_cube(bone, "shield_stud_%s%d_%d" % (sn, k, s > 0), p + u * s * 0.62 + v * 0.38 + nrm * 0.14, np.column_stack([u, v, nrm]),
                         (0.14, 0.14, 0.08), "gold")
        for k, z in enumerate(fs.PORT_Z):
            y = fs.PORT_Y + band_lift(z, 0.45) * 0.6
            hull_decal(bone, "port_%s%d" % (sn, k), z, y, side, 0.62, 0.62, "port_lit", out=0.02, th=0.05, glow=True)
        zl = [(a + b) / 2 for a, b in zip(fs.SHIELD_Z[:-1], fs.SHIELD_Z[1:])]
        for k, z in enumerate(zl):
            if side < 0 and 0.5 < z < 5.0:
                continue       # the stowed gangplank hangs above here on the starboard side
            y = 1.95 + band_lift(z, 0.3)
            p, u, v, nrm = side_frame(z, y, side)
            beam(bone, "lantern_bracket_%s%d" % (sn, k), p + nrm * 0.02, p + nrm * 0.5 + v3(0, 0.12, 0), 0.08, "iron")
            lantern(lights, "lantern_hull_%s%d" % (sn, k), p + nrm * 0.5 + v3(0, 0.1, 0), drop=0.2, s=1.1)


# ---------------------------------------------------------------- the stern castle
def roundhouse_x(z, y):
    return fs.hull_x(z, y)


def stern(bone, castle, lights):
    """The transom (dark wood below, the blue bands and gold wales across), the captain's cabin's stern: four arched
    lit windows in gold frames, the gold stern gallery in front of them, the lion panel on the counter; the
    roundhouse's stern wall: four arched lit windows between gold pilasters under the gold cornice."""
    z = TZ
    pts, regs = hull_rows(z)
    for k in range(len(pts) - 1):
        (xa, ya), (xb, yb) = pts[k], pts[k + 1]
        for j in range(4):
            fa0, fa1 = -1 + j / 2, -1 + (j + 1) / 2
            strake(bone, "transom_%d_%d" % (k, j), v3(fa0 * xa, ya, z), v3(fa0 * xb, yb, z), v3(fa1 * xa, ya, z), v3(fa1 * xb, yb, z),
                   0.16, regs[k], v3(0, 0, -1), overlap=1.02, inner="hull_brown")
    ys = fs.sheer_y(z)
    # the lion panel on the counter, between the gold corner pilasters
    add_cube(bone, "transom_lion", (0, 2.9, z - 0.1), EYE, (1.6, 1.9, 0.06), {"all": "gold", "-3": "lion_relief"}, stretch=True)
    yb0 = 1.3 + band_lift(z, 0.3)
    for j, s in enumerate((1, -1)):
        xp = fs.hull_x(z, (ys + yb0) / 2) - 0.26
        add_cube(bone, "transom_pilaster_%d" % j, (s * xp, (ys + yb0) / 2, z - 0.14), EYE, (0.36, ys - yb0, 0.16), "gold")
    # the castle's stern from the sheer to the quarterdeck: blue panels, the four arched lit windows of the cabin
    rows = [(ys, ys + 0.25, "gold_band"), (ys + 0.25, Q - 0.4, "castle_panel"), (Q - 0.4, Q - 0.05, "scroll"), (Q - 0.05, Q + 0.3, "gold_band")]
    for k, (ya, yb, reg) in enumerate(rows):
        xa, xb = fs.hull_x(z, ya), fs.hull_x(z, yb)
        for j in range(4):
            fa0, fa1 = -1 + j / 2, -1 + (j + 1) / 2
            strake(castle, "stern_wall_%d_%d" % (k, j), v3(fa0 * xa, ya, z), v3(fa0 * xb, yb, z), v3(fa1 * xa, ya, z),
                   v3(fa1 * xb, yb, z), 0.16, reg, v3(0, 0, -1), overlap=1.02, inner="wall_wood")
    axes = np.column_stack([v3(-1, 0, 0), v3(0, 1, 0), v3(0, 0, -1)])
    wy = 6.35
    for j, x in enumerate((-2.85, -0.95, 0.95, 2.85)):
        arch_window(castle, "stern_window_%d" % j, (x, wy, z - 0.08), axes, 0.95, 1.55, inner=(0, 0, 0.2))
    for j, x in enumerate((-3.9, -1.9, 0.0, 1.9, 3.9)):
        add_cube(castle, "stern_pilaster_%d" % j, (x, (ys + Q) / 2, z - 0.15), EYE, (0.26, Q - ys - 0.2, 0.14), "gold")
    # the stern gallery: a gold-railed balcony in front of the cabin windows on carved consoles
    gy = ys + 0.15
    xg = fs.hull_x(z, gy) - 0.3
    add_cube(castle, "gallery_floor", (0, gy, z - 0.55), EYE, (2 * xg, 0.16, 0.9), {"all": "dark_wood", "+2": "deck"})
    add_cube(castle, "gallery_fascia", (0, gy - 0.16, z - 0.99), EYE, (2 * xg + 0.1, 0.3, 0.1), "scroll", stretch=True)
    for k, x in enumerate(np.linspace(-xg + 0.4, xg - 0.4, 5)):
        beam(castle, "gallery_console_%d" % k, v3(x, gy - 0.9, z - 0.05), v3(x, gy - 0.08, z - 0.85), 0.16, "gold", width=0.16)
    gold_rail(castle, "gallery_rail", [v3(-xg, gy + 0.08, z - 0.95), v3(xg, gy + 0.08, z - 0.95)], 0.7, posts_every=0.35, big_every=6)
    for s in (1, -1):
        gold_rail(castle, "gallery_rail_end_%d" % (s > 0), [v3(s * xg, gy + 0.08, z - 0.95), v3(s * xg, gy + 0.08, z - 0.12)], 0.7,
                  posts_every=0.35)
    # the roundhouse's stern wall (on the quarterdeck), its four arched windows, the cornice
    xq = fs.hull_x(z, Q + 1.5)
    add_cube(castle, "rh_stern_wall", (0, (Q + 0.3 + RH1) / 2, z + 0.12), EYE, (2 * xq - 0.2, RH1 - Q - 0.3, 0.2),
             {"all": "castle_panel", "+3": "wall_wood"}, stretch=True)
    for j, x in enumerate((-2.7, -0.9, 0.9, 2.7)):
        arch_window(castle, "rh_stern_window_%d" % j, (x, Q + 1.45, z + 0.0), axes, 0.9, 1.6)
    for j, x in enumerate((-3.75, -1.8, 0.0, 1.8, 3.75)):
        add_cube(castle, "rh_stern_pilaster_%d" % j, (x, (Q + 0.3 + RH1) / 2, z - 0.02), EYE, (0.24, RH1 - Q - 0.3, 0.12), "gold")
    add_cube(castle, "rh_stern_banner", (0, Q + 1.45, z - 0.03), EYE, (0.01, 0.01, 0.01), "gold")


def castle(bone, lights):
    """The stern castle sides (from the sheer to the quarterdeck): blue panels between gold posts, three arched lit
    windows of the captain's cabin, a gold scroll cornice and wale under the quarterdeck, banners with the lion; the
    quarterdeck balustrade forward of the roundhouse; the front bulkhead with the cabin door, its windows and the
    guard rail between the two stairs, the stairs."""
    zs = sorted(set(round(z, 3) for z in [z for z in STATIONS if TZ <= z <= CF] + [CF, RF]))
    for side, sn in SIDES:
        for i in range(len(zs) - 1):
            za, zb = zs[i], zs[i + 1]
            ya, yb = fs.sheer_y(za), fs.sheer_y(zb)
            for r, (fa, fb, reg) in enumerate(((0.0, 0.1, "gold_band"), (0.1, 0.78, "castle_panel"), (0.78, 0.9, "scroll"),
                                               (0.9, 1.0, "gold_band"))):
                y0a, y1a = ya + (Q + 0.3 - ya) * fa, ya + (Q + 0.3 - ya) * fb
                y0b, y1b = yb + (Q + 0.3 - yb) * fa, yb + (Q + 0.3 - yb) * fb
                strake(bone, "castle_wall_%s%d_%d" % (sn, i, r), hp(za, y0a, side), hp(za, y1a, side), hp(zb, y0b, side), hp(zb, y1b, side),
                       0.16, reg, v3(side, 0, 0), overlap=1.03, inner="wall_wood")
            gn.wale_bar(bone, "castle_wale_%s%d" % (sn, i), hp(za, Q - 0.05, side, 0.06), hp(zb, Q - 0.05, side, 0.06), 0.24, 0.18,
                        "gold", extend=0.05)
            gn.wale_bar(bone, "castle_wale_low_%s%d" % (sn, i), hp(za, ya - 0.3, side, 0.06), hp(zb, yb - 0.3, side, 0.06), 0.22, 0.18,
                        "gold", extend=0.05)
            if za >= RF - 1e-6:
                # the blue bulwark of the quarterdeck forward of the roundhouse
                board(bone, "qd_bulwark_%s%d" % (sn, i), hp(za, Q + 0.3, side), hp(za, Q + 0.75, side), hp(zb, Q + 0.3, side),
                      hp(zb, Q + 0.75, side), 0.3, "hull_blue", v3(side, 0, 0), overlap=1.03, inner="hull_blue")
            else:
                # the roundhouse's side wall up to its cornice
                for r, (y0, y1, reg) in enumerate(((Q + 0.3, RH1 - 0.32, "castle_panel"), (RH1 - 0.32, RH1, "scroll"))):
                    strake(bone, "rh_wall_%s%d_%d" % (sn, i, r), hp(za, y0, side), hp(za, y1, side), hp(zb, y0, side), hp(zb, y1, side),
                           0.18, reg, v3(side, 0, 0), overlap=1.03, inner="wall_wood")
        for j, z in enumerate((TZ + 0.25, -17.1, -14.4, -11.9, CF + 0.1)):
            y0 = fs.sheer_y(z)
            p0, p1 = hp(z, y0, side, 0.05), hp(z, Q, side, 0.05)
            add_cube(bone, "castle_post_%s%d" % (sn, j), (p0 + p1) / 2, EYE, (0.26, Q - y0, 0.26), "gold")
        # arched lit windows of the captain's cabin
        for j, z in enumerate((-18.4, -15.75, -13.15)):
            p, u, v, n = side_frame(z, 6.35, side)
            axes = np.column_stack([u if side < 0 else -u, v, n])
            arch_window(bone, "castle_window_%s%d" % (sn, j), p, axes, 1.0, 1.5, inner=tuple(-n * 0.22))
        # a banner with the lion hanging under the castle wale, between the windows
        for j, z in enumerate((-17.05, -14.45)):
            hull_decal(bone, "banner_%s%d" % (sn, j), z, Q - 1.05, side, 0.8, 1.6, "banner", out=0.06, th=0.03)
        # the roundhouse's side windows and pilasters
        for j, z in enumerate((-19.0, -17.5)):
            p, u, v, n = side_frame(z, Q + 1.45, side)
            axes = np.column_stack([u if side < 0 else -u, v, n])
            arch_window(bone, "rh_window_%s%d" % (sn, j), p, axes, 0.85, 1.55)
        for j, z in enumerate((TZ + 0.2, -18.25, RF - 0.15)):
            p0 = hp(z, Q + 0.3, side, 0.06)
            add_cube(bone, "rh_pilaster_%s%d" % (sn, j), p0 + v3(0, (RH1 - Q - 0.62) / 2, 0), EYE, (0.24, RH1 - Q - 0.62, 0.24), "gold")
        # quarterdeck balustrade, from the roundhouse to the castle front
        path = [hp(z, Q + 0.75, side, -0.22) for z in np.linspace(RF + 0.1, CF - 0.05, 5)]
        gold_rail(bone, "qd_rail_" + sn, path, QD_RAIL - Q - 0.75, posts_every=0.5, big_every=4)
    # the front bulkhead (main deck -> quarterdeck), the cabin door frame, two windows
    bz = CF - 0.08
    wq = fs.hull_x(CF, M) - 0.2
    for side, sn in SIDES:
        x0, x1 = 1.0, wq
        add_cube(bone, "bulkhead_" + sn, (side * (x0 + x1) / 2, (M + Q) / 2, bz), EYE, (x1 - x0, Q - M, 0.16),
                 {"all": "castle_panel", "-3": "wall_wood"}, stretch=True)
        add_cube(bone, "bulkhead_jamb_" + sn, (side * 1.1, (M + Q - 0.5) / 2, CF + 0.04), EYE, (0.2, Q - 0.5 - M + 0.2, 0.14), "gold")
        axes = np.column_stack([v3(1, 0, 0), v3(0, 1, 0), v3(0, 0, 1)])
        arch_window(bone, "bulkhead_window_" + sn, (side * 1.9, 6.0, CF + 0.0), axes, 0.75, 1.2)
    add_cube(bone, "bulkhead_lintel", (0, Q - 0.4, CF + 0.04), EYE, (2.4, 0.3, 0.16), "gold")
    add_cube(bone, "bulkhead_band", (0, Q - 0.05, CF + 0.05), EYE, (2 * wq, 0.2, 0.14), "scroll", stretch=True)
    add_cube(bone, "bulkhead_lion", (0, Q - 0.95, CF + 0.06), EYE, (0.7, 0.7, 0.04), {"all": "gold", "+3": "lion_relief"}, stretch=True)
    x0 = fs.QD_STAIR_X[0] - 0.05
    gold_rail(bone, "qd_front_rail", [v3(-x0, Q, CF - 0.22), v3(x0, Q, CF - 0.22)], 0.95, posts_every=0.45, big_every=5)
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
    for side, sn in SIDES:
        beam(bone, "lantern_bulkhead_arm_" + sn, v3(side * 1.6, Q - 0.6, CF + 0.02), v3(side * 1.6, Q - 0.6, CF + 0.55), 0.08, "iron")
        lantern(lights, "lantern_bulkhead_" + sn, v3(side * 1.6, Q - 0.62, CF + 0.5), drop=0.25, s=0.9)


def roundhouse(bone, lights):
    """The roundhouse's front wall (its double door, two arched windows, gold pilasters, the lion over the door), the
    blue mansard roof over it (four slopes of blue slates with gold hip and eave boards, a flat top with a gold
    cresting), gold finials at the corners and the lantern turret in the middle (a lit lantern under a pointed blue
    cap with a gold finial), the striped awning over the helm in front of it."""
    z = RF - 0.08
    w = fs.hull_x(RF, Q + 1.5) - 0.2
    for side, sn in SIDES:
        x0, x1 = 1.0, w
        add_cube(bone, "rh_front_" + sn, (side * (x0 + x1) / 2, (Q + RH1) / 2, z), EYE, (x1 - x0, RH1 - Q, 0.16),
                 {"all": "castle_panel", "-3": "wall_wood"}, stretch=True)
        add_cube(bone, "rh_front_jamb_" + sn, (side * 1.1, Q + 1.3, RF + 0.04), EYE, (0.2, 2.7, 0.14), "gold")
        axes = np.column_stack([v3(1, 0, 0), v3(0, 1, 0), v3(0, 0, 1)])
        arch_window(bone, "rh_front_window_" + sn, (side * 2.75, Q + 1.45, RF + 0.0), axes, 0.85, 1.5)
        add_cube(bone, "rh_front_pilaster_" + sn, (side * (w - 0.1), (Q + RH1) / 2, RF + 0.04), EYE, (0.24, RH1 - Q, 0.14), "gold")
    add_cube(bone, "rh_front_over_door", (0, (Q + 2.5 + RH1) / 2, z), EYE, (2.0, RH1 - Q - 2.5, 0.16), {"all": "castle_panel", "-3": "wall_wood"},
             stretch=True)
    add_cube(bone, "rh_front_lintel", (0, Q + 2.62, RF + 0.04), EYE, (2.4, 0.24, 0.16), "gold")
    add_cube(bone, "rh_front_cornice", (0, RH1 - 0.15, RF + 0.05), EYE, (2 * w + 0.2, 0.3, 0.14), "scroll", stretch=True)
    # the mansard roof: the eave at the walls (RH1), sloping 1.1 inboard up to the flat top
    rise, inset = 1.1, 1.05
    yt = RH1 + rise
    zr = [TZ, -19.4, -18.6, -17.6, -16.8, RF]

    def wx(zz):
        return fs.hull_x(zz, RH1) + 0.08
    for side, sn in SIDES:
        for i in range(len(zr) - 1):
            za, zb = zr[i], zr[i + 1]
            ta, tb = min(max(za, TZ + inset), RF - inset), min(max(zb, TZ + inset), RF - inset)
            a0, b0 = v3(side * wx(za), RH1, za), v3(side * wx(zb), RH1, zb)
            a1, b1 = v3(side * (wx(ta) - inset), yt, ta), v3(side * (wx(tb) - inset), yt, tb)
            board(bone, "roof_side_%s%d" % (sn, i), a0, a1, b0, b1, 0.14, "roof", v3(side, 1, 0), overlap=1.02, inner="ceil")
        # the hip boards (gold) at the corners and the eave board along the side
        for k, zc in enumerate((TZ, RF)):
            zi = TZ + inset if k == 0 else RF - inset
            beam(bone, "roof_hip_%s%d" % (sn, k), v3(side * wx(zc), RH1 + 0.04, zc), v3(side * (wx(zi) - inset), yt + 0.04, zi), 0.14, "gold",
                 width=0.22, extend=0.06)
        for i in range(len(zr) - 1):
            beam(bone, "roof_eave_%s%d" % (sn, i), v3(side * wx(zr[i]), RH1 + 0.02, zr[i]), v3(side * wx(zr[i + 1]), RH1 + 0.02, zr[i + 1]), 0.14,
                 "gold", width=0.24, extend=0.04)
    for k, (zc, zi, sgn) in enumerate(((TZ, TZ + inset, 1), (RF, RF - inset, -1))):
        xa, xi = wx(zc), wx(zi) - inset
        for j in range(4):
            f0, f1 = -1 + j / 2, -1 + (j + 1) / 2
            board(bone, "roof_end_%d_%d" % (k, j), v3(f0 * xa, RH1, zc), v3(f0 * xi, yt, zi), v3(f1 * xa, RH1, zc), v3(f1 * xi, yt, zi), 0.14,
                  "roof", v3(0, 1, -sgn), overlap=1.02, inner="ceil")
        beam(bone, "roof_eave_end_%d" % k, v3(-xa, RH1 + 0.02, zc), v3(xa, RH1 + 0.02, zc), 0.14, "gold", width=0.24, extend=0.04)
    xt = min(wx(TZ + inset), wx(RF - inset)) - inset
    add_cube(bone, "roof_top", (0, yt + 0.06, (TZ + RF) / 2), EYE, (2 * xt + 0.1, 0.14, RF - TZ - 2 * inset + 0.1), {"all": "gold", "+2": "roof"})
    for k, (a, b) in enumerate(polyline([v3(-xt, yt + 0.2, TZ + inset), v3(xt, yt + 0.2, TZ + inset), v3(xt, yt + 0.2, RF - inset),
                                         v3(-xt, yt + 0.2, RF - inset)], closed=True)):
        beam(bone, "roof_cresting_%d" % k, a, b, 0.2, "roof_ridge", width=0.12, extend=0.06)
    # gold finials at the four corners (the spires of the references) and on the middle of the front slope
    for k, (x, zc) in enumerate(((wx(TZ), TZ), (-wx(TZ), TZ), (wx(RF), RF), (-wx(RF), RF))):
        p = v3(np.sign(x) * (abs(x) - 0.1), RH1 + 0.1, zc + (0.1 if zc == TZ else -0.1))
        turned(bone, "finial_%d" % k, p, p + v3(0, 1.0, 0), [(0, 0.3), (0.2, 0.22), (0.35, 0.34), (0.55, 0.16), (0.8, 0.1), (1.0, 0)], "gold")
    # the lantern turret on the roof top
    tc = v3(0, yt + 0.12, (TZ + RF) / 2)
    add_cube(bone, "turret_base", tc + v3(0, 0.2, 0), EYE, (1.1, 0.4, 1.1), {"all": "gold", "+2": "roof"})
    gn.g_great_lantern(bone, "turret_lantern", tc + v3(0, 0.4, 0), 1.6, metal="gold")
    turned(bone, "turret_cap", tc + v3(0, 1.55, 0), tc + v3(0, 2.5, 0), [(0, 0.95), (0.4, 0.6), (0.75, 0.3), (1.0, 0)], "roof")
    turned(bone, "turret_finial", tc + v3(0, 2.45, 0), tc + v3(0, 3.0, 0), [(0, 0.16), (0.3, 0.22), (0.6, 0.1), (1.0, 0)], "gold")
    # the stern corner lanterns on gold posts at the roof's eave, hanging from iron arms
    for side, sn in SIDES:
        x = side * (wx(TZ) - 0.1)
        beam(bone, "stern_lantern_arm_" + sn, v3(x, RH1 - 0.5, TZ + 0.1), v3(x + side * 0.55, RH1 - 0.5, TZ - 0.45), 0.1, "iron")
        lantern(lights, "lantern_stern_" + sn, v3(x + side * 0.55, RH1 - 0.55, TZ - 0.45), drop=0.3, s=1.5)
    # the striped awning over the helm, from the roundhouse's front wall forward to its gold posts
    za, zb = RF + 0.05, fs.MIZZEN_Z - 0.75
    ya, yb = RH1 - 0.35, RH1 - 0.85
    xw = 3.3
    for k in range(6):
        x0, x1 = -xw + 2 * xw * k / 6, -xw + 2 * xw * (k + 1) / 6
        sag = 0.08 * math.sin(math.pi * (k + 0.5) / 6)
        board(bone, "awning_%d" % k, v3(x0, ya, za), v3(x0, yb - sag, zb), v3(x1, ya, za), v3(x1, yb - sag, zb), 0.06, "awning", v3(0, 1, 0.3),
              overlap=1.0, inner="awning")
    for k in range(6):
        x0, x1 = -xw + 2 * xw * k / 6, -xw + 2 * xw * (k + 1) / 6
        add_cube(bone, "awning_fringe_f%d" % k, ((x0 + x1) / 2, yb - 0.22, zb + 0.02), EYE, (x1 - x0, 0.42, 0.02),
                 {"all": None, "+3": "awning_fringe", "-3": "awning_fringe"}, stretch=True)
    for side, sn in SIDES:
        for k in range(3):
            z0, z1 = za + (zb - za) * k / 3, za + (zb - za) * (k + 1) / 3
            ym = ya + (yb - ya) * (k + 0.5) / 3
            add_cube(bone, "awning_fringe_%s%d" % (sn, k), (side * (xw + 0.01), ym - 0.22, (z0 + z1) / 2), EYE, (0.02, 0.42, z1 - z0),
                     {"all": None, "+1": "awning_fringe", "-1": "awning_fringe"}, stretch=True)
        add_cube(bone, "awning_post_" + sn, (side * (xw - 0.1), (Q + yb) / 2, zb - 0.1), EYE, (0.16, yb - Q, 0.16), "gold")
        add_cube(bone, "awning_post_knob_" + sn, (side * (xw - 0.1), yb + 0.1, zb - 0.1), EYE, (0.24, 0.2, 0.24), "gold")
        beam(bone, "awning_rod_" + sn, v3(side * xw, ya - 0.04, za), v3(side * xw, yb - 0.04, zb), 0.08, "gold")
    beam(bone, "awning_rod_front", v3(-xw, yb - 0.04, zb), v3(xw, yb - 0.04, zb), 0.08, "gold")


def decks(bone, castle_bone):
    """Main deck planking (with the two companion hatches left open), the quarterdeck forward of the roundhouse."""
    zs = list(np.arange(CF - 0.5, FCZ + 0.01, 1.0))
    if zs[-1] < FCZ:
        zs.append(FCZ)
    holes = [(fs.CREW_STAIR_X, fs.CREW_STAIR_Z), (fs.HOLD_STAIR_X, fs.HOLD_STAIR_Z)]
    for j in range(len(zs) - 1):
        za, zb = zs[j], zs[j + 1]
        w = min(fs.hull_x(za, M), fs.hull_x(zb, M)) - 0.12
        cuts = sorted(xr for xr, zr in holes if za < zr[1] - 1e-6 and zb > zr[0] + 1e-6)
        spans, x = [], -w
        for x0, x1 in cuts:
            spans.append((x, x0))
            x = x1
        spans.append((x, w))
        for k, (x0, x1) in enumerate(spans):
            if x1 - x0 < 0.05:
                continue
            add_cube(bone, "deck_%d_%d" % (j, k), ((x0 + x1) / 2, M - 0.08, (za + zb) / 2), DECK_AXES, (zb - za + 0.01, 0.16, x1 - x0),
                     {"all": "deck", "-2": "dark_wood"})
    zs = list(np.arange(RF, CF + 1e-6, 1.0))
    if zs[-1] < CF:
        zs.append(CF)
    for j in range(len(zs) - 1):
        za, zb = zs[j], zs[j + 1]
        w = min(fs.hull_x(za, Q), fs.hull_x(zb, Q)) - 0.1
        add_cube(castle_bone, "qdeck_%d" % j, (0, Q - 0.08, (za + zb) / 2), DECK_AXES, (zb - za + 0.01, 0.16, 2 * w), {"all": "deck", "-2": "ceil"})


# ---------------------------------------------------------------- the bow and the lion figurehead
def lion_figurehead(bone, A, s=1.0):
    """The gilded lion of the references at the stem head, under the bowsprit (123, 126): a big maned head thrust
    forward with open roaring jaws, the shaggy mane flowing back over the stem, the chest and the forelegs reaching
    forward and down with their claws out, the body melting into the gilded stem (A: the root of the neck on the
    stem, s: scale)."""
    A = v3(*A)
    gold, mane, face = "gold", "mane", "lion_face"
    H = A + v3(0, 0.55, 1.15) * s                    # the head
    # the chest and the body against the stem
    add_cube(bone, "figurehead_body", A + v3(0, -0.85, -0.05) * s, rx(-0.35), (1.15 * s, 1.9 * s, 1.1 * s), {"all": gold, "+3": mane})
    add_cube(bone, "figurehead_chest", A + v3(0, -0.2, 0.55) * s, rx(-0.5), (1.2 * s, 1.2 * s, 0.9 * s), mane)
    # the mane: big locks round the head and flowing back along the neck
    for k in range(18):
        a = 2 * math.pi * k / 18
        r = 0.78 if k % 2 else 0.9
        off = v3(math.cos(a) * r, math.sin(a) * r, -0.3 - 0.1 * (k % 3)) * s
        add_cube(bone, "figurehead_mane_%d" % k, H + off, rz(a) @ rx(-0.35), (0.5 * s, 0.38 * s, 0.8 * s if k % 2 else 0.95 * s), mane)
    add_cube(bone, "figurehead_mane_back", H + v3(0, 0.0, -0.75) * s, rx(-0.25), (1.6 * s, 1.7 * s, 0.8 * s), mane)
    add_cube(bone, "figurehead_mane_nape", A + v3(0, 0.45, 0.05) * s, rx(-0.6), (1.35 * s, 1.0 * s, 1.0 * s), mane)
    add_cube(bone, "figurehead_head", H, EYE, (0.98 * s, 0.95 * s, 0.85 * s), {"all": gold, "+3": face}, stretch=True)
    add_cube(bone, "figurehead_muzzle", H + v3(0, -0.12, 0.55) * s, EYE, (0.64 * s, 0.42 * s, 0.4 * s), gold)
    add_cube(bone, "figurehead_nose", H + v3(0, 0.06, 0.76) * s, EYE, (0.3 * s, 0.16 * s, 0.08 * s), "dark_wood")
    add_cube(bone, "figurehead_jaw", H + v3(0, -0.6, 0.38) * s, rx(0.5), (0.56 * s, 0.15 * s, 0.6 * s), gold)
    add_cube(bone, "figurehead_tongue", H + v3(0, -0.5, 0.46) * s, rx(0.5), (0.26 * s, 0.05 * s, 0.38 * s), "red_paint")
    add_cube(bone, "figurehead_mouth", H + v3(0, -0.36, 0.5) * s, EYE, (0.5 * s, 0.14 * s, 0.3 * s), "navy")
    add_cube(bone, "figurehead_brow", H + v3(0, 0.33, 0.44) * s, EYE, (0.86 * s, 0.13 * s, 0.14 * s), "carving")
    for x in (0.26, -0.26):
        t = "l" if x > 0 else "r"
        add_cube(bone, "figurehead_eye_" + t, H + v3(x, 0.17, 0.44) * s, EYE, (0.16 * s, 0.1 * s, 0.03 * s), "dark_wood")
        add_cube(bone, "figurehead_ear_" + t, H + v3(x * 1.55, 0.55, 0.0) * s, EYE, (0.22 * s, 0.24 * s, 0.14 * s), gold)
        for j, dy in enumerate((-0.32, -0.62)):
            add_cube(bone, "figurehead_fang_%s%d" % (t, j), H + v3(x * 0.6, dy + 0.06 * j, 0.7 - 0.12 * j) * s, EYE,
                     (0.07 * s, 0.14 * s, 0.07 * s), "white_paint")
        # the forelegs reaching forward and down, the paws with their claws out
        sh = A + v3(x * 1.7, -0.45, 0.55) * s
        el = A + v3(x * 1.9, -0.95, 1.25) * s
        paw = A + v3(x * 1.75, -1.55, 1.75) * s
        beam(bone, "figurehead_foreleg_" + t, sh, el, 0.42 * s, gold, width=0.42 * s, extend=0.12 * s)
        beam(bone, "figurehead_forearm_" + t, el, paw, 0.36 * s, gold, width=0.36 * s, extend=0.1 * s)
        add_cube(bone, "figurehead_paw_" + t, paw + v3(0, -0.04, 0.14) * s, EYE, (0.46 * s, 0.28 * s, 0.52 * s), gold)
        for j in (-1, 0, 1):
            add_cube(bone, "figurehead_claw_%s%d" % (t, j + 1), paw + v3(j * 0.13, -0.14, 0.44) * s, rx(0.5), (0.08 * s, 0.08 * s, 0.2 * s),
                     "carving")
    # the scrolled gold bracket under it, curling into the stem
    for k in range(4):
        a = -0.4 - 0.5 * k
        add_cube(bone, "figurehead_scroll_%d" % k, A + v3(0, -1.9 - 0.32 * k, -0.25 + 0.22 * math.sin(k * 1.3)) * s, rx(a),
                 (0.7 * s - 0.08 * k, 0.4 * s, 0.6 * s), "carving")


def bow(bone, lights):
    """Stem, the gilded stepped head rails sweeping up to the bowsprit (the gold beakhead of the references), the
    leaping lion figurehead, the catheads with their anchors, the bow lantern under the bowsprit, the bowsprit
    (dark wood with gold bands) with its cap and the jib-boom."""
    pts = []
    for j in range(9):
        t = j / 8
        y = fs.keel_y(fs.HALF_LENGTH) - 0.1 + (rail_top(fs.HALF_LENGTH) + 0.3 - fs.keel_y(fs.HALF_LENGTH) + 0.1) * t
        z = BOW_Z + fs.rake(BOW_Z, y) + 0.05 - 0.6 * (1 - t) ** 2.2
        pts.append(v3(0, y, z))
    for j, (a, b) in enumerate(polyline(pts)):
        beam(bone, "stem_%d" % j, a, b, 0.46, "gold" if j >= 2 else "wood_dark", width=0.44, extend=0.08)
    sa, sb = v3(*fs.BOWSPRIT_FOOT), v3(*fs.BOWSPRIT_TIP)
    d = norm(sb - sa)
    cap = sa + d * 9.0
    round_bar(bone, "bowsprit", sa - d * 1.4, cap + d * 0.3, 0.7, "mast")
    for k, t in enumerate((0.6, 2.4, 4.2, 6.0, 7.8)):
        round_bar(bone, "bowsprit_band_%d" % k, sa + d * (t - 0.1), sa + d * (t + 0.1), 0.78, "gold")
    add_cube(bone, "bowsprit_cap", cap + d * 0.15 + v3(0, 0.2, 0), gg.frame_from(d, v3(0, 1, 0)), (0.42, 0.9, 0.55), "gold")
    round_bar(bone, "jib_boom", cap - d * 1.8 + v3(0, 0.4, 0), sb + v3(0, 0.4, 0), 0.36, "mast")
    add_cube(bone, "jib_boom_end", sb + v3(0, 0.4, 0) + d * 0.1, gg.frame_from(d, v3(0, 1, 0)), (0.42, 0.42, 0.26), "gold")
    beam(bone, "dolphin_striker", cap + v3(0, -0.1, 0), cap + v3(0, -1.7, 0.15), 0.12, "wood_dark")
    # the lion figurehead on the stem head, under the bowsprit
    zt = 21.6
    lion_figurehead(bone, v3(0, rail_top(zt) - 1.15, zt + 0.35), 1.15)
    # the gilded head rails: from the forecastle rail curving down and forward to the stem head, stepped gold blocks
    head = v3(0, rail_top(zt) - 0.6, zt + 0.2)
    for side, sn in SIDES:
        for k, (dy, name, th) in enumerate(((0.0, "head_rail", 0.6), (-0.62, "head_rail_mid", 0.5), (-1.2, "head_rail_low", 0.4))):
            p0 = hp(16.5, rail_top(16.5) + dy - 0.2, side, 0.08)
            c = v3(side * 2.4, rail_top(19.5) + dy - 0.7, 20.3)
            p1 = head + v3(side * 0.34, dy + 0.05, -0.15 - 0.25 * k)
            pts_ = []
            for p in bezier(p0, c, p1, 8):
                if p[2] < BOW_Z + 2.0:
                    xm = fs.hull_x(p[2], p[1]) + th * 0.5 + 0.03
                    if abs(p[0]) < xm:
                        p = v3(side * xm, p[1], p[2])
                pts_.append(p)
            for q, (a, b) in enumerate(polyline(pts_)):
                if k < 2:
                    cmid = (a + b) / 2
                    add_cube(bone, "%s_%s%d" % (name, sn, q), cmid, EYE, (abs(b[0] - a[0]) + th * 0.9, th, abs(b[2] - a[2]) + 0.04), "gold")
                else:
                    cap_rail(bone, "%s_%s%d" % (name, sn, q), a, b, th, th * 1.2, "gold", extend=0.06)
        # cathead, its anchor
        z = 16.6
        y = rail_top(z) - 0.2
        base = hp(z, y, side, -0.3)
        tip = hp(z + 0.5, y + 0.15, side, 0.9)
        beam(bone, "cathead_" + sn, base, tip, 0.32, "wood_dark", width=0.32)
        add_cube(bone, "cathead_lion_" + sn, tip + v3(side * 0.02, 0, 0.18), EYE, (0.34, 0.34, 0.06), {"all": "gold", "+3": "lion_face"},
                 stretch=True)
        x = side * (fs.hull_x(z + 0.6, 3.0) + 0.25)
        gn.g_anchor(bone, "anchor_" + sn, (x, y - 0.4, z + 0.5), (x, 2.0, z + 0.3), (0, 0, 1))
        disc(bone, "hawse_" + sn, side_frame(17.6, 4.0, side)[0] + v3(side * 0.03, 0, 0), (side, 0, 0), 0.16, 0.06, "iron")
    # the bow lantern hanging under the bowsprit (071)
    lp = sa + d * 3.2
    beam(bone, "bow_lantern_arm", lp + v3(0, -0.3, 0), lp + v3(0, -0.6, 0.2), 0.08, "iron")
    lantern(lights, "lantern_bow", lp + v3(0, -0.6, 0.2), drop=0.45, s=1.5)
    return sa, sb, cap


# ---------------------------------------------------------------- masts, yards, sails
MASTS = {
    # name: (z, top y (fighting top), topmast crosstrees y, masthead y, lower mast diameter)
    "fore": (fs.FORE_MAST_Z, 19.2, 25.0, fs.FORE_MAST_TOP, 1.0),
    "main": (fs.MAIN_MAST_Z, 20.0, 26.2, fs.MAIN_MAST_TOP, 1.06),
    "mizzen": (fs.MIZZEN_Z, 18.4, None, fs.MIZZEN_TOP, 0.8),
}
MAST_FOOT = {"fore": L - 0.4, "main": L - 0.4, "mizzen": Q}
# square sails: mast, name, yard y, foot y, half width at the head, at the foot, belly, texture region
SQUARE_SAILS = [
    ("fore", "fore_course", 18.2, 8.6, 7.6, 8.4, 2.1, "fore_course"),
    ("fore", "fore_topsail", 24.4, 19.8, 5.1, 6.0, 1.4, "fore_topsail"),
    ("main", "main_course", 19.0, 8.0, 8.3, 9.1, 2.3, "main_course"),
    ("main", "main_topsail", 25.6, 20.6, 5.5, 6.4, 1.5, "main_topsail"),
    ("mizzen", "mizzen_course", 17.4, 11.2, 5.4, 6.0, 1.3, "mizzen_course"),
]


def yard_step(mast_name, name):
    z, d = MASTS[mast_name][0], MASTS[mast_name][4]
    if "topsail" in name:
        return z + 0.45, d * 0.66 / 2 + 0.17
    return z, d / 2 + 0.17


def fighting_top(mb, lights, name, z, y, d):
    """A round fighting top on its trestle trees: an octagonal platform, a gold rail on gold stanchions round it, a
    lantern at each of its four corners (044)."""
    r = 1.45 + d * 0.3
    zc = z - 0.1
    for k in range(4):
        a = math.pi / 4 * k
        add_cube(mb, "%s_top_%d" % (name, k), (0, y + 0.06, zc), ry(a), (2 * r, 0.16 - 0.01 * k, 2 * r * math.tan(math.pi / 8)),
                 {"all": "dark_wood", "+2": "deck"})
    for sx in (1, -1):
        beam(mb, "%s_trestle_%d" % (name, sx > 0), (sx * d * 0.45, y - 0.14, zc - r), (sx * d * 0.45, y - 0.14, zc + r), 0.2, "wood_dark",
             width=0.16)
        beam(mb, "%s_crosstree_%d" % (name, sx > 0), (-r, y - 0.08, zc + sx * 0.5), (r, y - 0.08, zc + sx * 0.5), 0.14, "wood_dark", width=0.14)
    ring = []
    for k in range(8):
        a = math.pi / 8 + math.pi / 4 * k
        ring.append(v3(math.cos(a) * r * 0.98, 0, zc + math.sin(a) * r * 0.98))
    for k, (a, b) in enumerate(polyline(ring, closed=True)):
        beam(mb, "%s_top_rim_%d" % (name, k), a + v3(0, y + 0.22, 0), b + v3(0, y + 0.22, 0), 0.18, "gold", width=0.12, extend=0.05)
        beam(mb, "%s_top_rail_%d" % (name, k), a + v3(0, y + 0.95, 0), b + v3(0, y + 0.95, 0), 0.12, "rail", width=0.14, extend=0.05)
        add_cube(mb, "%s_top_stanchion_%d" % (name, k), a + v3(0, y + 0.6, 0), EYE, (0.1, 0.7, 0.1), "gold")
    for k in range(4):
        a = math.pi / 4 + math.pi / 2 * k
        p = v3(math.cos(a) * r * 0.98, y + 1.0, zc + math.sin(a) * r * 0.98)
        lantern(lights, "lantern_top_%s%d" % (name, k), p, hang=False, s=0.9)


def mast(root, fittings, lights, name):
    z, top1, top2, head, d = MASTS[name]
    foot = MAST_FOOT[name]
    deck = Q if name == "mizzen" else M
    mb = Bone("mast_" + name, origin=(0, deck, z), parent=root)
    if foot < deck:
        round_bar(fittings, "lit_mast_%s_below" % name, (0, foot, z), (0, deck, z), d + 0.05, "mast")
        disc(fittings, "lit_mast_%s_collar" % name, (0, L + 0.15, z), (0, 1, 0), d / 2 + 0.16, 0.3, "wood_dark", n=3)
    round_bar(mb, name + "_lower", (0, deck - 0.1, z), (0, top1 + 1.0, z), d, "mast")
    disc(mb, name + "_partners", (0, deck + 0.12, z), (0, 1, 0), d / 2 + 0.22, 0.24, "wood_dark", n=3)
    for k, y in enumerate(np.arange(deck + 1.8, top1 - 0.6, 2.0)):
        round_bar(mb, "%s_band_%d" % (name, k), (0, y - 0.1, z), (0, y + 0.1, z), d + 0.08, "gold")
    fighting_top(mb, lights, name, z, top1, d)
    add_cube(mb, name + "_cap", (0, top1 + 1.05, z + 0.2), EYE, (d + 0.2, 0.3, 1.4), "gold")
    if top2 is not None:
        d2 = d * 0.66
        round_bar(mb, name + "_topmast", (0, top1 - 0.5, z + 0.45), (0, head, z + 0.45), d2, "mast")
        for k, y in enumerate((top1 + 2.6, top1 + 5.2)):
            round_bar(mb, "%s_topmast_band_%d" % (name, k), (0, y - 0.07, z + 0.45), (0, y + 0.07, z + 0.45), d2 + 0.06, "gold")
        s2 = 1.0
        for sx in (1, -1):
            beam(mb, "%s_crosstree2_%d" % (name, sx > 0), (-s2, top2, z + 0.45 + sx * 0.3), (s2, top2, z + 0.45 + sx * 0.3), 0.12, "wood_dark",
                 width=0.12)
        disc(mb, name + "_truck", (0, head + 0.05, z + 0.45), (0, 1, 0), 0.22, 0.16, "gold", n=3)
        mz = z + 0.45
    else:
        round_bar(mb, name + "_topmast", (0, top1 - 0.5, z + 0.4), (0, head, z + 0.4), d * 0.62, "mast")
        disc(mb, name + "_truck", (0, head + 0.05, z + 0.4), (0, 1, 0), 0.2, 0.14, "gold", n=3)
        mz = z + 0.4
    return mb, mz


def square_sail(mb, sails_info, name, z, y_top, y_foot, half_top, half_foot, belly, region, off=0.42):
    """Yard (braced round with its sail) and the sail billowed forward."""
    br = Bone("brace_" + name, origin=(0, y_top, z), parent=mb)
    zz = z + off
    round_bar(br, name + "_yard", (-half_top - 0.5, y_top, zz), (half_top + 0.5, y_top, zz), 0.32, "mast", extend=0.05)
    for k, x in enumerate((-half_top * 0.6, 0.0, half_top * 0.6)):
        round_bar(br, "%s_yard_band_%d" % (name, k), (x - 0.1, y_top, zz), (x + 0.1, y_top, zz), 0.38, "gold")
    add_cube(br, name + "_sling", (0, y_top, zz - 0.1), EYE, (0.42, 0.38, 0.38), "rope")
    for sx in (1, -1):
        add_cube(br, "%s_yardarm_%d" % (name, sx > 0), (sx * (half_top + 0.4), y_top, zz), EYE, (0.14, 0.38, 0.38), "gold")
    beam(br, name + "_roll", (-half_top * 0.94, y_top - 0.24, zz + 0.05), (half_top * 0.94, y_top - 0.24, zz + 0.05), 0.28, "cloth_roll")
    sb = Bone("sail_" + name, origin=(0, y_top, zz), parent=br)
    height = y_top - y_foot
    cols, rows = ft.SAIL_CELLS[region]
    cols, rows = int(cols), int(math.ceil(rows))
    origin = v3(0, y_top - 0.16, zz + 0.05)

    def P(s, t):
        half = half_top + (half_foot - half_top) * t
        x = (2 * s - 1) * half
        bel = belly * math.sin(math.pi * min(1.0, t * 0.78)) * (0.35 + 0.65 * (1 - (2 * s - 1) ** 2))
        drop = t * height * (1 + 0.07 * t * t * (1 - (2 * s - 1) ** 2))
        return origin + v3(x, -drop, bel)
    patch_sail(sb, name, P, v3(0, 0, 1), region, cols, rows)
    sails_info.append((sb, False))
    br.rot = ry(BRACE)
    return br


def tri_sail(bone, name, head, tack, clew, belly, N, region):
    clew = gn.jib_clew(head, tack, clew)
    cols, rows = ft.SAIL_CELLS[region]
    return gn.g_tri_sail(bone, name, head, tack, clew, belly, N, region, int(cols), int(rows), round_=0.45), clew


def stays(bowsprit):
    sa, sb, cap = bowsprit
    d = norm(sb - sa)
    F_, N_, Z_ = MASTS["fore"], MASTS["main"], MASTS["mizzen"]
    fz, mz, zz = F_[0], N_[0], Z_[0]
    return {
        "fore_stay": (v3(0, F_[1] - 0.25, fz + 0.3), sa + d * 3.6 + v3(0, 0.3, 0)),
        "fore_topmast_stay": (v3(0, F_[2] - 0.2, fz + 0.6), cap + v3(0, 0.35, 0)),
        "fore_tg_stay": (v3(0, F_[3] - 1.0, fz + 0.6), sb + v3(0, 0.4, 0)),
        "main_stay": (v3(0, N_[1] - 0.2, mz + 0.45), v3(0, M + 0.25, fz - 2.4)),
        "main_topmast_stay": (v3(0, N_[2] - 0.2, mz + 0.6), v3(0, F_[1] + 0.5, fz - 0.4)),
        "mizzen_stay": (v3(0, Z_[1] - 0.3, zz + 0.3), v3(0, M + 6.5, mz - 0.55)),
        "mizzen_topmast_stay": (v3(0, Z_[3] - 1.0, zz + 0.5), v3(0, N_[1] + 0.6, mz - 0.4)),
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
    st_ = stays(bowsprit)
    jb = Bone("sail_jibs", origin=tuple(cap), parent=root)
    jib_tri, outer_clew = tri_sail(jb, "jib_outer", on(st_["fore_topmast_stay"], 0.22), on(st_["fore_topmast_stay"], 0.92), v3(0, 12.6, 16.0),
                                   1.3, v3(-1, 0, 0), "jib")
    _, inner_clew = tri_sail(jb, "jib_inner", on(st_["fore_stay"], 0.12), on(st_["fore_stay"], 0.9), v3(0, 9.8, 13.9), 1.0, v3(-1, 0, 0), "jib")
    sails_info.append((jb, True))
    return {"jib": jib_tri, "jib_clews": (outer_clew, inner_clew)}


# ---------------------------------------------------------------- rigging
def channel_point(z, side, out=0.48, dy=-0.3):
    if z < CF:
        y = Q + 0.7 + dy
    else:
        y = rail_top(z) + dy
    return hp(z, y, side, out)


def rigging(bone, hull_bone, masts, bowsprit, sails):
    sa, sb, cap = bowsprit
    d = norm(sb - sa)
    for mname, (z, top1, top2, head, dm) in MASTS.items():
        for side, sn in SIDES:
            za, zb = z - (3.6 if mname != 'mizzen' else 2.4), z + 0.4
            if mname == "mizzen":
                za, zb = z - 1.6, z + 1.2
            y0 = (rail_top((za + zb) / 2) if z > CF else Q + 0.7) - 0.3
            pa, pb = hp(za, y0, side, 0.3), hp(zb, y0, side, 0.3)
            beam(hull_bone, "channel_%s_%s" % (mname, sn), pa, pb, 0.14, "wood_dark", width=0.6, extend=0.05)
            for j, zk in enumerate((za + 0.3, zb - 0.3)):
                beam(hull_bone, "channel_knee_%s_%s%d" % (mname, sn, j), hp(zk, y0 - 0.7, side, 0.02), hp(zk, y0 - 0.05, side, 0.5), 0.12,
                     "wood_dark", width=0.12)
            feet, tops = [], []
            nsh = 5 if mname != "mizzen" else 3
            zf = np.linspace(zb - 0.3, za + 0.35, nsh)
            r = 1.45 + dm * 0.3
            for k, zz in enumerate(zf):
                foot = channel_point(zz, side, 0.52, -0.05)
                feet.append(foot + v3(0, 0.36, 0))
                tops.append(v3(side * (dm / 2 + 0.05 + 0.08 * k), top1 - 0.15, z - 0.1 * k))
                disc(bone, "deadeye_%s_%s%d" % (mname, sn, k), foot + v3(0, 0.36, 0), (side, 0, 0), 0.12, 0.08, "dark_wood")
                disc(bone, "deadeye_low_%s_%s%d" % (mname, sn, k), foot, (side, 0, 0), 0.12, 0.08, "dark_wood")
                beam(bone, "lanyard_%s_%s%d" % (mname, sn, k), foot + v3(0, 0.05, 0), foot + v3(0, 0.31, 0), 0.05, "rope")
                beam(bone, "chain_%s_%s%d" % (mname, sn, k), foot - v3(0, 0.06, 0), hp(zz, foot[1] - 1.1, side, 0.04), 0.06, "iron")
            ladder(bone, "%s_lower_%s" % (mname, sn), tops, feet, step=0.55, region="rope_dark", th=0.1)
            for k in range(2):
                beam(bone, "futtock_%s_%s%d" % (mname, sn, k), v3(side * r * 0.9, top1 + 0.05, z - 0.4 - 0.6 * k),
                     v3(side * dm * 0.5, top1 - 1.5, z - 0.1 * k), 0.05, "rope")
            if top2 is None:
                r2 = dm * 0.31
                t2 = [v3(side * (r2 + 0.04), head - 1.4, z + 0.4) for _ in range(2)]
                f2 = [v3(side * (r * 0.9 - 0.1 - 0.4 * k), top1 + 0.3, z - 0.3 - 0.5 * k) for k in range(2)]
                ladder(bone, "%s_top_%s" % (mname, sn), t2, f2, step=0.45, region="rope_dark", th=0.05)
                beam(bone, "%s_backstay_%s" % (mname, sn), v3(side * 0.2, head - 1.0, z + 0.4), channel_point(z - 4.5, side, 0.36, 0.0), 0.05, "rope")
                continue
            r2 = dm * 0.33
            t2 = [v3(side * (r2 + 0.04), top2 - 0.1, z + 0.45) for _ in range(3)]
            f2 = [v3(side * (r * 0.92 - 0.08), top1 + 0.3, z - 0.15 - 0.6 * k) for k in range(3)]
            ladder(bone, "%s_top_%s" % (mname, sn), t2, f2, step=0.45, region="rope_dark", th=0.05)
            beam(bone, "%s_tg_shroud_%s" % (mname, sn), v3(side * 0.22, head - 1.4, z + 0.45), v3(side * 1.0, top2 + 0.05, z + 0.45), 0.05,
                 "rope")
            zb1 = za - (3.8 if mname == "fore" else 2.4)
            ladder(bone, "%s_backstay_%s" % (mname, sn), [v3(side * (r2 + 0.04), top2 + 0.3, z + 0.4), v3(side * (r2 + 0.08), top2 + 0.1, z + 0.3)],
                   [channel_point(zb1, side, 0.36, 0.0), channel_point(zb1 - 0.7, side, 0.36, 0.0)], step=0.5, region="rope_dark", th=0.05)
    ropes = [(name, a, b) for name, (a, b) in stays(bowsprit).items()]
    fz, mz, zz = fs.FORE_MAST_Z, fs.MAIN_MAST_Z, fs.MIZZEN_Z
    ropes += [
        ("bobstay", cap - d * 0.6 + v3(0, -0.15, 0), v3(0, 1.2, BOW_Z + fs.rake(BOW_Z, 1.2) + 0.1)),
        ("martingale", cap + v3(0, -1.65, 0.15), sb + v3(0, 0.25, 0)),
        ("martingale_back", cap + v3(0, -1.65, 0.15), v3(0, 4.2, BOW_Z + fs.rake(BOW_Z, 4.2) + 0.1)),
        ("main_stay_ring", v3(0, M + 0.1, fz - 2.4), v3(0, M + 0.25, fz - 2.4)),
    ]
    outer_clew, inner_clew = sails["jib_clews"]
    for side, sn in SIDES:
        ropes.append(("jib_guy_" + sn, sb + v3(0, 0.3, 0), hp(18.0, rail_top(18.0), side, 0.2)))
        ropes.append(("bowsprit_shroud_" + sn, sa + d * 4.5, hp(19.2, 3.4, side, 0.05)))
        ropes.append(("jib_sheet_outer_" + sn, outer_clew, hp(14.5, rail_top(14.5), side, -0.1)))
        ropes.append(("jib_sheet_inner_" + sn, inner_clew, hp(12.6, rail_top(12.6), side, -0.1)))
        for mname, idx, to in (("fore", 0, v3(side * 0.6, MASTS["main"][1] - 2.0, mz + 0.2)),
                               ("main", 2, v3(side * 0.5, MASTS["mizzen"][1] - 1.5, zz + 0.2)),
                               ("mizzen", 4, hp(-17.5, Q + 1.5, side, -0.25))):
            sq = SQUARE_SAILS[idx]
            off = yard_step(mname, sq[1])[1]
            mzz = MASTS[mname][0]
            arm = gn.braced((side * (sq[4] + 0.3), sq[2], mzz + off), mzz, BRACE)
            ropes.append(("%s_brace_%s" % (mname, sn), arm, to))
        for mname, idx in (("fore", 0), ("main", 2)):
            sq = SQUARE_SAILS[idx]
            off = yard_step(mname, sq[1])[1]
            mzz = MASTS[mname][0]
            clew = gn.braced((side * (sq[5] + 0.1), sq[3] + 0.1, mzz + off + 0.3), mzz, BRACE)
            ropes.append(("%s_sheet_%s" % (mname, sn), clew, hp(mzz - 4.2, rail_top(mzz - 4.2), side, -0.15)))
    for name, a, b in ropes:
        if name in SLACK:
            slack_rope(bone, name, a, b, SLACK[name][0])
        else:
            beam(bone, "rope_" + name, a, b, 0.06, "rope")


SLACK = {
    "fore_brace_p": (0.035, 18), "fore_brace_s": (0.035, 18),
    "main_brace_p": (0.035, 16), "main_brace_s": (0.035, 16),
    "main_topmast_stay": (0.03, 14), "mizzen_topmast_stay": (0.03, 14),
    "jib_guy_p": (0.03, 15), "jib_guy_s": (0.03, 15),
}
gc.SLACK = dict(gc.SLACK, **SLACK)


# ---------------------------------------------------------------- pennants and the royal standard
def pennant(parent, name, root_pt, w, h, region, n=4, fly=(0, 0, -1)):
    """A long swallow-tailed pennant in two bones (the animation swings the root half and the fly), each half in n
    strips following a soft wave; the fly streams aft."""
    root_pt = v3(*root_pt)
    fly = norm(v3(*fly))
    side = np.cross(v3(0, 1, 0), fly)
    fb = Bone("flag_" + name, origin=tuple(root_pt), parent=parent)
    ft_ = Bone("flag_%s_tip" % name, origin=tuple(root_pt + fly * (w / 2)), parent=fb)
    amp = min(0.3, 0.06 * w)

    def P(s):
        return root_pt + side * (amp * math.sin(2 * math.pi * s * 1.3) * (0.3 + s)) + fly * (w * s) + v3(0, -0.25 * s * s * h, 0)
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


def flags(root, masts, castle_bone):
    """Blue and gold swallow-tailed pennants at the three mastheads (the longest at the main), the royal standard
    with the lion on the flagstaff over the stern."""
    for name, w, h, region in (("fore", 7.0, 1.25, "pennant"), ("main", 8.0, 1.35, "pennant"), ("mizzen", 5.4, 1.0, "pennant_small")):
        mb, mz = masts[name]
        head = MASTS[name][3]
        top = v3(0, head + 0.1, mz)
        beam(mb, "%s_flagstaff" % name, top, top + v3(0, h + 0.5, 0), 0.09, "wood_dark")
        disc(mb, "%s_flagstaff_knob" % name, top + v3(0, h + 0.55, 0), (0, 1, 0), 0.09, 0.12, "gold")
        pennant(mb, name, top + v3(0, h + 0.42, 0), w, h, region)
    # the royal standard on the stern flagstaff, over the roof's lantern turret (the stern pole of 071)
    top = v3(0, RH1 + 1.1 + 3.0, TZ + 1.15)
    beam(castle_bone, "stern_flagstaff", v3(0, RH1 + 1.1, TZ + 1.15), top + v3(0, 1.9, 0), 0.12, "wood_dark")
    disc(castle_bone, "stern_flagstaff_knob", top + v3(0, 1.95, 0), (0, 1, 0), 0.12, 0.14, "gold")
    pennant(castle_bone, "stern", top + v3(0, 1.85, 0), 2.4, 1.6, "flag_lion", n=3)


# ---------------------------------------------------------------- helm, rudder
def helm(bone):
    hz = fs.HELM_Z
    hub = v3(0, Q + 1.05, hz)
    disc(bone, "helm_pedestal_base", (0, Q + 0.06, hz + 0.1), (0, 1, 0), 0.32, 0.12, "wood_dark", n=3)
    turned(bone, "helm_pedestal", (0, Q + 0.1, hz + 0.1), (0, hub[1] + 0.1, hz + 0.1), [(0, 0.36), (0.12, 0.26), (0.5, 0.3), (0.9, 0.3), (1, 0)],
           "wood_dark")
    round_bar(bone, "helm_axle", (0, hub[1], hz + 0.2), (0, hub[1], hz - 0.14), 0.1, "iron")
    wheel = Bone("helm_wheel", origin=tuple(hub), parent=bone)
    r = 0.68
    zax = v3(0, 0, 1)
    disc(wheel, "helm_hub", hub, zax, 0.14, 0.22, "gold", n=3)
    for k in range(8):
        a = 2 * math.pi * k / 8
        dv = v3(math.cos(a), math.sin(a), 0)
        round_bar(wheel, "helm_spoke_%d" % k, hub + dv * 0.1, hub + dv * r, 0.07, "wood_mid")
        turned(wheel, "helm_handle_%d" % k, hub + dv * (r + 0.04), hub + dv * (r + 0.3), [(0, 0.07), (0.3, 0.1), (0.7, 0.07), (1, 0)], "gold")
    for k in range(16):
        a, a2 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
        p0, p1 = hub + v3(math.cos(a), math.sin(a), 0) * r, hub + v3(math.cos(a2), math.sin(a2), 0) * r
        beam(wheel, "helm_rim_%d" % k, p0, p1, 0.1, "wood_dark", width=0.1, up=zax, extend=0.02)
    bn = v3(1.1, Q, hz + 0.3)
    disc(bone, "binnacle", bn + v3(0, 0.45, 0), (0, 1, 0), 0.24, 0.9, "wood_mid")
    disc(bone, "binnacle_top", bn + v3(0, 0.93, 0), (0, 1, 0), 0.26, 0.06, "gold")
    disc(bone, "binnacle_card", bn + v3(0, 0.97, 0), (0, 1, 0), 0.17, 0.02, {"all": "gold", "+2": "compass"})


def rudder(root):
    piv = v3(0, 0.0, TZ - 0.15)
    rb = Bone("rudder", origin=tuple(piv), parent=root)
    zf = TZ - 0.18
    y_top, y_bot = fs.sheer_y(TZ) - 0.8, fs.keel_y(TZ) - 0.05
    bands = list(np.linspace(y_top, y_bot, 7))

    def back(y):
        t = (y_top - y) / (y_top - y_bot)
        return zf - 0.7 - 0.7 * t ** 0.8
    for k in range(len(bands) - 1):
        y0, y1 = bands[k], bands[k + 1]
        board(rb, "rudder_blade_%d" % k, v3(0.2, y0, zf), v3(0.2, y0, back(y0)), v3(0.2, y1, zf), v3(0.2, y1, back(y1)), 0.4, "wood_dark",
              v3(1, 0, 0), overlap=1.0)
    for k, y in enumerate(np.linspace(y_top - 0.4, y_bot + 0.4, 4)):
        for s in (1, -1):
            add_cube(rb, "rudder_strap_%d_%d" % (k, s > 0), (s * 0.215, y, (zf + back(y)) / 2 + 0.05), EYE, (0.03, 0.16, abs(back(y) - zf)), "gold")
        disc(rb, "rudder_gudgeon_%d" % k, (0, y, zf - 0.08), (0, 1, 0), 0.25, 0.16, "gold", n=3)
    round_bar(rb, "rudder_stock", (0, y_bot, zf - 0.08), (0, fs.sheer_y(TZ) - 0.3, zf - 0.08), 0.26, "wood_dark")


# ---------------------------------------------------------------- deck fittings
def deck_fittings(bone, detail):
    grating(bone, "grating_main", 0.0, 2.4, 2.0, 2.0, M)
    grating(bone, "grating_fore", 0.0, 15.6, 1.6, 1.6, F)
    gn.g_capstan(bone, "capstan", (0, M, 6.0))
    disc(bone, "main_stay_eyebolt", (0, M + 0.04, fs.FORE_MAST_Z - 2.4), (0, 1, 0), 0.16, 0.08, "iron")
    for k, (xr, zr) in enumerate(((fs.CREW_STAIR_X, fs.CREW_STAIR_Z), (fs.HOLD_STAIR_X, fs.HOLD_STAIR_Z))):
        x0, x1 = xr
        z0, z1 = zr
        for j, (a, b) in enumerate(((v3(x0, M, z0), v3(x0, M, z1)), (v3(x1, M, z0), v3(x1, M, z1)), (v3(x0, M, z0), v3(x1, M, z0)))):
            beam(bone, "companion_coaming_%d_%d" % (k, j), a + v3(0, 0.1, 0), b + v3(0, 0.1, 0), 0.2, "wood_dark", width=0.14, extend=0.07)
        for j, (x, z) in enumerate(((x0, z0), (x1, z0), (x0, z1 - 0.1), (x1, z1 - 0.1))):
            add_cube(bone, "companion_post_%d_%d" % (k, j), (x, M + 0.5, z), EYE, (0.12, 1.0, 0.12), "gold")
        beam(bone, "companion_rail_%d_0" % k, (x0, M + 0.95, z0), (x1, M + 0.95, z0), 0.09, "rail", extend=0.05)
        for j, x in enumerate((x0, x1)):
            beam(bone, "companion_rail_%d_%d" % (k, j + 1), (x, M + 0.95, z0), (x, M + 0.95, z1 - 0.1), 0.09, "rail", extend=0.05)
    sd.bell(gg, bone, "bell", (0.0, F, FCZ + 1.0), metal="bronze", wood="wood_dark")
    for z in (fs.FORE_MAST_Z, fs.MAIN_MAST_Z):
        sd.fife_rail(gg, detail, "fife_%d" % int(z + 20), 0.0, z - 1.0, M, half=0.95, wood="wood_dark", pin="gold", rope="rope")


# ---------------------------------------------------------------- the rooms, on the interior grid
MAX_TILE = 8
WOOD_ROOM = ("wall_wood", "floor", "ceil")
ROOM_MATERIALS = {"cabin": WOOD_ROOM, "stateroom": WOOD_ROOM, "crew": ("hold_wall", "hold_floor", "ceil"), "hold": ("hold_wall", "hold_floor", "ceil")}


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
        along_z = sx < sz
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


CUSTOM_BUILDERS = dict(gc.CUSTOM_BUILDERS)


# ---------------------------------------------------------------- the model
def build(g):
    root = Bone(ID)
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
    waist(hull_bone, detail, lights)
    hull_ornaments(detail, lights)
    decks(deck_bone, castle_bone)
    forecastle(hull_bone, deck_bone)
    castle(castle_bone, lights)
    roundhouse(castle_bone, lights)
    bowsprit = bow(bow_bone, lights)
    masts = {name: mast(root, fittings, lights, name) for name in MASTS}
    sails_info = []
    sails = sails_and_spars(root, masts, sails_info, bowsprit)
    rigging(ropes, hull_bone, masts, bowsprit, sails)
    flags(root, masts, castle_bone)
    helm(castle_bone)
    rudder(root)
    deck_fittings(deck_bone, detail)
    m = surfaces(rooms, g)
    beams_below(fittings)
    for builder, kwargs, solid in fd.CUSTOM:
        CUSTOM_BUILDERS[builder](furniture, **dict(kwargs))
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
    for k, name in enumerate(("fore", "main", "mizzen", "stern")):
        f, ft_ = find(root, "flag_" + name), find(root, "flag_%s_tip" % name)
        w, sh = 2 * math.pi / 1.2, 0.2 * k
        tracks.append((f, loop_kfs(lambda t, sh=sh: (0, 9 * math.cos(w * (t - sh)), 0), 1.2)))
        tracks.append((ft_, loop_kfs(lambda t, sh=sh: (0, -16 * math.cos(w * (t - sh) - 1.75), 0), 1.2)))
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
    paths = [os.path.join(tex_dir, "entity/%s.png" % ID), os.path.join(tex_dir, "entity/%s_sails.png" % ID)]
    ft.make_texture(paths[0])
    ft.make_sail_texture(paths[1], {"jib": sails["jib"]})
    ft.make_item_icon(os.path.join(tex_dir, "item/%s.png" % ID))
    textures = []
    for k, (p, size_) in enumerate(zip(paths, (ft.SIZE, ft.SAIL_SIZE))):
        with open(p, "rb") as f:
            png = f.read()
        t = gn.texture_entry(os.path.basename(p), size_, png, "entity", ID + ".png")
        t["id"] = str(k)
        textures.append(t)
    model = gn.export(root, anims, textures, [
        os.path.join(ROOT, "blockbench/%s.bbmodel" % ID),
        os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/%s.bbmodel" % ID),
    ], name=ID, visible_box=(60, 44, 0))
    print("grid bytes:", size, "hull boards:", n, "grid surfaces:", m, "cubes:", len(model["elements"]),
          "animations:", [a["name"] for a in model["animations"]])


if __name__ == "__main__":
    main()
