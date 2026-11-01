#!/usr/bin/env python3
"""tente_tissus — Tente du marchand de tissus / Cloth Merchant Tent (reference: scratchpad/ref/tente_tissus_ref.png).

The shared merchant pavilion (merchantlib.pavilion) in teal and beige with the scroll banner, dressed as a cloth
merchant's stall: a tall rack of fabric rolls (cream, blue, lilac, purple, yellow, gold, red) at the back right, a
counter at the back with a pyramid of short bolts and two hanging cloths (red, a teal lattice hanging) behind it, a
narrow shelf of folded cloth at the back left, a rod of hanging cloths (red, lilac, purple with a gold medallion,
cream) along the open left side over the left counter dressed with a rose cloth, folded cloth and spools, a mannequin
in a cream dress at the front left, the right counter under a teal cloth with a gold border and fringe, a teal
curtain at the right front post, two barrels at the front left, crates (Furnish) by the posts.

Usage:  python3 tools/merchant/generate_tente_tissus.py      (MERCHANT_OUT=<file.bbmodel>: only the model, previews)
Tent-local coordinates: y up, +z = the open front, (0, 0, 0) = centre of the footprint at ground level.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402
import props_m3 as pm  # noqa: E402

NAME = "tente_tissus"
UP, v3 = ml.UP, ml.v3


def roll_rack(root, det, L):
    """The tall rack of fabric rolls on the right, behind the teal counter: a low cabinet, a frame at the right end
    and the back, seven rolls lying along x stacked one on the other (their left ends free, as in the picture)."""
    b = ml.Bone("roll_rack", parent=root)
    x0, x1, z0, z1 = 1.05, 2.75, -0.55, 0.15
    top = ml.counter(b, "rack_base", x0, x1, z0, z1, h=0.8, detail=det)
    y0 = top[1]
    zc = (z0 + z1) / 2
    # the frame: two uprights at the right end, one at the back left, a cross bar on top
    for k, (x, z) in enumerate(((x1 - 0.06, z0 + 0.06), (x1 - 0.06, z1 - 0.06), (x0 + 0.1, z0 + 0.06))):
        ml.box(b, "rack_up_%d" % k, (x - 0.05, y0, z - 0.05), (x + 0.05, 2.98, z + 0.05), {"all": "wood_dark", "+2": "end_grain"})
    ml.box(b, "rack_bar_r", (x1 - 0.12, 2.92, z0), (x1 + 0.01, 3.02, z1), "wood_dark", u_dir=v3(0, 0, 1))
    ml.box(b, "rack_bar_back", (x0 + 0.05, 2.9, z0 + 0.01), (x1, 3.0, z0 + 0.11), "wood_dark", u_dir=v3(1, 0, 0))
    ml.box(b, "rack_back", (x0 + 0.05, y0, z0 - 0.02), (x1 - 0.06, 2.9, z0 + 0.01), "plank_dark", u_dir=UP)
    pm.roll_stack(b, "rack_roll", x0 + 0.02, x1 - 0.14, zc + 0.04, y0, ["cream", "blue", "lilac", "purple", "gold", "red"],
                  r=0.12, jitter=0.1, seed=3)
    ml.collide((x0 - 0.05, 0.0, z0 - 0.05, x1 + 0.05, 2.95, z1 + 0.05))
    return b


def back_counter(root, det, L):
    """The back counter: a pyramid of short bolts, folded cloth, spools; two hangings on the back wall above it."""
    b = ml.Bone("back_counter", parent=root)
    x0, x1, z0, z1 = -1.45, 1.05, -2.55, -1.88
    top = ml.counter(b, "back_counter", x0, x1, z0, z1, h=0.95, detail=det)
    y = top[1]
    pm.bolt_pyramid(b, "bolts", -0.42, (z0 + z1) / 2 + 0.05, y, ["yellow", "pink", "purple", "cream", "gold", "lilac", "teal", "red", "yellow"],
                    r=0.085, length=0.46, rows=(5, 4))
    pm.folded_stack(b, "back_fold_l", (-1.15, y, (z0 + z1) / 2), ["cream", "pink", "teal"], w=0.4, d=0.36, yaw=0.08)
    pm.folded_stack(det, "back_fold_r", (0.28, y, (z0 + z1) / 2 + 0.05), ["blue", "lilac"], w=0.3, d=0.32, yaw=-0.15)
    pm.roll(b, "back_roll_0", (0.55, y + 0.145, (z0 + z1) / 2 - 0.08), (1.0, y + 0.145, (z0 + z1) / 2 - 0.02), 0.11, "red")
    pm.roll(det, "back_roll_1", (0.6, y + 0.13, (z0 + z1) / 2 + 0.22), (1.02, y + 0.13, (z0 + z1) / 2 + 0.25), 0.1, "blue")
    # the hangings on a rod against the back wall
    zr = -2.64
    pm.hanging_row(b, det, "back_hang", (-1.35, 2.85, zr), (1.05, 2.85, zr),
                   [("tis_rag_red", 1.0), ("tis_rag_teal", 0.9), ("tis_hanging", 1.05), ("tis_rag_lilac", 0.85)], 1.15, sway=0.02)
    for k, x in enumerate((-1.35, 1.05)):
        ml.beam(det, "back_hang_cord_%d" % k, (x, 2.85, zr), (x, L.eave_y - 0.3, zr), 0.03, "rope")
    return b


def back_left_shelf(root, det, L):
    """A narrow shelf unit of folded cloth at the back left."""
    b = ml.Bone("left_shelf", parent=root)
    x0, x1 = -2.8, -1.65
    levels = ml.shelf_unit(b, "left_shelf", x0, x1, -2.62, -2.12, levels=(0.45, 1.05, 1.65, 2.25), h=2.5, uprights=2, detail=det)
    cols = (["teal", "cream", "red"], ["purple", "lilac"], ["gold", "yellow", "cream"], ["blue", "pink"])
    for k, (lx0, lx1, y, zf, zb) in enumerate(levels):
        zc = (zf + zb) / 2
        pm.folded_stack(b if k % 2 == 0 else det, "shelf_fold_%d" % k, (lx0 + 0.28, y, zc), cols[k], w=0.42, d=0.36, yaw=0.05 * (k - 1))
        if k in (1, 3):
            pm.roll(det, "shelf_roll_%d" % k, (lx1 - 0.46, y + 0.118, zc - 0.12), (lx1 - 0.46, y + 0.118, zc + 0.16), 0.09, cols[k][0])
            pm.roll(det, "shelf_roll_b%d" % k, (lx1 - 0.2, y + 0.118, zc - 0.12), (lx1 - 0.2, y + 0.118, zc + 0.16), 0.09, cols[k][1])
    return b


def left_side(root, det, L):
    """The open left side: a rod of hanging cloths under the eave, the rose cloth over the left counter, folded
    cloth, short bolts and spools on the counters."""
    b = ml.Bone("left_side", parent=root)
    hw, hd = L.half_w, L.half_d
    xr = -hw + 0.32
    pm.hanging_row(b, det, "side_hang", (xr, 2.82, hd - 0.45), (xr, 2.82, -0.2),
                   [("tis_rag_red", 1.0), ("tis_rag_lilac", 0.88), ("tis_rag_purple", 1.0), ("tis_rag_cream", 0.82)], 1.05, sway=0.03)
    for k, z in enumerate((hd - 0.45, -0.2)):
        ml.beam(det, "side_hang_cord_%d" % k, (xr, 2.82, z), (-hw + 0.05, L.eave_y - 0.3, z), 0.03, "rope")
    # the left counter (merchantlib front_counter="left": a front piece and a return along the side)
    y = L.counter_top_y
    side = [c for c in L.counter_boxes if c[0] < -1.5 and (c[5] - c[2]) > 1.2][0]     # the left return (along z)
    front = [c for c in L.counter_boxes if c[3] < 0 and (c[3] - c[0]) > 1.2][0]       # the left front piece
    # the rose cloth over the outer edge of the side return, folded cloth on it
    pm.drape(b, "rose_cloth", side[2] + 0.35, side[5] - 0.15, side[3] - 0.25, side[0] + 0.0, y, 0.62, "tis_cloth_pink", axis="x", nx=3)
    pm.folded_stack(b, "side_fold", ((side[0] + side[3]) / 2 + 0.05, y + 0.03, side[2] + 0.75), ["cream", "cream", "pink"], w=0.36, d=0.44, yaw=0.1)
    pm.roll(det, "side_roll_0", (side[0] + 0.13, y + 0.13, side[2] + 0.12), (side[0] + 0.13, y + 0.13, side[2] + 0.75), 0.1, "red")
    pm.roll(det, "side_roll_1", (side[0] + 0.41, y + 0.13, side[2] + 0.1), (side[0] + 0.41, y + 0.13, side[2] + 0.7), 0.1, "gold")
    # the front piece: short bolts, a folded stack, spools, a pair of shears
    fz = (front[2] + front[5]) / 2
    pm.bolt_pyramid(b, "front_bolts", front[0] + 0.85, fz, y, ["pink", "cream", "lilac", "yellow", "red"], r=0.08, length=0.42, rows=(3, 2))
    pm.folded_stack(b, "front_fold", (front[3] - 0.38, y, fz), ["teal", "purple", "cream"], w=0.4, d=0.34, yaw=-0.12)
    pm.spools(det, "spools", (front[0] + 1.35, y, front[5] - 0.12), ["red", "blue", "yellow", "purple"], step=0.1)
    for k, d in enumerate((v3(1, 0, 0.55), v3(1, 0, -0.55))):
        p = v3(front[0] + 1.42, y + 0.008, fz - 0.05)
        ml.beam(det, "shears_%d" % k, p, p + ml.norm(d) * 0.17, 0.01, "steel", width=0.026, up=UP)
    return b


def right_side(root, det, L):
    """The teal counter at the front right (its own counter: the teal cloth with a gold border and fringe over the
    front and the left end), folded cloth and spools on it, the teal curtain tied at the right front post, crates and
    a basket of offcuts in the back right corner."""
    b = ml.Bone("right_side", parent=root)
    hw, hd = L.half_w, L.half_d
    y = 1.0
    front = ml.counter(b, "teal_counter", 0.85, hw - 0.4, hd - 1.4, hd - 0.68, h=y, detail=det)
    pm.drape(b, "teal_cloth", front[0] + 0.05, front[3] - 0.08, front[2] + 0.05, front[5], y, 0.6, "tis_cloth_teal", axis="z", nx=3)
    pm.drape(b, "teal_cloth_end", front[5] - 0.05, front[2] + 0.08, front[0] + 0.5, front[0], y + 0.004, 0.5, "tis_cloth_teal", axis="x", nx=2)
    fz = (front[2] + front[5]) / 2
    pm.folded_stack(b, "teal_fold", (front[0] + 0.62, y + 0.02, fz), ["cream", "cream"], w=0.46, d=0.38, yaw=0.1)
    pm.folded_stack(det, "teal_fold_b", (front[0] + 1.25, y + 0.02, fz - 0.05), ["gold", "red"], w=0.36, d=0.32, yaw=-0.2)
    pm.spools(det, "spools_r", (front[3] - 0.32, y + 0.02, fz + 0.12), ["teal", "pink", "cream"], step=0.1)
    # the teal curtain at the right front, gathered and tied back to the post
    xc = hw + 0.08
    import wslib_a as wl
    wl.hanging_cloth(b, "curtain_r", (xc, L.eave_y - 0.25, hd - 0.3), (xc, L.eave_y - 0.25, hd - 1.25), 2.6, "tis_rag_teal", sway=0.05, nx=3, ny=3)
    ml.beam(det, "curtain_r_tie", (xc + 0.03, 1.45, hd - 0.3), (xc + 0.03, 1.45, hd - 1.25), 0.05, "trim_gold")
    return b


def front(root, det, L, decor):
    """The front: the mannequin in the cream dress (front left, in front of the counter), two barrels and a crate by
    the left post, crates by the right post."""
    b = ml.Bone("front", parent=root)
    hw, hd = L.half_w, L.half_d
    ml.collide(pm.mannequin(b, det, "mannequin", (-2.3, 0.0, hd + 0.3), yaw=-0.25))
    ml.barrel(b, "barrel_0", (-hw - 0.7, 0.0, hd + 0.55), r=0.4, h=1.02)
    ml.barrel(b, "barrel_1", (-hw - 0.75, 0.0, hd - 0.5), r=0.37, h=0.95)
    # mod crates (Furnish) with a vanilla stand-in
    decor.block("furnish:spruce_crate", -hw + 0.05, 0.0, hd + 0.75, facing="front", scale=0.68, alt="minecraft:barrel", fallback="crate")
    decor.block("furnish:spruce_crate", hw - 0.05, 0.0, hd + 0.78, facing="front", scale=0.82, alt="minecraft:barrel", fallback="crate")
    decor.block("furnish:spruce_crate", hw - 0.05, 0.82, hd + 0.78, facing="neg_x", scale=0.55, alt="minecraft:barrel", fallback="crate",
                solid=False)
    decor.block("furnish:spruce_crate", hw + 0.75, 0.0, hd - 0.45, facing="pos_x", scale=0.8, alt="minecraft:barrel", fallback="crate")
    # the back right corner: a crate, a basket of offcuts on it, a roll leaning on the wall
    decor.block("furnish:spruce_crate", hw - 0.7, 0.0, -hd + 0.62, facing="front", scale=0.85, alt="minecraft:barrel", fallback="crate")
    ml.basket(det, "offcuts", (hw - 0.7, 0.85, -hd + 0.62), r=0.24, h=0.2, content="tis_fab_pink")
    pm.roll(det, "corner_roll", (hw - 0.12, 0.03, -hd + 1.25), (hw + 0.06, 1.5, -hd + 1.15), 0.11, "teal")
    # a roll of cloth leaning against the left front post and a folded cloth on the barrel
    pm.roll(det, "lean_roll", (-hw + 0.35, 0.03, hd + 0.38), (-hw + 0.24, 1.15, hd + 0.25), 0.1, "purple")
    pm.folded_stack(det, "barrel_fold", (-hw - 0.7, 1.045, hd + 0.55), ["red", "cream"], w=0.36, d=0.32, yaw=0.3)
    return b


def build():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="teal")
    pm.register(atlas)
    root = ml.Bone(NAME)
    L = ml.pavilion(root, atlas, emblem="scroll", flag_corner="back_left", side_banners=0, rug=True, lanterns=2,
                    front_counter="left", back_shelves=False, ivy=False)
    det = L.detail
    decor = ml.Decor()
    roll_rack(root, det, L)
    back_counter(root, det, L)
    back_left_shelf(root, det, L)
    left_side(root, det, L)
    right_side(root, det, L)
    front(root, det, L, decor)
    return root, atlas, L, decor


def main():
    root, atlas, L, decor = build()
    ml.export(root, NAME, atlas, decor=decor, icon=dict(colour="teal", emblem="scroll"))


if __name__ == "__main__":
    main()
