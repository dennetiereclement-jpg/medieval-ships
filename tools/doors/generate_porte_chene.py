"""porte_chene (1.31.0): small oak door, 2 high x 1 wide, one leaf hinged on the left.

Reference: ref1 top row 1st, ref3 top 1st, ref4 top 1st, ref2 top 1st: vertical oak planks inside a riveted iron frame,
two broad iron bands (strap hinges ending in big hinge knuckles on the left, square plates on the right), a big iron
ring handle on the right half. Back: the same planks, two battens and a diagonal brace, a small ring.
Usage: python3 tools/doors/generate_porte_chene.py [--preview]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import doorlib_small as ds  # noqa: E402
from doorlib_small import rgb, shade  # noqa: E402

NAME = "porte_chene"
WOOD, WOOD_DARK = rgb("955a2a"), rgb("3e200c")
IRON, IRON_L, IRON_D = rgb("7a6e72"), rgb("bcb2b0"), rgb("2e2628")
RIV_L, RIV_D = rgb("d6d0cc"), rgb("2a2224")
BACK_WOOD = rgb("7a4520")

S = 1 / 32


def build():
    d = ds.Door(NAME, size=256, frame_w=3 * S, sill=2 * S, lintel=3 * S, seed=11)
    F, B = d.F, d.B
    d.material("wood_side", ds.tile_wood(shade(WOOD, 0.9), WOOD_DARK))
    d.material("iron_side", ds.tile_metal(shade(IRON, 0.85)))
    d.material("end_grain", ds.tile_flat(shade(WOOD, 0.75), noise=10))
    x0, x1, y0, y1 = d.lx0, d.lx1, d.ly0, d.ly1
    fz0, fz1 = -2 * S, 5 * S            # frame depth (flush with the leaf back, a reveal at the front)
    cz = 2 * S                          # leaf core half thickness (planks z in [-1/16, 1/16])

    # ---------------------------------------------------------------- pictures
    for C in (F, B):
        C.planks_v(x0, x1, y0, y1, 4, WOOD if C is F else BACK_WOOD, WOOD_DARK, grain=0.14)
        # iron frame all round
        C.metal(-0.5, x0, 0, 2, IRON, noise=12)
        C.metal(x1, 0.5, 0, 2, IRON, noise=12)
        C.metal(-0.5, 0.5, y1, 2, IRON, noise=12)
        C.metal(x0, x1, 0, y0, shade(IRON, 0.9), noise=12)
    for C in (F,):
        for xr in (-0.5 + 1.5 * S, 0.5 - 1.5 * S):
            C.rivets_v(xr - S / 2, 0.1, 1.85, 9, light=RIV_L, dark=RIV_D, big=True)
        C.rivets_h(-0.42, 0.42, 2 - 1.5 * S, 5, light=RIV_L, dark=RIV_D)
    # front: two broad bands with rivets, square plates at the latch end, big hinge plates at the hinge end
    bands = [(1.40, 1.54), (0.22, 0.36)]
    for k, (b0, b1) in enumerate(bands):
        F.metal(x0, x1, b0, b1, IRON, noise=10)
        F.rivets_h(x0 + 0.12, x1 - 0.1, (b0 + b1) / 2 + S / 2, 4, light=RIV_L, dark=RIV_D, big=True)
        F.metal(x1 - 5 * S, x1, b0 - S, b1 + S, shade(IRON, 1.05), noise=8)
        F.rivet(x1 - 2.5 * S, (b0 + b1) / 2, light=RIV_L, dark=RIV_D, big=True)
        F.metal(-0.5, x0 + 2 * S, b0 - S, b1 + S, shade(IRON, 1.08), noise=8)       # hinge plate + knuckle
        F.rivet(-0.5 + 1.5 * S, (b0 + b1) / 2, light=RIV_L, dark=RIV_D, big=True)
        F.metal(x0 - S, x0 + S, b0 - 3 * S, b1 + 3 * S, shade(IRON, 0.9), noise=6)   # knuckle barrel
    ring_c = (0.13, 0.86)
    ds.paint_ring(F, ring_c[0], ring_c[1], 4 * S, 6 * S, IRON_L, IRON, IRON_D)
    # back: battens + diagonal brace (painted on the planks) + small ring
    for (b0, b1) in ((1.36, 1.48), (0.30, 0.42)):
        B.planks_v(x0 + 0.08, x1, b0, b1, 1, shade(BACK_WOOD, 0.88), WOOD_DARK, knots=1)
        B.rivets_h(x0 + 0.12, x1 - 0.05, (b0 + b1) / 2, 3, light=RIV_L, dark=RIV_D)
    for t in range(0, 64):
        y = 0.42 + (1.36 - 0.42) * t / 63
        x = x1 - 0.06 - (x1 - x0 - 0.2) * t / 63
        for w in range(-2, 3):
            i, j = B.pix(x + w * S, y)
            B.put(i, j, shade(BACK_WOOD, 0.8 if abs(w) < 2 else 0.6))
    ds.paint_ring(B, 0.15, 0.86, 3 * S, 5 * S, IRON_L, IRON, IRON_D)

    # ---------------------------------------------------------------- frame cubes
    fr = d.frame
    d.box(fr, "jamb_l", -0.5, x0, 0, 2, fz0, fz1, side="iron_side")
    d.box(fr, "jamb_r", x1, 0.5, 0, 2, fz0, fz1, side="iron_side")
    d.box(fr, "lintel", x0, x1, y1, 2, fz0, fz1, side="iron_side")
    d.box(fr, "sill", x0, x1, 0, y0, fz0, 3 * S, side="iron_side")
    det_f = d.detail(fr)
    for k, (b0, b1) in enumerate(bands):
        d.box(det_f, "hinge_plate_%d" % k, -0.5, x0, b0 - S, b1 + S, fz1, fz1 + S, side="iron_side")

    # ---------------------------------------------------------------- leaf cubes
    lf = d.leaf
    d.box(lf, "planks", x0, x1, y0, y1, -cz, cz, side="wood_side", top="end_grain", bottom="end_grain")
    for k, (b0, b1) in enumerate(bands):
        d.box(lf, "band_%d" % k, x0, x1 - 5 * S, b0, b1, cz, cz + S, side="iron_side")
        d.box(lf, "band_plate_%d" % k, x1 - 5 * S, x1, b0 - S, b1 + S, cz, cz + 1.5 * S, side="iron_side")
        d.box(lf, "knuckle_%d" % k, x0, x0 + S, b0 - 3 * S, b1 + 3 * S, cz, cz + 2 * S, side="iron_side")
    det = d.detail(lf)
    ds.ring_handle(d, det, ring_c[0], ring_c[1], cz, "iron_side", plate=4 * S, ring=6 * S)
    for k, (b0, b1) in enumerate(((1.36, 1.48), (0.30, 0.42))):
        d.box(lf, "batten_%d" % k, x0 + 0.08, x1, b0, b1, -cz - S, -cz, side="wood_side")
    ds.ring_handle(d, det, 0.15, 0.86, -cz, "iron_side", plate=3 * S, ring=5 * S, back=True)
    return d


def main():
    d = build()
    d.export()
    if "--preview" in sys.argv:
        out = os.environ.get("DOOR_PREVIEW", os.path.join(ds.REF_DIR, "..", "doors_out", "small_%s.png" % NAME))
        d.preview(out, refs=[(os.path.join(ds.REF_DIR, "ref1.png"), (36, 186, 154, 440)),
                             (os.path.join(ds.REF_DIR, "ref3.png"), (120, 30, 310, 395)),
                             (os.path.join(ds.REF_DIR, "ref4.png"), (76, 80, 217, 370))])


if __name__ == "__main__":
    main()
