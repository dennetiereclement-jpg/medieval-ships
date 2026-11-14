"""porte_chene (1.32.0): small oak door, 2 high x 1 wide, one leaf hinged on the left.

Reference: ref1 top row 1st, ref3 top 1st, ref4 top 1st, ref2 top 1st: vertical oak planks inside a heavy riveted iron
frame, two broad riveted iron bands ending in square plates at the latch side and in hinge plates on the frame at the
hinge side, a big iron ring handle (bone handle_0, turns when the door is unlocked). Back: the same planks, two battens
and a diagonal brace, a small ring.
The frame takes the whole thickness of the block, rebated for the leaf (doorlib_small.Door.build_frame).
Usage: python3 tools/doors/generate_porte_chene.py [--preview]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import doorlib_small as ds  # noqa: E402
from doorlib_small import rgb, shade, G  # noqa: E402

NAME = "porte_chene"
WOOD, WOOD_DARK = rgb("9a5e2c"), rgb("3e200c")
IRON, IRON_L, IRON_D = rgb("7a6e72"), rgb("bcb2b0"), rgb("2e2628")
RIV_L, RIV_D = rgb("d6d0cc"), rgb("2a2224")
BACK_WOOD = rgb("7e4822")

S = 1 / 32


def build():
    d = ds.Door(NAME, size=256, sill=2 * S, lintel=3 * S, cz=2 * S, seed=11)
    F, B = d.F, d.B
    d.material("wood_side", ds.tile_wood(shade(WOOD, 0.9), WOOD_DARK))
    d.material("iron_side", ds.tile_metal(shade(IRON, 0.85)))
    d.material("iron_in", ds.tile_metal(shade(IRON, 0.62)))
    d.material("end_grain", ds.tile_flat(shade(WOOD, 0.75), noise=10))
    x0, x1, y0, y1, cz = d.lx0, d.lx1, d.ly0, d.ly1, d.cz
    vx0, vx1 = d.vx0 + G, d.vx1 - G          # front relief stays clear of the frame stops
    bands = [(1.40, 1.54), (0.24, 0.38)]
    plate_w = 5 * S
    ring_c = (0.125, 0.875)

    # ---------------------------------------------------------------- pictures
    ds.frame_picture(d.FF, IRON, IRON_D, RIV_L, RIV_D, x0, x1, y0, y1)
    ds.frame_picture(d.FB, shade(IRON, 0.9), IRON_D, RIV_L, RIV_D, x0, x1, y0, y1, rivets=7, big=False)
    for (b0, b1) in bands:   # hinge plates on the frame (relief), painted on the frame picture
        d.FF.metal(-0.5 + G, x0 + ds.LIP - G, b0 - S, b1 + S, shade(IRON, 1.1), noise=8)
        d.FF.rivet(-0.5 + 2 * S, (b0 + b1) / 2 + S / 2, light=RIV_L, dark=RIV_D, big=True)
        d.FF.fill(x0 - 1.5 * S, x0 - 0.5 * S, b0 - S, b1 + S, shade(IRON, 0.7))      # knuckle shadow
    F.planks_v(x0, x1, y0, y1, 4, WOOD, WOOD_DARK, grain=0.14)
    F.fill(x0, x1, y0, y0 + 2 * S, shade(WOOD, 0.62))                               # dark foot of the planks
    for (b0, b1) in bands:
        F.metal(vx0, vx1 - plate_w, b0, b1, IRON, noise=10)
        F.rivets_h(vx0 + 0.04, vx1 - plate_w - 0.02, (b0 + b1) / 2 + S / 2, 4, light=RIV_L, dark=RIV_D, big=True)
        F.metal(vx1 - plate_w, vx1, b0 - S, b1 + S, shade(IRON, 1.06), noise=8)
        F.rivet(vx1 - 2.5 * S - S / 2, (b0 + b1) / 2 + S / 2, light=RIV_L, dark=RIV_D, big=True)
        F.fill(vx0, vx1 - plate_w, b0 - S, b0, shade(WOOD, 0.6))                    # shadow under the band
    F.disc(ring_c[0], ring_c[1] - 3 * S, 3.2 * S, shade(WOOD, 0.7))                 # worn wood round the ring
    B.planks_v(x0, x1, y0, y1, 4, BACK_WOOD, WOOD_DARK, grain=0.14)
    battens = [(1.36, 1.48), (0.30, 0.42)]
    for (b0, b1) in battens:
        B.planks_v(x0, x1, b0, b1, 1, shade(BACK_WOOD, 0.9), WOOD_DARK, knots=1)
        B.fill(x0, x1, b0, b0 + S, shade(BACK_WOOD, 0.62))
        B.rivets_h(x0 + 0.08, x1 - 0.05, (b0 + b1) / 2, 3, light=RIV_L, dark=RIV_D)
    for t in range(0, 80):   # diagonal brace (painted between the battens)
        y = battens[1][1] + (battens[0][0] - battens[1][1]) * t / 79
        x = x1 - 0.08 - (x1 - x0 - 0.2) * t / 79
        for w in range(-2, 3):
            i, j = B.pix(x + w * S, y)
            B.put(i, j, shade(BACK_WOOD, 0.86 if abs(w) < 2 else 0.6))

    # ---------------------------------------------------------------- frame
    d.build_frame("iron_side", inner="iron_in")
    for k, (b0, b1) in enumerate(bands):
        d.relief(d.frame, "hinge_plate_%d" % k, -0.5 + G, x0 + ds.LIP - G, b0 - S, b1 + S, d.zf, S, "iron_side",
                 face="ffront")

    # ---------------------------------------------------------------- leaf
    lf = d.leaf
    d.core("wood_side", top="end_grain", bottom="end_grain")
    for k, (b0, b1) in enumerate(bands):
        d.relief(lf, "band_%d" % k, vx0, vx1 - plate_w, b0, b1, cz, S, "iron_side")
        d.relief(lf, "band_plate_%d" % k, vx1 - plate_w, vx1, b0 - S, b1 + S, cz, 1.5 * S, "iron_side")
    for k, (b0, b1) in enumerate(battens):
        d.relief(lf, "batten_%d" % k, x0, x1, b0, b1, -cz, -S, "wood_side")
    ds.ring_handle(d, lf, "handle_0", ring_c[0], ring_c[1], cz, "iron_side", s=1)
    ds.ring_handle(d, lf, "handle_1", 0.16, 0.875, -cz, "iron_side", s=-1, big=False)
    return d


def main():
    d = build()
    d.export()
    if "--preview" in sys.argv:
        out = os.environ.get("DOOR_PREVIEW", os.path.join(ds.REF_DIR, "..", "doors_out2", "small_%s.png" % NAME))
        d.preview(out, refs=[(os.path.join(ds.REF_DIR, "ref1.png"), (36, 186, 154, 440)),
                             (os.path.join(ds.REF_DIR, "ref3.png"), (120, 30, 310, 395))])


if __name__ == "__main__":
    main()
