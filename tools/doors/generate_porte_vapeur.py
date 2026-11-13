"""porte_vapeur (1.31.0): small steam door, 2 high x 1 wide, one leaf hinged on the left.

Reference: ref4 bottom right (lit porthole, copper pipes and valve on dark planks in a riveted iron frame), ref5 top 5th
(gear, copper pipes, small lit grate), ref3 top 4th (brass bands, big gear). Dark wood planks, brass bands, a round
lit porthole (glow) with a copper rim and cross bars, two meshing gears (gear_a_0 clockwise, gear_b_1
anti-clockwise), copper pipes with a valve, a small piston (piston_0) coming out of a cylinder, a brass pull handle.
Back: planks, two iron battens, the porthole, a small handle.
Usage: python3 tools/doors/generate_porte_vapeur.py [--preview]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import doorlib_small as ds  # noqa: E402
from doorlib_small import rgb, shade  # noqa: E402

NAME = "porte_vapeur"
WOOD, WOOD_DARK = rgb("6c4428"), rgb("26160a")
FRAME = rgb("5c5254")
BRASS, BRASS_L, BRASS_D = rgb("b0762c"), rgb("e8b45a"), rgb("5a3410")
COPPER, COPPER_L, COPPER_D = rgb("b4602e"), rgb("ee9a5c"), rgb("5c2612")
RIV_L, RIV_D = rgb("f0c070"), rgb("3a2008")
IRON_RIV_L, IRON_RIV_D = rgb("b0a8a8"), rgb("1c1618")

S = 1 / 32


def pipe_v(C, x, y0, y1, w=3 * S):
    C.fill(x - w / 2, x + w / 2, y0, y1, COPPER, noise=6)
    C.fill(x - w / 2, x - w / 2 + S, y0, y1, COPPER_L, noise=4)
    C.fill(x + w / 2 - S, x + w / 2, y0, y1, COPPER_D, noise=4)


def pipe_h(C, x0, x1, y, w=3 * S):
    C.fill(x0, x1, y - w / 2, y + w / 2, COPPER, noise=6)
    C.fill(x0, x1, y + w / 2 - S, y + w / 2, COPPER_L, noise=4)
    C.fill(x0, x1, y - w / 2, y - w / 2 + S, COPPER_D, noise=4)


def build():
    d = ds.Door(NAME, size=256, frame_w=3 * S, sill=2 * S, lintel=3 * S, seed=37)
    F, B = d.F, d.B
    d.material("wood_side", ds.tile_wood(shade(WOOD, 0.9), WOOD_DARK))
    d.material("iron_side", ds.tile_metal(shade(FRAME, 0.85)))
    d.material("brass_side", ds.tile_metal(shade(BRASS, 0.85)))
    d.material("copper_side", ds.tile_metal(shade(COPPER, 0.9)))
    big = d.sprite("gear_big", 16, 16, lambda c: ds.paint_gear(c, 8, BRASS, BRASS_L, BRASS_D, hole=(30, 18, 10)))
    small = d.sprite("gear_small", 10, 10, lambda c: ds.paint_gear(c, 6, COPPER, COPPER_L, COPPER_D, hole=(30, 18, 10),
                                                                  spokes=3, tooth_depth=2.0, rim_w=1.6, hub=1.6))
    x0, x1, y0, y1 = d.lx0, d.lx1, d.ly0, d.ly1
    fz0, fz1 = -2 * S, 5 * S
    cz = 2 * S
    pc, pr = (0.0, 1.52), 7 * S                 # porthole centre / outer radius of the copper rim
    hh = 4 * S                                  # half size of the lit square hole
    ga = (0.0, 0.92, 8 * S)                     # big gear (centre x, y, radius)
    gb = (-0.24, 1.16, 5 * S)                    # small gear, meshing
    py = 0.26                                   # horizontal pipe
    pxl, pxr = -0.30, 0.32                      # vertical pipes
    cyl = (pxr - 2.5 * S, pxr + 2.5 * S, 0.40, 0.64)
    rod = (pxr - S, pxr + S, 0.64, 0.76)
    handle = (0.31, 1.18)

    # ---------------------------------------------------------------- pictures
    for C in (F, B):
        C.planks_v(x0, x1, y0, y1, 4, WOOD, WOOD_DARK, knots=2)
        C.metal(-0.5, x0, 0, 2, FRAME, noise=12)
        C.metal(x1, 0.5, 0, 2, FRAME, noise=12)
        C.metal(x0, x1, y1, 2, FRAME, noise=12)
        C.metal(x0, x1, 0, y0, shade(FRAME, 0.9), noise=12)
        for xr in (-0.5 + 1.5 * S, 0.5 - 1.5 * S):
            C.rivets_v(xr - S / 2, 0.05, 1.9, 9, light=IRON_RIV_L, dark=IRON_RIV_D)
        C.rivets_h(-0.4, 0.4, 2 - 1.5 * S, 5, light=RIV_L, dark=RIV_D)
        # porthole: copper rim, lit glass, cross bars
        C.disc(pc[0], pc[1], pr, COPPER, noise=8, ring=(1, COPPER_D))
        C.disc(pc[0] - S / 2, pc[1] + S / 2, pr - S, COPPER_L)
        C.disc(pc[0], pc[1], pr - S, COPPER)
        C.fill(-hh, hh, pc[1] - hh, pc[1] + hh, (0, 0, 0))
        C.glow(-hh, hh, pc[1] - hh, pc[1] + hh)
        C.fill(-hh, hh, pc[1] - S / 2, pc[1] + S / 2, COPPER_D)
        C.fill(-S / 2, S / 2, pc[1] - hh, pc[1] + hh, COPPER_D)
        for a in range(8):
            import math
            C.rivet(pc[0] + (pr - 1.6 * S) * math.cos(a * math.pi / 4) - S / 2,
                    pc[1] + (pr - 1.6 * S) * math.sin(a * math.pi / 4), light=RIV_L, dark=RIV_D)
    # front: brass bands (top + bottom), copper pipes, valve, cylinder, handle
    for (b0, b1) in ((y1 - 3 * S, y1), (y0, y0 + 3 * S)):
        F.metal(x0, x1, b0, b1, BRASS, noise=10)
        F.rivets_h(x0, x1, (b0 + b1) / 2, 5, light=RIV_L, dark=RIV_D)
    pipe_h(F, pxl - 1.5 * S, pxr + 1.5 * S, py)
    pipe_v(F, pxl, py - 1.5 * S, 0.76)
    pipe_v(F, pxr, py - 1.5 * S, cyl[2])
    for (jx, jy) in ((pxl, py), (pxr, py), (pxl, 0.62)):
        F.metal(jx - 2.5 * S, jx + 2.5 * S, jy - 2 * S, jy + 2 * S, BRASS, noise=6)   # couplings / elbows
    F.disc(pxl, 0.80, 2.5 * S, BRASS_D)                                                 # valve wheel
    F.disc(pxl, 0.80, 2 * S, BRASS, ring=(1, BRASS_L))
    F.fill(pxl - S / 2, pxl + S / 2, 0.80 - 2 * S, 0.80 + 2 * S, BRASS_D)
    F.fill(pxl - 2 * S, pxl + 2 * S, 0.80 - S / 2, 0.80 + S / 2, BRASS_D)
    F.metal(cyl[0], cyl[1], cyl[2], cyl[3], COPPER, noise=8)
    F.fill(cyl[0], cyl[0] + S, cyl[2], cyl[3], COPPER_L)
    F.metal(cyl[0] - S / 2, cyl[1] + S / 2, cyl[3] - 2 * S, cyl[3], BRASS, noise=4)
    F.metal(rod[0], rod[1], rod[2], rod[3], rgb("c8c0b8"), noise=4)
    F.metal(handle[0] - S, handle[0] + 2 * S, handle[1] - 0.09, handle[1] + 0.09, BRASS, noise=6)
    # back: iron battens + small handle
    for (b0, b1) in ((1.18, 1.28), (0.30, 0.40)):
        B.metal(x0 + 0.08, x1, b0, b1, FRAME, noise=10)
        B.rivets_h(x0 + 0.1, x1 - 0.04, (b0 + b1) / 2, 4, light=IRON_RIV_L, dark=IRON_RIV_D)
    B.metal(0.22, 0.32, 0.82, 0.92, BRASS, noise=6)

    # ---------------------------------------------------------------- frame cubes
    fr = d.frame
    d.box(fr, "jamb_l", -0.5, x0, 0, 2, fz0, fz1, side="iron_side")
    d.box(fr, "jamb_r", x1, 0.5, 0, 2, fz0, fz1, side="iron_side")
    d.box(fr, "lintel", x0, x1, y1, 2, fz0, fz1, side="iron_side")
    d.box(fr, "sill", x0, x1, 0, y0, fz0, 3 * S, side="iron_side")
    for k, y in enumerate((0.35, 1.0, 1.65)):
        d.box(fr, "hinge_%d" % k, x0 - S, x0 + S, y - 3 * S, y + 3 * S, fz1 - S, fz1 + S, side="brass_side",
              front="brass_side")

    # ---------------------------------------------------------------- leaf cubes
    lf = d.leaf
    ds.core_with_hole(d, lf, x0, x1, y0, y1, -hh, hh, pc[1] - hh, pc[1] + hh, cz, "wood_side")
    d.box(lf, "glow_porthole", -hh, hh, pc[1] - hh, pc[1] + hh, -cz + S / 2, cz - S / 2, side="copper_side")
    for zs, tag in ((1, "f"), (-1, "b")):
        z0, z1 = zs * cz, zs * (cz + 1.5 * S)
        # octagonal copper rim round the lit square
        d.box(lf, "rim_t_" + tag, -hh, hh, pc[1] + hh, pc[1] + pr, z0, z1, side="copper_side")
        d.box(lf, "rim_d_" + tag, -hh, hh, pc[1] - pr, pc[1] - hh, z0, z1, side="copper_side")
        d.box(lf, "rim_l_" + tag, -pr, -hh, pc[1] - hh, pc[1] + hh, z0, z1, side="copper_side")
        d.box(lf, "rim_r_" + tag, hh, pr, pc[1] - hh, pc[1] + hh, z0, z1, side="copper_side")
        for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
            a0, a1 = sorted((sx * (hh - S), sx * (pr - 1.5 * S)))
            c0, c1 = sorted((pc[1] + sy * (hh - S), pc[1] + sy * (pr - 1.5 * S)))
            d.box(lf, "rim_c%d_%s" % (k, tag), a0, a1, c0, c1, z0, z1, side="copper_side")
        d.box(lf, "cross_h_" + tag, -hh, hh, pc[1] - S / 2, pc[1] + S / 2, zs * (cz - S / 2), zs * (cz + S / 2),
              side="copper_side")
        d.box(lf, "cross_v_" + tag, -S / 2, S / 2, pc[1] - hh, pc[1] + hh, zs * (cz - S / 2), zs * (cz + S / 2),
              side="copper_side")
    for k, (b0, b1) in enumerate(((y1 - 3 * S, y1), (y0, y0 + 3 * S))):
        d.box(lf, "brass_band_%d" % k, x0, x1, b0, b1, cz, cz + S, side="brass_side")
    for k, (b0, b1) in enumerate(((1.18, 1.28), (0.30, 0.40))):
        d.box(lf, "batten_%d" % k, x0 + 0.08, x1, b0, b1, -cz - S, -cz, side="iron_side")
    pz0, pz1 = cz, cz + 2 * S
    d.box(lf, "pipe_h", pxl - 1.5 * S, pxr + 1.5 * S, py - 1.5 * S, py + 1.5 * S, pz0, pz1, side="copper_side")
    d.box(lf, "pipe_l", pxl - 1.5 * S, pxl + 1.5 * S, py + 1.5 * S, 0.76, pz0, pz1, side="copper_side")
    d.box(lf, "pipe_r", pxr - 1.5 * S, pxr + 1.5 * S, py + 1.5 * S, cyl[2], pz0, pz1, side="copper_side")
    det = d.detail(lf)
    for k, (jx, jy) in enumerate(((pxl, py), (pxr, py), (pxl, 0.62))):
        d.box(det, "coupling_%d" % k, jx - 2.5 * S, jx + 2.5 * S, jy - 2 * S, jy + 2 * S, pz0, pz1 + S * 0.5,
              side="brass_side")
    d.box(det, "valve", pxl - 2.5 * S, pxl + 2.5 * S, 0.80 - 2.5 * S, 0.80 + 2.5 * S, pz0, pz1, side="brass_side")
    d.box(lf, "cylinder", cyl[0], cyl[1], cyl[2], cyl[3], pz0, cz + 2.5 * S, side="copper_side")
    pist = ds.Bone("piston_0", origin=((rod[0] + rod[1]) / 2, rod[2], cz + 1.25 * S), parent=lf)
    d.box(pist, "piston_rod", rod[0], rod[1], rod[2], rod[3], cz + 0.5 * S, cz + 2 * S, side="iron_side")
    d.box(det, "handle", handle[0] - S, handle[0] + 2 * S, handle[1] - 0.09, handle[1] + 0.09, cz, cz + 2 * S,
          side="brass_side")
    d.box(det, "handle_back", 0.22, 0.32, 0.82, 0.92, -cz - 2 * S, -cz, side="brass_side")
    ds.gear(d, lf, "gear_a_0", ga[0], ga[1], ga[2], cz, "gear_big", "brass_side")
    ds.gear(d, lf, "gear_b_1", gb[0], gb[1], gb[2], cz, "gear_small", "copper_side")
    return d


def main():
    d = build()
    d.export()
    if "--preview" in sys.argv:
        out = os.environ.get("DOOR_PREVIEW", os.path.join(ds.REF_DIR, "..", "doors_out", "small_%s.png" % NAME))
        d.preview(out, refs=[(os.path.join(ds.REF_DIR, "ref4.png"), (1482, 490, 1624, 815)),
                             (os.path.join(ds.REF_DIR, "ref5.png"), (1418, 8, 1574, 226)),
                             (os.path.join(ds.REF_DIR, "ref3.png"), (1140, 26, 1340, 394))])


if __name__ == "__main__":
    main()
