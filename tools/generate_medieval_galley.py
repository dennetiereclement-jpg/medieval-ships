#!/usr/bin/env python3
"""Generates the red medieval galley (medieval_galley) Blockbench model, its texture and animations.

Usage:  python3 tools/generate_medieval_galley.py

Outputs:
  blockbench/medieval_galley.bbmodel                                   (editable, texture embedded)
  src/main/resources/assets/medievalships/models/entity/medieval_galley.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/medieval_galley.png
  src/main/resources/assets/medievalships/textures/item/medieval_galley.png

Reference: long narrow red galley, crescent hull rising at both ends into red dragon heads,
round red shields with a white cross along the sides, twelve oars a side, one mast with a
big rectangular sail in red and white vertical stripes, red flag with a white cross.

Same conventions and helpers as tools/generate_galleon.py; shape and layout come from
tools/medieval_galley_shape.py, identical to the Java collision code.

Bones used by the mod (keep their names when editing in Blockbench):
  oar_l1..oar_l12, oar_r1..oar_r12 (row)   sail (sail_wind, sail_furl)   rudder (steer)
  flag, flag_tip (flag_wave)
"""
import math
import os
import sys
import uuid

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import generate_galleon as gn  # noqa: E402
import generate_galley as gg  # noqa: E402
import medieval_galley_shape as ms  # noqa: E402
import medieval_galley_texture as mt  # noqa: E402
import ship_details as sd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/medieval_galley/%d" % _uuid_counter[0]))


gg.new_uuid = new_uuid
gn.new_uuid = new_uuid
gn.gs = ms
gn.REGIONS = {k: (0,) + r for k, r in mt.REGIONS.items()}
gn.SIZE = mt.SIZE

v3, norm, Bone, add_cube, beam, board = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam, gg.board
rx, ry, rz = gg.rx, gg.ry, gg.rz
EYE = np.eye(3)
SIDES = ((1, "p"), (-1, "s"))
BRACE = math.radians(42)

END = 13.0  # the planking closes into the stem and stern posts here
STATIONS = [-END, -12.6, -12.0, -11.2, -10.2, -9.0, -7.5, -5.8, -4.0, -2.0, 0.0, 2.0, 4.0, 5.8, 7.5, 9.0, 10.2,
            11.2, 12.0, 12.6, END]
# planking above the turn of the bilge, as fractions of the height between y=0.3 and the
# sheer: the strakes sweep up with the crescent sheer
UPPER = [0.0, 0.3, 0.55, 0.78, 1.0]
STRAKES = ["hull_dark", "hull_dark", "hull_dark", "hull_dark",   # bottom (keel -> turn of the bilge)
           "hull_dark", "hull_red", "wale", "hull_red"]


def hw(z):
    return ms.half_width(z)


def sheer(z):
    return ms.sheer_y(z)


def upper_y(z, f):
    return 0.3 + (sheer(z) - 0.3) * f


def outer_x(z, y):
    """Outer surface of the side: the planking flares slightly out up to the gunwale."""
    w = hw(z)
    if y <= 0.3:
        return 0.97 * w
    f = min(1.0, (y - 0.3) / max(0.05, sheer(z) - 0.3))
    return w * (0.97 + 0.03 * f)


gn.outer_x = outer_x
gn.hw = hw


def section(z, side):
    w, yk = hw(z), ms.keel_y(z)
    pts = [(0.06, yk)]
    for fx, fy in ms.BOTTOM_SECTION[1:]:
        pts.append((fx * w, fy * yk))
    for f in UPPER:
        y = upper_y(z, f)
        pts.append((outer_x(z, y), y))
    return [v3(side * max(x, 0.06), y, z) for x, y in pts]


def dragon_tail(bone, tag, s):
    """Carved dragon tail at the stern (s=-1): the sternpost rises into a scaly tail that tapers,
    arches back over the ship and curls down, with a dorsal crest and a gold spade-shaped tip."""
    def P(y, z):
        return v3(0, y, s * z)
    curve = [P(ms.keel_y(END) - 0.05, END - 0.25), P(0.7, END + 0.3), P(2.0, END + 0.62), P(3.3, END + 0.72),
             P(4.5, END + 0.6), P(5.5, END + 0.25), P(6.2, END - 0.25), P(6.5, END - 0.85), P(6.3, END - 1.4),
             P(5.8, END - 1.75), P(5.25, END - 1.8)]
    widths = [0.5, 0.56, 0.6, 0.56, 0.5, 0.44, 0.38, 0.32, 0.27, 0.23, 0.2]
    for j in range(len(curve) - 1):
        reg = "hull_dark" if j < 2 else "dragon"
        beam(bone, "%s_seg_%d" % (tag, j), curve[j], curve[j + 1], widths[j], reg, width=widths[j] * 0.85, extend=0.1)
    beam(bone, tag + "_collar", P(1.6, END + 0.5), P(2.0, END + 0.6), 0.62, "gold", width=0.58)
    # gold rings along the tail
    for j in (3, 5, 7):
        a, b = curve[j], curve[j + 1]
        c = (a + b) / 2
        d = norm(b - a)
        beam(bone, "%s_ring_%d" % (tag, j), c - d * 0.06, c + d * 0.06, widths[j] + 0.1, "gold", width=widths[j] * 0.85 + 0.1)
    # dorsal crest on the outside of the curve (pointing away from the curl centre)
    centre = P(4.9, END - 0.6)
    for j in range(2, len(curve) - 2):
        a, b = curve[j], curve[j + 1]
        c = (a + b) / 2
        out = norm(c - centre)
        size = 0.42 - 0.03 * j
        beam(bone, "%s_crest_%d" % (tag, j), c + out * widths[j] * 0.4, c + out * (widths[j] * 0.4 + size),
             0.26 - 0.015 * j, "dragon_dark", width=0.06)
    # spade tip: a flat gold arrowhead continuing the last segment
    a, b = curve[-2], curve[-1]
    d = norm(b - a)
    tip = b + d * 0.75
    beam(bone, tag + "_tip_a", b, tip, 0.12, "gold", width=0.55)
    beam(bone, tag + "_tip_b", b + d * 0.2, b + d * 0.5, 0.14, "gold", width=0.8)
    beam(bone, tag + "_tip_c", tip - d * 0.1, tip + d * 0.25, 0.1, "gold", width=0.22)


def dragon(bone, tag, s):
    """Carved dragon post at one end (s=+1 bow, s=-1 stern): the stem curves up into a scaly
    neck with a dorsal crest, the head looks outwards with its jaws open."""
    def P(y, z):
        return v3(0, y, s * z)
    # stem (from the keel) then the neck, as a smooth curve of thick beams
    curve = [P(ms.keel_y(END) - 0.05, END - 0.25), P(0.7, END + 0.3), P(2.0, END + 0.62), P(3.3, END + 0.78),
             P(4.6, END + 0.74), P(5.8, END + 0.52), P(6.8, END + 0.25), P(7.5, END + 0.2)]
    widths = [0.5, 0.58, 0.66, 0.76, 0.82, 0.84, 0.8, 0.74]
    for j in range(len(curve) - 1):
        reg = "hull_dark" if j < 2 else "dragon"
        beam(bone, "%s_neck_%d" % (tag, j), curve[j], curve[j + 1], widths[j], reg, width=widths[j] * 0.85, extend=0.12)
    # gold band where the hull planking ends and the carving begins, belly scales
    beam(bone, tag + "_collar", P(1.6, END + 0.5), P(2.0, END + 0.6), 0.62, "gold", width=0.58)
    for j, (a, b) in enumerate(zip(curve[2:-1], curve[3:])):
        c = (a + b) / 2 + v3(0, 0, s * 0.27)
        beam(bone, "%s_belly_%d" % (tag, j), c - (b - a) * 0.35, c + (b - a) * 0.35, 0.12, "gold", width=0.4)
    # dorsal crest: spikes along the back of the neck
    for j in range(5):
        a = curve[2 + j]
        b = curve[3 + j]
        c = (a + b) / 2 + v3(0, 0, -s * 0.3)
        d = norm(b - a)
        back = v3(0, -d[2], d[1]) * (-s)  # perpendicular, pointing backwards
        if back[2] * s > 0:
            back = -back
        beam(bone, "%s_crest_%d" % (tag, j), c, c + back * 0.42 + v3(0, 0.12, 0), 0.32, "dragon_dark", width=0.06)
    # head: skull, snout, open lower jaw with teeth, eyes, horns, frills, nostrils
    hb = P(7.75, END + 0.4)
    head = Bone(tag + "_head", origin=tuple(hb), parent=bone)

    def hcube(b, name, c, R_, size, reg, **kw):
        """Head parts are drawn 1.45 times larger around the head pivot."""
        c = hb + (v3(*c) - hb) * 1.45
        return add_cube(b, name, c, R_, tuple(x * 1.45 for x in size), reg, **kw)

    def beam_h(b, name, a, c, th, reg, **kw):
        return beam(b, name, hb + (v3(*a) - hb) * 1.45, hb + (v3(*c) - hb) * 1.45, th * 1.45, reg, **kw)
    out = v3(0, 0, s)
    R = ry(0 if s > 0 else math.pi)
    hcube(head, tag + "_skull", hb + out * 0.25 + v3(0, 0.05, 0), R, (0.62, 0.56, 0.78), "dragon")
    hcube(head, tag + "_brow", hb + out * 0.32 + v3(0, 0.33, 0), R, (0.66, 0.12, 0.5), "dragon_dark")
    hcube(head, tag + "_snout", hb + out * 0.85 + v3(0, -0.02, 0), R, (0.46, 0.32, 0.66), "dragon")
    hcube(head, tag + "_snout_tip", hb + out * 1.2 + v3(0, 0.02, 0), R, (0.5, 0.3, 0.16), "dragon_dark")
    jaw = hb + out * 0.78 + v3(0, -0.36, 0)
    Rj = R @ rx(-0.35)
    hcube(head, tag + "_jaw", jaw, Rj, (0.42, 0.13, 0.78), "dragon_dark")
    for k, (x, dz) in enumerate(((0.16, 0.25), (-0.16, 0.25), (0.16, -0.05), (-0.16, -0.05), (0.08, 0.45), (-0.08, 0.45))):
        hcube(head, "%s_tooth_up_%d" % (tag, k), hb + out * (0.85 + dz) + v3(x, -0.22, 0), R, (0.06, 0.12, 0.06), "ivory")
        hcube(head, "%s_tooth_low_%d" % (tag, k), jaw + Rj @ v3(x, 0.1, 0.2 - dz * 0.6), Rj, (0.06, 0.11, 0.06), "ivory")
    for x in (0.32, -0.32):
        hcube(head, "%s_eye_%d" % (tag, x > 0), hb + out * 0.38 + v3(x, 0.15, 0), R, (0.03, 0.17, 0.2),
                 {"all": "eye"}, stretch=True)
        hcube(head, "%s_nostril_%d" % (tag, x > 0), hb + out * 1.24 + v3(x * 0.45, 0.13, 0), R, (0.08, 0.06, 0.04), "gold")
        horn0 = hb + out * 0.05 + v3(x * 0.7, 0.3, 0)
        beam_h(head, "%s_horn_a_%d" % (tag, x > 0), horn0, horn0 + v3(x * 0.25, 0.42, -s * 0.45), 0.1, "gold")
        beam_h(head, "%s_horn_b_%d" % (tag, x > 0), horn0 + v3(x * 0.25, 0.42, -s * 0.45), horn0 + v3(x * 0.3, 0.55, -s * 0.85),
               0.07, "gold")
        # frill (ear fin) behind the jaw
        hcube(head, "%s_frill_%d" % (tag, x > 0), hb + out * (-0.05) + v3(x * 1.05, -0.05, 0), R @ ry(x * 0.5) @ rz(-x * 0.5),
                 (0.05, 0.42, 0.42), "dragon_dark")
    # tongue
    hcube(head, tag + "_tongue", jaw + Rj @ v3(0, 0.08, 0.15), Rj, (0.16, 0.04, 0.5), "red_paint")
    # gold crest along the top of the skull, sweeping back into the neck crest
    for k in range(4):
        base = hb + out * (0.5 - 0.28 * k) + v3(0, 0.36 - 0.05 * k, 0)
        tip = base + v3(0, 0.3 - 0.03 * k, -s * (0.22 + 0.04 * k))
        beam_h(head, "%s_crown_%d" % (tag, k), base, tip, 0.05, "gold", width=0.07)
    # whiskers: thin gold barbels curling down and back from the snout
    for x in (0.26, -0.26):
        w0 = hb + out * 1.1 + v3(x, -0.05, 0)
        w1 = w0 + v3(x * 0.85, -0.18, s * 0.05)
        beam_h(head, "%s_whisker_a_%d" % (tag, x > 0), w0, w1, 0.04, "gold")
        beam_h(head, "%s_whisker_b_%d" % (tag, x > 0), w1, w1 + v3(x * 0.3, -0.3, -s * 0.06), 0.035, "gold")
    # gold cheek plate under the eye
    for x in (0.31, -0.31):
        hcube(head, "%s_cheek_%d" % (tag, x > 0), hb + out * 0.55 + v3(x, -0.12, 0), R, (0.04, 0.14, 0.42), "gold")


def build():
    root = Bone("medieval_galley")
    hull = Bone("hull", parent=root)
    deck = Bone("deck", parent=root)
    bow = Bone("bow", parent=root)
    stern = Bone("stern", parent=root)
    shields = Bone("shields", parent=root)
    ropes = Bone("ropes", parent=root)
    lanterns = Bone("lanterns", parent=root)
    main_y = ms.MAIN_DECK_Y

    # ---- hull planking: tilted boards between rounded sections, crescent strakes
    for side, sn in SIDES:
        for i in range(len(STATIONS) - 1):
            za, zb = STATIONS[i], STATIONS[i + 1]
            A, B = section(za, side), section(zb, side)
            for k, reg in enumerate(STRAKES):
                mid = (A[k] + A[k + 1] + B[k] + B[k + 1]) / 4
                outward = norm(v3(side, -0.7 if k < 4 else 0.0, 0) + v3(0, 0, 0.35 * np.sign(mid[2])))
                board(hull, "hull_%s%d_%d" % (sn, i, k), A[k], A[k + 1], B[k], B[k + 1], 0.1, reg, outward,
                      inner="hull_light" if k >= 6 else None)
            # gunwale (red cap), blue trim under it, gold mouldings between the strakes
            pa, pb = v3(side * hw(za), sheer(za) + 0.05, za), v3(side * hw(zb), sheer(zb) + 0.05, zb)
            beam(hull, "gunwale_%s%d" % (sn, i), pa, pb, 0.12, "red_paint", width=0.24, extend=0.04)
            for j, (f, reg, th) in enumerate(((0.9, "blue_trim", 0.13), (0.78, "gold", 0.05), (0.55, "gold", 0.05),
                                              (0.3, "blue_trim", 0.09))):
                ya, yb = upper_y(za, f), upper_y(zb, f)
                pa, pb = v3(side * (outer_x(za, ya) + 0.03), ya, za), v3(side * (outer_x(zb, yb) + 0.03), yb, zb)
                beam(hull, "band_%s%d_%d" % (sn, i, j), pa, pb, th, reg, width=0.05, extend=0.04)
    for i in range(len(STATIONS) - 1):
        za, zb = STATIONS[i], STATIONS[i + 1]
        beam(hull, "keel_%d" % i, (0, ms.keel_y(za) - 0.05, za), (0, ms.keel_y(zb) - 0.05, zb), 0.2, "hull_dark",
             width=0.26, extend=0.05)

    # ---- dragon posts at both ends
    dragon(bow, "dragon_bow", 1)
    dragon_tail(Bone("dragon_tail", parent=stern), "dragon_tail", -1)

    # ---- deck, rowing benches, mast step, barrels and ropes
    n = 32
    for j in range(n):
        za = ms.DECK_MIN_Z + (ms.DECK_MAX_Z - ms.DECK_MIN_Z) * j / n
        zb = ms.DECK_MIN_Z + (ms.DECK_MAX_Z - ms.DECK_MIN_Z) * (j + 1) / n
        w = min(ms.inner_half_width(za), ms.inner_half_width(zb)) + 0.1
        add_cube(deck, "deck_%d" % j, (0, main_y - 0.06, (za + zb) / 2), EYE, (2 * w, 0.12, zb - za + 0.02),
                 {"all": "deck", "-2": "dark_wood"})
    for k, z in enumerate(ms.OAR_Z):
        zb_ = z - 0.5
        if abs(zb_ - ms.MAST_Z) < 0.7:
            continue
        w = ms.inner_half_width(zb_) - 0.02
        add_cube(deck, "bench_%d" % k, (0, main_y + 0.4, zb_), EYE, (2 * w, 0.09, 0.36), {"all": "dark_wood", "+2": "hull_light"})
        for x in (0.0,):
            add_cube(deck, "bench_leg_%d" % k, (x, main_y + 0.18, zb_), EYE, (0.16, 0.36, 0.16), "dark_wood")
    # centre walkway (gangway) and the stern platform of the helmsman
    add_cube(deck, "gangway", (0, main_y + 0.03, 0), EYE, (0.7, 0.06, 2 * ms.DECK_MAX_Z - 1.0), {"all": "dark_wood", "+2": "deck"})
    for k, (x, z) in enumerate(((0.9, -10.0), (-0.95, 9.8), (0.95, 9.6))):
        sd.barrel(gg, deck, "barrel_%d" % k, (x, main_y, z), h=0.6, r=0.22, wood="dark_wood", ends="end_grain")
    sd.rope_coil(gg, deck, "coil_0", (-0.8, main_y, -9.6), r=0.28)
    sd.rope_coil(gg, deck, "coil_1", (0.0, main_y, 10.4), r=0.26)
    add_cube(deck, "chest", (0.0, main_y + 0.2, -9.3), EYE, (0.8, 0.4, 0.5), {"all": "red_paint", "+2": "gold"})
    add_cube(deck, "helm_stool", (0, main_y + 0.22, ms.PILOT_Z), EYE, (0.5, 0.1, 0.45), "dark_wood")
    add_cube(deck, "helm_stool_leg", (0, main_y + 0.09, ms.PILOT_Z), EYE, (0.16, 0.18, 0.16), "dark_wood")

    # ---- round shields along the sides, hung on the gunwale
    for side, sn in SIDES:
        for k, z in enumerate(ms.SHIELD_Z):
            y = sheer(z) - 0.2
            p, u, v, nrm = gn.side_frame(z, y, side)
            add_cube(shields, "shield_%s%d" % (sn, k), p + nrm * 0.05, np.column_stack([u, v, nrm]), (1.22, 1.22, 0.05),
                     {"all": None, "+3": "shield", "-3": "dark_wood"}, stretch=True, u_dir=u * side, v_dir=v3(0, -1, 0))

    # ---- oars: 12 per side, each its own bone pivoting at its oar port under the shields
    down = math.radians(21)
    for side, sn in SIDES:
        sname = "l" if side > 0 else "r"
        group = Bone("oars_" + ("left" if side > 0 else "right"), parent=root)
        for i, z in enumerate(ms.OAR_Z):
            y = main_y + 0.3
            pivot = v3(side * (outer_x(z, y) + 0.02), y, z)
            ob = Bone("oar_%s%d" % (sname, i + 1), origin=tuple(pivot), parent=group)
            d = v3(side * math.cos(down), -math.sin(down), 0)
            beam(ob, "oar_shaft_%s%d" % (sname, i + 1), pivot - d * 1.25, pivot + d * 3.3, 0.12, "oar")
            beam(ob, "oar_blade_%s%d" % (sname, i + 1), pivot + d * 3.0, pivot + d * 4.05, 0.06, "oar", width=0.42, up=v3(0, 0, 1))
            add_cube(ob, "oar_port_%s%d" % (sname, i + 1), pivot, EYE, (0.06, 0.24, 0.24), "dark_wood")

    # ---- mast, yard and the striped square sail (braced), mast head flag
    mz = ms.MAST_Z
    mast = Bone("mast", origin=(0, main_y, mz), parent=root)
    beam(mast, "mast", (0, main_y - 0.2, mz), (0, ms.MAST_TOP, mz), 0.34, "mast")
    add_cube(mast, "mast_partners", (0, main_y + 0.1, mz), EYE, (0.7, 0.2, 0.7), "dark_wood")
    add_cube(mast, "mast_cap", (0, ms.MAST_TOP - 0.1, mz), EYE, (0.44, 0.22, 0.44), "gold")
    add_cube(mast, "mast_block", (0, ms.YARD_Y + 0.5, mz + 0.1), EYE, (0.4, 0.4, 0.42), "dark_wood")
    br = Bone("brace_yard", origin=(0, ms.YARD_Y, mz), parent=mast)
    yh = ms.YARD_HALF
    beam(br, "yard", (-yh, ms.YARD_Y, mz + 0.3), (yh, ms.YARD_Y, mz + 0.3), 0.2, "mast", extend=0.08)
    for x in (-yh - 0.08, yh + 0.08):
        add_cube(br, "yard_tip_%d" % (x > 0), (x, ms.YARD_Y, mz + 0.3), EYE, (0.14, 0.24, 0.24), "gold")
    beam(br, "yard_roll", (-yh * 0.95, ms.YARD_Y - 0.18, mz + 0.34), (yh * 0.95, ms.YARD_Y - 0.18, mz + 0.34), 0.2, "cloth_roll")
    sail_bone = Bone("sail", origin=(0, ms.YARD_Y, mz + 0.34), parent=br)
    sail_h = 8.0
    gn.sail(sail_bone, "sail", v3(0, ms.YARD_Y - 0.1, mz + 0.36), v3(1, 0, 0), v3(0, -1, 0), v3(0, 0, 1), yh - 0.2, yh,
            sail_h, 1.55, "sail", nx=9, ny=9, round_=0.75, overlap=0.03, foot=0.07)
    br.rot = ry(BRACE)
    fb = Bone("flag", origin=(0, ms.MAST_TOP + 0.85, mz), parent=mast)
    beam(mast, "flagpole", (0, ms.MAST_TOP, mz), (0, ms.MAST_TOP + 1.1, mz), 0.08, "dark_wood")
    root_pt = v3(0, ms.MAST_TOP + 0.95, mz)
    w, h = 1.7, 0.85
    c1 = add_cube(fb, "flag_a", root_pt + v3(0, -h / 2, -w / 4), EYE, (0.03, h, w / 2), {"all": None, "+1": "flag", "-1": "flag"},
                  stretch=True, u_dir=v3(0, 0, -1), v_dir=v3(0, -1, 0))
    tip_root = root_pt + v3(0, 0, -w / 2)
    ft = Bone("flag_tip", origin=tuple(tip_root), parent=fb)
    c2 = add_cube(ft, "flag_b", tip_root + v3(0, -h / 2, -w / 4), EYE, (0.03, h, w / 2), {"all": None, "+1": "flag", "-1": "flag"},
                  stretch=True, u_dir=v3(0, 0, -1), v_dir=v3(0, -1, 0))
    gn.set_sub(c1, (0, 0, 0.5, 1), faces=("west", "east"))
    gn.set_sub(c2, (0.5, 0, 1, 1), faces=("west", "east"))

    # ---- steering oar on the starboard quarter (bone "rudder" turns with "steer")
    sz = ms.STEER_Z
    pivot = v3(-(hw(sz) + 0.12), sheer(sz) - 0.25, sz)
    rb = Bone("rudder", origin=tuple(pivot), parent=root)
    blade_top = pivot + v3(-0.15, -1.9, -1.1)
    blade_bot = pivot + v3(-0.2, -2.9, -1.7)
    beam(rb, "rudder_shaft", pivot + v3(0, 0.45, 0.3), blade_top, 0.16, "oar", extend=0.05)
    beam(rb, "rudder_blade", blade_top, blade_bot, 0.08, "hull_red", width=0.55, up=v3(1, 0, 0))
    beam(rb, "rudder_tiller", pivot + v3(0, 0.35, 0.2), v3(-0.25, main_y + 0.85, ms.PILOT_Z + 0.25), 0.08, "dark_wood")
    add_cube(stern, "rudder_boss", pivot + v3(0.06, 0, 0), EYE, (0.2, 0.34, 0.34), "dark_wood")

    # ---- lantern posts on the gunwale, near both ends
    for k, (x, z) in enumerate(((1, -8.6), (-1, -8.6), (1, 8.6), (-1, 8.6))):
        base = v3(x * (hw(z) - 0.02), sheer(z) + 0.05, z)
        beam(lanterns, "lantern_post_%d" % k, base, base + v3(0, 0.9, 0), 0.1, "red_paint")
        beam(lanterns, "lantern_arm_%d" % k, base + v3(0, 0.85, 0), base + v3(x * 0.25, 0.85, 0), 0.06, "iron")
        add_cube(lanterns, "lantern_%d" % k, base + v3(x * 0.25, 0.62, 0), EYE, (0.26, 0.36, 0.26),
                 {"all": "lantern", "+2": "iron", "-2": "iron"}, stretch=True)
        add_cube(lanterns, "glow_lantern_%d" % k, base + v3(x * 0.25, 0.62, 0), EYE, (0.17, 0.26, 0.17), "glow", stretch=True)

    # ---- rigging
    top = v3(0, ms.MAST_TOP - 0.4, mz)
    rig = []
    for side, sn in SIDES:
        for k, z in enumerate((-0.6, -2.2)):
            rig.append(("shroud_%s%d" % (sn, k), top, v3(side * hw(z), sheer(z) + 0.05, z)))
        rig.append(("brace_" + sn, gn.braced((side * yh, ms.YARD_Y, mz + 0.3), mz), v3(side * hw(-7.0), sheer(-7.0), -7.0)))
        rig.append(("sheet_" + sn, gn.braced((side * yh, ms.YARD_Y - sail_h + 0.5, mz + 1.1), mz),
                    v3(side * hw(-3.5), sheer(-3.5), -3.5)))
    rig += [
        ("forestay", top + v3(0, 0.2, 0), v3(0, 3.0, END + 0.6)),
        ("backstay", top + v3(0, 0.2, 0), v3(0, 3.0, -END - 0.6)),
        ("halyard", v3(0.1, ms.MAST_TOP - 0.2, mz), v3(0.12, ms.YARD_Y + 0.3, mz + 0.2)),
    ]
    for name, a, b in rig:
        beam(ropes, "rope_" + name, a, b, 0.05, "rope")
    return root


def build_animations(root):
    kf, rot_kf, animation, find = gg.kf, gg.rot_kf, gg.animation, gg.find
    anims = []
    cycle = [(0.0, 22, 0), (0.9, -22, 0), (1.1, -24, 11), (1.8, 20, 11), (2.0, 22, 0)]
    tracks = []
    for side, prefix in ((1, "oar_l"), (-1, "oar_r")):
        for i in range(len(ms.OAR_Z)):
            b = find(root, "%s%d" % (prefix, i + 1))
            kfs = []
            for t, sweep, lift in cycle:
                be, ga = gg.oar_euler(side, sweep, lift)
                kfs.append(rot_kf(t, (0, be, ga)))
            tracks.append((b, kfs))
    anims.append(animation("row", 2.0, "loop", tracks))
    sail = find(root, "sail")
    anims.append(animation("sail_wind", 3.6, "loop", [(sail, [
        kf("scale", 0.0, (1, 1, 1.0), "catmullrom"), kf("scale", 0.9, (1, 1, 1.14), "catmullrom"),
        kf("scale", 1.8, (1, 1, 0.92), "catmullrom"), kf("scale", 2.7, (1, 1, 1.08), "catmullrom"),
        kf("scale", 3.6, (1, 1, 1.0), "catmullrom"),
        rot_kf(0.0, (0, 0, 0), "catmullrom"), rot_kf(1.2, (-1.4, 0, 0), "catmullrom"),
        rot_kf(2.4, (0.8, 0, 0), "catmullrom"), rot_kf(3.6, (0, 0, 0), "catmullrom")])]))
    anims.append(animation("sail_furl", 1.0, "hold", [(sail, [kf("scale", 0.0, (1, 1, 1)), kf("scale", 1.0, (0.95, 0, 0))])]))
    rudder = find(root, "rudder")
    anims.append(animation("steer", 2.0, "hold", [
        (rudder, [rot_kf(0.0, (0, -25, 0)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 25, 0))])]))
    f, ft = find(root, "flag"), find(root, "flag_tip")
    anims.append(animation("flag_wave", 1.2, "loop", [
        (f, [rot_kf(0, (0, 10, 0), "catmullrom"), rot_kf(0.6, (0, -10, 0), "catmullrom"), rot_kf(1.2, (0, 10, 0), "catmullrom")]),
        (ft, [rot_kf(0, (0, -18, 0), "catmullrom"), rot_kf(0.6, (0, 18, 0), "catmullrom"), rot_kf(1.2, (0, -18, 0), "catmullrom")])]))
    return anims


def main():
    root = build()
    anims = build_animations(root)
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    tex_path = os.path.join(tex_dir, "entity/medieval_galley.png")
    mt.make_texture(tex_path)
    mt.make_item_icon(os.path.join(tex_dir, "item/medieval_galley.png"))
    with open(tex_path, "rb") as f:
        png = f.read()
    textures = [gn.texture_entry("medieval_galley.png", mt.SIZE, png, "entity", "medieval_galley.png")]
    textures[0]["id"] = "0"
    model = gn.export(root, anims, textures, [
        os.path.join(ROOT, "blockbench/medieval_galley.bbmodel"),
        os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/medieval_galley.bbmodel"),
    ], name="medieval_galley", visible_box=(32, 20, 0))
    print("cubes:", len(model["elements"]), "animations:", [a["name"] for a in model["animations"]])


if __name__ == "__main__":
    main()
