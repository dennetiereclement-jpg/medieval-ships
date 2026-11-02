"""Red drapery (deco_draperie): two tall squared posts (golden rope bindings at the top, iron bands at the foot) holding a
red cloth with small gold dots and gold dagged edges, hung in a deep swag between the post tops (two layers: a deeper
one behind, a shallower one in front), its two ends falling down beside the posts. About 4.6 blocks wide, 3.6 high.
Run: python3 tools/deco/generate_deco_draperie.py (writes the model, the JSON, the shared atlas and the icon).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decolib as dl  # noqa: E402

NAME = "deco_draperie"
HALF = 2.2
D = 0.42
TOP_L, TOP_R = 3.62, 3.42


def build():
    dl.setup(NAME)
    root = dl.Bone(NAME)
    det = dl.Bone("detail", parent=root)
    # the cloth is tied under golden rope bindings near the top of each post (the post's top stands above them)
    yl, yr = TOP_L - 0.4, TOP_R - 0.4
    left = dl.post(root, "post_l", (-HALF, 0, 0), TOP_L, d=D, bindings=[yl + 0.02], bands=[0.36], detail=det)
    right = dl.post(root, "post_r", (HALF, 0, 0), TOP_R, d=D, bindings=[yr + 0.02], bands=[0.36], detail=det)
    a = dl.v3(-HALF + D * 0.5, yl, D / 2 + 0.02)
    b = dl.v3(HALF - D * 0.5, yr, D / 2 + 0.02)
    # the back layer: the deeper swag, its gold edge the lowest (about 2 above the ground in the middle)
    dl.swag(root, "swag_back", a + dl.v3(0, -0.04, -0.05), b + dl.v3(0, -0.04, -0.05), 0.55, 1.3, "drape_swag", top_sag=0.12,
            bulge=0.3, folds=0.025, nx=10, ny=2)
    # the front layer: a shallower swag over it, bellying out more
    dl.swag(root, "swag_front", a + dl.v3(0, 0.02, 0.02), b + dl.v3(0, 0.02, 0.02), 0.2, 0.92, "drape_swag", top_sag=0.14,
            bulge=0.42, folds=0.025, nx=10, ny=2)
    # the two ends hanging down beside the posts (in front of their inner faces), gathered at the top
    dl.tail(root, "tail_l", a + dl.v3(0.2, -0.02, 0.1), 0.58, 1.68, "drape_tail", out=(0.25, 0, 1), gather=0.4, folds=0.07)
    dl.tail(root, "tail_r", b + dl.v3(-0.2, -0.02, 0.1), 0.58, 1.52, "drape_tail", out=(-0.25, 0, 1), gather=0.4, folds=0.07)
    # the gathered corners: a bunched knot of cloth in front of each binding
    for k, (p, s) in enumerate(((a, 1), (b, -1))):
        dl.add_cube(root, "gather_%d" % k, p + dl.v3(-s * 0.08, 0.0, 0.08), dl.ry(0.3 * s) @ dl.rz(0.5 * s), (0.22, 0.3, 0.16),
                    "drape_red")
    return root


def icon(put):
    dl.icon_posts(put, xs=(1, 14), top=(1, 2))
    red, dark, gold = (164, 40, 42), (94, 20, 20), (217, 169, 58)
    for x in range(2, 14):
        t = (x - 2) / 11
        depth = int(round(2 + 4 * (1 - (2 * t - 1) ** 2)))
        for y in range(2, 2 + depth):
            put(x, y, red if y < 1 + depth else dark)
        put(x, 2 + depth, gold)
    for x0 in (2, 12):
        for y in range(2, 10):
            put(x0, y, red)
            put(x0 + 1, y, dark if y % 3 == 0 else red)
        put(x0, 10, gold)
        put(x0 + 1, 10, gold)


if __name__ == "__main__":
    dl.export(build(), NAME, light=0, icon=icon)
