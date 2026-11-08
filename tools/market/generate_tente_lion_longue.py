#!/usr/bin/env python3
"""tente_lion_longue — Longue tente au lion / Long Lion Tent (1.26.0, Lion Port market, group A; reference
scratchpad/ref2/tente_lion_longue_ref.png, picture 041).

A long blue and cream merchant tent, one block (TentType group "tents"), about 10.5 x 7 blocks (the two side awnings,
the guy poles and the rug included), the flag at about 8.4:

  - in the middle, two raised parts side by side: on the left a tall PAVILION PEAK (a bell-shaped hipped roof in blue /
    cream gores, twisted ropes down its front hips, a big capped block on the apex carrying the flag pole with the long
    blue LION PENNANT), on the right the GABLED HALL with the entrance (wide blue / cream stripes down its two slopes, a
    striped gable end, a gold finial on its right ridge end, ivy spilling over the roof's right end);
  - the pavilion's valance in alternating blue and cream square tabs edged in gold; the hall's front valance in cream and
    gold with dark iron crosses and round gold dags;
  - two lower cream AWNINGS on posts, sagging: on the left (gold spike finials on its posts, chains up to the pavilion's
    corner, a leaning prop pole on a stake, ivy at its end) over the potions counter, crates of gold bars and of cloth
    bundles; on the right (gold-capped posts, a prop pole) over a long counter of cloth rolls (red, blue, cream), books,
    gold coins and iron-banded chests;
  - the hall's entrance: two LION BANNERS hanging from the valance on either side, cream and blue curtains tied back, a
    big lantern on each side; inside, a writing desk with an open ledger and a scroll (the merchant's counter) and the
    back shelves of sacks, jars, pots and books;
  - the pavilion front: a dark blue curtain behind the hanging brass SCALES and a lantern, a low counter with a book;
  - the blue RUG with gold lattice running out of the entrance over a stone threshold.

The merchant's place (an EasyNPC, 1 x 1 x 2.2 free) is behind the writing desk (NPC_SPOT); players walk in by the
entrance and round the desk's right end. No trade system, nothing ticks.

Usage:  python3 tools/market/generate_tente_lion_longue.py     (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_lion_longue.json, models/entity + blockbench/tente_lion_longue.bbmodel,
textures/entity/tente_lion_longue.png, textures/item/tente_lion_longue.png, interiors/tente_lion_longue_decor.json.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import props_a as pa  # noqa: E402

ml = pa.ml
np = pa.np
v3, norm, add_cube, beam, loft, Bone = pa.v3, pa.norm, pa.add_cube, pa.beam, pa.loft, pa.Bone
EYE, UP, X, Z = pa.EYE, pa.UP, pa.X, pa.Z
ry, rx, rz = pa.ry, pa.rx, pa.rz
box, collide = pa.box, pa.collide
BLUE, CREAM, GOLD = pa.BLUE, pa.CREAM, pa.GOLD
IRON = pa._rgb("3a3a40")

NAME = "tente_lion_longue"
# ---------------------------------------------------------------- dimensions (tent-local blocks, +z = the open front)
HD = 2.0                      # half depth of the pavilion and the hall (posts at z = +-HD)
PX0, PX1 = -3.0, -0.4         # the pavilion's posts in x
PCX = (PX0 + PX1) / 2         # the pavilion's centre
P_EAVE, P_APEX = 3.5, 6.0
HX1 = 2.6                     # the hall's right posts (its left posts are the pavilion's right ones)
H_EAVE, H_RIDGE = 3.4, 5.15
LX = -5.0                     # the left awning's outer posts
RX = 4.75                     # the right awning's outer posts
AW_Y_OUT = 2.75               # the awnings' outer edge height
FLAG_TOP = 8.1
DESK = (-0.35, 1.0, 0.45, 1.05)   # the writing desk (the merchant's counter): x0, x1, z0, z1
DESK_H = 1.0
NPC_SPOT = (-0.4, -0.85)      # (x0, z0) of the free 1 x 1 x 2.2 place behind the desk (the merchant)


def cross_valance(seed):
    """The hall's front valance: a cream band between gold rules, dark iron crosses in a row, round gold dags below."""
    def p(img):
        rng = random.Random(seed)
        w, h = img.size
        pa.weave(img, CREAM, rng)
        px = img.load()
        b = int(h * 0.66)
        n = 18
        tw = w / n
        for y in range(h):
            for x in range(w):
                lx = (x % tw) / tw
                if y > b:
                    dy = (y - b) / (h - b)
                    if (lx - 0.5) ** 2 + (dy * 0.85) ** 2 > 0.25:
                        px[x, y] = pa.CLEAR
                        continue
                    edge = abs(math.hypot(lx - 0.5, dy * 0.85) - 0.5) * tw < 1.4
                    px[x, y] = pa._jitter(pa.GOLD_D if edge else GOLD, rng, 8) + (255,)
                    continue
                if y < 2 or y >= b - 1:
                    px[x, y] = pa._jitter(GOLD if y != 0 else pa.GOLD_D, rng, 8) + (255,)
                elif y == 2 or y == b - 2:
                    px[x, y] = pa._jitter(pa._scale(GOLD, 0.8), rng, 8) + (255,)
        s = int(min(w / 6 * 0.5, b - 6))
        for k in range(6):
            pa.stamp(img, (int(k * w / 6 + w / 12 - s / 2), 3 + (b - 6 - s) // 2, s, s), "cross", fill=IRON, outline=pa._rgb("1a1a1e"),
                     light=pa._rgb("6a6a72"), rng=rng)
    return p


def regions(atlas):
    pa.add_regions(atlas, "lg", [
        ("proof", 128, 96, pa.stripes([BLUE, CREAM], 4, 4101, fold=0.17)),
        ("rug", 80, 128, pa.rug(4102, scrolls="lattice")),
        ("banner", 40, 88, pa.banner(4103, emblem="lion", bottom="point")),
        ("hroof", 128, 64, pa.stripes([CREAM, BLUE], 4, 4104, fold=0.15)),
        ("flag", 112, 40, pa.lion_flag(4105)),
        ("awning", 96, 64, pa.plain(4106, pa._rgb("e6d0a4"), folds=5, depth=0.12)),
        ("wall", 128, 64, pa.plain(4107, pa.BLUE_D, folds=8, depth=0.2)),
        ("curtain_b", 48, 64, pa.plain(4108, BLUE, folds=4, depth=0.22)),
        ("curtain_d", 64, 64, pa.plain(4121, pa._scale(pa.BLUE_D, 0.8), folds=6, depth=0.25)),
        ("curtain_c", 48, 64, pa.drape(4109, motif=None)),
        ("pvalance", 192, 24, pa.dag_valance(8, 4110, cloth=BLUE, alt=CREAM, band=0.45)),
        ("hvalance", 256, 32, cross_valance(4111)),
        ("stone", 32, 32, pa.stone(4112)),
        ("chest", 32, 32, pa.chest_wood(4113, base=pa._rgb("6e4220"), trim=pa._rgb("8a8c92"))),
        ("book", 32, 24, pa.parchment(4114, kind="text")),
        ("books", 64, 16, pa.books(4115)),
        ("roll_b", 16, 16, pa.roll_end(4116, BLUE)),
        ("roll_r", 16, 16, pa.roll_end(4117, pa._rgb("a82a26"))),
        ("roll_c", 16, 16, pa.roll_end(4118, pa.CREAM_D, core=pa._rgb("8a6a40"))),
        ("post", 64, 16, pa.post_wood(4119)),
        ("striped", 32, 32, pa.stripes([pa._rgb("a82a26"), BLUE], 4, 4120, fold=0.1)),
    ])


def awning(shell, det, name, x_in, y_in, x_out, y_out, z0, z1, nx=6):
    """A cream canvas lean-to from the tent's side (x_in, y_in) out to (x_out, y_out), over z0..z1, sagging between
    its edges, soft folds across; a rolled front hem."""
    def P(s, t):
        z = z1 - (z1 - z0) * s if x_out < x_in else z0 + (z1 - z0) * s
        x = x_in + (x_out - x_in) * t
        y = y_in + (y_out - y_in) * t - 0.16 * math.sin(math.pi * t) - 0.05 * math.sin(math.pi * ((s * 5) % 1.0))
        return v3(x, y, z)
    loft(shell, name, P, nx, 3, "lg_awning", th=0.035, overlap=0.03)
    beam(det, name + "_hem", (x_out, y_out - 0.02, z0), (x_out, y_out - 0.02, z1), 0.09, "cloth_beige", extend=0.04)
    beam(det, name + "_hem_f", (x_in, y_in - 0.02, z1), (x_out, y_out - 0.02, z1), 0.07, "cloth_beige", extend=0.02)


def build(atlas, decor):
    rng = random.Random(41)
    root = Bone(NAME)
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)
    PR = dict(stone_region="lg_stone", post_region="lg_post")
    # ---- posts: the pavilion's four, the hall's right two (the pavilion's right posts are shared), awning posts
    for k, (x, z) in enumerate(((PX0, HD), (PX1, HD), (PX1, -HD), (PX0, -HD))):
        pa.post(shell, det, "ppost_%d" % k, x, z, P_EAVE + 0.3, d=0.38, stone_w=0.56, stone_h=0.35, bands=(1.2, 2.5), cap=0.5,
                collide_top=P_EAVE, **PR)
    for k, z in enumerate((HD, -HD)):
        pa.post(shell, det, "hpost_%d" % k, HX1, z, H_EAVE + 0.32, d=0.38, stone_w=0.56, stone_h=0.35, bands=(1.2, 2.45), cap=0.5,
                collide_top=H_EAVE, **PR)
    for k, z in enumerate((1.75, -1.35)):
        pa.post(shell, det, "lpost_%d" % k, LX, z, AW_Y_OUT + 0.1, d=0.3, stone_w=0.0, bands=(0.4, 1.9), cap=0.4, finial="small",
                collide_top=AW_Y_OUT, **PR)
        pa.post(shell, det, "rpost_%d" % k, RX, z, AW_Y_OUT - 0.05, d=0.3, stone_w=0.0, bands=(0.4, 1.9), cap=0.42, cap_region="gold",
                collide_top=AW_Y_OUT - 0.05, **PR)
    # eave beams of the pavilion and the hall
    pb, hb = P_EAVE - 0.15, H_EAVE - 0.15
    pc = [(PX0, HD), (PX1, HD), (PX1, -HD), (PX0, -HD)]
    for k in range(4):
        (xa, za), (xb, zb) = pc[k], pc[(k + 1) % 4]
        beam(shell, "peave_%d" % k, (xa, pb, za), (xb, pb, zb), 0.3, {"all": "beam", "+1": "end_grain", "-1": "end_grain"}, width=0.26, extend=0.12)
    for k, z in enumerate((HD, -HD)):
        beam(shell, "heave_%d" % k, (PX1, hb, z), (HX1, hb, z), 0.3, {"all": "beam", "+1": "end_grain", "-1": "end_grain"}, width=0.26, extend=0.12)
    beam(shell, "heave_r", (HX1, hb, -HD), (HX1, hb, HD), 0.3, {"all": "beam", "+1": "end_grain", "-1": "end_grain"}, width=0.26, extend=0.12)
    for k, (p, q) in enumerate((((HX1 - 0.18, H_EAVE - 1.1, HD), (HX1 - 0.85, hb - 0.1, HD)), ((PX1 + 0.18, H_EAVE - 1.1, HD), (PX1 + 0.8, hb - 0.1, HD)))):
        beam(shell, "brace_%d" % k, p, q, 0.14, "wood_dark", extend=0.05)
    # ---- the pavilion peak: bell hipped roof, gores, its valance (blue and cream tabs), the apex block and flag pole
    W0, W1, D = PX0 - 0.35, PX1 + 0.35, HD + 0.35
    ey = P_EAVE + 0.02
    pa.hip_roof(shell, "proof", (PCX, P_APEX, 0), [(W0, ey, D), (W1, ey, D), (W1, ey, -D), (W0, ey, -D)], "lg_proof", nx=4, ny=7, a=0.32,
                droop=0.1)
    for k, (c0, c1, o) in enumerate((((W0, ey, D + 0.02), (W1, ey, D + 0.02), Z), ((W1 + 0.02, ey, -D), (W1 + 0.02, ey, D), X),
                                     ((W1, ey, -D - 0.02), (W0, ey, -D - 0.02), -Z), ((W0 - 0.02, ey, -D), (W0 - 0.02, ey, D), -X))):
        if k == 1:
            continue   # the hall joins the pavilion on its right
        pa.valance(shell, "pvalance_%d" % k, c0, c1, o, h=0.58, region="lg_pvalance", segs=3, sag=0.05)
    for k, (cx, cz) in enumerate(((W0, D), (W1, D), (W1, -D), (W0, -D))):
        pts = [v3(PCX + (cx - PCX) * (i / 4), P_APEX - (P_APEX - ey) * pa.bell(i / 4, 0.32) + 0.04, cz * (i / 4)) for i in range(5)]
        for i in range(4):
            beam(det, "phip_%d_%d" % (k, i), pts[i], pts[i + 1], 0.07, "cloth_beige", width=0.11, extend=0.03)
        if k < 2:   # twisted ropes hanging in swags down the two front hips
            ml.rope(det, "hip_rope_%d" % k, pts[0] + v3(0, 0.06, 0.05), pts[4] + v3(0, 0.0, 0.08), d=0.08, sag=0.18, segs=4)
    box(shell, "apex_block", (PCX - 0.32, P_APEX - 0.08, -0.32), (PCX + 0.32, P_APEX + 0.3, 0.32), {"all": "wood", "+2": "end_grain"}, stretch=False)
    box(shell, "apex_block_top", (PCX - 0.38, P_APEX + 0.3, -0.38), (PCX + 0.38, P_APEX + 0.46, 0.38), "gold", stretch=False)
    beam(shell, "flag_pole", (PCX, P_APEX + 0.46, 0), (PCX, FLAG_TOP, 0), 0.14, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    for k, y in enumerate((FLAG_TOP - 1.25, FLAG_TOP)):
        box(det if k == 0 else shell, "flag_cap_%d" % k, (PCX - 0.13, y - 0.06, -0.13), (PCX + 0.13, y + 0.12, 0.13), "gold", stretch=False)
    add_cube(shell, "flag_tip", (PCX, FLAG_TOP + 0.24, 0), ry(math.pi / 4), (0.1, 0.22, 0.1), "gold")

    def F(s, t):
        return v3(PCX + 0.08 + 2.35 * s, FLAG_TOP - 0.1 - 1.0 * t + 0.32 * s * t + 0.06 * math.sin(s * math.pi * 2.0),
                  0.18 * math.sin(s * math.pi * 1.4) + 0.02 * t)
    loft(shell, "flag", F, 6, 1, "lg_flag", th=0.025)
    # ---- the gabled hall: ridge along x from inside the pavilion roof to the right gable end, stripes down the slopes
    HXL, HXR, HD2 = PCX + 0.3, HX1 + 0.32, HD + 0.32
    hy = H_EAVE + 0.02

    def hroof(s, t, sgn):
        x = HXL + (HXR - HXL) * s
        drop = H_RIDGE - hy
        y = H_RIDGE - drop * pa.bell(t, 0.45) - 0.07 * math.sin(math.pi * s) * math.sin(math.pi * t)
        p = v3(x, y, HD2 * t)
        return v3(p[0], p[1], sgn * p[2])
    loft(shell, "hroof_f", lambda s, t: hroof(s, t, 1), 8, 4, "lg_hroof", th=0.04, overlap=0.03)
    loft(shell, "hroof_b", lambda s, t: hroof(1 - s, t, -1), 8, 4, "lg_hroof", th=0.04, overlap=0.03)
    box(shell, "hridge", (HXL, H_RIDGE - 0.02, -0.12), (HXR, H_RIDGE + 0.06, 0.12), {"all": "cloth_beige"}, u_dir=X)
    pa.tri_plate(shell, atlas, "hgable", (HXR - 0.02, H_RIDGE, 0), (HXR - 0.02, hy, HD2), (HXR - 0.02, hy, -HD2), n=4, size=64, seed=4130,
                 colours=(BLUE, CREAM))
    # the gold finial on its stepped base at the right ridge end
    box(shell, "hfinial_base", (HXR - 0.24, H_RIDGE - 0.1, -0.24), (HXR + 0.24, H_RIDGE + 0.2, 0.24), {"all": "wood", "+2": "end_grain"}, stretch=False)
    box(shell, "hfinial_base2", (HXR - 0.17, H_RIDGE + 0.2, -0.17), (HXR + 0.17, H_RIDGE + 0.34, 0.17), "gold", stretch=False)
    pa.finial_spike(shell, "hfinial", (HXR, H_RIDGE + 0.34, 0), h=0.62, w=0.22)
    # the hall's valances: the cream / gold front one with iron crosses, plain blue-tab ones at the back and the right
    pa.valance(shell, "hvalance_f", (PX1 + 0.2, hy, HD2 + 0.02), (HXR, hy, HD2 + 0.02), Z, h=0.62, region="lg_hvalance", segs=3, sag=0.04)
    pa.valance(shell, "hvalance_b", (HXR, hy, -HD2 - 0.02), (PX1 + 0.2, hy, -HD2 - 0.02), -Z, h=0.5, region="lg_pvalance", segs=2, sag=0.04)
    pa.valance(shell, "hvalance_r", (HXR + 0.02, hy, HD2), (HXR + 0.02, hy, -HD2), X, h=0.5, region="lg_pvalance", segs=3, sag=0.04)
    # ivy spilling over the roof's right end
    for k in range(4):
        ml.vine(det, "hivy_%d" % k, (HXR - 0.55 - 0.32 * k, hy + 0.2 - 0.05 * k, HD2 + 0.12), 0.75 + 0.3 * (k % 2), 0.42, normal=(0, 0, 1))
    ml.crossed(det, "hivy_top", (HXR - 0.9, hy + 0.45, HD2 - 0.1), 1.0, 0.4, "ivy")
    # ---- walls: the back of both parts, the pavilion's left side, the hall's right side, the pavilion's front curtain
    pa.wall(shell, "wall_back", (PX0, 0, -HD - 0.06), (HX1, 0, -HD - 0.06), 0.0, pb - 0.15, -Z, "lg_wall", nx=10)
    collide((PX0, 0.0, -HD - 0.12, HX1, pb - 0.15, -HD))
    pa.wall(shell, "wall_left", (PX0 - 0.06, 0, -HD), (PX0 - 0.06, 0, HD), 0.0, pb - 0.15, -X, "lg_wall", nx=6)
    collide((PX0 - 0.12, 0.0, -HD, PX0, pb - 0.15, HD))
    pa.wall(shell, "wall_right", (HX1 + 0.06, 0, HD), (HX1 + 0.06, 0, -HD), 0.0, hb - 0.15, X, "lg_wall", nx=6)
    collide((HX1, 0.0, -HD, HX1 + 0.12, hb - 0.15, HD))
    pa.wall(shell, "pcurtain", (PX0 + 0.2, 0, 1.35), (PX1 - 0.2, 0, 1.35), 0.9, pb - 0.12, Z, "lg_curtain_d", nx=6, fold=0.07)
    collide((PX0, 0.0, 1.29, PX1 - 0.2, pb - 0.12, 1.41))
    # ---- the pavilion front: the hanging scales, a lantern, the low counter with a book
    pa.scales(shell, det, "scales", (PX0 + 0.95, pb - 0.12, HD + 0.02), span=0.62, drop=0.55, pan_drop=0.32)
    ml.lantern(shell, "lamp_p", (PX1 - 0.45, 2.2, HD + 0.08), size=0.34, metal="iron", chain_to=(PX1 - 0.45, pb - 0.12, HD + 0.02))
    top = ml.counter(shell, "pcounter", PX0 + 0.3, PX1 - 0.65, 1.42, 2.0, h=0.95, detail=det)
    pa.book_stack(det, "pbooks", (PX0 + 1.2, 0.95, 1.7), n=2, yaw=0.1, rng=rng, w=0.42, d=0.3, th=0.09)
    # crates in front of the pavilion: gold bars, cloth bundles
    ml.crate(shell, "gold_crate", (-2.15, 0.0, 2.75), size=(0.8, 0.82, 0.7), yaw=0.03, solid=True)
    pa.gold_bars(det, "gold", (-2.15, 0.82, 2.75), rows=2, yaw=math.pi / 2)
    pa.gold_bars(det, "gold_b", (-1.95, 0.82, 2.55), rows=1, yaw=0.0)
    ml.crate(shell, "bundle_crate", (-1.18, 0.0, 2.8), size=(0.75, 0.7, 0.66), yaw=-0.05, solid=True)
    for k, (dx, dz) in enumerate(((-0.17, -0.1), (0.17, -0.08), (0.0, 0.14), (-0.12, 0.12))):
        add_cube(det, "bundle_%d" % k, (-1.18 + dx, 0.82 + 0.06 * (k == 2), 2.8 + dz), ry(0.3 * k), (0.32, 0.22, 0.26), "cloth_beige")
    add_cube(det, "bundle_green", (-1.05, 0.98, 2.72), ry(0.4), (0.24, 0.14, 0.2), "herbs")
    # ---- the left awning: canvas, chains from the finial posts up to the pavilion's corner, prop pole, ivy
    lz0, lz1 = -1.6, 2.05
    awning(shell, det, "l_awning", PX0 - 0.05, P_EAVE - 0.25, LX - 0.3, AW_Y_OUT, lz0, lz1)
    for k, z in enumerate((1.75, -1.35)):
        beam(shell, "l_beam_%d" % k, (PX0, AW_Y_OUT - 0.15, z), (LX, AW_Y_OUT - 0.15, z), 0.2, "beam", extend=0.15)
    beam(shell, "l_beam_side", (LX, AW_Y_OUT - 0.1, -1.35), (LX, AW_Y_OUT - 0.1, 1.75), 0.2, "beam", extend=0.15)
    pa.chain(det, "l_chain", (LX, AW_Y_OUT + 0.55, 1.75), (W0 + 0.05, ey + 0.1, D - 0.05), link=0.12, region="black_iron")
    beam(shell, "l_prop", (LX + 0.55, 0.0, 3.1), (LX + 0.95, AW_Y_OUT - 0.2, 1.8), 0.13, "wood", extend=0.05)
    box(shell, "l_prop_stake", (LX + 0.38, 0.0, 2.92), (LX + 0.72, 0.28, 3.28), {"all": "wood", "+2": "end_grain"}, stretch=False)
    pa.rope_coil_post(det, "l_prop_rope", LX + 0.6, 2.95, 0.3, 0.55, d=0.14, turns=1)
    for k in range(3):
        ml.vine(det, "l_ivy_%d" % k, (LX - 0.32, AW_Y_OUT + 0.05, 1.4 - 0.55 * k), 1.1 + 0.35 * (k % 2), 0.45, normal=(-1, 0, 0))
    # the potions counter, crates of scrolls and cloth under it
    top = ml.counter(shell, "lcounter", LX + 0.25, PX0 - 0.35, 0.85, 1.5, h=1.0, detail=det)
    for k, (dx, col) in enumerate(((0.35, "purple"), (0.62, "cyan"), (0.88, "purple"), (1.15, "green"))):
        ml.bottle(det, "lpot_%d" % k, (LX + 0.25 + dx, 1.0, 1.15), col, r=0.085, h=0.22, shape="round" if k % 2 == 0 else "tall", neck_h=0.08,
                  glow=k in (0, 1))
    ml.crate(shell, "lcrate_0", (LX + 0.65, 0.0, 2.1), size=(0.7, 0.55, 0.6), yaw=0.05, solid=True)
    for k in range(3):
        pa.cloth_roll(det, "lscroll_%d" % k, (LX + 0.65, 0.62 + 0.0, 1.96 + 0.15 * k), length=0.6, r=0.07, region="cloth_beige", end="lg_roll_c")
    decor.block("furnish:spruce_crate", LX + 1.55, 0.0, 2.1, facing="front", alt="minecraft:barrel", fallback="crate")
    decor.block("farmhouse_decorations:pile_of_books", LX + 0.85, 1.0, 1.15, facing="front", solid=False, fallback="leather")
    ml.lantern(shell, "lamp_lc", (PX0 - 0.55, 1.18, 1.25), size=0.24, metal="iron")
    # ---- the right awning: canvas, prop pole, the cloth-rolls counter, chests
    rz0, rz1 = -1.6, 2.05
    awning(shell, det, "r_awning", HX1 + 0.05, H_EAVE - 0.25, RX + 0.3, AW_Y_OUT - 0.15, rz0, rz1)
    for k, z in enumerate((1.75, -1.35)):
        beam(shell, "r_beam_%d" % k, (HX1, AW_Y_OUT - 0.3, z), (RX, AW_Y_OUT - 0.3, z), 0.2, "beam", extend=0.15)
    beam(shell, "r_beam_side", (RX, AW_Y_OUT - 0.25, -1.35), (RX, AW_Y_OUT - 0.25, 1.75), 0.2, "beam", extend=0.15)
    beam(shell, "r_prop", (HX1 + 0.35, 2.35, HD + 0.05), (HX1 + 0.95, 0.0, 2.85), 0.12, "wood", extend=0.05)
    box(shell, "r_prop_stake", (HX1 + 0.8, 0.0, 2.7), (HX1 + 1.12, 0.26, 3.02), {"all": "wood", "+2": "end_grain"}, stretch=False)
    box(shell, "rcounter", (HX1 + 0.45, 0.0, 0.55), (RX - 0.2, 0.78, 1.35), {"all": "crate", "+2": "plank"}, solid=True)
    box(shell, "rcounter_top", (HX1 + 0.41, 0.78, 0.51), (RX - 0.16, 0.86, 1.39), "plank", stretch=False, u_dir=X)
    for k, (dx, zz, yy, reg, end) in enumerate(((0.0, 0.75, 0.98, "lg_striped", "lg_roll_r"), (0.0, 1.05, 0.98, "cloth_blue", "lg_roll_b"),
                                                (0.0, 0.9, 1.2, "cloth_beige", "lg_roll_c"), (0.85, 0.8, 0.98, "cloth_red", "lg_roll_r"))):
        pa.cloth_roll(det, "rroll_%d" % k, (HX1 + 1.05 + dx, yy, zz), length=1.0 if k < 3 else 0.6, r=0.13, region=reg, end=end)
    pa.book_stack(det, "rbooks", (RX - 0.55, 0.86, 1.15), n=4, yaw=0.2, rng=rng)
    pa.gold_bars(det, "rcoins", (RX - 0.55, 0.86, 0.75), rows=1, yaw=0.3, bar=(0.18, 0.06, 0.1))
    pa.chest(shell, det, "rchest_0", (HX1 + 1.0, 0.0, 1.85), w=0.8, d=0.55, h=0.6, yaw=0.0, region="lg_chest", trim="black_iron")
    pa.chest(shell, det, "rchest_1", (RX - 0.35, 0.0, 1.9), w=0.6, d=0.5, h=0.55, yaw=-0.15, region="lg_chest", trim="black_iron")
    decor.block("mebahelcreaturesdwarven:dwemer_chest", HX1 - 0.2, 0.0, 2.75, facing="front", alt="minecraft:chest", fallback="lg_chest")
    # ---- the hall's entrance: lion banners, curtains tied back, lanterns
    for k, x in enumerate((PX1 + 0.35, HX1 - 0.35)):
        ml.banner(shell, "banner_%d" % k, (x, hy - 0.1, HD2 + 0.1), 0.6, 1.9, normal=(0, 0, 1), region="lg_banner", rod=True, wave=0.03,
                  rod_region="wood_dark")
    pa.drape_tied(shell, det, "curtain_l", (PX1 + 0.28, hb - 0.12, HD - 0.15), (PX1 + 1.15, hb - 0.12, HD - 0.15), (PX1 + 0.38, 1.2, HD - 0.18),
                  (PX1 + 0.25, 0.03, HD - 0.18), (PX1 + 0.75, 0.03, HD - 0.18), Z, "lg_curtain_c", nx=3)
    pa.drape_tied(shell, det, "curtain_r", (HX1 - 0.26, hb - 0.12, HD - 0.15), (HX1 - 1.2, hb - 0.12, HD - 0.15), (HX1 - 0.4, 1.2, HD - 0.18),
                  (HX1 - 0.25, 0.03, HD - 0.18), (HX1 - 0.8, 0.03, HD - 0.18), Z, "lg_curtain_c", nx=3)
    pa.drape_tied(shell, det, "curtain_rb", (HX1 - 0.3, hb - 0.15, HD - 0.3), (HX1 - 0.85, hb - 0.15, HD - 0.3), (HX1 - 0.42, 1.35, HD - 0.33),
                  (HX1 - 0.3, 0.03, HD - 0.33), (HX1 - 0.6, 0.03, HD - 0.33), Z, "lg_curtain_b", nx=2)
    ml.lantern(shell, "lamp_l", (PX1 + 0.85, 2.45, HD + 0.05), size=0.44, metal="iron", chain_to=(PX1 + 0.85, hb - 0.12, HD + 0.02))
    pa.lantern_bracket(det, shell, "lamp_r", (HX1 + 0.2, 3.0, HD + 0.05), (1, 0, 0.3), y_drop=0.55, size=0.42, arm=0.5)
    ml.lantern(shell, "lamp_in", (1.6, 2.4, -0.4), size=0.32, metal="iron", chain_to=(1.6, hb - 0.12, -0.4))
    beam(shell, "tie_beam", (PX1, hb, -0.4), (HX1, hb, -0.4), 0.18, "wood_dark", extend=0.08)
    # ---- inside: the writing desk (open ledger, scroll, ink) and the back shelves of sacks, jars, pots, books
    dx0, dx1, dz0, dz1 = DESK
    top = ml.counter(shell, "desk", dx0, dx1, dz0, dz1, h=DESK_H, detail=det)
    y = top[1]
    add_cube(shell, "ledger_l", (dx0 + 0.45, y + 0.04, (dz0 + dz1) / 2), rz(0.08), (0.36, 0.04, 0.42), {"all": "white", "+2": "lg_book"}, stretch=True)
    add_cube(shell, "ledger_r", (dx0 + 0.82, y + 0.04, (dz0 + dz1) / 2), rz(-0.08), (0.36, 0.04, 0.42), {"all": "white", "+2": "lg_book"}, stretch=True)
    add_cube(det, "ledger_cover", (dx0 + 0.635, y + 0.012, (dz0 + dz1) / 2), EYE, (0.8, 0.02, 0.48), "leather_dark")
    pa.cloth_roll(det, "desk_scroll", (dx1 - 0.15, y + 0.06, dz0 + 0.18), length=0.42, r=0.05, yaw=0.3, region="cloth_beige", end="lg_roll_c")
    ml.bottle(det, "ink", (dx0 + 0.12, y, dz0 + 0.15), "blue", r=0.05, h=0.08, shape="tall", neck_h=0.03, cork=False)
    shelf_l = ml.shelf_unit(shell, "shelves", -2.8, 2.35, -HD + 0.12, -HD + 0.6, levels=(0.55, 1.1, 1.65, 2.2), h=2.5, back=True,
                            uprights=5, detail=det)
    for j, (x0, x1, yy, zf, zb) in enumerate(sorted(shelf_l, key=lambda s: s[2])):
        zc = (zf + zb) / 2
        if j == 0:
            for i in range(5):
                ml.sack(det, "ssack_%d" % i, (x0 + 0.35 + i * 1.0, yy, zc), s=0.34, yaw=0.3 * i)
        elif j == 1:
            for i in range(9):
                ml.bottle(det, "sjar_%d" % i, (x0 + 0.25 + i * 0.55, yy, zc), ("orange", "green", "yellow")[i % 3], r=0.1, h=0.2,
                          shape="tall" if i % 2 else "round")
        elif j == 2:
            pa.book_row(det, "sbooks_0", x0 + 0.1, x0 + 1.4, yy, zc, h=0.3, region="lg_books")
            pa.potion_row(det, "spots", x0 + 1.9, x1 - 0.2, yy, zc, ("red", "blue", "purple", "cyan"), rng, n=10)
        else:
            for i in range(4):
                ml.basket(det, "sbasket_%d" % i, (x0 + 0.5 + i * 1.25, yy, zc), r=0.18, h=0.16, content="apples" if i % 2 else "produce")
            pa.book_stack(det, "spile", (x1 - 0.35, yy, zc), n=3, rng=rng)
    # ---- the rug out of the entrance over a stone threshold
    ml.rug(shell, "rug", -0.05, 1.95, 0.0, 4.35, y=0.0, region="lg_rug")
    box(shell, "threshold", (-0.25, 0.0, HD - 0.05), (2.15, 0.06, HD + 0.35), {"all": "lg_stone"}, stretch=False, u_dir=X)
    return root


def item_icon(path):
    """16x16: the long tent: a blue / cream pointed peak on the left, the striped hall on the right, cream awnings."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    wood = (110, 72, 40, 255)
    for y in range(1, 9):   # the pointed peak (x 3..8)
        half = (y - 1) * 0.55
        for x in range(16):
            if abs(x - 5.5) <= half + 0.3:
                p[x, y] = (BLUE if int((x - 5.5 + half) / max(1.0, half) * 1.5) % 2 == 0 else CREAM) + (255,)
    p[5, 0] = p[6, 0] = GOLD + (255,)
    for y in range(4, 9):   # the hall (x 8..12)
        for x in range(8, 13):
            if y >= 4 + (12 - x) // 3:
                p[x, y] = (BLUE if (x // 2) % 2 == 0 else CREAM) + (255,)
    for x in range(0, 16):  # awnings
        if x < 3 or x > 12:
            p[x, 8] = (230, 210, 170, 255)
    for x in range(1, 15):
        p[x, 9] = (GOLD if x % 2 == 0 else CREAM) + (255,)
    for y in range(10, 15):
        for x in (0, 3, 8, 12, 15):
            p[x, y] = wood
        for x in range(9, 12):
            p[x, y] = (40, 28, 18, 255)
    p[8, 10] = p[8, 11] = BLUE + (255,)
    p[8, 11] = GOLD + (255,)
    for x in range(0, 16):
        p[x, 15] = (BLUE if 9 <= x <= 11 else (90, 70, 45)) + (255,)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)


def main():
    pa.setup(NAME)
    atlas = ml.Atlas(NAME, colour="blue")
    regions(atlas)
    decor = ml.Decor()
    root = build(atlas, decor)
    ml.export(root, NAME, atlas, decor=decor, icon=item_icon, light=13)
    print("atlas", atlas.size, "NPC spot", NPC_SPOT)


if __name__ == "__main__":
    main()
