"""porte_prison (1.32.0): small prison door, 2 high x 1 wide, one leaf hinged on the left.

Reference: ref1 top row 2nd, ref2 top 2nd, ref3 top 2nd, ref5 top 2nd: dark riveted iron (plates with seams), a heavy
riveted frame, a barred judas up high lit from inside (glow) with a riveted surround on both faces, riveted bands, a
lock plate with a sliding bolt (bolt_0) facing a keeper on the right jamb, a small ring handle (handle_0).
The bars go through the whole leaf (seen from both faces); the frame is rebated (doorlib_small.Door.build_frame).
bolt_0: its pivot is left of the middle of the leaf on purpose, so that the renderer slides it to the LEFT, out of the
keeper, when the door opens (DoorModels: a bolt left of the middle moves -x).
Usage: python3 tools/doors/generate_porte_prison.py [--preview]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import doorlib_small as ds  # noqa: E402
from doorlib_small import rgb, shade, G  # noqa: E402

NAME = "porte_prison"
PLATE, PLATE_D = rgb("3e383c"), rgb("1c181b")
FRAME = rgb("544c51")
BAND = rgb("4c4549")
BAR = rgb("2a2629")
RIV_L, RIV_D = rgb("aaa2a6"), rgb("161214")
RUST = rgb("6a4630")

S = 1 / 32


def build():
    d = ds.Door(NAME, size=256, sill=2 * S, lintel=4 * S, cz=2 * S, seed=23)
    F, B = d.F, d.B
    d.material("plate_side", ds.tile_metal(shade(PLATE, 0.9), RUST, 0.03))
    d.material("iron_side", ds.tile_metal(shade(FRAME, 0.85)))
    d.material("iron_in", ds.tile_metal(shade(FRAME, 0.6)))
    d.material("bar_side", ds.tile_metal(BAR))
    d.material("bolt_side", ds.tile_metal(rgb("858086")))
    x0, x1, y0, y1, cz = d.lx0, d.lx1, d.ly0, d.ly1, d.cz
    vx0, vx1 = d.vx0 + G, d.vx1 - G
    hx0, hx1, hy0, hy1 = -6 * S, 6 * S, 1.3125, 1.6875     # the judas (hole through the leaf)
    wf = 2 * S                                             # its riveted surround
    bands = [(1.0625, 1.1875), (0.1875, 0.3125)]
    lock = (0.0, vx1, 0.70, 0.92)
    bolt = (0.19, vx1, 0.795, 0.825)
    bar_x = [(-10 / 3) * S, 0.0, (10 / 3) * S]
    bar_w = (2 / 3) * S
    hc = (hy0 + hy1) / 2

    # ---------------------------------------------------------------- pictures
    ds.frame_picture(d.FF, FRAME, PLATE_D, RIV_L, RIV_D, x0, x1, y0, y1, rivets=10)
    ds.frame_picture(d.FB, shade(FRAME, 0.92), PLATE_D, RIV_L, RIV_D, x0, x1, y0, y1, rivets=10)
    for C in (F, B):
        C.planks_v(x0, x1, y0, y1, 3, PLATE, PLATE_D, grain=0.05, knots=0, seam=shade(PLATE_D, 0.8))
        for k in range(26):  # scratches / rust specks
            i = C.rng.randint(0, C.w - 1)
            j = C.rng.randint(0, C.h - 1)
            C.put(i, j, shade(RUST, 0.7 + C.rng.random() * 0.2) if k % 3 else shade(PLATE, 1.25))
        for (b0, b1) in bands:
            C.metal(x0, x1, b0, b1, BAND, noise=10)
            C.rivets_h(x0 + 0.06, x1 - 0.04, (b0 + b1) / 2 + S / 2, 5, light=RIV_L, dark=RIV_D, big=True)
            C.fill(x0, x1, b0 - S, b0, shade(PLATE, 0.6))
        C.metal(hx0 - wf, hx1 + wf, hy0 - wf, hy1 + wf, BAND, noise=10)
        for (rx, ry) in ((hx0 - wf / 2, hy0 - wf / 2), (hx1 + wf / 2, hy0 - wf / 2), (hx0 - wf / 2, hy1 + wf / 2),
                         (hx1 + wf / 2, hy1 + wf / 2), (0, hy1 + wf / 2), (0, hy0 - wf / 2)):
            C.rivet(rx - S / 2, ry + S / 2, light=RIV_L, dark=RIV_D)
        C.glow(hx0, hx1, hy0, hy1)
        C.fill(hx0 - wf, hx1 + wf, hy0 - wf - S, hy0 - wf, shade(PLATE, 0.55))
    # front: lock plate with keyhole and rivets, keeper on the frame
    F.metal(lock[0], lock[1], lock[2], lock[3], shade(BAND, 1.12), noise=8)
    F.fill(lock[0] + 3 * S, lock[0] + 4 * S, lock[2] + 1.5 * S, lock[2] + 3.5 * S, (12, 10, 10))
    F.fill(lock[0] + 2.5 * S, lock[0] + 4.5 * S, lock[2] + 3 * S, lock[2] + 4 * S, (12, 10, 10))
    for (rx, ry) in ((lock[0] + S, lock[2] + S), (lock[0] + S, lock[3] - S), (lock[1] - 1.5 * S, lock[2] + S),
                     (lock[1] - 1.5 * S, lock[3] - S)):
        F.rivet(rx - S / 2, ry + S / 2, light=RIV_L, dark=RIV_D)
    F.fill(lock[0], lock[1], lock[2] - S, lock[2], shade(PLATE, 0.55))
    keeper = (x1 - ds.LIP, 0.5 - 2 * S, bolt[2] - 2 * S, bolt[3] + 2 * S)
    d.FF.metal(keeper[0], keeper[1], keeper[2], keeper[3], shade(FRAME, 1.2), noise=6)
    d.FF.fill(keeper[0], keeper[0] + S, bolt[2], bolt[3], (14, 12, 12))
    for k, y in enumerate((0.32, 1.0, 1.68)):   # hinge knuckles on the left jamb
        d.FF.metal(-0.5 + 2 * S, x0 + ds.LIP - G, y - 3 * S, y + 3 * S, shade(FRAME, 1.15), noise=6)

    # ---------------------------------------------------------------- frame
    d.build_frame("iron_side", inner="iron_in")
    d.relief(d.frame, "keeper", keeper[0], keeper[1], keeper[2], keeper[3], d.zf, 1.5 * S, "iron_side", face="ffront")
    for k, y in enumerate((0.32, 1.0, 1.68)):
        d.relief(d.frame, "hinge_%d" % k, -0.5 + 2 * S, x0 + ds.LIP - G, y - 3 * S, y + 3 * S, d.zf, S, "iron_side",
                 face="ffront")

    # ---------------------------------------------------------------- leaf
    lf = d.leaf
    d.core("plate_side", hole=(hx0, hx1, hy0, hy1))
    d.box(lf, "glow_judas", hx0, hx1, hy0, hy1, -cz + G, cz - G, side="plate_side")
    for k, bx in enumerate(bar_x):   # through the whole leaf, ends buried in the core
        d.box(lf, "bar_v%d" % k, bx - bar_w, bx + bar_w, hy0 - S, hy1 + S, -cz - G, cz + G, side="bar_side",
              front="bar_side", back="bar_side")
    d.box(lf, "bar_h", hx0 - S, hx1 + S, hc - bar_w, hc + bar_w, -cz - 3 * G, cz + 3 * G, side="bar_side",
          front="bar_side", back="bar_side")
    for zs, tag in ((1, "f"), (-1, "b")):
        zb = zs * cz
        h = zs * S
        d.relief(lf, "judas_t_" + tag, hx0 - wf, hx1 + wf, hy1, hy1 + wf, zb, h, "iron_side")
        d.relief(lf, "judas_d_" + tag, hx0 - wf, hx1 + wf, hy0 - wf, hy0, zb, h, "iron_side")
        d.relief(lf, "judas_l_" + tag, hx0 - wf, hx0, hy0, hy1, zb, h, "iron_side")
        d.relief(lf, "judas_r_" + tag, hx1, hx1 + wf, hy0, hy1, zb, h, "iron_side")
        bx0, bx1 = (vx0, vx1) if zs > 0 else (x0, x1)
        for k, (b0, b1) in enumerate(bands):
            d.relief(lf, "band_%d_%s" % (k, tag), bx0, bx1, b0, b1, zb, h, "iron_side")
    d.relief(lf, "lock", lock[0], lock[1], lock[2], lock[3], cz, 2 * S, "iron_side")
    bolt_b = d.part("bolt_0", (-0.05, (bolt[2] + bolt[3]) / 2, cz + 2.5 * S), lf)
    d.box(bolt_b, "bolt", bolt[0], bolt[1], bolt[2], bolt[3], cz + 2 * S + G, cz + 3 * S + G, side="bolt_side",
          front="bolt_side", back="bolt_side")
    d.box(bolt_b, "bolt_knob", bolt[0] + 2 * S, bolt[0] + 3 * S, bolt[3], bolt[3] + 2 * S, cz + 2 * S + G,
          cz + 3 * S + G, side="bolt_side", front="bolt_side", back="bolt_side")
    ds.ring_handle(d, lf, "handle_0", 0.06, 0.58, cz, "iron_side", s=1, big=False,
                   colours=((170, 162, 166), (92, 84, 88), (34, 30, 32)))
    ds.ring_handle(d, lf, "handle_1", 0.2, 0.86, -cz, "iron_side", s=-1, big=False,
                   colours=((170, 162, 166), (92, 84, 88), (34, 30, 32)))
    return d


def main():
    d = build()
    d.export()
    if "--preview" in sys.argv:
        out = os.environ.get("DOOR_PREVIEW", os.path.join(ds.REF_DIR, "..", "doors_out2", "small_%s.png" % NAME))
        d.preview(out, refs=[(os.path.join(ds.REF_DIR, "ref1.png"), (204, 186, 322, 440)),
                             (os.path.join(ds.REF_DIR, "ref3.png"), (460, 14, 666, 394))])


if __name__ == "__main__":
    main()
