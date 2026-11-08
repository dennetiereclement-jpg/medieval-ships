#!/usr/bin/env python3
"""tente_balance_fer — Pavillon à la balance et ferronnerie / Wrought-Iron Scales Pavilion (1.26.0, market tents group C;
reference: scratchpad/ref2/tente_balance_fer_ref.png, picture 050).

A round red-and-cream pavilion on an ornate WROUGHT-IRON frame, one block (TentType group "tents"), about 11 blocks wide
(the banner post on the left and the sign post on the right included) and 7.2 deep (the rug in front), the spire at
about 8:

  - the roof: a pavilion cone over a rounded square, twelve gores in faded crimson (gold filigree scrolls painted on
    them) and weathered cream, steep at the top and flaring to the eaves, a gold rope along the eave with brass studs,
    broad and low; the pointed-dag valance in cream and crimson edged in gold on the right of the front, the right side
    and the back (none under the arches);
  - the BRASS FINIAL on the apex (collar, bulb, spire, ball) with a long red streamer flag;
  - the frame: four square black-iron posts with brass collars and brass ball-and-spike finials (the front-left one
    tall and thick, rising well above the eave), iron eave beams; from high on the front-left post two big WROUGHT-IRON
    ARCHES sweep out and down to the eave, one over the entrance and one along the left side (a thinner concentric arch
    under each, cut-out brass-coloured scrollwork in their corners), a small one at the front-right post; scroll
    brackets under the front beam;
  - the walls: faded striped cloth (crimson, blue, cream); on the LEFT the cloth sweeps down from the eave to the
    ground well outside the frame (a bell-tent skirt under the left arch, closed at the back), straight walls at the
    back and on the right; red drapes with gold fringe tied back at the front posts; bunting of red and cream pennants
    from the front-left post across the front and out to the banner post;
  - the tall iron BANNER POST on the left (brass spikes): a long arm carrying, on three chains, the big crimson banner
    with the gold SCALES over a laurel wreath and a gold fringe;
  - the iron SIGN POST on the right: an arm with a spear tip, the dark sign with a gold frame and a gold SCROLL hanging
    from two chains;
  - inside: the back SHELVES full of CLOTH BOLTS (red, blue, green, cream, orange, olive), the left COUNTER under a
    crimson runner with the gold scales and a gold fringe (books, scrolls), the right counter (coin bags, a standing
    lantern), a small iron-banded chest; a lantern on the front-left post's bracket and one hanging inside; a dark rug;
  - outside: on the left a big open crate full of standing cloth rolls with a box on top, a barrel draped with a cream
    and crimson cloth carrying scrolls and a book, a burlap sack, ivy; on the right the domed TREASURE CHEST and a big
    crate of standing cloth rolls under a cream cloth; the crimson RUG with its gold scroll border and fringe in front.

The merchant's place (an EasyNPC, 1 x 1 x 2.2 free) is behind the left counter (NPC_SPOT), reached from the open front.
No trade system, nothing ticks.

Usage:  python3 tools/market/generate_tente_balance_fer.py     (MERCHANT_OUT=<file.bbmodel>: preview model only)
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import props_c as pc  # noqa: E402

ml = pc.ml
v3, norm, add_cube, beam, loft, Bone = pc.v3, pc.norm, pc.add_cube, pc.beam, pc.loft, pc.Bone
EYE, UP, X, Z = pc.EYE, pc.UP, pc.X, pc.Z
ry, rx = pc.ry, pc.rx
box, collide = pc.box, pc.collide
_rgb, _scale, _mix = pc._rgb, pc._scale, pc._mix

NAME = "tente_balance_fer"
P = pc.Pal(red="8e2428", red_dark="4e1014", red_light="b4403a", cream="d4be96", gold="d8a03a", gold_dark="7e5216", gold_light="f6d482")
BLUE = _rgb("34405a")
IRON = "c2_iron"

# ---------------------------------------------------------------- dimensions (tent-local blocks, +z = the open front)
PX, PZF, PZB = 2.6, 2.1, -2.0   # iron posts: x = +-PX, z = PZF (front) / PZB (back)
BEAM_Y = 3.25                   # eave beams
EA, EB, EZ0 = 3.05, 2.72, 0.05  # the roof's eave: half sizes (x, z) of its rounded square, its centre z
EY = 3.48                       # the eave height
APEX = 5.25                     # the cloth apex (a broad, low cone as in the picture)
SPIRE = 6.95                    # the spire's ball
NG = 12                         # roof gores
BP = (-4.3, 0.75)               # the banner post (x, z), in front of the sloping left skirt
SP = (3.6, 0.55)                # the sign post (x, z)
COUNTER = (-2.2, -0.45, 0.45, 1.0)
R_COUNTER = (1.0, 2.25, -0.9, -0.35)
NPC_SPOT = (-1.45, -0.62)       # (x0, z0) of the free 1 x 1 x 2.2 place behind the left counter
VAL_CUT = 1.62                  # the front valance stops at this eave angle (x about -0.6): the arches on its left
SK_X, SK_Z = -3.9, (-1.95, 1.2) # the sloping left skirt: its foot line (x) and its back / front ends on the ground
SHELF_Z = (-1.85, -1.4)
FL_TOP, FR_TOP = 4.5, 3.95      # the front posts rise above the eave (the arches spring from them)


def regions():
    red, rd, rl, cr, g, gd, gl = P.red, P.red_dark, P.red_light, P.cream, P.gold, P.gold_dark, P.gold_light
    rg = [
        ("c2_gore_red", 48, 112, pc.gore_painter(red, rd, g, 5001, ornament=True, faded=0.25)),
        ("c2_gore_cream", 48, 112, pc.gore_painter(cr, _scale(cr, 0.7), g, 5002, ornament=False, faded=0.1)),
        ("c2_banner", 56, 144, pc.banner_painter(red, rd, g, gd, gl, 5003, point="flat", laurel=True, fringe=True, border=3, emblem_y=0.3,
                                                 emblem_w=0.7)),
        ("c2_rug", 96, 128, pc.carpet_painter(red, rd, g, gd, 5004, style="scroll")),
        ("c2_wall", 128, 64, pc.stripes_painter([red, _scale(cr, 0.8), rd, BLUE, red, _scale(cr, 0.8), BLUE, rd], 8, 5005, fold=0.34, grad=(0.7, 0.9),
                                               stains=2)),
        ("c2_drape", 32, 64, pc.stripes_painter([red, _scale(red, 0.9)], 3, 5006, fold=0.36, seam=0.86, hem=g, hem_h=5, grad=(0.8, 1.0))),
        ("c2_val", 192, 28, pc.valance_painter([cr, red], 8, 5007, kind="point", edge=g, edge_dark=gd, solid=0.36)),
        ("c2_runner", 48, 48, pc.runner_painter(red, rd, g, 5008, motif="none", fringe=True, emblem="scales", gold_dark=gd, gold_light=gl)),
        ("c2_sign", 56, 48, pc.sign_painter("scroll", 5009, board="2e2620", board_dark="161210", frame="5a3a1a", gold=g, gold_dark=gd,
                                            gold_light=gl, clip=7, frame_col=g)),
        ("c2_streamer", 96, 20, pc.flag_painter(red, rd, g, 5010, notch=0.22, border=True, patches=False)),
        ("c2_filigree", 64, 40, pc.filigree_painter(5011, iron="7a5a22", hi="c49a48", brass="e0b04a")),
        ("c2_cloth", 32, 32, pc.stripes_painter([cr], 1, 5012, fold=0.25, hem=red, hem_h=6, grad=(0.85, 1.0))),
        ("c2_pen_red", 16, 24, pc.pennant_painter(red, g, 5013)),
        ("c2_pen_cream", 16, 24, pc.pennant_painter(cr, g, 5014)),
        ("c2_iron", 32, 16, pc.iron_painter(5015, brass="9a7a3a")),
        ("c_chest", 32, 32, pc.chest_painter(5016, base="5e4026", dark="2a1a0c")),
        ("c_burlap", 32, 32, pc.burlap_painter("b49a72", 5017)),
        ("c2_crate", 32, 32, pc.chest_painter(5018, base="6e5638", dark="34261a")),
    ]
    for col in ("red", "blue", "green", "cream", "orange", "olive"):
        rg.append(("c_fab_" + col, 32, 16, pc.fabric_painter(col)))
        rg.append(("c_end_" + col, 16, 16, pc.bolt_end_painter(col)))
    return rg


# ---------------------------------------------------------------- roof
def eave_pt(th, y=EY, grow=0.0):
    c, s = math.cos(th), math.sin(th)
    p = 4.0
    x = (EA + grow) * math.copysign(abs(c) ** (2 / p), c)
    z = (EB + grow) * math.copysign(abs(s) ** (2 / p), s) + EZ0
    return v3(x, y, z)


def roof(shell, det):
    apex = v3(0.0, APEX, 0.0)
    # red gores wider than the cream ones (the roof reads crimson), the front gore red and centred on the entrance
    wts = [1.35 if k % 2 == 0 else 0.65 for k in range(NG)]
    edges = [0.0]
    for wv in wts:
        edges.append(edges[-1] + wv)
    ph = math.pi / 2 - math.pi * wts[0] / sum(wts)
    for k in range(NG):
        a0, a1 = ph + 2 * math.pi * edges[k] / edges[-1], ph + 2 * math.pi * edges[k + 1] / edges[-1]
        pc.skirt(shell, "gore_%d" % k, lambda s: apex, lambda s, a0=a0, a1=a1: eave_pt(a0 + (a1 - a0) * s), "c2_gore_red" if k % 2 == 0 else "c2_gore_cream",
                 2, 5, a=0.42, belly=0.12, th=0.03, overlap=0.03)
    # the pointed-dag valance all round (one loft per side, 4 tabs each), the gold rope and brass studs on the eave
    for k, (a0, a1) in enumerate(((math.pi / 4, VAL_CUT), (5 * math.pi / 4, 7 * math.pi / 4), (-math.pi / 4, math.pi / 4))):

        def V(s, t, a0=a0, a1=a1):
            th = a0 + (a1 - a0) * s
            e = eave_pt(th, grow=0.03)
            out = norm(eave_pt(th) - v3(0, EY, EZ0))
            return e - UP * (0.68 * t) + out * (0.02 + 0.05 * t)
        loft(shell, "valance_%d" % k, lambda s, t, V=V: V(1 - s, t), 4 if k else 3, 1, "c2_val", th=0.025)
    n = 28
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        beam(det, "eave_rope_%d" % k, eave_pt(a0, EY + 0.02, 0.04), eave_pt(a1, EY + 0.02, 0.04), 0.06, "gold", extend=0.03)
    for k in range(8):
        th = math.pi / 8 + k * math.pi / 4
        p = eave_pt(th, EY + 0.0, 0.07)
        out = norm(p - v3(0, EY, EZ0))
        add_cube(det, "eave_stud_%d" % k, p, ry(math.atan2(out[0], out[2])) @ pc.rz(math.pi / 4), (0.14, 0.14, 0.04), "brass")
    # the brass finial and the spire, the streamer flag
    ml.octo(shell, "finial_collar", (0, APEX - 0.25, 0), 0.24, 0.32, "brass")
    ml.octo(shell, "finial_ring", (0, APEX + 0.05, 0), 0.32, 0.08, "gold")
    ml.octo(shell, "finial_bulb_0", (0, APEX + 0.12, 0), 0.2, 0.18, "brass")
    ml.octo(shell, "finial_bulb_1", (0, APEX + 0.3, 0), 0.14, 0.16, "gold")
    beam(shell, "spire", (0, APEX + 0.4, 0), (0, SPIRE, 0), 0.07, "brass")
    ml.octo(det, "spire_ball", (0, SPIRE - 0.04, 0), 0.08, 0.13, "gold")
    beam(det, "spire_tip", (0, SPIRE + 0.08, 0), (0, SPIRE + 0.3, 0), 0.035, "gold")

    def F(s, t):
        L, H = 1.75, 0.38 * (1 - 0.6 * s)
        return v3(0.04 + L * s, SPIRE - 0.18 - H * t - 0.12 * s * s + 0.07 * math.sin(s * 5.0), 0.12 * math.sin(s * 6.5) * s)
    loft(shell, "streamer", F, 5, 1, "c2_streamer", th=0.02, u_hint=X, v_hint=-UP)


# ---------------------------------------------------------------- iron work
def iron_post(shell, det, name, x, z, top, d=0.2, finial=True, collars=(), foot=True):
    """A square black-iron post: a brass-banded foot plinth, brass collars, a brass ball-and-spike finial."""
    if foot:
        box(shell, name + "_foot", (x - 0.2, 0.0, z - 0.2), (x + 0.2, 0.22, z + 0.2), {"all": IRON, "+2": "black_iron"})
        box(det, name + "_foot_band", (x - 0.21, 0.16, z - 0.21), (x + 0.21, 0.22, z + 0.21), "brass")
    beam(shell, name, (x, 0.2 if foot else 0.0, z), (x, top, z), d, {"all": IRON, "+1": "black_iron", "-1": "black_iron"})
    for k, y in enumerate(collars):
        box(det, "%s_collar_%d" % (name, k), (x - d / 2 - 0.035, y, z - d / 2 - 0.035), (x + d / 2 + 0.035, y + 0.09, z + d / 2 + 0.035), "brass")
    if finial:
        box(det, name + "_cap", (x - d / 2 - 0.04, top, z - d / 2 - 0.04), (x + d / 2 + 0.04, top + 0.07, z + d / 2 + 0.04), "brass")
        ml.octo(shell, name + "_ball", (x, top + 0.07, z), 0.12, 0.2, "brass")
        add_cube(det, name + "_spike", (x, top + 0.42, z), pc.rz(math.pi / 4), (0.09, 0.09, 0.09), "gold")
        beam(det, name + "_spike_tip", (x, top + 0.26, z), (x, top + 0.62, z), 0.04, "gold")
    collide((x - 0.2, 0.0, z - 0.2, x + 0.2, top, z + 0.2))


def scroll_bracket(det, name, post_pt, beam_pt, n=4):
    """A quarter-circle iron scroll under a beam from a post (post_pt, low) to the beam (beam_pt), a curl at its end."""
    p0, p1 = v3(*post_pt), v3(*beam_pt)
    pts = []
    for k in range(n + 1):
        t = k / n
        ang = math.pi / 2 * t
        pts.append(v3(p0[0] + (p1[0] - p0[0]) * (1 - math.cos(ang)), p0[1] + (p1[1] - p0[1]) * math.sin(ang), p0[2] + (p1[2] - p0[2]) * t))
    for k in range(n):
        beam(det, "%s_%d" % (name, k), pts[k], pts[k + 1], 0.05, IRON, extend=0.02)
    c = pts[n // 2] + (p1 - p0) * 0.12 * v3(1, 0, 1) - UP * 0.04
    for k in range(4):
        a0, a1 = k * math.pi / 2, (k + 1) * math.pi / 2
        q0 = c + (v3(1, 0, 0) * math.cos(a0) + UP * math.sin(a0)) * 0.08 * (1 - 0.15 * k)
        q1 = c + (v3(1, 0, 0) * math.cos(a1) + UP * math.sin(a1)) * 0.08 * (1 - 0.15 * (k + 1))
        beam(det, "%s_curl_%d" % (name, k), q0, q1, 0.03, IRON)


def corner_arch(shell, det, name, a, b, n=6, d=0.11, inner=0.36, filigree=True):
    """A big wrought-iron arch from high on a post (a) sweeping out and down to b (on the eave line), a quarter
    ellipse bulging up and out as in the picture; a thinner concentric arch `inner` lower; cut-out scrollwork filling
    the corner under them, a brass ball at the foot."""
    a, b = v3(*a), v3(*b)

    def curve(p, q, m):
        pts = []
        for k in range(m + 1):
            ang = math.pi / 2 * k / m
            h = p + (q - p) * math.sin(ang)
            pts.append(v3(h[0], q[1] + (p[1] - q[1]) * math.cos(ang), h[2]))
        return pts
    outer = curve(a, b, n)
    for k in range(n):
        beam(shell, "%s_%d" % (name, k), outer[k], outer[k + 1], d, IRON, extend=d * 0.5)
    ml.octo(det, name + "_ball", b - UP * 0.08, 0.07, 0.14, "brass")
    if inner:
        a2 = a - UP * inner
        b2 = a + (b - a) * 0.7
        b2[1] = b[1]
        inn = curve(a2, b2, n - 2)
        for k in range(n - 2):
            beam(det, "%s_in_%d" % (name, k), inn[k], inn[k + 1], d * 0.6, IRON, extend=d * 0.3)
    if filigree:
        hor = b - a
        hor[1] = 0.0
        L = pc.np.linalg.norm(hor)
        u = hor / L
        nrm = norm(pc.np.cross(u, UP))
        w, h = L * 0.62, (a[1] - b[1]) * 0.8
        c = a + u * (L * 0.36)
        c[1] = b[1] + h / 2 - 0.02
        ml.plate(det, name + "_filigree", c, w, h, "c2_filigree", normal=nrm, th=0.01)


def chain(det, name, a, b, link=0.07):
    a, b = v3(*a), v3(*b)
    L = pc.np.linalg.norm(b - a)
    n = max(1, int(L / link))
    for k in range(n):
        p = a + (b - a) * ((k + 0.5) / n)
        add_cube(det, "%s_%d" % (name, k), p, ry(math.pi / 2 * (k % 2)), (0.05, L / n * 1.1, 0.018), IRON)


# ---------------------------------------------------------------- props
def draped_barrel(shell, det, name, foot, r=0.36, h=0.86, rng=None):
    """A barrel with a cream and crimson cloth thrown over its top, hanging down the front and the side."""
    f = v3(*foot)
    ml.barrel(shell, name, f, r=r, h=h)
    box(shell, name + "_cloth", (f[0] - r * 0.95, h, f[2] - r * 0.95), (f[0] + r * 0.95, h + 0.02, f[2] + r * 0.95), {"all": "c2_cloth"}, stretch=True)
    ml.plate(shell, name + "_cloth_front", (f[0] + 0.05, h - 0.3, f[2] + r * 0.98), r * 1.5, 0.6, "c2_cloth", normal=(0, 0, 1), th=0.012)
    ml.plate(shell, name + "_cloth_side", (f[0] + r * 0.98, h - 0.24, f[2] - 0.05), r * 1.3, 0.48, "c2_cloth", normal=(1, 0, 0), th=0.012)


def roll_crate(shell, det, name, foot, size, cols, rng, yaw=0.0, cloth=False, sack=False):
    """A big open crate of weathered planks with cloth rolls standing in it (and a small sack), a cloth over its
    front edge."""
    f = v3(*foot)
    w, h, d = size
    ml.crate(shell, name, f, size=(w, h, d), yaw=yaw, region="c2_crate", top="c2_crate")
    for k, (sx, sz) in enumerate(((-0.42, -0.28), (0.42, -0.28), (-0.42, 0.28), (0.42, 0.28))):
        add_cube(det, "%s_corner_%d" % (name, k), f + ry(yaw) @ v3(sx * w * 1.02, h / 2, sz * d * 1.65), ry(yaw), (0.06, h + 0.02, 0.06), "wood_dark")
    n = len(cols)
    for i, col in enumerate(cols):
        x = (i + 0.5) / n - 0.5
        rr = rng.uniform(0.09, 0.12)
        hh = rng.uniform(0.55, 0.8)
        zc = rng.uniform(-0.12, 0.12) * d
        base = f + ry(yaw) @ v3(x * w * 0.86, h - 0.25, zc)
        tilt = v3(rng.uniform(-0.08, 0.08), 1.0, rng.uniform(-0.1, 0.05))
        if col == "sack":
            ml.sack(det, name + "_sack", base + UP * 0.2, s=0.3, yaw=0.4)
            continue
        pc.bolt(det, "%s_roll_%d" % (name, i), base, base + norm(tilt) * hh, rr, col)
    if cloth:
        ml.plate(shell, name + "_cloth", f + ry(yaw) @ v3(w * 0.15, h - 0.16, d / 2 + 0.015), w * 0.55, 0.42, "c2_cloth", normal=ry(yaw) @ Z, th=0.012)
        box(shell, name + "_cloth_top", f + ry(yaw) @ v3(-w * 0.12, h, d / 2 - 0.16), f + ry(yaw) @ v3(w * 0.42, h + 0.02, d / 2 + 0.01),
            {"all": "c2_cloth"}, stretch=True)


def build(decor):
    rng = random.Random(50)
    root = Bone(NAME)
    shell = Bone("shell", parent=root)
    det = Bone("detail", parent=root)
    # ---- the iron frame
    posts = {"fl": (-PX, PZF), "fr": (PX, PZF), "br": (PX, PZB), "bl": (-PX, PZB)}
    tops = {"fl": FL_TOP, "fr": FR_TOP, "br": BEAM_Y + 0.12, "bl": BEAM_Y + 0.12}
    for k, (x, z) in posts.items():
        iron_post(shell, det, "post_" + k, x, z, tops[k], d=0.27 if k == "fl" else 0.2, collars=(0.6, 1.5, 2.4, BEAM_Y - 0.25) + ((BEAM_Y + 0.55,) if tops[k] > BEAM_Y + 0.5 else ()))
    for k, ((xa, za), (xb, zb)) in enumerate(((posts["fl"], posts["fr"]), (posts["fr"], posts["br"]), (posts["br"], posts["bl"]), (posts["bl"], posts["fl"]))):
        beam(shell, "eave_%d" % k, (xa, BEAM_Y, za), (xb, BEAM_Y, zb), 0.12, IRON, extend=0.1)
    # the big iron arches of the front-left corner (over the entrance and along the left side), a small one at the right
    corner_arch(shell, det, "arch_front", (-PX + 0.08, FL_TOP - 0.3, PZF + 0.16), (-0.62, EY - 0.12, EB + EZ0 + 0.14), n=7, d=0.16)
    corner_arch(shell, det, "arch_left", (-PX - 0.12, FL_TOP - 0.3, PZF - 0.06), (-EA - 0.16, EY - 0.12, 0.25), n=6, d=0.16)
    corner_arch(shell, det, "arch_right", (PX + 0.1, FR_TOP - 0.25, PZF - 0.06), (EA + 0.12, EY - 0.1, 0.95), n=4, inner=0.0, d=0.09)
    for k, sx in enumerate((-1, 1)):
        scroll_bracket(det, "bracket_%d" % k, (sx * (PX - 0.1), BEAM_Y - 0.75, PZF), (sx * (PX - 0.85), BEAM_Y - 0.06, PZF))
    # the front rod with diamond ends (carries the bunting and the lantern)
    beam(shell, "front_rod", (-PX - 0.45, 2.95, PZF + 0.12), (-PX + 0.7, 2.95, PZF + 0.12), 0.06, "brass")
    add_cube(det, "front_rod_tip", (-PX - 0.5, 2.95, PZF + 0.12), pc.rz(math.pi / 4), (0.12, 0.12, 0.05), "gold")
    # ---- roof
    roof(shell, det)
    # ---- walls and drapes
    pc.wall(shell, "wall_back", (-PX, 0, PZB - 0.06), (PX, 0, PZB - 0.06), 0.0, BEAM_Y - 0.06, -Z, "c2_wall", nx=6, fold=0.07)
    collide((-PX, 0.0, PZB - 0.12, PX, BEAM_Y - 0.1, PZB))
    for k, sx in enumerate((-1, 1)):
        x = sx * (PX + 0.06)
        a, b = ((x, 0, PZB), (x, 0, 0.35)) if sx < 0 else ((x, 0, 0.35), (x, 0, PZB))
        pc.wall(shell, "wall_side_%d" % k, a, b, 0.0, BEAM_Y - 0.06, v3(sx, 0, 0), "c2_wall", nx=4, fold=0.07)
        collide((x - 0.06, 0.0, PZB, x + 0.06, BEAM_Y - 0.1, 0.35))
        if sx > 0:
            pc.drape(shell, det, "drape_side_%d" % k, (x, BEAM_Y - 0.1, 0.25), (x, BEAM_Y - 0.1, 1.05), (x, 1.45, 0.35), (x, 0.03, 0.2), (x, 0.03, 0.55),
                     v3(sx, 0, 0), "c2_drape", nx=2, tie_region="gold")
        xa, xb = sx * (PX - 0.15), sx * (PX - 0.95)
        pc.drape(shell, det, "drape_front_%d" % k, (xa, BEAM_Y - 0.1, PZF - 0.1), (xb, BEAM_Y - 0.1, PZF - 0.1), (sx * (PX - 0.25), 1.5, PZF - 0.14),
                 (sx * (PX - 0.18), 0.03, PZF - 0.12), (sx * (PX - 0.62), 0.03, PZF - 0.12), Z, "c2_drape", nx=3, tie_region="gold")
    # the left side: the cloth sweeps down from the eave to the ground well outside the frame (a bell-tent skirt, its
    # top under the left arch), closed at the back
    def eave_x(z):
        r = min(1.0, abs(z - EZ0) / (EB + 0.03))
        return -(EA + 0.03) * (1.0 - r ** 4) ** 0.25

    def SK(s, t):
        zt = -2.0 + 3.6 * s
        zb = SK_Z[0] + (SK_Z[1] - SK_Z[0]) * s
        top = v3(eave_x(zt), EY - 0.03, zt)
        bot = v3(SK_X, 0.0, zb)
        p = top + (bot - top) * t
        return p + v3(-1, 0, 0) * (0.1 * math.sin(math.pi * t) + 0.05 * math.sin(math.pi * ((s * 6) % 1.0)) * t)
    loft(shell, "skirt_left", SK, 6, 3, "c2_wall", th=0.03, overlap=0.03)

    def SKB(s, t):
        a = SK(0.0, t)
        b = v3(-PX - 0.02, (EY - 0.2) * (1 - t), PZB - 0.06)
        return a + (b - a) * s
    loft(shell, "skirt_back", SKB, 1, 2, "c2_wall", th=0.03, overlap=0.03)
    collide((SK_X, 0.0, SK_Z[0], -PX - 0.06, 0.9, SK_Z[1]))
    # bunting across the front and out to the banner post
    pc.bunting(det, "bunting_front", (-PX + 0.1, 2.98, PZF + 0.16), (0.2, 3.05, PZF + 0.3), 5, ("c2_pen_red", "c2_pen_cream"), sag=0.22, size=(0.24, 0.38))
    pc.bunting(det, "bunting_out", (-PX - 0.45, 2.98, PZF + 0.12), (BP[0] + 0.05, 3.9, BP[1] + 0.1), 4, ("c2_pen_cream", "c2_pen_red"), sag=0.2,
               size=(0.22, 0.34))
    # ---- the banner post (left) and the sign post (right)
    bx, bz = BP
    iron_post(shell, det, "banner_post", bx, bz, 6.1, d=0.16, collars=(0.8, 2.0, 3.4, 4.8, 5.45))
    ay = 5.55
    beam(shell, "banner_arm", (bx + 0.25, ay, bz), (bx - 1.3, ay, bz), 0.08, IRON, extend=0.04)
    for k, x in enumerate((bx + 0.3, bx - 1.36)):
        ml.octo(det, "banner_arm_ball_%d" % k, (x, ay - 0.06, bz), 0.06, 0.12, "brass")
        beam(det, "banner_arm_spike_%d" % k, (x, ay + 0.04, bz), (x, ay + 0.3, bz), 0.035, "gold")
    beam(det, "banner_arm_brace", (bx, ay - 0.65, bz), (bx - 0.6, ay - 0.04, bz), 0.04, IRON)
    cx = bx - 0.62
    beam(shell, "banner_rod", (cx - 0.62, ay - 0.42, bz), (cx + 0.62, ay - 0.42, bz), 0.06, "brass")
    for k, dx in enumerate((-0.48, 0.0, 0.48)):
        chain(det, "banner_chain_%d" % k, (cx + dx, ay - 0.05, bz), (cx + dx, ay - 0.4, bz))
    ml.banner(shell, "banner", (cx, ay - 0.45, bz + 0.02), 1.1, 2.75, normal=(0, 0, 1), region="c2_banner", rod=False, wave=0.03)
    sx_, sz_ = SP
    iron_post(shell, det, "sign_post", sx_, sz_, 4.85, d=0.16, collars=(0.8, 2.0, 3.3, 4.3))
    sy = 4.45
    beam(shell, "sign_arm", (sx_ - 0.15, sy, sz_), (sx_ + 1.35, sy, sz_), 0.08, IRON, extend=0.03)
    add_cube(det, "sign_arm_tip", (sx_ + 1.45, sy, sz_), pc.rz(math.pi / 4), (0.15, 0.15, 0.04), "brass")
    for k, x in enumerate((sx_ + 0.2, sx_ + 0.85)):
        add_cube(det, "sign_arm_ring_%d" % k, (x, sy, sz_), EYE, (0.11, 0.11, 0.11), "brass")
    beam(det, "sign_arm_brace", (sx_, sy - 0.6, sz_), (sx_ + 0.55, sy - 0.04, sz_), 0.04, IRON)
    scx = sx_ + 0.8
    for k, dx in enumerate((-0.32, 0.32)):
        chain(det, "sign_chain_%d" % k, (scx + dx, sy - 0.05, sz_), (scx + dx, sy - 0.42, sz_))
    box(shell, "sign", (scx - 0.46, sy - 1.27, sz_ - 0.04), (scx + 0.46, sy - 0.42, sz_ + 0.04), {"all": None, "+3": "c2_sign", "-3": "c2_sign"},
        stretch=True, u_dir=X, v_dir=-UP)
    box(det, "sign_edge", (scx - 0.4, sy - 1.25, sz_ - 0.03), (scx + 0.4, sy - 0.44, sz_ + 0.03), "c_chest", stretch=True)
    # ---- lanterns: on the front-left post's rod, hanging inside, standing on the right counter
    ml.lantern(shell, "lamp_front", (-PX + 0.62, 2.45, PZF + 0.12), size=0.34, metal="brass", chain_to=(-PX + 0.62, 2.92, PZF + 0.12))
    ml.lantern(shell, "lamp_in", (-1.3, 2.35, 0.25), size=0.32, metal="brass", chain_to=(-1.3, APEX - 1.6, 0.25))
    beam(det, "lamp_in_rod", (-PX, BEAM_Y - 0.1, 0.25), (0.0, APEX - 1.55, 0.25), 0.04, IRON)
    # ---- inside: the back shelves of cloth bolts, the left counter, the right counter, a small chest
    levels = ml.shelf_unit(shell, "shelves", -1.55, 1.15, SHELF_Z[0], SHELF_Z[1], levels=(0.5, 1.05, 1.6, 2.15), h=2.55, back=True, uprights=3, detail=det)
    cols = ("cream", "red", "green", "blue", "red", "orange", "olive", "cream", "blue", "red", "green", "cream", "red", "blue")
    for j, (x0, x1, yy, zf, zb) in enumerate(sorted(levels, key=lambda s: s[2])):
        n = 5 if j % 2 else 4
        L = (x1 - x0 - 0.08) / n
        for i in range(n):
            xa = x0 + 0.04 + L * i + 0.02
            r = 0.1 + 0.012 * ((i + j) % 3 == 0)
            col = cols[(i * 3 + j * 5) % len(cols)]
            zc = (zf + zb) / 2 + 0.03 * ((i + j) % 2)
            pc.bolt(det, "bolt_%d_%d" % (j, i), (xa, yy + r * 1.3, zc), (xa + L - 0.04, yy + r * 1.3, zc), r, col)
            if (i + j) % 3 == 1:
                pc.bolt(det, "bolt_top_%d_%d" % (j, i), (xa + 0.06, yy + r * 3.5, zc - 0.02), (xa + L - 0.1, yy + r * 3.5, zc - 0.02), r * 0.92,
                        cols[(i * 3 + j * 5 + 4) % len(cols)])
    cx0, cx1, cz0, cz1 = COUNTER
    top = ml.counter(shell, "counter", cx0, cx1, cz0, cz1, h=1.0, detail=det)
    y = top[1]
    box(shell, "runner_top", (cx0 + 0.25, y, cz0 + 0.02), (cx0 + 1.15, y + 0.015, cz1 + 0.03), {"all": "cloth_red"}, stretch=True)
    ml.plate(shell, "runner_front", (cx0 + 0.7, y - 0.4, cz1 + 0.045), 0.92, 0.82, "c2_runner", normal=(0, 0, 1), th=0.012, edge="cloth_red")
    pc.book_stack(det, "counter_books", (cx0 + 0.3, y + 0.015, (cz0 + cz1) / 2), 4, rng, covers=("leather", "leather_dark", "cloth_red", "leather"), w=0.3,
                  d=0.36)
    for k, (dx, dz, yaw) in enumerate(((0.95, 0.1, 0.2), (1.2, -0.05, -0.3), (1.08, 0.06, 0.1))):
        pc.scroll(det, "counter_scroll_%d" % k, (cx0 + dx, y + 0.07 + 0.1 * (k == 2), (cz0 + cz1) / 2 + dz), length=0.42, r=0.065, yaw=yaw)
    decor.block("farmhouse_decorations:pile_of_books", cx0 + 1.55, y, (cz0 + cz1) / 2 - 0.05, facing="front", scale=1.1, solid=False, fallback="leather")
    rx0, rx1, rz0, rz1 = R_COUNTER
    rtop = ml.counter(shell, "r_counter", rx0, rx1, rz0, rz1, h=1.0, detail=det)
    for k, (dx, s_) in enumerate(((0.25, 0.26), (0.55, 0.2))):
        ml.sack(det, "coin_bag_%d" % k, (rx0 + dx, rtop[1], (rz0 + rz1) / 2), s=s_, yaw=0.4 * k, region="c_burlap")
    pc.standing_lantern(shell, det, "lamp_counter", (rx0 + 0.95, rtop[1], (rz0 + rz1) / 2), size=0.32, metal="brass")
    pc.chest(shell, det, "small_chest", (1.55, 0.0, 0.2), size=(0.62, 0.46, 0.42), yaw=-0.2, wood="c_chest", domed=False)
    # ---- outside left: the big open crate of rolls with a box on top, the draped barrel, the sack
    roll_crate(shell, det, "crate_l", (-3.2, 0.0, 1.75), (1.15, 0.82, 0.8), ("blue", "red", "sack"), rng, yaw=0.08, cloth=False)
    collide((-3.82, 0.0, 1.3, -2.58, 0.86, 2.2))
    decor.block("furnish:spruce_crate", -3.35, 0.82, 1.5, facing="front", scale=0.62, alt="minecraft:barrel", fallback="crate", solid=True)
    draped_barrel(shell, det, "barrel_l", (-2.25, 0.0, 2.92), rng=rng)
    pc.scroll(det, "barrel_scroll_0", (-2.3, 0.94, 2.9), length=0.44, r=0.07, yaw=0.15)
    pc.scroll(det, "barrel_scroll_1", (-2.22, 0.94, 3.05), length=0.4, r=0.065, yaw=-0.2)
    pc.book(det, "barrel_book", (-2.25, 1.06, 2.95), size=(0.3, 0.08, 0.36), yaw=0.3, cover="leather")
    decor.block("farmersdelight:rice_bag", -3.2, 0.0, 2.95, facing="front", scale=0.9, fallback="c_burlap")
    # ---- outside right: the domed treasure chest, the big crate of standing rolls under a cream cloth
    pc.chest(shell, det, "treasure", (2.35, 0.0, 2.85), size=(1.0, 0.78, 0.66), yaw=-0.12, wood="c_chest", domed=True, trim="gold")
    roll_crate(shell, det, "crate_r", (3.55, 0.0, 1.95), (1.2, 0.85, 0.82), ("red", "blue", "green", "orange", "sack"), rng, yaw=-0.06, cloth=True)
    collide((2.92, 0.0, 1.5, 4.18, 0.88, 2.4))
    # ---- ivy at the feet, the rug in front
    for k, (x, z) in enumerate(((-3.95, 2.35), (-2.65, 3.45), (4.25, 2.55), (-1.75, 3.2))):
        pc.ivy_bush(det, "ivy_%d" % k, (x, 0.0, z), h=0.55, w=0.6, rng=rng)
    ml.vine(det, "ivy_crate", (-2.62, 0.82, 1.85), 0.7, 0.45, normal=(1, 0, 0.3))
    ml.rug(shell, "rug", -1.3, 1.6, 1.55, 4.35, y=0.005, region="c2_rug")
    return root


def item_icon(path):
    """16x16: the red-and-cream cone with its brass spire on the black iron frame, the banner on the left."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    red, cr, gold, iron = P.red, P.cream, P.gold, (40, 38, 40)
    for y in range(3, 10):
        half = 0.6 + (y - 3) * 0.95
        for x in range(2, 16):
            dx = x - 9.0
            if abs(dx) <= half:
                k = int((math.atan2(dx, (y - 2.5)) + 1.6) * 3.2) % 2
                p[x, y] = (red if k == 0 else cr) + (255,)
    for y in range(0, 3):
        p[9, y] = gold + (255,)
    for x in range(3, 16):
        p[x, 10] = (cr if (x // 2) % 2 else red) + (255,)
    for x in (4, 14):
        for y in range(10, 16):
            p[x, y] = iron + (255,)
    for y in range(11, 15):
        for x in range(5, 14):
            p[x, y] = (54, 34, 22, 255)
    for y in range(2, 15):
        p[1, y] = iron + (255,)
    for y in range(4, 10):
        p[0, y] = red + (255,)
    p[0, 6] = gold + (255,)
    for x in range(5, 14):
        p[x, 15] = (red if 7 <= x <= 11 else (80, 56, 34)) + (255,)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)


def main():
    ml.setup(NAME)
    atlas = ml.Atlas(NAME, colour="red")
    pc.add_regions(atlas, regions())
    decor = ml.Decor()
    root = build(decor)
    ml.export(root, NAME, atlas, decor=decor, icon=item_icon, light=12)
    print("atlas", atlas.size)


if __name__ == "__main__":
    main()
