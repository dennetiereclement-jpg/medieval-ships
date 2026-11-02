"""Festive bunting (deco_guirlande): two squared posts (rope bindings at the top, iron bands at the foot), a sagging
rope between them with six dagged cloth pennants (red, yellow, blue, red, yellow, red) and a small lantern hanging on an
iron bracket on the inner face of each post (glow; the anchor block gives light 12). About 5 blocks wide, 3.3 high.
Run: python3 tools/deco/generate_deco_guirlande.py (writes the model, the JSON, the shared atlas and the icon).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decolib as dl  # noqa: E402

NAME = "deco_guirlande"
HALF = 2.3            # post axes at x = +-HALF
D = 0.36              # post section
COLOURS = ["pennant_red", "pennant_yellow", "pennant_blue", "pennant_red", "pennant_yellow", "pennant_red"]


def build():
    dl.setup(NAME)
    root = dl.Bone(NAME)
    det = dl.Bone("detail", parent=root)
    left = dl.post(root, "post_l", (-HALF, 0, 0), 3.3, d=D, bindings=[3.08], bands=[0.34], detail=det)
    right = dl.post(root, "post_r", (HALF, 0, 0), 3.15, d=D, bindings=[2.92], bands=[0.34], detail=det)
    # the rope: from the binding of one post to the other's, sagging a little, a turn round each post
    p0 = left.at(3.06, (1, 0, 0)) + dl.v3(-0.05, 0, 0.06)
    p1 = right.at(2.9, (-1, 0, 0)) + dl.v3(0.05, 0, 0.06)
    line = dl.sag_rope(root, "rope", p0, p1, sag=0.32, segs=10, d=0.055)
    dl.knot(det, "knot_l", p0 + dl.v3(0.04, 0, 0), 0.1)
    dl.knot(det, "knot_r", p1 - dl.v3(0.04, 0, 0), 0.1)
    # six pennants evenly along the rope, each following the rope's slope, swinging a little out
    n = len(COLOURS)
    t0, t1, gap = 0.07, 0.93, 0.03
    step = (t1 - t0) / n
    for k, reg in enumerate(COLOURS):
        a, b = t0 + k * step + gap / 2, t0 + (k + 1) * step - gap / 2
        tilt = 0.05 if k % 2 else -0.03
        dl.pennant(root, "pennant_%d" % k, line.at(a) - dl.UP * 0.02 + dl.Z * 0.01, line.at(b) - dl.UP * 0.02 + dl.Z * 0.01,
                   0.98 - 0.08 * (k % 2), reg, tilt=tilt, flutter=0.04)
    # two small lanterns on iron brackets, on the inner faces of the posts
    dl.wall_lantern(root, "lantern_l", left, 2.02, side=(1, 0, 0.3), arm=0.3, size=0.42, drop=0.0, detail=det, metal="wood_dark")
    dl.wall_lantern(root, "lantern_r", right, 2.15, side=(-1, 0, 0.3), arm=0.3, size=0.42, drop=0.0, detail=det, metal="wood_dark")
    return root


def icon(put):
    dl.icon_posts(put, xs=(1, 14), top=(2, 3))
    y_of = dl.icon_sag(put, 2, 13, 3, 2)
    cols = [(164, 40, 42), (224, 170, 42), (58, 72, 168), (164, 40, 42), (224, 170, 42)]
    for k, c in enumerate(cols):
        x0 = 3 + k * 2
        for dx in range(2):
            y = y_of(x0 + dx) + 1
            for dy in range(3 if dx == 0 else 2):
                put(x0 + dx, y + dy, c)
    for x, y in ((3, 8), (12, 9)):
        put(x, y, (255, 214, 120))
        put(x, y + 1, (240, 170, 60))
        put(x, y - 1, (60, 60, 64))


if __name__ == "__main__":
    dl.export(build(), NAME, light=12, icon=icon)
