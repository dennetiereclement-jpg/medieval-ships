#!/usr/bin/env python3
"""tent_market — the big market awning (reference: scratchpad/ref/tent3_market_ref.png).

A large worn beige canvas hipped roof (short ridge, four sagging slopes, torn fringes all round the eaves) on eight
slightly leaning posts and two centre posts, eave beams and a ridge pole, rustic rails along the back and the rear
halves of the sides, red and dark cloth pieces and pennants hanging from the front eave, lanterns, two long trestle
stalls in front covered with goods, crates, barrels, sacks, baskets and jars round the posts, flagstones on the ground.
The goods come from the decoration mods (stand-ins when the mods are missing).

Usage:  python3 tools/tents/generate_tent_market.py      (TENT_OUT=<file>: write only the model there, for previews)
Writes: blockbench/tent_market.bbmodel, the assets copy, textures/entity/tents.png, textures/item/tent_market.png,
        interiors/tent_market_decor.json, tents/tent_market.json (extent + collision boxes for TentType).
Tent-local coordinates: y up, +z = front (the open side with the stalls), the anchor block at (0, 0, 0).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tentlib as tl  # noqa: E402

NAME = "tent_market"
HALF_X, HALF_Z = 4.4, 3.3          # the post rows
EAVE_Y, RIDGE_Y = 4.05, 5.5
EAVE_X, EAVE_Z = 5.4, 4.3          # the canvas overhang
STALL_Y = 0.95
POST_D = 0.2


def stall(bone, name, x0, x1, z, y=STALL_Y, depth=1.05, region="plank"):
    """A long trestle stall: two top boards, an apron, splayed legs at each end; collides as a box."""
    L = x1 - x0
    cx = (x0 + x1) / 2
    for k, dz in enumerate((-depth / 4, depth / 4)):
        tl.add_cube(bone, "%s_top_%d" % (name, k), (cx, y - 0.04, z + dz), tl.EYE, (L, 0.08, depth / 2 * 0.98), region,
                    u_dir=tl.v3(1, 0, 0))
    tl.add_cube(bone, "%s_apron" % name, (cx, y - 0.2, z + depth / 2 - 0.08), tl.EYE, (L - 0.3, 0.22, 0.06), "wood_dark",
                u_dir=tl.v3(1, 0, 0))
    for e, xe in enumerate((x0 + 0.35, x1 - 0.35)):
        for s in (-1, 1):
            tl.post(bone, "%s_leg_%d_%d" % (name, e, s), (xe, 0.0, z + s * (depth / 2 + 0.08)), (xe, y - 0.08, z + s * 0.12),
                    d=0.11, solid=False, cap=False)
        tl.pole(bone, "%s_tie_%d" % (name, e), (xe, 0.42, z - depth / 2), (xe, 0.42, z + depth / 2), d=0.08, region="wood_dark")
    tl.collide((x0, 0.0, z - depth / 2 - 0.1, x1, y, z + depth / 2 + 0.1))


def hanging_cloth(bone, name, x, z, top_y, width, height, region, fringe_region, lean=0.1):
    """A red / dark cloth piece hanging from the front eave, blown a little outwards."""
    tl.canvas_panel(bone, name, (x - width / 2, top_y, z), (x + width / 2, top_y, z),
                    (x - width / 2 * 0.9, top_y - height, z + lean), (x + width / 2 * 0.9, top_y - height, z + lean),
                    sag=0.06, nx=1, ny=2, region=region, fringe=0.22, fringe_region=fringe_region, sag_dir=(0, 0, 1), ripple=0.03)


def build():
    root = tl.Bone(NAME)
    frame = tl.Bone("frame", parent=root)
    cloth = tl.Bone("canvas", parent=root)
    detail = tl.Bone("detail", parent=root)
    furn = tl.Bone("furniture", parent=root)

    # ---- posts: two rows of four, slightly leaning, and two taller centre posts under the ridge
    posts_x = (-HALF_X, -1.5, 1.5, HALF_X)
    leans = ((0.12, 0.08), (-0.05, 0.1), (0.06, -0.04), (-0.1, 0.07), (0.08, -0.1), (-0.07, -0.06), (0.1, 0.05), (-0.12, 0.04))
    k = 0
    for zr, zn in ((HALF_Z, "front"), (-HALF_Z, "back")):
        for x in posts_x:
            lx, lz = leans[k]
            k += 1
            tl.post(frame, "post_%s_%d" % (zn, k), (x, -0.05, zr), (x + lx, EAVE_Y + 0.1, zr + lz * (1 if zr > 0 else -1)), d=POST_D)
    for s in (-1, 1):
        tl.post(frame, "king_%d" % s, (s * 2.9, -0.05, -0.3), (s * 2.75, RIDGE_Y + 0.05, -0.2), d=POST_D)
    # eave beams and the ridge pole
    tl.pole(frame, "eave_front", (-HALF_X - 0.45, EAVE_Y + 0.12, HALF_Z), (HALF_X + 0.45, EAVE_Y + 0.12, HALF_Z), d=0.17, region="wood_dark")
    tl.pole(frame, "eave_back", (-HALF_X - 0.45, EAVE_Y + 0.12, -HALF_Z), (HALF_X + 0.45, EAVE_Y + 0.12, -HALF_Z), d=0.17, region="wood_dark")
    for s in (-1, 1):
        tl.pole(frame, "eave_side_%d" % s, (s * HALF_X, EAVE_Y + 0.14, -HALF_Z - 0.4), (s * HALF_X, EAVE_Y + 0.14, HALF_Z + 0.4), d=0.15,
                region="wood_dark")
    tl.pole(frame, "ridge", (-3.9, RIDGE_Y - 0.08, -0.2), (3.9, RIDGE_Y - 0.08, -0.2), d=0.17, region="wood_dark")
    # hip rafters from the ridge ends to the corners, two rafters down the long slopes
    for sx in (-1, 1):
        for sz in (-1, 1):
            tl.pole(frame, "hip_%d_%d" % (sx, sz), (sx * 3.6, RIDGE_Y - 0.1, -0.2), (sx * HALF_X, EAVE_Y + 0.12, sz * HALF_Z), d=0.12)
        tl.pole(frame, "rafter_%d" % sx, (sx * 1.5, RIDGE_Y - 0.1, -0.2), (sx * 1.5, EAVE_Y + 0.12, sx * HALF_Z), d=0.11)
    # cross braces at the king posts
    for s in (-1, 1):
        tl.pole(detail, "brace_%d" % s, (s * 2.85, RIDGE_Y - 0.9, -0.25), (s * 1.9, RIDGE_Y + 0.0, -0.2), d=0.09, region="wood_dark")

    # ---- rustic rails: along the back and the rear halves of the sides (the front stays open)
    tl.railing(frame, "rail_back", (-HALF_X, 0, -HALF_Z), (HALF_X, 0, -HALF_Z), h=1.05, post_every=2.95, d=0.1)
    for s in (-1, 1):
        tl.railing(frame, "rail_side_%d" % s, (s * HALF_X, 0, -HALF_Z), (s * HALF_X, 0, 0.2), h=1.05, post_every=3.6, d=0.1)

    # ---- the canvas: a hipped roof of four sagging panels (two halves each on the long slopes), torn fringes
    ridge0, ridge1 = (-3.6, RIDGE_Y, -0.2), (3.6, RIDGE_Y, -0.2)
    for sz, zn in ((1, "front"), (-1, "back")):
        ez = sz * EAVE_Z - 0.2
        for sx, xn in ((-1, "l"), (1, "r")):
            reg = "canvas" if (sx * sz) > 0 else "canvas_b"
            top_in, top_out = (0, RIDGE_Y, -0.2), (sx * 3.6, RIDGE_Y, -0.2)
            bot_in, bot_out = (0, EAVE_Y - 0.1, ez), (sx * EAVE_X, EAVE_Y - 0.1, ez)
            t0, t1 = (top_out, top_in) if sx < 0 else (top_in, top_out)
            b0, b1 = (bot_out, bot_in) if sx < 0 else (bot_in, bot_out)
            if sz < 0:   # keep the panel's outer face pointing outwards
                t0, t1, b0, b1 = t1, t0, b1, b0
            tl.canvas_panel(cloth, "roof_%s_%s" % (zn, xn), t0, t1, b0, b1, sag=0.36, nx=4, ny=4, region=reg, fringe=0.45, ripple=0.15)
    for sx, xn in ((-1, "l"), (1, "r")):
        apex = (sx * 3.6, RIDGE_Y, -0.2)
        a0, a1 = (sx * 3.6, RIDGE_Y, -0.3), (sx * 3.6, RIDGE_Y, -0.1)
        c_back, c_front = (sx * EAVE_X, EAVE_Y - 0.1, -EAVE_Z - 0.2), (sx * EAVE_X, EAVE_Y - 0.1, EAVE_Z - 0.2)
        if sx > 0:
            tl.canvas_panel(cloth, "roof_hip_%s" % xn, a1, a0, c_front, c_back, sag=0.28, nx=3, ny=4, region="canvas_b", fringe=0.42, ripple=0.13)
        else:
            tl.canvas_panel(cloth, "roof_hip_%s" % xn, a0, a1, c_back, c_front, sag=0.28, nx=3, ny=4, region="canvas", fringe=0.42, ripple=0.13)

    # ---- red and dark cloth pieces, pennants along the front eave; a beige valance piece at the back
    fz = HALF_Z + 0.15
    hanging_cloth(detail, "cloth_red_1", -2.6, fz, EAVE_Y + 0.05, 0.8, 1.1, "canvas_red", "fringe_red")
    hanging_cloth(detail, "cloth_dark_1", -0.3, fz, EAVE_Y + 0.05, 0.7, 0.95, "canvas_dark", "fringe_dark")
    hanging_cloth(detail, "cloth_red_2", 0.9, fz, EAVE_Y + 0.05, 0.6, 1.25, "canvas_red", "fringe_red")
    hanging_cloth(detail, "cloth_red_3", 3.4, fz, EAVE_Y + 0.05, 0.85, 1.0, "canvas_red", "fringe_red")
    hanging_cloth(detail, "cloth_beige", 2.1, fz, EAVE_Y + 0.05, 0.55, 0.8, "canvas_b", "fringe")
    hanging_cloth(detail, "cloth_dark_side", -HALF_X - 0.1, 1.6, EAVE_Y + 0.05, 0.7, 0.9, "canvas_dark", "fringe_dark", lean=0.0)
    hanging_cloth(detail, "cloth_side_r", HALF_X + 0.1, 0.4, EAVE_Y + 0.05, 0.6, 0.75, "canvas", "fringe", lean=0.0)
    for x, d in ((-3.9, (-0.4, 0, 1)), (3.9, (0.4, 0, 1))):
        tl.pennant(detail, "pennant_%d" % int(x * 10), (x, RIDGE_Y + 0.12, 0.0), length=0.7, width=0.26, direction=d)
    tl.pennant(detail, "pennant_c", (0.1, RIDGE_Y + 0.14, 0.0), length=0.6, width=0.22, region="canvas_dark", direction=(0.2, 0, 1))

    # ---- guy ropes to pegs at the four corners, rope lashings at the beams
    for sx in (-1, 1):
        for sz in (-1, 1):
            tl.guy(detail, "guy_%d_%d" % (sx, sz), (sx * (HALF_X + 0.1), EAVE_Y, sz * (HALF_Z + 0.1)), (sx * (HALF_X + 1.1), 0, sz * (HALF_Z + 1.1)))
            tl.rope(detail, "lash_%d_%d" % (sx, sz), (sx * HALF_X - 0.14, EAVE_Y - 0.05, sz * HALF_Z - 0.14), (sx * HALF_X + 0.14, EAVE_Y + 0.2, sz * HALF_Z + 0.14), d=0.07)
    # a bunting rope between the front middle posts, with small coloured flags
    tl.rope(detail, "bunting", (-1.5, EAVE_Y - 0.6, HALF_Z + 0.05), (1.5, EAVE_Y - 0.6, HALF_Z + 0.05), d=0.04, sag=0.25, segs=4)
    for i, (x, reg) in enumerate(((-1.0, "canvas_red"), (-0.35, "canvas_b"), (0.3, "canvas_dark"), (0.95, "canvas_red"))):
        t = (x + 1.5) / 3.0
        yb = EAVE_Y - 0.6 - 0.25 * math.sin(math.pi * t) * 4 * t * (1 - t)
        tl.pennant(detail, "flag_%d" % i, (x, yb, HALF_Z + 0.06), length=0.32, width=0.2, region=reg, direction=(0, 0, 1))

    # ---- lanterns of the mods hanging from the front eave and the king posts
    decor = tl.Decor()
    for x in (-1.5, 1.5):
        decor.block("farmhouse_decorations:chained_kerosene_lantern", x + 0.35, EAVE_Y - 0.95, HALF_Z, facing="front", glow=True,
                    fallback="lantern", solid=False)
    for s in (-1, 1):
        decor.block("farmhouse_decorations:chained_kerosene_lantern", s * 2.9, RIDGE_Y - 1.5, -0.65, facing="front", glow=True,
                    fallback="lantern", solid=False)

    # ---- the two long stalls in front, their goods on top (from the mods), crates and sacks under them
    stall(furn, "stall_l", -4.0, -0.7, 1.7)
    stall(furn, "stall_r", 0.7, 4.0, 1.7)
    goods = [
        ("farmersdelight:apple_pie", -3.5, 1.7, "front", 0.9, "sack"),
        ("farmersdelight:sweet_berry_cheesecake", -2.75, 1.45, "neg_x", 0.9, "sack"),
        ("farmersdelight:honey_glazed_ham_block", -1.9, 1.75, "front", 0.85, "leather"),
        ("farmhouse_decorations:wine_bottle", -1.25, 1.5, "front", 1.0, "glass"),
        ("farmhouse_decorations:red_wine_bottle", -1.1, 1.95, "front", 1.0, "glass"),
        ("farmersdelight:wooden_basket", 1.2, 1.7, "front", 0.7, "crate"),
        ("farmersdelight:roast_chicken_block", 2.1, 1.6, "front", 0.85, "leather"),
        ("furnish:book_pile", 2.9, 1.85, "pos_x", 0.9, "books"),
        ("farmersdelight:pumpkin_pie", 3.55, 1.5, "front", 0.9, "sack"),
        ("farmhouse_decorations:kerosene_lantern", -0.95, 1.95, "front", 0.9, "lantern"),
    ]
    for bid, x, z, facing, scale, fb in goods:
        decor.block(bid, x, STALL_Y, z, facing=facing, scale=scale, fallback=fb, solid=False,
                    glow=(fb == "lantern"))
    decor.block("farmersdelight:rice_bag", -3.3, 0.0, 1.75, facing="front", scale=0.75, fallback="sack")
    decor.block("furnish:spruce_crate", 3.2, 0.0, 1.7, facing="front", scale=0.8, fallback="crate")

    # ---- goods round the posts: vegetable crates stacked at the left front, barrels at the right, jars and bales behind
    decor.block("farmersdelight:carrot_crate", -4.9, 0.0, 3.9, facing="front", fallback="crate")
    decor.block("farmersdelight:cabbage_crate", -4.9, 0.0, 2.85, facing="front", fallback="crate")
    decor.block("farmersdelight:tomato_crate", -4.9, 1.0, 3.4, facing="pos_x", scale=0.85, fallback="crate")
    decor.block("furnish:oak_crate", -3.6, 0.0, 4.2, facing="front", scale=0.8, fallback="crate")
    decor.block("landsoficaria:loaded_cypress_barrel", 4.95, 0.0, 2.4, facing="front", alt="minecraft:barrel", fallback="barrel")
    decor.block("landsoficaria:loaded_cypress_barrel", 4.95, 0.0, 3.45, facing="front", alt="minecraft:barrel", fallback="barrel")
    decor.block("landsoficaria:cypress_barrel", 4.9, 0.9, 2.95, facing="front", scale=0.85, alt="minecraft:barrel", fallback="barrel")
    decor.block("landsoficaria:loaded_cypress_barrel", 4.0, 0.0, 4.2, facing="neg_x", scale=0.9, alt="minecraft:barrel", fallback="barrel")
    decor.block("furnish:spruce_crate", -4.95, 0.0, -2.6, facing="front", fallback="crate")
    decor.block("furnish:oak_crate", -4.95, 1.0, -2.6, facing="neg_x", scale=0.8, fallback="crate")
    decor.block("farmersdelight:rice_bag", -4.0, 0.0, -2.75, facing="pos_x", scale=0.85, fallback="sack")
    decor.block("farmersdelight:straw_bale", 4.9, 0.0, -2.6, facing="front", fallback="straw")
    decor.block("landsoficaria:storage_vase", 3.9, 0.0, -2.75, facing="front", scale=0.95, alt="minecraft:decorated_pot", fallback="barrel",
                bounds=(0.062, 0.938, 0.0, 1.0, 0.062, 0.938))
    decor.block("furnish:amphora", 3.1, 0.0, -2.8, facing="back", scale=0.8, alt="minecraft:decorated_pot", fallback="barrel")
    decor.block("farmersdelight:bamboo_basket", -2.6, 0.0, -2.75, facing="front", scale=0.8, fallback="crate")
    decor.block("farmersdelight:onion_crate", -1.4, 0.0, -2.8, facing="front", scale=0.9, fallback="crate")
    decor.block("furnish:spruce_bench", 1.0, 0.0, -2.75, facing="front", fallback="plank")
    decor.fallbacks(root)

    # ---- flagstones on the ground inside and in front
    stones = ((-3.2, 0.2, 1.3, 1.0), (-1.6, -0.4, 1.1, 0.9), (0.0, 0.3, 1.4, 1.1), (1.7, -0.6, 1.0, 0.8), (3.0, 0.4, 1.2, 1.0),
              (-2.4, -1.6, 1.0, 0.9), (0.9, -1.8, 1.3, 0.9), (-0.5, 3.0, 1.1, 0.9), (0.7, 4.3, 1.2, 0.8), (-0.4, 5.2, 0.9, 0.8),
              (2.4, 3.2, 0.9, 0.8), (-2.2, 3.3, 0.8, 0.7), (-1.0, 4.4, 1.0, 0.7))
    for k, (x, z, w, d) in enumerate(stones):
        tl.add_cube(detail, "flag_%d" % k, (x, 0.03, z), tl.EYE, (w, 0.06, d), "stone")
    return root, decor


def icon_awning(path):
    """16x16 inventory icon: the beige awning on posts, a red cloth piece."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    cloth, dark, wood, red = (201, 180, 138), (141, 122, 86), (110, 76, 40), (150, 40, 40)
    for y in range(2, 7):
        half = 4 + (y - 2) * 1.0
        for x in range(16):
            d = abs(x - 7.5)
            if d <= half:
                c = dark if (abs(d - half) < 0.6 or y == 6) else cloth
                p[x, y] = c + (255,)
    for x in (2, 5, 9, 13):
        p[x, 7] = dark + (255,)
    for x in (4, 10):
        for y in (7, 8):
            p[x, y] = red + (255,)
    for x in (2, 13):
        for y in range(6, 15):
            p[x, y] = wood + (255,)
    for x in (6, 9):
        for y in range(7, 14):
            p[x, y] = wood + (255,)
    for x in range(4, 12):
        p[x, 11] = (90, 70, 45, 255)
        p[x, 12] = (60, 45, 30, 255)
    for x in range(0, 16):
        p[x, 14] = (90, 110, 50, 255)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)


def main():
    tl.setup(NAME)
    root, decor = build()
    tl.export(root, NAME, decor, icon=icon_awning, visible_box=(8, 6, 0))


if __name__ == "__main__":
    main()
