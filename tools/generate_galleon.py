#!/usr/bin/env python3
"""Generates the great galleon Blockbench model (.bbmodel), its textures and
its animations.

Usage:  python3 tools/generate_galleon.py

Outputs:
  blockbench/galleon.bbmodel                                     (editable in Blockbench, textures embedded)
  src/main/resources/assets/medievalships/models/entity/galleon.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/galleon.png
  src/main/resources/assets/medievalships/textures/entity/galleon_flag.png   (flags: emblem, texture #1)
  src/main/resources/assets/medievalships/textures/item/galleon.png

Same conventions and helpers as tools/generate_galley.py. The shape and the layout
come from tools/galleon_shape.py, identical to the Java collision code.

Bones used by the mod (keep their names when editing in Blockbench):
  sail_* (wind, furl)  jib  helm_wheel, rudder (steer)  flag_*, flag_*_tip, pennant_* (flag_wave)
  gunport_<l|r><n> (lid, closed/open later), cannon_<l|r><n> (empty: future cannons)
"""
import base64
import math
import os
import sys
import uuid
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import galleon_shape as gs  # noqa: E402
import ship_details as sd  # noqa: E402
import generate_galley as gg  # noqa: E402
from galleon_texture import FLAG_SIZE, REGIONS, SIZE, make_item_icon, make_textures  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/galleon/%d" % _uuid_counter[0]))


gg.new_uuid = new_uuid  # bones and cubes created through the galley helpers get galleon ids

v3, norm, Bone, add_cube, beam, board = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam, gg.board
rx, ry, rz = gg.rx, gg.ry, gg.rz
EYE = np.eye(3)
SIDES = ((1, "p"), (-1, "s"))
BRACE = math.radians(22)  # square yards braced round (port arms aft)


def braced(p, mast_z, a=BRACE):
    """Point of a braced yard or sail, given where it would be with the yard square."""
    o = v3(0, 0, mast_z)
    return ry(a) @ (v3(*p) - o) + o

# hull stations (dense where the shape changes fast); the visual bow closes beyond the
# collision hull end (17.5), where the half width reaches zero
STATIONS = [-17.5, -16.6, -15.6, -14.4, -13.0, -11.5, -10.0, -8.5, -7.0, -5.4, -3.7, -2.0, -0.3, 1.4,
            3.1, 4.8, 6.4, 8.0, 9.4, 10.5, 11.7, 12.8, 13.9, 14.9, 15.8, 16.6, 17.2, 17.6, 17.9]


def hw(z):
    return gs.half_width(z)


def section(z, side):
    """Outer hull cross-section (one side), from the keel to the sheer."""
    w, yk, ys = hw(z), gs.keel_y(z), gs.sheer_y(z)
    pts = [(0.08, yk)]
    for fx, fy in gs.BOTTOM_SECTION[1:]:
        pts.append((fx * w, fy * yk))
    pts += [(1.0 * w, 0.45), (0.995 * w, 1.25), (0.985 * w, ys - 0.45), (0.98 * w, ys)]
    return [v3(side * max(x, 0.08), y, z) for x, y in pts]


STRAKES = ["hull_dark", "hull_dark", "hull_mid", "hull_mid", "wood_honey", "wood_honey", "wood_honey"]


def outer_x(z, y):
    """Outer surface of the hull side (above the waterline) at height y."""
    w = hw(z)
    ys = gs.sheer_y(z)
    if y >= ys:
        return 0.98 * w
    if y >= 1.25:
        f = (y - 1.25) / max(0.01, ys - 1.25)
        return w * (0.995 - 0.015 * f)
    return w


def side_frame(z, y, side):
    """Point on the hull side and an outward frame (u along +z, v up, n outward)."""
    dz = 0.05
    p0 = v3(side * outer_x(z - dz, y), y, z - dz)
    p1 = v3(side * outer_x(z + dz, y), y, z + dz)
    u = norm(p1 - p0)
    v = v3(0, 1, 0)
    n = norm(np.cross(v, u)) * side  # outward
    if np.dot(n, v3(side, 0, 0)) < 0:
        n = -n
    return (p0 + p1) / 2, u, v, n


def decal(bone, name, z, y, side, w, h, region, depth=0.04, out=0.01, glow=False, th=None):
    """Thin flat element on the hull side (windows, gun ports, panels...)."""
    p, u, v, n = side_frame(z, y, side)
    th = th if th is not None else depth
    c = p + n * (out + th / 2)
    axes = np.column_stack([u, v, n])
    faces = {"all": region, "+1": region, "-1": region, "+2": region, "-2": region}
    return add_cube(bone, ("glow_" if glow else "") + name, c, axes, (w, h, th), faces, stretch=True,
                    u_dir=u * side * -1 if side > 0 else u, v_dir=v3(0, -1, 0))


def inner_decal(bone, name, z, y, side, w, h, region, wall=0.12, th=0.03):
    """Thin flat element on the inner face of the hull side (window seen from inside, painting...)."""
    p, u, v, n = side_frame(z, y, side)
    c = p - n * (wall + 0.02 + th / 2)
    return add_cube(bone, name, c, np.column_stack([u, v, n]), (w, h, th), {"all": None, "-3": region}, stretch=True,
                    u_dir=u * side, v_dir=v3(0, -1, 0))


def set_sub(cube, sub, faces=("north", "south")):
    for f in faces:
        if cube.faces.get(f):
            cube.faces[f]["sub"] = sub


# ---------------------------------------------------------------- sails
def sail_surface(origin, U, V, N, half_top, half_bottom, height, depth, fx, fy, triangle=False, round_=0.0, foot=0.0):
    """Point of a billowed sail. fx in [-1, 1] across, fy in [0, 1] from the head down.
    The belly only depends on fy: every horizontal strip is then exactly planar and shares its
    edges with its neighbours (no cracks, no overlap, no saw-tooth edges), the head stays on its
    yard / stay and the cloth curves out below it."""
    half = half_top + (half_bottom - half_top) * fy
    belly = depth * math.sin(math.pi * min(1.0, fy * (0.6 if triangle else 0.72)))
    if round_:
        # rounder sail: the belly also grows towards the middle of the width (the head stays on the yard)
        belly *= 1.0 - round_ + round_ * (1.0 - fx * fx)
    # the wind lifts the middle of the foot: the lower edge curves up between the clews
    drop = fy * height * (1.0 - foot * fy * fy * (1.0 - fx * fx))
    return origin + U * (fx * half) + V * drop + N * belly


def sail(bone, name, origin, U, V, N, half_top, half_bottom, height, depth, region, nx=1, ny=8,
         triangle=False, th=0.04, round_=0.0, overlap=0.005, foot=0.0):
    """Square (or triangle-textured) sail made of tilted strips following a curved surface.
    Each strip maps its own part of the texture region, so the cloth (and its emblem) is continuous."""
    U, V, N = norm(U), norm(V), norm(N)
    for i in range(nx):
        for j in range(ny):
            fx0, fx1 = -1 + 2 * i / nx, -1 + 2 * (i + 1) / nx
            fy0, fy1 = j / ny, (j + 1) / ny
            P = lambda a, b: sail_surface(origin, U, V, N, half_top, half_bottom, height, depth, a, b, triangle, round_, foot)  # noqa: E731
            a0, a1, b0, b1 = P(fx0, fy1), P(fx0, fy0), P(fx1, fy1), P(fx1, fy0)
            c = (a0 + a1 + b0 + b1) / 4
            u = ((b0 + b1) - (a0 + a1)) / 2
            L = np.linalg.norm(u)
            u = u / L
            vp = ((a0 - a1) + (b0 - b1)) / 2   # downwards
            H = np.linalg.norm(vp)
            v = norm(vp - np.dot(vp, u) * u)
            n = np.cross(u, v)
            if np.dot(n, N) < 0:
                u, n = -u, -n  # keep a proper rotation (flipping n alone would mirror the strip)
            axes = np.column_stack([u, v, n])
            cube = add_cube(bone, "%s_%d_%d" % (name, i, j), c, axes, (L + overlap, H + overlap, th),
                            {"all": None, "+3": region, "-3": region}, stretch=True, u_dir=U, v_dir=V)
            set_sub(cube, (i / nx, j / ny, (i + 1) / nx, (j + 1) / ny))


JIB_UC = 0.62


def jib_clew(head, tack, clew):
    """Moves the clew along the luff so that it projects at JIB_UC of it: every jib then has the same
    triangle in its texture region (they share it), at the same distance from its luff."""
    head, tack, clew = v3(*head), v3(*tack), v3(*clew)
    U = tack - head
    L = np.linalg.norm(U)
    U = U / L
    Vp = clew - head - np.dot(clew - head, U) * U
    return head + U * L * JIB_UC + Vp


def tri_sail(bone, name, head, tack, clew, depth, N, region, nx=1, ny=7):
    """Triangular sail (lateen, jib): rectangle grid spanning the triangle, transparent outside.
    head-tack = luff (U axis); returns the triangle in [0,1] region coordinates."""
    U = tack - head
    L = np.linalg.norm(U)
    U = U / L
    Vp = clew - head - np.dot(clew - head, U) * U
    H = np.linalg.norm(Vp)
    V = Vp / H
    uc = np.dot(clew - head, U) / L
    origin = head + U * (L / 2)
    sail(bone, name, origin, U, V, N, L / 2, L / 2, H, depth, region, nx=nx, ny=ny, triangle=True)
    return [(0.0, 0.0), (1.0, 0.0), (uc, 1.0)]


# ---------------------------------------------------------------- the galleon
def build():
    root = Bone("galleon")
    hull = Bone("hull", parent=root)
    deck = Bone("deck", parent=root)
    castle_aft = Bone("sterncastle", parent=root)
    castle_fore = Bone("forecastle", parent=root)
    cabin = Bone("cabin", parent=root)
    poop = Bone("poop_house", parent=root)
    bow = Bone("bow", parent=root)
    ropes = Bone("ropes", parent=root)
    lanterns = Bone("lanterns", parent=root)
    guns = Bone("gunports", parent=root)
    main_y, fc_y, qd_y = gs.MAIN_DECK_Y, gs.FORECASTLE_Y, gs.QUARTERDECK_Y

    # ---- hull planking (tilted boards between stations: smooth, rounded hull)
    for side, sn in SIDES:
        for i in range(len(STATIONS) - 1):
            za, zb = STATIONS[i], STATIONS[i + 1]
            A, B = section(za, side), section(zb, side)
            for k, reg in enumerate(STRAKES):
                mid = (A[k] + A[k + 1] + B[k] + B[k + 1]) / 4
                outward = norm(v3(side, -0.7 if k < 3 else 0.0, 0) + v3(0, 0, 0.35 * np.sign(mid[2])))
                board(hull, "hull_%s%d_%d" % (sn, i, k), A[k], A[k + 1], B[k], B[k + 1], 0.12, reg,
                      outward, inner="hull_light" if k >= 4 else None)
            # sheer rail (cap) where there is no castle
            if gs.BULKHEAD_Z - 0.01 <= za and zb <= gs.FORECASTLE_START + 0.01:
                pa = v3(side * 0.98 * hw(za), gs.sheer_y(za) + 0.07, za)
                pb = v3(side * 0.98 * hw(zb), gs.sheer_y(zb) + 0.07, zb)
                beam(hull, "rail_%s%d" % (sn, i), pa, pb, 0.14, "rail", width=0.3, extend=0.06)
                # gold moulding along the hull under the rail
                pa2 = v3(side * (0.99 * hw(za) + 0.02), gs.sheer_y(za) - 0.25, za)
                pb2 = v3(side * (0.99 * hw(zb) + 0.02), gs.sheer_y(zb) - 0.25, zb)
                beam(hull, "moulding_%s%d" % (sn, i), pa2, pb2, 0.08, "wood_trim", width=0.1, extend=0.05)
            # main wale (thick dark band at the waterline)
            pa = v3(side * (hw(za) + 0.04), 0.85, za)
            pb = v3(side * (hw(zb) + 0.04), 0.85, zb)
            if hw(za) > 0.6 and hw(zb) > 0.6:
                beam(hull, "wale_%s%d" % (sn, i), pa, pb, 0.16, "wale", width=0.18, extend=0.05)
                # upper wale under the gun ports
                pa2 = v3(side * (outer_x(za, 1.25) + 0.04), 1.25, za)
                pb2 = v3(side * (outer_x(zb, 1.25) + 0.04), 1.25, zb)
                beam(hull, "wale_up_%s%d" % (sn, i), pa2, pb2, 0.12, "wale", width=0.14, extend=0.05)
    # keel
    for i in range(len(STATIONS) - 1):
        za, zb = STATIONS[i], STATIONS[i + 1]
        beam(hull, "keel_%d" % i, (0, gs.keel_y(za) - 0.06, za), (0, gs.keel_y(zb) - 0.06, zb), 0.25,
             "dark_wood", width=0.35, extend=0.06)

    # ---- transom (flat stern) with the balcony door, gallery windows and carvings
    zt = -gs.HALF_LENGTH
    bands = np.linspace(gs.keel_y(zt), gs.QD_RAIL_Y, 14)
    for k in range(len(bands) - 1):
        y0, y1 = bands[k], bands[k + 1]
        ym = (y0 + y1) / 2
        if ym < 0:
            w = max(0.2, max(abs(p[0]) for p in section(zt, 1) if p[1] <= ym + 0.3))
            w = min(w, hw(zt))
        else:
            w = outer_x(zt, min(ym, gs.sheer_y(zt))) if ym < gs.sheer_y(zt) else 0.98 * hw(zt)
        reg = "hull_dark" if ym < 0.5 else ("wood_honey" if ym < gs.sheer_y(zt) else "wood_honey")
        if main_y < ym < gs.DOOR_TOP:
            for side, sn in SIDES:
                x0, x1 = gs.DOOR_HALF, w
                add_cube(castle_aft, "transom_%d_%s" % (k, sn), (side * (x0 + x1) / 2, ym, zt + 0.1), EYE,
                         (x1 - x0, y1 - y0 + 0.02, 0.2), reg)
        else:
            add_cube(castle_aft, "transom_%d" % k, (0, ym, zt + 0.1), EYE, (2 * w, y1 - y0 + 0.02, 0.2), reg)
    # door frame (gold) and lintel carving
    add_cube(castle_aft, "transom_door_lintel", (0, gs.DOOR_TOP + 0.1, zt - 0.02), EYE, (2 * gs.DOOR_HALF + 0.3, 0.2, 0.1), "gold")
    for side, sn in SIDES:
        add_cube(castle_aft, "transom_door_jamb_" + sn, (side * (gs.DOOR_HALF + 0.07), (main_y + gs.DOOR_TOP) / 2, zt - 0.02),
                 EYE, (0.14, gs.DOOR_TOP - main_y, 0.1), "gold")
        # gallery windows (lit) each side of the door
        for j, x in enumerate((1.3, 1.95)):
            add_cube(castle_aft, "glow_transom_window_%s%d" % (sn, j), (side * x, 2.05, zt - 0.03), EYE, (0.5, 1.0, 0.06),
                     "glow_window", stretch=True)
            add_cube(cabin, "transom_window_in_%s%d" % (sn, j), (side * x, 2.05, gs.TRANSOM_Z + 0.02), EYE, (0.5, 1.0, 0.03),
                     {"all": None, "+3": "window_in"}, stretch=True)
        # upper windows of the poop house level
        add_cube(castle_aft, "transom_upper_window_" + sn, (side * 1.2, 4.05, zt - 0.03), EYE, (0.55, 0.6, 0.06),
                 "window", stretch=True)
    arms = v3(0, 3.98, zt - 0.06)
    add_cube(castle_aft, "arms_frame", arms + v3(0, 0, 0.02), EYE, (1.55, 1.12, 0.08), "gold")
    add_cube(castle_aft, "arms_emblem", arms - v3(0, 0, 0.03), EYE, (1.35, 0.92, 0.04),
             {"all": None, "-3": "flag"}, stretch=True, u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0))
    add_cube(castle_aft, "arms_crown", arms + v3(0, 0.68, -0.02), EYE, (0.6, 0.26, 0.1), "carving", stretch=True)
    for side, sn in SIDES:
        add_cube(castle_aft, "arms_supporter_" + sn, arms + v3(side * 0.95, -0.05, -0.02), EYE, (0.22, 0.95, 0.14), "pilaster", stretch=True)
    add_cube(castle_aft, "transom_cornice", (0, gs.QD_RAIL_Y + 0.08, zt + 0.05), EYE, (2 * 0.98 * hw(zt) + 0.2, 0.16, 0.4), "gold")
    add_cube(castle_aft, "transom_carving", (0, 3.25, zt - 0.04), EYE, (2 * 0.98 * hw(zt), 0.22, 0.08), "carving", stretch=True)
    add_cube(castle_aft, "transom_carving_low", (0, 0.65, zt - 0.04), EYE, (2 * hw(zt) - 0.2, 0.18, 0.08), "carving", stretch=True)

    # ---- stern balcony (gallery), walkable through the door
    bb, bh = gs.BALCONY_BACK, gs.BALCONY_HALF
    add_cube(castle_aft, "balcony_floor", (0, main_y - gs.BALCONY_FLOOR / 2, (bb + zt) / 2), EYE,
             (2 * bh, gs.BALCONY_FLOOR, zt - bb), {"all": "dark_wood", "+2": "deck"})
    rail_top = main_y + gs.BALCONY_RAIL
    beam(castle_aft, "balcony_rail_back", (-bh, rail_top - 0.05, bb + 0.06), (bh, rail_top - 0.05, bb + 0.06), 0.1, "gold",
         width=0.14, extend=0.05)
    for side, sn in SIDES:
        beam(castle_aft, "balcony_rail_" + sn, (side * (bh - 0.06), rail_top - 0.05, bb), (side * (bh - 0.06), rail_top - 0.05, zt),
             0.1, "gold", width=0.14)
    for j, x in enumerate(np.linspace(-bh + 0.06, bh - 0.06, 9)):
        beam(castle_aft, "balcony_baluster_%d" % j, (x, main_y, bb + 0.06), (x, rail_top - 0.1, bb + 0.06), 0.09, "hull_light")
    for side, sn in SIDES:
        for j, z in enumerate((bb + 0.4, (bb + zt) / 2 + 0.1)):
            beam(castle_aft, "balcony_baluster_%s%d" % (sn, j), (side * (bh - 0.06), main_y, z),
                 (side * (bh - 0.06), rail_top - 0.1, z), 0.09, "hull_light")
        # brackets under the floor
        beam(castle_aft, "balcony_bracket_" + sn, (side * (bh - 0.3), -0.3, zt), (side * (bh - 0.3), main_y - 0.25, bb + 0.2),
             0.14, "dark_wood")

    # ---- castle bulwarks (above the sheer), red with gold caps and panels
    def bulwark(bone, tag, z0, z1, top_y):
        zs = [z for z in STATIONS if z0 < z < z1]
        zs = [z0] + zs + [z1]
        for side, sn in SIDES:
            for i in range(len(zs) - 1):
                za, zb = zs[i], zs[i + 1]
                xa, xb = side * 0.98 * hw(za), side * 0.98 * hw(zb)
                a0, a1 = v3(xa, gs.sheer_y(za) - 0.05, za), v3(xa, top_y, za)
                b0, b1 = v3(xb, gs.sheer_y(zb) - 0.05, zb), v3(xb, top_y, zb)
                board(bone, "%s_wall_%s%d" % (tag, sn, i), a0, a1, b0, b1, 0.12, "wood_honey", v3(side, 0, 0),
                      inner="hull_light")
                beam(bone, "%s_cap_%s%d" % (tag, sn, i), (xa, top_y + 0.07, za), (xb, top_y + 0.07, zb), 0.14, "wood_trim",
                     width=0.3, extend=0.06)
                beam(bone, "%s_band_%s%d" % (tag, sn, i), (xa + side * 0.07, top_y - 0.35, za), (xb + side * 0.07, top_y - 0.35, zb),
                     0.08, "wood_trim", width=0.08, extend=0.04)

    bulwark(castle_aft, "qd", -gs.HALF_LENGTH, gs.BULKHEAD_Z, gs.QD_RAIL_Y)
    bulwark(castle_fore, "fc", gs.FORECASTLE_START, 17.9, gs.FC_RAIL_Y)
    # stern castle side decoration: painted panels and lit cabin windows
    for side, sn in SIDES:
        for j, z in enumerate((-16.0, -14.4, -12.8, -11.2, -9.6)):
            decal(castle_aft, "qd_window_%s%d" % (sn, j), z, gs.QD_RAIL_Y - 0.5, side, 0.55, 0.5, "glow_window", glow=True)
            decal(castle_aft, "qd_post_%s%d" % (sn, j), z + 0.8, gs.QD_RAIL_Y - 0.5, side, 0.12, 0.9, "dark_wood", out=0.02)
        for j, z in enumerate((-15.4, -13.0, -10.6)):
            decal(cabin, "cabin_window_%s%d" % (sn, j), z, 2.2, side, 0.6, 0.75, "glow_window", glow=True)
            inner_decal(cabin, "cabin_window_in_%s%d" % (sn, j), z, 2.2, side, 0.6, 0.75, "window_in")
        for j, z in enumerate((11.6, 13.4, 15.2)):
            decal(castle_fore, "fc_window_%s%d" % (sn, j), z, gs.FC_RAIL_Y - 0.5, side, 0.5, 0.45, "glow_window", glow=True)
        # quarter gallery: a closed balcony with lit windows on each stern corner
        qz0, qz1 = -16.95, -14.25
        qx = 0.98 * hw(-15.6)
        gal = v3(side * (qx + 0.22), 2.55, (qz0 + qz1) / 2)
        add_cube(castle_aft, "quarter_gallery_" + sn, gal, EYE, (0.5, 1.9, qz1 - qz0), {"all": "wood_honey", "+2": "dark_wood"})
        for j, z in enumerate((qz0 + 0.65, qz1 - 0.65)):
            add_cube(castle_aft, "glow_quarter_window_%s%d" % (sn, j), (side * (qx + 0.48), 2.6, z), EYE, (0.04, 1.05, 0.62),
                     "arch_window", stretch=True)
        add_cube(castle_aft, "quarter_gallery_cornice_" + sn, gal + v3(side * 0.03, 1.0, 0), EYE, (0.6, 0.14, qz1 - qz0 + 0.12), "wood_trim")
        add_cube(castle_aft, "quarter_gallery_sill_" + sn, gal + v3(side * 0.03, -0.98, 0), EYE, (0.6, 0.12, qz1 - qz0 + 0.12), "wood_trim")
        board(castle_aft, "quarter_gallery_roof_" + sn, v3(side * (qx + 0.55), 3.55, qz0 - 0.05), v3(side * (qx - 0.05), 4.05, qz0 - 0.05),
              v3(side * (qx + 0.55), 3.55, qz1 + 0.05), v3(side * (qx - 0.05), 4.05, qz1 + 0.05), 0.1, "roof", v3(side, 1, 0), overlap=1.0)
        beam(castle_aft, "quarter_gallery_bracket_" + sn, (side * (qx - 0.05), 0.8, (qz0 + qz1) / 2), (side * (qx + 0.4), 1.6, (qz0 + qz1) / 2),
             0.2, "carving", width=0.5)
        # chain-wales (channels) carrying the deadeyes of the shrouds, with their chains
        for tag, z0, z1, ys in (("main", -1.0, 2.8, None), ("fore", 11.0, 13.4, None), ("mizzen", -13.6, -11.6, None)):
            zm = (z0 + z1) / 2
            y = gs.rail_y(zm) - 0.22
            beam(hull, "channel_%s_%s" % (tag, sn), (side * (0.98 * hw(z0) + 0.16), y, z0), (side * (0.98 * hw(z1) + 0.16), y, z1),
                 0.1, "dark_wood", width=0.36, up=v3(0, 0, 1) if False else v3(0, 1, 0))

    # ---- decks
    def deck_span(bone, z0, z1, n, y, tag, under="dark_wood"):
        for j in range(n):
            za = z0 + (z1 - z0) * j / n
            zb = z0 + (z1 - z0) * (j + 1) / n
            w = max(gs.inner_half_width(za), gs.inner_half_width(zb)) + 0.1
            add_cube(bone, "deck_%s%d" % (tag, j), (0, y - 0.075, (za + zb) / 2), EYE, (2 * w, 0.15, zb - za + 0.02),
                     {"all": "deck", "-2": under})

    deck_span(deck, gs.TRANSOM_Z, gs.FORECASTLE_START, 14, main_y, "main")
    deck_span(castle_fore, gs.FORECASTLE_START, gs.DECK_MAX_Z, 4, fc_y, "fore")
    deck_span(castle_aft, gs.TRANSOM_Z, gs.BULKHEAD_Z, 6, qd_y, "quarter")
    # forecastle front wall (with a carved door) and quarterdeck bulkhead (real door to the cabin)
    wf = gs.inner_half_width(gs.FORECASTLE_START) + 0.12
    add_cube(castle_fore, "fc_front", (0, (main_y + fc_y) / 2, gs.FORECASTLE_START), EYE, (2 * wf, fc_y - main_y, 0.16),
             {"all": "wood_honey", "+3": "hull_light"})
    add_cube(castle_fore, "fc_front_door", (0, main_y + 0.8, gs.FORECASTLE_START - 0.09), EYE, (0.8, 1.55, 0.04), "door", stretch=True)
    for side, sn in SIDES:
        add_cube(castle_fore, "fc_front_window_" + sn, (side * 1.1, main_y + 1.3, gs.FORECASTLE_START - 0.09), EYE,
                 (0.45, 0.45, 0.04), "window", stretch=True)
    bz0, bz1 = gs.BULKHEAD_Z - gs.BULKHEAD_THICK, gs.BULKHEAD_Z
    bw = gs.inner_half_width(bz0) + 0.12
    slab_bottom = qd_y - gs.QUARTERDECK_SLAB
    for side, sn in SIDES:
        x0, x1 = gs.DOOR_HALF, bw
        add_cube(cabin, "bulkhead_" + sn, (side * (x0 + x1) / 2, (main_y + slab_bottom) / 2, (bz0 + bz1) / 2), EYE,
                 (x1 - x0, slab_bottom - main_y, bz1 - bz0), {"all": "wood_honey", "-3": "hull_light"})
        add_cube(cabin, "bulkhead_jamb_" + sn, (side * (gs.DOOR_HALF + 0.07), (main_y + gs.DOOR_TOP) / 2, bz1 + 0.02), EYE,
                 (0.14, gs.DOOR_TOP - main_y, 0.08), "gold")
        add_cube(cabin, "bulkhead_window_" + sn, (side * 2.0, 2.15, bz1 + 0.02), EYE, (0.6, 0.7, 0.05), "window", stretch=True)
        add_cube(cabin, "bulkhead_window_in_" + sn, (side * 2.0, 2.15, bz0 - 0.02), EYE, (0.6, 0.7, 0.03),
                 {"all": None, "-3": "window_in"}, stretch=True)
        add_cube(cabin, "bulkhead_pillar_" + sn, (side * 3.0, (main_y + slab_bottom) / 2, bz1 + 0.06), EYE,
                 (0.18, slab_bottom - main_y, 0.12), "gold")
    add_cube(cabin, "bulkhead_lintel", (0, (gs.DOOR_TOP + slab_bottom) / 2, (bz0 + bz1) / 2), EYE,
             (2 * gs.DOOR_HALF, slab_bottom - gs.DOOR_TOP, bz1 - bz0), "wood_honey")
    add_cube(cabin, "bulkhead_door_arch", (0, gs.DOOR_TOP + 0.06, bz1 + 0.03), EYE, (2 * gs.DOOR_HALF + 0.3, 0.12, 0.1), "gold")
    # slab edge (front of the quarterdeck)
    add_cube(castle_aft, "quarterdeck_edge", (0, qd_y - 0.15, bz1 + 0.02), EYE, (2 * bw, 0.3, 0.06), "carving", stretch=True)

    # ---- great cabin interior: chairs (seats), lanterns, chest, table against the side
    for side, sn in SIDES:
        x, z = side * 2.2, -13.0
        add_cube(cabin, "chair_seat_" + sn, (x, main_y + 0.42, z), EYE, (0.55, 0.08, 0.55), "hull_light")
        add_cube(cabin, "chair_back_" + sn, (x + side * 0.24, main_y + 0.8, z), EYE, (0.08, 0.75, 0.55), "wood_honey")
        for dx in (-0.22, 0.22):
            for dz in (-0.22, 0.22):
                add_cube(cabin, "chair_leg_%s%d%d" % (sn, int(dx > 0), int(dz > 0)), (x + dx, main_y + 0.19, z + dz), EYE,
                         (0.07, 0.38, 0.07), "dark_wood")
        add_cube(lanterns, "cabin_lantern_" + sn, (side * 1.6, 2.5, bz0 - 0.18), EYE, (0.3, 0.42, 0.3),
                 {"all": "lantern", "+2": "iron", "-2": "iron"}, stretch=True)
        add_cube(lanterns, "glow_cabin_lantern_" + sn, (side * 1.6, 2.5, bz0 - 0.18), EYE, (0.2, 0.3, 0.2), "glow", stretch=True)
    add_cube(cabin, "cabin_chest", (2.6, main_y + 0.3, -16.3), EYE, (0.9, 0.6, 0.55), {"all": "dark_wood", "+2": "iron"})
    add_cube(cabin, "cabin_ceiling_beam", (0, slab_bottom - 0.1, -12.0), EYE, (2 * 3.7, 0.2, 0.25), "dark_wood")
    add_cube(cabin, "cabin_ceiling_beam2", (0, slab_bottom - 0.1, -15.0), EYE, (2 * 3.1, 0.2, 0.25), "dark_wood")
    # furnishing: carpet, chart table and dining table by the two chairs, bunk, bookshelf,
    # weapon rack, globe, paintings between the windows, lanterns hanging from the beams
    sd.rug(gg, cabin, "cabin_rug", (0, main_y, -13.8), 1.9, 4.6)
    for side, sn in SIDES:
        sd.table(gg, cabin, "cabin_table_" + sn, (side * 1.35, main_y, -13.0), 0.7, 0.95, h=0.75)
        sd.hanging_lantern(gg, lanterns, "cabin_hanging_lantern_" + sn, (side * 1.3, slab_bottom - 0.2, -15.0), drop=0.2)
        p, u, v, n = side_frame(-11.8, 2.3, side)
        sd.painting(gg, cabin, "cabin_painting_" + sn, p - n * 0.14, -n, w=0.75, h=0.55)
    top = main_y + 0.75
    sd.chart_on_table(gg, cabin, "cabin_chart", (1.35, top, -13.1), yaw=math.pi / 2)
    sd.candle(gg, cabin, "cabin_candle_p", (1.45, top, -12.68))
    sd.tableware(gg, cabin, "cabin_dinner", (-1.35, top, -13.0), yaw=math.pi / 2)
    sd.candle(gg, cabin, "cabin_candle_s", (-1.4, top, -13.4))
    sd.bunk(gg, cabin, "cabin_bunk", (-2.0, main_y, -15.3), l=1.8, w=0.85)
    sd.globe(gg, cabin, "cabin_globe", (2.6, main_y + 0.6, -16.3))
    sd.bookshelf(gg, cabin, "cabin_books", (3.1, main_y, bz0 - 0.19), yaw=math.pi, w=1.0, h=1.9)
    sd.weapon_rack(gg, cabin, "cabin_arms", (-3.1, main_y, bz0), (0, 0, -1), w=1.0)

    # ---- stairs (match the collision boxes) and guard rails
    d = gs.STEP_DEPTH
    for k in range(1, 6):
        top = main_y + (qd_y - main_y) * k / 5.0
        z_front = gs.QD_STAIR_START - (k - 1) * d
        for side, sn in SIDES:
            add_cube(deck, "qd_step_%s%d" % (sn, k), (side * (gs.STAIR_X0 + gs.STAIR_X1) / 2, (main_y + top) / 2, z_front - d / 2),
                     EYE, (gs.STAIR_X1 - gs.STAIR_X0, top - main_y, d), {"all": "dark_wood", "+2": "deck"})
    for k in range(1, 5):
        top = main_y + (fc_y - main_y) * k / 4.0
        z_back = gs.FC_STAIR_START + (k - 1) * d
        for side, sn in SIDES:
            add_cube(deck, "fc_step_%s%d" % (sn, k), (side * (gs.FC_STAIR_X0 + gs.FC_STAIR_X1) / 2, (main_y + top) / 2, z_back + d / 2),
                     EYE, (gs.FC_STAIR_X1 - gs.FC_STAIR_X0, top - main_y, d), {"all": "dark_wood", "+2": "deck"})
    for side, sn in SIDES:
        # stair hand rails (inner side)
        beam(deck, "qd_handrail_" + sn, (side * gs.STAIR_X0, main_y + 0.9, gs.QD_STAIR_START), (side * gs.STAIR_X0, qd_y + 0.9, gs.BULKHEAD_Z),
             0.08, "rail")
        beam(deck, "fc_handrail_" + sn, (side * gs.FC_STAIR_X0, main_y + 0.9, gs.FC_STAIR_START),
             (side * gs.FC_STAIR_X0, fc_y + 0.9, gs.FORECASTLE_START), 0.08, "rail")

    def guard_rail(bone, tag, half, y, z):
        beam(bone, tag + "_top", (-half, y + gs.RAIL_HEIGHT - 0.05, z), (half, y + gs.RAIL_HEIGHT - 0.05, z), 0.1, "gold",
             width=gs.RAIL_THICK, extend=0.05)
        for j, x in enumerate(np.linspace(-half, half, 7)):
            beam(bone, "%s_baluster_%d" % (tag, j), (x, y, z), (x, y + gs.RAIL_HEIGHT - 0.1, z), 0.1, "hull_light")

    guard_rail(castle_aft, "qd_rail", gs.STAIR_X0 - 0.1, qd_y, gs.BULKHEAD_Z - gs.RAIL_THICK / 2)
    guard_rail(castle_fore, "fc_rail", gs.FC_STAIR_X0 - 0.1, fc_y, gs.FORECASTLE_START + gs.RAIL_THICK / 2)

    # ---- main deck life: benches (seats), hatches, capstan-less coils, barrels
    for k, z in enumerate(gs.BENCH_Z):
        for side, sn in SIDES:
            x = side * 3.1
            add_cube(deck, "bench_%s%d" % (sn, k), (x, main_y + 0.42, z), EYE, (0.5, 0.1, 1.0), {"all": "hull_light", "+2": "rail"})
            for dz in (-0.38, 0.38):
                add_cube(deck, "bench_leg_%s%d_%d" % (sn, k, int(dz > 0)), (x, main_y + 0.19, z + dz), EYE, (0.12, 0.38, 0.12),
                         "dark_wood")
    add_cube(deck, "hatch_main", (0, main_y + 0.04, -1.5), EYE, (1.6, 0.08, 1.6), {"all": "dark_wood", "+2": "grating"})
    add_cube(deck, "hatch_fore", (0, main_y + 0.04, 6.0), EYE, (1.3, 0.08, 1.3), {"all": "dark_wood", "+2": "grating"})
    add_cube(deck, "hatch_aft", (0, main_y + 0.04, -5.0), EYE, (1.3, 0.08, 1.3), {"all": "dark_wood", "+2": "grating"})
    # deck details: pin rails at the mast feet, barrels, crates, coils, bucket, the ship's bell
    sd.fife_rail(gg, deck, "fife_main", 0.0, gs.MAIN_MAST_Z, main_y, half=0.95)
    sd.fife_rail(gg, castle_fore, "fife_fore", 0.0, gs.FORE_MAST_Z, fc_y, half=0.75)
    sd.barrel(gg, deck, "barrel_w0", (3.45, main_y, -3.0))
    sd.lying_barrel(gg, deck, "barrel_w1", (-3.3, main_y, -2.9), yaw=0.3)
    sd.crate(gg, deck, "crate_w0", (-3.25, main_y, 5.5), s=0.6, yaw=0.15)
    sd.crate(gg, deck, "crate_w1", (-3.2, main_y + 0.6, 5.45), s=0.45, yaw=-0.2)
    sd.rope_coil(gg, deck, "coil_main", (1.5, main_y, 3.1))
    sd.rope_coil(gg, deck, "coil_main2", (-1.5, main_y, 0.1))
    sd.rope_coil(gg, castle_fore, "coil_fore", (1.2, fc_y, 14.6), r=0.28)
    sd.bucket(gg, deck, "bucket", (1.2, main_y, -0.2))
    sd.bell(gg, castle_fore, "bell", (0.0, fc_y, 11.0))
    for j, (x, z) in enumerate(((-3.3, 9.3), (3.3, 9.6))):
        add_cube(deck, "barrel_%d" % j, (x * 0.85, main_y + 0.35, z - 0.9), ry(0.5 * j), (0.5, 0.7, 0.5),
                 {"all": "hull_mid", "+2": "end_grain", "-2": "end_grain"})

    # ---- gun ports: frame, lid (bone: can open later), empty cannon bones for a future combat system
    for side, sn in SIDES:
        tag = "l" if side > 0 else "r"
        for k, z in enumerate(gs.GUNPORT_Z):
            decal(guns, "gunport_frame_%s%d" % (tag, k + 1), z, gs.GUNPORT_Y, side, 0.62, 0.58, "gunport", out=0.0)
            p, u, v, n = side_frame(z, gs.GUNPORT_Y + 0.3, side)
            hinge = p + n * 0.05
            lid = Bone("gunport_%s%d" % (tag, k + 1), origin=hinge, parent=guns)
            # open lid: hinged at the top, swung outwards and up
            ang = math.radians(55)
            lid_dir = norm(-v * math.cos(ang) + n * math.sin(ang))
            centre = hinge + lid_dir * 0.29
            axes = np.column_stack([u, np.cross(n, u) * 0 + norm(-lid_dir), norm(np.cross(u, -lid_dir))])
            add_cube(lid, "gunport_lid_%s%d" % (tag, k + 1), centre, axes, (0.6, 0.56, 0.08), "hull_mid")
            Bone("cannon_%s%d" % (tag, k + 1), origin=p - n * 0.6 + v3(0, -0.1, 0), parent=guns)
            # inner side of the bulwark
            pi_ = v3(side * (outer_x(z, gs.GUNPORT_Y) - 0.13), gs.GUNPORT_Y, z)
            add_cube(guns, "gunport_inner_%s%d" % (tag, k + 1), pi_, np.column_stack([u, v, v3(side, 0, 0)]),
                     (0.5, 0.48, 0.02), "gunport", stretch=True)

    # ---- poop house with its red roof
    pf, pb, ph = gs.POOP_FRONT, gs.POOP_BACK, gs.POOP_HALF
    wall_h = gs.POOP_WALL_TOP - qd_y
    for side, sn in SIDES:
        add_cube(poop, "poop_wall_" + sn, (side * (ph - 0.08), qd_y + wall_h / 2, (pf + pb) / 2), EYE, (0.16, wall_h, pf - pb),
                 {"all": "wood_honey", "+1": "wood_honey"})
        for j, z in enumerate((pb + 0.7, pf - 0.7)):
            add_cube(poop, "glow_poop_window_%s%d" % (sn, j), (side * (ph + 0.01), qd_y + 1.45, z), EYE, (0.04, 1.1, 0.62),
                     "arch_window", stretch=True)
        add_cube(poop, "poop_pilaster_" + sn, (side * (ph + 0.02), qd_y + wall_h / 2, (pf + pb) / 2), EYE, (0.08, wall_h, 0.24),
                 "pilaster", stretch=True)
        add_cube(poop, "poop_base_" + sn, (side * (ph + 0.02), qd_y + 0.12, (pf + pb) / 2), EYE, (0.1, 0.24, pf - pb), "dark_wood")
        add_cube(poop, "poop_corner_" + sn, (side * (ph - 0.05), qd_y + wall_h / 2, pf - 0.05), EYE, (0.22, wall_h, 0.22), "dark_wood")
        add_cube(poop, "poop_corner_back_" + sn, (side * (ph - 0.05), qd_y + wall_h / 2, pb + 0.05), EYE, (0.22, wall_h, 0.22), "dark_wood")
        add_cube(poop, "poop_beam_" + sn, (side * (ph + 0.03), qd_y + 2.0, (pf + pb) / 2), EYE, (0.08, 0.16, pf - pb), "dark_wood")
    add_cube(poop, "poop_front", (0, qd_y + wall_h / 2, pf - 0.08), EYE, (2 * ph, wall_h, 0.16), {"all": "wood_honey", "-3": "hull_light"})
    add_cube(poop, "poop_back", (0, qd_y + wall_h / 2, pb + 0.08), EYE, (2 * ph, wall_h, 0.16), "wood_honey")
    add_cube(poop, "poop_door", (0, qd_y + 0.95, pf + 0.01), EYE, (0.9, 1.8, 0.04), "door", stretch=True)
    for side, sn in SIDES:
        add_cube(poop, "glow_poop_front_window_" + sn, (side * 1.7, qd_y + 1.45, pf + 0.01), EYE, (0.62, 1.1, 0.04), "arch_window",
                 stretch=True)
        add_cube(poop, "poop_front_pilaster_" + sn, (side * 0.75, qd_y + wall_h / 2, pf + 0.02), EYE, (0.24, wall_h, 0.06),
                 "pilaster", stretch=True)
    add_cube(poop, "poop_cornice", (0, gs.POOP_WALL_TOP + 0.06, (pf + pb) / 2), EYE, (2 * ph + 0.2, 0.14, pf - pb + 0.2), "wood_trim")
    # roof: two tile slopes meeting at the ridge, with overhang, plus gables
    eave_y, ridge_y = gs.POOP_WALL_TOP + 0.1, gs.POOP_RIDGE
    for side, sn in SIDES:
        eave_f, eave_b = v3(side * (ph + 0.8), eave_y - 0.4, pf + 0.6), v3(side * (ph + 0.8), eave_y - 0.4, pb - 0.6)
        ridge_f, ridge_b = v3(0, ridge_y, pf + 0.6), v3(0, ridge_y, pb - 0.6)
        board(poop, "roof_" + sn, eave_b, ridge_b, eave_f, ridge_f, 0.14, "roof", v3(side * 0.5, 1, 0), overlap=1.0)
    add_cube(poop, "roof_ridge", (0, ridge_y + 0.05, (pf + pb) / 2), EYE, (0.24, 0.2, pf - pb + 1.3), "roof")
    for side, sn in SIDES:
        for k, zz in enumerate((pf + 0.45, pb - 0.45)):
            corner = v3(side * (ph + 0.6), eave_y - 0.55, zz)
            beam(lanterns, "roof_lantern_arm_%s%d" % (sn, k), corner + v3(-side * 0.5, 0.25, 0), corner + v3(0, 0.25, 0), 0.08, "iron")
            add_cube(lanterns, "roof_lantern_%s%d" % (sn, k), corner, EYE, (0.36, 0.5, 0.36), {"all": "lantern", "+2": "iron", "-2": "iron"},
                     stretch=True)
            add_cube(lanterns, "glow_roof_lantern_%s%d" % (sn, k), corner, EYE, (0.24, 0.36, 0.24), "glow", stretch=True)
    for k, zz in enumerate((pf + 0.35, pb - 0.35)):
        add_cube(poop, "roof_finial_%d" % k, (0, ridge_y + 0.3, zz), EYE, (0.2, 0.3, 0.2), "gold")
        add_cube(poop, "roof_finial_ball_%d" % k, (0, ridge_y + 0.55, zz), EYE, (0.14, 0.14, 0.14), "gold")
    for zz, tag in ((pf, "front"), (pb, "back")):
        for k in range(5):
            f0, f1 = k / 5.0, (k + 1) / 5.0
            y0 = eave_y + (ridge_y - eave_y) * f0
            y1 = eave_y + (ridge_y - eave_y) * f1
            half = ph * (1 - (f0 + f1) / 2)
            add_cube(poop, "gable_%s_%d" % (tag, k), (0, (y0 + y1) / 2, zz + (0.08 if tag == "back" else -0.08)), EYE,
                     (2 * half, y1 - y0 + 0.01, 0.14), "wood_honey")
    # stern lanterns: two on the transom corners, a big one on the poop roof
    for k, (x, y, z, s) in enumerate(((2.15, gs.QD_RAIL_Y + 0.2, -17.25, 1.0), (-2.15, gs.QD_RAIL_Y + 0.2, -17.25, 1.0),
                                      (0, ridge_y + 0.15, pb - 0.2, 1.35))):
        beam(lanterns, "stern_lantern_pole_%d" % k, (x, y, z), (x, y + 0.6 * s, z), 0.1, "iron")
        add_cube(lanterns, "stern_lantern_%d" % k, (x, y + 0.95 * s, z), EYE, (0.5 * s, 0.7 * s, 0.5 * s),
                 {"all": "lantern", "+2": "gold", "-2": "gold"}, stretch=True)
        add_cube(lanterns, "glow_stern_lantern_%d" % k, (x, y + 0.95 * s, z), EYE, (0.34 * s, 0.52 * s, 0.34 * s), "glow", stretch=True)
        add_cube(lanterns, "stern_lantern_cap_%d" % k, (x, y + 1.38 * s, z), EYE, (0.3 * s, 0.18 * s, 0.3 * s), "gold")
    # bow lantern
    add_cube(lanterns, "bow_lantern", (0, gs.FC_RAIL_Y + 0.55, 17.3), EYE, (0.4, 0.55, 0.4), {"all": "lantern", "+2": "iron"}, stretch=True)
    add_cube(lanterns, "glow_bow_lantern", (0, gs.FC_RAIL_Y + 0.55, 17.3), EYE, (0.26, 0.4, 0.26), "glow", stretch=True)

    # ---- helm: wheel on a pedestal (bone helm_wheel turns with "steer")
    hub = v3(0, qd_y + 1.05, gs.HELM_Z)
    add_cube(castle_aft, "helm_pedestal", (0, qd_y + 0.5, gs.HELM_Z + 0.12), EYE, (0.3, 1.0, 0.3), "dark_wood")
    add_cube(castle_aft, "helm_pedestal_base", (0, qd_y + 0.08, gs.HELM_Z + 0.12), EYE, (0.55, 0.16, 0.55), "gold")
    wheel = Bone("helm_wheel", origin=hub, parent=castle_aft)
    radius = 0.62
    add_cube(wheel, "helm_hub", hub, EYE, (0.2, 0.2, 0.22), "gold")
    for k in range(8):
        a = 2 * math.pi * k / 8
        dvec = v3(math.cos(a), math.sin(a), 0)
        beam(wheel, "helm_spoke_%d" % k, hub, hub + dvec * (radius + 0.22), 0.07, "hull_light", up=v3(0, 0, 1))
        a2 = 2 * math.pi * (k + 1) / 8
        p0 = hub + dvec * radius
        p1 = hub + v3(math.cos(a2), math.sin(a2), 0) * radius
        beam(wheel, "helm_rim_%d" % k, p0, p1, 0.08, "dark_wood", width=0.1, up=v3(0, 0, 1), extend=0.04)

    # ---- rudder (bone "rudder" turns with "steer"), hinged on the transom
    rpivot = v3(0, 0.0, -gs.HALF_LENGTH - 0.12)
    rudder = Bone("rudder", origin=rpivot, parent=root)
    add_cube(rudder, "rudder_blade", (0, -0.55, -gs.HALF_LENGTH - 0.55), EYE, (0.18, 2.1, 0.85), {"all": "hull_dark", "+2": "end_grain"})
    add_cube(rudder, "rudder_stock", (0, 0.2, -gs.HALF_LENGTH - 0.16), EYE, (0.22, 0.9, 0.22), "dark_wood")
    for k, y in enumerate((-1.1, -0.4, 0.3)):
        add_cube(rudder, "rudder_pintle_%d" % k, (0, y, -gs.HALF_LENGTH - 0.15), EYE, (0.3, 0.1, 0.3), "iron")

    # ---- bow: stem post, beakhead, figurehead, bowsprit, anchors
    stem_pts = []
    for j in range(7):
        t = j / 6
        z = 17.5 + 0.8 * t ** 1.6
        y = gs.keel_y(17.5) - 0.1 + (gs.FC_RAIL_Y + 0.2 - gs.keel_y(17.5)) * t
        stem_pts.append(v3(0, y, z))
    for j in range(len(stem_pts) - 1):
        beam(bow, "stem_%d" % j, stem_pts[j], stem_pts[j + 1], 0.4, "dark_wood", width=0.5, extend=0.1)
    beak_z0, beak_z1 = 17.6, 20.0
    beam(bow, "beakhead", (0, 2.2, beak_z0), (0, 2.6, beak_z1), 0.3, "wood_honey", width=0.9)
    beam(bow, "beakhead_rail", (0, 2.6, beak_z0), (0, 3.1, beak_z1 - 0.2), 0.12, "gold", width=0.95)
    for side, sn in SIDES:
        beam(bow, "beak_rail_" + sn, (side * 0.5, 3.6, 17.3), (side * 0.1, 2.75, beak_z1), 0.1, "gold")
    lion = Bone("figurehead", origin=(0, 2.6, beak_z1), parent=bow)
    add_cube(lion, "figurehead_body", (0, 2.75, beak_z1 + 0.25), rx(-0.5), (0.45, 0.5, 0.75), "gold")
    add_cube(lion, "figurehead_head", (0, 3.15, beak_z1 + 0.55), EYE, (0.4, 0.4, 0.4), "gold")
    add_cube(lion, "figurehead_mane", (0, 3.15, beak_z1 + 0.4), EYE, (0.55, 0.55, 0.15), "carving", stretch=True)
    sprit_a, sprit_b = v3(0, 3.9, 16.4), v3(0, 6.9, 24.6)
    beam(bow, "bowsprit", sprit_a, sprit_b, 0.4, "mast")
    beam(bow, "bowsprit_cap", sprit_b - norm(sprit_b - sprit_a) * 0.15, sprit_b + norm(sprit_b - sprit_a) * 0.1, 0.48, "dark_wood")
    jib_boom = sprit_b + norm(sprit_b - sprit_a) * 0.05
    beam(bow, "bowsprit_staff", jib_boom, jib_boom + v3(0, 0.9, 0), 0.08, "dark_wood")
    for side, sn in SIDES:
        z = 14.6
        x = side * (hw(z) + 0.15)
        beam(bow, "anchor_shank_" + sn, (x, 3.3, z), (x, 1.6, z - 0.1), 0.14, "iron")
        beam(bow, "anchor_stock_" + sn, (x, 3.15, z - 0.45), (x, 3.15, z + 0.45), 0.1, "dark_wood")
        beam(bow, "anchor_arm_a_" + sn, (x, 1.6, z - 0.1), (x, 2.05, z - 0.6), 0.12, "iron")
        beam(bow, "anchor_arm_b_" + sn, (x, 1.6, z - 0.1), (x, 2.05, z + 0.4), 0.12, "iron")
        add_cube(bow, "hawse_" + sn, side_frame(16.0, 2.5, side)[0] + v3(side * 0.03, 0, 0), EYE, (0.06, 0.25, 0.25), "iron")

    # ---- masts, tops, yards
    def mast(name, z, foot, top, lower_top, thick):
        mb = Bone(name, origin=(0, foot, z), parent=root)
        beam(mb, name + "_lower", (0, foot - 0.2, z), (0, lower_top + 0.6, z), thick, "mast")
        beam(mb, name + "_upper", (0, lower_top - 0.4, z), (0, top, z), thick * 0.62, "mast")
        add_cube(mb, name + "_partners", (0, foot + 0.12, z), EYE, (thick + 0.35, 0.24, thick + 0.35), "dark_wood")
        add_cube(mb, name + "_cap", (0, top - 0.08, z), EYE, (thick * 0.62 + 0.15, 0.22, thick * 0.62 + 0.15), "gold")
        # fighting top (round platform) at the head of the lower mast
        r = 0.95 + thick
        for k in range(8):
            a = 2 * math.pi * (k + 0.5) / 8
            c = v3(math.cos(a) * r * 0.62, lower_top, z + math.sin(a) * r * 0.62)
            add_cube(mb, "%s_top_%d" % (name, k), c, ry(-a), (r * 0.8, 0.12, r * 0.75), {"all": "dark_wood", "+2": "deck"})
        for k in range(8):
            a = 2 * math.pi * k / 8
            a2 = 2 * math.pi * (k + 1) / 8
            p0 = v3(math.cos(a) * r, lower_top + 0.3, z + math.sin(a) * r)
            p1 = v3(math.cos(a2) * r, lower_top + 0.3, z + math.sin(a2) * r)
            board(mb, "%s_top_rim_%d" % (name, k), p0 - v3(0, 0.35, 0), p0, p1 - v3(0, 0.35, 0), p1, 0.06, "dark_wood",
                  v3(math.cos(a), 0, math.sin(a)), overlap=1.12)
        return mb

    m_main = mast("mainmast", gs.MAIN_MAST_Z, main_y, gs.MAIN_MAST_TOP, 15.2, 0.62)
    m_fore = mast("foremast", gs.FORE_MAST_Z, fc_y, gs.FORE_MAST_TOP, 13.0, 0.52)
    m_mizzen = Bone("mizzen", origin=(0, main_y, gs.MIZZEN_Z), parent=root)
    beam(m_mizzen, "mizzen_mast", (0, main_y, gs.MIZZEN_Z), (0, gs.MIZZEN_TOP, gs.MIZZEN_Z), 0.42, "mast")
    add_cube(m_mizzen, "mizzen_partners", (0, qd_y + 0.12, gs.MIZZEN_Z), EYE, (0.8, 0.24, 0.8), "dark_wood")
    add_cube(m_mizzen, "mizzen_cap", (0, gs.MIZZEN_TOP - 0.08, gs.MIZZEN_Z), EYE, (0.55, 0.22, 0.55), "gold")

    def yard(mb, name, z, y, half):
        beam(mb, name, (-half, y, z + 0.38), (half, y, z + 0.38), 0.22, "mast", extend=0.1)
        add_cube(mb, name + "_sling", (0, y, z + 0.3), EYE, (0.4, 0.34, 0.34), "rope")
        # furled canvas bundle along the yard (seen when the sail is struck)
        beam(mb, name + "_roll", (-half * 0.92, y - 0.2, z + 0.42), (half * 0.92, y - 0.2, z + 0.42), 0.24, "cloth_roll")

    sails_info = []

    def square_sail(mb, name, z, y_top, half_top, half_bottom, height, region, depth):
        # yard and sail hang in a bone turned around the mast: the yards are braced round, so the
        # bellied sails show their curve from the side as on the reference pictures
        br = Bone("brace_" + name, origin=(0, y_top, z), parent=mb)
        yard(br, name + "_yard", z, y_top, half_top + 0.35)
        sb = Bone("sail_" + name, origin=(0, y_top, z + 0.42), parent=br)
        sail(sb, name, v3(0, y_top - 0.12, z + 0.45), v3(1, 0, 0), v3(0, -1, 0), v3(0, 0, 1), half_top, half_bottom,
             height, depth * 2.1, region, nx=7, ny=10, round_=0.8, overlap=0.03, foot=0.09)
        br.rot = ry(BRACE)
        sails_info.append((sb, False))
        return sb

    square_sail(m_main, "main_course", gs.MAIN_MAST_Z, 14.1, 4.6, 5.3, 8.9, "course", 1.25)
    square_sail(m_main, "main_topsail", gs.MAIN_MAST_Z, 23.4, 2.9, 4.1, 6.6, "topsail", 0.9)
    square_sail(m_fore, "fore_course", gs.FORE_MAST_Z, 12.2, 3.8, 4.5, 6.0, "course", 1.0)
    square_sail(m_fore, "fore_topsail", gs.FORE_MAST_Z, 19.9, 2.4, 3.3, 5.4, "topsail", 0.75)

    # mizzen lateen yard and sail
    lat_fore, lat_aft = v3(0.32, 8.0, -8.0), v3(0.32, 16.6, -17.4)
    beam(m_mizzen, "lateen_yard", lat_fore - norm(lat_aft - lat_fore) * 0.3, lat_aft, 0.2, "mast")
    beam(m_mizzen, "lateen_roll", lat_fore + v3(0.05, -0.2, 0) + norm(lat_aft - lat_fore) * 0.8,
         lat_aft + v3(0.05, -0.2, 0) - norm(lat_aft - lat_fore) * 0.4, 0.24, "cloth_roll")
    lat_sail = Bone("sail_mizzen", origin=tuple((lat_fore + lat_aft) / 2), parent=m_mizzen)
    lateen_tri = tri_sail(lat_sail, "mizzen_lateen", lat_aft + v3(0.08, -0.12, 0.05), lat_fore + v3(0.08, -0.12, 0),
                          v3(0.4, 8.0, -16.4), 0.85, v3(1, 0, 0), "lateen", ny=8)
    sails_info.append((lat_sail, True))

    # jibs on the stays to the bowsprit
    beam(bow, "jib_roll", sprit_a + (sprit_b - sprit_a) * 0.5 + v3(0, 0.25, 0), sprit_b + v3(0, 0.22, -0.3), 0.2, "cloth_roll")
    jib = Bone("jib", origin=tuple(sprit_b), parent=root)
    fore_head = v3(0, gs.FORE_MAST_TOP - 0.5, gs.FORE_MAST_Z)
    stay_top = sprit_b + (fore_head - sprit_b) * 0.62
    outer_clew = jib_clew(stay_top, sprit_b, v3(0.05, 6.6, 19.2))
    jib_tri = tri_sail(jib, "jib_outer", stay_top + v3(0.0, -0.05, -0.06), sprit_b + v3(0, 0.05, -0.12),
                       outer_clew, 0.6, v3(1, 0, 0), "jib", nx=4, ny=6)
    fore_low = v3(0, 13.0, gs.FORE_MAST_Z)
    mid_sprit = sprit_a + (sprit_b - sprit_a) * 0.55
    st2 = mid_sprit + (fore_low - mid_sprit) * 0.62
    tri_sail(jib, "jib_inner", st2 + v3(0.0, -0.05, -0.06), mid_sprit + v3(0, 0.05, -0.1),
             jib_clew(st2, mid_sprit, v3(0.05, 5.0, 16.2)), 0.5, v3(1, 0, 0), "jib", nx=4, ny=6)
    sails_info.append((jib, True))
    sprit_yard = sprit_a + (sprit_b - sprit_a) * 0.72
    beam(bow, "spritsail_yard", sprit_yard + v3(-2.3, -0.25, 0), sprit_yard + v3(2.3, -0.25, 0), 0.16, "mast", extend=0.08)
    beam(bow, "spritsail_roll", sprit_yard + v3(-1.9, -0.45, 0.05), sprit_yard + v3(1.9, -0.45, 0.05), 0.22, "cloth_roll")
    sprit_sail = Bone("sail_sprit", origin=tuple(sprit_yard + v3(0, -0.3, 0)), parent=bow)
    sail(sprit_sail, "spritsail", sprit_yard + v3(0, -0.36, 0.12), v3(1, 0, 0), v3(0, -1, 0), v3(0, 0, 1), 2.1, 2.4, 2.3, 0.8,
         "topsail", nx=4, ny=5, round_=0.7, foot=0.08)
    sails_info.append((sprit_sail, False))

    # ---- flags (texture #1): masthead flags, main pennant, stern ensign
    def flag(parent, name, root_pt, w, h, region="flag"):
        fb = Bone("flag_" + name, origin=tuple(root_pt), parent=parent)
        c1 = add_cube(fb, "flag_%s_a" % name, root_pt + v3(0, -h / 2, -w / 4), EYE, (0.03, h, w / 2),
                      {"all": None, "+1": region, "-1": region}, stretch=True, u_dir=v3(0, 0, -1), v_dir=v3(0, -1, 0))
        tip_root = root_pt + v3(0, 0, -w / 2)
        ft = Bone("flag_%s_tip" % name, origin=tuple(tip_root), parent=fb)
        c2 = add_cube(ft, "flag_%s_b" % name, tip_root + v3(0, -h / 2, -w / 4), EYE, (0.03, h, w / 2),
                      {"all": None, "+1": region, "-1": region}, stretch=True, u_dir=v3(0, 0, -1), v_dir=v3(0, -1, 0))
        set_sub(c1, (0, 0, 0.5, 1), faces=("west", "east"))
        set_sub(c2, (0.5, 0, 1, 1), faces=("west", "east"))
        return fb

    for mb, name, z, top in ((m_main, "main", gs.MAIN_MAST_Z, gs.MAIN_MAST_TOP), (m_fore, "fore", gs.FORE_MAST_Z, gs.FORE_MAST_TOP),
                             (m_mizzen, "mizzen", gs.MIZZEN_Z, gs.MIZZEN_TOP)):
        beam(mb, name + "_flagpole", (0, top, z), (0, top + 1.3, z), 0.1, "dark_wood")
        if name == "main":
            # long swallow-tail pennant
            fb = flag(mb, name, v3(0, top + 1.2, z), 4.2, 0.55, region="pennant")
        else:
            flag(mb, name, v3(0, top + 1.2, z), 1.9, 1.15)
    staff_base = v3(0, gs.POOP_RIDGE + 0.1, gs.POOP_BACK - 0.6)
    beam(castle_aft, "ensign_staff", staff_base, staff_base + v3(0, 3.2, -0.6), 0.12, "dark_wood")
    flag(castle_aft, "stern", staff_base + v3(0, 3.1, -0.65), 2.7, 1.7)

    # ---- rigging
    rope = 0.055
    rig = []

    def deadeye(z, side, y=None):
        y = gs.rail_y(z) if y is None else y
        return v3(side * (0.98 * hw(z) + 0.12), y - 0.1, z)

    for side, sn in SIDES:
        for k, z in enumerate((-0.6, 0.4, 1.4, 2.4)):
            rig.append(("main_shroud_%s%d" % (sn, k), v3(side * 0.9, 15.15, gs.MAIN_MAST_Z), deadeye(z, side)))
        for k, z in enumerate((11.4, 12.2, 13.0)):
            rig.append(("fore_shroud_%s%d" % (sn, k), v3(side * 0.8, 12.95, gs.FORE_MAST_Z), deadeye(z, side)))
        for k, z in enumerate((-12.0, -13.2)):
            rig.append(("mizzen_shroud_%s%d" % (sn, k), v3(side * 0.2, 13.0, gs.MIZZEN_Z), deadeye(z, side)))
        for k in range(2):
            rig.append(("main_topshroud_%s%d" % (sn, k), v3(side * 0.25, gs.MAIN_MAST_TOP - 1.2, gs.MAIN_MAST_Z),
                        v3(side * 1.4, 15.4, gs.MAIN_MAST_Z + (k - 0.5) * 0.9)))
            rig.append(("fore_topshroud_%s%d" % (sn, k), v3(side * 0.2, gs.FORE_MAST_TOP - 1.0, gs.FORE_MAST_Z),
                        v3(side * 1.25, 13.2, gs.FORE_MAST_Z + (k - 0.5) * 0.8)))
        # sheets from the course clews to the rail, braces from the yard arms aft
        mz, fz = gs.MAIN_MAST_Z, gs.FORE_MAST_Z
        rig.append(("main_sheet_" + sn, braced((side * 5.2, 5.6, mz + 1.6), mz), deadeye(-3.0, side)))
        rig.append(("main_brace_" + sn, braced((side * 4.9, 14.1, mz + 0.4), mz), deadeye(-9.5, side, gs.QD_RAIL_Y)))
        rig.append(("main_topbrace_" + sn, braced((side * 3.2, 23.4, mz + 0.4), mz), v3(side * 0.2, 15.0, gs.MIZZEN_Z)))
        rig.append(("fore_sheet_" + sn, braced((side * 4.4, 6.6, fz + 1.3), fz), deadeye(8.6, side)))
        rig.append(("fore_brace_" + sn, braced((side * 4.1, 12.2, fz + 0.4), fz), v3(side * 0.6, 14.4, mz)))
    rig += [
        ("main_stay", v3(0, 15.0, gs.MAIN_MAST_Z + 0.3), v3(0, fc_y + 0.4, gs.FORE_MAST_Z - 0.4)),
        ("main_topstay", v3(0, gs.MAIN_MAST_TOP - 0.6, gs.MAIN_MAST_Z), v3(0, 13.2, gs.FORE_MAST_Z)),
        ("fore_stay", v3(0, 12.9, gs.FORE_MAST_Z + 0.2), mid_sprit),
        ("fore_topstay", fore_head, sprit_b),
        ("mizzen_stay", v3(0, gs.MIZZEN_TOP - 0.4, gs.MIZZEN_Z), v3(0, 9.5, gs.MAIN_MAST_Z - 0.3)),
        ("mizzen_backstay", v3(0, gs.MIZZEN_TOP - 0.6, gs.MIZZEN_Z), v3(0, gs.QD_RAIL_Y + 0.2, -17.3)),
        ("lateen_halyard", v3(0.2, gs.MIZZEN_TOP - 0.4, gs.MIZZEN_Z), lat_fore + (lat_aft - lat_fore) * 0.5),
        ("lateen_sheet", v3(0.4, 8.0, -16.4), v3(0.4, gs.QD_RAIL_Y + 0.1, -17.2)),
        ("jib_sheet", outer_clew, v3(0.4, gs.FC_RAIL_Y, 15.9)),
        ("bobstay", sprit_b - v3(0, 0.15, 0.3), v3(0, 1.0, 18.0)),
    ]
    for name, a, b in rig:
        beam(ropes, "rope_" + name, a, b, rope, "rope")
        if "shroud" in name and "top" not in name:
            add_cube(ropes, "deadeye_" + name, b, EYE, (0.14, 0.2, 0.2), "dark_wood")
            beam(ropes, "chain_" + name, b, b + v3(0, -0.9, 0), 0.05, "iron")
    # ratlines across the main and fore shrouds
    for side, sn in SIDES:
        for mast_tag, top_y, z_top, z0, z1, foot_y in (("main", 15.15, gs.MAIN_MAST_Z, -0.6, 2.4, None),
                                                      ("fore", 12.95, gs.FORE_MAST_Z, 11.4, 13.0, None)):
            top_pt = v3(side * 0.9, top_y, z_top)
            fa, fb_ = deadeye(z0, side), deadeye(z1, side)
            for k in range(1, 9):
                t = k / 9.5
                pa = fa + (top_pt - fa) * t
                pb = fb_ + (top_pt - fb_) * t
                beam(ropes, "ratline_%s_%s%d" % (mast_tag, sn, k), pa, pb, 0.04, "rope")
    return root, lateen_tri, jib_tri, sails_info


# ---------------------------------------------------------------- animations
def build_animations(root, sails_info):
    kf, rot_kf, animation, find = gg.kf, gg.rot_kf, gg.animation, gg.find
    anims = []
    # wind in the sails: the belly breathes (scale along the billow) and the cloth sways
    tracks = []
    for k, (b, side_billow) in enumerate(sails_info):
        ph = 0.37 * k
        if side_billow:
            sc = [kf("scale", t, (s, 1, 1), "catmullrom") for t, s in ((0, 1.0), (0.9, 1.18), (1.8, 0.92), (2.7, 1.1), (3.6, 1.0))]
            rt = [rot_kf(t, (0, 0, a), "catmullrom") for t, a in ((0, 0), (1.2, 1.2), (2.4, -0.8), (3.6, 0))]
        else:
            sc = [kf("scale", t, (1, 1, s), "catmullrom") for t, s in ((0, 1.0), (0.9 + ph * 0.1, 1.16), (1.8, 0.9), (2.7, 1.08), (3.6, 1.0))]
            rt = [rot_kf(t, (a, 0, 0), "catmullrom") for t, a in ((0, 0), (1.2, -1.6), (2.4, 0.8), (3.6, 0))]
        tracks.append((b, sc + rt))
    anims.append(animation("sail_wind", 3.6, "loop", tracks))
    # furl: sails gathered up to their yards (time 0 = set, 1 = furled)
    tracks = []
    for b, side_billow in sails_info:
        if side_billow:
            tracks.append((b, [kf("scale", 0.0, (1, 1, 1)), kf("scale", 1.0, (0, 0, 0))]))
        else:
            tracks.append((b, [kf("scale", 0.0, (1, 1, 1)), kf("scale", 1.0, (0.95, 0, 0))]))
    anims.append(animation("sail_furl", 1.0, "hold", tracks))
    # steer: 0 = full port helm, 1 = centre, 2 = full starboard
    wheel, rudder = find(root, "helm_wheel"), find(root, "rudder")
    anims.append(animation("steer", 2.0, "hold", [
        (wheel, [rot_kf(0.0, (0, 0, -150)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 0, 150))]),
        (rudder, [rot_kf(0.0, (0, -30, 0)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 30, 0))])]))
    # flags
    tracks = []
    for k, name in enumerate(("main", "fore", "mizzen", "stern")):
        f, ft = find(root, "flag_" + name), find(root, "flag_%s_tip" % name)
        a = 8 if name != "main" else 12
        sh = 0.15 * k
        tracks.append((f, [rot_kf(0 + sh, (0, a, 0), "catmullrom"), rot_kf(0.6 + sh, (0, -a, 0), "catmullrom"),
                           rot_kf(1.2 + sh, (0, a, 0), "catmullrom")]))
        tracks.append((ft, [rot_kf(0 + sh, (0, -2 * a, 0), "catmullrom"), rot_kf(0.6 + sh, (0, 2 * a, 0), "catmullrom"),
                            rot_kf(1.2 + sh, (0, -2 * a, 0), "catmullrom")]))
    for b, kfs in tracks:
        # keep keyframe times inside the loop
        for k in kfs:
            k["time"] = round(k["time"] % 1.2 if k["time"] > 1.2 else k["time"], 4)
        kfs.sort(key=lambda k: k["time"])
    anims.append(animation("flag_wave", 1.2, "loop", tracks))
    return anims


# ---------------------------------------------------------------- export
def face_uv(cube, bbface, spec, seed):
    tex, u0, v0, rw, rh = REGIONS[spec["region"]]
    normal, udir, vdir = gg.FACE_AXES[bbface]
    size_bb = cube.size
    du = abs(np.dot(udir, size_bb))
    dv = abs(np.dot(vdir, size_bb))
    sub = spec.get("sub")
    if sub is not None:
        uv = [u0 + sub[0] * rw, v0 + sub[1] * rh, u0 + sub[2] * rw, v0 + sub[3] * rh]
    elif spec["stretch"]:
        uv = [u0, v0, u0 + rw, v0 + rh]
    else:
        su = min(rw, max(1, round(du * 16 * spec["density"])))
        sv = min(rh, max(1, round(dv * 16 * spec["density"])))
        ou = (seed * 7) % max(1, rw - su + 1)
        ov = ((seed // 3) * 4) % max(1, rh - sv + 1)
        ov -= ov % 4
        uv = [u0 + ou, v0 + ov, u0 + ou + su, v0 + ov + sv]
    Rbb = gg.to_bb_rot(cube.axes)
    for idx, hint, axis in ((0, spec["u_dir"], udir), (1, spec["v_dir"], vdir)):
        if hint is None:
            continue
        world_axis = gg.M @ (Rbb @ axis)
        if np.dot(world_axis, hint) < 0:
            uv[idx], uv[idx + 2] = uv[idx + 2], uv[idx]
    return [round(x, 4) for x in uv], tex


def texture_entry(name, size, png, rel, default_name="galleon.png"):
    return {
        "path": "", "name": name, "folder": "entity", "namespace": "medievalships", "id": str(len(name) % 2),
        "group": "", "width": size, "height": size, "uv_width": size, "uv_height": size,
        "particle": False, "use_as_default": name == default_name, "layers_enabled": False, "sync_to_project": "",
        "render_mode": "default", "render_sides": "auto", "frame_time": 1, "frame_order_type": "loop",
        "frame_order": "", "frame_interpolate": False, "visible": True, "internal": True, "saved": True,
        "uuid": new_uuid(), "relative_path": "../src/main/resources/assets/medievalships/textures/entity/" + name,
        "source": "data:image/png;base64," + base64.b64encode(png).decode()}


def export(root, anims, textures, out_paths, name="galleon", visible_box=(40, 32, 0)):
    import lanterns  # every ship gets the same lit-glass lanterns
    print("lanterns: %d" % lanterns.convert(root))
    import rope_follow  # sheets stay on the clews when the sails are furled
    print("ropes following the furled sails: %d" % rope_follow.follow(root, anims))
    import zfight  # coplanar faces would flicker in game
    zfight.fix(root)
    elements = []

    def group_json(b):
        children = []
        for c in b.cubes:
            Rbb = gg.to_bb_rot(c.axes)
            euler = gg.matrix_to_euler_zyx(Rbb)
            center = gg.to_bb_point(c.center)
            half = c.size * 8.0
            frm = [round(center[k] - half[k], 4) for k in range(3)]
            to = [round(center[k] + half[k], 4) for k in range(3)]
            faces = {}
            for bbface, spec in c.faces.items():
                if spec is None:
                    faces[bbface] = {"uv": [0, 0, 0, 0], "texture": None}
                else:
                    seed = zlib.crc32((c.name + bbface).encode()) % 9973
                    uv, tex = face_uv(c, bbface, spec, seed)
                    faces[bbface] = {"uv": uv, "texture": tex}
            el = {"name": c.name, "box_uv": False, "rescale": False, "locked": False,
                  "render_order": "default", "allow_mirror_modeling": True,
                  "from": frm, "to": to, "autouv": 0, "color": 0, "origin": center,
                  "faces": faces, "type": "cube", "uuid": c.uuid}
            if any(abs(x) > 1e-4 for x in euler):
                el["rotation"] = euler
            elements.append(el)
            children.append(c.uuid)
        for ch in b.children:
            children.append(group_json(ch))
        g = {"name": b.name, "origin": gg.to_bb_point(b.origin), "color": 0, "uuid": b.uuid, "export": True,
             "mirror_uv": False, "isOpen": False, "locked": False, "visibility": True, "autouv": 0,
             "children": children}
        e = gg.matrix_to_euler_zyx(gg.to_bb_rot(b.rot))
        if any(abs(x) > 1e-4 for x in e):
            g["rotation"] = e
        return g

    outliner = [group_json(root)]
    model = {
        "meta": {"format_version": "4.10", "model_format": "free", "box_uv": False},
        "name": name,
        "model_identifier": name,
        "visible_box": list(visible_box),
        "variable_placeholders": "",
        "variable_placeholder_buttons": [],
        "timeline_setups": [],
        "unhandled_root_fields": {},
        "resolution": {"width": SIZE, "height": SIZE},
        "elements": elements,
        "outliner": outliner,
        "textures": textures,
        "animations": anims,
    }
    for p in out_paths:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            json_dump(model, f, compact="resources" in p)
    return model


def json_dump(model, f, compact):
    import json
    json.dump(model, f, separators=(",", ":") if compact else (", ", ": "), indent=None if compact else 1)


def main():
    root, lateen_tri, jib_tri, sails_info = build()
    anims = build_animations(root, sails_info)
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    tex_path = os.path.join(tex_dir, "entity/galleon.png")
    flag_path = os.path.join(tex_dir, "entity/galleon_flag.png")
    make_textures(tex_path, flag_path, lateen_tri, jib_tri)
    make_item_icon(os.path.join(tex_dir, "item/galleon.png"))
    with open(tex_path, "rb") as f:
        png = f.read()
    with open(flag_path, "rb") as f:
        flag_png = f.read()
    textures = [texture_entry("galleon.png", SIZE, png, "entity"), texture_entry("galleon_flag.png", FLAG_SIZE, flag_png, "entity")]
    textures[0]["id"], textures[1]["id"] = "0", "1"
    model = export(root, anims, textures, [
        os.path.join(ROOT, "blockbench/galleon.bbmodel"),
        os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/galleon.bbmodel"),
    ])
    n_groups = [0]

    def count(g):
        n_groups[0] += 1
        for c in g["children"]:
            if isinstance(c, dict):
                count(c)
    count(model["outliner"][0])
    print("cubes:", len(model["elements"]), "bones:", n_groups[0], "animations:",
          [a["name"] for a in model["animations"]])


if __name__ == "__main__":
    main()
