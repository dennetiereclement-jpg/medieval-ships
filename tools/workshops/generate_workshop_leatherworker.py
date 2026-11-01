#!/usr/bin/env python3
"""workshop_leatherworker — Atelier du tailleur de cuir / Leatherworker's Workshop
(reference: scratchpad/ref/workshop_leatherworker_ref.png).

A plank-roofed wooden stall: a big hide stretched and laced on a wooden frame against the back wall, the workbench in
front with leather draped over it (pieces, knives, an awl, a mallet), a back counter with a lit lantern, iron-banded
crates at the front left, a banded chest with leather rolls at the front right, a shelf with a hanging leather jacket
and a pot of herbs, a leather hide hanging from the roof beam.

Usage:  python3 tools/workshops/generate_workshop_leatherworker.py    (WS_OUT=<file>: only the model, for previews)
Workshop-local coordinates: y up, +z = front, the anchor block (0, 0, 0) is inside the workbench.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wslib_a as wl  # noqa: E402

NAME = "workshop_leatherworker"
UP, v3 = wl.UP, wl.v3
XP = 2.25                 # corner posts at x = +-XP
ZF, ZB = 0.5, -1.38
TOP = 2.9                 # top of the posts / beams
WALL_Z = -1.42


def frame(root, detail):
    b = wl.Bone("frame", parent=root)
    for s in (1, -1):
        for k, z in enumerate((ZF, ZB)):
            wl.post(b, "post_%d_%d" % (s, k), (s * XP, 0.0, z), (s * XP, TOP, z), d=0.26, region="wood")
        wl.beam(b, "side_beam_%d" % s, (s * XP, TOP - 0.1, ZB - 0.2), (s * XP, TOP - 0.1, ZF + 0.25), 0.2, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
        wl.bracket(detail, "brace_%d" % s, (s * XP, TOP - 0.62, ZF), (s * (XP - 0.5), TOP - 0.15, ZF), d=0.11)
    for e, z in (("f", ZF), ("b", ZB)):
        wl.beam(b, "beam_" + e, (-XP - 0.35, TOP + 0.02, z), (XP + 0.35, TOP + 0.02, z), 0.24, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    # middle post between the hide frame and the shelves
    wl.post(b, "post_mid", (0.62, 0.0, -1.22), (0.62, TOP, -1.22), d=0.24, region="wood")
    # the back wall: vertical boards
    n = 16
    for k in range(n):
        x = -XP + (k + 0.5) * (2 * XP / n)
        wl.beam(b, "wall_%d" % k, (x, 0.0, WALL_Z), (x, TOP - 0.1, WALL_Z), 0.07, "plank_dark", width=2 * XP / n * 0.99, up=v3(0, 0, 1))
    wl.beam(b, "wall_rail_0", (-XP, 0.95, WALL_Z + 0.06), (XP, 0.95, WALL_Z + 0.06), 0.1, "wood_dark", up=UP)
    wl.collide((-XP, 0.0, WALL_Z - 0.05, XP, TOP, WALL_Z + 0.05))
    # rafters and the flat plank roof
    for k, x in enumerate((-2.1, -1.05, 0.0, 1.05, 2.1)):
        wl.beam(b, "rafter_%d" % k, (x, TOP + 0.2, ZB - 0.45), (x, TOP + 0.12, ZF + 0.65), 0.16, {"all": "wood", "+1": "end_grain", "-1": "end_grain"})
    wl.plank_roof(b, "roof", -XP - 0.3, XP + 0.3, ZB - 0.45, ZF + 0.6, TOP + 0.48, TOP + 0.38, th=0.2, plank_w=0.32, fascia="wood_dark")
    return b


def hide_frame(root, detail):
    """The big hide laced on a frame of poles leaning against the back wall."""
    h = wl.Bone("hide", parent=root)
    x0, x1, y0, y1, z = -1.98, 0.42, 1.08, 2.82, -1.2
    for k, x in enumerate((x0, x1)):
        wl.beam(h, "hf_post_%d" % k, (x, 0.0, z), (x, y1 + 0.12, z), 0.14, {"all": "hide_frame", "+1": "end_grain", "-1": "end_grain"})
    for k, y in enumerate((y0, y1)):
        wl.beam(h, "hf_bar_%d" % k, (x0 - 0.12, y, z + 0.02), (x1 + 0.12, y, z + 0.02), 0.12, "hide_frame", extend=0.02)
    # a round hoop behind the hide (the frame of the picture)
    c = v3((x0 + x1) / 2, (y0 + y1) / 2, z - 0.08)
    r = 1.0
    segs = 14
    pts = [c + v3(math.cos(2 * math.pi * k / segs) * r, math.sin(2 * math.pi * k / segs) * r, 0) for k in range(segs)]
    for k in range(segs):
        wl.beam(h, "hoop_%d" % k, pts[k], pts[(k + 1) % segs], 0.09, "wood_dark", width=0.09, up=v3(0, 0, 1), extend=0.035)
    # the hide (transparent outline) and the lacing from its edge to the frame
    hc = v3((x0 + x1) / 2, (y0 + y1) / 2 + 0.02, z + 0.1)
    wl.plate(h, "hide_skin", hc, (0, 0, 1), UP, 2.3, 2.05, "hide", th=0.02)
    for k in range(10):
        a = 2 * math.pi * (k + 0.5) / 10
        p_edge = hc + v3(math.cos(a) * 0.78, math.sin(a) * 0.7, 0.0)
        tgt = v3(min(x1, max(x0, hc[0] + math.cos(a) * 1.4)), min(y1, max(y0, hc[1] + math.sin(a) * 1.2)), z + 0.06)
        wl.rope(detail, "lace_%d" % k, p_edge, tgt, d=0.03, region="leather_dark")
    # pegs holding the hide corners
    for k, (dx, dy) in enumerate(((-0.95, 0.88), (0.95, 0.88), (-0.95, -0.88), (0.95, -0.88))):
        wl.box(detail, "hide_peg_%d" % k, hc + v3(dx - 0.03, dy - 0.03, -0.02), hc + v3(dx + 0.03, dy + 0.03, 0.06), "wood_dark")
    wl.collide((x0 - 0.1, 0.0, z - 0.15, x1 + 0.1, y1, z + 0.15))
    return h


def bench(root, detail):
    b = wl.Bone("bench", parent=root)
    # the main workbench (the anchor is inside it), leather draped over its front
    wl.table(b, "bench", -1.25, 1.35, -0.5, 0.5, 1.0, top="plank", leg="wood", top_th=0.12, leg_d=0.18, shelf=True)
    wl.draped(b, "drape", -0.4, 0.75, -0.3, 0.5, 1.0, 0.5, "leather_red", out_dir=1, nx=3)
    # rolls of leather on the shelf under the top
    for k, (x, reg) in enumerate(((-0.65, "leather"), (-0.2, "leather_dark"), (0.85, "leather_tan"))):
        wl.octo(b, "shelf_roll_%d" % k, (x, 0.42, -0.3), (x, 0.42, 0.3), 0.13, reg, end="leather_dark")
    # things on the bench: cut pieces, knives, an awl, a mallet, a small box, a pot of dye, thread
    wl.rbox(detail, "piece_0", (-0.85, 1.0, 0.05), (0.42, 0.015, 0.3), 0.25, "leather", stretch=True)
    wl.rbox(detail, "piece_1", (-0.7, 1.015, -0.2), (0.3, 0.015, 0.22), -0.4, "leather_tan", stretch=True)
    wl.knife(detail, "knife_0", (-1.1, 1.02, 0.3), (1, 0, -0.2), length=0.26)
    wl.knife(detail, "knife_1", (0.95, 1.02, 0.25), (-1, 0, 0.5), length=0.22)
    wl.beam(detail, "awl", (-0.35, 1.02, 0.3), (-0.2, 1.02, 0.22), 0.02, "steel")
    wl.beam(detail, "awl_grip", (-0.47, 1.025, 0.36), (-0.35, 1.025, 0.3), 0.04, "wood")
    wl.beam(detail, "mallet_handle", (0.95, 1.03, -0.05), (1.25, 1.03, -0.3), 0.035, "wood")
    wl.beam(detail, "mallet_head", (0.88, 1.06, 0.02), (1.02, 1.06, -0.12), 0.11, "wood_dark", up=v3(1, 0, 1))
    wl.crate(b, "small_box", (-0.45, 1.0, -0.22), size=(0.3, 0.18, 0.22), solid=False, lid=True)
    wl.octo(detail, "dye_pot", (0.15, 1.0, -0.28), (0.15, 1.16, -0.28), 0.08, "leather_dark", end="coal")
    wl.octo(detail, "thread_spool", (0.42, 1.0, -0.3), (0.42, 1.09, -0.3), 0.045, "spools")
    # the back counter (higher), a lit lantern, jars and a leather roll on it
    wl.table(b, "counter", -1.7, 0.62, -1.15, -0.72, 1.2, top="plank_dark", leg="wood_dark", top_th=0.1, leg_d=0.14)
    wl.standing_lantern(b, "lantern", (0.42, 1.2, -0.92), size=0.32)
    for k, x in enumerate((-1.45, -1.25)):
        wl.octo(detail, "jar_%d" % k, (x, 1.2, -0.95), (x, 1.4 - 0.05 * k, -0.95), 0.08, "glass", end="leather_dark")
    wl.octo(b, "counter_roll", (-0.95, 1.31, -0.95), (-0.35, 1.31, -0.95), 0.11, "leather", end="leather_dark")
    wl.rbox(detail, "counter_box", (-0.05, 1.2, -0.95), (0.2, 0.14, 0.18), 0.2, "crate", stretch=True)
    return b


def left_crates(root, detail):
    c = wl.Bone("crates", parent=root)
    wl.crate(c, "crate_big", (-1.88, 0.0, 0.18), size=(1.05, 0.98, 0.9), solid=True)
    wl.chest(c, "crate_top", (-1.88, 0.98, 0.15), size=(0.92, 0.26, 0.74), detail=detail)
    # leather straps and buckles down the big crate's front
    for k, x in enumerate((-2.15, -1.6)):
        wl.box(detail, "strap_%d" % k, (x - 0.05, 0.08, 0.635), (x + 0.05, 0.92, 0.66), "leather_dark")
        wl.box(detail, "buckle_%d" % k, (x - 0.06, 0.48, 0.655), (x + 0.06, 0.6, 0.67), "brass")
    return c


def right_side(root, detail):
    r = wl.Bone("right", parent=root)
    # the banded chest at the front right with two rolls of leather on it
    wl.chest(r, "chest", (1.9, 0.0, 0.1), size=(0.95, 0.7, 0.72), detail=detail)
    wl.octo(r, "roll_0", (1.5, 0.98, -0.02), (2.3, 0.98, -0.02), 0.13, "leather", end="leather_dark")
    wl.octo(r, "roll_1", (1.55, 0.97, 0.26), (2.25, 0.97, 0.26), 0.12, "leather_dark", end="leather")
    wl.box(detail, "roll_strap_0", (1.88, 0.83, -0.17), (1.94, 1.13, 0.13), "leather_dark")
    # a leather satchel on the chest's lid
    wl.rbox(r, "satchel", (2.15, 0.84, 0.42), (0.36, 0.26, 0.16), 0.15, {"all": "leather_dark", "+3": "jacket"}, stretch=True)
    wl.rbox(detail, "satchel_flap", (2.15, 1.04, 0.43), (0.37, 0.08, 0.18), 0.15, "leather")
    wl.beam(detail, "satchel_strap", (1.98, 1.1, 0.4), (2.32, 1.1, 0.46), 0.02, "leather_dark", width=0.04)
    # the shelf behind it, the hanging jacket on a rail, a pot of herbs on top
    wl.shelf_rack(r, "shelf", 1.0, 2.05, -1.3, -0.55, (0.55, 1.2, 1.95), 2.0, back=None)
    wl.beam(r, "jacket_rail", (1.05, 1.88, -0.48), (2.0, 1.88, -0.48), 0.05, "wood_dark")
    jc = v3(1.55, 1.42, -0.45)
    wl.rbox(r, "jacket_body", jc - UP * 0.42, (0.62, 0.8, 0.14), 0.0, {"all": "jacket"}, stretch=True)
    for s in (1, -1):
        wl.beam(r, "jacket_sleeve_%d" % s, jc + v3(s * 0.3, 0.28, 0.0), jc + v3(s * 0.4, -0.3, 0.02), 0.14, "jacket", width=0.12)
    wl.beam(detail, "jacket_hanger", jc + v3(-0.25, 0.42, 0.0), jc + v3(0.25, 0.42, 0.0), 0.03, "wood")
    wl.beam(detail, "jacket_hook", jc + v3(0, 0.42, 0), jc + v3(0, 0.48, 0), 0.02, "iron")
    wl.octo(r, "herb_pot", (1.55, 2.0, -0.95), (1.55, 2.2, -0.95), 0.2, "pot_green", end="herbs")
    wl.rbox(r, "herb_top", (1.55, 2.2, -0.95), (0.36, 0.14, 0.36), 0.4, "herbs", stretch=True)
    wl.rbox(detail, "herb_top2", (1.55, 2.3, -0.95), (0.22, 0.08, 0.22), 1.2, "herbs", stretch=True)
    # folded leathers on the shelves
    for k, (y, reg) in enumerate(((0.55, "leather"), (0.6, "leather_dark"), (1.2, "leather_tan"), (1.25, "leather"))):
        wl.rbox(detail, "folded_%d" % k, (1.3 + 0.45 * (k % 2), y, -0.92), (0.38, 0.05, 0.5), 0.05 * k, reg, stretch=True)
    wl.chest(r, "small_chest", (1.55, 1.2, -0.95), size=(0.4, 0.2, 0.3), solid=False, detail=detail)
    return r


def hanging(root, detail):
    h = wl.Bone("hanging", parent=root)
    # a leather hide hanging over the front beam at the top left
    wl.hanging_cloth(h, "hang_hide", (-2.15, TOP + 0.1, ZF + 0.14), (-1.45, TOP + 0.1, ZF + 0.14), 0.75, "drape", sway=0.04)
    wl.hanging_cloth(h, "hang_hide_back", (-2.15, TOP + 0.1, ZF - 0.14), (-1.45, TOP + 0.1, ZF - 0.14), 0.35, "leather_red", sway=0.02)
    # tools hanging on the back wall right of the frame: knives and a round knife
    for k, x in enumerate((0.85, 1.0)):
        wl.knife(detail, "wall_knife_%d" % k, (x, 2.55, WALL_Z + 0.06), (0, -1, 0), length=0.3)
    wl.box(detail, "wall_peg_row", (0.75, 2.56, WALL_Z + 0.02), (1.1, 2.6, WALL_Z + 0.1), "wood_dark")
    # a drying line under the roof with leather pieces
    # leather pieces hanging on pegs from the right end of the back wall, above the shelf
    for k, (x, reg, L) in enumerate(((1.25, "leather_tan", 0.42), (1.6, "leather", 0.5), (1.95, "leather_dark", 0.38))):
        wl.box(detail, "piece_peg_%d" % k, (x - 0.03, 2.62, WALL_Z + 0.03), (x + 0.03, 2.67, WALL_Z + 0.14), "wood_dark")
        wl.hanging_cloth(h, "piece_hang_%d" % k, (x - 0.14, 2.62, WALL_Z + 0.1), (x + 0.14, 2.62, WALL_Z + 0.1), L, reg, sway=0.02, nx=1, ny=2)
    # a strap of belts hanging on the left post
    for k in range(3):
        wl.beam(detail, "belt_%d" % k, (-XP + 0.15, 2.3, ZF - 0.05 + 0.06 * k), (-XP + 0.15, 1.5 + 0.12 * k, ZF - 0.05 + 0.06 * k), 0.012,
                "leather_dark", width=0.06, up=v3(1, 0, 0))
    return h


def extras(root, detail):
    """Under the back counter: a stack of hides and a bucket; tools on the wall; thread and twine on the shelf."""
    e = wl.Bone("extras", parent=root)
    for k, (reg, yaw) in enumerate((("leather", 0.0), ("leather_tan", 0.12), ("leather_dark", -0.08), ("leather", 0.2))):
        wl.rbox(e, "hide_stack_%d" % k, (-1.0 + 0.02 * k, 0.07 * k, -0.95), (0.72, 0.07, 0.36), yaw, reg, stretch=True)
    wl.tub(e, "bucket", (-0.25, 0.0, -0.95), r=0.18, h=0.32, staves=8, handles=False, solid=False)
    wl.beam(detail, "bucket_stick", (-0.28, 0.2, -0.95), (-0.15, 0.55, -0.88), 0.03, "wood")
    # a half-moon round knife and awls on the wall, right of the frame
    wl.box(detail, "awl_rack", (0.75, 2.2, WALL_Z + 0.03), (1.15, 2.25, WALL_Z + 0.12), "wood_dark")
    for k in range(4):
        x = 0.8 + 0.1 * k
        wl.beam(detail, "rack_awl_%d" % k, (x, 2.2, WALL_Z + 0.09), (x, 2.05, WALL_Z + 0.09), 0.015, "steel")
        wl.beam(detail, "rack_awl_grip_%d" % k, (x, 2.32, WALL_Z + 0.09), (x, 2.22, WALL_Z + 0.09), 0.035, "wood")
    wl.plate(detail, "round_knife", (0.95, 1.78, WALL_Z + 0.06), (0, 0, 1), UP, 0.24, 0.14, "steel", th=0.012)
    wl.beam(detail, "round_knife_grip", (0.95, 1.85, WALL_Z + 0.06), (0.95, 2.0, WALL_Z + 0.06), 0.035, "wood")
    # thread, twine balls and a box of rivets on the shelf
    for k in range(3):
        wl.octo(detail, "shelf_spool_%d" % k, (1.15 + 0.15 * k, 1.95, -0.7), (1.15 + 0.15 * k, 2.05, -0.7), 0.045, "spools")
    for k, x in enumerate((1.25, 1.45)):
        wl.rbox(detail, "twine_%d" % k, (x, 0.55, -0.7), (0.15, 0.14, 0.15), 0.7 * k, "rope", stretch=True)
    wl.crate(e, "rivet_box", (1.85, 0.55, -0.8), size=(0.3, 0.14, 0.24), solid=False, lid=False)
    wl.rbox(detail, "rivets", (1.85, 0.69, -0.8), (0.24, 0.01, 0.18), 0.0, "brass", stretch=True)
    return e


def build():
    root = wl.Bone(NAME)
    detail = wl.Bone("detail", parent=root)
    frame(root, detail)
    hide_frame(root, detail)
    bench(root, detail)
    left_crates(root, detail)
    right_side(root, detail)
    hanging(root, detail)
    extras(root, detail)
    return root


def icon(path):
    """A stretched hide (the reference sheet's pictogram)."""
    im = wl.icon_canvas()
    rows = [
        "................",
        "...L........L...",
        "...LL..LL..LL...",
        "....LLLLLLLL....",
        "....LLLLLLLL....",
        "...LLLLLLLLLL...",
        "..LLLLLdLLLLLL..",
        "..LLLLLdLLLLLL..",
        "...LLLLdLLLLL...",
        "....LLLLLLLL....",
        "....LLLLLLLL....",
        "...LLLLLLLLLL...",
        "...LL..LL..LL...",
        "...L...LL...L...",
        "................",
        "................",
    ]
    wl.icon_draw(im, rows, {"L": (176, 118, 66), "d": (120, 76, 40)})
    p = im.load()
    for y in range(16):
        for x in range(16):
            if p[x, y][3] and (x == 0 or y == 0 or not p[x - 1, y][3] or not p[x, y - 1][3]):
                p[x, y] = (110, 70, 36, 255)
    im.save(path)


def main():
    wl.setup(NAME)
    root = build()
    wl.export(root, NAME, None, icon=icon, particles=[], visible_box=(8, 5, 0))


if __name__ == "__main__":
    main()
