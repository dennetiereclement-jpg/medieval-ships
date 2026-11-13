"""porte_prison (1.31.0): small prison door, 2 high x 1 wide, one leaf hinged on the left.

Reference: ref1 top row 2nd, ref2 top 2nd, ref3 top 2nd, ref5 top 2nd: dark riveted iron (plates with plank-like
seams), a heavy riveted frame, a small barred judas up high lit from inside (glow), riveted bands, a lock box on the
right with a sliding bolt (bolt_0) into a keeper on the right jamb, a pull handle. Back: plates, two cross bands,
the judas bars and a small handle.
Usage: python3 tools/doors/generate_porte_prison.py [--preview]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import doorlib_small as ds  # noqa: E402
from doorlib_small import rgb, shade  # noqa: E402

NAME = "porte_prison"
PLATE, PLATE_D = rgb("3d373b"), rgb("1c181b")
FRAME = rgb("524a4f")
BAND = rgb("4a4347")
BAR = rgb("2a2629")
RIV_L, RIV_D = rgb("a49ca0"), rgb("161214")
RUST = rgb("6a4630")

S = 1 / 32


def build():
    d = ds.Door(NAME, size=256, frame_w=3 * S, sill=2 * S, lintel=4 * S, seed=23)
    F, B = d.F, d.B
    d.material("plate_side", ds.tile_metal(shade(PLATE, 0.9), RUST, 0.03))
    d.material("iron_side", ds.tile_metal(shade(FRAME, 0.85)))
    d.material("bar_side", ds.tile_metal(BAR))
    x0, x1, y0, y1 = d.lx0, d.lx1, d.ly0, d.ly1
    fz0, fz1 = -2 * S, 5 * S
    cz = 2 * S
    wx0, wx1, wy0, wy1 = -7 * S, 7 * S, 1.3125, 1.6875        # the judas (hole through the leaf)
    wf = 2 * S                                                   # its iron surround
    bands = [(1.0625, 1.1875), (0.1875, 0.3125)]
    lock = (5 * S, x1 - S, 0.74, 0.93)                           # lock box
    bolt = (0.28, x1 + 0.0, 0.805, 0.865)                        # bolt bar (slides along x)

    # ---------------------------------------------------------------- pictures
    for C in (F, B):
        C.planks_v(x0, x1, y0, y1, 4, PLATE, PLATE_D, grain=0.05, knots=0, seam=shade(PLATE_D, 0.8))
        for k in range(18):  # scratches / rust specks
            i = C.rng.randint(0, C.w - 1)
            j = C.rng.randint(0, C.h - 1)
            C.put(i, j, shade(RUST, 0.7 + C.rng.random() * 0.2) if k % 3 else shade(PLATE, 1.25))
        C.metal(-0.5, x0, 0, 2, FRAME, noise=12)
        C.metal(x1, 0.5, 0, 2, FRAME, noise=12)
        C.metal(x0, x1, y1, 2, FRAME, noise=12)
        C.metal(x0, x1, 0, y0, shade(FRAME, 0.9), noise=12)
        for xr in (-0.5 + 1.5 * S, 0.5 - 1.5 * S):
            C.rivets_v(xr - S / 2, 0.05, 1.9, 10, light=RIV_L, dark=RIV_D, big=True)
        C.rivets_h(-0.4, 0.4, 2 - 2 * S, 5, light=RIV_L, dark=RIV_D)
        for (b0, b1) in bands:
            C.metal(x0, x1, b0, b1, BAND, noise=10)
            C.rivets_h(x0 + 0.02, x1 - 0.02, (b0 + b1) / 2 + S / 2, 5, light=RIV_L, dark=RIV_D, big=True)
        # judas: surround, lit glass, bars (3 columns x 2 rows)
        C.metal(wx0 - wf, wx1 + wf, wy0 - wf, wy1 + wf, BAND, noise=10)
        for (rx, ry) in ((wx0 - wf / 2, wy0 - wf / 2), (wx1 + wf / 2, wy0 - wf / 2), (wx0 - wf / 2, wy1 + wf / 2),
                         (wx1 + wf / 2, wy1 + wf / 2)):
            C.rivet(rx - S / 2, ry, light=RIV_L, dark=RIV_D)
        C.glow(wx0, wx1, wy0, wy1)
        for bx in (wx0 + (wx1 - wx0) / 3, wx0 + 2 * (wx1 - wx0) / 3):
            C.metal(bx - S, bx + S, wy0, wy1, BAR, noise=6, bevel=False)
            C.fill(bx - S, bx, wy0, wy1, shade(BAR, 1.6))
        C.metal(wx0, wx1, (wy0 + wy1) / 2 - S, (wy0 + wy1) / 2 + S, BAR, noise=6, bevel=False)
        C.fill(wx0, wx1, (wy0 + wy1) / 2, (wy0 + wy1) / 2 + S, shade(BAR, 1.6))
    # front: lock box with keyhole, bolt, keeper, pull handle, vertical strap below the judas
    F.metal(-2 * S, 2 * S, bands[1][1], bands[0][0], BAND, noise=8)
    F.rivets_v(-S / 2, bands[1][1], bands[0][0], 5, light=RIV_L, dark=RIV_D)
    F.metal(lock[0], lock[1], lock[2], lock[3], shade(BAND, 1.1), noise=8)
    F.fill(lock[0] + 2 * S, lock[0] + 3 * S, lock[2] + 1.5 * S, lock[2] + 3.5 * S, (12, 10, 10))
    for (rx, ry) in ((lock[0] + S, lock[2] + S), (lock[0] + S, lock[3] - S), (lock[1] - 1.5 * S, lock[2] + S),
                     (lock[1] - 1.5 * S, lock[3] - S)):
        F.rivet(rx - S / 2, ry, light=RIV_L, dark=RIV_D)
    F.metal(bolt[0], bolt[1], bolt[2], bolt[3], rgb("7c7479"), noise=6)
    F.metal(x1, 0.5, bolt[2] - 2 * S, bolt[3] + 2 * S, shade(FRAME, 1.15), noise=6)        # keeper
    F.metal(bolt[0] + 2 * S, bolt[0] + 3 * S, bolt[3], bolt[3] + 2 * S, rgb("6c6469"), noise=4)  # bolt knob
    hy = 0.52
    F.metal(0.18, 0.22, hy - 0.11, hy + 0.11, BAND, noise=6)
    F.metal(0.24, 0.30, hy - 0.11, hy - 0.08, BAR, noise=4)
    F.metal(0.24, 0.30, hy + 0.08, hy + 0.11, BAR, noise=4)
    F.metal(0.27, 0.30, hy - 0.08, hy + 0.08, shade(BAR, 1.4), noise=4)
    # back: small handle
    B.metal(0.2, 0.3, 0.86, 0.96, BAND, noise=6)

    # ---------------------------------------------------------------- frame cubes
    fr = d.frame
    d.box(fr, "jamb_l", -0.5, x0, 0, 2, fz0, fz1, side="iron_side")
    d.box(fr, "jamb_r", x1, 0.5, 0, 2, fz0, fz1, side="iron_side")
    d.box(fr, "lintel", x0, x1, y1, 2, fz0, fz1, side="iron_side")
    d.box(fr, "sill", x0, x1, 0, y0, fz0, 3 * S, side="iron_side")
    d.box(d.detail(fr), "keeper", x1, 0.5, bolt[2] - 2 * S, bolt[3] + 2 * S, fz1, fz1 + S, side="iron_side")
    for k, y in enumerate((0.3, 1.0, 1.7)):   # hinge knuckles on the left jamb
        d.box(fr, "hinge_%d" % k, x0 - S, x0 + S, y - 3 * S, y + 3 * S, fz1 - S, fz1 + S, side="iron_side",
              front="iron_side")

    # ---------------------------------------------------------------- leaf cubes
    lf = d.leaf
    side = dict(side="plate_side")
    d.box(lf, "plate_bottom", x0, x1, y0, wy0, -cz, cz, **side)
    d.box(lf, "plate_top", x0, x1, wy1, y1, -cz, cz, **side)
    d.box(lf, "plate_left", x0, wx0, wy0, wy1, -cz, cz, **side)
    d.box(lf, "plate_right", wx1, x1, wy0, wy1, -cz, cz, **side)
    d.box(lf, "glow_judas", wx0, wx1, wy0, wy1, -cz + S / 2, cz - S / 2, side="plate_side")
    for zs, tag in ((1, "f"), (-1, "b")):
        z0, z1 = zs * cz, zs * (cz + S)
        # surround of the judas
        d.box(lf, "judas_t_" + tag, wx0 - wf, wx1 + wf, wy1, wy1 + wf, z0, z1, side="iron_side")
        d.box(lf, "judas_d_" + tag, wx0 - wf, wx1 + wf, wy0 - wf, wy0, z0, z1, side="iron_side")
        d.box(lf, "judas_l_" + tag, wx0 - wf, wx0, wy0, wy1, z0, z1, side="iron_side")
        d.box(lf, "judas_r_" + tag, wx1, wx1 + wf, wy0, wy1, z0, z1, side="iron_side")
        for k, bx in enumerate((wx0 + (wx1 - wx0) / 3, wx0 + 2 * (wx1 - wx0) / 3)):
            d.box(lf, "bar_v%d_%s" % (k, tag), bx - S, bx + S, wy0, wy1, zs * (cz - S / 2), z1 * 0.9, side="bar_side")
        d.box(lf, "bar_h_" + tag, wx0, wx1, (wy0 + wy1) / 2 - S, (wy0 + wy1) / 2 + S, zs * (cz - S / 2), z1 * 0.8,
              side="bar_side")
        for k, (b0, b1) in enumerate(bands):
            d.box(lf, "band_%d_%s" % (k, tag), x0, x1, b0, b1, z0, z1, side="iron_side")
    d.box(lf, "strap", -2 * S, 2 * S, bands[1][1], bands[0][0], cz, cz + S, side="iron_side")
    d.box(lf, "lock", lock[0], lock[1], lock[2], lock[3], cz, cz + 2 * S, side="iron_side")
    bolt_b = ds.Bone("bolt_0", origin=((bolt[0] + bolt[1]) / 2, (bolt[2] + bolt[3]) / 2, cz + 2.5 * S), parent=lf)
    d.box(bolt_b, "bolt", bolt[0], bolt[1], bolt[2], bolt[3], cz + 2 * S, cz + 3 * S, side="bar_side")
    d.box(bolt_b, "bolt_knob", bolt[0] + 2 * S, bolt[0] + 3 * S, bolt[3], bolt[3] + 2 * S, cz + 2 * S, cz + 4 * S,
          side="bar_side")
    det = d.detail(lf)
    d.box(det, "handle_plate", 0.18, 0.22, hy - 0.11, hy + 0.11, cz, cz + S, side="iron_side")
    d.box(det, "handle_t", 0.22, 0.30, hy + 0.08, hy + 0.11, cz, cz + 3 * S, side="bar_side")
    d.box(det, "handle_d", 0.22, 0.30, hy - 0.11, hy - 0.08, cz, cz + 3 * S, side="bar_side")
    d.box(det, "handle_v", 0.27, 0.30, hy - 0.08, hy + 0.08, cz + 2 * S, cz + 3 * S, side="bar_side")
    d.box(det, "handle_back", 0.2, 0.3, 0.86, 0.96, -cz - 2 * S, -cz, side="iron_side")
    return d


def main():
    d = build()
    d.export()
    if "--preview" in sys.argv:
        out = os.environ.get("DOOR_PREVIEW", os.path.join(ds.REF_DIR, "..", "doors_out", "small_%s.png" % NAME))
        d.preview(out, refs=[(os.path.join(ds.REF_DIR, "ref1.png"), (204, 186, 322, 440)),
                             (os.path.join(ds.REF_DIR, "ref3.png"), (460, 14, 666, 394)),
                             (os.path.join(ds.REF_DIR, "ref2.png"), (340, 50, 530, 410))])


if __name__ == "__main__":
    main()
