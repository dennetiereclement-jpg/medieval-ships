"""Herb drying rack (deco_sechoir, 1.20.0): two squared posts on stone footings, a long horizontal beam across their
tops (the left post standing above it) with an angled brace on the left and iron bolts, four bundles hanging on
ropes looped over the beam: big green herbs, lavender, sage-green sprigs, white flowers. ~4.6 wide, 4.1 high.
Posts and footings collide; the bundles and ropes do not (the passage under the beam stays free)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decolib as dl  # noqa: E402
import props_d2 as pd  # noqa: E402

NAME = "deco_sechoir"
PX, PD = 1.9, 0.46                     # posts at x = -PX / +PX, section PD
BEAM_Y0, BEAM_Y1, BEAM_D = 3.56, 3.92, 0.34
BUNDLES = [  # x, atlas region, length, width, rope length, yaw phase
    (-0.7, "herbs_green_big", 2.15, 1.42, 0.3, 0.0),
    (0.2, "herbs_lavender_big", 1.45, 1.02, 0.38, 0.35),
    (0.94, "herbs_sage_big", 1.6, 0.72, 0.36, 0.7),
    (1.36, "herbs_white_big", 1.12, 0.6, 0.5, 1.05),
]


def build(root, det):
    L = dl.post(root, "post_l", (-PX, 0, 0), 4.36, d=PD, footing=(0.82, 0.86), detail=det)
    R = dl.post(root, "post_r", (PX, 0, 0), BEAM_Y1 + 0.1, d=PD, footing=(0.82, 0.86), detail=det)
    # the beam across, its left end standing out of the left post, the right end flush with the right post
    pd.hbeam(root, "beam", -PX - 0.4, PX + PD / 2 + 0.02, BEAM_Y0, BEAM_Y1, 0.0, BEAM_D)
    # the angled brace under the beam on the left
    p0 = dl.v3(-PX + PD / 2 - 0.02, BEAM_Y0 - 0.72, 0)
    p1 = dl.v3(-PX + PD / 2 + 0.62, BEAM_Y0 + 0.02, 0)
    dl.beam(root, "brace", p0, p1, 0.2, {"all": "post", "+1": "end_grain", "-1": "end_grain"}, width=0.22, up=dl.Z)
    # iron bolts: two where the beam crosses the left post, one on the right, one at each end of the brace
    zf = BEAM_D / 2
    ym = (BEAM_Y0 + BEAM_Y1) / 2
    for k, x in enumerate((-PX - 0.1, -PX + 0.1, PX)):
        pd.bolt(det, "bolt_%d" % k, (x, ym, zf), (0, 0, 1))
        pd.bolt(det, "bolt_b%d" % k, (x, ym, -zf), (0, 0, -1))
    pd.bolt(det, "bolt_brace_0", (-PX + PD / 2 + 0.05, BEAM_Y0 - 0.58, 0.11), (0, 0, 1))
    pd.bolt(det, "bolt_brace_1", (-PX + PD / 2 + 0.5, BEAM_Y0 - 0.1, 0.11), (0, 0, 1))
    for k, (x, region, length, width, rope, phase) in enumerate(BUNDLES):
        pd.herb_bundle(root, det, "bundle_%d" % k, (x, BEAM_Y0, 0.0), region, length, width, rope, beam_d=BEAM_D, phase=phase)
    return L, R


def draw_icon(put):
    wood, dark, stone = (122, 82, 50), (70, 46, 26), (150, 148, 140)
    for y in range(2, 14):
        put(1, y, wood if y % 4 else dark)
        put(2, y, dark)
    for y in range(4, 14):
        put(13, y, wood if y % 4 else dark)
        put(14, y, dark)
    for x in range(0, 16):
        put(x, 3, wood)
        put(x, 4, dark)
    put(3, 5, wood)
    put(4, 5, wood)
    for x in (0, 1, 2, 3, 12, 13, 14, 15):
        put(x, 14, stone)
        put(x, 15, (110, 108, 102))
    cols = [(78, 138, 42), (122, 74, 180), (138, 160, 106), (240, 236, 222)]
    for k, (x0, n) in enumerate(((5, 7), (7, 5), (9, 6), (11, 4))):
        put(x0, 5, (216, 192, 142))
        for i in range(n):
            put(x0 - (1 if i > 2 and k == 0 else 0), 6 + i, cols[k])
            if i > 1:
                put(x0 + (1 if k != 3 else 0), 6 + i, cols[k])


if __name__ == "__main__":
    dl.setup(NAME)
    root = dl.Bone(NAME)
    det = dl.Bone("detail", parent=root)
    build(root, det)
    dl.export(root, NAME, light=0, icon=draw_icon)
