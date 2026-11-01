"""Tente du vendeur d'armures (tente_armures): navy blue and beige pavilion (merchantlib shell), the banner with the
heraldic shield at the front left, four armour stands of different styles (silver knight's plate, gilded fantasy
armour, bulky dark-steel heavy armour with its helm, the soldier's mail and plain breastplate behind the counter),
helmets of six shapes on the back shelf, the counter and the chests, a dark breastplate on the crates at the left,
the big blue shield with the golden eagle leaning at the front, the eagle rug, crates of the decoration mods.

Run: python3 tools/merchant/generate_tente_armures.py (MERCHANT_OUT=<file.bbmodel> for a preview only).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merchantlib as ml  # noqa: E402
import props_m6 as p6  # noqa: E402

NAME = "tente_armures"
v3, UP, EYE, X = ml.v3, ml.UP, ml.EYE, ml.X


def drape(bone, name, x, z0, z1, y_top, y_bot, region, out=-1, n=3, curl=0.05):
    """A side curtain hanging from the eave at x (between z0 and z1), in n gently waving vertical strips."""
    for k in range(n):
        za, zb = z0 + (z1 - z0) * k / n, z0 + (z1 - z0) * (k + 1) / n
        c = v3(x + out * curl * (0.5 + 0.5 * math.sin(k * 2.1)), (y_top + y_bot) / 2, (za + zb) / 2)
        ml.plate(bone, "%s_%d" % (name, k), c, zb - za + 0.04, y_top - y_bot, region, normal=(out, 0, 0.12 * math.sin(k * 1.7 + 0.5)),
                 th=0.02, edge=region)


def main():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="blue", banner_colour="navy")
    p6.add_regions(atlas)
    root = ml.Bone(NAME)
    L = ml.pavilion(root, atlas, emblem="shield", flag_corner="back_left", side_banners=0, rug=False, lanterns=2, front_counter=False,
                    back_shelves=False, eave_y=4.2, roof_rise=2.4)
    shell, det = L.shell, L.detail
    # the right side stays open (trees seen through it on the picture): no canvas wall there
    shell.cubes = [c for c in shell.cubes if not c.name.startswith("wall_side_1")]
    hw, hd, ey = L.half_w, L.half_d, L.eave_y
    # the heraldic banner hangs at the front left (between the left post and the middle), narrower, as on the picture
    shell.cubes = [c for c in shell.cubes if not c.name.startswith("banner_front")]
    ml.banner(shell, "banner_front", (-2.05, ey + 0.12, hd + 0.44), 1.12, 1.78, normal=(0, 0, 1))

    # ---- the wooden lining of the back wall: three panels, two dark posts, a rail
    for k in range(3):
        x0 = -hw + 0.2 + k * (2 * hw - 0.4) / 3
        x1 = x0 + (2 * hw - 0.4) / 3
        ml.box(shell, "lining_%d" % k, (x0, 0.0, -hd - 0.13), (x1, ey - 0.25, -hd - 0.07), {"all": "m6_wall"}, stretch=True, u_dir=X)
    for k, x in enumerate((-1.05, 1.05)):
        ml.box(shell, "lining_post_%d" % k, (x - 0.08, 0.0, -hd - 0.08), (x + 0.08, ey - 0.25, -hd + 0.06),
               {"all": "wood_dark", "+2": "end_grain"})
    ml.box(det, "lining_rail", (-hw + 0.2, 1.02, -hd - 0.08), (hw - 0.2, 1.1, -hd - 0.02), "wood_dark", u_dir=X)

    # ---- the high back shelf with its helmets
    zb, zf = -hd - 0.06, -hd + 0.42
    SY = 2.92
    ml.box(shell, "shelf_top", (-2.4, SY - 0.06, zb), (1.0, SY, zf), "plank", u_dir=X)
    ml.box(det, "shelf_top_lip", (-2.4, SY - 0.1, zf - 0.03), (1.0, SY, zf), "wood_dark", u_dir=X)
    for k, x in enumerate((-2.25, -0.7, 0.85)):
        ml.beam(det, "shelf_top_brace_%d" % k, (x, SY - 0.48, zb + 0.03), (x, SY - 0.1, zf - 0.06), 0.07, "wood_dark")
    for k, (x, kind, metal, s, crest) in enumerate(((-1.9, "armet", "m6_silver", 1.6, None), (-1.2, "bascinet", "m6_silver", 1.3, None),
                                                    (-0.5, "great", "m6_silver", 1.5, "gold"), (0.25, "sallet", "m6_silver", 1.4, None))):
        p6.helmet(det if k % 2 else shell, "shelf_helm_%d" % k, (x, SY, (zb + zf) / 2 + 0.02), kind=kind, metal=metal, s=s, crest=crest,
                  yaw=0.15 * ((k % 3) - 1))

    # ---- the armour stands: silver knight, gilded fantasy, dark heavy (with its helm)
    p6.armour_stand(shell, det, "knight", (-1.42, 0, -0.75), style="knight", pedestal_kind="block", yaw=0.12, s=1.35)
    p6.armour_stand(shell, det, "fantasy", (-0.26, 0, -0.95), style="fantasy", pedestal_kind="tier", s=1.35)
    p6.armour_stand(shell, det, "heavy", (0.9, 0, -0.92), style="heavy", pedestal_kind="tier", yaw=-0.12, helm=("armet", "m6_dark", "gold"),
                    s=1.35)

    # ---- the right: the counter (the merchant stands behind it), the soldier's armour on a high pedestal at the back,
    # a wall bracket with the crested helm
    top = ml.counter(shell, "counter", 1.4, 2.8, -0.25, 0.45, h=1.0, detail=det)
    cy = top[1]
    p6.helmet(shell, "counter_helm_0", (1.72, cy, 0.12), kind="great", metal="m6_silver", yaw=0.25, s=1.15)
    p6.helmet(det, "counter_helm_1", (2.08, cy, 0.05), kind="armet", metal="m6_silver", yaw=-0.1, s=1.1)
    p6.chest(shell, det, "counter_box", (2.33, cy, 0.12), size=(0.34, 0.2, 0.24), yaw=-0.2, solid=False)
    for k in range(3):
        ml.add_cube(det, "counter_gold_%d" % k, (2.27 + 0.07 * k, cy + 0.215, 0.12 + 0.02 * k), ml.ry(0.3 * k), (0.07, 0.04, 0.16),
                    "gold_ingot", stretch=True)
    p6.armour_stand(shell, det, "soldier", (2.1, 0, -2.2), style="soldier", pedestal_kind="tall", helm=("nasal", "m6_steel", None), s=1.2)
    ml.box(shell, "bracket_shelf", (2.45, 2.16, -hd - 0.06), (2.95, 2.22, -hd + 0.4), "plank", u_dir=X)
    ml.beam(det, "bracket_brace", (2.7, 1.8, -hd - 0.03), (2.7, 2.14, -hd + 0.3), 0.07, "wood_dark")
    p6.helmet(shell, "bracket_helm", (2.7, 2.22, -hd + 0.17), kind="armet", metal="m6_silver", crest="gold", yaw=-0.3, s=1.1)

    # ---- chests: front left (before the knight), front right (two round helms on it)
    p6.chest(shell, det, "chest_l", (-1.42, 0, 0.32), size=(0.95, 0.58, 0.62), yaw=0.05)
    t = p6.chest(shell, det, "chest_r", (2.5, 0, 1.25), size=(0.88, 0.56, 0.6), yaw=-0.08)
    p6.helmet(shell, "chest_r_helm_0", (2.29, t, 1.23), kind="bascinet", metal="m6_dark", yaw=0.3, s=1.05)
    p6.helmet(det, "chest_r_helm_1", (2.71, t, 1.27), kind="bascinet", metal="m6_dark", yaw=-0.4, s=1.05)

    # ---- the left inside: crates, the barbute, a dark breastplate on the crates, the eagle shield at the front
    ml.crate(shell, "crate_l0", (-2.42, 0, 2.08), size=(0.66, 0.84, 0.6))
    p6.helmet(shell, "crate_l0_helm", (-2.42, 0.84, 2.06), kind="barbute", metal="m6_silver", yaw=0.25, s=1.35)
    ml.crate(shell, "crate_l1", (-2.5, 0, 0.75), size=0.74)
    ml.crate(shell, "crate_l2", (-2.5, 0.74, 0.72), size=(0.6, 0.3, 0.55), yaw=0.15)
    p6.armour_stand(shell, det, "breastplate", (-2.5, 1.04 - 0.86, 0.7), style="heavy", pedestal_kind=None, skirt=False, arms=False,
                    yaw=0.35, solid=False)
    ml.collide((-2.87, 1.04, 0.38, -2.13, 1.85, 1.02))
    p6.eagle_shield(shell, det, "eagle_shield", (-2.3, 0.53, 2.6), (0, 0.24, 1), w=0.86, h=1.06)
    ml.collide((-2.75, 0.0, 2.4, -1.85, 1.0, 2.75))

    # ---- side drapes at the front left (navy and beige, as on the picture)
    drape(shell, "drape_l", -hw - 0.3, -0.2, 0.95, ey - 0.05, 0.25, "canvas", n=3)
    drape(shell, "drape_l_b", -hw - 0.3, 0.95, 2.25, ey - 0.05, 0.35, "beige", n=3)

    # ---- the eagle rug in front of the stands
    ml.rug(shell, "rug", -0.75, 2.0, 0.7, 4.62, region="m6_rug")

    # ---- furniture of the decoration mods (vanilla alt / stand-in when missing)
    decor = ml.Decor()
    decor.block("furnish:spruce_crate", -3.85, 0.0, 2.05, facing="front", scale=0.8, fallback="crate")
    decor.block("furnish:spruce_crate", -3.85, 0.0, 1.15, facing="neg_x", scale=0.8, fallback="crate")
    decor.block("furnish:dark_oak_crate", -3.85, 0.8, 1.95, facing="front", scale=0.6, fallback="crate")
    p6.helmet(shell, "out_helm", (-3.85, 0.8, 1.1), kind="great", metal="m6_dark", yaw=0.4)
    decor.block("furnish:spruce_crate", 3.8, 0.0, 2.15, facing="front", scale=0.75, fallback="crate")
    decor.block("landsoficaria:cypress_barrel", -2.5, 0.0, -1.95, facing="front", alt="minecraft:barrel", fallback="barrel")
    decor.block("furnish:dark_oak_crate", -2.45, 0.0, -0.75, facing="front", scale=0.7, fallback="crate")
    decor.block("farmhouse_decorations:kerosene_lantern", 2.62, cy, -0.05, facing="front", glow=True, fallback="lantern", solid=False)
    ml.export(root, NAME, atlas, decor=decor, icon=dict(colour="blue", emblem="shield"))


if __name__ == "__main__":
    main()
