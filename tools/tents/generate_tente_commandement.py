#!/usr/bin/env python3
"""tente_commandement — the military command tent (camp militaire 1.25.0; reference scratchpad/ref/tente_commandement_ref.png).

A big rectangular marquee (posts 9.8 x 11.8 blocks, the cloth 10.7 x 12.5, walls 3.9 high, the ridge at 6.9) of mottled
olive canvas: a gabled roof running front to back whose two slopes sag between the rafters, stepped beige-and-olive camo
bands along its ends and eaves, dagged camo bargeboards along the front and back roof edges, a dagged camo valance all
round the eaves, canvas walls with soft folds, thick wooden posts with riveted iron bands at the corners, along the sides
and at the entrance (the corner posts poking above the eave, two king posts through the ridge), the front beam with a
dagged valance hanging under it, thick guy ropes to grey anchor stones, a big central entrance (4.4 wide) under the front
gable with camo curtains tied back (the left one darker olive), a big green banner (gold border, pointed bottom, gold
crossed swords in a laurel wreath) on the front gable, two more on the front wall either side of the entrance, glowing
lanterns hanging left and right of the entrance, the ridge pole ending in a tall flag pole with a small olive
swallow-tailed flag, crossed poles over the back gable.
Inside, a command post: a large strategy table with a campaign map, scrolls, a pile of books, an ink pot with a
quill and a lamp; a chair; two tall bookshelves and crates of equipment along the back wall; a weapon rack; a lantern
hanging from the ridge; a red ornate carpet from the entrance; free floor for several NPCs.
Outside (part of the model): front left a table with a map, scrolls, quills and a lantern on a small crate, a stack of
crates marked with crossed swords with a steel knight's helmet on top, small crates in front; on the right a chest,
crates and a cart wheel leaning on the wall.

Usage:  python3 tools/tents/generate_tente_commandement.py   (MERCHANT_OUT=<file.bbmodel>: only the model, for previews)
Writes: blockbench/tente_commandement.bbmodel, models/entity/tente_commandement.bbmodel, textures/entity/tente_commandement.png,
        textures/item/tente_commandement.png, interiors/tente_commandement_decor.json, tents/tente_commandement.json.
Tent-local coordinates: y up, +z = the front (the entrance, towards the player who placed it), the anchor block at (0, 0, 0).
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "merchant"))
import merchantlib as ml  # noqa: E402
import props_tente_commandement as pc  # noqa: E402

tl = ml.tl
v3, UP, EYE, X, Z = ml.v3, ml.UP, ml.EYE, ml.X, ml.Z
beam, add_cube, loft, box, collide = ml.beam, ml.add_cube, ml.loft, ml.box, ml.collide

NAME = "tente_commandement"
HW, HD = 4.9, 5.9            # post centres: half width (x), half length (z)
EAVE = 3.9                   # top of the walls
RIDGE = 6.9                  # the ridge (top of the cloth)
RX, RZ = HW + 0.45, HD + 0.35   # the roof's edges: overhang beyond the posts
EDGE_Y = 3.75                # height of the roof edge (at the rafters)
RAFTERS = (-HD, -2.0, 2.0, HD)
DOOR = 2.2                   # half width of the entrance (the entrance posts)
BEAM_Y = 3.85                # the front beam across the top of the front wall (centre), the valance hanging under it
VAL_DROP = 0.6               # depth of the front valance hanging from the beam
LINTEL = BEAM_Y - 0.06 - VAL_DROP + 0.01   # top of the opening = the tips of the front valance's dags
POST_TOP = 4.55              # tops of the corner posts (above the roof edge)
SAG, DROOP, SLACK = 0.55, 0.25, 0.06   # cloth sag between rafters, eave droop between posts, overall slack
TABLE = (0.0, -2.2, 3.0, 1.7, 1.0)    # strategy table: centre x, z, length (x), width (z), height
OUT_TABLE = (-1.95, 7.45, 2.25, 1.0, 0.88)   # the table outside, front left
# free 1 x 1 x 2.2 spots for NPCs (x0, z0): checked by CampCommandementTest
NPC_SPOTS = ((-3.5, 0.0), (2.5, 0.0), (-3.5, 2.5), (2.5, 2.5), (-0.5, -1.2))


def bay(z):
    """0 on the rafters, 1 in the middle of a bay (the cloth sags between the rafters); 0 on the overhangs."""
    for a, b in zip(RAFTERS[:-1], RAFTERS[1:]):
        if a <= z <= b:
            return math.sin(math.pi * (z - a) / (b - a))
    return 0.0


ROOF_NX = 14   # strips along the ridge: one per overhang, four per bay (the rafters fall on strip edges)
S_RAFTERS = (1 / ROOF_NX, 5 / ROOF_NX, 9 / ROOF_NX, 13 / ROOF_NX)


def roof_z(s):
    """z of the roof at s (0 front end, 1 back end): piecewise linear so that the rafters fall on S_RAFTERS."""
    knots_s = (0.0,) + S_RAFTERS + (1.0,)
    knots_z = (RZ,) + tuple(reversed(RAFTERS)) + (-RZ,)
    return float(np.interp(s, knots_s, knots_z))


def roof_pt(sgn, s, t):
    """A point of the roof slope on side sgn (-1 left, +1 right): s from the front end (0) to the back (1), t from the
    ridge (0) down to the eave edge (1)."""
    z = roof_z(s)
    f = bay(z)
    y = RIDGE - (RIDGE - EDGE_Y) * t - SLACK * math.sin(math.pi * t) - f * (SAG * math.sin(math.pi * t) + DROOP * t * t)
    y -= 0.035 * t * math.sin(z * 2.7 + sgn)
    return v3(sgn * RX * t, y, z)


def roof_y_end(xa):
    """Height of the cloth at the ends (on a rafter) at |x| = xa."""
    t = min(1.0, xa / RX)
    return RIDGE - (RIDGE - EDGE_Y) * t - SLACK * math.sin(math.pi * t)


def wall_top(z):
    """Height of the cloth's underside where it passes over the side wall (x = +-HW) at z."""
    t = HW / RX
    return roof_y_end(HW) - bay(z) * (SAG * math.sin(math.pi * t) + DROOP * t * t) - 0.05


def iron_band(bone, name, c, d, h=0.12):
    """A riveted iron band round a square post of side d at centre c."""
    add_cube(bone, name, c, EYE, (d + 0.05, h, d + 0.05), "cmd_band", stretch=True)


def heavy_post(frame, det, name, x, z, top, d=0.42, bands=(0.35, 1.7), cap=True):
    """A thick squared wooden post from the ground to `top`, riveted iron bands, a cap; one collision box."""
    beam(frame, name, (x, -0.05, z), (x, top, z), d, {"all": "wood", "+1": "end_grain", "-1": "end_grain"})
    for k, y in enumerate(bands):
        iron_band(det, "%s_band_%d" % (name, k), (x, y, z), d)
    if cap:
        add_cube(frame, name + "_cap", (x, top + 0.09, z), EYE, (d + 0.12, 0.18, d + 0.12), {"all": "wood_dark", "+2": "end_grain"})
        iron_band(det, name + "_collar", (x, top - 0.12, z), d, h=0.1)
    collide((x - d / 2, 0.0, z - d / 2, x + d / 2, min(top, 3.6), z + d / 2))


def anchor(bone, det, name, p, towards):
    """A grey anchor stone with an iron ring the guy rope is tied to; collides (low)."""
    p = v3(*p)
    box(bone, name, (p[0] - 0.26, 0.0, p[2] - 0.26), (p[0] + 0.26, 0.46, p[2] + 0.26), {"all": "cmd_stone", "+2": "cmd_stone"},
        solid=True, stretch=True)
    add_cube(det, name + "_ring", p + UP * 0.5, EYE, (0.2, 0.08, 0.2), "iron")


def guy(bone, det, name, top, ground):
    top, ground = v3(*top), v3(*ground)
    ml.rope(det, name, top, ground + UP * 0.5, d=0.11, sag=0.06, segs=2)
    anchor(bone, det, name + "_stone", ground, top)


def curtain(bone, name, x_post, sgn, w_top, w_tie, w_bot, z, region="cmd_curtain"):
    """A camo curtain tied back against the entrance post at x_post (sgn: +1 it reaches towards +x): hanging from the
    lintel, gathered at a rope tie half way down, flaring again at the floor, bulging a little out."""
    t_tie = 0.52

    def width(t):
        if t < t_tie:
            a = t / t_tie
            return w_top + (w_tie - w_top) * (a * a * (3 - 2 * a))
        a = (t - t_tie) / (1 - t_tie)
        return w_tie + (w_bot - w_tie) * (a * a * (3 - 2 * a))

    def P(s, t):
        y = (LINTEL - 0.02) * (1 - t) + 0.02 * t
        x = x_post + sgn * width(t) * s
        bulge = 0.07 * math.sin(math.pi * s) * max(0.0, 1 - abs(t - t_tie) * 1.6) + 0.04 * math.sin(s * math.pi * 3 + t * 2) * t
        return v3(x, y, z + max(0.0, bulge))
    loft(bone, name, P, 2, 8, region, th=0.03)
    tie = P(0.5, t_tie)
    add_cube(bone, name + "_tie", tie + Z * 0.02, EYE, (w_tie + 0.08, 0.07, 0.24), "rope")


def table(bone, det, name, cx, cz, lx, lz, h, top_region="plank", solid=True):
    """A heavy rustic table: plank top, four square legs, two stretchers; collides as one box."""
    add_cube(bone, name + "_top", (cx, h - 0.05, cz), EYE, (lx, 0.1, lz), {"all": "wood_dark", "+2": top_region, "-2": "plank_dark"},
             stretch=False, u_dir=X)
    for k, (sx, sz) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        x, z = cx + sx * (lx / 2 - 0.16), cz + sz * (lz / 2 - 0.14)
        beam(bone, "%s_leg_%d" % (name, k), (x, 0.0, z), (x, h - 0.1, z), 0.15, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    for k, sz in enumerate((-1, 1)):
        z = cz + sz * (lz / 2 - 0.14)
        beam(det, "%s_rail_%d" % (name, k), (cx - lx / 2 + 0.16, 0.28, z), (cx + lx / 2 - 0.16, 0.28, z), 0.09, "wood_dark")
    if solid:
        collide((cx - lx / 2, 0.0, cz - lz / 2, cx + lx / 2, h, cz + lz / 2))
    return h


def scroll(bone, name, a, b, r=0.07):
    beam(bone, name, a, b, r * 2, {"all": "cmd_parch", "+1": "cmd_parch", "-1": "cmd_parch"})


def quill(bone, name, foot, lean=(0.08, 0.0)):
    """A quill standing in an ink pot."""
    foot = v3(*foot)
    add_cube(bone, name + "_pot", foot + UP * 0.05, EYE, (0.1, 0.1, 0.1), {"all": "black_iron", "+2": "coal"})
    top = foot + v3(lean[0], 0.42, lean[1])
    c = (foot + UP * 0.08 + top) / 2
    for k, a in enumerate((0.3, 0.3 + math.pi / 2)):
        R = ml.ry(a)
        axes = np.column_stack([R[:, 0], tl.norm(top - foot - UP * 0.08), np.cross(R[:, 0], tl.norm(top - foot - UP * 0.08))])
        add_cube(bone, "%s_feather_%d" % (name, k), c, axes, (0.12, np.linalg.norm(top - foot) - 0.05, 0.004),
                 {"all": None, "+3": "cmd_quill", "-3": "cmd_quill"}, stretch=True, u_dir=axes[:, 0], v_dir=-axes[:, 1])


def crate_x(bone, name, foot, s, yaw=0.0, solid=True):
    """A crate marked with crossed swords (iron corners)."""
    return ml.crate(bone, name, foot, size=s, yaw=yaw, region="cmd_crate_x", top="crate_top", solid=solid)


def helmet(bone, name, foot, yaw=0.0):
    """A steel knight's great helm (a face plate with the eye slit and breathing holes, a rounded top, a neck rim)."""
    foot = v3(*foot)
    R = ml.ry(yaw)
    add_cube(bone, name, foot + UP * 0.2, R, (0.38, 0.32, 0.4), {"all": "steel", "+3": "cmd_helmet"}, stretch=True)
    add_cube(bone, name + "_oct", foot + UP * 0.2, R @ ml.ry(math.pi / 4), (0.37, 0.3, 0.37), "steel", stretch=True)
    for k, a in enumerate((0.0, math.pi / 4)):
        add_cube(bone, "%s_top_%d" % (name, k), foot + UP * 0.4, R @ ml.ry(a), (0.33, 0.1, 0.33), "steel", stretch=True)
        add_cube(bone, "%s_dome_%d" % (name, k), foot + UP * 0.47, R @ ml.ry(a), (0.24, 0.06, 0.24), "steel", stretch=True)
    add_cube(bone, name + "_crown", foot + UP * 0.51, R, (0.13, 0.04, 0.14), "steel", stretch=True)
    add_cube(bone, name + "_rim", foot + UP * 0.025, R, (0.42, 0.05, 0.44), "black_iron", stretch=True)
    add_cube(bone, name + "_ridge", foot + UP * 0.27 + R @ v3(0, 0, 0.205), R, (0.04, 0.42, 0.03), "steel")


def chest(bone, det, name, foot, w=1.0, d=0.62, h=0.72, yaw=0.0):
    """A banded wooden chest with a slightly domed lid; collides."""
    foot = v3(*foot)
    R = ml.ry(yaw)
    ml.rbox(bone, name, foot, (w, h * 0.68, d), yaw, {"all": "cmd_chest", "+2": "plank_dark", "-2": "plank_dark"}, stretch=True)
    ml.rbox(bone, name + "_lid", foot + UP * h * 0.68, (w + 0.04, h * 0.22, d + 0.04), yaw, {"all": "wood_dark", "+3": "cmd_chest"},
            stretch=True)
    ml.rbox(bone, name + "_dome", foot + UP * h * 0.9, (w * 0.96, h * 0.1, d * 0.7), yaw, "wood_dark", stretch=True)
    add_cube(det, name + "_lock", foot + UP * h * 0.66 + R @ v3(0, 0, d / 2 + 0.03), R, (0.12, 0.16, 0.04), "gold")
    collide((foot[0] - w / 2, 0.0, foot[2] - d / 2, foot[0] + w / 2, h, foot[2] + d / 2))


def leaning_wheel(bone, name, center, radius=0.55, lean=0.25, segs=10, spokes=6):
    """A cart wheel standing in the y-z plane, leaning by `lean` radians towards -x (against a wall); collides."""
    c = v3(*center)
    e1 = v3(0, 0, 1)
    e2 = v3(-math.sin(lean), math.cos(lean), 0)
    axle = np.cross(e1, e2)
    rm = radius - 0.07
    pts = [c + (e1 * math.cos(2 * math.pi * k / segs) + e2 * math.sin(2 * math.pi * k / segs)) * rm for k in range(segs)]
    for k in range(segs):
        beam(bone, "%s_rim_%d" % (name, k), pts[k], pts[(k + 1) % segs], 0.14, {"all": "wood_dark"}, width=0.13, up=axle,
             extend=0.07 * math.tan(math.pi / segs) + 0.03)
    for k in range(spokes):
        a = 2 * math.pi * (k + 0.5) / spokes
        dr = e1 * math.cos(a) + e2 * math.sin(a)
        beam(bone, "%s_spoke_%d" % (name, k), c + dr * 0.08, c + dr * (radius - 0.1), 0.06, "wood", up=axle)
    add_cube(bone, name + "_hub", c, np.column_stack([e1, e2, axle]), (0.2, 0.2, 0.24), {"all": "wood_dark", "+3": "iron", "-3": "iron"})
    collide((c[0] - 0.22, 0.0, c[2] - radius * 0.8, c[0] + 0.16, c[1] + radius * 0.9, c[2] + radius * 0.8))


def build(atlas):
    root = ml.Bone(NAME)
    frame = ml.Bone("frame", parent=root)
    cloth = ml.Bone("canvas", parent=root)
    furn = ml.Bone("furniture", parent=root)
    det = ml.Bone("detail", parent=root)

    # ---- atlas regions of this tent
    atlas.add("cmd_roof", 256, 128, pc.roof_painter(1241, S_RAFTERS, end_band=28, eave_band=12))
    atlas.add("cmd_carpet", 96, 128, pc.carpet_painter(1242))
    atlas.add("cmd_banner", 64, 112, pc.banner_painter(1243))
    atlas.add("cmd_curtain", 48, 96, pc.curtain_painter(1244, beige=0.06))
    atlas.add("cmd_curtain_d", 48, 96, pc.curtain_painter(1260, beige=-0.1))
    atlas.add("cmd_wall", 256, 64, pc.wall_painter(1245, folds=14))
    atlas.add("cmd_gable", 160, 64, pc.gable_painter(1246, HW, EDGE_Y, RIDGE, roof_y_end))
    atlas.add("cmd_map", 64, 48, pc.map_painter(1247))
    atlas.add("cmd_flag", 64, 32, pc.flag_painter(1248))
    atlas.add("cmd_val_side", 256, 24, pc.dag_painter(1249, 26, beige=-0.18))
    atlas.add("cmd_val_end", 192, 24, pc.dag_painter(1250, 20, beige=0.06))
    atlas.add("cmd_barge", 128, 24, pc.dag_painter(1251, 9, solid=0.6, beige=0.1))
    for nm, w, h, painter in (("cmd_crate_x", 32, 32, pc.crate_x_painter(1252)), ("cmd_helmet", 32, 32, pc.helmet_painter(1253)),
                              ("cmd_books", 32, 32, pc.books_painter(1254)), ("cmd_chest", 32, 32, pc.chest_painter(1255)),
                              ("cmd_stone", 32, 32, pc.stone_painter(1256)), ("cmd_band", 32, 16, pc.band_painter(1257)),
                              ("cmd_parch", 16, 16, pc.parch_painter(1258)), ("cmd_quill", 16, 16, pc.quill_painter(1259))):
        atlas.add(nm, w, h, painter)

    # ---- the roof: two sagging slopes, camo bands painted at the ends and the eave
    for sgn, nm in ((-1, "l"), (1, "r")):
        loft(cloth, "roof_" + nm, lambda s, t, sgn=sgn: roof_pt(sgn, s, t), ROOF_NX, 5, "cmd_roof", th=0.04, overlap=0.04)
        # the dagged valance along the eave, following the droop
        def V(s, t, sgn=sgn):
            return roof_pt(sgn, s, 1.0) + UP * 0.03 - UP * (0.55 * t) + X * (sgn * 0.05 * t)
        loft(cloth, "valance_" + nm, V, ROOF_NX, 1, "cmd_val_side", th=0.025)
        # the dagged camo bargeboards along the front and back roof edges
        for se, end in ((0.0, "f"), (1.0, "b")):
            o = Z if se == 0.0 else -Z

            def B(s, t, sgn=sgn, se=se, o=o):
                return roof_pt(sgn, se, s) + UP * 0.04 - UP * (0.72 * t) + o * 0.035
            loft(cloth, "barge_%s_%s" % (end, nm), B, 5, 1, "cmd_barge", th=0.025)

    # ---- the gable ends (cut out under the roof) and the front / back valances at the eave line
    gh = RIDGE - EDGE_Y
    for sz, nm in ((1, "front"), (-1, "back")):
        ml.plate(cloth, "gable_" + nm, (0, EDGE_Y + gh / 2, sz * (HD + 0.03)), 2 * HW, gh, "cmd_gable", normal=(0, 0, sz), th=0.02)

        def E(s, t, sz=sz):
            x = -HW - 0.2 + (2 * HW + 0.4) * s
            if sz > 0:   # the front: hanging from the front beam over the entrance
                return v3(x, BEAM_Y - 0.06 - VAL_DROP * t, HD + 0.35 + 0.04 * t)
            top = min(EDGE_Y + 0.42, roof_y_end(abs(x)) - 0.03)
            return v3(x, top - 0.55 * t, -(HD + 0.28 + 0.04 * t))
        loft(cloth, "valance_" + nm, E, 6, 1, "cmd_val_end", th=0.025)

    # ---- canvas walls with soft folds (the entrance left open in the front wall)
    for sgn, nm in ((-1, "l"), (1, "r")):
        def W(s, t, sgn=sgn):
            z = HD - 2 * HD * s
            y = wall_top(z) * (1 - t)
            x = sgn * (HW - 0.02 + 0.06 * math.sin(z * 2.4 + sgn) * (0.35 + 0.65 * t) + 0.05 * t)
            return v3(x, y, z)
        loft(cloth, "wall_" + nm, W, 12, 2, "cmd_wall", th=0.035)
        collide((sgn * HW - 0.12, 0.0, -HD, sgn * HW + 0.12, EAVE, HD))

    def WB(s, t):
        x = -HW + 2 * HW * s
        return v3(x, EAVE * (1 - t), -HD - 0.02 - 0.06 * math.sin(x * 2.2) * (0.35 + 0.65 * t) - 0.04 * t)
    loft(cloth, "wall_back", WB, 8, 2, "cmd_wall", th=0.035)
    collide((-HW, 0.0, -HD - 0.12, HW, EAVE, -HD + 0.12))
    for sgn, nm in ((-1, "l"), (1, "r")):
        def WF(s, t, sgn=sgn):
            x = sgn * (DOOR + (HW - DOOR) * s)
            return v3(x, EAVE * (1 - t), HD + 0.02 + 0.05 * math.sin(x * 2.6) * (0.35 + 0.65 * t) + 0.03 * t)
        loft(cloth, "wall_front_" + nm, WF, 4, 2, "cmd_wall", th=0.035)
        collide((min(sgn * (DOOR + 0.16), sgn * HW), 0.0, HD - 0.12, max(sgn * (DOOR + 0.16), sgn * HW), EAVE, HD + 0.12))
    ml.plate(cloth, "wall_lintel", (0, (LINTEL + EAVE) / 2, HD + 0.01), 2 * DOOR, EAVE - LINTEL + 0.05, "cmd_wall", normal=(0, 0, 1), th=0.03)

    # ---- posts: corners, sides, entrance; the front beam with knee braces; the ridge pole, the flag pole
    for sx in (-1, 1):
        for sz in (-1, 1):
            heavy_post(frame, det, "post_%s%s" % ("r" if sx > 0 else "l", "f" if sz > 0 else "b"), sx * HW, sz * HD, POST_TOP, d=0.5,
                       bands=(0.35, 1.8))
        for k, z in enumerate((-2.0, 2.0)):   # under the eave (the cloth hides their tops)
            heavy_post(frame, det, "post_side_%s_%d" % ("r" if sx > 0 else "l", k), sx * HW, z, roof_y_end(HW) - 0.14, d=0.36, cap=False)
        heavy_post(frame, det, "post_door_" + ("r" if sx > 0 else "l"), sx * DOOR, HD + 0.08, BEAM_Y - 0.1, d=0.4, bands=(0.35, 1.7), cap=False)
    beam(frame, "front_beam", (-HW - 0.3, BEAM_Y, HD + 0.22), (HW + 0.3, BEAM_Y, HD + 0.22), 0.22,
         {"all": "wood", "+1": "end_grain", "-1": "end_grain"}, width=0.2)
    for k, x in enumerate((-HW, -DOOR, DOOR, HW)):
        add_cube(det, "beam_plate_%d" % k, (x, BEAM_Y, HD + 0.39), EYE, (0.42, 0.3, 0.03), "cmd_band", stretch=True)
    for sx in (-1, 1):
        beam(frame, "knee_%d" % ((sx + 1) // 2), (sx * HW, BEAM_Y - 0.75, HD + 0.2), (sx * (HW - 0.75), BEAM_Y - 0.05, HD + 0.2), 0.12,
             "wood_dark", extend=0.04)
    beam(frame, "back_beam", (-HW, EAVE - 0.3, -HD - 0.15), (HW, EAVE - 0.3, -HD - 0.15), 0.2, "wood", width=0.18)
    beam(frame, "ridge_pole", (0, RIDGE - 0.14, -RZ - 0.25), (0, RIDGE - 0.14, RZ + 0.25), 0.2,
         {"all": "wood", "+1": "end_grain", "-1": "end_grain"})
    for k, z in enumerate((-RZ - 0.12, RZ + 0.12)):
        iron_band(det, "ridge_band_%d" % k, (0, RIDGE - 0.14, z), 0.2, h=0.1)
    for k, z in enumerate(RAFTERS):
        for sgn in (-1, 1):
            t = HW / RX
            beam(frame, "rafter_%d_%d" % (k, (sgn + 1) // 2), (0, RIDGE - 0.3, z), (sgn * HW, roof_y_end(HW) - 0.3, z), 0.12, "wood_dark",
                 extend=0.05)
    for k, z in enumerate((-2.0, 2.0)):   # king posts poking through the ridge over the middle rafters
        beam(frame, "king_post_%d" % k, (0, RIDGE - 0.4, z), (0, RIDGE + 0.6, z), 0.26, {"all": "wood", "+1": "end_grain", "-1": "end_grain"})
        add_cube(frame, "king_post_cap_%d" % k, (0, RIDGE + 0.68, z), EYE, (0.36, 0.16, 0.36), {"all": "wood_dark", "+2": "end_grain"})
        iron_band(det, "king_post_band_%d" % k, (0, RIDGE + 0.32, z), 0.26, h=0.1)
    # the back post under the ridge, crossed poles over the back gable
    beam(frame, "post_back", (0, -0.05, -HD - 0.12), (0, RIDGE + 0.1, -HD - 0.12), 0.3, {"all": "wood", "+1": "end_grain", "-1": "end_grain"})
    collide((-0.15, 0.0, -HD - 0.27, 0.15, 3.6, -HD + 0.03))
    for k, sx in enumerate((-1, 1)):
        beam(frame, "cross_%d" % k, (sx * 0.62, RIDGE - 0.55, -RZ - 0.05), (-sx * 0.42, RIDGE + 0.72, -RZ - 0.05), 0.15, "wood",
             extend=0.04)
    iron_band(det, "cross_band", (0, RIDGE + 0.15, -RZ - 0.05), 0.2, h=0.12)
    # the flag pole on the front gable (on the front beam), the flag
    fz = HD + 0.12
    beam(frame, "flag_pole", (0, BEAM_Y + 0.1, fz), (0, RIDGE + 1.75, fz), 0.22, {"all": "wood", "+1": "end_grain", "-1": "end_grain"})
    for k, y in enumerate((RIDGE - 0.3, RIDGE + 0.4, RIDGE + 1.0)):
        iron_band(det, "flag_band_%d" % k, (0, y, fz), 0.22, h=0.11)
    add_cube(frame, "flag_knob", (0, RIDGE + 1.85, fz), EYE, (0.3, 0.2, 0.3), {"all": "wood_dark", "+2": "end_grain"})

    def FL(s, t):
        return v3(0.12 + 2.3 * s, RIDGE + 1.65 - 0.95 * t - 0.32 * s * s, fz + 0.18 * math.sin(math.pi * 1.6 * s) * (0.4 + s))
    loft(cloth, "flag", FL, 4, 1, "cmd_flag", th=0.02)

    # ---- banners: the big one on the gable, two on the front wall
    ml.banner(cloth, "banner_gable", (0, RIDGE - 0.78, RZ + 0.12), 1.6, 2.7, normal=(0, 0, 1), region="cmd_banner", rod=True, wave=0.05)
    for sx in (-1, 1):
        bx = sx * (DOOR + HW) / 2
        ml.banner(cloth, "banner_wall_%d" % ((sx + 1) // 2), (bx, LINTEL + 0.14, HD + 0.42), 1.12, 2.0, normal=(0, 0, 1),
                  region="cmd_banner", rod=True, wave=0.04)

    # ---- lanterns hanging left and right inside the entrance, guy ropes to anchor stones
    for sx in (-1, 1):
        ml.lantern(det, "lantern_door_%d" % ((sx + 1) // 2), (sx * (DOOR - 0.5), 2.72, HD + 0.16), size=0.34, chain_to=(sx * (DOOR - 0.5), LINTEL + 0.25, HD + 0.16))
    for sx in (-1, 1):
        for sz in (-1, 1):
            guy(frame, det, "guy_%d%d" % ((sx + 1) // 2, (sz + 1) // 2), (sx * HW, POST_TOP - 0.25, sz * HD),
                (sx * (HW + 1.2), 0.0, sz * (HD + 1.2)))
        for k, z in enumerate((-2.0, 2.0)):
            guy(frame, det, "guy_side_%d%d" % ((sx + 1) // 2, k), (sx * HW, roof_y_end(HW) - 0.32, z), (sx * (HW + 1.25), 0.0, z))

    # ---- curtains tied back at the entrance
    curtain(cloth, "curtain_l", -DOOR + 0.12, 1, 1.35, 0.45, 0.95, HD - 0.04, region="cmd_curtain_d")
    curtain(cloth, "curtain_r", DOOR - 0.12, -1, 1.5, 0.5, 1.05, HD - 0.04)

    # ---- inside: the red carpet, the strategy table and what lies on it, the hanging lantern, a weapon rack
    ml.rug(furn, "carpet", -1.45, 1.85, 3.0, 7.5, y=0.0, region="cmd_carpet")
    cx, cz, lx, lz, th = TABLE
    top = table(furn, det, "strategy_table", cx, cz, lx, lz, th)
    ml.plate(furn, "map_big", (cx - 0.15, top + 0.012, cz + 0.05), 1.7, 1.05, "cmd_map", normal=(0, 1, 0), up=(0, 0, -1), th=0.012)
    ml.plate(furn, "map_small", (cx + 0.95, top + 0.03, cz + 0.2), 0.7, 0.55, "cmd_parch", normal=(0, 1, 0), up=(0.35, 0, -1), th=0.01)
    scroll(det, "scroll_a", (cx - 1.35, top + 0.07, cz - 0.55), (cx - 0.75, top + 0.07, cz - 0.35))
    scroll(det, "scroll_b", (cx + 0.7, top + 0.07, cz - 0.6), (cx + 1.3, top + 0.07, cz - 0.5), r=0.06)
    scroll(det, "scroll_c", (cx - 1.3, top + 0.07, cz + 0.55), (cx - 1.25, top + 0.07, cz - 0.05), r=0.055)
    quill(det, "quill_in", (cx + 0.55, top, cz + 0.55))
    for k, (x, z, reg) in enumerate(((cx - 0.4, cz - 0.1, "cloth_red"), (cx + 0.1, cz + 0.25, "cloth_blue"), (cx - 0.7, cz + 0.3, "cloth_red"))):
        add_cube(det, "marker_%d" % k, (x, top + 0.06, z), EYE, (0.07, 0.1, 0.07), reg)
    ml.banner(furn, "banner_back", (0.9, 2.95, -HD + 0.16), 1.0, 1.75, normal=(0, 0, 1), region="cmd_banner", rod=True, wave=0.03)
    ml.lantern(det, "lantern_ridge", (cx, 3.55, cz), size=0.34, chain_to=(cx, RIDGE - 0.24, cz))
    ml.weapon_rack(furn, "rack", (HW - 0.45, 0.0, -0.4), (HW - 0.45, 0.0, 1.0), h=1.7, normal=(-1, 0, 0),
                   items=("sword", "spear", "sword", "axe"), detail=det)

    # ---- outside, front left: the table with maps, scrolls, quills and a lantern on a crate; crates and the helmet
    ox, oz, olx, olz, oth = OUT_TABLE
    otop = table(furn, det, "camp_table", ox, oz, olx, olz, oth)
    ml.plate(furn, "map_out", (ox + 0.2, otop + 0.012, oz + 0.02), 1.15, 0.7, "cmd_map", normal=(0, 1, 0), up=(-0.12, 0, -1), th=0.012)
    scroll(det, "scroll_out_a", (ox + 0.3, otop + 0.07, oz - 0.3), (ox + 0.85, otop + 0.07, oz - 0.22))
    scroll(det, "scroll_out_b", (ox + 0.45, otop + 0.065, oz + 0.3), (ox + 0.9, otop + 0.065, oz + 0.12), r=0.06)
    quill(det, "quill_out_a", (ox - 0.15, otop, oz - 0.18), lean=(0.1, 0.05))
    quill(det, "quill_out_b", (ox + 0.62, otop, oz - 0.05), lean=(-0.06, 0.08))
    ml.crate(furn, "lamp_crate", (ox - 0.65, otop, oz - 0.05), size=0.34, solid=False)
    ml.lantern(det, "lantern_table", (ox - 0.65, otop + 0.34 + 0.21, oz - 0.05), size=0.3)
    crate_x(furn, "crate_stack_a", (-4.85, 0.0, 6.55), 0.9, yaw=0.1)
    crate_x(furn, "crate_stack_b", (-3.85, 0.0, 6.8), 0.85, yaw=-0.06)
    crate_x(furn, "crate_stack_c", (-4.8, 0.9, 6.5), 0.8, yaw=0.18, solid=False)
    collide((-5.3, 0.9, 6.05, -4.3, 1.7, 6.95))
    helmet(det, "helmet", (-3.82, 0.85, 6.85), yaw=-0.35)
    ml.crate(furn, "crate_small_a", (-4.35, 0.0, 7.75), size=0.6, yaw=0.12)
    crate_x(furn, "crate_small_b", (-3.4, 0.0, 7.75), 0.55, yaw=-0.2)

    # ---- outside, right: a chest, crates, a cart wheel leaning on the wall
    chest(furn, det, "chest", (2.75, 0.0, 6.62), yaw=-0.05)
    ml.crate(furn, "crate_right_a", (3.85, 0.0, 6.7), size=0.85, yaw=0.04)
    crate_x(furn, "crate_right_b", (4.6, 0.0, 7.3), 0.6, yaw=-0.15)
    leaning_wheel(furn, "wheel", (5.3, 0.55, 6.6), radius=0.55, lean=0.22)

    # ---- the decoration mods' furniture (stand-ins when a mod is missing)
    decor = ml.Decor()
    decor.block("farmhouse_decorations:pile_of_books", cx + 1.15, top, cz - 0.15, facing="neg_x", fallback="cmd_books", solid=False)
    decor.block("farmhouse_decorations:kerosene_lantern", cx - 1.05, top, cz + 0.1, facing="front", glow=True, alt="minecraft:lantern",
                fallback="lantern", solid=False)
    decor.block("furnish:spruce_chair", cx, 0.0, cz - 1.25, facing="front", fallback="crate", solid=False)
    for k, x in enumerate((cx - 1.95, cx + 1.95)):
        decor.block("furnish:spruce_stool", x, 0.0, cz + 0.1, facing="pos_x" if k == 0 else "neg_x", fallback="crate", solid=False)
    for k, x in enumerate((-2.7, -1.7)):
        decor.block("farmhouse_decorations:tall_bookshelf", x, 0.0, -HD + 0.62, facing="front", alt="minecraft:bookshelf", fallback="cmd_books")
    for k, (x, y, z) in enumerate(((2.3, 0.0, -5.25), (3.35, 0.0, -5.25), (3.35, 1.0, -5.25), (-4.2, 0.0, -3.4))):
        decor.block("furnish:spruce_crate", x, y, z, facing="front" if k % 2 == 0 else "neg_x", scale=0.9 if k == 2 else 1.0,
                    alt="minecraft:barrel", fallback="crate", solid=y == 0.0)
    return root, decor


def main():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="green")
    root, decor = build(atlas)
    ml.export(root, NAME, atlas, decor=decor, icon=pc.icon, visible_box=(14, 9, 0), light=13)


if __name__ == "__main__":
    main()
