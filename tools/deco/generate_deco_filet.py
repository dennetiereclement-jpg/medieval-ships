"""Hanging net (deco_filet): two squared posts (thick rope bindings at the top, iron bands at the foot), a heavy sagging
rope between them with a slack fishing net (diamond rope mesh) hanging from it in a deep belly, knotted to the rope,
and red-and-white floats on strings (a big one near each post, a small one under the left one). About 5 blocks wide,
3.3 high. No light.
Run: python3 tools/deco/generate_deco_filet.py (writes the model, the JSON, the shared atlas and the icon).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decolib as dl  # noqa: E402

NAME = "deco_filet"
HALF = 2.35
D = 0.44


def build():
    dl.setup(NAME)
    root = dl.Bone(NAME)
    det = dl.Bone("detail", parent=root)
    left = dl.post(root, "post_l", (-HALF, 0, 0), 3.35, d=D, bindings=[2.98], bands=[0.36], detail=det, rings=4)
    right = dl.post(root, "post_r", (HALF, 0, 0), 3.05, d=D, bindings=[2.72], bands=[0.36], detail=det)
    p0 = left.at(2.94, (1, 0, 0)) + dl.v3(-0.06, 0, 0.07)
    p1 = right.at(2.7, (-1, 0, 0)) + dl.v3(0.06, 0, 0.07)
    line = dl.sag_rope(root, "rope", p0, p1, sag=0.42, segs=10, d=0.085)
    # knots where the net is lashed to the rope
    for k, t in enumerate((0.13, 0.36, 0.62, 0.88)):
        dl.knot(det, "knot_%d" % k, line.at(t), 0.13)

    # the net: deepest left of the middle, rising towards the right post
    def drop(s):
        return 1.55 * math.sin(math.pi * min(1.0, s * 1.08)) ** 0.9 * (1.0 - 0.25 * s) + 0.12
    dl.net(root, "net", line, 0.13, 0.95, 1.5, belly=0.16, nx=9, ny=3, drop_fn=drop, tile=(0.25, 0.25))
    # floats: a big one near each post on its own string, a small red one under the left one
    fl = dl.float_buoy(root, "float_l", line.at(0.07) + dl.Z * 0.03, r=0.19, h=0.56, string=0.92, detail=det)
    dl.float_buoy(root, "float_s", fl + dl.v3(0.3, -0.02, 0.06), r=0.12, h=0.32, region="float_small", string=0.3, detail=det)
    dl.float_buoy(root, "float_r", line.at(0.91) + dl.Z * 0.03, r=0.19, h=0.56, string=0.8, detail=det)
    return root


def icon(put):
    dl.icon_posts(put, xs=(1, 14), top=(2, 3))
    y_of = dl.icon_sag(put, 2, 13, 4, 2, c=(200, 176, 120))
    for x in range(3, 13):
        y0 = y_of(x) + 1
        depth = int(round(1 + 5 * math.sin(math.pi * (x - 3) / 10)))
        for y in range(y0, y0 + depth):
            if (x + y) % 2 == 0:
                put(x, y, (200, 176, 120))
    for x, y in ((3, 8), (12, 8)):
        put(x, y, (232, 226, 210))
        put(x, y + 1, (168, 40, 42))
        put(x, y + 2, (58, 74, 138))


if __name__ == "__main__":
    dl.export(build(), NAME, light=0, icon=icon)
