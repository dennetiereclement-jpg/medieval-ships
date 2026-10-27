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
views; measurements in docs/JUNK_PLAN.md). A long dark wooden hull in a rounded V, narrowing forwards to a square bow over
a pale beak, sweeping up aft in a V-shaped counter to a small raked transom (the pale sternpost down its middle, the big
rudder under it); a white band of plaster blocks with dark posts along the bulwarks, red lacquered panels between dark
posts under a carved frieze along the quarterdeck; the stern gallery round the stern house at the quarterdeck's level
(pale balusters along the sides, solid panels of pale boards round the stern, knobbed dark posts, brackets, the pale
post on the sternpost's line); under it the red panels between pale posts and the broad pale wale on dark brackets
across the transom; the stern house of cream boards in a grid of dark beams (pairs of small lattice windows in its sides,
three big arched windows in heavy dark frames in its back wall) under a tall red roof of four stacked tiers, each a
skirt of tiles whose eaves sweep up and out towards every corner, bamboo poles round each tier crossing at the corners
with big knobs, a spine pole down the hipped back, a spire on the ridge's back end, a heavy eave beam on knobbed corner
posts; in front of it the lower gable of the porch (heavy pale bargeboards ending in scrolls, a tympanum of cream boards
between dark timbers, the round medallion); the companion house's lean-to with its white plaster ridge; one mast stepped far forward and raked aft, the
great red sail with the black stencilled dragon: two battened panels hung from a short yard under the masthead and
spread in a V, their clews held out by long pale booms; a small cream sail under the short bowsprit, a rope ladder down
the bow face, lanterns on posts, an outside stair on the hull side, balustrades, the anchor hanging on its chain.

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
TOP_Z = js.transom_z(js.QUARTERDECK_Y - 0.1) + 0.015      # just inside the transom's top (the stern house's back corners)
TOP_HW = js.hull_x(TOP_Z, js.QUARTERDECK_Y - 0.1)


def sm(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def box(bone, name, c, size, region, R=EYE, **kw):
    return add_cube(bone, name, v3(*c), R, size, region, **kw)


def hp(z, y, side, out=0.0):
    """Point on the outside of the hull at (z, y), pushed out by `out` along x."""
    return v3(side * (js.hull_x(z, y) + out), y, z)


# ================================================================ hull
TF_Z, TF_Y = js.TRANSOM_FOOT
TRANSOM = "transom"          # the last station aft: the raked transom (each row at its own z)
STATIONS = [TRANSOM, TF_Z, -18.75, -18.3, -17.8, -17.2, -16.5, -15.8, -15.0, -14.0, -13.0, -11.9, -10.6, -9.4, -8.3, -6.9, -5.5, -4.1, -2.7, -1.5,
            -0.3,
            0.9, 2.2, 3.6, 5.0, 6.4, 7.8, 9.2, 10.6, 11.9, 13.1, 14.2, 15.2, 16.1, 16.9, 17.6, 18.2, 18.7, 19.15, BZ]
BEAK_STATIONS = [BZ, 20.1, 20.7, 21.25, 21.75, 22.2, js.BEAK_TIP_Z - 0.02]
LOW_F = (0.0, 0.1, 0.24, 0.4, 0.58, 0.78, 1.0)
FOREFOOT_Z = 16.0            # forward of this the lower hull is pale planks like the beak (side and perspective views)
WALE_TOP = js.WALE_Y + 0.4


def aft_f(z):
    """0 forward of the break's rise, 1 aft of the break (the red band and the carved frieze above it)."""
    return sm((js.BREAK_RISE[0] - 0.3 - z) / 1.6)


def dark_top(z):
    """Top of the dark planking (the red band's foot aft, the white band's foot forward)."""
    return WALE_TOP + (js.red_bottom(z) - WALE_TOP) * aft_f(z)


def low_top(z):
    """Top of the lower planking: the wale's foot, riding up along the counter aft."""
    k = js.keel_y(z)
    return max(js.WALE_Y, k + 0.6 * (dark_top(z) - k))


def wale_top(z):
    lt = low_top(z)
    return min(dark_top(z), max(WALE_TOP, lt + 0.35 * (dark_top(z) - lt)))


def hull_rows(z):
    """(y, region of the strake above) of a station, from the keel up to the sheer: the dark planks, the wale (riding up the
    counter aft), then forward the white band of plaster blocks up to the bulwark's top; aft the dark planks up to the red
    band's foot (sweeping up towards the transom), the red lacquered panels and the carved frieze under the quarterdeck."""
    k = js.keel_y(z)
    beak = z > BZ + 1e-6
    rows = []
    fore = z > FOREFOOT_Z                         # the forefoot under the bow is planked pale like the beak
    low_reg = "beak" if beak or fore else "hull_low"     # the pale beak juts out of the dark bow
    mid_reg = "beak" if beak or fore else "hull"
    if beak:
        yw = max(js.beak_top(z), k)
        for f in LOW_F:
            rows.append((k + (yw - k) * f, low_reg if f < 0.3 else mid_reg))
        rows[-1] = (rows[-1][0], None)
        return k, rows
    sh = js.sheer_y(z)

    def cl(y, lo):
        return max(lo, min(y, sh))
    yw = cl(low_top(z), k)
    for f in LOW_F:
        rows.append((k + (yw - k) * f, low_reg if f < 0.3 else mid_reg))
    rows[-1] = (rows[-1][0], "wale")
    af = aft_f(z)
    yt = cl(wale_top(z), yw)
    ya = cl(dark_top(z), yt)
    yb = cl(WALE_TOP + (js.RED_BAND[1] - WALE_TOP) * af, ya)
    rows.append((yt, "hull"))
    rows.append((ya, "red_panel"))
    rows.append((yb, "frieze" if af > 0.5 else "plaster"))
    rows.append((sh, None))
    return k, rows


def section_pts(z, side):
    """Points of a station from the middle of the keel up to the sheer; the raked transom's station takes the rows of
    its foot, each at the transom's z at its height."""
    if z == TRANSOM:
        k, rows = hull_rows(TF_Z)
        pts = [v3(0.0, k, TF_Z)]
        regs = [rows[0][1]]
        for y, reg in rows:
            zt = js.transom_z(y)
            pts.append(v3(side * js.hull_x(zt + 0.004, max(y, js.keel_y(zt + 0.004) + 1e-4)), y, zt))
            regs.append(reg)
        return pts, regs
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
                    t = (a1 + b1) - (a0 + b0)
                    outward = norm(v3(side * t[1], -side * t[0], 0) + v3(0, -0.2 if r == 0 else 0.0, 0))
                    zm = (a0[2] + b0[2]) / 2
                    above_deck = (a0[1] + b0[1]) / 2 >= js.deck_y(zm) - 0.05
                    region = reg
                    back = "plank_light" if above_deck else "hull"
                    q = quad(bone, "hull_%s%s%d_%d" % (tag, sn, i, r), a0, b0, a1, b1, 0.12, region, outward, back=back,
                             u_dir=v3(0, 0, 1), v_dir=v3(0, -1, 0), stretch=region in ("red_panel", "frieze"), overlap=(1.03, 1.04))
                    if q is not None:
                        n += 1
    # the keel: a dark timber along the bottom, rising into the beak; aft, the broad pale sternpost along the counter's
    # middle up to the transom's foot
    zz = [z for z in STATIONS if z != TRANSOM] + BEAK_STATIONS[1:]
    for i in range(len(zz) - 1):
        a, b = zz[i], zz[i + 1]
        pale = b <= -13.0
        beam(bone, "keel_%d" % i, (0, js.keel_y(a) - 0.08, a), (0, js.keel_y(b) - 0.08, b), 0.26 if pale else 0.22, "sternpost" if pale else "wale",
             width=0.48 if pale else 0.3, extend=0.06)
    return n


def bow_face(bone, detail):
    """The square bow: a flat face from the wale up to the raised bulwark, white plaster blocks between dark corner posts,
    a heavy dark beam on top, iron straps; the beak's top under it, sloping down to the tip."""
    z = BZ
    top = js.sheer_y(BZ)
    ys = [js.WALE_Y, WALE_TOP, 0.0, 1.0, top]
    for k in range(len(ys) - 1):
        ya, yb = ys[k], ys[k + 1]
        wa, wb = js.hull_x(z - 0.01, ya + 0.01) + 0.02, js.hull_x(z - 0.01, yb - 0.01) + 0.02
        quad(bone, "bow_face_%d" % k, v3(-wa, ya, z), v3(wa, ya, z), v3(-wb, yb, z), v3(wb, yb, z), 0.14, "wale" if k == 0 else "plaster",
             v3(0, 0, 1), back="plank_light", u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0), stretch=False)
    w = js.hull_x(z - 0.01, 0.5)
    for side, sn in SIDES:
        wy = lambda y: js.hull_x(z - 0.01, y)  # noqa: E731
        box(bone, "bow_corner_post_" + sn, (side * (w - 0.18), (js.WALE_Y + top + 0.3) / 2, z - 0.12), (0.42, top + 0.3 - js.WALE_Y, 0.42), "post")
        box(bone, "bow_corner_cap_" + sn, (side * (w - 0.18), top + 0.38, z - 0.12), (0.5, 0.16, 0.5), "dark_wood")
        for k, y in enumerate((-0.9, 0.0, 0.8)):
            box(detail, "bow_strap_%s_%d" % (sn, k), (side * (wy(y) - 0.6), y, z + 0.02), (0.5, 0.08, 0.05), "iron")
    for x in (-0.85, 0.85):
        box(bone, "bow_post_%d" % (x > 0), (x, (js.WALE_Y + top) / 2, z + 0.03), (0.28, top - js.WALE_Y, 0.12), "post")
    beam(bone, "bow_head_beam", (-w - 0.1, top + 0.12, z - 0.15), (w + 0.1, top + 0.12, z - 0.15), 0.26, "dark_wood", width=0.5)
    wl = js.hull_x(z - 0.01, js.WALE_Y + 0.06)
    beam(bone, "bow_wale_beam", (-wl - 0.05, js.WALE_Y + 0.05, z + 0.02), (wl + 0.05, js.WALE_Y + 0.05, z + 0.02), 0.2, "wale", width=0.2)
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
    # the dark post with its bolts where the pale forefoot meets the dark planking
    zf = min(z for z in STATIONS if z != TRANSOM and z > FOREFOOT_Z)
    for side, sn in SIDES:
        ys = np.linspace(js.keel_y(zf) + 0.05, js.WALE_Y, 5)
        pts = [hp(zf, y, side, 0.05) for y in ys]
        for j in range(len(pts) - 1):
            beam(bone, "forefoot_post_%s%d" % (sn, j), pts[j], pts[j + 1], 0.08, "post", width=0.4, extend=0.03, up=v3(side, 0, 0))
        for j, y in enumerate(ys[1:-1]):
            box(detail, "forefoot_bolt_%s%d" % (sn, j), hp(zf, y, side, 0.13), (0.1, 0.1, 0.1), "iron")


def tw(y, out=0.0):
    """Half width of the raked transom at height y (0 under its foot)."""
    zt = js.transom_z(y)
    if y < TF_Y:
        return 0.0
    return js.hull_x(zt + 0.004, max(y, js.keel_y(zt + 0.004) + 1e-4)) + out


TRANSOM_N = norm(v3(0, -(js.STERN_Z - TF_Z), -(js.QUARTERDECK_Y - TF_Y)))   # outward normal of the raked face (aft, down)


def tp(x, y, out=0.0):
    """Point on the raked transom's face at (x, y), pushed out (aft) by out."""
    return v3(x, y, js.transom_z(y)) + TRANSOM_N * out


WALE_AFT = (TF_Y, 1.3)        # the pale wale across the transom's foot (the red strip above it)


def transom(bone, detail, lights):
    """The raked transom (its top aft of its foot): dark planks narrowing in a V down to its foot, a pale wale across,
    the red lacquered strip between dark posts under the stern gallery, the broad pale sternpost with iron bands down its
    middle (the rudder hangs on it under the foot)."""
    ya, yb = TF_Y + 0.02, WALE_AFT[1]
    wa, wb = tw(ya, 0.02), tw(yb, 0.02)
    quad(bone, "transom_foot", tp(wa, ya), tp(-wa, ya), tp(wb, yb), tp(-wb, yb), 0.14, "plank_light", TRANSOM_N, back="hull",
         u_dir=v3(-1, 0, 0), v_dir=v3(0, -1, 0), stretch=False)
    # the red strip: panels between dark posts
    y0, y1 = WALE_AFT[1], js.QUARTERDECK_Y - 0.08
    w = min(tw(y0), tw(y1))
    xs = np.linspace(-w, w, 8)
    for k in range(len(xs) - 1):
        xa, xb = xs[k], xs[k + 1]
        quad(bone, "transom_red_%d" % k, tp(xb, y0), tp(xa, y0), tp(xb, y1), tp(xa, y1), 0.12, "red_panel", TRANSOM_N, back="hull",
             u_dir=v3(-1, 0, 0), v_dir=v3(0, -1, 0))
    for k, x in enumerate(xs):
        xx = max(-w + 0.1, min(w - 0.1, x))
        beam(bone, "transom_post_%d" % k, tp(xx, y0 - 0.05, 0.08), tp(xx, y1 + 0.02, 0.08), 0.2, "plank_light", width=0.18, up=TRANSOM_N)
    # the broad pale wale across the transom's foot (the pale band of the back view), on dark brackets
    wy = (WALE_AFT[0] + WALE_AFT[1]) / 2 - 0.05
    beam(bone, "transom_wale", tp(-tw(1.05) - 0.12, wy, 0.1), tp(tw(1.05) + 0.12, wy, 0.1), 0.24, "plank_light", width=0.62, up=TRANSOM_N)
    beam(bone, "transom_wale_bead", tp(-tw(1.05) - 0.14, wy + 0.3, 0.2), tp(tw(1.05) + 0.14, wy + 0.3, 0.2), 0.08, "dark_wood", width=0.08,
         up=TRANSOM_N)
    for k, x in enumerate((-2.6, -1.1, 1.1, 2.6)):
        box(detail, "transom_bracket_%d" % k, tp(x, wy - 0.42, 0.16), (0.24, 0.34, 0.26), "dark_wood")
        box(detail, "transom_bracket_tip_%d" % k, tp(x, wy - 0.62, 0.12), (0.16, 0.14, 0.18), "dark_wood")
    beam(bone, "transom_red_rail", tp(-w - 0.1, y1, 0.1), tp(w + 0.1, y1, 0.1), 0.14, "dark_wood", width=0.2, up=TRANSOM_N)
    # the sternpost: a broad pale timber from the gallery down the middle of the transom to its foot
    top, foot = tp(0, js.QUARTERDECK_Y - 0.1, 0.13), tp(0, TF_Y, 0.13)
    beam(bone, "sternpost", foot - norm(top - foot) * 0.1, top, 0.26, "sternpost", width=0.5, up=TRANSOM_N)
    for j, y in enumerate((TF_Y + 0.2, 1.75)):
        beam(detail, "sternpost_band_%d" % j, tp(-0.3, y, 0.28), tp(0.3, y, 0.28), 0.12, "iron", width=0.06, up=TRANSOM_N)
    # iron bands round the pale timber along the counter
    for j, z in enumerate((-18.3, -17.2, -15.8, -14.2)):
        y = js.keel_y(z) - 0.08
        c = v3(0, y, z)
        box(detail, "counter_band_%d" % j, c, (0.6, 0.36, 0.12), "iron")


# ================================================================ the stern gallery
def gallery_outline():
    """The gallery's outer edge in plan (x, z), from the starboard forward end round the stern to the port forward end, and
    the matching inner edge on the hull's side and the transom's top."""
    y = js.QUARTERDECK_Y - 0.05
    zc = js.STERN_Z + 0.9                       # where the side turns round the corner
    zb = js.STERN_Z - js.GALLERY_AFT
    zt = TOP_Z
    xt = js.hull_x(zt, y) - 0.02
    outer, inner = [], []
    for z in np.linspace(js.GALLERY_Z0, zc, 9):
        hx = js.hull_x(z, y)
        outer.append((hx + js.GALLERY_OUT, z))
        inner.append((hx - 0.02, z))
    xs = js.hull_x(zc, y) + js.GALLERY_OUT
    rx = 0.9
    for t in (0.35, 0.7, 1.0):                  # the rounded corner
        a = t * math.pi / 2
        outer.append((xs - rx * (1 - math.cos(a)), zc - (zc - zb) * math.sin(a)))
        zi = zc + (zt - zc) * t
        inner.append((js.hull_x(zi, y) - 0.02, zi))
    xe = outer[-1][0]
    for x in np.linspace(xe, 0.0, 4)[1:]:       # across the back to the middle
        outer.append((x, zb))
        inner.append((x * xt / xe, zt))
    outer = outer + [(-x, z) for x, z in outer[:-1]][::-1]
    inner = inner + [(-x, z) for x, z in inner[:-1]][::-1]
    return outer, inner


def stern_gallery(bone, detail):
    """The balcony round the stern house at the quarterdeck's level: its floor projecting from the hull's sides and aft of
    the transom on dark brackets, dark posts, a dark top rail and a pale balustrade of turned balusters."""
    y = js.QUARTERDECK_Y
    outer, inner = gallery_outline()
    ft = y + 0.06
    rail_h = js.GALLERY_RAIL_H
    n = len(outer)
    O = [v3(x, ft, z) for x, z in outer]
    I = [v3(x, ft, z) for x, z in inner]
    D = [norm(o - i) for o, i in zip(O, I)]                 # outwards, in plan
    R = [o - d * 0.08 for o, d in zip(O, D)]                # the balustrade's line
    for k in range(n - 1):
        quad(bone, "gallery_floor_%d" % k, I[k], O[k], I[k + 1], O[k + 1], 0.16, "deck", v3(0, 1, 0), back="roof_under", side="dark_wood",
             u_dir=O[k] - I[k], v_dir=I[k + 1] - I[k], stretch=False)
        beam(bone, "gallery_fascia_%d" % k, O[k] - v3(0, 0.12, 0), O[k + 1] - v3(0, 0.12, 0), 0.26, "dark_wood", width=0.14, extend=0.06)
        a, b = R[k], R[k + 1]
        on = norm(D[k] + D[k + 1])
        aft = max(a[2], b[2]) < js.STERN_Z + 0.35       # round the stern: solid panels of pale boards, as on the back view
        beam(bone, "gallery_rail_top_%d" % k, a + v3(0, rail_h, 0), b + v3(0, rail_h, 0), 0.14, "rail", width=0.22, extend=0.08)
        beam(bone, "gallery_rail_mid_%d" % k, a + v3(0, rail_h - 0.2, 0), b + v3(0, rail_h - 0.2, 0), 0.08, "dark_wood", width=0.12, extend=0.04)
        beam(bone, "gallery_rail_low_%d" % k, a + v3(0, 0.16, 0), b + v3(0, 0.16, 0), 0.12, "dark_wood", width=0.16, extend=0.05)
        quad(bone, "gallery_balusters_%d" % k, a + v3(0, 0.21, 0), b + v3(0, 0.21, 0), a + v3(0, rail_h - 0.26, 0), b + v3(0, rail_h - 0.26, 0),
             0.05 if aft else 0.04, "parapet" if aft else "baluster", on, u_dir=b - a, v_dir=v3(0, -1, 0), stretch=False)
    for k in range(n):
        p = R[k]
        tube(bone, "gallery_post_%d" % k, p - v3(0, 0.05, 0), p + v3(0, rail_h + 0.12, 0), 0.2, "dark_wood", sides=4)
        box(detail, "gallery_post_cap_%d" % k, p + v3(0, rail_h + 0.22, 0), (0.26, 0.2, 0.26), "post")
        if k % 2 == 0:
            # a bracket (knee) under the floor, down to the hull's side or the transom
            foot = I[k] - v3(0, 0.95, 0) + D[k] * 0.04
            beam(bone, "gallery_bracket_%d" % k, foot, O[k] - D[k] * 0.12 - v3(0, 0.12, 0), 0.14, "dark_wood", width=0.14, extend=0.04)
    # the pale post in the middle of the back (the sternpost's line, up from the counter to the rail)
    pc = v3(0, ft, js.STERN_Z - js.GALLERY_AFT - 0.02)
    tube(bone, "gallery_sternpost", pc - v3(0, 0.3, 0), pc + v3(0, rail_h + 0.2, 0), 0.3, "sternpost", sides=4)
    box(detail, "gallery_sternpost_cap", pc + v3(0, rail_h + 0.3, 0), (0.36, 0.2, 0.36), "post")


# ================================================================ hull dressing: wales, posts, rails, the gallery
NUM_STATIONS = [z for z in STATIONS if z != TRANSOM]


def side_line(bone, name, yfn, z0, z1, side, out, th, width, region, n=None):
    zz = [z for z in NUM_STATIONS if z0 <= z <= z1]
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
        # the dark wale under the white band (riding up the counter aft), a thin dark strake on its top all along
        side_line(bone, "wale_" + sn, lambda z: low_top(z) + 0.12, TF_Z + 0.25, BZ - 0.02, side, 0.05, 0.28, 0.2, "wale")
        side_line(bone, "wale2_" + sn, lambda z: wale_top(z) - 0.02, TF_Z + 0.25, BZ - 0.02, side, 0.03, 0.12, 0.14, "dark_wood")
        # aft: the pale rail along the red band's foot sweeping up to the transom's wale, the dark rail on its top
        side_line(bone, "redband_foot_" + sn, lambda z: js.red_bottom(z) - 0.03, js.transom_z(1.1) + 0.06, -11.0, side, 0.06, 0.18, 0.18,
                  "plank_light")
        side_line(bone, "redband_rail_" + sn, lambda z: js.RED_BAND[1], js.transom_z(js.RED_BAND[1]) + 0.05, js.BREAK_RISE[1] + 0.3, side, 0.05, 0.16, 0.18,
                  "dark_wood")
        # the cap rail on the bulwark, along the sheer
        side_line(bone, "cap_rail_" + sn, lambda z: js.sheer_y(z) + 0.06, js.HOUSE_FRONT_Z, BZ - 0.05, side, -0.2, 0.16, 0.56, "rail")
        # dark posts on the hull side: through the white band forward, between the red panels aft
        z = BZ - 1.4
        k = 0
        while z > js.STERN_Z + 0.6:
            aft = aft_f(z) > 0.5
            y0 = js.WALE_Y + 0.1 if not aft else js.red_bottom(z) - 0.05
            y1 = js.sheer_y(z) + 0.1 if not aft else js.RED_BAND[1]
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
                 "baluster", v3(side, 0, 0), u_dir=b - a, v_dir=v3(0, -1, 0), stretch=False)
        b = v3(*pts[-1])
        tube(bone, "qd_rail_post_%s_end" % sn, b, b + v3(0, 1.05, 0), 0.2, "dark_wood", sides=4)
    # across the front edge, between the stair (starboard) and the companion house (port)
    zc = js.BREAK_Z - 0.2
    x0, x1 = ji.QD_FRONT_RAIL
    a, b = v3(x0 + 0.1, y, zc), v3(x1 - 0.05, y, zc)
    for p in (a, b):
        tube(bone, "qd_front_post_%d" % (p[0] > 0), p, p + v3(0, 1.05, 0), 0.2, "dark_wood", sides=4)
    beam(bone, "qd_front_top", a + v3(0, 1.0, 0), b + v3(0, 1.0, 0), 0.12, "rail", width=0.22, extend=0.08)
    quad(bone, "qd_front_lattice", a + v3(0, 0.18, 0), b + v3(0, 0.18, 0), a + v3(0, 0.94, 0), b + v3(0, 0.94, 0), 0.04, "baluster", v3(0, 0, 1),
         u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0), stretch=False)


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
    w = js.hull_x(zb, 0.2) - 0.45
    quad(bone, "waterway_bow", v3(-w, M0 + 0.02, zb - 0.3), v3(w, M0 + 0.02, zb - 0.3), v3(-w, M0 + 0.02, BZ - 0.08),
         v3(w, M0 + 0.02, BZ - 0.08), 0.04, "dark_wood", v3(0, 1, 0), u_dir=v3(1, 0, 0), v_dir=v3(0, 0, 1), stretch=False)
    # the bulwark's cap at the bow
    wc = js.hull_x(BZ - 0.2, 0.5)
    beam(bone, "bow_cap_rail", (-wc, js.sheer_y(BZ - 0.2) + 0.06, BZ - 0.2), (wc, js.sheer_y(BZ - 0.2) + 0.06, BZ - 0.2), 0.16, "rail", width=0.56)
    # the grating amidships (decorative: the deck is solid under it)
    gx, gz0, gz1 = 1.5, 4.5, 7.5
    quad(bone, "grating", v3(-gx, M0 + 0.06, gz0), v3(gx, M0 + 0.06, gz0), v3(-gx, M0 + 0.06, gz1), v3(gx, M0 + 0.06, gz1), 0.05, "grating",
         v3(0, 1, 0), u_dir=v3(1, 0, 0), v_dir=v3(0, 0, 1))
    quad(bone, "grating_shadow", v3(-gx, M0 + 0.012, gz0), v3(gx, M0 + 0.012, gz0), v3(-gx, M0 + 0.012, gz1), v3(gx, M0 + 0.012, gz1), 0.01,
         "void", v3(0, 1, 0), back="void")
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


def wall_panels(bone, detail, lights, name, p0, p1, y0, y1, normal, windows=(), region="plaster_wall", post_every=1.9):
    """A white plaster wall in a grid of dark posts and rails from p0 to p1 (bottom corners) between heights y0 and y1, its
    outer face along `normal`: a sill, a head beam, a rail at mid height, posts, lattice windows (lit) at the given
    fractions."""
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
    for k, s_ in enumerate(xs):
        p = p0 + u * min(max(s_, 0.11), L - 0.11)
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
            quad(lights, "glow_" + name + "_window_%d" % k, c - u * ww / 2 + v3(0, wy0, 0) + n * 0.01, c + u * ww / 2 + v3(0, wy0, 0) + n * 0.01,
                 c - u * ww / 2 + v3(0, wy1, 0) + n * 0.01, c + u * ww / 2 + v3(0, wy1, 0) + n * 0.01, 0.03, "window", n, u_dir=u,
                 v_dir=v3(0, -1, 0))
            for j, (pa, pb) in enumerate(((c - u * (ww / 2 + 0.06) + v3(0, wy0, 0), c + u * (ww / 2 + 0.06) + v3(0, wy0, 0)),
                                           (c - u * (ww / 2 + 0.06) + v3(0, wy1, 0), c + u * (ww / 2 + 0.06) + v3(0, wy1, 0)),
                                           (c - u * (ww / 2 + 0.03) + v3(0, wy0, 0), c - u * (ww / 2 + 0.03) + v3(0, wy1, 0)),
                                           (c + u * (ww / 2 + 0.03) + v3(0, wy0, 0), c + u * (ww / 2 + 0.03) + v3(0, wy1, 0)))):
                timber(detail, "%s_window_frame_%d_%d" % (name, k, j), pa + n * 0.08, pb + n * 0.08, 0.1, "dark_wood")


def roof_under(x, z):
    """Height of the main roof's underside over (x, z): under the lowest tier there (where a wall closes against it)."""
    d = max(0.0, min(js.ROOF_HW - abs(x), z - js.ROOF_BACK_Z))
    ys = [tier_y(k, d) for k in range(js.ROOF_TIERS) if tier_span(k)[0] - 1e-9 <= d <= tier_span(k)[1] + 1e-9]
    return (min(ys) if ys else js.roof_top(d)) - 0.15


def porch_under(x):
    return js.porch_y(js.ROOF_HW - abs(x)) - 0.1


HOUSE_HEAD_Y = 6.6           # the plaster walls end here, the dark carved eave frieze above closes up to the roofs


def eave_frieze(bone, name, pa, pb, ya_top, yb_top, normal):
    """The dark band between the walls' head beam and the roof's underside (a trapezoid along the wall)."""
    n = norm(v3(*normal))
    y0 = HOUSE_HEAD_Y - 0.05
    quad(bone, name, pa + v3(0, y0, 0) - n * 0.03, pb + v3(0, y0, 0) - n * 0.03, pa + v3(0, ya_top, 0) - n * 0.03, pb + v3(0, yb_top, 0) - n * 0.03,
         0.1, "eave_frieze", n, back="roof_under", u_dir=pb - pa, v_dir=v3(0, -1, 0), stretch=False)


# ================================================================ the stern house, its roof and the porch
def house(bone, detail, lights, root):
    """The stern house's walls (the stern cabin inside): white plaster in a grid of dark posts and rails, lit windows,
    the dark eave frieze up to the roof; the back wall over the transom with its three arched windows; the front wall
    with the double door under the porch."""
    y0, y1 = QD, HOUSE_HEAD_Y
    zf = js.HOUSE_FRONT_Z
    for side, sn in SIDES:
        zz = [zf, -11.0, -14.0, -17.0, TOP_Z]
        for k in range(len(zz) - 1):
            a, b = zz[k], zz[k + 1]
            pa = v3(side * (js.hull_x(a, QD - 0.1) - 0.02), 0, a)
            pb = v3(side * (js.hull_x(b, QD - 0.1) - 0.02), 0, b)
            if side < 0:
                pa, pb = pb, pa
            wall_panels(bone, detail, lights, "house_side_%s%d" % (sn, k), pa, pb, y0, y1, v3(side, 0, 0), windows=(), post_every=1.5)
            eave_frieze(bone, "house_side_frieze_%s%d" % (sn, k), pa, pb, roof_under(pa[0], pa[2]), roof_under(pb[0], pb[2]), v3(side, 0, 0))
        # small lattice windows in pairs, high in the side walls (as on the side and perspective views)
        for j, zc in enumerate((-12.5, -15.5, -18.3)):
            for q, dz in enumerate((-0.36, 0.36)):
                z = zc + dz
                x = side * (js.hull_x(z, QD - 0.1) + 0.03)
                n = v3(side, 0, 0)
                c = v3(x, 5.15, z)
                quad(lights, "glow_house_side_window_%s%d_%d" % (sn, j, q), c + v3(0, -0.32, -0.25), c + v3(0, -0.32, 0.25), c + v3(0, 0.32, -0.25),
                     c + v3(0, 0.32, 0.25), 0.02, "window", n, u_dir=v3(0, 0, side), v_dir=v3(0, -1, 0))
                for m, (a, b) in enumerate(((v3(0, -0.38, -0.31), v3(0, -0.38, 0.31)), (v3(0, 0.38, -0.31), v3(0, 0.38, 0.31)),
                                            (v3(0, -0.38, -0.29), v3(0, 0.38, -0.29)), (v3(0, -0.38, 0.29), v3(0, 0.38, 0.29)))):
                    timber(detail, "house_side_window_frame_%s%d_%d_%d" % (sn, j, q, m), c + a + n * 0.07, c + b + n * 0.07, 0.11, "dark_wood")
            beam(detail, "house_side_window_sill_%s%d" % (sn, j), v3(x, 4.74, zc - 0.8) + n * 0.12, v3(x, 4.74, zc + 0.8) + n * 0.12, 0.1, "dark_wood",
                 width=0.18)
    back_wall(bone, detail, lights)
    # the front wall, the double door in it (the door's leaves are drawn by doors()), up to the porch roof
    w = js.hull_x(zf, QD - 0.1)
    for k, (a, b) in enumerate(((-w, -1.0), (1.0, w))):
        wall_panels(bone, detail, lights, "house_front_%d" % k, v3(a, 0, zf + 0.02), v3(b, 0, zf + 0.02), y0, y1, v3(0, 0, 1),
                    windows=(0.5,), post_every=1.5)
    quad(bone, "house_front_over_door", v3(-1.0, QD + 2.0, zf), v3(1.0, QD + 2.0, zf), v3(-1.0, y1, zf), v3(1.0, y1, zf), 0.12, "plaster_wall",
         v3(0, 0, 1), back="plank_light", u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0), stretch=False)
    timber(bone, "house_front_head_mid", v3(-1.0, y1 - 0.12, zf + 0.08), v3(1.0, y1 - 0.12, zf + 0.08), 0.24)
    # its gable under the porch roof: carved dark panels between the posts
    gable_panel(bone, "house_gable", -w, w, y1 - 0.05, zf - 0.02, porch_under, v3(0, 0, 1))
    # the carved door frame and its lintel crest, lanterns either side of the door
    for side, sn in SIDES:
        timber(bone, "door_frame_post_" + sn, v3(side * 1.12, QD, zf + 0.1), v3(side * 1.12, QD + 2.25, zf + 0.1), 0.24, "dark_wood")
        box(lights, "house_door_lantern_" + sn, (side * 1.6, QD + 1.75, zf + 0.3), (0.32, 0.46, 0.32), {"all": "lantern", "+2": "iron", "-2": "iron"},
            stretch=True)
        beam(bone, "house_door_lantern_arm_" + sn, (side * 1.6, QD + 2.06, zf + 0.03), (side * 1.6, QD + 2.06, zf + 0.34), 0.06, "iron")
        box(detail, "house_door_lantern_cap_" + sn, (side * 1.6, QD + 2.03, zf + 0.3), (0.38, 0.06, 0.38), "dark_wood")
    timber(bone, "door_lintel", v3(-1.35, QD + 2.25, zf + 0.12), v3(1.35, QD + 2.25, zf + 0.12), 0.28, "dark_wood")
    quad(detail, "door_crest", v3(-1.0, QD + 2.38, zf + 0.15), v3(1.0, QD + 2.38, zf + 0.15), v3(-1.0, QD + 2.9, zf + 0.15), v3(1.0, QD + 2.9, zf + 0.15),
         0.05, "carved", v3(0, 0, 1), u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0))


def gable_panel(bone, name, x0, x1, y0, z, top_fn, normal, n=6, region="carved", posts=True):
    """A gable's infill from y0 up to top_fn(x), in vertical strips with dark posts between them."""
    nrm = norm(v3(*normal))
    for k in range(n):
        xa, xb = x0 + (x1 - x0) * k / n, x0 + (x1 - x0) * (k + 1) / n
        ta, tb = top_fn(xa), top_fn(xb)
        if max(ta, tb) <= y0 + 0.05:
            continue
        ta, tb = max(ta, y0 + 0.02), max(tb, y0 + 0.02)
        quad(bone, "%s_%d" % (name, k), v3(xa, y0, z), v3(xb, y0, z), v3(xa, ta, z), v3(xb, tb, z), 0.1, region, nrm, back="roof_under",
             u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0), stretch=False)
        if 0 < k and posts:
            timber(bone, "%s_post_%d" % (name, k), v3(xa, y0, z) + nrm * 0.06, v3(xa, ta - 0.02, z) + nrm * 0.06, 0.16, "dark_wood")


ARCH_X = (-2.45, 0.0, 2.45)
ARCH_W, ARCH_H = 1.7, 2.3       # each arched window's opening (its carved frame round it), as wide as on the back view


def arch_window(bone, detail, lights, name, xc, y0, z, n):
    """A big arched lattice window in the back wall: the lit lattice, the carved dark frame, heavy jambs and a round arch
    of dark timber standing out of the wall, a keystone, a sill on two small brackets."""
    hw = ARCH_W / 2
    a1 = y0 + ARCH_H
    u = v3(-1, 0, 0) if n[2] < 0 else v3(1, 0, 0)
    zp = z + n[2] * 0.025
    quad(lights, "glow_%s" % name, v3(xc + hw - 0.06, y0 + 0.04, zp), v3(xc - hw + 0.06, y0 + 0.04, zp), v3(xc + hw - 0.06, a1 - 0.04, zp),
         v3(xc - hw + 0.06, a1 - 0.04, zp), 0.02, "window_arch", n, u_dir=u, v_dir=v3(0, -1, 0))
    r = hw + 0.1
    yc = a1 - hw
    out = n * 0.16
    for sgn in (-1, 1):
        beam(bone, "%s_jamb_%d" % (name, sgn > 0), v3(xc + sgn * r, y0 - 0.02, z) + out, v3(xc + sgn * r, yc + 0.02, z) + out, 0.24, "dark_wood",
             width=0.22, up=n)
    N = 6
    pts = [v3(xc + r * math.cos(math.pi * i / N), yc + r * math.sin(math.pi * i / N), z) + out for i in range(N + 1)]
    for i in range(N):
        beam(bone, "%s_arch_%d" % (name, i), pts[i], pts[i + 1], 0.24, "dark_wood", width=0.22, up=n, extend=0.07)
    box(detail, "%s_keystone" % name, v3(xc, yc + r + 0.05, z) + n * 0.2, (0.3, 0.36, 0.2), "carved")
    beam(bone, "%s_sill" % name, v3(xc - r - 0.2, y0 - 0.1, z) + n * 0.2, v3(xc + r + 0.2, y0 - 0.1, z) + n * 0.2, 0.2, "dark_wood", width=0.16,
         up=v3(0, 1, 0))
    for sgn in (-1, 1):
        box(detail, "%s_sill_bracket_%d" % (name, sgn > 0), v3(xc + sgn * (r - 0.05), y0 - 0.3, z) + n * 0.14, (0.16, 0.26, 0.2), "dark_wood")


def back_wall(bone, detail, lights):
    """The stern house's back wall over the transom: cream boards in a frame of dark posts and rails, three big arched
    lattice windows in heavy carved dark frames (as on the back view: they fill the wall between the gallery's rail and
    the eaves), carved panels at the ends, the dark eave frieze up to the roof."""
    z = SZ - 0.02
    w = TOP_HW - 0.02
    y0, y1 = QD, HOUSE_HEAD_Y
    n = v3(0, 0, -1)
    quad(bone, "house_back_wall", v3(w, y0, z), v3(-w, y0, z), v3(w, y1, z), v3(-w, y1, z), 0.12, "plaster_wall", n, back="plank_light",
         u_dir=v3(-1, 0, 0), v_dir=v3(0, -1, 0), stretch=False)
    eave_frieze(bone, "house_back_frieze", v3(w, 0, z), v3(-w, 0, z), roof_under(w, z), roof_under(-w, z), n)
    out = n * 0.07
    wy0 = QD + js.GALLERY_RAIL_H + 0.25           # the windows' sill, over the gallery's rail
    for k, (y, th) in enumerate(((y0 + 0.11, 0.22), (wy0 - 0.3, 0.14), (y1 - 0.12, 0.3))):
        timber(bone, "house_back_rail_%d" % k, v3(w, y, z) + out, v3(-w, y, z) + out, th)
    for k, x in enumerate((w - 0.11, 1.225, -1.225, -(w - 0.11))):
        timber(bone, "house_back_post_%d" % k, v3(x, y0, z) + out, v3(x, y1, z) + out, 0.24)
    for k, xc in enumerate(ARCH_X):
        arch_window(bone, detail, lights, "house_back_window_%d" % k, xc, wy0, z, n)
    for side, sn in SIDES:
        quad(detail, "house_back_carving_end_" + sn, v3(side * (w - 0.2), wy0 + 0.1, z - 0.05), v3(side * (w - 0.5), wy0 + 0.1, z - 0.05),
             v3(side * (w - 0.2), wy0 + ARCH_H - 0.2, z - 0.05), v3(side * (w - 0.5), wy0 + ARCH_H - 0.2, z - 0.05), 0.04, "carved", n,
             u_dir=v3(-side, 0, 0), v_dir=v3(0, -1, 0))


def porch(bone, detail, lights):
    """The porch in front of the house under its own lower gable roof: two posts on stone bases at the front corners, the
    eave beam across with carved brackets, the gable filled with dark carved panels, the round carved medallion and a
    hanging lantern under its apex."""
    zf = js.HOUSE_FRONT_Z
    zp = js.PORCH_FRONT_Z + 0.3              # the front of the porch's frame (the roof overhangs it)
    w = js.hull_x(zp, QD - 0.1) - 0.3
    ey = js.EAVE_Y
    for side, sn in SIDES:
        x = side * w
        timber(bone, "porch_post_" + sn, v3(x, QD, zp), v3(x, ey + 0.05, zp), 0.28, "dark_wood")
        box(bone, "porch_post_base_" + sn, (x, QD + 0.16, zp), (0.44, 0.32, 0.44), "stone")
        timber(bone, "porch_beam_" + sn, v3(x, ey - 0.15, zp), v3(side * (js.hull_x(zf, QD) - 0.1), ey - 0.15, zf), 0.24)
        beam(bone, "porch_bracket_" + sn, v3(x, ey - 0.9, zp + 0.05), v3(x - side * 0.8, ey - 0.12, zp + 0.05), 0.16, "dark_wood", width=0.18)
        beam(bone, "porch_bracket2_" + sn, v3(x, ey - 0.75, zp + 0.05), v3(x + side * 0.55, ey - 0.12, zp + 0.05), 0.14, "dark_wood", width=0.16)
        gl.hanging_lantern(lights, "porch_" + sn, (x - side * 0.25, ey - 0.25, zp + 0.25), drop=0.2, w=0.32, h=0.44)
    timber(bone, "porch_eave_beam", v3(-w - 0.4, ey - 0.08, zp), v3(w + 0.4, ey - 0.08, zp), 0.3, "dark_wood")
    timber(bone, "porch_eave_beam2", v3(-w - 0.2, ey + 0.18, zp - 0.05), v3(w + 0.2, ey + 0.18, zp - 0.05), 0.18, "post")
    # the gable's tympanum: cream boards in a frame of dark timbers (a king post, a collar, struts), as on the perspective
    gable_panel(bone, "porch_gable", -js.ROOF_HW + 0.6, js.ROOF_HW - 0.6, ey + 0.27, zp - 0.02, porch_under, v3(0, 0, 1), n=8, region="plaster_wall",
                posts=False)
    gz = zp + 0.06
    top = porch_under(0.0)
    yc = ey + 1.05
    timber(bone, "porch_gable_collar", v3(-(js.ROOF_HW - 1.6), yc, gz), v3(js.ROOF_HW - 1.6, yc, gz), 0.2, "dark_wood")
    for side, sn in SIDES:
        x0 = side * (js.ROOF_HW - 0.9)
        timber(bone, "porch_gable_strut_" + sn, v3(x0, ey + 0.3, gz), v3(side * 0.75, top - 0.25, gz), 0.18, "dark_wood")
        timber(bone, "porch_gable_post_" + sn, v3(side * 2.3, ey + 0.3, gz), v3(side * 2.3, porch_under(2.3) - 0.05, gz), 0.18, "dark_wood")
    timber(bone, "porch_gable_king", v3(0, ey + 2.4, gz), v3(0, top - 0.05, gz), 0.2, "dark_wood")
    # the round carved medallion on the gable, a lantern hanging from its apex
    disc(detail, "porch_medallion_rim", (0, ey + 1.75, zp + 0.06), (0, 0, 1), 0.62, 0.1, "dark_wood", sides=16)
    quad(detail, "porch_medallion", v3(-0.56, ey + 1.19, zp + 0.13), v3(0.56, ey + 1.19, zp + 0.13), v3(-0.56, ey + 2.31, zp + 0.13),
         v3(0.56, ey + 2.31, zp + 0.13), 0.02, "medallion", v3(0, 0, 1), u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0))
    gl.hanging_lantern(lights, "porch_apex", (0.0, ey + 0.1, zp + 0.35), drop=0.35, w=0.36, h=0.5)


LIP = 0.45           # each upper tier's lip laps over the tier below by this much (in plan)


def horn(bone, detail, name, base, out, up=0.55, size=0.24):
    """An upturned corner: three stepped dark segments curling up and out from base (along the horizontal out)."""
    out = norm(v3(out[0], 0, out[2]))
    pts = [base, base + out * 0.42 + v3(0, 0.08, 0), base + out * 0.72 + v3(0, 0.3, 0), base + out * 0.82 + v3(0, up + 0.05, 0)]
    for j in range(3):
        sz = size * (1.0 - 0.18 * j)
        beam(bone, "%s_%d" % (name, j), pts[j], pts[j + 1], sz, "dark_wood", width=sz, extend=0.06)
    box(detail, name + "_tip", pts[-1] - out * 0.06 + v3(0, 0.02, 0), (size * 0.62, size * 0.5, size * 0.62), "dark_wood")


# ================================================================ the main roof
# Four stacked tiers, as on the back view: each tier a skirt of red tiles, nearly flat at its lip and steepening under the
# tier above, its lip resting over the top of the tier below (a dark shadow under it); the eaves of every tier sweep up and
# out towards each corner (the upturned eaves); thick bamboo poles laid round each tier, crossing at the corners with
# chunky knobs, poles down the slopes, a central spine pole down the hipped back; the hips curling up at their feet,
# the ridge, a tall spire at its back end; a heavy dark eave beam on short corner posts under the lowest lip.
ROOF_OVER = 0.1          # the lowest lip juts past the eave line (and forwards past the gable)
TIER_GAP = 0.12          # each lip rests this high over the top of the tier below
TIER_SAG = 1.15          # a tier's profile: y = y_lip + (y_top - y_lip) s^TIER_SAG (s: 0 at the lip, 1 at its top)
LIP_KICK = 0.14          # the very edge of each lip turns up
CORNER_L = (4.2, 3.3, 2.7, 2.1)   # the eaves sweep up over this length from each corner (a sag between the corners)
CORNER_UP = (0.9, 0.65, 0.55, 0.45)    # rise of each tier's corners at its lip
CORNER_OUT = (0.3, 0.26, 0.22, 0.18)   # and how far they jut out (plan, along the diagonal)
FRONT_UP = 0.75          # the gable's lower corners rise a little less
T_SIDE = (0.0, 0.035, 0.08, 0.14, 0.22, 0.33, 0.46, 0.6, 0.72, 0.82, 0.9, 0.955, 1.0)   # along a side: gable (0) -> hip (1)
T_BACK = (0.0, 0.05, 0.12, 0.22, 0.35, 0.5, 0.65, 0.78, 0.88, 0.95, 1.0)              # across the back: port hip -> starboard
S_TIER = (0.0, 0.12, 0.3, 0.55, 1.0)                                                   # across a tier: lip (0) -> top (1)


def tier_span(k):
    """(d at its lip, d at its top) of tier k, d the distance from the main roof's eave line."""
    d0, d1 = js.roof_tiers()[k]
    return (-ROOF_OVER if k == 0 else d0 - LIP), d1


def tier_ends(k):
    """Heights of tier k at its lip and at its top (the top tier's top is the ridge)."""
    top = js.roof_y(tier_span(k)[1]) + js.TIER_LIFT * k
    return (js.EAVE_Y if k == 0 else tier_ends(k - 1)[1] + TIER_GAP), top


def tier_y(k, d):
    """Height of tier k's tiles at a distance d from the eave line (without the corners' sweep)."""
    dl, d1 = tier_span(k)
    s = max(0.0, min(1.0, (d - dl) / (d1 - dl)))
    y0, y1 = tier_ends(k)
    return y0 + (y1 - y0) * s ** TIER_SAG + LIP_KICK * (1.0 - s) ** 8


def tile_y(x, z):
    """Top of the main roof's tiles over (x, z) in plan (the highest tier there): where walls and gables close under it."""
    d = min(js.ROOF_HW - abs(x), z - js.ROOF_BACK_Z)
    ys = [tier_y(k, d) for k in range(js.ROOF_TIERS) if tier_span(k)[0] - 1e-9 <= d <= tier_span(k)[1] + 1e-9]
    return max(ys) if ys else js.roof_y(d)


def front_edge_z(d):
    """z of the main roof's front gable at a distance d from the eaves (the lowest lip juts forwards too)."""
    return js.roof_front_z(max(0.0, d)) + max(0.0, -d)


def tier_point(k, band, t, s, lift=0.0):
    """Point of tier k's tiles (raised by lift along the vertical): band +1 / -1 a side, from the gable (t 0) to the hip
    (t 1); band 0 the back, from the port hip (t 0) to the starboard hip (t 1); s from the lip (0) to the tier's top (1).
    The eaves sweep up and out towards each corner, less and less up the tier."""
    dl, d1 = tier_span(k)
    d = dl + (d1 - dl) * s
    w = js.ROOF_HW - d
    zh = js.ROOF_BACK_Z + d
    if band:
        zf = front_edge_z(d)
        z = zf + (zh - zf) * t
        x = band * w
        r_h, r_g = z - zh, zf - z
    else:
        x = w * (1.0 - 2.0 * t)
        z = zh
        r_h, r_g = w - abs(x), 1e9
    y0, y1 = tier_ends(k)
    y = y0 + (y1 - y0) * s ** TIER_SAG + LIP_KICK * (1.0 - s) ** 8
    e = (1.0 - s) ** 1.3
    wh = max(0.0, 1.0 - r_h / CORNER_L[k]) ** 1.7 * e
    wg = max(0.0, 1.0 - r_g / CORNER_L[k]) ** 1.7 * e
    sx = 1.0 if x > 1e-6 else -1.0 if x < -1e-6 else 0.0
    o = CORNER_OUT[k]
    return v3(x + sx * o * (wh + wg), y + CORNER_UP[k] * (wh + FRONT_UP * wg) + lift, z - o * wh + o * wg)


def band_grid(k, band, ss=S_TIER, lift=0.0):
    T = T_BACK if band == 0 else T_SIDE
    return [[tier_point(k, band, t, s, lift) for s in ss] for t in T]


def band_normal(band):
    return v3(band, 1.2, 0) if band else v3(0, 1.2, -1)


def polyline_on(bone, name, pts, d, region, sides=4, ext=(0.0, 0.0), knobs=None):
    """A pole through pts, carried on past its ends by ext, with a knob (size) at each carried end."""
    pts = list(pts)
    a = pts[0] + norm(pts[0] - pts[1]) * ext[0]
    b = pts[-1] + norm(pts[-1] - pts[-2]) * ext[1]
    pts = [a] + pts[1:-1] + [b]
    for i in range(len(pts) - 1):
        tube(bone, "%s_%d" % (name, i), pts[i], pts[i + 1], d, region, sides=sides, extend=d * 0.3)
    if knobs:
        for j, (p, e) in enumerate(((a, ext[0]), (b, ext[1]))):
            if e > 0:
                box(bone, "%s_knob_%d" % (name, j), p, (knobs, knobs, knobs), "post")


def roof(bone, detail, lights):
    """The stern house's main roof (see above): a gable at the front (behind the porch roof) with stepped heavy dark
    bargeboards, hipped over the stern."""
    zb, hw = js.ROOF_BACK_Z, js.ROOF_HW
    for k in range(js.ROOF_TIERS):
        for band, bn in ((1, "p"), (0, "back"), (-1, "s")):
            G = band_grid(k, band)
            n_out = band_normal(band)
            along = v3(0, 0, 1) if band else v3(1, 0, 0)
            down = v3(band, -1.0, 0) if band else v3(0, -1.0, -1.0)
            for i in range(len(G) - 1):
                for j in range(len(S_TIER) - 1):
                    quad(bone, "roof_t%d_%s_%d_%d" % (k, bn, i, j), G[i][j], G[i + 1][j], G[i][j + 1], G[i + 1][j + 1], 0.12, "roof", n_out,
                         back="roof_under", u_dir=along, v_dir=down, stretch=False, overlap=(1.04, 1.06))
            # the lip: a course of round tile ends along its edge, the dark rafter line under it
            for i in range(len(G) - 1):
                a, b = G[i][0], G[i + 1][0]
                quad(detail, "roof_ends_t%d_%s_%d" % (k, bn, i), a - v3(0, 0.16, 0), b - v3(0, 0.16, 0), a + v3(0, 0.03, 0), b + v3(0, 0.03, 0),
                     0.06, "tile_end", v3(band, 0, 0) if band else v3(0, 0, -1), u_dir=along, v_dir=v3(0, -1, 0), stretch=False, overlap=(1.05, 1.0))
            inward = v3(-band, 0, 0) if band else v3(0, 0, 1)
            rl = [G[i][0] + inward * 0.18 - v3(0, 0.24, 0) for i in range(0, len(G), 2)] + ([G[-1][0] + inward * 0.18 - v3(0, 0.24, 0)]
                                                                                         if (len(G) - 1) % 2 else [])
            for i in range(len(rl) - 1):
                beam(bone, "roof_rafter_line_t%d_%s_%d" % (k, bn, i), rl[i], rl[i + 1], 0.16, "dark_wood", width=0.18, extend=0.08)
        # the hips: dark ridge tiles from the tier's lip up to its top, the foot curling up and out at the corner
        for side, sn in SIDES:
            pts = [tier_point(k, side, 1.0, s, 0.13) for s in (0.0, 0.2, 0.45, 0.7, 1.0)]
            for j in range(len(pts) - 1):
                beam(bone, "roof_hip_t%d_%s%d" % (k, sn, j), pts[j], pts[j + 1], 0.24, "ridge", width=0.3, extend=0.08)
            foot, nxt = pts[0], pts[1]
            out = norm(v3(foot[0] - nxt[0], 0, foot[2] - nxt[2]))
            tip = foot + out * 0.45 + v3(0, 0.3, 0)
            beam(detail, "roof_hip_tip_t%d_%s" % (k, sn), foot, tip, 0.2, "ridge", width=0.24, extend=0.04)
            # the gable's corner: the same curl at the foot of the bargeboard
            gf, gn_ = tier_point(k, side, 0.0, 0.0, 0.13), tier_point(k, side, 0.0, 0.2, 0.13)
            out = norm(v3(gf[0] - gn_[0], 0, 0.35))
            beam(detail, "roof_gable_tip_t%d_%s" % (k, sn), gf, gf + out * 0.4 + v3(0, 0.26, 0), 0.2, "ridge", width=0.24, extend=0.04)
    # the ridge, its cap, the curled finial at the gable, the spire at its back end
    ry = js.ridge_top() + 0.12
    zr, zh = front_edge_z(hw), zb + hw
    beam(bone, "roof_ridge", (0, ry, zr - 0.2), (0, ry, zh), 0.4, "ridge", width=0.46, extend=0.15)
    beam(bone, "roof_ridge_cap", (0, ry + 0.22, zr - 0.1), (0, ry + 0.22, zh - 0.1), 0.12, "dark_wood", width=0.3)
    base = v3(0, ry + 0.1, zr - 0.35)
    pts = [base, base + v3(0, 0.45, 0.12), base + v3(0, 0.85, 0.42), base + v3(0, 1.0, 0.75)]
    for j in range(3):
        beam(detail if j else bone, "roof_finial_0_%d" % j, pts[j], pts[j + 1], 0.3 - 0.06 * j, "dark_wood", width=0.3 - 0.06 * j, extend=0.06)
    box(detail, "roof_finial_tip_0", pts[-1] + v3(0, 0.05, 0.08), (0.2, 0.2, 0.2), "gold")
    sp = v3(0, ry + 0.1, zh)
    box(bone, "roof_spire_base", sp + v3(0, 0.15, 0), (0.62, 0.3, 0.62), "dark_wood")
    tube(bone, "roof_spire_post", sp + v3(0, 0.3, 0), sp + v3(0, 1.45, 0), 0.32, "dark_wood", sides=6)
    for j, y in enumerate((0.55, 1.1)):
        tube(detail, "roof_spire_ring_%d" % j, sp + v3(0, y - 0.05, 0), sp + v3(0, y + 0.05, 0), 0.42, "gold", sides=6)
    box(bone, "roof_spire_knob", sp + v3(0, 1.6, 0), (0.4, 0.34, 0.4), "dark_wood")
    tube(bone, "roof_spire_spike", sp + v3(0, 1.75, 0), sp + v3(0, 2.45, 0), 0.16, "dark_wood", sides=4)
    box(detail, "roof_spire_tip", sp + v3(0, 2.5, 0), (0.12, 0.14, 0.12), "gold")
    for side, sn in SIDES:
        c = [sp + v3(side * 0.2, 0.25, 0), sp + v3(side * 0.48, 0.32, 0), sp + v3(side * 0.6, 0.55, 0), sp + v3(side * 0.5, 0.75, 0)]
        for j in range(3):
            beam(detail, "roof_spire_curl_%s%d" % (sn, j), c[j], c[j + 1], 0.13, "dark_wood", width=0.13, extend=0.03)
    # the heavy bargeboards of the front gable: stepped with the tiers, a scroll at the foot
    for side, sn in SIDES:
        for k in range(js.ROOF_TIERS):
            pts = [tier_point(k, side, 0.0, s, 0.22) + v3(0, 0, 0.12) for s in (0.0, 0.25, 0.55, 1.0)]
            for j in range(len(pts) - 1):
                beam(bone, "roof_bargeboard_t%d_%s%d" % (k, sn, j), pts[j], pts[j + 1], 0.36, "bargeboard", width=0.22, extend=0.1)
        scroll(bone, detail, "roof_bargeboard_scroll_" + sn, tier_point(0, side, 0.0, 0.0, 0.1) + v3(side * 0.05, -0.1, 0.12), side)
    # the main gable's face over the porch roof: cream boards between dark timbers from the porch roof up under the tiers
    zf = js.ROOF_FRONT_Z
    gable_panel(bone, "roof_gable", -hw + 0.3, hw - 0.3, js.EAVE_Y, zf + 0.05, lambda x: tile_y(x, zf + 0.06) - 0.18, v3(0, 0, 1), n=10,
                region="plaster_wall")
    for side, sn in SIDES:
        timber(bone, "roof_gable_strut_" + sn, v3(side * 3.2, js.PORCH_RIDGE_Y - 0.6, zf + 0.12), v3(side * 0.4, tile_y(0.4, zf + 0.06) - 0.4, zf + 0.12),
               0.18, "dark_wood")
    timber(bone, "roof_gable_tie", v3(-2.6, js.PORCH_RIDGE_Y + 0.55, zf + 0.12), v3(2.6, js.PORCH_RIDGE_Y + 0.55, zf + 0.12), 0.2, "dark_wood")
    box(detail, "roof_gable_crest", (0, js.PORCH_RIDGE_Y + 1.35, zf + 0.12), (0.7, 0.7, 0.08), "carved")
    # bamboo poles: round each tier (crossing at the corners, knobbed ends), down the slopes, the spine down the back
    for k in range(js.ROOF_TIERS):
        s = 0.16 if k < 3 else 0.2
        knob = 0.36 - 0.04 * k
        for band, bn in ((1, "p"), (0, "back"), (-1, "s")):
            T = T_BACK if band == 0 else T_SIDE
            pts = [tier_point(k, band, t, s, 0.19) for t in T]
            if band == 0 and k == 3:
                continue                             # the top tier's back is a small triangle: its spine is enough
            polyline_on(bone, "roof_pole_t%d_%s" % (k, bn), pts[::2] + ([pts[-1]] if (len(pts) - 1) % 2 else []), 0.24, "bamboo",
                        ext=(0.42, 0.42), knobs=knob)
    for side, sn in SIDES:
        for j, z in enumerate((-10.9, -13.9, -16.9)):
            for k in range(js.ROOF_TIERS):
                dl, d1 = tier_span(k)
                pts = []
                for s in (0.04, 0.3, 0.6, 0.96):
                    d = dl + (d1 - dl) * s
                    zh, zf_ = zb + d, front_edge_z(d)
                    if z < zh + 0.3 or z > zf_ - 0.3:
                        continue
                    pts.append(tier_point(k, side, (z - zf_) / (zh - zf_), s, 0.2))
                for i in range(len(pts) - 1):
                    tube(bone, "roof_batten_%s%d_t%d_%d" % (sn, j, k, i), pts[i], pts[i + 1], 0.22, "bamboo", sides=4, extend=0.07)
    for k in range(js.ROOF_TIERS):
        pts = [tier_point(k, 0, 0.5, s, 0.2) for s in (0.0, 0.3, 0.65, 1.0)]
        polyline_on(bone, "roof_spine_t%d" % k, pts, 0.26, "bamboo", ext=(0.3 if k == 0 else 0.0, 0.0), knobs=0.34 if k == 0 else None)
    # the heavy eave beam under the lowest lip, round the sides and the back, on short corner posts whose knobbed heads
    # stand above the upturned corners (the "ears" of the back view); lanterns hang from the corners
    for band, bn in ((1, "p"), (0, "back"), (-1, "s")):
        T = T_BACK if band == 0 else T_SIDE
        inward = v3(-band, 0, 0) if band else v3(0, 0, 1)
        pts = [tier_point(0, band, t, 0.3) for t in T]
        ys = js.EAVE_Y - 0.05
        line = [v3(p[0], ys, p[2]) + inward * 0.05 for p in (pts[0], pts[len(pts) // 2], pts[-1])]
        if band:
            line = [line[0], line[-1]]
        for i in range(len(line) - 1):
            beam(bone, "roof_eave_beam_%s_%d" % (bn, i), line[i], line[i + 1], 0.34, "dark_wood", width=0.3, extend=0.3)
    for side, sn in SIDES:
        for c, (t, band) in enumerate(((1.0, side), (0.0, side))):
            p = tier_point(0, band, t, 0.0)
            foot = v3(p[0], js.EAVE_Y - 0.2, p[2])
            head = v3(p[0], p[1] + 0.45, p[2])
            tube(bone, "roof_corner_post_%s%d" % (sn, c), foot, head, 0.26, "dark_wood", sides=4)
            box(bone, "roof_corner_knob_%s%d" % (sn, c), head + v3(0, 0.12, 0), (0.4, 0.34, 0.4), "post")
            gl.hanging_lantern(lights, "eave_%s%d" % (sn, c), (p[0] - side * 0.1, js.EAVE_Y - 0.3, p[2] + (0.15 if c == 0 else -0.15)), drop=0.25,
                               w=0.32, h=0.44)


def scroll(bone, detail, name, base, side):
    """A carved scroll at a bargeboard's foot: a short dark curl turning out and up."""
    pts = [base, base + v3(side * 0.3, -0.18, 0.05), base + v3(side * 0.5, 0.0, 0.08), base + v3(side * 0.42, 0.22, 0.08)]
    for j in range(3):
        beam(bone, "%s_%d" % (name, j), pts[j], pts[j + 1], 0.22 - 0.03 * j, "bargeboard", width=0.2, extend=0.05)


def porch_roof(bone, detail, lights):
    """The porch's own roof: a lower gable (about 38 degrees, gently concave) in front of the main roof, red tiles with a
    kicked-up lip at the eaves, heavy dark bargeboards ending in scrolls, a carved crest at the apex, bamboo battens."""
    z0, z1 = js.PORCH_FRONT_Z, js.ROOF_FRONT_Z - 0.45      # its front gable, its back end under the main roof
    hw = js.ROOF_HW
    ds = list(np.linspace(0.0, hw, 7))
    for side, sn in SIDES:
        P = lambda d, z: v3(side * (hw - d), js.porch_y(d), z)  # noqa: E731
        for j in range(len(ds) - 1):
            da, db = ds[j], ds[j + 1]
            quad(bone, "porch_roof_%s%d" % (sn, j), P(da, z1), P(da, z0), P(db, z1), P(db, z0), 0.12, "roof", v3(side, 1.2, 0), back="roof_under",
                 u_dir=v3(0, 0, 1), v_dir=v3(-side, -0.6, 0), stretch=False)
        # the lip at the eaves, kicked up
        zl = js.ROOF_FRONT_Z + 0.05
        la, lb = v3(side * (hw + 0.22), js.EAVE_Y + js.TIER_FLARE * 0.6, z0 - 0.15), v3(side * (hw + 0.22), js.EAVE_Y + js.TIER_FLARE * 0.6, zl)
        quad(bone, "porch_roof_lip_" + sn, lb, la, P(0.02, zl), P(0.02, z0 - 0.15), 0.12, "roof", v3(side, 1.2, 0), back="roof_under",
             u_dir=v3(0, 0, 1), v_dir=v3(-side, -0.3, 0), stretch=False)
        quad(detail, "porch_roof_ends_" + sn, lb - v3(0, 0.12, 0), la - v3(0, 0.12, 0), lb + v3(0, 0.02, 0), la + v3(0, 0.02, 0), 0.05, "tile_end",
             v3(side, 0, 0), u_dir=v3(0, 0, 1), v_dir=v3(0, -1, 0), stretch=False)
        beam(bone, "porch_roof_purlin_" + sn, la - v3(side * 0.14, 0.24, 0), lb - v3(side * 0.14, 0.24, 0), 0.3, "dark_wood", width=0.3, extend=0.2)
        horn(bone, detail, "porch_roof_horn_" + sn, la - v3(side * 0.0, 0.2, 0.0) + v3(0, 0, -0.05), v3(side, 0, 0.7), up=0.55, size=0.26)
        # the heavy bargeboards along the front gable, a scroll at the foot
        pts = [P(d, z0 - 0.14) + v3(0, 0.2, 0) for d in np.linspace(0.0, hw, 8)]
        for j in range(len(pts) - 1):
            beam(bone, "porch_bargeboard_%s%d" % (sn, j), pts[j], pts[j + 1], 0.4, "bargeboard", width=0.24, extend=0.08)
        scroll(bone, detail, "porch_bargeboard_scroll_" + sn, pts[0] + v3(side * 0.1, -0.12, 0), side)
        # battens down the slope
        for j, z in enumerate((z0 - 1.15, z1 + 0.6)):
            q = [P(d, z) + v3(0, 0.16, 0) for d in np.linspace(0.1, hw - 0.15, 6)]
            for i in range(len(q) - 1):
                tube(bone, "porch_batten_%s%d_%d" % (sn, j, i), q[i], q[i + 1], 0.22, "bamboo", sides=4, extend=0.05)
        q = [P(hw * 0.45, z0 - 0.1), P(hw * 0.45, z1 + 0.2)]
        tube(bone, "porch_batten_long_" + sn, q[0] + v3(0, 0.17, 0), q[1] + v3(0, 0.17, 0), 0.22, "bamboo", sides=4, extend=0.05)
    ry = js.PORCH_RIDGE_Y + 0.12
    beam(bone, "porch_ridge", (0, ry, z0 - 0.25), (0, ry, z1), 0.34, "ridge", width=0.4, extend=0.1)
    # the carved crest at the apex
    for j, (a, b, w_) in enumerate((((0, ry + 0.05, z0 - 0.3), (0, ry + 0.7, z0 - 0.45), 0.3), ((0, ry + 0.7, z0 - 0.45), (0, ry + 1.05, z0 - 0.2), 0.22))):
        beam(bone, "porch_crest_%d" % j, a, b, w_, "bargeboard", width=0.18, extend=0.05)
    for side, sn in SIDES:
        beam(detail, "porch_crest_wing_" + sn, (0, ry + 0.35, z0 - 0.38), (side * 0.45, ry + 0.62, z0 - 0.4), 0.14, "bargeboard", width=0.14, extend=0.04)


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
    """On the port side at the break: walls of red lacquered panels between dark posts, a door facing the bow, a lean-to
    roof of red tiles sloping down outboard from its high edge (capped with white plaster) inboard, the carved white
    corner post with the round carved medallion."""
    z0, z1 = js.MID_Z
    xi = js.MID_X[0]
    xo = js.hull_x(1.0, 0.5)
    ry = js.mid_roof_y
    # inboard wall (x = xi) up to the high edge, front wall (z = z1) with the door and aft wall up to the slope
    yi = ry(xi) - 0.1
    quad(bone, "mid_wall_in", v3(xi, M0, z1), v3(xi, M0, z0), v3(xi, yi, z1), v3(xi, yi, z0), 0.12, "red_panel", v3(-1, 0, 0), back="plank_light",
         u_dir=v3(0, 0, -1), v_dir=v3(0, -1, 0), stretch=False)
    d0, d1 = ji.DOORS[ji.COMPANION_DOOR][1][0], ji.DOORS[ji.COMPANION_DOOR][1][1]
    for k, (a, b) in enumerate(((xi, d0), (d1, xo))):
        quad(bone, "mid_wall_front_%d" % k, v3(a, M0, z1), v3(b, M0, z1), v3(a, ry(a) - 0.1, z1), v3(b, ry(b) - 0.1, z1), 0.12, "red_panel", v3(0, 0, 1),
             back="plank_light", u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0), stretch=False)
    quad(bone, "mid_wall_front_top", v3(d0, M0 + 2.0, z1), v3(d1, M0 + 2.0, z1), v3(d0, ry(d0) - 0.1, z1), v3(d1, ry(d1) - 0.1, z1), 0.12, "red_panel",
         v3(0, 0, 1), back="plank_light", u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0), stretch=False)
    quad(bone, "mid_wall_aft", v3(xo, QD, z0), v3(xi, QD, z0), v3(xo, ry(xo) - 0.1, z0), v3(xi, ry(xi) - 0.1, z0), 0.12, "red_panel", v3(0, 0, -1),
         back="plank_light", u_dir=v3(-1, 0, 0), v_dir=v3(0, -1, 0), stretch=False)
    # outboard wall above the bulwark (x = hull side) up to the eave
    zz = np.linspace(z0, z1, 6)
    for k in range(len(zz) - 1):
        a, b = zz[k], zz[k + 1]
        ya, yb = js.sheer_y(a), js.sheer_y(b)
        xa, xb = js.hull_x(a, 0.5) - 0.02, js.hull_x(b, 0.5) - 0.02
        top = ry(xo) - 0.1
        if top > min(ya, yb) + 0.05:
            quad(bone, "mid_wall_out_%d" % k, v3(xa, min(ya, yb), a), v3(xb, min(ya, yb), b), v3(xa, top, a), v3(xb, top, b), 0.12, "red_panel",
                 v3(1, 0, 0), back="plank_light", u_dir=v3(0, 0, 1), v_dir=v3(0, -1, 0), stretch=False)
    # posts and beams
    for k, (x, z) in enumerate(((xi, z1), (xi, z0), (xo, z1), (xo, z0), (xi, (z0 + z1) / 2), (d0, z1), (d1, z1))):
        timber(bone, "mid_post_%d" % k, v3(x, M0, z), v3(x, ry(x) - 0.12, z), 0.24 if k < 4 else 0.18)
    timber(bone, "mid_head_in", v3(xi, yi - 0.1, z0), v3(xi, yi - 0.1, z1), 0.22)
    timber(bone, "mid_door_lintel", v3(d0, M0 + 2.08, z1 + 0.05), v3(d1, M0 + 2.08, z1 + 0.05), 0.18)
    # the carved white corner post with the medallion, at the front inboard corner
    yt = js.MID_WALL_Y + 0.25
    box(bone, "mid_corner_post", (xi + 0.05, (M0 + yt) / 2, z1 + 0.05), (0.62, yt - M0, 0.62), "plaster")
    box(bone, "mid_corner_post_cap", (xi + 0.05, yt + 0.1, z1 + 0.05), (0.74, 0.2, 0.74), "dark_wood")
    box(bone, "mid_corner_post_base", (xi + 0.05, M0 + 0.12, z1 + 0.05), (0.74, 0.24, 0.74), "dark_wood")
    for k, (n, c) in enumerate(((v3(0, 0, 1), (xi + 0.05, M0 + 1.6, z1 + 0.37)), (v3(-1, 0, 0), (xi - 0.27, M0 + 1.6, z1 + 0.05)))):
        u = np.cross(v3(0, 1, 0), n)
        c = v3(*c)
        quad(detail, "mid_emblem_%d" % k, c - u * 0.29 - v3(0, 0.29, 0), c + u * 0.29 - v3(0, 0.29, 0), c - u * 0.29 + v3(0, 0.29, 0),
             c + u * 0.29 + v3(0, 0.29, 0), 0.03, "medallion", n, u_dir=u, v_dir=v3(0, -1, 0))
    # the lean-to roof: rows of tiles running down the slope outboard, a kicked-up lip at the eave, the high edge capped
    # with a white plaster ridge, battens
    rz0, rz1 = js.MID_ROOF_Z
    xa, xb = xi - 0.35, xo + 0.55
    xs = np.linspace(xa, xb, 5)
    for k in range(len(xs) - 1):
        pa, pb = v3(xs[k], ry(xs[k]), rz0), v3(xs[k + 1], ry(xs[k + 1]), rz0)
        quad(bone, "mid_roof_%d" % k, pa, pb, pa + v3(0, 0, rz1 - rz0), pb + v3(0, 0, rz1 - rz0), 0.1, "roof", v3(1, 2.0, 0), back="roof_under",
             u_dir=v3(0, 0, 1), v_dir=v3(1, -0.5, 0), stretch=False)
    la, lb = v3(xb + 0.2, ry(xb) + 0.12, rz0 - 0.1), v3(xb + 0.2, ry(xb) + 0.12, rz1 + 0.1)
    quad(bone, "mid_roof_lip", la, lb, v3(xb - 0.02, ry(xb - 0.02), rz0 - 0.1), v3(xb - 0.02, ry(xb - 0.02), rz1 + 0.1), 0.1, "roof", v3(1, 1.2, 0),
         back="roof_under", u_dir=v3(0, 0, 1), v_dir=v3(1, -0.3, 0), stretch=False)
    quad(detail, "mid_roof_ends", la - v3(0, 0.12, 0), lb - v3(0, 0.12, 0), la + v3(0, 0.02, 0), lb + v3(0, 0.02, 0), 0.05, "tile_end", v3(1, 0, 0),
         u_dir=v3(0, 0, 1), v_dir=v3(0, -1, 0), stretch=False)
    beam(bone, "mid_roof_purlin", la - v3(0.12, 0.22, 0), lb - v3(0.12, 0.22, 0), 0.22, "dark_wood", width=0.22, extend=0.15)
    for j, (zz_, dz) in enumerate(((rz0, -1), (rz1, 1))):
        horn(bone, detail, "mid_roof_horn_%d" % j, v3(xb + 0.1, ry(xb) - 0.1, zz_ + dz * 0.12), v3(1, 0, dz * 0.8), up=0.4, size=0.2)
    beam(bone, "mid_roof_ridge", (xa - 0.02, ry(xa) + 0.12, rz0 - 0.1), (xa - 0.02, ry(xa) + 0.12, rz1 + 0.1), 0.36, "plaster", width=0.5)
    beam(bone, "mid_roof_ridge_cap", (xa - 0.02, ry(xa) + 0.33, rz0 - 0.05), (xa - 0.02, ry(xa) + 0.33, rz1 + 0.05), 0.1, "dark_wood", width=0.3)
    for j, z in enumerate((rz0 + 1.1, (rz0 + rz1) / 2, rz1 - 1.1)):
        tube(bone, "mid_roof_batten_%d" % j, v3(xa + 0.3, ry(xa + 0.3) + 0.14, z), v3(xb - 0.1, ry(xb - 0.1) + 0.14, z), 0.2, "bamboo", sides=4)
    tube(bone, "mid_roof_batten_long", v3((xa + xb) / 2, ry((xa + xb) / 2) + 0.15, rz0 + 0.1), v3((xa + xb) / 2, ry((xa + xb) / 2) + 0.15, rz1 - 0.1),
         0.2, "bamboo", sides=4)
    gl.hanging_lantern(lights, "companion", ((xi + d0) / 2 + 0.2, ry((xi + d0) / 2) - 0.25, rz1 - 0.25), drop=0.2, w=0.3, h=0.42)


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
    # battens: thin dark poles across the panel on its outer face (the reference shows them as dark lines, the dragon
    # stays clear), clipped to the cloth
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
                tube(sb, "sail_batten_%s%d_%d_%d" % (sn, k, r, m), pts[m], pts[m + 1], 0.1, "dark_wood", sides=4, extend=0.06)
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


def chunky_chain(bone, name, p0, p1, link=0.34, w=0.2, th=0.075, region="iron"):
    """A heavy chain of open links, each a ring of four bars, every other one turned a quarter round."""
    p0, p1 = v3(*p0), v3(*p1)
    d = p1 - p0
    L = np.linalg.norm(d)
    u = d / L
    e1 = norm(np.cross(u, v3(0, 1, 0) if abs(u[1]) < 0.9 else v3(1, 0, 0)))
    e2 = np.cross(u, e1)
    n = max(1, int(round(L / (link * 0.78))))
    step = L / n
    for k in range(n):
        c = p0 + u * (step * (k + 0.5))
        e = e1 if k % 2 == 0 else e2
        h = link / 2
        for j, (a, b) in enumerate(((c - u * h + e * w / 2, c + u * h + e * w / 2), (c - u * h - e * w / 2, c + u * h - e * w / 2),
                                    (c - u * h - e * w / 2, c - u * h + e * w / 2), (c + u * h - e * w / 2, c + u * h + e * w / 2))):
            beam(bone, "%s_%d_%d" % (name, k, j), a, b, th, region, width=th, up=np.cross(u, e), extend=th / 2)


def anchor(bone, detail):
    """The anchor hanging well clear under the keel on a heavy chain from a cathead jutting out of the port side, as on
    the side and perspective views."""
    x, z = js.ANCHOR
    side = 1
    cat_in = hp(z, -0.3, side, -0.2)
    cat_out = cat_in + v3(js.CATHEAD_OUT, 0.08, 0)
    beam(bone, "cathead", cat_in, cat_out, 0.3, "dark_wood", width=0.32, extend=0.05)
    beam(bone, "cathead_knee", hp(z, -1.25, side, 0.0), cat_out - v3(0.35, 0.12, 0), 0.18, "dark_wood", width=0.2, extend=0.05)
    box(detail, "cathead_cap", cat_out + v3(0.05, 0, 0), (0.12, 0.36, 0.36), "iron")
    top = v3(cat_out[0] - 0.08, js.ANCHOR_TOP_Y, z)
    chunky_chain(bone, "anchor_chain", cat_out - v3(0.08, 0.2, 0), top + v3(0, 0.18, 0))
    # a big anchor, as on the reference: ring, stock across, a thick shank, curved arms with broad flukes
    crown = v3(top[0], js.ANCHOR_BOTTOM_Y + 0.2, z)
    ring(bone, "anchor_ring", top, (1, 0, 0), 0.2, 0.08, "iron", n=6)
    tube(bone, "anchor_shank", top - v3(0, 0.15, 0), crown, 0.22, "iron", sides=6)
    beam(bone, "anchor_stock", top + v3(0, -0.5, -0.85), top + v3(0, -0.5, 0.85), 0.2, "dark_wood", width=0.2, extend=0.05)
    for e in (-0.65, 0.65):
        box(detail, "anchor_stock_band_%d" % (e > 0), top + v3(0, -0.5, e), (0.24, 0.26, 0.1), "iron")
    for s_, sn_ in ((1, "a"), (-1, "b")):
        pts = [crown, crown + v3(0, 0.12, s_ * 0.55), crown + v3(0, 0.55, s_ * 0.95), crown + v3(0, 1.05, s_ * 1.05)]
        for j in range(len(pts) - 1):
            beam(bone, "anchor_arm_%s%d" % (sn_, j), pts[j], pts[j + 1], 0.18, "iron", width=0.18, extend=0.05)
        tip = pts[-1]
        quad(bone, "anchor_fluke_" + sn_, tip + v3(0, -0.15, -s_ * 0.18), tip + v3(0, -0.15, s_ * 0.12), tip + v3(0, 0.3, -s_ * 0.05),
             tip + v3(0, 0.3, s_ * 0.2), 0.08, "iron", v3(1, 0, 0), side="iron")
    box(bone, "anchor_crown", crown, (0.28, 0.28, 0.42), "iron")


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
    """The big rudder hung under the counter: a deep blade of dark planks with iron straps reaching down to the keel's
    depth, its top edge up inside the counter, a pale trailing edge (in line with the pale sternpost from behind), turned
    by the helm about its stock."""
    zs, y_bot, wd = js.RUDDER
    rb = Bone("rudder", origin=(0.0, 0.0, zs), parent=root)
    th = 0.32
    ze = zs - wd

    def top(z):
        return js.keel_y(z) + 0.25
    zz = list(np.linspace(zs, ze, 6))
    for k in range(len(zz) - 1):
        za, zb = zz[k], zz[k + 1]
        quad(rb, "rudder_blade_%d" % k, v3(0, y_bot, za), v3(0, y_bot + (0.3 if k == len(zz) - 2 else 0.0), zb), v3(0, top(za), za), v3(0, top(zb), zb),
             th, "hull", v3(1, 0, 0), back="hull", side="dark_wood", u_dir=v3(0, 0, -1), v_dir=v3(0, -1, 0), stretch=False)
    beam(rb, "rudder_edge", v3(0, y_bot + 0.3, ze - 0.08), v3(0, top(ze) - 0.1, ze - 0.08), 0.42, "sternpost", width=0.2, extend=0.05)
    beam(rb, "rudder_foot", v3(0, y_bot - 0.02, zs + 0.05), v3(0, y_bot + 0.25, ze - 0.05), 0.14, "iron", width=th + 0.06)
    tube(rb, "rudder_stock", v3(0, y_bot + 0.2, zs + 0.08), v3(0, top(zs) + 0.4, zs + 0.08), 0.36, "dark_wood", sides=6)
    for k, y in enumerate(np.linspace(y_bot + 0.8, top(ze) - 0.3, 4)):
        beam(rb, "rudder_strap_%d" % k, v3(0, y, zs + 0.1), v3(0, y, ze + 0.1), 0.08, "iron", width=th + 0.06)


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


def ladders(bone, outside=None):
    for name, (x0, x1, y0, y1, z0, z1) in ji.LADDERS.items():
        if name == "bow":
            # a rope ladder down the bow face: two ropes, wooden rungs
            pa = lambda y: v3(x0 + 0.12, y, z0 + 0.1)  # noqa: E731
            pb = lambda y: v3(x1 - 0.12, y, z0 + 0.1)  # noqa: E731
            top = js.sheer_y(BZ) + 0.2
            bottom = max(y0, js.beak_top(z0 + 0.3)) + 0.05
            rope(outside, "bow_ladder_rope_a", pa(top), pa(bottom), d=0.07)
            rope(outside, "bow_ladder_rope_b", pb(top), pb(bottom), d=0.07)
            y, i = bottom + 0.3, 0
            while y < top - 0.1:
                beam(outside, "bow_ladder_rung_%d" % i, pa(y) + v3(-0.05, 0, 0.02), pb(y) + v3(0.05, 0, 0.02), 0.07, "plank_light", width=0.09)
                y += 0.42
                i += 1
            continue
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
    stern_gallery(hull_b, detail)
    house(house_b, detail, lights, root)
    porch(house_b, detail, lights)
    roof(roof_b, detail, lights)
    porch_roof(roof_b, detail, lights)
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
    ladders(fittings, hull_b)
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
