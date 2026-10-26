#!/usr/bin/env python3
"""Generates the Dragon Junk (dragon_junk) Blockbench model, its textures, its item icon, its interior grid and
its furniture file.

Usage:  python3 tools/generate_junk.py        (JUNK_FAST=1: no z-fighting pass, for quick previews)

Outputs:
  blockbench/dragon_junk.bbmodel                                            (editable, textures embedded)
  src/main/resources/assets/medievalships/models/entity/dragon_junk.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/dragon_junk.png, dragon_junk_interior.png, dragon_junk_sail.png
  src/main/resources/assets/medievalships/textures/item/dragon_junk.png
  src/main/resources/assets/medievalships/interiors/dragon_junk.grid         (collisions, ladder, doors)
  src/main/resources/assets/medievalships/interiors/dragon_junk_decor.json   (mod furniture, seats)

Reference: the Minecraft sheet "La Jonque du Dragon" (perspective, side, top, front and back views, five interior
views; measurements in docs/JUNK_PLAN.md). A long dark wooden hull curving up to a high stern, a pale beak pointing
forwards low down under a square bow, a white band of plaster blocks with dark posts along the bulwarks, red
lacquered panels between dark posts along the quarterdeck, a multi-level stern house of white plaster and dark
beams under a tall red roof of four stacked tiers with upturned edges and pale bamboo battens, the companion house
with its own red gable roof and a carved white post at the break, one mast stepped far forward and raked aft, the
great red sail with the black dragon: two battened panels hung from a short yard under the masthead and spread in a
V, their clews held out by long pale booms; a small cream sail under the bowsprit, lanterns on posts, an outside
stair on the hull side, balustrades, the anchor hanging on its chain.

The hull is a body of boards between 40 stations (no staircase). The decks, the walls, floors and ceilings of the
rooms are drawn on the boundaries of the interior grid (tools/junk_interior.py): what is drawn is what collides.

Bones used by the mod (keep their names when editing in Blockbench):
  helm_wheel, rudder (steer)   sail_p, sail_s, bow_sail (sail_wind: the panels breathe, the bow sail flaps)
  pennant_* (streamer_wave)   flag, flag_tip (flag_wave)   lantern_* (lantern_sway)   rope_slack_* (rope_sway)
  door_<k> (door k: 0 = closed, 1 = open)   rooms, furniture, fittings (hidden far away)   detail (hidden very far)
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
import generate_leviathan as gl  # noqa: E402  (its generic helpers: plates, ropes, chains, lanterns, wheel, balustrades)
import leviathan_texture as lt  # noqa: E402
import junk_shape as js  # noqa: E402
import junk_interior as ji  # noqa: E402
import junk_texture as jt  # noqa: E402
import junk_decor as jd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/dragon_junk/%d" % _uuid_counter[0]))


gg.new_uuid = new_uuid
gn.new_uuid = new_uuid
gl.new_uuid = new_uuid
REGIONS = {k: (0,) + r for k, r in jt.REGIONS.items()}
REGIONS.update({k: (1,) + r for k, r in lt.REGIONS_IN.items()})          # the rooms and their furniture: second texture
REGIONS.update({k: (1,) + r for k, r in jt.REGIONS_IN_EXTRA.items()})
REGIONS["globe"] = (1,) + lt.REGIONS_IN["in_globe"]
REGIONS["sail"] = (2,) + jt.REGIONS_SAIL["sail"]                          # the great sail: third texture
gn.REGIONS = REGIONS
gn.SIZE = jt.SIZE

v3, norm, Bone, add_cube, beam = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam
tube, disc, ring, polyline, catmull = ga.tube, ga.disc, ga.ring, ga.polyline, ga.catmull
quad, rope, chain, set_sub = gl.quad, gl.rope, gl.chain, gl.set_sub
EYE = np.eye(3)
SIDES = ((1, "p"), (-1, "s"))
M0, QD, LO = js.MAIN_DECK_Y, js.QUARTERDECK_Y, js.LOWER_DECK_Y
BZ, SZ = js.BOW_Z, js.STERN_Z


def sm(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def box(bone, name, c, size, region, R=EYE, **kw):
    return add_cube(bone, name, v3(*c), R, size, region, **kw)


def hp(z, y, side, out=0.0):
    """Point on the outside of the hull at (z, y), pushed out by `out` along x."""
    return v3(side * (js.hull_x(z, y) + out), y, z)


# ================================================================ hull
STATIONS = [SZ, -19.15, -18.7, -18.1, -17.4, -16.6, -15.7, -14.7, -13.6, -12.4, -11.1, -9.7, -8.3, -6.9, -5.5, -4.1, -2.7, -1.5, -0.3,
            0.9, 2.2, 3.6, 5.0, 6.4, 7.8, 9.2, 10.6, 11.9, 13.1, 14.2, 15.2, 16.1, 16.9, 17.6, 18.2, 18.7, 19.15, BZ]
BEAK_STATIONS = [BZ, 20.1, 20.7, 21.25, 21.75, 22.2, js.BEAK_TIP_Z - 0.02]
LOW_F = (0.0, 0.1, 0.24, 0.4, 0.58, 0.78, 1.0)
WALE_TOP = js.WALE_Y + 0.4


def aft_f(z):
    """0 forward of the break's rise, 1 aft of the break (the red band and the higher white band)."""
    return sm((js.BREAK_RISE[0] - 0.3 - z) / 1.6)


def red_top(z):
    return WALE_TOP + (js.RED_BAND[1] - WALE_TOP) * aft_f(z)


def hull_rows(z):
    """(y, region of the strake above, back region) of a station, from the keel up to the sheer (the first point is
    the middle of the flat bottom)."""
    k = js.keel_y(z)
    beak = z > BZ + 1e-6
    yw = js.beak_top(z) if beak else js.WALE_Y
    yw = max(yw, k)
    rows = []
    low_reg = "beak" if z > 15.6 else "hull_low"
    mid_reg = "beak" if z > 15.6 else "hull"
    for i, f in enumerate(LOW_F):
        y = k + (yw - k) * f
        rows.append((y, low_reg if f < 0.3 else mid_reg))
    if not beak:
        sh = js.sheer_y(z)
        yt = max(k, min(WALE_TOP, sh))
        rows.append((yt, "red_panel" if aft_f(z) > 0.5 else "plaster"))
        yr = max(yt, min(red_top(z), sh))
        rows.append((yr, "plaster"))
        rows.append((sh, None))
        rows[len(LOW_F) - 1] = (rows[len(LOW_F) - 1][0], "wale")
    else:
        rows[-1] = (rows[-1][0], None)
    return k, rows


def section_pts(z, side):
    k, rows = hull_rows(z)
    pts = [v3(0.0, k, z)]
    regs = [rows[0][1]]
    for y, reg in rows:
        pts.append(v3(side * js.hull_x(min(z, js.BEAK_TIP_Z - 0.03), y + (1e-4 if y <= k + 1e-6 else 0.0)), y, z))
        regs.append(reg)
    return pts, regs


def hull(bone, detail):
    n = 0
    for stations, tag in ((STATIONS, "h"), (BEAK_STATIONS, "b")):
        for side, sn in SIDES:
            for i in range(len(stations) - 1):
                za, zb = stations[i], stations[i + 1]
                A, regs = section_pts(za, side)
                B, _ = section_pts(zb, side)
                m = min(len(A), len(B))
                for r in range(m - 1):
                    reg = regs[r]
                    if reg is None:
                        continue
                    a0, a1, b0, b1 = A[r], A[r + 1], B[r], B[r + 1]
                    if np.linalg.norm(a1 - a0) + np.linalg.norm(b1 - b0) < 0.03:
                        continue
                    mid = (a0 + a1 + b0 + b1) / 4
                    t = (a1 + b1) - (a0 + b0)
                    outward = norm(v3(side * t[1], -side * t[0], 0) + v3(0, -0.2 if r == 0 else 0.0, 0))
                    above_deck = (a0[1] + b0[1]) / 2 >= js.deck_y((za + zb) / 2) - 0.05
                    region = reg
                    back = "plank_light" if above_deck else "hull"
                    q = quad(bone, "hull_%s%s%d_%d" % (tag, sn, i, r), a0, b0, a1, b1, 0.12, region, outward, back=back,
                             u_dir=v3(0, 0, 1), v_dir=v3(0, -1, 0), stretch=region in ("red_panel",), overlap=(1.03, 1.04))
                    if q is not None:
                        n += 1
    # the keel: a dark timber along the bottom, rising into the beak and up the transom
    zz = [z for z in STATIONS if z > SZ + 0.3] + BEAK_STATIONS[1:]
    for i in range(len(zz) - 1):
        a, b = zz[i], zz[i + 1]
        beam(bone, "keel_%d" % i, (0, js.keel_y(a) - 0.06, a), (0, js.keel_y(b) - 0.06, b), 0.22, "wale", width=0.3, extend=0.05)
    return n


def bow_face(bone, detail):
    """The square bow: a flat face from the wale up to the bulwark, white plaster blocks between dark corner posts,
    a heavy dark beam on top, iron straps; the beak's top under it, sloping down to the tip."""
    z = BZ
    ys = [js.WALE_Y, WALE_TOP, 0.0, js.SHEER_FORE]
    for k in range(len(ys) - 1):
        ya, yb = ys[k], ys[k + 1]
        w = js.hull_x(z - 0.01, (ya + yb) / 2) + 0.02
        quad(bone, "bow_face_%d" % k, v3(-w, ya, z), v3(w, ya, z), v3(-w, yb, z), v3(w, yb, z), 0.14, "wale" if k == 0 else "plaster",
             v3(0, 0, 1), back="plank_light", u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0), stretch=False)
    w = js.hull_x(z - 0.01, 0.5)
    for side, sn in SIDES:
        box(bone, "bow_corner_post_" + sn, (side * (w - 0.18), (js.WALE_Y + js.SHEER_FORE + 0.3) / 2, z - 0.12),
            (0.42, js.SHEER_FORE + 0.3 - js.WALE_Y, 0.42), "post")
        box(bone, "bow_corner_cap_" + sn, (side * (w - 0.18), js.SHEER_FORE + 0.38, z - 0.12), (0.5, 0.16, 0.5), "dark_wood")
        for k, y in enumerate((-0.9, 0.0, 0.7)):
            box(detail, "bow_strap_%s_%d" % (sn, k), (side * (w - 0.6), y, z + 0.02), (0.5, 0.08, 0.05), "iron")
    for x in (-1.2, 1.2):
        box(bone, "bow_post_%d" % (x > 0), (x, (js.WALE_Y + js.SHEER_FORE) / 2, z + 0.03), (0.3, js.SHEER_FORE - js.WALE_Y, 0.12), "post")
    beam(bone, "bow_head_beam", (-w - 0.1, js.SHEER_FORE + 0.12, z - 0.15), (w + 0.1, js.SHEER_FORE + 0.12, z - 0.15), 0.26, "dark_wood",
         width=0.5)
    beam(bone, "bow_wale_beam", (-w - 0.05, js.WALE_Y + 0.05, z + 0.02), (w + 0.05, js.WALE_Y + 0.05, z + 0.02), 0.2, "wale", width=0.2)
    # the beak's top: from the bow face down to the tip, pale planks with an iron strap; the shelf under the bow
    zz = BEAK_STATIONS
    for i in range(len(zz) - 1):
        za, zb = zz[i], zz[i + 1]
        ya, yb = js.beak_top(za), js.beak_top(zb)
        wa, wb = js.hull_x(za, ya - 1e-3), js.hull_x(min(zb, js.BEAK_TIP_Z - 0.03), yb - 1e-3)
        if wa < 0.02 and wb < 0.02:
            continue
        quad(bone, "beak_top_%d" % i, v3(-wa, ya, za), v3(wa, ya, za), v3(-wb, yb, zb), v3(wb, yb, zb), 0.1, "beak", v3(0, 1, 0.5),
             u_dir=v3(1, 0, 0), v_dir=v3(0, 0, 1), stretch=False)
    # the shelf: the underside of the square bow where it overhangs the narrowing lower hull
    for i, z0 in enumerate((15.6, 16.6, 17.6, 18.6)):
        z1 = min(BZ, z0 + 1.0)
        for side, sn in SIDES:
            xi0, xi1 = js.hull_x(z0, js.WALE_Y - 0.25), js.hull_x(z1, js.WALE_Y - 0.25)
            xo0, xo1 = js.hull_x(z0, js.WALE_Y + 0.01), js.hull_x(z1, js.WALE_Y + 0.01)
            if xo0 - xi0 < 0.1 and xo1 - xi1 < 0.1:
                continue
            quad(bone, "bow_shelf_%s%d" % (sn, i), v3(side * xi0, js.WALE_Y, z0), v3(side * xo0, js.WALE_Y, z0), v3(side * xi1, js.WALE_Y, z1),
                 v3(side * xo1, js.WALE_Y, z1), 0.08, "wale", v3(0, -1, 0), stretch=False)
    # iron straps over the beak, its tip capped with iron
    for k, f in enumerate((0.25, 0.55, 0.82)):
        z = BZ + (js.BEAK_TIP_Z - BZ) * f
        y0, y1 = js.keel_y(z), js.beak_top(z)
        for side, sn in SIDES:
            pts = [hp(z, y0 + (y1 - y0) * t, side, 0.06) for t in (0.0, 0.5, 1.0)]
            for j in range(2):
                beam(detail, "beak_strap_%s%d_%d" % (sn, k, j), pts[j], pts[j + 1], 0.05, "iron", width=0.14, extend=0.02)
    box(bone, "beak_tip_cap", (0, js.BEAK_TIP_Y + 0.12, js.BEAK_TIP_Z - 0.25), (0.34, 0.34, 0.5), "iron")


def transom(bone, detail, lights):
    """The flat stern: the red lacquered band between dark posts, the white band, then the stern house's back wall
    (white plaster in a dark timber frame, three lit lattice windows) up to the eaves."""
    z = SZ
    k = js.keel_y(z)
    ys = [k, js.RED_BAND[1], QD]
    regs = ["red_panel", "plaster"]
    for i in range(len(ys) - 1):
        ya, yb = ys[i], ys[i + 1]
        n = 4
        for j in range(n):
            # split in strips of the hull's width at their height
            y0 = ya + (yb - ya) * j / n
            y1 = ya + (yb - ya) * (j + 1) / n
            w = js.hull_x(z + 0.01, (y0 + y1) / 2) + 0.02
            quad(bone, "transom_%d_%d" % (i, j), v3(w, y0, z), v3(-w, y0, z), v3(w, y1, z), v3(-w, y1, z), 0.14, regs[i], v3(0, 0, -1),
                 back="hull", u_dir=v3(-1, 0, 0), v_dir=v3(0, -1, 0), stretch=False)
    w = js.hull_x(z + 0.01, 1.0)
    for x in np.linspace(-w + 0.15, w - 0.15, 6):
        box(bone, "transom_post_%d" % int(round(x * 10)), (x, (k + QD) / 2 + 0.1, z - 0.06), (0.24, QD - k - 0.1, 0.16), "post")
    beam(bone, "transom_rudder_post", (0, k - 0.1, z - 0.18), (0, QD + 0.6, z - 0.18), 0.34, "post", width=0.3)
    for j, y in enumerate(np.linspace(k + 0.4, QD - 0.2, 4)):
        box(detail, "transom_gudgeon_%d" % j, (0, y, z - 0.25), (0.5, 0.12, 0.22), "iron")
    beam(bone, "transom_rail_low", (-w - 0.1, js.RED_BAND[1], z - 0.1), (w + 0.1, js.RED_BAND[1], z - 0.1), 0.18, "dark_wood", width=0.22)
    beam(bone, "transom_rail_top", (-w - 0.15, QD, z - 0.12), (w + 0.15, QD, z - 0.12), 0.24, "rail", width=0.3)


# ================================================================ hull dressing: wales, posts, rails, the gallery
def side_line(bone, name, yfn, z0, z1, side, out, th, width, region, n=None):
    zz = [z for z in STATIONS if z0 <= z <= z1]
    if not zz or zz[0] > z0 + 1e-6:
        zz = [z0] + zz
    if zz[-1] < z1 - 1e-6:
        zz.append(z1)
    for i in range(len(zz) - 1):
        a, b = zz[i], zz[i + 1]
        pa, pb = hp(a, yfn(a), side, out), hp(b, yfn(b), side, out)
        beam(bone, "%s_%d" % (name, i), pa, pb, th, region, width=width, extend=0.04)


def hull_dressing(bone, detail):
    for side, sn in SIDES:
        # the dark wale under the white band, a rubbing strake along the bottom of the red band aft
        side_line(bone, "wale_" + sn, lambda z: js.WALE_Y + 0.12, SZ + 0.05, BZ - 0.02, side, 0.05, 0.28, 0.2, "wale")
        side_line(bone, "wale2_" + sn, lambda z: WALE_TOP - 0.02, SZ + 0.05, BZ - 0.02, side, 0.03, 0.12, 0.14, "dark_wood")
        side_line(bone, "redband_rail_" + sn, lambda z: js.RED_BAND[1], SZ + 0.05, js.BREAK_RISE[1] + 0.3, side, 0.05, 0.16, 0.18,
                  "dark_wood")
        # the cap rail on the bulwark, along the sheer
        side_line(bone, "cap_rail_" + sn, lambda z: js.sheer_y(z) + 0.06, js.HOUSE_FRONT_Z, BZ - 0.05, side, -0.2, 0.16, 0.56, "rail")
        # dark posts on the hull side: through the white band forward, between the red panels aft
        z = BZ - 1.4
        k = 0
        while z > SZ + 0.6:
            aft = aft_f(z) > 0.5
            y0 = js.WALE_Y + 0.1
            y1 = js.sheer_y(z) + (0.1 if not aft else 0.0)
            p0, p1 = hp(z, y0, side, 0.07), hp(z, y1, side, 0.07)
            beam(bone, "hull_post_%s%d" % (sn, k), p0, p1, 0.3 if not aft else 0.22, "post", width=0.16, up=v3(side, 0, 0))
            if not aft and k % 2 == 0:
                for j, y in enumerate((-0.6, 0.4)):
                    box(detail, "hull_bolt_%s%d_%d" % (sn, k, j), hp(z, y, side, 0.17), (0.08, 0.08, 0.08), "iron")
            z -= 2.55 if not aft else 1.3
            k += 1
        # the dark lower posts / frames on the dark hull (the reference's vertical dark battens), every other station
        for j, z in enumerate((14.2, 9.2, 3.6, -2.7, -8.3, -13.6)):
            ks = js.keel_y(z)
            pts = [hp(z, ks + (js.WALE_Y - ks) * t, side, 0.05) for t in (0.25, 0.6, 1.0)]
            for i in range(2):
                beam(detail, "hull_frame_%s%d_%d" % (sn, j, i), pts[i], pts[i + 1], 0.06, "dark_wood", width=0.22, extend=0.03)


def quarter_gallery(bone, detail):
    """Along the quarterdeck: the red lattice panels and dark posts of the balustrade (the grid's rail cells),
    across the deck's front edge between the stair and the companion house."""
    y = QD
    for side, sn in SIDES:
        zz = np.linspace(js.HOUSE_FRONT_Z + 0.1, js.BREAK_Z - 0.05, 6)
        pts = [(side * (js.hull_x(z, y - 0.1) - 0.22), y, z) for z in zz]
        for k in range(len(pts) - 1):
            a, b = v3(*pts[k]), v3(*pts[k + 1])
            tube(bone, "qd_rail_post_%s%d" % (sn, k), a, a + v3(0, 1.05, 0), 0.2, "dark_wood", sides=4)
            beam(bone, "qd_rail_top_%s%d" % (sn, k), a + v3(0, 1.0, 0), b + v3(0, 1.0, 0), 0.12, "rail", width=0.22, extend=0.08)
            beam(bone, "qd_rail_bottom_%s%d" % (sn, k), a + v3(0, 0.12, 0), b + v3(0, 0.12, 0), 0.1, "rail", width=0.16, extend=0.05)
            quad(bone, "qd_lattice_%s%d" % (sn, k), a + v3(0, 0.18, 0), b + v3(0, 0.18, 0), a + v3(0, 0.94, 0), b + v3(0, 0.94, 0), 0.04,
                 "lattice", v3(side, 0, 0), u_dir=b - a, v_dir=v3(0, -1, 0))
        b = v3(*pts[-1])
        tube(bone, "qd_rail_post_%s_end" % sn, b, b + v3(0, 1.05, 0), 0.2, "dark_wood", sides=4)
    # across the front edge, between the stair (starboard) and the companion house (port)
    zc = js.BREAK_Z - 0.2
    x0, x1 = ji.QD_FRONT_RAIL
    a, b = v3(x0 + 0.1, y, zc), v3(x1 - 0.05, y, zc)
    for p in (a, b):
        tube(bone, "qd_front_post_%d" % (p[0] > 0), p, p + v3(0, 1.05, 0), 0.2, "dark_wood", sides=4)
    beam(bone, "qd_front_top", a + v3(0, 1.0, 0), b + v3(0, 1.0, 0), 0.12, "rail", width=0.22, extend=0.08)
    quad(bone, "qd_front_lattice", a + v3(0, 0.18, 0), b + v3(0, 0.18, 0), a + v3(0, 0.94, 0), b + v3(0, 0.94, 0), 0.04, "lattice", v3(0, 0, 1),
         u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0))


# ================================================================ decks
MAX_TILE = 8


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


def grid_floor(bone, g, y, region, name, lit=False, zrange=None, xrange=None):
    """Top faces of the solid cells at height y walked on (open or room cells above them), 4 block tiles."""
    j = int(round((y - ji.Y0) / ji.CELL))
    below = g.k[:, j - 1, :]
    above = g.k[:, j, :]
    mask = (below == ji.SOLID) & ((above == ji.OUT) | (above == ji.DRY) | (above == ji.FURNITURE) | (above >= ji.DOOR))
    if zrange is not None:
        mask &= ((g.zs >= zrange[0]) & (g.zs <= zrange[1]))[None, :]
    if xrange is not None:
        mask &= ((g.xs >= xrange[0]) & (g.xs <= xrange[1]))[:, None]
    key = np.zeros(mask.shape, dtype=np.int16)
    count = 0
    for (i0, j0, i1, j1, kk) in greedy(mask, key, True, True):
        x0, x1 = ji.X0 + i0 * ji.CELL, ji.X0 + (i1 + 1) * ji.CELL
        z0, z1 = ji.Z0 + j0 * ji.CELL, ji.Z0 + (j1 + 1) * ji.CELL
        cube = add_cube(bone, "%s%s_%d" % ("lit_" if lit else "", name, count), v3((x0 + x1) / 2, y - 0.005, (z0 + z1) / 2), EYE,
                        (x1 - x0, 0.01, z1 - z0), {"+2": region}, u_dir=v3(0, 0, 1), v_dir=v3(1, 0, 0))
        set_sub(cube, ((j0 % MAX_TILE) / MAX_TILE, (i0 % MAX_TILE) / MAX_TILE, (j1 % MAX_TILE + 1) / MAX_TILE, (i1 % MAX_TILE + 1) / MAX_TILE))
        count += 1
    return count


def decks(bone, detail, g):
    n = grid_floor(bone, g, M0, "deck", "main_deck", zrange=(js.BREAK_Z - 0.6, BZ))
    n += grid_floor(bone, g, QD, "deck", "quarterdeck", zrange=(js.HOUSE_FRONT_Z - 0.1, js.BREAK_Z + 0.1))
    # the waterways: dark planks along the bulwarks over the edge of the deck, the inner lining of the bulwark
    for side, sn in SIDES:
        for (z0, z1, y) in ((js.BREAK_Z + 0.3, BZ - 0.5, M0), (js.HOUSE_FRONT_Z, js.BREAK_Z - 0.05, QD)):
            zz = list(np.arange(z0, z1, 1.5)) + [z1]
            for i in range(len(zz) - 1):
                a, b = zz[i], zz[i + 1]
                xa, xb = js.hull_x(a, y + 0.2), js.hull_x(b, y + 0.2)
                quad(bone, "waterway_%s%d_%d" % (sn, int(y), i), v3(side * (xa - 0.75), y + 0.02, a), v3(side * (xa - 0.08), y + 0.02, a),
                     v3(side * (xb - 0.75), y + 0.02, b), v3(side * (xb - 0.08), y + 0.02, b), 0.04, "dark_wood", v3(0, 1, 0),
                     u_dir=v3(0, 0, 1), v_dir=v3(1, 0, 0), stretch=False)
    zb = BZ - 0.5
    w = js.hull_x(zb, 0.2)
    quad(bone, "waterway_bow", v3(-w, M0 + 0.02, zb - 0.3), v3(w, M0 + 0.02, zb - 0.3), v3(-w, M0 + 0.02, BZ - 0.08),
         v3(w, M0 + 0.02, BZ - 0.08), 0.04, "dark_wood", v3(0, 1, 0), u_dir=v3(1, 0, 0), v_dir=v3(0, 0, 1), stretch=False)
    # the bulwark's cap at the bow
    beam(bone, "bow_cap_rail", (-w, js.SHEER_FORE + 0.06, BZ - 0.2), (w, js.SHEER_FORE + 0.06, BZ - 0.2), 0.16, "rail", width=0.56)
    # the grating amidships (decorative: the deck is solid under it)
    gx, gz0, gz1 = 1.5, 4.5, 7.5
    quad(bone, "grating", v3(-gx, M0 + 0.06, gz0), v3(gx, M0 + 0.06, gz0), v3(-gx, M0 + 0.06, gz1), v3(gx, M0 + 0.06, gz1), 0.05, "grating",
         v3(0, 1, 0), u_dir=v3(1, 0, 0), v_dir=v3(0, 0, 1))
    quad(bone, "grating_shadow", v3(-gx, M0 + 0.012, gz0), v3(gx, M0 + 0.012, gz0), v3(-gx, M0 + 0.012, gz1), v3(gx, M0 + 0.012, gz1), 0.01,
         "roof_under", v3(0, 1, 0))
    for k, (a, b) in enumerate((((-gx - 0.12, gz0 - 0.12), (gx + 0.12, gz0 - 0.12)), ((-gx - 0.12, gz1 + 0.12), (gx + 0.12, gz1 + 0.12)),
                                ((-gx - 0.12, gz0 - 0.12), (-gx - 0.12, gz1 + 0.12)), ((gx + 0.12, gz0 - 0.12), (gx + 0.12, gz1 + 0.12)))):
        beam(bone, "grating_coaming_%d" % k, (a[0], M0 + 0.1, a[1]), (b[0], M0 + 0.1, b[1]), 0.2, "dark_wood", width=0.26, extend=0.12)
    return n


def stairs(outside, inside):
    for st in ji.STAIRS:
        name, x0, x1, zs, d, y0, n = st
        interior = n < 0
        bone = inside if interior else outside
        pre = "lit_" if interior else ""
        for k, (sx0, sx1, sz0, sz1, top) in enumerate(ji.stair_steps(st)):
            bottom = top - 0.5 if interior else y0
            c = v3((sx0 + sx1) / 2, (top + bottom) / 2, (sz0 + sz1) / 2)
            add_cube(bone, "%sstair_%s_%d" % (pre, name, k), c, EYE, (sx1 - sx0, top - bottom, sz1 - sz0),
                     {"all": "dark_wood" if not interior else "in_beam", "+2": "deck" if not interior else "in_floor"}, u_dir=v3(1, 0, 0))
            nose_z = sz1 if d > 0 else sz0
            if not interior:
                nose_z = sz1
            add_cube(bone, "%sstair_%s_%d_nose" % (pre, name, k), v3(c[0], top - 0.04, nose_z), EYE, (sx1 - sx0 + 0.02, 0.08, 0.08),
                     "rail" if not interior else "in_beam")
        if not interior:
            steps = ji.stair_steps(st)
            xin = x1   # the open side, towards the middle of the deck
            pts = [v3(xin - 0.08, s[4], (s[2] + s[3]) / 2) for s in steps]
            tube(outside, "stair_%s_newel" % name, pts[0] + v3(0, -0.5, 0.25), pts[0] + v3(0, 0.6, 0.25), 0.2, "dark_wood", sides=4)
            beam(outside, "stair_%s_handrail" % name, pts[0] + v3(0, 0.55, 0.25), pts[-1] + v3(0, 0.95, -0.2), 0.1, "rail", width=0.14,
                 extend=0.1)


def side_stair(bone):
    """The outside stair down the port side of the quarterdeck (decorative boarding steps), as on the side and
    perspective views."""
    (x, ya, za), (_, yb, zb) = js.SIDE_STAIR
    n = 9
    for k in range(n + 1):
        t = k / n
        y = ya + (yb - ya) * t
        z = za + (zb - za) * t
        xo = js.hull_x(z, y) + 0.05
        add_cube(bone, "side_stair_step_%d" % k, v3(xo + 0.4, y, z), EYE, (0.8, 0.1, 0.36), {"all": "dark_wood", "+2": "plank_light"})
    for j, off in enumerate((0.04, 0.8)):
        pa = v3(js.hull_x(za, ya) + 0.05 + off, ya + 0.05, za)
        pb = v3(js.hull_x(zb, yb) + 0.05 + off, yb - 0.1, zb)
        beam(bone, "side_stair_stringer_%d" % j, pa, pb, 0.14, "dark_wood", width=0.08, extend=0.15)
    pa = v3(js.hull_x(za, ya) + 0.88, ya + 0.95, za - 0.1)
    pb = v3(js.hull_x(zb, yb) + 0.88, yb + 0.95, zb)
    beam(bone, "side_stair_handrail", pa, pb, 0.08, "rail", width=0.08, extend=0.1)
    for t in (0.0, 0.5, 1.0):
        p = pa + (pb - pa) * t
        tube(bone, "side_stair_stanchion_%d" % int(t * 2), p - v3(0, 0.95, 0), p, 0.07, "dark_wood", sides=4)
    # the landing at its foot
    add_cube(bone, "side_stair_landing", v3(js.hull_x(zb, yb) + 0.5, yb - 0.08, zb + 0.4), EYE, (1.0, 0.14, 0.9), {"all": "dark_wood", "+2": "deck"})


# ================================================================ helpers for the houses
def timber(bone, name, a, b, w=0.22, region="post"):
    beam(bone, name, a, b, w, region, width=w)


def wall_panels(bone, detail, lights, name, p0, p1, y0, y1, normal, windows=(), region="plaster_wall", post_every=1.9, brace=True):
    """A white plaster wall in a dark timber frame from p0 to p1 (bottom corners) between heights y0 and y1, its outer
    face along `normal`: a sill, a head beam, posts, diagonal braces, lattice windows (lit) at the given fractions."""
    p0, p1 = v3(*p0), v3(*p1)
    n = norm(v3(*normal))
    L = np.linalg.norm(p1 - p0)
    u = (p1 - p0) / L
    quad(bone, name + "_wall", p0 + v3(0, y0, 0) - n * 0.02, p1 + v3(0, y0, 0) - n * 0.02, p0 + v3(0, y1, 0) - n * 0.02,
         p1 + v3(0, y1, 0) - n * 0.02, 0.12, region, n, back="plank_light", u_dir=u, v_dir=v3(0, -1, 0), stretch=False)
    out = n * 0.06
    timber(bone, name + "_sill", p0 + v3(0, y0 + 0.11, 0) + out, p1 + v3(0, y0 + 0.11, 0) + out, 0.22)
    timber(bone, name + "_head", p0 + v3(0, y1 - 0.12, 0) + out, p1 + v3(0, y1 - 0.12, 0) + out, 0.24)
    timber(bone, name + "_mid", p0 + v3(0, y0 + (y1 - y0) * 0.36, 0) + out * 0.7, p1 + v3(0, y0 + (y1 - y0) * 0.36, 0) + out * 0.7, 0.12)
    m = max(1, int(round(L / post_every)))
    xs = [L * k / m for k in range(m + 1)]
    for k, s in enumerate(xs):
        p = p0 + u * min(max(s, 0.11), L - 0.11)
        timber(bone, "%s_post_%d" % (name, k), p + v3(0, y0, 0) + out, p + v3(0, y1, 0) + out, 0.22)
    for k in range(m):
        a = xs[k]
        b = xs[k + 1]
        mid = (a + b) / 2
        frac = mid / L
        if any(abs(frac - f) < 0.5 / m for f in windows):
            wy0, wy1 = y0 + (y1 - y0) * 0.42, y0 + (y1 - y0) * 0.86
            ww = min(1.1, (b - a) - 0.5)
            c = p0 + u * mid
            quad(lights, "glow_" + name + "_window_%d" % k, c - u * ww / 2 + v3(0, wy0, 0) + n * 0.03, c + u * ww / 2 + v3(0, wy0, 0) + n * 0.03,
                 c - u * ww / 2 + v3(0, wy1, 0) + n * 0.03, c + u * ww / 2 + v3(0, wy1, 0) + n * 0.03, 0.03, "window", n, u_dir=u,
                 v_dir=v3(0, -1, 0))
            for j, (pa, pb) in enumerate(((c - u * (ww / 2 + 0.06) + v3(0, wy0, 0), c + u * (ww / 2 + 0.06) + v3(0, wy0, 0)),
                                           (c - u * (ww / 2 + 0.06) + v3(0, wy1, 0), c + u * (ww / 2 + 0.06) + v3(0, wy1, 0)),
                                           (c - u * (ww / 2 + 0.03) + v3(0, wy0, 0), c - u * (ww / 2 + 0.03) + v3(0, wy1, 0)),
                                           (c + u * (ww / 2 + 0.03) + v3(0, wy0, 0), c + u * (ww / 2 + 0.03) + v3(0, wy1, 0)))):
                timber(detail, "%s_window_frame_%d_%d" % (name, k, j), pa + n * 0.08, pb + n * 0.08, 0.1, "dark_wood")
        elif brace and (b - a) > 1.0 and k % 2 == 0:
            ya_, yb_ = y0 + (y1 - y0) * 0.4, y1 - 0.2
            timber(bone, "%s_brace_%d" % (name, k), p0 + u * (a + 0.15) + v3(0, ya_, 0) + out * 0.8, p0 + u * (b - 0.15) + v3(0, yb_, 0) + out * 0.8,
                   0.12)


# ================================================================ the stern house and its roof
def house(bone, detail, lights, root):
    """The stern house's walls (the stern cabin inside), its front wall with the double door, the porch under the
    overhanging gable."""
    y0, y1 = QD, js.EAVE_Y + 0.35
    zf = js.HOUSE_FRONT_Z
    for side, sn in SIDES:
        zz = [zf, -11.0, -14.0, -17.0, SZ]
        for k in range(len(zz) - 1):
            a, b = zz[k], zz[k + 1]
            pa = v3(side * (js.hull_x(a, QD - 0.1) - 0.02), 0, a)
            pb = v3(side * (js.hull_x(b, QD - 0.1) - 0.02), 0, b)
            if side < 0:
                pa, pb = pb, pa
            wall_panels(bone, detail, lights, "house_side_%s%d" % (sn, k), pa, pb, y0, y1, v3(side, 0, 0),
                        windows=(0.5,) if k in (0, 2) else (), post_every=1.5)
    # the back wall over the transom, three windows
    w = js.hull_x(SZ + 0.01, QD - 0.1)
    wall_panels(bone, detail, lights, "house_back", v3(w, 0, SZ - 0.02), v3(-w, 0, SZ - 0.02), y0, y1, v3(0, 0, -1), windows=(0.2, 0.5, 0.8),
                post_every=1.3)
    # the front wall, the double door in it (the door's leaves are drawn by doors())
    w = js.hull_x(zf, QD - 0.1)
    for k, (a, b) in enumerate(((-w, -1.0), (1.0, w))):
        wall_panels(bone, detail, lights, "house_front_%d" % k, v3(a, 0, zf + 0.02), v3(b, 0, zf + 0.02), y0, y1, v3(0, 0, 1),
                    windows=(0.5,), post_every=1.5, brace=False)
    quad(bone, "house_front_over_door", v3(-1.0, QD + 2.0, zf), v3(1.0, QD + 2.0, zf), v3(-1.0, y1, zf), v3(1.0, y1, zf), 0.12, "plaster_wall",
         v3(0, 0, 1), back="plank_light", u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0), stretch=False)
    # the gable over the front wall: plaster between dark beams, up to the roof's underside
    gable_h = js.roof_y(js.ROOF_HW) - 0.3
    n = 6
    for k in range(n):
        x0, x1 = -w + 2 * w * k / n, -w + 2 * w * (k + 1) / n
        xm = (x0 + x1) / 2
        top = js.roof_y(js.ROOF_HW - abs(xm)) - 0.45
        if top <= y1 + 0.05:
            continue
        quad(bone, "house_gable_%d" % k, v3(x0, y1, zf - 0.05), v3(x1, y1, zf - 0.05), v3(x0, top, zf - 0.05), v3(x1, top, zf - 0.05), 0.1,
             "gable", v3(0, 0, 1), u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0), sub=((x0 + w) / (2 * w), 1 - (top - y1) / (gable_h - y1),
                                                                                 (x1 + w) / (2 * w), 1.0))
    timber(bone, "house_gable_king", v3(0, y1, zf + 0.02), v3(0, gable_h - 0.2, zf + 0.02), 0.26)
    # the emblem on the gable (the round plaque with the coiled dragon)
    disc(detail, "house_gable_emblem", (0, y1 + 1.3, zf + 0.06), (0, 0, 1), 0.55, 0.08, "emblem", sides=16)
    quad(detail, "house_gable_emblem_face", v3(-0.5, y1 + 0.8, zf + 0.11), v3(0.5, y1 + 0.8, zf + 0.11), v3(-0.5, y1 + 1.8, zf + 0.11),
         v3(0.5, y1 + 1.8, zf + 0.11), 0.02, "emblem", v3(0, 0, 1), u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0))
    # carved brackets under the porch's eaves, lanterns beside the door
    for side, sn in SIDES:
        x = side * (w - 0.3)
        timber(bone, "porch_post_" + sn, v3(x, QD, js.ROOF_FRONT_Z + 0.5), v3(x, js.EAVE_Y + 0.6, js.ROOF_FRONT_Z + 0.5), 0.26)
        box(bone, "porch_post_base_" + sn, (x, QD + 0.15, js.ROOF_FRONT_Z + 0.5), (0.42, 0.3, 0.42), "stone")
        timber(bone, "porch_beam_" + sn, v3(x, js.EAVE_Y + 0.45, js.ROOF_FRONT_Z + 0.5), v3(x, js.EAVE_Y + 0.45, zf), 0.24)
        beam(bone, "porch_bracket_" + sn, v3(x, js.EAVE_Y - 0.3, js.ROOF_FRONT_Z + 0.5), v3(x, js.EAVE_Y + 0.35, js.ROOF_FRONT_Z - 0.2), 0.16,
             "bargeboard", width=0.2)
    timber(bone, "porch_lintel", v3(-w + 0.3, js.EAVE_Y + 0.6, js.ROOF_FRONT_Z + 0.5), v3(w - 0.3, js.EAVE_Y + 0.6, js.ROOF_FRONT_Z + 0.5), 0.28)
    gl.hanging_lantern(lights, "porch", (0.0, js.EAVE_Y + 0.45, js.ROOF_FRONT_Z + 0.9), drop=0.35, w=0.36, h=0.5)
    for side, sn in SIDES:
        box(lights, "house_door_lantern_" + sn, (side * 1.55, QD + 2.05, zf + 0.25), (0.3, 0.42, 0.3), {"all": "lantern", "+2": "iron", "-2": "iron"},
            stretch=True)
        beam(bone, "house_door_lantern_arm_" + sn, (side * 1.55, QD + 2.3, zf + 0.03), (side * 1.55, QD + 2.3, zf + 0.3), 0.06, "iron")


def roof_pt(x_sign, d, z, lift=0.0):
    return v3(x_sign * (js.ROOF_HW - d), js.roof_y(d) + lift, z)


TIER_LIFT = 0.3      # each tier stands proud of the one below
LIP = 0.5            # and laps over it by this much (in plan), its lower edge kicked up


def roof(bone, detail, lights):
    """The stern house's roof: four stacked tiers of red tiles with upturned edges on a concave profile, a gable
    over the porch, hipped over the stern; dark beams under each tier's lip with pale knobs, upturned corners, pale
    bamboo battens, the ridge, the bargeboards of the front gable, the staff on the ridge."""
    zf, zb = js.ROOF_FRONT_Z, js.ROOF_BACK_Z
    tiers = js.roof_tiers()
    for k, (d0, d1) in enumerate(tiers):
        lift = TIER_LIFT * k
        dl = max(0.0, d0 - (LIP if k else 0.0))
        kick = 0.28 if k else 0.36
        # side bands (port and starboard): from the gable to the hip line, mitred near the hip with narrow strips
        for side, sn in SIDES:
            # the body of the band: d from d0 to d1, z from the hip at d1 forward to the gable
            p_out0, p_in0 = roof_pt(side, d0, js.roof_front_z(d0), lift), roof_pt(side, d1, js.roof_front_z(d1), lift)
            z_h1 = zb + d1
            p_out1, p_in1 = roof_pt(side, d0, z_h1, lift), roof_pt(side, d1, z_h1, lift)
            quad(bone, "roof_t%d_%s" % (k, sn), p_out1, p_out0, p_in1, p_in0, 0.12, "roof", v3(side, 2.0, 0), back="roof_under",
                 u_dir=v3(0, 0, 1), v_dir=v3(-side, -0.6, 0), stretch=False)
            # mitred strips towards the hip (between the hip at d0 and at d1)
            ns = 3
            for j in range(ns):
                da = d0 + (d1 - d0) * j / ns
                db = d0 + (d1 - d0) * (j + 1) / ns
                quad(bone, "roof_t%d_%s_m%d" % (k, sn, j), roof_pt(side, da, zb + da, lift), roof_pt(side, da, z_h1 + 0.02, lift),
                     roof_pt(side, db, zb + da + 0.02, lift), roof_pt(side, db, z_h1, lift), 0.12, "roof", v3(side, 2.0, 0), back="roof_under",
                     u_dir=v3(0, 0, 1), v_dir=v3(-side, -0.6, 0), stretch=False)
            # the lip: lapping over the tier below, its edge kicked up
            if k == 0:
                ya = js.roof_y(0.0) + kick
                pa0, pa1 = v3(side * (js.ROOF_HW + 0.15), ya, zf - 0.1), v3(side * (js.ROOF_HW + 0.15), ya, zb - 0.15)
            else:
                ya = js.roof_y(dl) + lift + kick
                pa0, pa1 = v3(side * (js.ROOF_HW - dl), ya, js.roof_front_z(dl)), v3(side * (js.ROOF_HW - dl), ya, zb + dl)
            pb0 = roof_pt(side, d0 + 0.02, js.roof_front_z(d0), lift)
            pb1 = roof_pt(side, d0 + 0.02, zb + d0, lift)
            quad(bone, "roof_lip_t%d_%s" % (k, sn), pa1, pa0, pb1, pb0, 0.12, "roof", v3(side, 1.2, 0), back="roof_under", u_dir=v3(0, 0, 1),
                 v_dir=v3(-side, -0.3, 0), stretch=False)
            # the tile ends along the lip, the dark beam under it with its pale knobs
            quad(detail, "roof_ends_t%d_%s" % (k, sn), pa1 - v3(0, 0.12, 0), pa0 - v3(0, 0.12, 0), pa1 + v3(0, 0.02, 0), pa0 + v3(0, 0.02, 0), 0.05,
                 "tile_end", v3(side, 0, 0), u_dir=v3(0, 0, 1), v_dir=v3(0, -1, 0), stretch=False)
            bm = 0.22 + 0.04 * (3 - k)
            beam(bone, "roof_purlin_t%d_%s" % (k, sn), pa0 - v3(side * 0.12, 0.25, 0), pa1 - v3(side * 0.12, 0.25, 0), bm, "dark_wood", width=bm,
                 extend=0.25)
            for j, zz in enumerate((zf - 0.25, )):
                box(detail, "roof_knob_t%d_%s%d" % (k, sn, j), pa0 - v3(side * 0.12, 0.25, 0.15), (0.32, 0.32, 0.32), "bargeboard")
        # the back band (hipped): x across at the stern, from the hip at d0 to the hip at d1
        z_out, z_in = zb + d0, zb + d1
        w_out, w_in = js.ROOF_HW - d0, js.ROOF_HW - d1
        y_out, y_in = js.roof_y(d0) + lift, js.roof_y(d1) + lift
        quad(bone, "roof_t%d_back" % k, v3(-w_in, y_out, z_out), v3(w_in, y_out, z_out), v3(-w_in, y_in, z_in), v3(w_in, y_in, z_in), 0.12, "roof",
             v3(0, 2.0, -1), back="roof_under", u_dir=v3(1, 0, 0), v_dir=v3(0, -0.6, 1), stretch=False)
        ns = 3
        for side, sn in SIDES:
            for j in range(ns):
                da = d0 + (d1 - d0) * j / ns
                db = d0 + (d1 - d0) * (j + 1) / ns
                xa, xb = side * (js.ROOF_HW - da), side * w_in
                quad(bone, "roof_t%d_back_m%s%d" % (k, sn, j), v3(xa, js.roof_y(da) + lift, zb + da), v3(xb, js.roof_y(da) + lift, zb + da),
                     v3(side * (js.ROOF_HW - db) + side * 0.02, js.roof_y(db) + lift, zb + db), v3(xb, js.roof_y(db) + lift, zb + db), 0.12, "roof",
                     v3(0, 2.0, -1), back="roof_under", u_dir=v3(1, 0, 0), v_dir=v3(0, -0.6, 1), stretch=False)
        if k == 0:
            ya = js.roof_y(0.0) + kick
            pa0, pa1 = v3(-(js.ROOF_HW + 0.15), ya, zb - 0.15), v3(js.ROOF_HW + 0.15, ya, zb - 0.15)
        else:
            ya = js.roof_y(dl) + lift + kick
            pa0, pa1 = v3(-(js.ROOF_HW - dl), ya, zb + dl), v3(js.ROOF_HW - dl, ya, zb + dl)
        pb0, pb1 = v3(-(js.ROOF_HW - d0), js.roof_y(d0 + 0.02) + lift, zb + d0), v3(js.ROOF_HW - d0, js.roof_y(d0 + 0.02) + lift, zb + d0)
        quad(bone, "roof_lip_t%d_back" % k, pa0, pa1, pb0, pb1, 0.12, "roof", v3(0, 1.2, -1), back="roof_under", u_dir=v3(1, 0, 0),
             v_dir=v3(0, -0.3, 1), stretch=False)
        quad(detail, "roof_ends_t%d_back" % k, pa0 - v3(0, 0.12, 0), pa1 - v3(0, 0.12, 0), pa0 + v3(0, 0.02, 0), pa1 + v3(0, 0.02, 0), 0.05,
             "tile_end", v3(0, 0, -1), u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0), stretch=False)
        bm = 0.22 + 0.04 * (3 - k)
        beam(bone, "roof_purlin_t%d_back" % k, pa0 - v3(0, 0.25, -0.12), pa1 - v3(0, 0.25, -0.12), bm, "dark_wood", width=bm, extend=0.25)
        # upturned corners: at each hip, the purlins' ends sweep up and out, capped by pale carved knobs
        for side, sn in SIDES:
            c = v3(side * (js.ROOF_HW - dl + (0.15 if k == 0 else 0.0)), ya - 0.25, zb + dl - (0.15 if k == 0 else 0.0))
            tip = c + norm(v3(side, 0, -1)) * 0.75 + v3(0, 0.55, 0)
            beam(bone, "roof_ear_t%d_%s" % (k, sn), c, tip, 0.2, "dark_wood", width=0.2, extend=0.08)
            box(detail, "roof_ear_knob_t%d_%s" % (k, sn), tip + v3(0, 0.12, 0), (0.3, 0.3, 0.3), "bargeboard")
            # the front ends of the purlins sweep up too (the gable's corners)
            c2 = v3(side * (js.ROOF_HW - dl + (0.15 if k == 0 else 0.0)), ya - 0.25, js.roof_front_z(dl))
            tip2 = c2 + norm(v3(side * 0.6, 0, 1)) * 0.6 + v3(0, 0.5, 0)
            beam(bone, "roof_ear_front_t%d_%s" % (k, sn), c2, tip2, 0.2, "dark_wood", width=0.2, extend=0.08)
            box(detail, "roof_ear_front_knob_t%d_%s" % (k, sn), tip2 + v3(0, 0.12, 0), (0.3, 0.3, 0.3), "bargeboard")
    # hips: dark ridge tiles from the stern corners up to the ridge
    for side, sn in SIDES:
        pts = [roof_pt(side, d, zb + d, TIER_LIFT * min(3, int(d / 1.45))) + v3(0, 0.12, 0) for d in np.linspace(0.0, js.ROOF_HW, 6)]
        for j in range(len(pts) - 1):
            beam(bone, "roof_hip_%s%d" % (sn, j), pts[j], pts[j + 1], 0.24, "ridge", width=0.3, extend=0.1)
    # the ridge and its finials
    ry = js.RIDGE_Y + TIER_LIFT * 3 + 0.12
    zr = js.roof_front_z(js.ROOF_HW)
    beam(bone, "roof_ridge", (0, ry, zr - 0.2), (0, ry, zb + js.ROOF_HW), 0.36, "ridge", width=0.42, extend=0.15)
    for k, z in enumerate((zr - 0.35, zb + js.ROOF_HW - 0.1)):
        tube(detail, "roof_finial_%d" % k, (0, ry + 0.1, z), (0, ry + 0.8, z + (0.35 if k == 0 else -0.35)), 0.24, "bargeboard", sides=6)
        box(detail, "roof_finial_knob_%d" % k, (0, ry + 0.9, z + (0.4 if k == 0 else -0.4)), (0.3, 0.3, 0.3), "dark_wood")
    # the bargeboards of the front gable: carved pale boards along the roof's edge, from the eaves to the ridge
    for side, sn in SIDES:
        ds = np.linspace(0.0, js.ROOF_HW, 9)
        pts = [roof_pt(side, d, js.roof_front_z(d) + 0.06, TIER_LIFT * min(3, int(d / 1.45)) + 0.18) for d in ds]
        for j in range(len(pts) - 1):
            beam(bone, "roof_bargeboard_%s%d" % (sn, j), pts[j], pts[j + 1], 0.42, "bargeboard", width=0.18, extend=0.06)
            beam(detail, "roof_bargeboard_low_%s%d" % (sn, j), pts[j] - v3(0, 0.36, -0.04), pts[j + 1] - v3(0, 0.36, -0.04), 0.16, "dark_wood",
                 width=0.14, extend=0.04)
    # bamboo battens on the tiles: running down the slopes, and along the tiers
    for side, sn in SIDES:
        for j, z in enumerate((-6.9, -9.6, -12.3)):
            pts = []
            for d in np.linspace(0.05, js.ROOF_HW - 0.15, 7):
                k = min(3, int(d / 1.45))
                pts.append(roof_pt(side, d, z, TIER_LIFT * k) + v3(0, 0.16, 0))
            for i in range(len(pts) - 1):
                tube(bone, "roof_batten_%s%d_%d" % (sn, j, i), pts[i], pts[i + 1], 0.13, "bamboo", sides=4, extend=0.05)
        for k, (d0, d1) in enumerate(tiers):
            d = d0 + 0.45 * (d1 - d0)
            a, b = roof_pt(side, d, js.roof_front_z(d) + 0.1, TIER_LIFT * k + 0.16), roof_pt(side, d, zb + d + 0.2, TIER_LIFT * k + 0.16)
            tube(bone, "roof_batten_long_%s%d" % (sn, k), a, b, 0.12, "bamboo", sides=4, extend=0.05)
    for j, x in enumerate((-2.2, 0.0, 2.2)):
        pts = [v3(x, js.roof_y(d) + TIER_LIFT * min(3, int(d / 1.45)) + 0.16, zb + d) for d in np.linspace(0.05, js.ROOF_HW - 0.15 - abs(x) * 0.0, 7)
               if js.ROOF_HW - d > abs(x) + 0.2]
        for i in range(len(pts) - 1):
            tube(bone, "roof_batten_back_%d_%d" % (j, i), pts[i], pts[i + 1], 0.13, "bamboo", sides=4, extend=0.05)
    # lanterns hanging at the corners of the eaves
    for side, sn in SIDES:
        for k, z in enumerate((zf + 0.2, zb + 0.4)):
            gl.hanging_lantern(lights, "eave_%s%d" % (sn, k), (side * (js.ROOF_HW - 0.3), js.EAVE_Y - 0.1, z), drop=0.25, w=0.32, h=0.44)


def stern_pole(bone, pennants):
    a, b = v3(*js.STERN_POLE[0]), v3(*js.STERN_POLE[1])
    tube(bone, "stern_pole", a, b, 0.24, "dark_wood", sides=6)
    for k, t in enumerate((0.3, 0.7)):
        p = a + (b - a) * t
        tube(bone, "stern_pole_band_%d" % k, p - norm(b - a) * 0.06, p + norm(b - a) * 0.06, 0.3, "iron", sides=6)
    box(bone, "stern_pole_cap", b + norm(b - a) * 0.1, (0.3, 0.3, 0.3), "gold")
    pen(pennants, "pennant_stern", b - norm(b - a) * 0.3, 0.55, 3.2, (0, -0.25, -1))


def pen(parent, name, root_pt, w, length, fly):
    """A long red pennant streaming from root_pt along `fly` (in its own bone, swung by streamer_wave)."""
    root_pt = v3(*root_pt)
    b = Bone(name, origin=tuple(root_pt), parent=parent)
    f = norm(v3(*fly))
    n = 4
    for k in range(n):
        s0, s1 = k / n, (k + 1) / n
        a = root_pt + f * length * s0 + v3(0, -0.12 * math.sin(math.pi * s0), 0)
        c = root_pt + f * length * s1 + v3(0, -0.12 * math.sin(math.pi * s1), 0)
        wa, wc = w * (1 - 0.7 * s0), w * (1 - 0.7 * s1)
        quad(b, "%s_%d" % (name, k), a, c, a - v3(0, wa, 0), c - v3(0, wc, 0), 0.03, "pennant", np.cross(f, v3(0, 1, 0)) + v3(1e-3, 0, 0),
             u_dir=v3(0, -1, 0), v_dir=f, sub=(0, s0, 1, s1))
    return b


# ================================================================ the companion house at the break
def companion_house(bone, detail, lights):
    """On the port side at the break: walls of red lacquered panels between dark posts, a door facing the bow, a
    gable roof of red tiles (two tiers) running fore and aft with upturned ends, the carved white corner post with
    the round dragon emblem."""
    z0, z1 = js.MID_Z
    xi = js.MID_X[0]
    xo = js.hull_x(1.0, 0.5)
    yt = js.MID_WALL_Y + 0.25
    # inboard wall (x = xi), front wall (z = z1) with the door, aft wall above the quarterdeck
    quad(bone, "mid_wall_in", v3(xi, M0, z1), v3(xi, M0, z0), v3(xi, yt, z1), v3(xi, yt, z0), 0.12, "red_panel", v3(-1, 0, 0), back="plank_light",
         u_dir=v3(0, 0, -1), v_dir=v3(0, -1, 0), stretch=False)
    d0, d1 = ji.DOORS[ji.COMPANION_DOOR][1][0], ji.DOORS[ji.COMPANION_DOOR][1][1]
    for k, (a, b) in enumerate(((xi, d0), (d1, xo))):
        quad(bone, "mid_wall_front_%d" % k, v3(a, M0, z1), v3(b, M0, z1), v3(a, yt, z1), v3(b, yt, z1), 0.12, "red_panel", v3(0, 0, 1),
             back="plank_light", u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0), stretch=False)
    quad(bone, "mid_wall_front_top", v3(d0, M0 + 2.0, z1), v3(d1, M0 + 2.0, z1), v3(d0, yt, z1), v3(d1, yt, z1), 0.12, "red_panel", v3(0, 0, 1),
         back="plank_light", u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0), stretch=False)
    quad(bone, "mid_wall_aft", v3(xo, QD, z0), v3(xi, QD, z0), v3(xo, yt, z0), v3(xi, yt, z0), 0.12, "red_panel", v3(0, 0, -1), back="plank_light",
         u_dir=v3(-1, 0, 0), v_dir=v3(0, -1, 0), stretch=False)
    # outboard wall above the bulwark (x = hull side)
    zz = np.linspace(z0, z1, 6)
    for k in range(len(zz) - 1):
        a, b = zz[k], zz[k + 1]
        ya, yb = js.sheer_y(a), js.sheer_y(b)
        xa, xb = js.hull_x(a, 0.5) - 0.02, js.hull_x(b, 0.5) - 0.02
        quad(bone, "mid_wall_out_%d" % k, v3(xa, min(ya, yb), a), v3(xb, min(ya, yb), b), v3(xa, yt, a), v3(xb, yt, b), 0.12, "red_panel",
             v3(1, 0, 0), back="plank_light", u_dir=v3(0, 0, 1), v_dir=v3(0, -1, 0), stretch=False)
    # posts and beams
    for k, (x, z) in enumerate(((xi, z1), (xi, z0), (xo, z1), (xo, z0), (xi, (z0 + z1) / 2), (d0, z1), (d1, z1))):
        timber(bone, "mid_post_%d" % k, v3(x, M0, z), v3(x, yt, z), 0.24 if k < 4 else 0.18)
    for k, (a, b) in enumerate((((xi, z0), (xi, z1)), ((xi, z1), (xo, z1)), ((xo, z0), (xo, z1)))):
        timber(bone, "mid_head_%d" % k, v3(a[0], yt - 0.1, a[1]), v3(b[0], yt - 0.1, b[1]), 0.22)
    timber(bone, "mid_door_lintel", v3(d0, M0 + 2.08, z1 + 0.05), v3(d1, M0 + 2.08, z1 + 0.05), 0.18)
    # the carved white corner post with the emblem, at the front inboard corner
    box(bone, "mid_corner_post", (xi + 0.05, (M0 + yt) / 2, z1 + 0.05), (0.62, yt - M0, 0.62), "plaster")
    box(bone, "mid_corner_post_cap", (xi + 0.05, yt + 0.1, z1 + 0.05), (0.74, 0.2, 0.74), "dark_wood")
    box(bone, "mid_corner_post_base", (xi + 0.05, M0 + 0.12, z1 + 0.05), (0.74, 0.24, 0.74), "dark_wood")
    for k, (n, c) in enumerate(((v3(0, 0, 1), (xi + 0.05, M0 + 1.5, z1 + 0.37)), (v3(-1, 0, 0), (xi - 0.27, M0 + 1.5, z1 + 0.05)))):
        u = np.cross(v3(0, 1, 0), n)
        c = v3(*c)
        quad(detail, "mid_emblem_%d" % k, c - u * 0.28 - v3(0, 0.28, 0), c + u * 0.28 - v3(0, 0.28, 0), c - u * 0.28 + v3(0, 0.28, 0),
             c + u * 0.28 + v3(0, 0.28, 0), 0.03, "emblem", n, u_dir=u, v_dir=v3(0, -1, 0))
    # the gable roof: ridge along z over the middle of the house, two tiers a side, upturned ends
    xc = (xi + xo) / 2
    hw = (xo - xi) / 2 + 0.55
    rz0, rz1 = js.MID_ROOF_Z
    ridge = js.MID_RIDGE_Y
    eave = js.MID_WALL_Y + 0.1

    def ry_(d):
        t = d / hw
        return eave + (ridge - eave) * (1 - (1 - t) ** 1.5)
    for side, sn in SIDES:
        for k, (da, db) in enumerate(((0.0, hw * 0.48), (hw * 0.4, hw))):
            lift = 0.18 * k
            p = lambda d, z: v3(xc + side * (hw - d), ry_(d) + lift, z)  # noqa: E731
            quad(bone, "mid_roof_%s%d" % (sn, k), p(da, rz0), p(da, rz1), p(db, rz0), p(db, rz1), 0.1, "roof", v3(side, 2.0, 0), back="roof_under",
                 u_dir=v3(0, 0, 1), v_dir=v3(-side, -0.6, 0), stretch=False)
            lip = p(da, rz0) + v3(side * 0.25, 0.22, 0)
            lip1 = p(da, rz1) + v3(side * 0.25, 0.22, 0)
            quad(detail, "mid_roof_ends_%s%d" % (sn, k), lip - v3(0, 0.12, 0), lip1 - v3(0, 0.12, 0), lip, lip1, 0.05, "tile_end", v3(side, 0, 0),
                 u_dir=v3(0, 0, 1), v_dir=v3(0, -1, 0), stretch=False)
            beam(bone, "mid_roof_purlin_%s%d" % (sn, k), lip - v3(side * 0.1, 0.25, 0.25), lip1 - v3(side * 0.1, 0.25, -0.25), 0.2, "dark_wood",
                 width=0.2)
            for j, (zz_, dz) in enumerate(((rz0, -1), (rz1, 1))):
                c = v3(lip[0] - side * 0.1, lip[1] - 0.25, zz_ + dz * 0.25)
                tip = c + norm(v3(side, 0, dz)) * 0.6 + v3(0, 0.45, 0)
                beam(bone, "mid_roof_ear_%s%d_%d" % (sn, k, j), c, tip, 0.18, "dark_wood", width=0.18)
                box(detail, "mid_roof_ear_knob_%s%d_%d" % (sn, k, j), tip + v3(0, 0.1, 0), (0.26, 0.26, 0.26), "bargeboard")
        for j, z in enumerate((rz0 + 1.2, (rz0 + rz1) / 2, rz1 - 1.2)):
            a, b = v3(xc + side * (hw - 0.1), ry_(0.1) + 0.1, z), v3(xc + side * 0.15, ridge + 0.32, z)
            tube(bone, "mid_roof_batten_%s%d" % (sn, j), a, b, 0.11, "bamboo", sides=4)
    beam(bone, "mid_roof_ridge", (xc, ridge + 0.34, rz0 - 0.1), (xc, ridge + 0.34, rz1 + 0.1), 0.3, "ridge", width=0.36)
    # its front gable: plaster between beams, the bargeboards
    for k in range(4):
        xa, xb = xc - hw + 0.5 + (2 * hw - 1.0) * k / 4, xc - hw + 0.5 + (2 * hw - 1.0) * (k + 1) / 4
        top = ry_(hw - abs((xa + xb) / 2 - xc)) - 0.35
        if top < yt + 0.05:
            continue
        quad(bone, "mid_gable_%d" % k, v3(xa, yt, z1 + 0.02), v3(xb, yt, z1 + 0.02), v3(xa, top, z1 + 0.02), v3(xb, top, z1 + 0.02), 0.08, "gable",
             v3(0, 0, 1), u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0))
    for side, sn in SIDES:
        pts = [v3(xc + side * (hw - d), ry_(d) + 0.2, rz1 + 0.05) for d in np.linspace(0, hw, 5)]
        for j in range(len(pts) - 1):
            beam(bone, "mid_bargeboard_%s%d" % (sn, j), pts[j], pts[j + 1], 0.3, "bargeboard", width=0.14, extend=0.05)
    gl.hanging_lantern(lights, "companion", (xc, eave - 0.05, rz1 - 0.2), drop=0.25, w=0.3, h=0.42)


# ================================================================ mast, spars, sail, rigging
def mast(bone, detail):
    """The mast stepped far forward on the main deck and raked aft, iron bands and rope lashings, the masthead
    with its cap, crosstree and the big block the yard hangs from."""
    foot = v3(*js.MAST_FOOT)
    head = v3(*js.mast_head())
    d0, d1 = js.MAST_D
    n = 6
    for k in range(n):
        a, b = foot + (head - foot) * k / n, foot + (head - foot) * (k + 1) / n
        d = d0 + (d1 - d0) * (k + 0.5) / n
        tube(bone, "mast_%d" % k, a, b, d, "dark_wood", sides=8, extend=0.02)
    u = norm(head - foot)
    for k, t in enumerate((0.04, 0.16, 0.34, 0.52, 0.7, 0.86)):
        p = foot + (head - foot) * t
        d = d0 + (d1 - d0) * t + 0.08
        tube(detail if k > 1 else bone, "mast_band_%d" % k, p - u * 0.08, p + u * 0.08, d, "iron" if k % 2 == 0 else "rope", sides=8)
    # its heel goes on down through the storage to the keel
    tube(bone, "lit_mast_heel", v3(*js.mast_point(js.LOWER_DECK_Y - 0.6)), foot + u * 0.02, d0 + 0.04, "dark_wood", sides=8)
    # the partners: a heavy wooden collar on the deck round the foot
    box(bone, "mast_partner", (0, M0 + 0.15, js.MAST_FOOT[2] - 0.05), (1.2, 0.3, 1.2), "dark_wood")
    box(bone, "mast_partner_top", (0, M0 + 0.36, js.MAST_FOOT[2] - 0.12), (0.95, 0.14, 0.95), "post")
    # masthead: cap, a crosstree along the ship, the block and hook of the yard's halyard
    tube(bone, "mast_cap", head, head + u * 0.5, d1 + 0.12, "dark_wood", sides=8)
    box(bone, "mast_truck", head + u * 0.65, (0.4, 0.2, 0.4), "gold")
    ct = head - u * 0.2
    beam(bone, "mast_crosstree", ct + v3(0, 0.05, 0.9), ct + v3(0, 0.05, -0.9), 0.22, "dark_wood", width=0.26, extend=0.05)
    beam(bone, "mast_crosstree_x", ct + v3(0.8, 0.05, 0), ct + v3(-0.8, 0.05, 0), 0.18, "dark_wood", width=0.2, extend=0.05)
    blk = ct + v3(0, -0.6, 0.6)
    box(bone, "mast_block", blk, (0.3, 0.5, 0.36), "dark_wood")
    disc(detail, "mast_block_sheave", blk, (1, 0, 0), 0.16, 0.34, "iron", sides=8)
    ya, yb = v3(*js.YARD[0]), v3(*js.YARD[1])
    hook = yb + (ya - yb) * 0.25 + v3(0, 0.25, 0)
    chain(bone, "yard_chain", blk - v3(0, 0.25, 0), hook + v3(0, 0.2, 0), link=0.2, th=0.05)
    beam(bone, "yard_hook", hook + v3(0, 0.25, 0), hook - v3(0, 0.05, 0), 0.12, "iron", width=0.06)
    return foot, head


def yard_and_booms(bone, detail):
    ya, yb = v3(*js.YARD[0]), v3(*js.YARD[1])
    gn.round_bar(bone, "yard", ya, yb, 0.3, "dark_wood", extend=0.35)
    for k, p in enumerate((ya, yb)):
        box(detail, "yard_end_%d" % k, p + norm(p - (ya + yb) / 2) * 0.42, (0.36, 0.36, 0.36), "iron")
    # the rolled head of the sail along the yard
    beam(bone, "yard_roll", ya + v3(0, -0.2, -0.1), yb + v3(0, -0.2, 0.1), 0.26, "sail_edge", width=0.34)
    # the boom along the foot forward (the tacks are lashed to its end), crossing the mast
    fa, fb = v3(*js.FORE_BOOM[0]), v3(*js.FORE_BOOM[1])
    gn.round_bar(bone, "fore_boom", fa, fb, 0.26, "dark_wood", extend=0.15)
    box(detail, "fore_boom_cap", fb + norm(fb - fa) * 0.2, (0.3, 0.3, 0.3), "iron")
    # the long pale booms holding the clews out and aft along the sides
    for side, sn in SIDES:
        c, end = js.clew_boom(side)
        c, end = v3(*c), v3(*end)
        d = norm(end - c)
        a = c - d * 0.5
        gn.round_bar(bone, "clew_boom_" + sn, a, end, 0.22, "plank_light", extend=0.0)
        gl.arrowhead(detail, "clew_boom_tip_" + sn, end, d, 0.7, 0.24, "iron")
        for k, t in enumerate((0.1, 0.45, 0.8)):
            p = a + (end - a) * t
            tube(detail, "clew_boom_band_%s%d" % (sn, k), p - d * 0.06, p + d * 0.06, 0.28, "rope" if k == 1 else "iron", sides=6)


def sail_panel(root, side, sn, lights):
    """One panel of the great sail: cells on a grid of the flattened panel (1 block), each placed on the billowed,
    slightly twisted panel (its corners through the inverse of the panel's bilinear patch) and mapping its part of the
    sail texture, whose alpha cuts the outline (the arch round the mast, the curved leech) and carries the dragon;
    battens across it; in its own bone (sail_wind)."""
    ya, yb = v3(*js.YARD[0]), v3(*js.YARD[1])
    sb = Bone("sail_" + sn, origin=tuple((ya + yb) / 2), parent=root)
    N = v3(*js.sail_normal(side))
    amin, amax = jt.sail_box()
    step = 1.0
    na = int(math.ceil((amax[0] - amin[0]) / step))
    nb = int(math.ceil((amax[1] - amin[1]) / step))
    cache = {}

    def P3(a, b):
        key = (round(a, 4), round(b, 4))
        if key not in cache:
            s, t = jt.flat_to_st(a, b)
            cache[key] = v3(*js.sail_point(side, s, t))
        return cache[key]
    count = 0
    for i in range(na):
        for j in range(nb):
            a0, a1 = amin[0] + i * step, amin[0] + (i + 1) * step
            b0, b1 = amin[1] + j * step, amin[1] + (j + 1) * step
            samples = [(a0 + (a1 - a0) * fa, b0 + (b1 - b0) * fb) for fa in (0.02, 0.5, 0.98) for fb in (0.02, 0.5, 0.98)]
            if not any(jt.inside_flat(a, b) for a, b in samples):
                continue
            p00, p10, p01, p11 = P3(a0, b0), P3(a1, b0), P3(a0, b1), P3(a1, b1)
            sub = ((a0 - amin[0]) / (amax[0] - amin[0]), (b0 - amin[1]) / (amax[1] - amin[1]),
                   (a1 - amin[0]) / (amax[0] - amin[0]), (b1 - amin[1]) / (amax[1] - amin[1]))
            q = quad(sb, "sail_%s_%d_%d" % (sn, i, j), p00, p10, p01, p11, 0.04, "sail", N, u_dir=p10 + p11 - p00 - p01,
                     v_dir=p01 + p11 - p00 - p10, overlap=(1.04, 1.04), sub=sub)
            count += 1 if q is not None else 0
    # battens: bamboo poles across the panel on its outer face, clipped to the cloth
    for k, s in enumerate(js.SAIL_BATTENS):
        ts = np.linspace(0.0, 1.0, 41)
        inside = jt.sail_inside(np.full(ts.shape, s), ts)
        runs, cur = [], []
        for t, ok in zip(ts, inside):
            if ok:
                cur.append(t)
            elif cur:
                runs.append(cur)
                cur = []
        if cur:
            runs.append(cur)
        for r, run in enumerate(runs):
            if len(run) < 3:
                continue
            pts = [v3(*js.sail_point(side, s, t)) + N * 0.07 for t in np.linspace(run[0], run[-1], 6)]
            for m in range(len(pts) - 1):
                tube(sb, "sail_batten_%s%d_%d_%d" % (sn, k, r, m), pts[m], pts[m + 1], 0.13, "bamboo", sides=4, extend=0.06)
            for e, p in enumerate((pts[0], pts[-1])):
                box(sb, "sail_batten_end_%s%d_%d_%d" % (sn, k, r, e), p, (0.18, 0.18, 0.18), "rope")
    return sb, count


def bow_sail(root, bone, detail):
    """The bowsprit, its yard and the small cream sail hanging from it (bone bow_sail, flapping in the wind)."""
    a, b = v3(*js.BOWSPRIT[0]), v3(*js.BOWSPRIT[1])
    gn.round_bar(bone, "bowsprit", a, b, 0.32, "dark_wood", extend=0.1)
    d = norm(b - a)
    for k, t in enumerate((0.15, 0.55, 0.9)):
        p = a + (b - a) * t
        tube(detail, "bowsprit_band_%d" % k, p - d * 0.07, p + d * 0.07, 0.4, "iron", sides=6)
    box(bone, "bowsprit_cap", b + d * 0.15, (0.36, 0.36, 0.36), "dark_wood")
    ya, yb = v3(*js.BOW_YARD[0]), v3(*js.BOW_YARD[1])
    gn.round_bar(bone, "bow_yard", ya, yb, 0.2, "dark_wood", extend=0.2)
    rope(bone, "bow_yard_lashing", yb, b + v3(0, 0.1, -0.3), d=0.07)
    rope(bone, "bow_yard_heel", ya, a + v3(0, 0.3, 0.4), d=0.07)
    sb = Bone("bow_sail", origin=tuple((ya + yb) / 2), parent=root)
    nx, ny = 4, 3
    drop = js.BOW_SAIL_DROP
    for i in range(nx):
        for j in range(ny):
            t0, t1, s0, s1 = i / nx, (i + 1) / nx, j / ny, (j + 1) / ny

            def P(t, s):
                top = ya + (yb - ya) * (0.08 + 0.84 * t) + v3(0, -0.12, 0)
                bel = 0.35 * math.sin(math.pi * t) * math.sin(math.pi * min(1.0, s * 0.9))
                return top + v3(bel, -drop * s * (1.0 - 0.15 * t), 0.25 * s)
            quad(sb, "bow_sail_%d_%d" % (i, j), P(t0, s0), P(t1, s0), P(t0, s1), P(t1, s1), 0.04, "bow_sail", v3(1, 0, 0),
                 u_dir=P(1, (s0 + s1) / 2) - P(0, (s0 + s1) / 2), v_dir=v3(0, -1, 0), overlap=(1.03, 1.03), sub=(t0, s0, t1, s1))
    return sb


def rigging(bone, slack_root):
    head = v3(*js.mast_head())
    u = norm(head - v3(*js.MAST_FOOT))
    top = head - u * 0.3
    # shrouds to the bulwarks either side, forward of the mast's foot
    for side, sn in SIDES:
        for k, z in enumerate((17.9, 16.2, 14.5)):
            p = hp(z, js.sheer_y(z) + 0.05, side, 0.05)
            rope(bone, "shroud_%s%d" % (sn, k), top + v3(side * 0.2, -0.3 * k, 0), p, d=0.07)
    # forestays to the bowsprit and the bow corners
    rope(bone, "forestay", top + v3(0, 0, 0.2), v3(*js.BOWSPRIT[1]) + v3(0, 0.15, -0.2), d=0.09)
    # the two stays from the masthead to the staff on the stern house's ridge
    a, b = v3(*js.STERN_POLE[0]), v3(*js.STERN_POLE[1])
    for k, off in enumerate((-0.25, 0.25)):
        p = a + (b - a) * 0.62 + v3(off, 0, 0)
        rope(bone, "backstay_%d" % k, top + v3(off * 0.6, 0.1, -0.2), p, d=0.08, sag=0.6, n=6)
    # the lifts from the masthead to the yard's ends
    ya, yb = v3(*js.YARD[0]), v3(*js.YARD[1])
    rope(bone, "lift_fore", top + v3(0, 0, 0.3), ya + v3(0, 0.1, 0.2), d=0.06)
    rope(bone, "lift_aft", top + v3(0, 0, -0.2), yb + v3(0, 0.1, -0.2), d=0.06)
    # the sheets from the clews to the bulwarks, the tack lashings to the fore boom
    fb = v3(*js.FORE_BOOM[1])
    for side, sn in SIDES:
        clew = v3(*js.sail_point(side, 1.0, 1.0))
        tack = v3(*js.sail_point(side, 1.0, 0.0))
        rope(bone, "sheet_" + sn, clew, hp(-1.0, js.sheer_y(-1.0) + 0.1, side, 0.05), d=0.07, sag=0.35, n=5)
        rope(bone, "tack_" + sn, tack, fb, d=0.07)
        rope(bone, "clew_lashing_" + sn, clew, clew + v3(side * 0.1, -0.3, -0.2), d=0.09)
    # a few slack lines hanging from the yard (sway)
    for k, (p0, p1, sag) in enumerate(((ya + v3(0.1, -0.1, 0), v3(0.2, 3.4, 15.0), 0.8), (yb + v3(-0.1, -0.1, 0), v3(-0.2, 2.6, 13.6), 1.0))):
        sb = Bone("rope_slack_%d" % k, origin=tuple(p0), parent=slack_root)
        rope(sb, "rope_slack_line_%d" % k, p0, p1, d=0.06, sag=sag, n=6)


def anchor(bone, detail):
    """The anchor hanging on its chain from a cathead on the port side, as on the side and perspective views."""
    x, z = js.ANCHOR
    side = 1
    cat_in = hp(z, -0.3, side, -0.2)
    cat_out = cat_in + v3(0.75, 0.05, 0)
    beam(bone, "cathead", cat_in, cat_out, 0.28, "dark_wood", width=0.3, extend=0.05)
    box(detail, "cathead_cap", cat_out + v3(0.05, 0, 0), (0.12, 0.34, 0.34), "iron")
    top = v3(cat_out[0] - 0.05, js.ANCHOR_TOP_Y, z)
    chain(bone, "anchor_chain", cat_out - v3(0.05, 0.15, 0), top + v3(0, 0.15, 0), link=0.3, th=0.09, region="iron")
    # a big anchor, as on the reference: ring, stock across, a thick shank, curved arms with broad flukes
    crown = v3(top[0], js.ANCHOR_BOTTOM_Y + 0.2, z)
    disc(bone, "anchor_ring", top, (1, 0, 0), 0.2, 0.07, "iron", sides=8)
    tube(bone, "anchor_shank", top - v3(0, 0.15, 0), crown, 0.2, "iron", sides=6)
    beam(bone, "anchor_stock", top + v3(0, -0.45, -0.8), top + v3(0, -0.45, 0.8), 0.18, "dark_wood", width=0.18, extend=0.05)
    for e in (-0.6, 0.6):
        box(detail, "anchor_stock_band_%d" % (e > 0), top + v3(0, -0.45, e), (0.22, 0.24, 0.1), "iron")
    for s_, sn_ in ((1, "a"), (-1, "b")):
        pts = [crown, crown + v3(0, 0.12, s_ * 0.55), crown + v3(0, 0.55, s_ * 0.95), crown + v3(0, 1.05, s_ * 1.05)]
        for j in range(len(pts) - 1):
            beam(bone, "anchor_arm_%s%d" % (sn_, j), pts[j], pts[j + 1], 0.17, "iron", width=0.17, extend=0.05)
        tip = pts[-1]
        quad(bone, "anchor_fluke_" + sn_, tip + v3(0, -0.15, -s_ * 0.18), tip + v3(0, -0.15, s_ * 0.12), tip + v3(0, 0.3, -s_ * 0.05),
             tip + v3(0, 0.3, s_ * 0.2), 0.08, "iron", v3(1, 0, 0), side="iron")
    box(bone, "anchor_crown", crown, (0.26, 0.26, 0.4), "iron")


def helm(root, bone):
    """The helm on the quarterdeck, in front of the stern house's porch: a turned pedestal, the wheel (helm_wheel)
    facing aft towards the pilot, who looks over it at the sail and the bow."""
    z = js.HELM_Z
    y = QD
    tube(bone, "helm_pedestal", (0, y, z + 0.05), (0, y + 0.95, z + 0.05), 0.34, "dark_wood", sides=8)
    for k, yy in enumerate((y + 0.1, y + 0.55, y + 0.9)):
        tube(bone, "helm_pedestal_ring_%d" % k, (0, yy - 0.05, z + 0.05), (0, yy + 0.05, z + 0.05), 0.42, "brass", sides=8)
    c = v3(0, y + 1.25, z - 0.3)
    tube(bone, "helm_shaft", (0, y + 1.25, z + 0.05), c, 0.1, "iron", sides=6)
    wb = Bone("helm_wheel", origin=tuple(c), parent=root)
    gl.ship_wheel(wb, "helm", c, (0, 0, 1), r=0.6)


def rudder(root):
    """The rudder hanging under the counter: a big blade of dark planks with iron straps, turned by the helm."""
    zs, ze = js.RUDDER_Z
    rb = Bone("rudder", origin=(0.0, 0.0, zs), parent=root)
    bottom = js.keel_y(0.0) + 0.15
    n = 5
    for k in range(n):
        za, zb = zs - (zs - ze) * k / n, zs - (zs - ze) * (k + 1) / n
        ta, tb = js.keel_y(za) + 0.25, js.keel_y(zb) + 0.25
        quad(rb, "rudder_blade_%d" % k, v3(0, bottom, za), v3(0, bottom, zb), v3(0, ta, za), v3(0, tb, zb), 0.22, "hull", v3(1, 0, 0), back="hull",
             side="dark_wood", u_dir=v3(0, 0, -1), v_dir=v3(0, -1, 0), stretch=False)
    tube(rb, "rudder_stock", (0, bottom - 0.05, zs + 0.05), (0, QD + 0.3, zs + 0.05), 0.3, "dark_wood", sides=6)
    for k, y in enumerate(np.linspace(bottom + 0.4, js.keel_y(ze) - 0.2, 3)):
        beam(rb, "rudder_strap_%d" % k, (0, y, zs + 0.1), (0, y, ze + 0.3), 0.08, "iron", width=0.26)
    beam(rb, "rudder_heel", (0, bottom, zs + 0.1), (0, bottom, ze + 0.15), 0.16, "iron", width=0.26)


# ================================================================ lanterns and deck fittings
def lantern_post(bone, lights, name, p, h=1.35):
    """A lantern standing on a stone pedestal and a short post (reference interior views: the main deck)."""
    p = v3(*p)
    box(bone, name + "_pedestal", p + v3(0, 0.3, 0), (0.56, 0.6, 0.56), "stone")
    box(bone, name + "_pedestal_cap", p + v3(0, 0.64, 0), (0.64, 0.08, 0.64), "dark_wood")
    tube(bone, name + "_post", p + v3(0, 0.66, 0), p + v3(0, h - 0.05, 0), 0.24, "post", sides=4)
    box(lights, name, p + v3(0, h + 0.25, 0), (0.36, 0.48, 0.36), {"all": "lantern", "+2": "iron", "-2": "iron"}, stretch=True)


def deck_fittings(bone, lights, detail):
    for name, p in jd.DECK_LANTERNS:
        lantern_post(bone, lights, name, p)
    # bollards (stout posts) along the bulwarks, as on the reference's deck view
    for k, (side, z) in enumerate(jd.BOLLARDS):
        x = side * (js.hull_x(z, 0.2) - 0.75)
        tube(bone, "bollard_%d" % k, (x, M0, z), (x, M0 + 0.75, z), 0.36, "dark_wood", sides=6)
        tube(detail, "bollard_cap_%d" % k, (x, M0 + 0.75, z), (x, M0 + 0.85, z), 0.42, "iron", sides=6)
    # the hatch's coaming over the storage ladder
    x0, x1, _, _, z0, z1 = ji.DOORS[ji.HATCH][1]
    for k, (a, b) in enumerate((((x0 - 0.1, z0 - 0.1), (x1 + 0.1, z0 - 0.1)), ((x0 - 0.1, z1 + 0.1), (x1 + 0.1, z1 + 0.1)))):
        beam(bone, "hatch_coaming_%d" % k, (a[0], M0 + 0.06, a[1]), (b[0], M0 + 0.06, b[1]), 0.12, "dark_wood", width=0.2, extend=0.1)


# ================================================================ the rooms, on the interior grid
ROOM_MATERIALS = {
    "storage": ("in_wall_hold", "in_floor_hold", "in_ceil"),
    "main_room": ("in_wall", "in_floor", "in_ceil"),
    "bedroom": ("in_wall", "in_floor_capt", "in_ceil"),
    "stern_cabin": ("in_wall_plaster", "in_floor_light", "in_ceil_beams"),
    "companion": ("in_wall", "in_floor", "in_ceil"),
}
SHAFT_MAT = ("in_wall", "in_floor", "in_ceil")
OPEN_KINDS = (ji.DRY, ji.LADDER)
ROOM_TILE = 4


def room_at(x, y, z):
    for name, (x0, x1, y0, y1, z0, z1) in ji.ROOMS.items():
        if x0 - 0.01 <= x <= x1 + 0.01 and y0 - 0.01 <= y <= y1 + 0.01 and z0 - 0.01 <= z <= z1 + 0.01:
            return name
    return None


def surfaces(rooms_bone, g):
    """Walls, floors and ceilings of the rooms on the cell boundaries (solid next to a room cell)."""
    global MAX_TILE
    keep = MAX_TILE
    MAX_TILE = ROOM_TILE
    k = g.k
    solid = k == ji.SOLID
    roomish = np.isin(k, OPEN_KINDS) | (k >= ji.DOOR)
    near = roomish.copy()
    for a in range(3):
        for s in (1, -1):
            near |= np.roll(roomish, s, axis=a)
    opened = roomish | ((k == ji.FURNITURE) & near)
    C = ji.CELL
    origin = (ji.X0, ji.Y0, ji.Z0)
    mats = [SHAFT_MAT] + [m for m in dict.fromkeys(ROOM_MATERIALS.values()) if m != SHAFT_MAT]
    mat_index = np.zeros(k.shape, dtype=np.int16)
    for name, box_ in ji.ROOMS.items():
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
                    T = ROOM_TILE
                    if a == 1:
                        sub = ((i0 % T) / T, (j0 % T) / T, (i1 % T + 1) / T, (j1 % T + 1) / T)
                    else:
                        hz0, hz1 = (j0, j1) if a == 0 else (i0, i1)
                        room = room_at(center[0] + s * 0.3 if a == 0 else center[0], center[1], center[2] + s * 0.3 if a == 2 else center[2])
                        ry0, ry1 = (ji.ROOMS[room][2], ji.ROOMS[room][3]) if room else (lo[1], hi[1])
                        hgt = max(0.5, ry1 - ry0)
                        v0 = min(1.0, max(0.0, (ry1 - hi[1]) / hgt))
                        v1 = min(1.0, max(v0 + 0.01, (ry1 - lo[1]) / hgt))
                        sub = ((hz0 % T) / T, v0, (hz1 % T + 1) / T, v1)
                    set_sub(cube, sub)
                    count += 1
    MAX_TILE = keep
    return count


def ladders(bone):
    for name, (x0, x1, y0, y1, z0, z1) in ji.LADDERS.items():
        wall = z0
        pa = lambda y: v3(x0 + 0.15, y, wall + 0.08)  # noqa: E731
        pb = lambda y: v3(x1 - 0.15, y, wall + 0.08)  # noqa: E731
        beam(bone, "lit_ladder_%s_rail_a" % name, pa(y0), pa(y1 + 0.4), 0.08, "rung")
        beam(bone, "lit_ladder_%s_rail_b" % name, pb(y0), pb(y1 + 0.4), 0.08, "rung")
        y, i = y0 + 0.25, 0
        while y < y1 - 0.1:
            beam(bone, "lit_ladder_%s_rung_%d" % (name, i), pa(y), pb(y), 0.07, "rung")
            y += 0.5
            i += 1


def doors(root, g):
    anims = []
    for d, (name, box_) in ji.DOORS.items():
        x0, x1, y0, y1, z0, z1 = box_
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        flat = sy <= min(sx, sz) + 1e-6
        pre = "lit_"
        if flat:
            hinge = v3((x0 + x1) / 2, y1, z0)
            bone = Bone("door_%d" % d, origin=tuple(hinge), parent=root)
            add_cube(bone, "door_%d" % d, v3((x0 + x1) / 2, y1 - 0.08, (z0 + z1) / 2), EYE, (sx - 0.04, 0.14, sz - 0.04),
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
        thin = 0.12
        if max(sx, sz) > 1.6:
            tracks = []
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
            continue
        hinge = v3(x1, y0, (z0 + z1) / 2) if not along_z else v3((x0 + x1) / 2, y0, z1)
        bone = Bone("door_%d" % d, origin=tuple(hinge), parent=root)
        cc = v3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        size = (sx - 0.02, sy, thin) if not along_z else (thin, sy, sz - 0.02)
        big = ("+3", "-3") if not along_z else ("+1", "-1")
        add_cube(bone, "%sdoor_%d" % (pre, d), cc, EYE, size, {"all": "dark_wood", big[0]: "door_leaf", big[1]: "door_leaf"}, stretch=True,
                 u_dir=v3(1, 0, 0) if not along_z else v3(0, 0, 1), v_dir=v3(0, -1, 0))
        anims.append(gg.animation("door_%d" % d, 1.0, "hold", [(bone, [gg.rot_kf(0.0, (0, 0, 0)), gg.rot_kf(1.0, (0, 100, 0))])]))
    return anims


def fallbacks(root):
    """Stand-ins of the decoration blocks, shown only when their mod is missing on a client."""
    for i, b in enumerate(jd.BLOCKS):
        x0, x1, y0, y1, z0, z1 = jd.footprint(b)
        bone = Bone("fallback_%d" % i, parent=root)
        pre = "glow" if b["block"] in jd.GLOWING_FALLBACK else "lit"
        add_cube(bone, "%s_fallback_%d" % (pre, i), v3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), EYE,
                 (max(0.04, x1 - x0), max(0.04, y1 - y0), max(0.04, z1 - z0)), jd.FALLBACK_REGION.get(b["block"], "in_plank"), stretch=True)


FURNITURE_BUILDERS = dict(gl.FURNITURE_BUILDERS)
FURNITURE_BUILDERS["none"] = lambda bone_, **kw: None   # footprints of parts the model draws elsewhere


# ================================================================ build
def build(g):
    root = Bone("dragon_junk")
    hull_b = Bone("hull", parent=root)
    detail = Bone("detail", parent=root)
    deck_b = Bone("decks", parent=root)
    house_b = Bone("house", parent=root)
    roof_b = Bone("roof", parent=root)
    mid_b = Bone("companion_house", parent=root)
    spars = Bone("spars", parent=root)
    rig = Bone("rigging", parent=root)
    slack = Bone("slack_ropes", parent=root)
    pennants = Bone("pennants", parent=root)
    lights = Bone("lanterns", parent=root)
    rooms = Bone("rooms", parent=root)
    fittings = Bone("fittings", parent=root)
    furniture = Bone("furniture", parent=root)
    n = hull(hull_b, detail)
    bow_face(hull_b, detail)
    transom(hull_b, detail, lights)
    hull_dressing(hull_b, detail)
    quarter_gallery(deck_b, detail)
    decks(deck_b, detail, g)
    stairs(deck_b, fittings)
    side_stair(hull_b)
    house(house_b, detail, lights, root)
    roof(roof_b, detail, lights)
    stern_pole(roof_b, pennants)
    companion_house(mid_b, detail, lights)
    mast(spars, detail)
    yard_and_booms(spars, detail)
    sails = []
    cells = 0
    for side, sn in SIDES:
        sb, c = sail_panel(root, side, sn, lights)
        sails.append(sb)
        cells += c
    bs = bow_sail(root, spars, detail)
    rigging(rig, slack)
    head = v3(*js.mast_head())
    pen(pennants, "pennant_mast", head + v3(0, 0.5, 0), 0.6, 4.2, (0, -0.15, -1))
    anchor(hull_b, detail)
    helm(root, fittings)
    rudder(root)
    deck_fittings(deck_b, lights, detail)
    m = surfaces(rooms, g)
    ladders(fittings)
    fallbacks(root)
    for k, (builder, kwargs, solid) in enumerate(jd.CUSTOM):
        kw = dict(kwargs)
        kw.setdefault("name", "%s_%d" % (builder, k))
        FURNITURE_BUILDERS[builder](furniture, **kw)
    print("hull boards:", n, "sail cells:", cells)
    return root, m, sails, bs


def _loop_keys(length, n, fn):
    ts = [length * i / n for i in range(n + 1)]
    return [(t, fn(t if i < n else 0.0)) for i, t in enumerate(ts)]


def build_animations(root, sails, bow):
    """steer (hold, 0..2 = helm from -1 to 1): the wheel, the rudder;
    sail_wind (time = the game time, weight = sail set): the two panels breathe (their belly fills and slackens,
      scaled across about the yard) and swing a little, the bow sail flaps;
    streamer_wave: the pennants of the masthead and the stern staff; lantern_sway: the hanging lanterns;
    rope_sway: the slack lines under the yard."""
    kf, rot_kf, animation, find = gg.kf, gg.rot_kf, gg.animation, gg.find
    anims = [animation("steer", 2.0, "hold", [
        (find(root, "helm_wheel"), [rot_kf(0.0, (0, 0, -150)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 0, 150))]),
        (find(root, "rudder"), [rot_kf(0.0, (0, -24, 0)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 24, 0))])])]
    w = 2 * math.pi / 3.6
    tracks = []
    for k, b in enumerate(sails):
        sgn = 1 if k == 0 else -1
        sh = 0.9 * k
        keys = _loop_keys(3.6, 12, lambda t, sh=sh: (0.9 * math.sin(w * t + sh) + 0.35 * math.sin(2 * w * t + 2 * sh),
                                                     1.0 + 0.07 * math.sin(w * t + sh + 0.8)))
        tracks.append((b, [rot_kf(t, (0, 0, sgn * v[0]), "catmullrom") for t, v in keys] + [kf("scale", t, (v[1], 1, 1), "catmullrom") for t, v in keys]))
    keys = _loop_keys(3.6, 24, lambda t: (5.0 * math.sin(2 * w * t) + 2.5 * math.sin(5 * w * t + 0.7), 2.0 * math.sin(3 * w * t)))
    tracks.append((bow, [rot_kf(t, (v[1], 0, v[0])) for t, v in keys]))
    anims.append(animation("sail_wind", 3.6, "loop", tracks))
    tracks = []
    for k, b in enumerate(c for c in find(root, "pennants").children):
        sh = 0.8 * k
        keys = _loop_keys(3.0, 12, lambda t, sh=sh: (6 * math.sin(2 * math.pi * t / 1.5 + sh), 4 * math.cos(2 * math.pi * t / 3.0 + sh)))
        tracks.append((b, [rot_kf(t, (v[1], v[0], 0)) for t, v in keys]))
    anims.append(animation("streamer_wave", 3.0, "loop", tracks))
    tracks = []
    lan = find(root, "lanterns")
    for k, b in enumerate(c for c in lan.children if c.name.startswith("lantern_")):
        sh = (0.37 * k) % 4.0
        keys = [rot_kf(t, (5 * math.sin(2 * math.pi * (t + sh) / 4.0), 0, 4 * math.cos(2 * math.pi * (t + sh) / 4.0))) for t in (0.0, 1.0, 2.0, 3.0, 4.0)]
        tracks.append((b, keys))
    anims.append(animation("lantern_sway", 4.0, "loop", tracks))
    tracks = []
    for k, b in enumerate(c for c in find(root, "slack_ropes").children):
        ph = 0.61 * k
        tracks.append((b, [rot_kf(t, v, "catmullrom") for t, v in _loop_keys(4.8, 8, lambda t, ph=ph: (3.0 * math.sin(2 * math.pi * (t - ph) / 4.8), 0, 0))]))
    anims.append(animation("rope_sway", 4.8, "loop", tracks))
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


def main():
    if os.environ.get("JUNK_FAST"):   # quick previews: no z-fighting pass
        import zfight
        zfight.fix = lambda root: 0
    g = ji.build()
    jd.build()
    jd.apply_to_grid(g)
    jd.write(os.path.join(ROOT, jd.DECOR_PATH))
    size = g.write(os.path.join(ROOT, ji.GRID_PATH))
    reached, total = ji.walkable_report(g)
    unreachable = [name for name, n in reached.items() if not n]
    print("decor blocks:", len(jd.BLOCKS), "seats:", len(jd.SEATS), "standing places:", total, "unreachable:", unreachable,
          "leaks:", len(ji.leaks(g)))
    root, m, sails, bow = build(g)
    anims = build_animations(root, sails, bow)
    anims += doors(gg.find(root, "rooms"), g)
    bad = check_axes(root)
    if bad:
        print("WARNING: %d cubes with skewed axes, e.g." % len(bad), bad[:8])
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    paths = [os.path.join(tex_dir, "entity/dragon_junk.png"), os.path.join(tex_dir, "entity/dragon_junk_interior.png"),
             os.path.join(tex_dir, "entity/dragon_junk_sail.png")]
    jt.make_texture(paths[0])
    jt.make_interior_texture(paths[1])
    jt.make_sail_texture(paths[2])
    jt.make_item_icon(os.path.join(tex_dir, "item/dragon_junk.png"))
    textures = []
    for k, (p, size_) in enumerate(zip(paths, (jt.SIZE, jt.SIZE_IN, jt.SIZE_SAIL))):
        with open(p, "rb") as f:
            png = f.read()
        t = gn.texture_entry(os.path.basename(p), size_, png, "entity", "dragon_junk.png")
        t["id"] = str(k)
        textures.append(t)
    model = gn.export(root, anims, textures, [
        os.path.join(ROOT, "blockbench/dragon_junk.bbmodel"),
        os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/dragon_junk.bbmodel"),
    ], name="dragon_junk", visible_box=(50, 40, 0))
    print("grid bytes:", size, "grid surfaces:", m, "cubes:", len(model["elements"]), "animations:", [a["name"] for a in model["animations"]])


if __name__ == "__main__":
    main()
