#!/usr/bin/env python3
"""tente_lion_pavillon — Pavillon au lion / Lion Pavilion (1.26.0, Lion Port market, group A; reference
scratchpad/ref2/tente_lion_pavillon_ref.png, picture 032).

A blue and cream striped merchant pavilion, one block (TentType group "tents"), about 8 x 7 blocks (crates, sacks and
the rug included), the finial at about 5.8 (a low, wide pavilion, as in the picture):

  - a low bell-shaped hipped roof, flaring out flat at the eaves and rising steeply to a pointed centre under a gold
    finial and a cream crown ring with gold tabs, wide blue / warm cream gores, a blue valance with deep square tabs
    edged in gold all round;
  - on the front, the LION CREST: a tall blue banner board (gold border, the golden lion rampant, V point) standing on
    the front eave under a gold-capped bar (braced back to the roof), rising in front of the roof slope and hanging on
    past the valance, flanked by two shorter cream pennants with gold fleurs-de-lis;
  - four dark posts on grey stone feet with iron bands and caps poking through the roof corners, eave beams, braces;
  - a tall BANNER POLE at the front left (stone foot, a cross bar carrying the blue banner with the gold cross fleury,
    a thick twisted rope hanging from the bar's outer end), a rope of blue / cream pennant BUNTING running from its top
    to the roof's finial;
  - cream drapes with faint gold fleurs tied back at the front corners and along the left side, the striped back and
    side walls, an ivy planter hanging off the front-left post;
  - inside: the COUNTER under a blue cloth with gold dags and fleurs-de-lis (piles of red and blue books, an open map,
    a small lantern), the back SHELVES of potions (purple, teal, red, blue), books and jars, a cabinet with a blue
    fleur-de-lis hanging; on the right a low table of fat CLOTH BOLTS stacked in a pyramid (blue, red-striped, cream,
    red rolls) with books, and the gold
    chest at the front right; two lanterns hanging under the front eave;
  - outside: two big burlap SACKS at the front left, crates on the left and the right, the blue RUG with gold scrolls
    from the counter out past the front.

The merchant's place (an EasyNPC, 1 x 1 x 2.2 free) is behind the counter (NPC_SPOT); players walk in by the front
between the counter and the cloth table. No trade system, nothing ticks.

Usage:  python3 tools/market/generate_tente_lion_pavillon.py     (MERCHANT_OUT=<file.bbmodel>: preview model only)
Writes (merchantlib.export): tents/tente_lion_pavillon.json, models/entity + blockbench/tente_lion_pavillon.bbmodel,
textures/entity/tente_lion_pavillon.png, textures/item/tente_lion_pavillon.png, interiors/tente_lion_pavillon_decor.json.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import props_a as pa  # noqa: E402

ml = pa.ml
v3, norm, add_cube, beam, loft, Bone = pa.v3, pa.norm, pa.add_cube, pa.beam, pa.loft, pa.Bone
EYE, UP, X, Z = pa.EYE, pa.UP, pa.X, pa.Z
ry, rx, rz = pa.ry, pa.rx, pa.rz
box, collide = pa.box, pa.collide
BLUE, CREAM, GOLD = pa.BLUE, pa.CREAM, pa.GOLD

NAME = "tente_lion_pavillon"
# ---------------------------------------------------------------- dimensions (tent-local blocks, +z = the open front)
HW, HD = 3.0, 2.4            # corner posts at x = +-HW, z = +-HD
EAVE = 3.15                  # top of the eave beams (a low, wide pavilion)
EY = 3.2                     # the roof's lower edge
AY = 4.75                    # the roof's apex (a low roof, pointed under the finial)
ROOF_A, ROOF_PW = 0.25, 2.5  # the bell profile: steep under the finial, flaring out flat at the eaves
W, D = HW + 0.45, HD + 0.45  # the roof's eave corners
PX, PZ = -HW - 0.8, HD - 0.3    # the tall banner pole (outside the left side, near the front corner)
POLE_TOP = 5.5
COUNTER = (-2.4, -0.35, 0.85, 1.5)   # x0, x1, z0, z1
COUNTER_H = 1.0
TABLE = (0.8, 2.6, 0.0, 0.85)
NPC_SPOT = (-1.45, -0.7)     # (x0, z0) of the free 1 x 1 x 2.2 place behind the counter (the merchant)


def regions(atlas):
    pa.add_regions(atlas, "pv", [
        ("roof", 128, 96, pa.stripes([BLUE, pa._mix(CREAM, pa.CREAM_D, 0.3)], 4, 3201, fold=0.17)),
        ("rug", 96, 112, pa.rug(3202, scrolls=True)),
        ("cross", 40, 80, pa.banner(3203, emblem="cross", bottom="point", box=(0.16, 0.1, 0.84, 0.56))),
        ("crest", 44, 88, pa.banner(3204, emblem="lion", bottom="point", inner=pa.BLUE_D, box=(0.1, 0.09, 0.9, 0.6))),
        ("wall", 128, 64, pa.stripes([BLUE, CREAM], 8, 3205, fold=0.2)),
        ("drape", 48, 64, pa.drape(3206)),
        ("pennant", 26, 58, pa.pennant(3207)),
        ("fdl", 32, 48, pa.banner(3208, emblem="fdl", bottom="point", box=(0.18, 0.12, 0.82, 0.56))),
        ("cloth", 96, 40, pa.counter_cloth(3209)),
        ("valance", 256, 24, pa.dag_valance(12, 3210, band=0.36)),
        ("stone", 32, 32, pa.stone(3211)),
        ("chest", 32, 32, pa.chest_wood(3212)),
        ("map", 32, 24, pa.parchment(3213)),
        ("post", 64, 16, pa.post_wood(3224)),
        ("burlap", 32, 32, pa.burlap(3226)),
        ("wall_r", 32, 32, pa.stripes([pa._rgb("a82a26"), CREAM], 4, 3225, fold=0.1)),
        ("runner", 32, 32, pa.drape(3223, cloth=pa.CREAM, folds=1, motif="fdl")),
        ("ring", 64, 12, pa.dag_valance(8, 3227, cloth=CREAM, edge=GOLD, shape="square", band=0.62)),
        ("bunt_b", 16, 24, pa.bunting_flag(3214, BLUE)),
        ("bunt_c", 16, 24, pa.bunting_flag(3215, CREAM)),
        ("books", 64, 16, pa.books(3216)),
        ("roll_b", 16, 16, pa.roll_end(3217, BLUE)),
        ("roll_r", 16, 16, pa.roll_end(3218, pa._rgb("a82a26"))),
        ("roll_c", 16, 16, pa.roll_end(3219, pa.CREAM_D, core=pa._rgb("8a6a40"))),
    ])


def build(atlas, decor):
    rng = random.Random(32)
    root = Bone(NAME)
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)
    # ---- the four corner posts (stone feet, iron bands, caps poking through the roof corners)
    corners = [(-HW, HD), (HW, HD), (HW, -HD), (-HW, -HD)]   # FL, FR, BR, BL
    for k, (x, z) in enumerate(corners):
        pa.post(shell, det, "post_%d" % k, x, z, EY + 0.32, d=0.38, bands=(1.25, 2.55), cap=0.52, collide_top=EAVE, stone_region="pv_stone", post_region="pv_post")
    by = EAVE - 0.15
    for k in range(4):
        (xa, za), (xb, zb) = corners[k], corners[(k + 1) % 4]
        beam(shell, "eave_%d" % k, (xa, by, za), (xb, by, zb), 0.3, {"all": "beam", "+1": "end_grain", "-1": "end_grain"}, width=0.26,
             extend=0.12)
    for k, (p, q) in enumerate((((-HW + 0.18, EAVE - 1.1, HD), (-HW + 0.9, by - 0.1, HD)), ((HW - 0.18, EAVE - 1.1, HD), (HW - 0.9, by - 0.1, HD)),
                                ((-HW, EAVE - 1.1, -HD + 0.18), (-HW, by - 0.1, -HD + 0.9)), ((HW, EAVE - 1.1, -HD + 0.18), (HW, by - 0.1, -HD + 0.9)))):
        beam(shell, "brace_%d" % k, p, q, 0.14, "wood_dark", extend=0.05)
    beam(shell, "tie_beam", (-HW, by, 0.0), (HW, by, 0.0), 0.2, "wood_dark", extend=0.1)
    beam(shell, "king_post", (0, by, 0), (0, AY - 0.1, 0), 0.18, "wood_dark")
    # ---- the bell-shaped hipped roof, blue / cream gores
    roof_y = pa.hip_roof(shell, "roof", (0, AY, 0), [(-W, EY, D), (W, EY, D), (W, EY, -D), (-W, EY, -D)], "pv_roof", nx=4, ny=14, a=ROOF_A,
                         droop=0.08, pw=ROOF_PW)
    # cream cords along the four hips (over the joins of the faces)
    for k, (cx, cz) in enumerate(((-W, D), (W, D), (W, -D), (-W, -D))):
        pts = []
        for i in range(7):
            t = i / 6
            pts.append(v3(cx * t, AY - (AY - EY) * pa.bell(t, ROOF_A, ROOF_PW) + 0.03, cz * t))
        for i in range(6):
            beam(det, "hip_%d_%d" % (k, i), pts[i], pts[i + 1], 0.07, "cloth_beige", width=0.12, extend=0.03)
    box(shell, "apex_collar", (-0.17, AY - 0.1, -0.17), (0.17, AY + 0.12, 0.17), "gold", stretch=False)
    pa.finial_spike(shell, "apex_finial", (0, AY + 0.1, 0), h=0.8, w=0.26)
    # the cream crown ring with gold tabs round the roof under the finial
    t_r = 0.075
    rw, rd, ry0 = W * t_r + 0.05, D * t_r + 0.05, AY - (AY - EY) * pa.bell(t_r, ROOF_A, ROOF_PW)
    for k, (c0, c1, o) in enumerate((((-rw, ry0, rd), (rw, ry0, rd), Z), ((rw, ry0, rd), (rw, ry0, -rd), X),
                                     ((rw, ry0, -rd), (-rw, ry0, -rd), -Z), ((-rw, ry0, -rd), (-rw, ry0, rd), -X))):
        pa.valance(det, "crown_%d" % k, c0, c1, o, h=0.2, region="pv_ring", segs=1, flare=0.04)
    # ---- the valance (blue, square tabs edged in gold) on the four sides, curving a little between the corners
    for k, (c0, c1, o) in enumerate((((-W, EY, D + 0.02), (W, EY, D + 0.02), Z), ((W + 0.02, EY, D), (W + 0.02, EY, -D), X),
                                     ((W, EY, -D - 0.02), (-W, EY, -D - 0.02), -Z), ((-W - 0.02, EY, -D), (-W - 0.02, EY, D), -X))):
        pa.valance(shell, "valance_%d" % k, c0, c1, o, h=0.6, region="pv_valance", segs=6, sag=0.06)
    # ---- the lion crest: a tall blue banner board standing on the front eave, rising in front of the roof slope and
    # hanging on past the valance, under a gold-capped bar (a brace behind it back to the roof); the two cream
    # fleur-de-lis pennants beside it, shorter
    zc, CW, CT, CB = D + 0.13, 0.84, EY + 1.0, EY - 0.72
    ml.banner(shell, "crest", (0.0, CT, zc), CW, CT - CB, normal=(0, 0, 1), region="pv_crest", rod=False, wave=0.02)
    box(shell, "crest_bar", (-CW / 2 - 0.09, CT - 0.01, zc - 0.08), (CW / 2 + 0.09, CT + 0.12, zc + 0.06), {"all": "trim_gold", "-1": "gold",
                                                                                                             "+1": "gold"}, u_dir=X)
    box(det, "crest_bar_top", (-CW / 2 - 0.02, CT + 0.12, zc - 0.05), (CW / 2 + 0.02, CT + 0.16, zc + 0.03), "cloth_beige", u_dir=X)
    for k, sx in enumerate((-1, 1)):
        add_cube(det, "crest_knob_%d" % k, (sx * (CW / 2 + 0.13), CT + 0.055, zc - 0.01), EYE, (0.11, 0.17, 0.11), "gold")
    zb = 2.0
    beam(shell, "crest_brace", (0.0, CT + 0.02, zc - 0.08), (0.0, roof_y(0.0, zb) + 0.02, zb), 0.08, "wood_dark", width=0.08)
    for k, sx in enumerate((-1, 1)):
        xp = sx * 0.77
        ml.banner(shell, "pennant_%d" % k, (xp, EY + 0.56, zc - 0.01), 0.54, 1.24, normal=(0, 0, 1), region="pv_pennant", rod=True,
                  wave=0.02, rod_region="gold")
    # ---- the tall banner pole at the front left: stone foot, rope wound round it, cross bar, the cross banner
    pa.post(shell, det, "pole", PX, PZ, POLE_TOP, d=0.34, stone_w=0.62, stone_h=0.55, bands=(1.4, 2.6), cap=0.46, stone_region="pv_stone", post_region="pv_post")
    bar_y = POLE_TOP - 0.22
    # the thick twisted rope hanging from the bar's outer end down past the banner
    for k in range(13):
        add_cube(det, "pole_rope_%d" % k, (PX - 0.26, bar_y - 0.1 - k * 0.12, PZ + 0.2), ry(k * 0.75) @ rz(0.3)[:3, :3], (0.12, 0.14, 0.12), "rope")
    beam(shell, "pole_bar", (PX - 0.3, bar_y, PZ + 0.2), (PX + 1.15, bar_y, PZ + 0.2), 0.12, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    box(det, "pole_bar_strap", (PX - 0.2, bar_y - 0.1, PZ + 0.02), (PX + 0.2, bar_y + 0.1, PZ + 0.3), "iron", stretch=False)
    beam(det, "pole_bar_brace", (PX + 0.12, bar_y - 0.6, PZ + 0.2), (PX + 0.7, bar_y - 0.03, PZ + 0.2), 0.07, "wood_dark")
    ml.banner(shell, "pole_banner", (PX + 0.6, bar_y - 0.06, PZ + 0.27), 0.82, 1.95, normal=(0, 0, 1), region="pv_cross", rod=False, wave=0.04)
    for k, dx in enumerate((-0.3, 0.3)):
        add_cube(det, "pole_ring_%d" % k, (PX + 0.6 + dx, bar_y - 0.03, PZ + 0.25), EYE, (0.05, 0.12, 0.05), "iron")
    # the bunting from the pole top to the finial
    pa.bunting(det, det, "bunting", (PX + 0.1, POLE_TOP - 0.05, PZ - 0.1), (0, AY + 0.35, 0.1), 8, ["pv_bunt_b", "pv_bunt_c"], sag=0.62,
               size=(0.38, 0.56))
    # ---- walls: the back, the closed back half of the sides (blue / cream stripes)
    pa.wall(shell, "wall_back", (-HW, 0, -HD - 0.06), (HW, 0, -HD - 0.06), 0.0, by - 0.15, -Z, "pv_wall", nx=8)
    collide((-HW, 0.0, -HD - 0.12, HW, by - 0.15, -HD))
    pa.wall(shell, "wall_left", (-HW - 0.06, 0, -HD), (-HW - 0.06, 0, -0.35), 0.0, by - 0.15, -X, "pv_wall", nx=4)
    collide((-HW - 0.12, 0.0, -HD, -HW, by - 0.15, -0.35))
    pa.wall(shell, "wall_right", (HW + 0.06, 0, -0.1), (HW + 0.06, 0, -HD), 0.0, by - 0.15, X, "pv_wall", nx=4)
    collide((HW, 0.0, -HD, HW + 0.12, by - 0.15, -0.1))
    # ---- cream drapes tied back: along the left side, at the two front corners
    pa.drape_tied(shell, det, "drape_left", (-HW - 0.03, by - 0.15, -0.4), (-HW - 0.03, by - 0.15, HD - 0.3), (-HW - 0.05, 1.3, HD - 0.5),
                  (-HW - 0.03, 0.03, HD - 0.75), (-HW - 0.03, 0.03, HD - 0.3), -X, "pv_drape", nx=3)
    pa.drape_tied(shell, det, "drape_fl", (-HW + 0.22, by - 0.15, HD - 0.08), (-HW + 1.25, by - 0.15, HD - 0.08), (-HW + 0.32, 1.2, HD - 0.1),
                  (-HW + 0.22, 0.03, HD - 0.14), (-HW + 0.85, 0.03, HD - 0.14), Z, "pv_drape", nx=3)
    pa.drape_tied(shell, det, "drape_fr", (HW - 0.22, by - 0.15, HD - 0.08), (HW - 1.5, by - 0.15, HD - 0.08), (HW - 0.34, 1.15, HD - 0.1),
                  (HW - 0.22, 0.03, HD - 0.14), (HW - 0.95, 0.03, HD - 0.14), Z, "pv_drape", nx=3)
    # ---- the ivy planter off the front-left post
    pa.ivy_planter(shell, det, "ivy", (-HW + 0.2, 2.65, HD + 0.05), (0.55, 0, 1), w=0.82)
    # ---- lanterns hanging under the front eave
    for k, x in enumerate((-1.25, 1.95)):
        ml.lantern(shell, "lamp_%d" % k, (x, 2.45, HD - 0.12), size=0.42, metal="iron", chain_to=(x, by - 0.12, HD - 0.05))
    # ---- the counter under the blue cloth with gold dags, its goods
    cx0, cx1, cz0, cz1 = COUNTER
    top = ml.counter(shell, "counter", cx0, cx1, cz0, cz1, h=COUNTER_H, detail=det)
    y = top[1]
    box(shell, "cloth_top", (cx0 - 0.02, y, cz0 - 0.02), (cx1 + 0.02, y + 0.015, cz1 + 0.04), {"all": "cloth"}, u_dir=X)
    pa.plate(shell, "cloth_front", ((cx0 + cx1) / 2, y - 0.36, cz1 + 0.05), cx1 - cx0 + 0.06, 0.74, "pv_cloth", normal=(0, 0, 1), th=0.012)
    # a cream runner with a gold pattern laid over the middle of the counter, hanging down the front
    rx0, rx1 = cx0 + 0.75, cx0 + 1.55
    box(shell, "runner_top", (rx0, y + 0.016, cz0 + 0.05), (rx1, y + 0.026, cz1 + 0.06), {"all": "pv_runner"}, u_dir=X)
    pa.plate(shell, "runner_front", ((rx0 + rx1) / 2, y - 0.2, cz1 + 0.065), rx1 - rx0, 0.44, "pv_runner", normal=(0, 0, 1), th=0.01)
    pa.book_stack(det, "books_l", (cx0 + 0.3, y + 0.015, cz0 + 0.3), n=4, yaw=0.15, rng=rng)
    for k, (dx, reg, hh) in enumerate(((0.62, "cloth_red", 0.42), (0.78, "cloth_blue", 0.46), (0.92, "cloth_red", 0.36))):
        box(det, "tome_%d" % k, (cx0 + dx, y + 0.015, cz0 + 0.12), (cx0 + dx + 0.13, y + 0.015 + hh, cz0 + 0.45), {"all": reg, "+2": "white", "-3": "white"},
            stretch=False)
    pa.plate(det, "map", (cx0 + 1.42, y + 0.025, (cz0 + cz1) / 2 + 0.05), 0.62, 0.42, "pv_map", normal=(0, 1, 0), up=(0, 0, -1), th=0.01)
    ml.lantern(shell, "lamp_counter", (cx1 - 0.22, y + 0.2, cz0 + 0.3), size=0.24, metal="iron")
    box(det, "lamp_counter_base", (cx1 - 0.36, y + 0.015, cz0 + 0.16), (cx1 - 0.08, y + 0.05, cz0 + 0.44), "iron", stretch=False)
    # ---- the back shelves: potions, books, jars; the cabinet with the fleur-de-lis hanging
    levels = ml.shelf_unit(shell, "shelves", -HW + 0.4, -0.2, -HD + 0.15, -HD + 0.65, levels=(0.55, 1.1, 1.65, 2.2), h=2.5, back=True,
                           uprights=3, detail=det)
    pots = ("purple", "cyan", "red", "blue", "pink", "purple", "green", "cyan")
    for j, (x0, x1, yy, zf, zb) in enumerate(sorted(levels, key=lambda s: s[2])):
        zc = (zf + zb) / 2
        if j in (1, 2):
            pa.potion_row(det, "pots_%d" % j, x0 + 0.05, x1 - 0.05, yy, zc, pots[j:] + pots[:j], rng, n=9)
        elif j == 3:
            pa.book_row(det, "shelf_books", x0 + 0.05, x0 + 1.2, yy, zc, h=0.28, region="pv_books")
            ml.bottle(det, "jar_0", (x1 - 0.45, yy, zc), "green", r=0.1, h=0.22, shape="tall")
            ml.lantern(shell, "lamp_shelf", (x1 - 0.18, yy + 0.16, zc), size=0.22, metal="iron")
        else:
            ml.sack(det, "shelf_sack", (x0 + 0.35, yy, zc), s=0.34, yaw=0.3)
            ml.crate(det, "shelf_box", (x0 + 1.0, yy, zc), size=(0.45, 0.3, 0.36), solid=False)
            pa.book_stack(det, "shelf_pile", (x1 - 0.4, yy, zc), n=3, rng=rng)
    cab = (0.2, 1.35, -HD + 0.12, -HD + 0.7)
    box(shell, "cabinet", (cab[0], 0.0, cab[2]), (cab[1], 2.3, cab[3]), {"all": "plank_dark", "+3": "crate"}, solid=True)
    box(shell, "cabinet_top", (cab[0] - 0.06, 2.3, cab[2] - 0.04), (cab[1] + 0.06, 2.4, cab[3] + 0.05), "wood_dark")
    ml.banner(shell, "cabinet_fdl", ((cab[0] + cab[1]) / 2, 2.22, cab[3] + 0.03), 0.62, 0.95, normal=(0, 0, 1), region="pv_fdl", rod=True,
              wave=0.02, rod_region="gold")
    pa.cloth_roll(det, "cab_roll", ((cab[0] + cab[1]) / 2, 2.52, (cab[2] + cab[3]) / 2), length=0.95, r=0.1, region="cloth_red", end="pv_roll_r")
    # ---- the cloth table on the right: rolls of cloth (blue, red, cream), books
    tx0, tx1, tz0, tz1 = TABLE
    box(shell, "table_body", (tx0, 0.0, tz0), (tx1, 0.72, tz1), {"all": "crate", "+2": "plank"}, solid=True)
    box(shell, "table_top", (tx0 - 0.04, 0.72, tz0 - 0.04), (tx1 + 0.04, 0.8, tz1 + 0.04), "plank", stretch=False, u_dir=X)
    # fat bolts in a pyramid: three below, two above, one on top (their spiral ends towards the entrance side)
    for k, (zz, yy, reg, end) in enumerate(((0.16, 0.96, "cloth_blue", "pv_roll_b"), (0.46, 0.96, "pv_wall_r", "pv_roll_r"),
                                           (0.76, 0.96, "cloth_beige", "pv_roll_c"), (0.31, 1.23, "cloth_red", "pv_roll_r"),
                                           (0.61, 1.23, "cloth_blue", "pv_roll_b"), (0.46, 1.5, "pv_wall_r", "pv_roll_r"))):
        pa.cloth_roll(det, "roll_%d" % k, ((tx0 + tx1) / 2 - 0.2 + 0.06 * (k % 2), yy, tz0 + zz), length=1.25, r=0.155, region=reg, end=end)
    pa.book_stack(det, "table_books", (tx1 - 0.3, 0.8, tz0 + 0.25), n=5, yaw=-0.2, rng=rng)
    decor.block("furnish:book_pile", tx1 - 0.35, 0.8, tz1 - 0.15, facing="front", solid=False, fallback="leather")
    # the gold chest at the front right
    decor.block("mebahelcreaturesdwarven:dwemer_chest", 2.05, 0.0, 1.55, facing="front", alt="minecraft:chest", fallback="pv_chest")
    # ---- the rug from the counter out past the front
    ml.rug(shell, "rug", -2.0, 1.55, -0.1, 3.95, y=0.0, region="pv_rug")
    # ---- outside: the big sacks at the front left, crates on the left and the right
    pa.sack_big(shell, det, "sack_0", (-2.4, 0.0, 3.05), yaw=0.2, w=0.8, h=1.12, region="pv_burlap")
    pa.sack_big(shell, det, "sack_1", (-1.6, 0.0, 3.3), yaw=-0.3, w=0.74, h=1.02, region="pv_burlap")
    collide((-2.8, 0.0, 2.65, -1.23, 1.0, 3.67))
    decor.block("furnish:spruce_crate", -3.85, 0.0, 1.05, facing="front", alt="minecraft:barrel", fallback="crate")
    ml.crate(shell, "crate_l_top", (-3.85, 1.0, 1.05), size=0.62, yaw=0.15, solid=True)
    ml.crate(shell, "crate_l_low", (-3.8, 0.0, 0.05), size=(0.7, 0.55, 0.62), yaw=-0.1, solid=True)
    ml.crate(shell, "crate_r_0", (3.7, 0.0, 1.35), size=0.62, yaw=0.1, solid=True)
    ml.crate(shell, "crate_r_1", (3.72, 0.62, 1.38), size=0.45, yaw=-0.2, solid=True)
    ml.crate(det, "crate_r_small", (3.6, 0.0, 2.15), size=(0.4, 0.3, 0.36), yaw=0.3, solid=False)
    return root


def item_icon(path):
    """16x16: the blue / cream striped pavilion icon (gold lion dot on the banner) + the tall banner pole on the left."""
    from PIL import Image
    ml.icon(path, colour="blue", emblem="star")
    im = Image.open(path).convert("RGBA")
    p = im.load()
    for y in range(0, 15):
        p[0, y] = (96, 64, 34, 255)
    for y in range(1, 5):
        p[1, y] = BLUE + (255,)
        p[2, y] = BLUE + (255,) if y < 4 else (0, 0, 0, 0)
    p[1, 2] = GOLD + (255,)
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
