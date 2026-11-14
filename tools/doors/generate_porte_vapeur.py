"""porte_vapeur (1.32.0): small steam door, 2 high x 1 wide, one leaf hinged on the left.

Reference: ref4 bottom right (lit porthole with a copper rim and cross bars, copper pipes and a valve on dark planks in a
riveted iron frame), ref5 top 5th (a copper gear with spokes, pipes, a cylinder), ref3 top 4th (brass trim, gears).
Dark wood planks, a brass trim band, a round lit porthole (glow) with a riveted copper rim on both faces and bars going
through the leaf, two gears made of cubes (gear_a_0 big brass, turns clockwise; gear_b_1 small copper, turns the
other way), copper pipes with brass flanges, a valve wheel (handle_0, turns when the door is unlocked), a cylinder with
its piston rod (piston_0), a brass pull handle. Back: planks, two iron battens, the porthole, a small handle.
No cut-out sprite anywhere: every face is opaque (door_audit_small.py).
Usage: python3 tools/doors/generate_porte_vapeur.py [--preview]
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import doorlib_small as ds  # noqa: E402
from doorlib_small import rgb, shade, G  # noqa: E402

NAME = "porte_vapeur"
WOOD, WOOD_DARK = rgb("6c4428"), rgb("26160a")
FRAME = rgb("5c5254")
BRASS, BRASS_L, BRASS_D = rgb("b8802e"), rgb("f0c060"), rgb("5a3410")
COPPER, COPPER_L, COPPER_D = rgb("b4602e"), rgb("ee9a5c"), rgb("5c2612")
RIV_L, RIV_D = rgb("f0c070"), rgb("3a2008")
IRON_RIV_L, IRON_RIV_D = rgb("b0a8a8"), rgb("1c1618")

P = 1 / 32


def pipe_paint(C, x0, x1, y0, y1, vertical):
    C.fill(x0, x1, y0, y1, COPPER, noise=6)
    if vertical:
        C.fill(x0, x0 + P, y0, y1, COPPER_L)
        C.fill(x1 - P, x1, y0, y1, COPPER_D)
    else:
        C.fill(x0, x1, y1 - P, y1, COPPER_L)
        C.fill(x0, x1, y0, y0 + P, COPPER_D)


def valve_wheel(d, parent, name, cx, cy, zbase):
    """Brass valve wheel (bone `name`, turns about z): boss on the pipe, octagonal rim, two crossed spokes."""
    sh = d.sheet(name, cx - 5 * P, cx + 5 * P, cy - 5 * P, cy + 5 * P)
    sh.fill(sh.X0, sh.X1, sh.Y0, sh.Y1, BRASS_L, noise=6)          # rim: light brass, darker lower right
    sh.fill(cx, cx + 4 * P, cy - 4 * P, cy, shade(BRASS_L, 0.82))
    sh.fill(cx - 2 * P, cx + 2 * P, cy - 2 * P, cy + 2 * P, BRASS_D)  # (the hole: never drawn)
    sh.fill(cx - 0.5 * P, cx + 0.5 * P, cy - 2.5 * P, cy + 2.5 * P, BRASS)
    sh.fill(cx - 2.5 * P, cx + 2.5 * P, cy - 0.5 * P, cy + 0.5 * P, BRASS)
    sh.metal(cx - P, cx + P, cy - P, cy + P, shade(BRASS_D, 1.3), noise=4)
    sh.put(*sh.pix(cx - P / 2, cy + P / 2), c=BRASS_L)
    b = d.part(name, (cx, cy, zbase), parent)
    d.relief(b, name + "_boss", cx - P, cx + P, cy - P, cy + P, zbase, 2 * P + 3 * G, "brass_side", face=name)
    za = zbase + P
    ro, ri = 3.5, 2.0

    def rb(nm, a0, a1, b0, b1, dz=0.0, th=P):
        d.box(b, name + nm, cx + a0 * P, cx + a1 * P, cy + b0 * P, cy + b1 * P, za + dz, za + dz + th,
              side="brass_side", front=name, back=name)
    c = ri + 0.5
    rb("_rim_t", -c + 0.5, c - 0.5, ri, ro)
    rb("_rim_d", -c + 0.5, c - 0.5, -ro, -ri)
    rb("_rim_l", -ro, -ri, -c + 0.5, c - 0.5)
    rb("_rim_r", ri, ro, -c + 0.5, c - 0.5)
    for k, (sx, sy) in enumerate(((-1, 1), (1, 1), (-1, -1), (1, -1))):
        a0, a1 = sorted((sx * (ri - 1), sx * (ro - 1)))
        b0, b1 = sorted((sy * (ri - 1), sy * (ro - 1)))
        rb("_rim_c%d" % k, a0, a1, b0, b1, dz=G)
    # four spokes from the boss to the rim (they do not cross: no coplanar faces)
    rb("_spoke_r", 1, ri + 0.5, -0.5, 0.5, dz=G)
    rb("_spoke_l", -(ri + 0.5), -1, -0.5, 0.5, dz=G)
    rb("_spoke_u", -0.5, 0.5, 1, ri + 0.5, dz=G)
    rb("_spoke_d", -0.5, 0.5, -(ri + 0.5), -1, dz=G)
    return b


def build():
    d = ds.Door(NAME, size=256, sill=2 * P, lintel=3 * P, cz=2 * P, seed=37)
    F, B = d.F, d.B
    d.material("wood_side", ds.tile_wood(shade(WOOD, 0.9), WOOD_DARK))
    d.material("iron_side", ds.tile_metal(shade(FRAME, 0.85)))
    d.material("iron_in", ds.tile_metal(shade(FRAME, 0.6)))
    d.material("brass_side", ds.tile_metal(shade(BRASS, 0.85)))
    d.material("copper_side", ds.tile_metal(shade(COPPER, 0.9)))
    d.material("rod_side", ds.tile_metal(rgb("c8c0b8")))
    x0, x1, y0, y1, cz = d.lx0, d.lx1, d.ly0, d.ly1, d.cz
    vx0, vx1, vy0, vy1 = d.vx0 + G, d.vx1 - G, d.vy0 + G, d.vy1 - G
    pc = (0.0, 1.52)                      # porthole centre
    hh = 5 * P                            # half size of the lit square hole
    ga = (0.0, 1.0)                       # big gear centre (body radius 5 px)
    gb = (ga[0] - 0.42 * math.cos(math.radians(65)), ga[1] - 0.42 * math.sin(math.radians(65)))
    gb = (round(gb[0] * 64) / 64, round(gb[1] * 64) / 64)
    py, pxl, pxr = 0.24, -0.27, 0.27      # bottom pipe, left / right vertical pipes
    pw = 1.5 * P
    cyl = (pxr - 2.5 * P, pxr + 2.5 * P, 0.40, 0.60)
    rod = (pxr - P, pxr + P, 0.33, 0.63)   # its foot stays buried in the pipe / cylinder over the whole stroke
    ltop = 0.42                           # top of the left pipe (under the small gear)
    hd = (0.31, 1.12)                     # pull handle
    band = (vy1 - 2 * P, vy1)

    # ---------------------------------------------------------------- pictures
    ds.frame_picture(d.FF, FRAME, rgb("2a2426"), IRON_RIV_L, IRON_RIV_D, x0, x1, y0, y1, rivets=9)
    ds.frame_picture(d.FB, shade(FRAME, 0.92), rgb("2a2426"), IRON_RIV_L, IRON_RIV_D, x0, x1, y0, y1, rivets=8,
                     big=False)
    for k, y in enumerate((0.35, 1.0, 1.65)):
        d.FF.metal(-0.5 + 2 * P, x0 + ds.LIP - G, y - 3 * P, y + 3 * P, BRASS, noise=6)
        d.FF.fill(-0.5 + 2 * P, x0 + ds.LIP - G, y - 0.5 * P, y + 0.5 * P, BRASS_D)
    for C, wood in ((F, WOOD), (B, shade(WOOD, 0.9))):
        C.planks_v(x0, x1, y0, y1, 4, wood, WOOD_DARK, knots=2)
        # porthole: copper rim (stepped circle), lit glass, rivets
        C.disc(pc[0], pc[1], 8.6 * P, COPPER, noise=8, ring=(1, COPPER_D))
        C.disc(pc[0] - P / 2, pc[1] + P / 2, 7 * P, COPPER_L)
        C.disc(pc[0], pc[1], 6.6 * P, COPPER)
        C.fill(pc[0] - hh, pc[0] + hh, pc[1] - hh, pc[1] + hh, (0, 0, 0))
        C.glow(pc[0] - hh, pc[0] + hh, pc[1] - hh, pc[1] + hh)
        for a in range(8):
            ang = a * math.pi / 4 + math.pi / 8
            C.rivet(pc[0] + 6.6 * P * math.cos(ang) - P / 2, pc[1] + 6.6 * P * math.sin(ang) + P / 2,
                    light=RIV_L, dark=RIV_D)
        C.disc(pc[0], pc[1] - 9.5 * P, 6 * P, shade(wood, 0.62))     # shadow under the rim
        C.disc(pc[0], pc[1], 8.6 * P, COPPER, ring=(1, COPPER_D))
        C.disc(pc[0] - P / 2, pc[1] + P / 2, 7 * P, COPPER_L)
        C.disc(pc[0], pc[1], 6.6 * P, COPPER)
        C.glow(pc[0] - hh, pc[0] + hh, pc[1] - hh, pc[1] + hh)
        for a in range(8):
            ang = a * math.pi / 4 + math.pi / 8
            C.rivet(pc[0] + 6.8 * P * math.cos(ang) - P / 2, pc[1] + 6.8 * P * math.sin(ang) + P / 2,
                    light=RIV_L, dark=RIV_D)
    # front: brass trim band, pipes, flanges, cylinder, handle plate, shadows of the gears
    F.metal(vx0, vx1, band[0], band[1], BRASS, noise=8)
    F.rivets_h(vx0 + 0.02, vx1 - 0.02, (band[0] + band[1]) / 2 + P / 2, 5, light=RIV_L, dark=RIV_D)
    F.disc(ga[0] + P, ga[1] - P, 8.5 * P, shade(WOOD, 0.55))
    F.disc(gb[0] + P, gb[1] - P, 5 * P, shade(WOOD, 0.55))
    pipe_paint(F, pxl - pw, pxl + pw, py + pw, ltop, True)
    pipe_paint(F, pxr - pw, pxr + pw, py + pw, cyl[2], True)
    pipe_paint(F, pxl - pw, pxr + pw, py - pw, py + pw, False)
    for (jx, jy) in ((pxl, py), (pxr, py)):
        F.metal(jx - 2.5 * P, jx + 2.5 * P, jy - 2.5 * P, jy + 2.5 * P, BRASS, noise=6)
        F.rivet(jx - P / 2, jy + P / 2, light=RIV_L, dark=RIV_D)
    F.metal(pxl - 2 * P, pxl + 2 * P, ltop - P, ltop + 0.5 * P, BRASS_L, noise=4)
    F.metal(cyl[0], cyl[1], cyl[2], cyl[3], COPPER, noise=8)
    F.fill(cyl[0], cyl[0] + P, cyl[2], cyl[3], COPPER_L)
    F.fill(cyl[1] - P, cyl[1], cyl[2], cyl[3], COPPER_D)
    for yb in (cyl[2] + 2 * P, cyl[3] - 2 * P):
        F.metal(cyl[0], cyl[1], yb - P, yb, BRASS, noise=4, bevel=False)
    F.metal(hd[0] - 1.5 * P, hd[0] + 1.5 * P, hd[1] - 0.12, hd[1] + 0.12, BRASS_D, noise=4)
    F.metal(hd[0] - 0.5 * P, hd[0] + 0.5 * P, hd[1] - 0.09, hd[1] + 0.09, BRASS_L, noise=4, bevel=False)
    # back: iron battens + small handle plate
    battens = [(1.08, 1.18), (0.30, 0.40)]
    for (b0, b1) in battens:
        B.metal(x0, x1, b0, b1, FRAME, noise=10)
        B.rivets_h(x0 + 0.08, x1 - 0.04, (b0 + b1) / 2 + P / 2, 4, light=IRON_RIV_L, dark=IRON_RIV_D)
        B.fill(x0, x1, b0 - P, b0, shade(WOOD, 0.55))
    B.metal(0.22, 0.32, 0.78, 0.92, BRASS, noise=6)

    # ---------------------------------------------------------------- frame
    d.build_frame("iron_side", inner="iron_in")
    for k, y in enumerate((0.35, 1.0, 1.65)):
        d.relief(d.frame, "hinge_%d" % k, -0.5 + 2 * P, x0 + ds.LIP - G, y - 3 * P, y + 3 * P, d.zf, P, "brass_side",
                 face="ffront")

    # ---------------------------------------------------------------- leaf
    lf = d.leaf
    d.core("wood_side", hole=(pc[0] - hh, pc[0] + hh, pc[1] - hh, pc[1] + hh))
    d.box(lf, "glow_porthole", pc[0] - hh, pc[0] + hh, pc[1] - hh, pc[1] + hh, -cz + G, cz - G, side="copper_side")
    d.box(lf, "bar_v", pc[0] - 0.5 * P, pc[0] + 0.5 * P, pc[1] - hh - P, pc[1] + hh + P, -cz - G, cz + G,
          side="copper_side", front="copper_side", back="copper_side")
    d.box(lf, "bar_h", pc[0] - hh - P, pc[0] + hh + P, pc[1] - 0.5 * P, pc[1] + 0.5 * P, -cz - 3 * G, cz + 3 * G,
          side="copper_side", front="copper_side", back="copper_side")
    for zs, tag in ((1, "f"), (-1, "b")):
        zb = zs * cz
        h = zs * 2 * P
        X, Y = pc
        d.relief(lf, "rim_t_" + tag, X - 4.5 * P, X + 4.5 * P, Y + hh, Y + 8 * P, zb, h, "copper_side")
        d.relief(lf, "rim_d_" + tag, X - 4.5 * P, X + 4.5 * P, Y - 8 * P, Y - hh, zb, h, "copper_side")
        d.relief(lf, "rim_l_" + tag, X - 8 * P, X - hh, Y - 4.5 * P, Y + 4.5 * P, zb, h, "copper_side")
        d.relief(lf, "rim_r_" + tag, X + hh, X + 8 * P, Y - 4.5 * P, Y + 4.5 * P, zb, h, "copper_side")
        for k, (sx, sy) in enumerate(((-1, 1), (1, 1), (-1, -1), (1, -1))):
            a0, a1 = sorted((X + sx * 3.5 * P, X + sx * 6.5 * P))
            b0, b1 = sorted((Y + sy * 3.5 * P, Y + sy * 6.5 * P))
            z0, z1 = sorted((zb + zs * G, zb + zs * (G + 2 * P)))
            d.box(lf, "rim_c%d_%s" % (k, tag), a0, a1, b0, b1, z0, z1, side="copper_side",
                  front="front" if zs > 0 else None, back="back" if zs < 0 else None)
    d.relief(lf, "band", vx0, vx1, band[0], band[1], cz, P, "brass_side")
    for k, (b0, b1) in enumerate(battens):
        d.relief(lf, "batten_%d" % k, x0, x1, b0, b1, -cz, -P, "iron_side")
    ph = 3 * P
    d.relief(lf, "pipe_h", pxl - pw, pxr + pw, py - pw, py + pw, cz, ph, "copper_side")
    d.relief(lf, "pipe_l", pxl - pw, pxl + pw, py + pw, ltop, cz, ph, "copper_side")
    d.relief(lf, "pipe_r", pxr - pw, pxr + pw, py + pw, cyl[2], cz, ph, "copper_side")
    for k, (jx, jy) in enumerate(((pxl, py), (pxr, py))):
        d.relief(lf, "flange_%d" % k, jx - 2.5 * P, jx + 2.5 * P, jy - 2.5 * P, jy + 2.5 * P, cz, ph + 2 * G,
                 "brass_side")
    d.relief(lf, "pipe_cap", pxl - 2 * P, pxl + 2 * P, ltop - P, ltop + 0.5 * P, cz, ph + G, "brass_side")
    d.relief(lf, "cylinder", cyl[0], cyl[1], cyl[2], cyl[3], cz, 4 * P, "copper_side")
    pist = d.part("piston_0", ((rod[0] + rod[1]) / 2, cyl[3], cz + 2 * P), lf)
    d.box(pist, "piston_rod", rod[0], rod[1], rod[2], rod[3], cz + 1.5 * P, cz + 2.5 * P, side="rod_side",
          front="rod_side", back="rod_side")
    d.relief(lf, "handle_plate", hd[0] - 1.5 * P, hd[0] + 1.5 * P, hd[1] - 0.12, hd[1] + 0.12, cz, P, "brass_side")
    d.relief(lf, "handle_grip", hd[0] - 0.5 * P, hd[0] + 0.5 * P, hd[1] - 0.09, hd[1] + 0.09, cz + P, 2 * P,
             "brass_side")
    d.relief(lf, "handle_back", 0.22, 0.32, 0.78, 0.92, -cz, -2 * P, "brass_side")
    ds.cube_gear(d, lf, "gear_a_0", ga[0], ga[1], 6, cz, "brass_side", BRASS, BRASS_L, rgb("2e1a08"),
                 rgb("3a2412"), spokes=4, cc=4.25)
    ds.cube_gear(d, lf, "gear_b_1", gb[0], gb[1], 3, cz, "copper_side", COPPER, COPPER_L, rgb("2a1006"),
                 rgb("38200e"), spokes=3, tooth_w=1.5, diag=2.0)
    valve_wheel(d, lf, "handle_0", 0.0, py, cz + ph)
    return d


def main():
    d = build()
    d.export()
    if "--preview" in sys.argv:
        out = os.environ.get("DOOR_PREVIEW", os.path.join(ds.REF_DIR, "..", "doors_out2", "small_%s.png" % NAME))
        d.preview(out, refs=[(os.path.join(ds.REF_DIR, "ref4.png"), (1482, 490, 1624, 815)),
                             (os.path.join(ds.REF_DIR, "ref5.png"), (1418, 8, 1574, 226))])


if __name__ == "__main__":
    main()
