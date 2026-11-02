"""Shade sails (deco_ombrage, 1.20.0): four squared posts (rope bindings where the sails are tied, stone footings
under the back ones) holding two large beige cloth sails, tilted opposite ways so that they cross when seen from the
front (the upper one rising to the right, the lower one falling to the right), sagging in the middle and along their
edges, tied by short ropes at their corners; a loose rope end hangs from the lower sail. An open shelter for
markets: ~5 x 4, 3.75 high. The posts collide; the sails do not and stay above head height (>= 1.9)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decolib as dl  # noqa: E402
import props_d2 as pd  # noqa: E402

NAME = "deco_ombrage"
HX, HZ, D = 2.3, 1.75, 0.36
INSET = 0.26          # the sail corners stand this far in from the posts' axes (x and z)
# post: (x, z, height, footing, (tie height of the upper sail, tie height of the lower sail), extra binding)
POSTS = {
    "fl": (-HX, HZ, 3.2, None, (2.82, 2.62), 1.95),
    "fr": (HX, HZ, 3.86, None, (3.5, 2.1), None),
    "bl": (-HX, -HZ, 3.05, (0.52, 0.4), (2.7, 2.42), None),
    "br": (HX, -HZ, 3.42, (0.52, 0.4), (3.06, 2.06), None),
}


def corner(key, which):
    x, z, _, _, ties, _ = POSTS[key]
    return dl.v3(x - (INSET if x > 0 else -INSET), ties[which] - 0.06, z - (INSET if z > 0 else -INSET))


def build(root, det):
    posts = {}
    for key, (x, z, h, foot, ties, extra) in POSTS.items():
        heights = list(ties) if abs(ties[0] - ties[1]) > 0.3 else [(ties[0] + ties[1]) / 2]
        if extra:
            heights.append(extra)
        posts[key] = dl.post(root, "post_" + key, (x, 0, z), h, d=D, bindings=heights, footing=foot, detail=det, rings=4,
                             ring_h=0.085)
    sails = {}
    for which, (name, sag, edge) in enumerate((("sail_upper", 0.44, 0.13), ("sail_lower", 0.36, 0.12))):
        c = {k: corner(k, which) for k in POSTS}
        sails[name] = pd.shade_sail(root, name, c["fl"], c["fr"], c["bl"], c["br"], sag=sag, edge_sag=edge, nx=6, ny=5)
        for k in POSTS:
            x, z, _, _, ties, _ = POSTS[k]
            out = dl.norm(dl.v3(c[k][0] - x, 0, c[k][2] - z))
            a = dl.v3(x, ties[which] - 0.02, z) + out * (D / 2 + 0.05)
            pd.tie_rope(det, "%s_tie_%s" % (name, k), a, c[k], sag=0.03, segs=2, detail=det)
            # the rope round the post's outer side
            dl.knot(det, "%s_knot_%s" % (name, k), dl.v3(x, ties[which] - 0.02, z) - out * (D / 2 + 0.06), s=0.11)
    # the loose rope end hanging from the lower sail's front edge (the tassel in the picture) and a rope from the
    # lower sail's middle back to the back right post
    P = sails["sail_lower"]
    tip = P(0.62, 0.0)
    dl.sag_rope(det, "tassel", tip, tip - dl.UP * 0.32 + dl.v3(0.03, 0, 0.02), sag=0.0, segs=1, d=0.045)
    dl.knot(det, "tassel_knot", tip - dl.UP * 0.05, s=0.1)
    dl.knot(det, "tassel_end", tip - dl.UP * 0.33, s=0.08)
    return posts


def draw_icon(put):
    wood, dark, cloth, cloth_d, rope = (122, 82, 50), (70, 46, 26), (232, 220, 190), (196, 180, 144), (216, 192, 142)
    for x, top in ((1, 5), (14, 2), (11, 6)):
        for y in range(top, 16):
            put(x, y, wood if y % 4 else dark)
    for x in range(2, 14):
        t = (x - 2) / 11.0
        y0 = int(round(6 - 3 * t + 1.6 * (1 - (2 * t - 1) ** 2)))
        for y in range(y0, y0 + 2):
            put(x, y, cloth)
        y1 = int(round(7 + 3 * t + 1.4 * (1 - (2 * t - 1) ** 2)))
        put(x, y1, cloth_d)
        put(x, y1 + 1, cloth)
    put(1, 6, rope)
    put(14, 3, rope)
    put(14, 10, rope)
    put(1, 7, rope)


if __name__ == "__main__":
    dl.setup(NAME)
    root = dl.Bone(NAME)
    det = dl.Bone("detail", parent=root)
    build(root, det)
    dl.export(root, NAME, light=0, icon=draw_icon)
