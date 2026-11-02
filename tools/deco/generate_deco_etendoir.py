"""Clothesline (deco_etendoir): two squared posts (rope bindings near the top, thick rope wraps at the feet), a sagging
rope between them with clothes pegs holding four pieces of laundry: a white sheet, a blue tunic with white stripes, a
worn beige cloth with a torn hem, a brick-red cloth. About 5 blocks wide, 3.3 high. No light.
Run: python3 tools/deco/generate_deco_etendoir.py (writes the model, the JSON, the shared atlas and the icon).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decolib as dl  # noqa: E402

NAME = "deco_etendoir"
HALF = 2.35
D = 0.38
# (region, start t, end t, length below the rope, sway, taper, pegs)
LAUNDRY = [
    ("sheet_white", 0.09, 0.30, 1.55, 0.05, 0.02, 2),
    ("tunic_stripes", 0.32, 0.50, 1.75, 0.04, 0.0, 2),
    ("cloth_worn", 0.53, 0.70, 1.05, 0.05, 0.04, 2),
    ("cloth_red_worn", 0.73, 0.92, 1.4, 0.06, 0.02, 2),
]


def build():
    dl.setup(NAME)
    root = dl.Bone(NAME)
    det = dl.Bone("detail", parent=root)
    left = dl.post(root, "post_l", (-HALF, 0, 0), 3.35, d=D, bindings=[3.0, 2.78], bands=[], detail=det)
    right = dl.post(root, "post_r", (HALF, 0, 0), 3.0, d=D, bindings=[2.72], bands=[], detail=det)
    # thick rope wraps at the feet (the posts are lashed to their footing)
    dl.binding(root, "foot_wrap_l", left.at(0.32), D, rings=4, ring_h=0.085, grow=0.075)
    dl.binding(root, "foot_wrap_r", right.at(0.36), D, rings=3, ring_h=0.085, grow=0.075)
    p0 = left.at(2.78, (1, 0, 0)) + dl.v3(-0.05, 0, 0.05)
    p1 = right.at(2.7, (-1, 0, 0)) + dl.v3(0.05, 0, 0.05)
    line = dl.sag_rope(root, "rope", p0, p1, sag=0.3, segs=10, d=0.055)
    dl.knot(det, "knot_l", p0 + dl.v3(0.03, 0, 0), 0.1)
    dl.knot(det, "knot_r", p1 - dl.v3(0.03, 0, 0), 0.1)
    for k, (reg, a, b, length, sway, taper, pegs) in enumerate(LAUNDRY):
        A, B = line.at(a) - dl.UP * 0.035 + dl.Z * 0.03, line.at(b) - dl.UP * 0.035 + dl.Z * 0.03
        dl.clothes(root, "laundry_%d" % k, A, B, length, reg, pegs=pegs, detail=det, sway=sway, taper=taper,
                   peg_region="wood_dark", peg_h=0.26, nx=3, ny=1)
    # one spare peg left on the rope near the right post
    p = line.at(0.96)
    dl.add_cube(det, "spare_peg", p + dl.UP * 0.07 + dl.Z * 0.02, dl.frame(dl.UP + dl.X * 0.15, dl.Z), (0.24, 0.07, 0.06),
                {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    return root


def icon(put):
    dl.icon_posts(put, xs=(1, 14), top=(2, 3))
    y_of = dl.icon_sag(put, 2, 13, 4, 1)
    pieces = [(3, 5, 7, (232, 226, 210)), (6, 7, 8, (74, 84, 144)), (9, 10, 5, (212, 192, 152)), (11, 12, 6, (162, 69, 58))]
    for x0, x1, h, c in pieces:
        for x in range(x0, x1 + 1):
            for y in range(y_of(x) + 1, y_of(x) + 1 + h):
                put(x, y, c if not (c[2] > 140 and c[0] < 100 and x == x0 + 1) else (216, 212, 200))
        put(x0, y_of(x0) - 1, (60, 42, 26))


if __name__ == "__main__":
    dl.export(build(), NAME, light=0, icon=icon)
