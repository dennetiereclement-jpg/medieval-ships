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
# hull stations, closer together towards the ends where the crescent lines curve fast
STATIONS = [round(END * (0.4 * s + 0.6 * math.sin(math.pi / 2 * s)), 4) for s in np.linspace(-1, 1, 33)]
# planking above the turn of the bilge, as fractions of the height between y=0.3 and the
# sheer: the strakes sweep up with the crescent sheer
UPPER = [0.0, 0.3, 0.55, 0.78, 1.0]
SPAN_REGIONS = ["hull_dark", "hull_dark", "hull_dark", "hull_dark",   # bottom (keel -> turn of the bilge)
                "hull_dark", "hull_red", "wale", "hull_red"]
# each span of the section is cut into this many strakes: the bottom rounds smoothly into the sides
SECTION_SUB = [2, 2, 2, 2, 1, 1, 1, 1]
STRAKES = [reg for reg, n in zip(SPAN_REGIONS, SECTION_SUB) for _ in range(n)]
STRAKE_SPAN = [k for k, n in enumerate(SECTION_SUB) for _ in range(n)]


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


def _rbeam(bone, name, p0, p1, th, region, up=None, extend=0.0, **kw):
    """Round-looking spar: a square beam and the same beam turned 45 degrees about its axis (8 sides)."""
    p0, p1 = v3(*p0), v3(*p1)
    d = norm(p1 - p0)
    u0 = v3(0, 1, 0) if up is None else norm(np.asarray(up, dtype=float))
    if abs(np.dot(d, u0)) > 0.98:
        u0 = v3(1, 0, 0)
    w = norm(u0 - np.dot(u0, d) * d)
    u1 = norm(w + np.cross(d, w))
    beam(bone, name, p0, p1, th, region, up=w, extend=extend, **kw)
    reg = {"all": region, "+1": None, "-1": None} if isinstance(region, str) else dict(region, **{"+1": None, "-1": None})
    beam(bone, name + "_r", p0, p1, th, reg, up=u1, extend=extend, **kw)


def _octo(bone, name, c, R, size, region):
    """Octagonal block: a box and the same box turned 45 degrees about its own y axis."""
    add_cube(bone, name, c, R, size, region)
    reg = {"all": region, "+2": None, "-2": None} if isinstance(region, str) else dict(region, **{"+2": None, "-2": None})
    add_cube(bone, name + "_r", c, R @ ry(math.pi / 4), size, reg)


def _cbox(bone, name, c, R, size, region, ch):
    """Box with its four long edges (along its local z) chamfered by ch: two crossed boxes and four
    diamonds along the edges."""
    sx, sy, sz = size
    c = v3(*c)
    add_cube(bone, name, c, R, (sx, sy - 2 * ch, sz), region)
    add_cube(bone, name + "_x", c, R, (sx - 2 * ch, sy, sz), region)
    d = ch * math.sqrt(2)
    for k, (a, b) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        add_cube(bone, "%s_e%d" % (name, k), c + R @ v3(a * (sx / 2 - ch), b * (sy / 2 - ch), 0), R @ rz(math.pi / 4),
                 (d, d, sz), region)


def _post(bone, name, ctrl, widths, region_of, sub=3, extend=0.1, squash=0.85):
    """Round carved post (stem, neck, tail) along a smooth curve through the control points,
    tapering with the given widths."""
    pts = _smooth(ctrl, [sub] * (len(ctrl) - 1))
    ws = np.interp(np.linspace(0, len(ctrl) - 1, len(pts)), range(len(ctrl)), widths)
    for j in range(len(pts) - 1):
        w = (ws[j] + ws[j + 1]) / 2 * (1 + squash) / 2
        _rbeam(bone, "%s_%d" % (name, j), pts[j], pts[j + 1], w, region_of(j // sub), up=v3(1, 0, 0), extend=extend)
    return pts


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


# the stem and the sternpost rise from the keel and curve outwards (dragon neck and tail): the
# last strakes end inside them instead of in a flat cut, so no gap is left between the two
STEM_Y = [ms.keel_y(END) - 0.05, 0.7, 2.0, 3.3, 4.5]
STEM_DZ = [-0.25, 0.3, 0.62, 0.72, 0.6]


def end_z(z, y):
    """z of the hull end at height y (z = +-END marks the ends)."""
    if abs(z) < END - 1e-6:
        return z
    return math.copysign(END + float(np.interp(y, STEM_Y, STEM_DZ)), z)


def section(z, side):
    w, yk = hw(z), ms.keel_y(z)
    pts = [(0.06, yk)]
    for fx, fy in ms.BOTTOM_SECTION[1:]:
        pts.append((fx * w, fy * yk))
    for f in UPPER:
        y = upper_y(z, f)
        pts.append((outer_x(z, y), y))
    pts = _smooth(pts, SECTION_SUB)
    return [v3(side * max(x, 0.06), y, end_z(z, y)) for x, y in pts]


def dragon_tail(bone, tag, s):
    """Carved dragon tail at the stern (s=-1): the sternpost rises into a scaly tail that tapers,
    arches back over the ship and curls down, with a dorsal crest and a gold spade-shaped tip."""
    def P(y, z):
        return v3(0, y, s * z)
    curve = [P(ms.keel_y(END) - 0.05, END - 0.25), P(0.7, END + 0.3), P(2.0, END + 0.62), P(3.3, END + 0.72),
             P(4.5, END + 0.6), P(5.5, END + 0.25), P(6.2, END - 0.25), P(6.5, END - 0.85), P(6.3, END - 1.4),
             P(5.8, END - 1.75), P(5.25, END - 1.8)]
    widths = [0.5, 0.56, 0.6, 0.56, 0.5, 0.44, 0.38, 0.32, 0.27, 0.23, 0.2]
    _post(bone, tag + "_seg", curve, widths, lambda j: "hull_dark" if j < 2 else "dragon", sub=3, extend=0.08)
    _rbeam(bone, tag + "_collar", P(1.6, END + 0.5), P(2.0, END + 0.6), 0.64, "gold", up=v3(1, 0, 0))
    # gold rings along the tail
    for j in (3, 5, 7):
        a, b = curve[j], curve[j + 1]
        c = (a + b) / 2
        d = norm(b - a)
        _rbeam(bone, "%s_ring_%d" % (tag, j), c - d * 0.06, c + d * 0.06, widths[j] * 0.93 + 0.1, "gold", up=v3(1, 0, 0))
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
    # (a heart-shaped leaf: two lobes and a pointed diamond, with a raised midrib)
    ax_ = gg.frame_from(d, v3(1, 0, 0))   # x along the tail, y across the ship: the leaf lies in the plane of the curl
    side_ = ax_[:, 2]
    for k, sg in enumerate((1, -1)):
        add_cube(bone, "%s_tip_lobe_%d" % (tag, k), b + d * 0.3 + side_ * sg * 0.17, ax_ @ ry(math.pi / 4), (0.36, 0.1, 0.36), "gold")
    add_cube(bone, tag + "_tip_a", b + d * 0.5, ax_ @ ry(math.pi / 4), (0.5, 0.11, 0.5), "gold")
    beam(bone, tag + "_tip_c", b, tip + d * 0.08, 0.16, "gold", width=0.08, up=v3(1, 0, 0))


def dragon(bone, tag, s):
    """Carved dragon post at one end (s=+1 bow, s=-1 stern): the stem curves up into a scaly
    neck with a dorsal crest, the head looks outwards with its jaws open."""
    def P(y, z):
        return v3(0, y, s * z)
    # stem (from the keel) then the neck, as a smooth curve of thick beams
    curve = [P(ms.keel_y(END) - 0.05, END - 0.25), P(0.7, END + 0.3), P(2.0, END + 0.62), P(3.3, END + 0.78),
             P(4.6, END + 0.74), P(5.8, END + 0.52), P(6.8, END + 0.25), P(7.5, END + 0.2)]
    widths = [0.5, 0.58, 0.66, 0.76, 0.82, 0.84, 0.8, 0.74]
    _post(bone, tag + "_neck", curve, widths, lambda j: "hull_dark" if j < 2 else "dragon", sub=3, extend=0.1)
    # gold band where the hull planking ends and the carving begins, belly scales
    _rbeam(bone, tag + "_collar", P(1.6, END + 0.5), P(2.0, END + 0.6), 0.64, "gold", up=v3(1, 0, 0))
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
    # head: skull with brow ridges, tapering snout with fangs, lower jaw hinged under the skull,
    # glowing eyes, swept-back horns, a crest of spines and fins behind the jaw
    hb = P(7.75, END + 0.4)
    head = Bone(tag + "_head", origin=tuple(hb), parent=bone)
    K = 1.45  # the head is drawn 1.45 times larger around its pivot

    def at(off_out, y, x=0.0):
        return hb + (out * off_out + v3(x, y, 0)) * K

    def hcube(name, c, R_, size, reg, **kw):
        return add_cube(head, name, c, R_, tuple(q * K for q in size), reg, **kw)

    def hcbox(name, c, R_, size, reg, ch):
        return _cbox(head, name, c, R_, tuple(q * K for q in size), reg, ch * K)

    def hbeam(name, p0, p1, th, reg, **kw):
        if "width" in kw:
            kw["width"] = kw["width"] * K
        return beam(head, name, p0, p1, th * K, reg, **kw)
    out = v3(0, 0, s)
    R = ry(0 if s > 0 else math.pi)
    # skull and brow
    hcbox(tag + "_skull", at(0.18, 0.05), R, (0.66, 0.5, 0.72), "dragon", 0.1)
    hcube(tag + "_skull_back", at(-0.15, 0.0), R, (0.56, 0.42, 0.3), "dragon_dark")
    for x in (0.23, -0.23):
        hcube("%s_brow_%d" % (tag, x > 0), at(0.36, 0.33, x), R @ rz(-x * 0.9), (0.24, 0.12, 0.44), "dragon_dark")
    # upper snout, tapering, with a ridge, nostrils and fangs
    hcbox(tag + "_snout", at(0.72, 0.0), R @ rx(0.06), (0.52, 0.3, 0.6), "dragon", 0.07)
    hcbox(tag + "_snout_tip", at(1.1, -0.02), R @ rx(0.1), (0.44, 0.26, 0.26), "dragon", 0.07)
    hcube(tag + "_snout_ridge", at(0.8, 0.18), R @ rx(0.12), (0.18, 0.08, 0.62), "dragon_dark")
    for x in (0.12, -0.12):
        hcube("%s_nostril_%d" % (tag, x > 0), at(1.2, 0.08, x), R, (0.09, 0.06, 0.06), "dragon_dark")
    for k, (x, dz, ln) in enumerate(((0.2, 1.08, 0.2), (-0.2, 1.08, 0.2), (0.21, 0.88, 0.12), (-0.21, 0.88, 0.12),
                                     (0.22, 0.68, 0.1), (-0.22, 0.68, 0.1), (0.22, 0.5, 0.09), (-0.22, 0.5, 0.09))):
        hcube("%s_fang_up_%d" % (tag, k), at(dz, -0.17 - ln / 2, x), R, (0.06, ln, 0.06), "ivory")
    # lower jaw: hinged under the back of the skull, open by ~22 degrees
    a = 0.38
    hinge = at(0.0, -0.17)
    d = norm(out * math.cos(a) + v3(0, -math.sin(a), 0))
    Rj = R @ rx(a)
    jaw_c = hinge + d * 0.55 * K
    hcbox(tag + "_jaw", jaw_c, Rj, (0.44, 0.13, 1.05), "dragon_dark", 0.04)
    hcube(tag + "_jaw_chin", jaw_c + d * 0.45 * K + Rj @ v3(0, -0.04, 0) * K, Rj, (0.38, 0.15, 0.16), "dragon")
    hcube(tag + "_tongue", jaw_c + Rj @ v3(0, 0.08, 0.05) * K, Rj, (0.16, 0.04, 0.8), "red_paint")
    for k, (x, t) in enumerate(((0.17, 0.42), (-0.17, 0.42), (0.18, 0.2), (-0.18, 0.2), (0.18, -0.02), (-0.18, -0.02))):
        hcube("%s_fang_low_%d" % (tag, k), jaw_c + Rj @ v3(x, 0.12, t) * K, Rj, (0.06, 0.12, 0.06), "ivory")
    for x in (1, -1):
        hcbox("%s_cheek_%d" % (tag, x > 0), at(0.15, -0.06, x * 0.3), R, (0.12, 0.3, 0.42), "dragon", 0.04)
        hbeam("%s_eye_ridge_%d" % (tag, x > 0), at(0.58, 0.27, x * 0.29), at(0.1, 0.3, x * 0.32), 0.08, "dragon_dark", extend=0.02)
        hcube("%s_nostril_rim_%d" % (tag, x > 0), at(1.17, 0.07, x * 0.16), R @ rz(math.pi / 4), (0.1, 0.1, 0.12), "dragon_dark")
    # eyes: gold with a slit pupil, glowing at night
    for x in (0.335, -0.335):
        hcube("glow_%s_eye_%d" % (tag, x > 0), at(0.36, 0.17, x), R, (0.03, 0.17, 0.2), {"all": "eye"}, stretch=True)
    # horns: three tapering gold segments sweeping back and up
    for x in (1, -1):
        p0 = at(-0.05, 0.27, x * 0.22)
        p1 = p0 + (v3(x * 0.1, 0.2, 0) - out * 0.32) * K
        p2 = p1 + (v3(x * 0.05, 0.16, 0) - out * 0.32) * K
        p3 = p2 + (v3(x * 0.02, 0.02, 0) - out * 0.28) * K
        hbeam("%s_horn_a_%d" % (tag, x > 0), p0, p1, 0.13, "gold", extend=0.02)
        hbeam("%s_horn_b_%d" % (tag, x > 0), p1, p2, 0.1, "gold", extend=0.02)
        hbeam("%s_horn_c_%d" % (tag, x > 0), p2, p3, 0.06, "gold", extend=0.02)
        # fins behind the jaw: three thin spines fanning backwards
        for j, (dy, dx) in enumerate(((0.1, 0.32), (-0.05, 0.36), (-0.2, 0.3))):
            f0 = at(-0.02, dy, x * 0.3)
            f1 = f0 + (v3(x * dx, dy * 0.6, 0) - out * 0.3) * K
            hbeam("%s_fin_%d_%d" % (tag, x > 0, j), f0, f1, 0.05, "dragon_dark", width=0.14 - 0.03 * j)
    # crest: spines along the middle of the skull, continuing the one on the neck
    for k in range(3):
        c0 = at(0.45 - 0.25 * k, 0.3)
        hbeam("%s_spine_%d" % (tag, k), c0, c0 + (v3(0, 0.2 + 0.04 * k, 0) - out * 0.14) * K, 0.05, "dragon_dark",
              width=0.16)
    # short gold barbels under the chin
    for x in (0.1, -0.1):
        b0 = jaw_c + d * 0.5 * K + Rj @ v3(x, -0.09, 0) * K
        hbeam("%s_barbel_%d" % (tag, x > 0), b0, b0 + v3(x * 0.4, -0.28, 0) * K, 0.035, "gold")


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
                outward = norm(v3(mid[0], mid[1] - 0.7, 0.35 * np.sign(mid[2]) * abs(mid[0])))
                board(hull, "hull_%s%d_%d" % (sn, i, k), A[k], A[k + 1], B[k], B[k + 1], 0.1, reg, outward,
                      inner="hull_light" if STRAKE_SPAN[k] >= 6 else None)
            # gunwale (red cap with a rounded outer edge), blue trim under it, gold mouldings between the strakes
            pa = v3(side * hw(za), sheer(za) + 0.05, end_z(za, sheer(za)))
            pb = v3(side * hw(zb), sheer(zb) + 0.05, end_z(zb, sheer(zb)))
            beam(hull, "gunwale_%s%d" % (sn, i), pa, pb, 0.1, "red_paint", width=0.22, extend=0.04)
            o = v3(side * 0.1, -0.035, 0)
            beam(hull, "gunwale_bead_%s%d" % (sn, i), pa + o, pb + o, 0.11, "red_paint", width=0.11,
                 up=norm(v3(side, 1, 0)), extend=0.04)
            for j, (f, reg, th) in enumerate(((0.9, "blue_trim", 0.13), (0.78, "gold", 0.05), (0.55, "gold", 0.05),
                                              (0.3, "blue_trim", 0.09))):
                ya, yb = upper_y(za, f), upper_y(zb, f)
                pa = v3(side * (outer_x(za, ya) + 0.03), ya, end_z(za, ya))
                pb = v3(side * (outer_x(zb, yb) + 0.03), yb, end_z(zb, yb))
                beam(hull, "band_%s%d_%d" % (sn, i, j), pa, pb, th, reg, width=0.05 if reg == "gold" else 0.07,
                     up=v3(0, 1, 0) if reg == "gold" else norm(v3(side * 0.5, 1, 0)), extend=0.04)
    for i in range(len(STATIONS) - 1):
        za, zb = STATIONS[i], STATIONS[i + 1]
        beam(hull, "keel_%d" % i, (0, ms.keel_y(za) - 0.05, za), (0, ms.keel_y(zb) - 0.05, zb), 0.2, "hull_dark",
             width=0.26, extend=0.05)

    # ---- dragon posts at both ends
    dragon(bow, "dragon_bow", 1)
    dragon_tail(Bone("dragon_tail", parent=stern), "dragon_tail", -1)

    # ---- deck, rowing benches, mast step, barrels and ropes
    # the planking runs right into the stem and the sternpost (no hollow left at the ends)
    n, z0, z1 = 40, -END + 0.3, END - 0.3
    for j in range(n):
        za = z0 + (z1 - z0) * j / n
        zb = z0 + (z1 - z0) * (j + 1) / n
        w = min(ms.inner_half_width(za), ms.inner_half_width(zb)) + 0.1
        add_cube(deck, "deck_%d" % j, (0, main_y - 0.06, (za + zb) / 2), EYE, (2 * w, 0.12, zb - za + 0.02),
                 {"all": "deck", "-2": "dark_wood"})
    for k, z in enumerate(ms.OAR_Z):
        zb_ = z - 0.5
        if abs(zb_ - ms.MAST_Z) < 0.7:
            continue
        w = ms.inner_half_width(zb_) - 0.02
        add_cube(deck, "bench_%d" % k, (0, main_y + 0.4, zb_), EYE, (2 * w, 0.09, 0.3), {"all": "dark_wood", "+2": "hull_light"})
        for s_ in (1, -1):
            beam(deck, "bench_edge_%d_%d" % (k, s_ > 0), (-w + 0.04, main_y + 0.4, zb_ + s_ * 0.15), (w - 0.04, main_y + 0.4, zb_ + s_ * 0.15),
                 0.09, "dark_wood", width=0.09, up=norm(v3(0, 1, s_)))
        _rbeam(deck, "bench_leg_%d" % k, (0, main_y, zb_), (0, main_y + 0.36, zb_), 0.16, "dark_wood")
    # centre walkway (gangway) and the stern platform of the helmsman
    add_cube(deck, "gangway", (0, main_y + 0.03, 0), EYE, (0.7, 0.06, 2 * ms.DECK_MAX_Z - 1.0), {"all": "dark_wood", "+2": "deck"})
    for k, (x, z) in enumerate(((0.9, -10.0), (-0.95, 9.8), (0.95, 9.6))):
        sd.barrel(gg, deck, "barrel_%d" % k, (x, main_y, z), h=0.6, r=0.22, wood="dark_wood", ends="end_grain")
    sd.rope_coil(gg, deck, "coil_0", (-0.8, main_y, -9.6), r=0.28)
    sd.rope_coil(gg, deck, "coil_1", (0.0, main_y, 10.4), r=0.26)
    add_cube(deck, "chest", (0.0, main_y + 0.18, -9.3), EYE, (0.8, 0.36, 0.5), {"all": "red_paint", "+2": "gold"})
    _rbeam(deck, "chest_lid", (-0.4, main_y + 0.38, -9.3), (0.4, main_y + 0.38, -9.3), 0.34, {"all": "red_paint", "+2": "gold"})
    for x in (-0.25, 0.25):
        _rbeam(deck, "chest_band_%d" % (x > 0), (x - 0.03, main_y + 0.38, -9.3), (x + 0.03, main_y + 0.38, -9.3), 0.37, "gold")
    _octo(deck, "helm_stool", (0, main_y + 0.22, ms.PILOT_Z), EYE, (0.48, 0.1, 0.48), "dark_wood")
    _rbeam(deck, "helm_stool_leg", (0, main_y, ms.PILOT_Z), (0, main_y + 0.17, ms.PILOT_Z), 0.16, "dark_wood")

    # ---- round shields along the sides, hung on the gunwale
    for side, sn in SIDES:
        for k, z in enumerate(ms.SHIELD_Z):
            y = sheer(z) - 0.2
            p, u, v, nrm = gn.side_frame(z, y, side)
            add_cube(shields, "shield_%s%d" % (sn, k), p + nrm * 0.05, np.column_stack([u, v, nrm]), (1.22, 1.22, 0.05),
                     {"all": None, "+3": "shield", "-3": "dark_wood"}, stretch=True, u_dir=u * side, v_dir=v3(0, -1, 0))
            # gilded boss in the middle of the shield
            Rb = np.column_stack([u, nrm, np.cross(u, nrm)])
            _octo(shields, "shield_boss_%s%d" % (sn, k), p + nrm * 0.11, Rb, (0.26, 0.08, 0.26), "gold")
            _octo(shields, "shield_boss_top_%s%d" % (sn, k), p + nrm * 0.16, Rb, (0.14, 0.04, 0.14), "gold")
            # raised gilded rim round the edge of the shield
            nr = 10
            rr = 0.56
            for j in range(nr):
                a0, a1 = 2 * math.pi * j / nr, 2 * math.pi * (j + 1) / nr
                q0 = p + nrm * 0.1 + (u * math.cos(a0) + v * math.sin(a0)) * rr
                q1 = p + nrm * 0.1 + (u * math.cos(a1) + v * math.sin(a1)) * rr
                beam(shields, "shield_rim_%s%d_%d" % (sn, k, j), q0, q1, 0.07, "gold", width=0.05, up=nrm, extend=0.03)

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
            _rbeam(ob, "oar_shaft_%s%d" % (sname, i + 1), pivot - d * 1.25, pivot + d * 3.3, 0.12, "oar")
            # leaf-shaped blade: a neck tapering out of the loom, a pointed rounded tip
            ax_ = gg.frame_from(d, v3(0, 0, 1))
            add_cube(ob, "oar_blade_neck_%s%d" % (sname, i + 1), pivot + d * 3.1, ax_ @ ry(math.pi / 4), (0.3, 0.05, 0.3), "oar")
            beam(ob, "oar_blade_%s%d" % (sname, i + 1), pivot + d * 3.1, pivot + d * 4.0, 0.06, "oar", width=0.42, up=v3(0, 0, 1))
            add_cube(ob, "oar_blade_tip_%s%d" % (sname, i + 1), pivot + d * 4.0, ax_ @ ry(math.pi / 4), (0.42 / math.sqrt(2), 0.06,
                     0.42 / math.sqrt(2)), "oar")
            # round oar port
            _octo(ob, "oar_port_%s%d" % (sname, i + 1), pivot, rz(math.pi / 2), (0.24, 0.06, 0.24), "dark_wood")

    # ---- mast, yard and the striped square sail (braced), mast head flag
    mz = ms.MAST_Z
    mast = Bone("mast", origin=(0, main_y, mz), parent=root)
    _rbeam(mast, "mast", (0, main_y - 0.2, mz), (0, ms.MAST_TOP, mz), 0.34, "mast")
    _octo(mast, "mast_partners", (0, main_y + 0.1, mz), EYE, (0.7, 0.2, 0.7), "dark_wood")
    _octo(mast, "mast_cap", (0, ms.MAST_TOP - 0.1, mz), EYE, (0.44, 0.22, 0.44), "gold")
    _octo(mast, "mast_block", (0, ms.YARD_Y + 0.5, mz + 0.1), EYE, (0.4, 0.4, 0.42), "dark_wood")
    br = Bone("brace_yard", origin=(0, ms.YARD_Y, mz), parent=mast)
    yh = ms.YARD_HALF
    _rbeam(br, "yard", (-yh, ms.YARD_Y, mz + 0.3), (yh, ms.YARD_Y, mz + 0.3), 0.2, "mast", extend=0.08)
    for x in (-yh - 0.08, yh + 0.08):
        _octo(br, "yard_tip_%d" % (x > 0), (x, ms.YARD_Y, mz + 0.3), rz(math.pi / 2), (0.24, 0.14, 0.24), "gold")
    _rbeam(br, "yard_roll", (-yh * 0.95, ms.YARD_Y - 0.18, mz + 0.34), (yh * 0.95, ms.YARD_Y - 0.18, mz + 0.34), 0.2, "cloth_roll")
    sail_bone = Bone("sail", origin=(0, ms.YARD_Y, mz + 0.34), parent=br)
    sail_h = 8.0
    gn.sail(sail_bone, "sail", v3(0, ms.YARD_Y - 0.1, mz + 0.36), v3(1, 0, 0), v3(0, -1, 0), v3(0, 0, 1), yh - 0.2, yh,
            sail_h, 1.55, "sail", nx=9, ny=9, round_=0.75, overlap=0.03, foot=0.07)
    br.rot = ry(BRACE)
    fb = Bone("flag", origin=(0, ms.MAST_TOP + 0.85, mz), parent=mast)
    _rbeam(mast, "flagpole", (0, ms.MAST_TOP, mz), (0, ms.MAST_TOP + 1.1, mz), 0.08, "dark_wood")
    _octo(mast, "flagpole_knob", (0, ms.MAST_TOP + 1.14, mz), EYE, (0.13, 0.1, 0.13), "gold")
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
    _rbeam(rb, "rudder_shaft", pivot + v3(0, 0.45, 0.3), blade_top, 0.16, "oar", extend=0.05)
    beam(rb, "rudder_blade", blade_top, blade_bot, 0.08, "hull_red", width=0.55, up=v3(1, 0, 0))
    dd = norm(blade_bot - blade_top)
    beam(rb, "rudder_blade_tip", blade_bot, blade_bot + dd * 0.14, 0.08, "hull_red", width=0.36, up=v3(1, 0, 0))
    _rbeam(rb, "rudder_tiller", pivot + v3(0, 0.35, 0.2), v3(-0.25, main_y + 0.85, ms.PILOT_Z + 0.25), 0.08, "dark_wood")
    _octo(stern, "rudder_boss", pivot + v3(0.06, 0, 0), rz(math.pi / 2), (0.34, 0.2, 0.34), "dark_wood")

    # ---- lantern posts on the gunwale, near both ends
    for k, (x, z) in enumerate(((1, -8.6), (-1, -8.6), (1, 8.6), (-1, 8.6))):
        base = v3(x * (hw(z) - 0.02), sheer(z) + 0.05, z)
        _rbeam(lanterns, "lantern_post_%d" % k, base, base + v3(0, 0.9, 0), 0.1, "red_paint")
        _octo(lanterns, "lantern_post_knob_%d" % k, base + v3(0, 0.93, 0), EYE, (0.14, 0.08, 0.14), "gold")
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
