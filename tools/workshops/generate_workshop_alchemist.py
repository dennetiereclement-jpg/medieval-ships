#!/usr/bin/env python3
"""workshop_alchemist — Atelier de l'alchimiste / Alchemist's Workshop (reference: scratchpad/ref/workshop_alchemist_ref.png).

A dark wooden stall: a long alchemy table with a purple cloth runner (gold points) and an open book, a tall candle,
two shelves of coloured vials (green, red, pink, blue, purple, orange, teal) and an amethyst cluster, a glowing green
flask on a brass stand over a burner with a copper pipe running to a collecting bottle, a mortar and pestle, ivy
hanging from the roof beam, a purple banner with a flask emblem, a barrel, a yellow bottle on the ground.

Usage:  python3 tools/workshops/generate_workshop_alchemist.py      (WS_OUT=<file>: write only the model there)
Writes: blockbench/workshop_alchemist.bbmodel, the assets copy, textures/entity/workshops_b.png,
        textures/item/workshop_alchemist.png, workshops/workshop_alchemist.json.
Workshop-local coordinates: y up, +z = front (the player works from there), the anchor block at (0, 0, 0) in the
table.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wslib_b as wl  # noqa: E402

NAME = "workshop_alchemist"
UP, v3 = wl.UP, wl.v3
Y_TOP = 3.15                 # the roof's top (back), front a little lower
WALL_Z = -0.92               # front face of the back wall
TABLE = (-1.85, 0.42, -0.34, 0.55, 0.98)     # x0, x1, z0, z1, top
FLASK = v3(0.8, 0.98, -0.3)               # the flask stand's foot on the right counter


def frame(root, detail, rng):
    s = wl.Bone("frame", parent=root)
    posts = ((-2.0, 0.62, Y_TOP - 0.35), (-2.0, -1.05, Y_TOP - 0.3), (1.88, -1.05, Y_TOP - 0.3), (1.88, 0.25, Y_TOP - 0.35))
    for k, (x, z, top) in enumerate(posts):
        wl.post(s, "post_%d" % k, (x, 0, z), (x, top, z), d=0.28, region="wood_dark")
        wl.add_cube(s, "post_cap_%d" % k, (x, top - 0.06, z), wl.EYE, (0.34, 0.12, 0.34), {"all": "wood", "+2": "end_grain"})
    wl.stone_block(s, "plinth", (1.62, 0, -1.3), (2.14, 0.85, -0.8), course=0.43, seed=3)
    wl.plank_roof(s, "roof", -2.3, 2.2, -1.3, 0.85, Y_TOP, Y_TOP - 0.15, th=0.2, plank_w=0.49, region="plank_dark", rng=rng,
                  beam_region="wood_dark", ragged=0.2, along="x")
    wl.beam(s, "front_beam", (-2.35, Y_TOP - 0.45, 0.62), (2.1, Y_TOP - 0.45, 0.62), 0.24, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"},
            width=0.22)
    wl.collide((-2.3, Y_TOP - 0.55, -1.3, 2.2, Y_TOP, 0.85))
    for x in (-2.0, 1.88):
        wl.beam(s, "side_beam_%d" % (x > 0), (x, Y_TOP - 0.42, 0.75), (x, Y_TOP - 0.42, -1.2), 0.2, "wood_dark", width=0.2)
    # the back wall: dark vertical planks, a rail half way up
    n = 13
    W0, W1 = -1.9, 1.76
    for k in range(n):
        x0 = W0 + k * ((W1 - W0) / n)
        wl.add_cube(s, "wall_%d" % k, (x0 + (W1 - W0) / n / 2, (Y_TOP - 0.4) / 2, WALL_Z - 0.04), wl.EYE, ((W1 - W0) / n * 0.98, Y_TOP - 0.4, 0.08),
                    {"all": "plank_dark", "+1": "end_grain", "-1": "end_grain"}, u_dir=UP)
    wl.collide((W0, 0, WALL_Z - 0.08, W1, Y_TOP - 0.4, WALL_Z))
    wl.beam(s, "wall_rail", (W0, 1.05, WALL_Z + 0.04), (W1, 1.05, WALL_Z + 0.04), 0.12, "wood_dark", width=0.08)
    # ivy hanging from the front beam on the left, a few strands down the left post
    for k, (x, L) in enumerate(((-2.05, 1.9), (-1.78, 1.5), (-1.5, 1.1), (-1.22, 0.7), (-0.95, 0.45), (-0.4, 0.3))):
        wl.vine(detail, "ivy_%d" % k, (x, Y_TOP - 0.36, 0.76 + 0.03 * (k % 2)), L, 0.5, region="ivy" if k % 2 == 0 else "vines")
    wl.vine(detail, "ivy_post", (-2.16, Y_TOP - 0.4, 0.62), 2.3, 0.32, normal=(-1, 0, 0), region="ivy")
    wl.vine(detail, "ivy_top", (-1.55, Y_TOP + 0.02, 0.86), 0.55, 1.2, region="ivy")
    wl.vine(detail, "ivy_side", (-2.32, Y_TOP - 0.2, -0.2), 1.2, 1.2, normal=(-1, 0, 0), region="vines")


def table(root, detail, rng):
    t = wl.Bone("table", parent=root)
    x0, x1, z0, z1, y = TABLE
    wl.table(t, "table", x0, x1, z0, z1, y, top_th=0.14, leg=0.18, top_region="plank_dark", leg_region="wood_dark", shelf_y=0.28)
    # the purple runner over the table and down its front, the open book on it
    cx = -0.85
    wl.box(t, "runner_top", (cx - 0.46, y, z0 + 0.05), (cx + 0.46, y + 0.015, z1 + 0.02), {"all": "cloth_purple"})
    wl.plate(t, "runner_front", (cx, y - 0.26, z1 + 0.025), 0.92, 0.54, "altar_cloth", normal=(0, 0, 1), th=0.012)
    wl.open_book(t, "book", (cx, y + 0.015, 0.12), w=0.9, d=0.58, yaw=0.08, cover="book_red", glow=False)
    wl.add_cube(detail, "ribbon", (cx + 0.05, y + 0.03, 0.38), wl.EYE, (0.03, 0.01, 0.16), "cloth_red")
    # the candle at the left, small bottles, a dish of powder, a scroll
    wl.candle(t, "candle", (-1.62, y, 0.12), h=0.48, r=0.075)
    wl.candle(detail, "candle_b", (-1.45, y, -0.12), h=0.26, r=0.055)
    wl.bottle(detail, "b_t0", (-0.2, y, 0.3), "green", r=0.07, h=0.16, shape="round")
    wl.bottle(detail, "b_t1", (-0.05, y, -0.08), "purple", r=0.06, h=0.22, shape="tall")
    wl.bottle(detail, "b_t2", (0.22, y, 0.3), "yellow", r=0.06, h=0.16, shape="flask")
    wl.bowl(detail, "dish", (-1.32, y, 0.32), r=0.12, h=0.06, content="cobble")
    wl.parchment(detail, "scroll", (-0.2, y + 0.005, 0.05), w=0.26, d=0.34, yaw=0.4)
    wl.book_stack(detail, "books_t", (0.2, y, -0.12), 2, rng, w=0.32, d=0.24)
    # under the table: a crate, jars, books on the lower shelf
    wl.crate(t, "under_crate", (-1.38, 0.28, -0.02), s=0.48, yaw=0.1, solid=False)
    wl.jar(detail, "under_jar0", (-0.8, 0.28, 0.0), r=0.11, h=0.3, region="clay")
    wl.jar(detail, "under_jar1", (-0.5, 0.28, 0.05), r=0.09, h=0.24)
    wl.book_stack(detail, "under_books", (-0.05, 0.28, 0.05), 3, rng, w=0.34, d=0.26)


def shelves(root, detail, rng):
    s = wl.Bone("shelves", parent=root)
    x0, x1 = -1.88, -0.02
    for k, y in enumerate((1.6, 2.3)):
        wl.shelf(s, "shelf_%d" % k, x0, x1, WALL_Z, y, depth=0.36, th=0.08, region="plank", brackets=3)
    wl.collide((x0, 1.3, WALL_Z, x1, 2.35, WALL_Z + 0.36))
    zc = WALL_Z + 0.17
    # lower shelf: big round vials; upper shelf: tall bottles and the amethyst cluster
    low = (("pink", "round", 0.12, 0.24), ("blue", "round", 0.12, 0.25), ("green", "round", 0.115, 0.23),
           ("teal", "round", 0.115, 0.22), ("purple", "tall", 0.08, 0.28))
    x = x0 + 0.2
    for k, (col, shape, r, h) in enumerate(low):
        wl.bottle(detail, "vial_l_%d" % k, (x, 1.6, zc + 0.02 * (k % 2)), col, r=r, h=h, shape=shape, neck_h=0.1)
        x += 0.31
    up = (("green", "tall", 0.09, 0.3), ("orange", "round", 0.11, 0.22), ("orange", "tall", 0.085, 0.28))
    x = x0 + 0.22
    for k, (col, shape, r, h) in enumerate(up):
        wl.bottle(detail, "vial_u_%d" % k, (x, 2.3, zc), col, r=r, h=h, shape=shape, neck_h=0.1)
        x += 0.33
    wl.crystal_cluster(s, "amethyst", (-0.68, 2.3, zc), "purple", rng, n=7, h=0.6, w=0.14, spread=0.15)
    wl.jar(detail, "shelf_jar", (-0.22, 2.3, zc), r=0.09, h=0.24, region="clay")
    # books standing at the right end of the lower shelf
    wl.book_row(detail, "shelf_books", -0.36, -0.06, 1.6, WALL_Z + 0.34, 0.28, rng, hmin=0.26, hmax=0.34)


def apparatus(root, detail, rng):
    a = wl.Bone("apparatus", parent=root)
    # the right counter (set back a little)
    wl.table(a, "counter", 0.42, 1.62, -0.84, 0.22, 0.98, top_th=0.14, leg=0.18, top_region="plank_dark", leg_region="wood_dark",
             shelf_y=0.28)
    # brass stand round a little burner, the big flask on it (lit green), its neck and a copper pipe
    f = FLASK
    for k in range(3):
        ang = 2 * math.pi * k / 3 + 0.4
        foot = f + v3(math.cos(ang) * 0.24, 0, math.sin(ang) * 0.24)
        wl.beam(a, "stand_leg_%d" % k, foot, f + v3(math.cos(ang) * 0.2, 0.3, math.sin(ang) * 0.2), 0.04, "brass", width=0.04)
    for k in range(8):
        a0, a1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
        wl.beam(detail, "stand_ring_%d" % k, f + v3(math.cos(a0) * 0.21, 0.3, math.sin(a0) * 0.21),
                f + v3(math.cos(a1) * 0.21, 0.3, math.sin(a1) * 0.21), 0.035, "brass", width=0.035, extend=0.01)
    wl.candle(a, "burner", f, h=0.12, r=0.06, holder="iron_dark")
    body = f + UP * 0.27
    # a round flask: stacked rings (green lit liquid below, clear glass above)
    rings = ((0.0, 0.06, 0.18, "potion_green"), (0.06, 0.1, 0.27, "potion_brew"), (0.16, 0.16, 0.33, "potion_brew"),
             (0.32, 0.1, 0.3, "potion_green"), (0.42, 0.07, 0.24, "glass"), (0.49, 0.05, 0.15, "glass"))
    for k, (y, hh, r, reg) in enumerate(rings):
        pre = "glow_" if reg != "glass" else ""
        wl.octo(a, "%sflask_%d" % (pre, k), body + UP * y, r, hh, {"all": reg}, stretch=True, k=0.9)
    neck0 = body + UP * 0.54
    wl.add_cube(a, "flask_neck", neck0 + UP * 0.12, wl.EYE, (0.11, 0.24, 0.11), "glass", stretch=True)
    wl.add_cube(a, "flask_collar", neck0 + UP * 0.25, wl.EYE, (0.15, 0.05, 0.15), "copper")
    p = [neck0 + UP * 0.27, neck0 + UP * 0.62, neck0 + UP * 0.62 + v3(0.62, 0, 0), neck0 + v3(0.62, 0.2, 0)]
    for k in range(3):
        wl.beam(a, "pipe_%d" % k, p[k], p[k + 1], 0.07, "copper", width=0.07, extend=0.035)
    for k, q in enumerate(p[1:3]):
        wl.add_cube(a, "pipe_joint_%d" % k, q, wl.EYE, (0.11, 0.11, 0.11), "brass")
    # the collecting bottle under the pipe's end, a clamp post holding the pipe
    wl.bottle(a, "collector", (p[3][0], 0.98, p[3][2]), "green", r=0.1, h=0.22, shape="round", neck_h=0.1, cork=False)
    wl.beam(detail, "clamp_post", (p[2][0] + 0.18, 0.98, p[2][2] - 0.12), (p[2][0] + 0.18, p[2][1] + 0.05, p[2][2] - 0.12), 0.05,
            "wood_dark", width=0.05)
    wl.beam(detail, "clamp", (p[2][0] + 0.18, p[2][1], p[2][2] - 0.12), (p[2][0] - 0.02, p[2][1], p[2][2]), 0.04, "iron_dark", width=0.04)
    # mortar and pestle, small bottles, a jar of herbs
    wl.mortar(a, "mortar", (1.12, 0.98, -0.6), r=0.2, h=0.16)
    wl.bottle(detail, "b_c0", (1.15, 0.98, 0.1), "teal", r=0.07, h=0.16)
    wl.bottle(detail, "b_c1", (0.52, 0.98, 0.08), "green", r=0.06, h=0.2, shape="tall")
    wl.jar(detail, "herb_jar", (1.45, 0.98, 0.05), r=0.09, h=0.22, region="clay")
    wl.crossed(detail, "herb_jar_plant", (1.45, 1.36, 0.05), 0.28, 0.24, "herbs")
    # under the counter: bottles in a crate
    wl.box(a, "bottle_crate", (0.62, 0.28, -0.55), (1.22, 0.5, -0.05), "crate", stretch=True)
    for k in range(4):
        wl.bottle(detail, "crate_b_%d" % k, (0.74 + 0.13 * k, 0.5, -0.3 + 0.06 * (k % 2)), ("green", "blue", "red", "yellow")[k], r=0.045,
                  h=0.12, shape="tall")


def outside(root, detail, rng):
    o = wl.Bone("outside", parent=root)
    # the banner with the flask emblem, hanging from a rod in front of the right part of the back wall
    wl.banner(o, "banner", (1.12, Y_TOP - 0.5, WALL_Z + 0.1), 0.9, 1.7, "banner_flask", normal=(0, 0, 1))
    for k, x in enumerate((1.12 - 0.55, 1.12 + 0.55)):
        wl.add_cube(o, "banner_hook_%d" % k, (x, Y_TOP - 0.47, WALL_Z + 0.05), wl.EYE, (0.05, 0.05, 0.12), "iron_dark")
    # the barrel at the front right, a yellow bottle and a small crate on the ground
    wl.barrel(o, "barrel", (1.72, 0, 0.78), r=0.42, h=1.0, staves=10)
    wl.bottle(detail, "ground_bottle", (1.0, 0, 0.62), "yellow", r=0.11, h=0.24, shape="round", neck_h=0.12)
    wl.bottle(detail, "ground_bottle_b", (0.75, 0, 0.75), "orange", r=0.07, h=0.18, shape="tall")


def build():
    rng = random.Random(23)
    root = wl.Bone(NAME)
    detail = wl.Bone("detail", parent=root)
    frame(root, detail, rng)
    table(root, detail, rng)
    shelves(root, detail, rng)
    apparatus(root, detail, rng)
    outside(root, detail, rng)
    return root


def icon(path):
    """32x32: a round flask of glowing green liquid with a cork and bubbles."""
    im, d = wl.new_icon(32)
    d.ellipse([5, 11, 27, 31], fill=(210, 225, 230, 255))
    d.ellipse([7, 13, 25, 29], fill=(150, 200, 210, 255))
    d.chord([7, 13, 25, 29], 200, 340, fill=(150, 200, 210, 255))
    d.pieslice([7, 13, 25, 29], 0, 180, fill=(80, 220, 60, 255))
    d.rectangle([7, 20, 25, 21], fill=(120, 240, 90, 255))
    d.rectangle([13, 3, 19, 12], fill=(210, 225, 230, 255))
    d.rectangle([14, 4, 18, 12], fill=(150, 200, 210, 255))
    d.rectangle([12, 1, 20, 4], fill=(160, 120, 70, 255))
    d.rectangle([10, 15, 11, 18], fill=(255, 255, 255, 220))
    for x, y in ((14, 24), (18, 22), (20, 26)):
        d.rectangle([x, y, x + 1, y + 1], fill=(200, 255, 170, 255))
    wl.save_icon(im, path)


def main():
    wl.setup(NAME)
    root = build()
    neck = FLASK + UP * 0.9
    particles = [
        {"type": "witch", "pos": (neck[0], neck[1], neck[2]), "chance": 0.25, "count": 1},
        {"type": "small_flame", "pos": (-1.62, 1.6, 0.12), "chance": 0.08, "count": 1},
    ]
    wl.export(root, NAME, particles=particles, icon=icon, visible_box=(8, 5, 0))


if __name__ == "__main__":
    main()
