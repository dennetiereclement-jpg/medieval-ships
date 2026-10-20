#!/usr/bin/env python3
"""Generates the great warship Blockbench model (.bbmodel), its textures and animations.

Usage:  python3 tools/generate_warship.py

Outputs:
  blockbench/warship.bbmodel                                     (editable, textures embedded)
  src/main/resources/assets/medievalships/models/entity/warship.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/warship.png
  src/main/resources/assets/medievalships/textures/entity/warship_flag.png  (flags: emblem, texture #1)
  src/main/resources/assets/medievalships/textures/item/warship.png

Same conventions and helpers as tools/generate_galleon.py; shape and layout come from
tools/warship_shape.py, identical to the Java collision code.

Bones used by the mod (keep their names when editing in Blockbench):
  sail_* and jib (wind, furl)  helm_wheel, rudder (steer)  flag_*, flag_*_tip (flag_wave)
  cannon_l1..cannon_l29, cannon_r1..cannon_r29: one bone per gun (barrel inside), for a future
  combat system (recoil, hiding, smoke origin); same order as ShipGeometry.gunports()
"""
import math
import os
import sys
import uuid

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import generate_galleon as gn  # noqa: E402
import generate_galley as gg  # noqa: E402
import warship_shape as ws  # noqa: E402
import warship_texture as wt  # noqa: E402
import ship_details as sd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/warship/%d" % _uuid_counter[0]))


# the galleon helpers (sails, decals, export) work on the warship shape and textures
gg.new_uuid = new_uuid
gn.new_uuid = new_uuid
gn.gs = ws
gn.REGIONS = wt.REGIONS
gn.SIZE = wt.SIZE

v3, norm, Bone, add_cube, beam, board = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam, gg.board
rx, ry = gg.rx, gg.ry
EYE = np.eye(3)
SIDES = ((1, "p"), (-1, "s"))

# hull stations (the frames the planking is laid on): the original ones, plus one between each pair
# for a smoother run of the bands and wales towards the ends
STATIONS0 = [-27.5, -26.4, -25.0, -23.4, -21.6, -19.6, -17.4, -15.0, -12.5, -10.0, -7.4, -4.8, -2.2, 0.4,
             3.0, 5.6, 8.2, 10.8, 13.2, 15.6, 17.8, 19.8, 21.6, 23.2, 24.6, 25.8, 26.8, 27.5, 28.0, 28.35]
STATIONS = sorted(set(STATIONS0 + [(a + b) / 2 for a, b in zip(STATIONS0, STATIONS0[1:])]))
# hull bands above the waterline, bottom to top: white bottom, black wale, ochre (lower guns),
# black, ochre (middle guns), black wale, dark upper works
BANDS = [0.3, 1.0, 2.05, 2.6, 3.85, 4.4]
# (band from, band to, strakes in it, colour)
BAND_STRAKES = [(0, 1, 3, "hull_black"), (1, 2, 2, "ochre"), (2, 3, 1, "hull_black"), (3, 4, 2, "ochre"),
                (4, 5, 1, "hull_black"), (5, 6, 2, "hull_black")]
BOTTOM_STRAKES = 6
STRAKES = ["white_bottom"] * BOTTOM_STRAKES + [c for _, _, n, c in BAND_STRAKES for _ in range(n)]


CABIN_WINDOWS_Z = (-12.0, -14.5, -17.0, -21.0, -22.8)
CABIN_WINDOW_Y = 5.65


def lift(z):
    return ws.band_lift(z)


def hw(z):
    return ws.half_width(z)


def smoothstep(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


# ---- visual hull form (the collision hull in warship_shape.py is unchanged): the sides swell out
# a little above the waterline and fall in towards the decks (tumblehome); aft, the lower hull is
# drawn in towards the stern post (the run), so that the stern rises from the water like a wine glass
SWELL = 0.035        # extra breadth at the widest point, fraction of the half width
Y_WIDE, Y_DECK = 1.45, 4.5
RUN_Z = -20.0
SWEEP_POOP, SWEEP_QD, SWEEP_FC = 3.0, 3.6, 3.2   # length of the castles' sweeps down to the lower rails
DEAD_Z, DEADWOOD_HEEL = -21.0, -1.8   # deadwood under the run, down to the rudder's heel


def breadth(y):
    """Half breadth of the hull side at height y (>= 0.3), as a fraction of the collision half width."""
    if y <= 0.3:
        return 1.0
    if y <= Y_WIDE:
        t = (y - 0.3) / (Y_WIDE - 0.3)
        m0 = 0.06
        return (2 * t ** 3 - 3 * t ** 2 + 1) * 1.0 + (t ** 3 - 2 * t ** 2 + t) * m0 + (-2 * t ** 3 + 3 * t ** 2) * (1 + SWELL)
    if y <= Y_DECK:
        return 1 + SWELL + (0.978 - 1 - SWELL) * smoothstep((y - Y_WIDE) / (Y_DECK - Y_WIDE))
    return 0.975 + 0.003 * (1 - smoothstep((y - Y_DECK) / 1.2))


def pinch(z, y):
    """How much the lower hull is drawn in towards the stern post (0 = not at all)."""
    if z >= RUN_Z:
        return 0.0
    t = min(1.0, (RUN_Z - z) / (ws.HALF_LENGTH + RUN_Z))
    yk = ws.keel_y(z)
    top = 1.3 + 0.8 * t
    return 0.62 * t ** 1.8 * (1.0 - smoothstep((y - yk) / (top - yk)))


def outer_x(z, y):
    """Outer surface of the hull side (above the waterline)."""
    return hw(z) * breadth(y) * (1 - pinch(z, y))


def _catmull(p0, p1, p2, p3, t):
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)


def section_xy(z):
    """Outer cross-section (x >= 0, y) from the keel to the sheer: a rounded bilge (spline through the
    collision bottom), then the bands."""
    w, yk, ys = hw(z), ws.keel_y(z), ws.sheer_y(z)
    ctrl = [np.array((0.08, yk))] + [np.array((fx * w, fy * yk)) for fx, fy in ws.BOTTOM_SECTION[1:]]
    ctrl.append(np.array((w, 0.3)))
    ctrl = [np.array((-0.08, yk))] + ctrl + [np.array((w * breadth(1.0), 1.0))]
    pts = []
    for i, n in zip(range(1, len(ctrl) - 2), (1, 2, 2, 1)):
        for k in range(n):
            pts.append(_catmull(ctrl[i - 1], ctrl[i], ctrl[i + 1], ctrl[i + 2], k / n))
    ys_list = [0.3]
    lifted = [b + (lift(z) if b > 0.5 else 0.0) for b in BANDS] + [ys]
    for i0, i1, n, _ in BAND_STRAKES:
        for k in range(1, n + 1):
            ys_list.append(lifted[i0] + (lifted[i1] - lifted[i0]) * k / n)
    out = []
    for x, y in pts:
        out.append((max(0.08, x * (1 - pinch(z, y))), y))
    for y in ys_list:
        out.append((max(0.08, outer_x(z, y)), y))
    return out


def section(z, side):
    return [v3(side * x, y, z) for x, y in section_xy(z)]


def side_frame(z, y, side):
    """Point on the hull side and a frame lying on it (u along +z, v up the side, n outward)."""
    d = 0.05
    def P(zz, yy):
        return v3(side * outer_x(zz, yy), yy, zz)
    p = P(z, y)
    u = norm(P(z + d, y) - P(z - d, y))
    v = P(z, y + d) - P(z, y - d)
    v = norm(v - np.dot(v, u) * u)
    n = np.cross(v, u) * side
    if np.dot(n, v3(side, 0, 0)) < 0:
        n = -n
    return p, u, v, n


def inner_decal(bone, name, z, y, side, w, h, region, wall=0.12, th=0.03):
    """Thin element on the inner face of the hull side, kept clear of the planking (which is bent here)."""
    p, u, v, n = side_frame(z, y, side)
    c = p - n * (wall + 0.05 + th / 2)
    return add_cube(bone, name, c, np.column_stack([u, v, n]), (w, h, th), {"all": None, "-3": region}, stretch=True,
                    u_dir=u * side, v_dir=v3(0, -1, 0))


gn.outer_x = outer_x
gn.hw = hw
gn.side_frame = side_frame
gn.inner_decal = inner_decal


# ---- rounded and bevelled timber
T225 = math.tan(math.pi / 8)


def round_beam(bone, name, p0, p1, d, region, extend=0.0, up=v3(0, 1, 0)):
    """Round spar or post: an eight-sided prism of diameter d (four bars turned by 45 degrees)."""
    p0, p1 = v3(*p0), v3(*p1)
    ax = norm(p1 - p0)
    if abs(np.dot(ax, up)) > 0.98:
        up = v3(1, 0, 0)
    F = gg.frame_from(ax, up)
    out = []
    for k in range(4):
        a = math.pi * k / 4
        upk = F[:, 1] * math.cos(a) + F[:, 2] * math.sin(a)
        out.append(beam(bone, "%s%s" % (name, "" if k == 0 else "_r%d" % k), p0, p1, d, region, width=d * T225 * 1.02,
                        up=upk, extend=extend))
    return out


def bevel_beam(bone, name, p0, p1, th, width, region, c=None, corners=("+v+n", "+v-n"), up=v3(0, 1, 0), extend=0.0,
               out_hint=None):
    """Beam (th along up, width across) whose chosen long edges are bevelled at 45 degrees.
    corners: among +v+n, +v-n, -v+n, -v-n; out_hint flips n so that +n points that way."""
    p0, p1 = v3(*p0), v3(*p1)
    dvec = p1 - p0
    L = np.linalg.norm(dvec) + 2 * extend
    if abs(np.dot(norm(dvec), up)) > 0.98:
        up = v3(1, 0, 0)
    F = gg.frame_from(dvec, up)
    u, v, n = F[:, 0], F[:, 1], F[:, 2]
    if out_hint is not None and np.dot(n, out_hint) < 0:
        n, u = -n, -u
    c = c if c is not None else 0.28 * min(th, width)
    cen = (p0 + p1) / 2
    cs = set(corners)
    vp, vm = any(k.startswith("+v") for k in cs), any(k.startswith("-v") for k in cs)
    np_, nm = any(k.endswith("+n") for k in cs), any(k.endswith("-n") for k in cs)
    e = 0.007
    axes = np.column_stack([u, v, n])
    # bar A: full height, narrowed across where an edge is bevelled; bar B: full width, lowered
    a_n0, a_n1 = -width / 2 + (c if nm else e), width / 2 - (c if np_ else e)
    b_v0, b_v1 = -th / 2 + (c if vm else e), th / 2 - (c if vp else e)
    out = [add_cube(bone, name, cen + n * (a_n0 + a_n1) / 2, axes, (L, th, a_n1 - a_n0), region),
           add_cube(bone, name + "_b", cen + v * (b_v0 + b_v1) / 2, axes, (L - 0.004, b_v1 - b_v0, width), region)]
    for k in cs:
        sv = 1 if k[0] == "+" else -1
        sn_ = 1 if k[2] == "+" else -1
        mid = cen + v * sv * (th / 2 - c / 2) + n * sn_ * (width / 2 - c / 2)
        dn = norm(v * sv + n * sn_)   # the bevel's normal
        dv = np.cross(dn, u)
        out.append(add_cube(bone, "%s_bevel_%s" % (name, k.replace("+", "p").replace("-", "m")), mid - dn * 0.012,
                            np.column_stack([u, dv, dn]), (L - 0.008, c * math.sqrt(2) + 0.012, 0.024), region))
    return out


# ---- the stern: bow-fronted (curved in plan), with a curved counter under the galleries
ZT = -ws.HALF_LENGTH
COUNTER_TOP = 1.0 + ws.band_lift(-ws.HALF_LENGTH)   # the lower wale on the stern
B_LOW, B_TOP = 0.08, 0.62


def bulge(y):
    """How far the middle of the stern stands out aft of its corners, at height y."""
    return B_LOW + (B_TOP - B_LOW) * smoothstep((y - 0.0) / (COUNTER_TOP + 0.2))


_SXY = None


def stern_w(y):
    """Half width of the stern at height y (where the hull sides end)."""
    global _SXY
    if _SXY is None:
        _SXY = section_xy(ZT)
    if y >= 0.3:
        return outer_x(ZT, y)
    xs, ys = [p[0] for p in _SXY], [p[1] for p in _SXY]
    return float(np.interp(y, ys, xs))


def stern_z(x, y):
    w = stern_w(y)
    f = min(1.0, (x / w) ** 2) if w > 0.01 else 1.0
    return ZT - bulge(y) * (1 - f)


def stern_pt(x, y):
    return v3(x, y, stern_z(x, y))


def stern_frame(x, y):
    """Point on the stern, axes (u across to +x, v up, n forward into the ship) and the outward normal."""
    d = 0.03
    p = stern_pt(x, y)
    u = norm(stern_pt(x + d, y) - stern_pt(x - d, y))
    vv = stern_pt(x, y + d) - stern_pt(x, y - d)
    vv = norm(vv - np.dot(vv, u) * u)
    n = np.cross(u, vv)
    if n[2] < 0:
        n = -n
    return p, np.column_stack([u, vv, n]), -n


def scube(bone, name, x, y, off, size, regions, **kw):
    """Cube on the stern face, centre `off` outside it, following its curve."""
    p, R, out = stern_frame(x, y)
    return add_cube(bone, name, p + out * off, R, size, regions, **kw)


def sband(bone, name, y, h, off, depth, region, x0, x1, n=8, **kw):
    """Moulding across the stern following its curve, in n straight pieces."""
    xs = np.linspace(x0, x1, n + 1)
    out = []
    for j in range(n):
        pa, pb = stern_pt(xs[j], y), stern_pt(xs[j + 1], y)
        _, R, o = stern_frame((xs[j] + xs[j + 1]) / 2, y)
        u = norm(pb - pa)
        vv = R[:, 1]
        nn = np.cross(u, vv)
        out.append(add_cube(bone, "%s_%d" % (name, j), (pa + pb) / 2 + o * off, np.column_stack([u, vv, nn]),
                            (np.linalg.norm(pb - pa) + 0.02, h, depth), region, **kw))
    return out


def build():
    root = Bone("warship")
    hull = Bone("hull", parent=root)
    deck = Bone("deck", parent=root)
    stern = Bone("stern", parent=root)
    fore = Bone("forecastle", parent=root)
    cabin = Bone("cabin", parent=root)
    bow = Bone("bow", parent=root)
    ropes = Bone("ropes", parent=root)
    lanterns = Bone("lanterns", parent=root)
    guns = Bone("guns", parent=root)
    main_y, fc_y, qd_y, poop_y = ws.MAIN_DECK_Y, ws.FORECASTLE_Y, ws.QUARTERDECK_Y, ws.POOP_Y

    # ---- hull planking: tilted boards between rounded sections, coloured bands
    deck_strake = next(k for k, (x, y) in enumerate(section_xy(0.0)) if y > main_y - 0.6)
    for side, sn in SIDES:
        for i in range(len(STATIONS) - 1):
            za, zb = STATIONS[i], STATIONS[i + 1]
            A, B = section(za, side), section(zb, side)
            for k, reg in enumerate(STRAKES):
                mid = (A[k] + A[k + 1] + B[k] + B[k + 1]) / 4
                outward = norm(v3(mid[0], mid[1] - 3.0, 0) + v3(0, 0, 0.35 * np.sign(mid[2])))
                board(hull, "hull_%s%d_%d" % (sn, i, k), A[k], A[k + 1], B[k], B[k + 1], 0.14, reg,
                      outward, inner="hull_light" if k >= deck_strake else None)
    for side, sn in SIDES:
        # boot-topping: a thin black moulding along the waterline, where the white bottom meets the sides
        for i in range(len(STATIONS) - 1):
            za, zb = STATIONS[i], STATIONS[i + 1]
            if hw(za) > 0.3 and hw(zb) > 0.3:
                pa, pb = v3(side * (outer_x(za, 0.3) + 0.01), 0.3, za), v3(side * (outer_x(zb, 0.3) + 0.01), 0.3, zb)
                beam(hull, "boot_top_%s%d" % (sn, i), pa, pb, 0.16, "wale", width=0.08, extend=0.04)
        for i in range(len(STATIONS0) - 1):
            za, zb = STATIONS0[i], STATIONS0[i + 1]
            if hw(za) > 0.8 and hw(zb) > 0.8:
                # three black wales, rounded on their outer edges
                for j, y in enumerate((1.0, 2.6, 4.4)):
                    ya, yb = y + lift(za), y + lift(zb)
                    pa, pb = v3(side * (outer_x(za, ya) + 0.05), ya, za), v3(side * (outer_x(zb, yb) + 0.05), yb, zb)
                    bevel_beam(hull, "wale_%s%d_%d" % (sn, i, j), pa, pb, 0.2, 0.2, "wale", c=0.07,
                               corners=("+v+n", "-v+n"), extend=0.05, out_hint=v3(side, 0, 0))
                # thin gilded mouldings along the top of the ochre bands and under the rail
                for j, y in enumerate((2.05, 3.85, 5.25)):
                    ya, yb = y + lift(za), y + lift(zb)
                    if yb > ws.sheer_y(zb) - 0.1 or ya > ws.sheer_y(za) - 0.1:
                        continue
                    pa, pb = v3(side * (outer_x(za, ya) + 0.03), ya, za), v3(side * (outer_x(zb, yb) + 0.03), yb, zb)
                    beam(hull, "moulding_%s%d_%d" % (sn, i, j), pa, pb, 0.07, "gold", width=0.07, extend=0.04)
            if ws.QUARTERDECK_START - 0.01 <= za and zb <= ws.FORECASTLE_START + 0.01:
                pa = v3(side * 0.975 * hw(za), ws.sheer_y(za) + 0.09, za)
                pb = v3(side * 0.975 * hw(zb), ws.sheer_y(zb) + 0.09, zb)
                bevel_beam(hull, "rail_%s%d" % (sn, i), pa, pb, 0.18, 0.36, "red_paint", c=0.08, extend=0.06)
                # sailors' rolled hammocks stowed along the rail of the waist (hammock nettings)
                if za < ws.QUARTERDECK_START + SWEEP_QD or zb > ws.FORECASTLE_START - SWEEP_FC:
                    continue
                ha = v3(side * (0.975 * hw(za) - 0.12), ws.sheer_y(za) + 0.34, za)
                hb = v3(side * (0.975 * hw(zb) - 0.12), ws.sheer_y(zb) + 0.34, zb)
                bevel_beam(hull, "hammocks_%s%d" % (sn, i), ha, hb, 0.34, 0.3, "cloth_roll", c=0.09, extend=0.02)
    # keel, rounded at its foot, with the deadwood carrying it on to the stern post
    for i in range(len(STATIONS0) - 1):
        za, zb = STATIONS0[i], STATIONS0[i + 1]
        bevel_beam(hull, "keel_%d" % i, (0, ws.keel_y(za) - 0.07, za), (0, ws.keel_y(zb) - 0.07, zb), 0.3, 0.42,
                   "white_bottom", c=0.1, corners=("-v+n", "-v-n"), extend=0.06)

    def deadwood_y(z):
        t = (DEAD_Z - z) / (ws.HALF_LENGTH + DEAD_Z)
        return ws.keel_y(DEAD_Z) + (DEADWOOD_HEEL - ws.keel_y(DEAD_Z)) * t ** 1.3

    zs = list(np.linspace(DEAD_Z, -ws.HALF_LENGTH, 7))
    for i in range(len(zs) - 1):
        za, zb = zs[i], zs[i + 1]
        ta, tb = ws.keel_y(za) + 0.1, ws.keel_y(zb) + 0.1
        da, db = deadwood_y(za) - 0.07, deadwood_y(zb) - 0.07
        board(hull, "deadwood_%d" % i, v3(0.17, da, za), v3(0.17, ta, za), v3(0.17, db, zb), v3(0.17, tb, zb), 0.34,
              "white_bottom", v3(1, 0, 0))
        bevel_beam(hull, "deadwood_foot_%d" % i, (0, da + 0.08, za), (0, db + 0.08, zb), 0.3, 0.42, "white_bottom", c=0.1,
                   corners=("-v+n", "-v-n"), extend=0.04)
    # stern post: from the heel up into the counter, the rudder hangs on it
    round_beam(hull, "stern_post", (0, DEADWOOD_HEEL - 0.12, -ws.HALF_LENGTH + 0.02), (0, 1.8, -ws.HALF_LENGTH - 0.06), 0.38,
               "white_bottom")

    # ---- castle bulwarks above the sheer: black, ochre band, gold cap
    def bulwark(bone, tag, z0, z1, top_y, windows=()):
        zs = [z0] + [z for z in STATIONS if z0 < z < z1] + [z1]
        for side, sn in SIDES:
            for i in range(len(zs) - 1):
                za, zb = zs[i], zs[i + 1]
                xa, xb = side * 0.975 * hw(za), side * 0.975 * hw(zb)
                a0, a1 = v3(xa, ws.sheer_y(za) - 0.05, za), v3(xa, top_y, za)
                b0, b1 = v3(xb, ws.sheer_y(zb) - 0.05, zb), v3(xb, top_y, zb)
                board(bone, "%s_wall_%s%d" % (tag, sn, i), a0, a1, b0, b1, 0.14, "hull_black", v3(side, 0, 0), inner="hull_light")
                bevel_beam(bone, "%s_cap_%s%d" % (tag, sn, i), (xa, top_y + 0.09, za), (xb, top_y + 0.09, zb), 0.18, 0.36,
                           "red_paint", c=0.08, extend=0.06)
                beam(bone, "%s_band_%s%d" % (tag, sn, i), (xa + side * 0.08, top_y - 0.45, za), (xb + side * 0.08, top_y - 0.45, zb),
                     0.22, "ochre", width=0.1, extend=0.04)
            for j, z in enumerate(windows):
                gn.decal(bone, "%s_window_%s%d" % (tag, sn, j), z, top_y - 1.25, side, 0.55, 0.85, "arch_window", glow=True)
            # gilded pilasters along the castle side, between the windows
            zp = z0 + 0.6
            k = 0
            while zp < z1 - 0.4:
                if all(abs(zp - w) > 0.55 for w in windows):
                    hgt = top_y - ws.sheer_y(zp) - 0.2
                    if hgt > 0.5:
                        gn.decal(bone, "%s_pilaster_%s%d" % (tag, sn, k), zp, ws.sheer_y(zp) + hgt / 2, side, 0.16, hgt, "pilaster",
                                 out=0.03, th=0.05)
                        k += 1
                zp += 1.25

    bulwark(stern, "poop", -ws.HALF_LENGTH, ws.POOP_START, ws.POOP_RAIL_Y, windows=(-21.0, -23.0))
    bulwark(stern, "qd", ws.POOP_START, ws.QUARTERDECK_START, ws.QD_RAIL_Y, windows=(-12.0, -14.5, -17.0))
    bulwark(fore, "fc", ws.FORECASTLE_START, 28.38, ws.FC_RAIL_Y, windows=(20.5, 23.0))

    # where a raised castle meets a lower rail, its bulwark comes down in a long ogee sweep (S curve)
    # instead of a square step: the wall, the red cap, the ochre band follow it, a gilded scroll at its foot
    def sweep(bone, tag, z_e, length, direction, high, low_fn):
        n = 10
        zs = [z_e + direction * length * k / n for k in range(n + 1)]

        def og(t):
            return 0.5 * (1 + math.cos(math.pi * t))

        def cap_y(k):
            t = k / n
            return low_fn(zs[k]) + (high - low_fn(zs[k])) * og(t)

        for side, sn in SIDES:
            for k in range(n):
                za, zb = zs[k], zs[k + 1]
                xa, xb = side * 0.975 * hw(za), side * 0.975 * hw(zb)
                ya, yb = cap_y(k), cap_y(k + 1)
                la, lb = low_fn(za), low_fn(zb)
                if ya - la > 0.04:
                    board(bone, "%s_sweep_wall_%s%d" % (tag, sn, k), v3(xa, la - 0.12, za), v3(xa, ya, za), v3(xb, lb - 0.12, zb),
                          v3(xb, max(yb, lb + 0.02), zb), 0.14, "hull_black", v3(side, 0, 0), inner="hull_light")
                bevel_beam(bone, "%s_sweep_cap_%s%d" % (tag, sn, k), (xa, ya + 0.09, za), (xb, yb + 0.09, zb), 0.18, 0.36,
                           "red_paint", c=0.08, extend=0.05)
                if ya - 0.45 > la + 0.05:
                    yb2 = max(yb - 0.45, lb + 0.05)
                    beam(bone, "%s_sweep_band_%s%d" % (tag, sn, k), (xa + side * 0.08, ya - 0.45, za), (xb + side * 0.08, yb2, zb),
                         0.22, "ochre", width=0.1, extend=0.03)
            # gilded scroll (volute) where the sweep runs out on the lower rail
            zf = z_e + direction * length * 0.82
            xf = side * (0.975 * hw(zf) + 0.1)
            yf = low_fn(zf) + 0.32
            round_beam(bone, "%s_sweep_scroll_%s" % (tag, sn), (xf - side * 0.06, yf, zf), (xf + side * 0.06, yf, zf), 0.36, "gold",
                       up=v3(0, 0, 1))
            round_beam(bone, "%s_sweep_scroll_eye_%s" % (tag, sn), (xf, yf, zf), (xf + side * 0.1, yf, zf), 0.16, "gold_relief",
                       up=v3(0, 0, 1))

    sweep(stern, "poop", ws.POOP_START, SWEEP_POOP, 1, ws.POOP_RAIL_Y, lambda z: ws.QD_RAIL_Y)
    sweep(stern, "qd", ws.QUARTERDECK_START, SWEEP_QD, 1, ws.QD_RAIL_Y, ws.sheer_y)
    sweep(fore, "fc", ws.FORECASTLE_START, SWEEP_FC, -1, ws.FC_RAIL_Y, ws.sheer_y)

    # ---- decks
    def deck_span(bone, z0, z1, n, y, tag):
        for j in range(n):
            za = z0 + (z1 - z0) * j / n
            zb = z0 + (z1 - z0) * (j + 1) / n
            w = max(ws.inner_half_width(za), ws.inner_half_width(zb)) + 0.1
            add_cube(bone, "deck_%s%d" % (tag, j), (0, y - 0.075, (za + zb) / 2), EYE, (2 * w, 0.15, zb - za + 0.02),
                     {"all": "deck", "-2": "dark_wood"})

    deck_span(deck, ws.TRANSOM_Z, ws.FORECASTLE_START, 18, main_y, "main")
    deck_span(fore, ws.FORECASTLE_START, ws.DECK_MAX_Z, 5, fc_y, "fore")
    deck_span(stern, ws.TRANSOM_Z, ws.QUARTERDECK_START, 8, qd_y, "quarter")
    deck_span(stern, ws.TRANSOM_Z, ws.POOP_START, 4, poop_y, "poop")
    # forecastle front wall
    wf = ws.inner_half_width(ws.FORECASTLE_START) + 0.12
    add_cube(fore, "fc_front", (0, (main_y + fc_y) / 2, ws.FORECASTLE_START), EYE, (2 * wf, fc_y - main_y, 0.16),
             {"all": "hull_black", "+3": "hull_light"})
    add_cube(fore, "fc_front_door", (0, main_y + 0.85, ws.FORECASTLE_START - 0.09), EYE, (0.9, 1.65, 0.04), "door", stretch=True)
    for side, sn in SIDES:
        add_cube(fore, "fc_front_window_" + sn, (side * 1.0, main_y + 1.35, ws.FORECASTLE_START - 0.09), EYE, (0.45, 0.45, 0.04),
                 "window", stretch=True)
    # great cabin bulkhead (door) and the front of the upper cabin under the poop deck
    bz0, bz1 = ws.QUARTERDECK_START - ws.BULKHEAD_THICK, ws.QUARTERDECK_START
    bw = ws.inner_half_width(bz0) + 0.12
    slab_bottom = qd_y - ws.SLAB
    for side, sn in SIDES:
        add_cube(cabin, "bulkhead_" + sn, (side * (ws.DOOR_HALF + bw) / 2, (main_y + slab_bottom) / 2, (bz0 + bz1) / 2), EYE,
                 (bw - ws.DOOR_HALF, slab_bottom - main_y, bz1 - bz0), {"all": "hull_black", "-3": "hull_light"})
        add_cube(cabin, "bulkhead_jamb_" + sn, (side * (ws.DOOR_HALF + 0.07), (main_y + ws.DOOR_TOP) / 2, bz1 + 0.02), EYE,
                 (0.14, ws.DOOR_TOP - main_y, 0.08), "gold")
        for j, x in enumerate((2.0, 3.6, 5.0)):
            add_cube(cabin, "glow_bulkhead_window_%s%d" % (sn, j), (side * x, main_y + 1.4, bz1 + 0.02), EYE, (0.6, 0.85, 0.05),
                     "arch_window", stretch=True)
            add_cube(cabin, "bulkhead_window_in_%s%d" % (sn, j), (side * x, main_y + 1.4, bz0 - 0.02), EYE, (0.6, 0.85, 0.03),
                     {"all": None, "-3": "arch_window_in"}, stretch=True)
            add_cube(cabin, "bulkhead_pilaster_%s%d" % (sn, j), (side * (x + 0.6), (main_y + slab_bottom) / 2, bz1 + 0.04), EYE,
                     (0.12, slab_bottom - main_y, 0.08), "pilaster", stretch=True)
    add_cube(cabin, "bulkhead_lintel", (0, (ws.DOOR_TOP + slab_bottom) / 2, (bz0 + bz1) / 2), EYE,
             (2 * ws.DOOR_HALF, slab_bottom - ws.DOOR_TOP, bz1 - bz0), "hull_black")
    add_cube(cabin, "bulkhead_arch", (0, ws.DOOR_TOP + 0.07, bz1 + 0.03), EYE, (2 * ws.DOOR_HALF + 0.3, 0.14, 0.1), "gold")
    add_cube(stern, "quarterdeck_edge", (0, qd_y - 0.15, bz1 + 0.02), EYE, (2 * bw, 0.3, 0.06), "carving", stretch=True)
    pw = ws.inner_half_width(ws.POOP_START) + 0.12
    add_cube(stern, "poop_front", (0, (qd_y + poop_y) / 2, ws.POOP_START + 0.0), EYE, (2 * pw, poop_y - qd_y, 0.12),
             {"all": "hull_black"})
    add_cube(stern, "poop_front_door", (0, qd_y + 0.95, ws.POOP_START + 0.07), EYE, (0.9, 1.75, 0.04), "door", stretch=True)
    for side, sn in SIDES:
        for j, x in enumerate((1.6, 4.5)):
            add_cube(stern, "glow_poop_front_window_%s%d" % (sn, j), (side * x, qd_y + 1.2, ws.POOP_START + 0.07), EYE,
                     (0.6, 0.95, 0.04), "arch_window", stretch=True)
        add_cube(stern, "poop_front_pilaster_" + sn, (side * 0.75, (qd_y + poop_y) / 2, ws.POOP_START + 0.08), EYE,
                 (0.22, poop_y - qd_y, 0.06), "pilaster", stretch=True)
    add_cube(stern, "poop_front_cornice", (0, poop_y - 0.12, ws.POOP_START + 0.08), EYE, (2 * pw, 0.18, 0.1), "carving", stretch=True)

    # ---- great cabin interior
    for side, sn in SIDES:
        x, z = side * 3.0, -16.0
        add_cube(cabin, "chair_seat_" + sn, (x, main_y + 0.42, z), EYE, (0.6, 0.08, 0.6), "red_paint")
        add_cube(cabin, "chair_back_" + sn, (x + side * 0.27, main_y + 0.85, z), EYE, (0.08, 0.8, 0.6), "red_paint")
        for dx in (-0.24, 0.24):
            for dz in (-0.24, 0.24):
                add_cube(cabin, "chair_leg_%s%d%d" % (sn, int(dx > 0), int(dz > 0)), (x + dx, main_y + 0.19, z + dz), EYE,
                         (0.07, 0.38, 0.07), "dark_wood")
        add_cube(lanterns, "cabin_lantern_" + sn, (side * 1.25, main_y + 1.9, bz0 - 0.2), EYE, (0.3, 0.42, 0.3),
                 {"all": "lantern", "+2": "iron", "-2": "iron"}, stretch=True)
        add_cube(lanterns, "glow_cabin_lantern_" + sn, (side * 1.25, main_y + 1.9, bz0 - 0.2), EYE, (0.2, 0.3, 0.2), "glow", stretch=True)
        add_cube(cabin, "cabin_chest_" + sn, (side * 4.6, main_y + 0.3, -21.0), EYE, (0.6, 0.6, 1.1), {"all": "dark_wood", "+2": "iron"})
    for k, z in enumerate((-13.0, -17.5, -22.0, -25.5)):
        w = ws.inner_half_width(z)
        add_cube(cabin, "cabin_beam_%d" % k, (0, slab_bottom - 0.1, z), EYE, (2 * w, 0.2, 0.28), "dark_wood")
    # windows along the great cabin (lit outside, daylight inside), under the castle windows
    for side, sn in SIDES:
        for j, z in enumerate(CABIN_WINDOWS_Z):
            wy = max(CABIN_WINDOW_Y, 5.05 + lift(z))   # clear of the upper wale, which rises aft
            gn.decal(cabin, "cabin_window_%s%d" % (sn, j), z, wy, side, 0.7, 0.85, "glow_window", glow=True, out=0.06)
            gn.decal(cabin, "cabin_window_frame_%s%d" % (sn, j), z, wy, side, 0.86, 1.0, "gold", out=-0.06, th=0.13)
            gn.inner_decal(cabin, "cabin_window_in_%s%d" % (sn, j), z, wy, side, 0.7, 0.85, "window_in", wall=0.175)
    # the great cabin: council table with its chairs on a carpet, candelabras, chart and dinner,
    # captain's bed, desk and globe, bookshelf, weapon rack, paintings, hanging lanterns
    sd.rug(gg, cabin, "cabin_rug", (0, main_y, -21.5), 3.0, 6.0)
    sd.table(gg, cabin, "council_table", (0, main_y, -21.5), 1.4, 4.4, h=0.8, top="dark_wood", legs="dark_wood")
    tt = main_y + 0.8
    for side, sn in SIDES:
        for j, z in enumerate((-22.9, -21.5, -20.1)):
            sd.chair(gg, cabin, "council_chair_%s%d" % (sn, j), (side * 1.05, main_y, z), -side * math.pi / 2, seat="red_paint")
    sd.chair(gg, cabin, "council_chair_head", (0, main_y, -24.3), 0.0, seat="red_paint")
    sd.chair(gg, cabin, "council_chair_foot", (0, main_y, -18.7), math.pi, seat="red_paint")
    sd.candelabra(gg, cabin, "candelabra_0", (0, tt, -22.75))
    sd.candelabra(gg, cabin, "candelabra_1", (0, tt, -20.25))
    sd.chart_on_table(gg, cabin, "council_chart", (0, tt, -21.5))
    sd.tableware(gg, cabin, "council_dinner_0", (0.3, tt, -19.8), yaw=math.pi)
    sd.tableware(gg, cabin, "council_dinner_1", (-0.3, tt, -23.2))
    sd.chandelier(gg, cabin, "council_chandelier", (0, slab_bottom - 0.12, -21.5), drop=0.5, r=0.55, n=10)
    # wardroom in the fore part of the cabin: a round table round the mizzen with stools, sideboards
    # against the bulkhead, panelled walls with a gilded rail under the windows
    mz = ws.MIZZEN_Z
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        R8 = gg.ry(-a)
        add_cube(cabin, "mast_table_%d" % k, (math.sin(a) * 0.62, main_y + 0.76, mz + math.cos(a) * 0.62), R8, (0.55, 0.06, 0.62),
                 {"all": "dark_wood", "+2": "hull_light"})
    add_cube(cabin, "mast_table_foot", (0, main_y + 0.37, mz), EYE, (1.0, 0.74, 1.0), "dark_wood")
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        sd.stool(gg, cabin, "mast_stool_%d" % k, (math.sin(a) * 1.35, main_y, mz + math.cos(a) * 1.35), top="red_paint")
    sd.tableware(gg, cabin, "mast_dinner_0", (0.55, main_y + 0.79, mz + 0.35), yaw=0.6)
    sd.tableware(gg, cabin, "mast_dinner_1", (-0.55, main_y + 0.79, mz - 0.35), yaw=3.7)
    sd.candle(gg, cabin, "mast_candle_0", (0.6, main_y + 0.79, mz - 0.4))
    sd.candle(gg, cabin, "mast_candle_1", (-0.6, main_y + 0.79, mz + 0.4))
    for side, sn in SIDES:
        sd.sideboard(gg, cabin, "sideboard_" + sn, (side * 2.6, main_y, bz0 - 0.3), yaw=math.pi, w=1.2)
        sd.candle(gg, cabin, "sideboard_candle_" + sn, (side * 2.3, main_y + 0.9, bz0 - 0.3))
        gn.wainscot(cabin, "cabin_wainscot_" + sn, bz0 - 0.2, -25.8, main_y + 0.12, main_y + 0.62, side, wall=0.14)
    for side, sn in SIDES:
        sd.hanging_lantern(gg, lanterns, "cabin_hanging_lantern_" + sn, (side * 2.4, slab_bottom - 0.2, -17.5), drop=0.15)
        # paintings: on the bulkhead between its windows and on the side walls between the windows
        sd.painting(gg, cabin, "bulkhead_painting_" + sn, (side * 2.8, main_y + 1.4, bz0), (0, 0, -1), w=0.7, h=0.55)
        p, u, v, n = gn.side_frame(-15.75, 5.85, side)
        sd.painting(gg, cabin, "cabin_painting_" + sn, p - n * 0.16, -n, w=0.9, h=0.65)

    def wall_x(z, y):
        return outer_x(z, y) - 0.16

    sd.bookshelf(gg, cabin, "cabin_books", (wall_x(-19.0, 6.4) - 0.2, main_y, -19.0), yaw=-math.pi / 2, w=1.4, h=1.95, d=0.36)
    sd.weapon_rack(gg, cabin, "cabin_arms", (-wall_x(-19.0, 6.0), main_y, -19.0), (1, 0, 0), w=1.2)
    sd.bunk(gg, cabin, "captain_bed", (-(wall_x(-25.4, 5.0) - 0.55), main_y, -24.5), l=1.9, w=1.0, bedding="bedding")
    for k, y in enumerate((main_y + 1.5, main_y + 1.62)):
        add_cube(cabin, "captain_bed_canopy_%d" % k, (-(wall_x(-25.4, 5.0) - 0.55), y, -24.5), EYE, (1.0 - 0.1 * k, 0.08, 1.9 - 0.1 * k),
                 "red_paint")
    for k, dz in enumerate((-0.9, 0.9)):
        add_cube(cabin, "captain_bed_post_%d" % k, (-(wall_x(-25.4, 5.0) - 1.0), main_y + 0.8, -24.5 + dz), EYE, (0.08, 1.6, 0.08),
                 "dark_wood")
    dx = wall_x(-24.6, 5.0) - 0.35
    sd.table(gg, cabin, "captain_desk", (dx, main_y, -24.6), 0.6, 1.0, h=0.78)
    sd.chair(gg, cabin, "captain_desk_chair", (dx - 0.6, main_y, -24.6), math.pi / 2, seat="red_paint")
    sd.globe(gg, cabin, "captain_globe", (dx, main_y + 0.78, -24.95), sea="window", metal="gold")
    sd.candle(gg, cabin, "captain_candle", (dx + 0.05, main_y + 0.78, -24.3))

    # ---- stairs (match the collision boxes) and guard rails
    d = ws.STEP_DEPTH
    for k in range(1, 6):
        for side, sn in SIDES:
            top = main_y + (qd_y - main_y) * k / 5.0
            zf = ws.QD_STAIR_START - (k - 1) * d
            add_cube(deck, "qd_step_%s%d" % (sn, k), (side * (ws.QD_STAIR_X0 + ws.QD_STAIR_X1) / 2, (main_y + top) / 2, zf - d / 2),
                     EYE, (ws.QD_STAIR_X1 - ws.QD_STAIR_X0, top - main_y, d), {"all": "dark_wood", "+2": "deck"})
            top = qd_y + (poop_y - qd_y) * k / 5.0
            zp = ws.POOP_STAIR_START - (k - 1) * d
            add_cube(stern, "poop_step_%s%d" % (sn, k), (side * (ws.POOP_STAIR_X0 + ws.POOP_STAIR_X1) / 2, (qd_y + top) / 2, zp - d / 2),
                     EYE, (ws.POOP_STAIR_X1 - ws.POOP_STAIR_X0, top - qd_y, d), {"all": "dark_wood", "+2": "deck"})
            top = main_y + (fc_y - main_y) * k / 5.0
            zb = ws.FC_STAIR_START + (k - 1) * d
            add_cube(fore, "fc_step_%s%d" % (sn, k), (side * (ws.FC_STAIR_X0 + ws.FC_STAIR_X1) / 2, (main_y + top) / 2, zb + d / 2),
                     EYE, (ws.FC_STAIR_X1 - ws.FC_STAIR_X0, top - main_y, d), {"all": "dark_wood", "+2": "deck"})
    for side, sn in SIDES:
        beam(deck, "qd_handrail_" + sn, (side * ws.QD_STAIR_X0, main_y + 0.9, ws.QD_STAIR_START),
             (side * ws.QD_STAIR_X0, qd_y + 0.9, ws.QUARTERDECK_START), 0.08, "rail")
        beam(stern, "poop_handrail_" + sn, (side * ws.POOP_STAIR_X0, qd_y + 0.9, ws.POOP_STAIR_START),
             (side * ws.POOP_STAIR_X0, poop_y + 0.9, ws.POOP_START), 0.08, "rail")
        beam(fore, "fc_handrail_" + sn, (side * ws.FC_STAIR_X0, main_y + 0.9, ws.FC_STAIR_START),
             (side * ws.FC_STAIR_X0, fc_y + 0.9, ws.FORECASTLE_START), 0.08, "rail")

    def guard_rail(bone, tag, half, y, z):
        beam(bone, tag + "_top", (-half, y + ws.RAIL_HEIGHT - 0.05, z), (half, y + ws.RAIL_HEIGHT - 0.05, z), 0.1, "red_paint",
             width=ws.RAIL_THICK, extend=0.05)
        for j, x in enumerate(np.linspace(-half, half, 9)):
            beam(bone, "%s_baluster_%d" % (tag, j), (x, y, z), (x, y + ws.RAIL_HEIGHT - 0.1, z), 0.1, "red_paint")

    guard_rail(stern, "qd_rail", ws.QD_STAIR_X0 - 0.1, qd_y, ws.QUARTERDECK_START - ws.RAIL_THICK / 2)
    guard_rail(stern, "poop_rail", ws.POOP_STAIR_X0 - 0.1, poop_y, ws.POOP_START - ws.RAIL_THICK / 2)
    guard_rail(fore, "fc_rail", ws.FC_STAIR_X0 - 0.1, fc_y, ws.FORECASTLE_START + ws.RAIL_THICK / 2)
    for j, z in enumerate((-2.0, 6.0, 12.5)):
        add_cube(deck, "hatch_%d" % j, (0, main_y + 0.04, z), EYE, (1.6, 0.08, 1.6), {"all": "dark_wood", "+2": "grating"})
    add_cube(deck, "capstan", (0, main_y + 0.45, -5.5), EYE, (0.8, 0.9, 0.8), {"all": "dark_wood", "+2": "end_grain"})
    # deck details: pin rails at the three mast feet, belfry, barrels, crates, coils, buckets
    sd.fife_rail(gg, deck, "fife_main", 0.0, ws.MAIN_MAST_Z, main_y, half=1.15)
    sd.fife_rail(gg, fore, "fife_fore", 0.0, ws.FORE_MAST_Z, fc_y, half=1.0)
    sd.fife_rail(gg, stern, "fife_mizzen", 0.0, ws.MIZZEN_Z, qd_y, half=0.9)
    sd.bell(gg, fore, "belfry", (0.0, fc_y, 19.7))
    for k, (x, z) in enumerate(((4.4, 15.9), (-4.4, 15.9), (4.0, 15.2), (-4.0, 15.25))):
        sd.barrel(gg, deck, "barrel_%d" % k, (x, main_y, z), wood="dark_wood", ends="end_grain")
    sd.lying_barrel(gg, deck, "barrel_lying", (4.6, main_y, -8.9), yaw=0.0, wood="dark_wood")
    for k, x in enumerate((5.1, -5.1)):
        sd.crate(gg, deck, "crate_%d" % k, (x, main_y, -5.25), s=0.62, yaw=0.1 * k)
    sd.crate(gg, deck, "crate_top", (5.1, main_y + 0.62, -5.25), s=0.45, yaw=0.3)
    sd.rope_coil(gg, deck, "coil_0", (1.9, main_y, 2.7))
    sd.rope_coil(gg, deck, "coil_1", (-1.9, main_y, -0.6))
    sd.rope_coil(gg, fore, "coil_fc", (1.6, fc_y, 21.5), r=0.3)
    sd.rope_coil(gg, stern, "coil_qd", (-1.5, qd_y, -16.5), r=0.3)
    sd.bucket(gg, deck, "bucket_0", (-1.4, main_y, 2.6), wood="dark_wood")
    sd.bucket(gg, deck, "bucket_1", (1.5, main_y, -0.9), wood="dark_wood")
    boat = Bone("ship_boat", parent=deck)
    bz0, bz1, bh = ws.BOAT_Z0, ws.BOAT_Z1, ws.BOAT_HALF
    for zz in (bz0 + 0.5, bz1 - 0.5):
        add_cube(boat, "boat_skid_%d" % int(zz > 8), (0, main_y + 0.3, zz), EYE, (2 * bh + 0.6, 0.6, 0.3), "dark_wood")
    bot, top = main_y + 0.62, ws.BOAT_TOP

    def bw(t):
        return bh * max(0.08, 1 - (2 * t - 1) ** 2) ** 0.5

    nst = 6
    for side, sn in SIDES:
        for j in range(nst):
            ta, tb = j / nst, (j + 1) / nst
            za, zb = bz0 + (bz1 - bz0) * ta, bz0 + (bz1 - bz0) * tb
            a0, a1 = v3(side * 0.35 * bw(ta), bot, za), v3(side * bw(ta), top, za)
            b0, b1 = v3(side * 0.35 * bw(tb), bot, zb), v3(side * bw(tb), top, zb)
            board(boat, "boat_side_%s%d" % (sn, j), a0, a1, b0, b1, 0.08, "white_bottom", v3(side, 0, 0), inner="hull_light")
            beam(boat, "boat_gunwale_%s%d" % (sn, j), (side * bw(ta), top + 0.04, za), (side * bw(tb), top + 0.04, zb), 0.08, "ochre",
                 width=0.12, extend=0.04)
    add_cube(boat, "boat_bottom", (0, bot + 0.03, (bz0 + bz1) / 2), EYE, (0.75 * bh, 0.08, bz1 - bz0 - 0.8), "dark_wood")
    for k, zz in enumerate(np.linspace(bz0 + 1.4, bz1 - 1.4, 3)):
        add_cube(boat, "boat_thwart_%d" % k, (0, top - 0.35, zz), EYE, (1.7 * bw((zz - bz0) / (bz1 - bz0)), 0.08, 0.3), "hull_light")
    for side, sn in SIDES:
        beam(boat, "boat_oar_" + sn, (side * 0.35, top - 0.25, bz0 + 0.9), (side * 0.25, top - 0.2, bz1 - 0.9), 0.08, "hull_light")
    for side, sn in SIDES:
        # entry port with its steps on the hull side
        zz = 5.25
        gn.decal(hull, "entry_port_" + sn, zz, 5.0, side, 0.9, 1.0, "door", out=0.02)
        gn.decal(hull, "entry_pediment_" + sn, zz, 5.52, side, 1.3, 0.28, "gold_relief", out=0.04, th=0.06)
        for k, y in enumerate((4.2, 3.65, 3.1, 2.55)):
            p, u, v, nrm = gn.side_frame(zz, y, side)
            add_cube(hull, "entry_step_%s%d" % (sn, k), p + nrm * 0.1, np.column_stack([u, v, nrm]), (0.6, 0.1, 0.2), "dark_wood")
    for k in range(4):
        a = math.pi * k / 4
        beam(deck, "capstan_bar_%d" % k, (-math.cos(a) * 0.95, main_y + 0.8, -5.5 - math.sin(a) * 0.95),
             (math.cos(a) * 0.95, main_y + 0.8, -5.5 + math.sin(a) * 0.95), 0.08, "hull_light")

    # ---- guns: one bone per gun port (same order as ShipGeometry.gunports())
    gun_index = {1: 0, -1: 0}

    def gun(side, z, y, on_deck=False):
        tag = "l" if side > 0 else "r"
        gun_index[side] += 1
        n = gun_index[side]
        p, u, v, nrm = gn.side_frame(z, y, side)
        gn.decal(guns, "gunport_%s%d" % (tag, n), z, y, side, 0.8, 0.74, "gunport", out=0.0)
        cb = Bone("cannon_%s%d" % (tag, n), origin=tuple(p), parent=guns)
        if on_deck:
            gn.decal(guns, "garland_%s%d" % (tag, n), z, y, side, 1.25, 1.2, "garland", out=0.02, th=0.03)
            inner = ws.inner_half_width(z)
            x_in = side * (inner - 1.2)
            beam(cb, "cannon_barrel_%s%d" % (tag, n), (x_in, y, z), p + nrm * 0.65, 0.3, "cannon")
            add_cube(cb, "cannon_carriage_%s%d" % (tag, n), (side * (inner - 0.7), main_y + 0.3, z), EYE, (1.2, 0.6, 0.9),
                     {"all": "dark_wood", "+2": "hull_light"})
            for dz in (-0.42, 0.42):
                for dx in (-0.35, 0.35):
                    add_cube(cb, "cannon_wheel_%s%d_%d%d" % (tag, n, int(dz > 0), int(dx > 0)),
                             (side * (inner - 0.7) + dx, main_y + 0.17, z + dz), EYE, (0.3, 0.3, 0.1), "end_grain")
        else:
            beam(cb, "cannon_barrel_%s%d" % (tag, n), p - nrm * 0.1, p + nrm * 0.75, 0.3, "cannon")
            add_cube(cb, "cannon_muzzle_%s%d" % (tag, n), p + nrm * 0.72, np.column_stack([u, v, nrm]), (0.38, 0.38, 0.08), "iron")

    for side, sn in SIDES:
        for k in range(ws.LOWER_GUNS):
            z = ws.gun_z(k, ws.LOWER_GUNS)
            gun(side, z, ws.LOWER_GUN_Y + lift(z))
        for k in range(ws.MIDDLE_GUNS):
            z = ws.gun_z(k, ws.MIDDLE_GUNS)
            gun(side, z, ws.MIDDLE_GUN_Y + lift(z))
        for z in ws.CARRIAGE_Z:
            gun(side, z, ws.MAIN_GUN_Y, on_deck=True)

    # ---- stern: bow-fronted transom on a curved counter, three tiers of windows, curved galleries,
    # rounded quarter galleries, coat of arms
    zt = ZT
    lt = lift(zt)
    counter = [0.3, 1.0 + lt, 2.05 + lt, 2.6 + lt]
    bottom_ys = [y for x, y in section_xy(zt) if y < 0.3 and x > 0.35]
    low = bottom_ys + [0.3] + list(np.linspace(0.3, counter[1], 5))[1:]
    rows = [low[0]]
    for a, b in zip(low, low[1:]):   # thin rows where the stern widens fast, so that the boards stay true
        n = 1 if b >= 1.6 else (3 if a >= 0.0 else 2)
        rows += [a + (b - a) * (k + 1) / n for k in range(n)]
    rows += counter[2:] + list(np.linspace(counter[-1], ws.POOP_RAIL_Y, 11))[1:]
    fr = np.linspace(-1, 1, 11)
    for k in range(len(rows) - 1):
        y0, y1 = rows[k], rows[k + 1]
        ym = (y0 + y1) / 2
        if ym < 0.3:
            reg = "white_bottom"
        else:
            reg = "ochre" if counter[1] < ym < counter[2] else "hull_black"
        inside = ym > main_y - 0.2
        w0, w1 = stern_w(y0), stern_w(y1)
        for j in range(len(fr) - 1):
            a0, a1 = stern_pt(fr[j] * w0, y0), stern_pt(fr[j] * w1, y1)
            b0, b1 = stern_pt(fr[j + 1] * w0, y0), stern_pt(fr[j + 1] * w1, y1)
            board(stern, "transom_%d_%d" % (k, j), a0, a1, b0, b1, 0.24, reg, v3(0, 0, -1),
                  inner="hull_light" if inside else None)
    # the stern's own decks reach back into the bow of the transom
    for tag, y in (("main", main_y), ("qd", qd_y), ("poop", poop_y)):
        w = stern_w(y)
        xs = np.linspace(-w, w, 17)
        for j in range(16):
            xo = xs[j] if abs(xs[j]) > abs(xs[j + 1]) else xs[j + 1]
            z_aft = stern_z(xo, y) + 0.03
            if z_aft > ws.TRANSOM_Z - 0.05:
                continue
            add_cube(stern, "stern_deck_%s_%d" % (tag, j), ((xs[j] + xs[j + 1]) / 2, y - 0.075, (z_aft + ws.TRANSOM_Z + 0.04) / 2), EYE,
                     (xs[j + 1] - xs[j] + 0.01, 0.15, ws.TRANSOM_Z + 0.04 - z_aft), {"all": "dark_wood", "+2": "deck"})
    for j, y in enumerate(counter[1:]):
        w = stern_w(y) + 0.04
        if j == 1:
            sband(stern, "transom_moulding", y, 0.07, 0.03, 0.06, "gold", -w, w, n=10)
        else:
            xs = np.linspace(-w, w, 11)
            for q in range(10):
                pa, pb = stern_pt(xs[q], y), stern_pt(xs[q + 1], y)
                o = stern_frame((xs[q] + xs[q + 1]) / 2, y)[2]
                bevel_beam(stern, "transom_wale_%d_%d" % (j, q), pa + o * 0.05, pb + o * 0.05, 0.2, 0.2, "wale", c=0.07,
                           corners=("+v+n", "-v+n"), extend=0.03, out_hint=o)
    # stern chasers: two guns firing aft through the counter
    for side, sn in SIDES:
        y = (counter[1] + counter[2]) / 2
        x = side * 1.6
        p, R, o = stern_frame(x, y)
        scube(stern, "stern_chaser_port_" + sn, x, y, 0.01, (0.72, 0.66, 0.04), "gunport", stretch=True)
        beam(stern, "stern_chaser_" + sn, p - o * 0.1, p + o * 0.75, 0.3, "cannon")
        add_cube(stern, "stern_chaser_muzzle_" + sn, p + o * 0.72, R, (0.38, 0.38, 0.08), "iron")
        scube(stern, "stern_chaser_garland_" + sn, x, y, 0.025, (1.15, 1.0, 0.02), "garland", stretch=True)
    # carved name board across the counter, under the lowest gallery
    sband(stern, "counter_board", counter[3] + 0.25, 0.36, 0.04, 0.08, "gold_relief", -1.3, 1.3, n=4, stretch=True)
    for side, sn in SIDES:
        scube(stern, "counter_scroll_" + sn, side * 1.55, counter[3] + 0.25, 0.05, (0.5, 0.46, 0.1), "gold")
    tiers = ((5.0, 1.15, main_y), (7.75, 1.05, qd_y), (9.75, 0.6, poop_y))
    for t, (yc, h, floor) in enumerate(tiers):
        xs = (-2.7, -1.35, 0.0, 1.35, 2.7) if t < 2 else (-2.0, -0.7, 0.7, 2.0)
        for j, x in enumerate(xs):
            scube(stern, "glow_stern_window_%d_%d" % (t, j), x, yc, 0.03, (0.85, h, 0.06),
                  "arch_window" if t == 2 else "glow_window", stretch=True)
            scube(stern, "stern_window_frame_%d_%d" % (t, j), x, yc, 0.01, (1.02, h + 0.16, 0.04), "gold")
            if t < 2:
                scube(stern, "stern_window_sill_%d_%d" % (t, j), x, yc - h / 2 - 0.08, 0.08, (1.08, 0.08, 0.16), "gold")
                scube(stern, "stern_window_key_%d_%d" % (t, j), x, yc + h / 2 + 0.06, 0.08, (0.24, 0.18, 0.1),
                      "gold_relief", stretch=True)
            if t == 0:
                scube(cabin, "stern_window_in_%d" % j, x, yc, -0.26, (0.85, h, 0.03), {"all": None, "+3": "window_in"}, stretch=True)
        for j in range(len(xs) + 1):
            x = (xs[0] - 0.68) + j * (xs[1] - xs[0])
            scube(stern, "stern_pilaster_%d_%d" % (t, j), x, yc, 0.05, (0.18, h + 0.3, 0.08), "pilaster", stretch=True)
        w = stern_w(yc)
        sband(stern, "stern_cornice_%d" % t, yc + h / 2 + 0.22, 0.2, 0.06, 0.14, "gold", -w - 0.05, w + 0.05, n=10)
        sband(stern, "stern_frieze_%d" % t, yc - h / 2 - 0.22, 0.3, 0.05, 0.1, "gold_relief", -w, w, n=10)
        if t < 2:
            # stern gallery (balcony) under the windows, bowed out further than the stern itself
            gy = floor + 0.05
            gx = stern_w(yc) - 0.2

            def zo(x, gy=gy, gx=gx):
                f = min(1.0, (x / gx) ** 2)
                return stern_z(x, gy) - (0.55 + 0.4 * (1 - f))

            gxs = list(gx * np.sin(np.linspace(-math.pi / 2, math.pi / 2, 13)))
            for j in range(len(gxs) - 1):
                xa, xb = gxs[j], gxs[j + 1]
                c = board(stern, "stern_gallery_%d_%d" % (t, j), v3(xa, gy, stern_z(xa, gy) + 0.1), v3(xa, gy, zo(xa)),
                          v3(xb, gy, stern_z(xb, gy) + 0.1), v3(xb, gy, zo(xb)), 0.16, "dark_wood", v3(0, 1, 0))
                c.faces[gg.SEMANTIC_FACE["+3"]]["region"] = "deck"
                board(stern, "stern_gallery_fascia_%d_%d" % (t, j), v3(xa, gy - 0.28, zo(xa)), v3(xa, gy - 0.04, zo(xa)),
                      v3(xb, gy - 0.28, zo(xb)), v3(xb, gy - 0.04, zo(xb)), 0.08, "gold_relief", v3(0, 0, -1))
                beam(stern, "stern_gallery_rail_%d_%d" % (t, j), (xa, gy + 0.75, zo(xa) + 0.04), (xb, gy + 0.75, zo(xb) + 0.04),
                     0.1, "gold", width=0.14, extend=0.03)
            for j, x in enumerate(np.linspace(-gx + 0.12, gx - 0.12, 17)):
                beam(stern, "stern_gallery_baluster_%d_%d" % (t, j), (x, gy + 0.08, zo(x) + 0.05), (x, gy + 0.7, zo(x) + 0.05),
                     0.08, "gold")
            for side, sn in SIDES:
                xg = side * gx
                beam(stern, "stern_gallery_end_rail_%d_%s" % (t, sn), (xg, gy + 0.75, zo(xg)), (xg, gy + 0.75, stern_z(xg, gy)),
                     0.1, "gold", width=0.12)
                for j, f in enumerate((0.35, 0.68)):
                    z = stern_z(xg, gy) + (zo(xg) - stern_z(xg, gy)) * f
                    beam(stern, "stern_gallery_end_baluster_%d_%s%d" % (t, sn, j), (xg, gy + 0.08, z), (xg, gy + 0.7, z), 0.08, "gold")
                round_beam(stern, "stern_gallery_post_%d_%s" % (t, sn), (xg, gy - 0.3, zo(xg) + 0.04), (xg, gy + 0.9, zo(xg) + 0.04),
                           0.16, "gold_relief")
                round_beam(stern, "stern_gallery_post_cap_%d_%s" % (t, sn), (xg, gy + 0.9, zo(xg) + 0.04),
                           (xg, gy + 1.04, zo(xg) + 0.04), 0.22, "gold")
            for j, x in enumerate((-2.9, -1.0, 1.0, 2.9)):
                beam(stern, "stern_gallery_bracket_%d_%d" % (t, j), stern_pt(x, gy - 0.75) + v3(0, 0, 0.05),
                     (x, gy - 0.12, zo(x) + 0.12), 0.16, "gold_relief", width=0.2)
    # the top of the stern: a moulded cap following its curve
    w = stern_w(ws.POOP_RAIL_Y)
    xs = np.linspace(-w, w, 11)
    for q in range(10):
        pa, pb = stern_pt(xs[q], ws.POOP_RAIL_Y + 0.08), stern_pt(xs[q + 1], ws.POOP_RAIL_Y + 0.08)
        bevel_beam(stern, "taffrail_cap_%d" % q, pa + v3(0, 0, 0.08), pb + v3(0, 0, 0.08), 0.16, 0.34, "red_paint", c=0.08,
                   extend=0.03)

    def dzc(x):
        return stern_z(x, ws.POOP_RAIL_Y) - zt

    # gilded corner columns of the stern (round), carved crest (taffrail) around the arms
    for side, sn in SIDES:
        x = side * (outer_x(zt, 7.0) - 0.15)
        z = stern_z(x, 7.0) - 0.1
        round_beam(stern, "stern_column_" + sn, (x, 4.2, z), (x, ws.POOP_RAIL_Y + 0.2, z), 0.34, "gold_relief")
        round_beam(stern, "stern_column_cap_" + sn, (x, ws.POOP_RAIL_Y + 0.2, z), (x, ws.POOP_RAIL_Y + 0.5, z), 0.5, "gold")
        round_beam(stern, "stern_column_base_" + sn, (x, 3.95, z), (x, 4.25, z), 0.5, "gold")
    for k in range(9):
        a = math.pi * k / 8
        x = math.cos(a) * 2.25
        c = v3(x, ws.POOP_RAIL_Y + 0.35 + math.sin(a) * 1.55, zt + 0.12 + dzc(x))
        add_cube(stern, "taffrail_crest_%d" % k, c, gg.rz(a - math.pi / 2), (0.62, 0.36, 0.2), "gold_relief")
    for side, sn in SIDES:
        add_cube(stern, "taffrail_scroll_" + sn, (side * 2.6, ws.POOP_RAIL_Y + 0.25, zt + 0.12 + dzc(side * 2.6)), EYE,
                 (0.7, 0.4, 0.22), "gold_relief")
    for k in range(6):
        dy0, dy1 = 1.5 * k / 6, 1.5 * (k + 1) / 6
        half = 2.15 * max(0.0, 1 - ((dy0 + dy1) / 2 / 1.55) ** 2) ** 0.5
        add_cube(stern, "crest_plate_%d" % k, (0, ws.POOP_RAIL_Y + 0.35 + (dy0 + dy1) / 2, zt + 0.26 + dzc(0)), EYE,
                 (2 * half, dy1 - dy0 + 0.02, 0.06), {"all": "hull_black", "-3": "ochre"})
    for side, sn in SIDES:
        f = v3(side * 1.75, ws.POOP_RAIL_Y + 0.2, zt + 0.1 + dzc(side * 1.75))
        add_cube(stern, "crest_figure_base_" + sn, f + v3(0, 0.1, 0), EYE, (0.5, 0.2, 0.45), "gold")
        add_cube(stern, "crest_figure_body_" + sn, f + v3(0, 0.6, 0), gg.rz(side * 0.12), (0.34, 0.8, 0.3), "gold_relief")
        add_cube(stern, "crest_figure_head_" + sn, f + v3(side * 0.05, 1.15, 0), EYE, (0.24, 0.26, 0.24), "gold")
        beam(stern, "crest_figure_arm_" + sn, f + v3(side * 0.05, 0.85, 0), f + v3(-side * 0.35, 1.25, -0.05), 0.1, "gold")
        beam(stern, "crest_figure_trumpet_" + sn, f + v3(side * 0.05, 1.15, -0.1), f + v3(side * 0.35, 1.55, -0.25), 0.06, "gold")
    arms = v3(0, ws.POOP_RAIL_Y + 0.75, zt + 0.1 + dzc(0))
    add_cube(stern, "arms_frame", arms, EYE, (1.8, 1.3, 0.1), "gold")
    add_cube(stern, "arms_emblem", arms - v3(0, 0, 0.06), EYE, (1.55, 1.05, 0.04), {"all": None, "-3": "flag"}, stretch=True,
             u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0))
    add_cube(stern, "arms_crown", arms + v3(0, 0.82, 0), EYE, (0.8, 0.34, 0.12), "carving", stretch=True)
    for side, sn in SIDES:
        add_cube(stern, "arms_supporter_" + sn, arms + v3(side * 1.1, -0.1, 0), EYE, (0.3, 1.2, 0.16), "pilaster", stretch=True)

    # quarter galleries on the stern corners, two storeys, rounded in plan, under a gilded cupola and
    # over a carved pendant
    qz0, qz1 = -27.1, -23.6
    qzc, qh = (qz0 + qz1) / 2, (qz1 - qz0) / 2
    QD = 0.62
    ss = list(np.sin(np.linspace(-math.pi / 2, math.pi / 2, 13)))

    def qwall(z):
        return 0.975 * hw(z)

    def qpt(side, s, y, depth=1.0, half=1.0, extra=0.0):
        z = qzc + s * qh * half
        return v3(side * (qwall(z) + 0.08 + extra + QD * depth * math.sqrt(max(0.0, 1 - s * s))), y, z)

    def qframe(side, s, y):
        p = qpt(side, s, y)
        u = norm(qpt(side, min(1, s + 0.02), y) - qpt(side, max(-1, s - 0.02), y))
        vv = v3(0, 1, 0)
        n = np.cross(u, vv)
        if np.dot(n, v3(side, 0, 0)) < 0:
            n = -n
        return p, u, vv, n

    for side, sn in SIDES:
        for t, (y0, y1) in enumerate(((4.7, 6.9), (7.3, 9.3))):
            for j in range(len(ss) - 1):
                a0, a1, b0, b1 = qpt(side, ss[j], y0), qpt(side, ss[j], y1), qpt(side, ss[j + 1], y0), qpt(side, ss[j + 1], y1)
                board(stern, "quarter_gallery_%s%d_%d" % (sn, t, j), a0, a1, b0, b1, 0.12, "hull_black", v3(side, 0, 0))
                # floor and ceiling of the storey (the inner edge stays in the castle wall)
                for q, (y, nm) in enumerate(((y0 + 0.08, "floor"), (y1 - 0.02, "ceil"))):
                    za, zb = a0[2], b0[2]
                    ia, ib = v3(side * (qwall(za) - 0.08), y, za), v3(side * (qwall(zb) - 0.08), y, zb)
                    board(stern, "quarter_%s_%s%d_%d" % (nm, sn, t, j), ia, qpt(side, ss[j], y, extra=-0.06),
                          ib, qpt(side, ss[j + 1], y, extra=-0.06), 0.08, "dark_wood", v3(0, 1, 0))
                # cornice on top of the storey, base moulding under it
                for q, (y, th_, wd, reg) in enumerate(((y1 + 0.06, 0.14, 0.2, "gold"), (y0 + 0.04, 0.1, 0.14, "gold_relief"))):
                    pa, pb = qpt(side, ss[j], y, extra=0.04), qpt(side, ss[j + 1], y, extra=0.04)
                    beam(stern, "quarter_%s_%s%d_%d" % ("cornice" if q == 0 else "base", sn, t, j), pa, pb, th_, reg, width=wd,
                         extend=0.03)
            for j, s in enumerate((-0.55, 0.0, 0.55)):
                p, u, vv, n = qframe(side, s, (y0 + y1) / 2)
                R = np.column_stack([u, vv, n])
                add_cube(stern, "glow_quarter_window_%s%d_%d" % (sn, t, j), p + n * 0.03, R, (0.6, (y1 - y0) * 0.6, 0.04),
                         "arch_window", stretch=True)
                add_cube(stern, "quarter_window_frame_%s%d_%d" % (sn, t, j), p + n * 0.012, R, (0.74, (y1 - y0) * 0.6 + 0.14, 0.03),
                         "gold")
            for j, s in enumerate((-0.86, -0.28, 0.28, 0.86)):
                p, u, vv, n = qframe(side, s, (y0 + y1) / 2)
                add_cube(stern, "quarter_pilaster_%s%d_%d" % (sn, t, j), p + n * 0.04, np.column_stack([u, vv, n]),
                         (0.16, y1 - y0, 0.06), "pilaster", stretch=True)
        # cupola over the upper storey and the pendant under the lower one
        for tag, ybase, dy in (("dome", 9.44, 1.0), ("drop", 4.66, -1.1)):
            n_lv = 4
            for k in range(n_lv):
                ka, kb = k / n_lv, (k + 1) / n_lv
                ra, rb = math.cos(ka * math.pi / 2), math.cos(kb * math.pi / 2)
                ya, yb2 = ybase + dy * math.sin(ka * math.pi / 2), ybase + dy * math.sin(kb * math.pi / 2)
                if tag == "dome":
                    reg = "gold_relief" if k % 2 == 0 else "gold"
                else:
                    reg = "gold_relief" if k % 2 == 0 else "gold"
                for j in range(len(ss) - 1):
                    def P(s, r, y):
                        return qpt(side, s, y, depth=r, half=0.35 + 0.65 * r, extra=0.06 * r)
                    a0, a1 = P(ss[j], ra, ya), P(ss[j], rb, yb2)
                    b0, b1 = P(ss[j + 1], ra, ya), P(ss[j + 1], rb, yb2)
                    board(stern, "quarter_%s_%s%d_%d" % (tag, sn, k, j), a0, a1, b0, b1, 0.08, reg, v3(side, math.copysign(0.6, dy), 0))
            tip = qpt(side, 0.0, ybase + dy, depth=0.0) + v3(side * 0.05, 0, 0)
            if tag == "dome":
                round_beam(stern, "quarter_finial_" + sn, tip - v3(0, 0.05, 0), tip + v3(0, 0.4, 0), 0.16, "gold")
                round_beam(stern, "quarter_finial_ball_" + sn, tip + v3(0, 0.38, 0), tip + v3(0, 0.62, 0), 0.24, "gold")
            else:
                round_beam(stern, "quarter_drop_finial_" + sn, tip + v3(0, 0.1, 0), tip - v3(0, 0.3, 0), 0.26, "gold")
    # stern lanterns on the taffrail
    for k, (x, s) in enumerate(((2.7, 1.0), (-2.7, 1.0), (0.0, 1.4))):
        y, z = ws.POOP_RAIL_Y + (0.2 if k < 2 else 1.9), zt + 0.25 + dzc(x)
        beam(lanterns, "stern_lantern_pole_%d" % k, (x, y - 0.2, z), (x, y + 0.6 * s, z), 0.12, "iron")
        beam(lanterns, "stern_lantern_arm_%d" % k, (x * 0.8, y - 0.1, z + 0.4), (x, y + 0.45 * s, z), 0.1, "gold")
        add_cube(lanterns, "stern_lantern_%d" % k, (x, y + 0.95 * s, z), EYE, (0.55 * s, 0.8 * s, 0.55 * s),
                 {"all": "lantern", "+2": "gold", "-2": "gold"}, stretch=True)
        add_cube(lanterns, "glow_stern_lantern_%d" % k, (x, y + 0.95 * s, z), EYE, (0.38 * s, 0.6 * s, 0.38 * s), "glow", stretch=True)
        add_cube(lanterns, "stern_lantern_cap_%d" % k, (x, y + 1.45 * s, z), EYE, (0.34 * s, 0.2 * s, 0.34 * s), "gold")

    # ---- helm (double wheel) and rudder
    hub = v3(0, qd_y + 1.1, ws.HELM_Z)
    add_cube(stern, "helm_pedestal", (0, qd_y + 0.55, ws.HELM_Z), EYE, (0.4, 1.1, 1.0), "dark_wood")
    wheel = Bone("helm_wheel", origin=tuple(hub), parent=stern)
    for wz in (0.45, -0.45):
        c = hub + v3(0, 0, wz)
        add_cube(wheel, "helm_hub_%d" % int(wz > 0), c, EYE, (0.22, 0.22, 0.12), "gold")
        for k in range(8):
            a = 2 * math.pi * k / 8
            dvec = v3(math.cos(a), math.sin(a), 0)
            beam(wheel, "helm_spoke_%d_%d" % (int(wz > 0), k), c, c + dvec * 0.92, 0.07, "hull_light", up=v3(0, 0, 1))
            a2 = 2 * math.pi * (k + 1) / 8
            beam(wheel, "helm_rim_%d_%d" % (int(wz > 0), k), c + dvec * 0.7, c + v3(math.cos(a2), math.sin(a2), 0) * 0.7, 0.08,
                 "dark_wood", width=0.1, up=v3(0, 0, 1), extend=0.05)
    rudder = Bone("rudder", origin=(0, 0.0, -ws.HALF_LENGTH - 0.15), parent=root)
    # tapered blade hung on the stern post, its head going up into the counter
    zf = -ws.HALF_LENGTH - 0.17
    for k, (y0, y1, chord, reg) in enumerate(((-1.8, 0.3, 1.22, "white_bottom"), (0.3, 1.3, 1.1, "hull_black"),
                                                  (1.3, 2.0, 0.78, "hull_black"))):
        add_cube(rudder, "rudder_blade" + ("" if k == 0 else "_%d" % k), (0, (y0 + y1) / 2, zf - chord / 2), EYE,
                 (0.26 - 0.02 * k, y1 - y0 + (0.01 if k else 0), chord), reg)
    # rounded heel and back edge
    add_cube(rudder, "rudder_heel", (0, -1.72, zf - 1.0), gg.rx(math.pi / 4), (0.24, 0.3, 0.3), "white_bottom")
    for k, (y0, y1, c0, c1) in enumerate(((-1.62, 0.3, 1.22, 1.22), (0.3, 1.3, 1.22, 1.1), (1.3, 2.0, 1.1, 0.78))):
        beam(rudder, "rudder_back_%d" % k, (0, y0, zf - c0 - 0.02), (0, y1, zf - c1 - 0.02), 0.2,
             "white_bottom" if k == 0 else "hull_black", width=0.12)
    round_beam(rudder, "rudder_top", (0, 1.9, zf - 0.2), (0, 3.4, zf - 0.2), 0.34, "hull_black")
    for k, y in enumerate((-1.3, -0.2, 0.9, 1.8)):
        add_cube(rudder, "rudder_pintle_%d" % k, (0, y, zf - 0.05), EYE, (0.34, 0.12, 0.3), "iron")

    # ---- bow: stem, beakhead, figurehead, head rails, catheads, anchors, bowsprit
    y_stem0, y_stem1 = ws.keel_y(27.5) - 0.1, ws.FC_RAIL_Y + 0.5

    def stem_z(y):
        t = (y - y_stem0) / (y_stem1 - y_stem0)
        return 27.5 + 1.2 * max(0.0, t) ** 1.5

    stem = [v3(0, y, stem_z(y)) for y in np.linspace(y_stem0, y_stem1, 12)]
    add_cube(bow, "bow_breast", (0, 4.25, 28.12), EYE, (0.9, 7.4, 0.3), "hull_black")
    for j in range(len(stem) - 1):
        round_beam(bow, "stem_%d" % j, stem[j], stem[j + 1], 0.56, "hull_black", extend=0.1)

    def bez(a, c, b, t):
        a, c, b = v3(*a), v3(*c), v3(*b)
        return (1 - t) ** 2 * a + 2 * t * (1 - t) * c + t * t * b

    # knee of the head (cutwater): a solid curved fin sweeping forward from the waterline to the figurehead
    kn = [bez((0, 0.4, 27.75), (0, 2.6, 30.9), (0, 5.3, 31.05), t) for t in np.linspace(0, 1, 10)]
    for j in range(len(kn) - 1):
        ia, ib = v3(0.2, kn[j][1], stem_z(kn[j][1]) - 0.1), v3(0.2, kn[j + 1][1], stem_z(kn[j + 1][1]) - 0.1)
        oa, ob = kn[j] + v3(0.2, 0, 0), kn[j + 1] + v3(0.2, 0, 0)
        board(bow, "knee_%d" % j, ia, oa, ib, ob, 0.4, "hull_black", v3(1, 0, 0))
        bevel_beam(bow, "knee_edge_%d" % j, kn[j], kn[j + 1], 0.4, 0.2, "hull_black", c=0.07, corners=("+v+n", "+v-n"),
                   up=v3(0, 0, 1), extend=0.03)
        if j >= 4:
            for side, sn in SIDES:
                ta = kn[j] + (v3(0, kn[j][1], stem_z(kn[j][1])) - kn[j]) * 0.3
                tb = kn[j + 1] + (v3(0, kn[j + 1][1], stem_z(kn[j + 1][1])) - kn[j + 1]) * 0.3
                beam(bow, "trailboard_%s%d" % (sn, j), ta + v3(side * 0.22, 0, 0), tb + v3(side * 0.22, 0, 0), 0.32, "gold_relief",
                     width=0.05, extend=0.03)
    # beakhead: a tapering grating platform on the knee, between the curved head rails
    PY = 5.35

    def beak_w(z):
        f = min(1.0, max(0.0, (z - 27.6) / 3.3))
        return 0.3 + 1.05 * (1 - f) ** 0.85

    bz = list(np.linspace(27.6, 30.9, 7))
    for j in range(len(bz) - 1):
        za, zb = bz[j], bz[j + 1]
        c = board(bow, "beakhead_%d" % j, v3(-beak_w(za), PY, za), v3(beak_w(za), PY, za), v3(-beak_w(zb), PY, zb), v3(beak_w(zb), PY, zb),
                  0.16, "dark_wood", v3(0, 1, 0))
        c.faces[gg.SEMANTIC_FACE["+3"]]["region"] = "grating"
    for side, sn in SIDES:
        rails = (((side * 1.5, 7.25, 26.9), (side * 1.15, 5.7, 29.3), (side * 0.25, 6.05, 31.0), "head_rail"),
                 ((side * 1.6, 6.0, 27.1), (side * 1.05, 5.0, 29.2), (side * 0.3, 5.5, 30.75), "head_rail_low"))
        for a, cc, b, nm in rails:
            pts = [bez(a, cc, b, t) for t in np.linspace(0, 1, 8)]
            for j in range(len(pts) - 1):
                round_beam(bow, "%s_%s%d" % (nm, sn, j), pts[j], pts[j + 1], 0.14, "gold", extend=0.04)
        # head timbers between the platform and the upper rail
        for j, t in enumerate((0.3, 0.55, 0.8)):
            top = bez(*rails[0][:3], t)
            beam(bow, "head_timber_%s%d" % (sn, j), v3(top[0], PY, top[2]), top, 0.1, "gold_relief", width=0.14)
        z = 24.0
        x = side * (hw(z) * 0.975)
        beam(bow, "cathead_" + sn, (x - side * 0.3, ws.FC_RAIL_Y - 0.4, z), (x + side * 1.1, ws.FC_RAIL_Y - 0.25, z + 0.3), 0.3, "dark_wood")
        ax = x + side * 0.9
        beam(bow, "anchor_shank_" + sn, (ax, ws.FC_RAIL_Y - 0.6, z + 0.25), (ax, 4.0, z + 0.2), 0.18, "iron")
        beam(bow, "anchor_stock_" + sn, (ax, ws.FC_RAIL_Y - 0.75, z - 0.4), (ax, ws.FC_RAIL_Y - 0.75, z + 0.9), 0.14, "dark_wood")
        beam(bow, "anchor_arm_a_" + sn, (ax, 4.0, z + 0.2), (ax, 4.6, z - 0.5), 0.16, "iron")
        beam(bow, "anchor_arm_b_" + sn, (ax, 4.0, z + 0.2), (ax, 4.6, z + 0.9), 0.16, "iron")
        add_cube(bow, "hawse_" + sn, gn.side_frame(26.0, 5.6, side)[0] + v3(side * 0.03, 0, 0), EYE, (0.06, 0.32, 0.32), "iron")
    fig = Bone("figurehead", origin=(0, 5.6, 31.0), parent=bow)
    gn.lion_figurehead(fig, (0, 5.85, 31.3), 1.0, relief="gold_relief")
    for side, sn in SIDES:
        add_cube(bow, "cathead_face_" + sn, (side * (hw(24.0) * 0.975 + 1.15), ws.FC_RAIL_Y - 0.2, 24.3), EYE, (0.3, 0.34, 0.34), "gold")
    sprit_a, sprit_b = v3(0, 6.6, 25.0), v3(0, 12.2, 36.0)
    jib_end = v3(0, 13.5, 38.6)
    round_beam(bow, "bowsprit", sprit_a, sprit_b, 0.6, "mast")
    round_beam(bow, "jibboom", sprit_b - norm(sprit_b - sprit_a) * 1.2, jib_end, 0.34, "mast")
    beam(bow, "bowsprit_cap", sprit_b - norm(sprit_b - sprit_a) * 0.2, sprit_b + norm(sprit_b - sprit_a) * 0.1, 0.7, "dark_wood")
    beam(bow, "jack_staff", sprit_b, sprit_b + v3(0, 1.2, 0), 0.1, "dark_wood")
    add_cube(lanterns, "bow_lantern", (0, ws.FC_RAIL_Y + 0.6, 27.6), EYE, (0.45, 0.6, 0.45), {"all": "lantern", "+2": "iron"}, stretch=True)
    add_cube(lanterns, "glow_bow_lantern", (0, ws.FC_RAIL_Y + 0.6, 27.6), EYE, (0.3, 0.45, 0.3), "glow", stretch=True)

    # ---- masts with fighting tops, crosstrees and three square sails each
    sails_info = []

    def mast(name, z, foot, tops, thick):
        mb = Bone(name, origin=(0, foot, z), parent=root)
        t1, t2, t3 = tops
        round_beam(mb, name + "_lower", (0, foot - 0.2, z), (0, t1 + 0.8, z), thick, "mast")
        round_beam(mb, name + "_top", (0, t1 - 0.6, z), (0, t2 + 0.6, z), thick * 0.62, "mast")
        round_beam(mb, name + "_topgallant", (0, t2 - 0.5, z), (0, t3, z), thick * 0.4, "mast")
        add_cube(mb, name + "_partners", (0, foot + 0.14, z), EYE, (thick + 0.45, 0.28, thick + 0.45), "dark_wood")
        for k, y in enumerate(np.linspace(foot + 1.5, t1 - 1.0, 4)):
            round_beam(mb, "%s_woolding_%d" % (name, k), (0, y - 0.08, z), (0, y + 0.08, z), thick + 0.07, "rope")
        add_cube(mb, name + "_cap", (0, t3 - 0.08, z), EYE, (thick * 0.4 + 0.15, 0.22, thick * 0.4 + 0.15), "gold")
        r = 1.5 + thick
        for k in range(8):
            a = 2 * math.pi * (k + 0.5) / 8
            c = v3(math.cos(a) * r * 0.62, t1, z + math.sin(a) * r * 0.62)
            add_cube(mb, "%s_top_%d" % (name, k), c, ry(-a), (r * 0.8, 0.14, r * 0.75), {"all": "dark_wood", "+2": "deck"})
            a0, a1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
            p0 = v3(math.cos(a0) * r, t1 + 0.4, z + math.sin(a0) * r)
            p1 = v3(math.cos(a1) * r, t1 + 0.4, z + math.sin(a1) * r)
            board(mb, "%s_top_rim_%d" % (name, k), p0 - v3(0, 0.45, 0), p0, p1 - v3(0, 0.45, 0), p1, 0.07, "hull_black",
                  v3(math.cos(a0), 0, math.sin(a0)), overlap=1.12)
        add_cube(lanterns, name + "_top_lantern", (0, t1 + 0.75, z - r * 0.85), EYE, (0.4, 0.55, 0.4),
                 {"all": "lantern", "+2": "gold", "-2": "gold"}, stretch=True)
        add_cube(lanterns, "glow_" + name + "_top_lantern", (0, t1 + 0.75, z - r * 0.85), EYE, (0.26, 0.4, 0.26), "glow", stretch=True)
        beam(mb, name + "_crosstree_x", (-1.3, t2, z), (1.3, t2, z), 0.14, "dark_wood")
        beam(mb, name + "_crosstree_z", (0, t2, z - 0.8), (0, t2, z + 0.8), 0.14, "dark_wood")
        beam(mb, name + "_flagpole", (0, t3, z), (0, t3 + 1.6, z), 0.12, "dark_wood")
        return mb

    def yard(mb, name, z, y, half):
        round_beam(mb, name, (-half, y, z + 0.5), (half, y, z + 0.5), 0.3, "mast_dark", extend=0.12)
        for side in (1, -1):
            beam(mb, "%s_arm_%d" % (name, side > 0), (side * (half - 0.2), y, z + 0.5), (side * (half + 0.35), y, z + 0.5), 0.2,
                 "mast_dark")
        add_cube(mb, name + "_sling", (0, y, z + 0.38), EYE, (0.5, 0.4, 0.4), "rope")
        beam(mb, name + "_roll", (-half * 0.92, y - 0.24, z + 0.56), (half * 0.92, y - 0.24, z + 0.56), 0.3, "cloth_roll")

    def square_sail(mb, name, z, y_top, half_top, half_bottom, height, depth):
        br = Bone("brace_" + name, origin=(0, y_top, z), parent=mb)
        yard(br, name + "_yard", z, y_top, half_top + 0.4)
        sb = Bone("sail_" + name, origin=(0, y_top, z + 0.56), parent=br)
        gn.sail(sb, name, v3(0, y_top - 0.14, z + 0.58), v3(1, 0, 0), v3(0, -1, 0), v3(0, 0, 1), half_top, half_bottom,
                height, depth * 2.4, "course" if "course" in name else "topsail", nx=8, ny=10, round_=0.8, overlap=0.03, foot=0.09)
        br.rot = ry(gn.BRACE)
        sails_info.append((sb, False))

    m_fore = mast("foremast", ws.FORE_MAST_Z, fc_y, (19.0, 27.5, ws.FORE_MAST_TOP), 0.78)
    m_main = mast("mainmast", ws.MAIN_MAST_Z, main_y, (21.0, 31.0, ws.MAIN_MAST_TOP), 0.92)
    m_miz = mast("mizzen", ws.MIZZEN_Z, main_y, (17.0, 25.0, ws.MIZZEN_TOP), 0.62)
    square_sail(m_fore, "fore_course", ws.FORE_MAST_Z, 18.0, 5.6, 6.4, 9.0, 1.35)
    square_sail(m_fore, "fore_topsail", ws.FORE_MAST_Z, 26.6, 4.0, 5.2, 7.0, 1.3)
    square_sail(m_fore, "fore_topgallant", ws.FORE_MAST_Z, 33.2, 2.6, 3.4, 5.4, 1.0)
    square_sail(m_main, "main_course", ws.MAIN_MAST_Z, 20.0, 7.0, 7.8, 10.4, 1.9)
    square_sail(m_main, "main_topsail", ws.MAIN_MAST_Z, 30.2, 4.8, 6.4, 8.6, 1.5)
    square_sail(m_main, "main_topgallant", ws.MAIN_MAST_Z, 39.6, 3.2, 4.4, 7.4, 1.1)
    square_sail(m_miz, "mizzen_topsail", ws.MIZZEN_Z, 24.6, 3.4, 4.4, 6.4, 1.0)
    # mizzen lateen
    lat_fore, lat_aft = v3(0.5, 12.0, -9.8), v3(0.5, 23.5, -25.0)
    round_beam(m_miz, "lateen_yard", lat_fore - norm(lat_aft - lat_fore) * 0.4, lat_aft, 0.24, "mast")
    beam(m_miz, "lateen_roll", lat_fore + v3(0.06, -0.24, 0) + norm(lat_aft - lat_fore) * 1.0,
         lat_aft + v3(0.06, -0.24, 0) - norm(lat_aft - lat_fore) * 0.5, 0.28, "cloth_roll")
    lat_sail = Bone("sail_mizzen", origin=tuple((lat_fore + lat_aft) / 2), parent=m_miz)
    lateen_tri = gn.tri_sail(lat_sail, "mizzen_lateen", lat_aft + v3(0.1, -0.14, 0.05), lat_fore + v3(0.1, -0.14, 0),
                             v3(0.55, 12.6, -24.0), 1.25, v3(1, 0, 0), "lateen", ny=8)
    sails_info.append((lat_sail, True))
    # three jibs and the spritsail
    jib = Bone("jib", origin=tuple(sprit_b), parent=root)
    jib_tri = None
    for k, (top, tack, clew, depth) in enumerate((
            (v3(0, 18.6, ws.FORE_MAST_Z + 0.4), sprit_a + (sprit_b - sprit_a) * 0.5, v3(0.06, 10.4, 25.4), 0.5),
            (v3(0, 27.0, ws.FORE_MAST_Z + 0.3), sprit_b, v3(0.06, 12.8, 28.6), 0.5),
            (v3(0, 33.0, ws.FORE_MAST_Z + 0.2), jib_end, v3(0.06, 16.8, 32.0), 0.45))):
        head = tack + (top - tack) * 0.6
        clew = gn.jib_clew(head, tack, clew)
        tri = gn.tri_sail(jib, "jib_%d" % k, head + v3(0, -0.05, -0.06), tack + v3(0, 0.05, -0.12), clew, depth * 1.6, v3(1, 0, 0),
                          "jib", nx=4, ny=6)
        jib_tri = jib_tri or tri
        beam(ropes, "rope_jibstay_%d" % k, top, tack, 0.06, "rope")
    sails_info.append((jib, True))
    beam(bow, "jib_roll", sprit_a + (sprit_b - sprit_a) * 0.45 + v3(0, 0.36, 0), jib_end + v3(0, 0.2, -0.4), 0.24, "cloth_roll")
    sprit_yard = sprit_a + (sprit_b - sprit_a) * 0.72
    beam(bow, "spritsail_yard", sprit_yard + v3(-3.6, -0.3, 0), sprit_yard + v3(3.6, -0.3, 0), 0.2, "mast", extend=0.1)
    beam(bow, "spritsail_roll", sprit_yard + v3(-3.2, -0.52, 0.06), sprit_yard + v3(3.2, -0.52, 0.06), 0.26, "cloth_roll")
    sprit_sail = Bone("sail_sprit", origin=tuple(sprit_yard + v3(0, -0.36, 0)), parent=bow)
    gn.sail(sprit_sail, "spritsail", sprit_yard + v3(0, -0.42, 0.14), v3(1, 0, 0), v3(0, -1, 0), v3(0, 0, 1), 3.2, 3.7, 3.0, 1.0,
            "topsail", nx=5, ny=5, round_=0.7, foot=0.08)
    sails_info.append((sprit_sail, False))

    # ---- flags (texture #1)
    def flag(parent, name, root_pt, w, h, region="flag"):
        fb = Bone("flag_" + name, origin=tuple(root_pt), parent=parent)
        c1 = add_cube(fb, "flag_%s_a" % name, root_pt + v3(0, -h / 2, -w / 4), EYE, (0.03, h, w / 2),
                      {"all": None, "+1": region, "-1": region}, stretch=True, u_dir=v3(0, 0, -1), v_dir=v3(0, -1, 0))
        tip_root = root_pt + v3(0, 0, -w / 2)
        ft = Bone("flag_%s_tip" % name, origin=tuple(tip_root), parent=fb)
        c2 = add_cube(ft, "flag_%s_b" % name, tip_root + v3(0, -h / 2, -w / 4), EYE, (0.03, h, w / 2),
                      {"all": None, "+1": region, "-1": region}, stretch=True, u_dir=v3(0, 0, -1), v_dir=v3(0, -1, 0))
        gn.set_sub(c1, (0, 0, 0.5, 1), faces=("west", "east"))
        gn.set_sub(c2, (0.5, 0, 1, 1), faces=("west", "east"))

    flag(m_main, "main", v3(0, ws.MAIN_MAST_TOP + 1.5, ws.MAIN_MAST_Z), 6.5, 0.7, region="pennant")
    flag(m_fore, "fore", v3(0, ws.FORE_MAST_TOP + 1.5, ws.FORE_MAST_Z), 2.6, 1.7)
    flag(m_miz, "mizzen", v3(0, ws.MIZZEN_TOP + 1.5, ws.MIZZEN_Z), 2.6, 1.7)
    staff = v3(0, ws.POOP_RAIL_Y + 0.4, zt + 0.5)
    beam(stern, "ensign_staff", staff, staff + v3(0, 4.4, -1.0), 0.16, "dark_wood")
    flag(stern, "stern", staff + v3(0, 4.3, -1.05), 4.2, 2.8)

    # ---- rigging: shrouds with ratlines, chain-wales, stays, braces
    def chain_point(z, side):
        return v3(side * (0.975 * hw(z) + 0.2), ws.rail_y(z) - 0.3, z)

    for side, sn in SIDES:
        for tag, mz, t1, zs in (("main", ws.MAIN_MAST_Z, 21.0, (-1.6, -0.4, 0.8, 2.0, 3.2)),
                                ("fore", ws.FORE_MAST_Z, 19.0, (16.0, 17.0, 18.0, 19.0)),
                                ("mizzen", ws.MIZZEN_Z, 17.0, (-15.8, -14.6, -13.4))):
            top = v3(side * 1.3, t1 - 0.2, mz)
            pts = [chain_point(z, side) for z in zs]
            for k, b in enumerate(pts):
                beam(ropes, "shroud_%s_%s%d" % (tag, sn, k), top, b, 0.06, "rope")
                add_cube(ropes, "deadeye_%s_%s%d" % (tag, sn, k), b, EYE, (0.16, 0.24, 0.24), "dark_wood")
                beam(ropes, "chain_%s_%s%d" % (tag, sn, k), b, b + v3(0, -1.1, 0), 0.06, "iron")
            z0, z1 = zs[0] - 0.4, zs[-1] + 0.4
            beam(hull, "channel_%s_%s" % (tag, sn), chain_point(z0, side) + v3(-side * 0.1, -0.18, 0),
                 chain_point(z1, side) + v3(-side * 0.1, -0.18, 0), 0.12, "hull_black", width=0.44)
            for k in range(1, 12):
                t = k / 12.5
                pa = pts[0] + (top - pts[0]) * t
                pb = pts[-1] + (top - pts[-1]) * t
                beam(ropes, "ratline_%s_%s%d" % (tag, sn, k), pa, pb, 0.045, "rope")
        for tag, mz, t1, t2 in (("main", ws.MAIN_MAST_Z, 21.0, 31.0), ("fore", ws.FORE_MAST_Z, 19.0, 27.5),
                                ("mizzen", ws.MIZZEN_Z, 17.0, 25.0)):
            r = 1.5 + 0.6
            for k in range(2):
                beam(ropes, "topshroud_%s_%s%d" % (tag, sn, k), v3(side * 0.3, t2 - 0.3, mz),
                     v3(side * r * 0.9, t1 + 0.3, mz + (k - 0.5) * 1.0), 0.05, "rope")
        mz, fz = ws.MAIN_MAST_Z, ws.FORE_MAST_Z
        beam(ropes, "main_brace_" + sn, gn.braced((side * 7.4, 20.0, mz + 0.5), mz), chain_point(-12.0, side), 0.05, "rope")
        beam(ropes, "main_sheet_" + sn, gn.braced((side * 7.6, 10.0, mz + 2.4), mz), chain_point(-6.0, side), 0.05, "rope")
        beam(ropes, "fore_sheet_" + sn, gn.braced((side * 6.2, 9.6, fz + 2.0), fz), chain_point(12.0, side), 0.05, "rope")
        beam(ropes, "fore_brace_" + sn, gn.braced((side * 5.9, 18.0, fz + 0.5), fz), v3(side * 0.7, 20.6, mz), 0.05, "rope")
        beam(ropes, "topsail_brace_" + sn, gn.braced((side * 5.1, 30.2, mz + 0.5), mz), v3(side * 0.3, 24.5, ws.MIZZEN_Z), 0.05, "rope")
    for name, a, b in (
            ("main_stay", v3(0, 20.8, ws.MAIN_MAST_Z + 0.4), v3(0, fc_y + 0.4, ws.FORE_MAST_Z - 0.6)),
            ("main_topstay", v3(0, 30.6, ws.MAIN_MAST_Z), v3(0, 19.2, ws.FORE_MAST_Z)),
            ("main_tgstay", v3(0, ws.MAIN_MAST_TOP - 0.6, ws.MAIN_MAST_Z), v3(0, 27.6, ws.FORE_MAST_Z)),
            ("mizzen_stay", v3(0, 16.8, ws.MIZZEN_Z + 0.3), v3(0, main_y + 0.6, ws.MAIN_MAST_Z - 0.8)),
            ("mizzen_topstay", v3(0, 24.6, ws.MIZZEN_Z), v3(0, 21.2, ws.MAIN_MAST_Z)),
            ("lateen_sheet", v3(0.55, 12.6, -24.0), v3(0.5, ws.POOP_RAIL_Y + 0.1, -27.0)),
            ("bobstay", sprit_b - v3(0, 0.2, 0.4), v3(0, 3.0, 28.4)),
            ("martingale", jib_end, sprit_b + v3(0, -1.6, 0.1))):
        beam(ropes, "rope_" + name, a, b, 0.06, "rope")
    for side, sn in SIDES:
        for tag, mz, top in (("main", ws.MAIN_MAST_Z, 31.0), ("fore", ws.FORE_MAST_Z, 27.5), ("mizzen", ws.MIZZEN_Z, 25.0)):
            beam(ropes, "backstay_%s_%s" % (tag, sn), v3(side * 0.3, top - 0.3, mz), chain_point(mz - 5.5, side), 0.05, "rope")
    return root, lateen_tri, jib_tri, sails_info


def main():
    root, lateen_tri, jib_tri, sails_info = build()
    anims = gn.build_animations(root, sails_info)
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    tex_path = os.path.join(tex_dir, "entity/warship.png")
    flag_path = os.path.join(tex_dir, "entity/warship_flag.png")
    wt.make_textures(tex_path, flag_path, lateen_tri, jib_tri)
    wt.make_item_icon(os.path.join(tex_dir, "item/warship.png"))
    with open(tex_path, "rb") as f:
        png = f.read()
    with open(flag_path, "rb") as f:
        flag_png = f.read()
    textures = [gn.texture_entry("warship.png", wt.SIZE, png, "entity", "warship.png"),
                gn.texture_entry("warship_flag.png", wt.FLAG_SIZE, flag_png, "entity", "warship.png")]
    textures[0]["id"], textures[1]["id"] = "0", "1"
    model = gn.export(root, anims, textures, [
        os.path.join(ROOT, "blockbench/warship.bbmodel"),
        os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/warship.bbmodel"),
    ], name="warship", visible_box=(60, 46, 0))
    print("cubes:", len(model["elements"]), "animations:", [a["name"] for a in model["animations"]])


if __name__ == "__main__":
    main()
