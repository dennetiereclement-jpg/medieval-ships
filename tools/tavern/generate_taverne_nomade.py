#!/usr/bin/env python3
"""taverne_nomade — Taverne nomade / Nomad Tavern (reference: scratchpad/ref/taverne_nomade_ref.png).

A big medieval wagon turned into a tavern: a dark timber-framed body on four big spoked iron-tyred wheels, a ROUNDED
canvas roof (beige patched hood at the left end, wine red over the middle, beige again at the right end) with ivy
spilling over it, a rack with a chest and a crate on top, a stone chimney; at the left end a porch with steps up to a
door with a lit lattice window, a lantern and a small arched window, a mug banner hanging under the hood; along the
front a big open COUNTER (shelves of bottles, kegs with taps, mugs on the board, two lanterns) between two mug
banners, three bar stools on a ledge; a striped dagged awning stretched from the right end of the wagon to two posts;
the tall sign post with its hanging mug sign; in front a terrace on stone pavers: four square tables with mugs,
bottles and lanterns, wooden stools around them (seats), a red patterned rug, barrels, a sack, crates; at the right
a camp fire in a stone ring under a trestle frame with a black cauldron hanging on a chain.

Usage:  python3 tools/tavern/generate_taverne_nomade.py   (TAVERN_OUT=<file.bbmodel>: write only the model there)
Writes: blockbench/taverne_nomade.bbmodel, models/entity/taverne_nomade.bbmodel, textures/entity/taverne_nomade.png,
        textures/item/taverne_nomade.png, interiors/taverne_nomade_decor.json, carts/taverne_nomade.json (model,
        texture, decor, extent, colliders, particles, seats).
Prop-local coordinates: y up, +z = front (the terrace, towards the player who placed it), the anchor block at (0, 0, 0).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tavernlib as tv  # noqa: E402

v3, UP, X, Z, EYE = tv.v3, tv.UP, tv.X, tv.Z, tv.EYE
add_cube, beam, box, collide = tv.add_cube, tv.beam, tv.box, tv.collide
cl, ml, wl, tl = tv.cl, tv.ml, tv.wl, tv.tl

NAME = "taverne_nomade"

# the wagon: its length along x, its front long side (the counter) facing +z
WX0, WX1 = -5.0, 2.2          # end walls (left end: the door and porch; right end: the awning)
WZ0, WZ1 = -4.0, -1.0         # back and front walls
WZC, HW = (WZ0 + WZ1) / 2, (WZ1 - WZ0) / 2
BED_Y = 1.05                  # floor of the wagon
EAVE = 3.05                   # top of the walls
WALL = 0.08
AXLES = (-3.75, 1.05)         # wheel centres (x)
WHEEL_R = 0.95
WHEEL_Z = (WZ1 + 0.2, WZ0 - 0.2)
CX0, CX1 = -2.95, 0.45        # the counter opening (x)
CTR_Y = 2.05                  # counter top
OPEN_TOP = 2.9                # top of the counter opening
NICHE_Z = WZ1 - 0.95          # back of the bar niche
# the canvas roof
RY0 = EAVE - 0.06
RHW = HW + 0.17
RISE = 1.5
FLAT = 0.2
HOOD_X, HOOD_FLARE = -5.12, 0.66   # left hood: the canvas starts at x = HOOD_X at the eaves and flares out by HOOD_FLARE at the top
ROOF_SECTIONS = ((HOOD_X, -3.3, "tv_canvas_beige", 3), (-3.3, 1.05, "tv_canvas_red", 5), (1.05, WX1 + 0.14, "tv_canvas_beige", 2))
HOOPS = (WX0, -3.3, -1.1, 1.05, WX1)
# the porch and steps at the left end
PORCH_X = WX0 - 0.75
STEP_Z0, STEP_Z1 = -3.32, -2.18
DOOR_Z, DOOR_W, DOOR_H = -2.75, 0.85, 1.75
# the awning corners (wagon side A back, B front; posts C front, D back)
AW_A = v3(WX1 + 0.05, EAVE - 0.04, WZ0 + 0.06)
AW_B = v3(WX1 + 0.08, EAVE - 0.05, WZ1 + 0.36)
AW_C = v3(4.3, 2.5, -0.3)
AW_D = v3(4.6, 2.5, -3.55)
SIGN_POST = (4.3, -0.3)
FIRE = (5.6, 0.95)


def arch(s):
    """(z, y) of the roof arch at s in [0, 1] (0 = front eave, 1 = back eave)."""
    a, y = cl.arch(RHW, RISE, RY0, min(1.0, max(0.0, s)), FLAT)
    return WZC + a, y


def roof_point(s, x, sag_x=True):
    z, y = arch(s)
    h = (y - RY0) / RISE
    if sag_x:
        for a, b in zip(HOOPS[:-1], HOOPS[1:]):
            if a <= x <= b:
                f = (x - a) / (b - a)
                k = 1.0 - 0.035 * math.sin(math.pi * f) * h
                z = WZC + (z - WZC) * k
                y = RY0 + (y - RY0) * k
    return v3(x, y, z)


def roof_x(x, s, t, xa, xb):
    """The x of the canvas: the left hood flares out at the top, the right end a little."""
    h = (arch(s)[1] - RY0) / RISE
    if xa <= HOOD_X + 1e-6:
        return x - HOOD_FLARE * h ** 1.3 * (1 - t) ** 3
    if xb >= WX1:
        return x + 0.16 * h ** 1.3 * t ** 3
    return x


def roof_P(xa, xb):
    def P(s, t):
        x = xa + (xb - xa) * t
        p = roof_point(s, x)
        p[0] = roof_x(x, s, t, xa, xb)
        return p
    return P


def outward(p):
    """Unit normal of the roof at p (radial from the arch's base line)."""
    d = v3(0, (p[1] - RY0) * (RHW / RISE), p[2] - WZC)
    return tv.norm(d)


# ---------------------------------------------------------------- running gear and floor
def running_gear(root, det):
    g = tv.Bone("gear", parent=root)
    # the floor: planks along x, sills and cross members under it
    tl.platform(g, "floor", WX0 - 0.04, WX1 + 0.04, WZ0 - 0.04, WZ1 + 0.04, BED_Y, th=0.1, plank_w=0.5, along="x", region="plank_dark",
                solid=False, joists=False)
    for k, z in enumerate((WZ1 - 0.2, WZ0 + 0.2)):
        add_cube(g, "sill_%d" % k, ((WX0 + WX1) / 2, BED_Y - 0.19, z), EYE, (WX1 - WX0 + 0.1, 0.18, 0.18),
                 {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    # the heavy outer rave along the front and back, bolted
    for k, (z, s) in enumerate(((WZ1 + 0.05, 1), (WZ0 - 0.05, -1))):
        add_cube(g, "rave_%d" % k, ((WX0 + WX1) / 2, BED_Y - 0.1, z), EYE, (WX1 - WX0 + 0.2, 0.2, 0.12),
                 {"all": "tv_timber", "+1": "end_grain", "-1": "end_grain"}, u_dir=X)
        for j in range(8):
            x = WX0 + 0.3 + j * (WX1 - WX0 - 0.6) / 7
            tv.bolt(det, "rave_bolt_%d_%d" % (k, j), (x, BED_Y - 0.1, z + s * 0.06), (0, 0, s), s=0.07)
    for k, x in enumerate((WX0 + 0.1, -2.4, -0.6, WX1 - 0.1)):
        add_cube(g, "cross_%d" % k, (x, BED_Y - 0.16, WZC), EYE, (0.14, 0.12, WZ1 - WZ0 + 0.2), "wood_dark")
    # wheels, axles, bolsters
    for k, x in enumerate(AXLES):
        for j, z in enumerate(WHEEL_Z):
            tv.wheel_z(g, "wheel_%d_%d" % (k, j), (x, WHEEL_R, z), WHEEL_R, width=0.22, spokes=10, segs=16, detail=det,
                       region="wood_dark", spoke_region="wood")
        beam(g, "axle_%d" % k, (x, WHEEL_R, WHEEL_Z[1] - 0.12), (x, WHEEL_R, WHEEL_Z[0] + 0.12), 0.14,
             {"all": "wood_dark", "+1": "iron", "-1": "iron"}, up=UP)
        add_cube(g, "bolster_%d" % k, (x, (WHEEL_R + 0.07 + BED_Y - 0.28) / 2, WZC), EYE,
                 (0.24, max(0.06, BED_Y - 0.28 - WHEEL_R - 0.07), WZ1 - WZ0 - 0.1), "wood_dark")
        for j, z in enumerate((WZ1 - 0.25, WZ0 + 0.25)):
            add_cube(det, "axle_strap_%d_%d" % (k, j), (x, WHEEL_R + 0.05, z), EYE, (0.18, 0.2, 0.05), "iron")
    add_cube(g, "reach", ((AXLES[0] + AXLES[1]) / 2, BED_Y - 0.33, WZC), EYE, (AXLES[1] - AXLES[0] + 0.3, 0.12, 0.16), "wood_dark")
    # a chest slung under the floor between the axles (the picture's dark underbody)
    add_cube(g, "under_box", (-1.3, BED_Y - 0.48, WZC + 0.1), EYE, (2.6, 0.36, 1.9), {"all": "plank_dark", "+3": "tv_planks"}, u_dir=X)
    collide((WX0, 0.0, WZ0, WX1, BED_Y, WZ1))


# ---------------------------------------------------------------- body
def wall_x(bone, name, x0, x1, y0, y1, z, region="tv_planks"):
    """A plank wall along x at z, from x0 to x1, y0 to y1 (planks horizontal)."""
    if x1 - x0 < 0.01 or y1 - y0 < 0.01:
        return
    add_cube(bone, name, ((x0 + x1) / 2, (y0 + y1) / 2, z), EYE, (x1 - x0, y1 - y0, WALL), region, u_dir=X, v_dir=-UP)


def wall_z(bone, name, z0, z1, y0, y1, x, region="tv_planks"):
    if z1 - z0 < 0.01 or y1 - y0 < 0.01:
        return
    add_cube(bone, name, (x, (y0 + y1) / 2, (z0 + z1) / 2), EYE, (WALL, y1 - y0, z1 - z0), region, u_dir=Z, v_dir=-UP)


def timber(bone, name, p0, p1, d=0.17, region="tv_timber"):
    return beam(bone, name, p0, p1, d, {"all": region, "+1": "end_grain", "-1": "end_grain"}, up=UP if abs(p1[1] - p0[1]) < 1e-6 else X)


def body(root, det):
    b = tv.Bone("body", parent=root)
    # walls: back, front (with the counter opening), the two ends (door on the left)
    wall_x(b, "wall_back", WX0, WX1, BED_Y, EAVE, WZ0)
    wall_x(b, "wall_front_l", WX0, CX0, BED_Y, EAVE, WZ1)
    wall_x(b, "wall_front_r", CX1, WX1, BED_Y, EAVE, WZ1)
    wall_x(b, "wall_front_low", CX0, CX1, BED_Y, CTR_Y - 0.09, WZ1)
    wall_x(b, "wall_front_top", CX0, CX1, OPEN_TOP, EAVE, WZ1)
    dz0, dz1 = DOOR_Z - DOOR_W / 2, DOOR_Z + DOOR_W / 2
    wall_z(b, "wall_left_a", WZ0, dz0, BED_Y, EAVE, WX0)
    wall_z(b, "wall_left_b", dz1, WZ1, BED_Y, EAVE, WX0)
    wall_z(b, "wall_left_top", dz0, dz1, BED_Y + DOOR_H, EAVE, WX0)
    wall_z(b, "wall_right", WZ0, WZ1, BED_Y, EAVE, WX1)
    # gables: boards filling the arch above the eaves at both ends
    for e, x in (("l", WX0), ("r", WX1)):
        for k in range(5):
            y = EAVE + 0.06 + k * 0.23
            # half width of the arch at height y
            best = 0.0
            for i in range(41):
                z, yy = arch(i / 80)
                if yy >= y + 0.115:
                    best = z - WZC
                    break
            if best <= 0.05:
                continue
            add_cube(b, "gable_%s_%d" % (e, k), (x, y, WZC), EYE, (WALL, 0.24, 2 * best), "tv_planks", u_dir=Z)
    # the timber frame: corner posts, jambs, eave plates, sill rails, braces, iron bolts
    posts_front = (WX0, -4.05, CX0, CX1, WX1)
    posts_back = (WX0, -3.2, -1.4, 0.4, WX1)
    for k, x in enumerate(posts_front):
        timber(b, "post_f_%d" % k, (x, BED_Y - 0.2, WZ1 + 0.06), (x, EAVE + 0.04, WZ1 + 0.06))
        for j, y in enumerate((BED_Y + 0.25, CTR_Y - 0.25, EAVE - 0.2)):
            tv.bolt(det, "post_f_bolt_%d_%d" % (k, j), (x, y, WZ1 + 0.145), (0, 0, 1), s=0.08)
    for k, x in enumerate(posts_back):
        timber(b, "post_b_%d" % k, (x, BED_Y - 0.2, WZ0 - 0.06), (x, EAVE + 0.04, WZ0 - 0.06))
    for k, z in enumerate((WZ0 + 0.75, WZ1 - 0.75)):
        timber(b, "post_r_%d" % k, (WX1 + 0.06, BED_Y - 0.2, z), (WX1 + 0.06, EAVE + 0.04, z))
    for k, z in enumerate((DOOR_Z - DOOR_W / 2 - 0.09, DOOR_Z + DOOR_W / 2 + 0.09, WZ1 - 0.1, WZ0 + 0.1)):
        timber(b, "post_l_%d" % k, (WX0 - 0.06, BED_Y - 0.2, z), (WX0 - 0.06, EAVE + 0.04, z))
    timber(b, "door_lintel", (WX0 - 0.07, BED_Y + DOOR_H + 0.08, DOOR_Z - DOOR_W / 2 - 0.15), (WX0 - 0.07, BED_Y + DOOR_H + 0.08, DOOR_Z + DOOR_W / 2 + 0.15), d=0.16)
    for k, (z, s) in enumerate(((WZ1 + 0.08, 1), (WZ0 - 0.08, -1))):
        timber(b, "eave_plate_%d" % k, (WX0 - 0.12, EAVE - 0.08, z), (WX1 + 0.12, EAVE - 0.08, z), d=0.18)
        timber(b, "mid_rail_%d" % k, (WX0, BED_Y + 0.62, z - s * 0.01), (WX1, BED_Y + 0.62, z - s * 0.01), d=0.11)
    for k, x in enumerate((WX0 - 0.08, WX1 + 0.08)):
        timber(b, "end_plate_%d" % k, (x, EAVE - 0.08, WZ0 - 0.12), (x, EAVE - 0.08, WZ1 + 0.12), d=0.18)
    # carved brackets under the front eave (on the posts), as in the picture
    for k, x in enumerate(posts_front):
        for s in ((1,) if x == WX0 else (-1,) if x == WX1 else (1, -1)):
            if x in (CX0, CX1) and s == (1 if x == CX0 else -1):
                continue
            beam(det, "bracket_%d_%d" % (k, s), (x + s * 0.05, EAVE - 0.55, WZ1 + 0.12), (x + s * 0.42, EAVE - 0.15, WZ1 + 0.12), 0.08,
                 "tv_timber", width=0.08, up=Z)
    # door, its lit lattice window, the small arched window, the lantern
    add_cube(b, "door", (WX0 - 0.01, BED_Y + DOOR_H / 2, DOOR_Z), EYE, (0.06, DOOR_H, DOOR_W), {"all": "plank_dark", "-1": "tv_door", "+1": "tv_door"},
             stretch=True, u_dir=-Z, v_dir=-UP)
    add_cube(b, "glow_door_window", (WX0 - 0.05, BED_Y + DOOR_H - 0.5, DOOR_Z), EYE, (0.02, 0.62, 0.42),
             {"all": None, "-1": "tv_window"}, stretch=True, u_dir=-Z, v_dir=-UP)
    for k, z in enumerate((DOOR_Z - 0.23, DOOR_Z + 0.23)):
        beam(det, "door_win_bar_%d" % k, (WX0 - 0.065, BED_Y + DOOR_H - 0.82, z), (WX0 - 0.065, BED_Y + DOOR_H - 0.18, z), 0.04, "wood_dark", up=X)
    add_cube(det, "door_win_sill", (WX0 - 0.07, BED_Y + DOOR_H - 0.83, DOOR_Z), EYE, (0.06, 0.05, 0.52), "wood_dark")
    add_cube(b, "glow_side_window", (WX0 - 0.05, BED_Y + 1.25, -3.62), EYE, (0.02, 0.62, 0.36), {"all": None, "-1": "tv_window"},
             stretch=True, u_dir=-Z, v_dir=-UP)
    add_cube(det, "side_window_sill", (WX0 - 0.1, BED_Y + 0.92, -3.62), EYE, (0.12, 0.06, 0.48), "tv_timber")
    tl.lantern(det, "door_lamp", v3(WX0 - 0.33, BED_Y + 1.45, -1.72), size=0.24, chain_to=v3(WX0 - 0.33, BED_Y + 1.82, -1.72))
    beam(det, "door_lamp_arm", (WX0 - 0.05, BED_Y + 1.82, -1.72), (WX0 - 0.38, BED_Y + 1.82, -1.72), 0.05, "iron_dark", up=UP)
    add_cube(det, "door_lamp_plate", (WX0 - 0.07, BED_Y + 1.8, -1.72), EYE, (0.03, 0.18, 0.1), "iron_dark")
    # right end: a lantern beside the awning
    tl.lantern(det, "right_lamp", v3(WX1 + 0.32, BED_Y + 1.4, -1.62), size=0.24, chain_to=v3(WX1 + 0.32, BED_Y + 1.78, -1.62))
    beam(det, "right_lamp_arm", (WX1 + 0.05, BED_Y + 1.78, -1.62), (WX1 + 0.37, BED_Y + 1.78, -1.62), 0.05, "iron_dark", up=UP)
    collide((WX0, BED_Y, WZ0, WX1, EAVE, WZ1))
    return b


def counter(root, det):
    """The bar: the niche behind the opening (back wall with two shelves of bottles, kegs with taps on the back bench,
    a plank ceiling, two hanging lanterns), the counter board protruding outside with mugs, the ledge with three bar
    stools below."""
    c = tv.Bone("counter", parent=root)
    nz = NICHE_Z
    wall_x(c, "niche_back", CX0, CX1, BED_Y, EAVE, nz, region="plank")
    wall_z(c, "niche_l", nz, WZ1, CTR_Y, OPEN_TOP + 0.05, CX0 + 0.05, region="plank_dark")
    wall_z(c, "niche_r", nz, WZ1, CTR_Y, OPEN_TOP + 0.05, CX1 - 0.05, region="plank_dark")
    box(c, "niche_ceiling", (CX0, OPEN_TOP, nz), (CX1, OPEN_TOP + 0.06, WZ1), "plank_dark", u_dir=X)
    # the counter board (outside) and the back bench (inside), same height
    box(c, "board", (CX0 - 0.08, CTR_Y - 0.09, WZ1 - 0.5), (CX1 + 0.08, CTR_Y, WZ1 + 0.25), {"all": "plank", "+2": "plank"}, u_dir=X)
    box(c, "board_edge", (CX0 - 0.08, CTR_Y - 0.16, WZ1 + 0.21), (CX1 + 0.08, CTR_Y - 0.09, WZ1 + 0.27), "tv_timber", u_dir=X)
    box(c, "back_bench", (CX0, CTR_Y - 0.09, nz), (CX1, CTR_Y, nz + 0.45), "plank", u_dir=X)
    for k in range(5):
        x = CX0 + 0.15 + k * (CX1 - CX0 - 0.3) / 4
        beam(det, "board_brace_%d" % k, (x, CTR_Y - 0.5, WZ1 + 0.05), (x, CTR_Y - 0.12, WZ1 + 0.22), 0.07, "wood_dark", width=0.07, up=X)
    # shelves on the back wall: two boards, rows of bottles (cut-out plates) and a few modelled bottles
    for k, y in enumerate((2.42, 2.72)):
        box(c, "shelf_%d" % k, (CX0 + 0.08, y - 0.04, nz + 0.04), (CX1 - 0.08, y, nz + 0.26), "plank", u_dir=X)
        for j in range(3):
            xa = CX0 + 0.12 + j * (CX1 - CX0 - 0.24) / 3
            xb = xa + (CX1 - CX0 - 0.24) / 3 - 0.02
            if k == 0 and j == 0:
                continue        # the kegs stand there
            tv.plate(det, "bottles_%d_%d" % (k, j), ((xa + xb) / 2, y + 0.11, nz + 0.14 - 0.03 * (j % 2)), xb - xa, 0.22, "tv_bottles", th=0.004)
    for k, (x, col) in enumerate(((-0.55, "green"), (-0.25, "brown"), (0.15, "red"))):
        tv.bottle(det, "bar_bottle_%d" % k, (x, CTR_Y, nz + 0.25), col, h=0.26)
    # kegs with taps on the back bench (three small ones on the left, a bigger one on the right)
    for k, x in enumerate((-2.62, -2.2, -1.78)):
        tv.keg(c, det, "keg_%d" % k, (x, CTR_Y + 0.19, nz + 0.24), r=0.17, L=0.36, axis="z")
    tv.keg(c, det, "keg_big", (-1.15, CTR_Y + 0.24, nz + 0.25), r=0.22, L=0.4, axis="z")
    # jugs and mugs on the back bench, mugs along the counter board
    for k, x in enumerate((-0.75, 0.05)):
        ml.octo(det, "jug_%d" % k, (x, CTR_Y, nz + 0.25), 0.08, 0.2, {"all": "potion_orange", "+2": "cork"})
    for k, x in enumerate((-2.7, -2.35, -1.6, -1.25, -0.55, -0.2, 0.2)):
        tv.mug(det, "bar_mug_%d" % k, (x, CTR_Y, WZ1 + 0.06 - 0.06 * (k % 2)), yaw=0.3 * k)
    # lanterns hanging from the niche ceiling
    for k, x in enumerate((-2.0, -0.35)):
        tl.lantern(det, "bar_lamp_%d" % k, v3(x, 2.55, WZ1 - 0.42), size=0.22, chain_to=v3(x, OPEN_TOP, WZ1 - 0.42))
    collide((CX0 - 0.08, CTR_Y - 0.16, WZ1, CX1 + 0.08, CTR_Y, WZ1 + 0.27))
    # the ledge (the wagon floor running out between the wheels) and its braces
    lx0, lx1, lz1 = -2.7, 0.0, WZ1 + 0.9
    tl.platform(c, "ledge", lx0, lx1, WZ1, lz1, BED_Y, th=0.08, plank_w=0.45, along="x", region="plank", solid=False, joists=False)
    box(c, "ledge_edge", (lx0, BED_Y - 0.2, lz1 - 0.08), (lx1, BED_Y - 0.08, lz1), "tv_timber", u_dir=X)
    for k, x in enumerate((lx0 + 0.15, (lx0 + lx1) / 2, lx1 - 0.15)):
        beam(det, "ledge_brace_%d" % k, (x, BED_Y - 0.62, WZ1 + 0.06), (x, BED_Y - 0.12, lz1 - 0.12), 0.08, "wood_dark", width=0.08, up=X)
    collide((lx0, BED_Y - 0.2, WZ1, lx1, BED_Y, lz1))
    return c, (lx0, lx1, lz1)


# ---------------------------------------------------------------- roof
def roof(root, det):
    r = tv.Bone("roof", parent=root)
    for k, (xa, xb, reg, ny) in enumerate(ROOF_SECTIONS):
        tv.loft(r, "canvas_%d" % k, roof_P(xa, xb), 8, ny, reg, th=0.035)
    # the wooden rims of the hood (left) and of the right end
    nx = 8
    for e, (xa, xb, t) in (("l", (ROOF_SECTIONS[0][0], ROOF_SECTIONS[0][1], 0.0)), ("r", (ROOF_SECTIONS[2][0], ROOF_SECTIONS[2][1], 1.0))):
        P = roof_P(xa, xb)
        pts = [P(i / nx, t) for i in range(nx + 1)]
        for i in range(nx):
            a, b2 = pts[i], pts[i + 1]
            n = outward((a + b2) / 2)
            beam(r, "rim_%s_%d" % (e, i), a - n * 0.04, b2 - n * 0.04, 0.1, "wood_dark", width=0.1, up=X, extend=0.03)
    # straps (battens) over the canvas at the hoops, dark leather
    for k, x in enumerate((-3.3, -1.1, 1.05)):
        pts = [roof_point(i / nx, x) for i in range(nx + 1)]
        for i in range(nx):
            a, b2 = pts[i], pts[i + 1]
            n = outward((a + b2) / 2)
            beam(det, "strap_%d_%d" % (k, i), a + n * 0.03, b2 + n * 0.03, 0.025, "leather_dark", width=0.09, up=X, extend=0.01)
    # roof collision: two side walls and the top
    collide((WX0 - 0.1, EAVE, WZ1 - 0.2, WX1 + 0.1, EAVE + RISE * 0.6, WZ1 + 0.17))
    collide((WX0 - 0.1, EAVE, WZ0 - 0.17, WX1 + 0.1, EAVE + RISE * 0.6, WZ0 + 0.2))
    collide((WX0 - 0.1, EAVE + RISE * 0.6, WZ0 + 0.1, WX1 + 0.1, RY0 + RISE + 0.04, WZ1 - 0.1))
    return r


def roof_cargo(root, det):
    """The rack on the ridge with a big iron-banded chest and a crate, the chimney, the ivy."""
    rc = tv.Bone("roof_cargo", parent=root)
    top = RY0 + RISE + 0.12
    x0, x1, z0, z1 = -2.95, -0.75, WZC - 0.66, WZC + 0.66
    tl.platform(rc, "rack", x0, x1, z0, z1, top, th=0.07, plank_w=0.4, along="x", region="plank", solid=False, joists=False)
    for k, (x, z) in enumerate(((x0 + 0.08, z0 + 0.08), (x1 - 0.08, z0 + 0.08), (x0 + 0.08, z1 - 0.08), (x1 - 0.08, z1 - 0.08))):
        s = (z - WZC) / RHW
        yb = roof_point(0.5 - math.asin(max(-1, min(1, s))) / math.pi, x)[1]
        beam(rc, "rack_leg_%d" % k, (x, yb - 0.05, z), (x, top + 0.3, z), 0.09, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    for k, z in enumerate((z0 + 0.08, z1 - 0.08)):
        beam(det, "rack_rail_%d" % k, (x0 + 0.04, top + 0.24, z), (x1 - 0.04, top + 0.24, z), 0.06, "wood_dark", up=UP)
    wl.chest(rc, "chest", (-1.62, top, WZC + 0.02), w=1.15, h=0.72, d=0.7, yaw=0.0, solid=False)
    ml.crate(rc, "roof_crate", (-2.5, top, WZC - 0.12), size=0.52, yaw=0.15)
    ml.crate(rc, "roof_crate_b", (-2.55, top + 0.52, WZC - 0.1), size=(0.42, 0.3, 0.42), yaw=-0.2)
    collide((x0, top - 0.3, z0, x1, top + 0.72, z1))
    # the chimney (stone) rising through the roof near the right end
    tv.chimney(rc, det, "chimney", (0.55, RY0 + RISE - 0.5, WZC + 0.15), RY0 + RISE + 1.15, s=0.6)
    collide((0.25, RY0 + RISE - 0.3, WZC - 0.15, 0.85, RY0 + RISE + 1.15, WZC + 0.45))
    # ivy: strips lying on the front slope of the canvas, spilling over the eave, strands hanging over the counter
    for k, (xa, xb, sa, sb) in enumerate(((-2.3, -0.85, 0.47, 0.26), (-1.75, -0.15, 0.31, 0.1), (-1.15, 0.4, 0.15, -0.02),
                                         (-4.45, -3.45, 0.62, 0.38), (-3.25, -2.45, 0.6, 0.44), (-0.6, 0.1, 0.62, 0.45))):
        def P(s, t, xa=xa, xb=xb, sa=sa, sb=sb):
            x = xa + (xb - xa) * s
            p = roof_point(sa + (sb - sa) * t, x)
            return p + outward(p) * 0.045
        tv.loft(rc, "ivy_roof_%d" % k, P, 2, 3, "tv_ivy", th=0.006)
    for k, (x, L) in enumerate(((-2.45, 0.6), (-1.85, 0.95), (-1.15, 0.7), (-0.45, 0.5), (0.2, 0.75))):
        ml.vine(det, "ivy_hang_%d" % k, (x, EAVE + 0.06, WZ1 + 0.21 + 0.015 * (k % 3)), L, 0.5, normal=(0, 0, 1), region="tv_ivy_hang")
    return rc


def banners(root, det):
    bn = tv.Bone("banners", parent=root)
    for k, x in enumerate((-4.1, 1.42)):
        tv.mug_banner(bn, "banner_front_%d" % k, (x, EAVE - 0.12, WZ1 + 0.13), w=0.74, h=0.98, normal=(0, 0, 1))
    # under the hood at the left end, in front of the gable, hung by two cords from the rim
    top = v3(WX0 - 0.5, RY0 + RISE - 0.3, WZC)
    tv.mug_banner(bn, "banner_end", top, w=0.92, h=1.2, normal=(-1, 0, 0))
    for k, s in enumerate((-1, 1)):
        a = top + Z * s * 0.4 + UP * 0.03
        tl.rope(det, "banner_end_cord_%d" % k, a, a + UP * 0.24 + v3(-0.1, 0, 0), d=0.03)
    return bn


def porch(root, det):
    """The porch at the left end (a platform at the floor's height with railings), the steps down along -x, the rope
    hand rail."""
    p = tv.Bone("porch", parent=root)
    tl.platform(p, "porch", PORCH_X, WX0, WZ0 + 0.05, WZ1 - 0.05, BED_Y, th=0.09, plank_w=0.42, along="z", region="plank", solid=False,
                joists=False)
    add_cube(p, "porch_beam", (PORCH_X + 0.06, BED_Y - 0.2, WZC), EYE, (0.14, 0.24, WZ1 - WZ0), "tv_timber", u_dir=Z)
    for k, z in enumerate((WZ0 + 0.12, WZ1 - 0.12)):
        tl.post(p, "porch_leg_%d" % k, (PORCH_X + 0.08, 0.0, z), (PORCH_X + 0.08, BED_Y - 0.1, z), d=0.14, region="wood_dark", solid=False)
    collide((PORCH_X, 0.0, WZ0 + 0.05, WX0, BED_Y, WZ1 - 0.05))
    # railing posts with caps, rails between them (the steps' opening stays free)
    for k, (za, zb) in enumerate(((WZ0 + 0.08, STEP_Z0 - 0.06), (STEP_Z1 + 0.06, WZ1 - 0.08))):
        for j, z in enumerate((za, zb)):
            tl.post(p, "rail_post_%d_%d" % (k, j), (PORCH_X + 0.08, BED_Y - 0.05, z), (PORCH_X + 0.08, BED_Y + 1.0, z), d=0.16,
                    region="tv_timber", solid=False)
            add_cube(p, "rail_cap_%d_%d" % (k, j), (PORCH_X + 0.08, BED_Y + 1.04, z), EYE, (0.22, 0.08, 0.22), "wood_dark")
            tv.bolt(det, "rail_bolt_%d_%d" % (k, j), (PORCH_X + 0.0, BED_Y + 0.7, z), (-1, 0, 0), s=0.08)
        for j, y in enumerate((BED_Y + 0.45, BED_Y + 0.9)):
            beam(p, "rail_%d_%d" % (k, j), (PORCH_X + 0.08, y, za), (PORCH_X + 0.08, y, zb), 0.08, "tv_timber", width=0.08, up=UP, extend=0.05)
        collide((PORCH_X, BED_Y, min(za, zb) - 0.1, PORCH_X + 0.17, BED_Y + 1.0, max(za, zb) + 0.1))
    # the side rail along the porch's front edge (towards +z) to the wagon
    for k, z in enumerate((WZ1 - 0.08,)):
        for j, y in enumerate((BED_Y + 0.45, BED_Y + 0.9)):
            beam(p, "rail_side_%d" % j, (PORCH_X + 0.08, y, z), (WX0 - 0.06, y, z), 0.08, "tv_timber", width=0.08, up=UP)
    # steps
    n = 4
    rise = BED_Y / (n + 1)
    run = 0.26
    for k in range(n):
        top = BED_Y - rise * (k + 1)
        xa = PORCH_X - run * (k + 1)
        box(p, "step_%d" % k, (xa, 0.0, STEP_Z0), (xa + run + 0.02, top, STEP_Z1), {"all": "plank_dark", "+2": "plank", "-1": "plank"}, u_dir=Z)
        box(det, "step_nose_%d" % k, (xa - 0.02, top - 0.06, STEP_Z0 - 0.02), (xa + 0.06, top + 0.005, STEP_Z1 + 0.02), "wood_dark", u_dir=Z)
        collide((xa, 0.0, STEP_Z0, xa + run, top, STEP_Z1))
    xb = PORCH_X - run * n
    for k, z in enumerate((STEP_Z0 - 0.04, STEP_Z1 + 0.04)):
        beam(p, "stringer_%d" % k, (PORCH_X + 0.02, BED_Y - 0.02, z), (xb - 0.02, 0.0, z), 0.08, "wood_dark", width=0.2, up=Z)
    # a post at the foot of the steps and a rope hand rail up to the porch post
    tl.post(p, "step_post", (xb + 0.05, 0.0, STEP_Z1 + 0.16), (xb + 0.05, 0.95, STEP_Z1 + 0.16), d=0.14, region="tv_timber", solid=True)
    add_cube(p, "step_post_cap", (xb + 0.05, 0.98, STEP_Z1 + 0.16), EYE, (0.2, 0.07, 0.2), "wood_dark")
    tl.rope(det, "hand_rope", (xb + 0.05, 0.85, STEP_Z1 + 0.16), (PORCH_X + 0.08, BED_Y + 0.9, STEP_Z1 + 0.06), d=0.045, sag=0.12, segs=4)
    return p


def awning(root, det):
    """The striped awning stretched from the wagon's right end to two posts (the sign post at the front), its dagged
    valance along the front and the outer edge, a lantern hanging under it."""
    a = tv.Bone("awning", parent=root)
    A, B, C, D = AW_A, AW_B, AW_C, AW_D

    def P(s, t):
        p = (1 - t) * ((1 - s) * A + s * B) + t * ((1 - s) * D + s * C)
        return p - UP * (0.12 * math.sin(math.pi * s) * math.sin(math.pi * t))
    tv.loft(a, "cloth", P, 4, 3, "tv_awning", th=0.03)
    for e, F in (("front", lambda u, v: P(1.0, u) - UP * 0.5 * v + v3(0.0, 0, 0.012)),
                 ("side", lambda u, v: P(1.0 - u, 1.0) - UP * 0.5 * v + v3(0.012, 0, 0))):
        tv.loft(a, "valance_" + e, F, 4, 1, "tv_valance", th=0.02)
    # poles under the edges, the back post
    beam(a, "edge_front", B + v3(0, -0.05, 0), C + v3(0, -0.05, 0), 0.08, "wood_dark", up=UP)
    beam(a, "edge_side", C + v3(0, -0.05, 0), D + v3(0, -0.05, 0), 0.08, "wood_dark", up=UP)
    beam(a, "edge_wagon", A + v3(0.04, -0.06, 0), B + v3(0.04, -0.06, 0), 0.08, "wood_dark", up=UP)
    tl.post(a, "back_post", (D[0], 0.0, D[2]), (D[0], D[1] + 0.2, D[2]), d=0.16, region="tv_timber", solid=True)
    add_cube(a, "back_post_cap", (D[0], D[1] + 0.24, D[2]), EYE, (0.22, 0.08, 0.22), "wood_dark")
    lamp = P(0.92, 0.62)
    tl.lantern(det, "awning_lamp", lamp - UP * 0.62, size=0.24, chain_to=lamp - UP * 0.04)
    return a


def sign_post(root, det):
    """The tall sign post at the awning's front corner: a squared post, an arm to the right with a diagonal brace, the
    square mug sign hanging by two chains."""
    s = tv.Bone("sign", parent=root)
    x, z = SIGN_POST
    H = 4.45
    tl.post(s, "sign_post", (x, 0.0, z), (x, H, z), d=0.24, region="tv_timber", solid=True)
    add_cube(s, "sign_post_cap", (x, H + 0.04, z), EYE, (0.3, 0.08, 0.3), "wood_dark")
    add_cube(s, "sign_post_foot", (x, 0.12, z), EYE, (0.36, 0.24, 0.36), "wood_dark")
    ya = H - 0.32
    xe = x + 1.95
    beam(s, "sign_arm", (x - 0.2, ya, z), (xe, ya, z), 0.2, {"all": "tv_timber", "+1": "end_grain", "-1": "end_grain"}, width=0.18, up=UP)
    beam(s, "sign_brace", (x + 0.06, ya - 0.95, z), (x + 0.9, ya - 0.06, z), 0.13, "tv_timber", width=0.13, up=Z)
    for k, xx in enumerate((x, x + 0.9, xe - 0.08)):
        add_cube(det, "sign_band_%d" % k, (xx, ya, z), EYE, (0.06, 0.24, 0.23), "iron_dark")
    tv.bolt(det, "sign_post_bolt", (x, ya - 0.95, z + 0.12), (0, 0, 1))
    tv.hanging_sign(s, det, "sign_board", (x + 0.78, ya - 0.1, z), (x + 1.62, ya - 0.1, z), size=1.02, drop=0.24, normal=(0, 0, 1))


def fire_corner(root, det):
    f = tv.Bone("fire", parent=root)
    fx, fz = FIRE
    tv.campfire(f, det, "campfire", (fx, 0.0, fz), r=0.68)
    tv.tripod_cauldron(f, det, "trestle", (fx, 0.0, fz), span=1.6, h=1.85, axis="x", cauldron_y=0.46, r=0.3)
    # logs stacked beside the fire
    for k, (a, b2) in enumerate((((6.0, 0.12, -0.3), (6.0, 0.12, 0.3)), ((6.22, 0.12, -0.32), (6.22, 0.12, 0.28)),
                                 ((6.11, 0.32, -0.3), (6.11, 0.32, 0.3)))):
        cl.log(f, "firewood_%d" % k, a, b2, r=0.11)
    collide((5.85, 0.0, -0.45, 6.35, 0.44, 0.45))   # the firewood
    return f


def tapped_barrel_model(bone, name, foot):
    """The stand-in of landsoficaria:tapped_cypress_barrel: a barrel lying along z on a wooden cradle, its brass tap
    towards +z."""
    f = v3(*foot)
    tv.keg(bone, bone, name, f + UP * 0.47, r=0.36, L=0.86, axis="z")
    for k, dz in enumerate((-0.27, 0.27)):
        box(bone, "%s_cradle_%d" % (name, k), (f[0] - 0.4, 0.0, f[2] + dz - 0.05), (f[0] + 0.4, 0.2, f[2] + dz + 0.05), "wood_dark", u_dir=X)


def terrace(root, det, decor):
    """The pavers, the rug, the four tables with their stools (seats), mugs, bottles and lanterns, barrels, a sack,
    crates."""
    t = tv.Bone("terrace", parent=root)
    fu = tv.Bone("furniture", parent=root)
    tv.pavers(t, "pavers_0", (-1.25, 0, 2.15), 8.4, 4.5, y=0.0)
    tv.pavers(t, "pavers_1", (3.0, 0, 0.9), 3.6, 3.4, yaw=0.0, y=0.004)
    tv.pavers(t, "pavers_2", (-5.35, 0, 1.4), 2.3, 3.4, yaw=0.0, y=0.008)
    tv.rug(t, "rug", -2.85, 0.55, 0.72, 3.78, y=0.03)

    tables = [  # (name, centre, w, d, stools [(dx, dz, yaw)], props)
        ("t_left", (-5.05, 2.6), 1.0, 0.95, [(0.85, 0.0, 90), (0.0, 0.9, 180)]),
        ("t_centre", (-1.15, 2.25), 1.7, 1.05, [(-0.45, 0.9, 180), (0.45, 0.9, 180), (-0.45, -0.9, 0), (0.45, -0.9, 0), (-1.2, 0.0, 270),
                                               (1.2, 0.0, 90)]),
        ("t_right", (2.9, 0.5), 1.3, 0.95, [(-0.4, 0.85, 180), (0.4, 0.85, 180), (-1.0, 0.0, 270), (0.0, -0.85, 0)]),
        ("t_front", (1.65, 2.85), 0.95, 0.9, [(0.0, 0.85, 180), (0.85, 0.0, 90)]),
        ("t_back", (3.35, -1.85), 1.0, 0.9, [(0.0, 0.85, 180), (0.85, 0.0, 90)]),
    ]
    tops = {}
    for name, (cx, cz), w, d, stools in tables:
        h = tv.table(fu, det, name, (cx, 0.0, cz), w, d, h=0.84)
        tops[name] = (cx, h, cz)
        for dx, dz, yaw in stools:
            tv.stool(decor, cx + dx, 0.0, cz + dz, yaw)
    # what stands on the tables
    x, y, z = tops["t_left"]
    tv.standing_lantern(det, "lamp_t_left", (x - 0.22, y, z - 0.12))
    decor.block("farmhouse_decorations:wine_bottle", x + 0.18, y, z + 0.1, facing="front", fallback="potion_green", solid=False,
                builder=lambda b, n, x=x, y=y, z=z: tv.bottle(b, n, (x + 0.18, y, z + 0.1), "green", h=0.3))
    tv.mug(det, "mug_t_left", (x + 0.25, y, z - 0.25), yaw=0.4)
    x, y, z = tops["t_centre"]
    tv.standing_lantern(det, "lamp_t_centre", (x - 0.05, y, z - 0.05))
    for k, (dx, dz, yaw) in enumerate(((-0.55, 0.28, 0.2), (-0.35, -0.3, 1.2), (0.45, 0.25, 2.0), (0.62, -0.2, 0.7))):
        tv.mug(det, "mug_t_centre_%d" % k, (x + dx, y, z + dz), yaw=yaw)
    decor.block("farmhouse_decorations:wine_bottle", x + 0.28, y, z - 0.05, facing="front", fallback="potion_green", solid=False,
                builder=lambda b, n, x=x, y=y, z=z: tv.bottle(b, n, (x + 0.28, y, z - 0.05), "green", h=0.3))
    x, y, z = tops["t_right"]
    tv.standing_lantern(det, "lamp_t_right", (x + 0.3, y, z - 0.1))
    for k, (dx, dz, yaw) in enumerate(((-0.4, 0.2, 0.5), (-0.1, -0.22, 1.4), (0.05, 0.25, 2.4))):
        tv.mug(det, "mug_t_right_%d" % k, (x + dx, y, z + dz), yaw=yaw)
    x, y, z = tops["t_front"]
    tv.standing_lantern(det, "lamp_t_front", (x - 0.2, y, z - 0.15))
    for k, (dx, dz, yaw) in enumerate(((0.2, 0.15, 0.3), (0.25, -0.22, 1.1))):
        tv.mug(det, "mug_t_front_%d" % k, (x + dx, y, z + dz), yaw=yaw)
    x, y, z = tops["t_back"]
    ml.crate(fu, "crate_t_back", (x - 0.15, y, z - 0.1), size=0.46, yaw=0.2, solid=False)
    tv.mug(det, "mug_t_back", (x + 0.3, y, z + 0.25), yaw=0.9)
    tv.standing_lantern(det, "lamp_t_back", (x + 0.3, y, z - 0.2), size=0.2)
    # the three bar stools on the ledge (facing the counter)
    for k, sx in enumerate((-2.2, -1.35, -0.5)):
        tv.stool(decor, sx, BED_Y, WZ1 + 0.5, 180)
    # barrels, sack, crates
    decor.block("landsoficaria:tapped_cypress_barrel", -3.75, 0.0, 0.32, facing="front", alt="minecraft:barrel", fallback="barrel",
                builder=lambda b, n: tapped_barrel_model(b, n, (-3.75, 0.0, 0.44)))
    ml.barrel(fu, "barrel_steps", (-5.0, 0.0, 0.55), r=0.36, h=0.88)
    tv.mug(det, "mug_barrel_steps", (-4.92, 0.88, 0.5), yaw=0.6)
    ml.barrel(fu, "barrel_far_left", (-6.15, 0.0, 0.85), r=0.34, h=0.85)
    ml.sack(fu, "sack", (-3.05, 0.0, 0.45), s=0.48, yaw=0.3)
    ml.barrel(fu, "barrel_right_0", (5.05, 0.0, -2.75), r=0.36, h=0.88)
    ml.barrel(fu, "barrel_right_1", (5.85, 0.0, -1.95), r=0.32, h=0.8)
    wl.crate(fu, "crate_right_0", (5.4, 0.0, -1.25), s=0.62, yaw=0.25)
    wl.crate(fu, "crate_big", (4.3, 0.0, 0.62), s=0.84, yaw=0.0)
    ml.barrel(fu, "barrel_under_awning", (2.85, 0.0, -3.5), r=0.32, h=0.82)
    return t


def build():
    root = tv.Bone(NAME)
    det = tv.Bone("detail", parent=root)
    decor = tv.Decor()
    running_gear(root, det)
    body(root, det)
    counter(root, det)
    roof(root, det)
    roof_cargo(root, det)
    banners(root, det)
    porch(root, det)
    awning(root, det)
    sign_post(root, det)
    fire_corner(root, det)
    terrace(root, det, decor)
    particles = [
        tv.particle("campfire_smoke", (0.55, RY0 + RISE + 1.15 + 0.2, WZC + 0.15), chance=0.08, count=1),
        tv.particle("flame", (FIRE[0], 0.32, FIRE[1]), chance=0.3, count=1),
        tv.particle("smoke", (FIRE[0], 0.95, FIRE[1]), chance=0.15, count=1),
    ]
    return root, decor, particles


def main():
    tv.setup(NAME)
    atlas = tv.Atlas(NAME)
    root, decor, particles = build()
    tv.export(root, NAME, atlas, decor=decor, particles=particles, icon=tv.icon_tavern, visible_box=(14, 7, 0))


if __name__ == "__main__":
    main()
