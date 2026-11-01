#!/usr/bin/env python3
"""workshop_cook — Atelier du cuisinier / Cook's Workshop (reference: scratchpad/ref/workshop_cook_ref.png).

A stone hearth with a wood fire under a big black cauldron hanging from an iron hook, a stone back wall with a
chimney breast, a stone counter at the left (cheese, bread rolls, jars), a wooden prep table at the right (bread in a
bowl, cutting board, knife, onions), a shelf unit of apples, bread and jars, bunches of herbs, garlic and red peppers
hanging from the roof beam, a hanging sack, an iron-banded crate, a lantern on the front post, a thick sloping plank
roof on four posts.

Usage:  python3 tools/workshops/generate_workshop_cook.py      (WS_OUT=<file>: write only the model there)
Writes: blockbench/workshop_cook.bbmodel, the assets copy, textures/entity/workshops_b.png,
        textures/item/workshop_cook.png, workshops/workshop_cook.json.
Workshop-local coordinates: y up, +z = front (the player works from there), the anchor block at (0, 0, 0) in the
hearth's front.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wslib_b as wl  # noqa: E402

NAME = "workshop_cook"
UP, v3 = wl.UP, wl.v3
XL, XR = -2.0, 2.0            # post lines
ZB, ZF = -1.25, 0.42          # back / front posts
Y_BACK, Y_FRONT = 3.6, 3.35   # roof top heights
FIRE = v3(-0.1, 0.55, -0.35)  # the fire's foot on the hearth
HOOK_Y = 2.6
WALL_Z = -1.12                # front face of the back wall


def frame(root, detail, rng):
    s = wl.Bone("frame", parent=root)
    for k, (x, z) in enumerate(((XL, ZF), (XR, ZF), (XL, ZB), (XR, ZB))):
        top = Y_FRONT - 0.4 if z == ZF else Y_BACK - 0.42
        wl.post(s, "post_%d" % k, (x, 0, z), (x, top, z), d=0.32, region="wood")
        wl.add_cube(s, "post_foot_%d" % k, (x, 0.08, z), wl.EYE, (0.44, 0.16, 0.44), "cobble")
        wl.add_cube(s, "post_cap_%d" % k, (x, top - 0.08, z), wl.EYE, (0.4, 0.16, 0.4), {"all": "wood_dark", "+2": "end_grain"})
    # the roof: thick planks front to back over two heavy beams, a fascia board along the front
    wl.plank_roof(s, "roof", -2.45, 2.45, -1.65, 0.9, Y_BACK, Y_FRONT, th=0.24, plank_w=0.42, rng=rng, ragged=0.22, along="x")
    wl.beam(s, "fascia", (-2.5, Y_FRONT - 0.3, 0.88), (2.5, Y_FRONT - 0.3, 0.88), 0.2, {"all": "wood", "+1": "end_grain", "-1": "end_grain"},
            width=0.18)
    wl.collide((-2.45, Y_FRONT - 0.42, -1.65, 2.45, Y_BACK, 0.95))
    # side beams (front to back) on the posts, knee braces
    for x in (XL, XR):
        sg = 1 if x > 0 else -1
        wl.beam(s, "side_beam_%d" % (x > 0), (x, Y_FRONT - 0.48, ZF + 0.3), (x, Y_BACK - 0.5, ZB - 0.3), 0.24, "wood_dark", width=0.24)
        wl.beam(s, "brace_%d" % (x > 0), (x, Y_FRONT - 1.25, ZF), (x, Y_FRONT - 0.55, ZF + 0.55), 0.16, "wood", width=0.16, extend=0.05)
        wl.beam(s, "brace_x_%d" % (x > 0), (x, Y_FRONT - 1.2, ZF), (x - sg * 0.6, Y_FRONT - 0.55, ZF), 0.16, "wood", width=0.16, extend=0.05)
    # the stone back wall, its chimney breast behind the hearth, and a plank wall behind the shelves
    wl.stone_block(s, "back_wall", (-1.95, 0, -1.55), (0.85, Y_BACK - 0.5, WALL_Z), course=0.5, relief=0.025, seed=1)
    wl.stone_block(s, "breast", (-0.85, 0.55, WALL_Z - 0.02), (0.65, Y_BACK - 0.5, WALL_Z + 0.22), course=0.5, relief=0.03, seed=2,
                   top=None)
    wl.box(s, "breast_lintel", (-0.95, 2.95, WALL_Z + 0.18), (0.75, 3.15, WALL_Z + 0.3), {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    for k in range(4):
        x0 = 0.85 + k * 0.29
        wl.add_cube(s, "plank_wall_%d" % k, (x0 + 0.145, (Y_BACK - 0.5) / 2, -1.48), wl.EYE, (0.28, Y_BACK - 0.5, 0.08),
                    {"all": "plank_dark", "+1": "end_grain", "-1": "end_grain"}, u_dir=UP)
    wl.collide((0.85, 0, -1.55, 2.0, Y_BACK - 0.5, -1.42))


def hearth(root, detail, rng):
    h = wl.Bone("hearth", parent=root)
    fy = FIRE[1]
    # raised hearth: solid back part, two cheeks and a slab over the firewood niche at the front
    wl.stone_block(h, "hearth_back", (-0.95, 0, WALL_Z), (0.75, fy, 0.0), course=fy, seed=2)
    wl.stone_block(h, "hearth_l", (-0.95, 0, 0.0), (-0.48, fy, 0.55), course=fy, seed=3)
    wl.stone_block(h, "hearth_r", (0.28, 0, 0.0), (0.75, fy, 0.55), course=fy, seed=4)
    wl.box(h, "hearth_slab", (-0.48, fy - 0.12, 0.0), (0.28, fy, 0.55), {"all": "stone_slab"})
    wl.box(h, "hearth_lip", (-1.0, fy - 0.06, 0.5), (0.8, fy + 0.02, 0.6), {"all": "stone_slab"})
    wl.box(h, "hearth_niche_back", (-0.48, 0.0, -0.02), (0.28, fy - 0.12, 0.02), "cobble")
    wl.collide((-0.48, 0, 0.0, 0.28, fy, 0.6))
    # firewood in the niche
    for k in range(6):
        x = -0.37 + 0.18 * (k % 4) + (0.09 if k >= 4 else 0)
        y = 0.08 + (0.15 if k >= 4 else 0)
        wl.log(h, "niche_log_%d" % k, (x, y, 0.05), (x + 0.01, y, 0.5), r=0.075)
    # a ring of stones round the fire
    for k in range(9):
        a = 2 * math.pi * k / 9
        p = FIRE + v3(math.cos(a) * 0.46, 0.04, math.sin(a) * 0.4)
        wl.add_cube(detail, "fire_stone_%d" % k, p, wl.ry(a + 0.3), (0.17, 0.1, 0.14), "cobble")
    wl.fire(h, "fire", FIRE, s=0.6)
    # the big cauldron hanging over the fire from an iron arm out of the chimney breast
    cf = FIRE + UP * 0.36
    wl.cauldron(h, "cauldron", cf, r=0.5, h=0.62, legs=False, bail_to=cf + UP * 1.12, detail=detail)
    bail_top = cf + UP * 1.12
    wl.collide((FIRE[0] - 0.62, cf[1], FIRE[2] - 0.62, FIRE[0] + 0.62, cf[1] + 0.66, FIRE[2] + 0.62))
    zb = WALL_Z + 0.22
    wl.beam(h, "hook_arm", (FIRE[0], HOOK_Y, zb), (FIRE[0], HOOK_Y, FIRE[2] + 0.05), 0.08, "iron_dark", width=0.08, extend=0.03)
    wl.beam(h, "hook_brace", (FIRE[0], HOOK_Y - 0.4, zb), (FIRE[0], HOOK_Y - 0.02, FIRE[2] - 0.2), 0.05, "iron_dark", width=0.05, extend=0.02)
    wl.add_cube(h, "hook_plate", (FIRE[0], HOOK_Y - 0.2, zb + 0.02), wl.EYE, (0.22, 0.6, 0.04), "iron")
    wl.chain(detail, "hook_chain", (FIRE[0], HOOK_Y - 0.03, FIRE[2]), bail_top + UP * 0.02, link=0.08)
    wl.add_cube(h, "hook", bail_top + UP * 0.03, wl.EYE, (0.05, 0.08, 0.05), "iron_dark")
    # a ladle in the pot
    wl.beam(detail, "ladle", cf + v3(0.14, 0.52, 0.05), cf + v3(0.36, 1.0, 0.24), 0.04, "wood_dark", width=0.04)
    wl.add_cube(detail, "ladle_cup", cf + v3(0.13, 0.52, 0.04), wl.EYE, (0.12, 0.06, 0.12), "iron")
    # utensils hanging on the chimney breast: a frying pan, a ladle and a skimmer on pegs
    zu = WALL_Z + 0.25
    for k, ang in enumerate((0.0, math.pi / 4)):
        wl.add_cube(detail, "pan_%d" % k, (0.42, 1.72, zu), wl.gg.rz(ang), (0.34 - 0.06 * k, 0.34 - 0.06 * k, 0.04), "cauldron")
    wl.beam(detail, "pan_handle", (0.42, 1.88, zu), (0.42, 2.25, zu), 0.04, "wood_dark", width=0.03)
    for k, x in enumerate((-0.62, -0.42)):
        wl.add_cube(detail, "peg_u_%d" % k, (x, 2.3, zu - 0.02), wl.EYE, (0.04, 0.04, 0.12), "wood_dark")
        wl.beam(detail, "utensil_%d" % k, (x, 2.3, zu + 0.01), (x, 1.75, zu + 0.01), 0.03, "iron", width=0.025)
        wl.add_cube(detail, "utensil_cup_%d" % k, (x, 1.72, zu + 0.02), wl.EYE, (0.12, 0.1, 0.05), "iron_dark")
    wl.add_cube(detail, "pan_peg", (0.42, 2.27, zu - 0.02), wl.EYE, (0.04, 0.04, 0.12), "wood_dark")
    # logs piled by the hearth
    for k in range(3):
        wl.log(detail, "pile_log_%d" % k, (0.42 + 0.0 * k, 0.08 + 0.14 * (k // 2), 0.72 + 0.16 * (k % 2) - 0.08 * (k // 2)),
               (0.95, 0.08 + 0.14 * (k // 2), 0.74 + 0.16 * (k % 2) - 0.08 * (k // 2)), r=0.075)


def counter(root, detail, rng):
    c = wl.Bone("counter", parent=root)
    y = 1.0
    wl.stone_block(c, "counter", (-2.2, 0, -1.1), (-0.95, y - 0.1, 0.4), course=0.45, relief=0.03, seed=5)
    wl.box(c, "counter_top", (-2.28, y - 0.12, -1.12), (-0.92, y, 0.48), {"all": "stone_slab"})
    # cheese wheels, a cheese block, jars, a small crate of bread rolls, a bowl of stew
    wl.octo(detail, "cheese_0", (-1.9, y, 0.05), 0.17, 0.13, {"all": "cheese"}, stretch=True)
    wl.octo(detail, "cheese_1", (-1.88, y + 0.13, 0.04), 0.14, 0.12, {"all": "cheese"}, stretch=True)
    wl.box(detail, "cheese_block", (-1.62, y, 0.12), (-1.4, y + 0.15, 0.32), {"all": "cheese"}, yaw=0.3, stretch=True)
    wl.jar(detail, "jar_c0", (-2.0, y, -0.6), r=0.1, h=0.28)
    wl.jar(detail, "jar_c1", (-1.75, y, -0.75), r=0.08, h=0.2, region="clay")
    wl.crate(c, "small_crate", (-1.35, y, -0.45), s=0.42, yaw=0.15, solid=False, straps=False)
    for k in range(4):
        wl.bread(detail, "roll_%d" % k, (-1.42 + 0.13 * (k % 2), y + 0.42, -0.52 + 0.14 * (k // 2)), yaw=0.4 * k, l=0.16, w=0.11, h=0.08)
    wl.crate(c, "small_crate_2", (-1.2, y, 0.12), s=0.3, yaw=-0.2, solid=False, straps=False)
    for k in range(3):
        wl.bread(detail, "roll_b_%d" % k, (-1.25 + 0.08 * k, y + 0.3, 0.08 + 0.06 * (k % 2)), yaw=0.7 * k, l=0.13, w=0.09, h=0.07)
    # the iron-banded crate in front, a sack beside it
    wl.crate(c, "crate_front", (-1.85, 0, 0.9), s=0.64, yaw=0.06)


def prep_table(root, detail, rng):
    t = wl.Bone("table", parent=root)
    x0, x1, z0, z1, y = 0.95, 2.3, -0.62, 0.5, 0.98
    wl.table(t, "table", x0, x1, z0, z1, y, top_th=0.14, leg=0.2, shelf_y=0.3)
    # bread in a big bowl, a cutting board with a knife, onions, a loaf
    wl.bowl(detail, "bread_bowl", (1.42, y, -0.1), r=0.3, h=0.12, content="bread_top")
    for k in range(5):
        a = k * 1.25
        wl.bread(detail, "bowl_bread_%d" % k, (1.42 + 0.13 * math.cos(a), y + 0.1, -0.1 + 0.1 * math.sin(a)), yaw=a, l=0.24, w=0.14, h=0.1)
    wl.box(detail, "board", (1.75, y, 0.05), (2.2, y + 0.05, 0.4), {"all": "plank"}, yaw=-0.1)
    wl.beam(detail, "knife_blade", (1.85, y + 0.07, 0.18), (2.07, y + 0.07, 0.26), 0.014, "iron", width=0.06)
    wl.beam(detail, "knife_handle", (2.07, y + 0.07, 0.26), (2.19, y + 0.07, 0.3), 0.035, "wood_dark", width=0.04)
    for k in range(3):
        wl.apple(detail, "onion_%d" % k, (1.88 + 0.11 * k, y + 0.05, -0.3 + 0.05 * (k % 2)), s=0.1, color="onion")
    wl.bread(detail, "loaf_t", (2.05, y, -0.4), yaw=0.5, l=0.32, w=0.17, h=0.11)
    # under the table: jars, a small barrel, a basket of apples
    wl.jar(detail, "jar_t0", (1.22, 0.3, -0.25), r=0.11, h=0.3, region="clay")
    wl.jar(detail, "jar_t1", (1.48, 0.3, -0.2), r=0.09, h=0.24)
    wl.barrel(t, "small_barrel", (1.98, 0.3, -0.15), r=0.22, h=0.46, staves=8, solid=False)
    wl.box(detail, "basket", (1.2, 0.3, 0.02), (1.68, 0.5, 0.38), {"all": "crate", "+2": "apples"}, stretch=True)


def shelves(root, detail, rng):
    s = wl.Bone("shelves", parent=root)
    x0, x1, zb = 1.15, 2.05, -1.43
    for x in (x0, x1):
        wl.add_cube(s, "shelf_side_%d" % (x > 1.5), (x, 1.55, zb + 0.2), wl.EYE, (0.08, 1.6, 0.4), {"all": "wood", "+2": "end_grain"}, u_dir=UP)
    for k, y in enumerate((1.3, 1.85, 2.4)):
        wl.add_cube(s, "shelf_%d" % k, ((x0 + x1) / 2, y - 0.03, zb + 0.2), wl.EYE, (x1 - x0 + 0.06, 0.06, 0.42),
                    {"all": "plank", "+1": "end_grain", "-1": "end_grain"}, u_dir=wl.X)
    wl.collide((x0 - 0.05, 0.75, zb, x1 + 0.05, 2.4, zb + 0.42))
    # top: big red apples and a jar; middle: loaves; bottom: a bowl of bread and jars
    for k in range(3):
        wl.apple(detail, "apple_s_%d" % k, (1.32 + 0.21 * k, 2.4, -1.2 + 0.04 * (k % 2)), s=0.2)
    wl.jar(detail, "jar_s0", (1.92, 2.4, -1.25), r=0.1, h=0.28)
    for k in range(3):
        wl.bread(detail, "loaf_s_%d" % k, (1.36 + 0.27 * k, 1.85, -1.2), yaw=0.2 * (k - 1), l=0.28, w=0.16, h=0.12)
    wl.bread(detail, "loaf_s_top", (1.5, 1.97, -1.22), yaw=-0.3, l=0.26, w=0.15, h=0.11)
    wl.bowl(detail, "bowl_s", (1.4, 1.3, -1.2), r=0.17, h=0.09, content="apples")
    wl.jar(detail, "jar_s1", (1.72, 1.3, -1.25), r=0.09, h=0.26, region="clay")
    wl.jar(detail, "jar_s2", (1.92, 1.3, -1.22), r=0.08, h=0.2)
    # a sack hanging from a peg on the chimney breast's right, an orange jar on a bracket of the right post
    wl.add_cube(s, "peg", (0.92, 2.15, -1.05), wl.EYE, (0.05, 0.05, 0.18), "wood_dark")
    wl.sack(detail, "hanging_sack", (0.92, 1.4, -0.95), s=0.38)
    wl.beam(detail, "sack_cord", (0.92, 1.9, -0.95), (0.92, 2.15, -1.0), 0.025, "rope")
    wl.add_cube(s, "post_bracket", (XR - 0.28, 1.55, ZF), wl.EYE, (0.26, 0.06, 0.26), "plank")
    wl.jar(detail, "jar_post", (XR - 0.28, 1.58, ZF), r=0.09, h=0.26)


def hanging(root, detail, rng):
    h = wl.Bone("hanging", parent=root)
    yb = Y_FRONT - 0.42                       # under the roof's front beam
    zf = 0.62
    wl.beam(h, "bunch_rail", (-2.0, yb - 0.05, zf), (0.4, yb - 0.05, zf), 0.08, "wood_dark", width=0.08)
    for k, (x, kind, L) in enumerate(((-1.45, "herbs", 0.85), (-0.85, "garlic", 0.75), (-0.3, "peppers", 0.75))):
        wl.hanging_bunch(detail, "bunch_%d" % k, (x, yb - 0.09, zf), kind, length=L, width=0.42, string=0.1 + 0.06 * (k % 2))
    wl.hanging_bunch(detail, "bunch_r", (1.3, Y_FRONT - 0.5, 0.0), "herbs", length=0.6, width=0.34, string=0.1)
    wl.beam(h, "bunch_rail_r", (0.9, Y_FRONT - 0.5, 0.0), (2.0, Y_FRONT - 0.5, 0.0), 0.07, "wood_dark", width=0.07)
    # the lantern on an iron arm at the front of the left post
    base = v3(XL, 2.5, ZF + 0.16)
    tip = base + v3(0.0, 0.0, 0.34)
    wl.beam(h, "lamp_arm", base, tip, 0.05, "iron_dark", width=0.05)
    wl.beam(h, "lamp_brace", base - UP * 0.25, tip - v3(0, 0.02, 0.12), 0.04, "iron_dark", width=0.04)
    wl.lantern(h, "lamp", tip - UP * 0.36, size=0.3, chain_to=tip)


def build():
    rng = random.Random(11)
    root = wl.Bone(NAME)
    detail = wl.Bone("detail", parent=root)
    frame(root, detail, rng)
    hearth(root, detail, rng)
    counter(root, detail, rng)
    prep_table(root, detail, rng)
    shelves(root, detail, rng)
    hanging(root, detail, rng)
    return root


def icon(path):
    """32x32: a black cauldron over a fire with steam."""
    im, d = wl.new_icon(32)
    d.polygon([(9, 29), (12, 21), (14, 26), (16, 19), (18, 26), (20, 21), (23, 29)], fill=(240, 130, 30, 255))
    d.polygon([(12, 29), (14, 24), (16, 27), (18, 24), (20, 29)], fill=(255, 220, 90, 255))
    d.rectangle([7, 29, 25, 30], fill=(110, 70, 40, 255))
    d.ellipse([5, 9, 27, 25], fill=(48, 48, 56, 255), outline=(110, 110, 122, 255))
    d.rectangle([5, 9, 27, 13], fill=(40, 40, 46, 255))
    d.rectangle([4, 8, 28, 10], fill=(70, 70, 78, 255))
    d.rectangle([7, 10, 25, 11], fill=(150, 90, 40, 255))
    d.line([(9, 15), (9, 20)], fill=(90, 90, 100, 255))
    d.line([(4, 8), (16, 2), (28, 8)], fill=(90, 90, 100, 255))
    for x in (11, 17, 22):
        d.line([(x, 6), (x + 1, 4), (x, 2)], fill=(230, 230, 235, 200))
    wl.save_icon(im, path)


def main():
    wl.setup(NAME)
    root = build()
    particles = [
        {"type": "flame", "pos": (FIRE[0], FIRE[1] + 0.2, FIRE[2]), "chance": 0.35, "count": 1},
        {"type": "smoke", "pos": (FIRE[0], 1.6, FIRE[2]), "chance": 0.3, "count": 1},
        {"type": "campfire_smoke", "pos": (FIRE[0], 1.65, FIRE[2]), "chance": 0.04, "count": 1},
    ]
    wl.export(root, NAME, particles=particles, icon=icon, visible_box=(8, 5, 0))


if __name__ == "__main__":
    main()
