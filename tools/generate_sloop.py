#!/usr/bin/env python3
"""Generates the trade sloop (trade_sloop) Blockbench model, its texture and animations.

Usage:  python3 tools/generate_sloop.py

Outputs:
  blockbench/trade_sloop.bbmodel                                   (editable, texture embedded)
  src/main/resources/assets/medievalships/models/entity/trade_sloop.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/trade_sloop.png
  src/main/resources/assets/medievalships/textures/item/trade_sloop.png

Reference: a small chunky merchant sloop. Dark brown planking with a wide band of bright blue
strakes along the sides crossed by brown frames, a honey wale and cap rail; a raised bow with a
long bowsprit; one mast with crosstrees, a big gaff mainsail and a large jib, shrouds with
ratlines; a walkable deck with crates and barrels, a small raised stern platform with the cargo
and the tiller; lanterns on davits at the quarters and under the bowsprit.

Bones used by the mod (keep their names when editing in Blockbench):
  sail_main, sail_jib (sail_wind, sail_furl)   rudder (steer: blade and tiller)
  lantern_* (lantern_sway)   rope_slack_* (rope_sway)
"""
import math
import os
import sys
import uuid

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import sloop_shape as ss  # noqa: E402
import sloop_texture as st  # noqa: E402
import generate_galleon as gn  # noqa: E402
import generate_galley as gg  # noqa: E402
import ship_details as sd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/trade_sloop/%d" % _uuid_counter[0]))


gg.new_uuid = new_uuid
gn.new_uuid = new_uuid
gn.gs = ss
gn.REGIONS = {k: (0,) + r for k, r in st.REGIONS.items()}
gn.SIZE = st.SIZE

v3, norm, Bone, add_cube, beam, board = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam, gg.board
rx, ry, rz = gg.rx, gg.ry, gg.rz
round_bar, disc, turned = gn.round_bar, gn.disc, gn.turned
EYE = np.eye(3)
SIDES = ((1, "p"), (-1, "s"))

FORE_END, AFT_END = ss.FORE_SCALE - 0.05, -ss.AFT_SCALE + 0.05
# hull stations, closer together towards the ends where the lines turn fast
STATIONS = [AFT_END, -7.75, -7.5, -7.15, -6.7, -6.15, -5.5, -4.75, -3.95, -3.1, -2.2, -1.25, -0.3, 0.65, 1.6, 2.55, 3.45, 4.3,
            5.1, 5.85, 6.5, 7.05, 7.5, 7.82, FORE_END]
# above the waterline point (y = 0.15) the strakes follow the sheer: a dark strake, the blue band (two
# strakes), the honey wale under the cap rail
UPPER = [0.09, 0.37, 0.66, 1.0]
SPAN_REGIONS = ["hull_dark"] * 4 + ["hull_dark", "hull_blue", "hull_blue", "hull_wale"]
SECTION_SUB = [2, 2, 2, 1, 1, 1, 1, 1]
STRAKES = [reg for reg, n in zip(SPAN_REGIONS, SECTION_SUB) for _ in range(n)]
STRAKE_SPAN = [k for k, n in enumerate(SECTION_SUB) for _ in range(n)]
MZ = ss.MAST_Z


def _cr(p0, p1, p2, p3, t):
    """Catmull-Rom point between p1 and p2."""
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)


def _smooth(points, subs):
    """Smooth curve through the control points, span k cut into subs[k] pieces."""
    P = [np.asarray(p, dtype=float) for p in points]
    out = []
    for k in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(k - 1, 0)], P[k], P[k + 1], P[min(k + 2, len(P) - 1)]
        for j in range(subs[k]):
            out.append(_cr(p0, p1, p2, p3, j / subs[k]))
    out.append(P[-1])
    return out


def curve(points, n=6):
    """Catmull-Rom points through the given control points."""
    pts = [points[0]] + points + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(n):
            out.append(_cr(p0, p1, p2, p3, k / n))
    out.append(points[-1])
    return out


def _octo(bone, name, c, R, size, region):
    """Octagonal block: a box and the same box turned 45 degrees about its own y axis."""
    add_cube(bone, name, c, R, size, region)
    reg = {"all": region, "+2": None, "-2": None} if isinstance(region, str) else dict(region, **{"+2": None, "-2": None})
    add_cube(bone, name + "_r", c, R @ ry(math.pi / 4), size, reg)


def hw(z):
    return ss.half_width(z)


def sheer(z):
    return ss.rail_y(z)


def upper_y(z, f):
    """Strakes above the waterline point follow the sheer up to the rail."""
    return 0.15 + (sheer(z) - 0.15) * f


def outer_x(z, y):
    w = hw(z)
    if y <= 0.15:
        return w
    f = min(1.0, (y - 0.15) / max(0.05, sheer(z) - 0.15))
    return w * (1.0 - 0.04 * f * f)   # a touch of tumblehome: a rounded, chunky section


gn.outer_x = outer_x
gn.hw = hw


def section(z, side):
    w, yk = hw(z), ss.keel_y(z)
    pts = [(0.05, yk)]
    for fx, fy in ss.BOTTOM_SECTION[1:]:
        pts.append((fx * w, fy * yk))
    pts.append((outer_x(z, 0.15), 0.15))
    for f in UPPER:
        y = upper_y(z, f)
        pts.append((outer_x(z, y), y))
    pts = _smooth(pts, SECTION_SUB)
    return [v3(side * max(x, 0.05), y, z) for x, y in pts]


# ---------------------------------------------------------------- sails (cells fitted to a curved patch)
def patch_sail(bone, name, P, N, region, nx, ny, th=0.035, overlap=0.03, keep=None):
    """Sail on a curved patch P(s, t) (s across, t from the head down, both 0..1): cells fitted to their
    four corners, each mapping its own part of the texture region (same method as the Old Corsair)."""
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
            U0 = (P(1, (t0 + t1) / 2) - P(0, (t0 + t1) / 2))
            V0 = (P((s0 + s1) / 2, 1) - P((s0 + s1) / 2, 0))
            cube = add_cube(bone, "%s_%d_%d" % (name, i, j), c, axes, (Lu + overlap, Hv + overlap, th),
                            {"all": None, "+3": region, "-3": region}, stretch=True, u_dir=U0, v_dir=V0)
            gn.set_sub(cube, (s0, t0, s1, t1))


def quad_sail(bone, name, throat, peak, tack, clew, belly, N, region, nx=8, ny=9):
    """Fore-and-aft four sided sail: head along the gaff, luff on the mast, foot on the boom, the cloth
    bellying out between them (most in the middle of its width, towards the foot)."""
    def P(s, t):
        top = throat + (peak - throat) * s
        bot = tack + (clew - tack) * s
        p = top + (bot - top) * t
        return p + N * belly * math.sin(math.pi * s) ** 0.8 * math.sin(math.pi * min(1.0, t * 0.85 + 0.08))
    patch_sail(bone, name, P, N, region, nx, ny)


def hanging_lantern(parent, name, hook, drop=0.6, s=1.0, metal="iron"):
    """Iron lantern on a short chain, its own bone so that it sways (lantern_sway); rebuilt as lit
    glass in an iron frame by tools/lanterns.py on export."""
    b = Bone(name, origin=tuple(hook), parent=parent)
    beam(b, name + "_chain", hook, hook - v3(0, drop, 0), 0.04, "iron")
    c = hook - v3(0, drop + 0.22 * s, 0)
    add_cube(b, name + "_body", c, EYE, (0.3 * s, 0.4 * s, 0.3 * s), {"all": "lantern", "+2": metal, "-2": metal}, stretch=True)
    add_cube(b, "glow_" + name, c, EYE, (0.2 * s, 0.3 * s, 0.2 * s), "glow", stretch=True)
    return b


def crate(bone, name, x, z, y, s, yaw=0.0):
    gn.g_crate(bone, name, (x, y, z), s=s, yaw=yaw, wood="dark_wood", batten="hull_light")


def barrel(bone, name, x, z, y, r):
    gn.g_barrel(bone, name, (x, y, z), h=0.8, r=r, wood="hull_wale")


def bench(bone, name, p, length, along):
    """Plain plank bench on two trestle legs (the merchant's benches along the bulwarks)."""
    p, al = v3(*p), norm(v3(*along))
    ac = np.cross(v3(0, 1, 0), al)
    R = np.column_stack([al, v3(0, 1, 0), np.cross(al, v3(0, 1, 0))])
    add_cube(bone, name + "_seat", p + v3(0, 0.40, 0), R, (length, 0.08, 0.42), {"all": "hull_light", "+2": "rail"})
    for s in (1, -1):
        round_bar(bone, name + "_edge_%d" % (s > 0), p + v3(0, 0.395, 0) + ac * s * 0.21 - al * length / 2,
                  p + v3(0, 0.395, 0) + ac * s * 0.21 + al * length / 2, 0.07, "hull_light")
    for k, t in enumerate((-0.36, 0.36)):
        b = p + al * (t * length)
        add_cube(bone, "%s_leg_%d" % (name, k), b + v3(0, 0.18, 0), R, (0.1, 0.36, 0.34), "frame")


def build():
    root = Bone("trade_sloop")
    hull = Bone("hull", parent=root)
    deck = Bone("deck", parent=root)
    bow = Bone("bow", parent=root)
    stern = Bone("stern", parent=root)
    fittings = Bone("fittings", parent=root)
    cargo = Bone("cargo", parent=root)
    ropes = Bone("ropes", parent=root)
    lanterns = Bone("lanterns", parent=root)
    main_y, aft_y = ss.MAIN_DECK_Y, ss.AFT_DECK_Y

    # ---- hull: dark tarred bottom, the blue band crossed by frames, honey wale and cap rail
    for side, sn in SIDES:
        for i in range(len(STATIONS) - 1):
            za, zb = STATIONS[i], STATIONS[i + 1]
            A, B = section(za, side), section(zb, side)
            for k, reg in enumerate(STRAKES):
                mid = (A[k] + A[k + 1] + B[k] + B[k + 1]) / 4
                outward = norm(v3(mid[0], mid[1] - 0.8, 0.35 * np.sign(mid[2]) * abs(mid[0])))
                board(hull, "hull_%s%d_%d" % (sn, i, k), A[k], A[k + 1], B[k], B[k + 1], 0.1, reg, outward,
                      inner="hull_light" if STRAKE_SPAN[k] >= 5 else None)
            # cap rail: a wide honey cap with a rounded outer bead
            pa, pb = v3(side * outer_x(za, sheer(za)), sheer(za) + 0.05, za), v3(side * outer_x(zb, sheer(zb)), sheer(zb) + 0.05, zb)
            beam(hull, "caprail_%s%d" % (sn, i), pa, pb, 0.1, "rail", width=0.34, extend=0.04)
            o = v3(side * 0.16, -0.04, 0)
            beam(hull, "caprail_bead_%s%d" % (sn, i), pa + o, pb + o, 0.11, "hull_wale", width=0.11, up=norm(v3(side, 1, 0)), extend=0.04)
            # a thin moulding along the top of the blue band
            ya, yb = upper_y(za, UPPER[2]), upper_y(zb, UPPER[2])
            pa, pb = v3(side * (outer_x(za, ya) + 0.03), ya, za), v3(side * (outer_x(zb, yb) + 0.03), yb, zb)
            beam(hull, "moulding_%s%d" % (sn, i), pa, pb, 0.06, "rail", width=0.07, up=norm(v3(side, 1, 0)), extend=0.04)
        # brown frames crossing the blue band on the outside, every 1.3 blocks or so
        for k, z in enumerate(np.arange(-6.5, 7.0, 1.3)):
            y0, y1 = upper_y(z, UPPER[0]) - 0.04, upper_y(z, UPPER[2]) + 0.04
            p0, _, _, n0 = gn.side_frame(z, y0, side)
            p1, _, _, n1 = gn.side_frame(z, y1, side)
            beam(hull, "frame_%s%d" % (sn, k), p0 + n0 * 0.06, p1 + n1 * 0.06, 0.11, "frame", width=0.22, up=n0)
        # bulwark stanchions inside, from the deck to the cap rail
        for k, z in enumerate(np.arange(-6.2, 6.6, 1.6)):
            x = side * (0.97 * hw(z) - 0.12 - 0.08)
            beam(hull, "stanchion_%s%d" % (sn, k), v3(x, ss.deck_y(z) + 0.02, z), v3(x, sheer(z) - 0.02, z), 0.1, "frame", width=0.14)
        # a low open rail on the cap rail round the stern platform: turned posts and a rounded top rail
        prev = None
        for k, z in enumerate(np.arange(-7.2, ss.AFT_DECK_START + 0.2, 0.8)):
            x = side * (outer_x(z, sheer(z)) - 0.08)
            foot, top = v3(x, sheer(z) + 0.1, z), v3(x, sheer(z) + 0.6, z)
            turned(hull, "stern_rail_post_%s%d" % (sn, k), foot, top, [(0, 0.12), (0.3, 0.09), (0.7, 0.11), (1, 0)], "rail")
            if prev is not None:
                round_bar(hull, "stern_rail_%s%d" % (sn, k), prev, top, 0.09, "rail", extend=0.05)
            prev = top
    for i in range(len(STATIONS) - 1):
        za, zb = STATIONS[i], STATIONS[i + 1]
        beam(hull, "keel_%d" % i, (0, ss.keel_y(za) - 0.06, za), (0, ss.keel_y(zb) - 0.06, zb), 0.2, "hull_dark", width=0.26,
             extend=0.05)

    # ---- stem: the post rises with the sheer to a square stem head carrying the bowsprit
    hy, hz = ss.BOWSPRIT_HEEL
    ctrl = [v3(0, ss.keel_y(FORE_END) - 0.05, FORE_END - 0.25), v3(0, 0.3, FORE_END + 0.15), v3(0, 1.6, 8.25), v3(0, 2.7, 8.2),
            v3(0, hy + 0.35, 8.05)]
    pts = curve(ctrl, 4)
    for j in range(len(pts) - 1):
        t = j / (len(pts) - 1)
        th = 0.42 * (1 - t) + 0.3 * t
        reg = "hull_dark" if pts[j][1] < 0.3 else "hull_wale"
        round_bar(bow, "stem_%d" % j, pts[j], pts[j + 1], th, reg, extend=0.04)
    add_cube(bow, "stem_head", (0, hy - 0.1, 7.5), EYE, (0.62, 1.1, 1.1), "frame")
    add_cube(bow, "stem_head_cap", (0, hy + 0.48, 7.5), EYE, (0.72, 0.1, 1.2), "rail")
    for side in (1, -1):
        add_cube(bow, "knighthead_%d" % (side > 0), (side * 0.45, hy - 0.25, 7.0), EYE, (0.18, 0.8, 0.5), "frame")
    # bowsprit: a tapering round spar, iron gammon band at the stem head, a pale cap at the tip
    ty, tz = ss.BOWSPRIT_TIP
    heel, tip = v3(0, hy, hz), v3(0, ty, tz)
    mid = heel + (tip - heel) * 0.55
    round_bar(bow, "bowsprit_0", heel - (tip - heel) * 0.12, mid, 0.38, "mast")
    round_bar(bow, "bowsprit_1", mid - (tip - heel) * 0.02, tip, 0.29, "mast")
    d = norm(tip - heel)
    disc(bow, "gammon_iron", heel + d * 0.25, d, 0.24, 0.12, "iron", n=3)
    disc(bow, "bowsprit_band", mid, d, 0.2, 0.1, "iron", n=3)
    disc(bow, "bowsprit_cap", tip + d * 0.08, d, 0.16, 0.16, "truck", n=3)
    # mooring bitts and a windlass drum at the bow
    for k, x in enumerate((0.5, -0.5)):
        add_cube(bow, "bitt_%d" % k, (x, main_y + 0.42, 6.2), EYE, (0.2, 0.84, 0.2), "frame")
        add_cube(bow, "bitt_cap_%d" % k, (x, main_y + 0.88, 6.2), EYE, (0.26, 0.08, 0.26), "rail")
    turned(bow, "windlass", (0.52, main_y + 0.55, 6.2), (-0.52, main_y + 0.55, 6.2), [(0, 0.2), (0.15, 0.3), (0.85, 0.2), (1, 0)], "hull_wale")
    add_cube(bow, "windlass_bar", (0.0, main_y + 0.56, 6.2), rx(0.5), (0.1, 0.1, 0.6), "frame")
    sd.rope_coil(gg, bow, "coil_0", (0.75, main_y, 5.4), r=0.24, rope="rope")

    # ---- stern: round counter closed by the sternpost; the rudder hangs on it with the tiller inboard
    ctrl = [v3(0, ss.keel_y(AFT_END) - 0.05, AFT_END + 0.2), v3(0, 0.4, AFT_END - 0.15), v3(0, 1.4, -8.05), v3(0, sheer(AFT_END) + 0.15, -8.05)]
    pts = curve(ctrl, 4)
    for j in range(len(pts) - 1):
        t = j / (len(pts) - 1)
        reg = "hull_dark" if pts[j][1] < 0.3 else "hull_wale"
        round_bar(stern, "sternpost_%d" % j, pts[j], pts[j + 1], 0.34 * (1 - t) + 0.26 * t, reg, extend=0.04)
    add_cube(stern, "taffrail", (0, sheer(AFT_END) + 0.12, -7.95), EYE, (1.1, 0.1, 0.4), "rail")
    rudder = Bone("rudder", origin=(0, 0.4, ss.RUDDER_Z), parent=root)
    z_lead = ss.RUDDER_Z - 0.12
    nsl = 5
    for k in range(nsl):
        f0, f1 = k / nsl, (k + 1) / nsl
        fm = (f0 + f1) / 2
        y0, y1 = 0.3 - 1.5 * f0, 0.3 - 1.5 * f1
        chord = 0.4 + 0.3 * math.sin(math.pi * min(1.0, fm * 1.1)) ** 0.9
        add_cube(rudder, "rudder_blade_%d" % k, (0, (y0 + y1) / 2, z_lead - chord / 2), EYE, (0.16, y0 - y1 + 0.01, chord),
                 {"all": "hull_dark", "+1": "hull_wale", "-1": "hull_wale"})
    for k, y in enumerate((-0.9, -0.1)):
        add_cube(rudder, "pintle_%d" % k, (0, y, z_lead + 0.02), EYE, (0.24, 0.12, 0.2), "iron")
    # the stock rises through the counter to the tiller, which sweeps forward over the stern platform
    round_bar(rudder, "rudder_stock", (0, 0.3, z_lead - 0.12), (0, aft_y + 0.8, z_lead - 0.12), 0.18, "hull_wale")
    tiller_a, tiller_b = v3(0, aft_y + 0.8, z_lead - 0.1), v3(0, aft_y + 0.95, ss.HELM_Z + 0.75)
    round_bar(rudder, "tiller", tiller_a, tiller_b, 0.14, "hull_wale")
    disc(rudder, "tiller_grip", tiller_b, tiller_b - tiller_a, 0.09, 0.3, "frame", n=3)
    add_cube(rudder, "tiller_band", tiller_a + v3(0, 0, 0.3), EYE, (0.2, 0.2, 0.12), "iron")

    # ---- decks: planking right into the stem and the sternpost, the stern platform one step up, with its
    # front board and a half step in the middle
    n = 34
    z0, z1 = AFT_END + 0.2, FORE_END - 0.35
    for j in range(n):
        za = z0 + (z1 - z0) * j / n
        zb = z0 + (z1 - z0) * (j + 1) / n
        zm = (za + zb) / 2
        if za < ss.AFT_DECK_START < zb:
            zb = ss.AFT_DECK_START
        w = min(ss.inner_half_width(za), ss.inner_half_width(zb)) + 0.1
        add_cube(deck, "deck_%d" % j, (0, ss.deck_y(zm) - 0.06, (za + zb) / 2), EYE, (2 * w, 0.12, zb - za + 0.02),
                 {"all": "deck", "-2": "dark_wood"})
    wf = ss.inner_half_width(ss.AFT_DECK_START) + 0.1
    add_cube(deck, "aft_deck_front", (0, (main_y + aft_y) / 2, ss.AFT_DECK_START + 0.05), EYE, (2 * wf, aft_y - main_y, 0.1), "hull_light")
    add_cube(deck, "aft_deck_step", (0, main_y + 0.125, ss.AFT_DECK_START + 0.25), EYE, (1.0, 0.25, 0.4), {"all": "frame", "+2": "rail"})
    beam(deck, "aft_deck_edge", (-wf, aft_y + 0.02, ss.AFT_DECK_START + 0.05), (wf, aft_y + 0.02, ss.AFT_DECK_START + 0.05), 0.08, "rail",
         width=0.14)
    # hatch to the hold amidships, a grating in its coaming
    gn.g_hatch(deck, "hatch", 0.0, -1.0, 1.1, 1.3, main_y)

    # ---- benches, cargo (the same boxes are solid in the Java layout)
    for k, (x, z) in enumerate(ss.BENCH_SEATS):
        if x == 0:
            bench(deck, "bench_%d" % k, (x, main_y, z), 1.2, (1, 0, 0))
        else:
            bench(deck, "bench_%d" % k, (x, main_y, z), 1.1, (0, 0, 1))
    for k, (x, z, s) in enumerate(ss.CRATES):
        crate(cargo, "crate_%d" % k, x, z, ss.deck_y(z), s, yaw=0.0 if k % 2 else 0.12)
    for k, (x, z, r) in enumerate(ss.BARRELS):
        barrel(cargo, "barrel_%d" % k, x, z, ss.deck_y(z), r)
    # a sack and a small chest on the stern platform, a coil by the tiller
    add_cube(cargo, "sack", (-0.95, aft_y + 0.72 + 0.17, -6.3), ry(0.3), (0.5, 0.34, 0.42), "canvas")
    add_cube(cargo, "sack_tie", (-0.95, aft_y + 0.72 + 0.31, -6.3), ry(0.3), (0.16, 0.08, 0.16), "rope")
    add_cube(cargo, "chest", (1.0, aft_y + 0.7 + 0.14, -6.3), EYE, (0.5, 0.28, 0.4), {"all": "hull_wale", "+2": "dark_wood"})
    add_cube(cargo, "chest_band", (1.0, aft_y + 0.7 + 0.2, -6.3), EYE, (0.54, 0.06, 0.44), {"all": "iron", "+2": None, "-2": None})
    sd.rope_coil(gg, cargo, "coil_1", (-0.9, aft_y, -4.4), r=0.22, rope="rope")

    # ---- lantern davits at the quarters (an iron crane over the rail), a lantern under the bowsprit
    for k, side in enumerate((1, -1)):
        z = -6.6
        xr = side * (outer_x(z, sheer(z)) - 0.12)
        base = v3(xr, sheer(z) + 0.1, z)
        round_bar(lanterns, "davit_post_%d" % k, base, base + v3(0, 1.0, 0), 0.1, "iron")
        arm = curve([base + v3(0, 0.95, 0), base + v3(side * 0.15, 1.12, -0.05), base + v3(side * 0.4, 1.15, -0.15)], 2)
        for j in range(len(arm) - 1):
            beam(lanterns, "davit_arm_%d_%d" % (k, j), arm[j], arm[j + 1], 0.08, "iron", extend=0.02)
        beam(lanterns, "davit_brace_%d" % k, base + v3(0, 0.55, 0), base + v3(side * 0.34, 1.08, -0.12), 0.05, "iron")
        hanging_lantern(lanterns, "lantern_%d" % k, base + v3(side * 0.4, 1.12, -0.15), drop=0.3, s=1.0)
    hanging_lantern(lanterns, "lantern_bow", v3(0, hy - 0.3, 7.3), drop=0.25, s=0.9)

    # ---- mast with crosstrees and a pale truck; boom and gaff with their jaws; mast hoops
    mast = Bone("mast", origin=(0, main_y, MZ), parent=root)
    round_bar(mast, "mast_lower", (0, main_y - 0.3, MZ), (0, ss.CROSSTREE_Y + 0.5, MZ), 0.42, "mast")
    round_bar(mast, "mast_top", (0, ss.CROSSTREE_Y - 1.2, MZ + 0.02), (0, ss.MAST_TOP, MZ + 0.02), 0.26, "mast")
    _octo(mast, "mast_partners", (0, main_y + 0.12, MZ), EYE, (0.8, 0.24, 0.8), "frame")
    for k, y in enumerate((3.6, 6.8, 9.6)):
        disc(mast, "mast_band_%d" % k, (0, y, MZ), (0, 1, 0), 0.25, 0.12, "iron", n=3)
    cy = ss.CROSSTREE_Y
    add_cube(mast, "crosstree", (0, cy, MZ), EYE, (2.2, 0.14, 0.26), "mast")
    for k, z in enumerate((MZ + 0.3, MZ - 0.3)):
        add_cube(mast, "trestletree_%d" % k, (0, cy - 0.12, z), EYE, (0.7, 0.12, 0.14), "frame")
    _octo(mast, "mast_cap", (0, cy + 0.55, MZ), EYE, (0.62, 0.22, 0.62), "frame")
    disc(mast, "mast_cap_band", (0, cy + 0.4, MZ), (0, 1, 0), 0.3, 0.1, "iron", n=3)
    add_cube(mast, "truck", (0, ss.MAST_TOP + 0.12, MZ + 0.02), EYE, (0.3, 0.4, 0.3), "truck")
    add_cube(mast, "truck_top", (0, ss.MAST_TOP + 0.36, MZ + 0.02), EYE, (0.2, 0.12, 0.2), "truck")
    boom_a, boom_b = v3(0, ss.BOOM_Y, MZ - 0.25), v3(0, ss.BOOM_Y + 0.2, ss.BOOM_END_Z)
    round_bar(mast, "boom", boom_a, boom_b, 0.22, "mast", extend=0.1)
    round_bar(mast, "boom_roll", boom_a + v3(0, 0.2, -0.5), boom_b + v3(0, 0.2, 0.6), 0.2, "cloth_roll")
    py, pz = ss.GAFF_PEAK
    gaff_a, gaff_b = v3(0, ss.GAFF_THROAT_Y, MZ - 0.3), v3(0, py, pz)
    round_bar(mast, "gaff", gaff_a, gaff_b + norm(gaff_b - gaff_a) * 0.3, 0.17, "mast")
    for k, (p, y) in enumerate(((boom_a, ss.BOOM_Y), (gaff_a, ss.GAFF_THROAT_Y))):
        for side in (1, -1):
            add_cube(mast, "jaws_%d_%d" % (k, side > 0), v3(side * 0.24, y, MZ - 0.05), EYE, (0.1, 0.3, 0.6), "frame")
    for k in range(6):
        y = ss.BOOM_Y + 0.9 + k * 1.15
        disc(mast, "hoop_%d" % k, (0, y, MZ - 0.02), (0, 1, 0), 0.3, 0.07, "rope", n=3)
    disc(mast, "boom_gooseneck", (0, ss.BOOM_Y, MZ), (0, 1, 0), 0.3, 0.14, "iron", n=3)
    sd.rope_coil(gg, fittings, "coil_2", (-1.5, main_y, 1.9), r=0.2, rope="rope")

    # ---- the sails: a big gaff mainsail aft of the mast (its bone pivots on the boom at the mast, so that
    # it furls down onto the boom), a large jib from the mast head to the bowsprit end
    tris = {}
    sb = Bone("sail_main", origin=(0, ss.BOOM_Y + 0.1, MZ), parent=mast)
    quad_sail(sb, "sail_main", gaff_a + v3(0, -0.12, 0.05), gaff_b + v3(0, -0.14, 0.15), boom_a + v3(0, 0.22, 0.0),
              boom_b + v3(0, 0.22, 0.25), 1.1, v3(1, 0, 0), "sail_main", nx=8, ny=9)
    jib_head = v3(0, ss.JIB_HEAD_Y, MZ + 0.3)
    tack = tip + v3(0, 0.18, -0.3)
    jy, jz = ss.JIB_CLEW
    jb = Bone("sail_jib", origin=tuple(tack), parent=root)
    # every cell of the grid is kept (the cloth painted with its bowed edges spills a little past the triangle)
    tris["sail_jib"] = gn.tri_sail(jb, "sail_jib", jib_head, tack, v3(0.05, jy, jz), 0.95, v3(1, 0, 0), "sail_jib", nx=6, ny=9)

    # ---- rigging: forestay and jib stay to the bowsprit, bobstay, shrouds with ratlines, backstays,
    # peak halyard, topping lift, the sheets
    head = v3(0, ss.MAST_TOP - 0.5, MZ + 0.15)
    rig = [("forestay", head, tip + v3(0, 0.22, -0.05)),
           ("jib_stay", jib_head + v3(0, 0.12, 0.02), tack + v3(0, 0.04, 0)),
           ("bobstay", tip + v3(0, -0.14, -0.1), v3(0, 0.55, 8.15)),
           ("peak_halyard", v3(0, ss.MAST_TOP - 0.9, MZ - 0.15), gaff_b - norm(gaff_b - gaff_a) * 1.2 + v3(0, 0.1, 0)),
           ("topping_lift", v3(0, cy - 0.4, MZ - 0.25), boom_b + v3(0, 0.12, 0.05)),
           ("main_sheet", boom_b + v3(0, -0.1, 0.1), v3(0, aft_y + 0.1, -7.2)),
           ("jib_sheet_p", v3(0.05, jy, jz), v3(0.97 * hw(1.0), sheer(1.0) + 0.06, 1.0)),
           ("jib_sheet_s", v3(0.05, jy, jz), v3(-0.97 * hw(1.0), sheer(1.0) + 0.06, 1.0))]
    for side, sn in SIDES:
        rig.append(("backstay_%s" % sn, v3(side * 0.1, ss.MAST_TOP - 0.7, MZ), v3(side * 0.97 * hw(-6.2), sheer(-6.2) + 0.06, -6.2)))
        chains = []
        for k, z in enumerate((MZ + 0.35, MZ - 1.0)):
            top = v3(side * 0.22, cy - 0.1, MZ)
            foot = v3(side * (outer_x(z, sheer(z)) + 0.02), sheer(z) + 0.06, z)
            rig.append(("shroud_%s%d" % (sn, k), top, foot))
            chains.append((top, foot))
            # deadeye and chainplate on the outside of the wale
            disc(ropes, "deadeye_%s%d" % (sn, k), foot - v3(0, 0.0, 0) + v3(side * 0.08, -0.18, 0), v3(side, 0, 0), 0.11, 0.1, "frame", n=3)
            beam(ropes, "chainplate_%s%d" % (sn, k), foot + v3(side * 0.1, -0.3, 0), foot + v3(side * 0.1, -0.9, 0), 0.05, "iron", width=0.09)
        (t0, f0), (t1, f1) = chains
        for j in range(7):
            f = (0.85 + j * 0.95) / (cy - 0.1 - sheer(MZ))
            if f > 0.93:
                break
            a, b = t0 + (f0 - t0) * (1 - f), t1 + (f1 - t1) * (1 - f)
            beam(ropes, "ratline_%s%d" % (sn, j), a, b, 0.035, "rope", extend=0.02)
    for name, a, b in rig:
        beam(ropes, "rope_" + name, a, b, 0.045, "rope")
    # a slack coil of the halyard hanging from the mast, swaying (rope_sway)
    slack = Bone("rope_slack_0", origin=(0.26, main_y + 1.6, MZ + 0.1), parent=mast)
    pts = curve([v3(0.26, main_y + 1.6, MZ + 0.1), v3(0.38, main_y + 1.2, MZ + 0.28), v3(0.36, main_y + 0.8, MZ + 0.3), v3(0.3, main_y + 0.5, MZ + 0.22)], 3)
    for j in range(len(pts) - 1):
        beam(slack, "rope_slack_%d" % j, pts[j], pts[j + 1], 0.045, "rope", extend=0.015)
    return root, tris, [sb, jb]


def build_animations(root, sails):
    kf, rot_kf, animation, find = gg.kf, gg.rot_kf, gg.animation, gg.find
    anims = []
    tracks = []
    for k, b in enumerate(sails):
        ph = 0.5 * k
        tracks.append((b, [kf("scale", t, (s, 1, 1), "catmullrom") for t, s in ((0, 1.0), (0.9 + ph * 0.2, 1.1), (1.8, 0.95),
                                                                                (2.7, 1.05), (3.6, 1.0))] +
                       [rot_kf(t, (0, 0, a), "catmullrom") for t, a in ((0, 0), (1.2, 0.6), (2.4, -0.5), (3.6, 0))]))
    anims.append(animation("sail_wind", 3.6, "loop", tracks))
    # furled: the mainsail drops onto its boom (its bone pivots on the boom), the jib gathers to its tack
    anims.append(animation("sail_furl", 1.0, "hold", [
        (sails[0], [kf("scale", 0.0, (1, 1, 1)), kf("scale", 1.0, (0.3, 0.02, 1))]),
        (sails[1], [kf("scale", 0.0, (1, 1, 1)), kf("scale", 1.0, (0, 0, 0))])]))
    rudder = find(root, "rudder")
    anims.append(animation("steer", 2.0, "hold", [
        (rudder, [rot_kf(0.0, (0, -28, 0)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 28, 0))])]))
    tracks = []
    for k, name in enumerate(["lantern_0", "lantern_1", "lantern_bow"]):
        b = find(root, name)
        a = 5 if k < 2 else 7
        ph = 0.4 * k
        kfs = [rot_kf((ph + t) % 2.4, (a * math.cos(2 * math.pi * t / 2.4), 0, a * 0.6 * math.sin(2 * math.pi * t / 2.4)), "catmullrom")
               for t in (0.0, 0.6, 1.2, 1.8)]
        kfs.sort(key=lambda q: q["time"])
        tracks.append((b, kfs))
    anims.append(animation("lantern_sway", 2.4, "loop", tracks))
    slack = find(root, "rope_slack_0")
    anims.append(animation("rope_sway", 2.8, "loop", [
        (slack, [rot_kf(0, (0, 0, 4), "catmullrom"), rot_kf(0.9, (3, 0, -3), "catmullrom"), rot_kf(1.9, (-3, 0, -4), "catmullrom"),
                 rot_kf(2.8, (0, 0, 4), "catmullrom")])]))
    return anims


def main():
    root, tris, sails = build()
    anims = build_animations(root, sails)
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    tex_path = os.path.join(tex_dir, "entity/trade_sloop.png")
    st.make_texture(tex_path, tris)
    st.make_item_icon(os.path.join(tex_dir, "item/trade_sloop.png"))
    with open(tex_path, "rb") as f:
        png = f.read()
    textures = [gn.texture_entry("trade_sloop.png", st.SIZE, png, "entity", "trade_sloop.png")]
    textures[0]["id"] = "0"
    model = gn.export(root, anims, textures, [
        os.path.join(ROOT, "blockbench/trade_sloop.bbmodel"),
        os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/trade_sloop.bbmodel"),
    ], name="trade_sloop", visible_box=(22, 16, 0))
    print("cubes:", len(model["elements"]), "animations:", [a["name"] for a in model["animations"]])


if __name__ == "__main__":
    main()
