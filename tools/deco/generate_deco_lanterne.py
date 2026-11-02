"""Hanging lantern (deco_lanterne, 1.20.0): one tall squared post (a wooden sleeve with iron bands at its foot, an
iron band with bolts half way up, a top block with an iron cap), a horizontal arm through its top with an angled
brace, iron straps, and a big wooden-framed lantern (lit glass, 2 x 2 panes a side) hanging from a chain at the
arm's end. ~2 wide, 3.6 high. The post (and the lantern's body) collide. "light": 15 = the anchor block at the
post's foot shines like a torch (vanilla light engine, no tick); the lantern itself is drawn full bright."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decolib as dl  # noqa: E402
import props_d2 as pd  # noqa: E402

NAME = "deco_lanterne"
D = 0.42            # the post's section
H = 3.62            # the post's height
ARM_Y, ARM_D = 3.24, 0.42
HANG_X = 1.2        # where the chain hangs from the arm


def build(root, det):
    P = dl.post(root, "post", (0, 0, 0), H, d=D, bands=(2.42,), detail=det)
    # the sleeve at the foot: a wider wooden collar between two iron bands, bolts on its faces
    pd.collar(root, "sleeve", (0, 0.64, 0), D + 0.14, 0.4, region="post", top="end_grain")
    for k, y in enumerate((0.47, 0.81)):
        pd.collar(root, "sleeve_band_%d" % k, (0, y, 0), D + 0.17, 0.07)
    for k, (n, sgn) in enumerate((((0, 0, 1), 1), ((1, 0, 0), 1), ((0, 0, -1), 1), ((-1, 0, 0), 1))):
        c = dl.v3(*n) * ((D + 0.14) / 2)
        pd.bolt(det, "sleeve_bolt_%d" % k, (c[0], 0.64, c[2]), n)
    for k, n in enumerate(((0, 0, 1), (0, 0, -1), (1, 0, 0), (-1, 0, 0))):
        c = dl.v3(*n) * ((D + 0.05) / 2)
        pd.bolt(det, "band_bolt_%d" % k, (c[0], 2.42, c[2]), n, s=0.055)
    # the top block (wider), an iron band round it, an iron cap
    pd.collar(root, "top_block", (0, H - 0.17, 0), D + 0.1, 0.34, region="post", top="end_grain")
    pd.collar(root, "top_band", (0, H - 0.04, 0), D + 0.13, 0.08)
    # the arm through the top, standing out on the left; the brace (steep, as in the picture) and iron straps
    dl.gallows_arm(root, "arm", P, ARM_Y, 1.52, d=ARM_D, region="plank", brace=0, overhang=0.42, caps=True, detail=det)
    y_arm0 = ARM_Y - ARM_D / 2
    p0 = dl.v3(D / 2 - 0.03, y_arm0 - 1.0, 0)
    p1 = dl.v3(D / 2 + 0.6, y_arm0 + 0.03, 0)
    dl.beam(root, "brace", p0, p1, 0.22, {"all": "post", "+1": "end_grain", "-1": "end_grain"}, width=0.24, up=dl.Z)
    pd.bolt(det, "brace_bolt_0", (D / 2 + 0.07, y_arm0 - 0.86, 0.12), (0, 0, 1))
    pd.bolt(det, "brace_bolt_1", (D / 2 + 0.5, y_arm0 - 0.12, 0.12), (0, 0, 1))
    pd.bolt(det, "brace_bolt_2", (D / 2 + 0.07, y_arm0 - 0.86, -0.12), (0, 0, -1))
    # an iron strap over the arm where it meets the post (front and top)
    pd.cbox(det, "arm_strap", (D / 2 + 0.16, ARM_Y, 0), (0.09, ARM_D + 0.03, ARM_D * 0.9 + 0.03), {"all": "iron_band", "+1": "iron", "-1": "iron"})
    for k, x in enumerate((-0.1, 0.1)):
        pd.bolt(det, "arm_bolt_%d" % k, (x, ARM_Y + 0.06, D / 2 + 0.05), (0, 0, 1))
    # the chain and the big lantern
    end = dl.chain(det, "chain", (HANG_X, y_arm0, 0), 0.3, link=0.1, w=0.075)
    pd.cbox(det, "chain_eye", (HANG_X, y_arm0 - 0.02, 0), (0.12, 0.04, 0.12), "iron_dark")
    bottom = pd.big_lantern(root, det, "lantern", end)
    # the lantern's body collides (it hangs at head height)
    dl.collide((HANG_X - 0.45, bottom[1] + 0.3, -0.45, HANG_X + 0.45, end[1] - 0.2, 0.45))
    return P


def draw_icon(put):
    wood, dark, iron = (122, 82, 50), (70, 46, 26), (70, 70, 76)
    for y in range(1, 16):
        put(3, y, wood if y % 5 else dark)
        put(4, y, dark)
    for x in range(2, 14):
        put(x, 1, wood)
        put(x, 2, dark)
    for k in range(4):
        put(5 + k, 6 - k, wood)
    put(11, 3, iron)
    put(11, 4, iron)
    for x in range(8, 15):
        put(x, 5, dark)
        put(x, 11, dark)
    for y in range(6, 11):
        put(8, y, wood)
        put(14, y, wood)
        for x in range(9, 14):
            put(x, y, (255, 214, 120) if x != 11 and y != 8 else (196, 120, 40))
    put(11, 12, iron)
    put(11, 13, iron)
    put(3, 13, iron)
    put(4, 13, iron)


if __name__ == "__main__":
    dl.setup(NAME)
    root = dl.Bone(NAME)
    det = dl.Bone("detail", parent=root)
    build(root, det)
    dl.export(root, NAME, light=15, icon=draw_icon)
