#!/usr/bin/env python3
"""Canon médiéval (canon_medieval, 1.16.0): an independent medieval cannon, one block (TentType group "artillery").

Reference: scratchpad/ref/canon_medieval_ref.png. A long black cast-iron barrel (16-sided, reinforcing rings, a thick
flared muzzle lip round a visible bore, a big base ring, a domed breech and a heavy cascabel knob, a lifting lug and
the vent on top) on its trunnions in a massive oak field carriage: two stepped cheeks bound with bolted iron straps,
iron capsquares over the trunnions, front, middle and trail transoms, the bed and the wooden quoin under the breech,
the trail resting on the ground; two big spoked wheels (8 spokes, 16 felloes, riveted iron tyres, banded hubs) on an
iron-armed axletree; a small pyramid of four cannonballs behind the left wheel, inside the footprint (no crates: it
must fit on ramparts and in forts).

Bones (for the future firing system, docs/TENTES.md): "carriage" (pivot on the axle: the whole gun recoils with it),
under it "barrel" (pivot = the trunnion axis: elevation, recoil), "wheel_left" and "wheel_right" (pivot = their hub:
they roll when the gun recoils; left / right as seen by the gunner behind the breech looking along the barrel),
"detail" (bolts, straps: hidden beyond tentDecorDistance); under the root "furniture" (the cannonballs).
The JSON's "muzzle" is the centre of the bore's mouth, "muzzle_dir" the barrel's axis towards the mouth.

Orientation: +z = the breech side, towards the player who placed it (FACING like every prop); the muzzle points to -z.

Usage:  python3 tools/merchant/generate_canon_medieval.py   (ARTILLERY_OUT=<file.bbmodel>: the model only, for previews)
Writes: blockbench/canon_medieval.bbmodel, models/entity/canon_medieval.bbmodel, textures/entity/canon_medieval.png,
        textures/item/canon_medieval.png, artillery/canon_medieval.json.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artillery as ar  # noqa: E402

cl, v3, add_cube, EYE, box = ar.cl, ar.v3, ar.add_cube, ar.EYE, ar.box

NAME = "canon_medieval"
ELEV = math.radians(5.0)          # the barrel's elevation (muzzle up)
Y_T, Z_T = 1.50, 0.20             # trunnion axis height and position
AXIS = v3(0, math.sin(ELEV), -math.cos(ELEV))   # unit, from the trunnions towards the muzzle
MOUTH = 2.05                      # trunnions -> muzzle face along the axis
BORE = 0.20
R_WHEEL, Z_A, X_W = 0.75, 0.10, 0.90   # wheel radius, axle z, wheel centre plane x
CHEEK_IN, CHEEK_OUT = 0.38, 0.68
# the cheek in four steps, front to trail: (z0, z1, bottom, top)
STEPS = [(-0.70, 0.42, 0.28, 1.40), (0.42, 0.98, 0.22, 1.18), (0.98, 1.50, 0.12, 0.98), (1.50, 1.90, 0.0, 0.70)]

# the barrel from the muzzle face (u = 0) to the end of the cascabel: (u0, u1, r0, r1, region, stave thickness)
PROFILE = [
    (0.00, 0.14, 0.400, 0.400, "ring", 0.400 - BORE),     # muzzle lip
    (0.14, 0.30, 0.362, 0.312, None, 0.362 - BORE),       # flared mouth
    (0.30, 0.85, 0.300, 0.310, None, None),               # chase
    (0.85, 0.93, 0.345, 0.345, "ring", None),             # chase girdle
    (0.93, 1.55, 0.320, 0.335, None, None),
    (1.55, 1.65, 0.372, 0.372, "ring", None),             # second reinforce ring
    (1.65, 2.35, 0.355, 0.370, None, None),               # second reinforce (trunnions at u = 2.05)
    (2.35, 2.46, 0.412, 0.412, "ring", None),             # first reinforce ring
    (2.46, 3.00, 0.395, 0.405, None, None),               # first reinforce (vent field)
    (3.00, 3.15, 0.442, 0.442, "ring", None),             # base ring
    (3.15, 3.23, 0.410, 0.370, None, None),               # breech dome
    (3.23, 3.31, 0.370, 0.270, None, 0.270),
    (3.31, 3.37, 0.270, 0.150, None, 0.150),
    (3.37, 3.43, 0.130, 0.130, "iron", 0.130),            # neck
]
KNOB = [(3.43, 3.52, 0.220, 0.262, "ring", 0.262), (3.52, 3.66, 0.262, 0.262, "ring", 0.262), (3.66, 3.72, 0.262, 0.180, "ring", 0.180)]
U_END = 3.72


def at(u):
    """The barrel axis point at u (from the muzzle face towards the breech)."""
    return v3(0, Y_T, Z_T) + AXIS * (MOUTH - u)


def build_barrel(barrel):
    mouth = at(0.0)
    n = ar.lathe(barrel, "barrel", mouth, -AXIS, PROFILE, n=16, th=0.13)
    n += ar.lathe(barrel, "cascabel", mouth, -AXIS, KNOB, n=8, th=0.2, phase=0.0)
    ar.disc(barrel, "cascabel_end", at(U_END) - AXIS * 0.005, AXIS, 0.17, 0.02, "ring", n=8)
    # a dark plug deep in the bore (the bore never shows the sky through the barrel)
    ar.disc(barrel, "bore_back", at(1.2), AXIS, BORE + 0.01, 0.02, "bore", n=8)
    # trunnions (round bars across through the barrel) with their end faces
    for s in (1, -1):
        ar.cylinder_x(barrel, "trunnion_%d" % ((s + 1) // 2), s * 0.30, s * (CHEEK_OUT + 0.045), Y_T, Z_T, 0.11, "ring", n=8, cap="iron")
    # lifting lug on top at the trunnions, the vent (touch hole) pad near the breech
    up = np.cross(AXIS, v3(1, 0, 0))   # perpendicular to the barrel, upwards
    up = up if up[1] > 0 else -up
    R = np.column_stack([v3(1, 0, 0), up, -AXIS])
    add_cube(barrel, "lug", at(2.05) + up * 0.41, R, (0.14, 0.13, 0.30), "ring")
    add_cube(barrel, "lug_top", at(2.05) + up * 0.49, R, (0.18, 0.05, 0.22), "ring")
    add_cube(barrel, "vent_pad", at(2.85) + up * 0.405, R, (0.15, 0.03, 0.15), "ring")
    add_cube(barrel, "vent_hole", at(2.85) + up * 0.415, R, (0.05, 0.02, 0.05), "bore")


def cheek(car, det, s):
    """One stepped cheek (s = +1 right, -1 left) with its straps, brackets and bolts."""
    x0, x1 = (CHEEK_IN, CHEEK_OUT) if s > 0 else (-CHEEK_OUT, -CHEEK_IN)
    xo = x1 if s > 0 else x0                  # the outer face
    steps = STEPS
    for k, (z0, z1, y0, y1) in enumerate(steps):
        box(car, "cheek_%d_%d" % (s, k), (x0, y0, z0), (x1, y1, z1), {"all": "plank", "+2": "wood", "-3": "plank_end", "+3": "plank_end"})
    # trunnion notch: the capsquare (an iron band over the trunnion, bolted down at both ends)
    zc = Z_T
    box(det, "capsquare_top_%d" % s, (x0 - 0.01, Y_T + 0.10, zc - 0.13), (x1 + 0.01, Y_T + 0.15, zc + 0.13), "iron")
    for e in (-1, 1):
        box(det, "capsquare_side_%d_%d" % (s, e), (x0 - 0.01, 1.38, zc + e * 0.13 - 0.025), (x1 + 0.01, Y_T + 0.15, zc + e * 0.13 + 0.025), "iron")
    # vertical straps round the outer face and over the top, at regular stations
    for k, (zs, step) in enumerate(((-0.62, 0), (-0.22, 0), (0.62, 1), (0.88, 1), (1.12, 2), (1.42, 2), (1.80, 3))):
        z0, z1, y0, y1 = steps[step]
        box(det, "strap_%d_%d" % (s, k), (xo - 0.018, y0 - 0.005, zs - 0.045), (xo + 0.018, y1 + 0.02, zs + 0.045),
            {"all": "iron", "-1": "strap", "+1": "strap"}, stretch=True)
        box(det, "strap_top_%d_%d" % (s, k), (x0 - 0.005, y1, zs - 0.045), (x1 + 0.005, y1 + 0.02, zs + 0.045), "iron")
    # long horizontal band along the bottom of the front block, iron corner brackets on the front face
    box(det, "band_%d" % s, (xo - 0.02, 0.36, -0.70), (xo + 0.02, 0.44, 0.42), {"all": "iron", "-1": "strap_h", "+1": "strap_h"}, stretch=True)
    for k, (yy0, yy1) in enumerate(((0.28, 0.56), (1.12, 1.40))):
        box(det, "bracket_%d_%d" % (s, k), (x0 - 0.01, yy0, -0.72), (x1 + 0.01, yy1, -0.695), {"all": "iron", "+3": "strap", "-3": "strap"},
            stretch=True)
    # bolt heads on the outer face
    for k, (zb, yb) in enumerate(((-0.42, 1.18), (-0.42, 0.70), (0.05, 1.20), (0.05, 0.62), (0.75, 0.96), (0.75, 0.50), (1.27, 0.76),
                                  (1.27, 0.40), (1.70, 0.44))):
        add_cube(det, "bolt_%d_%d" % (s, k), (xo + 0.02 * (1 if s > 0 else -1), yb, zb), EYE, (0.05, 0.075, 0.075), "iron")


def build_carriage(car, det):
    for s in (1, -1):
        cheek(car, det, s)
    xi = CHEEK_IN + 0.005
    # transoms between the cheeks, the bed under the breech and the quoin
    box(car, "transom_front", (-xi, 0.30, -0.69), (xi, 1.16, -0.42), {"all": "plank", "+2": "wood", "-3": "plank", "+3": "plank"})
    box(car, "transom_mid", (-xi, 0.18, 0.98), (xi, 0.80, 1.24), "plank")
    box(car, "transom_trail", (-xi, 0.02, 1.56), (xi, 0.62, 1.86), "plank")
    box(car, "bed", (-xi, 0.80, 0.44), (xi, 0.88, 1.50), {"all": "wood", "+2": "plank"})
    yb = at(2.75)[1] - 0.40              # underside of the barrel over the quoin
    ar.beam(car, "quoin", (0, 0.88 + 0.02, 1.42), (0, yb - 0.005, 0.86), 0.18, {"all": "wood", "+1": "end_grain", "-1": "end_grain"},
            width=0.34)
    add_cube(car, "quoin_handle", (0, 0.97, 1.47), EYE, (0.08, 0.08, 0.12), "wood_dark")
    # the axletree (a squared beam across under the cheeks) and the axle's iron arms into the hubs
    box(car, "axletree", (-CHEEK_OUT - 0.02, 0.62, Z_A - 0.15), (CHEEK_OUT + 0.02, 0.90, Z_A + 0.15), {"all": "wood_dark", "+1": "end_grain",
                                                                                                         "-1": "end_grain"})
    cl.axle(car, "axle", -X_W - 0.2, X_W + 0.2, R_WHEEL, Z_A, d=0.13, region="iron")
    for s in (1, -1):
        box(det, "axle_band_%d" % s, (s * 0.5 - 0.04, 0.60, Z_A - 0.17), (s * 0.5 + 0.04, 0.92, Z_A + 0.17), "iron")
    # an iron eye bolt (breeching ring) on the trail transom
    add_cube(det, "trail_ring", (0, 0.36, 1.875), EYE, (0.16, 0.16, 0.03), {"all": "iron", "+3": "bore", "-3": "bore"})
    # the trail's iron shoe on the ground
    box(det, "trail_shoe", (-CHEEK_OUT - 0.01, 0.0, 1.84), (CHEEK_OUT + 0.01, 0.10, 1.92), {"all": "iron", "+3": "strap_h", "-3": "strap_h"},
        stretch=True)


def build_wheel(bone, s):
    c = (s * X_W, R_WHEEL, Z_A)
    cl.wheel(bone, "wheel", c, R_WHEEL, width=0.19, spokes=8, segs=16, felloe=0.17, hub_d=0.34, hub_len=0.36, spoke_d=0.1,
             region="wood_dark", spoke_region="wood", tyre="tyre", solid=False)
    # thin iron nave bands round the hub ends, the axle's end and its linchpin outside the cap
    for k, dx in enumerate((-0.14, 0.14)):
        ar.cylinder_x(bone, "nave_band_%d" % k, s * X_W + dx - 0.022, s * X_W + dx + 0.022, R_WHEEL, Z_A, 0.182, "iron", n=8)
    ar.cylinder_x(bone, "axle_end", s * (X_W + 0.19), s * (X_W + 0.25), R_WHEEL, Z_A, 0.075, "ring", n=8)
    add_cube(bone, "linchpin", (s * (X_W + 0.225), R_WHEEL + 0.1, Z_A), EYE, (0.03, 0.1, 0.03), "iron")


def build():
    root = ar.Bone(NAME)
    car = ar.Bone("carriage", origin=(0, R_WHEEL, Z_A), parent=root)
    barrel = ar.Bone("barrel", origin=(0, Y_T, Z_T), parent=car)
    wl = ar.Bone("wheel_left", origin=(-X_W, R_WHEEL, Z_A), parent=car)
    wr = ar.Bone("wheel_right", origin=(X_W, R_WHEEL, Z_A), parent=car)
    det = ar.Bone("detail", parent=car)
    furn = ar.Bone("furniture", parent=root)
    build_barrel(barrel)
    build_carriage(car, det)
    build_wheel(wl, -1)
    build_wheel(wr, 1)
    # four cannonballs piled on the ground under the muzzle's overhang (inside the footprint)
    ar.ball_pile(furn, "balls", (0.0, 0.0, -1.28), r=0.15)
    # collisions: the carriage (four steps), the barrel, the two wheels (the pile adds its own)
    for z0, z1, y0, y1 in STEPS:
        ar.collide((-CHEEK_OUT, 0.0, z0, CHEEK_OUT, y1, z1))
    ar.collide((-0.45, 1.02, -1.90, 0.45, 1.98, 1.90))
    for s in (1, -1):
        xa, xb = sorted((s * (X_W - 0.11), s * (X_W + 0.11)))
        ar.collide((xa, 0.0, Z_A - 0.6, xb, 1.42, Z_A + 0.6))
    return root


def icon(path):
    """16 x 16 item icon: the black barrel aiming up to the right over a wooden carriage and a spoked wheel."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    black, hi, ring = (40, 41, 47, 255), (92, 94, 104, 255), (70, 72, 80, 255)
    wood, wood_d, iron = (168, 116, 60, 255), (104, 68, 32, 255), (60, 60, 66, 255)
    # carriage
    for x in range(3, 12):
        for y in range(9, 12 if x < 9 else 13):
            p[x, y] = wood if (x + y) % 5 else wood_d
    for x in range(3, 12):
        p[x, 9] = wood_d
    # barrel: a thick line from (1, 9) to (14, 3)
    for k in range(0, 27):
        t = k / 26
        cx, cy = 1.5 + 12.5 * t, 8.6 - 5.6 * t
        r = 1.9 - 0.4 * t
        for x in range(16):
            for y in range(16):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                    p[x, y] = black
    for x, y in ((3, 7), (5, 6), (7, 5), (9, 4), (11, 3)):
        p[x, y] = hi
    for x, y in ((6, 7), (6, 8), (7, 7), (11, 4), (11, 5), (12, 4)):
        p[x, y] = ring
    p[14, 3] = p[14, 2] = ring
    p[15, 3] = (18, 18, 20, 255)
    p[14, 4] = ring
    # wheel: centre (6, 12), radius 3.5
    for x in range(16):
        for y in range(16):
            d = ((x + 0.5 - 6.5) ** 2 + (y + 0.5 - 12.0) ** 2) ** 0.5
            if 2.6 <= d <= 3.7:
                p[x, y] = iron if d > 3.25 else wood
            elif d < 2.6 and (x == 6 or y == 11 or x - y == -5 or x + y == 17):
                p[x, y] = wood_d
    p[6, 11] = iron
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)


def main():
    ar.setup(NAME)
    atlas = ar.Atlas(NAME)
    root = build()
    muzzle = at(0.0) + AXIS * 0.0
    ar.export(root, NAME, atlas, muzzle=tuple(muzzle), muzzle_dir=tuple(AXIS), icon=icon)


if __name__ == "__main__":
    main()
