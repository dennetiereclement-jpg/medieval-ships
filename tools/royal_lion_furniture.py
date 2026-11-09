"""Furniture modelled for the Royal Lion Ship: what the decoration mods lack (or not royal enough). The mods' pieces
(beds, desk, wardrobe, bookcase, dining table, gold-trimmed chairs, crates, barrels, sacks, plates, bottles, lanterns)
are placed by tools/royal_lion_decor.py; these are drawn in the ship's model by tools/generate_royal_lion.py, in the
regions of tools/royal_lion_texture.py: the royal blue carpets with the gold lion, the gold chandeliers and
candelabra, the cushioned window seat under the stern windows, the inner faces of the arched windows, the lion
tapestries and gold-framed paintings, the open strongbox of gold coins, the globe, the purser's desk and its ledger,
the white canvas bales and the bolts of cloth of the cargo.

Every builder takes the bone, a name prefix and its placement (ship-local blocks). Element names start with "lit"
(shaded like the rooms) or "glow" (full bright: the candle flames).
"""
import math

import numpy as np

import generate_galleon as gn
import generate_galley as gg

v3, norm, add_cube, beam, Bone = gg.v3, gg.norm, gg.add_cube, gg.beam, gg.Bone
ry = gg.ry
disc, turned = gn.disc, gn.turned
EYE = np.eye(3)


def frame(normal):
    """Axes (u along the wall, up, n out of the wall into the room) of a wall-mounted piece."""
    n = norm(v3(normal[0], 0, normal[2]))
    u = np.cross(v3(0, 1, 0), n)
    return np.column_stack([u, v3(0, 1, 0), n]), u, n


def royal_rug(bone, name, p, w, l, yaw=0.0):
    """A royal blue carpet with a gold border and the gold lion in a medallion, flat on the floor (w across x, l along z
    before the yaw)."""
    p = v3(*p)
    R = ry(yaw)
    add_cube(bone, "lit_" + name, p + v3(0, 0.014, 0), R, (w, 0.02, l), {"all": None, "+2": "royal_rug"}, stretch=True,
             u_dir=R @ v3(1, 0, 0), v_dir=R @ v3(0, 0, 1))


def candle(bone, name, p, h=0.22):
    """A cream candle in a gold cup, its flame full bright."""
    p = v3(*p)
    disc(bone, "lit_%s_cup" % name, p + v3(0, 0.02, 0), (0, 1, 0), 0.05, 0.04, "gold")
    add_cube(bone, "lit_%s_wax" % name, p + v3(0, 0.04 + h / 2, 0), EYE, (0.05, h, 0.05), "candle")
    add_cube(bone, "glow_%s_flame" % name, p + v3(0, 0.08 + h, 0), EYE, (0.035, 0.08, 0.035), "glow")


def chandelier(parent, name, hook, drop=0.7, r=0.55, n=6):
    """A gold chandelier hanging on a chain from the ceiling hook: a turned gold stem, a ring of n arms bent up, a candle
    on each, a gold ball at the foot. Its own bone (named lantern_*) swings with the lanterns."""
    hook = v3(*hook)
    b = Bone("lantern_" + name, origin=tuple(hook), parent=parent)
    add_cube(b, "lit_%s_rose" % name, hook - v3(0, 0.03, 0), EYE, (0.22, 0.06, 0.22), "gold")
    for k in range(3):
        add_cube(b, "lit_%s_chain_%d" % (name, k), hook - v3(0, 0.06 + (k + 0.5) * drop / 3, 0), ry(k * math.pi / 4),
                 (0.05, drop / 3 - 0.02, 0.05), "iron")
    top = hook - v3(0, drop, 0)
    turned(b, "lit_%s_stem" % name, top, top - v3(0, 0.55, 0), [(0, 0.1), (0.25, 0.16), (0.5, 0.09), (0.75, 0.2), (1, 0.0)], "gold")
    hub = top - v3(0, 0.4, 0)
    disc(b, "lit_%s_hub" % name, hub, (0, 1, 0), 0.14, 0.08, "gold", n=3)
    disc(b, "lit_%s_drop" % name, top - v3(0, 0.6, 0), (0, 1, 0), 0.06, 0.08, "gold")
    for k in range(n):
        a = 2 * math.pi * k / n + 0.3
        d = v3(math.cos(a), 0, math.sin(a))
        mid = hub + d * (r * 0.6) - v3(0, 0.06, 0)
        tip = hub + d * r + v3(0, 0.08, 0)
        beam(b, "lit_%s_arm_%d" % (name, k), hub, mid, 0.04, "gold")
        beam(b, "lit_%s_arm_up_%d" % (name, k), mid, tip, 0.04, "gold")
        candle(b, "%s_candle_%d" % (name, k), tip, h=0.16)
    return b


def candelabra(bone, name, p, arms=2):
    """A gold candelabra on the table: a round foot, a turned stem, two arms and the middle candle."""
    p = v3(*p)
    disc(bone, "lit_%s_foot" % name, p + v3(0, 0.02, 0), (0, 1, 0), 0.11, 0.04, "gold", n=3)
    turned(bone, "lit_%s_stem" % name, p + v3(0, 0.04, 0), p + v3(0, 0.42, 0), [(0, 0.06), (0.3, 0.1), (0.6, 0.05), (1, 0.07)], "gold")
    candle(bone, name + "_c", p + v3(0, 0.42, 0), h=0.18)
    for k, s in enumerate((-1, 1)[:arms]):
        q = p + v3(s * 0.2, 0.34, 0)
        beam(bone, "lit_%s_arm_%d" % (name, k), p + v3(0, 0.3, 0), q, 0.035, "gold")
        candle(bone, "%s_c%d" % (name, k), q, h=0.15)


def window_seat(bone, name, x0, x1, z_wall, y, depth=0.62, normal=1.0):
    """The cushioned bench under the stern windows: a dark carved front with a gold rail and feet, the royal blue
    velvet cushion on top, round bolsters at the ends, back cushions against the wall."""
    zf = z_wall + normal * depth
    zc = (z_wall + zf) / 2
    xc, w = (x0 + x1) / 2, x1 - x0
    add_cube(bone, "lit_%s_body" % name, (xc, y + 0.2, zc), EYE, (w, 0.36, depth), {"all": "wood_dark", "+2": "wood_dark"})
    add_cube(bone, "lit_%s_rail" % name, (xc, y + 0.3, zf + normal * 0.01), EYE, (w + 0.02, 0.06, 0.03), "gold")
    add_cube(bone, "lit_%s_plinth" % name, (xc, y + 0.03, zf - normal * 0.02), EYE, (w + 0.04, 0.06, 0.06), "gold")
    add_cube(bone, "lit_%s_cushion" % name, (xc, y + 0.43, zc), EYE, (w - 0.06, 0.1, depth - 0.06), "velvet_blue")
    for k, s in enumerate((-1, 1)):
        disc(bone, "lit_%s_bolster_%d" % (name, k), ((x0 + 0.12) if s < 0 else (x1 - 0.12), y + 0.55, zc), (1, 0, 0), 0.1, 0.22,
             "velvet_blue", n=3)
    nb = max(1, int(round(w / 0.9)))
    for k in range(nb):
        xa = x0 + (k + 0.5) * w / nb
        add_cube(bone, "lit_%s_back_%d" % (name, k), (xa, y + 0.72, z_wall + normal * 0.09), ry(0.0) @ gg.rx(normal * -0.12),
                 (w / nb - 0.1, 0.42, 0.12), "velvet_blue")


def inner_window(bone, name, c, normal, w, h):
    """The inside of an arched window (the glass seen from the room), a gold frame round it, a gold sill."""
    R, u, n = frame(normal)
    c = v3(*c) + n * 0.012
    add_cube(bone, "lit_" + name, c, R, (w, h, 0.01), {"all": None, "+3": "arch_window_in"}, stretch=True, u_dir=u, v_dir=v3(0, -1, 0))
    fr = 0.08
    for s in (1, -1):
        add_cube(bone, "lit_%s_jamb_%d" % (name, s > 0), c + u * s * (w / 2 + fr / 2) + v3(0, -h * 0.1, 0) + n * 0.02, R,
                 (fr, h * 0.8 + fr, 0.05), "gold")
    add_cube(bone, "lit_%s_sill" % name, c - v3(0, h / 2 + fr / 2, 0) + n * 0.05, R, (w + 2.5 * fr, fr, 0.12), "gold")
    add_cube(bone, "lit_%s_key" % name, c + v3(0, h / 2 + fr * 0.3, 0) + n * 0.02, R, (0.14, 0.14, 0.05), "gold")


def tapestry(bone, name, center, normal, w, h):
    """A wall tapestry with the gold lion, hanging from a gold rod with round finials."""
    R, u, n = frame(normal)
    c = v3(*center) + n * 0.03
    add_cube(bone, "lit_" + name, c, R, (w, h, 0.02), {"all": None, "+3": "tapestry", "-3": "wood_dark"}, stretch=True, u_dir=u,
             v_dir=v3(0, -1, 0))
    top = c + v3(0, h / 2 + 0.04, 0) + n * 0.03
    gn.round_bar(bone, "lit_%s_rod" % name, top - u * (w / 2 + 0.12), top + u * (w / 2 + 0.12), 0.05, "gold")
    for s in (1, -1):
        disc(bone, "lit_%s_finial_%d" % (name, s > 0), top + u * s * (w / 2 + 0.16), u, 0.06, 0.08, "gold")
        add_cube(bone, "lit_%s_bracket_%d" % (name, s > 0), top + u * s * (w / 2 + 0.05) - n * 0.03, R, (0.04, 0.04, 0.08), "gold")


def painting_frame(bone, name, center, normal, w, h):
    """A carved gold frame round a vanilla painting (the canvas is drawn by the renderer), a dark backboard."""
    R, u, n = frame(normal)
    c = v3(*center)
    add_cube(bone, "lit_%s_back" % name, c + n * 0.01, R, (w + 0.04, h + 0.04, 0.02), "wood_dark")
    for e in (-1, 1):
        add_cube(bone, "lit_%s_v%d" % (name, e > 0), c + u * e * (w / 2 + 0.06) + n * 0.04, R, (0.12, h + 0.24, 0.06), "carving")
        add_cube(bone, "lit_%s_h%d" % (name, e > 0), c + v3(0, e * (h / 2 + 0.06), 0) + n * 0.04, R, (w + 0.24, 0.12, 0.06), "carving")


def strongbox(bone, name, p, yaw=0.0, w=0.9, d=0.55):
    """The open strongbox of the merchant prince: an iron-bound chest, its lid thrown back, heaped with gold coins, a
    few coins and a goblet spilled beside it."""
    p = v3(*p)
    R = ry(yaw)
    add_cube(bone, "lit_" + name, p + v3(0, 0.25, 0), R, (w, 0.5, d), {"all": "wood_dark", "+2": "coins"})
    add_cube(bone, "lit_%s_heap" % name, p + v3(0, 0.53, 0), R, (w - 0.14, 0.08, d - 0.14), "coins")
    add_cube(bone, "lit_%s_heap_top" % name, p + v3(0, 0.6, 0), R, (w - 0.4, 0.07, d - 0.3), "coins")
    hinge = p + R @ v3(0, 0.5, -d / 2)
    lid_c = hinge + R @ v3(0, 0.25, -0.06)
    add_cube(bone, "lit_%s_lid" % name, lid_c, R @ gg.rx(-1.75), (w + 0.04, d + 0.02, 0.1), {"all": "wood_dark", "-3": "velvet_blue"})
    for k, sx in enumerate((-0.38, 0.0, 0.38)):
        add_cube(bone, "lit_%s_band_%d" % (name, k), p + R @ v3(sx * w, 0.25, 0), R, (0.06, 0.52, d + 0.04), "iron")
    add_cube(bone, "lit_%s_lock" % name, p + R @ v3(0, 0.36, d / 2 + 0.03), R, (0.14, 0.16, 0.03), "gold")
    for k, (dx, dz) in enumerate(((w / 2 + 0.15, 0.1), (w / 2 + 0.28, -0.12), (-w / 2 - 0.18, 0.2))):
        disc(bone, "lit_%s_coin_%d" % (name, k), p + R @ v3(dx, 0.012, dz), (0, 1, 0), 0.05, 0.02, "gold")
    q = p + R @ v3(w / 2 + 0.2, 0, d / 2 + 0.05)
    turned(bone, "lit_%s_goblet" % name, q, q + v3(0, 0.22, 0), [(0, 0.1), (0.15, 0.03), (0.6, 0.04), (0.7, 0.1), (1, 0.11)], "gold")


def coin_stacks(bone, name, pts):
    """Little stacks of gold coins on the desk or the purser's table."""
    for k, q in enumerate(pts):
        q = v3(*q)
        n = 2 + k % 3
        for j in range(n):
            disc(bone, "lit_%s_%d_%d" % (name, k, j), q + v3(0.004 * (j % 2), 0.012 + 0.024 * j, 0), (0, 1, 0), 0.055, 0.022, "gold")


def globe(bone, name, p):
    """A terrestrial globe on a turned wooden stand, the gold meridian ring round it."""
    p = v3(*p)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.5
        beam(bone, "lit_%s_leg_%d" % (name, k), p + v3(math.cos(a) * 0.28, 0.0, math.sin(a) * 0.28), p + v3(0, 0.45, 0), 0.06, "wood_dark")
    turned(bone, "lit_%s_stem" % name, p + v3(0, 0.4, 0), p + v3(0, 0.7, 0), [(0, 0.1), (0.5, 0.14), (1, 0.08)], "wood_dark")
    c = p + v3(0, 1.0, 0)
    tilt = gg.rz(0.4)
    add_cube(bone, "lit_%s_ball" % name, c, tilt, (0.46, 0.46, 0.46), "globe")
    add_cube(bone, "lit_%s_ball_r" % name, c, tilt @ ry(math.pi / 4), (0.42, 0.5, 0.42), "globe")
    add_cube(bone, "lit_%s_ball_t" % name, c, tilt @ ry(math.pi / 8), (0.5, 0.36, 0.5), "globe")
    for k in range(8):
        a = math.pi * k / 7 - math.pi / 2
        q = c + tilt @ v3(0.31 * math.cos(a), 0.31 * math.sin(a), 0)
        add_cube(bone, "lit_%s_ring_%d" % (name, k), q, tilt @ gg.rz(a), (0.04, 0.14, 0.04), "gold")
    add_cube(bone, "lit_%s_cradle" % name, p + v3(0, 0.72, 0), EYE, (0.7, 0.04, 0.06), "gold")


def purser_desk(bone, name, p, yaw=0.0):
    """The purser's sloped desk in the hold: a dark cabinet, the open ledger on the slope, an inkpot and a quill, the
    brass scales, stacks of coins."""
    p = v3(*p)
    R = ry(yaw)
    add_cube(bone, "lit_%s_body" % name, p + v3(0, 0.42, 0), R, (1.1, 0.84, 0.62), {"all": "wood_dark"})
    add_cube(bone, "lit_%s_slope" % name, p + R @ v3(0, 0.95, -0.02), R @ gg.rx(0.22), (1.14, 0.06, 0.66), {"all": "wood_dark", "+2": "wood_mid"})
    add_cube(bone, "lit_%s_book" % name, p + R @ v3(-0.05, 1.0, 0.02), R @ gg.rx(0.22), (0.62, 0.02, 0.4), {"all": "red_paint", "+2": "ledger"},
             stretch=True)
    add_cube(bone, "lit_%s_gallery" % name, p + R @ v3(0, 1.08, -0.32), R, (1.14, 0.1, 0.06), "gold")
    q = p + R @ v3(0.42, 1.12, -0.22)
    disc(bone, "lit_%s_ink" % name, q, (0, 1, 0), 0.05, 0.07, "navy")
    beam(bone, "lit_%s_quill" % name, q + v3(0, 0.03, 0), q + R @ v3(-0.08, 0.28, 0.06), 0.02, "linen")
    s = p + R @ v3(-0.42, 1.13, -0.22)
    disc(bone, "lit_%s_scale_foot" % name, s, (0, 1, 0), 0.07, 0.03, "bronze")
    add_cube(bone, "lit_%s_scale_post" % name, s + v3(0, 0.16, 0), EYE, (0.03, 0.3, 0.03), "bronze")
    beam(bone, "lit_%s_scale_beam" % name, s + R @ v3(-0.16, 0.3, 0), s + R @ v3(0.16, 0.3, 0), 0.025, "bronze")
    for k, dx in enumerate((-0.15, 0.15)):
        disc(bone, "lit_%s_pan_%d" % (name, k), s + R @ v3(dx, 0.16, 0), (0, 1, 0), 0.07, 0.02, "bronze")
        beam(bone, "lit_%s_cord_%d" % (name, k), s + R @ v3(dx, 0.3, 0), s + R @ v3(dx, 0.17, 0), 0.01, "bronze")
    for k, sx in enumerate((-0.5, 0.5)):
        add_cube(bone, "lit_%s_foot_%d" % (name, k), p + R @ v3(sx, 0.03, 0), R, (0.1, 0.06, 0.66), "gold")


def bale(bone, name, p, yaw=0.0, w=1.0, h=0.8, d=0.9, ties=2):
    """A bale of cloth (the deck cargo of reference 044): white canvas over a squarish bundle, rounded at the top edge,
    lashed with ropes."""
    p = v3(*p)
    R = ry(yaw)
    add_cube(bone, "lit_" + name, p + v3(0, h / 2 - 0.04, 0), R, (w, h - 0.08, d), "bale_white")
    add_cube(bone, "lit_%s_top" % name, p + v3(0, h - 0.04, 0), R, (w - 0.08, 0.08, d - 0.08), "bale_white")
    add_cube(bone, "lit_%s_skirt" % name, p + v3(0, 0.05, 0), R, (w + 0.04, 0.1, d + 0.04), "bale_white")
    for k in range(ties):
        t = (k + 1) / (ties + 1) - 0.5
        q = p + R @ v3(t * w, 0, 0)
        add_cube(bone, "lit_%s_tie_%d" % (name, k), q + v3(0, h / 2, 0), R, (0.05, h + 0.02, d + 0.03), "rope")
        add_cube(bone, "lit_%s_tie_top_%d" % (name, k), q + v3(0, h + 0.005, 0), R, (0.05, 0.03, d - 0.02), "rope")
    add_cube(bone, "lit_%s_band" % name, p + v3(0, h * 0.55, 0), R, (w + 0.03, 0.05, d + 0.03), {"all": "rope", "+2": None, "-2": None})


def tarp_stack(bone, name, p, yaw=0.0, w=1.9, d=0.95, h=1.0):
    """White canvas thrown over a stack of crates and lashed down (044): the cover over the top and hanging half way
    down the sides, ropes across."""
    p = v3(*p)
    R = ry(yaw)
    add_cube(bone, "lit_%s_cover" % name, p + v3(0, h + 0.02, 0), R, (w + 0.06, 0.04, d + 0.06), "bale_white")
    for s in (1, -1):
        add_cube(bone, "lit_%s_side_%d" % (name, s > 0), p + R @ v3(0, h - 0.25, s * (d / 2 + 0.03)), R @ gg.rx(-s * 0.08), (w + 0.06, 0.5, 0.03),
                 "bale_white")
        add_cube(bone, "lit_%s_end_%d" % (name, s > 0), p + R @ v3(s * (w / 2 + 0.03), h - 0.2, 0), R, (0.03, 0.4, d + 0.06), "bale_white")
    for k, t in enumerate((-0.3, 0.3)):
        q = p + R @ v3(t * w, 0, 0)
        add_cube(bone, "lit_%s_rope_%d" % (name, k), q + v3(0, h + 0.05, 0), R, (0.05, 0.03, d + 0.1), "rope")
        for s in (1, -1):
            beam(bone, "lit_%s_rope_%d_%d" % (name, k, s > 0), q + R @ v3(0, h + 0.04, s * (d / 2 + 0.06)), q + R @ v3(0, 0.05, s * (d / 2 + 0.12)),
                 0.04, "rope")


def cloth_bolts(bone, name, p, yaw=0.0, rows=3, cols=3, l=1.3):
    """Bolts of cloth (royal blue, red, gold) stacked on a low rack, lying along x before the yaw: the trade goods of
    the merchant prince."""
    p = v3(*p)
    R = ry(yaw)
    regions = ("cloth_roll", "silk_red", "silk_gold", "bale_white")
    add_cube(bone, "lit_%s_rack" % name, p + v3(0, 0.06, 0), R, (l + 0.1, 0.12, cols * 0.3 + 0.1), "wood_mid")
    for j in range(rows):
        n = cols - (j % 2)
        for k in range(n):
            z = (k - (n - 1) / 2) * 0.3
            c = p + R @ v3(0, 0.27 + j * 0.27, z)
            reg = regions[(j * 2 + k) % len(regions)]
            disc(bone, "lit_%s_%d_%d" % (name, j, k), c, R @ v3(1, 0, 0), 0.14, l, reg, n=3)


def counted_sacks(bone, name, p, yaw=0.0, n=3):
    """Spice sacks standing tied at the neck, leaning together."""
    p = v3(*p)
    R = ry(yaw)
    for k in range(n):
        q = p + R @ v3((k - (n - 1) / 2) * 0.38, 0, 0.05 * (k % 2))
        add_cube(bone, "lit_%s_%d" % (name, k), q + v3(0, 0.27, 0), R @ ry(0.2 * k), (0.36, 0.54, 0.34), "sack")
        add_cube(bone, "lit_%s_%d_top" % (name, k), q + v3(0, 0.58, 0), R @ ry(0.2 * k), (0.22, 0.1, 0.2), "sack")
        add_cube(bone, "lit_%s_%d_tie" % (name, k), q + v3(0, 0.55, 0), R @ ry(0.2 * k), (0.24, 0.04, 0.22), "rope")


def halberd_rack(bone, name, p, normal, n=4):
    """A rack of halberds of the royal guard against a wall: a dark board with two rails, the poles with their steel
    heads and gold tassels."""
    R, u, nn = frame(normal)
    p = v3(*p)
    add_cube(bone, "lit_%s_board" % name, p + v3(0, 1.0, 0) + nn * 0.03, R, (0.25 + 0.3 * n, 1.6, 0.05), "wood_dark")
    for k, y in enumerate((0.45, 1.5)):
        add_cube(bone, "lit_%s_rail_%d" % (name, k), p + v3(0, y, 0) + nn * 0.12, R, (0.3 * n + 0.2, 0.08, 0.12), "wood_mid")
    for k in range(n):
        q = p + u * ((k - (n - 1) / 2) * 0.3) + nn * 0.14
        beam(bone, "lit_%s_pole_%d" % (name, k), q + v3(0, 0.05, 0), q + v3(0, 2.1, 0), 0.05, "wood_mid")
        add_cube(bone, "lit_%s_blade_%d" % (name, k), q + v3(0, 2.05, 0) + u * 0.08, R, (0.18, 0.26, 0.02), "iron")
        add_cube(bone, "lit_%s_spike_%d" % (name, k), q + v3(0, 2.28, 0), R, (0.03, 0.22, 0.03), "iron")
        add_cube(bone, "lit_%s_tassel_%d" % (name, k), q + v3(0, 1.82, 0), R, (0.07, 0.12, 0.07), "gold")


def mess_ware(bone, name, pts):
    """Pewter plates and wooden tankards laid on the crew's table."""
    for k, q in enumerate(pts):
        q = v3(*q)
        disc(bone, "lit_%s_plate_%d" % (name, k), q + v3(0, 0.01, 0), (0, 1, 0), 0.14, 0.02, "iron")
        t = q + v3(0.2, 0, 0.12)
        disc(bone, "lit_%s_mug_%d" % (name, k), t + v3(0, 0.08, 0), (0, 1, 0), 0.06, 0.16, "wood_mid")
        disc(bone, "lit_%s_hoop_%d" % (name, k), t + v3(0, 0.12, 0), (0, 1, 0), 0.065, 0.02, "iron")


BUILDERS = {"royal_rug": royal_rug, "chandelier": chandelier, "candelabra": candelabra, "window_seat": window_seat, "inner_window": inner_window,
            "tapestry": tapestry, "painting_frame": painting_frame, "strongbox": strongbox, "coin_stacks": coin_stacks, "globe": globe,
            "purser_desk": purser_desk, "bale": bale, "tarp_stack": tarp_stack, "cloth_bolts": cloth_bolts, "counted_sacks": counted_sacks,
            "halberd_rack": halberd_rack, "mess_ware": mess_ware}
