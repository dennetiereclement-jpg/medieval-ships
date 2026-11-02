"""Crown banner (deco_banniere, 1.20.0): one tall squared post (a collar with an iron band at its foot, a wider
block with an iron band and bolts at the top), a short arm with gold rings and a gold finial, a gold rod hung under
it holding a navy-blue banner with a gold border, a golden rampant lion facing the post and a dagged pointed end.
~2 wide, 4 high. The post collides; the banner does not."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decolib as dl  # noqa: E402
import props_d2 as pd  # noqa: E402

NAME = "deco_banniere"
D = 0.46
H = 4.0
ARM_Y, ARM_D, ARM_L = 3.42, 0.3, 1.66
BANNER_X, BANNER_W, BANNER_H = 1.04, 1.0, 2.4


def build(root, det):
    P = dl.post(root, "post", (0, 0, 0), H, d=D, detail=det)
    # the collar at the foot: a wider block between two thin iron bands, bolts on the front and back
    pd.collar(root, "collar", (0, 1.06, 0), D + 0.12, 0.32, region="post", top="end_grain")
    for k, y in enumerate((0.93, 1.19)):
        pd.collar(root, "collar_band_%d" % k, (0, y, 0), D + 0.15, 0.06)
    for k, n in enumerate(((0, 0, 1), (0, 0, -1))):
        for j, x in enumerate((-0.12, 0.12)):
            pd.bolt(det, "collar_bolt_%d_%d" % (k, j), (x, 1.06, n[2] * (D + 0.12) / 2), n)
    # the top block where the arm goes through, an iron band with bolts round it
    pd.collar(root, "top_block", (0, ARM_Y + 0.0, 0), D + 0.16, 0.46, region="post", top="end_grain")
    pd.collar(root, "top_band", (0, ARM_Y + 0.0, 0), D + 0.19, 0.1)
    for k, n in enumerate(((0, 0, 1), (0, 0, -1))):
        for j, x in enumerate((-0.15, 0.15)):
            pd.bolt(det, "top_bolt_%d_%d" % (k, j), (x, ARM_Y, n[2] * (D + 0.19) / 2), n)
    # the arm (standing out a little on the left), gold rings, a gold finial at its end
    dl.gallows_arm(root, "arm", P, ARM_Y, ARM_L, d=ARM_D, region="plank", brace=0, overhang=0.36, caps=False)
    y_arm0 = ARM_Y - ARM_D / 2
    rings = (BANNER_X - BANNER_W / 2 + 0.12, BANNER_X + BANNER_W / 2 - 0.1)
    for k, x in enumerate(rings):
        pd.cbox(root, "arm_ring_%d" % k, (x, ARM_Y, 0), (0.08, ARM_D + 0.05, ARM_D * 0.9 + 0.05), "gold")
        pd.cbox(det, "arm_ring_%d_b" % k, (x + 0.1, ARM_Y, 0), (0.05, ARM_D + 0.03, ARM_D * 0.9 + 0.03), "gold")
        # the hanger down to the rod
        pd.cbox(det, "hanger_%d" % k, (x, y_arm0 - 0.08, 0), (0.04, 0.16, 0.05), "gold")
    pd.cbox(root, "finial_collar", (ARM_L + 0.02, ARM_Y, 0), (0.12, ARM_D + 0.07, ARM_D * 0.9 + 0.07), "gold")
    pd.add_cube(root, "finial", dl.v3(ARM_L + 0.15, ARM_Y, 0), dl.rx(0.785398) @ dl.rz(0.0), (0.16, 0.2, 0.2), "gold")
    pd.add_cube(det, "finial_tip", dl.v3(ARM_L + 0.27, ARM_Y, 0), dl.rx(0.785398), (0.1, 0.1, 0.1), "gold")
    # the banner from its gold rod
    dl.banner(root, "banner", (BANNER_X, y_arm0 - 0.19, 0.0), BANNER_W, BANNER_H, normal=(0, 0, 1), region="banner_crown",
              rod="gold_rod", knobs="gold", wave=0.035, rod_extra=0.07)
    return P


def draw_icon(put):
    wood, dark, gold, navy = (122, 82, 50), (70, 46, 26), (224, 168, 48), (44, 46, 124)
    for y in range(1, 16):
        put(2, y, wood if y % 5 else dark)
        put(3, y, dark)
    for x in range(1, 15):
        put(x, 2, wood)
    put(15, 2, gold)
    put(7, 2, gold)
    put(13, 2, gold)
    for x in range(6, 15):
        put(x, 3, gold)
    for y in range(4, 13):
        for x in range(6, 15):
            put(x, y, gold if x in (6, 14) else navy)
    for k in range(4):
        for x in range(6 + k, 15 - k):
            put(x, 13 + k, gold if x in (6 + k, 14 - k) else navy)
    for (x, y) in ((9, 5), (10, 5), (9, 6), (10, 7), (11, 7), (11, 8), (10, 9), (12, 9), (9, 10), (12, 10), (8, 6), (12, 6), (13, 5)):
        put(x, y, gold)


if __name__ == "__main__":
    dl.setup(NAME)
    root = dl.Bone(NAME)
    det = dl.Bone("detail", parent=root)
    build(root, det)
    dl.export(root, NAME, light=0, icon=draw_icon)
