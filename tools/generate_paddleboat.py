#!/usr/bin/env python3
"""Generates the armoured steam paddleboat (steam_paddleboat) Blockbench model, its texture and animations.

Usage:  python3 tools/generate_paddleboat.py

Outputs:
  blockbench/steam_paddleboat.bbmodel                                   (editable, texture embedded)
  src/main/resources/assets/medievalships/models/entity/steam_paddleboat.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/steam_paddleboat.png
  src/main/resources/assets/medievalships/textures/item/steam_paddleboat.png

Reference: low massive armoured hull in dark grey riveted plates, reinforced bow with a ram,
a long brown deckhouse with lit windows, two tall grey funnels one behind the other, a big
paddle wheel on each side under its arched box, iron railing with lanterns all
round, brass guns on turntables fore and aft, a small signal mast aft.

Bones used by the mod (keep their names when editing in Blockbench):
  paddle_wheel, paddle_wheel_port (paddle: one turn per animation loop, played with the signed speed)
  helm_wheel, rudder (steer)   flag, flag_tip (flag_wave)
"""
import math
import os
import sys
import uuid

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import generate_galleon as gn  # noqa: E402
import generate_galley as gg  # noqa: E402
import paddleboat_shape as ps  # noqa: E402
import paddleboat_texture as pt  # noqa: E402
import ship_details as sd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/steam_paddleboat/%d" % _uuid_counter[0]))


gg.new_uuid = new_uuid
gn.new_uuid = new_uuid
gn.gs = ps
gn.REGIONS = {k: (0,) + r for k, r in pt.REGIONS.items()}
gn.SIZE = pt.SIZE

v3, norm, Bone, add_cube, beam, board = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam, gg.board
rx, ry, rz = gg.rx, gg.ry, gg.rz
EYE = np.eye(3)
SIDES = ((1, "p"), (-1, "s"))

FORE_END, AFT_END = ps.FORE_SCALE - 0.02, -ps.AFT_SCALE + 0.02
STATIONS = [AFT_END, -11.0, -10.6, -10.0, -9.2, -8.0, -6.5, -4.8, -3.0, -1.0, 1.0, 3.0, 4.8, 6.4, 7.8, 8.9, 9.8, 10.4, 10.8,
            FORE_END]
UPPER = [0.4, 1.2, 1.9, ps.PLATING_TOP]
STRAKES = ["plate_dark"] * 4 + ["plate", "plate", "plate"]


def hw(z):
    return ps.half_width(z)


def outer_x(z, y):
    """Plated side: nearly vertical, a slight tumblehome up to the deck edge."""
    w = hw(z)
    if y <= 0.4:
        return w
    return w * (1.0 - 0.025 * min(1.0, (y - 0.4) / (ps.PLATING_TOP - 0.4)))


gn.outer_x = outer_x
gn.hw = hw


def section(z, side):
    w, yk = hw(z), ps.keel_y(z)
    pts = [(0.06, yk)]
    for fx, fy in ps.BOTTOM_SECTION[1:]:
        pts.append((fx * w, fy * yk))
    for y in UPPER:
        pts.append((outer_x(z, y), y))
    return [v3(side * max(x, 0.06), y, z) for x, y in pts]


def octagon(bone, name, c, half, h, region, cap=None):
    """Round-looking vertical column: a square box and the same box turned 45 degrees."""
    add_cube(bone, name + "_a", c, EYE, (2 * half, h, 2 * half), {"all": region, "+2": cap, "-2": cap})
    add_cube(bone, name + "_b", c, ry(math.pi / 4), (2 * half, h, 2 * half), {"all": region, "+2": cap, "-2": cap})


def gun(bone, tag, z, s):
    """Brass gun on a wooden carriage, on a brass turntable on top of a raised armoured platform
    (barbette) with its railing; s=+1 fires forward, -1 aft."""
    base = ps.MAIN_DECK_Y
    octagon(bone, tag + "_barbette", v3(0, base + ps.GUN_PLATFORM / 2, z), 0.95, ps.GUN_PLATFORM, "plate", cap="deck")
    octagon(bone, tag + "_barbette_band", v3(0, base + ps.GUN_PLATFORM - 0.06, z), 0.98, 0.1, "brass")
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        if abs(math.sin(a)) > 0.9 and math.cos(a) * s < 0:
            continue  # opening at the back for the gunners
        p = v3(math.sin(a) * 0.92, base + ps.GUN_PLATFORM, z + math.cos(a) * 0.92)
        beam(bone, "%s_rail_post_%d" % (tag, k), p, p + v3(0, 0.55, 0), 0.05, "brass")
        a2 = 2 * math.pi * (k + 1.5) / 8
        q = v3(math.sin(a2) * 0.92, base + ps.GUN_PLATFORM + 0.55, z + math.cos(a2) * 0.92)
        beam(bone, "%s_rail_%d" % (tag, k), p + v3(0, 0.55, 0), q, 0.05, "brass", extend=0.02)
    for k in range(3):
        add_cube(bone, "%s_step_%d" % (tag, k), v3(0, base + 0.1 + 0.2 * k, z - s * (1.15 - 0.12 * k)), EYE, (0.8, 0.2, 0.28), "gunmetal")
    deck = base + ps.GUN_PLATFORM
    octagon(bone, tag + "_turntable", v3(0, deck + 0.06, z), 0.75, 0.12, "brass", cap="gunmetal")
    for x in (0.32, -0.32):
        add_cube(bone, "%s_cheek_%d" % (tag, x > 0), v3(x, deck + 0.5, z), EYE, (0.14, 0.7, 1.5), "dark_wood")
        for dz in (-0.5, 0.5):
            add_cube(bone, "%s_wheel_%d_%d" % (tag, x > 0, dz > 0), v3(x * 1.35, deck + 0.3, z + dz), EYE, (0.08, 0.42, 0.42), "brass")
    y = deck + 0.92
    breech, muzzle = v3(0, y, z - s * 0.9), v3(0, y + 0.08, z + s * 1.4)
    beam(bone, tag + "_barrel", breech, muzzle, 0.38, "brass")
    beam(bone, tag + "_chase", muzzle - (muzzle - breech) * 0.35, muzzle, 0.3, "brass")
    add_cube(bone, tag + "_muzzle", muzzle, EYE, (0.42, 0.42, 0.14), "brass")
    add_cube(bone, tag + "_bore", muzzle + v3(0, 0, s * 0.075), EYE, (0.2, 0.2, 0.02), "iron")
    add_cube(bone, tag + "_breech", breech - v3(0, 0, s * 0.18), EYE, (0.3, 0.3, 0.2), "brass")
    for f in (0.25, 0.55):
        p = breech + (muzzle - breech) * f
        add_cube(bone, "%s_ring_%d" % (tag, int(f * 10)), p, EYE, (0.44, 0.44, 0.08), "gunmetal")
    add_cube(bone, tag + "_trunnion", v3(0, y - 0.05, z - s * 0.2), EYE, (0.72, 0.14, 0.14), "gunmetal")


def lamp(bone, name, c, s=1.0):
    """Ship's lantern: lit glass (drawn full bright) in a thin iron frame, base plate, domed cap,
    brass finial and carrying ring."""
    c = v3(*c)
    hw_, hh = 0.11 * s, 0.16 * s
    add_cube(bone, "glow_" + name, c, EYE, (2 * hw_, 2 * hh, 2 * hw_), {"all": "lamp_glass", "+2": "gunmetal", "-2": "gunmetal"},
             stretch=True)
    for i, (dx, dz) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        add_cube(bone, "%s_frame_%d" % (name, i), c + v3(dx * hw_, 0, dz * hw_), EYE, (0.035 * s, 2 * hh + 0.02 * s, 0.035 * s), "gunmetal")
    add_cube(bone, name + "_base", c - v3(0, hh + 0.025 * s, 0), EYE, (2 * hw_ + 0.07 * s, 0.05 * s, 2 * hw_ + 0.07 * s), "gunmetal")
    add_cube(bone, name + "_cap", c + v3(0, hh + 0.025 * s, 0), EYE, (2 * hw_ + 0.08 * s, 0.05 * s, 2 * hw_ + 0.08 * s), "gunmetal")
    add_cube(bone, name + "_dome", c + v3(0, hh + 0.09 * s, 0), EYE, (2 * hw_ - 0.02 * s, 0.08 * s, 2 * hw_ - 0.02 * s), "gunmetal")
    add_cube(bone, name + "_finial", c + v3(0, hh + 0.16 * s, 0), EYE, (0.06 * s, 0.07 * s, 0.06 * s), "brass")
    beam(bone, name + "_ring", c + v3(-0.06 * s, hh + 0.22 * s, 0), c + v3(0.06 * s, hh + 0.22 * s, 0), 0.025 * s, "brass")


def build():
    root = Bone("steam_paddleboat")
    hull = Bone("hull", parent=root)
    deck = Bone("deck", parent=root)
    house = Bone("deckhouse", parent=root)
    funnels = Bone("funnels", parent=root)
    rail = Bone("railing", parent=root)
    lanterns = Bone("lanterns", parent=root)
    box = Bone("paddle_box", parent=root)
    guns = Bone("guns", parent=root)
    ropes = Bone("ropes", parent=root)
    main_y = ps.MAIN_DECK_Y

    # ---- armoured hull: plates between rounded sections, riveted bands, portholes
    for side, sn in SIDES:
        for i in range(len(STATIONS) - 1):
            za, zb = STATIONS[i], STATIONS[i + 1]
            A, B = section(za, side), section(zb, side)
            for k, reg in enumerate(STRAKES):
                mid = (A[k] + A[k + 1] + B[k] + B[k + 1]) / 4
                outward = norm(v3(side, -0.7 if k < 4 else 0.0, 0) + v3(0, 0, 0.35 * np.sign(mid[2])))
                board(hull, "hull_%s%d_%d" % (sn, i, k), A[k], A[k + 1], B[k], B[k + 1], 0.14, reg, outward,
                      inner="plate_inner" if k >= 6 else None)
            for j, (y, reg, th) in enumerate(((0.4, "rivet_band", 0.16), (1.9, "rivet_band", 0.12), (ps.PLATING_TOP, "gunmetal", 0.14))):
                pa, pb = v3(side * (outer_x(za, y) + 0.04), y, za), v3(side * (outer_x(zb, y) + 0.04), y, zb)
                if j == 2:
                    pa, pb = pa - v3(side * 0.08, -0.02, 0), pb - v3(side * 0.08, -0.02, 0)
                beam(hull, "band_%s%d_%d" % (sn, i, j), pa, pb, th, reg, width=0.1 if j < 2 else 0.24, extend=0.05)
        for k, z in enumerate(np.arange(-8.4, 9.0, 1.6)):
            if abs(z - ps.WHEEL_Z) < ps.WHEEL_R + 0.6:
                continue
            p, u, v, n = gn.side_frame(z, 1.25, side)
            add_cube(hull, "glow_porthole_%s%d" % (sn, k), p + n * 0.02, np.column_stack([u, v, n]), (0.42, 0.42, 0.04),
                     {"all": None, "+3": "porthole"}, stretch=True, u_dir=u * side, v_dir=v3(0, -1, 0))
    for i in range(len(STATIONS) - 1):
        za, zb = STATIONS[i], STATIONS[i + 1]
        beam(hull, "keel_%d" % i, (0, ps.keel_y(za) - 0.06, za), (0, ps.keel_y(zb) - 0.06, zb), 0.24, "plate_dark",
             width=0.34, extend=0.05)
    # the sides close at the stern on a rounded counter plate
    ws = hw(AFT_END) + 0.08
    add_cube(hull, "stern_plate", (0, (ps.keel_y(AFT_END) + ps.PLATING_TOP) / 2, AFT_END - 0.02), EYE,
             (2 * ws, ps.PLATING_TOP - ps.keel_y(AFT_END), 0.16), {"all": "plate", "+3": "plate_inner"})
    beam(hull, "stern_post", (0, ps.keel_y(AFT_END) - 0.05, AFT_END - 0.08), (0, ps.PLATING_TOP + 0.05, AFT_END - 0.08), 0.3, "gunmetal",
         width=0.26)
    # reinforced bow: brass stem band and an iron ram at the waterline
    stem = [v3(0, ps.keel_y(FORE_END) - 0.05, FORE_END - 0.15), v3(0, 0.4, FORE_END + 0.05), v3(0, ps.PLATING_TOP + 0.1, FORE_END + 0.12)]
    for j in range(len(stem) - 1):
        beam(hull, "stem_%d" % j, stem[j], stem[j + 1], 0.34, "brass", width=0.3, extend=0.08)
    beam(hull, "ram", v3(0, -0.45, FORE_END - 0.6), v3(0, -0.2, ps.TIP), 0.5, "iron", width=0.7)
    beam(hull, "ram_tip", v3(0, -0.25, ps.TIP - 0.25), v3(0, -0.15, ps.TIP + 0.05), 0.32, "gunmetal", width=0.4)
    for side, sn in SIDES:
        add_cube(hull, "hawse_" + sn, gn.side_frame(9.6, 1.9, side)[0] + v3(side * 0.03, 0, 0), EYE, (0.06, 0.3, 0.3), "iron")
        # bow armour: a second, thicker layer of plates on the shoulders
        for k, z in enumerate((8.4, 9.4)):
            p, u, v, n = gn.side_frame(z, 1.2, side)
            add_cube(hull, "bow_armour_%s%d" % (sn, k), p + n * 0.05, np.column_stack([u, v, n]), (1.05, 2.0, 0.08),
                     {"all": "gunmetal", "+3": "plate"})
    # rounded counter at the stern, with the rudder under it
    rudder = Bone("rudder", origin=(0, 0.2, AFT_END + 0.1), parent=root)
    add_cube(rudder, "rudder_blade", (0, -0.7, AFT_END - 0.45), EYE, (0.2, 1.6, 0.95), "plate_dark")
    add_cube(rudder, "rudder_post", (0, 0.4, AFT_END + 0.05), EYE, (0.24, 1.0, 0.24), "iron")

    # ---- deck, hatches, vents, anchor, capstan, crates
    n = 32
    for j in range(n):
        za = ps.DECK_MIN_Z - 0.6 + (ps.DECK_MAX_Z - ps.DECK_MIN_Z + 1.0) * j / n
        zb = ps.DECK_MIN_Z - 0.6 + (ps.DECK_MAX_Z - ps.DECK_MIN_Z + 1.0) * (j + 1) / n
        w = min(ps.inner_half_width(za), ps.inner_half_width(zb)) + 0.1
        add_cube(deck, "deck_%d" % j, (0, main_y - 0.08, (za + zb) / 2), EYE, (2 * w, 0.16, zb - za + 0.02),
                 {"all": "plate_dark", "+2": "deck"})
    for k, (x, z) in enumerate(((0, 6.4), (0, -6.0))):
        add_cube(deck, "hatch_%d" % k, (x, main_y + 0.12, z), EYE, (1.4, 0.24, 1.0), {"all": "gunmetal", "+2": "grate"})
    for k, (x, z, s) in enumerate(((2.2, 5.6, 1), (-2.2, 5.6, 1), (2.6, -5.8, -1), (-2.6, -5.8, -1))):
        c = v3(x, main_y, z)
        beam(deck, "vent_pipe_%d" % k, c, c + v3(0, 1.0, 0), 0.24, "brass")
        add_cube(deck, "vent_cowl_%d" % k, c + v3(0, 1.15, s * 0.12), EYE, (0.46, 0.46, 0.38), {"all": "brass", "+3" if s > 0 else "-3": "iron"})
    for k, (x, z) in enumerate(((-1.6, -9.0), (1.7, -9.1), (1.6, 9.0))):
        sd.barrel(gg, deck, "barrel_%d" % k, (x, main_y, z), h=0.6, r=0.22, wood="gunmetal", ends="iron", hoop="brass")
    sd.crate(gg, deck, "crate_0", (-2.7, main_y, -8.0), s=0.55, wood="dark_wood", strap="iron")
    octagon(deck, "capstan", v3(0, main_y + 0.35, 9.4), 0.32, 0.7, "gunmetal", cap="brass")
    for side, sn in SIDES:
        ax = side * (hw(9.0) + 0.12)
        beam(deck, "anchor_shank_" + sn, (ax, 2.3, 9.0), (ax, 0.7, 9.0), 0.14, "iron")
        beam(deck, "anchor_arm_a_" + sn, (ax, 0.7, 9.0), (ax, 1.05, 8.6), 0.12, "iron")
        beam(deck, "anchor_arm_b_" + sn, (ax, 0.7, 9.0), (ax, 1.05, 9.4), 0.12, "iron")

    # ---- deckhouse: wooden panels in brass frames, lit windows, iron doors, pilot house in front
    z0, z1, hh, top = ps.HOUSE_Z0, ps.HOUSE_Z1, ps.HOUSE_HALF, ps.HOUSE_TOP
    hgt = top - main_y
    for side, sn in SIDES:
        add_cube(house, "house_wall_" + sn, (side * (hh - 0.08), main_y + hgt / 2, (z0 + z1) / 2), EYE, (0.16, hgt, z1 - z0),
                 "house")
        for k, z in enumerate(np.linspace(z0 + 0.9, z1 - 0.9, 7)):
            if k == 3:
                add_cube(house, "house_door_" + sn, (side * (hh + 0.01), main_y + 0.95, z), EYE, (0.04, 1.85, 0.8), "door",
                         stretch=True)
                continue
            add_cube(house, "glow_house_window_%s%d" % (sn, k), (side * (hh + 0.01), main_y + 1.35, z), EYE, (0.04, 0.6, 0.55),
                     "window", stretch=True)
        add_cube(house, "house_gauge_" + sn, (side * (hh + 0.02), main_y + 1.9, (z0 + z1) / 2 + 0.6), EYE, (0.04, 0.3, 0.3),
                 "gauge", stretch=True)
        beam(house, "house_pipe_" + sn, (side * (hh + 0.12), main_y + 0.3, z0 + 0.3), (side * (hh + 0.12), main_y + 0.3, z1 - 0.3),
             0.12, "copper")
    add_cube(house, "house_back", (0, main_y + hgt / 2, z0 + 0.08), EYE, (2 * hh, hgt, 0.16), "house")
    add_cube(house, "house_back_door", (0, main_y + 0.95, z0 - 0.01), EYE, (0.8, 1.85, 0.04), "door", stretch=True)
    add_cube(house, "house_front", (0, main_y + hgt / 2, z1 - 0.08), EYE, (2 * hh, hgt, 0.16), "house")
    for k, x in enumerate((-1.7, -0.85, 0.0, 0.85, 1.7)):
        add_cube(house, "glow_bridge_window_%d" % k, (x, main_y + 1.55, z1 + 0.01), EYE, (0.62, 0.75, 0.04), "window", stretch=True)
    add_cube(house, "house_roof", (0, top + 0.08, (z0 + z1) / 2), EYE, (2 * hh + 0.4, 0.16, z1 - z0 + 0.4),
             {"all": "brass", "+2": "roof", "-2": "plate_inner"})
    add_cube(house, "house_roof_rail", (0, top + 0.2, (z0 + z1) / 2), EYE, (2 * hh + 0.3, 0.08, z1 - z0 + 0.3), {"all": "iron", "+2": None,
                                                                                                         "-2": None})
    # bridge on the roof, over the front of the deckhouse
    add_cube(house, "bridge", (0, top + 0.75, z1 - 1.0), EYE, (2.4, 1.1, 1.6), {"all": "house", "+2": "roof"})
    for k, x in enumerate((-0.7, 0.0, 0.7)):
        add_cube(house, "glow_bridge_top_window_%d" % k, (x, top + 0.85, z1 - 0.19), EYE, (0.5, 0.5, 0.04), "window", stretch=True)
    add_cube(house, "bridge_roof", (0, top + 1.37, z1 - 1.0), EYE, (2.7, 0.12, 1.9), {"all": "brass", "+2": "roof"})
    add_cube(house, "whistle", (0.35, top + 1.65, z1 - 1.3), EYE, (0.14, 0.44, 0.14), "brass")
    # railing round the deckhouse roof, with lanterns at its corners, and skylights
    rt = top + 0.16
    corners = [v3(hh + 0.1, rt, z0 - 0.1), v3(hh + 0.1, rt, z1 + 0.1), v3(-hh - 0.1, rt, z1 + 0.1), v3(-hh - 0.1, rt, z0 - 0.1)]
    for k in range(4):
        a, b = corners[k], corners[(k + 1) % 4]
        n = max(2, int(np.linalg.norm(b - a) / 0.9))
        for j in range(n):
            p = a + (b - a) * (j / n)
            beam(house, "roof_post_%d_%d" % (k, j), p, p + v3(0, 0.55, 0), 0.05, "iron")
        beam(house, "roof_rail_%d" % k, a + v3(0, 0.55, 0), b + v3(0, 0.55, 0), 0.06, "brass", extend=0.03)
        c = a + v3(0, 0.55, 0)
        lamp(lanterns, "roof_lamp_%d" % k, c + v3(0, 0.22, 0))
    for k, z in enumerate((-3.9, -0.3, 2.6)):
        # skylight: an iron curb and a pitched glass roof, lit from the cabin below
        add_cube(house, "skylight_%d" % k, (0, top + 0.26, z), EYE, (1.1, 0.2, 0.7), {"all": "gunmetal", "+2": "iron"})
        for side in (1, -1):
            add_cube(house, "glow_skylight_%d_%d" % (k, side > 0), (side * 0.26, top + 0.46, z), gg.rz(-side * 0.42), (0.58, 0.04, 0.66),
                     {"all": "window", "-2": "iron"}, stretch=True)
        beam(house, "skylight_ridge_%d" % k, (0, top + 0.58, z - 0.36), (0, top + 0.58, z + 0.36), 0.05, "brass")

    # ---- funnels: grey brick, riveted iron bands, flared sooty tops; a steam pipe on each
    for k, z in enumerate(ps.FUNNEL_Z):
        h = ps.FUNNEL_TOP - top
        c = v3(0, top + h / 2, z)
        octagon(funnels, "funnel_%d" % k, c, ps.FUNNEL_HALF, h, "funnel")
        add_cube(funnels, "funnel_base_%d" % k, (0, top + 0.3, z), EYE, (2 * ps.FUNNEL_HALF + 0.3, 0.6, 2 * ps.FUNNEL_HALF + 0.3),
                 {"all": "gunmetal", "+2": "plate"})
        for j, y in enumerate((top + 1.6, top + 3.4, ps.FUNNEL_TOP - 1.0)):
            octagon(funnels, "funnel_band_%d_%d" % (k, j), v3(0, y, z), ps.FUNNEL_HALF + 0.06, 0.24, "funnel_band")
        octagon(funnels, "funnel_lip_%d" % k, v3(0, ps.FUNNEL_TOP + 0.1, z), ps.FUNNEL_HALF + 0.14, 0.3, "soot", cap="soot")
        # flared crown with a brass ring, like the reference funnels
        octagon(funnels, "funnel_crown_%d" % k, v3(0, ps.FUNNEL_TOP - 0.25, z), ps.FUNNEL_HALF + 0.22, 0.2, "funnel_band")
        octagon(funnels, "funnel_ring_%d" % k, v3(0, ps.FUNNEL_TOP - 0.45, z), ps.FUNNEL_HALF + 0.1, 0.1, "brass")
        add_cube(funnels, "funnel_mouth_%d" % k, (0, ps.FUNNEL_TOP + 0.26, z), EYE, (2 * ps.FUNNEL_HALF, 0.02, 2 * ps.FUNNEL_HALF),
                 {"all": None, "+2": "soot"})
        beam(funnels, "steam_pipe_%d" % k, (ps.FUNNEL_HALF + 0.12, top, z + 0.3), (ps.FUNNEL_HALF + 0.12, ps.FUNNEL_TOP - 0.6, z + 0.3),
             0.12, "copper")

    # ---- two paddle wheels, one on each side (as on the reference picture), each with its axle,
    # bearings and the arched box over it. o = +1 on the port side, -1 on the starboard side.
    wz, wy, R = ps.WHEEL_Z, ps.WHEEL_Y, ps.WHEEL_R
    for o, sn in SIDES:
        xi, xo = o * ps.WHEEL_X0, o * ps.WHEEL_X1
        xm = (xi + xo) / 2
        wheel = Bone("paddle_wheel" if o < 0 else "paddle_wheel_port", origin=(xm, wy, wz), parent=root)
        nseg = 20
        for ring, x in (("in", xi + o * 0.1), ("out", xo - o * 0.1)):
            for k in range(nseg):
                a0, a1 = 2 * math.pi * k / nseg, 2 * math.pi * (k + 1) / nseg
                p0 = v3(x, wy + R * math.cos(a0), wz + R * math.sin(a0))
                p1 = v3(x, wy + R * math.cos(a1), wz + R * math.sin(a1))
                beam(wheel, "rim_%s_%s_%d" % (sn, ring, k), p0, p1, 0.16, "iron", width=0.14, up=v3(1, 0, 0), extend=0.04)
                q0 = v3(x, wy + 1.15 * math.cos(a0), wz + 1.15 * math.sin(a0))
                q1 = v3(x, wy + 1.15 * math.cos(a1), wz + 1.15 * math.sin(a1))
                beam(wheel, "ring_%s_%s_%d" % (sn, ring, k), q0, q1, 0.1, "iron", width=0.1, up=v3(1, 0, 0), extend=0.03)
            for k in range(10):
                a = 2 * math.pi * (k + 0.5) / 10
                d = v3(0, math.cos(a), math.sin(a))
                beam(wheel, "spoke_%s_%s_%d" % (sn, ring, k), v3(x, wy, wz) + d * 0.3, v3(x, wy, wz) + d * (R - 0.05), 0.14, "wood",
                     width=0.12, up=v3(1, 0, 0))
        for k in range(10):
            a = 2 * math.pi * (k + 0.5) / 10
            d = v3(0, math.cos(a), math.sin(a))
            c = v3(xm, wy, wz) + d * (R - 0.32)
            tang = v3(0, -math.sin(a), math.cos(a))
            axes = np.column_stack([v3(1, 0, 0), d, tang])
            add_cube(wheel, "paddle_%s_%d" % (sn, k), c, axes, (abs(xo - xi) + 0.05, 0.7, 0.1),
                     {"all": "paddle", "+1": "iron", "-1": "iron"})
        add_cube(wheel, "hub_a_" + sn, (xm, wy, wz), EYE, (abs(xo - xi) + 0.5, 0.62, 0.62), "brass")
        add_cube(wheel, "hub_b_" + sn, (xm, wy, wz), rx(math.pi / 4), (abs(xo - xi) + 0.5, 0.62, 0.62), "brass")
        # fixed axle from the hull side to the outer bearing, the bearing and its brackets
        bx = o * ps.BOX_X1
        hx = o * (outer_x(wz, wy) - 0.1)
        beam(box, "axle_" + sn, (hx, wy, wz), (bx + o * 0.05, wy, wz), 0.26, "gunmetal")
        add_cube(box, "bearing_out_" + sn, (bx - o * 0.05, wy, wz), EYE, (0.22, 0.6, 0.6), "brass")
        add_cube(box, "bearing_in_" + sn, (hx + o * 0.15, wy, wz), EYE, (0.3, 0.6, 0.6), "brass")
        for s_ in (1, -1):
            beam(box, "bearing_strut_%s%d" % (sn, s_ > 0), (bx - o * 0.05, wy + 0.25, wz),
                 (bx - o * 0.05, wy + R * 0.82, wz + s_ * R * 0.55), 0.14, "iron", width=0.12)
        # the arched box: plates over the top of the wheel, open towards the outside below the arch
        na = 12
        rr = R + 0.32
        for k in range(na):
            a0 = math.radians(-78 + 156 * k / na)
            a1 = math.radians(-78 + 156 * (k + 1) / na)
            p0 = v3(0, wy + rr * math.cos(a0), wz + rr * math.sin(a0))
            p1 = v3(0, wy + rr * math.cos(a1), wz + rr * math.sin(a1))
            c = (p0 + p1) / 2
            x0, x1 = o * (outer_x(c[2], 2.0) - 0.05), bx
            L = np.linalg.norm(p1 - p0)
            t = norm(p1 - p0)
            nrm = norm(v3(0, c[1] - wy, c[2] - wz))
            axes = np.column_stack([v3(1, 0, 0), t, nrm])
            add_cube(box, "box_cover_%s%d" % (sn, k), v3((x0 + x1) / 2, c[1], c[2]), axes, (abs(x1 - x0), L + 0.04, 0.12),
                     {"all": "plate", "-3": "plate_inner"})
            # brass arch along the outer edge
            beam(box, "box_arch_%s%d" % (sn, k), v3(x1 + o * 0.05, p0[1], p0[2]), v3(x1 + o * 0.05, p1[1], p1[2]), 0.12, "brass",
                 width=0.34, up=v3(1, 0, 0), extend=0.05)
        for k in range(5):
            a = math.radians(-60 + 30 * k)
            d = v3(0, math.cos(a), math.sin(a))
            beam(box, "box_rib_%s%d" % (sn, k), v3(bx - o * 0.02, wy, wz) + d * 1.25, v3(bx - o * 0.02, wy, wz) + d * (rr - 0.1), 0.1,
                 "iron", width=0.08, up=v3(1, 0, 0))
        for s_ in (1, -1):
            z = wz + s_ * rr * math.sin(math.radians(78))
            beam(box, "box_sponson_%s%d" % (sn, s_ > 0), (o * (outer_x(z, wy) - 0.05), wy + 0.3, z), (bx, wy + 0.3, z), 0.2, "gunmetal",
                 width=0.2)
            beam(box, "box_strut_%s%d" % (sn, s_ > 0), (bx - o * 0.1, wy + 0.3, z), (o * (outer_x(z, -0.3) - 0.05), -0.4, z), 0.16, "iron")
        add_cube(box, "box_name_plate_" + sn, (bx + o * 0.02, wy + rr - 0.25, wz), EYE, (0.04, 0.3, 1.4), "brass")

    # ---- railing round the deck: iron posts and bars, lanterns on some posts
    stations = np.arange(ps.DECK_MIN_Z - 0.3, ps.DECK_MAX_Z + 0.21, 0.85)
    post_top = ps.RAIL_BASE
    for side, sn in SIDES:
        pts = []
        for k, z in enumerate(stations):
            x = side * (outer_x(z, ps.PLATING_TOP) - 0.12)
            p = v3(x, ps.PLATING_TOP, z)
            pts.append(p)
            beam(rail, "post_%s%d" % (sn, k), p, p + v3(0, post_top - ps.PLATING_TOP + 0.05, 0), 0.08, "iron")
        for j, y in enumerate((ps.PLATING_TOP + 0.4, post_top)):
            for k in range(len(pts) - 1):
                a, b = pts[k] + v3(0, y - ps.PLATING_TOP, 0), pts[k + 1] + v3(0, y - ps.PLATING_TOP, 0)
                beam(rail, "bar_%s%d_%d" % (sn, j, k), a, b, 0.07 if j == 0 else 0.09, "iron" if j == 0 else "brass", extend=0.03)
        for k, z in enumerate((-8.6, -5.2, -1.9, 4.6, 7.4)):
            x = side * (outer_x(z, ps.PLATING_TOP) - 0.12)
            base = v3(x, post_top + 0.05, z)
            beam(lanterns, "lamp_post_%s%d" % (sn, k), base, base + v3(0, 0.45, 0), 0.08, "brass")
            lamp(lanterns, "lamp_%s%d" % (sn, k), base + v3(0, 0.66, 0), s=1.15)
    # end rails across the bow and the stern
    for zz, tag in ((ps.DECK_MAX_Z + 0.2, "bow"), (ps.DECK_MIN_Z - 0.3, "stern")):
        w = outer_x(zz, ps.PLATING_TOP) - 0.15
        for j, y in enumerate((ps.PLATING_TOP + 0.4, post_top)):
            beam(rail, "end_bar_%s_%d" % (tag, j), (-w, y, zz), (w, y, zz), 0.08, "brass" if j else "iron")
        for k, x in enumerate(np.linspace(-w, w, 5)):
            beam(rail, "end_post_%s_%d" % (tag, k), (x, ps.PLATING_TOP, zz), (x, post_top + 0.05, zz), 0.08, "iron")

    # ---- guns fore and aft
    gun(guns, "gun_fore", ps.GUN_FORE_Z, 1)
    gun(guns, "gun_aft", ps.GUN_AFT_Z, -1)

    # ---- helm: brass wheel on its pedestal and the engine telegraph
    hub = v3(0, main_y + 1.1, ps.HELM_Z)
    add_cube(deck, "helm_pedestal", (0, main_y + 0.5, ps.HELM_Z + 0.1), EYE, (0.3, 1.0, 0.3), "gunmetal")
    hw_ = Bone("helm_wheel", origin=tuple(hub), parent=deck)
    add_cube(hw_, "helm_hub", hub, EYE, (0.2, 0.2, 0.2), "brass")
    for k in range(8):
        a = 2 * math.pi * k / 8
        d = v3(math.cos(a), math.sin(a), 0)
        beam(hw_, "helm_spoke_%d" % k, hub, hub + d * 0.62, 0.06, "brass", up=v3(0, 0, 1))
        a2 = 2 * math.pi * (k + 1) / 8
        beam(hw_, "helm_rim_%d" % k, hub + d * 0.48, hub + v3(math.cos(a2), math.sin(a2), 0) * 0.48, 0.07, "dark_wood", width=0.08,
             up=v3(0, 0, 1), extend=0.03)
    add_cube(deck, "telegraph_post", (0.9, main_y + 0.5, ps.HELM_Z - 0.3), EYE, (0.18, 1.0, 0.18), "brass")
    add_cube(deck, "telegraph_head", (0.9, main_y + 1.1, ps.HELM_Z - 0.3), EYE, (0.34, 0.34, 0.2), {"all": "brass", "+3": "gauge",
                                                                                                    "-3": "gauge"})

    # ---- signal mast aft with its yard and flag
    mz = ps.MAST_Z
    beam(deck, "mast", (0, main_y, mz), (0, ps.MAST_TOP, mz), 0.2, "gunmetal")
    beam(deck, "mast_yard", (-1.2, ps.MAST_TOP - 1.6, mz), (1.2, ps.MAST_TOP - 1.6, mz), 0.1, "gunmetal")
    lamp(lanterns, "mast_lamp", (0, ps.MAST_TOP - 1.2, mz + 0.2))
    fb = Bone("flag", origin=(0, ps.MAST_TOP - 0.1, mz), parent=deck)
    root_pt = v3(0, ps.MAST_TOP - 0.05, mz)
    w, h = 1.6, 0.8
    c1 = add_cube(fb, "flag_a", root_pt + v3(0, -h / 2, -w / 4), EYE, (0.03, h, w / 2), {"all": None, "+1": "flag", "-1": "flag"},
                  stretch=True, u_dir=v3(0, 0, -1), v_dir=v3(0, -1, 0))
    tip_root = root_pt + v3(0, 0, -w / 2)
    ft = Bone("flag_tip", origin=tuple(tip_root), parent=fb)
    c2 = add_cube(ft, "flag_b", tip_root + v3(0, -h / 2, -w / 4), EYE, (0.03, h, w / 2), {"all": None, "+1": "flag", "-1": "flag"},
                  stretch=True, u_dir=v3(0, 0, -1), v_dir=v3(0, -1, 0))
    gn.set_sub(c1, (0, 0, 0.5, 1), faces=("west", "east"))
    gn.set_sub(c2, (0.5, 0, 1, 1), faces=("west", "east"))
    for side in (1, -1):
        beam(ropes, "mast_stay_%d" % (side > 0), (0, ps.MAST_TOP - 1.5, mz), (side * 2.6, ps.RAIL_BASE, mz + 1.2), 0.04, "rope")
    beam(ropes, "mast_backstay", (0, ps.MAST_TOP - 1.5, mz), (0, ps.RAIL_BASE, ps.DECK_MIN_Z - 0.5), 0.04, "rope")
    beam(ropes, "funnel_stay_0", (0, ps.FUNNEL_TOP - 1.2, ps.FUNNEL_Z[1]), (0, top + 1.4, ps.HOUSE_Z1 - 0.3), 0.05, "iron")
    for side in (1, -1):
        for k, z in enumerate(ps.FUNNEL_Z):
            beam(ropes, "funnel_guy_%d_%d" % (k, side > 0), (side * 0.5, ps.FUNNEL_TOP - 1.0, z),
                 (side * (hh + 0.1), top + 0.2, z + (0.6 if k else -0.6)), 0.04, "iron")
    return root


def build_animations(root):
    kf, rot_kf, animation, find = gg.kf, gg.rot_kf, gg.animation, gg.find
    anims = []
    # one turn per loop, both wheels together; sign checked by verify_wheel_direction (ahead: the
    # lowest paddles push aft)
    anims.append(animation("paddle", 2.0, "loop", [(find(root, name), [
        rot_kf(t, (WHEEL_SIGN * a, 0, 0)) for t, a in ((0.0, 0), (0.5, 90), (1.0, 180), (1.5, 270), (2.0, 360))])
        for name in ("paddle_wheel", "paddle_wheel_port")]))
    hwb, rudder = find(root, "helm_wheel"), find(root, "rudder")
    anims.append(animation("steer", 2.0, "hold", [
        (hwb, [rot_kf(0.0, (0, 0, -140)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 0, 140))]),
        (rudder, [rot_kf(0.0, (0, -30, 0)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 30, 0))])]))
    f, ft = find(root, "flag"), find(root, "flag_tip")
    anims.append(animation("flag_wave", 1.2, "loop", [
        (f, [rot_kf(0, (0, 10, 0), "catmullrom"), rot_kf(0.6, (0, -10, 0), "catmullrom"), rot_kf(1.2, (0, 10, 0), "catmullrom")]),
        (ft, [rot_kf(0, (0, -18, 0), "catmullrom"), rot_kf(0.6, (0, 18, 0), "catmullrom"), rot_kf(1.2, (0, -18, 0), "catmullrom")])]))
    return anims


WHEEL_SIGN = -1


def verify_wheel_direction():
    """Ahead (animation time increasing) the lowest point of the wheel must move aft (-z)."""
    low = gg.M @ v3(0, -ps.WHEEL_R, 0)
    R = gg.euler_zyx_matrix((WHEEL_SIGN * 10, 0, 0))
    moved = gg.M @ (R @ low)
    assert moved[2] < -0.1, ("paddle wheel turns the wrong way", moved)


def main():
    verify_wheel_direction()
    root = build()
    anims = build_animations(root)
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    tex_path = os.path.join(tex_dir, "entity/steam_paddleboat.png")
    pt.make_texture(tex_path)
    pt.make_item_icon(os.path.join(tex_dir, "item/steam_paddleboat.png"))
    with open(tex_path, "rb") as f:
        png = f.read()
    textures = [gn.texture_entry("steam_paddleboat.png", pt.SIZE, png, "entity", "steam_paddleboat.png")]
    textures[0]["id"] = "0"
    model = gn.export(root, anims, textures, [
        os.path.join(ROOT, "blockbench/steam_paddleboat.bbmodel"),
        os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/steam_paddleboat.bbmodel"),
    ], name="steam_paddleboat", visible_box=(28, 16, 0))
    print("cubes:", len(model["elements"]), "animations:", [a["name"] for a in model["animations"]])


if __name__ == "__main__":
    main()
