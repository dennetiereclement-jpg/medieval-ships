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

STATIONS = [-27.5, -26.4, -25.0, -23.4, -21.6, -19.6, -17.4, -15.0, -12.5, -10.0, -7.4, -4.8, -2.2, 0.4,
            3.0, 5.6, 8.2, 10.8, 13.2, 15.6, 17.8, 19.8, 21.6, 23.2, 24.6, 25.8, 26.8, 27.5, 28.0, 28.35]
# hull bands above the waterline, bottom to top: white bottom, black wale, ochre (lower guns),
# black, ochre (middle guns), black wale, dark upper works
BANDS = [0.3, 1.0, 2.05, 2.6, 3.85, 4.4]
STRAKES = ["white_bottom", "white_bottom", "white_bottom", "white_bottom",
           "hull_black", "ochre", "hull_black", "ochre", "hull_black", "hull_black"]


CABIN_WINDOWS_Z = (-12.0, -14.5, -17.0, -21.0, -22.8)
CABIN_WINDOW_Y = 5.65


def lift(z):
    return ws.band_lift(z)


def hw(z):
    return ws.half_width(z)


def outer_x(z, y):
    """Outer surface of the hull side (above the waterline): slight tumblehome up to the sheer."""
    w = hw(z)
    ys = ws.sheer_y(z)
    if y >= ys:
        return 0.975 * w
    if y <= 0.3:
        return w
    return w * (1 - 0.035 * (y - 0.3) / (ys - 0.3))


gn.outer_x = outer_x
gn.hw = hw


def section(z, side):
    w, yk, ys = hw(z), ws.keel_y(z), ws.sheer_y(z)
    pts = [(0.08, yk)]
    for fx, fy in ws.BOTTOM_SECTION[1:]:
        pts.append((fx * w, fy * yk))
    for y in [b + (lift(z) if b > 0.5 else 0.0) for b in BANDS] + [ys]:
        pts.append((outer_x(z, y), y))
    return [v3(side * max(x, 0.08), y, z) for x, y in pts]


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
    for side, sn in SIDES:
        for i in range(len(STATIONS) - 1):
            za, zb = STATIONS[i], STATIONS[i + 1]
            A, B = section(za, side), section(zb, side)
            for k, reg in enumerate(STRAKES):
                mid = (A[k] + A[k + 1] + B[k] + B[k + 1]) / 4
                outward = norm(v3(side, -0.7 if k < 4 else 0.0, 0) + v3(0, 0, 0.35 * np.sign(mid[2])))
                board(hull, "hull_%s%d_%d" % (sn, i, k), A[k], A[k + 1], B[k], B[k + 1], 0.14, reg,
                      outward, inner="hull_light" if k >= 8 else None)
            if hw(za) > 0.8 and hw(zb) > 0.8:
                for j, y in enumerate((1.0, 2.6, 4.4)):
                    ya, yb = y + lift(za), y + lift(zb)
                    pa, pb = v3(side * (outer_x(za, ya) + 0.05), ya, za), v3(side * (outer_x(zb, yb) + 0.05), yb, zb)
                    beam(hull, "wale_%s%d_%d" % (sn, i, j), pa, pb, 0.16, "wale", width=0.2, extend=0.05)
                # thin gilded mouldings along the top of the ochre bands and under the rail
                for j, y in enumerate((2.05, 3.85, 5.25)):
                    ya, yb = y + lift(za), y + lift(zb)
                    if yb > ws.sheer_y(zb) - 0.1 or ya > ws.sheer_y(za) - 0.1:
                        continue
                    pa, pb = v3(side * (outer_x(za, ya) + 0.03), ya, za), v3(side * (outer_x(zb, yb) + 0.03), yb, zb)
                    beam(hull, "moulding_%s%d_%d" % (sn, i, j), pa, pb, 0.07, "gold", width=0.07, extend=0.04)
            if ws.QUARTERDECK_START - 0.01 <= za and zb <= ws.FORECASTLE_START + 0.01:
                pa = v3(side * 0.975 * hw(za), ws.sheer_y(za) + 0.08, za)
                pb = v3(side * 0.975 * hw(zb), ws.sheer_y(zb) + 0.08, zb)
                beam(hull, "rail_%s%d" % (sn, i), pa, pb, 0.16, "gold", width=0.34, extend=0.06)
                # sailors' rolled hammocks stowed along the rail of the waist (hammock nettings)
                ha = v3(side * (0.975 * hw(za) - 0.12), ws.sheer_y(za) + 0.32, za)
                hb = v3(side * (0.975 * hw(zb) - 0.12), ws.sheer_y(zb) + 0.32, zb)
                beam(hull, "hammocks_%s%d" % (sn, i), ha, hb, 0.34, "cloth_roll", width=0.3, extend=0.02)
    for i in range(len(STATIONS) - 1):
        za, zb = STATIONS[i], STATIONS[i + 1]
        beam(hull, "keel_%d" % i, (0, ws.keel_y(za) - 0.07, za), (0, ws.keel_y(zb) - 0.07, zb), 0.3,
             "white_bottom", width=0.42, extend=0.06)

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
                beam(bone, "%s_cap_%s%d" % (tag, sn, i), (xa, top_y + 0.08, za), (xb, top_y + 0.08, zb), 0.16, "gold",
                     width=0.34, extend=0.06)
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
    bulwark(fore, "fc", ws.FORECASTLE_START, 28.3, ws.FC_RAIL_Y, windows=(20.5, 23.0))

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
            gn.decal(cabin, "cabin_window_%s%d" % (sn, j), z, CABIN_WINDOW_Y, side, 0.7, 0.85, "glow_window", glow=True)
            gn.decal(cabin, "cabin_window_frame_%s%d" % (sn, j), z, CABIN_WINDOW_Y, side, 0.86, 1.0, "gold", out=0.0, th=0.03)
            gn.inner_decal(cabin, "cabin_window_in_%s%d" % (sn, j), z, CABIN_WINDOW_Y, side, 0.7, 0.85, "window_in", wall=0.14)
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
    sd.hanging_lantern(gg, lanterns, "council_lantern", (0, slab_bottom - 0.2, -22.0), drop=0.25)
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
        beam(bone, tag + "_top", (-half, y + ws.RAIL_HEIGHT - 0.05, z), (half, y + ws.RAIL_HEIGHT - 0.05, z), 0.1, "gold",
             width=ws.RAIL_THICK, extend=0.05)
        for j, x in enumerate(np.linspace(-half, half, 9)):
            beam(bone, "%s_baluster_%d" % (tag, j), (x, y, z), (x, y + ws.RAIL_HEIGHT - 0.1, z), 0.1, "hull_light")

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
        gn.decal(hull, "entry_pediment_" + sn, zz, 5.6, side, 1.3, 0.28, "gold_relief", out=0.04, th=0.06)
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

    # ---- stern: tall decorated transom, three tiers of windows, galleries, coat of arms
    zt = -ws.HALF_LENGTH
    # the hull bands wrap around the counter (white, black, ochre, black), the decorated stern
    # with its window tiers stands above
    lt = lift(zt)
    counter = [0.3, 1.0 + lt, 2.05 + lt, 2.6 + lt]
    bands = list(np.linspace(ws.keel_y(zt), 0.3, 5)) + counter[1:] + list(np.linspace(counter[-1], ws.POOP_RAIL_Y, 11))[1:]
    for k in range(len(bands) - 1):
        y0, y1 = bands[k], bands[k + 1]
        ym = (y0 + y1) / 2
        if ym < 0.3:
            pts = section(zt, 1)
            w = min(hw(zt), max(0.2, max(p[0] for p in pts if p[1] <= ym + 0.3)))
            reg = "white_bottom"
        else:
            w = outer_x(zt, ym)
            reg = "ochre" if counter[1] < ym < counter[2] else "hull_black"
        inside = main_y - 0.2 < ym < ws.POOP_Y
        add_cube(stern, "transom_%d" % k, (0, ym, zt + 0.12), EYE, (2 * w, y1 - y0 + 0.02, 0.24),
                 {"all": reg, "+3": "hull_light"} if inside else reg)
    for j, y in enumerate(counter[1:]):
        w = outer_x(zt, y)
        add_cube(stern, "transom_wale_%d" % j, (0, y, zt - 0.03), EYE, (2 * w + 0.1, 0.16 if j != 1 else 0.07, 0.1),
                 "gold" if j == 1 else "wale")
    # stern chasers: two guns firing aft through the counter
    for side, sn in SIDES:
        y = (counter[1] + counter[2]) / 2
        add_cube(stern, "stern_chaser_port_" + sn, (side * 1.6, y, zt - 0.01), EYE, (0.72, 0.66, 0.04), "gunport", stretch=True)
        beam(stern, "stern_chaser_" + sn, (side * 1.6, y, zt + 0.1), (side * 1.6, y, zt - 0.75), 0.3, "cannon")
        add_cube(stern, "stern_chaser_muzzle_" + sn, (side * 1.6, y, zt - 0.72), EYE, (0.38, 0.38, 0.08), "iron")
        add_cube(stern, "stern_chaser_garland_" + sn, (side * 1.6, y, zt - 0.02), EYE, (1.15, 1.0, 0.02), "garland", stretch=True)
    # carved name board across the counter, under the lowest gallery
    add_cube(stern, "counter_board", (0, counter[3] + 0.25, zt - 0.05), EYE, (2.6, 0.36, 0.08), "gold_relief", stretch=True)
    for side, sn in SIDES:
        add_cube(stern, "counter_scroll_" + sn, (side * 1.55, counter[3] + 0.25, zt - 0.06), EYE, (0.5, 0.46, 0.1), "gold")
    tiers = ((5.0, 1.15, main_y), (7.75, 1.05, qd_y), (9.75, 0.6, poop_y))
    for t, (yc, h, floor) in enumerate(tiers):
        xs = (-2.7, -1.35, 0.0, 1.35, 2.7) if t < 2 else (-2.0, -0.7, 0.7, 2.0)
        for j, x in enumerate(xs):
            add_cube(stern, "glow_stern_window_%d_%d" % (t, j), (x, yc, zt - 0.03), EYE, (0.85, h, 0.06),
                     "arch_window" if t == 2 else "glow_window", stretch=True)
            add_cube(stern, "stern_window_frame_%d_%d" % (t, j), (x, yc, zt - 0.01), EYE, (1.02, h + 0.16, 0.04), "gold")
            if t < 2:
                add_cube(stern, "stern_window_sill_%d_%d" % (t, j), (x, yc - h / 2 - 0.08, zt - 0.08), EYE, (1.08, 0.08, 0.16), "gold")
                add_cube(stern, "stern_window_key_%d_%d" % (t, j), (x, yc + h / 2 + 0.06, zt - 0.08), EYE, (0.24, 0.18, 0.1),
                         "gold_relief", stretch=True)
            if t == 0:
                add_cube(cabin, "stern_window_in_%d" % j, (x, yc, zt + 0.26), EYE, (0.85, h, 0.03),
                         {"all": None, "+3": "window_in"}, stretch=True)
        for j in range(len(xs) + 1):
            x = (xs[0] - 0.68) + j * (xs[1] - xs[0]) if j <= len(xs) else 0
            add_cube(stern, "stern_pilaster_%d_%d" % (t, j), (x, yc, zt - 0.05), EYE, (0.18, h + 0.3, 0.08), "pilaster", stretch=True)
        add_cube(stern, "stern_cornice_%d" % t, (0, yc + h / 2 + 0.22, zt - 0.06), EYE, (2 * outer_x(zt, yc) + 0.1, 0.2, 0.14), "gold")
        add_cube(stern, "stern_frieze_%d" % t, (0, yc - h / 2 - 0.22, zt - 0.06), EYE, (2 * outer_x(zt, yc), 0.3, 0.1), "gold_relief")
        if t < 2:
            # stern gallery (balcony) under the windows
            gy = floor + 0.05
            add_cube(stern, "stern_gallery_%d" % t, (0, gy, zt - 0.45), EYE, (2 * outer_x(zt, yc) - 0.3, 0.16, 0.8),
                     {"all": "dark_wood", "+2": "deck"})
            beam(stern, "stern_gallery_rail_%d" % t, (-outer_x(zt, yc) + 0.2, gy + 0.75, zt - 0.8), (outer_x(zt, yc) - 0.2, gy + 0.75, zt - 0.8),
                 0.1, "gold", width=0.12)
            for j, x in enumerate(np.linspace(-outer_x(zt, yc) + 0.25, outer_x(zt, yc) - 0.25, 11)):
                beam(stern, "stern_gallery_baluster_%d_%d" % (t, j), (x, gy + 0.08, zt - 0.8), (x, gy + 0.7, zt - 0.8), 0.08, "gold")
            gx = outer_x(zt, yc) - 0.2
            add_cube(stern, "stern_gallery_fascia_%d" % t, (0, gy - 0.16, zt - 0.84), EYE, (2 * gx + 0.1, 0.2, 0.08), "gold_relief",
                     stretch=True)
            for side, sn in SIDES:
                beam(stern, "stern_gallery_end_rail_%d_%s" % (t, sn), (side * gx, gy + 0.75, zt - 0.8), (side * gx, gy + 0.75, zt - 0.05),
                     0.1, "gold", width=0.12)
                for j, z in enumerate((zt - 0.3, zt - 0.55)):
                    beam(stern, "stern_gallery_end_baluster_%d_%s%d" % (t, sn, j), (side * gx, gy + 0.08, z), (side * gx, gy + 0.7, z),
                         0.08, "gold")
                beam(stern, "stern_gallery_post_%d_%s" % (t, sn), (side * gx, gy, zt - 0.8), (side * gx, gy + 0.9, zt - 0.8), 0.14,
                     "gold_relief")
                add_cube(stern, "stern_gallery_post_cap_%d_%s" % (t, sn), (side * gx, gy + 0.97, zt - 0.8), EYE, (0.2, 0.14, 0.2), "gold")
            for j, x in enumerate((-2.9, -1.0, 1.0, 2.9)):
                beam(stern, "stern_gallery_bracket_%d_%d" % (t, j), (x, gy - 0.75, zt - 0.05), (x, gy - 0.1, zt - 0.78),
                     0.16, "gold_relief", width=0.2)
    # gilded corner columns of the stern, carved crest (taffrail) around the arms
    for side, sn in SIDES:
        x = side * (outer_x(zt, 7.0) - 0.15)
        beam(stern, "stern_column_" + sn, (x, 4.2, zt - 0.1), (x, ws.POOP_RAIL_Y + 0.2, zt - 0.1), 0.34, "gold_relief")
        add_cube(stern, "stern_column_cap_" + sn, (x, ws.POOP_RAIL_Y + 0.35, zt - 0.1), EYE, (0.5, 0.3, 0.5), "gold")
        add_cube(stern, "stern_column_base_" + sn, (x, 4.1, zt - 0.1), EYE, (0.5, 0.3, 0.5), "gold")
    for k in range(9):
        a = math.pi * k / 8
        c = v3(math.cos(a) * 2.25, ws.POOP_RAIL_Y + 0.35 + math.sin(a) * 1.55, zt + 0.12)
        add_cube(stern, "taffrail_crest_%d" % k, c, gg.rz(a - math.pi / 2), (0.62, 0.36, 0.2), "gold_relief")
    for side, sn in SIDES:
        add_cube(stern, "taffrail_scroll_" + sn, (side * 2.6, ws.POOP_RAIL_Y + 0.25, zt + 0.12), EYE, (0.7, 0.4, 0.22), "gold_relief")
    for k in range(6):
        dy0, dy1 = 1.5 * k / 6, 1.5 * (k + 1) / 6
        half = 2.15 * max(0.0, 1 - ((dy0 + dy1) / 2 / 1.55) ** 2) ** 0.5
        add_cube(stern, "crest_plate_%d" % k, (0, ws.POOP_RAIL_Y + 0.35 + (dy0 + dy1) / 2, zt + 0.26), EYE, (2 * half, dy1 - dy0 + 0.02, 0.06),
                 {"all": "hull_black", "-3": "ochre"})
    for side, sn in SIDES:
        f = v3(side * 1.75, ws.POOP_RAIL_Y + 0.2, zt + 0.1)
        add_cube(stern, "crest_figure_base_" + sn, f + v3(0, 0.1, 0), EYE, (0.5, 0.2, 0.45), "gold")
        add_cube(stern, "crest_figure_body_" + sn, f + v3(0, 0.6, 0), gg.rz(side * 0.12), (0.34, 0.8, 0.3), "gold_relief")
        add_cube(stern, "crest_figure_head_" + sn, f + v3(side * 0.05, 1.15, 0), EYE, (0.24, 0.26, 0.24), "gold")
        beam(stern, "crest_figure_arm_" + sn, f + v3(side * 0.05, 0.85, 0), f + v3(-side * 0.35, 1.25, -0.05), 0.1, "gold")
        beam(stern, "crest_figure_trumpet_" + sn, f + v3(side * 0.05, 1.15, -0.1), f + v3(side * 0.35, 1.55, -0.25), 0.06, "gold")
    arms = v3(0, ws.POOP_RAIL_Y + 0.75, zt + 0.1)
    add_cube(stern, "arms_frame", arms, EYE, (1.8, 1.3, 0.1), "gold")
    add_cube(stern, "arms_emblem", arms - v3(0, 0, 0.06), EYE, (1.55, 1.05, 0.04), {"all": None, "-3": "flag"}, stretch=True,
             u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0))
    add_cube(stern, "arms_crown", arms + v3(0, 0.82, 0), EYE, (0.8, 0.34, 0.12), "carving", stretch=True)
    for side, sn in SIDES:
        add_cube(stern, "arms_supporter_" + sn, arms + v3(side * 1.1, -0.1, 0), EYE, (0.3, 1.2, 0.16), "pilaster", stretch=True)
        # quarter galleries on the stern corners, two storeys
        qz0, qz1 = -27.1, -23.6
        qx = 0.975 * hw(-25.4)
        for t, (y0, y1) in enumerate(((4.7, 6.9), (7.3, 9.3))):
            g = v3(side * (qx + 0.25), (y0 + y1) / 2, (qz0 + qz1) / 2)
            # in slices that follow the narrowing hull, so that nothing pokes into the cabins
            for j in range(8):
                za, zb = qz0 + (qz1 - qz0) * j / 8, qz0 + (qz1 - qz0) * (j + 1) / 8
                x_in, x_out = 0.975 * hw(zb) - 0.08, qx + 0.525
                add_cube(stern, "quarter_gallery_%s%d_%d" % (sn, t, j), (side * (x_in + x_out) / 2, (y0 + y1) / 2, (za + zb) / 2), EYE,
                         (x_out - x_in, y1 - y0, zb - za + 0.01), {"all": "hull_black", "+2": "dark_wood"})
            for j, z in enumerate((qz0 + 0.8, (qz0 + qz1) / 2, qz1 - 0.8)):
                add_cube(stern, "glow_quarter_window_%s%d_%d" % (sn, t, j), (side * (qx + 0.54), (y0 + y1) / 2, z), EYE,
                         (0.04, (y1 - y0) * 0.6, 0.6), "arch_window", stretch=True)
            for j, z in enumerate((qz0 + 0.1, (qz0 + qz1) / 2 - 0.9, (qz0 + qz1) / 2 + 0.9, qz1 - 0.1)):
                add_cube(stern, "quarter_pilaster_%s%d_%d" % (sn, t, j), (side * (qx + 0.55), (y0 + y1) / 2, z), EYE,
                         (0.06, y1 - y0, 0.16), "pilaster", stretch=True)
            add_cube(stern, "quarter_cornice_%s%d" % (sn, t), g + v3(side * 0.03, (y1 - y0) / 2 + 0.06, 0), EYE,
                     (0.65, 0.14, qz1 - qz0 + 0.14), "gold")
        # domed roof of the quarter gallery with its finial
        gc = v3(side * (qx + 0.2), 9.35, (qz0 + qz1) / 2)
        for t, (wx, wz, hy) in enumerate(((0.8, 3.7, 0.22), (0.62, 2.9, 0.22), (0.44, 2.0, 0.2), (0.26, 1.1, 0.2))):
            add_cube(stern, "quarter_dome_%s%d" % (sn, t), gc + v3(0, 0.11 + t * 0.2, 0), EYE, (wx, hy, wz), "gold" if t % 2 else "gold_relief")
        add_cube(stern, "quarter_finial_" + sn, gc + v3(0, 1.0, 0), EYE, (0.18, 0.4, 0.18), "gold")
        add_cube(stern, "quarter_finial_ball_" + sn, gc + v3(0, 1.3, 0), EYE, (0.24, 0.24, 0.24), "gold")
        beam(stern, "quarter_drop_" + sn, (side * (qx + 0.2), 4.6, (qz0 + qz1) / 2), (side * (qx - 0.1), 3.0, (qz0 + qz1) / 2),
             0.3, "gold_relief", width=0.9)
        add_cube(stern, "quarter_drop_finial_" + sn, (side * (qx - 0.05), 2.85, (qz0 + qz1) / 2), EYE, (0.3, 0.35, 0.3), "gold")
    # stern lanterns on the taffrail
    for k, (x, s) in enumerate(((2.7, 1.0), (-2.7, 1.0), (0.0, 1.4))):
        y, z = ws.POOP_RAIL_Y + (0.2 if k < 2 else 1.9), zt + 0.25
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
    add_cube(rudder, "rudder_blade", (0, -0.85, -ws.HALF_LENGTH - 0.75), EYE, (0.26, 1.9, 1.2), "white_bottom")
    add_cube(rudder, "rudder_blade_top", (0, 1.4, -ws.HALF_LENGTH - 0.75), EYE, (0.26, 2.6, 1.2), {"all": "hull_black", "+2": "end_grain"})
    add_cube(rudder, "rudder_top", (0, 3.1, -ws.HALF_LENGTH - 0.3), EYE, (0.3, 1.0, 0.36), "hull_black")
    for k, y in enumerate((-1.3, 0.0, 1.3, 2.5)):
        add_cube(rudder, "rudder_pintle_%d" % k, (0, y, -ws.HALF_LENGTH - 0.2), EYE, (0.36, 0.12, 0.36), "iron")

    # ---- bow: stem, beakhead, figurehead, head rails, catheads, anchors, bowsprit
    stem = []
    for j in range(8):
        t = j / 7
        stem.append(v3(0, ws.keel_y(27.5) - 0.1 + (ws.FC_RAIL_Y + 0.5 - ws.keel_y(27.5)) * t, 27.5 + 1.2 * t ** 1.5))
    for j in range(len(stem) - 1):
        beam(bow, "stem_%d" % j, stem[j], stem[j + 1], 0.5, "hull_black", width=0.6, extend=0.12)
    beam(bow, "beakhead", (0, 4.4, 27.8), (0, 5.4, 31.0), 0.4, "hull_black", width=1.4)
    beam(bow, "beakhead_deck", (0, 5.0, 27.6), (0, 5.8, 30.4), 0.14, "deck", width=1.8)
    for side, sn in SIDES:
        beam(bow, "head_rail_" + sn, (side * 1.0, 6.9, 27.0), (side * 0.15, 5.6, 31.0), 0.12, "gold")
        beam(bow, "head_rail_low_" + sn, (side * 1.2, 5.6, 27.2), (side * 0.2, 4.8, 30.8), 0.12, "gold")
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
    add_cube(fig, "figurehead_body", (0, 5.85, 31.35), rx(-0.55), (0.9, 1.0, 1.7), "gold_relief")
    add_cube(fig, "figurehead_mane", (0, 6.75, 32.0), rx(-0.3), (1.2, 1.15, 0.5), "gold_relief")
    add_cube(fig, "figurehead_head", (0, 6.75, 32.35), EYE, (0.8, 0.8, 0.75), "gold")
    add_cube(fig, "figurehead_muzzle", (0, 6.6, 32.8), EYE, (0.45, 0.4, 0.3), "gold")
    add_cube(fig, "figurehead_crown", (0, 7.3, 32.3), EYE, (0.6, 0.3, 0.55), "gold_relief")
    for side, sn in SIDES:
        add_cube(fig, "figurehead_paw_" + sn, (side * 0.3, 5.3, 31.95), EYE, (0.28, 0.5, 0.35), "gold")
        add_cube(fig, "figurehead_ear_" + sn, (side * 0.32, 7.15, 32.3), EYE, (0.18, 0.2, 0.15), "gold")
        pts = [v3(side * 1.4, 7.3, 26.8), v3(side * 1.05, 6.7, 28.6), v3(side * 0.55, 6.1, 30.1), v3(side * 0.2, 5.8, 31.0)]
        for j in range(len(pts) - 1):
            beam(bow, "head_rail_curve_%s%d" % (sn, j), pts[j], pts[j + 1], 0.14, "gold", extend=0.05)
        add_cube(bow, "beak_scroll_" + sn, (side * 0.72, 4.95, 29.3), EYE, (0.06, 0.6, 2.2), "gold_relief")
        add_cube(bow, "cathead_face_" + sn, (side * (hw(24.0) * 0.975 + 1.15), ws.FC_RAIL_Y - 0.2, 24.3), EYE, (0.3, 0.34, 0.34), "gold")
    sprit_a, sprit_b = v3(0, 6.6, 25.0), v3(0, 12.2, 36.0)
    jib_end = v3(0, 13.5, 38.6)
    beam(bow, "bowsprit", sprit_a, sprit_b, 0.6, "mast")
    beam(bow, "jibboom", sprit_b - norm(sprit_b - sprit_a) * 1.2, jib_end, 0.34, "mast")
    beam(bow, "bowsprit_cap", sprit_b - norm(sprit_b - sprit_a) * 0.2, sprit_b + norm(sprit_b - sprit_a) * 0.1, 0.7, "dark_wood")
    beam(bow, "jack_staff", sprit_b, sprit_b + v3(0, 1.2, 0), 0.1, "dark_wood")
    add_cube(lanterns, "bow_lantern", (0, ws.FC_RAIL_Y + 0.6, 27.6), EYE, (0.45, 0.6, 0.45), {"all": "lantern", "+2": "iron"}, stretch=True)
    add_cube(lanterns, "glow_bow_lantern", (0, ws.FC_RAIL_Y + 0.6, 27.6), EYE, (0.3, 0.45, 0.3), "glow", stretch=True)

    # ---- masts with fighting tops, crosstrees and three square sails each
    sails_info = []

    def mast(name, z, foot, tops, thick):
        mb = Bone(name, origin=(0, foot, z), parent=root)
        t1, t2, t3 = tops
        beam(mb, name + "_lower", (0, foot - 0.2, z), (0, t1 + 0.8, z), thick, "mast")
        beam(mb, name + "_top", (0, t1 - 0.6, z), (0, t2 + 0.6, z), thick * 0.62, "mast")
        beam(mb, name + "_topgallant", (0, t2 - 0.5, z), (0, t3, z), thick * 0.4, "mast")
        add_cube(mb, name + "_partners", (0, foot + 0.14, z), EYE, (thick + 0.45, 0.28, thick + 0.45), "dark_wood")
        for k, y in enumerate(np.linspace(foot + 1.5, t1 - 1.0, 4)):
            add_cube(mb, "%s_woolding_%d" % (name, k), (0, y, z), EYE, (thick + 0.06, 0.16, thick + 0.06), "rope")
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
        beam(mb, name, (-half, y, z + 0.5), (half, y, z + 0.5), 0.3, "mast_dark", extend=0.12)
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
    square_sail(m_fore, "fore_course", ws.FORE_MAST_Z, 18.0, 5.6, 6.4, 9.0, 1.6)
    square_sail(m_fore, "fore_topsail", ws.FORE_MAST_Z, 26.6, 4.0, 5.2, 7.0, 1.3)
    square_sail(m_fore, "fore_topgallant", ws.FORE_MAST_Z, 33.2, 2.6, 3.4, 5.4, 1.0)
    square_sail(m_main, "main_course", ws.MAIN_MAST_Z, 20.0, 7.0, 7.8, 10.4, 1.9)
    square_sail(m_main, "main_topsail", ws.MAIN_MAST_Z, 30.2, 4.8, 6.4, 8.6, 1.5)
    square_sail(m_main, "main_topgallant", ws.MAIN_MAST_Z, 39.6, 3.2, 4.4, 7.4, 1.1)
    square_sail(m_miz, "mizzen_topsail", ws.MIZZEN_Z, 24.6, 3.4, 4.4, 6.4, 1.0)
    # mizzen lateen
    lat_fore, lat_aft = v3(0.5, 12.0, -9.8), v3(0.5, 23.5, -25.0)
    beam(m_miz, "lateen_yard", lat_fore - norm(lat_aft - lat_fore) * 0.4, lat_aft, 0.24, "mast")
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
            (v3(0, 18.6, ws.FORE_MAST_Z + 0.4), sprit_a + (sprit_b - sprit_a) * 0.5, v3(0.06, 8.8, 23.6), 0.5),
            (v3(0, 27.0, ws.FORE_MAST_Z + 0.3), sprit_b, v3(0.06, 9.6, 27.2), 0.5),
            (v3(0, 33.0, ws.FORE_MAST_Z + 0.2), jib_end, v3(0.06, 11.4, 30.4), 0.45))):
        head = tack + (top - tack) * 0.6
        tri = gn.tri_sail(jib, "jib_%d" % k, head + v3(0, -0.05, -0.06), tack + v3(0, 0.05, -0.12), clew, depth * 1.6, v3(1, 0, 0),
                          "jib", ny=6)
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
