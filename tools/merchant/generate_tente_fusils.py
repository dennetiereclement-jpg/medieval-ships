#!/usr/bin/env python3
"""tente_fusils — Tente du vendeur de fusils / Gunsmith Merchant Tent (reference: scratchpad/ref/tente_fusils_ref.png).

The shared merchant pavilion (merchantlib.pavilion) in dark red and beige, the charcoal banner with the crossed
muskets hanging at the front left from a rod propped against the roof, dressed as a gunsmith's stall: a rack of a
dozen muskets and rifles standing along the back (two bays, a bench under them, a rail across), the long counter at
the front under a red runner with gold dags carrying a long rifle on rests, a steampunk revolver with brass gears,
brass bars and cartridges, ammunition boxes on the crate at the front left, a stack of powder barrels outside the
left post, the red curtains tied on both sides, an iron-bound chest and crates at the front right, a powder horn on
the left post, a hanging lantern; the merchant's place is behind the counter.

Usage:  python3 tools/merchant/generate_tente_fusils.py      (MERCHANT_OUT=<file.bbmodel>: only the model, previews)
Tent-local coordinates: y up, +z = the open front, (0, 0, 0) = centre of the footprint at ground level.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402
import props_m4 as pm  # noqa: E402

NAME = "tente_fusils"
UP, v3, X = ml.UP, ml.v3, ml.X
ROOF_RISE = 2.6


def roof_y(L, x, z):
    """Height of the roof's underside above (x, z) (the pavilion's concave pyramid, approximately)."""
    W, D = L.half_w + 0.34, L.half_d + 0.34
    t = min(1.0, max(abs(x) / W, abs(z) / D))
    dd = 0.4 * t + 0.6 * (1 - (1 - t) ** 2)
    return L.apex_y - (L.apex_y - (L.eave_y + 0.02)) * dd - 0.05


def front_banner(shell, det, L):
    """The muskets banner at the front left (the pavilion's centred banner moved there), on a rod with gold caps
    propped against the roof."""
    shell.cubes[:] = [c for c in shell.cubes if not c.name.startswith("banner_front")]
    D = L.half_d + 0.34
    x, y, z = -2.0, L.eave_y + 0.62, D + 0.14
    ml.banner(shell, "banner_front", (x, y, z), 1.38, 2.3, normal=(0, 0, 1), region="m4_banner_dark", rod=False)
    a, b = v3(x - 0.86, y + 0.04, z + 0.02), v3(x + 0.86, y + 0.04, z + 0.02)
    ml.beam(shell, "banner_rod", a, b, 0.14, {"all": "wood", "+1": "end_grain", "-1": "end_grain"})
    for k, p in enumerate((a, b)):
        ml.add_cube(shell, "banner_rod_cap_%d" % k, p + X * (0.06 if k else -0.06), ml.EYE, (0.08, 0.18, 0.18), "gold")
        q = v3(p[0], roof_y(L, p[0], 2.4) + 0.02, 2.4)
        ml.beam(det, "banner_strut_%d" % k, p - UP * 0.04, q, 0.08, "wood_dark")


def gun_rack(root, det, L, decor):
    """The rack along the back: a bench, three uprights, a dark back panel, a top beam and a rail across; six guns
    standing in each bay (muskets and rifles in turn)."""
    b = ml.Bone("gun_rack", parent=root)
    hd = L.half_d
    zb = -hd + 0.18                  # back panel
    x0, x1 = -1.85, 2.65
    bench_h, top_y = 0.95, 2.85
    ml.counter(b, "rack_bench", x0, x1, zb + 0.02, zb + 0.55, h=bench_h, detail=det)
    ml.box(b, "rack_back", (x0, bench_h, zb - 0.05), (x1, top_y, zb), "plank_dark", u_dir=UP)
    xm = (x0 + x1) / 2
    for k, x in enumerate((x0, xm, x1)):
        ml.box(b, "rack_post_%d" % k, (x - 0.09, 0.0, zb - 0.02), (x + 0.09, top_y + 0.12, zb + 0.16), {"all": "wood_dark", "+2": "end_grain"})
    ml.box(b, "rack_top", (x0 - 0.12, top_y, zb - 0.06), (x1 + 0.12, top_y + 0.16, zb + 0.2), "wood", u_dir=X)
    zr = zb + 0.34
    ml.box(b, "rack_rail", (x0 + 0.05, 2.02, zr - 0.04), (x1 - 0.05, 2.12, zr + 0.04), "wood", u_dir=X)
    for k, x in enumerate((x0, xm, x1)):
        ml.box(det, "rack_rail_arm_%d" % k, (x - 0.04, 2.03, zb + 0.14), (x + 0.04, 2.11, zr), "wood_dark")
    ml.box(det, "rack_slot", (x0 + 0.05, bench_h, zr - 0.05), (x1 - 0.05, bench_h + 0.08, zr + 0.05), "wood_dark", u_dir=X)
    n = 6
    for bay, (bx0, bx1) in enumerate(((x0 + 0.24, xm - 0.22), (xm + 0.22, x1 - 0.24))):
        for i in range(n):
            x = bx0 + (bx1 - bx0) * i / (n - 1)
            kind = "rifle" if (i + bay) % 3 == 0 else "musket"
            length = 1.68 if kind == "musket" else 1.58
            pm.rifle(b, det, "rack_gun_%d_%d" % (bay, i), (x, bench_h + 0.09, zr), (0, 1, 0), (1, 0, 0), length=length, kind=kind, w=1.2)
    decor.block("farmhouse_decorations:kerosene_lantern", xm, bench_h, zb + 0.38, facing="front", glow=True, fallback="lantern", solid=False)
    return b


def front_counter(root, det, L):
    """The long counter at the front under the red runner: the long rifle on two rests, the steampunk revolver on
    its stand, brass bars, cartridges."""
    b = ml.Bone("front_counter", parent=root)
    x0, x1, z0, z1 = -1.75, 2.45, 0.85, 1.65
    top = ml.counter(b, "counter", x0, x1, z0, z1, h=1.0, detail=det)
    y = top[1]
    ml.table_cloth(b, "runner", -1.5, 0.75, z0 - 0.05, z1 + 0.05, y, hang=0.85, region="cloth", edge="m4_runner", sides=("front",))
    yc = y + 0.015
    # the long rifle on two rests, its butt over the counter's left end
    for k, x in enumerate((-1.2, 0.2)):
        ml.box(det, "rest_%d" % k, (x - 0.05, yc, 1.2), (x + 0.05, yc + 0.16, 1.32), "wood_dark")
    pm.rifle(b, det, "long_rifle", (-1.95, yc + 0.27, 1.26), (1, 0.05, 0), (0, -1, 0), length=2.5, kind="rifle", w=1.45)
    # the revolver on its dark stand, its long barrel to the right
    ml.box(b, "revolver_stand", (0.85, yc, 1.05), (1.3, yc + 0.18, 1.45), "black_iron")
    pm.revolver(b, det, "revolver", (1.02, yc + 0.16, 1.25), yaw=0.0, s=1.7, long_barrel=0.25)
    # brass bars and ammunition boxes at the back of the counter, cartridges at the right end
    for k in range(3):
        ml.add_cube(b if k == 0 else det, "brass_bar_%d" % k, (1.7 + 0.24 * k, yc + 0.05, 0.98), ml.ry(0.05 * k), (0.24, 0.1, 0.12), "gold_ingot",
                    stretch=True)
    ml.add_cube(det, "brass_bar_3", (1.82, yc + 0.15, 0.98), ml.EYE, (0.24, 0.1, 0.12), "gold_ingot", stretch=True)
    pm.ammo_box(b, "counter_ammo", (1.85, yc, 1.42), size=(0.32, 0.14, 0.22), yaw=0.15)
    pm.cartridges(det, "cartridges", (2.2, yc, 1.05), n=4, step=0.09, h=0.28)
    pm.cartridges(det, "cartridges_b", (2.25, yc, 1.25), n=3, step=0.09, h=0.24)
    # a few gears and springs (small mechanical parts)
    for k, (x, z, s) in enumerate(((0.55, 1.5, 0.12), (0.7, 1.42, 0.09))):
        ml.add_cube(det, "loose_gear_%d" % k, (x, yc + 0.006, z), ml.EYE, (s, 0.008, s), {"all": None, "+2": "m4_gear", "-2": "m4_gear"}, stretch=True)
    return b


def front_sides(root, det, L, decor):
    """Left: the crate with ammunition boxes, the stack of powder barrels outside the left post, the tied curtain,
    the powder horn. Right: the iron-bound chest, the crate at the counter's end, the curtain, the hanging lantern."""
    b = ml.Bone("front_sides", parent=root)
    hw, hd = L.half_w, L.half_d
    # left
    ml.crate(b, "ammo_crate", (-2.25, 0.0, 2.15), size=(0.92, 0.82, 0.8), yaw=0.04)
    pm.ammo_box(b, "ammo_0", (-2.3, 0.82, 2.15), size=(0.5, 0.16, 0.32), yaw=0.08)
    pm.ammo_box(det, "ammo_1", (-2.3, 0.995, 2.12), size=(0.44, 0.14, 0.28), yaw=-0.05)
    ml.barrel(b, "powder_barrel_0", (-3.9, 0.0, 2.35), r=0.45, h=1.02)
    ml.barrel(b, "powder_barrel_1", (-3.82, 1.02, 2.3), r=0.36, h=0.62, solid=False)
    ml.add_cube(det, "powder_barrel_1_lid", (-3.82, 1.65, 2.3), ml.EYE, (0.5, 0.03, 0.5), "black_iron")
    ml.barrel(b, "powder_barrel_2", (-3.75, 0.0, 1.45), r=0.36, h=0.85)
    x = -hw - 0.22
    pm.curtain(b, "curtain_l", (x, L.eave_y - 0.15, hd - 0.15), (x, L.eave_y - 0.15, hd - 1.2), (x - 0.05, 1.3, hd - 0.45), region="canvas",
               bottom_y=0.03)
    pm.powder_horn(det, "powder_horn", (-2.75, 2.85, hd + 0.02))
    ml.beam(det, "powder_horn_hook", (-2.75, 2.85, hd + 0.02), (-2.75, L.eave_y - 0.32, hd + 0.02), 0.025, "leather")
    # right
    pm.chest(b, det, "chest", (2.35, 0.0, 2.1), size=(0.82, 0.62, 0.56), yaw=-0.06)
    decor.block("furnish:spruce_crate", 2.85, 0.0, 1.2, facing="front", scale=0.78, fallback="crate")
    decor.block("furnish:dark_oak_crate", 2.85, 0.78, 1.2, facing="pos_x", scale=0.55, fallback="crate")
    x = hw + 0.22
    pm.curtain(b, "curtain_r", (x, L.eave_y - 0.15, hd - 1.2), (x, L.eave_y - 0.15, hd - 0.15), (x + 0.05, 1.3, hd - 0.45), region="canvas",
               bottom_y=0.03)
    ml.lantern(b, "lamp_in", (2.35, 2.55, 0.35), size=0.3, chain_to=(2.35, roof_y(L, 2.35, 0.35), 0.35))
    # inside: a lying powder barrel in the back left corner, the tool board on the left wall
    decor.block("landsoficaria:cypress_barrel", -2.55, 0.0, -0.9, facing="front", alt="minecraft:barrel", fallback="barrel")
    decor.block("farmhouse_decorations:tool_board", -2.75, 1.55, -1.0, facing="pos_x", fallback="plank_dark", solid=False)
    return b


def main():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="darkred", banner_colour="charcoal")
    pm.register(atlas, "fusils")
    root = ml.Bone(NAME)
    L = ml.pavilion(root, atlas, emblem="muskets", flag_corner="back_left", side_banners=0, rug=False, lanterns=2, front_counter=False,
                    back_shelves=False, roof_rise=ROOF_RISE)
    shell, det = L.shell, L.detail
    front_banner(shell, det, L)
    decor = ml.Decor()
    gun_rack(root, det, L, decor)
    front_counter(root, det, L)
    front_sides(root, det, L, decor)
    ml.export(root, NAME, atlas, decor=decor, icon=dict(colour="darkred", emblem="muskets"))


if __name__ == "__main__":
    main()
