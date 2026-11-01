#!/usr/bin/env python3
"""workshop_tailor — Atelier du tailleur de lin / Tailor's Workshop (reference: scratchpad/ref/workshop_tailor_ref.png).

A wooden stall: a loom in the middle (warp threads from the back beam to the breast beam, the woven blue and white
cloth hanging over the front), shelves of cloth rolls at the back right (blue, white, beige, red) with thread
spools, white and blue cloths hanging from the front beam, a tunic on a mannequin stand at the front left, a sewing
table at the front right under a blue runner with a gold fringe (scissors, spools, folded cloth, a lit lantern), a
sack, a lantern on an arm at the top left.

Usage:  python3 tools/workshops/generate_workshop_tailor.py    (WS_OUT=<file>: only the model, for previews)
Workshop-local coordinates: y up, +z = front, the anchor block (0, 0, 0) is inside the loom (the weaver's place).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wslib_a as wl  # noqa: E402

NAME = "workshop_tailor"
UP, v3 = wl.UP, wl.v3
XP = 2.3
ZF, ZB = 0.45, -1.35
TOP = 2.85
WALL_Z = -1.4


def frame(root, detail):
    b = wl.Bone("frame", parent=root)
    for s in (1, -1):
        for k, z in enumerate((ZF, ZB)):
            wl.post(b, "post_%d_%d" % (s, k), (s * XP, 0.0, z), (s * XP, TOP, z), d=0.26, region="wood")
        wl.beam(b, "side_beam_%d" % s, (s * XP, TOP - 0.1, ZB - 0.25), (s * XP, TOP - 0.1, ZF + 0.3), 0.22, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
        wl.bracket(detail, "brace_%d" % s, (s * XP, TOP - 0.6, ZF), (s * (XP - 0.5), TOP - 0.12, ZF), d=0.11)
    for e, z in (("f", ZF), ("b", ZB)):
        wl.beam(b, "beam_" + e, (-XP - 0.4, TOP + 0.02, z), (XP + 0.4, TOP + 0.02, z), 0.26, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    # a second, higher front beam (the heavy frame of the picture) and short posts between them
    wl.beam(b, "beam_f2", (-XP - 0.3, TOP + 0.38, ZF + 0.05), (XP + 0.3, TOP + 0.38, ZF + 0.05), 0.2, {"all": "wood", "+1": "end_grain", "-1": "end_grain"})
    for k, x in enumerate((-1.2, 0.0, 1.2)):
        wl.beam(detail, "king_%d" % k, (x, TOP + 0.12, ZF + 0.02), (x, TOP + 0.3, ZF + 0.02), 0.14, "wood")
    # back rails between the back posts (open back, as in the picture)
    for k, y in enumerate((0.9, 1.9)):
        wl.beam(b, "back_rail_%d" % k, (-XP, y, ZB), (XP, y, ZB), 0.12, "wood_dark", up=UP)
    for k, x in enumerate((-2.1, -1.05, 0.0, 1.05, 2.1)):
        wl.beam(b, "rafter_%d" % k, (x, TOP + 0.24, ZB - 0.45), (x, TOP + 0.16, ZF + 0.7), 0.16, {"all": "wood", "+1": "end_grain", "-1": "end_grain"})
    wl.plank_roof(b, "roof", -XP - 0.3, XP + 0.3, ZB - 0.45, ZF + 0.55, TOP + 0.52, TOP + 0.44, th=0.18, plank_w=0.32, fascia=None)
    return b


def loom(root, detail):
    """The loom: two side frames, the warp beam at the back top, the breast beam at the front, the warp threads,
    the beater, the woven cloth over the breast beam."""
    lm = wl.Bone("loom", parent=root)
    x0, x1 = -1.3, 0.55
    zf, zb = 0.42, -0.72
    yf, yb = 0.98, 1.72
    for k, x in enumerate((x0, x1)):
        wl.beam(lm, "front_post_%d" % k, (x, 0.0, zf), (x, yf + 0.12, zf), 0.16, {"all": "wood", "+1": "end_grain", "-1": "end_grain"})
        wl.beam(lm, "back_post_%d" % k, (x, 0.0, zb), (x, yb + 0.25, zb), 0.16, {"all": "wood", "+1": "end_grain", "-1": "end_grain"})
        wl.beam(lm, "side_low_%d" % k, (x, 0.22, zb), (x, 0.22, zf), 0.12, "wood_dark")
        wl.beam(lm, "side_top_%d" % k, (x, yf + 0.06, zf), (x, yb + 0.06, zb), 0.11, "wood_dark", extend=0.05)
        wl.beam(lm, "castle_%d" % k, (x, yf + 0.06, -0.15), (x, 1.95, -0.15), 0.1, "wood")
        # the feet
        wl.beam(lm, "foot_%d" % k, (x, 0.05, zb - 0.12), (x, 0.05, zf + 0.12), 0.1, "wood_dark", width=0.18)
    wl.beam(lm, "castle_top", (x0 - 0.06, 1.95, -0.15), (x1 + 0.06, 1.95, -0.15), 0.1, "wood_dark", extend=0.04)
    wl.octo(lm, "breast_beam", (x0 - 0.1, yf, zf), (x1 + 0.1, yf, zf), 0.08, "wood", end="end_grain")
    wl.octo(lm, "warp_beam", (x0 - 0.1, yb, zb), (x1 + 0.1, yb, zb), 0.1, "wood", end="end_grain")
    wl.octo(lm, "cloth_beam", (x0 - 0.06, 0.55, zf - 0.08), (x1 + 0.06, 0.55, zf - 0.08), 0.1, "woven", end="roll_white")
    wl.beam(lm, "stretcher_back", (x0, 0.22, zb), (x1, 0.22, zb), 0.1, "wood_dark")
    # warp threads (two sheets, the shed open) from the warp beam to the fell of the cloth
    fell = v3(0, yf + 0.06, zf - 0.32)
    a, b_ = v3(x0 + 0.1, yb + 0.02, zb), v3(x1 - 0.1, yb + 0.02, zb)
    for k, dy in enumerate((0.04, -0.05)):
        def P(s, t, dy=dy):
            top = a + (b_ - a) * s
            bot = v3(top[0], fell[1], fell[2])
            mid = 0.5
            p = top + (bot - top) * t
            return p + UP * (dy * math.sin(math.pi * min(1.0, t / mid) / 2) * (1 - max(0, t - mid) / (1 - mid)))
        wl.loft(lm, "warp_%d" % k, P, 2, 2, "warp", th=0.01)
    # the woven cloth: on the loom from the fell to the breast beam, then hanging down the front
    def W(s, t):
        x = x0 + 0.1 + (x1 - x0 - 0.2) * s
        if t < 0.35:
            tt = t / 0.35
            return v3(x, fell[1] + 0.01 + (yf + 0.09 - fell[1]) * tt, fell[2] + (zf + 0.02 - fell[2]) * tt)
        tt = (t - 0.35) / 0.65
        return v3(x, yf + 0.09 - 0.55 * tt, zf + 0.09 + 0.03 * math.sin(s * 9) * tt)
    wl.loft(lm, "woven", W, 3, 3, "woven", th=0.02)
    # the beater (reed) hanging from the castle, and the heddle bars
    wl.beam(lm, "beater_bar", (x0 + 0.05, 1.2, -0.05), (x1 - 0.05, 1.2, -0.05), 0.1, "wood", width=0.08)
    for k, x in enumerate((x0 + 0.08, x1 - 0.08)):
        wl.beam(detail, "beater_arm_%d" % k, (x, 1.2, -0.05), (x, 1.93, -0.15), 0.05, "wood_dark")
    wl.beam(detail, "heddle_bar_0", (x0 + 0.05, 1.62, -0.3), (x1 - 0.05, 1.62, -0.3), 0.04, "wood_dark")
    wl.beam(detail, "heddle_bar_1", (x0 + 0.05, 1.45, -0.3), (x1 - 0.05, 1.45, -0.3), 0.04, "wood_dark")
    # treadles
    for k, x in enumerate((-0.6, -0.2)):
        wl.beam(detail, "treadle_%d" % k, (x, 0.08, zb + 0.1), (x, 0.14, zf - 0.05), 0.04, "wood", width=0.08)
    # a shuttle lying on the woven cloth
    wl.rbox(detail, "shuttle", (-0.6, yf + 0.06, zf - 0.2), (0.32, 0.05, 0.07), 0.05, "wood_dark")
    wl.collide((x0 - 0.1, 0.0, zb - 0.1, x1 + 0.1, 1.15, zf + 0.12))
    wl.collide((x0 - 0.1, 0.0, zb - 0.1, x1 + 0.1, 2.0, -0.05))
    return lm


def shelves(root, detail):
    s = wl.Bone("shelves", parent=root)
    x0, x1, z0, z1 = 0.78, 2.18, -1.3, -0.72
    wl.shelf_rack(s, "rack", x0, x1, z0, z1, (0.72, 1.35, 1.98, 2.55), 2.62)
    zc = (z0 + z1) / 2
    for k, (xa, xb, y, reg, end, r) in enumerate((
            (0.85, 1.48, 1.98, "cloth_blue", "roll_blue", 0.17), (1.5, 2.12, 1.98, "cloth_white", "roll_white", 0.17),
            (0.85, 1.45, 1.35, "linen", "roll_beige", 0.17), (1.48, 2.12, 1.35, "cloth_red", "roll_red", 0.17))):
        wl.cloth_roll(s, "roll_%d" % k, (xa, y + r, zc), (xb, y + r, zc), r, reg, end)
    # a small grey cloth hanging from the upper shelf, a blue one folded over the lower shelf
    wl.hanging_cloth(s, "shelf_rag", (1.45, 1.94, z1 + 0.05), (1.75, 1.94, z1 + 0.05), 0.38, "rag_grey", sway=0.02, nx=2, ny=2)
    # thread spools and folded cloth on the lowest shelf
    cols = ["spools"] * 6
    for k in range(6):
        x = 0.95 + 0.2 * k
        wl.octo(detail, "spool_%d" % k, (x, 0.72, zc + 0.08), (x, 0.84, zc + 0.08), 0.055, cols[k])
        wl.box(detail, "spool_rim_%d" % k, (x - 0.065, 0.84, zc + 0.015), (x + 0.065, 0.86, zc + 0.145), "wood")
    for k, (reg, y) in enumerate((("cloth_white", 0.72), ("cloth_blue", 0.78), ("linen", 0.84))):
        wl.rbox(detail, "fold_%d" % k, (1.9, y, zc - 0.05), (0.4, 0.06, 0.36), 0.04 * k, reg, stretch=True)
    # a roll leaning against the top of the rack
    wl.cloth_roll(s, "roll_top", (0.95, 2.55 + 0.12, zc), (1.6, 2.55 + 0.12, zc), 0.12, "cloth_red", "roll_red")
    return s


def table(root, detail):
    t = wl.Bone("table", parent=root)
    x0, x1, z0, z1 = 0.92, 2.22, -0.55, 0.42
    wl.table(t, "sew", x0, x1, z0, z1, 0.95, top="plank", leg="wood", top_th=0.1, leg_d=0.16)
    wl.draped(t, "runner", 1.3, 1.9, -0.5, z1, 0.95, 0.55, "runner", out_dir=1, nx=2)
    wl.standing_lantern(t, "lantern", (2.0, 0.95, -0.3), size=0.3)
    # folded cloth, a book, scissors, spools
    wl.rbox(t, "table_fold_0", (1.12, 0.95, -0.25), (0.34, 0.06, 0.3), 0.1, "cloth_white", stretch=True)
    wl.rbox(t, "table_fold_1", (1.12, 1.01, -0.25), (0.3, 0.05, 0.26), 0.25, "cloth_blue", stretch=True)
    wl.rbox(detail, "book", (1.62, 0.98, 0.0), (0.3, 0.05, 0.22), -0.2, {"all": "parchment", "-2": "leather"}, stretch=True)
    for k, d in enumerate((v3(1, 0, 0.6), v3(1, 0, -0.6))):
        wl.beam(detail, "scissor_%d" % k, v3(1.05, 0.965, 0.18), v3(1.05, 0.965, 0.18) + d * 0.16, 0.01, "steel", width=0.025, up=UP)
    for k, (x, z) in enumerate(((1.95, 0.15), (2.08, 0.02))):
        wl.octo(detail, "tspool_%d" % k, (x, 0.95, z), (x, 1.06, z), 0.045, "spools")
    wl.rbox(detail, "pincushion", (1.45, 0.95, -0.35), (0.12, 0.06, 0.12), 0.3, "cloth_red", stretch=True)
    # the sack by the table
    wl.sack(t, "sack", (2.62, 0.0, -0.15), size=(0.55, 0.7, 0.5), yaw=0.3, region="leather_tan", solid=True)
    return t


def mannequin(root, detail):
    m = wl.Bone("mannequin", parent=root)
    c = v3(-1.85, 0.0, 0.62)
    wl.rbox(m, "mq_base", c, (0.6, 0.1, 0.6), 0.0, {"all": "wood_dark", "+2": "plank"})
    for k, a in enumerate((0.0, math.pi / 2)):
        wl.rbox(m, "mq_foot_%d" % k, c + UP * 0.1, (0.7, 0.07, 0.12), a, "wood")
    wl.beam(m, "mq_pole", c + UP * 0.1, c + UP * 1.05, 0.08, "wood")
    tc = c + UP * 1.42
    wl.add_cube(m, "mq_torso", tc, wl.EYE, (0.56, 0.78, 0.3), {"all": "tunic"}, stretch=True)
    wl.add_cube(m, "mq_hem", tc - UP * 0.44, wl.EYE, (0.62, 0.12, 0.34), "cloth_white", stretch=True)
    wl.add_cube(m, "mq_shoulders", tc + UP * 0.34, wl.EYE, (0.68, 0.14, 0.32), "cloth_white", stretch=True)
    for s in (1, -1):
        wl.beam(m, "mq_sleeve_%d" % s, tc + v3(s * 0.33, 0.3, 0), tc + v3(s * 0.43, -0.05, 0.02), 0.17, "cloth_white", width=0.2)
        wl.beam(detail, "mq_cuff_%d" % s, tc + v3(s * 0.42, -0.02, 0.02), tc + v3(s * 0.435, -0.08, 0.02), 0.18, "linen", width=0.21)
    wl.add_cube(m, "mq_neck", tc + UP * 0.47, wl.EYE, (0.12, 0.12, 0.12), "wood")
    wl.add_cube(m, "mq_head", tc + UP * 0.58, wl.EYE, (0.16, 0.1, 0.16), "wood_dark")
    wl.collide((c[0] - 0.35, 0.0, c[2] - 0.35, c[0] + 0.35, 1.9, c[2] + 0.35))
    return m


def hanging(root, detail):
    h = wl.Bone("hanging", parent=root)
    wl.hanging_cloth(h, "cloth_white", (-1.6, TOP - 0.1, ZF + 0.16), (-0.95, TOP - 0.1, ZF + 0.16), 1.0, "rag_white", sway=0.04)
    wl.hanging_cloth(h, "cloth_blue", (-0.55, TOP - 0.1, ZF + 0.16), (0.05, TOP - 0.1, ZF + 0.16), 0.95, "rag_blue", sway=0.04)
    wl.beam(detail, "cloth_bar", (-1.7, TOP - 0.08, ZF + 0.16), (0.15, TOP - 0.08, ZF + 0.16), 0.05, "wood_dark")
    # the lantern on an arm out of the top left post
    wl.hanging_lantern(h, "lantern_l", (-XP - 0.38, 2.45, ZF + 0.1), drop=0.08, size=0.3, arm=(-XP - 0.13, 2.45, ZF))
    # a measuring stick leaning on the back rail, a basket of yarn balls by the loom
    wl.beam(detail, "yardstick", (-1.95, 0.0, ZB + 0.1), (-1.85, 1.85, ZB + 0.02), 0.04, "wood", width=0.08, up=v3(0, 0, 1))
    wl.octo(h, "basket", (-1.75, 0.0, -0.5), (-1.75, 0.32, -0.5), 0.26, "straw", end="straw")
    for k, (dx, dz, reg) in enumerate(((-0.08, -0.06, "cloth_blue"), (0.1, 0.0, "cloth_white"), (-0.02, 0.12, "cloth_red"), (0.05, -0.14, "linen"))):
        wl.rbox(detail, "yarn_%d" % k, (-1.75 + dx, 0.3, -0.5 + dz), (0.15, 0.13, 0.15), 0.6 * k, reg, stretch=True)
    wl.collide((-2.02, 0.0, -0.77, -1.48, 0.35, -0.23))
    return h


def extras(root, detail):
    """Ribbons hanging from the shelf, shears on the post, folded cloth under the table, a measuring tape."""
    e = wl.Bone("extras", parent=root)
    for k, (x, reg, L) in enumerate(((0.95, "cloth_red", 0.5), (1.03, "cloth_blue", 0.62), (1.11, "gold", 0.44))):
        wl.beam(detail, "ribbon_%d" % k, (x, 1.32, -0.68), (x + 0.02, 1.32 - L, -0.66), 0.01, reg, width=0.05, up=wl.v3(0, 0, 1))
    for k, d in enumerate((v3(0.25, -1, 0.0), v3(-0.25, -1, 0.0))):
        wl.beam(detail, "post_shears_%d" % k, v3(-XP + 0.16, 1.7, ZF + 0.02), v3(-XP + 0.16, 1.7, ZF + 0.02) + wl.norm(d) * 0.26, 0.015, "steel",
                width=0.035, up=v3(1, 0, 0))
    wl.box(detail, "post_hook", (-XP + 0.13, 1.68, ZF - 0.01), (-XP + 0.2, 1.74, ZF + 0.05), "iron")
    for k, (reg, h) in enumerate((("linen", 0.1), ("cloth_red", 0.08), ("cloth_white", 0.1), ("cloth_blue", 0.08))):
        y0 = sum(hh for _, hh in (("linen", 0.1), ("cloth_red", 0.08), ("cloth_white", 0.1), ("cloth_blue", 0.08))[:k])
        wl.rbox(e, "under_fold_%d" % k, (1.55 + 0.02 * k, 0.24 + y0, -0.1), (0.62, h, 0.48), 0.05 * (k % 2), reg, stretch=True)
    wl.box(e, "under_shelf", (1.12, 0.2, -0.38), (2.02, 0.24, 0.25), "plank", u_dir=v3(1, 0, 0))
    def T(s, t):
        return v3(1.25 + 0.5 * s, 0.962 + 0.0 * t, 0.2 - 0.06 * math.sin(s * 3) + 0.03 * t)
    wl.loft(detail, "tape", T, 2, 1, "parchment", th=0.006)
    for k, (x, z) in enumerate(((1.75, 0.3), (1.85, 0.3), (1.8, 0.2))):
        wl.octo(detail, "tspool_b_%d" % k, (x, 0.95, z), (x, 1.04, z), 0.035, "spools")
    wl.rbox(detail, "button_box", (2.05, 0.95, 0.28), (0.18, 0.06, 0.14), 0.2, {"all": "wood_dark", "+2": "brass"}, stretch=True)
    # a bolt of cloth leaning against the loom's left frame
    wl.cloth_roll(e, "bolt_lean", (-1.5, 0.05, 0.2), (-1.42, 1.0, 0.05), 0.11, "cloth_blue", "roll_blue")
    return e


def build():
    root = wl.Bone(NAME)
    detail = wl.Bone("detail", parent=root)
    frame(root, detail)
    loom(root, detail)
    shelves(root, detail)
    table(root, detail)
    mannequin(root, detail)
    hanging(root, detail)
    extras(root, detail)
    return root


def icon(path):
    """Three rolls of cloth (the reference sheet's pictogram)."""
    im = wl.icon_canvas()
    rows = [
        "................",
        "................",
        "...WWWWWWWWWw...",
        "..WwwwwwwwwwWw..",
        "..WWWWWWWWWWwW..",
        "................",
        ".BBBBBBBBBBb....",
        "BbbbbbbbbbbBb...",
        "BBBBBBBBBBBbB...",
        "................",
        "....RRRRRRRRRr..",
        "...RrrrrrrrrrRr.",
        "...RRRRRRRRRRrR.",
        "................",
        "................",
        "................",
    ]
    wl.icon_draw(im, rows, {"W": (230, 224, 210), "w": (170, 164, 150), "B": (52, 86, 146), "b": (32, 56, 100),
                            "R": (170, 44, 34), "r": (110, 26, 20)})
    im.save(path)


def main():
    wl.setup(NAME)
    root = build()
    wl.export(root, NAME, None, icon=icon, particles=[], visible_box=(8, 5, 0))


if __name__ == "__main__":
    main()
