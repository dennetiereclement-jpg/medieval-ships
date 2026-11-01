#!/usr/bin/env python3
"""tente_barde — Tente du vendeur de barde / Bard Merchant Tent (reference: scratchpad/ref/tente_barde_ref.png).

The shared merchant pavilion (merchantlib.pavilion) in burgundy and beige with a lower roof, the purple banner with the
gold lyre hanging from a gilded rod above the front valance, dressed as a music shop: a plank back wall with a lute,
mandolins and a fiddle hanging on pegs, a wall shelf, a narrow counter at the back left with flutes and a panpipe,
a low chest with quills and purple vials in the middle, the big golden harp, the right counter under a burgundy cloth
with an open book on a stand (the merchant's place is behind it), a back counter with a music stand and books, the
burgundy and beige curtain tied at the left, a barrel of flutes, the red drum with its gold rope and two natural
drums at the front left, an iron-bound chest at the front right, the purple rug with a gold border, lanterns.

Usage:  python3 tools/merchant/generate_tente_barde.py      (MERCHANT_OUT=<file.bbmodel>: only the model, previews)
Tent-local coordinates: y up, +z = the open front, (0, 0, 0) = centre of the footprint at ground level.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402
import props_m4 as pm  # noqa: E402

NAME = "tente_barde"
UP, v3 = ml.UP, ml.v3
ROOF_RISE = 2.4


def roof_y(L, x, z):
    """Height of the roof's underside above (x, z) (the pavilion's concave pyramid, approximately)."""
    W, D = L.half_w + 0.34, L.half_d + 0.34
    t = min(1.0, max(abs(x) / W, abs(z) / D))
    dd = 0.4 * t + 0.6 * (1 - (1 - t) ** 2)
    return L.apex_y - (L.apex_y - (L.eave_y + 0.02)) * dd - 0.05


def front_banner(shell, det, L):
    """The purple lyre banner: the pavilion's centred one replaced by a longer one hanging from a gilded rod set
    above the front valance and propped against the roof (as in the picture)."""
    shell.cubes[:] = [c for c in shell.cubes if not c.name.startswith("banner_front")]
    D = L.half_d + 0.34
    y = L.eave_y + 0.95
    z = D + 0.16
    ml.banner(shell, "banner_front", (0, y, z), 1.4, 2.35, normal=(0, 0, 1), rod=False)
    a, b = v3(-0.98, y + 0.04, z + 0.02), v3(0.98, y + 0.04, z + 0.02)
    ml.beam(shell, "banner_rod", a, b, 0.13, {"all": "wood", "+1": "end_grain", "-1": "end_grain"})
    for k, p in enumerate((a, b)):
        ml.add_cube(shell, "banner_rod_cap_%d" % k, p + ml.X * (0.06 if k else -0.06), ml.EYE, (0.08, 0.17, 0.17), "gold")
        q = v3(p[0] * 0.92, roof_y(L, p[0], 2.1) + 0.02, 2.1)
        ml.beam(det, "banner_strut_%d" % k, p - UP * 0.04, q, 0.08, "wood_dark")
        ml.box(det, "banner_band_%d" % k, (p[0] * 0.86 - 0.08, p[1] - 0.07, p[2] - 0.08), (p[0] * 0.86 + 0.08, p[1] + 0.07, p[2] + 0.08), "trim_gold")


def back_wall(root, det, L):
    """A plank wall in front of the back canvas: studs, two rails with pegs; instruments hanging on it (lute,
    mandolins, a fiddle), a narrow wall shelf in the middle with vials and a skull of music sheets."""
    b = ml.Bone("back_wall", parent=root)
    hw, hd = L.half_w, L.half_d
    zb = -hd - 0.1
    ml.box(b, "back_planks", (-hw + 0.18, 0.0, zb - 0.06), (hw - 0.18, L.eave_y - 0.25, zb), "plank", u_dir=UP)
    for k, x in enumerate((-1.15, 1.15)):
        ml.box(b, "back_stud_%d" % k, (x - 0.09, 0.0, zb), (x + 0.09, L.eave_y - 0.25, zb + 0.1), {"all": "wood_dark", "+2": "end_grain"})
    for k, y in enumerate((1.05, 2.85)):
        ml.box(b, "back_rail_%d" % k, (-hw + 0.2, y - 0.07, zb), (hw - 0.2, y + 0.07, zb + 0.08), "wood", u_dir=ml.X)
    zf = zb + 0.12
    # instruments (their bodies' fronts at zf + their depth)
    pm.lute(b, det, "lute_0", (-2.05, 1.8, zf + 0.23), kind="lute", s=1.35, tilt=0.05)
    pm.lute(b, det, "mandolin_0", (-1.32, 1.65, zf + 0.17), kind="mandolin", s=1.15, tilt=-0.08)
    pm.lute(b, det, "fiddle_0", (-0.95, 2.3, zf + 0.12), kind="fiddle", s=0.85, tilt=0.15)
    pm.lute(b, det, "mandolin_1", (2.3, 1.95, zf + 0.17), kind="mandolin", s=1.1, tilt=0.1)
    pm.lute(b, det, "fiddle_1", (1.3, 2.25, zf + 0.12), kind="fiddle", s=0.85, tilt=-0.12)
    # a wall shelf in the middle (behind the banner): vials, music sheets
    sy = 1.55
    ml.box(b, "wall_shelf", (-0.75, sy - 0.05, zb), (0.3, sy, zb + 0.32), "plank", u_dir=ml.X)
    for k, x in enumerate((-0.7, 0.25)):
        ml.beam(det, "wall_shelf_bracket_%d" % k, (x, sy - 0.3, zb + 0.02), (x, sy - 0.05, zb + 0.28), 0.05, "wood_dark")
    for k, (x, c) in enumerate(((-0.62, "purple"), (-0.48, "purple"), (-0.36, "blue"), (0.08, "purple"), (0.2, "red"))):
        ml.bottle(det, "shelf_vial_%d" % k, (x, sy, zb + 0.17), colour=c, r=0.045, h=0.13, shape="round" if k % 2 else "tall")
    pm.book_row(det, "shelf_books", -0.26, 0.0, sy, zb + 0.15, h=0.24, depth=0.2)
    return b


def left_counter(root, det, L):
    """The narrow counter at the back left: flutes and a panpipe lying on it, a small shelf above with sheets."""
    b = ml.Bone("left_counter", parent=root)
    x0, x1, z0, z1 = -2.8, -1.0, -1.25, -0.6
    top = ml.counter(b, "left_counter", x0, x1, z0, z1, h=0.95, detail=det)
    y = top[1]
    zc = (z0 + z1) / 2
    # a long recorder on two small rests, two short flutes
    for k, x in enumerate((-2.45, -1.55)):
        ml.box(det, "flute_rest_%d" % k, (x - 0.05, y, zc - 0.05), (x + 0.05, y + 0.08, zc + 0.05), "wood_dark")
    ml.beam(b, "long_flute", (-2.65, y + 0.12, zc), (-1.3, y + 0.12, zc - 0.03), 0.06, "m4_flute", stretch=True)
    ml.beam(det, "short_flute_0", (-2.3, y + 0.03, z1 - 0.12), (-1.85, y + 0.03, z1 - 0.06), 0.045, "m4_flute", stretch=True)
    ml.beam(det, "short_flute_1", (-1.75, y + 0.03, z1 - 0.1), (-1.3, y + 0.03, z1 - 0.16), 0.045, "m4_flute", stretch=True)
    # a panpipe: reeds of decreasing length tied side by side
    for k in range(6):
        h = 0.3 - k * 0.035
        x = -2.62 + k * 0.05
        ml.add_cube(det, "panpipe_%d" % k, (x, y + h / 2 + 0.01, z0 + 0.18), ml.EYE, (0.045, h, 0.045), "m4_flute", stretch=True)
    ml.box(det, "panpipe_tie", (-2.66, y + 0.17, z0 + 0.15), (-2.33, y + 0.21, z0 + 0.21), "leather")
    pm.book(b, "left_book", (-1.2, y, z0 + 0.25), size=(0.22, 0.05, 0.3), yaw=0.2, cover="m4_cover_blue")
    ml.plate(det, "left_score", (-1.55, y + 0.012, z0 + 0.2), 0.26, 0.32, "m4_score", normal=(0, 1, 0), up=(0, 0, -1), th=0.004)
    return b


def middle(root, det, L):
    """The low chest in the middle (quills in ink pots, purple vials, a book pile) and the golden harp."""
    b = ml.Bone("middle", parent=root)
    cz = -0.45
    pm.chest(b, det, "mid_chest", (-0.45, 0.0, cz), size=(1.0, 0.7, 0.55))
    y = 0.7
    for k, x in enumerate((-0.82, -0.6)):
        ml.octo(det, "ink_%d" % k, (x, y, cz + 0.05), 0.06, 0.1, "black_iron")
        pm.flutes(det, "quills_%d" % k, (x, y + 0.08, cz + 0.05), n=3, r=0.03, length=0.5, spread=0.22, seed=3 + k, feather=True)
    for k, (x, c) in enumerate(((-0.3, "purple"), (-0.2, "purple"), (-0.1, "pink"))):
        ml.bottle(det, "mid_vial_%d" % k, (x, y, cz + 0.1 + 0.05 * (k % 2)), colour=c, r=0.045, h=0.14, shape="tall")
    pm.harp(b, det, "harp", (1.05, 0.0, -0.6), yaw=0.0, h=1.85)
    return b


def right_side(root, det, L, decor):
    """The right counter under a burgundy cloth with the open book on a low stand; the back counter with a music
    stand and books; the iron-bound chest at the front right; the hanging lantern."""
    b = ml.Bone("right_side", parent=root)
    hw, hd = L.half_w, L.half_d
    x0, x1, z0, z1 = 1.6, 2.85, -0.25, 0.55
    top = ml.counter(b, "right_counter", x0, x1, z0, z1, h=1.0, detail=det)
    y = top[1]
    ml.table_cloth(b, "right_cloth", x0 - 0.06, x1 + 0.06, z0 - 0.06, z1 + 0.06, y, hang=0.55, region="cloth", edge="cloth_hang",
                   sides=("front", "left"))
    # the open book on a low stand
    ml.box(b, "book_stand", (1.98, y + 0.015, -0.02), (2.62, y + 0.1, 0.36), "wood_dark")
    pm.open_book(b, det, "open_book", (2.3, y + 0.24, 0.2), normal=(0, 0.7, 0.7), w=0.78, d=0.52)
    pm.book(det, "right_book_0", (1.85, y + 0.015, 0.05), size=(0.2, 0.06, 0.28), yaw=-0.3, cover="m4_cover_green")
    pm.book(det, "right_book_1", (1.85, y + 0.075, 0.05), size=(0.18, 0.05, 0.25), yaw=-0.1, cover="m4_cover_red")
    # back counter: a music stand with a sheet, books
    bx0, bx1, bz0, bz1 = 0.95, 2.75, -2.62, -1.95
    btop = ml.counter(b, "back_counter", bx0, bx1, bz0, bz1, h=0.95, detail=det)
    by = btop[1]
    c, n = pm.lectern(b, det, "music_stand", (1.35, by, -2.25), yaw=0.0, h=0.55)
    ml.plate(det, "music_stand_sheet", c + n * 0.01, 0.4, 0.3, "m4_score", normal=n, up=ml.np.cross(n, ml.X) * -1, th=0.004)
    pm.book_row(det, "back_books", 1.75, 2.45, by, -2.42, h=0.3, depth=0.22)
    pm.book(det, "back_book_flat", (2.15, by, -2.08), size=(0.24, 0.07, 0.3), yaw=0.15, cover="m4_cover_red")
    # the iron-bound chest at the front right (beside the counter)
    pm.chest(b, det, "front_chest", (2.45, 0.0, 1.75), size=(0.78, 0.62, 0.56), yaw=-0.08)
    # the hanging lantern inside, right of the harp, and a mandolin hanging on a string beside it
    ml.lantern(b, "lamp_in", (2.0, 2.62, -0.75), size=0.3, chain_to=(2.0, roof_y(L, 2.0, -0.75), -0.75))
    pm.lute(b, det, "mandolin_hang", (2.7, 2.05, -0.9), kind="mandolin", s=1.0, tilt=0.12, peg_hook=False)
    ml.beam(det, "mandolin_hang_string", (2.7, 2.5, -0.92), (2.7, roof_y(L, 2.7, -0.92), -0.92), 0.02, "rope")
    decor.block("farmhouse_decorations:kerosene_lantern", 1.72, y, 0.35, facing="front", glow=True, fallback="lantern", solid=False)
    decor.block("farmhouse_decorations:pile_of_books", 2.35, by, -2.12, facing="front", fallback="m4_spines", solid=False)
    return b


def front_left(root, det, L, decor):
    """The burgundy and beige curtain tied at the left, a barrel of flutes beside the left post, the red drum with
    the gold rope, two natural drums (one on a crate)."""
    b = ml.Bone("front_left", parent=root)
    hw, hd = L.half_w, L.half_d
    x = -hw - 0.22
    pm.curtain(b, "curtain_l", (x, L.eave_y - 0.15, hd - 0.15), (x, L.eave_y - 0.15, hd - 1.15), (x - 0.05, 1.25, hd - 0.4), region="canvas",
               bottom_y=0.03)
    pm.curtain(det, "curtain_l2", (x + 0.04, L.eave_y - 0.15, hd - 1.1), (x + 0.04, L.eave_y - 0.15, hd - 1.75), (x - 0.02, 1.3, hd - 0.65),
               region="beige", bottom_y=0.03, nx=2)
    ml.barrel(b, "flute_barrel", (-3.72, 0.0, 2.6), r=0.36, h=0.88)
    pm.flutes(det, "barrel_flutes", (-3.72, 0.8, 2.6), n=6, r=0.2, length=0.75, spread=0.08, seed=5, feather=True)
    pm.drum(b, det, "drum_red", (-2.0, 0.0, 2.3), r=0.5, h=0.95, kind="red")
    pm.drum(b, det, "drum_nat_0", (-1.2, 0.0, 1.5), r=0.36, h=0.62, kind="nat")
    decor.block("furnish:spruce_crate", -1.15, 0.0, 2.5, facing="front", scale=0.62, fallback="crate")
    pm.drum(det, det, "drum_nat_1", (-1.15, 0.62, 2.5), r=0.27, h=0.26, kind="nat", top_hoop=False)
    # a guitar leaning in the back left corner (the mod's acoustic guitar), a crate beside the left counter
    decor.block("farmhouse_decorations:acoustic_guitar", -2.55, 0.0, -2.35, facing="front", fallback="m4_guitar")
    decor.block("furnish:spruce_crate", -2.55, 0.0, 0.15, facing="front", scale=0.7, fallback="crate")
    return b


def main():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="burgundy", banner_colour="purple", rug_colour="purple")
    pm.register(atlas, "barde")
    root = ml.Bone(NAME)
    L = ml.pavilion(root, atlas, emblem="lyre", flag_corner="back_left", side_banners=0, rug=False, lanterns=2, front_counter=False,
                    back_shelves=False, roof_rise=ROOF_RISE)
    shell, det = L.shell, L.detail
    front_banner(shell, det, L)
    decor = ml.Decor()
    back_wall(root, det, L)
    left_counter(root, det, L)
    middle(root, det, L)
    right_side(root, det, L, decor)
    front_left(root, det, L, decor)
    ml.rug(shell, "rug", -0.6, 2.4, 0.95, 3.35, y=0.0)
    ml.export(root, NAME, atlas, decor=decor, icon=dict(colour="burgundy", emblem="lyre"))


if __name__ == "__main__":
    main()
