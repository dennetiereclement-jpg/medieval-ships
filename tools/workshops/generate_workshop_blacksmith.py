#!/usr/bin/env python3
"""workshop_blacksmith — Atelier du forgeron / Blacksmith's Workshop (reference: scratchpad/ref/workshop_blacksmith_ref.png).

A stone forge in the middle (lit hearth under a stepped stone hood, the chimney rising through the roof), a black
anvil on a stone block at the front right, a wooden water tub at the front left, stone plinths carrying four thick
posts and a plank roof, chains and a lantern hanging from the beams, tools on the stone bench and on the plank wall.

Usage:  python3 tools/workshops/generate_workshop_blacksmith.py    (WS_OUT=<file>: only the model, for previews)
Workshop-local coordinates: y up, +z = front (the player works at the forge ledge), the anchor block (0, 0, 0) is
inside the forge's base.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wslib_a as wl  # noqa: E402

NAME = "workshop_blacksmith"
UP, v3 = wl.UP, wl.v3
XP = 2.1                  # posts at x = +-XP
ZF, ZB = 0.2, -1.45       # front and back post rows
BEAM_Y = 2.82             # top of the beams
ROOF_B, ROOF_F = 3.28, 3.06


def frame(root, detail):
    b = wl.Bone("frame", parent=root)
    # stone plinths under the posts: the left one is the smith's bench, the right one carries a step
    wl.stone_box(b, "plinth_l", (-2.6, 0, -1.8), (-1.62, 0.86, 0.52))
    wl.stone_box(b, "plinth_l_foot", (-2.66, 0, -1.86), (-1.56, 0.14, 0.58), region="slate", top="slate")
    wl.stone_box(b, "plinth_r", (1.62, 0, -1.8), (2.6, 0.78, 0.28))
    wl.stone_box(b, "plinth_r_step", (1.72, 0, 0.28), (2.6, 0.42, 0.78))
    wl.stone_box(b, "plinth_r_foot", (1.56, 0, -1.86), (2.66, 0.14, 0.34), region="slate", top="slate")
    for s in (1, -1):
        y0 = 0.86 if s < 0 else 0.78
        for k, z in enumerate((ZF, ZB)):
            wl.post(b, "post_%d_%d" % (s, k), (s * XP, y0, z), (s * XP, BEAM_Y, z), d=0.28, region="wood_dark")
            # an iron strap round the post foot
            wl.box(detail, "post_strap_%d_%d" % (s, k), (s * XP - 0.155, y0 + 0.08, z - 0.155), (s * XP + 0.155, y0 + 0.14, z + 0.155), "iron")
        # side beam along z on the posts
        wl.beam(b, "side_beam_%d" % s, (s * XP, BEAM_Y - 0.12, ZB - 0.45), (s * XP, BEAM_Y - 0.12, ZF + 0.5), 0.24,
                {"all": "wood", "+1": "end_grain", "-1": "end_grain"}, width=0.26)
        # knee braces
        wl.bracket(detail, "brace_f_%d" % s, (s * XP, BEAM_Y - 0.75, ZF), (s * (XP - 0.6), BEAM_Y - 0.3, ZF), d=0.12)
        wl.bracket(detail, "brace_b_%d" % s, (s * XP, BEAM_Y - 0.75, ZB), (s * (XP - 0.6), BEAM_Y - 0.3, ZB), d=0.12)
        wl.bracket(detail, "brace_s_%d" % s, (s * XP, BEAM_Y - 0.7, ZF), (s * XP, BEAM_Y - 0.24, ZF - 0.5), d=0.12)
    # cross beams along x (front and back), through the posts
    for e, z in (("f", ZF), ("b", ZB)):
        wl.beam(b, "beam_" + e, (-3.0, BEAM_Y + 0.02, z), (3.0, BEAM_Y + 0.02, z), 0.24, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"},
                width=0.24)
    # rafters under the planks
    for k, x in enumerate((-2.55, -1.75, -0.95, 0.95, 1.75, 2.55)):
        zb, zf = ZB - 0.85, ZF + 1.05
        yb, yf = ROOF_B - 0.14, ROOF_F - 0.14
        wl.beam(b, "rafter_%d" % k, (x, yb - 0.1, zb), (x, yf - 0.1, zf), 0.2, {"all": "wood", "+1": "end_grain", "-1": "end_grain"}, width=0.2)
    # the plank roof in four parts round the chimney (x -0.55..0.55, z -1.2..-0.1)
    zb, zf = ZB - 0.6, ZF + 0.8

    def y_at(z):
        return ROOF_B + (ROOF_F - ROOF_B) * (z - zb) / (zf - zb)
    wl.plank_roof(b, "roof_l", -2.85, -0.44, zb, zf, ROOF_B, ROOF_F, th=0.22, plank_w=0.33, fascia="wood_dark")
    wl.plank_roof(b, "roof_r", 0.44, 2.85, zb, zf, ROOF_B, ROOF_F, th=0.22, plank_w=0.33, fascia="wood_dark")
    wl.plank_roof(b, "roof_mf", -0.44, 0.44, -0.21, zf, y_at(-0.21), ROOF_F, th=0.22, plank_w=0.3, layer2=False, fascia=None)
    wl.plank_roof(b, "roof_mb", -0.44, 0.44, zb, -1.09, ROOF_B, y_at(-1.09), th=0.22, plank_w=0.3, layer2=False, fascia=None)
    # a plank wall at the back right, where the tools hang
    for k in range(6):
        z = ZB + 0.15 + k * 0.27
        wl.beam(b, "wall_r_%d" % k, (XP + 0.02, 0.8, z), (XP + 0.02, BEAM_Y - 0.25, z), 0.07, "plank_dark", width=0.27, up=v3(0, 0, 1))
    wl.beam(b, "wall_r_rail", (XP - 0.06, 1.9, ZB), (XP - 0.06, 1.9, ZF), 0.08, "wood_dark", up=UP)
    return b


def forge(root, detail):
    f = wl.Bone("forge", parent=root)
    # base (the anchor block is inside it) and the work ledge in front of the hearth
    wl.stone_box(f, "base", (-1.15, 0, -1.65), (1.15, 0.97, 0.5))
    wl.stone_box(f, "plinth", (-1.22, 0, -1.72), (1.22, 0.12, 0.57), region="slate", top="slate", solid=False)
    wl.stone_box(f, "ledge", (-1.28, 0.86, 0.3), (1.28, 1.02, 0.74), region="stone_top", top="stone_top")
    # the hearth: two pillars, a back wall, coals and fire
    wl.box(f, "pillar_l", (-1.15, 0.97, -1.65), (-0.62, 1.62, 0.5), {"all": "stone", "+1": "fire_back"}, solid=True)
    wl.box(f, "pillar_r", (0.62, 0.97, -1.65), (1.15, 1.62, 0.5), {"all": "stone", "-1": "fire_back"}, solid=True)
    wl.box(f, "hearth_back", (-0.62, 0.97, -1.65), (0.62, 1.62, -0.85), {"all": "stone", "+3": "fire_back"}, solid=True)
    wl.box(f, "hearth_floor", (-0.62, 0.97, -0.85), (0.62, 1.04, 0.5), {"all": "stone", "+2": "coal"}, solid=True)
    wl.box(f, "glow_embers", (-0.56, 1.04, -0.82), (0.56, 1.1, 0.3), "embers")
    wl.box(f, "glow_embers_heap", (-0.34, 1.09, -0.6), (0.3, 1.16, 0.05), "embers")
    for k, (x, z) in enumerate(((-0.42, 0.2), (0.38, 0.25), (0.05, 0.32), (-0.2, -0.1))):
        wl.rbox(detail, "coal_lump_%d" % k, (x, 1.08, z), (0.12, 0.07, 0.1), 0.4 * k, "coal")
    # fire: crossed planes of flame tongues, drawn full bright
    for k, (x0, x1, z) in enumerate(((-0.5, 0.5, -0.5), (-0.4, 0.45, -0.2), (-0.45, 0.3, 0.05))):
        wl.plate(f, "glow_fire_x_%d" % k, ((x0 + x1) / 2, 1.1 + 0.2, z), (0, 0, 1), UP, x1 - x0, 0.42 - 0.06 * k, "fire", th=0.01)
    for k, x in enumerate((-0.25, 0.2)):
        wl.plate(f, "glow_fire_z_%d" % k, (x, 1.1 + 0.18, -0.3), (1, 0, 0), UP, 0.7, 0.36, "fire", th=0.01)
    # the stepped arch over the opening, the lintel and the cornice
    for s in (1, -1):
        wl.box(f, "arch_%d" % s, (s * 0.62 - (0.2 if s > 0 else 0), 1.44, -0.85), (s * 0.62 + (0.2 if s < 0 else 0), 1.62, 0.5), "stone")
        wl.box(f, "arch2_%d" % s, (s * 0.42 - (0.12 if s > 0 else 0), 1.54, -0.85), (s * 0.42 + (0.12 if s < 0 else 0), 1.62, 0.5), "stone")
    wl.stone_box(f, "lintel", (-1.15, 1.62, -1.65), (1.15, 1.98, 0.5))
    wl.stone_box(f, "cornice", (-1.26, 1.98, -1.76), (1.26, 2.1, 0.61), region="stone_top", top="stone_top")
    # the hood: stepped like stone stairs, narrowing to the chimney
    steps = 6
    for k in range(steps):
        t = (k + 1) / steps
        hx = 1.16 - 0.62 * t
        z0, z1 = -1.66 + 0.48 * t, 0.52 - 0.64 * t
        y0 = 2.1 + 0.15 * k
        wl.box(f, "hood_%d" % k, (-hx, y0, z0), (hx, y0 + 0.16, z1), {"all": "stone_dark", "+2": "stone_dark"}, solid=True)
    # the chimney through the roof, a cap with a dark mouth
    wl.box(f, "chimney", (-0.42, 2.95, -1.07), (0.42, 4.45, -0.23), "stone_dark", solid=True)
    for s in (1, -1):
        wl.box(f, "chimney_cap_x_%d" % s, (s * 0.5 - (0.16 if s > 0 else 0), 4.4, -1.15), (s * 0.5 + (0.16 if s < 0 else 0), 4.56, -0.15), "stone_top")
        wl.box(f, "chimney_cap_z_%d" % s, (-0.34, 4.4, (-0.65 + s * 0.5) - (0.16 if s > 0 else 0)), (0.34, 4.56, (-0.65 + s * 0.5) + (0.16 if s < 0 else 0)),
               "stone_top")
    wl.box(f, "chimney_mouth", (-0.34, 4.44, -0.99), (0.34, 4.47, -0.31), "coal")
    # protruding corner stones (quoins) up the two front corners and the chimney
    for s in (1, -1):
        for k in range(6):
            y0 = 0.12 + 0.31 * k
            big = k % 2 == 0
            x_out = s * (1.15 + 0.03)
            x_in = s * (1.15 - (0.34 if big else 0.22))
            z_in = 0.5 - (0.22 if big else 0.34)
            wl.box(detail, "quoin_%d_%d" % (s, k), (min(x_in, x_out), y0, z_in), (max(x_in, x_out), y0 + 0.28, 0.53), "stone")
        for k in range(4):
            y0 = 3.0 + 0.36 * k
            big = k % 2 == 0
            wl.box(detail, "cquoin_%d_%d" % (s, k), (min(s * 0.45, s * (0.42 - (0.26 if big else 0.18))), y0, -0.23 - (0.18 if big else 0.26)),
                   (max(s * 0.45, s * (0.42 - (0.26 if big else 0.18))), y0 + 0.32, -0.2), "stone_dark")
    # a bellows on the left of the forge (leather between two boards), its nozzle into the hearth side
    bel = (-1.4, 1.02, -0.9)
    wl.rbox(detail, "bellows_board_a", bel, (0.42, 0.04, 0.62), 0.0, "wood_dark")
    wl.rbox(detail, "bellows_leather", (bel[0], bel[1] + 0.04, bel[2]), (0.38, 0.14, 0.56), 0.0, "leather_dark")
    wl.rbox(detail, "bellows_board_b", (bel[0], bel[1] + 0.18, bel[2] + 0.02), (0.42, 0.04, 0.62), 0.0, "wood_dark")
    wl.beam(detail, "bellows_handle", (bel[0], bel[1] + 0.22, bel[2] + 0.3), (bel[0], bel[1] + 0.22, bel[2] + 0.55), 0.05, "wood")
    wl.beam(detail, "bellows_nozzle", (bel[0] + 0.2, bel[1] + 0.1, bel[2] - 0.25), (-1.12, bel[1] + 0.1, bel[2] - 0.25), 0.07, "iron")
    # tools on the ledge: tongs holding a red-hot bar, a poker
    wl.tongs(detail, "ledge_tongs", (0.95, 1.035, 0.62), (-1, 0, -0.35), length=0.5)
    wl.box(f, "glow_hot_bar", (0.36, 1.03, 0.4), (0.56, 1.06, 0.46), "red_hot")
    wl.beam(detail, "poker", (-1.0, 1.04, 0.66), (-0.4, 1.06, 0.2), 0.03, "iron")
    return f


def anvil_corner(root, detail):
    a = wl.Bone("anvil", parent=root)
    wl.stone_box(a, "anvil_slab", (0.62, 0, 0.62), (1.86, 0.18, 1.56), region="slate", top="slate")
    wl.stone_box(a, "anvil_block", (0.86, 0.18, 0.78), (1.62, 0.36, 1.4), region="slate", top="slate")
    wl.anvil(a, "anvil", (1.24, 0.36, 1.09), yaw=math.pi, s=1.3, detail=detail)
    wl.hammer(detail, "anvil_hammer", (1.6, 1.13, 1.32), (-0.6, 0, -0.5), length=0.36)
    wl.box(a, "glow_anvil_bar", (0.95, 1.12, 1.03), (1.35, 1.15, 1.1), "red_hot")
    # swords leaning on the right plinth step
    for k, x in enumerate((2.02, 2.25)):
        p0 = v3(x, 0.02, 0.9)
        p1 = v3(x - 0.05, 0.98, 0.84)
        wl.beam(detail, "sword_blade_%d" % k, p0, p0 + (p1 - p0) * 0.7, 0.012, "steel", width=0.06, up=v3(0, 0, 1))
        wl.beam(detail, "sword_guard_%d" % k, p0 + (p1 - p0) * 0.7 - v3(0.1, 0, 0), p0 + (p1 - p0) * 0.7 + v3(0.1, 0, 0), 0.03, "iron")
        wl.beam(detail, "sword_grip_%d" % k, p0 + (p1 - p0) * 0.7, p1, 0.035, "leather_dark")
    return a


def tub_corner(root, detail):
    t = wl.Bone("tub", parent=root)
    wl.tub(t, "tub", (-1.5, 0, 1.12), r=0.5, h=0.74, staves=12)
    wl.beam(detail, "tub_ladle", (-1.7, 0.66, 1.0), (-1.25, 0.98, 1.35), 0.035, "wood")
    return t


def hanging(root, detail):
    h = wl.Bone("hanging", parent=root)
    # the lantern on an iron arm from the front left post
    wl.hanging_lantern(h, "lantern_l", (-1.72, 2.42, ZF + 0.08), drop=0.08, size=0.34, arm=(-XP + 0.14, 2.42, ZF))
    # chains from the front beam on the left, from the right side beam
    for k, (x, L) in enumerate(((-1.38, 1.05), (-1.05, 0.8))):
        wl.chain(detail, "chain_l_%d" % k, (x, BEAM_Y - 0.09, ZF), L)
    for k, (z, L) in enumerate(((-0.35, 1.15), (-0.8, 0.85))):
        wl.chain(detail, "chain_r_%d" % k, (XP - 0.08, BEAM_Y - 0.24, z), L)
    # tools on the plank wall (right): hammers and tongs
    wl.hammer(detail, "wall_hammer_0", (XP - 0.06, 1.55, -1.05), (0, 1, 0), length=0.4, lying=False)
    wl.hammer(detail, "wall_hammer_1", (XP - 0.06, 1.6, -0.7), (0, 1, 0), length=0.34, lying=False)
    wl.tongs(detail, "wall_tongs", (XP - 0.06, 1.25, -0.35), (0, 1, 0), length=0.6)
    for k, z in enumerate((-1.05, -0.7, -0.35)):
        wl.box(detail, "wall_peg_%d" % k, (XP - 0.14, 1.88, z - 0.02), (XP - 0.04, 1.92, z + 0.02), "wood_dark")
    # horseshoes on the wall
    for k, z in enumerate((-1.15, -0.85, -0.55, -0.25)):
        c = v3(XP - 0.05, 2.3, z)
        wl.beam(detail, "shoe_%d_l" % k, c + v3(0, -0.1, -0.07), c + v3(0, 0.06, -0.07), 0.025, "iron", width=0.03)
        wl.beam(detail, "shoe_%d_r" % k, c + v3(0, -0.1, 0.07), c + v3(0, 0.06, 0.07), 0.025, "iron", width=0.03)
        wl.beam(detail, "shoe_%d_t" % k, c + v3(0, 0.08, -0.08), c + v3(0, 0.08, 0.08), 0.025, "iron", width=0.03)
    # a rack of finished blades on the left back post
    for k in range(3):
        x = -XP + 0.25 + 0.14 * k
        wl.beam(detail, "rack_blade_%d" % k, (x, 0.95, ZB + 0.18), (x, 1.75, ZB + 0.18), 0.012, "steel", width=0.06, up=v3(0, 0, 1))
        wl.beam(detail, "rack_grip_%d" % k, (x, 1.75, ZB + 0.18), (x, 1.95, ZB + 0.18), 0.04, "leather_dark")
        wl.beam(detail, "rack_guard_%d" % k, (x - 0.07, 1.75, ZB + 0.18), (x + 0.07, 1.75, ZB + 0.18), 0.03, "iron")
    wl.beam(detail, "rack_bar", (-XP + 0.1, 1.72, ZB + 0.24), (-XP + 0.65, 1.72, ZB + 0.24), 0.05, "wood_dark")
    return h


def bench_top(root, detail):
    """The left plinth as the smith's bench: a wooden top, tools, ingots, a coal box; a coal crate on the right."""
    b = wl.Bone("bench", parent=root)
    wl.box(b, "bench_board", (-2.55, 0.86, -1.1), (-1.66, 0.92, 0.47), {"all": "plank_dark", "+1": "end_grain"}, u_dir=v3(0, 0, 1))
    for k in range(3):
        wl.ingot(detail, "ingot_%d" % k, (-2.0 + 0.04 * k, 0.92, -0.75 + 0.1 * k), yaw=0.1 * k)
    for k in range(2):
        wl.ingot(detail, "ingot_top_%d" % k, (-1.98 + 0.05 * k, 0.97, -0.7 + 0.1 * k), yaw=1.57 + 0.1 * k)
    wl.hammer(detail, "bench_hammer", (-2.35, 0.95, 0.35), (1, 0, -0.4), length=0.34)
    wl.tongs(detail, "bench_tongs", (-2.4, 0.935, -0.3), (1, 0, 0.3), length=0.45)
    wl.rbox(detail, "whetstone", (-1.85, 0.92, 0.0), (0.22, 0.07, 0.09), 0.3, "slate")
    # a coal crate on the right plinth, behind the step
    wl.crate(b, "coal_crate", (2.12, 0.78, -1.05), size=(0.55, 0.36, 0.55), solid=True)
    wl.box(b, "coal_heap", (1.9, 1.1, -1.28), (2.34, 1.18, -0.82), "coal")
    wl.rbox(detail, "coal_heap_top", (2.1, 1.16, -1.06), (0.28, 0.06, 0.26), 0.4, "coal")
    return b


def back_yard(root, detail):
    """Behind the forge: a pile of firewood, a grindstone; a bundle of iron bars, a bucket at the front left."""
    y = wl.Bone("yard", parent=root)
    for k, (x, yy, z) in enumerate(((-0.9, 0.13, -2.0), (-0.62, 0.13, -2.0), (-0.34, 0.13, -2.0), (-0.06, 0.13, -2.0),
                                    (-0.76, 0.38, -2.0), (-0.48, 0.38, -2.0), (-0.2, 0.38, -2.0), (-0.62, 0.62, -2.0))):
        wl.octo(y, "log_%d" % k, (x, yy, z - 0.32), (x, yy, z + 0.3 - 0.04 * (k % 3)), 0.13, "wood_dark", end="end_grain")
    wl.collide((-1.05, 0.0, -2.35, 0.1, 0.75, -1.7))
    gx, gz = 1.0, -2.1
    for s in (1, -1):
        wl.beam(y, "grind_leg_%d" % s, (gx + s * 0.22, 0.0, gz - 0.2), (gx + s * 0.22, 0.62, gz), 0.08, "wood")
        wl.beam(y, "grind_leg_b%d" % s, (gx + s * 0.22, 0.0, gz + 0.2), (gx + s * 0.22, 0.62, gz), 0.08, "wood")
    wl.octo(y, "grind_stone", (gx - 0.07, 0.62, gz), (gx + 0.07, 0.62, gz), 0.34, "stone_top", end="stone_top")
    wl.octo(detail, "grind_axle", (gx - 0.3, 0.62, gz), (gx + 0.3, 0.62, gz), 0.03, "iron")
    wl.beam(detail, "grind_crank", (gx + 0.3, 0.62, gz), (gx + 0.3, 0.45, gz + 0.12), 0.03, "iron")
    wl.beam(detail, "grind_trough", (gx - 0.25, 0.22, gz), (gx + 0.25, 0.22, gz), 0.12, "wood_dark", width=0.3)
    wl.collide((gx - 0.3, 0.0, gz - 0.35, gx + 0.3, 0.96, gz + 0.35))
    for k in range(4):
        x = 2.5 + 0.04 * k
        wl.beam(detail, "bar_%d" % k, (x, 0.0, 0.62 - 0.05 * k), (x - 0.1, 1.15, 0.36), 0.04, "black_iron")
    wl.tub(y, "bucket", (-2.32, 0.0, 0.95), r=0.18, h=0.3, staves=8, handles=False, solid=False)
    wl.beam(detail, "bucket_handle", (-2.5, 0.3, 0.95), (-2.32, 0.45, 0.95), 0.02, "iron")
    wl.beam(detail, "bucket_handle_b", (-2.32, 0.45, 0.95), (-2.14, 0.3, 0.95), 0.02, "iron")
    return y


def build():
    root = wl.Bone(NAME)
    detail = wl.Bone("detail", parent=root)
    frame(root, detail)
    forge(root, detail)
    anvil_corner(root, detail)
    tub_corner(root, detail)
    hanging(root, detail)
    bench_top(root, detail)
    back_yard(root, detail)
    return root


def icon(path):
    """An anvil (the reference sheet's pictogram), with a spark."""
    im = wl.icon_canvas()
    rows = [
        "................",
        "................",
        "................",
        "...........y....",
        "..........yYy...",
        "...........y....",
        ".KKKKKKKKKKKKK..",
        "..kKKKKKKKKKKKK.",
        "....KKKKKKKKK...",
        ".......KKKK.....",
        ".......kKKk.....",
        "......kKKKKk....",
        ".....KKKKKKKK...",
        "....kKKKKKKKKk..",
        "....kkkkkkkkkk..",
        "................",
    ]
    wl.icon_draw(im, rows, {"K": (74, 74, 80), "k": (40, 40, 44), "y": (255, 170, 60), "Y": (255, 236, 160)})
    p = im.load()
    for x in range(1, 14):
        if p[x, 6][3]:
            p[x, 6] = (128, 128, 134, 255)
    im.save(path)


def main():
    wl.setup(NAME)
    root = build()
    parts = [wl.particle("flame", (0.0, 1.18, -0.25), 0.5, 1), wl.particle("small_flame", (0.2, 1.15, 0.1), 0.35, 1),
             wl.particle("campfire_smoke", (0.0, 4.6, -0.65), 0.18, 1), wl.particle("smoke", (0.0, 1.55, 0.3), 0.25, 1)]
    wl.export(root, NAME, None, icon=icon, particles=parts, visible_box=(8, 6, 0))


if __name__ == "__main__":
    main()
